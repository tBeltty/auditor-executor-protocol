"""Tests for actor rules, add_lead validation, scoring, and lead routing."""

import unittest

from crm import CRM, DuplicateLeadError


def build(reps=None):
    if reps is None:
        reps = [
            {"id": "r2", "role": "rep", "capacity": 1},
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 9},
        ]
    return CRM([dict(r) for r in reps])


class UnknownActorTests(unittest.TestCase):
    """General rule: unknown actor -> PermissionError, checked first."""

    def setUp(self):
        self.crm = build()
        self.lead_id = self.crm.add_lead("a@acme.com", "A", "referral", "r1")
        self.crm.qualify(self.lead_id, "r1")
        self.opp_id = self.crm.convert(self.lead_id, 1000, "r1")

    def test_add_lead_unknown_actor_beats_bad_input(self):
        with self.assertRaises(PermissionError):
            self.crm.add_lead("not an email", "", "bogus", "ghost")

    def test_qualify_unknown_actor_beats_unknown_lead(self):
        with self.assertRaises(PermissionError):
            self.crm.qualify("L999", "ghost")

    def test_convert_unknown_actor_beats_bad_amount(self):
        with self.assertRaises(PermissionError):
            self.crm.convert(self.lead_id, -5, "ghost")

    def test_advance_unknown_actor_beats_unknown_opp(self):
        with self.assertRaises(PermissionError):
            self.crm.advance("O999", "bogus", "ghost")

    def test_discount_unknown_actor_beats_unknown_opp(self):
        with self.assertRaises(PermissionError):
            self.crm.discount("O999", 99, "ghost")

    def test_transfer_unknown_actor_beats_unknown_opp(self):
        with self.assertRaises(PermissionError):
            self.crm.transfer("O999", "ghost", "ghost")

    def test_failed_calls_appended_nothing(self):
        self.assertEqual(
            self.crm.log,
            [("add_lead", "L1", "r1"), ("qualify", "L1", "r1"),
             ("convert", "O1", "r1")],
        )


class AddLeadBasicsTests(unittest.TestCase):
    def test_lead_record_and_log(self):
        crm = build()
        lead_id = crm.add_lead("  Alice@ACME.com ", "  Alice Doe  ", "referral", "m1")
        self.assertEqual(lead_id, "L1")
        self.assertEqual(crm.leads[lead_id], {
            "id": "L1",
            "email": "alice@acme.com",
            "name": "Alice Doe",
            "source": "referral",
            "score": 45,
            "owner": "r1",
            "status": "new",
        })
        self.assertEqual(crm.log, [("add_lead", "L1", "m1")])

    def test_ids_count_only_successes(self):
        crm = build()
        first = crm.add_lead("a@acme.com", "A", "web", "r1")
        with self.assertRaises(ValueError):
            crm.add_lead("bad-email", "A", "web", "r1")
        with self.assertRaises(ValueError):
            crm.add_lead("a@acme.com", "", "web", "r1")
        second = crm.add_lead("b@acme.com", "B", "web", "r1")
        self.assertEqual(first, "L1")
        self.assertEqual(second, "L2")
        self.assertEqual(sorted(crm.leads), ["L1", "L2"])
        self.assertEqual(len(crm.log), 2)

    def test_scores(self):
        cases = [
            ("w@gmail.com", "web", 10),
            ("y@yahoo.com", "web", 10),
            ("o@outlook.com", "event", 20),
            ("r@referral.com", "referral", 45),
            ("e@ex.com", "event", 35),
            ("g@gmail.com", "referral", 30),
        ]
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 99}])
        for email, source, expected in cases:
            with self.subTest(email=email):
                lead_id = crm.add_lead(email, "N", source, "r1")
                self.assertEqual(crm.leads[lead_id]["score"], expected)

    def test_domain_bonus_is_case_insensitive_after_normalization(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 99}])
        lead_id = crm.add_lead("  A@Gmail.COM ", "N", "web", "r1")
        self.assertEqual(crm.leads[lead_id]["score"], 10)
        self.assertEqual(crm.leads[lead_id]["email"], "a@gmail.com")


class EmailValidationTests(unittest.TestCase):
    def setUp(self):
        self.crm = CRM([{"id": "r1", "role": "rep", "capacity": 99}])

    def test_rejected_emails(self):
        bad = [
            None, 42, ["a@b.com"],
            "", "no-at-sign.com", "a@@b.com", "a@b@c.com",
            "@b.com", "  @b.com",
            "a@", "a@b", "a@yahoo", "a@.com", "a@com.", "a@.", "a@..",
        ]
        for email in bad:
            with self.subTest(email=email):
                with self.assertRaises(ValueError):
                    self.crm.add_lead(email, "N", "web", "r1")

    def test_accepted_emails(self):
        good = [
            "a@b.com", "x@y.io", "A.B@C.DE", "  a@b.co.uk  ", "a@b.c",
        ]
        for email in good:
            with self.subTest(email=email):
                self.crm.add_lead(email, "N", "web", "r1")


class NameAndSourceTests(unittest.TestCase):
    def setUp(self):
        self.crm = CRM([{"id": "r1", "role": "rep", "capacity": 99}])

    def test_bad_names(self):
        for name in [None, 5, "", "   ", "\t\n"]:
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    self.crm.add_lead("a@b.com", name, "web", "r1")

    def test_bad_sources(self):
        for source in [None, "", "Web", "WEB", "phone", 7]:
            with self.subTest(source=source):
                with self.assertRaises(ValueError):
                    self.crm.add_lead("a@b.com", "N", source, "r1")

    def test_checks_run_in_order(self):
        # email check before name check before source check
        with self.assertRaises(ValueError):
            self.crm.add_lead("bad", 5, "bogus", "r1")  # email error
        try:
            self.crm.add_lead("a@b.com", 5, "bogus", "r1")
        except ValueError as exc:
            self.assertIn("name", str(exc))
        # name check wins over source check
        try:
            self.crm.add_lead("a@b.com", "", "bogus", "r1")
        except ValueError as exc:
            self.assertIn("name", str(exc))


class DuplicateLeadTests(unittest.TestCase):
    def setUp(self):
        self.crm = CRM([{"id": "r1", "role": "rep", "capacity": 99}])
        self.existing = self.crm.add_lead("A@Example.com", "Ann", "web", "r1")

    def test_duplicate_raises_with_existing_id(self):
        with self.assertRaises(DuplicateLeadError) as ctx:
            self.crm.add_lead("  a@example.com  ", "Other", "referral", "r1")
        self.assertEqual(ctx.exception.existing_id, self.existing)
        self.assertIsInstance(ctx.exception, Exception)
        self.assertEqual(len(self.crm.leads), 1)
        self.assertEqual(self.crm.log, [("add_lead", "L1", "r1")])
        # next successful creation still gets L2 (failed call consumed no id)
        self.assertEqual(
            self.crm.add_lead("b@example.com", "B", "web", "r1"), "L2")

    def test_validation_precedes_duplicate_check(self):
        # invalid source with a duplicate email -> ValueError, not Duplicate
        with self.assertRaises(ValueError):
            self.crm.add_lead("a@example.com", "Ann", "cold-call", "r1")
        with self.assertRaises(ValueError):
            self.crm.add_lead("a@example.com", "   ", "web", "r1")


class RoutingTests(unittest.TestCase):
    def test_ties_broken_by_smallest_id_in_string_order(self):
        crm = CRM([
            {"id": "r2", "role": "rep", "capacity": 1},
            {"id": "r10", "role": "rep", "capacity": 1},
            {"id": "r9", "role": "rep", "capacity": 1},
        ])
        owners = []
        for i in range(3):
            lead_id = crm.add_lead("p%d@ex.com" % i, "N", "web", "r2")
            owners.append(crm.leads[lead_id]["owner"])
        self.assertEqual(owners, ["r10", "r2", "r9"])  # string order
        lead_id = crm.add_lead("full@ex.com", "N", "web", "r2")
        self.assertIsNone(crm.leads[lead_id]["owner"])

    def test_lowest_load_wins(self):
        crm = CRM([
            {"id": "alpha", "role": "rep", "capacity": 2},
            {"id": "beta", "role": "rep", "capacity": 5},
        ])
        first = crm.add_lead("a@ex.com", "A", "web", "alpha")   # both load 0 -> alpha
        second = crm.add_lead("b@ex.com", "B", "web", "alpha")  # alpha 1, beta 0 -> beta
        third = crm.add_lead("c@ex.com", "C", "web", "alpha")   # tie 1-1 -> alpha
        fourth = crm.add_lead("d@ex.com", "D", "web", "alpha")  # alpha 2 full -> beta
        self.assertEqual(crm.leads[first]["owner"], "alpha")
        self.assertEqual(crm.leads[second]["owner"], "beta")
        self.assertEqual(crm.leads[third]["owner"], "alpha")
        self.assertEqual(crm.leads[fourth]["owner"], "beta")

    def test_managers_never_receive_work(self):
        crm = CRM([
            {"id": "m1", "role": "manager", "capacity": 9},
            {"id": "r0", "role": "rep", "capacity": 0},
        ])
        lead_id = crm.add_lead("a@ex.com", "A", "web", "m1")
        self.assertIsNone(crm.leads[lead_id]["owner"])
        self.assertEqual(crm.log, [("add_lead", "L1", "m1")])

    def test_waiting_queue_when_no_capacity(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1}])
        first = crm.add_lead("a@ex.com", "A", "web", "r1")
        second = crm.add_lead("b@ex.com", "B", "web", "r1")
        third = crm.add_lead("c@ex.com", "C", "web", "r1")
        self.assertEqual(crm.leads[first]["owner"], "r1")
        self.assertIsNone(crm.leads[second]["owner"])
        self.assertIsNone(crm.leads[third]["owner"])
        self.assertEqual(
            crm.log,
            [("add_lead", "L1", "r1"), ("add_lead", "L2", "r1"),
             ("add_lead", "L3", "r1")],
        )


if __name__ == "__main__":
    unittest.main()
