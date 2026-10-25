import copy
import unittest

from crm import CRM, DuplicateLeadError


def default_crm():
    return CRM([
        {"id": "r1", "role": "rep", "capacity": 1},
        {"id": "r2", "role": "rep", "capacity": 2},
        {"id": "m1", "role": "manager", "capacity": 99},
    ])


def fill_with_queue(crm):
    """r1 gets L1, r2 gets L2+L3 (at capacity), L4 lands in the waiting queue."""
    crm.add_lead("a@ex.com", "Ann", "referral", "m1")   # L1 -> r1
    crm.add_lead("b@ex.com", "Bob", "referral", "m1")   # L2 -> r2
    crm.add_lead("c@ex.com", "Cy", "referral", "m1")    # L3 -> r2
    crm.add_lead("d@ex.com", "Dee", "referral", "m1")   # L4 -> queue
    return crm


class ActorCheckTests(unittest.TestCase):
    def test_unknown_actor_raises_permission_error_first(self):
        crm = default_crm()
        # the actor check precedes every other validation, even bad arguments
        with self.assertRaises(PermissionError):
            crm.add_lead("not-an-email", "", "phone", "ghost")
        with self.assertRaises(PermissionError):
            crm.qualify("nope", "ghost")
        with self.assertRaises(PermissionError):
            crm.convert("nope", -5, "ghost")
        with self.assertRaises(PermissionError):
            crm.advance("nope", "bogus", "ghost")
        with self.assertRaises(PermissionError):
            crm.discount("nope", 99, "ghost")
        with self.assertRaises(PermissionError):
            crm.transfer("nope", "ghost2", "ghost")
        self.assertEqual(crm.log, [])
        self.assertEqual(crm.leads, {})
        self.assertEqual(crm.opps, {})

    def test_non_string_actor(self):
        crm = default_crm()
        for bad in (None, 5, ["r1"], ("r1",), True):
            with self.assertRaises(PermissionError):
                crm.add_lead("a@b.co", "N", "web", bad)


class AddLeadValidationTests(unittest.TestCase):
    def setUp(self):
        self.crm = default_crm()

    def test_email_must_be_str(self):
        for bad in (None, 123, b"a@b.co", ["a@b.co"]):
            with self.assertRaises(ValueError):
                self.crm.add_lead(bad, "N", "web", "m1")

    def test_email_shape(self):
        bad_emails = [
            "noatsign.com",
            "a@b@c.com",       # two @
            "@b.com",          # empty local part
            "a@",              # empty domain
            "a@b",             # no dot in domain
            "a@.com",          # dot only at first position of domain
            "a@com.",          # dot only at last position of domain
            "a@.c.",           # dots only at both ends of domain
        ]
        for bad in bad_emails:
            with self.assertRaises(ValueError, msg=bad):
                self.crm.add_lead(bad, "N", "web", "m1")

    def test_email_acceptance(self):
        lead_id = self.crm.add_lead("  User@Example.COM  ", "N", "web", "m1")
        self.assertEqual(self.crm.leads[lead_id]["email"], "user@example.com")
        self.crm.add_lead("a@b.c", "N", "web", "m1")            # minimal domain
        self.crm.add_lead("x@sub.example.com", "N", "web", "m1")  # multiple dots
        # spaces are not forbidden by the spec
        lead_id = self.crm.add_lead("a b@c.com", "N", "web", "m1")
        self.assertEqual(self.crm.leads[lead_id]["email"], "a b@c.com")

    def test_name_rules(self):
        for bad_name in (None, 7, "", "   ", "\t\n"):
            with self.assertRaises(ValueError):
                self.crm.add_lead("a@b.co", bad_name, "web", "m1")
        lead_id = self.crm.add_lead("a@b.co", "  Ann  ", "web", "m1")
        self.assertEqual(self.crm.leads[lead_id]["name"], "Ann")

    def test_source_rules(self):
        for bad_source in ("phone", "WEB", "", None, ["web"]):
            with self.assertRaises(ValueError):
                self.crm.add_lead("a@b.co", "N", bad_source, "m1")

    def test_check_order(self):
        # unknown actor beats everything
        with self.assertRaises(PermissionError):
            self.crm.add_lead("bad", "", "bad", "ghost")
        # invalid arguments raise ValueError and add nothing
        with self.assertRaises(ValueError):
            self.crm.add_lead("bademail", "N", "web", "m1")
        with self.assertRaises(ValueError):
            self.crm.add_lead("a@b.co", "", "web", "m1")
        with self.assertRaises(ValueError):
            self.crm.add_lead("a@b.co", "N", "phone", "m1")
        self.assertEqual(self.crm.log, [])
        self.assertEqual(self.crm.leads, {})

    def test_duplicate_lead_error(self):
        first = self.crm.add_lead("A@B.com", "Ann", "web", "m1")
        self.assertEqual(first, "L1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            self.crm.add_lead(" a@b.COM ", "Other", "referral", "m1")
        self.assertEqual(ctx.exception.existing_id, "L1")
        # failed call changes nothing
        self.assertEqual(len(self.crm.leads), 1)
        self.assertEqual(self.crm.log, [("add_lead", "L1", "m1")])
        # next successful lead still gets L2 (ids count successes only)
        second = self.crm.add_lead("c@d.com", "Cy", "web", "m1")
        self.assertEqual(second, "L2")
        # duplicate detection also sees existing-qualified / other-owner leads
        with self.assertRaises(DuplicateLeadError):
            self.crm.add_lead("a@b.com", "Ann", "web", "m1")
        self.assertEqual(self.crm.log[-1], ("add_lead", "L2", "m1"))


class ScoringTests(unittest.TestCase):
    def setUp(self):
        self.crm = default_crm()

    def test_base_scores_and_domain_bonus(self):
        cases = [
            ("w@gmail.com", "web", 10),
            ("w@yahoo.com", "web", 10),
            ("w@outlook.com", "web", 10),
            ("w@ex.com", "web", 25),
            ("r@GMAIL.COM", "referral", 30),
            ("r@ex.com", "referral", 45),
            ("e@OUTLOOK.com", "event", 20),
            ("e@ex.com", "event", 35),
            ("e@sub.gmail.com", "event", 35),  # not exactly gmail.com
        ]
        for i, (email, source, score) in enumerate(cases):
            lead_id = self.crm.add_lead(email, "N", source, "m1")
            self.assertEqual(self.crm.leads[lead_id]["score"], score, email)

    def test_qualify_score_threshold_boundary(self):
        # referral on Yahoo => 30 exactly => qualifies
        lead_id = self.crm.add_lead("  R@Yahoo.com ", "N", "referral", "m1")
        self.crm.qualify(lead_id, "m1")
        self.assertEqual(self.crm.leads[lead_id]["status"], "qualified")
        # web on custom domain => 25 => ValueError
        lead_id = self.crm.add_lead("w@ex.com", "N", "web", "m1")
        with self.assertRaises(ValueError):
            self.crm.qualify(lead_id, "m1")


class RoutingTests(unittest.TestCase):
    def test_lowest_load_then_smallest_id(self):
        crm = CRM([
            {"id": "z9", "role": "rep", "capacity": 1},
            {"id": "a1", "role": "rep", "capacity": 1},
            {"id": "m", "role": "manager", "capacity": 0},
        ])
        l1 = crm.add_lead("1@ex.com", "A", "web", "m")
        self.assertEqual(crm.leads[l1]["owner"], "a1")  # load tie -> smallest id
        l2 = crm.add_lead("2@ex.com", "B", "web", "m")
        self.assertEqual(crm.leads[l2]["owner"], "z9")
        l3 = crm.add_lead("3@ex.com", "C", "web", "m")
        self.assertIsNone(crm.leads[l3]["owner"])  # everyone full -> queue

    def test_lowest_load_beats_id_order(self):
        crm = CRM([
            {"id": "a", "role": "rep", "capacity": 2},
            {"id": "b", "role": "rep", "capacity": 2},
            {"id": "m", "role": "manager", "capacity": 0},
        ])
        crm.add_lead("1@ex.com", "A", "web", "m")  # -> a (tie, "a" < "b")
        l2 = crm.add_lead("2@ex.com", "B", "web", "m")  # a load1, b load0 -> b
        self.assertEqual(crm.leads[l2]["owner"], "b")
        l3 = crm.add_lead("3@ex.com", "C", "web", "m")  # tie load1 -> a
        self.assertEqual(crm.leads[l3]["owner"], "a")

    def test_load_balancing(self):
        crm = default_crm()
        l1 = crm.add_lead("1@ex.com", "A", "referral", "m1")
        self.assertEqual(crm.leads[l1]["owner"], "r1")  # tie load 0, "r1" < "r2"
        l2 = crm.add_lead("2@ex.com", "B", "referral", "m1")
        self.assertEqual(crm.leads[l2]["owner"], "r2")  # r1 is full
        l3 = crm.add_lead("3@ex.com", "C", "referral", "m1")
        self.assertEqual(crm.leads[l3]["owner"], "r2")  # r2 load 1 < 2
        l4 = crm.add_lead("4@ex.com", "D", "referral", "m1")
        self.assertIsNone(crm.leads[l4]["owner"])  # queued
        l5 = crm.add_lead("5@ex.com", "E", "referral", "m1")
        self.assertIsNone(crm.leads[l5]["owner"])  # queue is FIFO: L4 then L5

    def test_capacity_zero_rep_never_gets_work(self):
        crm = CRM([{"id": "r0", "role": "rep", "capacity": 0},
                   {"id": "m", "role": "manager", "capacity": 0}])
        l1 = crm.add_lead("1@ex.com", "A", "web", "m")
        self.assertIsNone(crm.leads[l1]["owner"])

    def test_manager_never_owns(self):
        crm = CRM([{"id": "m", "role": "manager", "capacity": 9}])
        l1 = crm.add_lead("1@ex.com", "A", "web", "m")
        self.assertIsNone(crm.leads[l1]["owner"])

    def test_lead_record_exact(self):
        crm = default_crm()
        lead_id = crm.add_lead("  Ann@Ex.COM  ", " Ann Lee ", "event", "r1")
        self.assertEqual(lead_id, "L1")
        self.assertEqual(crm.leads[lead_id], {
            "id": "L1", "email": "ann@ex.com", "name": "Ann Lee",
            "source": "event", "score": 35, "owner": "r1", "status": "new",
        })
        self.assertEqual(crm.log, [("add_lead", "L1", "r1")])


class QualifyTests(unittest.TestCase):
    def setUp(self):
        self.crm = default_crm()
        self.lead = self.crm.add_lead("a@ex.com", "Ann", "referral", "m1")  # r1, 45

    def test_owner_success(self):
        self.crm.qualify(self.lead, "r1")
        self.assertEqual(self.crm.leads[self.lead]["status"], "qualified")
        self.assertEqual(self.crm.log,
                         [("add_lead", "L1", "m1"), ("qualify", "L1", "r1")])

    def test_other_rep_forbidden(self):
        with self.assertRaises(PermissionError):
            self.crm.qualify(self.lead, "r2")

    def test_unknown_lead_value_error(self):
        with self.assertRaises(ValueError):
            self.crm.qualify("L9", "r1")
        with self.assertRaises(ValueError):
            self.crm.qualify(None, "m1")

    def test_permission_before_status(self):
        # non-owner rep with an already-qualified lead -> PermissionError wins
        self.crm.qualify(self.lead, "m1")
        with self.assertRaises(PermissionError):
            self.crm.qualify(self.lead, "r2")

    def test_status_and_score_checks(self):
        low = self.crm.add_lead("w@ex.com", "W", "web", "m1")  # r2, 25
        self.crm.qualify(self.lead, "m1")
        with self.assertRaises(ValueError):  # score 25 < 30
            self.crm.qualify(low, "m1")
        with self.assertRaises(ValueError):  # already qualified
            self.crm.qualify(self.lead, "m1")
        self.assertEqual(self.crm.leads[low]["status"], "new")
        self.assertEqual(self.crm.leads[self.lead]["status"], "qualified")

    def test_manager_can_qualify_queued_unowned_lead(self):
        crm = fill_with_queue(default_crm())
        crm.qualify("L4", "m1")
        self.assertEqual(crm.leads["L4"]["status"], "qualified")
        self.assertIsNone(crm.leads["L4"]["owner"])


class ConvertTests(unittest.TestCase):
    def setUp(self):
        self.crm = default_crm()
        self.lead = self.crm.add_lead("a@ex.com", "Ann", "referral", "m1")  # r1
        self.crm.qualify(self.lead, "r1")

    def test_success(self):
        opp = self.crm.convert(self.lead, 1000, "r1")
        self.assertEqual(opp, "O1")
        self.assertEqual(self.crm.opps["O1"], {
            "id": "O1", "lead_id": "L1", "owner": "r1", "amount": 1000,
            "original_amount": 1000, "stage": "prospect",
        })
        self.assertEqual(self.crm.leads["L1"]["status"], "converted")
        self.assertEqual(self.crm.log[-1], ("convert", "O1", "r1"))

    def test_manager_convert_keeps_lead_owner_as_opp_owner(self):
        opp = self.crm.convert(self.lead, 500, "m1")
        self.assertEqual(self.crm.opps[opp]["owner"], "r1")

    def test_amount_validation(self):
        for bad in (0, -1, 10.0, "100", None, True, False):
            with self.assertRaises(ValueError, msg=repr(bad)):
                self.crm.convert(self.lead, bad, "r1")

    def test_amount_checked_before_ownership(self):
        # r2 is neither owner nor manager, but the amount error comes first
        with self.assertRaises(ValueError):
            self.crm.convert(self.lead, 0, "r2")

    def test_ownership_permission(self):
        with self.assertRaises(PermissionError):
            self.crm.convert(self.lead, 100, "r2")

    def test_status_and_owner_checks(self):
        fresh = self.crm.add_lead("n@ex.com", "N", "referral", "m1")  # -> r2, new
        with self.assertRaises(ValueError):
            self.crm.convert(fresh, 100, "r2")  # not qualified yet
        # fill r2, push a lead into the queue
        self.crm.add_lead("q@ex.com", "Q", "referral", "m1")  # -> r2 (full now)
        queued = self.crm.add_lead("z@ex.com", "Z", "referral", "m1")  # -> queue
        self.assertEqual(queued, "L4")
        self.crm.qualify("L4", "m1")
        with self.assertRaises(ValueError):
            self.crm.convert("L4", 100, "m1")  # qualified but unowned
        self.assertEqual(self.crm.leads["L4"]["status"], "qualified")

    def test_failed_convert_does_not_burn_opp_counter(self):
        with self.assertRaises(ValueError):
            self.crm.convert(self.lead, -5, "r1")
        self.assertEqual(self.crm.opps, {})
        self.assertEqual(self.crm.log, [("add_lead", "L1", "m1"),
                                        ("qualify", "L1", "r1")])
        opp = self.crm.convert(self.lead, 700, "r1")
        self.assertEqual(opp, "O1")
        second = self.crm.add_lead("b@ex.com", "B", "referral", "m1")  # r2
        self.crm.qualify(second, "r2")
        opp2 = self.crm.convert(second, 800, "r2")
        self.assertEqual(opp2, "O2")

    def test_conversion_preserves_load(self):
        # L1 counts for r1 while new/qualified; the opp counts after conversion,
        # so r1 stays at capacity 1 and cannot take more work.
        self.crm.convert(self.lead, 1000, "r1")
        nxt = self.crm.add_lead("n@ex.com", "N", "referral", "m1")
        self.assertEqual(crm_owner(self.crm, nxt), "r2")


class AdvanceTests(unittest.TestCase):
    def setUp(self):
        self.crm = default_crm()
        self.lead = self.crm.add_lead("a@ex.com", "Ann", "referral", "m1")
        self.crm.qualify(self.lead, "r1")
        self.opp = self.crm.convert(self.lead, 100, "r1")  # O1, owner r1

    def test_full_won_path(self):
        self.crm.advance(self.opp, "proposal", "r1")
        self.crm.advance(self.opp, "negotiation", "r1")
        self.crm.advance(self.opp, "won", "r1")
        self.assertEqual(self.crm.opps[self.opp]["stage"], "won")
        self.assertEqual(self.crm.log[-3:], [
            ("advance", "O1", "r1"),
            ("advance", "O1", "r1"),
            ("advance", "O1", "r1"),
        ])

    def test_lost_from_each_nonfinal_stage(self):
        crm = CRM([{"id": "r", "role": "rep", "capacity": 3},
                   {"id": "m", "role": "manager", "capacity": 0}])
        for i in range(3):
            lead = crm.add_lead("%d@ex.com" % i, "N", "referral", "m")
            crm.qualify(lead, "m")
            opp = crm.convert(lead, 100, "m")
            if i == 1:
                crm.advance(opp, "proposal", "m")
            elif i == 2:
                crm.advance(opp, "proposal", "m")
                crm.advance(opp, "negotiation", "m")
            crm.advance(opp, "lost", "m")  # lost allowed from every open stage
            self.assertEqual(crm.opps[opp]["stage"], "lost")

    def test_invalid_stage_value_checked_before_actor(self):
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "closed", "r2")  # bad stage beats perm
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, None, "m1")

    def test_permission_for_non_owner_rep(self):
        with self.assertRaises(PermissionError):
            self.crm.advance(self.opp, "proposal", "r2")
        # manager can act on anyone's opp
        self.crm.advance(self.opp, "proposal", "m1")

    def test_final_stage_stops_everything(self):
        self.crm.advance(self.opp, "proposal", "r1")
        self.crm.advance(self.opp, "negotiation", "r1")
        self.crm.advance(self.opp, "won", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "lost", "m1")
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "proposal", "m1")

    def test_only_next_stage_or_lost(self):
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "won", "r1")  # skipping ahead
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "negotiation", "r1")  # skipping
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "prospect", "r1")  # staying put
        self.crm.advance(self.opp, "proposal", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "prospect", "r1")  # no going back

    def test_stage_transition_checked_before_negotiation_gate(self):
        big_lead = self.crm.add_lead("b@ex.com", "B", "referral", "m1")  # r2
        self.crm.qualify(big_lead, "r2")
        big = self.crm.convert(big_lead, 60000, "r2")  # O2, prospect
        # skipping proposal is a ValueError even though the amount gate
        # would have said PermissionError
        with self.assertRaises(ValueError):
            self.crm.advance(big, "negotiation", "r2")

    def test_negotiation_amount_gate(self):
        big_lead = self.crm.add_lead("b@ex.com", "B", "referral", "m1")  # r2
        self.crm.qualify(big_lead, "r2")
        big = self.crm.convert(big_lead, 60000, "r2")
        self.crm.advance(big, "proposal", "r2")
        with self.assertRaises(PermissionError):
            self.crm.advance(big, "negotiation", "r2")
        self.crm.advance(big, "negotiation", "m1")  # manager allowed
        self.assertEqual(self.crm.opps[big]["stage"], "negotiation")

    def test_gate_boundary_exactly_50000_allowed_for_rep(self):
        lead = self.crm.add_lead("b@ex.com", "B", "referral", "m1")  # r2
        self.crm.qualify(lead, "r2")
        opp = self.crm.convert(lead, 50000, "r2")
        self.crm.advance(opp, "proposal", "r2")
        self.crm.advance(opp, "negotiation", "r2")  # not > 50000

    def test_won_frees_slot_and_assigns_oldest_queued(self):
        crm = fill_with_queue(default_crm())
        crm.qualify("L1", "r1")
        opp = crm.convert("L1", 100, "r1")  # O1 owner r1
        crm.advance(opp, "proposal", "r1")
        crm.advance(opp, "negotiation", "r1")
        crm.advance(opp, "won", "r1")
        self.assertEqual(crm.log[-2:], [
            ("advance", "O1", "r1"),
            ("assign", "L4", "system"),
        ])
        self.assertEqual(crm.leads["L4"]["owner"], "r1")
        self.assertEqual(crm.leads["L4"]["status"], "new")

    def test_nonfinal_advance_does_not_assign(self):
        crm = fill_with_queue(default_crm())
        crm.qualify("L1", "r1")
        opp = crm.convert("L1", 100, "r1")
        crm.advance(opp, "proposal", "r1")
        self.assertNotIn("assign", [e[0] for e in crm.log])
        self.assertIsNone(crm.leads["L4"]["owner"])

    def test_multi_slot_release_assigns_until_full(self):
        crm = CRM([
            {"id": "a", "role": "rep", "capacity": 3},
            {"id": "m", "role": "manager", "capacity": 0},
        ])
        for i in range(5):
            crm.add_lead("%d@ex.com" % i, "N", "referral", "m")
        self.assertIsNone(crm.leads["L4"]["owner"])
        self.assertIsNone(crm.leads["L5"]["owner"])
        for lid in ("L1", "L2", "L3"):
            crm.qualify(lid, "m")
        o1 = crm.convert("L1", 100, "m")
        o2 = crm.convert("L2", 100, "m")
        o3 = crm.convert("L3", 100, "m")
        crm.advance(o1, "lost", "m")
        self.assertEqual(crm.leads["L4"]["owner"], "a")   # oldest first
        crm.advance(o2, "proposal", "m")
        crm.advance(o2, "negotiation", "m")
        crm.advance(o2, "won", "m")
        self.assertEqual(crm.leads["L5"]["owner"], "a")
        crm.advance(o3, "lost", "m")  # queue empty -> no further assign
        assign_events = [e for e in crm.log if e[0] == "assign"]
        self.assertEqual(assign_events,
                         [("assign", "L4", "system"), ("assign", "L5", "system")])

    def test_failed_advance_changes_nothing(self):
        crm = fill_with_queue(default_crm())
        crm.qualify("L1", "r1")
        opp = crm.convert("L1", 60000, "r1")
        crm.advance(opp, "proposal", "r1")
        snapshot = copy.deepcopy((crm.leads, crm.opps, crm.log))
        with self.assertRaises(PermissionError):
            crm.advance(opp, "negotiation", "r1")  # >50k needs manager
        self.assertEqual((crm.leads, crm.opps, crm.log), snapshot)

    def test_lost_then_slot_free_via_manager_actor(self):
        # manager closes a rep's opp; the rep's slot frees, not the manager's
        crm = fill_with_queue(default_crm())
        crm.qualify("L1", "r1")
        opp = crm.convert("L1", 100, "r1")
        crm.advance(opp, "lost", "m1")
        self.assertEqual(crm.log[-1], ("assign", "L4", "system"))
        self.assertEqual(crm.leads["L4"]["owner"], "r1")

    def test_conversion_counts_in_load_until_closed(self):
        crm = fill_with_queue(default_crm())
        crm.qualify("L1", "r1")
        opp = crm.convert("L1", 100, "r1")
        new_lead = crm.add_lead("new@ex.com", "New", "referral", "m1")  # L5
        self.assertIsNone(crm.leads[new_lead]["owner"])  # r1 still loaded (O1)
        crm.advance(opp, "proposal", "r1")
        crm.advance(opp, "negotiation", "r1")
        crm.advance(opp, "won", "r1")
        # queue was [L4, L5]; one slot -> L4 only
        self.assertEqual(crm.leads["L4"]["owner"], "r1")
        self.assertIsNone(crm.leads["L5"]["owner"])

    def test_assigned_qualifying_lead_keeps_status(self):
        crm = fill_with_queue(default_crm())
        crm.qualify("L4", "m1")  # manager qualifies queued lead
        crm.qualify("L1", "r1")
        opp = crm.convert("L1", 100, "r1")
        crm.advance(opp, "proposal", "r1")
        crm.advance(opp, "negotiation", "r1")
        crm.advance(opp, "won", "r1")
        self.assertEqual(crm.leads["L4"]["owner"], "r1")
        self.assertEqual(crm.leads["L4"]["status"], "qualified")


class DiscountTests(unittest.TestCase):
    def setUp(self):
        self.crm = default_crm()
        lead = self.crm.add_lead("a@ex.com", "Ann", "referral", "m1")  # r1
        self.crm.qualify(lead, "r1")
        self.opp = self.crm.convert(lead, 1000, "r1")

    def test_rep_limit_10(self):
        self.crm.discount(self.opp, 10, "r1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 900)
        self.crm.discount(self.opp, 1, "r1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 891)
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp, 11, "r1")
        # manager may use higher pct, but 30 more would breach the 30%
        # cumulative floor against original_amount (1000): cap at 21
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp, 30, "m1")  # 891*.70=623 -> 62300<70000
        self.crm.discount(self.opp, 21, "m1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 703)  # 891*79//100

    def test_pct_validation(self):
        for bad in (0, 31, -5, 10.0, "10", None, True, False):
            with self.assertRaises(ValueError, msg=repr(bad)):
                self.crm.discount(self.opp, bad, "m1")

    def test_pct_checked_before_ownership(self):
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp, 0, "r2")  # ValueError beats perm
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp, 5, "r2")

    def test_check_order_ownership_stage_limit(self):
        # ownership PermissionError precedes the final-stage ValueError
        self.crm.advance(self.opp, "proposal", "r1")
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp, 5, "r2")
        self.crm.advance(self.opp, "negotiation", "r1")
        self.crm.advance(self.opp, "won", "r1")
        # final-stage ValueError precedes the rep-limit PermissionError
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp, 25, "r1")
        # ... and a valid pct on a closed opp by the owner is still ValueError
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp, 5, "r1")

    def test_cumulative_cap_30_percent(self):
        self.crm.discount(self.opp, 15, "m1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 850)
        self.crm.discount(self.opp, 15, "m1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 722)  # 850*.85
        self.crm.discount(self.opp, 1, "m1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 714)  # 722*.99
        self.crm.discount(self.opp, 1, "m1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 706)  # 714*.99
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp, 1, "m1")  # 706*.99=706 -> 698 -> 69800<70000
        self.assertEqual(self.crm.opps[self.opp]["amount"], 706)
        self.assertEqual(self.crm.log[-1], ("discount", "O1", "m1"))

    def test_floor_at_exactly_70_percent_allowed(self):
        self.crm.discount(self.opp, 30, "m1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 700)
        self.assertEqual(self.crm.log[-1], ("discount", "O1", "m1"))
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp, 1, "m1")  # 693 -> below 70% of original

    def test_discount_enables_negotiation_gate(self):
        lead = self.crm.add_lead("b@ex.com", "B", "referral", "m1")  # r2
        self.crm.qualify(lead, "r2")
        opp = self.crm.convert(lead, 60000, "r2")
        self.crm.advance(opp, "proposal", "r2")
        with self.assertRaises(PermissionError):
            self.crm.advance(opp, "negotiation", "r2")
        self.crm.discount(opp, 20, "m1")  # 48000
        self.crm.advance(opp, "negotiation", "r2")
        self.assertEqual(self.crm.opps[opp]["stage"], "negotiation")

    def test_failed_discount_no_log(self):
        snap = copy.deepcopy((self.crm.leads, self.crm.opps, self.crm.log))
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp, 30, "r1")  # rep limit is 10
        self.assertEqual((self.crm.leads, self.crm.opps, self.crm.log), snap)


class TransferTests(unittest.TestCase):
    def setUp(self):
        self.crm = fill_with_queue(default_crm())
        self.crm.qualify("L1", "m1")
        self.opp = self.crm.convert("L1", 100, "m1")  # O1 owner r1

    def _open_r2_slot(self):
        # convert+close r2's L2 so r2 drops below capacity
        self.crm.qualify("L2", "r2")
        o2 = self.crm.convert("L2", 100, "r2")
        self.crm.advance(o2, "lost", "r2")

    def test_manager_success(self):
        self._open_r2_slot()
        # L4 was reassigned to r2 when the slot opened, so r2 is full again
        self.assertEqual(self.crm.leads["L4"]["owner"], "r2")
        self.crm.qualify("L4", "r2")
        o4 = self.crm.convert("L4", 100, "r2")
        # walk O4 to the end so r2 drops below capacity
        self.crm.advance(o4, "proposal", "r2")
        self.crm.advance(o4, "negotiation", "r2")
        self.crm.advance(o4, "won", "r2")
        self.crm.transfer(self.opp, "r2", "m1")
        self.assertEqual(self.crm.opps[self.opp]["owner"], "r2")
        self.assertEqual(self.crm.log[-1], ("transfer", "O1", "m1"))

    def test_actor_must_be_manager(self):
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.opp, "r2", "r1")  # even the owner
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.opp, "r2", "r2")

    def test_actor_checked_before_new_owner_validation(self):
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.opp, "does-not-exist", "r1")

    def test_new_owner_must_be_rep(self):
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "m1", "m1")  # manager
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "ghost", "m1")  # unknown
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, None, "m1")

    def test_same_owner_rejected(self):
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "r1", "m1")

    def test_capacity_rejected(self):
        # r2 currently owns L2+L3 (load 2 = capacity 2)
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "r2", "m1")

    def test_final_stage_rejected(self):
        self.crm.advance(self.opp, "lost", "m1")
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "r2", "m1")

    def test_failed_transfer_changes_nothing(self):
        snap_leads = copy.deepcopy(self.crm.leads)
        snap_opps = copy.deepcopy(self.crm.opps)
        snap_log = list(self.crm.log)
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "r2", "m1")  # r2 at capacity
        self.assertEqual(self.crm.leads, snap_leads)
        self.assertEqual(self.crm.opps, snap_opps)
        self.assertEqual(self.crm.log, snap_log)
        self.assertIsNone(self.crm.leads["L4"]["owner"])  # no sneaky assign

    def test_unknown_opp_value_error(self):
        with self.assertRaises(ValueError):
            self.crm.transfer("O9", "r2", "m1")


class ForecastTests(unittest.TestCase):
    def test_empty(self):
        crm = default_crm()
        self.assertEqual(crm.forecast(), {"open": 0, "weighted": 0, "won": 0})

    def test_weights_and_floor(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 9},
                   {"id": "m", "role": "manager", "capacity": 0}])
        opps = []
        amounts = [1000, 999, 1000, 500, 700]
        for i, amt in enumerate(amounts):
            lead = crm.add_lead("l%d@ex.com" % i, "N", "referral", "m")
            crm.qualify(lead, "m")
            opps.append(crm.convert(lead, amt, "m"))
        # O1 prospect 1000 | O2 proposal 999 | O3 negotiation 1000
        # | O4 won 500 | O5 lost 700
        crm.advance(opps[1], "proposal", "m")
        crm.advance(opps[2], "proposal", "m")
        crm.advance(opps[2], "negotiation", "m")
        crm.advance(opps[3], "proposal", "m")
        crm.advance(opps[3], "negotiation", "m")
        crm.advance(opps[3], "won", "m")
        crm.advance(opps[4], "proposal", "m")
        crm.advance(opps[4], "lost", "m")
        result = crm.forecast()
        self.assertEqual(999 * 30 // 100, 299)
        self.assertEqual(result,
                         {"open": 3, "weighted": 100 + 299 + 600, "won": 500})

    def test_forecast_no_actor_no_log(self):
        crm = default_crm()
        before = list(crm.log)
        crm.forecast()
        self.assertEqual(crm.log, before)


class LoadAccountingTests(unittest.TestCase):
    def test_won_opp_and_converted_lead_do_not_count(self):
        crm = CRM([{"id": "r", "role": "rep", "capacity": 2},
                   {"id": "m", "role": "manager", "capacity": 0}])
        l1 = crm.add_lead("1@ex.com", "A", "referral", "m")
        l2 = crm.add_lead("2@ex.com", "B", "referral", "m")
        l3 = crm.add_lead("3@ex.com", "C", "referral", "m")  # queued
        crm.qualify(l1, "m")
        o1 = crm.convert(l1, 100, "m")
        crm.advance(o1, "proposal", "m")
        crm.advance(o1, "negotiation", "m")
        crm.advance(o1, "won", "m")  # frees slot -> l3 assigned
        self.assertEqual(crm.leads[l3]["owner"], "r")
        self.assertEqual(crm._load("r"), 2)  # l2 + l3

    def test_open_opp_blocks_capacity(self):
        crm = CRM([{"id": "r", "role": "rep", "capacity": 1},
                   {"id": "m", "role": "manager", "capacity": 0}])
        l1 = crm.add_lead("1@ex.com", "A", "referral", "m")
        crm.qualify(l1, "m")
        crm.convert(l1, 100, "m")
        l2 = crm.add_lead("2@ex.com", "B", "referral", "m")
        self.assertIsNone(crm.leads[l2]["owner"])

    def test_lost_lead_statuses_do_not_matter_for_load(self):
        crm = CRM([{"id": "r", "role": "rep", "capacity": 1},
                   {"id": "m", "role": "manager", "capacity": 0}])
        l1 = crm.add_lead("1@ex.com", "A", "referral", "m")
        self.assertEqual(crm._load("r"), 1)
        crm.qualify(l1, "m")
        self.assertEqual(crm._load("r"), 1)
        o1 = crm.convert(l1, 100, "m")
        self.assertEqual(crm._load("r"), 1)  # converted lead off, open opp on
        crm.advance(o1, "lost", "m")
        self.assertEqual(crm._load("r"), 0)


class IntegrationTests(unittest.TestCase):
    def test_end_to_end_log(self):
        crm = default_crm()
        l1 = crm.add_lead("a@ex.com", "Ann", "referral", "m1")  # r1, 45
        l2 = crm.add_lead("b@ex.com", "Bob", "web", "m1")  # r2, 25
        with self.assertRaises(ValueError):
            crm.qualify(l2, "r2")  # score 25
        l3 = crm.add_lead("c@gmail.com", "Cleo", "referral", "m1")  # r2, 30
        l4 = crm.add_lead("d@ex.com", "Dan", "event", "m1")  # queue, 35
        crm.qualify(l1, "r1")
        o1 = crm.convert(l1, 60000, "r1")
        crm.advance(o1, "proposal", "r1")
        with self.assertRaises(PermissionError):
            crm.advance(o1, "negotiation", "r1")  # > 50k
        crm.discount(o1, 20, "m1")  # 48000
        crm.advance(o1, "negotiation", "r1")
        crm.advance(o1, "won", "r1")
        self.assertEqual(crm.log, [
            ("add_lead", "L1", "m1"),
            ("add_lead", "L2", "m1"),
            ("add_lead", "L3", "m1"),
            ("add_lead", "L4", "m1"),
            ("qualify", "L1", "r1"),
            ("convert", "O1", "r1"),
            ("advance", "O1", "r1"),
            ("discount", "O1", "m1"),
            ("advance", "O1", "r1"),
            ("advance", "O1", "r1"),
            ("assign", "L4", "system"),
        ])
        self.assertEqual(crm.leads["L4"]["owner"], "r1")
        self.assertEqual(crm.leads["L4"]["status"], "new")
        self.assertEqual(crm.forecast(),
                         {"open": 0, "weighted": 0, "won": 48000})

    def test_every_failed_call_is_inert(self):
        crm = fill_with_queue(default_crm())
        crm.qualify("L1", "r1")
        crm.convert("L1", 100, "r1")
        crm.advance("O1", "proposal", "r1")
        failures = [
            lambda: crm.add_lead("a@ex.com", "dup", "web", "m1"),  # duplicate
            lambda: crm.add_lead("bad", "n", "web", "m1"),         # bad email
            lambda: crm.add_lead("ok@ex.com", "", "web", "m1"),    # bad name
            lambda: crm.qualify("L9", "m1"),                       # unknown lead
            lambda: crm.qualify("L2", "r1"),                       # not owner
            lambda: crm.convert("O1", 1, "m1"),                    # unknown lead
            lambda: crm.advance("O1", "won", "r1"),                # skipping
            lambda: crm.discount("O1", 55, "m1"),                  # bad pct
            lambda: crm.transfer("O1", "r2", "m1"),                # r2 full
        ]
        snapshot = copy.deepcopy((crm.leads, crm.opps, crm.log))
        for call in failures:
            with self.assertRaises(Exception):
                call()
        self.assertEqual((crm.leads, crm.opps, crm.log), snapshot)


def crm_owner(crm, lead_id):
    return crm.leads[lead_id]["owner"]


if __name__ == "__main__":
    unittest.main()
