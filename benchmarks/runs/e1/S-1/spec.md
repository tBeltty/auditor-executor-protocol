# Spec: Reliable asynchronous order webhooks

## Problem
Order confirmation calls the customer webhook synchronously. A customer endpoint timeout (10 s) blocks worker threads and pushes p99 confirmation latency to 14.2 s.

## Functional requirements
- FR1: Confirming an order must not perform any outbound HTTP call in the request path.
- FR2: The webhook event is persisted in the same SQLite transaction as the order state change (all or nothing).
- FR3: A background dispatcher delivers persisted events to the customer URL.
- FR4: Failed deliveries (timeout, connection error, non-2xx) are retried with exponential backoff and jitter.
- FR5: Delivery is at-least-once. Each request carries a stable `Idempotency-Key` (event id) so customers can deduplicate.
- FR6: Events survive process crashes: an event claimed by a dead worker becomes claimable again after a lease expires.
- FR7: Events that exhaust retries move to status `dead` and stay in the table for inspection and manual replay. Nothing is deleted.
- FR8: Outbound timeout is configurable and shorter than 10 s (default 3 s).
- FR9: Sustained 40 events/s and bursts of 100 events/s for 10 s are absorbed (queue grows, nothing dropped).

## User stories
- As a customer integrator, I receive a POST for every confirmed order, even if my endpoint was down, and I can deduplicate by `Idempotency-Key`.
- As a shopper, order confirmation returns quickly no matter how slow the merchant's webhook endpoint is.
- As an operator, I can query the outbox to see pending, failed and dead events.

## Acceptance criteria
- AC1: With a sender that blocks for the full timeout, p99 of `confirm_order` stays under 1.5 s (tests assert far lower).
- AC2: After confirming N orders under concurrency (burst of 100), the outbox holds exactly N events and, once the dispatcher drains, all N are `delivered`.
- AC3: A sender failing K times then succeeding yields one `delivered` event with attempts = K+1.
- AC4: An event left `in_flight` with an expired lease is redelivered.
- AC5: An event that always fails ends as `dead` and is still in the table.
- AC6: A rollback of the order transaction leaves no outbox row.
