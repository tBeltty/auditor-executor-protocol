# Technical plan

## Approach
Transactional outbox in the existing SQLite database plus an in-process dispatcher (thread pool). No broker, Redis, or container is needed.

## Components
- `webhooks.py`
  - `init_db(conn)`: creates `orders` (demo) and `webhook_outbox(id, order_id, url, payload, status, attempts, next_attempt_at, lease_until, last_error, created_at)` with an index on (status, next_attempt_at). WAL mode, busy_timeout.
  - `confirm_order(db_path, order_id, url)`: one transaction: update order, insert outbox row. Returns in milliseconds.
  - `Dispatcher`: a poller thread claims due rows (`pending` with next_attempt_at <= now, or `in_progress` with expired lease) via `UPDATE ... RETURNING`-style claim in a `BEGIN IMMEDIATE` transaction, sets a lease, and submits them to a `ThreadPoolExecutor` (default 32 workers, timeout 10 s per call). Result handling: 2xx -> `delivered`; otherwise attempts+1 and next_attempt_at = now + min(cap, base*2^n) with jitter; attempts >= max -> `dead`.
  - `replay_dead`, `stats`.
- Each thread uses its own sqlite3 connection (SQLite is single-writer; writes are tiny).

## Capacity
40/s steady, 100/s bursts for 10 s = 1000 inserts, trivial for SQLite WAL. If the endpoint hangs, 32 workers deliver at 3.2/s; backlog sits durably in the table and the claim batch is limited to free worker slots, so memory is bounded. Worker count is configurable.

## Reliability
At-least-once; duplicates possible after crash or lease expiry (lease = timeout + margin), mitigated by `X-Webhook-Id`. Dead rows retained.

## Testing
unittest with a local `http.server` stub (healthy, hanging, flaky) covering AC1-AC6.

NEW_INFRA: none
