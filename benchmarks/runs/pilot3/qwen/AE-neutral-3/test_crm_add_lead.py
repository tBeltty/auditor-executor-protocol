"""Spec lines 4, 6-7, 12-19: construction, actor check, add_lead."""

import unittest

from crm import CRM, DuplicateLeadError


def base_crm():
    return CRM([
        {"id": "r1", "role": "rep", "capacity": 1},
        {"id": "r2", "role": "rep", "capacity": 2},
        {"id": "m1", "role": "manager", "capacity": 5},
    ])


class TestRequiredAttributes(unittest.TestCase):
    """Line 5: leads, opps, log exist with the stated shapes."""

    def test_crm_starts_with_empty_leads_opps_and_log(self):
        crm = base_crm()
        self.assertIsInstance(crm.leads, dict)
        self.assertIsInstance(crm.opps, dict)
        self.assertIsInstance(crm.log, list)
        self.assertEqual(crm.leads, {})
        self.assertEqual(crm.opps, {})
        self.assertEqual(crm.log, [])

    def test_log_entries_are_tuples_of_op_entity_actor(self):
        crm = base_crm()
        crm.add_lead("a@corp.com", "Ann", "web", "m1")
        self.assertEqual(crm.log, [("add_lead", "L1", "m1")])
        self.assertIsInstance(crm.log[0], tuple)
        self.assertEqual(len(crm.log[0]), 3)


class TestUnknownActorFirst(unittest.TestCase):
    """Line 7: unknown actor -> PermissionError, checked first in every method."""

    def setUp(self):
        self.crm = base_crm()
        self.lead = self.crm.add_lead("a@corp.com", "Ann", "referral", "m1")
        self.crm.qualify(self.lead, "r1")
        self.opp = self.crm.convert(self.lead, 1000, "r1")

    def test_add_lead_unknown_actor(self):
        with self.assertRaises(PermissionError):
            self.crm.add_lead("a@corp.com", "Ann", "web", "ghost")

    def test_qualify_unknown_actor(self):
        with self.assertRaises(PermissionError):
            self.crm.qualify("L9", "ghost")

    def test_convert_unknown_actor(self):
        with self.assertRaises(PermissionError):
            self.crm.convert("L9", 1000, "ghost")

    def test_advance_unknown_actor(self):
        with self.assertRaises(PermissionError):
            self.crm.advance("O9", "bogus", "ghost")

    def test_discount_unknown_actor(self):
        with self.assertRaises(PermissionError):
            self.crm.discount("O9", 99, "ghost")

    def test_transfer_unknown_actor(self):
        with self.assertRaises(PermissionError):
            self.crm.transfer("O9", "ghost2", "ghost")

    def test_actor_check_precedes_argument_validation(self):
        """Unknown actor wins over an email that is also invalid (check order)."""
        with self.assertRaises(PermissionError):
            self.crm.add_lead("not-an-email", "", "bogus-source", "ghost")

    def test_actor_check_precedes_missing_entity(self):
        with self.assertRaises(PermissionError):
            self.crm.qualify("L404", "ghost")

    def test_manager_role_counts_as_known(self):
        self.crm.advance(self.opp, "proposal", "m1")
        self.assertEqual(self.crm.opps[self.opp]["stage"], "proposal")

    def test_non_string_actor_is_unknown(self):
        for actor in (None, 1, ["r1"], b"r1"):
            with self.subTest(actor=actor):
                with self.assertRaises(PermissionError):
                    self.crm.qualify(self.lead, actor)


class TestAddLeadEmailRule(unittest.TestCase):
    """Line 13: str, exactly one '@', non-empty local, domain dot not first/last."""

    def setUp(self):
        self.crm = base_crm()

    def test_email_must_be_str(self):
        for email in (None, 123, ["a@corp.com"], b"a@corp.com"):
            with self.subTest(email=email):
                with self.assertRaises(ValueError):
                    self.crm.add_lead(email, "Ann", "web", "m1")

    def test_requires_exactly_one_at(self):
        for email in ("nope", "a@b@c.com", "@@a.com"):
            with self.subTest(email=email):
                with self.assertRaises(ValueError):
                    self.crm.add_lead(email, "Ann", "web", "m1")

    def test_local_part_must_be_non_empty(self):
        with self.assertRaises(ValueError):
            self.crm.add_lead("@corp.com", "Ann", "web", "m1")
        with self.assertRaises(ValueError):
            self.crm.add_lead("   @corp.com", "Ann", "web", "m1")

    def test_domain_needs_a_dot_that_is_neither_first_nor_last(self):
        """Line 13: some '.' at a position that is not the domain's first/last char."""
        valid = ["a@corp.com", "a@x.y", "a@sub.corp.com", "a@corp.co.uk",
                 "a@co.m.", "a@corp.."]
        invalid = ["a@corpcom", "a@.com", "a@corp.", "a@.", "a@.c.", "a@.corp."]
        for email in valid:
            with self.subTest(valid=email):
                self.crm.add_lead(email, "Ann", "web", "m1")
        for email in invalid:
            with self.subTest(invalid=email):
                with self.assertRaises(ValueError):
                    self.crm.add_lead(email, "Ann", "web", "m1")
        self.assertEqual(len(self.crm.leads), len(valid))

    def test_interior_dot_wins_over_edge_dots(self):
        """'corp..' is accepted (interior dot); '.corp.' is not (only edge dots)."""
        self.crm.add_lead("a@corp..", "Ann", "web", "m1")
        self.assertEqual(len(self.crm.leads), 1)
        with self.assertRaises(ValueError):
            self.crm.add_lead("b@.corp.", "Bob", "web", "m1")
        self.assertEqual(len(self.crm.leads), 1)

    def test_stored_email_is_normalized_and_lookup_is_normalized(self):
        lead = self.crm.add_lead("  Ann@Corp.COM ", "Ann", "web", "m1")
        self.assertEqual(self.crm.leads[lead]["email"], "ann@corp.com")
        with self.assertRaises(DuplicateLeadError) as ctx:
            self.crm.add_lead("ANN@corp.com  ", "Other", "web", "m1")
        self.assertEqual(ctx.exception.existing_id, lead)


class TestAddLeadNameSource(unittest.TestCase):
    """Lines 14-15."""

    def setUp(self):
        self.crm = base_crm()

    def test_name_must_be_str(self):
        for name in (None, 1, ["Ann"], b"Ann"):
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    self.crm.add_lead("a@corp.com", name, "web", "m1")

    def test_name_must_be_non_empty_after_strip(self):
        for name in ("", "   ", "\t\n "):
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    self.crm.add_lead("a@corp.com", name, "web", "m1")

    def test_name_is_stored_stripped_but_inner_space_kept(self):
        lead = self.crm.add_lead("a@corp.com", "  Ann Lee ", "web", "m1")
        self.assertEqual(self.crm.leads[lead]["name"], "Ann Lee")

    def test_source_allowed_values(self):
        for pos, source in enumerate(("web", "referral", "event"), start=1):
            lead = self.crm.add_lead("%s@corp.com" % source, "Ann", source, "m1")
            self.assertEqual(self.crm.leads[lead]["source"], source)

    def test_source_rejects_other_values(self):
        for source in ("WEB", "web ", "", None, 0, ["web"], "newsletter"):
            with self.subTest(source=source):
                with self.assertRaises(ValueError):
                    self.crm.add_lead("a@corp.com", "Ann", source, "m1")

    def test_email_is_validated_before_name_and_source(self):
        """Line 10: the first failing check decides the exception."""
        with self.assertRaises(ValueError):
            self.crm.add_lead("bad-email", "", "bogus", "m1")
        with self.assertRaises(ValueError):
            self.crm.add_lead("a@corp.com", "", "bogus", "m1")
        with self.assertRaises(ValueError):
            self.crm.add_lead("a@corp.com", "   ", "web", "m1")


class TestAddLeadDuplicate(unittest.TestCase):
    """Line 16: DuplicateLeadError carries existing_id."""

    def setUp(self):
        self.crm = base_crm()

    def test_duplicate_raises_with_existing_id_of_the_first_lead(self):
        first = self.crm.add_lead("a@corp.com", "Ann", "web", "m1")
        second = self.crm.add_lead("b@corp.com", "Bob", "web", "m1")
        for email, expected in (("A@CORP.com", first), (" b@corp.com", second)):
            with self.subTest(email=email):
                with self.assertRaises(DuplicateLeadError) as ctx:
                    self.crm.add_lead(email, "Anyone", "referral", "m1")
                self.assertIsInstance(ctx.exception, DuplicateLeadError)
                self.assertEqual(ctx.exception.existing_id, expected)

    def test_duplicate_error_is_a_catchable_exception(self):
        self.crm.add_lead("a@corp.com", "Ann", "web", "m1")
        with self.assertRaises(Exception):
            self.crm.add_lead("a@corp.com", "Ann", "web", "m1")

    def test_duplicate_check_runs_after_argument_validation(self):
        """Line 10 order: a bad source on a duplicate email raises ValueError."""
        self.crm.add_lead("a@corp.com", "Ann", "web", "m1")
        with self.assertRaises(ValueError):
            self.crm.add_lead("a@corp.com", "Ann", "newsletter", "m1")
        with self.assertRaises(ValueError):
            self.crm.add_lead("a@corp.com", "  ", "web", "m1")


class TestAddLeadScore(unittest.TestCase):
    """Line 17: source base score plus 15 for a non-free domain."""

    def setUp(self):
        self.crm = base_crm()

    def _score(self, email, source):
        lead = self.crm.add_lead(email, "Ann", source, "m1")
        return self.crm.leads[lead]["score"]

    def test_base_scores(self):
        self.assertEqual(self._score("w@corp.com", "web"), 10 + 15)
        self.assertEqual(self._score("r@corp.com", "referral"), 30 + 15)
        self.assertEqual(self._score("e@corp.com", "event"), 20 + 15)

    def test_free_domains_get_no_bonus(self):
        for domain in ("gmail.com", "yahoo.com", "outlook.com"):
            for source, base in (("web", 10), ("referral", 30), ("event", 20)):
                with self.subTest(domain=domain, source=source):
                    email = "%s.%s@%s" % (source, domain, domain)
                    self.assertEqual(self._score(email, source), base)

    def test_free_domain_match_is_on_the_whole_domain_case_insensitively(self):
        self.assertEqual(self._score("Ann@GMAIL.COM", "web"), 10)
        self.assertEqual(self._score("a@mail.gmail.com", "web"), 10 + 15)
        self.assertEqual(self._score("a@gmail.com.br", "web"), 10 + 15)
        self.assertEqual(self._score("a@gmail.co", "web"), 10 + 15)


class TestAddLeadAssignment(unittest.TestCase):
    """Line 18: lowest load below capacity, ties by smallest id, else queue."""

    def test_load_of_both_reps_zero_picks_smallest_id_string_order(self):
        crm = CRM([
            {"id": "r2", "role": "rep", "capacity": 2},
            {"id": "r10", "role": "rep", "capacity": 2},
        ])
        lead = crm.add_lead("a@corp.com", "Ann", "web", "r2")
        self.assertEqual(crm.leads[lead]["owner"], "r10")  # "r10" < "r2" as strings

    def test_prefers_the_lower_load_rep(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 2},
            {"id": "r2", "role": "rep", "capacity": 2},
        ])
        first = crm.add_lead("a@corp.com", "Ann", "web", "r1")   # r1 -> load 1
        self.assertEqual(crm.leads[first]["owner"], "r1")
        second = crm.add_lead("b@corp.com", "Bob", "web", "r1")  # r2 load 0 wins
        self.assertEqual(crm.leads[second]["owner"], "r2")

    def test_rep_at_capacity_is_skipped(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 3},
        ])
        a = crm.add_lead("a@corp.com", "Ann", "web", "r2")
        b = crm.add_lead("b@corp.com", "Bob", "web", "r2")
        self.assertEqual((crm.leads[a]["owner"], crm.leads[b]["owner"]), ("r1", "r2"))
        c = crm.add_lead("c@corp.com", "Cal", "web", "r2")
        self.assertEqual(crm.leads[c]["owner"], "r2")  # r1 is full, r2 has room

    def test_zero_capacity_rep_never_receives_work(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 0},
            {"id": "m1", "role": "manager", "capacity": 9},
        ])
        lead = crm.add_lead("a@corp.com", "Ann", "web", "m1")
        self.assertIsNone(crm.leads[lead]["owner"])

    def test_only_managers_means_nobody_qualifies_and_lead_is_queued(self):
        """Line 9 "managers never own anything" + line 18 queue path."""
        crm = CRM([{"id": "m1", "role": "manager", "capacity": 5}])
        lead = crm.add_lead("a@corp.com", "Ann", "web", "m1")
        self.assertIsNone(crm.leads[lead]["owner"])
        # Queued, not lost: the spec offers no public accessor, so the queue is
        # observed through its effect -- the lead is still claimable later.
        self.assertEqual(crm.log, [("add_lead", lead, "m1")])
        self.assertEqual(crm.leads[lead]["status"], "new")

    def test_waiting_lead_has_owner_none_and_keeps_status_new(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1}])
        first = crm.add_lead("a@corp.com", "Ann", "web", "r1")
        second = crm.add_lead("b@corp.com", "Bob", "referral", "r1")
        self.assertEqual(crm.leads[first]["owner"], "r1")
        self.assertIsNone(crm.leads[second]["owner"])
        self.assertEqual(crm.leads[second]["status"], "new")
        self.assertEqual(crm.log, [("add_lead", first, "r1"), ("add_lead", second, "r1")])


class TestAddLeadIdAndLog(unittest.TestCase):
    """Lines 17, 19: "L<n>" counts successful creations from 1, one log entry."""

    def test_ids_start_at_one_and_count_successes_only(self):
        crm = base_crm()
        ids = [crm.add_lead("%s@corp.com" % n, "N", "web", "m1") for n in range(1, 4)]
        self.assertEqual(ids, ["L1", "L2", "L3"])

    def test_failed_creations_do_not_consume_an_id(self):
        crm = base_crm()
        first = crm.add_lead("a@corp.com", "Ann", "web", "m1")
        for bad in (lambda: crm.add_lead("bad", "Ann", "web", "m1"),
                    lambda: crm.add_lead("a@corp.com", "", "web", "m1"),
                    lambda: crm.add_lead("a@corp.com", "Ann", "nope", "m1"),
                    lambda: crm.add_lead("a@corp.com", "Ann", "web", "ghost"),
                    lambda: crm.add_lead("a@corp.com", "Ann", "web", "m1")):
            with self.assertRaises(Exception):
                bad()
        second = crm.add_lead("b@corp.com", "Bob", "web", "m1")
        self.assertEqual((first, second), ("L1", "L2"))

    def test_lead_dict_fields(self):
        crm = base_crm()
        lead = crm.add_lead("Ann@Corp.com", "  Ann  ", "event", "m1")
        self.assertEqual(crm.leads[lead], {
            "id": "L1",
            "email": "ann@corp.com",
            "name": "Ann",
            "source": "event",
            "score": 35,
            "owner": "r1",
            "status": "new",
        })

    def test_returns_the_id_and_appends_exactly_one_log_entry(self):
        crm = base_crm()
        returned = crm.add_lead("a@corp.com", "Ann", "web", "m1")
        self.assertEqual(returned, "L1")
        self.assertEqual(crm.log, [("add_lead", "L1", "m1")])
        self.assertEqual(sorted(crm.leads), ["L1"])


if __name__ == "__main__":
    unittest.main()
