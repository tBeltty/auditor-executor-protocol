"""Unit tests for crm.add_lead, qualify and convert."""

import unittest

from crm import CRM, DuplicateLeadError


def make_crm(reps=None):
    if reps is None:
        reps = [
            {"id": "r1", "role": "rep", "capacity": 3},
            {"id": "r2", "role": "rep", "capacity": 3},
            {"id": "m1", "role": "manager", "capacity": 0},
        ]
    return CRM(reps)


class AddLeadValidationTests(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()

    def test_unknown_actor_raises_and_logs_nothing(self):
        with self.assertRaises(PermissionError):
            self.crm.add_lead("a@b.com", "Ann", "web", "nobody")
        self.assertEqual(self.crm.leads, {})
        self.assertEqual(self.crm.log, [])

    def test_email_must_be_str(self):
        for bad in (None, 123, True, ["a@b.com"]):
            with self.assertRaises(ValueError):
                self.crm.add_lead(bad, "Ann", "web", "r1")

    def test_email_needs_exactly_one_at(self):
        for bad in ("noats.com", "a@@b.com", "a@b@c.com", "@b.com", "a@", ""):
            with self.assertRaises(ValueError):
                self.crm.add_lead(bad, "Ann", "web", "r1")

    def test_email_local_part_non_empty(self):
        with self.assertRaises(ValueError):
            self.crm.add_lead("@example.com", "Ann", "web", "r1")

    def test_email_domain_dot_rules(self):
        bad = ["a@b", "a@.b", "a@b.", "a@.com"]
        for email in bad:
            with self.assertRaises(ValueError, msg=email):
                self.crm.add_lead(email, "Ann", "web", "r1")
        # valid: dot in the middle of the domain
        ok = ["a@b.c", "a@sub.b.co", "a@x.y.z"]
        for email in ok:
            self.crm.add_lead(email, "Ann", "web", "r1")

    def test_email_is_normalized(self):
        self.crm.add_lead("  Foo.Bar@Example.COM ", "Ann", "web", "r1")
        lead = self.crm.leads["L1"]
        self.assertEqual(lead["email"], "foo.bar@example.com")

    def test_name_rules(self):
        with self.assertRaises(ValueError):
            self.crm.add_lead("a@b.com", None, "web", "r1")
        with self.assertRaises(ValueError):
            self.crm.add_lead("a@b.com", 42, "web", "r1")
        with self.assertRaises(ValueError):
            self.crm.add_lead("a@b.com", "   ", "web", "r1")
        self.crm.add_lead("a@b.com", "  Ann  ", "web", "r1")
        self.assertEqual(self.crm.leads["L1"]["name"], "Ann")

    def test_source_rules(self):
        with self.assertRaises(ValueError):
            self.crm.add_lead("a@b.com", "Ann", "email", "r1")
        with self.assertRaises(ValueError):
            self.crm.add_lead("a@b.com", "Ann", None, "r1")
        self.crm.add_lead("a@b.com", "Ann", "referral", "r1")

    def test_duplicate_email_raises_with_existing_id(self):
        first = self.crm.add_lead("a@b.com", "Ann", "web", "r1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            self.crm.add_lead(" A@B.com ", "Bob", "event", "r1")
        self.assertEqual(ctx.exception.existing_id, first)
        # nothing extra was logged or created
        self.assertEqual(len(self.crm.leads), 1)
        self.assertEqual(len(self.crm.log), 1)

    def test_duplicate_only_after_other_checks_pass(self):
        # invalid source + duplicate email -> ValueError (source checked first)
        self.crm.add_lead("a@b.com", "Ann", "web", "r1")
        with self.assertRaises(ValueError):
            self.crm.add_lead("a@b.com", "Bob", "nope", "r1")

    def test_scores(self):
        self.crm.add_lead("a@gmail.com", "A", "web", "r1")       # 10
        self.crm.add_lead("b@yahoo.com", "B", "referral", "r1")  # 30
        self.crm.add_lead("c@outlook.com", "C", "event", "r1")   # 20
        self.crm.add_lead("d@corp.io", "D", "web", "r1")         # 10 + 15
        self.crm.add_lead("e@gmail.com", "E", "referral", "r1")  # 30, no bonus
        expected = {"L1": 10, "L2": 30, "L3": 20, "L4": 25, "L5": 30}
        for lid, score in expected.items():
            self.assertEqual(self.crm.leads[lid]["score"], score)

    def test_sequential_ids_and_log(self):
        self.crm.add_lead("a@b.com", "A", "web", "r1")
        self.crm.add_lead("c@d.org", "B", "event", "r2")
        self.assertEqual(list(self.crm.leads), ["L1", "L2"])
        self.assertEqual(
            self.crm.log,
            [("add_lead", "L1", "r1"), ("add_lead", "L2", "r2")],
        )


class OwnerAssignmentTests(unittest.TestCase):
    def test_lowest_load_rep_wins_and_ties_broken_by_smallest_id(self):
        crm = make_crm()  # r1, r2 both load 0 capacity 3
        self.assertEqual(crm.add_lead("a@b.com", "A", "web", "m1"), "L1")
        self.assertEqual(crm.leads["L1"]["owner"], "r1")  # tie -> r1
        self.assertEqual(crm.add_lead("b@b.com", "B", "web", "m1"), "L2")
        self.assertEqual(crm.leads["L2"]["owner"], "r2")  # tie -> r2
        self.assertEqual(crm.add_lead("c@b.com", "C", "web", "m1"), "L3")
        self.assertEqual(crm.leads["L3"]["owner"], "r1")  # r1 back to load 1? no: r1=1, r2=1 tie -> r1

    def test_skips_reps_at_capacity(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1},
                   {"id": "r2", "role": "rep", "capacity": 1},
                   {"id": "m1", "role": "manager", "capacity": 0}])
        crm.add_lead("a@b.com", "A", "web", "r1")  # r1 load 1
        crm.add_lead("b@b.com", "B", "web", "r1")  # r2
        crm.add_lead("c@b.com", "C", "web", "r1")  # nobody free -> queued
        self.assertEqual(crm.leads["L3"]["owner"], None)
        # queue is FIFO: next add also queues behind L3
        crm.add_lead("d@b.com", "D", "web", "r1")
        self.assertEqual(crm.leads["L4"]["owner"], None)

    def test_managers_never_receive_work(self):
        crm = CRM([{"id": "m1", "role": "manager", "capacity": 5},
                   {"id": "r1", "role": "rep", "capacity": 5}])
        crm.add_lead("a@b.com", "A", "web", "m1")
        self.assertEqual(crm.leads["L1"]["owner"], "r1")

    def test_load_counts_leads_and_open_opps(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 4},
                   {"id": "r2", "role": "rep", "capacity": 4},
                   {"id": "m1", "role": "manager", "capacity": 0}])
        # r1: lead L1 (new) + opp O1 (prospect) = 2 after conversion
        crm.add_lead("a@corp.io", "A", "referral", "r1")     # L1 -> r1
        crm.add_lead("b@corp.io", "B", "referral", "r1")     # L2 -> r2
        crm.qualify("L1", "r1")
        crm.convert("L1", 100, "r1")                          # O1 -> r1
        # r1 load = O1 = 1; r2 load = L2 = 1 -> tie -> r1
        crm.add_lead("c@corp.io", "C", "referral", "r1")
        self.assertEqual(crm.leads["L3"]["owner"], "r1")
        crm.add_lead("d@corp.io", "D", "referral", "r1")      # r1 load 2, r2 load 1 -> r2
        self.assertEqual(crm.leads["L4"]["owner"], "r2")


class QualifyTests(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        self.crm.add_lead("a@gmail.com", "A", "referral", "r1")  # L1, score 30, owner r1
        self.crm.add_lead("b@gmail.com", "B", "web", "r1")       # L2, score 10, owner r2? r1... see below

    def test_happy_path(self):
        self.crm.qualify("L1", "r1")
        self.assertEqual(self.crm.leads["L1"]["status"], "qualified")
        self.assertIn(("qualify", "L1", "r1"), self.crm.log)

    def test_unknown_lead(self):
        with self.assertRaises(ValueError):
            self.crm.qualify("L99", "r1")

    def test_other_rep_cannot_qualify(self):
        # L1 owner is r1; r2 is neither owner nor manager
        with self.assertRaises(PermissionError):
            self.crm.qualify("L1", "r2")
        self.assertEqual(self.crm.leads["L1"]["status"], "new")

    def test_manager_can_qualify(self):
        self.crm.qualify("L1", "m1")
        self.assertEqual(self.crm.leads["L1"]["status"], "qualified")

    def test_cannot_qualify_twice(self):
        self.crm.qualify("L1", "r1")
        with self.assertRaises(ValueError):
            self.crm.qualify("L1", "r1")

    def test_low_score_cannot_qualify(self):
        crm = make_crm()
        crm.add_lead("b@gmail.com", "B", "web", "r1")  # score 10
        with self.assertRaises(ValueError):
            crm.qualify("L1", "r1")
        self.assertEqual(crm.leads["L1"]["status"], "new")

    def test_unknown_actor_checked_before_existence(self):
        with self.assertRaises(PermissionError):
            self.crm.qualify("L99", "ghost")

    def test_failed_qualify_changes_nothing(self):
        before = dict(self.crm.leads["L1"])
        with self.assertRaises(PermissionError):
            self.crm.qualify("L1", "r2")
        self.assertEqual(self.crm.leads["L1"], before)
        self.assertNotIn(("qualify", "L1", "r2"), self.crm.log)


class ConvertTests(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        self.crm.add_lead("a@gmail.com", "A", "referral", "r1")  # L1 owner r1
        self.crm.qualify("L1", "r1")

    def test_happy_path(self):
        opp_id = self.crm.convert("L1", 1000, "r1")
        self.assertEqual(opp_id, "O1")
        opp = self.crm.opps["O1"]
        self.assertEqual(opp, {"id": "O1", "lead_id": "L1", "owner": "r1",
                               "amount": 1000, "original_amount": 1000,
                               "stage": "prospect"})
        self.assertEqual(self.crm.leads["L1"]["status"], "converted")
        self.assertIn(("convert", "O1", "r1"), self.crm.log)

    def test_unknown_lead(self):
        with self.assertRaises(ValueError):
            self.crm.convert("L99", 100, "r1")

    def test_amount_must_be_positive_int_not_bool(self):
        for bad in (0, -5, True, False, 10.0, "100", None):
            with self.assertRaises(ValueError, msg=repr(bad)):
                self.crm.convert("L1", bad, "r1")
        self.assertNotIn("O1", self.crm.opps)

    def test_other_rep_cannot_convert(self):
        with self.assertRaises(PermissionError):
            self.crm.convert("L1", 100, "r2")

    def test_manager_can_convert(self):
        opp_id = self.crm.convert("L1", 100, "m1")
        self.assertEqual(opp_id, "O1")

    def test_must_be_qualified(self):
        self.crm.add_lead("b@corp.io", "B", "referral", "r1")  # L2, status new
        with self.assertRaises(ValueError):
            self.crm.convert("L2", 100, "m1")
        # converted leads cannot convert again
        self.crm.convert("L1", 100, "r1")
        with self.assertRaises(ValueError):
            self.crm.convert("L1", 100, "m1")

    def test_unowned_lead_cannot_convert_even_by_rep(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 0},
                   {"id": "m1", "role": "manager", "capacity": 0}])
        crm.add_lead("a@b.com", "A", "referral", "m1")  # queued, owner None
        crm.qualify("L1", "m1")                          # manager may qualify
        with self.assertRaises(ValueError):
            crm.convert("L1", 100, "m1")                 # still no owner

    def test_ids_count_successful_conversions(self):
        self.assertEqual(self.crm.convert("L1", 100, "r1"), "O1")
        self.crm.add_lead("b@corp.io", "B", "referral", "r1")  # L2 -> r2 (r1 busy)
        self.crm.qualify("L2", "r2")
        self.assertEqual(self.crm.convert("L2", 100, "r2"), "O2")
        self.crm.add_lead("c@corp.io", "C", "referral", "r1")  # tie at load 1 -> r1
        self.crm.qualify("L3", "r1")
        self.assertEqual(self.crm.convert("L3", 100, "r1"), "O3")

    def test_failed_convert_leaves_lead_qualified(self):
        with self.assertRaises(ValueError):
            self.crm.convert("L1", 0, "r1")
        self.assertEqual(self.crm.leads["L1"]["status"], "qualified")
        self.assertEqual(self.crm.opps, {})


if __name__ == "__main__":
    unittest.main()
