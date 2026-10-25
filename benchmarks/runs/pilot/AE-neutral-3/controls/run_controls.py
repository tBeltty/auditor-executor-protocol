"""Runs every negative control and writes the verbatim transcript to negcontrol-log.md."""

import pathlib
import subprocess

BASE = pathlib.Path("/tmp/aep-lab/pilot/AE-neutral-3")
AEPKIT = "/tmp/aep-lab/v060/bin/aepkit"
TEST_CMD = 'python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-neutral-3 -p "test*.py"'

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


def block(command, code, output):
    return "\n".join(
        [
            "```console",
            "$ " + command,
            output.rstrip("\n"),
            "(exit %d)" % code,
            "```",
        ]
    )


chunks = [
    "# Negative-control log — refunds.py",
    "",
    "Every guard in `refunds.py` is removed by a scripted break, the test suite is",
    "run against the broken file, and the original file is restored byte-for-byte.",
    "A control is only accepted when `aepkit negcontrol` exits 0: tests fail under",
    "the break, the failure output matches the expected test name, and tests pass",
    "again after restore.",
    "",
    "## Baseline: tests pass on the unmodified implementation",
    "",
]

code, output = run(TEST_CMD)
chunks.append(block(TEST_CMD, code, output))
if code != 0:
    raise SystemExit("baseline test run failed")

for label, script, expect in CONTROLS:
    command = (
        "%s negcontrol --file %s/refunds.py --break-cmd \"python3 %s/controls/%s\" "
        "--test-cmd '%s' --expect \"%s\" --timeout 20"
        % (AEPKIT, BASE, BASE, script, TEST_CMD, expect)
    )
    code, output = run(command)
    chunks.extend(["", "## Guard: %s" % label, "", block(command, code, output)])
    print("%-28s exit=%d" % (label, code))
    if code != 0:
        print(output)

pathlib.Path(BASE / "negcontrol-log.md").write_text("\n".join(chunks) + "\n")
print("wrote", BASE / "negcontrol-log.md")
