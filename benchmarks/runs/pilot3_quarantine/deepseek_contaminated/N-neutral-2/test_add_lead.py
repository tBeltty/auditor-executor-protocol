"""Tests for CRM.add_lead."""

import unittest

from _helpers import manager, rep, snapshot
from crm import CRM, DuplicateLeadError


class AddLeadValidationTests(unittest.TestCase):
    def setUp(self):
        self.crm = CRM([rep("r1", 5), manager("m1")])

    def assert_rejected(self, exc, **kwargs):
        before = snapshot(self.crm)
        with self.assertRaises(exc):
            self.crm.add_lead(**kwargs)
        self.assertEqual(snapshot(self.crm), before)

    def test_unknown_actor_wins_over_invalid_arguments(self):
        self.assert_rejected(
            PermissionError,
            email=None, name=None, source="bogus", actor="ghost",
        )

    def test_email_must_be_string(self):
        for bad in (None, 42, ["a@b.com"]):
            self.assert_rejected(ValueError, email=bad, name="N", source="web", actor="r1")

    def test_email_shape(self):
        bad = [
            "plain",
            "a@b@c.com",
            "@corp.com",
            "a@corp",
            "a@.com",
            "a@corp.",
            "a@.corp.",
            "   ",
        ]
        for email in bad:
            self.assert_rejected(ValueError, email=email, name="N", source="web", actor="r1")

    def test_valid_email_shapes(self):
        for n, email in enumerate(["a@b.co", "x@y.z", "a@sub.corp.com", "a@a-b.io"]):
            self.crm.add_lead(email, "N", "web", "r1")
            self.assertEqual(self.crm.leads["L%d" % (n + 1)]["email"], email.lower())

    def test_name_validation(self):
        for bad in (None, 3, "", "   ", "\t\n"):
            self.assert_rejected(ValueError, email="a@corp.com", name=bad, source="web", actor="r1")

    def test_source_validation(self):
        for bad in ("email", "", None, 3, ["web"]):
            self.assert_rejected(ValueError, email="a@corp.com", name="N", source=bad, actor="r1")


class AddLeadBehaviourTests(unittest.TestCase):
    def setUp(self):
        self.crm = CRM([rep("r1", 5), manager("m1")])

    def test_normalizes_and_stores_stripped_values(self):
        lead_id = self.crm.add_lead("  Alice@Corp.COM ", "  Alice  ", "referral", "r1")
        lead = self.crm.leads[lead_id]
        self.assertEqual(lead["email"], "alice@corp.com")
        self.assertEqual(lead["name"], "Alice")
        self.assertEqual(lead["status"], "new")
        self.assertEqual(lead["source"], "referral")
        self.assertEqual(lead["owner"], "r1")
        self.assertEqual(lead["id"], "L1")

    def test_scores_include_business_domain_bonus(self):
        expected = {
            ("gmail.com", "web"): 10,
            ("yahoo.com", "referral"): 30,
            ("outlook.com", "event"): 20,
            ("corp.com", "web"): 25,
            ("corp.com", "referral"): 45,
            ("corp.com", "event"): 35,
        }
        for (domain, source), score in expected.items():
            crm = CRM([rep("r1", 5)])
            lead_id = crm.add_lead("a@%s" % domain, "N", source, "r1")
            self.assertEqual(crm.leads[lead_id]["score"], score, (domain, source))

    def test_duplicate_email_is_case_and_space_insensitive(self):
        first = self.crm.add_lead("Bob@Corp.com", "Bob", "referral", "r1")
        before = snapshot(self.crm)
        with self.assertRaises(DuplicateLeadError) as ctx:
            self.crm.add_lead("  bob@CORP.COM ", "Other", "web", "r1")
        self.assertEqual(ctx.exception.existing_id, first)
        self.assertEqual(snapshot(self.crm), before)

    def test_duplicate_does_not_consume_lead_number(self):
        self.crm.add_lead("a@corp.com", "A", "referral", "r1")
        with self.assertRaises(DuplicateLeadError):
            self.crm.add_lead("a@corp.com", "A2", "referral", "r1")
        self.assertEqual(self.crm.add_lead("b@corp.com", "B", "referral", "r1"), "L2")

    def test_lead_numbers_count_all_successful_creations(self):
        ids = [
            self.crm.add_lead("%s@corp.com" % name, name, "referral", "r1")
            for name in ("a", "b", "c")
        ]
        self.assertEqual(ids, ["L1", "L2", "L3"])

    def test_log_entry(self):
        lead_id = self.crm.add_lead("a@corp.com", "A", "web", "m1")
        self.assertEqual(self.crm.log, [("add_lead", lead_id, "m1")])
        self.assertIsInstance(self.crm.log[0], tuple)


class OwnershipTests(unittest.TestCase):
    def test_lowest_load_wins(self):
        crm = CRM([rep("r1", 3), rep("r2", 3)])
        crm.add_lead("a@corp.com", "A", "referral", "r1")  # r1: 1
        lead_b = crm.add_lead("b@corp.com", "B", "referral", "r1")
        self.assertEqual(crm.leads[lead_b]["owner"], "r2")

    def test_ties_use_smallest_id_in_string_order(self):
        crm = CRM([rep("a2", 3), rep("a10", 3)])
        lead_id = crm.add_lead("a@corp.com", "A", "referral", "a2")
        self.assertEqual(crm.leads[lead_id]["owner"], "a10")

    def test_managers_never_own_leads(self):
        crm = CRM([manager("m1")])
        lead_id = crm.add_lead("a@corp.com", "A", "referral", "m1")
        self.assertIsNone(crm.leads[lead_id]["owner"])
        self.assertEqual(crm.waiting, [lead_id])

    def test_no_capacity_goes_to_fifo_waiting_queue(self):
        crm = CRM([rep("r1", 1)])
        first = crm.add_lead("a@corp.com", "A", "referral", "r1")
        second = crm.add_lead("b@corp.com", "B", "referral", "r1")
        third = crm.add_lead("c@corp.com", "C", "referral", "r1")
        self.assertEqual(crm.leads[first]["owner"], "r1")
        self.assertIsNone(crm.leads[second]["owner"])
        self.assertIsNone(crm.leads[third]["owner"])
        self.assertEqual(crm.waiting, [second, third])

    def test_capacity_zero_rep_never_owns(self):
        crm = CRM([rep("r1", 0)])
        lead_id = crm.add_lead("a@corp.com", "A", "referral", "r1")
        self.assertIsNone(crm.leads[lead_id]["owner"])


if __name__ == "__main__":
    unittest.main()
