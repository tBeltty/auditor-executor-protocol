"""Checks that each method's validations run in the order the spec lists.

The spec fixes both the exception type and the order in which conditions are
evaluated, so a call with several problems must report the *first* one.
"""

import unittest

from crm import CRM, DuplicateLeadError


def reps():
    return [
        {"id": "r1", "role": "rep", "capacity": 5},
        {"id": "r2", "role": "rep", "capacity": 5},
        {"id": "m1", "role": "manager", "capacity": 0},
    ]


def build(amount=1000, owner="r1"):
    crm = CRM(reps())
    lead_id = crm.add_lead("owner@corp.io", "Owner", "referral", owner)
    crm.qualify(lead_id, owner)
    return crm, crm.convert(lead_id, amount, owner)


class TestActorCheckedFirst(unittest.TestCase):
    def test_every_method_rejects_unknown_actor_before_anything_else(self):
        crm, opp = build()
        lead_id = crm.add_lead("second@corp.io", "S", "referral", "r1")
        calls = [
            (crm.add_lead, (1, 2, 3, "ghost")),
            (crm.qualify, ("no-such-lead", "ghost")),
            (crm.convert, ("no-such-lead", -1, "ghost")),
            (crm.advance, ("no-such-opp", "bogus", "ghost")),
            (crm.discount, ("no-such-opp", 999, "ghost")),
            (crm.transfer, ("no-such-opp", "nobody", "ghost")),
        ]
        log_before = list(crm.log)
        for method, args in calls:
            with self.assertRaises(PermissionError, msg=method.__name__):
                method(*args)
        self.assertEqual(crm.log, log_before)
        self.assertEqual(crm.leads[lead_id]["status"], "new")
        self.assertEqual(crm.opps[opp]["stage"], "prospect")

    def test_actor_must_be_a_string_id(self):
        crm = CRM(reps())
        with self.assertRaises(PermissionError):
            crm.add_lead("a@corp.io", "A", "web", 1)
        with self.assertRaises(PermissionError):
            crm.qualify("L1", None)


class TestAddLeadOrder(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(reps())
        self.first = self.crm.add_lead("dup@corp.io", "First", "web", "r1")

    def test_name_error_beats_duplicate(self):
        with self.assertRaises(ValueError) as ctx:
            self.crm.add_lead("  DUP@corp.io ", "   ", "web", "r1")
        self.assertNotIsInstance(ctx.exception, DuplicateLeadError)

    def test_email_error_beats_name_error(self):
        with self.assertRaises(ValueError) as ctx:
            self.crm.add_lead("not-an-email", "", "web", "r1")
        self.assertNotIsInstance(ctx.exception, DuplicateLeadError)

    def test_source_error_beats_duplicate(self):
        with self.assertRaises(ValueError) as ctx:
            self.crm.add_lead("dup@corp.io", "Name", "fax", "r1")
        self.assertNotIsInstance(ctx.exception, DuplicateLeadError)

    def test_duplicate_uses_normalized_email(self):
        with self.assertRaises(DuplicateLeadError) as ctx:
            self.crm.add_lead("  DuP@Corp.IO  ", "First", "event", "r1")
        self.assertEqual(ctx.exception.existing_id, self.first)
        self.assertEqual(len(self.crm.leads), 1)
        self.assertEqual(len(self.crm.log), 1)

    def test_non_string_name_and_source(self):
        with self.assertRaises(ValueError):
            self.crm.add_lead("x@corp.io", 5, "web", "r1")
        with self.assertRaises(ValueError):
            self.crm.add_lead("x@corp.io", "X", 5, "r1")
        self.assertEqual(len(self.crm.leads), 1)


class TestLeadFlowOrder(unittest.TestCase):
    def test_qualify_missing_lead_beats_permission(self):
        crm = CRM(reps())
        with self.assertRaises(ValueError):
            crm.qualify("L404", "r2")

    def test_qualify_permission_beats_status_and_score(self):
        crm = CRM(reps())
        low = crm.add_lead("low@gmail.com", "L", "web", "r1")
        self.assertEqual(crm.leads[low]["owner"], "r1")
        with self.assertRaises(PermissionError):
            crm.qualify(low, "r2")

    def test_convert_amount_beats_permission(self):
        crm = CRM(reps())
        lead_id = crm.add_lead("a@corp.io", "A", "referral", "r1")
        with self.assertRaises(ValueError):
            crm.convert(lead_id, 0, "r2")

    def test_convert_permission_beats_status(self):
        crm = CRM(reps())
        lead_id = crm.add_lead("a@corp.io", "A", "referral", "r1")
        with self.assertRaises(PermissionError):
            crm.convert(lead_id, 100, "r2")
        self.assertEqual(crm.leads[lead_id]["status"], "new")

    def test_convert_status_beats_missing_owner(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 0},
                   {"id": "m1", "role": "manager", "capacity": 0}])
        lead_id = crm.add_lead("a@corp.io", "A", "referral", "m1")
        self.assertIsNone(crm.leads[lead_id]["owner"])
        with self.assertRaises(ValueError):
            crm.convert(lead_id, 100, "m1")  # status, not owner, is the issue


class TestAdvanceAndDiscountOrder(unittest.TestCase):
    def test_illegal_transition_beats_manager_requirement(self):
        crm, opp = build(amount=90000)
        with self.assertRaises(ValueError):
            crm.advance(opp, "negotiation", "r1")  # skips proposal
        with self.assertRaises(ValueError):
            crm.advance(opp, "won", "r1")

    def test_reaching_won_requires_walking_the_order(self):
        crm, opp = build(amount=1000)
        crm.advance(opp, "proposal", "r1")
        with self.assertRaises(ValueError):
            crm.advance(opp, "won", "r1")
        crm.advance(opp, "negotiation", "r1")
        crm.advance(opp, "won", "r1")
        self.assertEqual(crm.opps[opp]["stage"], "won")

    def test_proposal_may_be_lost(self):
        crm, opp = build()
        crm.advance(opp, "proposal", "r1")
        crm.advance(opp, "lost", "r1")
        self.assertEqual(crm.opps[opp]["stage"], "lost")

    def test_discount_pct_beats_permission(self):
        crm, opp = build()
        with self.assertRaises(ValueError):
            crm.discount(opp, 0, "r2")  # bad pct, and r2 is not the owner

    def test_discount_final_stage_beats_rep_limit(self):
        crm, opp = build()
        crm.advance(opp, "lost", "r1")
        with self.assertRaises(ValueError):
            crm.discount(opp, 25, "m1")  # final stage wins over pct choice


class TestTransferOrder(unittest.TestCase):
    def test_manager_check_beats_bad_target(self):
        crm, opp = build()
        with self.assertRaises(PermissionError):
            crm.transfer(opp, "nobody", "r1")

    def test_target_check_beats_final_stage(self):
        crm, opp = build()
        crm.advance(opp, "lost", "r1")
        with self.assertRaises(ValueError):
            crm.transfer(opp, "nobody", "m1")

    def test_same_owner_beats_capacity(self):
        crm, opp = build()
        with self.assertRaises(ValueError):
            crm.transfer(opp, "r1", "m1")
        self.assertEqual(crm.opps[opp]["owner"], "r1")


class TestUnhashableAndOddIds(unittest.TestCase):
    def test_unhashable_ids_raise_value_error(self):
        crm, opp = build()
        for method_name, args in (
            ("qualify", ([], "m1")),
            ("convert", ([], 10, "m1")),
            ("advance", ([], "proposal", "m1")),
            ("discount", ([], 5, "m1")),
            ("transfer", ([], "r2", "m1")),
        ):
            with self.assertRaises(ValueError, msg=method_name):
                getattr(crm, method_name)(*args)


if __name__ == "__main__":
    unittest.main()
