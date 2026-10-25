import unittest

from crm import CRM, DuplicateLeadError


def make(reps=None):
    if reps is None:
        reps = [
            {"id": "r1", "role": "rep", "capacity": 2},
            {"id": "r2", "role": "rep", "capacity": 2},
            {"id": "m1", "role": "manager", "capacity": 5},
        ]
    return CRM(reps)


class TestAddLead(unittest.TestCase):
    def test_normalizes_and_scores(self):
        crm = make()
        lead_id = crm.add_lead("  Alice@Example.COM ", "  Alice  ", "web", "r1")
        self.assertEqual(lead_id, "L1")
        lead = crm.leads[lead_id]
        self.assertEqual(lead["email"], "alice@example.com")
        self.assertEqual(lead["name"], "Alice")
        self.assertEqual(lead["score"], 25)  # 10 + 15 for business domain
        self.assertEqual(lead["status"], "new")
        self.assertEqual(lead["owner"], "r1")
        self.assertEqual(crm.log, [("add_lead", "L1", "r1")])

    def test_source_scores(self):
        crm = make()
        crm.add_lead("a@corp.io", "A", "referral", "r1")
        crm.add_lead("b@gmail.com", "B", "referral", "r1")
        crm.add_lead("c@corp.io", "C", "event", "r1")
        self.assertEqual(crm.leads["L1"]["score"], 45)
        self.assertEqual(crm.leads["L2"]["score"], 30)
        self.assertEqual(crm.leads["L3"]["score"], 35)

    def test_invalid_emails(self):
        crm = make()
        bad = ["no-at", "a@@b.co", "@b.co", "a@b", "a@.co", "a@b.", 42, None]
        for value in bad:
            with self.assertRaises(ValueError):
                crm.add_lead(value, "Name", "web", "r1")
        self.assertEqual(crm.leads, {})
        self.assertEqual(crm.log, [])

    def test_invalid_name_and_source(self):
        crm = make()
        for name in ["", "   ", None, 5]:
            with self.assertRaises(ValueError):
                crm.add_lead("a@b.co", name, "web", "r1")
        with self.assertRaises(ValueError):
            crm.add_lead("a@b.co", "A", "ads", "r1")

    def test_unknown_actor_checked_first(self):
        crm = make()
        with self.assertRaises(PermissionError):
            crm.add_lead("nope", "", "bad", "ghost")

    def test_duplicate_email(self):
        crm = make()
        crm.add_lead("alice@example.com", "A", "web", "r1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            crm.add_lead(" ALICE@example.com ", "B", "web", "r1")
        self.assertEqual(ctx.exception.existing_id, "L1")
        self.assertEqual(list(crm.leads), ["L1"])
        self.assertEqual(len(crm.log), 1)

    def test_lowest_load_and_tie_break(self):
        crm = make([{"id": "r2", "role": "rep", "capacity": 5},
                    {"id": "r1", "role": "rep", "capacity": 5}])
        first = crm.add_lead("a@a.co", "A", "web", "r1")
        second = crm.add_lead("b@b.co", "B", "web", "r1")
        third = crm.add_lead("c@c.co", "C", "web", "r1")
        self.assertEqual(crm.leads[first]["owner"], "r1")
        self.assertEqual(crm.leads[second]["owner"], "r2")
        self.assertEqual(crm.leads[third]["owner"], "r1")

    def test_managers_never_own(self):
        crm = make([{"id": "m1", "role": "manager", "capacity": 9}])
        lead_id = crm.add_lead("a@a.co", "A", "web", "m1")
        self.assertIsNone(crm.leads[lead_id]["owner"])
        self.assertEqual(crm.waiting, ["L1"])

    def test_capacity_sends_lead_to_queue(self):
        crm = make([{"id": "r1", "role": "rep", "capacity": 1}])
        crm.add_lead("a@a.co", "A", "web", "r1")
        second = crm.add_lead("b@b.co", "B", "web", "r1")
        self.assertIsNone(crm.leads[second]["owner"])
        self.assertEqual(crm.waiting, ["L2"])


class TestQualify(unittest.TestCase):
    def test_flow(self):
        crm = make()
        crm.add_lead("a@corp.io", "A", "web", "r1")  # score 25
        with self.assertRaises(ValueError):
            crm.qualify("L1", "r1")  # score below 30
        crm.add_lead("b@corp.io", "B", "referral", "r1")  # score 45
        crm.qualify("L2", "m1")
        self.assertEqual(crm.leads["L2"]["status"], "qualified")
        self.assertEqual(crm.log[-1], ("qualify", "L2", "m1"))
        with self.assertRaises(ValueError):
            crm.qualify("L2", "m1")  # already qualified

    def test_permissions_and_unknown(self):
        crm = make()
        crm.add_lead("b@corp.io", "B", "referral", "r1")
        with self.assertRaises(ValueError):
            crm.qualify("L99", "r1")
        with self.assertRaises(PermissionError):
            crm.qualify("L1", "r2")
        crm.qualify("L1", "m1")  # managers may qualify anything
        self.assertEqual(crm.leads["L1"]["status"], "qualified")

    def test_failures_do_not_log(self):
        crm = make()
        crm.add_lead("b@corp.io", "B", "referral", "r1")
        before = list(crm.log)
        with self.assertRaises(PermissionError):
            crm.qualify("L1", "r2")
        self.assertEqual(crm.log, before)


class TestConvert(unittest.TestCase):
    def setUp(self):
        self.crm = make()
        self.crm.add_lead("a@corp.io", "A", "referral", "r1")
        self.crm.qualify("L1", "r1")

    def test_creates_opportunity(self):
        opp_id = self.crm.convert("L1", 1500, "r1")
        self.assertEqual(opp_id, "O1")
        opp = self.crm.opps[opp_id]
        self.assertEqual(opp["lead_id"], "L1")
        self.assertEqual(opp["owner"], "r1")
        self.assertEqual(opp["amount"], 1500)
        self.assertEqual(opp["original_amount"], 1500)
        self.assertEqual(opp["stage"], "prospect")
        self.assertEqual(self.crm.leads["L1"]["status"], "converted")
        self.assertEqual(self.crm.log[-1], ("convert", "O1", "r1"))

    def test_invalid_amounts(self):
        for amount in [0, -3, True, False, 1.5, "100", None]:
            with self.assertRaises(ValueError):
                self.crm.convert("L1", amount, "r1")

    def test_requires_qualified_and_owner(self):
        with self.assertRaises(ValueError):
            self.crm.convert("L99", 10, "r1")
        with self.assertRaises(PermissionError):
            self.crm.convert("L1", 10, "r2")
        self.crm.add_lead("b@corp.io", "B", "referral", "r1")
        with self.assertRaises(ValueError):
            self.crm.convert("L2", 10, "m1")  # still new

    def test_converted_lead_cannot_be_converted_again(self):
        self.crm.convert("L1", 10, "r1")
        with self.assertRaises(ValueError):
            self.crm.convert("L1", 10, "r1")


class TestAdvance(unittest.TestCase):
    def setUp(self):
        self.crm = make()
        self.crm.add_lead("a@corp.io", "A", "referral", "r1")
        self.crm.qualify("L1", "r1")
        self.opp_id = self.crm.convert("L1", 1000, "r1")

    def test_stage_order(self):
        crm, opp = self.crm, self.opp_id
        with self.assertRaises(ValueError):
            crm.advance(opp, "closed", "r1")
        with self.assertRaises(ValueError):
            crm.advance(opp, "won", "r1")  # skips stages
        crm.advance(opp, "proposal", "r1")
        self.assertEqual(crm.opps[opp]["stage"], "proposal")
        crm.advance(opp, "negotiation", "r1")
        crm.advance(opp, "won", "r1")
        self.assertEqual(crm.opps[opp]["stage"], "won")
        with self.assertRaises(ValueError):
            crm.advance(opp, "lost", "r1")  # already final

    def test_lost_from_any_open_stage(self):
        self.crm.advance(self.opp_id, "lost", "r1")
        self.assertEqual(self.crm.opps[self.opp_id]["stage"], "lost")

    def test_big_deal_needs_manager(self):
        self.crm.opps[self.opp_id]["amount"] = 60000
        self.crm.advance(self.opp_id, "proposal", "r1")
        with self.assertRaises(PermissionError):
            self.crm.advance(self.opp_id, "negotiation", "r1")
        self.assertEqual(self.crm.opps[self.opp_id]["stage"], "proposal")
        self.crm.advance(self.opp_id, "negotiation", "m1")
        self.assertEqual(self.crm.opps[self.opp_id]["stage"], "negotiation")

    def test_permission(self):
        with self.assertRaises(PermissionError):
            self.crm.advance(self.opp_id, "proposal", "r2")
        with self.assertRaises(ValueError):
            self.crm.advance("O9", "proposal", "r1")

    def test_win_assigns_waiting_lead(self):
        crm = make([{"id": "r1", "role": "rep", "capacity": 1}])
        crm.add_lead("a@corp.io", "A", "referral", "r1")
        crm.add_lead("b@corp.io", "B", "referral", "r1")  # queued
        self.assertEqual(crm.waiting, ["L2"])
        crm.qualify("L1", "r1")
        opp = crm.convert("L1", 500, "r1")
        crm.advance(opp, "proposal", "r1")
        crm.advance(opp, "negotiation", "r1")
        crm.advance(opp, "won", "r1")
        self.assertEqual(crm.leads["L2"]["owner"], "r1")
        self.assertEqual(crm.waiting, [])
        self.assertEqual(crm.log[-1], ("assign", "L2", "system"))

    def test_failed_advance_leaves_state(self):
        before = list(self.crm.log)
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp_id, "negotiation", "r1")
        self.assertEqual(self.crm.opps[self.opp_id]["stage"], "prospect")
        self.assertEqual(self.crm.log, before)


class TestDiscount(unittest.TestCase):
    def setUp(self):
        self.crm = make()
        self.crm.add_lead("a@corp.io", "A", "referral", "r1")
        self.crm.qualify("L1", "r1")
        self.opp_id = self.crm.convert("L1", 1000, "r1")

    def test_valid_discount(self):
        self.crm.discount(self.opp_id, 10, "r1")
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 900)
        self.assertEqual(self.crm.log[-1], ("discount", "O1", "r1"))

    def test_invalid_pct(self):
        for pct in [0, 31, -1, True, 1.0, "10"]:
            with self.assertRaises(ValueError):
                self.crm.discount(self.opp_id, pct, "m1")

    def test_rep_limit_and_manager(self):
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp_id, 15, "r1")
        self.crm.discount(self.opp_id, 15, "m1")
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 850)

    def test_cumulative_cap(self):
        self.crm.discount(self.opp_id, 20, "m1")
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 800)
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp_id, 20, "m1")
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 800)
        self.crm.discount(self.opp_id, 10, "m1")
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 720)

    def test_final_stage_rejected(self):
        self.crm.advance(self.opp_id, "lost", "r1")
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp_id, 5, "m1")

    def test_permission(self):
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp_id, 5, "r2")


class TestTransfer(unittest.TestCase):
    def setUp(self):
        self.crm = make()
        self.crm.add_lead("a@corp.io", "A", "referral", "r1")
        self.crm.qualify("L1", "r1")
        self.opp_id = self.crm.convert("L1", 1000, "r1")

    def test_transfer_and_free_slot(self):
        crm = self.crm
        crm.transfer(self.opp_id, "r2", "m1")
        self.assertEqual(crm.opps[self.opp_id]["owner"], "r2")
        self.assertEqual(crm.log[-1], ("transfer", "O1", "m1"))
        # r1's slot is free again: next lead goes to r1.
        lead = crm.add_lead("b@corp.io", "B", "web", "m1")
        self.assertEqual(crm.leads[lead]["owner"], "r1")

    def test_validation_order(self):
        crm = self.crm
        with self.assertRaises(PermissionError):
            crm.transfer(self.opp_id, "r2", "r1")  # actor not manager
        with self.assertRaises(ValueError):
            crm.transfer(self.opp_id, "m1", "m1")  # target is not a rep
        with self.assertRaises(ValueError):
            crm.transfer(self.opp_id, "ghost", "m1")
        with self.assertRaises(ValueError):
            crm.transfer(self.opp_id, "r1", "m1")  # same owner
        with self.assertRaises(ValueError):
            crm.transfer("O9", "r2", "m1")

    def test_target_at_capacity(self):
        crm = make([{"id": "r1", "role": "rep", "capacity": 2},
                    {"id": "r2", "role": "rep", "capacity": 1},
                    {"id": "m1", "role": "manager", "capacity": 9}])
        crm.add_lead("a@corp.io", "A", "referral", "r1")
        crm.add_lead("b@corp.io", "B", "referral", "r2")  # r2 now full
        crm.qualify("L1", "r1")
        opp = crm.convert("L1", 1000, "r1")
        with self.assertRaises(ValueError):
            crm.transfer(opp, "r2", "m1")
        self.assertEqual(crm.opps[opp]["owner"], "r1")

    def test_final_stage_rejected(self):
        self.crm.advance(self.opp_id, "lost", "m1")
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp_id, "r2", "m1")


class TestForecast(unittest.TestCase):
    def test_forecast_numbers(self):
        crm = make()
        crm.add_lead("a@corp.io", "A", "referral", "r1")
        crm.add_lead("b@corp.io", "B", "referral", "r1")
        crm.qualify("L1", "r1")
        crm.qualify("L2", "m1")
        o1 = crm.convert("L1", 1000, "r1")
        crm.convert("L2", 2000, "m1")
        self.assertEqual(crm.forecast(), {"open": 2, "weighted": 300, "won": 0})
        crm.advance(o1, "proposal", "r1")
        self.assertEqual(crm.forecast(), {"open": 2, "weighted": 500, "won": 0})
        crm.advance(o1, "negotiation", "r1")
        crm.advance(o1, "won", "r1")
        self.assertEqual(crm.forecast(), {"open": 1, "weighted": 200, "won": 1000})

    def test_forecast_does_not_log(self):
        crm = make()
        before = len(crm.log)
        crm.forecast()
        self.assertEqual(len(crm.log), before)


class TestSpecEdgeCases(unittest.TestCase):
    def test_add_lead_check_order_duplicate_after_source(self):
        crm = make()
        crm.add_lead("a@corp.io", "A", "web", "r1")
        with self.assertRaises(ValueError):
            crm.add_lead(" A@corp.io ", "A", "ads", "r1")
        with self.assertRaises(ValueError):
            crm.add_lead(" A@corp.io ", "  ", "web", "r1")
        with self.assertRaises(ValueError):
            crm.add_lead("not-an-email", "A", "ads", "r1")
        self.assertEqual(list(crm.leads), ["L1"])

    def test_unknown_actor_beats_every_other_error(self):
        crm = make()
        with self.assertRaises(PermissionError):
            crm.add_lead(None, None, None, None)
        with self.assertRaises(PermissionError):
            crm.qualify("L404", object())
        with self.assertRaises(PermissionError):
            crm.convert("L404", -1, [])
        with self.assertRaises(PermissionError):
            crm.advance("O404", "nope", {})
        with self.assertRaises(PermissionError):
            crm.discount("O404", "x", 3)
        with self.assertRaises(PermissionError):
            crm.transfer("O404", [], 3)

    def test_unhashable_arguments_use_documented_errors(self):
        crm = make()
        with self.assertRaises(ValueError):
            crm.add_lead("a@corp.io", "A", ["web"], "r1")
        crm.add_lead("a@corp.io", "A", "referral", "r1")
        crm.qualify("L1", "r1")
        opp = crm.convert("L1", 100, "r1")
        with self.assertRaises(ValueError):
            crm.advance(opp, ["proposal"], "r1")
        with self.assertRaises(ValueError):
            crm.transfer(opp, ["r2"], "m1")

    def test_qualified_unowned_lead_cannot_convert_until_assigned(self):
        crm = make([{"id": "m1", "role": "manager", "capacity": 5}])
        lead = crm.add_lead("a@corp.io", "A", "referral", "m1")
        crm.qualify(lead, "m1")
        self.assertEqual(crm.leads[lead]["status"], "qualified")
        self.assertIsNone(crm.leads[lead]["owner"])
        with self.assertRaises(ValueError):
            crm.convert(lead, 100, "m1")
        self.assertEqual(crm.opps, {})
        self.assertEqual(crm.leads[lead]["status"], "qualified")

    def test_queue_drains_in_fifo_order_and_logs_each(self):
        crm = make([{"id": "r1", "role": "rep", "capacity": 1},
                    {"id": "r2", "role": "rep", "capacity": 1}])
        crm.add_lead("a@corp.io", "A", "referral", "r1")
        crm.add_lead("b@corp.io", "B", "referral", "r2")
        q1 = crm.add_lead("c@corp.io", "C", "referral", "r1")
        q2 = crm.add_lead("d@corp.io", "D", "referral", "r1")
        self.assertEqual((q1, q2), ("L3", "L4"))
        crm.qualify("L1", "r1")
        crm.qualify("L2", "r2")
        opp1 = crm.convert("L1", 100, "r1")
        opp2 = crm.convert("L2", 100, "r2")
        crm.advance(opp1, "lost", "r1")
        self.assertEqual(crm.leads["L3"]["owner"], "r1")
        self.assertIsNone(crm.leads["L4"]["owner"])
        self.assertEqual(crm.log[-2:], [("advance", opp1, "r1"),
                                        ("assign", "L3", "system")])
        crm.advance(opp2, "lost", "r2")
        self.assertEqual(crm.leads["L4"]["owner"], "r2")
        self.assertEqual(crm.waiting, [])
        self.assertEqual(crm.log[-2:], [("advance", opp2, "r2"),
                                        ("assign", "L4", "system")])

    def test_transfer_frees_previous_owner_slot(self):
        # A queue normally implies every rep is full, so lift r2's capacity to
        # create the only state where a transfer both succeeds and drains.
        crm = make([{"id": "r1", "role": "rep", "capacity": 1},
                    {"id": "r2", "role": "rep", "capacity": 1},
                    {"id": "m1", "role": "manager", "capacity": 5}])
        crm.add_lead("a@corp.io", "A", "referral", "r1")
        crm.add_lead("b@corp.io", "B", "referral", "r2")
        waiting = crm.add_lead("c@corp.io", "C", "referral", "r1")
        crm.qualify("L1", "r1")
        opp = crm.convert("L1", 100, "r1")
        crm.users["r2"]["capacity"] = 2
        crm.transfer(opp, "r2", "m1")
        self.assertEqual(crm.leads[waiting]["owner"], "r1")
        self.assertEqual(crm.log[-2:], [("transfer", opp, "m1"),
                                        ("assign", waiting, "system")])

    def test_negotiation_threshold_is_strict(self):
        crm = make([{"id": "r1", "role": "rep", "capacity": 5},
                    {"id": "m1", "role": "manager", "capacity": 5}])
        crm.add_lead("a@corp.io", "A", "referral", "r1")
        crm.qualify("L1", "r1")
        at_limit = crm.convert("L1", 50000, "r1")
        crm.advance(at_limit, "proposal", "r1")
        crm.advance(at_limit, "negotiation", "r1")  # exactly 50000: rep ok

        crm.add_lead("b@corp.io", "B", "referral", "r1")
        crm.qualify("L2", "r1")
        over = crm.convert("L2", 50001, "r1")
        crm.advance(over, "proposal", "r1")
        with self.assertRaises(PermissionError):
            crm.advance(over, "negotiation", "r1")
        crm.advance(over, "negotiation", "m1")

    def test_forecast_excludes_lost(self):
        crm = make([{"id": "r1", "role": "rep", "capacity": 5},
                    {"id": "m1", "role": "manager", "capacity": 5}])
        crm.add_lead("a@corp.io", "A", "referral", "r1")
        crm.add_lead("b@corp.io", "B", "referral", "r1")
        crm.qualify("L1", "r1")
        crm.qualify("L2", "r1")
        o1 = crm.convert("L1", 1001, "r1")
        o2 = crm.convert("L2", 999, "r1")
        crm.advance(o1, "proposal", "r1")
        crm.advance(o2, "lost", "r1")
        self.assertEqual(crm.forecast(), {"open": 1, "weighted": 300, "won": 0})
        crm.advance(o1, "negotiation", "r1")
        crm.advance(o1, "won", "r1")
        self.assertEqual(crm.forecast(), {"open": 0, "weighted": 0, "won": 1001})

    def test_discount_rounding_and_cumulative_cap(self):
        crm = make()
        crm.add_lead("a@corp.io", "A", "referral", "r1")
        crm.qualify("L1", "r1")
        opp = crm.convert("L1", 333, "r1")
        crm.discount(opp, 10, "r1")
        self.assertEqual(crm.opps[opp]["amount"], 299)
        crm.discount(opp, 20, "m1")
        self.assertEqual(crm.opps[opp]["amount"], 239)
        with self.assertRaises(ValueError):
            crm.discount(opp, 3, "m1")
        self.assertEqual(crm.opps[opp]["amount"], 239)


if __name__ == "__main__":
    unittest.main()
