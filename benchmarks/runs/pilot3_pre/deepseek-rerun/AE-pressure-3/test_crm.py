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

    def test_waiting_queue_is_fifo_and_skips_managers(self):
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

    def test_requires_new_status_and_score_of_30(self):
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


if __name__ == "__main__":
    unittest.main()
