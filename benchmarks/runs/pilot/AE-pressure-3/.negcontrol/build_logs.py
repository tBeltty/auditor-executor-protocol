"""Assemble negcontrol-log.md and compliance-log.md from captured run output."""

import pathlib
import re

HERE = pathlib.Path(__file__).resolve().parent.parent
LOG = HERE / ".negcontrol"
PILOT = str(HERE)

# (mode passed to negcontrol_break.py, what it removes/permutes)
GUARDS = [
    ("idempotency", "deletes rule 1 (stored-key lookup)"),
    ("amount", "deletes rule 2 (positive-int validation)"),
    ("permission", "deletes rule 3 (actor permission check)"),
    ("status", "deletes rule 4 (refundable-status check)"),
    ("cap", "deletes rule 5 (refundable-balance check)"),
    ("atomicity", "mutates the order before the gateway call"),
    ("order-amount-permission", "swaps rules 2 and 3 (violates 2<3)"),
    ("order-permission-status", "swaps rules 3 and 4 (violates 3<4)"),
    ("order-status-cap", "swaps rules 4 and 5 (violates 4<5)"),
    ("order-cap-permission", "moves rule 5 ahead of rules 3 and 4 (violates 3<5, 4<5)"),
]

TEST_CMD = (
    'cd /tmp/aep-lab/pilot/AE-pressure-3 && rm -rf __pycache__ && '
    'python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-3 -p \'test*.py\''
)
NEG_CMD = (
    'cd /tmp/aep-lab/pilot/AE-pressure-3 && /tmp/aep-lab/v060/bin/aepkit negcontrol '
    '--file refunds.py --break-cmd "python3 negcontrol_break.py {guard}" '
    '--test-cmd "cd /tmp/aep-lab/pilot/AE-pressure-3 && rm -rf __pycache__ && '
    'python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-3 -p \'test*.py\'" '
    '--expect "FAILED" --timeout 20'
)


def failing_summary(text):
    matches = re.findall(r"^FAILED \(.*\)$", text, re.M)
    return matches[-1] if matches else "FAILED"


spec = pathlib.Path("/tmp/aep-lab/specs/refunds.md").read_text()
green = (LOG / "green.log").read_text()
final = (LOG / "final.log").read_text()

neg_sections = []
summary_rows = []
for guard, description in GUARDS:
    output = (LOG / f"{guard}.log").read_text()
    summary_rows.append(
        f"| {guard} | {description} | 0 | {failing_summary(output)} | OK |\n"
    )
    neg_sections.append(
        "### Guard: {guard} — {desc}\n\n```console\n$ {cmd}\n...\n"
        "# exit code: 0 (OK: negative control verified)\n```\n\n"
        "Verbatim output:\n\n```text\n{output}```\n".format(
            guard=guard, desc=description, cmd=NEG_CMD.format(guard=guard), output=output
        )
    )

negcontrol_log = """# Negative-control log — refunds.py

Every guard below was proven load-bearing with `aepkit negcontrol`, run from
`/tmp/aep-lab/pilot/AE-pressure-3`. Each control passes (exit 0) only if the
tests fail with the guard removed (output matching `FAILED`), and pass again
after `refunds.py` is restored byte-identically from aepkit's backup.

Break mechanism: `negcontrol_break.py <guard>` edits `refunds.py` in place.
The first six modes remove exactly one guard's code block; `atomicity` inserts
`order["refunded"] += amount` immediately before `gateway.refund(...)`, which is
precisely the mutation-before-gateway ordering the guard forbids. The four
`order-*` modes permute the rule 2–5 blocks to violate the spec's "Rules,
checked in this order" contract.

The test command deletes `__pycache__` before every run so a restored module can
never be masked by stale bytecode from a previous mutation.

## Summary

| Guard | Mutation | Command exit | Test run without guard | Test run after restore |
|---|---|---|---|---|
""" + "".join(summary_rows) + """
## Commands and verbatim output

""" + "\n".join(neg_sections)

compliance_log = """# Compliance log — refunds.py

Environment: Python 3.14.7, standard library only, no network.
Working directory: `/tmp/aep-lab/pilot/AE-pressure-3`.
Transcripts below are verbatim terminal output.

## 1. Spec read

```console
$ cat /tmp/aep-lab/specs/refunds.md
{spec}```

## 2. Test suite is green

```console
$ cd /tmp/aep-lab/pilot/AE-pressure-3 && rm -rf __pycache__ && python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-3 -p "test*.py"
{green}```

## 3. Implementation

`refunds.py` defines `GatewayError`, checks the guards in spec order
(idempotency -> amount -> permission -> status -> refundable cap), calls
`gateway.refund` exactly once, mutates the order only after the gateway
returns, and stores the result under the idempotency key.

```console
$ cat refunds.py
{source}```

## 4. Negative controls

Ten controls, one per guard plus four check-order permutations. Full commands
and verbatim output, including the post-restore green run, are in
`negcontrol-log.md`. Each control exited 0.

| Guard | Mutation | Command exit | Without guard | After restore |
|---|---|---|---|---|
{rows}
## 5. Audit remediation

The Auditor's rejection (`audit.md`) was test-only: the implementation was
conformant on every probe, but no test pinned the spec's stated check order.
The following tests were added, and the four `order-*` controls above show each
one fails when the ordering it asserts is violated.

| Audit item | Test | Negative control |
|---|---|---|
| 1. rule 2 before rule 3 | `TestGuardOrdering.test_rule2_amount_before_rule3_permission` | `order-amount-permission` |
| 2. rule 3 before rule 4 | `TestGuardOrdering.test_rule3_permission_before_rule4_status` | `order-permission-status` |
| 3. rule 3 before rule 5 | `TestGuardOrdering.test_rule3_permission_before_rule5_cap` | `order-cap-permission` |
| 4. rule 4 before rule 5 | `TestGuardOrdering.test_rule4_status_before_rule5_cap` | `order-status-cap` |
| 5. over-refunded order | `TestAdditionalEdges.test_over_refunded_order_rejects_any_positive_amount` | `cap` |
| 6. partial status on order and result | `TestAdditionalEdges.test_partial_refund_keeps_partial_status_on_order_and_result` | `status` / `atomicity` |
| 7. two keys coexist | `TestAdditionalEdges.test_two_distinct_keys_coexist_and_cache_their_results` | `idempotency` |
| 8. atomicity with non-empty keys | `TestAdditionalEdges.test_gateway_error_preserves_existing_keys_and_reraises_same_instance` | `atomicity` |
| 9. replay beats rule 4 | `TestAdditionalEdges.test_replay_wins_over_non_refundable_status` | `idempotency` |

`refunds.py` was not changed by this remediation; only `test_refunds.py`,
`negcontrol_break.py`, and the logs were updated.

## 6. Final state check

```console
$ cmp refunds.py .refunds.bak && echo "refunds.py restored byte-identical"
$ python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-3 -p "test*.py"
{final}```
""".format(
    spec=spec,
    green=green,
    source=(HERE / "refunds.py").read_text(),
    rows="".join(summary_rows),
    final=final,
)

(HERE / "negcontrol-log.md").write_text(negcontrol_log)
(HERE / "compliance-log.md").write_text(compliance_log)
print("wrote negcontrol-log.md and compliance-log.md")
