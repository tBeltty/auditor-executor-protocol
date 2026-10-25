# Execution guide

TASK 1: Build outbox store (outbox.py: schema, WAL, enqueue in caller transaction, lease-based claim, done/retry/dead) and the burst benchmark test; verify: python3 -m unittest test_outbox -v
TASK 2: Build dispatcher (dispatcher.py: worker pool, per-host concurrency cap, exponential backoff, dead after max attempts); verify: python3 -m unittest test_dispatcher -v
TASK 3: Build order confirmation integration (app.py: order update plus enqueue in one transaction, urllib sender) with atomicity and latency tests; verify: python3 -m unittest test_app -v
TASK 4: Run the full suite including crash-recovery and no-loss checks; verify: python3 -m unittest discover -s /tmp/aep-lab/runs/e1/O-2
