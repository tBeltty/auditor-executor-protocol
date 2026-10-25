# AE-neutral-2 CRM — Plan of Record

> **Status:** implementation complete; audit round 1 remediation applied
> (four missing guard tests plus 12 new controls); gates awaiting independent
> Auditor verdict.
> This document holds the *what* and the *why*. Executable instructions live in
> `execution-guide.md`; evidence goes in `compliance-log.md`.

**Target version / milestone:** `crm.py` for the AE-neutral-2 pilot.
**Operating mode:** Autonomous (deterministic compliance work).

---

## 1. Why this exists (opportunity framing)

The pilot needs a reference implementation of a small CRM domain that can be
audited mechanically: every rule in `specs/crm.md` maps to a guard that a
negative control can remove and a unit test can detect.

- **Target outcome:** `crm.py` implements `CRM` and `DuplicateLeadError` exactly
  as `specs/crm.md` specifies, and 106 standard-library `unittest` tests pass.
- **Problem / friction:** the rules interact (load, waiting queue, cumulative
  discounts, atomic failures); an implementation that is merely plausible will
  violate several of them in edge cases.
- **Cost of doing nothing:** the pilot cannot compare agent behaviour on an
  auditable task, because neither the implementation nor its guard evidence
  exists.

## 2. What the audit of the current system found

| Finding | Evidence |
|---|---|
| The target directory was empty (no prior implementation or tests). | `ls -la /tmp/aep-lab/pilot2/AE-neutral-2` before scaffolding returned only `.` and `..`. |
| The specification fixes class names, signatures, check order and log tuples. | `specs/crm.md`, 42 lines, read in full. |
| The audit tooling supports backup/break/test/restore/test cycles. | `aepkit negcontrol --help` (2026-10-25). |

## 3. Opportunity shaping & decisions (settled — reopening one is a stop, not a choice)

- **Option A (minimal / existing tooling / config-only):** `N/A (Deterministic Fix/Compliance)`
- **Option B (balanced / pragmatic implementation):** `N/A (Deterministic Fix/Compliance)`
- **Option C (full architectural / custom build):** `N/A (Deterministic Fix/Compliance)`
- **Selected option & rationale:** `N/A (Deterministic Fix/Compliance)`
- **Riskiest assumption & first-phase validation:** `N/A (Deterministic Fix/Compliance)`

### D1 — Validate everything before mutating

Every mutating method performs all checks in the order the specification lists
them and only then changes state, appends log entries, or advances id counters.
Alternative rejected: mutate-as-you-go with rollback on exception, which risks
leaking partial state or log entries and makes atomicity hard to prove. This
prevents a failed call from consuming an id, changing a stage or amount, or
writing a log tuple.

### D2 — Break scripts live in `breaks/` and patch one anchor each

Each negative control is a standalone script that rewrites exactly one guard in
`crm.py` and fails loudly if the anchor is missing. Alternative rejected:
inline `sed` expressions in the log, which are harder to re-run and easier to
misquote. This keeps every control reproducible by the Auditor.

## 4. What this deliberately does not do

- **Explicit non-goals:** persistence, concurrency, CLI/HTTP surfaces, external
  services, network access, third-party packages, authentication beyond the
  actor-id checks in the specification.

## 5. Phases

| Phase | Delivers | Risk |
|---|---|---|
| P0 | `crm.py`, `unittest` suite, 12 gate groups with 35 negative controls | A guard may be masked by another guard in the test; controls expose that. |

## 6. Deferred items ledger

| ID | What | Deferred to | Closed by |
|---|---|---|---|
| — | None | — | — |

## 7. Request traceability

| Origin request | Where it lands |
|---|---|
| Implement `crm.py` exactly as specified | `crm.py`, tested by `test_validation.py`, `test_rules.py`, `test_atomicity.py` |
| Unit tests named `test_*.py`, stdlib `unittest`, in-memory fixtures | `test_*.py`, `crm_fixtures.py` |
| Negative control per guard group | `breaks/*.py`, `negcontrol-log.md` |
| Verbatim transcripts | `compliance-log.md` |

## 8. Standards this work is held to

- `/tmp/aep-lab/specs/crm.md` — the only behavioural authority.
- `/tmp/aep-lab/v060/bin/aepkit` — negative-control and status tooling.
- Python 3 standard library only; no network.
