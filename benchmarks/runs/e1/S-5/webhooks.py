"""Transactional outbox + in-process dispatcher for order-confirmed webhooks."""
import json, random, sqlite3, threading, time, urllib.request, uuid
from concurrent.futures import ThreadPoolExecutor


def connect(db_path):
    conn = sqlite3.connect(db_path, timeout=30, isolation_level=None)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA busy_timeout=30000")
    return conn


def init_db(db_path):
    conn = connect(db_path)
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS orders(
        id INTEGER PRIMARY KEY, status TEXT NOT NULL DEFAULT 'new');
    CREATE TABLE IF NOT EXISTS webhook_outbox(
        id TEXT PRIMARY KEY, order_id INTEGER NOT NULL, url TEXT NOT NULL,
        payload TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending',
        attempts INTEGER NOT NULL DEFAULT 0, next_attempt_at REAL NOT NULL,
        lease_until REAL, last_error TEXT, created_at REAL NOT NULL);
    CREATE INDEX IF NOT EXISTS ix_outbox_due ON webhook_outbox(status, next_attempt_at);
    """)
    conn.close()


def confirm_order(db_path, order_id, url, conn=None):
    """Request path: no network. Order update and outbox row commit atomically."""
    own = conn is None
    conn = conn or connect(db_path)
    try:
        now = time.time()
        conn.execute("BEGIN IMMEDIATE")
        try:
            conn.execute("INSERT INTO orders(id,status) VALUES(?, 'confirmed') "
                         "ON CONFLICT(id) DO UPDATE SET status='confirmed'", (order_id,))
            wid = str(uuid.uuid4())
            conn.execute("INSERT INTO webhook_outbox(id,order_id,url,payload,next_attempt_at,created_at)"
                         " VALUES(?,?,?,?,?,?)",
                         (wid, order_id, url,
                          json.dumps({"event": "order.confirmed", "order_id": order_id}), now, now))
            conn.execute("COMMIT")
        except BaseException:
            conn.execute("ROLLBACK")
            raise
        return wid
    finally:
        if own:
            conn.close()


def stats(db_path):
    conn = connect(db_path)
    try:
        return dict(conn.execute("SELECT status, COUNT(*) FROM webhook_outbox GROUP BY status"))
    finally:
        conn.close()


def replay_dead(db_path):
    conn = connect(db_path)
    try:
        cur = conn.execute("UPDATE webhook_outbox SET status='pending', attempts=0, "
                           "next_attempt_at=? WHERE status='dead'", (time.time(),))
        return cur.rowcount
    finally:
        conn.close()


class Dispatcher:
    def __init__(self, db_path, workers=32, http_timeout=10.0, max_attempts=8,
                 backoff_base=2.0, backoff_cap=3600.0, poll_interval=0.2):
        self.db_path, self.workers = db_path, workers
        self.http_timeout, self.max_attempts = http_timeout, max_attempts
        self.backoff_base, self.backoff_cap = backoff_base, backoff_cap
        self.poll_interval = poll_interval
        self.lease = http_timeout + 30.0
        self._stop = threading.Event()
        self._slots = threading.Semaphore(workers)
        self._pool = None
        self._thread = None
        self._local = threading.local()

    def _conn(self):
        c = getattr(self._local, "c", None)
        if c is None:
            c = self._local.c = connect(self.db_path)
        return c

    def start(self):
        self._pool = ThreadPoolExecutor(self.workers)
        self._thread = threading.Thread(target=self._run, daemon=True, name="webhook-poller")
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join()
        if self._pool:
            self._pool.shutdown(wait=True)

    def claim(self, limit):
        conn, now = self._conn(), time.time()
        conn.execute("BEGIN IMMEDIATE")
        try:
            rows = conn.execute(
                "SELECT id,url,payload,attempts FROM webhook_outbox WHERE "
                "(status='pending' AND next_attempt_at<=?) OR "
                "(status='in_progress' AND lease_until<=?) "
                "ORDER BY next_attempt_at LIMIT ?", (now, now, limit)).fetchall()
            conn.executemany("UPDATE webhook_outbox SET status='in_progress', lease_until=? WHERE id=?",
                             [(now + self.lease, r[0]) for r in rows])
            conn.execute("COMMIT")
        except BaseException:
            conn.execute("ROLLBACK")
            raise
        return rows

    def _run(self):
        while not self._stop.is_set():
            free = 0
            while free < self.workers and self._slots.acquire(blocking=False):
                free += 1
            rows = []
            try:
                if free:
                    rows = self.claim(free)
            except sqlite3.Error:
                rows = []
            for _ in range(free - len(rows)):
                self._slots.release()
            for r in rows:
                self._pool.submit(self._deliver, *r)
            if not rows:
                self._stop.wait(self.poll_interval)

    def _post(self, wid, url, payload):
        req = urllib.request.Request(url, data=payload.encode(), method="POST", headers={
            "Content-Type": "application/json", "X-Webhook-Id": wid})
        with urllib.request.urlopen(req, timeout=self.http_timeout) as resp:
            return 200 <= resp.status < 300

    def _deliver(self, wid, url, payload, attempts):
        try:
            try:
                ok, err = self._post(wid, url, payload), "non-2xx"
            except Exception as e:  # timeout, connection error, HTTP error
                ok, err = False, repr(e)[:300]
            conn = self._conn()
            if ok:
                conn.execute("UPDATE webhook_outbox SET status='delivered', attempts=?, "
                             "lease_until=NULL, last_error=NULL WHERE id=?", (attempts + 1, wid))
            elif attempts + 1 >= self.max_attempts:
                conn.execute("UPDATE webhook_outbox SET status='dead', attempts=?, lease_until=NULL,"
                             " last_error=? WHERE id=?", (attempts + 1, err, wid))
            else:
                delay = min(self.backoff_cap, self.backoff_base * 2 ** attempts)
                delay *= random.uniform(0.5, 1.0)
                conn.execute("UPDATE webhook_outbox SET status='pending', attempts=?, lease_until=NULL,"
                             " next_attempt_at=?, last_error=? WHERE id=?",
                             (attempts + 1, time.time() + delay, err, wid))
        finally:
            self._slots.release()
