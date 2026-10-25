"""Unit tests for CRM.advance, including stage rules and slot freeing."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crm_test_support import add_lead, convert_lead, make_crm  # noqa: E402
from crm_test_support import walk_to_final  # noqa: E402,E501


class AdvanceStageRulesTests(unittest.TestCase):
    def test_happy_path_forward_moves_and_logging(self):
        crm = make_crm()
        _, opp_id = convert_lead(crm, 0, amount=500)
        crm.advance(opp_id, "proposal", "r1")
        self.assertEqual(crm.opps[opp_id]["stage"], "proposal")
        crm.advance(opp_id, "negotiation", "r1")
        self.assertEqual(crm.opps[opp_id]["stage"], "negotiation")
        crm.advance(opp_id, "won", "r1")
        self.assertEqual(crm.opps[opp_id]["stage"], "won")
        self.assertEqual(
            [entry for entry in crm.log if entry[0] == "advance"],
            [
                ("advance", opp_id, "r1"),
                ("advance", opp_id, "r1"),
                ("advance", opp_id, "r1"),
            ],
        )

    def test_lost_allowed_from_all_non_final_stages(self):
        crm = make_crm()
        prospect = convert_lead(crm, 0, 100)[1]     # owner r1
        proposal = convert_lead(crm, 1, 100)[1]     # owner r2
        negotiation = convert_lead(crm, 2, 100)[1]  # owner r3
        crm.advance(proposal, "proposal", "r2")
        crm.advance(negotiation, "proposal", "r3")
        crm.advance(negotiation, "negotiation", "r3")
        crm.advance(prospect, "lost", "r1")
        crm.advance(proposal, "lost", "r2")
        crm.advance(negotiation, "lost", "r3")
        self.assertEqual(crm.opps[prospect]["stage"], "lost")
        self.assertEqual(crm.opps[proposal]["stage"], "lost")
        self.assertEqual(crm.opps[negotiation]["stage"], "lost")

    def test_unknown_actor_checked_first(self):
        crm = make_crm()
        _, opp_id = convert_lead(crm, 0)
        for actor in ("ghost", 9, None):
            with self.subTest(actor=actor):
                with self.assertRaises(PermissionError):
                    crm.advance(opp_id, "sky-diving", actor)
        self.assertEqual(crm.log[-1], ("convert", opp_id, "m1"))

    def test_unknown_opportunity_raises_value_error(self):
        crm = make_crm()
        with self.assertRaises(ValueError):
            crm.advance("O404", "proposal", "m1")
        self.assertEqual(crm.log, [])

    def test_invalid_stage_checked_before_permission(self):
        crm = make_crm()
        _, opp_id = convert_lead(crm, 0)
        with self.assertRaises(ValueError):
            crm.advance(opp_id, "flying", "r2")  # r2 is not the owner
        self.assertEqual(crm.log[-1], ("convert", opp_id, "m1"))

    def test_owner_or_manager_permission(self):
        crm = make_crm()
        _, opp_id = convert_lead(crm, 0, 500)
        with self.assertRaises(PermissionError):
            crm.advance(opp_id, "proposal", "r2")
        self.assertEqual(crm.opps[opp_id]["stage"], "prospect")
        crm.advance(opp_id, "proposal", "m1")  # managers may act on any opp
        self.assertEqual(crm.opps[opp_id]["stage"], "proposal")

    def test_final_stage_current_is_rejected(self):
        crm = make_crm()
        won = convert_lead(crm, 0, 100)[1]     # owner r1
        lost = convert_lead(crm, 1, 100)[1]    # owner r2
        walk_to_final(crm, won, "r1")
        walk_to_final(crm, lost, "r2", final="lost")
        for opp_id, stage, owner in ((won, "proposal", "r1"),
                                     (won, "lost", "r1"),
                                     (lost, "proposal", "r2"),
                                     (lost, "prospect", "r2")):
            with self.subTest(opp=opp_id, stage=stage):
                log_before = list(crm.log)
                stage_before = crm.opps[opp_id]["stage"]
                with self.assertRaises(ValueError):
                    crm.advance(opp_id, stage, owner)
                self.assertEqual(crm.opps[opp_id]["stage"], stage_before)
                self.assertEqual(crm.log, log_before)

    def test_stage_skips_and_backwards_moves_are_rejected(self):
        crm = make_crm()
        opp_id = convert_lead(crm, 0, 500)[1]
        for target in ("negotiation", "won", "prospect"):
            with self.subTest(target=target):
                with self.assertRaises(ValueError):
                    crm.advance(opp_id, target, "r1")
        self.assertEqual(crm.opps[opp_id]["stage"], "prospect")
        crm.advance(opp_id, "proposal", "r1")
        with self.assertRaises(ValueError):
            crm.advance(opp_id, "won", "r1")       # proposal -> won skips 2
        with self.assertRaises(ValueError):
            crm.advance(opp_id, "prospect", "r1")  # no backwards moves
        self.assertEqual(crm.opps[opp_id]["stage"], "proposal")


class AdvanceAmountRulesTests(unittest.TestCase):
    def test_rep_cannot_move_over_50000_to_negotiation(self):
        crm = make_crm()
        _, opp_id = convert_lead(crm, 0, amount=60000)
        crm.advance(opp_id, "proposal", "r1")
        with self.assertRaises(PermissionError):
            crm.advance(opp_id, "negotiation", "r1")
        self.assertEqual(crm.opps[opp_id]["stage"], "proposal")
        crm.advance(opp_id, "negotiation", "m1")  # manager is allowed
        self.assertEqual(crm.opps[opp_id]["stage"], "negotiation")

    def test_exactly_50000_is_allowed_for_a_rep(self):
        crm = make_crm()
        _, opp_id = convert_lead(crm, 0, amount=50000)
        crm.advance(opp_id, "proposal", "r1")
        crm.advance(opp_id, "negotiation", "r1")
        self.assertEqual(crm.opps[opp_id]["stage"], "negotiation")

    def test_adjacency_is_checked_before_the_manager_rule(self):
        # From prospect, negotiation is not the next stage, so check 5 fails
        # with ValueError even though a rep would also lack permission (6).
        crm = make_crm()
        _, opp_id = convert_lead(crm, 0, amount=60000)
        with self.assertRaises(ValueError):
            crm.advance(opp_id, "negotiation", "r1")
        self.assertEqual(crm.opps[opp_id]["stage"], "prospect")


class AdvanceSlotFreeingTests(unittest.TestCase):
    def _crm_with_waiting_lead(self):
        """r1 cap1 holds the only opp; r2 is absent so leads queue up.

        r1: L1 (converted -> O1), L2 waiting.
        """
        crm = make_crm([
            {"id": "r1", "role": "rep", "capacity": 2},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        lead1 = add_lead(crm, 0)      # -> r1 (load 1)
        lead2 = add_lead(crm, 1)      # -> r1 (load 2)
        crm.qualify(lead1, "r1")
        opp_id = crm.convert(lead1, 100, "r1")   # r1 load: L2 + O1 = 2
        lead3 = add_lead(crm, 2)      # r1 is full -> waiting, owner None
        self.assertIsNone(crm.leads[lead3]["owner"])
        return crm, opp_id, lead3

    def test_won_frees_the_owners_slot_and_assigns_oldest_waiting_lead(self):
        crm, opp_id, waiting = self._crm_with_waiting_lead()
        walk_to_final(crm, opp_id, "r1", final="won")
        # r1's load drops to 1 (L2), below capacity 2 -> L3 gets assigned.
        self.assertIn(("advance", opp_id, "r1"), crm.log)
        self.assertEqual(crm.leads[waiting]["owner"], "r1")
        self.assertEqual(crm.leads[waiting]["status"], "new")
        self.assertEqual(crm.log[-1], ("assign", waiting, "system"))

    def test_lost_frees_the_owners_slot_too(self):
        crm, opp_id, waiting = self._crm_with_waiting_lead()
        walk_to_final(crm, opp_id, "r1", final="lost")
        self.assertEqual(crm.leads[waiting]["owner"], "r1")
        self.assertEqual(crm.log[-1], ("assign", waiting, "system"))

    def test_non_final_advance_does_not_free_slots(self):
        crm, opp_id, waiting = self._crm_with_waiting_lead()
        crm.advance(opp_id, "proposal", "r1")
        self.assertIsNone(crm.leads[waiting]["owner"])
        self.assertEqual(
            [entry[0] for entry in crm.log],
            ["add_lead", "add_lead", "qualify", "convert", "add_lead",
             "advance"],
        )

    def test_assignment_picks_fifo_and_only_until_capacity(self):
        # r1 cap 3, holds L1 (converted to O1), L2, L3; L4 waits.
        crm = make_crm([
            {"id": "r1", "role": "rep", "capacity": 4},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        lead1 = add_lead(crm, 0)
        lead2 = add_lead(crm, 1)
        lead3 = add_lead(crm, 2)
        lead4 = add_lead(crm, 3)  # r1 load 3 < 4 -> owned, no waiting yet
        lead5 = add_lead(crm, 4)  # r1 load 4 -> waiting
        self.assertIsNone(crm.leads[lead5]["owner"])
        crm.qualify(lead1, "r1")
        opp_id = crm.convert(lead1, 100, "r1")  # load stays 4 (L2..L4, O1)
        walk_to_final(crm, opp_id, "r1", final="won")  # load 3 -> assign L5
        self.assertEqual(crm.leads[lead5]["owner"], "r1")
        self.assertEqual(crm.leads[lead4]["owner"], "r1")
        assigns = [entry for entry in crm.log if entry[0] == "assign"]
        self.assertEqual(assigns, [("assign", lead5, "system")])


if __name__ == "__main__":
    unittest.main()
