"""Tests for CRM.add_lead: validation order, normalization, scoring, ownership."""

import unittest

from crm import DuplicateLeadError
from support import add, make_crm, snapshot


class TestActorFirst(unittest.TestCase):
    def test_unknown_actor_permission_error_beats_every_validation(self):
        crm = make_crm()
        with self.assertRaises(PermissionError):
            crm.add_lead("not-an-email", 42, "sms", "ghost")
        self.assertEqual(snapshot(crm), ({}, {}, []))

    def test_known_but_non_rep_actor_is_allowed_to_create(self):
        # A manager is a known actor; add_lead does not require ownership.
        crm = make_crm()
        lead_id = crm.add_lead("a@b.com", "N", "web", "m1")
        self.assertEqual(lead_id, "L1")
        self.assertEqual(crm.log, [("add_lead", "L1", "m1")])


class TestEmailValidation(unittest.TestCase):
    def test_email_must_be_str(self):
        crm = make_crm()
        for bad in (None, 5, b"a@b.com", ["a@b.com"], True):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    crm.add_lead(bad, "N", "web", "m1")

    def test_requires_exactly_one_at_sign(self):
        crm = make_crm()
        for bad in ("plainaddress", "a@@b.com", "a@b@c.com"):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    crm.add_lead(bad, "N", "web", "m1")

    def test_local_part_must_be_non_empty(self):
        crm = make_crm()
        with self.assertRaises(ValueError):
            crm.add_lead("@b.com", "N", "web", "m1")

    def test_domain_needs_a_dot_that_is_neither_first_nor_last(self):
        crm = make_crm()
        for bad in ("a@b", "a@.com", "a@com.", "a@.", "a@b.", "a@.b"):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    crm.add_lead(bad, "N", "web", "m1")

    def test_domain_dot_rule_is_existential_per_spec_literal_wording(self):
        # Spec: the domain must "contain a '.' which is neither the first nor
        # the last character". "b.com." and ".b.com" each contain such an
        # interior dot, so the literal rule accepts them even though they also
        # carry a leading/trailing dot; a leading/trailing dot with no
        # interior dot rejects. Decision logged in the compliance log as a
        # resolved ambiguity.
        crm = make_crm()
        for good in ("a@b.com.", "a@.b.com", "a@b..c", "a@b.c"):
            with self.subTest(good=good):
                crm.add_lead(good, "N", "web", "m1")
        self.assertEqual(len(crm.leads), 4)


    def test_valid_edge_domain_shapes(self):
        crm = make_crm()
        for good in ("a@b.c", "a@sub.example.com", "a@x.y.z"):
            with self.subTest(good=good):
                crm.add_lead(good, "N", "web", "m1")
        self.assertEqual(len(crm.leads), 3)

    def test_normalization_strips_and_lowercases(self):
        crm = make_crm()
        lead_id = crm.add_lead("  John.Doe@Gmail.COM  ", " N ", "web", "m1")
        self.assertEqual(crm.leads[lead_id]["email"], "john.doe@gmail.com")

    def test_normalized_duplicate_collides_across_case_and_spaces(self):
        crm = make_crm()
        first = crm.add_lead("a@b.com", "N", "web", "m1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            crm.add_lead("  A@B.COM ", "N2", "event", "m1")
        self.assertEqual(ctx.exception.existing_id, first)

    def test_duplicate_error_is_not_a_value_error(self):
        crm = make_crm()
        crm.add_lead("a@b.com", "N", "web", "m1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            crm.add_lead("a@b.com", "N", "web", "m1")
        self.assertNotIsInstance(ctx.exception, ValueError)
        self.assertIsInstance(ctx.exception, Exception)
        self.assertEqual(ctx.exception.existing_id, "L1")


class TestNameAndSourceValidation(unittest.TestCase):
    def test_name_must_be_non_empty_str_after_strip(self):
        crm = make_crm()
        for bad in (None, 7, "", "   ", "\t\n"):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    crm.add_lead("a@b.com", bad, "web", "m1")

    def test_name_is_stored_stripped(self):
        crm = make_crm()
        lead_id = crm.add_lead("a@b.com", "  Ada Lovelace  ", "web", "m1")
        self.assertEqual(crm.leads[lead_id]["name"], "Ada Lovelace")

    def test_source_restricted(self):
        crm = make_crm()
        for bad in ("phone", "WEB", "", None, 1):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    crm.add_lead("a@b.com", "N", bad, "m1")
        for good in ("web", "referral", "event"):
            with self.subTest(good=good):
                crm.add_lead(good + "@example.org", "N", good, "m1")

    def test_source_check_runs_before_duplicate_check(self):
        # Existing duplicate email + invalid source -> ValueError, not
        # DuplicateLeadError (check order: email, name, source, duplicate).
        crm = make_crm()
        crm.add_lead("a@b.com", "N", "web", "m1")
        with self.assertRaises(ValueError):
            crm.add_lead("a@b.com", "N", "sms", "m1")

    def test_name_check_runs_before_source_and_duplicate(self):
        crm = make_crm()
        crm.add_lead("a@b.com", "N", "web", "m1")
        with self.assertRaises(ValueError):
            crm.add_lead("a@b.com", "", "sms", "m1")  # bad name before dup check


class TestScoring(unittest.TestCase):
    def _score(self, email, source):
        crm = make_crm()
        lead_id = crm.add_lead(email, "N", source, "m1")
        return crm.leads[lead_id]["score"]

    def test_base_scores(self):
        self.assertEqual(self._score("a@example.com", "web"), 25)
        self.assertEqual(self._score("a@example.com", "referral"), 45)
        self.assertEqual(self._score("a@example.com", "event"), 35)

    def test_free_domains_get_no_bonus(self):
        for domain in ("gmail.com", "yahoo.com", "outlook.com"):
            with self.subTest(domain=domain):
                self.assertEqual(self._score("a@" + domain, "web"), 10)
                self.assertEqual(self._score("a@" + domain, "referral"), 30)
                self.assertEqual(self._score("a@" + domain, "event"), 20)

    def test_bonus_uses_normalized_domain_case(self):
        self.assertEqual(self._score("a@GMAIL.COM", "web"), 10)
        self.assertEqual(self._score("a@Example.ORG", "web"), 25)

    def test_subdomain_of_free_domain_still_gets_bonus(self):
        self.assertEqual(self._score("a@mail.gmail.com", "web"), 25)


class TestIdsAndCounters(unittest.TestCase):
    def test_ids_count_only_successful_creations(self):
        crm = make_crm()
        with self.assertRaises(ValueError):
            crm.add_lead("bad-email", "N", "web", "m1")
        with self.assertRaises(PermissionError):
            crm.add_lead("a@b.com", "N", "web", "ghost")
        self.assertEqual(crm.add_lead("a@b.com", "N", "web", "m1"), "L1")
        self.assertEqual(crm.add_lead("c@d.com", "N", "web", "m1"), "L2")

    def test_failed_call_leaves_no_trace(self):
        crm = make_crm()
        lead_id = crm.add_lead("a@b.com", "N", "web", "m1")
        before = snapshot(crm)
        with self.assertRaises(ValueError):
            crm.add_lead("a@b.com", "N", "sms", "m1")
        self.assertEqual(snapshot(crm), before)


class TestLeadShape(unittest.TestCase):
    def test_lead_fields_exactly_as_specified(self):
        crm = make_crm()
        lead_id = crm.add_lead("  Bob@Example.com ", " Bob ", "referral", "m1")
        self.assertEqual(
            crm.leads[lead_id],
            {
                "id": "L1",
                "email": "bob@example.com",
                "name": "Bob",
                "source": "referral",
                "score": 45,
                "owner": "r1",
                "status": "new",
            },
        )
        self.assertEqual(list(crm.leads), ["L1"])


class TestRoutingAndQueue(unittest.TestCase):
    def test_lowest_load_then_smallest_id_string(self):
        crm = make_crm()
        l1 = add(crm, "1@b.com")
        l2 = add(crm, "2@b.com")
        l3 = add(crm, "3@b.com")
        # r1 (cap 2) takes L1 (load 0 tie, "r1" < "r2"), r2 takes L2, r1 takes L3.
        self.assertEqual([crm.leads[x]["owner"] for x in (l1, l2, l3)], ["r1", "r2", "r1"])
        self.assertEqual(
            crm.log,
            [("add_lead", "L1", "m1"), ("add_lead", "L2", "m1"), ("add_lead", "L3", "m1")],
        )

    def test_ties_broken_by_string_order_not_length_or_insertion(self):
        reps = [
            {"id": "b1", "role": "rep", "capacity": 1},
            {"id": "aa", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 0},
        ]
        crm = make_crm(reps)
        lead_id = add(crm, "1@b.com")
        self.assertEqual(crm.leads[lead_id]["owner"], "aa")  # "aa" < "b1" in string order

    def test_full_capacity_sends_lead_to_waiting_queue(self):
        crm = make_crm()
        add(crm, "1@b.com")
        add(crm, "2@b.com")
        add(crm, "3@b.com")
        queued = add(crm, "4@b.com")
        self.assertIsNone(crm.leads[queued]["owner"])

    def test_zero_capacity_rep_never_receives_work(self):
        reps = [
            {"id": "r0", "role": "rep", "capacity": 0},
            {"id": "m1", "role": "manager", "capacity": 5},
        ]
        crm = make_crm(reps)
        lead_id = add(crm, "1@b.com")
        self.assertIsNone(crm.leads[lead_id]["owner"])

    def test_managers_never_own_anything(self):
        reps = [{"id": "m1", "role": "manager", "capacity": 9}]
        crm = make_crm(reps)
        for i in range(3):
            lead_id = add(crm, "%d@b.com" % i)
            self.assertIsNone(crm.leads[lead_id]["owner"])

    def test_lead_created_by_rep_actor_is_still_routed_by_load(self):
        crm = make_crm()
        lead_id = crm.add_lead("1@b.com", "N", "web", "r2")
        self.assertEqual(crm.leads[lead_id]["owner"], "r1")
        self.assertEqual(crm.log[-1], ("add_lead", "L1", "r2"))


class TestLoadDefinition(unittest.TestCase):
    SOLO = [{"id": "solo", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 0}]

    def test_only_new_and_qualified_leads_count(self):
        crm = make_crm(self.SOLO)
        l1 = add(crm, "1@b.com", source="referral")  # owner solo (load 0)
        self.assertEqual(crm.leads[l1]["owner"], "solo")
        queued = add(crm, "2@b.com")  # solo at capacity (l1 is "new")
        self.assertIsNone(crm.leads[queued]["owner"])
        # qualifying keeps the lead counted in load; nothing is drained here
        crm.qualify(l1, "m1")
        l3 = add(crm, "3@b.com")
        self.assertIsNone(crm.leads[l3]["owner"])

    def test_converted_lead_stops_counting_but_open_opportunity_counts(self):
        crm = make_crm(self.SOLO)
        l1 = add(crm, "1@b.com", source="referral")
        crm.qualify(l1, "m1")
        opp_id = crm.convert(l1, 100, "m1")
        # lead l1 is now "converted" (no lead load), but O1 is open (1 opp load)
        self.assertEqual(crm.leads[l1]["status"], "converted")
        l2 = add(crm, "2@b.com")
        self.assertIsNone(crm.leads[l2]["owner"])  # solo load is still 1 == capacity

    def test_won_or_lost_opportunity_stops_counting(self):
        crm = make_crm(self.SOLO)
        l1 = add(crm, "1@b.com", source="referral")
        crm.qualify(l1, "m1")
        opp_id = crm.convert(l1, 100, "m1")
        l2 = add(crm, "2@b.com")
        self.assertIsNone(crm.leads[l2]["owner"])
        for stage in ("proposal", "negotiation", "won"):
            crm.advance(opp_id, stage, "m1")
        # the win freed solo's slot and the waiting L2 was assigned to it
        self.assertEqual(crm.leads[l2]["owner"], "solo")
        self.assertEqual(crm.leads[l2]["status"], "new")
        self.assertEqual(crm.log[-1], ("assign", "L2", "system"))

    def test_losing_also_stops_counting(self):
        crm = make_crm(self.SOLO)
        l1 = add(crm, "1@b.com", source="referral")
        crm.qualify(l1, "m1")
        opp_id = crm.convert(l1, 100, "m1")
        l2 = add(crm, "2@b.com")
        crm.advance(opp_id, "lost", "m1")
        self.assertEqual(crm.leads[l2]["owner"], "solo")

    def test_manager_only_crm_queues_everything(self):
        crm = make_crm([{"id": "m1", "role": "manager", "capacity": 3}])
        for i in range(3):
            lead_id = add(crm, "%d@b.com" % i)
            self.assertIsNone(crm.leads[lead_id]["owner"])
            self.assertEqual(crm.log[-1], ("add_lead", lead_id, "m1"))



if __name__ == "__main__":
    unittest.main()
