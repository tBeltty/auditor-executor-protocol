# Execution guide

TASK 1: Outbox store (outbox.py): SQLite WAL schema, enqueue, claim, mark done/retry/dead, stale-claim recovery; validates the riskiest assumption with a concurrency/latency test. Verify: python3 -m unittest test_outbox -v
TASK 2: Dispatcher (dispatcher.py): bounded thread pool, short timeout HTTP POST with idempotency header, exponential backoff, dead state after max attempts. Verify: python3 -m unittest test_dispatcher -v
TASK 3: Order confirmation integration (orders.py): confirm_order writes order and webhook in one transaction, no network call. Verify: python3 -m unittest test_orders -v
TASK 4: Load test with a hanging endpoint at 100/s burst: p99 under 1.5 s and no loss after recovery. Verify: python3 -m unittest test_load -v
TASK 5: Full suite. Verify: python3 -m unittest discover -s /tmp/aep-lab/runs/e1/O-4
