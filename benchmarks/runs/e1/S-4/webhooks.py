"""Transactional outbox + in-process dispatcher for order webhooks (stdlib only)."""
import json
import random
import sqlite3
import threading
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

SCHEMA = """
CREATE TABLE IF NOT EXISTS orders(
  id INTEGER PRIMARY KEY, customer_url TEXT, status TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS webhook_outbox(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  order_id INTEGER NOT NULL,
  url TEXT NOT NULL,
  payload TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  attempts INTEGER NOT NULL DEFAULT 0,
  next_attempt_at REAL NOT NULL,
  lease_until REAL,
  last_error TEXT,
  created_at REAL NOT NULL);
CREATE INDEX IF NOT EXISTS ix_outbox_due ON webhook_outbox(status, next_attempt_at);
"""


def connect(path):
    conn = sqlite3.connect(path, timeout=30, isolation_level=None,
                           check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA busy_timeout=30000")
    return conn


def init_db(path):
    conn = connect(path)
    conn.executescript(SCHEMA)
    conn.close()


def confirm_order(conn, order_id, url, payload):
    """Confirm order and enqueue webhook atomically. No network I/O."""
    conn.execute("BEGIN IMMEDIATE")
    try:
        conn.execute("INSERT OR REPLACE INTO orders(id, customer_url, status) "
                     "VALUES(?,?,'confirmed')", (order_id, url))
        now = time.time()
        cur = conn.execute(
            "INSERT INTO webhook_outbox(order_id,url,payload,next_attempt_at,created_at)"
            " VALUES(?,?,?,?,?)", (order_id, url, json.dumps(payload), now, now))
        conn.execute("COMMIT")
        return cur.lastrowid
    except BaseException:
        conn.execute("ROLLBACK")
        raise


def claim(conn, limit=100, lease=30.0, now=None):
    """Atomically lease due rows (pending, or in_flight with expired lease)."""
    now = time.time() if now is None else now
    conn.execute("BEGIN IMMEDIATE")
    try:
        rows = conn.execute(
            "SELECT id,url,payload,attempts FROM webhook_outbox WHERE "
            "(status='pending' AND next_attempt_at<=?) OR "
            "(status='in_flight' AND lease_until<=?) ORDER BY id LIMIT ?",
            (now, now, limit)).fetchall()
        for r in rows:
            conn.execute("UPDATE webhook_outbox SET status='in_flight', lease_until=? "
                         "WHERE id=?", (now + lease, r[0]))
        conn.execute("COMMIT")
    except BaseException:
        conn.execute("ROLLBACK")
        raise
    return rows


def http_sender(url, body, key, timeout=5.0):
    req = urllib.request.Request(
        url, data=body.encode(), method="POST",
        headers={"Content-Type": "application/json", "Idempotency-Key": key})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        if not 200 <= resp.status < 300:
            raise RuntimeError("HTTP %s" % resp.status)


class Dispatcher:
    def __init__(self, db_path, sender=http_sender, workers=32, poll=0.05,
                 lease=30.0, max_attempts=8, base_delay=2.0, max_delay=3600.0):
        self.db_path, self.sender = db_path, sender
        self.poll, self.lease = poll, lease
        self.max_attempts, self.base_delay, self.max_delay = max_attempts, base_delay, max_delay
        self.pool = ThreadPoolExecutor(max_workers=workers)
        self.workers = workers
        self._stop = threading.Event()
        self._thread = None
        self._local = threading.local()
        self._inflight = 0
        self._lock = threading.Lock()

    def _conn(self):
        c = getattr(self._local, "c", None)
        if c is None:
            c = self._local.c = connect(self.db_path)
        return c

    def backoff(self, attempts):
        d = min(self.base_delay * (2 ** (attempts - 1)), self.max_delay)
        return d * random.uniform(0.5, 1.0)

    def _deliver(self, row):
        wid, url, payload, attempts = row
        attempts += 1
        err = None
        try:
            self.sender(url, payload, str(wid))
        except Exception as e:  # noqa: BLE001
            err = repr(e)[:500]
        conn = self._conn()
        if err is None:
            conn.execute("UPDATE webhook_outbox SET status='delivered',attempts=?,"
                         "lease_until=NULL,last_error=NULL WHERE id=?", (attempts, wid))
        elif attempts >= self.max_attempts:
            conn.execute("UPDATE webhook_outbox SET status='dead',attempts=?,"
                         "lease_until=NULL,last_error=? WHERE id=?", (attempts, err, wid))
        else:
            conn.execute("UPDATE webhook_outbox SET status='pending',attempts=?,"
                         "next_attempt_at=?,lease_until=NULL,last_error=? WHERE id=?",
                         (attempts, time.time() + self.backoff(attempts), err, wid))
        with self._lock:
            self._inflight -= 1

    def _run(self):
        conn = connect(self.db_path)
        while not self._stop.is_set():
            with self._lock:
                free = self.workers - self._inflight
            rows = claim(conn, limit=free, lease=self.lease) if free > 0 else []
            for r in rows:
                with self._lock:
                    self._inflight += 1
                self.pool.submit(self._deliver, r)
            if not rows:
                self._stop.wait(self.poll)
        conn.close()

    def start(self):
        self._thread = threading.Thread(target=self._run, daemon=True, name="webhook-dispatcher")
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join()
        self.pool.shutdown(wait=True)
