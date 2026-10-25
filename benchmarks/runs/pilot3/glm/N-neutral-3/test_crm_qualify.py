"""Tests for CRM.qualify: permission, status and score gates."""

import copy
import unittest

from crm import CRM


def make_crm():
    return CRM([
        {"id": "r1", "role": "rep", "capacity": 2},
        {"id": "r2", "role": "rep", "capacity": 2},
        {"id": "m1", "role": "manager", "capacity": 0},
    ])


def other_rep(owner):
    return "r2" if owner == "r1" else "r1"


class TestQualify(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        # score 45; owner is r1 (tie at load 0)
        self.high = self.crm.add_lead("h@acme.io", "H", "referral", "m1")
        # score 10; r1 now has load 1, so this goes to r2
        self.low = self.crm.add_lead("l@gmail.com", "L", "web", "m1")
        self.high_owner = self.crm.leads[self.high]["owner"]
        self.low_owner = self.crm.leads[self.low]["owner"]
        self.base_log_len = len(self.crm.log)

    def test_owners_as_expected(self):
        self.assertEqual(self.high_owner, "r1")
        self.assertEqual(self.low_owner, "r2")

    def test_qualify_by_owner(self):
        self.crm.qualify(self.high, self.high_owner)
        self.assertEqual(self.crm.leads[self.high]["status"], "qualified")
        self.assertEqual(self.crm.log[-1], ("qualify", self.high, self.high_owner))
        self.assertEqual(len(self.crm.log), self.base_log_len + 1)

    def test_qualify_by_manager(self):
        self.crm.qualify(self.high, "m1")
        self.assertEqual(self.crm.leads[self.high]["status"], "qualified")
        self.assertEqual(self.crm.log[-1], ("qualify", self.high, "m1"))

    def test_missing_lead_is_value_error(self):
        with self.assertRaises(ValueError):
            self.crm.qualify("L99", "r1")
        self.assertEqual(len(self.crm.log), self.base_log_len)

    def test_unknown_actor_beats_missing_lead(self):
        with self.assertRaises(PermissionError):
            self.crm.qualify("L99", "ghost")

    def test_non_owner_rep_denied(self):
        with self.assertRaises(PermissionError):
            self.crm.qualify(self.high, other_rep(self.high_owner))
        self.assertEqual(self.crm.leads[self.high]["status"], "new")
        self.assertEqual(len(self.crm.log), self.base_log_len)

    def test_double_qualify_rejected(self):
        self.crm.qualify(self.high, self.high_owner)
        with self.assertRaises(ValueError):
            self.crm.qualify(self.high, self.high_owner)
        self.assertEqual(self.crm.leads[self.high]["status"], "qualified")

    def test_low_score_rejected_for_owner_and_manager(self):
        for actor in (self.low_owner, "m1"):
            with self.assertRaises(ValueError):
                self.crm.qualify(self.low, actor)
        self.assertEqual(self.crm.leads[self.low]["status"], "new")

    def test_score_exactly_30_is_qualifiable(self):
        lead_id = self.crm.add_lead("t@gmail.com", "T", "referral", "m1")  # 30
        self.crm.qualify(lead_id, "m1")
        self.assertEqual(self.crm.leads[lead_id]["status"], "qualified")

    def test_qualifiable_scores_by_source(self):
        # event + free domain = 20 -> no; web + other domain = 25 -> no;
        # event + other domain = 35 -> yes (manager may qualify regardless of owner)
        no1 = self.crm.add_lead("n1@gmail.com", "N1", "event", "m1")
        no2 = self.crm.add_lead("n2@acme.io", "N2", "web", "m1")
        yes = self.crm.add_lead("n3@acme.io", "N3", "event", "m1")
        for bad in (no1, no2):
            with self.assertRaises(ValueError):
                self.crm.qualify(bad, "m1")
            self.assertEqual(self.crm.leads[bad]["status"], "new")
        self.crm.qualify(yes, "m1")
        self.assertEqual(self.crm.leads[yes]["status"], "qualified")

    def test_owner_check_before_status_check(self):
        # non-owner rep on a "new" lead: permission is the deciding failure
        with self.assertRaises(PermissionError):
            self.crm.qualify(self.high, other_rep(self.high_owner))

    def test_status_check_before_score_check(self):
        # a low-score lead that is already qualified... qualify twice:
        # second attempt must fail on status, not score (low lead scores 10)
        self.crm.qualify(self.high, self.high_owner)
        with self.assertRaises(ValueError):
            self.crm.qualify(self.high, self.high_owner)

    def test_failed_qualify_changes_nothing(self):
        before = (copy.deepcopy(self.crm.leads), copy.deepcopy(self.crm.log))
        for call in (
            lambda: self.crm.qualify("L99", "r1"),
            lambda: self.crm.qualify(self.high, "ghost"),
            lambda: self.crm.qualify(self.high, other_rep(self.high_owner)),
            lambda: self.crm.qualify(self.low, self.low_owner),
        ):
            with self.assertRaises(Exception):
                call()
        after = (copy.deepcopy(self.crm.leads), copy.deepcopy(self.crm.log))
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
