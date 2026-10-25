"""Guard group: email / name / source validation on add_lead."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import crm  # noqa: E402
import fixtures  # noqa: E402


class EmailValidationTests(unittest.TestCase):
    def setUp(self):
        self.crm = fixtures.team()

    def test_normalizes_case_and_whitespace(self):
        lead_id = self.crm.add_lead("  Alice@Example.COM  ", "Alice", "web", "r1")
        lead = self.crm.leads[lead_id]
        self.assertEqual(lead["email"], "alice@example.com")
        self.assertEqual(lead["name"], "Alice")

    def test_accepts_inner_dot_in_domain(self):
        lead_id = self.crm.add_lead("a@b.c", "A", "web", "r1")
        self.assertEqual(self.crm.leads[lead_id]["email"], "a@b.c")

    def test_rejects_non_string_email(self):
        for bad in (None, 123, 1.5, ["a@b.com"], {"e": "a@b.com"}):
            with self.subTest(email=bad):
                with self.assertRaises(ValueError):
                    self.crm.add_lead(bad, "A", "web", "r1")

    def test_rejects_email_without_at(self):
        with self.assertRaises(ValueError):
            self.crm.add_lead("alice.example.com", "A", "web", "r1")

    def test_rejects_email_with_several_ats(self):
        with self.assertRaises(ValueError):
            self.crm.add_lead("a@b@example.com", "A", "web", "r1")

    def test_rejects_empty_local_part(self):
        for bad in ("@example.com", "  @example.com  "):
            with self.subTest(email=bad):
                with self.assertRaises(ValueError):
                    self.crm.add_lead(bad, "A", "web", "r1")

    def test_rejects_domain_without_dot(self):
        with self.assertRaises(ValueError):
            self.crm.add_lead("alice@example", "A", "web", "r1")

    def test_rejects_dot_as_first_domain_character(self):
        with self.assertRaises(ValueError):
            self.crm.add_lead("alice@.example", "A", "web", "r1")

    def test_rejects_dot_as_last_domain_character(self):
        with self.assertRaises(ValueError):
            self.crm.add_lead("alice@example.", "A", "web", "r1")

    def test_rejects_blank_email(self):
        for bad in ("", "   ", "@"):
            with self.subTest(email=bad):
                with self.assertRaises(ValueError):
                    self.crm.add_lead(bad, "A", "web", "r1")

    def test_email_checked_before_name(self):
        with self.assertRaises(ValueError) as caught:
            self.crm.add_lead("nope", "", "web", "r1")
        self.assertIn("email", str(caught.exception).lower())

    def test_failed_email_validation_creates_nothing(self):
        with self.assertRaises(ValueError):
            self.crm.add_lead("nope", "A", "web", "r1")
        self.assertEqual(self.crm.leads, {})
        self.assertEqual(self.crm.log, [])


class NameValidationTests(unittest.TestCase):
    def setUp(self):
        self.crm = fixtures.team()

    def test_rejects_non_string_name(self):
        for bad in (None, 7, 3.5, ["Alice"]):
            with self.subTest(name=bad):
                with self.assertRaises(ValueError):
                    self.crm.add_lead("a@b.com", bad, "web", "r1")

    def test_rejects_blank_name(self):
        for bad in ("", "   ", "\t\n"):
            with self.subTest(name=bad):
                with self.assertRaises(ValueError):
                    self.crm.add_lead("a@b.com", bad, "web", "r1")

    def test_strips_name(self):
        lead_id = self.crm.add_lead("a@b.com", "  Alice Smith  ", "web", "r1")
        self.assertEqual(self.crm.leads[lead_id]["name"], "Alice Smith")


class SourceValidationTests(unittest.TestCase):
    def setUp(self):
        self.crm = fixtures.team()

    def test_accepts_the_three_sources(self):
        for source in ("web", "referral", "event"):
            with self.subTest(source=source):
                lead_id = self.crm.add_lead("a@%s.com" % source, "A", source, "r1")
                self.assertEqual(self.crm.leads[lead_id]["source"], source)

    def test_rejects_unknown_source(self):
        for bad in ("ads", "", "Web", "WEB", None, 3, ["web"]):
            with self.subTest(source=bad):
                with self.assertRaises(ValueError):
                    self.crm.add_lead("a@b.com", "A", bad, "r1")

    def test_source_checked_after_name(self):
        with self.assertRaises(ValueError) as caught:
            self.crm.add_lead("a@b.com", "", "ads", "r1")
        self.assertIn("name", str(caught.exception).lower())


if __name__ == "__main__":
    unittest.main()
