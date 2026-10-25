import unittest

from crm import CRM, DuplicateLeadError


def make_crm():
    return CRM(
        [
            {"id": "m1", "role": "manager", "capacity": 99},
            {"id": "r1", "role": "rep", "capacity": 2},
            {"id": "r2", "role": "rep", "capacity": 2},
        ]
    )


def make_full_crm():
    return CRM(
        [
            {"id": "m1", "role": "manager", "capacity": 99},
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 1},
        ]
    )


class TestInit(unittest.TestCase):
    def test_initial_state(self):
        crm = make_crm()
        self.assertEqual(crm.leads, {})
        self.assertEqual(crm.opps, {})
        self.assertEqual(crm.log, [])


class TestAddLeadValidation(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()

    def test_unknown_actor_checked_first(self):
        with self.assertRaises(PermissionError):
            self.crm.add_lead("not-an-email", "", "bogus", "ghost")
        self.assertEqual(self.crm.log, [])
        self.assertEqual(self.crm.leads, {})

    def test_email_must_be_string(self):
        for bad in (None, 123, ["a@b.com"]):
            with self.assertRaises(ValueError):
                self.crm.add_lead(bad, "Ann", "web", "r1")

    def test_email_shape(self):
        bad = [
            "plainaddress",
            "a@b@c.com",
            "@b.com",
            "a@bcom",
            "a@.com",
            "a@com.",
            "a@.b.",
        ]
        for email in bad:
            with self.assertRaises(ValueError):
                self.crm.add_lead(email, "Ann", "web", "r1")

    def test_valid_email_shapes(self):
        ok = ["a@b.co", "user@mail.example.com", " x@y.z "]
        for email in ok:
            self.crm.add_lead(email, "Ann", "web", "r1")

    def test_name_validation(self):
        for bad in (None, "", "   ", 5):
            with self.assertRaises(ValueError):
                self.crm.add_lead("a@b.com", bad, "web", "r1")

    def test_source_validation(self):
        for bad in ("", "Web", "ads", None):
            with self.assertRaises(ValueError):
                self.crm.add_lead("a@b.com", "Ann", bad, "r1")
        self.assertEqual(self.crm.leads, {})

    def test_normalized_email_and_name(self):
        lead_id = self.crm.add_lead("  Ann@Example.COM ", "  Ann  ", "web", "r1")
        lead = self.crm.leads[lead_id]
        self.assertEqual(lead["email"], "ann@example.com")
        self.assertEqual(lead["name"], "Ann")

    def test_duplicate_uses_normalized_email(self):
        first = self.crm.add_lead("dup@example.com", "Ann", "web", "r1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            self.crm.add_lead(" DUP@Example.com ", "Bob", "event", "r1")
        self.assertEqual(ctx.exception.existing_id, first)
        self.assertEqual(len(self.crm.leads), 1)

    def test_duplicate_error_is_exception_subclass(self):
        self.crm.add_lead("dup@example.com", "Ann", "web", "r1")
        with self.assertRaises(DuplicateLeadError):
            self.crm.add_lead("dup@example.com", "Bob", "web", "r1")


class TestAddLeadScoringAndOwnership(unittest.TestCase):
    def test_scores(self):
        crm = make_crm()
        cases = [
            ("a@gmail.com", "web", 10),
            ("b@gmail.com", "referral", 30),
            ("c@example.com", "event", 35),
            ("d@example.com", "referral", 45),
            ("e@outlook.com", "event", 20),
            ("f@yahoo.com", "web", 10),
        ]
        for email, source, score in cases:
            lead_id = crm.add_lead(email, "N", source, "r1")
            self.assertEqual(crm.leads[lead_id]["score"], score, email)

    def test_ids_and_lead_fields(self):
        crm = make_crm()
        first = crm.add_lead("a@gmail.com", " Ann ", "web", "r1")
        second = crm.add_lead("b@gmail.com", "Bob", "event", "r2")
        self.assertEqual(first, "L1")
        self.assertEqual(second, "L2")
        self.assertEqual(
            crm.leads[first],
            {
                "id": "L1",
                "email": "a@gmail.com",
                "name": "Ann",
                "source": "web",
                "score": 10,
                "owner": "r1",
                "status": "new",
            },
        )
        self.assertEqual(crm.log, [("add_lead", "L1", "r1"), ("add_lead", "L2", "r2")])

    def test_failed_creation_does_not_consume_id(self):
        crm = make_crm()
        with self.assertRaises(ValueError):
            crm.add_lead("bad", "Ann", "web", "r1")
        self.assertEqual(crm.add_lead("a@gmail.com", "Ann", "web", "r1"), "L1")

    def test_lowest_load_and_tie_break(self):
        crm = CRM(
            [
                {"id": "r9", "role": "rep", "capacity": 5},
                {"id": "r1", "role": "rep", "capacity": 5},
                {"id": "r5", "role": "rep", "capacity": 5},
            ]
        )
        owner = crm.leads[crm.add_lead("a@gmail.com", "A", "web", "r1")]["owner"]
        self.assertEqual(owner, "r1")
        owner2 = crm.leads[crm.add_lead("b@gmail.com", "B", "web", "r1")]["owner"]
        self.assertEqual(owner2, "r5")
        owner3 = crm.leads[crm.add_lead("c@gmail.com", "C", "web", "r1")]["owner"]
        self.assertEqual(owner3, "r9")

    def test_managers_never_own(self):
        crm = CRM(
            [
                {"id": "m1", "role": "manager", "capacity": 10},
                {"id": "r1", "role": "rep", "capacity": 0},
            ]
        )
        lead_id = crm.add_lead("a@gmail.com", "A", "web", "m1")
        self.assertIsNone(crm.leads[lead_id]["owner"])

    def test_waiting_queue_fifo_and_assign_log(self):
        crm = make_full_crm()
        l1 = crm.add_lead("a@example.com", "A", "referral", "r1")
        l2 = crm.add_lead("b@example.com", "B", "referral", "r1")
        l3 = crm.add_lead("c@example.com", "C", "referral", "r1")
        self.assertEqual(crm.leads[l1]["owner"], "r1")
        self.assertEqual(crm.leads[l2]["owner"], "r2")
        self.assertIsNone(crm.leads[l3]["owner"])

        crm.qualify(l1, "r1")
        o1 = crm.convert(l1, 1000, "r1")
        crm.advance(o1, "proposal", "r1")
        crm.advance(o1, "negotiation", "r1")
        crm.advance(o1, "won", "r1")

        self.assertEqual(crm.leads[l3]["owner"], "r1")
        self.assertEqual(
            crm.log[-2:],
            [("advance", "O1", "r1"), ("assign", l3, "system")],
        )


class TestQualify(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        self.lead = self.crm.add_lead("a@example.com", "A", "referral", "r1")

    def test_happy_path(self):
        self.crm.qualify(self.lead, "r1")
        self.assertEqual(self.crm.leads[self.lead]["status"], "qualified")
        self.assertEqual(self.crm.log[-1], ("qualify", self.lead, "r1"))

    def test_unknown_lead(self):
        with self.assertRaises(ValueError):
            self.crm.qualify("L99", "r1")

    def test_permission(self):
        with self.assertRaises(PermissionError):
            self.crm.qualify(self.lead, "r2")
        self.assertEqual(self.crm.leads[self.lead]["status"], "new")
        self.assertEqual(len(self.crm.log), 1)

    def test_manager_may_qualify(self):
        self.crm.qualify(self.lead, "m1")
        self.assertEqual(self.crm.leads[self.lead]["status"], "qualified")

    def test_must_be_new(self):
        self.crm.qualify(self.lead, "r1")
        with self.assertRaises(ValueError):
            self.crm.qualify(self.lead, "r1")

    def test_score_threshold(self):
        lead = self.crm.add_lead("b@gmail.com", "B", "web", "r2")
        with self.assertRaises(ValueError):
            self.crm.qualify(lead, "r2")
        self.assertEqual(self.crm.leads[lead]["status"], "new")


class TestConvert(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        self.lead = self.crm.add_lead("a@example.com", "A", "referral", "r1")

    def _qualified(self):
        self.crm.qualify(self.lead, "r1")
        return self.lead

    def test_happy_path(self):
        self._qualified()
        opp_id = self.crm.convert(self.lead, 1000, "r1")
        self.assertEqual(opp_id, "O1")
        self.assertEqual(
            self.crm.opps[opp_id],
            {
                "id": "O1",
                "lead_id": self.lead,
                "owner": "r1",
                "amount": 1000,
                "original_amount": 1000,
                "stage": "prospect",
            },
        )
        self.assertEqual(self.crm.leads[self.lead]["status"], "converted")
        self.assertEqual(self.crm.log[-1], ("convert", opp_id, "r1"))

    def test_unknown_lead(self):
        with self.assertRaises(ValueError):
            self.crm.convert("L99", 10, "r1")

    def test_amount_validation(self):
        self._qualified()
        for bad in (0, -5, True, False, 1.5, "10", None):
            with self.assertRaises(ValueError):
                self.crm.convert(self.lead, bad, "r1")
        self.assertFalse(self.crm.opps)

    def test_amount_checked_before_permission(self):
        with self.assertRaises(ValueError):
            self.crm.convert(self.lead, 0, "r2")
        self.assertFalse(self.crm.opps)

    def test_permission(self):
        self._qualified()
        with self.assertRaises(PermissionError):
            self.crm.convert(self.lead, 10, "r2")
        self.assertFalse(self.crm.opps)
        self.assertEqual(self.crm.leads[self.lead]["status"], "qualified")

    def test_manager_may_convert(self):
        self._qualified()
        self.assertEqual(self.crm.convert(self.lead, 10, "m1"), "O1")

    def test_must_be_qualified(self):
        with self.assertRaises(ValueError):
            self.crm.convert(self.lead, 10, "r1")

    def test_requires_owner(self):
        crm = CRM(
            [
                {"id": "m1", "role": "manager", "capacity": 9},
                {"id": "r1", "role": "rep", "capacity": 0},
            ]
        )
        lead = crm.add_lead("a@example.com", "A", "referral", "m1")
        crm.qualify(lead, "m1")
        with self.assertRaises(ValueError):
            crm.convert(lead, 100, "m1")
        self.assertFalse(crm.opps)
        self.assertEqual(crm.leads[lead]["status"], "qualified")

    def test_conversion_sequence(self):
        lead2 = self.crm.add_lead("b@example.com", "B", "referral", "r2")
        self._qualified()
        self.crm.qualify(lead2, "r2")
        first = self.crm.convert(self.lead, 5, "r1")
        second = self.crm.convert(lead2, 5, "r2")
        self.assertEqual((first, second), ("O1", "O2"))


class TestAdvance(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        self.lead = self.crm.add_lead("a@example.com", "A", "referral", "r1")
        self.crm.qualify(self.lead, "r1")
        self.opp = self.crm.convert(self.lead, 1000, "r1")

    def test_stage_order(self):
        self.crm.advance(self.opp, "proposal", "r1")
        self.crm.advance(self.opp, "negotiation", "r1")
        self.crm.advance(self.opp, "won", "r1")
        self.assertEqual(self.crm.opps[self.opp]["stage"], "won")
        self.assertEqual(
            self.crm.log[-3:],
            [
                ("advance", self.opp, "r1"),
                ("advance", self.opp, "r1"),
                ("advance", self.opp, "r1"),
            ],
        )

    def test_unknown_opp(self):
        with self.assertRaises(ValueError):
            self.crm.advance("O99", "proposal", "r1")

    def test_invalid_stage(self):
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "closed", "r1")

    def test_stage_checked_before_permission(self):
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "bogus", "r2")

    def test_permission(self):
        with self.assertRaises(PermissionError):
            self.crm.advance(self.opp, "proposal", "r2")

    def test_manager_may_advance(self):
        self.crm.advance(self.opp, "proposal", "m1")
        self.assertEqual(self.crm.opps[self.opp]["stage"], "proposal")

    def test_cannot_skip_stages(self):
        for target in ("negotiation", "won"):
            with self.assertRaises(ValueError):
                self.crm.advance(self.opp, target, "r1")
        self.assertEqual(self.crm.opps[self.opp]["stage"], "prospect")

    def test_can_go_lost_from_any_open_stage(self):
        self.crm.advance(self.opp, "lost", "r1")
        self.assertEqual(self.crm.opps[self.opp]["stage"], "lost")

    def test_final_is_final(self):
        self.crm.advance(self.opp, "lost", "r1")
        for target in ("lost", "proposal", "won"):
            with self.assertRaises(ValueError):
                self.crm.advance(self.opp, target, "r1")

    def test_large_negotiation_requires_manager(self):
        crm = CRM(
            [
                {"id": "m1", "role": "manager", "capacity": 9},
                {"id": "r1", "role": "rep", "capacity": 5},
            ]
        )
        lead = crm.add_lead("a@example.com", "A", "referral", "r1")
        crm.qualify(lead, "r1")
        opp_id = crm.convert(lead, 60000, "r1")
        crm.advance(opp_id, "proposal", "r1")
        with self.assertRaises(PermissionError):
            crm.advance(opp_id, "negotiation", "r1")
        self.assertEqual(crm.opps[opp_id]["stage"], "proposal")
        crm.advance(opp_id, "negotiation", "m1")
        self.assertEqual(crm.opps[opp_id]["stage"], "negotiation")

    def test_needs_manager_only_above_50000(self):
        crm = make_crm()
        lead = crm.add_lead("a@example.com", "A", "referral", "r1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 50000, "r1")
        crm.advance(opp, "proposal", "r1")
        crm.advance(opp, "negotiation", "r1")
        self.assertEqual(crm.opps[opp]["stage"], "negotiation")

    def test_free_slot_on_lost(self):
        crm = make_full_crm()
        l1 = crm.add_lead("a@example.com", "A", "referral", "r1")
        l2 = crm.add_lead("b@example.com", "B", "referral", "r1")
        l3 = crm.add_lead("c@example.com", "C", "referral", "r1")
        self.assertIsNone(crm.leads[l3]["owner"])
        crm.qualify(l1, "r1")
        o1 = crm.convert(l1, 100, "r1")
        crm.advance(o1, "lost", "r1")
        self.assertEqual(crm.leads[l3]["owner"], "r1")
        self.assertEqual(crm.log[-1], ("assign", l3, "system"))
        self.assertEqual(crm.leads[l2]["owner"], "r2")


class TestDiscount(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        self.lead = self.crm.add_lead("a@example.com", "A", "referral", "r1")
        self.crm.qualify(self.lead, "r1")
        self.opp = self.crm.convert(self.lead, 1000, "r1")

    def test_happy_path(self):
        self.crm.discount(self.opp, 10, "r1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 900)
        self.assertEqual(self.crm.opps[self.opp]["original_amount"], 1000)
        self.assertEqual(self.crm.log[-1], ("discount", self.opp, "r1"))

    def test_unknown_opp(self):
        with self.assertRaises(ValueError):
            self.crm.discount("O99", 5, "r1")

    def test_pct_validation(self):
        for bad in (0, 31, -1, True, False, 5.0, "5", None):
            with self.assertRaises(ValueError):
                self.crm.discount(self.opp, bad, "r1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 1000)

    def test_pct_checked_before_permission(self):
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp, 0, "r2")

    def test_permission(self):
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp, 5, "r2")

    def test_manager_may_use_more_than_10(self):
        self.crm.discount(self.opp, 30, "m1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 700)

    def test_non_manager_capped_at_10(self):
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp, 11, "r1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 1000)

    def test_stage_final(self):
        self.crm.advance(self.opp, "lost", "r1")
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp, 5, "r1")

    def test_cumulative_limit(self):
        self.crm.discount(self.opp, 10, "m1")
        self.crm.discount(self.opp, 10, "m1")
        self.crm.discount(self.opp, 10, "m1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 729)
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp, 10, "m1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 729)

    def test_rounding_floor(self):
        crm = make_crm()
        lead = crm.add_lead("a@example.com", "A", "referral", "r1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 101, "r1")
        crm.discount(opp, 1, "r1")
        self.assertEqual(crm.opps[opp]["amount"], 99)
        self.assertEqual(crm.log[-1], ("discount", opp, "r1"))


class TestTransfer(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        self.lead = self.crm.add_lead("a@example.com", "A", "referral", "r1")
        self.crm.qualify(self.lead, "r1")
        self.opp = self.crm.convert(self.lead, 1000, "r1")

    def test_happy_path(self):
        self.crm.transfer(self.opp, "r2", "m1")
        self.assertEqual(self.crm.opps[self.opp]["owner"], "r2")
        self.assertEqual(self.crm.log[-1], ("transfer", self.opp, "m1"))

    def test_unknown_opp(self):
        with self.assertRaises(ValueError):
            self.crm.transfer("O99", "r2", "m1")

    def test_actor_must_be_manager(self):
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.opp, "r2", "r1")
        self.assertEqual(self.crm.opps[self.opp]["owner"], "r1")

    def test_manager_check_before_new_owner(self):
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.opp, "nobody", "r1")

    def test_new_owner_must_be_rep(self):
        for bad in ("m1", "ghost", 5, None):
            with self.assertRaises(ValueError):
                self.crm.transfer(self.opp, bad, "m1")

    def test_stage_must_be_open(self):
        self.crm.advance(self.opp, "lost", "r1")
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "r2", "m1")

    def test_same_owner_rejected(self):
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "r1", "m1")

    def test_target_capacity(self):
        crm = make_full_crm()
        lead = crm.add_lead("a@example.com", "A", "referral", "r1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 100, "r1")
        crm.add_lead("b@example.com", "B", "referral", "r1")
        with self.assertRaises(ValueError):
            crm.transfer(opp, "r2", "m1")
        self.assertEqual(crm.opps[opp]["owner"], "r1")

    def test_transfer_frees_previous_owner_slot(self):
        crm = CRM(
            [
                {"id": "m1", "role": "manager", "capacity": 9},
                {"id": "r1", "role": "rep", "capacity": 1},
                {"id": "r2", "role": "rep", "capacity": 2},
            ]
        )
        lead = crm.add_lead("a@example.com", "A", "referral", "r1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 100, "r1")  # r1 is full: one open opportunity

        crm.transfer(opp, "r2", "m1")
        self.assertEqual(crm.opps[opp]["owner"], "r2")

        # r1 now has a free slot again and wins the next lead.
        new_lead = crm.add_lead("b@example.com", "B", "referral", "m1")
        self.assertEqual(crm.leads[new_lead]["owner"], "r1")


class TestForecast(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(make_crm().forecast(), {"open": 0, "weighted": 0, "won": 0})

    def test_values(self):
        crm = CRM(
            [
                {"id": "m1", "role": "manager", "capacity": 99},
                {"id": "r1", "role": "rep", "capacity": 10},
                {"id": "r2", "role": "rep", "capacity": 10},
            ]
        )
        lead = crm.add_lead("a@example.com", "A", "referral", "r1")
        crm.qualify(lead, "r1")
        o1 = crm.convert(lead, 1000, "r1")  # prospect 10% -> 100
        lead2 = crm.add_lead("b@example.com", "B", "referral", "r2")
        crm.qualify(lead2, "r2")
        o2 = crm.convert(lead2, 1000, "r2")  # proposal 30% -> 300
        crm.advance(o2, "proposal", "r2")
        lead3 = crm.add_lead("c@example.com", "C", "referral", "r1")
        crm.qualify(lead3, "r1")
        o3 = crm.convert(lead3, 1000, "r1")  # negotiation 60% -> 600
        crm.advance(o3, "proposal", "r1")
        crm.advance(o3, "negotiation", "r1")
        lead4 = crm.add_lead("d@example.com", "D", "referral", "r2")
        crm.qualify(lead4, "r2")
        o4 = crm.convert(lead4, 500, "r2")  # won -> 500
        crm.advance(o4, "proposal", "r2")
        crm.advance(o4, "negotiation", "r2")
        crm.advance(o4, "won", "r2")
        lead5 = crm.add_lead("e@example.com", "E", "referral", "r1")
        crm.qualify(lead5, crm.leads[lead5]["owner"])
        o5 = crm.convert(lead5, 700, crm.leads[lead5]["owner"])  # lost
        crm.advance(o5, "lost", "m1")

        self.assertEqual(crm.forecast(), {"open": 3, "weighted": 1000, "won": 500})

    def test_forecast_does_not_log(self):
        crm = make_crm()
        before = list(crm.log)
        crm.forecast()
        self.assertEqual(crm.log, before)

    def test_weighted_uses_floor_per_opp(self):
        crm = make_crm()
        lead = crm.add_lead("a@example.com", "A", "referral", "r1")
        crm.qualify(lead, "r1")
        crm.convert(lead, 33, "r1")
        self.assertEqual(crm.forecast()["weighted"], 3)


class TestAtomicity(unittest.TestCase):
    def test_failed_calls_do_not_log_or_mutate(self):
        crm = make_crm()
        lead = crm.add_lead("a@example.com", "A", "referral", "r1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 1000, "r1")
        snapshot = (
            dict(crm.leads[lead]),
            dict(crm.opps[opp]),
            list(crm.log),
        )
        attempts = [
            lambda: crm.qualify("L99", "r1"),
            lambda: crm.qualify(lead, "r2"),
            lambda: crm.convert("L99", 1, "r1"),
            lambda: crm.convert(lead, 0, "r1"),
            lambda: crm.advance(opp, "won", "r2"),
            lambda: crm.advance(opp, "negotiation", "r1"),
            lambda: crm.discount(opp, 0, "r1"),
            lambda: crm.discount(opp, 30, "r1"),
            lambda: crm.transfer(opp, "m1", "m1"),
            lambda: crm.transfer(opp, "r1", "m1"),
        ]
        for attempt in attempts:
            try:
                attempt()
            except (ValueError, PermissionError):
                pass
            else:
                self.fail("expected an exception")
        self.assertEqual(
            (dict(crm.leads[lead]), dict(crm.opps[opp]), list(crm.log)),
            snapshot,
        )


if __name__ == "__main__":
    unittest.main()
