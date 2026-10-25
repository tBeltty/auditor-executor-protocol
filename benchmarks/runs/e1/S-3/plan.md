# Technical plan

## Approach: transactional outbox on the existing SQLite database
1. `confirm_order` updates the order and inserts a row into `webhook_outbox` in one transaction, then returns. Cost is one local insert (sub-millisecond to a few ms), independent of the customer endpoint.
2. An in-process `Dispatcher` (daemon threads in the same monolith) polls the table, claims due rows (`pending` -> `in_flight` with a lease), POSTs with a 5 s timeout, and marks `delivered`, reschedules with backoff, or marks `dead`.
3. At-least-once semantics: the row is marked delivered only after a 2xx. `X-Webhook-Id` supports customer-side dedupe.

## Why this fits the constraints
- No broker, Redis or containers are available; SQLite is already the durable store, so the outbox gives durability and atomicity with the order write for free.
- Capacity: 100/s burst for 10 s = 1000 rows; inserts are cheap. If the endpoint hangs, a pool of 32 worker threads with 5 s timeout drains at most ~6/s per hanging URL, so a per-URL cooldown (after a failure the URL is skipped until its next retry time) stops one bad URL from consuming all workers. Backlog persists on disk, not in memory.
- SQLite settings: WAL, `busy_timeout`, `synchronous=NORMAL`, one connection per thread; claims use `BEGIN IMMEDIATE` so two dispatchers never claim the same row.

## Modules
- `outbox.py`: schema, `enqueue`, `claim_due`, `mark_delivered`, `mark_failed`, `requeue_dead`, `stats`.
- `dispatcher.py`: worker threads, HTTP sender (urllib), backoff, per-URL cooldown, lease recovery.
- `orders.py`: `confirm_order` (order update + enqueue in one transaction).
- Tests: `test_outbox.py`, `test_dispatcher.py`, `test_orders_latency.py` using a local `http.server` fake customer.

## Retry policy
delay = min(base * 2^(attempt-1), cap) with +-20% jitter; base 2 s, cap 15 min, max attempts 12 (about 1 day). Lease 30 s (> HTTP timeout).

## Risks
- Duplicates on crash between 2xx and DB update: accepted, mitigated by `X-Webhook-Id`.
- SQLite single writer: writes are tiny; revisit if throughput exceeds ~1000/s.

NEW_INFRA: none
