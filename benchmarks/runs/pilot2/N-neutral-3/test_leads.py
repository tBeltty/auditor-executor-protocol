"""Lead intake, validation, assignment and qualification tests."""

import unittest

from crm import CRM, DuplicateLeadError


def staff():
    return [
        {"id": "r1", "role": "rep", "capacity": 3},
        {"id": "r2", "role": "rep", "capacity": 2},
        {"id": "m1", "role": "manager", "capacity": 9},
    ]


class TestActorValidation(unittest.TestCase):
    def test_unknown_actor_is_a_permission_error_everywhere(self):
        crm = CRM(staff())
        lead = crm.add_lead("buyer@acme.com", "Buyer", "referral", "r1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 1000, "r1")
        for call in (
            lambda: crm.add_lead("x@acme.com", "X", "web", "ghost"),
            lambda: crm.qualify(lead, "ghost"),
            lambda: crm.convert(lead, 1000, "ghost"),
            lambda: crm.advance(opp, "proposal", "ghost"),
            lambda: crm.discount(opp, 5, "ghost"),
            lambda: crm.transfer(opp, "r2", "ghost"),
        ):
            with self.assertRaises(PermissionError):
                call()
        self.assertEqual(len(crm.log), 3)
        self.assertEqual(crm.leads[lead]["status"], "converted")
        self.assertEqual(crm.opps[opp]["stage"], "prospect")

    def test_unknown_actor_flagrant_before_any_other_check(self):
        crm = CRM(staff())
        with self.assertRaises(PermissionError):
            crm.add_lead(7, "", "ads", "ghost")
        with self.assertRaises(PermissionError):
            crm.qualify("L404", "ghost")

    def test_non_string_actor_is_a_permission_error(self):
        crm = CRM(staff())
        with self.assertRaises(PermissionError):
            crm.add_lead("a@b.com", "A", "web", None)
        self.assertEqual(crm.leads, {})


class TestEmailValidation(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(staff())

    def assert_rejected(self, email):
        with self.assertRaises(ValueError):
            self.crm.add_lead(email, "Name", "web", "r1")
        self.assertEqual(self.crm.leads, {})
        self.assertEqual(self.crm.log, [])

    def test_non_string_email(self):
        for bad in (None, 42, 3.5, ["a@b.com"]):
            self.assert_rejected(bad)

    def test_missing_or_multiple_at_signs(self):
        for bad in ("buyer.example.com", "buyer@@acme.com", "a@b@c.com"):
            self.assert_rejected(bad)

    def test_missing_local_part(self):
        for bad in ("@acme.com", "   @acme.com"):
            self.assert_rejected(bad)

    def test_missing_dot_in_domain(self):
        for bad in ("buyer@acme", "buyer@localhost", "buyer@acme."):
            self.assert_rejected(bad)

    def test_dot_that_is_first_or_last_character_of_domain(self):
        for bad in ("buyer@.com", "buyer@com.", "buyer@.com.", "buyer@."):
            self.assert_rejected(bad)

    def test_whitespace_is_stripped_and_persisted_normalized(self):
        lead = self.crm.add_lead("  Buyer@ACME.COM  ", "  Ada  ", "web", "r1")
        record = self.crm.leads[lead]
        self.assertEqual(record["email"], "buyer@acme.com")
        self.assertEqual(record["name"], "Ada")


class TestNameAndSourceValidation(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(staff())

    def test_invalid_names(self):
        for bad in ("", "   ", 5, None):
            with self.assertRaises(ValueError):
                self.crm.add_lead("buyer@acme.com", bad, "web", "r1")
            self.assertEqual(self.crm.leads, {})
            self.assertEqual(self.crm.log, [])

    def test_invalid_sources(self):
        for bad in ("ads", "WEB", "", None, "web "):
            with self.assertRaises(ValueError):
                self.crm.add_lead("buyer@acme.com", "Ada", bad, "r1")
            self.assertEqual(self.crm.leads, {})
            self.assertEqual(self.crm.log, [])

    def test_email_checked_before_name_and_source(self):
        with self.assertRaises(ValueError):
            self.crm.add_lead("bad", "", "ads", "r1")
        # name is the second check: a valid email with a bad name fails on name
        with self.assertRaises(ValueError):
            self.crm.add_lead("buyer@acme.com", "", "ads", "r1")


class TestDuplicates(unittest.TestCase):
    def test_duplicate_normalized_email_is_rejected(self):
        crm = CRM(staff())
        first = crm.add_lead("buyer@acme.com", "Ada", "web", "r1")
        for same in ("buyer@acme.com", "BUYER@ACME.COM", "  buyer@acme.com  "):
            with self.assertRaises(DuplicateLeadError) as caught:
                crm.add_lead(same, "Other", "referral", "r1")
            self.assertEqual(caught.exception.existing_id, first)
        self.assertEqual(list(crm.leads), [first])
        self.assertEqual(len(crm.log), 1)

    def test_duplicate_check_happens_before_id_allocation(self):
        crm = CRM(staff())
        first = crm.add_lead("buyer@acme.com", "Ada", "web", "r1")
        with self.assertRaises(DuplicateLeadError):
            crm.add_lead("buyer@acme.com", "Ada", "web", "r1")
        self.assertEqual(first, "L1")
        self.assertEqual(crm.add_lead("other@acme.com", "Bob", "web", "r1"), "L2")


class TestScore(unittest.TestCase):
    def test_base_scores_and_corporate_bonus(self):
        crm = CRM(staff())
        cases = {
            "a@acme.com": ("web", 25),
            "b@gmail.com": ("web", 10),
            "c@acme.com": ("referral", 45),
            "d@yahoo.com": ("referral", 30),
            "e@acme.com": ("event", 35),
            "f@outlook.com": ("event", 20),
        }
        for email, (source, expected) in cases.items():
            lead = crm.add_lead(email, "N", source, "r1")
            self.assertEqual(crm.leads[lead]["score"], expected, email)


class TestAssignment(unittest.TestCase):
    def test_smallest_id_wins_a_load_tie(self):
        crm = CRM([
            {"id": "r2", "role": "rep", "capacity": 5},
            {"id": "r1", "role": "rep", "capacity": 5},
        ])
        first = crm.add_lead("a@acme.com", "A", "web", "r2")
        second = crm.add_lead("b@acme.com", "B", "web", "r2")
        third = crm.add_lead("c@acme.com", "C", "web", "r2")
        self.assertEqual(crm.leads[first]["owner"], "r1")
        self.assertEqual(crm.leads[second]["owner"], "r2")
        self.assertEqual(crm.leads[third]["owner"], "r1")

    def test_lowest_load_wins(self):
        crm = CRM(staff())
        lead = crm.add_lead("a@acme.com", "A", "web", "r1")
        self.assertEqual(crm.leads[lead]["owner"], "r1")
        lead2 = crm.add_lead("b@acme.com", "B", "web", "r1")
        self.assertEqual(crm.leads[lead2]["owner"], "r2")
        lead3 = crm.add_lead("c@acme.com", "C", "web", "r1")
        self.assertEqual(crm.leads[lead3]["owner"], "r1")

    def test_qualified_leads_count_towards_load(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 1},
        ])
        first = crm.add_lead("a@acme.com", "A", "referral", "r1")
        crm.qualify(first, "r1")
        second = crm.add_lead("b@acme.com", "B", "web", "r1")
        self.assertEqual(crm.leads[second]["owner"], "r2")

    def test_manager_never_receives_work(self):
        crm = CRM([{"id": "m1", "role": "manager", "capacity": 5}])
        lead = crm.add_lead("a@acme.com", "A", "referral", "m1")
        self.assertIsNone(crm.leads[lead]["owner"])
        self.assertEqual(crm.waiting, [lead])

    def test_leads_queue_when_every_rep_is_at_capacity(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 1},
        ])
        first = crm.add_lead("a@acme.com", "A", "web", "r1")
        second = crm.add_lead("b@acme.com", "B", "web", "r1")
        third = crm.add_lead("c@acme.com", "C", "web", "r1")
        fourth = crm.add_lead("d@acme.com", "D", "web", "r1")
        self.assertEqual((crm.leads[first]["owner"], crm.leads[second]["owner"]), ("r1", "r2"))
        self.assertIsNone(crm.leads[third]["owner"])
        self.assertIsNone(crm.leads[fourth]["owner"])
        self.assertEqual(crm.waiting, [third, fourth])
        self.assertEqual(crm.load("r1"), 1)

    def test_waiting_queue_is_fifo_and_respects_capacity(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 0},
            {"id": "m1", "role": "manager", "capacity": 5},
        ])
        first = crm.add_lead("a@acme.com", "A", "referral", "r1")
        crm.qualify(first, "r1")
        opp = crm.convert(first, 1000, "r1")
        second = crm.add_lead("b@acme.com", "B", "web", "r1")
        third = crm.add_lead("c@acme.com", "C", "web", "r1")
        self.assertEqual(crm.waiting, [second, third])

        crm.advance(opp, "proposal", "r1")
        crm.advance(opp, "negotiation", "r1")
        crm.advance(opp, "won", "r1")

        self.assertEqual(crm.leads[second]["owner"], "r1")
        self.assertIsNone(crm.leads[third]["owner"])
        self.assertEqual(crm.waiting, [third])
        self.assertEqual(crm.log[-1], ("assign", second, "system"))
        self.assertEqual(crm.load("r1"), 1)

    def test_add_lead_log_shape(self):
        crm = CRM(staff())
        lead = crm.add_lead("a@acme.com", "A", "web", "m1")
        self.assertEqual(crm.log, [("add_lead", lead, "m1")])
        self.assertEqual(lead, "L1")


class TestQualify(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(staff())
        self.lead = self.crm.add_lead("buyer@acme.com", "Ada", "referral", "r1")

    def test_unknown_lead(self):
        with self.assertRaises(ValueError):
            self.crm.qualify("L999", "m1")

    def test_only_owner_or_manager_may_qualify(self):
        other_rep = self.crm.add_lead("b@acme.com", "B", "referral", "r2")
        with self.assertRaises(PermissionError):
            self.crm.qualify(other_rep, "r1")
        self.assertEqual(self.crm.leads[other_rep]["status"], "new")
        self.assertNotIn(("qualify", other_rep, "r1"), self.crm.log)

    def test_permission_is_checked_before_status(self):
        self.crm.qualify(self.lead, "r1")
        with self.assertRaises(PermissionError):
            self.crm.qualify(self.lead, "r2")
        self.assertEqual(self.crm.leads[self.lead]["status"], "qualified")

    def test_manager_may_qualify_another_reps_lead(self):
        self.crm.qualify(self.lead, "m1")
        self.assertEqual(self.crm.leads[self.lead]["status"], "qualified")
        self.assertEqual(self.crm.log[-1], ("qualify", self.lead, "m1"))

    def test_status_must_be_new(self):
        self.crm.qualify(self.lead, "r1")
        with self.assertRaises(ValueError):
            self.crm.qualify(self.lead, "r1")
        converted = self.crm.convert(self.lead, 500, "r1")
        self.assertEqual(self.crm.opps[converted]["stage"], "prospect")
        with self.assertRaises(ValueError):
            self.crm.qualify(self.lead, "m1")

    def test_score_threshold_is_thirty(self):
        low = self.crm.add_lead("web@gmail.com", "W", "web", "r2")
        self.assertEqual(self.crm.leads[low]["score"], 10)
        with self.assertRaises(ValueError):
            self.crm.qualify(low, "m1")
        self.assertEqual(self.crm.leads[low]["status"], "new")
        self.assertEqual(self.crm.log[-1], ("add_lead", low, "r2"))

        event = self.crm.add_lead("event@acme.com", "E", "event", "r2")
        self.assertEqual(self.crm.leads[event]["score"], 35)
        self.crm.qualify(event, "m1")
        self.assertEqual(self.crm.leads[event]["status"], "qualified")

        threshold = self.crm.add_lead("t@acme.com", "T", "referral", "r1")
        self.assertEqual(self.crm.leads[threshold]["score"], 45)
        self.crm.qualify(threshold, "m1")
        self.assertEqual(self.crm.leads[threshold]["status"], "qualified")

    def test_event_lead_at_twenty_is_rejected(self):
        crm = CRM(staff())
        lead = crm.add_lead("lead@outlook.com", "E", "event", "r1")
        self.assertEqual(crm.leads[lead]["score"], 20)
        with self.assertRaises(ValueError):
            crm.qualify(lead, "r1")
        self.assertEqual(crm.leads[lead]["status"], "new")
        self.assertEqual(len(crm.log), 1)

    def test_unowned_lead_needs_a_manager(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 0},
            {"id": "m1", "role": "manager", "capacity": 5},
        ])
        lead = crm.add_lead("a@acme.com", "A", "referral", "r1")
        self.assertIsNone(crm.leads[lead]["owner"])
        with self.assertRaises(PermissionError):
            crm.qualify(lead, "r1")
        crm.qualify(lead, "m1")
        self.assertEqual(crm.leads[lead]["status"], "qualified")


if __name__ == "__main__":
    unittest.main()
