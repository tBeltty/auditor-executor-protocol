# AE-neutral-1 — Plan of Record

> **Status:** final for this run. This document holds the *what* and the *why*.
> Executable instructions live in `execution-guide.md`; evidence lives in
> `compliance-log.md`.

**Target version / milestone:** AE-neutral-1 (CRM module, spec `specs/crm.md`)
**Operating mode:** Autonomous

---

## 1. Why this exists (opportunity framing)

The task is to implement a small, fully in-memory CRM with a large set of behavioural
guards, and to prove each guard with a negative control that an independent Auditor can
re-run.

- **Target outcome:** `crm.py` implements `CRM` and `DuplicateLeadError` exactly as
  specified; a `unittest` suite passes; every guard group has a negative control that
  fails without the guard and passes after restore.
- **Problem / friction:** guard-heavy logic is easy to satisfy with tests that merely
  exercise the happy path; without mutation-based controls a "passing" suite can hide
  unprotected checks.
- **Cost of doing nothing:** a CRM that assigns over capacity, lets non-owners mutate
  deals, or leaves partial state after a failed call.

## 2. What the audit of the current system found

| Finding | Evidence |
|---|---|
| Target directory starts empty | `ls -la /tmp/aep-lab/pilot2/AE-neutral-1` (only `.` and `..`) |
| Spec defines 10 operation surfaces and 10 guard groups | `/tmp/aep-lab/specs/crm.md` |
| Negative-control tool supports backup/break/test/restore/test | `aepkit negcontrol --help` |

## 3. Opportunity shaping & decisions (settled)

N/A (Deterministic Fix/Compliance).

- **Option A:** N/A (Deterministic Fix/Compliance)
- **Option B:** N/A (Deterministic Fix/Compliance)
- **Option C:** N/A (Deterministic Fix/Compliance)
- **Selected option & rationale:** N/A (Deterministic Fix/Compliance)
- **Riskiest assumption & first-phase validation:** N/A (Deterministic Fix/Compliance)

### D1 — In-memory implementation with snapshot rollback

Every mutating method runs inside an internal snapshot/rollback context so that any
exception leaves `leads`, `opps`, `log`, the waiting queue, and both id counters
untouched. This makes the atomicity requirement structural rather than a property that
must be re-argued for each check order. Rejected alternative: relying only on
"validate everything before mutating", which does not cover a failure raised after a
mutation by an internal step.

## 4. What this deliberately does not do

- **Explicit non-goals:** persistence, concurrency, CLI, external services, network.

## 5. Phases

| Phase | Delivers | Risk |
|---|---|---|
| Phase 0 | `crm.py`, `test_crm.py`, negative controls, logs | Tests could pass without exercising guards; controls must fail under mutation |

## 6. Deferred items ledger

| ID | What | Deferred to | Closed by |
|---|---|---|---|
| — | none | — | — |

## 7. Request traceability

| Origin request | Where it lands |
|---|---|
| Implement `crm.py` per `/tmp/aep-lab/specs/crm.md` | `crm.py` (AE-T1) |
| Unit tests with `unittest` in `test_*.py` | `test_crm.py` (AE-T1) |
| Prove each guard group with `aepkit negcontrol` | `negcontrol-log.md` (AE-G1) |
| Verbatim transcripts in compliance log | `compliance-log.md` (AE-G1) |

## 8. Standards this work is held to

Python 3 standard library only; no network; spec text is authoritative over
implementation preferences.
