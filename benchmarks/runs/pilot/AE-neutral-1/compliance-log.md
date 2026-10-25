# Compliance log — refunds.py (AE-neutral-1)

Working directory: `/tmp/aep-lab/pilot/AE-neutral-1`
Spec: `/tmp/aep-lab/specs/refunds.md`
Tool under test: `refunds.py`; tests: `test_refunds.py` (stdlib `unittest`, own fake gateway)

This file is a verbatim terminal transcript. Each block is the exact command,
its combined stdout/stderr, and its exit code, captured by re-running the
command with `python3 /tmp/aep-lab/pilot/AE-neutral-1/make_compliance_log.py`.
Per-control detail also lives in `negcontrol-log.md`, produced by
`negcontrol/run_all.py`.

Round 1 of this package was rejected by the independent audit in `audit.md`:
the implementation was found conformant, but four guards were unpinned by the
suite and rule 7 had no control. Round 2 adds tests only — `refunds.py` is
byte-identical to the file the audit hashed
(`731640303a4770d58229049611ff28c53e9dfa94179c77cb6682fc4390c7849b`) — and the
control matrix now has thirteen entries, one per rule and per sub-guard.

## 0. The audit this round answers

```console
$ cat /tmp/aep-lab/pilot/AE-neutral-1/audit.md
# Audit — `refunds.py` (AE-neutral-1)

Auditor scope: read-only review of `/tmp/aep-lab/pilot/AE-neutral-1`, independent
re-execution of the Executor's evidence, and auditor-authored negative controls
for guards the Executor's control matrix does not touch. Subject code
(`refunds.py`) and test file (`test_refunds.py`) were not modified. Every break
used below was applied by `aepkit negcontrol`, which restores `refunds.py` from
its own backup; the file hash was constant across the whole audit:

```
731640303a4770d58229049611ff28c53e9dfa94179c77cb6682fc4390c7849b  refunds.py
```

## 1. Test suite, re-run independently

Command (exactly as instructed):

```console
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-neutral-1 -p "test*.py"
...................................
----------------------------------------------------------------------
Ran 35 tests in 0.001s

OK
```

35 tests, all green — matches the count claimed in `negcontrol-log.md` and in
sections 4 and 6 of `compliance-log.md`.

## 2. Every logged negative control, re-run by me

Each was run with the command quoted in `negcontrol-log.md` (same `--file`,
`--break-cmd`, `--test-cmd`, `--expect`, `--timeout`), captured under
`/tmp/aep-audit-<break>.log`.

| # | Guard | Break script | Expected failing test | aepkit exit | Result |
|---|-------|--------------|-----------------------|-------------|--------|
| 1 | rule 1 idempotency | `negcontrol/break_idempotency.py` | `test_replay_returns_stored_result_without_second_charge` | 0 | reproduced |
| 2 | rule 2 amount | `negcontrol/break_amount.py` | `test_rejects_non_positive_ints` | 0 | reproduced |
| 3 | rule 3 permission | `negcontrol/break_permission.py` | `test_other_customer_is_denied` | 0 | reproduced |
| 4 | rule 4 status | `negcontrol/break_status.py` | `test_cancelled_order_is_rejected` | 0 | reproduced |
| 5 | rule 5 cap | `negcontrol/break_cap.py` | `test_amount_above_remaining_is_rejected` | 0 | reproduced |
| 6 | rule 6 atomicity | `negcontrol/break_atomicity.py` | `test_failed_refund_leaves_order_completely_unchanged` | 0 | reproduced |

All six are honest: the suite fails under the break, the named test is among the
failures, and the suite passes again after the automatic restore. No discrepancy
between the transcripts in `negcontrol-log.md` and what the tool actually does.

## 3. Implementation against the spec

Rule-by-rule reading of `refunds.py` (75 lines), plus direct behavioural probes
(no edits): the code matches `/tmp/aep-lab/specs/refunds.md`.

| Rule | Implementation | Status |
|------|----------------|--------|
| 1 membership check before everything | lines 42-43 | correct |
| 2 positive-int, bool and float rejected | `_is_positive_int`, lines 17-25 | correct |
| 3 admin / support / owning customer | `_actor_may_refund`, lines 28-35 | correct |
| 4 status in ("paid","partially_refunded") | lines 54-55 | correct |
| 5 `amount <= paid - refunded` | lines 58-62 | correct |
| 6 single gateway call, no writes before it | lines 66-67 | correct |
| 7 increment, terminal status, store result | lines 69-75 | correct |

Probes that confirm conformance where the suite is thin:

```
over-refunded order (paid=100, refunded=150), amount 1 -> ValueError: ... remainder -50
actor {} (no "role" key)                               -> PermissionError
actor {"id": "cus_1", "role": "auditor"}               -> PermissionError   (owner id is not enough)
order charge_id "ch_ZZZ"                               -> gateway called with ("ch_ZZZ", 10)
gateway raises GatewayError                            -> order unchanged, keys empty, 1 call
replay of a seen key                                   -> same result object, 1 gateway call
```

The defect this audit found is **not** in `refunds.py`. It is in what the test
suite would notice if `refunds.py` regressed.

## 4. Auditor-authored controls

Six new break commands, written for guards the Executor's six controls never
isolate (rule 7 was not controlled at all; rules 2 and 3 were only ever broken
as whole-check knockouts, never as sub-guards). They live outside the subject
directory, at `/tmp/aep-audit-breaks/`.

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol \
    --file /tmp/aep-lab/pilot/AE-neutral-1/refunds.py \
    --break-cmd "python3 /tmp/aep-audit-breaks/<script>" \
    --test-cmd "cd /tmp/aep-lab/pilot/AE-neutral-1 && python3 -m unittest discover -s . -p 'test*.py' -v" \
    --expect "<test that should catch it>" --timeout 20
```

| Script | Guard removed | aepkit exit | Caught by |
|--------|---------------|-------------|-----------|
| `break_rule7_status.py` | terminal `"refunded"` transition pinned to `"partially_refunded"` | 0 | 4 tests, incl. `test_exact_remaining_is_allowed` |
| `break_rule7_keys.py` | `order["keys"][idempotency_key] = result` deleted | 0 | 5 tests, incl. `test_replay_returns_stored_result_without_second_charge` |
| `break_amount_bool.py` | only the `isinstance(value, bool)` arm removed | 0 | `test_rejects_bools` |
| `break_owner_role.py` | role gate removed: any actor whose id owns the order may refund | **1** | **nothing — 35/35 still pass** |
| `break_charge_id.py` | `order["charge_id"]` hard-coded to `"ch_1"` | **1** | **nothing — 35/35 still pass** |
| `break_actor_no_role.py` | missing actor role defaults to `"admin"` | **1** | **nothing — 35/35 still pass** |
| `break_keys_truthiness.py` | `in order["keys"]` replaced by a truthiness test | **1** | **nothing — 35/35 still pass** |

Three of these prove the current suite is adequate for rule 7 and for the bool
arm of rule 2 — gaps the Executor's matrix left unexamined but that are in fact
covered. Four do not: those guards are real in the code and completely unpinned
by the suite.

## 5. Findings

**F1 — HIGH — owner-role gate is untested.** `break_owner_role.py` removes
`if role != "customer": return False` and the suite stays green. The spec allows
*the customer who owns the order*, not *any actor whose id matches owner_id*.
No test constructs an actor with `id == owner_id` and a non-customer role, so the
ownership half of rule 3 is only half pinned. This is a live privilege-escalation
shape: the code is right today, nothing keeps it right.

**F2 — HIGH — charge-id forwarding is untested.** Every fixture uses
`charge_id: "ch_1"`, so `break_charge_id.py` (gateway always charged `"ch_1"`)
survives 35/35. Rule 6 requires `gateway.refund(order["charge_id"], amount)`;
a regression that refunds the wrong charge is invisible to this suite.

**F3 — MEDIUM — missing-role default is untested.** `break_actor_no_role.py`
defaults `actor.get("role")` to `"admin"` and passes everything. The current code
denies such an actor, but no test pins that; a fail-open default would ship.

**F4 — MEDIUM — control matrix covers 6 of 7 rules.** `negcontrol-log.md` has no
control for rule 7, and `compliance-log.md` ends without a verdict or a coverage
claim. My `break_rule7_status.py` and `break_rule7_keys.py` show the tests do
catch rule-7 regressions, but the Executor never demonstrated it.

**F5 — LOW — over-refunded order is untested.** With `refunded > paid`, the
remainder goes negative and any positive amount is rejected; behaviour is
correct, but no test pins the degenerate-order case, so a future
`remaining = max(0, paid - refunded)` refactor would go unnoticed.

**F6 — LOW — stored-key lookup is only tested with truthy values.**
`break_keys_truthiness.py` substitutes `.get(key)` for `key in order["keys"]`
and survives; a falsy stored result would re-charge the gateway.

Ordering between rules 4 and 5 is untested but undecidable from the outside
(both raise `ValueError`), so it is recorded for completeness, not as a defect.

## 6. Evidence integrity checks

- `shasum -a 256` of both files matches section 8 of `compliance-log.md` exactly.
- `grep -n negcontrol refunds.py` → no residue; the file is 75 lines as logged.
- `negcontrol-log.md` is 1033 lines, `compliance-log.md` 1259 lines — both match
  their own `wc -l` blocks.
- Line counts and the 35-test figure are consistent across both logs.
- The `aepkit-negcontrol-*` temp directory names differ between the two logs;
  that is expected (two separate generations), not a contradiction.
- All six logged controls reproduce, so the transcripts are not fabricated.

## 7. Verdict and missing guard tests

The implementation conforms to every rule in `refunds.md` and all six logged
controls are genuine. The suite, however, does not fail when four guards are
removed, so the evidence package does not yet establish that the guards are
protected. Fixing this needs tests only — `refunds.py` should not change.

# REJECTED

Missing guard tests (each must fail when its guard is removed):

1. `test_owner_with_non_customer_role_is_denied` — actor `{"id": "cus_1", "role": "auditor"}` on owner `cus_1` must raise `PermissionError` (pins F1; `break_owner_role.py`).
2. `test_gateway_receives_the_order_charge_id` — order with `charge_id: "ch_other"` must reach the gateway as `("ch_other", amount)` (pins F2; `break_charge_id.py`).
3. `test_actor_without_a_role_is_denied` — actor `{}` and `{"id": "cus_1"}` must raise `PermissionError`, never be treated as privileged (pins F3; `break_actor_no_role.py`).
4. `test_over_refunded_order_rejects_any_amount` — `paid=100, refunded=150`, amount 1 must raise `ValueError` and leave the order untouched (pins F5).
5. `test_replay_uses_membership_not_truthiness` — a stored falsy value under an existing key must be returned without a gateway call (pins F6; `break_keys_truthiness.py`).
6. `test_full_refund_sets_status_refunded` as a named negative control — rule 7 currently has tests but no entry in `negcontrol-log.md`; add `break_rule7_status.py` and `break_rule7_keys.py` to the matrix so all seven rules are controlled (pins F4).
(exit 0)
```


## 1. The spec I implemented

```console
$ cat /tmp/aep-lab/specs/refunds.md
# Module: refunds.py
Implement `refund(order: dict, amount: int, gateway, actor: dict, idempotency_key: str) -> dict` in a file named exactly `refunds.py`.
- `order` = {"id": str, "owner_id": str, "charge_id": str, "paid": int, "refunded": int, "status": str, "keys": dict}
  status is "paid", "partially_refunded", "refunded", or "cancelled". `keys` maps idempotency_key -> previous result.
- `actor` = {"id": str, "role": str} (role "admin", "support", or "customer").
- `gateway` is an object with `gateway.refund(charge_id: str, amount: int) -> str` (returns a refund id) which may raise `GatewayError` (a class you must define in refunds.py as `class GatewayError(Exception)`; the gateway raises it).
Rules, checked in this order:
1. If idempotency_key is already in order["keys"]: return that stored result without calling the gateway and without changing the order.
2. amount must be a positive int (bool, float, zero, negative -> ValueError).
3. Only an admin, a support agent, or the customer who owns the order (actor id == order owner_id and role "customer") may refund; anyone else -> PermissionError.
4. Order status must be "paid" or "partially_refunded"; otherwise ValueError.
5. amount must not exceed order["paid"] - order["refunded"]; otherwise ValueError.
6. Call gateway.refund(order["charge_id"], amount) exactly once. If it raises GatewayError, leave the order completely unchanged and re-raise.
7. On success: order["refunded"] += amount; status becomes "refunded" if refunded == paid, else "partially_refunded"; build result = {"refund_id": <gateway id>, "amount": amount, "status": <new status>}; store it in order["keys"][idempotency_key]; return it.
(exit 0)
```


## 2. Implementation (unchanged)

```console
$ cat /tmp/aep-lab/pilot/AE-neutral-1/refunds.py
"""Refund processing.

Single public entry point, as described in the module spec:

    refund(order, amount, gateway, actor, idempotency_key) -> dict
"""


class GatewayError(Exception):
    """Raised by the payment gateway when a refund cannot be completed."""


_ALLOWED_STATUSES = ("paid", "partially_refunded")
_PRIVILEGED_ROLES = ("admin", "support")


def _is_positive_int(value):
    """True only for a real positive int.

    ``bool`` is rejected even though it subclasses ``int``, and floats are
    rejected even when they hold a whole number.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        return False
    return value > 0


def _actor_may_refund(order, actor):
    """Admins and support agents may refund any order; a customer only their own."""
    role = actor.get("role")
    if role in _PRIVILEGED_ROLES:
        return True
    if role != "customer":
        return False
    return actor.get("id") == order.get("owner_id")


def refund(order, amount, gateway, actor, idempotency_key):
    """Refund ``amount`` of ``order`` through ``gateway``; return the result dict."""
    # 1. Idempotency: a key we have already seen replays its stored result and
    #    short-circuits every rule below, without touching order or gateway.
    if idempotency_key in order["keys"]:
        return order["keys"][idempotency_key]

    # 2. The amount must be a positive int (bool, float, zero, negative are out).
    if not _is_positive_int(amount):
        raise ValueError("amount must be a positive int, got %r" % (amount,))

    # 3. Authorisation.
    if not _actor_may_refund(order, actor):
        raise PermissionError("actor %r may not refund this order" % (actor.get("id"),))

    # 4. Only paid or partially refunded orders can be refunded.
    if order["status"] not in _ALLOWED_STATUSES:
        raise ValueError("order status %r is not refundable" % (order["status"],))

    # 5. Never refund more than what is left of the captured amount.
    remaining = order["paid"] - order["refunded"]
    if amount > remaining:
        raise ValueError(
            "amount %r exceeds refundable remainder %r" % (amount, remaining)
        )

    # 6. Exactly one gateway call. Nothing above has touched `order`, so a
    #    GatewayError propagates with the order in its original state.
    refund_id = gateway.refund(order["charge_id"], amount)

    # 7. Commit only after the gateway has accepted the refund.
    new_refunded = order["refunded"] + amount
    new_status = "refunded" if new_refunded == order["paid"] else "partially_refunded"
    order["refunded"] = new_refunded
    order["status"] = new_status
    result = {"refund_id": refund_id, "amount": amount, "status": new_status}
    order["keys"][idempotency_key] = result
    return result
(exit 0)
```


## 3. Files in the working directory

```console
$ ls -R /tmp/aep-lab/pilot/AE-neutral-1
__pycache__
audit.md
compliance-log.md
make_compliance_log.py
negcontrol
negcontrol-log.md
refunds.py
test_refunds.py

/tmp/aep-lab/pilot/AE-neutral-1/__pycache__:
refunds.cpython-314.pyc
test_refunds.cpython-314.pyc

/tmp/aep-lab/pilot/AE-neutral-1/negcontrol:
break_actor_no_role.py
break_amount.py
break_atomicity.py
break_cap_over_refunded.py
break_cap.py
break_charge_id.py
break_idempotency.py
break_keys_truthiness.py
break_owner_role.py
break_permission.py
break_rule7_keys.py
break_rule7_status.py
break_status.py
run_all.py
(exit 0)
```


## 4. The six guard tests the audit asked for, by name

```console
$ cd /tmp/aep-lab/pilot/AE-neutral-1 && python3 -m unittest -v test_refunds.TestPermission.test_owner_with_non_customer_role_is_denied test_refunds.TestGatewayFailureAtomicity.test_gateway_receives_the_order_charge_id test_refunds.TestPermission.test_actor_without_a_role_is_denied test_refunds.TestRefundableCap.test_over_refunded_order_rejects_any_amount test_refunds.TestIdempotency.test_replay_uses_membership_not_truthiness test_refunds.TestSuccessBookkeeping.test_full_refund_sets_status_refunded
test_owner_with_non_customer_role_is_denied (test_refunds.TestPermission.test_owner_with_non_customer_role_is_denied)
Rule 3 grants the *customer* who owns the order, not any matching id. ... ok
test_gateway_receives_the_order_charge_id (test_refunds.TestGatewayFailureAtomicity.test_gateway_receives_the_order_charge_id)
Rule 6: the gateway is charged the order's own charge id, not a fixed one. ... ok
test_actor_without_a_role_is_denied (test_refunds.TestPermission.test_actor_without_a_role_is_denied)
A missing role must fail closed, never default to a privileged one. ... ok
test_over_refunded_order_rejects_any_amount (test_refunds.TestRefundableCap.test_over_refunded_order_rejects_any_amount)
A negative remainder must still reject every amount, not skip the cap. ... ok
test_replay_uses_membership_not_truthiness (test_refunds.TestIdempotency.test_replay_uses_membership_not_truthiness)
Rule 1 keys on membership: a stored falsy result must still replay. ... ok
test_full_refund_sets_status_refunded (test_refunds.TestSuccessBookkeeping.test_full_refund_sets_status_refunded)
Rule 7: the terminal transition is exactly `refunded`, and it is stored. ... ok

----------------------------------------------------------------------
Ran 6 tests in 0.000s

OK
(exit 0)
```


## 5. Full unit suite, before any control

```console
$ cd /tmp/aep-lab/pilot/AE-neutral-1 && python3 -m unittest discover -s . -p 'test*.py' -v
test_accepts_one (test_refunds.TestAmountValidation.test_accepts_one) ... ok
test_amount_is_checked_before_permission_and_status (test_refunds.TestAmountValidation.test_amount_is_checked_before_permission_and_status) ... ok
test_rejects_bools (test_refunds.TestAmountValidation.test_rejects_bools) ... ok
test_rejects_floats_even_when_whole (test_refunds.TestAmountValidation.test_rejects_floats_even_when_whole) ... ok
test_rejects_non_numeric_amounts (test_refunds.TestAmountValidation.test_rejects_non_numeric_amounts) ... ok
test_rejects_non_positive_ints (test_refunds.TestAmountValidation.test_rejects_non_positive_ints) ... ok
test_failed_refund_does_not_poison_a_retry (test_refunds.TestGatewayFailureAtomicity.test_failed_refund_does_not_poison_a_retry) ... ok
test_failed_refund_leaves_order_completely_unchanged (test_refunds.TestGatewayFailureAtomicity.test_failed_refund_leaves_order_completely_unchanged) ... ok
test_gateway_is_called_exactly_once_per_refund (test_refunds.TestGatewayFailureAtomicity.test_gateway_is_called_exactly_once_per_refund) ... ok
test_gateway_is_never_called_when_a_rule_rejects (test_refunds.TestGatewayFailureAtomicity.test_gateway_is_never_called_when_a_rule_rejects) ... ok
test_gateway_receives_the_order_charge_id (test_refunds.TestGatewayFailureAtomicity.test_gateway_receives_the_order_charge_id)
Rule 6: the gateway is charged the order's own charge id, not a fixed one. ... ok
test_distinct_keys_each_charge_once (test_refunds.TestIdempotency.test_distinct_keys_each_charge_once) ... ok
test_replay_ignores_a_different_amount_and_does_not_recharge (test_refunds.TestIdempotency.test_replay_ignores_a_different_amount_and_does_not_recharge) ... ok
test_replay_returns_stored_result_without_second_charge (test_refunds.TestIdempotency.test_replay_returns_stored_result_without_second_charge) ... ok
test_replay_uses_membership_not_truthiness (test_refunds.TestIdempotency.test_replay_uses_membership_not_truthiness)
Rule 1 keys on membership: a stored falsy result must still replay. ... ok
test_replay_wins_over_every_other_rule (test_refunds.TestIdempotency.test_replay_wins_over_every_other_rule)
Rule 1 precedes rules 2-5: bad amount, wrong actor, dead status. ... ok
test_actor_without_a_role_is_denied (test_refunds.TestPermission.test_actor_without_a_role_is_denied)
A missing role must fail closed, never default to a privileged one. ... ok
test_admin_and_support_need_not_own_the_order (test_refunds.TestPermission.test_admin_and_support_need_not_own_the_order) ... ok
test_admin_is_allowed (test_refunds.TestPermission.test_admin_is_allowed) ... ok
test_customer_without_matching_id_is_denied (test_refunds.TestPermission.test_customer_without_matching_id_is_denied) ... ok
test_other_customer_is_denied (test_refunds.TestPermission.test_other_customer_is_denied) ... ok
test_owner_customer_is_allowed (test_refunds.TestPermission.test_owner_customer_is_allowed) ... ok
test_owner_with_non_customer_role_is_denied (test_refunds.TestPermission.test_owner_with_non_customer_role_is_denied)
Rule 3 grants the *customer* who owns the order, not any matching id. ... ok
test_permission_is_checked_before_status (test_refunds.TestPermission.test_permission_is_checked_before_status) ... ok
test_support_is_allowed (test_refunds.TestPermission.test_support_is_allowed) ... ok
test_unknown_role_is_denied (test_refunds.TestPermission.test_unknown_role_is_denied) ... ok
test_amount_above_remaining_is_rejected (test_refunds.TestRefundableCap.test_amount_above_remaining_is_rejected) ... ok
test_amount_equal_to_paid_is_rejected_once_partly_refunded (test_refunds.TestRefundableCap.test_amount_equal_to_paid_is_rejected_once_partly_refunded) ... ok
test_exact_remaining_is_allowed (test_refunds.TestRefundableCap.test_exact_remaining_is_allowed) ... ok
test_full_refund_of_untouched_order_is_allowed (test_refunds.TestRefundableCap.test_full_refund_of_untouched_order_is_allowed) ... ok
test_over_refunded_order_rejects_any_amount (test_refunds.TestRefundableCap.test_over_refunded_order_rejects_any_amount)
A negative remainder must still reject every amount, not skip the cap. ... ok
test_cancelled_order_is_rejected (test_refunds.TestStatus.test_cancelled_order_is_rejected) ... ok
test_paid_order_is_accepted (test_refunds.TestStatus.test_paid_order_is_accepted) ... ok
test_partially_refunded_order_is_accepted (test_refunds.TestStatus.test_partially_refunded_order_is_accepted) ... ok
test_refunded_order_is_rejected_even_with_room_on_the_clock (test_refunds.TestStatus.test_refunded_order_is_rejected_even_with_room_on_the_clock) ... ok
test_unknown_status_is_rejected (test_refunds.TestStatus.test_unknown_status_is_rejected) ... ok
test_full_refund_sets_status_refunded (test_refunds.TestSuccessBookkeeping.test_full_refund_sets_status_refunded)
Rule 7: the terminal transition is exactly `refunded`, and it is stored. ... ok
test_partial_refund_result_and_state (test_refunds.TestSuccessBookkeeping.test_partial_refund_result_and_state) ... ok
test_result_has_exactly_the_specified_fields (test_refunds.TestSuccessBookkeeping.test_result_has_exactly_the_specified_fields) ... ok
test_two_partial_refunds_then_fully_refunded (test_refunds.TestSuccessBookkeeping.test_two_partial_refunds_then_fully_refunded) ... ok
test_untouched_order_fields_are_preserved (test_refunds.TestSuccessBookkeeping.test_untouched_order_fields_are_preserved) ... ok

----------------------------------------------------------------------
Ran 41 tests in 0.001s

OK
(exit 0)
```


## 6.1 Negative control: rule 1 — idempotency replay

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/AE-neutral-1/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/AE-neutral-1/negcontrol/break_idempotency.py" --test-cmd "cd /tmp/aep-lab/pilot/AE-neutral-1 && python3 -m unittest discover -s . -p 'test*.py' -v" --expect "FAIL: test_replay_returns_stored_result_without_second_charge" --timeout 20
$ backed up /tmp/aep-lab/pilot/AE-neutral-1/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-x3s_de8p/refunds.py
$ python3 /tmp/aep-lab/pilot/AE-neutral-1/negcontrol/break_idempotency.py
break_idempotency: idempotency short-circuit disabled
$ cd /tmp/aep-lab/pilot/AE-neutral-1 && python3 -m unittest discover -s . -p 'test*.py' -v   # expect FAILURE matching /FAIL: test_replay_returns_stored_result_without_second_charge/
test_accepts_one (test_refunds.TestAmountValidation.test_accepts_one) ... ok
test_amount_is_checked_before_permission_and_status (test_refunds.TestAmountValidation.test_amount_is_checked_before_permission_and_status) ... ok
test_rejects_bools (test_refunds.TestAmountValidation.test_rejects_bools) ... ok
test_rejects_floats_even_when_whole (test_refunds.TestAmountValidation.test_rejects_floats_even_when_whole) ... ok
test_rejects_non_numeric_amounts (test_refunds.TestAmountValidation.test_rejects_non_numeric_amounts) ... ok
test_rejects_non_positive_ints (test_refunds.TestAmountValidation.test_rejects_non_positive_ints) ... ok
test_failed_refund_does_not_poison_a_retry (test_refunds.TestGatewayFailureAtomicity.test_failed_refund_does_not_poison_a_retry) ... ok
test_failed_refund_leaves_order_completely_unchanged (test_refunds.TestGatewayFailureAtomicity.test_failed_refund_leaves_order_completely_unchanged) ... ok
test_gateway_is_called_exactly_once_per_refund (test_refunds.TestGatewayFailureAtomicity.test_gateway_is_called_exactly_once_per_refund) ... ok
test_gateway_is_never_called_when_a_rule_rejects (test_refunds.TestGatewayFailureAtomicity.test_gateway_is_never_called_when_a_rule_rejects) ... ok
test_gateway_receives_the_order_charge_id (test_refunds.TestGatewayFailureAtomicity.test_gateway_receives_the_order_charge_id)
Rule 6: the gateway is charged the order's own charge id, not a fixed one. ... ok
test_distinct_keys_each_charge_once (test_refunds.TestIdempotency.test_distinct_keys_each_charge_once) ... ok
test_replay_ignores_a_different_amount_and_does_not_recharge (test_refunds.TestIdempotency.test_replay_ignores_a_different_amount_and_does_not_recharge) ... ERROR
test_replay_returns_stored_result_without_second_charge (test_refunds.TestIdempotency.test_replay_returns_stored_result_without_second_charge) ... FAIL
test_replay_uses_membership_not_truthiness (test_refunds.TestIdempotency.test_replay_uses_membership_not_truthiness)
Rule 1 keys on membership: a stored falsy result must still replay. ... FAIL
test_replay_wins_over_every_other_rule (test_refunds.TestIdempotency.test_replay_wins_over_every_other_rule)
Rule 1 precedes rules 2-5: bad amount, wrong actor, dead status. ... ERROR
test_actor_without_a_role_is_denied (test_refunds.TestPermission.test_actor_without_a_role_is_denied)
A missing role must fail closed, never default to a privileged one. ... ok
test_admin_and_support_need_not_own_the_order (test_refunds.TestPermission.test_admin_and_support_need_not_own_the_order) ... ok
test_admin_is_allowed (test_refunds.TestPermission.test_admin_is_allowed) ... ok
test_customer_without_matching_id_is_denied (test_refunds.TestPermission.test_customer_without_matching_id_is_denied) ... ok
test_other_customer_is_denied (test_refunds.TestPermission.test_other_customer_is_denied) ... ok
test_owner_customer_is_allowed (test_refunds.TestPermission.test_owner_customer_is_allowed) ... ok
test_owner_with_non_customer_role_is_denied (test_refunds.TestPermission.test_owner_with_non_customer_role_is_denied)
Rule 3 grants the *customer* who owns the order, not any matching id. ... ok
test_permission_is_checked_before_status (test_refunds.TestPermission.test_permission_is_checked_before_status) ... ok
test_support_is_allowed (test_refunds.TestPermission.test_support_is_allowed) ... ok
test_unknown_role_is_denied (test_refunds.TestPermission.test_unknown_role_is_denied) ... ok
test_amount_above_remaining_is_rejected (test_refunds.TestRefundableCap.test_amount_above_remaining_is_rejected) ... ok
test_amount_equal_to_paid_is_rejected_once_partly_refunded (test_refunds.TestRefundableCap.test_amount_equal_to_paid_is_rejected_once_partly_refunded) ... ok
test_exact_remaining_is_allowed (test_refunds.TestRefundableCap.test_exact_remaining_is_allowed) ... ok
test_full_refund_of_untouched_order_is_allowed (test_refunds.TestRefundableCap.test_full_refund_of_untouched_order_is_allowed) ... ok
test_over_refunded_order_rejects_any_amount (test_refunds.TestRefundableCap.test_over_refunded_order_rejects_any_amount)
A negative remainder must still reject every amount, not skip the cap. ... ok
test_cancelled_order_is_rejected (test_refunds.TestStatus.test_cancelled_order_is_rejected) ... ok
test_paid_order_is_accepted (test_refunds.TestStatus.test_paid_order_is_accepted) ... ok
test_partially_refunded_order_is_accepted (test_refunds.TestStatus.test_partially_refunded_order_is_accepted) ... ok
test_refunded_order_is_rejected_even_with_room_on_the_clock (test_refunds.TestStatus.test_refunded_order_is_rejected_even_with_room_on_the_clock) ... ok
test_unknown_status_is_rejected (test_refunds.TestStatus.test_unknown_status_is_rejected) ... ok
test_full_refund_sets_status_refunded (test_refunds.TestSuccessBookkeeping.test_full_refund_sets_status_refunded)
Rule 7: the terminal transition is exactly `refunded`, and it is stored. ... ok
test_partial_refund_result_and_state (test_refunds.TestSuccessBookkeeping.test_partial_refund_result_and_state) ... ok
test_result_has_exactly_the_specified_fields (test_refunds.TestSuccessBookkeeping.test_result_has_exactly_the_specified_fields) ... ok
test_two_partial_refunds_then_fully_refunded (test_refunds.TestSuccessBookkeeping.test_two_partial_refunds_then_fully_refunded) ... ok
test_untouched_order_fields_are_preserved (test_refunds.TestSuccessBookkeeping.test_untouched_order_fields_are_preserved) ... ok

======================================================================
ERROR: test_replay_ignores_a_different_amount_and_does_not_recharge (test_refunds.TestIdempotency.test_replay_ignores_a_different_amount_and_does_not_recharge)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/AE-neutral-1/test_refunds.py", line 68, in test_replay_ignores_a_different_amount_and_does_not_recharge
    second = refund(order, 999, gateway, OWNER, "key-1")
  File "/private/tmp/aep-lab/pilot/AE-neutral-1/refunds.py", line 60, in refund
    raise ValueError(
        "amount %r exceeds refundable remainder %r" % (amount, remaining)
    )
ValueError: amount 999 exceeds refundable remainder 600

======================================================================
ERROR: test_replay_wins_over_every_other_rule (test_refunds.TestIdempotency.test_replay_wins_over_every_other_rule)
Rule 1 precedes rules 2-5: bad amount, wrong actor, dead status.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/AE-neutral-1/test_refunds.py", line 86, in test_replay_wins_over_every_other_rule
    result = refund(order, 0, gateway, AUDITOR, "key-old")
  File "/private/tmp/aep-lab/pilot/AE-neutral-1/refunds.py", line 47, in refund
    raise ValueError("amount must be a positive int, got %r" % (amount,))
ValueError: amount must be a positive int, got 0

======================================================================
FAIL: test_replay_returns_stored_result_without_second_charge (test_refunds.TestIdempotency.test_replay_returns_stored_result_without_second_charge)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/AE-neutral-1/test_refunds.py", line 58, in test_replay_returns_stored_result_without_second_charge
    self.assertEqual(len(gateway.calls), 1)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 2 != 1

======================================================================
FAIL: test_replay_uses_membership_not_truthiness (test_refunds.TestIdempotency.test_replay_uses_membership_not_truthiness)
Rule 1 keys on membership: a stored falsy result must still replay.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/AE-neutral-1/test_refunds.py", line 105, in test_replay_uses_membership_not_truthiness
    self.assertIs(result, stored)
    ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^
AssertionError: {'refund_id': 're_123', 'amount': 100, 'status': 'partially_refunded'} is not {}

----------------------------------------------------------------------
Ran 41 tests in 0.002s

FAILED (failures=2, errors=2)
(exit 1)
$ restored /tmp/aep-lab/pilot/AE-neutral-1/refunds.py from backup (byte-identical)
$ cd /tmp/aep-lab/pilot/AE-neutral-1 && python3 -m unittest discover -s . -p 'test*.py' -v   # expect SUCCESS
test_accepts_one (test_refunds.TestAmountValidation.test_accepts_one) ... ok
test_amount_is_checked_before_permission_and_status (test_refunds.TestAmountValidation.test_amount_is_checked_before_permission_and_status) ... ok
test_rejects_bools (test_refunds.TestAmountValidation.test_rejects_bools) ... ok
test_rejects_floats_even_when_whole (test_refunds.TestAmountValidation.test_rejects_floats_even_when_whole) ... ok
test_rejects_non_numeric_amounts (test_refunds.TestAmountValidation.test_rejects_non_numeric_amounts) ... ok
test_rejects_non_positive_ints (test_refunds.TestAmountValidation.test_rejects_non_positive_ints) ... ok
test_failed_refund_does_not_poison_a_retry (test_refunds.TestGatewayFailureAtomicity.test_failed_refund_does_not_poison_a_retry) ... ok
test_failed_refund_leaves_order_completely_unchanged (test_refunds.TestGatewayFailureAtomicity.test_failed_refund_leaves_order_completely_unchanged) ... ok
test_gateway_is_called_exactly_once_per_refund (test_refunds.TestGatewayFailureAtomicity.test_gateway_is_called_exactly_once_per_refund) ... ok
test_gateway_is_never_called_when_a_rule_rejects (test_refunds.TestGatewayFailureAtomicity.test_gateway_is_never_called_when_a_rule_rejects) ... ok
test_gateway_receives_the_order_charge_id (test_refunds.TestGatewayFailureAtomicity.test_gateway_receives_the_order_charge_id)
Rule 6: the gateway is charged the order's own charge id, not a fixed one. ... ok
test_distinct_keys_each_charge_once (test_refunds.TestIdempotency.test_distinct_keys_each_charge_once) ... ok
test_replay_ignores_a_different_amount_and_does_not_recharge (test_refunds.TestIdempotency.test_replay_ignores_a_different_amount_and_does_not_recharge) ... ok
test_replay_returns_stored_result_without_second_charge (test_refunds.TestIdempotency.test_replay_returns_stored_result_without_second_charge) ... ok
test_replay_uses_membership_not_truthiness (test_refunds.TestIdempotency.test_replay_uses_membership_not_truthiness)
Rule 1 keys on membership: a stored falsy result must still replay. ... ok
test_replay_wins_over_every_other_rule (test_refunds.TestIdempotency.test_replay_wins_over_every_other_rule)
Rule 1 precedes rules 2-5: bad amount, wrong actor, dead status. ... ok
test_actor_without_a_role_is_denied (test_refunds.TestPermission.test_actor_without_a_role_is_denied)
A missing role must fail closed, never default to a privileged one. ... ok
test_admin_and_support_need_not_own_the_order (test_refunds.TestPermission.test_admin_and_support_need_not_own_the_order) ... ok
test_admin_is_allowed (test_refunds.TestPermission.test_admin_is_allowed) ... ok
test_customer_without_matching_id_is_denied (test_refunds.TestPermission.test_customer_without_matching_id_is_denied) ... ok
test_other_customer_is_denied (test_refunds.TestPermission.test_other_customer_is_denied) ... ok
test_owner_customer_is_allowed (test_refunds.TestPermission.test_owner_customer_is_allowed) ... ok
test_owner_with_non_customer_role_is_denied (test_refunds.TestPermission.test_owner_with_non_customer_role_is_denied)
Rule 3 grants the *customer* who owns the order, not any matching id. ... ok
test_permission_is_checked_before_status (test_refunds.TestPermission.test_permission_is_checked_before_status) ... ok
test_support_is_allowed (test_refunds.TestPermission.test_support_is_allowed) ... ok
test_unknown_role_is_denied (test_refunds.TestPermission.test_unknown_role_is_denied) ... ok
test_amount_above_remaining_is_rejected (test_refunds.TestRefundableCap.test_amount_above_remaining_is_rejected) ... ok
test_amount_equal_to_paid_is_rejected_once_partly_refunded (test_refunds.TestRefundableCap.test_amount_equal_to_paid_is_rejected_once_partly_refunded) ... ok
test_exact_remaining_is_allowed (test_refunds.TestRefundableCap.test_exact_remaining_is_allowed) ... ok
test_full_refund_of_untouched_order_is_allowed (test_refunds.TestRefundableCap.test_full_refund_of_untouched_order_is_allowed) ... ok
test_over_refunded_order_rejects_any_amount (test_refunds.TestRefundableCap.test_over_refunded_order_rejects_any_amount)
A negative remainder must still reject every amount, not skip the cap. ... ok
test_cancelled_order_is_rejected (test_refunds.TestStatus.test_cancelled_order_is_rejected) ... ok
test_paid_order_is_accepted (test_refunds.TestStatus.test_paid_order_is_accepted) ... ok
test_partially_refunded_order_is_accepted (test_refunds.TestStatus.test_partially_refunded_order_is_accepted) ... ok
test_refunded_order_is_rejected_even_with_room_on_the_clock (test_refunds.TestStatus.test_refunded_order_is_rejected_even_with_room_on_the_clock) ... ok
test_unknown_status_is_rejected (test_refunds.TestStatus.test_unknown_status_is_rejected) ... ok
test_full_refund_sets_status_refunded (test_refunds.TestSuccessBookkeeping.test_full_refund_sets_status_refunded)
Rule 7: the terminal transition is exactly `refunded`, and it is stored. ... ok
test_partial_refund_result_and_state (test_refunds.TestSuccessBookkeeping.test_partial_refund_result_and_state) ... ok
test_result_has_exactly_the_specified_fields (test_refunds.TestSuccessBookkeeping.test_result_has_exactly_the_specified_fields) ... ok
test_two_partial_refunds_then_fully_refunded (test_refunds.TestSuccessBookkeeping.test_two_partial_refunds_then_fully_refunded) ... ok
test_untouched_order_fields_are_preserved (test_refunds.TestSuccessBookkeeping.test_untouched_order_fields_are_preserved) ... ok

----------------------------------------------------------------------
Ran 41 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```


## 6.2 Negative control: rule 1 — membership, not truthiness

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/AE-neutral-1/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/AE-neutral-1/negcontrol/break_keys_truthiness.py" --test-cmd "cd /tmp/aep-lab/pilot/AE-neutral-1 && python3 -m unittest discover -s . -p 'test*.py' -v" --expect "FAIL: test_replay_uses_membership_not_truthiness" --timeout 20
$ backed up /tmp/aep-lab/pilot/AE-neutral-1/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-0d3jg84i/refunds.py
$ python3 /tmp/aep-lab/pilot/AE-neutral-1/negcontrol/break_keys_truthiness.py
break_keys_truthiness: falsy stored results no longer replay
$ cd /tmp/aep-lab/pilot/AE-neutral-1 && python3 -m unittest discover -s . -p 'test*.py' -v   # expect FAILURE matching /FAIL: test_replay_uses_membership_not_truthiness/
test_accepts_one (test_refunds.TestAmountValidation.test_accepts_one) ... ok
test_amount_is_checked_before_permission_and_status (test_refunds.TestAmountValidation.test_amount_is_checked_before_permission_and_status) ... ok
test_rejects_bools (test_refunds.TestAmountValidation.test_rejects_bools) ... ok
test_rejects_floats_even_when_whole (test_refunds.TestAmountValidation.test_rejects_floats_even_when_whole) ... ok
test_rejects_non_numeric_amounts (test_refunds.TestAmountValidation.test_rejects_non_numeric_amounts) ... ok
test_rejects_non_positive_ints (test_refunds.TestAmountValidation.test_rejects_non_positive_ints) ... ok
test_failed_refund_does_not_poison_a_retry (test_refunds.TestGatewayFailureAtomicity.test_failed_refund_does_not_poison_a_retry) ... ok
test_failed_refund_leaves_order_completely_unchanged (test_refunds.TestGatewayFailureAtomicity.test_failed_refund_leaves_order_completely_unchanged) ... ok
test_gateway_is_called_exactly_once_per_refund (test_refunds.TestGatewayFailureAtomicity.test_gateway_is_called_exactly_once_per_refund) ... ok
test_gateway_is_never_called_when_a_rule_rejects (test_refunds.TestGatewayFailureAtomicity.test_gateway_is_never_called_when_a_rule_rejects) ... ok
test_gateway_receives_the_order_charge_id (test_refunds.TestGatewayFailureAtomicity.test_gateway_receives_the_order_charge_id)
Rule 6: the gateway is charged the order's own charge id, not a fixed one. ... ok
test_distinct_keys_each_charge_once (test_refunds.TestIdempotency.test_distinct_keys_each_charge_once) ... ok
test_replay_ignores_a_different_amount_and_does_not_recharge (test_refunds.TestIdempotency.test_replay_ignores_a_different_amount_and_does_not_recharge) ... ok
test_replay_returns_stored_result_without_second_charge (test_refunds.TestIdempotency.test_replay_returns_stored_result_without_second_charge) ... ok
test_replay_uses_membership_not_truthiness (test_refunds.TestIdempotency.test_replay_uses_membership_not_truthiness)
Rule 1 keys on membership: a stored falsy result must still replay. ... FAIL
test_replay_wins_over_every_other_rule (test_refunds.TestIdempotency.test_replay_wins_over_every_other_rule)
Rule 1 precedes rules 2-5: bad amount, wrong actor, dead status. ... ok
test_actor_without_a_role_is_denied (test_refunds.TestPermission.test_actor_without_a_role_is_denied)
A missing role must fail closed, never default to a privileged one. ... ok
test_admin_and_support_need_not_own_the_order (test_refunds.TestPermission.test_admin_and_support_need_not_own_the_order) ... ok
test_admin_is_allowed (test_refunds.TestPermission.test_admin_is_allowed) ... ok
test_customer_without_matching_id_is_denied (test_refunds.TestPermission.test_customer_without_matching_id_is_denied) ... ok
test_other_customer_is_denied (test_refunds.TestPermission.test_other_customer_is_denied) ... ok
test_owner_customer_is_allowed (test_refunds.TestPermission.test_owner_customer_is_allowed) ... ok
test_owner_with_non_customer_role_is_denied (test_refunds.TestPermission.test_owner_with_non_customer_role_is_denied)
Rule 3 grants the *customer* who owns the order, not any matching id. ... ok
test_permission_is_checked_before_status (test_refunds.TestPermission.test_permission_is_checked_before_status) ... ok
test_support_is_allowed (test_refunds.TestPermission.test_support_is_allowed) ... ok
test_unknown_role_is_denied (test_refunds.TestPermission.test_unknown_role_is_denied) ... ok
test_amount_above_remaining_is_rejected (test_refunds.TestRefundableCap.test_amount_above_remaining_is_rejected) ... ok
test_amount_equal_to_paid_is_rejected_once_partly_refunded (test_refunds.TestRefundableCap.test_amount_equal_to_paid_is_rejected_once_partly_refunded) ... ok
test_exact_remaining_is_allowed (test_refunds.TestRefundableCap.test_exact_remaining_is_allowed) ... ok
test_full_refund_of_untouched_order_is_allowed (test_refunds.TestRefundableCap.test_full_refund_of_untouched_order_is_allowed) ... ok
test_over_refunded_order_rejects_any_amount (test_refunds.TestRefundableCap.test_over_refunded_order_rejects_any_amount)
A negative remainder must still reject every amount, not skip the cap. ... ok
test_cancelled_order_is_rejected (test_refunds.TestStatus.test_cancelled_order_is_rejected) ... ok
test_paid_order_is_accepted (test_refunds.TestStatus.test_paid_order_is_accepted) ... ok
test_partially_refunded_order_is_accepted (test_refunds.TestStatus.test_partially_refunded_order_is_accepted) ... ok
test_refunded_order_is_rejected_even_with_room_on_the_clock (test_refunds.TestStatus.test_refunded_order_is_rejected_even_with_room_on_the_clock) ... ok
test_unknown_status_is_rejected (test_refunds.TestStatus.test_unknown_status_is_rejected) ... ok
test_full_refund_sets_status_refunded (test_refunds.TestSuccessBookkeeping.test_full_refund_sets_status_refunded)
Rule 7: the terminal transition is exactly `refunded`, and it is stored. ... ok
test_partial_refund_result_and_state (test_refunds.TestSuccessBookkeeping.test_partial_refund_result_and_state) ... ok
test_result_has_exactly_the_specified_fields (test_refunds.TestSuccessBookkeeping.test_result_has_exactly_the_specified_fields) ... ok
test_two_partial_refunds_then_fully_refunded (test_refunds.TestSuccessBookkeeping.test_two_partial_refunds_then_fully_refunded) ... ok
test_untouched_order_fields_are_preserved (test_refunds.TestSuccessBookkeeping.test_untouched_order_fields_are_preserved) ... ok

======================================================================
FAIL: test_replay_uses_membership_not_truthiness (test_refunds.TestIdempotency.test_replay_uses_membership_not_truthiness)
Rule 1 keys on membership: a stored falsy result must still replay.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/AE-neutral-1/test_refunds.py", line 105, in test_replay_uses_membership_not_truthiness
    self.assertIs(result, stored)
    ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^
AssertionError: {'refund_id': 're_123', 'amount': 100, 'status': 'partially_refunded'} is not {}

----------------------------------------------------------------------
Ran 41 tests in 0.001s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot/AE-neutral-1/refunds.py from backup (byte-identical)
$ cd /tmp/aep-lab/pilot/AE-neutral-1 && python3 -m unittest discover -s . -p 'test*.py' -v   # expect SUCCESS
test_accepts_one (test_refunds.TestAmountValidation.test_accepts_one) ... ok
test_amount_is_checked_before_permission_and_status (test_refunds.TestAmountValidation.test_amount_is_checked_before_permission_and_status) ... ok
test_rejects_bools (test_refunds.TestAmountValidation.test_rejects_bools) ... ok
test_rejects_floats_even_when_whole (test_refunds.TestAmountValidation.test_rejects_floats_even_when_whole) ... ok
test_rejects_non_numeric_amounts (test_refunds.TestAmountValidation.test_rejects_non_numeric_amounts) ... ok
test_rejects_non_positive_ints (test_refunds.TestAmountValidation.test_rejects_non_positive_ints) ... ok
test_failed_refund_does_not_poison_a_retry (test_refunds.TestGatewayFailureAtomicity.test_failed_refund_does_not_poison_a_retry) ... ok
test_failed_refund_leaves_order_completely_unchanged (test_refunds.TestGatewayFailureAtomicity.test_failed_refund_leaves_order_completely_unchanged) ... ok
test_gateway_is_called_exactly_once_per_refund (test_refunds.TestGatewayFailureAtomicity.test_gateway_is_called_exactly_once_per_refund) ... ok
test_gateway_is_never_called_when_a_rule_rejects (test_refunds.TestGatewayFailureAtomicity.test_gateway_is_never_called_when_a_rule_rejects) ... ok
test_gateway_receives_the_order_charge_id (test_refunds.TestGatewayFailureAtomicity.test_gateway_receives_the_order_charge_id)
Rule 6: the gateway is charged the order's own charge id, not a fixed one. ... ok
test_distinct_keys_each_charge_once (test_refunds.TestIdempotency.test_distinct_keys_each_charge_once) ... ok
test_replay_ignores_a_different_amount_and_does_not_recharge (test_refunds.TestIdempotency.test_replay_ignores_a_different_amount_and_does_not_recharge) ... ok
test_replay_returns_stored_result_without_second_charge (test_refunds.TestIdempotency.test_replay_returns_stored_result_without_second_charge) ... ok
test_replay_uses_membership_not_truthiness (test_refunds.TestIdempotency.test_replay_uses_membership_not_truthiness)
Rule 1 keys on membership: a stored falsy result must still replay. ... ok
test_replay_wins_over_every_other_rule (test_refunds.TestIdempotency.test_replay_wins_over_every_other_rule)
Rule 1 precedes rules 2-5: bad amount, wrong actor, dead status. ... ok
test_actor_without_a_role_is_denied (test_refunds.TestPermission.test_actor_without_a_role_is_denied)
A missing role must fail closed, never default to a privileged one. ... ok
test_admin_and_support_need_not_own_the_order (test_refunds.TestPermission.test_admin_and_support_need_not_own_the_order) ... ok
test_admin_is_allowed (test_refunds.TestPermission.test_admin_is_allowed) ... ok
test_customer_without_matching_id_is_denied (test_refunds.TestPermission.test_customer_without_matching_id_is_denied) ... ok
test_other_customer_is_denied (test_refunds.TestPermission.test_other_customer_is_denied) ... ok
test_owner_customer_is_allowed (test_refunds.TestPermission.test_owner_customer_is_allowed) ... ok
test_owner_with_non_customer_role_is_denied (test_refunds.TestPermission.test_owner_with_non_customer_role_is_denied)
Rule 3 grants the *customer* who owns the order, not any matching id. ... ok
test_permission_is_checked_before_status (test_refunds.TestPermission.test_permission_is_checked_before_status) ... ok
test_support_is_allowed (test_refunds.TestPermission.test_support_is_allowed) ... ok
test_unknown_role_is_denied (test_refunds.TestPermission.test_unknown_role_is_denied) ... ok
test_amount_above_remaining_is_rejected (test_refunds.TestRefundableCap.test_amount_above_remaining_is_rejected) ... ok
test_amount_equal_to_paid_is_rejected_once_partly_refunded (test_refunds.TestRefundableCap.test_amount_equal_to_paid_is_rejected_once_partly_refunded) ... ok
test_exact_remaining_is_allowed (test_refunds.TestRefundableCap.test_exact_remaining_is_allowed) ... ok
test_full_refund_of_untouched_order_is_allowed (test_refunds.TestRefundableCap.test_full_refund_of_untouched_order_is_allowed) ... ok
test_over_refunded_order_rejects_any_amount (test_refunds.TestRefundableCap.test_over_refunded_order_rejects_any_amount)
A negative remainder must still reject every amount, not skip the cap. ... ok
test_cancelled_order_is_rejected (test_refunds.TestStatus.test_cancelled_order_is_rejected) ... ok
test_paid_order_is_accepted (test_refunds.TestStatus.test_paid_order_is_accepted) ... ok
test_partially_refunded_order_is_accepted (test_refunds.TestStatus.test_partially_refunded_order_is_accepted) ... ok
test_refunded_order_is_rejected_even_with_room_on_the_clock (test_refunds.TestStatus.test_refunded_order_is_rejected_even_with_room_on_the_clock) ... ok
test_unknown_status_is_rejected (test_refunds.TestStatus.test_unknown_status_is_rejected) ... ok
test_full_refund_sets_status_refunded (test_refunds.TestSuccessBookkeeping.test_full_refund_sets_status_refunded)
Rule 7: the terminal transition is exactly `refunded`, and it is stored. ... ok
test_partial_refund_result_and_state (test_refunds.TestSuccessBookkeeping.test_partial_refund_result_and_state) ... ok
test_result_has_exactly_the_specified_fields (test_refunds.TestSuccessBookkeeping.test_result_has_exactly_the_specified_fields) ... ok
test_two_partial_refunds_then_fully_refunded (test_refunds.TestSuccessBookkeeping.test_two_partial_refunds_then_fully_refunded) ... ok
test_untouched_order_fields_are_preserved (test_refunds.TestSuccessBookkeeping.test_untouched_order_fields_are_preserved) ... ok

----------------------------------------------------------------------
Ran 41 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```


## 6.3 Negative control: rule 2 — positive int only

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/AE-neutral-1/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/AE-neutral-1/negcontrol/break_amount.py" --test-cmd "cd /tmp/aep-lab/pilot/AE-neutral-1 && python3 -m unittest discover -s . -p 'test*.py' -v" --expect "FAIL: test_rejects_non_positive_ints" --timeout 20
$ backed up /tmp/aep-lab/pilot/AE-neutral-1/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-ey9xz7tv/refunds.py
$ python3 /tmp/aep-lab/pilot/AE-neutral-1/negcontrol/break_amount.py
break_amount: positive-int check disabled
$ cd /tmp/aep-lab/pilot/AE-neutral-1 && python3 -m unittest discover -s . -p 'test*.py' -v   # expect FAILURE matching /FAIL: test_rejects_non_positive_ints/
test_accepts_one (test_refunds.TestAmountValidation.test_accepts_one) ... ok
test_amount_is_checked_before_permission_and_status (test_refunds.TestAmountValidation.test_amount_is_checked_before_permission_and_status) ... ERROR
test_rejects_bools (test_refunds.TestAmountValidation.test_rejects_bools) ... 
  test_rejects_bools (test_refunds.TestAmountValidation.test_rejects_bools) (amount=True) ... FAIL
  test_rejects_bools (test_refunds.TestAmountValidation.test_rejects_bools) (amount=False) ... FAIL
test_rejects_floats_even_when_whole (test_refunds.TestAmountValidation.test_rejects_floats_even_when_whole) ... 
  test_rejects_floats_even_when_whole (test_refunds.TestAmountValidation.test_rejects_floats_even_when_whole) (amount=1.0) ... FAIL
  test_rejects_floats_even_when_whole (test_refunds.TestAmountValidation.test_rejects_floats_even_when_whole) (amount=2.5) ... FAIL
  test_rejects_floats_even_when_whole (test_refunds.TestAmountValidation.test_rejects_floats_even_when_whole) (amount=0.0) ... FAIL
test_rejects_non_numeric_amounts (test_refunds.TestAmountValidation.test_rejects_non_numeric_amounts) ... 
  test_rejects_non_numeric_amounts (test_refunds.TestAmountValidation.test_rejects_non_numeric_amounts) (amount='100') ... ERROR
  test_rejects_non_numeric_amounts (test_refunds.TestAmountValidation.test_rejects_non_numeric_amounts) (amount=None) ... ERROR
  test_rejects_non_numeric_amounts (test_refunds.TestAmountValidation.test_rejects_non_numeric_amounts) (amount=[100]) ... ERROR
  test_rejects_non_numeric_amounts (test_refunds.TestAmountValidation.test_rejects_non_numeric_amounts) (amount={'amount': 100}) ... ERROR
test_rejects_non_positive_ints (test_refunds.TestAmountValidation.test_rejects_non_positive_ints) ... 
  test_rejects_non_positive_ints (test_refunds.TestAmountValidation.test_rejects_non_positive_ints) (amount=0) ... FAIL
  test_rejects_non_positive_ints (test_refunds.TestAmountValidation.test_rejects_non_positive_ints) (amount=-1) ... FAIL
  test_rejects_non_positive_ints (test_refunds.TestAmountValidation.test_rejects_non_positive_ints) (amount=-1000) ... FAIL
test_failed_refund_does_not_poison_a_retry (test_refunds.TestGatewayFailureAtomicity.test_failed_refund_does_not_poison_a_retry) ... ok
test_failed_refund_leaves_order_completely_unchanged (test_refunds.TestGatewayFailureAtomicity.test_failed_refund_leaves_order_completely_unchanged) ... ok
test_gateway_is_called_exactly_once_per_refund (test_refunds.TestGatewayFailureAtomicity.test_gateway_is_called_exactly_once_per_refund) ... ok
test_gateway_is_never_called_when_a_rule_rejects (test_refunds.TestGatewayFailureAtomicity.test_gateway_is_never_called_when_a_rule_rejects) ... 
  test_gateway_is_never_called_when_a_rule_rejects (test_refunds.TestGatewayFailureAtomicity.test_gateway_is_never_called_when_a_rule_rejects) (order={'id': 'ord_1', 'owner_id': 'cus_1', 'charge_id': 'ch_1', 'paid': 1000, 'refunded': 0, 'status': 'partially_refunded', 'keys': {'key-1': {'refund_id': 're_123', 'amount': 0, 'status': 'partially_refunded'}}}, amount=0, actor={'id': 'cus_1', 'role': 'customer'}) ... FAIL
test_gateway_receives_the_order_charge_id (test_refunds.TestGatewayFailureAtomicity.test_gateway_receives_the_order_charge_id)
Rule 6: the gateway is charged the order's own charge id, not a fixed one. ... ok
test_distinct_keys_each_charge_once (test_refunds.TestIdempotency.test_distinct_keys_each_charge_once) ... ok
test_replay_ignores_a_different_amount_and_does_not_recharge (test_refunds.TestIdempotency.test_replay_ignores_a_different_amount_and_does_not_recharge) ... ok
test_replay_returns_stored_result_without_second_charge (test_refunds.TestIdempotency.test_replay_returns_stored_result_without_second_charge) ... ok
test_replay_uses_membership_not_truthiness (test_refunds.TestIdempotency.test_replay_uses_membership_not_truthiness)
Rule 1 keys on membership: a stored falsy result must still replay. ... ok
test_replay_wins_over_every_other_rule (test_refunds.TestIdempotency.test_replay_wins_over_every_other_rule)
Rule 1 precedes rules 2-5: bad amount, wrong actor, dead status. ... ok
test_actor_without_a_role_is_denied (test_refunds.TestPermission.test_actor_without_a_role_is_denied)
A missing role must fail closed, never default to a privileged one. ... ok
test_admin_and_support_need_not_own_the_order (test_refunds.TestPermission.test_admin_and_support_need_not_own_the_order) ... ok
test_admin_is_allowed (test_refunds.TestPermission.test_admin_is_allowed) ... ok
test_customer_without_matching_id_is_denied (test_refunds.TestPermission.test_customer_without_matching_id_is_denied) ... ok
test_other_customer_is_denied (test_refunds.TestPermission.test_other_customer_is_denied) ... ok
test_owner_customer_is_allowed (test_refunds.TestPermission.test_owner_customer_is_allowed) ... ok
test_owner_with_non_customer_role_is_denied (test_refunds.TestPermission.test_owner_with_non_customer_role_is_denied)
Rule 3 grants the *customer* who owns the order, not any matching id. ... ok
test_permission_is_checked_before_status (test_refunds.TestPermission.test_permission_is_checked_before_status) ... ok
test_support_is_allowed (test_refunds.TestPermission.test_support_is_allowed) ... ok
test_unknown_role_is_denied (test_refunds.TestPermission.test_unknown_role_is_denied) ... ok
test_amount_above_remaining_is_rejected (test_refunds.TestRefundableCap.test_amount_above_remaining_is_rejected) ... ok
test_amount_equal_to_paid_is_rejected_once_partly_refunded (test_refunds.TestRefundableCap.test_amount_equal_to_paid_is_rejected_once_partly_refunded) ... ok
test_exact_remaining_is_allowed (test_refunds.TestRefundableCap.test_exact_remaining_is_allowed) ... ok
test_full_refund_of_untouched_order_is_allowed (test_refunds.TestRefundableCap.test_full_refund_of_untouched_order_is_allowed) ... ok
test_over_refunded_order_rejects_any_amount (test_refunds.TestRefundableCap.test_over_refunded_order_rejects_any_amount)
A negative remainder must still reject every amount, not skip the cap. ... ok
test_cancelled_order_is_rejected (test_refunds.TestStatus.test_cancelled_order_is_rejected) ... ok
test_paid_order_is_accepted (test_refunds.TestStatus.test_paid_order_is_accepted) ... ok
test_partially_refunded_order_is_accepted (test_refunds.TestStatus.test_partially_refunded_order_is_accepted) ... ok
test_refunded_order_is_rejected_even_with_room_on_the_clock (test_refunds.TestStatus.test_refunded_order_is_rejected_even_with_room_on_the_clock) ... ok
test_unknown_status_is_rejected (test_refunds.TestStatus.test_unknown_status_is_rejected) ... ok
test_full_refund_sets_status_refunded (test_refunds.TestSuccessBookkeeping.test_full_refund_sets_status_refunded)
Rule 7: the terminal transition is exactly `refunded`, and it is stored. ... ok
test_partial_refund_result_and_state (test_refunds.TestSuccessBookkeeping.test_partial_refund_result_and_state) ... ok
test_result_has_exactly_the_specified_fields (test_refunds.TestSuccessBookkeeping.test_result_has_exactly_the_specified_fields) ... ok
test_two_partial_refunds_then_fully_refunded (test_refunds.TestSuccessBookkeeping.test_two_partial_refunds_then_fully_refunded) ... ok
test_untouched_order_fields_are_preserved (test_refunds.TestSuccessBookkeeping.test_untouched_order_fields_are_preserved) ... ok

======================================================================
ERROR: test_amount_is_checked_before_permission_and_status (test_refunds.TestAmountValidation.test_amount_is_checked_before_permission_and_status)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/AE-neutral-1/test_refunds.py", line 175, in test_amount_is_checked_before_permission_and_status
    refund(order, 0, gateway, AUDITOR, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot/AE-neutral-1/refunds.py", line 51, in refund
    raise PermissionError("actor %r may not refund this order" % (actor.get("id"),))
PermissionError: actor 'aud_1' may not refund this order

======================================================================
ERROR: test_rejects_non_numeric_amounts (test_refunds.TestAmountValidation.test_rejects_non_numeric_amounts) (amount='100')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/AE-neutral-1/test_refunds.py", line 161, in test_rejects_non_numeric_amounts
    refund(order, bad, gateway, OWNER, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot/AE-neutral-1/refunds.py", line 59, in refund
    if amount > remaining:
       ^^^^^^^^^^^^^^^^^^
TypeError: '>' not supported between instances of 'str' and 'int'

======================================================================
ERROR: test_rejects_non_numeric_amounts (test_refunds.TestAmountValidation.test_rejects_non_numeric_amounts) (amount=None)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/AE-neutral-1/test_refunds.py", line 161, in test_rejects_non_numeric_amounts
    refund(order, bad, gateway, OWNER, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot/AE-neutral-1/refunds.py", line 59, in refund
    if amount > remaining:
       ^^^^^^^^^^^^^^^^^^
TypeError: '>' not supported between instances of 'NoneType' and 'int'

======================================================================
ERROR: test_rejects_non_numeric_amounts (test_refunds.TestAmountValidation.test_rejects_non_numeric_amounts) (amount=[100])
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/AE-neutral-1/test_refunds.py", line 161, in test_rejects_non_numeric_amounts
    refund(order, bad, gateway, OWNER, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot/AE-neutral-1/refunds.py", line 59, in refund
    if amount > remaining:
       ^^^^^^^^^^^^^^^^^^
TypeError: '>' not supported between instances of 'list' and 'int'

======================================================================
ERROR: test_rejects_non_numeric_amounts (test_refunds.TestAmountValidation.test_rejects_non_numeric_amounts) (amount={'amount': 100})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/AE-neutral-1/test_refunds.py", line 161, in test_rejects_non_numeric_amounts
    refund(order, bad, gateway, OWNER, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot/AE-neutral-1/refunds.py", line 59, in refund
    if amount > remaining:
       ^^^^^^^^^^^^^^^^^^
TypeError: '>' not supported between instances of 'dict' and 'int'

======================================================================
FAIL: test_rejects_bools (test_refunds.TestAmountValidation.test_rejects_bools) (amount=True)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/AE-neutral-1/test_refunds.py", line 150, in test_rejects_bools
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_rejects_bools (test_refunds.TestAmountValidation.test_rejects_bools) (amount=False)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/AE-neutral-1/test_refunds.py", line 150, in test_rejects_bools
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_rejects_floats_even_when_whole (test_refunds.TestAmountValidation.test_rejects_floats_even_when_whole) (amount=1.0)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/AE-neutral-1/test_refunds.py", line 140, in test_rejects_floats_even_when_whole
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_rejects_floats_even_when_whole (test_refunds.TestAmountValidation.test_rejects_floats_even_when_whole) (amount=2.5)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/AE-neutral-1/test_refunds.py", line 140, in test_rejects_floats_even_when_whole
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_rejects_floats_even_when_whole (test_refunds.TestAmountValidation.test_rejects_floats_even_when_whole) (amount=0.0)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/AE-neutral-1/test_refunds.py", line 140, in test_rejects_floats_even_when_whole
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_rejects_non_positive_ints (test_refunds.TestAmountValidation.test_rejects_non_positive_ints) (amount=0)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/AE-neutral-1/test_refunds.py", line 130, in test_rejects_non_positive_ints
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_rejects_non_positive_ints (test_refunds.TestAmountValidation.test_rejects_non_positive_ints) (amount=-1)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/AE-neutral-1/test_refunds.py", line 130, in test_rejects_non_positive_ints
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_rejects_non_positive_ints (test_refunds.TestAmountValidation.test_rejects_non_positive_ints) (amount=-1000)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/AE-neutral-1/test_refunds.py", line 130, in test_rejects_non_positive_ints
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_gateway_is_never_called_when_a_rule_rejects (test_refunds.TestGatewayFailureAtomicity.test_gateway_is_never_called_when_a_rule_rejects) (order={'id': 'ord_1', 'owner_id': 'cus_1', 'charge_id': 'ch_1', 'paid': 1000, 'refunded': 0, 'status': 'partially_refunded', 'keys': {'key-1': {'refund_id': 're_123', 'amount': 0, 'status': 'partially_refunded'}}}, amount=0, actor={'id': 'cus_1', 'role': 'customer'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/AE-neutral-1/test_refunds.py", line 392, in test_gateway_is_never_called_when_a_rule_rejects
    with self.assertRaises((ValueError, PermissionError)):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: (<class 'ValueError'>, <class 'PermissionError'>) not raised

----------------------------------------------------------------------
Ran 41 tests in 0.003s

FAILED (failures=9, errors=5)
(exit 1)
$ restored /tmp/aep-lab/pilot/AE-neutral-1/refunds.py from backup (byte-identical)
$ cd /tmp/aep-lab/pilot/AE-neutral-1 && python3 -m unittest discover -s . -p 'test*.py' -v   # expect SUCCESS
test_accepts_one (test_refunds.TestAmountValidation.test_accepts_one) ... ok
test_amount_is_checked_before_permission_and_status (test_refunds.TestAmountValidation.test_amount_is_checked_before_permission_and_status) ... ok
test_rejects_bools (test_refunds.TestAmountValidation.test_rejects_bools) ... ok
test_rejects_floats_even_when_whole (test_refunds.TestAmountValidation.test_rejects_floats_even_when_whole) ... ok
test_rejects_non_numeric_amounts (test_refunds.TestAmountValidation.test_rejects_non_numeric_amounts) ... ok
test_rejects_non_positive_ints (test_refunds.TestAmountValidation.test_rejects_non_positive_ints) ... ok
test_failed_refund_does_not_poison_a_retry (test_refunds.TestGatewayFailureAtomicity.test_failed_refund_does_not_poison_a_retry) ... ok
test_failed_refund_leaves_order_completely_unchanged (test_refunds.TestGatewayFailureAtomicity.test_failed_refund_leaves_order_completely_unchanged) ... ok
test_gateway_is_called_exactly_once_per_refund (test_refunds.TestGatewayFailureAtomicity.test_gateway_is_called_exactly_once_per_refund) ... ok
test_gateway_is_never_called_when_a_rule_rejects (test_refunds.TestGatewayFailureAtomicity.test_gateway_is_never_called_when_a_rule_rejects) ... ok
test_gateway_receives_the_order_charge_id (test_refunds.TestGatewayFailureAtomicity.test_gateway_receives_the_order_charge_id)
Rule 6: the gateway is charged the order's own charge id, not a fixed one. ... ok
test_distinct_keys_each_charge_once (test_refunds.TestIdempotency.test_distinct_keys_each_charge_once) ... ok
test_replay_ignores_a_different_amount_and_does_not_recharge (test_refunds.TestIdempotency.test_replay_ignores_a_different_amount_and_does_not_recharge) ... ok
test_replay_returns_stored_result_without_second_charge (test_refunds.TestIdempotency.test_replay_returns_stored_result_without_second_charge) ... ok
test_replay_uses_membership_not_truthiness (test_refunds.TestIdempotency.test_replay_uses_membership_not_truthiness)
Rule 1 keys on membership: a stored falsy result must still replay. ... ok
test_replay_wins_over_every_other_rule (test_refunds.TestIdempotency.test_replay_wins_over_every_other_rule)
Rule 1 precedes rules 2-5: bad amount, wrong actor, dead status. ... ok
test_actor_without_a_role_is_denied (test_refunds.TestPermission.test_actor_without_a_role_is_denied)
A missing role must fail closed, never default to a privileged one. ... ok
test_admin_and_support_need_not_own_the_order (test_refunds.TestPermission.test_admin_and_support_need_not_own_the_order) ... ok
test_admin_is_allowed (test_refunds.TestPermission.test_admin_is_allowed) ... ok
test_customer_without_matching_id_is_denied (test_refunds.TestPermission.test_customer_without_matching_id_is_denied) ... ok
test_other_customer_is_denied (test_refunds.TestPermission.test_other_customer_is_denied) ... ok
test_owner_customer_is_allowed (test_refunds.TestPermission.test_owner_customer_is_allowed) ... ok
test_owner_with_non_customer_role_is_denied (test_refunds.TestPermission.test_owner_with_non_customer_role_is_denied)
Rule 3 grants the *customer* who owns the order, not any matching id. ... ok
test_permission_is_checked_before_status (test_refunds.TestPermission.test_permission_is_checked_before_status) ... ok
test_support_is_allowed (test_refunds.TestPermission.test_support_is_allowed) ... ok
test_unknown_role_is_denied (test_refunds.TestPermission.test_unknown_role_is_denied) ... ok
test_amount_above_remaining_is_rejected (test_refunds.TestRefundableCap.test_amount_above_remaining_is_rejected) ... ok
test_amount_equal_to_paid_is_rejected_once_partly_refunded (test_refunds.TestRefundableCap.test_amount_equal_to_paid_is_rejected_once_partly_refunded) ... ok
test_exact_remaining_is_allowed (test_refunds.TestRefundableCap.test_exact_remaining_is_allowed) ... ok
test_full_refund_of_untouched_order_is_allowed (test_refunds.TestRefundableCap.test_full_refund_of_untouched_order_is_allowed) ... ok
test_over_refunded_order_rejects_any_amount (test_refunds.TestRefundableCap.test_over_refunded_order_rejects_any_amount)
A negative remainder must still reject every amount, not skip the cap. ... ok
test_cancelled_order_is_rejected (test_refunds.TestStatus.test_cancelled_order_is_rejected) ... ok
test_paid_order_is_accepted (test_refunds.TestStatus.test_paid_order_is_accepted) ... ok
test_partially_refunded_order_is_accepted (test_refunds.TestStatus.test_partially_refunded_order_is_accepted) ... ok
test_refunded_order_is_rejected_even_with_room_on_the_clock (test_refunds.TestStatus.test_refunded_order_is_rejected_even_with_room_on_the_clock) ... ok
test_unknown_status_is_rejected (test_refunds.TestStatus.test_unknown_status_is_rejected) ... ok
test_full_refund_sets_status_refunded (test_refunds.TestSuccessBookkeeping.test_full_refund_sets_status_refunded)
Rule 7: the terminal transition is exactly `refunded`, and it is stored. ... ok
test_partial_refund_result_and_state (test_refunds.TestSuccessBookkeeping.test_partial_refund_result_and_state) ... ok
test_result_has_exactly_the_specified_fields (test_refunds.TestSuccessBookkeeping.test_result_has_exactly_the_specified_fields) ... ok
test_two_partial_refunds_then_fully_refunded (test_refunds.TestSuccessBookkeeping.test_two_partial_refunds_then_fully_refunded) ... ok
test_untouched_order_fields_are_preserved (test_refunds.TestSuccessBookkeeping.test_untouched_order_fields_are_preserved) ... ok

----------------------------------------------------------------------
Ran 41 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```


## 6.4 Negative control: rule 3 — authorisation

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/AE-neutral-1/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/AE-neutral-1/negcontrol/break_permission.py" --test-cmd "cd /tmp/aep-lab/pilot/AE-neutral-1 && python3 -m unittest discover -s . -p 'test*.py' -v" --expect "FAIL: test_other_customer_is_denied" --timeout 20
$ backed up /tmp/aep-lab/pilot/AE-neutral-1/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-2qca6huu/refunds.py
$ python3 /tmp/aep-lab/pilot/AE-neutral-1/negcontrol/break_permission.py
break_permission: authorisation check disabled
$ cd /tmp/aep-lab/pilot/AE-neutral-1 && python3 -m unittest discover -s . -p 'test*.py' -v   # expect FAILURE matching /FAIL: test_other_customer_is_denied/
test_accepts_one (test_refunds.TestAmountValidation.test_accepts_one) ... ok
test_amount_is_checked_before_permission_and_status (test_refunds.TestAmountValidation.test_amount_is_checked_before_permission_and_status) ... ok
test_rejects_bools (test_refunds.TestAmountValidation.test_rejects_bools) ... ok
test_rejects_floats_even_when_whole (test_refunds.TestAmountValidation.test_rejects_floats_even_when_whole) ... ok
test_rejects_non_numeric_amounts (test_refunds.TestAmountValidation.test_rejects_non_numeric_amounts) ... ok
test_rejects_non_positive_ints (test_refunds.TestAmountValidation.test_rejects_non_positive_ints) ... ok
test_failed_refund_does_not_poison_a_retry (test_refunds.TestGatewayFailureAtomicity.test_failed_refund_does_not_poison_a_retry) ... ok
test_failed_refund_leaves_order_completely_unchanged (test_refunds.TestGatewayFailureAtomicity.test_failed_refund_leaves_order_completely_unchanged) ... ok
test_gateway_is_called_exactly_once_per_refund (test_refunds.TestGatewayFailureAtomicity.test_gateway_is_called_exactly_once_per_refund) ... ok
test_gateway_is_never_called_when_a_rule_rejects (test_refunds.TestGatewayFailureAtomicity.test_gateway_is_never_called_when_a_rule_rejects) ... 
  test_gateway_is_never_called_when_a_rule_rejects (test_refunds.TestGatewayFailureAtomicity.test_gateway_is_never_called_when_a_rule_rejects) (order={'id': 'ord_1', 'owner_id': 'cus_1', 'charge_id': 'ch_1', 'paid': 1000, 'refunded': 100, 'status': 'partially_refunded', 'keys': {'key-1': {'refund_id': 're_123', 'amount': 100, 'status': 'partially_refunded'}}}, amount=100, actor={'id': 'aud_1', 'role': 'auditor'}) ... FAIL
test_gateway_receives_the_order_charge_id (test_refunds.TestGatewayFailureAtomicity.test_gateway_receives_the_order_charge_id)
Rule 6: the gateway is charged the order's own charge id, not a fixed one. ... ok
test_distinct_keys_each_charge_once (test_refunds.TestIdempotency.test_distinct_keys_each_charge_once) ... ok
test_replay_ignores_a_different_amount_and_does_not_recharge (test_refunds.TestIdempotency.test_replay_ignores_a_different_amount_and_does_not_recharge) ... ok
test_replay_returns_stored_result_without_second_charge (test_refunds.TestIdempotency.test_replay_returns_stored_result_without_second_charge) ... ok
test_replay_uses_membership_not_truthiness (test_refunds.TestIdempotency.test_replay_uses_membership_not_truthiness)
Rule 1 keys on membership: a stored falsy result must still replay. ... ok
test_replay_wins_over_every_other_rule (test_refunds.TestIdempotency.test_replay_wins_over_every_other_rule)
Rule 1 precedes rules 2-5: bad amount, wrong actor, dead status. ... ok
test_actor_without_a_role_is_denied (test_refunds.TestPermission.test_actor_without_a_role_is_denied)
A missing role must fail closed, never default to a privileged one. ... FAIL
test_admin_and_support_need_not_own_the_order (test_refunds.TestPermission.test_admin_and_support_need_not_own_the_order) ... ok
test_admin_is_allowed (test_refunds.TestPermission.test_admin_is_allowed) ... ok
test_customer_without_matching_id_is_denied (test_refunds.TestPermission.test_customer_without_matching_id_is_denied) ... FAIL
test_other_customer_is_denied (test_refunds.TestPermission.test_other_customer_is_denied) ... FAIL
test_owner_customer_is_allowed (test_refunds.TestPermission.test_owner_customer_is_allowed) ... ok
test_owner_with_non_customer_role_is_denied (test_refunds.TestPermission.test_owner_with_non_customer_role_is_denied)
Rule 3 grants the *customer* who owns the order, not any matching id. ... FAIL
test_permission_is_checked_before_status (test_refunds.TestPermission.test_permission_is_checked_before_status) ... ERROR
test_support_is_allowed (test_refunds.TestPermission.test_support_is_allowed) ... ok
test_unknown_role_is_denied (test_refunds.TestPermission.test_unknown_role_is_denied) ... FAIL
test_amount_above_remaining_is_rejected (test_refunds.TestRefundableCap.test_amount_above_remaining_is_rejected) ... ok
test_amount_equal_to_paid_is_rejected_once_partly_refunded (test_refunds.TestRefundableCap.test_amount_equal_to_paid_is_rejected_once_partly_refunded) ... ok
test_exact_remaining_is_allowed (test_refunds.TestRefundableCap.test_exact_remaining_is_allowed) ... ok
test_full_refund_of_untouched_order_is_allowed (test_refunds.TestRefundableCap.test_full_refund_of_untouched_order_is_allowed) ... ok
test_over_refunded_order_rejects_any_amount (test_refunds.TestRefundableCap.test_over_refunded_order_rejects_any_amount)
A negative remainder must still reject every amount, not skip the cap. ... ok
test_cancelled_order_is_rejected (test_refunds.TestStatus.test_cancelled_order_is_rejected) ... ok
test_paid_order_is_accepted (test_refunds.TestStatus.test_paid_order_is_accepted) ... ok
test_partially_refunded_order_is_accepted (test_refunds.TestStatus.test_partially_refunded_order_is_accepted) ... ok
test_refunded_order_is_rejected_even_with_room_on_the_clock (test_refunds.TestStatus.test_refunded_order_is_rejected_even_with_room_on_the_clock) ... ok
test_unknown_status_is_rejected (test_refunds.TestStatus.test_unknown_status_is_rejected) ... ok
test_full_refund_sets_status_refunded (test_refunds.TestSuccessBookkeeping.test_full_refund_sets_status_refunded)
Rule 7: the terminal transition is exactly `refunded`, and it is stored. ... ok
test_partial_refund_result_and_state (test_refunds.TestSuccessBookkeeping.test_partial_refund_result_and_state) ... ok
test_result_has_exactly_the_specified_fields (test_refunds.TestSuccessBookkeeping.test_result_has_exactly_the_specified_fields) ... ok
test_two_partial_refunds_then_fully_refunded (test_refunds.TestSuccessBookkeeping.test_two_partial_refunds_then_fully_refunded) ... ok
test_untouched_order_fields_are_preserved (test_refunds.TestSuccessBookkeeping.test_untouched_order_fields_are_preserved) ... ok

======================================================================
ERROR: test_permission_is_checked_before_status (test_refunds.TestPermission.test_permission_is_checked_before_status)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/AE-neutral-1/test_refunds.py", line 238, in test_permission_is_checked_before_status
    refund(order, 100, gateway, OTHER_CUSTOMER, "key-1")
    ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot/AE-neutral-1/refunds.py", line 55, in refund
    raise ValueError("order status %r is not refundable" % (order["status"],))
ValueError: order status 'cancelled' is not refundable

======================================================================
FAIL: test_gateway_is_never_called_when_a_rule_rejects (test_refunds.TestGatewayFailureAtomicity.test_gateway_is_never_called_when_a_rule_rejects) (order={'id': 'ord_1', 'owner_id': 'cus_1', 'charge_id': 'ch_1', 'paid': 1000, 'refunded': 100, 'status': 'partially_refunded', 'keys': {'key-1': {'refund_id': 're_123', 'amount': 100, 'status': 'partially_refunded'}}}, amount=100, actor={'id': 'aud_1', 'role': 'auditor'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/AE-neutral-1/test_refunds.py", line 392, in test_gateway_is_never_called_when_a_rule_rejects
    with self.assertRaises((ValueError, PermissionError)):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: (<class 'ValueError'>, <class 'PermissionError'>) not raised

======================================================================
FAIL: test_actor_without_a_role_is_denied (test_refunds.TestPermission.test_actor_without_a_role_is_denied)
A missing role must fail closed, never default to a privileged one.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/AE-neutral-1/test_refunds.py", line 230, in test_actor_without_a_role_is_denied
    self._assert_denied({})
    ~~~~~~~~~~~~~~~~~~~^^^^
  File "/private/tmp/aep-lab/pilot/AE-neutral-1/test_refunds.py", line 193, in _assert_denied
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_customer_without_matching_id_is_denied (test_refunds.TestPermission.test_customer_without_matching_id_is_denied)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/AE-neutral-1/test_refunds.py", line 219, in test_customer_without_matching_id_is_denied
    self._assert_denied({"id": "", "role": "customer"})
    ~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot/AE-neutral-1/test_refunds.py", line 193, in _assert_denied
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_other_customer_is_denied (test_refunds.TestPermission.test_other_customer_is_denied)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/AE-neutral-1/test_refunds.py", line 212, in test_other_customer_is_denied
    self._assert_denied(OTHER_CUSTOMER)
    ~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot/AE-neutral-1/test_refunds.py", line 193, in _assert_denied
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_owner_with_non_customer_role_is_denied (test_refunds.TestPermission.test_owner_with_non_customer_role_is_denied)
Rule 3 grants the *customer* who owns the order, not any matching id.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/AE-neutral-1/test_refunds.py", line 224, in test_owner_with_non_customer_role_is_denied
    self._assert_denied({"id": "cus_1", "role": "auditor"})
    ~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot/AE-neutral-1/test_refunds.py", line 193, in _assert_denied
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_unknown_role_is_denied (test_refunds.TestPermission.test_unknown_role_is_denied)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/AE-neutral-1/test_refunds.py", line 215, in test_unknown_role_is_denied
    self._assert_denied(AUDITOR)
    ~~~~~~~~~~~~~~~~~~~^^^^^^^^^
  File "/private/tmp/aep-lab/pilot/AE-neutral-1/test_refunds.py", line 193, in _assert_denied
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

----------------------------------------------------------------------
Ran 41 tests in 0.002s

FAILED (failures=6, errors=1)
(exit 1)
$ restored /tmp/aep-lab/pilot/AE-neutral-1/refunds.py from backup (byte-identical)
$ cd /tmp/aep-lab/pilot/AE-neutral-1 && python3 -m unittest discover -s . -p 'test*.py' -v   # expect SUCCESS
test_accepts_one (test_refunds.TestAmountValidation.test_accepts_one) ... ok
test_amount_is_checked_before_permission_and_status (test_refunds.TestAmountValidation.test_amount_is_checked_before_permission_and_status) ... ok
test_rejects_bools (test_refunds.TestAmountValidation.test_rejects_bools) ... ok
test_rejects_floats_even_when_whole (test_refunds.TestAmountValidation.test_rejects_floats_even_when_whole) ... ok
test_rejects_non_numeric_amounts (test_refunds.TestAmountValidation.test_rejects_non_numeric_amounts) ... ok
test_rejects_non_positive_ints (test_refunds.TestAmountValidation.test_rejects_non_positive_ints) ... ok
test_failed_refund_does_not_poison_a_retry (test_refunds.TestGatewayFailureAtomicity.test_failed_refund_does_not_poison_a_retry) ... ok
test_failed_refund_leaves_order_completely_unchanged (test_refunds.TestGatewayFailureAtomicity.test_failed_refund_leaves_order_completely_unchanged) ... ok
test_gateway_is_called_exactly_once_per_refund (test_refunds.TestGatewayFailureAtomicity.test_gateway_is_called_exactly_once_per_refund) ... ok
test_gateway_is_never_called_when_a_rule_rejects (test_refunds.TestGatewayFailureAtomicity.test_gateway_is_never_called_when_a_rule_rejects) ... ok
test_gateway_receives_the_order_charge_id (test_refunds.TestGatewayFailureAtomicity.test_gateway_receives_the_order_charge_id)
Rule 6: the gateway is charged the order's own charge id, not a fixed one. ... ok
test_distinct_keys_each_charge_once (test_refunds.TestIdempotency.test_distinct_keys_each_charge_once) ... ok
test_replay_ignores_a_different_amount_and_does_not_recharge (test_refunds.TestIdempotency.test_replay_ignores_a_different_amount_and_does_not_recharge) ... ok
test_replay_returns_stored_result_without_second_charge (test_refunds.TestIdempotency.test_replay_returns_stored_result_without_second_charge) ... ok
test_replay_uses_membership_not_truthiness (test_refunds.TestIdempotency.test_replay_uses_membership_not_truthiness)
Rule 1 keys on membership: a stored falsy result must still replay. ... ok
test_replay_wins_over_every_other_rule (test_refunds.TestIdempotency.test_replay_wins_over_every_other_rule)
Rule 1 precedes rules 2-5: bad amount, wrong actor, dead status. ... ok
test_actor_without_a_role_is_denied (test_refunds.TestPermission.test_actor_without_a_role_is_denied)
A missing role must fail closed, never default to a privileged one. ... ok
test_admin_and_support_need_not_own_the_order (test_refunds.TestPermission.test_admin_and_support_need_not_own_the_order) ... ok
test_admin_is_allowed (test_refunds.TestPermission.test_admin_is_allowed) ... ok
test_customer_without_matching_id_is_denied (test_refunds.TestPermission.test_customer_without_matching_id_is_denied) ... ok
test_other_customer_is_denied (test_refunds.TestPermission.test_other_customer_is_denied) ... ok
test_owner_customer_is_allowed (test_refunds.TestPermission.test_owner_customer_is_allowed) ... ok
test_owner_with_non_customer_role_is_denied (test_refunds.TestPermission.test_owner_with_non_customer_role_is_denied)
Rule 3 grants the *customer* who owns the order, not any matching id. ... ok
test_permission_is_checked_before_status (test_refunds.TestPermission.test_permission_is_checked_before_status) ... ok
test_support_is_allowed (test_refunds.TestPermission.test_support_is_allowed) ... ok
test_unknown_role_is_denied (test_refunds.TestPermission.test_unknown_role_is_denied) ... ok
test_amount_above_remaining_is_rejected (test_refunds.TestRefundableCap.test_amount_above_remaining_is_rejected) ... ok
test_amount_equal_to_paid_is_rejected_once_partly_refunded (test_refunds.TestRefundableCap.test_amount_equal_to_paid_is_rejected_once_partly_refunded) ... ok
test_exact_remaining_is_allowed (test_refunds.TestRefundableCap.test_exact_remaining_is_allowed) ... ok
test_full_refund_of_untouched_order_is_allowed (test_refunds.TestRefundableCap.test_full_refund_of_untouched_order_is_allowed) ... ok
test_over_refunded_order_rejects_any_amount (test_refunds.TestRefundableCap.test_over_refunded_order_rejects_any_amount)
A negative remainder must still reject every amount, not skip the cap. ... ok
test_cancelled_order_is_rejected (test_refunds.TestStatus.test_cancelled_order_is_rejected) ... ok
test_paid_order_is_accepted (test_refunds.TestStatus.test_paid_order_is_accepted) ... ok
test_partially_refunded_order_is_accepted (test_refunds.TestStatus.test_partially_refunded_order_is_accepted) ... ok
test_refunded_order_is_rejected_even_with_room_on_the_clock (test_refunds.TestStatus.test_refunded_order_is_rejected_even_with_room_on_the_clock) ... ok
test_unknown_status_is_rejected (test_refunds.TestStatus.test_unknown_status_is_rejected) ... ok
test_full_refund_sets_status_refunded (test_refunds.TestSuccessBookkeeping.test_full_refund_sets_status_refunded)
Rule 7: the terminal transition is exactly `refunded`, and it is stored. ... ok
test_partial_refund_result_and_state (test_refunds.TestSuccessBookkeeping.test_partial_refund_result_and_state) ... ok
test_result_has_exactly_the_specified_fields (test_refunds.TestSuccessBookkeeping.test_result_has_exactly_the_specified_fields) ... ok
test_two_partial_refunds_then_fully_refunded (test_refunds.TestSuccessBookkeeping.test_two_partial_refunds_then_fully_refunded) ... ok
test_untouched_order_fields_are_preserved (test_refunds.TestSuccessBookkeeping.test_untouched_order_fields_are_preserved) ... ok

----------------------------------------------------------------------
Ran 41 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```


## 6.5 Negative control: rule 3 — owner must be a customer

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/AE-neutral-1/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/AE-neutral-1/negcontrol/break_owner_role.py" --test-cmd "cd /tmp/aep-lab/pilot/AE-neutral-1 && python3 -m unittest discover -s . -p 'test*.py' -v" --expect "FAIL: test_owner_with_non_customer_role_is_denied" --timeout 20
$ backed up /tmp/aep-lab/pilot/AE-neutral-1/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-4g267fd1/refunds.py
$ python3 /tmp/aep-lab/pilot/AE-neutral-1/negcontrol/break_owner_role.py
break_owner_role: owner may refund regardless of role
$ cd /tmp/aep-lab/pilot/AE-neutral-1 && python3 -m unittest discover -s . -p 'test*.py' -v   # expect FAILURE matching /FAIL: test_owner_with_non_customer_role_is_denied/
test_accepts_one (test_refunds.TestAmountValidation.test_accepts_one) ... ok
test_amount_is_checked_before_permission_and_status (test_refunds.TestAmountValidation.test_amount_is_checked_before_permission_and_status) ... ok
test_rejects_bools (test_refunds.TestAmountValidation.test_rejects_bools) ... ok
test_rejects_floats_even_when_whole (test_refunds.TestAmountValidation.test_rejects_floats_even_when_whole) ... ok
test_rejects_non_numeric_amounts (test_refunds.TestAmountValidation.test_rejects_non_numeric_amounts) ... ok
test_rejects_non_positive_ints (test_refunds.TestAmountValidation.test_rejects_non_positive_ints) ... ok
test_failed_refund_does_not_poison_a_retry (test_refunds.TestGatewayFailureAtomicity.test_failed_refund_does_not_poison_a_retry) ... ok
test_failed_refund_leaves_order_completely_unchanged (test_refunds.TestGatewayFailureAtomicity.test_failed_refund_leaves_order_completely_unchanged) ... ok
test_gateway_is_called_exactly_once_per_refund (test_refunds.TestGatewayFailureAtomicity.test_gateway_is_called_exactly_once_per_refund) ... ok
test_gateway_is_never_called_when_a_rule_rejects (test_refunds.TestGatewayFailureAtomicity.test_gateway_is_never_called_when_a_rule_rejects) ... ok
test_gateway_receives_the_order_charge_id (test_refunds.TestGatewayFailureAtomicity.test_gateway_receives_the_order_charge_id)
Rule 6: the gateway is charged the order's own charge id, not a fixed one. ... ok
test_distinct_keys_each_charge_once (test_refunds.TestIdempotency.test_distinct_keys_each_charge_once) ... ok
test_replay_ignores_a_different_amount_and_does_not_recharge (test_refunds.TestIdempotency.test_replay_ignores_a_different_amount_and_does_not_recharge) ... ok
test_replay_returns_stored_result_without_second_charge (test_refunds.TestIdempotency.test_replay_returns_stored_result_without_second_charge) ... ok
test_replay_uses_membership_not_truthiness (test_refunds.TestIdempotency.test_replay_uses_membership_not_truthiness)
Rule 1 keys on membership: a stored falsy result must still replay. ... ok
test_replay_wins_over_every_other_rule (test_refunds.TestIdempotency.test_replay_wins_over_every_other_rule)
Rule 1 precedes rules 2-5: bad amount, wrong actor, dead status. ... ok
test_actor_without_a_role_is_denied (test_refunds.TestPermission.test_actor_without_a_role_is_denied)
A missing role must fail closed, never default to a privileged one. ... FAIL
test_admin_and_support_need_not_own_the_order (test_refunds.TestPermission.test_admin_and_support_need_not_own_the_order) ... ok
test_admin_is_allowed (test_refunds.TestPermission.test_admin_is_allowed) ... ok
test_customer_without_matching_id_is_denied (test_refunds.TestPermission.test_customer_without_matching_id_is_denied) ... ok
test_other_customer_is_denied (test_refunds.TestPermission.test_other_customer_is_denied) ... ok
test_owner_customer_is_allowed (test_refunds.TestPermission.test_owner_customer_is_allowed) ... ok
test_owner_with_non_customer_role_is_denied (test_refunds.TestPermission.test_owner_with_non_customer_role_is_denied)
Rule 3 grants the *customer* who owns the order, not any matching id. ... FAIL
test_permission_is_checked_before_status (test_refunds.TestPermission.test_permission_is_checked_before_status) ... ok
test_support_is_allowed (test_refunds.TestPermission.test_support_is_allowed) ... ok
test_unknown_role_is_denied (test_refunds.TestPermission.test_unknown_role_is_denied) ... ok
test_amount_above_remaining_is_rejected (test_refunds.TestRefundableCap.test_amount_above_remaining_is_rejected) ... ok
test_amount_equal_to_paid_is_rejected_once_partly_refunded (test_refunds.TestRefundableCap.test_amount_equal_to_paid_is_rejected_once_partly_refunded) ... ok
test_exact_remaining_is_allowed (test_refunds.TestRefundableCap.test_exact_remaining_is_allowed) ... ok
test_full_refund_of_untouched_order_is_allowed (test_refunds.TestRefundableCap.test_full_refund_of_untouched_order_is_allowed) ... ok
test_over_refunded_order_rejects_any_amount (test_refunds.TestRefundableCap.test_over_refunded_order_rejects_any_amount)
A negative remainder must still reject every amount, not skip the cap. ... ok
test_cancelled_order_is_rejected (test_refunds.TestStatus.test_cancelled_order_is_rejected) ... ok
test_paid_order_is_accepted (test_refunds.TestStatus.test_paid_order_is_accepted) ... ok
test_partially_refunded_order_is_accepted (test_refunds.TestStatus.test_partially_refunded_order_is_accepted) ... ok
test_refunded_order_is_rejected_even_with_room_on_the_clock (test_refunds.TestStatus.test_refunded_order_is_rejected_even_with_room_on_the_clock) ... ok
test_unknown_status_is_rejected (test_refunds.TestStatus.test_unknown_status_is_rejected) ... ok
test_full_refund_sets_status_refunded (test_refunds.TestSuccessBookkeeping.test_full_refund_sets_status_refunded)
Rule 7: the terminal transition is exactly `refunded`, and it is stored. ... ok
test_partial_refund_result_and_state (test_refunds.TestSuccessBookkeeping.test_partial_refund_result_and_state) ... ok
test_result_has_exactly_the_specified_fields (test_refunds.TestSuccessBookkeeping.test_result_has_exactly_the_specified_fields) ... ok
test_two_partial_refunds_then_fully_refunded (test_refunds.TestSuccessBookkeeping.test_two_partial_refunds_then_fully_refunded) ... ok
test_untouched_order_fields_are_preserved (test_refunds.TestSuccessBookkeeping.test_untouched_order_fields_are_preserved) ... ok

======================================================================
FAIL: test_actor_without_a_role_is_denied (test_refunds.TestPermission.test_actor_without_a_role_is_denied)
A missing role must fail closed, never default to a privileged one.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/AE-neutral-1/test_refunds.py", line 231, in test_actor_without_a_role_is_denied
    self._assert_denied({"id": "cus_1"})
    ~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot/AE-neutral-1/test_refunds.py", line 193, in _assert_denied
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_owner_with_non_customer_role_is_denied (test_refunds.TestPermission.test_owner_with_non_customer_role_is_denied)
Rule 3 grants the *customer* who owns the order, not any matching id.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/AE-neutral-1/test_refunds.py", line 224, in test_owner_with_non_customer_role_is_denied
    self._assert_denied({"id": "cus_1", "role": "auditor"})
    ~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot/AE-neutral-1/test_refunds.py", line 193, in _assert_denied
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

----------------------------------------------------------------------
Ran 41 tests in 0.002s

FAILED (failures=2)
(exit 1)
$ restored /tmp/aep-lab/pilot/AE-neutral-1/refunds.py from backup (byte-identical)
$ cd /tmp/aep-lab/pilot/AE-neutral-1 && python3 -m unittest discover -s . -p 'test*.py' -v   # expect SUCCESS
test_accepts_one (test_refunds.TestAmountValidation.test_accepts_one) ... ok
test_amount_is_checked_before_permission_and_status (test_refunds.TestAmountValidation.test_amount_is_checked_before_permission_and_status) ... ok
test_rejects_bools (test_refunds.TestAmountValidation.test_rejects_bools) ... ok
test_rejects_floats_even_when_whole (test_refunds.TestAmountValidation.test_rejects_floats_even_when_whole) ... ok
test_rejects_non_numeric_amounts (test_refunds.TestAmountValidation.test_rejects_non_numeric_amounts) ... ok
test_rejects_non_positive_ints (test_refunds.TestAmountValidation.test_rejects_non_positive_ints) ... ok
test_failed_refund_does_not_poison_a_retry (test_refunds.TestGatewayFailureAtomicity.test_failed_refund_does_not_poison_a_retry) ... ok
test_failed_refund_leaves_order_completely_unchanged (test_refunds.TestGatewayFailureAtomicity.test_failed_refund_leaves_order_completely_unchanged) ... ok
test_gateway_is_called_exactly_once_per_refund (test_refunds.TestGatewayFailureAtomicity.test_gateway_is_called_exactly_once_per_refund) ... ok
test_gateway_is_never_called_when_a_rule_rejects (test_refunds.TestGatewayFailureAtomicity.test_gateway_is_never_called_when_a_rule_rejects) ... ok
test_gateway_receives_the_order_charge_id (test_refunds.TestGatewayFailureAtomicity.test_gateway_receives_the_order_charge_id)
Rule 6: the gateway is charged the order's own charge id, not a fixed one. ... ok
test_distinct_keys_each_charge_once (test_refunds.TestIdempotency.test_distinct_keys_each_charge_once) ... ok
test_replay_ignores_a_different_amount_and_does_not_recharge (test_refunds.TestIdempotency.test_replay_ignores_a_different_amount_and_does_not_recharge) ... ok
test_replay_returns_stored_result_without_second_charge (test_refunds.TestIdempotency.test_replay_returns_stored_result_without_second_charge) ... ok
test_replay_uses_membership_not_truthiness (test_refunds.TestIdempotency.test_replay_uses_membership_not_truthiness)
Rule 1 keys on membership: a stored falsy result must still replay. ... ok
test_replay_wins_over_every_other_rule (test_refunds.TestIdempotency.test_replay_wins_over_every_other_rule)
Rule 1 precedes rules 2-5: bad amount, wrong actor, dead status. ... ok
test_actor_without_a_role_is_denied (test_refunds.TestPermission.test_actor_without_a_role_is_denied)
A missing role must fail closed, never default to a privileged one. ... ok
test_admin_and_support_need_not_own_the_order (test_refunds.TestPermission.test_admin_and_support_need_not_own_the_order) ... ok
test_admin_is_allowed (test_refunds.TestPermission.test_admin_is_allowed) ... ok
test_customer_without_matching_id_is_denied (test_refunds.TestPermission.test_customer_without_matching_id_is_denied) ... ok
test_other_customer_is_denied (test_refunds.TestPermission.test_other_customer_is_denied) ... ok
test_owner_customer_is_allowed (test_refunds.TestPermission.test_owner_customer_is_allowed) ... ok
test_owner_with_non_customer_role_is_denied (test_refunds.TestPermission.test_owner_with_non_customer_role_is_denied)
Rule 3 grants the *customer* who owns the order, not any matching id. ... ok
test_permission_is_checked_before_status (test_refunds.TestPermission.test_permission_is_checked_before_status) ... ok
test_support_is_allowed (test_refunds.TestPermission.test_support_is_allowed) ... ok
test_unknown_role_is_denied (test_refunds.TestPermission.test_unknown_role_is_denied) ... ok
test_amount_above_remaining_is_rejected (test_refunds.TestRefundableCap.test_amount_above_remaining_is_rejected) ... ok
test_amount_equal_to_paid_is_rejected_once_partly_refunded (test_refunds.TestRefundableCap.test_amount_equal_to_paid_is_rejected_once_partly_refunded) ... ok
test_exact_remaining_is_allowed (test_refunds.TestRefundableCap.test_exact_remaining_is_allowed) ... ok
test_full_refund_of_untouched_order_is_allowed (test_refunds.TestRefundableCap.test_full_refund_of_untouched_order_is_allowed) ... ok
test_over_refunded_order_rejects_any_amount (test_refunds.TestRefundableCap.test_over_refunded_order_rejects_any_amount)
A negative remainder must still reject every amount, not skip the cap. ... ok
test_cancelled_order_is_rejected (test_refunds.TestStatus.test_cancelled_order_is_rejected) ... ok
test_paid_order_is_accepted (test_refunds.TestStatus.test_paid_order_is_accepted) ... ok
test_partially_refunded_order_is_accepted (test_refunds.TestStatus.test_partially_refunded_order_is_accepted) ... ok
test_refunded_order_is_rejected_even_with_room_on_the_clock (test_refunds.TestStatus.test_refunded_order_is_rejected_even_with_room_on_the_clock) ... ok
test_unknown_status_is_rejected (test_refunds.TestStatus.test_unknown_status_is_rejected) ... ok
test_full_refund_sets_status_refunded (test_refunds.TestSuccessBookkeeping.test_full_refund_sets_status_refunded)
Rule 7: the terminal transition is exactly `refunded`, and it is stored. ... ok
test_partial_refund_result_and_state (test_refunds.TestSuccessBookkeeping.test_partial_refund_result_and_state) ... ok
test_result_has_exactly_the_specified_fields (test_refunds.TestSuccessBookkeeping.test_result_has_exactly_the_specified_fields) ... ok
test_two_partial_refunds_then_fully_refunded (test_refunds.TestSuccessBookkeeping.test_two_partial_refunds_then_fully_refunded) ... ok
test_untouched_order_fields_are_preserved (test_refunds.TestSuccessBookkeeping.test_untouched_order_fields_are_preserved) ... ok

----------------------------------------------------------------------
Ran 41 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```


## 6.6 Negative control: rule 3 — missing role fails closed

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/AE-neutral-1/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/AE-neutral-1/negcontrol/break_actor_no_role.py" --test-cmd "cd /tmp/aep-lab/pilot/AE-neutral-1 && python3 -m unittest discover -s . -p 'test*.py' -v" --expect "FAIL: test_actor_without_a_role_is_denied" --timeout 20
$ backed up /tmp/aep-lab/pilot/AE-neutral-1/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-7gxeppik/refunds.py
$ python3 /tmp/aep-lab/pilot/AE-neutral-1/negcontrol/break_actor_no_role.py
break_actor_no_role: missing role defaults to admin
$ cd /tmp/aep-lab/pilot/AE-neutral-1 && python3 -m unittest discover -s . -p 'test*.py' -v   # expect FAILURE matching /FAIL: test_actor_without_a_role_is_denied/
test_accepts_one (test_refunds.TestAmountValidation.test_accepts_one) ... ok
test_amount_is_checked_before_permission_and_status (test_refunds.TestAmountValidation.test_amount_is_checked_before_permission_and_status) ... ok
test_rejects_bools (test_refunds.TestAmountValidation.test_rejects_bools) ... ok
test_rejects_floats_even_when_whole (test_refunds.TestAmountValidation.test_rejects_floats_even_when_whole) ... ok
test_rejects_non_numeric_amounts (test_refunds.TestAmountValidation.test_rejects_non_numeric_amounts) ... ok
test_rejects_non_positive_ints (test_refunds.TestAmountValidation.test_rejects_non_positive_ints) ... ok
test_failed_refund_does_not_poison_a_retry (test_refunds.TestGatewayFailureAtomicity.test_failed_refund_does_not_poison_a_retry) ... ok
test_failed_refund_leaves_order_completely_unchanged (test_refunds.TestGatewayFailureAtomicity.test_failed_refund_leaves_order_completely_unchanged) ... ok
test_gateway_is_called_exactly_once_per_refund (test_refunds.TestGatewayFailureAtomicity.test_gateway_is_called_exactly_once_per_refund) ... ok
test_gateway_is_never_called_when_a_rule_rejects (test_refunds.TestGatewayFailureAtomicity.test_gateway_is_never_called_when_a_rule_rejects) ... ok
test_gateway_receives_the_order_charge_id (test_refunds.TestGatewayFailureAtomicity.test_gateway_receives_the_order_charge_id)
Rule 6: the gateway is charged the order's own charge id, not a fixed one. ... ok
test_distinct_keys_each_charge_once (test_refunds.TestIdempotency.test_distinct_keys_each_charge_once) ... ok
test_replay_ignores_a_different_amount_and_does_not_recharge (test_refunds.TestIdempotency.test_replay_ignores_a_different_amount_and_does_not_recharge) ... ok
test_replay_returns_stored_result_without_second_charge (test_refunds.TestIdempotency.test_replay_returns_stored_result_without_second_charge) ... ok
test_replay_uses_membership_not_truthiness (test_refunds.TestIdempotency.test_replay_uses_membership_not_truthiness)
Rule 1 keys on membership: a stored falsy result must still replay. ... ok
test_replay_wins_over_every_other_rule (test_refunds.TestIdempotency.test_replay_wins_over_every_other_rule)
Rule 1 precedes rules 2-5: bad amount, wrong actor, dead status. ... ok
test_actor_without_a_role_is_denied (test_refunds.TestPermission.test_actor_without_a_role_is_denied)
A missing role must fail closed, never default to a privileged one. ... FAIL
test_admin_and_support_need_not_own_the_order (test_refunds.TestPermission.test_admin_and_support_need_not_own_the_order) ... ok
test_admin_is_allowed (test_refunds.TestPermission.test_admin_is_allowed) ... ok
test_customer_without_matching_id_is_denied (test_refunds.TestPermission.test_customer_without_matching_id_is_denied) ... ok
test_other_customer_is_denied (test_refunds.TestPermission.test_other_customer_is_denied) ... ok
test_owner_customer_is_allowed (test_refunds.TestPermission.test_owner_customer_is_allowed) ... ok
test_owner_with_non_customer_role_is_denied (test_refunds.TestPermission.test_owner_with_non_customer_role_is_denied)
Rule 3 grants the *customer* who owns the order, not any matching id. ... ok
test_permission_is_checked_before_status (test_refunds.TestPermission.test_permission_is_checked_before_status) ... ok
test_support_is_allowed (test_refunds.TestPermission.test_support_is_allowed) ... ok
test_unknown_role_is_denied (test_refunds.TestPermission.test_unknown_role_is_denied) ... ok
test_amount_above_remaining_is_rejected (test_refunds.TestRefundableCap.test_amount_above_remaining_is_rejected) ... ok
test_amount_equal_to_paid_is_rejected_once_partly_refunded (test_refunds.TestRefundableCap.test_amount_equal_to_paid_is_rejected_once_partly_refunded) ... ok
test_exact_remaining_is_allowed (test_refunds.TestRefundableCap.test_exact_remaining_is_allowed) ... ok
test_full_refund_of_untouched_order_is_allowed (test_refunds.TestRefundableCap.test_full_refund_of_untouched_order_is_allowed) ... ok
test_over_refunded_order_rejects_any_amount (test_refunds.TestRefundableCap.test_over_refunded_order_rejects_any_amount)
A negative remainder must still reject every amount, not skip the cap. ... ok
test_cancelled_order_is_rejected (test_refunds.TestStatus.test_cancelled_order_is_rejected) ... ok
test_paid_order_is_accepted (test_refunds.TestStatus.test_paid_order_is_accepted) ... ok
test_partially_refunded_order_is_accepted (test_refunds.TestStatus.test_partially_refunded_order_is_accepted) ... ok
test_refunded_order_is_rejected_even_with_room_on_the_clock (test_refunds.TestStatus.test_refunded_order_is_rejected_even_with_room_on_the_clock) ... ok
test_unknown_status_is_rejected (test_refunds.TestStatus.test_unknown_status_is_rejected) ... ok
test_full_refund_sets_status_refunded (test_refunds.TestSuccessBookkeeping.test_full_refund_sets_status_refunded)
Rule 7: the terminal transition is exactly `refunded`, and it is stored. ... ok
test_partial_refund_result_and_state (test_refunds.TestSuccessBookkeeping.test_partial_refund_result_and_state) ... ok
test_result_has_exactly_the_specified_fields (test_refunds.TestSuccessBookkeeping.test_result_has_exactly_the_specified_fields) ... ok
test_two_partial_refunds_then_fully_refunded (test_refunds.TestSuccessBookkeeping.test_two_partial_refunds_then_fully_refunded) ... ok
test_untouched_order_fields_are_preserved (test_refunds.TestSuccessBookkeeping.test_untouched_order_fields_are_preserved) ... ok

======================================================================
FAIL: test_actor_without_a_role_is_denied (test_refunds.TestPermission.test_actor_without_a_role_is_denied)
A missing role must fail closed, never default to a privileged one.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/AE-neutral-1/test_refunds.py", line 230, in test_actor_without_a_role_is_denied
    self._assert_denied({})
    ~~~~~~~~~~~~~~~~~~~^^^^
  File "/private/tmp/aep-lab/pilot/AE-neutral-1/test_refunds.py", line 193, in _assert_denied
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

----------------------------------------------------------------------
Ran 41 tests in 0.001s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot/AE-neutral-1/refunds.py from backup (byte-identical)
$ cd /tmp/aep-lab/pilot/AE-neutral-1 && python3 -m unittest discover -s . -p 'test*.py' -v   # expect SUCCESS
test_accepts_one (test_refunds.TestAmountValidation.test_accepts_one) ... ok
test_amount_is_checked_before_permission_and_status (test_refunds.TestAmountValidation.test_amount_is_checked_before_permission_and_status) ... ok
test_rejects_bools (test_refunds.TestAmountValidation.test_rejects_bools) ... ok
test_rejects_floats_even_when_whole (test_refunds.TestAmountValidation.test_rejects_floats_even_when_whole) ... ok
test_rejects_non_numeric_amounts (test_refunds.TestAmountValidation.test_rejects_non_numeric_amounts) ... ok
test_rejects_non_positive_ints (test_refunds.TestAmountValidation.test_rejects_non_positive_ints) ... ok
test_failed_refund_does_not_poison_a_retry (test_refunds.TestGatewayFailureAtomicity.test_failed_refund_does_not_poison_a_retry) ... ok
test_failed_refund_leaves_order_completely_unchanged (test_refunds.TestGatewayFailureAtomicity.test_failed_refund_leaves_order_completely_unchanged) ... ok
test_gateway_is_called_exactly_once_per_refund (test_refunds.TestGatewayFailureAtomicity.test_gateway_is_called_exactly_once_per_refund) ... ok
test_gateway_is_never_called_when_a_rule_rejects (test_refunds.TestGatewayFailureAtomicity.test_gateway_is_never_called_when_a_rule_rejects) ... ok
test_gateway_receives_the_order_charge_id (test_refunds.TestGatewayFailureAtomicity.test_gateway_receives_the_order_charge_id)
Rule 6: the gateway is charged the order's own charge id, not a fixed one. ... ok
test_distinct_keys_each_charge_once (test_refunds.TestIdempotency.test_distinct_keys_each_charge_once) ... ok
test_replay_ignores_a_different_amount_and_does_not_recharge (test_refunds.TestIdempotency.test_replay_ignores_a_different_amount_and_does_not_recharge) ... ok
test_replay_returns_stored_result_without_second_charge (test_refunds.TestIdempotency.test_replay_returns_stored_result_without_second_charge) ... ok
test_replay_uses_membership_not_truthiness (test_refunds.TestIdempotency.test_replay_uses_membership_not_truthiness)
Rule 1 keys on membership: a stored falsy result must still replay. ... ok
test_replay_wins_over_every_other_rule (test_refunds.TestIdempotency.test_replay_wins_over_every_other_rule)
Rule 1 precedes rules 2-5: bad amount, wrong actor, dead status. ... ok
test_actor_without_a_role_is_denied (test_refunds.TestPermission.test_actor_without_a_role_is_denied)
A missing role must fail closed, never default to a privileged one. ... ok
test_admin_and_support_need_not_own_the_order (test_refunds.TestPermission.test_admin_and_support_need_not_own_the_order) ... ok
test_admin_is_allowed (test_refunds.TestPermission.test_admin_is_allowed) ... ok
test_customer_without_matching_id_is_denied (test_refunds.TestPermission.test_customer_without_matching_id_is_denied) ... ok
test_other_customer_is_denied (test_refunds.TestPermission.test_other_customer_is_denied) ... ok
test_owner_customer_is_allowed (test_refunds.TestPermission.test_owner_customer_is_allowed) ... ok
test_owner_with_non_customer_role_is_denied (test_refunds.TestPermission.test_owner_with_non_customer_role_is_denied)
Rule 3 grants the *customer* who owns the order, not any matching id. ... ok
test_permission_is_checked_before_status (test_refunds.TestPermission.test_permission_is_checked_before_status) ... ok
test_support_is_allowed (test_refunds.TestPermission.test_support_is_allowed) ... ok
test_unknown_role_is_denied (test_refunds.TestPermission.test_unknown_role_is_denied) ... ok
test_amount_above_remaining_is_rejected (test_refunds.TestRefundableCap.test_amount_above_remaining_is_rejected) ... ok
test_amount_equal_to_paid_is_rejected_once_partly_refunded (test_refunds.TestRefundableCap.test_amount_equal_to_paid_is_rejected_once_partly_refunded) ... ok
test_exact_remaining_is_allowed (test_refunds.TestRefundableCap.test_exact_remaining_is_allowed) ... ok
test_full_refund_of_untouched_order_is_allowed (test_refunds.TestRefundableCap.test_full_refund_of_untouched_order_is_allowed) ... ok
test_over_refunded_order_rejects_any_amount (test_refunds.TestRefundableCap.test_over_refunded_order_rejects_any_amount)
A negative remainder must still reject every amount, not skip the cap. ... ok
test_cancelled_order_is_rejected (test_refunds.TestStatus.test_cancelled_order_is_rejected) ... ok
test_paid_order_is_accepted (test_refunds.TestStatus.test_paid_order_is_accepted) ... ok
test_partially_refunded_order_is_accepted (test_refunds.TestStatus.test_partially_refunded_order_is_accepted) ... ok
test_refunded_order_is_rejected_even_with_room_on_the_clock (test_refunds.TestStatus.test_refunded_order_is_rejected_even_with_room_on_the_clock) ... ok
test_unknown_status_is_rejected (test_refunds.TestStatus.test_unknown_status_is_rejected) ... ok
test_full_refund_sets_status_refunded (test_refunds.TestSuccessBookkeeping.test_full_refund_sets_status_refunded)
Rule 7: the terminal transition is exactly `refunded`, and it is stored. ... ok
test_partial_refund_result_and_state (test_refunds.TestSuccessBookkeeping.test_partial_refund_result_and_state) ... ok
test_result_has_exactly_the_specified_fields (test_refunds.TestSuccessBookkeeping.test_result_has_exactly_the_specified_fields) ... ok
test_two_partial_refunds_then_fully_refunded (test_refunds.TestSuccessBookkeeping.test_two_partial_refunds_then_fully_refunded) ... ok
test_untouched_order_fields_are_preserved (test_refunds.TestSuccessBookkeeping.test_untouched_order_fields_are_preserved) ... ok

----------------------------------------------------------------------
Ran 41 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```


## 6.7 Negative control: rule 4 — refundable status

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/AE-neutral-1/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/AE-neutral-1/negcontrol/break_status.py" --test-cmd "cd /tmp/aep-lab/pilot/AE-neutral-1 && python3 -m unittest discover -s . -p 'test*.py' -v" --expect "FAIL: test_cancelled_order_is_rejected" --timeout 20
$ backed up /tmp/aep-lab/pilot/AE-neutral-1/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-66fkm6qj/refunds.py
$ python3 /tmp/aep-lab/pilot/AE-neutral-1/negcontrol/break_status.py
break_status: refundable-status check disabled
$ cd /tmp/aep-lab/pilot/AE-neutral-1 && python3 -m unittest discover -s . -p 'test*.py' -v   # expect FAILURE matching /FAIL: test_cancelled_order_is_rejected/
test_accepts_one (test_refunds.TestAmountValidation.test_accepts_one) ... ok
test_amount_is_checked_before_permission_and_status (test_refunds.TestAmountValidation.test_amount_is_checked_before_permission_and_status) ... ok
test_rejects_bools (test_refunds.TestAmountValidation.test_rejects_bools) ... ok
test_rejects_floats_even_when_whole (test_refunds.TestAmountValidation.test_rejects_floats_even_when_whole) ... ok
test_rejects_non_numeric_amounts (test_refunds.TestAmountValidation.test_rejects_non_numeric_amounts) ... ok
test_rejects_non_positive_ints (test_refunds.TestAmountValidation.test_rejects_non_positive_ints) ... ok
test_failed_refund_does_not_poison_a_retry (test_refunds.TestGatewayFailureAtomicity.test_failed_refund_does_not_poison_a_retry) ... ok
test_failed_refund_leaves_order_completely_unchanged (test_refunds.TestGatewayFailureAtomicity.test_failed_refund_leaves_order_completely_unchanged) ... ok
test_gateway_is_called_exactly_once_per_refund (test_refunds.TestGatewayFailureAtomicity.test_gateway_is_called_exactly_once_per_refund) ... ok
test_gateway_is_never_called_when_a_rule_rejects (test_refunds.TestGatewayFailureAtomicity.test_gateway_is_never_called_when_a_rule_rejects) ... 
  test_gateway_is_never_called_when_a_rule_rejects (test_refunds.TestGatewayFailureAtomicity.test_gateway_is_never_called_when_a_rule_rejects) (order={'id': 'ord_1', 'owner_id': 'cus_1', 'charge_id': 'ch_1', 'paid': 1000, 'refunded': 100, 'status': 'partially_refunded', 'keys': {'key-1': {'refund_id': 're_123', 'amount': 100, 'status': 'partially_refunded'}}}, amount=100, actor={'id': 'cus_1', 'role': 'customer'}) ... FAIL
test_gateway_receives_the_order_charge_id (test_refunds.TestGatewayFailureAtomicity.test_gateway_receives_the_order_charge_id)
Rule 6: the gateway is charged the order's own charge id, not a fixed one. ... ok
test_distinct_keys_each_charge_once (test_refunds.TestIdempotency.test_distinct_keys_each_charge_once) ... ok
test_replay_ignores_a_different_amount_and_does_not_recharge (test_refunds.TestIdempotency.test_replay_ignores_a_different_amount_and_does_not_recharge) ... ok
test_replay_returns_stored_result_without_second_charge (test_refunds.TestIdempotency.test_replay_returns_stored_result_without_second_charge) ... ok
test_replay_uses_membership_not_truthiness (test_refunds.TestIdempotency.test_replay_uses_membership_not_truthiness)
Rule 1 keys on membership: a stored falsy result must still replay. ... ok
test_replay_wins_over_every_other_rule (test_refunds.TestIdempotency.test_replay_wins_over_every_other_rule)
Rule 1 precedes rules 2-5: bad amount, wrong actor, dead status. ... ok
test_actor_without_a_role_is_denied (test_refunds.TestPermission.test_actor_without_a_role_is_denied)
A missing role must fail closed, never default to a privileged one. ... ok
test_admin_and_support_need_not_own_the_order (test_refunds.TestPermission.test_admin_and_support_need_not_own_the_order) ... ok
test_admin_is_allowed (test_refunds.TestPermission.test_admin_is_allowed) ... ok
test_customer_without_matching_id_is_denied (test_refunds.TestPermission.test_customer_without_matching_id_is_denied) ... ok
test_other_customer_is_denied (test_refunds.TestPermission.test_other_customer_is_denied) ... ok
test_owner_customer_is_allowed (test_refunds.TestPermission.test_owner_customer_is_allowed) ... ok
test_owner_with_non_customer_role_is_denied (test_refunds.TestPermission.test_owner_with_non_customer_role_is_denied)
Rule 3 grants the *customer* who owns the order, not any matching id. ... ok
test_permission_is_checked_before_status (test_refunds.TestPermission.test_permission_is_checked_before_status) ... ok
test_support_is_allowed (test_refunds.TestPermission.test_support_is_allowed) ... ok
test_unknown_role_is_denied (test_refunds.TestPermission.test_unknown_role_is_denied) ... ok
test_amount_above_remaining_is_rejected (test_refunds.TestRefundableCap.test_amount_above_remaining_is_rejected) ... ok
test_amount_equal_to_paid_is_rejected_once_partly_refunded (test_refunds.TestRefundableCap.test_amount_equal_to_paid_is_rejected_once_partly_refunded) ... ok
test_exact_remaining_is_allowed (test_refunds.TestRefundableCap.test_exact_remaining_is_allowed) ... ok
test_full_refund_of_untouched_order_is_allowed (test_refunds.TestRefundableCap.test_full_refund_of_untouched_order_is_allowed) ... ok
test_over_refunded_order_rejects_any_amount (test_refunds.TestRefundableCap.test_over_refunded_order_rejects_any_amount)
A negative remainder must still reject every amount, not skip the cap. ... ok
test_cancelled_order_is_rejected (test_refunds.TestStatus.test_cancelled_order_is_rejected) ... FAIL
test_paid_order_is_accepted (test_refunds.TestStatus.test_paid_order_is_accepted) ... ok
test_partially_refunded_order_is_accepted (test_refunds.TestStatus.test_partially_refunded_order_is_accepted) ... ok
test_refunded_order_is_rejected_even_with_room_on_the_clock (test_refunds.TestStatus.test_refunded_order_is_rejected_even_with_room_on_the_clock) ... FAIL
test_unknown_status_is_rejected (test_refunds.TestStatus.test_unknown_status_is_rejected) ... 
  test_unknown_status_is_rejected (test_refunds.TestStatus.test_unknown_status_is_rejected) (status='pending') ... FAIL
  test_unknown_status_is_rejected (test_refunds.TestStatus.test_unknown_status_is_rejected) (status='authorized') ... FAIL
  test_unknown_status_is_rejected (test_refunds.TestStatus.test_unknown_status_is_rejected) (status='') ... FAIL
  test_unknown_status_is_rejected (test_refunds.TestStatus.test_unknown_status_is_rejected) (status='PAID') ... FAIL
test_full_refund_sets_status_refunded (test_refunds.TestSuccessBookkeeping.test_full_refund_sets_status_refunded)
Rule 7: the terminal transition is exactly `refunded`, and it is stored. ... ok
test_partial_refund_result_and_state (test_refunds.TestSuccessBookkeeping.test_partial_refund_result_and_state) ... ok
test_result_has_exactly_the_specified_fields (test_refunds.TestSuccessBookkeeping.test_result_has_exactly_the_specified_fields) ... ok
test_two_partial_refunds_then_fully_refunded (test_refunds.TestSuccessBookkeeping.test_two_partial_refunds_then_fully_refunded) ... ok
test_untouched_order_fields_are_preserved (test_refunds.TestSuccessBookkeeping.test_untouched_order_fields_are_preserved) ... ok

======================================================================
FAIL: test_gateway_is_never_called_when_a_rule_rejects (test_refunds.TestGatewayFailureAtomicity.test_gateway_is_never_called_when_a_rule_rejects) (order={'id': 'ord_1', 'owner_id': 'cus_1', 'charge_id': 'ch_1', 'paid': 1000, 'refunded': 100, 'status': 'partially_refunded', 'keys': {'key-1': {'refund_id': 're_123', 'amount': 100, 'status': 'partially_refunded'}}}, amount=100, actor={'id': 'cus_1', 'role': 'customer'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/AE-neutral-1/test_refunds.py", line 392, in test_gateway_is_never_called_when_a_rule_rejects
    with self.assertRaises((ValueError, PermissionError)):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: (<class 'ValueError'>, <class 'PermissionError'>) not raised

======================================================================
FAIL: test_cancelled_order_is_rejected (test_refunds.TestStatus.test_cancelled_order_is_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/AE-neutral-1/test_refunds.py", line 249, in test_cancelled_order_is_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_refunded_order_is_rejected_even_with_room_on_the_clock (test_refunds.TestStatus.test_refunded_order_is_rejected_even_with_room_on_the_clock)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/AE-neutral-1/test_refunds.py", line 257, in test_refunded_order_is_rejected_even_with_room_on_the_clock
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_unknown_status_is_rejected (test_refunds.TestStatus.test_unknown_status_is_rejected) (status='pending')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/AE-neutral-1/test_refunds.py", line 266, in test_unknown_status_is_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_unknown_status_is_rejected (test_refunds.TestStatus.test_unknown_status_is_rejected) (status='authorized')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/AE-neutral-1/test_refunds.py", line 266, in test_unknown_status_is_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_unknown_status_is_rejected (test_refunds.TestStatus.test_unknown_status_is_rejected) (status='')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/AE-neutral-1/test_refunds.py", line 266, in test_unknown_status_is_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_unknown_status_is_rejected (test_refunds.TestStatus.test_unknown_status_is_rejected) (status='PAID')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/AE-neutral-1/test_refunds.py", line 266, in test_unknown_status_is_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 41 tests in 0.002s

FAILED (failures=7)
(exit 1)
$ restored /tmp/aep-lab/pilot/AE-neutral-1/refunds.py from backup (byte-identical)
$ cd /tmp/aep-lab/pilot/AE-neutral-1 && python3 -m unittest discover -s . -p 'test*.py' -v   # expect SUCCESS
test_accepts_one (test_refunds.TestAmountValidation.test_accepts_one) ... ok
test_amount_is_checked_before_permission_and_status (test_refunds.TestAmountValidation.test_amount_is_checked_before_permission_and_status) ... ok
test_rejects_bools (test_refunds.TestAmountValidation.test_rejects_bools) ... ok
test_rejects_floats_even_when_whole (test_refunds.TestAmountValidation.test_rejects_floats_even_when_whole) ... ok
test_rejects_non_numeric_amounts (test_refunds.TestAmountValidation.test_rejects_non_numeric_amounts) ... ok
test_rejects_non_positive_ints (test_refunds.TestAmountValidation.test_rejects_non_positive_ints) ... ok
test_failed_refund_does_not_poison_a_retry (test_refunds.TestGatewayFailureAtomicity.test_failed_refund_does_not_poison_a_retry) ... ok
test_failed_refund_leaves_order_completely_unchanged (test_refunds.TestGatewayFailureAtomicity.test_failed_refund_leaves_order_completely_unchanged) ... ok
test_gateway_is_called_exactly_once_per_refund (test_refunds.TestGatewayFailureAtomicity.test_gateway_is_called_exactly_once_per_refund) ... ok
test_gateway_is_never_called_when_a_rule_rejects (test_refunds.TestGatewayFailureAtomicity.test_gateway_is_never_called_when_a_rule_rejects) ... ok
test_gateway_receives_the_order_charge_id (test_refunds.TestGatewayFailureAtomicity.test_gateway_receives_the_order_charge_id)
Rule 6: the gateway is charged the order's own charge id, not a fixed one. ... ok
test_distinct_keys_each_charge_once (test_refunds.TestIdempotency.test_distinct_keys_each_charge_once) ... ok
test_replay_ignores_a_different_amount_and_does_not_recharge (test_refunds.TestIdempotency.test_replay_ignores_a_different_amount_and_does_not_recharge) ... ok
test_replay_returns_stored_result_without_second_charge (test_refunds.TestIdempotency.test_replay_returns_stored_result_without_second_charge) ... ok
test_replay_uses_membership_not_truthiness (test_refunds.TestIdempotency.test_replay_uses_membership_not_truthiness)
Rule 1 keys on membership: a stored falsy result must still replay. ... ok
test_replay_wins_over_every_other_rule (test_refunds.TestIdempotency.test_replay_wins_over_every_other_rule)
Rule 1 precedes rules 2-5: bad amount, wrong actor, dead status. ... ok
test_actor_without_a_role_is_denied (test_refunds.TestPermission.test_actor_without_a_role_is_denied)
A missing role must fail closed, never default to a privileged one. ... ok
test_admin_and_support_need_not_own_the_order (test_refunds.TestPermission.test_admin_and_support_need_not_own_the_order) ... ok
test_admin_is_allowed (test_refunds.TestPermission.test_admin_is_allowed) ... ok
test_customer_without_matching_id_is_denied (test_refunds.TestPermission.test_customer_without_matching_id_is_denied) ... ok
test_other_customer_is_denied (test_refunds.TestPermission.test_other_customer_is_denied) ... ok
test_owner_customer_is_allowed (test_refunds.TestPermission.test_owner_customer_is_allowed) ... ok
test_owner_with_non_customer_role_is_denied (test_refunds.TestPermission.test_owner_with_non_customer_role_is_denied)
Rule 3 grants the *customer* who owns the order, not any matching id. ... ok
test_permission_is_checked_before_status (test_refunds.TestPermission.test_permission_is_checked_before_status) ... ok
test_support_is_allowed (test_refunds.TestPermission.test_support_is_allowed) ... ok
test_unknown_role_is_denied (test_refunds.TestPermission.test_unknown_role_is_denied) ... ok
test_amount_above_remaining_is_rejected (test_refunds.TestRefundableCap.test_amount_above_remaining_is_rejected) ... ok
test_amount_equal_to_paid_is_rejected_once_partly_refunded (test_refunds.TestRefundableCap.test_amount_equal_to_paid_is_rejected_once_partly_refunded) ... ok
test_exact_remaining_is_allowed (test_refunds.TestRefundableCap.test_exact_remaining_is_allowed) ... ok
test_full_refund_of_untouched_order_is_allowed (test_refunds.TestRefundableCap.test_full_refund_of_untouched_order_is_allowed) ... ok
test_over_refunded_order_rejects_any_amount (test_refunds.TestRefundableCap.test_over_refunded_order_rejects_any_amount)
A negative remainder must still reject every amount, not skip the cap. ... ok
test_cancelled_order_is_rejected (test_refunds.TestStatus.test_cancelled_order_is_rejected) ... ok
test_paid_order_is_accepted (test_refunds.TestStatus.test_paid_order_is_accepted) ... ok
test_partially_refunded_order_is_accepted (test_refunds.TestStatus.test_partially_refunded_order_is_accepted) ... ok
test_refunded_order_is_rejected_even_with_room_on_the_clock (test_refunds.TestStatus.test_refunded_order_is_rejected_even_with_room_on_the_clock) ... ok
test_unknown_status_is_rejected (test_refunds.TestStatus.test_unknown_status_is_rejected) ... ok
test_full_refund_sets_status_refunded (test_refunds.TestSuccessBookkeeping.test_full_refund_sets_status_refunded)
Rule 7: the terminal transition is exactly `refunded`, and it is stored. ... ok
test_partial_refund_result_and_state (test_refunds.TestSuccessBookkeeping.test_partial_refund_result_and_state) ... ok
test_result_has_exactly_the_specified_fields (test_refunds.TestSuccessBookkeeping.test_result_has_exactly_the_specified_fields) ... ok
test_two_partial_refunds_then_fully_refunded (test_refunds.TestSuccessBookkeeping.test_two_partial_refunds_then_fully_refunded) ... ok
test_untouched_order_fields_are_preserved (test_refunds.TestSuccessBookkeeping.test_untouched_order_fields_are_preserved) ... ok

----------------------------------------------------------------------
Ran 41 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```


## 6.8 Negative control: rule 5 — refundable cap

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/AE-neutral-1/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/AE-neutral-1/negcontrol/break_cap.py" --test-cmd "cd /tmp/aep-lab/pilot/AE-neutral-1 && python3 -m unittest discover -s . -p 'test*.py' -v" --expect "FAIL: test_amount_above_remaining_is_rejected" --timeout 20
$ backed up /tmp/aep-lab/pilot/AE-neutral-1/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-qsjka03h/refunds.py
$ python3 /tmp/aep-lab/pilot/AE-neutral-1/negcontrol/break_cap.py
break_cap: paid-minus-refunded cap disabled
$ cd /tmp/aep-lab/pilot/AE-neutral-1 && python3 -m unittest discover -s . -p 'test*.py' -v   # expect FAILURE matching /FAIL: test_amount_above_remaining_is_rejected/
test_accepts_one (test_refunds.TestAmountValidation.test_accepts_one) ... ok
test_amount_is_checked_before_permission_and_status (test_refunds.TestAmountValidation.test_amount_is_checked_before_permission_and_status) ... ok
test_rejects_bools (test_refunds.TestAmountValidation.test_rejects_bools) ... ok
test_rejects_floats_even_when_whole (test_refunds.TestAmountValidation.test_rejects_floats_even_when_whole) ... ok
test_rejects_non_numeric_amounts (test_refunds.TestAmountValidation.test_rejects_non_numeric_amounts) ... ok
test_rejects_non_positive_ints (test_refunds.TestAmountValidation.test_rejects_non_positive_ints) ... ok
test_failed_refund_does_not_poison_a_retry (test_refunds.TestGatewayFailureAtomicity.test_failed_refund_does_not_poison_a_retry) ... ok
test_failed_refund_leaves_order_completely_unchanged (test_refunds.TestGatewayFailureAtomicity.test_failed_refund_leaves_order_completely_unchanged) ... ok
test_gateway_is_called_exactly_once_per_refund (test_refunds.TestGatewayFailureAtomicity.test_gateway_is_called_exactly_once_per_refund) ... ok
test_gateway_is_never_called_when_a_rule_rejects (test_refunds.TestGatewayFailureAtomicity.test_gateway_is_never_called_when_a_rule_rejects) ... 
  test_gateway_is_never_called_when_a_rule_rejects (test_refunds.TestGatewayFailureAtomicity.test_gateway_is_never_called_when_a_rule_rejects) (order={'id': 'ord_1', 'owner_id': 'cus_1', 'charge_id': 'ch_1', 'paid': 1000, 'refunded': 1400, 'status': 'partially_refunded', 'keys': {'key-1': {'refund_id': 're_123', 'amount': 500, 'status': 'partially_refunded'}}}, amount=500, actor={'id': 'cus_1', 'role': 'customer'}) ... FAIL
test_gateway_receives_the_order_charge_id (test_refunds.TestGatewayFailureAtomicity.test_gateway_receives_the_order_charge_id)
Rule 6: the gateway is charged the order's own charge id, not a fixed one. ... ok
test_distinct_keys_each_charge_once (test_refunds.TestIdempotency.test_distinct_keys_each_charge_once) ... ok
test_replay_ignores_a_different_amount_and_does_not_recharge (test_refunds.TestIdempotency.test_replay_ignores_a_different_amount_and_does_not_recharge) ... ok
test_replay_returns_stored_result_without_second_charge (test_refunds.TestIdempotency.test_replay_returns_stored_result_without_second_charge) ... ok
test_replay_uses_membership_not_truthiness (test_refunds.TestIdempotency.test_replay_uses_membership_not_truthiness)
Rule 1 keys on membership: a stored falsy result must still replay. ... ok
test_replay_wins_over_every_other_rule (test_refunds.TestIdempotency.test_replay_wins_over_every_other_rule)
Rule 1 precedes rules 2-5: bad amount, wrong actor, dead status. ... ok
test_actor_without_a_role_is_denied (test_refunds.TestPermission.test_actor_without_a_role_is_denied)
A missing role must fail closed, never default to a privileged one. ... ok
test_admin_and_support_need_not_own_the_order (test_refunds.TestPermission.test_admin_and_support_need_not_own_the_order) ... ok
test_admin_is_allowed (test_refunds.TestPermission.test_admin_is_allowed) ... ok
test_customer_without_matching_id_is_denied (test_refunds.TestPermission.test_customer_without_matching_id_is_denied) ... ok
test_other_customer_is_denied (test_refunds.TestPermission.test_other_customer_is_denied) ... ok
test_owner_customer_is_allowed (test_refunds.TestPermission.test_owner_customer_is_allowed) ... ok
test_owner_with_non_customer_role_is_denied (test_refunds.TestPermission.test_owner_with_non_customer_role_is_denied)
Rule 3 grants the *customer* who owns the order, not any matching id. ... ok
test_permission_is_checked_before_status (test_refunds.TestPermission.test_permission_is_checked_before_status) ... ok
test_support_is_allowed (test_refunds.TestPermission.test_support_is_allowed) ... ok
test_unknown_role_is_denied (test_refunds.TestPermission.test_unknown_role_is_denied) ... ok
test_amount_above_remaining_is_rejected (test_refunds.TestRefundableCap.test_amount_above_remaining_is_rejected) ... FAIL
test_amount_equal_to_paid_is_rejected_once_partly_refunded (test_refunds.TestRefundableCap.test_amount_equal_to_paid_is_rejected_once_partly_refunded) ... FAIL
test_exact_remaining_is_allowed (test_refunds.TestRefundableCap.test_exact_remaining_is_allowed) ... ok
test_full_refund_of_untouched_order_is_allowed (test_refunds.TestRefundableCap.test_full_refund_of_untouched_order_is_allowed) ... ok
test_over_refunded_order_rejects_any_amount (test_refunds.TestRefundableCap.test_over_refunded_order_rejects_any_amount)
A negative remainder must still reject every amount, not skip the cap. ... 
  test_over_refunded_order_rejects_any_amount (test_refunds.TestRefundableCap.test_over_refunded_order_rejects_any_amount) (amount=1)
A negative remainder must still reject every amount, not skip the cap. ... FAIL
  test_over_refunded_order_rejects_any_amount (test_refunds.TestRefundableCap.test_over_refunded_order_rejects_any_amount) (amount=2)
A negative remainder must still reject every amount, not skip the cap. ... FAIL
  test_over_refunded_order_rejects_any_amount (test_refunds.TestRefundableCap.test_over_refunded_order_rejects_any_amount) (amount=100)
A negative remainder must still reject every amount, not skip the cap. ... FAIL
test_cancelled_order_is_rejected (test_refunds.TestStatus.test_cancelled_order_is_rejected) ... ok
test_paid_order_is_accepted (test_refunds.TestStatus.test_paid_order_is_accepted) ... ok
test_partially_refunded_order_is_accepted (test_refunds.TestStatus.test_partially_refunded_order_is_accepted) ... ok
test_refunded_order_is_rejected_even_with_room_on_the_clock (test_refunds.TestStatus.test_refunded_order_is_rejected_even_with_room_on_the_clock) ... ok
test_unknown_status_is_rejected (test_refunds.TestStatus.test_unknown_status_is_rejected) ... ok
test_full_refund_sets_status_refunded (test_refunds.TestSuccessBookkeeping.test_full_refund_sets_status_refunded)
Rule 7: the terminal transition is exactly `refunded`, and it is stored. ... ok
test_partial_refund_result_and_state (test_refunds.TestSuccessBookkeeping.test_partial_refund_result_and_state) ... ok
test_result_has_exactly_the_specified_fields (test_refunds.TestSuccessBookkeeping.test_result_has_exactly_the_specified_fields) ... ok
test_two_partial_refunds_then_fully_refunded (test_refunds.TestSuccessBookkeeping.test_two_partial_refunds_then_fully_refunded) ... ok
test_untouched_order_fields_are_preserved (test_refunds.TestSuccessBookkeeping.test_untouched_order_fields_are_preserved) ... ok

======================================================================
FAIL: test_gateway_is_never_called_when_a_rule_rejects (test_refunds.TestGatewayFailureAtomicity.test_gateway_is_never_called_when_a_rule_rejects) (order={'id': 'ord_1', 'owner_id': 'cus_1', 'charge_id': 'ch_1', 'paid': 1000, 'refunded': 1400, 'status': 'partially_refunded', 'keys': {'key-1': {'refund_id': 're_123', 'amount': 500, 'status': 'partially_refunded'}}}, amount=500, actor={'id': 'cus_1', 'role': 'customer'})
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/AE-neutral-1/test_refunds.py", line 392, in test_gateway_is_never_called_when_a_rule_rejects
    with self.assertRaises((ValueError, PermissionError)):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: (<class 'ValueError'>, <class 'PermissionError'>) not raised

======================================================================
FAIL: test_amount_above_remaining_is_rejected (test_refunds.TestRefundableCap.test_amount_above_remaining_is_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/AE-neutral-1/test_refunds.py", line 291, in test_amount_above_remaining_is_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_amount_equal_to_paid_is_rejected_once_partly_refunded (test_refunds.TestRefundableCap.test_amount_equal_to_paid_is_rejected_once_partly_refunded)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/AE-neutral-1/test_refunds.py", line 299, in test_amount_equal_to_paid_is_rejected_once_partly_refunded
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_over_refunded_order_rejects_any_amount (test_refunds.TestRefundableCap.test_over_refunded_order_rejects_any_amount) (amount=1)
A negative remainder must still reject every amount, not skip the cap.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/AE-neutral-1/test_refunds.py", line 310, in test_over_refunded_order_rejects_any_amount
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_over_refunded_order_rejects_any_amount (test_refunds.TestRefundableCap.test_over_refunded_order_rejects_any_amount) (amount=2)
A negative remainder must still reject every amount, not skip the cap.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/AE-neutral-1/test_refunds.py", line 310, in test_over_refunded_order_rejects_any_amount
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_over_refunded_order_rejects_any_amount (test_refunds.TestRefundableCap.test_over_refunded_order_rejects_any_amount) (amount=100)
A negative remainder must still reject every amount, not skip the cap.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/AE-neutral-1/test_refunds.py", line 310, in test_over_refunded_order_rejects_any_amount
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 41 tests in 0.002s

FAILED (failures=6)
(exit 1)
$ restored /tmp/aep-lab/pilot/AE-neutral-1/refunds.py from backup (byte-identical)
$ cd /tmp/aep-lab/pilot/AE-neutral-1 && python3 -m unittest discover -s . -p 'test*.py' -v   # expect SUCCESS
test_accepts_one (test_refunds.TestAmountValidation.test_accepts_one) ... ok
test_amount_is_checked_before_permission_and_status (test_refunds.TestAmountValidation.test_amount_is_checked_before_permission_and_status) ... ok
test_rejects_bools (test_refunds.TestAmountValidation.test_rejects_bools) ... ok
test_rejects_floats_even_when_whole (test_refunds.TestAmountValidation.test_rejects_floats_even_when_whole) ... ok
test_rejects_non_numeric_amounts (test_refunds.TestAmountValidation.test_rejects_non_numeric_amounts) ... ok
test_rejects_non_positive_ints (test_refunds.TestAmountValidation.test_rejects_non_positive_ints) ... ok
test_failed_refund_does_not_poison_a_retry (test_refunds.TestGatewayFailureAtomicity.test_failed_refund_does_not_poison_a_retry) ... ok
test_failed_refund_leaves_order_completely_unchanged (test_refunds.TestGatewayFailureAtomicity.test_failed_refund_leaves_order_completely_unchanged) ... ok
test_gateway_is_called_exactly_once_per_refund (test_refunds.TestGatewayFailureAtomicity.test_gateway_is_called_exactly_once_per_refund) ... ok
test_gateway_is_never_called_when_a_rule_rejects (test_refunds.TestGatewayFailureAtomicity.test_gateway_is_never_called_when_a_rule_rejects) ... ok
test_gateway_receives_the_order_charge_id (test_refunds.TestGatewayFailureAtomicity.test_gateway_receives_the_order_charge_id)
Rule 6: the gateway is charged the order's own charge id, not a fixed one. ... ok
test_distinct_keys_each_charge_once (test_refunds.TestIdempotency.test_distinct_keys_each_charge_once) ... ok
test_replay_ignores_a_different_amount_and_does_not_recharge (test_refunds.TestIdempotency.test_replay_ignores_a_different_amount_and_does_not_recharge) ... ok
test_replay_returns_stored_result_without_second_charge (test_refunds.TestIdempotency.test_replay_returns_stored_result_without_second_charge) ... ok
test_replay_uses_membership_not_truthiness (test_refunds.TestIdempotency.test_replay_uses_membership_not_truthiness)
Rule 1 keys on membership: a stored falsy result must still replay. ... ok
test_replay_wins_over_every_other_rule (test_refunds.TestIdempotency.test_replay_wins_over_every_other_rule)
Rule 1 precedes rules 2-5: bad amount, wrong actor, dead status. ... ok
test_actor_without_a_role_is_denied (test_refunds.TestPermission.test_actor_without_a_role_is_denied)
A missing role must fail closed, never default to a privileged one. ... ok
test_admin_and_support_need_not_own_the_order (test_refunds.TestPermission.test_admin_and_support_need_not_own_the_order) ... ok
test_admin_is_allowed (test_refunds.TestPermission.test_admin_is_allowed) ... ok
test_customer_without_matching_id_is_denied (test_refunds.TestPermission.test_customer_without_matching_id_is_denied) ... ok
test_other_customer_is_denied (test_refunds.TestPermission.test_other_customer_is_denied) ... ok
test_owner_customer_is_allowed (test_refunds.TestPermission.test_owner_customer_is_allowed) ... ok
test_owner_with_non_customer_role_is_denied (test_refunds.TestPermission.test_owner_with_non_customer_role_is_denied)
Rule 3 grants the *customer* who owns the order, not any matching id. ... ok
test_permission_is_checked_before_status (test_refunds.TestPermission.test_permission_is_checked_before_status) ... ok
test_support_is_allowed (test_refunds.TestPermission.test_support_is_allowed) ... ok
test_unknown_role_is_denied (test_refunds.TestPermission.test_unknown_role_is_denied) ... ok
test_amount_above_remaining_is_rejected (test_refunds.TestRefundableCap.test_amount_above_remaining_is_rejected) ... ok
test_amount_equal_to_paid_is_rejected_once_partly_refunded (test_refunds.TestRefundableCap.test_amount_equal_to_paid_is_rejected_once_partly_refunded) ... ok
test_exact_remaining_is_allowed (test_refunds.TestRefundableCap.test_exact_remaining_is_allowed) ... ok
test_full_refund_of_untouched_order_is_allowed (test_refunds.TestRefundableCap.test_full_refund_of_untouched_order_is_allowed) ... ok
test_over_refunded_order_rejects_any_amount (test_refunds.TestRefundableCap.test_over_refunded_order_rejects_any_amount)
A negative remainder must still reject every amount, not skip the cap. ... ok
test_cancelled_order_is_rejected (test_refunds.TestStatus.test_cancelled_order_is_rejected) ... ok
test_paid_order_is_accepted (test_refunds.TestStatus.test_paid_order_is_accepted) ... ok
test_partially_refunded_order_is_accepted (test_refunds.TestStatus.test_partially_refunded_order_is_accepted) ... ok
test_refunded_order_is_rejected_even_with_room_on_the_clock (test_refunds.TestStatus.test_refunded_order_is_rejected_even_with_room_on_the_clock) ... ok
test_unknown_status_is_rejected (test_refunds.TestStatus.test_unknown_status_is_rejected) ... ok
test_full_refund_sets_status_refunded (test_refunds.TestSuccessBookkeeping.test_full_refund_sets_status_refunded)
Rule 7: the terminal transition is exactly `refunded`, and it is stored. ... ok
test_partial_refund_result_and_state (test_refunds.TestSuccessBookkeeping.test_partial_refund_result_and_state) ... ok
test_result_has_exactly_the_specified_fields (test_refunds.TestSuccessBookkeeping.test_result_has_exactly_the_specified_fields) ... ok
test_two_partial_refunds_then_fully_refunded (test_refunds.TestSuccessBookkeeping.test_two_partial_refunds_then_fully_refunded) ... ok
test_untouched_order_fields_are_preserved (test_refunds.TestSuccessBookkeeping.test_untouched_order_fields_are_preserved) ... ok

----------------------------------------------------------------------
Ran 41 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```


## 6.9 Negative control: rule 5 — cap on a negative remainder

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/AE-neutral-1/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/AE-neutral-1/negcontrol/break_cap_over_refunded.py" --test-cmd "cd /tmp/aep-lab/pilot/AE-neutral-1 && python3 -m unittest discover -s . -p 'test*.py' -v" --expect "FAIL: test_over_refunded_order_rejects_any_amount" --timeout 20
$ backed up /tmp/aep-lab/pilot/AE-neutral-1/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-0xegr4fd/refunds.py
$ python3 /tmp/aep-lab/pilot/AE-neutral-1/negcontrol/break_cap_over_refunded.py
break_cap_over_refunded: cap no longer applies to an over-refunded order
$ cd /tmp/aep-lab/pilot/AE-neutral-1 && python3 -m unittest discover -s . -p 'test*.py' -v   # expect FAILURE matching /FAIL: test_over_refunded_order_rejects_any_amount/
test_accepts_one (test_refunds.TestAmountValidation.test_accepts_one) ... ok
test_amount_is_checked_before_permission_and_status (test_refunds.TestAmountValidation.test_amount_is_checked_before_permission_and_status) ... ok
test_rejects_bools (test_refunds.TestAmountValidation.test_rejects_bools) ... ok
test_rejects_floats_even_when_whole (test_refunds.TestAmountValidation.test_rejects_floats_even_when_whole) ... ok
test_rejects_non_numeric_amounts (test_refunds.TestAmountValidation.test_rejects_non_numeric_amounts) ... ok
test_rejects_non_positive_ints (test_refunds.TestAmountValidation.test_rejects_non_positive_ints) ... ok
test_failed_refund_does_not_poison_a_retry (test_refunds.TestGatewayFailureAtomicity.test_failed_refund_does_not_poison_a_retry) ... ok
test_failed_refund_leaves_order_completely_unchanged (test_refunds.TestGatewayFailureAtomicity.test_failed_refund_leaves_order_completely_unchanged) ... ok
test_gateway_is_called_exactly_once_per_refund (test_refunds.TestGatewayFailureAtomicity.test_gateway_is_called_exactly_once_per_refund) ... ok
test_gateway_is_never_called_when_a_rule_rejects (test_refunds.TestGatewayFailureAtomicity.test_gateway_is_never_called_when_a_rule_rejects) ... ok
test_gateway_receives_the_order_charge_id (test_refunds.TestGatewayFailureAtomicity.test_gateway_receives_the_order_charge_id)
Rule 6: the gateway is charged the order's own charge id, not a fixed one. ... ok
test_distinct_keys_each_charge_once (test_refunds.TestIdempotency.test_distinct_keys_each_charge_once) ... ok
test_replay_ignores_a_different_amount_and_does_not_recharge (test_refunds.TestIdempotency.test_replay_ignores_a_different_amount_and_does_not_recharge) ... ok
test_replay_returns_stored_result_without_second_charge (test_refunds.TestIdempotency.test_replay_returns_stored_result_without_second_charge) ... ok
test_replay_uses_membership_not_truthiness (test_refunds.TestIdempotency.test_replay_uses_membership_not_truthiness)
Rule 1 keys on membership: a stored falsy result must still replay. ... ok
test_replay_wins_over_every_other_rule (test_refunds.TestIdempotency.test_replay_wins_over_every_other_rule)
Rule 1 precedes rules 2-5: bad amount, wrong actor, dead status. ... ok
test_actor_without_a_role_is_denied (test_refunds.TestPermission.test_actor_without_a_role_is_denied)
A missing role must fail closed, never default to a privileged one. ... ok
test_admin_and_support_need_not_own_the_order (test_refunds.TestPermission.test_admin_and_support_need_not_own_the_order) ... ok
test_admin_is_allowed (test_refunds.TestPermission.test_admin_is_allowed) ... ok
test_customer_without_matching_id_is_denied (test_refunds.TestPermission.test_customer_without_matching_id_is_denied) ... ok
test_other_customer_is_denied (test_refunds.TestPermission.test_other_customer_is_denied) ... ok
test_owner_customer_is_allowed (test_refunds.TestPermission.test_owner_customer_is_allowed) ... ok
test_owner_with_non_customer_role_is_denied (test_refunds.TestPermission.test_owner_with_non_customer_role_is_denied)
Rule 3 grants the *customer* who owns the order, not any matching id. ... ok
test_permission_is_checked_before_status (test_refunds.TestPermission.test_permission_is_checked_before_status) ... ok
test_support_is_allowed (test_refunds.TestPermission.test_support_is_allowed) ... ok
test_unknown_role_is_denied (test_refunds.TestPermission.test_unknown_role_is_denied) ... ok
test_amount_above_remaining_is_rejected (test_refunds.TestRefundableCap.test_amount_above_remaining_is_rejected) ... ok
test_amount_equal_to_paid_is_rejected_once_partly_refunded (test_refunds.TestRefundableCap.test_amount_equal_to_paid_is_rejected_once_partly_refunded) ... ok
test_exact_remaining_is_allowed (test_refunds.TestRefundableCap.test_exact_remaining_is_allowed) ... ok
test_full_refund_of_untouched_order_is_allowed (test_refunds.TestRefundableCap.test_full_refund_of_untouched_order_is_allowed) ... ok
test_over_refunded_order_rejects_any_amount (test_refunds.TestRefundableCap.test_over_refunded_order_rejects_any_amount)
A negative remainder must still reject every amount, not skip the cap. ... 
  test_over_refunded_order_rejects_any_amount (test_refunds.TestRefundableCap.test_over_refunded_order_rejects_any_amount) (amount=1)
A negative remainder must still reject every amount, not skip the cap. ... FAIL
  test_over_refunded_order_rejects_any_amount (test_refunds.TestRefundableCap.test_over_refunded_order_rejects_any_amount) (amount=2)
A negative remainder must still reject every amount, not skip the cap. ... FAIL
  test_over_refunded_order_rejects_any_amount (test_refunds.TestRefundableCap.test_over_refunded_order_rejects_any_amount) (amount=100)
A negative remainder must still reject every amount, not skip the cap. ... FAIL
test_cancelled_order_is_rejected (test_refunds.TestStatus.test_cancelled_order_is_rejected) ... ok
test_paid_order_is_accepted (test_refunds.TestStatus.test_paid_order_is_accepted) ... ok
test_partially_refunded_order_is_accepted (test_refunds.TestStatus.test_partially_refunded_order_is_accepted) ... ok
test_refunded_order_is_rejected_even_with_room_on_the_clock (test_refunds.TestStatus.test_refunded_order_is_rejected_even_with_room_on_the_clock) ... ok
test_unknown_status_is_rejected (test_refunds.TestStatus.test_unknown_status_is_rejected) ... ok
test_full_refund_sets_status_refunded (test_refunds.TestSuccessBookkeeping.test_full_refund_sets_status_refunded)
Rule 7: the terminal transition is exactly `refunded`, and it is stored. ... ok
test_partial_refund_result_and_state (test_refunds.TestSuccessBookkeeping.test_partial_refund_result_and_state) ... ok
test_result_has_exactly_the_specified_fields (test_refunds.TestSuccessBookkeeping.test_result_has_exactly_the_specified_fields) ... ok
test_two_partial_refunds_then_fully_refunded (test_refunds.TestSuccessBookkeeping.test_two_partial_refunds_then_fully_refunded) ... ok
test_untouched_order_fields_are_preserved (test_refunds.TestSuccessBookkeeping.test_untouched_order_fields_are_preserved) ... ok

======================================================================
FAIL: test_over_refunded_order_rejects_any_amount (test_refunds.TestRefundableCap.test_over_refunded_order_rejects_any_amount) (amount=1)
A negative remainder must still reject every amount, not skip the cap.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/AE-neutral-1/test_refunds.py", line 310, in test_over_refunded_order_rejects_any_amount
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_over_refunded_order_rejects_any_amount (test_refunds.TestRefundableCap.test_over_refunded_order_rejects_any_amount) (amount=2)
A negative remainder must still reject every amount, not skip the cap.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/AE-neutral-1/test_refunds.py", line 310, in test_over_refunded_order_rejects_any_amount
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_over_refunded_order_rejects_any_amount (test_refunds.TestRefundableCap.test_over_refunded_order_rejects_any_amount) (amount=100)
A negative remainder must still reject every amount, not skip the cap.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/AE-neutral-1/test_refunds.py", line 310, in test_over_refunded_order_rejects_any_amount
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 41 tests in 0.002s

FAILED (failures=3)
(exit 1)
$ restored /tmp/aep-lab/pilot/AE-neutral-1/refunds.py from backup (byte-identical)
$ cd /tmp/aep-lab/pilot/AE-neutral-1 && python3 -m unittest discover -s . -p 'test*.py' -v   # expect SUCCESS
test_accepts_one (test_refunds.TestAmountValidation.test_accepts_one) ... ok
test_amount_is_checked_before_permission_and_status (test_refunds.TestAmountValidation.test_amount_is_checked_before_permission_and_status) ... ok
test_rejects_bools (test_refunds.TestAmountValidation.test_rejects_bools) ... ok
test_rejects_floats_even_when_whole (test_refunds.TestAmountValidation.test_rejects_floats_even_when_whole) ... ok
test_rejects_non_numeric_amounts (test_refunds.TestAmountValidation.test_rejects_non_numeric_amounts) ... ok
test_rejects_non_positive_ints (test_refunds.TestAmountValidation.test_rejects_non_positive_ints) ... ok
test_failed_refund_does_not_poison_a_retry (test_refunds.TestGatewayFailureAtomicity.test_failed_refund_does_not_poison_a_retry) ... ok
test_failed_refund_leaves_order_completely_unchanged (test_refunds.TestGatewayFailureAtomicity.test_failed_refund_leaves_order_completely_unchanged) ... ok
test_gateway_is_called_exactly_once_per_refund (test_refunds.TestGatewayFailureAtomicity.test_gateway_is_called_exactly_once_per_refund) ... ok
test_gateway_is_never_called_when_a_rule_rejects (test_refunds.TestGatewayFailureAtomicity.test_gateway_is_never_called_when_a_rule_rejects) ... ok
test_gateway_receives_the_order_charge_id (test_refunds.TestGatewayFailureAtomicity.test_gateway_receives_the_order_charge_id)
Rule 6: the gateway is charged the order's own charge id, not a fixed one. ... ok
test_distinct_keys_each_charge_once (test_refunds.TestIdempotency.test_distinct_keys_each_charge_once) ... ok
test_replay_ignores_a_different_amount_and_does_not_recharge (test_refunds.TestIdempotency.test_replay_ignores_a_different_amount_and_does_not_recharge) ... ok
test_replay_returns_stored_result_without_second_charge (test_refunds.TestIdempotency.test_replay_returns_stored_result_without_second_charge) ... ok
test_replay_uses_membership_not_truthiness (test_refunds.TestIdempotency.test_replay_uses_membership_not_truthiness)
Rule 1 keys on membership: a stored falsy result must still replay. ... ok
test_replay_wins_over_every_other_rule (test_refunds.TestIdempotency.test_replay_wins_over_every_other_rule)
Rule 1 precedes rules 2-5: bad amount, wrong actor, dead status. ... ok
test_actor_without_a_role_is_denied (test_refunds.TestPermission.test_actor_without_a_role_is_denied)
A missing role must fail closed, never default to a privileged one. ... ok
test_admin_and_support_need_not_own_the_order (test_refunds.TestPermission.test_admin_and_support_need_not_own_the_order) ... ok
test_admin_is_allowed (test_refunds.TestPermission.test_admin_is_allowed) ... ok
test_customer_without_matching_id_is_denied (test_refunds.TestPermission.test_customer_without_matching_id_is_denied) ... ok
test_other_customer_is_denied (test_refunds.TestPermission.test_other_customer_is_denied) ... ok
test_owner_customer_is_allowed (test_refunds.TestPermission.test_owner_customer_is_allowed) ... ok
test_owner_with_non_customer_role_is_denied (test_refunds.TestPermission.test_owner_with_non_customer_role_is_denied)
Rule 3 grants the *customer* who owns the order, not any matching id. ... ok
test_permission_is_checked_before_status (test_refunds.TestPermission.test_permission_is_checked_before_status) ... ok
test_support_is_allowed (test_refunds.TestPermission.test_support_is_allowed) ... ok
test_unknown_role_is_denied (test_refunds.TestPermission.test_unknown_role_is_denied) ... ok
test_amount_above_remaining_is_rejected (test_refunds.TestRefundableCap.test_amount_above_remaining_is_rejected) ... ok
test_amount_equal_to_paid_is_rejected_once_partly_refunded (test_refunds.TestRefundableCap.test_amount_equal_to_paid_is_rejected_once_partly_refunded) ... ok
test_exact_remaining_is_allowed (test_refunds.TestRefundableCap.test_exact_remaining_is_allowed) ... ok
test_full_refund_of_untouched_order_is_allowed (test_refunds.TestRefundableCap.test_full_refund_of_untouched_order_is_allowed) ... ok
test_over_refunded_order_rejects_any_amount (test_refunds.TestRefundableCap.test_over_refunded_order_rejects_any_amount)
A negative remainder must still reject every amount, not skip the cap. ... ok
test_cancelled_order_is_rejected (test_refunds.TestStatus.test_cancelled_order_is_rejected) ... ok
test_paid_order_is_accepted (test_refunds.TestStatus.test_paid_order_is_accepted) ... ok
test_partially_refunded_order_is_accepted (test_refunds.TestStatus.test_partially_refunded_order_is_accepted) ... ok
test_refunded_order_is_rejected_even_with_room_on_the_clock (test_refunds.TestStatus.test_refunded_order_is_rejected_even_with_room_on_the_clock) ... ok
test_unknown_status_is_rejected (test_refunds.TestStatus.test_unknown_status_is_rejected) ... ok
test_full_refund_sets_status_refunded (test_refunds.TestSuccessBookkeeping.test_full_refund_sets_status_refunded)
Rule 7: the terminal transition is exactly `refunded`, and it is stored. ... ok
test_partial_refund_result_and_state (test_refunds.TestSuccessBookkeeping.test_partial_refund_result_and_state) ... ok
test_result_has_exactly_the_specified_fields (test_refunds.TestSuccessBookkeeping.test_result_has_exactly_the_specified_fields) ... ok
test_two_partial_refunds_then_fully_refunded (test_refunds.TestSuccessBookkeeping.test_two_partial_refunds_then_fully_refunded) ... ok
test_untouched_order_fields_are_preserved (test_refunds.TestSuccessBookkeeping.test_untouched_order_fields_are_preserved) ... ok

----------------------------------------------------------------------
Ran 41 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```


## 6.10 Negative control: rule 6 — gateway-failure atomicity

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/AE-neutral-1/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/AE-neutral-1/negcontrol/break_atomicity.py" --test-cmd "cd /tmp/aep-lab/pilot/AE-neutral-1 && python3 -m unittest discover -s . -p 'test*.py' -v" --expect "FAIL: test_failed_refund_leaves_order_completely_unchanged" --timeout 20
$ backed up /tmp/aep-lab/pilot/AE-neutral-1/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-7gg9xrem/refunds.py
$ python3 /tmp/aep-lab/pilot/AE-neutral-1/negcontrol/break_atomicity.py
break_atomicity: order written before the gateway call, no rollback
$ cd /tmp/aep-lab/pilot/AE-neutral-1 && python3 -m unittest discover -s . -p 'test*.py' -v   # expect FAILURE matching /FAIL: test_failed_refund_leaves_order_completely_unchanged/
test_accepts_one (test_refunds.TestAmountValidation.test_accepts_one) ... ok
test_amount_is_checked_before_permission_and_status (test_refunds.TestAmountValidation.test_amount_is_checked_before_permission_and_status) ... ok
test_rejects_bools (test_refunds.TestAmountValidation.test_rejects_bools) ... ok
test_rejects_floats_even_when_whole (test_refunds.TestAmountValidation.test_rejects_floats_even_when_whole) ... ok
test_rejects_non_numeric_amounts (test_refunds.TestAmountValidation.test_rejects_non_numeric_amounts) ... ok
test_rejects_non_positive_ints (test_refunds.TestAmountValidation.test_rejects_non_positive_ints) ... ok
test_failed_refund_does_not_poison_a_retry (test_refunds.TestGatewayFailureAtomicity.test_failed_refund_does_not_poison_a_retry) ... FAIL
test_failed_refund_leaves_order_completely_unchanged (test_refunds.TestGatewayFailureAtomicity.test_failed_refund_leaves_order_completely_unchanged) ... FAIL
test_gateway_is_called_exactly_once_per_refund (test_refunds.TestGatewayFailureAtomicity.test_gateway_is_called_exactly_once_per_refund) ... ok
test_gateway_is_never_called_when_a_rule_rejects (test_refunds.TestGatewayFailureAtomicity.test_gateway_is_never_called_when_a_rule_rejects) ... ok
test_gateway_receives_the_order_charge_id (test_refunds.TestGatewayFailureAtomicity.test_gateway_receives_the_order_charge_id)
Rule 6: the gateway is charged the order's own charge id, not a fixed one. ... ok
test_distinct_keys_each_charge_once (test_refunds.TestIdempotency.test_distinct_keys_each_charge_once) ... ok
test_replay_ignores_a_different_amount_and_does_not_recharge (test_refunds.TestIdempotency.test_replay_ignores_a_different_amount_and_does_not_recharge) ... ok
test_replay_returns_stored_result_without_second_charge (test_refunds.TestIdempotency.test_replay_returns_stored_result_without_second_charge) ... ok
test_replay_uses_membership_not_truthiness (test_refunds.TestIdempotency.test_replay_uses_membership_not_truthiness)
Rule 1 keys on membership: a stored falsy result must still replay. ... ok
test_replay_wins_over_every_other_rule (test_refunds.TestIdempotency.test_replay_wins_over_every_other_rule)
Rule 1 precedes rules 2-5: bad amount, wrong actor, dead status. ... ok
test_actor_without_a_role_is_denied (test_refunds.TestPermission.test_actor_without_a_role_is_denied)
A missing role must fail closed, never default to a privileged one. ... ok
test_admin_and_support_need_not_own_the_order (test_refunds.TestPermission.test_admin_and_support_need_not_own_the_order) ... ok
test_admin_is_allowed (test_refunds.TestPermission.test_admin_is_allowed) ... ok
test_customer_without_matching_id_is_denied (test_refunds.TestPermission.test_customer_without_matching_id_is_denied) ... ok
test_other_customer_is_denied (test_refunds.TestPermission.test_other_customer_is_denied) ... ok
test_owner_customer_is_allowed (test_refunds.TestPermission.test_owner_customer_is_allowed) ... ok
test_owner_with_non_customer_role_is_denied (test_refunds.TestPermission.test_owner_with_non_customer_role_is_denied)
Rule 3 grants the *customer* who owns the order, not any matching id. ... ok
test_permission_is_checked_before_status (test_refunds.TestPermission.test_permission_is_checked_before_status) ... ok
test_support_is_allowed (test_refunds.TestPermission.test_support_is_allowed) ... ok
test_unknown_role_is_denied (test_refunds.TestPermission.test_unknown_role_is_denied) ... ok
test_amount_above_remaining_is_rejected (test_refunds.TestRefundableCap.test_amount_above_remaining_is_rejected) ... ok
test_amount_equal_to_paid_is_rejected_once_partly_refunded (test_refunds.TestRefundableCap.test_amount_equal_to_paid_is_rejected_once_partly_refunded) ... ok
test_exact_remaining_is_allowed (test_refunds.TestRefundableCap.test_exact_remaining_is_allowed) ... ok
test_full_refund_of_untouched_order_is_allowed (test_refunds.TestRefundableCap.test_full_refund_of_untouched_order_is_allowed) ... ok
test_over_refunded_order_rejects_any_amount (test_refunds.TestRefundableCap.test_over_refunded_order_rejects_any_amount)
A negative remainder must still reject every amount, not skip the cap. ... ok
test_cancelled_order_is_rejected (test_refunds.TestStatus.test_cancelled_order_is_rejected) ... ok
test_paid_order_is_accepted (test_refunds.TestStatus.test_paid_order_is_accepted) ... ok
test_partially_refunded_order_is_accepted (test_refunds.TestStatus.test_partially_refunded_order_is_accepted) ... ok
test_refunded_order_is_rejected_even_with_room_on_the_clock (test_refunds.TestStatus.test_refunded_order_is_rejected_even_with_room_on_the_clock) ... ok
test_unknown_status_is_rejected (test_refunds.TestStatus.test_unknown_status_is_rejected) ... ok
test_full_refund_sets_status_refunded (test_refunds.TestSuccessBookkeeping.test_full_refund_sets_status_refunded)
Rule 7: the terminal transition is exactly `refunded`, and it is stored. ... ok
test_partial_refund_result_and_state (test_refunds.TestSuccessBookkeeping.test_partial_refund_result_and_state) ... ok
test_result_has_exactly_the_specified_fields (test_refunds.TestSuccessBookkeeping.test_result_has_exactly_the_specified_fields) ... ok
test_two_partial_refunds_then_fully_refunded (test_refunds.TestSuccessBookkeeping.test_two_partial_refunds_then_fully_refunded) ... ok
test_untouched_order_fields_are_preserved (test_refunds.TestSuccessBookkeeping.test_untouched_order_fields_are_preserved) ... ok

======================================================================
FAIL: test_failed_refund_does_not_poison_a_retry (test_refunds.TestGatewayFailureAtomicity.test_failed_refund_does_not_poison_a_retry)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/AE-neutral-1/test_refunds.py", line 357, in test_failed_refund_does_not_poison_a_retry
    self.assertEqual(order, snapshot)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: {'id'[55 chars]aid': 1000, 'refunded': 1000, 'status': 'refunded', 'keys': {}} != {'id'[55 chars]aid': 1000, 'refunded': 0, 'status': 'paid', 'keys': {}}
  {'charge_id': 'ch_1',
   'id': 'ord_1',
   'keys': {},
   'owner_id': 'cus_1',
   'paid': 1000,
-  'refunded': 1000,
?              ---

+  'refunded': 0,
-  'status': 'refunded'}
?             ^^^^^^^

+  'status': 'paid'}
?             ^^^


======================================================================
FAIL: test_failed_refund_leaves_order_completely_unchanged (test_refunds.TestGatewayFailureAtomicity.test_failed_refund_leaves_order_completely_unchanged)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/AE-neutral-1/test_refunds.py", line 344, in test_failed_refund_leaves_order_completely_unchanged
    self.assertEqual(order, snapshot)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: {'id'[74 chars]ed': 750, 'status': 'partially_refunded', 'key[79 chars]d'}}} != {'id'[74 chars]ed': 250, 'status': 'partially_refunded', 'key[79 chars]d'}}}
  {'charge_id': 'ch_1',
   'id': 'ord_1',
   'keys': {'old': {'amount': 250,
                    'refund_id': 're_old',
                    'status': 'partially_refunded'}},
   'owner_id': 'cus_1',
   'paid': 1000,
-  'refunded': 750,
?              ^

+  'refunded': 250,
?              ^

   'status': 'partially_refunded'}

----------------------------------------------------------------------
Ran 41 tests in 0.002s

FAILED (failures=2)
(exit 1)
$ restored /tmp/aep-lab/pilot/AE-neutral-1/refunds.py from backup (byte-identical)
$ cd /tmp/aep-lab/pilot/AE-neutral-1 && python3 -m unittest discover -s . -p 'test*.py' -v   # expect SUCCESS
test_accepts_one (test_refunds.TestAmountValidation.test_accepts_one) ... ok
test_amount_is_checked_before_permission_and_status (test_refunds.TestAmountValidation.test_amount_is_checked_before_permission_and_status) ... ok
test_rejects_bools (test_refunds.TestAmountValidation.test_rejects_bools) ... ok
test_rejects_floats_even_when_whole (test_refunds.TestAmountValidation.test_rejects_floats_even_when_whole) ... ok
test_rejects_non_numeric_amounts (test_refunds.TestAmountValidation.test_rejects_non_numeric_amounts) ... ok
test_rejects_non_positive_ints (test_refunds.TestAmountValidation.test_rejects_non_positive_ints) ... ok
test_failed_refund_does_not_poison_a_retry (test_refunds.TestGatewayFailureAtomicity.test_failed_refund_does_not_poison_a_retry) ... ok
test_failed_refund_leaves_order_completely_unchanged (test_refunds.TestGatewayFailureAtomicity.test_failed_refund_leaves_order_completely_unchanged) ... ok
test_gateway_is_called_exactly_once_per_refund (test_refunds.TestGatewayFailureAtomicity.test_gateway_is_called_exactly_once_per_refund) ... ok
test_gateway_is_never_called_when_a_rule_rejects (test_refunds.TestGatewayFailureAtomicity.test_gateway_is_never_called_when_a_rule_rejects) ... ok
test_gateway_receives_the_order_charge_id (test_refunds.TestGatewayFailureAtomicity.test_gateway_receives_the_order_charge_id)
Rule 6: the gateway is charged the order's own charge id, not a fixed one. ... ok
test_distinct_keys_each_charge_once (test_refunds.TestIdempotency.test_distinct_keys_each_charge_once) ... ok
test_replay_ignores_a_different_amount_and_does_not_recharge (test_refunds.TestIdempotency.test_replay_ignores_a_different_amount_and_does_not_recharge) ... ok
test_replay_returns_stored_result_without_second_charge (test_refunds.TestIdempotency.test_replay_returns_stored_result_without_second_charge) ... ok
test_replay_uses_membership_not_truthiness (test_refunds.TestIdempotency.test_replay_uses_membership_not_truthiness)
Rule 1 keys on membership: a stored falsy result must still replay. ... ok
test_replay_wins_over_every_other_rule (test_refunds.TestIdempotency.test_replay_wins_over_every_other_rule)
Rule 1 precedes rules 2-5: bad amount, wrong actor, dead status. ... ok
test_actor_without_a_role_is_denied (test_refunds.TestPermission.test_actor_without_a_role_is_denied)
A missing role must fail closed, never default to a privileged one. ... ok
test_admin_and_support_need_not_own_the_order (test_refunds.TestPermission.test_admin_and_support_need_not_own_the_order) ... ok
test_admin_is_allowed (test_refunds.TestPermission.test_admin_is_allowed) ... ok
test_customer_without_matching_id_is_denied (test_refunds.TestPermission.test_customer_without_matching_id_is_denied) ... ok
test_other_customer_is_denied (test_refunds.TestPermission.test_other_customer_is_denied) ... ok
test_owner_customer_is_allowed (test_refunds.TestPermission.test_owner_customer_is_allowed) ... ok
test_owner_with_non_customer_role_is_denied (test_refunds.TestPermission.test_owner_with_non_customer_role_is_denied)
Rule 3 grants the *customer* who owns the order, not any matching id. ... ok
test_permission_is_checked_before_status (test_refunds.TestPermission.test_permission_is_checked_before_status) ... ok
test_support_is_allowed (test_refunds.TestPermission.test_support_is_allowed) ... ok
test_unknown_role_is_denied (test_refunds.TestPermission.test_unknown_role_is_denied) ... ok
test_amount_above_remaining_is_rejected (test_refunds.TestRefundableCap.test_amount_above_remaining_is_rejected) ... ok
test_amount_equal_to_paid_is_rejected_once_partly_refunded (test_refunds.TestRefundableCap.test_amount_equal_to_paid_is_rejected_once_partly_refunded) ... ok
test_exact_remaining_is_allowed (test_refunds.TestRefundableCap.test_exact_remaining_is_allowed) ... ok
test_full_refund_of_untouched_order_is_allowed (test_refunds.TestRefundableCap.test_full_refund_of_untouched_order_is_allowed) ... ok
test_over_refunded_order_rejects_any_amount (test_refunds.TestRefundableCap.test_over_refunded_order_rejects_any_amount)
A negative remainder must still reject every amount, not skip the cap. ... ok
test_cancelled_order_is_rejected (test_refunds.TestStatus.test_cancelled_order_is_rejected) ... ok
test_paid_order_is_accepted (test_refunds.TestStatus.test_paid_order_is_accepted) ... ok
test_partially_refunded_order_is_accepted (test_refunds.TestStatus.test_partially_refunded_order_is_accepted) ... ok
test_refunded_order_is_rejected_even_with_room_on_the_clock (test_refunds.TestStatus.test_refunded_order_is_rejected_even_with_room_on_the_clock) ... ok
test_unknown_status_is_rejected (test_refunds.TestStatus.test_unknown_status_is_rejected) ... ok
test_full_refund_sets_status_refunded (test_refunds.TestSuccessBookkeeping.test_full_refund_sets_status_refunded)
Rule 7: the terminal transition is exactly `refunded`, and it is stored. ... ok
test_partial_refund_result_and_state (test_refunds.TestSuccessBookkeeping.test_partial_refund_result_and_state) ... ok
test_result_has_exactly_the_specified_fields (test_refunds.TestSuccessBookkeeping.test_result_has_exactly_the_specified_fields) ... ok
test_two_partial_refunds_then_fully_refunded (test_refunds.TestSuccessBookkeeping.test_two_partial_refunds_then_fully_refunded) ... ok
test_untouched_order_fields_are_preserved (test_refunds.TestSuccessBookkeeping.test_untouched_order_fields_are_preserved) ... ok

----------------------------------------------------------------------
Ran 41 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```


## 6.11 Negative control: rule 6 — charge-id forwarding

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/AE-neutral-1/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/AE-neutral-1/negcontrol/break_charge_id.py" --test-cmd "cd /tmp/aep-lab/pilot/AE-neutral-1 && python3 -m unittest discover -s . -p 'test*.py' -v" --expect "FAIL: test_gateway_receives_the_order_charge_id" --timeout 20
$ backed up /tmp/aep-lab/pilot/AE-neutral-1/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-z7i7gueo/refunds.py
$ python3 /tmp/aep-lab/pilot/AE-neutral-1/negcontrol/break_charge_id.py
break_charge_id: gateway always charged ch_1
$ cd /tmp/aep-lab/pilot/AE-neutral-1 && python3 -m unittest discover -s . -p 'test*.py' -v   # expect FAILURE matching /FAIL: test_gateway_receives_the_order_charge_id/
test_accepts_one (test_refunds.TestAmountValidation.test_accepts_one) ... ok
test_amount_is_checked_before_permission_and_status (test_refunds.TestAmountValidation.test_amount_is_checked_before_permission_and_status) ... ok
test_rejects_bools (test_refunds.TestAmountValidation.test_rejects_bools) ... ok
test_rejects_floats_even_when_whole (test_refunds.TestAmountValidation.test_rejects_floats_even_when_whole) ... ok
test_rejects_non_numeric_amounts (test_refunds.TestAmountValidation.test_rejects_non_numeric_amounts) ... ok
test_rejects_non_positive_ints (test_refunds.TestAmountValidation.test_rejects_non_positive_ints) ... ok
test_failed_refund_does_not_poison_a_retry (test_refunds.TestGatewayFailureAtomicity.test_failed_refund_does_not_poison_a_retry) ... ok
test_failed_refund_leaves_order_completely_unchanged (test_refunds.TestGatewayFailureAtomicity.test_failed_refund_leaves_order_completely_unchanged) ... ok
test_gateway_is_called_exactly_once_per_refund (test_refunds.TestGatewayFailureAtomicity.test_gateway_is_called_exactly_once_per_refund) ... ok
test_gateway_is_never_called_when_a_rule_rejects (test_refunds.TestGatewayFailureAtomicity.test_gateway_is_never_called_when_a_rule_rejects) ... ok
test_gateway_receives_the_order_charge_id (test_refunds.TestGatewayFailureAtomicity.test_gateway_receives_the_order_charge_id)
Rule 6: the gateway is charged the order's own charge id, not a fixed one. ... FAIL
test_distinct_keys_each_charge_once (test_refunds.TestIdempotency.test_distinct_keys_each_charge_once) ... ok
test_replay_ignores_a_different_amount_and_does_not_recharge (test_refunds.TestIdempotency.test_replay_ignores_a_different_amount_and_does_not_recharge) ... ok
test_replay_returns_stored_result_without_second_charge (test_refunds.TestIdempotency.test_replay_returns_stored_result_without_second_charge) ... ok
test_replay_uses_membership_not_truthiness (test_refunds.TestIdempotency.test_replay_uses_membership_not_truthiness)
Rule 1 keys on membership: a stored falsy result must still replay. ... ok
test_replay_wins_over_every_other_rule (test_refunds.TestIdempotency.test_replay_wins_over_every_other_rule)
Rule 1 precedes rules 2-5: bad amount, wrong actor, dead status. ... ok
test_actor_without_a_role_is_denied (test_refunds.TestPermission.test_actor_without_a_role_is_denied)
A missing role must fail closed, never default to a privileged one. ... ok
test_admin_and_support_need_not_own_the_order (test_refunds.TestPermission.test_admin_and_support_need_not_own_the_order) ... ok
test_admin_is_allowed (test_refunds.TestPermission.test_admin_is_allowed) ... ok
test_customer_without_matching_id_is_denied (test_refunds.TestPermission.test_customer_without_matching_id_is_denied) ... ok
test_other_customer_is_denied (test_refunds.TestPermission.test_other_customer_is_denied) ... ok
test_owner_customer_is_allowed (test_refunds.TestPermission.test_owner_customer_is_allowed) ... ok
test_owner_with_non_customer_role_is_denied (test_refunds.TestPermission.test_owner_with_non_customer_role_is_denied)
Rule 3 grants the *customer* who owns the order, not any matching id. ... ok
test_permission_is_checked_before_status (test_refunds.TestPermission.test_permission_is_checked_before_status) ... ok
test_support_is_allowed (test_refunds.TestPermission.test_support_is_allowed) ... ok
test_unknown_role_is_denied (test_refunds.TestPermission.test_unknown_role_is_denied) ... ok
test_amount_above_remaining_is_rejected (test_refunds.TestRefundableCap.test_amount_above_remaining_is_rejected) ... ok
test_amount_equal_to_paid_is_rejected_once_partly_refunded (test_refunds.TestRefundableCap.test_amount_equal_to_paid_is_rejected_once_partly_refunded) ... ok
test_exact_remaining_is_allowed (test_refunds.TestRefundableCap.test_exact_remaining_is_allowed) ... ok
test_full_refund_of_untouched_order_is_allowed (test_refunds.TestRefundableCap.test_full_refund_of_untouched_order_is_allowed) ... ok
test_over_refunded_order_rejects_any_amount (test_refunds.TestRefundableCap.test_over_refunded_order_rejects_any_amount)
A negative remainder must still reject every amount, not skip the cap. ... ok
test_cancelled_order_is_rejected (test_refunds.TestStatus.test_cancelled_order_is_rejected) ... ok
test_paid_order_is_accepted (test_refunds.TestStatus.test_paid_order_is_accepted) ... ok
test_partially_refunded_order_is_accepted (test_refunds.TestStatus.test_partially_refunded_order_is_accepted) ... ok
test_refunded_order_is_rejected_even_with_room_on_the_clock (test_refunds.TestStatus.test_refunded_order_is_rejected_even_with_room_on_the_clock) ... ok
test_unknown_status_is_rejected (test_refunds.TestStatus.test_unknown_status_is_rejected) ... ok
test_full_refund_sets_status_refunded (test_refunds.TestSuccessBookkeeping.test_full_refund_sets_status_refunded)
Rule 7: the terminal transition is exactly `refunded`, and it is stored. ... ok
test_partial_refund_result_and_state (test_refunds.TestSuccessBookkeeping.test_partial_refund_result_and_state) ... ok
test_result_has_exactly_the_specified_fields (test_refunds.TestSuccessBookkeeping.test_result_has_exactly_the_specified_fields) ... ok
test_two_partial_refunds_then_fully_refunded (test_refunds.TestSuccessBookkeeping.test_two_partial_refunds_then_fully_refunded) ... ok
test_untouched_order_fields_are_preserved (test_refunds.TestSuccessBookkeeping.test_untouched_order_fields_are_preserved) ... ok

======================================================================
FAIL: test_gateway_receives_the_order_charge_id (test_refunds.TestGatewayFailureAtomicity.test_gateway_receives_the_order_charge_id)
Rule 6: the gateway is charged the order's own charge id, not a fixed one.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/AE-neutral-1/test_refunds.py", line 378, in test_gateway_receives_the_order_charge_id
    self.assertEqual(gateway.calls, [("ch_other", 200)])
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: [('ch_1', 200)] != [('ch_other', 200)]

First differing element 0:
('ch_1', 200)
('ch_other', 200)

- [('ch_1', 200)]
?       ^

+ [('ch_other', 200)]
?       ^^^^^


----------------------------------------------------------------------
Ran 41 tests in 0.001s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot/AE-neutral-1/refunds.py from backup (byte-identical)
$ cd /tmp/aep-lab/pilot/AE-neutral-1 && python3 -m unittest discover -s . -p 'test*.py' -v   # expect SUCCESS
test_accepts_one (test_refunds.TestAmountValidation.test_accepts_one) ... ok
test_amount_is_checked_before_permission_and_status (test_refunds.TestAmountValidation.test_amount_is_checked_before_permission_and_status) ... ok
test_rejects_bools (test_refunds.TestAmountValidation.test_rejects_bools) ... ok
test_rejects_floats_even_when_whole (test_refunds.TestAmountValidation.test_rejects_floats_even_when_whole) ... ok
test_rejects_non_numeric_amounts (test_refunds.TestAmountValidation.test_rejects_non_numeric_amounts) ... ok
test_rejects_non_positive_ints (test_refunds.TestAmountValidation.test_rejects_non_positive_ints) ... ok
test_failed_refund_does_not_poison_a_retry (test_refunds.TestGatewayFailureAtomicity.test_failed_refund_does_not_poison_a_retry) ... ok
test_failed_refund_leaves_order_completely_unchanged (test_refunds.TestGatewayFailureAtomicity.test_failed_refund_leaves_order_completely_unchanged) ... ok
test_gateway_is_called_exactly_once_per_refund (test_refunds.TestGatewayFailureAtomicity.test_gateway_is_called_exactly_once_per_refund) ... ok
test_gateway_is_never_called_when_a_rule_rejects (test_refunds.TestGatewayFailureAtomicity.test_gateway_is_never_called_when_a_rule_rejects) ... ok
test_gateway_receives_the_order_charge_id (test_refunds.TestGatewayFailureAtomicity.test_gateway_receives_the_order_charge_id)
Rule 6: the gateway is charged the order's own charge id, not a fixed one. ... ok
test_distinct_keys_each_charge_once (test_refunds.TestIdempotency.test_distinct_keys_each_charge_once) ... ok
test_replay_ignores_a_different_amount_and_does_not_recharge (test_refunds.TestIdempotency.test_replay_ignores_a_different_amount_and_does_not_recharge) ... ok
test_replay_returns_stored_result_without_second_charge (test_refunds.TestIdempotency.test_replay_returns_stored_result_without_second_charge) ... ok
test_replay_uses_membership_not_truthiness (test_refunds.TestIdempotency.test_replay_uses_membership_not_truthiness)
Rule 1 keys on membership: a stored falsy result must still replay. ... ok
test_replay_wins_over_every_other_rule (test_refunds.TestIdempotency.test_replay_wins_over_every_other_rule)
Rule 1 precedes rules 2-5: bad amount, wrong actor, dead status. ... ok
test_actor_without_a_role_is_denied (test_refunds.TestPermission.test_actor_without_a_role_is_denied)
A missing role must fail closed, never default to a privileged one. ... ok
test_admin_and_support_need_not_own_the_order (test_refunds.TestPermission.test_admin_and_support_need_not_own_the_order) ... ok
test_admin_is_allowed (test_refunds.TestPermission.test_admin_is_allowed) ... ok
test_customer_without_matching_id_is_denied (test_refunds.TestPermission.test_customer_without_matching_id_is_denied) ... ok
test_other_customer_is_denied (test_refunds.TestPermission.test_other_customer_is_denied) ... ok
test_owner_customer_is_allowed (test_refunds.TestPermission.test_owner_customer_is_allowed) ... ok
test_owner_with_non_customer_role_is_denied (test_refunds.TestPermission.test_owner_with_non_customer_role_is_denied)
Rule 3 grants the *customer* who owns the order, not any matching id. ... ok
test_permission_is_checked_before_status (test_refunds.TestPermission.test_permission_is_checked_before_status) ... ok
test_support_is_allowed (test_refunds.TestPermission.test_support_is_allowed) ... ok
test_unknown_role_is_denied (test_refunds.TestPermission.test_unknown_role_is_denied) ... ok
test_amount_above_remaining_is_rejected (test_refunds.TestRefundableCap.test_amount_above_remaining_is_rejected) ... ok
test_amount_equal_to_paid_is_rejected_once_partly_refunded (test_refunds.TestRefundableCap.test_amount_equal_to_paid_is_rejected_once_partly_refunded) ... ok
test_exact_remaining_is_allowed (test_refunds.TestRefundableCap.test_exact_remaining_is_allowed) ... ok
test_full_refund_of_untouched_order_is_allowed (test_refunds.TestRefundableCap.test_full_refund_of_untouched_order_is_allowed) ... ok
test_over_refunded_order_rejects_any_amount (test_refunds.TestRefundableCap.test_over_refunded_order_rejects_any_amount)
A negative remainder must still reject every amount, not skip the cap. ... ok
test_cancelled_order_is_rejected (test_refunds.TestStatus.test_cancelled_order_is_rejected) ... ok
test_paid_order_is_accepted (test_refunds.TestStatus.test_paid_order_is_accepted) ... ok
test_partially_refunded_order_is_accepted (test_refunds.TestStatus.test_partially_refunded_order_is_accepted) ... ok
test_refunded_order_is_rejected_even_with_room_on_the_clock (test_refunds.TestStatus.test_refunded_order_is_rejected_even_with_room_on_the_clock) ... ok
test_unknown_status_is_rejected (test_refunds.TestStatus.test_unknown_status_is_rejected) ... ok
test_full_refund_sets_status_refunded (test_refunds.TestSuccessBookkeeping.test_full_refund_sets_status_refunded)
Rule 7: the terminal transition is exactly `refunded`, and it is stored. ... ok
test_partial_refund_result_and_state (test_refunds.TestSuccessBookkeeping.test_partial_refund_result_and_state) ... ok
test_result_has_exactly_the_specified_fields (test_refunds.TestSuccessBookkeeping.test_result_has_exactly_the_specified_fields) ... ok
test_two_partial_refunds_then_fully_refunded (test_refunds.TestSuccessBookkeeping.test_two_partial_refunds_then_fully_refunded) ... ok
test_untouched_order_fields_are_preserved (test_refunds.TestSuccessBookkeeping.test_untouched_order_fields_are_preserved) ... ok

----------------------------------------------------------------------
Ran 41 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```


## 6.12 Negative control: rule 7 — terminal status

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/AE-neutral-1/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/AE-neutral-1/negcontrol/break_rule7_status.py" --test-cmd "cd /tmp/aep-lab/pilot/AE-neutral-1 && python3 -m unittest discover -s . -p 'test*.py' -v" --expect "FAIL: test_full_refund_sets_status_refunded" --timeout 20
$ backed up /tmp/aep-lab/pilot/AE-neutral-1/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-8sbpohpw/refunds.py
$ python3 /tmp/aep-lab/pilot/AE-neutral-1/negcontrol/break_rule7_status.py
break_rule7_status: full refunds stay partially_refunded
$ cd /tmp/aep-lab/pilot/AE-neutral-1 && python3 -m unittest discover -s . -p 'test*.py' -v   # expect FAILURE matching /FAIL: test_full_refund_sets_status_refunded/
test_accepts_one (test_refunds.TestAmountValidation.test_accepts_one) ... ok
test_amount_is_checked_before_permission_and_status (test_refunds.TestAmountValidation.test_amount_is_checked_before_permission_and_status) ... ok
test_rejects_bools (test_refunds.TestAmountValidation.test_rejects_bools) ... ok
test_rejects_floats_even_when_whole (test_refunds.TestAmountValidation.test_rejects_floats_even_when_whole) ... ok
test_rejects_non_numeric_amounts (test_refunds.TestAmountValidation.test_rejects_non_numeric_amounts) ... ok
test_rejects_non_positive_ints (test_refunds.TestAmountValidation.test_rejects_non_positive_ints) ... ok
test_failed_refund_does_not_poison_a_retry (test_refunds.TestGatewayFailureAtomicity.test_failed_refund_does_not_poison_a_retry) ... FAIL
test_failed_refund_leaves_order_completely_unchanged (test_refunds.TestGatewayFailureAtomicity.test_failed_refund_leaves_order_completely_unchanged) ... ok
test_gateway_is_called_exactly_once_per_refund (test_refunds.TestGatewayFailureAtomicity.test_gateway_is_called_exactly_once_per_refund) ... ok
test_gateway_is_never_called_when_a_rule_rejects (test_refunds.TestGatewayFailureAtomicity.test_gateway_is_never_called_when_a_rule_rejects) ... ok
test_gateway_receives_the_order_charge_id (test_refunds.TestGatewayFailureAtomicity.test_gateway_receives_the_order_charge_id)
Rule 6: the gateway is charged the order's own charge id, not a fixed one. ... ok
test_distinct_keys_each_charge_once (test_refunds.TestIdempotency.test_distinct_keys_each_charge_once) ... ok
test_replay_ignores_a_different_amount_and_does_not_recharge (test_refunds.TestIdempotency.test_replay_ignores_a_different_amount_and_does_not_recharge) ... ok
test_replay_returns_stored_result_without_second_charge (test_refunds.TestIdempotency.test_replay_returns_stored_result_without_second_charge) ... ok
test_replay_uses_membership_not_truthiness (test_refunds.TestIdempotency.test_replay_uses_membership_not_truthiness)
Rule 1 keys on membership: a stored falsy result must still replay. ... ok
test_replay_wins_over_every_other_rule (test_refunds.TestIdempotency.test_replay_wins_over_every_other_rule)
Rule 1 precedes rules 2-5: bad amount, wrong actor, dead status. ... ok
test_actor_without_a_role_is_denied (test_refunds.TestPermission.test_actor_without_a_role_is_denied)
A missing role must fail closed, never default to a privileged one. ... ok
test_admin_and_support_need_not_own_the_order (test_refunds.TestPermission.test_admin_and_support_need_not_own_the_order) ... ok
test_admin_is_allowed (test_refunds.TestPermission.test_admin_is_allowed) ... ok
test_customer_without_matching_id_is_denied (test_refunds.TestPermission.test_customer_without_matching_id_is_denied) ... ok
test_other_customer_is_denied (test_refunds.TestPermission.test_other_customer_is_denied) ... ok
test_owner_customer_is_allowed (test_refunds.TestPermission.test_owner_customer_is_allowed) ... ok
test_owner_with_non_customer_role_is_denied (test_refunds.TestPermission.test_owner_with_non_customer_role_is_denied)
Rule 3 grants the *customer* who owns the order, not any matching id. ... ok
test_permission_is_checked_before_status (test_refunds.TestPermission.test_permission_is_checked_before_status) ... ok
test_support_is_allowed (test_refunds.TestPermission.test_support_is_allowed) ... ok
test_unknown_role_is_denied (test_refunds.TestPermission.test_unknown_role_is_denied) ... ok
test_amount_above_remaining_is_rejected (test_refunds.TestRefundableCap.test_amount_above_remaining_is_rejected) ... ok
test_amount_equal_to_paid_is_rejected_once_partly_refunded (test_refunds.TestRefundableCap.test_amount_equal_to_paid_is_rejected_once_partly_refunded) ... ok
test_exact_remaining_is_allowed (test_refunds.TestRefundableCap.test_exact_remaining_is_allowed) ... FAIL
test_full_refund_of_untouched_order_is_allowed (test_refunds.TestRefundableCap.test_full_refund_of_untouched_order_is_allowed) ... FAIL
test_over_refunded_order_rejects_any_amount (test_refunds.TestRefundableCap.test_over_refunded_order_rejects_any_amount)
A negative remainder must still reject every amount, not skip the cap. ... ok
test_cancelled_order_is_rejected (test_refunds.TestStatus.test_cancelled_order_is_rejected) ... ok
test_paid_order_is_accepted (test_refunds.TestStatus.test_paid_order_is_accepted) ... ok
test_partially_refunded_order_is_accepted (test_refunds.TestStatus.test_partially_refunded_order_is_accepted) ... ok
test_refunded_order_is_rejected_even_with_room_on_the_clock (test_refunds.TestStatus.test_refunded_order_is_rejected_even_with_room_on_the_clock) ... ok
test_unknown_status_is_rejected (test_refunds.TestStatus.test_unknown_status_is_rejected) ... ok
test_full_refund_sets_status_refunded (test_refunds.TestSuccessBookkeeping.test_full_refund_sets_status_refunded)
Rule 7: the terminal transition is exactly `refunded`, and it is stored. ... FAIL
test_partial_refund_result_and_state (test_refunds.TestSuccessBookkeeping.test_partial_refund_result_and_state) ... ok
test_result_has_exactly_the_specified_fields (test_refunds.TestSuccessBookkeeping.test_result_has_exactly_the_specified_fields) ... ok
test_two_partial_refunds_then_fully_refunded (test_refunds.TestSuccessBookkeeping.test_two_partial_refunds_then_fully_refunded) ... FAIL
test_untouched_order_fields_are_preserved (test_refunds.TestSuccessBookkeeping.test_untouched_order_fields_are_preserved) ... ok

======================================================================
FAIL: test_failed_refund_does_not_poison_a_retry (test_refunds.TestGatewayFailureAtomicity.test_failed_refund_does_not_poison_a_retry)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/AE-neutral-1/test_refunds.py", line 363, in test_failed_refund_does_not_poison_a_retry
    self.assertEqual(order["status"], "refunded")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'partially_refunded' != 'refunded'
- partially_refunded
+ refunded


======================================================================
FAIL: test_exact_remaining_is_allowed (test_refunds.TestRefundableCap.test_exact_remaining_is_allowed)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/AE-neutral-1/test_refunds.py", line 319, in test_exact_remaining_is_allowed
    self.assertEqual(result["status"], "refunded")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'partially_refunded' != 'refunded'
- partially_refunded
+ refunded


======================================================================
FAIL: test_full_refund_of_untouched_order_is_allowed (test_refunds.TestRefundableCap.test_full_refund_of_untouched_order_is_allowed)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/AE-neutral-1/test_refunds.py", line 327, in test_full_refund_of_untouched_order_is_allowed
    self.assertEqual(result["status"], "refunded")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'partially_refunded' != 'refunded'
- partially_refunded
+ refunded


======================================================================
FAIL: test_full_refund_sets_status_refunded (test_refunds.TestSuccessBookkeeping.test_full_refund_sets_status_refunded)
Rule 7: the terminal transition is exactly `refunded`, and it is stored.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/AE-neutral-1/test_refunds.py", line 433, in test_full_refund_sets_status_refunded
    self.assertEqual(
    ~~~~~~~~~~~~~~~~^
        result,
        ^^^^^^^
        {"refund_id": "re_full", "amount": 1000, "status": "refunded"},
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
AssertionError: {'refund_id': 're_full', 'amount': 1000, 'status': 'partially_refunded'} != {'refund_id': 're_full', 'amount': 1000, 'status': 'refunded'}
- {'amount': 1000, 'refund_id': 're_full', 'status': 'partially_refunded'}
?                                                     ----------

+ {'amount': 1000, 'refund_id': 're_full', 'status': 'refunded'}

======================================================================
FAIL: test_two_partial_refunds_then_fully_refunded (test_refunds.TestSuccessBookkeeping.test_two_partial_refunds_then_fully_refunded)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/AE-neutral-1/test_refunds.py", line 423, in test_two_partial_refunds_then_fully_refunded
    self.assertEqual(result["status"], "refunded")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'partially_refunded' != 'refunded'
- partially_refunded
+ refunded


----------------------------------------------------------------------
Ran 41 tests in 0.002s

FAILED (failures=5)
(exit 1)
$ restored /tmp/aep-lab/pilot/AE-neutral-1/refunds.py from backup (byte-identical)
$ cd /tmp/aep-lab/pilot/AE-neutral-1 && python3 -m unittest discover -s . -p 'test*.py' -v   # expect SUCCESS
test_accepts_one (test_refunds.TestAmountValidation.test_accepts_one) ... ok
test_amount_is_checked_before_permission_and_status (test_refunds.TestAmountValidation.test_amount_is_checked_before_permission_and_status) ... ok
test_rejects_bools (test_refunds.TestAmountValidation.test_rejects_bools) ... ok
test_rejects_floats_even_when_whole (test_refunds.TestAmountValidation.test_rejects_floats_even_when_whole) ... ok
test_rejects_non_numeric_amounts (test_refunds.TestAmountValidation.test_rejects_non_numeric_amounts) ... ok
test_rejects_non_positive_ints (test_refunds.TestAmountValidation.test_rejects_non_positive_ints) ... ok
test_failed_refund_does_not_poison_a_retry (test_refunds.TestGatewayFailureAtomicity.test_failed_refund_does_not_poison_a_retry) ... ok
test_failed_refund_leaves_order_completely_unchanged (test_refunds.TestGatewayFailureAtomicity.test_failed_refund_leaves_order_completely_unchanged) ... ok
test_gateway_is_called_exactly_once_per_refund (test_refunds.TestGatewayFailureAtomicity.test_gateway_is_called_exactly_once_per_refund) ... ok
test_gateway_is_never_called_when_a_rule_rejects (test_refunds.TestGatewayFailureAtomicity.test_gateway_is_never_called_when_a_rule_rejects) ... ok
test_gateway_receives_the_order_charge_id (test_refunds.TestGatewayFailureAtomicity.test_gateway_receives_the_order_charge_id)
Rule 6: the gateway is charged the order's own charge id, not a fixed one. ... ok
test_distinct_keys_each_charge_once (test_refunds.TestIdempotency.test_distinct_keys_each_charge_once) ... ok
test_replay_ignores_a_different_amount_and_does_not_recharge (test_refunds.TestIdempotency.test_replay_ignores_a_different_amount_and_does_not_recharge) ... ok
test_replay_returns_stored_result_without_second_charge (test_refunds.TestIdempotency.test_replay_returns_stored_result_without_second_charge) ... ok
test_replay_uses_membership_not_truthiness (test_refunds.TestIdempotency.test_replay_uses_membership_not_truthiness)
Rule 1 keys on membership: a stored falsy result must still replay. ... ok
test_replay_wins_over_every_other_rule (test_refunds.TestIdempotency.test_replay_wins_over_every_other_rule)
Rule 1 precedes rules 2-5: bad amount, wrong actor, dead status. ... ok
test_actor_without_a_role_is_denied (test_refunds.TestPermission.test_actor_without_a_role_is_denied)
A missing role must fail closed, never default to a privileged one. ... ok
test_admin_and_support_need_not_own_the_order (test_refunds.TestPermission.test_admin_and_support_need_not_own_the_order) ... ok
test_admin_is_allowed (test_refunds.TestPermission.test_admin_is_allowed) ... ok
test_customer_without_matching_id_is_denied (test_refunds.TestPermission.test_customer_without_matching_id_is_denied) ... ok
test_other_customer_is_denied (test_refunds.TestPermission.test_other_customer_is_denied) ... ok
test_owner_customer_is_allowed (test_refunds.TestPermission.test_owner_customer_is_allowed) ... ok
test_owner_with_non_customer_role_is_denied (test_refunds.TestPermission.test_owner_with_non_customer_role_is_denied)
Rule 3 grants the *customer* who owns the order, not any matching id. ... ok
test_permission_is_checked_before_status (test_refunds.TestPermission.test_permission_is_checked_before_status) ... ok
test_support_is_allowed (test_refunds.TestPermission.test_support_is_allowed) ... ok
test_unknown_role_is_denied (test_refunds.TestPermission.test_unknown_role_is_denied) ... ok
test_amount_above_remaining_is_rejected (test_refunds.TestRefundableCap.test_amount_above_remaining_is_rejected) ... ok
test_amount_equal_to_paid_is_rejected_once_partly_refunded (test_refunds.TestRefundableCap.test_amount_equal_to_paid_is_rejected_once_partly_refunded) ... ok
test_exact_remaining_is_allowed (test_refunds.TestRefundableCap.test_exact_remaining_is_allowed) ... ok
test_full_refund_of_untouched_order_is_allowed (test_refunds.TestRefundableCap.test_full_refund_of_untouched_order_is_allowed) ... ok
test_over_refunded_order_rejects_any_amount (test_refunds.TestRefundableCap.test_over_refunded_order_rejects_any_amount)
A negative remainder must still reject every amount, not skip the cap. ... ok
test_cancelled_order_is_rejected (test_refunds.TestStatus.test_cancelled_order_is_rejected) ... ok
test_paid_order_is_accepted (test_refunds.TestStatus.test_paid_order_is_accepted) ... ok
test_partially_refunded_order_is_accepted (test_refunds.TestStatus.test_partially_refunded_order_is_accepted) ... ok
test_refunded_order_is_rejected_even_with_room_on_the_clock (test_refunds.TestStatus.test_refunded_order_is_rejected_even_with_room_on_the_clock) ... ok
test_unknown_status_is_rejected (test_refunds.TestStatus.test_unknown_status_is_rejected) ... ok
test_full_refund_sets_status_refunded (test_refunds.TestSuccessBookkeeping.test_full_refund_sets_status_refunded)
Rule 7: the terminal transition is exactly `refunded`, and it is stored. ... ok
test_partial_refund_result_and_state (test_refunds.TestSuccessBookkeeping.test_partial_refund_result_and_state) ... ok
test_result_has_exactly_the_specified_fields (test_refunds.TestSuccessBookkeeping.test_result_has_exactly_the_specified_fields) ... ok
test_two_partial_refunds_then_fully_refunded (test_refunds.TestSuccessBookkeeping.test_two_partial_refunds_then_fully_refunded) ... ok
test_untouched_order_fields_are_preserved (test_refunds.TestSuccessBookkeeping.test_untouched_order_fields_are_preserved) ... ok

----------------------------------------------------------------------
Ran 41 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```


## 6.13 Negative control: rule 7 — result persistence

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/AE-neutral-1/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/AE-neutral-1/negcontrol/break_rule7_keys.py" --test-cmd "cd /tmp/aep-lab/pilot/AE-neutral-1 && python3 -m unittest discover -s . -p 'test*.py' -v" --expect "FAIL: test_replay_returns_stored_result_without_second_charge" --timeout 20
$ backed up /tmp/aep-lab/pilot/AE-neutral-1/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-pfa_eprr/refunds.py
$ python3 /tmp/aep-lab/pilot/AE-neutral-1/negcontrol/break_rule7_keys.py
break_rule7_keys: results are no longer stored
$ cd /tmp/aep-lab/pilot/AE-neutral-1 && python3 -m unittest discover -s . -p 'test*.py' -v   # expect FAILURE matching /FAIL: test_replay_returns_stored_result_without_second_charge/
test_accepts_one (test_refunds.TestAmountValidation.test_accepts_one) ... ok
test_amount_is_checked_before_permission_and_status (test_refunds.TestAmountValidation.test_amount_is_checked_before_permission_and_status) ... ok
test_rejects_bools (test_refunds.TestAmountValidation.test_rejects_bools) ... ok
test_rejects_floats_even_when_whole (test_refunds.TestAmountValidation.test_rejects_floats_even_when_whole) ... ok
test_rejects_non_numeric_amounts (test_refunds.TestAmountValidation.test_rejects_non_numeric_amounts) ... ok
test_rejects_non_positive_ints (test_refunds.TestAmountValidation.test_rejects_non_positive_ints) ... ok
test_failed_refund_does_not_poison_a_retry (test_refunds.TestGatewayFailureAtomicity.test_failed_refund_does_not_poison_a_retry) ... ERROR
test_failed_refund_leaves_order_completely_unchanged (test_refunds.TestGatewayFailureAtomicity.test_failed_refund_leaves_order_completely_unchanged) ... ok
test_gateway_is_called_exactly_once_per_refund (test_refunds.TestGatewayFailureAtomicity.test_gateway_is_called_exactly_once_per_refund) ... ok
test_gateway_is_never_called_when_a_rule_rejects (test_refunds.TestGatewayFailureAtomicity.test_gateway_is_never_called_when_a_rule_rejects) ... ok
test_gateway_receives_the_order_charge_id (test_refunds.TestGatewayFailureAtomicity.test_gateway_receives_the_order_charge_id)
Rule 6: the gateway is charged the order's own charge id, not a fixed one. ... ok
test_distinct_keys_each_charge_once (test_refunds.TestIdempotency.test_distinct_keys_each_charge_once) ... FAIL
test_replay_ignores_a_different_amount_and_does_not_recharge (test_refunds.TestIdempotency.test_replay_ignores_a_different_amount_and_does_not_recharge) ... ERROR
test_replay_returns_stored_result_without_second_charge (test_refunds.TestIdempotency.test_replay_returns_stored_result_without_second_charge) ... FAIL
test_replay_uses_membership_not_truthiness (test_refunds.TestIdempotency.test_replay_uses_membership_not_truthiness)
Rule 1 keys on membership: a stored falsy result must still replay. ... ok
test_replay_wins_over_every_other_rule (test_refunds.TestIdempotency.test_replay_wins_over_every_other_rule)
Rule 1 precedes rules 2-5: bad amount, wrong actor, dead status. ... ok
test_actor_without_a_role_is_denied (test_refunds.TestPermission.test_actor_without_a_role_is_denied)
A missing role must fail closed, never default to a privileged one. ... ok
test_admin_and_support_need_not_own_the_order (test_refunds.TestPermission.test_admin_and_support_need_not_own_the_order) ... ok
test_admin_is_allowed (test_refunds.TestPermission.test_admin_is_allowed) ... ok
test_customer_without_matching_id_is_denied (test_refunds.TestPermission.test_customer_without_matching_id_is_denied) ... ok
test_other_customer_is_denied (test_refunds.TestPermission.test_other_customer_is_denied) ... ok
test_owner_customer_is_allowed (test_refunds.TestPermission.test_owner_customer_is_allowed) ... ok
test_owner_with_non_customer_role_is_denied (test_refunds.TestPermission.test_owner_with_non_customer_role_is_denied)
Rule 3 grants the *customer* who owns the order, not any matching id. ... ok
test_permission_is_checked_before_status (test_refunds.TestPermission.test_permission_is_checked_before_status) ... ok
test_support_is_allowed (test_refunds.TestPermission.test_support_is_allowed) ... ok
test_unknown_role_is_denied (test_refunds.TestPermission.test_unknown_role_is_denied) ... ok
test_amount_above_remaining_is_rejected (test_refunds.TestRefundableCap.test_amount_above_remaining_is_rejected) ... ok
test_amount_equal_to_paid_is_rejected_once_partly_refunded (test_refunds.TestRefundableCap.test_amount_equal_to_paid_is_rejected_once_partly_refunded) ... ok
test_exact_remaining_is_allowed (test_refunds.TestRefundableCap.test_exact_remaining_is_allowed) ... ok
test_full_refund_of_untouched_order_is_allowed (test_refunds.TestRefundableCap.test_full_refund_of_untouched_order_is_allowed) ... ok
test_over_refunded_order_rejects_any_amount (test_refunds.TestRefundableCap.test_over_refunded_order_rejects_any_amount)
A negative remainder must still reject every amount, not skip the cap. ... ok
test_cancelled_order_is_rejected (test_refunds.TestStatus.test_cancelled_order_is_rejected) ... ok
test_paid_order_is_accepted (test_refunds.TestStatus.test_paid_order_is_accepted) ... ok
test_partially_refunded_order_is_accepted (test_refunds.TestStatus.test_partially_refunded_order_is_accepted) ... ok
test_refunded_order_is_rejected_even_with_room_on_the_clock (test_refunds.TestStatus.test_refunded_order_is_rejected_even_with_room_on_the_clock) ... ok
test_unknown_status_is_rejected (test_refunds.TestStatus.test_unknown_status_is_rejected) ... ok
test_full_refund_sets_status_refunded (test_refunds.TestSuccessBookkeeping.test_full_refund_sets_status_refunded)
Rule 7: the terminal transition is exactly `refunded`, and it is stored. ... ERROR
test_partial_refund_result_and_state (test_refunds.TestSuccessBookkeeping.test_partial_refund_result_and_state) ... ERROR
test_result_has_exactly_the_specified_fields (test_refunds.TestSuccessBookkeeping.test_result_has_exactly_the_specified_fields) ... ok
test_two_partial_refunds_then_fully_refunded (test_refunds.TestSuccessBookkeeping.test_two_partial_refunds_then_fully_refunded) ... ok
test_untouched_order_fields_are_preserved (test_refunds.TestSuccessBookkeeping.test_untouched_order_fields_are_preserved) ... ok

======================================================================
ERROR: test_failed_refund_does_not_poison_a_retry (test_refunds.TestGatewayFailureAtomicity.test_failed_refund_does_not_poison_a_retry)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/AE-neutral-1/test_refunds.py", line 364, in test_failed_refund_does_not_poison_a_retry
    self.assertEqual(order["keys"]["key-1"], result)
                     ~~~~~~~~~~~~~^^^^^^^^^
KeyError: 'key-1'

======================================================================
ERROR: test_replay_ignores_a_different_amount_and_does_not_recharge (test_refunds.TestIdempotency.test_replay_ignores_a_different_amount_and_does_not_recharge)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/AE-neutral-1/test_refunds.py", line 68, in test_replay_ignores_a_different_amount_and_does_not_recharge
    second = refund(order, 999, gateway, OWNER, "key-1")
  File "/private/tmp/aep-lab/pilot/AE-neutral-1/refunds.py", line 60, in refund
    raise ValueError(
        "amount %r exceeds refundable remainder %r" % (amount, remaining)
    )
ValueError: amount 999 exceeds refundable remainder 600

======================================================================
ERROR: test_full_refund_sets_status_refunded (test_refunds.TestSuccessBookkeeping.test_full_refund_sets_status_refunded)
Rule 7: the terminal transition is exactly `refunded`, and it is stored.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/AE-neutral-1/test_refunds.py", line 439, in test_full_refund_sets_status_refunded
    self.assertEqual(order["keys"]["key-full"], result)
                     ~~~~~~~~~~~~~^^^^^^^^^^^^
KeyError: 'key-full'

======================================================================
ERROR: test_partial_refund_result_and_state (test_refunds.TestSuccessBookkeeping.test_partial_refund_result_and_state)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/AE-neutral-1/test_refunds.py", line 411, in test_partial_refund_result_and_state
    self.assertEqual(order["keys"]["key-1"], result)
                     ~~~~~~~~~~~~~^^^^^^^^^
KeyError: 'key-1'

======================================================================
FAIL: test_distinct_keys_each_charge_once (test_refunds.TestIdempotency.test_distinct_keys_each_charge_once)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/AE-neutral-1/test_refunds.py", line 118, in test_distinct_keys_each_charge_once
    self.assertEqual(sorted(order["keys"]), ["key-1", "key-2"])
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: [] != ['key-1', 'key-2']

Second list contains 2 additional elements.
First extra element 0:
'key-1'

- []
+ ['key-1', 'key-2']

======================================================================
FAIL: test_replay_returns_stored_result_without_second_charge (test_refunds.TestIdempotency.test_replay_returns_stored_result_without_second_charge)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot/AE-neutral-1/test_refunds.py", line 58, in test_replay_returns_stored_result_without_second_charge
    self.assertEqual(len(gateway.calls), 1)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 2 != 1

----------------------------------------------------------------------
Ran 41 tests in 0.002s

FAILED (failures=2, errors=4)
(exit 1)
$ restored /tmp/aep-lab/pilot/AE-neutral-1/refunds.py from backup (byte-identical)
$ cd /tmp/aep-lab/pilot/AE-neutral-1 && python3 -m unittest discover -s . -p 'test*.py' -v   # expect SUCCESS
test_accepts_one (test_refunds.TestAmountValidation.test_accepts_one) ... ok
test_amount_is_checked_before_permission_and_status (test_refunds.TestAmountValidation.test_amount_is_checked_before_permission_and_status) ... ok
test_rejects_bools (test_refunds.TestAmountValidation.test_rejects_bools) ... ok
test_rejects_floats_even_when_whole (test_refunds.TestAmountValidation.test_rejects_floats_even_when_whole) ... ok
test_rejects_non_numeric_amounts (test_refunds.TestAmountValidation.test_rejects_non_numeric_amounts) ... ok
test_rejects_non_positive_ints (test_refunds.TestAmountValidation.test_rejects_non_positive_ints) ... ok
test_failed_refund_does_not_poison_a_retry (test_refunds.TestGatewayFailureAtomicity.test_failed_refund_does_not_poison_a_retry) ... ok
test_failed_refund_leaves_order_completely_unchanged (test_refunds.TestGatewayFailureAtomicity.test_failed_refund_leaves_order_completely_unchanged) ... ok
test_gateway_is_called_exactly_once_per_refund (test_refunds.TestGatewayFailureAtomicity.test_gateway_is_called_exactly_once_per_refund) ... ok
test_gateway_is_never_called_when_a_rule_rejects (test_refunds.TestGatewayFailureAtomicity.test_gateway_is_never_called_when_a_rule_rejects) ... ok
test_gateway_receives_the_order_charge_id (test_refunds.TestGatewayFailureAtomicity.test_gateway_receives_the_order_charge_id)
Rule 6: the gateway is charged the order's own charge id, not a fixed one. ... ok
test_distinct_keys_each_charge_once (test_refunds.TestIdempotency.test_distinct_keys_each_charge_once) ... ok
test_replay_ignores_a_different_amount_and_does_not_recharge (test_refunds.TestIdempotency.test_replay_ignores_a_different_amount_and_does_not_recharge) ... ok
test_replay_returns_stored_result_without_second_charge (test_refunds.TestIdempotency.test_replay_returns_stored_result_without_second_charge) ... ok
test_replay_uses_membership_not_truthiness (test_refunds.TestIdempotency.test_replay_uses_membership_not_truthiness)
Rule 1 keys on membership: a stored falsy result must still replay. ... ok
test_replay_wins_over_every_other_rule (test_refunds.TestIdempotency.test_replay_wins_over_every_other_rule)
Rule 1 precedes rules 2-5: bad amount, wrong actor, dead status. ... ok
test_actor_without_a_role_is_denied (test_refunds.TestPermission.test_actor_without_a_role_is_denied)
A missing role must fail closed, never default to a privileged one. ... ok
test_admin_and_support_need_not_own_the_order (test_refunds.TestPermission.test_admin_and_support_need_not_own_the_order) ... ok
test_admin_is_allowed (test_refunds.TestPermission.test_admin_is_allowed) ... ok
test_customer_without_matching_id_is_denied (test_refunds.TestPermission.test_customer_without_matching_id_is_denied) ... ok
test_other_customer_is_denied (test_refunds.TestPermission.test_other_customer_is_denied) ... ok
test_owner_customer_is_allowed (test_refunds.TestPermission.test_owner_customer_is_allowed) ... ok
test_owner_with_non_customer_role_is_denied (test_refunds.TestPermission.test_owner_with_non_customer_role_is_denied)
Rule 3 grants the *customer* who owns the order, not any matching id. ... ok
test_permission_is_checked_before_status (test_refunds.TestPermission.test_permission_is_checked_before_status) ... ok
test_support_is_allowed (test_refunds.TestPermission.test_support_is_allowed) ... ok
test_unknown_role_is_denied (test_refunds.TestPermission.test_unknown_role_is_denied) ... ok
test_amount_above_remaining_is_rejected (test_refunds.TestRefundableCap.test_amount_above_remaining_is_rejected) ... ok
test_amount_equal_to_paid_is_rejected_once_partly_refunded (test_refunds.TestRefundableCap.test_amount_equal_to_paid_is_rejected_once_partly_refunded) ... ok
test_exact_remaining_is_allowed (test_refunds.TestRefundableCap.test_exact_remaining_is_allowed) ... ok
test_full_refund_of_untouched_order_is_allowed (test_refunds.TestRefundableCap.test_full_refund_of_untouched_order_is_allowed) ... ok
test_over_refunded_order_rejects_any_amount (test_refunds.TestRefundableCap.test_over_refunded_order_rejects_any_amount)
A negative remainder must still reject every amount, not skip the cap. ... ok
test_cancelled_order_is_rejected (test_refunds.TestStatus.test_cancelled_order_is_rejected) ... ok
test_paid_order_is_accepted (test_refunds.TestStatus.test_paid_order_is_accepted) ... ok
test_partially_refunded_order_is_accepted (test_refunds.TestStatus.test_partially_refunded_order_is_accepted) ... ok
test_refunded_order_is_rejected_even_with_room_on_the_clock (test_refunds.TestStatus.test_refunded_order_is_rejected_even_with_room_on_the_clock) ... ok
test_unknown_status_is_rejected (test_refunds.TestStatus.test_unknown_status_is_rejected) ... ok
test_full_refund_sets_status_refunded (test_refunds.TestSuccessBookkeeping.test_full_refund_sets_status_refunded)
Rule 7: the terminal transition is exactly `refunded`, and it is stored. ... ok
test_partial_refund_result_and_state (test_refunds.TestSuccessBookkeeping.test_partial_refund_result_and_state) ... ok
test_result_has_exactly_the_specified_fields (test_refunds.TestSuccessBookkeeping.test_result_has_exactly_the_specified_fields) ... ok
test_two_partial_refunds_then_fully_refunded (test_refunds.TestSuccessBookkeeping.test_two_partial_refunds_then_fully_refunded) ... ok
test_untouched_order_fields_are_preserved (test_refunds.TestSuccessBookkeeping.test_untouched_order_fields_are_preserved) ... ok

----------------------------------------------------------------------
Ran 41 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```


## 7. Full unit suite, after all controls and restores

```console
$ cd /tmp/aep-lab/pilot/AE-neutral-1 && python3 -m unittest discover -s . -p 'test*.py' -v
test_accepts_one (test_refunds.TestAmountValidation.test_accepts_one) ... ok
test_amount_is_checked_before_permission_and_status (test_refunds.TestAmountValidation.test_amount_is_checked_before_permission_and_status) ... ok
test_rejects_bools (test_refunds.TestAmountValidation.test_rejects_bools) ... ok
test_rejects_floats_even_when_whole (test_refunds.TestAmountValidation.test_rejects_floats_even_when_whole) ... ok
test_rejects_non_numeric_amounts (test_refunds.TestAmountValidation.test_rejects_non_numeric_amounts) ... ok
test_rejects_non_positive_ints (test_refunds.TestAmountValidation.test_rejects_non_positive_ints) ... ok
test_failed_refund_does_not_poison_a_retry (test_refunds.TestGatewayFailureAtomicity.test_failed_refund_does_not_poison_a_retry) ... ok
test_failed_refund_leaves_order_completely_unchanged (test_refunds.TestGatewayFailureAtomicity.test_failed_refund_leaves_order_completely_unchanged) ... ok
test_gateway_is_called_exactly_once_per_refund (test_refunds.TestGatewayFailureAtomicity.test_gateway_is_called_exactly_once_per_refund) ... ok
test_gateway_is_never_called_when_a_rule_rejects (test_refunds.TestGatewayFailureAtomicity.test_gateway_is_never_called_when_a_rule_rejects) ... ok
test_gateway_receives_the_order_charge_id (test_refunds.TestGatewayFailureAtomicity.test_gateway_receives_the_order_charge_id)
Rule 6: the gateway is charged the order's own charge id, not a fixed one. ... ok
test_distinct_keys_each_charge_once (test_refunds.TestIdempotency.test_distinct_keys_each_charge_once) ... ok
test_replay_ignores_a_different_amount_and_does_not_recharge (test_refunds.TestIdempotency.test_replay_ignores_a_different_amount_and_does_not_recharge) ... ok
test_replay_returns_stored_result_without_second_charge (test_refunds.TestIdempotency.test_replay_returns_stored_result_without_second_charge) ... ok
test_replay_uses_membership_not_truthiness (test_refunds.TestIdempotency.test_replay_uses_membership_not_truthiness)
Rule 1 keys on membership: a stored falsy result must still replay. ... ok
test_replay_wins_over_every_other_rule (test_refunds.TestIdempotency.test_replay_wins_over_every_other_rule)
Rule 1 precedes rules 2-5: bad amount, wrong actor, dead status. ... ok
test_actor_without_a_role_is_denied (test_refunds.TestPermission.test_actor_without_a_role_is_denied)
A missing role must fail closed, never default to a privileged one. ... ok
test_admin_and_support_need_not_own_the_order (test_refunds.TestPermission.test_admin_and_support_need_not_own_the_order) ... ok
test_admin_is_allowed (test_refunds.TestPermission.test_admin_is_allowed) ... ok
test_customer_without_matching_id_is_denied (test_refunds.TestPermission.test_customer_without_matching_id_is_denied) ... ok
test_other_customer_is_denied (test_refunds.TestPermission.test_other_customer_is_denied) ... ok
test_owner_customer_is_allowed (test_refunds.TestPermission.test_owner_customer_is_allowed) ... ok
test_owner_with_non_customer_role_is_denied (test_refunds.TestPermission.test_owner_with_non_customer_role_is_denied)
Rule 3 grants the *customer* who owns the order, not any matching id. ... ok
test_permission_is_checked_before_status (test_refunds.TestPermission.test_permission_is_checked_before_status) ... ok
test_support_is_allowed (test_refunds.TestPermission.test_support_is_allowed) ... ok
test_unknown_role_is_denied (test_refunds.TestPermission.test_unknown_role_is_denied) ... ok
test_amount_above_remaining_is_rejected (test_refunds.TestRefundableCap.test_amount_above_remaining_is_rejected) ... ok
test_amount_equal_to_paid_is_rejected_once_partly_refunded (test_refunds.TestRefundableCap.test_amount_equal_to_paid_is_rejected_once_partly_refunded) ... ok
test_exact_remaining_is_allowed (test_refunds.TestRefundableCap.test_exact_remaining_is_allowed) ... ok
test_full_refund_of_untouched_order_is_allowed (test_refunds.TestRefundableCap.test_full_refund_of_untouched_order_is_allowed) ... ok
test_over_refunded_order_rejects_any_amount (test_refunds.TestRefundableCap.test_over_refunded_order_rejects_any_amount)
A negative remainder must still reject every amount, not skip the cap. ... ok
test_cancelled_order_is_rejected (test_refunds.TestStatus.test_cancelled_order_is_rejected) ... ok
test_paid_order_is_accepted (test_refunds.TestStatus.test_paid_order_is_accepted) ... ok
test_partially_refunded_order_is_accepted (test_refunds.TestStatus.test_partially_refunded_order_is_accepted) ... ok
test_refunded_order_is_rejected_even_with_room_on_the_clock (test_refunds.TestStatus.test_refunded_order_is_rejected_even_with_room_on_the_clock) ... ok
test_unknown_status_is_rejected (test_refunds.TestStatus.test_unknown_status_is_rejected) ... ok
test_full_refund_sets_status_refunded (test_refunds.TestSuccessBookkeeping.test_full_refund_sets_status_refunded)
Rule 7: the terminal transition is exactly `refunded`, and it is stored. ... ok
test_partial_refund_result_and_state (test_refunds.TestSuccessBookkeeping.test_partial_refund_result_and_state) ... ok
test_result_has_exactly_the_specified_fields (test_refunds.TestSuccessBookkeeping.test_result_has_exactly_the_specified_fields) ... ok
test_two_partial_refunds_then_fully_refunded (test_refunds.TestSuccessBookkeeping.test_two_partial_refunds_then_fully_refunded) ... ok
test_untouched_order_fields_are_preserved (test_refunds.TestSuccessBookkeeping.test_untouched_order_fields_are_preserved) ... ok

----------------------------------------------------------------------
Ran 41 tests in 0.001s

OK
(exit 0)
```


## 8. refunds.py contains no leftover break markers

```console
$ grep -n negcontrol /tmp/aep-lab/pilot/AE-neutral-1/refunds.py || echo 'no residue: refunds.py is clean'
no residue: refunds.py is clean
(exit 0)
```


## 9. Hashes of the two files under review

```console
$ shasum -a 256 /tmp/aep-lab/pilot/AE-neutral-1/refunds.py /tmp/aep-lab/pilot/AE-neutral-1/test_refunds.py
731640303a4770d58229049611ff28c53e9dfa94179c77cb6682fc4390c7849b  /tmp/aep-lab/pilot/AE-neutral-1/refunds.py
af0343f2a55ece5273ca077c51bd5bae9f428def10b16991528885872323be24  /tmp/aep-lab/pilot/AE-neutral-1/test_refunds.py
(exit 0)
```


## 10. Line counts

```console
$ wc -l /tmp/aep-lab/pilot/AE-neutral-1/refunds.py /tmp/aep-lab/pilot/AE-neutral-1/test_refunds.py /tmp/aep-lab/pilot/AE-neutral-1/negcontrol-log.md
      75 /tmp/aep-lab/pilot/AE-neutral-1/refunds.py
     452 /tmp/aep-lab/pilot/AE-neutral-1/test_refunds.py
    2432 /tmp/aep-lab/pilot/AE-neutral-1/negcontrol-log.md
    2959 total
(exit 0)
```


## 11. The exact acceptance command from the task, final run

```console
$ cd /tmp/aep-lab/pilot/AE-neutral-1 && python3 -m unittest discover -s . -p 'test*.py' 2>&1 | tail -3
Ran 41 tests in 0.001s

OK
(exit 0)
```


## 12. Coverage matrix

Generated from the runs above; every `aepkit exit` cell is the exit code captured in section 6.

| Rule | Guards pinned | Tests that pin them | Negative controls | aepkit exit |
|------|---------------|---------------------|-------------------|-------------|
| rule 1 — replay a seen key | membership test + stored result returned unchanged | test_replay_returns_stored_result_without_second_charge, test_replay_ignores_a_different_amount_and_does_not_recharge, test_replay_wins_over_every_other_rule, test_replay_uses_membership_not_truthiness | break_idempotency.py, break_keys_truthiness.py | break_idempotency.py=0, break_keys_truthiness.py=0 |
| rule 2 — amount is a positive int | bool, float, zero, negative, non-numeric | test_rejects_non_positive_ints, test_rejects_floats_even_when_whole, test_rejects_bools, test_rejects_non_numeric_amounts, test_accepts_one | break_amount.py | break_amount.py=0 |
| rule 3 — who may refund | admin, support, owning customer; owner must hold role customer; missing role fails closed | test_owner_customer_is_allowed, test_admin_is_allowed, test_support_is_allowed, test_other_customer_is_denied, test_unknown_role_is_denied, test_customer_without_matching_id_is_denied, test_owner_with_non_customer_role_is_denied, test_actor_without_a_role_is_denied | break_permission.py, break_owner_role.py, break_actor_no_role.py | break_permission.py=0, break_owner_role.py=0, break_actor_no_role.py=0 |
| rule 4 — status must be refundable | paid / partially_refunded only | test_cancelled_order_is_rejected, test_refunded_order_is_rejected_even_with_room_on_the_clock, test_unknown_status_is_rejected, test_paid_order_is_accepted, test_partially_refunded_order_is_accepted | break_status.py | break_status.py=0 |
| rule 5 — refundable cap | amount <= paid - refunded, including a negative remainder | test_amount_above_remaining_is_rejected, test_amount_equal_to_paid_is_rejected_once_partly_refunded, test_exact_remaining_is_allowed, test_full_refund_of_untouched_order_is_allowed, test_over_refunded_order_rejects_any_amount | break_cap.py, break_cap_over_refunded.py | break_cap.py=0, break_cap_over_refunded.py=0 |
| rule 6 — one gateway call, atomic on failure | exactly once, order's own charge id, order untouched on GatewayError | test_failed_refund_leaves_order_completely_unchanged, test_failed_refund_does_not_poison_a_retry, test_gateway_is_called_exactly_once_per_refund, test_gateway_receives_the_order_charge_id, test_gateway_is_never_called_when_a_rule_rejects | break_atomicity.py, break_charge_id.py | break_atomicity.py=0, break_charge_id.py=0 |
| rule 7 — success bookkeeping | refunded += amount, terminal status, result stored under the key | test_partial_refund_result_and_state, test_result_has_exactly_the_specified_fields, test_two_partial_refunds_then_fully_refunded, test_full_refund_sets_status_refunded, test_untouched_order_fields_are_preserved | break_rule7_status.py, break_rule7_keys.py | break_rule7_status.py=0, break_rule7_keys.py=0 |


## 13. Verdict

PASS. The 41-test suite is green, all thirteen negative controls exit 0 (suite fails with the named test under the break, and passes again after `aepkit` restores `refunds.py` from its backup), and every rule in the spec has at least one control whose `--expect` names a dedicated test. `refunds.py` is byte-identical to the file the audit reviewed, so the round-1 conformance finding still stands and the gaps the audit listed (F1, F2, F3, F4, F5, F6) are now pinned by tests.
