"""SQLite transactional outbox for order webhooks (stdlib only)."""
import json
import sqlite3
import time
import uuid

SCHEMA = """
CREATE TABLE IF NOT EXISTS orders (
  id TEXT PRIMARY KEY, status TEXT NOT NULL, webhook_url TEXT);
CREATE TABLE IF NOT EXISTS outbox (
  id TEXT PRIMARY KEY,
  order_id TEXT NOT NULL,
  url TEXT NOT NULL,
  payload TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',   -- pending | delivered | dead
  attempts INTEGER NOT NULL DEFAULT 0,
  next_at REAL NOT NULL,
  lease_until REAL NOT NULL DEFAULT 0,
  last_error TEXT,
  created_at REAL NOT NULL);
CREATE INDEX IF NOT EXISTS outbox_due ON outbox(status, next_at);
"""


def connect(path):
    conn = sqlite3.connect(path, timeout=5, isolation_level=None,
                           check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


def init(path):
    conn = connect(path)
    conn.executescript(SCHEMA)
    conn.close()


def enqueue(conn, order_id, url, payload, now=None):
    """Insert an outbox row using the caller's connection/transaction."""
    now = time.time() if now is None else now
    oid = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO outbox(id,order_id,url,payload,next_at,created_at)"
        " VALUES(?,?,?,?,?,?)",
        (oid, order_id, url, json.dumps(payload), now, now))
    return oid


def claim(conn, limit=50, lease=30.0, now=None):
    """Atomically lease due rows. Expired leases (crashed worker) are reclaimed."""
    now = time.time() if now is None else now
    conn.execute("BEGIN IMMEDIATE")
    try:
        rows = conn.execute(
            "SELECT id,order_id,url,payload,attempts FROM outbox"
            " WHERE status='pending' AND next_at<=? AND lease_until<=?"
            " ORDER BY next_at LIMIT ?", (now, now, limit)).fetchall()
        for r in rows:
            conn.execute("UPDATE outbox SET lease_until=? WHERE id=?",
                         (now + lease, r[0]))
        conn.execute("COMMIT")
    except BaseException:
        conn.execute("ROLLBACK")
        raise
    return [dict(id=r[0], order_id=r[1], url=r[2], payload=r[3], attempts=r[4])
            for r in rows]


def mark_delivered(conn, oid):
    conn.execute("UPDATE outbox SET status='delivered', lease_until=0 WHERE id=?",
                 (oid,))


def mark_failed(conn, oid, attempts, error, max_attempts=8, base=2.0,
                cap=3600.0, now=None):
    now = time.time() if now is None else now
    attempts += 1
    if attempts >= max_attempts:
        conn.execute("UPDATE outbox SET status='dead',attempts=?,last_error=?,"
                     "lease_until=0 WHERE id=?", (attempts, error, oid))
    else:
        delay = min(cap, base * (2 ** (attempts - 1)))
        conn.execute("UPDATE outbox SET attempts=?,last_error=?,next_at=?,"
                     "lease_until=0 WHERE id=?",
                     (attempts, error, now + delay, oid))


def counts(conn):
    return dict(conn.execute(
        "SELECT status,COUNT(*) FROM outbox GROUP BY status").fetchall())
