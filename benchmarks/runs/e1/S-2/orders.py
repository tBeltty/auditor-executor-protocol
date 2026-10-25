import outbox


def init_db(conn):
    conn.execute("CREATE TABLE IF NOT EXISTS orders("
                 "id INTEGER PRIMARY KEY, status TEXT NOT NULL, webhook_url TEXT)")
    outbox.init_schema(conn)


def confirm_order(conn, order_id):
    """Confirm an order and enqueue its webhook atomically. No network I/O."""
    conn.execute("BEGIN IMMEDIATE")
    try:
        row = conn.execute("SELECT webhook_url FROM orders WHERE id=?",
                           (order_id,)).fetchone()
        if row is None:
            raise KeyError(order_id)
        conn.execute("UPDATE orders SET status='confirmed' WHERE id=?", (order_id,))
        if row[0]:
            outbox.enqueue(conn, order_id, row[0],
                           {"event": "order.confirmed", "order_id": order_id})
        conn.execute("COMMIT")
    except BaseException:
        conn.execute("ROLLBACK")
        raise
