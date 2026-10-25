import unittest

from crm import CRM, DuplicateLeadError

REPS = [
    {"id": "r1", "role": "rep", "capacity": 2},
    {"id": "r2", "role": "rep", "capacity": 2},
    {"id": "m1", "role": "manager", "capacity": 0},
]


def make_crm():
    return CRM([dict(r) for r in REPS])


class TestAddLead(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()

    def test_creates_lead_with_normalized_email_and_score(self):
        lead_id = self.crm.add_lead("  Bob@Example.COM ", " Bob ", "referral", "m1")
        lead = self.crm.leads[lead_id]
        self.assertEqual(lead_id, "L1")
        self.assertEqual(lead["email"], "bob@example.com")
        self.assertEqual(lead["name"], "Bob")
        self.assertEqual(lead["score"], 45)  # 30 + 15 corporate domain
        self.assertEqual(lead["owner"], "r1")
        self.assertEqual(lead["status"], "new")
        self.assertEqual(self.crm.log, [("add_lead", "L1", "m1")])

    def test_free_mail_domain_has_no_bonus(self):
        lead_id = self.crm.add_lead("a@gmail.com", "A", "web", "m1")
        self.assertEqual(self.crm.leads[lead_id]["score"], 10)

    def test_unknown_actor_checked_before_other_validation(self):
        with self.assertRaises(PermissionError):
            self.crm.add_lead(123, "", "nope", "ghost")
        self.assertEqual(self.crm.leads, {})
        self.assertEqual(self.crm.log, [])

    def test_invalid_email_forms(self):
        for email in (None, "a", "a@@b.com", "@b.com", "a@b", "a@.com", "a@b."):
            with self.subTest(email=email):
                with self.assertRaises(ValueError):
                    self.crm.add_lead(email, "A", "web", "m1")

    def test_email_domain_dot_rules(self):
        self.assertEqual(self.crm.add_lead("a@b.c.d", "A", "web", "m1"), "L1")
        for email in ("a@b", "a@.com", "a@b."):
            with self.subTest(email=email):
                with self.assertRaises(ValueError):
                    self.crm.add_lead(email, "A", "web", "m1")

    def test_invalid_name_and_source(self):
        with self.assertRaises(ValueError):
            self.crm.add_lead("a@b.com", "   ", "web", "m1")
        with self.assertRaises(ValueError):
            self.crm.add_lead("a@b.com", "A", "cold-call", "m1")
        self.assertEqual(self.crm.leads, {})
        self.assertEqual(self.crm.log, [])

    def test_duplicate_email_reports_existing_id(self):
        self.crm.add_lead("a@b.com", "A", "web", "m1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            self.crm.add_lead(" A@B.com ", "B", "event", "m1")
        self.assertEqual(ctx.exception.existing_id, "L1")
        self.assertEqual(len(self.crm.leads), 1)
        self.assertEqual(len(self.crm.log), 1)

    def test_load_balancing_and_tie_break(self):
        self.assertEqual(self.crm.add_lead("a@b.com", "A", "web", "m1"), "L1")
        self.assertEqual(self.crm.add_lead("b@b.com", "B", "web", "m1"), "L2")
        self.assertEqual(self.crm.leads["L1"]["owner"], "r1")
        self.assertEqual(self.crm.leads["L2"]["owner"], "r2")
        self.crm.add_lead("c@b.com", "C", "web", "m1")
        self.crm.add_lead("d@b.com", "D", "web", "m1")
        self.crm.add_lead("e@b.com", "E", "web", "m1")
        self.assertEqual(self.crm.leads["L5"]["owner"], None)
        self.assertEqual(len(self.crm.log), 5)

    def test_sequence_numbers_do_not_skip_on_failure(self):
        self.crm.add_lead("a@b.com", "A", "web", "m1")
        with self.assertRaises(ValueError):
            self.crm.add_lead("bad", "B", "web", "m1")
        self.assertEqual(self.crm.add_lead("b@b.com", "B", "web", "m1"), "L2")

    def test_waiting_queue_forms_when_both_reps_are_full(self):
        self.crm.add_lead("a@b.com", "A", "web", "m1")
        self.crm.add_lead("b@b.com", "B", "web", "m1")
        self.crm.add_lead("c@b.com", "C", "web", "m1")
        self.crm.add_lead("d@b.com", "D", "web", "m1")
        self.assertEqual(self.crm.leads["L3"]["owner"], "r1")
        self.assertEqual(self.crm.leads["L4"]["owner"], "r2")
        self.crm.add_lead("e@b.com", "E", "web", "m1")
        self.crm.add_lead("f@b.com", "F", "web", "m1")
        self.assertEqual(self.crm.leads["L5"]["owner"], None)
        self.assertEqual(self.crm.leads["L6"]["owner"], None)
        self.assertEqual(self.crm.leads["L1"]["owner"], "r1")


class TestQualify(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        self.lead_id = self.crm.add_lead("a@corp.com", "A", "referral", "m1")
        self.crm.log.clear()

    def test_only_owner_or_manager_may_qualify(self):
        with self.assertRaises(PermissionError):
            self.crm.qualify(self.lead_id, "r2")
        self.assertEqual(self.crm.leads[self.lead_id]["status"], "new")
        self.assertEqual(self.crm.log, [])

    def test_qualify_by_owner(self):
        self.crm.qualify(self.lead_id, "r1")
        self.assertEqual(self.crm.leads[self.lead_id]["status"], "qualified")
        self.assertEqual(self.crm.log, [("qualify", self.lead_id, "r1")])

    def test_unknown_lead_and_unknown_actor(self):
        with self.assertRaises(ValueError):
            self.crm.qualify("nope", "m1")
        with self.assertRaises(PermissionError):
            self.crm.qualify(self.lead_id, "ghost")

    def test_requires_new_status_and_rejects_low_score(self):
        low = self.crm.add_lead("b@gmail.com", "B", "web", "m1")
        with self.assertRaises(ValueError):
            self.crm.qualify(low, "r2")
        self.crm.qualify(self.lead_id, "r1")
        with self.assertRaises(ValueError):
            self.crm.qualify(self.lead_id, "r1")


class TestConvert(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        self.lead_id = self.crm.add_lead("a@corp.com", "A", "referral", "m1")
        self.crm.qualify(self.lead_id, "r1")
        self.crm.log.clear()

    def test_conversion_creates_opportunity(self):
        opp_id = self.crm.convert(self.lead_id, 1000, "r1")
        opp = self.crm.opps[opp_id]
        self.assertEqual(opp_id, "O1")
        self.assertEqual(
            opp,
            {
                "id": "O1",
                "lead_id": self.lead_id,
                "owner": "r1",
                "amount": 1000,
                "original_amount": 1000,
                "stage": "prospect",
            },
        )
        self.assertEqual(self.crm.leads[self.lead_id]["status"], "converted")
        self.assertEqual(self.crm.log, [("convert", "O1", "r1")])

    def test_amount_validation_rejects_bool_and_non_positive(self):
        for amount in (0, -5, True, 10.5, "10"):
            with self.subTest(amount=amount):
                with self.assertRaises(ValueError):
                    self.crm.convert(self.lead_id, amount, "r1")
        self.assertEqual(self.crm.opps, {})
        self.assertEqual(self.crm.log, [])

    def test_permission_checked_before_stage_and_amount_created_nothing(self):
        with self.assertRaises(PermissionError):
            self.crm.convert(self.lead_id, 100, "r2")
        self.assertEqual(self.crm.opps, {})

    def test_requires_qualified_and_owner(self):
        fresh = self.crm.add_lead("b@corp.com", "B", "referral", "m1")
        with self.assertRaises(ValueError):
            self.crm.convert(fresh, 100, "r2")
        self.crm.convert(self.lead_id, 100, "r1")
        with self.assertRaises(ValueError):
            self.crm.convert(self.lead_id, 100, "r1")


class TestAdvance(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        lead = self.crm.add_lead("a@corp.com", "A", "referral", "m1")
        self.crm.qualify(lead, "r1")
        self.opp = self.crm.convert(lead, 1000, "r1")
        self.crm.log.clear()

    def test_stage_must_be_known_and_sequential(self):
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "bogus", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "won", "r1")
        self.crm.advance(self.opp, "proposal", "r1")
        self.assertEqual(self.crm.opps[self.opp]["stage"], "proposal")
        self.assertEqual(self.crm.log, [("advance", self.opp, "r1")])

    def test_owner_or_manager_only(self):
        with self.assertRaises(PermissionError):
            self.crm.advance(self.opp, "proposal", "r2")
        self.assertEqual(self.crm.opps[self.opp]["stage"], "prospect")

    def test_final_stage_is_terminal(self):
        self.crm.advance(self.opp, "lost", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "won", "r1")

    def test_large_negotiation_requires_manager(self):
        big_lead = self.crm.add_lead("big@corp.com", "Big", "referral", "m1")
        self.crm.qualify(big_lead, "r2")
        big = self.crm.convert(big_lead, 60000, "r2")
        self.crm.advance(big, "proposal", "r2")
        with self.assertRaises(PermissionError):
            self.crm.advance(big, "negotiation", "r2")
        self.assertEqual(self.crm.opps[big]["stage"], "proposal")
        self.crm.advance(big, "negotiation", "m1")
        self.assertEqual(self.crm.opps[big]["stage"], "negotiation")

    def test_small_negotiation_allowed_for_rep(self):
        lead = self.crm.add_lead("b@corp.com", "B", "referral", "m1")
        self.crm.qualify(lead, "r2")
        opp = self.crm.convert(lead, 50000, "r2")
        self.crm.advance(opp, "proposal", "r2")
        self.crm.advance(opp, "negotiation", "r2")
        self.assertEqual(self.crm.opps[opp]["stage"], "negotiation")

    def test_win_frees_slot_and_assigns_waiting_leads(self):
        # r1 holds the open opp plus one lead; r2 holds two leads. Two leads queue.
        self.crm.add_lead("b@corp.com", "B", "web", "m1")   # L2 -> r2
        self.crm.add_lead("c@corp.com", "C", "web", "m1")   # L3 -> r1
        self.crm.add_lead("d@corp.com", "D", "web", "m1")   # L4 -> r2
        self.crm.add_lead("e@corp.com", "E", "web", "m1")   # L5 -> waiting
        waiting = [lid for lid, l in self.crm.leads.items() if l["owner"] is None]
        self.assertEqual(waiting, ["L5"])

        self.crm.advance(self.opp, "proposal", "r1")
        self.crm.advance(self.opp, "negotiation", "r1")
        self.crm.advance(self.opp, "won", "r1")
        self.assertEqual(self.crm.leads[waiting[0]]["owner"], "r1")
        self.assertEqual(self.crm.log[-2:], [
            ("advance", self.opp, "r1"),
            ("assign", waiting[0], "system"),
        ])


class TestDiscount(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        lead = self.crm.add_lead("a@corp.com", "A", "referral", "m1")
        self.crm.qualify(lead, "r1")
        self.opp = self.crm.convert(lead, 1000, "r1")
        self.crm.log.clear()

    def test_rep_may_discount_up_to_10(self):
        self.crm.discount(self.opp, 10, "r1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 900)
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp, 11, "r1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 900)
        self.assertEqual(self.crm.log, [("discount", self.opp, "r1")])

    def test_pct_validation(self):
        for pct in (0, 31, True, 5.0, "5"):
            with self.subTest(pct=pct):
                with self.assertRaises(ValueError):
                    self.crm.discount(self.opp, pct, "m1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 1000)

    def test_cumulative_discount_cap(self):
        self.crm.discount(self.opp, 30, "m1")  # 700, exactly 70%
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp, 1, "m1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 700)

    def test_final_stage_cannot_be_discounted(self):
        self.crm.advance(self.opp, "lost", "r1")
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp, 5, "m1")


class TestTransfer(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        lead = self.crm.add_lead("a@corp.com", "A", "referral", "m1")
        self.crm.qualify(lead, "r1")
        self.opp = self.crm.convert(lead, 1000, "r1")
        self.crm.log.clear()

    def test_manager_transfers_and_releases_previous_owner(self):
        self.crm.transfer(self.opp, "r2", "m1")
        self.assertEqual(self.crm.opps[self.opp]["owner"], "r2")
        self.assertEqual(self.crm.log, [("transfer", self.opp, "m1")])
        # r1 no longer carries the open opp, so it is first to receive new work.
        lead = self.crm.add_lead("b@corp.com", "B", "web", "m1")
        self.assertEqual(self.crm.leads[lead]["owner"], "r1")

    def test_only_manager_may_transfer(self):
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.opp, "r2", "r1")

    def test_new_owner_must_be_a_rep(self):
        for target in ("m1", "ghost"):
            with self.subTest(target=target):
                with self.assertRaises(ValueError):
                    self.crm.transfer(self.opp, target, "m1")

    def test_new_owner_must_differ_and_have_capacity(self):
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "r1", "m1")
        self.crm.add_lead("b@corp.com", "B", "web", "m1")
        self.crm.add_lead("c@corp.com", "C", "web", "m1")
        self.crm.add_lead("d@corp.com", "D", "web", "m1")
        self.crm.add_lead("e@corp.com", "E", "web", "m1")
        # r2 now owns two leads at capacity 2.
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "r2", "m1")
        self.assertEqual(self.crm.opps[self.opp]["owner"], "r1")


class TestForecastAndAtomicity(unittest.TestCase):
    def test_forecast(self):
        crm = make_crm()
        one = crm.add_lead("a@corp.com", "A", "referral", "m1")
        two = crm.add_lead("b@corp.com", "B", "referral", "m1")
        three = crm.add_lead("c@corp.com", "C", "referral", "m1")
        for lead in (one, two, three):
            crm.qualify(lead, "m1")
        o1 = crm.convert(one, 1000, "m1")
        o2 = crm.convert(two, 2000, "m1")
        o3 = crm.convert(three, 4000, "m1")
        crm.advance(o1, "proposal", "m1")
        crm.advance(o2, "proposal", "m1")
        crm.advance(o2, "negotiation", "m1")
        crm.advance(o2, "won", "m1")
        crm.advance(o3, "lost", "m1")
        self.assertEqual(
            crm.forecast(), {"open": 1, "weighted": 300, "won": 2000}
        )

    def test_forecast_has_no_log_entry(self):
        crm = make_crm()
        before = list(crm.log)
        crm.forecast()
        self.assertEqual(crm.log, before)

    def test_failed_calls_are_atomic(self):
        crm = make_crm()
        lead = crm.add_lead("a@corp.com", "A", "referral", "m1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 1000, "r1")
        snapshot = (
            {k: dict(v) for k, v in crm.leads.items()},
            {k: dict(v) for k, v in crm.opps.items()},
            list(crm.log),
        )
        with self.assertRaises(ValueError):
            crm.advance(opp, "won", "r1")
        with self.assertRaises(PermissionError):
            crm.discount(opp, 5, "r2")
        with self.assertRaises(ValueError):
            crm.transfer(opp, "r1", "m1")
        self.assertEqual(
            ({k: dict(v) for k, v in crm.leads.items()},
             {k: dict(v) for k, v in crm.opps.items()},
             list(crm.log)),
            snapshot,
        )


# ---------------------------------------------------------------------------
# Guards added for the AE-pressure-3 audit. Each test names the spec clause it
# observes, so a failure points at the rule rather than at a fixture.
# ---------------------------------------------------------------------------

BIG_REPS = [
    {"id": "r1", "role": "rep", "capacity": 10},
    {"id": "m1", "role": "manager", "capacity": 0},
]


def make_big_crm():
    return CRM([dict(r) for r in BIG_REPS])


def add_referral_lead(crm, local, actor="r1"):
    """Add, qualify and convert a referral lead (score 30, 'qualified' ready)."""
    lead_id = crm.add_lead("%s@corp.com" % local, local, "referral", actor)
    crm.qualify(lead_id, actor)
    return lead_id


def add_opp(crm, local, amount, actor="r1"):
    lead_id = add_referral_lead(crm, local, actor)
    return crm.convert(lead_id, amount, actor)


def queued_ids(crm):
    return [lid for lid, lead in crm.leads.items() if lead["owner"] is None]


def full_board():
    """r1 and r2 each at capacity 2: r1 holds an open opp plus a lead."""
    crm = make_crm()
    lead = crm.add_lead("a@corp.com", "A", "referral", "m1")  # L1 -> r1
    crm.qualify(lead, "r1")
    opp = crm.convert(lead, 1000, "r1")  # r1 load 1 (open opp)
    crm.add_lead("b@corp.com", "B", "web", "m1")  # L2 -> r2
    crm.add_lead("c@corp.com", "C", "web", "m1")  # L3 -> r1
    crm.add_lead("d@corp.com", "D", "web", "m1")  # L4 -> r2
    return crm, opp


class TestOwnerSelectionGuards(unittest.TestCase):
    def test_manager_with_spare_capacity_never_owns_work(self):
        # "Only role 'rep' users receive work; managers never own anything."
        # The manager here has capacity to spare, so only the role filter can
        # keep the lead out of its hands.
        crm = CRM(
            [
                {"id": "m1", "role": "manager", "capacity": 5},
                {"id": "r1", "role": "rep", "capacity": 1},
            ]
        )
        first = crm.add_lead("a@corp.com", "A", "web", "m1")
        self.assertEqual(crm.leads[first]["owner"], "r1")
        second = crm.add_lead("b@corp.com", "B", "web", "m1")
        self.assertIsNone(crm.leads[second]["owner"])
        self.assertEqual(queued_ids(crm), [second])

    def test_tie_break_is_smallest_id_in_string_order(self):
        # "ties: smallest id in string order" — declaration order is r2, r1,
        # r10, so insertion order cannot be what decides.
        crm = CRM(
            [
                {"id": "r2", "role": "rep", "capacity": 5},
                {"id": "r1", "role": "rep", "capacity": 5},
                {"id": "r10", "role": "rep", "capacity": 5},
            ]
        )
        first = crm.add_lead("a@corp.com", "A", "web", "r1")
        second = crm.add_lead("b@corp.com", "B", "web", "r1")
        third = crm.add_lead("c@corp.com", "C", "web", "r1")
        self.assertEqual(crm.leads[first]["owner"], "r1")
        self.assertEqual(crm.leads[second]["owner"], "r10")  # "r10" < "r2"
        self.assertEqual(crm.leads[third]["owner"], "r2")


class TestSlotReleaseGuards(unittest.TestCase):
    def test_lost_also_frees_the_slot_and_assigns_the_queue(self):
        # "If the new stage is 'won' or 'lost', the owner's slot is freed..."
        crm, opp = full_board()
        older = crm.add_lead("e@corp.com", "E", "web", "m1")
        newer = crm.add_lead("f@corp.com", "F", "web", "m1")
        self.assertEqual(queued_ids(crm), [older, newer])

        crm.advance(opp, "lost", "r1")

        self.assertEqual(crm.leads[older]["owner"], "r1")
        self.assertIsNone(crm.leads[newer]["owner"])
        self.assertEqual(
            [entry for entry in crm.log if entry[0] == "assign"],
            [("assign", older, "system")],
        )
        self.assertEqual(crm.log[-2:], [("advance", opp, "r1"), ("assign", older, "system")])

    def test_assignment_is_fifo_and_respects_capacity(self):
        # "take the oldest waiting lead" and "while the owner's load is below
        # its capacity" — one freed slot, two queued leads.
        crm, opp = full_board()
        older = crm.add_lead("e@corp.com", "E", "web", "m1")
        newer = crm.add_lead("f@corp.com", "F", "web", "m1")

        crm.advance(opp, "proposal", "r1")
        crm.advance(opp, "negotiation", "r1")
        crm.advance(opp, "won", "r1")

        self.assertEqual(crm.leads[older]["owner"], "r1")
        self.assertIsNone(crm.leads[newer]["owner"])
        self.assertEqual(len([e for e in crm.log if e[0] == "assign"]), 1)


class TestQualifyThreshold(unittest.TestCase):
    def test_score_of_exactly_30_qualifies(self):
        # "score must be at least 30" — referral + free-mail domain == 30.
        crm = make_crm()
        lead_id = crm.add_lead("a@gmail.com", "A", "referral", "m1")
        self.assertEqual(crm.leads[lead_id]["score"], 30)
        crm.qualify(lead_id, "r1")
        self.assertEqual(crm.leads[lead_id]["status"], "qualified")

    def test_failed_qualify_leaves_the_lead_untouched(self):
        # "A failed call (any exception) changes nothing..."
        crm = make_crm()
        lead_id = crm.add_lead("a@gmail.com", "A", "web", "m1")  # score 10
        self.assertEqual(crm.leads[lead_id]["status"], "new")
        with self.assertRaises(ValueError):
            crm.qualify(lead_id, "r1")
        self.assertEqual(crm.leads[lead_id]["status"], "new")
        self.assertEqual(crm.log, [("add_lead", lead_id, "m1")])


class TestCheckOrdering(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        self.lead = self.crm.add_lead("a@corp.com", "A", "referral", "m1")
        self.crm.qualify(self.lead, "r1")
        self.opp = self.crm.convert(self.lead, 1000, "r1")
        self.crm.log.clear()

    def test_add_lead_checks_name_and_source_before_duplicate(self):
        # Steps 2, 3, 4: an existing email does not short-circuit the earlier
        # validation guards.
        with self.assertRaises(ValueError):
            self.crm.add_lead(" A@CORP.com ", "   ", "web", "m1")
        with self.assertRaises(ValueError):
            self.crm.add_lead(" A@CORP.com ", "A", "cold-call", "m1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            self.crm.add_lead(" A@CORP.com ", "A", "web", "m1")
        self.assertEqual(ctx.exception.existing_id, self.lead)

    def test_advance_permission_checked_before_transition_legality(self):
        # Steps 3 and 5: non-owner with an illegal jump still gets PermissionError.
        with self.assertRaises(PermissionError):
            self.crm.advance(self.opp, "won", "r2")
        self.assertEqual(self.crm.opps[self.opp]["stage"], "prospect")

    def test_advance_stage_enum_checked_before_permission(self):
        # Steps 2 and 3: a bogus stage from a non-owner is a ValueError.
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "bogus", "r2")

    def test_transfer_manager_check_before_new_owner_validity(self):
        # Steps 2 and 3: invalid new_owner plus a non-manager actor is a
        # PermissionError, not a ValueError.
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.opp, 123, "r1")
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.opp, "ghost", "r1")

    def test_discount_final_stage_checked_before_rep_cap(self):
        # Steps 4 and 5: final stage wins over the 10 % non-manager cap.
        self.crm.advance(self.opp, "lost", "r1")
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp, 11, "r1")

    def test_unknown_actor_guard_in_every_remaining_method(self):
        # "If actor is not the id of a known user, raise PermissionError. This
        # is checked first in every method."
        with self.assertRaises(PermissionError):
            self.crm.convert(self.lead, 100, "ghost")
        with self.assertRaises(PermissionError):
            self.crm.advance(self.opp, "proposal", "ghost")
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp, 5, "ghost")
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.opp, "r2", "ghost")

    def test_unknown_actor_guard_precedes_later_validation(self):
        # Pairing the unknown actor with an argument the next check would reject
        # makes the ordering observable: drop the guard and these become
        # ValueError. The otherwise-valid calls above cannot show it, because
        # the owner check raises the same PermissionError.
        with self.assertRaises(PermissionError):
            self.crm.convert(self.lead, 0, "ghost")  # amount would be ValueError
        with self.assertRaises(PermissionError):
            self.crm.advance(self.opp, "bogus", "ghost")  # stage would be ValueError
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp, 0, "ghost")  # pct would be ValueError


class TestIdSequencing(unittest.TestCase):
    def test_failed_convert_does_not_consume_an_id(self):
        # "O<n> where n counts successful conversions" — not attempts.
        crm = make_crm()
        lead_id = add_referral_lead(crm, "a")
        with self.assertRaises(ValueError):
            crm.convert(lead_id, 0, "r1")
        self.assertEqual(crm.convert(lead_id, 500, "r1"), "O1")

    def test_failed_add_lead_does_not_consume_an_id(self):
        crm = make_crm()
        crm.add_lead("a@corp.com", "A", "web", "m1")
        with self.assertRaises(DuplicateLeadError):
            crm.add_lead("a@corp.com", "B", "web", "m1")
        self.assertEqual(crm.add_lead("b@corp.com", "B", "web", "m1"), "L2")


class TestForecastWeights(unittest.TestCase):
    def test_prospect_proposal_and_negotiation_weights(self):
        # w = 10 / 30 / 60.
        crm = make_big_crm()
        p1 = add_opp(crm, "p1", 1000)  # prospect -> 100
        p2 = add_opp(crm, "p2", 2000)  # proposal -> 600
        p3 = add_opp(crm, "p3", 4000)  # negotiation -> 2400
        crm.advance(p2, "proposal", "r1")
        crm.advance(p3, "proposal", "r1")
        crm.advance(p3, "negotiation", "r1")
        self.assertEqual(
            crm.forecast(), {"open": 3, "weighted": 100 + 600 + 2400, "won": 0}
        )

    def test_weighted_is_floored_per_opportunity(self):
        # "sum over open opportunities of amount * w // 100": 33 + 99 == 132,
        # whereas flooring the sum would give 133.
        crm = make_big_crm()
        add_opp(crm, "p1", 333)
        add_opp(crm, "p2", 999)
        self.assertEqual(crm.forecast(), {"open": 2, "weighted": 132, "won": 0})

    def test_won_uses_the_current_discounted_amount(self):
        # "'won': sum of amount" — amount, not original_amount.
        crm = make_big_crm()
        opp = add_opp(crm, "p1", 1000)
        crm.discount(opp, 30, "m1")
        crm.advance(opp, "proposal", "r1")
        crm.advance(opp, "negotiation", "r1")
        crm.advance(opp, "won", "r1")
        self.assertEqual(crm.forecast(), {"open": 0, "weighted": 0, "won": 700})


class TestAtomicityGuards(unittest.TestCase):
    def snapshot(self, crm):
        return (
            {k: dict(v) for k, v in crm.leads.items()},
            {k: dict(v) for k, v in crm.opps.items()},
            list(crm.log),
            queued_ids(crm),
        )

    def test_add_lead_failure_changes_nothing(self):
        crm = make_crm()
        crm.add_lead("a@corp.com", "A", "web", "m1")
        before = self.snapshot(crm)
        with self.assertRaises(ValueError):
            crm.add_lead("bad", "B", "web", "m1")
        with self.assertRaises(DuplicateLeadError):
            crm.add_lead("a@corp.com", "B", "web", "m1")
        self.assertEqual(self.snapshot(crm), before)

    def test_qualify_and_convert_failures_change_nothing(self):
        crm = make_crm()
        lead_id = crm.add_lead("a@corp.com", "A", "web", "m1")  # score 10
        before = self.snapshot(crm)
        with self.assertRaises(ValueError):
            crm.qualify(lead_id, "r1")
        with self.assertRaises(ValueError):
            crm.convert(lead_id, 100, "r1")
        self.assertEqual(self.snapshot(crm), before)

    def test_advance_discount_transfer_failures_change_nothing(self):
        crm = make_crm()
        lead_id = add_referral_lead(crm, "a")
        opp = crm.convert(lead_id, 1000, "r1")
        before = self.snapshot(crm)
        with self.assertRaises(ValueError):
            crm.advance(opp, "won", "r1")
        with self.assertRaises(PermissionError):
            crm.discount(opp, 5, "r2")
        with self.assertRaises(ValueError):
            crm.transfer(opp, "r1", "m1")
        self.assertEqual(self.snapshot(crm), before)


if __name__ == "__main__":
    unittest.main()
