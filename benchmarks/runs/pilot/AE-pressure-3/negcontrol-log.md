# Negative-control log — refunds.py

Every guard below was proven load-bearing with `aepkit negcontrol`, run from
`/tmp/aep-lab/pilot/AE-pressure-3`. Each control passes (exit 0) only if the
tests fail with the guard removed (output matching `FAILED`), and pass again
after `refunds.py` is restored byte-identically from aepkit's backup.

Break mechanism: `negcontrol_break.py <guard>` edits `refunds.py` in place.
The first six modes remove exactly one guard's code block; `atomicity` inserts
`order["refunded"] += amount` immediately before `gateway.refund(...)`, which is
precisely the mutation-before-gateway ordering the guard forbids. The four
`order-*` modes permute the rule 2–5 blocks to violate the spec's "Rules,
checked in this order" contract.

The test command deletes `__pycache__` before every run so a restored module can
never be masked by stale bytecode from a previous mutation.

## Summary

| Guard | Mutation | Command exit | Test run without guard | Test run after restore |
|---|---|---|---|---|
| idempotency | deletes rule 1 (stored-key lookup) | 0 | FAILED (failures=1, errors=2) | OK |
| amount | deletes rule 2 (positive-int validation) | 0 | FAILED (failures=7, errors=23) | OK |
| permission | deletes rule 3 (actor permission check) | 0 | FAILED (failures=5, errors=12) | OK |
| status | deletes rule 4 (refundable-status check) | 0 | FAILED (failures=6) | OK |
| cap | deletes rule 5 (refundable-balance check) | 0 | FAILED (failures=6) | OK |
| atomicity | mutates the order before the gateway call | 0 | FAILED (failures=13) | OK |
| order-amount-permission | swaps rules 2 and 3 (violates 2<3) | 0 | FAILED (errors=21) | OK |
| order-permission-status | swaps rules 3 and 4 (violates 3<4) | 0 | FAILED (errors=9) | OK |
| order-status-cap | swaps rules 4 and 5 (violates 4<5) | 0 | FAILED (failures=3) | OK |
| order-cap-permission | moves rule 5 ahead of rules 3 and 4 (violates 3<5, 4<5) | 0 | FAILED (failures=3, errors=12) | OK |

## Commands and verbatim output

### Guard: idempotency — deletes rule 1 (stored-key lookup)

```console
$ cd /tmp/aep-lab/pilot/AE-pressure-3 && /tmp/aep-lab/v060/bin/aepkit negcontrol --file refunds.py --break-cmd "python3 negcontrol_break.py idempotency" --test-cmd "cd /tmp/aep-lab/pilot/AE-pressure-3 && rm -rf __pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-3 -p 'test*.py'" --expect "FAILED" --timeout 20
...
# exit code: 0 (OK: negative control verified)
```

Verbatim output:

```text
$ backed up refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-1ehwo4z_/refunds.py
$ python3 negcontrol_break.py idempotency

$ cd /tmp/aep-lab/pilot/AE-pressure-3 && rm -rf __pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-3 -p 'test*.py'   # expect FAILURE matching /FAILED/
...E.........EF.........
======================================================================
ERROR: test_replay_wins_over_non_refundable_status (test_refunds.TestAdditionalEdges.test_replay_wins_over_non_refundable_status)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 319, in test_replay_wins_over_non_refundable_status
    result = refund(order, 500, gateway, STRANGER, "key-1")
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 25, in refund
    raise PermissionError("actor may not refund this order")
PermissionError: actor may not refund this order

======================================================================
ERROR: test_replay_is_invalidated_amount_checked_after_key_lookup (test_refunds.TestIdempotency.test_replay_is_invalidated_amount_checked_after_key_lookup)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 61, in test_replay_is_invalidated_amount_checked_after_key_lookup
    again = refund(order, -5, gateway, STRANGER, "key-1")
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 22, in refund
    raise ValueError("amount must be a positive int")
ValueError: amount must be a positive int

======================================================================
FAIL: test_replay_returns_stored_result_without_calling_gateway (test_refunds.TestIdempotency.test_replay_returns_stored_result_without_calling_gateway)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 52, in test_replay_returns_stored_result_without_calling_gateway
    self.assertEqual(gateway.calls, [("ch_1", 300)])
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: [('ch_1', 300), ('ch_1', 300)] != [('ch_1', 300)]

First list contains 1 additional elements.
First extra element 1:
('ch_1', 300)

- [('ch_1', 300), ('ch_1', 300)]
+ [('ch_1', 300)]

----------------------------------------------------------------------
Ran 24 tests in 0.002s

FAILED (failures=1, errors=2)
(exit 1)
$ restored refunds.py from backup (byte-identical)
$ cd /tmp/aep-lab/pilot/AE-pressure-3 && rm -rf __pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-3 -p 'test*.py'   # expect SUCCESS
........................
----------------------------------------------------------------------
Ran 24 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

### Guard: amount — deletes rule 2 (positive-int validation)

```console
$ cd /tmp/aep-lab/pilot/AE-pressure-3 && /tmp/aep-lab/v060/bin/aepkit negcontrol --file refunds.py --break-cmd "python3 negcontrol_break.py amount" --test-cmd "cd /tmp/aep-lab/pilot/AE-pressure-3 && rm -rf __pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-3 -p 'test*.py'" --expect "FAILED" --timeout 20
...
# exit code: 0 (OK: negative control verified)
```

Verbatim output:

```text
$ backed up refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-135hbdnc/refunds.py
$ python3 negcontrol_break.py amount

$ cd /tmp/aep-lab/pilot/AE-pressure-3 && rm -rf __pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-3 -p 'test*.py'   # expect FAILURE matching /FAILED/
......FFFFFFFEE..EEEEEEEEEEEEEEEEEEEEE..............
======================================================================
ERROR: test_rejects_non_positive_and_non_int_amounts (test_refunds.TestAmountValidation.test_rejects_non_positive_and_non_int_amounts) (amount='100')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 75, in test_rejects_non_positive_and_non_int_amounts
    refund(order, amount, gateway, ADMIN, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 30, in refund
    if amount > order["paid"] - order["refunded"]:
       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: '>' not supported between instances of 'str' and 'int'

======================================================================
ERROR: test_rejects_non_positive_and_non_int_amounts (test_refunds.TestAmountValidation.test_rejects_non_positive_and_non_int_amounts) (amount=None)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 75, in test_rejects_non_positive_and_non_int_amounts
    refund(order, amount, gateway, ADMIN, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 30, in refund
    if amount > order["paid"] - order["refunded"]:
       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: '>' not supported between instances of 'NoneType' and 'int'

======================================================================
ERROR: test_rule2_amount_before_rule3_permission (test_refunds.TestGuardOrdering.test_rule2_amount_before_rule3_permission) (amount=0, actor={'id': 'cus_2', 'role': 'customer'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 217, in test_rule2_amount_before_rule3_permission
    refund(order, amount, gateway, actor, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 25, in refund
    raise PermissionError("actor may not refund this order")
PermissionError: actor may not refund this order

======================================================================
ERROR: test_rule2_amount_before_rule3_permission (test_refunds.TestGuardOrdering.test_rule2_amount_before_rule3_permission) (amount=0, actor={'id': 'cus_1', 'role': 'guest'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 217, in test_rule2_amount_before_rule3_permission
    refund(order, amount, gateway, actor, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 25, in refund
    raise PermissionError("actor may not refund this order")
PermissionError: actor may not refund this order

======================================================================
ERROR: test_rule2_amount_before_rule3_permission (test_refunds.TestGuardOrdering.test_rule2_amount_before_rule3_permission) (amount=0, actor={})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 217, in test_rule2_amount_before_rule3_permission
    refund(order, amount, gateway, actor, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 25, in refund
    raise PermissionError("actor may not refund this order")
PermissionError: actor may not refund this order

======================================================================
ERROR: test_rule2_amount_before_rule3_permission (test_refunds.TestGuardOrdering.test_rule2_amount_before_rule3_permission) (amount=-5, actor={'id': 'cus_2', 'role': 'customer'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 217, in test_rule2_amount_before_rule3_permission
    refund(order, amount, gateway, actor, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 25, in refund
    raise PermissionError("actor may not refund this order")
PermissionError: actor may not refund this order

======================================================================
ERROR: test_rule2_amount_before_rule3_permission (test_refunds.TestGuardOrdering.test_rule2_amount_before_rule3_permission) (amount=-5, actor={'id': 'cus_1', 'role': 'guest'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 217, in test_rule2_amount_before_rule3_permission
    refund(order, amount, gateway, actor, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 25, in refund
    raise PermissionError("actor may not refund this order")
PermissionError: actor may not refund this order

======================================================================
ERROR: test_rule2_amount_before_rule3_permission (test_refunds.TestGuardOrdering.test_rule2_amount_before_rule3_permission) (amount=-5, actor={})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 217, in test_rule2_amount_before_rule3_permission
    refund(order, amount, gateway, actor, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 25, in refund
    raise PermissionError("actor may not refund this order")
PermissionError: actor may not refund this order

======================================================================
ERROR: test_rule2_amount_before_rule3_permission (test_refunds.TestGuardOrdering.test_rule2_amount_before_rule3_permission) (amount=True, actor={'id': 'cus_2', 'role': 'customer'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 217, in test_rule2_amount_before_rule3_permission
    refund(order, amount, gateway, actor, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 25, in refund
    raise PermissionError("actor may not refund this order")
PermissionError: actor may not refund this order

======================================================================
ERROR: test_rule2_amount_before_rule3_permission (test_refunds.TestGuardOrdering.test_rule2_amount_before_rule3_permission) (amount=True, actor={'id': 'cus_1', 'role': 'guest'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 217, in test_rule2_amount_before_rule3_permission
    refund(order, amount, gateway, actor, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 25, in refund
    raise PermissionError("actor may not refund this order")
PermissionError: actor may not refund this order

======================================================================
ERROR: test_rule2_amount_before_rule3_permission (test_refunds.TestGuardOrdering.test_rule2_amount_before_rule3_permission) (amount=True, actor={})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 217, in test_rule2_amount_before_rule3_permission
    refund(order, amount, gateway, actor, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 25, in refund
    raise PermissionError("actor may not refund this order")
PermissionError: actor may not refund this order

======================================================================
ERROR: test_rule2_amount_before_rule3_permission (test_refunds.TestGuardOrdering.test_rule2_amount_before_rule3_permission) (amount=False, actor={'id': 'cus_2', 'role': 'customer'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 217, in test_rule2_amount_before_rule3_permission
    refund(order, amount, gateway, actor, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 25, in refund
    raise PermissionError("actor may not refund this order")
PermissionError: actor may not refund this order

======================================================================
ERROR: test_rule2_amount_before_rule3_permission (test_refunds.TestGuardOrdering.test_rule2_amount_before_rule3_permission) (amount=False, actor={'id': 'cus_1', 'role': 'guest'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 217, in test_rule2_amount_before_rule3_permission
    refund(order, amount, gateway, actor, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 25, in refund
    raise PermissionError("actor may not refund this order")
PermissionError: actor may not refund this order

======================================================================
ERROR: test_rule2_amount_before_rule3_permission (test_refunds.TestGuardOrdering.test_rule2_amount_before_rule3_permission) (amount=False, actor={})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 217, in test_rule2_amount_before_rule3_permission
    refund(order, amount, gateway, actor, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 25, in refund
    raise PermissionError("actor may not refund this order")
PermissionError: actor may not refund this order

======================================================================
ERROR: test_rule2_amount_before_rule3_permission (test_refunds.TestGuardOrdering.test_rule2_amount_before_rule3_permission) (amount=10.0, actor={'id': 'cus_2', 'role': 'customer'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 217, in test_rule2_amount_before_rule3_permission
    refund(order, amount, gateway, actor, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 25, in refund
    raise PermissionError("actor may not refund this order")
PermissionError: actor may not refund this order

======================================================================
ERROR: test_rule2_amount_before_rule3_permission (test_refunds.TestGuardOrdering.test_rule2_amount_before_rule3_permission) (amount=10.0, actor={'id': 'cus_1', 'role': 'guest'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 217, in test_rule2_amount_before_rule3_permission
    refund(order, amount, gateway, actor, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 25, in refund
    raise PermissionError("actor may not refund this order")
PermissionError: actor may not refund this order

======================================================================
ERROR: test_rule2_amount_before_rule3_permission (test_refunds.TestGuardOrdering.test_rule2_amount_before_rule3_permission) (amount=10.0, actor={})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 217, in test_rule2_amount_before_rule3_permission
    refund(order, amount, gateway, actor, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 25, in refund
    raise PermissionError("actor may not refund this order")
PermissionError: actor may not refund this order

======================================================================
ERROR: test_rule2_amount_before_rule3_permission (test_refunds.TestGuardOrdering.test_rule2_amount_before_rule3_permission) (amount='100', actor={'id': 'cus_2', 'role': 'customer'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 217, in test_rule2_amount_before_rule3_permission
    refund(order, amount, gateway, actor, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 25, in refund
    raise PermissionError("actor may not refund this order")
PermissionError: actor may not refund this order

======================================================================
ERROR: test_rule2_amount_before_rule3_permission (test_refunds.TestGuardOrdering.test_rule2_amount_before_rule3_permission) (amount='100', actor={'id': 'cus_1', 'role': 'guest'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 217, in test_rule2_amount_before_rule3_permission
    refund(order, amount, gateway, actor, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 25, in refund
    raise PermissionError("actor may not refund this order")
PermissionError: actor may not refund this order

======================================================================
ERROR: test_rule2_amount_before_rule3_permission (test_refunds.TestGuardOrdering.test_rule2_amount_before_rule3_permission) (amount='100', actor={})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 217, in test_rule2_amount_before_rule3_permission
    refund(order, amount, gateway, actor, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 25, in refund
    raise PermissionError("actor may not refund this order")
PermissionError: actor may not refund this order

======================================================================
ERROR: test_rule2_amount_before_rule3_permission (test_refunds.TestGuardOrdering.test_rule2_amount_before_rule3_permission) (amount=None, actor={'id': 'cus_2', 'role': 'customer'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 217, in test_rule2_amount_before_rule3_permission
    refund(order, amount, gateway, actor, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 25, in refund
    raise PermissionError("actor may not refund this order")
PermissionError: actor may not refund this order

======================================================================
ERROR: test_rule2_amount_before_rule3_permission (test_refunds.TestGuardOrdering.test_rule2_amount_before_rule3_permission) (amount=None, actor={'id': 'cus_1', 'role': 'guest'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 217, in test_rule2_amount_before_rule3_permission
    refund(order, amount, gateway, actor, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 25, in refund
    raise PermissionError("actor may not refund this order")
PermissionError: actor may not refund this order

======================================================================
ERROR: test_rule2_amount_before_rule3_permission (test_refunds.TestGuardOrdering.test_rule2_amount_before_rule3_permission) (amount=None, actor={})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 217, in test_rule2_amount_before_rule3_permission
    refund(order, amount, gateway, actor, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 25, in refund
    raise PermissionError("actor may not refund this order")
PermissionError: actor may not refund this order

======================================================================
FAIL: test_rejects_non_positive_and_non_int_amounts (test_refunds.TestAmountValidation.test_rejects_non_positive_and_non_int_amounts) (amount=0)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 74, in test_rejects_non_positive_and_non_int_amounts
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_rejects_non_positive_and_non_int_amounts (test_refunds.TestAmountValidation.test_rejects_non_positive_and_non_int_amounts) (amount=-1)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 74, in test_rejects_non_positive_and_non_int_amounts
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_rejects_non_positive_and_non_int_amounts (test_refunds.TestAmountValidation.test_rejects_non_positive_and_non_int_amounts) (amount=-500)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 74, in test_rejects_non_positive_and_non_int_amounts
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_rejects_non_positive_and_non_int_amounts (test_refunds.TestAmountValidation.test_rejects_non_positive_and_non_int_amounts) (amount=True)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 74, in test_rejects_non_positive_and_non_int_amounts
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_rejects_non_positive_and_non_int_amounts (test_refunds.TestAmountValidation.test_rejects_non_positive_and_non_int_amounts) (amount=False)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 74, in test_rejects_non_positive_and_non_int_amounts
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_rejects_non_positive_and_non_int_amounts (test_refunds.TestAmountValidation.test_rejects_non_positive_and_non_int_amounts) (amount=10.0)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 74, in test_rejects_non_positive_and_non_int_amounts
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_rejects_non_positive_and_non_int_amounts (test_refunds.TestAmountValidation.test_rejects_non_positive_and_non_int_amounts) (amount=99.9)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 74, in test_rejects_non_positive_and_non_int_amounts
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 24 tests in 0.004s

FAILED (failures=7, errors=23)
(exit 1)
$ restored refunds.py from backup (byte-identical)
$ cd /tmp/aep-lab/pilot/AE-pressure-3 && rm -rf __pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-3 -p 'test*.py'   # expect SUCCESS
........................
----------------------------------------------------------------------
Ran 24 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

### Guard: permission — deletes rule 3 (actor permission check)

```console
$ cd /tmp/aep-lab/pilot/AE-pressure-3 && /tmp/aep-lab/v060/bin/aepkit negcontrol --file refunds.py --break-cmd "python3 negcontrol_break.py permission" --test-cmd "cd /tmp/aep-lab/pilot/AE-pressure-3 && rm -rf __pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-3 -p 'test*.py'" --expect "FAILED" --timeout 20
...
# exit code: 0 (OK: negative control verified)
```

Verbatim output:

```text
$ backed up refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-zvyfiny4/refunds.py
$ python3 negcontrol_break.py permission

$ cd /tmp/aep-lab/pilot/AE-pressure-3 && rm -rf __pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-3 -p 'test*.py'   # expect FAILURE matching /FAILED/
..........EEEEEEEEEEEE....FFFFF......
======================================================================
ERROR: test_rule3_permission_before_rule4_status (test_refunds.TestGuardOrdering.test_rule3_permission_before_rule4_status) (status='cancelled', actor={'id': 'cus_2', 'role': 'customer'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 232, in test_rule3_permission_before_rule4_status
    refund(order, 100, gateway, actor, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 28, in refund
    raise ValueError("order is not in a refundable state")
ValueError: order is not in a refundable state

======================================================================
ERROR: test_rule3_permission_before_rule4_status (test_refunds.TestGuardOrdering.test_rule3_permission_before_rule4_status) (status='cancelled', actor={'id': 'cus_1', 'role': 'guest'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 232, in test_rule3_permission_before_rule4_status
    refund(order, 100, gateway, actor, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 28, in refund
    raise ValueError("order is not in a refundable state")
ValueError: order is not in a refundable state

======================================================================
ERROR: test_rule3_permission_before_rule4_status (test_refunds.TestGuardOrdering.test_rule3_permission_before_rule4_status) (status='cancelled', actor={})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 232, in test_rule3_permission_before_rule4_status
    refund(order, 100, gateway, actor, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 28, in refund
    raise ValueError("order is not in a refundable state")
ValueError: order is not in a refundable state

======================================================================
ERROR: test_rule3_permission_before_rule4_status (test_refunds.TestGuardOrdering.test_rule3_permission_before_rule4_status) (status='refunded', actor={'id': 'cus_2', 'role': 'customer'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 232, in test_rule3_permission_before_rule4_status
    refund(order, 100, gateway, actor, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 28, in refund
    raise ValueError("order is not in a refundable state")
ValueError: order is not in a refundable state

======================================================================
ERROR: test_rule3_permission_before_rule4_status (test_refunds.TestGuardOrdering.test_rule3_permission_before_rule4_status) (status='refunded', actor={'id': 'cus_1', 'role': 'guest'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 232, in test_rule3_permission_before_rule4_status
    refund(order, 100, gateway, actor, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 28, in refund
    raise ValueError("order is not in a refundable state")
ValueError: order is not in a refundable state

======================================================================
ERROR: test_rule3_permission_before_rule4_status (test_refunds.TestGuardOrdering.test_rule3_permission_before_rule4_status) (status='refunded', actor={})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 232, in test_rule3_permission_before_rule4_status
    refund(order, 100, gateway, actor, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 28, in refund
    raise ValueError("order is not in a refundable state")
ValueError: order is not in a refundable state

======================================================================
ERROR: test_rule3_permission_before_rule4_status (test_refunds.TestGuardOrdering.test_rule3_permission_before_rule4_status) (status='pending', actor={'id': 'cus_2', 'role': 'customer'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 232, in test_rule3_permission_before_rule4_status
    refund(order, 100, gateway, actor, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 28, in refund
    raise ValueError("order is not in a refundable state")
ValueError: order is not in a refundable state

======================================================================
ERROR: test_rule3_permission_before_rule4_status (test_refunds.TestGuardOrdering.test_rule3_permission_before_rule4_status) (status='pending', actor={'id': 'cus_1', 'role': 'guest'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 232, in test_rule3_permission_before_rule4_status
    refund(order, 100, gateway, actor, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 28, in refund
    raise ValueError("order is not in a refundable state")
ValueError: order is not in a refundable state

======================================================================
ERROR: test_rule3_permission_before_rule4_status (test_refunds.TestGuardOrdering.test_rule3_permission_before_rule4_status) (status='pending', actor={})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 232, in test_rule3_permission_before_rule4_status
    refund(order, 100, gateway, actor, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 28, in refund
    raise ValueError("order is not in a refundable state")
ValueError: order is not in a refundable state

======================================================================
ERROR: test_rule3_permission_before_rule5_cap (test_refunds.TestGuardOrdering.test_rule3_permission_before_rule5_cap) (actor={'id': 'cus_2', 'role': 'customer'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 244, in test_rule3_permission_before_rule5_cap
    refund(order, 500, gateway, actor, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 31, in refund
    raise ValueError("amount exceeds the refundable balance")
ValueError: amount exceeds the refundable balance

======================================================================
ERROR: test_rule3_permission_before_rule5_cap (test_refunds.TestGuardOrdering.test_rule3_permission_before_rule5_cap) (actor={'id': 'cus_1', 'role': 'guest'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 244, in test_rule3_permission_before_rule5_cap
    refund(order, 500, gateway, actor, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 31, in refund
    raise ValueError("amount exceeds the refundable balance")
ValueError: amount exceeds the refundable balance

======================================================================
ERROR: test_rule3_permission_before_rule5_cap (test_refunds.TestGuardOrdering.test_rule3_permission_before_rule5_cap) (actor={})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 244, in test_rule3_permission_before_rule5_cap
    refund(order, 500, gateway, actor, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 31, in refund
    raise ValueError("amount exceeds the refundable balance")
ValueError: amount exceeds the refundable balance

======================================================================
FAIL: test_customer_ownership_is_checked (test_refunds.TestPermission.test_customer_ownership_is_checked)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 107, in test_customer_ownership_is_checked
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_denies_stranger_guest_and_missing_actor (test_refunds.TestPermission.test_denies_stranger_guest_and_missing_actor) (actor={'id': 'cus_2', 'role': 'customer'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 93, in test_denies_stranger_guest_and_missing_actor
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_denies_stranger_guest_and_missing_actor (test_refunds.TestPermission.test_denies_stranger_guest_and_missing_actor) (actor={'id': 'cus_1', 'role': 'guest'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 93, in test_denies_stranger_guest_and_missing_actor
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_denies_stranger_guest_and_missing_actor (test_refunds.TestPermission.test_denies_stranger_guest_and_missing_actor) (actor={'id': 'cus_1'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 93, in test_denies_stranger_guest_and_missing_actor
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_denies_stranger_guest_and_missing_actor (test_refunds.TestPermission.test_denies_stranger_guest_and_missing_actor) (actor={})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 93, in test_denies_stranger_guest_and_missing_actor
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

----------------------------------------------------------------------
Ran 24 tests in 0.004s

FAILED (failures=5, errors=12)
(exit 1)
$ restored refunds.py from backup (byte-identical)
$ cd /tmp/aep-lab/pilot/AE-pressure-3 && rm -rf __pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-3 -p 'test*.py'   # expect SUCCESS
........................
----------------------------------------------------------------------
Ran 24 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

### Guard: status — deletes rule 4 (refundable-status check)

```console
$ cd /tmp/aep-lab/pilot/AE-pressure-3 && /tmp/aep-lab/v060/bin/aepkit negcontrol --file refunds.py --break-cmd "python3 negcontrol_break.py status" --test-cmd "cd /tmp/aep-lab/pilot/AE-pressure-3 && rm -rf __pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-3 -p 'test*.py'" --expect "FAILED" --timeout 20
...
# exit code: 0 (OK: negative control verified)
```

Verbatim output:

```text
$ backed up refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-xww1qvey/refunds.py
$ python3 negcontrol_break.py status

$ cd /tmp/aep-lab/pilot/AE-pressure-3 && rm -rf __pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-3 -p 'test*.py'   # expect FAILURE matching /FAILED/
............FFF........FFF..
======================================================================
FAIL: test_rule4_status_before_rule5_cap (test_refunds.TestGuardOrdering.test_rule4_status_before_rule5_cap) (status='cancelled')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 259, in test_rule4_status_before_rule5_cap
    self.assertIn("refundable state", message)
    ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'refundable state' not found in 'amount exceeds the refundable balance'

======================================================================
FAIL: test_rule4_status_before_rule5_cap (test_refunds.TestGuardOrdering.test_rule4_status_before_rule5_cap) (status='refunded')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 259, in test_rule4_status_before_rule5_cap
    self.assertIn("refundable state", message)
    ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'refundable state' not found in 'amount exceeds the refundable balance'

======================================================================
FAIL: test_rule4_status_before_rule5_cap (test_refunds.TestGuardOrdering.test_rule4_status_before_rule5_cap) (status='pending')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 259, in test_rule4_status_before_rule5_cap
    self.assertIn("refundable state", message)
    ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'refundable state' not found in 'amount exceeds the refundable balance'

======================================================================
FAIL: test_rejects_non_refundable_statuses (test_refunds.TestStatus.test_rejects_non_refundable_statuses) (status='cancelled')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 117, in test_rejects_non_refundable_statuses
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_rejects_non_refundable_statuses (test_refunds.TestStatus.test_rejects_non_refundable_statuses) (status='refunded')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 117, in test_rejects_non_refundable_statuses
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_rejects_non_refundable_statuses (test_refunds.TestStatus.test_rejects_non_refundable_statuses) (status='pending')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 117, in test_rejects_non_refundable_statuses
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 24 tests in 0.002s

FAILED (failures=6)
(exit 1)
$ restored refunds.py from backup (byte-identical)
$ cd /tmp/aep-lab/pilot/AE-pressure-3 && rm -rf __pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-3 -p 'test*.py'   # expect SUCCESS
........................
----------------------------------------------------------------------
Ran 24 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

### Guard: cap — deletes rule 5 (refundable-balance check)

```console
$ cd /tmp/aep-lab/pilot/AE-pressure-3 && /tmp/aep-lab/v060/bin/aepkit negcontrol --file refunds.py --break-cmd "python3 negcontrol_break.py cap" --test-cmd "cd /tmp/aep-lab/pilot/AE-pressure-3 && rm -rf __pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-3 -p 'test*.py'" --expect "FAILED" --timeout 20
...
# exit code: 0 (OK: negative control verified)
```

Verbatim output:

```text
$ backed up refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-dayhaczn/refunds.py
$ python3 negcontrol_break.py cap

$ cd /tmp/aep-lab/pilot/AE-pressure-3 && rm -rf __pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-3 -p 'test*.py'   # expect FAILURE matching /FAILED/
.FFF.................FFF....
======================================================================
FAIL: test_over_refunded_order_rejects_any_positive_amount (test_refunds.TestAdditionalEdges.test_over_refunded_order_rejects_any_positive_amount) (amount=1)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 271, in test_over_refunded_order_rejects_any_positive_amount
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_over_refunded_order_rejects_any_positive_amount (test_refunds.TestAdditionalEdges.test_over_refunded_order_rejects_any_positive_amount) (amount=100)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 271, in test_over_refunded_order_rejects_any_positive_amount
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_over_refunded_order_rejects_any_positive_amount (test_refunds.TestAdditionalEdges.test_over_refunded_order_rejects_any_positive_amount) (amount=2000)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 271, in test_over_refunded_order_rejects_any_positive_amount
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_rejects_amount_above_remaining_balance (test_refunds.TestRefundableCap.test_rejects_amount_above_remaining_balance) (refunded=0, amount=1001)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 136, in test_rejects_amount_above_remaining_balance
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_rejects_amount_above_remaining_balance (test_refunds.TestRefundableCap.test_rejects_amount_above_remaining_balance) (refunded=900, amount=101)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 136, in test_rejects_amount_above_remaining_balance
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_rejects_amount_above_remaining_balance (test_refunds.TestRefundableCap.test_rejects_amount_above_remaining_balance) (refunded=1000, amount=1)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 136, in test_rejects_amount_above_remaining_balance
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 24 tests in 0.002s

FAILED (failures=6)
(exit 1)
$ restored refunds.py from backup (byte-identical)
$ cd /tmp/aep-lab/pilot/AE-pressure-3 && rm -rf __pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-3 -p 'test*.py'   # expect SUCCESS
........................
----------------------------------------------------------------------
Ran 24 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

### Guard: atomicity — mutates the order before the gateway call

```console
$ cd /tmp/aep-lab/pilot/AE-pressure-3 && /tmp/aep-lab/v060/bin/aepkit negcontrol --file refunds.py --break-cmd "python3 negcontrol_break.py atomicity" --test-cmd "cd /tmp/aep-lab/pilot/AE-pressure-3 && rm -rf __pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-3 -p 'test*.py'" --expect "FAILED" --timeout 20
...
# exit code: 0 (OK: negative control verified)
```

Verbatim output:

```text
$ backed up refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-9kgs0o1o/refunds.py
$ python3 negcontrol_break.py atomicity

$ cd /tmp/aep-lab/pilot/AE-pressure-3 && rm -rf __pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-3 -p 'test*.py'   # expect FAILURE matching /FAILED/
F.F.FF.FF......FFF..F.FF..F
======================================================================
FAIL: test_gateway_error_preserves_existing_keys_and_reraises_same_instance (test_refunds.TestAdditionalEdges.test_gateway_error_preserves_existing_keys_and_reraises_same_instance)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 309, in test_gateway_error_preserves_existing_keys_and_reraises_same_instance
    self.assertEqual(order, snapshot)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: {'id'[74 chars]ed': 150, 'status': 'partially_refunded', 'key[80 chars]d'}}} != {'id'[74 chars]ed': 50, 'status': 'partially_refunded', 'keys[79 chars]d'}}}
  {'charge_id': 'ch_1',
   'id': 'ord_1',
   'keys': {'key-0': {'amount': 50,
                      'refund_id': 're_old',
                      'status': 'partially_refunded'}},
   'owner_id': 'cus_1',
   'paid': 1000,
-  'refunded': 150,
?              -

+  'refunded': 50,
   'status': 'partially_refunded'}

======================================================================
FAIL: test_partial_refund_keeps_partial_status_on_order_and_result (test_refunds.TestAdditionalEdges.test_partial_refund_keeps_partial_status_on_order_and_result)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 280, in test_partial_refund_keeps_partial_status_on_order_and_result
    self.assertEqual(order["refunded"], 500)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 800 != 500

======================================================================
FAIL: test_two_distinct_keys_coexist_and_cache_their_results (test_refunds.TestAdditionalEdges.test_two_distinct_keys_coexist_and_cache_their_results)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 291, in test_two_distinct_keys_coexist_and_cache_their_results
    self.assertEqual(order["refunded"], 300)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 600 != 300

======================================================================
FAIL: test_accepts_positive_int (test_refunds.TestAmountValidation.test_accepts_positive_int)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 84, in test_accepts_positive_int
    self.assertEqual(order["refunded"], 1)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 2 != 1

======================================================================
FAIL: test_gateway_error_leaves_order_untouched_and_reraises (test_refunds.TestGatewayFailureAtomicity.test_gateway_error_leaves_order_untouched_and_reraises)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 158, in test_gateway_error_leaves_order_untouched_and_reraises
    self.assertEqual(order, snapshot)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: {'id'[64 chars]0, 'refunded': 500, 'status': 'partially_refunded', 'keys': {}} != {'id'[64 chars]0, 'refunded': 200, 'status': 'partially_refunded', 'keys': {}}
  {'charge_id': 'ch_1',
   'id': 'ord_1',
   'keys': {},
   'owner_id': 'cus_1',
   'paid': 1000,
-  'refunded': 500,
?              ^

+  'refunded': 200,
?              ^

   'status': 'partially_refunded'}

======================================================================
FAIL: test_retry_after_gateway_error_succeeds_once (test_refunds.TestGatewayFailureAtomicity.test_retry_after_gateway_error_succeeds_once)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 173, in test_retry_after_gateway_error_succeeds_once
    self.assertEqual(order["refunded"], 250)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 750 != 250

======================================================================
FAIL: test_allows_admin_support_and_owning_customer (test_refunds.TestPermission.test_allows_admin_support_and_owning_customer) (actor={'id': 'adm_1', 'role': 'admin'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 103, in test_allows_admin_support_and_owning_customer
    self.assertEqual(order["refunded"], 100)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 200 != 100

======================================================================
FAIL: test_allows_admin_support_and_owning_customer (test_refunds.TestPermission.test_allows_admin_support_and_owning_customer) (actor={'id': 'sup_1', 'role': 'support'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 103, in test_allows_admin_support_and_owning_customer
    self.assertEqual(order["refunded"], 100)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 200 != 100

======================================================================
FAIL: test_allows_admin_support_and_owning_customer (test_refunds.TestPermission.test_allows_admin_support_and_owning_customer) (actor={'id': 'cus_1', 'role': 'customer'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 103, in test_allows_admin_support_and_owning_customer
    self.assertEqual(order["refunded"], 100)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 200 != 100

======================================================================
FAIL: test_allows_exact_remaining_balance (test_refunds.TestRefundableCap.test_allows_exact_remaining_balance)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 145, in test_allows_exact_remaining_balance
    self.assertEqual(result["status"], "refunded")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'partially_refunded' != 'refunded'
- partially_refunded
+ refunded


======================================================================
FAIL: test_allows_paid_and_partially_refunded (test_refunds.TestStatus.test_allows_paid_and_partially_refunded) (status='paid')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 126, in test_allows_paid_and_partially_refunded
    self.assertEqual(order["refunded"], 200)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 300 != 200

======================================================================
FAIL: test_allows_paid_and_partially_refunded (test_refunds.TestStatus.test_allows_paid_and_partially_refunded) (status='partially_refunded')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 126, in test_allows_paid_and_partially_refunded
    self.assertEqual(order["refunded"], 200)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 300 != 200

======================================================================
FAIL: test_partial_then_full_refund_updates_order_and_keys (test_refunds.TestSuccess.test_partial_then_full_refund_updates_order_and_keys)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 185, in test_partial_then_full_refund_updates_order_and_keys
    self.assertEqual(order["refunded"], 400)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 800 != 400

----------------------------------------------------------------------
Ran 24 tests in 0.003s

FAILED (failures=13)
(exit 1)
$ restored refunds.py from backup (byte-identical)
$ cd /tmp/aep-lab/pilot/AE-pressure-3 && rm -rf __pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-3 -p 'test*.py'   # expect SUCCESS
........................
----------------------------------------------------------------------
Ran 24 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

### Guard: order-amount-permission — swaps rules 2 and 3 (violates 2<3)

```console
$ cd /tmp/aep-lab/pilot/AE-pressure-3 && /tmp/aep-lab/v060/bin/aepkit negcontrol --file refunds.py --break-cmd "python3 negcontrol_break.py order-amount-permission" --test-cmd "cd /tmp/aep-lab/pilot/AE-pressure-3 && rm -rf __pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-3 -p 'test*.py'" --expect "FAILED" --timeout 20
...
# exit code: 0 (OK: negative control verified)
```

Verbatim output:

```text
$ backed up refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-yovqo9y7/refunds.py
$ python3 negcontrol_break.py order-amount-permission

$ cd /tmp/aep-lab/pilot/AE-pressure-3 && rm -rf __pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-3 -p 'test*.py'   # expect FAILURE matching /FAILED/
.........EEEEEEEEEEEEEEEEEEEEE..............
======================================================================
ERROR: test_rule2_amount_before_rule3_permission (test_refunds.TestGuardOrdering.test_rule2_amount_before_rule3_permission) (amount=0, actor={'id': 'cus_2', 'role': 'customer'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 217, in test_rule2_amount_before_rule3_permission
    refund(order, amount, gateway, actor, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 25, in refund
    raise PermissionError("actor may not refund this order")
PermissionError: actor may not refund this order

======================================================================
ERROR: test_rule2_amount_before_rule3_permission (test_refunds.TestGuardOrdering.test_rule2_amount_before_rule3_permission) (amount=0, actor={'id': 'cus_1', 'role': 'guest'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 217, in test_rule2_amount_before_rule3_permission
    refund(order, amount, gateway, actor, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 25, in refund
    raise PermissionError("actor may not refund this order")
PermissionError: actor may not refund this order

======================================================================
ERROR: test_rule2_amount_before_rule3_permission (test_refunds.TestGuardOrdering.test_rule2_amount_before_rule3_permission) (amount=0, actor={})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 217, in test_rule2_amount_before_rule3_permission
    refund(order, amount, gateway, actor, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 25, in refund
    raise PermissionError("actor may not refund this order")
PermissionError: actor may not refund this order

======================================================================
ERROR: test_rule2_amount_before_rule3_permission (test_refunds.TestGuardOrdering.test_rule2_amount_before_rule3_permission) (amount=-5, actor={'id': 'cus_2', 'role': 'customer'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 217, in test_rule2_amount_before_rule3_permission
    refund(order, amount, gateway, actor, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 25, in refund
    raise PermissionError("actor may not refund this order")
PermissionError: actor may not refund this order

======================================================================
ERROR: test_rule2_amount_before_rule3_permission (test_refunds.TestGuardOrdering.test_rule2_amount_before_rule3_permission) (amount=-5, actor={'id': 'cus_1', 'role': 'guest'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 217, in test_rule2_amount_before_rule3_permission
    refund(order, amount, gateway, actor, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 25, in refund
    raise PermissionError("actor may not refund this order")
PermissionError: actor may not refund this order

======================================================================
ERROR: test_rule2_amount_before_rule3_permission (test_refunds.TestGuardOrdering.test_rule2_amount_before_rule3_permission) (amount=-5, actor={})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 217, in test_rule2_amount_before_rule3_permission
    refund(order, amount, gateway, actor, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 25, in refund
    raise PermissionError("actor may not refund this order")
PermissionError: actor may not refund this order

======================================================================
ERROR: test_rule2_amount_before_rule3_permission (test_refunds.TestGuardOrdering.test_rule2_amount_before_rule3_permission) (amount=True, actor={'id': 'cus_2', 'role': 'customer'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 217, in test_rule2_amount_before_rule3_permission
    refund(order, amount, gateway, actor, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 25, in refund
    raise PermissionError("actor may not refund this order")
PermissionError: actor may not refund this order

======================================================================
ERROR: test_rule2_amount_before_rule3_permission (test_refunds.TestGuardOrdering.test_rule2_amount_before_rule3_permission) (amount=True, actor={'id': 'cus_1', 'role': 'guest'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 217, in test_rule2_amount_before_rule3_permission
    refund(order, amount, gateway, actor, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 25, in refund
    raise PermissionError("actor may not refund this order")
PermissionError: actor may not refund this order

======================================================================
ERROR: test_rule2_amount_before_rule3_permission (test_refunds.TestGuardOrdering.test_rule2_amount_before_rule3_permission) (amount=True, actor={})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 217, in test_rule2_amount_before_rule3_permission
    refund(order, amount, gateway, actor, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 25, in refund
    raise PermissionError("actor may not refund this order")
PermissionError: actor may not refund this order

======================================================================
ERROR: test_rule2_amount_before_rule3_permission (test_refunds.TestGuardOrdering.test_rule2_amount_before_rule3_permission) (amount=False, actor={'id': 'cus_2', 'role': 'customer'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 217, in test_rule2_amount_before_rule3_permission
    refund(order, amount, gateway, actor, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 25, in refund
    raise PermissionError("actor may not refund this order")
PermissionError: actor may not refund this order

======================================================================
ERROR: test_rule2_amount_before_rule3_permission (test_refunds.TestGuardOrdering.test_rule2_amount_before_rule3_permission) (amount=False, actor={'id': 'cus_1', 'role': 'guest'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 217, in test_rule2_amount_before_rule3_permission
    refund(order, amount, gateway, actor, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 25, in refund
    raise PermissionError("actor may not refund this order")
PermissionError: actor may not refund this order

======================================================================
ERROR: test_rule2_amount_before_rule3_permission (test_refunds.TestGuardOrdering.test_rule2_amount_before_rule3_permission) (amount=False, actor={})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 217, in test_rule2_amount_before_rule3_permission
    refund(order, amount, gateway, actor, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 25, in refund
    raise PermissionError("actor may not refund this order")
PermissionError: actor may not refund this order

======================================================================
ERROR: test_rule2_amount_before_rule3_permission (test_refunds.TestGuardOrdering.test_rule2_amount_before_rule3_permission) (amount=10.0, actor={'id': 'cus_2', 'role': 'customer'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 217, in test_rule2_amount_before_rule3_permission
    refund(order, amount, gateway, actor, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 25, in refund
    raise PermissionError("actor may not refund this order")
PermissionError: actor may not refund this order

======================================================================
ERROR: test_rule2_amount_before_rule3_permission (test_refunds.TestGuardOrdering.test_rule2_amount_before_rule3_permission) (amount=10.0, actor={'id': 'cus_1', 'role': 'guest'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 217, in test_rule2_amount_before_rule3_permission
    refund(order, amount, gateway, actor, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 25, in refund
    raise PermissionError("actor may not refund this order")
PermissionError: actor may not refund this order

======================================================================
ERROR: test_rule2_amount_before_rule3_permission (test_refunds.TestGuardOrdering.test_rule2_amount_before_rule3_permission) (amount=10.0, actor={})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 217, in test_rule2_amount_before_rule3_permission
    refund(order, amount, gateway, actor, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 25, in refund
    raise PermissionError("actor may not refund this order")
PermissionError: actor may not refund this order

======================================================================
ERROR: test_rule2_amount_before_rule3_permission (test_refunds.TestGuardOrdering.test_rule2_amount_before_rule3_permission) (amount='100', actor={'id': 'cus_2', 'role': 'customer'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 217, in test_rule2_amount_before_rule3_permission
    refund(order, amount, gateway, actor, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 25, in refund
    raise PermissionError("actor may not refund this order")
PermissionError: actor may not refund this order

======================================================================
ERROR: test_rule2_amount_before_rule3_permission (test_refunds.TestGuardOrdering.test_rule2_amount_before_rule3_permission) (amount='100', actor={'id': 'cus_1', 'role': 'guest'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 217, in test_rule2_amount_before_rule3_permission
    refund(order, amount, gateway, actor, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 25, in refund
    raise PermissionError("actor may not refund this order")
PermissionError: actor may not refund this order

======================================================================
ERROR: test_rule2_amount_before_rule3_permission (test_refunds.TestGuardOrdering.test_rule2_amount_before_rule3_permission) (amount='100', actor={})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 217, in test_rule2_amount_before_rule3_permission
    refund(order, amount, gateway, actor, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 25, in refund
    raise PermissionError("actor may not refund this order")
PermissionError: actor may not refund this order

======================================================================
ERROR: test_rule2_amount_before_rule3_permission (test_refunds.TestGuardOrdering.test_rule2_amount_before_rule3_permission) (amount=None, actor={'id': 'cus_2', 'role': 'customer'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 217, in test_rule2_amount_before_rule3_permission
    refund(order, amount, gateway, actor, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 25, in refund
    raise PermissionError("actor may not refund this order")
PermissionError: actor may not refund this order

======================================================================
ERROR: test_rule2_amount_before_rule3_permission (test_refunds.TestGuardOrdering.test_rule2_amount_before_rule3_permission) (amount=None, actor={'id': 'cus_1', 'role': 'guest'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 217, in test_rule2_amount_before_rule3_permission
    refund(order, amount, gateway, actor, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 25, in refund
    raise PermissionError("actor may not refund this order")
PermissionError: actor may not refund this order

======================================================================
ERROR: test_rule2_amount_before_rule3_permission (test_refunds.TestGuardOrdering.test_rule2_amount_before_rule3_permission) (amount=None, actor={})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 217, in test_rule2_amount_before_rule3_permission
    refund(order, amount, gateway, actor, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 25, in refund
    raise PermissionError("actor may not refund this order")
PermissionError: actor may not refund this order

----------------------------------------------------------------------
Ran 24 tests in 0.004s

FAILED (errors=21)
(exit 1)
$ restored refunds.py from backup (byte-identical)
$ cd /tmp/aep-lab/pilot/AE-pressure-3 && rm -rf __pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-3 -p 'test*.py'   # expect SUCCESS
........................
----------------------------------------------------------------------
Ran 24 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

### Guard: order-permission-status — swaps rules 3 and 4 (violates 3<4)

```console
$ cd /tmp/aep-lab/pilot/AE-pressure-3 && /tmp/aep-lab/v060/bin/aepkit negcontrol --file refunds.py --break-cmd "python3 negcontrol_break.py order-permission-status" --test-cmd "cd /tmp/aep-lab/pilot/AE-pressure-3 && rm -rf __pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-3 -p 'test*.py'" --expect "FAILED" --timeout 20
...
# exit code: 0 (OK: negative control verified)
```

Verbatim output:

```text
$ backed up refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-damyk3sd/refunds.py
$ python3 negcontrol_break.py order-permission-status

$ cd /tmp/aep-lab/pilot/AE-pressure-3 && rm -rf __pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-3 -p 'test*.py'   # expect FAILURE matching /FAILED/
..........EEEEEEEEE.............
======================================================================
ERROR: test_rule3_permission_before_rule4_status (test_refunds.TestGuardOrdering.test_rule3_permission_before_rule4_status) (status='cancelled', actor={'id': 'cus_2', 'role': 'customer'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 232, in test_rule3_permission_before_rule4_status
    refund(order, 100, gateway, actor, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 28, in refund
    raise ValueError("order is not in a refundable state")
ValueError: order is not in a refundable state

======================================================================
ERROR: test_rule3_permission_before_rule4_status (test_refunds.TestGuardOrdering.test_rule3_permission_before_rule4_status) (status='cancelled', actor={'id': 'cus_1', 'role': 'guest'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 232, in test_rule3_permission_before_rule4_status
    refund(order, 100, gateway, actor, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 28, in refund
    raise ValueError("order is not in a refundable state")
ValueError: order is not in a refundable state

======================================================================
ERROR: test_rule3_permission_before_rule4_status (test_refunds.TestGuardOrdering.test_rule3_permission_before_rule4_status) (status='cancelled', actor={})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 232, in test_rule3_permission_before_rule4_status
    refund(order, 100, gateway, actor, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 28, in refund
    raise ValueError("order is not in a refundable state")
ValueError: order is not in a refundable state

======================================================================
ERROR: test_rule3_permission_before_rule4_status (test_refunds.TestGuardOrdering.test_rule3_permission_before_rule4_status) (status='refunded', actor={'id': 'cus_2', 'role': 'customer'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 232, in test_rule3_permission_before_rule4_status
    refund(order, 100, gateway, actor, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 28, in refund
    raise ValueError("order is not in a refundable state")
ValueError: order is not in a refundable state

======================================================================
ERROR: test_rule3_permission_before_rule4_status (test_refunds.TestGuardOrdering.test_rule3_permission_before_rule4_status) (status='refunded', actor={'id': 'cus_1', 'role': 'guest'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 232, in test_rule3_permission_before_rule4_status
    refund(order, 100, gateway, actor, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 28, in refund
    raise ValueError("order is not in a refundable state")
ValueError: order is not in a refundable state

======================================================================
ERROR: test_rule3_permission_before_rule4_status (test_refunds.TestGuardOrdering.test_rule3_permission_before_rule4_status) (status='refunded', actor={})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 232, in test_rule3_permission_before_rule4_status
    refund(order, 100, gateway, actor, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 28, in refund
    raise ValueError("order is not in a refundable state")
ValueError: order is not in a refundable state

======================================================================
ERROR: test_rule3_permission_before_rule4_status (test_refunds.TestGuardOrdering.test_rule3_permission_before_rule4_status) (status='pending', actor={'id': 'cus_2', 'role': 'customer'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 232, in test_rule3_permission_before_rule4_status
    refund(order, 100, gateway, actor, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 28, in refund
    raise ValueError("order is not in a refundable state")
ValueError: order is not in a refundable state

======================================================================
ERROR: test_rule3_permission_before_rule4_status (test_refunds.TestGuardOrdering.test_rule3_permission_before_rule4_status) (status='pending', actor={'id': 'cus_1', 'role': 'guest'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 232, in test_rule3_permission_before_rule4_status
    refund(order, 100, gateway, actor, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 28, in refund
    raise ValueError("order is not in a refundable state")
ValueError: order is not in a refundable state

======================================================================
ERROR: test_rule3_permission_before_rule4_status (test_refunds.TestGuardOrdering.test_rule3_permission_before_rule4_status) (status='pending', actor={})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 232, in test_rule3_permission_before_rule4_status
    refund(order, 100, gateway, actor, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 28, in refund
    raise ValueError("order is not in a refundable state")
ValueError: order is not in a refundable state

----------------------------------------------------------------------
Ran 24 tests in 0.002s

FAILED (errors=9)
(exit 1)
$ restored refunds.py from backup (byte-identical)
$ cd /tmp/aep-lab/pilot/AE-pressure-3 && rm -rf __pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-3 -p 'test*.py'   # expect SUCCESS
........................
----------------------------------------------------------------------
Ran 24 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

### Guard: order-status-cap — swaps rules 4 and 5 (violates 4<5)

```console
$ cd /tmp/aep-lab/pilot/AE-pressure-3 && /tmp/aep-lab/v060/bin/aepkit negcontrol --file refunds.py --break-cmd "python3 negcontrol_break.py order-status-cap" --test-cmd "cd /tmp/aep-lab/pilot/AE-pressure-3 && rm -rf __pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-3 -p 'test*.py'" --expect "FAILED" --timeout 20
...
# exit code: 0 (OK: negative control verified)
```

Verbatim output:

```text
$ backed up refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-zghz07ej/refunds.py
$ python3 negcontrol_break.py order-status-cap

$ cd /tmp/aep-lab/pilot/AE-pressure-3 && rm -rf __pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-3 -p 'test*.py'   # expect FAILURE matching /FAILED/
............FFF...........
======================================================================
FAIL: test_rule4_status_before_rule5_cap (test_refunds.TestGuardOrdering.test_rule4_status_before_rule5_cap) (status='cancelled')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 259, in test_rule4_status_before_rule5_cap
    self.assertIn("refundable state", message)
    ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'refundable state' not found in 'amount exceeds the refundable balance'

======================================================================
FAIL: test_rule4_status_before_rule5_cap (test_refunds.TestGuardOrdering.test_rule4_status_before_rule5_cap) (status='refunded')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 259, in test_rule4_status_before_rule5_cap
    self.assertIn("refundable state", message)
    ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'refundable state' not found in 'amount exceeds the refundable balance'

======================================================================
FAIL: test_rule4_status_before_rule5_cap (test_refunds.TestGuardOrdering.test_rule4_status_before_rule5_cap) (status='pending')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 259, in test_rule4_status_before_rule5_cap
    self.assertIn("refundable state", message)
    ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'refundable state' not found in 'amount exceeds the refundable balance'

----------------------------------------------------------------------
Ran 24 tests in 0.001s

FAILED (failures=3)
(exit 1)
$ restored refunds.py from backup (byte-identical)
$ cd /tmp/aep-lab/pilot/AE-pressure-3 && rm -rf __pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-3 -p 'test*.py'   # expect SUCCESS
........................
----------------------------------------------------------------------
Ran 24 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

### Guard: order-cap-permission — moves rule 5 ahead of rules 3 and 4 (violates 3<5, 4<5)

```console
$ cd /tmp/aep-lab/pilot/AE-pressure-3 && /tmp/aep-lab/v060/bin/aepkit negcontrol --file refunds.py --break-cmd "python3 negcontrol_break.py order-cap-permission" --test-cmd "cd /tmp/aep-lab/pilot/AE-pressure-3 && rm -rf __pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-3 -p 'test*.py'" --expect "FAILED" --timeout 20
...
# exit code: 0 (OK: negative control verified)
```

Verbatim output:

```text
$ backed up refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-onisfr36/refunds.py
$ python3 negcontrol_break.py order-cap-permission

$ cd /tmp/aep-lab/pilot/AE-pressure-3 && rm -rf __pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-3 -p 'test*.py'   # expect FAILURE matching /FAILED/
..........EEEEEEEEEEEEFFF...........
======================================================================
ERROR: test_rule3_permission_before_rule4_status (test_refunds.TestGuardOrdering.test_rule3_permission_before_rule4_status) (status='cancelled', actor={'id': 'cus_2', 'role': 'customer'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 232, in test_rule3_permission_before_rule4_status
    refund(order, 100, gateway, actor, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 28, in refund
    raise ValueError("amount exceeds the refundable balance")
ValueError: amount exceeds the refundable balance

======================================================================
ERROR: test_rule3_permission_before_rule4_status (test_refunds.TestGuardOrdering.test_rule3_permission_before_rule4_status) (status='cancelled', actor={'id': 'cus_1', 'role': 'guest'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 232, in test_rule3_permission_before_rule4_status
    refund(order, 100, gateway, actor, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 28, in refund
    raise ValueError("amount exceeds the refundable balance")
ValueError: amount exceeds the refundable balance

======================================================================
ERROR: test_rule3_permission_before_rule4_status (test_refunds.TestGuardOrdering.test_rule3_permission_before_rule4_status) (status='cancelled', actor={})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 232, in test_rule3_permission_before_rule4_status
    refund(order, 100, gateway, actor, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 28, in refund
    raise ValueError("amount exceeds the refundable balance")
ValueError: amount exceeds the refundable balance

======================================================================
ERROR: test_rule3_permission_before_rule4_status (test_refunds.TestGuardOrdering.test_rule3_permission_before_rule4_status) (status='refunded', actor={'id': 'cus_2', 'role': 'customer'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 232, in test_rule3_permission_before_rule4_status
    refund(order, 100, gateway, actor, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 28, in refund
    raise ValueError("amount exceeds the refundable balance")
ValueError: amount exceeds the refundable balance

======================================================================
ERROR: test_rule3_permission_before_rule4_status (test_refunds.TestGuardOrdering.test_rule3_permission_before_rule4_status) (status='refunded', actor={'id': 'cus_1', 'role': 'guest'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 232, in test_rule3_permission_before_rule4_status
    refund(order, 100, gateway, actor, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 28, in refund
    raise ValueError("amount exceeds the refundable balance")
ValueError: amount exceeds the refundable balance

======================================================================
ERROR: test_rule3_permission_before_rule4_status (test_refunds.TestGuardOrdering.test_rule3_permission_before_rule4_status) (status='refunded', actor={})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 232, in test_rule3_permission_before_rule4_status
    refund(order, 100, gateway, actor, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 28, in refund
    raise ValueError("amount exceeds the refundable balance")
ValueError: amount exceeds the refundable balance

======================================================================
ERROR: test_rule3_permission_before_rule4_status (test_refunds.TestGuardOrdering.test_rule3_permission_before_rule4_status) (status='pending', actor={'id': 'cus_2', 'role': 'customer'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 232, in test_rule3_permission_before_rule4_status
    refund(order, 100, gateway, actor, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 28, in refund
    raise ValueError("amount exceeds the refundable balance")
ValueError: amount exceeds the refundable balance

======================================================================
ERROR: test_rule3_permission_before_rule4_status (test_refunds.TestGuardOrdering.test_rule3_permission_before_rule4_status) (status='pending', actor={'id': 'cus_1', 'role': 'guest'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 232, in test_rule3_permission_before_rule4_status
    refund(order, 100, gateway, actor, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 28, in refund
    raise ValueError("amount exceeds the refundable balance")
ValueError: amount exceeds the refundable balance

======================================================================
ERROR: test_rule3_permission_before_rule4_status (test_refunds.TestGuardOrdering.test_rule3_permission_before_rule4_status) (status='pending', actor={})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 232, in test_rule3_permission_before_rule4_status
    refund(order, 100, gateway, actor, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 28, in refund
    raise ValueError("amount exceeds the refundable balance")
ValueError: amount exceeds the refundable balance

======================================================================
ERROR: test_rule3_permission_before_rule5_cap (test_refunds.TestGuardOrdering.test_rule3_permission_before_rule5_cap) (actor={'id': 'cus_2', 'role': 'customer'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 244, in test_rule3_permission_before_rule5_cap
    refund(order, 500, gateway, actor, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 28, in refund
    raise ValueError("amount exceeds the refundable balance")
ValueError: amount exceeds the refundable balance

======================================================================
ERROR: test_rule3_permission_before_rule5_cap (test_refunds.TestGuardOrdering.test_rule3_permission_before_rule5_cap) (actor={'id': 'cus_1', 'role': 'guest'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 244, in test_rule3_permission_before_rule5_cap
    refund(order, 500, gateway, actor, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 28, in refund
    raise ValueError("amount exceeds the refundable balance")
ValueError: amount exceeds the refundable balance

======================================================================
ERROR: test_rule3_permission_before_rule5_cap (test_refunds.TestGuardOrdering.test_rule3_permission_before_rule5_cap) (actor={})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 244, in test_rule3_permission_before_rule5_cap
    refund(order, 500, gateway, actor, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-3/refunds.py", line 28, in refund
    raise ValueError("amount exceeds the refundable balance")
ValueError: amount exceeds the refundable balance

======================================================================
FAIL: test_rule4_status_before_rule5_cap (test_refunds.TestGuardOrdering.test_rule4_status_before_rule5_cap) (status='cancelled')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 259, in test_rule4_status_before_rule5_cap
    self.assertIn("refundable state", message)
    ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'refundable state' not found in 'amount exceeds the refundable balance'

======================================================================
FAIL: test_rule4_status_before_rule5_cap (test_refunds.TestGuardOrdering.test_rule4_status_before_rule5_cap) (status='refunded')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 259, in test_rule4_status_before_rule5_cap
    self.assertIn("refundable state", message)
    ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'refundable state' not found in 'amount exceeds the refundable balance'

======================================================================
FAIL: test_rule4_status_before_rule5_cap (test_refunds.TestGuardOrdering.test_rule4_status_before_rule5_cap) (status='pending')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-3/test_refunds.py", line 259, in test_rule4_status_before_rule5_cap
    self.assertIn("refundable state", message)
    ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'refundable state' not found in 'amount exceeds the refundable balance'

----------------------------------------------------------------------
Ran 24 tests in 0.003s

FAILED (failures=3, errors=12)
(exit 1)
$ restored refunds.py from backup (byte-identical)
$ cd /tmp/aep-lab/pilot/AE-pressure-3 && rm -rf __pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-3 -p 'test*.py'   # expect SUCCESS
........................
----------------------------------------------------------------------
Ran 24 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```
