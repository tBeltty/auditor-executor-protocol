"""Unit tests for the intake half of crm.py: actor checks, validation,
normalization, scoring, ids, duplicates, balancing and the waiting queue."""

import unittest

from crm import CRM, DuplicateLeadError


def reps_two(cap_a=2, cap_b=2):
    return [
        {"id": "r1", "role": "rep", "capacity": cap_a},
        {"id": "r2", "role": "rep", "capacity": cap_b},
        {"id": "m1", "role": "manager", "capacity": 0},
    ]


def snapshot(crm):
    """Full observable state, used to assert that failed calls change nothing.

    ``_lead_seq`` / ``_opp_seq`` are private id counters; reading them is a
    deliberate white-box check so a failed call cannot silently consume an id.
    """
    return (
        {lead_id: dict(lead) for lead_id, lead in crm.leads.items()},
        {opp_id: dict(opp) for opp_id, opp in crm.opps.items()},
        list(crm.log),
        list(crm.waiting),
        crm._lead_seq,
        crm._opp_seq,
    )


class ActorCheckTests(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(reps_two())

    def test_unknown_actor_is_rejected_first(self):
        # Invalid email too: actor check wins.
        with self.assertRaises(PermissionError):
            self.crm.add_lead("not-an-email", "", "web", "ghost")
        with self.assertRaises(PermissionError):
            self.crm.qualify("L999", "ghost")
        with self.assertRaises(PermissionError):
            self.crm.convert("L999", 0, "ghost")
        with self.assertRaises(PermissionError):
            self.crm.advance("O999", "nonsense", "ghost")
        with self.assertRaises(PermissionError):
            self.crm.discount("O999", 99, "ghost")
        with self.assertRaises(PermissionError):
            self.crm.transfer("O999", "nobody", "ghost")

    def test_actor_must_be_string_id(self):
        with self.assertRaises(PermissionError):
            self.crm.add_lead("a@b.com", "A", "web", None)
        with self.assertRaises(PermissionError):
            self.crm.add_lead("a@b.com", "A", "web", ["r1"])

    def test_manager_is_a_known_actor(self):
        lead_id = self.crm.add_lead("a@b.com", "A", "referral", "m1")
        self.assertEqual(lead_id, "L1")


class EmailValidationTests(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(reps_two())

    def test_invalid_emails(self):
        invalid = [
            "",
            "plainaddress",
            "a@b",
            "a@",
            "@b.com",
            "a@@b.com",
            "a@b@c.com",
            "a@.com",
            "a@com.",
            "a@b.",
            "a@.b",
            "a@.",
            "   ",
            None,
            123,
            ["a@b.com"],
        ]
        for email in invalid:
            with self.subTest(email=email):
                with self.assertRaises(ValueError):
                    self.crm.add_lead(email, "Name", "web", "r1")
        self.assertEqual(self.crm.leads, {})
        self.assertEqual(self.crm.log, [])

    def test_email_domain_rule_is_existential_interior_dot(self):
        # Spec: the domain must contain a "." that is neither its first nor
        # its last character.  One such dot is enough, even when the domain
        # also starts or ends with a dot.
        valid = ["a@b.com.", "a@.b.com", "a@b.c.", "a@b..com", "a@b.c"]
        for email in valid:
            with self.subTest(email=email):
                lead_id = self.crm.add_lead(email, "Name", "web", "r1")
                self.assertEqual(self.crm.leads[lead_id]["email"], email)
        # A dot only at the first or only at the last position is not interior.
        invalid = ["a@b.", "a@.b", "a@.", "a@.com", "a@com."]
        for email in invalid:
            with self.subTest(email=email):
                with self.assertRaises(ValueError):
                    self.crm.add_lead(email, "Name", "web", "r1")

    def test_valid_emails_are_normalized(self):
        cases = {
            "  Alice@Example.COM  ": "alice@example.com",
            "a@b.c": "a@b.c",
            "a@b.com.": "a@b.com.",
            "a@.b.com": "a@.b.com",
            "first.last+tag@sub.example.co": "first.last+tag@sub.example.co",
        }
        for raw, expected in cases.items():
            with self.subTest(raw=raw):
                lead_id = self.crm.add_lead(raw, "Name", "web", "r1")
                self.assertEqual(self.crm.leads[lead_id]["email"], expected)

    def test_name_is_stored_stripped(self):
        lead_id = self.crm.add_lead("a@b.com", "  Alice  ", "web", "r1")
        self.assertEqual(self.crm.leads[lead_id]["name"], "Alice")

    def test_name_validation(self):
        for bad in ["", "   ", None, 7]:
            with self.subTest(name=bad):
                with self.assertRaises(ValueError):
                    self.crm.add_lead("a@b.com", bad, "web", "r1")

    def test_source_validation(self):
        for bad in ["email", "WEB", "", None, 3]:
            with self.subTest(source=bad):
                with self.assertRaises(ValueError):
                    self.crm.add_lead("a@b.com", "Alice", bad, "r1")

    def test_check_order_email_then_name_then_source(self):
        with self.assertRaises(ValueError):
            self.crm.add_lead("a@b", "", "bogus", "r1")
        with self.assertRaises(ValueError):
            self.crm.add_lead("a@b.com", "", "bogus", "r1")
        self.assertEqual(self.crm.leads, {})


class ScoringAndIdTests(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(reps_two(cap_a=10, cap_b=10))

    def test_scores(self):
        expectations = [
            ("web", "a@gmail.com", 10),
            ("web", "a@yahoo.com", 10),
            ("web", "a@outlook.com", 10),
            ("web", "a@corp.example", 25),
            ("referral", "b@gmail.com", 30),
            ("referral", "b@corp.example", 45),
            ("event", "c@gmail.com", 20),
            ("event", "c@corp.example", 35),
        ]
        for source, email, score in expectations:
            with self.subTest(source=source, email=email):
                lead_id = self.crm.add_lead(email, "N", source, "r1")
                self.assertEqual(self.crm.leads[lead_id]["score"], score)

    def test_ids_are_sequential_and_failures_do_not_consume_them(self):
        self.assertEqual(self.crm.add_lead("a@b.com", "A", "referral", "r1"), "L1")
        with self.assertRaises(ValueError):
            self.crm.add_lead("bad", "B", "referral", "r1")
        with self.assertRaises(ValueError):
            self.crm.add_lead("c@b.com", "C", "nope", "r1")
        self.assertEqual(self.crm.add_lead("d@b.com", "D", "referral", "r1"), "L2")

    def test_lead_payload_and_log(self):
        lead_id = self.crm.add_lead("  A@Corp.COM ", " Alice ", "referral", "r2")
        self.assertEqual(
            self.crm.leads[lead_id],
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
        self.assertEqual(self.crm.log, [("add_lead", "L1", "r2")])


class DuplicateTests(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(reps_two(cap_a=10, cap_b=10))

    def test_duplicate_is_detected_after_normalization(self):
        first = self.crm.add_lead("Alice@Example.com", "Alice", "web", "r1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            self.crm.add_lead("  alice@example.COM ", "Other", "referral", "r1")
        self.assertEqual(ctx.exception.existing_id, first)
        self.assertEqual(len(self.crm.leads), 1)
        self.assertEqual(len(self.crm.log), 1)

    def test_duplicate_error_is_an_exception(self):
        self.assertTrue(issubclass(DuplicateLeadError, Exception))
        err = DuplicateLeadError("L7")
        self.assertEqual(err.existing_id, "L7")

    def test_duplicate_check_comes_after_source_check(self):
        self.crm.add_lead("a@b.com", "A", "web", "r1")
        with self.assertRaises(ValueError):
            self.crm.add_lead("a@b.com", "A", "telepathy", "r1")


class AddLeadAtomicityTests(unittest.TestCase):
    """A failing add_lead must not touch leads, queue, log or id counters."""

    def setUp(self):
        # Capacity 1 and one lead already owned, so a successful add would be
        # queued: this makes an accidental queue append visible.
        self.crm = CRM([{"id": "r1", "role": "rep", "capacity": 1}])
        self.crm.add_lead("a@b.com", "A", "web", "r1")

    def test_name_failure_leaves_state_untouched(self):
        before = snapshot(self.crm)
        for bad in ["", "   ", None, 7]:
            with self.subTest(name=bad):
                with self.assertRaises(ValueError):
                    self.crm.add_lead("z@b.com", bad, "web", "r1")
        self.assertEqual(snapshot(self.crm), before)

    def test_source_failure_leaves_state_untouched(self):
        before = snapshot(self.crm)
        for bad in ["email", "WEB", "", None, 3]:
            with self.subTest(source=bad):
                with self.assertRaises(ValueError):
                    self.crm.add_lead("z@b.com", "Z", bad, "r1")
        self.assertEqual(snapshot(self.crm), before)

    def test_email_failure_leaves_state_untouched(self):
        before = snapshot(self.crm)
        with self.assertRaises(ValueError):
            self.crm.add_lead("not-an-email", "Z", "web", "r1")
        self.assertEqual(snapshot(self.crm), before)

    def test_duplicate_failure_leaves_state_untouched(self):
        before = snapshot(self.crm)
        with self.assertRaises(DuplicateLeadError):
            self.crm.add_lead("A@B.com ", "Z", "web", "r1")
        self.assertEqual(snapshot(self.crm), before)


class BalanceAndQueueTests(unittest.TestCase):
    def test_lowest_load_then_smallest_id(self):
        crm = CRM(reps_two(cap_a=2, cap_b=2))
        self.assertEqual(crm.leads[crm.add_lead("a@x.com", "A", "web", "r1")]["owner"], "r1")
        self.assertEqual(crm.leads[crm.add_lead("b@x.com", "B", "web", "r1")]["owner"], "r2")
        # r2 has load 1; r1 has load 1, so id order picks r1.
        self.assertEqual(crm.leads[crm.add_lead("c@x.com", "C", "web", "r1")]["owner"], "r1")

    def test_tie_break_is_string_order_not_numeric(self):
        # "r10" < "r2" as strings, so a numeric key would pick "r2".
        crm = CRM(
            [
                {"id": "r2", "role": "rep", "capacity": 2},
                {"id": "r10", "role": "rep", "capacity": 2},
            ]
        )
        first = crm.add_lead("a@x.com", "A", "web", "r10")
        self.assertEqual(crm.leads[first]["owner"], "r10")
        second = crm.add_lead("b@x.com", "B", "web", "r10")
        self.assertEqual(crm.leads[second]["owner"], "r2")
        # Both now at load 1; string order again picks "r10".
        third = crm.add_lead("c@x.com", "C", "web", "r10")
        self.assertEqual(crm.leads[third]["owner"], "r10")

    def test_capacity_is_respected_and_overflow_queues_fifo(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1}])
        l1 = crm.add_lead("a@x.com", "A", "web", "r1")
        l2 = crm.add_lead("b@x.com", "B", "web", "r1")
        l3 = crm.add_lead("c@x.com", "C", "web", "r1")
        self.assertEqual(crm.leads[l1]["owner"], "r1")
        self.assertIsNone(crm.leads[l2]["owner"])
        self.assertIsNone(crm.leads[l3]["owner"])
        self.assertEqual(list(crm.waiting), [l2, l3])
        self.assertEqual(crm._load("r1"), 1)

    def test_managers_never_receive_leads(self):
        crm = CRM(
            [
                {"id": "m1", "role": "manager", "capacity": 5},
                {"id": "m2", "role": "manager", "capacity": 5},
            ]
        )
        lead_id = crm.add_lead("a@corp.com", "A", "referral", "m1")
        self.assertIsNone(crm.leads[lead_id]["owner"])
        self.assertEqual(list(crm.waiting), [lead_id])

    def test_zero_capacity_never_receives(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 0}])
        lead_id = crm.add_lead("a@x.com", "A", "web", "r1")
        self.assertIsNone(crm.leads[lead_id]["owner"])

    def test_load_counts_new_and_qualified_leads_only(self):
        crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 10},
                {"id": "r2", "role": "rep", "capacity": 10},
            ]
        )
        l1 = crm.add_lead("a@corp.com", "A", "referral", "r1")
        l2 = crm.add_lead("b@corp.com", "B", "referral", "r1")
        # l1 owner r1, l2 owner r2 (balanced). Force both to r1 is not possible;
        # qualify l1 and check the count stays the same.
        crm.qualify(l1, "r1")
        self.assertEqual(crm._load("r1"), 1)
        self.assertEqual(crm._load("r2"), 1)


if __name__ == "__main__":
    unittest.main()
