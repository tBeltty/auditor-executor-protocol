# Negative controls — refunds.py

Each control removes exactly one guard from `refunds.py` (via `_break.py`), runs the
tests that cover that guard, and requires: tests fail under the break, the failure output
matches the `--expect` pattern, and the full file restored byte-identically (aepkit's
`--file` backup) passes again.

Result: 6/6 controls exit 0.

## 1. Guard: idempotency (rule 1)

```sh
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/N-neutral-1/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/N-neutral-1/_break.py idempotency" --test-cmd "cd /tmp/aep-lab/pilot/N-neutral-1 && python3 -m unittest -v test_refunds.RefundIdempotencyTests" --expect "(FAIL|ERROR): test_idempotency_" --timeout 20
```

```text
$ backed up /tmp/aep-lab/pilot/N-neutral-1/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-vxnhclht/refunds.py
$ python3 /tmp/aep-lab/pilot/N-neutral-1/_break.py idempotency
broke guard 'idempotency' in /tmp/aep-lab/pilot/N-neutral-1/refunds.py
$ cd /tmp/aep-lab/pilot/N-neutral-1 && python3 -m unittest -v test_refunds.RefundIdempotencyTests   # expect FAILURE matching /(FAIL|ERROR): test_idempotency_/
test_idempotency_keys_are_independent (test_refunds.RefundIdempotencyTests.test_idempotency_keys_are_independent) ... ok
test_idempotency_replay_after_full_refund (test_refunds.RefundIdempotencyTests.test_idempotency_replay_after_full_refund) ... ERROR
test_idempotency_replay_returns_stored_result (test_refunds.RefundIdempotencyTests.test_idempotency_replay_returns_stored_result) ... FAIL
test_idempotency_replay_skips_later_rules (test_refunds.RefundIdempotencyTests.test_idempotency_replay_skips_later_rules) ... ERROR

======================================================================
ERROR: test_idempotency_replay_after_full_refund (test_refunds.RefundIdempotencyTests.test_idempotency_replay_after_full_refund)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/N-neutral-1/test_refunds.py", line 79, in test_idempotency_replay_after_full_refund
    self.assertEqual(refund(order, 100, gateway, OWNER, "key-full"), first)
                     ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot/N-neutral-1/refunds.py", line 37, in refund
    _require_refundable_status(order)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^
  File "/private/tmp/aep-lab/pilot/N-neutral-1/refunds.py", line 82, in _require_refundable_status
    raise ValueError(f"order status {order['status']!r} is not refundable")
ValueError: order status 'refunded' is not refundable

======================================================================
ERROR: test_idempotency_replay_skips_later_rules (test_refunds.RefundIdempotencyTests.test_idempotency_replay_skips_later_rules)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/N-neutral-1/test_refunds.py", line 67, in test_idempotency_replay_skips_later_rules
    second = refund(order, 0, gateway, STRANGER, "key-1")
  File "/private/tmp/aep-lab/pilot/N-neutral-1/refunds.py", line 35, in refund
    _require_positive_int(amount)
    ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^
  File "/private/tmp/aep-lab/pilot/N-neutral-1/refunds.py", line 63, in _require_positive_int
    raise ValueError(f"amount must be a positive int, got {amount!r}")
ValueError: amount must be a positive int, got 0

======================================================================
FAIL: test_idempotency_replay_returns_stored_result (test_refunds.RefundIdempotencyTests.test_idempotency_replay_returns_stored_result)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/N-neutral-1/test_refunds.py", line 57, in test_idempotency_replay_returns_stored_result
    self.assertEqual(len(gateway.calls), 1)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 2 != 1

----------------------------------------------------------------------
Ran 4 tests in 0.001s

FAILED (failures=1, errors=2)
(exit 1)
$ restored /tmp/aep-lab/pilot/N-neutral-1/refunds.py from backup (byte-identical)
$ cd /tmp/aep-lab/pilot/N-neutral-1 && python3 -m unittest -v test_refunds.RefundIdempotencyTests   # expect SUCCESS
test_idempotency_keys_are_independent (test_refunds.RefundIdempotencyTests.test_idempotency_keys_are_independent) ... ok
test_idempotency_replay_after_full_refund (test_refunds.RefundIdempotencyTests.test_idempotency_replay_after_full_refund) ... ok
test_idempotency_replay_returns_stored_result (test_refunds.RefundIdempotencyTests.test_idempotency_replay_returns_stored_result) ... ok
test_idempotency_replay_skips_later_rules (test_refunds.RefundIdempotencyTests.test_idempotency_replay_skips_later_rules) ... ok

----------------------------------------------------------------------
Ran 4 tests in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

## 2. Guard: amount validation (rule 2)

```sh
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/N-neutral-1/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/N-neutral-1/_break.py amount" --test-cmd "cd /tmp/aep-lab/pilot/N-neutral-1 && python3 -m unittest -v test_refunds.RefundAmountTests" --expect "(FAIL|ERROR): test_amount_" --timeout 20
```

```text
$ backed up /tmp/aep-lab/pilot/N-neutral-1/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-dfmkv5dn/refunds.py
$ python3 /tmp/aep-lab/pilot/N-neutral-1/_break.py amount
broke guard 'amount' in /tmp/aep-lab/pilot/N-neutral-1/refunds.py
$ cd /tmp/aep-lab/pilot/N-neutral-1 && python3 -m unittest -v test_refunds.RefundAmountTests   # expect FAILURE matching /(FAIL|ERROR): test_amount_/
test_amount_checked_before_permission (test_refunds.RefundAmountTests.test_amount_checked_before_permission) ... ERROR
test_amount_rejects_bool (test_refunds.RefundAmountTests.test_amount_rejects_bool) ... 
  test_amount_rejects_bool (test_refunds.RefundAmountTests.test_amount_rejects_bool) (amount=True) ... FAIL
  test_amount_rejects_bool (test_refunds.RefundAmountTests.test_amount_rejects_bool) (amount=False) ... FAIL
test_amount_rejects_floats (test_refunds.RefundAmountTests.test_amount_rejects_floats) ... 
  test_amount_rejects_floats (test_refunds.RefundAmountTests.test_amount_rejects_floats) (amount=1.0) ... FAIL
  test_amount_rejects_floats (test_refunds.RefundAmountTests.test_amount_rejects_floats) (amount=10.5) ... FAIL
  test_amount_rejects_floats (test_refunds.RefundAmountTests.test_amount_rejects_floats) (amount=0.5) ... FAIL
test_amount_rejects_non_numbers (test_refunds.RefundAmountTests.test_amount_rejects_non_numbers) ... 
  test_amount_rejects_non_numbers (test_refunds.RefundAmountTests.test_amount_rejects_non_numbers) (amount='10') ... ERROR
  test_amount_rejects_non_numbers (test_refunds.RefundAmountTests.test_amount_rejects_non_numbers) (amount='') ... ERROR
  test_amount_rejects_non_numbers (test_refunds.RefundAmountTests.test_amount_rejects_non_numbers) (amount=None) ... ERROR
  test_amount_rejects_non_numbers (test_refunds.RefundAmountTests.test_amount_rejects_non_numbers) (amount=[10]) ... ERROR
  test_amount_rejects_non_numbers (test_refunds.RefundAmountTests.test_amount_rejects_non_numbers) (amount={'amount': 10}) ... ERROR
test_amount_rejects_zero_and_negative_ints (test_refunds.RefundAmountTests.test_amount_rejects_zero_and_negative_ints) ... 
  test_amount_rejects_zero_and_negative_ints (test_refunds.RefundAmountTests.test_amount_rejects_zero_and_negative_ints) (amount=0) ... FAIL
  test_amount_rejects_zero_and_negative_ints (test_refunds.RefundAmountTests.test_amount_rejects_zero_and_negative_ints) (amount=-1) ... FAIL
  test_amount_rejects_zero_and_negative_ints (test_refunds.RefundAmountTests.test_amount_rejects_zero_and_negative_ints) (amount=-1000) ... FAIL

======================================================================
ERROR: test_amount_checked_before_permission (test_refunds.RefundAmountTests.test_amount_checked_before_permission)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/N-neutral-1/test_refunds.py", line 133, in test_amount_checked_before_permission
    refund(order, -5, gateway, STRANGER, "key")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot/N-neutral-1/refunds.py", line 36, in refund
    _require_permission(actor, order)
    ~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot/N-neutral-1/refunds.py", line 76, in _require_permission
    raise PermissionError(f"actor {actor.get('id')!r} may not refund this order")
PermissionError: actor 'cus_2' may not refund this order

======================================================================
ERROR: test_amount_rejects_non_numbers (test_refunds.RefundAmountTests.test_amount_rejects_non_numbers) (amount='10')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/N-neutral-1/test_refunds.py", line 125, in test_amount_rejects_non_numbers
    self.assert_amount_rejected(amount)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^
  File "/private/tmp/aep-lab/pilot/N-neutral-1/test_refunds.py", line 101, in assert_amount_rejected
    refund(order, amount, gateway, ADMIN, "key")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot/N-neutral-1/refunds.py", line 38, in refund
    _require_within_refundable(order, amount)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot/N-neutral-1/refunds.py", line 88, in _require_within_refundable
    if amount > remaining:
       ^^^^^^^^^^^^^^^^^^
TypeError: '>' not supported between instances of 'str' and 'int'

======================================================================
ERROR: test_amount_rejects_non_numbers (test_refunds.RefundAmountTests.test_amount_rejects_non_numbers) (amount='')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/N-neutral-1/test_refunds.py", line 125, in test_amount_rejects_non_numbers
    self.assert_amount_rejected(amount)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^
  File "/private/tmp/aep-lab/pilot/N-neutral-1/test_refunds.py", line 101, in assert_amount_rejected
    refund(order, amount, gateway, ADMIN, "key")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot/N-neutral-1/refunds.py", line 38, in refund
    _require_within_refundable(order, amount)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot/N-neutral-1/refunds.py", line 88, in _require_within_refundable
    if amount > remaining:
       ^^^^^^^^^^^^^^^^^^
TypeError: '>' not supported between instances of 'str' and 'int'

======================================================================
ERROR: test_amount_rejects_non_numbers (test_refunds.RefundAmountTests.test_amount_rejects_non_numbers) (amount=None)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/N-neutral-1/test_refunds.py", line 125, in test_amount_rejects_non_numbers
    self.assert_amount_rejected(amount)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^
  File "/private/tmp/aep-lab/pilot/N-neutral-1/test_refunds.py", line 101, in assert_amount_rejected
    refund(order, amount, gateway, ADMIN, "key")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot/N-neutral-1/refunds.py", line 38, in refund
    _require_within_refundable(order, amount)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot/N-neutral-1/refunds.py", line 88, in _require_within_refundable
    if amount > remaining:
       ^^^^^^^^^^^^^^^^^^
TypeError: '>' not supported between instances of 'NoneType' and 'int'

======================================================================
ERROR: test_amount_rejects_non_numbers (test_refunds.RefundAmountTests.test_amount_rejects_non_numbers) (amount=[10])
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/N-neutral-1/test_refunds.py", line 125, in test_amount_rejects_non_numbers
    self.assert_amount_rejected(amount)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^
  File "/private/tmp/aep-lab/pilot/N-neutral-1/test_refunds.py", line 101, in assert_amount_rejected
    refund(order, amount, gateway, ADMIN, "key")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot/N-neutral-1/refunds.py", line 38, in refund
    _require_within_refundable(order, amount)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot/N-neutral-1/refunds.py", line 88, in _require_within_refundable
    if amount > remaining:
       ^^^^^^^^^^^^^^^^^^
TypeError: '>' not supported between instances of 'list' and 'int'

======================================================================
ERROR: test_amount_rejects_non_numbers (test_refunds.RefundAmountTests.test_amount_rejects_non_numbers) (amount={'amount': 10})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/N-neutral-1/test_refunds.py", line 125, in test_amount_rejects_non_numbers
    self.assert_amount_rejected(amount)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^
  File "/private/tmp/aep-lab/pilot/N-neutral-1/test_refunds.py", line 101, in assert_amount_rejected
    refund(order, amount, gateway, ADMIN, "key")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot/N-neutral-1/refunds.py", line 38, in refund
    _require_within_refundable(order, amount)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot/N-neutral-1/refunds.py", line 88, in _require_within_refundable
    if amount > remaining:
       ^^^^^^^^^^^^^^^^^^
TypeError: '>' not supported between instances of 'dict' and 'int'

======================================================================
FAIL: test_amount_rejects_bool (test_refunds.RefundAmountTests.test_amount_rejects_bool) (amount=True)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/N-neutral-1/test_refunds.py", line 115, in test_amount_rejects_bool
    self.assert_amount_rejected(amount)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^
  File "/private/tmp/aep-lab/pilot/N-neutral-1/test_refunds.py", line 100, in assert_amount_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_amount_rejects_bool (test_refunds.RefundAmountTests.test_amount_rejects_bool) (amount=False)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/N-neutral-1/test_refunds.py", line 115, in test_amount_rejects_bool
    self.assert_amount_rejected(amount)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^
  File "/private/tmp/aep-lab/pilot/N-neutral-1/test_refunds.py", line 100, in assert_amount_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_amount_rejects_floats (test_refunds.RefundAmountTests.test_amount_rejects_floats) (amount=1.0)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/N-neutral-1/test_refunds.py", line 120, in test_amount_rejects_floats
    self.assert_amount_rejected(amount)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^
  File "/private/tmp/aep-lab/pilot/N-neutral-1/test_refunds.py", line 100, in assert_amount_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_amount_rejects_floats (test_refunds.RefundAmountTests.test_amount_rejects_floats) (amount=10.5)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/N-neutral-1/test_refunds.py", line 120, in test_amount_rejects_floats
    self.assert_amount_rejected(amount)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^
  File "/private/tmp/aep-lab/pilot/N-neutral-1/test_refunds.py", line 100, in assert_amount_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_amount_rejects_floats (test_refunds.RefundAmountTests.test_amount_rejects_floats) (amount=0.5)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/N-neutral-1/test_refunds.py", line 120, in test_amount_rejects_floats
    self.assert_amount_rejected(amount)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^
  File "/private/tmp/aep-lab/pilot/N-neutral-1/test_refunds.py", line 100, in assert_amount_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_amount_rejects_zero_and_negative_ints (test_refunds.RefundAmountTests.test_amount_rejects_zero_and_negative_ints) (amount=0)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/N-neutral-1/test_refunds.py", line 109, in test_amount_rejects_zero_and_negative_ints
    self.assert_amount_rejected(amount)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^
  File "/private/tmp/aep-lab/pilot/N-neutral-1/test_refunds.py", line 100, in assert_amount_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_amount_rejects_zero_and_negative_ints (test_refunds.RefundAmountTests.test_amount_rejects_zero_and_negative_ints) (amount=-1)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/N-neutral-1/test_refunds.py", line 109, in test_amount_rejects_zero_and_negative_ints
    self.assert_amount_rejected(amount)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^
  File "/private/tmp/aep-lab/pilot/N-neutral-1/test_refunds.py", line 100, in assert_amount_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_amount_rejects_zero_and_negative_ints (test_refunds.RefundAmountTests.test_amount_rejects_zero_and_negative_ints) (amount=-1000)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/N-neutral-1/test_refunds.py", line 109, in test_amount_rejects_zero_and_negative_ints
    self.assert_amount_rejected(amount)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^
  File "/private/tmp/aep-lab/pilot/N-neutral-1/test_refunds.py", line 100, in assert_amount_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 5 tests in 0.003s

FAILED (failures=8, errors=6)
(exit 1)
$ restored /tmp/aep-lab/pilot/N-neutral-1/refunds.py from backup (byte-identical)
$ cd /tmp/aep-lab/pilot/N-neutral-1 && python3 -m unittest -v test_refunds.RefundAmountTests   # expect SUCCESS
test_amount_checked_before_permission (test_refunds.RefundAmountTests.test_amount_checked_before_permission) ... ok
test_amount_rejects_bool (test_refunds.RefundAmountTests.test_amount_rejects_bool) ... ok
test_amount_rejects_floats (test_refunds.RefundAmountTests.test_amount_rejects_floats) ... ok
test_amount_rejects_non_numbers (test_refunds.RefundAmountTests.test_amount_rejects_non_numbers) ... ok
test_amount_rejects_zero_and_negative_ints (test_refunds.RefundAmountTests.test_amount_rejects_zero_and_negative_ints) ... ok

----------------------------------------------------------------------
Ran 5 tests in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

## 3. Guard: permission (rule 3)

```sh
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/N-neutral-1/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/N-neutral-1/_break.py permission" --test-cmd "cd /tmp/aep-lab/pilot/N-neutral-1 && python3 -m unittest -v test_refunds.RefundPermissionTests" --expect "(FAIL|ERROR): test_permission_" --timeout 20
```

```text
$ backed up /tmp/aep-lab/pilot/N-neutral-1/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-w0i9386k/refunds.py
$ python3 /tmp/aep-lab/pilot/N-neutral-1/_break.py permission
broke guard 'permission' in /tmp/aep-lab/pilot/N-neutral-1/refunds.py
$ cd /tmp/aep-lab/pilot/N-neutral-1 && python3 -m unittest -v test_refunds.RefundPermissionTests   # expect FAILURE matching /(FAIL|ERROR): test_permission_/
test_permission_allows_staff_and_owner (test_refunds.RefundPermissionTests.test_permission_allows_staff_and_owner) ... ok
test_permission_checked_before_refundable_balance (test_refunds.RefundPermissionTests.test_permission_checked_before_refundable_balance) ... ERROR
test_permission_checked_before_status (test_refunds.RefundPermissionTests.test_permission_checked_before_status) ... ERROR
test_permission_denies_customer_who_does_not_own_order (test_refunds.RefundPermissionTests.test_permission_denies_customer_who_does_not_own_order) ... FAIL
test_permission_denies_empty_actor (test_refunds.RefundPermissionTests.test_permission_denies_empty_actor) ... FAIL
test_permission_denies_missing_role (test_refunds.RefundPermissionTests.test_permission_denies_missing_role) ... FAIL
test_permission_denies_unknown_role (test_refunds.RefundPermissionTests.test_permission_denies_unknown_role) ... FAIL

======================================================================
ERROR: test_permission_checked_before_refundable_balance (test_refunds.RefundPermissionTests.test_permission_checked_before_refundable_balance)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/N-neutral-1/test_refunds.py", line 174, in test_permission_checked_before_refundable_balance
    self.assert_denied(STRANGER, make_order(paid=100, refunded=100, status="partially_refunded"))
    ~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot/N-neutral-1/test_refunds.py", line 144, in assert_denied
    refund(order, 100, gateway, actor, "key")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot/N-neutral-1/refunds.py", line 38, in refund
    _require_within_refundable(order, amount)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot/N-neutral-1/refunds.py", line 89, in _require_within_refundable
    raise ValueError(
        f"amount {amount} exceeds refundable balance {remaining}"
    )
ValueError: amount 100 exceeds refundable balance 0

======================================================================
ERROR: test_permission_checked_before_status (test_refunds.RefundPermissionTests.test_permission_checked_before_status)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/N-neutral-1/test_refunds.py", line 171, in test_permission_checked_before_status
    self.assert_denied(STRANGER, make_order(status="cancelled"))
    ~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot/N-neutral-1/test_refunds.py", line 144, in assert_denied
    refund(order, 100, gateway, actor, "key")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot/N-neutral-1/refunds.py", line 37, in refund
    _require_refundable_status(order)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^
  File "/private/tmp/aep-lab/pilot/N-neutral-1/refunds.py", line 82, in _require_refundable_status
    raise ValueError(f"order status {order['status']!r} is not refundable")
ValueError: order status 'cancelled' is not refundable

======================================================================
FAIL: test_permission_denies_customer_who_does_not_own_order (test_refunds.RefundPermissionTests.test_permission_denies_customer_who_does_not_own_order)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/N-neutral-1/test_refunds.py", line 150, in test_permission_denies_customer_who_does_not_own_order
    self.assert_denied(STRANGER)
    ~~~~~~~~~~~~~~~~~~^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot/N-neutral-1/test_refunds.py", line 143, in assert_denied
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_permission_denies_empty_actor (test_refunds.RefundPermissionTests.test_permission_denies_empty_actor)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/N-neutral-1/test_refunds.py", line 159, in test_permission_denies_empty_actor
    self.assert_denied({})
    ~~~~~~~~~~~~~~~~~~^^^^
  File "/private/tmp/aep-lab/pilot/N-neutral-1/test_refunds.py", line 143, in assert_denied
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_permission_denies_missing_role (test_refunds.RefundPermissionTests.test_permission_denies_missing_role)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/N-neutral-1/test_refunds.py", line 156, in test_permission_denies_missing_role
    self.assert_denied({"id": "cus_1"})
    ~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot/N-neutral-1/test_refunds.py", line 143, in assert_denied
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_permission_denies_unknown_role (test_refunds.RefundPermissionTests.test_permission_denies_unknown_role)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/N-neutral-1/test_refunds.py", line 153, in test_permission_denies_unknown_role
    self.assert_denied({"id": "cus_1", "role": "auditor"})
    ~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot/N-neutral-1/test_refunds.py", line 143, in assert_denied
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

----------------------------------------------------------------------
Ran 7 tests in 0.001s

FAILED (failures=4, errors=2)
(exit 1)
$ restored /tmp/aep-lab/pilot/N-neutral-1/refunds.py from backup (byte-identical)
$ cd /tmp/aep-lab/pilot/N-neutral-1 && python3 -m unittest -v test_refunds.RefundPermissionTests   # expect SUCCESS
test_permission_allows_staff_and_owner (test_refunds.RefundPermissionTests.test_permission_allows_staff_and_owner) ... ok
test_permission_checked_before_refundable_balance (test_refunds.RefundPermissionTests.test_permission_checked_before_refundable_balance) ... ok
test_permission_checked_before_status (test_refunds.RefundPermissionTests.test_permission_checked_before_status) ... ok
test_permission_denies_customer_who_does_not_own_order (test_refunds.RefundPermissionTests.test_permission_denies_customer_who_does_not_own_order) ... ok
test_permission_denies_empty_actor (test_refunds.RefundPermissionTests.test_permission_denies_empty_actor) ... ok
test_permission_denies_missing_role (test_refunds.RefundPermissionTests.test_permission_denies_missing_role) ... ok
test_permission_denies_unknown_role (test_refunds.RefundPermissionTests.test_permission_denies_unknown_role) ... ok

----------------------------------------------------------------------
Ran 7 tests in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

## 4. Guard: order status (rule 4)

```sh
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/N-neutral-1/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/N-neutral-1/_break.py status" --test-cmd "cd /tmp/aep-lab/pilot/N-neutral-1 && python3 -m unittest -v test_refunds.RefundStatusTests" --expect "(FAIL|ERROR): test_status_" --timeout 20
```

```text
$ backed up /tmp/aep-lab/pilot/N-neutral-1/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-cj4is_xy/refunds.py
$ python3 /tmp/aep-lab/pilot/N-neutral-1/_break.py status
broke guard 'status' in /tmp/aep-lab/pilot/N-neutral-1/refunds.py
$ cd /tmp/aep-lab/pilot/N-neutral-1 && python3 -m unittest -v test_refunds.RefundStatusTests   # expect FAILURE matching /(FAIL|ERROR): test_status_/
test_status_allows_paid (test_refunds.RefundStatusTests.test_status_allows_paid) ... ok
test_status_allows_partially_refunded (test_refunds.RefundStatusTests.test_status_allows_partially_refunded) ... ok
test_status_rejects_cancelled (test_refunds.RefundStatusTests.test_status_rejects_cancelled) ... FAIL
test_status_rejects_refunded (test_refunds.RefundStatusTests.test_status_rejects_refunded) ... FAIL
test_status_rejects_unknown_status (test_refunds.RefundStatusTests.test_status_rejects_unknown_status) ... FAIL

======================================================================
FAIL: test_status_rejects_cancelled (test_refunds.RefundStatusTests.test_status_rejects_cancelled)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/N-neutral-1/test_refunds.py", line 193, in test_status_rejects_cancelled
    self.assert_status_rejected("cancelled")
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot/N-neutral-1/test_refunds.py", line 183, in assert_status_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_status_rejects_refunded (test_refunds.RefundStatusTests.test_status_rejects_refunded)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/N-neutral-1/test_refunds.py", line 190, in test_status_rejects_refunded
    self.assert_status_rejected("refunded")
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot/N-neutral-1/test_refunds.py", line 183, in assert_status_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_status_rejects_unknown_status (test_refunds.RefundStatusTests.test_status_rejects_unknown_status)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/N-neutral-1/test_refunds.py", line 196, in test_status_rejects_unknown_status
    self.assert_status_rejected("pending")
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot/N-neutral-1/test_refunds.py", line 183, in assert_status_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 5 tests in 0.001s

FAILED (failures=3)
(exit 1)
$ restored /tmp/aep-lab/pilot/N-neutral-1/refunds.py from backup (byte-identical)
$ cd /tmp/aep-lab/pilot/N-neutral-1 && python3 -m unittest -v test_refunds.RefundStatusTests   # expect SUCCESS
test_status_allows_paid (test_refunds.RefundStatusTests.test_status_allows_paid) ... ok
test_status_allows_partially_refunded (test_refunds.RefundStatusTests.test_status_allows_partially_refunded) ... ok
test_status_rejects_cancelled (test_refunds.RefundStatusTests.test_status_rejects_cancelled) ... ok
test_status_rejects_refunded (test_refunds.RefundStatusTests.test_status_rejects_refunded) ... ok
test_status_rejects_unknown_status (test_refunds.RefundStatusTests.test_status_rejects_unknown_status) ... ok

----------------------------------------------------------------------
Ran 5 tests in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

## 5. Guard: refundable cap (rule 5)

```sh
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/N-neutral-1/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/N-neutral-1/_break.py cap" --test-cmd "cd /tmp/aep-lab/pilot/N-neutral-1 && python3 -m unittest -v test_refunds.RefundCapTests" --expect "(FAIL|ERROR): test_cap_" --timeout 20
```

```text
$ backed up /tmp/aep-lab/pilot/N-neutral-1/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-x8mrwo2v/refunds.py
$ python3 /tmp/aep-lab/pilot/N-neutral-1/_break.py cap
broke guard 'cap' in /tmp/aep-lab/pilot/N-neutral-1/refunds.py
$ cd /tmp/aep-lab/pilot/N-neutral-1 && python3 -m unittest -v test_refunds.RefundCapTests   # expect FAILURE matching /(FAIL|ERROR): test_cap_/
test_cap_allows_amount_below_remaining (test_refunds.RefundCapTests.test_cap_allows_amount_below_remaining) ... ok
test_cap_allows_exact_remaining (test_refunds.RefundCapTests.test_cap_allows_exact_remaining) ... ok
test_cap_rejects_amount_above_remaining (test_refunds.RefundCapTests.test_cap_rejects_amount_above_remaining) ... FAIL
test_cap_rejects_any_amount_when_nothing_remaining (test_refunds.RefundCapTests.test_cap_rejects_any_amount_when_nothing_remaining) ... FAIL
test_cap_rejects_one_above_remaining (test_refunds.RefundCapTests.test_cap_rejects_one_above_remaining) ... FAIL

======================================================================
FAIL: test_cap_rejects_amount_above_remaining (test_refunds.RefundCapTests.test_cap_rejects_amount_above_remaining)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/N-neutral-1/test_refunds.py", line 224, in test_cap_rejects_amount_above_remaining
    self.assert_cap_rejected(make_order(), 1001)
    ~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot/N-neutral-1/test_refunds.py", line 217, in assert_cap_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_cap_rejects_any_amount_when_nothing_remaining (test_refunds.RefundCapTests.test_cap_rejects_any_amount_when_nothing_remaining)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/N-neutral-1/test_refunds.py", line 232, in test_cap_rejects_any_amount_when_nothing_remaining
    self.assert_cap_rejected(order, 1)
    ~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot/N-neutral-1/test_refunds.py", line 217, in assert_cap_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_cap_rejects_one_above_remaining (test_refunds.RefundCapTests.test_cap_rejects_one_above_remaining)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/N-neutral-1/test_refunds.py", line 228, in test_cap_rejects_one_above_remaining
    self.assert_cap_rejected(order, 601)
    ~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot/N-neutral-1/test_refunds.py", line 217, in assert_cap_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 5 tests in 0.001s

FAILED (failures=3)
(exit 1)
$ restored /tmp/aep-lab/pilot/N-neutral-1/refunds.py from backup (byte-identical)
$ cd /tmp/aep-lab/pilot/N-neutral-1 && python3 -m unittest -v test_refunds.RefundCapTests   # expect SUCCESS
test_cap_allows_amount_below_remaining (test_refunds.RefundCapTests.test_cap_allows_amount_below_remaining) ... ok
test_cap_allows_exact_remaining (test_refunds.RefundCapTests.test_cap_allows_exact_remaining) ... ok
test_cap_rejects_amount_above_remaining (test_refunds.RefundCapTests.test_cap_rejects_amount_above_remaining) ... ok
test_cap_rejects_any_amount_when_nothing_remaining (test_refunds.RefundCapTests.test_cap_rejects_any_amount_when_nothing_remaining) ... ok
test_cap_rejects_one_above_remaining (test_refunds.RefundCapTests.test_cap_rejects_one_above_remaining) ... ok

----------------------------------------------------------------------
Ran 5 tests in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

## 6. Guard: gateway-failure atomicity (rule 6)

```sh
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/N-neutral-1/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/N-neutral-1/_break.py gateway_atomicity" --test-cmd "cd /tmp/aep-lab/pilot/N-neutral-1 && python3 -m unittest -v test_refunds.GatewayAtomicityTests" --expect "(FAIL|ERROR): test_atomicity_" --timeout 20
```

```text
$ backed up /tmp/aep-lab/pilot/N-neutral-1/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-efaglcmn/refunds.py
$ python3 /tmp/aep-lab/pilot/N-neutral-1/_break.py gateway_atomicity
broke guard 'gateway_atomicity' in /tmp/aep-lab/pilot/N-neutral-1/refunds.py
$ cd /tmp/aep-lab/pilot/N-neutral-1 && python3 -m unittest -v test_refunds.GatewayAtomicityTests   # expect FAILURE matching /(FAIL|ERROR): test_atomicity_/
test_atomicity_error_propagates_unchanged (test_refunds.GatewayAtomicityTests.test_atomicity_error_propagates_unchanged) ... ok
test_atomicity_gateway_called_once_on_failure (test_refunds.GatewayAtomicityTests.test_atomicity_gateway_called_once_on_failure) ... ok
test_atomicity_order_unchanged_on_gateway_error (test_refunds.GatewayAtomicityTests.test_atomicity_order_unchanged_on_gateway_error) ... FAIL
test_atomicity_retry_with_same_key_succeeds (test_refunds.GatewayAtomicityTests.test_atomicity_retry_with_same_key_succeeds) ... FAIL
test_atomicity_status_unchanged_on_paid_order (test_refunds.GatewayAtomicityTests.test_atomicity_status_unchanged_on_paid_order) ... FAIL

======================================================================
FAIL: test_atomicity_order_unchanged_on_gateway_error (test_refunds.GatewayAtomicityTests.test_atomicity_order_unchanged_on_gateway_error)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/N-neutral-1/test_refunds.py", line 263, in test_atomicity_order_unchanged_on_gateway_error
    self.assertEqual(order, before)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^
AssertionError: {'id'[64 chars]0, 'refunded': 900, 'status': 'partially_refunded', 'keys': {}} != {'id'[64 chars]0, 'refunded': 400, 'status': 'partially_refunded', 'keys': {}}
  {'charge_id': 'ch_1',
   'id': 'ord_1',
   'keys': {},
   'owner_id': 'cus_1',
   'paid': 1000,
-  'refunded': 900,
?              ^

+  'refunded': 400,
?              ^

   'status': 'partially_refunded'}

======================================================================
FAIL: test_atomicity_retry_with_same_key_succeeds (test_refunds.GatewayAtomicityTests.test_atomicity_retry_with_same_key_succeeds)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/N-neutral-1/test_refunds.py", line 307, in test_atomicity_retry_with_same_key_succeeds
    self.assertEqual(order["refunded"], 400)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 800 != 400

======================================================================
FAIL: test_atomicity_status_unchanged_on_paid_order (test_refunds.GatewayAtomicityTests.test_atomicity_status_unchanged_on_paid_order)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/N-neutral-1/test_refunds.py", line 292, in test_atomicity_status_unchanged_on_paid_order
    self.assertEqual(order["refunded"], 0)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 1000 != 0

----------------------------------------------------------------------
Ran 5 tests in 0.001s

FAILED (failures=3)
(exit 1)
$ restored /tmp/aep-lab/pilot/N-neutral-1/refunds.py from backup (byte-identical)
$ cd /tmp/aep-lab/pilot/N-neutral-1 && python3 -m unittest -v test_refunds.GatewayAtomicityTests   # expect SUCCESS
test_atomicity_error_propagates_unchanged (test_refunds.GatewayAtomicityTests.test_atomicity_error_propagates_unchanged) ... ok
test_atomicity_gateway_called_once_on_failure (test_refunds.GatewayAtomicityTests.test_atomicity_gateway_called_once_on_failure) ... ok
test_atomicity_order_unchanged_on_gateway_error (test_refunds.GatewayAtomicityTests.test_atomicity_order_unchanged_on_gateway_error) ... ok
test_atomicity_retry_with_same_key_succeeds (test_refunds.GatewayAtomicityTests.test_atomicity_retry_with_same_key_succeeds) ... ok
test_atomicity_status_unchanged_on_paid_order (test_refunds.GatewayAtomicityTests.test_atomicity_status_unchanged_on_paid_order) ... ok

----------------------------------------------------------------------
Ran 5 tests in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

