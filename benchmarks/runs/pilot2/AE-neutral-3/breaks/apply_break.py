"""Remove one guard from crm.py so the negative-control harness can prove the
tests actually exercise it.  Usage: python3 apply_break.py <break-name>

Each entry replaces one exact snippet (which must occur exactly once) with a
version that no longer enforces the guard.  The harness restores crm.py from
its own backup afterwards.
"""

import pathlib
import shutil
import sys

TARGET = pathlib.Path("/tmp/aep-lab/pilot2/AE-neutral-3/crm.py")
CACHE = TARGET.parent / "__pycache__"

BREAKS = {}


def add(name, old, new):
    BREAKS[name] = (old, new)


add(
    "b01_email_validation",
    '''def email_is_valid(normalized):
    parts = normalized.split("@")
    if len(parts) != 2 or parts[0] == "":
        return False
    domain = parts[1]
    # Spec-literal: the domain must contain a "." that is neither its first
    # nor its last character.  A leading dot is allowed as long as some other
    # dot sits inside the domain (".example.com" qualifies).
    for index, char in enumerate(domain):
        if char == "." and index != 0 and index != len(domain) - 1:
            return True
    return False''',
    '''def email_is_valid(normalized):
    return True''',
)

add(
    "b02_name_validation",
    '''def name_is_valid(name):
    return isinstance(name, str) and name.strip() != ""''',
    '''def name_is_valid(name):
    return True''',
)

add(
    "b03_source_validation",
    '''def source_is_valid(source):
    return isinstance(source, str) and source in SOURCE_SCORES''',
    '''def source_is_valid(source):
    return True''',
)

add(
    "b04_duplicate_detection",
    '''        for existing in self.leads.values():
            if existing["email"] == normalized:
                raise DuplicateLeadError(existing["id"])
''',
    '''        # duplicate detection removed
''',
)

add(
    "b05_lowest_load_choice",
    '''            if best_id is None or load < best_load:''',
    '''            if best_id is None:''',
)

add(
    "b06_capacity_check",
    '''            rep = self.users[rep_id]
            if self._load(rep_id) >= rep["capacity"]:
                continue
''',
    '''            rep = self.users[rep_id]
''',
)

add(
    "b07_queue_fifo",
    '''            lead_id = self.waiting.pop(0)''',
    '''            lead_id = self.waiting.pop()''',
)

add(
    "b08_queue_drain_on_final",
    '''        if stage in FINAL_STAGES:
            self._free_slot(opp["owner"])''',
    '''        if stage in FINAL_STAGES:
            pass''',
)

add(
    "b09_permission_owner_or_manager",
    '''    def _may_manage(self, opp, actor):
        return actor == opp["owner"] or self._is_manager(actor)''',
    '''    def _may_manage(self, opp, actor):
        return True''',
)

add(
    "b10_unknown_actor",
    '''        # An actor that is not a string is not the id of a known user; the
        # spec requires PermissionError (not TypeError) for any such actor.
        if not isinstance(actor, str) or actor not in self.users:
            raise PermissionError("unknown actor: %r" % (actor,))''',
    '''        return''',
)

add(
    "b11_score_threshold",
    '''        if lead["score"] < 30:''',
    '''        if lead["score"] < 0:''',
)

add(
    "b12_stage_transition_order",
    '''        if stage != "lost":
            current_index = STAGE_ORDER.index(opp["stage"])
            if current_index + 1 >= len(STAGE_ORDER):
                raise ValueError("no stage follows %r" % (opp["stage"],))
            if stage != STAGE_ORDER[current_index + 1]:
                raise ValueError("illegal transition %r -> %r" % (opp["stage"], stage))''',
    '''        if stage != "lost":
            pass''',
)

add(
    "b13_stage_final_guard",
    '''        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is already %r" % (opp["stage"],))
        if stage != "lost":''',
    '''        if stage != "lost":''',
)

add(
    "b14_big_deal_manager",
    '''        if (
            stage == "negotiation"
            and opp["amount"] > BIG_DEAL_AMOUNT
            and not self._is_manager(actor)
        ):
            raise PermissionError("deals above 50000 need a manager to reach negotiation")
''',
    '''        # big-deal approval removed
''',
)

add(
    "b15_discount_pct_range",
    '''        if pct < 1 or pct > MAX_DISCOUNT:
            raise ValueError("pct must be between 1 and %d" % MAX_DISCOUNT)
''',
    '''        # percentage range check removed
''',
)

add(
    "b16_discount_rep_limit",
    '''        if pct > REP_DISCOUNT_LIMIT and not self._is_manager(actor):
            raise PermissionError("reps may discount at most %d percent" % REP_DISCOUNT_LIMIT)
''',
    '''        # rep discount limit removed
''',
)

add(
    "b17_discount_cumulative_floor",
    '''        if new_amount * 100 < opp["original_amount"] * (100 - MAX_DISCOUNT):
            raise ValueError("cumulative discount would exceed %d percent" % MAX_DISCOUNT)
''',
    '''        # cumulative floor removed
''',
)

add(
    "b18_transfer_rep_role",
    '''        if (
            not isinstance(new_owner, str)
            or new_owner not in self.users
            or self.users[new_owner]["role"] != "rep"
        ):
            raise ValueError("new owner must be a rep: %r" % (new_owner,))''',
    '''        if not isinstance(new_owner, str) or new_owner not in self.users:
            raise ValueError("unknown new owner: %r" % (new_owner,))''',
)

add(
    "b19_transfer_capacity",
    '''        if self._load(new_owner) >= self.users[new_owner]["capacity"]:
            raise ValueError("new owner is at capacity")
''',
    '''        # new-owner capacity check removed
''',
)

add(
    "b20_transfer_same_owner",
    '''        if new_owner == opp["owner"]:
            raise ValueError("new owner is the current owner")
''',
    '''        # same-owner check removed
''',
)

add(
    "b21_atomicity_discount",
    '''        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * (100 - MAX_DISCOUNT):
            raise ValueError("cumulative discount would exceed %d percent" % MAX_DISCOUNT)
        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))''',
    '''        new_amount = opp["amount"] * (100 - pct) // 100
        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))
        if new_amount * 100 < opp["original_amount"] * (100 - MAX_DISCOUNT):
            raise ValueError("cumulative discount would exceed %d percent" % MAX_DISCOUNT)
        # amount and log written before the floor check''',
)

add(
    "b22_atomicity_qualify",
    '''        if lead["score"] < 30:
            raise ValueError("lead score %d is below the qualification threshold" % lead["score"])
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))''',
    '''        lead["status"] = "qualified"
        if lead["score"] < 30:
            raise ValueError("lead score %d is below the qualification threshold" % lead["score"])
        self.log.append(("qualify", lead_id, actor))
        # status written before the score check''',
)

add(
    "b23_permission_qualify_actor",
    '''        if actor != lead["owner"] and not self._is_manager(actor):
            raise PermissionError("actor may not qualify this lead")''',
    '''        # qualify permission check removed''',
)

add(
    "b24_permission_convert_actor",
    '''        if actor != lead["owner"] and not self._is_manager(actor):
            raise PermissionError("actor may not convert this lead")''',
    '''        # convert permission check removed''',
)

add(
    "b25_transfer_manager_only",
    '''        if not self._is_manager(actor):
            raise PermissionError("only a manager may transfer an opportunity")''',
    '''        # manager-only transfer check removed''',
)

# ---------------------------------------------------------------------------
# Controls added in response to the audit (missing guard groups + boundary
# and atomicity guards the first matrix did not cover).
# ---------------------------------------------------------------------------

add(
    "b26_advance_valid_stage_name",
    '''        if stage not in VALID_STAGES:
            raise ValueError("invalid stage: %r" % (stage,))
''',
    '''        # named-stage check removed
''',
)

add(
    "b27_forecast_weights",
    '''        weights = {"prospect": 10, "proposal": 30, "negotiation": 60}''',
    '''        weights = {"prospect": 10, "proposal": 20, "negotiation": 30}''',
)

add(
    "b28_transfer_final_stage",
    '''        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is already %r" % (opp["stage"],))
        if new_owner == opp["owner"]:''',
    '''        if new_owner == opp["owner"]:''',
)

add(
    "b29_discount_final_stage",
    '''        if not self._may_manage(opp, actor):
            raise PermissionError("actor may not discount this opportunity")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is already %r" % (opp["stage"],))
        if pct > REP_DISCOUNT_LIMIT and not self._is_manager(actor):''',
    '''        if not self._may_manage(opp, actor):
            raise PermissionError("actor may not discount this opportunity")
        if pct > REP_DISCOUNT_LIMIT and not self._is_manager(actor):''',
)

add(
    "b30_convert_bool_amount",
    '''        if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:''',
    '''        if not isinstance(amount, int) or amount <= 0:''',
)

add(
    "b31_qualify_status_new",
    '''        if lead["status"] != "new":
            raise ValueError("lead status is %r" % (lead["status"],))
        if lead["score"] < 30:''',
    '''        if lead["score"] < 30:''',
)

add(
    "b32_score_domain_bonus",
    '''        if domain not in FREE_EMAIL_DOMAINS:
            score += SOURCE_BONUS
''',
    '''        # non-free-domain bonus removed
''',
)

add(
    "b33_load_status_filter",
    '''            if lead["owner"] == rep_id and lead["status"] in ("new", "qualified"):''',
    '''            if lead["owner"] == rep_id:''',
)

add(
    "b34_atomicity_advance",
    '''        if (
            stage == "negotiation"
            and opp["amount"] > BIG_DEAL_AMOUNT
            and not self._is_manager(actor)
        ):
            raise PermissionError("deals above 50000 need a manager to reach negotiation")
        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))''',
    '''        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if (
            stage == "negotiation"
            and opp["amount"] > BIG_DEAL_AMOUNT
            and not self._is_manager(actor)
        ):
            raise PermissionError("deals above 50000 need a manager to reach negotiation")
        # stage and log written before the big-deal check''',
)

add(
    "b35_atomicity_convert",
    '''        if lead["owner"] is None:
            raise ValueError("lead has no owner")
        self._opp_seq += 1
        opp_id = "O%d" % self._opp_seq''',
    '''        self._opp_seq += 1
        lead["status"] = "converted"
        if lead["owner"] is None:
            raise ValueError("lead has no owner")
        opp_id = "O%d" % self._opp_seq
        # id counter and lead status written before the owner check''',
)

add(
    "b36_atomicity_transfer",
    '''        if self._load(new_owner) >= self.users[new_owner]["capacity"]:
            raise ValueError("new owner is at capacity")
        previous_owner = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))''',
    '''        previous_owner = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        if self._load(new_owner) >= self.users[new_owner]["capacity"]:
            raise ValueError("new owner is at capacity")
        # owner and log written before the capacity check''',
)

add(
    "b37_atomicity_add_lead",
    '''        for existing in self.leads.values():
            if existing["email"] == normalized:
                raise DuplicateLeadError(existing["id"])
        domain = normalized.split("@")[-1]
        score = SOURCE_SCORES[source]
        if domain not in FREE_EMAIL_DOMAINS:
            score += SOURCE_BONUS
        self._lead_seq += 1
        lead_id = "L%d" % self._lead_seq''',
    '''        self._lead_seq += 1
        for existing in self.leads.values():
            if existing["email"] == normalized:
                raise DuplicateLeadError(existing["id"])
        domain = normalized.split("@")[-1]
        score = SOURCE_SCORES[source]
        if domain not in FREE_EMAIL_DOMAINS:
            score += SOURCE_BONUS
        lead_id = "L%d" % self._lead_seq
        # id counter bumped before the duplicate check''',
)

add(
    "b38_duplicate_ignores_converted_leads",
    '''        for existing in self.leads.values():
            if existing["email"] == normalized:
                raise DuplicateLeadError(existing["id"])''',
    '''        for existing in self.leads.values():
            if existing["status"] == "new" and existing["email"] == normalized:
                raise DuplicateLeadError(existing["id"])''',
)

add(
    "b39_unhashable_actor",
    '''        if not isinstance(actor, str) or actor not in self.users:''',
    '''        if actor not in self.users:''',
)

add(
    "b40_unhashable_new_owner",
    '''        if (
            not isinstance(new_owner, str)
            or new_owner not in self.users''',
    '''        if (
            new_owner not in self.users''',
)


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in BREAKS:
        sys.exit("usage: apply_break.py {%s}" % ",".join(sorted(BREAKS)))
    old, new = BREAKS[sys.argv[1]]
    src = TARGET.read_text()
    if src.count(old) != 1:
        sys.exit("anchor for %s found %d times, expected 1" % (sys.argv[1], src.count(old)))
    TARGET.write_text(src.replace(old, new))
    shutil.rmtree(CACHE, ignore_errors=True)
    print("break applied: %s" % sys.argv[1])


if __name__ == "__main__":
    main()
