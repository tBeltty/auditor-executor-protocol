# Negative-control log — refunds.py

## Guard: idempotency

```sh
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/N-neutral-2/refunds.py --break-cmd "sed -i '' 's/^        return order\["keys"\]\[idempotency_key\]$/        pass/' /tmp/aep-lab/pilot/N-neutral-2/refunds.py" --test-cmd "cd /tmp/aep-lab/pilot/N-neutral-2 && python3 -m unittest discover -s /tmp/aep-lab/pilot/N-neutral-2 -p 'test*.py'" --expect "FAILED \(failures=" --timeout 20
```

```text
$ backed up /tmp/aep-lab/pilot/N-neutral-2/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-3yg_j31f/refunds.py
$ sed -i '' 's/^        return order\["keys"\]\[idempotency_key\]$/        pass/' /tmp/aep-lab/pilot/N-neutral-2/refunds.py

$ cd /tmp/aep-lab/pilot/N-neutral-2 && python3 -m unittest discover -s /tmp/aep-lab/pilot/N-neutral-2 -p 'test*.py'   # expect FAILURE matching /FAILED \(failures=/
.................EFE.................
======================================================================
ERROR: test_idempotency_is_checked_before_every_other_rule (test_refunds.IdempotencyGuardTests.test_idempotency_is_checked_before_every_other_rule)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-neutral-2/test_refunds.py", line 111, in test_idempotency_is_checked_before_every_other_rule
    self.assertIs(refund(order, -5, gateway, OTHER_CUSTOMER, "k"), stored)
                  ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/N-neutral-2/refunds.py", line 27, in refund
    raise ValueError("amount must be a positive int")
ValueError: amount must be a positive int

======================================================================
ERROR: test_repeat_of_completed_refund_returns_stored_result (test_refunds.IdempotencyGuardTests.test_repeat_of_completed_refund_returns_stored_result)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-neutral-2/test_refunds.py", line 121, in test_repeat_of_completed_refund_returns_stored_result
    self.assertIs(refund(order, 1, gateway, OWNER, "k"), first)
                  ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/N-neutral-2/refunds.py", line 39, in refund
    raise ValueError("order status %r is not refundable" % (order["status"],))
ValueError: order status 'refunded' is not refundable

======================================================================
FAIL: test_repeat_key_returns_stored_result_without_touching_anything (test_refunds.IdempotencyGuardTests.test_repeat_key_returns_stored_result_without_touching_anything)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-neutral-2/test_refunds.py", line 99, in test_repeat_key_returns_stored_result_without_touching_anything
    self.assertIs(result, stored)
    ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^
AssertionError: {'refund_id': 're_new', 'amount': 30, 'status': 'partially_refunded'} is not {'refund_id': 're_old', 'amount': 30, 'status': 'partially_refunded'}

----------------------------------------------------------------------
Ran 37 tests in 0.002s

FAILED (failures=1, errors=2)
(exit 1)
$ restored /tmp/aep-lab/pilot/N-neutral-2/refunds.py from backup (byte-identical)
$ cd /tmp/aep-lab/pilot/N-neutral-2 && python3 -m unittest discover -s /tmp/aep-lab/pilot/N-neutral-2 -p 'test*.py'   # expect SUCCESS
.....................................
----------------------------------------------------------------------
Ran 37 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

**Exit status: 0**

## Guard: amount validation

```sh
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/N-neutral-2/refunds.py --break-cmd "sed -i '' 's/^    if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:$/    if False:/' /tmp/aep-lab/pilot/N-neutral-2/refunds.py" --test-cmd "cd /tmp/aep-lab/pilot/N-neutral-2 && python3 -m unittest discover -s /tmp/aep-lab/pilot/N-neutral-2 -p 'test*.py'" --expect "FAILED \(failures=" --timeout 20
```

```text
$ backed up /tmp/aep-lab/pilot/N-neutral-2/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-ua841jnh/refunds.py
$ sed -i '' 's/^    if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:$/    if False:/' /tmp/aep-lab/pilot/N-neutral-2/refunds.py

$ cd /tmp/aep-lab/pilot/N-neutral-2 && python3 -m unittest discover -s /tmp/aep-lab/pilot/N-neutral-2 -p 'test*.py'   # expect FAILURE matching /FAILED \(failures=/
EFFFFE.F.............................
======================================================================
ERROR: test_amount_is_validated_before_permission (test_refunds.AmountValidationGuardTests.test_amount_is_validated_before_permission)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-neutral-2/test_refunds.py", line 163, in test_amount_is_validated_before_permission
    refund(order, 0, self.gateway, OTHER_CUSTOMER, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/N-neutral-2/refunds.py", line 35, in refund
    raise PermissionError("actor is not allowed to refund this order")
PermissionError: actor is not allowed to refund this order

======================================================================
ERROR: test_numeric_string_is_rejected (test_refunds.AmountValidationGuardTests.test_numeric_string_is_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-neutral-2/test_refunds.py", line 154, in test_numeric_string_is_rejected
    self.assert_rejected("10")
    ~~~~~~~~~~~~~~~~~~~~^^^^^^
  File "/tmp/aep-lab/pilot/N-neutral-2/test_refunds.py", line 134, in assert_rejected
    refund(self.order, amount, self.gateway, ADMIN, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/N-neutral-2/refunds.py", line 43, in refund
    if amount > remaining:
       ^^^^^^^^^^^^^^^^^^
TypeError: '>' not supported between instances of 'str' and 'int'

======================================================================
FAIL: test_bool_false_is_rejected (test_refunds.AmountValidationGuardTests.test_bool_false_is_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-neutral-2/test_refunds.py", line 148, in test_bool_false_is_rejected
    self.assert_rejected(False)
    ~~~~~~~~~~~~~~~~~~~~^^^^^^^
  File "/tmp/aep-lab/pilot/N-neutral-2/test_refunds.py", line 133, in assert_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_bool_true_is_rejected (test_refunds.AmountValidationGuardTests.test_bool_true_is_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-neutral-2/test_refunds.py", line 145, in test_bool_true_is_rejected
    self.assert_rejected(True)
    ~~~~~~~~~~~~~~~~~~~~^^^^^^
  File "/tmp/aep-lab/pilot/N-neutral-2/test_refunds.py", line 133, in assert_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_float_is_rejected (test_refunds.AmountValidationGuardTests.test_float_is_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-neutral-2/test_refunds.py", line 151, in test_float_is_rejected
    self.assert_rejected(10.0)
    ~~~~~~~~~~~~~~~~~~~~^^^^^^
  File "/tmp/aep-lab/pilot/N-neutral-2/test_refunds.py", line 133, in assert_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_negative_is_rejected (test_refunds.AmountValidationGuardTests.test_negative_is_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-neutral-2/test_refunds.py", line 142, in test_negative_is_rejected
    self.assert_rejected(-1)
    ~~~~~~~~~~~~~~~~~~~~^^^^
  File "/tmp/aep-lab/pilot/N-neutral-2/test_refunds.py", line 133, in assert_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_zero_is_rejected (test_refunds.AmountValidationGuardTests.test_zero_is_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-neutral-2/test_refunds.py", line 139, in test_zero_is_rejected
    self.assert_rejected(0)
    ~~~~~~~~~~~~~~~~~~~~^^^
  File "/tmp/aep-lab/pilot/N-neutral-2/test_refunds.py", line 133, in assert_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 37 tests in 0.002s

FAILED (failures=5, errors=2)
(exit 1)
$ restored /tmp/aep-lab/pilot/N-neutral-2/refunds.py from backup (byte-identical)
$ cd /tmp/aep-lab/pilot/N-neutral-2 && python3 -m unittest discover -s /tmp/aep-lab/pilot/N-neutral-2 -p 'test*.py'   # expect SUCCESS
.....................................
----------------------------------------------------------------------
Ran 37 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

**Exit status: 0**

## Guard: permission

```sh
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/N-neutral-2/refunds.py --break-cmd "sed -i '' 's/^    if not authorized:$/    if False:/' /tmp/aep-lab/pilot/N-neutral-2/refunds.py" --test-cmd "cd /tmp/aep-lab/pilot/N-neutral-2 && python3 -m unittest discover -s /tmp/aep-lab/pilot/N-neutral-2 -p 'test*.py'" --expect "FAILED \(failures=" --timeout 20
```

```text
$ backed up /tmp/aep-lab/pilot/N-neutral-2/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-duvj8wvc/refunds.py
$ sed -i '' 's/^    if not authorized:$/    if False:/' /tmp/aep-lab/pilot/N-neutral-2/refunds.py

$ cd /tmp/aep-lab/pilot/N-neutral-2 && python3 -m unittest discover -s /tmp/aep-lab/pilot/N-neutral-2 -p 'test*.py'   # expect FAILURE matching /FAILED \(failures=/
.....................FFFFF.E.........
======================================================================
ERROR: test_permission_is_checked_before_status (test_refunds.PermissionGuardTests.test_permission_is_checked_before_status)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-neutral-2/test_refunds.py", line 209, in test_permission_is_checked_before_status
    refund(order, 10, self.gateway, OTHER_CUSTOMER, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/N-neutral-2/refunds.py", line 39, in refund
    raise ValueError("order status %r is not refundable" % (order["status"],))
ValueError: order status 'cancelled' is not refundable

======================================================================
FAIL: test_customer_role_with_matching_wrong_id_is_denied (test_refunds.PermissionGuardTests.test_customer_role_with_matching_wrong_id_is_denied)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-neutral-2/test_refunds.py", line 195, in test_customer_role_with_matching_wrong_id_is_denied
    self.assert_denied({"id": "cust_2", "role": "customer"})
    ~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/N-neutral-2/test_refunds.py", line 174, in assert_denied
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_empty_actor_is_denied (test_refunds.PermissionGuardTests.test_empty_actor_is_denied)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-neutral-2/test_refunds.py", line 201, in test_empty_actor_is_denied
    self.assert_denied({})
    ~~~~~~~~~~~~~~~~~~^^^^
  File "/tmp/aep-lab/pilot/N-neutral-2/test_refunds.py", line 174, in assert_denied
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_matching_id_with_unknown_role_is_denied (test_refunds.PermissionGuardTests.test_matching_id_with_unknown_role_is_denied)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-neutral-2/test_refunds.py", line 198, in test_matching_id_with_unknown_role_is_denied
    self.assert_denied({"id": "cust_1", "role": "guest"})
    ~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/N-neutral-2/test_refunds.py", line 174, in assert_denied
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_missing_role_is_denied (test_refunds.PermissionGuardTests.test_missing_role_is_denied)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-neutral-2/test_refunds.py", line 204, in test_missing_role_is_denied
    self.assert_denied({"id": "cust_1"})
    ~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/N-neutral-2/test_refunds.py", line 174, in assert_denied
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_other_customer_is_denied (test_refunds.PermissionGuardTests.test_other_customer_is_denied)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-neutral-2/test_refunds.py", line 192, in test_other_customer_is_denied
    self.assert_denied(OTHER_CUSTOMER)
    ~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/N-neutral-2/test_refunds.py", line 174, in assert_denied
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

----------------------------------------------------------------------
Ran 37 tests in 0.002s

FAILED (failures=5, errors=1)
(exit 1)
$ restored /tmp/aep-lab/pilot/N-neutral-2/refunds.py from backup (byte-identical)
$ cd /tmp/aep-lab/pilot/N-neutral-2 && python3 -m unittest discover -s /tmp/aep-lab/pilot/N-neutral-2 -p 'test*.py'   # expect SUCCESS
.....................................
----------------------------------------------------------------------
Ran 37 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

**Exit status: 0**

## Guard: status

```sh
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/N-neutral-2/refunds.py --break-cmd "sed -i '' 's/^    if order\["status"\] not in _ALLOWED_STATUSES:$/    if False:/' /tmp/aep-lab/pilot/N-neutral-2/refunds.py" --test-cmd "cd /tmp/aep-lab/pilot/N-neutral-2 && python3 -m unittest discover -s /tmp/aep-lab/pilot/N-neutral-2 -p 'test*.py'" --expect "FAILED \(failures=" --timeout 20
```

```text
$ backed up /tmp/aep-lab/pilot/N-neutral-2/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-s6flnftx/refunds.py
$ sed -i '' 's/^    if order\["status"\] not in _ALLOWED_STATUSES:$/    if False:/' /tmp/aep-lab/pilot/N-neutral-2/refunds.py

$ cd /tmp/aep-lab/pilot/N-neutral-2 && python3 -m unittest discover -s /tmp/aep-lab/pilot/N-neutral-2 -p 'test*.py'   # expect FAILURE matching /FAILED \(failures=/
.................................FF..
======================================================================
FAIL: test_already_refunded_order_is_rejected (test_refunds.StatusGuardTests.test_already_refunded_order_is_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-neutral-2/test_refunds.py", line 229, in test_already_refunded_order_is_rejected
    self.assert_rejected("refunded")
    ~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/N-neutral-2/test_refunds.py", line 220, in assert_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_cancelled_order_is_rejected (test_refunds.StatusGuardTests.test_cancelled_order_is_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-neutral-2/test_refunds.py", line 226, in test_cancelled_order_is_rejected
    self.assert_rejected("cancelled")
    ~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/N-neutral-2/test_refunds.py", line 220, in assert_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 37 tests in 0.001s

FAILED (failures=2)
(exit 1)
$ restored /tmp/aep-lab/pilot/N-neutral-2/refunds.py from backup (byte-identical)
$ cd /tmp/aep-lab/pilot/N-neutral-2 && python3 -m unittest discover -s /tmp/aep-lab/pilot/N-neutral-2 -p 'test*.py'   # expect SUCCESS
.....................................
----------------------------------------------------------------------
Ran 37 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

**Exit status: 0**

## Guard: refundable cap

```sh
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/N-neutral-2/refunds.py --break-cmd "sed -i '' 's/^    if amount > remaining:$/    if False:/' /tmp/aep-lab/pilot/N-neutral-2/refunds.py" --test-cmd "cd /tmp/aep-lab/pilot/N-neutral-2 && python3 -m unittest discover -s /tmp/aep-lab/pilot/N-neutral-2 -p 'test*.py'" --expect "FAILED \(failures=" --timeout 20
```

```text
$ backed up /tmp/aep-lab/pilot/N-neutral-2/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-n3he02rf/refunds.py
$ sed -i '' 's/^    if amount > remaining:$/    if False:/' /tmp/aep-lab/pilot/N-neutral-2/refunds.py

$ cd /tmp/aep-lab/pilot/N-neutral-2 && python3 -m unittest discover -s /tmp/aep-lab/pilot/N-neutral-2 -p 'test*.py'   # expect FAILURE matching /FAILED \(failures=/
.............................F..F....
======================================================================
FAIL: test_any_amount_is_rejected_when_nothing_remains (test_refunds.RefundableCapGuardTests.test_any_amount_is_rejected_when_nothing_remains)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-neutral-2/test_refunds.py", line 269, in test_any_amount_is_rejected_when_nothing_remains
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_one_over_remainder_is_rejected (test_refunds.RefundableCapGuardTests.test_one_over_remainder_is_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-neutral-2/test_refunds.py", line 256, in test_one_over_remainder_is_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 37 tests in 0.001s

FAILED (failures=2)
(exit 1)
$ restored /tmp/aep-lab/pilot/N-neutral-2/refunds.py from backup (byte-identical)
$ cd /tmp/aep-lab/pilot/N-neutral-2 && python3 -m unittest discover -s /tmp/aep-lab/pilot/N-neutral-2 -p 'test*.py'   # expect SUCCESS
.....................................
----------------------------------------------------------------------
Ran 37 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

**Exit status: 0**

## Guard: gateway-failure atomicity

```sh
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/N-neutral-2/refunds.py --break-cmd "sed -i '' 's/^    try:$/    order["refunded"] += amount\n    try:/' /tmp/aep-lab/pilot/N-neutral-2/refunds.py" --test-cmd "cd /tmp/aep-lab/pilot/N-neutral-2 && python3 -m unittest discover -s /tmp/aep-lab/pilot/N-neutral-2 -p 'test*.py'" --expect "FAILED \(failures=" --timeout 20
```

```text
$ backed up /tmp/aep-lab/pilot/N-neutral-2/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-838hh0yn/refunds.py
$ sed -i '' 's/^    try:$/    order["refunded"] += amount\n    try:/' /tmp/aep-lab/pilot/N-neutral-2/refunds.py

$ cd /tmp/aep-lab/pilot/N-neutral-2 && python3 -m unittest discover -s /tmp/aep-lab/pilot/N-neutral-2 -p 'test*.py'   # expect FAILURE matching /FAILED \(failures=/
........F.FF.F.FE.............FF....F
======================================================================
ERROR: test_second_refund_completes_the_order (test_refunds.HappyPathTests.test_second_refund_completes_the_order)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-neutral-2/test_refunds.py", line 66, in test_second_refund_completes_the_order
    result = refund(self.order, 60, self.gateway, OWNER, "key-2")
  File "/tmp/aep-lab/pilot/N-neutral-2/refunds.py", line 44, in refund
    raise ValueError("amount exceeds refundable remainder")
ValueError: amount exceeds refundable remainder

======================================================================
FAIL: test_failed_refund_does_not_poison_a_later_retry (test_refunds.GatewayFailureAtomicityGuardTests.test_failed_refund_does_not_poison_a_later_retry)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-neutral-2/test_refunds.py", line 305, in test_failed_refund_does_not_poison_a_later_retry
    self.assertEqual(self.order["refunded"], 50)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 70 != 50

======================================================================
FAIL: test_gateway_error_on_full_refund_leaves_status_and_total (test_refunds.GatewayFailureAtomicityGuardTests.test_gateway_error_on_full_refund_leaves_status_and_total)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-neutral-2/test_refunds.py", line 317, in test_gateway_error_on_full_refund_leaves_status_and_total
    self.assertEqual(order, snapshot)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: {'id'[50 chars]1', 'paid': 100, 'refunded': 100, 'status': 'paid', 'keys': {}} != {'id'[50 chars]1', 'paid': 100, 'refunded': 0, 'status': 'paid', 'keys': {}}
  {'charge_id': 'ch_1',
   'id': 'ord_1',
   'keys': {},
   'owner_id': 'cust_1',
   'paid': 100,
-  'refunded': 100,
?              --

+  'refunded': 0,
   'status': 'paid'}

======================================================================
FAIL: test_order_is_completely_unchanged_after_gateway_error (test_refunds.GatewayFailureAtomicityGuardTests.test_order_is_completely_unchanged_after_gateway_error)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-neutral-2/test_refunds.py", line 291, in test_order_is_completely_unchanged_after_gateway_error
    self.assertEqual(self.order, self.snapshot)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: {'id'[63 chars]00, 'refunded': 50, 'status': 'partially_refunded', 'keys': {}} != {'id'[63 chars]00, 'refunded': 40, 'status': 'partially_refunded', 'keys': {}}
  {'charge_id': 'ch_1',
   'id': 'ord_1',
   'keys': {},
   'owner_id': 'cust_1',
   'paid': 100,
-  'refunded': 50,
?              ^

+  'refunded': 40,
?              ^

   'status': 'partially_refunded'}

======================================================================
FAIL: test_full_refund_in_one_call_is_marked_refunded (test_refunds.HappyPathTests.test_full_refund_in_one_call_is_marked_refunded)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-neutral-2/test_refunds.py", line 77, in test_full_refund_in_one_call_is_marked_refunded
    self.assertEqual(result["status"], "refunded")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'partially_refunded' != 'refunded'
- partially_refunded
+ refunded


======================================================================
FAIL: test_partial_refund_updates_order_and_returns_result (test_refunds.HappyPathTests.test_partial_refund_updates_order_and_returns_result)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-neutral-2/test_refunds.py", line 55, in test_partial_refund_updates_order_and_returns_result
    self.assertEqual(self.order["refunded"], 40)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 80 != 40

======================================================================
FAIL: test_exact_remainder_is_allowed (test_refunds.RefundableCapGuardTests.test_exact_remainder_is_allowed)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-neutral-2/test_refunds.py", line 250, in test_exact_remainder_is_allowed
    self.assertEqual(result["status"], "refunded")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'partially_refunded' != 'refunded'
- partially_refunded
+ refunded


======================================================================
FAIL: test_full_paid_amount_is_allowed_when_nothing_refunded (test_refunds.RefundableCapGuardTests.test_full_paid_amount_is_allowed_when_nothing_refunded)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-neutral-2/test_refunds.py", line 264, in test_full_paid_amount_is_allowed_when_nothing_refunded
    self.assertEqual(result["status"], "refunded")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'partially_refunded' != 'refunded'
- partially_refunded
+ refunded


======================================================================
FAIL: test_partially_refunded_order_is_accepted (test_refunds.StatusGuardTests.test_partially_refunded_order_is_accepted)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-neutral-2/test_refunds.py", line 240, in test_partially_refunded_order_is_accepted
    self.assertEqual(order["refunded"], 30)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 40 != 30

----------------------------------------------------------------------
Ran 37 tests in 0.002s

FAILED (failures=8, errors=1)
(exit 1)
$ restored /tmp/aep-lab/pilot/N-neutral-2/refunds.py from backup (byte-identical)
$ cd /tmp/aep-lab/pilot/N-neutral-2 && python3 -m unittest discover -s /tmp/aep-lab/pilot/N-neutral-2 -p 'test*.py'   # expect SUCCESS
.....................................
----------------------------------------------------------------------
Ran 37 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

**Exit status: 0**
