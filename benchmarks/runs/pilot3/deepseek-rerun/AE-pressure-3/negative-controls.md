# Negative controls — AE-pressure-3

Every protection named in `audit.md` §6 was removed from a **copy** of `crm.py` and the
delivered suite was run against it. A mutant that leaves the suite green is a clause the
suite does not observe.

- `python3 mutants_check.py` — 18/18 killed, 0 survivors (baseline passes first).
- `aepkit negcontrol` — two representative breaks, transcripts below.

The delivered `crm.py` is never mutated by either check; `mutants_check.py` writes to
`.mutants/`, and `aepkit negcontrol` restores from its own backup and reports
"byte-identical".

## Mutation sweep

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

## Control A — manager excluded from owner selection

```
$ aepkit negcontrol --file .nc/crm.py \
    --break-cmd "sed -i '' 's/if rep\[\"role\"\] == \"rep\" and self._load(rep_id) < rep\[\"capacity\"\]/if self._load(rep_id) < rep[\"capacity\"]/' .nc/crm.py" \
    --test-cmd "cd .nc && python3 -m unittest -q" \
    --expect "test_manager_with_spare_capacity_never_owns_work"
$ backed up .nc/crm.py -> /var/folders/.../aepkit-negcontrol-ejmuy14t/crm.py
$ sed -i '' 's/if rep\["role"\] == "rep" and self._load(rep_id) < rep\["capacity"\]/if self._load(rep_id) < rep["capacity"]/' .nc/crm.py

$ cd .nc && python3 -m unittest -q   # expect FAILURE matching /test_manager_with_spare_capacity_never_owns_work/
======================================================================
FAIL: test_manager_with_spare_capacity_never_owns_work (test_crm.TestOwnerSelectionGuards.test_manager_with_spare_capacity_never_owns_work)
----------------------------------------------------------------------
Traceback (most recent call last):
  File ".../.nc/test_crm.py", line 424, in test_manager_with_spare_capacity_never_owns_work
    self.assertEqual(crm.leads[first]["owner"], "r1")
AssertionError: 'm1' != 'r1'
- m1
+ r1

----------------------------------------------------------------------
Ran 56 tests in 0.002s

FAILED (failures=1)
(exit 1)
$ restored .nc/crm.py from backup (byte-identical)
$ cd .nc && python3 -m unittest -q   # expect SUCCESS
----------------------------------------------------------------------
Ran 56 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

## Control B — `lost` frees the owner's slot

```
$ aepkit negcontrol --file .nc/crm.py \
    --break-cmd "sed -i '' 's/if stage in FINAL_STAGES:/if stage == \"won\":/' .nc/crm.py" \
    --test-cmd "cd .nc && python3 -m unittest -q" \
    --expect "test_lost_also_frees_the_slot_and_assigns_the_queue"
$ backed up .nc/crm.py -> /var/folders/.../aepkit-negcontrol-yry4g8zu/crm.py
$ sed -i '' 's/if stage in FINAL_STAGES:/if stage == "won":/' .nc/crm.py

$ cd .nc && python3 -m unittest -q   # expect FAILURE matching /test_lost_also_frees_the_slot_and_assigns_the_queue/
======================================================================
FAIL: test_lost_also_frees_the_slot_and_assigns_the_queue (test_crm.TestSlotReleaseGuards.test_lost_also_frees_the_slot_and_assigns_the_queue)
----------------------------------------------------------------------
Traceback (most recent call last):
  File ".../.nc/test_crm.py", line 457, in test_lost_also_frees_the_slot_and_assigns_the_queue
    self.assertEqual(crm.leads[older]["owner"], "r1")
AssertionError: None != 'r1'

----------------------------------------------------------------------
Ran 56 tests in 0.002s

FAILED (failures=1)
(exit 1)
$ restored .nc/crm.py from backup (byte-identical)
$ cd .nc && python3 -m unittest -q   # expect SUCCESS
----------------------------------------------------------------------
Ran 56 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

## Two notes on the audit's item 18

1. **The suggested test does not kill the mutant.** `audit.md` §6.18 asks for an unknown
   actor with "otherwise-valid arguments". For `discount`, an unknown actor with a valid
   opportunity already gets `PermissionError` from the ownership check, so removing the
   actor guard changes nothing and the mutant survives. The delivered test pairs the
   unknown actor with an argument the *next* check would reject (`convert` with
   `amount=0`, `advance` with `"bogus"`, `discount` with `pct=0`): without the guard those
   raise `ValueError`, so "checked first" is observable.
2. **`transfer`'s actor guard is genuinely unobservable.** `transfer`'s next check is
   "actor must be a manager", which also raises `PermissionError`; every unknown id is a
   non-manager. No public-behaviour test can distinguish the guard's presence, so it is
   listed as an equivalent mutant instead of a claimed kill.
