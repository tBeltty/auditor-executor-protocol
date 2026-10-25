"""Tests for lead handling, scoring, ownership and access control."""

import copy
import unittest

from crm import CRM, DuplicateLeadError


def make_crm(capacity=3):
    return CRM([
        {"id": "r1", "role": "rep", "capacity": capacity},
        {"id": "r2", "role": "rep", "capacity": capacity},
        {"id": "m1", "role": "manager", "capacity": 0},
    ])


def snapshot(crm):
    return copy.deepcopy(crm.leads), copy.deepcopy(crm.opps), list(crm.log)


class ActorCheckTest(unittest.TestCase):
    def test_unknown_actor_rejected_first_in_add_lead(self):
        crm = make_crm()
        with self.assertRaises(PermissionError):
            crm.add_lead("not-an-email", "", "nope", "ghost")

    def test_unknown_actor_rejected_in_qualify(self):
        crm = make_crm()
        with self.assertRaises(PermissionError):
            crm.qualify("L404", "ghost")

    def test_non_string_actor_rejected(self):
        crm = make_crm()
        with self.assertRaises(PermissionError):
            crm.add_lead("a@b.com", "A", "web", None)

    def test_manager_is_known_user(self):
        crm = make_crm()
        lead_id = crm.add_lead("a@b.com", "A", "web", "m1")
        self.assertEqual(lead_id, "L1")


class EmailValidationTest(unittest.TestCase):
    def assert_invalid_email(self, email):
        crm = make_crm()
        before = snapshot(crm)
        with self.assertRaises(ValueError):
            crm.add_lead(email, "Name", "web", "r1")
        self.assertEqual(snapshot(crm), before)

    def test_non_string_email(self):
        self.assert_invalid_email(123)

    def test_missing_at(self):
        self.assert_invalid_email("plainaddress.com")

    def test_multiple_at(self):
        self.assert_invalid_email("a@@b.com")

    def test_empty_local_part(self):
        self.assert_invalid_email("@b.com")
        self.assert_invalid_email("   @b.com")

    def test_missing_domain(self):
        self.assert_invalid_email("a@")

    def test_domain_without_dot(self):
        self.assert_invalid_email("a@localhost")

    def test_domain_dot_at_edges(self):
        self.assert_invalid_email("a@.com")
        self.assert_invalid_email("a@com.")

    def test_email_normalized_and_trimmed(self):
        crm = make_crm()
        lead_id = crm.add_lead("  Alice@Example.COM ", "  Alice  ", "web", "r1")
        lead = crm.leads[lead_id]
        self.assertEqual(lead["email"], "alice@example.com")
        self.assertEqual(lead["name"], "Alice")

    def test_email_with_inner_dot_in_domain_is_valid(self):
        crm = make_crm()
        lead_id = crm.add_lead("a@mail.example.co.uk", "A", "web", "r1")
        self.assertEqual(crm.leads[lead_id]["email"], "a@mail.example.co.uk")


class NameAndSourceTest(unittest.TestCase):
    def test_non_string_name(self):
        crm = make_crm()
        with self.assertRaises(ValueError):
            crm.add_lead("a@b.com", None, "web", "r1")

    def test_blank_name(self):
        crm = make_crm()
        with self.assertRaises(ValueError):
            crm.add_lead("a@b.com", "   ", "web", "r1")

    def test_invalid_source(self):
        crm = make_crm()
        with self.assertRaises(ValueError):
            crm.add_lead("a@b.com", "A", "cold-call", "r1")

    def test_name_checked_before_source(self):
        crm = make_crm()
        with self.assertRaises(ValueError):
            crm.add_lead("a@b.com", "", "cold-call", "r1")

    def test_nothing_logged_on_failure(self):
        crm = make_crm()
        with self.assertRaises(ValueError):
            crm.add_lead("a@b.com", "A", "nope", "r1")
        self.assertEqual(crm.log, [])
        self.assertEqual(crm.leads, {})


class DuplicateTest(unittest.TestCase):
    def test_duplicate_detection_is_case_insensitive(self):
        crm = make_crm()
        first = crm.add_lead("Dup@Example.com", "A", "web", "r1")
        before = snapshot(crm)
        with self.assertRaises(DuplicateLeadError) as ctx:
            crm.add_lead("  dup@example.COM ", "B", "referral", "r1")
        self.assertEqual(ctx.exception.existing_id, first)
        self.assertEqual(snapshot(crm), before)

    def test_duplicate_checked_after_source_validation(self):
        crm = make_crm()
        crm.add_lead("dup@example.com", "A", "web", "r1")
        with self.assertRaises(ValueError):
            crm.add_lead("dup@example.com", "B", "bogus", "r1")

    def test_failed_creation_does_not_consume_id(self):
        crm = make_crm()
        with self.assertRaises(ValueError):
            crm.add_lead("bad", "A", "web", "r1")
        self.assertEqual(crm.add_lead("a@b.com", "A", "web", "r1"), "L1")
        self.assertEqual(crm.add_lead("c@d.com", "C", "web", "r1"), "L2")


class ScoreTest(unittest.TestCase):
    def score_for(self, email, source):
        crm = make_crm()
        lead_id = crm.add_lead(email, "A", source, "r1")
        return crm.leads[lead_id]["score"]

    def test_web_freemail(self):
        self.assertEqual(self.score_for("a@gmail.com", "web"), 10)

    def test_web_corporate(self):
        self.assertEqual(self.score_for("a@corp.com", "web"), 25)

    def test_referral_freemail(self):
        self.assertEqual(self.score_for("a@yahoo.com", "referral"), 30)

    def test_referral_corporate(self):
        self.assertEqual(self.score_for("a@corp.com", "referral"), 45)

    def test_event_freemail(self):
        self.assertEqual(self.score_for("a@outlook.com", "event"), 20)

    def test_event_corporate(self):
        self.assertEqual(self.score_for("a@corp.com", "event"), 35)


class LeadRecordTest(unittest.TestCase):
    def test_lead_fields_and_log(self):
        crm = make_crm()
        lead_id = crm.add_lead("a@corp.com", " Alice ", "referral", "r1")
        self.assertEqual(lead_id, "L1")
        self.assertEqual(
            crm.leads[lead_id],
            {
                "id": "L1",
                "email": "a@corp.com",
                "name": "Alice",
                "source": "referral",
                "score": 45,
                "owner": "r1",
                "status": "new",
            },
        )
        self.assertEqual(crm.log, [("add_lead", "L1", "r1")])


class OwnershipTest(unittest.TestCase):
    def test_lowest_load_gets_new_lead(self):
        crm = make_crm()
        first = crm.add_lead("a@b.com", "A", "web", "r1")
        second = crm.add_lead("c@d.com", "C", "web", "r1")
        third = crm.add_lead("e@f.com", "E", "web", "r1")
        self.assertEqual(crm.leads[first]["owner"], "r1")
        self.assertEqual(crm.leads[second]["owner"], "r2")
        self.assertEqual(crm.leads[third]["owner"], "r1")

    def test_ties_use_smallest_id_in_string_order(self):
        crm = CRM([
            {"id": "r2", "role": "rep", "capacity": 5},
            {"id": "r10", "role": "rep", "capacity": 5},
            {"id": "m1", "role": "manager", "capacity": 5},
        ])
        lead_id = crm.add_lead("a@b.com", "A", "web", "r2")
        self.assertEqual(crm.leads[lead_id]["owner"], "r10")

    def test_managers_never_receive_work(self):
        crm = CRM([{"id": "m1", "role": "manager", "capacity": 10}])
        lead_id = crm.add_lead("a@b.com", "A", "web", "m1")
        self.assertIsNone(crm.leads[lead_id]["owner"])

    def test_full_reps_send_lead_to_queue(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1}])
        first = crm.add_lead("a@b.com", "A", "web", "r1")
        second = crm.add_lead("c@d.com", "C", "web", "r1")
        self.assertEqual(crm.leads[first]["owner"], "r1")
        self.assertIsNone(crm.leads[second]["owner"])

    def test_load_counts_new_and_qualified_leads(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        crm.add_lead("a@b.com", "A", "referral", "r1")
        crm.qualify("L1", "r1")
        self.assertEqual(crm.leads["L1"]["status"], "qualified")
        second = crm.add_lead("c@d.com", "C", "web", "r1")
        self.assertIsNone(crm.leads[second]["owner"])


class QualifyTest(unittest.TestCase):
    def test_unknown_lead(self):
        crm = make_crm()
        with self.assertRaises(ValueError):
            crm.qualify("L99", "r1")

    def test_non_owner_cannot_qualify(self):
        crm = make_crm()
        crm.add_lead("a@corp.com", "A", "referral", "r1")
        before = snapshot(crm)
        with self.assertRaises(PermissionError):
            crm.qualify("L1", "r2")
        self.assertEqual(snapshot(crm), before)

    def test_permission_checked_before_status(self):
        crm = make_crm()
        crm.add_lead("a@corp.com", "A", "referral", "r1")
        crm.qualify("L1", "r1")
        crm.convert("L1", 500, "r1")
        with self.assertRaises(PermissionError):
            crm.qualify("L1", "r2")

    def test_manager_can_qualify(self):
        crm = make_crm()
        crm.add_lead("a@corp.com", "A", "referral", "r1")
        crm.qualify("L1", "m1")
        self.assertEqual(crm.leads["L1"]["status"], "qualified")

    def test_low_score_rejected(self):
        crm = make_crm()
        crm.add_lead("a@gmail.com", "A", "web", "r1")
        before = snapshot(crm)
        with self.assertRaises(ValueError):
            crm.qualify("L1", "r1")
        self.assertEqual(crm.leads["L1"]["status"], "new")
        self.assertEqual(snapshot(crm), before)

    def test_success_sets_status_and_logs(self):
        crm = make_crm()
        crm.add_lead("a@corp.com", "A", "event", "r1")
        crm.qualify("L1", "r1")
        self.assertEqual(crm.leads["L1"]["status"], "qualified")
        self.assertEqual(crm.log[-1], ("qualify", "L1", "r1"))

    def test_not_new_rejected(self):
        crm = make_crm()
        crm.add_lead("a@corp.com", "A", "referral", "r1")
        crm.qualify("L1", "r1")
        with self.assertRaises(ValueError):
            crm.qualify("L1", "r1")


if __name__ == "__main__":
    unittest.main()
