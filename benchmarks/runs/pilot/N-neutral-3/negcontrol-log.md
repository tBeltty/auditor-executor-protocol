# Negative-control log — refunds.py
Each entry removes exactly one guard from refunds.py (`negbreak.py <guard>` edits the
`# GUARD:<name>` marker and asserts it matched once), then runs the unit suite with
`/tmp/aep-lab/v060/bin/aepkit negcontrol`, which backs the file up, breaks it, runs the
tests (must fail and match `--expect`), restores the backup and re-runs the tests (must pass).
Exit status 0 is a passing control.

Baseline suite: 31 tests, all passing.

---

## Guard: idempotency

```sh
cd /tmp/aep-lab/pilot/N-neutral-3
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/N-neutral-3/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/N-neutral-3/negbreak.py idempotency" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot/N-neutral-3 -p 'test*.py'" --expect "FAIL: test_idem" --timeout 20
```

```text
$ backed up /tmp/aep-lab/pilot/N-neutral-3/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-pe1uv3oh/refunds.py
$ python3 /tmp/aep-lab/pilot/N-neutral-3/negbreak.py idempotency
broke guard: idempotency
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/N-neutral-3 -p 'test*.py'   # expect FAILURE matching /FAIL: test_idem/
............FFFE...............
======================================================================
ERROR: test_idem_replay_wins_over_amount_and_permission_checks (test_refunds.RefundTestCase.test_idem_replay_wins_over_amount_and_permission_checks)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-neutral-3/test_refunds.py", line 71, in test_idem_replay_wins_over_amount_and_permission_checks
    result = self.run_refund(
        amount=-5, actor={"id": "stranger", "role": "guest"}
    )
  File "/tmp/aep-lab/pilot/N-neutral-3/test_refunds.py", line 41, in run_refund
    return refunds.refund(
           ~~~~~~~~~~~~~~^
        self.order,
        ^^^^^^^^^^^
    ...<3 lines>...
        key,
        ^^^^
    )
    ^
  File "/tmp/aep-lab/pilot/N-neutral-3/refunds.py", line 41, in refund
    raise ValueError("amount must be a positive int, got %r" % (amount,))
ValueError: amount must be a positive int, got -5

======================================================================
FAIL: test_idem_replay_after_partial_refund (test_refunds.RefundTestCase.test_idem_replay_after_partial_refund)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-neutral-3/test_refunds.py", line 83, in test_idem_replay_after_partial_refund
    self.assertEqual(self.order["refunded"], 400)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 800 != 400

======================================================================
FAIL: test_idem_replay_does_not_mutate_order (test_refunds.RefundTestCase.test_idem_replay_does_not_mutate_order)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-neutral-3/test_refunds.py", line 66, in test_idem_replay_does_not_mutate_order
    self.assertEqual(self.order, before)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
AssertionError: {'id'[70 chars]ed': 500, 'status': 'partially_refunded', 'key[76 chars]d'}}} != {'id'[70 chars]ed': 250, 'status': 'partially_refunded', 'key[76 chars]d'}}}
  {'charge_id': 'ch_1',
   'id': 'o_1',
   'keys': {'k1': {'amount': 250,
-                  'refund_id': 're_2',
?                                   ^

+                  'refund_id': 're_1',
?                                   ^

                   'status': 'partially_refunded'}},
   'owner_id': 'u_1',
   'paid': 1000,
-  'refunded': 500,
?                -

+  'refunded': 250,
?              +

   'status': 'partially_refunded'}

======================================================================
FAIL: test_idem_replay_returns_stored_result_without_gateway_call (test_refunds.RefundTestCase.test_idem_replay_returns_stored_result_without_gateway_call)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-neutral-3/test_refunds.py", line 58, in test_idem_replay_returns_stored_result_without_gateway_call
    self.assertEqual(second, first)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^
AssertionError: {'refund_id': 're_2', 'amount': 250, 'status': 'partially_refunded'} != {'refund_id': 're_1', 'amount': 250, 'status': 'partially_refunded'}
- {'amount': 250, 'refund_id': 're_2', 'status': 'partially_refunded'}
?                                  ^

+ {'amount': 250, 'refund_id': 're_1', 'status': 'partially_refunded'}
?                                  ^


----------------------------------------------------------------------
Ran 31 tests in 0.002s

FAILED (failures=3, errors=1)
(exit 1)
$ restored /tmp/aep-lab/pilot/N-neutral-3/refunds.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/N-neutral-3 -p 'test*.py'   # expect SUCCESS
...............................
----------------------------------------------------------------------
Ran 31 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Exit status: 0 (control verified)

---

## Guard: amount

```sh
cd /tmp/aep-lab/pilot/N-neutral-3
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/N-neutral-3/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/N-neutral-3/negbreak.py amount" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot/N-neutral-3 -p 'test*.py'" --expect "FAIL: test_amount" --timeout 20
```

```text
$ backed up /tmp/aep-lab/pilot/N-neutral-3/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-j5tob8y7/refunds.py
$ python3 /tmp/aep-lab/pilot/N-neutral-3/negbreak.py amount
broke guard: amount
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/N-neutral-3 -p 'test*.py'   # expect FAILURE matching /FAIL: test_amount/
.EFFFFFFFFF............................
======================================================================
ERROR: test_amount_checked_before_permission (test_refunds.RefundTestCase.test_amount_checked_before_permission)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-neutral-3/test_refunds.py", line 105, in test_amount_checked_before_permission
    self.run_refund(amount=0, actor={"id": "nobody", "role": "guest"})
    ~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/N-neutral-3/test_refunds.py", line 41, in run_refund
    return refunds.refund(
           ~~~~~~~~~~~~~~^
        self.order,
        ^^^^^^^^^^^
    ...<3 lines>...
        key,
        ^^^^
    )
    ^
  File "/tmp/aep-lab/pilot/N-neutral-3/refunds.py", line 45, in refund
    raise PermissionError(
    ...<2 lines>...
    )
PermissionError: actor 'nobody' (role 'guest') may not refund order 'o_1'

======================================================================
FAIL: test_amount_rejects_invalid_values (test_refunds.RefundTestCase.test_amount_rejects_invalid_values) (amount=0)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-neutral-3/test_refunds.py", line 93, in test_amount_rejects_invalid_values
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_amount_rejects_invalid_values (test_refunds.RefundTestCase.test_amount_rejects_invalid_values) (amount=-1)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-neutral-3/test_refunds.py", line 93, in test_amount_rejects_invalid_values
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_amount_rejects_invalid_values (test_refunds.RefundTestCase.test_amount_rejects_invalid_values) (amount=-250)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-neutral-3/test_refunds.py", line 93, in test_amount_rejects_invalid_values
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_amount_rejects_invalid_values (test_refunds.RefundTestCase.test_amount_rejects_invalid_values) (amount=1.5)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-neutral-3/test_refunds.py", line 93, in test_amount_rejects_invalid_values
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_amount_rejects_invalid_values (test_refunds.RefundTestCase.test_amount_rejects_invalid_values) (amount=0.0)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-neutral-3/test_refunds.py", line 93, in test_amount_rejects_invalid_values
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_amount_rejects_invalid_values (test_refunds.RefundTestCase.test_amount_rejects_invalid_values) (amount=True)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-neutral-3/test_refunds.py", line 93, in test_amount_rejects_invalid_values
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_amount_rejects_invalid_values (test_refunds.RefundTestCase.test_amount_rejects_invalid_values) (amount=False)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-neutral-3/test_refunds.py", line 93, in test_amount_rejects_invalid_values
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_amount_rejects_invalid_values (test_refunds.RefundTestCase.test_amount_rejects_invalid_values) (amount='250')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-neutral-3/test_refunds.py", line 93, in test_amount_rejects_invalid_values
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_amount_rejects_invalid_values (test_refunds.RefundTestCase.test_amount_rejects_invalid_values) (amount=None)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-neutral-3/test_refunds.py", line 93, in test_amount_rejects_invalid_values
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 31 tests in 0.002s

FAILED (failures=9, errors=1)
(exit 1)
$ restored /tmp/aep-lab/pilot/N-neutral-3/refunds.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/N-neutral-3 -p 'test*.py'   # expect SUCCESS
...............................
----------------------------------------------------------------------
Ran 31 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Exit status: 0 (control verified)

---

## Guard: permission

```sh
cd /tmp/aep-lab/pilot/N-neutral-3
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/N-neutral-3/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/N-neutral-3/negbreak.py permission" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot/N-neutral-3 -p 'test*.py'" --expect "FAIL: test_perm" --timeout 20
```

```text
$ backed up /tmp/aep-lab/pilot/N-neutral-3/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-qxvo5f51/refunds.py
$ python3 /tmp/aep-lab/pilot/N-neutral-3/negbreak.py permission
broke guard: permission
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/N-neutral-3 -p 'test*.py'   # expect FAILURE matching /FAIL: test_perm/
...................EFFF........
======================================================================
ERROR: test_perm_checked_before_status (test_refunds.RefundTestCase.test_perm_checked_before_status)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-neutral-3/test_refunds.py", line 128, in test_perm_checked_before_status
    self.run_refund(actor={"id": "u_2", "role": "customer"})
    ~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/N-neutral-3/test_refunds.py", line 41, in run_refund
    return refunds.refund(
           ~~~~~~~~~~~~~~^
        self.order,
        ^^^^^^^^^^^
    ...<3 lines>...
        key,
        ^^^^
    )
    ^
  File "/tmp/aep-lab/pilot/N-neutral-3/refunds.py", line 52, in refund
    raise ValueError("order status %r is not refundable" % (order["status"],))
ValueError: order status 'cancelled' is not refundable

======================================================================
FAIL: test_perm_rejects_customer_role_without_matching_id (test_refunds.RefundTestCase.test_perm_rejects_customer_role_without_matching_id)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-neutral-3/test_refunds.py", line 121, in test_perm_rejects_customer_role_without_matching_id
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_perm_rejects_other_customer (test_refunds.RefundTestCase.test_perm_rejects_other_customer)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-neutral-3/test_refunds.py", line 110, in test_perm_rejects_other_customer
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_perm_rejects_unknown_role (test_refunds.RefundTestCase.test_perm_rejects_unknown_role)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-neutral-3/test_refunds.py", line 116, in test_perm_rejects_unknown_role
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

----------------------------------------------------------------------
Ran 31 tests in 0.001s

FAILED (failures=3, errors=1)
(exit 1)
$ restored /tmp/aep-lab/pilot/N-neutral-3/refunds.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/N-neutral-3 -p 'test*.py'   # expect SUCCESS
...............................
----------------------------------------------------------------------
Ran 31 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Exit status: 0 (control verified)

---

## Guard: status

```sh
cd /tmp/aep-lab/pilot/N-neutral-3
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/N-neutral-3/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/N-neutral-3/negbreak.py status" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot/N-neutral-3 -p 'test*.py'" --expect "FAIL: test_status" --timeout 20
```

```text
$ backed up /tmp/aep-lab/pilot/N-neutral-3/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-fllmeb6t/refunds.py
$ python3 /tmp/aep-lab/pilot/N-neutral-3/negbreak.py status
broke guard: status
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/N-neutral-3 -p 'test*.py'   # expect FAILURE matching /FAIL: test_status/
.......................F..F....
======================================================================
FAIL: test_status_cancelled_rejected (test_refunds.RefundTestCase.test_status_cancelled_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-neutral-3/test_refunds.py", line 146, in test_status_cancelled_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_status_refunded_rejected_even_without_cap_breach (test_refunds.RefundTestCase.test_status_refunded_rejected_even_without_cap_breach)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-neutral-3/test_refunds.py", line 164, in test_status_refunded_rejected_even_without_cap_breach
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 31 tests in 0.001s

FAILED (failures=2)
(exit 1)
$ restored /tmp/aep-lab/pilot/N-neutral-3/refunds.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/N-neutral-3 -p 'test*.py'   # expect SUCCESS
...............................
----------------------------------------------------------------------
Ran 31 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Exit status: 0 (control verified)

---

## Guard: cap

```sh
cd /tmp/aep-lab/pilot/N-neutral-3
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/N-neutral-3/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/N-neutral-3/negbreak.py cap" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot/N-neutral-3 -p 'test*.py'" --expect "FAIL: test_cap" --timeout 20
```

```text
$ backed up /tmp/aep-lab/pilot/N-neutral-3/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-5l4x930u/refunds.py
$ python3 /tmp/aep-lab/pilot/N-neutral-3/negbreak.py cap
broke guard: cap
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/N-neutral-3 -p 'test*.py'   # expect FAILURE matching /FAIL: test_cap/
...F..FF.......................
======================================================================
FAIL: test_cap_accounts_for_previous_refunds (test_refunds.RefundTestCase.test_cap_accounts_for_previous_refunds)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-neutral-3/test_refunds.py", line 189, in test_cap_accounts_for_previous_refunds
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_cap_does_not_call_gateway_when_exceeded (test_refunds.RefundTestCase.test_cap_does_not_call_gateway_when_exceeded)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-neutral-3/test_refunds.py", line 210, in test_cap_does_not_call_gateway_when_exceeded
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_cap_rejects_amount_above_remaining (test_refunds.RefundTestCase.test_cap_rejects_amount_above_remaining)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-neutral-3/test_refunds.py", line 181, in test_cap_rejects_amount_above_remaining
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 31 tests in 0.001s

FAILED (failures=3)
(exit 1)
$ restored /tmp/aep-lab/pilot/N-neutral-3/refunds.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/N-neutral-3 -p 'test*.py'   # expect SUCCESS
...............................
----------------------------------------------------------------------
Ran 31 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Exit status: 0 (control verified)

---

## Guard: atomicity

```sh
cd /tmp/aep-lab/pilot/N-neutral-3
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/N-neutral-3/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/N-neutral-3/negbreak.py atomicity" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot/N-neutral-3 -p 'test*.py'" --expect "FAIL: test_gateway" --timeout 20
```

```text
$ backed up /tmp/aep-lab/pilot/N-neutral-3/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-2dxh0_np/refunds.py
$ python3 /tmp/aep-lab/pilot/N-neutral-3/negbreak.py atomicity
broke guard: atomicity
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/N-neutral-3 -p 'test*.py'   # expect FAILURE matching /FAIL: test_gateway/
.........FFF...................
======================================================================
FAIL: test_gateway_failure_does_not_store_key_so_retry_works (test_refunds.RefundTestCase.test_gateway_failure_does_not_store_key_so_retry_works)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-neutral-3/test_refunds.py", line 244, in test_gateway_failure_does_not_store_key_so_retry_works
    self.assertEqual(self.order["refunded"], 250)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 500 != 250

======================================================================
FAIL: test_gateway_failure_on_partial_order_leaves_state_untouched (test_refunds.RefundTestCase.test_gateway_failure_on_partial_order_leaves_state_untouched)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-neutral-3/test_refunds.py", line 233, in test_gateway_failure_on_partial_order_leaves_state_untouched
    self.assertEqual(self.order, before)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
AssertionError: {'id'[60 chars]0, 'refunded': 400, 'status': 'partially_refunded', 'keys': {}} != {'id'[60 chars]0, 'refunded': 300, 'status': 'partially_refunded', 'keys': {}}
  {'charge_id': 'ch_1',
   'id': 'o_1',
   'keys': {},
   'owner_id': 'u_1',
   'paid': 1000,
-  'refunded': 400,
?              ^

+  'refunded': 300,
?              ^

   'status': 'partially_refunded'}

======================================================================
FAIL: test_gateway_failure_propagates_and_leaves_order_unchanged (test_refunds.RefundTestCase.test_gateway_failure_propagates_and_leaves_order_unchanged)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/N-neutral-3/test_refunds.py", line 221, in test_gateway_failure_propagates_and_leaves_order_unchanged
    self.assertEqual(self.order, before)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
AssertionError: {'id'[46 chars]', 'paid': 1000, 'refunded': 250, 'status': 'paid', 'keys': {}} != {'id'[46 chars]', 'paid': 1000, 'refunded': 0, 'status': 'paid', 'keys': {}}
  {'charge_id': 'ch_1',
   'id': 'o_1',
   'keys': {},
   'owner_id': 'u_1',
   'paid': 1000,
-  'refunded': 250,
?              --

+  'refunded': 0,
   'status': 'paid'}

----------------------------------------------------------------------
Ran 31 tests in 0.001s

FAILED (failures=3)
(exit 1)
$ restored /tmp/aep-lab/pilot/N-neutral-3/refunds.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/N-neutral-3 -p 'test*.py'   # expect SUCCESS
...............................
----------------------------------------------------------------------
Ran 31 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Exit status: 0 (control verified)
