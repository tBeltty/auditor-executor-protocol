"""Tests for CRM.discount and CRM.transfer."""

import unittest

from support import add, converted, make_crm, qualified, snapshot, win


class TestDiscount(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        self.opp = converted(self.crm, "a@b.com", 10000)

    def test_rep_discount_10_floors(self):
        self.crm.discount(self.opp, 10, "r1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 9000)
        self.assertEqual(self.crm.opps[self.opp]["original_amount"], 10000)
        self.assertEqual(self.crm.log[-1], ("discount", "O1", "r1"))

    def test_floor_division_is_floor_not_round(self):
        # 10015 * 90 // 100 == 9013 (floor), whereas rounding would give 9014
        c = make_crm()
        opp = converted(c, "x@b.com", 10015)
        c.discount(opp, 10, "m1")
        self.assertEqual(c.opps[opp]["amount"], 9013)

    def test_floor_at_the_30_percent_edge_rejects(self):
        # 9999 * 70 // 100 == 6999, and 6999*100 < 9999*70: the floor makes a
        # nominal-30% discount exceed the cap, so the spec check rejects it.
        c = make_crm()
        opp = converted(c, "x@b.com", 9999)
        before = snapshot(c)
        with self.assertRaises(ValueError):
            c.discount(opp, 30, "m1")
        self.assertEqual(snapshot(c), before)
        # the aligned amount 10000 passes exactly at the boundary
        c2 = make_crm()
        opp2 = converted(c2, "y@b.com", 10000)
        c2.discount(opp2, 30, "m1")
        self.assertEqual(c2.opps[opp2]["amount"], 7000)


    def test_single_30_is_allowed_but_31_rejected(self):
        self.crm.discount(self.opp, 30, "m1")  # 10000 -> 7000; 700000 >= 700000
        self.assertEqual(self.crm.opps[self.opp]["amount"], 7000)
        c = make_crm()
        opp = converted(c, "a@b.com", 10000)
        with self.assertRaises(ValueError):
            c.discount(opp, 31, "m1")
        self.assertEqual(c.opps[opp]["amount"], 10000)

    def test_rep_cap_is_10_inclusive(self):
        self.crm.discount(self.opp, 10, "r1")
        before = snapshot(self.crm)
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp, 11, "r1")
        self.assertEqual(snapshot(self.crm), before)

    def test_cumulative_cap_of_30_percent(self):
        c = self.crm
        c.discount(self.opp, 10, "r1")  # 10000 -> 9000
        c.discount(self.opp, 10, "m1")  # -> 8100
        c.discount(self.opp, 10, "m1")  # -> 7290
        before = snapshot(c)
        with self.assertRaises(ValueError):  # -> 6561 would be past the 30% cap
            c.discount(self.opp, 10, "m1")
        self.assertEqual(snapshot(c), before)
        self.assertEqual(c.opps[self.opp]["amount"], 7290)

    def test_pct_type_and_range_checks(self):
        for bad in (0, -1, 31, 100, True, False, 10.0, "10", None, 2.5):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    self.crm.discount(self.opp, bad, "m1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 10000)

    def test_actor_check_first(self):
        with self.assertRaises(PermissionError):
            self.crm.discount("O404", 999, "ghost")  # unknown actor beats all

    def test_missing_opp_value_error(self):
        with self.assertRaises(ValueError):
            self.crm.discount("O404", 5, "m1")

    def test_pct_check_before_permission(self):
        # wrong rep AND bad pct -> ValueError (pct is check 2, permission is 3)
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp, 50, "r2")

    def test_permission_before_final_stage(self):
        win(self.crm, self.opp)
        # a different rep on a final opp -> PermissionError (3) before stage (4)
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp, 5, "r2")

    def test_final_stage_rejected(self):
        win(self.crm, self.opp)
        before = snapshot(self.crm)
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp, 5, "m1")
        self.assertEqual(snapshot(self.crm), before)

    def test_cumulative_check_after_rep_cap(self):
        # rep asking 15% on a deep-discounted opp: the cap (5) fires first
        self.crm.discount(self.opp, 25, "m1")  # 10000 -> 7500
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp, 15, "r1")

    def test_discount_does_not_change_stage(self):
        self.crm.advance(self.opp, "proposal", "r1")
        self.crm.discount(self.opp, 5, "r1")
        self.assertEqual(self.crm.opps[self.opp]["stage"], "proposal")


class TestTransfer(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        self.opp = converted(self.crm, "a@b.com", 1000)  # owner r1
        self.assertEqual(self.crm.opps[self.opp]["owner"], "r1")

    def test_manager_happy_path(self):
        self.crm.transfer(self.opp, "r2", "m1")
        self.assertEqual(self.crm.opps[self.opp]["owner"], "r2")
        self.assertEqual(self.crm.log[-1], ("transfer", "O1", "m1"))

    def test_new_owner_can_act_old_owner_cannot(self):
        self.crm.transfer(self.opp, "r2", "m1")
        with self.assertRaises(PermissionError):
            self.crm.advance(self.opp, "proposal", "r1")
        self.crm.advance(self.opp, "proposal", "r2")
        self.assertEqual(self.crm.opps[self.opp]["stage"], "proposal")

    def test_actor_check_first(self):
        with self.assertRaises(PermissionError):
            self.crm.transfer("O404", "nobody", "ghost")

    def test_missing_opp_before_manager_check(self):
        # unknown opp touched by a rep -> ValueError (check 1 before 2)
        with self.assertRaises(ValueError):
            self.crm.transfer("O404", "r2", "r1")

    def test_only_managers_transfer(self):
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.opp, "r2", "r1")  # the current owner is a rep

    def test_manager_check_before_target_validation(self):
        # a rep naming a bogus target -> PermissionError (2), not ValueError (3)
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.opp, "nonexistent", "r2")

    def test_target_must_be_known_rep(self):
        for bad in ("m1", "nonexistent", "r1", None, 5):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    self.crm.transfer(self.opp, bad, "m1")

    def test_target_same_as_current_owner_value_error(self):
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "r1", "m1")

    def test_final_stage_rejected(self):
        win(self.crm, self.opp)
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "r2", "m1")

    def test_final_check_before_target_checks(self):
        # final stage + same owner -> ValueError from the stage rule (check 4)
        win(self.crm, self.opp)
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "r1", "m1")

    def test_target_at_capacity_rejected(self):
        # r2 cap 1: give it one qualified lead so load == 1
        l2 = add(self.crm, "2@b.com", source="referral")  # routes to r2 (r1 busy)
        self.assertEqual(self.crm.leads[l2]["owner"], "r2")
        before = snapshot(self.crm)
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "r2", "m1")
        self.assertEqual(snapshot(self.crm), before)
        self.assertEqual(self.crm.opps[self.opp]["owner"], "r1")

    def test_transfer_assign_branch_pinned_by_constructed_state(self):
        # The spec says transfer frees the previous owner's slot "exactly as in
        # advance". That branch is unreachable through the public API alone:
        # add_lead only queues when every rep is at capacity, and every drain
        # refills the rep it freed, so a non-empty waiting queue always
        # coincides with all reps full -- which in turn makes transfer's own
        # capacity check (6) impossible to pass. We therefore construct that
        # state directly to pin the documented behavior.
        c = make_crm()
        l1 = qualified(c, "1@b.com")
        opp = c.convert(l1, 100, "m1")  # r1: load 1 (open opp)
        add(c, "2@b.com")  # r1 load 2 (== cap 2)
        add(c, "3@b.com")  # r2 load 1 (== cap 1)
        l4 = add(c, "4@b.com")
        self.assertIsNone(c.leads[l4]["owner"])
        # now fabricate the contradiction: r3 with free capacity while L4 waits
        c._users["r3"] = {"id": "r3", "role": "rep", "capacity": 1}
        c._reps.append("r3")
        c.transfer(opp, "r3", "m1")
        self.assertEqual(c.opps[opp]["owner"], "r3")
        # previous owner r1 freed a slot (its opp left) -> queue drains to r1
        self.assertEqual(c.leads[l4]["owner"], "r1")
        self.assertEqual(
            c.log[-2:],
            [("transfer", "O1", "m1"), ("assign", "L4", "system")],
        )


    def test_failed_transfer_appends_nothing(self):
        before = snapshot(self.crm)
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "m1", "m1")  # manager as target
        self.assertEqual(snapshot(self.crm), before)


if __name__ == "__main__":
    unittest.main()
