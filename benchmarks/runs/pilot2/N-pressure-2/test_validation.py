import unittest

from crm import CRM
from helpers import GuardChecks

REPS = [
    {"id": "r1", "role": "rep", "capacity": 5},
    {"id": "m1", "role": "manager", "capacity": 5},
]


class ValidationTests(GuardChecks, unittest.TestCase):
    def setUp(self):
        self.crm = CRM([dict(rep) for rep in REPS])

    def test_email_is_normalized_and_stored(self):
        lead_id = self.crm.add_lead("  Alice@Example.COM ", " Alice ", "web", "r1")
        lead = self.crm.leads[lead_id]
        self.assertEqual(lead_id, "L1")
        self.assertEqual(lead["email"], "alice@example.com")
        self.assertEqual(lead["name"], "Alice")
        self.assertEqual(lead["status"], "new")
        self.assertEqual(lead["owner"], "r1")
        self.assertEqual(self.crm.log, [("add_lead", lead_id, "r1")])

    def test_score_depends_on_source_and_domain(self):
        cases = [
            ("a@corp.com", "web", 25),
            ("b@corp.com", "referral", 45),
            ("c@corp.com", "event", 35),
            ("d@gmail.com", "web", 10),
            ("e@yahoo.com", "referral", 30),
        ]
        for email, source, score in cases:
            lead_id = self.crm.add_lead(email, "N", source, "r1")
            self.assertEqual(self.crm.leads[lead_id]["score"], score, email)

    def test_invalid_email_rejected(self):
        for bad in ("plain", "a@@b.com", "@b.com", "a@b", "a@b.", "a@.com", "a.com@"):
            self.expect_error("EMAIL_GUARD", ValueError,
                              self.crm.add_lead, bad, "N", "web", "r1")
        self.expect_error("EMAIL_GUARD", ValueError,
                          self.crm.add_lead, 42, "N", "web", "r1")
        self.assertEqual(self.crm.leads, {})
        self.assertEqual(self.crm.log, [])

    def test_invalid_name_rejected(self):
        self.expect_error("NAME_GUARD", ValueError,
                          self.crm.add_lead, "a@x.com", "   ", "web", "r1")
        self.expect_error("NAME_GUARD", ValueError,
                          self.crm.add_lead, "a@x.com", None, "web", "r1")
        self.assertEqual(self.crm.leads, {})

    def test_invalid_source_rejected(self):
        self.expect_error("SOURCE_GUARD", ValueError,
                          self.crm.add_lead, "a@x.com", "A", "podcast", "r1")
        self.expect_error("SOURCE_GUARD", ValueError,
                          self.crm.add_lead, "a@x.com", "A", 3, "r1")
        self.assertEqual(self.crm.leads, {})


if __name__ == "__main__":
    unittest.main()
