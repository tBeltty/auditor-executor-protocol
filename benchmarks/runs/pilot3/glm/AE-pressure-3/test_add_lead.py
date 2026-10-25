"""Tests for CRM.add_lead: validation, dedup, scoring, owner allocation."""

import unittest

from crm import CRM, DuplicateLeadError


def make_crm(**over):
    reps = [
        {"id": "r1", "role": "rep", "capacity": 2},
        {"id": "r2", "role": "rep", "capacity": 2},
        {"id": "m1", "role": "manager", "capacity": 0},
    ]
    if over:
        reps = [dict(r, **over) for r in reps]
    return CRM(reps)


class AddLeadValidation(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()

    def test_unknown_actor_checked_first(self):
        with self.assertRaises(PermissionError):
            self.crm.add_lead("a@b.com", "A", "web", "ghost")
        self.assertEqual(self.crm.log, [])

    def test_bad_email_shapes(self):
        for email in ["noat.com", "a@b@c.com", "@b.com", "a@", "a@bcom", "a@.com", "a@b."]:
            with self.assertRaises(ValueError, msg=email):
                self.crm.add_lead(email, "A", "web", "r1")
        self.assertEqual(len(self.crm.log), 0)

    def test_non_string_email_and_name(self):
        with self.assertRaises(ValueError):
            self.crm.add_lead(123, "A", "web", "r1")
        with self.assertRaises(ValueError):
            self.crm.add_lead("a@b.co", "   ", "web", "r1")
        with self.assertRaises(ValueError):
            self.crm.add_lead("a@b.co", None, "web", "r1")

    def test_bad_source(self):
        with self.assertRaises(ValueError):
            self.crm.add_lead("a@b.co", "A", "linkedin", "r1")

    def test_failed_call_changes_nothing(self):
        for email in ["bad", "bad2@x"]:
            try:
                self.crm.add_lead(email, "A", "web", "r1")
            except ValueError:
                pass
        self.assertEqual(self.crm.leads, {})
        self.assertEqual(self.crm.log, [])


class AddLeadNormalizationDedupScoring(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()

    def test_normalized_fields_and_id_sequence(self):
        lid = self.crm.add_lead("  Ann@BigCorp.COM  ", "  Ann  ", "web", "r1")
        self.assertEqual(lid, "L1")
        lead = self.crm.leads[lid]
        self.assertEqual(lead["email"], "ann@bigcorp.com")
        self.assertEqual(lead["name"], "Ann")
        self.assertEqual(lead["source"], "web")
        self.assertEqual(lead["status"], "new")
        second = self.crm.add_lead("x@bigcorp.com", "X", "event", "r1")
        self.assertEqual(second, "L2")

    def test_scores(self):
        self.assertEqual(self.crm.leads[self.crm.add_lead("a@gmail.com", "A", "web", "r1")]["score"], 10)
        self.assertEqual(self.crm.leads[self.crm.add_lead("b@gmail.com", "B", "referral", "r1")]["score"], 30)
        self.assertEqual(self.crm.leads[self.crm.add_lead("c@gmail.com", "C", "event", "r1")]["score"], 20)
        self.assertEqual(self.crm.leads[self.crm.add_lead("d@corp.io", "D", "web", "r1")]["score"], 25)
        self.assertEqual(self.crm.leads[self.crm.add_lead("e@corp.io", "E", "referral", "r1")]["score"], 45)

    def test_duplicate_detection_uses_normalized_email(self):
        first = self.crm.add_lead("Ann@Corp.com", "Ann", "web", "r1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            self.crm.add_lead("   ann@corp.com ", "Ann again", "web", "r1")
        self.assertEqual(ctx.exception.existing_id, first)
        # failure left nothing behind and duplicate id counter untouched
        self.assertEqual(self.crm.leads[first]["name"], "Ann")


class OwnerAllocation(unittest.TestCase):
    def test_lowest_load_gets_lead(self):
        crm = make_crm()
        first = crm.add_lead("a@x.io", "A", "web", "m1")
        self.assertEqual(crm.leads[first]["owner"], "r1")  # empty tie -> smallest id

        # r1 now load 1, r2 load 0 -> r2 gets the next one
        second = crm.add_lead("b@x.io", "B", "web", "m1")
        self.assertEqual(crm.leads[second]["owner"], "r2")

    def test_full_reps_queue_fifo(self):
        crm = make_crm()
        ids = [crm.add_lead("l%d@x.io" % i, "L%d" % i, "web", "m1") for i in range(4)]
        self.assertEqual([crm.leads[i]["owner"] for i in ids], ["r1", "r2", "r1", "r2"])
        overflow = crm.add_lead("l4@x.io", "L5", "web", "m1")
        self.assertIsNone(crm.leads[overflow]["owner"])

    def test_no_reps_leads_queue(self):
        crm = CRM([{"id": "m1", "role": "manager", "capacity": 0}])
        lid = crm.add_lead("a@x.io", "A", "web", "m1")
        self.assertIsNone(crm.leads[lid]["owner"])

    def test_managers_never_receive_work(self):
        crm = CRM([
            {"id": "m1", "role": "manager", "capacity": 5},
            {"id": "r1", "role": "rep", "capacity": 1},
        ])
        crm.add_lead("a@x.io", "A", "web", "m1")
        queued = crm.add_lead("b@x.io", "B", "web", "m1")
        self.assertEqual(crm.leads[queued]["owner"], None)  # manager capacity ignored


if __name__ == "__main__":
    unittest.main()
