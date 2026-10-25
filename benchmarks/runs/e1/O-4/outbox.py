"""Transactional webhook outbox on SQLite (WAL)."""
import json
import sqlite3
import threading
import time
import uuid

SCHEMA = """
CREATE TABLE IF NOT EXISTS webhook_outbox (
    id TEXT PRIMARY KEY,
    url TEXT NOT NULL,
    payload TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',   -- pending | in_flight | done | dead
    attempts INTEGER NOT NULL DEFAULT 0,
    next_attempt_at REAL NOT NULL,
    claimed_at REAL,
    last_error TEXT,
    created_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_outbox_due ON webhook_outbox(status, next_attempt_at);
"""


def connect(path):
    conn = sqlite3.connect(path, timeout=30, isolation_level=None, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA busy_timeout=30000")
    return conn


class Outbox:
    def __init__(self, path):
        self.path = path
        self._local = threading.local()
        c = self.conn()
        c.executescript(SCHEMA)

    def conn(self):
        c = getattr(self._local, "c", None)
        if c is None:
            c = self._local.c = connect(self.path)
        return c

    def enqueue(self, url, payload, conn=None, now=None):
        """Insert a webhook row. Pass the caller's connection to share its transaction."""
        now = time.time() if now is None else now
        wid = uuid.uuid4().hex
        (conn or self.conn()).execute(
            "INSERT INTO webhook_outbox(id,url,payload,next_attempt_at,created_at) VALUES(?,?,?,?,?)",
            (wid, url, json.dumps(payload), now, now))
        return wid

    def claim(self, limit=1, now=None):
        now = time.time() if now is None else now
        c = self.conn()
        c.execute("BEGIN IMMEDIATE")
        try:
            rows = c.execute(
                "SELECT id,url,payload,attempts FROM webhook_outbox "
                "WHERE status='pending' AND next_attempt_at<=? ORDER BY next_attempt_at LIMIT ?",
                (now, limit)).fetchall()
            for r in rows:
                c.execute("UPDATE webhook_outbox SET status='in_flight',claimed_at=? WHERE id=?", (now, r[0]))
            c.execute("COMMIT")
        except BaseException:
            c.execute("ROLLBACK")
            raise
        return [{"id": r[0], "url": r[1], "payload": json.loads(r[2]), "attempts": r[3]} for r in rows]

    def mark_done(self, wid):
        self.conn().execute(
            "UPDATE webhook_outbox SET status='done',attempts=attempts+1,claimed_at=NULL WHERE id=?", (wid,))

    def mark_failed(self, wid, error, max_attempts, backoff_base, now=None):
        now = time.time() if now is None else now
        c = self.conn()
        attempts = c.execute("SELECT attempts FROM webhook_outbox WHERE id=?", (wid,)).fetchone()[0] + 1
        if attempts >= max_attempts:
            c.execute("UPDATE webhook_outbox SET status='dead',attempts=?,last_error=?,claimed_at=NULL WHERE id=?",
                      (attempts, error, wid))
        else:
            delay = backoff_base * (2 ** (attempts - 1))
            c.execute("UPDATE webhook_outbox SET status='pending',attempts=?,last_error=?,claimed_at=NULL,"
                      "next_attempt_at=? WHERE id=?", (attempts, error, now + delay, wid))

    def recover_stale(self, stale_after, now=None):
        """Return rows left in_flight by a crashed process to pending."""
        now = time.time() if now is None else now
        cur = self.conn().execute(
            "UPDATE webhook_outbox SET status='pending',claimed_at=NULL "
            "WHERE status='in_flight' AND claimed_at<=?", (now - stale_after,))
        return cur.rowcount

    def counts(self):
        return dict(self.conn().execute("SELECT status,COUNT(*) FROM webhook_outbox GROUP BY status").fetchall())
