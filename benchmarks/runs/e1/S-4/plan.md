# Technical plan

Pattern: transactional outbox plus in-process dispatcher, all on the existing SQLite file.

- Table `webhook_outbox(id, order_id, url, payload, status, attempts, next_attempt_at, lease_until, last_error, created_at)`; statuses `pending`, `in_flight`, `delivered`, `dead`. Index on (status, next_attempt_at).
- `confirm_order(conn, ...)` writes the order and the outbox row in one transaction; the request returns after commit (a local insert, milliseconds).
- `Dispatcher` runs a poller thread plus a bounded worker pool (`ThreadPoolExecutor`, default 32 workers). The poller atomically claims due rows (`UPDATE ... status='in_flight', lease_until=now+lease` inside `BEGIN IMMEDIATE`), then submits them. Backlog lives in the DB, so bursts of 100/s only grow the queue; they never block requests.
- Sender uses `urllib.request` with a 5 s timeout, JSON body, `Idempotency-Key` header. 2xx = success; anything else or exception = failure.
- Retry: delay = min(base * 2^attempts, cap) with jitter; max 8 attempts then `dead`.
- Crash recovery: claim query also selects `in_flight` rows whose lease expired.
- SQLite: WAL mode, busy_timeout, one connection per thread (a connection factory).
- Capacity note: 40/s steady with 10 s timeouts needs about 400 concurrent slots in the worst case where every endpoint is dead; with the pool of 32 the backlog drains once endpoints recover, and a healthy endpoint answers in well under a second. Pool size is configurable.
- Delivery semantics: at-least-once, deduplicated by Idempotency-Key.

NEW_INFRA: none
