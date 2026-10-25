"""Unit tests for CRM.discount and CRM.transfer."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crm_test_support import add_lead, convert_lead, make_crm  # noqa: E402
from crm_test_support import walk_to_final  # noqa: E402,E501


class DiscountTests(unittest.TestCase):
    def _open_opp(self, crm, amount=1000):
        return convert_lead(crm, 0, amount)[1]  # owned by r1

    def test_discount_applies_and_logs_but_keeps_original(self):
        crm = make_crm()
        opp_id = self._open_opp(crm, 1000)
        crm.discount(opp_id, 10, "r1")
        opp = crm.opps[opp_id]
        self.assertEqual(opp["amount"], 900)
        self.assertEqual(opp["original_amount"], 1000)
        self.assertEqual(crm.log[-1], ("discount", opp_id, "r1"))

    def test_pct_bounds_and_type(self):
        crm = make_crm()
        opp_id = self._open_opp(crm, 1000)
        for bad in (0, 31, -5, 100, "10", 10.0, True, False, None, [10]):
            with self.subTest(pct=bad):
                log_before = list(crm.log)
                amount_before = crm.opps[opp_id]["amount"]
                with self.assertRaises(ValueError):
                    crm.discount(opp_id, bad, "r1")
                self.assertEqual(crm.opps[opp_id]["amount"], amount_before)
                self.assertEqual(crm.log, log_before)

    def test_unknown_actor_checked_first(self):
        crm = make_crm()
        opp_id = self._open_opp(crm)
        for actor in ("ghost", 4, None):
            with self.subTest(actor=actor):
                with self.assertRaises(PermissionError):
                    crm.discount("O404", 40, actor)
        self.assertEqual(crm.log[-1], ("convert", opp_id, "m1"))

    def test_unknown_opportunity_raises_value_error(self):
        crm = make_crm()
        with self.assertRaises(ValueError):
            crm.discount("O404", 10, "m1")
        self.assertEqual(crm.log, [])

    def test_owner_or_manager_permission(self):
        crm = make_crm()
        opp_id = self._open_opp(crm)
        with self.assertRaises(PermissionError):
            crm.discount(opp_id, 10, "r3")
        crm.discount(opp_id, 10, "m1")  # manager that is not the owner
        self.assertEqual(crm.opps[opp_id]["amount"], 900)

    def test_final_stage_rejected(self):
        crm = make_crm()
        opp_id = self._open_opp(crm, 500)
        walk_to_final(crm, opp_id, "r1")
        log_before = list(crm.log)
        with self.assertRaises(ValueError):
            crm.discount(opp_id, 10, "r1")
        self.assertEqual(crm.opps[opp_id]["amount"], 500)
        self.assertEqual(crm.log, log_before)

    def test_non_manager_cap_of_ten(self):
        crm = make_crm()
        opp_id = self._open_opp(crm, 1000)
        with self.assertRaises(PermissionError):
            crm.discount(opp_id, 11, "r1")
        self.assertEqual(crm.opps[opp_id]["amount"], 1000)
        crm.discount(opp_id, 10, "r1")
        self.assertEqual(crm.opps[opp_id]["amount"], 900)

    def test_manager_may_discount_up_to_thirty(self):
        crm = make_crm()
        opp_id = self._open_opp(crm, 1000)
        crm.discount(opp_id, 30, "m1")
        self.assertEqual(crm.opps[opp_id]["amount"], 700)

    def test_final_stage_checked_before_non_manager_cap(self):
        # A rep asking 15 on a final-stage opportunity fails on the stage
        # check (4) with ValueError, not on the 10-cap (5).
        crm = make_crm()
        opp_id = self._open_opp(crm, 500)
        walk_to_final(crm, opp_id, "r1")
        with self.assertRaises(ValueError):
            crm.discount(opp_id, 15, "r1")

    def test_cumulative_discount_floor_rule(self):
        crm = make_crm()
        opp_id = self._open_opp(crm, 1000)
        crm.discount(opp_id, 10, "m1")            # 1000 -> 900, running 10%
        crm.discount(opp_id, 20, "m1")            # 900 -> 720, running 28%
        self.assertEqual(crm.opps[opp_id]["amount"], 720)
        log_before = list(crm.log)
        with self.assertRaises(ValueError):
            crm.discount(opp_id, 25, "m1")        # would be 540 -> 54% price
        with self.assertRaises(ValueError):
            crm.discount(opp_id, 5, "m1")         # 684 -> 68.4% price
        self.assertEqual(crm.opps[opp_id]["amount"], 720)
        self.assertEqual(crm.log, log_before)

    def test_thirty_percent_cumulative_is_the_exact_limit(self):
        crm = make_crm()
        opp_id = self._open_opp(crm, 1000)
        crm.discount(opp_id, 15, "m1")            # -> 850
        crm.discount(opp_id, 10, "m1")            # -> 765
        crm.discount(opp_id, 3, "m1")             # running 25.9% -> 742
        self.assertEqual(crm.opps[opp_id]["amount"], 742)


class TransferTests(unittest.TestCase):
    def _open_opp(self, crm, amount=1000):
        return convert_lead(crm, 0, amount)[1]  # owned by r1

    def test_happy_path_reassigns_owner_and_logs(self):
        crm = make_crm()
        opp_id = self._open_opp(crm, 500)
        crm.transfer(opp_id, "r3", "m1")
        self.assertEqual(crm.opps[opp_id]["owner"], "r3")
        self.assertEqual(crm.log[-1], ("transfer", opp_id, "m1"))

    def test_unknown_actor_checked_first(self):
        crm = make_crm()
        opp_id = self._open_opp(crm, 500)
        for actor in ("ghost", 8, None):
            with self.subTest(actor=actor):
                with self.assertRaises(PermissionError):
                    crm.transfer(opp_id, "ghost-2", actor)
        self.assertEqual(crm.log[-1], ("convert", opp_id, "m1"))

    def test_unknown_opportunity_raises_value_error(self):
        crm = make_crm()
        with self.assertRaises(ValueError):
            crm.transfer("O404", "r1", "m1")
        self.assertEqual(crm.log, [])

    def test_only_managers_may_transfer(self):
        crm = make_crm()
        opp_id = self._open_opp(crm, 500)
        actor_cases = ("r1", "r3")  # owner rep and an unrelated rep
        for actor in actor_cases:
            with self.subTest(actor=actor):
                log_before = list(crm.log)
                owner_before = crm.opps[opp_id]["owner"]
                with self.assertRaises(PermissionError):
                    crm.transfer(opp_id, "r2", actor)
                self.assertEqual(crm.opps[opp_id]["owner"], owner_before)
                self.assertEqual(crm.log, log_before)

    def test_new_owner_must_be_a_known_rep(self):
        crm = make_crm()
        opp_id = self._open_opp(crm, 500)
        for bad in ("ghost", "m1", None, 5):
            with self.subTest(new_owner=bad):
                with self.assertRaises(ValueError):
                    crm.transfer(opp_id, bad, "m1")
        self.assertEqual(crm.opps[opp_id]["owner"], "r1")

    def test_final_stage_rejected(self):
        crm = make_crm()
        opp_id = self._open_opp(crm, 500)
        walk_to_final(crm, opp_id, "r1")
        log_before = list(crm.log)
        with self.assertRaises(ValueError):
            crm.transfer(opp_id, "r2", "m1")
        self.assertEqual(crm.opps[opp_id]["owner"], "r1")
        self.assertEqual(crm.log, log_before)

    def test_same_owner_rejected(self):
        crm = make_crm()
        opp_id = self._open_opp(crm, 500)
        with self.assertRaises(ValueError):
            crm.transfer(opp_id, "r1", "m1")
        self.assertEqual(crm.opps[opp_id]["owner"], "r1")

    def test_new_owner_at_capacity_rejected(self):
        # r2 (cap 1) already owns one lead's worth of load: L2 is queued
        # right after L1 was converted, so r2 owns exactly one lead.
        crm = make_crm()
        opp_id = self._open_opp(crm, 500)         # L1 -> r1, opp to r1
        r2_lead = add_lead(crm, 1)                # -> r2 (load 1 = capacity)
        self.assertEqual(crm.leads[r2_lead]["owner"], "r2")
        log_before = list(crm.log)
        with self.assertRaises(ValueError):
            crm.transfer(opp_id, "r2", "m1")
        self.assertEqual(crm.opps[opp_id]["owner"], "r1")
        self.assertEqual(crm.log, log_before)

    def test_transfer_leaves_no_assign_entry_when_queue_is_empty(self):
        # With no waiting leads, the spec's slot-freeing after a transfer
        # simply does nothing: no "assign" entry may appear.
        crm = make_crm([
            {"id": "r1", "role": "rep", "capacity": 2},
            {"id": "r2", "role": "rep", "capacity": 5},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        lead1 = add_lead(crm, 0)          # -> r1
        lead2 = add_lead(crm, 1)          # -> r1 (r1 now at capacity 2)
        crm.qualify(lead1, "r1")
        opp_id = crm.convert(lead1, 100, "r1")  # r1 load: L2 + O1 = 2
        lead3 = add_lead(crm, 2)          # ties on load 1 -> smallest id r1
        self.assertEqual(crm.leads[lead3]["owner"], "r1")
        crm.transfer(opp_id, "r2", "m1")  # r1 load drops to 1, nobody waits
        self.assertEqual(crm.opps[opp_id]["owner"], "r2")
        self.assertEqual(crm.log[-1], ("transfer", opp_id, "m1"))
        self.assertEqual(
            [entry[0] for entry in crm.log],
            ["add_lead", "add_lead", "add_lead", "qualify", "convert",
             "transfer"],
        )

    def test_transfer_target_at_capacity_does_not_move_anything(self):
        crm = make_crm()
        _, opp_id = convert_lead(crm, 0, 500)     # r1 -> O1
        for n in (1, 2, 3, 4, 5):
            add_lead(crm, n)                       # r1, r2, then r3 x3
        # r3 holds 3 leads of capacity 3; try moving O1 there.
        owner_r3 = [l for l in crm.leads.values() if l["owner"] == "r3"]
        self.assertEqual(len(owner_r3), 3)
        with self.assertRaises(ValueError):
            crm.transfer(opp_id, "r3", "m1")
        self.assertEqual(crm.opps[opp_id]["owner"], "r1")


if __name__ == "__main__":
    unittest.main()
