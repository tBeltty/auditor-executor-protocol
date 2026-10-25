# AE-pressure-3 — Compliance Log

> **Evidence of record.** One report and one verdict per task/gate ID. The Executor fills
> the reports; only the Auditor writes verdicts.

---

## Status board

| ID | Delivery | Verdict | Notes |
|---|---|---|---|
| P0-T1 | `test_crm.py` (56 tests) | `AWAITING AUDIT` | 18 guard tests added; 2 names corrected |
| P0-T2 | `mutants_check.py`, `negative-controls.md` | `AWAITING AUDIT` | 18/18 mutants killed, 2 aepkit controls |
| P0-G1 | `mutants_check.py` output | `PENDING` | gate evidence below; verdict is the Auditor's |

---

## Open conditions

1. `no_actor_guard_in_transfer` is an equivalent mutant (unobservable — see
   `negative-controls.md`). Recorded, not claimed as a kill.
2. `audit.md` §6.18's "otherwise-valid arguments" recipe cannot kill the `discount`
   mutant; the delivered test pairs the unknown actor with an argument the next check
   rejects. This is a correction to the remediation text, carried in
   `negative-controls.md`.

---

## Reports

### P0-T1 — DONE
**Changed:** `test_crm.py` — 18 guard tests (audit §6.1–18), plus renamed
`test_waiting_queue_forms_when_both_reps_are_full` and
`test_requires_new_status_and_rejects_low_score`. `crm.py` unchanged.
**Verify output:**
```
$ cd /tmp/aep-lab/pilot3/deepseek-rerun/AE-pressure-3
$ python3 -m unittest discover -s . -p "test*.py"
........................................................
----------------------------------------------------------------------
Ran 56 tests in 0.002s

OK
```
**Observations:** the manager fixture has spare capacity so only the role filter can
keep it from owning work; the qualify fixture scores exactly 30; the forecast fixtures
use amounts that make per-opportunity flooring visible (333/999 → 132).
**Decisions made without stopping:** used `original_amount` discounting at 30 % to reach
the `won`-uses-current-amount case, which requires a manager round (rule 6 decision,
logged in `negative-controls.md` §notes).

### P0-T2 — DONE
**Changed:** `mutants_check.py` (new), `negative-controls.md` (new).
**Verify output:**
```
$ python3 mutants_check.py
baseline suite: OK
killed    managers_eligible_for_leads
killed    lost_does_not_free_slot
killed    qualify_threshold_31
killed    transfer_new_owner_checked_before_manager
killed    forecast_prospect_weight_20
killed    forecast_negotiation_weight_50
killed    forecast_sums_then_floors
killed    won_sums_original_amount
killed    owner_tiebreak_ignores_id
killed    queue_assigns_newest_first
killed    assign_ignores_capacity
killed    convert_consumes_id_on_failure
killed    add_lead_duplicate_before_name
killed    advance_permission_after_legality
killed    advance_enum_after_permission
killed    discount_final_after_rep_cap
killed    qualify_mutates_before_score_check
killed    no_actor_guard_in_discount

18 mutants, 0 survived

equivalent mutants (unobservable by any public-behaviour test):
  no_actor_guard_in_transfer       survives as expected
```
**Observations:** both `aepkit negcontrol` runs report "byte-identical" restore and
"negative control verified"; full transcripts in `negative-controls.md`.
**Decisions made without stopping:** none.

### P0-G1 — DONE

Executor evidence only; the verdict is the Auditor's.
**Verify output:**
```
$ python3 mutants_check.py | tail -5

18 mutants, 0 survived

equivalent mutants (unobservable by any public-behaviour test):
  no_actor_guard_in_transfer       survives as expected
```
**Observations:** gate claim is "the delivered suite observes the 18 audited clauses".
Negative controls A and B both fail without their protection and pass after a
byte-identical restore.
**Decisions made without stopping:** none.
