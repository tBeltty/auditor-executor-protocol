"""Transactional webhook outbox on SQLite. Stdlib only. At-least-once delivery."""
import json
import sqlite3
import threading
import time
import urllib.request
from urllib.parse import urlsplit

SCHEMA = """
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY, status TEXT NOT NULL, webhook_url TEXT);
CREATE TABLE IF NOT EXISTS webhook_outbox (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    url TEXT NOT NULL,
    payload TEXT NOT NULL,
    state TEXT NOT NULL DEFAULT 'pending',   -- pending | claimed | delivered | dead
    attempts INTEGER NOT NULL DEFAULT 0,
    next_at REAL NOT NULL,
    claimed_at REAL,
    last_error TEXT);
CREATE INDEX IF NOT EXISTS ix_outbox_due ON webhook_outbox(state, next_at);
"""

MAX_ATTEMPTS = 12


def connect(path):
    conn = sqlite3.connect(path, timeout=30, isolation_level=None,
                           check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA busy_timeout=30000")
    conn.executescript(SCHEMA)
    return conn


def enqueue(conn, order_id, url, payload, now=None):
    """Call inside the order transaction so the record commits atomically with it."""
    conn.execute(
        "INSERT INTO webhook_outbox(order_id,url,payload,next_at) VALUES(?,?,?,?)",
        (order_id, url, json.dumps(payload), now if now is not None else time.time()))


def confirm_order(conn, order_id, url, payload):
    conn.execute("BEGIN IMMEDIATE")
    try:
        conn.execute("UPDATE orders SET status='confirmed' WHERE id=?", (order_id,))
        if url:
            enqueue(conn, order_id, url, dict(payload, order_id=order_id))
        conn.execute("COMMIT")
    except BaseException:
        conn.execute("ROLLBACK")
        raise


def claim(conn, limit=10, now=None, skip_urls=()):
    now = now if now is not None else time.time()
    conn.execute("BEGIN IMMEDIATE")
    try:
        rows = conn.execute(
            "SELECT id,url,payload,attempts FROM webhook_outbox "
            "WHERE state='pending' AND next_at<=? ORDER BY next_at LIMIT ?",
            (now, limit * 4)).fetchall()
        rows = [r for r in rows if r[1] not in skip_urls][:limit]
        for r in rows:
            conn.execute("UPDATE webhook_outbox SET state='claimed',claimed_at=? WHERE id=?",
                         (now, r[0]))
        conn.execute("COMMIT")
    except BaseException:
        conn.execute("ROLLBACK")
        raise
    return rows


def backoff(attempts):
    return min(3600.0, 2.0 ** attempts)


def mark_delivered(conn, row_id):
    conn.execute("UPDATE webhook_outbox SET state='delivered',claimed_at=NULL WHERE id=?",
                 (row_id,))


def mark_failed(conn, row_id, attempts, error, now=None):
    now = now if now is not None else time.time()
    attempts += 1
    if attempts >= MAX_ATTEMPTS:
        conn.execute("UPDATE webhook_outbox SET state='dead',attempts=?,last_error=?,"
                     "claimed_at=NULL WHERE id=?", (attempts, error, row_id))
    else:
        conn.execute("UPDATE webhook_outbox SET state='pending',attempts=?,last_error=?,"
                     "next_at=?,claimed_at=NULL WHERE id=?",
                     (attempts, error, now + backoff(attempts), row_id))


def recover_stale(conn, older_than=60.0, now=None):
    """Return claims abandoned by a crashed process to the pending state."""
    now = now if now is not None else time.time()
    cur = conn.execute("UPDATE webhook_outbox SET state='pending',claimed_at=NULL "
                       "WHERE state='claimed' AND claimed_at<?", (now - older_than,))
    return cur.rowcount


def http_send(url, body, timeout=5.0):
    req = urllib.request.Request(url, data=body.encode(), method="POST",
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        if not 200 <= resp.status < 300:
            raise RuntimeError("HTTP %s" % resp.status)


class CircuitBreaker:
    """Per-host: after `threshold` consecutive failures, skip it for `cooldown` s."""

    def __init__(self, threshold=3, cooldown=30.0, clock=time.time):
        self.threshold, self.cooldown, self.clock = threshold, cooldown, clock
        self._fails, self._open_until = {}, {}
        self._lock = threading.Lock()

    @staticmethod
    def key(url):
        return urlsplit(url).netloc

    def ok(self, url):
        with self._lock:
            self._fails.pop(self.key(url), None)
            self._open_until.pop(self.key(url), None)

    def fail(self, url):
        k = self.key(url)
        with self._lock:
            self._fails[k] = self._fails.get(k, 0) + 1
            if self._fails[k] >= self.threshold:
                self._open_until[k] = self.clock() + self.cooldown

    def open_hosts(self):
        now = self.clock()
        with self._lock:
            return {k for k, t in self._open_until.items() if t > now}


class Dispatcher:
    def __init__(self, db_path, workers=16, sender=http_send, poll=0.2,
                 stale_after=60.0, breaker=None):
        self.db_path, self.workers, self.sender = db_path, workers, sender
        self.poll, self.stale_after = poll, stale_after
        self.breaker = breaker or CircuitBreaker()
        self._stop = threading.Event()
        self._threads = []

    def start(self):
        c = connect(self.db_path)
        recover_stale(c, 0)  # at startup no other claim of ours can be live
        c.close()
        for _ in range(self.workers):
            t = threading.Thread(target=self._run, daemon=True)
            t.start()
            self._threads.append(t)

    def stop(self):
        self._stop.set()
        for t in self._threads:
            t.join(timeout=15)

    def _run(self):
        conn = connect(self.db_path)
        while not self._stop.is_set():
            rows = claim(conn, limit=1, skip_urls=self._skip(conn))
            if not rows:
                self._stop.wait(self.poll)
                continue
            rid, url, payload, attempts = rows[0]
            try:
                self.sender(url, payload)
            except Exception as e:  # noqa: BLE001
                self.breaker.fail(url)
                mark_failed(conn, rid, attempts, repr(e)[:200])
            else:
                self.breaker.ok(url)
                mark_delivered(conn, rid)
        conn.close()

    def _skip(self, conn):
        hosts = self.breaker.open_hosts()
        if not hosts:
            return ()
        return _HostSet(hosts)


class _HostSet:
    """Membership test by host so claim() can skip URLs of tripped endpoints."""

    def __init__(self, hosts):
        self.hosts = hosts

    def __contains__(self, url):
        return CircuitBreaker.key(url) in self.hosts
