"""Tests for advance (stage machine + manager gate) and discount."""

import unittest

from crm import CRM


def open_crm(amount=1000):
    """CRM with one opportunity O1 owned by rep r1, at stage 'prospect'."""
    crm = CRM([
        {"id": "r1", "role": "rep", "capacity": 2},
        {"id": "r2", "role": "rep", "capacity": 2},
        {"id": "m1", "role": "manager", "capacity": 2},
    ])
    crm.add_lead("a@acme.com", "A", "referral", "m1")
    crm.qualify("L1", "r1")
    crm.convert("L1", amount, "r1")
    return crm


class TestAdvanceHappyPath(unittest.TestCase):
    def test_full_path_to_won(self):
        crm = open_crm()
        crm.advance("O1", "proposal", "r1")
        self.assertEqual(crm.opps["O1"]["stage"], "proposal")
        crm.advance("O1", "negotiation", "r1")
        self.assertEqual(crm.opps["O1"]["stage"], "negotiation")
        crm.advance("O1", "won", "r1")
        self.assertEqual(crm.opps["O1"]["stage"], "won")
        self.assertEqual(crm.log[-3:], [
            ("advance", "O1", "r1"),
            ("advance", "O1", "r1"),
            ("advance", "O1", "r1"),
        ])
        self.assertEqual(len(crm.log), 6)

    def test_lost_from_each_open_stage(self):
        for path in [[], ["proposal"], ["proposal", "negotiation"]]:
            with self.subTest(path=path):
                crm = open_crm()
                for stage in path:
                    crm.advance("O1", stage, "r1")
                crm.advance("O1", "lost", "r1")
                self.assertEqual(crm.opps["O1"]["stage"], "lost")
                self.assertEqual(crm.log[-1], ("advance", "O1", "r1"))

    def test_manager_may_advance(self):
        crm = open_crm()
        crm.advance("O1", "proposal", "m1")
        self.assertEqual(crm.opps["O1"]["stage"], "proposal")


class TestAdvanceRejections(unittest.TestCase):
    def test_unknown_opp(self):
        crm = open_crm()
        with self.assertRaises(ValueError):
            crm.advance("O9", "proposal", "r1")

    def test_unknown_stage(self):
        crm = open_crm()
        for bad in ["closed", "Won", "", None, 0, "prospect ", ["won"]]:
            with self.subTest(stage=bad):
                with self.assertRaises(ValueError):
                    crm.advance("O1", bad, "r1")
        self.assertEqual(crm.opps["O1"]["stage"], "prospect")

    def test_stage_validity_before_permission(self):
        crm = open_crm()
        with self.assertRaises(ValueError):  # rule 2 beats rule 3
            crm.advance("O1", "nonsense", "r2")

    def test_non_owner_rep_forbidden(self):
        crm = open_crm()
        with self.assertRaises(PermissionError):
            crm.advance("O1", "proposal", "r2")
        self.assertEqual(crm.opps["O1"]["stage"], "prospect")
        self.assertEqual(len(crm.log), 3)

    def test_final_stage_rejects_any_move(self):
        crm = open_crm()
        crm.advance("O1", "lost", "m1")
        n = len(crm.log)
        for stage in ["prospect", "proposal", "negotiation", "won", "lost"]:
            with self.subTest(stage=stage):
                with self.assertRaises(ValueError):
                    crm.advance("O1", stage, "m1")
        self.assertEqual(len(crm.log), n)

    def test_permission_before_finality(self):
        crm = open_crm()
        crm.advance("O1", "lost", "r1")
        with self.assertRaises(PermissionError):
            crm.advance("O1", "lost", "r2")

    def test_skipping_stages_rejected(self):
        crm = open_crm()
        with self.assertRaises(ValueError):
            crm.advance("O1", "won", "r1")  # prospect -> won is a skip
        self.assertEqual(crm.opps["O1"]["stage"], "prospect")
        crm.advance("O1", "proposal", "r1")
        with self.assertRaises(ValueError):
            crm.advance("O1", "won", "r1")  # proposal -> won is a skip
        self.assertEqual(crm.opps["O1"]["stage"], "proposal")

    def test_backwards_and_same_stage_rejected(self):
        crm = open_crm()
        crm.advance("O1", "proposal", "r1")
        crm.advance("O1", "negotiation", "r1")
        for bad in ["prospect", "proposal", "negotiation"]:
            with self.subTest(stage=bad):
                with self.assertRaises(ValueError):
                    crm.advance("O1", bad, "r1")
        self.assertEqual(crm.opps["O1"]["stage"], "negotiation")

    def test_failed_advance_logs_nothing(self):
        crm = open_crm()
        before = list(crm.log)
        with self.assertRaises(ValueError):
            crm.advance("O1", "won", "r1")
        self.assertEqual(crm.log, before)


class TestNegotiationManagerGate(unittest.TestCase):
    def test_rep_blocked_above_50000(self):
        crm = open_crm(50001)
        crm.advance("O1", "proposal", "r1")
        with self.assertRaises(PermissionError):
            crm.advance("O1", "negotiation", "r1")
        self.assertEqual(crm.opps["O1"]["stage"], "proposal")
        self.assertEqual(len(crm.log), 4)

    def test_manager_allowed_above_50000(self):
        crm = open_crm(50001)
        crm.advance("O1", "proposal", "r1")
        crm.advance("O1", "negotiation", "m1")
        self.assertEqual(crm.opps["O1"]["stage"], "negotiation")

    def test_exactly_50000_allowed_for_rep(self):
        crm = open_crm(50000)
        crm.advance("O1", "proposal", "r1")
        crm.advance("O1", "negotiation", "r1")
        self.assertEqual(crm.opps["O1"]["stage"], "negotiation")

    def test_gate_only_applies_to_negotiation(self):
        crm = open_crm(999999)
        crm.advance("O1", "proposal", "r1")
        crm.advance("O1", "negotiation", "m1")
        crm.advance("O1", "won", "r1")  # closing a big deal needs no manager
        self.assertEqual(crm.opps["O1"]["stage"], "won")

    def test_gate_uses_current_amount_after_discount(self):
        crm = open_crm(60000)
        crm.advance("O1", "proposal", "r1")
        crm.discount("O1", 30, "m1")  # 60000 -> 42000
        self.assertEqual(crm.opps["O1"]["amount"], 42000)
        crm.advance("O1", "negotiation", "r1")
        self.assertEqual(crm.opps["O1"]["stage"], "negotiation")

    def test_gate_checked_after_transition_validity(self):
        crm = open_crm(60000)
        with self.assertRaises(ValueError):  # illegal skip is rule 5
            crm.advance("O1", "negotiation", "r1")

    def test_lost_allowed_for_rep_on_big_deal(self):
        crm = open_crm(60000)
        crm.advance("O1", "proposal", "r1")
        crm.advance("O1", "lost", "r1")
        self.assertEqual(crm.opps["O1"]["stage"], "lost")


class TestDiscount(unittest.TestCase):
    def test_owner_small_discount(self):
        crm = open_crm(10000)
        crm.discount("O1", 10, "r1")
        self.assertEqual(crm.opps["O1"]["amount"], 9000)
        self.assertEqual(crm.opps["O1"]["original_amount"], 10000)
        self.assertEqual(crm.opps["O1"]["stage"], "prospect")
        self.assertEqual(crm.log[-1], ("discount", "O1", "r1"))

    def test_manager_up_to_30(self):
        for pct in [1, 10, 11, 29, 30]:
            with self.subTest(pct=pct):
                crm = open_crm(10000)
                crm.discount("O1", pct, "m1")
                self.assertEqual(crm.opps["O1"]["amount"], 10000 * (100 - pct) // 100)

    def test_floor_division_is_integral(self):
        crm = open_crm(999)
        crm.discount("O1", 10, "m1")  # 999*90//100 == 899
        self.assertEqual(crm.opps["O1"]["amount"], 899)

    def test_rep_may_use_10(self):
        crm = open_crm(10000)
        crm.discount("O1", 10, "r1")
        self.assertEqual(crm.opps["O1"]["amount"], 9000)

    def test_rep_limited_to_10(self):
        for pct in [11, 12, 20, 30]:
            with self.subTest(pct=pct):
                crm = open_crm(10000)
                with self.assertRaises(PermissionError):
                    crm.discount("O1", pct, "r1")
                self.assertEqual(crm.opps["O1"]["amount"], 10000)
                self.assertEqual(len(crm.log), 3)

    def test_pct_validation(self):
        crm = open_crm(10000)
        for bad in [0, -1, 31, 100, True, False, 10.0, "10", None, [], {}]:
            with self.subTest(pct=bad):
                with self.assertRaises(ValueError):
                    crm.discount("O1", bad, "m1")
        self.assertEqual(crm.opps["O1"]["amount"], 10000)
        self.assertEqual(len(crm.log), 3)

    def test_pct_validated_before_permission(self):
        crm = open_crm(10000)
        with self.assertRaises(ValueError):  # rule 2 before rule 3
            crm.discount("O1", 99, "r2")

    def test_non_owner_forbidden(self):
        crm = open_crm(10000)
        with self.assertRaises(PermissionError):
            crm.discount("O1", 5, "r2")

    def test_final_stage_forbidden(self):
        crm = open_crm(10000)
        crm.advance("O1", "lost", "m1")
        before = list(crm.log)
        with self.assertRaises(ValueError):
            crm.discount("O1", 5, "m1")
        self.assertEqual(crm.opps["O1"]["amount"], 10000)
        self.assertEqual(crm.log, before)

    def test_permission_before_finality(self):
        crm = open_crm(10000)
        crm.advance("O1", "lost", "m1")
        with self.assertRaises(PermissionError):
            crm.discount("O1", 5, "r2")

    def test_cumulative_floor_allows_up_to_exactly_70_percent(self):
        crm = open_crm(10000)
        crm.discount("O1", 10, "m1")
        self.assertEqual(crm.opps["O1"]["amount"], 9000)
        crm.discount("O1", 10, "m1")
        self.assertEqual(crm.opps["O1"]["amount"], 8100)
        crm.discount("O1", 10, "m1")
        self.assertEqual(crm.opps["O1"]["amount"], 7290)
        crm.discount("O1", 3, "m1")  # 7290*97//100 == 7071, still above floor
        self.assertEqual(crm.opps["O1"]["amount"], 7071)
        crm.discount("O1", 1, "m1")  # 7071*99//100 == 7000, right on the floor
        self.assertEqual(crm.opps["O1"]["amount"], 7000)
        self.assertEqual(crm.log[-1], ("discount", "O1", "m1"))

    def test_single_30_percent_is_allowed_then_blocked(self):
        crm = open_crm(10000)
        crm.discount("O1", 30, "m1")
        self.assertEqual(crm.opps["O1"]["amount"], 7000)
        before = list(crm.log)
        with self.assertRaises(ValueError):  # 6930 is below the 7000 floor
            crm.discount("O1", 1, "m1")
        self.assertEqual(crm.opps["O1"]["amount"], 7000)
        self.assertEqual(crm.log, before)

    def test_floor_uses_original_amount_not_current(self):
        crm = open_crm(10000)
        crm.discount("O1", 30, "m1")
        with self.assertRaises(ValueError):
            crm.discount("O1", 10, "r1")

    def test_floor_checked_after_rep_cap(self):
        crm = open_crm(10000)
        crm.discount("O1", 30, "m1")
        with self.assertRaises(PermissionError):  # rule 5 before rule 6
            crm.discount("O1", 20, "r1")

    def test_unknown_opp(self):
        crm = open_crm()
        with self.assertRaises(ValueError):
            crm.discount("O7", 5, "m1")


if __name__ == "__main__":
    unittest.main()
