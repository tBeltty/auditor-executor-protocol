"""Unit tests for CRM.add_lead: validation, ids, scores, dispatch and log."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crm import CRM  # noqa: E402
from crm import DuplicateLeadError  # noqa: E402,F401  (re-exported for users)
from crm_test_support import add_lead, make_crm  # noqa: E402
from crm_test_support import convert_lead, walk_to_final  # noqa: E402,E501


class AddLeadEmailValidationTests(unittest.TestCase):
    def test_valid_add_normalizes_and_stores_lead(self):
        crm = make_crm()
        lead_id = crm.add_lead("  Alice@Example.COM ", "  Alice Smith ", "web", "m1")
        self.assertEqual(lead_id, "L1")
        lead = crm.leads["L1"]
        self.assertEqual(lead["id"], "L1")
        self.assertEqual(lead["email"], "alice@example.com")
        self.assertEqual(lead["name"], "Alice Smith")
        self.assertEqual(lead["source"], "web")
        self.assertEqual(lead["score"], 25)  # web (10) + non-common domain (15)
        self.assertEqual(lead["status"], "new")
        self.assertEqual(lead["owner"], "r1")

    def test_scores_per_source_and_domain(self):
        cases = [
            ("bob@gmail.com", "web", 10),
            ("bob@gmail.com", "referral", 30),
            ("bob@gmail.com", "event", 20),
            ("bob@example.com", "web", 25),
            ("bob@example.com", "referral", 45),
            ("bob@example.com", "event", 35),
        ]
        for email, source, expected in cases:
            with self.subTest(email=email, source=source):
                crm = make_crm()
                lead_id = crm.add_lead(email, "Bob", source, "m1")
                self.assertEqual(crm.leads[lead_id]["score"], expected)

    def test_emails_invalid_formats_fail(self):
        bad_emails = [
            "no-at-sign",
            "two@@x.com",
            "a@b@c.com",
            "@nolocal.com",
            "a@",           # empty domain
            "nodot@host",   # domain without a dot
            "a@.host",      # dot may not be the first domain char
            "a@host.",      # dot may not be the last domain char
        ]
        for email in bad_emails:
            with self.subTest(email=email):
                crm = make_crm()
                with self.assertRaises(ValueError):
                    crm.add_lead(email, "Bob", "web", "m1")
                self.assertEqual(crm.leads, {})
                self.assertEqual(crm.log, [])

    def test_domain_dot_edge_cases(self):
        # An inner dot always satisfies the rule, even when another dot
        # touches an end; "b.c." contains "." at index 1, which is neither
        # the first nor the last character of the domain.
        for email in ("a@b.c.", "a@x.y.z", "a@b.cc", "a@sub.example.co"):
            with self.subTest(email=email):
                crm = make_crm()
                lead_id = crm.add_lead(email, "A", "web", "m1")
                self.assertIn(lead_id, crm.leads)

    def test_non_string_email_raises_value_error(self):
        crm = make_crm()
        for bad in (123, None, ["a@b.com"], 1.5):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    crm.add_lead(bad, "Bob", "web", "m1")
        self.assertEqual(crm.log, [])


class AddLeadOtherValidationTests(unittest.TestCase):
    def test_name_must_be_non_empty_string_after_strip(self):
        crm = make_crm()
        for bad in (None, 42, ["Bob"], "", "   "):
            with self.subTest(name=bad):
                with self.assertRaises(ValueError):
                    crm.add_lead("bob@example.com", bad, "web", "m1")
        self.assertEqual(crm.log, [])

    def test_source_must_be_one_of_three_literals(self):
        crm = make_crm()
        for bad in ("WEB", "newsletter", "", None, 3):
            with self.subTest(source=bad):
                with self.assertRaises(ValueError):
                    crm.add_lead("bob@example.com", "Bob", bad, "m1")
        self.assertEqual(crm.log, [])

    def test_unknown_actor_checked_first_even_with_bad_email(self):
        crm = make_crm()
        for actor in ("ghost", "", None, 5):
            with self.subTest(actor=actor):
                with self.assertRaises(PermissionError):
                    crm.add_lead("bad-email", "B", "web", actor)
        self.assertEqual(crm.leads, {})
        self.assertEqual(crm.log, [])


class AddLeadIdentityAndLogTests(unittest.TestCase):
    def test_ids_count_successful_creations_and_failures_are_free(self):
        crm = make_crm()
        with self.assertRaises(ValueError):
            crm.add_lead("bad-email", "B", "web", "m1")
        first = crm.add_lead("a@example.com", "A", "web", "m1")
        self.assertEqual(first, "L1")
        second = crm.add_lead("b@example.com", "B", "web", "m1")
        self.assertEqual(second, "L2")
        self.assertEqual(
            crm.log,
            [("add_lead", "L1", "m1"), ("add_lead", "L2", "m1")],
        )

    def test_duplicate_normalized_email_raises_with_existing_id(self):
        crm = make_crm()
        first = crm.add_lead("bob@gmail.com", "Bob", "web", "m1")
        for twister in ("bob@gmail.com", "  BOB@GMAIL.COM ", "bob@gmail.com "):
            with self.subTest(email=twister):
                with self.assertRaises(DuplicateLeadError) as ctx:
                    crm.add_lead(twister, "Bob 2", "referral", "m1")
                self.assertEqual(ctx.exception.existing_id, first)
        self.assertEqual(len(crm.leads), 1)
        self.assertEqual(crm.log, [("add_lead", first, "m1")])

    def test_duplicate_attempt_does_not_consume_an_id(self):
        crm = make_crm()
        crm.add_lead("bob@gmail.com", "Bob", "web", "m1")
        with self.assertRaises(DuplicateLeadError):
            crm.add_lead("bob@gmail.com", "Bob", "web", "m1")
        second = crm.add_lead("ann@gmail.com", "Ann", "web", "m1")
        self.assertEqual(second, "L2")

    def test_leads_of_same_local_part_on_different_domains_are_distinct(self):
        crm = make_crm()
        a = crm.add_lead("bob@gmail.com", "Bob", "web", "m1")
        b = crm.add_lead("bob@example.com", "Bob", "web", "m1")
        self.assertEqual(b, "L2")
        self.assertEqual(crm.leads[a]["owner"], "r1")
        self.assertEqual(crm.leads[b]["owner"], "r2")


class OwnerDispatchTests(unittest.TestCase):
    def test_lowest_load_wins_with_smallest_id_tiebreak(self):
        # Capacities: r1=2, r2=1, r3=3. Expect r1, r2, r3, r1.
        crm = make_crm()
        owners = []
        for n in range(4):
            lead_id = add_lead(crm, n)
            owners.append(crm.leads[lead_id]["owner"])
        self.assertEqual(owners, ["r1", "r2", "r3", "r1"])
        self.assertEqual([entry[0] for entry in crm.log], ["add_lead"] * 4)

    def test_reps_at_capacity_dispatch_none_and_queue_fifo(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 0},
            {"id": "m1", "role": "manager", "capacity": 5},
        ])
        kept = crm.add_lead("a@a.com", "A", "web", "m1")
        queued = crm.add_lead("b@b.com", "B", "web", "m1")
        self.assertEqual(crm.leads[kept]["owner"], "r1")
        self.assertIsNone(crm.leads[queued]["owner"])
        self.assertEqual(queued, "L2")
        self.assertEqual(crm.leads[queued]["status"], "new")

    def test_managers_never_own_work_even_with_capacity(self):
        crm = CRM([
            {"id": "rep1", "role": "rep", "capacity": 5},
            {"id": "boss", "role": "manager", "capacity": 99},
        ])
        for n in range(3):
            lead_id = crm.add_lead("l%d@x.com" % n, "L", "web", "boss")
            self.assertEqual(crm.leads[lead_id]["owner"], "rep1")

    def test_open_opportunities_count_toward_load(self):
        # A converted lead stops counting as a lead but its open opportunity
        # consumes the rep's capacity for further dispatch.
        crm = make_crm()
        lead_id = add_lead(crm, 0)                    # -> r1 (load 1)
        crm.qualify(lead_id, "r1")
        opp_id = crm.convert(lead_id, 100, "r1")      # load stays 1 (opp open)
        second = add_lead(crm, 1)                     # goes to r2 (load 0)
        self.assertEqual(crm.leads[second]["owner"], "r2")
        walk_to_final(crm, opp_id, "r1")              # r1 load drops to 0
        third = add_lead(crm, 2)
        self.assertEqual(crm.leads[third]["owner"], "r1")


if __name__ == "__main__":
    unittest.main()
