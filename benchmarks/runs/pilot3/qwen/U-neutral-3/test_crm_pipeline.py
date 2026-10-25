"""Tests for qualify, convert, advance, discount and transfer, including the
order in which their checks run and the atomicity of failing calls."""

import copy
import unittest

from crm import CRM

TEAM = [
    {"id": "r1", "role": "rep", "capacity": 3},
    {"id": "r2", "role": "rep", "capacity": 3},
    {"id": "m1", "role": "manager", "capacity": 0},
]


def build(reps=None):
    return CRM(copy.deepcopy(reps if reps is not None else TEAM))


def email(n):
    return "lead%d@acme.com" % n


def qualified_lead(crm, n=1, source="referral", actor="m1"):
    lead = crm.add_lead(email(n), "N", source, actor)
    crm.qualify(lead, actor)
    return lead


class QualifyTest(unittest.TestCase):
    def setUp(self):
        self.crm = build()

    def test_owner_qualifies_own_lead(self):
        lead = self.crm.add_lead(email(1), "N", "referral", "m1")
        self.crm.qualify(lead, "r1")
        self.assertEqual(self.crm.leads[lead]["status"], "qualified")
        self.assertEqual(self.crm.log[-1], ("qualify", lead, "r1"))

    def test_manager_qualifies_any_lead(self):
        lead = self.crm.add_lead(email(1), "N", "referral", "m1")
        self.crm.qualify(lead, "m1")
        self.assertEqual(self.crm.leads[lead]["status"], "qualified")
        self.assertEqual(self.crm.log[-1], ("qualify", lead, "m1"))

    def test_other_rep_is_rejected(self):
        lead = self.crm.add_lead(email(1), "N", "referral", "m1")
        with self.assertRaises(PermissionError):
            self.crm.qualify(lead, "r2")
        self.assertEqual(self.crm.leads[lead]["status"], "new")
        self.assertEqual(len(self.crm.log), 1)

    def test_unknown_lead_is_value_error(self):
        with self.assertRaises(ValueError):
            self.crm.qualify("L99", "r1")

    def test_low_score_is_rejected(self):
        for source, expected in (("web", 25), ("event", 35), ("referral", 45)):
            crm = build()
            lead = crm.add_lead(email(1), "N", source, "r1")
            if expected >= 30:
                crm.qualify(lead, "r1")
                self.assertEqual(crm.leads[lead]["status"], "qualified")
            else:
                with self.assertRaises(ValueError):
                    crm.qualify(lead, "r1")
                self.assertEqual(crm.leads[lead]["status"], "new")

    def test_score_30_exactly_qualifies(self):
        lead = self.crm.add_lead("a@gmail.com", "N", "referral", "r1")
        self.assertEqual(self.crm.leads[lead]["score"], 30)
        self.crm.qualify(lead, "r1")
        self.assertEqual(self.crm.leads[lead]["status"], "qualified")

    def test_score_29_is_rejected(self):
        lead = self.crm.add_lead("a@acme.com", "N", "web", "r1")
        self.assertEqual(self.crm.leads[lead]["score"], 25)
        with self.assertRaises(ValueError):
            self.crm.qualify(lead, "r1")

    def test_double_qualify_is_value_error(self):
        lead = qualified_lead(self.crm)
        with self.assertRaises(ValueError):
            self.crm.qualify(lead, "r1")

    def test_converted_lead_cannot_be_qualified(self):
        lead = qualified_lead(self.crm)
        self.crm.convert(lead, 100, "r1")
        with self.assertRaises(ValueError):
            self.crm.qualify(lead, "r1")

    def test_permission_check_precedes_score_check(self):
        lead = self.crm.add_lead(email(1), "N", "web", "m1")  # score 25
        with self.assertRaises(PermissionError):
            self.crm.qualify(lead, "r2")
        with self.assertRaises(ValueError):
            self.crm.qualify(lead, "r1")

    def test_existence_check_precedes_permission_check(self):
        with self.assertRaises(ValueError):
            self.crm.qualify("L404", "r2")


class ConvertTest(unittest.TestCase):
    def setUp(self):
        self.crm = build()
        self.lead = qualified_lead(self.crm)

    def test_happy_path(self):
        opp = self.crm.convert(self.lead, 2500, "r1")
        self.assertEqual(opp, "O1")
        self.assertEqual(
            self.crm.opps["O1"],
            {
                "id": "O1",
                "lead_id": self.lead,
                "owner": "r1",
                "amount": 2500,
                "original_amount": 2500,
                "stage": "prospect",
            },
        )
        self.assertEqual(self.crm.leads[self.lead]["status"], "converted")
        self.assertEqual(self.crm.log[-1], ("convert", "O1", "r1"))

    def test_manager_can_convert(self):
        opp = self.crm.convert(self.lead, 100, "m1")
        self.assertEqual(opp, "O1")
        self.assertEqual(self.crm.log[-1], ("convert", "O1", "m1"))

    def test_ids_increment_per_conversion(self):
        other = qualified_lead(self.crm, n=2)
        self.assertEqual(self.crm.convert(self.lead, 100, "m1"), "O1")
        self.assertEqual(self.crm.convert(other, 100, "m1"), "O2")

    def test_amount_validation(self):
        for bad in (0, -1, -100, 1.0, 2.5, "100", None, [100], True, False):
            with self.assertRaises(ValueError):
                self.crm.convert(self.lead, bad, "r1")
        self.assertEqual(self.crm.opps, {})
        self.assertEqual(self.crm.leads[self.lead]["status"], "qualified")

    def test_amount_one_is_valid(self):
        self.assertEqual(self.crm.convert(self.lead, 1, "r1"), "O1")

    def test_new_lead_cannot_be_converted(self):
        lead = self.crm.add_lead(email(5), "N", "referral", "m1")
        self.assertEqual(self.crm.leads[lead]["status"], "new")
        with self.assertRaises(ValueError):
            self.crm.convert(lead, 100, "m1")

    def test_unowned_lead_cannot_be_converted(self):
        crm = build([{"id": "m1", "role": "manager", "capacity": 0}])
        lead = crm.add_lead(email(1), "N", "referral", "m1")
        self.assertIsNone(crm.leads[lead]["owner"])
        crm.qualify(lead, "m1")
        with self.assertRaises(ValueError):
            crm.convert(lead, 100, "m1")
        self.assertEqual(crm.opps, {})
        self.assertEqual(crm.log, [("add_lead", lead, "m1"), ("qualify", lead, "m1")])

    def test_other_rep_cannot_convert(self):
        with self.assertRaises(PermissionError):
            self.crm.convert(self.lead, 100, "r2")

    def test_check_order_amount_before_permission(self):
        with self.assertRaises(ValueError):
            self.crm.convert(self.lead, 0, "r2")

    def test_check_order_permission_before_status(self):
        # self.lead (L1) went to r1, so this second lead lands on r2: r1 may not act.
        lead = self.crm.add_lead(email(9), "N", "referral", "m1")
        self.assertEqual(self.crm.leads[lead]["owner"], "r2")
        with self.assertRaises(PermissionError):
            self.crm.convert(lead, 100, "r1")

    def test_check_order_status_before_owner(self):
        crm = build([{"id": "m1", "role": "manager", "capacity": 0}])
        lead = crm.add_lead(email(1), "N", "referral", "m1")  # unowned, status new
        with self.assertRaises(ValueError):
            crm.convert(lead, 100, "m1")

    def test_failed_convert_consumes_no_id(self):
        with self.assertRaises(ValueError):
            self.crm.convert(self.lead, 0, "r1")
        self.assertEqual(self.crm.convert(self.lead, 100, "r1"), "O1")


class AdvanceTest(unittest.TestCase):
    def setUp(self):
        self.crm = build()
        self.lead = qualified_lead(self.crm)
        self.opp = self.crm.convert(self.lead, 1000, "r1")

    def test_happy_path_through_the_stages(self):
        for stage in ("proposal", "negotiation", "won"):
            self.crm.advance(self.opp, stage, "r1")
            self.assertEqual(self.crm.opps[self.opp]["stage"], stage)
        self.assertEqual(
            [entry for entry in self.crm.log if entry[0] == "advance"],
            [("advance", self.opp, "r1")] * 3,
        )

    def test_manager_may_advance_any_opportunity(self):
        self.crm.advance(self.opp, "proposal", "m1")
        self.assertEqual(self.crm.opps[self.opp]["stage"], "proposal")

    def test_other_rep_may_not(self):
        with self.assertRaises(PermissionError):
            self.crm.advance(self.opp, "proposal", "r2")

    def test_skipping_forward_is_rejected(self):
        for stage in ("won", "negotiation", "prospect", "proposal"):
            crm = build()
            lead = qualified_lead(crm)
            opp = crm.convert(lead, 1000, "r1")
            if stage == "proposal":
                continue  # that one is legal
            with self.assertRaises(ValueError):
                crm.advance(opp, stage, "r1")
            self.assertEqual(crm.opps[opp]["stage"], "prospect")

    def test_backward_is_rejected(self):
        self.crm.advance(self.opp, "proposal", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "prospect", "r1")

    def test_lost_from_every_open_stage(self):
        for steps, stage in (((), "prospect"), (("proposal",), "proposal"),
                            (("proposal", "negotiation"), "negotiation")):
            crm = build()
            lead = qualified_lead(crm)
            opp = crm.convert(lead, 1000, "r1")
            for partial in steps:
                crm.advance(opp, partial, "r1")
            crm.advance(opp, "lost", "r1")
            self.assertEqual(crm.opps[opp]["stage"], "lost")

    def test_final_stages_are_final(self):
        for closing in ("won", "lost"):
            crm = build()
            lead = qualified_lead(crm)
            opp = crm.convert(lead, 1000, "m1")
            if closing == "won":
                for stage in ("proposal", "negotiation", "won"):
                    crm.advance(opp, stage, "m1")
            else:
                crm.advance(opp, "lost", "m1")
            self.assertEqual(crm.opps[opp]["stage"], closing)
            for stage in ("prospect", "proposal", "negotiation", "won", "lost"):
                with self.assertRaises(ValueError):
                    crm.advance(opp, stage, "m1")

    def test_unknown_stage(self):
        for bad in ("closed", "Won", "", None, 0, "deferred"):
            with self.assertRaises(ValueError):
                self.crm.advance(self.opp, bad, "r1")
        self.assertEqual(self.crm.opps[self.opp]["stage"], "prospect")

    def test_unknown_opportunity(self):
        with self.assertRaises(ValueError):
            self.crm.advance("O42", "proposal", "r1")

    def test_big_negotiation_needs_a_manager(self):
        crm = build()
        lead = qualified_lead(crm)
        opp = crm.convert(lead, 50001, "r1")
        crm.advance(opp, "proposal", "r1")
        with self.assertRaises(PermissionError):
            crm.advance(opp, "negotiation", "r1")
        self.assertEqual(crm.opps[opp]["stage"], "proposal")
        crm.advance(opp, "negotiation", "m1")
        self.assertEqual(crm.opps[opp]["stage"], "negotiation")

    def test_boundary_50000_needs_no_manager(self):
        crm = build()
        lead = qualified_lead(crm)
        opp = crm.convert(lead, 50000, "r1")
        crm.advance(opp, "proposal", "r1")
        crm.advance(opp, "negotiation", "r1")
        self.assertEqual(crm.opps[opp]["stage"], "negotiation")

    def test_big_won_and_lost_need_no_manager(self):
        crm = build()
        lead = qualified_lead(crm)
        opp = crm.convert(lead, 999999, "r1")
        crm.advance(opp, "proposal", "r1")
        crm.advance(opp, "negotiation", "m1")
        crm.advance(opp, "won", "r1")
        self.assertEqual(crm.opps[opp]["stage"], "won")

    def test_manager_rule_is_checked_after_stage_legality(self):
        crm = build()
        lead = qualified_lead(crm)
        opp = crm.convert(lead, 90000, "r1")
        with self.assertRaises(ValueError):
            crm.advance(opp, "negotiation", "r1")  # prospect -> negotiation skips one

    def test_manager_rule_is_checked_after_ownership(self):
        crm = build()
        lead = qualified_lead(crm)
        opp = crm.convert(lead, 90000, "r1")
        crm.advance(opp, "proposal", "r1")
        with self.assertRaises(PermissionError):
            crm.advance(opp, "negotiation", "r2")

    def test_amount_threshold_uses_current_amount(self):
        crm = build()
        lead = qualified_lead(crm)
        opp = crm.convert(lead, 60000, "r1")
        crm.advance(opp, "proposal", "r1")
        crm.discount(opp, 30, "m1")  # 60000 -> 42000
        self.assertEqual(crm.opps[opp]["amount"], 42000)
        crm.advance(opp, "negotiation", "r1")
        self.assertEqual(crm.opps[opp]["stage"], "negotiation")

    def test_failed_advance_leaves_stage_and_log(self):
        self.crm.advance(self.opp, "proposal", "r1")
        snapshot_stage = self.crm.opps[self.opp]["stage"]
        before = copy.deepcopy(self.crm.log)
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "won", "r1")
        self.assertEqual(self.crm.opps[self.opp]["stage"], snapshot_stage)
        self.assertEqual(self.crm.log, before)


class DiscountTest(unittest.TestCase):
    def setUp(self):
        self.crm = build()
        self.lead = qualified_lead(self.crm)
        self.opp = self.crm.convert(self.lead, 1000, "r1")

    def test_rep_limit_of_ten(self):
        self.crm.discount(self.opp, 10, "r1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 900)
        self.assertEqual(self.crm.log[-1], ("discount", self.opp, "r1"))
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp, 11, "r1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 900)

    def test_manager_up_to_thirty(self):
        self.crm.discount(self.opp, 30, "m1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 700)

    def test_pct_validation(self):
        for bad in (0, -1, 31, 100, "10", 1.5, None, True, False, [10]):
            with self.assertRaises(ValueError):
                self.crm.discount(self.opp, bad, "m1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 1000)

    def test_unknown_opportunity(self):
        with self.assertRaises(ValueError):
            self.crm.discount("O42", 5, "m1")

    def test_other_rep_cannot_discount(self):
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp, 5, "r2")

    def test_final_stage_blocks_discount(self):
        self.crm.discount(self.opp, 5, "r1")  # discount does not close the stage
        self.crm.advance(self.opp, "proposal", "r1")
        self.crm.advance(self.opp, "negotiation", "m1")
        self.crm.advance(self.opp, "won", "m1")
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp, 5, "r1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 950)

    def test_closed_stage_check_precedes_rep_limit(self):
        self.crm.advance(self.opp, "lost", "r1")
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp, 20, "r1")

    def test_rep_limit_precedes_cumulative_floor(self):
        # Both check 5 (rep over 10%) and check 6 (below the 70% floor) fail here;
        # the permission error is the one that wins.
        crm = build()
        lead = qualified_lead(crm)
        opp = crm.convert(lead, 101, "r1")
        with self.assertRaises(PermissionError):
            crm.discount(opp, 30, "r1")
        self.assertEqual(crm.opps[opp]["amount"], 101)

    def test_cumulative_floor_is_on_original_amount(self):
        crm = build()
        lead = qualified_lead(crm)
        opp = crm.convert(lead, 101, "m1")
        with self.assertRaises(ValueError):
            crm.discount(opp, 30, "m1")  # 101*70//100 = 70 -> 7000 < 7070
        self.assertEqual(crm.opps[opp]["amount"], 101)
        crm.discount(opp, 29, "m1")  # 101*71//100 = 71 -> 7100 >= 7070
        self.assertEqual(crm.opps[opp]["amount"], 71)

    def test_two_step_discount_hits_the_floor(self):
        self.crm.discount(self.opp, 30, "m1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 700)
        for pct in (1, 5, 30):
            with self.assertRaises(ValueError):
                self.crm.discount(self.opp, pct, "m1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 700)
        self.assertEqual(self.crm.opps[self.opp]["original_amount"], 1000)

    def test_floor_allows_the_exact_thirty_percent(self):
        crm = build()
        lead = qualified_lead(crm)
        opp = crm.convert(lead, 1000, "m1")
        crm.discount(opp, 20, "m1")
        self.assertEqual(crm.opps[opp]["amount"], 800)
        crm.discount(opp, 12, "m1")  # 800*88//100 = 704 >= 700
        self.assertEqual(crm.opps[opp]["amount"], 704)
        with self.assertRaises(ValueError):
            crm.discount(opp, 1, "m1")  # 704*99//100 = 696 -> below 700

    def test_original_amount_never_changes(self):
        self.crm.discount(self.opp, 10, "r1")
        self.crm.discount(self.opp, 10, "m1")
        self.assertEqual(self.crm.opps[self.opp]["original_amount"], 1000)
        self.assertEqual(self.crm.opps[self.opp]["amount"], 810)


class TransferTest(unittest.TestCase):
    def setUp(self):
        self.crm = build()
        self.lead = qualified_lead(self.crm)
        self.opp = self.crm.convert(self.lead, 1000, "r1")

    def test_manager_transfers(self):
        self.crm.transfer(self.opp, "r2", "m1")
        self.assertEqual(self.crm.opps[self.opp]["owner"], "r2")
        self.assertEqual(self.crm.log[-1], ("transfer", self.opp, "m1"))

    def test_rep_cannot_transfer(self):
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.opp, "r2", "r1")
        self.assertEqual(self.crm.opps[self.opp]["owner"], "r1")
        self.assertEqual(len(self.crm.log), 3)

    def test_new_owner_must_be_a_known_rep(self):
        for bad in ("r9", "m1", None, 7, ""):
            with self.assertRaises(ValueError):
                self.crm.transfer(self.opp, bad, "m1")
        self.assertEqual(self.crm.opps[self.opp]["owner"], "r1")

    def test_same_owner_rejected(self):
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "r1", "m1")

    def test_final_stage_rejected(self):
        self.crm.advance(self.opp, "lost", "r1")
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "r2", "m1")

    def test_capacity_blocks_transfer(self):
        crm = build([
            {"id": "r1", "role": "rep", "capacity": 2},
            {"id": "r2", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        r2_lead = crm.add_lead(email(2), "N", "web", "m1")  # r1 (load 0 tie -> r1)
        self.assertEqual(crm.leads[r2_lead]["owner"], "r1")
        busy = crm.add_lead(email(3), "N", "web", "m1")
        self.assertEqual(crm.leads[busy]["owner"], "r2")
        lead = qualified_lead(crm, n=1)
        self.assertEqual(crm.leads[lead]["owner"], "r1")
        opp = crm.convert(lead, 1000, "r1")
        with self.assertRaises(ValueError):
            crm.transfer(opp, "r2", "m1")
        self.assertEqual(crm.opps[opp]["owner"], "r1")

    def test_check_order_new_owner_before_stage(self):
        crm = build()
        lead = qualified_lead(crm)
        opp = crm.convert(lead, 1000, "r1")
        crm.advance(opp, "lost", "r1")
        with self.assertRaises(ValueError):
            crm.transfer(opp, "ghost", "m1")

    def test_check_order_stage_before_capacity(self):
        crm = build([
            {"id": "r1", "role": "rep", "capacity": 2},
            {"id": "r2", "role": "rep", "capacity": 0},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        lead = qualified_lead(crm)
        self.assertEqual(crm.leads[lead]["owner"], "r1")
        opp = crm.convert(lead, 1000, "r1")
        crm.advance(opp, "lost", "m1")
        with self.assertRaises(ValueError):
            crm.transfer(opp, "r2", "m1")  # closed stage reported first

    def test_transfer_frees_the_previous_owner_for_new_work(self):
        crm = build([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 2},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        lead = crm.add_lead(email(1), "N", "referral", "m1")
        self.assertEqual(crm.leads[lead]["owner"], "r1")
        crm.qualify(lead, "m1")
        opp = crm.convert(lead, 1000, "m1")
        other = crm.add_lead(email(2), "N", "web", "m1")
        self.assertEqual(crm.leads[other]["owner"], "r2")  # r1 is busy
        crm.log.clear()
        crm.transfer(opp, "r2", "m1")
        self.assertEqual(crm.log, [("transfer", opp, "m1")])  # nobody was waiting
        self.assertEqual(crm.opps[opp]["owner"], "r2")
        # r1's slot is open again, so the next lead lands on r1.
        third = crm.add_lead(email(3), "N", "web", "m1")
        self.assertEqual(crm.leads[third]["owner"], "r1")

    def test_transfer_is_impossible_while_anybody_waits(self):
        # A waiting lead exists only while every rep is at capacity, and a
        # transfer needs a rep with room, so the queue cannot be drained here.
        crm = build([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        first = crm.add_lead(email(1), "N", "referral", "m1")
        second = crm.add_lead(email(2), "N", "referral", "m1")
        waiting = crm.add_lead(email(3), "N", "web", "m1")
        self.assertEqual(
            (crm.leads[first]["owner"], crm.leads[second]["owner"], crm.leads[waiting]["owner"]),
            ("r1", "r2", None),
        )
        crm.qualify(first, "m1")
        opp = crm.convert(first, 1000, "m1")
        with self.assertRaises(ValueError):
            crm.transfer(opp, "r2", "m1")  # r2 is at capacity
        self.assertEqual(crm.leads[waiting]["owner"], None)
        crm.advance(opp, "lost", "m1")  # closing does drain the queue
        self.assertEqual(crm.leads[waiting]["owner"], "r1")

    def test_transfer_with_empty_queue_logs_only_the_transfer(self):
        self.crm.transfer(self.opp, "r2", "m1")
        self.assertEqual(self.crm.log[-1], ("transfer", self.opp, "m1"))
        self.assertNotIn("assign", [entry[0] for entry in self.crm.log])

    def test_failed_transfer_changes_nothing(self):
        before = copy.deepcopy((self.crm.leads, self.crm.opps, self.crm.log))
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.opp, "r2", "r1")
        self.assertEqual((self.crm.leads, self.crm.opps, self.crm.log), before)


if __name__ == "__main__":
    unittest.main()
