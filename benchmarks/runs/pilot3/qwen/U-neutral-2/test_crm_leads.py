"""Tests for CRM.add_lead / CRM.qualify, actor rules, assignment and queue."""

import copy
import unittest

from crm import CRM, DuplicateLeadError


def make_crm():
    return CRM([
        {"id": "ana", "role": "rep", "capacity": 2},
        {"id": "bob", "role": "rep", "capacity": 1},
        {"id": "mia", "role": "manager", "capacity": 5},
    ])


class ActorCheck(unittest.TestCase):
    def test_unknown_actor_raises_permission_error_everywhere(self):
        crm = make_crm()
        self.assertRaises(PermissionError, crm.add_lead, "a@b.com", "A", "web", "ghost")
        self.assertRaises(PermissionError, crm.qualify, "L1", "ghost")
        self.assertRaises(PermissionError, crm.convert, "L1", 100, "ghost")
        self.assertRaises(PermissionError, crm.advance, "O1", "proposal", "ghost")
        self.assertRaises(PermissionError, crm.discount, "O1", 5, "ghost")
        self.assertRaises(PermissionError, crm.transfer, "O1", "ana", "ghost")
        self.assertEqual(crm.log, [])

    def test_actor_checked_before_any_other_validation(self):
        crm = make_crm()
        # Bad args everywhere, but the unknown actor wins.
        self.assertRaises(PermissionError, crm.add_lead, 42, "", "phone", "ghost")
        self.assertRaises(PermissionError, crm.qualify, "does-not-exist", "ghost")
        self.assertRaises(PermissionError, crm.convert, "does-not-exist", -1, "ghost")
        self.assertRaises(PermissionError, crm.advance, "does-not-exist", "bogus", "ghost")
        self.assertRaises(PermissionError, crm.discount, "does-not-exist", 99, "ghost")
        self.assertRaises(PermissionError, crm.transfer, "does-not-exist", "ghost2", "ghost")

    def test_non_string_actor_raises_permission_error(self):
        crm = make_crm()
        for actor in (None, 7, ["ana"], True):
            self.assertRaises(PermissionError, crm.add_lead, "a@b.com", "A", "web", actor)
        self.assertEqual(crm.log, [])


class EmailValidation(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()

    def test_invalid_emails_rejected(self):
        bad = [
            "",
            "noatsign",
            "a@b",            # domain has no dot
            "a@@b.com",       # two @
            "@b.com",         # empty local part
            "a@.com",         # dot is first char of domain
            "a@com.",         # dot is last char of domain
            "a@.",            # single-dot domain, first and last
            "a@co m",         # no dot in domain
        ]
        for email in bad:
            with self.subTest(email=email):
                self.assertRaises(ValueError, self.crm.add_lead, email, "N", "web", "mia")

    def test_email_with_two_at_signs_rejected(self):
        self.assertRaises(ValueError, self.crm.add_lead, "a@b.com@c.com", "N", "web", "mia")

    def test_non_string_email_rejected(self):
        for email in (123, None, True, ["a@b.com"], b"a@b.com"):
            self.assertRaises(ValueError, self.crm.add_lead, email, "N", "web", "mia")

    def test_valid_minimal_emails_accepted(self):
        # Domain "b.c": dot at position 1 of 3, neither first nor last.
        first = self.crm.add_lead("a@b.c", "N", "web", "mia")
        self.assertEqual(first, "L1")
        # "a@b.c." is valid: the dot at index 1 is neither first nor last.
        second = self.crm.add_lead("d@e.f.", "N", "web", "mia")
        self.assertEqual(second, "L2")

    def test_email_normalized_on_storage(self):
        lead_id = self.crm.add_lead("  MixedCase@Example.COM ", "N", "web", "mia")
        self.assertEqual(self.crm.leads[lead_id]["email"], "mixedcase@example.com")


class NameAndSourceValidation(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()

    def test_name_must_be_nonempty_string(self):
        for name in ("", "   ", "\t\n", 5, None, True):
            self.assertRaises(ValueError, self.crm.add_lead, "a@b.com", name, "web", "mia")

    def test_name_is_stripped(self):
        lead_id = self.crm.add_lead("a@b.com", "  Alice  ", "web", "mia")
        self.assertEqual(self.crm.leads[lead_id]["name"], "Alice")

    def test_source_must_be_one_of_three(self):
        for source in ("phone", "Web", "WEB", "web ", "", None, 0):
            self.assertRaises(ValueError, self.crm.add_lead, "a@b.com", "N", source, "mia")

    def test_invalid_source_checked_before_duplicate(self):
        self.crm.add_lead("dup@example.com", "N", "web", "mia")
        self.assertRaises(ValueError, self.crm.add_lead, "dup@example.com", "N", "phone", "mia")

    def test_invalid_name_checked_before_duplicate(self):
        self.crm.add_lead("dup2@example.com", "N", "web", "mia")
        self.assertRaises(ValueError, self.crm.add_lead, "dup2@example.com", " ", "web", "mia")


class DuplicateLead(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()

    def test_duplicate_raises_with_existing_id(self):
        first = self.crm.add_lead("John@Acme.COM", "John", "web", "mia")
        with self.assertRaises(DuplicateLeadError) as ctx:
            self.crm.add_lead(" john@acme.com ", "Johnny", "web", "mia")
        self.assertEqual(ctx.exception.existing_id, first)
        self.assertEqual(ctx.exception.existing_id, "L1")

    def test_duplicate_error_type(self):
        self.assertTrue(issubclass(DuplicateLeadError, Exception))
        self.assertFalse(issubclass(DuplicateLeadError, ValueError))
        err = DuplicateLeadError("L7")
        self.assertEqual(err.existing_id, "L7")

    def test_duplicate_changes_nothing(self):
        self.crm.add_lead("a@x.com", "A", "web", "mia")
        before = copy.deepcopy({"leads": self.crm.leads, "log": self.crm.log})
        self.assertRaises(DuplicateLeadError, self.crm.add_lead, "a@x.com", "B", "web", "mia")
        self.assertEqual(self.crm.leads, before["leads"])
        self.assertEqual(self.crm.log, before["log"])

    def test_id_sequence_ignores_failed_creations(self):
        self.assertRaises(ValueError, self.crm.add_lead, "bad-email", "N", "web", "mia")
        self.assertRaises(ValueError, self.crm.add_lead, "a@b.com", "", "web", "mia")
        first = self.crm.add_lead("x@y.com", "N", "web", "mia")
        self.assertEqual(first, "L1")
        self.assertRaises(DuplicateLeadError, self.crm.add_lead, "x@y.com", "N", "web", "mia")
        nxt = self.crm.add_lead("w@y.com", "N", "web", "mia")
        self.assertEqual(nxt, "L2")


class Scores(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()

    def score_of(self, email, source):
        lead_id = self.crm.add_lead(email, "N", source, "mia")
        return self.crm.leads[lead_id]["score"]

    def test_base_scores_with_free_domains(self):
        self.assertEqual(self.score_of("w@gmail.com", "web"), 10)
        self.assertEqual(self.score_of("e@outlook.com", "event"), 20)
        self.assertEqual(self.score_of("r@yahoo.com", "referral"), 30)

    def test_custom_domain_bonus(self):
        self.assertEqual(self.score_of("w@acme.io", "web"), 25)
        self.assertEqual(self.score_of("e@acme.io", "event"), 35)
        self.assertEqual(self.score_of("r@acme.io", "referral"), 45)

    def test_domain_checked_after_normalization(self):
        self.assertEqual(self.score_of("  x@GMAIL.com ", "web"), 10)
        self.assertEqual(self.score_of("x@Acme.IO", "web"), 25)


class OwnerAssignment(unittest.TestCase):
    def test_lowest_load_and_string_tie_break(self):
        crm = CRM([
            {"id": "r2", "role": "rep", "capacity": 2},
            {"id": "r10", "role": "rep", "capacity": 2},
            {"id": "m", "role": "manager", "capacity": 9},
        ])
        l1 = crm.add_lead("a@b.com", "A", "web", "m")   # tie at load 0 -> "r10" < "r2"
        self.assertEqual(crm.leads[l1]["owner"], "r10")
        l2 = crm.add_lead("c@d.com", "C", "web", "m")   # r10 load 1, r2 load 0
        self.assertEqual(crm.leads[l2]["owner"], "r2")
        l3 = crm.add_lead("e@f.com", "E", "web", "m")   # both load 1 -> tie -> r10
        self.assertEqual(crm.leads[l3]["owner"], "r10")
        l4 = crm.add_lead("g@h.com", "G", "web", "m")   # r10 2 full, r2 1 -> r2
        self.assertEqual(crm.leads[l4]["owner"], "r2")
        l5 = crm.add_lead("i@j.com", "I", "web", "m")   # everyone full -> queue
        self.assertIsNone(crm.leads[l5]["owner"])

    def test_managers_never_receive_work(self):
        crm = CRM([{"id": "aaa", "role": "manager", "capacity": 9},
                   {"id": "zzz", "role": "rep", "capacity": 1}])
        lead_id = crm.add_lead("a@b.com", "A", "web", "aaa")
        self.assertEqual(crm.leads[lead_id]["owner"], "zzz")

    def test_capacity_zero_rep_never_selected(self):
        crm = CRM([{"id": "a0", "role": "rep", "capacity": 0},
                   {"id": "b1", "role": "rep", "capacity": 1}])
        l1 = crm.add_lead("x@y.z", "X", "web", "b1")
        self.assertEqual(crm.leads[l1]["owner"], "b1")

    def test_waiting_lead_is_queued_and_has_none_owner(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1}])
        l1 = crm.add_lead("a@b.co", "A", "web", "r1")
        l2 = crm.add_lead("c@d.co", "C", "web", "r1")
        self.assertEqual(crm.leads[l1]["owner"], "r1")
        self.assertIsNone(crm.leads[l2]["owner"])
        # Failed ownership does not add an extra log entry beyond add_lead.
        self.assertEqual(crm.log, [("add_lead", "L1", "r1"), ("add_lead", "L2", "r1")])

    def test_load_includes_qualified_leads_and_open_opps(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 1},
            {"id": "m", "role": "manager", "capacity": 1},
        ])
        l1 = crm.add_lead("a@a.io", "A", "referral", "m")  # r1, score 30
        self.assertEqual(crm.leads[l1]["owner"], "r1")
        crm.qualify(l1, "r1")                               # still counts (qualified)
        l2 = crm.add_lead("b@b.io", "B", "referral", "m")  # -> r2
        self.assertEqual(crm.leads[l2]["owner"], "r2")
        o1 = crm.convert(l1, 500, "r1")                     # converted lead out, opp in
        l3 = crm.add_lead("c@c.io", "C", "referral", "m")   # all full -> queue
        self.assertIsNone(crm.leads[l3]["owner"])
        crm.advance(o1, "proposal", "r1")                   # still open, still counts
        l4 = crm.add_lead("d@d.io", "D", "referral", "m")
        self.assertIsNone(crm.leads[l4]["owner"])
        crm.advance(o1, "negotiation", "m")                 # still open
        crm.advance(o1, "won", "r1")                        # frees r1's slot
        self.assertEqual(crm.leads[l3]["owner"], "r1")      # oldest waiting first
        self.assertEqual(crm.leads[l4]["owner"], None)      # one slot only
        self.assertIn(("assign", "L3", "system"), crm.log)

    def test_queue_is_fifo_across_events(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 1},
            {"id": "m", "role": "manager", "capacity": 1},
        ])
        l1 = crm.add_lead("e1@x.io", "E1", "referral", "m")  # r1
        l2 = crm.add_lead("e2@x.io", "E2", "referral", "m")  # r2
        l3 = crm.add_lead("e3@x.io", "E3", "referral", "m")  # queue
        l4 = crm.add_lead("e4@x.io", "E4", "referral", "m")  # queue
        crm.qualify(l1, "m")
        crm.qualify(l2, "m")
        o1 = crm.convert(l1, 100, "m")   # r1 still loaded
        o2 = crm.convert(l2, 100, "m")   # r2 still loaded
        crm.advance(o1, "lost", "r1")    # frees r1 -> assigns l3
        self.assertEqual(crm.leads[l3]["owner"], "r1")
        self.assertEqual(crm.leads[l4]["owner"], None)
        crm.advance(o2, "lost", "r2")    # frees r2 -> assigns l4
        self.assertEqual(crm.leads[l4]["owner"], "r2")
        self.assertEqual([entry for entry in crm.log if entry[0] == "assign"],
                         [("assign", "L3", "system"), ("assign", "L4", "system")])


class Qualify(unittest.TestCase):
    def setUp(self):
        self.crm = CRM([
            {"id": "ana", "role": "rep", "capacity": 1},
            {"id": "bob", "role": "rep", "capacity": 1},
            {"id": "mia", "role": "manager", "capacity": 9},
        ])

    def test_owner_can_qualify(self):
        lead_id = self.crm.add_lead("a@acme.io", "A", "referral", "mia")  # score 45 -> ana
        self.assertEqual(self.crm.leads[lead_id]["owner"], "ana")
        self.assertIsNone(self.crm.qualify(lead_id, "ana"))
        self.assertEqual(self.crm.leads[lead_id]["status"], "qualified")
        self.assertEqual(self.crm.log[-1], ("qualify", lead_id, "ana"))

    def test_manager_can_qualify_any_lead(self):
        lead_id = self.crm.add_lead("a@acme.io", "A", "referral", "mia")
        self.crm.qualify(lead_id, "mia")
        self.assertEqual(self.crm.leads[lead_id]["status"], "qualified")
        self.assertEqual(self.crm.log[-1], ("qualify", lead_id, "mia"))

    def test_other_rep_is_permission_error(self):
        lead_id = self.crm.add_lead("a@acme.io", "A", "referral", "mia")
        self.assertRaises(PermissionError, self.crm.qualify, lead_id, "bob")
        self.assertEqual(self.crm.leads[lead_id]["status"], "new")

    def test_unknown_lead_value_error(self):
        self.assertRaises(ValueError, self.crm.qualify, "L99", "mia")

    def test_status_must_be_new(self):
        lead_id = self.crm.add_lead("a@acme.io", "A", "referral", "mia")
        self.crm.qualify(lead_id, "mia")
        self.assertRaises(ValueError, self.crm.qualify, lead_id, "mia")

    def test_score_threshold(self):
        low = self.crm.add_lead("w@gmail.com", "W", "web", "mia")        # 10
        mid = self.crm.add_lead("e@gmail.com", "E", "event", "mia")      # 20
        webcustom = self.crm.add_lead("v@acme.io", "V", "web", "mia")    # 25
        referral = self.crm.add_lead("r@gmail.com", "R", "referral", "mia")  # 30
        eventcustom = self.crm.add_lead("t@acme.io", "T", "event", "mia")    # 35
        for lead_id in (low, mid, webcustom):
            self.assertRaises(ValueError, self.crm.qualify, lead_id, "mia")
        for lead_id in (referral, eventcustom):
            self.crm.qualify(lead_id, "mia")
            self.assertEqual(self.crm.leads[lead_id]["status"], "qualified")

    def test_auth_check_runs_before_status_and_score(self):
        low = self.crm.add_lead("w@gmail.com", "W", "web", "mia")  # score 10, owner ana
        # Not owner, not manager: PermissionError even though score/status also fail.
        self.assertRaises(PermissionError, self.crm.qualify, low, "bob")
        # Manager (auth passes) with a bad status gets ValueError.
        referral = self.crm.add_lead("q@acme.io", "Q", "referral", "mia")
        self.crm.leads[referral]["status"] = "converted"
        self.assertRaises(ValueError, self.crm.qualify, referral, "mia")

    def test_manager_can_qualify_waiting_lead(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1},
                   {"id": "m", "role": "manager", "capacity": 1}])
        crm.add_lead("a@a.io", "A", "referral", "m")   # -> r1 (full)
        waiting = crm.add_lead("b@b.io", "B", "referral", "m")  # owner None
        self.assertRaises(PermissionError, crm.qualify, waiting, "r1")
        crm.qualify(waiting, "m")
        self.assertEqual(crm.leads[waiting]["status"], "qualified")

    def test_failed_qualify_changes_nothing(self):
        lead_id = self.crm.add_lead("w@gmail.com", "W", "web", "mia")
        snapshot = copy.deepcopy({"leads": self.crm.leads, "log": self.crm.log})
        self.assertRaises(ValueError, self.crm.qualify, lead_id, "ana")
        self.assertEqual(self.crm.leads, snapshot["leads"])
        self.assertEqual(self.crm.log, snapshot["log"])


if __name__ == "__main__":
    unittest.main()
