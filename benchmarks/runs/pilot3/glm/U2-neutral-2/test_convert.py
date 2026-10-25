"""Tests for CRM.qualify and CRM.convert."""

import unittest

from crm import CRM, DuplicateLeadError


def make_crm():
    """r1 is the default owner of early leads (tie -> smallest id)."""
    return CRM(
        [
            {"id": "r1", "role": "rep", "capacity": 5},
            {"id": "r2", "role": "rep", "capacity": 5},
            {"id": "m1", "role": "manager", "capacity": 0},
        ]
    )


def add(crm, email="a@x.com", actor="r1"):
    return crm.add_lead(email, "N", "referral", actor)  # score 45


class QualifyTests(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        self.lead = add(self.crm)  # owned by r1

    def test_unknown_lead(self):
        with self.assertRaises(ValueError):
            self.crm.qualify("L99", "r1")

    def test_unknown_actor_first(self):
        with self.assertRaises(PermissionError):
            self.crm.qualify("L99", "ghost")

    def test_non_owner_rep_cannot(self):
        with self.assertRaises(PermissionError):
            self.crm.qualify(self.lead, "r2")

    def test_owner_can_qualify(self):
        self.crm.qualify(self.lead, "r1")
        self.assertEqual(self.crm.leads[self.lead]["status"], "qualified")
        self.assertEqual(self.crm.log[-1], ("qualify", self.lead, "r1"))

    def test_manager_can_qualify_others_lead(self):
        self.crm.qualify(self.lead, "m1")
        self.assertEqual(self.crm.log[-1], ("qualify", self.lead, "m1"))

    def test_low_score_cannot_qualify(self):
        low = self.crm.add_lead("low@gmail.com", "L", "web", "r1")  # score 10
        # this second lead goes to r2 (lowest load), not r1
        self.assertEqual(self.crm.leads[low]["owner"], "r2")
        with self.assertRaises(ValueError):
            self.crm.qualify(low, "r2")

    def test_double_qualify_fails(self):
        self.crm.qualify(self.lead, "r1")
        with self.assertRaises(ValueError):
            self.crm.qualify(self.lead, "r1")

    def test_converted_lead_cannot_qualify(self):
        self.crm.qualify(self.lead, "r1")
        self.crm.convert(self.lead, 100, "r1")
        with self.assertRaises(ValueError):
            self.crm.qualify(self.lead, "r1")

    def test_failure_changes_nothing(self):
        before_log = list(self.crm.log)
        before_status = self.crm.leads[self.lead]["status"]
        with self.assertRaises(PermissionError):
            self.crm.qualify(self.lead, "r2")
        self.assertEqual(self.crm.log, before_log)
        self.assertEqual(self.crm.leads[self.lead]["status"], before_status)


class ConvertTests(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        self.lead = add(self.crm)  # owned by r1
        self.crm.qualify(self.lead, "r1")

    def test_unknown_lead(self):
        with self.assertRaises(ValueError):
            self.crm.convert("L99", 100, "r1")

    def test_amount_validation(self):
        for bad in [0, -5, "100", 1.5, True, False, None]:
            with self.assertRaises(ValueError):
                self.crm.convert(self.lead, bad, "r1")

    def test_non_owner_rep_cannot(self):
        with self.assertRaises(PermissionError):
            self.crm.convert(self.lead, 100, "r2")

    def test_unqualified_cannot_convert(self):
        other = add(self.crm, email="b@x.com")  # owned by r2
        self.assertEqual(self.crm.leads[other]["owner"], "r2")
        with self.assertRaises(ValueError):
            self.crm.convert(other, 100, "r2")  # status still "new"

    def test_ownerless_lead_cannot_convert(self):
        # a manager can qualify a queued lead that has no owner, but the
        # lead still cannot be converted without an owner
        crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 1},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        assigned = crm.add_lead("a@x.com", "A", "referral", "r1")
        queued = crm.add_lead("b@x.com", "B", "referral", "r1")  # r1 full
        self.assertEqual(crm.leads[assigned]["owner"], "r1")
        self.assertIsNone(crm.leads[queued]["owner"])
        crm.qualify(queued, "m1")
        with self.assertRaises(ValueError):
            crm.convert(queued, 100, "m1")

    def test_successful_convert(self):
        opp_id = self.crm.convert(self.lead, 1000, "r1")
        self.assertEqual(opp_id, "O1")
        opp = self.crm.opps[opp_id]
        self.assertEqual(
            opp,
            {
                "id": "O1",
                "lead_id": self.lead,
                "owner": "r1",
                "amount": 1000,
                "original_amount": 1000,
                "stage": "prospect",
            },
        )
        self.assertEqual(self.crm.leads[self.lead]["status"], "converted")
        self.assertEqual(self.crm.log[-1], ("convert", "O1", "r1"))

    def test_manager_can_convert_others_lead(self):
        opp_id = self.crm.convert(self.lead, 500, "m1")
        self.assertEqual(self.crm.opps[opp_id]["owner"], "r1")
        self.assertEqual(self.crm.log[-1], ("convert", "O1", "m1"))

    def test_opp_counter_only_on_success(self):
        with self.assertRaises(ValueError):
            self.crm.convert(self.lead, 0, "r1")
        opp_id = self.crm.convert(self.lead, 100, "r1")
        self.assertEqual(opp_id, "O1")

    def test_convert_frees_lead_but_adds_open_opp(self):
        # a converted lead no longer counts as a lead, but its open
        # opportunity counts the same, so net load is unchanged
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 2}])
        lead = crm.add_lead("a@x.com", "A", "referral", "r1")
        crm.qualify(lead, "r1")
        crm.convert(lead, 100, "r1")  # r1 load still 1 (open opp)
        second = crm.add_lead("b@x.com", "B", "web", "r1")  # load 1 < 2
        self.assertEqual(crm.leads[second]["owner"], "r1")
        third = crm.add_lead("c@x.com", "C", "web", "r1")  # load 2 = cap
        self.assertIsNone(crm.leads[third]["owner"])


if __name__ == "__main__":
    unittest.main()
