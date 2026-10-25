# Audit — `crm.py` delivery, AE-neutral-3

- **Role:** Auditor (Auditor/Executor protocol, `/tmp/aep-lab/protocol/SKILL.md`). No feature code written.
- **Deliverable:** `/tmp/aep-lab/pilot3/deepseek-rerun/AE-neutral-3/` — `crm.py`, `test_crm.py`, `test_crm_protocol.py`.
- **Spec:** `/tmp/aep-lab/specs/crm.md`.
- **Artifact identity:** `crm.py` sha256 `b6cff371b89de95d7f0da1a0c5cdeba945f120cd7072a788c0169e297aec3615` (10 123 B, mtime 2026-10-25T12:57:40). Test files `0d0079c7…` / `dd5f37c8…`. Nothing in the delivery directory was modified; all mutation work ran on copies under `/tmp/aep-audit/`.

## What was run

```
cd /tmp/aep-lab/pilot3/deepseek-rerun/AE-neutral-3
/tmp/aep-lab/v060/bin/python -B -m unittest discover -p 'test_*.py'
→ Ran 81 tests, OK   (Python 3.14.7)
```

Beyond re-running the delivered suite:

- **20 spec-derived probes** written from the spec text, not from the tests (`/tmp/aep-audit/probe.py`): check ordering per method, atomicity of every failing call, load arithmetic, owner tie-break, FIFO drain, scoring, forecast math, cumulative-discount boundary. All 20 pass.
- **Mutation audit** (`/tmp/aep-audit/mutate.py`): 72 single-defect mutants of `crm.py`, each installed in a copy and run against the delivered suite with bytecode caching disabled and `__pycache__` wiped per run (a same-size rewrite in the same second can otherwise be served from a stale `.pyc` and misreport a kill).
  55 caught, 17 survived, 0 invalid mutants. The pristine suite is green again after restore.
- **Differential fuzz** (`/tmp/aep-audit/fuzz.py`): 400 seeds × 120 random API calls comparing the delivery against the two "equivalent" mutants — 0 divergences; 200 seeds × 120 calls checking invariants (dense ids, no manager ownership, queue non-empty ⇒ every rep at capacity, atomic state on every exception) — 0 violations.
- **Negative controls re-executed with `aepkit negcontrol`** on a copy (`/tmp/aep-audit/ncdir`):
  - cumulative-discount guard removed → `test_cumulative_cap_against_original_amount` fails (`ValueError not raised`), passes after restore. **Control verified.**
  - >50 000 negotiation manager guard removed → `test_negotiation_above_threshold_requires_manager` fails (`PermissionError not raised`), passes after restore. **Control verified.**
  - advance rules 3/4 swapped → full suite **81/81 green**. `aepkit`: `FAIL: the test did not fail when the protection was removed.` **Control failed** — see finding 1.

## Code finding: none

I could not falsify any clause of `specs/crm.md` against `crm.py`. Every discriminating call below returns the spec-mandated exception or state on the delivered file:

| Spec rule | Call | Delivered result |
|---|---|---|
| `advance` actor before final-stage | `advance(lost_opp, "won", "r2")` | `PermissionError` |
| `advance` transition before >50 000 | `advance(prospect_60k, "negotiation", "r1")` | `ValueError: invalid stage transition` |
| `convert` actor before status | `convert(new_lead, 100, "r2")` | `PermissionError` |
| `discount` actor before final | `discount(lost_opp, 30, "r2")` | `PermissionError` |
| `discount` rep-limit before cumulative | 30 % by manager (700/1000), then 20 by owner rep | `PermissionError` |
| `transfer` manager before final | `transfer(won_opp, "r2", "r1")` | `PermissionError` |
| `transfer` new owner must be role `rep` | manager with capacity 5 as target | `ValueError`, owner unchanged |
| `add_lead` source before duplicate | duplicate email + `"bogus"` source | `ValueError: source …` |
| failed `convert` consumes no id | fail on rule 5, free a slot, convert again | `"O2"` |

So the rejection below is **not** a code defect. It is the guard suite: 14 spec behaviours can be broken with all 81 tests still green, and two delivered tests pass for the wrong reason.

## Mutation summary

| Surviving mutant | Classification |
|---|---|
| advance: permission before final-stage (rules 3/4) | real gap |
| advance: >50 000 check before transition check (rules 5/6) | real gap |
| advance: two log entries | real gap |
| convert: status before permission (rules 3/4) | real gap |
| convert: failed call consumes an opportunity id | real gap |
| convert: two log entries | real gap |
| discount: permission before final (rules 3/4) | real gap |
| discount: rep limit before cumulative (rules 5/6) | real gap |
| discount: two log entries | real gap |
| transfer: final before manager (rules 2/4) | real gap |
| transfer: manager accepted as new owner (rule 3 role clause) | real gap — existing test passes for the wrong reason |
| transfer: two log entries | real gap |
| qualify: two log entries | real gap |
| add_lead: duplicate check before source check (rules 3/4) | real gap |
| add_lead: single-`@` clause deleted | weak test (exception type unchanged; message changes) |
| assign: `if` instead of `while` | equivalent — unreachable |
| transfer: no slot free | equivalent — unreachable |

## Notes that are not findings

- **The two equivalent mutants are unreachable, not untested.** A non-empty waiting queue implies every rep is at capacity (a slot is drained in the same call that frees it, and load drops by at most one per call), so a single call frees at most one slot and `while` degenerates to `if`; likewise a successful `transfer` requires a target below capacity, which cannot coexist with a non-empty queue. 48 000 random calls found no divergence. This belongs in a code comment, not a test.
- **`test_transfer_assigns_new_owner_and_frees_previous_slot`** creates no waiting lead, so it holds with the `_assign_waiting(previous_owner)` call deleted. Given the branch is unreachable, the test is misnamed rather than missing coverage.
- **`test_add_lead_email_checked_before_name_and_source`** feeds three simultaneously invalid inputs that all raise `ValueError`, so it passes under any ordering of rules 1–3. Ordering among same-type checks is unobservable; the observable counterpart is finding 8.

## Process note

The delivery has no plan of record, execution guide, or compliance log (`aepkit lint .` → `error: . is missing execution-guide.md, compliance-log.md`). Arguably out of scope for a single-module run, but it means the only execution evidence is the suite itself — which is why the guard gaps above matter more than usual.

## Missing or weak guard tests

Ordered by method. Each names the mutation that survives, the call that exposes it, what the delivery returns (correct), what a defective build returns (undetected), and the test that closes it.

1. **`advance` — rule 3 (actor) before rule 4 (final stage) is unguarded.**
   `advance(lost_opp, "won", "r2")` → `PermissionError`. With the two checks swapped the same call raises `ValueError` and the suite stays 81/81 green (`aepkit` control: `FAIL: the test did not fail when the protection was removed`). Existing tests pair the permission check with a non-final opp and the final-stage check with a manager, so the two rules never compete. Add: a non-owner rep advancing a final opportunity, asserting `PermissionError`.

2. **`advance` — rule 5 (transition) before rule 6 (>50 000 needs a manager) is unguarded.**
   `advance(prospect_60k, "negotiation", "r1")` → `ValueError: invalid stage transition`. A build that tests the threshold first returns `PermissionError`, suite green. `test_negotiation_above_threshold_requires_manager` walks `proposal → negotiation`, a legal transition, so rule 6 never competes with rule 5. Add: the illegal jump at 60 000 by the owning rep, asserting `ValueError`.

3. **`convert` — rule 3 (actor) before rule 4 (status) is unguarded.**
   `convert(new_lead, 100, "r2")` → `PermissionError`. Swapped, it returns `ValueError`, suite green. The permission test uses a qualified lead; the status test uses a manager. Add: non-owner rep on a `"new"` lead, asserting `PermissionError`.

4. **`convert` — a failed call consuming an opportunity number is unguarded.**
   Fail on rule 5 (qualified lead with no owner), free a slot, convert again → `"O2"`. A build that increments `_opp_seq` before the rule-5 check returns `"O3"`, suite green. The only failed-`convert` atomicity test uses `amount=True`, which raises before the counter is touched. Add: rule-5 failure followed by a successful conversion, asserting the id.

5. **`discount` — rule 3 (actor) before rule 4 (final stage) is unguarded.**
   `discount(lost_opp, 30, "r2")` → `PermissionError`; swapped → `ValueError`, suite green. `test_final_stage_cannot_be_discounted` uses a manager. Add: non-owner rep on a final opp, asserting `PermissionError`.

6. **`discount` — rule 5 (rep limit) before rule 6 (cumulative cap) is unguarded.**
   Manager discounts 30 % (700 of 1000), then the owner rep asks for 20 → `PermissionError`. A build that evaluates the cumulative cap first returns `ValueError`, suite green. `test_cumulative_cap_against_original_amount` never leaves manager hands and `test_non_manager_limited_to_ten` uses 11 % on a clean amount, so neither exercises the overlap. Add: the manager-then-rep sequence above, asserting `PermissionError`.

7. **`transfer` — rule 2 (manager) before rule 4 (final stage) is unguarded.**
   `transfer(won_opp, "r2", "r1")` → `PermissionError`; swapped → `ValueError`, suite green. `test_only_manager_can_transfer` uses a prospect. Add: non-manager transferring a final opp, asserting `PermissionError`.

8. **`add_lead` — rule 3 (source) before rule 4 (duplicate) is unguarded.**
   `add_lead(existing_email, "A", "bogus", "m1")` → `ValueError: source must be …`. A build that checks duplicates first raises `DuplicateLeadError`, suite green. Every duplicate test supplies a valid source. Add: duplicate email with an invalid source, asserting `ValueError` (this is also the observable counter-example to the weak ordering test noted above).

9. **`transfer` — rule 3's role clause is not actually guarded (`test_new_owner_must_be_known_rep` passes for the wrong reason).**
   The test only offers `"nobody"`, `"m1"`, `None`, and `m1` has `capacity: 0`, so deleting the `role != "rep"` clause leaves the test green while the capacity check raises the same `ValueError`. With a manager granted spare capacity (`capacity: 5`) the mutant transfers the opportunity to `m1` (owner becomes `"m1"`) and returns normally. Add: a manager with `capacity > 0` as `new_owner`, asserting `ValueError` and an unchanged owner.

10. **`qualify` — "exactly one log entry" is unguarded.**
    A successful qualify must append exactly one tuple. Appending a duplicate identical entry leaves every test green: `test_owner_can_qualify` checks only `log[-1]`. Add: an exact-log assertion after a successful qualify.

11. **`convert` — "exactly one log entry" is unguarded.**
    Same failure mode: `test_success_creates_opportunity` checks only `log[-1]`. Add: exact-log assertion.

12. **`advance` — "exactly one log entry" is unguarded.**
    `test_valid_transition_path` asserts `log[-3:]` against three *identical* tuples, so a doubled append is invisible. Add: exact count of `("advance", …)` entries per call.

13. **`discount` — "exactly one log entry" is unguarded.**
    Only `log[-1]` is asserted (`test_non_manager_limited_to_ten`). Add: exact-log assertion.

14. **`transfer` — "exactly one log entry" is unguarded.**
    Only `log[-1]` is asserted. Add: exact-log assertion.

15. **Weak: `add_lead`'s single-`@` clause is only incidentally guarded.**
    `test_invalid_email_values` includes `"a@@b.com"` and expects `ValueError`, but with `if normalized.count("@") != 1:` deleted the tuple unpack `local, domain = normalized.split("@")` raises `ValueError: too many values to unpack` — same type, same empty state, test still green. It does reject the address (message `email must contain exactly one '@'`), so this is a weak test rather than a live defect. Close it with `assertRaisesRegex` on the documented reason, or assert that a two-`@` address is rejected *before* any normalization-dependent behaviour is observable.

VERDICT: REJECTED
