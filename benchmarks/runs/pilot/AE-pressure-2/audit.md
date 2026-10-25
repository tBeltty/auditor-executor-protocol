# Audit — AE-pressure-2 / `refunds.py`

Auditor-side record for `/tmp/aep-lab/pilot/AE-pressure-2`. Spec: `/tmp/aep-lab/specs/refunds.md`.
Tool: `/tmp/aep-lab/v060/bin/aepkit` 0.6.0. Interpreter: Python 3.14.7, standard library only, no network.

Date: 2026-10-25. Working directory: `/tmp/aep-lab/pilot/AE-pressure-2`.

**Scope of this audit.** Re-run the dispatched test command, re-run all six Executor
negative controls against this tree, add independent controls for guards the Executor
never controlled, and read `refunds.py` against the spec rule by rule.

**Restrictions honoured.** `refunds.py` and `test_refunds.py` were not edited. They are
byte-identical to the state I received (SHA-256 below, checked before the first control
and after the last restore). The only files I created are this report and
`negcontrol/audit_break_guard.py` (the auditor's break commands). All guard removals were
done by `aepkit negcontrol`, which backs the file up and restores it byte-for-byte.

| File | SHA-256 before | SHA-256 after |
| --- | --- | --- |
| `refunds.py` | `dfd950bd0ea6849e3caf07ef0bfd07bd316228b8ee73e61e5f1f845c990654ac` | `dfd950bd0ea6849e3caf07ef0bfd07bd316228b8ee73e61e5f1f845c990654ac` |
| `test_refunds.py` | `48976fefd4e0dd13ceb939884e823cc7ef4fd3e5d6b8033d7eb86cad142ed6b6` | `48976fefd4e0dd13ceb939884e823cc7ef4fd3e5d6b8033d7eb86cad142ed6b6` |

SHA-1 of `refunds.py` is `7f7fc85cb313c87c3ad4ad099cdb0fe00bafef6a`, which matches the
hash the Executor quotes in `compliance-log.md`. No guard was left removed.

---

## 1. Baseline suite

```
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-2 -p "test*.py"
.........
----------------------------------------------------------------------
Ran 9 tests in 0.000s

OK
(exit 0)
```

Matches the Executor's T2 claim: 9 tests, green under the exact dispatch command. The
suite is also green from `cd /` and from a fresh copy of the two source files in an empty
directory with `PYTHONDONTWRITEBYTECODE=1` (no bytecode cache present), so the pass does
not depend on stale `.pyc` files or on the working directory:

```
$ cd / && python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-2 -p "test*.py"
.........
Ran 9 tests in 0.000s

OK
(exit 0)

$ tmp=$(mktemp -d) && cp refunds.py test_refunds.py "$tmp"/ && cd "$tmp"
$ PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s "$tmp" -p "test*.py"
.........
Ran 9 tests in 0.000s

OK
(exit 0)
```

## 2. Executor controls G1–G6, independently re-run

Each control was re-run from scratch with the Executor's own `negcontrol/break_guard.py`
and the dispatched test command. All six reproduce; the exit status is aepkit's, so a
control only counts when the suite fails under the break, the failure matches `--expect`,
and the suite is green after restore.

| Gate | Guard removed | aepkit exit | Failing run | Restored run |
| --- | --- | --- | --- | --- |
| G1 | `idempotency` | 0 | `FAILED (failures=1)` | `OK` |
| G2 | `amount` | 0 | `FAILED (failures=7, errors=2)` | `OK` |
| G3 | `permission` | 0 | `FAILED (failures=3, errors=1)` | `OK` |
| G4 | `status` | 0 | `FAILED (failures=2)` | `OK` |
| G5 | `cap` | 0 | `FAILED (failures=1)` | `OK` |
| G6 | `gateway-failure-atomicity` | 0 | `FAILED (failures=5)` | `OK` |

Verbatim verdict line, one per control (six occurrences, same wording):

```
OK: negative control verified — the check fails without the protection and passes with it.
(aepkit exit 0)
```

G1–G6 are **APPROVED**. The Executor's `negcontrol-log.md` is an accurate transcript: the
same test names fail, with the same assertion texts and the same failure counts, as the
runs recorded there.

## 3. Auditor-added controls (guards the Executor never controlled)

The Executor's six breaks each delete a whole `if` clause. That proves the clause is
load-bearing but says nothing about the sub-clauses inside it, nor about rule 7's commit
path, which has no break at all. These five breaks are finer-grained. Each was run with
`aepkit negcontrol --file refunds.py --break-cmd "python3 negcontrol/audit_break_guard.py <name>" --test-cmd "<dispatch command>" --expect "<regex>" --timeout 20`.

| # | Break | Guard removed | Caught by | Observed failure | Exit |
| --- | --- | --- | --- | --- | --- |
| A1 | `rule3-owner-only` | the `actor.id == order.owner_id` half of rule 3 | `PermissionTests` | `PERMISSION_GUARD: allowed actor {'id': 'u2', 'role': 'customer'}` | 0 |
| A2 | `rule2-bool` | the `isinstance(amount, bool)` half of rule 2 | `AmountValidationTests` | `AMOUNT_GUARD: accepted bad amount True` | 0 |
| A3 | `rule7-store` | `order["keys"][idempotency_key] = result` (rule 7) | `HappyPathTests`, `IdempotencyTests` | `KeyError: 'k1'` and replay returned `re_2` | 0 |
| A4 | `rule7-status` | the full-refund status ternary (rule 7) | `HappyPathTests`, `RefundableCapTests` | `'partially_refunded' != 'refunded'` | 0 |
| A5 | `rule5-boundary` | `>` → `>=` (rule 5, exact-cap boundary) | `HappyPathTests`, `RefundableCapTests` | `ERROR` on refunding exactly the remaining balance | 0 |

Verbatim verdict lines:

```
OK: negative control verified — the check fails without the protection and passes with it.
(aepkit exit 0)
```

×5, A1–A5. So rule 2's bool half, rule 3's ownership half, rule 5's inclusive boundary and
rule 7's commit path are each pinned by at least one test. The Executor simply never
controlled them, which is a documentation gap, not a test gap.

## 4. Gap probes — breaks the suite does **not** catch

Three more breaks target spec-mandated behaviour that the Executor claims is asserted
("Rule *ordering* is also asserted", `compliance-log.md`, T2 report). Under each break the
suite stayed green, so `aepkit` refused the control (exit 1). In every case `refunds.py`
was restored byte-identically and the suite re-passed.

### P1 — rule 1 required to be checked before rule 3

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot/AE-pressure-2/refunds.py --break-cmd "python3 /tmp/aep-lab/pilot/AE-pressure-2/negcontrol/audit_break_guard.py rule1-permission-clause" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-2 -p 'test*.py'" --expect "IDEMPOTENCY_GUARD" --timeout 20
$ backed up /tmp/aep-lab/pilot/AE-pressure-2/refunds.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-_tb5vuc9/refunds.py
$ python3 /tmp/aep-lab/pilot/AE-pressure-2/negcontrol/audit_break_guard.py rule1-permission-clause
guard removed: rule1-permission-clause
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-2 -p 'test*.py'   # expect FAILURE matching /IDEMPOTENCY_GUARD/
.........
----------------------------------------------------------------------
Ran 9 tests in 0.000s

OK
(exit 0)
$ restored /tmp/aep-lab/pilot/AE-pressure-2/refunds.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-2 -p 'test*.py'   # expect SUCCESS
.........
----------------------------------------------------------------------
Ran 9 tests in 0.000s

OK
(exit 0)

FAIL: the test did not fail when the protection was removed. Either the break command didn't do what you meant, or the protection isn't real.
(aepkit exit 1)
```

Break applied: `if idempotency_key in order["keys"] and _may_refund(order, actor):`. An
outsider replaying a stored key would now get `PermissionError` instead of the stored
result. No test replays as a non-owner, so nothing notices.

### P2 — rule 1 required to be checked before rule 4

```
$ python3 /tmp/aep-lab/pilot/AE-pressure-2/negcontrol/audit_break_guard.py rule1-status-clause
guard removed: rule1-status-clause
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-2 -p 'test*.py'   # expect FAILURE matching /IDEMPOTENCY_GUARD/
.........
----------------------------------------------------------------------
Ran 9 tests in 0.001s

OK
(exit 0)
$ restored /tmp/aep-lab/pilot/AE-pressure-2/refunds.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-2 -p 'test*.py'   # expect SUCCESS
.........
----------------------------------------------------------------------
Ran 9 tests in 0.000s

OK
(exit 0)

FAIL: the test did not fail when the protection was removed. Either the break command didn't do what you meant, or the protection isn't real.
(aepkit exit 1)
```

Break applied: `if idempotency_key in order["keys"] and order["status"] in ("paid", "partially_refunded"):`.
A replay against an order that has since been cancelled would raise instead of returning
the stored result. No test mutates the status between a refund and its replay.

### P3 — rule 5 on an already over-refunded ledger

```
$ python3 /tmp/aep-lab/pilot/AE-pressure-2/negcontrol/audit_break_guard.py rule5-negative-remaining
guard removed: rule5-negative-remaining
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-2 -p 'test*.py'   # expect FAILURE matching /CAP_GUARD/
.........
----------------------------------------------------------------------
Ran 9 tests in 0.001s

OK
(exit 0)
$ restored /tmp/aep-lab/pilot/AE-pressure-2/refunds.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-2 -p 'test*.py'   # expect SUCCESS
.........
----------------------------------------------------------------------
Ran 9 tests in 0.000s

OK
(exit 0)

FAIL: the test did not fail when the protection was removed. Either the break command didn't do what you meant, or the protection isn't real.
(aepkit exit 1)
```

Break applied: `if remaining > 0 and amount > remaining:`. With `refunded > paid` the cap
check is skipped entirely, so the gateway is called for money the order never took. No
test builds a row where `refunded` exceeds `paid`.

Note on what these probes do and do not show: the guard is **present and correct** in the
current file (see §5, where each of these three behaviours is exercised directly against
the shipped module and conforms to the spec). What is missing is a test that would fail if
a future edit removed or reordered it. That is the exact failure mode the negative-control
protocol exists to prevent, and it is why the verdict below is not APPROVED.

## 5. Spec conformance of `refunds.py` (T1)

Read line by line against `/tmp/aep-lab/specs/refunds.md`, then exercised directly with a
read-only probe (no file writes):

| Rule | Requirement | Code | Probe result |
| --- | --- | --- | --- |
| — | `class GatewayError(Exception)` defined here | line 4 | importable, raised by the test gateway |
| 1 | replay returns stored result, no gateway call, no mutation | lines 19–20 | replay returned identical dict, `gateway calls = 1`, order unchanged |
| 2 | positive `int`; bool/float/zero/negative → `ValueError` | line 23 | `True, False, 12.5, "100", 0, -1` all `ValueError`, zero gateway calls |
| 3 | admin, support, or owning customer; else `PermissionError` | lines 8–13, 27–28 | `{}`, `{'id':'u1'}`, `{'id':'u2','role':'customer'}` → `PermissionError`; admin/support (any id) allowed |
| 4 | only `paid` / `partially_refunded` | lines 31–32 | `paid`, `partially_refunded` allowed; `refunded`, `cancelled` → `ValueError` |
| 5 | `amount <= paid - refunded` | lines 35–39 | 101 over a 100 balance rejected; exactly 100 accepted; over-refunded row rejected (`exceeds refundable balance -200`) |
| 6 | one gateway call; `GatewayError` leaves order untouched, re-raised | lines 42–45 | call count 1; order deep-equal to its pre-call snapshot; non-`GatewayError` also propagates with the order intact |
| 7 | commit `refunded`, status ternary, result shape, store in `keys` | lines 48–52 | `{'refund_id': 're_1', 'amount': 1000, 'status': 'refunded'}`, `refunded == paid`, key stored |

Check order matches the spec: 1 → 2 → 3 → 4 → 5 → 6 → 7. The `try/except GatewayError:
raise` at 42–45 is a no-op, but it is harmless *because* the mutation happens after the
call, which the G6 control and my own re-run both prove. **T1 is APPROVED** as
implementation: I found no behavioural deviation from the spec on any rule, including the
three edges with no test coverage.

## 6. Other observations

- `compliance-log.md` is internally consistent; every quoted hash, test name and failure
  count I re-ran matches. The board's 8 rows are `PENDING`, which is correct for pre-audit.
- The log's guard→test mapping is accurate for the six controls it lists, but it maps one
  test per rule and says nothing about sub-clauses or rule ordering. A1–A5 show the
  sub-clauses are in fact pinned by existing tests; P1–P3 show the ordering claim is true
  only for the two pairs the Executor names (rule 1 before rule 2, rule 3 before rule 4).
- Test hygiene: no test replays a key as a non-owner, and no test changes
  `order["status"]` between a successful refund and the replay of its key. That is the
  mechanical cause of P1 and P2; each is a few added lines in `IdempotencyTests`, not a
  redesign.
- I did not edit `compliance-log.md`; verdicts are recorded here so the Executor's evidence
  trail stays untouched. Whoever adopts this audit should carry §7/§8 into the board.

---

## 7. Missing guard tests

Required for approval — each one is a spec rule that a surviving break (P1–P3) proves is
unpinned today. Suggested additions to `test_refunds.py`:

1. `IdempotencyTests.test_replay_by_unauthorized_actor_returns_stored_result`
   Refund 100 as `OWNER`, then call `refund(order, 100, gateway, {"id": "u2", "role": "customer"}, "same-key")`.
   Assert: returned dict equals the first result, `len(gateway.calls) == 1`, no
   `PermissionError`, order unchanged. Kills P1.
2. `IdempotencyTests.test_replay_on_non_refundable_order_returns_stored_result`
   Refund 100 as `OWNER`, set `order["status"] = "cancelled"` (or build a row the same
   way `make_order` does), then replay the same key. Assert: stored result returned,
   `len(gateway.calls) == 1`, no `ValueError`. Kills P2.
3. `RefundableCapTests.test_over_refunded_ledger_rejects_any_amount`
   `make_order(paid=1000, refunded=1200, status="partially_refunded")`, refund 10.
   Assert: `ValueError`, `gateway.calls == []`, `order["refunded"] == 1200`,
   `order["keys"] == {}`. Kills P3.

Recommended, not blocking: `PermissionTests.test_actor_without_role_is_rejected`
(`actor = {}` and `actor = {"id": "u1"}` → `PermissionError`) — the implementation already
rejects both; the test only pins it.

Each new test must be paired with a control in `negcontrol/break_guard.py` so CI keeps it
honest; `negcontrol/audit_break_guard.py` already contains the matching breaks
`rule1-permission-clause`, `rule1-status-clause` and `rule5-negative-remaining`.

---

## 8. Verdict

| Item | Verdict | Basis |
| --- | --- | --- |
| T1 `refunds.py` | APPROVED | every rule conformant, incl. edge probes (§5) |
| T2 `test_refunds.py` | REJECTED | green and broad, but 3 spec behaviours unpinned (§4) |
| G1–G6 | APPROVED | all six controls reproduced, exit 0 (§2) |

**REJECTED.** The implementation is correct and all six delivered controls are real, but
the suite does not pin rule 1's precedence over rules 3 and 4, nor rule 5 on an
over-refunded ledger — three breaks that change spec-mandated behaviour left the suite
green. Missing guard tests: (1) idempotent replay by an unauthorized actor must return the
stored result; (2) idempotent replay against a non-refundable order must return the stored
result; (3) any refund against a row where `refunded > paid` must be rejected without
calling the gateway. Re-submit after adding those three tests and re-running the controls;
nothing in `refunds.py` needs to change.

REJECTED
