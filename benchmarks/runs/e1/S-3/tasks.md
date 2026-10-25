TASK 1: Create outbox.py with schema (WAL pragmas) and enqueue/claim/mark/requeue/stats functions.
TASK 2: Create orders.py with confirm_order writing order update and outbox row in one transaction.
TASK 3: Create dispatcher.py with worker threads, HTTP POST, backoff with jitter, per-URL cooldown, lease recovery.
TASK 4: Write test_outbox.py (atomicity, claim exclusivity, dead/requeue, lease recovery).
TASK 5: Write test_dispatcher.py (delivery, retry then success, headers, burst of 1000 with no loss).
TASK 6: Write test_orders_latency.py (hanging endpoint, p99 < 1.5 s).
TASK 7: Run python3 -m unittest discover -s D until all pass.
