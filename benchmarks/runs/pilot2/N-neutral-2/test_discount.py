"""Guard groups: discount limits (per-call cap, manager ceiling) and the
cumulative floor tied to original_amount."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import fixtures  # noqa: E402


def deal(amount=10000, owner_capacity=5):
    system = fixtures.make(("r1", "rep", owner_capacity), ("m1", "manager", 0))
    lead = system.add_lead("deal@corp.com", "Deal", "referral", "r1")
    system.qualify(lead, "r1")
    opp = system.convert(lead, amount, "r1")
    return system, opp


class DiscountRangeTests(unittest.TestCase):
    def setUp(self):
        self.crm, self.opp = deal()

    def test_pct_must_be_int_in_range(self):
        for bad in (0, -1, 31, 100, True, False, 5.0, "5", None):
            with self.subTest(pct=bad):
                with self.assertRaises(ValueError):
                    self.crm.discount(self.opp, bad, "r1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 10000)

    def test_range_edges_are_accepted_by_manager(self):
        system, opp = deal()
        system.discount(opp, 1, "m1")
        self.assertEqual(system.opps[opp]["amount"], 9900)
        system.discount(opp, 29, "m1")
        self.assertEqual(system.opps[opp]["amount"], 7029)

    def test_unknown_opportunity_is_rejected(self):
        with self.assertRaises(ValueError):
            self.crm.discount("O404", 5, "r1")


class DiscountPermissionTests(unittest.TestCase):
    def setUp(self):
        self.crm, self.opp = deal()

    def test_rep_ceiling_is_ten(self):
        self.crm.discount(self.opp, 10, "r1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 9000)
        system, opp = deal()
        with self.assertRaises(PermissionError):
            system.discount(opp, 11, "r1")
        self.assertEqual(system.opps[opp]["amount"], 10000)

    def test_other_rep_cannot_discount(self):
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp, 5, "r2")

    def test_manager_may_exceed_rep_ceiling(self):
        self.crm.discount(self.opp, 25, "m1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 7500)

    def test_rep_ceiling_precedes_cumulative_floor(self):
        system, opp = deal()
        system.discount(opp, 30, "m1")  # amount now 7000 of original 10000
        # pct 11 violates the rep ceiling; that PermissionError comes first
        with self.assertRaises(PermissionError):
            system.discount(opp, 11, "r1")


class FinalStageTests(unittest.TestCase):
    def test_cannot_discount_won(self):
        system = fixtures.make(("r1", "rep", 5), ("m1", "manager", 0))
        lead = system.add_lead("w@corp.com", "W", "referral", "r1")
        system.qualify(lead, "r1")
        opp = system.convert(lead, 1000, "r1")
        system.advance(opp, "proposal", "r1")
        system.advance(opp, "negotiation", "r1")
        system.advance(opp, "won", "r1")
        with self.assertRaises(ValueError):
            system.discount(opp, 5, "m1")
        self.assertEqual(system.opps[opp]["amount"], 1000)

    def test_cannot_discount_lost(self):
        system, opp = deal()
        system.advance(opp, "lost", "r1")
        with self.assertRaises(ValueError):
            system.discount(opp, 5, "m1")


class CumulativeFloorTests(unittest.TestCase):
    def test_cumulative_thirty_percent_is_allowed_exactly(self):
        system, opp = deal(1000)
        system.discount(opp, 30, "m1")
        self.assertEqual(system.opps[opp]["amount"], 700)

    def test_beyond_thirty_percent_of_original_is_rejected(self):
        system, opp = deal(1000)
        system.discount(opp, 30, "m1")
        with self.assertRaises(ValueError):
            system.discount(opp, 1, "m1")
        self.assertEqual(system.opps[opp]["amount"], 700)

    def test_floor_uses_original_amount_not_running_amount(self):
        system, opp = deal(1000)
        system.discount(opp, 10, "m1")  # 900
        system.discount(opp, 10, "m1")  # 810
        system.discount(opp, 10, "m1")  # 729 (> 700, allowed)
        self.assertEqual(system.opps[opp]["amount"], 729)
        with self.assertRaises(ValueError):
            system.discount(opp, 5, "m1")  # 729*95//100 = 692 < 700
        self.assertEqual(system.opps[opp]["amount"], 729)

    def test_original_amount_is_never_reduced(self):
        system, opp = deal(2000)
        system.discount(opp, 30, "m1")
        self.assertEqual(system.opps[opp]["original_amount"], 2000)

    def test_floor_is_inclusive_at_exactly_seventy_percent(self):
        system, opp = deal(1000)
        system.discount(opp, 25, "m1")  # 750
        with self.assertRaises(ValueError):
            system.discount(opp, 7, "m1")  # 697 -> rejected (below 700)
        self.assertEqual(system.opps[opp]["amount"], 750)
        system, opp = deal(1000)
        system.discount(opp, 20, "m1")  # 800
        system.discount(opp, 12, "m1")  # 704
        with self.assertRaises(ValueError):
            system.discount(opp, 1, "m1")  # 696 -> rejected
        self.assertEqual(system.opps[opp]["amount"], 704)

    def test_exact_floor_passes(self):
        system, opp = deal(1000)
        system.discount(opp, 15, "m1")  # 850
        system.discount(opp, 17, "m1")  # 705
        with self.assertRaises(ValueError):
            system.discount(opp, 1, "m1")  # 697 rejected
        self.assertEqual(system.opps[opp]["amount"], 705)
        system, opp = deal(10000)
        system.discount(opp, 30, "m1")  # 7000 exactly at floor
        self.assertEqual(system.opps[opp]["amount"], 7000)

    def test_failed_discount_logs_nothing_and_keeps_amount(self):
        system, opp = deal(1000)
        system.discount(opp, 30, "m1")
        log_before = list(system.log)
        with self.assertRaises(ValueError):
            system.discount(opp, 5, "m1")
        self.assertEqual(system.log, log_before)
        self.assertEqual(system.opps[opp]["amount"], 700)

    def test_successful_discount_logs(self):
        system, opp = deal(1000)
        system.discount(opp, 10, "r1")
        self.assertEqual(system.log[-1], ("discount", opp, "r1"))


if __name__ == "__main__":
    unittest.main()
