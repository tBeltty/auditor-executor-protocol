"""Conversion, stage flow, discounts, transfers, forecasting and atomicity."""

import copy
import unittest

from crm import CRM, DuplicateLeadError

REPS = [
    {"id": "r1", "role": "rep", "capacity": 3},
    {"id": "r2", "role": "rep", "capacity": 3},
    {"id": "r3", "role": "rep", "capacity": 3},
    {"id": "m1", "role": "manager", "capacity": 0},
]

SOLO = [
    {"id": "r1", "role": "rep", "capacity": 10},
    {"id": "m1", "role": "manager", "capacity": 0},
]


def make(reps=None):
    source = REPS if reps is None else reps
    return CRM([dict(rep) for rep in source])


def solo():
    """One rep with room for every fixture lead, so ownership is predictable."""
    return make(SOLO)


def state(crm):
    return copy.deepcopy((crm.leads, crm.opps, crm.log))


def lead(crm, email="lead@example.com", source="referral", actor="r1"):
    return crm.add_lead(email, "Ada", source, actor)


def qualified(crm, email="lead@example.com", source="referral"):
    lead_id = lead(crm, email, source)
    crm.qualify(lead_id, "m1")
    return lead_id


def make_opp(crm, amount=1000, email="deal@example.com", source="referral"):
    lead_id = qualified(crm, email, source)
    return crm.convert(lead_id, amount, "m1")


class ConvertTest(unittest.TestCase):
    def test_convert_requires_existing_lead(self):
        crm = make()
        with self.assertRaises(ValueError):
            crm.convert("L404", 1000, "r1")

    def test_convert_amount_must_be_positive_int(self):
        crm = make()
        lead_id = qualified(crm)
        before = state(crm)
        for bad in (0, -5, 1.5, "100", None, True, False):
            with self.assertRaises(ValueError):
                crm.convert(lead_id, bad, "r1")
        self.assertEqual(crm.opps, {})
        self.assertEqual(crm.leads[lead_id]["status"], "qualified")
        self.assertEqual(state(crm), before)

    def test_convert_requires_permission(self):
        crm = make()
        lead_id = qualified(crm)
        before = state(crm)
        with self.assertRaises(PermissionError):
            crm.convert(lead_id, 1000, "r2")
        self.assertEqual(state(crm), before)

    def test_convert_requires_qualified_status(self):
        crm = make()
        lead_id = lead(crm)
        before = state(crm)
        with self.assertRaises(ValueError):
            crm.convert(lead_id, 1000, "r1")
        self.assertEqual(crm.leads[lead_id]["status"], "new")
        self.assertEqual(state(crm), before)

    def test_convert_requires_owner(self):
        crm = make([
            {"id": "r1", "role": "rep", "capacity": 0},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        lead_id = lead(crm)
        crm.qualify(lead_id, "m1")
        before = state(crm)
        with self.assertRaises(ValueError):
            crm.convert(lead_id, 1000, "m1")
        self.assertEqual(state(crm), before)

    def test_convert_builds_opportunity(self):
        crm = make()
        lead_id = qualified(crm)
        opp_id = crm.convert(lead_id, 2500, "r1")
        self.assertEqual(opp_id, "O1")
        self.assertEqual(crm.opps[opp_id], {
            "id": "O1",
            "lead_id": lead_id,
            "owner": "r1",
            "amount": 2500,
            "original_amount": 2500,
            "stage": "prospect",
        })
        self.assertEqual(crm.leads[lead_id]["status"], "converted")
        self.assertEqual(crm.log, [("add_lead", lead_id, "r1"),
                                   ("qualify", lead_id, "m1"),
                                   ("convert", "O1", "r1")])

    def test_convert_ids_increment(self):
        crm = solo()
        first = crm.convert(qualified(crm, "a@example.com"), 100, "r1")
        second = crm.convert(qualified(crm, "b@example.com"), 200, "r1")
        self.assertEqual((first, second), ("O1", "O2"))


class AdvanceTest(unittest.TestCase):
    def test_advance_requires_existing_opportunity(self):
        crm = make()
        with self.assertRaises(ValueError):
            crm.advance("O404", "proposal", "r1")

    def test_advance_stage_name_validated_before_permission(self):
        crm = make()
        opp = make_opp(crm)
        before = state(crm)
        with self.assertRaises(ValueError):
            crm.advance(opp, "bogus", "r2")
        with self.assertRaises(ValueError):
            crm.advance(opp, "bogus", "r1")
        self.assertEqual(state(crm), before)

    def test_advance_requires_permission(self):
        crm = make()
        opp = make_opp(crm)
        before = state(crm)
        with self.assertRaises(PermissionError):
            crm.advance(opp, "proposal", "r2")
        self.assertEqual(crm.opps[opp]["stage"], "prospect")
        self.assertEqual(state(crm), before)

    def test_advance_rejects_final_opportunity(self):
        crm = make()
        opp = make_opp(crm)
        crm.advance(opp, "proposal", "r1")
        crm.advance(opp, "negotiation", "r1")
        crm.advance(opp, "won", "r1")
        before = state(crm)
        for stage in ("lost", "won", "proposal"):
            with self.assertRaises(ValueError):
                crm.advance(opp, stage, "r1")
        self.assertEqual(state(crm), before)
        self.assertEqual(crm.opps[opp]["stage"], "won")

    def test_advance_requires_immediate_next_stage(self):
        crm = solo()
        first = make_opp(crm, 1000, "a@example.com")
        second = make_opp(crm, 1000, "b@example.com")
        crm.advance(second, "proposal", "r1")
        before = state(crm)
        with self.assertRaises(ValueError):
            crm.advance(first, "negotiation", "r1")
        with self.assertRaises(ValueError):
            crm.advance(second, "won", "r1")
        with self.assertRaises(ValueError):
            crm.advance(first, "prospect", "r1")
        self.assertEqual(state(crm), before)

    def test_advance_to_lost_from_any_open_stage(self):
        crm = solo()
        first = make_opp(crm, 1000, "a@example.com")
        second = make_opp(crm, 1000, "b@example.com")
        crm.advance(second, "proposal", "r1")
        crm.advance(first, "lost", "r1")
        crm.advance(second, "lost", "r1")
        self.assertEqual(crm.opps[first]["stage"], "lost")
        self.assertEqual(crm.opps[second]["stage"], "lost")
        self.assertEqual(crm.log[-2:], [("advance", first, "r1"), ("advance", second, "r1")])

    def test_advance_full_path_logs(self):
        crm = make()
        opp = make_opp(crm)
        for stage in ("proposal", "negotiation", "won"):
            crm.advance(opp, stage, "r1")
        self.assertEqual(crm.opps[opp]["stage"], "won")
        self.assertEqual([entry for entry in crm.log if entry[0] == "advance"],
                         [("advance", opp, "r1")] * 3)

    def test_big_deal_requires_manager(self):
        crm = make()
        opp = make_opp(crm, 50001)
        crm.advance(opp, "proposal", "r1")
        before = state(crm)
        with self.assertRaises(PermissionError):
            crm.advance(opp, "negotiation", "r1")
        self.assertEqual(crm.opps[opp]["stage"], "proposal")
        self.assertEqual(state(crm), before)
        crm.advance(opp, "negotiation", "m1")
        self.assertEqual(crm.opps[opp]["stage"], "negotiation")

    def test_big_deal_threshold_is_inclusive(self):
        crm = make()
        opp = make_opp(crm, 50000)
        crm.advance(opp, "proposal", "r1")
        crm.advance(opp, "negotiation", "r1")
        self.assertEqual(crm.opps[opp]["stage"], "negotiation")

    def test_big_deal_denied_only_at_negotiation(self):
        crm = make()
        opp = make_opp(crm, 60000)
        crm.advance(opp, "proposal", "r1")
        self.assertEqual(crm.opps[opp]["stage"], "proposal")
        crm.advance(opp, "lost", "r1")
        self.assertEqual(crm.opps[opp]["stage"], "lost")

    def test_big_deal_check_follows_stage_order(self):
        crm = make()
        opp = make_opp(crm, 60000)
        before = state(crm)
        with self.assertRaises(ValueError):
            crm.advance(opp, "negotiation", "r1")
        self.assertEqual(state(crm), before)

    def test_big_deal_uses_current_amount(self):
        crm = make()
        opp = make_opp(crm, 60000)
        crm.advance(opp, "proposal", "r1")
        crm.discount(opp, 30, "m1")
        self.assertEqual(crm.opps[opp]["amount"], 42000)
        crm.advance(opp, "negotiation", "r1")
        self.assertEqual(crm.opps[opp]["stage"], "negotiation")


class DiscountTest(unittest.TestCase):
    def test_discount_pct_validation(self):
        crm = make()
        opp = make_opp(crm, 1000)
        before = state(crm)
        for bad in (0, 31, -10, 11.0, "10", None, True):
            with self.assertRaises(ValueError):
                crm.discount(opp, bad, "r1")
        self.assertEqual(crm.opps[opp]["amount"], 1000)
        self.assertEqual(state(crm), before)

    def test_discount_requires_permission(self):
        crm = make()
        opp = make_opp(crm)
        before = state(crm)
        with self.assertRaises(PermissionError):
            crm.discount(opp, 5, "r2")
        self.assertEqual(state(crm), before)

    def test_discount_rejects_final_stage(self):
        crm = make()
        opp = make_opp(crm)
        crm.advance(opp, "proposal", "r1")
        crm.advance(opp, "negotiation", "r1")
        crm.advance(opp, "won", "r1")
        before = state(crm)
        with self.assertRaises(ValueError):
            crm.discount(opp, 5, "m1")
        self.assertEqual(crm.opps[opp]["amount"], 1000)
        self.assertEqual(state(crm), before)

    def test_discount_rep_limit_is_ten(self):
        crm = make()
        opp = make_opp(crm, 1000)
        before = state(crm)
        with self.assertRaises(PermissionError):
            crm.discount(opp, 11, "r1")
        self.assertEqual(state(crm), before)
        crm.discount(opp, 10, "r1")
        self.assertEqual(crm.opps[opp]["amount"], 900)

    def test_discount_manager_may_use_full_range(self):
        crm = make()
        opp = make_opp(crm, 1000)
        crm.discount(opp, 30, "m1")
        self.assertEqual(crm.opps[opp]["amount"], 700)

    def test_discount_cumulative_floor(self):
        crm = make()
        opp = make_opp(crm, 1000)
        for _ in range(3):
            crm.discount(opp, 10, "r1")
        self.assertEqual(crm.opps[opp]["amount"], 729)
        before = state(crm)
        with self.assertRaises(ValueError):
            crm.discount(opp, 10, "r1")
        self.assertEqual(crm.opps[opp]["amount"], 729)
        self.assertEqual(state(crm), before)

    def test_discount_keeps_original_amount(self):
        crm = make()
        opp = make_opp(crm, 1000)
        crm.discount(opp, 10, "r1")
        self.assertEqual(crm.opps[opp]["original_amount"], 1000)
        self.assertEqual(crm.opps[opp]["amount"], 900)
        self.assertEqual(crm.log[-1], ("discount", opp, "r1"))

    def test_discount_floor_tracks_original_amount(self):
        crm = make()
        opp = make_opp(crm, 1000)
        crm.discount(opp, 30, "m1")
        self.assertEqual(crm.opps[opp]["amount"], 700)
        before = state(crm)
        with self.assertRaises(ValueError):
            crm.discount(opp, 1, "m1")
        self.assertEqual(state(crm), before)


class TransferTest(unittest.TestCase):
    def test_transfer_requires_existing_opportunity(self):
        crm = make()
        with self.assertRaises(ValueError):
            crm.transfer("O404", "r2", "m1")

    def test_transfer_is_manager_only(self):
        crm = make()
        opp = make_opp(crm)
        before = state(crm)
        with self.assertRaises(PermissionError):
            crm.transfer(opp, "r2", "r1")
        self.assertEqual(crm.opps[opp]["owner"], "r1")
        self.assertEqual(state(crm), before)

    def test_transfer_manager_check_precedes_target_check(self):
        crm = make()
        opp = make_opp(crm)
        with self.assertRaises(PermissionError):
            crm.transfer(opp, "nobody", "r1")

    def test_transfer_target_must_be_known_rep(self):
        crm = make([
            {"id": "r1", "role": "rep", "capacity": 3},
            {"id": "m1", "role": "manager", "capacity": 5},
        ])
        opp = make_opp(crm)
        before = state(crm)
        for bad in ("nobody", "m1", None, 7):
            with self.assertRaises(ValueError):
                crm.transfer(opp, bad, "m1")
        self.assertEqual(crm.opps[opp]["owner"], "r1")
        self.assertEqual(state(crm), before)

    def test_transfer_rejects_final_stage(self):
        crm = make()
        opp = make_opp(crm)
        crm.advance(opp, "proposal", "r1")
        crm.advance(opp, "negotiation", "r1")
        crm.advance(opp, "won", "r1")
        before = state(crm)
        with self.assertRaises(ValueError):
            crm.transfer(opp, "r2", "m1")
        self.assertEqual(crm.opps[opp]["owner"], "r1")
        self.assertEqual(state(crm), before)

    def test_transfer_rejects_same_owner(self):
        crm = make()
        opp = make_opp(crm)
        before = state(crm)
        with self.assertRaises(ValueError):
            crm.transfer(opp, "r1", "m1")
        self.assertEqual(state(crm), before)

    def test_transfer_rejects_target_at_capacity(self):
        crm = make([
            {"id": "r1", "role": "rep", "capacity": 3},
            {"id": "r2", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        lead(crm, "a@example.com")
        occupied = lead(crm, "b@example.com")
        self.assertEqual(crm.leads[occupied]["owner"], "r2")
        opp = make_opp(crm, 1000, "c@example.com")
        before = state(crm)
        with self.assertRaises(ValueError):
            crm.transfer(opp, "r2", "m1")
        self.assertEqual(crm.opps[opp]["owner"], "r1")
        self.assertEqual(state(crm), before)

    def test_transfer_moves_owner_and_logs(self):
        crm = make()
        opp = make_opp(crm)
        crm.transfer(opp, "r2", "m1")
        self.assertEqual(crm.opps[opp]["owner"], "r2")
        self.assertEqual(crm.log[-1], ("transfer", opp, "m1"))

    def test_transfer_releases_previous_owner_load(self):
        crm = make([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 3},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        opp = make_opp(crm)
        self.assertEqual(crm.opps[opp]["owner"], "r1")
        crm.transfer(opp, "r2", "m1")
        newcomer = lead(crm, "next@example.com")
        self.assertEqual(crm.leads[newcomer]["owner"], "r1")


class ForecastTest(unittest.TestCase):
    def test_forecast_empty(self):
        self.assertEqual(make().forecast(), {"open": 0, "weighted": 0, "won": 0})

    def test_forecast_mixed_pipeline(self):
        crm = solo()
        prospect = make_opp(crm, 1000, "a@example.com")
        proposal = make_opp(crm, 2000, "b@example.com")
        won = make_opp(crm, 3000, "c@example.com")
        lost = make_opp(crm, 4000, "d@example.com")
        crm.advance(proposal, "proposal", "r1")
        for stage in ("proposal", "negotiation", "won"):
            crm.advance(won, stage, "r1")
        crm.advance(lost, "lost", "r1")
        self.assertEqual(crm.forecast(), {"open": 2, "weighted": 100 + 600, "won": 3000})
        self.assertEqual(crm.log[0][0], "add_lead")
        self.assertNotIn("forecast", [entry[0] for entry in crm.log])
        self.assertEqual(crm.opps[prospect]["stage"], "prospect")

    def test_forecast_uses_current_amount(self):
        crm = make()
        opp = make_opp(crm, 1000)
        crm.discount(opp, 10, "r1")
        self.assertEqual(crm.forecast(), {"open": 1, "weighted": 90, "won": 0})


class AtomicityTest(unittest.TestCase):
    def test_atomic_log_qualify(self):
        crm = make()
        lead_id = lead(crm, "low@gmail.com", "web")
        self.assertEqual(crm.leads[lead_id]["score"], 10)
        before = state(crm)
        with self.assertRaises(ValueError):
            crm.qualify(lead_id, "r1")
        self.assertEqual(crm.leads[lead_id]["status"], "new")
        self.assertEqual(state(crm), before)

    def test_atomic_state_convert(self):
        crm = make()
        lead_id = lead(crm, "fresh@example.com")
        before = state(crm)
        with self.assertRaises(ValueError):
            crm.convert(lead_id, 1000, "r1")
        self.assertEqual(crm.leads[lead_id]["status"], "new")
        self.assertEqual(state(crm), before)

    def test_atomic_advance_bigdeal(self):
        crm = make()
        opp = make_opp(crm, 60000)
        crm.advance(opp, "proposal", "r1")
        before = state(crm)
        with self.assertRaises(PermissionError):
            crm.advance(opp, "negotiation", "r1")
        self.assertEqual(crm.opps[opp]["stage"], "proposal")
        self.assertEqual(state(crm), before)

    def test_atomic_discount_failure(self):
        crm = make()
        opp = make_opp(crm, 1000)
        before = state(crm)
        with self.assertRaises(PermissionError):
            crm.discount(opp, 25, "r1")
        with self.assertRaises(ValueError):
            crm.discount(opp, 0, "r1")
        self.assertEqual(crm.opps[opp]["amount"], 1000)
        self.assertEqual(state(crm), before)

    def test_atomic_discount_floor_failure(self):
        crm = make()
        opp = make_opp(crm, 1000)
        crm.discount(opp, 30, "m1")
        before = state(crm)
        with self.assertRaises(ValueError):
            crm.discount(opp, 1, "m1")
        self.assertEqual(crm.opps[opp]["amount"], 700)
        self.assertEqual(state(crm), before)

    def test_atomic_transfer_failure(self):
        crm = make()
        opp = make_opp(crm)
        before = state(crm)
        with self.assertRaises(PermissionError):
            crm.transfer(opp, "r2", "r1")
        with self.assertRaises(ValueError):
            crm.transfer(opp, "r1", "m1")
        self.assertEqual(crm.opps[opp]["owner"], "r1")
        self.assertEqual(state(crm), before)

    def test_atomic_add_lead_failure_leaves_queue_untouched(self):
        crm = make([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        lead(crm, "first@example.com")
        waiting = lead(crm, "second@example.com")
        self.assertIsNone(crm.leads[waiting]["owner"])
        before = state(crm)
        with self.assertRaises(DuplicateLeadError):
            crm.add_lead("second@example.com", "Copy", "web", "r1")
        self.assertEqual(state(crm), before)


if __name__ == "__main__":
    unittest.main()
