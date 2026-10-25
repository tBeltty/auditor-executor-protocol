"""Shared in-memory fixtures for the CRM unit tests."""

import copy

from crm import CRM


def wide_crm():
    """Two reps with room to spare plus a manager."""
    return CRM(
        [
            {"id": "r1", "role": "rep", "capacity": 5},
            {"id": "r2", "role": "rep", "capacity": 5},
            {"id": "m1", "role": "manager", "capacity": 0},
        ]
    )


def add(crm, email="lead@corp.com", name="Lead", source="referral", actor="r1"):
    return crm.add_lead(email, name, source, actor)


def make_opp(crm, amount=1000, email="lead@corp.com", actor="m1"):
    """Create a qualified lead and convert it; returns (opp_id, lead_id)."""
    lead_id = crm.add_lead(email, "Lead", "referral", actor)
    crm.qualify(lead_id, actor)
    opp_id = crm.convert(lead_id, amount, actor)
    return opp_id, lead_id


def snapshot(crm):
    """Deep copy of every piece of state a failed call must leave untouched."""
    return copy.deepcopy(
        {
            "leads": crm.leads,
            "opps": crm.opps,
            "log": crm.log,
        }
    )
