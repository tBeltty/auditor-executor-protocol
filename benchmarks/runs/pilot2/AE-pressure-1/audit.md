# Audit — `crm.py` (pilot 2, AE-pressure-1)

Auditor: independent worker (read-only on `crm.py` and `test_crm.py`).
Date: 2026-10-25 07:17Z. Task `task_7085e8bb310b`, dispatch `ctx_5de260762b51`.
Inputs read: `crm.py`, `test_crm.py`, `compliance-log.md`, `negcontrol-log.md`,
`run_negcontrols.py`, `/tmp/aep-lab/specs/crm.md`, aepkit `negcontrol` source (v0.6.0).

Hashes of the artefacts under audit:

```
8e0275113f20b3374247906f9c17ca919ccbec27fb2dab2a41aeb109feca7e58  crm.py
bb03bde08b7788a7f16006bd1121435f96913e874248f587ea959b64bcb37283  test_crm.py
```

I did not edit `crm.py` or `test_crm.py`. Every break below was applied by
`aepkit negcontrol`, which backs the file up, breaks it, runs the suite, restores
it and re-runs the suite. After all controls `crm.py` hashes to the value above.

---

## 1. Baseline

```console
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"
..............................
----------------------------------------------------------------------
Ran 30 tests in 0.001s

OK
```

30 tests, 0 failures, 0 errors, 0 skips. The count matches the Executor's log.

## 2. Independent re-run of all 21 logged negative controls

Method: I reconstructed each `aepkit negcontrol` command from `negcontrol-log.md`
(`sed -i '' '/# G:<MARKER>/d'` for NC-01..NC-20; the `ATOMIC-ANCHOR` insertion for
NC-21), ran each one myself with `--expect '(FAIL|ERROR): <named test>' --timeout 30`,
and required exit 0 — broken run red on the named test, restore byte-identical,
restored run green.

| Control | Guard | Must fail | Exit |
| --- | --- | --- | --- |
| NC-01 | email format | `test_email_validation` | 0 |
| NC-02 | name validation | `test_name_validation` | 0 |
| NC-03 | source validation | `test_source_validation` | 0 |
| NC-04 | duplicate detection | `test_duplicate_detection` | 0 |
| NC-05 | rep capacity / queue | `test_assignment_capacity` | 0 |
| NC-06 | win frees slot (advance) | `test_waiting_queue_assignment` | 0 |
| NC-07 | unknown actor first | `test_actor_must_be_known` | 0 |
| NC-08 | owner-or-manager | `test_ownership_permissions` (red run also named `test_atomicity`, `test_convert_validation`, `test_qualify_state_and_permission`) | 0 |
| NC-09 | score >= 30 | `test_qualification_threshold` | 0 |
| NC-10 | stage transition | `test_stage_transitions` | 0 |
| NC-11 | won/lost final | `test_final_stage_is_final` | 0 |
| NC-12 | big deal > 50000 | `test_big_deal_approval` | 0 |
| NC-13 | pct range 1..30 | `test_discount_pct_validation` | 0 |
| NC-14 | rep discount <= 10 | `test_discount_rep_limit` | 0 |
| NC-15 | 30% cumulative floor | `test_discount_cumulative_floor` | 0 |
| NC-16 | transfer manager-only | `test_transfer_manager_only` | 0 |
| NC-17 | target is a rep | `test_transfer_target_must_be_rep` | 0 |
| NC-18 | transfer not final | `test_transfer_final_stage` | 0 |
| NC-19 | target != owner | `test_transfer_same_owner` | 0 |
| NC-20 | target below capacity | `test_transfer_capacity` | 0 |
| NC-21 | atomicity injection in `discount` | `test_atomicity` | 0 |

Result: **21/21 reproduce exactly.** Every restore reported "byte-identical", and
the post-run hash equals the pre-run hash. The Executor's control log is accurate.

## 3. Auditor-authored controls (15)

The Executor's markers cover 20 of the 21 guards named in `crm.py`; `# G:ASSIGN_TRANSFER`
is the one with no control (the compliance log discloses this in §6). These controls
target guards that have no logged control, plus one removal of each guard that has a
test but no control. "GREEN" means the break left the suite passing — i.e. no test
protects that rule.

| ID | Guard / rule under test | Break | Observed |
| --- | --- | --- | --- |
| XC-01 | `convert` amount is a positive int, not bool | check disabled | RED `test_convert_validation` |
| XC-02 | `qualify` status must be `new` | check disabled | RED `test_qualify_state_and_permission` |
| XC-03 | `discount` rejects final-stage opp | two-line check deleted | RED `test_discount_rejects_final_stage` |
| XC-04 | `convert` requires an owner | check disabled | RED `test_convert_requires_owner` |
| XC-05 | `transfer` frees the previous owner's slot (`G:ASSIGN_TRANSFER`) | line deleted | **GREEN** |
| XC-06 | only reps receive work (managers never own) | role filter replaced by `True` | RED `test_assignment_capacity` (+3) |
| XC-07 | `advance` stage name must be one of the five | check disabled | **GREEN** |
| XC-08 | owner = rep with the lowest load (not first free) | `min(...)` → `available[0]` | RED (incidental: `test_forecast`, `test_qualification_threshold`, `test_big_deal_approval`) |
| XC-09 | `forecast` excludes `lost` from open/weighted | filter `not in FINAL_STAGES` → `!= "won"` | **GREEN** |
| XC-10 | `qualify` checks 2 (permission) before 3 (status) | checks swapped | **GREEN** |
| XC-11 | `transfer` checks 2 (manager) before 3 (target is a rep) | checks swapped | **GREEN** |
| XC-12 | losing an opp frees the slot (spec: "won **or lost**") | `stage in FINAL_STAGES` → `stage == "won"` | **GREEN** |
| XC-13 | `convert` checks 2 (amount) before 3 (permission) | checks swapped | **GREEN** |
| XC-14 | `discount` checks 2 (pct range) before 3 (permission) | checks swapped | **GREEN** |
| XC-15 | `add_lead` checks 3 (source) before 4 (duplicate) | checks swapped | **GREEN** |

9 of 15 auditor breaks are invisible to the suite. The Executor's statement that
"every guard group named in the task has at least one negative control" therefore
does not extend to the spec's ordered-check requirement, the `lost` paths, or
`forecast`'s exclusion of `lost`.

## 4. Independent behavioural probes (not via the suite)

**Atomicity.** 1,500 random CRMs × 25 operations, mixing valid and invalid types
(`None`, `[]`, `{}`, `1.5`, `True`, unknown ids and actors): 13,353 calls raised and
**0** left `leads`, `opps`, `log`, `waiting`, `_lead_count` or `_opp_count` changed.
The "a failed call changes nothing" property holds beyond what `test_atomicity` checks.

**Queue invariant / `G:ASSIGN_TRANSFER`.** 3,000 random sessions × 40 operations:
**0** states had a non-empty waiting queue while any rep had spare capacity, 42
transfers succeeded, and **0** `("assign", …, "system")` entries were produced by a
transfer. This confirms the Executor's §6 disclosure: `_free_slot(previous)` in
`transfer` is unreachable through the public API, so no test or control can cover it.

**Ordered checks, current behaviour (all correct):**

```
advance(opp,'bogus',r2)   -> ValueError        (check 2 before 3)
convert(lead,0,'r2')      -> ValueError        (check 2 before 3)
discount(opp,0,'r2')      -> ValueError        (check 2 before 3)
transfer(opp,'ghost','r1')-> PermissionError   (check 2 before 3)
qualify(l1,'r2') on a qualified lead -> PermissionError (check 2 before 3)
add_lead(dup_email,'','nope','m1')   -> ValueError      (check 2 before 3/4)
```

**`lost` paths, current behaviour (correct):** advancing an opp to `lost` assigns the
queued lead to the freed rep and logs `("assign", lead, "system")`; `forecast()`
afterwards returns `{"open": 0, "weighted": 0, "won": 0}`.

**Argument types.** Unhashable arguments escape as `TypeError`, not the `ValueError`
the spec mandates:

```
add_lead(..., source=[], actor='m1')  -> TypeError: unhashable type: 'list'
add_lead(..., actor=[])               -> TypeError
qualify([], 'm1')                     -> TypeError
convert([], 100, 'm1')                -> TypeError
advance(opp, [], 'r1')                -> TypeError
transfer(opp, {}, 'm1')               -> TypeError
```

The spec says: invalid `source`, unknown lead/opp id, invalid `stage` and invalid
`new_owner` are `ValueError`; an unknown actor is `PermissionError`.

## 5. Findings

- **F-1 (contract defect, current).** Unhashable values for `actor`, `source`,
  `lead_id`, `opp_id`, `stage` and `new_owner` raise `TypeError` instead of the
  specified `ValueError`/`PermissionError` (probe in §4). The spec's type discipline
  is explicit for `email`, `name`, `amount` and `pct`; ids, `source` and `stage` are
  not type-checked before set/dict membership.
- **F-2 (coverage, high).** `advance(..., "lost")` freeing the slot is not tested;
  a `won`-only implementation passes all 30 tests (XC-12). This is a spec sentence
  with zero coverage.
- **F-3 (coverage, medium).** `forecast()` excluding `lost` is not tested; counting
  a lost opp as open passes all 30 tests (XC-09).
- **F-4 (coverage, high).** The ordered-check rule ("the first failing check decides
  the exception") is untested for every pair except unknown-actor-first: `advance`
  stage-name vs permission, `qualify`, `convert`, `discount`, `transfer`, and
  `add_lead` source vs duplicate (XC-07, XC-10, XC-11, XC-13, XC-14, XC-15).
- **F-5 (disclosed, accepted).** `# G:ASSIGN_TRANSFER` is unreachable dead code
  (XC-05). The compliance log states this and my fuzz agrees. The marker itself is
  uncontrolled; either delete the marker (keep the call) or guard the invariant.
- **F-6 (process).** The directory holds only `compliance-log.md` and
  `negcontrol-log.md`; `aepkit lint .` exits 2 with "missing execution-guide.md",
  so the protocol's drift check cannot run on this task.

**What holds.** The suite is green (30/30); all 21 logged controls reproduce exactly;
the file is restored byte-for-byte; every spec rule I exercised behaves correctly,
including atomicity on 13,353 raising calls and the FIFO/capacity invariants; the
one guard the suite cannot reach is disclosed rather than hidden.

## 6. Missing guard tests

Each item below was verified by a break that leaves the suite green, unless marked
"needs code fix". Test sketches are written against the existing fixtures
(`make_crm`, `qualified_opp`, `REPS`). I wrote and ran all nine sketches: they pass
on the current `crm.py` (9/9) and each one goes red under the matching break, so
they are sufficient to close the gap.

1. **`test_losing_frees_the_slot`** — spec: "If the new stage is `won` or `lost`, the
   owner's slot is freed". One-rep fixture cap 1, two leads (second queued), convert
   the first, `advance(opp, "lost", "r1")`, assert the queued lead's owner is `r1`
   and `crm.log[-1] == ("assign", l2, "system")`.
2. **`test_forecast_ignores_lost`** — convert one opp, `advance(opp, "lost", "r1")`,
   assert `forecast() == {"open": 0, "weighted": 0, "won": 0}`.
3. **`test_advance_stage_check_precedes_permission`** — `advance(opp, "bogus", "r2")`
   (r2 is a known rep, not the owner) must raise `ValueError`, not `PermissionError`.
4. **`test_qualify_check_order`** — qualify a lead, then `qualify(lead, "r2")` must
   raise `PermissionError` (permission before status), not `ValueError`.
5. **`test_convert_check_order`** — `convert(qualified_lead, 0, "r2")` must raise
   `ValueError` (amount before permission).
6. **`test_discount_check_order`** — `discount(opp, 0, "r2")` must raise `ValueError`
   (pct before permission).
7. **`test_transfer_check_order`** — `transfer(opp, "ghost", "r1")` must raise
   `PermissionError` (manager check before target validation).
8. **`test_add_lead_check_order`** — with an existing email: `add_lead(same_email,
   "", "web", "m1")` must raise `ValueError` (name before duplicate); and
   `add_lead(same_email, "Valid Name", "nope", "m1")` must raise `ValueError`
   (source before duplicate), not `DuplicateLeadError`. Both cases are needed — the
   first alone still passes if checks 3 and 4 are swapped.
9. **Unhashable arguments (needs code fix + test)** — check the type of `actor`,
   `source`, `stage`, `lead_id`, `opp_id` and `new_owner` before membership tests
   (`isinstance(x, str)` is enough for this spec), then assert `ValueError` for
   `source=[]`, `lead_id={}`, `stage=[]`, `new_owner={}`, and `PermissionError` for
   `actor=[]`.
10. **Missing negative controls for guards that already have tests** (no test change
    needed, just a control each): `convert` amount check (XC-01), `qualify` status
    check (XC-02), `discount` final-stage check (XC-03), `convert` owner check
    (XC-04), rep-only assignment (XC-06), and the `isinstance(email, str)` line.
11. **Direct assertion for the lowest-load rule** — `test_lowest_load_wins`: r1 carries
    one open opp (load 1), r2 carries nothing; the next lead must go to r2. XC-08 is
    currently caught only incidentally, by tests that assume `r1` is picked before
    `r2` for unrelated reasons.

## 7. Verdict

The implementation behaves correctly on every rule I could exercise, and the
Executor's 21 controls are honest and reproducible. It is nonetheless not ready to
close: nine spec-mandated protections — including the `lost` branch of slot freeing,
`forecast`'s exclusion of `lost`, and the entire ordered-check rule — can be removed
with a fully green suite, and unhashable arguments currently violate the specified
exception contract. Add the tests in §6 (and fix F-1), then re-run this audit.

**REJECTED**
