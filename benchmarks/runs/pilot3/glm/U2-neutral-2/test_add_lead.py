"""Tests for CRM.add_lead: validation, scoring, and owner assignment."""

import unittest

from crm import CRM, DuplicateLeadError


def make_crm(reps=None):
    if reps is None:
        reps = [
            {"id": "r1", "role": "rep", "capacity": 3},
            {"id": "r2", "role": "rep", "capacity": 3},
        ]
    return CRM(reps)


class AddLeadValidationTests(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()

    def test_actor_checked_first(self):
        with self.assertRaises(PermissionError):
            self.crm.add_lead("bad-email", "", "nope", "ghost")

    def test_email_must_be_str(self):
        with self.assertRaises(ValueError):
            self.crm.add_lead(42, "N", "web", "r1")
        with self.assertRaises(ValueError):
            self.crm.add_lead(None, "N", "web", "r1")

    def test_email_normalization_and_single_at(self):
        for bad in ["a@@b.com", "@b.com", "ab.com", "a@b@c.com"]:
            with self.assertRaises(ValueError):
                self.crm.add_lead(bad, "N", "web", "r1")

    def test_email_domain_dot_positions(self):
        for bad in ["a@bc", "a@.bc", "a@bc."]:
            with self.assertRaises(ValueError):
                self.crm.add_lead(bad, "N", "web", "r1")
        # dot in the middle of the domain is fine
        lead_id = self.crm.add_lead("a@b.c", "N", "web", "r1")
        self.assertEqual(lead_id, "L1")

    def test_email_stripped_and_lowered(self):
        self.crm.add_lead("  Ada@Example.COM ", "N", "web", "r1")
        self.assertEqual(self.crm.leads["L1"]["email"], "ada@example.com")

    def test_name_validation(self):
        with self.assertRaises(ValueError):
            self.crm.add_lead("a@b.com", 7, "web", "r1")
        with self.assertRaises(ValueError):
            self.crm.add_lead("a@b.com", "   ", "web", "r1")

    def test_name_is_stripped(self):
        self.crm.add_lead("a@b.com", "  Ada  ", "web", "r1")
        self.assertEqual(self.crm.leads["L1"]["name"], "Ada")

    def test_source_validation(self):
        for source in ["web", "referral", "event"]:
            self.assertIsNotNone(
                self.crm.add_lead("u{}@b.com".format(source), "N", source, "r1")
            )
        with self.assertRaises(ValueError):
            self.crm.add_lead("x@b.com", "N", "cold-call", "r1")

    def test_duplicate_lead(self):
        first = self.crm.add_lead("ada@b.com", "Ada", "web", "r1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            self.crm.add_lead("  ADA@B.COM ", "Other", "referral", "r2")
        self.assertEqual(ctx.exception.existing_id, first)


class AddLeadScoringTests(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()

    def test_scores(self):
        self.crm.add_lead("w@b.com", "N", "web", "r1")
        self.crm.add_lead("r@b.com", "N", "referral", "r1")
        self.crm.add_lead("e@b.com", "N", "event", "r1")
        self.assertEqual(self.crm.leads["L1"]["score"], 25)
        self.assertEqual(self.crm.leads["L2"]["score"], 45)
        self.assertEqual(self.crm.leads["L3"]["score"], 35)

    def test_common_domains_no_bonus(self):
        for domain in ["gmail.com", "yahoo.com", "outlook.com"]:
            self.crm.add_lead("u@{}".format(domain), "N", "web", "r1")
        self.assertEqual(
            [self.crm.leads["L{}".format(n)]["score"] for n in (1, 2, 3)],
            [10, 10, 10],
        )
        self.crm.add_lead("u@acme.co", "N", "web", "r1")
        self.assertEqual(self.crm.leads["L4"]["score"], 25)


class AddLeadAssignmentTests(unittest.TestCase):
    def test_lowest_load_rep_wins_ties_by_smallest_id(self):
        crm = CRM(
            [
                {"id": "r2", "role": "rep", "capacity": 2},
                {"id": "r1", "role": "rep", "capacity": 2},
            ]
        )
        a = crm.add_lead("a@x.com", "A", "web", "r2")
        self.assertEqual(crm.leads[a]["owner"], "r1")  # tie -> smallest id "r1"

    def test_owner_fills_round_robin_by_load(self):
        crm = make_crm()
        ids = [crm.add_lead("u{}@x.com".format(i), "N", "web", "r1") for i in range(4)]
        owners = [crm.leads[i]["owner"] for i in ids]
        # loads: r1=0,r2=0 -> r1; r1=1,r2=0 -> r2; r1=1,r2=1 -> r1; r1=2,r2=1 -> r2
        self.assertEqual(owners, ["r1", "r2", "r1", "r2"])

    def test_queue_when_all_reps_full(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1}])
        first = crm.add_lead("a@x.com", "A", "web", "r1")
        second = crm.add_lead("b@x.com", "B", "web", "r1")
        self.assertEqual(crm.leads[first]["owner"], "r1")
        self.assertIsNone(crm.leads[second]["owner"])
        self.assertEqual(crm._waiting, [second])

    def test_managers_never_own(self):
        crm = CRM(
            [
                {"id": "m1", "role": "manager", "capacity": 5},
                {"id": "r1", "role": "rep", "capacity": 1},
            ]
        )
        crm.add_lead("a@x.com", "A", "web", "m1")
        crm.add_lead("b@x.com", "B", "web", "m1")
        self.assertEqual(crm.leads["L1"]["owner"], "r1")
        self.assertIsNone(crm.leads["L2"]["owner"])

    def test_success_log_and_return(self):
        crm = make_crm()
        lead_id = crm.add_lead("a@x.com", "A", "web", "r1")
        self.assertEqual(lead_id, "L1")
        self.assertEqual(crm.log, [("add_lead", "L1", "r1")])
        self.assertEqual(crm.leads["L1"]["status"], "new")

    def test_failed_call_changes_nothing(self):
        crm = make_crm()
        crm.add_lead("a@x.com", "A", "web", "r1")
        before_log = list(crm.log)
        with self.assertRaises(ValueError):
            crm.add_lead("bad", "A", "web", "r1")
        self.assertEqual(crm.log, before_log)
        self.assertEqual(len(crm.leads), 1)
        # counter not consumed by the failure
        self.assertEqual(crm.add_lead("b@x.com", "B", "web", "r1"), "L2")


if __name__ == "__main__":
    unittest.main()
