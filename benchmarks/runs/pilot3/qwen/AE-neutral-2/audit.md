# Audit — pilot3/qwen/AE-neutral-2 vs specs/crm.md

**Auditor:** AE Auditor (re-run based audit per auditor-executor-protocol SKILL.md §"Auditing").
**Date:** 2026-10-25. **Environment:** `/tmp/aep-lab/v060/bin/python` (CPython 3.14.7, `unittest`; no pytest in env — suite is unittest-based and runs with `python -m unittest discover`).
**Constraint honored:** `crm.py` and all test files were never edited in place. All mutations ran on a byte-identical copy in scratch (`/private/var/folders/.../opencode/audit-neutral2`); crm.py sha256 before and after: `0c8700d9...ba5868d` (delivery untouched).

## 1. Suite re-run (independent)

```
$ cd /tmp/aep-lab/pilot3/qwen/AE-neutral-2 && /tmp/aep-lab/v060/bin/python -m unittest discover
Ran 131 tests in 0.005s
OK
```
All 131 delivered tests pass. Read of every test file confirms they assert the spec's check-order rules, exception types, atomicity (snapshot equality after failed calls), log contracts, and routing/queue semantics — not generic smoke tests.

## 2. Negative controls (15, re-executed from scratch with `aepkit negcontrol`)

Each control removes one spec protection from the scratch copy; the suite must fail with the named test. Restores were verified byte-identical (`restored crm.py from backup (byte-identical)` in each transcript; full transcripts in scratch `controls.log`).

| # | Protection broken | Result |
|---|---|---|
| 1 | qualify: actor-checked-first removed | **caught** (3 errors) |
| 2 | convert: amount check moved after permission | **caught** (test_amount_check_runs_before_permission_check) |
| 3 | add_lead: duplicate check moved before source check | **caught** (test_source_check_runs_before_duplicate_check) |
| 4 | negotiation gate `> 50000` → `>= 50000` | **caught** (test_exactly_50000_allowed_for_rep) |
| 5 | discount cumulative `<` → `<=` (30% edge must pass) | **caught** (test_single_30_is_allowed…) |
| 6 | routing tie-break drops string-order (insertion order) | **caught** (test_ties_broken_by_string_order…) |
| 7 | assign goes to first rep instead of freed rep | **caught** (test_assign_goes_to_freed_rep…) |
| 8 | forecast counts lost as open | **caught** (test_lost_excluded_from_every_bucket) |
| 9 | discount mutates amount before cumulative check (atomicity) | **caught** (snapshot comparisons) |
| 10 | add_lead: `_lead_seq += 1` moved **before** duplicate check | **NOT CAUGHT — 131 tests still OK** |
| 11 | load includes "converted" leads | **caught** (10 failures) |
| 12 | advance: actor-checked-first removed | **caught** (4 errors) |
| 13 | duplicate check skips converted leads | **caught** (TestAtomicity sweep) |
| 14 | advance allows **backward** stage moves | **NOT CAUGHT — 131 tests still OK** |
| 15 | forecast `weighted` uses `original_amount` instead of current `amount` | **NOT CAUGHT — 131 tests still OK** (manual mutation run, restored byte-identical) |

12 of 15 protections are genuinely guarded. Controls 10, 14, 15 survived — see §4.

## 3. Auditor probes (load-bearing claims with no delivered guard)

Written per protocol audit rule 5 (probe asserts what the unguarded claim requires; deleted after — kept only in scratch), verified two ways: pass against pristine delivery, and fail against the matching mutant:

```
probe P1  duplicate/failed add_lead must not consume an L id  → OK pristine, FAIL vs control-10 mutant
probe P2  duplicate vs a converted lead's email raises         → OK pristine (behavior also guarded via #13)
probe P3  backward moves (proposal→prospect etc.) ValueError   → OK pristine, FAIL vs control-14 mutant
probe P4  rep qualifying an ownerless queued lead → PermissionError → OK pristine
probe P5  source check precedes duplicate check (non-str src)  → OK pristine
probe P6  open weighted after discount = current amount (7500→2250) → OK pristine, FAIL vs control-15 mutant
```

**Code verdict basis:** the delivered implementation itself is spec-correct on all three unguarded claims (probes prove the behavior is real, not the tests). No spec violation was found in `crm.py` by re-running or mutation.

## 4. Missing or weak guard tests

- **MISSING — lead-id counter across `DuplicateLeadError` (control 10).** Spec: "n counts **successful** lead creations." `test_ids_count_only_successful_creations` pins this for the ValueError and PermissionError paths only; a duplicate attempt consuming an id ships green. Guard to add: after a dup failure, the next successful `add_lead` still returns the next dense id (`L2`).
- **MISSING — backward stage moves (control 14).** Spec check 5 allows only `lost` or the immediate next stage. The suite tests forward skips and same-stage, but `proposal→prospect` / `negotiation→proposal` are untested; relaxing check 5 to permit backward moves survives the whole suite.
- **MISSING — `forecast` "weighted" on a discounted *open* opportunity (control 15).** Spec sums `amount * w // 100` over open opps; `amount` is the current (post-discount) value. Existing tests only pin the current-amount rule for the `won` bucket; a mutant weighting by `original_amount` passes all 131 tests.
- **WEAK — `test_final_check_before_target_checks` (transfer, check 4 vs 5).** Both checks raise `ValueError`, so the asserted ordering is observationally indistinguishable; swapping checks 4 and 5 passes the suite (verified by mutation). The test name claims to pin order it cannot pin.
- **WEAK — transfer's slot-freeing branch is pinned only whitebox.** `test_transfer_assign_branch_pinned_by_constructed_state` reaches into `c._users`/`c._reps`; the branch's public-API unreachability argument is correct (verified by analysis), but the ("transfer", …)→("assign", …) log ordering has no black-box anchor.
- **PROCESS — no document set shipped.** The delivery has no compliance log / execution guide / plan of record, yet `test_crm_add_lead.py:57` states an ambiguity decision was "logged in the compliance log." The log is not part of the delivery, so that record cannot be audited. Recommend delivering it alongside.

## 5. Process findings (separate from code findings, per protocol)

- Email domain rule is implemented under the **existential** literal reading ("contains a '.' that is neither first nor last" ⇒ `a@b.com.` valid). This is the spec's plain wording and is documented in-test; recorded as a resolved ambiguity rather than a defect.
- Executor reported no evidence artifacts (no pasted verify output in the folder); treated as evidence-free from the audit's side — hence this full independent re-run.

## Conclusion

The implementation passes independent re-run, survives 15 mutation attempts on all spec-critical rules checked (behavioral correctness), and auditor probes confirm the three behaviors the suite fails to guard are nonetheless correct as delivered. The gaps above are guard-test holes (regressions that could ship undetected), not present-tense spec violations. They should be closed with the four small tests named in §4; none of them falsifies the delivery.

VERDICT: APPROVED
