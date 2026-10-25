"""forecast(): counts, weighted pipeline and won totals."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import fixtures  # noqa: E402


class ForecastTests(unittest.TestCase):
    def setUp(self):
        self.crm = fixtures.make(("r1", "rep", 10), ("m1", "manager", 0))
        self.opps = []
        for index, amount in enumerate((1000, 2000, 3000, 5000, 700)):
            lead = self.crm.add_lead("l%d@corp.com" % index, "L%d" % index, "referral", "r1")
            self.crm.qualify(lead, "r1")
            self.opps.append(self.crm.convert(lead, amount, "r1"))

    def test_empty_pipeline(self):
        self.assertEqual(fixtures.make().forecast(), {"open": 0, "weighted": 0, "won": 0})

    def test_stage_weights_and_totals(self):
        prospect, proposal, negotiation, won, lost = self.opps
        self.crm.advance(proposal, "proposal", "r1")
        self.crm.advance(negotiation, "proposal", "r1")
        self.crm.advance(negotiation, "negotiation", "r1")
        expected = {
            "open": 5,
            "weighted": 1000 * 10 // 100 + 2000 * 30 // 100 + 3000 * 60 // 100 + 5000 * 10 // 100 + 700 * 10 // 100,
            "won": 0,
        }
        self.assertEqual(self.crm.forecast(), expected)
        for stage, actor in (("proposal", "r1"), ("negotiation", "m1"), ("won", "r1")):
            self.crm.advance(won, stage, actor)
        self.crm.advance(lost, "lost", "r1")
        expected = {
            "open": 3,
            "weighted": 1000 * 10 // 100 + 2000 * 30 // 100 + 3000 * 60 // 100,
            "won": 5000,
        }
        self.assertEqual(self.crm.forecast(), expected)

    def test_weighted_uses_current_amount_after_discount(self):
        system = fixtures.make(("r1", "rep", 5), ("m1", "manager", 0))
        lead = system.add_lead("one@corp.com", "One", "referral", "r1")
        system.qualify(lead, "r1")
        opp = system.convert(lead, 1000, "r1")
        system.discount(opp, 30, "m1")
        self.assertEqual(system.forecast(), {"open": 1, "weighted": 70, "won": 0})

    def test_forecast_does_not_log(self):
        before = list(self.crm.log)
        self.crm.forecast()
        self.assertEqual(self.crm.log, before)

    def test_lost_is_never_counted(self):
        self.crm.advance(self.opps[0], "lost", "r1")
        result = self.crm.forecast()
        self.assertEqual(result["open"], 4)
        self.assertEqual(result["won"], 0)

    def test_integer_weighted_math(self):
        lead = self.crm.add_lead("tiny@corp.com", "Tiny", "referral", "r1")
        self.crm.qualify(lead, "r1")
        opp = self.crm.convert(lead, 999, "r1")
        self.crm.advance(opp, "proposal", "r1")
        self.assertEqual(self.crm.forecast()["weighted"] % 1, 0)
        self.assertIsInstance(self.crm.forecast()["weighted"], int)


if __name__ == "__main__":
    unittest.main()
