import unittest

from crm import CRM, DuplicateLeadError


def make_crm():
    reps = [
        {"id": "r1", "role": "rep", "capacity": 1},
        {"id": "r2", "role": "rep", "capacity": 2},
        {"id": "m1", "role": "manager", "capacity": 0},
    ]
    return CRM(reps)


def make_opp(crm, email, owner_hint, amount=1000):
    """Create a qualified lead owned by owner_hint and convert it."""
    lead = crm.add_lead(email, "Name", "referral", owner_hint)
    owner = crm.leads[lead]["owner"]
    crm.qualify(lead, owner)
    return crm.convert(lead, amount, owner)


class TestAddLead(unittest.TestCase):
    def test_unknown_actor(self):
        crm = make_crm()
        with self.assertRaises(PermissionError):
            crm.add_lead("a@b.com", "Ann", "web", "nobody")
        self.assertEqual(crm.log, [])
        self.assertEqual(crm.leads, {})

    def test_invalid_emails(self):
        crm = make_crm()
        for bad in ["noat", "a@b", "a@@b.com", "@b.com", "a@", "a@.com", "a@com."]:
            with self.assertRaises(ValueError):
                crm.add_lead(bad, "Ann", "web", "r1")
        with self.assertRaises(ValueError):
            crm.add_lead(123, "Ann", "web", "r1")
        with self.assertRaises(ValueError):
            crm.add_lead(None, "Ann", "web", "r1")
        self.assertEqual(crm.log, [])
        self.assertEqual(crm.leads, {})

    def test_valid_email_shapes(self):
        crm = make_crm()
        self.assertEqual(crm.add_lead("a@b.co", "A", "web", "r1"), "L1")
        self.assertEqual(crm.add_lead("a@b.c.d", "A", "web", "r1"), "L2")

    def test_email_normalization(self):
        crm = make_crm()
        lead_id = crm.add_lead("  Bob@GMAIL.com ", "  Bob  ", "web", "r1")
        self.assertEqual(crm.leads[lead_id]["email"], "bob@gmail.com")
        self.assertEqual(crm.leads[lead_id]["name"], "Bob")
        self.assertEqual(crm.leads[lead_id]["source"], "web")
        self.assertEqual(crm.leads[lead_id]["status"], "new")

    def test_invalid_name(self):
        crm = make_crm()
        for bad in ["", "   ", None, 42]:
            with self.assertRaises(ValueError):
                crm.add_lead("a@b.com", bad, "web", "r1")

    def test_invalid_source(self):
        crm = make_crm()
        for bad in ["email", "WEB", "", None]:
            with self.assertRaises(ValueError):
                crm.add_lead("a@b.com", "Ann", bad, "r1")

    def test_duplicate_email(self):
        crm = make_crm()
        first = crm.add_lead("a@gmail.com", "Ann", "web", "r1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            crm.add_lead(" A@GMAIL.COM ", "Ann", "web", "r1")
        self.assertEqual(ctx.exception.existing_id, first)
        # failed call logged nothing and did not consume an id
        self.assertEqual(len(crm.log), 1)
        self.assertEqual(crm.add_lead("b@gmail.com", "Bob", "web", "r1"), "L2")

    def test_scores(self):
        crm = make_crm()
        web = crm.add_lead("a@gmail.com", "A", "web", "r1")
        ref = crm.add_lead("b@gmail.com", "B", "referral", "r1")
        event = crm.add_lead("c@gmail.com", "C", "event", "r1")
        custom = crm.add_lead("d@corp.io", "D", "web", "r1")
        self.assertEqual(crm.leads[web]["score"], 10)
        self.assertEqual(crm.leads[ref]["score"], 30)
        self.assertEqual(crm.leads[event]["score"], 20)
        self.assertEqual(crm.leads[custom]["score"], 25)

    def test_owner_assignment_and_queue(self):
        crm = make_crm()
        l1 = crm.add_lead("a@gmail.com", "A", "web", "r1")
        # tie on load 0 -> smallest rep id r1
        self.assertEqual(crm.leads[l1]["owner"], "r1")
        l2 = crm.add_lead("b@gmail.com", "B", "web", "r1")
        # r1 is at capacity 1 -> r2
        self.assertEqual(crm.leads[l2]["owner"], "r2")
        l3 = crm.add_lead("c@gmail.com", "C", "web", "r1")
        self.assertEqual(crm.leads[l3]["owner"], "r2")
        l4 = crm.add_lead("d@gmail.com", "D", "web", "r1")
        # everyone full -> unowned and waiting
        self.assertIsNone(crm.leads[l4]["owner"])
        self.assertEqual(
            crm.log,
            [
                ("add_lead", l1, "r1"),
                ("add_lead", l2, "r1"),
                ("add_lead", l3, "r1"),
                ("add_lead", l4, "r1"),
            ],
        )

    def test_manager_never_owns(self):
        crm = make_crm()
        lead = crm.add_lead("a@gmail.com", "A", "referral", "m1")
        self.assertEqual(crm.leads[lead]["owner"], "r1")


class TestQualify(unittest.TestCase):
    def test_unknown_lead(self):
        crm = make_crm()
        with self.assertRaises(ValueError):
            crm.qualify("L99", "r1")

    def test_unknown_actor_first(self):
        crm = make_crm()
        lead = crm.add_lead("a@gmail.com", "A", "web", "r1")
        with self.assertRaises(PermissionError):
            crm.qualify(lead, "nobody")

    def test_non_owner_rep(self):
        crm = make_crm()
        lead = crm.add_lead("b@gmail.com", "B", "referral", "r1")  # owner r1
        with self.assertRaises(PermissionError):
            crm.qualify(lead, "r2")
        self.assertEqual(crm.leads[lead]["status"], "new")
        self.assertEqual(len(crm.log), 1)

    def test_owner_allowed(self):
        crm = make_crm()
        lead = crm.add_lead("b@gmail.com", "B", "referral", "r1")  # score 30
        crm.qualify(lead, "r1")
        self.assertEqual(crm.leads[lead]["status"], "qualified")
        self.assertEqual(crm.log[-1], ("qualify", lead, "r1"))

    def test_manager_allowed(self):
        crm = make_crm()
        lead = crm.add_lead("b@gmail.com", "B", "referral", "r1")
        crm.qualify(lead, "m1")
        self.assertEqual(crm.leads[lead]["status"], "qualified")
        self.assertEqual(crm.log[-1], ("qualify", lead, "m1"))

    def test_low_score(self):
        crm = make_crm()
        lead = crm.add_lead("a@gmail.com", "A", "web", "r1")  # score 10
        with self.assertRaises(ValueError):
            crm.qualify(lead, "r1")
        self.assertEqual(crm.leads[lead]["status"], "new")

    def test_not_new(self):
        crm = make_crm()
        lead = crm.add_lead("b@gmail.com", "B", "referral", "r1")
        crm.qualify(lead, "r1")
        with self.assertRaises(ValueError):
            crm.qualify(lead, "r1")


class TestConvert(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        self.ok = self.crm.add_lead("b@gmail.com", "B", "referral", "r1")  # r1
        self.crm.qualify(self.ok, "r1")
        self.low = self.crm.add_lead("a@gmail.com", "A", "web", "r1")  # owner r2

    def test_unknown_lead(self):
        with self.assertRaises(ValueError):
            self.crm.convert("L99", 100, "r1")

    def test_amount_validation(self):
        for bad in [0, -5, True, False, "10", 3.5, None]:
            with self.assertRaises(ValueError):
                self.crm.convert(self.ok, bad, "r1")
        self.assertEqual(self.crm.opps, {})
        self.assertEqual(self.crm.leads[self.ok]["status"], "qualified")

    def test_permission(self):
        with self.assertRaises(PermissionError):
            self.crm.convert(self.ok, 100, "r2")

    def test_requires_qualified(self):
        with self.assertRaises(ValueError):
            self.crm.convert(self.low, 100, "r2")

    def test_requires_owner_even_for_manager(self):
        crm = make_crm()
        for e in ["a@gmail.com", "b@gmail.com", "c@gmail.com"]:
            crm.add_lead(e, "X", "web", "r1")  # fills r1 (1) and r2 (2)
        lead = crm.add_lead("x@corp.io", "X", "referral", "m1")  # unowned, score 45
        self.assertIsNone(crm.leads[lead]["owner"])
        crm.qualify(lead, "m1")
        with self.assertRaises(ValueError):
            crm.convert(lead, 100, "m1")

    def test_success(self):
        opp_id = self.crm.convert(self.ok, 1000, "r1")
        self.assertEqual(opp_id, "O1")
        self.assertEqual(
            self.crm.opps[opp_id],
            {
                "id": "O1",
                "lead_id": self.ok,
                "owner": "r1",
                "amount": 1000,
                "original_amount": 1000,
                "stage": "prospect",
            },
        )
        self.assertEqual(self.crm.leads[self.ok]["status"], "converted")
        self.assertEqual(self.crm.log[-1], ("convert", "O1", "r1"))
        # second conversion gets the next id
        lead2 = self.crm.add_lead("c@gmail.com", "C", "referral", "r2")
        self.crm.qualify(lead2, "r2")
        self.assertEqual(self.crm.convert(lead2, 1, "r2"), "O2")


class TestAdvance(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        self.opp = make_opp(self.crm, "b@gmail.com", "r1", 40000)  # owner r1

    def test_unknown_opp(self):
        with self.assertRaises(ValueError):
            self.crm.advance("O99", "proposal", "r1")

    def test_invalid_stage(self):
        for bad in ["signed", "prospect ", "", None]:
            with self.assertRaises(ValueError):
                self.crm.advance(self.opp, bad, "r1")

    def test_unknown_actor_first(self):
        with self.assertRaises(PermissionError):
            self.crm.advance(self.opp, "proposal", "ghost")

    def test_permission(self):
        with self.assertRaises(PermissionError):
            self.crm.advance(self.opp, "proposal", "r2")

    def test_skip_stage(self):
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "negotiation", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "won", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "prospect", "r1")
        self.assertEqual(self.crm.opps[self.opp]["stage"], "prospect")

    def test_big_deal_needs_manager_for_negotiation(self):
        big_opp = make_opp(self.crm, "c@gmail.com", "r2", 60000)
        self.crm.advance(big_opp, "proposal", "r2")
        with self.assertRaises(PermissionError):
            self.crm.advance(big_opp, "negotiation", "r2")
        self.assertEqual(self.crm.opps[big_opp]["stage"], "proposal")
        self.crm.advance(big_opp, "negotiation", "m1")
        self.assertEqual(self.crm.opps[big_opp]["stage"], "negotiation")

    def test_small_deal_rep_can_negotiation(self):
        self.crm.advance(self.opp, "proposal", "r1")
        self.crm.advance(self.opp, "negotiation", "r1")
        self.assertEqual(self.crm.opps[self.opp]["stage"], "negotiation")

    def test_lost_anytime(self):
        self.crm.advance(self.opp, "lost", "r1")
        self.assertEqual(self.crm.opps[self.opp]["stage"], "lost")
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "proposal", "r1")

    def test_final_stage(self):
        for stage in ["proposal", "negotiation", "won"]:
            self.crm.advance(self.opp, stage, "r1")
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "lost", "r1")

    def test_manager_can_advance_any_opp(self):
        self.crm.advance(self.opp, "proposal", "m1")
        self.assertEqual(self.crm.opps[self.opp]["stage"], "proposal")

    def test_won_frees_slot_and_assigns_waiting(self):
        crm = make_crm()
        opp = make_opp(crm, "b@gmail.com", "r1", 1000)  # r1 load 1 (opp)
        crm.add_lead("c@gmail.com", "C", "web", "r1")  # r2
        crm.add_lead("d@gmail.com", "D", "web", "r1")  # r2 (full)
        queued = crm.add_lead("e@gmail.com", "E", "web", "r1")  # waiting
        self.assertIsNone(crm.leads[queued]["owner"])
        crm.advance(opp, "proposal", "r1")
        crm.advance(opp, "negotiation", "r1")
        crm.advance(opp, "won", "r1")
        self.assertEqual(crm.leads[queued]["owner"], "r1")
        self.assertEqual(
            crm.log[-2:],
            [("advance", opp, "r1"), ("assign", queued, "system")],
        )

    def test_lost_frees_slot_too(self):
        crm = make_crm()
        opp = make_opp(crm, "b@gmail.com", "r1", 1000)
        crm.add_lead("c@gmail.com", "C", "web", "r1")  # r2
        crm.add_lead("d@gmail.com", "D", "web", "r1")  # r2
        queued = crm.add_lead("e@gmail.com", "E", "web", "r1")  # waiting
        crm.advance(opp, "lost", "r1")
        self.assertEqual(crm.leads[queued]["owner"], "r1")
        self.assertEqual(crm.log[-1], ("assign", queued, "system"))


class TestDiscount(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        self.opp = make_opp(self.crm, "b@gmail.com", "r1", 1000)  # owner r1

    def test_unknown_opp(self):
        with self.assertRaises(ValueError):
            self.crm.discount("O99", 5, "r1")

    def test_pct_validation(self):
        for bad in [0, 31, -5, True, "10", 2.5, None]:
            with self.assertRaises(ValueError):
                self.crm.discount(self.opp, bad, "r1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 1000)

    def test_unknown_actor_first(self):
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp, 5, "ghost")

    def test_permission(self):
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp, 5, "r2")

    def test_rep_over_ten(self):
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp, 15, "r1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 1000)

    def test_rep_up_to_ten(self):
        self.crm.discount(self.opp, 10, "r1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 900)

    def test_manager_over_ten(self):
        self.crm.discount(self.opp, 20, "m1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 800)
        self.assertEqual(self.crm.log[-1], ("discount", self.opp, "m1"))

    def test_cumulative_cap(self):
        self.crm.discount(self.opp, 20, "m1")  # 1000 -> 800
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp, 15, "m1")  # 680 < 700
        self.assertEqual(self.crm.opps[self.opp]["amount"], 800)
        self.crm.discount(self.opp, 10, "r1")  # 720 >= 700
        self.assertEqual(self.crm.opps[self.opp]["amount"], 720)

    def test_final_stage(self):
        self.crm.advance(self.opp, "lost", "r1")
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp, 5, "r1")


class TestTransfer(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        self.opp = make_opp(self.crm, "b@gmail.com", "r1", 1000)  # owner r1

    def test_unknown_opp(self):
        with self.assertRaises(ValueError):
            self.crm.transfer("O99", "r2", "m1")

    def test_non_manager_actor(self):
        for actor in ["r1", "r2"]:
            with self.assertRaises(PermissionError):
                self.crm.transfer(self.opp, "r2", actor)
        self.assertEqual(self.crm.opps[self.opp]["owner"], "r1")

    def test_unknown_actor_first(self):
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.opp, "r2", "ghost")

    def test_new_owner_must_be_rep(self):
        for bad in ["m1", "ghost"]:
            with self.assertRaises(ValueError):
                self.crm.transfer(self.opp, bad, "m1")

    def test_full_new_owner(self):
        crm = make_crm()
        opp = make_opp(crm, "b@gmail.com", "r1", 1000)  # owner r1
        crm.add_lead("c@gmail.com", "C", "web", "m1")  # r2 load 1
        crm.add_lead("d@gmail.com", "D", "web", "m1")  # r2 load 2 (capacity)
        with self.assertRaises(ValueError):
            crm.transfer(opp, "r2", "m1")
        self.assertEqual(crm.opps[opp]["owner"], "r1")

    def test_same_owner(self):
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "r1", "m1")

    def test_final_stage(self):
        self.crm.advance(self.opp, "lost", "r1")
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "r2", "m1")

    def test_success(self):
        self.crm.transfer(self.opp, "r2", "m1")
        self.assertEqual(self.crm.opps[self.opp]["owner"], "r2")
        self.assertEqual(self.crm.log[-1], ("transfer", self.opp, "m1"))

    def test_transfer_to_prev_owner_after_their_slot_freed(self):
        crm = make_crm()
        opp = make_opp(crm, "b@gmail.com", "r1", 1000)  # owner r1, r1 full
        crm.add_lead("c@gmail.com", "C", "web", "m1")  # r2 load 1
        crm.add_lead("d@gmail.com", "D", "web", "m1")  # r2 load 2 (capacity)
        queued = crm.add_lead("e@gmail.com", "E", "web", "m1")  # waiting
        self.assertIsNone(crm.leads[queued]["owner"])
        # r2 is at capacity, so transfer fails; but a won opp on r1 opens a slot
        with self.assertRaises(ValueError):
            crm.transfer(opp, "r2", "m1")
        # give r1 a second convertible lead? capacity 1, so instead free r1 first:
        lead2 = crm.add_lead("f@gmail.com", "F", "referral", "m1")  # still waiting
        self.assertIsNone(crm.leads[lead2]["owner"])
        crm.advance(opp, "proposal", "r1")
        crm.advance(opp, "negotiation", "r1")
        crm.advance(opp, "won", "r1")  # frees r1 -> assigns queued lead
        self.assertEqual(crm.leads[queued]["owner"], "r1")
        self.assertEqual(crm.log[-1], ("assign", queued, "system"))


class TestForecast(unittest.TestCase):
    def test_forecast_empty(self):
        crm = make_crm()
        self.assertEqual(crm.forecast(), {"open": 0, "weighted": 0, "won": 0})

    def test_forecast(self):
        crm = make_crm()
        o1 = make_opp(crm, "a@gmail.com", "r1", 1000)  # prospect, owner r1
        o2 = make_opp(crm, "b@gmail.com", "r2", 2000)  # prospect, owner r2
        crm.advance(o2, "proposal", "r2")
        crm.discount(o2, 10, "r2")  # 1800
        result = crm.forecast()
        self.assertEqual(result["open"], 2)
        # 1000*10//100 + 1800*30//100 = 100 + 540
        self.assertEqual(result["weighted"], 640)
        self.assertEqual(result["won"], 0)
        crm.advance(o1, "proposal", "r1")
        crm.advance(o1, "negotiation", "r1")
        crm.advance(o1, "won", "r1")
        result = crm.forecast()
        self.assertEqual(result["open"], 1)
        self.assertEqual(result["weighted"], 540)
        self.assertEqual(result["won"], 1000)

    def test_lost_excluded(self):
        crm = make_crm()
        o1 = make_opp(crm, "a@gmail.com", "r1", 1000)
        crm.advance(o1, "lost", "r1")
        self.assertEqual(crm.forecast(), {"open": 0, "weighted": 0, "won": 0})


class TestLoadDetails(unittest.TestCase):
    def test_converted_leads_do_not_count(self):
        crm = make_crm()  # r1 capacity 1
        lead = crm.add_lead("a@gmail.com", "A", "referral", "r1")
        self.assertEqual(crm._load("r1"), 1)
        crm.qualify(lead, "r1")
        self.assertEqual(crm._load("r1"), 1)
        opp = crm.convert(lead, 100, "r1")
        self.assertEqual(crm._load("r1"), 1)  # open opp counts instead
        crm.advance(opp, "proposal", "r1")
        self.assertEqual(crm._load("r1"), 1)
        crm.advance(opp, "lost", "r1")
        self.assertEqual(crm._load("r1"), 0)

    def test_queue_fifo_order(self):
        reps = [{"id": "r1", "role": "rep", "capacity": 1}]
        crm = CRM(reps)
        lead = crm.add_lead("a@gmail.com", "A", "referral", "r1")  # owner r1
        crm.qualify(lead, "r1")
        q1 = crm.add_lead("b@gmail.com", "B", "web", "r1")  # waiting
        q2 = crm.add_lead("c@gmail.com", "C", "web", "r1")  # waiting
        q3 = crm.add_lead("d@gmail.com", "D", "web", "r1")  # waiting
        opp = crm.convert(lead, 100, "r1")
        crm.advance(opp, "proposal", "r1")
        crm.advance(opp, "negotiation", "r1")
        crm.advance(opp, "won", "r1")
        # one slot freed -> only q1 assigned
        self.assertEqual(crm.leads[q1]["owner"], "r1")
        self.assertIsNone(crm.leads[q2]["owner"])
        self.assertIsNone(crm.leads[q3]["owner"])
        self.assertEqual(
            crm.log[-2:],
            [("advance", "O1", "r1"), ("assign", q1, "system")],
        )

    def test_failed_calls_append_nothing(self):
        crm = make_crm()
        lead = crm.add_lead("a@gmail.com", "A", "web", "r1")
        before = list(crm.log)
        with self.assertRaises(ValueError):
            crm.qualify("L99", "r1")
        with self.assertRaises(ValueError):
            crm.add_lead("bad", "A", "web", "r1")
        self.assertEqual(crm.log, before)


if __name__ == "__main__":
    unittest.main()
