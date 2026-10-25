"""Edge-case tests written directly from the specification wording."""

import unittest

from crm import CRM, DuplicateLeadError


REPS = [
    {"id": "r1", "role": "rep", "capacity": 1},
    {"id": "r2", "role": "rep", "capacity": 1},
    {"id": "r3", "role": "rep", "capacity": 5},
    {"id": "mgr", "role": "manager", "capacity": 0},
]


def make(reps=None):
    return CRM(REPS if reps is None else reps)


class TestAddLeadValidation(unittest.TestCase):
    def test_actor_checked_before_everything(self):
        crm = make()
        with self.assertRaises(PermissionError):
            crm.add_lead("not-an-email", "", "bogus", "ghost")
        self.assertEqual(crm.leads, {})
        self.assertEqual(crm.log, [])

    def test_email_rules(self):
        crm = make()
        bad = [
            None,
            123,
            "",
            "no-at-sign.com",
            "a@@b.com",
            "a@b@c.com",
            " @acme.com",
            " a@.com",
            "a@com",
            "a@com.",
            "a@.x",
            "a@acme",
        ]
        for email in bad:
            with self.subTest(email=email):
                with self.assertRaises(ValueError):
                    crm.add_lead(email, "N", "web", "mgr")
        self.assertEqual(crm.leads, {})
        self.assertEqual(crm.log, [])

    def test_email_is_normalized(self):
        crm = make()
        lead_id = crm.add_lead("  Bob@Acme.COM ", "  Bob  ", "event", "mgr")
        lead = crm.leads[lead_id]
        self.assertEqual(lead["email"], "bob@acme.com")
        self.assertEqual(lead["name"], "Bob")
        self.assertEqual(lead["status"], "new")
        self.assertEqual(lead["score"], 35)

    def test_name_rules(self):
        crm = make()
        for name in [None, 5, "", "   "]:
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    crm.add_lead("a@acme.com", name, "web", "mgr")
        self.assertEqual(crm.leads, {})

    def test_source_rules(self):
        crm = make()
        for source in [None, "Web", "email", 3, "web "]:
            with self.subTest(source=source):
                with self.assertRaises(ValueError):
                    crm.add_lead("a@acme.com", "A", source, "mgr")
        self.assertEqual(crm.leads, {})

    def test_duplicate_detection_normalized(self):
        crm = make()
        first = crm.add_lead("a@acme.com", "A", "referral", "mgr")
        with self.assertRaises(DuplicateLeadError) as ctx:
            crm.add_lead(" A@ACME.COM ", "Other", "web", "mgr")
        self.assertEqual(ctx.exception.existing_id, first)
        self.assertEqual(len(crm.leads), 1)
        self.assertEqual([entry[0] for entry in crm.log], ["add_lead"])
        # ids are only consumed by successful creations
        second = crm.add_lead("b@acme.com", "B", "referral", "mgr")
        self.assertEqual(second, "L2")

    def test_scores(self):
        crm = make()
        cases = [
            ("w1@acme.com", "web", 25),
            ("w2@gmail.com", "web", 10),
            ("e1@acme.com", "event", 35),
            ("e2@yahoo.com", "event", 20),
            ("rr@outlook.com", "referral", 30),
            ("rn@acme.com", "referral", 45),
        ]
        for email, source, score in cases:
            lead_id = crm.add_lead(email, "n", source, "mgr")
            self.assertEqual(crm.leads[lead_id]["score"], score, email)


class TestAssignment(unittest.TestCase):
    def test_lowest_load_then_smallest_id(self):
        crm = make()
        a = crm.add_lead("a@acme.com", "A", "referral", "mgr")
        b = crm.add_lead("b@acme.com", "B", "referral", "mgr")
        c = crm.add_lead("c@acme.com", "C", "referral", "mgr")
        self.assertEqual(crm.leads[a]["owner"], "r1")
        self.assertEqual(crm.leads[b]["owner"], "r2")
        self.assertEqual(crm.leads[c]["owner"], "r3")

    def test_capacity_respected_then_waiting(self):
        crm = make()
        first = crm.add_lead("a@acme.com", "A", "referral", "mgr")
        second = crm.add_lead("b@acme.com", "B", "referral", "mgr")
        third = crm.add_lead("c@acme.com", "C", "referral", "mgr")
        self.assertEqual(crm.leads[first]["owner"], "r1")
        self.assertEqual(crm.leads[second]["owner"], "r2")
        self.assertEqual(crm.leads[third]["owner"], "r3")
        # r1/r2 are full, r3 still has room
        extra = crm.add_lead("d@acme.com", "D", "referral", "mgr")
        self.assertEqual(crm.leads[extra]["owner"], "r3")

    def test_all_full_goes_to_waiting(self):
        reps = [
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 1},
            {"id": "mgr", "role": "manager", "capacity": 0},
        ]
        crm = make(reps)
        first = crm.add_lead("a@acme.com", "A", "referral", "mgr")
        second = crm.add_lead("b@acme.com", "B", "referral", "mgr")
        third = crm.add_lead("c@acme.com", "C", "referral", "mgr")
        self.assertEqual(crm.leads[first]["owner"], "r1")
        self.assertEqual(crm.leads[second]["owner"], "r2")
        self.assertIsNone(crm.leads[third]["owner"])
        self.assertEqual(crm.waiting, [third])

    def test_waiting_lead_keeps_capacity(self):
        crm = make(
            [
                {"id": "only", "role": "rep", "capacity": 1},
                {"id": "mgr", "role": "manager", "capacity": 0},
            ]
        )
        first = crm.add_lead("a@acme.com", "A", "referral", "mgr")
        second = crm.add_lead("b@acme.com", "B", "referral", "mgr")
        self.assertEqual(crm.leads[first]["owner"], "only")
        self.assertIsNone(crm.leads[second]["owner"])

    def test_qualify_and_convert_free_then_reassign(self):
        reps = [
            {"id": "only", "role": "rep", "capacity": 1},
            {"id": "mgr", "role": "manager", "capacity": 0},
        ]
        crm = make(reps)
        first = crm.add_lead("a@acme.com", "A", "referral", "mgr")
        second = crm.add_lead("b@acme.com", "B", "referral", "mgr")
        self.assertIsNone(crm.leads[second]["owner"])
        crm.qualify(first, "mgr")
        opp = crm.convert(first, 1000, "mgr")
        self.assertEqual(crm.leads[first]["status"], "converted")
        crm.advance(opp, "proposal", "mgr")
        crm.advance(opp, "negotiation", "mgr")
        crm.advance(opp, "won", "mgr")
        self.assertEqual(crm.leads[second]["owner"], "only")
        self.assertEqual(crm.log[-2:], [("advance", opp, "mgr"), ("assign", second, "system")])


class TestQualify(unittest.TestCase):
    def test_order_of_checks(self):
        crm = make()
        with self.assertRaises(ValueError):
            crm.qualify("L404", "r1")
        with self.assertRaises(PermissionError):
            crm.qualify("L404", "ghost")

    def test_rep_may_not_qualify_someone_elses_or_unowned_lead(self):
        crm = make(
            [
                {"id": "only", "role": "rep", "capacity": 0},
                {"id": "mgr", "role": "manager", "capacity": 0},
            ]
        )
        lead = crm.add_lead("a@acme.com", "A", "referral", "mgr")
        self.assertIsNone(crm.leads[lead]["owner"])
        with self.assertRaises(PermissionError):
            crm.qualify(lead, "only")
        crm.qualify(lead, "mgr")
        self.assertEqual(crm.leads[lead]["status"], "qualified")
        with self.assertRaises(ValueError):
            crm.qualify(lead, "mgr")
        self.assertEqual(crm.log[-1], ("qualify", lead, "mgr"))

    def test_low_score_cannot_qualify(self):
        crm = make()
        web = crm.add_lead("w@acme.com", "W", "web", "mgr")  # 25
        event_free = crm.add_lead("e@gmail.com", "E", "event", "mgr")  # 20
        event = crm.add_lead("e2@acme.com", "E2", "event", "mgr")  # 35
        for lead in (web, event_free):
            with self.assertRaises(ValueError):
                crm.qualify(lead, "mgr")
            self.assertEqual(crm.leads[lead]["status"], "new")
        crm.qualify(event, "mgr")
        self.assertEqual(crm.leads[event]["status"], "qualified")

    def test_owner_may_qualify_own_lead(self):
        crm = make()
        lead = crm.add_lead("a@acme.com", "A", "referral", "mgr")
        owner = crm.leads[lead]["owner"]
        crm.qualify(lead, owner)
        self.assertEqual(crm.leads[lead]["status"], "qualified")


class TestConvert(unittest.TestCase):
    def test_amount_validation(self):
        crm = make()
        lead = crm.add_lead("a@acme.com", "A", "referral", "mgr")
        crm.qualify(lead, "mgr")
        for amount in [0, -5, 1.0, "10", True, False, None]:
            with self.subTest(amount=amount):
                with self.assertRaises(ValueError):
                    crm.convert(lead, amount, "mgr")
        self.assertEqual(crm.opps, {})

    def test_amount_validated_before_permission(self):
        crm = make()
        lead = crm.add_lead("a@acme.com", "A", "referral", "mgr")
        crm.qualify(lead, "mgr")
        with self.assertRaises(ValueError):
            crm.convert(lead, 0, "r1")

    def test_status_and_owner_checks(self):
        crm = make()
        lead = crm.add_lead("a@acme.com", "A", "referral", "mgr")
        with self.assertRaises(ValueError):
            crm.convert(lead, 100, "mgr")
        crm.qualify(lead, "mgr")
        opp = crm.convert(lead, 100, "mgr")
        self.assertEqual(opp, "O1")
        self.assertEqual(crm.leads[lead]["status"], "converted")
        self.assertEqual(
            crm.opps[opp],
            {
                "id": "O1",
                "lead_id": lead,
                "owner": "r1",
                "amount": 100,
                "original_amount": 100,
                "stage": "prospect",
            },
        )
        with self.assertRaises(ValueError):
            crm.convert(lead, 100, "mgr")
        self.assertEqual(crm.log[-1], ("convert", "O1", "mgr"))


class TestAdvance(unittest.TestCase):
    def setUp(self):
        self.crm = make()
        lead = self.crm.add_lead("a@acme.com", "A", "referral", "mgr")
        self.crm.qualify(lead, "mgr")
        self.opp = self.crm.convert(lead, 1000, "mgr")

    def test_stage_bounce_rules(self):
        crm, opp = self.crm, self.opp
        for bad in ["prospect", "won", "negotiation", "bogus", None, 1]:
            with self.subTest(stage=bad):
                with self.assertRaises(ValueError):
                    crm.advance(opp, bad, "mgr")
        crm.advance(opp, "proposal", "mgr")
        crm.advance(opp, "negotiation", "mgr")
        with self.assertRaises(ValueError):
            crm.advance(opp, "proposal", "mgr")
        crm.advance(opp, "won", "mgr")
        self.assertEqual(crm.opps[opp]["stage"], "won")
        with self.assertRaises(ValueError):
            crm.advance(opp, "lost", "mgr")
        with self.assertRaises(ValueError):
            crm.advance(opp, "won", "mgr")

    def test_lost_from_any_open_stage(self):
        crm = make()
        lead = crm.add_lead("a@acme.com", "A", "referral", "mgr")
        crm.qualify(lead, "mgr")
        opp = crm.convert(lead, 1000, "mgr")
        crm.advance(opp, "lost", "mgr")
        self.assertEqual(crm.opps[opp]["stage"], "lost")
        self.assertEqual(crm.log[-1], ("advance", opp, "mgr"))

    def test_permission_order(self):
        crm, opp = self.crm, self.opp
        # stage validity (check 2) comes before permission (check 3)
        with self.assertRaises(ValueError):
            crm.advance(opp, "bogus", "r2")
        with self.assertRaises(PermissionError):
            crm.advance(opp, "proposal", "r2")
        crm.advance(opp, "proposal", "mgr")
        with self.assertRaises(PermissionError):
            crm.advance(opp, "negotiation", "r2")

    def test_large_negotiation_needs_manager(self):
        crm = make()
        lead = crm.add_lead("a@acme.com", "A", "referral", "mgr")
        crm.qualify(lead, "mgr")
        opp = crm.convert(lead, 50001, "mgr")
        owner = crm.opps[opp]["owner"]
        crm.advance(opp, "proposal", owner)
        with self.assertRaises(PermissionError):
            crm.advance(opp, "negotiation", owner)
        self.assertEqual(crm.opps[opp]["stage"], "proposal")
        crm.advance(opp, "negotiation", "mgr")
        self.assertEqual(crm.opps[opp]["stage"], "negotiation")

    def test_exactly_50000_allowed_for_rep(self):
        crm = make()
        lead = crm.add_lead("a@acme.com", "A", "referral", "mgr")
        crm.qualify(lead, "mgr")
        opp = crm.convert(lead, 50000, "mgr")
        owner = crm.opps[opp]["owner"]
        crm.advance(opp, "proposal", owner)
        crm.advance(opp, "negotiation", owner)
        self.assertEqual(crm.opps[opp]["stage"], "negotiation")

    def test_final_stage_frees_and_assigns_fifo(self):
        reps = [
            {"id": "only", "role": "rep", "capacity": 2},
            {"id": "mgr", "role": "manager", "capacity": 0},
        ]
        crm = make(reps)
        first = crm.add_lead("a@acme.com", "A", "referral", "mgr")
        crm.qualify(first, "mgr")
        opp = crm.convert(first, 100, "mgr")
        w1 = crm.add_lead("b@acme.com", "B", "referral", "mgr")
        w2 = crm.add_lead("c@acme.com", "C", "referral", "mgr")
        w3 = crm.add_lead("d@acme.com", "D", "referral", "mgr")
        # capacity 2: opp + w1 fill it, w2 and w3 wait in FIFO order
        self.assertEqual(crm.leads[w1]["owner"], "only")
        self.assertIsNone(crm.leads[w2]["owner"])
        self.assertIsNone(crm.leads[w3]["owner"])
        crm.advance(opp, "lost", "mgr")
        self.assertEqual(crm.leads[w2]["owner"], "only")
        self.assertIsNone(crm.leads[w3]["owner"])
        self.assertEqual(crm.log[-2:], [("advance", opp, "mgr"), ("assign", w2, "system")])


class TestDiscount(unittest.TestCase):
    def setUp(self):
        self.crm = make()
        lead = self.crm.add_lead("a@acme.com", "A", "referral", "mgr")
        self.crm.qualify(lead, "mgr")
        self.opp = self.crm.convert(lead, 1000, "mgr")

    def test_pct_validation(self):
        crm, opp = self.crm, self.opp
        for pct in [0, 31, -5, 10.0, True, None]:
            with self.subTest(pct=pct):
                with self.assertRaises(ValueError):
                    crm.discount(opp, pct, "mgr")
        self.assertEqual(crm.opps[opp]["amount"], 1000)

    def test_rep_limit_and_manager_limit(self):
        crm, opp = self.crm, self.opp
        with self.assertRaises(PermissionError):
            crm.discount(opp, 11, "r2")
        crm.discount(opp, 10, "mgr")
        self.assertEqual(crm.opps[opp]["amount"], 900)
        crm.discount(opp, 10, "mgr")
        self.assertEqual(crm.opps[opp]["amount"], 810)
        crm.discount(opp, 10, "mgr")
        self.assertEqual(crm.opps[opp]["amount"], 729)
        with self.assertRaises(ValueError):
            crm.discount(opp, 10, "mgr")  # 656 < 70% of 1000
        self.assertEqual(crm.opps[opp]["amount"], 729)

    def test_owner_and_final_stage_checks(self):
        crm, opp = self.crm, self.opp
        with self.assertRaises(PermissionError):
            crm.discount(opp, 5, "r2")
        crm.advance(opp, "proposal", "mgr")
        crm.advance(opp, "negotiation", "mgr")
        crm.advance(opp, "won", "mgr")
        with self.assertRaises(ValueError):
            crm.discount(opp, 5, "mgr")

    def test_floor_division(self):
        crm = make()
        lead = crm.add_lead("a@acme.com", "A", "referral", "mgr")
        crm.qualify(lead, "mgr")
        opp = crm.convert(lead, 999, "mgr")
        crm.discount(opp, 3, "mgr")
        self.assertEqual(crm.opps[opp]["amount"], 969)
        self.assertEqual(crm.log[-1], ("discount", opp, "mgr"))


class TestTransfer(unittest.TestCase):
    def setUp(self):
        self.crm = make()
        lead = self.crm.add_lead("a@acme.com", "A", "referral", "mgr")
        self.crm.qualify(lead, "mgr")
        self.opp = self.crm.convert(lead, 1000, "mgr")
        self.assertTrue(self.crm.opps[self.opp]["owner"] == "r1")

    def test_permission_and_arguments(self):
        crm, opp = self.crm, self.opp
        with self.assertRaises(PermissionError):
            crm.transfer(opp, "r2", "r1")
        with self.assertRaises(ValueError):
            crm.transfer("O404", "r2", "mgr")
        with self.assertRaises(ValueError):
            crm.transfer(opp, "ghost", "mgr")
        with self.assertRaises(ValueError):
            crm.transfer(opp, "mgr", "mgr")
        with self.assertRaises(ValueError):
            crm.transfer(opp, "r1", "mgr")
        self.assertEqual(crm.opps[opp]["owner"], "r1")
        self.assertEqual(crm.log, [("add_lead", "L1", "mgr"), ("qualify", "L1", "mgr"), ("convert", opp, "mgr")])

    def test_capacity_and_freeing_previous_slot(self):
        crm, opp = self.crm, self.opp
        # r2 is full (capacity 1) with its own open opportunity
        lead2 = crm.add_lead("b@acme.com", "B", "referral", "mgr")
        crm.qualify(lead2, "mgr")
        crm.convert(lead2, 200, "mgr")
        with self.assertRaises(ValueError):
            crm.transfer(opp, "r2", "mgr")
        crm.transfer(opp, "r3", "mgr")
        self.assertEqual(crm.opps[opp]["owner"], "r3")
        self.assertEqual(crm.log[-1], ("transfer", opp, "mgr"))

    def test_transfer_moves_ownership_and_logs(self):
        crm = make(
            [
                {"id": "r1", "role": "rep", "capacity": 1},
                {"id": "r2", "role": "rep", "capacity": 3},
                {"id": "mgr", "role": "manager", "capacity": 0},
            ]
        )
        lead = crm.add_lead("a@acme.com", "A", "referral", "mgr")
        crm.qualify(lead, "mgr")
        opp = crm.convert(lead, 1000, "mgr")
        self.assertEqual(crm.opps[opp]["owner"], "r1")
        crm.transfer(opp, "r2", "mgr")
        self.assertEqual(crm.opps[opp]["owner"], "r2")
        self.assertEqual(crm.log[-1], ("transfer", opp, "mgr"))
        # the freed slot now allows another lead for r1
        extra = crm.add_lead("b@acme.com", "B", "referral", "mgr")
        self.assertEqual(crm.leads[extra]["owner"], "r1")

    def test_transfer_into_final_stage_rejected(self):
        crm, opp = self.crm, self.opp
        crm.advance(opp, "lost", "mgr")
        with self.assertRaises(ValueError):
            crm.transfer(opp, "r2", "mgr")


class TestForecast(unittest.TestCase):
    def test_forecast_math(self):
        crm = make()
        a = crm.add_lead("a@acme.com", "A", "referral", "mgr")
        b = crm.add_lead("b@acme.com", "B", "referral", "mgr")
        c = crm.add_lead("c@acme.com", "C", "referral", "mgr")
        d = crm.add_lead("d@acme.com", "D", "referral", "mgr")
        for lead in (a, b, c, d):
            crm.qualify(lead, "mgr")
        o1 = crm.convert(a, 1000, "mgr")
        o2 = crm.convert(b, 2000, "mgr")
        o3 = crm.convert(c, 3000, "mgr")
        o4 = crm.convert(d, 4000, "mgr")
        crm.advance(o2, "proposal", "mgr")
        crm.advance(o3, "proposal", "mgr")
        crm.advance(o3, "negotiation", "mgr")
        for stage in ("proposal", "negotiation", "won"):
            crm.advance(o4, stage, "mgr")
        self.assertEqual(
            crm.forecast(),
            {"open": 3, "weighted": 100 + 600 + 1800, "won": 4000},
        )
        self.assertEqual(crm.log[-1][0], "advance")

    def test_forecast_empty_and_no_log(self):
        crm = make()
        self.assertEqual(crm.forecast(), {"open": 0, "weighted": 0, "won": 0})
        self.assertEqual(crm.log, [])

    def test_lost_and_discount_affect_forecast(self):
        crm = make()
        lead = crm.add_lead("a@acme.com", "A", "referral", "mgr")
        crm.qualify(lead, "mgr")
        opp = crm.convert(lead, 200, "mgr")
        crm.discount(opp, 10, "mgr")
        self.assertEqual(crm.forecast(), {"open": 1, "weighted": 18, "won": 0})
        crm.advance(opp, "lost", "mgr")
        self.assertEqual(crm.forecast(), {"open": 0, "weighted": 0, "won": 0})


class TestFailureAtomicity(unittest.TestCase):
    def test_failed_calls_change_nothing(self):
        crm = make()
        lead = crm.add_lead("a@acme.com", "A", "referral", "mgr")
        crm.qualify(lead, "mgr")
        opp = crm.convert(lead, 1000, "mgr")
        before = (repr(crm.leads), repr(crm.opps), list(crm.log), list(crm.waiting))
        failures = [
            lambda: crm.add_lead("a@acme.com", "A", "web", "mgr"),
            lambda: crm.qualify("L9", "mgr"),
            lambda: crm.convert("L9", 5, "mgr"),
            lambda: crm.convert(lead, 0, "mgr"),
            lambda: crm.advance("O9", "won", "mgr"),
            lambda: crm.advance(opp, "won", "r2"),
            lambda: crm.discount(opp, 0, "mgr"),
            lambda: crm.transfer(opp, "r2", "r1"),
            lambda: crm.add_lead("x@acme.com", "X", "web", "ghost"),
        ]
        for call in failures:
            with self.assertRaises((ValueError, PermissionError, DuplicateLeadError)):
                call()
            after = (repr(crm.leads), repr(crm.opps), list(crm.log), list(crm.waiting))
            self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
