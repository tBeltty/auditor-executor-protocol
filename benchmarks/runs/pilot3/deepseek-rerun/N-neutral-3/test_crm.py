import unittest

from crm import CRM, DuplicateLeadError

REPS = [
    {"id": "r1", "role": "rep", "capacity": 2},
    {"id": "r2", "role": "rep", "capacity": 2},
    {"id": "m1", "role": "manager", "capacity": 0},
]


def make(reps=None):
    return CRM(reps or REPS)


class ValidationTests(unittest.TestCase):
    def test_unknown_actor_is_permission_error_first(self):
        crm = make()
        with self.assertRaises(PermissionError):
            crm.add_lead("not-an-email", "", "bogus", "ghost")
        with self.assertRaises(PermissionError):
            crm.add_lead("a@b.com", "A", "web", 123)
        self.assertEqual(crm.log, [])
        self.assertEqual(crm.leads, {})

    def test_email_validation(self):
        crm = make()
        bad = ["nope", "a@@b.com", "@b.com", "a@bcom", "a@.com", "a@b.", "", 42, None]
        for email in bad:
            with self.assertRaises(ValueError, msg=repr(email)):
                crm.add_lead(email, "Name", "web", "r1")
        self.assertEqual(crm.leads, {})
        self.assertEqual(crm.log, [])

    def test_email_normalized(self):
        crm = make()
        lead_id = crm.add_lead("  Alice@Example.COM ", "  Alice  ", "web", "r1")
        lead = crm.leads[lead_id]
        self.assertEqual(lead["email"], "alice@example.com")
        self.assertEqual(lead["name"], "Alice")
        self.assertEqual(lead_id, "L1")

    def test_name_and_source_validation(self):
        crm = make()
        for name in ["", "   ", 7, None]:
            with self.assertRaises(ValueError):
                crm.add_lead("a@b.com", name, "web", "r1")
        with self.assertRaises(ValueError):
            crm.add_lead("a@b.com", "A", "ads", "r1")
        self.assertEqual(crm.leads, {})

    def test_duplicate_lead(self):
        crm = make()
        first = crm.add_lead("dup@example.com", "A", "web", "r1")
        log_len = len(crm.log)
        with self.assertRaises(DuplicateLeadError) as ctx:
            crm.add_lead("  DUP@Example.com  ", "B", "event", "r1")
        self.assertEqual(ctx.exception.existing_id, first)
        self.assertEqual(len(crm.leads), 1)
        self.assertEqual(len(crm.log), log_len)
        # the failed creation must not consume an id
        self.assertEqual(crm.add_lead("other@example.com", "C", "web", "r1"), "L2")


class AddLeadTests(unittest.TestCase):
    def test_score_by_source_and_domain(self):
        crm = make([{"id": "r1", "role": "rep", "capacity": 10}])
        cases = [
            ("a@gmail.com", "web", 10),
            ("b@corp.com", "web", 25),
            ("c@gmail.com", "referral", 30),
            ("d@corp.com", "referral", 45),
            ("e@yahoo.com", "event", 20),
            ("f@outlook.com", "event", 20),
            ("g@corp.com", "event", 35),
        ]
        for email, source, expected in cases:
            lead = crm.leads[crm.add_lead(email, "X", source, "r1")]
            self.assertEqual(lead["score"], expected, email)
            self.assertEqual(lead["status"], "new")

    def test_lowest_load_owner_with_tiebreak(self):
        crm = make(
            [
                {"id": "r9", "role": "rep", "capacity": 5},
                {"id": "r3", "role": "rep", "capacity": 5},
                {"id": "m1", "role": "manager", "capacity": 9},
            ]
        )
        self.assertEqual(crm.leads[crm.add_lead("a@x.com", "A", "web", "m1")]["owner"], "r3")
        self.assertEqual(crm.leads[crm.add_lead("b@x.com", "B", "web", "m1")]["owner"], "r9")
        self.assertEqual(crm.leads[crm.add_lead("c@x.com", "C", "web", "m1")]["owner"], "r3")

    def test_managers_never_own_and_queue_is_fifo(self):
        crm = make([{"id": "m1", "role": "manager", "capacity": 5}])
        lead_id = crm.add_lead("a@x.com", "A", "web", "m1")
        self.assertIsNone(crm.leads[lead_id]["owner"])
        self.assertIn(lead_id, crm.waiting)

    def test_capacity_exhausted_puts_lead_in_queue(self):
        crm = make(
            [
                {"id": "r1", "role": "rep", "capacity": 1},
                {"id": "r2", "role": "rep", "capacity": 1},
            ]
        )
        self.assertEqual(crm.leads[crm.add_lead("a@x.com", "A", "web", "r1")]["owner"], "r1")
        self.assertEqual(crm.leads[crm.add_lead("b@x.com", "B", "web", "r1")]["owner"], "r2")
        third = crm.add_lead("c@x.com", "C", "web", "r1")
        self.assertIsNone(crm.leads[third]["owner"])
        self.assertEqual(crm.waiting, [third])
        self.assertEqual(crm.log[-1], ("add_lead", third, "r1"))

    def test_load_counts_qualified_leads_and_open_opps(self):
        crm = make(
            [
                {"id": "r1", "role": "rep", "capacity": 2},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        l1 = crm.add_lead("a@corp.com", "A", "referral", "m1")  # r1 load 1
        crm.add_lead("b@corp.com", "B", "referral", "m1")  # r1 load 2 (full)
        self.assertEqual(crm.leads[l1]["owner"], "r1")
        queued = crm.add_lead("c@corp.com", "C", "web", "m1")
        self.assertIsNone(crm.leads[queued]["owner"])
        self.assertEqual(crm.waiting, [queued])
        # a converted lead is replaced by its (open) opportunity: load stays 2
        crm.qualify(l1, "m1")
        crm.convert(l1, 1000, "m1")
        self.assertEqual(crm.waiting, [queued])
        crm.advance("O1", "proposal", "m1")
        self.assertEqual(crm.waiting, [queued])


class QualifyTests(unittest.TestCase):
    def test_qualify_flow(self):
        crm = make()
        lead_id = crm.add_lead("a@corp.com", "A", "referral", "r1")
        crm.qualify(lead_id, "r1")
        self.assertEqual(crm.leads[lead_id]["status"], "qualified")
        self.assertEqual(crm.log[-1], ("qualify", lead_id, "r1"))

    def test_qualify_low_score_rejected(self):
        crm = make()
        lead_id = crm.add_lead("a@gmail.com", "A", "web", "r1")
        with self.assertRaises(ValueError):
            crm.qualify(lead_id, "r1")
        self.assertEqual(crm.leads[lead_id]["status"], "new")

    def test_qualify_checks_order(self):
        crm = make()
        with self.assertRaises(ValueError):
            crm.qualify("L404", "r1")
        lead_id = crm.add_lead("a@corp.com", "A", "referral", "r1")
        with self.assertRaises(PermissionError):
            crm.qualify(lead_id, "r2")
        crm.qualify(lead_id, "r1")
        with self.assertRaises(ValueError):  # already qualified
            crm.qualify(lead_id, "m1")

    def test_manager_can_qualify_unowned_lead(self):
        crm = make([{"id": "m1", "role": "manager", "capacity": 0}])
        lead_id = crm.add_lead("a@corp.com", "A", "referral", "m1")
        crm.qualify(lead_id, "m1")
        self.assertEqual(crm.leads[lead_id]["status"], "qualified")
        self.assertEqual(crm.log[-1], ("qualify", lead_id, "m1"))


class ConvertTests(unittest.TestCase):
    def test_convert_creates_opportunity(self):
        crm = make()
        lead_id = crm.add_lead("a@corp.com", "A", "referral", "r1")
        crm.qualify(lead_id, "r1")
        opp_id = crm.convert(lead_id, 5000, "r1")
        self.assertEqual(opp_id, "O1")
        opp = crm.opps[opp_id]
        self.assertEqual(
            opp,
            {
                "id": "O1",
                "lead_id": lead_id,
                "owner": "r1",
                "amount": 5000,
                "original_amount": 5000,
                "stage": "prospect",
            },
        )
        self.assertEqual(crm.leads[lead_id]["status"], "converted")
        self.assertEqual(crm.log[-1], ("convert", "O1", "r1"))

    def test_convert_amount_validation(self):
        crm = make()
        lead_id = crm.add_lead("a@corp.com", "A", "referral", "r1")
        crm.qualify(lead_id, "r1")
        for amount in [0, -5, True, False, 1.5, "10", None]:
            with self.assertRaises(ValueError, msg=repr(amount)):
                crm.convert(lead_id, amount, "r1")
        self.assertEqual(crm.opps, {})

    def test_convert_status_and_permission(self):
        crm = make()
        lead_id = crm.add_lead("a@corp.com", "A", "referral", "r1")
        with self.assertRaises(ValueError):  # not qualified yet
            crm.convert(lead_id, 100, "r1")
        crm.qualify(lead_id, "r1")
        with self.assertRaises(PermissionError):
            crm.convert(lead_id, 100, "r2")
        self.assertEqual(crm.opps, {})
        self.assertEqual(crm.leads[lead_id]["status"], "qualified")

    def test_convert_unowned_lead(self):
        crm = make([{"id": "m1", "role": "manager", "capacity": 0}])
        lead_id = crm.add_lead("a@corp.com", "A", "referral", "m1")
        crm.qualify(lead_id, "m1")
        with self.assertRaises(ValueError):
            crm.convert(lead_id, 100, "m1")
        self.assertEqual(crm.opps, {})
        self.assertEqual(crm.leads[lead_id]["status"], "qualified")


class AdvanceTests(unittest.TestCase):
    def setUp(self):
        self.crm = make()
        lead_id = self.crm.add_lead("a@corp.com", "A", "referral", "r1")
        self.crm.qualify(lead_id, "r1")
        self.opp_id = self.crm.convert(lead_id, 1000, "r1")

    def test_full_pipeline(self):
        for stage in ["proposal", "negotiation", "won"]:
            self.crm.advance(self.opp_id, stage, "r1")
            self.assertEqual(self.crm.opps[self.opp_id]["stage"], stage)
            self.assertEqual(self.crm.log[-1], ("advance", self.opp_id, "r1"))

    def test_invalid_stage_value(self):
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp_id, "closed", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance("O99", "proposal", "r1")

    def test_stage_skips_and_backwards_rejected(self):
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp_id, "negotiation", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp_id, "won", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp_id, "prospect", "r1")
        self.crm.advance(self.opp_id, "proposal", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp_id, "prospect", "r1")

    def test_final_stage_is_terminal(self):
        self.crm.advance(self.opp_id, "lost", "r1")
        for stage in ["prospect", "proposal", "negotiation", "won", "lost"]:
            with self.assertRaises(ValueError):
                self.crm.advance(self.opp_id, stage, "r1")

    def test_permission(self):
        with self.assertRaises(PermissionError):
            self.crm.advance(self.opp_id, "proposal", "r2")
        self.assertEqual(self.crm.opps[self.opp_id]["stage"], "prospect")

    def test_large_amount_negotiation_needs_manager(self):
        lead_id = self.crm.add_lead("b@corp.com", "B", "referral", "r2")
        self.crm.qualify(lead_id, "m1")
        opp_id = self.crm.convert(lead_id, 50001, "r2")
        self.crm.advance(opp_id, "proposal", "r2")
        with self.assertRaises(PermissionError):
            self.crm.advance(opp_id, "negotiation", "r2")
        self.assertEqual(self.crm.opps[opp_id]["stage"], "proposal")
        self.crm.advance(opp_id, "negotiation", "m1")
        self.assertEqual(self.crm.opps[opp_id]["stage"], "negotiation")

    def test_exactly_50000_negotiation_allowed_for_rep(self):
        lead_id = self.crm.add_lead("c@corp.com", "C", "referral", "r2")
        self.crm.qualify(lead_id, "m1")
        opp_id = self.crm.convert(lead_id, 50000, "r2")
        self.crm.advance(opp_id, "proposal", "r2")
        self.crm.advance(opp_id, "negotiation", "r2")
        self.assertEqual(self.crm.opps[opp_id]["stage"], "negotiation")

    def test_winning_frees_slot_and_assigns_queue(self):
        crm = make(
            [
                {"id": "r1", "role": "rep", "capacity": 1},
                {"id": "r2", "role": "rep", "capacity": 1},
            ]
        )
        l1 = crm.add_lead("a@corp.com", "A", "referral", "r1")
        crm.add_lead("b@corp.com", "B", "web", "r1")
        queued = crm.add_lead("c@corp.com", "C", "web", "r1")
        self.assertEqual(crm.leads[queued]["owner"], None)
        crm.qualify(l1, "r1")
        opp_id = crm.convert(l1, 100, "r1")
        crm.advance(opp_id, "proposal", "r1")
        crm.advance(opp_id, "negotiation", "r1")
        crm.advance(opp_id, "won", "r1")
        self.assertEqual(crm.leads[queued]["owner"], "r1")
        self.assertEqual(crm.log[-1], ("assign", queued, "system"))
        self.assertEqual(crm.waiting, [])

    def test_lost_also_frees_slot(self):
        crm = make([{"id": "r1", "role": "rep", "capacity": 1}])
        l1 = crm.add_lead("a@corp.com", "A", "referral", "r1")
        queued = crm.add_lead("b@corp.com", "B", "web", "r1")
        crm.qualify(l1, "r1")
        opp_id = crm.convert(l1, 100, "r1")
        crm.advance(opp_id, "lost", "r1")
        self.assertEqual(crm.leads[queued]["owner"], "r1")
        self.assertEqual(crm.log[-1], ("assign", queued, "system"))


class DiscountTests(unittest.TestCase):
    def setUp(self):
        self.crm = make()
        lead_id = self.crm.add_lead("a@corp.com", "A", "referral", "r1")
        self.crm.qualify(lead_id, "r1")
        self.opp_id = self.crm.convert(lead_id, 1000, "r1")

    def test_discount_applies(self):
        self.crm.discount(self.opp_id, 10, "r1")
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 900)
        self.assertEqual(self.crm.opps[self.opp_id]["original_amount"], 1000)
        self.assertEqual(self.crm.log[-1], ("discount", self.opp_id, "r1"))

    def test_pct_validation(self):
        for pct in [0, 31, -1, True, False, 5.0, "5", None]:
            with self.assertRaises(ValueError, msg=repr(pct)):
                self.crm.discount(self.opp_id, pct, "r1")
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 1000)

    def test_rep_cap_of_ten(self):
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp_id, 11, "r1")
        self.crm.discount(self.opp_id, 30, "m1")
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 700)

    def test_cumulative_floor(self):
        self.crm.discount(self.opp_id, 10, "r1")
        self.crm.discount(self.opp_id, 10, "r1")
        self.crm.discount(self.opp_id, 10, "r1")
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 729)
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp_id, 10, "r1")
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 729)

    def test_cannot_discount_final_or_foreign(self):
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp_id, 5, "r2")
        with self.assertRaises(ValueError):
            self.crm.discount("O7", 5, "r1")
        self.crm.advance(self.opp_id, "lost", "r1")
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp_id, 5, "r1")


class TransferTests(unittest.TestCase):
    def setUp(self):
        self.crm = make()
        lead_id = self.crm.add_lead("a@corp.com", "A", "referral", "r1")
        self.crm.qualify(lead_id, "r1")
        self.opp_id = self.crm.convert(lead_id, 1000, "r1")

    def test_transfer_moves_owner(self):
        self.crm.transfer(self.opp_id, "r2", "m1")
        self.assertEqual(self.crm.opps[self.opp_id]["owner"], "r2")
        self.assertEqual(self.crm.log[-1], ("transfer", self.opp_id, "m1"))

    def test_transfer_requires_manager(self):
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.opp_id, "r2", "r1")
        self.assertEqual(self.crm.opps[self.opp_id]["owner"], "r1")

    def test_transfer_target_validation(self):
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp_id, "ghost", "m1")
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp_id, "m1", "m1")
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp_id, "r1", "m1")
        self.assertEqual(self.crm.opps[self.opp_id]["owner"], "r1")

    def test_transfer_target_capacity(self):
        crm = make(
            [
                {"id": "r1", "role": "rep", "capacity": 2},
                {"id": "r2", "role": "rep", "capacity": 1},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        l1 = crm.add_lead("a@corp.com", "A", "referral", "m1")  # r1 (tie on load -> r1)
        crm.qualify(l1, "m1")
        opp_id = crm.convert(l1, 1000, "m1")
        # fill r2 to capacity
        crm.add_lead("b@corp.com", "B", "web", "m1")
        self.assertEqual(crm.leads["L2"]["owner"], "r2")
        with self.assertRaises(ValueError):
            crm.transfer(opp_id, "r2", "m1")
        self.assertEqual(crm.opps[opp_id]["owner"], "r1")

    def test_transfer_final_stage_rejected(self):
        self.crm.advance(self.opp_id, "lost", "r1")
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp_id, "r2", "m1")

    def test_transfer_frees_previous_owner(self):
        crm = make(
            [
                {"id": "r1", "role": "rep", "capacity": 1},
                {"id": "r2", "role": "rep", "capacity": 2},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        l1 = crm.add_lead("a@corp.com", "A", "referral", "m1")  # r1, now at capacity
        self.assertEqual(crm.leads[l1]["owner"], "r1")
        crm.qualify(l1, "m1")
        opp_id = crm.convert(l1, 1000, "m1")  # r1 still loaded by the open opp
        crm.transfer(opp_id, "r2", "m1")
        self.assertEqual(crm.opps[opp_id]["owner"], "r2")
        # r1's slot is free again, so a new lead lands on r1
        self.assertEqual(crm.leads[crm.add_lead("b@corp.com", "B", "web", "m1")]["owner"], "r1")


class ForecastTests(unittest.TestCase):
    def test_forecast_math_and_no_log(self):
        crm = make([{"id": "r1", "role": "rep", "capacity": 10}, {"id": "m1", "role": "manager", "capacity": 0}])
        amounts = [1000, 2000, 3000, 4000]
        stages = [(), ("proposal",), ("proposal", "negotiation"), ("proposal", "negotiation", "won")]
        for i, (amount, path) in enumerate(zip(amounts, stages)):
            lead = crm.add_lead("u%d@corp.com" % i, "U", "referral", "m1")
            crm.qualify(lead, "m1")
            opp = crm.convert(lead, amount, "m1")
            for stage in path:
                crm.advance(opp, stage, "m1")
        log_len = len(crm.log)
        self.assertEqual(
            crm.forecast(), {"open": 3, "weighted": 100 + 600 + 1800, "won": 4000}
        )
        self.assertEqual(len(crm.log), log_len)

    def test_empty_forecast(self):
        self.assertEqual(make().forecast(), {"open": 0, "weighted": 0, "won": 0})


class LogTests(unittest.TestCase):
    def test_log_entries_are_tuples_and_ordered(self):
        crm = make()
        lead_id = crm.add_lead("a@corp.com", "A", "referral", "r1")
        crm.qualify(lead_id, "r1")
        opp_id = crm.convert(lead_id, 1000, "r1")
        crm.advance(opp_id, "proposal", "r1")
        crm.discount(opp_id, 10, "m1")
        crm.transfer(opp_id, "r2", "m1")
        self.assertEqual(
            crm.log,
            [
                ("add_lead", lead_id, "r1"),
                ("qualify", lead_id, "r1"),
                ("convert", opp_id, "r1"),
                ("advance", opp_id, "r1"),
                ("discount", opp_id, "m1"),
                ("transfer", opp_id, "m1"),
            ],
        )
        self.assertTrue(all(isinstance(entry, tuple) and len(entry) == 3 for entry in crm.log))


if __name__ == "__main__":
    unittest.main()
