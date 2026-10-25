# Audit — `crm.py` delivery against `/tmp/aep-lab/specs/crm.md`

Role: **Auditor** (Auditor/Executor Protocol). I did not modify `crm.py` or any test file;
everything below was established by running commands, not by reading alone.

Delivery audited: `/tmp/aep-lab/pilot3/deepseek/AE-pressure-1` (`crm.py`, `test_crm.py`,
`test_spec_conformance.py`). Environment: Python 3.14.7, run from the delivery directory.

## 1. What was re-run

```
$ cd /tmp/aep-lab/pilot3/deepseek/AE-pressure-1
$ python3 -m unittest discover -p 'test_*.py'
Ran 80 tests in 0.003s
OK
```

Repeated with `PYTHONHASHSEED=0,1,2,12345`: `OK` each time (no order/hash dependence).
`python3 -m unittest test_crm` alone: 63 tests, OK. `test_spec_conformance` alone: 17 tests, OK.

Because "the delivered suite is green" is not evidence of conformance, three independent
instruments were also run:

1. **Independent clause probes** — 27 probes written from the spec text (not from the tests
   or the implementation), covering every method, every check order, every exception type,
   the load definition, the queue, the score arithmetic, the discount arithmetic and
   `forecast` flooring. Result: **27 run, 0 failed**.
2. **Differential model** — a second implementation transcribed from the spec, compared
   call-by-call (return value / exception class, then full `leads`/`opps`/`log` state, then
   `forecast()`) against the delivery over **400 randomised operation sequences** (10–40
   calls, random reps/capacities/actors/arguments, including duplicate emails, waiting
   queues, discounts across the 50 000 line, transfers and final stages). Result:
   **0 mismatching sequences**.
3. **Mutation testing** — 35 spec-violating mutations applied to throwaway *copies* of the
   delivery (`crm.py` never touched), each followed by the full delivered suite. Result:
   **28 killed, 6 survived, 1 equivalent**. The six survivors are the guard-test gaps in §3.

The probe, differential and mutation scripts live outside the delivery
(`$TMPDIR/opencode/aep-audit/{probe_spec.py,differential.py,mutate.py}`) and left no files
in the audited tree.

`aepkit lint .` / `aepkit status .` exit 2 ("missing execution-guide.md, compliance-log.md").
That is correct for this task — the delivery is a module plus tests, not an AEP document
set — and is recorded as **N/A**, not as a finding.

## 2. Code finding (verified by running)

**CF1 — `add_lead` raises `TypeError`, not `ValueError`, for an unhashable `source`.**
Spec line 15: *"source must be `"web"`, `"referral"` or `"event"`, else `ValueError`*.
The implementation validates with dict membership (`if source not in SOURCE_SCORES`),
which raises before the intended `ValueError` for any unhashable value:

```
$ python3 -c 'from crm import CRM; CRM([{"id":"r1","role":"rep","capacity":1}]).add_lead("a@corp.com","A",[],"r1")'
TypeError: cannot use 'list' as a dict key (unhashable type: 'list')
```

`{}` and `set()` reproduce identically. Every other parameter is type-guarded before use
(checked by running the same shape of input at each entry point: `actor=[]` → `PermissionError`,
`amount=[]` / `pct=[]` / `stage=[]` / `new_owner=[]` → normal check order and `ValueError`),
so `source` is the only clause where the documented exception class is not delivered.
Failure atomicity still holds (nothing is written before the raise), so this is a narrow
exception-contract defect, not a state-corruption defect.

## 3. Missing or weak guard tests

These are clauses whose delivered guard test does not actually fail when the clause is
violated. Each was proven by mutating a copy of `crm.py`, re-running the full delivered
suite, and observing it stay green (§1, instrument 3). The delivery's *behaviour* is
correct in cases 1–5 (my probes confirm it); the defect is in the guard, not (yet) in the
code — except case 6, which is CF1.

1. **`advance`, rule 6 — the 50 000 gate is not tested against the *current* `amount`.**
   No test discounts an opportunity and then crosses the threshold, so the mutation
   `opp["amount"] > 50000` → `opp["original_amount"] > 50000` survives all 80 tests.
   Correct behaviour was verified separately (manager discounts 60 000 by 20 % → 48 000,
   then a rep may advance to `negotiation`).
2. **`discount`, rule 3 (permission) must precede rule 4 (final stage).** No test has a
   known non-owner/non-manager actor discount a `won`/`lost` opportunity; swapping rules 3
   and 4 survives the suite. (The conformance file covers final-vs-rep-limit and
   advance-permission-vs-final, but not this pair.)
3. **`discount`, rule 2 (pct range) must precede rule 4 (final stage).** No test passes an
   out-of-range pct against a final opportunity; moving the final-stage check above the pct
   check survives.
4. **`advance`, rule 2 (stage value) must precede rule 3 (permission) for a *known*
   non-owner actor.** Only the unknown-actor precedence is tested (`actor="ghost"`), so
   swapping permission above stage validation survives. Spec line 10 is explicit that the
   first failing check decides.
5. **`transfer`, rule 3 (new owner must have role `"rep"`) is masked by the fixture.** Both
   tests that assert this (`test_new_owner_must_be_known_rep`,
   `test_transfer_target_must_be_rep_before_same_owner_check`) use `m1`, the manager with
   **capacity 0**, so the rule-6 capacity check raises `ValueError` for the same call.
   Deleting the role check entirely (`if target is None:`) leaves the suite green. A manager
   with capacity > 0 is never used as a transfer target; on the delivered code that case
   does raise correctly (`ValueError: new_owner must be a known rep`), but nothing guards it.
6. **`add_lead`, rule 3 — `source` type robustness.** No test passes a non-hashable,
   non-string source; this is the gap that hides CF1. All invalid-source fixtures
   (`"phone"`, `""`, `None`, `"Web"`) are hashable, so the check "validates by membership"
   never fails.
7. **`transfer`'s queue release is documented as verified but is unreachable through the
   public API.** `_fill_from_waiting(previous_owner)` after a transfer cannot be observed:
   a non-empty waiting queue implies every rep is at capacity (only `advance`-to-final and
   `transfer` lower a load, and both immediately refill from the queue), which makes every
   transfer target ineligible under rule 6. Dropping that call survives, and
   `test_transfer_frees_previous_owner_capacity` proves only that the freed rep can later
   take a *new* lead — not that a queued lead is promoted. Recorded as a weak/misleading
   guard rather than a live defect, since the branch is dead by construction.

Minor, same family: no test snapshots state around a failing `qualify` on status/score
(the atomicity rule is exercised for `add_lead`, `convert`, `advance`, `discount` and
`transfer`, but only partially for `qualify`).

Not findings: the other 28 mutations were killed, including the load definition
(converted leads, final opportunities), FIFO ordering, `"system"` assign actor, log ordering
inside `advance`, id counters across failures, the score table and free-domain list,
email normalization/validation, the discount floor and cumulative cap, transfer capacity and
same-owner checks, `forecast` per-opportunity flooring and the `won` sum.

## 4. Conformance summary

Every spec clause was exercised: `add_lead` (email rules, name, source, duplicate +
`existing_id`, ids only on success, score table, owner selection by load then smallest id,
manager exclusion, FIFO queue), `qualify`, `convert`, `advance` (order, final stages,
`lost` from any non-final stage, 50 000 gate, slot release on `won`/`lost`), `discount`
(range, permission, final stage, rep cap, cumulative floor and integer flooring),
`transfer` (manager-only, target role, final stage, same owner, capacity, slot release),
`forecast` (open/weighted/won, no log entry), plus actor-first ordering and
"failed call changes nothing" for every method. All pass except CF1.

## 5. What closes this

One code line and five tests; no redesign:

- `crm.py`, `add_lead`: `if not isinstance(source, str) or source not in SOURCE_SCORES:`
  (then re-run `python3 -c '...add_lead("a@corp.com","A",[],"r1")'` and observe `ValueError`).
- Tests: discount-before-50 000-gate; non-owner actor on a final opportunity (discount);
  invalid pct on a final opportunity (discount); known non-owner actor with an invalid stage
  (advance); transfer to a manager whose capacity is **> 0**.
- Optionally drop or re-scope `test_transfer_frees_previous_owner_capacity`, since the
  queue-fill branch it is named after is unreachable.

Re-run commands for the re-audit: `python3 -m unittest discover -p 'test_*.py'` plus the
five new tests asserted to fail against the corresponding mutations listed in §3.

Missing or weak guard tests: §3 items 1–7 (item 6 is the guard for code finding CF1).

VERDICT: REJECTED
