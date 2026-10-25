import unittest

import crm
from crm import CRM, DuplicateLeadError


def make_crm(**overrides):
    reps = [
        {"id": "r1", "role": "rep", "capacity": 2},
        {"id": "r2", "role": "rep", "capacity": 2},
        {"id": "r3", "role": "rep", "capacity": 2},
        {"id": "m1", "role": "manager", "capacity": 2},
    ]
    for rep in reps:
        rep.update(overrides.get(rep["id"], {}))
    return CRM(reps)


class EmailValidationTests(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()

    def test_email_must_be_str(self):
        for bad in (None, 5, b"a@b.com", ["a@b.com"]):
            with self.assertRaises(ValueError):
                self.crm.add_lead(bad, "Ann", "web", "r1")
        self.assertEqual(self.crm.leads, {})
        self.assertEqual(self.crm.log, [])

    def test_email_shapes(self):
        bad = [
            "plainaddress",
            "a@@b.com",
            "a@b@c.com",
            "@b.com",
            "  @b.com  ",
            "a@bcom",
            "a@.com",
            "a@com.",
            "a@b.",
            "a@b.com.",
            "a@b..",
        ]
        for email in bad:
            with self.assertRaises(ValueError):
                self.crm.add_lead(email, "Ann", "web", "r1")

    def test_email_normalized(self):
        lead_id = self.crm.add_lead("  Ann@Example.COM  ", "  Ann Lee  ", "web", "r1")
        lead = self.crm.leads[lead_id]
        self.assertEqual(lead["email"], "ann@example.com")
        self.assertEqual(lead["name"], "Ann Lee")


class AddLeadTests(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()

    def test_name_and_source_validation(self):
        for name in ("", "   ", None, 3):
            with self.assertRaises(ValueError):
                self.crm.add_lead("a@b.com", name, "web", "r1")
        for source in ("WEB", "phone", None, ""):
            with self.assertRaises(ValueError):
                self.crm.add_lead("a@b.com", "Ann", source, "r1")
        self.assertEqual(self.crm.leads, {})
        self.assertEqual(self.crm.log, [])

    def test_unknown_actor_checked_first(self):
        with self.assertRaises(PermissionError):
            self.crm.add_lead("not-an-email", "", "nope", "ghost")

    def test_scores(self):
        cases = [
            ("u1@gmail.com", "web", 10),
            ("u2@corp.com", "web", 25),
            ("u3@yahoo.com", "referral", 30),
            ("u4@outlook.com", "event", 20),
            ("u5@corp.com", "event", 35),
            ("u6@corp.com", "referral", 45),
        ]
        for email, source, expected in cases:
            lead_id = self.crm.add_lead(email, "Ann", source, "r1")
            self.assertEqual(self.crm.leads[lead_id]["score"], expected, email)

    def test_lead_structure_and_log(self):
        lead_id = self.crm.add_lead("Ann@Corp.com", " Ann ", "event", "m1")
        self.assertEqual(lead_id, "L1")
        self.assertEqual(
            self.crm.leads[lead_id],
            {
                "id": "L1",
                "email": "ann@corp.com",
                "name": "Ann",
                "source": "event",
                "score": 35,
                "owner": "r1",
                "status": "new",
            },
        )
        self.assertEqual(self.crm.log, [("add_lead", "L1", "m1")])

    def test_duplicate_raises_with_existing_id(self):
        first = self.crm.add_lead("dup@corp.com", "Ann", "web", "r1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            self.crm.add_lead("  DUP@corp.com ", "Other", "event", "r1")
        self.assertEqual(ctx.exception.existing_id, first)
        self.assertEqual(len(self.crm.leads), 1)
        self.assertEqual(len(self.crm.log), 1)
        # a failed creation does not consume an id
        self.assertEqual(self.crm.add_lead("new@corp.com", "New", "web", "r1"), "L2")

    def test_duplicate_checked_after_email_name_source(self):
        self.crm.add_lead("dup@corp.com", "Ann", "web", "r1")
        with self.assertRaises(ValueError):
            self.crm.add_lead("dup@corp.com", "", "web", "r1")
        with self.assertRaises(ValueError):
            self.crm.add_lead("dup@corp.com", "Ann", "phone", "r1")
        with self.assertRaises(DuplicateLeadError):
            self.crm.add_lead("dup@corp.com", "Ann", "web", "r1")

    def test_assignment_lowest_load_then_id(self):
        self.assertEqual(self.crm.add_lead("a@x.com", "A", "web", "r1"), "L1")
        self.assertEqual(self.crm.leads["L1"]["owner"], "r1")  # tie -> smallest id
        self.crm.add_lead("b@x.com", "B", "web", "r1")
        self.assertEqual(self.crm.leads["L2"]["owner"], "r2")
        self.crm.add_lead("c@x.com", "C", "web", "r1")
        self.assertEqual(self.crm.leads["L3"]["owner"], "r3")
        self.crm.add_lead("d@x.com", "D", "web", "r1")
        self.assertEqual(self.crm.leads["L4"]["owner"], "r1")

    def test_managers_never_own(self):
        self.crm.add_lead("a@x.com", "A", "web", "r1")
        owners = {lead["owner"] for lead in self.crm.leads.values()}
        self.assertNotIn("m1", owners)

    def test_queue_when_all_full(self):
        small = make_crm(r1={"capacity": 1}, r2={"capacity": 1}, r3={"capacity": 1})
        for i, email in enumerate(["a@x.com", "b@x.com", "c@x.com", "d@x.com"]):
            small.add_lead(email, "N%d" % i, "web", "r1")
        self.assertEqual(small.leads["L4"]["owner"], None)
        self.assertEqual(small.waiting, ["L4"])

    def test_capacity_zero_rep_never_owns(self):
        small = make_crm(r1={"capacity": 0}, r2={"capacity": 1}, r3={"capacity": 0})
        small.add_lead("a@x.com", "A", "web", "r1")
        self.assertEqual(small.leads["L1"]["owner"], "r2")
        small.add_lead("b@x.com", "B", "web", "r1")
        self.assertIsNone(small.leads["L2"]["owner"])


class QualifyTests(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()

    def test_unknown_lead(self):
        with self.assertRaises(ValueError):
            self.crm.qualify("L99", "m1")

    def test_permission(self):
        lead_id = self.crm.add_lead("a@corp.com", "Ann", "event", "r1")
        with self.assertRaises(PermissionError):
            self.crm.qualify(lead_id, "r2")
        self.crm.qualify(lead_id, "m1")
        self.assertEqual(self.crm.leads[lead_id]["status"], "qualified")

    def test_owner_may_qualify(self):
        lead_id = self.crm.add_lead("a@corp.com", "Ann", "event", "r1")
        self.crm.qualify(lead_id, "r1")
        self.assertEqual(self.crm.leads[lead_id]["status"], "qualified")
        self.assertEqual(self.crm.log[-1], ("qualify", lead_id, "r1"))

    def test_status_must_be_new(self):
        lead_id = self.crm.add_lead("a@corp.com", "Ann", "event", "r1")
        self.crm.qualify(lead_id, "r1")
        with self.assertRaises(ValueError):
            self.crm.qualify(lead_id, "r1")
        self.assertEqual(self.crm.log.count(("qualify", lead_id, "r1")), 1)

    def test_score_threshold(self):
        low = self.crm.add_lead("a@gmail.com", "Ann", "web", "r1")  # 10
        with self.assertRaises(ValueError):
            self.crm.qualify(low, "r1")
        self.assertEqual(self.crm.leads[low]["status"], "new")

    def test_freemail_referral_can_qualify(self):
        lead_id = self.crm.add_lead("a@gmail.com", "Ann", "referral", "r1")  # 30
        self.crm.qualify(lead_id, "r1")
        self.assertEqual(self.crm.leads[lead_id]["status"], "qualified")

    def test_unowned_lead_qualifies_only_for_manager(self):
        small = make_crm(r1={"capacity": 1}, r2={"capacity": 0}, r3={"capacity": 0})
        small.add_lead("a@corp.com", "A", "event", "r1")
        queued = small.add_lead("b@corp.com", "B", "event", "r1")
        with self.assertRaises(PermissionError):
            small.qualify(queued, "r1")
        small.qualify(queued, "m1")
        self.assertEqual(small.leads[queued]["status"], "qualified")


class ConvertTests(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        self.lead = self.crm.add_lead("a@corp.com", "Ann", "event", "r1")
        self.crm.qualify(self.lead, "r1")

    def test_unknown_lead(self):
        with self.assertRaises(ValueError):
            self.crm.convert("L42", 100, "m1")

    def test_amount_validation(self):
        for bad in (0, -5, True, False, 1.5, "10", None):
            with self.assertRaises(ValueError):
                self.crm.convert(self.lead, bad, "r1")
        self.assertEqual(self.crm.opps, {})

    def test_permission(self):
        with self.assertRaises(PermissionError):
            self.crm.convert(self.lead, 100, "r2")
        with self.assertRaises(PermissionError):
            self.crm.convert(self.lead, 100, "ghost")

    def test_status_must_be_qualified(self):
        other = self.crm.add_lead("b@corp.com", "Bob", "web", "r2")
        with self.assertRaises(ValueError):
            self.crm.convert(other, 100, "r2")

    def test_success(self):
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
        self.assertEqual(self.crm.log[-1], ("convert", "O1", "r1"))

    def test_manager_may_convert(self):
        opp_id = self.crm.convert(self.lead, 50, "m1")
        self.assertEqual(self.crm.opps[opp_id]["owner"], "r1")

    def test_unowned_qualified_lead_cannot_convert(self):
        small = make_crm(r1={"capacity": 0}, r2={"capacity": 0}, r3={"capacity": 0})
        lead = small.add_lead("a@corp.com", "A", "event", "m1")
        small.qualify(lead, "m1")
        with self.assertRaises(ValueError):
            small.convert(lead, 100, "m1")
        self.assertEqual(small.opps, {})

    def test_second_conversion_gets_next_id(self):
        self.crm.convert(self.lead, 100, "r1")
        lead2 = self.crm.add_lead("b@corp.com", "B", "event", "r2")
        self.crm.qualify(lead2, "r2")
        self.assertEqual(self.crm.convert(lead2, 200, "r2"), "O2")


class AdvanceTests(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        lead = self.crm.add_lead("a@corp.com", "Ann", "event", "r1")
        self.crm.qualify(lead, "r1")
        self.opp = self.crm.convert(lead, 1000, "r1")

    def test_unknown_opp(self):
        with self.assertRaises(ValueError):
            self.crm.advance("O9", "proposal", "m1")

    def test_bad_stage_value(self):
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "closed", "r1")

    def test_permission(self):
        with self.assertRaises(PermissionError):
            self.crm.advance(self.opp, "proposal", "r2")

    def test_order_enforced(self):
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "negotiation", "r1")
        self.crm.advance(self.opp, "proposal", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "proposal", "r1")

    def test_full_ladder_and_final(self):
        self.crm.advance(self.opp, "proposal", "r1")
        self.crm.advance(self.opp, "negotiation", "r1")
        self.crm.advance(self.opp, "won", "r1")
        self.assertEqual(self.crm.opps[self.opp]["stage"], "won")
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "lost", "r1")
        self.assertEqual(
            self.crm.log[-1], ("advance", self.opp, "r1")
        )

    def test_lost_from_any_open_stage(self):
        self.crm.advance(self.opp, "proposal", "r1")
        self.crm.advance(self.opp, "lost", "r1")
        self.assertEqual(self.crm.opps[self.opp]["stage"], "lost")

    def test_large_deal_needs_manager_for_negotiation(self):
        big_lead = self.crm.add_lead("big@corp.com", "Big", "event", "r2")
        self.crm.qualify(big_lead, "r2")
        big = self.crm.convert(big_lead, 50001, "r2")
        self.crm.advance(big, "proposal", "r2")
        with self.assertRaises(PermissionError):
            self.crm.advance(big, "negotiation", "r2")
        self.assertEqual(self.crm.opps[big]["stage"], "proposal")
        self.crm.advance(big, "negotiation", "m1")
        self.assertEqual(self.crm.opps[big]["stage"], "negotiation")

    def test_exactly_50000_allowed_for_owner(self):
        lead = self.crm.add_lead("edge@corp.com", "Edge", "event", "r2")
        self.crm.qualify(lead, "r2")
        opp = self.crm.convert(lead, 50000, "r2")
        self.crm.advance(opp, "proposal", "r2")
        self.crm.advance(opp, "negotiation", "r2")
        self.assertEqual(self.crm.opps[opp]["stage"], "negotiation")

    def test_final_stage_frees_slot_and_assigns_fifo(self):
        small = make_crm(r1={"capacity": 1}, r2={"capacity": 0}, r3={"capacity": 0})
        lead = small.add_lead("a@corp.com", "A", "referral", "r1")
        small.qualify(lead, "r1")
        opp = small.convert(lead, 500, "r1")
        waiting1 = small.add_lead("w1@corp.com", "W1", "referral", "m1")
        waiting2 = small.add_lead("w2@corp.com", "W2", "referral", "m1")
        self.assertIsNone(small.leads[waiting1]["owner"])
        self.assertIsNone(small.leads[waiting2]["owner"])

        small.advance(opp, "lost", "r1")
        self.assertEqual(small.leads[waiting1]["owner"], "r1")
        self.assertIsNone(small.leads[waiting2]["owner"])
        self.assertEqual(small.log[-1], ("assign", waiting1, "system"))
        self.assertEqual(small.waiting, [waiting2])

    def test_no_assign_when_not_final(self):
        small = make_crm(r1={"capacity": 1}, r2={"capacity": 0}, r3={"capacity": 0})
        lead = small.add_lead("a@corp.com", "A", "referral", "r1")
        small.qualify(lead, "r1")
        opp = small.convert(lead, 500, "r1")
        waiting = small.add_lead("w@corp.com", "W", "web", "m1")
        small.advance(opp, "proposal", "r1")
        self.assertIsNone(small.leads[waiting]["owner"])


class DiscountTests(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        lead = self.crm.add_lead("a@corp.com", "Ann", "event", "r1")
        self.crm.qualify(lead, "r1")
        self.opp = self.crm.convert(lead, 10000, "r1")

    def test_unknown_opp(self):
        with self.assertRaises(ValueError):
            self.crm.discount("O77", 5, "m1")

    def test_pct_validation(self):
        for bad in (0, 31, -1, True, 5.0, "5", None):
            with self.assertRaises(ValueError):
                self.crm.discount(self.opp, bad, "r1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 10000)

    def test_permission(self):
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp, 5, "r2")

    def test_final_stage_rejected(self):
        self.crm.advance(self.opp, "lost", "r1")
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp, 5, "m1")

    def test_rep_limited_to_ten(self):
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp, 11, "r1")
        self.crm.discount(self.opp, 10, "r1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 9000)
        self.assertEqual(self.crm.log[-1], ("discount", self.opp, "r1"))

    def test_manager_up_to_thirty(self):
        self.crm.discount(self.opp, 30, "m1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 7000)

    def test_cumulative_cap(self):
        self.crm.discount(self.opp, 20, "m1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 8000)
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp, 20, "m1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 8000)
        self.crm.discount(self.opp, 10, "m1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 7200)
        self.crm.discount(self.opp, 2, "m1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 7056)
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp, 2, "m1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 7056)
        self.assertEqual(self.crm.opps[self.opp]["original_amount"], 10000)

    def test_floor_rounding(self):
        lead = self.crm.add_lead("b@corp.com", "B", "event", "r2")
        self.crm.qualify(lead, "r2")
        opp = self.crm.convert(lead, 999, "r2")
        self.crm.discount(opp, 10, "r2")
        self.assertEqual(self.crm.opps[opp]["amount"], 899)


class TransferTests(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        lead = self.crm.add_lead("a@corp.com", "Ann", "event", "r1")
        self.crm.qualify(lead, "r1")
        self.opp = self.crm.convert(lead, 1000, "r1")

    def test_unknown_opp(self):
        with self.assertRaises(ValueError):
            self.crm.transfer("O12", "r2", "m1")

    def test_manager_only(self):
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.opp, "r2", "r1")

    def test_target_must_be_rep(self):
        for bad in ("m1", "ghost", None, 7):
            with self.assertRaises(ValueError):
                self.crm.transfer(self.opp, bad, "m1")

    def test_same_owner_rejected(self):
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "r1", "m1")

    def test_final_stage_rejected(self):
        self.crm.advance(self.opp, "lost", "r1")
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "r2", "m1")

    def test_capacity_enforced(self):
        small = make_crm(r1={"capacity": 1}, r2={"capacity": 1}, r3={"capacity": 0})
        lead = small.add_lead("a@corp.com", "A", "referral", "r1")
        small.qualify(lead, "r1")
        opp = small.convert(lead, 100, "r1")
        small.add_lead("b@corp.com", "B", "referral", "r1")  # goes to r2 (load 0)
        with self.assertRaises(ValueError):
            small.transfer(opp, "r2", "m1")  # r2 now full
        self.assertEqual(small.opps[opp]["owner"], "r1")

    def test_success_frees_previous_owner(self):
        small = make_crm(r1={"capacity": 1}, r2={"capacity": 1}, r3={"capacity": 0})
        lead = small.add_lead("a@corp.com", "A", "referral", "r1")
        small.qualify(lead, "r1")
        opp = small.convert(lead, 100, "r1")
        self.assertEqual(small._load("r1"), 1)

        small.transfer(opp, "r2", "m1")
        self.assertEqual(small.opps[opp]["owner"], "r2")
        self.assertEqual(small.log[-1], ("transfer", opp, "m1"))
        self.assertEqual(small._load("r1"), 0)
        fresh = small.add_lead("b@corp.com", "B", "event", "m1")
        self.assertEqual(small.leads[fresh]["owner"], "r1")

    def test_transfer_does_not_reassign_previous_owner_twice(self):
        small = make_crm(r1={"capacity": 3}, r2={"capacity": 3}, r3={"capacity": 3})
        lead = small.add_lead("a@corp.com", "A", "referral", "r1")
        small.qualify(lead, "r1")
        opp = small.convert(lead, 100, "r1")
        small.transfer(opp, "r2", "m1")
        self.assertEqual(small.waiting, [])
        self.assertEqual(
            [entry for entry in small.log if entry[0] == "assign"], []
        )


class ForecastTests(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()

    def test_empty(self):
        self.assertEqual(self.crm.forecast(), {"open": 0, "weighted": 0, "won": 0})

    def test_weighted_and_won(self):
        self.crm = make_crm(r1={"capacity": 10}, r2={"capacity": 10}, r3={"capacity": 0})
        lead1 = self.crm.add_lead("a@corp.com", "A", "event", "r1")
        self.crm.qualify(lead1, "r1")
        prospect = self.crm.convert(lead1, 1000, "r1")

        lead2 = self.crm.add_lead("b@corp.com", "B", "event", "r2")
        self.crm.qualify(lead2, "r2")
        proposal = self.crm.convert(lead2, 5000, "r2")
        self.crm.advance(proposal, "proposal", "r2")

        lead3 = self.crm.add_lead("c@corp.com", "C", "event", "r1")
        self.crm.qualify(lead3, "r1")
        negotiation = self.crm.convert(lead3, 1001, "r1")
        self.crm.advance(negotiation, "proposal", "r1")
        self.crm.advance(negotiation, "negotiation", "r1")

        lead4 = self.crm.add_lead("d@corp.com", "D", "event", "r2")
        self.crm.qualify(lead4, "r2")
        won = self.crm.convert(lead4, 777, "r2")
        self.crm.advance(won, "proposal", "r2")
        self.crm.advance(won, "negotiation", "r2")
        self.crm.advance(won, "won", "r2")

        lead5 = self.crm.add_lead("e@corp.com", "E", "event", "r1")
        self.crm.qualify(lead5, "r2")
        lost = self.crm.convert(lead5, 9999, "r2")
        self.crm.advance(lost, "lost", "r2")

        expected_weighted = 1000 * 10 // 100 + 5000 * 30 // 100 + 1001 * 60 // 100
        self.assertEqual(
            self.crm.forecast(),
            {"open": 3, "weighted": expected_weighted, "won": 777},
        )
        self.assertEqual(prospect, "O1")

    def test_forecast_uses_discounted_amount(self):
        lead = self.crm.add_lead("a@corp.com", "A", "event", "r1")
        self.crm.qualify(lead, "r1")
        opp = self.crm.convert(lead, 1000, "r1")
        self.crm.discount(opp, 10, "r1")
        self.assertEqual(self.crm.forecast()["weighted"], 90)

    def test_forecast_adds_no_log(self):
        lead = self.crm.add_lead("a@corp.com", "A", "event", "r1")
        self.crm.qualify(lead, "r1")
        self.crm.convert(lead, 10, "r1")
        before = list(self.crm.log)
        self.crm.forecast()
        self.assertEqual(self.crm.log, before)


class LogAndAtomicityTests(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        lead = self.crm.add_lead("a@corp.com", "Ann", "event", "r1")
        self.crm.qualify(lead, "r1")
        self.opp = self.crm.convert(lead, 1000, "r1")

    def test_failed_calls_are_atomic(self):
        before_opps = {key: dict(value) for key, value in self.crm.opps.items()}
        before_leads = {key: dict(value) for key, value in self.crm.leads.items()}
        before_log = list(self.crm.log)
        before_waiting = list(self.crm.waiting)

        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "won", "r1")
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp, 50, "m1")
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "r9", "m1")
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp, 5, "r3")

        self.assertEqual(self.crm.opps, before_opps)
        self.assertEqual(self.crm.leads, before_leads)
        self.assertEqual(self.crm.log, before_log)
        self.assertEqual(self.crm.waiting, before_waiting)

    def test_unknown_actor_first_everywhere(self):
        calls = [
            lambda: self.crm.qualify("nope", "ghost"),
            lambda: self.crm.convert("nope", -1, "ghost"),
            lambda: self.crm.advance("nope", "bogus", "ghost"),
            lambda: self.crm.discount("nope", 999, "ghost"),
            lambda: self.crm.transfer("nope", "ghost", "ghost"),
        ]
        for call in calls:
            with self.assertRaises(PermissionError):
                call()

    def test_log_is_tuple_triples(self):
        for entry in self.crm.log:
            self.assertIsInstance(entry, tuple)
            self.assertEqual(len(entry), 3)
            self.assertIsInstance(entry[0], str)
            self.assertIsInstance(entry[1], str)
            self.assertIsInstance(entry[2], str)


class DuplicateLeadErrorTests(unittest.TestCase):
    def test_attributes(self):
        err = DuplicateLeadError("L3")
        self.assertEqual(err.existing_id, "L3")
        self.assertIsInstance(err, Exception)
        self.assertTrue(hasattr(crm, "DuplicateLeadError"))


if __name__ == "__main__":
    unittest.main()
