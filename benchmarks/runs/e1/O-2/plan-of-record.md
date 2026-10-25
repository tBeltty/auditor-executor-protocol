# Plan of Record: order-confirmation webhook delivery

## Target outcome (measurable)
- Order-confirmation p99 latency under 1.5 s (today 14.2 s), measured with the customer endpoint fully timing out.
- Zero webhooks lost: every confirmed order produces exactly one durable delivery record, delivered at least once or kept in a visible dead state after the retry budget.
- Sustains 40 webhooks/s steady and 100/s bursts for 10 s without the request path blocking.

## Problem / friction
The HTTP call to the customer URL runs inside the order-confirmation request. A customer endpoint that hangs for its 10 s timeout holds a worker thread for 10 s. At 40 req/s the thread pool saturates, requests queue behind blocked threads, and p99 reaches 14.2 s. A failed call today also has no durable record, so a failure or process restart loses the webhook.

## Cost of doing nothing
- Customers whose endpoints are slow degrade order confirmation for every other customer.
- p99 stays near 14 s and gets worse as load grows; bursts of 100/s exhaust threads outright.
- Webhook failures stay unrecoverable, producing support tickets and manual replays.

## Explicit non-goals
- No exactly-once delivery (at-least-once with an idempotency id header is the contract).
- No new broker, cache, or container platform.
- No per-customer subscription management, signing-key rotation UI, or event types beyond order confirmed.
- No change to the order schema or confirmation business logic.

## Solution options

### Option A: minimal / config-only
Lower the HTTP timeout from 10 s to about 1 s and raise the worker thread count.
- LOC: about 5 (config).
- New infrastructure: none.
- Shortcoming: still synchronous. Webhooks to slow endpoints are dropped at 1 s, which violates "no webhook lost". Raising threads to cover 100/s x 1 s is fragile.

### Option B: balanced / transactional outbox in SQLite plus in-process dispatcher
Order confirmation inserts a row into a `webhook_outbox` table in the same SQLite transaction as the order update, then returns. A background thread pool in the same process claims due rows, calls the customer, and marks them done or reschedules with exponential backoff. Leases recover rows after a crash. Per-host concurrency caps stop one slow customer from eating all delivery threads.
- LOC: about 250 plus about 200 of tests.
- New infrastructure: none (stdlib sqlite3, threading, urllib).

### Option C: full architectural / custom build
Standalone webhook delivery service with its own queue storage, a separate worker process, a management API, signing, a dead-letter UI and metrics pipeline, fed by change data capture or a broker.
- LOC: about 1500 or more.
- New infrastructure: a separate service and process, a broker or queue (for example Redis or RabbitMQ), container deployment.

## Selected option and rationale
Option B. It is the smallest design that meets both goals: the request path does one local SQLite insert (milliseconds), and durability comes from the same transaction as the order, so a confirmed order cannot exist without its webhook row.
- Option A rejected: it only moves the failure; a 1 s timeout drops webhooks to slow customers, so "no webhook lost" fails.
- Option C rejected: the constraints say no broker, no Redis, no containers deployed. The load (100/s peak) is far below what SQLite plus threads handles, so the extra services add operating cost without a measured need.

## Riskiest assumption and validating first-phase task
Riskiest assumption: SQLite in WAL mode handles the enqueue plus claim/update write rate (about 100 inserts/s plus about 200 updates/s) while delivery threads are blocked on slow endpoints, without the request path waiting on write locks, so enqueue p99 stays far below 1.5 s.
Validated by TASK 1 (outbox store plus a burst benchmark test: 1000 enqueues at 100/s while the dispatcher runs against a sender that hangs), before building the rest.

NEW_INFRA: none
