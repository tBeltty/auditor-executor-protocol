"""Tests for CRM.advance: stage order, finality, the negotiation gate, slot freeing."""

import unittest

from support import add, converted, lose, make_crm, qualified, snapshot, win


class TestAdvanceTransitions(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        self.opp = converted(self.crm, "a@b.com", 1000)
        self.assertEqual(self.crm.opps[self.opp]["owner"], "r1")

    def test_happy_full_path_to_won(self):
        c = self.crm
        c.advance(self.opp, "proposal", "r1")
        c.advance(self.opp, "negotiation", "r1")  # amount 1000: no manager needed
        c.advance(self.opp, "won", "r1")
        self.assertEqual(c.opps[self.opp]["stage"], "won")
        self.assertEqual(
            c.log[-3:],
            [
                ("advance", "O1", "r1"),
                ("advance", "O1", "r1"),
                ("advance", "O1", "r1"),
            ],
        )

    def test_lost_allowed_from_each_non_final_stage(self):
        for stage in ("prospect", "proposal", "negotiation"):
            with self.subTest(stage=stage):
                c = make_crm()
                opp = converted(c, stage + "@b.com", 1000)
                if stage != "prospect":
                    c.advance(opp, "proposal", "m1")
                if stage == "negotiation":
                    c.advance(opp, "negotiation", "m1")
                c.advance(opp, "lost", "m1")
                self.assertEqual(c.opps[opp]["stage"], "lost")

    def test_manager_may_act_on_rep_owned_opportunity(self):
        self.crm.advance(self.opp, "proposal", "m1")
        self.assertEqual(self.crm.opps[self.opp]["stage"], "proposal")
        self.assertEqual(self.crm.log[-1], ("advance", "O1", "m1"))

    def test_invalid_stage_value_error(self):
        for bad in ("won ", "WON", "", None, 5, "closed"):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    self.crm.advance(self.opp, bad, "r1")

    def test_cannot_skip_stages(self):
        for bad in ("negotiation", "won"):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    self.crm.advance(self.opp, bad, "r1")  # from prospect
        c = make_crm()
        opp = converted(c, "a@b.com", 1000)
        c.advance(opp, "proposal", "r1")
        with self.assertRaises(ValueError):
            c.advance(opp, "won", "r1")  # must pass negotiation

    def test_same_stage_is_not_the_immediate_next(self):
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "prospect", "r1")

    def test_final_stages_are_final(self):
        win(self.crm, self.opp)  # prospect -> proposal -> negotiation -> won
        before = snapshot(self.crm)
        for stage in ("prospect", "proposal", "negotiation", "won", "lost"):
            with self.subTest(stage=stage):
                with self.assertRaises(ValueError):
                    self.crm.advance(self.opp, stage, "m1")
        self.assertEqual(snapshot(self.crm), before)

    def test_other_rep_permission_error(self):
        with self.assertRaises(PermissionError):
            self.crm.advance(self.opp, "proposal", "r2")
        self.assertEqual(self.crm.opps[self.opp]["stage"], "prospect")

    def test_unknown_actor_first(self):
        with self.assertRaises(PermissionError):
            self.crm.advance("O404", "nonsense", "ghost")

    def test_missing_opp_value_error(self):
        with self.assertRaises(ValueError):
            self.crm.advance("O404", "proposal", "m1")

    def test_stage_check_before_permission_check(self):
        # invalid stage from a forbidden actor -> ValueError (stage is check 2)
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "bogus", "r2")

    def test_permission_check_before_finality_check(self):
        win(self.crm, self.opp)  # now final
        # final opp touched by the wrong rep -> PermissionError (check 3 before 4)
        with self.assertRaises(PermissionError):
            self.crm.advance(self.opp, "proposal", "r2")


    def test_bad_stage_move_before_negotiation_gate(self):
        # from prospect, "won" is an illegal move (check 5) even though the
        # negotiation gate (check 6) could never apply: use big amount + rep
        c = make_crm()
        opp = converted(c, "a@b.com", 60000)
        with self.assertRaises(ValueError):
            c.advance(opp, "won", "r1")

    def test_failed_advance_appends_nothing(self):
        before = snapshot(self.crm)
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "won", "r1")
        self.assertEqual(snapshot(self.crm), before)


class TestNegotiationGate(unittest.TestCase):
    def test_over_50000_requires_manager(self):
        c = make_crm()
        opp = converted(c, "a@b.com", 50001)
        c.advance(opp, "proposal", "r1")
        with self.assertRaises(PermissionError):
            c.advance(opp, "negotiation", "r1")
        self.assertEqual(c.opps[opp]["stage"], "proposal")
        c.advance(opp, "negotiation", "m1")
        self.assertEqual(c.opps[opp]["stage"], "negotiation")

    def test_exactly_50000_allowed_for_rep(self):
        c = make_crm()
        opp = converted(c, "a@b.com", 50000)
        c.advance(opp, "proposal", "r1")
        c.advance(opp, "negotiation", "r1")
        self.assertEqual(c.opps[opp]["stage"], "negotiation")

    def test_gate_uses_current_amount_after_discount(self):
        c = make_crm()
        opp = converted(c, "a@b.com", 60000)
        c.advance(opp, "proposal", "r1")
        with self.assertRaises(PermissionError):
            c.advance(opp, "negotiation", "r1")
        c.discount(opp, 20, "m1")  # 60000 -> 48000
        self.assertEqual(c.opps[opp]["amount"], 48000)
        c.advance(opp, "negotiation", "r1")
        self.assertEqual(c.opps[opp]["stage"], "negotiation")

    def test_gate_only_applies_to_negotiation(self):
        c = make_crm()
        opp = converted(c, "a@b.com", 999999)
        c.advance(opp, "proposal", "r1")  # big amount, but not negotiation
        with self.assertRaises(ValueError):
            c.advance(opp, "won", "r1")  # still an illegal move, not a permission issue
        c.advance(opp, "lost", "r1")
        self.assertEqual(c.opps[opp]["stage"], "lost")


class TestSlotFreeing(unittest.TestCase):
    def test_win_drains_oldest_waiting_lead_to_the_freed_rep(self):
        c = make_crm()
        l1 = qualified(c, "1@b.com")  # owner r1 (tie load 0, "r1" < "r2")
        opp = c.convert(l1, 1000, "m1")
        add(c, "2@b.com")  # r1: O1 + L2 -> load 2 == capacity
        add(c, "3@b.com")  # r2 takes this -> load 1 == capacity
        l4 = add(c, "4@b.com")  # every rep full -> queue
        self.assertIsNone(c.leads[l4]["owner"])
        win(c, opp)
        self.assertEqual(c.leads[l4]["owner"], "r1")
        self.assertEqual(
            c.log[-2:],
            [("advance", "O1", "m1"), ("assign", "L4", "system")],
        )

    def test_loss_also_frees_the_slot(self):
        c = make_crm()
        l1 = qualified(c, "1@b.com")
        opp = c.convert(l1, 1000, "m1")
        add(c, "2@b.com")  # r1 full
        add(c, "3@b.com")  # r2 full
        l4 = add(c, "4@b.com")
        self.assertIsNone(c.leads[l4]["owner"])
        lose(c, opp)
        self.assertEqual(c.leads[l4]["owner"], "r1")
        self.assertEqual(c.log[-1], ("assign", "L4", "system"))


    def test_queue_drains_in_fifo_order_until_capacity(self):
        reps = [
            {"id": "solo", "role": "rep", "capacity": 3},
            {"id": "m1", "role": "manager", "capacity": 0},
        ]
        c = make_crm(reps)
        owned = [qualified(c, "%d@b.com" % i) for i in range(1, 4)]
        self.assertTrue(all(c.leads[x]["owner"] == "solo" for x in owned))
        queued = [add(c, "%d@b.com" % i) for i in range(4, 8)]
        self.assertTrue(all(c.leads[x]["owner"] is None for x in queued))
        opp = c.convert(owned[0], 500, "m1")  # solo still at 3 (opp replaces the lead)
        win(c, opp)  # frees exactly one slot
        self.assertEqual(c.leads[queued[0]]["owner"], "solo")
        self.assertEqual(c.leads[queued[1]]["owner"], None)
        self.assertEqual(c.log[-2:], [("advance", "O1", "m1"), ("assign", "L4", "system")])
        self.assertEqual(c.leads[queued[0]]["status"], "new")

    def test_assign_goes_to_freed_rep_not_to_the_lowest_load_rep(self):
        reps = [
            {"id": "a2", "role": "rep", "capacity": 1},
            {"id": "z1", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 0},
        ]
        c = make_crm(reps)
        l1 = add(c, "1@b.com", source="referral")  # tie load 0 -> "a2" < "z1"
        self.assertEqual(c.leads[l1]["owner"], "a2")
        c.qualify(l1, "m1")
        l2 = add(c, "2@b.com", source="referral")
        self.assertEqual(c.leads[l2]["owner"], "z1")
        c.qualify(l2, "m1")
        l3 = add(c, "3@b.com")  # both reps full -> queue
        self.assertIsNone(c.leads[l3]["owner"])
        opp = c.convert(l2, 400, "m1")  # z1 still full via the open opp
        win(c, opp)  # frees z1; a2 is still busy with L1
        self.assertEqual(c.leads[l3]["owner"], "z1")
        self.assertEqual(c.leads[l3]["status"], "new")

    def test_no_assigns_when_queue_empty(self):
        c = make_crm()
        l1 = qualified(c, "1@b.com")
        opp = c.convert(l1, 100, "m1")
        win(c, opp)
        self.assertEqual(c.log[-1], ("advance", "O1", "m1"))
        self.assertNotIn("assign", [e[0] for e in c.log])

    def test_qualified_queued_lead_can_be_assigned(self):
        reps = [
            {"id": "solo", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 0},
        ]
        c = make_crm(reps)
        l1 = qualified(c, "1@b.com")
        opp = c.convert(l1, 100, "m1")
        l2 = add(c, "2@b.com", source="referral")
        c.qualify(l2, "m1")  # manager qualifies an ownerless queued lead
        lose(c, opp)
        self.assertEqual(c.leads[l2]["owner"], "solo")
        self.assertEqual(c.leads[l2]["status"], "qualified")
        self.assertEqual(c.log[-2:], [("advance", "O1", "m1"), ("assign", "L2", "system")])

    def test_assign_stops_when_capacity_reached_even_with_leads_left(self):
        # capacity 2, one open opp: win frees 2 slots worth? no - load drops by 1
        reps = [
            {"id": "solo", "role": "rep", "capacity": 2},
            {"id": "m1", "role": "manager", "capacity": 0},
        ]
        c = make_crm(reps)
        l1 = qualified(c, "1@b.com")
        l2 = add(c, "2@b.com")  # solo load 2 -> at capacity
        self.assertEqual(c.leads[l2]["owner"], "solo")
        l3 = add(c, "3@b.com")
        self.assertIsNone(c.leads[l3]["owner"])
        opp = c.convert(l1, 700, "m1")  # still load 2 (opp replaces lead)
        lose(c, opp)  # load 1 -> exactly one assign
        self.assertEqual(c.leads[l3]["owner"], "solo")
        self.assertEqual([e for e in c.log if e[0] == "assign"], [("assign", "L3", "system")])



if __name__ == "__main__":
    unittest.main()
