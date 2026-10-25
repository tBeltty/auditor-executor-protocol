# Spec: Reliable asynchronous order webhooks

## Problem
Order confirmation calls the customer webhook synchronously. When the customer endpoint times out (10 s), request threads block and p99 confirmation latency reaches 14.2 s.

## Functional requirements
- FR1: Confirming an order must never perform the customer HTTP call in the request path.
- FR2: The webhook intent is persisted in the same SQLite transaction that confirms the order (all or nothing).
- FR3: A background dispatcher delivers persisted webhooks over HTTP POST (JSON body) with a bounded timeout.
- FR4: Failed deliveries (timeout, connection error, non-2xx) are retried with exponential backoff and jitter, up to a configurable maximum.
- FR5: Webhooks that exhaust retries are kept as `dead` (never deleted) and can be requeued manually.
- FR6: Delivery survives process crash and restart: undelivered rows are picked up again, including rows left `in_flight` after a crash (lease expiry).
- FR7: Each delivery carries a stable `X-Webhook-Id` header so customers can deduplicate (delivery is at-least-once).
- FR8: A slow or failing customer URL must not starve deliveries to other URLs (per-URL cooldown).
- FR9: Sustain 40 webhooks/s, with bursts of 100/s for 10 s, without loss; backlog drains after the burst.

## User stories
- US1: As a shopper, I get an order confirmation in under 1.5 s (p99) even if the merchant's endpoint is down.
- US2: As a merchant, I receive every confirmed order's webhook at least once, even after outages on my side or a server restart.
- US3: As an operator, I can see pending/dead counts and requeue dead webhooks.

## Acceptance criteria
- AC1: With a customer endpoint that hangs, 200 order confirmations complete with p99 < 1.5 s (test measures; expected in the low milliseconds).
- AC2: Order row and outbox row are committed atomically; a failure inside the transaction leaves neither.
- AC3: An endpoint failing N times then succeeding receives the webhook; attempts are recorded.
- AC4: After simulated crash (rows `in_flight` with expired lease), a new dispatcher delivers them.
- AC5: Burst of 1000 confirmations at >=100/s enqueues with zero loss and all are eventually delivered to a healthy endpoint.
- AC6: Exhausted webhooks end `dead`, not deleted; `requeue_dead` makes them deliverable again.
- AC7: No new infrastructure beyond Python stdlib and the existing SQLite file.
