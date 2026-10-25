"""Tests for CRM.transfer: manager-only, rep targets, slot freeing."""

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


class TestTransfer(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        self.opp, self.owner = make_opp(self.crm, "h@acme.io", 1000)  # r1
        self.base_log_len = len(self.crm.log)

    def test_owner_is_r1(self):
        self.assertEqual(self.owner, "r1")

    def test_transfer_by_manager(self):
        self.crm.transfer(self.opp, "r2", "m1")
        self.assertEqual(self.crm.opps[self.opp]["owner"], "r2")
        self.assertEqual(self.crm.log[-1], ("transfer", self.opp, "m1"))
        self.assertEqual(len(self.crm.log), self.base_log_len + 1)

    def test_rep_cannot_transfer_even_their_own(self):
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.opp, "r2", self.owner)
        self.assertEqual(self.crm.opps[self.opp]["owner"], self.owner)
        self.assertEqual(len(self.crm.log), self.base_log_len)

    def test_missing_opp(self):
        with self.assertRaises(ValueError):
            self.crm.transfer("O99", "r2", "m1")
        self.assertEqual(len(self.crm.log), self.base_log_len)

    def test_unknown_actor_beats_missing_opp(self):
        with self.assertRaises(PermissionError):
            self.crm.transfer("O99", "r2", "ghost")

    def test_new_owner_must_be_known_rep(self):
        for bad in ("ghost", "m1", None, 42):
            with self.assertRaises(ValueError):
                self.crm.transfer(self.opp, bad, "m1")
        self.assertEqual(self.crm.opps[self.opp]["owner"], self.owner)
        self.assertEqual(len(self.crm.log), self.base_log_len)

    def test_permission_beats_new_owner_validation(self):
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.opp, "ghost", "r2")

    def test_final_stage_rejected(self):
        walk_to_won(self.crm, self.opp, self.owner)
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "r2", "m1")
        self.assertEqual(self.crm.opps[self.opp]["owner"], self.owner)

    def test_new_owner_validation_before_final_check(self):
        walk_to_won(self.crm, self.opp, self.owner)
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "ghost", "m1")

    def test_same_owner_rejected(self):
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, self.owner, "m1")
        self.assertEqual(len(self.crm.log), self.base_log_len)

    def test_full_new_owner_rejected(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        opp1, owner1 = make_opp(crm, "a@x.com", 100)   # r1 load 1 = cap
        opp2, owner2 = make_opp(crm, "b@x.com", 100)   # r2 load 1 = cap
        with self.assertRaises(ValueError):
            crm.transfer(opp1, "r2", "m1")
        self.assertEqual(crm.opps[opp1]["owner"], owner1)
        # once r2 frees a slot the transfer succeeds
        crm.advance(opp2, "lost", owner2)
        crm.transfer(opp1, "r2", "m1")
        self.assertEqual(crm.opps[opp1]["owner"], "r2")

    def test_transfer_logs_no_assign_when_queue_is_empty(self):
        self.crm.transfer(self.opp, "r2", "m1")
        self.assertFalse(any(entry[0] == "assign" for entry in self.crm.log))
        self.assertEqual(self.crm.log[-1], ("transfer", self.opp, "m1"))

    def test_transfer_chain_back_and_forth(self):
        self.crm.transfer(self.opp, "r2", "m1")
        self.crm.transfer(self.opp, "r1", "m1")
        self.assertEqual(self.crm.opps[self.opp]["owner"], "r1")
        self.assertEqual(self.crm.log[-2:], [
            ("transfer", self.opp, "m1"),
            ("transfer", self.opp, "m1"),
        ])

    def test_failed_transfer_changes_nothing(self):
        before = (copy.deepcopy(self.crm.leads), copy.deepcopy(self.crm.opps),
                  copy.deepcopy(self.crm.log))
        for call in (
            lambda: self.crm.transfer("O99", "r2", "m1"),
            lambda: self.crm.transfer(self.opp, "r2", "r1"),
            lambda: self.crm.transfer(self.opp, "ghost", "m1"),
            lambda: self.crm.transfer(self.opp, self.owner, "m1"),
        ):
            with self.assertRaises(Exception):
                call()
        after = (copy.deepcopy(self.crm.leads), copy.deepcopy(self.crm.opps),
                 copy.deepcopy(self.crm.log))
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
