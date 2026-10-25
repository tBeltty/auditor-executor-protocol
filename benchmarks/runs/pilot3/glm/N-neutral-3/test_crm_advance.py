"""Tests for CRM.advance: stage order, permissions, slot freeing."""

import copy
import unittest

from crm import CRM


def make_crm():
    return CRM([
        {"id": "r1", "role": "rep", "capacity": 2},
        {"id": "r2", "role": "rep", "capacity": 2},
        {"id": "m1", "role": "manager", "capacity": 0},
    ])


def make_opp(crm, email, amount):
    """Create a qualified lead and convert it; returns (opp_id, owner)."""
    lead = crm.add_lead(email, email, "referral", "m1")
    crm.qualify(lead, "m1")
    opp = crm.convert(lead, amount, "m1")
    return opp, crm.leads[lead]["owner"]


def walk_to_won(crm, opp, owner):
    crm.advance(opp, "proposal", owner)
    crm.advance(opp, "negotiation", owner)
    crm.advance(opp, "won", owner)


class TestAdvance(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        self.opp, self.owner = make_opp(self.crm, "h@acme.io", 1000)  # r1
        self.base_log_len = len(self.crm.log)

    def test_owner_is_r1(self):
        self.assertEqual(self.owner, "r1")

    def test_happy_path_through_all_stages(self):
        walk_to_won(self.crm, self.opp, self.owner)
        self.assertEqual(self.crm.opps[self.opp]["stage"], "won")
        self.assertEqual(self.crm.log[-3:], [
            ("advance", self.opp, self.owner),
            ("advance", self.opp, self.owner),
            ("advance", self.opp, self.owner),
        ])

    def test_missing_opp(self):
        with self.assertRaises(ValueError):
            self.crm.advance("O99", "proposal", "r1")
        self.assertEqual(len(self.crm.log), self.base_log_len)

    def test_unknown_actor_beats_missing_opp(self):
        with self.assertRaises(PermissionError):
            self.crm.advance("O99", "proposal", "ghost")

    def test_invalid_stage_names(self):
        for bad in ("", "PROPOSAL", "closed", None, "prospects"):
            with self.assertRaises(ValueError):
                self.crm.advance(self.opp, bad, "r1")
        self.assertEqual(len(self.crm.log), self.base_log_len)

    def test_invalid_stage_beats_permission(self):
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "bogus", "r2")

    def test_permission_owner_or_manager(self):
        with self.assertRaises(PermissionError):
            self.crm.advance(self.opp, "proposal", "r2")
        self.assertEqual(self.crm.opps[self.opp]["stage"], "prospect")
        self.assertEqual(len(self.crm.log), self.base_log_len)
        self.crm.advance(self.opp, "proposal", "m1")
        self.assertEqual(self.crm.opps[self.opp]["stage"], "proposal")

    def test_final_stage_is_terminal(self):
        walk_to_won(self.crm, self.opp, self.owner)
        last = len(self.crm.log)
        for stage in ("prospect", "proposal", "negotiation", "won", "lost"):
            with self.assertRaises(ValueError):
                self.crm.advance(self.opp, stage, "r1")
        self.assertEqual(len(self.crm.log), last)
        self.assertEqual(self.crm.opps[self.opp]["stage"], "won")

    def test_lost_is_terminal_too(self):
        self.crm.advance(self.opp, "lost", self.owner)
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "proposal", "r1")

    def test_must_follow_stage_order(self):
        # skip proposal
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "negotiation", self.owner)
        # backwards / never-next
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "prospect", self.owner)
        # "won" is not the immediate next from prospect
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "won", self.owner)
        self.assertEqual(self.crm.opps[self.opp]["stage"], "prospect")
        self.crm.advance(self.opp, "proposal", self.owner)
        # from proposal, won is two steps ahead
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "won", self.owner)
        self.assertEqual(self.crm.opps[self.opp]["stage"], "proposal")

    def test_lost_allowed_from_any_nonfinal_stage(self):
        opp1, owner1 = self.opp, self.owner
        opp2, owner2 = make_opp(self.crm, "o2@acme.io", 100)   # O2
        opp3, owner3 = make_opp(self.crm, "o3@acme.io", 100)   # O3
        self.crm.advance(opp1, "lost", owner1)                 # from prospect
        self.crm.advance(opp2, "proposal", owner2)
        self.crm.advance(opp2, "lost", owner2)                 # from proposal
        self.crm.advance(opp3, "proposal", owner3)
        self.crm.advance(opp3, "negotiation", owner3)
        self.crm.advance(opp3, "lost", owner3)                 # from negotiation
        stages = [self.crm.opps[o]["stage"] for o in (opp1, opp2, opp3)]
        self.assertEqual(stages, ["lost", "lost", "lost"])

    def test_negotiation_above_50000_requires_manager(self):
        big, owner = make_opp(self.crm, "big@acme.io", 60000)  # r2
        self.crm.advance(big, "proposal", owner)
        mark = len(self.crm.log)
        with self.assertRaises(PermissionError):
            self.crm.advance(big, "negotiation", owner)
        self.assertEqual(self.crm.opps[big]["stage"], "proposal")
        self.assertEqual(len(self.crm.log), mark)
        self.crm.advance(big, "negotiation", "m1")
        self.assertEqual(self.crm.opps[big]["stage"], "negotiation")

    def test_negotiation_at_exactly_50000_ok_for_rep(self):
        opp, owner = make_opp(self.crm, "e@acme.io", 50000)
        self.crm.advance(opp, "proposal", owner)
        self.crm.advance(opp, "negotiation", owner)
        self.assertEqual(self.crm.opps[opp]["stage"], "negotiation")

    def test_negotiation_gate_uses_current_amount_after_discount(self):
        opp, owner = make_opp(self.crm, "d@acme.io", 60000)
        self.crm.advance(opp, "proposal", owner)
        self.crm.discount(opp, 17, "m1")  # 60000*83//100 = 49800
        self.assertEqual(self.crm.opps[opp]["amount"], 49800)
        self.crm.advance(opp, "negotiation", owner)  # now below the gate

    def test_discounted_amount_above_50000_still_gated(self):
        opp, owner = make_opp(self.crm, "d2@acme.io", 60000)
        self.crm.advance(opp, "proposal", owner)
        self.crm.discount(opp, 15, "m1")  # 60000*85//100 = 51000
        with self.assertRaises(PermissionError):
            self.crm.advance(opp, "negotiation", owner)

    def test_won_frees_slot_and_assigns_waiting_leads_fifo(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        lead = crm.add_lead("a@x.com", "A", "referral", "m1")   # r1
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 100, "r1")                      # r1 load 1 = cap
        w1 = crm.add_lead("w1@x.com", "W1", "web", "m1")        # waiting
        w2 = crm.add_lead("w2@x.com", "W2", "web", "m1")        # waiting
        self.assertIsNone(crm.leads[w1]["owner"])
        walk_to_won(crm, opp, "r1")
        self.assertEqual(crm.leads[w1]["owner"], "r1")
        self.assertIsNone(crm.leads[w2]["owner"])               # cap reached
        self.assertEqual(crm.log[-2:], [
            ("advance", opp, "r1"),
            ("assign", w1, "system"),
        ])

    def test_lost_also_frees_slot(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        lead = crm.add_lead("a@x.com", "A", "referral", "m1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 100, "r1")
        w1 = crm.add_lead("w1@x.com", "W1", "web", "m1")
        w2 = crm.add_lead("w2@x.com", "W2", "web", "m1")
        crm.advance(opp, "lost", "m1")
        self.assertEqual(crm.leads[w1]["owner"], "r1")
        self.assertIsNone(crm.leads[w2]["owner"])
        self.assertEqual(crm.log[-2:], [
            ("advance", opp, "m1"),
            ("assign", w1, "system"),
        ])

    def test_nonfinal_advance_does_not_free_slot(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        lead = crm.add_lead("a@x.com", "A", "referral", "m1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 100, "r1")
        w1 = crm.add_lead("w1@x.com", "W1", "web", "m1")  # waiting
        crm.advance(opp, "proposal", "r1")
        self.assertIsNone(crm.leads[w1]["owner"])
        self.assertEqual(len(crm.log), 5)  # 4 setup entries + advance, no assign

    def test_freeing_stops_at_capacity(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 2},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        lead = crm.add_lead("a@x.com", "A", "referral", "m1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 100, "r1")                # r1 load 1
        held = crm.add_lead("h@x.com", "H", "web", "m1")  # r1 load 2 = cap
        w2 = crm.add_lead("w2@x.com", "W2", "web", "m1")  # waiting
        w3 = crm.add_lead("w3@x.com", "W3", "web", "m1")  # waiting
        self.assertEqual(crm.leads[held]["owner"], "r1")
        walk_to_won(crm, opp, "r1")                       # r1 load drops to 1
        self.assertEqual(crm.leads[w2]["owner"], "r1")    # load 2 -> stop
        self.assertIsNone(crm.leads[w3]["owner"])
        self.assertEqual(crm.log[-2:], [("advance", opp, "r1"),
                                        ("assign", w2, "system")])

    def test_manager_advance_frees_the_owner_slot_not_manager(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        lead = crm.add_lead("a@x.com", "A", "referral", "m1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 100, "r1")
        w1 = crm.add_lead("w1@x.com", "W1", "web", "m1")
        crm.advance(opp, "proposal", "r1")
        crm.advance(opp, "negotiation", "r1")
        crm.advance(opp, "won", "m1")   # manager closes it
        self.assertEqual(crm.leads[w1]["owner"], "r1")  # freed slot is r1's

    def test_failed_advance_changes_nothing(self):
        before = (copy.deepcopy(self.crm.opps), copy.deepcopy(self.crm.log))
        for call in (
            lambda: self.crm.advance("O99", "proposal", "r1"),
            lambda: self.crm.advance(self.opp, "bogus", "r1"),
            lambda: self.crm.advance(self.opp, "negotiation", "r1"),  # skip
            lambda: self.crm.advance(self.opp, "proposal", "r2"),     # perm
        ):
            with self.assertRaises(Exception):
                call()
        after = (copy.deepcopy(self.crm.opps), copy.deepcopy(self.crm.log))
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
