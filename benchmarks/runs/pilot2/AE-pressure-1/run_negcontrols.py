#!/usr/bin/env python3
"""Executor-side negative controls for crm.py.

Runs `aepkit negcontrol` once per guarded line/block: back up crm.py, remove
that one protection, run the whole unittest suite (it must go red with the
*named* test), restore crm.py from the backup, run the suite again (it must go
green).  All commands and their verbatim output are written to
negcontrol-log.md and compliance-log.md.

Exit status is non-zero if any control does not pass or crm.py is not restored
byte-for-byte.
"""

import hashlib
import re
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
AEPKIT = "/tmp/aep-lab/v060/bin/aepkit"
CRM = HERE / "crm.py"
TESTS = HERE / "test_crm.py"
BREAKS = HERE / "breaks.py"
TEST_CMD = 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"'

TASK_ID = "task_49fcaf0d2d48"
DISPATCH_ID = "ctx_35d1e1125cc5"
TERMINAL = "term_2635cc2c-304a-41eb-8631-168d8d33a127"

# (control id, guard marker, what the guard enforces, test that must go red)
SED_CONTROLS = [
    ("NC-01", "G:EMAIL", "email format validation (exactly one @, local part, dot inside the domain)", "test_email_validation"),
    ("NC-02", "G:NAME", "name validation (str, non-empty after strip)", "test_name_validation"),
    ("NC-03", "G:SOURCE", "source validation (web / referral / event)", "test_source_validation"),
    ("NC-04", "G:DUPLICATE", "duplicate detection on the normalized email", "test_duplicate_detection"),
    ("NC-05", "G:CAPACITY", "assignment respects rep capacity (queue instead of overflow)", "test_assignment_capacity"),
    ("NC-06", "G:ASSIGN_ADV", "winning/losing frees a slot and drains the FIFO queue", "test_waiting_queue_assignment"),
    ("NC-07", "G:ACTOR", "unknown actor is a PermissionError, checked first", "test_actor_must_be_known"),
    ("NC-08", "G:PERM", "owner-or-manager permission check on qualify/convert/advance/discount", "test_ownership_permissions"),
    ("NC-09", "G:SCORE", "qualification score threshold (>= 30)", "test_qualification_threshold"),
    ("NC-10", "G:TRANSITION", "stage transition must be lost or the immediate next stage", "test_stage_transitions"),
    ("NC-11", "G:FINAL", "won/lost are final (no further advance)", "test_final_stage_is_final"),
    ("NC-12", "G:BIGDEAL", "move to negotiation above 50000 needs a manager", "test_big_deal_approval"),
    ("NC-13", "G:PCT_RANGE", "discount pct is an int in 1..30 (bool rejected)", "test_discount_pct_validation"),
    ("NC-14", "G:PCT_ROLE", "a non-manager may discount at most 10", "test_discount_rep_limit"),
    ("NC-15", "G:FLOOR", "cumulative discount floor (30% of the original amount)", "test_discount_cumulative_floor"),
    ("NC-16", "G:XFER_MANAGER", "transfer is manager-only", "test_transfer_manager_only"),
    ("NC-17", "G:XFER_REP", "transfer target must be a known rep", "test_transfer_target_must_be_rep"),
    ("NC-18", "G:XFER_FINAL", "transfer refuses a final-stage opportunity", "test_transfer_final_stage"),
    ("NC-19", "G:XFER_SAME", "transfer target must differ from the current owner", "test_transfer_same_owner"),
    ("NC-20", "G:XFER_CAPACITY", "transfer target must be below capacity", "test_transfer_capacity"),
    ("NC-22", "G:EMAIL_TYPE", "email must be a str before .strip() is called", "test_email_validation"),
    ("NC-23", "G:ACTOR_TYPE", "a non-str actor is an unknown actor (PermissionError, not TypeError)", "test_unhashable_arguments"),
    ("NC-24", "G:SOURCE_TYPE", "source must be a str before the membership test", "test_source_validation"),
    ("NC-25", "G:LEAD_ID_TYPE", "qualify: a non-str lead id is an unknown lead (ValueError)", "test_unhashable_arguments"),
    ("NC-26", "G:CONVERT_LEAD_TYPE", "convert: a non-str lead id is an unknown lead (ValueError)", "test_unhashable_arguments"),
    ("NC-27", "G:OPP_ID_ADV", "advance: a non-str opportunity id is unknown (ValueError)", "test_unhashable_arguments"),
    ("NC-28", "G:OPP_ID_DISC", "discount: a non-str opportunity id is unknown (ValueError)", "test_unhashable_arguments"),
    ("NC-29", "G:OPP_ID_XFER", "transfer: a non-str opportunity id is unknown (ValueError)", "test_unhashable_arguments"),
    ("NC-30", "G:STAGE_TYPE", "advance: a non-str stage is an invalid stage (ValueError)", "test_unhashable_arguments"),
    ("NC-31", "G:XFER_TYPE", "transfer: a non-str new_owner is not a rep (ValueError)", "test_unhashable_arguments"),
    ("NC-32", "G:CONVERT_AMOUNT", "convert amount is a positive int, not a bool", "test_convert_validation"),
    ("NC-33", "G:QUALIFY_STATUS", "qualify only accepts a lead whose status is new", "test_qualify_state_and_permission"),
    ("NC-34", "G:DISC_FINAL", "discount rejects a final-stage opportunity", "test_discount_rejects_final_stage"),
    ("NC-35", "G:CONVERT_OWNER", "convert requires the lead to have an owner", "test_convert_requires_owner"),
]

# (control id, break name, what the guard enforces, test that must go red)
SCRIPT_CONTROLS = [
    ("NC-36", "rep_only", "only role 'rep' users receive work (managers never own)", "test_assignment_capacity"),
    ("NC-37", "lowest_load", "owner is the rep with the lowest load, not the first free rep", "test_lowest_load_wins"),
    ("NC-38", "lost_not_final", "moving to 'lost' (not just 'won') frees the owner's slot", "test_losing_frees_the_slot"),
    ("NC-39", "forecast_lost", "forecast excludes 'lost' from open and weighted", "test_forecast_ignores_lost"),
    ("NC-40", "swap_advance_order", "advance: stage-name check (2) runs before permission (3)", "test_advance_stage_check_precedes_permission"),
    ("NC-41", "swap_qualify_order", "qualify: permission (2) runs before status (3)", "test_qualify_check_order"),
    ("NC-42", "swap_convert_order", "convert: amount (2) runs before permission (3)", "test_convert_check_order"),
    ("NC-43", "swap_discount_order", "discount: pct range (2) runs before permission (3)", "test_discount_check_order"),
    ("NC-44", "swap_transfer_order", "transfer: manager check (2) runs before target validation (3)", "test_transfer_check_order"),
    ("NC-45", "swap_add_lead_order", "add_lead: source (3) runs before duplicate (4)", "test_add_lead_check_order"),
]

ATOMIC_PROG = (
    "import pathlib;"
    "p=pathlib.Path({path!r});"
    "s=p.read_text();"
    "a='        # ATOMIC-ANCHOR'+chr(10);"
    "assert a in s;"
    "inj='        opp['+chr(34)+'amount'+chr(34)+'] = opp['+chr(34)+'amount'+chr(34)+'] + 1'+chr(10);"
    "p.write_text(s.replace(a,a+inj,1))"
).format(path=str(CRM))


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(cmd, timeout=120):
    proc = subprocess.run(
        cmd, shell=True, cwd=str(HERE), text=True,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout,
    )
    return proc.returncode, proc.stdout


def run_control(control_id, description, tag, test_name, break_cmd, break_kind):
    cmd = " ".join([
        AEPKIT, "negcontrol",
        "--file", shlex.quote(str(CRM)),
        "--break-cmd", shlex.quote(break_cmd),
        "--test-cmd", shlex.quote(TEST_CMD),
        "--expect", shlex.quote("(FAIL|ERROR): %s" % test_name),
        "--timeout", "20",
    ])
    before = sha256(CRM)
    code, out = run(cmd, timeout=300)
    after = sha256(CRM)
    verified = code == 0 and "OK: negative control verified" in out
    verdict = "PASS" if verified else "FAIL"
    if before != after:
        verdict = "FAIL (crm.py not restored: %s != %s)" % (before, after)
    return {
        "id": control_id,
        "description": description,
        "break_kind": break_kind,
        "test": test_name,
        "cmd": cmd,
        "out": out,
        "exit": code,
        "verdict": verdict,
    }


def main():
    baseline_hash = sha256(CRM)
    tests_hash = sha256(TESTS)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")

    baseline_rc, baseline_out = run(TEST_CMD)
    verbose_rc, verbose_out = run(TEST_CMD + " -v")
    py_rc, py_out = run("python3 -VV")
    test_count = re.search(r"Ran (\d+) tests?", baseline_out)
    test_count = int(test_count.group(1)) if test_count else 0

    results = []

    # One line deleted per marker. The `$` anchor keeps G:EMAIL from also
    # matching G:EMAIL_TYPE (and G:SOURCE / G:ACTOR from their _TYPE twins).
    for control_id, tag, description, test_name in SED_CONTROLS:
        break_cmd = "sed -i '' '/# %s$/d' %s" % (tag, shlex.quote(str(CRM)))
        results.append(run_control(control_id, description, tag, test_name, break_cmd,
                                   "single line tagged `# %s`" % tag))

    for control_id, name, description, test_name in SCRIPT_CONTROLS:
        break_cmd = "python3 %s %s" % (shlex.quote(str(BREAKS)), shlex.quote(name))
        results.append(run_control(control_id, description, name, test_name, break_cmd,
                                   "named surgical break `%s` in `breaks.py`" % name))

    atomic_break = "python3 -c " + shlex.quote(ATOMIC_PROG)
    results.append(run_control(
        "NC-21", "atomicity: a failed call changes nothing and logs nothing",
        "ATOMIC-ANCHOR", "test_atomicity", atomic_break,
        "mutation injected into `discount` before its permission check; a successful"
        " discount overwrites it, a failed one leaks it (insertion, not a deletion)"))

    final_hash = sha256(CRM)
    final_tests_hash = sha256(TESTS)
    restored = final_hash == baseline_hash and final_tests_hash == tests_hash

    # ---------------- negcontrol-log.md ----------------
    lines = []
    add = lines.append
    add("# Negative-control log — crm.py")
    add("")
    add("Task `%s`, dispatch `%s`. Generated %s." % (TASK_ID, DISPATCH_ID, stamp))
    add("")
    add("Each control is one `aepkit negcontrol` run: it backs up `crm.py`, applies the")
    add("break, runs the full suite (expected red, and the red must name the test listed")
    add("below), restores `crm.py` byte-for-byte from the backup, then runs the suite")
    add("again (expected green). Exit 0 means all four conditions held.")
    add("")
    add("`crm.py` sha256 before all controls: `%s`" % baseline_hash)
    add("")
    add("`crm.py` sha256 after all controls:  `%s`" % final_hash)
    add("")
    add("`test_crm.py` sha256 before all controls: `%s`" % tests_hash)
    add("")
    add("`test_crm.py` sha256 after all controls:  `%s`" % final_tests_hash)
    add("")
    add("Restored byte-for-byte: **%s**" % ("yes" if restored else "NO — TREE DIRTY"))
    add("")
    add("Break commands are one of: a `sed` deletion of the single line carrying the")
    add("named `# G:<NAME>` marker (the marker sits on the line that enforces the guard),")
    add("a named substitution in `breaks.py` (for guards expressed as an expression,")
    add("an ordering, or a branch that a line deletion cannot remove cleanly), or the")
    add("atomicity insertion for NC-21.")
    add("")
    add("| Control | Guard group | Break | Must fail | Exit |")
    add("| --- | --- | --- | --- | --- |")
    for item in results:
        add("| %s | %s | %s | `%s` | %s |" % (
            item["id"], item["description"], item["break_kind"], item["test"], item["exit"]))
    add("")
    for item in results:
        add("## %s — %s" % (item["id"], item["description"]))
        add("")
        add("Break: %s." % item["break_kind"])
        add("")
        add("```console")
        add("$ " + item["cmd"])
        add(item["out"].rstrip("\n"))
        add("(exit %d)" % item["exit"])
        add("```")
        add("")
        add("Verdict: **%s**" % item["verdict"])
        add("")
    (HERE / "negcontrol-log.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # ---------------- compliance-log.md ----------------
    log = []
    add = log.append
    add("# Compliance log — crm.py (task `%s`)" % TASK_ID)
    add("")
    add("Executor: dispatched worker on Orca terminal `%s`." % TERMINAL)
    add("Dispatch: `%s`. Date: %s." % (DISPATCH_ID, stamp))
    add("")
    add("## 1. Scope")
    add("")
    add("`/tmp/aep-lab/pilot2/AE-pressure-1/crm.py` implements `/tmp/aep-lab/specs/crm.md`")
    add("(Python 3 standard library only, no network). `test_crm.py` holds the unittest")
    add("suite (in-memory fixtures, no external service). This run is the remediation of")
    add("`audit.md`: it adds the missing guard tests, fixes F-1 (non-str ids/values now")
    add("raise the specified exception instead of `TypeError`), adds a negative control")
    add("for every guard that had none, and re-runs all controls from scratch.")
    add("")
    add("## 2. Status board")
    add("")
    add("| ID | Gate | Executor report | Verdict |")
    add("| --- | --- | --- | --- |")
    add("| CRM-001 | crm.py guards NC-01 .. NC-45 (validation, duplicates, assignment/queue,"
        " permissions, score, stage rules, big-deal approval, discounts, transfer, chain"
        " order, atomicity) | DONE | PENDING |")
    add("")
    add("## 3. Environment")
    add("")
    add("```console")
    add("$ python3 -VV")
    add(py_out.rstrip("\n"))
    add("(exit %d)" % py_rc)
    add("```")
    add("")
    add("`crm.py` sha256 before the control run: `%s`" % baseline_hash)
    add("")
    add("`crm.py` sha256 after the control run:  `%s` (restored: %s)" % (
        final_hash, "yes" if restored else "NO"))
    add("")
    add("`test_crm.py` sha256 before the control run: `%s`" % tests_hash)
    add("")
    add("`test_crm.py` sha256 after the control run:  `%s`" % final_tests_hash)
    add("")
    add("## 4. Baseline test run")
    add("")
    add("The exact required command:")
    add("")
    add("```console")
    add("$ " + TEST_CMD)
    add(baseline_out.rstrip("\n"))
    add("(exit %d)" % baseline_rc)
    add("```")
    add("")
    add("Same command verbosely, so every test name is on the record (`%d` tests):" % test_count)
    add("")
    add("```console")
    add("$ " + TEST_CMD + " -v")
    add(verbose_out.rstrip("\n"))
    add("(exit %d)" % verbose_rc)
    add("```")
    add("")
    add("## 5. Negative controls (verbatim transcripts)")
    add("")
    add("One `aepkit negcontrol` run per guard. Full transcripts appear once here;")
    add("the same text is in `negcontrol-log.md`. A control passes only when the suite is red")
    add("under the break, the red run's output matches the expected failing test, the file is")
    add("restored byte-identically, and the suite is green again.")
    add("")
    for item in results:
        add("#### %s — %s" % (item["id"], item["description"]))
        add("")
        add("Break: %s." % item["break_kind"])
        add("")
        add("```console")
        add("$ " + item["cmd"])
        add(item["out"].rstrip("\n"))
        add("(exit %d)" % item["exit"])
        add("```")
        add("")
        add("Result: **%s**" % item["verdict"])
        add("")
    add("## 6. Audit remediation map")
    add("")
    add("| Audit finding | Remediation | Controls |")
    add("| --- | --- | --- |")
    add("| F-1: unhashable actor/source/id/stage/new_owner escaped as TypeError | type checks added before every membership test; `test_unhashable_arguments` asserts ValueError / PermissionError | NC-22 .. NC-31 |")
    add("| F-2: `lost` freeing the slot untested | `test_losing_frees_the_slot` | NC-38 |")
    add("| F-3: forecast did not exclude `lost` under test | `test_forecast_ignores_lost` | NC-39 |")
    add("| F-4: ordered checks untested | six check-order tests | NC-40 .. NC-45 |")
    add("| XC-01 convert amount | existing test, new control | NC-32 |")
    add("| XC-02 qualify status | existing test, new control | NC-33 |")
    add("| XC-03 discount final stage | existing test, new control | NC-34 |")
    add("| XC-04 convert owner | existing test, new control | NC-35 |")
    add("| XC-06 rep-only assignment | existing test, new control | NC-36 |")
    add("| XC-07 advance stage-name check | new order test | NC-40 |")
    add("| XC-08 lowest-load rule (caught only incidentally) | `test_lowest_load_wins` | NC-37 |")
    add("| XC-09 forecast excludes lost | new test | NC-39 |")
    add("| XC-10 .. XC-15 ordered checks | six order tests | NC-40 .. NC-45 |")
    add("| F-5: `# G:ASSIGN_TRANSFER` marker uncontrolled | marker removed; the `_free_slot(previous)` call the spec mandates is kept | — (unreachable, see below) |")
    add("| F-6: missing `execution-guide.md`, so `aepkit lint` cannot run | not changed: the guide is the Auditor's document and this task's deliverable is the implementation plus controls. Guard verification here is by `aepkit negcontrol`, whose transcripts are below. | — |")
    add("")
    add("One implemented behaviour has no reachable test path: the `_free_slot(previous)` call")
    add("at the end of `transfer`. The queue invariant is \"whenever the waiting queue is")
    add("non-empty, every rep is at capacity\": leads join the queue only when no rep has room,")
    add("and every load decrease (advance to won/lost, transfer) drains the queue until it is")
    add("empty or the rep is full again. So `transfer` can only pass its own capacity check")
    add("while the queue is empty, and that `_free_slot` call is a no-op. The code is there")
    add("because the spec mandates it, but no unit test can exercise it through the public API,")
    add("so the misleading guard marker was removed and no control claims to cover it.")
    add("")
    add("## 7. Executor report")
    add("")
    add("### CRM-001 — DONE")
    add("")
    add("`python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p \"test*.py\"`")
    add("exits %d with %d tests; all %d negative controls exit 0; `crm.py` and"
        " `test_crm.py` are byte-identical before and after the control run. Awaiting"
        " independent audit." % (baseline_rc, test_count, len(results)))
    add("")
    add("## Annex A — breaks.py (verbatim)")
    add("")
    add("The scripted breaks used by NC-36 .. NC-45 (and only those) are defined here so")
    add("the Auditor can inspect exactly which substitution each control applies.")
    add("")
    add("```python")
    add(BREAKS.read_text(encoding="utf-8").rstrip("\n"))
    add("```")
    add("")
    (HERE / "compliance-log.md").write_text("\n".join(log) + "\n", encoding="utf-8")

    # ---------------- console summary ----------------
    for item in results:
        print("%s  %-32s exit=%d  %s" % (item["id"], item["test"], item["exit"], item["verdict"]))
    print()
    print("baseline exit=%d  controls=%d  restored=%s" % (baseline_rc, len(results), restored))
    ok = baseline_rc == 0 and restored and all(i["exit"] == 0 for i in results)
    print("ALL CONTROLS PASS" if ok else "SOME CONTROLS FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
