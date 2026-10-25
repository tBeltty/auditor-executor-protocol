"""Run every negative control and append command + verbatim output to the log."""

import subprocess
from pathlib import Path

BASE = Path("/tmp/aep-lab/pilot2/N-neutral-1")
AEPKIT = "/tmp/aep-lab/v060/bin/aepkit"
BREAK = "python3 %s/_negctl_break.py" % BASE
TEST = "python3 -m unittest discover -s %s -p 'test*.py'" % BASE
LOG = BASE / "negcontrol-log.md"

CONTROLS = [
    ("email validation", "email: every sub-rule disabled at once",
     "%s kill email_str email_at email_local email_dot" % BREAK, "test_email_"),
    ("email validation", "email: exactly-one-@ rule removed",
     "%s kill email_at" % BREAK, "test_email_requires_exactly_one_at"),
    ("email validation", "email: non-empty local part rule removed",
     "%s kill email_local" % BREAK, "test_email_requires_local_part"),
    ("email validation", "email: inner-dot-in-domain rule removed",
     "%s kill email_dot" % BREAK, "test_email_requires_inner_dot_in_domain"),
    ("email validation", "email: str-type rule removed",
     "%s kill email_str" % BREAK, "test_email_not_str"),
    ("name validation", "name: str + non-empty rule removed",
     "%s kill name_str" % BREAK, "test_name_must_be_str_and_non_empty"),
    ("source validation", "source: allow-list removed",
     "%s kill source_valid" % BREAK, "test_source_must_be_known"),
    ("duplicate detection", "duplicate check removed",
     "%s kill dup" % BREAK, "test_duplicate"),
    ("rep assignment / capacity / waiting queue", "capacity limit removed when picking a rep",
     "%s kill assign_capacity" % BREAK, "test_capacity_full_sends_lead_to_waiting_queue"),
    ("rep assignment / capacity / waiting queue", "tie-break flipped to largest id",
     "%s sub assign_tie 'if best is None or load <= best[0]:'" % BREAK,
     "test_tie_break_prefers_smallest_id"),
    ("rep assignment / capacity / waiting queue", "lead no longer enqueued when no rep is free",
     "%s kill queue_push" % BREAK, "test_waiting_queue_is_fifo_on_freed_slot"),
    ("rep assignment / capacity / waiting queue", "drain ignores capacity",
     "%s kill drain_capacity" % BREAK, "test_drain_stops_at_capacity"),
    ("rep assignment / capacity / waiting queue", "drain ignores an empty queue",
     "%s kill drain_empty" % BREAK, "pop from empty list"),
    ("permission checks", "manager branch of the owner-or-manager check removed",
     "%s sub perm_manager 'return True'" % BREAK, "test_non_owner_rep_cannot_act"),
    ("permission checks", "owner branch of the owner-or-manager check removed",
     "%s kill perm_owner" % BREAK, "test_owner_can_act"),
    ("permission checks", "unknown-actor rejection removed",
     "%s kill actor_known" % BREAK, "test_unknown_actor"),
    ("qualification score threshold", "score >= 30 gate removed",
     "%s kill qualify_score" % BREAK, "test_score_below_threshold_cannot_qualify"),
    ("stage-transition rules", "unknown stage name accepted",
     "%s kill advance_stage_valid" % BREAK, "test_advance_stage_name_validated_before_permission"),
    ("stage-transition rules", "immediate-next-stage rule removed",
     "%s kill advance_order" % BREAK, "test_advance_requires_immediate_next_stage"),
    ("stage-transition rules", "final-stage lock removed",
     "%s kill advance_final" % BREAK, "test_advance_rejects_final_opportunity"),
    ("big-deal approval", "manager requirement above 50000 removed",
     "%s kill advance_bigdeal" % BREAK, "test_big_deal_requires_manager"),
    ("discount limits and cumulative floor", "pct range/type check removed",
     "%s kill discount_pct" % BREAK, "test_discount_pct_validation"),
    ("discount limits and cumulative floor", "non-manager 10% cap removed",
     "%s kill discount_rep_limit" % BREAK, "test_discount_rep_limit_is_ten"),
    ("discount limits and cumulative floor", "70% cumulative floor removed",
     "%s kill discount_floor" % BREAK, "test_discount_cumulative_floor"),
    ("discount limits and cumulative floor", "final-stage discount lock removed",
     "%s kill discount_final" % BREAK, "test_discount_rejects_final_stage"),
    ("transfer rules", "manager-only rule removed",
     "%s kill transfer_manager" % BREAK, "test_transfer_is_manager_only"),
    ("transfer rules", "target must be a known rep: rule removed",
     "%s kill transfer_target" % BREAK, "test_transfer_target_must_be_known_rep"),
    ("transfer rules", "same-owner rule removed",
     "%s kill transfer_same" % BREAK, "test_transfer_rejects_same_owner"),
    ("transfer rules", "target capacity rule removed",
     "%s kill transfer_capacity" % BREAK, "test_transfer_rejects_target_at_capacity"),
    ("transfer rules", "final-stage transfer lock removed",
     "%s kill transfer_final" % BREAK, "test_transfer_rejects_final_stage"),
    ("atomicity (failed call changes nothing, logs nothing)", "log entry written before the failing guard (qualify)",
     "%s insert qualify_score 'self.log.append((\"qualify\", lead_id, actor))'" % BREAK,
     "test_atomic_log_qualify"),
    ("atomicity (failed call changes nothing, logs nothing)", "lead status mutated before the failing guard (convert)",
     "%s insert convert_status 'lead[\"status\"] = \"converted\"'" % BREAK,
     "test_atomic_state_convert"),
    ("atomicity (failed call changes nothing, logs nothing)", "opp stage mutated before the failing guard (advance)",
     "%s insert advance_bigdeal 'opp[\"stage\"] = stage'" % BREAK,
     "test_atomic_advance_bigdeal"),
    ("atomicity (failed call changes nothing, logs nothing)", "amount mutated before the failing floor guard (discount)",
     "%s insert discount_floor 'opp[\"amount\"] = new_amount'" % BREAK,
     "test_atomic_discount_floor_failure"),
]


def main():
    failures = []
    header = [
        "# Negative-control log",
        "",
        "Every control below runs `/tmp/aep-lab/v060/bin/aepkit negcontrol`, which backs up",
        "`crm.py`, applies one break, runs the test suite, requires the output to match",
        "`--expect`, restores the file byte-for-byte, and re-runs the suite.",
        "A control passes (exit 0) only when the tests fail under the break and pass after restore.",
        "",
    ]
    LOG.write_text("\n".join(header) + "\n")
    for index, (group, label, break_cmd, expect) in enumerate(CONTROLS, start=1):
        command = [
            AEPKIT, "negcontrol",
            "--file", str(BASE / "crm.py"),
            "--break-cmd", break_cmd,
            "--test-cmd", TEST,
            "--expect", expect,
            "--timeout", "20",
        ]
        printable = " ".join(
            piece if " " not in piece else '"%s"' % piece for piece in command
        )
        result = subprocess.run(command, capture_output=True, text=True)
        output = (result.stdout + result.stderr).rstrip()
        verdict = "PASS (exit 0)" if result.returncode == 0 else "FAIL (exit %d)" % result.returncode
        block = [
            "## %d. %s" % (index, group),
            "",
            "Case: %s" % label,
            "",
            "```sh",
            "$ " + printable,
            "```",
            "",
            "Verdict: **%s**" % verdict,
            "",
            "```text",
            output,
            "```",
            "",
        ]
        with LOG.open("a") as handle:
            handle.write("\n".join(block) + "\n")
        print("%02d %-58s %s" % (index, group[:58], verdict))
        if result.returncode != 0:
            failures.append((index, group, label, output))
    print("\n%d/%d controls passed" % (len(CONTROLS) - len(failures), len(CONTROLS)))
    for item in failures:
        print("\n--- failed control %d (%s): %s\n%s" % item)


if __name__ == "__main__":
    main()
