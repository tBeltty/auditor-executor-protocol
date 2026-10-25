#!/usr/bin/env python3
"""Named, surgical breaks used by the crm.py negative controls.

Each break is a textual substitution that removes exactly one protection and
leaves the rest of the module intact, so the suite still exercises every valid
path.  Usage:

    python3 breaks.py <name>

The script exits non-zero if the anchor it expects is missing or not unique.
Every anchor carries the ``# G:<NAME>`` marker (or, for the ordering breaks, a
two/three-line block whose order is the guard) so a reviewer can see exactly
what was disabled.
"""

import pathlib
import sys

CRM = pathlib.Path(__file__).resolve().with_name("crm.py")


def replace(old, new):
    text = CRM.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit("anchor found %d times, expected 1: %r" % (count, old))
    CRM.write_text(text.replace(old, new, 1), encoding="utf-8")


def swap(first, second):
    text = CRM.read_text(encoding="utf-8")
    count = text.count(first)
    if count != 1:
        raise SystemExit("swap anchor found %d times, expected 1: %r" % (count, first))
    CRM.write_text(text.replace(first, second, 1), encoding="utf-8")


BREAKS = {}


def brk(name):
    def register(fn):
        BREAKS[name] = fn
        return fn
    return register


@brk("rep_only")
def _rep_only():
    replace('if self.users[user_id]["role"] == "rep"  # G:REP_ONLY',
            'if True  # G:REP_ONLY')


@brk("lowest_load")
def _lowest_load():
    replace("return min(available, key=lambda user_id: (self._load(user_id), user_id))  # G:LOWEST_LOAD",
            "return available[0]  # G:LOWEST_LOAD")


@brk("lost_not_final")
def _lost_not_final():
    replace('if stage in FINAL_STAGES: self._free_slot(opp["owner"])  # G:ASSIGN_ADV',
            'if stage == "won": self._free_slot(opp["owner"])  # G:ASSIGN_ADV')


@brk("forecast_lost")
def _forecast_lost():
    replace('open_opps = [opp for opp in self.opps.values() if opp["stage"] not in FINAL_STAGES]  # G:FORECAST_OPEN',
            'open_opps = [opp for opp in self.opps.values() if opp["stage"] != "won"]  # G:FORECAST_OPEN')


@brk("swap_advance_order")
def _swap_advance_order():
    swap('        if stage not in ALL_STAGES: raise ValueError("invalid stage %r" % (stage,))  # G:STAGE_VALID\n'
         '        self._require_owner_or_manager(actor, opp["owner"])\n',
         '        self._require_owner_or_manager(actor, opp["owner"])\n'
         '        if stage not in ALL_STAGES: raise ValueError("invalid stage %r" % (stage,))  # G:STAGE_VALID\n')


@brk("swap_qualify_order")
def _swap_qualify_order():
    swap('        self._require_owner_or_manager(actor, lead["owner"])\n'
         '        if lead["status"] != "new": raise ValueError("lead %s is not new" % lead_id)  # G:QUALIFY_STATUS\n',
         '        if lead["status"] != "new": raise ValueError("lead %s is not new" % lead_id)  # G:QUALIFY_STATUS\n'
         '        self._require_owner_or_manager(actor, lead["owner"])\n')


@brk("swap_convert_order")
def _swap_convert_order():
    swap('        if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0: raise ValueError("amount must be a positive int")  # G:CONVERT_AMOUNT\n'
         '        self._require_owner_or_manager(actor, lead["owner"])\n',
         '        self._require_owner_or_manager(actor, lead["owner"])\n'
         '        if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0: raise ValueError("amount must be a positive int")  # G:CONVERT_AMOUNT\n')


@brk("swap_discount_order")
def _swap_discount_order():
    swap('        if not isinstance(pct, int) or isinstance(pct, bool) or not (1 <= pct <= 30): raise ValueError("invalid pct %r" % (pct,))  # G:PCT_RANGE\n'
         '        # ATOMIC-ANCHOR\n'
         '        self._require_owner_or_manager(actor, opp["owner"])\n',
         '        self._require_owner_or_manager(actor, opp["owner"])\n'
         '        if not isinstance(pct, int) or isinstance(pct, bool) or not (1 <= pct <= 30): raise ValueError("invalid pct %r" % (pct,))  # G:PCT_RANGE\n'
         '        # ATOMIC-ANCHOR\n')


@brk("swap_transfer_order")
def _swap_transfer_order():
    swap('        if self.users[actor]["role"] != "manager": raise PermissionError("only a manager may transfer")  # G:XFER_MANAGER\n'
         '        if not isinstance(new_owner, str): raise ValueError("target %r is not a rep" % (new_owner,))  # G:XFER_TYPE\n'
         '        target = self.users.get(new_owner)\n'
         '        if target is None or target["role"] != "rep": raise ValueError("target %r is not a rep" % (new_owner,))  # G:XFER_REP\n',
         '        if not isinstance(new_owner, str): raise ValueError("target %r is not a rep" % (new_owner,))  # G:XFER_TYPE\n'
         '        target = self.users.get(new_owner)\n'
         '        if target is None or target["role"] != "rep": raise ValueError("target %r is not a rep" % (new_owner,))  # G:XFER_REP\n'
         '        if self.users[actor]["role"] != "manager": raise PermissionError("only a manager may transfer")  # G:XFER_MANAGER\n')


@brk("swap_add_lead_order")
def _swap_add_lead_order():
    swap('        if source not in SOURCE_SCORES: raise ValueError("invalid source %r" % (source,))  # G:SOURCE\n'
         '        existing = self._email_index.get(normalized)\n'
         '        if existing is not None: raise DuplicateLeadError(existing)  # G:DUPLICATE\n',
         '        existing = self._email_index.get(normalized)\n'
         '        if existing is not None: raise DuplicateLeadError(existing)  # G:DUPLICATE\n'
         '        if source not in SOURCE_SCORES: raise ValueError("invalid source %r" % (source,))  # G:SOURCE\n')


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in BREAKS:
        raise SystemExit("usage: python3 breaks.py <%s>" % "|".join(sorted(BREAKS)))
    BREAKS[sys.argv[1]]()
