"""Deliberate single-guard mutations of crm.py, used by negative controls.

Usage:
    python3 mutate.py <mutation-name>     # patch crm.py in place
    python3 mutate.py --check             # verify every pattern occurs once

Each mutation replaces one guard with a no-op so the corresponding test(s)
must fail.  aepkit negcontrol restores crm.py from its backup afterwards.
"""

import pathlib
import sys

MUTATIONS = {
    # email / name / source validation
    "email_format": (
        '            if normalized.count("@") != 1:',
        '            if False:',
    ),
    "name_required": (
        '            if not isinstance(name, str) or not name.strip():',
        '            if False:',
    ),
    "source_enum": (
        '            if source not in SOURCES:',
        '            if False:',
    ),
    # duplicate detection
    "duplicate_check": (
        '                if existing["email"] == normalized:',
        '                if False:',
    ),
    # rep assignment and capacity
    "assign_lowest_load": (
        '            if best is None or current < best_load:',
        '            if best is None:',
    ),
    "assign_capacity": (
        '            if current >= user["capacity"]:',
        '            if False:',
    ),
    "refill_queue": (
        '        while self.waiting and self.load(rep_id) < capacity:',
        '        while False:',
    ),
    # permission checks
    "actor_known": (
        '        if not isinstance(actor, str) or actor not in self.users:',
        '        if False:',
    ),
    "qualify_permission": (
        '            if not self._can_act_on(actor, lead["owner"]):\n'
        '                raise PermissionError("actor may not qualify this lead")',
        '            if False:\n'
        '                raise PermissionError("actor may not qualify this lead")',
    ),
    # qualification score threshold
    "qualify_score": (
        '            if lead["score"] < 30:',
        '            if False:',
    ),
    # stage-transition rules
    "stage_transition": (
        '                if index + 1 >= len(STAGES) or STAGES[index + 1] != stage:',
        '                if False:',
    ),
    "final_stage": (
        '            if current in FINAL_STAGES:\n'
        '                raise ValueError("opportunity is already final")',
        '            if False:\n'
        '                raise ValueError("opportunity is already final")',
    ),
    # big-deal approval
    "big_deal_manager": (
        '            if stage == "negotiation" and opp["amount"] > 50000 and not self._is_manager(actor):',
        '            if False:',
    ),
    # discount limits and cumulative floor
    "discount_manager_limit": (
        '            if not self._is_manager(actor) and pct > 10:',
        '            if False:',
    ),
    "discount_cumulative_floor": (
        '            if new_amount * 100 < opp["original_amount"] * 70:',
        '            if False:',
    ),
    # transfer rules
    "transfer_target": (
        '            if target is None or target["role"] != "rep":',
        '            if False:',
    ),
    "transfer_differ": (
        '            if new_owner == opp["owner"]:',
        '            if False:',
    ),
    "transfer_capacity": (
        '            if self.load(new_owner) >= target["capacity"]:',
        '            if False:',
    ),
    # atomicity rollback
    "atomic_rollback": (
        '        (self.leads, self.opps, self.log, self.waiting, self._lead_seq, self._opp_seq) = snapshot',
        '        pass',
    ),
    # --- guards identified as untested by the independent audit (F1-F5) ---
    # email must be a str
    "email_is_str": (
        '            if not isinstance(email, str):',
        '            if False:',
    ),
    # only role "rep" users receive work
    "rep_role_skip": (
        '            if user["role"] != "rep":',
        '            if False:',
    ),
    # qualify: lead must exist (checked before permission)
    "qualify_exists": (
        '            lead = self.leads.get(lead_id)\n'
        '            if lead is None:\n'
        '                raise ValueError("unknown lead: %r" % (lead_id,))\n'
        '            if not self._can_act_on(actor, lead["owner"]):',
        '            lead = self.leads.get(lead_id)\n'
        '            if False:\n'
        '                raise ValueError("unknown lead: %r" % (lead_id,))\n'
        '            if not self._can_act_on(actor, lead["owner"]):',
    ),
    # qualify: status must be "new"
    "qualify_status": (
        '            if lead["status"] != "new":',
        '            if False:',
    ),
    # convert: lead must exist
    "convert_exists": (
        '            lead = self.leads.get(lead_id)\n'
        '            if lead is None:\n'
        '                raise ValueError("unknown lead: %r" % (lead_id,))\n'
        '            if isinstance(amount, bool)',
        '            lead = self.leads.get(lead_id)\n'
        '            if False:\n'
        '                raise ValueError("unknown lead: %r" % (lead_id,))\n'
        '            if isinstance(amount, bool)',
    ),
    # convert: owner-or-manager (F1)
    "convert_permission": (
        '            if not self._can_act_on(actor, lead["owner"]):\n'
        '                raise PermissionError("actor may not convert this lead")',
        '            if False:\n'
        '                raise PermissionError("actor may not convert this lead")',
    ),
    # convert: lead status must be "qualified"
    "convert_status": (
        '            if lead["status"] != "qualified":',
        '            if False:',
    ),
    # convert: lead must have an owner
    "convert_owner": (
        '            if lead["owner"] is None:',
        '            if False:',
    ),
    # convert: amount is a positive int, not a bool
    "amount_positive": (
        '            if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:',
        '            if False:',
    ),
    # advance: opportunity must exist
    "advance_exists": (
        '            opp = self.opps.get(opp_id)\n'
        '            if opp is None:\n'
        '                raise ValueError("unknown opportunity: %r" % (opp_id,))\n'
        '            if stage not in ALL_STAGES:',
        '            opp = self.opps.get(opp_id)\n'
        '            if False:\n'
        '                raise ValueError("unknown opportunity: %r" % (opp_id,))\n'
        '            if stage not in ALL_STAGES:',
    ),
    # advance: owner-or-manager
    "advance_permission": (
        '            if not self._can_act_on(actor, opp["owner"]):\n'
        '                raise PermissionError("actor may not advance this opportunity")',
        '            if False:\n'
        '                raise PermissionError("actor may not advance this opportunity")',
    ),
    # discount: opportunity must exist
    "discount_exists": (
        '            opp = self.opps.get(opp_id)\n'
        '            if opp is None:\n'
        '                raise ValueError("unknown opportunity: %r" % (opp_id,))\n'
        '            if isinstance(pct, bool)',
        '            opp = self.opps.get(opp_id)\n'
        '            if False:\n'
        '                raise ValueError("unknown opportunity: %r" % (opp_id,))\n'
        '            if isinstance(pct, bool)',
    ),
    # discount: pct is an int in 1..30, not a bool
    "pct_bounds": (
        '            if isinstance(pct, bool) or not isinstance(pct, int) or not 1 <= pct <= 30:',
        '            if False:',
    ),
    # discount: owner-or-manager
    "discount_permission": (
        '            if not self._can_act_on(actor, opp["owner"]):\n'
        '                raise PermissionError("actor may not discount this opportunity")',
        '            if False:\n'
        '                raise PermissionError("actor may not discount this opportunity")',
    ),
    # discount: final stage rejected
    "discount_final": (
        '            if not self._can_act_on(actor, opp["owner"]):\n'
        '                raise PermissionError("actor may not discount this opportunity")\n'
        '            if opp["stage"] in FINAL_STAGES:\n'
        '                raise ValueError("opportunity is already final")',
        '            if not self._can_act_on(actor, opp["owner"]):\n'
        '                raise PermissionError("actor may not discount this opportunity")\n'
        '            if False:\n'
        '                raise ValueError("opportunity is already final")',
    ),
    # transfer: opportunity must exist
    "transfer_exists": (
        '            opp = self.opps.get(opp_id)\n'
        '            if opp is None:\n'
        '                raise ValueError("unknown opportunity: %r" % (opp_id,))\n'
        '            if not self._is_manager(actor):',
        '            opp = self.opps.get(opp_id)\n'
        '            if False:\n'
        '                raise ValueError("unknown opportunity: %r" % (opp_id,))\n'
        '            if not self._is_manager(actor):',
    ),
    # transfer: manager-only
    "transfer_manager": (
        '            if not self._is_manager(actor):',
        '            if False:',
    ),
    # transfer: final stage rejected
    "transfer_final": (
        '            if target is None or target["role"] != "rep":\n'
        '                raise ValueError("new owner must be a known rep")\n'
        '            if opp["stage"] in FINAL_STAGES:\n'
        '                raise ValueError("opportunity is already final")',
        '            if target is None or target["role"] != "rep":\n'
        '                raise ValueError("new owner must be a known rep")\n'
        '            if False:\n'
        '                raise ValueError("opportunity is already final")',
    ),
    # transfer: free the previous owner's slot (F2)
    "transfer_refill": (
        '            self._refill(previous)',
        '            pass',
    ),
    # advance to "lost" must also free the slot (F3)
    "lost_refill": (
        '            if stage in FINAL_STAGES:\n'
        '                self._refill(opp["owner"])',
        '            if stage == "won":\n'
        '                self._refill(opp["owner"])',
    ),
    # forecast: stage weights (O3)
    "forecast_weights": (
        'OPEN_WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}',
        'OPEN_WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 50}',
    ),
    # forecast: open count bookkeeping (O3)
    "forecast_open": (
        '                open_count += 1',
        '                pass',
    ),
}


def main(argv):
    path = pathlib.Path(__file__).resolve().with_name("crm.py")
    text = path.read_text()
    if argv[1:] == ["--check"]:
        bad = False
        for name, (old, _new) in sorted(MUTATIONS.items()):
            count = text.count(old)
            print("%-28s occurrences=%d" % (name, count))
            if count != 1:
                bad = True
        return 1 if bad else 0
    name = argv[1]
    old, new = MUTATIONS[name]
    count = text.count(old)
    if count != 1:
        raise SystemExit("mutation %r pattern occurs %d times, expected 1" % (name, count))
    path.write_text(text.replace(old, new, 1))
    print("applied %s" % name)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
