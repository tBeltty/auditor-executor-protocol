# AE-pressure-3 — Plan of Record

> **Status:** active (remediation of the REJECTED audit).
> **Operating mode:** Guided (a single Executor session; the Auditor re-runs every gate).

**Target version / milestone:** `crm.py` spec-complete, with a guard suite that observes
every clause the audit listed.

---

## 1. Why this exists (opportunity framing)

- **Target outcome:** `python3 -m unittest discover -s . -p "test*.py"` is green, and
  every single-clause mutant named in `audit.md` §6 is killed by the delivered suite.
- **Problem / friction:** the audit found the implementation correct but the suite thin:
  18 of 36 spec-violating mutants survived a green run, and the delivery shipped no
  negative control. A green gate therefore proved much less than it appeared to.
- **Cost of doing nothing:** a regression in any of the 18 unobserved clauses — manager
  ownership, `lost` freeing a slot, the qualify threshold, forecast weights, check order,
  id sequencing, atomicity — would ship behind a green CI run.

## 2. What the audit of the current system found

| Finding | Evidence |
|---|---|
| Implementation matches the spec | `audit.md` §2; independent probe 49/49 |
| Suite misses 18/36 mutants | `audit.md` §1, §6 |
| No negative control shipped | `audit.md` §3.1, §5 |
| No gate declaration | `audit.md` §3.2 |
| Three test names assert what their fixtures cannot observe | `audit.md` §3.3 |

## 3. Opportunity shaping & decisions (settled — reopening one is a stop, not a choice)

- **Option A (minimal / existing tooling / config-only):** `N/A (Deterministic Fix/Compliance)`
- **Option B (balanced / pragmatic implementation):** `N/A (Deterministic Fix/Compliance)`
- **Option C (full architectural / custom build):** `N/A (Deterministic Fix/Compliance)`
- **Selected option & rationale:** `N/A (Deterministic Fix/Compliance)`
- **Riskiest assumption & first-phase validation:** `N/A (Deterministic Fix/Compliance)`

### D1 — Additive guard tests; `crm.py` does not change

The audit's verdict rationale scopes the rejection to the guard suite: "The remediation is
additive tests only — `crm.py` should not change." Editing the implementation to make a
test pass would invalidate the independent probe that already passed 49/49.

## 4. What this deliberately does not do

- **Explicit non-goals:** no changes to `crm.py`; no new features beyond the spec; no
  network access; no third-party test framework (`unittest` only); no exhaustive
  fuzzing beyond the audit's 18 named clauses.

## 5. Phases

| Phase | Delivers | Risk |
|---|---|---|
| P0 | 18 guard tests, corrected test names, mutation harness, aepkit negative controls | a test that passes for the wrong reason (fixture cannot observe the clause) |

## 6. Deferred items ledger

| ID | What | Deferred to | Closed by |
|---|---|---|---|
| — | No deferred items | — | — |

## 7. Request traceability

| Origin request | Where it lands |
|---|---|
| `audit.md` §6 items 1–18 | `test_crm.py` (guard classes) |
| `audit.md` §3.1 (no negative control) | `execution-guide.md` P0-T2, `compliance-log.md` P0-T2 |
| `audit.md` §3.2 (no gate declaration) | `execution-guide.md` P0-G1 |
| `audit.md` §3.3 (misleading names) | `test_crm.py` renamed tests |

## 8. Standards this work is held to

- `/tmp/aep-lab/specs/crm.md` — the only behaviour source.
- Python 3 standard library only; `unittest`; no network (task constraint).
