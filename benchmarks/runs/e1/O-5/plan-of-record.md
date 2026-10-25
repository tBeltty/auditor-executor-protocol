# Plan of record: order-confirmation webhooks

## Target outcome (measurable)
- Order-confirmation p99 latency under 1.5 s with the customer endpoint timing out at 10 s (today 14.2 s).
- Zero webhooks lost: every confirmed order produces at least one delivery attempt record that ends in `delivered` or a visible `dead` state; nothing disappears on crash or restart.
- Sustains 40 webhooks/s steady and 100/s bursts for 10 s (1,000 events) without the confirm path waiting on any customer endpoint.

## Problem / friction
- The HTTP call to the customer URL runs inside the order-confirmation request. A slow or dead endpoint holds the worker thread for up to 10 s.
- Blocked workers queue other confirmations behind them, so p99 reaches 14.2 s.
- If the process dies mid-call, no durable record says the webhook is owed.

## Cost of doing nothing
- Confirmations stay at p99 14.2 s during any customer outage; thread exhaustion can stall unrelated orders.
- Webhooks that fail or are interrupted are silently dropped, so customers' systems drift from ours and support handles manual re-sends.

## Explicit non-goals
- No new broker, cache, container or managed service.
- No webhook signing, payload redesign or customer-facing retry dashboard.
- No exactly-once guarantee (at-least-once with an idempotency key is the contract).
- No multi-node scaling.

## Options

### Option A: minimal / config-only
Lower the HTTP timeout from 10 s to 2 s and raise worker thread count; keep the call synchronous.
- LOC: about 10.
- New infrastructure: none.
- Weakness: confirm latency is still bounded by the endpoint (up to 2 s, above the 1.5 s target), and failed calls are still lost.

### Option B: balanced / pragmatic
Transactional outbox table in the existing SQLite file, written in the same transaction as the order confirmation. An in-process dispatcher (stdlib threads) claims due rows with a lease, posts with a short timeout, and retries with exponential backoff; exhausted rows move to `dead`, never deleted.
- LOC: about 250 plus tests.
- New infrastructure: none (stdlib sqlite3, threading, urllib).

### Option C: full architectural / custom build
Dedicated webhook delivery service with a message broker (for example RabbitMQ or Kafka), its own datastore, per-tenant rate limiting, dashboards and a replay API.
- LOC: about 2,000 or more.
- New infrastructure: broker, separate service, container platform, monitoring.

## Selected option and rationale
Option B.
- It decouples confirmation from the endpoint (the confirm path only does one local INSERT) and the outbox row is committed atomically with the order, so no webhook is lost.
- Option A rejected: cannot meet 1.5 s p99 and does not prevent loss.
- Option C rejected: the load (100/s peak) is far inside SQLite WAL capacity; a broker and service add operational cost with no deployed platform to host them.

## Riskiest assumption and first-phase task that validates it
Assumption: SQLite in WAL mode accepts the outbox INSERT inside the confirm transaction at 100/s while the dispatcher concurrently updates rows, keeping confirm p99 well under 1.5 s. TASK 1 builds the outbox store and a concurrent write/claim load test that measures this before any other work.

NEW_INFRA: none
