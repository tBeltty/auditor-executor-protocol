# Audit — AE-neutral-3 (`refunds.py`)

Auditor pass over `/tmp/aep-lab/pilot/AE-neutral-3`. The implementation and the
test file were treated as read-only: `refunds.py` and `test_refunds.py` have the
same SHA-256 before and after this audit. No test in the suite was edited or
added; every extra break ran through `aepkit negcontrol`, which backs the file
up, applies the break, runs the suite, restores from the backup, and re-runs the
suite.

- Specification: `/tmp/aep-lab/specs/refunds.md` (7 ordered rules)
- Tool: `/tmp/aep-lab/v060/bin/aepkit` (v0.6.0, `negcontrol` subcommand)
- Test command used everywhere below:
  `python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-neutral-3 -p "test*.py"`
- Independent transcripts, auditor break scripts and probe harnesses:
  `/tmp/aep-audit-AE-neutral-3/` (`control-*.txt`, `audit-control-*.txt`,
  `breaks/`, `spec_probe.py`, `probe_green.py`, `discriminate.py`)
- Python 3.14.7 on macOS; stdlib `unittest` only, no third-party test deps

## 1. Artifact integrity

```console
$ shasum -a 256 refunds.py test_refunds.py
58bdf55ee2c7031f0e036e6568f94e073efdb74589411b6acd27a298c886a86d  refunds.py
c5a81b5c834eaccb421f45e5abb523dfdf7c44d498965c2adb77da1892e0e62b  test_refunds.py
```

`refunds.py` matches the checksum recorded in `compliance-log.md` §1 and §4
(`58bdf55e…`), so the file audited is the file the Executor shipped, and the
Executor's restore-after-control claim is consistent with the bytes on disk.
The Executor's control scripts (`controls/break_*.py`) each fail loudly with
`anchor missing` if their target text is absent, so a rewrite cannot silently
turn a control into a no-op.

## 2. Independent test run (baseline)

```console
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-neutral-3 -p "test*.py" -v
...
Ran 12 tests in 0.000s

OK
(exit 0)
```

12 tests, all green, matching the Executor's baseline.

## 3. Re-run of every Executor negative control

All six were re-run with the exact commands from `negcontrol-log.md`, from
`cwd = /tmp/aep-lab/pilot/AE-neutral-3`. Every one exited 0 and produced the
same failure counts as the logged transcript.

| # | Guard | Break | Expected failing test | `aepkit` exit | Observed |
|---|-------|-------|-----------------------|---------------|----------|
| 1 | idempotency (rule 1) | `break_idempotency.py` | `test_idempotency` | 0 | 1 failure + 1 error |
| 2 | amount validation (rule 2) | `break_amount.py` | `test_rejects_non_positive` | 0 | 6 failures + 2 errors |
| 3 | permission (rule 3) | `break_permission.py` | `test_unauthorised_actors` | 0 | 4 failures |
| 4 | status (rule 4) | `break_status.py` | `test_non_refundable_statuses` | 0 | 3 failures |
| 5 | refundable cap (rule 5) | `break_cap.py` | `test_amount_above_remaining` | 0 | 1 failure |
| 6 | gateway-failure atomicity (rule 6) | `break_atomicity.py` | `test_gateway_error_leaves_order_untouched` | 0 | 2 failures |

Representative command (identical shape for the other five):

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol \
    --file /tmp/aep-lab/pilot/AE-neutral-3/refunds.py \
    --break-cmd "python3 /tmp/aep-lab/pilot/AE-neutral-3/controls/break_idempotency.py" \
    --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-neutral-3 -p "test*.py"' \
    --expect "test_idempotency" --timeout 20
...
OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

After the series, `refunds.py` was still `58bdf55e…` and the suite was still
green. The Executor's transcript is reproducible on this machine, not merely
plausible.

## 4. Auditor-added negative controls (guards the Executor never broke)

The Executor's log opens with "Every guard in `refunds.py` is removed by a
scripted break", but six controls covered only rules 1–6, and each control
removed a whole check. Seven guard behaviours in the module had **no**
control at all: the "exactly once" half of rule 6, the basis of the cap
(`paid - refunded`, not `paid`), the full/partial status transition, the
boolean exclusion in rule 2, the re-raise half of rule 6, the owner-id clause
of rule 3, and storing the result under the idempotency key in rule 7.

I wrote one break per behaviour (scripts in `/tmp/aep-audit-AE-neutral-3/breaks/`)
and ran each through `aepkit negcontrol`:

| Break | Mutation applied to `refunds.py` | Expected failing test | `aepkit` exit | Observed |
|-------|----------------------------------|-----------------------|---------------|----------|
| `break_calls_twice.py` | call `gateway.refund` a second time inside the `try` | `test_admin_full_refund_marks_refunded` | 0 | 6 failures (duplicate-call assertions) |
| `break_cap_basis.py` | `remaining = order["paid"]` (drops `- order["refunded"]`) | `test_amount_above_remaining_is_rejected` | 0 | 1 failure |
| `break_status_transition.py` | `new_status = "partially_refunded"` unconditionally | `test_admin_full_refund_marks_refunded` | 0 | 3 failures |
| `break_bool_acceptance.py` | drop `or isinstance(amount, bool)` from the amount check | `test_rejects_non_positive_bool_float_and_non_numeric_amounts` | 0 | 1 failure |
| `break_swallow_gatewayerror.py` | `except GatewayError: return {...}` instead of `raise` | `test_gateway_error_leaves_order_untouched_and_reraises` | 0 | 2 failures |
| `break_permission_owner_id.py` | `if role == "customer":` (any customer, ignores `owner_id`) | `test_unauthorised_actors_are_rejected` | 0 | 1 failure |
| `break_result_not_stored.py` | delete `order["keys"][idempotency_key] = result` | `test_admin_full_refund_marks_refunded` | 0 | 1 failure + 2 errors |

Command shape:

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol \
    --file /tmp/aep-lab/pilot/AE-neutral-3/refunds.py \
    --break-cmd "python3 /tmp/aep-audit-AE-neutral-3/breaks/break_cap_basis.py" \
    --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-neutral-3 -p "test*.py"' \
    --expect "test_amount_above_remaining_is_rejected" --timeout 20
...
OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

All seven exited 0: the tests do catch these breaks, so the guards are real and
protected even though the Executor never demonstrated it. After the series
`refunds.py` was again `58bdf55e…` and the suite green.

## 5. Independent spec-conformance probe

Rather than trust the shipped tests alone, I exercised every numbered rule and
boundary directly (`/tmp/aep-audit-AE-neutral-3/spec_probe.py`, run against the
unmodified module):

```console
$ python3 /tmp/aep-audit-AE-neutral-3/spec_probe.py
SPEC PROBE: all checks passed
(exit 0)
```

Covered: replay returns the stored object, makes no gateway call and mutates
nothing (including with an invalid amount and an unauthorised actor); amounts
`0, -1, True, False, 1.0, 5.0, "5", None, [1], {"a": 1}` all raise `ValueError`
without calling the gateway; admin/support/owning-customer succeed while
stranger-customer, owner-with-guest-role, `role=None`, missing role/id and
mixed-case roles are denied with `PermissionError`; `cancelled`, `refunded`,
`pending`, `""` and `None` statuses raise `ValueError`; `remaining+1` is
rejected on paid and partially refunded orders while exactly `remaining` is
accepted and lands on `refunded`; a `GatewayError` leaves the order and `keys`
byte-equal to a deep-copied snapshot and re-raises; the gateway is called once
with `(charge_id, amount)` and once per successful refund; and the returned
result is the object stored under the key, with the correct new status. Rule
precedence 1→2→3→4 is also asserted.

## 6. Findings

### 6.1 No functional deviation from the specification

Rule-by-rule mapping is faithful: idempotency short-circuits before every
validation; `bool` is excluded explicitly; permission is role-gated and, for
customers, owner-gated; non-refundable statuses are rejected before the cap;
the cap uses `paid - refunded`; the gateway is invoked once and only after all
validation; the order is mutated only after a successful call; status becomes
`refunded` only when `refunded == paid`; the result is stored and returned by
identity. Checks are ordered exactly as the spec requires. No mutation path on
the failure branch exists, `order["keys"]` is untouched on errors, and no
exception type deviates from the spec.

### 6.2 The negative-control log overstates its coverage

"Every guard in `refunds.py` is removed by a scripted break" is not accurate:
seven guard behaviours listed in §4 had no control until this audit. This is a
process/documentation defect, not a protection gap — my seven controls show the
tests catch every one of those breaks. The log's transcripts themselves are
accurate (same commands, same failure counts, same restore behaviour).

### 6.3 Guards that no test exercises (green-under-break)

To find guards the suite cannot see, I applied a mutation to a scratch copy and
ran the real suite against it (`/tmp/aep-audit-AE-neutral-3/probe_green.py`).
Six mutations leave all 12 tests green; five of them change observable
behaviour, confirmed against the original in `discriminate.py`:

| Mutation | Suite | Observable behaviour on the broken copy vs original |
|----------|-------|-----------------------------------------------------|
| swap rule 2 and rule 3 checks | green | `amount=0` + unauthorised actor → `PermissionError` (original: `ValueError`) |
| swap rule 3 and rule 4 checks | green | `cancelled` order + unauthorised actor → `ValueError: order is not refundable…` (original: `PermissionError`) — leaks order status to an unauthorised caller |
| swap rule 4 and rule 5 checks | green | both raise `ValueError`; only the message differs (`amount 5000 exceeds…` vs `order is not refundable…`) — not distinguishable by exception type |
| `return dict(order["keys"][key])` on replay | green | replay result is equal but no longer the stored object (`again is o["keys"]["k"]` is `False`) |
| `role = (actor.get("role") or "").lower()` | green | `{"role": "ADMIN"}` is granted (original: `PermissionError`) |
| delete the `try/except GatewayError` wrapper | green | no behaviour change; the handler is dead code because the only mutation happens after the gateway call |

The last row is not a test gap: the `try/except GatewayError: raise` block is
redundant. It is harmless (the function is atomic by construction), but it is
not what provides rule 6's atomicity — the ordering is. Worth noting so a future
reader does not over-trust the handler.

### 6.4 Minor observations

- The suite never checks that an unauthorised actor is rejected *before* an
  invalid status is reported; see §6.3 row 2. This is the only gap here with an
  information-disclosure flavour.
- `compliance-log.md` §3 is titled "Negative controls, one per guard" while
  listing six controls for more than six guards; the heading should match the
  actual control set once the §4 breaks are folded in.
- No dependency on wall-clock, randomness, network or filesystem state in either
  the module or the tests; runs are deterministic and fast (12 tests, <0.01 s).

## 7. Missing guard tests

Ordered by risk. Each is a test the suite lacks today; each was proved absent by
a mutation that leaves all 12 tests green. None of them indicates a defect in the
current implementation — the code already behaves correctly in every case.

1. **Rule order: amount validation before permission (2 before 3).**
   `refund(order(), 0, gateway, {"id": "c2", "role": "customer"}, "k")` must raise
   `ValueError`, not `PermissionError`, and must not call the gateway.
   *Severity: medium.* The spec says rules are checked in order; a swap is
   currently invisible to the suite.
2. **Rule order: permission before status (3 before 4).**
   `refund(order(status="cancelled"), 10, gateway, {"id": "c2", "role": "customer"}, "k")`
   must raise `PermissionError`, not `ValueError`. *Severity: medium-high* — the
   swapped order tells an unauthorised caller whether the order is cancelled.
3. **Exact role matching.** `{"id": "c1", "role": "ADMIN"}` and
   `{"id": "c1", "role": "Admin"}` must raise `PermissionError`; role values are
   the exact lowercase strings in the spec, and a case-insensitive regression
   would silently widen privileged access. *Severity: medium.*
4. **Replay returns the stored object.**
   After a successful refund, `refund(...)` with the same key must return the
   identical object stored in `order["keys"][key]` (`assertIs`), not a copy, and
   returning a copy must not be able to corrupt or diverge from the stored
   result. *Severity: low.*
5. **Rule order: status before cap (4 before 5).** A cancelled order whose amount
   also exceeds the remainder must report the status error. Both paths raise
   `ValueError`, so this is only observable through the message; add it if the
   suite is meant to pin messages. *Severity: low / informational.*

Once tests 1–4 exist, every guard in `refunds.py` has both a passing test and a
successful negative control, and the seven auditor breaks in §4 can be promoted
into `controls/` and replayed by `controls/run_controls.py`.

## 8. Verdict

Implementation conforms to every rule and ordering requirement of
`refunds.md`; the shipped tests pass, all six Executor controls reproduce
exactly, and all seven auditor-added controls for previously uncontrolled guards
exit 0. The suite has the coverage gaps listed in §7, which are test debt rather
than defects — the code already satisfies each of them and the gaps are recorded
as required follow-up before the suite is used as a regression gate.

APPROVED
