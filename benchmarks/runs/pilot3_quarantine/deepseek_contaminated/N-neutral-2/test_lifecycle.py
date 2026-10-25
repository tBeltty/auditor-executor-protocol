"""Tests for CRM.qualify and CRM.convert."""

import unittest

from _helpers import manager, qualify_and_convert, rep, snapshot
from crm import CRM


class QualifyTests(unittest.TestCase):
    def setUp(self):
        self.crm = CRM([rep("r1", 5), rep("r2", 0), manager("m1")])

    def test_unknown_actor_checked_first(self):
        lead_id = self.crm.add_lead("a@corp.com", "A", "referral", "r1")
        before = snapshot(self.crm)
        with self.assertRaises(PermissionError):
            self.crm.qualify(lead_id, "ghost")
        self.assertEqual(snapshot(self.crm), before)

    def test_unknown_lead(self):
        with self.assertRaises(ValueError):
            self.crm.qualify("L999", "r1")

    def test_non_owner_rep_cannot_qualify(self):
        lead_id = self.crm.add_lead("a@corp.com", "A", "referral", "r1")
        before = snapshot(self.crm)
        with self.assertRaises(PermissionError):
            self.crm.qualify(lead_id, "r2")
        self.assertEqual(snapshot(self.crm), before)

    def test_manager_can_qualify(self):
        lead_id = self.crm.add_lead("a@corp.com", "A", "referral", "r1")
        self.crm.qualify(lead_id, "m1")
        self.assertEqual(self.crm.leads[lead_id]["status"], "qualified")

    def test_only_new_leads_can_be_qualified(self):
        lead_id, _ = qualify_and_convert(self.crm)
        before = snapshot(self.crm)
        with self.assertRaises(ValueError):
            self.crm.qualify(lead_id, "r1")
        self.assertEqual(snapshot(self.crm), before)

    def test_low_score_cannot_be_qualified(self):
        low = self.crm.add_lead("a@corp.com", "A", "web", "r1")  # 25 with corp.com
        self.assertEqual(self.crm.leads[low]["score"], 25)
        before = snapshot(self.crm)
        with self.assertRaises(ValueError):
            self.crm.qualify(low, "r1")
        self.assertEqual(snapshot(self.crm), before)

    def test_score_thirty_is_enough(self):
        lead_id = self.crm.add_lead("a@gmail.com", "A", "referral", "r1")
        self.assertEqual(self.crm.leads[lead_id]["score"], 30)
        self.crm.qualify(lead_id, "r1")
        self.assertEqual(self.crm.leads[lead_id]["status"], "qualified")

    def test_success_logs(self):
        lead_id = self.crm.add_lead("a@corp.com", "A", "referral", "r1")
        self.crm.qualify(lead_id, "r1")
        self.assertEqual(self.crm.log[-1], ("qualify", lead_id, "r1"))


class ConvertTests(unittest.TestCase):
    def setUp(self):
        self.crm = CRM([rep("r1", 5), rep("r2", 0), manager("m1")])

    def ready_lead(self, email="a@corp.com", source="referral", actor="r1"):
        lead_id = self.crm.add_lead(email, "A", source, actor)
        self.crm.qualify(lead_id, actor)
        return lead_id

    def test_unknown_actor_checked_first(self):
        lead_id = self.ready_lead()
        before = snapshot(self.crm)
        with self.assertRaises(PermissionError):
            self.crm.convert(lead_id, 100, "ghost")
        self.assertEqual(snapshot(self.crm), before)

    def test_unknown_lead(self):
        with self.assertRaises(ValueError):
            self.crm.convert("L42", 100, "r1")

    def test_amount_validation(self):
        lead_id = self.ready_lead()
        for bad in (0, -5, True, False, 10.5, "100", None):
            before = snapshot(self.crm)
            with self.assertRaises(ValueError):
                self.crm.convert(lead_id, bad, "r1")
            self.assertEqual(snapshot(self.crm), before)
        self.assertEqual(self.crm.opps, {})

    def test_amount_checked_before_permission(self):
        lead_id = self.ready_lead()
        with self.assertRaises(ValueError):
            self.crm.convert(lead_id, 0, "r2")

    def test_non_owner_cannot_convert(self):
        lead_id = self.ready_lead()
        before = snapshot(self.crm)
        with self.assertRaises(PermissionError):
            self.crm.convert(lead_id, 100, "r2")
        self.assertEqual(snapshot(self.crm), before)

    def test_manager_can_convert(self):
        lead_id = self.ready_lead()
        opp_id = self.crm.convert(lead_id, 100, "m1")
        self.assertEqual(self.crm.opps[opp_id]["owner"], "r1")

    def test_lead_must_be_qualified(self):
        lead_id = self.crm.add_lead("a@corp.com", "A", "referral", "r1")
        before = snapshot(self.crm)
        with self.assertRaises(ValueError):
            self.crm.convert(lead_id, 100, "r1")
        self.assertEqual(snapshot(self.crm), before)

    def test_unowned_lead_cannot_be_converted(self):
        crm = CRM([rep("r1", 0), manager("m1")])
        lead_id = crm.add_lead("a@corp.com", "A", "referral", "m1")
        self.assertIsNone(crm.leads[lead_id]["owner"])
        crm.qualify(lead_id, "m1")
        before = snapshot(crm)
        with self.assertRaises(ValueError):
            crm.convert(lead_id, 100, "m1")
        self.assertEqual(snapshot(crm), before)
        self.assertEqual(crm.opps, {})

    def test_success_creates_opportunity_and_logs(self):
        lead_id = self.ready_lead()
        opp_id = self.crm.convert(lead_id, 2500, "r1")
        self.assertEqual(opp_id, "O1")
        self.assertEqual(
            self.crm.opps[opp_id],
            {
                "id": "O1",
                "lead_id": lead_id,
                "owner": "r1",
                "amount": 2500,
                "original_amount": 2500,
                "stage": "prospect",
            },
        )
        self.assertEqual(self.crm.leads[lead_id]["status"], "converted")
        self.assertEqual(self.crm.log[-1], ("convert", opp_id, "r1"))

    def test_opportunity_numbers_count_successful_conversions_only(self):
        lead_a = self.ready_lead("a@corp.com")
        lead_b = self.ready_lead("b@corp.com")
        with self.assertRaises(ValueError):
            self.crm.convert(lead_a, -1, "r1")
        self.assertEqual(self.crm.convert(lead_a, 10, "r1"), "O1")
        self.assertEqual(self.crm.convert(lead_b, 10, "r1"), "O2")

    def test_converted_lead_does_not_use_a_load_slot(self):
        crm = CRM([rep("r1", 2)])
        _, opp_id = qualify_and_convert(crm)
        next_lead = crm.add_lead("b@corp.com", "B", "referral", "r1")
        self.assertEqual(crm.leads[next_lead]["owner"], "r1")
        self.assertEqual(crm.waiting, [])
        self.assertEqual(len(crm.opps), 1)
        self.assertEqual(crm.opps[opp_id]["owner"], "r1")


if __name__ == "__main__":
    unittest.main()
