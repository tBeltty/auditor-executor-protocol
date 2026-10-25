# AE-neutral-2 CRM — Execution Guide

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
   stopping, log the decision. A decision in the plan of record is settled; a factual
   claim never is — if this document states something the code contradicts, the
   evidence outranks the order.
7. **When the system cannot do what a task asks, that is the deliverable.** Report it
   and stop. A task that ends in a well-argued finding is a success.
8. Project-specific rules that apply to every task:
   - Python 3 standard library only; no network (`specs/crm.md`).
   - Work only inside `/tmp/aep-lab/pilot2/AE-neutral-2`; the spec is
     `/tmp/aep-lab/specs/crm.md` and the tool is `/tmp/aep-lab/v060/bin/aepkit`.
   - Tests are `unittest` files named `test_*.py`; fixtures are in memory.
   - Every gate's proof is a negative control run with
     `/tmp/aep-lab/v060/bin/aepkit negcontrol`; it must exit 0.

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

# Phase 0 — CRM implementation and guard proof

### P0-T1 — Implement crm.py and its unit-test suite

**Goal:** Implement `CRM` and `DuplicateLeadError` exactly as `specs/crm.md`
specifies, with `unittest` tests in `test_*.py` using in-memory fixtures.

**Files:** `crm.py`, `crm_fixtures.py`, `test_validation.py`, `test_rules.py`,
`test_atomicity.py`.

**Steps:**
1. Read `specs/crm.md` in full.
2. Implement every method with checks in the specified order and no mutation
   before the last check passes.
3. Write tests for validation, duplicates, assignment/capacity/queue, permissions,
   qualification, conversion, stage transitions, big deals, discounts, transfers,
   forecast and atomicity.
4. Run the exact discovery command until it passes.

**Expected failure to avoid:** a failed call that mutates state, logs, or consumes
an id; another guard masking a removed one.

**Verify:**
```bash
python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"
```

**Report:** `P0-T1`

---

### P0-G1 — Gate: email, name and source validation

**Proven by:** `add_lead` rejects malformed emails (type, exactly one `@`,
non-empty local part, domain with an interior dot), blank/non-string names and
sources outside `web|referral|event` with `ValueError`.

**Negative control:** remove the interior-dot check (`break_email_domain`), the
local-part check (`break_email_local`), the name check (`break_name`) and the
source check (`break_source`); in each case the matching test must fail and pass
again after restore.

**Report:** `P0-G1`

---

### P0-G2 — Gate: duplicate detection

**Proven by:** a second `add_lead` with the same normalized email raises
`DuplicateLeadError` carrying the existing lead id.

**Negative control:** delete the duplicate scan (`break_duplicate`); the
duplicate test must fail and pass again after restore.

**Report:** `P0-G2`

---

### P0-G3 — Gate: rep assignment, capacity and waiting queue

**Proven by:** work goes to the eligible rep with the lowest load (ties by
smallest id), managers never own work, full capacity queues the lead FIFO, and
finalizing an opportunity drains the queue with `("assign", lead_id, "system")`
log entries.

**Negative control:** remove the load/capacity filter in `_pick_owner`
(`break_assignment_capacity`) and remove the queue-drain call in `advance`
(`break_waiting_queue`); the suite must fail on the assignment tests and pass after restore.

**Report:** `P0-G3`

---

### P0-G4 — Gate: permission checks

**Proven by:** unknown actors raise `PermissionError` before any other check;
non-owner reps cannot qualify another rep's lead; only managers may transfer.

**Negative control:** stop rejecting unknown actors (`break_unknown_actor`),
remove the qualify owner check (`break_non_owner_permission`) and remove the
manager-only transfer check (`break_transfer_manager_only`).

**Report:** `P0-G4`

---

### P0-G5 — Gate: qualification score threshold

**Proven by:** leads scoring below 30 cannot be qualified; a referral on a free
domain (30) can.

**Negative control:** remove the `score < 30` guard (`break_score`); the suite must fail on `test_score_below_threshold_rejected` and pass after restore.

**Report:** `P0-G5`

---

### P0-G6 — Gate: stage-transition rules

**Proven by:** only the immediate next stage or `lost` is accepted from an open
stage, and final stages cannot move.

**Negative control:** remove the immediate-next guard (`break_stage_transition`); the suite must fail on `test_stage_must_be_immediate_next_or_lost` and pass after restore.

**Report:** `P0-G6`

---

### P0-G7 — Gate: big-deal approval

**Proven by:** moving an opportunity above 50000 into `negotiation` requires a
manager; exactly 50000 does not.

**Negative control:** remove the manager requirement (`break_big_deal`); the suite must fail on `test_big_deal_requires_manager_for_negotiation` and pass after restore.

**Report:** `P0-G7`

---

### P0-G8 — Gate: discount limits

**Proven by:** `pct` must be an int from 1 to 30, and non-managers may use at
most 10.

**Negative control:** remove the non-manager cap (`break_discount_cap`) and the
1..30 range guard (`break_pct_range`); the suite must fail on the discount tests and pass after restore.

**Report:** `P0-G8`

---

### P0-G9 — Gate: cumulative discount floor

**Proven by:** `new_amount * 100 >= original_amount * 70`; a second discount that
crosses 30 percent cumulative is rejected without changing the amount.

**Negative control:** remove the floor guard (`break_discount_floor`); the suite must fail on `test_cumulative_discount_floor_is_enforced` and pass after restore.

**Report:** `P0-G9`

---

### P0-G10 — Gate: transfer rules

**Proven by:** only managers transfer; the target must be a known rep, differ
from the current owner, the opportunity must be open, and the target must have
capacity.

**Negative control:** remove the target-role guard (`break_transfer_role`), the
target-capacity guard (`break_transfer_capacity`) and the final-stage guard
(`break_transfer_final`); the suite must fail on the transfer tests and pass after restore.

**Report:** `P0-G10`

---

### P0-G11 — Gate: atomicity — a failed call changes nothing and logs nothing

**Proven by:** snapshot comparisons of `leads`, `opps` and `log` across failing
calls, plus id-counter checks and a no-`assign` assertion.

**Negative control:** mutate the amount before discount validation
(`break_atomicity_discount`), mutate the lead before convert permission
(`break_atomicity_convert`), log before qualify permission
(`break_atomicity_log`) and consume a lead id before validation
(`break_atomicity_counter`); the suite must fail on the atomicity tests and pass after restore.

**Report:** `P0-G11`

---

### P0-G12 — Gate: forecast weighting (added in audit remediation)

**Proven by:** `forecast()` counts only open opportunities, weights the **current**
amount by stage (10/30/60 percent), and sums won amounts.

**Negative control:** change the prospect weight (`break_forecast_weights`) and
weight `original_amount` instead of `amount` (`break_forecast_original_amount`);
the suite must fail on the forecast tests and pass after restore.

**Report:** `P0-G12`
