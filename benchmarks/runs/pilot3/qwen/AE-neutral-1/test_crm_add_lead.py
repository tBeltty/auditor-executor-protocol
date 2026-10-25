"""Tests for CRM.add_lead: validation order, ids, scores, assignment, queue."""
import unittest

from crm import CRM, DuplicateLeadError


REPS = [
    {"id": "r1", "role": "rep", "capacity": 1},
    {"id": "r2", "role": "rep", "capacity": 1},
    {"id": "m1", "role": "manager", "capacity": 99},
]


class AddLeadTest(unittest.TestCase):
    def setUp(self):
        self.crm = CRM([dict(r) for r in REPS])

    def test_unknown_actor_raises_permission_error_first(self):
        # Rule: actor check runs before every other check.
        with self.assertRaises(PermissionError):
            self.crm.add_lead("not-an-email", "", "bogus", "ghost")

    def test_email_must_be_str(self):
        with self.assertRaises(ValueError):
            self.crm.add_lead(123, "Ann", "web", "m1")
        with self.assertRaises(ValueError):
            self.crm.add_lead(None, "Ann", "web", "m1")

    def test_email_requires_exactly_one_at(self):
        for bad in ["plainaddress", "a@@b.com", "a@b@c.com"]:
            with self.assertRaises(ValueError):
                self.crm.add_lead(bad, "Ann", "web", "m1")

    def test_email_requires_nonempty_local_part(self):
        with self.assertRaises(ValueError):
            self.crm.add_lead("@example.com", "Ann", "web", "m1")

    def test_domain_requires_inner_dot(self):
        # dot missing, dot first, dot last: all invalid
        for bad in ["a@example", "a@.com", "a@com.", "a@x.", "a@.x"]:
            with self.assertRaises(ValueError):
                self.crm.add_lead(bad, "Ann", "web", "m1")
        self.crm.add_lead("a@x.y", "Ann", "web", "m1")  # inner dot ok
        self.crm.add_lead("a@sub.example.co.uk", "Bob", "web", "m1")  # multi-dot ok

    def test_name_must_be_nonempty_str(self):
        with self.assertRaises(ValueError):
            self.crm.add_lead("a@b.com", 5, "web", "m1")
        with self.assertRaises(ValueError):
            self.crm.add_lead("a@b.com", "", "web", "m1")
        with self.assertRaises(ValueError):
            self.crm.add_lead("a@b.com", "   ", "web", "m1")

    def test_source_must_be_valid(self):
        with self.assertRaises(ValueError):
            self.crm.add_lead("a@b.com", "Ann", "phone", "m1")

    def test_duplicate_raises_with_existing_id(self):
        first = self.crm.add_lead("  Ann@Example.COM  ", "Ann", "web", "m1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            self.crm.add_lead("ann@example.com", "Ann Two", "web", "m1")
        self.assertEqual(ctx.exception.existing_id, first)

    def test_duplicate_changes_nothing(self):
        first = self.crm.add_lead("ann@example.com", "Ann", "web", "m1")
        before_log = list(self.crm.log)
        with self.assertRaises(DuplicateLeadError):
            self.crm.add_lead("ANN@EXAMPLE.COM", "Other", "referral", "m1")
        self.assertEqual(self.crm.log, before_log)
        self.assertEqual(len(self.crm.leads), 1)
        # next id still increments from 1 -> 2, proving the dup did not consume a number
        second = self.crm.add_lead("bob@example.com", "Bob", "web", "m1")
        self.assertEqual(second, "L2")
        self.assertEqual(self.crm.leads[first]["id"], "L1")

    def test_failed_call_appends_nothing_to_log(self):
        with self.assertRaises(ValueError):
            self.crm.add_lead("bad-email", "Ann", "web", "m1")
        with self.assertRaises(PermissionError):
            self.crm.add_lead("a@b.com", "Ann", "web", "ghost")
        self.assertEqual(self.crm.log, [])
        self.assertEqual(self.crm.leads, {})

    def test_normalization_and_stripping_stored(self):
        lid = self.crm.add_lead("  Ann@Example.COM ", "  Ann Lee ", "web", "m1")
        lead = self.crm.leads[lid]
        self.assertEqual(lead["email"], "ann@example.com")
        self.assertEqual(lead["name"], "Ann Lee")
        self.assertEqual(lead["status"], "new")
        self.assertEqual(
            set(lead),
            {"id", "email", "name", "source", "score", "owner", "status"},
        )

    def test_scores(self):
        cases = [
            ("a@gmail.com", "web", 10),
            ("b@yahoo.com", "referral", 30),
            ("c@outlook.com", "event", 20),
            ("d@example.com", "web", 25),
            ("e@example.com", "referral", 45),
            ("f@example.com", "event", 35),
        ]
        for i, (email, source, expected) in enumerate(cases):
            lid = self.crm.add_lead(
                email, "N{}".format(i), source, "m1"
            )
            # owners vary (capacity 1 reps); score is independent of assignment
            self.assertEqual(self.crm.leads[lid]["score"], expected, email)

    def test_ids_count_successes_starting_at_1(self):
        self.assertEqual(self.crm.add_lead("a@x.com", "A", "web", "m1"), "L1")
        with self.assertRaises(ValueError):
            self.crm.add_lead("bad", "B", "web", "m1")
        self.assertEqual(self.crm.add_lead("b@x.com", "B", "web", "m1"), "L2")
        self.assertEqual(
            self.crm.log,
            [("add_lead", "L1", "m1"), ("add_lead", "L2", "m1")],
        )

    def test_assignment_picks_lowest_load_below_capacity(self):
        l1 = self.crm.add_lead("a@x.com", "A", "web", "m1")
        self.assertEqual(self.crm.leads[l1]["owner"], "r1")  # tie -> smallest id
        l2 = self.crm.add_lead("b@x.com", "B", "web", "m1")
        self.assertEqual(self.crm.leads[l2]["owner"], "r2")  # r1 now at capacity

    def test_queue_when_no_capacity(self):
        self.crm.add_lead("a@x.com", "A", "web", "m1")
        self.crm.add_lead("b@x.com", "B", "web", "m1")
        l3 = self.crm.add_lead("c@x.com", "C", "web", "m1")
        self.assertIsNone(self.crm.leads[l3]["owner"])
        self.assertEqual(self.crm.leads[l3]["status"], "new")
        # queued lead still logs add_lead
        self.assertEqual(self.crm.log[-1], ("add_lead", l3, "m1"))

    def test_rep_can_add_own_lead(self):
        lid = self.crm.add_lead("a@x.com", "A", "web", "r1")
        self.assertEqual(self.crm.leads[lid]["owner"], "r1")

    def test_tie_break_is_string_order(self):
        crm = CRM([
            {"id": "r10", "role": "rep", "capacity": 5},
            {"id": "r2", "role": "rep", "capacity": 5},
        ])
        lid = crm.add_lead("a@x.com", "A", "web", "r2")
        self.assertEqual(crm.leads[lid]["owner"], "r10")  # "r10" < "r2" as strings

    def test_tie_break_is_string_order_not_insertion_order(self):
        # Guard for spec add_lead step 6: ties break by smallest id in STRING
        # order, never by the first-encountered minimum-load rep. With
        # [r10, r2] the first candidate is also the string-minimum, so that
        # case alone cannot tell the two rules apart; the reverse insertion
        # order below can.
        crm = CRM([
            {"id": "r2", "role": "rep", "capacity": 5},
            {"id": "r10", "role": "rep", "capacity": 5},
        ])
        lid = crm.add_lead("a@x.com", "A", "web", "r2")
        self.assertEqual(crm.leads[lid]["owner"], "r10")
        # Three-way tie: string order ("a9" < "r10" < "r2") differs from
        # insertion order in every position except the first.
        crm3 = CRM([
            {"id": "r2", "role": "rep", "capacity": 5},
            {"id": "r10", "role": "rep", "capacity": 5},
            {"id": "a9", "role": "rep", "capacity": 5},
        ])
        lid3 = crm3.add_lead("a@x.com", "A", "web", "r2")
        self.assertEqual(crm3.leads[lid3]["owner"], "a9")

    def test_qualified_leads_count_toward_capacity_and_drain(self):
        # Guard for spec "General rules" load: a rep's load counts leads
        # with status "new" OR "qualified". Qualifying a lead must not
        # magically free the rep's slot.
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 9},
        ])
        l1 = crm.add_lead("a@x.com", "A", "referral", "m1")  # -> r1 (load 1)
        self.assertEqual(crm.leads[l1]["owner"], "r1")
        crm.qualify(l1, "m1")  # still "r1"'s work: status is qualified, not new
        l2 = crm.add_lead("b@x.com", "B", "web", "m1")
        self.assertIsNone(crm.leads[l2]["owner"])  # r1 still at capacity -> queued
        # Converting keeps the slot occupied (open opportunity, load still 1).
        oid = crm.convert(l1, 1000, "m1")
        self.assertIsNone(crm.leads[l2]["owner"])
        # Only reaching a final stage frees the slot and drains the queue.
        crm.advance(oid, "proposal", "m1")
        self.assertIsNone(crm.leads[l2]["owner"])
        crm.advance(oid, "negotiation", "m1")
        self.assertIsNone(crm.leads[l2]["owner"])
        crm.advance(oid, "won", "m1")
        self.assertEqual(crm.leads[l2]["owner"], "r1")
        self.assertEqual(
            crm.log[-2:], [("advance", oid, "m1"), ("assign", l2, "system")]
        )

    def test_source_check_runs_before_duplicate_check(self):
        # Guard for spec add_lead check order (steps 3 then 4): with an
        # existing email AND an invalid source, the source ValueError is what
        # the "first failing check decides" rule requires, not
        # DuplicateLeadError. Same for an invalid name (step 2) vs duplicate
        # (step 4). Swapping the checks in the implementation passes every
        # other test but fails this one.
        first = self.crm.add_lead("a@x.com", "A", "web", "m1")
        with self.assertRaises(ValueError) as ctx:
            self.crm.add_lead("a@x.com", "A", "phone", "m1")
        self.assertNotIsInstance(ctx.exception, DuplicateLeadError)
        with self.assertRaises(ValueError) as ctx:
            self.crm.add_lead("a@x.com", 5, "web", "m1")
        self.assertNotIsInstance(ctx.exception, DuplicateLeadError)
        # Nothing changed: no extra lead, no extra log entry, no id consumed.
        self.assertEqual(len(self.crm.leads), 1)
        self.assertEqual(self.crm.log, [("add_lead", first, "m1")])
        second = self.crm.add_lead("b@x.com", "B", "web", "m1")
        self.assertEqual(second, "L2")

    def test_duplicate_lead_error_is_not_a_value_error(self):
        # Guard for spec section 1: DuplicateLeadError derives from Exception
        # directly. Reparenting it to ValueError would make callers catching
        # validation errors silently swallow duplicates and collapse the
        # spec's ValueError-vs-DuplicateLeadError distinction.
        self.assertTrue(issubclass(DuplicateLeadError, Exception))
        self.assertFalse(issubclass(DuplicateLeadError, ValueError))

    def test_no_reps_at_all_goes_to_queue(self):
        crm = CRM([{"id": "m1", "role": "manager", "capacity": 10}])
        lid = crm.add_lead("a@x.com", "A", "web", "m1")
        self.assertIsNone(crm.leads[lid]["owner"])


if __name__ == "__main__":
    unittest.main()
