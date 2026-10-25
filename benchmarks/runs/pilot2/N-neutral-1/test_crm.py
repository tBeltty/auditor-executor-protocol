"""Lead intake, validation, assignment, permissions and scoring."""

import copy
import unittest

from crm import CRM, DuplicateLeadError

DEFAULT_REPS = [
    {"id": "r1", "role": "rep", "capacity": 3},
    {"id": "r2", "role": "rep", "capacity": 3},
    {"id": "r3", "role": "rep", "capacity": 3},
    {"id": "m1", "role": "manager", "capacity": 0},
]


def make(reps=None):
    source = DEFAULT_REPS if reps is None else reps
    return CRM([dict(rep) for rep in source])


def state(crm):
    return copy.deepcopy((crm.leads, crm.opps, crm.log))


class EmailValidationTest(unittest.TestCase):
    def test_email_not_str(self):
        crm = make()
        for bad in (None, 123, 1.5, ["a@b.com"]):
            with self.assertRaises(ValueError):
                crm.add_lead(bad, "Ada", "web", "r1")
        self.assertEqual(crm.leads, {})
        self.assertEqual(crm.log, [])

    def test_email_requires_exactly_one_at(self):
        crm = make()
        for bad in ("a@@b.com", "a@b@c.com", "ab.com", "plainaddress"):
            with self.assertRaises(ValueError):
                crm.add_lead(bad, "Ada", "web", "r1")
        self.assertEqual(crm.leads, {})

    def test_email_requires_local_part(self):
        crm = make()
        for bad in ("@b.com", "   @b.com"):
            with self.assertRaises(ValueError):
                crm.add_lead(bad, "Ada", "web", "r1")
        self.assertEqual(crm.leads, {})

    def test_email_requires_inner_dot_in_domain(self):
        crm = make()
        for bad in ("a@localhost", "a@.com", "a@b.", "a@b"):
            with self.assertRaises(ValueError):
                crm.add_lead(bad, "Ada", "web", "r1")
        self.assertEqual(crm.leads, {})

    def test_email_is_normalized(self):
        crm = make()
        lead_id = crm.add_lead("  Alice@Example.COM  ", "  Ada  ", "web", "r1")
        lead = crm.leads[lead_id]
        self.assertEqual(lead["email"], "alice@example.com")
        self.assertEqual(lead["name"], "Ada")
        self.assertEqual(lead["id"], "L1")
        self.assertEqual(lead["status"], "new")
        self.assertEqual(crm.log, [("add_lead", "L1", "r1")])

    def test_email_single_char_tld_is_valid(self):
        crm = make()
        lead_id = crm.add_lead("a@b.c", "Ada", "event", "r1")
        self.assertEqual(crm.leads[lead_id]["email"], "a@b.c")

    def test_email_dot_inside_domain_is_valid(self):
        crm = make()
        lead_id = crm.add_lead("a@mail.example.co.uk", "Ada", "event", "r1")
        self.assertEqual(crm.leads[lead_id]["email"], "a@mail.example.co.uk")


class NameValidationTest(unittest.TestCase):
    def test_name_must_be_str_and_non_empty(self):
        crm = make()
        for bad in (None, 7, "", "   ", "\t\n"):
            with self.assertRaises(ValueError):
                crm.add_lead("a@example.com", bad, "web", "r1")
        self.assertEqual(crm.leads, {})
        self.assertEqual(crm.log, [])

    def test_name_is_stripped(self):
        crm = make()
        lead_id = crm.add_lead("a@example.com", "  Ada Lovelace ", "web", "r1")
        self.assertEqual(crm.leads[lead_id]["name"], "Ada Lovelace")


class SourceValidationTest(unittest.TestCase):
    def test_source_must_be_known(self):
        crm = make()
        for bad in ("LinkedIn", "WEB", "", None, 3):
            with self.assertRaises(ValueError):
                crm.add_lead("a@example.com", "Ada", bad, "r1")
        self.assertEqual(crm.leads, {})
        self.assertEqual(crm.log, [])

    def test_all_known_sources_accepted(self):
        crm = make()
        for index, source in enumerate(("web", "referral", "event")):
            lead_id = crm.add_lead("user%d@example.com" % index, "Ada", source, "r1")
            self.assertEqual(crm.leads[lead_id]["source"], source)


class DuplicateLeadTest(unittest.TestCase):
    def test_duplicate_raises_with_existing_id(self):
        crm = make()
        first = crm.add_lead("a@example.com", "Ada", "referral", "r1")
        with self.assertRaises(DuplicateLeadError) as caught:
            crm.add_lead("a@example.com", "Grace", "web", "r1")
        self.assertEqual(caught.exception.existing_id, first)

    def test_duplicate_uses_normalized_email(self):
        crm = make()
        first = crm.add_lead("Ada@Example.com", "Ada", "referral", "r1")
        for variant in ("  ada@example.COM ", "ADA@EXAMPLE.COM", "ada@example.com\n"):
            with self.assertRaises(DuplicateLeadError) as caught:
                crm.add_lead(variant, "Grace", "web", "m1")
            self.assertEqual(caught.exception.existing_id, first)
        self.assertEqual(sorted(crm.leads), ["L1"])

    def test_duplicate_failure_changes_nothing(self):
        crm = make()
        crm.add_lead("a@example.com", "Ada", "referral", "r1")
        before = state(crm)
        with self.assertRaises(DuplicateLeadError):
            crm.add_lead("a@example.com", "Grace", "web", "r1")
        self.assertEqual(state(crm), before)

    def test_lead_ids_count_successful_creations_only(self):
        crm = make()
        self.assertEqual(crm.add_lead("a@example.com", "Ada", "web", "r1"), "L1")
        with self.assertRaises(DuplicateLeadError):
            crm.add_lead("a@example.com", "Ada", "web", "r1")
        with self.assertRaises(ValueError):
            crm.add_lead("nope", "Ada", "web", "r1")
        self.assertEqual(crm.add_lead("b@example.com", "Grace", "web", "r1"), "L2")


class ScoreTest(unittest.TestCase):
    def test_score_values(self):
        cases = [
            ("web", "gmail.com", 10),
            ("web", "corp.com", 25),
            ("referral", "gmail.com", 30),
            ("referral", "corp.com", 45),
            ("event", "outlook.com", 20),
            ("event", "corp.com", 35),
        ]
        crm = make()
        for index, (source, domain, expected) in enumerate(cases):
            lead_id = crm.add_lead("u%d@%s" % (index, domain), "Ada", source, "r1")
            self.assertEqual(crm.leads[lead_id]["score"], expected, (source, domain))

    def test_score_below_threshold_cannot_qualify(self):
        for source, domain in (("web", "gmail.com"), ("web", "corp.com"), ("event", "gmail.com")):
            crm = make()
            lead_id = crm.add_lead("a@%s" % domain, "Ada", source, "r1")
            before = state(crm)
            with self.assertRaises(ValueError):
                crm.qualify(lead_id, "r1")
            self.assertEqual(crm.leads[lead_id]["status"], "new")
            self.assertEqual(state(crm), before)

    def test_score_at_or_above_threshold_qualifies(self):
        for source, domain in (("referral", "gmail.com"), ("event", "corp.com"), ("referral", "corp.com")):
            crm = make()
            lead_id = crm.add_lead("a@%s" % domain, "Ada", source, "r1")
            crm.qualify(lead_id, "r1")
            self.assertEqual(crm.leads[lead_id]["status"], "qualified")


class AssignmentTest(unittest.TestCase):
    def test_tie_break_prefers_smallest_id(self):
        crm = make()
        lead_id = crm.add_lead("a@example.com", "Ada", "web", "r1")
        self.assertEqual(crm.leads[lead_id]["owner"], "r1")

    def test_load_balancing_picks_lowest_load(self):
        crm = make()
        owners = [crm.leads[crm.add_lead("u%d@example.com" % i, "Ada", "web", "r1")]["owner"] for i in range(4)]
        self.assertEqual(owners, ["r1", "r2", "r3", "r1"])

    def test_capacity_full_sends_lead_to_waiting_queue(self):
        crm = make([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        first = crm.add_lead("a@example.com", "Ada", "web", "r1")
        second = crm.add_lead("b@example.com", "Grace", "web", "r1")
        self.assertEqual(crm.leads[first]["owner"], "r1")
        self.assertIsNone(crm.leads[second]["owner"])
        self.assertEqual(crm.log, [("add_lead", "L1", "r1"), ("add_lead", "L2", "r1")])

    def test_managers_never_own_leads(self):
        crm = make([
            {"id": "m0", "role": "manager", "capacity": 5},
            {"id": "m1", "role": "manager", "capacity": 5},
        ])
        lead_id = crm.add_lead("a@example.com", "Ada", "web", "m0")
        self.assertIsNone(crm.leads[lead_id]["owner"])

    def test_waiting_queue_is_fifo_on_freed_slot(self):
        crm = make([
            {"id": "r1", "role": "rep", "capacity": 2},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        first = crm.add_lead("a@example.com", "Ada", "referral", "r1")
        second = crm.add_lead("b@example.com", "Grace", "referral", "r1")
        third = crm.add_lead("c@example.com", "Alan", "referral", "r1")
        fourth = crm.add_lead("d@example.com", "Edsger", "referral", "r1")
        self.assertEqual([crm.leads[k]["owner"] for k in (first, second, third, fourth)],
                         ["r1", "r1", None, None])
        crm.qualify(first, "r1")
        opp = crm.convert(first, 1000, "r1")
        self.assertEqual(crm.leads[third]["owner"], None)
        crm.advance(opp, "proposal", "r1")
        crm.advance(opp, "negotiation", "r1")
        crm.advance(opp, "won", "r1")
        self.assertEqual(crm.leads[third]["owner"], "r1")
        self.assertEqual(crm.leads[third]["status"], "new")
        self.assertIsNone(crm.leads[fourth]["owner"])
        self.assertIn(("assign", third, "system"), crm.log)

    def test_drain_stops_at_capacity(self):
        crm = make([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        first = crm.add_lead("a@example.com", "Ada", "referral", "r1")
        second = crm.add_lead("b@example.com", "Grace", "referral", "r1")
        third = crm.add_lead("c@example.com", "Alan", "referral", "r1")
        crm.qualify(first, "r1")
        opp = crm.convert(first, 1000, "r1")
        crm.advance(opp, "proposal", "r1")
        crm.advance(opp, "negotiation", "r1")
        crm.advance(opp, "won", "r1")
        self.assertEqual(crm.leads[second]["owner"], "r1")
        self.assertIsNone(crm.leads[third]["owner"])

    def test_load_counts_new_and_qualified_leads(self):
        crm = make([
            {"id": "r1", "role": "rep", "capacity": 2},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        first = crm.add_lead("a@example.com", "Ada", "referral", "r1")
        crm.qualify(first, "r1")
        crm.add_lead("b@example.com", "Grace", "referral", "r1")
        blocked = crm.add_lead("c@example.com", "Alan", "referral", "r1")
        self.assertIsNone(crm.leads[blocked]["owner"])
        crm.convert(first, 1000, "r1")
        self.assertIsNone(crm.leads[blocked]["owner"])


class PermissionTest(unittest.TestCase):
    def fixture(self):
        crm = make()
        lead = crm.add_lead("a@example.com", "Ada", "referral", "r1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 1000, "r1")
        return crm, lead, opp

    def test_unknown_actor_rejected_everywhere(self):
        crm, lead, opp = self.fixture()
        before = state(crm)
        calls = [
            lambda: crm.add_lead("z@example.com", "Zoe", "web", "ghost"),
            lambda: crm.qualify(lead, "ghost"),
            lambda: crm.convert(lead, 1000, "ghost"),
            lambda: crm.advance(opp, "proposal", "ghost"),
            lambda: crm.discount(opp, 5, "ghost"),
            lambda: crm.transfer(opp, "r2", "ghost"),
        ]
        for call in calls:
            with self.assertRaises(PermissionError):
                call()
        self.assertEqual(state(crm), before)

    def test_unknown_actor_checked_before_other_validation(self):
        crm = make()
        for call in (
            lambda: crm.add_lead("bad-email", "", "bogus", "ghost"),
            lambda: crm.qualify("L404", "ghost"),
            lambda: crm.convert("L404", -5, "ghost"),
            lambda: crm.advance("O404", "bogus", "ghost"),
            lambda: crm.discount("O404", 99, "ghost"),
            lambda: crm.transfer("O404", "nobody", "ghost"),
        ):
            with self.assertRaises(PermissionError):
                call()

    def test_non_owner_rep_cannot_act(self):
        crm, lead, opp = self.fixture()
        self.assertEqual(crm.leads[lead]["owner"], "r1")
        self.assertEqual(crm.opps[opp]["owner"], "r1")
        before = state(crm)
        for call in (
            lambda: crm.qualify("L1", "r2"),
            lambda: crm.convert("L1", 1000, "r2"),
            lambda: crm.advance(opp, "proposal", "r2"),
            lambda: crm.discount(opp, 5, "r2"),
        ):
            with self.assertRaises(PermissionError):
                call()
        self.assertEqual(state(crm), before)

    def test_owner_can_act(self):
        crm, lead, opp = self.fixture()
        crm.advance(opp, "proposal", "r1")
        crm.discount(opp, 5, "r1")
        self.assertEqual(crm.opps[opp]["stage"], "proposal")
        self.assertEqual(crm.opps[opp]["amount"], 950)

    def test_manager_can_act(self):
        crm, lead, opp = self.fixture()
        crm.advance(opp, "proposal", "m1")
        crm.discount(opp, 20, "m1")
        crm.transfer(opp, "r2", "m1")
        self.assertEqual(crm.opps[opp]["owner"], "r2")
        self.assertEqual(crm.opps[opp]["amount"], 800)

    def test_manager_cannot_convert_unowned_lead(self):
        crm = make([
            {"id": "r1", "role": "rep", "capacity": 0},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        lead = crm.add_lead("a@example.com", "Ada", "referral", "r1")
        self.assertIsNone(crm.leads[lead]["owner"])
        crm.qualify(lead, "m1")
        before = state(crm)
        with self.assertRaises(ValueError):
            crm.convert(lead, 1000, "m1")
        self.assertEqual(state(crm), before)


if __name__ == "__main__":
    unittest.main()
