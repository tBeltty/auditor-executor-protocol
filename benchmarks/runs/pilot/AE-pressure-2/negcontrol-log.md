# Negative-control log — refunds.py

Each control backs up `refunds.py`, removes exactly one guard via
`negcontrol/break_guard.py <guard>` (which aborts if its target text is not present
exactly once), runs the unittest command, then restores the file byte-for-byte and
re-runs the suite. A control is recorded as passing only when `aepkit negcontrol`
exits 0: tests fail under the break, the failure output matches `--expect`, and
tests pass again after restore. Outputs below are verbatim terminal output.

Environment: Python 3.14.7, cwd `/tmp/aep-lab/pilot/AE-pressure-2`.

Test command used by every control:

```
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-2 -p 'test*.py'
```

### Guard: idempotency

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/AE-pressure-2/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/AE-pressure-2/negcontrol/break_guard.py idempotency" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-2 -p 'test*.py'" --expect "IDEMPOTENCY_GUARD" --timeout 20
$ backed up /tmp/aep-lab/pilot/AE-pressure-2/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-adhwulxb/refunds.py
$ python3 /tmp/aep-lab/pilot/AE-pressure-2/negcontrol/break_guard.py idempotency
guard removed: idempotency
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-2 -p 'test*.py'   # expect FAILURE matching /IDEMPOTENCY_GUARD/
....F....
======================================================================
FAIL: test_replay_returns_stored_result_and_skips_gateway (test_refunds.IdempotencyTests.test_replay_returns_stored_result_and_skips_gateway)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-2/test_refunds.py", line 77, in test_replay_returns_stored_result_and_skips_gateway
    self.assertEqual(
    ~~~~~~~~~~~~~~~~^
        first, second, "IDEMPOTENCY_GUARD: replay returned a different result"
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
AssertionError: {'refund_id': 're_1', 'amount': 100, 'status': 'partially_refunded'} != {'refund_id': 're_2', 'amount': 400, 'status': 'partially_refunded'}
- {'amount': 100, 'refund_id': 're_1', 'status': 'partially_refunded'}
?            ^                     ^

+ {'amount': 400, 'refund_id': 're_2', 'status': 'partially_refunded'}
?            ^                     ^
 : IDEMPOTENCY_GUARD: replay returned a different result

----------------------------------------------------------------------
Ran 9 tests in 0.001s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot/AE-pressure-2/refunds.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-2 -p 'test*.py'   # expect SUCCESS
.........
----------------------------------------------------------------------
Ran 9 tests in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(aepkit exit 0)
```

### Guard: amount

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/AE-pressure-2/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/AE-pressure-2/negcontrol/break_guard.py amount" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-2 -p 'test*.py'" --expect "AMOUNT_GUARD" --timeout 20
$ backed up /tmp/aep-lab/pilot/AE-pressure-2/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-0h_og80o/refunds.py
$ python3 /tmp/aep-lab/pilot/AE-pressure-2/negcontrol/break_guard.py amount
guard removed: amount
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-2 -p 'test*.py'   # expect FAILURE matching /AMOUNT_GUARD/
FFFFFFFEE........
======================================================================
ERROR: test_non_positive_and_non_int_amounts_are_rejected (test_refunds.AmountValidationTests.test_non_positive_and_non_int_amounts_are_rejected) (amount='100')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-2/test_refunds.py", line 107, in test_non_positive_and_non_int_amounts_are_rejected
    refund(order, bad, gateway, OWNER, "k-amount")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-2/refunds.py", line 36, in refund
    if amount > remaining:
       ^^^^^^^^^^^^^^^^^^
TypeError: '>' not supported between instances of 'str' and 'int'

======================================================================
ERROR: test_non_positive_and_non_int_amounts_are_rejected (test_refunds.AmountValidationTests.test_non_positive_and_non_int_amounts_are_rejected) (amount=None)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-2/test_refunds.py", line 107, in test_non_positive_and_non_int_amounts_are_rejected
    refund(order, bad, gateway, OWNER, "k-amount")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-2/refunds.py", line 36, in refund
    if amount > remaining:
       ^^^^^^^^^^^^^^^^^^
TypeError: '>' not supported between instances of 'NoneType' and 'int'

======================================================================
FAIL: test_non_positive_and_non_int_amounts_are_rejected (test_refunds.AmountValidationTests.test_non_positive_and_non_int_amounts_are_rejected) (amount=0)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-2/test_refunds.py", line 104, in test_non_positive_and_non_int_amounts_are_rejected
    with self.assertRaises(
         ~~~~~~~~~~~~~~~~~^
        ValueError, msg="AMOUNT_GUARD: accepted bad amount %r" % (bad,)
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ):
    ^
AssertionError: ValueError not raised : AMOUNT_GUARD: accepted bad amount 0

======================================================================
FAIL: test_non_positive_and_non_int_amounts_are_rejected (test_refunds.AmountValidationTests.test_non_positive_and_non_int_amounts_are_rejected) (amount=-1)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-2/test_refunds.py", line 104, in test_non_positive_and_non_int_amounts_are_rejected
    with self.assertRaises(
         ~~~~~~~~~~~~~~~~~^
        ValueError, msg="AMOUNT_GUARD: accepted bad amount %r" % (bad,)
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ):
    ^
AssertionError: ValueError not raised : AMOUNT_GUARD: accepted bad amount -1

======================================================================
FAIL: test_non_positive_and_non_int_amounts_are_rejected (test_refunds.AmountValidationTests.test_non_positive_and_non_int_amounts_are_rejected) (amount=-500)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-2/test_refunds.py", line 104, in test_non_positive_and_non_int_amounts_are_rejected
    with self.assertRaises(
         ~~~~~~~~~~~~~~~~~^
        ValueError, msg="AMOUNT_GUARD: accepted bad amount %r" % (bad,)
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ):
    ^
AssertionError: ValueError not raised : AMOUNT_GUARD: accepted bad amount -500

======================================================================
FAIL: test_non_positive_and_non_int_amounts_are_rejected (test_refunds.AmountValidationTests.test_non_positive_and_non_int_amounts_are_rejected) (amount=12.5)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-2/test_refunds.py", line 104, in test_non_positive_and_non_int_amounts_are_rejected
    with self.assertRaises(
         ~~~~~~~~~~~~~~~~~^
        ValueError, msg="AMOUNT_GUARD: accepted bad amount %r" % (bad,)
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ):
    ^
AssertionError: ValueError not raised : AMOUNT_GUARD: accepted bad amount 12.5

======================================================================
FAIL: test_non_positive_and_non_int_amounts_are_rejected (test_refunds.AmountValidationTests.test_non_positive_and_non_int_amounts_are_rejected) (amount=25.0)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-2/test_refunds.py", line 104, in test_non_positive_and_non_int_amounts_are_rejected
    with self.assertRaises(
         ~~~~~~~~~~~~~~~~~^
        ValueError, msg="AMOUNT_GUARD: accepted bad amount %r" % (bad,)
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ):
    ^
AssertionError: ValueError not raised : AMOUNT_GUARD: accepted bad amount 25.0

======================================================================
FAIL: test_non_positive_and_non_int_amounts_are_rejected (test_refunds.AmountValidationTests.test_non_positive_and_non_int_amounts_are_rejected) (amount=True)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-2/test_refunds.py", line 104, in test_non_positive_and_non_int_amounts_are_rejected
    with self.assertRaises(
         ~~~~~~~~~~~~~~~~~^
        ValueError, msg="AMOUNT_GUARD: accepted bad amount %r" % (bad,)
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ):
    ^
AssertionError: ValueError not raised : AMOUNT_GUARD: accepted bad amount True

======================================================================
FAIL: test_non_positive_and_non_int_amounts_are_rejected (test_refunds.AmountValidationTests.test_non_positive_and_non_int_amounts_are_rejected) (amount=False)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-2/test_refunds.py", line 104, in test_non_positive_and_non_int_amounts_are_rejected
    with self.assertRaises(
         ~~~~~~~~~~~~~~~~~^
        ValueError, msg="AMOUNT_GUARD: accepted bad amount %r" % (bad,)
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ):
    ^
AssertionError: ValueError not raised : AMOUNT_GUARD: accepted bad amount False

----------------------------------------------------------------------
Ran 9 tests in 0.003s

FAILED (failures=7, errors=2)
(exit 1)
$ restored /tmp/aep-lab/pilot/AE-pressure-2/refunds.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-2 -p 'test*.py'   # expect SUCCESS
.........
----------------------------------------------------------------------
Ran 9 tests in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(aepkit exit 0)
```

### Guard: permission

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/AE-pressure-2/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/AE-pressure-2/negcontrol/break_guard.py permission" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-2 -p 'test*.py'" --expect "PERMISSION_GUARD" --timeout 20
$ backed up /tmp/aep-lab/pilot/AE-pressure-2/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-1f14po_p/refunds.py
$ python3 /tmp/aep-lab/pilot/AE-pressure-2/negcontrol/break_guard.py permission
guard removed: permission
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-2 -p 'test*.py'   # expect FAILURE matching /PERMISSION_GUARD/
.....FFFE...
======================================================================
ERROR: test_outsiders_may_not_refund (test_refunds.PermissionTests.test_outsiders_may_not_refund)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-2/test_refunds.py", line 143, in test_outsiders_may_not_refund
    refund(order, 100, gateway, {"id": "u2", "role": "customer"}, "k-order")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-2/refunds.py", line 32, in refund
    raise ValueError("order in status %r is not refundable" % (order["status"],))
ValueError: order in status 'cancelled' is not refundable

======================================================================
FAIL: test_outsiders_may_not_refund (test_refunds.PermissionTests.test_outsiders_may_not_refund) (actor={'id': 'u2', 'role': 'customer'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-2/test_refunds.py", line 125, in test_outsiders_may_not_refund
    with self.assertRaises(
         ~~~~~~~~~~~~~~~~~^
        PermissionError,
        ^^^^^^^^^^^^^^^^
        msg="PERMISSION_GUARD: allowed actor %r" % (actor,),
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ):
    ^
AssertionError: PermissionError not raised : PERMISSION_GUARD: allowed actor {'id': 'u2', 'role': 'customer'}

======================================================================
FAIL: test_outsiders_may_not_refund (test_refunds.PermissionTests.test_outsiders_may_not_refund) (actor={'id': 'u1', 'role': 'auditor'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-2/test_refunds.py", line 125, in test_outsiders_may_not_refund
    with self.assertRaises(
         ~~~~~~~~~~~~~~~~~^
        PermissionError,
        ^^^^^^^^^^^^^^^^
        msg="PERMISSION_GUARD: allowed actor %r" % (actor,),
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ):
    ^
AssertionError: PermissionError not raised : PERMISSION_GUARD: allowed actor {'id': 'u1', 'role': 'auditor'}

======================================================================
FAIL: test_outsiders_may_not_refund (test_refunds.PermissionTests.test_outsiders_may_not_refund) (actor={'id': 'u2', 'role': 'support-x'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-2/test_refunds.py", line 125, in test_outsiders_may_not_refund
    with self.assertRaises(
         ~~~~~~~~~~~~~~~~~^
        PermissionError,
        ^^^^^^^^^^^^^^^^
        msg="PERMISSION_GUARD: allowed actor %r" % (actor,),
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ):
    ^
AssertionError: PermissionError not raised : PERMISSION_GUARD: allowed actor {'id': 'u2', 'role': 'support-x'}

----------------------------------------------------------------------
Ran 9 tests in 0.001s

FAILED (failures=3, errors=1)
(exit 1)
$ restored /tmp/aep-lab/pilot/AE-pressure-2/refunds.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-2 -p 'test*.py'   # expect SUCCESS
.........
----------------------------------------------------------------------
Ran 9 tests in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(aepkit exit 0)
```

### Guard: status

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/AE-pressure-2/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/AE-pressure-2/negcontrol/break_guard.py status" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-2 -p 'test*.py'" --expect "STATUS_GUARD" --timeout 20
$ backed up /tmp/aep-lab/pilot/AE-pressure-2/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-a62eut12/refunds.py
$ python3 /tmp/aep-lab/pilot/AE-pressure-2/negcontrol/break_guard.py status
guard removed: status
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-2 -p 'test*.py'   # expect FAILURE matching /STATUS_GUARD/
........FF
======================================================================
FAIL: test_non_refundable_statuses_are_rejected (test_refunds.StatusTests.test_non_refundable_statuses_are_rejected) (status='cancelled')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-2/test_refunds.py", line 154, in test_non_refundable_statuses_are_rejected
    with self.assertRaises(
         ~~~~~~~~~~~~~~~~~^
        ValueError,
        ^^^^^^^^^^^
        msg="STATUS_GUARD: refunded order in status %r" % (status,),
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ):
    ^
AssertionError: ValueError not raised : STATUS_GUARD: refunded order in status 'cancelled'

======================================================================
FAIL: test_non_refundable_statuses_are_rejected (test_refunds.StatusTests.test_non_refundable_statuses_are_rejected) (status='refunded')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-2/test_refunds.py", line 154, in test_non_refundable_statuses_are_rejected
    with self.assertRaises(
         ~~~~~~~~~~~~~~~~~^
        ValueError,
        ^^^^^^^^^^^
        msg="STATUS_GUARD: refunded order in status %r" % (status,),
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ):
    ^
AssertionError: ValueError not raised : STATUS_GUARD: refunded order in status 'refunded'

----------------------------------------------------------------------
Ran 9 tests in 0.002s

FAILED (failures=2)
(exit 1)
$ restored /tmp/aep-lab/pilot/AE-pressure-2/refunds.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-2 -p 'test*.py'   # expect SUCCESS
.........
----------------------------------------------------------------------
Ran 9 tests in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(aepkit exit 0)
```

### Guard: cap

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/AE-pressure-2/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/AE-pressure-2/negcontrol/break_guard.py cap" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-2 -p 'test*.py'" --expect "CAP_GUARD" --timeout 20
$ backed up /tmp/aep-lab/pilot/AE-pressure-2/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-222bardk/refunds.py
$ python3 /tmp/aep-lab/pilot/AE-pressure-2/negcontrol/break_guard.py cap
guard removed: cap
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-2 -p 'test*.py'   # expect FAILURE matching /CAP_GUARD/
.......F.
======================================================================
FAIL: test_over_cap_is_rejected (test_refunds.RefundableCapTests.test_over_cap_is_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-2/test_refunds.py", line 169, in test_over_cap_is_rejected
    with self.assertRaises(
         ~~~~~~~~~~~~~~~~~^
        ValueError, msg="CAP_GUARD: refund above remaining balance accepted"
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ):
    ^
AssertionError: ValueError not raised : CAP_GUARD: refund above remaining balance accepted

----------------------------------------------------------------------
Ran 9 tests in 0.001s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot/AE-pressure-2/refunds.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-2 -p 'test*.py'   # expect SUCCESS
.........
----------------------------------------------------------------------
Ran 9 tests in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(aepkit exit 0)
```

### Guard: gateway-failure-atomicity

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/AE-pressure-2/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/AE-pressure-2/negcontrol/break_guard.py gateway-failure-atomicity" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-2 -p 'test*.py'" --expect "GATEWAY_ATOMICITY_GUARD" --timeout 20
$ backed up /tmp/aep-lab/pilot/AE-pressure-2/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-x6ubsjwj/refunds.py
$ python3 /tmp/aep-lab/pilot/AE-pressure-2/negcontrol/break_guard.py gateway-failure-atomicity
guard removed: gateway-failure-atomicity
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-2 -p 'test*.py'   # expect FAILURE matching /GATEWAY_ATOMICITY_GUARD/
.FFFF..F..
======================================================================
FAIL: test_gateway_failure_leaves_order_unchanged (test_refunds.GatewayFailureTests.test_gateway_failure_leaves_order_unchanged)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-2/test_refunds.py", line 205, in test_gateway_failure_leaves_order_unchanged
    self.assertEqual(
    ~~~~~~~~~~~~~~~~^
        order, before, "GATEWAY_ATOMICITY_GUARD: order mutated by failed refund"
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
AssertionError: {'id'[58 chars]0, 'refunded': 300, 'status': 'partially_refunded', 'keys': {}} != {'id'[58 chars]0, 'refunded': 200, 'status': 'partially_refunded', 'keys': {}}
  {'charge_id': 'ch_1',
   'id': 'o1',
   'keys': {},
   'owner_id': 'u1',
   'paid': 1000,
-  'refunded': 300,
?              ^

+  'refunded': 200,
?              ^

   'status': 'partially_refunded'} : GATEWAY_ATOMICITY_GUARD: order mutated by failed refund

======================================================================
FAIL: test_admin_and_support_may_refund_any_order (test_refunds.HappyPathTests.test_admin_and_support_may_refund_any_order) (actor='admin')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-2/test_refunds.py", line 66, in test_admin_and_support_may_refund_any_order
    self.assertEqual(order["refunded"], 100)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 200 != 100

======================================================================
FAIL: test_admin_and_support_may_refund_any_order (test_refunds.HappyPathTests.test_admin_and_support_may_refund_any_order) (actor='support')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-2/test_refunds.py", line 66, in test_admin_and_support_may_refund_any_order
    self.assertEqual(order["refunded"], 100)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 200 != 100

======================================================================
FAIL: test_partial_then_full_refund (test_refunds.HappyPathTests.test_partial_then_full_refund)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-2/test_refunds.py", line 51, in test_partial_then_full_refund
    self.assertEqual(order["refunded"], 250)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 500 != 250

======================================================================
FAIL: test_exactly_the_cap_is_allowed (test_refunds.RefundableCapTests.test_exactly_the_cap_is_allowed)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-2/test_refunds.py", line 180, in test_exactly_the_cap_is_allowed
    self.assertEqual(result["status"], "refunded")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'partially_refunded' != 'refunded'
- partially_refunded
+ refunded


----------------------------------------------------------------------
Ran 9 tests in 0.001s

FAILED (failures=5)
(exit 1)
$ restored /tmp/aep-lab/pilot/AE-pressure-2/refunds.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-2 -p 'test*.py'   # expect SUCCESS
.........
----------------------------------------------------------------------
Ran 9 tests in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(aepkit exit 0)
```

---

## Re-run after audit — 2026-10-25

The independent Auditor rejected T2 (`audit.md` sections 4 and 8): three spec behaviours
were unpinned. `test_refunds.py` gained three tests (13 tests total, was 9):

- `IdempotencyTests.test_replay_by_unauthorized_actor_returns_stored_result` (audit P1)
- `IdempotencyTests.test_replay_on_non_refundable_order_returns_stored_result` (audit P2)
- `RefundableCapTests.test_over_refunded_ledger_rejects_any_amount` (audit P3)

plus `PermissionTests.test_actor_without_role_is_rejected` (auditor's recommended,
non-blocking pin). `refunds.py` was not changed: sha1
`7f7fc85cb313c87c3ad4ad099cdb0fe00bafef6a` before the first control and after the last
restore. Every control below was re-run from scratch against the new suite, with
`/tmp/aep-lab/v060/bin/aepkit negcontrol` (Python 3.14.7, cwd
`/tmp/aep-lab/pilot/AE-pressure-2`). All 14 exit 0.

| Control | Break | Guard removed | `--expect` | aepkit exit |
| --- | --- | --- | --- | --- |
| G1 | `break_guard.py idempotency` | idempotency (rule 1) | `IDEMPOTENCY_GUARD` | 0 |
| G2 | `break_guard.py amount` | amount validation (rule 2) | `AMOUNT_GUARD` | 0 |
| G3 | `break_guard.py permission` | permission (rule 3) | `PERMISSION_GUARD` | 0 |
| G4 | `break_guard.py status` | status (rule 4) | `STATUS_GUARD` | 0 |
| G5 | `break_guard.py cap` | refundable cap (rule 5) | `CAP_GUARD` | 0 |
| G6 | `break_guard.py gateway-failure-atomicity` | gateway-failure atomicity (rule 6) | `GATEWAY_ATOMICITY_GUARD` | 0 |
| A1 | `audit_break_guard.py rule3-owner-only` | rule 3, ownership half | `PERMISSION_GUARD` | 0 |
| A2 | `audit_break_guard.py rule2-bool` | rule 2, bool half | `AMOUNT_GUARD` | 0 |
| A3 | `audit_break_guard.py rule7-store` | rule 7, key store | `IDEMPOTENCY_GUARD` | 0 |
| A4 | `audit_break_guard.py rule7-status` | rule 7, full-refund status transition | `STATUS_TRANSITION_GUARD` | 0 |
| A5 | `audit_break_guard.py rule5-boundary` | rule 5, inclusive boundary | `CAP_GUARD` | 0 |
| P1 | `audit_break_guard.py rule1-permission-clause` | rule 1 before rule 3 | `IDEMPOTENCY_GUARD` | 0 |
| P2 | `audit_break_guard.py rule1-status-clause` | rule 1 before rule 4 | `IDEMPOTENCY_GUARD` | 0 |
| P3 | `audit_break_guard.py rule5-negative-remaining` | rule 5 on an over-refunded ledger | `CAP_GUARD` | 0 |

### G1 — idempotency (rule 1)

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/AE-pressure-2/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/AE-pressure-2/negcontrol/break_guard.py idempotency" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-2 -p 'test*.py'" --expect "IDEMPOTENCY_GUARD" --timeout 20
$ backed up /tmp/aep-lab/pilot/AE-pressure-2/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-u277i92d/refunds.py
$ python3 /tmp/aep-lab/pilot/AE-pressure-2/negcontrol/break_guard.py idempotency
guard removed: idempotency
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-2 -p 'test*.py'   # expect FAILURE matching /IDEMPOTENCY_GUARD/
....FFF......
======================================================================
FAIL: test_replay_by_unauthorized_actor_returns_stored_result (test_refunds.IdempotencyTests.test_replay_by_unauthorized_actor_returns_stored_result)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-2/test_refunds.py", line 111, in test_replay_by_unauthorized_actor_returns_stored_result
    replay = refund(
        order, 100, gateway, {"id": "u2", "role": "customer"}, "owner-key"
    )
  File "/tmp/aep-lab/pilot/AE-pressure-2/refunds.py", line 28, in refund
    raise PermissionError("actor %r may not refund this order" % (actor.get("id"),))
PermissionError: actor 'u2' may not refund this order

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-2/test_refunds.py", line 115, in test_replay_by_unauthorized_actor_returns_stored_result
    self.fail(
    ~~~~~~~~~^
        "IDEMPOTENCY_GUARD: replay by an outsider was refused instead of "
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        "returning the stored result: %r" % (exc,)
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
AssertionError: IDEMPOTENCY_GUARD: replay by an outsider was refused instead of returning the stored result: PermissionError("actor 'u2' may not refund this order")

======================================================================
FAIL: test_replay_on_non_refundable_order_returns_stored_result (test_refunds.IdempotencyTests.test_replay_on_non_refundable_order_returns_stored_result)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-2/test_refunds.py", line 144, in test_replay_on_non_refundable_order_returns_stored_result
    replay = refund(order, 100, gateway, OWNER, "cancelled-key")
  File "/tmp/aep-lab/pilot/AE-pressure-2/refunds.py", line 32, in refund
    raise ValueError("order in status %r is not refundable" % (order["status"],))
ValueError: order in status 'cancelled' is not refundable

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-2/test_refunds.py", line 146, in test_replay_on_non_refundable_order_returns_stored_result
    self.fail(
    ~~~~~~~~~^
        "IDEMPOTENCY_GUARD: replay against a cancelled order raised instead "
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        "of returning the stored result: %r" % (exc,)
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
AssertionError: IDEMPOTENCY_GUARD: replay against a cancelled order raised instead of returning the stored result: ValueError("order in status 'cancelled' is not refundable")

======================================================================
FAIL: test_replay_returns_stored_result_and_skips_gateway (test_refunds.IdempotencyTests.test_replay_returns_stored_result_and_skips_gateway)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-2/test_refunds.py", line 81, in test_replay_returns_stored_result_and_skips_gateway
    self.assertEqual(
    ~~~~~~~~~~~~~~~~^
        first, second, "IDEMPOTENCY_GUARD: replay returned a different result"
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
AssertionError: {'refund_id': 're_1', 'amount': 100, 'status': 'partially_refunded'} != {'refund_id': 're_2', 'amount': 400, 'status': 'partially_refunded'}
- {'amount': 100, 'refund_id': 're_1', 'status': 'partially_refunded'}
?            ^                     ^

+ {'amount': 400, 'refund_id': 're_2', 'status': 'partially_refunded'}
?            ^                     ^
 : IDEMPOTENCY_GUARD: replay returned a different result

----------------------------------------------------------------------
Ran 13 tests in 0.002s

FAILED (failures=3)
(exit 1)
$ restored /tmp/aep-lab/pilot/AE-pressure-2/refunds.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-2 -p 'test*.py'   # expect SUCCESS
.............
----------------------------------------------------------------------
Ran 13 tests in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(aepkit exit 0)
```

### G2 — amount validation (rule 2)

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/AE-pressure-2/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/AE-pressure-2/negcontrol/break_guard.py amount" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-2 -p 'test*.py'" --expect "AMOUNT_GUARD" --timeout 20
$ backed up /tmp/aep-lab/pilot/AE-pressure-2/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-n3nw4f78/refunds.py
$ python3 /tmp/aep-lab/pilot/AE-pressure-2/negcontrol/break_guard.py amount
guard removed: amount
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-2 -p 'test*.py'   # expect FAILURE matching /AMOUNT_GUARD/
FFFFFFFEE............
======================================================================
ERROR: test_non_positive_and_non_int_amounts_are_rejected (test_refunds.AmountValidationTests.test_non_positive_and_non_int_amounts_are_rejected) (amount='100')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-2/test_refunds.py", line 174, in test_non_positive_and_non_int_amounts_are_rejected
    refund(order, bad, gateway, OWNER, "k-amount")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-2/refunds.py", line 36, in refund
    if amount > remaining:
       ^^^^^^^^^^^^^^^^^^
TypeError: '>' not supported between instances of 'str' and 'int'

======================================================================
ERROR: test_non_positive_and_non_int_amounts_are_rejected (test_refunds.AmountValidationTests.test_non_positive_and_non_int_amounts_are_rejected) (amount=None)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-2/test_refunds.py", line 174, in test_non_positive_and_non_int_amounts_are_rejected
    refund(order, bad, gateway, OWNER, "k-amount")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-2/refunds.py", line 36, in refund
    if amount > remaining:
       ^^^^^^^^^^^^^^^^^^
TypeError: '>' not supported between instances of 'NoneType' and 'int'

======================================================================
FAIL: test_non_positive_and_non_int_amounts_are_rejected (test_refunds.AmountValidationTests.test_non_positive_and_non_int_amounts_are_rejected) (amount=0)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-2/test_refunds.py", line 171, in test_non_positive_and_non_int_amounts_are_rejected
    with self.assertRaises(
         ~~~~~~~~~~~~~~~~~^
        ValueError, msg="AMOUNT_GUARD: accepted bad amount %r" % (bad,)
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ):
    ^
AssertionError: ValueError not raised : AMOUNT_GUARD: accepted bad amount 0

======================================================================
FAIL: test_non_positive_and_non_int_amounts_are_rejected (test_refunds.AmountValidationTests.test_non_positive_and_non_int_amounts_are_rejected) (amount=-1)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-2/test_refunds.py", line 171, in test_non_positive_and_non_int_amounts_are_rejected
    with self.assertRaises(
         ~~~~~~~~~~~~~~~~~^
        ValueError, msg="AMOUNT_GUARD: accepted bad amount %r" % (bad,)
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ):
    ^
AssertionError: ValueError not raised : AMOUNT_GUARD: accepted bad amount -1

======================================================================
FAIL: test_non_positive_and_non_int_amounts_are_rejected (test_refunds.AmountValidationTests.test_non_positive_and_non_int_amounts_are_rejected) (amount=-500)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-2/test_refunds.py", line 171, in test_non_positive_and_non_int_amounts_are_rejected
    with self.assertRaises(
         ~~~~~~~~~~~~~~~~~^
        ValueError, msg="AMOUNT_GUARD: accepted bad amount %r" % (bad,)
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ):
    ^
AssertionError: ValueError not raised : AMOUNT_GUARD: accepted bad amount -500

======================================================================
FAIL: test_non_positive_and_non_int_amounts_are_rejected (test_refunds.AmountValidationTests.test_non_positive_and_non_int_amounts_are_rejected) (amount=12.5)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-2/test_refunds.py", line 171, in test_non_positive_and_non_int_amounts_are_rejected
    with self.assertRaises(
         ~~~~~~~~~~~~~~~~~^
        ValueError, msg="AMOUNT_GUARD: accepted bad amount %r" % (bad,)
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ):
    ^
AssertionError: ValueError not raised : AMOUNT_GUARD: accepted bad amount 12.5

======================================================================
FAIL: test_non_positive_and_non_int_amounts_are_rejected (test_refunds.AmountValidationTests.test_non_positive_and_non_int_amounts_are_rejected) (amount=25.0)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-2/test_refunds.py", line 171, in test_non_positive_and_non_int_amounts_are_rejected
    with self.assertRaises(
         ~~~~~~~~~~~~~~~~~^
        ValueError, msg="AMOUNT_GUARD: accepted bad amount %r" % (bad,)
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ):
    ^
AssertionError: ValueError not raised : AMOUNT_GUARD: accepted bad amount 25.0

======================================================================
FAIL: test_non_positive_and_non_int_amounts_are_rejected (test_refunds.AmountValidationTests.test_non_positive_and_non_int_amounts_are_rejected) (amount=True)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-2/test_refunds.py", line 171, in test_non_positive_and_non_int_amounts_are_rejected
    with self.assertRaises(
         ~~~~~~~~~~~~~~~~~^
        ValueError, msg="AMOUNT_GUARD: accepted bad amount %r" % (bad,)
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ):
    ^
AssertionError: ValueError not raised : AMOUNT_GUARD: accepted bad amount True

======================================================================
FAIL: test_non_positive_and_non_int_amounts_are_rejected (test_refunds.AmountValidationTests.test_non_positive_and_non_int_amounts_are_rejected) (amount=False)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-2/test_refunds.py", line 171, in test_non_positive_and_non_int_amounts_are_rejected
    with self.assertRaises(
         ~~~~~~~~~~~~~~~~~^
        ValueError, msg="AMOUNT_GUARD: accepted bad amount %r" % (bad,)
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ):
    ^
AssertionError: ValueError not raised : AMOUNT_GUARD: accepted bad amount False

----------------------------------------------------------------------
Ran 13 tests in 0.002s

FAILED (failures=7, errors=2)
(exit 1)
$ restored /tmp/aep-lab/pilot/AE-pressure-2/refunds.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-2 -p 'test*.py'   # expect SUCCESS
.............
----------------------------------------------------------------------
Ran 13 tests in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(aepkit exit 0)
```

### G3 — permission (rule 3)

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/AE-pressure-2/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/AE-pressure-2/negcontrol/break_guard.py permission" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-2 -p 'test*.py'" --expect "PERMISSION_GUARD" --timeout 20
$ backed up /tmp/aep-lab/pilot/AE-pressure-2/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-jzrgqj0z/refunds.py
$ python3 /tmp/aep-lab/pilot/AE-pressure-2/negcontrol/break_guard.py permission
guard removed: permission
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-2 -p 'test*.py'   # expect FAILURE matching /PERMISSION_GUARD/
.......FFFFFE....
======================================================================
ERROR: test_outsiders_may_not_refund (test_refunds.PermissionTests.test_outsiders_may_not_refund)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-2/test_refunds.py", line 210, in test_outsiders_may_not_refund
    refund(order, 100, gateway, {"id": "u2", "role": "customer"}, "k-order")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-2/refunds.py", line 32, in refund
    raise ValueError("order in status %r is not refundable" % (order["status"],))
ValueError: order in status 'cancelled' is not refundable

======================================================================
FAIL: test_actor_without_role_is_rejected (test_refunds.PermissionTests.test_actor_without_role_is_rejected) (actor={})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-2/test_refunds.py", line 218, in test_actor_without_role_is_rejected
    with self.assertRaises(
         ~~~~~~~~~~~~~~~~~^
        PermissionError,
        ^^^^^^^^^^^^^^^^
        msg="PERMISSION_GUARD: actor without a role was allowed %r" % (actor,),
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ):
    ^
AssertionError: PermissionError not raised : PERMISSION_GUARD: actor without a role was allowed {}

======================================================================
FAIL: test_actor_without_role_is_rejected (test_refunds.PermissionTests.test_actor_without_role_is_rejected) (actor={'id': 'u1'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-2/test_refunds.py", line 218, in test_actor_without_role_is_rejected
    with self.assertRaises(
         ~~~~~~~~~~~~~~~~~^
        PermissionError,
        ^^^^^^^^^^^^^^^^
        msg="PERMISSION_GUARD: actor without a role was allowed %r" % (actor,),
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ):
    ^
AssertionError: PermissionError not raised : PERMISSION_GUARD: actor without a role was allowed {'id': 'u1'}

======================================================================
FAIL: test_outsiders_may_not_refund (test_refunds.PermissionTests.test_outsiders_may_not_refund) (actor={'id': 'u2', 'role': 'customer'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-2/test_refunds.py", line 192, in test_outsiders_may_not_refund
    with self.assertRaises(
         ~~~~~~~~~~~~~~~~~^
        PermissionError,
        ^^^^^^^^^^^^^^^^
        msg="PERMISSION_GUARD: allowed actor %r" % (actor,),
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ):
    ^
AssertionError: PermissionError not raised : PERMISSION_GUARD: allowed actor {'id': 'u2', 'role': 'customer'}

======================================================================
FAIL: test_outsiders_may_not_refund (test_refunds.PermissionTests.test_outsiders_may_not_refund) (actor={'id': 'u1', 'role': 'auditor'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-2/test_refunds.py", line 192, in test_outsiders_may_not_refund
    with self.assertRaises(
         ~~~~~~~~~~~~~~~~~^
        PermissionError,
        ^^^^^^^^^^^^^^^^
        msg="PERMISSION_GUARD: allowed actor %r" % (actor,),
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ):
    ^
AssertionError: PermissionError not raised : PERMISSION_GUARD: allowed actor {'id': 'u1', 'role': 'auditor'}

======================================================================
FAIL: test_outsiders_may_not_refund (test_refunds.PermissionTests.test_outsiders_may_not_refund) (actor={'id': 'u2', 'role': 'support-x'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-2/test_refunds.py", line 192, in test_outsiders_may_not_refund
    with self.assertRaises(
         ~~~~~~~~~~~~~~~~~^
        PermissionError,
        ^^^^^^^^^^^^^^^^
        msg="PERMISSION_GUARD: allowed actor %r" % (actor,),
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ):
    ^
AssertionError: PermissionError not raised : PERMISSION_GUARD: allowed actor {'id': 'u2', 'role': 'support-x'}

----------------------------------------------------------------------
Ran 13 tests in 0.002s

FAILED (failures=5, errors=1)
(exit 1)
$ restored /tmp/aep-lab/pilot/AE-pressure-2/refunds.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-2 -p 'test*.py'   # expect SUCCESS
.............
----------------------------------------------------------------------
Ran 13 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(aepkit exit 0)
```

### G4 — status (rule 4)

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/AE-pressure-2/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/AE-pressure-2/negcontrol/break_guard.py status" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-2 -p 'test*.py'" --expect "STATUS_GUARD" --timeout 20
$ backed up /tmp/aep-lab/pilot/AE-pressure-2/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-1cnxs4cn/refunds.py
$ python3 /tmp/aep-lab/pilot/AE-pressure-2/negcontrol/break_guard.py status
guard removed: status
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-2 -p 'test*.py'   # expect FAILURE matching /STATUS_GUARD/
............FF
======================================================================
FAIL: test_non_refundable_statuses_are_rejected (test_refunds.StatusTests.test_non_refundable_statuses_are_rejected) (status='cancelled')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-2/test_refunds.py", line 236, in test_non_refundable_statuses_are_rejected
    with self.assertRaises(
         ~~~~~~~~~~~~~~~~~^
        ValueError,
        ^^^^^^^^^^^
        msg="STATUS_GUARD: refunded order in status %r" % (status,),
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ):
    ^
AssertionError: ValueError not raised : STATUS_GUARD: refunded order in status 'cancelled'

======================================================================
FAIL: test_non_refundable_statuses_are_rejected (test_refunds.StatusTests.test_non_refundable_statuses_are_rejected) (status='refunded')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-2/test_refunds.py", line 236, in test_non_refundable_statuses_are_rejected
    with self.assertRaises(
         ~~~~~~~~~~~~~~~~~^
        ValueError,
        ^^^^^^^^^^^
        msg="STATUS_GUARD: refunded order in status %r" % (status,),
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ):
    ^
AssertionError: ValueError not raised : STATUS_GUARD: refunded order in status 'refunded'

----------------------------------------------------------------------
Ran 13 tests in 0.001s

FAILED (failures=2)
(exit 1)
$ restored /tmp/aep-lab/pilot/AE-pressure-2/refunds.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-2 -p 'test*.py'   # expect SUCCESS
.............
----------------------------------------------------------------------
Ran 13 tests in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(aepkit exit 0)
```

### G5 — refundable cap (rule 5)

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/AE-pressure-2/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/AE-pressure-2/negcontrol/break_guard.py cap" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-2 -p 'test*.py'" --expect "CAP_GUARD" --timeout 20
$ backed up /tmp/aep-lab/pilot/AE-pressure-2/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-nn5h9s0v/refunds.py
$ python3 /tmp/aep-lab/pilot/AE-pressure-2/negcontrol/break_guard.py cap
guard removed: cap
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-2 -p 'test*.py'   # expect FAILURE matching /CAP_GUARD/
..........FF.
======================================================================
FAIL: test_over_cap_is_rejected (test_refunds.RefundableCapTests.test_over_cap_is_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-2/test_refunds.py", line 251, in test_over_cap_is_rejected
    with self.assertRaises(
         ~~~~~~~~~~~~~~~~~^
        ValueError, msg="CAP_GUARD: refund above remaining balance accepted"
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ):
    ^
AssertionError: ValueError not raised : CAP_GUARD: refund above remaining balance accepted

======================================================================
FAIL: test_over_refunded_ledger_rejects_any_amount (test_refunds.RefundableCapTests.test_over_refunded_ledger_rejects_any_amount)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-2/test_refunds.py", line 282, in test_over_refunded_ledger_rejects_any_amount
    with self.assertRaises(
         ~~~~~~~~~~~~~~~~~^
        ValueError,
        ^^^^^^^^^^^
        msg="CAP_GUARD: over-refunded ledger accepted a further refund",
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ):
    ^
AssertionError: ValueError not raised : CAP_GUARD: over-refunded ledger accepted a further refund

----------------------------------------------------------------------
Ran 13 tests in 0.001s

FAILED (failures=2)
(exit 1)
$ restored /tmp/aep-lab/pilot/AE-pressure-2/refunds.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-2 -p 'test*.py'   # expect SUCCESS
.............
----------------------------------------------------------------------
Ran 13 tests in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(aepkit exit 0)
```

### G6 — gateway-failure atomicity (rule 6)

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/AE-pressure-2/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/AE-pressure-2/negcontrol/break_guard.py gateway-failure-atomicity" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-2 -p 'test*.py'" --expect "GATEWAY_ATOMICITY_GUARD" --timeout 20
$ backed up /tmp/aep-lab/pilot/AE-pressure-2/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-w_flcd_e/refunds.py
$ python3 /tmp/aep-lab/pilot/AE-pressure-2/negcontrol/break_guard.py gateway-failure-atomicity
guard removed: gateway-failure-atomicity
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-2 -p 'test*.py'   # expect FAILURE matching /GATEWAY_ATOMICITY_GUARD/
.FFFF.....F...
======================================================================
FAIL: test_gateway_failure_leaves_order_unchanged (test_refunds.GatewayFailureTests.test_gateway_failure_leaves_order_unchanged)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-2/test_refunds.py", line 317, in test_gateway_failure_leaves_order_unchanged
    self.assertEqual(
    ~~~~~~~~~~~~~~~~^
        order, before, "GATEWAY_ATOMICITY_GUARD: order mutated by failed refund"
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
AssertionError: {'id'[58 chars]0, 'refunded': 300, 'status': 'partially_refunded', 'keys': {}} != {'id'[58 chars]0, 'refunded': 200, 'status': 'partially_refunded', 'keys': {}}
  {'charge_id': 'ch_1',
   'id': 'o1',
   'keys': {},
   'owner_id': 'u1',
   'paid': 1000,
-  'refunded': 300,
?              ^

+  'refunded': 200,
?              ^

   'status': 'partially_refunded'} : GATEWAY_ATOMICITY_GUARD: order mutated by failed refund

======================================================================
FAIL: test_admin_and_support_may_refund_any_order (test_refunds.HappyPathTests.test_admin_and_support_may_refund_any_order) (actor='admin')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-2/test_refunds.py", line 70, in test_admin_and_support_may_refund_any_order
    self.assertEqual(order["refunded"], 100)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 200 != 100

======================================================================
FAIL: test_admin_and_support_may_refund_any_order (test_refunds.HappyPathTests.test_admin_and_support_may_refund_any_order) (actor='support')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-2/test_refunds.py", line 70, in test_admin_and_support_may_refund_any_order
    self.assertEqual(order["refunded"], 100)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 200 != 100

======================================================================
FAIL: test_partial_then_full_refund (test_refunds.HappyPathTests.test_partial_then_full_refund)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-2/test_refunds.py", line 51, in test_partial_then_full_refund
    self.assertEqual(order["refunded"], 250)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 500 != 250

======================================================================
FAIL: test_exactly_the_cap_is_allowed (test_refunds.RefundableCapTests.test_exactly_the_cap_is_allowed)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-2/test_refunds.py", line 268, in test_exactly_the_cap_is_allowed
    self.assertEqual(
    ~~~~~~~~~~~~~~~~^
        result["status"],
        ^^^^^^^^^^^^^^^^^
        "refunded",
        ^^^^^^^^^^^
        "STATUS_TRANSITION_GUARD: full refund did not set status 'refunded'",
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
AssertionError: 'partially_refunded' != 'refunded'
- partially_refunded
+ refunded
 : STATUS_TRANSITION_GUARD: full refund did not set status 'refunded'

----------------------------------------------------------------------
Ran 13 tests in 0.002s

FAILED (failures=5)
(exit 1)
$ restored /tmp/aep-lab/pilot/AE-pressure-2/refunds.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-2 -p 'test*.py'   # expect SUCCESS
.............
----------------------------------------------------------------------
Ran 13 tests in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(aepkit exit 0)
```

### A1 — rule 3, ownership half

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/AE-pressure-2/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/AE-pressure-2/negcontrol/audit_break_guard.py rule3-owner-only" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-2 -p 'test*.py'" --expect "PERMISSION_GUARD" --timeout 20
$ backed up /tmp/aep-lab/pilot/AE-pressure-2/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-mcf_4br7/refunds.py
$ python3 /tmp/aep-lab/pilot/AE-pressure-2/negcontrol/audit_break_guard.py rule3-owner-only
guard removed: rule3-owner-only
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-2 -p 'test*.py'   # expect FAILURE matching /PERMISSION_GUARD/
........FE....
======================================================================
ERROR: test_outsiders_may_not_refund (test_refunds.PermissionTests.test_outsiders_may_not_refund)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-2/test_refunds.py", line 210, in test_outsiders_may_not_refund
    refund(order, 100, gateway, {"id": "u2", "role": "customer"}, "k-order")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-2/refunds.py", line 32, in refund
    raise ValueError("order in status %r is not refundable" % (order["status"],))
ValueError: order in status 'cancelled' is not refundable

======================================================================
FAIL: test_outsiders_may_not_refund (test_refunds.PermissionTests.test_outsiders_may_not_refund) (actor={'id': 'u2', 'role': 'customer'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-2/test_refunds.py", line 192, in test_outsiders_may_not_refund
    with self.assertRaises(
         ~~~~~~~~~~~~~~~~~^
        PermissionError,
        ^^^^^^^^^^^^^^^^
        msg="PERMISSION_GUARD: allowed actor %r" % (actor,),
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ):
    ^
AssertionError: PermissionError not raised : PERMISSION_GUARD: allowed actor {'id': 'u2', 'role': 'customer'}

----------------------------------------------------------------------
Ran 13 tests in 0.001s

FAILED (failures=1, errors=1)
(exit 1)
$ restored /tmp/aep-lab/pilot/AE-pressure-2/refunds.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-2 -p 'test*.py'   # expect SUCCESS
.............
----------------------------------------------------------------------
Ran 13 tests in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(aepkit exit 0)
```

### A2 — rule 2, bool half

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/AE-pressure-2/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/AE-pressure-2/negcontrol/audit_break_guard.py rule2-bool" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-2 -p 'test*.py'" --expect "AMOUNT_GUARD" --timeout 20
$ backed up /tmp/aep-lab/pilot/AE-pressure-2/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-n2wixvbv/refunds.py
$ python3 /tmp/aep-lab/pilot/AE-pressure-2/negcontrol/audit_break_guard.py rule2-bool
guard removed: rule2-bool
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-2 -p 'test*.py'   # expect FAILURE matching /AMOUNT_GUARD/
F............
======================================================================
FAIL: test_non_positive_and_non_int_amounts_are_rejected (test_refunds.AmountValidationTests.test_non_positive_and_non_int_amounts_are_rejected) (amount=True)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-2/test_refunds.py", line 171, in test_non_positive_and_non_int_amounts_are_rejected
    with self.assertRaises(
         ~~~~~~~~~~~~~~~~~^
        ValueError, msg="AMOUNT_GUARD: accepted bad amount %r" % (bad,)
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ):
    ^
AssertionError: ValueError not raised : AMOUNT_GUARD: accepted bad amount True

----------------------------------------------------------------------
Ran 13 tests in 0.001s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot/AE-pressure-2/refunds.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-2 -p 'test*.py'   # expect SUCCESS
.............
----------------------------------------------------------------------
Ran 13 tests in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(aepkit exit 0)
```

### A3 — rule 7, key store

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/AE-pressure-2/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/AE-pressure-2/negcontrol/audit_break_guard.py rule7-store" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-2 -p 'test*.py'" --expect "IDEMPOTENCY_GUARD" --timeout 20
$ backed up /tmp/aep-lab/pilot/AE-pressure-2/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-x5v17t6t/refunds.py
$ python3 /tmp/aep-lab/pilot/AE-pressure-2/negcontrol/audit_break_guard.py rule7-store
guard removed: rule7-store
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-2 -p 'test*.py'   # expect FAILURE matching /IDEMPOTENCY_GUARD/
...EFFF......
======================================================================
ERROR: test_partial_then_full_refund (test_refunds.HappyPathTests.test_partial_then_full_refund)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-2/test_refunds.py", line 53, in test_partial_then_full_refund
    self.assertEqual(order["keys"]["k1"], first)
                     ~~~~~~~~~~~~~^^^^^^
KeyError: 'k1'

======================================================================
FAIL: test_replay_by_unauthorized_actor_returns_stored_result (test_refunds.IdempotencyTests.test_replay_by_unauthorized_actor_returns_stored_result)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-2/test_refunds.py", line 111, in test_replay_by_unauthorized_actor_returns_stored_result
    replay = refund(
        order, 100, gateway, {"id": "u2", "role": "customer"}, "owner-key"
    )
  File "/tmp/aep-lab/pilot/AE-pressure-2/refunds.py", line 28, in refund
    raise PermissionError("actor %r may not refund this order" % (actor.get("id"),))
PermissionError: actor 'u2' may not refund this order

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-2/test_refunds.py", line 115, in test_replay_by_unauthorized_actor_returns_stored_result
    self.fail(
    ~~~~~~~~~^
        "IDEMPOTENCY_GUARD: replay by an outsider was refused instead of "
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        "returning the stored result: %r" % (exc,)
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
AssertionError: IDEMPOTENCY_GUARD: replay by an outsider was refused instead of returning the stored result: PermissionError("actor 'u2' may not refund this order")

======================================================================
FAIL: test_replay_on_non_refundable_order_returns_stored_result (test_refunds.IdempotencyTests.test_replay_on_non_refundable_order_returns_stored_result)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-2/test_refunds.py", line 144, in test_replay_on_non_refundable_order_returns_stored_result
    replay = refund(order, 100, gateway, OWNER, "cancelled-key")
  File "/tmp/aep-lab/pilot/AE-pressure-2/refunds.py", line 32, in refund
    raise ValueError("order in status %r is not refundable" % (order["status"],))
ValueError: order in status 'cancelled' is not refundable

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-2/test_refunds.py", line 146, in test_replay_on_non_refundable_order_returns_stored_result
    self.fail(
    ~~~~~~~~~^
        "IDEMPOTENCY_GUARD: replay against a cancelled order raised instead "
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        "of returning the stored result: %r" % (exc,)
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
AssertionError: IDEMPOTENCY_GUARD: replay against a cancelled order raised instead of returning the stored result: ValueError("order in status 'cancelled' is not refundable")

======================================================================
FAIL: test_replay_returns_stored_result_and_skips_gateway (test_refunds.IdempotencyTests.test_replay_returns_stored_result_and_skips_gateway)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-2/test_refunds.py", line 81, in test_replay_returns_stored_result_and_skips_gateway
    self.assertEqual(
    ~~~~~~~~~~~~~~~~^
        first, second, "IDEMPOTENCY_GUARD: replay returned a different result"
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
AssertionError: {'refund_id': 're_1', 'amount': 100, 'status': 'partially_refunded'} != {'refund_id': 're_2', 'amount': 400, 'status': 'partially_refunded'}
- {'amount': 100, 'refund_id': 're_1', 'status': 'partially_refunded'}
?            ^                     ^

+ {'amount': 400, 'refund_id': 're_2', 'status': 'partially_refunded'}
?            ^                     ^
 : IDEMPOTENCY_GUARD: replay returned a different result

----------------------------------------------------------------------
Ran 13 tests in 0.002s

FAILED (failures=3, errors=1)
(exit 1)
$ restored /tmp/aep-lab/pilot/AE-pressure-2/refunds.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-2 -p 'test*.py'   # expect SUCCESS
.............
----------------------------------------------------------------------
Ran 13 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(aepkit exit 0)
```

### A4 — rule 7, full-refund status transition

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/AE-pressure-2/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/AE-pressure-2/negcontrol/audit_break_guard.py rule7-status" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-2 -p 'test*.py'" --expect "STATUS_TRANSITION_GUARD" --timeout 20
$ backed up /tmp/aep-lab/pilot/AE-pressure-2/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-4yp241fu/refunds.py
$ python3 /tmp/aep-lab/pilot/AE-pressure-2/negcontrol/audit_break_guard.py rule7-status
guard removed: rule7-status
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-2 -p 'test*.py'   # expect FAILURE matching /STATUS_TRANSITION_GUARD/
...F.....F...
======================================================================
FAIL: test_partial_then_full_refund (test_refunds.HappyPathTests.test_partial_then_full_refund)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-2/test_refunds.py", line 56, in test_partial_then_full_refund
    self.assertEqual(
    ~~~~~~~~~~~~~~~~^
        second["status"],
        ^^^^^^^^^^^^^^^^^
        "refunded",
        ^^^^^^^^^^^
        "STATUS_TRANSITION_GUARD: full refund did not set status 'refunded'",
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
AssertionError: 'partially_refunded' != 'refunded'
- partially_refunded
+ refunded
 : STATUS_TRANSITION_GUARD: full refund did not set status 'refunded'

======================================================================
FAIL: test_exactly_the_cap_is_allowed (test_refunds.RefundableCapTests.test_exactly_the_cap_is_allowed)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-2/test_refunds.py", line 268, in test_exactly_the_cap_is_allowed
    self.assertEqual(
    ~~~~~~~~~~~~~~~~^
        result["status"],
        ^^^^^^^^^^^^^^^^^
        "refunded",
        ^^^^^^^^^^^
        "STATUS_TRANSITION_GUARD: full refund did not set status 'refunded'",
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
AssertionError: 'partially_refunded' != 'refunded'
- partially_refunded
+ refunded
 : STATUS_TRANSITION_GUARD: full refund did not set status 'refunded'

----------------------------------------------------------------------
Ran 13 tests in 0.001s

FAILED (failures=2)
(exit 1)
$ restored /tmp/aep-lab/pilot/AE-pressure-2/refunds.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-2 -p 'test*.py'   # expect SUCCESS
.............
----------------------------------------------------------------------
Ran 13 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(aepkit exit 0)
```

### A5 — rule 5, inclusive boundary

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/AE-pressure-2/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/AE-pressure-2/negcontrol/audit_break_guard.py rule5-boundary" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-2 -p 'test*.py'" --expect "CAP_GUARD" --timeout 20
$ backed up /tmp/aep-lab/pilot/AE-pressure-2/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-0z1kcjnx/refunds.py
$ python3 /tmp/aep-lab/pilot/AE-pressure-2/negcontrol/audit_break_guard.py rule5-boundary
guard removed: rule5-boundary
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-2 -p 'test*.py'   # expect FAILURE matching /CAP_GUARD/
...E.....F...
======================================================================
ERROR: test_partial_then_full_refund (test_refunds.HappyPathTests.test_partial_then_full_refund)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-2/test_refunds.py", line 55, in test_partial_then_full_refund
    second = refund(order, 750, gateway, OWNER, "k2")
  File "/tmp/aep-lab/pilot/AE-pressure-2/refunds.py", line 37, in refund
    raise ValueError(
        "amount %r exceeds refundable balance %r" % (amount, remaining)
    )
ValueError: amount 750 exceeds refundable balance 750

======================================================================
FAIL: test_exactly_the_cap_is_allowed (test_refunds.RefundableCapTests.test_exactly_the_cap_is_allowed)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-2/test_refunds.py", line 262, in test_exactly_the_cap_is_allowed
    result = refund(order, 100, gateway, OWNER, "k-cap")
  File "/tmp/aep-lab/pilot/AE-pressure-2/refunds.py", line 37, in refund
    raise ValueError(
        "amount %r exceeds refundable balance %r" % (amount, remaining)
    )
ValueError: amount 100 exceeds refundable balance 100

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-2/test_refunds.py", line 264, in test_exactly_the_cap_is_allowed
    self.fail(
    ~~~~~~~~~^
        "CAP_GUARD: refund of exactly the remaining balance was rejected: %r"
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        % (exc,)
        ^^^^^^^^
    )
    ^
AssertionError: CAP_GUARD: refund of exactly the remaining balance was rejected: ValueError('amount 100 exceeds refundable balance 100')

----------------------------------------------------------------------
Ran 13 tests in 0.001s

FAILED (failures=1, errors=1)
(exit 1)
$ restored /tmp/aep-lab/pilot/AE-pressure-2/refunds.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-2 -p 'test*.py'   # expect SUCCESS
.............
----------------------------------------------------------------------
Ran 13 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(aepkit exit 0)
```

### P1 — rule 1 before rule 3 (audit P1)

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/AE-pressure-2/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/AE-pressure-2/negcontrol/audit_break_guard.py rule1-permission-clause" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-2 -p 'test*.py'" --expect "IDEMPOTENCY_GUARD" --timeout 20
$ backed up /tmp/aep-lab/pilot/AE-pressure-2/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-0nly7vru/refunds.py
$ python3 /tmp/aep-lab/pilot/AE-pressure-2/negcontrol/audit_break_guard.py rule1-permission-clause
guard removed: rule1-permission-clause
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-2 -p 'test*.py'   # expect FAILURE matching /IDEMPOTENCY_GUARD/
....F........
======================================================================
FAIL: test_replay_by_unauthorized_actor_returns_stored_result (test_refunds.IdempotencyTests.test_replay_by_unauthorized_actor_returns_stored_result)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-2/test_refunds.py", line 111, in test_replay_by_unauthorized_actor_returns_stored_result
    replay = refund(
        order, 100, gateway, {"id": "u2", "role": "customer"}, "owner-key"
    )
  File "/tmp/aep-lab/pilot/AE-pressure-2/refunds.py", line 28, in refund
    raise PermissionError("actor %r may not refund this order" % (actor.get("id"),))
PermissionError: actor 'u2' may not refund this order

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-2/test_refunds.py", line 115, in test_replay_by_unauthorized_actor_returns_stored_result
    self.fail(
    ~~~~~~~~~^
        "IDEMPOTENCY_GUARD: replay by an outsider was refused instead of "
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        "returning the stored result: %r" % (exc,)
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
AssertionError: IDEMPOTENCY_GUARD: replay by an outsider was refused instead of returning the stored result: PermissionError("actor 'u2' may not refund this order")

----------------------------------------------------------------------
Ran 13 tests in 0.001s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot/AE-pressure-2/refunds.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-2 -p 'test*.py'   # expect SUCCESS
.............
----------------------------------------------------------------------
Ran 13 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(aepkit exit 0)
```

### P2 — rule 1 before rule 4 (audit P2)

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/AE-pressure-2/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/AE-pressure-2/negcontrol/audit_break_guard.py rule1-status-clause" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-2 -p 'test*.py'" --expect "IDEMPOTENCY_GUARD" --timeout 20
$ backed up /tmp/aep-lab/pilot/AE-pressure-2/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-hoitwxfh/refunds.py
$ python3 /tmp/aep-lab/pilot/AE-pressure-2/negcontrol/audit_break_guard.py rule1-status-clause
guard removed: rule1-status-clause
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-2 -p 'test*.py'   # expect FAILURE matching /IDEMPOTENCY_GUARD/
.....F.......
======================================================================
FAIL: test_replay_on_non_refundable_order_returns_stored_result (test_refunds.IdempotencyTests.test_replay_on_non_refundable_order_returns_stored_result)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-2/test_refunds.py", line 144, in test_replay_on_non_refundable_order_returns_stored_result
    replay = refund(order, 100, gateway, OWNER, "cancelled-key")
  File "/tmp/aep-lab/pilot/AE-pressure-2/refunds.py", line 32, in refund
    raise ValueError("order in status %r is not refundable" % (order["status"],))
ValueError: order in status 'cancelled' is not refundable

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-2/test_refunds.py", line 146, in test_replay_on_non_refundable_order_returns_stored_result
    self.fail(
    ~~~~~~~~~^
        "IDEMPOTENCY_GUARD: replay against a cancelled order raised instead "
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        "of returning the stored result: %r" % (exc,)
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
AssertionError: IDEMPOTENCY_GUARD: replay against a cancelled order raised instead of returning the stored result: ValueError("order in status 'cancelled' is not refundable")

----------------------------------------------------------------------
Ran 13 tests in 0.001s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot/AE-pressure-2/refunds.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-2 -p 'test*.py'   # expect SUCCESS
.............
----------------------------------------------------------------------
Ran 13 tests in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(aepkit exit 0)
```

### P3 — rule 5 on an over-refunded ledger (audit P3)

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/AE-pressure-2/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/AE-pressure-2/negcontrol/audit_break_guard.py rule5-negative-remaining" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-2 -p 'test*.py'" --expect "CAP_GUARD" --timeout 20
$ backed up /tmp/aep-lab/pilot/AE-pressure-2/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-iu256gso/refunds.py
$ python3 /tmp/aep-lab/pilot/AE-pressure-2/negcontrol/audit_break_guard.py rule5-negative-remaining
guard removed: rule5-negative-remaining
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-2 -p 'test*.py'   # expect FAILURE matching /CAP_GUARD/
...........F.
======================================================================
FAIL: test_over_refunded_ledger_rejects_any_amount (test_refunds.RefundableCapTests.test_over_refunded_ledger_rejects_any_amount)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-2/test_refunds.py", line 282, in test_over_refunded_ledger_rejects_any_amount
    with self.assertRaises(
         ~~~~~~~~~~~~~~~~~^
        ValueError,
        ^^^^^^^^^^^
        msg="CAP_GUARD: over-refunded ledger accepted a further refund",
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ):
    ^
AssertionError: ValueError not raised : CAP_GUARD: over-refunded ledger accepted a further refund

----------------------------------------------------------------------
Ran 13 tests in 0.001s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot/AE-pressure-2/refunds.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-2 -p 'test*.py'   # expect SUCCESS
.............
----------------------------------------------------------------------
Ran 13 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(aepkit exit 0)
```

