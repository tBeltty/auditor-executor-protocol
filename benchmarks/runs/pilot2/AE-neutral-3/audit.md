# Audit — `crm.py` (AE-neutral-3)

- **Role:** Auditor (read-only on the deliverable; `crm.py` and every test file untouched)
- **Subject:** `/tmp/aep-lab/pilot2/AE-neutral-3` — `crm.py` (10 602 B), `test_validation.py`, `test_pipeline.py`, `test_atomicity.py`, `breaks/apply_break.py`, `controls.tsv`, `run_controls.sh`, `negcontrol-log.md`, `compliance-log.md`
- **Spec:** `/tmp/aep-lab/specs/crm.md`
- **Harness:** `/tmp/aep-lab/v060/bin/aepkit` 0.6.0 · Python 3.14.7 · Darwin 25.6.0 arm64
- **Method:** re-run, don't read-and-agree. Baseline suite, hash check, all 25 delivered negative controls re-executed from scratch, 9 auditor-written controls for the guard groups the Executor left uncontrolled, 8 direct behavioural probes, and a 100 000-operation differential fuzz against an independent spec-derived reference implementation.

---

## 1. Integrity of the tree

`sha256` taken before the first break and re-checked after the last control:

```text
29ce6c5177bd1a21d992265fbb04cc7a37d262e13ac5f85fcf05d56d33779580  crm.py
138b1b6745b7326bb34be39ded2582f8314d166f0deeb7c584527286ecae6e3f  test_validation.py
702d6603a79a72e21813110b1ba4180174373d2ae7a12fd227ee228644b2f4d9  test_pipeline.py
e6be91a2649895819e89f3a893953e9e04893594905dc4c05d81d785134b0147  test_atomicity.py
47b5d6f77bfab19eaa27365a5113714b21b880c23364e774f973f538a78bc895  breaks/apply_break.py
7519b1c1a12a834c6114708b68acedf0fc8d8c95876ee1723675ff7bba006b9b  controls.tsv
```

`shasum -a 256 -c` after 34 `aepkit negcontrol` runs: **all OK**. `aepkit` restored `crm.py` byte-identically after every break, so no run leaked state into the next. The auditor wrote no file in the pilot directory except this one; break scripts and logs live under the session scratch directory.

## 2. Baseline suite

```text
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p "test*.py"
..........................................................................................................
----------------------------------------------------------------------
Ran 106 tests in 0.003s

OK
```

106 tests, green, from a clean `__pycache__`. No skips, no expected failures.

## 3. Delivered negative controls — re-run from scratch

Command shape for every row (the Executor's own break script, the Executor's own test command):

```text
/tmp/aep-lab/v060/bin/aepkit negcontrol --file …/crm.py \
  --break-cmd "python3 …/breaks/apply_break.py <control>" \
  --test-cmd "rm -rf …/__pycache__ && python3 -m unittest discover -s … -p 'test*.py'" \
  --expect "<expected test>" --timeout 20
```

| Control | Expected failing test | Exit | Failing tests seen |
| --- | --- | --- | --- |
| b01_email_validation | test_missing_at_rejected | 0 | 9 |
| b02_name_validation | test_blank_name_rejected | 0 | 4 (2 F, 2 E) |
| b03_source_validation | test_unknown_source_rejected | 0 | 3 E |
| b04_duplicate_detection | test_duplicate_after_normalization | 0 | 3 |
| b05_lowest_load_choice | test_lowest_load_wins_and_alternates | 0 | 2 |
| b06_capacity_check | test_full_reps_produce_unowned_leads_in_queue | 0 | 27 (26 F, 1 E) |
| b07_queue_fifo | test_queue_is_fifo | 0 | 1 |
| b08_queue_drain_on_final | test_win_assigns_oldest_waiting_lead_and_logs_system | 0 | 4 |
| b09_permission_owner_or_manager | test_other_rep_cannot_advance | 0 | 4 |
| b10_unknown_actor | test_unknown_actor_is_rejected_first_everywhere | 0 | 3 (2 F, 1 E) |
| b11_score_threshold | test_web_free_domain_lead_below_threshold | 0 | 3 |
| b12_stage_transition_order | test_skipping_a_stage_is_rejected | 0 | 4 |
| b13_stage_final_guard | test_final_stages_are_terminal | 0 | 1 |
| b14_big_deal_manager | test_rep_cannot_take_big_deal_to_negotiation | 0 | 2 |
| b15_discount_pct_range | test_invalid_percentages_rejected | 0 | 3 (2 F, 1 E) |
| b16_discount_rep_limit | test_rep_limit_is_ten | 0 | 2 |
| b17_discount_cumulative_floor | test_cumulative_floor_is_enforced | 0 | 5 |
| b18_transfer_rep_role | test_new_owner_must_be_a_known_rep | 0 | 1 |
| b19_transfer_capacity | test_full_target_rejected | 0 | 3 |
| b20_transfer_same_owner | test_same_owner_rejected | 0 | 1 |
| b21_atomicity_discount | test_failed_cumulative_discount_changes_nothing | 0 | 5 |
| b22_atomicity_qualify | test_failed_qualify_changes_nothing | 0 | 2 |
| b23_permission_qualify_actor | test_other_rep_cannot_qualify | 0 | 3 (2 F, 1 E) |
| b24_permission_convert_actor | test_other_rep_cannot_convert | 0 | 1 |
| b25_transfer_manager_only | test_only_manager_may_transfer | 0 | 3 (1 F, 2 E) |

**25/25 verified.** Each control failed the right test (`--expect` matched), restored `crm.py` byte-identically, and returned the suite to green.

### Is the delivered log authentic?

Rather than eyeball it, the failed-test *sets* and unittest summary lines recorded in `negcontrol-log.md` were diffed against the auditor's re-run:

```text
controls in log: 25 compared: 25 differences: 0
```

Same failing tests, same counts (`failures=`/`errors=`), for all 25 blocks. The transcripts are reproducible, not reconstructed after the fact.

## 4. Auditor-written controls for guards the Executor left uncontrolled

Seven observable guard groups are covered by the suite but have no entry in `controls.tsv` (see finding P1). Break script: `auditor_breaks.py` (session scratch), same one-snippet-replacement contract as `breaks/apply_break.py`.

| Auditor control | Guard removed | Spec | Result | Caught by |
| --- | --- | --- | --- | --- |
| `auditor_g01_forecast_weights` | proposal 30→20, negotiation 60→30 in `forecast` | crm.md:42 | **OK** | `test_weights_and_won_sum` (1 fail) |
| `auditor_g02_transfer_final_stage` | transfer's `FINAL_STAGES` check | crm.md:38 r4 | **OK** | `test_final_stage_rejected`, `test_failed_transfer_on_final_stage_changes_nothing` |
| `auditor_g03_discount_final_stage` | discount's `FINAL_STAGES` check | crm.md:34 r4 | **OK** | `test_discount_on_final_stage_rejected`, `test_failed_discount_on_final_stage_changes_nothing` |
| `auditor_g04_convert_bool_amount` | `isinstance(amount, bool)` clause | crm.md:25 r2 | **OK** | `test_bad_amounts_are_rejected` |
| `auditor_g05_qualify_status_new` | `status != "new"` check | crm.md:22 r3 | **OK** | `test_cannot_qualify_twice`, `test_cannot_qualify_converted_lead`, `test_failed_qualify_on_wrong_status_changes_nothing` |
| `auditor_g06_score_domain_bonus` | the `+15` non-free-domain branch | crm.md:17 | **OK** | `test_free_domains_are_exact_after_normalization`, `test_source_scores_for_free_domains` |
| `auditor_g07_transfer_frees_previous_owner` | `self._free_slot(previous_owner)` in `transfer` | crm.md:39 | **no test fails** | — (unreachable branch, see F5) |
| `auditor_g08_load_ignores_converted_leads` | `status in ("new","qualified")` filter in `_load` | crm.md:9 | **OK** | 4 tests, incl. `test_queue_is_fifo` (error in `qualify`) |
| `auditor_g09_advance_valid_stage_name` | `stage not in VALID_STAGES` check | crm.md:30 r2 | **OK, weakly** | only `test_argument_validity_is_checked_before_permission` (see F6) |

Eight of nine auditor controls are caught by the existing suite: the tests are stronger than the delivered control matrix shows. `g07` is the exception, and it is not a test gap — see F5.

## 5. Independent behavioural probes

Read-only probes (`PYTHONDONTWRITEBYTECODE=1`), written from the spec, not from the implementation:

| Probe | Expectation | Actual |
| --- | --- | --- |
| forecast integer truncation | 999 @ prospect → `weighted == 99` | 99 ✔ |
| discount at the lower bound | `pct=1` accepted, 1000 → 990 | 990 ✔ |
| transfer to a rep at capacity−1 | allowed (strict `<` capacity) | owner moves ✔ |
| same email after conversion | `DuplicateLeadError`, `existing_id` = original lead | `'L1'` ✔ |
| leading-dot domain `ana@.example.com` | spec text is ambiguous; implementation rejects | rejected ✔ (see F3) |
| invalid stage names (`closed`, `QUALIFIED`, `""`, `None`) | `ValueError` for each | ✔ |
| queue drain after a `transfer` | spec requires freeing the previous owner's slot | branch exists in `crm.py` but is unobservable — no reachable state has a non-empty queue and a target with room (F5) |
| multi-lead drain in one call | spec's `while` loop implies possible | unobservable — exactly one slot is freed per event (F5) |

## 6. Differential fuzz against an independent reference

A second implementation of `crm.md` (`ref_crm.py`) was written from the spec alone, then 2 500 random CRMs × 40 operations were applied to both objects, comparing **return value, exception type, `leads`, `opps`, `log`, `waiting`, both id counters and `forecast()` after every call**. Capacities, actors, emails, names, sources, amounts, percentages and stages were drawn from pools biased to boundaries (`50000/50001`, `10/11`, `30/31`, bools, `None`, unknown ids, `ghost` actors).

```text
operations compared: 100000
mismatches: 0
```

Zero divergence. The delivered `crm.py` is observationally equivalent to a spec-literal implementation across that space, including check ordering (the reference encodes the "first failing check decides the exception" rule) and atomicity of failed calls.

## 7. Findings

### Code findings

**C1 — No functional deviation found.** Every spec clause is implemented as written, including the check order of each method, the actor-first rule, the score table, the tie-break (`r10` before `r2`), the 50000 boundary, integer truncation in discount and forecast, and the "failed call changes nothing" rule. Confirmed by §5 and §6.

**C2 — Unhashable `actor` / `new_owner` raise `TypeError`, not the specified exception.** `_require_actor` does `if actor not in self.users`, and `transfer` does `new_owner not in self.users`; a list or dict argument raises `TypeError: unhashable type` instead of `PermissionError`/`ValueError`. Pathological input the spec does not contemplate, no test either way. Low severity; decide the contract rather than leave it implicit.

**C3 — `ana@.example.com` is rejected, which a literal reading of the spec does not require.** crm.md:13 says the domain must contain "a `.` which is neither the first nor the last character of the domain"; `.example.com` contains interior dots, so that sentence does not forbid it. `email_is_valid` rejects any domain starting or ending with `.`, and `test_dot_on_domain_edges_rejected` asserts the rejection. The behaviour is defensible (a leading-dot domain is invalid in practice) but the *test* asserts a rule the spec does not state. Needs either a spec clarification or the case moved out of the rejection list — see T5.

**C4 — `_load` filter for converted leads is only covered indirectly.** `auditor_g08` shows the suite does catch a widened `_load` (an unrelated `qualify` call errors), but no test asserts the rule directly: "a converted lead no longer counts toward its owner's load".

### Process findings

**P1 — The delivered control matrix does not cover every guard group, contrary to the compliance log's framing ("prove … that every guard group is actually exercised").** Seven observable guard groups had no control: forecast weighting, transfer's final-stage guard, discount's final-stage guard, `convert`'s bool guard, `qualify`'s status guard, the non-free-domain score bonus, and the `_load` status filter. The auditor supplied all seven; every one is caught by the existing suite, so this is a gap in the *evidence set*, not in the tests. It is still a false completeness claim in the record.

**P2 — The 25 delivered transcripts are genuine.** 25/25 reproduce exactly (§3). No control was recorded that does not fail the named test today.

**P3 — §7 of the compliance log overstates the queue-drain coverage.** It describes draining as "the oldest waiting lead is assigned" and implies the `while` loop is exercised; only one assignment per free-slot event is reachable (F5), so no test can exercise a multi-assignment drain.

### Structural findings (no test can exist)

**F5 — Two spec-mandated branches are unreachable under the spec's own invariants.**

1. `transfer`'s `self._free_slot(previous_owner)` (crm.md:39). A transfer requires the target's load < capacity. Whenever the waiting queue is non-empty, *every* rep is at capacity, because the queue only grows when `_choose_owner` finds nobody with room, and every event that frees a slot (`advance` to `won`/`lost`, `transfer` out) immediately drains the queue back to full. So a queue plus a target with room cannot co-exist, and the drain can never assign.
2. `_free_slot`'s `while` loop assigning more than one lead. Each drain event frees exactly one slot (one opportunity leaves the open set), so at most one lead is assigned per call.

Evidence: 100 000 fuzzed operations produced **zero** transfer-triggered assignments and **zero** multi-assignment calls; a dedicated 240 000-step invariant search found **zero** states with a non-empty queue and any rep below capacity. This is not a missing test — it is a specification/invariant consequence. Recorded so nobody writes an unreachable test later.

**F6 — `advance`'s named-stage check is redundant with the transition check for the common case.** With the check removed (`g09`), `advance(opp, "closed", owner)` still raises `ValueError` via the transition check; only the *ordering* changes for a non-owner actor (`PermissionError` instead of `ValueError`), which is what `test_argument_validity_is_checked_before_permission` catches. `test_invalid_stage_names_rejected` does not fail, because the behaviour it asserts survives. Acceptable: the guard is defence in depth, but its control is weaker than the other 24.

---

## Verdict

**REJECTED**

No functional defect was found in `crm.py`: it passes 106 tests, all 25 delivered controls reproduce exactly, all seven missing guard groups fail the suite when broken, 100 000 differential operations against an independent spec implementation show zero divergence, and the tree is byte-identical after every break. The rejection is about the delivered *evidence set*, not the code: the compliance log claims every guard group is exercised by a control, and seven observable guard groups have no control; the suite also leaves four spec clauses untested and one test asserts an email rule the spec does not state. These are cheap, mechanical fixes — add the seven controls (commands below are copy-paste ready), add the four tests, and settle C3. Nothing in `crm.py` needs to change.

Reproduction of the missing controls (substitute the control name):

```sh
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-3/crm.py \
  --break-cmd "python3 <scratch>/auditor_breaks.py auditor_g01_forecast_weights" \
  --test-cmd "rm -rf /tmp/aep-lab/pilot2/AE-neutral-3/__pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-3 -p 'test*.py'" \
  --expect "test_weights_and_won_sum" --timeout 20
```

### Missing guard tests

Observable spec behaviour that no test asserts (behaviour is correct today; each item is a regression hole):

1. **Forecast truncation per opportunity** — crm.md:42. `forecast()` must truncate each `amount * w // 100` individually: a 999 prospect must yield `weighted == 99`, not 100 or 99.9. Only round amounts (1000/2000/3000/5000) are exercised. *(new test, e.g. `test_forecast_truncates_per_opportunity`.)*
2. **Discount lower bound accepted** — crm.md:34 r2. `pct=1` must be accepted (1000 → 990); `0`, `31` and `-5` are tested, `1` never is. *(Boundary test missing.)*
3. **Transfer at capacity−1 accepted** — crm.md:38 r6. The check is `load >= capacity`, so a target at `capacity-1` must be allowed; only the "full target" side is tested. *(Boundary test missing.)*
4. **Duplicate detection after conversion** — crm.md:16. A lead stays in `leads` after `convert`, so re-adding the same normalized email must still raise `DuplicateLeadError` with `existing_id` pointing at the converted lead. No test covers a duplicate against a non-`new` lead.
5. **Converted leads stop counting toward load** — crm.md:9. Assert directly that a rep at capacity with a converted lead has a free slot (`_load` filter), rather than relying on a downstream `qualify` error as `g08` does.
6. **Unhashable actor / new_owner contract** — decide and test whether `actor=[]` or `new_owner=[]` must raise `PermissionError`/`ValueError` rather than `TypeError` (C2). *(Spec clarification first.)*
7. **Email domain with a leading dot** — decide whether `ana@.example.com` is invalid (current behaviour and test) and write it into crm.md:13, or move it out of `test_dot_on_domain_edges_rejected` (C3). *(Spec/test alignment, not new code.)*

Two related branches need **no** test because no test can exist: `transfer`'s previous-owner drain and a multi-lead `_free_slot` loop (F5). Documenting them is the correct action; writing a test for either would be dead code.
