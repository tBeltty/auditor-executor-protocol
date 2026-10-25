"""Tests for CRM.add_lead: validation, dedup, scoring, assignment, queueing."""

import copy
import unittest

from crm import CRM, DuplicateLeadError


def make_crm():
    return CRM([
        {"id": "r1", "role": "rep", "capacity": 2},
        {"id": "r2", "role": "rep", "capacity": 2},
        {"id": "m1", "role": "manager", "capacity": 0},
    ])


class TestAddLeadValidation(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()

    def test_unknown_actor_checked_first(self):
        with self.assertRaises(PermissionError):
            self.crm.add_lead("bad-email", "", "nope", "ghost")
        self.assertEqual(self.crm.leads, {})
        self.assertEqual(self.crm.log, [])

    def test_email_must_be_str(self):
        for bad in (None, 5, ["a@b.com"], 3.2, b"a@b.com"):
            with self.assertRaises(ValueError):
                self.crm.add_lead(bad, "Ann", "web", "m1")
        self.assertEqual(self.crm.log, [])

    def test_email_needs_exactly_one_at_and_nonempty_local(self):
        for bad in ("ab.com", "a@@b.com", "a@b@c.com", "@b.com", "a@", "@"):
            with self.assertRaises(ValueError):
                self.crm.add_lead(bad, "Ann", "web", "m1")
        self.assertEqual(self.crm.log, [])

    def test_email_domain_needs_inner_dot(self):
        for bad in ("a@b", "a@b.", "a@.b", "a@.com", "a@com."):
            with self.assertRaises(ValueError):
                self.crm.add_lead(bad, "Ann", "web", "m1")
        self.assertEqual(self.crm.log, [])
        # a short domain with an inner dot is fine
        self.assertEqual(self.crm.add_lead("a@b.c", "Ann", "web", "m1"), "L1")

    def test_email_is_normalized(self):
        lead_id = self.crm.add_lead("  MiXed@Example.COM  ", "Ann", "web", "m1")
        self.assertEqual(self.crm.leads[lead_id]["email"], "mixed@example.com")
        # duplicate detection works on the normalized form
        with self.assertRaises(DuplicateLeadError):
            self.crm.add_lead("MIXED@example.com", "Other", "web", "m1")

    def test_name_must_be_nonempty_after_strip(self):
        for bad in ("", "   ", "\t", None, 7):
            with self.assertRaises(ValueError):
                self.crm.add_lead("a@b.com", bad, "web", "m1")
        self.assertEqual(self.crm.log, [])

    def test_source_must_be_allowed(self):
        for bad in ("WEB", "phone", "", None, "web "):
            with self.assertRaises(ValueError):
                self.crm.add_lead("a@b.com", "Ann", bad, "m1")
        self.assertEqual(self.crm.log, [])

    def test_check_order_email_name_source_duplicate(self):
        # bad email wins over bad name
        with self.assertRaises(ValueError):
            self.crm.add_lead("bad", "", "web", "m1")
        self.crm.add_lead("a@b.com", "Ann", "web", "m1")
        # bad name wins over duplicate email
        with self.assertRaises(ValueError):
            self.crm.add_lead("a@b.com", "  ", "web", "m1")
        # bad source wins over duplicate email
        with self.assertRaises(ValueError):
            self.crm.add_lead("a@b.com", "Ann", "x", "m1")
        # finally the duplicate itself
        with self.assertRaises(DuplicateLeadError) as cm:
            self.crm.add_lead("a@b.com", "Ann", "web", "m1")
        self.assertEqual(cm.exception.existing_id, "L1")
        self.assertEqual(len(self.crm.leads), 1)
        self.assertEqual(self.crm.log, [("add_lead", "L1", "m1")])


class TestAddLeadScoringAndAssignment(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()

    def test_scores_by_source_and_domain(self):
        specs = [
            ("a1@gmail.com", "web", 10),
            ("a2@acme.io", "web", 25),
            ("a3@gmail.com", "referral", 30),
            ("a4@acme.io", "referral", 45),
            ("a5@gmail.com", "event", 20),
            ("a6@acme.io", "event", 35),
        ]
        for i, (email, source, expected) in enumerate(specs):
            lead_id = self.crm.add_lead(email, "N%d" % i, source, "m1")
            self.assertEqual(self.crm.leads[lead_id]["score"], expected)

    def test_lead_fields_and_log(self):
        lead_id = self.crm.add_lead("  Ann@Example.COM ", "  Ann  ", "referral", "r1")
        lead = self.crm.leads[lead_id]
        self.assertEqual(lead["id"], lead_id)
        self.assertEqual(lead["email"], "ann@example.com")
        self.assertEqual(lead["name"], "Ann")
        self.assertEqual(lead["source"], "referral")
        self.assertEqual(lead["score"], 45)
        self.assertEqual(lead["owner"], "r1")
        self.assertEqual(lead["status"], "new")
        self.assertEqual(self.crm.log, [("add_lead", lead_id, "r1")])

    def test_lowest_load_with_tie_broken_by_smallest_id_string(self):
        crm = CRM([
            {"id": "r10", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 5},
        ])
        crm.add_lead("a@x.com", "A", "web", "m1")
        self.assertEqual(crm.leads["L1"]["owner"], "r10")  # "r10" < "r2"
        crm.add_lead("b@x.com", "B", "web", "m1")
        self.assertEqual(crm.leads["L2"]["owner"], "r2")
        crm.add_lead("c@x.com", "C", "web", "m1")
        self.assertIsNone(crm.leads["L3"]["owner"])  # everyone full

    def test_managers_never_own(self):
        crm = CRM([{"id": "m1", "role": "manager", "capacity": 5}])
        lead_id = crm.add_lead("a@x.com", "A", "web", "m1")
        self.assertIsNone(crm.leads[lead_id]["owner"])

    def test_zero_capacity_rep_never_owns(self):
        crm = CRM([
            {"id": "r0", "role": "rep", "capacity": 0},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        lead_id = crm.add_lead("a@x.com", "A", "web", "m1")
        self.assertIsNone(crm.leads[lead_id]["owner"])

    def test_load_counts_new_qualified_leads_and_open_opps(self):
        lead = self.crm.add_lead("a@acme.io", "A", "referral", "m1")  # r1 load 1
        self.crm.qualify(lead, "r1")                                  # still 1
        opp = self.crm.convert(lead, 100, "r1")                       # still 1
        # r1 now at capacity 2 -> next lead goes to r2
        other = self.crm.add_lead("b@acme.io", "B", "referral", "m1")
        self.assertEqual(self.crm.leads[other]["owner"], "r2")
        # closing the opp frees r1: it stops counting toward load once final.
        self.crm.advance(opp, "proposal", "r1")
        self.crm.advance(opp, "negotiation", "r1")
        self.crm.advance(opp, "won", "r1")
        third = self.crm.add_lead("c@acme.io", "C", "referral", "m1")
        self.assertEqual(self.crm.leads[third]["owner"], "r1")

    def test_ids_count_successful_creations_only(self):
        self.assertEqual(self.crm.add_lead("a@x.com", "A", "web", "m1"), "L1")
        with self.assertRaises(ValueError):
            self.crm.add_lead("bad", "A", "web", "m1")
        with self.assertRaises(DuplicateLeadError):
            self.crm.add_lead("a@x.com", "A", "web", "m1")
        self.assertEqual(self.crm.add_lead("b@x.com", "B", "web", "m1"), "L2")

    def test_failed_calls_change_nothing(self):
        self.crm.add_lead("a@x.com", "A", "web", "m1")
        before = (copy.deepcopy(self.crm.leads), copy.deepcopy(self.crm.log))
        with self.assertRaises(ValueError):
            self.crm.add_lead("b@", "B", "web", "m1")
        with self.assertRaises(ValueError):
            self.crm.add_lead(42, "B", "web", "m1")
        with self.assertRaises(PermissionError):
            self.crm.add_lead("b@x.com", "B", "web", "ghost")
        with self.assertRaises(DuplicateLeadError):
            self.crm.add_lead("a@x.com", "B", "web", "m1")
        after = (copy.deepcopy(self.crm.leads), copy.deepcopy(self.crm.log))
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
