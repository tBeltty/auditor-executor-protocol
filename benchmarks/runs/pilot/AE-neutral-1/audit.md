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
