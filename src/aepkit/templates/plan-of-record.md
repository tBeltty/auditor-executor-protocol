# {{PROJECT_NAME}} — Plan of Record

> **Status:** draft. This document holds the *what* and the *why*. Nobody implements
> from this file. The executable instructions live in `execution-guide.md`; evidence
> goes in `compliance-log.md`.

**Target version / milestone:**
**Operating mode:** <Guided | Autonomous>

---

## 1. Why this exists (opportunity framing)

What problem is this solving, and why now. If several requests trace back to one
underlying gap, name the gap here rather than listing the requests as unrelated.

- **Target outcome:** <measurable behavior, metric, or system state that changes when this is done>
- **Problem / friction:** <verified gap or failure mode in the current system, without prescribing the feature yet>
- **Cost of doing nothing:** <concrete impact of not doing this work or deferring it>

## 2. What the audit of the current system found

| Finding | Evidence |
|---|---|
| | |

State each finding with the command or artifact that established it, not from memory.

## 3. Opportunity shaping & decisions (settled — reopening one is a stop, not a choice)

For open-design or new-capability work, compare at least three distinct approaches before
locking the architecture. For deterministic bugfixes, security patches, schema migrations,
or strict compliance work, mark the shaping and assumption fields as
`N/A (Deterministic Fix/Compliance)` and go straight to `D1`.

- **Option A (minimal / existing tooling / config-only):** <approach, cost, and limits — or `N/A (Deterministic Fix/Compliance)`>
- **Option B (balanced / pragmatic implementation):** <approach, cost, and limits — or `N/A (Deterministic Fix/Compliance)`>
- **Option C (full architectural / custom build):** <approach, cost, and limits — or `N/A (Deterministic Fix/Compliance)`>
- **Selected option & rationale:** <which option wins and why the other two were rejected — or `N/A (Deterministic Fix/Compliance)`>
- **Riskiest assumption & first-phase validation:** <the primary value, usability, feasibility, or viability assumption that could invalidate the plan, and how the first phase (`P0` or `P1`) tests it before building the rest — or `N/A (Deterministic Fix/Compliance)`>

### D1 — <decision name>

What was decided, what alternative was rejected and why, what failure this prevents.

## 4. What this deliberately does not do

Scope boundaries the Auditor is holding, so an Executor (or a future Auditor) doesn't
drift into rebuilding something that was cut on purpose.

- **Explicit non-goals:** <what is deliberately out of scope for this run>

## 5. Phases

When the plan carries an unverified technical or product assumption, the first phase
(`P0` or `P1`) must test that riskiest assumption before building secondary scaffolding.

| Phase | Delivers | Risk |
|---|---|---|
| | | |

## 6. Deferred items ledger

| ID | What | Deferred to | Closed by |
|---|---|---|---|
| | | | |

Every decision or annex that pushes work to a future phase gets a row here in the same
edit. An open row (`Closed by` without a task ID) for a phase being closed is a stop.

## 7. Request traceability

| Origin request | Where it lands |
|---|---|
| | |

## 8. Standards this work is held to

Cite the project's own conventions rather than restating them here.
