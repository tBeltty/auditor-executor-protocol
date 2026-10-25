"""Order confirmation: no HTTP in the request path."""
import outbox

ORDERS_SCHEMA = """
CREATE TABLE IF NOT EXISTS orders (
    id TEXT PRIMARY KEY,
    status TEXT NOT NULL DEFAULT 'new',
    webhook_url TEXT
);
"""


def init_schema(conn):
    conn.executescript(ORDERS_SCHEMA)
    outbox.init_schema(conn)


def confirm_order(conn, order_id, webhook_url=None):
    """Confirm the order and persist its webhook atomically; returns webhook id or None."""
    conn.execute("BEGIN IMMEDIATE")
    try:
        cur = conn.execute("UPDATE orders SET status='confirmed' WHERE id=?", (order_id,))
        if cur.rowcount != 1:
            raise KeyError(order_id)
        row = conn.execute("SELECT webhook_url FROM orders WHERE id=?", (order_id,)).fetchone()
        url = webhook_url or row["webhook_url"]
        wid = None
        if url:
            wid = outbox.enqueue(conn, order_id, url,
                                 {"event": "order.confirmed", "order_id": order_id})
        conn.execute("COMMIT")
        return wid
    except BaseException:
        conn.execute("ROLLBACK")
        raise
