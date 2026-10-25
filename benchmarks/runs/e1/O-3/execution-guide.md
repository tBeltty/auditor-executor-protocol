# Execution guide

TASK 1: Create outbox.py with the webhook_outbox schema (WAL, busy timeout) and transactional enqueue(); verify: python3 -m unittest test_outbox.TestEnqueue -v
TASK 2: Add burst benchmark test (100/s, concurrent dispatchers, slow endpoint) asserting enqueue p99 < 1.5 s and no lost rows; verify: python3 -m unittest test_outbox.TestBurst -v
TASK 3: Implement claim/mark-delivered/retry with exponential backoff and max attempts; verify: python3 -m unittest test_outbox.TestDelivery -v
TASK 4: Implement stale-claim recovery after crash and the per-URL circuit breaker; verify: python3 -m unittest test_outbox.TestRecovery -v
TASK 5: Implement Dispatcher thread pool and HTTP sender (urllib, timeout) ; verify: python3 -m unittest test_outbox.TestDispatcher -v
TASK 6: Add confirm_order() integration showing confirmation latency independent of a hanging endpoint; verify: python3 -m unittest test_outbox.TestConfirmOrder -v
TASK 7: Run the whole suite; verify: python3 -m unittest discover -s /tmp/aep-lab/runs/e1/O-3
