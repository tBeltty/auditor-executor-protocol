# Spec: Asynchronous order-confirmation webhooks

## Problem
Confirming an order calls the customer webhook synchronously. When the customer endpoint hangs (10 s timeout), worker threads block and p99 confirmation latency reaches 14.2 s.

## Functional requirements
- FR1: Confirming an order must not perform any outbound HTTP call. It writes the order change and a webhook record in ONE SQLite transaction.
- FR2: A background dispatcher inside the same process delivers pending webhooks over HTTP POST (JSON body).
- FR3: Delivery is at-least-once. Each delivery carries a stable `X-Webhook-Id` header so customers can deduplicate.
- FR4: Failed deliveries (timeout, connection error, non-2xx) are retried with exponential backoff and jitter.
- FR5: A webhook is never deleted. After the maximum attempts it moves to status `dead` and can be replayed with `replay_dead()`.
- FR6: A crash during delivery must not lose a webhook: claims are leases that expire and the row becomes deliverable again.
- FR7: One slow customer URL must not starve others: in-flight deliveries per URL are capped.
- FR8: Load: sustain 40 webhooks/s, absorb bursts of 100/s for 10 s (1000 rows) without blocking confirmation.

## User stories
- As a customer-service owner, I want order confirmation to stay fast when a customer endpoint is down.
- As an integrator, I want every confirmed order to reach my endpoint eventually, with a dedupe id.
- As an operator, I want undelivered webhooks inspectable and replayable.

## Acceptance criteria
- AC1: With an endpoint that hangs, confirm_order p99 over 200 calls is below 1.5 s (target in practice: milliseconds).
- AC2: If the confirmation transaction rolls back, no webhook row exists; if it commits, exactly one exists.
- AC3: An endpoint that fails N times then succeeds receives the webhook; status ends `delivered`.
- AC4: A row claimed by a dispatcher that "crashed" is redelivered after the lease expires.
- AC5: 1000 webhooks enqueued in a burst are all delivered or remain persisted (count conserved).
- AC6: Exhausted retries end in `dead`, and replay_dead() makes them pending again.
- AC7: No new services or dependencies (standard library only).
