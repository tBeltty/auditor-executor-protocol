"""Shared fixtures for the crm.py unit tests (not collected by discovery)."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crm import DuplicateLeadError, CRM  # noqa: E402

# r1 (cap 2), r2 (cap 1), r3 (cap 3) and manager m1. Owners join in order
# r1, r2, r3, r1 when all reps start empty and full capacities leave room.
DEFAULT_USERS = [
    {"id": "r1", "role": "rep", "capacity": 2},
    {"id": "r2", "role": "rep", "capacity": 1},
    {"id": "r3", "role": "rep", "capacity": 3},
    {"id": "m1", "role": "manager", "capacity": 0},
]


def make_crm(users=None):
    """A CRM built from DEFAULT_USERS (or an explicit rep list)."""
    return CRM([dict(u) for u in (DEFAULT_USERS if users is None else users)])


def add_lead(crm, n, source="referral", actor="m1"):
    """Add a score-30 referral lead with a unique email, returning its id."""
    return crm.add_lead("bob%d@gmail.com" % n, "Bob %d" % n, source, actor)


def convert_lead(crm, n, amount=1000, actor="m1"):
    """Add + qualify + convert a lead via a manager actor (any owner).

    Returns (lead_id, opp_id); the opportunity stays owned by the lead's
    owner, not by the manager.
    """
    lead_id = add_lead(crm, n)
    crm.qualify(lead_id, actor)
    opp_id = crm.convert(lead_id, amount, actor)
    return lead_id, opp_id


def walk_to_final(crm, opp_id, actor, final="won"):
    """Move an open opportunity legally to a final stage.

    won requires proposal -> negotiation -> won; lost is one step from any
    non-final stage. Use a manager or the owner as the actor; negotiation
    below 50000 amount needs no manager.
    """
    if final == "lost":
        crm.advance(opp_id, "lost", actor)
    else:
        for stage in ("proposal", "negotiation", final):
            crm.advance(opp_id, stage, actor)
