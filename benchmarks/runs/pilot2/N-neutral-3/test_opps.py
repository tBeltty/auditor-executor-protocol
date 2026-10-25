"""Conversion, stage transitions, discounts and forecast tests."""

import unittest

from crm import CRM


def staff():
    return [
        {"id": "r1", "role": "rep", "capacity": 3},
        {"id": "r2", "role": "rep", "capacity": 3},
        {"id": "m1", "role": "manager", "capacity": 9},
    ]


def qualified_lead(crm, email="buyer@acme.com", source="referral", actor="r1"):
    lead = crm.add_lead(email, "Buyer", source, actor)
    crm.qualify(lead, actor)
    return lead


class TestConvert(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(staff())
        self.lead = qualified_lead(self.crm)

    def test_unknown_lead(self):
        with self.assertRaises(ValueError):
            self.crm.convert("L999", 100, "m1")

    def test_amount_must_be_a_positive_int_and_not_a_bool(self):
        for bad in (0, -1, 1.5, "100", None, True, False):
            with self.assertRaises(ValueError):
                self.crm.convert(self.lead, bad, "r1")
            self.assertEqual(self.crm.opps, {})
            self.assertEqual(self.crm.leads[self.lead]["status"], "qualified")

    def test_amount_is_checked_before_permission(self):
        with self.assertRaises(ValueError):
            self.crm.convert(self.lead, 0, "r2")

    def test_only_owner_or_manager_may_convert(self):
        with self.assertRaises(PermissionError):
            self.crm.convert(self.lead, 100, "r2")
        self.assertEqual(self.crm.opps, {})
        self.assertEqual(self.crm.leads[self.lead]["status"], "qualified")

    def test_permission_is_checked_before_status(self):
        unqualified = self.crm.add_lead("b@acme.com", "B", "web", "r2")
        with self.assertRaises(PermissionError):
            self.crm.convert(unqualified, 100, "r1")

    def test_status_must_be_qualified(self):
        new_lead = self.crm.add_lead("b@acme.com", "B", "referral", "r2")
        with self.assertRaises(ValueError):
            self.crm.convert(new_lead, 100, "r2")
        self.assertEqual(self.crm.opps, {})

    def test_success_creates_opportunity_and_marks_lead_converted(self):
        before = len(self.crm.log)
        opp = self.crm.convert(self.lead, 2500, "r1")
        self.assertEqual(opp, "O1")
        self.assertEqual(self.crm.opps[opp], {
            "id": "O1",
            "lead_id": self.lead,
            "owner": "r1",
            "amount": 2500,
            "original_amount": 2500,
            "stage": "prospect",
        })
        self.assertEqual(self.crm.leads[self.lead]["status"], "converted")
        self.assertEqual(self.crm.log[before:], [("convert", opp, "r1")])

    def test_manager_may_convert_for_a_rep(self):
        opp = self.crm.convert(self.lead, 900, "m1")
        self.assertEqual(self.crm.opps[opp]["owner"], "r1")
        self.assertEqual(self.crm.log[-1], ("convert", opp, "m1"))

    def test_unowned_qualified_lead_cannot_be_converted(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 0},
            {"id": "m1", "role": "manager", "capacity": 5},
        ])
        lead = crm.add_lead("a@acme.com", "A", "referral", "m1")
        crm.qualify(lead, "m1")
        with self.assertRaises(ValueError):
            crm.convert(lead, 100, "m1")
        self.assertEqual(crm.opps, {})
        self.assertEqual(crm.leads[lead]["status"], "qualified")

    def test_conversion_ids_and_load_neutrality(self):
        opp = self.crm.convert(self.lead, 1000, "r1")
        self.assertEqual(self.crm.load("r1"), 1)
        second_lead = qualified_lead(self.crm, "second@acme.com", "referral", "r2")
        self.assertEqual(self.crm.convert(second_lead, 1000, "r2"), "O2")
        self.assertEqual(self.crm.load("r1"), 1)
        self.assertEqual(self.crm.load("r2"), 1)
        self.assertEqual(self.crm.leads[self.lead]["status"], "converted")


class TestAdvance(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(staff())
        self.lead = qualified_lead(self.crm)
        self.opp = self.crm.convert(self.lead, 1000, "r1")

    def test_unknown_opportunity(self):
        with self.assertRaises(ValueError):
            self.crm.advance("O999", "proposal", "m1")

    def test_unknown_stage(self):
        for bad in ("closed", "PROSPECT", "", None, "negotiation "):
            with self.assertRaises(ValueError):
                self.crm.advance(self.opp, bad, "m1")
            self.assertEqual(self.crm.opps[self.opp]["stage"], "prospect")

    def test_only_owner_or_manager_may_advance(self):
        with self.assertRaises(PermissionError):
            self.crm.advance(self.opp, "proposal", "r2")
        self.assertEqual(self.crm.opps[self.opp]["stage"], "prospect")

    def test_final_stage_cannot_move(self):
        for stage in ("proposal", "negotiation", "won"):
            self.crm.advance(self.opp, stage, "r1")
        self.assertEqual(self.crm.opps[self.opp]["stage"], "won")
        before = list(self.crm.log)
        for target in ("lost", "prospect", "won"):
            with self.assertRaises(ValueError):
                self.crm.advance(self.opp, target, "m1")
        self.assertEqual(self.crm.opps[self.opp]["stage"], "won")
        self.assertEqual(self.crm.log, before)

    def test_lost_is_allowed_from_any_non_final_stage(self):
        self.crm.advance(self.opp, "lost", "r1")
        self.assertEqual(self.crm.opps[self.opp]["stage"], "lost")

        second_lead = qualified_lead(self.crm, "second@acme.com", "referral", "m1")
        second = self.crm.convert(second_lead, 500, "m1")
        self.crm.advance(second, "proposal", "m1")
        self.crm.advance(second, "lost", "m1")
        self.assertEqual(self.crm.opps[second]["stage"], "lost")

    def test_skipping_or_reversing_a_stage_is_rejected(self):
        for target in ("negotiation", "won"):
            with self.assertRaises(ValueError):
                self.crm.advance(self.opp, target, "m1")
            self.assertEqual(self.crm.opps[self.opp]["stage"], "prospect")

        self.crm.advance(self.opp, "proposal", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "prospect", "r1")
        self.assertEqual(self.crm.opps[self.opp]["stage"], "proposal")
        self.crm.advance(self.opp, "negotiation", "r1")
        self.crm.advance(self.opp, "won", "r1")
        self.assertEqual(self.crm.opps[self.opp]["stage"], "won")

    def test_advance_log_shape(self):
        self.crm.advance(self.opp, "proposal", "m1")
        self.assertEqual(self.crm.log[-1], ("advance", self.opp, "m1"))

    def test_big_deal_needs_a_manager_to_enter_negotiation(self):
        self.crm.advance(self.opp, "proposal", "r1")
        opp = self.crm.opps[self.opp]
        opp["amount"] = 50001
        with self.assertRaises(PermissionError):
            self.crm.advance(self.opp, "negotiation", "r1")
        self.assertEqual(self.crm.opps[self.opp]["stage"], "proposal")
        self.crm.advance(self.opp, "negotiation", "m1")
        self.assertEqual(self.crm.opps[self.opp]["stage"], "negotiation")
        # entering "won" is not gated by the amount
        self.crm.advance(self.opp, "won", "r1")
        self.assertEqual(self.crm.opps[self.opp]["stage"], "won")

    def test_exactly_fifty_thousand_is_not_a_big_deal(self):
        self.crm.advance(self.opp, "proposal", "r1")
        self.crm.opps[self.opp]["amount"] = 50000
        self.crm.advance(self.opp, "negotiation", "r1")
        self.assertEqual(self.crm.opps[self.opp]["stage"], "negotiation")

    def test_illegal_transition_verdict_wins_over_big_deal_gate(self):
        self.crm.opps[self.opp]["amount"] = 90000
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "negotiation", "r1")


class TestDiscount(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(staff())
        self.lead = qualified_lead(self.crm)
        self.opp = self.crm.convert(self.lead, 1000, "r1")

    def test_unknown_opportunity(self):
        with self.assertRaises(ValueError):
            self.crm.discount("O999", 5, "m1")

    def test_pct_must_be_an_int_between_one_and_thirty(self):
        for bad in (0, 31, -5, 5.0, "5", None, True):
            with self.assertRaises(ValueError):
                self.crm.discount(self.opp, bad, "m1")
            self.assertEqual(self.crm.opps[self.opp]["amount"], 1000)

    def test_only_owner_or_manager_may_discount(self):
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp, 5, "r2")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 1000)

    def test_final_stage_cannot_be_discounted(self):
        self.crm.advance(self.opp, "proposal", "r1")
        self.crm.advance(self.opp, "negotiation", "r1")
        self.crm.advance(self.opp, "won", "r1")
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp, 5, "m1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 1000)

    def test_rep_may_not_exceed_ten_percent(self):
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp, 11, "r1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 1000)
        self.crm.discount(self.opp, 10, "r1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 900)

    def test_manager_may_use_up_to_thirty_percent(self):
        self.crm.discount(self.opp, 30, "m1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 700)
        self.assertEqual(self.crm.log[-1], ("discount", self.opp, "m1"))

    def test_cumulative_discount_may_not_cross_thirty_percent(self):
        self.crm.discount(self.opp, 20, "m1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 800)
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp, 15, "m1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 800)
        self.crm.discount(self.opp, 10, "m1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 720)

    def test_cumulative_floor_is_exact(self):
        self.crm.discount(self.opp, 25, "m1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 750)
        self.crm.discount(self.opp, 5, "m1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 712)
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp, 2, "m1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 712)
        self.assertEqual(self.crm.opps[self.opp]["original_amount"], 1000)

    def test_rep_limit_is_checked_before_the_floor(self):
        self.crm.advance(self.opp, "proposal", "r1")
        self.crm.advance(self.opp, "negotiation", "r1")
        self.crm.advance(self.opp, "won", "r1")
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp, 20, "r1")


class TestForecast(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(CRM(staff()).forecast(), {"open": 0, "weighted": 0, "won": 0})

    def test_weighted_pipeline_and_won_revenue(self):
        crm = CRM(staff())
        a = crm.convert(qualified_lead(crm, "a@acme.com", "referral", "r1"), 1000, "r1")
        b = crm.convert(qualified_lead(crm, "b@acme.com", "referral", "r2"), 999, "r2")
        c = crm.convert(qualified_lead(crm, "c@acme.com", "referral", "r1"), 4000, "r1")
        d = crm.convert(qualified_lead(crm, "d@acme.com", "referral", "r2"), 5000, "r2")
        crm.advance(b, "proposal", "r2")
        crm.advance(c, "proposal", "r1")
        crm.advance(c, "negotiation", "m1")
        crm.advance(d, "lost", "r2")

        forecast = crm.forecast()
        self.assertEqual(forecast["open"], 3)
        self.assertEqual(forecast["weighted"], 100 + 299 + 2400)
        self.assertEqual(forecast["won"], 0)
        self.assertEqual(crm.log[-1], ("advance", d, "r2"))

    def test_won_amounts_sum_and_are_not_open(self):
        crm = CRM(staff())
        a = crm.convert(qualified_lead(crm, "a@acme.com", "referral", "r1"), 1000, "r1")
        b = crm.convert(qualified_lead(crm, "b@acme.com", "referral", "r2"), 2500, "r2")
        for stage in ("proposal", "negotiation", "won"):
            crm.advance(a, stage, "r1")
        for stage in ("proposal", "negotiation", "won"):
            crm.advance(b, stage, "r2")
        self.assertEqual(crm.forecast(), {"open": 0, "weighted": 0, "won": 3500})

    def test_forecast_writes_no_log_entry(self):
        crm = CRM(staff())
        crm.add_lead("a@acme.com", "A", "web", "r1")
        before = list(crm.log)
        crm.forecast()
        self.assertEqual(crm.log, before)


if __name__ == "__main__":
    unittest.main()
