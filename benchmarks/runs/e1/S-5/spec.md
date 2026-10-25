# Spec: Asynchronous order-confirmation webhooks

## Problem
Webhook HTTP call runs inside the confirm request. A customer endpoint timeout (10 s) blocks worker threads; p99 confirmation latency is 14.2 s.

## Functional requirements
- FR1: Confirming an order must not perform any customer HTTP call in the request path.
- FR2: Confirming an order records the webhook intent durably in the same SQLite transaction as the order status change (transactional outbox). Either both persist or neither.
- FR3: A background dispatcher inside the monolith delivers pending webhooks with a bounded worker pool.
- FR4: Failed deliveries (timeout, connection error, non-2xx) are retried with exponential backoff and jitter, up to a configurable maximum; after that the row is marked `dead` and stays in the table (never deleted) for manual replay.
- FR5: Delivery is at-least-once. Each request carries a stable `X-Webhook-Id` header (idempotency key) so customers can deduplicate.
- FR6: A crash while a delivery is in flight must not lose it: leases expire and the row is re-claimed.
- FR7: Operators can query counts by status and replay dead rows.

## User stories
- As a shop customer, I want my order confirmation to return quickly even when the merchant's endpoint is down.
- As a merchant, I want every order-confirmed event delivered at least once, with an id to deduplicate.
- As an operator, I want undeliverable events kept and replayable.

## Acceptance criteria
- AC1: With a customer endpoint that hangs, confirm_order p99 over 1000 calls (burst of 100/s style) is < 1.5 s (target: a few ms).
- AC2: Order status and outbox row are atomic (rollback leaves neither).
- AC3: A webhook failing N times then succeeding is delivered exactly once successfully and marked `delivered`.
- AC4: A row left `in_progress` with an expired lease is delivered after dispatcher start.
- AC5: Rows exceeding max attempts become `dead`, not deleted; `replay_dead` makes them pending again.
- AC6: No webhook lost: after a burst of 1000 confirmations against a healthy endpoint, all 1000 are delivered.
- AC7: No new services or dependencies (stdlib + SQLite only).
