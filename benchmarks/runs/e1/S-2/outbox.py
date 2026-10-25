"""Transactional outbox for webhooks on SQLite. Standard library only."""
import json
import random
import sqlite3
import threading
import time
import urllib.request

SCHEMA = """
CREATE TABLE IF NOT EXISTS webhook_outbox(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  order_id INTEGER NOT NULL,
  url TEXT NOT NULL,
  payload TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  attempts INTEGER NOT NULL DEFAULT 0,
  next_attempt_at REAL NOT NULL,
  locked_until REAL NOT NULL DEFAULT 0,
  last_error TEXT,
  created_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_outbox_due ON webhook_outbox(status, next_attempt_at);
"""


def connect(path):
    conn = sqlite3.connect(path, timeout=10, isolation_level=None,
                           check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=10000")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def init_schema(conn):
    conn.executescript(SCHEMA)


def enqueue(conn, order_id, url, payload):
    """Insert inside the caller's transaction; no commit here."""
    now = time.time()
    cur = conn.execute(
        "INSERT INTO webhook_outbox(order_id,url,payload,next_attempt_at,created_at)"
        " VALUES(?,?,?,?,?)", (order_id, url, json.dumps(payload), now, now))
    return cur.lastrowid


def claim(conn, limit=10, lease=30.0, per_url_cap=4, in_flight=None, now=None):
    """Atomically lease due rows. Returns list of (id, url, payload, attempts)."""
    now = time.time() if now is None else now
    in_flight = in_flight or {}
    conn.execute("BEGIN IMMEDIATE")
    try:
        rows = conn.execute(
            "SELECT id,url,payload,attempts FROM webhook_outbox WHERE "
            "((status='pending' AND next_attempt_at<=?) OR "
            " (status='in_flight' AND locked_until<?)) "
            "ORDER BY next_attempt_at LIMIT ?", (now, now, limit * 8)).fetchall()
        counts = dict(in_flight)
        chosen = []
        for r in rows:
            if len(chosen) >= limit:
                break
            if counts.get(r[1], 0) >= per_url_cap:
                continue
            counts[r[1]] = counts.get(r[1], 0) + 1
            chosen.append(r)
        for r in chosen:
            conn.execute("UPDATE webhook_outbox SET status='in_flight',"
                         "locked_until=? WHERE id=?", (now + lease, r[0]))
        conn.execute("COMMIT")
    except BaseException:
        conn.execute("ROLLBACK")
        raise
    return chosen


def mark_delivered(conn, wid):
    conn.execute("UPDATE webhook_outbox SET status='delivered',"
                 "attempts=attempts+1,last_error=NULL WHERE id=?", (wid,))


def mark_failed(conn, wid, error, attempts, max_attempts=8, base=2.0, cap=600.0,
                now=None):
    now = time.time() if now is None else now
    attempts += 1
    if attempts >= max_attempts:
        conn.execute("UPDATE webhook_outbox SET status='dead',attempts=?,"
                     "last_error=? WHERE id=?", (attempts, str(error)[:500], wid))
        return
    delay = min(cap, base * (2 ** (attempts - 1))) * random.uniform(0.5, 1.0)
    conn.execute("UPDATE webhook_outbox SET status='pending',attempts=?,"
                 "next_attempt_at=?,last_error=? WHERE id=?",
                 (attempts, now + delay, str(error)[:500], wid))


def replay_dead(conn):
    cur = conn.execute("UPDATE webhook_outbox SET status='pending',attempts=0,"
                       "next_attempt_at=? WHERE status='dead'", (time.time(),))
    return cur.rowcount


def http_post(url, body, webhook_id, timeout):
    req = urllib.request.Request(
        url, data=body.encode(), method="POST",
        headers={"Content-Type": "application/json",
                 "X-Webhook-Id": str(webhook_id)})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        if not 200 <= resp.status < 300:
            raise RuntimeError("HTTP %d" % resp.status)


class Dispatcher:
    def __init__(self, db_path, workers=32, http_timeout=3.0, lease=30.0,
                 per_url_cap=4, max_attempts=8, backoff_base=2.0, poll=0.05,
                 sender=http_post):
        self.db_path, self.workers = db_path, workers
        self.http_timeout, self.lease = http_timeout, lease
        self.per_url_cap, self.max_attempts = per_url_cap, max_attempts
        self.backoff_base, self.poll, self.sender = backoff_base, poll, sender
        self._stop = threading.Event()
        self._threads = []
        self._lock = threading.Lock()
        self._in_flight = {}

    def start(self):
        for i in range(self.workers):
            t = threading.Thread(target=self._run, name="webhook-%d" % i,
                                 daemon=True)
            t.start()
            self._threads.append(t)

    def stop(self, join_timeout=15):
        self._stop.set()
        for t in self._threads:
            t.join(join_timeout)
        self._threads = []

    def _run(self):
        conn = connect(self.db_path)
        try:
            while not self._stop.is_set():
                with self._lock:
                    snapshot = dict(self._in_flight)
                    rows = claim(conn, 1, self.lease, self.per_url_cap, snapshot)
                    for r in rows:
                        self._in_flight[r[1]] = self._in_flight.get(r[1], 0) + 1
                if not rows:
                    self._stop.wait(self.poll)
                    continue
                wid, url, payload, attempts = rows[0]
                try:
                    try:
                        self.sender(url, payload, wid, self.http_timeout)
                        mark_delivered(conn, wid)
                    except Exception as exc:  # noqa: BLE001
                        mark_failed(conn, wid, repr(exc), attempts,
                                    self.max_attempts, self.backoff_base)
                finally:
                    with self._lock:
                        self._in_flight[url] -= 1
        finally:
            conn.close()


def counts(conn):
    return dict(conn.execute(
        "SELECT status,COUNT(*) FROM webhook_outbox GROUP BY status").fetchall())
