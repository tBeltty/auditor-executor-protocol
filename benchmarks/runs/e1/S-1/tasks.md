TASK 1: Create schema (orders, webhook_outbox) and connection helper with WAL and busy_timeout.
TASK 2: Implement confirm_order writing order update and outbox row in one transaction.
TASK 3: Implement outbox claim with BEGIN IMMEDIATE and lease expiry recovery.
TASK 4: Implement delivery outcome handling: delivered, retry with exponential backoff and jitter, dead after max attempts.
TASK 5: Implement threaded Dispatcher with injectable sender and default urllib sender (timeout 3 s, Idempotency-Key header).
TASK 6: Write unittest tests for AC1 to AC6 and run discover until green.
