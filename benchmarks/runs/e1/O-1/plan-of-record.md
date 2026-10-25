# Plan of record: order-confirmation webhooks

## Target outcome (measurable)
- Order-confirmation p99 latency under 1.5 s (today 14.2 s) while the customer endpoint is timing out.
- Zero webhooks lost: every confirmed order produces a webhook that is eventually delivered, including across process restarts and endpoint outages.
- Sustains 40 webhooks/s steady and a 100/s burst for 10 s (1,000 events) without blocking request threads.

## Problem / friction
The HTTP call to the customer URL happens inside the confirmation request. When the endpoint takes 10 s to time out, the request holds a worker thread for that time, the thread pool fills, and latency for every order rises. A failed or timed-out call has no durable record, so the event can disappear.

## Cost of doing nothing
Customers with slow endpoints degrade confirmation for all customers (p99 14.2 s). Timeouts drop events silently, which creates support tickets and reconciliation work. Each burst of 100/s for 10 s can exhaust the thread pool and cause an outage.

## Explicit non-goals
- No message broker, Redis, container or new service.
- No exactly-once delivery (at-least-once with an event id for customer-side dedupe).
- No customer-facing delivery dashboard or signing scheme changes.
- No migration off SQLite.

## Solution options

### Option A: minimal / config-only
Lower the HTTP timeout (10 s to 2 s) and raise the worker thread count.
- LOC: ~5 (config).
- New infrastructure: none.
- Gap: still synchronous, so p99 stays above 2 s whenever an endpoint is slow, and timeouts still lose events. Fails both targets.

### Option B: balanced / pragmatic
Transactional outbox in the existing SQLite file: confirming an order inserts the outbox row in the same transaction as the status update, then returns. A pool of background threads inside the monolith claims due rows, delivers with a short timeout, and retries with exponential backoff. Expired leases are reclaimed after a crash.
- LOC: ~200 plus ~150 tests.
- New infrastructure: none (stdlib sqlite3, threading, urllib).

### Option C: full architectural / custom build
Standalone delivery service with its own queue, per-customer rate limiting, circuit breakers, delivery log API and a separate datastore.
- LOC: ~1,500+.
- New infrastructure: a separate service and process, a queue or broker and its datastore, deployment and monitoring for them.

## Selected option and rationale
Option B. It decouples request latency from endpoint speed (request does one local SQLite insert) and gives durability through the outbox, so no event is lost, with no new infrastructure.
- Option A rejected: it cannot meet p99 under 1.5 s with slow endpoints and cannot guarantee no loss.
- Option C rejected: the volume (100/s peak) is well within SQLite WAL write capacity, and the extra services conflict with the "no broker, no containers" constraint for cost far beyond the need.

## Riskiest assumption and first-phase task that validates it
Assumption: SQLite in WAL mode handles confirmation inserts plus concurrent worker claim/update writes at 100/s without confirmation latency suffering from write-lock contention. Validated first by TASK 1 (storage layer and confirm path) and TASK 2 (a latency test with a deliberately slow endpoint and concurrent workers measuring p99 under 1.5 s).

NEW_INFRA: none
