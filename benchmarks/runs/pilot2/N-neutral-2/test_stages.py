"""Guard groups: stage-transition rules and big-deal manager approval."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import fixtures  # noqa: E402

CHAIN = ["prospect", "proposal", "negotiation", "won"]


class TransitionTests(unittest.TestCase):
    def setUp(self):
        self.crm = fixtures.make(("r1", "rep", 5), ("m1", "manager", 0))
        lead = self.crm.add_lead("a@corp.com", "A", "referral", "r1")
        self.crm.qualify(lead, "r1")
        self.opp = self.crm.convert(lead, 1000, "r1")

    def test_forward_path_is_allowed(self):
        for stage in ("proposal", "negotiation", "won"):
            self.crm.advance(self.opp, stage, "r1")
            self.assertEqual(self.crm.opps[self.opp]["stage"], stage)
        self.assertEqual(
            [entry[0] for entry in self.crm.log[-3:]],
            ["advance", "advance", "advance"],
        )

    def test_each_step_logs_the_advance(self):
        self.crm.advance(self.opp, "proposal", "r1")
        self.assertEqual(self.crm.log[-1], ("advance", self.opp, "r1"))

    def test_skip_ahead_is_rejected(self):
        for target in ("negotiation", "won"):
            with self.subTest(target=target):
                with self.assertRaises(ValueError):
                    self.crm.advance(self.opp, target, "r1")
                self.assertEqual(self.crm.opps[self.opp]["stage"], "prospect")

    def test_lost_is_reachable_from_every_open_stage(self):
        for start in ("prospect", "proposal", "negotiation"):
            with self.subTest(start=start):
                system = fixtures.make(("r1", "rep", 5), ("m1", "manager", 0))
                lead = system.add_lead("x@corp.com", "X", "referral", "r1")
                system.qualify(lead, "r1")
                opp = system.convert(lead, 1000, "r1")
                if start != "prospect":
                    system.advance(opp, "proposal", "r1")
                if start == "negotiation":
                    system.advance(opp, "negotiation", "r1")
                system.advance(opp, "lost", "r1")
                self.assertEqual(system.opps[opp]["stage"], "lost")

    def test_backwards_transition_is_rejected(self):
        self.crm.advance(self.opp, "proposal", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "prospect", "r1")
        self.assertEqual(self.crm.opps[self.opp]["stage"], "proposal")

    def test_unknown_stage_is_rejected(self):
        for bad in ("closed", "WON", "", None, 1):
            with self.subTest(stage=bad):
                with self.assertRaises(ValueError):
                    self.crm.advance(self.opp, bad, "r1")
        self.assertEqual(self.crm.opps[self.opp]["stage"], "prospect")

    def test_final_stage_cannot_move(self):
        self.crm.advance(self.opp, "proposal", "r1")
        self.crm.advance(self.opp, "negotiation", "r1")
        self.crm.advance(self.opp, "won", "r1")
        for target in ("lost", "negotiation", "won"):
            with self.subTest(target=target):
                with self.assertRaises(ValueError):
                    self.crm.advance(self.opp, target, "r1")
        self.assertEqual(self.crm.opps[self.opp]["stage"], "won")

    def test_lost_is_final_too(self):
        self.crm.advance(self.opp, "lost", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "proposal", "r1")

    def test_permission_is_checked_before_final_state(self):
        self.crm.advance(self.opp, "lost", "r1")
        with self.assertRaises(PermissionError):
            self.crm.advance(self.opp, "proposal", "r2")

    def test_invalid_transition_happens_before_big_deal_check(self):
        self.crm.opps[self.opp]["amount"] = 90000
        with self.assertRaises(ValueError):
            # prospect -> negotiation is an illegal jump; ValueError wins over
            # the manager-approval PermissionError.
            self.crm.advance(self.opp, "negotiation", "r1")

    def test_failed_transition_logs_nothing(self):
        log_before = list(self.crm.log)
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "won", "r1")
        self.assertEqual(self.crm.log, log_before)


class BigDealTests(unittest.TestCase):
    def make_deal(self, amount, reps=None):
        system = fixtures.make(*(reps or (("r1", "rep", 5), ("m1", "manager", 0))))
        lead = system.add_lead("big@corp.com", "Big", "referral", "r1")
        system.qualify(lead, "r1")
        opp = system.convert(lead, amount, "r1")
        system.advance(opp, "proposal", "r1")
        return system, opp

    def test_rep_needs_manager_above_50000(self):
        system, opp = self.make_deal(50001)
        log_before = list(system.log)
        with self.assertRaises(PermissionError):
            system.advance(opp, "negotiation", "r1")
        self.assertEqual(system.opps[opp]["stage"], "proposal")
        self.assertEqual(system.log, log_before)

    def test_rep_may_advance_at_exactly_50000(self):
        system, opp = self.make_deal(50000)
        system.advance(opp, "negotiation", "r1")
        self.assertEqual(system.opps[opp]["stage"], "negotiation")

    def test_rep_may_advance_small_deals(self):
        system, opp = self.make_deal(1200)
        system.advance(opp, "negotiation", "r1")
        self.assertEqual(system.opps[opp]["stage"], "negotiation")

    def test_manager_may_advance_big_deals(self):
        system, opp = self.make_deal(90000)
        system.advance(opp, "negotiation", "m1")
        self.assertEqual(system.opps[opp]["stage"], "negotiation")

    def test_big_deal_threshold_is_only_for_negotiation(self):
        system, opp = self.make_deal(90000)
        system.advance(opp, "negotiation", "m1")
        # the owner rep may still move the deal to won
        system.advance(opp, "won", "r1")
        self.assertEqual(system.opps[opp]["stage"], "won")

    def test_discount_can_bring_a_deal_under_the_threshold(self):
        system, opp = self.make_deal(60000)
        system.discount(opp, 20, "m1")
        self.assertEqual(system.opps[opp]["amount"], 48000)
        system.advance(opp, "negotiation", "r1")
        self.assertEqual(system.opps[opp]["stage"], "negotiation")


if __name__ == "__main__":
    unittest.main()
