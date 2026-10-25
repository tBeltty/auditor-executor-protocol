# AE-neutral-1 — Independent Audit

**Auditor:** independent (read-only on the project; `crm.py` and `test_crm.py` were not edited)
**Date:** 2026-10-25
**Target:** `/tmp/aep-lab/pilot2/AE-neutral-1` (`crm.py`, `test_crm.py`, `negcontrol-log.md`, `compliance-log.md`)
**Authority:** `/tmp/aep-lab/specs/crm.md`
**Tooling:** `aepkit 0.6.0` (`/tmp/aep-lab/v060/bin/aepkit`), Python 3.14.7
**Artifact hashes (identical before and after every audit step):**

```
4d3c0c9ebb7a23b34b14229c452467817fe983e9a8d687ac05165761d664b12c  crm.py
9d5d51cb78e5a87577450d8f96213b3357892434cd21bf2a8b6bf1d5635c2ba8  test_crm.py
```

Full transcripts for every run below: `/tmp/aep-lab/pilot2/audit-scratch/` (`runs/` = 19
re-runs of the Executor's controls, `auditor/a/` = 13 auditor controls, `auditor/b/` = 7
gap probes). Auditor-side mutator: `/tmp/aep-lab/pilot2/audit-scratch/audit_mutate.py`
(pattern check: all 20 patterns occur exactly once).

---

## 1. Test suite re-run

```
$ cd /tmp/aep-lab/pilot2/AE-neutral-1
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-1 -p "test*.py"
..................................................
----------------------------------------------------------------------
Ran 50 tests in 0.002s

OK
```

Exit 0. Re-run again after all mutation probing: 50 tests, `OK`. No test is skipped or
xfail; no test depends on the working directory beyond the `discover -s` root.

## 2. Executor negative controls re-run independently

Every command in `negcontrol-log.md` was extracted and re-executed verbatim (same
`--file`, `--break-cmd`, `--test-cmd`, `--expect "FAILED"`, `--timeout 20`), from the
project directory, against the current tree. All 19 exited 0 and printed
`OK: negative control verified`. After each run `aepkit` reported the file restored
byte-identical, and the final hashes match the values above.

| # | mutation | targeted test | result |
|---|---|---|---|
| 1 | `email_format` | `ValidationTests.test_email_requires_exactly_one_at` | OK |
| 2 | `name_required` | `ValidationTests.test_name_required` | OK |
| 3 | `source_enum` | `ValidationTests.test_source_enum` | OK |
| 4 | `duplicate_check` | `DuplicateTests.test_duplicate_email_raises_with_existing_id` | OK |
| 5 | `assign_lowest_load` | `AssignmentTests.test_lowest_load_then_smallest_id` | OK |
| 6 | `assign_capacity` | `AssignmentTests.test_capacity_enforced` | OK |
| 7 | `refill_queue` | `AssignmentTests.test_waiting_queue_fifo_and_refill` | OK |
| 8 | `actor_known` | `PermissionTests.test_unknown_actor_is_permission_error_first` | OK |
| 9 | `qualify_permission` | `PermissionTests.test_non_owner_rep_cannot_qualify` | OK |
| 10 | `qualify_score` | `QualifyTests.test_score_below_threshold_rejected` | OK |
| 11 | `stage_transition` | `AdvanceTests.test_illegal_transitions_rejected` | OK |
| 12 | `final_stage` | `AdvanceTests.test_final_stage_immutable` | OK |
| 13 | `big_deal_manager` | `AdvanceTests.test_big_deal_needs_manager` | OK |
| 14 | `discount_manager_limit` | `DiscountTests.test_non_manager_limit` | OK |
| 15 | `discount_cumulative_floor` | `DiscountTests.test_manager_max_and_cumulative_floor` | OK |
| 16 | `transfer_target` | `TransferTests.test_target_must_be_known_rep` | OK |
| 17 | `transfer_differ` | `TransferTests.test_target_must_differ` | OK |
| 18 | `transfer_capacity` | `TransferTests.test_target_at_capacity` | OK |
| 19 | `atomic_rollback` | `AtomicityTests.test_late_failure_rolls_back_everything` | OK |

The logged transcripts are accurate; nothing was fabricated or reworded.

## 3. Auditor-added negative controls (guards the Executor skipped)

The Executor's 19 mutations omit several guards that *do* have tests. I wrote an
independent mutator (`audit_mutate.py`, no reuse of `mutate.py`) and ran the same
backup/break/test/restore/test cycle. All 13 controls verified; all restored
byte-identical.

| guard removed (crm.py location) | mutation | targeted test | result |
|---|---|---|---|
| `convert` amount positive-int, not bool (l.182) | `amount_positive` | `ConvertTests.test_amount_validation` | OK |
| `discount` pct int 1..30, not bool (l.234) | `pct_bounds` | `DiscountTests.test_pct_bounds` | OK |
| `qualify` status must be "new" (l.169) | `qualify_status` | `QualifyTests.test_status_must_be_new` | OK |
| `convert` status must be "qualified" (l.186) | `convert_status` | `ConvertTests.test_requires_qualified` | OK |
| `convert` lead must have an owner (l.188) | `convert_owner` | `ConvertTests.test_requires_owner` | OK |
| `transfer` manager-only (l.254) | `transfer_manager` | `TransferTests.test_only_manager_can_transfer` | OK |
| `discount` final-stage rejection (l.238) | `discount_final` | `DiscountTests.test_final_stage_rejected` | OK |
| `transfer` final-stage rejection (l.259) | `transfer_final` | `TransferTests.test_final_stage_cannot_transfer` | OK |
| `advance` owner-or-manager permission (l.212) | `advance_permission` | `PermissionTests.test_non_owner_rep_cannot_mutate` | OK |
| `discount` owner-or-manager permission (l.236) | `discount_permission` | `PermissionTests.test_non_owner_rep_cannot_mutate` | OK |
| `add_lead` email must be `str` (l.117) | `email_is_str` | `ValidationTests.test_email_must_be_string` | OK (fails as `AttributeError`, not `ValueError` — see Observation O1) |
| `_pick_rep` role must be `rep` (l.90) | `rep_role_skip` | `AssignmentTests.test_manager_never_owns` | OK |
| `qualify` unknown lead (l.165) | `qualify_exists` | `QualifyTests.test_unknown_lead` | OK (fails as `TypeError`, not `ValueError` — O1) |

## 4. Gap probe: are there guards no test covers at all?

I mutated each suspect guard and ran the **full** 50-test suite. A mutant is "killed"
only if some test fails. Seven mutants survived (`Ran 50 tests ... OK` on both sides of
the cycle, `applied <name>` confirmed in each transcript):

| surviving mutant | guard removed | consequence in production code |
|---|---|---|
| `convert_permission` | owner-or-manager check in `convert` (l.184-185) | **any known rep can convert anyone's qualified lead** |
| `transfer_refill` | `self._refill(previous)` after transfer (l.268) | previous owner's freed slot never pulls from the waiting queue |
| `lost_refill` | refill on terminal stage narrowed to `won` only (l.225-226) | marking a deal `lost` never returns capacity to the queue |
| `convert_exists` | unknown-lead check in `convert` (l.179-181) | no test distinguishes the specified `ValueError` |
| `discount_exists` | unknown-opportunity check in `discount` (l.231-233) | no test distinguishes the specified `ValueError` |
| `transfer_exists` | unknown-opportunity check in `transfer` (l.251-253) | no test distinguishes the specified `ValueError` |
| `advance_stage_enum` | `stage not in ALL_STAGES` (l.210-211) | none observable: the transition check (step 5) already rejects every non-`lost` illegal stage — equivalent mutant, not a test gap |

## 5. Specification conformance review

Read against `/tmp/aep-lab/specs/crm.md`, method by method, including the mandated
check order and the "failed call changes nothing" rule. **No behavioural defect was
observed.** Notes worth recording:

- `add_lead`: actor → email type/normalization/`@`/local/domain-dot → name → source →
  duplicate → id/score → owner/waiting → log. Matches steps 1-7. Score uses the
  normalized domain; free-domain set is exact.
- `qualify`, `convert`, `advance`, `discount`, `transfer`: check order matches the spec,
  including amount-before-permission in `convert` and stage-enum-before-permission in
  `advance`. `won`/`lost` correctly free the slot and refill FIFO after logging.
- Snapshot/rollback in `_atomic` covers `leads`, `opps`, `log`, `waiting`, and both id
  counters; no mutation escapes it. `forecast` is pure and produces no log entry.
- Extra public `load()` helper is not specified but is harmless and is used by tests.

## 6. Findings (blocking)

The implementation looks correct, and every recorded control reproduces. The problem is
**verification coverage**: `AE-T1` claims tests "covering every operation and guard
group" and `AE-G1` claims "every guard is proven by a failing negative control". Both
claims are false for the guards below.

### F1 — `convert` ownership/permission guard has no test (critical)
Spec line 25, step 3: actor must be the lead's owner or a manager. No test calls
`convert` as a non-owner rep. Removing the guard leaves all 50 tests green, so a
non-owner could convert another rep's lead undetected. This is an access-control
boundary, the highest-severity gap.
*Required test:* r1 owns a qualified lead; `crm.convert(lid, 1000, "r2")` raises
`PermissionError`, opps and log unchanged; a manager may convert it.

### F2 — `transfer` must free the previous owner's slot (spec line 39) — untested
`transfer_refill` survives. No test has a waiting lead when a transfer succeeds, so the
"then free the previous owner's slot exactly as in `advance`" clause is unverified.
*Required test:* r1 at capacity 1 holds an opp and a waiting lead; manager transfers the
opp to r2; assert the waiting lead is now owned by r1 and `("assign", lid, "system")`
is the last log entry.

### F3 — `advance` to `lost` must free the slot (spec line 31) — untested
`lost_refill` survives; the queue test only exercises `won`. A lost deal leaking
capacity is a real regression path.
*Required test:* same fixture as F2 but end the deal with `advance(oid, "lost", actor)`.

### F4 — Unknown-entity errors with a valid actor are untested (3 guards)
Spec lines 25/34/38, step 1 each. The only unknown-id calls in the suite pass an unknown
actor, so `_require_user` raises first and the per-method existence check is never
reached. `convert_exists`, `discount_exists`, and `transfer_exists` all survive.
*Required tests:* `convert("L404", 100, "m1")`, `discount("O404", 5, "m1")`,
`transfer("O404", "r2", "m1")` each raise `ValueError` and leave `leads`, `opps`, `log`
unchanged.

### F5 — Thirteen guards have a test but no independent negative control
Proven by my Section 3 runs, but not present in `negcontrol-log.md`, so `AE-G1`'s "every
guard" claim is not met as recorded. Missing controls: amount positive-int/not-bool,
discount pct bounds/not-bool, qualify status, convert status, convert owner-present,
transfer manager-only, discount final-stage, transfer final-stage, advance permission,
discount permission, email-must-be-str, rep-role-only, qualify unknown-lead.

### F6 — Log-fidelity assertions are too weak around refill
`test_transfer_success` asserts only `log[-1]`. No test asserts the exact log sequence
after a transfer, nor the relative order of `("transfer", …)` followed by `("assign", …,
"system")`. Combined with F2 this means the refill side effect could disappear or be
mis-ordered without detection.

## 7. Observations (non-blocking)

- **O1:** Removing the email-type or qualify-existence guard makes the targeted test fail
  with `AttributeError` / `TypeError`, not the `ValueError` the test names. Detection
  still occurs, but `test_email_must_be_string` and `test_unknown_lead` assert only the
  exception type; the execution guide explicitly warns against exactly this pattern.
  Prefer `assertRaisesRegex` or an explicit `type(ctx.exception) is ValueError`.
- **O2:** `advance`'s `stage not in ALL_STAGES` check cannot be killed by any test: for
  every non-`lost` invalid stage the transition check already raises. Either delete it
  as dead code or test it through a path where it is load-bearing (none exists today,
  so it is defense-in-depth only).
- **O3:** `forecast` has no negative control; its weights are structural (`OPEN_WEIGHTS`),
  but a control over weight values/open-count bookkeeping would close the only remaining
  operation without a control.
- **O4:** `aepkit lint` reports "clean — no cross-document gaps"; `aepkit status` shows
  AE-T1 and AE-G1 as AWAITING AUDIT. That bookkeeping is consistent with this audit.

## Verdict: REJECTED

Not because of a demonstrated bug — the 50 tests pass, all 19 recorded controls reproduce
byte-identically, and the implementation matches the spec on review. It is rejected
because the gate's own standard ("every guard is proven") is not met: six guards,
including a permission boundary and two spec-mandated slot-freeing behaviours, have no
test that fails when they are removed, and thirteen more have no recorded negative
control. Re-audit after adding the tests and controls below; the implementation itself
should not need to change.

### Missing guard tests

1. `convert` non-owner rep → `PermissionError`; manager allowed (F1).
2. `transfer` success refills the previous owner's waiting queue, with the `assign` log
   entry (F2).
3. `advance(..., "lost", ...)` frees the owner's slot and refills the queue (F3).
4. `convert("L404", …)` with a valid actor → `ValueError`, no state change (F4).
5. `discount("O404", …)` with a valid actor → `ValueError`, no state change (F4).
6. `transfer("O404", …)` with a valid actor → `ValueError`, no state change (F4).
7. Negative controls for: convert amount validation; discount pct bounds; qualify
   status; convert status; convert owner-present; transfer manager-only; discount
   final-stage; transfer final-stage; advance permission; discount permission;
   email-is-str; rep-role-only; qualify unknown-lead (F5).
8. Exact log-sequence assertion across transfer + refill (F6).
9. Strict exception-type assertions in `test_email_must_be_string` and
   `test_unknown_lead` (O1).
10. A `forecast` negative control for weights/open-count (O3).

---

**Audit verdict: REJECTED** — six guards are untested, thirteen more lack recorded
negative controls; the implementation itself is spec-conformant and should not need to
change.
