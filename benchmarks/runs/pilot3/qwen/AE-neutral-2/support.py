"""Shared fixtures for the crm.py test suite (not a test module itself).

These helpers build spec-legal states through the public API only; nothing
here pokes crm.py internals.
"""

import copy

from crm import CRM

# Default roster: two reps with different capacities and one manager.
REPS = [
    {"id": "r1", "role": "rep", "capacity": 2},
    {"id": "r2", "role": "rep", "capacity": 1},
    {"id": "m1", "role": "manager", "capacity": 0},
]

_ORDER = ["proposal", "negotiation", "won"]


def make_crm(reps=None):
    return CRM(copy.deepcopy(REPS if reps is None else reps))


def add(crm, email, name="N", source="web", actor="m1"):
    return crm.add_lead(email, name, source, actor)


def qualified(crm, email="a@b.com", source="referral", actor="m1"):
    """Create a referral lead (score 30) and qualify it; return the lead id."""
    lead_id = add(crm, email, "N", source, actor)
    crm.qualify(lead_id, actor)
    return lead_id


def converted(crm, email="a@b.com", amount=1000, actor="m1"):
    """Create, qualify and convert a lead; return the opportunity id."""
    lead_id = qualified(crm, email, actor=actor)
    return crm.convert(lead_id, amount, actor)


def to_stage(crm, opp_id, stage, actor="m1"):
    """Walk an opportunity from prospect to `stage` via legal single steps."""
    assert crm.opps[opp_id]["stage"] == "prospect"
    if stage == "prospect":
        return opp_id
    if stage == "lost":
        crm.advance(opp_id, "lost", actor)
    else:
        for step in _ORDER[: _ORDER.index(stage) + 1]:
            crm.advance(opp_id, step, actor)
    return opp_id



def win(crm, opp_id, actor="m1"):
    return to_stage(crm, opp_id, "won", actor)


def lose(crm, opp_id, actor="m1"):
    return to_stage(crm, opp_id, "lost", actor)


def snapshot(crm):
    """Full observable state; any failed call must leave this byte-identical."""
    return (copy.deepcopy(crm.leads), copy.deepcopy(crm.opps), list(crm.log))
