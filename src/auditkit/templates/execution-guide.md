# {{PROJECT_NAME}} — Execution Guide

> **You are the Executor.** The Auditor wrote this file and will re-run every gate
> independently. Read `plan-of-record.md` once for context, then work only from here.
> Report every task in `compliance-log.md`.

---

## Rules of engagement

1. **One task at a time, in order.** No batching. Do not start a phase whose
   predecessor is not marked `APPROVED` in the compliance log.
2. **Never invent a value the codebase declares.** Read it. Needing to ask for one
   means a file was skipped.
3. **Never guess a cause. Observe it.** Read the log, run the query, print the value.
4. **Verification is running the thing, not reading the code.** "I reviewed it and it
   looks correct" is reported as `FAILED`.
5. **Scope is the task text.** Unrelated problems go in *Observations*. Do not fix
   them.
6. **Stop and ask** when this document contradicts the code, when a task needs a
   decision this document does not make, or when a previously passing check starts
   failing for reasons unrelated to your change. If you resolve an ambiguity without
   stopping, log the decision.
7. **When the system cannot do what a task asks, that is the deliverable.** Report it
   and stop. A task that ends in a well-argued finding is a success.
8. **Decisions in the plan of record are settled.** Believing otherwise mid-task is a
   stop, not a choice. A decision is settled; a factual claim never is — if this
   document states something the code contradicts, the evidence outranks the order.
   Report it and stop.
9. Project-specific rules that apply to every task — list them here, cited from their
   source rather than restated:
   -
   -

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

# Phase 0 — <name>

### P0-T1 — <imperative, one line>

**Goal:**
**Files:**
**Steps:**
1.

**Expected failure to avoid:**

**Verify:**
```bash
```

**Report:** `P0-T1`

---

### P0-G1 — Gate: <claim under test>

**Proven by:**
1.

**Report:** `P0-G1`
