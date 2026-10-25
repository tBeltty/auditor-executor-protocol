"""Spec lines 28-31 and 37-39: advance and transfer."""

import unittest

from crm import CRM

OPEN_STAGES = ("prospect", "proposal", "negotiation")


def one_rep_one_manager(rep_capacity=3):
    return CRM([
        {"id": "r1", "role": "rep", "capacity": rep_capacity},
        {"id": "m1", "role": "manager", "capacity": 9},
    ])


class Advancer(unittest.TestCase):
    def make_opp(self, amount=1000, crm=None, manager="m1"):
        crm = crm or one_rep_one_manager()
        self.crm = crm
        lead = crm.add_lead("a@corp.com", "Ann", "referral", manager)
        crm.qualify(lead, manager)
        return crm.convert(lead, amount, manager)


class TestAdvanceStages(Advancer):
    """Lines 28-30: stage order, "lost" from anywhere open, finals are final."""

    def test_full_order_prospect_to_won(self):
        opp = self.make_opp()
        for stage in ("proposal", "negotiation", "won"):
            self.crm.advance(opp, stage, "r1")
            self.assertEqual(self.crm.opps[opp]["stage"], stage)
        self.assertEqual(self.crm.log,
                         [("add_lead", "L1", "m1"), ("qualify", "L1", "m1"),
                          ("convert", "O1", "m1"), ("advance", "O1", "r1"),
                          ("advance", "O1", "r1"), ("advance", "O1", "r1")])

    def test_lost_is_allowed_from_every_open_stage(self):
        for stage in OPEN_STAGES:
            with self.subTest(stage=stage):
                crm = one_rep_one_manager()
                lead = crm.add_lead("a@corp.com", "Ann", "referral", "m1")
                crm.qualify(lead, "m1")
                opp = crm.convert(lead, 1000, "m1")
                # Walk prospect -> ... -> stage, then drop to "lost".
                for intermediate in OPEN_STAGES[1:OPEN_STAGES.index(stage) + 1]:
                    crm.advance(opp, intermediate, "r1")
                self.assertEqual(crm.opps[opp]["stage"], stage)
                crm.advance(opp, "lost", "r1")
                self.assertEqual(crm.opps[opp]["stage"], "lost")

    def test_staying_on_the_same_stage_is_not_the_next_stage(self):
        opp = self.make_opp()
        for stage in ("prospect",):
            with self.assertRaises(ValueError):
                self.crm.advance(opp, stage, "r1")

    def test_skipping_forward_is_rejected(self):
        opp = self.make_opp()
        for stage in ("negotiation", "won"):
            with self.subTest(stage=stage):
                with self.assertRaises(ValueError):
                    self.crm.advance(opp, stage, "r1")

    def test_moving_backwards_is_rejected(self):
        opp = self.make_opp()
        self.crm.advance(opp, "proposal", "r1")
        self.crm.advance(opp, "negotiation", "r1")
        for stage in ("prospect", "proposal"):
            with self.subTest(stage=stage):
                with self.assertRaises(ValueError):
                    self.crm.advance(opp, stage, "r1")
        self.assertEqual(self.crm.opps[opp]["stage"], "negotiation")

    def test_from_negotiation_only_won_or_lost(self):
        opp = self.make_opp()
        self.crm.advance(opp, "proposal", "r1")
        self.crm.advance(opp, "negotiation", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance(opp, "proposal", "r1")
        self.crm.advance(opp, "won", "r1")
        self.assertEqual(self.crm.opps[opp]["stage"], "won")

    def test_final_stages_cannot_advance_to_anything(self):
        for final in ("won", "lost"):
            with self.subTest(final=final):
                crm = one_rep_one_manager()
                lead = crm.add_lead("a@corp.com", "Ann", "referral", "m1")
                crm.qualify(lead, "m1")
                opp = crm.convert(lead, 1000, "m1")
                for stage in ("proposal", "negotiation", final):
                    crm.advance(opp, stage, "r1")
                for stage in ("prospect", "proposal", "negotiation", "won", "lost"):
                    with self.assertRaises(ValueError):
                        crm.advance(opp, stage, "r1")
                self.assertEqual(crm.opps[opp]["stage"], final)


class TestAdvanceChecks(Advancer):
    """Line 30 check order: exist -> stage known -> owner -> not final -> legal move."""

    def test_unknown_opp_raises_value_error(self):
        self.make_opp()
        for bad in ("O404", None, 3, ["O1"], b"O1"):
            with self.subTest(opp_id=bad):
                with self.assertRaises(ValueError):
                    self.crm.advance(bad, "proposal", "r1")

    def test_unknown_stage_raises_value_error(self):
        opp = self.make_opp()
        for stage in ("closed", "", None, 0, True, ["won"], "WON"):
            with self.subTest(stage=stage):
                with self.assertRaises(ValueError):
                    self.crm.advance(opp, stage, "r1")
        self.assertEqual(self.crm.opps[opp]["stage"], "prospect")

    def test_non_owner_rep_is_forbidden(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 1},
        ])
        lead = crm.add_lead("a@corp.com", "Ann", "referral", "m1")
        crm.qualify(lead, "m1")
        opp = crm.convert(lead, 1000, "m1")
        self.assertEqual(crm.opps[opp]["owner"], "r1")
        with self.assertRaises(PermissionError):
            crm.advance(opp, "proposal", "r2")

    def test_check_order_stage_known_before_ownership(self):
        """Invalid stage + no-permission actor -> ValueError (check 2 first)."""
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 1},
        ])
        lead = crm.add_lead("a@corp.com", "Ann", "referral", "m1")
        crm.qualify(lead, "m1")
        opp = crm.convert(lead, 1000, "m1")
        with self.assertRaises(ValueError):
            crm.advance(opp, "not-a-stage", "r2")

    def test_check_order_ownership_before_final_stage(self):
        """Final opportunity + non-owner actor -> PermissionError (check 3 first)."""
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 9},
        ])
        lead = crm.add_lead("a@corp.com", "Ann", "referral", "m1")
        crm.qualify(lead, "m1")
        opp = crm.convert(lead, 1000, "m1")
        for stage in ("proposal", "negotiation", "won"):
            crm.advance(opp, stage, "m1")
        self.assertEqual(crm.opps[opp]["stage"], "won")
        with self.assertRaises(PermissionError):
            crm.advance(opp, "lost", "r2")

    def test_check_order_legal_move_before_manager_rule(self):
        """Illegal move + big amount + rep actor -> ValueError (check 5 before 6)."""
        opp = self.make_opp(amount=60000)
        with self.assertRaises(ValueError):
            self.crm.advance(opp, "won", "r1")

    def test_winning_a_big_deal_needs_no_manager(self):
        """Line 30 check 6 only mentions negotiation."""
        opp = self.make_opp(amount=60000)
        self.crm.advance(opp, "proposal", "r1")
        self.crm.advance(opp, "lost", "r1")
        self.assertEqual(self.crm.opps[opp]["stage"], "lost")


class TestAdvanceNegotiationThreshold(Advancer):
    """Line 30 check 6: amount > 50000 to negotiation requires a manager."""

    def test_rep_may_take_50000_to_negotiation(self):
        """Exactly 50000 is not "greater than 50000"."""
        opp = self.make_opp(amount=50000)
        self.crm.advance(opp, "proposal", "r1")
        self.crm.advance(opp, "negotiation", "r1")
        self.assertEqual(self.crm.opps[opp]["stage"], "negotiation")

    def test_rep_is_forbidden_at_50001(self):
        """50001 > 50000: one unit above the threshold is a manager-only move."""
        opp = self.make_opp(amount=50001)
        self.crm.advance(opp, "proposal", "r1")
        with self.assertRaises(PermissionError):
            self.crm.advance(opp, "negotiation", "r1")
        self.assertEqual(self.crm.opps[opp]["stage"], "proposal")

    def test_manager_may_take_50001_to_negotiation(self):
        opp = self.make_opp(amount=50001)
        self.crm.advance(opp, "proposal", "m1")
        self.crm.advance(opp, "negotiation", "m1")
        self.assertEqual(self.crm.opps[opp]["stage"], "negotiation")

    def test_rep_may_take_a_larger_than_50000_deal_to_proposal(self):
        opp = self.make_opp(amount=50001)
        self.crm.advance(opp, "proposal", "r1")
        self.assertEqual(self.crm.opps[opp]["stage"], "proposal")

    def test_discount_below_the_threshold_lets_the_rep_advance(self):
        """Threshold is tested against the current amount, not the original."""
        opp = self.make_opp(amount=52000)
        self.crm.advance(opp, "proposal", "m1")
        self.crm.discount(opp, 5, "m1")
        self.assertEqual(self.crm.opps[opp]["amount"], 49400)
        self.crm.advance(opp, "negotiation", "r1")
        self.assertEqual(self.crm.opps[opp]["stage"], "negotiation")


class TestAdvanceFreesSlot(Advancer):
    """Line 31: a won/lost opportunity frees the owner's slot for queued leads."""

    def build(self, rep_capacity):
        """r1 carries one opportunity plus enough leads to be exactly full."""
        crm = CRM([{"id": "r1", "role": "rep", "capacity": rep_capacity},
                   {"id": "m1", "role": "manager", "capacity": 9}])
        self.crm = crm
        lead = crm.add_lead("own@corp.com", "Own", "referral", "m1")
        crm.qualify(lead, "m1")
        opp = crm.convert(lead, 1000, "m1")           # slot now held by the opp
        for i in range(rep_capacity - 1):             # fill the remaining slots
            filler = crm.add_lead("f%d@corp.com" % i, "F%d" % i, "referral", "m1")
            self.assertEqual(crm.leads[filler]["owner"], "r1")
        queued = [crm.add_lead("q%d@corp.com" % i, "Q%d" % i, "referral", "m1")
                  for i in range(3)]
        for q in queued:
            self.assertIsNone(crm.leads[q]["owner"])
        self.log_len = len(crm.log)
        return opp, queued

    def close(self, opp, final="won"):
        for stage in ("proposal", "negotiation"):
            self.crm.advance(opp, stage, "m1")
        self.crm.advance(opp, final, "m1")

    def test_won_assigns_oldest_waiting_lead_with_system_log(self):
        opp, queued = self.build(rep_capacity=1)
        self.close(opp)
        self.assertEqual(self.crm.leads[queued[0]]["owner"], "r1")
        self.assertEqual(self.crm.log[-1], ("assign", queued[0], "system"))
        self.assertEqual(len(self.crm.log), self.log_len + 3 + 1)
        self.assertIsNone(self.crm.leads[queued[1]]["owner"])

    def test_lost_also_frees_the_slot(self):
        opp, queued = self.build(rep_capacity=1)
        self.crm.advance(opp, "lost", "m1")
        self.assertEqual(self.crm.leads[queued[0]]["owner"], "r1")
        self.assertEqual(self.crm.log[-1], ("assign", queued[0], "system"))

    def test_non_final_advance_assigns_nothing(self):
        opp, queued = self.build(rep_capacity=1)
        self.crm.advance(opp, "proposal", "m1")
        for q in queued:
            self.assertIsNone(self.crm.leads[q]["owner"])
        self.assertNotIn("assign", [entry[0] for entry in self.crm.log])

    def test_drain_stops_at_capacity_not_through_the_whole_queue(self):
        """Line 31's loop is bounded by capacity: one freed slot releases one lead."""
        opp, queued = self.build(rep_capacity=2)
        self.close(opp)
        self.assertEqual(self.crm.leads[queued[0]]["owner"], "r1")
        self.assertIsNone(self.crm.leads[queued[1]]["owner"])
        self.assertIsNone(self.crm.leads[queued[2]]["owner"])
        self.assertEqual([e for e in self.crm.log if e[0] == "assign"],
                         [("assign", queued[0], "system")])

    def test_an_escaped_lead_is_never_assigned_twice(self):
        opp, queued = self.build(rep_capacity=1)
        self.close(opp)
        first_owner = self.crm.leads[queued[0]]["owner"]
        # The escaped lead becomes the next opportunity; closing it frees a slot for
        # the NEXT waiting lead, never a second assignment of the same one.
        self.crm.qualify(queued[0], "r1")
        opp2 = self.crm.convert(queued[0], 1000, "r1")
        self.crm.advance(opp2, "lost", "r1")
        self.assertEqual(self.crm.leads[queued[0]]["owner"], first_owner)
        self.assertEqual(self.crm.leads[queued[1]]["owner"], "r1")
        self.assertEqual([e[1] for e in self.crm.log if e[0] == "assign"],
                         [queued[0], queued[1]])

    def test_assign_entries_use_actor_system_and_never_the_caller(self):
        opp, queued = self.build(rep_capacity=1)
        self.close(opp, final="lost")
        assign = [e for e in self.crm.log if e[0] == "assign"]
        self.assertEqual(assign, [("assign", queued[0], "system")])

    def test_freed_slot_reopens_normal_assignment_after_the_queue(self):
        """After the queue drains, the next add_lead sees the rep's load again."""
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1},
                   {"id": "m1", "role": "manager", "capacity": 9}])
        self.crm = crm
        lead = crm.add_lead("a@corp.com", "Ann", "referral", "m1")
        crm.qualify(lead, "m1")
        opp = crm.convert(lead, 1000, "m1")
        queued = crm.add_lead("q@corp.com", "Q", "referral", "m1")
        self.assertIsNone(crm.leads[queued]["owner"])
        self.close(opp, final="won")
        self.assertEqual(crm.leads[queued]["owner"], "r1")
        third = crm.add_lead("t@corp.com", "T", "referral", "m1")
        self.assertIsNone(crm.leads[third]["owner"])  # r1 is full again


class TestTransfer(unittest.TestCase):
    """Lines 37-39: manager-only move of an open opportunity to another rep."""

    def setUp(self):
        self.crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 9},
        ])
        lead = self.crm.add_lead("a@corp.com", "Ann", "referral", "m1")
        self.crm.qualify(lead, "m1")
        self.opp = self.crm.convert(lead, 1000, "m1")
        self.assertEqual(self.crm.opps[self.opp]["owner"], "r1")

    def test_happy_path_changes_owner_and_logs(self):
        self.crm.transfer(self.opp, "r2", "m1")
        self.assertEqual(self.crm.opps[self.opp]["owner"], "r2")
        self.assertEqual(self.crm.log[-1], ("transfer", self.opp, "m1"))
        self.assertEqual(self.crm.leads["L1"]["owner"], "r1")

    def test_unknown_opp_raises_value_error(self):
        with self.assertRaises(ValueError):
            self.crm.transfer("O404", "r2", "m1")

    def test_non_manager_actor_is_forbidden_even_for_a_known_rep(self):
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.opp, "r2", "r1")

    def test_check_order_exists_before_manager_rule(self):
        with self.assertRaises(ValueError):
            self.crm.transfer("O404", "r2", "r1")

    def test_new_owner_must_be_a_known_rep(self):
        for bad in ("m1", "ghost", None, 3, ["r2"], b"r2"):
            with self.subTest(new_owner=bad):
                with self.assertRaises(ValueError):
                    self.crm.transfer(self.opp, bad, "m1")
        self.assertEqual(self.crm.opps[self.opp]["owner"], "r1")

    def test_new_owner_checked_before_final_stage(self):
        """Both raise ValueError; assert the final-stage case on a valid target."""
        self.crm.advance(self.opp, "proposal", "m1")
        self.crm.advance(self.opp, "negotiation", "m1")
        self.crm.advance(self.opp, "won", "m1")
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "r2", "m1")
        self.assertEqual(self.crm.opps[self.opp]["owner"], "r1")

    def test_new_owner_must_differ_from_current(self):
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "r1", "m1")

    def test_same_owner_checked_before_capacity(self):
        """r1 is at capacity 1, yet the self-transfer fails as "must differ"."""
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "r1", "m1")

    def test_new_owner_must_be_below_capacity(self):
        lead2 = self.crm.add_lead("b@corp.com", "Bob", "referral", "m1")
        self.crm.qualify(lead2, "m1")
        opp2 = self.crm.convert(lead2, 1000, "m1")
        self.assertEqual(self.crm.opps[opp2]["owner"], "r2")
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "r2", "m1")
        self.assertEqual(self.crm.opps[self.opp]["owner"], "r1")

    def test_source_at_capacity_does_not_block_the_transfer(self):
        """Line 38 check 6 tests the target's load, not the source's."""
        self.crm.transfer(self.opp, "r2", "m1")   # r1 full (cap 1), r2 has room
        self.assertEqual(self.crm.opps[self.opp]["owner"], "r2")
        # r1's slot is free again, so the next lead lands on r1, not on full r2.
        lead2 = self.crm.add_lead("b@corp.com", "Bob", "referral", "m1")
        self.assertEqual(self.crm.leads[lead2]["owner"], "r1")

    def test_successful_transfer_logs_no_assign(self):
        """A legal transfer means some rep had a free slot, so the queue is empty."""
        self.crm.transfer(self.opp, "r2", "m1")
        self.assertEqual([e for e in self.crm.log if e[0] == "assign"], [])
        self.assertEqual(self.crm.log[-1], ("transfer", self.opp, "m1"))

    def test_transfer_is_blocked_while_every_rep_is_full(self):
        """Lines 18/38/39 together: a waiting lead implies no legal transfer target."""
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 9},
        ])
        l1 = crm.add_lead("a@corp.com", "Ann", "referral", "m1")    # r1
        crm.add_lead("b@corp.com", "Bob", "referral", "m1")         # r2
        waiting = crm.add_lead("c@corp.com", "Cal", "referral", "m1")
        self.assertIsNone(crm.leads[waiting]["owner"])
        crm.qualify(l1, "m1")
        opp = crm.convert(l1, 1000, "m1")
        with self.assertRaises(ValueError):
            crm.transfer(opp, "r2", "m1")
        self.assertEqual(crm.opps[opp]["owner"], "r1")
        self.assertEqual(crm.leads[waiting]["owner"], None)
        self.assertNotIn("assign", [e[0] for e in crm.log])


if __name__ == "__main__":
    unittest.main()
