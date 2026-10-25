"""Unit tests for lead intake, ownership and qualification/ conversion."""

import copy
import unittest

from crm import CRM, DuplicateLeadError


DEFAULT_REPS = [
    {"id": "r1", "role": "rep", "capacity": 2},
    {"id": "r2", "role": "rep", "capacity": 2},
    {"id": "m1", "role": "manager", "capacity": 0},
]


class BaseCase(unittest.TestCase):
    def make(self, rep_list=None):
        if rep_list is None:
            rep_list = DEFAULT_REPS
        return CRM([dict(rep) for rep in rep_list])

    def assert_unchanged(self, crm, exc, fn, *args):
        before = copy.deepcopy((crm.leads, crm.opps, crm.log, crm.waiting))
        with self.assertRaises(exc):
            fn(*args)
        after = copy.deepcopy((crm.leads, crm.opps, crm.log, crm.waiting))
        self.assertEqual(before, after)


class TestAddLead(BaseCase):
    def test_unknown_actor_is_rejected_first(self):
        crm = self.make()
        with self.assertRaises(PermissionError):
            crm.add_lead("a@corp.io", "A", "web", "ghost")
        self.assertEqual(crm.leads, {})
        self.assertEqual(crm.log, [])

    def test_actor_check_precedes_every_other_check(self):
        crm = self.make()
        with self.assertRaises(PermissionError):
            crm.add_lead(123, "", "nope", "ghost")

    def test_email_must_be_a_string(self):
        crm = self.make()
        for bad in (None, 123, 1.5, ["a@corp.io"], True):
            with self.subTest(email=bad):
                self.assertRaises(
                    ValueError,
                    crm.add_lead,
                    bad,
                    "A",
                    "web",
                    "r1",
                )
        self.assertEqual(crm.leads, {})
        self.assertEqual(crm.log, [])

    def test_email_shape_is_validated(self):
        crm = self.make()
        bad_emails = [
            "",
            "   ",
            "nobody",
            "a@@corp.io",
            "a@b@corp.io",
            "@corp.io",
            "a@corpio",
            "a@.corp.io",
            "a@corp.io.",
            "a@.",
            "a@.io",
        ]
        for bad in bad_emails:
            with self.subTest(email=bad):
                self.assertRaises(
                    ValueError, crm.add_lead, bad, "A", "web", "r1"
                )
        self.assertEqual(crm.leads, {})
        self.assertEqual(crm.log, [])

    def test_email_is_normalized(self):
        crm = self.make()
        lead_id = crm.add_lead("  Alice@Corp.IO  ", "Alice", "web", "r1")
        lead = crm.leads[lead_id]
        self.assertEqual(lead["email"], "alice@corp.io")
        self.assertEqual(lead["name"], "Alice")

    def test_name_is_validated(self):
        crm = self.make()
        for bad in ("", "   ", None, 7, ["A"]):
            with self.subTest(name=bad):
                self.assertRaises(
                    ValueError, crm.add_lead, "a@corp.io", bad, "web", "r1"
                )
        self.assertEqual(crm.leads, {})

    def test_source_is_validated(self):
        crm = self.make()
        for bad in ("phone", "WEB", "", None, ["web"]):
            with self.subTest(source=bad):
                self.assertRaises(
                    ValueError, crm.add_lead, "a@corp.io", "A", bad, "r1"
                )
        self.assertEqual(crm.leads, {})

    def test_duplicate_email_raises_with_existing_id(self):
        crm = self.make()
        first = crm.add_lead("a@corp.io", "A", "web", "r1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            crm.add_lead("  A@Corp.io ", "Other", "event", "r2")
        self.assertEqual(ctx.exception.existing_id, first)
        self.assertEqual(len(crm.leads), 1)
        self.assertEqual(len(crm.log), 1)

    def test_duplicate_check_uses_normalized_email(self):
        crm = self.make()
        crm.add_lead("bob@gmail.com", "Bob", "web", "r1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            crm.add_lead("BOB@GMAIL.COM", "Bob 2", "referral", "r1")
        self.assertEqual(ctx.exception.existing_id, "L1")

    def test_score_depends_on_source_and_domain(self):
        cases = [
            ("web", "a@gmail.com", 10),
            ("web", "a@yahoo.com", 10),
            ("web", "a@outlook.com", 10),
            ("web", "a@corp.io", 25),
            ("referral", "a@gmail.com", 30),
            ("referral", "a@corp.io", 45),
            ("event", "a@outlook.com", 20),
            ("event", "a@corp.io", 35),
        ]
        crm = self.make([{"id": "r1", "role": "rep", "capacity": 50}])
        for index, (source, email, expected) in enumerate(cases):
            with self.subTest(source=source, email=email):
                lead_id = crm.add_lead(
                    "%d%s" % (index, email), "Lead", source, "r1"
                )
                self.assertEqual(crm.leads[lead_id]["score"], expected)

    def test_lead_shape_and_log(self):
        crm = self.make()
        lead_id = crm.add_lead("  Bob@Corp.io ", "  Bob  ", "referral", "r1")
        self.assertEqual(lead_id, "L1")
        self.assertEqual(
            crm.leads["L1"],
            {
                "id": "L1",
                "email": "bob@corp.io",
                "name": "Bob",
                "source": "referral",
                "score": 45,
                "owner": "r1",
                "status": "new",
            },
        )
        self.assertEqual(crm.log, [("add_lead", "L1", "r1")])

    def test_owner_is_the_least_loaded_rep(self):
        crm = self.make()
        crm.add_lead("a@corp.io", "A", "web", "r1")  # r1 load 1, r2 load 0
        crm.add_lead("b@corp.io", "B", "web", "r1")  # r2 lowest
        crm.add_lead("c@corp.io", "C", "web", "r1")  # tie 1/1 -> r1
        crm.add_lead("d@corp.io", "D", "web", "r1")  # tie 2/1 -> r2
        owners = {lid: lead["owner"] for lid, lead in crm.leads.items()}
        self.assertEqual(
            owners, {"L1": "r1", "L2": "r2", "L3": "r1", "L4": "r2"}
        )

    def test_ties_use_id_string_order(self):
        crm = self.make(
            [
                {"id": "r2", "role": "rep", "capacity": 5},
                {"id": "r10", "role": "rep", "capacity": 5},
            ]
        )
        lead_id = crm.add_lead("a@corp.io", "A", "web", "r10")
        self.assertEqual(crm.leads[lead_id]["owner"], "r10")

    def test_lead_waits_when_all_reps_are_at_capacity(self):
        crm = self.make(
            [
                {"id": "r1", "role": "rep", "capacity": 1},
                {"id": "r2", "role": "rep", "capacity": 1},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        crm.add_lead("a@corp.io", "A", "web", "r1")
        crm.add_lead("b@corp.io", "B", "web", "r1")
        crm.add_lead("c@corp.io", "C", "web", "r1")
        self.assertIsNone(crm.leads["L3"]["owner"])
        self.assertEqual(crm.leads["L3"]["status"], "new")
        self.assertEqual(crm.waiting, ["L3"])

    def test_managers_never_own_work(self):
        crm = self.make(
            [
                {"id": "m1", "role": "manager", "capacity": 5},
                {"id": "r1", "role": "rep", "capacity": 0},
            ]
        )
        crm.add_lead("a@corp.io", "A", "web", "m1")
        self.assertIsNone(crm.leads["L1"]["owner"])

    def test_failed_creation_does_not_consume_an_id(self):
        crm = self.make()
        with self.assertRaises(ValueError):
            crm.add_lead("a@corp.io", "A", "phone", "r1")
        self.assertEqual(crm.add_lead("a@corp.io", "A", "web", "r1"), "L1")
        self.assertEqual(crm.add_lead("b@corp.io", "B", "web", "r1"), "L2")


class TestQualify(BaseCase):
    def test_owner_qualifies_a_high_score_lead(self):
        crm = self.make()
        crm.add_lead("a@corp.io", "A", "referral", "r1")
        crm.qualify("L1", "r1")
        self.assertEqual(crm.leads["L1"]["status"], "qualified")
        self.assertEqual(
            crm.log, [("add_lead", "L1", "r1"), ("qualify", "L1", "r1")]
        )

    def test_manager_can_qualify_someone_elses_lead(self):
        crm = self.make()
        crm.add_lead("a@corp.io", "A", "referral", "r1")
        crm.qualify("L1", "m1")
        self.assertEqual(crm.leads["L1"]["status"], "qualified")
        self.assertEqual(crm.log[-1], ("qualify", "L1", "m1"))

    def test_another_rep_may_not_qualify(self):
        crm = self.make()
        crm.add_lead("a@corp.io", "A", "referral", "r1")
        self.assert_unchanged(crm, PermissionError, crm.qualify, "L1", "r2")

    def test_permission_is_checked_before_status_and_score(self):
        crm = self.make()
        crm.add_lead("a@corp.io", "A", "web", "r1")  # score 25
        self.assert_unchanged(crm, PermissionError, crm.qualify, "L1", "r2")

    def test_unknown_lead(self):
        crm = self.make()
        self.assertRaises(ValueError, crm.qualify, "L99", "r1")

    def test_unknown_actor_beats_unknown_lead(self):
        crm = self.make()
        self.assertRaises(PermissionError, crm.qualify, "L99", "ghost")

    def test_lead_must_be_new(self):
        crm = self.make()
        crm.add_lead("a@corp.io", "A", "referral", "r1")
        crm.qualify("L1", "r1")
        self.assert_unchanged(crm, ValueError, crm.qualify, "L1", "r1")

    def test_score_must_be_at_least_thirty(self):
        crm = self.make([{"id": "r1", "role": "rep", "capacity": 5}])
        crm.add_lead("a@corp.io", "A", "web", "r1")  # 25
        self.assert_unchanged(crm, ValueError, crm.qualify, "L1", "r1")
        crm.add_lead("b@gmail.com", "B", "web", "r1")  # 10
        self.assert_unchanged(crm, ValueError, crm.qualify, "L2", "r1")
        crm.add_lead("c@gmail.com", "C", "referral", "r1")  # 30
        crm.qualify("L3", "r1")
        self.assertEqual(crm.leads["L3"]["status"], "qualified")


class TestConvert(BaseCase):
    def test_convert_creates_the_opportunity(self):
        crm = self.make()
        crm.add_lead("a@corp.io", "A", "referral", "r1")
        crm.qualify("L1", "r1")
        opp_id = crm.convert("L1", 1200, "r1")
        self.assertEqual(opp_id, "O1")
        self.assertEqual(
            crm.opps["O1"],
            {
                "id": "O1",
                "lead_id": "L1",
                "owner": "r1",
                "amount": 1200,
                "original_amount": 1200,
                "stage": "prospect",
            },
        )
        self.assertEqual(crm.leads["L1"]["status"], "converted")
        self.assertEqual(crm.log[-1], ("convert", "O1", "r1"))

    def test_amount_must_be_a_positive_int(self):
        crm = self.make()
        crm.add_lead("a@corp.io", "A", "referral", "r1")
        crm.qualify("L1", "r1")
        for bad in (0, -5, True, False, 1.5, "10", None):
            with self.subTest(amount=bad):
                self.assert_unchanged(
                    crm, ValueError, crm.convert, "L1", bad, "r1"
                )

    def test_amount_is_checked_before_permission(self):
        crm = self.make()
        crm.add_lead("a@corp.io", "A", "referral", "r1")
        crm.qualify("L1", "r1")
        self.assert_unchanged(crm, ValueError, crm.convert, "L1", 0, "r2")

    def test_lead_must_be_qualified(self):
        crm = self.make()
        crm.add_lead("a@corp.io", "A", "referral", "r1")
        self.assert_unchanged(crm, ValueError, crm.convert, "L1", 100, "r1")

    def test_owner_or_manager_may_convert(self):
        crm = self.make()
        crm.add_lead("a@corp.io", "A", "referral", "r1")
        crm.qualify("L1", "r1")
        self.assert_unchanged(crm, PermissionError, crm.convert, "L1", 100, "r2")
        crm.convert("L1", 100, "m1")
        self.assertEqual(crm.leads["L1"]["status"], "converted")

    def test_ownerless_lead_cannot_be_converted(self):
        crm = self.make(
            [
                {"id": "r1", "role": "rep", "capacity": 0},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        crm.add_lead("a@corp.io", "A", "referral", "m1")
        crm.qualify("L1", "m1")
        self.assert_unchanged(crm, ValueError, crm.convert, "L1", 100, "m1")

    def test_unknown_lead(self):
        crm = self.make()
        self.assertRaises(ValueError, crm.convert, "L99", 100, "r1")

    def test_opportunity_ids_count_only_successes(self):
        crm = self.make(
            [
                {"id": "r1", "role": "rep", "capacity": 10},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        crm.add_lead("a@corp.io", "A", "referral", "r1")
        crm.add_lead("b@corp.io", "B", "referral", "r1")
        crm.qualify("L1", "r1")
        crm.qualify("L2", "r1")
        with self.assertRaises(ValueError):
            crm.convert("L1", 0, "r1")
        self.assertEqual(crm.convert("L1", 100, "r1"), "O1")
        self.assertEqual(crm.convert("L2", 200, "r1"), "O2")


if __name__ == "__main__":
    unittest.main()
