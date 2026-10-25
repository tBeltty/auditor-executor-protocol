"""Order confirmation: writes order + webhook in one transaction; never touches the network."""
from outbox import Outbox


class Orders:
    def __init__(self, outbox):
        self.outbox = outbox
        c = outbox.conn()
        c.execute("CREATE TABLE IF NOT EXISTS orders(id TEXT PRIMARY KEY, status TEXT NOT NULL, webhook_url TEXT)")

    def create(self, order_id, webhook_url):
        self.outbox.conn().execute("INSERT INTO orders VALUES(?,?,?)", (order_id, "new", webhook_url))

    def confirm_order(self, order_id):
        c = self.outbox.conn()
        c.execute("BEGIN IMMEDIATE")
        try:
            row = c.execute("SELECT webhook_url FROM orders WHERE id=?", (order_id,)).fetchone()
            if row is None:
                raise KeyError(order_id)
            c.execute("UPDATE orders SET status='confirmed' WHERE id=?", (order_id,))
            if row[0]:
                self.outbox.enqueue(row[0], {"event": "order.confirmed", "order_id": order_id}, conn=c)
            c.execute("COMMIT")
        except BaseException:
            c.execute("ROLLBACK")
            raise
