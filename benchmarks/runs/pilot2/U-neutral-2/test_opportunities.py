"""Unit tests for opportunity stages, discounts, transfers and forecast."""

import copy
import unittest

from crm import CRM


DEFAULT_REPS = [
    {"id": "r1", "role": "rep", "capacity": 2},
    {"id": "r2", "role": "rep", "capacity": 2},
    {"id": "m1", "role": "manager", "capacity": 0},
]


class BaseCase(unittest.TestCase):
    def make(self, rep_list=None):
        if rep_list is None:
            rep_list = DEFAULT_REPS
        return CRM([dict(rep) for rep in rep_list])

    def make_with_opp(self, amount=1000, rep_list=None):
        crm = self.make(rep_list)
        crm.add_lead("lead@corp.io", "Lead", "referral", "r1")
        crm.qualify("L1", "r1")
        opp_id = crm.convert("L1", amount, "r1")
        return crm, opp_id

    def assert_unchanged(self, crm, exc, fn, *args):
        before = copy.deepcopy((crm.leads, crm.opps, crm.log, crm.waiting))
        with self.assertRaises(exc):
            fn(*args)
        after = copy.deepcopy((crm.leads, crm.opps, crm.log, crm.waiting))
        self.assertEqual(before, after)


class TestAdvance(BaseCase):
    def test_full_happy_path(self):
        crm, opp = self.make_with_opp()
        crm.advance(opp, "proposal", "r1")
        crm.advance(opp, "negotiation", "r1")
        crm.advance(opp, "won", "r1")
        self.assertEqual(crm.opps[opp]["stage"], "won")
        self.assertEqual(
            [entry for entry in crm.log if entry[0] == "advance"],
            [
                ("advance", "O1", "r1"),
                ("advance", "O1", "r1"),
                ("advance", "O1", "r1"),
            ],
        )

    def test_stages_move_one_step_at_a_time(self):
        crm, opp = self.make_with_opp()
        self.assert_unchanged(crm, ValueError, crm.advance, opp, "won", "r1")
        self.assert_unchanged(
            crm, ValueError, crm.advance, opp, "prospect", "r1"
        )
        crm.advance(opp, "proposal", "r1")
        self.assert_unchanged(
            crm, ValueError, crm.advance, opp, "prospect", "r1"
        )
        self.assert_unchanged(crm, ValueError, crm.advance, opp, "won", "r1")

    def test_unknown_stage(self):
        crm, opp = self.make_with_opp()
        for bad in ("closed", "", None, "PROPOSAL"):
            with self.subTest(stage=bad):
                self.assert_unchanged(
                    crm, ValueError, crm.advance, opp, bad, "r1"
                )

    def test_lost_is_reachable_from_any_open_stage(self):
        crm, first = self.make_with_opp()
        crm.advance(first, "lost", "r1")
        self.assertEqual(crm.opps[first]["stage"], "lost")

        crm2, second = self.make_with_opp()
        crm2.advance(second, "proposal", "r1")
        crm2.advance(second, "lost", "r1")
        self.assertEqual(crm2.opps[second]["stage"], "lost")

    def test_final_stages_are_frozen(self):
        crm, opp = self.make_with_opp()
        crm.advance(opp, "lost", "r1")
        for stage in ("prospect", "proposal", "negotiation", "won", "lost"):
            with self.subTest(stage=stage):
                self.assert_unchanged(
                    crm, ValueError, crm.advance, opp, stage, "r1"
                )

    def test_owner_or_manager_may_advance(self):
        crm, opp = self.make_with_opp()
        self.assert_unchanged(
            crm, PermissionError, crm.advance, opp, "proposal", "r2"
        )
        crm.advance(opp, "proposal", "m1")
        self.assertEqual(crm.opps[opp]["stage"], "proposal")

    def test_permission_is_checked_before_the_final_stage_rule(self):
        crm, opp = self.make_with_opp()
        crm.advance(opp, "lost", "r1")
        self.assert_unchanged(
            crm, PermissionError, crm.advance, opp, "won", "r2"
        )

    def test_unknown_opportunity(self):
        crm = self.make()
        self.assertRaises(ValueError, crm.advance, "O99", "proposal", "r1")

    def test_big_negotiation_requires_a_manager(self):
        crm, opp = self.make_with_opp(amount=50001)
        crm.advance(opp, "proposal", "r1")
        self.assert_unchanged(
            crm, PermissionError, crm.advance, opp, "negotiation", "r1"
        )
        crm.advance(opp, "negotiation", "m1")
        self.assertEqual(crm.opps[opp]["stage"], "negotiation")

    def test_negotiation_at_the_limit_does_not_require_a_manager(self):
        crm, opp = self.make_with_opp(amount=50000)
        crm.advance(opp, "proposal", "r1")
        crm.advance(opp, "negotiation", "r1")
        self.assertEqual(crm.opps[opp]["stage"], "negotiation")

    def test_discounted_amount_decides_the_manager_rule(self):
        crm, opp = self.make_with_opp(amount=50010)
        crm.advance(opp, "proposal", "r1")
        crm.discount(opp, 10, "m1")  # 50010 -> 45009
        crm.advance(opp, "negotiation", "r1")
        self.assertEqual(crm.opps[opp]["stage"], "negotiation")

    def test_stage_rule_is_checked_before_the_manager_rule(self):
        crm, opp = self.make_with_opp(amount=90000)
        self.assert_unchanged(
            crm, ValueError, crm.advance, opp, "negotiation", "r1"
        )

    def test_won_frees_the_slot_and_assigns_waiting_leads(self):
        crm = self.make(
            [
                {"id": "r1", "role": "rep", "capacity": 1},
                {"id": "r2", "role": "rep", "capacity": 1},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        crm.add_lead("a@corp.io", "A", "referral", "r1")  # r1, full
        crm.add_lead("b@corp.io", "B", "referral", "r1")  # r2, full
        crm.add_lead("c@corp.io", "C", "referral", "r1")  # waits
        self.assertIsNone(crm.leads["L3"]["owner"])
        crm.qualify("L1", "r1")
        opp = crm.convert("L1", 1000, "r1")
        crm.advance(opp, "proposal", "r1")
        crm.advance(opp, "negotiation", "r1")
        self.assertIsNone(crm.leads["L3"]["owner"])
        crm.advance(opp, "won", "r1")
        self.assertEqual(crm.leads["L3"]["owner"], "r1")
        self.assertEqual(crm.waiting, [])
        self.assertEqual(crm.log[-1], ("assign", "L3", "system"))

    def test_multiple_waiting_leads_are_assigned_in_fifo_order(self):
        crm = self.make(
            [
                {"id": "r1", "role": "rep", "capacity": 2},
                {"id": "r2", "role": "rep", "capacity": 1},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        crm.add_lead("a@corp.io", "A", "referral", "r1")  # r1 load 1
        crm.add_lead("b@corp.io", "B", "referral", "r1")  # r2 load 1
        crm.add_lead("c@corp.io", "C", "referral", "r1")  # r1 load 2 == cap
        crm.add_lead("d@corp.io", "D", "referral", "r1")  # waits
        crm.add_lead("e@corp.io", "E", "referral", "r1")  # waits
        self.assertEqual(crm.waiting, ["L4", "L5"])

        crm.qualify("L1", "r1")
        opp = crm.convert("L1", 1000, "r1")
        crm.advance(opp, "lost", "r1")

        # A single freed slot admits exactly one lead: the oldest one.
        self.assertEqual(crm.leads["L4"]["owner"], "r1")
        self.assertIsNone(crm.leads["L5"]["owner"])
        self.assertEqual(crm.waiting, ["L5"])
        self.assertEqual(crm.log[-1], ("assign", "L4", "system"))

        crm.qualify("L3", "r1")
        second = crm.convert("L3", 500, "r1")
        crm.advance(second, "lost", "r1")

        self.assertEqual(crm.leads["L5"]["owner"], "r1")
        self.assertEqual(crm.waiting, [])
        self.assertEqual(crm.log[-1], ("assign", "L5", "system"))

    def test_lost_also_frees_the_slot(self):
        crm = self.make(
            [
                {"id": "r1", "role": "rep", "capacity": 1},
                {"id": "r2", "role": "rep", "capacity": 1},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        crm.add_lead("a@corp.io", "A", "referral", "r1")
        crm.add_lead("b@corp.io", "B", "referral", "r1")
        crm.add_lead("c@corp.io", "C", "referral", "r1")
        crm.qualify("L1", "r1")
        opp = crm.convert("L1", 1000, "r1")
        crm.advance(opp, "lost", "r1")
        self.assertEqual(crm.leads["L3"]["owner"], "r1")
        self.assertEqual(crm.log[-1], ("assign", "L3", "system"))


class TestDiscount(BaseCase):
    def test_owner_discounts_within_ten_percent(self):
        crm, opp = self.make_with_opp(amount=1000)
        crm.discount(opp, 10, "r1")
        self.assertEqual(crm.opps[opp]["amount"], 900)
        self.assertEqual(crm.opps[opp]["original_amount"], 1000)
        self.assertEqual(crm.log[-1], ("discount", "O1", "r1"))

    def test_pct_validation(self):
        crm, opp = self.make_with_opp(amount=1000)
        for bad in (0, 31, -1, 100, True, 10.0, "10", None):
            with self.subTest(pct=bad):
                self.assert_unchanged(
                    crm, ValueError, crm.discount, opp, bad, "r1"
                )

    def test_pct_checked_before_permission(self):
        crm, opp = self.make_with_opp(amount=1000)
        self.assert_unchanged(crm, ValueError, crm.discount, opp, 0, "r2")

    def test_owner_or_manager_may_discount(self):
        crm, opp = self.make_with_opp(amount=1000)
        self.assert_unchanged(
            crm, PermissionError, crm.discount, opp, 5, "r2"
        )
        crm.discount(opp, 5, "m1")
        self.assertEqual(crm.opps[opp]["amount"], 950)

    def test_non_manager_is_limited_to_ten(self):
        crm, opp = self.make_with_opp(amount=1000)
        self.assert_unchanged(
            crm, PermissionError, crm.discount, opp, 11, "r1"
        )
        self.assertEqual(crm.opps[opp]["amount"], 1000)

    def test_manager_may_use_up_to_thirty(self):
        crm, opp = self.make_with_opp(amount=1000)
        crm.discount(opp, 30, "m1")
        self.assertEqual(crm.opps[opp]["amount"], 700)

    def test_cumulative_discount_cannot_exceed_thirty(self):
        crm, opp = self.make_with_opp(amount=1000)
        crm.discount(opp, 30, "m1")
        self.assert_unchanged(crm, ValueError, crm.discount, opp, 1, "m1")
        self.assertEqual(crm.opps[opp]["amount"], 700)

    def test_discount_check_uses_the_floor_result(self):
        crm, opp = self.make_with_opp(amount=333)
        # 333 * 70 // 100 == 233 but 233 * 100 < 333 * 70 -> rejected
        self.assert_unchanged(crm, ValueError, crm.discount, opp, 30, "m1")

    def test_final_opportunities_cannot_be_discounted(self):
        crm, opp = self.make_with_opp(amount=1000)
        crm.advance(opp, "proposal", "r1")
        crm.advance(opp, "negotiation", "r1")
        crm.advance(opp, "won", "r1")
        self.assert_unchanged(crm, ValueError, crm.discount, opp, 5, "r1")
        self.assert_unchanged(crm, ValueError, crm.discount, opp, 11, "r1")

    def test_unknown_opportunity(self):
        crm = self.make()
        self.assertRaises(ValueError, crm.discount, "O99", 5, "r1")


class TestTransfer(BaseCase):
    def test_manager_transfers_an_opportunity(self):
        crm, opp = self.make_with_opp(amount=1000)
        crm.transfer(opp, "r2", "m1")
        self.assertEqual(crm.opps[opp]["owner"], "r2")
        self.assertEqual(crm.log[-1], ("transfer", "O1", "m1"))

    def test_only_a_manager_may_transfer(self):
        crm, opp = self.make_with_opp(amount=1000)
        self.assert_unchanged(crm, PermissionError, crm.transfer, opp, "r2", "r1")

    def test_manager_check_precedes_target_validation(self):
        crm, opp = self.make_with_opp(amount=1000)
        self.assert_unchanged(
            crm, PermissionError, crm.transfer, opp, "ghost", "r1"
        )

    def test_target_must_be_a_rep(self):
        crm, opp = self.make_with_opp(amount=1000)
        for bad in ("ghost", "m1", None, 5):
            with self.subTest(target=bad):
                self.assert_unchanged(
                    crm, ValueError, crm.transfer, opp, bad, "m1"
                )

    def test_final_opportunities_cannot_be_transferred(self):
        crm, opp = self.make_with_opp(amount=1000)
        crm.advance(opp, "lost", "r1")
        self.assert_unchanged(crm, ValueError, crm.transfer, opp, "r2", "m1")

    def test_cannot_transfer_to_the_same_owner(self):
        crm, opp = self.make_with_opp(amount=1000)
        self.assert_unchanged(crm, ValueError, crm.transfer, opp, "r1", "m1")

    def test_target_must_be_below_capacity(self):
        crm, opp = self.make_with_opp(
            amount=1000,
            rep_list=[
                {"id": "r1", "role": "rep", "capacity": 2},
                {"id": "r2", "role": "rep", "capacity": 0},
                {"id": "m1", "role": "manager", "capacity": 0},
            ],
        )
        self.assert_unchanged(crm, ValueError, crm.transfer, opp, "r2", "m1")

    def test_transfer_does_not_touch_the_previous_owner_load(self):
        crm, opp = self.make_with_opp(amount=1000)
        crm.add_lead("wait@corp.io", "Wait", "referral", "r1")
        # r1 load: O1 + L2 == 2 == capacity, r2 load 0 -> L2 went to r2
        self.assertEqual(crm.leads["L2"]["owner"], "r2")
        crm.transfer(opp, "r2", "m1")
        self.assertEqual(crm.opps[opp]["owner"], "r2")
        self.assertEqual(crm.waiting, [])

    def test_unknown_opportunity(self):
        crm = self.make()
        self.assertRaises(ValueError, crm.transfer, "O99", "r2", "m1")


class TestForecast(BaseCase):
    def test_empty_forecast(self):
        crm = self.make()
        self.assertEqual(
            crm.forecast(), {"open": 0, "weighted": 0, "won": 0}
        )

    def test_forecast_weights_each_open_stage(self):
        crm = self.make(
            [
                {"id": "r1", "role": "rep", "capacity": 20},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        amounts = [1000, 2000, 3000, 4000, 500]
        stages = [None, "proposal", "negotiation", "won", "lost"]
        opp_ids = []
        for index, amount in enumerate(amounts):
            crm.add_lead("lead%d@corp.io" % index, "L", "referral", "r1")
            lead_id = "L%d" % (index + 1)
            crm.qualify(lead_id, "r1")
            opp_ids.append(crm.convert(lead_id, amount, "r1"))

        for opp_id, stage in zip(opp_ids, stages):
            if stage == "proposal":
                crm.advance(opp_id, "proposal", "r1")
            elif stage == "negotiation":
                crm.advance(opp_id, "proposal", "r1")
                crm.advance(opp_id, "negotiation", "r1")
            elif stage == "won":
                crm.advance(opp_id, "proposal", "r1")
                crm.advance(opp_id, "negotiation", "r1")
                crm.advance(opp_id, "won", "r1")
            elif stage == "lost":
                crm.advance(opp_id, "lost", "r1")

        self.assertEqual(
            crm.forecast(), {"open": 3, "weighted": 2500, "won": 4000}
        )

    def test_forecast_uses_discounted_amounts(self):
        crm, opp = self.make_with_opp(amount=1000)
        crm.discount(opp, 10, "r1")
        self.assertEqual(
            crm.forecast(), {"open": 1, "weighted": 90, "won": 0}
        )

    def test_forecast_does_not_log(self):
        crm, opp = self.make_with_opp(amount=1000)
        before = list(crm.log)
        crm.forecast()
        self.assertEqual(crm.log, before)


if __name__ == "__main__":
    unittest.main()
