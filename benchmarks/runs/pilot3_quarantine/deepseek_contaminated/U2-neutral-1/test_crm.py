import copy
import unittest

from crm import CRM, DuplicateLeadError


REPS = [
    {"id": "rep1", "role": "rep", "capacity": 3},
    {"id": "rep2", "role": "rep", "capacity": 3},
    {"id": "mgr", "role": "manager", "capacity": 0},
]

ORDER = ["prospect", "proposal", "negotiation", "won"]


def snapshot(crm):
    return (
        copy.deepcopy(crm.leads),
        copy.deepcopy(crm.opps),
        list(crm.log),
        list(crm.waiting),
    )


def new_lead(crm, email="a@acme.com", name="A", source="referral", actor="mgr"):
    return crm.add_lead(email, name, source, actor)


def qualified_lead(crm, email="a@acme.com"):
    lead_id = crm.add_lead(email, "A", "referral", "mgr")
    crm.qualify(lead_id, "mgr")
    return lead_id


def new_opp(crm, email="a@acme.com", amount=1000):
    lead_id = qualified_lead(crm, email)
    return crm.convert(lead_id, amount, "mgr")


def walk(crm, opp_id, target, actor="mgr"):
    """Advance step by step (or straight to lost) until target is reached."""
    if target == "lost":
        crm.advance(opp_id, "lost", actor)
        return
    while crm.opps[opp_id]["stage"] != target:
        current = crm.opps[opp_id]["stage"]
        crm.advance(opp_id, ORDER[ORDER.index(current) + 1], actor)


class TestInitialState(unittest.TestCase):
    def test_empty(self):
        crm = CRM(REPS)
        self.assertEqual(crm.leads, {})
        self.assertEqual(crm.opps, {})
        self.assertEqual(crm.log, [])

    def test_unknown_actor_rejected_first(self):
        crm = CRM(REPS)
        lead = new_lead(crm, "first@acme.com")
        opp = new_opp(crm, "second@acme.com")
        before = snapshot(crm)
        calls = [
            lambda: crm.add_lead("x@y.com", "X", "web", "ghost"),
            lambda: crm.add_lead(5, None, "bogus", "ghost"),
            lambda: crm.qualify(lead, "ghost"),
            lambda: crm.qualify("L99", "ghost"),
            lambda: crm.convert(lead, 100, "ghost"),
            lambda: crm.convert("L99", 0, "ghost"),
            lambda: crm.advance(opp, "proposal", "ghost"),
            lambda: crm.advance("O99", "bogus", "ghost"),
            lambda: crm.discount(opp, 5, "ghost"),
            lambda: crm.discount("O99", 0, "ghost"),
            lambda: crm.transfer(opp, "rep2", "ghost"),
            lambda: crm.transfer("O99", "ghost", "ghost"),
        ]
        for call in calls:
            with self.assertRaises(PermissionError):
                call()
        self.assertEqual(snapshot(crm), before)

    def test_unhashable_actor_is_permission_error(self):
        crm = CRM(REPS)
        with self.assertRaises(PermissionError):
            crm.qualify("L1", ["not", "hashable"])


class TestAddLead(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(REPS)

    def test_happy_path(self):
        lead_id = self.crm.add_lead("  Alice@Example.COM ", "  Alice  ", "web", "rep1")
        self.assertEqual(lead_id, "L1")
        self.assertEqual(
            self.crm.leads["L1"],
            {
                "id": "L1",
                "email": "alice@example.com",
                "name": "Alice",
                "source": "web",
                "score": 25,
                "owner": "rep1",
                "status": "new",
            },
        )
        self.assertEqual(self.crm.log, [("add_lead", "L1", "rep1")])

    def test_sequential_ids(self):
        self.assertEqual(new_lead(self.crm, "a@x.com"), "L1")
        self.assertEqual(new_lead(self.crm, "b@x.com"), "L2")

    def test_failures_do_not_consume_ids_or_log(self):
        bad = [
            lambda: self.crm.add_lead(5, "A", "web", "rep1"),
            lambda: self.crm.add_lead("nope", "A", "web", "rep1"),
            lambda: self.crm.add_lead("a@x.com", "   ", "web", "rep1"),
            lambda: self.crm.add_lead("a@x.com", "A", "tv", "rep1"),
            lambda: self.crm.add_lead("a@x.com", "A", "web", "ghost"),
        ]
        for call in bad:
            with self.assertRaises((ValueError, PermissionError)):
                call()
        self.assertEqual(self.crm.leads, {})
        self.assertEqual(self.crm.log, [])
        self.assertEqual(new_lead(self.crm, "a@x.com"), "L1")

    def test_invalid_emails(self):
        for email in ("", "plain", "a@@b.com", "@b.com", "a@bcom", "a@.com", "a@com.", "a@.b", "a@b."):
            with self.assertRaises(ValueError, msg=email):
                self.crm.add_lead(email, "A", "web", "rep1")
        self.assertEqual(self.crm.log, [])

    def test_email_edge_cases_accepted(self):
        for email in ("a@b.c", "a@b..com", "first.last@sub.example.org"):
            lead_id = self.crm.add_lead(email, "A", "web", "rep1")
            self.assertIn(lead_id, self.crm.leads)
        self.assertEqual(len(self.crm.leads), 3)

    def test_invalid_names(self):
        for name in (None, "", "   ", 7, ["x"]):
            with self.assertRaises(ValueError, msg=repr(name)):
                self.crm.add_lead("a@x.com", name, "web", "rep1")

    def test_invalid_sources(self):
        for source in ("Web", "", None, 1, "email", ["web"]):
            with self.assertRaises(ValueError, msg=repr(source)):
                self.crm.add_lead("a@x.com", "A", source, "rep1")

    def test_scores(self):
        cases = [
            ("web", "gmail.com", 10),
            ("web", "yahoo.com", 10),
            ("web", "outlook.com", 10),
            ("web", "acme.com", 25),
            ("referral", "gmail.com", 30),
            ("referral", "acme.com", 45),
            ("event", "outlook.com", 20),
            ("event", "acme.com", 35),
        ]
        for i, (source, domain, expected) in enumerate(cases):
            crm = CRM(REPS)
            lead_id = crm.add_lead("u%d@%s" % (i, domain), "U", source, "rep1")
            self.assertEqual(crm.leads[lead_id]["score"], expected, (source, domain))

    def test_score_domain_check_is_case_insensitive(self):
        lead_id = self.crm.add_lead("A@GMAIL.COM", "A", "web", "rep1")
        self.assertEqual(self.crm.leads[lead_id]["score"], 10)

    def test_duplicate_after_normalization(self):
        self.crm.add_lead("Bob@Mail.com", "Bob", "web", "rep1")
        for email in ("bob@mail.com", "  BOB@MAIL.COM "):
            with self.assertRaises(DuplicateLeadError) as ctx:
                self.crm.add_lead(email, "Other", "event", "rep2")
            self.assertEqual(ctx.exception.existing_id, "L1")
        self.assertEqual(len(self.crm.leads), 1)
        self.assertEqual(self.crm.log, [("add_lead", "L1", "rep1")])

    def test_duplicate_error_type(self):
        self.crm.add_lead("bob@mail.com", "Bob", "web", "rep1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            self.crm.add_lead("bob@mail.com", "Bob", "web", "rep1")
        self.assertIsInstance(ctx.exception, Exception)
        self.assertFalse(isinstance(ctx.exception, ValueError))

    def test_source_error_beats_duplicate(self):
        self.crm.add_lead("bob@mail.com", "Bob", "web", "rep1")
        with self.assertRaises(ValueError) as ctx:
            self.crm.add_lead("bob@mail.com", "Bob", "bogus", "rep1")
        self.assertNotIsInstance(ctx.exception, DuplicateLeadError)

    def test_duplicate_error_beats_assignment(self):
        crm = CRM([{"id": "r", "role": "rep", "capacity": 0}])
        crm.add_lead("bob@mail.com", "Bob", "web", "r")
        before = snapshot(crm)
        with self.assertRaises(DuplicateLeadError):
            crm.add_lead("bob@mail.com", "Bob", "web", "r")
        self.assertEqual(snapshot(crm), before)

    def test_tie_break_smallest_id_not_insertion_order(self):
        reps = [
            {"id": "zz", "role": "rep", "capacity": 5},
            {"id": "aa", "role": "rep", "capacity": 5},
            {"id": "mm", "role": "manager", "capacity": 5},
        ]
        crm = CRM(reps)
        self.assertEqual(crm.leads[new_lead(crm, "a@x.com", actor="aa")]["owner"], "aa")
        self.assertEqual(crm.leads[new_lead(crm, "b@x.com", actor="aa")]["owner"], "zz")

    def test_lowest_load_wins(self):
        crm = CRM(
            [
                {"id": "a", "role": "rep", "capacity": 5},
                {"id": "b", "role": "rep", "capacity": 5},
            ]
        )
        owners = [crm.leads[new_lead(crm, "%s@x.com" % c, actor="a")]["owner"] for c in "xyz"]
        self.assertEqual(owners, ["a", "b", "a"])

    def test_managers_never_receive_work(self):
        crm = CRM([{"id": "mgr", "role": "manager", "capacity": 5}])
        lead_id = new_lead(crm, "a@x.com")
        self.assertIsNone(crm.leads[lead_id]["owner"])
        self.assertEqual(crm.waiting, [lead_id])

    def test_zero_capacity_rep_queues(self):
        crm = CRM([{"id": "r", "role": "rep", "capacity": 0}])
        lead_id = new_lead(crm, "a@x.com", actor="r")
        self.assertIsNone(crm.leads[lead_id]["owner"])
        self.assertEqual(crm.waiting, [lead_id])

    def test_fifo_waiting_order(self):
        crm = CRM([{"id": "r", "role": "rep", "capacity": 1}])
        first = new_lead(crm, "a@x.com", actor="r")
        queued = [new_lead(crm, "%s@x.com" % c, actor="r") for c in "bcd"]
        self.assertEqual(crm.waiting, queued)
        self.assertEqual(crm.leads[first]["owner"], "r")


class TestQualify(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(REPS)
        self.lead = new_lead(self.crm, "corp@acme.com")

    def test_success(self):
        self.crm.qualify(self.lead, "rep1")
        self.assertEqual(self.crm.leads[self.lead]["status"], "qualified")
        self.assertEqual(self.crm.log[-1], ("qualify", self.lead, "rep1"))

    def test_manager_may_qualify(self):
        self.crm.qualify(self.lead, "mgr")
        self.assertEqual(self.crm.leads[self.lead]["status"], "qualified")

    def test_unknown_lead(self):
        for lead_id in ("L99", None, 5):
            with self.assertRaises(ValueError, msg=repr(lead_id)):
                self.crm.qualify(lead_id, "rep1")

    def test_non_owner_rep_denied(self):
        before = snapshot(self.crm)
        with self.assertRaises(PermissionError):
            self.crm.qualify(self.lead, "rep2")
        self.assertEqual(snapshot(self.crm), before)

    def test_status_must_be_new(self):
        self.crm.qualify(self.lead, "rep1")
        before = snapshot(self.crm)
        with self.assertRaises(ValueError):
            self.crm.qualify(self.lead, "rep1")
        self.assertEqual(snapshot(self.crm), before)

    def test_score_gate(self):
        low = new_lead(self.crm, "web@gmail.com", source="web")
        self.assertEqual(self.crm.leads[low]["score"], 10)
        with self.assertRaises(ValueError):
            self.crm.qualify(low, "mgr")
        event_low = new_lead(self.crm, "ev@outlook.com", source="event")
        self.assertEqual(self.crm.leads[event_low]["score"], 20)
        with self.assertRaises(ValueError):
            self.crm.qualify(event_low, "mgr")
        event_ok = new_lead(self.crm, "ev@acme.com", source="event")
        self.crm.qualify(event_ok, "mgr")
        self.assertEqual(self.crm.leads[event_ok]["status"], "qualified")

    def test_stale_owner_cannot_qualify(self):
        crm = CRM([{"id": "r", "role": "rep", "capacity": 0}, {"id": "mgr", "role": "manager", "capacity": 0}])
        lead = new_lead(crm, "a@acme.com")
        before = snapshot(crm)
        with self.assertRaises(PermissionError):
            crm.qualify(lead, "r")
        self.assertEqual(snapshot(crm), before)


class TestConvert(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(REPS)
        self.lead = qualified_lead(self.crm, "corp@acme.com")

    def test_success(self):
        opp_id = self.crm.convert(self.lead, 5000, "rep1")
        self.assertEqual(opp_id, "O1")
        self.assertEqual(
            self.crm.opps["O1"],
            {
                "id": "O1",
                "lead_id": self.lead,
                "owner": "rep1",
                "amount": 5000,
                "original_amount": 5000,
                "stage": "prospect",
            },
        )
        self.assertEqual(self.crm.leads[self.lead]["status"], "converted")
        self.assertEqual(self.crm.log[-1], ("convert", "O1", "rep1"))

    def test_sequential_ids(self):
        second = qualified_lead(self.crm, "b@acme.com")
        self.assertEqual(self.crm.convert(self.lead, 1, "mgr"), "O1")
        self.assertEqual(self.crm.convert(second, 2, "mgr"), "O2")

    def test_manager_may_convert_and_owner_is_lead_owner(self):
        opp_id = self.crm.convert(self.lead, 10, "mgr")
        self.assertEqual(self.crm.opps[opp_id]["owner"], "rep1")

    def test_amount_validation(self):
        for amount in (0, -5, True, False, 1.5, "10", None):
            with self.assertRaises(ValueError, msg=repr(amount)):
                self.crm.convert(self.lead, amount, "rep1")
        self.assertEqual(self.crm.opps, {})
        self.assertEqual(self.crm.leads[self.lead]["status"], "qualified")

    def test_unknown_lead(self):
        with self.assertRaises(ValueError):
            self.crm.convert("L42", 10, "rep1")

    def test_amount_check_precedes_permission(self):
        with self.assertRaises(ValueError):
            self.crm.convert(self.lead, 0, "rep2")

    def test_permission(self):
        before = snapshot(self.crm)
        with self.assertRaises(PermissionError):
            self.crm.convert(self.lead, 10, "rep2")
        self.assertEqual(snapshot(self.crm), before)

    def test_status_must_be_qualified(self):
        fresh = new_lead(self.crm, "new@acme.com")
        with self.assertRaises(ValueError):
            self.crm.convert(fresh, 10, "mgr")
        self.assertEqual(self.crm.opps, {})

    def test_owner_required(self):
        crm = CRM(
            [
                {"id": "r", "role": "rep", "capacity": 0},
                {"id": "mgr", "role": "manager", "capacity": 0},
            ]
        )
        lead_id = new_lead(crm, "a@acme.com")
        crm.qualify(lead_id, "mgr")
        with self.assertRaises(ValueError):
            crm.convert(lead_id, 100, "mgr")
        self.assertEqual(crm.opps, {})
        self.assertEqual(crm.leads[lead_id]["status"], "qualified")
        self.assertEqual(crm.log, [("add_lead", "L1", "mgr"), ("qualify", "L1", "mgr")])


class TestAdvance(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(REPS)
        self.opp = new_opp(self.crm, "corp@acme.com", 1000)

    def test_full_chain_and_log(self):
        walk(self.crm, self.opp, "won")
        self.assertEqual(self.crm.opps[self.opp]["stage"], "won")
        self.assertEqual(
            [entry for entry in self.crm.log if entry[0] == "advance"],
            [
                ("advance", self.opp, "mgr"),
                ("advance", self.opp, "mgr"),
                ("advance", self.opp, "mgr"),
            ],
        )

    def test_lost_from_any_non_final(self):
        for start in (0, 1, 2):
            crm = CRM(REPS)
            opp = new_opp(crm, "corp@acme.com", 1000)
            if start:
                walk(crm, opp, ORDER[start])
            crm.advance(opp, "lost", "mgr")
            self.assertEqual(crm.opps[opp]["stage"], "lost")
            self.assertEqual(crm.log[-1], ("advance", opp, "mgr"))

    def test_skipping_rejected(self):
        crm = CRM(REPS)
        opp = new_opp(crm, "corp@acme.com", 1000)
        for stage in ("negotiation", "won"):
            with self.assertRaises(ValueError, msg=stage):
                crm.advance(opp, stage, "mgr")
        self.assertEqual(crm.opps[opp]["stage"], "prospect")

    def test_backwards_and_same_stage_rejected(self):
        crm = CRM(REPS)
        opp = new_opp(crm, "corp@acme.com", 1000)
        crm.advance(opp, "proposal", "mgr")
        for stage in ("prospect", "proposal", "won"):
            with self.assertRaises(ValueError, msg=stage):
                crm.advance(opp, stage, "mgr")

    def test_bad_stage(self):
        for stage in ("Proposal", "", None, "closed", 3):
            with self.assertRaises(ValueError, msg=repr(stage)):
                self.crm.advance(self.opp, stage, "mgr")

    def test_stage_check_precedes_permission(self):
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "bogus", "rep2")

    def test_final_stage_is_frozen(self):
        walk(self.crm, self.opp, "won")
        before = snapshot(self.crm)
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "lost", "mgr")
        self.assertEqual(snapshot(self.crm), before)

    def test_unknown_opp(self):
        for opp_id in ("O9", None, 1):
            with self.assertRaises(ValueError, msg=repr(opp_id)):
                self.crm.advance(opp_id, "proposal", "mgr")

    def test_permission(self):
        before = snapshot(self.crm)
        with self.assertRaises(PermissionError):
            self.crm.advance(self.opp, "proposal", "rep2")
        self.assertEqual(snapshot(self.crm), before)

    def test_owner_may_advance(self):
        owner = self.crm.opps[self.opp]["owner"]
        self.crm.advance(self.opp, "proposal", owner)
        self.assertEqual(self.crm.opps[self.opp]["stage"], "proposal")

    def test_large_negotiation_requires_manager(self):
        opp = new_opp(self.crm, "big@acme.com", 60000)
        owner = self.crm.opps[opp]["owner"]
        self.crm.advance(opp, "proposal", owner)
        before = snapshot(self.crm)
        with self.assertRaises(PermissionError):
            self.crm.advance(opp, "negotiation", owner)
        self.assertEqual(snapshot(self.crm), before)
        self.crm.advance(opp, "negotiation", "mgr")
        self.assertEqual(self.crm.opps[opp]["stage"], "negotiation")

    def test_threshold_is_strictly_greater(self):
        opp = new_opp(self.crm, "edge@acme.com", 50000)
        owner = self.crm.opps[opp]["owner"]
        self.crm.advance(opp, "proposal", owner)
        self.crm.advance(opp, "negotiation", owner)
        self.assertEqual(self.crm.opps[opp]["stage"], "negotiation")

    def test_large_amount_after_discounts_may_proceed(self):
        opp = new_opp(self.crm, "d@acme.com", 60000)
        owner = self.crm.opps[opp]["owner"]
        self.crm.discount(opp, 10, owner)
        self.crm.discount(opp, 10, owner)
        self.assertEqual(self.crm.opps[opp]["amount"], 48600)
        self.crm.advance(opp, "proposal", owner)
        self.crm.advance(opp, "negotiation", owner)
        self.assertEqual(self.crm.opps[opp]["stage"], "negotiation")


class TestQueueOnClose(unittest.TestCase):
    def test_won_frees_slot_and_assigns_fifo(self):
        crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 1},
                {"id": "mgr", "role": "manager", "capacity": 0},
            ]
        )
        first = new_lead(crm, "a@acme.com")
        self.assertEqual(crm.leads[first]["owner"], "r1")
        queued = [new_lead(crm, "%s@acme.com" % c) for c in ("b", "c")]
        self.assertEqual(crm.waiting, queued)

        crm.qualify(first, "mgr")
        opp = crm.convert(first, 100, "mgr")
        walk(crm, opp, "won")

        self.assertEqual(crm.leads[queued[0]]["owner"], "r1")
        self.assertEqual(crm.waiting, [queued[1]])
        self.assertEqual(crm.log[-1], ("assign", queued[0], "system"))

    def test_lost_frees_slot_too(self):
        crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 1},
                {"id": "mgr", "role": "manager", "capacity": 0},
            ]
        )
        first = new_lead(crm, "a@acme.com")
        queued = new_lead(crm, "b@acme.com")
        crm.qualify(first, "mgr")
        opp = crm.convert(first, 100, "mgr")
        crm.advance(opp, "lost", "mgr")
        self.assertEqual(crm.leads[queued]["owner"], "r1")
        self.assertEqual(crm.log[-1], ("assign", queued, "system"))

    def test_assignment_stops_at_capacity(self):
        crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 2},
                {"id": "mgr", "role": "manager", "capacity": 0},
            ]
        )
        first = new_lead(crm, "a@acme.com")
        second = new_lead(crm, "b@acme.com")
        queued = [new_lead(crm, "%s@acme.com" % c) for c in ("c", "d")]
        self.assertEqual(crm.waiting, queued)

        crm.qualify(first, "mgr")
        opp = crm.convert(first, 100, "mgr")
        walk(crm, opp, "won")

        self.assertEqual(crm.leads[queued[0]]["owner"], "r1")
        self.assertEqual(crm.waiting, [queued[1]])
        self.assertEqual(crm.leads[second]["owner"], "r1")

    def test_middle_close_keeps_queue_when_no_capacity(self):
        crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 2},
                {"id": "mgr", "role": "manager", "capacity": 0},
            ]
        )
        a = new_lead(crm, "a@acme.com")
        b = new_lead(crm, "b@acme.com")
        queued = new_lead(crm, "c@acme.com")
        crm.qualify(a, "mgr")
        opp = crm.convert(a, 100, "mgr")
        walk(crm, opp, "won")
        self.assertEqual(crm.leads[queued]["owner"], "r1")
        self.assertEqual(crm.leads[b]["owner"], "r1")


class TestDiscount(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(REPS)
        self.opp = new_opp(self.crm, "corp@acme.com", 1000)

    def test_success(self):
        owner = self.crm.opps[self.opp]["owner"]
        self.crm.discount(self.opp, 10, owner)
        self.assertEqual(self.crm.opps[self.opp]["amount"], 900)
        self.assertEqual(self.crm.opps[self.opp]["original_amount"], 1000)
        self.assertEqual(self.crm.log[-1], ("discount", self.opp, owner))

    def test_manager_may_use_30(self):
        self.crm.discount(self.opp, 30, "mgr")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 700)

    def test_pct_validation(self):
        for pct in (0, 31, -1, True, False, 5.0, "5", None):
            with self.assertRaises(ValueError, msg=repr(pct)):
                self.crm.discount(self.opp, pct, "mgr")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 1000)

    def test_pct_check_precedes_permission(self):
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp, 0, "rep2")

    def test_rep_capped_at_10(self):
        owner = self.crm.opps[self.opp]["owner"]
        for pct in (11, 30):
            before = snapshot(self.crm)
            with self.assertRaises(PermissionError, msg=pct):
                self.crm.discount(self.opp, pct, owner)
            self.assertEqual(snapshot(self.crm), before)

    def test_manager_may_exceed_10(self):
        self.crm.discount(self.opp, 15, "mgr")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 850)

    def test_non_owner_denied(self):
        owner = self.crm.opps[self.opp]["owner"]
        other = "rep2" if owner == "rep1" else "rep1"
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp, 5, other)

    def test_final_stage_rejected(self):
        walk(self.crm, self.opp, "lost")
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp, 5, "mgr")

    def test_cumulative_cap(self):
        self.crm.discount(self.opp, 20, "mgr")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 800)
        before = snapshot(self.crm)
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp, 20, "mgr")
        self.assertEqual(snapshot(self.crm), before)
        self.crm.discount(self.opp, 12, "mgr")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 704)

    def test_exact_boundary_allowed(self):
        crm = CRM(REPS)
        opp = new_opp(crm, "corp@acme.com", 100)
        crm.discount(opp, 30, "mgr")
        self.assertEqual(crm.opps[opp]["amount"], 70)
        crm2 = CRM(REPS)
        opp2 = new_opp(crm2, "corp@acme.com", 1000)
        crm2.discount(opp2, 10, "mgr")
        crm2.discount(opp2, 10, "mgr")
        crm2.discount(opp2, 10, "mgr")
        self.assertEqual(crm2.opps[opp2]["amount"], 729)
        with self.assertRaises(ValueError):
            crm2.discount(opp2, 10, "mgr")

    def test_floor_division(self):
        crm = CRM(REPS)
        opp = new_opp(crm, "corp@acme.com", 1001)
        crm.discount(opp, 3, "mgr")
        self.assertEqual(crm.opps[opp]["amount"], 1001 * 97 // 100)

    def test_unknown_opp(self):
        with self.assertRaises(ValueError):
            self.crm.discount("O99", 5, "mgr")


class TestTransfer(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(REPS)
        self.opp = new_opp(self.crm, "corp@acme.com", 1000)

    def test_success(self):
        self.crm.transfer(self.opp, "rep2", "mgr")
        self.assertEqual(self.crm.opps[self.opp]["owner"], "rep2")
        self.assertEqual(self.crm.log[-1], ("transfer", self.opp, "mgr"))

    def test_actor_must_be_manager(self):
        for actor in ("rep1", "rep2"):
            with self.assertRaises(PermissionError):
                self.crm.transfer(self.opp, "rep2", actor)

    def test_manager_check_precedes_new_owner_validation(self):
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.opp, "ghost", "rep1")

    def test_new_owner_must_be_known_rep(self):
        for new_owner in ("ghost", "mgr", None, 7, ["rep2"]):
            before = snapshot(self.crm)
            with self.assertRaises(ValueError, msg=repr(new_owner)):
                self.crm.transfer(self.opp, new_owner, "mgr")
            self.assertEqual(snapshot(self.crm), before)

    def test_same_owner_rejected(self):
        owner = self.crm.opps[self.opp]["owner"]
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, owner, "mgr")

    def test_final_stage_rejected(self):
        walk(self.crm, self.opp, "won")
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "rep2", "mgr")

    def test_new_owner_needs_capacity(self):
        crm = CRM(
            [
                {"id": "a", "role": "rep", "capacity": 1},
                {"id": "b", "role": "rep", "capacity": 1},
                {"id": "mgr", "role": "manager", "capacity": 0},
            ]
        )
        first = new_lead(crm, "x@acme.com")
        crm.qualify(first, "mgr")
        opp = crm.convert(first, 10, "mgr")
        new_lead(crm, "y@acme.com")  # b is now full
        with self.assertRaises(ValueError):
            crm.transfer(opp, "b", "mgr")

    def test_frees_previous_owner_slot(self):
        crm = CRM(
            [
                {"id": "a", "role": "rep", "capacity": 1},
                {"id": "b", "role": "rep", "capacity": 0},
                {"id": "mgr", "role": "manager", "capacity": 0},
            ]
        )
        first = new_lead(crm, "x@acme.com")
        crm.qualify(first, "mgr")
        opp = crm.convert(first, 10, "mgr")
        queued = new_lead(crm, "y@acme.com")
        self.assertIsNone(crm.leads[queued]["owner"])
        # b had no capacity when the queue formed; it gains spare capacity
        # (a setup mutation, not a CRM operation) so the transfer can proceed.
        crm.users["b"]["capacity"] = 5
        crm.transfer(opp, "b", "mgr")
        self.assertEqual(crm.leads[queued]["owner"], "a")
        self.assertEqual(crm.log[-1], ("assign", queued, "system"))

    def test_unknown_opp(self):
        with self.assertRaises(ValueError):
            self.crm.transfer("O99", "rep2", "mgr")


class TestLoadAndForecast(unittest.TestCase):
    def test_load_counts_only_open_items(self):
        crm = CRM(
            [
                {"id": "r", "role": "rep", "capacity": 10},
                {"id": "mgr", "role": "manager", "capacity": 0},
            ]
        )
        a = new_lead(crm, "a@acme.com")
        new_lead(crm, "b@acme.com")
        crm.qualify(a, "mgr")
        opp = crm.convert(a, 100, "mgr")
        new_lead(crm, "c@acme.com")
        self.assertEqual(crm._load("r"), 3)  # two new leads + one open opp
        crm.advance(opp, "proposal", "mgr")
        self.assertEqual(crm._load("r"), 3)
        walk(crm, opp, "won")
        self.assertEqual(crm._load("r"), 2)

    def test_load_ignores_unchosen_reps(self):
        crm = CRM(REPS)
        self.assertEqual(crm._load("mgr"), 0)
        self.assertEqual(crm._load("rep2"), 0)
        new_lead(crm, "a@acme.com")
        self.assertEqual(crm._load("mgr"), 0)
        self.assertEqual(crm._load("rep2"), 0)

    def test_forecast_empty(self):
        self.assertEqual(CRM(REPS).forecast(), {"open": 0, "weighted": 0, "won": 0})

    def test_forecast(self):
        crm = CRM(REPS)
        p = new_opp(crm, "p@acme.com", 1000)
        q = new_opp(crm, "q@acme.com", 2000)
        w = new_opp(crm, "w@acme.com", 3333)
        lost = new_opp(crm, "l@acme.com", 700)
        n = new_opp(crm, "n@acme.com", 1001)
        walk(crm, q, "proposal")
        walk(crm, w, "won")
        walk(crm, lost, "lost")
        walk(crm, n, "negotiation")
        self.assertEqual(crm.opps[p]["stage"], "prospect")
        self.assertEqual(
            crm.forecast(),
            {
                "open": 3,
                "weighted": 1000 * 10 // 100 + 2000 * 30 // 100 + 1001 * 60 // 100,
                "won": 3333,
            },
        )

    def test_forecast_uses_current_amount(self):
        crm = CRM(REPS)
        opp = new_opp(crm, "x@acme.com", 1000)
        crm.discount(opp, 10, "mgr")
        walk(crm, opp, "won")
        self.assertEqual(crm.forecast(), {"open": 0, "weighted": 0, "won": 900})

    def test_forecast_does_not_log(self):
        crm = CRM(REPS)
        new_opp(crm, "x@acme.com", 1000)
        before = list(crm.log)
        crm.forecast()
        self.assertEqual(crm.log, before)


class TestAtomicity(unittest.TestCase):
    def test_failed_calls_leave_state_untouched(self):
        crm = CRM(REPS)
        lead = new_lead(crm, "a@acme.com")
        crm.qualify(lead, "mgr")
        opp = crm.convert(lead, 60000, "mgr")
        owner = crm.opps[opp]["owner"]
        other = "rep2" if owner == "rep1" else "rep1"
        before = snapshot(crm)
        bad = [
            lambda: crm.qualify(lead, "mgr"),
            lambda: crm.convert(lead, 10, "mgr"),
            lambda: crm.advance(opp, "won", "mgr"),
            lambda: crm.advance(opp, "proposal", other),
            lambda: crm.discount(opp, 0, owner),
            lambda: crm.transfer(opp, "rep2" if owner == "rep1" else "rep1", "rep1"),
        ]
        for call in bad:
            with self.assertRaises((ValueError, PermissionError)):
                call()
            self.assertEqual(snapshot(crm), before)

    def test_manager_never_owns_the_opportunity(self):
        crm = CRM(REPS)
        lead = new_lead(crm, "a@acme.com")
        crm.qualify(lead, "mgr")
        opp = crm.convert(lead, 100, "mgr")
        owner = crm.opps[opp]["owner"]
        self.assertIn(owner, ("rep1", "rep2"))
        with self.assertRaises(PermissionError):
            crm.advance(opp, "proposal", "rep2" if owner == "rep1" else "rep1")
        crm.advance(opp, "proposal", "mgr")
        self.assertEqual(crm.opps[opp]["stage"], "proposal")


if __name__ == "__main__":
    unittest.main()
