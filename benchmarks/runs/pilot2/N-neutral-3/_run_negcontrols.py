#!/usr/bin/env python3
"""Run every negative control and append the verbatim transcript to negcontrol-log.md."""

import pathlib
import subprocess

ROOT = pathlib.Path("/tmp/aep-lab/pilot2/N-neutral-3")
AEPKIT = "/tmp/aep-lab/v060/bin/aepkit"
CRM = str(ROOT / "crm.py")
BREAK = str(ROOT / "_break.py")
TEST_CMD = 'python3 -m unittest discover -s %s -p "test*.py"' % ROOT

CONTROLS = [
    ("Email validation: malformed email must be rejected", "email-type"),
    ("Email validation: exactly one @ and a non-empty local part", "email-local"),
    ("Email validation: domain must contain an inner dot", "email-domain"),
    ("Name validation: non-empty string after strip()", "name"),
    ("Source validation: web/referral/event only", "source"),
    ("Duplicate detection on the normalized email", "duplicate"),
    ("Rep assignment: capacity filter decides who may receive work", "assign-capacity"),
    ("Rep assignment: load tie broken by smallest id", "assign-tie"),
    ("Rep assignment: unassignable leads join the FIFO queue", "waiting-enqueue"),
    ("Slot freeing: a rep may not be filled past capacity", "free-capacity"),
    ("Slot freeing: the waiting queue is FIFO", "queue-fifo"),
    ("Permission: unknown actor is rejected first", "permission-actor"),
    ("Permission: only the owner or a manager may act", "permission-owner"),
    ("Qualification: score threshold of 30", "qualify-score"),
    ("Stage transition: only lost or the immediate next stage", "stage-next"),
    ("Stage transition: final stages are frozen", "stage-final"),
    ("Big-deal approval: negotiation above 50000 needs a manager", "bigdeal"),
    ("Discount: pct must be an int in 1..30", "discount-range"),
    ("Discount: a rep may use at most 10 percent", "discount-rep"),
    ("Discount: final opportunities are frozen", "discount-final"),
    ("Discount: cumulative floor of 70 percent of the original amount", "discount-floor"),
    ("Transfer: manager only", "transfer-manager"),
    ("Transfer: new owner must be a rep", "transfer-role"),
    ("Transfer: final opportunities are frozen", "transfer-final"),
    ("Transfer: new owner must differ from the current owner", "transfer-same"),
    ("Transfer: new owner must be below capacity", "transfer-cap"),
    ("Atomicity: a failed add_lead does not burn an id", "atomic-id"),
    ("Atomicity: a failed convert does not mutate the lead", "atomic-state"),
    ("Atomicity: a failed discount does not log", "atomic-log"),
]

HEADER = """# Negative-control log

Every entry below removes exactly one guard from `crm.py` with `_break.py`
(which asserts that the guard line it patches exists exactly once), runs the
full unit suite with `aepkit negcontrol`, and requires three things: the suite
fails under the break, the failure output matches `/FAILED/`, and the suite
passes again after the byte-identical restore. Exit code 0 means the control
held.

Test command used throughout:

```sh
python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"
```

Baseline before any control: `Ran 86 tests ... OK`.

"""


def main():
    log = [HEADER]
    failures = []
    print("baseline")
    baseline = subprocess.run(
        TEST_CMD, shell=True, cwd=str(ROOT), capture_output=True, text=True
    )
    log.append("```\n$ %s\n%s```\n\n" % (TEST_CMD, baseline.stdout + baseline.stderr))
    if baseline.returncode != 0:
        failures.append("baseline")

    for number, (title, mode) in enumerate(CONTROLS, start=1):
        command = (
            "%s negcontrol --file %s --break-cmd \"python3 %s %s\" "
            "--test-cmd '%s' --expect \"FAILED\" --timeout 20"
            % (AEPKIT, CRM, BREAK, mode, TEST_CMD)
        )
        print("%02d %-16s %s" % (number, mode, title))
        done = subprocess.run(
            command, shell=True, cwd=str(ROOT), capture_output=True, text=True
        )
        output = (done.stdout + done.stderr).rstrip("\n")
        block = [
            "## %d. %s\n" % (number, title),
            "Guard removed: `%s` (mode `%s`).\n" % (mode, mode),
            "```sh\n$ %s\n```\n" % command,
            "Verbatim output:\n",
            "```\n%s\n```\n" % output,
            "Exit code: %d -- %s\n" % (
                done.returncode,
                "control held" if done.returncode == 0 else "CONTROL FAILED",
            ),
        ]
        log.append("\n".join(block))
        if done.returncode != 0:
            failures.append(mode)

    path = ROOT / "negcontrol-log.md"
    path.write_text("\n".join(log))
    print("\nlog written: %s" % path)
    if failures:
        print("FAILURES: %s" % ", ".join(failures))
        raise SystemExit(1)
    print("ALL %d CONTROLS PASSED" % len(CONTROLS))


if __name__ == "__main__":
    main()
