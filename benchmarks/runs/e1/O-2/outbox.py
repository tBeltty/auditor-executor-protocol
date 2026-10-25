"""Transactional outbox for webhooks, stored in the same SQLite file as orders."""
import sqlite3
import time
from urllib.parse import urlsplit

SCHEMA = """
CREATE TABLE IF NOT EXISTS webhook_outbox (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    url TEXT NOT NULL,
    host TEXT NOT NULL,
    payload TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',   -- pending | inflight | done | dead
    attempts INTEGER NOT NULL DEFAULT 0,
    next_attempt_at REAL NOT NULL,
    lease_until REAL NOT NULL DEFAULT 0,
    last_error TEXT,
    created_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_outbox_due ON webhook_outbox(status, next_attempt_at);
"""


def connect(path):
    conn = sqlite3.connect(path, timeout=5.0, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


def init_schema(path):
    conn = connect(path)
    try:
        conn.executescript(SCHEMA)
    finally:
        conn.close()


def enqueue(conn, order_id, url, payload, now=None):
    """Insert a row using the caller's connection, so it commits with the caller's transaction."""
    now = time.time() if now is None else now
    host = urlsplit(url).netloc.lower()
    cur = conn.execute(
        "INSERT INTO webhook_outbox(order_id,url,host,payload,next_attempt_at,created_at)"
        " VALUES(?,?,?,?,?,?)",
        (order_id, url, host, payload, now, now),
    )
    return cur.lastrowid


class Outbox:
    def __init__(self, path, lease_seconds=30.0):
        self.path = path
        self.lease_seconds = lease_seconds

    def claim(self, limit, exclude_hosts=(), now=None):
        """Atomically lease up to `limit` due rows. Expired leases are reclaimed (crash recovery)."""
        now = time.time() if now is None else now
        conn = connect(self.path)
        try:
            conn.execute("BEGIN IMMEDIATE")
            marks = ",".join("?" * len(exclude_hosts))
            excl = f" AND host NOT IN ({marks})" if exclude_hosts else ""
            rows = conn.execute(
                "SELECT * FROM webhook_outbox WHERE "
                "((status='pending' AND next_attempt_at<=?) OR (status='inflight' AND lease_until<?))"
                + excl + " ORDER BY next_attempt_at LIMIT ?",
                (now, now, *exclude_hosts, limit),
            ).fetchall()
            for r in rows:
                conn.execute(
                    "UPDATE webhook_outbox SET status='inflight', lease_until=? WHERE id=?",
                    (now + self.lease_seconds, r["id"]),
                )
            conn.execute("COMMIT")
            return [dict(r) for r in rows]
        except Exception:
            try:
                conn.execute("ROLLBACK")
            except sqlite3.Error:
                pass
            raise
        finally:
            conn.close()

    def _update(self, sql, args):
        conn = connect(self.path)
        try:
            conn.execute(sql, args)
        finally:
            conn.close()

    def mark_done(self, row_id):
        self._update("UPDATE webhook_outbox SET status='done', attempts=attempts+1 WHERE id=?", (row_id,))

    def mark_retry(self, row_id, next_at, error):
        self._update(
            "UPDATE webhook_outbox SET status='pending', attempts=attempts+1, next_attempt_at=?, last_error=? WHERE id=?",
            (next_at, error, row_id),
        )

    def mark_dead(self, row_id, error):
        self._update(
            "UPDATE webhook_outbox SET status='dead', attempts=attempts+1, last_error=? WHERE id=?",
            (error, row_id),
        )

    def counts(self):
        conn = connect(self.path)
        try:
            return {r["status"]: r["n"] for r in conn.execute(
                "SELECT status, COUNT(*) n FROM webhook_outbox GROUP BY status")}
        finally:
            conn.close()
