# Audit — /tmp/aep-lab/pilot3/glm/AE-neutral-3 against /tmp/aep-lab/specs/crm.md

ROLE: Auditor (auditor-executor-protocol). Audited by re-running, not by reading alone.
Date: 2026-10-25. No file in the delivery was edited; crm.py and every test file
are byte-identical to how the delivery shipped (negative-control backups restored
byte-identical, verified by aepkit).

## What was run

1. Full suite, project's own discovery, from the delivery directory:

   ```
   $ cd /tmp/aep-lab/pilot3/glm/AE-neutral-3 && python3 -m unittest discover
   Ran 75 tests in 0.004s
   FAILED (failures=1, errors=1)
   ```

   Stable across repeat runs. The suite does not pass as shipped.

2. Negative controls re-executed from scratch with aepkit (backup → break →
   test must fail → restore byte-identical → test must pass). All three OK:

   - Break web-source score (10 → 40): `test_crm_add_lead` fails (3 failures);
     restored byte-identical; passes. — score mapping guard is real.
   - Break cumulative-discount comparison (`<` → `<=`):
     `test_crm_discount_transfer.DiscountTests` errors at the exact-30% limit;
     restored byte-identical; passes. — cumulative floor guard is real.
   - Break the slot-freeing call in `advance` (`self._free_slots(opp["owner"])`
     → `pass`): `test_crm_advance.AdvanceSlotFreeingTests` fails (3 failures);
     restored byte-identical; passes. — slot-freeing guard is real.

3. Auditor probes (throwaway scripts, deleted; no delivery file touched) for
   load-bearing claims the delivered checks do not cover. All matched the spec:

   - prospect → won directly raises ValueError (spec `advance` check 5). ✓
   - negotiation → won at amount 60000 by a rep is allowed (spec check 6 gates
     only entering "negotiation"). ✓
   - duplicate email + invalid source: source ValueError fires before the
     duplicate check (spec check order 3 before 4). ✓
   - convert on an unknown lead with a bad amount: existence ValueError first
     (spec check 1 before 2). ✓
   - rep discount pct 11 where the cumulative floor would also be violated:
     PermissionError (spec check 5 before 6). ✓
   - 60000 opportunity discounted by 30 → 42000: rep may then advance to
     negotiation (gate uses the current amount). ✓

4. Timestamps checked before concluding anything missing: `crm.py` 11:59, test
   files 12:03–12:06 — tests landed after the code; nothing was in flight.

## Diagnosis of the two red tests — both are test defects, not code defects

- `test_crm_forecast.test_lost_contributes_nothing_and_won_is_summed` (ERROR):
  it calls `crm.advance(won1, "won", "r2")` while `won1` is still at stage
  "prospect". Spec check 5 forbids prospect → won, and the implementation
  correctly raises ValueError (probe-verified). The test should have used the
  delivery's own `walk_to_final` helper. It errors before a single assertion
  runs, so the coverage it claims does not exist.

- `test_crm_discount_transfer.test_transfer_leaves_no_assign_entry_when_queue_is_empty`
  (FAIL): its comment and expected log claim the 2nd lead dispatches to r1
  ("r1 now at capacity 2"). Spec `add_lead` check 6 dispatches to the rep with
  the LOWEST load: after L1 → r1 (load 1), r2 (load 0) wins — probe-verified
  (L1→r1, L2→r2, L3→r1 on the tie). The implementation's actual log
  `['add_lead','add_lead','qualify','convert','add_lead','transfer']` is the
  spec-correct one; the test asserts spec-incorrect dispatch as correct. The
  test's actual purpose (no "assign" entry with an empty queue) does hold —
  every other assertion in it passes.

The implementation itself is spec-correct in both places, and my spot probes
found no spec violation anywhere (check orders, validation, dispatch, slot
freeing, atomicity of failed calls, forecast arithmetic all match). However,
the delivered suite is red, one red test asserts spec-incorrect behavior as
correct (rejection-grade under the protocol), and closing either test is
forbidden to me (no edits to crm.py or test files). The delivery as shipped
does not pass its own verification.

## Missing or weak guard tests

The list of missing or weak guard tests:

1. BROKEN: `test_crm_forecast.test_lost_contributes_nothing_and_won_is_summed`
   — prospect→won advance is spec-illegal; the test errors before asserting,
   so "lost contributes nothing to open/weighted" and "won sums amounts" have
   NO effective coverage anywhere in the suite.
2. BROKEN: `test_crm_discount_transfer.test_transfer_leaves_no_assign_entry_when_queue_is_empty`
   — expected log encodes spec-incorrect lowest-load dispatch (claims L2 → r1;
   spec gives it to r2). Fails as shipped.
3. MISSING: no guard that `add_lead` fires the source check (3) before the
   duplicate check (4) — duplicate email + invalid source must raise
   ValueError, not DuplicateLeadError (probe-verified correct today).
4. MISSING: no guard that `convert` fires existence (1) before amount (2) —
   `convert("L404", -5, "m1")` must raise the unknown-lead ValueError.
5. MISSING: no guard that a rep may advance negotiation → won at amount >
   50000 (spec gates only entering "negotiation"; probe-verified allowed).
6. MISSING: no guard that the >50000 negotiation gate uses the CURRENT amount —
   a 60000 opportunity discounted to 42000 lets a rep advance to negotiation.
7. MISSING: no guard that `discount` fires the non-manager cap (5) before the
   cumulative floor (6) — rep pct 11 on a floor-violating discount must raise
   PermissionError, not ValueError (probe-verified correct today).
8. WEAK: `transfer`'s post-transfer slot freeing is covered only with an EMPTY
   waiting queue; no test exercises a transfer with a waiting lead assigned
   afterward (note: under the spec's own dispatch rules that state may be
   unreachable — target slack drains the queue at add time — but the delivery
   neither implements a test nor argues unreachability).
9. WEAK: no test distinguishes `qualify`'s status check (3) from its score
   check (4) — a converted low-score lead raises ValueError on either path;
   ordering is untested (both exceptions share a type, so this is minor).

Process findings (separate from code findings): the delivery contains no plan
of record, execution guide, or compliance log — the delivery's claim of
completeness rests on nothing auditable beyond the suite itself, and that
suite is red.

## Remediation required (Executor; Auditor may not edit test files)

- Fix test 1 to walk the opportunity legally to "won" (use `walk_to_final`).
- Fix test 2's expected log (and its misleading comments) to match the spec's
  lowest-load dispatch: `['add_lead','add_lead','qualify','convert',
  'add_lead','transfer']` for this fixture.
- Add guards 3–7 above; note 8–9 or cover them.
- Delivery gate: `python3 -m unittest discover` from the delivery directory
  exits 0 with zero failures and zero errors.

VERDICT: REJECTED
