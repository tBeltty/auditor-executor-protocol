import unittest

from crm import CRM, DuplicateLeadError


REPS = [
    {"id": "r1", "role": "rep", "capacity": 3},
    {"id": "r2", "role": "rep", "capacity": 3},
    {"id": "m1", "role": "manager", "capacity": 0},
]


def make_crm(reps=None):
    return CRM([dict(r) for r in (reps if reps is not None else REPS)])


class TestConstruction(unittest.TestCase):
    def test_attributes(self):
        crm = make_crm()
        self.assertEqual(crm.leads, {})
        self.assertEqual(crm.opps, {})
        self.assertEqual(crm.log, [])

    def test_duplicate_lead_error_attribute(self):
        err = DuplicateLeadError("L7")
        self.assertEqual(err.existing_id, "L7")

    def test_duplicate_lead_error_is_exception(self):
        self.assertTrue(issubclass(DuplicateLeadError, Exception))


class TestActorCheck(unittest.TestCase):
    def test_unknown_actor_everywhere(self):
        crm = make_crm()
        lead_id = crm.add_lead("a@b.com", "A", "referral", "r1")
        crm.qualify(lead_id, "r1")
        opp_id = crm.convert(lead_id, 100, "r1")
        crm.log = []
        self.assertRaises(PermissionError, crm.add_lead, "x@y.com", "X", "web", "zz")
        self.assertRaises(PermissionError, crm.qualify, lead_id, "zz")
        self.assertRaises(PermissionError, crm.convert, lead_id, 100, "zz")
        self.assertRaises(PermissionError, crm.advance, opp_id, "proposal", "zz")
        self.assertRaises(PermissionError, crm.discount, opp_id, 5, "zz")
        self.assertRaises(PermissionError, crm.transfer, opp_id, "r2", "zz")
        self.assertEqual(crm.log, [])

    def test_actor_checked_before_entity(self):
        crm = make_crm()
        self.assertRaises(PermissionError, crm.qualify, "L999", "nobody")
        self.assertRaises(PermissionError, crm.advance, "O999", "proposal", "nobody")
        self.assertRaises(PermissionError, crm.transfer, "O999", "r2", "nobody")

    def test_non_string_actor(self):
        crm = make_crm()
        self.assertRaises(PermissionError, crm.add_lead, "a@b.com", "A", "web", None)


class TestAddLeadValidation(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()

    def test_bad_email_type(self):
        for bad in (None, 5, [], b"a@b.com"):
            self.assertRaises(ValueError, self.crm.add_lead, bad, "A", "web", "r1")

    def test_bad_email_shapes(self):
        bad = [
            "ab.com",
            "a@@b.com",
            "a@b@c.com",
            "@b.com",
            "   @b.com",
            "a@com",
            "a@.com",
            "a@com.",
            "a@b.",
            "",
        ]
        for email in bad:
            self.assertRaises(ValueError, self.crm.add_lead, email, "A", "web", "r1")
        self.assertEqual(self.crm.leads, {})

    def test_bad_name(self):
        for bad in (None, 5, "", "   "):
            self.assertRaises(ValueError, self.crm.add_lead, "a@b.com", bad, "web", "r1")

    def test_bad_source(self):
        self.assertRaises(ValueError, self.crm.add_lead, "a@b.com", "A", "ads", "r1")
        self.assertRaises(ValueError, self.crm.add_lead, "a@b.com", "A", "WEB", "r1")

    def test_normalization(self):
        lead_id = self.crm.add_lead("  Alice@Example.COM ", "  Alice  ", "referral", "r1")
        lead = self.crm.leads[lead_id]
        self.assertEqual(lead["email"], "alice@example.com")
        self.assertEqual(lead["name"], "Alice")

    def test_lead_shape(self):
        lead_id = self.crm.add_lead("a@example.com", "A", "web", "r1")
        self.assertEqual(lead_id, "L1")
        self.assertEqual(
            self.crm.leads[lead_id],
            {
                "id": "L1",
                "email": "a@example.com",
                "name": "A",
                "source": "web",
                "score": 25,
                "owner": "r1",
                "status": "new",
            },
        )
        self.assertEqual(self.crm.log, [("add_lead", "L1", "r1")])

    def test_ids_increment_on_success_only(self):
        self.assertEqual(self.crm.add_lead("a@example.com", "A", "web", "r1"), "L1")
        with self.assertRaises(DuplicateLeadError):
            self.crm.add_lead("A@EXAMPLE.com", "B", "web", "r1")
        self.assertEqual(self.crm.add_lead("b@example.com", "B", "web", "r1"), "L2")


class TestScoring(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()

    def score(self, email, source):
        return self.crm.leads[self.crm.add_lead(email, "N", source, "r1")]["score"]

    def test_free_domains(self):
        for i, domain in enumerate(("gmail.com", "yahoo.com", "outlook.com")):
            self.assertEqual(self.score("u%d@%s" % (i, domain), "web"), 10)
            self.assertEqual(self.score("v%d@%s" % (i, domain), "referral"), 30)
            self.assertEqual(self.score("w%d@%s" % (i, domain), "event"), 20)

    def test_business_domain_bonus(self):
        self.assertEqual(self.score("a@acme.io", "web"), 25)
        self.assertEqual(self.score("b@acme.io", "referral"), 45)
        self.assertEqual(self.score("c@acme.io", "event"), 35)

    def test_bonus_is_domain_exact(self):
        self.assertEqual(self.score("a@gmail.com.evil.com", "web"), 25)
        self.assertEqual(self.score("b@notgmail.com", "web"), 25)


class TestDuplicates(unittest.TestCase):
    def test_duplicate_detection_normalized(self):
        crm = make_crm()
        lead_id = crm.add_lead("Dup@Example.com", "A", "web", "r1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            crm.add_lead("  dup@example.COM  ", "B", "event", "r1")
        self.assertEqual(ctx.exception.existing_id, lead_id)
        self.assertEqual(len(crm.leads), 1)
        self.assertEqual(len(crm.log), 1)

    def test_different_emails_allowed(self):
        crm = make_crm()
        crm.add_lead("a@example.com", "A", "web", "r1")
        crm.add_lead("b@example.com", "B", "web", "r1")
        self.assertEqual(len(crm.leads), 2)


class TestAssignment(unittest.TestCase):
    def test_lowest_load_wins(self):
        reps = [
            {"id": "ra", "role": "rep", "capacity": 5},
            {"id": "rb", "role": "rep", "capacity": 5},
        ]
        crm = make_crm(reps)
        self.assertEqual(crm.leads[crm.add_lead("a@x.com", "A", "web", "ra")]["owner"], "ra")
        self.assertEqual(crm.leads[crm.add_lead("b@x.com", "B", "web", "ra")]["owner"], "rb")
        self.assertEqual(crm.leads[crm.add_lead("c@x.com", "C", "web", "ra")]["owner"], "ra")

    def test_tie_break_smallest_id(self):
        reps = [
            {"id": "r2", "role": "rep", "capacity": 5},
            {"id": "r1", "role": "rep", "capacity": 5},
        ]
        crm = make_crm(reps)
        self.assertEqual(crm.leads[crm.add_lead("a@x.com", "A", "web", "r1")]["owner"], "r1")

    def test_managers_never_own(self):
        reps = [{"id": "m1", "role": "manager", "capacity": 10}]
        crm = make_crm(reps)
        lead_id = crm.add_lead("a@x.com", "A", "web", "m1")
        self.assertIsNone(crm.leads[lead_id]["owner"])

    def test_waiting_queue_when_full(self):
        reps = [{"id": "r1", "role": "rep", "capacity": 1}]
        crm = make_crm(reps)
        first = crm.add_lead("a@x.com", "A", "web", "r1")
        second = crm.add_lead("b@x.com", "B", "web", "r1")
        self.assertEqual(crm.leads[first]["owner"], "r1")
        self.assertIsNone(crm.leads[second]["owner"])
        self.assertEqual(crm.waiting, [second])

    def test_load_counts_only_open_leads_and_opps(self):
        reps = [{"id": "r1", "role": "rep", "capacity": 3}]
        crm = make_crm(reps)
        lead_id = crm.add_lead("a@x.com", "A", "referral", "r1")
        self.assertEqual(crm._load("r1"), 1)
        crm.qualify(lead_id, "r1")
        self.assertEqual(crm._load("r1"), 1)
        crm.convert(lead_id, 100, "r1")
        self.assertEqual(crm._load("r1"), 1)
        opp_id = "O1"
        crm.advance(opp_id, "lost", "r1")
        self.assertEqual(crm._load("r1"), 0)


class TestQualify(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()

    def test_qualify_ok(self):
        lead_id = self.crm.add_lead("a@example.com", "A", "referral", "r1")
        self.assertIsNone(self.crm.qualify(lead_id, "r1"))
        self.assertEqual(self.crm.leads[lead_id]["status"], "qualified")
        self.assertEqual(self.crm.log[-1], ("qualify", lead_id, "r1"))

    def test_unknown_lead(self):
        self.assertRaises(ValueError, self.crm.qualify, "L404", "r1")

    def test_manager_may_qualify_others(self):
        lead_id = self.crm.add_lead("a@example.com", "A", "referral", "r2")
        self.crm.qualify(lead_id, "m1")
        self.assertEqual(self.crm.leads[lead_id]["status"], "qualified")

    def test_permission(self):
        lead_id = self.crm.add_lead("a@example.com", "A", "referral", "r1")
        self.assertRaises(PermissionError, self.crm.qualify, lead_id, "r2")

    def test_status_check(self):
        lead_id = self.crm.add_lead("a@example.com", "A", "referral", "r1")
        self.crm.qualify(lead_id, "r1")
        self.assertRaises(ValueError, self.crm.qualify, lead_id, "r1")

    def test_score_check(self):
        lead_id = self.crm.add_lead("a@gmail.com", "A", "web", "r1")
        self.assertEqual(self.crm.leads[lead_id]["score"], 10)
        self.assertRaises(ValueError, self.crm.qualify, lead_id, "r1")
        self.assertEqual(self.crm.leads[lead_id]["status"], "new")

    def test_permission_before_status(self):
        lead_id = self.crm.add_lead("a@example.com", "A", "web", "r1")
        self.assertRaises(PermissionError, self.crm.qualify, lead_id, "r2")


class TestConvert(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        self.lead_id = self.crm.add_lead("a@example.com", "A", "referral", "r1")
        self.crm.qualify(self.lead_id, "r1")

    def test_convert_ok(self):
        opp_id = self.crm.convert(self.lead_id, 1000, "r1")
        self.assertEqual(opp_id, "O1")
        self.assertEqual(
            self.crm.opps[opp_id],
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
        self.assertEqual(self.crm.log[-1], ("convert", "O1", "r1"))

    def test_bad_amount(self):
        for bad in (0, -5, True, False, 1.5, "100", None):
            self.assertRaises(ValueError, self.crm.convert, self.lead_id, bad, "r1")
        self.assertEqual(self.crm.opps, {})

    def test_amount_checked_before_permission(self):
        self.assertRaises(ValueError, self.crm.convert, self.lead_id, 0, "r2")

    def test_unknown_lead(self):
        self.assertRaises(ValueError, self.crm.convert, "L404", 100, "r1")

    def test_permission(self):
        self.assertRaises(PermissionError, self.crm.convert, self.lead_id, 100, "r2")

    def test_manager_may_convert(self):
        self.assertEqual(self.crm.convert(self.lead_id, 100, "m1"), "O1")

    def test_requires_qualified(self):
        lead_id = self.crm.add_lead("b@example.com", "B", "referral", "r2")
        self.assertRaises(ValueError, self.crm.convert, lead_id, 100, "r2")

    def test_requires_owner(self):
        reps = [
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 0},
        ]
        crm = make_crm(reps)
        lead_id = crm.add_lead("a@example.com", "A", "referral", "r1")
        waiting = crm.add_lead("b@example.com", "B", "referral", "r1")
        self.assertIsNone(crm.leads[waiting]["owner"])
        crm.qualify(waiting, "m1")
        self.assertEqual(crm.leads[waiting]["status"], "qualified")
        self.assertRaises(ValueError, crm.convert, waiting, 100, "m1")
        self.assertEqual(crm.opps, {})

    def test_ids_increment_on_success(self):
        opp1 = self.crm.convert(self.lead_id, 100, "r1")
        lead2 = self.crm.add_lead("b@example.com", "B", "referral", "r2")
        self.crm.qualify(lead2, "r2")
        opp2 = self.crm.convert(lead2, 200, "r2")
        self.assertEqual((opp1, opp2), ("O1", "O2"))


class TestAdvance(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        lead_id = self.crm.add_lead("a@example.com", "A", "referral", "r1")
        self.crm.qualify(lead_id, "r1")
        self.opp_id = self.crm.convert(lead_id, 1000, "r1")

    def test_happy_path(self):
        stages = ["proposal", "negotiation", "won"]
        for stage in stages:
            self.crm.advance(self.opp_id, stage, "r1")
            self.assertEqual(self.crm.opps[self.opp_id]["stage"], stage)
            self.assertEqual(self.crm.log[-1], ("advance", self.opp_id, "r1"))

    def test_unknown_opp(self):
        self.assertRaises(ValueError, self.crm.advance, "O404", "proposal", "r1")

    def test_invalid_stage_name(self):
        self.assertRaises(ValueError, self.crm.advance, self.opp_id, "closed", "r1")

    def test_permission(self):
        self.assertRaises(PermissionError, self.crm.advance, self.opp_id, "proposal", "r2")

    def test_manager_may_advance(self):
        self.crm.advance(self.opp_id, "proposal", "m1")
        self.assertEqual(self.crm.opps[self.opp_id]["stage"], "proposal")

    def test_skipping_stage_rejected(self):
        self.assertRaises(ValueError, self.crm.advance, self.opp_id, "negotiation", "r1")
        self.assertRaises(ValueError, self.crm.advance, self.opp_id, "won", "r1")
        self.assertEqual(self.crm.opps[self.opp_id]["stage"], "prospect")

    def test_no_going_back(self):
        self.crm.advance(self.opp_id, "proposal", "r1")
        self.assertRaises(ValueError, self.crm.advance, self.opp_id, "prospect", "r1")

    def test_lost_from_any_stage(self):
        self.crm.advance(self.opp_id, "lost", "r1")
        self.assertEqual(self.crm.opps[self.opp_id]["stage"], "lost")

    def test_final_stage_is_terminal(self):
        for stage in ("proposal", "negotiation", "won"):
            self.crm.advance(self.opp_id, stage, "r1")
        self.assertRaises(ValueError, self.crm.advance, self.opp_id, "lost", "r1")
        self.assertRaises(ValueError, self.crm.advance, self.opp_id, "won", "r1")

    def test_negotiation_over_50k_needs_manager(self):
        crm = make_crm()
        lead_id = crm.add_lead("big@example.com", "B", "referral", "r1")
        crm.qualify(lead_id, "r1")
        opp_id = crm.convert(lead_id, 60000, "r1")
        crm.advance(opp_id, "proposal", "r1")
        self.assertRaises(PermissionError, crm.advance, opp_id, "negotiation", "r1")
        self.assertEqual(crm.opps[opp_id]["stage"], "proposal")
        crm.advance(opp_id, "negotiation", "m1")
        self.assertEqual(crm.opps[opp_id]["stage"], "negotiation")

    def test_negotiation_at_50k_allowed_for_rep(self):
        crm = make_crm()
        lead_id = crm.add_lead("edge@example.com", "E", "referral", "r1")
        crm.qualify(lead_id, "r1")
        opp_id = crm.convert(lead_id, 50000, "r1")
        crm.advance(opp_id, "proposal", "r1")
        crm.advance(opp_id, "negotiation", "r1")
        self.assertEqual(crm.opps[opp_id]["stage"], "negotiation")

    def test_final_stage_frees_slot_and_assigns(self):
        reps = [{"id": "r1", "role": "rep", "capacity": 1}]
        crm = make_crm(reps)
        lead_id = crm.add_lead("a@example.com", "A", "referral", "r1")
        crm.qualify(lead_id, "r1")
        opp_id = crm.convert(lead_id, 100, "r1")
        waiting = crm.add_lead("b@example.com", "B", "web", "r1")
        self.assertIsNone(crm.leads[waiting]["owner"])
        for stage in ("proposal", "negotiation", "won"):
            crm.advance(opp_id, stage, "r1")
        self.assertEqual(crm.leads[waiting]["owner"], "r1")
        self.assertEqual(crm.log[-1], ("assign", waiting, "system"))
        self.assertEqual(crm.waiting, [])

    def test_failed_advance_logs_nothing(self):
        before = list(self.crm.log)
        self.assertRaises(ValueError, self.crm.advance, self.opp_id, "won", "r1")
        self.assertEqual(self.crm.log, before)


class TestDiscount(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        lead_id = self.crm.add_lead("a@example.com", "A", "referral", "r1")
        self.crm.qualify(lead_id, "r1")
        self.opp_id = self.crm.convert(lead_id, 1000, "r1")

    def test_discount_ok(self):
        self.crm.discount(self.opp_id, 10, "r1")
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 900)
        self.assertEqual(self.crm.opps[self.opp_id]["original_amount"], 1000)
        self.assertEqual(self.crm.log[-1], ("discount", self.opp_id, "r1"))

    def test_bad_pct(self):
        for bad in (0, 31, -1, True, 5.0, "5", None):
            self.assertRaises(ValueError, self.crm.discount, self.opp_id, bad, "r1")
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 1000)

    def test_pct_checked_before_permission(self):
        self.assertRaises(ValueError, self.crm.discount, self.opp_id, 99, "r2")

    def test_unknown_opp(self):
        self.assertRaises(ValueError, self.crm.discount, "O404", 5, "r1")

    def test_rep_limit(self):
        self.assertRaises(PermissionError, self.crm.discount, self.opp_id, 11, "r1")
        self.crm.discount(self.opp_id, 10, "r1")
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 900)

    def test_manager_can_use_30(self):
        self.crm.discount(self.opp_id, 30, "m1")
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 700)

    def test_cumulative_limit(self):
        self.crm.discount(self.opp_id, 30, "m1")
        self.assertRaises(ValueError, self.crm.discount, self.opp_id, 1, "m1")
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 700)

    def test_floor_division(self):
        crm = make_crm()
        lead_id = crm.add_lead("f@example.com", "F", "referral", "r1")
        crm.qualify(lead_id, "r1")
        opp_id = crm.convert(lead_id, 999, "r1")
        crm.discount(opp_id, 10, "r1")
        self.assertEqual(crm.opps[opp_id]["amount"], 899)

    def test_final_stage_rejected(self):
        self.crm.advance(self.opp_id, "lost", "r1")
        self.assertRaises(ValueError, self.crm.discount, self.opp_id, 5, "r1")
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 1000)

    def test_permission(self):
        self.assertRaises(PermissionError, self.crm.discount, self.opp_id, 5, "r2")


class TestTransfer(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        lead_id = self.crm.add_lead("a@example.com", "A", "referral", "r1")
        self.crm.qualify(lead_id, "r1")
        self.opp_id = self.crm.convert(lead_id, 1000, "r1")

    def test_transfer_ok(self):
        self.crm.transfer(self.opp_id, "r2", "m1")
        self.assertEqual(self.crm.opps[self.opp_id]["owner"], "r2")
        self.assertEqual(self.crm.log[-1], ("transfer", self.opp_id, "m1"))

    def test_only_manager(self):
        self.assertRaises(PermissionError, self.crm.transfer, self.opp_id, "r2", "r1")
        self.assertEqual(self.crm.opps[self.opp_id]["owner"], "r1")

    def test_target_must_be_rep(self):
        self.assertRaises(ValueError, self.crm.transfer, self.opp_id, "m1", "m1")
        self.assertRaises(ValueError, self.crm.transfer, self.opp_id, "ghost", "m1")

    def test_unknown_opp(self):
        self.assertRaises(ValueError, self.crm.transfer, "O404", "r2", "m1")

    def test_final_stage_rejected(self):
        for stage in ("proposal", "negotiation", "won"):
            self.crm.advance(self.opp_id, stage, "r1")
        self.assertRaises(ValueError, self.crm.transfer, self.opp_id, "r2", "m1")

    def test_same_owner_rejected(self):
        self.assertRaises(ValueError, self.crm.transfer, self.opp_id, "r1", "m1")

    def test_capacity_required(self):
        reps = [
            {"id": "r1", "role": "rep", "capacity": 5},
            {"id": "r2", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 0},
        ]
        crm = make_crm(reps)
        first = crm.add_lead("a@example.com", "A", "referral", "r1")
        crm.qualify(first, "m1")
        opp_id = crm.convert(first, 500, "m1")
        second = crm.add_lead("b@example.com", "B", "referral", "m1")
        crm.qualify(second, "m1")
        crm.convert(second, 700, "m1")
        self.assertEqual(crm._load("r2"), 1)
        self.assertRaises(ValueError, crm.transfer, opp_id, "r2", "m1")
        self.assertEqual(crm.opps[opp_id]["owner"], "r1")

    def test_transfer_frees_previous_owner_slot(self):
        reps = [
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 2},
            {"id": "m1", "role": "manager", "capacity": 0},
        ]
        crm = make_crm(reps)
        lead_id = crm.add_lead("a@example.com", "A", "referral", "r1")
        crm.qualify(lead_id, "m1")
        opp_id = crm.convert(lead_id, 100, "m1")
        self.assertEqual(crm.opps[opp_id]["owner"], "r1")
        crm.transfer(opp_id, "r2", "m1")
        self.assertEqual(crm.opps[opp_id]["owner"], "r2")
        self.assertEqual(crm._load("r1"), 0)
        self.assertEqual(crm.waiting, [])
        self.assertEqual(crm.log[-1], ("transfer", opp_id, "m1"))
        # the freed slot is real: the next lead goes to r1 instead of queueing
        new_lead = crm.add_lead("b@example.com", "B", "web", "m1")
        self.assertEqual(crm.leads[new_lead]["owner"], "r1")


class TestForecast(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(make_crm().forecast(), {"open": 0, "weighted": 0, "won": 0})

    def test_weighted_and_won(self):
        crm = make_crm()
        ids = []
        for i, source in enumerate(("referral", "referral", "referral", "referral")):
            lead_id = crm.add_lead("l%d@example.com" % i, "N%d" % i, source, "m1")
            crm.qualify(lead_id, "m1")
            ids.append(crm.convert(lead_id, 1000, "m1"))
        crm.advance(ids[0], "proposal", "m1")
        crm.advance(ids[1], "proposal", "m1")
        crm.advance(ids[1], "negotiation", "m1")
        for stage in ("proposal", "negotiation", "won"):
            crm.advance(ids[2], stage, "m1")
        crm.advance(ids[3], "lost", "m1")
        self.assertEqual(
            crm.forecast(), {"open": 2, "weighted": 300 + 600, "won": 1000}
        )

    def test_forecast_ignores_actor_and_logs_nothing(self):
        crm = make_crm()
        lead_id = crm.add_lead("a@example.com", "A", "referral", "r1")
        crm.qualify(lead_id, "r1")
        crm.convert(lead_id, 1000, "r1")
        before = list(crm.log)
        crm.forecast()
        self.assertEqual(crm.log, before)

    def test_weighted_uses_current_amount(self):
        crm = make_crm()
        lead_id = crm.add_lead("a@example.com", "A", "referral", "r1")
        crm.qualify(lead_id, "r1")
        opp_id = crm.convert(lead_id, 1000, "r1")
        crm.discount(opp_id, 10, "r1")
        crm.advance(opp_id, "proposal", "r1")
        self.assertEqual(crm.forecast()["weighted"], 900 * 30 // 100)


class TestEdgeCases(unittest.TestCase):
    def test_waiting_queue_is_fifo_and_one_slot_one_lead(self):
        reps = [
            {"id": "r1", "role": "rep", "capacity": 2},
            {"id": "r2", "role": "rep", "capacity": 2},
            {"id": "m1", "role": "manager", "capacity": 0},
        ]
        crm = make_crm(reps)
        l1 = crm.add_lead("a@x.com", "A", "referral", "m1")
        crm.qualify(l1, "m1")
        opp1 = crm.convert(l1, 100, "m1")
        l2 = crm.add_lead("b@x.com", "B", "referral", "m1")
        crm.qualify(l2, "m1")
        crm.convert(l2, 100, "m1")
        w1 = crm.add_lead("c@x.com", "C", "web", "m1")
        w2 = crm.add_lead("d@x.com", "D", "web", "m1")
        w3 = crm.add_lead("e@x.com", "E", "web", "m1")
        w4 = crm.add_lead("f@x.com", "F", "web", "m1")
        self.assertEqual((crm.leads[w1]["owner"], crm.leads[w2]["owner"]), ("r1", "r2"))
        self.assertEqual(crm.waiting, [w3, w4])
        crm.advance(opp1, "lost", "m1")
        self.assertEqual(crm.leads[w3]["owner"], "r1")
        self.assertIsNone(crm.leads[w4]["owner"])
        self.assertEqual(crm.waiting, [w4])

    def test_lost_from_prospect_frees_slot(self):
        reps = [
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 0},
        ]
        crm = make_crm(reps)
        lead_id = crm.add_lead("a@x.com", "A", "referral", "m1")
        crm.qualify(lead_id, "m1")
        opp_id = crm.convert(lead_id, 100, "m1")
        waiting = crm.add_lead("b@x.com", "B", "web", "m1")
        self.assertIsNone(crm.leads[waiting]["owner"])
        crm.advance(opp_id, "lost", "m1")
        self.assertEqual(crm.leads[waiting]["owner"], "r1")

    def test_failed_add_lead_consumes_no_id(self):
        crm = make_crm()
        for bad in (
            ("bad", "A", "web"),
            ("a@x.com", "  ", "web"),
            ("a@x.com", "A", "ads"),
        ):
            self.assertRaises(ValueError, crm.add_lead, bad[0], bad[1], bad[2], "r1")
        self.assertEqual(crm.leads, {})
        self.assertEqual(crm.log, [])
        self.assertEqual(crm.add_lead("a@x.com", "A", "web", "r1"), "L1")

    def test_transfer_check_order(self):
        crm = make_crm()
        lead_id = crm.add_lead("a@x.com", "A", "referral", "r1")
        crm.qualify(lead_id, "r1")
        opp_id = crm.convert(lead_id, 100, "r1")
        # non-manager is rejected before the target is inspected
        self.assertRaises(PermissionError, crm.transfer, opp_id, "ghost", "r1")
        # invalid target is rejected before the final-stage check
        crm.advance(opp_id, "lost", "r1")
        self.assertRaises(ValueError, crm.transfer, opp_id, "ghost", "m1")
        self.assertRaises(ValueError, crm.transfer, opp_id, "r2", "m1")

    def test_negotiation_threshold_uses_current_amount(self):
        crm = make_crm()
        lead_id = crm.add_lead("big@x.com", "B", "referral", "r1")
        crm.qualify(lead_id, "r1")
        opp_id = crm.convert(lead_id, 52000, "r1")
        crm.advance(opp_id, "proposal", "r1")
        crm.discount(opp_id, 30, "m1")
        crm.advance(opp_id, "negotiation", "r1")
        self.assertEqual(crm.opps[opp_id]["stage"], "negotiation")

    def test_opportunity_ids_independent_of_lead_ids(self):
        crm = make_crm()
        for i in range(2):
            lead_id = crm.add_lead("g%d@x.com" % i, "N", "referral", "m1")
            crm.qualify(lead_id, "m1")
        self.assertEqual(crm.convert("L2", 100, "m1"), "O1")

    def test_non_string_entity_ids_raise_value_error(self):
        crm = make_crm()
        for bad in (None, 1, [], ("L1",)):
            self.assertRaises(ValueError, crm.qualify, bad, "r1")
            self.assertRaises(ValueError, crm.convert, bad, 100, "r1")
            self.assertRaises(ValueError, crm.advance, bad, "proposal", "r1")
            self.assertRaises(ValueError, crm.discount, bad, 5, "r1")
            self.assertRaises(ValueError, crm.transfer, bad, "r2", "m1")

    def test_manager_never_owns_or_carries_load(self):
        reps = [{"id": "m1", "role": "manager", "capacity": 5}]
        crm = make_crm(reps)
        lead_id = crm.add_lead("a@x.com", "A", "web", "m1")
        self.assertIsNone(crm.leads[lead_id]["owner"])
        self.assertEqual(crm._load("m1"), 0)


if __name__ == "__main__":
    unittest.main()
