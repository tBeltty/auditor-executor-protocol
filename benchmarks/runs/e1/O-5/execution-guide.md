# Execution guide

TASK 1: Outbox store (schema, WAL, enqueue in caller transaction, claim with lease, mark delivered/retry/dead) and a concurrent load test of 1,000 enqueues at 100/s while claiming; verify: python3 -m unittest test_outbox -v
TASK 2: Dispatcher (thread pool, short timeout, exponential backoff, dead state, lease recovery after crash); verify: python3 -m unittest test_dispatcher -v
TASK 3: confirm_order integration (order update plus outbox insert in one transaction, no HTTP in the request) and an end-to-end test against a local endpoint that hangs; verify: python3 -m unittest test_confirm -v
TASK 4: Full suite; verify: python3 -m unittest discover -s /tmp/aep-lab/runs/e1/O-5
