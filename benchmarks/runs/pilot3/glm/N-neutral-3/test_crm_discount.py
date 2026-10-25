"""Tests for CRM.discount: bounds, permissions, cumulative cap, finality."""

import copy
import unittest

from crm import CRM


def make_crm():
    return CRM([
        {"id": "r1", "role": "rep", "capacity": 2},
        {"id": "r2", "role": "rep", "capacity": 2},
        {"id": "m1", "role": "manager", "capacity": 0},
    ])


def make_opp(crm, email, owner, amount):
    lead = crm.add_lead(email, email, "referral", "m1")
    crm.qualify(lead, owner)
    return crm.convert(lead, amount, owner)


class TestDiscount(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        self.opp = make_opp(self.crm, "h@acme.io", "r1", 1000)
        self.base_log_len = len(self.crm.log)

    def test_basic_discount_by_owner(self):
        self.crm.discount(self.opp, 10, "r1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 900)
        self.assertEqual(self.crm.opps[self.opp]["original_amount"], 1000)
        self.assertEqual(self.crm.log[-1], ("discount", self.opp, "r1"))

    def test_discount_by_manager(self):
        self.crm.discount(self.opp, 10, "m1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 900)

    def test_missing_opp(self):
        with self.assertRaises(ValueError):
            self.crm.discount("O99", 10, "r1")
        self.assertEqual(len(self.crm.log), self.base_log_len)

    def test_unknown_actor_beats_missing_opp(self):
        with self.assertRaises(PermissionError):
            self.crm.discount("O99", 10, "ghost")

    def test_pct_bounds_and_type(self):
        for bad in (0, 31, -5, 100, 10.0, "10", True, False, None):
            with self.assertRaises(ValueError):
                self.crm.discount(self.opp, bad, "r1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 1000)
        self.assertEqual(len(self.crm.log), self.base_log_len)

    def test_bad_pct_beats_permission(self):
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp, 40, "r2")

    def test_permission_owner_or_manager(self):
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp, 10, "r2")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 1000)
        self.crm.discount(self.opp, 10, "m1")

    def test_rep_discount_capped_at_10(self):
        for pct in (11, 15, 30):
            with self.assertRaises(PermissionError):
                self.crm.discount(self.opp, pct, "r1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 1000)
        self.crm.discount(self.opp, 10, "r1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 900)

    def test_rep_cap_checked_after_owner_check(self):
        # non-owner rep with pct > 10 -> PermissionError either way, but the
        # owner/manager check (3) must come before the 10 percent cap (5).
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp, 11, "r2")

    def test_manager_can_discount_up_to_30(self):
        self.crm.discount(self.opp, 30, "m1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 700)

    def test_final_stage_rejected(self):
        self.crm.advance(self.opp, "proposal", "r1")
        self.crm.advance(self.opp, "negotiation", "r1")
        self.crm.advance(self.opp, "won", "r1")
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp, 10, "r1")
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp, 10, "m1")

    def test_permission_before_final_check(self):
        self.crm.advance(self.opp, "lost", "r1")
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp, 10, "r2")

    def test_cumulative_discount_capped_at_30_percent(self):
        self.crm.discount(self.opp, 25, "m1")   # 1000 -> 750; 75000 >= 70000
        self.crm.discount(self.opp, 5, "r1")    # 750 -> 712; 71200 >= 70000
        self.assertEqual(self.crm.opps[self.opp]["amount"], 712)
        self.crm.discount(self.opp, 1, "r1")    # 712 -> 704; 70400 >= 70000
        self.assertEqual(self.crm.opps[self.opp]["amount"], 704)
        with self.assertRaises(ValueError):     # 704 -> 696; 69600 < 70000
            self.crm.discount(self.opp, 1, "r1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 704)

    def test_cumulative_cap_uses_original_amount_not_current(self):
        self.crm.discount(self.opp, 30, "m1")  # 1000 -> 700, exactly 70 percent
        self.assertEqual(self.crm.opps[self.opp]["amount"], 700)

    def test_discount_uses_current_amount_as_base(self):
        self.crm.discount(self.opp, 10, "r1")   # 1000 -> 900
        self.crm.discount(self.opp, 10, "r1")   # 900 -> 810
        self.assertEqual(self.crm.opps[self.opp]["amount"], 810)

    def test_failed_discount_changes_nothing(self):
        before = (copy.deepcopy(self.crm.opps), copy.deepcopy(self.crm.log))
        for call in (
            lambda: self.crm.discount("O99", 10, "r1"),
            lambda: self.crm.discount(self.opp, 0, "r1"),
            lambda: self.crm.discount(self.opp, 10, "r2"),
            lambda: self.crm.discount(self.opp, 20, "r1"),
        ):
            with self.assertRaises(Exception):
                call()
        after = (copy.deepcopy(self.crm.opps), copy.deepcopy(self.crm.log))
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
