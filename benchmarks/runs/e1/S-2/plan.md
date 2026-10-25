# Technical plan

## Approach: transactional outbox on the existing SQLite file
No broker, Redis or containers exist, so the outbox is a table in the application database, drained by in-process threads.

1. Table `webhook_outbox(id, order_id, url, payload, status, attempts, next_attempt_at, locked_until, last_error, created_at)`; index on (status, next_attempt_at).
2. `confirm_order` updates the order and inserts the outbox row in one transaction (atomic, no lost webhook, no HTTP in request path).
3. `Dispatcher`: N worker threads (default 32) poll, claim rows by setting `status='in_flight'` and `locked_until=now+lease` inside a `BEGIN IMMEDIATE` transaction, then POST with a 3 s timeout (below the customer's 10 s so threads recycle faster).
4. Success (2xx) -> `delivered`. Failure -> `pending` with `next_attempt_at = now + min(cap, base*2^attempts) * jitter`; after `max_attempts` -> `dead`.
5. Expired leases (`in_flight` and `locked_until < now`) are claimable again, giving crash recovery.
6. Per-URL cap on in-flight deliveries (default 4) so a hanging endpoint occupies only a few threads.
7. SQLite in WAL mode with busy_timeout; each thread uses its own connection. Writes are tiny, which suits 100/s.

## Capacity
Fast endpoints: 32 threads at ~100 ms is ~300/s, above the 100/s burst. Hanging endpoints are bounded by the per-URL cap, and backlog is persisted, so latency of confirmation is unaffected.

## Risks
- Duplicate deliveries after crash or timeout-but-processed: mitigated by `X-Webhook-Id`.
- Many distinct hanging URLs could still occupy threads: pool size is configurable.
- Single process only; multi-process works too because claims are transactional.

## Files
outbox.py (store + dispatcher), orders.py (confirm_order), test_*.py.

NEW_INFRA: none
