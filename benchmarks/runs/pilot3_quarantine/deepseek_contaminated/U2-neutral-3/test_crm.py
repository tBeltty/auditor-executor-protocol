import unittest

from crm import CRM, DuplicateLeadError


REPS = [
    {"id": "r1", "role": "rep", "capacity": 2},
    {"id": "r2", "role": "rep", "capacity": 2},
    {"id": "m1", "role": "manager", "capacity": 0},
]


def crm_with(*reps):
    return CRM([dict(r) for r in reps])


class TestValidation(unittest.TestCase):
    def setUp(self):
        self.crm = crm_with(*REPS)

    def test_unknown_actor_permission_first(self):
        calls = [
            lambda: self.crm.add_lead("a@b.com", "A", "web", "ghost"),
            lambda: self.crm.qualify("nope", "ghost"),
            lambda: self.crm.convert("nope", 10, "ghost"),
            lambda: self.crm.advance("nope", "proposal", "ghost"),
            lambda: self.crm.discount("nope", 5, "ghost"),
            lambda: self.crm.transfer("nope", "r1", "ghost"),
        ]
        for call in calls:
            with self.assertRaises(PermissionError):
                call()

    def test_email_validation(self):
        bad = [
            123,
            "",
            "plain",
            "a@b",
            "a@@b.com",
            "a@b@c.com",
            "@b.com",
            "a@.com",
            "a@com.",
            "a@.",
        ]
        for email in bad:
            with self.assertRaises(ValueError, msg=repr(email)):
                self.crm.add_lead(email, "A", "web", "r1")

    def test_email_validation_accepts_subdomains(self):
        lead_id = self.crm.add_lead("a@mail.example.com", "A", "web", "r1")
        self.assertEqual(self.crm.leads[lead_id]["email"], "a@mail.example.com")

    def test_email_normalized_and_name_stripped(self):
        lead_id = self.crm.add_lead("  Ann@Example.COM ", "  Ann  ", "event", "r1")
        lead = self.crm.leads[lead_id]
        self.assertEqual(lead["email"], "ann@example.com")
        self.assertEqual(lead["name"], "Ann")

    def test_name_validation(self):
        for name in ("", "   ", None, 5):
            with self.assertRaises(ValueError):
                self.crm.add_lead("a@b.com", name, "web", "r1")

    def test_source_validation(self):
        with self.assertRaises(ValueError):
            self.crm.add_lead("a@b.com", "A", "cold-call", "r1")

    def test_duplicate_after_source_check(self):
        self.crm.add_lead("a@b.com", "A", "web", "r1")
        with self.assertRaises(ValueError):
            self.crm.add_lead("a@b.com", "A", "bogus", "r1")


class TestAddLead(unittest.TestCase):
    def test_scores(self):
        crm = crm_with(*REPS)
        self.assertEqual(crm.leads[crm.add_lead("a@gmail.com", "A", "web", "r1")]["score"], 10)
        self.assertEqual(crm.leads[crm.add_lead("b@yahoo.com", "B", "referral", "r1")]["score"], 30)
        self.assertEqual(crm.leads[crm.add_lead("c@outlook.com", "C", "event", "r1")]["score"], 20)
        self.assertEqual(crm.leads[crm.add_lead("d@corp.io", "D", "web", "r1")]["score"], 25)
        self.assertEqual(crm.leads[crm.add_lead("e@corp.io", "E", "referral", "r1")]["score"], 45)
        self.assertEqual(crm.leads[crm.add_lead("f@corp.io", "F", "event", "r1")]["score"], 35)

    def test_ids_only_advance_on_success(self):
        crm = crm_with(*REPS)
        with self.assertRaises(ValueError):
            crm.add_lead("bad", "A", "web", "r1")
        self.assertEqual(crm.add_lead("a@b.com", "A", "web", "r1"), "L1")
        self.assertEqual(crm.add_lead("b@b.com", "B", "web", "r1"), "L2")

    def test_duplicate_case_insensitive(self):
        crm = crm_with(*REPS)
        first = crm.add_lead("A@B.com", "A", "web", "r1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            crm.add_lead(" a@b.COM ", "B", "web", "r1")
        self.assertEqual(ctx.exception.existing_id, first)
        self.assertEqual(len(crm.log), 1)

    def test_lowest_load_owner_and_tiebreak(self):
        crm = crm_with(*REPS)
        l1 = crm.add_lead("a@x.com", "A", "web", "r1")
        self.assertEqual(crm.leads[l1]["owner"], "r1")
        l2 = crm.add_lead("b@x.com", "B", "web", "r1")
        self.assertEqual(crm.leads[l2]["owner"], "r2")
        # both at load 1, smallest id wins the third
        l3 = crm.add_lead("c@x.com", "C", "web", "r1")
        self.assertEqual(crm.leads[l3]["owner"], "r1")
        l4 = crm.add_lead("d@x.com", "D", "web", "r1")
        self.assertEqual(crm.leads[l4]["owner"], "r2")
        l5 = crm.add_lead("e@x.com", "E", "web", "r1")
        self.assertIsNone(crm.leads[l5]["owner"])

    def test_manager_never_owns(self):
        crm = crm_with({"id": "m1", "role": "manager", "capacity": 5})
        lead_id = crm.add_lead("a@x.com", "A", "web", "m1")
        self.assertIsNone(crm.leads[lead_id]["owner"])

    def test_zero_capacity_rep_gets_no_work(self):
        crm = crm_with({"id": "r1", "role": "rep", "capacity": 0})
        lead_id = crm.add_lead("a@x.com", "A", "web", "r1")
        self.assertIsNone(crm.leads[lead_id]["owner"])
        self.assertEqual(crm._waiting, [lead_id])

    def test_log_entry(self):
        crm = crm_with(*REPS)
        lead_id = crm.add_lead("a@x.com", "A", "web", "m1")
        self.assertEqual(crm.log, [("add_lead", lead_id, "m1")])


    def test_tiebreak_is_string_order_not_insertion_order(self):
        crm = crm_with(
            {"id": "r2", "role": "rep", "capacity": 2},
            {"id": "r10", "role": "rep", "capacity": 2},
        )
        lead_id = crm.add_lead("a@x.com", "A", "web", "r2")
        # "r10" < "r2" in string order, so r10 wins the tie at load 0.
        self.assertEqual(crm.leads[lead_id]["owner"], "r10")

    def test_manager_with_spare_capacity_is_still_skipped(self):
        crm = crm_with(
            {"id": "m1", "role": "manager", "capacity": 99},
            {"id": "r1", "role": "rep", "capacity": 1},
        )
        lead_id = crm.add_lead("a@x.com", "A", "web", "m1")
        self.assertEqual(crm.leads[lead_id]["owner"], "r1")


class TestQualify(unittest.TestCase):
    def setUp(self):
        self.crm = crm_with(*REPS)

    def test_score_gate(self):
        lead_id = self.crm.add_lead("a@x.com", "A", "web", "r1")
        with self.assertRaises(ValueError):
            self.crm.qualify(lead_id, "r1")
        self.assertEqual(self.crm.leads[lead_id]["status"], "new")

    def test_status_gate(self):
        lead_id = self.crm.add_lead("a@x.com", "A", "referral", "r1")
        self.crm.qualify(lead_id, "r1")
        with self.assertRaises(ValueError):
            self.crm.qualify(lead_id, "r1")

    def test_permission(self):
        lead_id = self.crm.add_lead("a@x.com", "A", "referral", "r1")
        with self.assertRaises(PermissionError):
            self.crm.qualify(lead_id, "r2")
        self.crm.qualify(lead_id, "m1")
        self.assertEqual(self.crm.leads[lead_id]["status"], "qualified")
        self.assertEqual(self.crm.log[-1], ("qualify", lead_id, "m1"))

    def test_unknown_lead(self):
        with self.assertRaises(ValueError):
            self.crm.qualify("L99", "r1")


class TestConvert(unittest.TestCase):
    def setUp(self):
        self.crm = crm_with(*REPS)
        self.lead_id = self.crm.add_lead("a@x.com", "A", "referral", "r1")
        self.crm.qualify(self.lead_id, "r1")

    def test_amount_validation_before_permission(self):
        for amount in (0, -5, True, False, 1.5, "10", None):
            with self.assertRaises(ValueError, msg=repr(amount)):
                self.crm.convert(self.lead_id, amount, "r2")

    def test_permission(self):
        with self.assertRaises(PermissionError):
            self.crm.convert(self.lead_id, 100, "r2")
        self.assertNotIn("O1", self.crm.opps)

    def test_status_gate(self):
        other = self.crm.add_lead("b@x.com", "B", "referral", "r1")
        with self.assertRaises(ValueError):
            self.crm.convert(other, 100, "m1")

    def test_requires_owner(self):
        crm = crm_with({"id": "r1", "role": "rep", "capacity": 0}, {"id": "m1", "role": "manager", "capacity": 0})
        lead_id = crm.add_lead("a@x.com", "A", "referral", "m1")
        crm.qualify(lead_id, "m1")
        with self.assertRaises(ValueError):
            crm.convert(lead_id, 100, "m1")

    def test_creates_opportunity(self):
        opp_id = self.crm.convert(self.lead_id, 1500, "m1")
        self.assertEqual(opp_id, "O1")
        self.assertEqual(
            self.crm.opps[opp_id],
            {
                "id": "O1",
                "lead_id": self.lead_id,
                "owner": "r1",
                "amount": 1500,
                "original_amount": 1500,
                "stage": "prospect",
            },
        )
        self.assertEqual(self.crm.leads[self.lead_id]["status"], "converted")
        self.assertEqual(self.crm.log[-1], ("convert", "O1", "m1"))
        with self.assertRaises(DuplicateLeadError):
            self.crm.add_lead("a@x.com", "A", "web", "r1")

    def test_lead_not_reusable(self):
        self.crm.convert(self.lead_id, 100, "r1")
        with self.assertRaises(ValueError):
            self.crm.convert(self.lead_id, 100, "r1")


class TestAdvance(unittest.TestCase):
    def setUp(self):
        self.crm = crm_with(*REPS)
        self.lead_id = self.crm.add_lead("a@x.com", "A", "referral", "r1")
        self.crm.qualify(self.lead_id, "r1")
        self.opp_id = self.crm.convert(self.lead_id, 1000, "r1")

    def test_stage_validation(self):
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp_id, "bogus", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance("O9", "proposal", "r1")

    def test_sequential_only(self):
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp_id, "negotiation", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp_id, "won", "r1")
        self.crm.advance(self.opp_id, "proposal", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp_id, "proposal", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp_id, "prospect", "r1")

    def test_permission(self):
        with self.assertRaises(PermissionError):
            self.crm.advance(self.opp_id, "proposal", "r2")
        self.crm.advance(self.opp_id, "proposal", "m1")
        self.assertEqual(self.crm.opps[self.opp_id]["stage"], "proposal")

    def test_lost_from_any_non_final(self):
        self.crm.advance(self.opp_id, "lost", "r1")
        self.assertEqual(self.crm.opps[self.opp_id]["stage"], "lost")
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp_id, "won", "r1")

    def test_large_negotiation_requires_manager(self):
        self.crm.discount(self.opp_id, 1, "m1")
        big_lead = self.crm.add_lead("b@x.com", "B", "referral", "r1")
        self.crm.qualify(big_lead, "m1")
        big = self.crm.convert(big_lead, 50001, "m1")
        self.crm.advance(big, "proposal", "m1")
        with self.assertRaises(PermissionError):
            self.crm.advance(big, "negotiation", "r1")
        self.crm.advance(big, "negotiation", "m1")
        self.assertEqual(self.crm.opps[big]["stage"], "negotiation")

    def test_exactly_50000_ok_for_rep(self):
        lead = self.crm.add_lead("b@x.com", "B", "referral", "r1")
        owner = self.crm.leads[lead]["owner"]
        self.crm.qualify(lead, "m1")
        opp = self.crm.convert(lead, 50000, "m1")
        self.crm.advance(opp, "proposal", owner)
        self.crm.advance(opp, "negotiation", owner)
        self.assertEqual(self.crm.opps[opp]["stage"], "negotiation")

    def test_negotiation_gate_applies_to_owner_rep(self):
        crm = crm_with({"id": "r1", "role": "rep", "capacity": 5}, {"id": "m1", "role": "manager", "capacity": 0})
        lead = crm.add_lead("a@x.com", "A", "referral", "r1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 60000, "r1")
        self.assertEqual(crm.opps[opp]["owner"], "r1")
        crm.advance(opp, "proposal", "r1")
        with self.assertRaises(PermissionError):
            crm.advance(opp, "negotiation", "r1")
        self.assertEqual(crm.opps[opp]["stage"], "proposal")
        self.assertEqual(crm.log[-1], ("advance", opp, "r1"))
        crm.advance(opp, "negotiation", "m1")
        self.assertEqual(crm.opps[opp]["stage"], "negotiation")

    def test_won_logs_and_frees_slot(self):
        self.crm.advance(self.opp_id, "proposal", "r1")
        self.crm.advance(self.opp_id, "negotiation", "r1")
        before = len(self.crm.log)
        self.crm.advance(self.opp_id, "won", "r1")
        self.assertEqual(self.crm.log[before], ("advance", self.opp_id, "r1"))
        self.assertEqual(self.crm.leads[self.lead_id]["status"], "converted")


class TestWaitingQueue(unittest.TestCase):
    def setUp(self):
        self.crm = crm_with({"id": "r1", "role": "rep", "capacity": 1}, {"id": "m1", "role": "manager", "capacity": 0})

    def test_fifo_and_assignment_on_final(self):
        l1 = self.crm.add_lead("a@x.com", "A", "referral", "r1")
        l2 = self.crm.add_lead("b@x.com", "B", "referral", "r1")
        l3 = self.crm.add_lead("c@x.com", "C", "referral", "r1")
        self.assertEqual(self.crm.leads[l1]["owner"], "r1")
        self.assertIsNone(self.crm.leads[l2]["owner"])
        self.assertIsNone(self.crm.leads[l3]["owner"])

        self.crm.qualify(l1, "r1")
        opp = self.crm.convert(l1, 100, "r1")
        self.crm.advance(opp, "lost", "r1")

        self.assertEqual(self.crm.leads[l2]["owner"], "r1")
        self.assertIsNone(self.crm.leads[l3]["owner"])
        self.assertEqual(self.crm.log[-1], ("assign", l2, "system"))

    def test_no_assignment_when_slot_not_freed(self):
        l1 = self.crm.add_lead("a@x.com", "A", "referral", "r1")
        l2 = self.crm.add_lead("b@x.com", "B", "referral", "r1")
        self.crm.qualify(l1, "r1")
        opp = self.crm.convert(l1, 100, "r1")
        before = list(self.crm.log)
        self.crm.advance(opp, "proposal", "r1")
        self.assertIsNone(self.crm.leads[l2]["owner"])
        self.assertEqual(self.crm.log, before + [("advance", opp, "r1")])

    def test_convert_keeps_load_so_queue_waits(self):
        crm = crm_with({"id": "r1", "role": "rep", "capacity": 1}, {"id": "m1", "role": "manager", "capacity": 0})
        l1 = crm.add_lead("a@x.com", "A", "referral", "r1")
        l2 = crm.add_lead("b@x.com", "B", "referral", "r1")
        crm.qualify(l1, "r1")  # new -> qualified, still one unit of load
        self.assertIsNone(crm.leads[l2]["owner"])
        opp = crm.convert(l1, 100, "r1")  # lead load becomes an opportunity load
        self.assertIsNone(crm.leads[l2]["owner"])
        self.assertEqual(crm.leads[l1]["status"], "converted")
        crm.advance(opp, "lost", "r1")
        self.assertEqual(crm.leads[l2]["owner"], "r1")
        self.assertEqual(crm.log[-1], ("assign", l2, "system"))

    def test_queue_stays_when_load_remains(self):
        crm = crm_with({"id": "r1", "role": "rep", "capacity": 2})
        l1 = crm.add_lead("a@x.com", "A", "referral", "r1")
        l2 = crm.add_lead("b@x.com", "B", "referral", "r1")
        l3 = crm.add_lead("c@x.com", "C", "referral", "r1")
        crm.qualify(l1, "r1")
        opp = crm.convert(l1, 100, "r1")
        crm.advance(opp, "lost", "r1")  # load: l2 only -> 1 < 2 -> l3 assigned
        self.assertEqual(crm.leads[l2]["owner"], "r1")
        self.assertEqual(crm.leads[l3]["owner"], "r1")
        self.assertEqual(crm._waiting, [])


class TestDiscount(unittest.TestCase):
    def setUp(self):
        self.crm = crm_with(*REPS)
        self.lead_id = self.crm.add_lead("a@x.com", "A", "referral", "r1")
        self.crm.qualify(self.lead_id, "r1")
        self.opp_id = self.crm.convert(self.lead_id, 1000, "r1")

    def test_pct_validation(self):
        for pct in (0, 31, -1, True, 5.0, "5", None):
            with self.assertRaises(ValueError, msg=repr(pct)):
                self.crm.discount(self.opp_id, pct, "m1")

    def test_permission(self):
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp_id, 5, "r2")

    def test_rep_limit(self):
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp_id, 11, "r1")
        self.crm.discount(self.opp_id, 10, "r1")
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 900)

    def test_final_stage(self):
        self.crm.advance(self.opp_id, "lost", "r1")
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp_id, 5, "m1")

    def test_cumulative_cap(self):
        self.crm.discount(self.opp_id, 30, "m1")
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 700)
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp_id, 1, "m1")
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 700)

    def test_original_amount_is_reference(self):
        self.crm.discount(self.opp_id, 10, "r1")
        self.crm.discount(self.opp_id, 10, "r1")
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 810)
        self.assertEqual(self.crm.log[-1], ("discount", self.opp_id, "r1"))


class TestTransfer(unittest.TestCase):
    def setUp(self):
        self.crm = crm_with(*REPS)
        self.lead_id = self.crm.add_lead("a@x.com", "A", "referral", "r1")
        self.crm.qualify(self.lead_id, "r1")
        self.opp_id = self.crm.convert(self.lead_id, 1000, "r1")

    def test_requires_manager(self):
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.opp_id, "r2", "r1")

    def test_new_owner_validation(self):
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp_id, "ghost", "m1")
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp_id, "m1", "m1")
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp_id, "r1", "m1")

    def test_final_stage(self):
        self.crm.advance(self.opp_id, "lost", "r1")
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp_id, "r2", "m1")

    def test_capacity(self):
        crm = crm_with(
            {"id": "r1", "role": "rep", "capacity": 2},
            {"id": "r2", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 0},
        )
        l1 = crm.add_lead("a@x.com", "A", "referral", "r1")
        crm.add_lead("b@x.com", "B", "web", "r1")
        crm.qualify(l1, "r1")
        opp = crm.convert(l1, 100, "r1")
        with self.assertRaises(ValueError):
            crm.transfer(opp, "r2", "m1")

    def test_transfer_sets_owner_and_logs(self):
        crm = crm_with(
            {"id": "r1", "role": "rep", "capacity": 2},
            {"id": "r2", "role": "rep", "capacity": 2},
            {"id": "m1", "role": "manager", "capacity": 0},
        )
        l1 = crm.add_lead("a@x.com", "A", "referral", "r1")
        crm.qualify(l1, "r1")
        opp = crm.convert(l1, 100, "r1")
        before = len(crm.log)
        crm.transfer(opp, "r2", "m1")
        self.assertEqual(crm.opps[opp]["owner"], "r2")
        self.assertEqual(crm.log[before], ("transfer", opp, "m1"))
        self.assertEqual(len(crm.log), before + 1)

    def test_transfer_blocked_when_all_reps_full_with_queue(self):
        crm = crm_with(
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 0},
        )
        l1 = crm.add_lead("a@x.com", "A", "referral", "r1")
        l2 = crm.add_lead("b@x.com", "B", "referral", "r1")
        l3 = crm.add_lead("c@x.com", "C", "referral", "r1")
        self.assertIsNone(crm.leads[l3]["owner"])
        crm.qualify(l1, "r1")
        opp = crm.convert(l1, 100, "r1")
        with self.assertRaises(ValueError):
            crm.transfer(opp, "r2", "m1")
        self.assertEqual(crm.opps[opp]["owner"], "r1")
        self.assertIsNone(crm.leads[l3]["owner"])

    def test_failed_transfer_leaves_state_untouched(self):
        crm = crm_with(
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 0},
        )
        l1 = crm.add_lead("a@x.com", "A", "referral", "r1")
        crm.add_lead("b@x.com", "B", "referral", "r2")
        crm.qualify(l1, "r1")
        opp = crm.convert(l1, 100, "r1")
        snapshot = (dict(crm.opps[opp]), list(crm.log))
        with self.assertRaises(ValueError):
            crm.transfer(opp, "r2", "m1")  # r2 is at capacity
        self.assertEqual(crm.opps[opp], snapshot[0])
        self.assertEqual(crm.log, snapshot[1])

    def test_transfer_without_waiting_logs_only_transfer(self):
        before = len(self.crm.log)
        self.crm.transfer(self.opp_id, "r2", "m1")
        self.assertEqual(len(self.crm.log), before + 1)
        self.assertEqual(self.crm.log[-1], ("transfer", self.opp_id, "m1"))


class TestForecast(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(crm_with(*REPS).forecast(), {"open": 0, "weighted": 0, "won": 0})

    def test_weighted_and_won(self):
        crm = crm_with(*REPS)
        amounts = [1000, 2000, 3000, 4000]
        opps = []
        for i, amount in enumerate(amounts):
            lead = crm.add_lead("a%d@x.com" % i, "N", "referral", "r1")
            crm.qualify(lead, "m1")
            opps.append(crm.convert(lead, amount, "m1"))
        crm.advance(opps[0], "proposal", "m1")
        crm.advance(opps[1], "proposal", "m1")
        crm.advance(opps[1], "negotiation", "m1")
        crm.advance(opps[2], "lost", "m1")
        self.assertEqual(
            crm.forecast(),
            {
                "open": 3,
                "weighted": 1000 * 30 // 100 + 2000 * 60 // 100 + 4000 * 10 // 100,
                "won": 0,
            },
        )
        lead = crm.add_lead("won@x.com", "N", "referral", "r1")
        crm.qualify(lead, "m1")
        opp = crm.convert(lead, 500, "m1")
        crm.advance(opp, "proposal", "m1")
        crm.advance(opp, "negotiation", "m1")
        crm.advance(opp, "won", "m1")
        result = crm.forecast()
        self.assertEqual(result["won"], 500)
        self.assertEqual(result["open"], 3)

    def test_uses_current_amount(self):
        crm = crm_with(*REPS)
        lead = crm.add_lead("a@x.com", "A", "referral", "r1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 1000, "r1")
        crm.discount(opp, 20, "m1")
        self.assertEqual(crm.forecast()["weighted"], 800 * 10 // 100)

    def test_forecast_does_not_log(self):
        crm = crm_with(*REPS)
        crm.forecast()
        self.assertEqual(crm.log, [])


class TestAtomicity(unittest.TestCase):
    def test_failed_calls_leave_state_untouched(self):
        crm = crm_with(*REPS)
        lead = crm.add_lead("a@x.com", "A", "referral", "r1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 100, "r1")
        snapshot = (
            {k: dict(v) for k, v in crm.leads.items()},
            {k: dict(v) for k, v in crm.opps.items()},
            list(crm.log),
        )
        attempts = [
            lambda: crm.add_lead("bad", "A", "web", "r1"),
            lambda: crm.add_lead("a@x.com", "A", "bogus", "r1"),
            lambda: crm.qualify("L99", "r1"),
            lambda: crm.convert("L99", 0, "r1"),
            lambda: crm.advance(opp, "won", "r1"),
            lambda: crm.discount(opp, 0, "r1"),
            lambda: crm.transfer("O99", "r2", "m1"),
        ]
        for attempt in attempts:
            with self.assertRaises((ValueError, PermissionError, DuplicateLeadError)):
                attempt()
        self.assertEqual({k: dict(v) for k, v in crm.leads.items()}, snapshot[0])
        self.assertEqual({k: dict(v) for k, v in crm.opps.items()}, snapshot[1])
        self.assertEqual(crm.log, snapshot[2])



class TestCheckOrdering(unittest.TestCase):
    def setUp(self):
        self.crm = crm_with(*REPS)
        self.lead_id = self.crm.add_lead("a@x.com", "A", "referral", "r1")
        self.crm.qualify(self.lead_id, "r1")
        self.opp_id = self.crm.convert(self.lead_id, 1000, "r1")

    def test_non_string_actor_rejected_everywhere(self):
        for actor in (None, 7, 7.5, [], {}, ()):
            for call in (
                lambda a=actor: self.crm.add_lead("z@x.com", "Z", "web", a),
                lambda a=actor: self.crm.qualify(self.lead_id, a),
                lambda a=actor: self.crm.convert(self.lead_id, 1, a),
                lambda a=actor: self.crm.advance(self.opp_id, "proposal", a),
                lambda a=actor: self.crm.discount(self.opp_id, 5, a),
                lambda a=actor: self.crm.transfer(self.opp_id, "r2", a),
            ):
                with self.assertRaises(PermissionError, msg=repr(actor)):
                    call()

    def test_entity_existence_precedes_other_checks(self):
        # A known but unauthorised actor still hits the missing entity first.
        with self.assertRaises(ValueError):
            self.crm.qualify("L99", "r2")
        with self.assertRaises(ValueError):
            self.crm.convert("L99", 0, "r2")
        with self.assertRaises(ValueError):
            self.crm.advance("O99", "bogus", "r2")
        with self.assertRaises(ValueError):
            self.crm.discount("O99", 99, "r2")
        with self.assertRaises(ValueError):
            self.crm.transfer("O99", "ghost", "r1")

    def test_transfer_manager_check_precedes_new_owner_check(self):
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.opp_id, "ghost", "r1")

    def test_qualify_permission_precedes_status(self):
        other = self.crm.add_lead("b@x.com", "B", "referral", "r1")
        self.crm.qualify(other, "m1")  # now qualified
        with self.assertRaises(PermissionError):
            self.crm.qualify(other, "r1")  # r1 is not this lead's owner

    def test_convert_permission_precedes_status(self):
        other = self.crm.add_lead("b@x.com", "B", "referral", "r1")  # still new
        with self.assertRaises(PermissionError):
            self.crm.convert(other, 100, "r1")  # r1 is not this lead's owner

    def test_advance_permission_precedes_final_stage(self):
        self.crm.advance(self.opp_id, "lost", "r1")
        with self.assertRaises(PermissionError):
            self.crm.advance(self.opp_id, "won", "r2")

    def test_discount_permission_precedes_final_stage(self):
        self.crm.advance(self.opp_id, "lost", "r1")
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp_id, 20, "r2")
        # The final-stage check still precedes the rep discount limit.
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp_id, 20, "r1")


class TestScoreBoundaries(unittest.TestCase):
    def test_referral_free_domain_scores_exactly_30_and_qualifies(self):
        crm = crm_with(*REPS)
        lead_id = crm.add_lead("a@gmail.com", "A", "referral", "r1")
        self.assertEqual(crm.leads[lead_id]["score"], 30)
        crm.qualify(lead_id, "r1")
        self.assertEqual(crm.leads[lead_id]["status"], "qualified")

    def test_free_domain_match_is_exact(self):
        crm = crm_with(*REPS)
        lead_id = crm.add_lead("a@mail.gmail.com", "A", "web", "r1")
        self.assertEqual(crm.leads[lead_id]["score"], 25)

    def test_event_corporate_scores_35_and_qualifies(self):
        crm = crm_with(*REPS)
        lead_id = crm.add_lead("a@corp.io", "A", "event", "r1")
        self.assertEqual(crm.leads[lead_id]["score"], 35)
        crm.qualify(lead_id, "r1")
        self.assertEqual(crm.leads[lead_id]["status"], "qualified")

    def test_web_lead_below_threshold_never_qualifies(self):
        crm = crm_with(*REPS)
        lead_id = crm.add_lead("a@corp.io", "A", "web", "r1")
        self.assertEqual(crm.leads[lead_id]["score"], 25)
        for actor in ("r1", "m1"):
            with self.assertRaises(ValueError):
                crm.qualify(lead_id, actor)
        self.assertEqual(crm.leads[lead_id]["status"], "new")
        self.assertEqual(crm.log, [("add_lead", lead_id, "r1")])


class TestSequences(unittest.TestCase):
    def test_lead_ids_are_per_instance_and_skip_failures(self):
        first = crm_with(*REPS)
        second = crm_with(*REPS)
        self.assertEqual(first.add_lead("a@x.com", "A", "web", "r1"), "L1")
        self.assertEqual(second.add_lead("a@x.com", "A", "web", "r1"), "L1")
        with self.assertRaises(DuplicateLeadError):
            first.add_lead("a@x.com", "A", "web", "r1")
        self.assertEqual(first.add_lead("b@x.com", "B", "web", "r1"), "L2")

    def test_opportunity_ids_skip_failed_conversions(self):
        crm = crm_with(*REPS)
        first = crm.add_lead("a@x.com", "A", "referral", "r1")
        crm.qualify(first, "r1")
        self.assertEqual(crm.convert(first, 100, "r1"), "O1")

        second = crm.add_lead("b@x.com", "B", "referral", "r1")
        crm.qualify(second, "m1")
        with self.assertRaises(ValueError):
            crm.convert(second, 0, "m1")
        self.assertEqual(crm.convert(second, 200, "m1"), "O2")


class TestQueueLifecycle(unittest.TestCase):
    def setUp(self):
        self.crm = crm_with(
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 0},
        )

    def test_manager_can_qualify_queued_lead_and_it_is_assigned_later(self):
        owned = self.crm.add_lead("a@x.com", "A", "referral", "r1")
        queued = self.crm.add_lead("b@x.com", "B", "referral", "r1")
        self.assertIsNone(self.crm.leads[queued]["owner"])

        self.crm.qualify(queued, "m1")
        self.assertEqual(self.crm.leads[queued]["status"], "qualified")
        self.assertIsNone(self.crm.leads[queued]["owner"])

        self.crm.qualify(owned, "r1")
        opp = self.crm.convert(owned, 100, "r1")
        self.crm.advance(opp, "lost", "r1")
        self.assertEqual(self.crm.leads[queued]["owner"], "r1")
        self.assertEqual(self.crm.log[-1], ("assign", queued, "system"))

        # The queued lead is now workable by its new owner.
        opp2 = self.crm.convert(queued, 200, "r1")
        self.assertEqual(self.crm.opps[opp2]["owner"], "r1")

    def test_queue_drains_one_lead_per_freed_slot_in_fifo_order(self):
        crm = crm_with(
            {"id": "r1", "role": "rep", "capacity": 2},
            {"id": "m1", "role": "manager", "capacity": 0},
        )
        l1 = crm.add_lead("a@x.com", "A", "referral", "r1")
        l2 = crm.add_lead("b@x.com", "B", "referral", "r1")
        l3 = crm.add_lead("c@x.com", "C", "referral", "r1")
        l4 = crm.add_lead("d@x.com", "D", "referral", "r1")
        self.assertEqual(crm._waiting, [l3, l4])

        crm.qualify(l1, "r1")
        opp1 = crm.convert(l1, 100, "r1")
        crm.advance(opp1, "lost", "r1")
        self.assertEqual(crm.leads[l3]["owner"], "r1")
        self.assertIsNone(crm.leads[l4]["owner"])
        self.assertEqual(crm._waiting, [l4])

        crm.qualify(l2, "r1")
        opp2 = crm.convert(l2, 100, "r1")
        crm.advance(opp2, "lost", "r1")
        self.assertEqual(crm.leads[l4]["owner"], "r1")
        self.assertEqual(crm._waiting, [])

    def test_won_logs_advance_before_assign(self):
        owned = self.crm.add_lead("a@x.com", "A", "referral", "r1")
        queued = self.crm.add_lead("b@x.com", "B", "referral", "r1")
        self.crm.qualify(owned, "r1")
        opp = self.crm.convert(owned, 100, "r1")
        self.crm.advance(opp, "proposal", "r1")
        self.crm.advance(opp, "negotiation", "r1")
        before = len(self.crm.log)
        self.crm.advance(opp, "won", "r1")
        self.assertEqual(
            self.crm.log[before:],
            [("advance", opp, "r1"), ("assign", queued, "system")],
        )


class TestTransferDetails(unittest.TestCase):
    def setUp(self):
        self.crm = crm_with(
            {"id": "r1", "role": "rep", "capacity": 2},
            {"id": "r2", "role": "rep", "capacity": 2},
            {"id": "m1", "role": "manager", "capacity": 0},
        )
        self.lead_id = self.crm.add_lead("a@x.com", "A", "referral", "r1")
        self.crm.qualify(self.lead_id, "r1")
        self.opp_id = self.crm.convert(self.lead_id, 1500, "r1")

    def test_transfer_preserves_amount_state_and_lead_link(self):
        self.crm.discount(self.opp_id, 10, "m1")
        self.crm.transfer(self.opp_id, "r2", "m1")
        opp = self.crm.opps[self.opp_id]
        self.assertEqual(opp["amount"], 1350)
        self.assertEqual(opp["original_amount"], 1500)
        self.assertEqual(opp["lead_id"], self.lead_id)
        self.assertEqual(opp["stage"], "prospect")
        self.assertEqual(self.crm.leads[self.lead_id]["status"], "converted")
        # The new owner may drive the opportunity onward.
        self.crm.advance(self.opp_id, "proposal", "r2")
        self.assertEqual(self.crm.opps[self.opp_id]["stage"], "proposal")

    def test_transfer_does_not_touch_the_forecast(self):
        before = dict(self.crm.forecast())
        self.crm.transfer(self.opp_id, "r2", "m1")
        self.assertEqual(self.crm.forecast(), before)


class TestForecastDetails(unittest.TestCase):
    def test_weighted_uses_integer_floor_division(self):
        crm = crm_with(*REPS)
        lead = crm.add_lead("a@x.com", "A", "referral", "r1")
        crm.qualify(lead, "r1")
        crm.convert(lead, 999, "r1")
        self.assertEqual(crm.forecast(), {"open": 1, "weighted": 99, "won": 0})

    def test_lost_amounts_are_not_counted(self):
        crm = crm_with(*REPS)
        lead = crm.add_lead("a@x.com", "A", "referral", "r1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 5000, "r1")
        crm.advance(opp, "lost", "r1")
        self.assertEqual(crm.forecast(), {"open": 0, "weighted": 0, "won": 0})

    def test_only_named_keys_returned(self):
        self.assertEqual(set(crm_with(*REPS).forecast()), {"open", "weighted", "won"})


class TestAtomicityDetails(unittest.TestCase):
    def _snapshot(self, crm):
        return (
            {k: dict(v) for k, v in crm.leads.items()},
            {k: dict(v) for k, v in crm.opps.items()},
            list(crm.log),
            list(crm._waiting),
            crm._lead_seq,
            crm._opp_seq,
        )

    def test_failed_calls_change_no_counters_and_leave_no_log(self):
        crm = crm_with(*REPS)
        lead = crm.add_lead("a@x.com", "A", "referral", "r1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 60000, "r1")
        crm.advance(opp, "proposal", "r1")
        snapshot = self._snapshot(crm)
        attempts = [
            lambda: crm.add_lead("bad", "A", "web", "r1"),
            lambda: crm.add_lead("a@x.com", "A", "web", "r1"),
            lambda: crm.qualify("L99", "r1"),
            lambda: crm.qualify(lead, "r1"),
            lambda: crm.convert("L99", 10, "r1"),
            lambda: crm.convert(lead, 10, "r1"),
            lambda: crm.advance(opp, "negotiation", "r1"),  # manager gate
            lambda: crm.advance(opp, "won", "r1"),
            lambda: crm.discount(opp, 0, "m1"),
            lambda: crm.discount(opp, 31, "m1"),
            lambda: crm.transfer(opp, "r1", "m1"),
            lambda: crm.transfer(opp, "m1", "m1"),
        ]
        for attempt in attempts:
            with self.assertRaises((ValueError, PermissionError, DuplicateLeadError)):
                attempt()
            self.assertEqual(self._snapshot(crm), snapshot)

    def test_unknown_actor_does_not_create_a_lead(self):
        crm = crm_with(*REPS)
        with self.assertRaises(PermissionError):
            crm.add_lead("a@x.com", "A", "web", "ghost")
        self.assertEqual(crm.leads, {})
        self.assertEqual(crm.log, [])
        self.assertEqual(crm._waiting, [])
        self.assertEqual(crm._lead_seq, 0)

if __name__ == "__main__":
    unittest.main()
