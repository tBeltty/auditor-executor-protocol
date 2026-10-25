"""Transactional-outbox webhook delivery on SQLite (stdlib only)."""
import json
import sqlite3
import threading
import time
import urllib.request

SCHEMA = """
CREATE TABLE IF NOT EXISTS orders(
  id INTEGER PRIMARY KEY, status TEXT NOT NULL DEFAULT 'new', webhook_url TEXT);
CREATE TABLE IF NOT EXISTS outbox(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  order_id INTEGER NOT NULL, url TEXT NOT NULL, payload TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',   -- pending | in_flight | delivered | dead
  attempts INTEGER NOT NULL DEFAULT 0,
  next_attempt_at REAL NOT NULL, locked_until REAL NOT NULL DEFAULT 0,
  last_error TEXT);
CREATE INDEX IF NOT EXISTS outbox_due ON outbox(status, next_attempt_at);
"""


def connect(path):
    c = sqlite3.connect(path, timeout=30, isolation_level=None)
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA synchronous=NORMAL")
    c.execute("PRAGMA busy_timeout=30000")
    return c


def init_db(path):
    c = connect(path)
    c.executescript(SCHEMA)
    c.close()


def confirm_order(conn, order_id, now=None):
    """Confirm an order and enqueue its webhook atomically. No network I/O."""
    now = time.time() if now is None else now
    conn.execute("BEGIN IMMEDIATE")
    try:
        row = conn.execute("SELECT webhook_url FROM orders WHERE id=?", (order_id,)).fetchone()
        if row is None:
            raise KeyError(order_id)
        conn.execute("UPDATE orders SET status='confirmed' WHERE id=?", (order_id,))
        if row[0]:
            payload = json.dumps({"event": "order.confirmed", "order_id": order_id})
            conn.execute(
                "INSERT INTO outbox(order_id,url,payload,next_attempt_at) VALUES(?,?,?,?)",
                (order_id, row[0], payload, now))
        conn.execute("COMMIT")
    except BaseException:
        conn.execute("ROLLBACK")
        raise


def claim(conn, lease=30.0, now=None):
    """Claim one due event (or one whose lease expired after a crash)."""
    now = time.time() if now is None else now
    conn.execute("BEGIN IMMEDIATE")
    try:
        row = conn.execute(
            "SELECT id,url,payload,attempts FROM outbox WHERE "
            "(status='pending' AND next_attempt_at<=?) OR (status='in_flight' AND locked_until<?) "
            "ORDER BY next_attempt_at LIMIT 1", (now, now)).fetchone()
        if row:
            conn.execute("UPDATE outbox SET status='in_flight', locked_until=? WHERE id=?",
                         (now + lease, row[0]))
        conn.execute("COMMIT")
        return row
    except BaseException:
        conn.execute("ROLLBACK")
        raise


def http_post(url, payload, timeout, event_id):
    req = urllib.request.Request(
        url, data=payload.encode(), method="POST",
        headers={"Content-Type": "application/json", "X-Webhook-Id": str(event_id)})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return 200 <= r.status < 300


class Dispatcher:
    def __init__(self, db_path, workers=32, timeout=3.0, max_attempts=50,
                 backoff_base=1.0, backoff_cap=300.0, poll=0.05, post=http_post):
        self.db_path, self.workers, self.timeout = db_path, workers, timeout
        self.max_attempts, self.backoff_base, self.backoff_cap = max_attempts, backoff_base, backoff_cap
        self.poll, self.post = poll, post
        self.lease = timeout + 30
        self._stop = threading.Event()
        self._threads = []

    def start(self):
        for _ in range(self.workers):
            t = threading.Thread(target=self._run, daemon=True)
            t.start()
            self._threads.append(t)

    def stop(self):
        self._stop.set()
        for t in self._threads:
            t.join()
        self._threads = []

    def _run(self):
        conn = connect(self.db_path)
        while not self._stop.is_set():
            if not self.process_one(conn):
                self._stop.wait(self.poll)
        conn.close()

    def process_one(self, conn):
        row = claim(conn, self.lease)
        if row is None:
            return False
        eid, url, payload, attempts = row
        try:
            ok, err = self.post(url, payload, self.timeout, eid), None
            if not ok:
                err = "non-2xx"
        except Exception as e:  # network error, timeout, HTTP error
            ok, err = False, repr(e)
        attempts += 1
        if ok:
            conn.execute("UPDATE outbox SET status='delivered', attempts=? WHERE id=?", (attempts, eid))
        elif attempts >= self.max_attempts:
            conn.execute("UPDATE outbox SET status='dead', attempts=?, last_error=? WHERE id=?",
                         (attempts, err, eid))  # kept for manual replay, never deleted
        else:
            delay = min(self.backoff_cap, self.backoff_base * 2 ** (attempts - 1))
            conn.execute("UPDATE outbox SET status='pending', attempts=?, last_error=?, "
                         "next_attempt_at=? WHERE id=?", (attempts, err, time.time() + delay, eid))
        return True
