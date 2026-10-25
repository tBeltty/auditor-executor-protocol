"""Run every negative control and append the verbatim transcript to
negcontrol-log.md.

Each row is (guard group, break name, regex the failing output must contain).
"""

import pathlib
import shlex
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
CRM = ROOT / "crm.py"
BREAK = ROOT / "negcontrol" / "break.py"
LOG = ROOT / "negcontrol-log.md"
AEPKIT = "/tmp/aep-lab/v060/bin/aepkit"
TEST_CMD = 'python3 -m unittest discover -s %s -p "test*.py"' % ROOT

CONTROLS = [
    ("email/name/source validation", "email", "test_rejects_email_without_at"),
    ("email/name/source validation", "name", "test_rejects_blank_name"),
    ("email/name/source validation", "source", "test_rejects_unknown_source"),
    ("duplicate detection", "duplicate", "test_duplicate_after_normalization_raises"),
    ("rep assignment and capacity", "capacity", "test_capacity_is_respected"),
    ("rep assignment and capacity", "lowest_load", "test_lowest_load_wins"),
    ("waiting queue", "queue_fifo", "test_queue_is_fifo"),
    ("waiting queue", "queue_capacity", "test_at_capacity_queue_does_not_overflow_capacity"),
    ("permission checks", "actor", "test_unknown_actor_rejected_everywhere"),
    ("permission checks", "ownership", "test_other_rep_cannot_qualify"),
    ("permission checks", "manager_only", "test_transfer_requires_manager"),
    ("qualification score threshold", "score", "test_score_below_threshold_is_rejected"),
    ("stage-transition rules", "transition", "test_skip_ahead_is_rejected"),
    ("big-deal approval", "bigdeal", "test_rep_needs_manager_above_50000"),
    ("discount limits", "discount_range", "test_pct_must_be_int_in_range"),
    ("discount limits", "discount_ceiling", "test_rep_ceiling_is_ten"),
    ("cumulative discount floor", "discount_floor", "test_beyond_thirty_percent_of_original_is_rejected"),
    ("atomicity", "atomicity", "test_failed_discount_does_not_move_amount_below_the_floor"),
    ("transfer rules", "transfer_target_role", "test_manager_cannot_be_target"),
    ("transfer rules", "transfer_same_owner", "test_same_owner_is_rejected"),
    ("transfer rules", "transfer_capacity", "test_target_at_capacity_is_rejected"),
]


def run(entry):
    group, name, expect = entry
    command = (
        "%s negcontrol --file %s --break-cmd %s --test-cmd %s --expect %s --timeout 20"
        % (
            AEPKIT,
            CRM,
            shlex.quote("python3 %s %s" % (BREAK, name)),
            shlex.quote(TEST_CMD),
            shlex.quote(expect),
        )
    )
    completed = subprocess.run(
        command, shell=True, capture_output=True, text=True, cwd=str(ROOT)
    )
    output = completed.stdout + completed.stderr
    return group, name, expect, command, completed.returncode, output


def main():
    failures = 0
    with LOG.open("a") as log:
        for entry in CONTROLS:
            group, name, expect, command, code, output = run(entry)
            log.write("\n## Guard group: %s -- break `%s`\n\n" % (group, name))
            log.write("```sh\n%s\n```\n\n" % command)
            log.write("Verbatim output (exit %d):\n\n```\n%s```\n\n" % (code, output))
            log.write("Verdict: %s\n" % ("PASS (exit 0)" if code == 0 else "FAIL (exit %d)" % code))
            log.flush()
            print("%-32s %-22s exit=%d %s" % (group, name, code, "ok" if code == 0 else "FAILED"))
            if code != 0:
                failures += 1
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
