# Plan of Record: asynchronous order-confirmation webhooks

## Target outcome (measurable)
- Order-confirmation p99 latency under 1.5 s (today 14.2 s) while the customer endpoint is fully timing out, at 40 webhooks/s sustained and 100/s bursts for 10 s.
- Zero lost webhooks: every confirmed order produces a webhook row that is delivered (HTTP 2xx) or ends in an explicit, queryable "dead" state after retries. Rows survive process restarts.

## Problem / friction
- The HTTP call to the customer URL runs inside the confirmation request. A 10 s endpoint timeout holds a worker thread for 10 s, so the thread pool saturates and confirmation latency tracks the customer's slowest endpoint.
- If the call fails, nothing records that the webhook is owed, so a failure or crash loses it.

## Cost of doing nothing
- p99 stays at 14.2 s whenever any customer endpoint degrades; at 100/s bursts the thread pool exhausts and confirmations for unrelated customers stall or fail.
- Customers miss order events with no audit trail, producing support load and trust loss.

## Explicit non-goals
- No message broker, Redis, containers or new services.
- No exactly-once delivery (at-least-once with an idempotency key header is the contract).
- No customer-facing delivery dashboard, no per-customer rate limiting, no payload schema changes.
- No migration off SQLite.

## Solution options

### Option A: minimal / config-only
Lower the HTTP timeout (10 s to 2 s) and raise the worker thread count; keep the call synchronous.
- LOC: about 5 (config).
- New infrastructure: none.
- Does not meet the goals: p99 still bound by the timeout (above 1.5 s), and failed calls are still lost.

### Option B: balanced / pragmatic
Transactional outbox in the existing SQLite file. Order confirmation inserts a webhook row (same transaction as the order) and returns. A bounded in-process thread pool claims due rows, POSTs with a short timeout, and on failure reschedules with exponential backoff up to a max attempts, then marks dead. Stale claims are recovered after a crash.
- LOC: about 250 plus about 200 tests.
- New infrastructure: none (stdlib sqlite3, threading, urllib).

### Option C: full architectural / custom build
Separate dispatcher service with its own durable queue or broker, per-tenant isolation, circuit breakers, delivery dashboard and replay API.
- LOC: about 2000-3000.
- New infrastructure: message broker (for example RabbitMQ or Kafka), a separately deployed dispatcher service, container runtime.

## Selected option and rationale
Option B. Confirmation latency becomes one local SQLite insert (milliseconds), independent of customer endpoints, and durability comes from the same database that holds the order, so no webhook is lost. It needs no new infrastructure, which fits a monolith with no broker or containers.
- Option A rejected: still synchronous, so p99 is at least the timeout and failures remain unrecorded; fails both goals.
- Option C rejected: meets the goals but adds a broker and a deployed service and roughly ten times the code for a load (100/s peak) that SQLite handles; cost and operational burden are unjustified.

## Riskiest assumption and first-phase validation
Riskiest assumption: a single SQLite file in WAL mode absorbs 100 inserts/s from request threads while worker threads concurrently claim and update rows, without lock contention pushing p99 over 1.5 s. The first task (TASK 1) builds the outbox store and a load test that enqueues at 100/s against a pool of always-timing-out workers and asserts enqueue p99 under 1.5 s (measured far lower).

NEW_INFRA: none
