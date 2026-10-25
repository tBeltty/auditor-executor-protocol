"""Unit tests for forecasting, the audit log and failure atomicity."""

import copy
import unittest

from crm import CRM, DuplicateLeadError


def make_crm(reps=None):
    if reps is None:
        reps = [
            {"id": "r1", "role": "rep", "capacity": 2},
            {"id": "r2", "role": "rep", "capacity": 2},
            {"id": "m1", "role": "manager", "capacity": 10},
        ]
    return CRM(reps)


def new_deal(crm, amount, email):
    lead_id = crm.add_lead(email, "Deal", "referral", "m1")
    crm.qualify(lead_id, "m1")
    return crm.convert(lead_id, amount, "m1")


def force_stage(crm, opp_id, stage, actor="m1"):
    order = ["prospect", "proposal", "negotiation", "won"]
    while crm.opps[opp_id]["stage"] != stage:
        current = order.index(crm.opps[opp_id]["stage"])
        crm.advance(opp_id, order[current + 1], actor)


class ForecastTests(unittest.TestCase):
    def test_empty_forecast(self):
        self.assertEqual(make_crm().forecast(), {"open": 0, "weighted": 0, "won": 0})

    def test_mixed_pipeline(self):
        crm = make_crm(
            [
                {"id": "r1", "role": "rep", "capacity": 10},
                {"id": "r2", "role": "rep", "capacity": 10},
                {"id": "m1", "role": "manager", "capacity": 10},
            ]
        )
        new_deal(crm, 10000, "a@corp.com")
        proposal = new_deal(crm, 20000, "b@corp.com")
        crm.advance(proposal, "proposal", "m1")
        negotiation = new_deal(crm, 30000, "c@corp.com")
        crm.advance(negotiation, "proposal", "m1")
        crm.advance(negotiation, "negotiation", "m1")
        won = new_deal(crm, 40000, "d@corp.com")
        crm.advance(won, "proposal", "m1")
        crm.advance(won, "negotiation", "m1")
        crm.advance(won, "won", "m1")
        lost = new_deal(crm, 50000, "e@corp.com")
        crm.advance(lost, "lost", "m1")
        self.assertEqual(
            crm.forecast(),
            {"open": 3, "weighted": 1000 + 6000 + 18000, "won": 40000},
        )

    def test_weights_use_floor_division_per_opportunity(self):
        crm = make_crm()
        opp_id = new_deal(crm, 999, "a@corp.com")
        self.assertEqual(crm.forecast(), {"open": 1, "weighted": 99, "won": 0})
        crm.advance(opp_id, "proposal", "m1")
        self.assertEqual(crm.forecast(), {"open": 1, "weighted": 299, "won": 0})
        crm.advance(opp_id, "negotiation", "m1")
        self.assertEqual(crm.forecast(), {"open": 1, "weighted": 599, "won": 0})
        crm.advance(opp_id, "won", "m1")
        self.assertEqual(crm.forecast(), {"open": 0, "weighted": 0, "won": 999})

    def test_lost_is_excluded_everywhere(self):
        crm = make_crm()
        opp_id = new_deal(crm, 7000, "a@corp.com")
        crm.advance(opp_id, "lost", "m1")
        self.assertEqual(crm.forecast(), {"open": 0, "weighted": 0, "won": 0})

    def test_forecast_uses_current_discounted_amount(self):
        crm = make_crm()
        opp_id = new_deal(crm, 1000, "a@corp.com")
        crm.discount(opp_id, 10, "m1")
        self.assertEqual(crm.forecast(), {"open": 1, "weighted": 90, "won": 0})
        crm.advance(opp_id, "proposal", "m1")
        self.assertEqual(crm.forecast(), {"open": 1, "weighted": 270, "won": 0})
        crm.advance(opp_id, "negotiation", "m1")
        self.assertEqual(crm.forecast(), {"open": 1, "weighted": 540, "won": 0})
        crm.advance(opp_id, "won", "m1")
        self.assertEqual(crm.forecast(), {"open": 0, "weighted": 0, "won": 900})

    def test_forecast_needs_no_actor_and_logs_nothing(self):
        crm = make_crm()
        new_deal(crm, 12000, "a@corp.com")
        before = copy.deepcopy((crm.leads, crm.opps, crm.log))
        first = crm.forecast()
        second = crm.forecast()
        self.assertEqual(first, second)
        self.assertEqual(copy.deepcopy((crm.leads, crm.opps, crm.log)), before)


class LogTests(unittest.TestCase):
    def test_entries_are_three_tuples(self):
        crm = make_crm()
        new_deal(crm, 1000, "a@corp.com")
        self.assertTrue(crm.log)
        for entry in crm.log:
            self.assertIsInstance(entry, tuple)
            self.assertEqual(len(entry), 3)

    def test_full_pipeline_logs_exactly_the_named_entries(self):
        crm = make_crm(
            [
                {"id": "r1", "role": "rep", "capacity": 1},
                {"id": "r2", "role": "rep", "capacity": 1},
                {"id": "m1", "role": "manager", "capacity": 5},
            ]
        )
        l1 = crm.add_lead("a@corp.com", "A", "referral", "m1")
        crm.add_lead("b@corp.com", "B", "referral", "m1")
        l3 = crm.add_lead("c@corp.com", "C", "referral", "m1")
        crm.qualify(l1, "r1")
        opp_id = crm.convert(l1, 2000, "m1")
        crm.discount(opp_id, 10, "r1")
        crm.advance(opp_id, "proposal", "r1")
        crm.advance(opp_id, "negotiation", "m1")
        crm.advance(opp_id, "won", "r1")
        crm.add_lead("d@corp.com", "D", "referral", "m1")
        self.assertEqual(
            crm.log,
            [
                ("add_lead", "L1", "m1"),
                ("add_lead", "L2", "m1"),
                ("add_lead", "L3", "m1"),
                ("qualify", "L1", "r1"),
                ("convert", "O1", "m1"),
                ("discount", "O1", "r1"),
                ("advance", "O1", "r1"),
                ("advance", "O1", "m1"),
                ("advance", "O1", "r1"),
                ("assign", l3, "system"),
                ("add_lead", "L4", "m1"),
            ],
        )
        self.assertEqual(crm.leads[l3]["owner"], "r1")
        self.assertEqual(crm.forecast(), {"open": 0, "weighted": 0, "won": 1800})


class AtomicityTests(unittest.TestCase):
    def test_failed_calls_change_nothing(self):
        crm = make_crm()
        lead_id = crm.add_lead("a@corp.com", "A", "referral", "r1")
        crm.qualify(lead_id, "m1")
        opp_id = crm.convert(lead_id, 1000, "m1")
        before = copy.deepcopy((crm.leads, crm.opps, crm.log))

        failures = [
            (DuplicateLeadError,
             lambda: crm.add_lead(" A@corp.COM ", "Dup", "web", "m1")),
            (ValueError, lambda: crm.add_lead("bad", "B", "web", "r1")),
            (ValueError, lambda: crm.add_lead("b@corp.com", " ", "web", "r1")),
            (ValueError, lambda: crm.add_lead("b@corp.com", "B", "social", "r1")),
            (PermissionError,
             lambda: crm.add_lead("b@corp.com", "B", "web", "ghost")),
            (ValueError, lambda: crm.qualify("L99", "m1")),
            (PermissionError, lambda: crm.qualify(lead_id, "r2")),
            (ValueError, lambda: crm.convert(lead_id, 1000, "m1")),
            (ValueError, lambda: crm.convert(lead_id, 0, "m1")),
            (ValueError, lambda: crm.advance(opp_id, "won", "m1")),
            (PermissionError, lambda: crm.advance(opp_id, "proposal", "r2")),
            (ValueError, lambda: crm.discount(opp_id, 31, "m1")),
            (PermissionError, lambda: crm.discount(opp_id, 5, "r2")),
            (ValueError, lambda: crm.transfer(opp_id, "r1", "m1")),
            (PermissionError, lambda: crm.transfer(opp_id, "r2", "r1")),
        ]
        for expected, call in failures:
            with self.subTest(expected=expected):
                with self.assertRaises(expected):
                    call()
                self.assertEqual(copy.deepcopy((crm.leads, crm.opps, crm.log)),
                                 before)


if __name__ == "__main__":
    unittest.main()
