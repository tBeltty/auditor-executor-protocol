"""Tests for CRM.forecast and cross-cutting rules (log shape, actor-first)."""

import copy
import unittest

from crm import CRM


def make_crm():
    return CRM([
        {"id": "r1", "role": "rep", "capacity": 3},
        {"id": "r2", "role": "rep", "capacity": 3},
        {"id": "m1", "role": "manager", "capacity": 0},
    ])


def make_opp(crm, email, owner, amount):
    lead = crm.add_lead(email, email, "referral", "m1")
    crm.qualify(lead, owner)
    return crm.convert(lead, amount, owner)


class TestForecast(unittest.TestCase):
    def test_empty_crm(self):
        self.assertEqual(make_crm().forecast(),
                         {"open": 0, "weighted": 0, "won": 0})

    def test_mixed_pipeline(self):
        crm = make_crm()
        o1 = make_opp(crm, "a@acme.io", "r1", 1000)     # stays prospect
        o2 = make_opp(crm, "b@acme.io", "r2", 500)      # -> negotiation
        o3 = make_opp(crm, "c@acme.io", "r1", 20000)    # -> lost
        o4 = make_opp(crm, "d@acme.io", "r2", 700)      # -> won
        o5 = make_opp(crm, "e@acme.io", "r1", 333)      # -> proposal
        crm.advance(o2, "proposal", "r2")
        crm.advance(o2, "negotiation", "r2")
        crm.advance(o3, "lost", "r1")
        crm.advance(o4, "proposal", "r2")
        crm.advance(o4, "negotiation", "r2")
        crm.advance(o4, "won", "r2")
        crm.advance(o5, "proposal", "r1")
        f = crm.forecast()
        expected_weighted = (1000 * 10 // 100     # prospect
                             + 500 * 60 // 100    # negotiation
                             + 333 * 30 // 100)   # proposal
        self.assertEqual(f, {"open": 3, "weighted": expected_weighted, "won": 700})

    def test_weighted_uses_floor_division_per_opportunity(self):
        crm = make_crm()
        o1 = make_opp(crm, "a@acme.io", "r1", 101)   # prospect: 101*10//100 = 10
        o2 = make_opp(crm, "b@acme.io", "r2", 101)
        f = crm.forecast()
        self.assertEqual(f["weighted"], 20)          # 10 + 10, not 20.2 floored
        self.assertEqual(f["open"], 2)

    def test_discount_reflected_in_forecast(self):
        crm = make_crm()
        opp = make_opp(crm, "a@acme.io", "r1", 1000)
        crm.discount(opp, 10, "r1")                  # 900
        f = crm.forecast()
        self.assertEqual(f["weighted"], 90)

    def test_forecast_takes_no_actor_and_logs_nothing(self):
        crm = make_crm()
        opp = make_opp(crm, "a@acme.io", "r1", 1000)
        before = list(crm.log)
        f = crm.forecast()
        self.assertEqual(crm.log, before)
        self.assertEqual(f["open"], 1)


class TestCrossCuttingRules(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        lead = self.crm.add_lead("a@acme.io", "A", "referral", "m1")
        self.crm.qualify(lead, "r1")
        self.opp = self.crm.convert(lead, 1000, "r1")

    def test_actor_checked_first_in_every_method(self):
        cases = [
            lambda: self.crm.add_lead("bad", "", "nope", "ghost"),
            lambda: self.crm.qualify("L99", "ghost"),
            lambda: self.crm.convert("L99", -1, "ghost"),
            lambda: self.crm.advance("O99", "bogus", "ghost"),
            lambda: self.crm.discount("O99", 0, "ghost"),
            lambda: self.crm.transfer("O99", "ghost", "ghost"),
        ]
        for call in cases:
            with self.assertRaises(PermissionError):
                call()

    def test_rep_actors_can_act(self):
        lead = self.crm.add_lead("b@acme.io", "B", "referral", "r1")
        owner = self.crm.leads[lead]["owner"]
        self.crm.qualify(lead, owner)
        self.crm.advance(self.opp, "proposal", "r1")
        self.crm.discount(self.opp, 10, "r1")

    def test_log_entries_are_tuples_of_three(self):
        lead = self.crm.add_lead("b@acme.io", "B", "referral", "m1")
        owner = self.crm.leads[lead]["owner"]
        self.crm.qualify(lead, owner)
        opp = self.crm.convert(lead, 100, owner)
        self.crm.advance(opp, "proposal", owner)
        self.crm.discount(opp, 10, owner)
        target = "r1" if owner == "r2" else "r2"
        self.crm.transfer(opp, target, "m1")
        for entry in self.crm.log:
            self.assertIsInstance(entry, tuple)
            self.assertEqual(len(entry), 3)
            self.assertIsInstance(entry[0], str)
            self.assertIsInstance(entry[1], str)
            self.assertIsInstance(entry[2], str)

    def test_full_lifecycle_log_order(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        lead = crm.add_lead("a@x.com", "A", "referral", "m1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 100, "r1")
        w = crm.add_lead("w@x.com", "W", "web", "m1")   # waiting
        crm.advance(opp, "proposal", "r1")
        crm.advance(opp, "negotiation", "r1")
        crm.discount(opp, 10, "r1")
        crm.advance(opp, "won", "r1")                   # frees slot -> assign
        self.assertEqual(crm.log, [
            ("add_lead", lead, "m1"),
            ("qualify", lead, "r1"),
            ("convert", opp, "r1"),
            ("add_lead", w, "m1"),
            ("advance", opp, "r1"),
            ("advance", opp, "r1"),
            ("discount", opp, "r1"),
            ("advance", opp, "r1"),
            ("assign", w, "system"),
        ])

    def test_waiting_lead_then_assignment_keeps_fields(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        lead = crm.add_lead("a@x.com", "A", "referral", "m1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 100, "r1")
        w = crm.add_lead("W@X.com ", "  W  ", "event", "m1")
        crm.advance(opp, "lost", "r1")                  # frees slot -> assign
        assigned = crm.leads[w]
        self.assertEqual(assigned["owner"], "r1")
        self.assertEqual(assigned["email"], "w@x.com")
        self.assertEqual(assigned["name"], "W")
        self.assertEqual(assigned["source"], "event")
        self.assertEqual(assigned["score"], 35)
        self.assertEqual(assigned["status"], "new")

    def test_leads_and_opps_are_dicts_keyed_by_id(self):
        self.assertIsInstance(self.crm.leads, dict)
        self.assertIsInstance(self.crm.opps, dict)
        for key in self.crm.leads:
            self.assertEqual(self.crm.leads[key]["id"], key)
        for key in self.crm.opps:
            self.assertEqual(self.crm.opps[key]["id"], key)

    def test_no_assign_log_on_failed_closing_advance(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        lead = crm.add_lead("a@x.com", "A", "referral", "m1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 100, "r1")
        crm.add_lead("w@x.com", "W", "web", "m1")  # waiting
        before = list(crm.log)
        with self.assertRaises(ValueError):
            crm.advance(opp, "negotiation", "r1")  # skip stage -> fails
        self.assertEqual(crm.log, before)


if __name__ == "__main__":
    unittest.main()
