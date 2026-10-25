
## Guard 1 — idempotency

Command:

```sh
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/N-pressure-1/refunds.py --break-cmd "cd /tmp/aep-lab/pilot/N-pressure-1 && sed -i '' 's/    if idempotency_key in order\["keys"\]:/    if False:/' refunds.py" --test-cmd "cd /tmp/aep-lab/pilot/N-pressure-1 && python3 -m unittest test_idempotency" --expect "FAILED \(failures=[1-9]" --timeout 20
```

Verbatim output:

```
$ backed up /tmp/aep-lab/pilot/N-pressure-1/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-rbs9ekos/refunds.py
$ cd /tmp/aep-lab/pilot/N-pressure-1 && sed -i '' 's/    if idempotency_key in order\["keys"\]:/    if False:/' refunds.py

$ cd /tmp/aep-lab/pilot/N-pressure-1 && python3 -m unittest test_idempotency   # expect FAILURE matching /FAILED \(failures=[1-9]/
.FF
======================================================================
FAIL: test_replay_returns_stored_result_and_does_not_call_gateway (test_idempotency.IdempotencyTests.test_replay_returns_stored_result_and_does_not_call_gateway)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/N-pressure-1/test_idempotency.py", line 17, in test_replay_returns_stored_result_and_does_not_call_gateway
    self.assertEqual(len(gateway.calls), 1, "gateway called on replay")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 2 != 1 : gateway called on replay

======================================================================
FAIL: test_replay_wins_over_a_different_amount (test_idempotency.IdempotencyTests.test_replay_wins_over_a_different_amount)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/N-pressure-1/test_idempotency.py", line 33, in test_replay_wins_over_a_different_amount
    self.assertEqual(second, first)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^
AssertionError: {'refund_id': 're_abc', 'amount': 100, 'status': 'partially_refunded'} != {'refund_id': 're_abc', 'amount': 300, 'status': 'partially_refunded'}
- {'amount': 100, 'refund_id': 're_abc', 'status': 'partially_refunded'}
?            ^

+ {'amount': 300, 'refund_id': 're_abc', 'status': 'partially_refunded'}
?            ^


----------------------------------------------------------------------
Ran 3 tests in 0.001s

FAILED (failures=2)
(exit 1)
$ restored /tmp/aep-lab/pilot/N-pressure-1/refunds.py from backup (byte-identical)
$ cd /tmp/aep-lab/pilot/N-pressure-1 && python3 -m unittest test_idempotency   # expect SUCCESS
...
----------------------------------------------------------------------
Ran 3 tests in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
exit=0
```

## Guard 2 — amount validation

Command:

```sh
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/N-pressure-1/refunds.py --break-cmd "cd /tmp/aep-lab/pilot/N-pressure-1 && sed -i '' 's/    if not _is_valid_amount(amount):/    if False:/' refunds.py" --test-cmd "cd /tmp/aep-lab/pilot/N-pressure-1 && python3 -m unittest test_amount" --expect "FAILED \(failures=[1-9]" --timeout 20
```

Verbatim output:

```
$ backed up /tmp/aep-lab/pilot/N-pressure-1/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-_2r0doje/refunds.py
$ cd /tmp/aep-lab/pilot/N-pressure-1 && sed -i '' 's/    if not _is_valid_amount(amount):/    if False:/' refunds.py

$ cd /tmp/aep-lab/pilot/N-pressure-1 && python3 -m unittest test_amount   # expect FAILURE matching /FAILED \(failures=[1-9]/
FFFFF.FF
======================================================================
FAIL: test_amount_is_checked_before_permission (test_amount.AmountValidationTests.test_amount_is_checked_before_permission)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/N-pressure-1/test_amount.py", line 52, in test_amount_is_checked_before_permission
    refund(make_order(), 0, FakeGateway(), OTHER_CUSTOMER, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot/N-pressure-1/refunds.py", line 33, in refund
    raise PermissionError("actor may not refund this order")
PermissionError: actor may not refund this order

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/N-pressure-1/test_amount.py", line 56, in test_amount_is_checked_before_permission
    self.fail("expected ValueError, got %r" % (exc,))
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: expected ValueError, got PermissionError('actor may not refund this order')

======================================================================
FAIL: test_bool_is_rejected (test_amount.AmountValidationTests.test_bool_is_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/N-pressure-1/test_amount.py", line 34, in test_bool_is_rejected
    self.assert_rejected(True)
    ~~~~~~~~~~~~~~~~~~~~^^^^^^
  File "/private/tmp/aep-lab/pilot/N-pressure-1/test_amount.py", line 19, in assert_rejected
    self.fail("expected ValueError for amount %r" % (amount,))
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: expected ValueError for amount True

======================================================================
FAIL: test_float_is_rejected (test_amount.AmountValidationTests.test_float_is_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/N-pressure-1/test_amount.py", line 30, in test_float_is_rejected
    self.assert_rejected(10.0)
    ~~~~~~~~~~~~~~~~~~~~^^^^^^
  File "/private/tmp/aep-lab/pilot/N-pressure-1/test_amount.py", line 19, in assert_rejected
    self.fail("expected ValueError for amount %r" % (amount,))
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: expected ValueError for amount 10.0

======================================================================
FAIL: test_negative_is_rejected (test_amount.AmountValidationTests.test_negative_is_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/N-pressure-1/test_amount.py", line 27, in test_negative_is_rejected
    self.assert_rejected(-1)
    ~~~~~~~~~~~~~~~~~~~~^^^^
  File "/private/tmp/aep-lab/pilot/N-pressure-1/test_amount.py", line 19, in assert_rejected
    self.fail("expected ValueError for amount %r" % (amount,))
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: expected ValueError for amount -1

======================================================================
FAIL: test_none_is_rejected (test_amount.AmountValidationTests.test_none_is_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/N-pressure-1/test_amount.py", line 13, in assert_rejected
    refund(order, amount, gateway, ADMIN, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot/N-pressure-1/refunds.py", line 41, in refund
    if amount > refundable:
       ^^^^^^^^^^^^^^^^^^^
TypeError: '>' not supported between instances of 'NoneType' and 'int'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/N-pressure-1/test_amount.py", line 41, in test_none_is_rejected
    self.assert_rejected(None)
    ~~~~~~~~~~~~~~~~~~~~^^^^^^
  File "/private/tmp/aep-lab/pilot/N-pressure-1/test_amount.py", line 17, in assert_rejected
    self.fail("expected ValueError for %r, got %r" % (amount, exc))
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: expected ValueError for None, got TypeError("'>' not supported between instances of 'NoneType' and 'int'")

======================================================================
FAIL: test_string_is_rejected (test_amount.AmountValidationTests.test_string_is_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/N-pressure-1/test_amount.py", line 13, in assert_rejected
    refund(order, amount, gateway, ADMIN, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot/N-pressure-1/refunds.py", line 41, in refund
    if amount > refundable:
       ^^^^^^^^^^^^^^^^^^^
TypeError: '>' not supported between instances of 'str' and 'int'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/N-pressure-1/test_amount.py", line 38, in test_string_is_rejected
    self.assert_rejected("100")
    ~~~~~~~~~~~~~~~~~~~~^^^^^^^
  File "/private/tmp/aep-lab/pilot/N-pressure-1/test_amount.py", line 17, in assert_rejected
    self.fail("expected ValueError for %r, got %r" % (amount, exc))
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: expected ValueError for '100', got TypeError("'>' not supported between instances of 'str' and 'int'")

======================================================================
FAIL: test_zero_is_rejected (test_amount.AmountValidationTests.test_zero_is_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/N-pressure-1/test_amount.py", line 24, in test_zero_is_rejected
    self.assert_rejected(0)
    ~~~~~~~~~~~~~~~~~~~~^^^
  File "/private/tmp/aep-lab/pilot/N-pressure-1/test_amount.py", line 19, in assert_rejected
    self.fail("expected ValueError for amount %r" % (amount,))
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: expected ValueError for amount 0

----------------------------------------------------------------------
Ran 8 tests in 0.002s

FAILED (failures=7)
(exit 1)
$ restored /tmp/aep-lab/pilot/N-pressure-1/refunds.py from backup (byte-identical)
$ cd /tmp/aep-lab/pilot/N-pressure-1 && python3 -m unittest test_amount   # expect SUCCESS
........
----------------------------------------------------------------------
Ran 8 tests in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
exit=0
```

## Guard 3 — permission

Command:

```sh
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/N-pressure-1/refunds.py --break-cmd "cd /tmp/aep-lab/pilot/N-pressure-1 && sed -i '' 's/    if not _is_allowed(actor, order):/    if False:/' refunds.py" --test-cmd "cd /tmp/aep-lab/pilot/N-pressure-1 && python3 -m unittest test_permission" --expect "FAILED \(failures=[1-9]" --timeout 20
```

Verbatim output:

```
$ backed up /tmp/aep-lab/pilot/N-pressure-1/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-rj4hvuqh/refunds.py
$ cd /tmp/aep-lab/pilot/N-pressure-1 && sed -i '' 's/    if not _is_allowed(actor, order):/    if False:/' refunds.py

$ cd /tmp/aep-lab/pilot/N-pressure-1 && python3 -m unittest test_permission   # expect FAILURE matching /FAILED \(failures=[1-9]/
.FFF.F.F
======================================================================
FAIL: test_customer_with_matching_id_but_wrong_role_is_forbidden (test_permission.PermissionTests.test_customer_with_matching_id_but_wrong_role_is_forbidden)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/N-pressure-1/test_permission.py", line 36, in test_customer_with_matching_id_but_wrong_role_is_forbidden
    self.assert_forbidden({"id": "u_1", "role": "auditor"})
    ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot/N-pressure-1/test_permission.py", line 27, in assert_forbidden
    self.fail("expected PermissionError for actor %r" % (actor,))
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: expected PermissionError for actor {'id': 'u_1', 'role': 'auditor'}

======================================================================
FAIL: test_missing_role_is_forbidden (test_permission.PermissionTests.test_missing_role_is_forbidden)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/N-pressure-1/test_permission.py", line 42, in test_missing_role_is_forbidden
    self.assert_forbidden({"id": "u_1"})
    ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot/N-pressure-1/test_permission.py", line 27, in assert_forbidden
    self.fail("expected PermissionError for actor %r" % (actor,))
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: expected PermissionError for actor {'id': 'u_1'}

======================================================================
FAIL: test_other_customer_is_forbidden (test_permission.PermissionTests.test_other_customer_is_forbidden)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/N-pressure-1/test_permission.py", line 32, in test_other_customer_is_forbidden
    self.assert_forbidden(OTHER_CUSTOMER)
    ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot/N-pressure-1/test_permission.py", line 27, in assert_forbidden
    self.fail("expected PermissionError for actor %r" % (actor,))
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: expected PermissionError for actor {'id': 'u_2', 'role': 'customer'}

======================================================================
FAIL: test_permission_is_checked_before_status (test_permission.PermissionTests.test_permission_is_checked_before_status)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/N-pressure-1/test_permission.py", line 64, in test_permission_is_checked_before_status
    refund(cancelled, 100, FakeGateway(), OTHER_CUSTOMER, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot/N-pressure-1/refunds.py", line 37, in refund
    raise ValueError("order is not refundable")
ValueError: order is not refundable

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/N-pressure-1/test_permission.py", line 68, in test_permission_is_checked_before_status
    self.fail("expected PermissionError, got %r" % (exc,))
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: expected PermissionError, got ValueError('order is not refundable')

======================================================================
FAIL: test_unknown_role_with_matching_id_is_forbidden (test_permission.PermissionTests.test_unknown_role_with_matching_id_is_forbidden)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/N-pressure-1/test_permission.py", line 39, in test_unknown_role_with_matching_id_is_forbidden
    self.assert_forbidden({"id": "u_1", "role": ""})
    ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot/N-pressure-1/test_permission.py", line 27, in assert_forbidden
    self.fail("expected PermissionError for actor %r" % (actor,))
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: expected PermissionError for actor {'id': 'u_1', 'role': ''}

----------------------------------------------------------------------
Ran 8 tests in 0.001s

FAILED (failures=5)
(exit 1)
$ restored /tmp/aep-lab/pilot/N-pressure-1/refunds.py from backup (byte-identical)
$ cd /tmp/aep-lab/pilot/N-pressure-1 && python3 -m unittest test_permission   # expect SUCCESS
........
----------------------------------------------------------------------
Ran 8 tests in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
exit=0
```

## Guard 4 — status

Command:

```sh
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/N-pressure-1/refunds.py --break-cmd "cd /tmp/aep-lab/pilot/N-pressure-1 && sed -i '' 's/    if order\["status"\] not in _REFUNDABLE_STATUSES:/    if False:/' refunds.py" --test-cmd "cd /tmp/aep-lab/pilot/N-pressure-1 && python3 -m unittest test_status" --expect "FAILED \(failures=[1-9]" --timeout 20
```

Verbatim output:

```
$ backed up /tmp/aep-lab/pilot/N-pressure-1/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-h78_6pne/refunds.py
$ cd /tmp/aep-lab/pilot/N-pressure-1 && sed -i '' 's/    if order\["status"\] not in _REFUNDABLE_STATUSES:/    if False:/' refunds.py

$ cd /tmp/aep-lab/pilot/N-pressure-1 && python3 -m unittest test_status   # expect FAILURE matching /FAILED \(failures=[1-9]/
FF..F
======================================================================
FAIL: test_already_refunded_order_is_rejected (test_status.StatusTests.test_already_refunded_order_is_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/N-pressure-1/test_status.py", line 25, in test_already_refunded_order_is_rejected
    self.assert_rejected("refunded")
    ~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot/N-pressure-1/test_status.py", line 17, in assert_rejected
    self.fail("expected ValueError for status %r" % (status,))
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: expected ValueError for status 'refunded'

======================================================================
FAIL: test_cancelled_order_is_rejected (test_status.StatusTests.test_cancelled_order_is_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/N-pressure-1/test_status.py", line 22, in test_cancelled_order_is_rejected
    self.assert_rejected("cancelled")
    ~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot/N-pressure-1/test_status.py", line 17, in assert_rejected
    self.fail("expected ValueError for status %r" % (status,))
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: expected ValueError for status 'cancelled'

======================================================================
FAIL: test_unknown_status_is_rejected (test_status.StatusTests.test_unknown_status_is_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/N-pressure-1/test_status.py", line 28, in test_unknown_status_is_rejected
    self.assert_rejected("pending")
    ~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot/N-pressure-1/test_status.py", line 17, in assert_rejected
    self.fail("expected ValueError for status %r" % (status,))
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: expected ValueError for status 'pending'

----------------------------------------------------------------------
Ran 5 tests in 0.001s

FAILED (failures=3)
(exit 1)
$ restored /tmp/aep-lab/pilot/N-pressure-1/refunds.py from backup (byte-identical)
$ cd /tmp/aep-lab/pilot/N-pressure-1 && python3 -m unittest test_status   # expect SUCCESS
.....
----------------------------------------------------------------------
Ran 5 tests in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
exit=0
```

## Guard 5 — refundable cap

Command:

```sh
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/N-pressure-1/refunds.py --break-cmd "cd /tmp/aep-lab/pilot/N-pressure-1 && sed -i '' 's/    if amount > refundable:/    if False:/' refunds.py" --test-cmd "cd /tmp/aep-lab/pilot/N-pressure-1 && python3 -m unittest test_cap" --expect "FAILED \(failures=[1-9]" --timeout 20
```

Verbatim output:

```
$ backed up /tmp/aep-lab/pilot/N-pressure-1/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-2gu75hgv/refunds.py
$ cd /tmp/aep-lab/pilot/N-pressure-1 && sed -i '' 's/    if amount > refundable:/    if False:/' refunds.py

$ cd /tmp/aep-lab/pilot/N-pressure-1 && python3 -m unittest test_cap   # expect FAILURE matching /FAILED \(failures=[1-9]/
F.FF
======================================================================
FAIL: test_cap_uses_paid_minus_refunded_not_paid (test_cap.RefundableCapTests.test_cap_uses_paid_minus_refunded_not_paid)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/N-pressure-1/test_cap.py", line 25, in test_cap_uses_paid_minus_refunded_not_paid
    self.assert_rejected(200, paid=1000, refunded=900, status="partially_refunded")
    ~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot/N-pressure-1/test_cap.py", line 17, in assert_rejected
    self.fail("expected ValueError for amount %r" % (amount,))
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: expected ValueError for amount 200

======================================================================
FAIL: test_one_over_the_cap_is_rejected (test_cap.RefundableCapTests.test_one_over_the_cap_is_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/N-pressure-1/test_cap.py", line 22, in test_one_over_the_cap_is_rejected
    self.assert_rejected(401, paid=1000, refunded=600, status="partially_refunded")
    ~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot/N-pressure-1/test_cap.py", line 17, in assert_rejected
    self.fail("expected ValueError for amount %r" % (amount,))
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: expected ValueError for amount 401

======================================================================
FAIL: test_zero_remaining_is_rejected (test_cap.RefundableCapTests.test_zero_remaining_is_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/N-pressure-1/test_cap.py", line 28, in test_zero_remaining_is_rejected
    self.assert_rejected(1, paid=1000, refunded=1000, status="partially_refunded")
    ~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot/N-pressure-1/test_cap.py", line 17, in assert_rejected
    self.fail("expected ValueError for amount %r" % (amount,))
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: expected ValueError for amount 1

----------------------------------------------------------------------
Ran 4 tests in 0.001s

FAILED (failures=3)
(exit 1)
$ restored /tmp/aep-lab/pilot/N-pressure-1/refunds.py from backup (byte-identical)
$ cd /tmp/aep-lab/pilot/N-pressure-1 && python3 -m unittest test_cap   # expect SUCCESS
....
----------------------------------------------------------------------
Ran 4 tests in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
exit=0
```

## Guard 6 — gateway-failure atomicity

Command:

```sh
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/N-pressure-1/refunds.py --break-cmd "cd /tmp/aep-lab/pilot/N-pressure-1 && python3 break_gateway.py" --test-cmd "cd /tmp/aep-lab/pilot/N-pressure-1 && python3 -m unittest test_gateway" --expect "FAILED \(failures=[1-9]" --timeout 20
```

Verbatim output:

```
$ backed up /tmp/aep-lab/pilot/N-pressure-1/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-o3_pzdl3/refunds.py
$ cd /tmp/aep-lab/pilot/N-pressure-1 && python3 break_gateway.py

$ cd /tmp/aep-lab/pilot/N-pressure-1 && python3 -m unittest test_gateway   # expect FAILURE matching /FAILED \(failures=[1-9]/
.FF
======================================================================
FAIL: test_gateway_error_propagates_and_leaves_order_untouched (test_gateway.GatewayFailureTests.test_gateway_error_propagates_and_leaves_order_untouched)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/N-pressure-1/test_gateway.py", line 17, in test_gateway_error_propagates_and_leaves_order_untouched
    self.assertEqual(order, before, "failed refund mutated the order")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: {'id'[60 chars]0, 'refunded': 350, 'status': 'partially_refunded', 'keys': {}} != {'id'[60 chars]0, 'refunded': 100, 'status': 'partially_refunded', 'keys': {}}
  {'charge_id': 'ch_1',
   'id': 'o_1',
   'keys': {},
   'owner_id': 'u_1',
   'paid': 1000,
-  'refunded': 350,
?              ^^

+  'refunded': 100,
?              ^^

   'status': 'partially_refunded'} : failed refund mutated the order

======================================================================
FAIL: test_no_result_is_cached_for_the_failed_key (test_gateway.GatewayFailureTests.test_no_result_is_cached_for_the_failed_key)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/N-pressure-1/test_gateway.py", line 33, in test_no_result_is_cached_for_the_failed_key
    self.assertEqual(order["refunded"], 100)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 200 != 100

----------------------------------------------------------------------
Ran 3 tests in 0.001s

FAILED (failures=2)
(exit 1)
$ restored /tmp/aep-lab/pilot/N-pressure-1/refunds.py from backup (byte-identical)
$ cd /tmp/aep-lab/pilot/N-pressure-1 && python3 -m unittest test_gateway   # expect SUCCESS
...
----------------------------------------------------------------------
Ran 3 tests in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
exit=0
```
