import outbox


def confirm_order(conn, order_id, url, payload=None):
    """Confirm an order and record the webhook in ONE transaction. No HTTP here."""
    conn.execute("BEGIN IMMEDIATE")
    try:
        conn.execute("INSERT OR REPLACE INTO orders(id,status,webhook_url)"
                     " VALUES(?,?,?)", (order_id, "confirmed", url))
        outbox.enqueue(conn, order_id, url,
                       payload or {"event": "order.confirmed", "order_id": order_id})
        conn.execute("COMMIT")
    except BaseException:
        conn.execute("ROLLBACK")
        raise
