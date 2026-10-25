"""Transactional outbox + background dispatcher for order webhooks (stdlib only)."""
import json
import random
import sqlite3
import threading
import time
import urllib.request
import uuid

SCHEMA = """
CREATE TABLE IF NOT EXISTS orders(
  id TEXT PRIMARY KEY, status TEXT NOT NULL DEFAULT 'new');
CREATE TABLE IF NOT EXISTS webhook_outbox(
  id TEXT PRIMARY KEY, order_id TEXT NOT NULL, url TEXT NOT NULL,
  payload TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending',
  attempts INTEGER NOT NULL DEFAULT 0, next_attempt_at REAL NOT NULL,
  lease_until REAL, last_error TEXT, created_at REAL NOT NULL, delivered_at REAL);
CREATE INDEX IF NOT EXISTS ix_outbox_due ON webhook_outbox(status, next_attempt_at);
"""


def connect(path):
    conn = sqlite3.connect(path, timeout=30, isolation_level=None)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA busy_timeout=30000")
    return conn


def init_db(path):
    conn = connect(path)
    conn.executescript(SCHEMA)
    conn.close()


def confirm_order(conn, order_id, url, payload):
    """Confirm an order and enqueue its webhook atomically. No network I/O."""
    event_id = str(uuid.uuid4())
    now = time.time()
    conn.execute("BEGIN IMMEDIATE")
    try:
        conn.execute("INSERT INTO orders(id,status) VALUES(?, 'confirmed') "
                     "ON CONFLICT(id) DO UPDATE SET status='confirmed'", (order_id,))
        conn.execute(
            "INSERT INTO webhook_outbox(id,order_id,url,payload,next_attempt_at,created_at) "
            "VALUES(?,?,?,?,?,?)",
            (event_id, order_id, url, json.dumps(payload), now, now))
        conn.execute("COMMIT")
    except BaseException:
        conn.execute("ROLLBACK")
        raise
    return event_id


def http_sender(url, body, event_id, timeout=3.0):
    """Default sender: returns on 2xx, raises otherwise."""
    req = urllib.request.Request(
        url, data=body.encode(), method="POST",
        headers={"Content-Type": "application/json", "Idempotency-Key": event_id})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        if not 200 <= resp.status < 300:
            raise RuntimeError("HTTP %s" % resp.status)


class Dispatcher:
    def __init__(self, path, sender=http_sender, workers=32, batch=10, lease=30.0,
                 max_attempts=8, backoff_base=1.0, backoff_cap=300.0, poll=0.05):
        self.path, self.sender = path, sender
        self.workers, self.batch, self.lease = workers, batch, lease
        self.max_attempts, self.backoff_base = max_attempts, backoff_base
        self.backoff_cap, self.poll = backoff_cap, poll
        self._stop = threading.Event()
        self._threads = []

    def start(self):
        for i in range(self.workers):
            t = threading.Thread(target=self._run, name="webhook-%d" % i, daemon=True)
            t.start()
            self._threads.append(t)

    def stop(self):
        self._stop.set()
        for t in self._threads:
            t.join(timeout=5)

    def claim(self, conn, limit):
        now = time.time()
        conn.execute("BEGIN IMMEDIATE")
        try:
            rows = conn.execute(
                "SELECT id,url,payload,attempts FROM webhook_outbox "
                "WHERE (status='pending' AND next_attempt_at<=?) "
                "OR (status='in_flight' AND lease_until<=?) "
                "ORDER BY next_attempt_at LIMIT ?", (now, now, limit)).fetchall()
            for r in rows:
                conn.execute("UPDATE webhook_outbox SET status='in_flight', lease_until=? "
                             "WHERE id=?", (now + self.lease, r[0]))
            conn.execute("COMMIT")
        except BaseException:
            conn.execute("ROLLBACK")
            raise
        return rows

    def _finish(self, conn, event_id, attempts, error):
        attempts += 1
        if error is None:
            conn.execute("UPDATE webhook_outbox SET status='delivered', attempts=?, "
                         "delivered_at=?, lease_until=NULL, last_error=NULL WHERE id=?",
                         (attempts, time.time(), event_id))
        elif attempts >= self.max_attempts:
            conn.execute("UPDATE webhook_outbox SET status='dead', attempts=?, "
                         "lease_until=NULL, last_error=? WHERE id=?",
                         (attempts, error, event_id))
        else:
            delay = min(self.backoff_cap, self.backoff_base * 2 ** (attempts - 1))
            delay *= random.uniform(0.5, 1.0)
            conn.execute("UPDATE webhook_outbox SET status='pending', attempts=?, "
                         "next_attempt_at=?, lease_until=NULL, last_error=? WHERE id=?",
                         (attempts, time.time() + delay, error, event_id))

    def process_once(self, conn):
        rows = self.claim(conn, self.batch)
        for event_id, url, payload, attempts in rows:
            try:
                self.sender(url, payload, event_id)
                err = None
            except Exception as exc:  # any failure is retried
                err = "%s: %s" % (type(exc).__name__, exc)
            self._finish(conn, event_id, attempts, err)
        return len(rows)

    def _run(self):
        conn = connect(self.path)
        try:
            while not self._stop.is_set():
                try:
                    n = self.process_once(conn)
                except sqlite3.Error:
                    n = 0
                if n == 0:
                    self._stop.wait(self.poll + random.uniform(0, self.poll))
        finally:
            conn.close()
