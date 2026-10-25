TASK 1: Create schema and init_db (orders, webhook_outbox, WAL, index).
TASK 2: Implement confirm_order with atomic order update and outbox insert.
TASK 3: Implement claim logic with leases (including expired lease recovery).
TASK 4: Implement Dispatcher with worker pool, delivery, backoff with jitter, dead state.
TASK 5: Implement stats and replay_dead.
TASK 6: Write unittest tests for AC1-AC6 using a local stub HTTP server.
TASK 7: Run python3 -m unittest discover -s D until all pass.
