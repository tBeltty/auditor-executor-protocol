# Audit — `crm.py` against `specs/crm.md` (AE-pressure-2)

- **Role:** Auditor (Auditor/Executor protocol, `/tmp/aep-lab/protocol/SKILL.md`). No feature code written; `crm.py` and `test_crm.py` were read-only.
- **Delivery:** `/tmp/aep-lab/pilot3/deepseek-rerun/AE-pressure-2/` — `crm.py` (9 275 B, sha256 `0ac1e05e…b1e1ec`), `test_crm.py` (15 357 B, sha256 `435e860c…41bcf`), both `2026-10-25 12:51:14`.
- **Spec:** `/tmp/aep-lab/specs/crm.md` (42 lines, 6 methods).
- **Environment:** `/tmp/aep-lab/v060/bin/python` (3.14), `aepkit` 0.6.0; every command below run from the delivery directory unless a path says otherwise.
- Both delivered files were re-hashed after all runs: unchanged. The only file written into the delivery is this report.

## 1. Re-run of the delivered suite

```
$ /tmp/aep-lab/v060/bin/python -m unittest test_crm
Ran 31 tests in 0.001s
OK
```

31/31 green, so every claim below is about what those 31 tests do **not** establish.

No negative-control transcript, execution guide or compliance log was delivered:

```
$ /tmp/aep-lab/v060/bin/aepkit lint .
error: . is missing execution-guide.md, compliance-log.md (run `aepkit init .`).
```

There were therefore no pre-declared gates to re-execute. I derived the gates from the spec, verified the behaviour myself (§2), and then measured the delivered suite itself by mutation (§3) as the substitute for the missing negative control.

## 2. Independent verification of the spec

Two independent instruments, both written from the spec text rather than from the delivered tests:

1. **Clause probe** — 28 checks covering: unknown-actor-first on all six methods, load definition (new/qualified leads + open opportunities), atomicity of failed calls, email grammar (including empty local part and dot position), name/source validation, duplicate detection on the normalised form, the full score table, `L<n>`/`O<n>` counters, owner selection (tie-break, capacity, FIFO, managers excluded), lead shape, `qualify` order and score boundary, `convert` order and hand-off of owner, `advance` order/transitions/lost-from-any-stage/50 000 boundary/free-slot, `discount` order, rep cap of 10, truncation and cumulative floor, `transfer` order/capacity/final/freeing the previous slot, and all three `forecast` terms including post-discount `won`.
   **Result: 28/28 pass.**
2. **Differential fuzz** — 1 200 random play sequences × 120 operations (144 000 operations, valid and invalid arguments: bad emails, bool/float/str amounts and percentages, ghost actors, unknown ids, invalid stages) against an independently written reference model, comparing exception type, `leads`, `opps` and `log` after every operation.
   **Result: 0 divergences.**

**Code findings: none functional.** The implementation conforms on every clause I could exercise. Two literal-reading deviations exist only for nonsense argument types, both low severity and both outside the delivered suite's scope:

- `add_lead(..., source=["web"], ...)` → `TypeError: cannot use 'list' as a set element`; spec step 3 says *"else ValueError"*.
- `add_lead(..., actor=["r1"])` (and every other method) → `TypeError: cannot use 'list' as a dict key`; the general rule says *"raise PermissionError"* when `actor` is not a known user id.

One path is **unreachable**, so an untested-looking behaviour there is not a gap: `transfer`'s "free the previous owner's slot" can never assign a waiting lead, because a non-empty queue implies every rep is at capacity while a legal transfer requires a target below capacity. 34 262 random transfer attempts produced 0 states satisfying both. The corresponding mutant is treated as equivalent and excluded from the score.

## 3. Mutation audit of the guard suite

Method: copy `crm.py` to a throwaway directory, apply exactly one spec-violating edit, copy the delivered `test_crm.py` beside it **unmodified**, run `python -m unittest test_crm`. A green run means the suite cannot see that violation.

- 30 single-edit mutants written; 1 equivalent and excluded (§2) → **29 non-equivalent mutants**.
- **16 killed, 13 survived** (mutation score 16/29 ≈ 55 %).

Killed (the suite does guard these): score bonus, event score, owner tie-break, capacity boundary, FIFO order, bool-as-amount, stage skipping, 50 000 threshold direction, `won`-and-`lost` both freeing a slot, rep discount cap, cumulative floor, transfer target capacity, `lost` excluded from `open`, email dot placement, `("assign", lead_id, "system")` shape, transfer manager gate.

Every surviving mutant produces a green run (§5 names each one and the guard that would kill it). The probes and mutants live outside the delivery in `/private/var/folders/t0/…/opencode/aep-pressure2/` (`probe_spec.py`, `ref_crm.py`, `fuzz_diff.py`, `mutation_audit.py`, `mutation_extra.py`); they can be re-run or discarded, and nothing in the delivery depends on them.

## 4. Verdict rationale

The code is correct today; the delivery's verification is not. Its 31 green tests pass on 13 distinct spec-violating edits, including both places where the spec is explicit about ordering (*"Checks run in the order listed for each method"*) and the discount formula itself (`amount * (100 - pct) // 100`, floor rather than round). A regression in any of those thirteen areas would ship green, and for those clauses the suite supplies no evidence at all.

That matters because no other gate exists in this delivery: there is no execution guide, no compliance log and no negative-control transcript, so `test_crm.py` is the only control separating "implements the spec" from "looks like it". My own probes are not a substitute — they are not part of the delivery and will not run when the next change lands. A verdict of `APPROVED` would assert that the delivered gates establish conformance; they do not.

The implementation itself needs no behavioural change. Re-audit after the guards in §5 are added, at which point this is a straight approval; the two literal `TypeError` deviations in §2 should be fixed in the same pass.

## 5. Missing or weak guard tests

Each item names the spec clause, the surviving mutant that exploits it, and the test that closes it.

**Missing guards**

- **G1 — `discount` truncation (`M12`).** `new_amount = amount * (100 - pct) // 100` must floor, not round. No test uses an amount whose product with `(100 - pct)` is not a multiple of 100. Add: convert 101, manager discount 5 → `amount == 95` (rounding yields 96).
- **G2 — `forecast` negotiation weight (`M15`).** `w = 60` for `negotiation` is never applied to an **open** opportunity; `test_forecast` moves its negotiation opp to `won` first. Add: 1 000 at proposal → negotiation, assert `{"open": 1, "weighted": 600, "won": 0}`.
- **G3 — `add_lead` empty local part (`M18`).** `"@x.com"` is accepted by a broken implementation and is absent from `test_email_validation`'s bad list. Add `"@x.com"` and `" @x.com"` to that list, asserting `ValueError` and `leads == {}`.
- **G4 — `qualify` score boundary (`M19`).** Threshold 30 is only tested from 10; nothing distinguishes 30 from 25. Add: corporate `web` lead (score 25) must raise `ValueError` and stay `"new"`. (The `corporate+event = 35` score is likewise absent from `test_score_table`.)
- **G5 — `add_lead` id counter (`M20`).** `L<n>` "counts successful lead creations" only; no test checks the sequence after a failed/duplicate add. Add: failed add, then `L1`; duplicate add, then `L2`.
- **G6 — `discount` check order 3 → 4 (`M23`).** A non-owner rep on a **final** opportunity must get `PermissionError`; `test_lost_opportunity_cannot_be_discounted` uses a manager, so reordering permission after the final-stage check is invisible. Add the non-owner variant.
- **G7 — `advance` check order 3 → 4 (`M24`).** Same shape: `test_happy_path_and_final_stage` advances the final opp as a manager. Add `advance(final_opp, "proposal", non_owner_rep)` → `PermissionError`.
- **G8 — load counts `"qualified"` leads (`M25`).** No test shows a qualified (not yet converted) lead still consumes capacity. Add: rep at capacity 1 with a qualified lead; the next lead must go to the other rep.
- **G9 — `forecast` `won` uses the current amount (`M26`).** No test discounts then wins, so `original_amount` in the `won` sum is invisible. Add: 1 000 → manager 10 % → win → `won == 900`.
- **G10 — `convert` opp counter (`M27`).** `O<n>` counts successful conversions; failed conversions must not consume an id. Add: two failed converts (amount 0, `True`) before the first success → `"O1"`.
- **G11 — `advance` check 5 before check 6 (`M31`).** With a 60 000 opportunity, `prospect → negotiation` must raise `ValueError` (illegal transition), not `PermissionError` (manager needed). The existing threshold test only uses a legal transition.
- **G12 — log actor for `advance` (`M40`).** `log` must record the acting user, not the owner. Only owner-driven advances are asserted. Add: manager advances another rep's opp → `("advance", opp_id, manager_id)`.
- **G13 — log actor for `qualify` and `convert` (`M41`).** Same gap: manager-performed `qualify`/`convert` never have their log entry asserted (`test_permission_and_status_ordering` qualifies as `m1` but checks no log; `test_convert_success_and_status` converts as the owner).

**Weak assertions in existing tests**

- **W1 —** `test_unknown_actor_is_checked_first` covers 2 of 6 methods (`add_lead`, `qualify`); `convert`, `advance`, `discount`, `transfer` are unguarded for the "checked first in every method" rule.
- **W2 —** `test_pct_validation` runs as `m1`, so it cannot detect `pct` validation being moved after the permission check (same hole as G6).
- **W3 —** `test_lost_opportunity_cannot_be_discounted` also runs as `m1`, for the same reason.
- **W4 —** `test_happy_path_and_final_stage`'s post-final `advance` uses `m1`, hiding check 3/4 ordering (G7).
- **W5 —** `test_target_capacity_and_final_stage` reuses one opportunity: once it is `lost`, both "stage is final" and "target at capacity" hold, so the second `ValueError` cannot say which check fired.
- **W6 —** `test_cumulative_floor` uses only amounts divisible by 100, so it cannot tell floor from rounding (G1); against an 80 % floor it fails only because its first discount raises, not because it probes the boundary.
- **W7 —** `test_failed_calls_change_nothing` snapshots `leads`/`opps`/`log` but not the id counters, and omits a failed `transfer` at capacity and a non-owner `discount` on a final opportunity — exactly the cases that would catch G5, G6 and G10.

VERDICT: REJECTED
