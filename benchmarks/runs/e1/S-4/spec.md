# Spec: Asynchronous order-confirmation webhooks

## Functional requirements
- FR1: Confirming an order must not perform the customer HTTP call in the request path.
- FR2: The webhook is recorded durably (SQLite) in the same transaction that confirms the order. If the confirmation rolls back, no webhook exists; if it commits, the webhook exists.
- FR3: A background dispatcher in the same process delivers pending webhooks, retrying failures with exponential backoff.
- FR4: Delivery is at-least-once; each request carries a stable `Idempotency-Key` (webhook id) so customers can deduplicate.
- FR5: Webhooks interrupted by a crash (leased but unfinished) are re-delivered after the lease expires.
- FR6: After the maximum attempts a webhook becomes `dead` and stays in the table for inspection and manual replay; it is never deleted.
- FR7: A slow customer endpoint must not delay other deliveries beyond the worker pool limits, and must never delay order confirmation.

## User stories
- As a shop operator, I want order confirmation to return fast even when a customer endpoint is down.
- As a customer integrator, I want every confirmed order to eventually reach my URL, with an id to deduplicate retries.
- As an on-call engineer, I want undeliverable webhooks kept and queryable, not dropped.

## Acceptance criteria
- AC1: With a sender that blocks 10 s, 200 confirmations complete with p99 < 1.5 s (test uses a scaled blocking sender).
- AC2: Rolled-back confirmation leaves no outbox row.
- AC3: A sender that fails N times then succeeds results in `delivered` with attempts N+1.
- AC4: Always-failing sender ends `dead` after max attempts; row still present.
- AC5: Expired leases are reclaimed and delivered; no row is lost after simulated crash.
- AC6: A burst of 1000 enqueues (100/s x 10 s) is all stored, and all get delivered, none lost or duplicated on success.
