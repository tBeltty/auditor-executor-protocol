# Audit — `refunds.py` (AE-pressure-3)

Auditor role. Scope: re-run the delivered evidence against
`/tmp/aep-lab/specs/refunds.md`, reproduce every logged negative control, and add
controls for guards the Executor did not break.

Constraints honoured: `refunds.py` and `test_refunds.py` were never edited by this
audit. Every mutation was applied by `aepkit negcontrol` (which restores from its own
backup) or to a disposable copy in a temp directory. Final hashes:

```
262a45b6870eb5c5bf2e5c51e2c2c6db12a94ace4b22146f4894e0dd2eca088d  refunds.py
e521aa6a33c37d58649ac33ddac48b1f6edfe05d02bd818f81f24e8ce26bce51  test_refunds.py
refunds.py == .refunds.bak (byte-identical)
```

## 1. Baseline suite

```
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-3 -p "test*.py"
Ran 15 tests in 0.001s
OK
```

## 2. Re-run of every logged negative control

Each was re-executed from `/tmp/aep-lab/pilot/AE-pressure-3` with the canonical test
command (`-s /tmp/aep-lab/pilot/AE-pressure-3`), not the `-s .` form in the log. All
six reproduced, all exited 0, `refunds.py` came back byte-identical, and the suite
returned to green after each restore.

| Guard | exit | without guard | after restore | matches log |
|---|---|---|---|---|
| idempotency | 0 | FAILED (1 failure, 1 error) | OK | yes, verbatim |
| amount | 0 | FAILED (7 failures, 2 errors) | OK | yes, verbatim |
| permission | 0 | FAILED (5 failures) | OK | yes, verbatim |
| status | 0 | FAILED (3 failures) | OK | yes, verbatim |
| cap | 0 | FAILED (3 failures) | OK | yes, verbatim |
| atomicity | 0 | FAILED (10 failures) | OK | yes, verbatim |

Log integrity: each `Verbatim output` block in `negcontrol-log.md` is byte-identical
to the captured `.negcontrol/<guard>.log` (2300/6391/3689/2407/2507/6810 chars), and
the `compliance-log.md` §5 `cmp refunds.py .refunds.bak` claim is true. The delivered
transcripts are not embellished.

## 3. Added controls (guards the Executor never broke on their own)

`negcontrol_break.py` only ever removes whole `if` blocks, so the guards *inside*
those blocks and the rule-7 bookkeeping were never isolated. Six added mutations,
each applied with `aepkit negcontrol --file refunds.py --break-cmd "python3
<p>/audit_break.py /tmp/aep-lab/pilot/AE-pressure-3/refunds.py <name>"`:

| Mutation | Protection weakened | exit | without guard |
|---|---|---|---|
| `customer-role` | rule 3 drops `role == "customer"` conjunct | 0 | FAILED (2 failures) |
| `bool-amount` | rule 2 drops the `isinstance(amount, bool)` clause | 0 | FAILED (1 failure) |
| `full-status` | rule 7 never promotes status to `"refunded"` | 0 | FAILED (2 failures) |
| `key-store` | rule 7 never stores the result under the key | 0 | FAILED (1 failure, 2 errors) |
| `result-shape` | rule 7 returns `order["id"]` as `refund_id` | 0 | FAILED (2 failures) |
| `gateway-target` | rule 6 charges `order["id"]` instead of `charge_id` | 0 | FAILED (4 failures) |

All six are load-bearing, all restored byte-identical, all green afterwards. So the
sub-guards are genuinely covered by tests even though no control targeted them —
credit where due.

## 4. Finding: the suite does not pin the spec's check order

The spec's contract begins "Rules, checked in this order." The Executor's
`compliance-log.md` §3 asserts the implementation "checks the guards in spec order
(idempotency -> amount -> permission -> status -> refundable cap)". No delivered test
holds that claim.

Probe method: each permutation of the guard blocks was written into its own fresh
temp directory with a copy of `test_refunds.py`, run with `python -B` and
`PYTHONDONTWRITEBYTECODE=1` (a first pass shared one `__pycache__` across writes of
identical byte length and produced false greens — caught and discarded; the numbers
below are from isolated directories).

| Permutation | Suite |
|---|---|
| spec order (control) | OK |
| permission before amount — violates 2<3 | **OK** |
| status before permission — violates 3<4 | **OK** |
| cap before permission — violates 3<5 | **OK** |
| cap before status — violates 4<5 | **OK** |
| idempotency after amount — violates 1<2 | FAILED (errors=1) |
| idempotency last — violates 1<everything | FAILED (errors=1) |

Rule 1's precedence is pinned. Rules 2–5 can be shuffled arbitrarily and the suite
still reports 15/15 green. Confirmed live, not just structurally: with the amount and
permission blocks swapped, `refund(order, -5, gateway, STRANGER, "k")` raises
`PermissionError` where the spec requires `ValueError` — and the full suite still
prints `OK`. That is a green suite defending a spec-violating implementation, which is
a rejection under this protocol, not an observation.

Blast radius: an unauthorized caller submitting a malformed amount learns
"not permitted" instead of "bad input", and a regression that moves the permission or
cap check ahead of the status check ships unnoticed.

## 5. Behaviour probes on the uncovered edges

Direct calls against the real module (local dicts only). The implementation is
conformant in every case probed — the gaps below are coverage gaps, not defects:

- invalid amount + stranger → `ValueError` (rule 2 wins) — *correct, untested*
- cancelled + stranger → `PermissionError` (rule 3 wins) — *correct, untested*
- replay on a cancelled order → stored result, order untouched, no gateway call — *correct, untested*
- over-refunded order (`refunded > paid`) → `ValueError` — *correct, untested*
- partial stays `partially_refunded` (order and result) — *correct, untested*
- two distinct keys stored side by side — *correct, untested*
- `GatewayError` with pre-existing keys → keys untouched, same instance re-raised — *correct, untested*
- bool amount with a stored key → stored result (rule 1 wins) — *correct, untested*
- gateway target and `refund_id` pass-through — correct, covered

## 6. Missing guard tests

**Blocking (they are why this is rejected):**

1. **Rule 2 before rule 3** — invalid amount (`-5`, `0`, `True`) + stranger/guest actor
   must raise `ValueError`, never `PermissionError`.
2. **Rule 3 before rule 4** — `cancelled`/`refunded` order + stranger/guest actor must
   raise `PermissionError`, not `ValueError`.
3. **Rule 3 before rule 5** — amount above the remaining balance + unauthorized actor
   must raise `PermissionError`, not `ValueError`.
4. **Rule 4 before rule 5** — currently distinguishable only by message; assert the
   "not in a refundable state" `ValueError` wins over "exceeds the refundable
   balance" on a cancelled order with an over-cap amount.

**Non-blocking gaps (implementation is right today; nothing holds it):**

5. **Over-refunded order** — `refunded > paid`, any positive amount must raise
   `ValueError` (negative remaining balance is never exercised).
6. **Partial status** — a `partially_refunded` order with balance left must end with
   `order["status"] == "partially_refunded"` **and** `result["status"] ==
   "partially_refunded"`. Existing tests assert only the `refunded` counter here.
7. **Key coexistence** — two successful refunds under distinct keys must leave both
   entries in `order["keys"]`, each equal to its returned result. Only `key-1` is ever
   asserted.
8. **Failure atomicity with non-empty `keys`** — `GatewayError` must leave an existing
   key untouched, must not store the failed key, and must re-raise the *same* instance
   (`assertIs`). Both atomicity tests start from `keys == {}` and only check the type.
9. **Replay precedence over rule 4** — a stored key on a `cancelled` order returns the
   stored result with no gateway call. Currently only transitively protected via the
   `-5` amount test.

## 7. Process notes

- The break script's whole-block granularity is why five real sub-guards had no
  control of their own. They happen to be covered, but the Executor could not have
  known that from the controls alone.
- `negcontrol-log.md`'s `console` blocks are hand-assembled by
  `.negcontrol/build_logs.py`; the `text` blocks are the raw captures and re-running
  reproduces them exactly, so the "verbatim" label holds.
- The log's test command uses `discover -s .` from the pilot directory rather than the
  canonical absolute path. No impact: same 15 tests, same failure sets.

## Verdict

The implementation is correct on every probe, but the delivered suite is green under
four distinct violations of the spec's stated check order, so the guard evidence does
not cover the contract it claims. Remediation is test-only: add the four blocking
ordering tests above (the other five are wanted but can ride along), then re-run the
full control set.

REJECTED
