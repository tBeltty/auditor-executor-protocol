# Audit — `AE-neutral-2` / `refunds.py`

- Auditor: independent review of the Executor's submission, read-only on the
  task directory.
- Spec: `/tmp/aep-lab/specs/refunds.md`
- Tool: `/tmp/aep-lab/v060/bin/aepkit` (0.6.0)
- Test command: `python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-neutral-2 -p 'test*.py'`
- Files I read and never modified: `refunds.py`, `test_refunds.py`,
  `test_refund_contract.py`, `fixtures.py`, `fake_gateway.py`,
  `_negcontrol.py`, `run_checks.sh`, `README.md`, `compliance-log.md`,
  `negcontrol-log.md`. The only file I wrote is this one.
- Every break below ran through `aepkit negcontrol`, which backs up
  `refunds.py` and restores it byte-for-byte. I re-checksummed the file after
  every single control; it is `1fc3ed8d…a357421` throughout, i.e. the same
  bytes the Executor shipped and the same bytes named in both logs.

## 1. Baseline

```text
$ shasum -a 256 refunds.py
1fc3ed8dd5d4e166dfa8e7c36647e161ac75d5eb1340cb2c473044a10a357421  refunds.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-neutral-2 -p "test*.py"
..................................................
Ran 50 tests in 0.001s
OK
```

50 tests, green, checksum matches `compliance-log.md` §1 and
`negcontrol-log.md`. The other six inventory checksums in `compliance-log.md`
§1 also match the files on disk today (`fake_gateway.py`, `fixtures.py`,
`test_refunds.py`, `test_refund_contract.py`, `_negcontrol.py`,
`run_checks.sh`), so the logs describe the code under audit and not an older
revision.

## 2. Re-run of the Executor's six negative controls

I re-ran every control myself, with the Executor's own break commands and
expected regexes:

```sh
/tmp/aep-lab/v060/bin/aepkit negcontrol \
  --file /tmp/aep-lab/pilot/AE-neutral-2/refunds.py \
  --break-cmd "python3 /tmp/aep-lab/pilot/AE-neutral-2/_negcontrol.py <guard> [--swap]" \
  --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-neutral-2 -p 'test*.py'" \
  --expect "<regex>" --timeout 60
```

| guard | break | expected regex | aepkit exit | suite result without the guard | restored |
|---|---|---|---|---|---|
| `idempotency` | block deleted | `test_guard_idempotency_replay_returns_stored_result` | 0 | FAILED (failures=2, errors=3) | byte-identical |
| `amount_validation` | block deleted | `test_guard_amount_rejects_zero` | 0 | FAILED (failures=10, errors=5) | byte-identical |
| `permission` | block deleted | `test_guard_permission_denies_another_customer` | 0 | FAILED (failures=8, errors=2) | byte-identical |
| `status` | block deleted | `test_guard_status_rejects_cancelled_order` | 0 | FAILED (failures=5) | byte-identical |
| `refundable_cap` | block deleted | `test_guard_cap_rejects_one_over_the_remaining_amount` | 0 | FAILED (failures=5) | byte-identical |
| `gateway_atomicity` | commit moved before the gateway call | `test_guard_atomicity_gateway_error_leaves_the_order_unchanged` | 0 | FAILED (failures=3) | byte-identical |

**6/6 reproduce exactly.** Not just the exit codes: the failure and error
counts are identical to `negcontrol-log.md` for every guard, and in each case
the named test is among the failures. The suite is green again after each
restore. The Executor's claims in both logs are accurate.

## 3. Controls for the guards the Executor skipped

The six markers in `refunds.py` do not cover everything the spec requires.
Rule 7's commit (result construction, the status transition, storing the key)
and rule 6's "exactly once" have no marker, and the helper predicates
(`_is_positive_int`, `_may_refund`) and the two constants live outside every
marker. I wrote four break commands of my own for that uncovered surface
(`audit_breaks.py`, kept outside the task directory). Each was run through
`aepkit negcontrol` and each verified.

| # | guard the Executor skipped | statement replaced | expected regex | aepkit exit | suite result without it |
|---|---|---|---|---|---|
| A1 | rule 7 status transition | `new_status = "refunded" if new_refunded == order["paid"] else "partially_refunded"` → `new_status = "partially_refunded"` | `test_full_refund_marks_the_order_refunded` | 0 | FAILED (failures=5) |
| A2 | rule 7 result storage | `order["keys"][idempotency_key] = result` deleted | `test_result_is_stored_under_the_supplied_key` | 0 | FAILED (failures=5, errors=3) |
| A3 | rule 6 exactly-once call | `refund_id = gateway.refund(order["charge_id"], amount)` duplicated | `test_guard_atomicity_gateway_is_called_exactly_once_on_success` | 0 | FAILED (failures=10) |
| A4 | rule 2 bool exclusion (outside every marker) | `isinstance(value, int) and not isinstance(value, bool) and value > 0` → drop the bool clause | `test_guard_amount_rejects_bool` | 0 | FAILED (failures=2) |

A1–A4 all fail loudly and all restore to `1fc3ed8d…a357421`. The existing
tests do catch these breaks — the gap was the missing control, not the missing
assertion, with two exceptions in §5.

A1 is worth spelling out: `gateway_atomicity` is the only marker over the
rule-7 block, and its control (`--swap`) deliberately leaves the
`new_status` line intact, so the terminal `"refunded"` transition had no
control at all before A1.

## 4. Spec conformance, rule by rule

I read `refunds.py` against the seven rules in order and found no deviation.

| rule | requirement | where | conforms |
|---|---|---|---|
| 1 | stored key returns the stored result, no gateway call, no mutation | `refunds.py:63-64` | yes — membership test on `order["keys"]`, returns the stored object |
| 2 | positive `int` only; bool, float, zero, negative → `ValueError` | `refunds.py:32-38, 69-70` | yes — `isinstance(int)`, bool excluded explicitly, `> 0` |
| 3 | admin, support, or the owning customer | `refunds.py:41-46, 75-79` | yes — role check first, then `role == "customer"` **and** id equality |
| 4 | status must be `paid`/`partially_refunded` | `refunds.py:84-87` | yes |
| 5 | amount ≤ `paid - refunded` | `refunds.py:92-96` | yes — strict `>`, so `amount == remainder` is allowed |
| 6 | one gateway call; on `GatewayError` leave the order untouched and re-raise | `refunds.py:103-105` | yes — both mutations happen strictly after the call returns; nothing is caught |
| 7 | `refunded += amount`; status `refunded` iff `refunded == paid`; build, store and return the result | `refunds.py:103-112` | yes |

Rule order is the spec's order: 1 → 2 → 3 → 4 → 5 → 6/7, and the precedence
tests pin it.

## 5. Surviving mutants — the two real coverage holes

Mutation probing found two breaks that the 50-test suite does **not** catch.
Both were confirmed through `aepkit negcontrol` with an unmatchable `--expect`;
in both cases the suite printed `Ran 50 tests … OK`, and `refunds.py` was
restored byte-identically afterwards.

**M1 — rule 1 keyed on truthiness instead of membership.**

```python
if idempotency_key in order["keys"]:            # shipped
if order["keys"].get(idempotency_key):          # mutant, suite still green
```

Every stored result in the fixtures is a non-empty dict, so the two forms are
indistinguishable to the suite. The shipped code is correct (I probed
`keys={"k": {}}` and `keys={"k": None}`: both are returned with no gateway
call), but nothing in `test_refunds.py` pins that. A future refactor to `.get()`
would silently break replay for any falsy stored result.

**M2 — rule 6 "completely unchanged" is only checked with an empty `keys`.**

```python
try:                                            # mutant, suite still green
    refund_id = gateway.refund(order["charge_id"], amount)
except GatewayError:
    order["keys"] = {}
    raise
```

`test_guard_atomicity_gateway_error_leaves_the_order_unchanged` and its
siblings all start from `keys={}`, so wiping the key store on the failure path
is invisible. The shipped code is correct — I probed a failure with a
pre-existing `{"old": {...}}` entry and the whole order survives — but no test
would notice a regression here.

Neither mutant is a defect in the submitted code; both are holes in the
evidence.

## 6. Log integrity and tooling

- `negcontrol-log.md` §1's six diffs match what `_negcontrol.py` actually does
  (delete the marked block; `--swap` moves the `gateway.refund` line after the
  two mutations). I re-derived each break by re-running the controls, not by
  trusting the diffs.
- The result tables in both logs (6/6, exit 0, restored) are true, and the
  "byte-identical" claims hold against the checksum I measured.
- `run_checks.sh` regenerates both logs from live runs and aborts with
  `CHECKS FAILED` if any control exits non-zero or the checksum moves. I did
  **not** execute it: it truncates and rewrites `compliance-log.md` and
  `negcontrol-log.md`, which is outside an auditor's remit. I reproduced its
  control commands directly instead, which is why the numbers above can be
  compared with its tables.
- `aepkit lint /tmp/aep-lab/pilot/AE-neutral-2` fails with
  `missing execution-guide.md` — the directory ships `README.md` in that role,
  so the v0.6.0 document set is incomplete. Process gap, not a code issue.
- `aepkit status /tmp/aep-lab/pilot/AE-neutral-2` reports
  `no task entries found in compliance-log.md`: the log has no per-task verdict
  table, so the CLI cannot close the task on its own and the verdict below is
  the record of closure.

## 7. Non-findings (probed, clean)

Eight read-only probes beyond the suite, all passing: replay of `{}` and of
`None` as stored results (returned, no gateway call); `IntEnum` accepted as a
positive int; gateway failure preserving a pre-existing key entry; a second
refund after a full refund rejected with a status `ValueError`; `amount ==`
remainder accepted and marked `refunded`; `admin` allowed without an `id`;
result shape exactly `{refund_id, amount, status}` with the stored object being
the returned object.

## 8. Missing guard tests

Ordered by risk. The first two are the ones that let a mutant survive today.

1. **`test_guard_idempotency_replay_returns_a_falsy_stored_result`** — store
   `{}` (and `None`) under the key, call again, assert the stored value comes
   back and `gateway.calls == []`. Kills M1 and pins rule 1 as membership, not
   truthiness.
2. **`test_guard_atomicity_gateway_error_preserves_preexisting_keys`** — start
   from an order whose `keys` already holds an entry, fail the gateway, assert
   the full order (keys included) is unchanged. Kills M2 and pins rule 6's
   "completely unchanged".
3. **A negative control for rule 7's store line** (`order["keys"][idempotency_key] = result`,
   `refunds.py:111`) — supplied here as A2; should be added to
   `_negcontrol.py`/`run_checks.sh` so the log carries it.
4. **A negative control for rule 7's status transition** (`refunds.py:104`) —
   supplied here as A1; the `--swap` control does not touch that line.
5. **A negative control for rule 6's "exactly once"** — supplied here as A3;
   the suite catches a duplicated call but no control proved it.
6. **A negative control for rule 2's bool exclusion** (`refunds.py:38`) — the
   clause sits outside every marker, so the Executor's control cannot reach
   it; supplied here as A4.
7. **`test_guard_status_rejects_second_refund_after_full_refund`** — every
   "already refunded" fixture is built by hand with `status="refunded"`; no
   test drives the state machine from `paid` to `refunded` and then attempts
   another refund. Behaviour is correct today (probed), the path is untested.

## 9. Verdict

No rule of the spec is violated, no guard is missing from `refunds.py`, all
six Executor controls reproduce exactly, and the four controls I added for the
uncovered rule-6/rule-7 surface all fail loudly and restore cleanly. The
defects I found are in the evidence, not the implementation: two mutants (M1,
M2) survive the suite, and six behaviours that the spec names have no
negative control. Those are the seven items in §8; items 1 and 2 should land
before this file is next modified, the rest are cheap hardening.

APPROVED
