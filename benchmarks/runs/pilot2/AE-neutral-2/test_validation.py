"""Tests for add_lead validation, duplicate detection, assignment and capacity."""

import unittest

from crm import CRM, DuplicateLeadError
from crm_fixtures import add, wide_crm


class TestEmailValidation(unittest.TestCase):
    def test_email_must_be_a_string(self):
        for email in (None, 42, 3.5, b"a@b.com", ["a@b.com"], {"e": "a@b.com"}):
            with self.subTest(email=email):
                crm = wide_crm()
                with self.assertRaises(ValueError):
                    crm.add_lead(email, "Lead", "web", "r1")
                self.assertEqual(crm.leads, {})
                self.assertEqual(crm.log, [])

    def test_email_requires_exactly_one_at(self):
        bad = ["ab.com", "a@@b.com", "a@b@c.com", "@@b.com", "a@b.com@c.com"]
        for email in bad:
            with self.subTest(email=email):
                crm = wide_crm()
                with self.assertRaises(ValueError):
                    crm.add_lead(email, "Lead", "web", "r1")
                self.assertEqual(crm.leads, {})
                self.assertEqual(crm.log, [])

    def test_email_requires_non_empty_local_part(self):
        for email in ("@corp.com", "   @corp.com", "@"):
            with self.subTest(email=email):
                crm = wide_crm()
                with self.assertRaises(ValueError):
                    crm.add_lead(email, "Lead", "web", "r1")
                self.assertEqual(crm.leads, {})

    def test_email_requires_a_domain(self):
        for email in ("a@", "a@   ", "a@ "):
            with self.subTest(email=email):
                crm = wide_crm()
                with self.assertRaises(ValueError):
                    crm.add_lead(email, "Lead", "web", "r1")
                self.assertEqual(crm.leads, {})

    def test_email_domain_requires_an_interior_dot(self):
        bad = ["a@b", "a@.com", "a@com.", "a@.", "a@..", "a@.b."]
        for email in bad:
            with self.subTest(email=email):
                crm = wide_crm()
                with self.assertRaises(ValueError):
                    crm.add_lead(email, "Lead", "web", "r1")
                self.assertEqual(crm.leads, {})
                self.assertEqual(crm.log, [])

    def test_email_normalized_before_storage(self):
        crm = wide_crm()
        lead_id = crm.add_lead("  Alice@Corp.COM  ", "  Alice  ", "web", "r1")
        lead = crm.leads[lead_id]
        self.assertEqual(lead["email"], "alice@corp.com")
        self.assertEqual(lead["name"], "Alice")

    def test_valid_email_shapes(self):
        valid = ["a@b.co", "a.b@sub.domain.org", "x@b-c.co.uk", "a@b..c"]
        crm = wide_crm()
        for index, email in enumerate(valid):
            with self.subTest(email=email):
                lead_id = crm.add_lead(email, "Lead", "web", "r1")
                self.assertEqual(crm.leads[lead_id]["email"], email.lower())

    def test_failed_validation_does_not_consume_lead_id(self):
        crm = wide_crm()
        with self.assertRaises(ValueError):
            crm.add_lead("not-an-email", "Lead", "web", "r1")
        self.assertEqual(crm.add_lead("a@b.com", "Lead", "web", "r1"), "L1")


class TestNameValidation(unittest.TestCase):
    def test_name_must_be_non_empty_string(self):
        for name in ("", "   ", "\t\n", None, 42, ["Lead"], b"Lead"):
            with self.subTest(name=name):
                crm = wide_crm()
                with self.assertRaises(ValueError):
                    crm.add_lead("a@corp.com", name, "web", "r1")
                self.assertEqual(crm.leads, {})
                self.assertEqual(crm.log, [])

    def test_name_is_stripped(self):
        crm = wide_crm()
        lead_id = crm.add_lead("a@corp.com", "  Bob  ", "web", "r1")
        self.assertEqual(crm.leads[lead_id]["name"], "Bob")


class TestSourceValidation(unittest.TestCase):
    def test_source_must_be_allowed_value(self):
        for source in ("phone", "", "WEB", "web ", None, 1, ["web"]):
            with self.subTest(source=source):
                crm = wide_crm()
                with self.assertRaises(ValueError):
                    crm.add_lead("a@corp.com", "Lead", source, "r1")
                self.assertEqual(crm.leads, {})
                self.assertEqual(crm.log, [])

    def test_source_controls_score(self):
        crm = wide_crm()
        web = crm.add_lead("w@corp.com", "W", "web", "r1")
        referral = crm.add_lead("r@corp.com", "R", "referral", "r1")
        event = crm.add_lead("e@corp.com", "E", "event", "r1")
        self.assertEqual(crm.leads[web]["score"], 25)
        self.assertEqual(crm.leads[referral]["score"], 45)
        self.assertEqual(crm.leads[event]["score"], 35)

    def test_free_email_domains_get_no_boost(self):
        crm = wide_crm()
        for domain in ("gmail.com", "yahoo.com", "outlook.com"):
            with self.subTest(domain=domain):
                lead_id = crm.add_lead("a@%s" % domain, "Lead", "web", "r1")
                self.assertEqual(crm.leads[lead_id]["score"], 10)


class TestDuplicateDetection(unittest.TestCase):
    def test_duplicate_raises_with_existing_id(self):
        crm = wide_crm()
        first = add(crm, email="User@Corp.com")
        with self.assertRaises(DuplicateLeadError) as ctx:
            crm.add_lead(" user@corp.COM ", "Other", "web", "r2")
        self.assertEqual(ctx.exception.existing_id, first)
        self.assertEqual(list(crm.leads), [first])
        self.assertEqual(crm.log, [("add_lead", first, "r1")])

    def test_duplicate_check_uses_normalized_email(self):
        crm = wide_crm()
        add(crm, email="a.b@corp.com")
        for email in ("A.B@CORP.COM", "  a.b@corp.com  ", "a.b@corp.com"):
            with self.subTest(email=email):
                with self.assertRaises(DuplicateLeadError):
                    crm.add_lead(email, "Other", "event", "r2")

    def test_source_is_validated_before_duplicate(self):
        crm = wide_crm()
        add(crm, email="a@corp.com")
        with self.assertRaises(ValueError):
            crm.add_lead("a@corp.com", "Other", "fax", "r1")

    def test_failed_duplicate_does_not_consume_id_or_log(self):
        crm = wide_crm()
        first = add(crm, email="a@corp.com")
        with self.assertRaises(DuplicateLeadError):
            crm.add_lead("a@corp.com", "Other", "web", "r1")
        second = crm.add_lead("b@corp.com", "Other", "web", "r1")
        self.assertEqual(second, "L2")
        self.assertEqual(crm.log, [("add_lead", first, "r1"), ("add_lead", second, "r1")])


class TestAssignmentAndCapacity(unittest.TestCase):
    def test_tie_broken_by_smallest_id(self):
        crm = CRM(
            [
                {"id": "b", "role": "rep", "capacity": 5},
                {"id": "a", "role": "rep", "capacity": 5},
            ]
        )
        lead_id = add(crm, email="x@corp.com", actor="a")
        self.assertEqual(crm.leads[lead_id]["owner"], "a")

    def test_lowest_load_wins(self):
        crm = wide_crm()
        first = add(crm, email="a@corp.com")
        second = add(crm, email="b@corp.com")
        self.assertEqual(crm.leads[first]["owner"], "r1")
        self.assertEqual(crm.leads[second]["owner"], "r2")

    def test_open_opportunities_count_against_capacity(self):
        crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 1},
                {"id": "r2", "role": "rep", "capacity": 1},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        first = add(crm, email="a@corp.com")
        crm.qualify(first, "m1")
        crm.convert(first, 1000, "m1")
        # r1's converted lead is replaced by the open opportunity: still one slot.
        second = add(crm, email="b@corp.com")
        self.assertEqual(crm.leads[second]["owner"], "r2")
        third = add(crm, email="c@corp.com")
        self.assertIsNone(crm.leads[third]["owner"])

    def test_full_capacity_queues_lead(self):
        crm = CRM(
            [
                {"id": "a", "role": "rep", "capacity": 1},
                {"id": "b", "role": "rep", "capacity": 1},
            ]
        )
        first = add(crm, email="a@corp.com", actor="a")
        second = add(crm, email="b@corp.com", actor="a")
        third = add(crm, email="c@corp.com", actor="a")
        self.assertEqual(crm.leads[first]["owner"], "a")
        self.assertEqual(crm.leads[second]["owner"], "b")
        self.assertIsNone(crm.leads[third]["owner"])

    def test_managers_never_receive_work(self):
        crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 1},
                {"id": "m1", "role": "manager", "capacity": 10},
            ]
        )
        first = add(crm, email="a@corp.com")
        second = add(crm, email="b@corp.com")
        self.assertEqual(crm.leads[first]["owner"], "r1")
        self.assertIsNone(crm.leads[second]["owner"])

    def test_final_stage_frees_slot_and_assigns_waiting_lead(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1}])
        first = add(crm, email="a@corp.com")
        waiting = add(crm, email="b@corp.com")
        self.assertIsNone(crm.leads[waiting]["owner"])
        crm.qualify(first, "r1")
        opp_id = crm.convert(first, 1000, "r1")
        crm.advance(opp_id, "lost", "r1")
        self.assertEqual(crm.leads[waiting]["owner"], "r1")
        self.assertEqual(crm.log[-1], ("assign", waiting, "system"))

    def test_won_frees_slot_and_assigns_waiting_lead(self):
        """Spec line 31: every final stage frees the slot, not just 'lost'."""
        crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 1},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        first = add(crm, email="a@corp.com")
        waiting = add(crm, email="b@corp.com")
        self.assertIsNone(crm.leads[waiting]["owner"])
        crm.qualify(first, "r1")
        opp_id = crm.convert(first, 1000, "r1")
        for stage in ("proposal", "negotiation", "won"):
            crm.advance(opp_id, stage, "r1")
        self.assertEqual(crm.leads[waiting]["owner"], "r1")
        self.assertEqual(crm.log[-1], ("assign", waiting, "system"))

    def test_manager_finalization_assigns_waiting_lead_to_the_owner(self):
        """Spec line 31: the drain targets the opportunity owner, not the actor."""
        crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 1},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        first = add(crm, email="a@corp.com")
        waiting = add(crm, email="b@corp.com")
        self.assertIsNone(crm.leads[waiting]["owner"])
        crm.qualify(first, "m1")
        opp_id = crm.convert(first, 1000, "m1")
        self.assertEqual(crm.opps[opp_id]["owner"], "r1")
        crm.advance(opp_id, "lost", "m1")  # actor is the manager
        self.assertEqual(crm.leads[waiting]["owner"], "r1")
        self.assertEqual(crm.log[-1], ("assign", waiting, "system"))

    def test_owned_leads_never_join_the_waiting_queue(self):
        """Spec step 6: only leads left without an owner join the queue."""
        crm = wide_crm()
        first = add(crm, email="a@corp.com")
        self.assertEqual(crm.leads[first]["owner"], "r1")
        crm.qualify(first, "r1")
        opp_id = crm.convert(first, 1000, "r1")
        crm.advance(opp_id, "lost", "r1")
        self.assertEqual(
            [entry for entry in crm.log if entry[0] == "assign"], []
        )
        self.assertEqual(crm.log[-1], ("advance", opp_id, "r1"))

    def test_waiting_queue_is_fifo_and_drains_multiple_slots(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 2}])
        l1 = add(crm, email="1@corp.com")
        l2 = add(crm, email="2@corp.com")
        l3 = add(crm, email="3@corp.com")
        l4 = add(crm, email="4@corp.com")
        self.assertEqual(crm.leads[l1]["owner"], "r1")
        self.assertEqual(crm.leads[l2]["owner"], "r1")
        self.assertIsNone(crm.leads[l3]["owner"])
        self.assertIsNone(crm.leads[l4]["owner"])

        crm.qualify(l1, "r1")
        o1 = crm.convert(l1, 1000, "r1")
        crm.qualify(l2, "r1")
        o2 = crm.convert(l2, 2000, "r1")

        crm.advance(o1, "lost", "r1")
        self.assertEqual(crm.leads[l3]["owner"], "r1")
        self.assertIsNone(crm.leads[l4]["owner"])
        self.assertEqual(crm.log[-1], ("assign", l3, "system"))

        crm.advance(o2, "lost", "r1")
        self.assertEqual(crm.leads[l4]["owner"], "r1")
        self.assertEqual(crm.log[-1], ("assign", l4, "system"))

    def test_qualified_lead_still_counts_and_converted_lead_does_not(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 2}])
        first = add(crm, email="a@corp.com")
        crm.qualify(first, "r1")
        second = add(crm, email="b@corp.com")
        self.assertEqual(crm.leads[second]["owner"], "r1")
        third = add(crm, email="c@corp.com")
        self.assertIsNone(crm.leads[third]["owner"])


if __name__ == "__main__":
    unittest.main()
