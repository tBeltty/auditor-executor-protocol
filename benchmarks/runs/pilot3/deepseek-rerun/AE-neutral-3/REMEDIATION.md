# Remediation — AE-neutral-3 (Executor response to `audit.md`)

Verdict addressed: `REJECTED`. The audit found **no code defect** in `crm.py`
(sha256 unchanged: `b6cff371…aec3615`, 10 123 B). All 15 findings were missing or
weak guard tests. `crm.py` was not modified.

## What changed

- Added `test_crm_guards.py` (16 tests). One test per audit finding, named after the
  mutation it must kill.

| Finding | Guard test |
|---|---|
| 1 advance rule 3 before 4 | `TestAdvanceOrdering.test_actor_checked_before_final_stage` |
| 2 advance rule 5 before 6 | `TestAdvanceOrdering.test_transition_checked_before_negotiation_manager_rule` |
| 3 convert rule 3 before 4 | `TestConvertOrderingAndIds.test_actor_checked_before_lead_status` |
| 4 failed convert consumes no id | `TestConvertOrderingAndIds.test_rule_five_failure_consumes_no_opportunity_number` |
| 5 discount rule 3 before 4 | `TestDiscountOrdering.test_actor_checked_before_final_stage` |
| 6 discount rule 5 before 6 | `TestDiscountOrdering.test_rep_limit_checked_before_cumulative_cap` |
| 7 transfer rule 2 before 4 | `TestTransferRules.test_manager_checked_before_final_stage` |
| 8 add_lead rule 3 before 4 | `TestAddLeadGuard.test_source_checked_before_duplicate` |
| 9 transfer role clause | `TestTransferRules.test_new_owner_manager_with_spare_capacity_is_rejected` |
| 10 qualify exactly one log entry | `TestQualifyLog.test_successful_qualify_appends_exactly_one_entry` |
| 11 convert exactly one log entry | `TestConvertOrderingAndIds.test_successful_convert_appends_exactly_one_entry` |
| 12 advance exactly one log entry | `TestAdvanceOrdering.test_successful_advance_appends_exactly_one_entry` |
| 13 discount exactly one log entry | `TestDiscountOrdering.test_successful_discount_appends_exactly_one_entry` |
| 14 transfer exactly one log entry | `TestTransferRules.test_successful_transfer_appends_exactly_one_entry` |
| 15 single-`@` clause | `TestAddLeadGuard.test_multiple_at_signs_are_rejected_by_the_documented_rule` |

`test_crm.py`, `test_crm_protocol.py` and `crm.py` are untouched.

## Verification

```
cd /tmp/aep-lab/pilot3/deepseek-rerun/AE-neutral-3
python3 -m unittest discover -s /tmp/aep-lab/pilot3/deepseek-rerun/AE-neutral-3 -p "test*.py"
→ Ran 97 tests, OK
```

Mutation check (transient harness, removed afterward; baseline green, each mutant
installed in an isolated copy under this directory, bytecode caching disabled):

```
killed=15 survived=0 invalid=0 total=15
```

All 15 mutants the audit reported as surviving are now killed by the guard suite,
including the two that previously passed for the wrong reason (transfer role clause)
and the incidental `@`-count guard.

## Not addressed (out of scope, per audit)

- `aepkit lint` still reports no plan of record / execution guide / compliance log.
  The audit itself calls this arguably out of scope for a single-module run.
- The two equivalent mutants reported by the audit (`_assign_waiting` `if` vs `while`,
  transfer's slot-free branch) were confirmed unreachable; no test was fabricated for
  them.
- `test_transfer_assigns_new_owner_and_frees_previous_slot` in `test_crm.py` is misnamed
  but not defective; left as-is rather than edited outside the findings list.
