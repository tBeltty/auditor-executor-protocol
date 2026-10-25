"""Tests for convert, advance, discount, transfer and forecast."""

import copy
import unittest

from crm import CRM


def make_crm(r1=3, r2=3):
    return CRM([
        {"id": "r1", "role": "rep", "capacity": r1},
        {"id": "r2", "role": "rep", "capacity": r2},
        {"id": "m1", "role": "manager", "capacity": 0},
    ])


def snapshot(crm):
    return copy.deepcopy(crm.leads), copy.deepcopy(crm.opps), list(crm.log)


def qualified_lead(crm, email="lead@corp.com", source="referral"):
    lead_id = crm.add_lead(email, "Lead", source, "m1")
    crm.qualify(lead_id, "m1")
    return lead_id


def make_opp(crm, amount=1000, email="lead@corp.com", source="referral"):
    lead_id = qualified_lead(crm, email, source)
    return crm.convert(lead_id, amount, "m1")


class ConvertTest(unittest.TestCase):
    def test_unknown_lead(self):
        crm = make_crm()
        with self.assertRaises(ValueError):
            crm.convert("L404", 100, "m1")

    def test_invalid_amounts(self):
        crm = make_crm()
        qualified_lead(crm)
        for amount in (0, -1, 1.5, "100", True, False, None):
            with self.subTest(amount=amount):
                with self.assertRaises(ValueError):
                    crm.convert("L1", amount, "m1")
        self.assertEqual(crm.opps, {})

    def test_amount_checked_before_permission(self):
        crm = make_crm()
        qualified_lead(crm)
        with self.assertRaises(ValueError):
            crm.convert("L1", 0, "r2")
        with self.assertRaises(PermissionError):
            crm.convert("L1", 0, "ghost")

    def test_non_owner_cannot_convert(self):
        crm = make_crm()
        qualified_lead(crm)  # owned by r1
        before = snapshot(crm)
        with self.assertRaises(PermissionError):
            crm.convert("L1", 100, "r2")
        self.assertEqual(snapshot(crm), before)

    def test_status_must_be_qualified(self):
        crm = make_crm()
        crm.add_lead("lead@corp.com", "Lead", "referral", "r1")
        with self.assertRaises(ValueError):
            crm.convert("L1", 100, "r1")

    def test_lead_must_have_owner(self):
        crm = CRM([
            {"id": "m1", "role": "manager", "capacity": 0},
            {"id": "r9", "role": "rep", "capacity": 0},
        ])
        lead_id = crm.add_lead("lead@corp.com", "Lead", "referral", "m1")
        crm.qualify(lead_id, "m1")
        self.assertIsNone(crm.leads[lead_id]["owner"])
        before = snapshot(crm)
        with self.assertRaises(ValueError):
            crm.convert(lead_id, 100, "m1")
        self.assertEqual(snapshot(crm), before)

    def test_success_creates_opportunity(self):
        crm = make_crm()
        qualified_lead(crm)
        opp_id = crm.convert("L1", 750, "r1")
        self.assertEqual(opp_id, "O1")
        self.assertEqual(
            crm.opps[opp_id],
            {
                "id": "O1",
                "lead_id": "L1",
                "owner": "r1",
                "amount": 750,
                "original_amount": 750,
                "stage": "prospect",
            },
        )
        self.assertEqual(crm.leads["L1"]["status"], "converted")
        self.assertEqual(crm.log[-1], ("convert", "O1", "r1"))

    def test_failed_conversion_does_not_consume_id(self):
        crm = make_crm()
        qualified_lead(crm)
        with self.assertRaises(ValueError):
            crm.convert("L1", True, "r1")
        self.assertEqual(crm.convert("L1", 100, "r1"), "O1")
        self.assertEqual(list(crm.opps), ["O1"])

    def test_second_opportunity_id_increments(self):
        crm = make_crm()
        first = make_opp(crm, 100, "a@corp.com")
        second = make_opp(crm, 100, "b@corp.com")
        self.assertEqual((first, second), ("O1", "O2"))

    def test_conversion_does_not_assign_waiting_leads(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1}])
        crm.add_lead("a@corp.com", "A", "referral", "r1")
        waiting = crm.add_lead("b@corp.com", "B", "referral", "r1")
        self.assertIsNone(crm.leads[waiting]["owner"])
        crm.qualify("L1", "r1")
        crm.convert("L1", 100, "r1")
        self.assertIsNone(crm.leads[waiting]["owner"])
        self.assertNotIn(("assign", waiting, "system"), crm.log)


class AdvanceTest(unittest.TestCase):
    def test_unknown_opportunity(self):
        crm = make_crm()
        with self.assertRaises(ValueError):
            crm.advance("O9", "proposal", "m1")

    def test_invalid_stage_name(self):
        crm = make_crm()
        opp_id = make_opp(crm)
        with self.assertRaises(ValueError):
            crm.advance(opp_id, "signed", "r1")
        with self.assertRaises(ValueError):
            crm.advance(opp_id, None, "r1")

    def test_invalid_stage_before_permission(self):
        crm = make_crm()
        opp_id = make_opp(crm)
        with self.assertRaises(ValueError):
            crm.advance(opp_id, "bogus", "r2")

    def test_non_owner_cannot_advance(self):
        crm = make_crm()
        opp_id = make_opp(crm)
        before = snapshot(crm)
        with self.assertRaises(PermissionError):
            crm.advance(opp_id, "proposal", "r2")
        self.assertEqual(snapshot(crm), before)

    def test_manager_can_advance_any_opportunity(self):
        crm = make_crm()
        opp_id = make_opp(crm)
        crm.advance(opp_id, "proposal", "m1")
        self.assertEqual(crm.opps[opp_id]["stage"], "proposal")

    def test_transition_rules(self):
        crm = make_crm()
        opp_id = make_opp(crm)
        for bad in ("negotiation", "won", "lost "):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    crm.advance(opp_id, bad, "r1")
        crm.advance(opp_id, "proposal", "r1")
        with self.assertRaises(ValueError):
            crm.advance(opp_id, "won", "r1")
        crm.advance(opp_id, "negotiation", "r1")
        with self.assertRaises(ValueError):
            crm.advance(opp_id, "proposal", "r1")
        crm.advance(opp_id, "won", "r1")
        self.assertEqual(crm.opps[opp_id]["stage"], "won")

    def test_lost_allowed_from_any_open_stage(self):
        crm = make_crm()
        opp_id = make_opp(crm)
        crm.advance(opp_id, "lost", "r1")
        self.assertEqual(crm.opps[opp_id]["stage"], "lost")

    def test_final_stage_is_frozen(self):
        crm = make_crm()
        opp_id = make_opp(crm)
        crm.advance(opp_id, "lost", "r1")
        for stage in ("prospect", "proposal", "won", "lost"):
            with self.subTest(stage=stage):
                with self.assertRaises(ValueError):
                    crm.advance(opp_id, stage, "r1")

    def test_large_negotiation_requires_manager(self):
        crm = make_crm()
        opp_id = make_opp(crm, 50001)
        crm.advance(opp_id, "proposal", "r1")
        before = snapshot(crm)
        with self.assertRaises(PermissionError):
            crm.advance(opp_id, "negotiation", "r1")
        self.assertEqual(snapshot(crm), before)
        crm.advance(opp_id, "negotiation", "m1")
        self.assertEqual(crm.opps[opp_id]["stage"], "negotiation")

    def test_negotiation_at_threshold_allowed_for_owner(self):
        crm = make_crm()
        opp_id = make_opp(crm, 50000)
        crm.advance(opp_id, "proposal", "r1")
        crm.advance(opp_id, "negotiation", "r1")
        self.assertEqual(crm.opps[opp_id]["stage"], "negotiation")

    def test_discounted_amount_used_for_negotiation_threshold(self):
        crm = make_crm()
        opp_id = make_opp(crm, 60000)
        crm.advance(opp_id, "proposal", "r1")
        crm.discount(opp_id, 30, "m1")
        self.assertEqual(crm.opps[opp_id]["amount"], 42000)
        crm.advance(opp_id, "negotiation", "r1")
        self.assertEqual(crm.opps[opp_id]["stage"], "negotiation")

    def test_win_frees_slot_and_assigns_waiting_lead(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        crm.add_lead("a@corp.com", "A", "referral", "r1")
        waiting = crm.add_lead("b@corp.com", "B", "referral", "r1")
        crm.qualify("L1", "r1")
        opp_id = crm.convert("L1", 1000, "r1")
        self.assertIsNone(crm.leads[waiting]["owner"])
        crm.advance(opp_id, "proposal", "r1")
        crm.advance(opp_id, "negotiation", "r1")
        crm.advance(opp_id, "won", "r1")
        self.assertEqual(crm.leads[waiting]["owner"], "r1")
        self.assertEqual(
            crm.log[-2:],
            [("advance", opp_id, "r1"), ("assign", waiting, "system")],
        )

    def test_lost_frees_slot_and_assigns_waiting_lead(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        crm.add_lead("a@corp.com", "A", "referral", "r1")
        waiting = crm.add_lead("b@corp.com", "B", "referral", "r1")
        crm.qualify("L1", "r1")
        opp_id = crm.convert("L1", 1000, "r1")
        crm.advance(opp_id, "lost", "r1")
        self.assertEqual(crm.leads[waiting]["owner"], "r1")
        self.assertEqual(crm.log[-1], ("assign", waiting, "system"))

    def test_no_assignment_without_waiting_leads(self):
        crm = make_crm()
        opp_id = make_opp(crm)
        crm.advance(opp_id, "proposal", "r1")
        crm.advance(opp_id, "negotiation", "r1")
        crm.advance(opp_id, "won", "r1")
        self.assertEqual(
            [entry for entry in crm.log if entry[0] == "assign"], []
        )


class DiscountTest(unittest.TestCase):
    def test_unknown_opportunity(self):
        crm = make_crm()
        with self.assertRaises(ValueError):
            crm.discount("O9", 5, "m1")

    def test_invalid_percentages(self):
        crm = make_crm()
        opp_id = make_opp(crm, 1000)
        for pct in (0, 31, -5, 1.5, True, "10", None):
            with self.subTest(pct=pct):
                with self.assertRaises(ValueError):
                    crm.discount(opp_id, pct, "m1")
        self.assertEqual(crm.opps[opp_id]["amount"], 1000)

    def test_percentage_checked_before_permission(self):
        crm = make_crm()
        opp_id = make_opp(crm, 1000)
        with self.assertRaises(ValueError):
            crm.discount(opp_id, 99, "r2")

    def test_non_owner_cannot_discount(self):
        crm = make_crm()
        opp_id = make_opp(crm, 1000)
        before = snapshot(crm)
        with self.assertRaises(PermissionError):
            crm.discount(opp_id, 5, "r2")
        self.assertEqual(snapshot(crm), before)

    def test_final_stage_cannot_be_discounted(self):
        crm = make_crm()
        opp_id = make_opp(crm, 1000)
        crm.advance(opp_id, "lost", "m1")
        with self.assertRaises(ValueError):
            crm.discount(opp_id, 5, "m1")

    def test_rep_limited_to_ten(self):
        crm = make_crm()
        opp_id = make_opp(crm, 1000)
        with self.assertRaises(PermissionError):
            crm.discount(opp_id, 11, "r1")
        crm.discount(opp_id, 10, "r1")
        self.assertEqual(crm.opps[opp_id]["amount"], 900)

    def test_manager_may_discount_thirty(self):
        crm = make_crm()
        opp_id = make_opp(crm, 1000)
        crm.discount(opp_id, 30, "m1")
        self.assertEqual(crm.opps[opp_id]["amount"], 700)

    def test_cumulative_discount_floor(self):
        crm = make_crm()
        opp_id = make_opp(crm, 1000)
        crm.discount(opp_id, 10, "r1")
        before = snapshot(crm)
        with self.assertRaises(ValueError):
            crm.discount(opp_id, 30, "m1")
        self.assertEqual(snapshot(crm), before)
        crm.discount(opp_id, 10, "r1")
        self.assertEqual(crm.opps[opp_id]["amount"], 810)
        crm.discount(opp_id, 10, "r1")
        self.assertEqual(crm.opps[opp_id]["amount"], 729)
        with self.assertRaises(ValueError):
            crm.discount(opp_id, 10, "r1")
        self.assertEqual(crm.opps[opp_id]["amount"], 729)

    def test_cumulative_exactly_thirty_allowed(self):
        crm = make_crm()
        opp_id = make_opp(crm, 1000)
        crm.discount(opp_id, 30, "m1")
        self.assertEqual(crm.opps[opp_id]["amount"], 700)
        with self.assertRaises(ValueError):
            crm.discount(opp_id, 1, "m1")

    def test_floor_division_and_original_amount(self):
        crm = make_crm()
        opp_id = make_opp(crm, 999)
        crm.discount(opp_id, 10, "r1")
        self.assertEqual(crm.opps[opp_id]["amount"], 899)
        self.assertEqual(crm.opps[opp_id]["original_amount"], 999)
        self.assertEqual(crm.log[-1], ("discount", opp_id, "r1"))


class TransferTest(unittest.TestCase):
    def test_unknown_opportunity(self):
        crm = make_crm()
        with self.assertRaises(ValueError):
            crm.transfer("O9", "r2", "m1")

    def test_only_manager_may_transfer(self):
        crm = make_crm()
        opp_id = make_opp(crm)
        before = snapshot(crm)
        with self.assertRaises(PermissionError):
            crm.transfer(opp_id, "r2", "r1")
        with self.assertRaises(PermissionError):
            crm.transfer(opp_id, "nobody", "r1")
        self.assertEqual(snapshot(crm), before)

    def test_new_owner_must_be_a_rep(self):
        crm = make_crm()
        opp_id = make_opp(crm)
        for new_owner in ("m1", "ghost", None, 7):
            with self.subTest(new_owner=new_owner):
                with self.assertRaises(ValueError):
                    crm.transfer(opp_id, new_owner, "m1")

    def test_final_stage_cannot_be_transferred(self):
        crm = make_crm()
        opp_id = make_opp(crm)
        crm.advance(opp_id, "lost", "m1")
        with self.assertRaises(ValueError):
            crm.transfer(opp_id, "r2", "m1")

    def test_same_owner_rejected(self):
        crm = make_crm()
        opp_id = make_opp(crm)
        with self.assertRaises(ValueError):
            crm.transfer(opp_id, "r1", "m1")

    def test_capacity_of_new_owner_enforced(self):
        crm = make_crm(r1=1, r2=1)
        make_opp(crm, 100, "a@corp.com")  # r1
        make_opp(crm, 100, "b@corp.com")  # r2 (r1 at capacity)
        with self.assertRaises(ValueError):
            crm.transfer("O1", "r2", "m1")

    def test_transfer_success_and_log(self):
        crm = make_crm()
        opp_id = make_opp(crm)
        crm.transfer(opp_id, "r2", "m1")
        self.assertEqual(crm.opps[opp_id]["owner"], "r2")
        self.assertEqual(crm.log[-1], ("transfer", opp_id, "m1"))

    def test_transfer_frees_previous_owner_slot(self):
        crm = make_crm(r1=2, r2=2)
        opp_id = make_opp(crm, 1000)  # owned by r1
        self.assertEqual(crm.opps[opp_id]["owner"], "r1")
        crm.transfer(opp_id, "r2", "m1")
        # r1 now has a free slot again, so the next lead lands on r1.
        new_lead = crm.add_lead("b@corp.com", "B", "web", "m1")
        self.assertEqual(crm.leads[new_lead]["owner"], "r1")


class ForecastTest(unittest.TestCase):
    def test_empty_forecast(self):
        crm = make_crm()
        self.assertEqual(
            crm.forecast(), {"open": 0, "weighted": 0, "won": 0}
        )
        self.assertEqual(crm.log, [])

    def test_mixed_forecast(self):
        crm = make_crm(r1=10)
        prospect = make_opp(crm, 1000, "a@corp.com")
        proposal = make_opp(crm, 2000, "b@corp.com")
        negotiation = make_opp(crm, 1000, "c@corp.com")
        won = make_opp(crm, 5000, "d@corp.com")
        lost = make_opp(crm, 999, "e@corp.com")

        crm.advance(proposal, "proposal", "m1")
        crm.advance(negotiation, "proposal", "m1")
        crm.advance(negotiation, "negotiation", "m1")
        crm.advance(won, "proposal", "m1")
        crm.advance(won, "negotiation", "m1")
        crm.advance(won, "won", "m1")
        crm.advance(lost, "lost", "m1")

        self.assertEqual(
            crm.forecast(), {"open": 3, "weighted": 1300, "won": 5000}
        )

    def test_forecast_uses_current_amount(self):
        crm = make_crm()
        opp_id = make_opp(crm, 1000)
        crm.discount(opp_id, 10, "r1")
        self.assertEqual(crm.forecast()["weighted"], 90)

    def test_forecast_has_no_side_effects(self):
        crm = make_crm()
        make_opp(crm, 1000)
        before = snapshot(crm)
        crm.forecast()
        self.assertEqual(snapshot(crm), before)


class EdgeTypeTest(unittest.TestCase):
    def test_non_string_identifiers_raise_value_error(self):
        crm = make_crm()
        make_opp(crm, 1000)
        with self.assertRaises(ValueError):
            crm.qualify(None, "r1")
        with self.assertRaises(ValueError):
            crm.convert(None, 100, "r1")
        with self.assertRaises(ValueError):
            crm.advance(None, "proposal", "r1")
        with self.assertRaises(ValueError):
            crm.discount(None, 5, "r1")
        with self.assertRaises(ValueError):
            crm.transfer(None, "r2", "m1")

    def test_unhashable_stage_and_source_raise_value_error(self):
        crm = make_crm()
        opp_id = make_opp(crm, 1000)
        with self.assertRaises(ValueError):
            crm.advance(opp_id, ["proposal"], "r1")
        with self.assertRaises(ValueError):
            crm.add_lead("x@y.com", "X", ["web"], "r1")


class LogInvariantTest(unittest.TestCase):
    def test_successful_calls_log_exact_tuples(self):
        crm = make_crm()
        lead_id = crm.add_lead("a@corp.com", "A", "referral", "m1")
        crm.qualify(lead_id, "m1")
        opp_id = crm.convert(lead_id, 500, "m1")
        crm.advance(opp_id, "proposal", "m1")
        crm.discount(opp_id, 5, "m1")
        self.assertEqual(
            crm.log,
            [
                ("add_lead", "L1", "m1"),
                ("qualify", "L1", "m1"),
                ("convert", "O1", "m1"),
                ("advance", "O1", "m1"),
                ("discount", "O1", "m1"),
            ],
        )

    def test_failures_never_mutate_state(self):
        crm = make_crm()
        lead_id = crm.add_lead("a@corp.com", "A", "referral", "r1")
        before = snapshot(crm)
        with self.assertRaises(PermissionError):
            crm.qualify(lead_id, "ghost")
        with self.assertRaises(ValueError):
            crm.qualify("L404", "r1")
        self.assertEqual(snapshot(crm), before)


if __name__ == "__main__":
    unittest.main()
