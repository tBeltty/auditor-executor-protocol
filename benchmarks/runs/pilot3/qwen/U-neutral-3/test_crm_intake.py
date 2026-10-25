"""Tests for lead intake: actor gate, validation order, duplicates, scoring."""

import copy
import unittest

from crm import CRM, DuplicateLeadError

REPS = [
    {"id": "r1", "role": "rep", "capacity": 5},
    {"id": "r2", "role": "rep", "capacity": 5},
    {"id": "m1", "role": "manager", "capacity": 0},
]


def new_crm(reps=None):
    return CRM(reps if reps is not None else copy.deepcopy(REPS))


class ActorGateTest(unittest.TestCase):
    def test_unknown_actor_raises_permission_error(self):
        crm = new_crm()
        lead = crm.add_lead("a@acme.com", "Ann", "referral", "r1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 1000, "r1")
        for call in (
            lambda: crm.add_lead("c@d.com", "Cy", "web", "ghost"),
            lambda: crm.qualify(lead, "ghost"),
            lambda: crm.convert(lead, 100, "ghost"),
            lambda: crm.advance(opp, "proposal", "ghost"),
            lambda: crm.discount(opp, 5, "ghost"),
            lambda: crm.transfer(opp, "r2", "ghost"),
        ):
            with self.assertRaises(PermissionError):
                call()
        self.assertEqual([entry[2] for entry in crm.log], ["r1", "r1", "r1"])

    def test_actor_check_runs_before_other_validation(self):
        crm = new_crm()
        # Bad email and bad source, yet the unknown actor wins.
        with self.assertRaises(PermissionError):
            crm.add_lead("not-an-email", "", "nonsense", "ghost")
        # Unknown lead would be a ValueError, but the actor is checked first.
        with self.assertRaises(PermissionError):
            crm.qualify("L99", "ghost")
        with self.assertRaises(PermissionError):
            crm.convert("L99", -1, "ghost")

    def test_manager_is_a_valid_actor(self):
        crm = new_crm()
        self.assertEqual(crm.add_lead("a@b.com", "Ann", "web", "m1"), "L1")

    def test_failed_call_logs_nothing(self):
        crm = new_crm()
        with self.assertRaises(PermissionError):
            crm.add_lead("a@b.com", "Ann", "web", "ghost")
        self.assertEqual(crm.log, [])
        self.assertEqual(crm.leads, {})


class EmailValidationTest(unittest.TestCase):
    def setUp(self):
        self.crm = new_crm()

    def assertBadEmail(self, email):
        with self.assertRaises(ValueError):
            self.crm.add_lead(email, "Ann", "web", "r1")
        self.assertEqual(self.crm.leads, {})
        self.assertEqual(self.crm.log, [])

    def test_non_string_email(self):
        for bad in (None, 123, b"a@b.com", ["a@b.com"], 1.5):
            self.assertBadEmail(bad)

    def test_missing_or_multiple_at_signs(self):
        for bad in ("plainaddress", "@b.com", "a@@b.com", "a@b@c.com", "a@"):
            self.assertBadEmail(bad)

    def test_empty_local_part(self):
        self.assertBadEmail("@example.com")
        self.assertBadEmail("   @example.com")

    def test_domain_needs_interior_dot(self):
        for bad in ("a@example", "a@.com", "a@example.", "a@com.", "a@."):
            self.assertBadEmail(bad)

    def test_valid_emails(self):
        for good in ("a@b.com", "x.y+z@sub.example.co.uk", "a@b.c"):
            self.crm.add_lead(good, "Ann", "web", "r1")
        self.assertEqual(len(self.crm.leads), 3)

    def test_email_is_stripped_and_lowercased(self):
        lead_id = self.crm.add_lead("  Ann@Acme.COM ", "Ann", "web", "r1")
        self.assertEqual(self.crm.leads[lead_id]["email"], "ann@acme.com")

    def test_uppercase_gmail_counts_as_free_domain(self):
        lead_id = self.crm.add_lead("a@GMAIL.com", "Ann", "referral", "r1")
        self.assertEqual(self.crm.leads[lead_id]["score"], 30)


class NameAndSourceValidationTest(unittest.TestCase):
    def setUp(self):
        self.crm = new_crm()

    def test_name_must_be_string(self):
        for bad in (None, 5, ["Ann"], b"Ann"):
            with self.assertRaises(ValueError):
                self.crm.add_lead("a@b.com", bad, "web", "r1")

    def test_name_must_be_non_empty_after_strip(self):
        for bad in ("", "   ", "\t\n "):
            with self.assertRaises(ValueError):
                self.crm.add_lead("a@b.com", bad, "web", "r1")

    def test_name_is_stored_stripped(self):
        lead_id = self.crm.add_lead("a@b.com", "  Ann Lee  ", "web", "r1")
        self.assertEqual(self.crm.leads[lead_id]["name"], "Ann Lee")

    def test_source_must_be_known(self):
        for bad in ("phone", "WEB", "", None, 0):
            with self.assertRaises(ValueError):
                self.crm.add_lead("a@b.com", "Ann", bad, "r1")
        self.assertEqual(self.crm.leads, {})


class DuplicateTest(unittest.TestCase):
    def setUp(self):
        self.crm = new_crm()

    def test_duplicate_raises_with_existing_id(self):
        first = self.crm.add_lead("Ann@Acme.com", "Ann", "web", "r1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            self.crm.add_lead("  ann@acme.com  ", "Ann Again", "referral", "r1")
        self.assertEqual(ctx.exception.existing_id, first)

    def test_duplicate_changes_nothing(self):
        first = self.crm.add_lead("ann@acme.com", "Ann", "web", "r1")
        snapshot = copy.deepcopy(self.crm)
        with self.assertRaises(DuplicateLeadError):
            self.crm.add_lead("ann@acme.com", "Other", "event", "m1")
        self.assertEqual(self.crm.leads, snapshot.leads)
        self.assertEqual(self.crm.log, snapshot.log)
        self.assertEqual(self.crm.opps, snapshot.opps)

    def test_sequence_number_is_not_consumed_by_failure(self):
        self.crm.add_lead("ann@acme.com", "Ann", "web", "r1")
        with self.assertRaises(DuplicateLeadError):
            self.crm.add_lead("ann@acme.com", "Ann", "web", "r1")
        self.assertEqual(self.crm.add_lead("bob@acme.com", "Bob", "web", "r1"), "L2")

    def test_duplicate_detected_against_converted_lead(self):
        lead = self.crm.add_lead("ann@acme.com", "Ann", "referral", "r1")
        self.crm.qualify(lead, "r1")
        self.crm.convert(lead, 500, "r1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            self.crm.add_lead("ann@acme.com", "Ann", "web", "r1")
        self.assertEqual(ctx.exception.existing_id, lead)

    def test_is_a_normal_exception(self):
        self.assertTrue(issubclass(DuplicateLeadError, Exception))
        err = DuplicateLeadError("L7")
        self.assertEqual(err.existing_id, "L7")
        self.assertIn("L7", str(err))


class ScoringTest(unittest.TestCase):
    def test_source_scores(self):
        crm = new_crm()
        cases = {
            "web": 10,
            "referral": 30,
            "event": 20,
        }
        for index, (source, score) in enumerate(cases.items(), start=1):
            lead_id = crm.add_lead("a%d@acme.com" % index, "N", source, "r1")
            self.assertEqual(crm.leads[lead_id]["score"], score + 15)

    def test_free_domains_get_no_bonus(self):
        crm = new_crm()
        for index, domain in enumerate(("gmail.com", "yahoo.com", "outlook.com"), start=1):
            lead_id = crm.add_lead("a%d@%s" % (index, domain), "N", "web", "r1")
            self.assertEqual(crm.leads[lead_id]["score"], 10)
        lead_id = crm.add_lead("x@gmal.com", "N", "web", "r1")
        self.assertEqual(crm.leads[lead_id]["score"], 25)

    def test_lead_record_shape_and_log(self):
        crm = new_crm()
        lead_id = crm.add_lead(" ann@acme.com ", "  Ann  ", "event", "m1")
        self.assertEqual(lead_id, "L1")
        self.assertEqual(
            crm.leads["L1"],
            {
                "id": "L1",
                "email": "ann@acme.com",
                "name": "Ann",
                "source": "event",
                "score": 35,
                "owner": "r1",
                "status": "new",
            },
        )
        self.assertEqual(crm.log, [("add_lead", "L1", "m1")])


if __name__ == "__main__":
    unittest.main()
