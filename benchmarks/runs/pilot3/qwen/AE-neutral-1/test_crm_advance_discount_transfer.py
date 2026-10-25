"""Tests for CRM.advance, CRM.discount, CRM.transfer, CRM.forecast."""
import unittest

from crm import CRM


class AdvanceTest(unittest.TestCase):
    def setUp(self):
        self.crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 99},
        ])
        self.lid = self.crm.add_lead("a@x.com", "A", "referral", "m1")  # -> r1
        self.crm.qualify(self.lid, "r1")
        self.oid = self.crm.convert(self.lid, 10000, "r1")  # opp owned by r1

    def test_unknown_actor_first(self):
        with self.assertRaises(PermissionError):
            self.crm.advance("O404", "bogus", "ghost")

    def test_missing_opp(self):
        with self.assertRaises(ValueError):
            self.crm.advance("O42", "proposal", "m1")

    def test_bad_stage_beats_actor_check(self):
        # r2 is a known non-owner rep; step 2 (ValueError) runs before step 3
        with self.assertRaises(ValueError):
            self.crm.advance(self.oid, "pipeline", "r2")

    def test_non_owner_permission(self):
        with self.assertRaises(PermissionError):
            self.crm.advance(self.oid, "proposal", "r2")

    def test_full_happy_path(self):
        self.crm.advance(self.oid, "proposal", "r1")
        self.crm.advance(self.oid, "negotiation", "r1")  # 10000 <= 50000: rep ok
        self.crm.advance(self.oid, "won", "r1")
        self.assertEqual(self.crm.opps[self.oid]["stage"], "won")
        self.assertEqual(
            self.crm.log[-3:],
            [
                ("advance", self.oid, "r1"),
                ("advance", self.oid, "r1"),
                ("advance", self.oid, "r1"),
            ],
        )

    def test_cannot_skip_stages(self):
        with self.assertRaises(ValueError):
            self.crm.advance(self.oid, "negotiation", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance(self.oid, "won", "r1")
        self.assertEqual(self.crm.opps[self.oid]["stage"], "prospect")

    def test_same_stage_rejected(self):
        with self.assertRaises(ValueError):
            self.crm.advance(self.oid, "prospect", "r1")

    def test_lost_from_any_nonfinal(self):
        self.crm.advance(self.oid, "proposal", "m1")
        self.crm.advance(self.oid, "lost", "m1")
        self.assertEqual(self.crm.opps[self.oid]["stage"], "lost")
        with self.assertRaises(ValueError):
            self.crm.advance(self.oid, "won", "m1")
        with self.assertRaises(ValueError):
            self.crm.advance(self.oid, "lost", "m1")

    def test_final_stage_check_before_next_stage_check(self):
        self.crm.advance(self.oid, "proposal", "m1")
        self.crm.advance(self.oid, "negotiation", "m1")
        self.crm.advance(self.oid, "won", "m1")
        # won is final: step 4 (ValueError) fires before step 5
        with self.assertRaises(ValueError):
            self.crm.advance(self.oid, "negotiation", "m1")

    def test_negotiation_gate_big_deal(self):
        self.crm.advance(self.oid, "proposal", "r1")
        self.crm.opps[self.oid]["amount"] = 50001
        with self.assertRaises(PermissionError):
            self.crm.advance(self.oid, "negotiation", "r1")
        self.assertEqual(self.crm.opps[self.oid]["stage"], "proposal")
        self.crm.advance(self.oid, "negotiation", "m1")
        self.assertEqual(self.crm.opps[self.oid]["stage"], "negotiation")

    def test_negotiation_gate_boundary_50000(self):
        self.crm.advance(self.oid, "proposal", "r1")
        self.crm.opps[self.oid]["amount"] = 50000
        self.crm.advance(self.oid, "negotiation", "r1")  # not > 50000
        self.assertEqual(self.crm.opps[self.oid]["stage"], "negotiation")

    def test_stage_order_check_beats_manager_gate(self):
        self.crm.advance(self.oid, "proposal", "r1")
        self.crm.opps[self.oid]["amount"] = 60000
        # "won" is not the immediate next stage -> step 5 ValueError fires first
        with self.assertRaises(ValueError):
            self.crm.advance(self.oid, "won", "r1")

    def test_won_frees_slot_and_assigns_queue_fifo(self):
        # single rep capacity 1; two leads queued behind an open opp
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 9},
        ])
        l1 = crm.add_lead("a@x.com", "A", "referral", "m1")  # -> r1
        crm.qualify(l1, "m1")
        o1 = crm.convert(l1, 1000, "m1")  # r1 load still 1 (open opp)
        l2 = crm.add_lead("b@x.com", "B", "web", "m1")  # queued (oldest)
        l3 = crm.add_lead("c@x.com", "C", "web", "m1")  # queued
        self.assertIsNone(crm.leads[l2]["owner"])
        crm.advance(o1, "proposal", "m1")
        crm.advance(o1, "negotiation", "m1")
        crm.advance(o1, "won", "m1")
        self.assertEqual(crm.leads[l2]["owner"], "r1")  # oldest first
        self.assertIsNone(crm.leads[l3]["owner"])  # capacity 1: only one slot
        self.assertEqual(
            crm.log[-2:],
            [("advance", o1, "m1"), ("assign", l2, "system")],
        )

    def test_lost_frees_too(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 9},
        ])
        l1 = crm.add_lead("a@x.com", "A", "referral", "m1")
        crm.qualify(l1, "m1")
        o1 = crm.convert(l1, 1000, "m1")
        l2 = crm.add_lead("b@x.com", "B", "web", "m1")
        crm.advance(o1, "lost", "r1")
        self.assertEqual(crm.leads[l2]["owner"], "r1")
        self.assertEqual(crm.log[-1], ("assign", l2, "system"))

    def test_failed_advance_no_side_effects(self):
        log_before = list(self.crm.log)
        amount_before = self.crm.opps[self.oid]["amount"]
        with self.assertRaises(ValueError):
            self.crm.advance(self.oid, "won", "r1")  # skipping stages
        self.assertEqual(self.crm.log, log_before)
        self.assertEqual(self.crm.opps[self.oid]["stage"], "prospect")
        self.assertEqual(self.crm.opps[self.oid]["amount"], amount_before)


class DiscountTest(unittest.TestCase):
    def setUp(self):
        self.crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 2},
            {"id": "r2", "role": "rep", "capacity": 2},
            {"id": "m1", "role": "manager", "capacity": 9},
        ])
        lid = self.crm.add_lead("a@x.com", "A", "referral", "m1")  # -> r1
        self.crm.qualify(lid, "m1")
        self.oid = self.crm.convert(lid, 1000, "m1")  # opp owned by r1

    def test_unknown_actor_first(self):
        with self.assertRaises(PermissionError):
            self.crm.discount(self.oid, 999, "ghost")

    def test_bad_pct_beats_actor_check(self):
        # r2 is a known non-owner rep; step 2 (ValueError) before step 3
        for bad in [0, 31, 100, -5, True, False, 5.0, "5", None]:
            with self.assertRaises(ValueError):
                self.crm.discount(self.oid, bad, "r2")

    def test_non_owner_permission(self):
        with self.assertRaises(PermissionError):
            self.crm.discount(self.oid, 5, "r2")

    def test_final_stage_beats_manager_cap(self):
        self.crm.advance(self.oid, "proposal", "m1")
        self.crm.advance(self.oid, "negotiation", "m1")
        self.crm.advance(self.oid, "won", "m1")
        # stage final (step 4 ValueError) fires before step 5 cap check
        with self.assertRaises(ValueError):
            self.crm.discount(self.oid, 20, "r1")

    def test_rep_capped_at_10(self):
        with self.assertRaises(PermissionError):
            self.crm.discount(self.oid, 11, "r1")
        self.crm.discount(self.oid, 10, "r1")
        self.assertEqual(self.crm.opps[self.oid]["amount"], 900)

    def test_manager_up_to_30(self):
        self.crm.discount(self.oid, 30, "m1")
        self.assertEqual(self.crm.opps[self.oid]["amount"], 700)
        with self.assertRaises(ValueError):
            self.crm.discount(self.oid, 30, "m1")  # would drop below 700 floor

    def test_cumulative_floor_uses_original_amount(self):
        # 1000 -> 800 (20%)
        self.crm.discount(self.oid, 20, "m1")
        self.assertEqual(self.crm.opps[self.oid]["amount"], 800)
        # 800 -> 640: 64000 < 1000*70 -> ValueError
        with self.assertRaises(ValueError):
            self.crm.discount(self.oid, 20, "m1")
        # 800 -> 680 (15%): 68000 < 70000 -> ValueError
        with self.assertRaises(ValueError):
            self.crm.discount(self.oid, 15, "m1")
        # 800 -> 704 (12%): 70400 >= 70000 -> ok
        self.crm.discount(self.oid, 12, "m1")
        self.assertEqual(self.crm.opps[self.oid]["amount"], 704)

    def test_failed_discount_changes_nothing(self):
        log_before = list(self.crm.log)
        with self.assertRaises(PermissionError):
            self.crm.discount(self.oid, 25, "r1")  # rep over 10
        self.assertEqual(self.crm.log, log_before)
        self.assertEqual(self.crm.opps[self.oid]["amount"], 1000)

    def test_log_entry(self):
        self.crm.discount(self.oid, 5, "r1")
        self.assertEqual(self.crm.log[-1], ("discount", self.oid, "r1"))


class TransferTest(unittest.TestCase):
    def setUp(self):
        self.crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 3},
            {"id": "m1", "role": "manager", "capacity": 9},
        ])
        self.lid = self.crm.add_lead("a@x.com", "A", "referral", "m1")  # -> r1
        self.crm.qualify(self.lid, "m1")
        self.oid = self.crm.convert(self.lid, 1000, "m1")  # opp owned by r1
        # r2 has load 0 < capacity 3, so it can receive the transfer

    def test_unknown_actor_first(self):
        with self.assertRaises(PermissionError):
            self.crm.transfer("O404", "r2", "ghost")

    def test_missing_opp(self):
        with self.assertRaises(ValueError):
            self.crm.transfer("O99", "r2", "m1")

    def test_only_manager_may_transfer(self):
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.oid, "r2", "r1")
        # actor check (step 2) precedes new_owner check (step 3):
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.oid, "ghost", "r1")

    def test_new_owner_must_be_known_rep(self):
        with self.assertRaises(ValueError):
            self.crm.transfer(self.oid, "m1", "m1")  # manager, not rep
        with self.assertRaises(ValueError):
            self.crm.transfer(self.oid, "ghost", "m1")
        with self.assertRaises(ValueError):
            self.crm.transfer(self.oid, 5, "m1")

    def test_final_stage_rejected(self):
        self.crm.advance(self.oid, "proposal", "m1")
        self.crm.advance(self.oid, "negotiation", "m1")
        self.crm.advance(self.oid, "won", "m1")
        with self.assertRaises(ValueError):
            self.crm.transfer(self.oid, "r2", "m1")

    def test_same_owner_rejected(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 3},
            {"id": "m1", "role": "manager", "capacity": 9},
        ])
        lid = crm.add_lead("a@x.com", "A", "referral", "m1")
        crm.qualify(lid, "m1")
        oid = crm.convert(lid, 1000, "m1")  # owned by r1
        with self.assertRaises(ValueError):
            crm.transfer(oid, "r1", "m1")

    def test_destination_at_capacity_rejected(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 2},
            {"id": "r2", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 9},
        ])
        l_a = crm.add_lead("a@x.com", "A", "referral", "m1")  # -> r1
        l_b = crm.add_lead("b@x.com", "B", "referral", "m1")  # -> r2 (now full)
        crm.qualify(l_b, "m1")
        oid_b = crm.convert(l_b, 500, "m1")  # r2 still at capacity (open opp)
        crm.qualify(l_a, "m1")
        oid_a = crm.convert(l_a, 1000, "m1")
        with self.assertRaises(ValueError):
            crm.transfer(oid_a, "r2", "m1")
        self.assertEqual(crm.opps[oid_a]["owner"], "r1")

    def test_success_changes_owner_and_logs_exactly_one_entry(self):
        crm = self.crm
        before = len(crm.log)
        crm.transfer(self.oid, "r2", "m1")
        self.assertEqual(crm.opps[self.oid]["owner"], "r2")
        self.assertEqual(crm.log[before:], [("transfer", self.oid, "m1")])
        self.assertEqual(len(crm.log), before + 1)  # no stray assign entries
        # previous owner r1 now has a free slot; next add_lead goes to r1
        l_new = crm.add_lead("c@x.com", "C", "web", "m1")
        self.assertEqual(crm.leads[l_new]["owner"], "r1")


class ForecastTest(unittest.TestCase):
    def setUp(self):
        self.crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 5},
            {"id": "m1", "role": "manager", "capacity": 9},
        ])

    def _opp(self, email, amount, stage_seq):
        lid = self.crm.add_lead(email, "N", "referral", "m1")
        self.crm.qualify(lid, "m1")
        oid = self.crm.convert(lid, amount, "m1")
        for s in stage_seq:
            self.crm.advance(oid, s, "m1")
        return oid

    def test_empty(self):
        self.assertEqual(
            self.crm.forecast(), {"open": 0, "weighted": 0, "won": 0}
        )

    def test_weights_and_floor_division(self):
        self._opp("a@x.com", 1000, [])           # prospect: 1000*10//100 = 100
        self._opp("b@x.com", 999, ["proposal"])  # 999*30//100 = 299
        self._opp("c@x.com", 100000, ["proposal", "negotiation"])  # 60000
        f = self.crm.forecast()
        self.assertEqual(f["open"], 3)
        self.assertEqual(f["weighted"], 100 + 299 + 60000)
        self.assertEqual(f["won"], 0)

    def test_won_summed_and_lost_excluded(self):
        self._opp("a@x.com", 500, ["proposal", "negotiation", "won"])
        self._opp("b@x.com", 700, ["lost"])
        self._opp("c@x.com", 300, [])  # open prospect, weighted 30
        f = self.crm.forecast()
        self.assertEqual(f, {"open": 1, "weighted": 30, "won": 500})

    def test_discounted_amount_used(self):
        oid = self._opp("a@x.com", 1000, ["proposal"])
        self.crm.discount(oid, 10, "m1")  # 900
        f = self.crm.forecast()
        self.assertEqual(f["weighted"], 900 * 30 // 100)

    def test_forecast_no_log_entry(self):
        before = list(self.crm.log)
        self.crm.forecast()
        self.assertEqual(self.crm.log, before)


if __name__ == "__main__":
    unittest.main()
