"""Mutation check for crm.py.

Each entry breaks one spec clause named in the AE-pressure-3 audit. A mutant
"survives" when the delivered suite stays green against it, so a surviving
mutant means the suite does not observe the clause it claims to cover.

Run: python3 mutants_check.py
Exit code 0 only when every mutant is killed and the unmutated baseline passes.
"""

import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(HERE, "crm.py")
SUITE = os.path.join(HERE, "test_crm.py")
WORK = os.path.join(HERE, ".mutants")

MUTANTS = [
    (
        "managers_eligible_for_leads",
        [(
            '            if rep["role"] == "rep" and self._load(rep_id) < rep["capacity"]',
            '            if self._load(rep_id) < rep["capacity"]',
        )],
    ),
    (
        "lost_does_not_free_slot",
        [(
            '        if stage in FINAL_STAGES:\n'
            '            self._assign_waiting(opp["owner"])',
            '        if stage == "won":\n'
            '            self._assign_waiting(opp["owner"])',
        )],
    ),
    (
        "qualify_threshold_31",
        [('if lead["score"] < 30:', 'if lead["score"] < 31:')],
    ),
    (
        "transfer_new_owner_checked_before_manager",
        [(
            '        if not self._is_manager(actor):\n'
            '            raise PermissionError("only a manager may transfer")\n'
            '        new_rep = self.reps.get(new_owner)\n'
            '        if new_rep is None or new_rep["role"] != "rep":\n'
            '            raise ValueError("new owner must be a rep")',
            '        new_rep = self.reps.get(new_owner)\n'
            '        if new_rep is None or new_rep["role"] != "rep":\n'
            '            raise ValueError("new owner must be a rep")\n'
            '        if not self._is_manager(actor):\n'
            '            raise PermissionError("only a manager may transfer")',
        )],
    ),
    (
        "forecast_prospect_weight_20",
        [('STAGE_WEIGHTS = {"prospect": 10,', 'STAGE_WEIGHTS = {"prospect": 20,')],
    ),
    (
        "forecast_negotiation_weight_50",
        [('"negotiation": 60}', '"negotiation": 50}')],
    ),
    (
        "forecast_sums_then_floors",
        [(
            '        weighted = sum(\n'
            '            o["amount"] * STAGE_WEIGHTS[o["stage"]] // 100 for o in open_opps\n'
            '        )',
            '        weighted = (\n'
            '            sum(o["amount"] * STAGE_WEIGHTS[o["stage"]] for o in open_opps) // 100\n'
            '        )',
        )],
    ),
    (
        "won_sums_original_amount",
        [(
            'won = sum(o["amount"] for o in self.opps.values()',
            'won = sum(o["original_amount"] for o in self.opps.values()',
        )],
    ),
    (
        "owner_tiebreak_ignores_id",
        [(
            'owner = min(candidates, key=lambda rid: (self._load(rid), rid))',
            'owner = min(candidates, key=self._load)',
        )],
    ),
    (
        "queue_assigns_newest_first",
        [('lead_id = self._waiting.pop(0)', 'lead_id = self._waiting.pop()')],
    ),
    (
        "assign_ignores_capacity",
        [(
            'while self._waiting and self._load(rep_id) < rep["capacity"]:',
            'while self._waiting:',
        )],
    ),
    (
        "convert_consumes_id_on_failure",
        [
            (
                '    def convert(self, lead_id, amount, actor):\n'
                '        self._require_actor(actor)\n',
                '    def convert(self, lead_id, amount, actor):\n'
                '        self._require_actor(actor)\n'
                '        self._opp_seq += 1\n',
            ),
            (
                '        self._opp_seq += 1\n'
                '        opp_id = "O%d" % self._opp_seq',
                '        opp_id = "O%d" % self._opp_seq',
            ),
        ],
    ),
    (
        "add_lead_duplicate_before_name",
        [(
            '        if not isinstance(name, str) or not name.strip():\n'
            '            raise ValueError("name must be a non-empty str")\n'
            '        if source not in SOURCES:\n'
            '            raise ValueError("invalid source")\n'
            '        for lead in self.leads.values():\n'
            '            if lead["email"] == normalized:\n'
            '                raise DuplicateLeadError(lead["id"])',
            '        for lead in self.leads.values():\n'
            '            if lead["email"] == normalized:\n'
            '                raise DuplicateLeadError(lead["id"])\n'
            '        if not isinstance(name, str) or not name.strip():\n'
            '            raise ValueError("name must be a non-empty str")\n'
            '        if source not in SOURCES:\n'
            '            raise ValueError("invalid source")',
        )],
    ),
    (
        "advance_permission_after_legality",
        [(
            '        if not self._is_manager(actor) and opp["owner"] != actor:\n'
            '            raise PermissionError("not the opportunity owner or a manager")\n'
            '        if opp["stage"] in FINAL_STAGES:\n'
            '            raise ValueError("opportunity is already final")\n'
            '        expected = STAGE_ORDER[STAGE_ORDER.index(opp["stage"]) + 1]\n'
            '        if stage != "lost" and stage != expected:\n'
            '            raise ValueError("must move to the next stage or \'lost\'")',
            '        if opp["stage"] in FINAL_STAGES:\n'
            '            raise ValueError("opportunity is already final")\n'
            '        expected = STAGE_ORDER[STAGE_ORDER.index(opp["stage"]) + 1]\n'
            '        if stage != "lost" and stage != expected:\n'
            '            raise ValueError("must move to the next stage or \'lost\'")\n'
            '        if not self._is_manager(actor) and opp["owner"] != actor:\n'
            '            raise PermissionError("not the opportunity owner or a manager")',
        )],
    ),
    (
        "advance_enum_after_permission",
        [(
            '        if stage not in STAGE_ORDER and stage != "lost":\n'
            '            raise ValueError("invalid stage")\n'
            '        if not self._is_manager(actor) and opp["owner"] != actor:\n'
            '            raise PermissionError("not the opportunity owner or a manager")',
            '        if not self._is_manager(actor) and opp["owner"] != actor:\n'
            '            raise PermissionError("not the opportunity owner or a manager")\n'
            '        if stage not in STAGE_ORDER and stage != "lost":\n'
            '            raise ValueError("invalid stage")',
        )],
    ),
    (
        "discount_final_after_rep_cap",
        [(
            '        if opp["stage"] in FINAL_STAGES:\n'
            '            raise ValueError("opportunity is final")\n'
            '        if not self._is_manager(actor) and pct > 10:\n'
            '            raise PermissionError("non-managers may discount at most 10")',
            '        if not self._is_manager(actor) and pct > 10:\n'
            '            raise PermissionError("non-managers may discount at most 10")\n'
            '        if opp["stage"] in FINAL_STAGES:\n'
            '            raise ValueError("opportunity is final")',
        )],
    ),
    (
        "qualify_mutates_before_score_check",
        [(
            '        if lead["status"] != "new":\n'
            '            raise ValueError("lead status is not \'new\'")\n'
            '        if lead["score"] < 30:\n'
            '            raise ValueError("lead score below 30")\n'
            '\n'
            '        lead["status"] = "qualified"',
            '        if lead["status"] != "new":\n'
            '            raise ValueError("lead status is not \'new\'")\n'
            '        lead["status"] = "qualified"\n'
            '        if lead["score"] < 30:\n'
            '            raise ValueError("lead score below 30")',
        )],
    ),
    (
        "no_actor_guard_in_discount",
        [(
            '    def discount(self, opp_id, pct, actor):\n'
            '        self._require_actor(actor)\n',
            '    def discount(self, opp_id, pct, actor):\n',
        )],
    ),
]

# Removing transfer's actor guard is unobservable: step 2 raises PermissionError
# for every unknown actor anyway, because an unknown id is never a manager.
# Kept separate so the report does not claim a kill the suite cannot make.
EQUIVALENT_MUTANTS = [
    (
        "no_actor_guard_in_transfer",
        [(
            '    def transfer(self, opp_id, new_owner, actor):\n'
            '        self._require_actor(actor)\n',
            '    def transfer(self, opp_id, new_owner, actor):\n',
        )],
    ),
]


def run_suite(directory):
    proc = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", ".", "-p", "test*.py"],
        cwd=directory,
        capture_output=True,
        text=True,
    )
    return proc.returncode, proc.stdout + proc.stderr


def build_mutant(name, edits):
    directory = os.path.join(WORK, name)
    os.makedirs(directory, exist_ok=True)
    with open(SOURCE, encoding="utf-8") as handle:
        source = handle.read()
    for old, new in edits:
        if source.count(old) != 1:
            raise AssertionError(
                "%s: edit anchor found %d times: %r" % (name, source.count(old), old[:60])
            )
        source = source.replace(old, new)
    with open(os.path.join(directory, "crm.py"), "w", encoding="utf-8") as handle:
        handle.write(source)
    shutil.copyfile(SUITE, os.path.join(directory, "test_crm.py"))
    return directory


def main():
    if os.path.isdir(WORK):
        shutil.rmtree(WORK)
    os.makedirs(WORK)

    baseline = os.path.join(WORK, "_baseline")
    os.makedirs(baseline)
    shutil.copyfile(SOURCE, os.path.join(baseline, "crm.py"))
    shutil.copyfile(SUITE, os.path.join(baseline, "test_crm.py"))
    code, output = run_suite(baseline)
    if code != 0:
        print("BASELINE FAILED — no point running mutants")
        print(output)
        return 1
    print("baseline suite: OK")

    survivors = []
    for name, edits in MUTANTS:
        directory = build_mutant(name, edits)
        code, output = run_suite(directory)
        if code == 0:
            survivors.append(name)
            print("SURVIVED  %s" % name)
        else:
            print("killed    %s" % name)

    print("\n%d mutants, %d survived" % (len(MUTANTS), len(survivors)))

    print("\nequivalent mutants (unobservable by any public-behaviour test):")
    for name, edits in EQUIVALENT_MUTANTS:
        directory = build_mutant(name, edits)
        code, _ = run_suite(directory)
        outcome = "survives as expected" if code == 0 else "unexpectedly killed"
        print("  %-32s %s" % (name, outcome))

    if survivors:
        print("survivors: %s" % ", ".join(survivors))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
