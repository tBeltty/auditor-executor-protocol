TASK 1: Create outbox schema and connection helper (WAL, busy_timeout) in outbox.py.
TASK 2: Implement enqueue(conn, ...) usable inside the caller's transaction.
TASK 3: Implement transactional claim with lease and per-URL in-flight cap.
TASK 4: Implement delivery, success/failure marking, backoff with jitter, dead state, replay_dead.
TASK 5: Implement Dispatcher with worker threads and clean stop.
TASK 6: Implement confirm_order in orders.py that writes order and outbox atomically with no HTTP.
TASK 7: Write unittest tests for latency, atomicity, retry, crash recovery, burst, dead/replay.
TASK 8: Run python3 -m unittest discover -s D until green.
