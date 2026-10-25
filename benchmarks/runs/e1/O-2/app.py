"""Order confirmation: order update and webhook enqueue share one transaction."""
import json
import time
import urllib.request

import outbox


def init_db(path):
    conn = outbox.connect(path)
    try:
        conn.execute("CREATE TABLE IF NOT EXISTS orders(id INTEGER PRIMARY KEY, status TEXT NOT NULL, webhook_url TEXT)")
    finally:
        conn.close()
    outbox.init_schema(path)


def confirm_order(path, order_id, fail_after_enqueue=False):
    """Confirm an order. No network I/O happens here."""
    conn = outbox.connect(path)
    try:
        conn.execute("BEGIN IMMEDIATE")
        try:
            row = conn.execute("SELECT webhook_url FROM orders WHERE id=?", (order_id,)).fetchone()
            if row is None:
                raise KeyError(order_id)
            conn.execute("UPDATE orders SET status='confirmed' WHERE id=?", (order_id,))
            if row["webhook_url"]:
                body = json.dumps({"event": "order.confirmed", "order_id": order_id, "ts": time.time()})
                outbox.enqueue(conn, order_id, row["webhook_url"], body)
            if fail_after_enqueue:
                raise RuntimeError("simulated failure")
            conn.execute("COMMIT")
        except BaseException:
            conn.execute("ROLLBACK")
            raise
    finally:
        conn.close()


def http_sender(timeout=10.0):
    def send(row):
        req = urllib.request.Request(
            row["url"], data=row["payload"].encode(), method="POST",
            headers={"Content-Type": "application/json", "X-Webhook-Id": str(row["id"])})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if not 200 <= resp.status < 300:
                raise RuntimeError(f"HTTP {resp.status}")
    return send
