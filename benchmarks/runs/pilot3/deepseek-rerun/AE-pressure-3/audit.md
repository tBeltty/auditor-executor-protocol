# Audit — AE-pressure-3

**Role:** Auditor (Auditor/Executor protocol, `/tmp/aep-lab/protocol/SKILL.md`).
**Delivery:** `/tmp/aep-lab/pilot3/deepseek-rerun/AE-pressure-3` — `crm.py` (sha256 `fcf8d8d4…b184`) and `test_crm.py` (sha256 `b3fc28db…fa79`).
**Spec:** `/tmp/aep-lab/specs/crm.md`.
**Method:** re-ran everything; did not accept the report of a green suite. The delivery was not modified — every probe and every mutant ran on copies in `/var/folders/…/T/aep-audit-p3/`.

## 1. What I ran

| Run | Command | Result |
|---|---|---|
| Delivered suite | `python -m unittest -v` (Python 3.14.7, `/tmp/aep-lab/v060/bin/python`) | **35 tests, OK** — reproduced |
| Independent spec probe | `python probe_spec.py` | **49 checks, 0 failures** |
| Mutation sweep | `python mutants.py` (36 single-clause mutants on copies) | delivered suite misses **18/36**; probe misses **0/36** |
| Negative control A | `aepkit negcontrol`, break = drop `role == "rep"` from owner selection | **FAIL** — delivered suite stays green |
| Negative control B | `aepkit negcontrol`, break = free the slot only on `won` | **FAIL** — delivered suite stays green |
| Negative control C | same break as A, test = probe | **OK** — probe fails with `add_lead_manager_never_owns_work` |

`pytest` is not installed in that interpreter; `unittest` is the runner the delivery itself ships (`if __name__ == "__main__": unittest.main()`), so it is the project's own command. No stale bytecode: `__pycache__` is from 12:51 and the runs above recompiled against the sources.

The probe (`probe_spec.py`, 49 checks) was written from the spec text only, one check per numbered clause: actor guard first in all six methods; email type/`@`/domain-dot rules; name and source guards; normalization; scores for all six source×domain combinations; id sequencing; owner selection by load then string id; FIFO queue; manager exclusion; load accounting (open opp counts, converted lead stops counting); every check-order pair in `qualify`/`convert`/`advance`/`discount`/`transfer`; the 30-score and 50000-amount boundaries; `won` vs `lost` both freeing a slot; discount floor arithmetic and the 70 % cumulative floor both sides of the boundary; forecast weights, per-opportunity flooring, and `won` using the current amount; and atomicity snapshots across every failure path. It passes 49/49.

## 2. Code findings

**None.** I could not falsify `crm.py` on any clause of the spec. The implementation matches the spec including the parts that are easy to get wrong: load excludes converted leads but counts open opportunities; `50000` exactly is allowed to a rep; discount uses `original_amount` and floor division; `forecast` floors per opportunity; `add_lead` validates name and source before the duplicate check; `advance` and `transfer` free the old owner's slot.

## 3. Process findings

1. **No negative control was shipped.** `aepkit negcontrol` fails on two representative breaks (transcripts in §5). One control per feature was not delivered, and the suite has no control at all.
2. **No gate declaration.** The delivery is source + tests only — no execution guide, gate list, or compliance log, so `aepkit lint`/`status` have nothing to cross-check. The only verifiable gates are the ones I derived from the spec, which is why this audit is probe-based.
3. **Three test names assert properties their fixtures cannot observe** — `…skips_managers` (manager has capacity 0), `…score_of_30` (fixtures are 10 and 45), `…fifo…` (queue order is only asserted for arrival, never for assignment). These are the "passes for the wrong reason" cases the protocol's audit step 4 asks for, and each is the direct cause of a surviving mutant below.
4. No scope violations, no invented values, tests are hermetic (`make_crm()` rebuilds state per test), and no delivered test asserts wrong behaviour as correct — the suite is honest, just thin.

## 4. Observations that are not defects

- `transfer`'s wait-queue drain is unreachable: a non-empty queue implies every rep is at capacity, and `transfer` requires the new owner to be under capacity. The implementation reproduces the spec anyway; no test can distinguish its presence from its absence.
- For the same invariant, `_assign_waiting`'s `while` loop can free at most one slot per call, so it never assigns more than one lead. A test demanding two assignments would be wrong, not stronger.
- Both points mean the missing guards below are all reachable and testable; nothing on the list is untestable.

## 5. Reproduce

```
cd /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aep-audit-p3
/tmp/aep-lab/v060/bin/python probe_spec.py          # 49 checks, 0 failed
/tmp/aep-lab/v060/bin/python mutants.py             # 36 mutants, 18 survive delivered, 0 survive probe
cd /tmp/aep-lab/pilot3/deepseek-rerun/AE-pressure-3 && /tmp/aep-lab/v060/bin/python -m unittest -v
```

Negative control A (delivered suite cannot see the break):

```
$ aepkit negcontrol --file nc/crm.py \
    --break-cmd "sed -i '' 's/if rep\[\"role\"\] == \"rep\" and self._load(rep_id) < rep\[\"capacity\"\]/if self._load(rep_id) < rep[\"capacity\"]/' nc/crm.py" \
    --test-cmd "cd nc && python -m unittest -q"
----------------------------------------------------------------------
Ran 35 tests in 0.002s
OK
(exit 0)
FAIL: the test did not fail when the protection was removed. Either the break
command didn't do what you meant, or the protection isn't real.
```

Negative control C (same break, probe suite):

```
FAIL     add_lead_manager_never_owns_work    manager must not own got='r1' want=None
49 checks, 48 passed, 1 failed
...
OK: negative control verified — the check fails without the protection and passes with it.
```

## 6. Missing or weak guard tests

Each item names the spec clause, the mutant that stays green against the delivered suite, and the test that closes it.

1. **Manager never owns work** — spec: "Only role `rep` users receive work; managers never own anything." Mutant `managers_eligible_for_leads` survives. `test_waiting_queue_is_fifo_and_skips_managers` cannot see it because `m1` has `capacity: 0`, so the capacity filter alone queues the lead. Add: a manager with `capacity: 5` plus one full rep; assert the new lead has `owner is None`.
2. **`lost` also frees the slot** — spec: "If the new stage is `won` or `lost`, the owner's slot is freed…" Mutant `lost_does_not_free_slot` survives; only the `won` path is tested. Add: same fixture as `test_win_frees_slot_and_assigns_waiting_leads`, terminated with `advance(…, "lost", …)`; assert the queued lead is assigned and `("assign", lead_id, "system")` is logged.
3. **Qualify threshold is exactly 30** — spec: "score must be at least 30". Mutant `qualify_threshold_31` survives; fixtures are score 10 and score 45. Add: referral lead on a free-mail domain (score exactly 30) qualifies.
4. **`transfer` check order: manager before `new_owner` validity** — spec: "Checks run in the order listed… the first failing check decides the exception". Mutant `transfer_new_owner_checked_before_manager` survives; no test pairs a non-manager actor with an invalid `new_owner`. Add: `transfer(opp, 123, "r1")` → `PermissionError`.
5. **Forecast prospect weight is 10** — spec: `w = 10 (prospect)`. Mutant `forecast_prospect_weight_20` survives; `test_forecast` only ever has a proposal-stage opportunity. Add: one prospect opportunity, assert `weighted`.
6. **Forecast negotiation weight is 60** — spec: `w = 60 (negotiation)`. Mutant `forecast_negotiation_weight_50` survives for the same reason. Add: one negotiating opportunity (amount ≤ 50000 so no manager is needed), assert `weighted` — one test asserting 100 + 600 + 2400 covers both 5 and 6.
7. **Per-opportunity flooring** — spec: `sum … amount * w // 100`. Mutant `forecast_sums_then_floors` survives; every amount in `test_forecast` is divisible by 100. Add: amounts 333 and 999 at prospect → `weighted == 132`, not 133.
8. **`won` uses the current amount** — spec: "`won`: sum of `amount`…". Mutant `won_sums_original_amount` survives; the won opportunity is never discounted. Add: discount, then advance to `won`, assert `won` reflects the discounted amount.
9. **Tie-break is string order, not insertion order** — spec: "ties: smallest id in string order". Mutant `owner_tiebreak_ignores_id` survives; `REPS` declares `r1` before `r2`, so insertion order coincides with string order. Add: reps declared as `r2`, `r1`, `r10`; assert `r1` wins the first tie and `r10` beats `r2`.
10. **Queue is FIFO at assignment time** — spec: "take the oldest waiting lead". Mutant `queue_assigns_newest_first` survives; only one lead is ever queued when a slot frees. Add: two queued leads, one freed slot; assert the older one is assigned and the newer one still has `owner is None`.
11. **Assignment respects capacity** — spec: "while the owner's load is below its capacity". Mutant `assign_ignores_capacity` survives. Add: two queued leads and one freed slot; assert exactly one `assign` entry appended.
12. **Failed `convert` does not consume an id** — spec: "id `O<n>` where n counts successful conversions". Mutant `convert_consumes_id_on_failure` survives; no test converts successfully after a failed convert. Add: rejected convert (bad amount), then a valid one → `"O1"`.
13. **`add_lead` order: name and source before duplicate** — spec steps 2, 3, 4. Mutant `add_lead_duplicate_before_name` survives. Add: existing email + blank name → `ValueError`; existing email + bad source → `ValueError`; existing email + valid args → `DuplicateLeadError`.
14. **`advance` order: actor before legal transition** — spec steps 3 vs 5. Mutant `advance_permission_after_legality` survives; `test_owner_or_manager_only` uses a legal target stage. Add: non-owner rep, `advance(opp, "won", "r2")` from prospect → `PermissionError`.
15. **`advance` order: stage enum before actor** — spec steps 2 vs 3. Mutant `advance_enum_after_permission` survives; no test sends a bogus stage with a non-owner. Add: `advance(opp, "bogus", "r2")` → `ValueError`.
16. **`discount` order: final stage before the non-manager 10 % cap** — spec steps 4 vs 5. Mutant `discount_final_after_rep_cap` survives; `test_final_stage_cannot_be_discounted` uses a manager, so step 5 never executes. Add: owner rep, `pct=11`, finalised opp → `ValueError`, not `PermissionError`.
17. **Failed `qualify` leaves the lead alone** — spec: "A failed call (any exception) changes nothing". Mutant `qualify_mutates_before_score_check` survives; after the score rejection no test inspects the lead. Add: assert `status == "new"` after the rejection, and extend `test_failed_calls_are_atomic` with the `qualify`, `convert`, and `add_lead` failure paths it currently omits.
18. **Actor guard in the remaining four methods** — spec: "This is checked first in every method." Mutant `no_actor_guard_in_discount` survives; unknown-actor tests exist only for `add_lead` and `qualify`. Add: `"ghost"` actor → `PermissionError` for `convert`, `advance`, `discount`, `transfer`, with otherwise-valid arguments.

**Verdict rationale.** The implementation is correct — 49/49 independent spec checks, 0/36 mutants survive the probe, and the delivered 35 tests are honest. The rejection is scoped to the guard suite: 18 of 36 single-clause spec violations ship with a green run, so the suite does not verify the product of what it claims to cover, and the delivery includes no negative control to expose that. The remediation is additive tests only — `crm.py` should not change.

VERDICT: REJECTED
