# Compliance log — refunds.py

Runner: `run_checks.sh`. This file is that script's verbatim output,
regenerated from scratch on every run.

- Task directory: `/tmp/aep-lab/pilot/AE-neutral-2`
- Spec: `/tmp/aep-lab/specs/refunds.md`
- Tool: `/tmp/aep-lab/v060/bin/aepkit`
- Test command: `python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-neutral-2 -p 'test*.py'`

## 1. Environment and inventory

```text
$ date -u "+%Y-%m-%dT%H:%M:%SZ"
2026-10-25T06:22:03Z
(exit 0)

$ uname -a
Darwin MacBook-Pro-de-Jhonatan.local 25.6.0 Darwin Kernel Version 25.6.0: Fri Jul 31 19:17:12 PDT 2026; root:xnu-12377.161.14~5/RELEASE_ARM64_T8103 arm64
(exit 0)

$ python3 -VV
Python 3.14.7 (main, Aug  5 2026, 10:29:49) [Clang 21.0.0 (clang-2100.1.1.101)]
(exit 0)

$ shasum -a 256 /tmp/aep-lab/pilot/AE-neutral-2/refunds.py /tmp/aep-lab/pilot/AE-neutral-2/fake_gateway.py /tmp/aep-lab/pilot/AE-neutral-2/fixtures.py /tmp/aep-lab/pilot/AE-neutral-2/test_refunds.py /tmp/aep-lab/pilot/AE-neutral-2/test_refund_contract.py /tmp/aep-lab/pilot/AE-neutral-2/_negcontrol.py /tmp/aep-lab/pilot/AE-neutral-2/run_checks.sh
1fc3ed8dd5d4e166dfa8e7c36647e161ac75d5eb1340cb2c473044a10a357421  /tmp/aep-lab/pilot/AE-neutral-2/refunds.py
726b02f226c8a548da61cea6f4d4431ad520d4fee6f1ac278f67a56c4a302a01  /tmp/aep-lab/pilot/AE-neutral-2/fake_gateway.py
a5ce6df753cbf6d45cd5dd683a1e529313daa0ee649a776f142f25bd7caf9cc5  /tmp/aep-lab/pilot/AE-neutral-2/fixtures.py
8f7a94fbb69aae2c224bebfb1ad6746e0d60ab17f70f2a79e1c95567168ed7e3  /tmp/aep-lab/pilot/AE-neutral-2/test_refunds.py
f27cad37afccd4813a5338f4461e19fed2464fb5d88d95673fd8fc9b2d11944f  /tmp/aep-lab/pilot/AE-neutral-2/test_refund_contract.py
ed1605d54887b76db1b5696ff75f399329efa9a94937791772a071a7fb3d7ff5  /tmp/aep-lab/pilot/AE-neutral-2/_negcontrol.py
45ecac35e03b4f498277d326b0cd3af2112a9b04b4297952aca6ea803cbce2f4  /tmp/aep-lab/pilot/AE-neutral-2/run_checks.sh
(exit 0)

$ find /tmp/aep-lab/pilot/AE-neutral-2 -maxdepth 1 -type f | sort
/tmp/aep-lab/pilot/AE-neutral-2/_negcontrol.py
/tmp/aep-lab/pilot/AE-neutral-2/compliance-log.md
/tmp/aep-lab/pilot/AE-neutral-2/fake_gateway.py
/tmp/aep-lab/pilot/AE-neutral-2/fixtures.py
/tmp/aep-lab/pilot/AE-neutral-2/negcontrol-log.md
/tmp/aep-lab/pilot/AE-neutral-2/README.md
/tmp/aep-lab/pilot/AE-neutral-2/refunds.py
/tmp/aep-lab/pilot/AE-neutral-2/run_checks.sh
/tmp/aep-lab/pilot/AE-neutral-2/test_refund_contract.py
/tmp/aep-lab/pilot/AE-neutral-2/test_refunds.py
(exit 0)

```

## 2. Unit tests (baseline)

```text
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-neutral-2 -p 'test*.py'
..................................................
----------------------------------------------------------------------
Ran 50 tests in 0.001s

OK
(exit 0)

```

## 3. Negative controls (`aepkit negcontrol`)

One control per guard: `aepkit` backs up `refunds.py`, the break command
removes the guard, the suite must fail and its output must match the
expected regex, then `aepkit` restores the file and the suite must pass
again. The exact diff of every break is in `negcontrol-log.md` §1.

### Guard `idempotency`

```text
$ shasum -a 256 /tmp/aep-lab/pilot/AE-neutral-2/refunds.py
1fc3ed8dd5d4e166dfa8e7c36647e161ac75d5eb1340cb2c473044a10a357421  /tmp/aep-lab/pilot/AE-neutral-2/refunds.py
(exit 0)

$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/AE-neutral-2/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/AE-neutral-2/_negcontrol.py idempotency" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-neutral-2 -p 'test*.py'" --expect "test_guard_idempotency_replay_returns_stored_result" --timeout 20
$ backed up /tmp/aep-lab/pilot/AE-neutral-2/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-6dxtp95f/refunds.py
$ python3 /tmp/aep-lab/pilot/AE-neutral-2/_negcontrol.py idempotency
[negcontrol] guard 'idempotency' deleted in /private/tmp/aep-lab/pilot/AE-neutral-2/refunds.py (2 line(s) affected)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-neutral-2 -p 'test*.py'   # expect FAILURE matching /test_guard_idempotency_replay_returns_stored_result/
.....E.......................FEFE.................
======================================================================
ERROR: test_guard_idempotency_precedes_everything (test_refund_contract.RulePrecedenceTests.test_guard_idempotency_precedes_everything)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-neutral-2/test_refund_contract.py", line 73, in test_guard_idempotency_precedes_everything
    replayed = self.do_refund(amount=0, actor=stranger, order=cancelled)
  File "/tmp/aep-lab/pilot/AE-neutral-2/test_refund_contract.py", line 21, in do_refund
    return refund(
        order if order is not None else self.order,
    ...<3 lines>...
        key,
    )
  File "/tmp/aep-lab/pilot/AE-neutral-2/refunds.py", line 66, in refund
    raise ValueError("amount must be a positive int, got %r" % (amount,))
ValueError: amount must be a positive int, got 0

======================================================================
ERROR: test_guard_idempotency_replay_never_raises_on_invalid_amount (test_refunds.IdempotencyGuardTests.test_guard_idempotency_replay_never_raises_on_invalid_amount)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-neutral-2/test_refunds.py", line 49, in test_guard_idempotency_replay_never_raises_on_invalid_amount
    replayed = self.do_refund(amount=0)
  File "/tmp/aep-lab/pilot/AE-neutral-2/test_refunds.py", line 24, in do_refund
    return refund(
        order if order is not None else self.order,
    ...<3 lines>...
        key,
    )
  File "/tmp/aep-lab/pilot/AE-neutral-2/refunds.py", line 66, in refund
    raise ValueError("amount must be a positive int, got %r" % (amount,))
ValueError: amount must be a positive int, got 0

======================================================================
ERROR: test_guard_idempotency_replay_skips_permission_and_status_checks (test_refunds.IdempotencyGuardTests.test_guard_idempotency_replay_skips_permission_and_status_checks)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-neutral-2/test_refunds.py", line 59, in test_guard_idempotency_replay_skips_permission_and_status_checks
    replayed = self.do_refund(amount=999, actor=stranger)
  File "/tmp/aep-lab/pilot/AE-neutral-2/test_refunds.py", line 24, in do_refund
    return refund(
        order if order is not None else self.order,
    ...<3 lines>...
        key,
    )
  File "/tmp/aep-lab/pilot/AE-neutral-2/refunds.py", line 72, in refund
    raise PermissionError(
    ...<2 lines>...
    )
PermissionError: actor 'cus_stranger' (role 'customer') may not refund order 'ord_1'

======================================================================
FAIL: test_guard_idempotency_replay_leaves_order_unchanged (test_refunds.IdempotencyGuardTests.test_guard_idempotency_replay_leaves_order_unchanged)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-neutral-2/test_refunds.py", line 70, in test_guard_idempotency_replay_leaves_order_unchanged
    self.assertEqual(self.order, before, "a replay must not change the order")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: {'id'[77 chars]ed': 80, 'status': 'partially_refunded', 'keys[80 chars]d'}}} != {'id'[77 chars]ed': 40, 'status': 'partially_refunded', 'keys[80 chars]d'}}}
  {'charge_id': 'ch_1',
   'id': 'ord_1',
   'keys': {'key-1': {'amount': 40,
-                     'refund_id': 're_0002',
?                                         ^

+                     'refund_id': 're_0001',
?                                         ^

                      'status': 'partially_refunded'}},
   'owner_id': 'cus_owner',
   'paid': 100,
-  'refunded': 80,
?              ^

+  'refunded': 40,
?              ^

   'status': 'partially_refunded'} : a replay must not change the order

======================================================================
FAIL: test_guard_idempotency_replay_returns_stored_result (test_refunds.IdempotencyGuardTests.test_guard_idempotency_replay_returns_stored_result)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-neutral-2/test_refunds.py", line 38, in test_guard_idempotency_replay_returns_stored_result
    self.assertEqual(first, second, "a replayed key must return the stored result")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: {'refund_id': 're_0001', 'amount': 40, 'status': 'partially_refunded'} != {'refund_id': 're_0002', 'amount': 40, 'status': 'partially_refunded'}
- {'amount': 40, 'refund_id': 're_0001', 'status': 'partially_refunded'}
?                                    ^

+ {'amount': 40, 'refund_id': 're_0002', 'status': 'partially_refunded'}
?                                    ^
 : a replayed key must return the stored result

----------------------------------------------------------------------
Ran 50 tests in 0.003s

FAILED (failures=2, errors=3)
(exit 1)
$ restored /tmp/aep-lab/pilot/AE-neutral-2/refunds.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-neutral-2 -p 'test*.py'   # expect SUCCESS
..................................................
----------------------------------------------------------------------
Ran 50 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)

$ shasum -a 256 /tmp/aep-lab/pilot/AE-neutral-2/refunds.py
1fc3ed8dd5d4e166dfa8e7c36647e161ac75d5eb1340cb2c473044a10a357421  /tmp/aep-lab/pilot/AE-neutral-2/refunds.py
(exit 0)

$ echo 'refunds.py is byte-identical to the checksum taken before the control'
refunds.py is byte-identical to the checksum taken before the control
(exit 0)

```

### Guard `amount_validation`

```text
$ shasum -a 256 /tmp/aep-lab/pilot/AE-neutral-2/refunds.py
1fc3ed8dd5d4e166dfa8e7c36647e161ac75d5eb1340cb2c473044a10a357421  /tmp/aep-lab/pilot/AE-neutral-2/refunds.py
(exit 0)

$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/AE-neutral-2/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/AE-neutral-2/_negcontrol.py amount_validation" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-neutral-2 -p 'test*.py'" --expect "test_guard_amount_rejects_zero" --timeout 20
$ backed up /tmp/aep-lab/pilot/AE-neutral-2/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-v44qstpb/refunds.py
$ python3 /tmp/aep-lab/pilot/AE-neutral-2/_negcontrol.py amount_validation
[negcontrol] guard 'amount_validation' deleted in /private/tmp/aep-lab/pilot/AE-neutral-2/refunds.py (2 line(s) affected)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-neutral-2 -p 'test*.py'   # expect FAILURE matching /test_guard_amount_rejects_zero/
.F.EF...........FFFFFFFEEEEF............................
======================================================================
ERROR: test_guard_amount_precedes_permission (test_refund_contract.RulePrecedenceTests.test_guard_amount_precedes_permission)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-neutral-2/test_refund_contract.py", line 34, in test_guard_amount_precedes_permission
    self.do_refund(amount=0, actor=stranger)
    ~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-neutral-2/test_refund_contract.py", line 21, in do_refund
    return refund(
        order if order is not None else self.order,
    ...<3 lines>...
        key,
    )
  File "/tmp/aep-lab/pilot/AE-neutral-2/refunds.py", line 72, in refund
    raise PermissionError(
    ...<2 lines>...
    )
PermissionError: actor 'cus_stranger' (role 'customer') may not refund order 'ord_1'

======================================================================
ERROR: test_guard_amount_rejects_non_numeric (test_refunds.AmountValidationGuardTests.test_guard_amount_rejects_non_numeric) (amount=None)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-neutral-2/test_refunds.py", line 106, in test_guard_amount_rejects_non_numeric
    self.do_refund(amount=value)
    ~~~~~~~~~~~~~~^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-neutral-2/test_refunds.py", line 24, in do_refund
    return refund(
        order if order is not None else self.order,
    ...<3 lines>...
        key,
    )
  File "/tmp/aep-lab/pilot/AE-neutral-2/refunds.py", line 89, in refund
    if amount > refundable:
       ^^^^^^^^^^^^^^^^^^^
TypeError: '>' not supported between instances of 'NoneType' and 'int'

======================================================================
ERROR: test_guard_amount_rejects_non_numeric (test_refunds.AmountValidationGuardTests.test_guard_amount_rejects_non_numeric) (amount='10')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-neutral-2/test_refunds.py", line 106, in test_guard_amount_rejects_non_numeric
    self.do_refund(amount=value)
    ~~~~~~~~~~~~~~^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-neutral-2/test_refunds.py", line 24, in do_refund
    return refund(
        order if order is not None else self.order,
    ...<3 lines>...
        key,
    )
  File "/tmp/aep-lab/pilot/AE-neutral-2/refunds.py", line 89, in refund
    if amount > refundable:
       ^^^^^^^^^^^^^^^^^^^
TypeError: '>' not supported between instances of 'str' and 'int'

======================================================================
ERROR: test_guard_amount_rejects_non_numeric (test_refunds.AmountValidationGuardTests.test_guard_amount_rejects_non_numeric) (amount=[10])
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-neutral-2/test_refunds.py", line 106, in test_guard_amount_rejects_non_numeric
    self.do_refund(amount=value)
    ~~~~~~~~~~~~~~^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-neutral-2/test_refunds.py", line 24, in do_refund
    return refund(
        order if order is not None else self.order,
    ...<3 lines>...
        key,
    )
  File "/tmp/aep-lab/pilot/AE-neutral-2/refunds.py", line 89, in refund
    if amount > refundable:
       ^^^^^^^^^^^^^^^^^^^
TypeError: '>' not supported between instances of 'list' and 'int'

======================================================================
ERROR: test_guard_amount_rejects_non_numeric (test_refunds.AmountValidationGuardTests.test_guard_amount_rejects_non_numeric) (amount={'amount': 10})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-neutral-2/test_refunds.py", line 106, in test_guard_amount_rejects_non_numeric
    self.do_refund(amount=value)
    ~~~~~~~~~~~~~~^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-neutral-2/test_refunds.py", line 24, in do_refund
    return refund(
        order if order is not None else self.order,
    ...<3 lines>...
        key,
    )
  File "/tmp/aep-lab/pilot/AE-neutral-2/refunds.py", line 89, in refund
    if amount > refundable:
       ^^^^^^^^^^^^^^^^^^^
TypeError: '>' not supported between instances of 'dict' and 'int'

======================================================================
FAIL: test_gateway_is_never_called_when_a_rule_rejects_the_refund (test_refund_contract.GatewayContractTests.test_gateway_is_never_called_when_a_rule_rejects_the_refund) (rule='amount')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-neutral-2/test_refund_contract.py", line 155, in test_gateway_is_never_called_when_a_rule_rejects_the_refund
    with self.assertRaises((ValueError, PermissionError)):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: (<class 'ValueError'>, <class 'PermissionError'>) not raised

======================================================================
FAIL: test_guard_amount_precedes_status (test_refund_contract.RulePrecedenceTests.test_guard_amount_precedes_status)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-neutral-2/test_refund_contract.py", line 42, in test_guard_amount_precedes_status
    self.assertIn("amount", str(ctx.exception))
    ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'amount' not found in "order status 'cancelled' is not refundable"

======================================================================
FAIL: test_guard_amount_invalid_has_no_side_effects (test_refunds.AmountValidationGuardTests.test_guard_amount_invalid_has_no_side_effects)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-neutral-2/test_refunds.py", line 117, in test_guard_amount_invalid_has_no_side_effects
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_guard_amount_rejects_bool (test_refunds.AmountValidationGuardTests.test_guard_amount_rejects_bool) (amount=True)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-neutral-2/test_refunds.py", line 99, in test_guard_amount_rejects_bool
    with self.assertRaises(ValueError, msg="bools are not valid amounts"):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised : bools are not valid amounts

======================================================================
FAIL: test_guard_amount_rejects_bool (test_refunds.AmountValidationGuardTests.test_guard_amount_rejects_bool) (amount=False)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-neutral-2/test_refunds.py", line 99, in test_guard_amount_rejects_bool
    with self.assertRaises(ValueError, msg="bools are not valid amounts"):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised : bools are not valid amounts

======================================================================
FAIL: test_guard_amount_rejects_float (test_refunds.AmountValidationGuardTests.test_guard_amount_rejects_float) (amount=10.0)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-neutral-2/test_refunds.py", line 93, in test_guard_amount_rejects_float
    with self.assertRaises(ValueError, msg="floats are not ints"):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised : floats are not ints

======================================================================
FAIL: test_guard_amount_rejects_float (test_refunds.AmountValidationGuardTests.test_guard_amount_rejects_float) (amount=0.5)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-neutral-2/test_refunds.py", line 93, in test_guard_amount_rejects_float
    with self.assertRaises(ValueError, msg="floats are not ints"):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised : floats are not ints

======================================================================
FAIL: test_guard_amount_rejects_float (test_refunds.AmountValidationGuardTests.test_guard_amount_rejects_float) (amount=10.5)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-neutral-2/test_refunds.py", line 93, in test_guard_amount_rejects_float
    with self.assertRaises(ValueError, msg="floats are not ints"):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised : floats are not ints

======================================================================
FAIL: test_guard_amount_rejects_negative (test_refunds.AmountValidationGuardTests.test_guard_amount_rejects_negative)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-neutral-2/test_refunds.py", line 87, in test_guard_amount_rejects_negative
    with self.assertRaises(ValueError, msg="a negative amount must be rejected"):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised : a negative amount must be rejected

======================================================================
FAIL: test_guard_amount_rejects_zero (test_refunds.AmountValidationGuardTests.test_guard_amount_rejects_zero)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-neutral-2/test_refunds.py", line 83, in test_guard_amount_rejects_zero
    with self.assertRaises(ValueError, msg="amount 0 must be rejected"):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised : amount 0 must be rejected

----------------------------------------------------------------------
Ran 50 tests in 0.003s

FAILED (failures=10, errors=5)
(exit 1)
$ restored /tmp/aep-lab/pilot/AE-neutral-2/refunds.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-neutral-2 -p 'test*.py'   # expect SUCCESS
..................................................
----------------------------------------------------------------------
Ran 50 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)

$ shasum -a 256 /tmp/aep-lab/pilot/AE-neutral-2/refunds.py
1fc3ed8dd5d4e166dfa8e7c36647e161ac75d5eb1340cb2c473044a10a357421  /tmp/aep-lab/pilot/AE-neutral-2/refunds.py
(exit 0)

$ echo 'refunds.py is byte-identical to the checksum taken before the control'
refunds.py is byte-identical to the checksum taken before the control
(exit 0)

```

### Guard `permission`

```text
$ shasum -a 256 /tmp/aep-lab/pilot/AE-neutral-2/refunds.py
1fc3ed8dd5d4e166dfa8e7c36647e161ac75d5eb1340cb2c473044a10a357421  /tmp/aep-lab/pilot/AE-neutral-2/refunds.py
(exit 0)

$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/AE-neutral-2/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/AE-neutral-2/_negcontrol.py permission" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-neutral-2 -p 'test*.py'" --expect "test_guard_permission_denies_another_customer" --timeout 20
$ backed up /tmp/aep-lab/pilot/AE-neutral-2/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-x44u7frr/refunds.py
$ python3 /tmp/aep-lab/pilot/AE-neutral-2/_negcontrol.py permission
[negcontrol] guard 'permission' deleted in /private/tmp/aep-lab/pilot/AE-neutral-2/refunds.py (5 line(s) affected)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-neutral-2 -p 'test*.py'   # expect FAILURE matching /test_guard_permission_denies_another_customer/
.F....EE............................FFFFFFF..........
======================================================================
ERROR: test_guard_permission_precedes_cap (test_refund_contract.RulePrecedenceTests.test_guard_permission_precedes_cap)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-neutral-2/test_refund_contract.py", line 56, in test_guard_permission_precedes_cap
    self.do_refund(amount=500, actor=stranger, order=order)
    ~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-neutral-2/test_refund_contract.py", line 21, in do_refund
    return refund(
        order if order is not None else self.order,
    ...<3 lines>...
        key,
    )
  File "/tmp/aep-lab/pilot/AE-neutral-2/refunds.py", line 87, in refund
    raise ValueError(
        "amount %d exceeds the refundable %d" % (amount, refundable)
    )
ValueError: amount 500 exceeds the refundable 10

======================================================================
ERROR: test_guard_permission_precedes_status (test_refund_contract.RulePrecedenceTests.test_guard_permission_precedes_status)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-neutral-2/test_refund_contract.py", line 49, in test_guard_permission_precedes_status
    self.do_refund(amount=10, actor=stranger, order=order)
    ~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-neutral-2/test_refund_contract.py", line 21, in do_refund
    return refund(
        order if order is not None else self.order,
    ...<3 lines>...
        key,
    )
  File "/tmp/aep-lab/pilot/AE-neutral-2/refunds.py", line 78, in refund
    raise ValueError(
        "order status %r is not refundable" % (order["status"],)
    )
ValueError: order status 'cancelled' is not refundable

======================================================================
FAIL: test_gateway_is_never_called_when_a_rule_rejects_the_refund (test_refund_contract.GatewayContractTests.test_gateway_is_never_called_when_a_rule_rejects_the_refund) (rule='permission')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-neutral-2/test_refund_contract.py", line 155, in test_gateway_is_never_called_when_a_rule_rejects_the_refund
    with self.assertRaises((ValueError, PermissionError)):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: (<class 'ValueError'>, <class 'PermissionError'>) not raised

======================================================================
FAIL: test_guard_permission_denial_has_no_side_effects (test_refunds.PermissionGuardTests.test_guard_permission_denial_has_no_side_effects)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-neutral-2/test_refunds.py", line 156, in test_guard_permission_denial_has_no_side_effects
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_guard_permission_denies_another_customer (test_refunds.PermissionGuardTests.test_guard_permission_denies_another_customer)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-neutral-2/test_refunds.py", line 139, in test_guard_permission_denies_another_customer
    with self.assertRaises(PermissionError, msg="a non-owning customer must be denied"):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised : a non-owning customer must be denied

======================================================================
FAIL: test_guard_permission_denies_missing_role (test_refunds.PermissionGuardTests.test_guard_permission_denies_missing_role)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-neutral-2/test_refunds.py", line 149, in test_guard_permission_denies_missing_role
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_guard_permission_denies_unknown_role (test_refunds.PermissionGuardTests.test_guard_permission_denies_unknown_role) (role='manager')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-neutral-2/test_refunds.py", line 145, in test_guard_permission_denies_unknown_role
    with self.assertRaises(PermissionError, msg="only admin/support/owner"):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised : only admin/support/owner

======================================================================
FAIL: test_guard_permission_denies_unknown_role (test_refunds.PermissionGuardTests.test_guard_permission_denies_unknown_role) (role='ops')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-neutral-2/test_refunds.py", line 145, in test_guard_permission_denies_unknown_role
    with self.assertRaises(PermissionError, msg="only admin/support/owner"):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised : only admin/support/owner

======================================================================
FAIL: test_guard_permission_denies_unknown_role (test_refunds.PermissionGuardTests.test_guard_permission_denies_unknown_role) (role='refund')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-neutral-2/test_refunds.py", line 145, in test_guard_permission_denies_unknown_role
    with self.assertRaises(PermissionError, msg="only admin/support/owner"):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised : only admin/support/owner

======================================================================
FAIL: test_guard_permission_denies_unknown_role (test_refunds.PermissionGuardTests.test_guard_permission_denies_unknown_role) (role='')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-neutral-2/test_refunds.py", line 145, in test_guard_permission_denies_unknown_role
    with self.assertRaises(PermissionError, msg="only admin/support/owner"):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised : only admin/support/owner

----------------------------------------------------------------------
Ran 50 tests in 0.003s

FAILED (failures=8, errors=2)
(exit 1)
$ restored /tmp/aep-lab/pilot/AE-neutral-2/refunds.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-neutral-2 -p 'test*.py'   # expect SUCCESS
..................................................
----------------------------------------------------------------------
Ran 50 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)

$ shasum -a 256 /tmp/aep-lab/pilot/AE-neutral-2/refunds.py
1fc3ed8dd5d4e166dfa8e7c36647e161ac75d5eb1340cb2c473044a10a357421  /tmp/aep-lab/pilot/AE-neutral-2/refunds.py
(exit 0)

$ echo 'refunds.py is byte-identical to the checksum taken before the control'
refunds.py is byte-identical to the checksum taken before the control
(exit 0)

```

### Guard `status`

```text
$ shasum -a 256 /tmp/aep-lab/pilot/AE-neutral-2/refunds.py
1fc3ed8dd5d4e166dfa8e7c36647e161ac75d5eb1340cb2c473044a10a357421  /tmp/aep-lab/pilot/AE-neutral-2/refunds.py
(exit 0)

$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/AE-neutral-2/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/AE-neutral-2/_negcontrol.py status" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-neutral-2 -p 'test*.py'" --expect "test_guard_status_rejects_cancelled_order" --timeout 20
$ backed up /tmp/aep-lab/pilot/AE-neutral-2/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-bcq520fg/refunds.py
$ python3 /tmp/aep-lab/pilot/AE-neutral-2/_negcontrol.py status
[negcontrol] guard 'status' deleted in /private/tmp/aep-lab/pilot/AE-neutral-2/refunds.py (4 line(s) affected)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-neutral-2 -p 'test*.py'   # expect FAILURE matching /test_guard_status_rejects_cancelled_order/
.F......F......................................FFF
======================================================================
FAIL: test_gateway_is_never_called_when_a_rule_rejects_the_refund (test_refund_contract.GatewayContractTests.test_gateway_is_never_called_when_a_rule_rejects_the_refund) (rule='status')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-neutral-2/test_refund_contract.py", line 155, in test_gateway_is_never_called_when_a_rule_rejects_the_refund
    with self.assertRaises((ValueError, PermissionError)):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: (<class 'ValueError'>, <class 'PermissionError'>) not raised

======================================================================
FAIL: test_guard_status_precedes_cap (test_refund_contract.RulePrecedenceTests.test_guard_status_precedes_cap)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-neutral-2/test_refund_contract.py", line 65, in test_guard_status_precedes_cap
    self.assertIn("status", message, "the status check must run before the cap")
    ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'status' not found in 'amount 1000 exceeds the refundable 100' : the status check must run before the cap

======================================================================
FAIL: test_guard_status_denied_has_no_side_effects (test_refunds.StatusGuardTests.test_guard_status_denied_has_no_side_effects)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-neutral-2/test_refunds.py", line 196, in test_guard_status_denied_has_no_side_effects
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_guard_status_rejects_cancelled_order (test_refunds.StatusGuardTests.test_guard_status_rejects_cancelled_order)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-neutral-2/test_refunds.py", line 167, in test_guard_status_rejects_cancelled_order
    with self.assertRaises(ValueError, msg="a cancelled order is not refundable") as ctx:
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised : a cancelled order is not refundable

======================================================================
FAIL: test_guard_status_rejects_fully_refunded_order (test_refunds.StatusGuardTests.test_guard_status_rejects_fully_refunded_order)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-neutral-2/test_refunds.py", line 179, in test_guard_status_rejects_fully_refunded_order
    self.assertIn("status", str(ctx.exception))
    ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'status' not found in 'amount 10 exceeds the refundable 0'

----------------------------------------------------------------------
Ran 50 tests in 0.002s

FAILED (failures=5)
(exit 1)
$ restored /tmp/aep-lab/pilot/AE-neutral-2/refunds.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-neutral-2 -p 'test*.py'   # expect SUCCESS
..................................................
----------------------------------------------------------------------
Ran 50 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)

$ shasum -a 256 /tmp/aep-lab/pilot/AE-neutral-2/refunds.py
1fc3ed8dd5d4e166dfa8e7c36647e161ac75d5eb1340cb2c473044a10a357421  /tmp/aep-lab/pilot/AE-neutral-2/refunds.py
(exit 0)

$ echo 'refunds.py is byte-identical to the checksum taken before the control'
refunds.py is byte-identical to the checksum taken before the control
(exit 0)

```

### Guard `refundable_cap`

```text
$ shasum -a 256 /tmp/aep-lab/pilot/AE-neutral-2/refunds.py
1fc3ed8dd5d4e166dfa8e7c36647e161ac75d5eb1340cb2c473044a10a357421  /tmp/aep-lab/pilot/AE-neutral-2/refunds.py
(exit 0)

$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/AE-neutral-2/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/AE-neutral-2/_negcontrol.py refundable_cap" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-neutral-2 -p 'test*.py'" --expect "test_guard_cap_rejects_one_over_the_remaining_amount" --timeout 20
$ backed up /tmp/aep-lab/pilot/AE-neutral-2/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-jtamatmx/refunds.py
$ python3 /tmp/aep-lab/pilot/AE-neutral-2/_negcontrol.py refundable_cap
[negcontrol] guard 'refundable_cap' deleted in /private/tmp/aep-lab/pilot/AE-neutral-2/refunds.py (5 line(s) affected)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-neutral-2 -p 'test*.py'   # expect FAILURE matching /test_guard_cap_rejects_one_over_the_remaining_amount/
.F.......................................FFFF.....
======================================================================
FAIL: test_gateway_is_never_called_when_a_rule_rejects_the_refund (test_refund_contract.GatewayContractTests.test_gateway_is_never_called_when_a_rule_rejects_the_refund) (rule='cap')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-neutral-2/test_refund_contract.py", line 155, in test_gateway_is_never_called_when_a_rule_rejects_the_refund
    with self.assertRaises((ValueError, PermissionError)):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: (<class 'ValueError'>, <class 'PermissionError'>) not raised

======================================================================
FAIL: test_guard_cap_rejection_has_no_side_effects (test_refunds.RefundableCapGuardTests.test_guard_cap_rejection_has_no_side_effects)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-neutral-2/test_refunds.py", line 235, in test_guard_cap_rejection_has_no_side_effects
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_guard_cap_rejects_any_amount_on_a_fully_refunded_order (test_refunds.RefundableCapGuardTests.test_guard_cap_rejects_any_amount_on_a_fully_refunded_order)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-neutral-2/test_refunds.py", line 228, in test_guard_cap_rejects_any_amount_on_a_fully_refunded_order
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_guard_cap_rejects_full_paid_amount_when_partly_refunded (test_refunds.RefundableCapGuardTests.test_guard_cap_rejects_full_paid_amount_when_partly_refunded)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-neutral-2/test_refunds.py", line 222, in test_guard_cap_rejects_full_paid_amount_when_partly_refunded
    with self.assertRaises(ValueError, msg="the cap is paid minus refunded"):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised : the cap is paid minus refunded

======================================================================
FAIL: test_guard_cap_rejects_one_over_the_remaining_amount (test_refunds.RefundableCapGuardTests.test_guard_cap_rejects_one_over_the_remaining_amount)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-neutral-2/test_refunds.py", line 214, in test_guard_cap_rejects_one_over_the_remaining_amount
    with self.assertRaises(ValueError, msg="41 is more than the 40 still owed") as ctx:
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised : 41 is more than the 40 still owed

----------------------------------------------------------------------
Ran 50 tests in 0.002s

FAILED (failures=5)
(exit 1)
$ restored /tmp/aep-lab/pilot/AE-neutral-2/refunds.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-neutral-2 -p 'test*.py'   # expect SUCCESS
..................................................
----------------------------------------------------------------------
Ran 50 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)

$ shasum -a 256 /tmp/aep-lab/pilot/AE-neutral-2/refunds.py
1fc3ed8dd5d4e166dfa8e7c36647e161ac75d5eb1340cb2c473044a10a357421  /tmp/aep-lab/pilot/AE-neutral-2/refunds.py
(exit 0)

$ echo 'refunds.py is byte-identical to the checksum taken before the control'
refunds.py is byte-identical to the checksum taken before the control
(exit 0)

```

### Guard `gateway_atomicity`

```text
$ shasum -a 256 /tmp/aep-lab/pilot/AE-neutral-2/refunds.py
1fc3ed8dd5d4e166dfa8e7c36647e161ac75d5eb1340cb2c473044a10a357421  /tmp/aep-lab/pilot/AE-neutral-2/refunds.py
(exit 0)

$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/AE-neutral-2/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/AE-neutral-2/_negcontrol.py gateway_atomicity --swap" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-neutral-2 -p 'test*.py'" --expect "test_guard_atomicity_gateway_error_leaves_the_order_unchanged" --timeout 20
$ backed up /tmp/aep-lab/pilot/AE-neutral-2/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-iu0na8de/refunds.py
$ python3 /tmp/aep-lab/pilot/AE-neutral-2/_negcontrol.py gateway_atomicity --swap
[negcontrol] guard 'gateway_atomicity' reordered (commit before gateway call) in /private/tmp/aep-lab/pilot/AE-neutral-2/refunds.py (5 line(s) affected)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-neutral-2 -p 'test*.py'   # expect FAILURE matching /test_guard_atomicity_gateway_error_leaves_the_order_unchanged/
......................F.FF........................
======================================================================
FAIL: test_guard_atomicity_failed_refund_can_be_retried_with_the_same_key (test_refunds.GatewayAtomicityGuardTests.test_guard_atomicity_failed_refund_can_be_retried_with_the_same_key)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-neutral-2/test_refunds.py", line 282, in test_guard_atomicity_failed_refund_can_be_retried_with_the_same_key
    self.assertEqual(self.order["refunded"], 40)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 80 != 40

======================================================================
FAIL: test_guard_atomicity_gateway_error_leaves_the_order_unchanged (test_refunds.GatewayAtomicityGuardTests.test_guard_atomicity_gateway_error_leaves_the_order_unchanged)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-neutral-2/test_refunds.py", line 251, in test_guard_atomicity_gateway_error_leaves_the_order_unchanged
    self.assertEqual(order, before, "the order must be untouched after a gateway failure")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: {'id'[66 chars]00, 'refunded': 50, 'status': 'partially_refunded', 'keys': {}} != {'id'[66 chars]00, 'refunded': 30, 'status': 'partially_refunded', 'keys': {}}
  {'charge_id': 'ch_1',
   'id': 'ord_1',
   'keys': {},
   'owner_id': 'cus_owner',
   'paid': 100,
-  'refunded': 50,
?              ^

+  'refunded': 30,
?              ^

   'status': 'partially_refunded'} : the order must be untouched after a gateway failure

======================================================================
FAIL: test_guard_atomicity_gateway_error_on_a_paid_order_leaves_it_paid (test_refunds.GatewayAtomicityGuardTests.test_guard_atomicity_gateway_error_on_a_paid_order_leaves_it_paid)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-neutral-2/test_refunds.py", line 260, in test_guard_atomicity_gateway_error_on_a_paid_order_leaves_it_paid
    self.assertEqual(self.order, before)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
AssertionError: {'id'[57 chars]'paid': 100, 'refunded': 100, 'status': 'refunded', 'keys': {}} != {'id'[57 chars]'paid': 100, 'refunded': 0, 'status': 'paid', 'keys': {}}
  {'charge_id': 'ch_1',
   'id': 'ord_1',
   'keys': {},
   'owner_id': 'cus_owner',
   'paid': 100,
-  'refunded': 100,
?              --

+  'refunded': 0,
-  'status': 'refunded'}
?             ^^^^^^^

+  'status': 'paid'}
?             ^^^


----------------------------------------------------------------------
Ran 50 tests in 0.002s

FAILED (failures=3)
(exit 1)
$ restored /tmp/aep-lab/pilot/AE-neutral-2/refunds.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-neutral-2 -p 'test*.py'   # expect SUCCESS
..................................................
----------------------------------------------------------------------
Ran 50 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)

$ shasum -a 256 /tmp/aep-lab/pilot/AE-neutral-2/refunds.py
1fc3ed8dd5d4e166dfa8e7c36647e161ac75d5eb1340cb2c473044a10a357421  /tmp/aep-lab/pilot/AE-neutral-2/refunds.py
(exit 0)

$ echo 'refunds.py is byte-identical to the checksum taken before the control'
refunds.py is byte-identical to the checksum taken before the control
(exit 0)

```

## 4. Restore integrity and final suite

```text
$ shasum -a 256 /tmp/aep-lab/pilot/AE-neutral-2/refunds.py
1fc3ed8dd5d4e166dfa8e7c36647e161ac75d5eb1340cb2c473044a10a357421  /tmp/aep-lab/pilot/AE-neutral-2/refunds.py
(exit 0)

$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-neutral-2 -p 'test*.py'
..................................................
----------------------------------------------------------------------
Ran 50 tests in 0.001s

OK
(exit 0)

```

## 5. Result table

| guard | expected failure regex | break applied | aepkit exit | refunds.py restored exactly |
|---|---|---|---|---|
| idempotency | `test_guard_idempotency_replay_returns_stored_result` | delete block | 0 | yes |
| amount_validation | `test_guard_amount_rejects_zero` | delete block | 0 | yes |
| permission | `test_guard_permission_denies_another_customer` | delete block | 0 | yes |
| status | `test_guard_status_rejects_cancelled_order` | delete block | 0 | yes |
| refundable_cap | `test_guard_cap_rejects_one_over_the_remaining_amount` | delete block | 0 | yes |
| gateway_atomicity | `test_guard_atomicity_gateway_error_leaves_the_order_unchanged` | --swap | 0 | yes |

Checksum of `refunds.py` before all controls: `1fc3ed8dd5d4e166dfa8e7c36647e161ac75d5eb1340cb2c473044a10a357421`

```text
$ ls -l /tmp/aep-lab/pilot/AE-neutral-2/refunds.py /tmp/aep-lab/pilot/AE-neutral-2/fake_gateway.py /tmp/aep-lab/pilot/AE-neutral-2/fixtures.py /tmp/aep-lab/pilot/AE-neutral-2/test_*.py /tmp/aep-lab/pilot/AE-neutral-2/_negcontrol.py /tmp/aep-lab/pilot/AE-neutral-2/run_checks.sh /tmp/aep-lab/pilot/AE-neutral-2/README.md
-rw-r--r--@ 1 jhonatan  wheel   2993 Oct 25 01:18 /tmp/aep-lab/pilot/AE-neutral-2/_negcontrol.py
-rw-r--r--@ 1 jhonatan  wheel   1956 Oct 25 01:17 /tmp/aep-lab/pilot/AE-neutral-2/fake_gateway.py
-rw-r--r--@ 1 jhonatan  wheel    643 Oct 25 01:17 /tmp/aep-lab/pilot/AE-neutral-2/fixtures.py
-rw-r--r--@ 1 jhonatan  wheel   2115 Oct 25 01:22 /tmp/aep-lab/pilot/AE-neutral-2/README.md
-rw-r--r--@ 1 jhonatan  wheel   4114 Oct 25 01:17 /tmp/aep-lab/pilot/AE-neutral-2/refunds.py
-rw-r--r--@ 1 jhonatan  wheel   8342 Oct 25 01:21 /tmp/aep-lab/pilot/AE-neutral-2/run_checks.sh
-rw-r--r--@ 1 jhonatan  wheel   6617 Oct 25 01:18 /tmp/aep-lab/pilot/AE-neutral-2/test_refund_contract.py
-rw-r--r--@ 1 jhonatan  wheel  11932 Oct 25 01:17 /tmp/aep-lab/pilot/AE-neutral-2/test_refunds.py
(exit 0)

```

ALL CHECKS PASSED — 6/6 negative controls verified, suite green after restore.
