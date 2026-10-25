# Negative-control log — refunds.py

Every guard in `refunds.py` is removed by a scripted break, the test suite is
run against the broken file, and the original file is restored byte-for-byte.
A control is only accepted when `aepkit negcontrol` exits 0: tests fail under
the break, the failure output matches the expected test name, and tests pass
again after restore.

## Baseline: tests pass on the unmodified implementation

```console
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-neutral-3 -p "test*.py"
............
----------------------------------------------------------------------
Ran 12 tests in 0.000s

OK
(exit 0)
```

## Guard: idempotency

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/AE-neutral-3/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/AE-neutral-3/controls/break_idempotency.py" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-neutral-3 -p "test*.py"' --expect "test_idempotency" --timeout 20
$ backed up /tmp/aep-lab/pilot/AE-neutral-3/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-kozix7ov/refunds.py
$ python3 /tmp/aep-lab/pilot/AE-neutral-3/controls/break_idempotency.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-neutral-3 -p "test*.py"   # expect FAILURE matching /test_idempotency/
...FE.......
======================================================================
ERROR: test_idempotency_takes_precedence_over_validation (test_refunds.GuardIdempotencyTests.test_idempotency_takes_precedence_over_validation)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-neutral-3/test_refunds.py", line 109, in test_idempotency_takes_precedence_over_validation
    replay = refund(order, -1, gateway, {"id": "x", "role": "guest"}, "idem")
  File "/tmp/aep-lab/pilot/AE-neutral-3/refunds.py", line 53, in refund
    _check_amount_type(amount)
    ~~~~~~~~~~~~~~~~~~^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-neutral-3/refunds.py", line 18, in _check_amount_type
    raise ValueError("amount must be a positive int")
ValueError: amount must be a positive int

======================================================================
FAIL: test_idempotency_replay_does_not_call_gateway_or_mutate (test_refunds.GuardIdempotencyTests.test_idempotency_replay_does_not_call_gateway_or_mutate)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-neutral-3/test_refunds.py", line 98, in test_idempotency_replay_does_not_call_gateway_or_mutate
    self.assertEqual(replay, first)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^
AssertionError: {'refund_id': 're_1', 'amount': 999, 'status': 'partially_refunded'} != {'refund_id': 're_1', 'amount': 4000, 'status': 'partially_refunded'}
- {'amount': 999, 'refund_id': 're_1', 'status': 'partially_refunded'}
?            ^^^

+ {'amount': 4000, 'refund_id': 're_1', 'status': 'partially_refunded'}
?            ^^^^


----------------------------------------------------------------------
Ran 12 tests in 0.002s

FAILED (failures=1, errors=1)
(exit 1)
$ restored /tmp/aep-lab/pilot/AE-neutral-3/refunds.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-neutral-3 -p "test*.py"   # expect SUCCESS
............
----------------------------------------------------------------------
Ran 12 tests in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

## Guard: amount validation

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/AE-neutral-3/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/AE-neutral-3/controls/break_amount.py" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-neutral-3 -p "test*.py"' --expect "test_rejects_non_positive" --timeout 20
$ backed up /tmp/aep-lab/pilot/AE-neutral-3/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-nshftwyi/refunds.py
$ python3 /tmp/aep-lab/pilot/AE-neutral-3/controls/break_amount.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-neutral-3 -p "test*.py"   # expect FAILURE matching /test_rejects_non_positive/
FFFFFFEE...........
======================================================================
ERROR: test_rejects_non_positive_bool_float_and_non_numeric_amounts (test_refunds.GuardAmountTests.test_rejects_non_positive_bool_float_and_non_numeric_amounts) (amount='100')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-neutral-3/test_refunds.py", line 123, in test_rejects_non_positive_bool_float_and_non_numeric_amounts
    refund(order, bad, gateway, ADMIN, "k")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-neutral-3/refunds.py", line 63, in refund
    _check_cap(order, amount)
    ~~~~~~~~~~^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-neutral-3/refunds.py", line 38, in _check_cap
    if amount > remaining:
       ^^^^^^^^^^^^^^^^^^
TypeError: '>' not supported between instances of 'str' and 'int'

======================================================================
ERROR: test_rejects_non_positive_bool_float_and_non_numeric_amounts (test_refunds.GuardAmountTests.test_rejects_non_positive_bool_float_and_non_numeric_amounts) (amount=None)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-neutral-3/test_refunds.py", line 123, in test_rejects_non_positive_bool_float_and_non_numeric_amounts
    refund(order, bad, gateway, ADMIN, "k")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-neutral-3/refunds.py", line 63, in refund
    _check_cap(order, amount)
    ~~~~~~~~~~^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-neutral-3/refunds.py", line 38, in _check_cap
    if amount > remaining:
       ^^^^^^^^^^^^^^^^^^
TypeError: '>' not supported between instances of 'NoneType' and 'int'

======================================================================
FAIL: test_rejects_non_positive_bool_float_and_non_numeric_amounts (test_refunds.GuardAmountTests.test_rejects_non_positive_bool_float_and_non_numeric_amounts) (amount=0)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-neutral-3/test_refunds.py", line 122, in test_rejects_non_positive_bool_float_and_non_numeric_amounts
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_rejects_non_positive_bool_float_and_non_numeric_amounts (test_refunds.GuardAmountTests.test_rejects_non_positive_bool_float_and_non_numeric_amounts) (amount=-100)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-neutral-3/test_refunds.py", line 122, in test_rejects_non_positive_bool_float_and_non_numeric_amounts
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_rejects_non_positive_bool_float_and_non_numeric_amounts (test_refunds.GuardAmountTests.test_rejects_non_positive_bool_float_and_non_numeric_amounts) (amount=True)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-neutral-3/test_refunds.py", line 122, in test_rejects_non_positive_bool_float_and_non_numeric_amounts
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_rejects_non_positive_bool_float_and_non_numeric_amounts (test_refunds.GuardAmountTests.test_rejects_non_positive_bool_float_and_non_numeric_amounts) (amount=False)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-neutral-3/test_refunds.py", line 122, in test_rejects_non_positive_bool_float_and_non_numeric_amounts
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_rejects_non_positive_bool_float_and_non_numeric_amounts (test_refunds.GuardAmountTests.test_rejects_non_positive_bool_float_and_non_numeric_amounts) (amount=1.5)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-neutral-3/test_refunds.py", line 122, in test_rejects_non_positive_bool_float_and_non_numeric_amounts
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_rejects_non_positive_bool_float_and_non_numeric_amounts (test_refunds.GuardAmountTests.test_rejects_non_positive_bool_float_and_non_numeric_amounts) (amount=100.0)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-neutral-3/test_refunds.py", line 122, in test_rejects_non_positive_bool_float_and_non_numeric_amounts
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 12 tests in 0.002s

FAILED (failures=6, errors=2)
(exit 1)
$ restored /tmp/aep-lab/pilot/AE-neutral-3/refunds.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-neutral-3 -p "test*.py"   # expect SUCCESS
............
----------------------------------------------------------------------
Ran 12 tests in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

## Guard: permission

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/AE-neutral-3/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/AE-neutral-3/controls/break_permission.py" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-neutral-3 -p "test*.py"' --expect "test_unauthorised_actors" --timeout 20
$ backed up /tmp/aep-lab/pilot/AE-neutral-3/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-dum9tm3y/refunds.py
$ python3 /tmp/aep-lab/pilot/AE-neutral-3/controls/break_permission.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-neutral-3 -p "test*.py"   # expect FAILURE matching /test_unauthorised_actors/
.....FFFF......
======================================================================
FAIL: test_unauthorised_actors_are_rejected (test_refunds.GuardPermissionTests.test_unauthorised_actors_are_rejected) (actor={'id': 'cust_2', 'role': 'customer'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-neutral-3/test_refunds.py", line 141, in test_unauthorised_actors_are_rejected
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_unauthorised_actors_are_rejected (test_refunds.GuardPermissionTests.test_unauthorised_actors_are_rejected) (actor={'id': 'cust_1', 'role': 'guest'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-neutral-3/test_refunds.py", line 141, in test_unauthorised_actors_are_rejected
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_unauthorised_actors_are_rejected (test_refunds.GuardPermissionTests.test_unauthorised_actors_are_rejected) (actor={'id': 'cust_1', 'role': 'viewer'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-neutral-3/test_refunds.py", line 141, in test_unauthorised_actors_are_rejected
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_unauthorised_actors_are_rejected (test_refunds.GuardPermissionTests.test_unauthorised_actors_are_rejected) (actor={'id': 'admin_2', 'role': ''})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-neutral-3/test_refunds.py", line 141, in test_unauthorised_actors_are_rejected
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

----------------------------------------------------------------------
Ran 12 tests in 0.001s

FAILED (failures=4)
(exit 1)
$ restored /tmp/aep-lab/pilot/AE-neutral-3/refunds.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-neutral-3 -p "test*.py"   # expect SUCCESS
............
----------------------------------------------------------------------
Ran 12 tests in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

## Guard: status

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/AE-neutral-3/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/AE-neutral-3/controls/break_status.py" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-neutral-3 -p "test*.py"' --expect "test_non_refundable_statuses" --timeout 20
$ backed up /tmp/aep-lab/pilot/AE-neutral-3/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-ely4wg5r/refunds.py
$ python3 /tmp/aep-lab/pilot/AE-neutral-3/controls/break_status.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-neutral-3 -p "test*.py"   # expect FAILURE matching /test_non_refundable_statuses/
......FFF....
======================================================================
FAIL: test_non_refundable_statuses_are_rejected (test_refunds.GuardStatusTests.test_non_refundable_statuses_are_rejected) (status='cancelled')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-neutral-3/test_refunds.py", line 154, in test_non_refundable_statuses_are_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_non_refundable_statuses_are_rejected (test_refunds.GuardStatusTests.test_non_refundable_statuses_are_rejected) (status='refunded')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-neutral-3/test_refunds.py", line 154, in test_non_refundable_statuses_are_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_unknown_status_is_rejected (test_refunds.GuardStatusTests.test_unknown_status_is_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-neutral-3/test_refunds.py", line 163, in test_unknown_status_is_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 12 tests in 0.001s

FAILED (failures=3)
(exit 1)
$ restored /tmp/aep-lab/pilot/AE-neutral-3/refunds.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-neutral-3 -p "test*.py"   # expect SUCCESS
............
----------------------------------------------------------------------
Ran 12 tests in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

## Guard: refundable cap

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/AE-neutral-3/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/AE-neutral-3/controls/break_cap.py" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-neutral-3 -p "test*.py"' --expect "test_amount_above_remaining" --timeout 20
$ backed up /tmp/aep-lab/pilot/AE-neutral-3/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-vv8x84a3/refunds.py
$ python3 /tmp/aep-lab/pilot/AE-neutral-3/controls/break_cap.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-neutral-3 -p "test*.py"   # expect FAILURE matching /test_amount_above_remaining/
.F..........
======================================================================
FAIL: test_amount_above_remaining_is_rejected (test_refunds.GuardCapTests.test_amount_above_remaining_is_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-neutral-3/test_refunds.py", line 172, in test_amount_above_remaining_is_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 12 tests in 0.001s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot/AE-neutral-3/refunds.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-neutral-3 -p "test*.py"   # expect SUCCESS
............
----------------------------------------------------------------------
Ran 12 tests in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

## Guard: gateway-failure atomicity

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/AE-neutral-3/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/AE-neutral-3/controls/break_atomicity.py" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-neutral-3 -p "test*.py"' --expect "test_gateway_error_leaves_order_untouched" --timeout 20
$ backed up /tmp/aep-lab/pilot/AE-neutral-3/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-hsxh3q3i/refunds.py
$ python3 /tmp/aep-lab/pilot/AE-neutral-3/controls/break_atomicity.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-neutral-3 -p "test*.py"   # expect FAILURE matching /test_gateway_error_leaves_order_untouched/
..FF.........
======================================================================
FAIL: test_gateway_error_leaves_order_untouched_and_reraises (test_refunds.GuardGatewayAtomicityTests.test_gateway_error_leaves_order_untouched_and_reraises) (refunded=0, status='paid')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-neutral-3/test_refunds.py", line 189, in test_gateway_error_leaves_order_untouched_and_reraises
    self.assertEqual(order, snapshot)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: {'id'[76 chars]ed': 1000, 'status': 'partially_refunded', 'ke[82 chars]d'}}} != {'id'[76 chars]ed': 0, 'status': 'paid', 'keys': {}}
  {'charge_id': 'ch_1',
   'id': 'ord_1',
+  'keys': {},
-  'keys': {'boom-key': {'amount': 1000,
-                        'refund_id': None,
-                        'status': 'partially_refunded'}},
   'owner_id': 'cust_1',
   'paid': 10000,
-  'refunded': 1000,
?              ---

+  'refunded': 0,
-  'status': 'partially_refunded'}
+  'status': 'paid'}

======================================================================
FAIL: test_gateway_error_leaves_order_untouched_and_reraises (test_refunds.GuardGatewayAtomicityTests.test_gateway_error_leaves_order_untouched_and_reraises) (refunded=4000, status='partially_refunded')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-neutral-3/test_refunds.py", line 189, in test_gateway_error_leaves_order_untouched_and_reraises
    self.assertEqual(order, snapshot)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: {'id'[76 chars]ed': 5000, 'status': 'partially_refunded', 'ke[82 chars]d'}}} != {'id'[76 chars]ed': 4000, 'status': 'partially_refunded', 'keys': {}}
  {'charge_id': 'ch_1',
   'id': 'ord_1',
+  'keys': {},
-  'keys': {'boom-key': {'amount': 1000,
-                        'refund_id': None,
-                        'status': 'partially_refunded'}},
   'owner_id': 'cust_1',
   'paid': 10000,
-  'refunded': 5000,
?              ^

+  'refunded': 4000,
?              ^

   'status': 'partially_refunded'}

----------------------------------------------------------------------
Ran 12 tests in 0.001s

FAILED (failures=2)
(exit 1)
$ restored /tmp/aep-lab/pilot/AE-neutral-3/refunds.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-neutral-3 -p "test*.py"   # expect SUCCESS
............
----------------------------------------------------------------------
Ran 12 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```
