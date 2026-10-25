import unittest

from crm import CRM, DuplicateLeadError


def make_crm(reps=None):
    if reps is None:
        reps = [
            {"id": "r1", "role": "rep", "capacity": 2},
            {"id": "r2", "role": "rep", "capacity": 2},
            {"id": "m1", "role": "manager", "capacity": 0},
        ]
    return CRM(reps)


class Base(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()

    def assertNoSideEffects(self, before_log, before_leads, before_opps):
        self.assertEqual(self.crm.log, before_log)
        self.assertEqual(self.crm.leads, before_leads)
        self.assertEqual(self.crm.opps, before_opps)


class TestActors(Base):
    def test_unknown_actor_raises_before_anything_else(self):
        with self.assertRaises(PermissionError):
            self.crm.add_lead("a@b.com", "A", "web", "ghost")
        with self.assertRaises(PermissionError):
            self.crm.qualify("L999", "ghost")
        with self.assertRaises(PermissionError):
            self.crm.convert("L999", 10, "ghost")
        with self.assertRaises(PermissionError):
            self.crm.advance("O999", "proposal", "ghost")
        with self.assertRaises(PermissionError):
            self.crm.discount("O999", 5, "ghost")
        with self.assertRaises(PermissionError):
            self.crm.transfer("O999", "r1", "ghost")
        self.assertEqual(self.crm.log, [])


class TestAddLead(Base):
    def test_normalization_and_fields(self):
        lead_id = self.crm.add_lead("  Bob@Example.COM ", "  Bob  ", "referral", "r1")
        lead = self.crm.leads[lead_id]
        self.assertEqual(lead["email"], "bob@example.com")
        self.assertEqual(lead["name"], "Bob")
        self.assertEqual(lead["score"], 45)  # referral 30 + 15 corporate
        self.assertEqual(lead["status"], "new")
        self.assertEqual(lead["owner"], "r1")
        self.assertEqual(self.crm.log, [("add_lead", lead_id, "r1")])

    def test_scores(self):
        self.assertEqual(
            self.crm.leads[self.crm.add_lead("a@gmail.com", "A", "web", "r1")]["score"], 10
        )
        self.assertEqual(
            self.crm.leads[self.crm.add_lead("b@yahoo.com", "B", "event", "r1")]["score"], 20
        )
        self.assertEqual(
            self.crm.leads[self.crm.add_lead("c@outlook.com", "C", "referral", "r1")]["score"], 30
        )
        self.assertEqual(
            self.crm.leads[self.crm.add_lead("d@corp.io", "D", "web", "r1")]["score"], 25
        )

    def test_bad_emails(self):
        for email in ["a@b", "a@@b.com", "@b.com", "a@.com", "a@com.", "plain", 5, None]:
            with self.assertRaises(ValueError):
                self.crm.add_lead(email, "A", "web", "r1")

    def test_bad_name_and_source(self):
        for name in ["", "   ", 3]:
            with self.assertRaises(ValueError):
                self.crm.add_lead("a@b.com", name, "web", "r1")
        with self.assertRaises(ValueError):
            self.crm.add_lead("a@b.com", "A", "phone", "r1")

    def test_duplicate_normalized_email(self):
        first = self.crm.add_lead("a@b.com", "A", "web", "r1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            self.crm.add_lead(" A@B.COM ", "A2", "web", "r2")
        self.assertEqual(ctx.exception.existing_id, first)
        self.assertEqual(len(self.crm.leads), 1)
        self.assertEqual(len(self.crm.log), 1)

    def test_ids_count_only_successes(self):
        with self.assertRaises(ValueError):
            self.crm.add_lead("bad", "A", "web", "r1")
        self.assertEqual(self.crm.add_lead("a@b.com", "A", "web", "r1"), "L1")
        self.assertEqual(self.crm.add_lead("c@d.com", "C", "web", "r2"), "L2")

    def test_manager_never_owns(self):
        crm = make_crm([{"id": "m1", "role": "manager", "capacity": 5}])
        lead_id = crm.add_lead("a@b.com", "A", "web", "m1")
        self.assertIsNone(crm.leads[lead_id]["owner"])
        self.assertEqual(crm.waiting, [lead_id])

    def test_load_balancing_ties_by_id(self):
        lead_ids = [
            self.crm.add_lead("%s@x.com" % name, name, "web", "r1")
            for name in ["a", "b", "c", "d", "e"]
        ]
        owners = [self.crm.leads[i]["owner"] for i in lead_ids]
        self.assertEqual(owners, ["r1", "r2", "r1", "r2", None])
        self.assertEqual(self.crm.waiting, ["L5"])


class TestQualifyAndConvert(Base):
    def test_qualify_rules(self):
        lead_id = self.crm.add_lead("a@b.com", "A", "web", "r1")  # score 10
        with self.assertRaises(ValueError):
            self.crm.qualify("L999", "r1")  # unknown lead
        with self.assertRaises(PermissionError):
            self.crm.qualify(lead_id, "r2")
        with self.assertRaises(ValueError):
            self.crm.qualify(lead_id, "r1")  # score too low
        with self.assertRaises(ValueError):
            self.crm.qualify(lead_id, "m1")  # managers bypass ownership, not score
        self.assertEqual(self.crm.leads[lead_id]["status"], "new")

    def test_qualify_success_and_status(self):
        lead_id = self.crm.add_lead("a@corp.io", "A", "referral", "r1")  # 45
        self.crm.qualify(lead_id, "r1")
        self.assertEqual(self.crm.leads[lead_id]["status"], "qualified")
        self.assertEqual(self.crm.log[-1], ("qualify", lead_id, "r1"))
        with self.assertRaises(ValueError):
            self.crm.qualify(lead_id, "r1")

    def test_convert_rules_and_opp(self):
        lead_id = self.crm.add_lead("a@corp.io", "A", "referral", "r1")
        self.crm.qualify(lead_id, "r1")
        for bad in [0, -5, True, False, 1.5, "10"]:
            with self.assertRaises(ValueError):
                self.crm.convert(lead_id, bad, "r1")
        with self.assertRaises(PermissionError):
            self.crm.convert(lead_id, 100, "r2")
        opp_id = self.crm.convert(lead_id, 100, "r1")
        self.assertEqual(opp_id, "O1")
        self.assertEqual(
            self.crm.opps[opp_id],
            {
                "id": "O1",
                "lead_id": lead_id,
                "owner": "r1",
                "amount": 100,
                "original_amount": 100,
                "stage": "prospect",
            },
        )
        self.assertEqual(self.crm.leads[lead_id]["status"], "converted")
        self.assertEqual(self.crm.log[-1], ("convert", opp_id, "r1"))
        with self.assertRaises(ValueError):
            self.crm.convert(lead_id, 100, "r1")

    def test_convert_requires_qualified_and_owner(self):
        lead_id = self.crm.add_lead("a@corp.io", "A", "referral", "r1")
        with self.assertRaises(ValueError):
            self.crm.convert(lead_id, 100, "r1")  # still new
        crm = make_crm([{"id": "m1", "role": "manager", "capacity": 0}])
        lead_id = crm.add_lead("a@corp.io", "A", "referral", "m1")
        crm.qualify(lead_id, "m1")
        with self.assertRaises(ValueError):
            crm.convert(lead_id, 100, "m1")  # waiting lead has no owner


class TestAdvance(Base):
    def setUp(self):
        super().setUp()
        self.lead_id = self.crm.add_lead("a@corp.io", "A", "referral", "r1")
        self.crm.qualify(self.lead_id, "r1")

    def test_stage_order(self):
        opp = self.crm.convert(self.lead_id, 1000, "r1")
        with self.assertRaises(ValueError):
            self.crm.advance(opp, "negotiation", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance(opp, "won", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance(opp, "bogus", "r1")
        self.crm.advance(opp, "proposal", "r1")
        self.crm.advance(opp, "negotiation", "r1")
        self.crm.advance(opp, "won", "r1")
        self.assertEqual(self.crm.opps[opp]["stage"], "won")
        with self.assertRaises(ValueError):
            self.crm.advance(opp, "lost", "r1")

    def test_permissions(self):
        opp = self.crm.convert(self.lead_id, 1000, "r1")
        with self.assertRaises(PermissionError):
            self.crm.advance(opp, "proposal", "r2")
        self.crm.advance(opp, "proposal", "m1")  # managers may advance

    def test_negotiation_over_50k_needs_manager(self):
        opp = self.crm.convert(self.lead_id, 60000, "r1")
        self.crm.advance(opp, "proposal", "r1")
        with self.assertRaises(PermissionError):
            self.crm.advance(opp, "negotiation", "r1")
        self.crm.advance(opp, "negotiation", "m1")
        self.assertEqual(self.crm.opps[opp]["stage"], "negotiation")

    def test_exactly_50k_allowed_for_rep(self):
        opp = self.crm.convert(self.lead_id, 50000, "r1")
        self.crm.advance(opp, "proposal", "r1")
        self.crm.advance(opp, "negotiation", "r1")

    def test_lost_is_allowed_from_any_open_stage(self):
        opp = self.crm.convert(self.lead_id, 1000, "r1")
        self.crm.advance(opp, "lost", "r1")
        self.assertEqual(self.crm.opps[opp]["stage"], "lost")


class TestWaitingQueue(Base):
    def setUp(self):
        self.crm = make_crm(
            [
                {"id": "r1", "role": "rep", "capacity": 1},
                {"id": "r2", "role": "rep", "capacity": 1},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )

    def test_assign_on_win(self):
        first = self.crm.add_lead("a@corp.io", "A", "referral", "r1")
        second = self.crm.add_lead("b@corp.io", "B", "referral", "r1")
        waiting = self.crm.add_lead("c@corp.io", "C", "referral", "r1")
        self.assertEqual(self.crm.leads[waiting]["owner"], None)
        self.crm.qualify(first, "r1")
        opp = self.crm.convert(first, 1000, "r1")
        self.crm.advance(opp, "proposal", "r1")
        self.crm.advance(opp, "negotiation", "r1")
        self.crm.advance(opp, "won", "r1")
        self.assertEqual(self.crm.leads[waiting]["owner"], "r1")
        self.assertEqual(self.crm.log[-1], ("assign", waiting, "system"))
        self.assertEqual(self.crm.waiting, [])

    def test_fifo_order(self):
        a = self.crm.add_lead("a@corp.io", "A", "referral", "r1")
        self.crm.add_lead("b@corp.io", "B", "referral", "r1")
        w1 = self.crm.add_lead("c@corp.io", "C", "referral", "r1")
        w2 = self.crm.add_lead("d@corp.io", "D", "referral", "r1")
        self.crm.qualify(a, "r1")
        opp = self.crm.convert(a, 1000, "r1")
        self.crm.advance(opp, "lost", "r1")
        self.assertEqual(self.crm.waiting, [w2])
        self.assertEqual(self.crm.leads[w1]["owner"], "r1")

    def test_lost_frees_slot(self):
        a = self.crm.add_lead("a@corp.io", "A", "referral", "r1")
        self.crm.add_lead("b@corp.io", "B", "referral", "r2")
        waiting = self.crm.add_lead("c@corp.io", "C", "referral", "r1")
        self.assertEqual(self.crm.leads[waiting]["owner"], None)
        self.crm.qualify(a, "r1")
        opp = self.crm.convert(a, 1000, "r1")
        self.crm.advance(opp, "proposal", "r1")
        self.crm.advance(opp, "lost", "r1")
        self.assertEqual(self.crm.leads[waiting]["owner"], "r1")


class TestDiscount(Base):
    def setUp(self):
        super().setUp()
        lead = self.crm.add_lead("a@corp.io", "A", "referral", "r1")
        self.crm.qualify(lead, "r1")
        self.opp = self.crm.convert(lead, 1000, "r1")

    def test_validation(self):
        for bad in [0, 31, -1, True, 1.0, "5"]:
            with self.assertRaises(ValueError):
                self.crm.discount(self.opp, bad, "r1")
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp, 5, "r2")
        with self.assertRaises(ValueError):
            self.crm.discount("O999", 5, "r1")

    def test_non_manager_cap(self):
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp, 11, "r1")
        self.crm.discount(self.opp, 10, "r1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 900)
        self.assertEqual(self.crm.log[-1], ("discount", self.opp, "r1"))

    def test_cumulative_floor(self):
        self.crm.discount(self.opp, 30, "m1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 700)
        before = dict(self.crm.opps[self.opp])
        log = list(self.crm.log)
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp, 1, "m1")
        self.assertEqual(self.crm.opps[self.opp], before)
        self.assertEqual(self.crm.log, log)

    def test_cannot_discount_final_stage(self):
        self.crm.advance(self.opp, "proposal", "r1")
        self.crm.advance(self.opp, "negotiation", "r1")
        self.crm.advance(self.opp, "won", "r1")
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp, 10, "m1")


class TestTransfer(Base):
    def setUp(self):
        super().setUp()
        lead = self.crm.add_lead("a@corp.io", "A", "referral", "r1")
        self.crm.qualify(lead, "r1")
        self.opp = self.crm.convert(lead, 1000, "r1")

    def test_rules(self):
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.opp, "r2", "r1")
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "ghost", "m1")
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "m1", "m1")
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "r1", "m1")
        self.crm.transfer(self.opp, "r2", "m1")
        self.assertEqual(self.crm.opps[self.opp]["owner"], "r2")
        self.assertEqual(self.crm.log[-1], ("transfer", self.opp, "m1"))

    def test_transfer_respects_capacity(self):
        self.crm.add_lead("b@corp.io", "B", "web", "r2")
        self.crm.add_lead("c@corp.io", "C", "web", "r1")
        self.crm.add_lead("d@corp.io", "D", "web", "r2")
        # r2 now at capacity 2
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "r2", "m1")
        self.assertEqual(self.crm.opps[self.opp]["owner"], "r1")

    def test_transfer_to_rep_with_room(self):
        self.crm.add_lead("b@corp.io", "B", "web", "r2")
        self.crm.transfer(self.opp, "r2", "m1")
        self.assertEqual(self.crm.opps[self.opp]["owner"], "r2")

    def test_transfer_frees_previous_capacity_check(self):
        # After a transfer, the previous owner's load drops by one, so it can
        # accept further work again.
        crm = make_crm(
            [
                {"id": "r1", "role": "rep", "capacity": 1},
                {"id": "r2", "role": "rep", "capacity": 1},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        lead = crm.add_lead("a@corp.io", "A", "referral", "r1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 1000, "r1")
        crm.transfer(opp, "r2", "m1")
        self.assertEqual(crm._load("r1"), 0)
        self.assertEqual(crm._load("r2"), 1)

    def test_cannot_transfer_final(self):
        self.crm.advance(self.opp, "proposal", "r1")
        self.crm.advance(self.opp, "negotiation", "r1")
        self.crm.advance(self.opp, "won", "r1")
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "r2", "m1")


class TestForecast(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm(
            [
                {"id": "r1", "role": "rep", "capacity": 10},
                {"id": "r2", "role": "rep", "capacity": 10},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )

    def test_empty(self):
        self.assertEqual(self.crm.forecast(), {"open": 0, "weighted": 0, "won": 0})

    def test_weighted(self):
        def make_opp(email, amount):
            lead = self.crm.add_lead(email, "N", "referral", "r1")
            self.crm.qualify(lead, "m1")
            return self.crm.convert(lead, amount, "m1")

        p = make_opp("a@corp.io", 1000)  # prospect -> 100
        pr = make_opp("b@corp.io", 2000)  # proposal -> 600
        self.crm.advance(pr, "proposal", "m1")
        ne = make_opp("c@corp.io", 3000)  # negotiation -> 1800
        self.crm.advance(ne, "proposal", "m1")
        self.crm.advance(ne, "negotiation", "m1")
        w = make_opp("d@corp.io", 4000)  # won -> 4000
        self.crm.advance(w, "proposal", "m1")
        self.crm.advance(w, "negotiation", "m1")
        self.crm.advance(w, "won", "m1")
        lost = make_opp("e@corp.io", 5000)
        self.crm.advance(lost, "lost", "m1")

        self.assertEqual(
            self.crm.forecast(),
            {"open": 3, "weighted": 100 + 600 + 1800, "won": 4000},
        )

    def test_forecast_ignores_actor_and_logs_nothing(self):
        lead = self.crm.add_lead("a@corp.io", "A", "referral", "r1")
        self.crm.qualify(lead, "r1")
        opp = self.crm.convert(lead, 1000, "r1")
        before = list(self.crm.log)
        self.crm.forecast()
        self.assertEqual(self.crm.log, before)
        self.assertEqual(self.crm.opps[opp]["stage"], "prospect")


class TestAtomicFailures(Base):
    def test_failed_calls_change_nothing(self):
        lead = self.crm.add_lead("a@corp.io", "A", "referral", "r1")
        self.crm.qualify(lead, "r1")
        opp = self.crm.convert(lead, 1000, "r1")
        self.crm.advance(opp, "proposal", "r1")

        before = (list(self.crm.log), {k: dict(v) for k, v in self.crm.leads.items()}, {k: dict(v) for k, v in self.crm.opps.items()})
        attempts = [
            lambda: self.crm.qualify("L999", "r1"),
            lambda: self.crm.convert(lead, 0, "r1"),
            lambda: self.crm.advance(opp, "won", "r1"),
            lambda: self.crm.discount(opp, 99, "m1"),
            lambda: self.crm.transfer(opp, "m1", "m1"),
            lambda: self.crm.add_lead("bad", "X", "web", "r1"),
        ]
        for attempt in attempts:
            with self.assertRaises(Exception):
                attempt()
        after = (list(self.crm.log), {k: dict(v) for k, v in self.crm.leads.items()}, {k: dict(v) for k, v in self.crm.opps.items()})
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
