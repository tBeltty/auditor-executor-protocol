"""Unit tests for the pipeline half of crm.py: qualify, convert, advance,
discount, transfer, slot freeing/queue assignment and forecast."""

import unittest

from crm import CRM


def crm_two(cap_a=5, cap_b=5):
    return CRM(
        [
            {"id": "r1", "role": "rep", "capacity": cap_a},
            {"id": "r2", "role": "rep", "capacity": cap_b},
            {"id": "m1", "role": "manager", "capacity": 0},
        ]
    )


def maxed_rep(capacity=1):
    """CRM whose r1 is the only rep, plus a manager for overrides."""
    return CRM(
        [
            {"id": "r1", "role": "rep", "capacity": capacity},
            {"id": "m1", "role": "manager", "capacity": 0},
        ]
    )


class QualifyTests(unittest.TestCase):
    def setUp(self):
        self.crm = crm_two()
        self.lead = self.crm.add_lead("a@corp.com", "A", "referral", "r1")
        self.assertEqual(self.crm.leads[self.lead]["owner"], "r1")

    def test_owner_qualifies(self):
        self.crm.qualify(self.lead, "r1")
        self.assertEqual(self.crm.leads[self.lead]["status"], "qualified")
        self.assertEqual(self.crm.log[-1], ("qualify", self.lead, "r1"))

    def test_manager_qualifies(self):
        self.crm.qualify(self.lead, "m1")
        self.assertEqual(self.crm.leads[self.lead]["status"], "qualified")

    def test_other_rep_cannot_qualify(self):
        with self.assertRaises(PermissionError):
            self.crm.qualify(self.lead, "r2")
        self.assertEqual(self.crm.leads[self.lead]["status"], "new")

    def test_missing_lead(self):
        with self.assertRaises(ValueError):
            self.crm.qualify("L404", "r1")
        with self.assertRaises(ValueError):
            self.crm.qualify(None, "r1")

    def test_status_must_be_new(self):
        self.crm.qualify(self.lead, "r1")
        with self.assertRaises(ValueError):
            self.crm.qualify(self.lead, "r1")
        self.assertEqual(sum(1 for entry in self.crm.log if entry[0] == "qualify"), 1)

    def test_score_must_reach_30(self):
        web = self.crm.add_lead("b@gmail.com", "B", "web", "r2")
        self.assertEqual(self.crm.leads[web]["score"], 10)
        with self.assertRaises(ValueError):
            self.crm.qualify(web, "m1")
        event_consumer = self.crm.add_lead("c@gmail.com", "C", "event", "r2")
        self.assertEqual(self.crm.leads[event_consumer]["score"], 20)
        with self.assertRaises(ValueError):
            self.crm.qualify(event_consumer, "m1")
        event_corp = self.crm.add_lead("d@corp.com", "D", "event", "r2")
        self.assertEqual(self.crm.leads[event_corp]["score"], 35)
        self.crm.qualify(event_corp, "m1")
        self.assertEqual(self.crm.leads[event_corp]["status"], "qualified")

    def test_queued_lead_can_be_qualified_only_by_manager(self):
        crm = maxed_rep(1)
        first = crm.add_lead("a@corp.com", "A", "referral", "r1")
        queued = crm.add_lead("b@corp.com", "B", "referral", "r1")
        self.assertIsNone(crm.leads[queued]["owner"])
        with self.assertRaises(PermissionError):
            crm.qualify(queued, "r1")
        crm.qualify(queued, "m1")
        self.assertEqual(crm.leads[queued]["status"], "qualified")
        self.assertEqual(crm.leads[first]["status"], "new")

    def test_actor_check_precedes_existence(self):
        with self.assertRaises(PermissionError):
            self.crm.qualify("L404", "ghost")


class ConvertTests(unittest.TestCase):
    def setUp(self):
        self.crm = crm_two()
        self.lead = self.crm.add_lead("a@corp.com", "A", "referral", "r1")
        self.crm.qualify(self.lead, "r1")

    def test_convert_creates_opportunity(self):
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

    def test_manager_can_convert_someone_elses_lead(self):
        opp_id = self.crm.convert(self.lead, 500, "m1")
        self.assertEqual(self.crm.opps[opp_id]["owner"], "r1")

    def test_other_rep_cannot_convert(self):
        with self.assertRaises(PermissionError):
            self.crm.convert(self.lead, 500, "r2")
        self.assertEqual(self.crm.opps, {})
        self.assertEqual(self.crm.leads[self.lead]["status"], "qualified")

    def test_amount_must_be_positive_int_not_bool(self):
        for amount in [0, -5, 1.5, True, False, "10", None]:
            with self.subTest(amount=amount):
                with self.assertRaises(ValueError):
                    self.crm.convert(self.lead, amount, "r1")
        self.assertEqual(self.crm.opps, {})

    def test_amount_check_precedes_permission(self):
        with self.assertRaises(ValueError):
            self.crm.convert(self.lead, 0, "r2")

    def test_status_must_be_qualified(self):
        new_lead = self.crm.add_lead("b@corp.com", "B", "referral", "r2")
        with self.assertRaises(ValueError):
            self.crm.convert(new_lead, 100, "r2")
        with self.assertRaises(ValueError):
            self.crm.convert(new_lead, 100, "m1")

    def test_lead_must_have_owner(self):
        crm = maxed_rep(1)
        crm.add_lead("a@corp.com", "A", "referral", "r1")
        queued = crm.add_lead("b@corp.com", "B", "referral", "r1")
        crm.qualify(queued, "m1")
        with self.assertRaises(ValueError):
            crm.convert(queued, 100, "m1")
        self.assertEqual(crm.opps, {})

    def test_failed_conversions_do_not_consume_ids(self):
        with self.assertRaises(ValueError):
            self.crm.convert("L404", 100, "r1")
        with self.assertRaises(ValueError):
            self.crm.convert(self.lead, 0, "r1")
        self.assertEqual(self.crm.convert(self.lead, 100, "r1"), "O1")
        # A second qualified lead continues the sequence.
        second = self.crm.add_lead("b@corp.com", "B", "referral", "r2")
        self.crm.qualify(second, "r2")
        self.assertEqual(self.crm.convert(second, 200, "r2"), "O2")


class AdvanceTests(unittest.TestCase):
    def setUp(self):
        self.crm = crm_two()
        lead = self.crm.add_lead("a@corp.com", "A", "referral", "r1")
        self.crm.qualify(lead, "r1")
        self.opp = self.crm.convert(lead, 1000, "r1")

    def test_full_stage_walk(self):
        self.crm.advance(self.opp, "proposal", "r1")
        self.crm.advance(self.opp, "negotiation", "r1")
        self.crm.advance(self.opp, "won", "r1")
        self.assertEqual(self.crm.opps[self.opp]["stage"], "won")
        self.assertEqual(
            [entry[0] for entry in self.crm.log],
            ["add_lead", "qualify", "convert", "advance", "advance", "advance"],
        )

    def test_lost_allowed_from_every_open_stage(self):
        crm = crm_two()
        for stage in ["prospect", "proposal"]:
            lead = crm.add_lead("%s@corp.com" % stage, "A", "referral", "r1")
            crm.qualify(lead, "r1")
            opp = crm.convert(lead, 100, "r1")
            if stage == "proposal":
                crm.advance(opp, "proposal", "r1")
            crm.advance(opp, "lost", "r1")
            self.assertEqual(crm.opps[opp]["stage"], "lost")

    def test_unknown_stage_and_stage_order(self):
        for bad in ["contact", "", None, "PROSPECT"]:
            with self.subTest(stage=bad):
                with self.assertRaises(ValueError):
                    self.crm.advance(self.opp, bad, "r1")
        for bad in ["negotiation", "won", "prospect"]:
            with self.subTest(stage=bad):
                with self.assertRaises(ValueError):
                    self.crm.advance(self.opp, bad, "r1")
        self.assertEqual(self.crm.opps[self.opp]["stage"], "prospect")

    def test_stage_membership_precedes_permission(self):
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "bogus", "r2")

    def test_non_owner_rep_cannot_advance(self):
        with self.assertRaises(PermissionError):
            self.crm.advance(self.opp, "proposal", "r2")
        self.assertEqual(self.crm.opps[self.opp]["stage"], "prospect")

    def test_manager_can_advance(self):
        self.crm.advance(self.opp, "proposal", "m1")
        self.assertEqual(self.crm.opps[self.opp]["stage"], "proposal")

    def test_final_stage_cannot_move(self):
        self.crm.advance(self.opp, "lost", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "lost", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "prospect", "r1")
        self.assertEqual(self.crm.opps[self.opp]["stage"], "lost")

    def test_final_current_checked_before_transition(self):
        crm = crm_two()
        lead = crm.add_lead("z@corp.com", "Z", "referral", "r1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 100, "r1")
        crm.advance(opp, "proposal", "r1")
        crm.advance(opp, "negotiation", "r1")
        crm.advance(opp, "won", "r1")
        # "proposal" is a valid stage but not reachable from final; check 4 wins.
        with self.assertRaises(ValueError):
            crm.advance(opp, "proposal", "r1")

    def test_negotiation_over_50000_needs_manager(self):
        crm = crm_two()
        lead = crm.add_lead("big@corp.com", "Big", "referral", "r1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 60000, "r1")
        crm.advance(opp, "proposal", "r1")
        with self.assertRaises(PermissionError):
            crm.advance(opp, "negotiation", "r1")
        self.assertEqual(crm.opps[opp]["stage"], "proposal")
        crm.advance(opp, "negotiation", "m1")
        self.assertEqual(crm.opps[opp]["stage"], "negotiation")

    def test_exactly_50000_does_not_need_manager(self):
        crm = crm_two()
        lead = crm.add_lead("edge@corp.com", "Edge", "referral", "r1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 50000, "r1")
        crm.advance(opp, "proposal", "r1")
        crm.advance(opp, "negotiation", "r1")
        self.assertEqual(crm.opps[opp]["stage"], "negotiation")

    def test_discounted_amount_can_fall_under_manager_threshold(self):
        crm = crm_two()
        lead = crm.add_lead("big@corp.com", "Big", "referral", "r1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 60000, "r1")
        crm.advance(opp, "proposal", "r1")
        crm.discount(opp, 20, "m1")  # 48000
        self.assertEqual(crm.opps[opp]["amount"], 48000)
        crm.advance(opp, "negotiation", "r1")
        self.assertEqual(crm.opps[opp]["stage"], "negotiation")


class QueueAssignmentTests(unittest.TestCase):
    def test_win_frees_slot_and_assigns_oldest_waiting_lead(self):
        crm = maxed_rep(1)
        lead = crm.add_lead("a@corp.com", "A", "referral", "r1")
        waiting = crm.add_lead("b@corp.com", "B", "referral", "r1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 1000, "r1")
        self.assertEqual(crm._load("r1"), 1)
        crm.advance(opp, "proposal", "r1")
        crm.advance(opp, "negotiation", "r1")
        crm.advance(opp, "won", "r1")
        self.assertEqual(crm.leads[waiting]["owner"], "r1")
        self.assertEqual(list(crm.waiting), [])
        self.assertEqual(crm.log[-2:], [("advance", opp, "r1"), ("assign", waiting, "system")])

    def test_lost_also_frees_slot(self):
        crm = maxed_rep(1)
        lead = crm.add_lead("a@corp.com", "A", "referral", "r1")
        waiting = crm.add_lead("b@corp.com", "B", "referral", "r1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 100, "r1")
        crm.advance(opp, "lost", "r1")
        self.assertEqual(crm.leads[waiting]["owner"], "r1")
        self.assertEqual(list(crm.waiting), [])

    def test_assignment_stops_when_capacity_is_reached_in_fifo_order(self):
        crm = maxed_rep(2)
        l1 = crm.add_lead("a@corp.com", "A", "referral", "r1")
        l2 = crm.add_lead("b@corp.com", "B", "referral", "r1")
        l3 = crm.add_lead("c@corp.com", "C", "referral", "r1")
        l4 = crm.add_lead("d@corp.com", "D", "referral", "r1")
        self.assertEqual([l3, l4], list(crm.waiting))
        crm.qualify(l1, "r1")
        opp = crm.convert(l1, 100, "r1")
        crm.advance(opp, "proposal", "r1")
        crm.advance(opp, "negotiation", "r1")
        crm.advance(opp, "won", "r1")
        # Before win: l2 new + opp prospect = 2. After: 1; assign l3 -> 2; stop.
        self.assertEqual(crm.leads[l3]["owner"], "r1")
        self.assertIsNone(crm.leads[l4]["owner"])
        self.assertEqual(list(crm.waiting), [l4])
        # Convert l2, win it: frees one, assigns l4.
        crm.qualify(l2, "r1")
        opp2 = crm.convert(l2, 100, "r1")
        crm.advance(opp2, "proposal", "r1")
        crm.advance(opp2, "negotiation", "r1")
        crm.advance(opp2, "won", "r1")
        self.assertEqual(crm.leads[l4]["owner"], "r1")
        self.assertEqual(list(crm.waiting), [])

    def test_non_final_advance_does_not_assign(self):
        crm = maxed_rep(1)
        lead = crm.add_lead("a@corp.com", "A", "referral", "r1")
        waiting = crm.add_lead("b@corp.com", "B", "referral", "r1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 100, "r1")
        crm.advance(opp, "proposal", "r1")
        self.assertIsNone(crm.leads[waiting]["owner"])
        self.assertEqual(list(crm.waiting), [waiting])


class DiscountTests(unittest.TestCase):
    def setUp(self):
        self.crm = crm_two()
        lead = self.crm.add_lead("a@corp.com", "A", "referral", "r1")
        self.crm.qualify(lead, "r1")
        self.opp = self.crm.convert(lead, 1000, "r1")

    def test_owner_discounts_ten_percent(self):
        self.crm.discount(self.opp, 10, "r1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 900)
        self.assertEqual(self.crm.opps[self.opp]["original_amount"], 1000)
        self.assertEqual(self.crm.log[-1], ("discount", self.opp, "r1"))

    def test_manager_discounts_up_to_thirty(self):
        self.crm.discount(self.opp, 30, "m1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 700)

    def test_pct_validation(self):
        for pct in [0, 31, -1, 10.5, True, "10", None]:
            with self.subTest(pct=pct):
                with self.assertRaises(ValueError):
                    self.crm.discount(self.opp, pct, "r1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 1000)

    def test_pct_check_precedes_permission(self):
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp, 0, "r2")

    def test_non_owner_rep_is_denied(self):
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp, 10, "r2")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 1000)

    def test_rep_cannot_exceed_ten(self):
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp, 11, "r1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 1000)

    def test_final_stage_checked_before_rep_limit(self):
        self.crm.advance(self.opp, "lost", "r1")
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp, 20, "r1")

    def test_final_stage_denied_to_manager(self):
        self.crm.advance(self.opp, "lost", "r1")
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp, 10, "m1")

    def test_cumulative_discount_cap_uses_original_amount(self):
        self.crm.discount(self.opp, 10, "r1")  # 900
        self.crm.discount(self.opp, 10, "r1")  # 810
        self.crm.discount(self.opp, 10, "r1")  # 729
        self.assertEqual(self.crm.opps[self.opp]["amount"], 729)
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp, 10, "r1")  # 656 < 700
        self.assertEqual(self.crm.opps[self.opp]["amount"], 729)

    def test_integer_floor_division(self):
        crm = crm_two()
        lead = crm.add_lead("b@corp.com", "B", "referral", "r1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 101, "r1")
        crm.discount(opp, 10, "r1")
        self.assertEqual(crm.opps[opp]["amount"], 90)  # 101 * 90 // 100


class TransferTests(unittest.TestCase):
    def setUp(self):
        self.crm = crm_two()
        lead = self.crm.add_lead("a@corp.com", "A", "referral", "r1")
        self.crm.qualify(lead, "r1")
        self.opp = self.crm.convert(lead, 1000, "r1")

    def test_manager_transfers_to_rep(self):
        self.crm.transfer(self.opp, "r2", "m1")
        self.assertEqual(self.crm.opps[self.opp]["owner"], "r2")
        self.assertEqual(self.crm.log[-1], ("transfer", self.opp, "m1"))

    def test_only_manager_may_transfer(self):
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.opp, "r2", "r1")
        self.assertEqual(self.crm.opps[self.opp]["owner"], "r1")

    def test_new_owner_validation(self):
        for bad in ["nobody", "m1", None, 3]:
            with self.subTest(new_owner=bad):
                with self.assertRaises(ValueError):
                    self.crm.transfer(self.opp, bad, "m1")
        self.assertEqual(self.crm.opps[self.opp]["owner"], "r1")

    def test_manager_check_precedes_new_owner_check(self):
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.opp, "nobody", "r1")

    def test_final_stage_cannot_transfer(self):
        self.crm.advance(self.opp, "lost", "r1")
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "r2", "m1")
        self.assertEqual(self.crm.opps[self.opp]["owner"], "r1")

    def test_same_owner_rejected(self):
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "r1", "m1")

    def test_new_owner_must_have_capacity(self):
        crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 5},
                {"id": "r2", "role": "rep", "capacity": 0},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        lead = crm.add_lead("a@corp.com", "A", "referral", "r1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 100, "r1")
        with self.assertRaises(ValueError):
            crm.transfer(opp, "r2", "m1")

    def test_transfer_frees_previous_owner_slot(self):
        crm = maxed_rep(1)
        lead = crm.add_lead("a@corp.com", "A", "referral", "r1")
        waiting = crm.add_lead("b@corp.com", "B", "referral", "r1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 100, "r1")
        # r1 is full (one open opp); a second rep with room is added.
        crm.users["r2"] = {"id": "r2", "role": "rep", "capacity": 1}
        crm.transfer(opp, "r2", "m1")
        self.assertEqual(crm.opps[opp]["owner"], "r2")
        self.assertEqual(crm.leads[waiting]["owner"], "r1")
        self.assertEqual(crm.log[-2:], [("transfer", opp, "m1"), ("assign", waiting, "system")])
        self.assertEqual(list(crm.waiting), [])
        self.assertEqual(crm._load("r2"), 1)


class ForecastTests(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(CRM([]).forecast(), {"open": 0, "weighted": 0, "won": 0})

    def test_mixed_pipeline(self):
        crm = crm_two(cap_a=10, cap_b=10)
        amounts = {"prospect": 1000, "proposal": 2000, "negotiation": 3000, "won": 4000, "lost": 5000}
        for index, (stage, amount) in enumerate(amounts.items()):
            lead = crm.add_lead("l%d@corp.com" % index, "L", "referral", "r1")
            crm.qualify(lead, "m1")
            opp = crm.convert(lead, amount, "m1")
            if stage == "proposal":
                crm.advance(opp, "proposal", "m1")
            elif stage == "negotiation":
                crm.advance(opp, "proposal", "m1")
                crm.advance(opp, "negotiation", "m1")
            elif stage == "won":
                crm.advance(opp, "proposal", "m1")
                crm.advance(opp, "negotiation", "m1")
                crm.advance(opp, "won", "m1")
            elif stage == "lost":
                crm.advance(opp, "lost", "m1")
        self.assertEqual(
            crm.forecast(),
            {
                "open": 3,
                "weighted": 1000 * 10 // 100 + 2000 * 30 // 100 + 3000 * 60 // 100,
                "won": 4000,
            },
        )

    def test_forecast_does_not_log(self):
        crm = crm_two()
        before = list(crm.log)
        crm.forecast()
        self.assertEqual(crm.log, before)


class LoadTests(unittest.TestCase):
    def test_load_counts_open_leads_and_open_opps_only(self):
        crm = crm_two(cap_a=10, cap_b=10)
        lead = crm.add_lead("a@corp.com", "A", "referral", "r1")
        self.assertEqual(crm._load("r1"), 1)
        crm.qualify(lead, "r1")
        self.assertEqual(crm._load("r1"), 1)
        opp = crm.convert(lead, 1000, "r1")
        self.assertEqual(crm._load("r1"), 1)  # converted lead + open opp
        crm.advance(opp, "proposal", "r1")
        self.assertEqual(crm._load("r1"), 1)
        crm.advance(opp, "negotiation", "r1")
        crm.advance(opp, "won", "r1")
        self.assertEqual(crm._load("r1"), 0)

    def test_won_or_lost_opps_do_not_block_new_leads(self):
        crm = maxed_rep(1)
        lead = crm.add_lead("a@corp.com", "A", "referral", "r1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 1000, "r1")
        crm.advance(opp, "proposal", "r1")
        crm.advance(opp, "negotiation", "r1")
        crm.advance(opp, "won", "r1")
        # The won opportunity no longer counts toward load, so a new lead fits.
        new_lead = crm.add_lead("b@corp.com", "B", "web", "r1")
        self.assertEqual(crm.leads[new_lead]["owner"], "r1")
        self.assertEqual(list(crm.waiting), [])


class AtomicityTests(unittest.TestCase):
    def setUp(self):
        self.crm = crm_two()
        lead = self.crm.add_lead("a@corp.com", "A", "referral", "r1")
        self.crm.qualify(lead, "r1")
        self.opp = self.crm.convert(lead, 1000, "r1")

    def test_failed_advance_changes_nothing(self):
        before_log = list(self.crm.log)
        before_opp = dict(self.crm.opps[self.opp])
        with self.assertRaises(PermissionError):
            self.crm.advance(self.opp, "proposal", "r2")
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "won", "r1")
        self.assertEqual(self.crm.log, before_log)
        self.assertEqual(self.crm.opps[self.opp], before_opp)

    def test_failed_discount_changes_nothing(self):
        before_log = list(self.crm.log)
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp, 20, "r1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 1000)
        self.assertEqual(self.crm.log, before_log)
        # A manager may take 30%, landing exactly on the cumulative floor.
        self.crm.discount(self.opp, 30, "m1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 700)
        amount = self.crm.opps[self.opp]["amount"]
        log = list(self.crm.log)
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp, 1, "m1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], amount)
        self.assertEqual(self.crm.log, log)
        self.assertEqual(len(log), len(before_log) + 1)

    def test_failed_transfer_changes_nothing(self):
        before_log = list(self.crm.log)
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "r1", "m1")
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.opp, "r2", "r1")
        self.assertEqual(self.crm.log, before_log)
        self.assertEqual(self.crm.opps[self.opp]["owner"], "r1")


if __name__ == "__main__":
    unittest.main()
