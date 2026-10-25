"""Unit tests for CRM.forecast (no actor, no log entry)."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crm_test_support import convert_lead, make_crm, walk_to_final  # noqa: E402


class ForecastTests(unittest.TestCase):
    def test_empty_crm_forecasts_zeroes(self):
        crm = make_crm()
        self.assertEqual(crm.forecast(), {"open": 0, "weighted": 0, "won": 0})
        self.assertEqual(crm.log, [])

    def test_weights_by_stage_and_floor_division(self):
        crm = make_crm()
        prospect = convert_lead(crm, 0, 1000)[1]      # owner r1
        proposal = convert_lead(crm, 1, 2000)[1]      # owner r2
        negotiation = convert_lead(crm, 2, 5000)[1]   # owner r3
        crm.advance(proposal, "proposal", "r2")
        crm.advance(negotiation, "proposal", "r3")
        crm.advance(negotiation, "negotiation", "r3")
        result = crm.forecast()
        self.assertEqual(result["open"], 3)
        self.assertEqual(
            result["weighted"],
            1000 * 10 // 100 + 2000 * 30 // 100 + 5000 * 60 // 100,
        )
        self.assertEqual(result["weighted"], 100 + 600 + 3000)
        self.assertEqual(result["won"], 0)

    def test_lost_contributes_nothing_and_won_is_summed(self):
        crm = make_crm()
        lost = convert_lead(crm, 0, 700)[1]
        won1 = convert_lead(crm, 1, 300)[1]
        won2 = convert_lead(crm, 2, 120)[1]
        crm.advance(lost, "lost", "r1")   # lost is one step from prospect
        # prospect -> won directly is spec-illegal (advance check 5), so the
        # two winners must walk legally: proposal -> negotiation -> won.
        walk_to_final(crm, won1, "r2")
        walk_to_final(crm, won2, "r3")
        result = crm.forecast()
        self.assertEqual(result["open"], 0)
        self.assertEqual(result["weighted"], 0)
        self.assertEqual(result["won"], 300 + 120)

    def test_weights_floor_per_opportunity(self):
        # 999 * 10 // 100 == 99 (floor of 99.9), not 100.
        crm = make_crm()
        opp_id = convert_lead(crm, 0, 999)[1]
        self.assertEqual(crm.forecast(), {"open": 1, "weighted": 99, "won": 0})

    def test_forecast_logs_nothing(self):
        crm = make_crm()
        convert_lead(crm, 0, 1000)
        log_before = list(crm.log)
        crm.forecast()
        self.assertEqual(crm.log, log_before)

    def test_discount_feeds_the_weighted_pipeline(self):
        crm = make_crm()
        opp_id = convert_lead(crm, 0, 1000)[1]
        crm.advance(opp_id, "proposal", "r1")
        crm.discount(opp_id, 10, "m1")   # 1000 -> 900
        self.assertEqual(crm.forecast(), {"open": 1, "weighted": 270, "won": 0})


if __name__ == "__main__":
    unittest.main()
