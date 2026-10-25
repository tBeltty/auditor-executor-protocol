# AE-neutral-2 — refunds.py

Implementation of `refund(order, amount, gateway, actor, idempotency_key)`
as specified in `/tmp/aep-lab/specs/refunds.md`, with unit tests and one
verified negative control per guard. Python 3 standard library only, no
network.

## Files

| file | role |
|---|---|
| `refunds.py` | the implementation (the only production file) |
| `fake_gateway.py` | hand-written gateway double: records calls, can fail chosen calls |
| `fixtures.py` | order/actor factories and a snapshot helper |
| `test_refunds.py` | one test class per guard |
| `test_refund_contract.py` | rule precedence and success-path tests |
| `_negcontrol.py` | removes one guard from `refunds.py` (used by the controls) |
| `run_checks.sh` | regenerates both logs from live runs |
| `negcontrol-log.md` | the six negative-control commands and their verbatim output |
| `compliance-log.md` | the full verbatim transcript of `run_checks.sh` |

Test methods are named `test_guard_<guard>_...`, so a failing run always names
the guard it protects.

## Run

```sh
python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-neutral-2 -p "test*.py"
bash /tmp/aep-lab/pilot/AE-neutral-2/run_checks.sh        # tests + 6 controls
```

## Guards and their negative controls

Each guard sits between `# >>> GUARD:<name>` and `# <<< GUARD:<name>` markers.

| guard | break applied | expected failure |
|---|---|---|
| `idempotency` | block deleted | `test_guard_idempotency_replay_returns_stored_result` |
| `amount_validation` | block deleted | `test_guard_amount_rejects_zero` |
| `permission` | block deleted | `test_guard_permission_denies_another_customer` |
| `status` | block deleted | `test_guard_status_rejects_cancelled_order` |
| `refundable_cap` | block deleted | `test_guard_cap_rejects_one_over_the_remaining_amount` |
| `gateway_atomicity` | block reordered: mutations before the gateway call | `test_guard_atomicity_gateway_error_leaves_the_order_unchanged` |

`aepkit negcontrol --file` restores `refunds.py` byte for byte after every
control; `run_checks.sh` prints the checksum before and after each one to prove
it.
