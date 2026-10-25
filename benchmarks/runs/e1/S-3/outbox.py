"""Transactional outbox for webhooks, stored in the existing SQLite file."""
import json
import random
import sqlite3
import time
import uuid

SCHEMA = """
CREATE TABLE IF NOT EXISTS webhook_outbox (
    id TEXT PRIMARY KEY,
    order_id TEXT NOT NULL,
    url TEXT NOT NULL,
    payload TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',   -- pending|in_flight|delivered|dead
    attempts INTEGER NOT NULL DEFAULT 0,
    next_attempt_at REAL NOT NULL,
    lease_until REAL,
    last_error TEXT,
    created_at REAL NOT NULL,
    delivered_at REAL
);
CREATE INDEX IF NOT EXISTS ix_outbox_due ON webhook_outbox(status, next_attempt_at);
"""


def connect(path):
    conn = sqlite3.connect(path, timeout=10, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA busy_timeout=10000")
    return conn


def init_schema(conn):
    conn.executescript(SCHEMA)


def enqueue(conn, order_id, url, payload, now=None):
    """Insert a pending webhook using the CALLER's connection/transaction."""
    wid = str(uuid.uuid4())
    now = time.time() if now is None else now
    conn.execute(
        "INSERT INTO webhook_outbox(id, order_id, url, payload, next_attempt_at, created_at)"
        " VALUES (?,?,?,?,?,?)",
        (wid, order_id, url, json.dumps(payload), now, now),
    )
    return wid


def claim_due(conn, limit, lease_seconds, skip_urls=(), now=None):
    """Atomically claim due rows (pending, or in_flight with expired lease)."""
    now = time.time() if now is None else now
    conn.execute("BEGIN IMMEDIATE")
    try:
        rows = conn.execute(
            "SELECT * FROM webhook_outbox WHERE"
            " ((status='pending' AND next_attempt_at<=?) OR (status='in_flight' AND lease_until<=?))"
            " ORDER BY next_attempt_at LIMIT ?",
            (now, now, limit + len(skip_urls) * 50),
        ).fetchall()
        picked, seen_skip = [], set(skip_urls)
        for r in rows:
            if r["url"] in seen_skip:
                continue
            picked.append(r)
            if len(picked) >= limit:
                break
        for r in picked:
            conn.execute(
                "UPDATE webhook_outbox SET status='in_flight', lease_until=? WHERE id=?",
                (now + lease_seconds, r["id"]),
            )
        conn.execute("COMMIT")
    except BaseException:
        conn.execute("ROLLBACK")
        raise
    return picked


def mark_delivered(conn, wid, now=None):
    now = time.time() if now is None else now
    conn.execute(
        "UPDATE webhook_outbox SET status='delivered', attempts=attempts+1, delivered_at=?,"
        " lease_until=NULL, last_error=NULL WHERE id=?", (now, wid))


def backoff_delay(attempt, base=2.0, cap=900.0, rng=random):
    d = min(base * (2 ** (attempt - 1)), cap)
    return d * rng.uniform(0.8, 1.2)


def mark_failed(conn, wid, error, max_attempts, base=2.0, cap=900.0, now=None):
    """Record a failed attempt. Returns ('pending'|'dead', next_attempt_at)."""
    now = time.time() if now is None else now
    row = conn.execute("SELECT attempts FROM webhook_outbox WHERE id=?", (wid,)).fetchone()
    attempts = row["attempts"] + 1
    if attempts >= max_attempts:
        status, nxt = "dead", now
    else:
        status, nxt = "pending", now + backoff_delay(attempts, base, cap)
    conn.execute(
        "UPDATE webhook_outbox SET status=?, attempts=?, next_attempt_at=?, lease_until=NULL,"
        " last_error=? WHERE id=?", (status, attempts, nxt, str(error)[:500], wid))
    return status, nxt


def requeue_dead(conn, now=None):
    now = time.time() if now is None else now
    cur = conn.execute(
        "UPDATE webhook_outbox SET status='pending', attempts=0, next_attempt_at=? WHERE status='dead'",
        (now,))
    return cur.rowcount


def stats(conn):
    out = {"pending": 0, "in_flight": 0, "delivered": 0, "dead": 0}
    for r in conn.execute("SELECT status, COUNT(*) c FROM webhook_outbox GROUP BY status"):
        out[r["status"]] = r["c"]
    return out
