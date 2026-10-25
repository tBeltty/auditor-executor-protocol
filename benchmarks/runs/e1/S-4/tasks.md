TASK 1: Create outbox schema and connection factory (WAL, busy_timeout) in webhooks.py.
TASK 2: Implement enqueue and confirm_order writing order + outbox row in one transaction.
TASK 3: Implement atomic claim with leases, including reclaim of expired leases.
TASK 4: Implement HTTP sender with timeout and Idempotency-Key header.
TASK 5: Implement retry with exponential backoff and dead state after max attempts.
TASK 6: Implement Dispatcher (poller thread plus worker pool) with start/stop.
TASK 7: Write unittest tests covering AC1 to AC6 and run them.
