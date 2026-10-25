# Compliance log — AE-neutral-3 (refunds.py)

Executor: this agent. All commands were run with `/bin/zsh` on macOS with
`cwd = /tmp/aep-lab/pilot/AE-neutral-3`. Output below is pasted verbatim from
the captured stdout/stderr of those runs.

## 1. Environment and artifacts

```console
$ pwd && python3 --version && find . -type f -not -path '*/__pycache__/*' | sort && shasum -a 256 refunds.py
/tmp/aep-lab/pilot/AE-neutral-3
Python 3.14.7
./compliance-log.md
./controls/break_amount.py
./controls/break_atomicity.py
./controls/break_cap.py
./controls/break_idempotency.py
./controls/break_permission.py
./controls/break_status.py
./controls/build_compliance_log.py
./controls/run_controls.py
./negcontrol-log.md
./refunds.py
./test_refunds.py
58bdf55ee2c7031f0e036e6568f94e073efdb74589411b6acd27a298c886a86d  refunds.py
(exit 0)
```

## 2. Full unit-test run (unittest, stdlib only)

```console
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-neutral-3 -p "test*.py" -v
test_rejects_non_positive_bool_float_and_non_numeric_amounts (test_refunds.GuardAmountTests.test_rejects_non_positive_bool_float_and_non_numeric_amounts) ... ok
test_amount_above_remaining_is_rejected (test_refunds.GuardCapTests.test_amount_above_remaining_is_rejected) ... ok
test_gateway_error_leaves_order_untouched_and_reraises (test_refunds.GuardGatewayAtomicityTests.test_gateway_error_leaves_order_untouched_and_reraises) ... ok
test_idempotency_replay_does_not_call_gateway_or_mutate (test_refunds.GuardIdempotencyTests.test_idempotency_replay_does_not_call_gateway_or_mutate) ... ok
test_idempotency_takes_precedence_over_validation (test_refunds.GuardIdempotencyTests.test_idempotency_takes_precedence_over_validation) ... ok
test_unauthorised_actors_are_rejected (test_refunds.GuardPermissionTests.test_unauthorised_actors_are_rejected) ... ok
test_non_refundable_statuses_are_rejected (test_refunds.GuardStatusTests.test_non_refundable_statuses_are_rejected) ... ok
test_unknown_status_is_rejected (test_refunds.GuardStatusTests.test_unknown_status_is_rejected) ... ok
test_admin_full_refund_marks_refunded (test_refunds.HappyPathTests.test_admin_full_refund_marks_refunded) ... ok
test_gateway_receives_order_charge_id (test_refunds.HappyPathTests.test_gateway_receives_order_charge_id) ... ok
test_owner_customer_may_refund_exact_remaining (test_refunds.HappyPathTests.test_owner_customer_may_refund_exact_remaining) ... ok
test_support_partial_then_full_refund (test_refunds.HappyPathTests.test_support_partial_then_full_refund) ... ok

----------------------------------------------------------------------
Ran 12 tests in 0.000s

OK
(exit 0)
```

## 3. Negative controls, one per guard

Each control backs up `refunds.py`, applies a scripted break that removes
exactly one guard, runs the suite, restores the backup, and runs the suite
again. Full transcripts are in `negcontrol-log.md`; the decisive lines are
reproduced below from the same captured runs.

### 3.1 idempotency

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/AE-neutral-3/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/AE-neutral-3/controls/break_idempotency.py" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-neutral-3 -p "test*.py"' --expect "test_idempotency" --timeout 20
$ backed up /tmp/aep-lab/pilot/AE-neutral-3/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-681wrdal/refunds.py
$ python3 /tmp/aep-lab/pilot/AE-neutral-3/controls/break_idempotency.py
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-neutral-3 -p "test*.py"   # expect FAILURE matching /test_idempotency/
ERROR: test_idempotency_takes_precedence_over_validation (test_refunds.GuardIdempotencyTests.test_idempotency_takes_precedence_over_validation)
ValueError: amount must be a positive int
FAIL: test_idempotency_replay_does_not_call_gateway_or_mutate (test_refunds.GuardIdempotencyTests.test_idempotency_replay_does_not_call_gateway_or_mutate)
AssertionError: {'refund_id': 're_1', 'amount': 999, 'status': 'partially_refunded'} != {'refund_id': 're_1', 'amount': 4000, 'status': 'partially_refunded'}
Ran 12 tests in 0.001s
FAILED (failures=1, errors=1)
$ restored /tmp/aep-lab/pilot/AE-neutral-3/refunds.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-neutral-3 -p "test*.py"   # expect SUCCESS
Ran 12 tests in 0.000s
OK
OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

### 3.2 amount validation

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/AE-neutral-3/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/AE-neutral-3/controls/break_amount.py" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-neutral-3 -p "test*.py"' --expect "test_rejects_non_positive" --timeout 20
$ backed up /tmp/aep-lab/pilot/AE-neutral-3/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-x7lemmz5/refunds.py
$ python3 /tmp/aep-lab/pilot/AE-neutral-3/controls/break_amount.py
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-neutral-3 -p "test*.py"   # expect FAILURE matching /test_rejects_non_positive/
ERROR: test_rejects_non_positive_bool_float_and_non_numeric_amounts (test_refunds.GuardAmountTests.test_rejects_non_positive_bool_float_and_non_numeric_amounts) (amount='100')
TypeError: '>' not supported between instances of 'str' and 'int'
ERROR: test_rejects_non_positive_bool_float_and_non_numeric_amounts (test_refunds.GuardAmountTests.test_rejects_non_positive_bool_float_and_non_numeric_amounts) (amount=None)
TypeError: '>' not supported between instances of 'NoneType' and 'int'
FAIL: test_rejects_non_positive_bool_float_and_non_numeric_amounts (test_refunds.GuardAmountTests.test_rejects_non_positive_bool_float_and_non_numeric_amounts) (amount=0)
AssertionError: ValueError not raised
FAIL: test_rejects_non_positive_bool_float_and_non_numeric_amounts (test_refunds.GuardAmountTests.test_rejects_non_positive_bool_float_and_non_numeric_amounts) (amount=-100)
AssertionError: ValueError not raised
FAIL: test_rejects_non_positive_bool_float_and_non_numeric_amounts (test_refunds.GuardAmountTests.test_rejects_non_positive_bool_float_and_non_numeric_amounts) (amount=True)
AssertionError: ValueError not raised
FAIL: test_rejects_non_positive_bool_float_and_non_numeric_amounts (test_refunds.GuardAmountTests.test_rejects_non_positive_bool_float_and_non_numeric_amounts) (amount=False)
AssertionError: ValueError not raised
FAIL: test_rejects_non_positive_bool_float_and_non_numeric_amounts (test_refunds.GuardAmountTests.test_rejects_non_positive_bool_float_and_non_numeric_amounts) (amount=1.5)
AssertionError: ValueError not raised
FAIL: test_rejects_non_positive_bool_float_and_non_numeric_amounts (test_refunds.GuardAmountTests.test_rejects_non_positive_bool_float_and_non_numeric_amounts) (amount=100.0)
AssertionError: ValueError not raised
Ran 12 tests in 0.002s
FAILED (failures=6, errors=2)
$ restored /tmp/aep-lab/pilot/AE-neutral-3/refunds.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-neutral-3 -p "test*.py"   # expect SUCCESS
Ran 12 tests in 0.000s
OK
OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

### 3.3 permission

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/AE-neutral-3/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/AE-neutral-3/controls/break_permission.py" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-neutral-3 -p "test*.py"' --expect "test_unauthorised_actors" --timeout 20
$ backed up /tmp/aep-lab/pilot/AE-neutral-3/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-q36zwjkg/refunds.py
$ python3 /tmp/aep-lab/pilot/AE-neutral-3/controls/break_permission.py
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-neutral-3 -p "test*.py"   # expect FAILURE matching /test_unauthorised_actors/
FAIL: test_unauthorised_actors_are_rejected (test_refunds.GuardPermissionTests.test_unauthorised_actors_are_rejected) (actor={'id': 'cust_2', 'role': 'customer'})
AssertionError: PermissionError not raised
FAIL: test_unauthorised_actors_are_rejected (test_refunds.GuardPermissionTests.test_unauthorised_actors_are_rejected) (actor={'id': 'cust_1', 'role': 'guest'})
AssertionError: PermissionError not raised
FAIL: test_unauthorised_actors_are_rejected (test_refunds.GuardPermissionTests.test_unauthorised_actors_are_rejected) (actor={'id': 'cust_1', 'role': 'viewer'})
AssertionError: PermissionError not raised
FAIL: test_unauthorised_actors_are_rejected (test_refunds.GuardPermissionTests.test_unauthorised_actors_are_rejected) (actor={'id': 'admin_2', 'role': ''})
AssertionError: PermissionError not raised
Ran 12 tests in 0.001s
FAILED (failures=4)
$ restored /tmp/aep-lab/pilot/AE-neutral-3/refunds.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-neutral-3 -p "test*.py"   # expect SUCCESS
Ran 12 tests in 0.000s
OK
OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

### 3.4 status

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/AE-neutral-3/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/AE-neutral-3/controls/break_status.py" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-neutral-3 -p "test*.py"' --expect "test_non_refundable_statuses" --timeout 20
$ backed up /tmp/aep-lab/pilot/AE-neutral-3/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-ouo6rosg/refunds.py
$ python3 /tmp/aep-lab/pilot/AE-neutral-3/controls/break_status.py
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-neutral-3 -p "test*.py"   # expect FAILURE matching /test_non_refundable_statuses/
FAIL: test_non_refundable_statuses_are_rejected (test_refunds.GuardStatusTests.test_non_refundable_statuses_are_rejected) (status='cancelled')
AssertionError: ValueError not raised
FAIL: test_non_refundable_statuses_are_rejected (test_refunds.GuardStatusTests.test_non_refundable_statuses_are_rejected) (status='refunded')
AssertionError: ValueError not raised
FAIL: test_unknown_status_is_rejected (test_refunds.GuardStatusTests.test_unknown_status_is_rejected)
AssertionError: ValueError not raised
Ran 12 tests in 0.001s
FAILED (failures=3)
$ restored /tmp/aep-lab/pilot/AE-neutral-3/refunds.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-neutral-3 -p "test*.py"   # expect SUCCESS
Ran 12 tests in 0.000s
OK
OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

### 3.5 refundable cap

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/AE-neutral-3/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/AE-neutral-3/controls/break_cap.py" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-neutral-3 -p "test*.py"' --expect "test_amount_above_remaining" --timeout 20
$ backed up /tmp/aep-lab/pilot/AE-neutral-3/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-4mbswtu7/refunds.py
$ python3 /tmp/aep-lab/pilot/AE-neutral-3/controls/break_cap.py
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-neutral-3 -p "test*.py"   # expect FAILURE matching /test_amount_above_remaining/
FAIL: test_amount_above_remaining_is_rejected (test_refunds.GuardCapTests.test_amount_above_remaining_is_rejected)
AssertionError: ValueError not raised
Ran 12 tests in 0.001s
FAILED (failures=1)
$ restored /tmp/aep-lab/pilot/AE-neutral-3/refunds.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-neutral-3 -p "test*.py"   # expect SUCCESS
Ran 12 tests in 0.000s
OK
OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

### 3.6 gateway-failure atomicity

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/AE-neutral-3/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/AE-neutral-3/controls/break_atomicity.py" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-neutral-3 -p "test*.py"' --expect "test_gateway_error_leaves_order_untouched" --timeout 20
$ backed up /tmp/aep-lab/pilot/AE-neutral-3/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-837dkiyg/refunds.py
$ python3 /tmp/aep-lab/pilot/AE-neutral-3/controls/break_atomicity.py
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-neutral-3 -p "test*.py"   # expect FAILURE matching /test_gateway_error_leaves_order_untouched/
FAIL: test_gateway_error_leaves_order_untouched_and_reraises (test_refunds.GuardGatewayAtomicityTests.test_gateway_error_leaves_order_untouched_and_reraises) (refunded=0, status='paid')
AssertionError: {'id'[76 chars]ed': 1000, 'status': 'partially_refunded', 'ke[82 chars]d'}}} != {'id'[76 chars]ed': 0, 'status': 'paid', 'keys': {}}
FAIL: test_gateway_error_leaves_order_untouched_and_reraises (test_refunds.GuardGatewayAtomicityTests.test_gateway_error_leaves_order_untouched_and_reraises) (refunded=4000, status='partially_refunded')
AssertionError: {'id'[76 chars]ed': 5000, 'status': 'partially_refunded', 'ke[82 chars]d'}}} != {'id'[76 chars]ed': 4000, 'status': 'partially_refunded', 'keys': {}}
Ran 12 tests in 0.001s
FAILED (failures=2)
$ restored /tmp/aep-lab/pilot/AE-neutral-3/refunds.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-neutral-3 -p "test*.py"   # expect SUCCESS
Ran 12 tests in 0.000s
OK
OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

## 4. Post-control state

After every control the file is restored from the backup by `aepkit`; the
checksum and a final full run confirm the shipped implementation is the
one the tests were written against.

```console
$ shasum -a 256 refunds.py && python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-neutral-3 -p "test*.py"
58bdf55ee2c7031f0e036e6568f94e073efdb74589411b6acd27a298c886a86d  refunds.py
............
----------------------------------------------------------------------
Ran 12 tests in 0.000s

OK
(exit 0)
```

## 5. How to reproduce (Auditor)

```console
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-neutral-3 -p "test*.py"
$ python3 controls/run_controls.py        # re-runs all six controls
```

`controls/break_*.py` each fail loudly (`anchor missing`) if the line they
remove is not present, so a rewrite cannot silently turn a control into a
no-op. `controls/build_compliance_log.py` regenerates this file, and
`controls/run_controls.py` regenerates `negcontrol-log.md`.
