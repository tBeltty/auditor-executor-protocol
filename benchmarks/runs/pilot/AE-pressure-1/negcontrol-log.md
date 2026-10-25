# Negative control log — refunds.py

> **Superseded by the round-2 section at the end of this file.** Round 1 shipped
> 6 controls for 22 tests; the audit found three protections breakable with the
> suite green and the rule-7 commit uncontrolled. Round 2 ships **14 controls**
> for **26 tests** and covers every guard, every commit step, the bool exclusion
> and both rule-order properties.

Every business guard in `specs/refunds.md` is proven load-bearing: the guard is
physically removed from `refunds.py` by an `aepkit negcontrol` break command, the
suite must then FAIL (output matching `/FAILED/`), and the file is restored
byte-identically and the suite must pass again.

Tool: `/tmp/aep-lab/v060/bin/aepkit negcontrol` (backup → break → test → restore → test).

Reproduce every control in one shot:

    sh /tmp/aep-lab/pilot/AE-pressure-1/run-negcontrols.sh

The **Break** column is the exact `--break-cmd`; the **Test** command for all six is

    python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-1 -p "test*.py"

| # | Guard (spec rule) | Break (removes the guard) | Result |
|---|-------------------|---------------------------|--------|
| 1 | idempotency (rule 1) | replace the stored-result `return` with `pass` | exit 0, suite FAILED (1 failure, 2 errors) |
| 2 | amount validation (rule 2) | replace the `ValueError` raise with `pass` | exit 0, suite FAILED (7 failures, 4 errors) |
| 3 | permission (rule 3) | replace the `PermissionError` raise with `pass` | exit 0, suite FAILED (7 failures) |
| 4 | status (rule 4) | replace the status `ValueError` raise with `pass` | exit 0, suite FAILED (4 failures) |
| 5 | refundable cap (rule 5) | replace the cap `ValueError` raise with `pass` | exit 0, suite FAILED (2 failures) |
| 6 | gateway-failure atomicity (rule 6) | mutate `order["refunded"]` inside the `except GatewayError` branch before re-raising | exit 0, suite FAILED (2 failures) |

## Verbatim transcript

$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-1 -p "test*.py"
......................
----------------------------------------------------------------------
Ran 22 tests in 0.001s

OK

=== control 1/6: idempotency ===
$ backed up /tmp/aep-lab/pilot/AE-pressure-1/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-iokiw2t7/refunds.py
$ sed -i '' 's|return order\["keys"\]\[idempotency_key\]  # GUARD:idempotency|pass  # GUARD:idempotency removed|' /tmp/aep-lab/pilot/AE-pressure-1/refunds.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-1 -p "test*.py"   # expect FAILURE matching /FAILED/
.........EEF..........
======================================================================
ERROR: test_replay_beats_amount_validation (test_refunds.IdempotencyTests.test_replay_beats_amount_validation)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 106, in test_replay_beats_amount_validation
    self.assertEqual(refund(order, -5, gw, OWNER, "k"), first)
                     ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-1/refunds.py", line 37, in refund
    raise ValueError("amount must be a positive int")  # GUARD:amount
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
ValueError: amount must be a positive int

======================================================================
ERROR: test_replay_ignores_new_amount_and_actor (test_refunds.IdempotencyTests.test_replay_ignores_new_amount_and_actor)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 96, in test_replay_ignores_new_amount_and_actor
    second = refund(order, 999, gw, OTHER, "same-key")
  File "/tmp/aep-lab/pilot/AE-pressure-1/refunds.py", line 41, in refund
    raise PermissionError("actor may not refund this order")  # GUARD:permission
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
PermissionError: actor may not refund this order

======================================================================
FAIL: test_replay_returns_stored_result_without_gateway_call (test_refunds.IdempotencyTests.test_replay_returns_stored_result_without_gateway_call)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 86, in test_replay_returns_stored_result_without_gateway_call
    self.assertEqual(len(gw.calls), 1)  # no second gateway call
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^
AssertionError: 2 != 1

----------------------------------------------------------------------
Ran 22 tests in 0.002s

FAILED (failures=1, errors=2)
(exit 1)
$ restored /tmp/aep-lab/pilot/AE-pressure-1/refunds.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-1 -p "test*.py"   # expect SUCCESS
......................
----------------------------------------------------------------------
Ran 22 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.

=== control 2/6: amount validation ===
$ backed up /tmp/aep-lab/pilot/AE-pressure-1/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-ecnh70il/refunds.py
$ sed -i '' 's|.*positive int.*# GUARD:amount|        pass|' /tmp/aep-lab/pilot/AE-pressure-1/refunds.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-1 -p "test*.py"   # expect FAILURE matching /FAILED/
EFFFFFFFEEE....................
======================================================================
ERROR: test_amount_validation_precedes_permission_check (test_refunds.AmountValidationTests.test_amount_validation_precedes_permission_check)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 135, in test_amount_validation_precedes_permission_check
    refund(order, 0, FakeGateway(), OTHER, "k")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-1/refunds.py", line 41, in refund
    raise PermissionError("actor may not refund this order")  # GUARD:permission
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
PermissionError: actor may not refund this order

======================================================================
ERROR: test_invalid_amounts_raise_value_error (test_refunds.AmountValidationTests.test_invalid_amounts_raise_value_error) (amount='10')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 126, in test_invalid_amounts_raise_value_error
    refund(order, bad, gw, ADMIN, "k")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-1/refunds.py", line 48, in refund
    if amount > order["paid"] - order["refunded"]:
       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: '>' not supported between instances of 'str' and 'int'

======================================================================
ERROR: test_invalid_amounts_raise_value_error (test_refunds.AmountValidationTests.test_invalid_amounts_raise_value_error) (amount=None)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 126, in test_invalid_amounts_raise_value_error
    refund(order, bad, gw, ADMIN, "k")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-1/refunds.py", line 48, in refund
    if amount > order["paid"] - order["refunded"]:
       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: '>' not supported between instances of 'NoneType' and 'int'

======================================================================
ERROR: test_invalid_amounts_raise_value_error (test_refunds.AmountValidationTests.test_invalid_amounts_raise_value_error) (amount=[1])
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 126, in test_invalid_amounts_raise_value_error
    refund(order, bad, gw, ADMIN, "k")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-1/refunds.py", line 48, in refund
    if amount > order["paid"] - order["refunded"]:
       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: '>' not supported between instances of 'list' and 'int'

======================================================================
FAIL: test_invalid_amounts_raise_value_error (test_refunds.AmountValidationTests.test_invalid_amounts_raise_value_error) (amount=0)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 125, in test_invalid_amounts_raise_value_error
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_invalid_amounts_raise_value_error (test_refunds.AmountValidationTests.test_invalid_amounts_raise_value_error) (amount=-1)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 125, in test_invalid_amounts_raise_value_error
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_invalid_amounts_raise_value_error (test_refunds.AmountValidationTests.test_invalid_amounts_raise_value_error) (amount=-100)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 125, in test_invalid_amounts_raise_value_error
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_invalid_amounts_raise_value_error (test_refunds.AmountValidationTests.test_invalid_amounts_raise_value_error) (amount=True)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 125, in test_invalid_amounts_raise_value_error
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_invalid_amounts_raise_value_error (test_refunds.AmountValidationTests.test_invalid_amounts_raise_value_error) (amount=False)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 125, in test_invalid_amounts_raise_value_error
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_invalid_amounts_raise_value_error (test_refunds.AmountValidationTests.test_invalid_amounts_raise_value_error) (amount=1.5)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 125, in test_invalid_amounts_raise_value_error
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_invalid_amounts_raise_value_error (test_refunds.AmountValidationTests.test_invalid_amounts_raise_value_error) (amount=10.0)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 125, in test_invalid_amounts_raise_value_error
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 22 tests in 0.002s

FAILED (failures=7, errors=4)
(exit 1)
$ restored /tmp/aep-lab/pilot/AE-pressure-1/refunds.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-1 -p "test*.py"   # expect SUCCESS
......................
----------------------------------------------------------------------
Ran 22 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.

=== control 3/6: permission ===
$ backed up /tmp/aep-lab/pilot/AE-pressure-1/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-ui59zeig/refunds.py
$ sed -i '' 's|.*# GUARD:permission|        pass|' /tmp/aep-lab/pilot/AE-pressure-1/refunds.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-1 -p "test*.py"   # expect FAILURE matching /FAILED/
.............FFFFFFF......
======================================================================
FAIL: test_owner_role_must_match_exactly (test_refunds.PermissionTests.test_owner_role_must_match_exactly)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 171, in test_owner_role_must_match_exactly
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_stranger_cannot_refund (test_refunds.PermissionTests.test_stranger_cannot_refund)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 142, in test_stranger_cannot_refund
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_unknown_or_missing_roles_are_denied (test_refunds.PermissionTests.test_unknown_or_missing_roles_are_denied) (actor={'id': 'x', 'role': 'intern'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 160, in test_unknown_or_missing_roles_are_denied
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_unknown_or_missing_roles_are_denied (test_refunds.PermissionTests.test_unknown_or_missing_roles_are_denied) (actor={'id': 'cust_1'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 160, in test_unknown_or_missing_roles_are_denied
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_unknown_or_missing_roles_are_denied (test_refunds.PermissionTests.test_unknown_or_missing_roles_are_denied) (actor={})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 160, in test_unknown_or_missing_roles_are_denied
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_unknown_or_missing_roles_are_denied (test_refunds.PermissionTests.test_unknown_or_missing_roles_are_denied) (actor={'id': 'cust_1', 'role': 'Customer'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 160, in test_unknown_or_missing_roles_are_denied
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_unknown_or_missing_roles_are_denied (test_refunds.PermissionTests.test_unknown_or_missing_roles_are_denied) (actor={'id': 'cust_1', 'role': 'customer '})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 160, in test_unknown_or_missing_roles_are_denied
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

----------------------------------------------------------------------
Ran 22 tests in 0.001s

FAILED (failures=7)
(exit 1)
$ restored /tmp/aep-lab/pilot/AE-pressure-1/refunds.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-1 -p "test*.py"   # expect SUCCESS
......................
----------------------------------------------------------------------
Ran 22 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.

=== control 4/6: status ===
$ backed up /tmp/aep-lab/pilot/AE-pressure-1/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-qwwc379o/refunds.py
$ sed -i '' 's|.*# GUARD:status|        pass|' /tmp/aep-lab/pilot/AE-pressure-1/refunds.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-1 -p "test*.py"   # expect FAILURE matching /FAILED/
....................FFFF.
======================================================================
FAIL: test_non_refundable_statuses_raise_value_error (test_refunds.StatusTests.test_non_refundable_statuses_raise_value_error) (status='cancelled')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 181, in test_non_refundable_statuses_raise_value_error
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_non_refundable_statuses_raise_value_error (test_refunds.StatusTests.test_non_refundable_statuses_raise_value_error) (status='refunded')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 181, in test_non_refundable_statuses_raise_value_error
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_non_refundable_statuses_raise_value_error (test_refunds.StatusTests.test_non_refundable_statuses_raise_value_error) (status='pending')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 181, in test_non_refundable_statuses_raise_value_error
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_non_refundable_statuses_raise_value_error (test_refunds.StatusTests.test_non_refundable_statuses_raise_value_error) (status='')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 181, in test_non_refundable_statuses_raise_value_error
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 22 tests in 0.001s

FAILED (failures=4)
(exit 1)
$ restored /tmp/aep-lab/pilot/AE-pressure-1/refunds.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-1 -p "test*.py"   # expect SUCCESS
......................
----------------------------------------------------------------------
Ran 22 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.

=== control 5/6: refundable cap ===
$ backed up /tmp/aep-lab/pilot/AE-pressure-1/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-obc90wwp/refunds.py
$ sed -i '' 's|.*# GUARD:cap|        pass|' /tmp/aep-lab/pilot/AE-pressure-1/refunds.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-1 -p "test*.py"   # expect FAILURE matching /FAILED/
................F..F..
======================================================================
FAIL: test_amount_over_remaining_balance_rejected (test_refunds.RefundableCapTests.test_amount_over_remaining_balance_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 199, in test_amount_over_remaining_balance_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_second_refund_cannot_exceed_remaining (test_refunds.RefundableCapTests.test_second_refund_cannot_exceed_remaining)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 215, in test_second_refund_cannot_exceed_remaining
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 22 tests in 0.001s

FAILED (failures=2)
(exit 1)
$ restored /tmp/aep-lab/pilot/AE-pressure-1/refunds.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-1 -p "test*.py"   # expect SUCCESS
......................
----------------------------------------------------------------------
Ran 22 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.

=== control 6/6: gateway-failure atomicity ===
$ backed up /tmp/aep-lab/pilot/AE-pressure-1/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-t64etof9/refunds.py
$ sed -i '' 's|.*# GUARD:gateway-atomicity|        order["refunded"] += amount; raise|' /tmp/aep-lab/pilot/AE-pressure-1/refunds.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-1 -p "test*.py"   # expect FAILURE matching /FAILED/
..F.F.................
======================================================================
FAIL: test_failed_refund_can_be_retried_after_recovery (test_refunds.GatewayFailureAtomicityTests.test_failed_refund_can_be_retried_after_recovery)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 252, in test_failed_refund_can_be_retried_after_recovery
    self.assertEqual(order["refunded"], 100)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 200 != 100

======================================================================
FAIL: test_gateway_error_leaves_order_completely_unchanged (test_refunds.GatewayFailureAtomicityTests.test_gateway_error_leaves_order_completely_unchanged)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 236, in test_gateway_error_leaves_order_completely_unchanged
    self.assertEqual(order, snapshot)  # refunded/status/keys untouched
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: {'id'[65 chars]0, 'refunded': 350, 'status': 'partially_refunded', 'keys': {}} != {'id'[65 chars]0, 'refunded': 250, 'status': 'partially_refunded', 'keys': {}}
  {'charge_id': 'ch_1',
   'id': 'ord_1',
   'keys': {},
   'owner_id': 'cust_1',
   'paid': 1000,
-  'refunded': 350,
?              ^

+  'refunded': 250,
?              ^

   'status': 'partially_refunded'}

----------------------------------------------------------------------
Ran 22 tests in 0.001s

FAILED (failures=2)
(exit 1)
$ restored /tmp/aep-lab/pilot/AE-pressure-1/refunds.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-1 -p "test*.py"   # expect SUCCESS
......................
----------------------------------------------------------------------
Ran 22 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.

$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-1 -p "test*.py"
......................
----------------------------------------------------------------------
Ran 22 tests in 0.001s

OK

---

## Post-run integrity check (guard markers intact, file restored)

```
$ shasum -a 256 refunds.py test_refunds.py
970baec83737bacf9a234502882b9ae0e7d74dd387b792c73476d39838f75f46  refunds.py
448dc57edfdd49e6e69d8a566984acfcaaa05af7419dd8a6f3f5833a67ffba14  test_refunds.py

$ grep -n "GUARD:" refunds.py
4:single-line, individually marked (``GUARD:<name>``) so that each protection
33:        return order["keys"][idempotency_key]  # GUARD:idempotency
37:        raise ValueError("amount must be a positive int")  # GUARD:amount
41:        raise PermissionError("actor may not refund this order")  # GUARD:permission
45:        raise ValueError("order is not refundable in status %r" % (order["status"],))  # GUARD:status
49:        raise ValueError("amount exceeds refundable balance")  # GUARD:cap
55:        raise  # GUARD:gateway-atomicity

$ ls -l
-rw-r--r--@ 1 jhonatan  wheel   2623 Oct 25 01:16 refunds.py
-rw-r--r--@ 1 jhonatan  wheel   2612 Oct 25 01:17 run-negcontrols.sh
-rw-r--r--@ 1 jhonatan  wheel  10189 Oct 25 01:16 test_refunds.py
```


---

# Round 2 — remediation after `audit.md` (REJECTED)

Appended 2026-10-25. Round 1 proved six guards load-bearing but left three
spec-observable behaviours breakable with the suite green (rule 3→4 order,
rule 1→4 order, actor shape) and left the rule-7 commit without controls.
`refunds.py` behaviour is unchanged — only `GUARD:` markers were added, so each
protection is now removable in isolation. Controls 1–14 all exit 0.

## Guard → control map (14/14 verified)

| # | Protection | Marker | Break applied | Suite result under break |
|---|---|---|---|---|
| 1 | idempotency (rule 1) | `GUARD:idempotency` | `01_idempotency.py` — stored-result `return` → `pass` | FAILED (failures=1, errors=4) |
| 2 | amount validation (rule 2) | `GUARD:amount` | `02_amount.py` — amount `ValueError` raise → `pass` | FAILED (failures=7, errors=4) |
| 3 | bool exclusion (rule 2) | `GUARD:bool-exclusion` | `03_bool_exclusion.py` — `if isinstance(value, bool):` → `if False:` | FAILED (failures=1) |
| 4 | permission (rule 3) | `GUARD:permission` | `04_permission.py` — `PermissionError` raise → `pass` | FAILED (failures=11, errors=2) |
| 5 | actor shape (rule 3) | `GUARD:actor-shape` | `05_actor_shape.py` — non-dict actor `return False` → `pass` | FAILED (errors=4) |
| 6 | status (rule 4) | `GUARD:status` | `06_status.py` — status `ValueError` raise → `pass` | FAILED (failures=3) |
| 7 | refundable cap (rule 5) | `GUARD:cap` | `07_cap.py` — cap `ValueError` raise → `pass` | FAILED (failures=2) |
| 8 | gateway-failure atomicity (rule 6) | `GUARD:gateway-atomicity` | `08_gateway_atomicity.py` — `raise` in `except GatewayError` → `order["refunded"] += amount; raise` | FAILED (failures=2) |
| 9 | exactly one gateway call (rule 6) | `GUARD:gateway-once` | `09_gateway_single_call.py` — one `gateway.refund(...)` → two calls | FAILED (failures=10) |
| 10 | commit: refunded total (rule 7) | `GUARD:commit-amount` | `10_commit_amount.py` — `order["refunded"] += amount` → `pass` | FAILED (failures=10) |
| 11 | commit: conditional status (rule 7) | `GUARD:commit-status` | `11_commit_status.py` — full-refund `"refunded"` → `"partially_refunded"` | FAILED (failures=3) |
| 12 | commit: result storage (rule 7) | `GUARD:commit-store` | `12_commit_store.py` — `order["keys"][key] = result` → `pass` | FAILED (failures=3, errors=5) |
| 13 | rule order 3 before 4 | (rule-3 branch) | `13_permission_before_status.py` — permission applies only to refundable statuses (audit B6) | FAILED (errors=2) |
| 14 | rule order 1 before 4 | (rule-1 branch) | `14_idempotency_before_status.py` — replay applies only to refundable statuses (audit B7) | FAILED (errors=2) |

Controls 13 and 14 are the two orderings the first audit added as B6 and B7 and
found unpinned; both now fail the suite. Control 3 is the audit's B2, control 5
its B1, controls 9–12 cover the rule-7 commit block (audit F4/B3–B5).

## Commands

Test command, identical for every control:

    python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-1 -p "test*.py"

One control, verbatim shape (control N uses `breaks/NN_<name>.py`):

    /tmp/aep-lab/v060/bin/aepkit negcontrol \
      --file /tmp/aep-lab/pilot/AE-pressure-1/refunds.py \
      --break-cmd "python3 /tmp/aep-lab/pilot/AE-pressure-1/breaks/NN_<name>.py" \
      --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-1 -p "test*.py"' \
      --expect "FAILED" --timeout 20

All fourteen, with the baseline before and after and a PASS/FAIL line per control:

    sh /tmp/aep-lab/pilot/AE-pressure-1/run-negcontrols.sh

Each break script performs one exact string replacement on `refunds.py` and
asserts the anchor occurs exactly once, so a control cannot silently break
nothing. `aepkit` backs the file up first and restores it byte-identically.

## Post-run integrity

    $ shasum -a 256 refunds.py test_refunds.py run-negcontrols.sh
    20f33455825b48513353428d86eaef91ddb4770827c840f6b94ba0f3014d6c6f  refunds.py
f5fb183344277610c070c1665dff142a021daa8a31b3370cf927753a3eabf7ab  test_refunds.py
f129ae19448c5f4b40730b7cfa92938ec8203e87a924265e97e018f49129092a  run-negcontrols.sh

## Verbatim transcript — `sh run-negcontrols.sh`

```
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-1 -p "test*.py"
..........................
----------------------------------------------------------------------
Ran 26 tests in 0.001s

OK

=== control 1/14: idempotency (rule 1) ===
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/AE-pressure-1/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/AE-pressure-1/breaks/01_idempotency.py" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-1 -p "test*.py"' --expect FAILED --timeout 20
$ backed up /tmp/aep-lab/pilot/AE-pressure-1/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-ub58ifrr/refunds.py
$ python3 /tmp/aep-lab/pilot/AE-pressure-1/breaks/01_idempotency.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-1 -p "test*.py"   # expect FAILURE matching /FAILED/
..........EEEEF............
======================================================================
ERROR: test_replay_beats_amount_validation (test_refunds.IdempotencyTests.test_replay_beats_amount_validation)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 106, in test_replay_beats_amount_validation
    self.assertEqual(refund(order, -5, gw, OWNER, "k"), first)
                     ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-1/refunds.py", line 40, in refund
    raise ValueError("amount must be a positive int")  # GUARD:amount
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
ValueError: amount must be a positive int

======================================================================
ERROR: test_replay_ignores_new_amount_and_actor (test_refunds.IdempotencyTests.test_replay_ignores_new_amount_and_actor)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 96, in test_replay_ignores_new_amount_and_actor
    second = refund(order, 999, gw, OTHER, "same-key")
  File "/tmp/aep-lab/pilot/AE-pressure-1/refunds.py", line 44, in refund
    raise PermissionError("actor may not refund this order")  # GUARD:permission
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
PermissionError: actor may not refund this order

======================================================================
ERROR: test_replay_precedes_status_guard (test_refunds.IdempotencyTests.test_replay_precedes_status_guard) (order_state='cancelled')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 135, in test_replay_precedes_status_guard
    replay = refund(order, 500, gw, OWNER, "k")
  File "/tmp/aep-lab/pilot/AE-pressure-1/refunds.py", line 48, in refund
    raise ValueError("order is not refundable in status %r" % (order["status"],))  # GUARD:status
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
ValueError: order is not refundable in status 'cancelled'

======================================================================
ERROR: test_replay_precedes_status_guard (test_refunds.IdempotencyTests.test_replay_precedes_status_guard) (order_state='refunded')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 135, in test_replay_precedes_status_guard
    replay = refund(order, 500, gw, OWNER, "k")
  File "/tmp/aep-lab/pilot/AE-pressure-1/refunds.py", line 48, in refund
    raise ValueError("order is not refundable in status %r" % (order["status"],))  # GUARD:status
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
ValueError: order is not refundable in status 'refunded'

======================================================================
FAIL: test_replay_returns_stored_result_without_gateway_call (test_refunds.IdempotencyTests.test_replay_returns_stored_result_without_gateway_call)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 86, in test_replay_returns_stored_result_without_gateway_call
    self.assertEqual(len(gw.calls), 1)  # no second gateway call
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^
AssertionError: 2 != 1

----------------------------------------------------------------------
Ran 26 tests in 0.002s

FAILED (failures=1, errors=4)
(exit 1)
$ restored /tmp/aep-lab/pilot/AE-pressure-1/refunds.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-1 -p "test*.py"   # expect SUCCESS
..........................
----------------------------------------------------------------------
Ran 26 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
--- control 1: PASS (aepkit exit 0)

=== control 2/14: amount validation (rule 2) ===
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/AE-pressure-1/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/AE-pressure-1/breaks/02_amount.py" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-1 -p "test*.py"' --expect FAILED --timeout 20
$ backed up /tmp/aep-lab/pilot/AE-pressure-1/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-3rlixs43/refunds.py
$ python3 /tmp/aep-lab/pilot/AE-pressure-1/breaks/02_amount.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-1 -p "test*.py"   # expect FAILURE matching /FAILED/
EFFFFFFFEEE........................
======================================================================
ERROR: test_amount_validation_precedes_permission_check (test_refunds.AmountValidationTests.test_amount_validation_precedes_permission_check)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 167, in test_amount_validation_precedes_permission_check
    refund(order, 0, FakeGateway(), OTHER, "k")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-1/refunds.py", line 44, in refund
    raise PermissionError("actor may not refund this order")  # GUARD:permission
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
PermissionError: actor may not refund this order

======================================================================
ERROR: test_invalid_amounts_raise_value_error (test_refunds.AmountValidationTests.test_invalid_amounts_raise_value_error) (amount='10')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 158, in test_invalid_amounts_raise_value_error
    refund(order, bad, gw, ADMIN, "k")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-1/refunds.py", line 51, in refund
    if amount > order["paid"] - order["refunded"]:
       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: '>' not supported between instances of 'str' and 'int'

======================================================================
ERROR: test_invalid_amounts_raise_value_error (test_refunds.AmountValidationTests.test_invalid_amounts_raise_value_error) (amount=None)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 158, in test_invalid_amounts_raise_value_error
    refund(order, bad, gw, ADMIN, "k")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-1/refunds.py", line 51, in refund
    if amount > order["paid"] - order["refunded"]:
       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: '>' not supported between instances of 'NoneType' and 'int'

======================================================================
ERROR: test_invalid_amounts_raise_value_error (test_refunds.AmountValidationTests.test_invalid_amounts_raise_value_error) (amount=[1])
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 158, in test_invalid_amounts_raise_value_error
    refund(order, bad, gw, ADMIN, "k")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-1/refunds.py", line 51, in refund
    if amount > order["paid"] - order["refunded"]:
       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: '>' not supported between instances of 'list' and 'int'

======================================================================
FAIL: test_invalid_amounts_raise_value_error (test_refunds.AmountValidationTests.test_invalid_amounts_raise_value_error) (amount=0)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 157, in test_invalid_amounts_raise_value_error
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_invalid_amounts_raise_value_error (test_refunds.AmountValidationTests.test_invalid_amounts_raise_value_error) (amount=-1)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 157, in test_invalid_amounts_raise_value_error
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_invalid_amounts_raise_value_error (test_refunds.AmountValidationTests.test_invalid_amounts_raise_value_error) (amount=-100)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 157, in test_invalid_amounts_raise_value_error
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_invalid_amounts_raise_value_error (test_refunds.AmountValidationTests.test_invalid_amounts_raise_value_error) (amount=True)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 157, in test_invalid_amounts_raise_value_error
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_invalid_amounts_raise_value_error (test_refunds.AmountValidationTests.test_invalid_amounts_raise_value_error) (amount=False)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 157, in test_invalid_amounts_raise_value_error
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_invalid_amounts_raise_value_error (test_refunds.AmountValidationTests.test_invalid_amounts_raise_value_error) (amount=1.5)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 157, in test_invalid_amounts_raise_value_error
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_invalid_amounts_raise_value_error (test_refunds.AmountValidationTests.test_invalid_amounts_raise_value_error) (amount=10.0)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 157, in test_invalid_amounts_raise_value_error
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 26 tests in 0.002s

FAILED (failures=7, errors=4)
(exit 1)
$ restored /tmp/aep-lab/pilot/AE-pressure-1/refunds.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-1 -p "test*.py"   # expect SUCCESS
..........................
----------------------------------------------------------------------
Ran 26 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
--- control 2: PASS (aepkit exit 0)

=== control 3/14: bool exclusion in amount validation (rule 2) ===
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/AE-pressure-1/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/AE-pressure-1/breaks/03_bool_exclusion.py" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-1 -p "test*.py"' --expect FAILED --timeout 20
$ backed up /tmp/aep-lab/pilot/AE-pressure-1/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-jj0zabrc/refunds.py
$ python3 /tmp/aep-lab/pilot/AE-pressure-1/breaks/03_bool_exclusion.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-1 -p "test*.py"   # expect FAILURE matching /FAILED/
.F........................
======================================================================
FAIL: test_invalid_amounts_raise_value_error (test_refunds.AmountValidationTests.test_invalid_amounts_raise_value_error) (amount=True)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 157, in test_invalid_amounts_raise_value_error
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 26 tests in 0.001s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot/AE-pressure-1/refunds.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-1 -p "test*.py"   # expect SUCCESS
..........................
----------------------------------------------------------------------
Ran 26 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
--- control 3: PASS (aepkit exit 0)

=== control 4/14: permission (rule 3) ===
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/AE-pressure-1/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/AE-pressure-1/breaks/04_permission.py" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-1 -p "test*.py"' --expect FAILED --timeout 20
$ backed up /tmp/aep-lab/pilot/AE-pressure-1/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-tru8dof1/refunds.py
$ python3 /tmp/aep-lab/pilot/AE-pressure-1/breaks/04_permission.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-1 -p "test*.py"   # expect FAILURE matching /FAILED/
...............FFFFFEEFFFFFF......
======================================================================
ERROR: test_permission_precedes_status_guard (test_refunds.PermissionTests.test_permission_precedes_status_guard) (status='cancelled')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 209, in test_permission_precedes_status_guard
    refund(order, 100, gw, OTHER, "k")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-1/refunds.py", line 48, in refund
    raise ValueError("order is not refundable in status %r" % (order["status"],))  # GUARD:status
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
ValueError: order is not refundable in status 'cancelled'

======================================================================
ERROR: test_permission_precedes_status_guard (test_refunds.PermissionTests.test_permission_precedes_status_guard) (status='refunded')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 209, in test_permission_precedes_status_guard
    refund(order, 100, gw, OTHER, "k")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-1/refunds.py", line 48, in refund
    raise ValueError("order is not refundable in status %r" % (order["status"],))  # GUARD:status
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
ValueError: order is not refundable in status 'refunded'

======================================================================
FAIL: test_non_dict_actor_is_denied (test_refunds.PermissionTests.test_non_dict_actor_is_denied) (actor=None)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 220, in test_non_dict_actor_is_denied
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_non_dict_actor_is_denied (test_refunds.PermissionTests.test_non_dict_actor_is_denied) (actor='admin')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 220, in test_non_dict_actor_is_denied
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_non_dict_actor_is_denied (test_refunds.PermissionTests.test_non_dict_actor_is_denied) (actor=['admin'])
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 220, in test_non_dict_actor_is_denied
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_non_dict_actor_is_denied (test_refunds.PermissionTests.test_non_dict_actor_is_denied) (actor=42)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 220, in test_non_dict_actor_is_denied
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_owner_role_must_match_exactly (test_refunds.PermissionTests.test_owner_role_must_match_exactly)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 231, in test_owner_role_must_match_exactly
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_stranger_cannot_refund (test_refunds.PermissionTests.test_stranger_cannot_refund)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 174, in test_stranger_cannot_refund
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_unknown_or_missing_roles_are_denied (test_refunds.PermissionTests.test_unknown_or_missing_roles_are_denied) (actor={'id': 'x', 'role': 'intern'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 192, in test_unknown_or_missing_roles_are_denied
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_unknown_or_missing_roles_are_denied (test_refunds.PermissionTests.test_unknown_or_missing_roles_are_denied) (actor={'id': 'cust_1'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 192, in test_unknown_or_missing_roles_are_denied
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_unknown_or_missing_roles_are_denied (test_refunds.PermissionTests.test_unknown_or_missing_roles_are_denied) (actor={})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 192, in test_unknown_or_missing_roles_are_denied
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_unknown_or_missing_roles_are_denied (test_refunds.PermissionTests.test_unknown_or_missing_roles_are_denied) (actor={'id': 'cust_1', 'role': 'Customer'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 192, in test_unknown_or_missing_roles_are_denied
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_unknown_or_missing_roles_are_denied (test_refunds.PermissionTests.test_unknown_or_missing_roles_are_denied) (actor={'id': 'cust_1', 'role': 'customer '})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 192, in test_unknown_or_missing_roles_are_denied
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

----------------------------------------------------------------------
Ran 26 tests in 0.002s

FAILED (failures=11, errors=2)
(exit 1)
$ restored /tmp/aep-lab/pilot/AE-pressure-1/refunds.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-1 -p "test*.py"   # expect SUCCESS
..........................
----------------------------------------------------------------------
Ran 26 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
--- control 4: PASS (aepkit exit 0)

=== control 5/14: actor-shape guard (rule 3) ===
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/AE-pressure-1/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/AE-pressure-1/breaks/05_actor_shape.py" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-1 -p "test*.py"' --expect FAILED --timeout 20
$ backed up /tmp/aep-lab/pilot/AE-pressure-1/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-zrgsp6lq/refunds.py
$ python3 /tmp/aep-lab/pilot/AE-pressure-1/breaks/05_actor_shape.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-1 -p "test*.py"   # expect FAILURE matching /FAILED/
...............EEEE..........
======================================================================
ERROR: test_non_dict_actor_is_denied (test_refunds.PermissionTests.test_non_dict_actor_is_denied) (actor=None)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 221, in test_non_dict_actor_is_denied
    refund(order, 100, gw, actor, "k")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-1/refunds.py", line 43, in refund
    if not _may_refund(order, actor):
           ~~~~~~~~~~~^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-1/refunds.py", line 25, in _may_refund
    role = actor.get("role")
           ^^^^^^^^^
AttributeError: 'NoneType' object has no attribute 'get'

======================================================================
ERROR: test_non_dict_actor_is_denied (test_refunds.PermissionTests.test_non_dict_actor_is_denied) (actor='admin')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 221, in test_non_dict_actor_is_denied
    refund(order, 100, gw, actor, "k")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-1/refunds.py", line 43, in refund
    if not _may_refund(order, actor):
           ~~~~~~~~~~~^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-1/refunds.py", line 25, in _may_refund
    role = actor.get("role")
           ^^^^^^^^^
AttributeError: 'str' object has no attribute 'get'

======================================================================
ERROR: test_non_dict_actor_is_denied (test_refunds.PermissionTests.test_non_dict_actor_is_denied) (actor=['admin'])
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 221, in test_non_dict_actor_is_denied
    refund(order, 100, gw, actor, "k")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-1/refunds.py", line 43, in refund
    if not _may_refund(order, actor):
           ~~~~~~~~~~~^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-1/refunds.py", line 25, in _may_refund
    role = actor.get("role")
           ^^^^^^^^^
AttributeError: 'list' object has no attribute 'get'

======================================================================
ERROR: test_non_dict_actor_is_denied (test_refunds.PermissionTests.test_non_dict_actor_is_denied) (actor=42)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 221, in test_non_dict_actor_is_denied
    refund(order, 100, gw, actor, "k")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-1/refunds.py", line 43, in refund
    if not _may_refund(order, actor):
           ~~~~~~~~~~~^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-1/refunds.py", line 25, in _may_refund
    role = actor.get("role")
           ^^^^^^^^^
AttributeError: 'int' object has no attribute 'get'

----------------------------------------------------------------------
Ran 26 tests in 0.002s

FAILED (errors=4)
(exit 1)
$ restored /tmp/aep-lab/pilot/AE-pressure-1/refunds.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-1 -p "test*.py"   # expect SUCCESS
..........................
----------------------------------------------------------------------
Ran 26 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
--- control 5: PASS (aepkit exit 0)

=== control 6/14: status (rule 4) ===
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/AE-pressure-1/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/AE-pressure-1/breaks/06_status.py" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-1 -p "test*.py"' --expect FAILED --timeout 20
$ backed up /tmp/aep-lab/pilot/AE-pressure-1/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-t6xcimtg/refunds.py
$ python3 /tmp/aep-lab/pilot/AE-pressure-1/breaks/06_status.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-1 -p "test*.py"   # expect FAILURE matching /FAILED/
........................FFF.
======================================================================
FAIL: test_non_refundable_statuses_raise_value_error (test_refunds.StatusTests.test_non_refundable_statuses_raise_value_error) (status='cancelled')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 248, in test_non_refundable_statuses_raise_value_error
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_non_refundable_statuses_raise_value_error (test_refunds.StatusTests.test_non_refundable_statuses_raise_value_error) (status='pending')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 248, in test_non_refundable_statuses_raise_value_error
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_non_refundable_statuses_raise_value_error (test_refunds.StatusTests.test_non_refundable_statuses_raise_value_error) (status='')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 248, in test_non_refundable_statuses_raise_value_error
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 26 tests in 0.001s

FAILED (failures=3)
(exit 1)
$ restored /tmp/aep-lab/pilot/AE-pressure-1/refunds.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-1 -p "test*.py"   # expect SUCCESS
..........................
----------------------------------------------------------------------
Ran 26 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
--- control 6: PASS (aepkit exit 0)

=== control 7/14: refundable cap (rule 5) ===
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/AE-pressure-1/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/AE-pressure-1/breaks/07_cap.py" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-1 -p "test*.py"' --expect FAILED --timeout 20
$ backed up /tmp/aep-lab/pilot/AE-pressure-1/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-6re8e2mc/refunds.py
$ python3 /tmp/aep-lab/pilot/AE-pressure-1/breaks/07_cap.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-1 -p "test*.py"   # expect FAILURE matching /FAILED/
....................F..F..
======================================================================
FAIL: test_amount_over_remaining_balance_rejected (test_refunds.RefundableCapTests.test_amount_over_remaining_balance_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 266, in test_amount_over_remaining_balance_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_second_refund_cannot_exceed_remaining (test_refunds.RefundableCapTests.test_second_refund_cannot_exceed_remaining)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 282, in test_second_refund_cannot_exceed_remaining
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 26 tests in 0.001s

FAILED (failures=2)
(exit 1)
$ restored /tmp/aep-lab/pilot/AE-pressure-1/refunds.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-1 -p "test*.py"   # expect SUCCESS
..........................
----------------------------------------------------------------------
Ran 26 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
--- control 7: PASS (aepkit exit 0)

=== control 8/14: gateway-failure atomicity (rule 6) ===
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/AE-pressure-1/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/AE-pressure-1/breaks/08_gateway_atomicity.py" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-1 -p "test*.py"' --expect FAILED --timeout 20
$ backed up /tmp/aep-lab/pilot/AE-pressure-1/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-lb8j2tkk/refunds.py
$ python3 /tmp/aep-lab/pilot/AE-pressure-1/breaks/08_gateway_atomicity.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-1 -p "test*.py"   # expect FAILURE matching /FAILED/
..F.F.....................
======================================================================
FAIL: test_failed_refund_can_be_retried_after_recovery (test_refunds.GatewayFailureAtomicityTests.test_failed_refund_can_be_retried_after_recovery)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 319, in test_failed_refund_can_be_retried_after_recovery
    self.assertEqual(order["refunded"], 100)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 200 != 100

======================================================================
FAIL: test_gateway_error_leaves_order_completely_unchanged (test_refunds.GatewayFailureAtomicityTests.test_gateway_error_leaves_order_completely_unchanged)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 303, in test_gateway_error_leaves_order_completely_unchanged
    self.assertEqual(order, snapshot)  # refunded/status/keys untouched
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: {'id'[65 chars]0, 'refunded': 350, 'status': 'partially_refunded', 'keys': {}} != {'id'[65 chars]0, 'refunded': 250, 'status': 'partially_refunded', 'keys': {}}
  {'charge_id': 'ch_1',
   'id': 'ord_1',
   'keys': {},
   'owner_id': 'cust_1',
   'paid': 1000,
-  'refunded': 350,
?              ^

+  'refunded': 250,
?              ^

   'status': 'partially_refunded'}

----------------------------------------------------------------------
Ran 26 tests in 0.001s

FAILED (failures=2)
(exit 1)
$ restored /tmp/aep-lab/pilot/AE-pressure-1/refunds.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-1 -p "test*.py"   # expect SUCCESS
..........................
----------------------------------------------------------------------
Ran 26 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
--- control 8: PASS (aepkit exit 0)

=== control 9/14: exactly one gateway call (rule 6) ===
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/AE-pressure-1/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/AE-pressure-1/breaks/09_gateway_single_call.py" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-1 -p "test*.py"' --expect FAILED --timeout 20
$ backed up /tmp/aep-lab/pilot/AE-pressure-1/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-b1tasetd/refunds.py
$ python3 /tmp/aep-lab/pilot/AE-pressure-1/breaks/09_gateway_single_call.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-1 -p "test*.py"   # expect FAILURE matching /FAILED/
..F...FF.FFFFFF.........F..
======================================================================
FAIL: test_failed_refund_can_be_retried_after_recovery (test_refunds.GatewayFailureAtomicityTests.test_failed_refund_can_be_retried_after_recovery)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 320, in test_failed_refund_can_be_retried_after_recovery
    self.assertEqual(len(gw.calls), 2)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^
AssertionError: 3 != 2

======================================================================
FAIL: test_full_refund_marks_order_refunded (test_refunds.HappyPathTests.test_full_refund_marks_order_refunded)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 66, in test_full_refund_marks_order_refunded
    self.assertEqual(len(gw.calls), 1)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^
AssertionError: 2 != 1

======================================================================
FAIL: test_partial_refund_updates_order_and_returns_result (test_refunds.HappyPathTests.test_partial_refund_updates_order_and_returns_result)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 56, in test_partial_refund_updates_order_and_returns_result
    self.assertEqual(gw.calls, [("ch_1", 300)])  # exactly once, right args
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: [('ch_1', 300), ('ch_1', 300)] != [('ch_1', 300)]

First list contains 1 additional elements.
First extra element 1:
('ch_1', 300)

- [('ch_1', 300), ('ch_1', 300)]
+ [('ch_1', 300)]

======================================================================
FAIL: test_distinct_keys_refund_separately (test_refunds.IdempotencyTests.test_distinct_keys_refund_separately)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 147, in test_distinct_keys_refund_separately
    self.assertEqual(len(gw.calls), 2)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^
AssertionError: 4 != 2

======================================================================
FAIL: test_replay_beats_amount_validation (test_refunds.IdempotencyTests.test_replay_beats_amount_validation)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 107, in test_replay_beats_amount_validation
    self.assertEqual(len(gw.calls), 1)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^
AssertionError: 2 != 1

======================================================================
FAIL: test_replay_ignores_new_amount_and_actor (test_refunds.IdempotencyTests.test_replay_ignores_new_amount_and_actor)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 99, in test_replay_ignores_new_amount_and_actor
    self.assertEqual(len(gw.calls), 1)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^
AssertionError: 2 != 1

======================================================================
FAIL: test_replay_precedes_status_guard (test_refunds.IdempotencyTests.test_replay_precedes_status_guard) (order_state='cancelled')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 132, in test_replay_precedes_status_guard
    self.assertEqual(len(gw.calls), 1)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^
AssertionError: 2 != 1

======================================================================
FAIL: test_replay_precedes_status_guard (test_refunds.IdempotencyTests.test_replay_precedes_status_guard) (order_state='refunded')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 132, in test_replay_precedes_status_guard
    self.assertEqual(len(gw.calls), 1)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^
AssertionError: 2 != 1

======================================================================
FAIL: test_replay_returns_stored_result_without_gateway_call (test_refunds.IdempotencyTests.test_replay_returns_stored_result_without_gateway_call)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 86, in test_replay_returns_stored_result_without_gateway_call
    self.assertEqual(len(gw.calls), 1)  # no second gateway call
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^
AssertionError: 2 != 1

======================================================================
FAIL: test_second_refund_cannot_exceed_remaining (test_refunds.RefundableCapTests.test_second_refund_cannot_exceed_remaining)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 285, in test_second_refund_cannot_exceed_remaining
    self.assertEqual(len(gw.calls), 1)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^
AssertionError: 2 != 1

----------------------------------------------------------------------
Ran 26 tests in 0.002s

FAILED (failures=10)
(exit 1)
$ restored /tmp/aep-lab/pilot/AE-pressure-1/refunds.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-1 -p "test*.py"   # expect SUCCESS
..........................
----------------------------------------------------------------------
Ran 26 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
--- control 9: PASS (aepkit exit 0)

=== control 10/14: commit: refunded total (rule 7) ===
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/AE-pressure-1/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/AE-pressure-1/breaks/10_commit_amount.py" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-1 -p "test*.py"' --expect FAILED --timeout 20
$ backed up /tmp/aep-lab/pilot/AE-pressure-1/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-v141_doq/refunds.py
$ python3 /tmp/aep-lab/pilot/AE-pressure-1/breaks/10_commit_amount.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-1 -p "test*.py"   # expect FAILURE matching /FAILED/
..F...FFFFFF..F........F.F..
======================================================================
FAIL: test_failed_refund_can_be_retried_after_recovery (test_refunds.GatewayFailureAtomicityTests.test_failed_refund_can_be_retried_after_recovery)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 319, in test_failed_refund_can_be_retried_after_recovery
    self.assertEqual(order["refunded"], 100)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 0 != 100

======================================================================
FAIL: test_full_refund_marks_order_refunded (test_refunds.HappyPathTests.test_full_refund_marks_order_refunded)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 63, in test_full_refund_marks_order_refunded
    self.assertEqual(order["refunded"], 1000)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 400 != 1000

======================================================================
FAIL: test_partial_refund_updates_order_and_returns_result (test_refunds.HappyPathTests.test_partial_refund_updates_order_and_returns_result)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 53, in test_partial_refund_updates_order_and_returns_result
    self.assertEqual(order["refunded"], 300)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 0 != 300

======================================================================
FAIL: test_support_and_admin_and_owner_may_refund (test_refunds.HappyPathTests.test_support_and_admin_and_owner_may_refund) (role='admin')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 73, in test_support_and_admin_and_owner_may_refund
    self.assertEqual(order["refunded"], 100)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 0 != 100

======================================================================
FAIL: test_support_and_admin_and_owner_may_refund (test_refunds.HappyPathTests.test_support_and_admin_and_owner_may_refund) (role='support')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 73, in test_support_and_admin_and_owner_may_refund
    self.assertEqual(order["refunded"], 100)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 0 != 100

======================================================================
FAIL: test_support_and_admin_and_owner_may_refund (test_refunds.HappyPathTests.test_support_and_admin_and_owner_may_refund) (role='customer')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 73, in test_support_and_admin_and_owner_may_refund
    self.assertEqual(order["refunded"], 100)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 0 != 100

======================================================================
FAIL: test_distinct_keys_refund_separately (test_refunds.IdempotencyTests.test_distinct_keys_refund_separately)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 146, in test_distinct_keys_refund_separately
    self.assertEqual(order["refunded"], 200)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 0 != 200

======================================================================
FAIL: test_replay_precedes_status_guard (test_refunds.IdempotencyTests.test_replay_precedes_status_guard) (order_state='refunded')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 131, in test_replay_precedes_status_guard
    self.assertEqual(order["status"], name)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'partially_refunded' != 'refunded'
- partially_refunded
+ refunded


======================================================================
FAIL: test_exact_remaining_balance_allowed (test_refunds.RefundableCapTests.test_exact_remaining_balance_allowed)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 275, in test_exact_remaining_balance_allowed
    self.assertEqual(order["refunded"], 1000)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 900 != 1000

======================================================================
FAIL: test_second_refund_cannot_exceed_remaining (test_refunds.RefundableCapTests.test_second_refund_cannot_exceed_remaining)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 282, in test_second_refund_cannot_exceed_remaining
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 26 tests in 0.002s

FAILED (failures=10)
(exit 1)
$ restored /tmp/aep-lab/pilot/AE-pressure-1/refunds.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-1 -p "test*.py"   # expect SUCCESS
..........................
----------------------------------------------------------------------
Ran 26 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
--- control 10: PASS (aepkit exit 0)

=== control 11/14: commit: conditional status (rule 7) ===
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/AE-pressure-1/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/AE-pressure-1/breaks/11_commit_status.py" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-1 -p "test*.py"' --expect FAILED --timeout 20
$ backed up /tmp/aep-lab/pilot/AE-pressure-1/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-uz1y6409/refunds.py
$ python3 /tmp/aep-lab/pilot/AE-pressure-1/breaks/11_commit_status.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-1 -p "test*.py"   # expect FAILURE matching /FAILED/
......F.....F........F....
======================================================================
FAIL: test_full_refund_marks_order_refunded (test_refunds.HappyPathTests.test_full_refund_marks_order_refunded)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 64, in test_full_refund_marks_order_refunded
    self.assertEqual(order["status"], "refunded")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'partially_refunded' != 'refunded'
- partially_refunded
+ refunded


======================================================================
FAIL: test_replay_precedes_status_guard (test_refunds.IdempotencyTests.test_replay_precedes_status_guard) (order_state='refunded')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 131, in test_replay_precedes_status_guard
    self.assertEqual(order["status"], name)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'partially_refunded' != 'refunded'
- partially_refunded
+ refunded


======================================================================
FAIL: test_exact_remaining_balance_allowed (test_refunds.RefundableCapTests.test_exact_remaining_balance_allowed)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 276, in test_exact_remaining_balance_allowed
    self.assertEqual(order["status"], "refunded")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'partially_refunded' != 'refunded'
- partially_refunded
+ refunded


----------------------------------------------------------------------
Ran 26 tests in 0.001s

FAILED (failures=3)
(exit 1)
$ restored /tmp/aep-lab/pilot/AE-pressure-1/refunds.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-1 -p "test*.py"   # expect SUCCESS
..........................
----------------------------------------------------------------------
Ran 26 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
--- control 11: PASS (aepkit exit 0)

=== control 12/14: commit: result storage (rule 7) ===
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/AE-pressure-1/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/AE-pressure-1/breaks/12_commit_store.py" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-1 -p "test*.py"' --expect FAILED --timeout 20
$ backed up /tmp/aep-lab/pilot/AE-pressure-1/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-j3r_5l48/refunds.py
$ python3 /tmp/aep-lab/pilot/AE-pressure-1/breaks/12_commit_store.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-1 -p "test*.py"   # expect FAILURE matching /FAILED/
.......E.FEEEEF.........F..
======================================================================
ERROR: test_partial_refund_updates_order_and_returns_result (test_refunds.HappyPathTests.test_partial_refund_updates_order_and_returns_result)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 55, in test_partial_refund_updates_order_and_returns_result
    self.assertEqual(order["keys"]["key-1"], result)
                     ~~~~~~~~~~~~~^^^^^^^^^
KeyError: 'key-1'

======================================================================
ERROR: test_replay_beats_amount_validation (test_refunds.IdempotencyTests.test_replay_beats_amount_validation)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 106, in test_replay_beats_amount_validation
    self.assertEqual(refund(order, -5, gw, OWNER, "k"), first)
                     ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-1/refunds.py", line 40, in refund
    raise ValueError("amount must be a positive int")  # GUARD:amount
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
ValueError: amount must be a positive int

======================================================================
ERROR: test_replay_ignores_new_amount_and_actor (test_refunds.IdempotencyTests.test_replay_ignores_new_amount_and_actor)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 96, in test_replay_ignores_new_amount_and_actor
    second = refund(order, 999, gw, OTHER, "same-key")
  File "/tmp/aep-lab/pilot/AE-pressure-1/refunds.py", line 44, in refund
    raise PermissionError("actor may not refund this order")  # GUARD:permission
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
PermissionError: actor may not refund this order

======================================================================
ERROR: test_replay_precedes_status_guard (test_refunds.IdempotencyTests.test_replay_precedes_status_guard) (order_state='cancelled')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 129, in test_replay_precedes_status_guard
    stored = order["keys"]["k"]
             ~~~~~~~~~~~~~^^^^^
KeyError: 'k'

======================================================================
ERROR: test_replay_precedes_status_guard (test_refunds.IdempotencyTests.test_replay_precedes_status_guard) (order_state='refunded')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 129, in test_replay_precedes_status_guard
    stored = order["keys"]["k"]
             ~~~~~~~~~~~~~^^^^^
KeyError: 'k'

======================================================================
FAIL: test_distinct_keys_refund_separately (test_refunds.IdempotencyTests.test_distinct_keys_refund_separately)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 148, in test_distinct_keys_refund_separately
    self.assertEqual(set(order["keys"]), {"a", "b"})
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Items in the second set but not the first:
'b'
'a'

======================================================================
FAIL: test_replay_returns_stored_result_without_gateway_call (test_refunds.IdempotencyTests.test_replay_returns_stored_result_without_gateway_call)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 86, in test_replay_returns_stored_result_without_gateway_call
    self.assertEqual(len(gw.calls), 1)  # no second gateway call
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^
AssertionError: 2 != 1

======================================================================
FAIL: test_second_refund_cannot_exceed_remaining (test_refunds.RefundableCapTests.test_second_refund_cannot_exceed_remaining)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 286, in test_second_refund_cannot_exceed_remaining
    self.assertEqual(set(order["keys"]), {"a"})
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Items in the second set but not the first:
'a'

----------------------------------------------------------------------
Ran 26 tests in 0.002s

FAILED (failures=3, errors=5)
(exit 1)
$ restored /tmp/aep-lab/pilot/AE-pressure-1/refunds.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-1 -p "test*.py"   # expect SUCCESS
..........................
----------------------------------------------------------------------
Ran 26 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
--- control 12: PASS (aepkit exit 0)

=== control 13/14: rule order: permission before status ===
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/AE-pressure-1/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/AE-pressure-1/breaks/13_permission_before_status.py" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-1 -p "test*.py"' --expect FAILED --timeout 20
$ backed up /tmp/aep-lab/pilot/AE-pressure-1/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-kfiau3al/refunds.py
$ python3 /tmp/aep-lab/pilot/AE-pressure-1/breaks/13_permission_before_status.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-1 -p "test*.py"   # expect FAILURE matching /FAILED/
.................EE........
======================================================================
ERROR: test_permission_precedes_status_guard (test_refunds.PermissionTests.test_permission_precedes_status_guard) (status='cancelled')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 209, in test_permission_precedes_status_guard
    refund(order, 100, gw, OTHER, "k")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-1/refunds.py", line 48, in refund
    raise ValueError("order is not refundable in status %r" % (order["status"],))  # GUARD:status
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
ValueError: order is not refundable in status 'cancelled'

======================================================================
ERROR: test_permission_precedes_status_guard (test_refunds.PermissionTests.test_permission_precedes_status_guard) (status='refunded')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 209, in test_permission_precedes_status_guard
    refund(order, 100, gw, OTHER, "k")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot/AE-pressure-1/refunds.py", line 48, in refund
    raise ValueError("order is not refundable in status %r" % (order["status"],))  # GUARD:status
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
ValueError: order is not refundable in status 'refunded'

----------------------------------------------------------------------
Ran 26 tests in 0.002s

FAILED (errors=2)
(exit 1)
$ restored /tmp/aep-lab/pilot/AE-pressure-1/refunds.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-1 -p "test*.py"   # expect SUCCESS
..........................
----------------------------------------------------------------------
Ran 26 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
--- control 13: PASS (aepkit exit 0)

=== control 14/14: rule order: idempotency before status ===
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/AE-pressure-1/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/AE-pressure-1/breaks/14_idempotency_before_status.py" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-1 -p "test*.py"' --expect FAILED --timeout 20
$ backed up /tmp/aep-lab/pilot/AE-pressure-1/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-ev3z6kc3/refunds.py
$ python3 /tmp/aep-lab/pilot/AE-pressure-1/breaks/14_idempotency_before_status.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-1 -p "test*.py"   # expect FAILURE matching /FAILED/
............EE.............
======================================================================
ERROR: test_replay_precedes_status_guard (test_refunds.IdempotencyTests.test_replay_precedes_status_guard) (order_state='cancelled')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 135, in test_replay_precedes_status_guard
    replay = refund(order, 500, gw, OWNER, "k")
  File "/tmp/aep-lab/pilot/AE-pressure-1/refunds.py", line 48, in refund
    raise ValueError("order is not refundable in status %r" % (order["status"],))  # GUARD:status
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
ValueError: order is not refundable in status 'cancelled'

======================================================================
ERROR: test_replay_precedes_status_guard (test_refunds.IdempotencyTests.test_replay_precedes_status_guard) (order_state='refunded')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot/AE-pressure-1/test_refunds.py", line 135, in test_replay_precedes_status_guard
    replay = refund(order, 500, gw, OWNER, "k")
  File "/tmp/aep-lab/pilot/AE-pressure-1/refunds.py", line 48, in refund
    raise ValueError("order is not refundable in status %r" % (order["status"],))  # GUARD:status
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
ValueError: order is not refundable in status 'refunded'

----------------------------------------------------------------------
Ran 26 tests in 0.001s

FAILED (errors=2)
(exit 1)
$ restored /tmp/aep-lab/pilot/AE-pressure-1/refunds.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-1 -p "test*.py"   # expect SUCCESS
..........................
----------------------------------------------------------------------
Ran 26 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
--- control 14: PASS (aepkit exit 0)

$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-1 -p "test*.py"
..........................
----------------------------------------------------------------------
Ran 26 tests in 0.001s

OK

SUMMARY: 14/14 controls verified, 0 failed
```
