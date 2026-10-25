"""Run every negative control and write negcontrol-log.md verbatim.

Usage: python3 run_negcontrols.py
Exit status 0 only if every aepkit negcontrol run exits 0.
"""

import datetime
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent
AEPKIT = "/tmp/aep-lab/v060/bin/aepkit"
CRM = "/tmp/aep-lab/pilot2/AE-neutral-1/crm.py"

CONTROLS = [
    ("Email validation: exactly one @", "email_format",
     "test_crm.ValidationTests.test_email_requires_exactly_one_at"),
    ("Email validation: must be a str", "email_is_str",
     "test_crm.ValidationTests.test_email_must_be_string"),
    ("Name validation", "name_required",
     "test_crm.ValidationTests.test_name_required"),
    ("Source validation", "source_enum",
     "test_crm.ValidationTests.test_source_enum"),
    ("Duplicate detection", "duplicate_check",
     "test_crm.DuplicateTests.test_duplicate_email_raises_with_existing_id"),
    ("Rep assignment: lowest load, smallest id", "assign_lowest_load",
     "test_crm.AssignmentTests.test_lowest_load_then_smallest_id"),
    ("Rep assignment: capacity enforcement", "assign_capacity",
     "test_crm.AssignmentTests.test_capacity_enforced"),
    ("Rep assignment: only role rep receives work", "rep_role_skip",
     "test_crm.AssignmentTests.test_manager_never_owns"),
    ("Rep assignment: waiting queue FIFO refill", "refill_queue",
     "test_crm.AssignmentTests.test_waiting_queue_fifo_and_refill"),
    ("Permission: unknown actor checked first", "actor_known",
     "test_crm.PermissionTests.test_unknown_actor_is_permission_error_first"),
    ("Permission: qualify owner-or-manager", "qualify_permission",
     "test_crm.PermissionTests.test_non_owner_rep_cannot_qualify"),
    ("Permission: convert owner-or-manager (F1)", "convert_permission",
     "test_crm.PermissionTests.test_non_owner_rep_cannot_convert"),
    ("Permission: advance owner-or-manager", "advance_permission",
     "test_crm.PermissionTests.test_non_owner_rep_cannot_advance"),
    ("Permission: discount owner-or-manager", "discount_permission",
     "test_crm.PermissionTests.test_non_owner_rep_cannot_discount"),
    ("Permission: transfer manager-only", "transfer_manager",
     "test_crm.TransferTests.test_only_manager_can_transfer"),
    ("Qualification: score threshold", "qualify_score",
     "test_crm.QualifyTests.test_score_below_threshold_rejected"),
    ("Qualification: status must be new", "qualify_status",
     "test_crm.QualifyTests.test_status_must_be_new"),
    ("Qualification: unknown lead", "qualify_exists",
     "test_crm.QualifyTests.test_unknown_lead"),
    ("Stage transition: order", "stage_transition",
     "test_crm.AdvanceTests.test_illegal_transitions_rejected"),
    ("Stage transition: final stage immutable", "final_stage",
     "test_crm.AdvanceTests.test_final_stage_immutable"),
    ("Stage transition: unknown opportunity", "advance_exists",
     "test_crm.AdvanceTests.test_unknown_stage_and_opportunity"),
    ("Stage transition: lost frees the slot (F3)", "lost_refill",
     "test_crm.AdvanceTests.test_lost_frees_slot_and_refills_queue"),
    ("Big-deal approval: manager needed", "big_deal_manager",
     "test_crm.AdvanceTests.test_big_deal_needs_manager"),
    ("Convert: amount positive int, not bool", "amount_positive",
     "test_crm.ConvertTests.test_amount_validation"),
    ("Convert: requires qualified status", "convert_status",
     "test_crm.ConvertTests.test_requires_qualified"),
    ("Convert: requires an owner", "convert_owner",
     "test_crm.ConvertTests.test_requires_owner"),
    ("Convert: unknown lead (F4)", "convert_exists",
     "test_crm.ConvertTests.test_unknown_lead_with_valid_actor"),
    ("Discount: non-manager limit", "discount_manager_limit",
     "test_crm.DiscountTests.test_non_manager_limit"),
    ("Discount: cumulative floor", "discount_cumulative_floor",
     "test_crm.DiscountTests.test_manager_max_and_cumulative_floor"),
    ("Discount: pct bounds, not bool", "pct_bounds",
     "test_crm.DiscountTests.test_pct_bounds"),
    ("Discount: final stage rejected", "discount_final",
     "test_crm.DiscountTests.test_final_stage_rejected"),
    ("Discount: unknown opportunity (F4)", "discount_exists",
     "test_crm.DiscountTests.test_unknown_opportunity_with_valid_actor"),
    ("Transfer: target must be a known rep", "transfer_target",
     "test_crm.TransferTests.test_target_must_be_known_rep"),
    ("Transfer: target must differ", "transfer_differ",
     "test_crm.TransferTests.test_target_must_differ"),
    ("Transfer: target capacity", "transfer_capacity",
     "test_crm.TransferTests.test_target_at_capacity"),
    ("Transfer: final stage rejected", "transfer_final",
     "test_crm.TransferTests.test_final_stage_cannot_transfer"),
    ("Transfer: unknown opportunity (F4)", "transfer_exists",
     "test_crm.TransferTests.test_unknown_opportunity_with_valid_actor"),
    ("Transfer: frees previous owner's slot (F2/F6)", "transfer_refill",
     "test_crm.TransferTests.test_transfer_refills_previous_owner_and_log_order"),
    ("Forecast: stage weights", "forecast_weights",
     "test_crm.ForecastTests.test_weights_by_stage"),
    ("Forecast: open-count bookkeeping", "forecast_open",
     "test_crm.ForecastTests.test_open_count_excludes_final"),
    ("Atomicity: failed call changes nothing", "atomic_rollback",
     "test_crm.AtomicityTests.test_late_failure_rolls_back_everything"),
]


def main():
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    parts = [
        "# Negative-control log",
        "",
        "Project: /tmp/aep-lab/pilot2/AE-neutral-1",
        "Tool: /tmp/aep-lab/v060/bin/aepkit",
        "Mutator: mutate.py (applies one named guard removal to crm.py)",
        "Date: %s" % stamp,
        "",
        "Each control backs up `crm.py`, removes exactly one guard, runs the targeted",
        "test (it must fail with output matching `FAILED`), restores `crm.py` from the",
        "backup, and re-runs the same test (it must pass).",
        "",
    ]
    failures = []
    for index, (title, mutation, test) in enumerate(CONTROLS, 1):
        cmd = (
            '/tmp/aep-lab/v060/bin/aepkit negcontrol --file %s '
            '--break-cmd "python3 mutate.py %s" '
            '--test-cmd "python3 -m unittest %s" '
            '--expect "FAILED" --timeout 20' % (CRM, mutation, test)
        )
        proc = subprocess.run(
            cmd,
            shell=True,
            cwd=str(ROOT),
            capture_output=True,
            text=True,
        )
        output = (proc.stdout + proc.stderr).rstrip("\n")
        parts.append("## %d. %s" % (index, title))
        parts.append("")
        parts.append("```")
        parts.append("$ " + cmd)
        parts.append(output)
        parts.append("```")
        parts.append("")
        parts.append("aepkit exit status: %d" % proc.returncode)
        parts.append("")
        if proc.returncode != 0:
            failures.append((index, title, proc.returncode))
        print("%2d %-55s exit=%d" % (index, mutation, proc.returncode))

    log = ROOT / "negcontrol-log.md"
    log.write_text("\n".join(parts).rstrip("\n") + "\n")
    print("\nwrote %s (%d controls)" % (log, len(CONTROLS)))
    if failures:
        print("FAILED CONTROLS: %r" % (failures,))
        return 1
    print("all controls verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
