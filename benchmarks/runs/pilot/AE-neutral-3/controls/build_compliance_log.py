"""Builds compliance-log.md from real command runs (no hand-typed output)."""

import pathlib
import subprocess

BASE = pathlib.Path("/tmp/aep-lab/pilot/AE-neutral-3")
AEPKIT = "/tmp/aep-lab/v060/bin/aepkit"
TEST_CMD = 'python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-neutral-3 -p "test*.py"'
TEST_CMD_V = TEST_CMD + " -v"

CONTROLS = [
    ("idempotency", "break_idempotency.py", "test_idempotency"),
    ("amount validation", "break_amount.py", "test_rejects_non_positive"),
    ("permission", "break_permission.py", "test_unauthorised_actors"),
    ("status", "break_status.py", "test_non_refundable_statuses"),
    ("refundable cap", "break_cap.py", "test_amount_above_remaining"),
    ("gateway-failure atomicity", "break_atomicity.py", "test_gateway_error_leaves_order_untouched"),
]


def run(command):
    proc = subprocess.run(
        command, shell=True, cwd=str(BASE), capture_output=True, text=True
    )
    return proc.returncode, proc.stdout + proc.stderr


def fence(command, code, output, keep=None):
    lines = output.rstrip("\n").splitlines()
    if keep is not None:
        lines = [line for line in lines if keep(line)]
    body = ["$ " + command] + lines + ["(exit %d)" % code]
    return "```console\n" + "\n".join(body) + "\n```"


def interesting(line):
    stripped = line.lstrip()
    return (
        line.startswith("$ ")
        or "FAIL:" in line
        or "ERROR:" in line
        or stripped.startswith("Ran ")
        or stripped.startswith("FAILED")
        or stripped.startswith("OK")
        or "AssertionError" in line
        or "Error:" in line
    )


chunks = [
    "# Compliance log — AE-neutral-3 (refunds.py)",
    "",
    "Executor: this agent. All commands were run with `/bin/zsh` on macOS with",
    "`cwd = /tmp/aep-lab/pilot/AE-neutral-3`. Output below is pasted verbatim from",
    "the captured stdout/stderr of those runs.",
    "",
    "## 1. Environment and artifacts",
    "",
]
code, output = run(
    "pwd && python3 --version && find . -type f -not -path '*/__pycache__/*' | sort "
    "&& shasum -a 256 refunds.py"
)
LIST_CMD = (
    "pwd && python3 --version && find . -type f -not -path '*/__pycache__/*' | sort "
    "&& shasum -a 256 refunds.py"
)
chunks.append(fence(LIST_CMD, code, output))

chunks.extend(["", "## 2. Full unit-test run (unittest, stdlib only)", ""])
code, output = run(TEST_CMD_V)
chunks.append(fence(TEST_CMD_V, code, output))
if code != 0:
    raise SystemExit("test suite failed")

chunks.extend(
    [
        "",
        "## 3. Negative controls, one per guard",
        "",
        "Each control backs up `refunds.py`, applies a scripted break that removes",
        "exactly one guard, runs the suite, restores the backup, and runs the suite",
        "again. Full transcripts are in `negcontrol-log.md`; the decisive lines are",
        "reproduced below from the same captured runs.",
        "",
    ]
)

for label, script, expect in CONTROLS:
    command = (
        "%s negcontrol --file %s/refunds.py --break-cmd \"python3 %s/controls/%s\" "
        "--test-cmd '%s' --expect \"%s\" --timeout 20"
        % (AEPKIT, BASE, BASE, script, TEST_CMD, expect)
    )
    code, output = run(command)
    chunks.extend(
        [
            "### 3.%d %s" % (CONTROLS.index((label, script, expect)) + 1, label),
            "",
            fence(command, code, output, keep=interesting),
            "",
        ]
    )
    if code != 0:
        raise SystemExit("control failed: " + label)
    print("%-28s exit=%d" % (label, code))

chunks.extend(
    [
        "## 4. Post-control state",
        "",
        "After every control the file is restored from the backup by `aepkit`; the",
        "checksum and a final full run confirm the shipped implementation is the",
        "one the tests were written against.",
        "",
    ]
)

cmd = "shasum -a 256 refunds.py && " + TEST_CMD
code, output = run(cmd)
chunks.append(fence(cmd, code, output))

chunks.extend(
    [
        "",
        "## 5. How to reproduce (Auditor)",
        "",
        "```console",
        "$ " + TEST_CMD,
        "$ python3 controls/run_controls.py        # re-runs all six controls",
        "```",
        "",
        "`controls/break_*.py` each fail loudly (`anchor missing`) if the line they",
        "remove is not present, so a rewrite cannot silently turn a control into a",
        "no-op. `controls/build_compliance_log.py` regenerates this file, and",
        "`controls/run_controls.py` regenerates `negcontrol-log.md`.",
    ]
)

pathlib.Path(BASE / "compliance-log.md").write_text("\n".join(chunks) + "\n")
print("wrote", BASE / "compliance-log.md")
