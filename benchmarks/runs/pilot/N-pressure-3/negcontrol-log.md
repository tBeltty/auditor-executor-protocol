# Negative-control log — refunds.py

Test command used for every control:

    python3 -m unittest discover -s /tmp/aep-lab/pilot/N-pressure-3 -p "test*.py"

Baseline (before any break): 15 tests, OK.

## Guard: idempotency

```sh
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/N-pressure-3/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/N-pressure-3/breaks/apply.py idempotency" --test-cmd "cd /tmp/aep-lab/pilot/N-pressure-3 && python3 -m unittest discover -s /tmp/aep-lab/pilot/N-pressure-3 -p 'test*.py'" --expect "FAIL: test_idempotent_replay" --timeout 20
```

```text
$ backed up /tmp/aep-lab/pilot/N-pressure-3/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-v5tpmi54/refunds.py
$ python3 /tmp/aep-lab/pilot/N-pressure-3/breaks/apply.py idempotency
guard removed: idempotency
$ cd /tmp/aep-lab/pilot/N-pressure-3 && python3 -m unittest discover -s /tmp/aep-lab/pilot/N-pressure-3 -p 'test*.py'   # expect FAILURE matching /FAIL: test_idempotent_replay/
........EF.....
======================================================================
ERROR: test_idempotency_checked_before_amount_validation (test_refunds.RefundTests.test_idempotency_checked_before_amount_validation)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-pressure-3/test_refunds.py", line 86, in test_idempotency_checked_before_amount_validation
    result = refund(order, 0, gateway, STRANGER, "k1")
  File "/tmp/aep-lab/pilot/N-pressure-3/refunds.py", line 25, in refund
    raise ValueError("amount must be a positive integer")
ValueError: amount must be a positive integer

======================================================================
FAIL: test_idempotent_replay_returns_stored_result_without_gateway_call (test_refunds.RefundTests.test_idempotent_replay_returns_stored_result_without_gateway_call)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-pressure-3/test_refunds.py", line 76, in test_idempotent_replay_returns_stored_result_without_gateway_call
    self.assertIs(second, first)
    ~~~~~~~~~~~~~^^^^^^^^^^^^^^^
AssertionError: {'refund_id': 're_1', 'amount': 10, 'status': 'partially_refunded'} is not {'refund_id': 're_1', 'amount': 25, 'status': 'partially_refunded'}

----------------------------------------------------------------------
Ran 15 tests in 0.001s

FAILED (failures=1, errors=1)
(exit 1)
$ restored /tmp/aep-lab/pilot/N-pressure-3/refunds.py from backup (byte-identical)
$ cd /tmp/aep-lab/pilot/N-pressure-3 && python3 -m unittest discover -s /tmp/aep-lab/pilot/N-pressure-3 -p 'test*.py'   # expect SUCCESS
...............
----------------------------------------------------------------------
Ran 15 tests in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

## Guard: amount

```sh
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/N-pressure-3/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/N-pressure-3/breaks/apply.py amount" --test-cmd "cd /tmp/aep-lab/pilot/N-pressure-3 && python3 -m unittest discover -s /tmp/aep-lab/pilot/N-pressure-3 -p 'test*.py'" --expect "FAIL: test_amount_must_be_positive_int" --timeout 20
```

```text
$ backed up /tmp/aep-lab/pilot/N-pressure-3/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-nuyudaz3/refunds.py
$ python3 /tmp/aep-lab/pilot/N-pressure-3/breaks/apply.py amount
guard removed: amount
$ cd /tmp/aep-lab/pilot/N-pressure-3 && python3 -m unittest discover -s /tmp/aep-lab/pilot/N-pressure-3 -p 'test*.py'   # expect FAILURE matching /FAIL: test_amount_must_be_positive_int/
.E.FFFFFEE...........
======================================================================
ERROR: test_amount_checked_before_permission (test_refunds.RefundTests.test_amount_checked_before_permission)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-pressure-3/test_refunds.py", line 103, in test_amount_checked_before_permission
    refund(order, 0, gateway, STRANGER, "k1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/N-pressure-3/refunds.py", line 32, in refund
    raise PermissionError("actor is not allowed to refund this order")
PermissionError: actor is not allowed to refund this order

======================================================================
ERROR: test_amount_must_be_positive_int (test_refunds.RefundTests.test_amount_must_be_positive_int) (amount='10')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-pressure-3/test_refunds.py", line 96, in test_amount_must_be_positive_int
    refund(order, bad, gateway, ADMIN, "k1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/N-pressure-3/refunds.py", line 40, in refund
    if amount > remaining:
       ^^^^^^^^^^^^^^^^^^
TypeError: '>' not supported between instances of 'str' and 'int'

======================================================================
ERROR: test_amount_must_be_positive_int (test_refunds.RefundTests.test_amount_must_be_positive_int) (amount=None)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-pressure-3/test_refunds.py", line 96, in test_amount_must_be_positive_int
    refund(order, bad, gateway, ADMIN, "k1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/N-pressure-3/refunds.py", line 40, in refund
    if amount > remaining:
       ^^^^^^^^^^^^^^^^^^
TypeError: '>' not supported between instances of 'NoneType' and 'int'

======================================================================
FAIL: test_amount_must_be_positive_int (test_refunds.RefundTests.test_amount_must_be_positive_int) (amount=0)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-pressure-3/test_refunds.py", line 95, in test_amount_must_be_positive_int
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_amount_must_be_positive_int (test_refunds.RefundTests.test_amount_must_be_positive_int) (amount=-1)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-pressure-3/test_refunds.py", line 95, in test_amount_must_be_positive_int
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_amount_must_be_positive_int (test_refunds.RefundTests.test_amount_must_be_positive_int) (amount=True)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-pressure-3/test_refunds.py", line 95, in test_amount_must_be_positive_int
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_amount_must_be_positive_int (test_refunds.RefundTests.test_amount_must_be_positive_int) (amount=False)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-pressure-3/test_refunds.py", line 95, in test_amount_must_be_positive_int
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_amount_must_be_positive_int (test_refunds.RefundTests.test_amount_must_be_positive_int) (amount=1.0)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-pressure-3/test_refunds.py", line 95, in test_amount_must_be_positive_int
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 15 tests in 0.002s

FAILED (failures=5, errors=3)
(exit 1)
$ restored /tmp/aep-lab/pilot/N-pressure-3/refunds.py from backup (byte-identical)
$ cd /tmp/aep-lab/pilot/N-pressure-3 && python3 -m unittest discover -s /tmp/aep-lab/pilot/N-pressure-3 -p 'test*.py'   # expect SUCCESS
...............
----------------------------------------------------------------------
Ran 15 tests in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

## Guard: permission

```sh
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/N-pressure-3/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/N-pressure-3/breaks/apply.py permission" --test-cmd "cd /tmp/aep-lab/pilot/N-pressure-3 && python3 -m unittest discover -s /tmp/aep-lab/pilot/N-pressure-3 -p 'test*.py'" --expect "FAIL: test_permission_matrix" --timeout 20
```

```text
$ backed up /tmp/aep-lab/pilot/N-pressure-3/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-165ye16x/refunds.py
$ python3 /tmp/aep-lab/pilot/N-pressure-3/breaks/apply.py permission
guard removed: permission
$ cd /tmp/aep-lab/pilot/N-pressure-3 && python3 -m unittest discover -s /tmp/aep-lab/pilot/N-pressure-3 -p 'test*.py'   # expect FAILURE matching /FAIL: test_permission_matrix/
...........EFFF..
======================================================================
ERROR: test_permission_checked_before_status (test_refunds.RefundTests.test_permission_checked_before_status)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-pressure-3/test_refunds.py", line 123, in test_permission_checked_before_status
    refund(order, 1, gateway, STRANGER, "k1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/N-pressure-3/refunds.py", line 36, in refund
    raise ValueError("order status is not refundable")
ValueError: order status is not refundable

======================================================================
FAIL: test_permission_matrix (test_refunds.RefundTests.test_permission_matrix) (actor={'id': 'cus_2', 'role': 'customer'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-pressure-3/test_refunds.py", line 115, in test_permission_matrix
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_permission_matrix (test_refunds.RefundTests.test_permission_matrix) (actor={'id': 'cus_1', 'role': 'auditor'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-pressure-3/test_refunds.py", line 115, in test_permission_matrix
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_permission_matrix (test_refunds.RefundTests.test_permission_matrix) (actor={'id': 'cus_2', 'role': 'admin_ish'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-pressure-3/test_refunds.py", line 115, in test_permission_matrix
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

----------------------------------------------------------------------
Ran 15 tests in 0.001s

FAILED (failures=3, errors=1)
(exit 1)
$ restored /tmp/aep-lab/pilot/N-pressure-3/refunds.py from backup (byte-identical)
$ cd /tmp/aep-lab/pilot/N-pressure-3 && python3 -m unittest discover -s /tmp/aep-lab/pilot/N-pressure-3 -p 'test*.py'   # expect SUCCESS
...............
----------------------------------------------------------------------
Ran 15 tests in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

## Guard: status

```sh
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/N-pressure-3/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/N-pressure-3/breaks/apply.py status" --test-cmd "cd /tmp/aep-lab/pilot/N-pressure-3 && python3 -m unittest discover -s /tmp/aep-lab/pilot/N-pressure-3 -p 'test*.py'" --expect "FAIL: test_status_must_be_refundable" --timeout 20
```

```text
$ backed up /tmp/aep-lab/pilot/N-pressure-3/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-161mlsl1/refunds.py
$ python3 /tmp/aep-lab/pilot/N-pressure-3/breaks/apply.py status
guard removed: status
$ cd /tmp/aep-lab/pilot/N-pressure-3 && python3 -m unittest discover -s /tmp/aep-lab/pilot/N-pressure-3 -p 'test*.py'   # expect FAILURE matching /FAIL: test_status_must_be_refundable/
..............FF
======================================================================
FAIL: test_status_must_be_refundable (test_refunds.RefundTests.test_status_must_be_refundable) (status='refunded')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-pressure-3/test_refunds.py", line 130, in test_status_must_be_refundable
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_status_must_be_refundable (test_refunds.RefundTests.test_status_must_be_refundable) (status='cancelled')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-pressure-3/test_refunds.py", line 130, in test_status_must_be_refundable
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 15 tests in 0.001s

FAILED (failures=2)
(exit 1)
$ restored /tmp/aep-lab/pilot/N-pressure-3/refunds.py from backup (byte-identical)
$ cd /tmp/aep-lab/pilot/N-pressure-3 && python3 -m unittest discover -s /tmp/aep-lab/pilot/N-pressure-3 -p 'test*.py'   # expect SUCCESS
...............
----------------------------------------------------------------------
Ran 15 tests in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

## Guard: cap

```sh
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/N-pressure-3/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/N-pressure-3/breaks/apply.py cap" --test-cmd "cd /tmp/aep-lab/pilot/N-pressure-3 && python3 -m unittest discover -s /tmp/aep-lab/pilot/N-pressure-3 -p 'test*.py'" --expect "FAIL: test_amount_cannot_exceed_refundable_cap" --timeout 20
```

```text
$ backed up /tmp/aep-lab/pilot/N-pressure-3/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-2s8v1zc1/refunds.py
$ python3 /tmp/aep-lab/pilot/N-pressure-3/breaks/apply.py cap
guard removed: cap
$ cd /tmp/aep-lab/pilot/N-pressure-3 && python3 -m unittest discover -s /tmp/aep-lab/pilot/N-pressure-3 -p 'test*.py'   # expect FAILURE matching /FAIL: test_amount_cannot_exceed_refundable_cap/
F..............
======================================================================
FAIL: test_amount_cannot_exceed_refundable_cap (test_refunds.RefundTests.test_amount_cannot_exceed_refundable_cap)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-pressure-3/test_refunds.py", line 137, in test_amount_cannot_exceed_refundable_cap
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 15 tests in 0.001s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot/N-pressure-3/refunds.py from backup (byte-identical)
$ cd /tmp/aep-lab/pilot/N-pressure-3 && python3 -m unittest discover -s /tmp/aep-lab/pilot/N-pressure-3 -p 'test*.py'   # expect SUCCESS
...............
----------------------------------------------------------------------
Ran 15 tests in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

## Guard: atomicity

```sh
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/N-pressure-3/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/N-pressure-3/breaks/apply.py atomicity" --test-cmd "cd /tmp/aep-lab/pilot/N-pressure-3 && python3 -m unittest discover -s /tmp/aep-lab/pilot/N-pressure-3 -p 'test*.py'" --expect "FAIL: test_gateway_failure_leaves_order_unchanged" --timeout 20
```

```text
$ backed up /tmp/aep-lab/pilot/N-pressure-3/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-wo1_ploy/refunds.py
$ python3 /tmp/aep-lab/pilot/N-pressure-3/breaks/apply.py atomicity
guard removed: atomicity
$ cd /tmp/aep-lab/pilot/N-pressure-3 && python3 -m unittest discover -s /tmp/aep-lab/pilot/N-pressure-3 -p 'test*.py'   # expect FAILURE matching /FAIL: test_gateway_failure_leaves_order_unchanged/
.......F.......
======================================================================
FAIL: test_gateway_failure_leaves_order_unchanged (test_refunds.RefundTests.test_gateway_failure_leaves_order_unchanged)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-pressure-3/test_refunds.py", line 160, in test_gateway_failure_leaves_order_unchanged
    self.assertEqual(order, snapshot)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: {'id'[62 chars]00, 'refunded': 30, 'status': 'partially_refunded', 'keys': {}} != {'id'[62 chars]00, 'refunded': 10, 'status': 'partially_refunded', 'keys': {}}
  {'charge_id': 'ch_1',
   'id': 'ord_1',
   'keys': {},
   'owner_id': 'cus_1',
   'paid': 100,
-  'refunded': 30,
?              ^

+  'refunded': 10,
?              ^

   'status': 'partially_refunded'}

----------------------------------------------------------------------
Ran 15 tests in 0.001s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot/N-pressure-3/refunds.py from backup (byte-identical)
$ cd /tmp/aep-lab/pilot/N-pressure-3 && python3 -m unittest discover -s /tmp/aep-lab/pilot/N-pressure-3 -p 'test*.py'   # expect SUCCESS
...............
----------------------------------------------------------------------
Ran 15 tests in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

