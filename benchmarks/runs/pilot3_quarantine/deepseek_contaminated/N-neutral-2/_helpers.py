"""Shared helpers for the CRM unit tests."""

import copy


def rep(rep_id, capacity=2, role="rep"):
    return {"id": rep_id, "role": role, "capacity": capacity}


def manager(rep_id):
    return {"id": rep_id, "role": "manager", "capacity": 0}


def snapshot(crm):
    return copy.deepcopy((crm.leads, crm.opps, crm.log, crm.waiting))


def qualify_and_convert(crm, email="lead@corp.com", name="Lead", source="referral",
                        actor="r1", amount=1000):
    lead_id = crm.add_lead(email, name, source, actor)
    crm.qualify(lead_id, actor)
    return lead_id, crm.convert(lead_id, amount, actor)
