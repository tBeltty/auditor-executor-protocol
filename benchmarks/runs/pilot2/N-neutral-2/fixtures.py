"""Shared fixtures for the crm tests (not collected: name does not match test*.py)."""

import crm


def make(*reps):
    """make(("r1", "rep", 2), ("m1", "manager", 0)) -> CRM"""
    return crm.CRM([{"id": i, "role": role, "capacity": cap} for (i, role, cap) in reps])


def team():
    return make(("r1", "rep", 2), ("r2", "rep", 2), ("m1", "manager", 0))


def solo():
    return make(("r1", "rep", 1), ("m1", "manager", 0))


def qualified_lead(system, actor="r1", email="lead@corp.com", source="referral"):
    lead_id = system.add_lead(email, "Lead", source, actor)
    system.qualify(lead_id, actor)
    return lead_id


def converted(system, amount=1000, actor="r1", email="lead@corp.com", source="referral"):
    lead_id = qualified_lead(system, actor, email, source)
    return system.convert(lead_id, amount, actor)
