import unittest

from crm import CRM


def reps(r1_cap=1, r2_cap=2):
    return [
        {"id": "r1", "role": "rep", "capacity": r1_cap},
        {"id": "r2", "role": "rep", "capacity": r2_cap},
        {"id": "m1", "role": "manager", "capacity": 0},
    ]


def single_rep(capacity=10):
    return [
        {"id": "r1", "role": "rep", "capacity": capacity},
        {"id": "m1", "role": "manager", "capacity": 0},
    ]


def qualified_opp(crm, email, actor, amount=1000, lead_actor=None):
    lead_id = crm.add_lead(email, "N", "referral", lead_actor or actor)
    crm.qualify(lead_id, lead_actor or actor)
    return crm.convert(lead_id, amount, actor)


class TestAdvance(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(reps())
        self.opp = qualified_opp(self.crm, "a@corp.io", "r1")

    def test_happy_path(self):
        self.crm.advance(self.opp, "proposal", "r1")
        self.assertEqual(self.crm.opps[self.opp]["stage"], "proposal")
        self.crm.advance(self.opp, "negotiation", "r1")
        self.assertEqual(self.crm.opps[self.opp]["stage"], "negotiation")
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

    def test_manager_may_advance_any_opp(self):
        self.crm.advance(self.opp, "proposal", "m1")
        self.assertEqual(self.crm.opps[self.opp]["stage"], "proposal")

    def test_missing_opp(self):
        with self.assertRaises(ValueError):
            self.crm.advance("O99", "proposal", "m1")

    def test_invalid_stage_name(self):
        for stage in ("qualified", "PROSPECT", "", None, 3):
            with self.assertRaises(ValueError, msg=repr(stage)):
                self.crm.advance(self.opp, stage, "r1")

    def test_stage_validity_precedes_permission(self):
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "bogus", "r2")

    def test_non_owner_rep_forbidden(self):
        with self.assertRaises(PermissionError):
            self.crm.advance(self.opp, "proposal", "r2")
        self.assertEqual(self.crm.opps[self.opp]["stage"], "prospect")

    def test_no_skipping(self):
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "negotiation", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "won", "r1")

    def test_lost_from_any_open_stage(self):
        self.crm.advance(self.opp, "lost", "r1")
        self.assertEqual(self.crm.opps[self.opp]["stage"], "lost")

    def test_final_stage_is_terminal(self):
        self.crm.advance(self.opp, "lost", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "won", "m1")

    def test_negotiation_above_threshold_needs_manager(self):
        crm = CRM(single_rep())
        opp = qualified_opp(crm, "big@corp.io", "r1", amount=60000)
        crm.advance(opp, "proposal", "r1")
        with self.assertRaises(PermissionError):
            crm.advance(opp, "negotiation", "r1")
        self.assertEqual(crm.opps[opp]["stage"], "proposal")
        crm.advance(opp, "negotiation", "m1")
        self.assertEqual(crm.opps[opp]["stage"], "negotiation")

    def test_negotiation_at_threshold_allowed_for_rep(self):
        crm = CRM(single_rep())
        opp = qualified_opp(crm, "edge@corp.io", "r1", amount=50000)
        crm.advance(opp, "proposal", "r1")
        crm.advance(opp, "negotiation", "r1")
        self.assertEqual(crm.opps[opp]["stage"], "negotiation")

    def test_failed_advance_logs_nothing(self):
        before = list(self.crm.log)
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "won", "r1")
        self.assertEqual(self.crm.log, before)


class TestAdvanceQueue(unittest.TestCase):
    def setUp(self):
        self.crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        self.opp = qualified_opp(self.crm, "a@corp.io", "r1")
        # fill r2's only slot so later leads truly have to wait
        filler = self.crm.add_lead("z@corp.io", "Z", "web", "r1")
        self.assertEqual(self.crm.leads[filler]["owner"], "r2")

    def test_win_assigns_oldest_waiting_lead(self):
        b = self.crm.add_lead("b@corp.io", "B", "referral", "r1")
        c = self.crm.add_lead("c@corp.io", "C", "referral", "r1")
        self.assertIsNone(self.crm.leads[b]["owner"])
        self.assertIsNone(self.crm.leads[c]["owner"])
        self.crm.advance(self.opp, "proposal", "r1")
        self.crm.advance(self.opp, "negotiation", "r1")
        self.crm.advance(self.opp, "won", "r1")
        self.assertEqual(self.crm.leads[b]["owner"], "r1")
        self.assertIsNone(self.crm.leads[c]["owner"])
        self.assertIn(("assign", b, "system"), self.crm.log)
        self.assertNotIn(("assign", c, "system"), self.crm.log)

    def test_only_one_slot_freed(self):
        b = self.crm.add_lead("b@corp.io", "B", "referral", "r1")
        c = self.crm.add_lead("c@corp.io", "C", "referral", "r1")
        self.crm.advance(self.opp, "lost", "r1")
        self.assertEqual(self.crm.leads[b]["owner"], "r1")
        self.assertIsNone(self.crm.leads[c]["owner"])
        self.assertEqual(
            [entry for entry in self.crm.log if entry[0] == "assign"],
            [("assign", b, "system")],
        )

    def test_queue_fills_all_free_capacity(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 2},
                   {"id": "m1", "role": "manager", "capacity": 0}])
        lead = crm.add_lead("a@corp.io", "A", "referral", "r1")
        crm.qualify(lead, "r1")
        first_opp = crm.convert(lead, 100, "r1")
        second_lead = crm.add_lead("b@corp.io", "B", "referral", "r1")
        crm.qualify(second_lead, "r1")
        second_opp = crm.convert(second_lead, 100, "r1")
        waiting_one = crm.add_lead("c@corp.io", "C", "web", "r1")
        waiting_two = crm.add_lead("d@corp.io", "D", "web", "r1")
        self.assertIsNone(crm.leads[waiting_one]["owner"])
        self.assertIsNone(crm.leads[waiting_two]["owner"])
        crm.advance(first_opp, "lost", "r1")
        self.assertEqual(crm.leads[waiting_one]["owner"], "r1")
        self.assertIsNone(crm.leads[waiting_two]["owner"])
        crm.advance(second_opp, "lost", "r1")
        self.assertEqual(crm.leads[waiting_two]["owner"], "r1")

    def test_no_assign_log_without_waiting_leads(self):
        self.crm.advance(self.opp, "lost", "r1")
        self.assertFalse([e for e in self.crm.log if e[0] == "assign"])

    def test_advance_log_precedes_assign_log(self):
        self.crm.add_lead("b@corp.io", "B", "referral", "r1")
        b = "L3"
        before = len(self.crm.log)
        self.crm.advance(self.opp, "lost", "r1")
        self.assertEqual(self.crm.log[before:], [("advance", self.opp, "r1"),
                                                 ("assign", b, "system")])

    def test_manager_may_qualify_queue_lead_but_it_stays_unowned(self):
        waiting = self.crm.add_lead("w@corp.io", "W", "referral", "r1")
        self.assertIsNone(self.crm.leads[waiting]["owner"])
        self.crm.qualify(waiting, "m1")
        self.assertEqual(self.crm.leads[waiting]["status"], "qualified")
        self.assertIsNone(self.crm.leads[waiting]["owner"])
        with self.assertRaises(ValueError):
            self.crm.convert(waiting, 100, "m1")


class TestDiscount(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(reps())
        self.opp = qualified_opp(self.crm, "a@corp.io", "r1", amount=1000)

    def test_ok(self):
        self.crm.discount(self.opp, 10, "r1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 900)
        self.assertEqual(self.crm.opps[self.opp]["original_amount"], 1000)
        self.assertEqual(self.crm.log[-1], ("discount", self.opp, "r1"))

    def test_pct_validation(self):
        for pct in (0, 31, -5, True, 5.5, "5", None):
            with self.assertRaises(ValueError, msg=repr(pct)):
                self.crm.discount(self.opp, pct, "r1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 1000)

    def test_missing_opp(self):
        with self.assertRaises(ValueError):
            self.crm.discount("O99", 5, "m1")

    def test_permission(self):
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp, 5, "r2")

    def test_manager_can_discount_up_to_30(self):
        self.crm.discount(self.opp, 30, "m1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 700)

    def test_rep_capped_at_10(self):
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp, 11, "r1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 1000)
        self.crm.discount(self.opp, 10, "r1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 900)

    def test_final_stage(self):
        self.crm.advance(self.opp, "lost", "r1")
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp, 5, "m1")

    def test_cumulative_limit(self):
        self.crm.discount(self.opp, 30, "m1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 700)
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp, 1, "m1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 700)

    def test_cumulative_limit_exact_boundary(self):
        crm = CRM(reps())
        opp = qualified_opp(crm, "b@corp.io", "r1", amount=1000)
        crm.discount(opp, 20, "m1")
        self.assertEqual(crm.opps[opp]["amount"], 800)
        crm.discount(opp, 12, "m1")
        self.assertEqual(crm.opps[opp]["amount"], 704)
        with self.assertRaises(ValueError):
            crm.discount(opp, 1, "m1")

    def test_rep_repeated_discount_hits_cap(self):
        for _ in range(3):
            self.crm.discount(self.opp, 10, "r1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 729)
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp, 10, "r1")

    def test_amount_floor_rounding(self):
        crm = CRM(reps())
        opp = qualified_opp(crm, "c@corp.io", "r1", amount=101)
        crm.discount(opp, 10, "r1")
        self.assertEqual(crm.opps[opp]["amount"], 90)

    def test_failure_logs_nothing(self):
        before = list(self.crm.log)
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp, 50, "m1")
        self.assertEqual(self.crm.log, before)


class TestTransfer(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(reps(r1_cap=2, r2_cap=2))
        self.opp = qualified_opp(self.crm, "a@corp.io", "r1")
        self.assertEqual(self.crm.opps[self.opp]["owner"], "r1")

    def test_ok(self):
        self.crm.transfer(self.opp, "r2", "m1")
        self.assertEqual(self.crm.opps[self.opp]["owner"], "r2")
        self.assertEqual(self.crm.log[-1], ("transfer", self.opp, "m1"))

    def test_missing_opp(self):
        with self.assertRaises(ValueError):
            self.crm.transfer("O99", "r2", "m1")

    def test_actor_must_be_manager(self):
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.opp, "r2", "r1")
        self.assertEqual(self.crm.opps[self.opp]["owner"], "r1")

    def test_actor_unknown(self):
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.opp, "r2", "ghost")

    def test_new_owner_must_be_a_rep(self):
        for target in ("m1", "nobody", None, 7):
            with self.assertRaises(ValueError, msg=repr(target)):
                self.crm.transfer(self.opp, target, "m1")

    def test_final_stage(self):
        self.crm.advance(self.opp, "lost", "r1")
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "r2", "m1")

    def test_same_owner(self):
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "r1", "m1")

    def test_target_at_capacity(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 5},
                   {"id": "r2", "role": "rep", "capacity": 1},
                   {"id": "m1", "role": "manager", "capacity": 0}])
        opp = qualified_opp(crm, "a@corp.io", "r1")
        # r2 has the lowest load, so it takes the lead and becomes full
        lead = crm.add_lead("b@corp.io", "B", "web", "r1")
        self.assertEqual(crm.leads[lead]["owner"], "r2")
        self.assertEqual(crm._load("r2"), 1)
        with self.assertRaises(ValueError):
            crm.transfer(opp, "r2", "m1")
        self.assertEqual(crm.opps[opp]["owner"], "r1")

    def test_previous_owner_slot_is_free(self):
        self.assertEqual(self.crm._load("r1"), 1)
        self.crm.transfer(self.opp, "r2", "m1")
        self.assertEqual(self.crm._load("r1"), 0)
        self.assertEqual(self.crm._load("r2"), 1)
        lead_id = self.crm.add_lead("b@corp.io", "B", "referral", "m1")
        self.assertEqual(self.crm.leads[lead_id]["owner"], "r1")

    def test_failed_transfer_changes_nothing(self):
        before = list(self.crm.log)
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "r1", "m1")
        self.assertEqual(self.crm.log, before)
        self.assertEqual(self.crm.opps[self.opp]["owner"], "r1")


class TestForecast(unittest.TestCase):
    def test_empty(self):
        crm = CRM(reps())
        self.assertEqual(crm.forecast(), {"open": 0, "weighted": 0, "won": 0})

    def test_weighted_and_won(self):
        crm = CRM(single_rep())
        prospect = qualified_opp(crm, "a@corp.io", "r1", amount=1000)
        proposal = qualified_opp(crm, "b@corp.io", "r1", amount=2000)
        crm.advance(proposal, "proposal", "r1")
        negotiation = qualified_opp(crm, "c@corp.io", "r1", amount=3000)
        crm.advance(negotiation, "proposal", "r1")
        crm.advance(negotiation, "negotiation", "r1")
        won = qualified_opp(crm, "d@corp.io", "r1", amount=4000)
        crm.advance(won, "proposal", "r1")
        crm.advance(won, "negotiation", "r1")
        crm.advance(won, "won", "r1")
        lost = qualified_opp(crm, "e@corp.io", "r1", amount=5000)
        crm.advance(lost, "lost", "r1")
        result = crm.forecast()
        self.assertEqual(result["open"], 3)
        self.assertEqual(result["weighted"], 100 + 600 + 1800)
        self.assertEqual(result["won"], 4000)

    def test_uses_current_amount_and_does_not_log(self):
        crm = CRM(reps())
        opp = qualified_opp(crm, "a@corp.io", "r1", amount=1000)
        crm.discount(opp, 10, "r1")
        before = list(crm.log)
        result = crm.forecast()
        self.assertEqual(result, {"open": 1, "weighted": 90, "won": 0})
        self.assertEqual(crm.log, before)


if __name__ == "__main__":
    unittest.main()
