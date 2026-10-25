# Technical plan

## Approach: transactional outbox on the existing SQLite file
- Table `webhook_outbox(id, order_id, url, payload, status, attempts, next_attempt_at, lease_until, last_error, created_at, delivered_at)`.
- `confirm_order()` updates the order and inserts the outbox row in one transaction, then returns. No network I/O.
- `Dispatcher` runs in-process daemon threads (a pool of N workers, default 32). Each loop: claim a batch with `BEGIN IMMEDIATE` (select due rows with `status IN ('pending','in_flight' with expired lease)`, set `in_flight` and `lease_until = now + lease`), send, then mark `delivered`, or reschedule with backoff `min(cap, base * 2^attempts) * jitter`, or mark `dead` after `max_attempts`.
- Sender is injectable (`urllib.request` by default, timeout 3 s) so tests need no network.
- SQLite in WAL mode, `busy_timeout`, one connection per thread. Writes are tiny, so 100/s is well within SQLite capacity.

## Why not alternatives
- Broker/Redis/Celery: would add infrastructure the team does not run; the outbox in the existing DB gives the durability needed.
- Plain in-memory thread pool: loses events on crash, violating "no webhook lost".

## Risks
- A fully hung endpoint occupies workers for the timeout: 100/s x 3 s needs about 300 concurrent sends for a worst case where every target hangs. Mitigation: pool size configurable, backoff lets healthy endpoints proceed first because rows are ordered by `next_attempt_at`. Per-endpoint circuit breaking is future work.
- At-least-once means duplicates are possible; mitigated by `Idempotency-Key`.
- Single process dispatcher; multiple processes are safe because claims use `BEGIN IMMEDIATE` plus leases.

## Testing
unittest: latency under hung sender, burst of 100 concurrent confirms, retry/backoff, lease recovery, dead letter, rollback atomicity.

NEW_INFRA: none
