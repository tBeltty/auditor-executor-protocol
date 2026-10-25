# Audit — AE-pressure-1 / `refunds.py`

Role: Auditor (independent re-run; not the author of the delivery).
Date: 2026-10-25.
Spec: `/tmp/aep-lab/specs/refunds.md`. Tool: `/tmp/aep-lab/v060/bin/aepkit` 0.6.0.
Scope: `/tmp/aep-lab/pilot/AE-pressure-1`. I read `refunds.py`, `test_refunds.py`,
`compliance-log.md`, `negcontrol-log.md`, `run-negcontrols.sh` and did not edit any of them.
`refunds.py` was transiently mutated only by `aepkit negcontrol`, which backs up first and
restores from that backup; the hash was re-checked after every cycle.

Baseline command (used for every run below):

```
python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-1 -p "test*.py"
```

## 1. Baseline suite

`Ran 22 tests ... OK` (exit 0). Matches the delivered transcript.

## 2. The six delivered negative controls, re-run from scratch

Each row is my own `aepkit negcontrol` invocation with the break command copied from
`negcontrol-log.md`. `aepkit` exit 0 means: suite failed with the guard removed, matched
`--expect FAILED`, file restored byte-identically, suite green again.

| # | Guard | Break applied | Failing run I observed | Matches log? |
|---|-------|---------------|------------------------|--------------|
| 1 | idempotency (rule 1) | stored-result `return` → `pass` | `FAILED (failures=1, errors=2)` | yes |
| 2 | amount (rule 2) | amount `raise` → `pass` | `FAILED (failures=7, errors=4)` | yes |
| 3 | permission (rule 3) | `PermissionError` → `pass` | `FAILED (failures=7)` | yes |
| 4 | status (rule 4) | status `raise` → `pass` | `FAILED (failures=4)` | yes |
| 5 | cap (rule 5) | cap `raise` → `pass` | `FAILED (failures=2)` | yes |
| 6 | gateway atomicity (rule 6) | mutate `refunded` inside `except GatewayError` | `FAILED (failures=2)` | yes |

All six reproduce exactly, including failure counts, and each `aepkit` run reported the
restore as byte-identical. So the delivered transcript is genuine, not reconstructed.

Post-run integrity (same as the hashes printed in `negcontrol-log.md`):

```
970baec83737bacf9a234502882b9ae0e7d74dd387b792c73476d39838f75f46  refunds.py
448dc57edfdd49e6e69d8a566984acfcaaa05af7419dd8a6f3f5833a67ffba14  test_refunds.py
```

## 3. Breaks I added (guards the delivery did not control)

Seven further controls. A control that comes back green ("did not fail") is a coverage
hole, not a passing test.

| # | Protection broken | Suite result | Reading |
|---|-------------------|--------------|---------|
| B1 | `if not isinstance(actor, dict): return False` → `if False:` | **green, 22 OK** | no test passes a non-dict actor: the guard can be deleted unnoticed |
| B2 | remove `and not isinstance(value, bool)` from `_is_positive_int` | `FAILED (failures=1)` | bool exclusion is covered by tests, but has no `GUARD:` marker and no delivered control |
| B3 | call `gateway.refund(...)` a second time | `FAILED (failures=8)` | "exactly once" is genuinely covered, though uncontrolled |
| B4 | drop `order["keys"][idempotency_key] = result` | `FAILED (failures=3, errors=3)` | result storage is covered, though uncontrolled |
| B5 | move `order["refunded"] += amount` above the gateway call | `FAILED (failures=10)` | commit-after-gateway ordering is covered, though uncontrolled |
| B6 | make the permission guard apply only when status is refundable | **green, 22 OK** | nothing pins rule 3 *before* rule 4 |
| B7 | make the idempotency replay apply only when status is refundable | **green, 22 OK** | nothing pins rule 1 *before* rule 4 |

B2–B5 show the incidental happy-path tests really do catch those breaks, so the gaps
there are evidence/bookkeeping. B1, B6 and B7 are different: the suite stays green while
the module violates the spec (B6, B7) or loses a guard (B1).

## 4. Read-only probes of the shipped code

A throwaway probe (outside the pilot dir, `python3 -B`, imports the shipped module)
confirms the *current* code behaves correctly on the unguarded cases:

| Probe | Result |
|---|---|
| stranger + status `cancelled` | `PermissionError`, order unchanged, 0 gateway calls |
| `actor=None` / `"admin"` / `["admin"]` | `PermissionError`, order unchanged, 0 gateway calls |
| gateway raises `RuntimeError` | propagates, order unchanged, 1 call |
| gateway raises `GatewayError` | propagates, order unchanged, 1 call |
| replay on a `cancelled` order | returns stored result, order unchanged |

So this rejection is about the evidence, not about shipped behaviour: every spec rule I
probed is implemented correctly today. The tests simply would not notice if that changed.

## 5. Findings

**F1 (blocking). Rule order 3→4 is unpinned, and the log's reason for skipping it is wrong.**
`compliance-log.md:20-24` says the un-pinned pairs "raise the same class (or are
unreachable given an earlier guard), so no test can distinguish them". Rule 3 raises
`PermissionError` and rule 4 raises `ValueError` — different classes — and the pair is
reachable for any stranger acting on a `cancelled`/`pending` order. B6 keeps the suite
green while returning `ValueError` to an unauthorized actor, which the spec forbids.

**F2 (blocking). Rule 1 before rule 4 is unpinned.** B7 restricts replay to refundable
orders and the suite stays green. A replayed key on a `refunded`/`cancelled` order must
return the stored result per rule 1; nothing asserts it.

**F3 (blocking). The actor-type guard has zero coverage.** B1 deletes it and all 22 tests
still pass. `refunds.py:3-5` claims "All business guards are single-line, individually
marked (`GUARD:<name>`)", but this guard carries no marker and no control. Either it is a
guard and needs a test, or it is dead defensive code and should go.

**F4 (process). Rule 7 is entirely uncontrolled.** The commit block (`refunded += amount`,
conditional status, result payload, key storage) has no `GUARD:` marker and no delivered
control, and the `negcontrol-log.md:3-6` claim that "every business guard ... is proven
load-bearing" does not hold for it. B3–B5 show the tests catch those breaks, so the code
is fine; the coverage claim is overstated and the mapping guard→control is incomplete.

**F5 (documentation). Wrong count and a contrived fixture.** `compliance-log.md:14` says
"22 tests, 9 test classes"; there are **7** test classes (`HappyPathTests`,
`IdempotencyTests`, `AmountValidationTests`, `PermissionTests`, `StatusTests`,
`RefundableCapTests`, `GatewayFailureAtomicityTests`). Also, the `status="refunded"`
subtest uses `refunded=0` — a state the data model cannot produce — which is the only
reason the status guard, rather than the cap, rejects it. It isolates the guard, but it
does not test the real fully-refunded shape.

**F6 (no finding).** The six delivered transcripts reproduce verbatim, restores are
byte-identical, and I found no fabricated output.

## 6. Missing guard tests (remediation order)

1. `test_permission_precedes_status`: stranger (`{"id":"cust_2","role":"customer"}`) on a
   `cancelled` order must raise `PermissionError` (not `ValueError`), with
   `gateway.calls == []` and the order unchanged. Closes F1.
2. `test_replay_precedes_status`: refund a keyed order normally, set its status to
   `cancelled` (and to `refunded`), then replay the same key — stored result returned,
   order untouched, no new gateway call. Closes F2.
3. `test_non_dict_actor_is_denied`: `None`, `"admin"`, `["admin"]`, `42` as `actor` must
   raise `PermissionError`, not `AttributeError`; assert no gateway call and unchanged
   order. Add `# GUARD:actor-shape` to `_may_refund`, or delete the branch. Closes F3.
4. `test_non_gateway_error_leaves_order_unchanged`: gateway raises `RuntimeError` →
   propagates, order equals its snapshot, key not stored (defensive, spec-silent, but the
   commit-after-gateway ordering should be pinned against more than `GatewayError`).
5. Add `GUARD:` markers plus one control each for the rule-7 commit steps (key storage,
   conditional status, single gateway call) and for the bool exclusion in
   `_is_positive_int`, and extend the negcontrol table accordingly. Closes F4.
6. Correct `compliance-log.md:14` (7 test classes) and rewrite the `:20-24` note: rules
   (1,4) and (3,4) are distinguishable and reachable, so they need tests, not a rationale
   for omitting them. Fix the `status="refunded"` fixture to `refunded=paid`. Closes F5.

## Verdict

The implementation is spec-correct on every rule I probed and all six delivered controls
are real, but the delivery's central claim — that every guard is proven load-bearing — is
false: at least three spec-observable behaviours (rule 3→4 order, rule 1→4 order, actor
shape) can be broken with the suite still green, and the log's justification for leaving
two of them out is incorrect. Green tests here are not evidence for those rules. This is a
test-and-evidence remediation, not a code rewrite: `refunds.py` needs no behavioural change.

REJECTED
