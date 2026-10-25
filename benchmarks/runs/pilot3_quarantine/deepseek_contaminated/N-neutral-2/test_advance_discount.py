"""Tests for CRM.advance and CRM.discount."""

import unittest

from _helpers import manager, qualify_and_convert, rep, snapshot
from crm import CRM


class AdvanceTests(unittest.TestCase):
    def setUp(self):
        self.crm = CRM([rep("r1", 5), rep("r2", 0), manager("m1")])
        self.lead_id, self.opp_id = qualify_and_convert(self.crm, amount=1000)

    def test_unknown_actor_checked_first(self):
        before = snapshot(self.crm)
        with self.assertRaises(PermissionError):
            self.crm.advance(self.opp_id, "bogus", "ghost")
        self.assertEqual(snapshot(self.crm), before)

    def test_unknown_opportunity(self):
        with self.assertRaises(ValueError):
            self.crm.advance("O99", "proposal", "r1")

    def test_invalid_stage_name(self):
        for bad in ("closed", "", None, 3):
            before = snapshot(self.crm)
            with self.assertRaises(ValueError):
                self.crm.advance(self.opp_id, bad, "r1")
            self.assertEqual(snapshot(self.crm), before)

    def test_stage_checked_before_permission(self):
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp_id, "nope", "r2")

    def test_non_owner_rep_cannot_advance(self):
        with self.assertRaises(PermissionError):
            self.crm.advance(self.opp_id, "proposal", "r2")

    def test_manager_can_advance(self):
        self.crm.advance(self.opp_id, "proposal", "m1")
        self.assertEqual(self.crm.opps[self.opp_id]["stage"], "proposal")

    def test_forward_path(self):
        for stage in ("proposal", "negotiation", "won"):
            self.crm.advance(self.opp_id, stage, "r1")
            self.assertEqual(self.crm.opps[self.opp_id]["stage"], stage)

    def test_cannot_skip_stages_or_go_backwards(self):
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp_id, "negotiation", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp_id, "won", "r1")
        self.crm.advance(self.opp_id, "proposal", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp_id, "prospect", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp_id, "won", "r1")

    def test_lost_is_reachable_from_any_open_stage(self):
        self.crm.advance(self.opp_id, "lost", "r1")
        self.assertEqual(self.crm.opps[self.opp_id]["stage"], "lost")

    def test_final_stages_freeze_the_opportunity(self):
        self.crm.advance(self.opp_id, "lost", "r1")
        for stage in ("prospect", "proposal", "negotiation", "won", "lost"):
            before = snapshot(self.crm)
            with self.assertRaises(ValueError):
                self.crm.advance(self.opp_id, stage, "r1")
            self.assertEqual(snapshot(self.crm), before)

    def test_large_negotiation_requires_manager(self):
        crm = CRM([rep("r1", 5), manager("m1")])
        _, big_opp = qualify_and_convert(crm, amount=50001)
        crm.advance(big_opp, "proposal", "r1")
        before = snapshot(crm)
        with self.assertRaises(PermissionError):
            crm.advance(big_opp, "negotiation", "r1")
        self.assertEqual(snapshot(crm), before)
        crm.advance(big_opp, "negotiation", "m1")
        self.assertEqual(crm.opps[big_opp]["stage"], "negotiation")

    def test_negotiation_at_exactly_50000_allowed_for_rep(self):
        crm = CRM([rep("r1", 5), manager("m1")])
        _, opp = qualify_and_convert(crm, amount=50000)
        crm.advance(opp, "proposal", "r1")
        crm.advance(opp, "negotiation", "r1")
        self.assertEqual(crm.opps[opp]["stage"], "negotiation")

    def test_success_logs(self):
        self.crm.advance(self.opp_id, "proposal", "r1")
        self.assertEqual(self.crm.log[-1], ("advance", self.opp_id, "r1"))

    def test_winning_frees_slot_and_assigns_waiting_fifo(self):
        crm = CRM([rep("r1", 1)])
        lead_a = crm.add_lead("a@corp.com", "A", "referral", "r1")
        crm.qualify(lead_a, "r1")
        opp = crm.convert(lead_a, 100, "r1")
        waiting_b = crm.add_lead("b@corp.com", "B", "referral", "r1")
        waiting_c = crm.add_lead("c@corp.com", "C", "referral", "r1")
        self.assertIsNone(crm.leads[waiting_b]["owner"])
        self.assertIsNone(crm.leads[waiting_c]["owner"])

        crm.advance(opp, "proposal", "r1")
        crm.advance(opp, "negotiation", "r1")
        crm.advance(opp, "won", "r1")

        self.assertEqual(crm.leads[waiting_b]["owner"], "r1")
        self.assertIsNone(crm.leads[waiting_c]["owner"])
        self.assertEqual(crm.waiting, [waiting_c])
        self.assertEqual(
            crm.log[-2:],
            [("advance", opp, "r1"), ("assign", waiting_b, "system")],
        )

    def test_losing_also_frees_slot(self):
        crm = CRM([rep("r1", 1)])
        lead_a = crm.add_lead("a@corp.com", "A", "referral", "r1")
        crm.qualify(lead_a, "r1")
        opp = crm.convert(lead_a, 100, "r1")
        waiting = crm.add_lead("b@corp.com", "B", "referral", "r1")
        crm.advance(opp, "lost", "r1")
        self.assertEqual(crm.leads[waiting]["owner"], "r1")
        self.assertEqual(crm.waiting, [])

    def test_winning_fills_only_available_capacity(self):
        crm = CRM([rep("r1", 1)])
        lead_a = crm.add_lead("a@corp.com", "A", "referral", "r1")
        crm.qualify(lead_a, "r1")
        opp = crm.convert(lead_a, 100, "r1")
        waiting = [
            crm.add_lead("w%d@corp.com" % i, "W", "referral", "r1")
            for i in range(3)
        ]
        crm.advance(opp, "proposal", "r1")
        crm.advance(opp, "negotiation", "r1")
        crm.advance(opp, "won", "r1")
        self.assertEqual(crm.leads[waiting[0]]["owner"], "r1")
        self.assertIsNone(crm.leads[waiting[1]]["owner"])
        self.assertEqual(crm.waiting, waiting[1:])


class DiscountTests(unittest.TestCase):
    def setUp(self):
        self.crm = CRM([rep("r1", 5), rep("r2", 0), manager("m1")])
        self.lead_id, self.opp_id = qualify_and_convert(self.crm, amount=1000)

    def test_unknown_actor_checked_first(self):
        before = snapshot(self.crm)
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp_id, 999, "ghost")
        self.assertEqual(snapshot(self.crm), before)

    def test_unknown_opportunity(self):
        with self.assertRaises(ValueError):
            self.crm.discount("O99", 5, "r1")

    def test_pct_validation(self):
        for bad in (0, 31, -1, True, False, 5.0, "5", None):
            before = snapshot(self.crm)
            with self.assertRaises(ValueError):
                self.crm.discount(self.opp_id, bad, "r1")
            self.assertEqual(snapshot(self.crm), before)

    def test_pct_checked_before_permission(self):
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp_id, 31, "r2")

    def test_non_owner_cannot_discount(self):
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp_id, 5, "r2")

    def test_final_stage_cannot_be_discounted(self):
        self.crm.advance(self.opp_id, "lost", "r1")
        before = snapshot(self.crm)
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp_id, 5, "r1")
        self.assertEqual(snapshot(self.crm), before)

    def test_rep_limit_is_ten(self):
        self.crm.discount(self.opp_id, 10, "r1")
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 900)
        before = snapshot(self.crm)
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp_id, 11, "r1")
        self.assertEqual(snapshot(self.crm), before)

    def test_manager_may_go_up_to_thirty(self):
        self.crm.discount(self.opp_id, 30, "m1")
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 700)

    def test_cumulative_limit_uses_original_amount(self):
        self.crm.discount(self.opp_id, 10, "r1")   # 900
        self.crm.discount(self.opp_id, 20, "m1")   # 720, 28% total
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 720)
        before = snapshot(self.crm)
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp_id, 10, "m1")  # would be 648 (35.2%)
        self.assertEqual(snapshot(self.crm), before)

    def test_exact_thirty_percent_total_is_allowed(self):
        crm = CRM([rep("r1", 5), manager("m1")])
        _, opp = qualify_and_convert(crm, amount=100)
        crm.discount(opp, 10, "r1")   # 90
        crm.discount(opp, 22, "m1")   # 70, exactly 30% below original
        self.assertEqual(crm.opps[opp]["amount"], 70)

    def test_floor_division_new_amount(self):
        crm = CRM([rep("r1", 5)])
        _, opp = qualify_and_convert(crm, amount=101)
        crm.discount(opp, 10, "r1")  # 101 * 90 // 100 == 90
        self.assertEqual(crm.opps[opp]["amount"], 90)

    def test_success_logs(self):
        self.crm.discount(self.opp_id, 5, "r1")
        self.assertEqual(self.crm.log[-1], ("discount", self.opp_id, "r1"))


if __name__ == "__main__":
    unittest.main()
