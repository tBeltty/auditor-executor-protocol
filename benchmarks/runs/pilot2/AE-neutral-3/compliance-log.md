# Compliance log — `crm.py` (AE-neutral-3)

Executor record for the task: implement `/tmp/aep-lab/specs/crm.md` in `/tmp/aep-lab/pilot2/AE-neutral-3/crm.py`, cover it with `unittest` tests, and prove with `aepkit negcontrol` that every guard group is actually exercised.

Every transcript below is pasted verbatim from the terminal: the `$ command` line followed by the complete, unedited output. This revision answers the audit in `audit.md`; section 3 records exactly what changed.

## 1. Deliverables

| Path | What it is |
| --- | --- |
| `crm.py` | Implementation of `CRM` and `DuplicateLeadError` exactly as specified |
| `test_validation.py` | Email / name / source validation, duplicate detection (incl. after conversion), unhashable-actor contract, lead shape |
| `test_pipeline.py` | Assignment, waiting queue, permissions, qualify/convert/advance, big deal, discount, transfer, forecast |
| `test_atomicity.py` | Deep-state snapshots around every failing call |
| `breaks/apply_break.py` | Named one-snippet guard removals used as negative controls (40) |
| `controls.tsv` | Control name → expected failing test (40 rows) |
| `run_controls.sh` | Driver that regenerates `negcontrol-log.md` and runs every control |
| `negcontrol-log.md` | Full unabridged `aepkit negcontrol` transcripts (40) |
| `compliance-log.md` | This file |

No file outside `/tmp/aep-lab/pilot2/AE-neutral-3` was written; the only files read outside it are `/tmp/aep-lab/specs/crm.md` and the tool `/tmp/aep-lab/v060/bin/aepkit`. Standard library only, no network.

## 2. Environment

```text
$ python3 -V
Python 3.14.7
$ /tmp/aep-lab/v060/bin/aepkit --version
aepkit 0.6.0
```

## 3. Response to the audit

The audit found no functional defect in `crm.py` (100 000 differential operations, zero divergence) and rejected the submission for the *evidence set*: seven observable guard groups had no negative control, four spec behaviours had no test, one test asserted an email rule the spec does not state, and two contract questions were left implicit. Every item is addressed below.

### 3.1 Seven missing negative controls (finding P1)

Added as controls `b26`–`b33`; all seven are caught by the suite and exit 0:

| Audit finding | New control | Guard removed |
| --- | --- | --- |
| g01 | `b27_forecast_weights` | proposal 30 → 20, negotiation 60 → 30 in `forecast` |
| g02 | `b28_transfer_final_stage` | `transfer`'s final-stage check |
| g03 | `b29_discount_final_stage` | `discount`'s final-stage check |
| g04 | `b30_convert_bool_amount` | `convert`'s `isinstance(amount, bool)` clause |
| g05 | `b31_qualify_status_new` | `qualify`'s `status != "new"` check |
| g06 | `b32_score_domain_bonus` | the `+15` non-free-domain branch |
| g08 | `b33_load_status_filter` | the `status in ("new", "qualified")` filter in `_load` |

Four further controls close adjacent holes the first matrix also left open: `b26` (advance's named-stage check, audit g09/F6 — now caught by a dedicated ordering test instead of only `test_argument_validity_is_checked_before_permission`), `b38` (duplicate detection after conversion), `b39` (unhashable `actor`), `b40` (unhashable `new_owner`). Four atomicity controls were added for methods that previously had none: `b34` (advance/big deal), `b35` (convert/owner check), `b36` (transfer/capacity check), `b37` (add_lead/id counter). The matrix is now 40 controls, 40 × exit 0.

### 3.2 Missing guard tests (finding section "Missing guard tests")

| # | Spec clause | New test | Status |
| --- | --- | --- | --- |
| 1 | crm.md:42, per-opportunity truncation | `test_forecast_truncates_each_opportunity` (999→99, 333→99, 1001→600) | added, green |
| 2 | crm.md:34 r2, lower bound | `test_lower_bound_of_one_percent_is_accepted` (1000→990) | added, green |
| 3 | crm.md:38 r6, capacity−1 accepted | `test_target_at_capacity_minus_one_is_accepted` | added, green |
| 4 | crm.md:16, duplicate after conversion | `test_duplicate_after_conversion` (`existing_id` = converted lead) | added, green |
| 5 | crm.md:9, converted leads stop counting | `test_converted_lead_no_longer_counts_toward_load` (direct load assertion via assignment) | added, green |
| 6 | crm.md:7, unhashable actor (C2) | `test_unhashable_actor_rejected_by_every_method` (all six acting methods, state compared) | contract decided + tested |
| 7 | crm.md:13, leading-dot domain (C3) | `test_interior_dot_is_what_the_spec_requires` | behaviour made spec-literal + tested |

`test_failed_convert_on_unowned_lead_changes_nothing` was also added so the atomicity control `b35` has a test that inspects state rather than only the exception.

### 3.3 Contract decisions (C2, C3)

- **C2 — unhashable `actor` / `new_owner`.** crm.md:7 says an actor that is not the id of a known user must raise `PermissionError`. A list or dict is not a string id, so both `_require_actor` and `transfer` now type-check before the membership test: `actor=[]` raises `PermissionError` (previously `TypeError`), `new_owner=[]` raises `ValueError` (previously `TypeError`). Controls `b39`/`b40` prove the tests hold the contract.
- **C3 — `ana@.example.com`.** crm.md:13 requires the domain to contain "a `.` which is neither the first nor the last character of the domain". `.example.com` contains such a dot, so the rejection was stricter than the spec. `email_is_valid` was made literal (scan for at least one interior dot); `ana@.example.com` is now accepted, while `ana@.com`, `ana@example.` and `ana@.` (only edge dots) are still rejected. The old assertion that contradicted the spec was replaced by `test_interior_dot_is_what_the_spec_requires`.

### 3.4 Findings with no test (recorded, not papered over)

- **F5 — unreachable branches.** `transfer`'s `_free_slot(previous_owner)` and the multi-lead `while` loop in `_free_slot` cannot be observed: a non-empty waiting queue implies every rep is at capacity, and a transfer requires the target to have room. No test was written for either branch, because a reachable state does not exist under the spec's invariants. `b08` and `b07` continue to prove the reachable single-lead drain and its FIFO order.
- **P3 — queue-drain wording.** Section 8 now states the reachable coverage precisely: each free-slot event assigns at most one waiting lead.

## 4. Baseline test run (verbatim)

```text
$ rm -rf __pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py' -v
test_failed_add_lead_changes_nothing (test_atomicity.AtomicityTest.test_failed_add_lead_changes_nothing) ... ok
test_failed_add_lead_does_not_consume_an_id (test_atomicity.AtomicityTest.test_failed_add_lead_does_not_consume_an_id) ... ok
test_failed_add_lead_with_unknown_actor_changes_nothing (test_atomicity.AtomicityTest.test_failed_add_lead_with_unknown_actor_changes_nothing) ... ok
test_failed_advance_changes_nothing (test_atomicity.AtomicityTest.test_failed_advance_changes_nothing) ... ok
test_failed_advance_from_final_stage_changes_nothing (test_atomicity.AtomicityTest.test_failed_advance_from_final_stage_changes_nothing) ... ok
test_failed_big_deal_advance_changes_nothing (test_atomicity.AtomicityTest.test_failed_big_deal_advance_changes_nothing) ... ok
test_failed_convert_changes_nothing (test_atomicity.AtomicityTest.test_failed_convert_changes_nothing) ... ok
test_failed_convert_does_not_consume_an_opportunity_id (test_atomicity.AtomicityTest.test_failed_convert_does_not_consume_an_opportunity_id) ... ok
test_failed_convert_on_unowned_lead_changes_nothing (test_atomicity.AtomicityTest.test_failed_convert_on_unowned_lead_changes_nothing) ... ok
test_failed_cumulative_discount_changes_nothing (test_atomicity.AtomicityTest.test_failed_cumulative_discount_changes_nothing) ... ok
test_failed_discount_changes_nothing (test_atomicity.AtomicityTest.test_failed_discount_changes_nothing) ... ok
test_failed_discount_on_final_stage_changes_nothing (test_atomicity.AtomicityTest.test_failed_discount_on_final_stage_changes_nothing) ... ok
test_failed_qualify_changes_nothing (test_atomicity.AtomicityTest.test_failed_qualify_changes_nothing) ... ok
test_failed_qualify_on_wrong_status_changes_nothing (test_atomicity.AtomicityTest.test_failed_qualify_on_wrong_status_changes_nothing) ... ok
test_failed_transfer_changes_nothing (test_atomicity.AtomicityTest.test_failed_transfer_changes_nothing) ... ok
test_failed_transfer_on_final_stage_changes_nothing (test_atomicity.AtomicityTest.test_failed_transfer_on_final_stage_changes_nothing) ... ok
test_successful_calls_only_append_the_named_entries (test_atomicity.AtomicityTest.test_successful_calls_only_append_the_named_entries) ... ok
test_final_stages_are_terminal (test_pipeline.AdvanceTest.test_final_stages_are_terminal) ... ok
test_full_chain_logs_every_step (test_pipeline.AdvanceTest.test_full_chain_logs_every_step) ... ok
test_going_backwards_is_rejected (test_pipeline.AdvanceTest.test_going_backwards_is_rejected) ... ok
test_invalid_stage_names_are_rejected_before_the_permission_check (test_pipeline.AdvanceTest.test_invalid_stage_names_are_rejected_before_the_permission_check) ... ok
test_invalid_stage_names_rejected (test_pipeline.AdvanceTest.test_invalid_stage_names_rejected) ... ok
test_lost_is_reachable_from_every_open_stage (test_pipeline.AdvanceTest.test_lost_is_reachable_from_every_open_stage) ... ok
test_lost_is_terminal (test_pipeline.AdvanceTest.test_lost_is_terminal) ... ok
test_negotiation_can_go_lost (test_pipeline.AdvanceTest.test_negotiation_can_go_lost) ... ok
test_same_stage_is_rejected (test_pipeline.AdvanceTest.test_same_stage_is_rejected) ... ok
test_skipping_a_stage_is_rejected (test_pipeline.AdvanceTest.test_skipping_a_stage_is_rejected) ... ok
test_unknown_opportunity_rejected (test_pipeline.AdvanceTest.test_unknown_opportunity_rejected) ... ok
test_converted_lead_no_longer_counts_toward_load (test_pipeline.AssignmentTest.test_converted_lead_no_longer_counts_toward_load) ... ok
test_full_reps_produce_unowned_leads_in_queue (test_pipeline.AssignmentTest.test_full_reps_produce_unowned_leads_in_queue) ... ok
test_lowest_load_wins_and_alternates (test_pipeline.AssignmentTest.test_lowest_load_wins_and_alternates) ... ok
test_manager_never_receives_work (test_pipeline.AssignmentTest.test_manager_never_receives_work) ... ok
test_open_opportunities_count_toward_load (test_pipeline.AssignmentTest.test_open_opportunities_count_toward_load) ... ok
test_qualified_leads_still_count_toward_load (test_pipeline.AssignmentTest.test_qualified_leads_still_count_toward_load) ... ok
test_tie_breaks_on_smallest_id_string (test_pipeline.AssignmentTest.test_tie_breaks_on_smallest_id_string) ... ok
test_big_deal_can_still_go_lost_without_manager (test_pipeline.BigDealApprovalTest.test_big_deal_can_still_go_lost_without_manager) ... ok
test_exactly_fifty_thousand_needs_no_manager (test_pipeline.BigDealApprovalTest.test_exactly_fifty_thousand_needs_no_manager) ... ok
test_manager_can_take_big_deal_to_negotiation (test_pipeline.BigDealApprovalTest.test_manager_can_take_big_deal_to_negotiation) ... ok
test_rep_cannot_take_big_deal_to_negotiation (test_pipeline.BigDealApprovalTest.test_rep_cannot_take_big_deal_to_negotiation) ... ok
test_bad_amounts_are_rejected (test_pipeline.ConvertTest.test_bad_amounts_are_rejected) ... ok
test_opportunity_ids_increment_on_success_only (test_pipeline.ConvertTest.test_opportunity_ids_increment_on_success_only) ... ok
test_successful_conversion_shape (test_pipeline.ConvertTest.test_successful_conversion_shape) ... ok
test_unknown_lead_is_rejected (test_pipeline.ConvertTest.test_unknown_lead_is_rejected) ... ok
test_unowned_lead_is_rejected (test_pipeline.ConvertTest.test_unowned_lead_is_rejected) ... ok
test_unqualified_lead_is_rejected (test_pipeline.ConvertTest.test_unqualified_lead_is_rejected) ... ok
test_amount_truncation (test_pipeline.DiscountTest.test_amount_truncation) ... ok
test_cumulative_floor_is_enforced (test_pipeline.DiscountTest.test_cumulative_floor_is_enforced) ... ok
test_discount_logs (test_pipeline.DiscountTest.test_discount_logs) ... ok
test_discount_on_final_stage_rejected (test_pipeline.DiscountTest.test_discount_on_final_stage_rejected) ... ok
test_floor_uses_original_amount_and_integer_truncation (test_pipeline.DiscountTest.test_floor_uses_original_amount_and_integer_truncation) ... ok
test_invalid_percentages_rejected (test_pipeline.DiscountTest.test_invalid_percentages_rejected) ... ok
test_lower_bound_of_one_percent_is_accepted (test_pipeline.DiscountTest.test_lower_bound_of_one_percent_is_accepted) ... ok
test_manager_may_use_full_range (test_pipeline.DiscountTest.test_manager_may_use_full_range) ... ok
test_rep_limit_is_ten (test_pipeline.DiscountTest.test_rep_limit_is_ten) ... ok
test_repeated_rep_discounts_stop_at_the_floor (test_pipeline.DiscountTest.test_repeated_rep_discounts_stop_at_the_floor) ... ok
test_two_steps_can_reach_exactly_the_floor (test_pipeline.DiscountTest.test_two_steps_can_reach_exactly_the_floor) ... ok
test_discount_changes_weighted_value (test_pipeline.ForecastTest.test_discount_changes_weighted_value) ... ok
test_empty_crm (test_pipeline.ForecastTest.test_empty_crm) ... ok
test_forecast_does_not_log (test_pipeline.ForecastTest.test_forecast_does_not_log) ... ok
test_forecast_truncates_each_opportunity (test_pipeline.ForecastTest.test_forecast_truncates_each_opportunity) ... ok
test_lost_is_excluded (test_pipeline.ForecastTest.test_lost_is_excluded) ... ok
test_weights_and_won_sum (test_pipeline.ForecastTest.test_weights_and_won_sum) ... ok
test_argument_validity_is_checked_before_permission (test_pipeline.PermissionTest.test_argument_validity_is_checked_before_permission) ... ok
test_existence_is_checked_before_permission (test_pipeline.PermissionTest.test_existence_is_checked_before_permission) ... ok
test_manager_may_act_on_any_lead_and_opportunity (test_pipeline.PermissionTest.test_manager_may_act_on_any_lead_and_opportunity) ... ok
test_other_rep_cannot_advance (test_pipeline.PermissionTest.test_other_rep_cannot_advance) ... ok
test_other_rep_cannot_convert (test_pipeline.PermissionTest.test_other_rep_cannot_convert) ... ok
test_other_rep_cannot_discount (test_pipeline.PermissionTest.test_other_rep_cannot_discount) ... ok
test_other_rep_cannot_qualify (test_pipeline.PermissionTest.test_other_rep_cannot_qualify) ... ok
test_transfer_requires_manager_before_owner_validation (test_pipeline.PermissionTest.test_transfer_requires_manager_before_owner_validation) ... ok
test_unknown_actor_is_rejected_first_everywhere (test_pipeline.PermissionTest.test_unknown_actor_is_rejected_first_everywhere) ... ok
test_unowned_lead_cannot_be_qualified_by_a_rep (test_pipeline.PermissionTest.test_unowned_lead_cannot_be_qualified_by_a_rep) ... ok
test_cannot_qualify_converted_lead (test_pipeline.QualifyTest.test_cannot_qualify_converted_lead) ... ok
test_cannot_qualify_twice (test_pipeline.QualifyTest.test_cannot_qualify_twice) ... ok
test_threshold_boundary_is_qualifiable (test_pipeline.QualifyTest.test_threshold_boundary_is_qualifiable) ... ok
test_web_corporate_lead_below_threshold (test_pipeline.QualifyTest.test_web_corporate_lead_below_threshold) ... ok
test_web_free_domain_lead_below_threshold (test_pipeline.QualifyTest.test_web_free_domain_lead_below_threshold) ... ok
test_final_stage_rejected (test_pipeline.TransferTest.test_final_stage_rejected) ... ok
test_full_target_rejected (test_pipeline.TransferTest.test_full_target_rejected) ... ok
test_new_owner_must_be_a_known_rep (test_pipeline.TransferTest.test_new_owner_must_be_a_known_rep) ... ok
test_only_manager_may_transfer (test_pipeline.TransferTest.test_only_manager_may_transfer) ... ok
test_same_owner_rejected (test_pipeline.TransferTest.test_same_owner_rejected) ... ok
test_target_at_capacity_minus_one_is_accepted (test_pipeline.TransferTest.test_target_at_capacity_minus_one_is_accepted) ... ok
test_transfer_counts_open_opportunities_against_capacity (test_pipeline.TransferTest.test_transfer_counts_open_opportunities_against_capacity) ... ok
test_transfer_moves_owner_and_logs (test_pipeline.TransferTest.test_transfer_moves_owner_and_logs) ... ok
test_unknown_opportunity_rejected (test_pipeline.TransferTest.test_unknown_opportunity_rejected) ... ok
test_lost_stage_frees_the_slot_too (test_pipeline.WaitingQueueTest.test_lost_stage_frees_the_slot_too) ... ok
test_no_assignment_when_queue_is_empty (test_pipeline.WaitingQueueTest.test_no_assignment_when_queue_is_empty) ... ok
test_queue_is_fifo (test_pipeline.WaitingQueueTest.test_queue_is_fifo) ... ok
test_win_assigns_oldest_waiting_lead_and_logs_system (test_pipeline.WaitingQueueTest.test_win_assigns_oldest_waiting_lead_and_logs_system) ... ok
test_ids_increment_on_success_only (test_validation.AddLeadShapeTest.test_ids_increment_on_success_only) ... ok
test_lead_fields_and_log (test_validation.AddLeadShapeTest.test_lead_fields_and_log) ... ok
test_different_emails_are_not_duplicates (test_validation.DuplicateTest.test_different_emails_are_not_duplicates) ... ok
test_duplicate_after_conversion (test_validation.DuplicateTest.test_duplicate_after_conversion) ... ok
test_duplicate_after_normalization (test_validation.DuplicateTest.test_duplicate_after_normalization) ... ok
test_duplicate_check_runs_after_name_validation (test_validation.DuplicateTest.test_duplicate_check_runs_after_name_validation) ... ok
test_duplicate_check_runs_after_source_validation (test_validation.DuplicateTest.test_duplicate_check_runs_after_source_validation) ... ok
test_failed_duplicate_does_not_consume_an_id (test_validation.DuplicateTest.test_failed_duplicate_does_not_consume_an_id) ... ok
test_domain_without_dot_rejected (test_validation.EmailValidationTest.test_domain_without_dot_rejected) ... ok
test_dot_on_domain_edges_rejected (test_validation.EmailValidationTest.test_dot_on_domain_edges_rejected) ... ok
test_empty_local_part_rejected (test_validation.EmailValidationTest.test_empty_local_part_rejected) ... ok
test_empty_or_missing_domain_rejected (test_validation.EmailValidationTest.test_empty_or_missing_domain_rejected) ... ok
test_interior_dot_is_what_the_spec_requires (test_validation.EmailValidationTest.test_interior_dot_is_what_the_spec_requires) ... ok
test_missing_at_rejected (test_validation.EmailValidationTest.test_missing_at_rejected) ... ok
test_multiple_at_rejected (test_validation.EmailValidationTest.test_multiple_at_rejected) ... ok
test_non_string_email_rejected (test_validation.EmailValidationTest.test_non_string_email_rejected) ... ok
test_valid_email_stored_normalized (test_validation.EmailValidationTest.test_valid_email_stored_normalized) ... ok
test_blank_name_rejected (test_validation.NameValidationTest.test_blank_name_rejected) ... ok
test_name_is_stored_stripped (test_validation.NameValidationTest.test_name_is_stored_stripped) ... ok
test_non_string_name_rejected (test_validation.NameValidationTest.test_non_string_name_rejected) ... ok
test_free_domains_are_exact_after_normalization (test_validation.SourceValidationTest.test_free_domains_are_exact_after_normalization) ... ok
test_source_scores_for_free_domains (test_validation.SourceValidationTest.test_source_scores_for_free_domains) ... ok
test_source_scores_include_domain_bonus (test_validation.SourceValidationTest.test_source_scores_include_domain_bonus) ... ok
test_unknown_source_rejected (test_validation.SourceValidationTest.test_unknown_source_rejected) ... ok
test_unhashable_actor_rejected_by_every_method (test_validation.UnhashableActorTest.test_unhashable_actor_rejected_by_every_method) ... ok

----------------------------------------------------------------------
Ran 115 tests in 0.004s

OK
[exit 0]
```



## 5. Negative-control matrix

Each control backs up `crm.py`, removes exactly one guard, runs the suite, restores `crm.py`, and runs the suite again. `aepkit` exits 0 only when the suite fails under the break, the failing output matches the expected test name, and the suite passes after the restore.

| Guard group | Control | Expected failing test | Result |
| --- | --- | --- | --- |
| email validation | `b01_email_validation` | `test_missing_at_rejected` | verified: exit 0 |
| name validation | `b02_name_validation` | `test_blank_name_rejected` | verified: exit 0 |
| source validation | `b03_source_validation` | `test_unknown_source_rejected` | verified: exit 0 |
| duplicate detection | `b04_duplicate_detection` | `test_duplicate_after_normalization` | verified: exit 0 |
| rep assignment (lowest load / tie-break) | `b05_lowest_load_choice` | `test_lowest_load_wins_and_alternates` | verified: exit 0 |
| capacity + waiting queue | `b06_capacity_check` | `test_full_reps_produce_unowned_leads_in_queue` | verified: exit 0 |
| FIFO waiting queue | `b07_queue_fifo` | `test_queue_is_fifo` | verified: exit 0 |
| queue drain when a slot frees | `b08_queue_drain_on_final` | `test_win_assigns_oldest_waiting_lead_and_logs_system` | verified: exit 0 |
| permission: owner-or-manager (advance/discount) | `b09_permission_owner_or_manager` | `test_other_rep_cannot_advance` | verified: exit 0 |
| permission: unknown actor rejected first | `b10_unknown_actor` | `test_unknown_actor_is_rejected_first_everywhere` | verified: exit 0 |
| qualification score threshold | `b11_score_threshold` | `test_web_free_domain_lead_below_threshold` | verified: exit 0 |
| stage-transition order | `b12_stage_transition_order` | `test_skipping_a_stage_is_rejected` | verified: exit 0 |
| stage-transition: final stages are terminal | `b13_stage_final_guard` | `test_final_stages_are_terminal` | verified: exit 0 |
| big-deal approval (> 50000 to negotiation) | `b14_big_deal_manager` | `test_rep_cannot_take_big_deal_to_negotiation` | verified: exit 0 |
| discount percentage limits | `b15_discount_pct_range` | `test_invalid_percentages_rejected` | verified: exit 0 |
| discount: rep limit of 10 | `b16_discount_rep_limit` | `test_rep_limit_is_ten` | verified: exit 0 |
| discount: cumulative 30% floor | `b17_discount_cumulative_floor` | `test_cumulative_floor_is_enforced` | verified: exit 0 |
| transfer: new owner must be a rep | `b18_transfer_rep_role` | `test_new_owner_must_be_a_known_rep` | verified: exit 0 |
| transfer: target capacity | `b19_transfer_capacity` | `test_full_target_rejected` | verified: exit 0 |
| transfer: new owner differs | `b20_transfer_same_owner` | `test_same_owner_rejected` | verified: exit 0 |
| atomicity: failed discount mutates nothing | `b21_atomicity_discount` | `test_failed_cumulative_discount_changes_nothing` | verified: exit 0 |
| atomicity: failed qualify mutates nothing | `b22_atomicity_qualify` | `test_failed_qualify_changes_nothing` | verified: exit 0 |
| permission: qualify owner-or-manager | `b23_permission_qualify_actor` | `test_other_rep_cannot_qualify` | verified: exit 0 |
| permission: convert owner-or-manager | `b24_permission_convert_actor` | `test_other_rep_cannot_convert` | verified: exit 0 |
| permission: transfer manager-only | `b25_transfer_manager_only` | `test_only_manager_may_transfer` | verified: exit 0 |
| stage names validated before permission (audit g09) | `b26_advance_valid_stage_name` | `test_invalid_stage_names_are_rejected_before_the_permission_check` | verified: exit 0 |
| forecast weights (audit g01) | `b27_forecast_weights` | `test_weights_and_won_sum` | verified: exit 0 |
| transfer final-stage guard (audit g02) | `b28_transfer_final_stage` | `test_final_stage_rejected` | verified: exit 0 |
| discount final-stage guard (audit g03) | `b29_discount_final_stage` | `test_discount_on_final_stage_rejected` | verified: exit 0 |
| convert bool-amount guard (audit g04) | `b30_convert_bool_amount` | `test_bad_amounts_are_rejected` | verified: exit 0 |
| qualify status guard (audit g05) | `b31_qualify_status_new` | `test_cannot_qualify_twice` | verified: exit 0 |
| non-free-domain score bonus (audit g06) | `b32_score_domain_bonus` | `test_source_scores_include_domain_bonus` | verified: exit 0 |
| `_load` status filter (audit g08) | `b33_load_status_filter` | `test_converted_lead_no_longer_counts_toward_load` | verified: exit 0 |
| atomicity: failed big-deal advance | `b34_atomicity_advance` | `test_failed_big_deal_advance_changes_nothing` | verified: exit 0 |
| atomicity: failed convert on unowned lead | `b35_atomicity_convert` | `test_failed_convert_on_unowned_lead_changes_nothing` | verified: exit 0 |
| atomicity: failed transfer at capacity | `b36_atomicity_transfer` | `test_failed_transfer_changes_nothing` | verified: exit 0 |
| atomicity: failed duplicate does not consume an id | `b37_atomicity_add_lead` | `test_failed_duplicate_does_not_consume_an_id` | verified: exit 0 |
| duplicate detection after conversion | `b38_duplicate_ignores_converted_leads` | `test_duplicate_after_conversion` | verified: exit 0 |
| unhashable actor → PermissionError (C2) | `b39_unhashable_actor` | `test_unhashable_actor_rejected_by_every_method` | verified: exit 0 |
| unhashable new owner → ValueError (C2) | `b40_unhashable_new_owner` | `test_new_owner_must_be_a_known_rep` | verified: exit 0 |

All 40 controls exit 0. The suite is 115 tests.

## 6. Negative-control transcripts (verbatim)

Full transcripts, copied from `negcontrol-log.md` without edits:

# Negative-control log

Each block is a verbatim transcript of the shell command and its complete output.

- harness: /tmp/aep-lab/v060/bin/aepkit negcontrol (backup / break / test / restore / test)
- python: Python 3.14.7
- module under test: /tmp/aep-lab/pilot2/AE-neutral-3/crm.py

## control b01_email_validation

```text
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b01_email_validation" --test-cmd "rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'" --expect "test_missing_at_rejected" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-m5oq091q/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b01_email_validation
break applied: b01_email_validation
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect FAILURE matching /test_missing_at_rejected/
FF........................................................................................F.......FFFF.FF..........
======================================================================
FAIL: test_failed_add_lead_changes_nothing (test_atomicity.AtomicityTest.test_failed_add_lead_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_atomicity.py", line 48, in test_failed_add_lead_changes_nothing
    self.assert_atomic(
    ~~~~~~~~~~~~~~~~~~^
        lambda: self.crm.add_lead("nope", "X", "web", "rep1"), ValueError
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_atomicity.py", line 43, in assert_atomic
    with self.assertRaises(exc):
         ~~~~~~~~~~~~~~~~~^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_failed_add_lead_does_not_consume_an_id (test_atomicity.AtomicityTest.test_failed_add_lead_does_not_consume_an_id)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_atomicity.py", line 63, in test_failed_add_lead_does_not_consume_an_id
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_ids_increment_on_success_only (test_validation.AddLeadShapeTest.test_ids_increment_on_success_only)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_validation.py", line 243, in test_ids_increment_on_success_only
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_domain_without_dot_rejected (test_validation.EmailValidationTest.test_domain_without_dot_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_validation.py", line 53, in test_domain_without_dot_rejected
    self.assert_rejected("ana@localhost")
    ~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_validation.py", line 29, in assert_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_dot_on_domain_edges_rejected (test_validation.EmailValidationTest.test_dot_on_domain_edges_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_validation.py", line 59, in test_dot_on_domain_edges_rejected
    self.assert_rejected(bad)
    ~~~~~~~~~~~~~~~~~~~~^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_validation.py", line 29, in assert_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_empty_local_part_rejected (test_validation.EmailValidationTest.test_empty_local_part_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_validation.py", line 46, in test_empty_local_part_rejected
    self.assert_rejected(bad)
    ~~~~~~~~~~~~~~~~~~~~^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_validation.py", line 29, in assert_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_empty_or_missing_domain_rejected (test_validation.EmailValidationTest.test_empty_or_missing_domain_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_validation.py", line 50, in test_empty_or_missing_domain_rejected
    self.assert_rejected(bad)
    ~~~~~~~~~~~~~~~~~~~~^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_validation.py", line 29, in assert_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_missing_at_rejected (test_validation.EmailValidationTest.test_missing_at_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_validation.py", line 38, in test_missing_at_rejected
    self.assert_rejected("ana.example.com")
    ~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_validation.py", line 29, in assert_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_multiple_at_rejected (test_validation.EmailValidationTest.test_multiple_at_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_validation.py", line 42, in test_multiple_at_rejected
    self.assert_rejected(bad)
    ~~~~~~~~~~~~~~~~~~~~^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_validation.py", line 29, in assert_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 115 tests in 0.004s

FAILED (failures=9)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-3/crm.py from backup (byte-identical)
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect SUCCESS
...................................................................................................................
----------------------------------------------------------------------
Ran 115 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
[exit 0]
```

## control b02_name_validation

```text
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b02_name_validation" --test-cmd "rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'" --expect "test_blank_name_rejected" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-68onxk58/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b02_name_validation
break applied: b02_name_validation
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect FAILURE matching /test_blank_name_rejected/
F..............................................................................................E...........F.E.....
======================================================================
ERROR: test_duplicate_check_runs_after_name_validation (test_validation.DuplicateTest.test_duplicate_check_runs_after_name_validation)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_validation.py", line 140, in test_duplicate_check_runs_after_name_validation
    self.crm.add_lead("ana@example.com", "  ", "web", "rep1")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-3/crm.py", line 126, in add_lead
    raise DuplicateLeadError(existing["id"])
crm.DuplicateLeadError: duplicate lead email, existing lead L1

======================================================================
ERROR: test_non_string_name_rejected (test_validation.NameValidationTest.test_non_string_name_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_validation.py", line 78, in test_non_string_name_rejected
    self.crm.add_lead("ana@example.com", bad, "web", "rep1")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-3/crm.py", line 137, in add_lead
    "name": name.strip(),
            ^^^^^^^^^^
AttributeError: 'NoneType' object has no attribute 'strip'

======================================================================
FAIL: test_failed_add_lead_changes_nothing (test_atomicity.AtomicityTest.test_failed_add_lead_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_atomicity.py", line 51, in test_failed_add_lead_changes_nothing
    self.assert_atomic(
    ~~~~~~~~~~~~~~~~~~^
        lambda: self.crm.add_lead("x@corp.io", "  ", "web", "rep1"), ValueError
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_atomicity.py", line 43, in assert_atomic
    with self.assertRaises(exc):
         ~~~~~~~~~~~~~~~~~^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_blank_name_rejected (test_validation.NameValidationTest.test_blank_name_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_validation.py", line 83, in test_blank_name_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 115 tests in 0.004s

FAILED (failures=2, errors=2)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-3/crm.py from backup (byte-identical)
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect SUCCESS
...................................................................................................................
----------------------------------------------------------------------
Ran 115 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
[exit 0]
```

## control b03_source_validation

```text
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b03_source_validation" --test-cmd "rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'" --expect "test_unknown_source_rejected" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-9mp45n22/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b03_source_validation
break applied: b03_source_validation
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect FAILURE matching /test_unknown_source_rejected/
E...............................................................................................E................E.
======================================================================
ERROR: test_failed_add_lead_changes_nothing (test_atomicity.AtomicityTest.test_failed_add_lead_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_atomicity.py", line 54, in test_failed_add_lead_changes_nothing
    self.assert_atomic(
    ~~~~~~~~~~~~~~~~~~^
        lambda: self.crm.add_lead("x@corp.io", "X", "radio", "rep1"), ValueError
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_atomicity.py", line 44, in assert_atomic
    call()
    ~~~~^^
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_atomicity.py", line 55, in <lambda>
    lambda: self.crm.add_lead("x@corp.io", "X", "radio", "rep1"), ValueError
            ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-3/crm.py", line 128, in add_lead
    score = SOURCE_SCORES[source]
            ~~~~~~~~~~~~~^^^^^^^^
KeyError: 'radio'

======================================================================
ERROR: test_duplicate_check_runs_after_source_validation (test_validation.DuplicateTest.test_duplicate_check_runs_after_source_validation)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_validation.py", line 135, in test_duplicate_check_runs_after_source_validation
    self.crm.add_lead("ana@example.com", "Ana", "podcast", "rep1")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-3/crm.py", line 126, in add_lead
    raise DuplicateLeadError(existing["id"])
crm.DuplicateLeadError: duplicate lead email, existing lead L1

======================================================================
ERROR: test_unknown_source_rejected (test_validation.SourceValidationTest.test_unknown_source_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_validation.py", line 96, in test_unknown_source_rejected
    self.crm.add_lead("ana@example.com", "Ana", bad, "rep1")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-3/crm.py", line 128, in add_lead
    score = SOURCE_SCORES[source]
            ~~~~~~~~~~~~~^^^^^^^^
KeyError: 'ads'

----------------------------------------------------------------------
Ran 115 tests in 0.004s

FAILED (errors=3)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-3/crm.py from backup (byte-identical)
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect SUCCESS
...................................................................................................................
----------------------------------------------------------------------
Ran 115 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
[exit 0]
```

## control b04_duplicate_detection

```text
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b04_duplicate_detection" --test-cmd "rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'" --expect "test_duplicate_after_normalization" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-omgn0jtf/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b04_duplicate_detection
break applied: b04_duplicate_detection
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect FAILURE matching /test_duplicate_after_normalization/
F............................................................................................FF..F.................
======================================================================
FAIL: test_failed_add_lead_changes_nothing (test_atomicity.AtomicityTest.test_failed_add_lead_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_atomicity.py", line 57, in test_failed_add_lead_changes_nothing
    self.assert_atomic(
    ~~~~~~~~~~~~~~~~~~^
        lambda: self.crm.add_lead("ANA@corp.io ", "X", "web", "rep1"),
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        DuplicateLeadError,
        ^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_atomicity.py", line 43, in assert_atomic
    with self.assertRaises(exc):
         ~~~~~~~~~~~~~~~~~^^^^^
AssertionError: DuplicateLeadError not raised

======================================================================
FAIL: test_duplicate_after_conversion (test_validation.DuplicateTest.test_duplicate_after_conversion)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_validation.py", line 160, in test_duplicate_after_conversion
    with self.assertRaises(DuplicateLeadError) as caught:
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
AssertionError: DuplicateLeadError not raised

======================================================================
FAIL: test_duplicate_after_normalization (test_validation.DuplicateTest.test_duplicate_after_normalization)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_validation.py", line 126, in test_duplicate_after_normalization
    with self.assertRaises(DuplicateLeadError) as caught:
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
AssertionError: DuplicateLeadError not raised

======================================================================
FAIL: test_failed_duplicate_does_not_consume_an_id (test_validation.DuplicateTest.test_failed_duplicate_does_not_consume_an_id)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_validation.py", line 144, in test_failed_duplicate_does_not_consume_an_id
    with self.assertRaises(DuplicateLeadError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
AssertionError: DuplicateLeadError not raised

----------------------------------------------------------------------
Ran 115 tests in 0.004s

FAILED (failures=4)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-3/crm.py from backup (byte-identical)
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect SUCCESS
...................................................................................................................
----------------------------------------------------------------------
Ran 115 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
[exit 0]
```

## control b05_lowest_load_choice

```text
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b05_lowest_load_choice" --test-cmd "rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'" --expect "test_lowest_load_wins_and_alternates" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-9ddh7xqk/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b05_lowest_load_choice
break applied: b05_lowest_load_choice
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect FAILURE matching /test_lowest_load_wins_and_alternates/
..............................F...................................................FF...............................
======================================================================
FAIL: test_lowest_load_wins_and_alternates (test_pipeline.AssignmentTest.test_lowest_load_wins_and_alternates)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_pipeline.py", line 53, in test_lowest_load_wins_and_alternates
    self.assertEqual(owners, ["rep1", "rep2", "rep1", "rep2"])
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: ['rep1', 'rep1', 'rep1', 'rep1'] != ['rep1', 'rep2', 'rep1', 'rep2']

First differing element 1:
'rep1'
'rep2'

- ['rep1', 'rep1', 'rep1', 'rep1']
+ ['rep1', 'rep2', 'rep1', 'rep2']

======================================================================
FAIL: test_target_at_capacity_minus_one_is_accepted (test_pipeline.TransferTest.test_target_at_capacity_minus_one_is_accepted)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_pipeline.py", line 569, in test_target_at_capacity_minus_one_is_accepted
    self.assertEqual(crm.leads["L2"]["owner"], "rep2")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'rep1' != 'rep2'
- rep1
?    ^
+ rep2
?    ^


======================================================================
FAIL: test_transfer_counts_open_opportunities_against_capacity (test_pipeline.TransferTest.test_transfer_counts_open_opportunities_against_capacity)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_pipeline.py", line 557, in test_transfer_counts_open_opportunities_against_capacity
    self.assertEqual(crm.leads[other]["owner"], "rep2")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'rep1' != 'rep2'
- rep1
?    ^
+ rep2
?    ^


----------------------------------------------------------------------
Ran 115 tests in 0.005s

FAILED (failures=3)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-3/crm.py from backup (byte-identical)
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect SUCCESS
...................................................................................................................
----------------------------------------------------------------------
Ran 115 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
[exit 0]
```

## control b06_capacity_check

```text
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b06_capacity_check" --test-cmd "rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'" --expect "test_full_reps_produce_unowned_leads_in_queue" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-a25xb0my/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b06_capacity_check
break applied: b06_capacity_check
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect FAILURE matching /test_full_reps_produce_unowned_leads_in_queue/
FFFFFFFFFFFFFFFFF............F.FFF.........F.....................F.F...F..............F.EF.........................
======================================================================
ERROR: test_queue_is_fifo (test_pipeline.WaitingQueueTest.test_queue_is_fifo)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_pipeline.py", line 120, in test_queue_is_fifo
    crm.qualify(second, "rep1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-3/crm.py", line 153, in qualify
    raise PermissionError("actor may not qualify this lead")
PermissionError: actor may not qualify this lead

======================================================================
FAIL: test_failed_add_lead_changes_nothing (test_atomicity.AtomicityTest.test_failed_add_lead_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_atomicity.py", line 39, in setUp
    self.assertEqual(self.crm.waiting, [self.queued_id])
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: [] != ['L2']

Second list contains 1 additional elements.
First extra element 0:
'L2'

- []
+ ['L2']

======================================================================
FAIL: test_failed_add_lead_does_not_consume_an_id (test_atomicity.AtomicityTest.test_failed_add_lead_does_not_consume_an_id)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_atomicity.py", line 39, in setUp
    self.assertEqual(self.crm.waiting, [self.queued_id])
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: [] != ['L2']

Second list contains 1 additional elements.
First extra element 0:
'L2'

- []
+ ['L2']

======================================================================
FAIL: test_failed_add_lead_with_unknown_actor_changes_nothing (test_atomicity.AtomicityTest.test_failed_add_lead_with_unknown_actor_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_atomicity.py", line 39, in setUp
    self.assertEqual(self.crm.waiting, [self.queued_id])
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: [] != ['L2']

Second list contains 1 additional elements.
First extra element 0:
'L2'

- []
+ ['L2']

======================================================================
FAIL: test_failed_advance_changes_nothing (test_atomicity.AtomicityTest.test_failed_advance_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_atomicity.py", line 39, in setUp
    self.assertEqual(self.crm.waiting, [self.queued_id])
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: [] != ['L2']

Second list contains 1 additional elements.
First extra element 0:
'L2'

- []
+ ['L2']

======================================================================
FAIL: test_failed_advance_from_final_stage_changes_nothing (test_atomicity.AtomicityTest.test_failed_advance_from_final_stage_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_atomicity.py", line 39, in setUp
    self.assertEqual(self.crm.waiting, [self.queued_id])
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: [] != ['L2']

Second list contains 1 additional elements.
First extra element 0:
'L2'

- []
+ ['L2']

======================================================================
FAIL: test_failed_big_deal_advance_changes_nothing (test_atomicity.AtomicityTest.test_failed_big_deal_advance_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_atomicity.py", line 39, in setUp
    self.assertEqual(self.crm.waiting, [self.queued_id])
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: [] != ['L2']

Second list contains 1 additional elements.
First extra element 0:
'L2'

- []
+ ['L2']

======================================================================
FAIL: test_failed_convert_changes_nothing (test_atomicity.AtomicityTest.test_failed_convert_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_atomicity.py", line 39, in setUp
    self.assertEqual(self.crm.waiting, [self.queued_id])
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: [] != ['L2']

Second list contains 1 additional elements.
First extra element 0:
'L2'

- []
+ ['L2']

======================================================================
FAIL: test_failed_convert_does_not_consume_an_opportunity_id (test_atomicity.AtomicityTest.test_failed_convert_does_not_consume_an_opportunity_id)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_atomicity.py", line 39, in setUp
    self.assertEqual(self.crm.waiting, [self.queued_id])
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: [] != ['L2']

Second list contains 1 additional elements.
First extra element 0:
'L2'

- []
+ ['L2']

======================================================================
FAIL: test_failed_convert_on_unowned_lead_changes_nothing (test_atomicity.AtomicityTest.test_failed_convert_on_unowned_lead_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_atomicity.py", line 39, in setUp
    self.assertEqual(self.crm.waiting, [self.queued_id])
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: [] != ['L2']

Second list contains 1 additional elements.
First extra element 0:
'L2'

- []
+ ['L2']

======================================================================
FAIL: test_failed_cumulative_discount_changes_nothing (test_atomicity.AtomicityTest.test_failed_cumulative_discount_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_atomicity.py", line 39, in setUp
    self.assertEqual(self.crm.waiting, [self.queued_id])
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: [] != ['L2']

Second list contains 1 additional elements.
First extra element 0:
'L2'

- []
+ ['L2']

======================================================================
FAIL: test_failed_discount_changes_nothing (test_atomicity.AtomicityTest.test_failed_discount_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_atomicity.py", line 39, in setUp
    self.assertEqual(self.crm.waiting, [self.queued_id])
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: [] != ['L2']

Second list contains 1 additional elements.
First extra element 0:
'L2'

- []
+ ['L2']

======================================================================
FAIL: test_failed_discount_on_final_stage_changes_nothing (test_atomicity.AtomicityTest.test_failed_discount_on_final_stage_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_atomicity.py", line 39, in setUp
    self.assertEqual(self.crm.waiting, [self.queued_id])
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: [] != ['L2']

Second list contains 1 additional elements.
First extra element 0:
'L2'

- []
+ ['L2']

======================================================================
FAIL: test_failed_qualify_changes_nothing (test_atomicity.AtomicityTest.test_failed_qualify_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_atomicity.py", line 39, in setUp
    self.assertEqual(self.crm.waiting, [self.queued_id])
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: [] != ['L2']

Second list contains 1 additional elements.
First extra element 0:
'L2'

- []
+ ['L2']

======================================================================
FAIL: test_failed_qualify_on_wrong_status_changes_nothing (test_atomicity.AtomicityTest.test_failed_qualify_on_wrong_status_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_atomicity.py", line 39, in setUp
    self.assertEqual(self.crm.waiting, [self.queued_id])
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: [] != ['L2']

Second list contains 1 additional elements.
First extra element 0:
'L2'

- []
+ ['L2']

======================================================================
FAIL: test_failed_transfer_changes_nothing (test_atomicity.AtomicityTest.test_failed_transfer_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_atomicity.py", line 39, in setUp
    self.assertEqual(self.crm.waiting, [self.queued_id])
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: [] != ['L2']

Second list contains 1 additional elements.
First extra element 0:
'L2'

- []
+ ['L2']

======================================================================
FAIL: test_failed_transfer_on_final_stage_changes_nothing (test_atomicity.AtomicityTest.test_failed_transfer_on_final_stage_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_atomicity.py", line 39, in setUp
    self.assertEqual(self.crm.waiting, [self.queued_id])
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: [] != ['L2']

Second list contains 1 additional elements.
First extra element 0:
'L2'

- []
+ ['L2']

======================================================================
FAIL: test_successful_calls_only_append_the_named_entries (test_atomicity.AtomicityTest.test_successful_calls_only_append_the_named_entries)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_atomicity.py", line 39, in setUp
    self.assertEqual(self.crm.waiting, [self.queued_id])
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: [] != ['L2']

Second list contains 1 additional elements.
First extra element 0:
'L2'

- []
+ ['L2']

======================================================================
FAIL: test_full_reps_produce_unowned_leads_in_queue (test_pipeline.AssignmentTest.test_full_reps_produce_unowned_leads_in_queue)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_pipeline.py", line 61, in test_full_reps_produce_unowned_leads_in_queue
    self.assertIsNone(crm.leads[second]["owner"])
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'rep2' is not None

======================================================================
FAIL: test_manager_never_receives_work (test_pipeline.AssignmentTest.test_manager_never_receives_work)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_pipeline.py", line 68, in test_manager_never_receives_work
    self.assertIsNone(crm.leads[lead_id]["owner"])
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'rep1' is not None

======================================================================
FAIL: test_open_opportunities_count_toward_load (test_pipeline.AssignmentTest.test_open_opportunities_count_toward_load)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_pipeline.py", line 84, in test_open_opportunities_count_toward_load
    self.assertIsNone(crm.leads[second]["owner"])
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'rep2' is not None

======================================================================
FAIL: test_qualified_leads_still_count_toward_load (test_pipeline.AssignmentTest.test_qualified_leads_still_count_toward_load)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_pipeline.py", line 75, in test_qualified_leads_still_count_toward_load
    self.assertIsNone(crm.leads[second]["owner"])
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'rep2' is not None

======================================================================
FAIL: test_unowned_lead_is_rejected (test_pipeline.ConvertTest.test_unowned_lead_is_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_pipeline.py", line 289, in test_unowned_lead_is_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_other_rep_cannot_advance (test_pipeline.PermissionTest.test_other_rep_cannot_advance)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_pipeline.py", line 180, in test_other_rep_cannot_advance
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_other_rep_cannot_discount (test_pipeline.PermissionTest.test_other_rep_cannot_discount)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_pipeline.py", line 184, in test_other_rep_cannot_discount
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_unowned_lead_cannot_be_qualified_by_a_rep (test_pipeline.PermissionTest.test_unowned_lead_cannot_be_qualified_by_a_rep)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_pipeline.py", line 221, in test_unowned_lead_cannot_be_qualified_by_a_rep
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_lost_stage_frees_the_slot_too (test_pipeline.WaitingQueueTest.test_lost_stage_frees_the_slot_too)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_pipeline.py", line 144, in test_lost_stage_frees_the_slot_too
    self.assertEqual(crm.leads[waiting_id]["owner"], "rep1")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'rep2' != 'rep1'
- rep2
?    ^
+ rep1
?    ^


======================================================================
FAIL: test_win_assigns_oldest_waiting_lead_and_logs_system (test_pipeline.WaitingQueueTest.test_win_assigns_oldest_waiting_lead_and_logs_system)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_pipeline.py", line 109, in test_win_assigns_oldest_waiting_lead_and_logs_system
    self.assertIsNone(crm.leads[waiting_id]["owner"])
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'rep2' is not None

----------------------------------------------------------------------
Ran 115 tests in 0.006s

FAILED (failures=27, errors=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-3/crm.py from backup (byte-identical)
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect SUCCESS
...................................................................................................................
----------------------------------------------------------------------
Ran 115 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
[exit 0]
```

## control b07_queue_fifo

```text
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b07_queue_fifo" --test-cmd "rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'" --expect "test_queue_is_fifo" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-hybstm3a/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b07_queue_fifo
break applied: b07_queue_fifo
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect FAILURE matching /test_queue_is_fifo/
........................................................................................F..........................
======================================================================
FAIL: test_queue_is_fifo (test_pipeline.WaitingQueueTest.test_queue_is_fifo)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_pipeline.py", line 125, in test_queue_is_fifo
    self.assertEqual(crm.leads[third]["owner"], "rep1")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: None != 'rep1'

----------------------------------------------------------------------
Ran 115 tests in 0.004s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-3/crm.py from backup (byte-identical)
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect SUCCESS
...................................................................................................................
----------------------------------------------------------------------
Ran 115 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
[exit 0]
```

## control b08_queue_drain_on_final

```text
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b08_queue_drain_on_final" --test-cmd "rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'" --expect "test_win_assigns_oldest_waiting_lead_and_logs_system" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-bcutstd_/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b08_queue_drain_on_final
break applied: b08_queue_drain_on_final
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect FAILURE matching /test_win_assigns_oldest_waiting_lead_and_logs_system/
................F.....................................................................F.FF.........................
======================================================================
FAIL: test_successful_calls_only_append_the_named_entries (test_atomicity.AtomicityTest.test_successful_calls_only_append_the_named_entries)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_atomicity.py", line 224, in test_successful_calls_only_append_the_named_entries
    self.assertEqual(self.crm.log[-2], ("advance", self.opp_id, "rep1"))
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Tuples differ: ('add_lead', 'L2', 'rep1') != ('advance', 'O1', 'rep1')

First differing element 0:
'add_lead'
'advance'

- ('add_lead', 'L2', 'rep1')
+ ('advance', 'O1', 'rep1')

======================================================================
FAIL: test_lost_stage_frees_the_slot_too (test_pipeline.WaitingQueueTest.test_lost_stage_frees_the_slot_too)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_pipeline.py", line 144, in test_lost_stage_frees_the_slot_too
    self.assertEqual(crm.leads[waiting_id]["owner"], "rep1")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: None != 'rep1'

======================================================================
FAIL: test_queue_is_fifo (test_pipeline.WaitingQueueTest.test_queue_is_fifo)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_pipeline.py", line 125, in test_queue_is_fifo
    self.assertEqual(crm.leads[third]["owner"], "rep1")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: None != 'rep1'

======================================================================
FAIL: test_win_assigns_oldest_waiting_lead_and_logs_system (test_pipeline.WaitingQueueTest.test_win_assigns_oldest_waiting_lead_and_logs_system)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_pipeline.py", line 111, in test_win_assigns_oldest_waiting_lead_and_logs_system
    self.assertEqual(crm.leads[waiting_id]["owner"], "rep1")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: None != 'rep1'

----------------------------------------------------------------------
Ran 115 tests in 0.004s

FAILED (failures=4)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-3/crm.py from backup (byte-identical)
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect SUCCESS
...................................................................................................................
----------------------------------------------------------------------
Ran 115 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
[exit 0]
```

## control b09_permission_owner_or_manager

```text
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b09_permission_owner_or_manager" --test-cmd "rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'" --expect "test_other_rep_cannot_advance" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-38tbxlqw/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b09_permission_owner_or_manager
break applied: b09_permission_owner_or_manager
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect FAILURE matching /test_other_rep_cannot_advance/
...F......F......................................................F.F...............................................
======================================================================
FAIL: test_failed_advance_changes_nothing (test_atomicity.AtomicityTest.test_failed_advance_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_atomicity.py", line 129, in test_failed_advance_changes_nothing
    self.assert_atomic(
    ~~~~~~~~~~~~~~~~~~^
        lambda: self.crm.advance(self.opp_id, "proposal", "rep2"), PermissionError
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_atomicity.py", line 43, in assert_atomic
    with self.assertRaises(exc):
         ~~~~~~~~~~~~~~~~~^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_failed_discount_changes_nothing (test_atomicity.AtomicityTest.test_failed_discount_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_atomicity.py", line 168, in test_failed_discount_changes_nothing
    self.assert_atomic(
    ~~~~~~~~~~~~~~~~~~^
        lambda: self.crm.discount(self.opp_id, 5, "rep2"), PermissionError
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_atomicity.py", line 43, in assert_atomic
    with self.assertRaises(exc):
         ~~~~~~~~~~~~~~~~~^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_other_rep_cannot_advance (test_pipeline.PermissionTest.test_other_rep_cannot_advance)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_pipeline.py", line 180, in test_other_rep_cannot_advance
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_other_rep_cannot_discount (test_pipeline.PermissionTest.test_other_rep_cannot_discount)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_pipeline.py", line 184, in test_other_rep_cannot_discount
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

----------------------------------------------------------------------
Ran 115 tests in 0.004s

FAILED (failures=4)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-3/crm.py from backup (byte-identical)
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect SUCCESS
...................................................................................................................
----------------------------------------------------------------------
Ran 115 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
[exit 0]
```

## control b10_unknown_actor

```text
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b10_unknown_actor" --test-cmd "rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'" --expect "test_unknown_actor_is_rejected_first_everywhere" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-sy1h79ju/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b10_unknown_actor
break applied: b10_unknown_actor
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect FAILURE matching /test_unknown_actor_is_rejected_first_everywhere/
..FE..................................................................F...........................................F
======================================================================
ERROR: test_failed_advance_changes_nothing (test_atomicity.AtomicityTest.test_failed_advance_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_atomicity.py", line 132, in test_failed_advance_changes_nothing
    self.assert_atomic(
    ~~~~~~~~~~~~~~~~~~^
        lambda: self.crm.advance(self.opp_id, "proposal", "ghost"), PermissionError
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_atomicity.py", line 44, in assert_atomic
    call()
    ~~~~^^
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_atomicity.py", line 133, in <lambda>
    lambda: self.crm.advance(self.opp_id, "proposal", "ghost"), PermissionError
            ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-3/crm.py", line 196, in advance
    if not self._may_manage(opp, actor):
           ~~~~~~~~~~~~~~~~^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-3/crm.py", line 74, in _may_manage
    return actor == opp["owner"] or self._is_manager(actor)
                                    ~~~~~~~~~~~~~~~~^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-3/crm.py", line 71, in _is_manager
    return self.users[actor]["role"] == "manager"
           ~~~~~~~~~~^^^^^^^
KeyError: 'ghost'

======================================================================
FAIL: test_failed_add_lead_with_unknown_actor_changes_nothing (test_atomicity.AtomicityTest.test_failed_add_lead_with_unknown_actor_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_atomicity.py", line 70, in test_failed_add_lead_with_unknown_actor_changes_nothing
    self.assert_atomic(
    ~~~~~~~~~~~~~~~~~~^
        lambda: self.crm.add_lead("x@corp.io", "X", "web", "ghost"), PermissionError
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_atomicity.py", line 43, in assert_atomic
    with self.assertRaises(exc):
         ~~~~~~~~~~~~~~~~~^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_unknown_actor_is_rejected_first_everywhere (test_pipeline.PermissionTest.test_unknown_actor_is_rejected_first_everywhere)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_pipeline.py", line 156, in test_unknown_actor_is_rejected_first_everywhere
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_unhashable_actor_rejected_by_every_method (test_validation.UnhashableActorTest.test_unhashable_actor_rejected_by_every_method)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_validation.py", line 203, in test_unhashable_actor_rejected_by_every_method
    self.assert_permission_error_and_no_change(
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^
        lambda bad=bad: self.crm.add_lead("x@corp.io", "X", "web", bad)
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_validation.py", line 189, in assert_permission_error_and_no_change
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

----------------------------------------------------------------------
Ran 115 tests in 0.004s

FAILED (failures=3, errors=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-3/crm.py from backup (byte-identical)
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect SUCCESS
...................................................................................................................
----------------------------------------------------------------------
Ran 115 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
[exit 0]
```

## control b11_score_threshold

```text
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b11_score_threshold" --test-cmd "rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'" --expect "test_web_free_domain_lead_below_threshold" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-gfhe30nn/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b11_score_threshold
break applied: b11_score_threshold
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect FAILURE matching /test_web_free_domain_lead_below_threshold/
............F..............................................................FF......................................
======================================================================
FAIL: test_failed_qualify_changes_nothing (test_atomicity.AtomicityTest.test_failed_qualify_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_atomicity.py", line 78, in test_failed_qualify_changes_nothing
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_web_corporate_lead_below_threshold (test_pipeline.QualifyTest.test_web_corporate_lead_below_threshold)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_pipeline.py", line 238, in test_web_corporate_lead_below_threshold
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_web_free_domain_lead_below_threshold (test_pipeline.QualifyTest.test_web_free_domain_lead_below_threshold)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_pipeline.py", line 231, in test_web_free_domain_lead_below_threshold
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 115 tests in 0.004s

FAILED (failures=3)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-3/crm.py from backup (byte-identical)
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect SUCCESS
...................................................................................................................
----------------------------------------------------------------------
Ran 115 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
[exit 0]
```

## control b12_stage_transition_order

```text
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b12_stage_transition_order" --test-cmd "rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'" --expect "test_skipping_a_stage_is_rejected" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-1cjcvqio/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b12_stage_transition_order
break applied: b12_stage_transition_order
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect FAILURE matching /test_skipping_a_stage_is_rejected/
...F...............F.....FF........................................................................................
======================================================================
FAIL: test_failed_advance_changes_nothing (test_atomicity.AtomicityTest.test_failed_advance_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_atomicity.py", line 123, in test_failed_advance_changes_nothing
    self.assert_atomic(
    ~~~~~~~~~~~~~~~~~~^
        lambda: self.crm.advance(self.opp_id, "won", "rep1"), ValueError
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_atomicity.py", line 43, in assert_atomic
    with self.assertRaises(exc):
         ~~~~~~~~~~~~~~~~~^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_going_backwards_is_rejected (test_pipeline.AdvanceTest.test_going_backwards_is_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_pipeline.py", line 352, in test_going_backwards_is_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_same_stage_is_rejected (test_pipeline.AdvanceTest.test_same_stage_is_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_pipeline.py", line 356, in test_same_stage_is_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_skipping_a_stage_is_rejected (test_pipeline.AdvanceTest.test_skipping_a_stage_is_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_pipeline.py", line 345, in test_skipping_a_stage_is_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 115 tests in 0.004s

FAILED (failures=4)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-3/crm.py from backup (byte-identical)
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect SUCCESS
...................................................................................................................
----------------------------------------------------------------------
Ran 115 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
[exit 0]
```

## control b13_stage_final_guard

```text
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b13_stage_final_guard" --test-cmd "rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'" --expect "test_final_stages_are_terminal" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-jm6ds4v6/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b13_stage_final_guard
break applied: b13_stage_final_guard
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect FAILURE matching /test_final_stages_are_terminal/
.................F.................................................................................................
======================================================================
FAIL: test_final_stages_are_terminal (test_pipeline.AdvanceTest.test_final_stages_are_terminal)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_pipeline.py", line 381, in test_final_stages_are_terminal
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 115 tests in 0.004s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-3/crm.py from backup (byte-identical)
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect SUCCESS
...................................................................................................................
----------------------------------------------------------------------
Ran 115 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
[exit 0]
```

## control b14_big_deal_manager

```text
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b14_big_deal_manager" --test-cmd "rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'" --expect "test_rep_cannot_take_big_deal_to_negotiation" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-l9pk77t0/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b14_big_deal_manager
break applied: b14_big_deal_manager
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect FAILURE matching /test_rep_cannot_take_big_deal_to_negotiation/
.....F................................F............................................................................
======================================================================
FAIL: test_failed_big_deal_advance_changes_nothing (test_atomicity.AtomicityTest.test_failed_big_deal_advance_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_atomicity.py", line 143, in test_failed_big_deal_advance_changes_nothing
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_rep_cannot_take_big_deal_to_negotiation (test_pipeline.BigDealApprovalTest.test_rep_cannot_take_big_deal_to_negotiation)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_pipeline.py", line 407, in test_rep_cannot_take_big_deal_to_negotiation
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

----------------------------------------------------------------------
Ran 115 tests in 0.004s

FAILED (failures=2)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-3/crm.py from backup (byte-identical)
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect SUCCESS
...................................................................................................................
----------------------------------------------------------------------
Ran 115 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
[exit 0]
```

## control b15_discount_pct_range

```text
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b15_discount_pct_range" --test-cmd "rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'" --expect "test_invalid_percentages_rejected" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-8hhaska5/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b15_discount_pct_range
break applied: b15_discount_pct_range
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect FAILURE matching /test_invalid_percentages_rejected/
..........F.......................................F...........E....................................................
======================================================================
ERROR: test_argument_validity_is_checked_before_permission (test_pipeline.PermissionTest.test_argument_validity_is_checked_before_permission)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_pipeline.py", line 210, in test_argument_validity_is_checked_before_permission
    self.crm.discount(self.opp_id, 99, "rep2")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-3/crm.py", line 229, in discount
    raise PermissionError("actor may not discount this opportunity")
PermissionError: actor may not discount this opportunity

======================================================================
FAIL: test_failed_discount_changes_nothing (test_atomicity.AtomicityTest.test_failed_discount_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_atomicity.py", line 162, in test_failed_discount_changes_nothing
    self.assert_atomic(
    ~~~~~~~~~~~~~~~~~~^
        lambda: self.crm.discount(self.opp_id, 0, "rep1"), ValueError
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_atomicity.py", line 43, in assert_atomic
    with self.assertRaises(exc):
         ~~~~~~~~~~~~~~~~~^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_invalid_percentages_rejected (test_pipeline.DiscountTest.test_invalid_percentages_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_pipeline.py", line 434, in test_invalid_percentages_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 115 tests in 0.004s

FAILED (failures=2, errors=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-3/crm.py from backup (byte-identical)
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect SUCCESS
...................................................................................................................
----------------------------------------------------------------------
Ran 115 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
[exit 0]
```

## control b16_discount_rep_limit

```text
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b16_discount_rep_limit" --test-cmd "rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'" --expect "test_rep_limit_is_ten" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-nsjizhoy/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b16_discount_rep_limit
break applied: b16_discount_rep_limit
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect FAILURE matching /test_rep_limit_is_ten/
..........F..........................................F.............................................................
======================================================================
FAIL: test_failed_discount_changes_nothing (test_atomicity.AtomicityTest.test_failed_discount_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_atomicity.py", line 159, in test_failed_discount_changes_nothing
    self.assert_atomic(
    ~~~~~~~~~~~~~~~~~~^
        lambda: self.crm.discount(self.opp_id, 11, "rep1"), PermissionError
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_atomicity.py", line 43, in assert_atomic
    with self.assertRaises(exc):
         ~~~~~~~~~~~~~~~~~^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_rep_limit_is_ten (test_pipeline.DiscountTest.test_rep_limit_is_ten)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_pipeline.py", line 444, in test_rep_limit_is_ten
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

----------------------------------------------------------------------
Ran 115 tests in 0.004s

FAILED (failures=2)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-3/crm.py from backup (byte-identical)
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect SUCCESS
...................................................................................................................
----------------------------------------------------------------------
Ran 115 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
[exit 0]
```

## control b17_discount_cumulative_floor

```text
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b17_discount_cumulative_floor" --test-cmd "rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'" --expect "test_cumulative_floor_is_enforced" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-0id4zuv4/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b17_discount_cumulative_floor
break applied: b17_discount_cumulative_floor
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect FAILURE matching /test_cumulative_floor_is_enforced/
.........F....................................F..F....FF...........................................................
======================================================================
FAIL: test_failed_cumulative_discount_changes_nothing (test_atomicity.AtomicityTest.test_failed_cumulative_discount_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_atomicity.py", line 174, in test_failed_cumulative_discount_changes_nothing
    self.assert_atomic(
    ~~~~~~~~~~~~~~~~~~^
        lambda: self.crm.discount(self.opp_id, 1, "boss"), ValueError
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_atomicity.py", line 43, in assert_atomic
    with self.assertRaises(exc):
         ~~~~~~~~~~~~~~~~~^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_cumulative_floor_is_enforced (test_pipeline.DiscountTest.test_cumulative_floor_is_enforced)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_pipeline.py", line 461, in test_cumulative_floor_is_enforced
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_floor_uses_original_amount_and_integer_truncation (test_pipeline.DiscountTest.test_floor_uses_original_amount_and_integer_truncation)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_pipeline.py", line 468, in test_floor_uses_original_amount_and_integer_truncation
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_repeated_rep_discounts_stop_at_the_floor (test_pipeline.DiscountTest.test_repeated_rep_discounts_stop_at_the_floor)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_pipeline.py", line 488, in test_repeated_rep_discounts_stop_at_the_floor
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_two_steps_can_reach_exactly_the_floor (test_pipeline.DiscountTest.test_two_steps_can_reach_exactly_the_floor)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_pipeline.py", line 478, in test_two_steps_can_reach_exactly_the_floor
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 115 tests in 0.004s

FAILED (failures=5)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-3/crm.py from backup (byte-identical)
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect SUCCESS
...................................................................................................................
----------------------------------------------------------------------
Ran 115 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
[exit 0]
```

## control b18_transfer_rep_role

```text
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b18_transfer_rep_role" --test-cmd "rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'" --expect "test_new_owner_must_be_a_known_rep" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-xx9u3zwc/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b18_transfer_rep_role
break applied: b18_transfer_rep_role
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect FAILURE matching /test_new_owner_must_be_a_known_rep/
...............................................................................F...................................
======================================================================
FAIL: test_new_owner_must_be_a_known_rep (test_pipeline.TransferTest.test_new_owner_must_be_a_known_rep)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_pipeline.py", line 517, in test_new_owner_must_be_a_known_rep
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 115 tests in 0.004s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-3/crm.py from backup (byte-identical)
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect SUCCESS
...................................................................................................................
----------------------------------------------------------------------
Ran 115 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
[exit 0]
```

## control b19_transfer_capacity

```text
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b19_transfer_capacity" --test-cmd "rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'" --expect "test_full_target_rejected" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-1wcqsurr/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b19_transfer_capacity
break applied: b19_transfer_capacity
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect FAILURE matching /test_full_target_rejected/
..............F...............................................................F....F...............................
======================================================================
FAIL: test_failed_transfer_changes_nothing (test_atomicity.AtomicityTest.test_failed_transfer_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_atomicity.py", line 200, in test_failed_transfer_changes_nothing
    self.assert_atomic(
    ~~~~~~~~~~~~~~~~~~^
        lambda: self.crm.transfer(self.opp_id, "rep2", "boss"), ValueError
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_atomicity.py", line 43, in assert_atomic
    with self.assertRaises(exc):
         ~~~~~~~~~~~~~~~~~^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_full_target_rejected (test_pipeline.TransferTest.test_full_target_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_pipeline.py", line 543, in test_full_target_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_transfer_counts_open_opportunities_against_capacity (test_pipeline.TransferTest.test_transfer_counts_open_opportunities_against_capacity)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_pipeline.py", line 558, in test_transfer_counts_open_opportunities_against_capacity
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 115 tests in 0.004s

FAILED (failures=3)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-3/crm.py from backup (byte-identical)
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect SUCCESS
...................................................................................................................
----------------------------------------------------------------------
Ran 115 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
[exit 0]
```

## control b20_transfer_same_owner

```text
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b20_transfer_same_owner" --test-cmd "rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'" --expect "test_same_owner_rejected" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-50tc6d_w/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b20_transfer_same_owner
break applied: b20_transfer_same_owner
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect FAILURE matching /test_same_owner_rejected/
.................................................................................F.................................
======================================================================
FAIL: test_same_owner_rejected (test_pipeline.TransferTest.test_same_owner_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_pipeline.py", line 529, in test_same_owner_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 115 tests in 0.004s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-3/crm.py from backup (byte-identical)
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect SUCCESS
...................................................................................................................
----------------------------------------------------------------------
Ran 115 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
[exit 0]
```

## control b21_atomicity_discount

```text
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b21_atomicity_discount" --test-cmd "rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'" --expect "test_failed_cumulative_discount_changes_nothing" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-yzsm6j03/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b21_atomicity_discount
break applied: b21_atomicity_discount
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect FAILURE matching /test_failed_cumulative_discount_changes_nothing/
.........F....................................F..F....FF...........................................................
======================================================================
FAIL: test_failed_cumulative_discount_changes_nothing (test_atomicity.AtomicityTest.test_failed_cumulative_discount_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_atomicity.py", line 174, in test_failed_cumulative_discount_changes_nothing
    self.assert_atomic(
    ~~~~~~~~~~~~~~~~~~^
        lambda: self.crm.discount(self.opp_id, 1, "boss"), ValueError
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_atomicity.py", line 45, in assert_atomic
    self.assertEqual(snapshot(self.crm), before)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: {'lea[332 chars]nt': 693, 'original_amount': 1000, 'stage': 'p[229 chars]': 1} != {'lea[332 chars]nt': 700, 'original_amount': 1000, 'stage': 'p[201 chars]': 1}
Diff is 1140 characters long. Set self.maxDiff to None to see it.

======================================================================
FAIL: test_cumulative_floor_is_enforced (test_pipeline.DiscountTest.test_cumulative_floor_is_enforced)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_pipeline.py", line 463, in test_cumulative_floor_is_enforced
    self.assertEqual(self.crm.opps[self.opp_id]["amount"], 700)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 693 != 700

======================================================================
FAIL: test_floor_uses_original_amount_and_integer_truncation (test_pipeline.DiscountTest.test_floor_uses_original_amount_and_integer_truncation)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_pipeline.py", line 470, in test_floor_uses_original_amount_and_integer_truncation
    self.assertEqual(crm.opps[opp_id]["amount"], 999)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 699 != 999

======================================================================
FAIL: test_repeated_rep_discounts_stop_at_the_floor (test_pipeline.DiscountTest.test_repeated_rep_discounts_stop_at_the_floor)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_pipeline.py", line 490, in test_repeated_rep_discounts_stop_at_the_floor
    self.assertEqual(self.crm.opps[self.opp_id]["amount"], 729)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 656 != 729

======================================================================
FAIL: test_two_steps_can_reach_exactly_the_floor (test_pipeline.DiscountTest.test_two_steps_can_reach_exactly_the_floor)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_pipeline.py", line 480, in test_two_steps_can_reach_exactly_the_floor
    self.assertEqual(crm.opps[opp_id]["amount"], 704)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 696 != 704

----------------------------------------------------------------------
Ran 115 tests in 0.005s

FAILED (failures=5)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-3/crm.py from backup (byte-identical)
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect SUCCESS
...................................................................................................................
----------------------------------------------------------------------
Ran 115 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
[exit 0]
```

## control b22_atomicity_qualify

```text
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b22_atomicity_qualify" --test-cmd "rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'" --expect "test_failed_qualify_changes_nothing" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-qrmpcszq/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b22_atomicity_qualify
break applied: b22_atomicity_qualify
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect FAILURE matching /test_failed_qualify_changes_nothing/
............F...............................................................F......................................
======================================================================
FAIL: test_failed_qualify_changes_nothing (test_atomicity.AtomicityTest.test_failed_qualify_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_atomicity.py", line 80, in test_failed_qualify_changes_nothing
    self.assertEqual(snapshot(crm), before)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: {'lea[117 chars]s': 'qualified'}}, 'opps': {}, 'log': [('add_l[60 chars]': 0} != {'lea[117 chars]s': 'new'}}, 'opps': {}, 'log': [('add_lead', [54 chars]': 0}
  {'lead_seq': 1,
   'leads': {'L1': {'email': 'low@gmail.com',
                    'id': 'L1',
                    'name': 'L',
                    'owner': 'rep1',
                    'score': 10,
                    'source': 'web',
-                   'status': 'qualified'}},
?                              ^^^^^^^ ^

+                   'status': 'new'}},
?                              ^ ^

   'log': [('add_lead', 'L1', 'rep1')],
   'opp_seq': 0,
   'opps': {},
   'waiting': []}

======================================================================
FAIL: test_web_free_domain_lead_below_threshold (test_pipeline.QualifyTest.test_web_free_domain_lead_below_threshold)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_pipeline.py", line 233, in test_web_free_domain_lead_below_threshold
    self.assertEqual(crm.leads[lead_id]["status"], "new")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'qualified' != 'new'
- qualified
+ new


----------------------------------------------------------------------
Ran 115 tests in 0.004s

FAILED (failures=2)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-3/crm.py from backup (byte-identical)
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect SUCCESS
...................................................................................................................
----------------------------------------------------------------------
Ran 115 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
[exit 0]
```

## control b23_permission_qualify_actor

```text
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b23_permission_qualify_actor" --test-cmd "rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'" --expect "test_other_rep_cannot_qualify" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-9gp114mr/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b23_permission_qualify_actor
break applied: b23_permission_qualify_actor
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect FAILURE matching /test_other_rep_cannot_qualify/
............E.......................................................F..F...........................................
======================================================================
ERROR: test_failed_qualify_changes_nothing (test_atomicity.AtomicityTest.test_failed_qualify_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_atomicity.py", line 85, in test_failed_qualify_changes_nothing
    crm.qualify(lead_id, "rep2")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-3/crm.py", line 158, in qualify
    raise ValueError("lead score %d is below the qualification threshold" % lead["score"])
ValueError: lead score 10 is below the qualification threshold

======================================================================
FAIL: test_other_rep_cannot_qualify (test_pipeline.PermissionTest.test_other_rep_cannot_qualify)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_pipeline.py", line 171, in test_other_rep_cannot_qualify
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_unowned_lead_cannot_be_qualified_by_a_rep (test_pipeline.PermissionTest.test_unowned_lead_cannot_be_qualified_by_a_rep)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_pipeline.py", line 221, in test_unowned_lead_cannot_be_qualified_by_a_rep
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

----------------------------------------------------------------------
Ran 115 tests in 0.004s

FAILED (failures=2, errors=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-3/crm.py from backup (byte-identical)
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect SUCCESS
...................................................................................................................
----------------------------------------------------------------------
Ran 115 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
[exit 0]
```

## control b24_permission_convert_actor

```text
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b24_permission_convert_actor" --test-cmd "rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'" --expect "test_other_rep_cannot_convert" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-0t1l1i2k/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b24_permission_convert_actor
break applied: b24_permission_convert_actor
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect FAILURE matching /test_other_rep_cannot_convert/
..................................................................F................................................
======================================================================
FAIL: test_other_rep_cannot_convert (test_pipeline.PermissionTest.test_other_rep_cannot_convert)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_pipeline.py", line 176, in test_other_rep_cannot_convert
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

----------------------------------------------------------------------
Ran 115 tests in 0.004s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-3/crm.py from backup (byte-identical)
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect SUCCESS
...................................................................................................................
----------------------------------------------------------------------
Ran 115 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
[exit 0]
```

## control b25_transfer_manager_only

```text
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b25_transfer_manager_only" --test-cmd "rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'" --expect "test_only_manager_may_transfer" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-jmc6o4qw/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b25_transfer_manager_only
break applied: b25_transfer_manager_only
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect FAILURE matching /test_only_manager_may_transfer/
..............E......................................................E..........F..................................
======================================================================
ERROR: test_failed_transfer_changes_nothing (test_atomicity.AtomicityTest.test_failed_transfer_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_atomicity.py", line 191, in test_failed_transfer_changes_nothing
    self.assert_atomic(
    ~~~~~~~~~~~~~~~~~~^
        lambda: self.crm.transfer(self.opp_id, "rep2", "rep1"), PermissionError
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_atomicity.py", line 44, in assert_atomic
    call()
    ~~~~^^
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_atomicity.py", line 192, in <lambda>
    lambda: self.crm.transfer(self.opp_id, "rep2", "rep1"), PermissionError
            ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-3/crm.py", line 258, in transfer
    raise ValueError("new owner is at capacity")
ValueError: new owner is at capacity

======================================================================
ERROR: test_transfer_requires_manager_before_owner_validation (test_pipeline.PermissionTest.test_transfer_requires_manager_before_owner_validation)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_pipeline.py", line 216, in test_transfer_requires_manager_before_owner_validation
    self.crm.transfer(self.opp_id, "ghost", "rep1")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-3/crm.py", line 252, in transfer
    raise ValueError("new owner must be a rep: %r" % (new_owner,))
ValueError: new owner must be a rep: 'ghost'

======================================================================
FAIL: test_only_manager_may_transfer (test_pipeline.TransferTest.test_only_manager_may_transfer)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_pipeline.py", line 510, in test_only_manager_may_transfer
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

----------------------------------------------------------------------
Ran 115 tests in 0.004s

FAILED (failures=1, errors=2)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-3/crm.py from backup (byte-identical)
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect SUCCESS
...................................................................................................................
----------------------------------------------------------------------
Ran 115 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
[exit 0]
```

## control b26_advance_valid_stage_name

```text
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b26_advance_valid_stage_name" --test-cmd "rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'" --expect "test_invalid_stage_names_are_rejected_before_the_permission_check" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-njz_cty_/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b26_advance_valid_stage_name
break applied: b26_advance_valid_stage_name
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect FAILURE matching /test_invalid_stage_names_are_rejected_before_the_permission_check/
....................E.........................................E....................................................
======================================================================
ERROR: test_invalid_stage_names_are_rejected_before_the_permission_check (test_pipeline.AdvanceTest.test_invalid_stage_names_are_rejected_before_the_permission_check)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_pipeline.py", line 336, in test_invalid_stage_names_are_rejected_before_the_permission_check
    self.crm.advance(self.opp_id, bad, "rep2")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-3/crm.py", line 199, in advance
    raise PermissionError("actor may not advance this opportunity")
PermissionError: actor may not advance this opportunity

======================================================================
ERROR: test_argument_validity_is_checked_before_permission (test_pipeline.PermissionTest.test_argument_validity_is_checked_before_permission)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_pipeline.py", line 208, in test_argument_validity_is_checked_before_permission
    self.crm.advance(self.opp_id, "closed", "rep2")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-3/crm.py", line 199, in advance
    raise PermissionError("actor may not advance this opportunity")
PermissionError: actor may not advance this opportunity

----------------------------------------------------------------------
Ran 115 tests in 0.004s

FAILED (errors=2)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-3/crm.py from backup (byte-identical)
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect SUCCESS
...................................................................................................................
----------------------------------------------------------------------
Ran 115 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
[exit 0]
```

## control b27_forecast_weights

```text
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b27_forecast_weights" --test-cmd "rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'" --expect "test_weights_and_won_sum" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-9c1bx949/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b27_forecast_weights
break applied: b27_forecast_weights
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect FAILURE matching /test_weights_and_won_sum/
...........................................................F.F.....................................................
======================================================================
FAIL: test_forecast_truncates_each_opportunity (test_pipeline.ForecastTest.test_forecast_truncates_each_opportunity)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_pipeline.py", line 611, in test_forecast_truncates_each_opportunity
    self.assertEqual(
    ~~~~~~~~~~~~~~~~^
        crm.forecast(), {"open": 3, "weighted": 99 + 99 + 600, "won": 0}
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
AssertionError: {'open': 3, 'weighted': 465, 'won': 0} != {'open': 3, 'weighted': 798, 'won': 0}
- {'open': 3, 'weighted': 465, 'won': 0}
?                         ^^^

+ {'open': 3, 'weighted': 798, 'won': 0}
?                         ^^^


======================================================================
FAIL: test_weights_and_won_sum (test_pipeline.ForecastTest.test_weights_and_won_sum)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_pipeline.py", line 591, in test_weights_and_won_sum
    self.assertEqual(crm.forecast(), {"open": 3, "weighted": 2500, "won": 5000})
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: {'open': 3, 'weighted': 1400, 'won': 5000} != {'open': 3, 'weighted': 2500, 'won': 5000}
- {'open': 3, 'weighted': 1400, 'won': 5000}
?                         ^^

+ {'open': 3, 'weighted': 2500, 'won': 5000}
?                         ^^


----------------------------------------------------------------------
Ran 115 tests in 0.004s

FAILED (failures=2)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-3/crm.py from backup (byte-identical)
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect SUCCESS
...................................................................................................................
----------------------------------------------------------------------
Ran 115 tests in 0.004s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
[exit 0]
```

## control b28_transfer_final_stage

```text
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b28_transfer_final_stage" --test-cmd "rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'" --expect "test_final_stage_rejected" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-xa5ua01_/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b28_transfer_final_stage
break applied: b28_transfer_final_stage
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect FAILURE matching /test_final_stage_rejected/
...............F.............................................................F.....................................
======================================================================
FAIL: test_failed_transfer_on_final_stage_changes_nothing (test_atomicity.AtomicityTest.test_failed_transfer_on_final_stage_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_atomicity.py", line 214, in test_failed_transfer_on_final_stage_changes_nothing
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_final_stage_rejected (test_pipeline.TransferTest.test_final_stage_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_pipeline.py", line 535, in test_final_stage_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 115 tests in 0.004s

FAILED (failures=2)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-3/crm.py from backup (byte-identical)
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect SUCCESS
...................................................................................................................
----------------------------------------------------------------------
Ran 115 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
[exit 0]
```

## control b29_discount_final_stage

```text
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b29_discount_final_stage" --test-cmd "rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'" --expect "test_discount_on_final_stage_rejected" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-4_9z6lr2/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b29_discount_final_stage
break applied: b29_discount_final_stage
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect FAILURE matching /test_discount_on_final_stage_rejected/
...........F....................................F..................................................................
======================================================================
FAIL: test_failed_discount_on_final_stage_changes_nothing (test_atomicity.AtomicityTest.test_failed_discount_on_final_stage_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_atomicity.py", line 186, in test_failed_discount_on_final_stage_changes_nothing
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_discount_on_final_stage_rejected (test_pipeline.DiscountTest.test_discount_on_final_stage_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_pipeline.py", line 455, in test_discount_on_final_stage_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 115 tests in 0.004s

FAILED (failures=2)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-3/crm.py from backup (byte-identical)
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect SUCCESS
...................................................................................................................
----------------------------------------------------------------------
Ran 115 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
[exit 0]
```

## control b30_convert_bool_amount

```text
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b30_convert_bool_amount" --test-cmd "rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'" --expect "test_bad_amounts_are_rejected" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-_d8vm8lj/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b30_convert_bool_amount
break applied: b30_convert_bool_amount
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect FAILURE matching /test_bad_amounts_are_rejected/
.......................................F...........................................................................
======================================================================
FAIL: test_bad_amounts_are_rejected (test_pipeline.ConvertTest.test_bad_amounts_are_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_pipeline.py", line 271, in test_bad_amounts_are_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 115 tests in 0.004s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-3/crm.py from backup (byte-identical)
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect SUCCESS
...................................................................................................................
----------------------------------------------------------------------
Ran 115 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
[exit 0]
```

## control b31_qualify_status_new

```text
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b31_qualify_status_new" --test-cmd "rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'" --expect "test_cannot_qualify_twice" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-84wy_9f8/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b31_qualify_status_new
break applied: b31_qualify_status_new
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect FAILURE matching /test_cannot_qualify_twice/
.............F..........................................................FF.........................................
======================================================================
FAIL: test_failed_qualify_on_wrong_status_changes_nothing (test_atomicity.AtomicityTest.test_failed_qualify_on_wrong_status_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_atomicity.py", line 89, in test_failed_qualify_on_wrong_status_changes_nothing
    self.assert_atomic(
    ~~~~~~~~~~~~~~~~~~^
        lambda: self.crm.qualify(self.lead_id, "boss"), ValueError
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_atomicity.py", line 43, in assert_atomic
    with self.assertRaises(exc):
         ~~~~~~~~~~~~~~~~~^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_cannot_qualify_converted_lead (test_pipeline.QualifyTest.test_cannot_qualify_converted_lead)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_pipeline.py", line 259, in test_cannot_qualify_converted_lead
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_cannot_qualify_twice (test_pipeline.QualifyTest.test_cannot_qualify_twice)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_pipeline.py", line 252, in test_cannot_qualify_twice
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 115 tests in 0.004s

FAILED (failures=3)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-3/crm.py from backup (byte-identical)
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect SUCCESS
...................................................................................................................
----------------------------------------------------------------------
Ran 115 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
[exit 0]
```

## control b32_score_domain_bonus

```text
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b32_score_domain_bonus" --test-cmd "rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'" --expect "test_source_scores_include_domain_bonus" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-lvucwlgd/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b32_score_domain_bonus
break applied: b32_score_domain_bonus
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect FAILURE matching /test_source_scores_include_domain_bonus/
...........................................................................................F..........F.......F.F..
======================================================================
FAIL: test_lead_fields_and_log (test_validation.AddLeadShapeTest.test_lead_fields_and_log)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_validation.py", line 227, in test_lead_fields_and_log
    self.assertEqual(
    ~~~~~~~~~~~~~~~~^
        self.crm.leads[lead_id],
        ^^^^^^^^^^^^^^^^^^^^^^^^
    ...<8 lines>...
        },
        ^^
    )
    ^
AssertionError: {'id'[52 chars]ce': 'referral', 'score': 30, 'owner': 'rep1', 'status': 'new'} != {'id'[52 chars]ce': 'referral', 'score': 45, 'owner': 'rep1', 'status': 'new'}
  {'email': 'ana@corp.io',
   'id': 'L1',
   'name': 'Ana',
   'owner': 'rep1',
-  'score': 30,
?           ^^

+  'score': 45,
?           ^^

   'source': 'referral',
   'status': 'new'}

======================================================================
FAIL: test_interior_dot_is_what_the_spec_requires (test_validation.EmailValidationTest.test_interior_dot_is_what_the_spec_requires)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_validation.py", line 67, in test_interior_dot_is_what_the_spec_requires
    self.assertEqual(self.crm.leads[lead_id]["score"], 25)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 10 != 25

======================================================================
FAIL: test_free_domains_are_exact_after_normalization (test_validation.SourceValidationTest.test_free_domains_are_exact_after_normalization)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_validation.py", line 119, in test_free_domains_are_exact_after_normalization
    self.assertEqual(crm.leads[other]["score"], 25)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 10 != 25

======================================================================
FAIL: test_source_scores_include_domain_bonus (test_validation.SourceValidationTest.test_source_scores_include_domain_bonus)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_validation.py", line 112, in test_source_scores_include_domain_bonus
    self.assertEqual(crm.leads[lead_id]["score"], score)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 10 != 25

----------------------------------------------------------------------
Ran 115 tests in 0.004s

FAILED (failures=4)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-3/crm.py from backup (byte-identical)
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect SUCCESS
...................................................................................................................
----------------------------------------------------------------------
Ran 115 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
[exit 0]
```

## control b33_load_status_filter

```text
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b33_load_status_filter" --test-cmd "rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'" --expect "test_converted_lead_no_longer_counts_toward_load" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-baz_2gnc/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b33_load_status_filter
break applied: b33_load_status_filter
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect FAILURE matching /test_converted_lead_no_longer_counts_toward_load/
................F...........F.....................................................F...F.EF.........................
======================================================================
ERROR: test_queue_is_fifo (test_pipeline.WaitingQueueTest.test_queue_is_fifo)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_pipeline.py", line 120, in test_queue_is_fifo
    crm.qualify(second, "rep1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-3/crm.py", line 155, in qualify
    raise PermissionError("actor may not qualify this lead")
PermissionError: actor may not qualify this lead

======================================================================
FAIL: test_successful_calls_only_append_the_named_entries (test_atomicity.AtomicityTest.test_successful_calls_only_append_the_named_entries)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_atomicity.py", line 224, in test_successful_calls_only_append_the_named_entries
    self.assertEqual(self.crm.log[-2], ("advance", self.opp_id, "rep1"))
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Tuples differ: ('add_lead', 'L2', 'rep1') != ('advance', 'O1', 'rep1')

First differing element 0:
'add_lead'
'advance'

- ('add_lead', 'L2', 'rep1')
+ ('advance', 'O1', 'rep1')

======================================================================
FAIL: test_converted_lead_no_longer_counts_toward_load (test_pipeline.AssignmentTest.test_converted_lead_no_longer_counts_toward_load)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_pipeline.py", line 100, in test_converted_lead_no_longer_counts_toward_load
    self.assertEqual(crm.leads[replacement]["owner"], "rep1")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'rep2' != 'rep1'
- rep2
?    ^
+ rep1
?    ^


======================================================================
FAIL: test_target_at_capacity_minus_one_is_accepted (test_pipeline.TransferTest.test_target_at_capacity_minus_one_is_accepted)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_pipeline.py", line 570, in test_target_at_capacity_minus_one_is_accepted
    self.assertEqual(crm._load("rep2"), 1)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 2 != 1

======================================================================
FAIL: test_lost_stage_frees_the_slot_too (test_pipeline.WaitingQueueTest.test_lost_stage_frees_the_slot_too)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_pipeline.py", line 144, in test_lost_stage_frees_the_slot_too
    self.assertEqual(crm.leads[waiting_id]["owner"], "rep1")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: None != 'rep1'

======================================================================
FAIL: test_win_assigns_oldest_waiting_lead_and_logs_system (test_pipeline.WaitingQueueTest.test_win_assigns_oldest_waiting_lead_and_logs_system)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_pipeline.py", line 111, in test_win_assigns_oldest_waiting_lead_and_logs_system
    self.assertEqual(crm.leads[waiting_id]["owner"], "rep1")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: None != 'rep1'

----------------------------------------------------------------------
Ran 115 tests in 0.005s

FAILED (failures=5, errors=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-3/crm.py from backup (byte-identical)
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect SUCCESS
...................................................................................................................
----------------------------------------------------------------------
Ran 115 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
[exit 0]
```

## control b34_atomicity_advance

```text
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b34_atomicity_advance" --test-cmd "rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'" --expect "test_failed_big_deal_advance_changes_nothing" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-erfxugh0/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b34_atomicity_advance
break applied: b34_atomicity_advance
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect FAILURE matching /test_failed_big_deal_advance_changes_nothing/
.....F................................F............................................................................
======================================================================
FAIL: test_failed_big_deal_advance_changes_nothing (test_atomicity.AtomicityTest.test_failed_big_deal_advance_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_atomicity.py", line 145, in test_failed_big_deal_advance_changes_nothing
    self.assertEqual(snapshot(crm), before)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: {'lea[249 chars]e': 'negotiation'}}, 'log': [('add_lead', 'L1'[158 chars]': 1} != {'lea[249 chars]e': 'proposal'}}, 'log': [('add_lead', 'L1', '[128 chars]': 1}
Diff is 863 characters long. Set self.maxDiff to None to see it.

======================================================================
FAIL: test_rep_cannot_take_big_deal_to_negotiation (test_pipeline.BigDealApprovalTest.test_rep_cannot_take_big_deal_to_negotiation)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_pipeline.py", line 409, in test_rep_cannot_take_big_deal_to_negotiation
    self.assertEqual(crm.opps[opp_id]["stage"], "proposal")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'negotiation' != 'proposal'
- negotiation
+ proposal


----------------------------------------------------------------------
Ran 115 tests in 0.004s

FAILED (failures=2)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-3/crm.py from backup (byte-identical)
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect SUCCESS
...................................................................................................................
----------------------------------------------------------------------
Ran 115 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
[exit 0]
```

## control b35_atomicity_convert

```text
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b35_atomicity_convert" --test-cmd "rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'" --expect "test_failed_convert_on_unowned_lead_changes_nothing" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-2uht_fyo/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b35_atomicity_convert
break applied: b35_atomicity_convert
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect FAILURE matching /test_failed_convert_on_unowned_lead_changes_nothing/
........F..........................................................................................................
======================================================================
FAIL: test_failed_convert_on_unowned_lead_changes_nothing (test_atomicity.AtomicityTest.test_failed_convert_on_unowned_lead_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_atomicity.py", line 119, in test_failed_convert_on_unowned_lead_changes_nothing
    self.assertEqual(snapshot(crm), before)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: {'lea[116 chars]s': 'converted'}}, 'opps': {}, 'log': [('add_l[91 chars]': 1} != {'lea[116 chars]s': 'qualified'}}, 'opps': {}, 'log': [('add_l[91 chars]': 0}
  {'lead_seq': 1,
   'leads': {'L1': {'email': 'a@corp.io',
                    'id': 'L1',
                    'name': 'A',
                    'owner': None,
                    'score': 45,
                    'source': 'referral',
-                   'status': 'converted'}},
?                              ^^^^^^^

+                   'status': 'qualified'}},
?                              ^^^^^^^

   'log': [('add_lead', 'L1', 'boss'), ('qualify', 'L1', 'boss')],
-  'opp_seq': 1,
?             ^

+  'opp_seq': 0,
?             ^

   'opps': {},
   'waiting': ['L1']}

----------------------------------------------------------------------
Ran 115 tests in 0.004s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-3/crm.py from backup (byte-identical)
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect SUCCESS
...................................................................................................................
----------------------------------------------------------------------
Ran 115 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
[exit 0]
```

## control b36_atomicity_transfer

```text
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b36_atomicity_transfer" --test-cmd "rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'" --expect "test_failed_transfer_changes_nothing" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-m47eibdd/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b36_atomicity_transfer
break applied: b36_atomicity_transfer
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect FAILURE matching /test_failed_transfer_changes_nothing/
..............F...................................................................EF...............................
======================================================================
ERROR: test_target_at_capacity_minus_one_is_accepted (test_pipeline.TransferTest.test_target_at_capacity_minus_one_is_accepted)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_pipeline.py", line 571, in test_target_at_capacity_minus_one_is_accepted
    crm.transfer(opp_id, "rep2", "boss")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-3/crm.py", line 262, in transfer
    raise ValueError("new owner is at capacity")
ValueError: new owner is at capacity

======================================================================
FAIL: test_failed_transfer_changes_nothing (test_atomicity.AtomicityTest.test_failed_transfer_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_atomicity.py", line 200, in test_failed_transfer_changes_nothing
    self.assert_atomic(
    ~~~~~~~~~~~~~~~~~~^
        lambda: self.crm.transfer(self.opp_id, "rep2", "boss"), ValueError
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_atomicity.py", line 45, in assert_atomic
    self.assertEqual(snapshot(self.crm), before)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: {'lea[318 chars] 'rep2', 'amount': 1000, 'original_amount': 10[216 chars]': 1} != {'lea[318 chars] 'rep1', 'amount': 1000, 'original_amount': 10[188 chars]': 1}
Diff is 1186 characters long. Set self.maxDiff to None to see it.

======================================================================
FAIL: test_transfer_counts_open_opportunities_against_capacity (test_pipeline.TransferTest.test_transfer_counts_open_opportunities_against_capacity)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_pipeline.py", line 560, in test_transfer_counts_open_opportunities_against_capacity
    self.assertEqual(crm.opps[opp_id]["owner"], "rep1")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'rep2' != 'rep1'
- rep2
?    ^
+ rep1
?    ^


----------------------------------------------------------------------
Ran 115 tests in 0.005s

FAILED (failures=2, errors=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-3/crm.py from backup (byte-identical)
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect SUCCESS
...................................................................................................................
----------------------------------------------------------------------
Ran 115 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
[exit 0]
```

## control b37_atomicity_add_lead

```text
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b37_atomicity_add_lead" --test-cmd "rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'" --expect "test_failed_duplicate_does_not_consume_an_id" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-jxpmovka/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b37_atomicity_add_lead
break applied: b37_atomicity_add_lead
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect FAILURE matching /test_failed_duplicate_does_not_consume_an_id/
F................................................................................................F.................
======================================================================
FAIL: test_failed_add_lead_changes_nothing (test_atomicity.AtomicityTest.test_failed_add_lead_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_atomicity.py", line 57, in test_failed_add_lead_changes_nothing
    self.assert_atomic(
    ~~~~~~~~~~~~~~~~~~^
        lambda: self.crm.add_lead("ANA@corp.io ", "X", "web", "rep1"),
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        DuplicateLeadError,
        ^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_atomicity.py", line 45, in assert_atomic
    self.assertEqual(snapshot(self.crm), before)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: {'lea[494 chars]'L2', 'rep1')], 'waiting': ['L2'], 'lead_seq': 3, 'opp_seq': 1} != {'lea[494 chars]'L2', 'rep1')], 'waiting': ['L2'], 'lead_seq': 2, 'opp_seq': 1}
Diff is 1015 characters long. Set self.maxDiff to None to see it.

======================================================================
FAIL: test_failed_duplicate_does_not_consume_an_id (test_validation.DuplicateTest.test_failed_duplicate_does_not_consume_an_id)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_validation.py", line 146, in test_failed_duplicate_does_not_consume_an_id
    self.assertEqual(self.crm.add_lead("bob@example.com", "Bob", "web", "rep1"), "L2")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'L3' != 'L2'
- L3
+ L2


----------------------------------------------------------------------
Ran 115 tests in 0.004s

FAILED (failures=2)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-3/crm.py from backup (byte-identical)
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect SUCCESS
...................................................................................................................
----------------------------------------------------------------------
Ran 115 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
[exit 0]
```

## control b38_duplicate_ignores_converted_leads

```text
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b38_duplicate_ignores_converted_leads" --test-cmd "rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'" --expect "test_duplicate_after_conversion" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-k9q7sy5k/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b38_duplicate_ignores_converted_leads
break applied: b38_duplicate_ignores_converted_leads
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect FAILURE matching /test_duplicate_after_conversion/
F............................................................................................F.....................
======================================================================
FAIL: test_failed_add_lead_changes_nothing (test_atomicity.AtomicityTest.test_failed_add_lead_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_atomicity.py", line 57, in test_failed_add_lead_changes_nothing
    self.assert_atomic(
    ~~~~~~~~~~~~~~~~~~^
        lambda: self.crm.add_lead("ANA@corp.io ", "X", "web", "rep1"),
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        DuplicateLeadError,
        ^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_atomicity.py", line 43, in assert_atomic
    with self.assertRaises(exc):
         ~~~~~~~~~~~~~~~~~^^^^^
AssertionError: DuplicateLeadError not raised

======================================================================
FAIL: test_duplicate_after_conversion (test_validation.DuplicateTest.test_duplicate_after_conversion)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_validation.py", line 160, in test_duplicate_after_conversion
    with self.assertRaises(DuplicateLeadError) as caught:
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
AssertionError: DuplicateLeadError not raised

----------------------------------------------------------------------
Ran 115 tests in 0.004s

FAILED (failures=2)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-3/crm.py from backup (byte-identical)
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect SUCCESS
...................................................................................................................
----------------------------------------------------------------------
Ran 115 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
[exit 0]
```

## control b39_unhashable_actor

```text
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b39_unhashable_actor" --test-cmd "rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'" --expect "test_unhashable_actor_rejected_by_every_method" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-jxrx4tyc/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b39_unhashable_actor
break applied: b39_unhashable_actor
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect FAILURE matching /test_unhashable_actor_rejected_by_every_method/
..................................................................................................................E
======================================================================
ERROR: test_unhashable_actor_rejected_by_every_method (test_validation.UnhashableActorTest.test_unhashable_actor_rejected_by_every_method)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_validation.py", line 203, in test_unhashable_actor_rejected_by_every_method
    self.assert_permission_error_and_no_change(
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^
        lambda bad=bad: self.crm.add_lead("x@corp.io", "X", "web", bad)
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_validation.py", line 190, in assert_permission_error_and_no_change
    call()
    ~~~~^^
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_validation.py", line 204, in <lambda>
    lambda bad=bad: self.crm.add_lead("x@corp.io", "X", "web", bad)
                    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-3/crm.py", line 114, in add_lead
    self._require_actor(actor)
    ~~~~~~~~~~~~~~~~~~~^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-3/crm.py", line 70, in _require_actor
    if actor not in self.users:
       ^^^^^^^^^^^^^^^^^^^^^^^
TypeError: cannot use 'list' as a dict key (unhashable type: 'list')

----------------------------------------------------------------------
Ran 115 tests in 0.004s

FAILED (errors=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-3/crm.py from backup (byte-identical)
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect SUCCESS
...................................................................................................................
----------------------------------------------------------------------
Ran 115 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
[exit 0]
```

## control b40_unhashable_new_owner

```text
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b40_unhashable_new_owner" --test-cmd "rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'" --expect "test_new_owner_must_be_a_known_rep" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-pejqx3s8/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-neutral-3/breaks/apply_break.py b40_unhashable_new_owner
break applied: b40_unhashable_new_owner
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect FAILURE matching /test_new_owner_must_be_a_known_rep/
...............................................................................E...................................
======================================================================
ERROR: test_new_owner_must_be_a_known_rep (test_pipeline.TransferTest.test_new_owner_must_be_a_known_rep)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-3/test_pipeline.py", line 518, in test_new_owner_must_be_a_known_rep
    crm.transfer(opp_id, bad, "boss")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-3/crm.py", line 249, in transfer
    new_owner not in self.users
TypeError: cannot use 'list' as a dict key (unhashable type: 'list')

----------------------------------------------------------------------
Ran 115 tests in 0.005s

FAILED (errors=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-3/crm.py from backup (byte-identical)
$ rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'   # expect SUCCESS
...................................................................................................................
----------------------------------------------------------------------
Ran 115 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
[exit 0]
```

## 7. State after the control sweep (verbatim)

```text
$ shasum -a 256 crm.py test_validation.py test_pipeline.py test_atomicity.py breaks/apply_break.py controls.tsv
e94196edf466998feaacfcf565aee2f10ca85bdf4a0fd153be88aeefbc5104ee  crm.py
1be76aee9e1736a754158b5eace841c6752727566a37a0549edba7f1b03e4df7  test_validation.py
421ff8a93c63eedaef2c07f84100a72a692b797b18c03324e36866b06992fe05  test_pipeline.py
7d59d26aa91cbc501dc01fcc6e5a740c2c9b962b9e2c0d1af6da102e7266487d  test_atomicity.py
c97a73d583b4c2753fc37ac436de812b22f385464522cfb5d0fa0dc87c6038ce  breaks/apply_break.py
3ac0182b49c8f0f57e846b2cdbb7feab469f6ea1a38a5455d2bda31b233e7bd1  controls.tsv
$ grep -c 'OK: negative control verified' negcontrol-log.md
40
$ grep -c '^## control ' negcontrol-log.md
40
$ rm -rf __pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'
...................................................................................................................
----------------------------------------------------------------------
Ran 115 tests in 0.003s

OK
[exit 0]
```

`aepkit` reports `restored ... (byte-identical)` on every control, and the hash above is the hash of the file the sweep ended with, so the final `crm.py` is the pre-sweep `crm.py`.



## 8. How each guard group is actually asserted

- **Email / name / source validation**: each rejection asserts the exception *and* that `leads`, `opps`, `log`, `waiting` and both id counters are untouched, so a silently accepted bad row fails the test; accepted rows assert the normalized email, stripped name and computed score (10/30/20, +15 for a non-free domain). The domain rule is tested at its exact boundary: a dot that is only first or only last is rejected, an interior dot is accepted (including `.example.com`).
- **Duplicate detection**: the same email in different case/whitespace raises `DuplicateLeadError` whose `existing_id` is the original lead, no new lead is created, no id is consumed, and no log entry is appended; duplicates are also detected against a *converted* lead, and the duplicate check is shown to run after the source and name checks.
- **Rep assignment and capacity**: ties go to the smallest id in string order (`r10` before `r2`), the lowest-load rep wins, managers never receive work, full reps leave the lead unowned and queued in FIFO order, and nothing is assigned while the owner is still at capacity. Converted leads stop counting toward load and the resulting free slot is asserted directly through the next assignment.
- **Waiting queue**: a win or a loss frees the slot and the oldest waiting lead is assigned with the log entry `("assign", lead_id, "system")`; the second free slot takes the second queued lead. Each event assigns exactly one lead (the multi-assignment `while` iteration is unreachable — see F5); no assignment happens when the queue is empty.
- **Permission checks**: unknown actors (including unhashable ones) raise `PermissionError` before any existence check in all six acting methods and leave the object untouched; another rep cannot qualify, convert, advance or discount; a manager can do all of those; a rep cannot qualify a lead it does not own; transfer is manager-only even when the target is invalid.
- **Qualification score**: 10 and 25 both fail, 30 passes, a lead can be qualified only once and only while `new`, and a failed qualify leaves the status and the log unchanged.
- **Stage transitions**: skipping, going backwards, staying put, unknown stage names and any move out of `won`/`lost` are rejected; invalid stage names are rejected *before* the permission check (so a non-owner gets `ValueError`), `lost` is reachable from every open stage, and 50001 vs 50000 pins the big-deal boundary.
- **Big-deal approval**: 50001 to `negotiation` by the owning rep is refused (state unchanged), the same move by a manager succeeds, 50000 needs no manager, and a big deal can still be marked lost by its rep.
- **Discounts**: bools, 0, 31, floats and strings are rejected; 1 is accepted at the lower bound; a rep stops at 10; a manager may use up to 30; the cumulative floor is checked against `original_amount` with integer truncation (999 at 30% is refused because `699*100 < 70000`), and a second discount after reaching the floor is refused.
- **Transfer rules**: managers only, new owner must be a known rep (a manager with free capacity is still refused, and an unhashable owner is `ValueError`, not `TypeError`), final stages are refused, the current owner is refused, a full target is refused, a target at `capacity-1` is accepted, and open opportunities count against the target's capacity.
- **Atomicity**: `test_atomicity.py` snapshots `leads`, `opps`, `log`, `waiting` and both id counters with `copy.deepcopy` and compares the whole object after each failing call, including failures that happen *after* other guard groups have already passed (duplicate email, highest-numbered check of `discount`, big-deal approval, the owner check in `convert`, the capacity check in `transfer`, final-stage advance). Controls `b21`, `b22`, `b34`, `b35`, `b36` and `b37` move the mutation in front of the last check to prove those tests catch a partially applied call, and `b37` additionally proves a failed call does not consume an id.
