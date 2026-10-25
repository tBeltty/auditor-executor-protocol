# Plan of Record: Webhook delivery on order confirmation

## Target outcome (measurable)
- Order-confirmation p99 latency under 1.5 s (today 14.2 s) at 40 webhooks/s sustained and bursts of 100/s for 10 s.
- Zero webhooks lost: every confirmed order has a durable webhook record, delivered at least once, including after a process crash.
- Confirmation latency independent of customer endpoint speed (a 10 s timeout adds 0 s to the request).

## Problem / friction
The webhook HTTP call runs inside the order-confirmation request. When a customer endpoint takes 10 s to time out, the worker thread is held for that time, the thread pool saturates, and unrelated orders queue behind it. The request outcome depends on a third party's availability, and a failed call has no recorded retry.

## Cost of doing nothing
- p99 stays at 14.2 s; orders from healthy customers are slowed by one slow endpoint.
- Webhooks that fail or time out are dropped, so customers hold stale order state and open support tickets.
- Burst traffic (100/s x 10 s) against a slow endpoint can exhaust all workers and take the service down.

## Explicit non-goals
- No message broker, Redis, or container deployment.
- No exactly-once delivery (at-least-once with an idempotency key is the contract).
- No customer-facing UI, webhook signing changes, or payload schema changes.
- No migration off SQLite.

## Solution options

### Option A: minimal / config-only
Lower the HTTP timeout (e.g. 10 s to 2 s) and fire the call from a bare `threading.Thread` per order, no persistence.
- LOC: ~30.
- New infrastructure: none.
- Weakness: webhooks are lost on crash, restart or failure; unbounded threads under burst.

### Option B: balanced / pragmatic (transactional outbox in SQLite)
Insert a row into a `webhook_outbox` table in the same transaction that confirms the order. A pool of in-process dispatcher threads claims due rows, performs the HTTP call, and marks them delivered or reschedules with exponential backoff. Stale claims are recovered after a crash. A per-URL circuit breaker bounds threads held by dead endpoints.
- LOC: ~250 including tests ~200 more.
- New infrastructure: none (stdlib sqlite3, threading, urllib).

### Option C: full architectural / custom build
Separate delivery service with its own queue store, per-tenant rate limiting, signing, dead-letter UI, and metrics, deployed as an independent process.
- LOC: ~2000+.
- New infrastructure: a separate service/process, a dedicated queue datastore (or broker), deployment and monitoring pipeline.

## Selected option and rationale
Option B. It meets both goals (durable record in the order transaction gives no loss; async delivery removes the third party from the request path) with zero new infrastructure, which the constraints require.
- Option A rejected: it fails the "no webhook lost" goal (in-memory only) and does not bound concurrency in bursts.
- Option C rejected: it needs a new service and datastore the constraints forbid, and costs roughly ten times the effort for scale (100/s) that a SQLite WAL outbox handles.

## Riskiest assumption and validating first-phase task
Riskiest assumption: SQLite in WAL mode can absorb the enqueue write at 100/s (with dispatcher threads updating rows concurrently) while keeping enqueue p99 well under 1.5 s. First-phase task (TASK 1 and TASK 2 in the execution guide): build the outbox schema and enqueue path, then run a burst benchmark test (100/s for a scaled-down window with concurrent dispatchers and a slow endpoint) asserting enqueue p99 under 1.5 s and zero lost rows.

NEW_INFRA: none
