"""Tests for CRM.forecast."""

import unittest

from support import converted, make_crm, to_stage


BIG_REPS = [
    {"id": "r", "role": "rep", "capacity": 100},
    {"id": "m", "role": "manager", "capacity": 0},
]


def opp_at(crm, email, stage, amount):
    """Build an opportunity and walk it to `stage` (manager-driven)."""
    opp = converted(crm, email, amount, actor="m")  # stage prospect
    return to_stage(crm, opp, stage, actor="m")


class TestForecast(unittest.TestCase):
    def test_empty(self):
        c = make_crm(BIG_REPS)
        self.assertEqual(c.forecast(), {"open": 0, "weighted": 0, "won": 0})

    def test_keys_are_exact(self):
        c = make_crm(BIG_REPS)
        self.assertEqual(sorted(c.forecast()), ["open", "weighted", "won"])

    def test_weights_per_stage(self):
        c = make_crm(BIG_REPS)
        opp_at(c, "1@b.com", "prospect", 1000)
        opp_at(c, "2@b.com", "proposal", 1000)
        opp_at(c, "3@b.com", "negotiation", 1000)
        self.assertEqual(c.forecast(), {"open": 3, "weighted": 100 + 300 + 600, "won": 0})

    def test_floor_division_per_opportunity(self):
        c = make_crm(BIG_REPS)
        opp_at(c, "1@b.com", "prospect", 1055)  # 105.5 -> 105
        opp_at(c, "2@b.com", "proposal", 999)   # 299.7 -> 299
        opp_at(c, "3@b.com", "negotiation", 150)  # 90 exactly
        self.assertEqual(c.forecast(), {"open": 3, "weighted": 105 + 299 + 90, "won": 0})

    def test_won_sums_amount_not_weighted(self):
        c = make_crm(BIG_REPS)
        opp_at(c, "1@b.com", "won", 4000)
        f = c.forecast()
        self.assertEqual(f["won"], 4000)
        self.assertEqual(f["open"], 0)
        self.assertEqual(f["weighted"], 0)

    def test_lost_excluded_from_every_bucket(self):
        c = make_crm(BIG_REPS)
        opp_at(c, "1@b.com", "lost", 5000)
        opp_at(c, "2@b.com", "prospect", 1000)
        self.assertEqual(c.forecast(), {"open": 1, "weighted": 100, "won": 0})

    def test_won_amount_is_the_current_amount(self):
        c = make_crm(BIG_REPS)
        opp = converted(c, "1@b.com", 10000, actor="m")
        c.discount(opp, 25, "m")  # 10000 -> 7500
        c.advance(opp, "proposal", "m")
        c.advance(opp, "negotiation", "m")
        c.advance(opp, "won", "m")
        self.assertEqual(c.forecast()["won"], 7500)

    def test_forecast_needs_no_actor_and_logs_nothing(self):
        c = make_crm(BIG_REPS)
        opp_at(c, "1@b.com", "proposal", 500)
        before = list(c.log)
        c.forecast()
        c.forecast()
        self.assertEqual(c.log, before)

    def test_several_opps_mixed_stages(self):
        c = make_crm(BIG_REPS)
        opp_at(c, "1@b.com", "prospect", 2000)
        opp_at(c, "2@b.com", "proposal", 3000)
        opp_at(c, "3@b.com", "negotiation", 4000)
        opp_at(c, "4@b.com", "won", 5000)
        opp_at(c, "5@b.com", "lost", 6000)
        expected_w = 200 + 900 + 2400
        self.assertEqual(c.forecast(), {"open": 3, "weighted": expected_w, "won": 5000})


if __name__ == "__main__":
    unittest.main()
