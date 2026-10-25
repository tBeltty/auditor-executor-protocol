# AE-neutral-1 — Execution Guide

> **You are the Executor.** The Auditor re-runs every check independently.
> Read `plan-of-record.md` once for context, then work only from here.
> Report every task in `compliance-log.md`.

---

## Rules of engagement

1. **One task at a time, in order.** No batching.
2. **Never invent a value the codebase declares.** Read the spec.
3. **Never guess a cause. Observe it.**
4. **Verification is running the thing, not reading the code.**
5. **Scope is the task text.** Unrelated problems go in *Observations*.
6. **Stop and ask** when the spec contradicts itself.
7. **When the system cannot do what a task asks, that is the deliverable.**
8. Project-specific rules:
   - Work only inside `/tmp/aep-lab/pilot2/AE-neutral-1`; the only readable files
     outside are `/tmp/aep-lab/specs/crm.md` and `/tmp/aep-lab/v060/bin/aepkit`.
   - Python 3 standard library only, no network.
   - Tests live in `test_*.py` and use plain in-memory fixtures.

## Reporting format

For each task, append to `compliance-log.md`:

```
### <TASK-ID> — DONE | BLOCKED | FAILED
**Changed:** <paths>
**Verify output:**
<pasted, literal, unedited command output>
**Observations:** <or "none">
**Decisions made without stopping:** <or "none">
```

A `DONE` with no pasted output is recorded as `FAILED`.

---

# Phase 0 — CRM module

### AE-T1 — Implement `crm.py` and the unittest suite

**Goal:** Implement `CRM` and `DuplicateLeadError` exactly as specified, with tests
covering every operation and guard group.

**Files:** `crm.py`, `test_crm.py`

**Steps:**
1. Read `/tmp/aep-lab/specs/crm.md`.
2. Implement `crm.py`.
3. Write `test_crm.py` with unittest.
4. Run `python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-1 -p "test*.py"` until green.

**Expected failure to avoid:** tests that assert only the exception type when a
different `ValueError` (for example an unpacking error) could satisfy them.

**Verify:**
```bash
python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-1 -p "test*.py"
```

**Report:** `AE-T1`

---

### AE-G1 — Gate: every guard is proven by a failing negative control

**Proven by:** 19 `aepkit negcontrol` runs, one per guard group (email/name/source,
duplicate detection, assignment/capacity/waiting queue, permissions, score threshold,
stage transitions, big-deal approval, discount limit and cumulative floor, transfer
rules, atomicity rollback). Each control breaks exactly one guard via `mutate.py`,
runs the targeted test, requires output matching `FAILED`, restores `crm.py`, and
re-runs the same test to green.

**Negative control:** `python3 mutate.py <mutation>`; the targeted test fails until
the guard is restored. All commands and verbatim outputs are in `negcontrol-log.md`
and repeated in `compliance-log.md`.

**Verify:**
```bash
python3 mutate.py --check
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-1/crm.py \
  --break-cmd "python3 mutate.py <mutation>" \
  --test-cmd "python3 -m unittest <target-test>" \
  --expect "FAILED" --timeout 20
```

**Report:** `AE-G1`
