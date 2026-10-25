"""Unit tests for crm.advance, discount, transfer, forecast and queue flows."""

import unittest

from crm import CRM


def make_crm(reps=None):
    if reps is None:
        reps = [
            {"id": "r1", "role": "rep", "capacity": 3},
            {"id": "r2", "role": "rep", "capacity": 3},
            {"id": "m1", "role": "manager", "capacity": 0},
        ]
    return CRM(reps)


def ready_opp(crm, lead_owner="r1", amount=1000, actor="m1"):
    """Add + qualify + convert a lead; return the opportunity id."""
    lead_id = crm.add_lead("x%d@corp.io" % (len(crm.leads) + 1), "X", "referral", lead_owner)
    crm.qualify(lead_id, actor)
    return crm.convert(lead_id, amount, actor)


class AdvanceTests(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        self.opp = ready_opp(self.crm)  # O1 owned by r1, stage prospect

    def test_happy_path_full_pipeline(self):
        for stage in ("proposal", "negotiation", "won"):
            self.crm.advance(self.opp, stage, "r1")
        self.assertEqual(self.crm.opps[self.opp]["stage"], "won")
        self.assertEqual(self.crm.log[-1], ("advance", self.opp, "r1"))

    def test_unknown_opp(self):
        with self.assertRaises(ValueError):
            self.crm.advance("O9", "proposal", "r1")

    def test_invalid_stage(self):
        for bad in ("draft", "won ", "", None, "lost "):
            with self.assertRaises(ValueError):
                self.crm.advance(self.opp, bad, "r1")

    def test_unknown_actor_checked_first(self):
        with self.assertRaises(PermissionError):
            self.crm.advance("O9", "proposal", "ghost")

    def test_non_owner_rep_cannot_advance(self):
        with self.assertRaises(PermissionError):
            self.crm.advance(self.opp, "proposal", "r2")
        self.assertEqual(self.crm.opps[self.opp]["stage"], "prospect")

    def test_manager_can_advance(self):
        self.crm.advance(self.opp, "proposal", "m1")
        self.assertEqual(self.crm.opps[self.opp]["stage"], "proposal")

    def test_final_stage_cannot_advance(self):
        self.crm.advance(self.opp, "proposal", "r1")
        self.crm.advance(self.opp, "negotiation", "r1")
        self.crm.advance(self.opp, "won", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "proposal", "r1")

    def test_stage_must_be_next_or_lost(self):
        for bad in ("negotiation", "won", "prospect"):
            with self.assertRaises(ValueError):
                self.crm.advance(self.opp, bad, "r1")
        self.crm.advance(self.opp, "lost", "r1")
        self.assertEqual(self.crm.opps[self.opp]["stage"], "lost")

    def test_lost_allowed_from_any_non_final_stage(self):
        self.crm.advance(self.opp, "proposal", "r1")
        self.crm.advance(self.opp, "negotiation", "r1")
        opp2 = ready_opp(self.crm)
        self.crm.advance(self.opp, "lost", "m1")
        self.crm.advance(opp2, "lost", "m1")

    def test_big_negotiation_requires_manager(self):
        crm = make_crm()
        opp = ready_opp(crm, amount=60000)
        crm.advance(opp, "proposal", "r1")
        with self.assertRaises(PermissionError):
            crm.advance(opp, "negotiation", "r1")
        crm.advance(opp, "negotiation", "m1")
        self.assertEqual(crm.opps[opp]["stage"], "negotiation")

    def test_big_negotiation_boundary_and_discounted_amount(self):
        crm = make_crm()
        # exactly 50000 -> rep may advance
        opp = ready_opp(crm, amount=50000)
        crm.advance(opp, "proposal", "r1")
        crm.advance(opp, "negotiation", "r1")
        # 51000 discounted by 5% -> 48450 -> rep may advance
        crm2 = make_crm()
        opp2 = ready_opp(crm2, amount=51000)
        crm2.discount(opp2, 5, "m1")
        crm2.advance(opp2, "proposal", "r1")
        crm2.advance(opp2, "negotiation", "r1")

    def test_won_frees_slot_and_assigns_waiting_leads(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1},
                   {"id": "m1", "role": "manager", "capacity": 0}])
        opp = ready_opp(crm)  # r1 at capacity (1 opp)
        crm.add_lead("a@corp.io", "A", "referral", "m1")  # queued, owner None
        crm.add_lead("b@b.com", "B", "web", "m1")  # queued
        self.assertEqual(crm.leads["L2"]["owner"], None)
        self.assertEqual(crm.leads["L3"]["owner"], None)
        crm.advance(opp, "proposal", "r1")
        crm.advance(opp, "negotiation", "r1")
        crm.advance(opp, "won", "r1")
        # one slot freed -> exactly one waiting lead assigned by "system"
        self.assertEqual(crm.leads["L2"]["owner"], "r1")
        self.assertEqual(crm.leads["L3"]["owner"], None)
        self.assertEqual(crm.log[-1], ("assign", "L2", "system"))
        # the freed lead can now be qualified/converted by its owner
        crm.qualify("L2", "r1")
        self.assertEqual(crm.leads["L2"]["status"], "qualified")

    def test_lost_frees_slot_too(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1},
                   {"id": "m1", "role": "manager", "capacity": 0}])
        opp = ready_opp(crm)
        crm.add_lead("a@b.com", "A", "web", "m1")
        crm.advance(opp, "lost", "r1")
        self.assertEqual(crm.leads["L2"]["owner"], "r1")
        self.assertEqual(crm.log[-1], ("assign", "L2", "system"))


class DiscountTests(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        self.opp = ready_opp(self.crm, amount=1000)  # O1 owner r1

    def test_happy_path(self):
        self.crm.discount(self.opp, 10, "r1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 900)

    def test_unknown_opp(self):
        with self.assertRaises(ValueError):
            self.crm.discount("O9", 10, "r1")

    def test_pct_bounds_and_type(self):
        for bad in (0, 31, -5, True, False, 10.0, "10", None):
            with self.assertRaises(ValueError, msg=repr(bad)):
                self.crm.discount(self.opp, bad, "r1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 1000)

    def test_non_owner_cannot_discount(self):
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp, 5, "r2")

    def test_final_stage_cannot_discount(self):
        self.crm.advance(self.opp, "proposal", "r1")
        self.crm.advance(self.opp, "negotiation", "r1")
        self.crm.advance(self.opp, "won", "r1")
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp, 5, "r1")

    def test_non_manager_capped_at_10(self):
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp, 11, "r1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 1000)
        self.crm.discount(self.opp, 10, "r1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 900)

    def test_manager_may_discount_up_to_30(self):
        self.crm.discount(self.opp, 30, "m1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 700)

    def test_cumulative_discount_cap_30_percent(self):
        self.crm.discount(self.opp, 20, "m1")  # 800, cumulative 20%
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp, 15, "m1")  # would be 680 -> 68% < 70%
        self.crm.discount(self.opp, 12, "m1")  # 800*88//100 = 704 -> 70.4% ok
        self.assertEqual(self.crm.opps[self.opp]["amount"], 704)

    def test_floor_discount_hits_cap_exactly(self):
        # 999: 15% -> 999*85//100 = 849; 849*100 = 84900 >= 69930 ok
        crm = make_crm()
        opp = ready_opp(crm, amount=999)
        crm.discount(opp, 15, "m1")
        self.assertEqual(crm.opps[opp]["amount"], 849)
        # now 849 * 70 // 100 -> any further 15%: 849*85//100 = 721; 72100 < 69930? no: ok
        crm.discount(opp, 17, "m1")  # 849*83//100 = 704; 70400 >= 69930 ok
        self.assertEqual(crm.opps[opp]["amount"], 704)

    def test_failed_discount_logs_nothing(self):
        before_log = list(self.crm.log)
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp, 20, "r1")
        self.assertEqual(self.crm.log, before_log)


class TransferTests(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        self.opp = ready_opp(self.crm)  # O1 owner r1

    def test_manager_transfer_happy_path(self):
        self.crm.transfer(self.opp, "r2", "m1")
        self.assertEqual(self.crm.opps[self.opp]["owner"], "r2")
        self.assertEqual(self.crm.log[-1], ("transfer", self.opp, "m1"))

    def test_unknown_opp(self):
        with self.assertRaises(ValueError):
            self.crm.transfer("O9", "r2", "m1")

    def test_only_manager_may_transfer(self):
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.opp, "r2", "r1")  # even the owner

    def test_new_owner_must_be_known_rep(self):
        for bad in ("m1", "ghost", None, 5):
            with self.assertRaises(ValueError, msg=repr(bad)):
                self.crm.transfer(self.opp, bad, "m1")

    def test_final_stage_cannot_transfer(self):
        self.crm.advance(self.opp, "lost", "m1")
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "r2", "m1")

    def test_same_owner_transfer_rejected(self):
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "r1", "m1")

    def test_new_owner_at_capacity_rejected(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1},
                   {"id": "r2", "role": "rep", "capacity": 1},
                   {"id": "m1", "role": "manager", "capacity": 0}])
        opp = ready_opp(crm)                       # r1 owns O1
        crm.add_lead("a@b.com", "A", "web", "m1")  # r2 gets L1 -> r2 at capacity
        with self.assertRaises(ValueError):
            crm.transfer(opp, "r2", "m1")
        self.assertEqual(crm.opps[opp]["owner"], "r1")

    def test_transfer_frees_previous_owner_slot(self):
        # Queue is empty here (see analysis: a queued lead implies all reps are
        # at capacity, which blocks transfer), so freeing the previous owner's
        # slot must be a no-op that logs nothing beyond the transfer.
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1},
                   {"id": "r2", "role": "rep", "capacity": 3},
                   {"id": "m1", "role": "manager", "capacity": 0}])
        opp = ready_opp(crm)                          # L1 -> r1, O1 -> r1 (load 1)
        crm.add_lead("a@corp.io", "A", "referral", "m1")  # L2 -> r2 (load 1)
        crm.transfer(opp, "r2", "m1")                 # r2 load 2, r1 load 0
        self.assertEqual(crm.opps[opp]["owner"], "r2")
        self.assertEqual(crm.log[-1], ("transfer", opp, "m1"))
        self.assertFalse(any(e[0] == "assign" for e in crm.log))

    def test_transfer_failure_leaves_everything_unchanged(self):
        before_owner = self.crm.opps[self.opp]["owner"]
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.opp, "r2", "r1")
        self.assertEqual(self.crm.opps[self.opp]["owner"], before_owner)


class ForecastTests(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(make_crm().forecast(), {"open": 0, "weighted": 0, "won": 0})

    def test_weights_and_won(self):
        crm = make_crm()
        o1 = ready_opp(crm, amount=1000)   # prospect
        crm.advance(o1, "proposal", "m1")  # 1000 -> proposal
        o2 = ready_opp(crm, amount=100)    # prospect
        crm.advance(o1, "negotiation", "m1")
        o3 = ready_opp(crm, amount=100)
        crm.advance(o1, "won", "m1")
        o4 = ready_opp(crm, amount=100)
        crm.advance(o4, "lost", "m1")
        # open: o2 (prospect), o3 (prospect); won: o1 1000; lost ignored
        result = crm.forecast()
        self.assertEqual(result["open"], 2)
        self.assertEqual(result["weighted"], 100 * 10 // 100 + 100 * 10 // 100)
        self.assertEqual(result["won"], 1000)

    def test_weighted_uses_floor_division_per_opportunity(self):
        crm = make_crm()
        a = ready_opp(crm, amount=999)   # 999*30//100 = 299 (proposal)
        b = ready_opp(crm, amount=999)   # prospect
        crm.advance(a, "proposal", "m1")
        crm.discount(b, 3, "m1")         # 999*97//100 = 969
        result = crm.forecast()
        self.assertEqual(result["weighted"], 299 + 969 * 10 // 100)
        self.assertEqual(result["open"], 2)
        self.assertEqual(result["won"], 0)

    def test_forecast_takes_no_actor_and_logs_nothing(self):
        crm = make_crm()
        log_before = list(crm.log)
        crm.forecast()
        self.assertEqual(crm.log, log_before)


class QueueFifoAndIsolationTests(unittest.TestCase):
    def test_waiting_queue_is_fifo(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 3},
                   {"id": "m1", "role": "manager", "capacity": 0}])
        ready_opp(crm)                              # L1 -> r1 (load 1)
        crm.add_lead("a@b.com", "A", "web", "m1")   # L2 -> r1 (load 2)
        crm.add_lead("b@b.com", "B", "web", "m1")   # L3 -> r1 (load 3)
        self.assertEqual(crm.leads["L2"]["owner"], "r1")
        self.assertEqual(crm.leads["L3"]["owner"], "r1")

    def test_fifo_order_across_full_capacity(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 2},
                   {"id": "m1", "role": "manager", "capacity": 0}])
        opp = ready_opp(crm)                        # L1 -> r1, O1 -> r1 (load 1)
        crm.add_lead("a@b.com", "A", "web", "m1")   # L2 -> r1 (load 2)
        crm.add_lead("b@corp.io", "B", "referral", "m1")  # L3 queued
        crm.add_lead("c@b.com", "C", "web", "m1")   # L4 queued
        self.assertEqual(crm.leads["L2"]["owner"], "r1")
        self.assertEqual([crm.leads["L3"]["owner"], crm.leads["L4"]["owner"]],
                         [None, None])
        crm.advance(opp, "proposal", "m1")
        crm.advance(opp, "negotiation", "m1")
        crm.advance(opp, "won", "m1")               # r1 load 1 -> one slot free
        self.assertEqual(crm.leads["L3"]["owner"], "r1")  # L3 oldest first
        self.assertEqual(crm.leads["L4"]["owner"], None)
        # converting the newly assigned lead does NOT re-trigger assignment
        crm.qualify("L3", "r1")
        crm.convert("L3", 100, "r1")                # r1 load 1 (O2 only)
        self.assertEqual(crm.leads["L4"]["owner"], None)

    def test_assignment_fills_multiple_slots(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1},
                   {"id": "m1", "role": "manager", "capacity": 0}])
        crm.add_lead("a@corp.io", "A", "referral", "m1")  # L1 -> r1 (load 1)
        crm.add_lead("b@corp.io", "B", "referral", "m1")  # L2 queued
        crm.qualify("L1", "m1")
        opp = crm.convert("L1", 100, "m1")          # O1 -> r1 (load 1)
        crm.add_lead("c@b.com", "C", "web", "m1")   # L3 queued
        crm.advance(opp, "proposal", "m1")
        crm.advance(opp, "negotiation", "m1")
        crm.advance(opp, "won", "m1")               # slot free -> L2 assigned
        self.assertEqual(crm.leads["L2"]["owner"], "r1")
        self.assertEqual(crm.leads["L3"]["owner"], None)
        crm.qualify("L2", "r1")
        crm.convert("L2", 100, "r1")                # no auto-assign on convert
        self.assertEqual(crm.leads["L3"]["owner"], None)

    def test_failed_call_never_mutates_state(self):
        crm = make_crm()
        ready_opp(crm)
        snapshot_log = list(crm.log)
        snapshot_leads = {k: dict(v) for k, v in crm.leads.items()}
        snapshot_opps = {k: dict(v) for k, v in crm.opps.items()}
        with self.assertRaises(ValueError):
            crm.advance("O1", "negotiation", "r1")  # skipping proposal
        with self.assertRaises(ValueError):
            crm.discount("O1", 99, "m1")
        with self.assertRaises(ValueError):
            crm.transfer("O1", "r1", "m1")
        self.assertEqual(crm.log, snapshot_log)
        self.assertEqual(crm.leads, snapshot_leads)
        self.assertEqual(crm.opps, snapshot_opps)


if __name__ == "__main__":
    unittest.main()
