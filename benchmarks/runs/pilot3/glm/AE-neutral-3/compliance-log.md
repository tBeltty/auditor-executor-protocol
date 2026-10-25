# Compliance Log — AE-neutral-3 remediation

ROLE: Executor, reporting on the remediation ordered in `audit.md`
(VERDICT: REJECTED, 2026-10-25).

STATUS: DONE.

## Remediation actions (per audit.md "Remediation required")

### 1. Broken test fixed — `test_crm_forecast.test_lost_contributes_nothing_and_won_is_summed`

The test called `crm.advance(won1, "won", "r2")` while `won1` was still at
"prospect" (spec-illegal: advance check 5). It now uses the delivery's own
`walk_to_final` helper for both winners (`lost` still goes directly, which is
legal from any non-final stage). Coverage now actually asserts: lost
contributes nothing to open/weighted, and won sums amounts.

### 2. Broken test fixed — `test_crm_discount_transfer.test_transfer_leaves_no_assign_entry_when_queue_is_empty`

Expected log and comments corrected to the spec's lowest-load dispatch for
this fixture (L1 -> r1 on the load-0 tie; L2 -> r2, which holds load 0 while
r1 holds 1; L3 -> r1 on the load-1 tie):

```
['add_lead', 'add_lead', 'qualify', 'convert', 'add_lead', 'transfer']
```

The test's actual purpose (no "assign" entry when the queue is empty) is kept
and passes.

### 3-7. New guard file — `test_crm_check_ordering.py` (8 tests)

- Item 3: `AddLeadCheckOrderTests.test_source_check_fires_before_duplicate_check`
  — duplicate email + invalid source raises ValueError, not
  DuplicateLeadError.
- Item 4: `ConvertCheckOrderTests.test_existence_check_fires_before_amount_check`
  — `convert("L404", -5, "m1")` raises the unknown-lead ValueError atomically.
  Documented limitation: both checks raise ValueError, so their relative
  order is not observable by exception type (negative control: swapping the
  two checks in crm.py passes the suite). Mirrors the auditor's own note on
  item 9.
- Item 5: `AdvanceNegotiationGateTests.test_rep_may_advance_negotiation_to_won_above_50000`
  — check 6 gates only entering negotiation; the rep closes negotiation ->
  won alone.
- Item 6: `AdvanceNegotiationGateTests.test_negotiation_gate_uses_current_discounted_amount`
  — a 60000 opportunity discounted to 42000 lets a rep enter negotiation.
- Item 7: `DiscountCheckOrderTests.test_non_manager_cap_fires_before_cumulative_floor`
  — rep pct 11 on a floor-violating discount raises PermissionError, not
  ValueError; contrast shows the floor still bites at pct <= 10.
- Item 8: `TransferReachabilityTests.test_waiting_lead_implies_no_legal_transfer_target`
  — behavioral guard plus a documented unreachability argument: a lead only
  waits when every rep is at capacity, and slots free only inside
  advance-to-final / transfer, both of which drain the queue immediately, so
  "non-empty queue AND a legal transfer target" cannot exist.
- Item 9: `QualifyStatusVsScoreTests` — each branch of qualify's status vs
  score check exercised on its own trigger (ordering itself is unobservable
  by exception type).

## Negative controls (aepkit negcontrol, run this session; backup -> break -> test fails -> restore byte-identical -> test passes)

Each control targets one new guard in `test_crm_check_ordering.py`:

1. discount check order swapped (floor before 10-cap): `DiscountCheckOrderTests`
   fails with ValueError; restored byte-identical; passes. — guard 7 real.
2. negotiation gate reads `original_amount`: `AdvanceNegotiationGateTests`
   fails; restored byte-identical; passes. — guard 6 real.
3. negotiation gate extended to "won": `AdvanceNegotiationGateTests` fails;
   restored byte-identical; passes. — guard 5 real.
4. add_lead source check moved after the duplicate loop:
   `AddLeadCheckOrderTests` fails; restored byte-identical; passes. —
   guard 3 real.
5. transfer capacity check disabled: `TransferReachabilityTests` fails;
   restored byte-identical; passes. — item 8 guard real.

(Item 4's control produced the documented finding above: the 1<->2 swap in
convert is not observable by exception type.)

## Delivery gate

```
$ python3 -m unittest discover
Ran 83 tests in 0.002s
OK
```

```
$ python3 -m unittest discover -s /tmp/aep-lab/pilot3/glm/AE-neutral-3 -p "test*.py"
Ran 83 tests in 0.002s
OK
```

crm.py was not modified by this remediation (every negative control restored
byte-identical); only test files and this log changed.

## Deviations from the task text

None beyond what the remediation order itself specifies.

## Stops logged

None.
