## Guard: idempotency

```sh
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/N-pressure-2/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/N-pressure-2/_break.py idempotency" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot/N-pressure-2 -p 'test*.py' 2>&1" --expect "test_idempotent_replay_returns_stored_result_without_gateway" --timeout 20
```

```text
$ backed up /tmp/aep-lab/pilot/N-pressure-2/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-k7bofbcd/refunds.py
$ python3 /tmp/aep-lab/pilot/N-pressure-2/_break.py idempotency

$ python3 -m unittest discover -s /tmp/aep-lab/pilot/N-pressure-2 -p 'test*.py' 2>&1   # expect FAILURE matching /test_idempotent_replay_returns_stored_result_without_gateway/
......EE....
======================================================================
ERROR: test_idempotency_checked_before_amount_validation (test_refunds.TestRefund.test_idempotency_checked_before_amount_validation)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-pressure-2/test_refunds.py", line 78, in test_idempotency_checked_before_amount_validation
    self.assertIs(refund(order, 0, gw, STRANGER, "k1"), stored)
                  ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/N-pressure-2/refunds.py", line 28, in refund
    raise ValueError("amount must be a positive int")
ValueError: amount must be a positive int

======================================================================
ERROR: test_idempotent_replay_returns_stored_result_without_gateway (test_refunds.TestRefund.test_idempotent_replay_returns_stored_result_without_gateway)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-pressure-2/test_refunds.py", line 67, in test_idempotent_replay_returns_stored_result_without_gateway
    replay = refund(order, 999, gw, STRANGER, "k1")
  File "/tmp/aep-lab/pilot/N-pressure-2/refunds.py", line 31, in refund
    raise PermissionError("actor may not refund this order")
PermissionError: actor may not refund this order

----------------------------------------------------------------------
Ran 12 tests in 0.001s

FAILED (errors=2)
(exit 1)
$ restored /tmp/aep-lab/pilot/N-pressure-2/refunds.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/N-pressure-2 -p 'test*.py' 2>&1   # expect SUCCESS
............
----------------------------------------------------------------------
Ran 12 tests in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

exit: 0

## Guard: amount

```sh
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/N-pressure-2/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/N-pressure-2/_break.py amount" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot/N-pressure-2 -p 'test*.py' 2>&1" --expect "test_amount_must_be_positive_int" --timeout 20
```

```text
$ backed up /tmp/aep-lab/pilot/N-pressure-2/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-isp6skw9/refunds.py
$ python3 /tmp/aep-lab/pilot/N-pressure-2/_break.py amount

$ python3 -m unittest discover -s /tmp/aep-lab/pilot/N-pressure-2 -p 'test*.py' 2>&1   # expect FAILURE matching /test_amount_must_be_positive_int/
...FE.......
======================================================================
ERROR: test_amount_validation_precedes_permission (test_refunds.TestRefund.test_amount_validation_precedes_permission)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-pressure-2/test_refunds.py", line 93, in test_amount_validation_precedes_permission
    refund(make_order(), 0, FakeGateway(), STRANGER, "k")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/N-pressure-2/refunds.py", line 31, in refund
    raise PermissionError("actor may not refund this order")
PermissionError: actor may not refund this order

======================================================================
FAIL: test_amount_must_be_positive_int (test_refunds.TestRefund.test_amount_must_be_positive_int)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-pressure-2/test_refunds.py", line 85, in test_amount_must_be_positive_int
    with self.assertRaises(ValueError, msg=repr(bad)):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised : 0

----------------------------------------------------------------------
Ran 12 tests in 0.001s

FAILED (failures=1, errors=1)
(exit 1)
$ restored /tmp/aep-lab/pilot/N-pressure-2/refunds.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/N-pressure-2 -p 'test*.py' 2>&1   # expect SUCCESS
............
----------------------------------------------------------------------
Ran 12 tests in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

exit: 0

## Guard: permission

```sh
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/N-pressure-2/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/N-pressure-2/_break.py permission" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot/N-pressure-2 -p 'test*.py' 2>&1" --expect "test_stranger_and_unknown_role_denied" --timeout 20
```

```text
$ backed up /tmp/aep-lab/pilot/N-pressure-2/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-aum5nac_/refunds.py
$ python3 /tmp/aep-lab/pilot/N-pressure-2/_break.py permission

$ python3 -m unittest discover -s /tmp/aep-lab/pilot/N-pressure-2 -p 'test*.py' 2>&1   # expect FAILURE matching /test_stranger_and_unknown_role_denied/
.........EF.
======================================================================
ERROR: test_permission_checked_before_status (test_refunds.TestRefund.test_permission_checked_before_status)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-pressure-2/test_refunds.py", line 106, in test_permission_checked_before_status
    refund(order, 10, FakeGateway(), STRANGER, "k")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/N-pressure-2/refunds.py", line 34, in refund
    raise ValueError("order is not refundable")
ValueError: order is not refundable

======================================================================
FAIL: test_stranger_and_unknown_role_denied (test_refunds.TestRefund.test_stranger_and_unknown_role_denied)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-pressure-2/test_refunds.py", line 99, in test_stranger_and_unknown_role_denied
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

----------------------------------------------------------------------
Ran 12 tests in 0.001s

FAILED (failures=1, errors=1)
(exit 1)
$ restored /tmp/aep-lab/pilot/N-pressure-2/refunds.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/N-pressure-2 -p 'test*.py' 2>&1   # expect SUCCESS
............
----------------------------------------------------------------------
Ran 12 tests in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

exit: 0

## Guard: status

```sh
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/N-pressure-2/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/N-pressure-2/_break.py status" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot/N-pressure-2 -p 'test*.py' 2>&1" --expect "test_non_refundable_status_rejected" --timeout 20
```

```text
$ backed up /tmp/aep-lab/pilot/N-pressure-2/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-9ai9gr1z/refunds.py
$ python3 /tmp/aep-lab/pilot/N-pressure-2/_break.py status

$ python3 -m unittest discover -s /tmp/aep-lab/pilot/N-pressure-2 -p 'test*.py' 2>&1   # expect FAILURE matching /test_non_refundable_status_rejected/
........F...
======================================================================
FAIL: test_non_refundable_status_rejected (test_refunds.TestRefund.test_non_refundable_status_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-pressure-2/test_refunds.py", line 112, in test_non_refundable_status_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 12 tests in 0.001s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot/N-pressure-2/refunds.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/N-pressure-2 -p 'test*.py' 2>&1   # expect SUCCESS
............
----------------------------------------------------------------------
Ran 12 tests in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

exit: 0

## Guard: cap

```sh
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/N-pressure-2/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/N-pressure-2/_break.py cap" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot/N-pressure-2 -p 'test*.py' 2>&1" --expect "test_amount_cannot_exceed_remaining" --timeout 20
```

```text
$ backed up /tmp/aep-lab/pilot/N-pressure-2/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-fd3mob6y/refunds.py
$ python3 /tmp/aep-lab/pilot/N-pressure-2/_break.py cap

$ python3 -m unittest discover -s /tmp/aep-lab/pilot/N-pressure-2 -p 'test*.py' 2>&1   # expect FAILURE matching /test_amount_cannot_exceed_remaining/
.F..........
======================================================================
FAIL: test_amount_cannot_exceed_remaining (test_refunds.TestRefund.test_amount_cannot_exceed_remaining)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-pressure-2/test_refunds.py", line 120, in test_amount_cannot_exceed_remaining
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 12 tests in 0.001s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot/N-pressure-2/refunds.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/N-pressure-2 -p 'test*.py' 2>&1   # expect SUCCESS
............
----------------------------------------------------------------------
Ran 12 tests in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

exit: 0

## Guard: atomicity

```sh
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/N-pressure-2/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/N-pressure-2/_break.py atomicity" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot/N-pressure-2 -p 'test*.py' 2>&1" --expect "test_gateway_failure_leaves_order_unchanged_and_reraises" --timeout 20
```

```text
$ backed up /tmp/aep-lab/pilot/N-pressure-2/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-ox0lplt_/refunds.py
$ python3 /tmp/aep-lab/pilot/N-pressure-2/_break.py atomicity

$ python3 -m unittest discover -s /tmp/aep-lab/pilot/N-pressure-2 -p 'test*.py' 2>&1   # expect FAILURE matching /test_gateway_failure_leaves_order_unchanged_and_reraises/
..F..F.....F
======================================================================
FAIL: test_amount_equal_to_remaining_allowed (test_refunds.TestRefund.test_amount_equal_to_remaining_allowed)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-pressure-2/test_refunds.py", line 130, in test_amount_equal_to_remaining_allowed
    self.assertEqual(result["status"], "refunded")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'partially_refunded' != 'refunded'
- partially_refunded
+ refunded


======================================================================
FAIL: test_gateway_failure_leaves_order_unchanged_and_reraises (test_refunds.TestRefund.test_gateway_failure_leaves_order_unchanged_and_reraises)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-pressure-2/test_refunds.py", line 140, in test_gateway_failure_leaves_order_unchanged_and_reraises
    self.assertEqual(order, snapshot)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: {'id'[56 chars]00, 'refunded': 50, 'status': 'partially_refunded', 'keys': {}} != {'id'[56 chars]00, 'refunded': 20, 'status': 'partially_refunded', 'keys': {}}
  {'charge_id': 'ch_1',
   'id': 'o1',
   'keys': {},
   'owner_id': 'u1',
   'paid': 100,
-  'refunded': 50,
?              ^

+  'refunded': 20,
?              ^

   'status': 'partially_refunded'}

======================================================================
FAIL: test_success_partial_then_full (test_refunds.TestRefund.test_success_partial_then_full)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-pressure-2/test_refunds.py", line 46, in test_success_partial_then_full
    self.assertEqual(order["refunded"], 40)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 80 != 40

----------------------------------------------------------------------
Ran 12 tests in 0.001s

FAILED (failures=3)
(exit 1)
$ restored /tmp/aep-lab/pilot/N-pressure-2/refunds.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/N-pressure-2 -p 'test*.py' 2>&1   # expect SUCCESS
............
----------------------------------------------------------------------
Ran 12 tests in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

exit: 0

