"""Unit tests for the opportunity pipeline: advance, discount and transfer."""

import unittest

from crm import CRM


def make_crm(reps=None):
    if reps is None:
        reps = [
            {"id": "r1", "role": "rep", "capacity": 2},
            {"id": "r2", "role": "rep", "capacity": 2},
            {"id": "m1", "role": "manager", "capacity": 10},
        ]
    return CRM(reps)


def new_deal(crm, amount=1000, email="deal@corp.com"):
    lead_id = crm.add_lead(email, "Deal", "referral", "r1")
    crm.qualify(lead_id, "m1")
    return lead_id, crm.convert(lead_id, amount, "m1")


def force_stage(crm, opp_id, stage, actor="m1"):
    order = ["prospect", "proposal", "negotiation", "won"]
    while crm.opps[opp_id]["stage"] != stage:
        current = order.index(crm.opps[opp_id]["stage"])
        crm.advance(opp_id, order[current + 1], actor)


class AdvanceTests(unittest.TestCase):
    def test_walks_the_stage_order(self):
        crm = make_crm()
        _, opp_id = new_deal(crm)
        for stage in ("proposal", "negotiation", "won"):
            crm.advance(opp_id, stage, "m1")
            self.assertEqual(crm.opps[opp_id]["stage"], stage)
        self.assertEqual(crm.log[-3:], [("advance", opp_id, "m1")] * 3)

    def test_lost_from_prospect(self):
        crm = make_crm()
        _, opp_id = new_deal(crm)
        crm.advance(opp_id, "lost", "m1")
        self.assertEqual(crm.opps[opp_id]["stage"], "lost")
        self.assertEqual(crm.log[-1], ("advance", opp_id, "m1"))

    def test_lost_from_proposal(self):
        crm = make_crm()
        _, opp_id = new_deal(crm)
        crm.advance(opp_id, "proposal", "m1")
        crm.advance(opp_id, "lost", "m1")
        self.assertEqual(crm.opps[opp_id]["stage"], "lost")

    def test_lost_from_negotiation(self):
        crm = make_crm()
        _, opp_id = new_deal(crm)
        crm.advance(opp_id, "proposal", "m1")
        crm.advance(opp_id, "negotiation", "m1")
        crm.advance(opp_id, "lost", "m1")
        self.assertEqual(crm.opps[opp_id]["stage"], "lost")

    def test_unknown_stage_rejected(self):
        crm = make_crm()
        _, opp_id = new_deal(crm)
        for stage in ("closed", "Won", None, 5, []):
            with self.subTest(stage=stage):
                with self.assertRaises(ValueError):
                    crm.advance(opp_id, stage, "m1")
        self.assertEqual(crm.opps[opp_id]["stage"], "prospect")

    def test_unknown_opportunity_rejected(self):
        crm = make_crm()
        with self.assertRaises(ValueError):
            crm.advance("O99", "proposal", "m1")

    def test_unknown_actor_checked_before_opportunity(self):
        crm = make_crm()
        with self.assertRaises(PermissionError):
            crm.advance("O99", "proposal", "ghost")

    def test_owner_can_advance(self):
        crm = make_crm()
        _, opp_id = new_deal(crm)
        owner = crm.opps[opp_id]["owner"]
        crm.advance(opp_id, "proposal", owner)
        self.assertEqual(crm.opps[opp_id]["stage"], "proposal")
        self.assertEqual(crm.log[-1], ("advance", opp_id, owner))

    def test_other_rep_is_denied(self):
        crm = make_crm()
        _, opp_id = new_deal(crm)
        with self.assertRaises(PermissionError):
            crm.advance(opp_id, "proposal", "r2")
        self.assertEqual(crm.opps[opp_id]["stage"], "prospect")

    def test_final_opportunity_cannot_advance(self):
        crm = make_crm()
        _, opp_id = new_deal(crm)
        force_stage(crm, opp_id, "won")
        with self.assertRaises(ValueError):
            crm.advance(opp_id, "lost", "m1")
        self.assertEqual(crm.opps[opp_id]["stage"], "won")

    def test_requires_immediate_next_stage(self):
        cases = [
            ("prospect", "negotiation"),
            ("prospect", "won"),
            ("proposal", "won"),
            ("proposal", "prospect"),
            ("proposal", "proposal"),
            ("negotiation", "proposal"),
        ]
        for start, target in cases:
            with self.subTest(start=start, target=target):
                crm = make_crm()
                _, opp_id = new_deal(crm)
                force_stage(crm, opp_id, start)
                with self.assertRaises(ValueError):
                    crm.advance(opp_id, target, "m1")
                self.assertEqual(crm.opps[opp_id]["stage"], start)

    def test_negotiation_above_50000_needs_manager(self):
        crm = make_crm()
        _, opp_id = new_deal(crm, amount=50001)
        owner = crm.opps[opp_id]["owner"]
        crm.advance(opp_id, "proposal", owner)
        with self.assertRaises(PermissionError):
            crm.advance(opp_id, "negotiation", owner)
        self.assertEqual(crm.opps[opp_id]["stage"], "proposal")
        crm.advance(opp_id, "negotiation", "m1")
        self.assertEqual(crm.opps[opp_id]["stage"], "negotiation")

    def test_negotiation_at_exactly_50000_allowed_for_owner(self):
        crm = make_crm()
        _, opp_id = new_deal(crm, amount=50000)
        owner = crm.opps[opp_id]["owner"]
        crm.advance(opp_id, "proposal", owner)
        crm.advance(opp_id, "negotiation", owner)
        self.assertEqual(crm.opps[opp_id]["stage"], "negotiation")

    def test_win_does_not_need_manager_for_large_amount(self):
        crm = make_crm()
        _, opp_id = new_deal(crm, amount=60000)
        owner = crm.opps[opp_id]["owner"]
        force_stage(crm, opp_id, "negotiation")
        crm.advance(opp_id, "won", owner)
        self.assertEqual(crm.opps[opp_id]["stage"], "won")

    def test_win_frees_slot_and_assigns_oldest_waiting_lead(self):
        crm = make_crm(
            [
                {"id": "r1", "role": "rep", "capacity": 1},
                {"id": "r2", "role": "rep", "capacity": 1},
                {"id": "m1", "role": "manager", "capacity": 5},
            ]
        )
        l1 = crm.add_lead("a@corp.com", "A", "referral", "m1")
        l2 = crm.add_lead("b@corp.com", "B", "referral", "m1")
        l3 = crm.add_lead("c@corp.com", "C", "referral", "m1")
        l4 = crm.add_lead("d@corp.com", "D", "referral", "m1")
        crm.qualify(l1, "m1")
        opp_id = crm.convert(l1, 900, "m1")
        crm.advance(opp_id, "proposal", "m1")
        crm.advance(opp_id, "negotiation", "m1")
        log_len = len(crm.log)
        crm.advance(opp_id, "won", "m1")
        self.assertEqual(
            crm.log[log_len:],
            [("advance", opp_id, "m1"), ("assign", l3, "system")],
        )
        self.assertEqual(crm.leads[l3]["owner"], "r1")
        self.assertIsNone(crm.leads[l4]["owner"])
        self.assertEqual(crm.leads[l2]["owner"], "r2")

    def test_lost_frees_slot_too(self):
        crm = make_crm(
            [
                {"id": "r1", "role": "rep", "capacity": 1},
                {"id": "r2", "role": "rep", "capacity": 1},
                {"id": "m1", "role": "manager", "capacity": 5},
            ]
        )
        l1 = crm.add_lead("a@corp.com", "A", "referral", "m1")
        crm.add_lead("b@corp.com", "B", "referral", "m1")
        waiting = crm.add_lead("c@corp.com", "C", "referral", "m1")
        crm.qualify(l1, "m1")
        opp_id = crm.convert(l1, 900, "m1")
        crm.advance(opp_id, "lost", "m1")
        self.assertEqual(crm.leads[waiting]["owner"], "r1")
        self.assertEqual(crm.log[-1], ("assign", waiting, "system"))

    def test_win_leaves_queue_when_owner_still_at_capacity(self):
        crm = make_crm(
            [
                {"id": "r1", "role": "rep", "capacity": 2},
                {"id": "r2", "role": "rep", "capacity": 1},
                {"id": "m1", "role": "manager", "capacity": 5},
            ]
        )
        l1 = crm.add_lead("a@corp.com", "A", "referral", "m1")
        crm.add_lead("b@corp.com", "B", "referral", "m1")
        crm.add_lead("c@corp.com", "C", "referral", "m1")
        l4 = crm.add_lead("d@corp.com", "D", "referral", "m1")
        l5 = crm.add_lead("e@corp.com", "E", "referral", "m1")
        self.assertIsNone(crm.leads[l4]["owner"])
        self.assertIsNone(crm.leads[l5]["owner"])
        crm.qualify(l1, "m1")
        opp_id = crm.convert(l1, 900, "m1")
        force_stage(crm, opp_id, "won")
        self.assertEqual(crm.leads[l4]["owner"], "r1")
        self.assertIsNone(crm.leads[l5]["owner"])
        self.assertEqual(
            crm.log[-2:],
            [("advance", opp_id, "m1"), ("assign", l4, "system")],
        )

    def test_win_without_waiting_leads_does_not_assign(self):
        crm = make_crm()
        _, opp_id = new_deal(crm)
        force_stage(crm, opp_id, "won")
        self.assertEqual(crm.log[-1], ("advance", opp_id, "m1"))
        self.assertNotIn("assign", [entry[0] for entry in crm.log])


class DiscountTests(unittest.TestCase):
    def test_manager_can_discount_30_percent(self):
        crm = make_crm()
        _, opp_id = new_deal(crm, amount=100000)
        crm.discount(opp_id, 30, "m1")
        self.assertEqual(crm.opps[opp_id]["amount"], 70000)
        self.assertEqual(crm.opps[opp_id]["original_amount"], 100000)
        self.assertEqual(crm.log[-1], ("discount", opp_id, "m1"))

    def test_owner_rep_is_limited_to_10_percent(self):
        crm = make_crm()
        _, opp_id = new_deal(crm)
        owner = crm.opps[opp_id]["owner"]
        crm.discount(opp_id, 10, owner)
        self.assertEqual(crm.opps[opp_id]["amount"], 900)
        with self.assertRaises(PermissionError):
            crm.discount(opp_id, 11, owner)
        self.assertEqual(crm.opps[opp_id]["amount"], 900)

    def test_pct_validation(self):
        crm = make_crm()
        _, opp_id = new_deal(crm)
        for pct in (0, 31, -1, True, False, 5.0, "5", None, [5]):
            with self.subTest(pct=pct):
                with self.assertRaises(ValueError):
                    crm.discount(opp_id, pct, "m1")
        self.assertEqual(crm.opps[opp_id]["amount"], 1000)

    def test_pct_checked_before_permission(self):
        crm = make_crm()
        _, opp_id = new_deal(crm)
        with self.assertRaises(ValueError):
            crm.discount(opp_id, 0, "r2")

    def test_other_rep_is_denied(self):
        crm = make_crm()
        _, opp_id = new_deal(crm)
        with self.assertRaises(PermissionError):
            crm.discount(opp_id, 5, "r2")
        self.assertEqual(crm.opps[opp_id]["amount"], 1000)

    def test_final_stage_rejected(self):
        crm = make_crm()
        _, opp_id = new_deal(crm)
        force_stage(crm, opp_id, "won")
        with self.assertRaises(ValueError):
            crm.discount(opp_id, 5, "m1")

    def test_final_stage_checked_before_rep_limit(self):
        crm = make_crm()
        _, opp_id = new_deal(crm)
        owner = crm.opps[opp_id]["owner"]
        force_stage(crm, opp_id, "won")
        with self.assertRaises(ValueError):
            crm.discount(opp_id, 20, owner)

    def test_cumulative_discount_capped_at_30_percent(self):
        crm = make_crm()
        _, opp_id = new_deal(crm, amount=1000)
        for _ in range(3):
            crm.discount(opp_id, 10, "m1")
        self.assertEqual(crm.opps[opp_id]["amount"], 729)
        with self.assertRaises(ValueError):
            crm.discount(opp_id, 10, "m1")
        self.assertEqual(crm.opps[opp_id]["amount"], 729)

    def test_new_amount_uses_floor_division(self):
        crm = make_crm()
        _, opp_id = new_deal(crm, amount=1010)
        crm.discount(opp_id, 10, "m1")
        self.assertEqual(crm.opps[opp_id]["amount"], 909)

    def test_unknown_opportunity_rejected(self):
        crm = make_crm()
        with self.assertRaises(ValueError):
            crm.discount("O99", 5, "m1")

    def test_unknown_actor_checked_before_opportunity(self):
        crm = make_crm()
        with self.assertRaises(PermissionError):
            crm.discount("O99", 5, "ghost")

    def test_discount_keeps_stage_and_original_amount(self):
        crm = make_crm()
        _, opp_id = new_deal(crm, amount=5000)
        crm.advance(opp_id, "proposal", "m1")
        crm.discount(opp_id, 20, "m1")
        self.assertEqual(crm.opps[opp_id]["stage"], "proposal")
        self.assertEqual(crm.opps[opp_id]["original_amount"], 5000)
        self.assertEqual(crm.opps[opp_id]["amount"], 4000)


class TransferTests(unittest.TestCase):
    def test_manager_transfers_opportunity(self):
        crm = make_crm()
        _, opp_id = new_deal(crm)
        owner = crm.opps[opp_id]["owner"]
        self.assertEqual(owner, "r1")
        crm.transfer(opp_id, "r2", "m1")
        self.assertEqual(crm.opps[opp_id]["owner"], "r2")
        self.assertEqual(crm.log[-1], ("transfer", opp_id, "m1"))

    def test_non_manager_cannot_transfer(self):
        crm = make_crm()
        _, opp_id = new_deal(crm)
        with self.assertRaises(PermissionError):
            crm.transfer(opp_id, "r2", "r1")
        self.assertEqual(crm.opps[opp_id]["owner"], "r1")

    def test_unknown_opportunity_rejected(self):
        crm = make_crm()
        with self.assertRaises(ValueError):
            crm.transfer("O99", "r2", "m1")

    def test_unknown_actor_checked_before_opportunity(self):
        crm = make_crm()
        with self.assertRaises(PermissionError):
            crm.transfer("O99", "nobody", "ghost")

    def test_new_owner_must_be_known(self):
        crm = make_crm()
        _, opp_id = new_deal(crm)
        with self.assertRaises(ValueError):
            crm.transfer(opp_id, "nobody", "m1")

    def test_new_owner_must_be_a_rep(self):
        crm = make_crm(
            [
                {"id": "r1", "role": "rep", "capacity": 2},
                {"id": "m1", "role": "manager", "capacity": 10},
                {"id": "m2", "role": "manager", "capacity": 10},
            ]
        )
        _, opp_id = new_deal(crm)
        with self.assertRaises(ValueError):
            crm.transfer(opp_id, "m1", "m2")
        with self.assertRaises(ValueError):
            crm.transfer(opp_id, "m2", "m1")

    def test_final_stage_rejected(self):
        crm = make_crm()
        _, opp_id = new_deal(crm)
        force_stage(crm, opp_id, "won")
        with self.assertRaises(ValueError):
            crm.transfer(opp_id, "r2", "m1")
        self.assertEqual(crm.opps[opp_id]["owner"], "r1")

    def test_same_owner_rejected(self):
        crm = make_crm()
        _, opp_id = new_deal(crm)
        with self.assertRaises(ValueError):
            crm.transfer(opp_id, "r1", "m1")
        self.assertEqual(crm.opps[opp_id]["owner"], "r1")

    def test_new_owner_at_capacity_rejected(self):
        crm = make_crm(
            [
                {"id": "r1", "role": "rep", "capacity": 2},
                {"id": "r2", "role": "rep", "capacity": 1},
                {"id": "m1", "role": "manager", "capacity": 5},
            ]
        )
        l1 = crm.add_lead("a@corp.com", "A", "referral", "m1")
        crm.add_lead("b@corp.com", "B", "referral", "m1")
        crm.qualify(l1, "m1")
        opp_id = crm.convert(l1, 1000, "m1")
        with self.assertRaises(ValueError):
            crm.transfer(opp_id, "r2", "m1")
        self.assertEqual(crm.opps[opp_id]["owner"], "r1")

    def test_transfer_preserves_amount_and_stage(self):
        crm = make_crm()
        _, opp_id = new_deal(crm, amount=8000)
        crm.advance(opp_id, "proposal", "m1")
        crm.discount(opp_id, 10, "m1")
        crm.transfer(opp_id, "r2", "m1")
        self.assertEqual(crm.opps[opp_id]["amount"], 7200)
        self.assertEqual(crm.opps[opp_id]["stage"], "proposal")


if __name__ == "__main__":
    unittest.main()
