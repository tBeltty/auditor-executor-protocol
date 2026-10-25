"""Tests for forecast() and for the general invariants of the log."""

import copy
import unittest

from crm import CRM

TEAM = [
    {"id": "r1", "role": "rep", "capacity": 5},
    {"id": "r2", "role": "rep", "capacity": 5},
    {"id": "m1", "role": "manager", "capacity": 0},
]


def build(reps=None):
    return CRM(copy.deepcopy(reps if reps is not None else TEAM))


def email(n):
    return "lead%d@acme.com" % n


def opp_at(crm, n, stage, amount=1000, actor="m1"):
    """Create a qualified lead, convert it and walk the opportunity to ``stage``."""
    lead = crm.add_lead(email(n), "N", "referral", actor)
    crm.qualify(lead, actor)
    opp = crm.convert(lead, amount, actor)
    if stage == "lost":
        crm.advance(opp, "lost", actor)
        return opp
    order = ("prospect", "proposal", "negotiation", "won")
    for step in order[1 : order.index(stage) + 1]:
        crm.advance(opp, step, actor)
    return opp


class ForecastTest(unittest.TestCase):
    def setUp(self):
        self.crm = build()

    def test_empty_book(self):
        self.assertEqual(self.crm.forecast(), {"open": 0, "weighted": 0, "won": 0})

    def test_forecast_needs_no_actor_and_logs_nothing(self):
        self.crm.add_lead(email(1), "N", "web", "r1")
        before = copy.deepcopy(self.crm.log)
        self.crm.forecast()
        self.crm.forecast()
        self.assertEqual(self.crm.log, before)

    def test_weights_per_stage(self):
        # 10% / 30% / 60% of 1000
        crm = build()
        opp_at(crm, 1, "prospect", 1000)
        self.assertEqual(crm.forecast(), {"open": 1, "weighted": 100, "won": 0})
        opp_at(crm, 2, "proposal", 1000)
        self.assertEqual(crm.forecast(), {"open": 2, "weighted": 400, "won": 0})
        opp_at(crm, 3, "negotiation", 1000)
        self.assertEqual(crm.forecast(), {"open": 3, "weighted": 1000, "won": 0})

    def test_weighted_uses_floor_division(self):
        crm = build()
        opp_at(crm, 1, "prospect", 999)  # 999*10//100 = 99
        opp_at(crm, 2, "proposal", 101)  # 101*30//100 = 30
        self.assertEqual(crm.forecast()["weighted"], 129)

    def test_lost_is_excluded_everywhere(self):
        crm = build()
        opp_at(crm, 1, "prospect", 1000)
        lost = opp_at(crm, 2, "prospect", 5000)
        crm.advance(lost, "lost", "m1")
        self.assertEqual(crm.forecast(), {"open": 1, "weighted": 100, "won": 0})

    def test_won_counts_full_amount(self):
        crm = build()
        won = opp_at(crm, 1, "negotiation", 4000)
        crm.advance(won, "won", "m1")
        self.assertEqual(crm.forecast(), {"open": 0, "weighted": 0, "won": 4000})

    def test_discount_lowers_weighted_and_won(self):
        crm = build()
        open_opp = opp_at(crm, 1, "proposal", 1000)
        crm.discount(open_opp, 10, "m1")  # 900 -> weighted 270
        won = opp_at(crm, 2, "prospect", 1000)
        crm.discount(won, 20, "m1")  # 800
        crm.advance(won, "proposal", "m1")
        crm.advance(won, "negotiation", "m1")
        crm.advance(won, "won", "m1")
        self.assertEqual(crm.forecast(), {"open": 1, "weighted": 270, "won": 800})

    def test_transfer_does_not_change_the_total(self):
        crm = build([
            {"id": "r1", "role": "rep", "capacity": 5},
            {"id": "r2", "role": "rep", "capacity": 5},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        opp = opp_at(crm, 1, "proposal", 1000)
        before = crm.forecast()
        crm.transfer(opp, "r2", "m1")
        self.assertEqual(crm.forecast(), before)

    def test_mixed_book(self):
        crm = build()
        opp_at(crm, 1, "prospect", 100)
        opp_at(crm, 2, "proposal", 200)
        opp_at(crm, 3, "negotiation", 300)
        won = opp_at(crm, 4, "prospect", 400)
        crm.advance(won, "proposal", "m1")
        crm.advance(won, "negotiation", "m1")
        crm.advance(won, "won", "m1")
        lost = opp_at(crm, 5, "prospect", 500)
        crm.advance(lost, "lost", "m1")
        self.assertEqual(
            crm.forecast(),
            {
                "open": 3,
                "weighted": 100 * 10 // 100 + 200 * 30 // 100 + 300 * 60 // 100,
                "won": 400,
            },
        )
        self.assertEqual(crm.forecast()["weighted"], 10 + 60 + 180)

    def test_returns_a_plain_dict(self):
        result = self.crm.forecast()
        self.assertIsInstance(result, dict)
        self.assertEqual(sorted(result), ["open", "weighted", "won"])
        # Mutating the result must not corrupt the CRM.
        result["open"] = 99
        self.assertEqual(self.crm.forecast()["open"], 0)


class LogShapeTest(unittest.TestCase):
    def test_log_entries_are_three_tuples(self):
        crm = build()
        lead = crm.add_lead(email(1), "N", "referral", "m1")
        crm.qualify(lead, "m1")
        opp = crm.convert(lead, 1000, "m1")
        crm.discount(opp, 5, "m1")
        crm.advance(opp, "proposal", "m1")
        crm.advance(opp, "negotiation", "m1")
        crm.transfer(opp, "r2", "m1")
        crm.advance(opp, "won", "m1")
        for entry in crm.log:
            self.assertIsInstance(entry, tuple)
            self.assertEqual(len(entry), 3)
            self.assertIsInstance(entry[0], str)
        self.assertEqual(
            crm.log,
            [
                ("add_lead", "L1", "m1"),
                ("qualify", "L1", "m1"),
                ("convert", "O1", "m1"),
                ("discount", "O1", "m1"),
                ("advance", "O1", "m1"),
                ("advance", "O1", "m1"),
                ("transfer", "O1", "m1"),
                ("advance", "O1", "m1"),
            ],
        )

    def test_attributes_exist(self):
        crm = build()
        self.assertEqual(crm.leads, {})
        self.assertEqual(crm.opps, {})
        self.assertEqual(crm.log, [])
        lead = crm.add_lead(email(1), "N", "referral", "m1")
        self.assertEqual(list(crm.leads), ["L1"])
        self.assertIn(lead, crm.leads)


if __name__ == "__main__":
    unittest.main()
