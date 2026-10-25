"""Unit tests for lead intake, ownership, qualification and conversion."""

import unittest

from crm import CRM, DuplicateLeadError


def make_crm(reps=None):
    if reps is None:
        reps = [
            {"id": "r1", "role": "rep", "capacity": 2},
            {"id": "r2", "role": "rep", "capacity": 2},
            {"id": "m1", "role": "manager", "capacity": 10},
        ]
    return CRM(reps)


def qualified_lead(crm, email="a@corp.com", lead_actor="r1"):
    lead_id = crm.add_lead(email, "Lead", "referral", lead_actor)
    crm.qualify(lead_id, "m1")
    return lead_id


class CRMSetupTests(unittest.TestCase):
    def test_state_starts_empty(self):
        crm = make_crm()
        self.assertEqual(crm.leads, {})
        self.assertEqual(crm.opps, {})
        self.assertEqual(crm.log, [])

    def test_duplicate_lead_error_is_an_exception(self):
        self.assertTrue(issubclass(DuplicateLeadError, Exception))


class AddLeadTests(unittest.TestCase):
    def test_records_normalized_lead_and_returns_id(self):
        crm = make_crm()
        lead_id = crm.add_lead("  Alice@Example.COM ", " Alice ", "referral", "r1")
        self.assertEqual(lead_id, "L1")
        self.assertEqual(
            crm.leads["L1"],
            {
                "id": "L1",
                "email": "alice@example.com",
                "name": "Alice",
                "source": "referral",
                "score": 45,
                "owner": "r1",
                "status": "new",
            },
        )
        self.assertEqual(crm.log, [("add_lead", "L1", "r1")])

    def test_ids_increment_per_success(self):
        crm = make_crm()
        self.assertEqual(crm.add_lead("a@corp.com", "A", "web", "r1"), "L1")
        self.assertEqual(crm.add_lead("b@corp.com", "B", "web", "r1"), "L2")
        self.assertEqual(crm.add_lead("c@corp.com", "C", "web", "r1"), "L3")

    def test_score_table(self):
        cases = [
            ("web", "a@gmail.com", 10),
            ("web", "a@acme.io", 25),
            ("referral", "b@yahoo.com", 30),
            ("referral", "b@acme.io", 45),
            ("event", "c@outlook.com", 20),
            ("event", "c@acme.io", 35),
        ]
        for source, email, expected in cases:
            with self.subTest(source=source, email=email):
                crm = make_crm()
                lead_id = crm.add_lead(email, "Lead", source, "r1")
                self.assertEqual(crm.leads[lead_id]["score"], expected)

    def test_accepts_minimal_valid_email(self):
        crm = make_crm()
        lead_id = crm.add_lead("a@b.c", "A", "web", "r1")
        self.assertEqual(crm.leads[lead_id]["email"], "a@b.c")

    def test_rejects_malformed_email(self):
        invalid = [
            "plain",
            "a@@b.com",
            "a@b@c.com",
            "@b.com",
            "a@",
            "a@bcom",
            "a@.com",
            "a@com.",
            "a@b.",
            "   ",
            "",
        ]
        for email in invalid:
            with self.subTest(email=email):
                crm = make_crm()
                with self.assertRaises(ValueError):
                    crm.add_lead(email, "Lead", "web", "r1")
                self.assertEqual(crm.leads, {})
                self.assertEqual(crm.log, [])

    def test_rejects_non_string_email(self):
        for email in (None, 5, ["a@b.com"]):
            with self.subTest(email=email):
                crm = make_crm()
                with self.assertRaises(ValueError):
                    crm.add_lead(email, "Lead", "web", "r1")

    def test_rejects_bad_name(self):
        for name in ("", "   ", None, 5, b"Bob"):
            with self.subTest(name=name):
                crm = make_crm()
                with self.assertRaises(ValueError):
                    crm.add_lead("a@corp.com", name, "web", "r1")
                self.assertEqual(crm.leads, {})

    def test_rejects_bad_source(self):
        for source in ("Web", "social", None, 5):
            with self.subTest(source=source):
                crm = make_crm()
                with self.assertRaises(ValueError):
                    crm.add_lead("a@corp.com", "A", source, "r1")
                self.assertEqual(crm.leads, {})

    def test_duplicate_email_raises_with_existing_id(self):
        crm = make_crm()
        crm.add_lead("bob@corp.com", "Bob", "web", "r1")
        with self.assertRaises(DuplicateLeadError) as caught:
            crm.add_lead("  BOB@Corp.COM ", "Robert", "event", "r1")
        self.assertEqual(caught.exception.existing_id, "L1")
        self.assertEqual(len(crm.leads), 1)
        self.assertEqual(len(crm.log), 1)

    def test_failed_creation_does_not_consume_an_id(self):
        crm = make_crm()
        crm.add_lead("bob@corp.com", "Bob", "web", "r1")
        with self.assertRaises(DuplicateLeadError):
            crm.add_lead("bob@corp.com", "Bob", "web", "r1")
        self.assertEqual(crm.add_lead("amy@corp.com", "Amy", "web", "r1"), "L2")

    def test_duplicate_check_runs_after_name_and_source(self):
        crm = make_crm()
        crm.add_lead("bob@corp.com", "Bob", "web", "r1")
        with self.assertRaises(ValueError):
            crm.add_lead("bob@corp.com", "   ", "web", "r1")
        with self.assertRaises(ValueError):
            crm.add_lead("bob@corp.com", "Bob", "social", "r1")
        self.assertEqual(len(crm.leads), 1)

    def test_unknown_actor_checked_before_payload(self):
        crm = make_crm()
        with self.assertRaises(PermissionError):
            crm.add_lead("not-an-email", "", "bogus", "ghost")
        self.assertEqual(crm.leads, {})
        self.assertEqual(crm.log, [])


class OwnershipTests(unittest.TestCase):
    def test_assigns_to_least_loaded_rep(self):
        crm = make_crm(
            [
                {"id": "r1", "role": "rep", "capacity": 2},
                {"id": "r2", "role": "rep", "capacity": 2},
            ]
        )
        owners = []
        for index, email in enumerate(("a@x.com", "b@x.com", "c@x.com")):
            lead_id = crm.add_lead(email, "Lead", "web", "r1")
            owners.append(crm.leads[lead_id]["owner"])
        self.assertEqual(owners, ["r1", "r2", "r1"])

    def test_tie_break_is_smallest_id_in_string_order(self):
        crm = make_crm(
            [
                {"id": "r9", "role": "rep", "capacity": 1},
                {"id": "r2", "role": "rep", "capacity": 1},
                {"id": "r10", "role": "rep", "capacity": 1},
            ]
        )
        owners = []
        for index, email in enumerate(("a@x.com", "b@x.com", "c@x.com")):
            lead_id = crm.add_lead(email, "Lead", "web", "r9")
            owners.append(crm.leads[lead_id]["owner"])
        self.assertEqual(owners, ["r10", "r2", "r9"])

    def test_full_and_zero_capacity_reps_are_skipped(self):
        crm = make_crm(
            [
                {"id": "r1", "role": "rep", "capacity": 0},
                {"id": "r2", "role": "rep", "capacity": 1},
            ]
        )
        first = crm.add_lead("a@x.com", "A", "web", "r2")
        second = crm.add_lead("b@x.com", "B", "web", "r2")
        self.assertEqual(crm.leads[first]["owner"], "r2")
        self.assertIsNone(crm.leads[second]["owner"])

    def test_manager_never_owns_leads(self):
        crm = make_crm(
            [
                {"id": "r1", "role": "rep", "capacity": 0},
                {"id": "m1", "role": "manager", "capacity": 5},
            ]
        )
        lead_id = crm.add_lead("a@x.com", "A", "web", "m1")
        self.assertIsNone(crm.leads[lead_id]["owner"])


class QualifyTests(unittest.TestCase):
    def test_owner_qualifies(self):
        crm = make_crm()
        lead_id = crm.add_lead("a@corp.com", "A", "referral", "r1")
        self.assertIsNone(crm.qualify(lead_id, "r1"))
        self.assertEqual(crm.leads[lead_id]["status"], "qualified")
        self.assertEqual(crm.log[-1], ("qualify", lead_id, "r1"))

    def test_manager_qualifies_any_lead(self):
        crm = make_crm()
        lead_id = crm.add_lead("a@corp.com", "A", "referral", "r1")
        crm.qualify(lead_id, "m1")
        self.assertEqual(crm.log[-1], ("qualify", lead_id, "m1"))

    def test_unknown_lead_rejected(self):
        crm = make_crm()
        with self.assertRaises(ValueError):
            crm.qualify("L99", "m1")

    def test_unknown_actor_checked_before_lead(self):
        crm = make_crm()
        with self.assertRaises(PermissionError):
            crm.qualify("L99", "ghost")

    def test_other_rep_is_denied(self):
        crm = make_crm()
        lead_id = crm.add_lead("a@corp.com", "A", "referral", "r1")
        with self.assertRaises(PermissionError):
            crm.qualify(lead_id, "r2")
        self.assertEqual(crm.leads[lead_id]["status"], "new")
        self.assertEqual(len(crm.log), 1)

    def test_requires_new_status(self):
        crm = make_crm()
        lead_id = qualified_lead(crm)
        with self.assertRaises(ValueError):
            crm.qualify(lead_id, "r1")
        self.assertEqual(crm.leads[lead_id]["status"], "qualified")
        self.assertEqual(len(crm.log), 2)

    def test_requires_score_of_at_least_30(self):
        cases = [
            ("web", "a@gmail.com"),
            ("web", "a@acme.io"),
            ("event", "b@yahoo.com"),
        ]
        for source, email in cases:
            with self.subTest(source=source, email=email):
                crm = make_crm()
                lead_id = crm.add_lead(email, "A", source, "r1")
                with self.assertRaises(ValueError):
                    crm.qualify(lead_id, "r1")
                self.assertEqual(crm.leads[lead_id]["status"], "new")

    def test_score_of_exactly_30_is_enough(self):
        crm = make_crm()
        lead_id = crm.add_lead("a@yahoo.com", "A", "referral", "r1")
        crm.qualify(lead_id, "r1")
        self.assertEqual(crm.leads[lead_id]["status"], "qualified")

    def test_permission_checked_before_status_and_score(self):
        crm = make_crm()
        qualified = qualified_lead(crm, "a@corp.com")
        with self.assertRaises(PermissionError):
            crm.qualify(qualified, "r2")
        crm2 = make_crm()
        low = crm2.add_lead("b@yahoo.com", "B", "web", "r1")
        self.assertEqual(crm2.leads[low]["score"], 10)
        with self.assertRaises(PermissionError):
            crm2.qualify(low, "r2")

    def test_manager_can_qualify_a_lead_without_owner(self):
        crm = make_crm(
            [
                {"id": "r1", "role": "rep", "capacity": 0},
                {"id": "m1", "role": "manager", "capacity": 5},
            ]
        )
        lead_id = crm.add_lead("a@corp.com", "A", "referral", "m1")
        self.assertIsNone(crm.leads[lead_id]["owner"])
        crm.qualify(lead_id, "m1")
        self.assertEqual(crm.leads[lead_id]["status"], "qualified")
        self.assertIsNone(crm.leads[lead_id]["owner"])


class ConvertTests(unittest.TestCase):
    def test_converts_qualified_lead_into_opportunity(self):
        crm = make_crm()
        lead_id = qualified_lead(crm)
        opp_id = crm.convert(lead_id, 1500, "r1")
        self.assertEqual(opp_id, "O1")
        self.assertEqual(
            crm.opps["O1"],
            {
                "id": "O1",
                "lead_id": "L1",
                "owner": "r1",
                "amount": 1500,
                "original_amount": 1500,
                "stage": "prospect",
            },
        )
        self.assertEqual(crm.leads[lead_id]["status"], "converted")
        self.assertEqual(crm.log[-1], ("convert", "O1", "r1"))

    def test_manager_can_convert(self):
        crm = make_crm()
        lead_id = qualified_lead(crm)
        self.assertEqual(crm.convert(lead_id, 10, "m1"), "O1")
        self.assertEqual(crm.log[-1], ("convert", "O1", "m1"))

    def test_unknown_lead_rejected(self):
        crm = make_crm()
        with self.assertRaises(ValueError):
            crm.convert("L99", 100, "m1")

    def test_unknown_actor_checked_before_lead(self):
        crm = make_crm()
        with self.assertRaises(PermissionError):
            crm.convert("L99", 100, "ghost")

    def test_amount_must_be_positive_int_not_bool(self):
        crm = make_crm()
        lead_id = qualified_lead(crm)
        for amount in (0, -5, True, False, 1.5, "100", None):
            with self.subTest(amount=amount):
                with self.assertRaises(ValueError):
                    crm.convert(lead_id, amount, "r1")
                self.assertEqual(crm.opps, {})
                self.assertEqual(crm.leads[lead_id]["status"], "qualified")

    def test_amount_checked_before_permission(self):
        crm = make_crm()
        lead_id = qualified_lead(crm)
        with self.assertRaises(ValueError):
            crm.convert(lead_id, 0, "r2")
        self.assertEqual(crm.opps, {})

    def test_requires_qualified_status(self):
        crm = make_crm()
        lead_id = crm.add_lead("a@corp.com", "A", "referral", "r1")
        with self.assertRaises(ValueError):
            crm.convert(lead_id, 100, "r1")
        self.assertEqual(crm.opps, {})

    def test_other_rep_is_denied(self):
        crm = make_crm()
        lead_id = qualified_lead(crm)
        with self.assertRaises(PermissionError):
            crm.convert(lead_id, 100, "r2")
        self.assertEqual(crm.opps, {})

    def test_requires_owner(self):
        crm = make_crm(
            [
                {"id": "r1", "role": "rep", "capacity": 0},
                {"id": "m1", "role": "manager", "capacity": 5},
            ]
        )
        lead_id = crm.add_lead("a@corp.com", "A", "referral", "m1")
        crm.qualify(lead_id, "m1")
        with self.assertRaises(ValueError):
            crm.convert(lead_id, 100, "m1")
        self.assertEqual(crm.opps, {})

    def test_ids_increment_and_failures_do_not_consume(self):
        crm = make_crm()
        first = qualified_lead(crm, "a@corp.com")
        self.assertEqual(crm.convert(first, 100, "m1"), "O1")
        second = qualified_lead(crm, "b@corp.com")
        with self.assertRaises(ValueError):
            crm.convert(second, 0, "m1")
        self.assertEqual(crm.convert(second, 100, "m1"), "O2")

    def test_converted_lead_cannot_be_converted_again(self):
        crm = make_crm()
        lead_id = qualified_lead(crm)
        crm.convert(lead_id, 100, "m1")
        with self.assertRaises(ValueError):
            crm.convert(lead_id, 100, "m1")
        self.assertEqual(len(crm.opps), 1)

    def test_conversion_keeps_owner_at_capacity(self):
        crm = make_crm(
            [
                {"id": "r1", "role": "rep", "capacity": 1},
                {"id": "r2", "role": "rep", "capacity": 0},
                {"id": "m1", "role": "manager", "capacity": 5},
            ]
        )
        first = crm.add_lead("a@corp.com", "A", "referral", "m1")
        waiting = crm.add_lead("b@corp.com", "B", "referral", "m1")
        self.assertEqual(crm.leads[first]["owner"], "r1")
        self.assertIsNone(crm.leads[waiting]["owner"])
        crm.qualify(first, "m1")
        crm.convert(first, 100, "m1")
        later = crm.add_lead("c@corp.com", "C", "referral", "m1")
        self.assertIsNone(crm.leads[later]["owner"])


if __name__ == "__main__":
    unittest.main()
