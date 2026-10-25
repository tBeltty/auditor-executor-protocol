"""Transfer rules, slot freeing and ownership integrity tests."""

import unittest

from crm import CRM


def staff():
    return [
        {"id": "r1", "role": "rep", "capacity": 2},
        {"id": "r2", "role": "rep", "capacity": 2},
        {"id": "m1", "role": "manager", "capacity": 9},
    ]


def qualified_lead(crm, email, actor):
    lead = crm.add_lead(email, "Buyer", "referral", actor)
    crm.qualify(lead, actor)
    return lead


class TestTransfer(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(staff())
        self.lead = qualified_lead(self.crm, "buyer@acme.com", "r1")
        self.opp = self.crm.convert(self.lead, 1000, "r1")
        self.assertEqual(self.crm.opps[self.opp]["owner"], "r1")

    def test_unknown_opportunity(self):
        with self.assertRaises(ValueError):
            self.crm.transfer("O999", "r2", "m1")

    def test_only_a_manager_may_transfer(self):
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.opp, "r2", "r1")
        self.assertEqual(self.crm.opps[self.opp]["owner"], "r1")
        self.assertEqual(self.crm.log[-1], ("convert", self.opp, "r1"))

    def test_manager_check_precedes_target_validation(self):
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.opp, "nobody", "r1")

    def test_target_must_be_a_rep(self):
        for target in ("m1", "nobody", None, 3):
            with self.assertRaises(ValueError):
                self.crm.transfer(self.opp, target, "m1")
            self.assertEqual(self.crm.opps[self.opp]["owner"], "r1")

    def test_final_opportunity_cannot_be_transferred(self):
        for stage in ("proposal", "negotiation", "won"):
            self.crm.advance(self.opp, stage, "r1")
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "r2", "m1")
        self.assertEqual(self.crm.opps[self.opp]["owner"], "r1")

    def test_target_must_differ_from_current_owner(self):
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "r1", "m1")
        self.assertEqual(self.crm.opps[self.opp]["owner"], "r1")

    def test_target_must_have_free_capacity(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 2},
            {"id": "r2", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 9},
        ])
        first = qualified_lead(crm, "a@acme.com", "r1")
        opp = crm.convert(first, 1000, "r1")
        filler = crm.add_lead("b@acme.com", "B", "referral", "r2")
        self.assertEqual(crm.leads[filler]["owner"], "r2")
        crm.qualify(filler, "r2")
        self.assertEqual(crm.load("r2"), 1)
        before = list(crm.log)
        with self.assertRaises(ValueError):
            crm.transfer(opp, "r2", "m1")
        self.assertEqual(crm.opps[opp]["owner"], "r1")
        self.assertEqual(crm.log, before)

    def test_success_moves_owner_and_logs(self):
        before = len(self.crm.log)
        self.crm.transfer(self.opp, "r2", "m1")
        self.assertEqual(self.crm.opps[self.opp]["owner"], "r2")
        self.assertEqual(self.crm.log[before:], [("transfer", self.opp, "m1")])
        self.assertEqual(self.crm.load("r1"), 0)
        self.assertEqual(self.crm.load("r2"), 1)

    def test_transfer_releases_the_previous_owner_without_extra_log_entries(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 3},
            {"id": "m1", "role": "manager", "capacity": 9},
        ])
        first = qualified_lead(crm, "a@acme.com", "r1")
        opp = crm.convert(first, 1000, "r1")
        crm.add_lead("b@acme.com", "B", "web", "r1")
        crm.add_lead("c@acme.com", "C", "web", "r1")
        self.assertEqual(crm.waiting, [])
        before = len(crm.log)

        crm.transfer(opp, "r2", "m1")

        self.assertEqual(crm.log[before:], [("transfer", opp, "m1")])
        self.assertEqual(crm.load("r1"), 0)
        self.assertEqual(crm.load("r2"), 3)
        extra = crm.add_lead("d@acme.com", "D", "web", "r1")
        self.assertEqual(crm.leads[extra]["owner"], "r1")

    def test_transfer_is_impossible_while_leads_are_waiting(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 9},
        ])
        first = qualified_lead(crm, "a@acme.com", "r1")
        opp = crm.convert(first, 1000, "r1")
        crm.qualify(crm.add_lead("b@acme.com", "B", "referral", "r2"), "r2")
        waiting = crm.add_lead("c@acme.com", "C", "web", "m1")
        self.assertEqual(crm.waiting, [waiting])
        before = list(crm.log)
        for target in ("r1", "r2"):
            with self.assertRaises(ValueError):
                crm.transfer(opp, target, "m1")
        self.assertEqual(crm.log, before)
        self.assertEqual(crm.opps[opp]["owner"], "r1")

    def test_transfer_to_a_rep_whose_load_is_only_qualified_leads(self):
        crm = CRM(staff())
        first = qualified_lead(crm, "a@acme.com", "r1")
        opp = crm.convert(first, 500, "r1")
        extra = crm.add_lead("b@acme.com", "B", "referral", "r2")
        self.assertEqual(crm.leads[extra]["owner"], "r2")
        crm.qualify(extra, "r2")
        crm.transfer(opp, "r2", "m1")
        self.assertEqual(crm.opps[opp]["owner"], "r2")
        self.assertEqual(crm.load("r2"), 2)


class TestTransferLoadAccounting(unittest.TestCase):
    def test_incoming_opportunity_counts_towards_the_new_owners_load(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 2},
            {"id": "r2", "role": "rep", "capacity": 2},
            {"id": "m1", "role": "manager", "capacity": 9},
        ])
        first = qualified_lead(crm, "a@acme.com", "r1")
        opp = crm.convert(first, 1000, "r1")
        filler = qualified_lead(crm, "b@acme.com", "r2")
        self.assertEqual(crm.leads[filler]["owner"], "r2")
        crm.transfer(opp, "r2", "m1")
        self.assertEqual(crm.load("r2"), 2)
        self.assertEqual(crm.load("r1"), 0)
        third = crm.add_lead("c@acme.com", "C", "web", "r1")
        self.assertEqual(crm.leads[third]["owner"], "r1")


if __name__ == "__main__":
    unittest.main()
