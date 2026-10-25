"""Tests for CRM.advance, discount, transfer, forecast, and the waiting queue."""

import unittest

from crm import CRM


def build():
    """r1 owns the pipeline lead (tie -> smallest id); m1 is the manager."""
    return CRM(
        [
            {"id": "r1", "role": "rep", "capacity": 5},
            {"id": "r2", "role": "rep", "capacity": 5},
            {"id": "m1", "role": "manager", "capacity": 0},
        ]
    )


def pipeline(opp_amount=1000):
    """Return (crm, opp_id) with a qualified, converted lead owned by r1."""
    crm = build()
    lead = crm.add_lead("a@x.com", "A", "referral", "r1")  # score 45
    crm.qualify(lead, "r1")
    opp = crm.convert(lead, opp_amount, "r1")
    return crm, opp


def close(crm, opp, actor="r1"):
    """Advance prospect -> proposal -> negotiation -> won."""
    crm.advance(opp, "proposal", actor)
    if crm.opps[opp]["amount"] > 50000:
        actor = "m1"
    crm.advance(opp, "negotiation", actor)
    crm.advance(opp, "won", actor)


class AdvanceTests(unittest.TestCase):
    def setUp(self):
        self.crm, self.opp = pipeline()

    def test_unknown_opp(self):
        with self.assertRaises(ValueError):
            self.crm.advance("O99", "proposal", "r1")

    def test_invalid_stage_name(self):
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "closed", "r1")

    def test_non_owner_rep(self):
        with self.assertRaises(PermissionError):
            self.crm.advance(self.opp, "proposal", "r2")

    def test_skip_stage_rejected(self):
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "negotiation", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "prospect", "r1")

    def test_valid_path(self):
        self.crm.advance(self.opp, "proposal", "r1")
        self.crm.advance(self.opp, "negotiation", "r1")
        self.crm.advance(self.opp, "won", "r1")
        self.assertEqual(self.crm.opps[self.opp]["stage"], "won")

    def test_lost_from_any_nonfinal_stage(self):
        self.crm.advance(self.opp, "lost", "r1")
        self.assertEqual(self.crm.opps[self.opp]["stage"], "lost")
        crm, opp = pipeline()
        crm.advance(opp, "proposal", "r1")
        crm.advance(opp, "lost", "r1")
        self.assertEqual(crm.opps[opp]["stage"], "lost")

    def test_final_stage_is_stuck(self):
        close(self.crm, self.opp)
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "proposal", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "lost", "r1")

    def test_big_negotiation_needs_manager(self):
        crm, opp = pipeline(opp_amount=60000)
        crm.advance(opp, "proposal", "r1")
        with self.assertRaises(PermissionError):
            crm.advance(opp, "negotiation", "r1")
        crm.advance(opp, "negotiation", "m1")
        self.assertEqual(crm.opps[opp]["stage"], "negotiation")

    def test_small_negotiation_ok_for_rep(self):
        crm, opp = pipeline(opp_amount=50000)
        crm.advance(opp, "proposal", "r1")
        crm.advance(opp, "negotiation", "r1")  # 50000 is not > 50000
        self.assertEqual(crm.opps[opp]["stage"], "negotiation")

    def test_won_frees_slot_and_assigns_queue(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1}])
        lead = crm.add_lead("a@x.com", "A", "referral", "r1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 100, "r1")  # r1 load: 1 (open opp)
        queued = crm.add_lead("b@x.com", "B", "web", "r1")
        self.assertIsNone(crm.leads[queued]["owner"])
        close(crm, opp)
        self.assertEqual(crm.leads[queued]["owner"], "r1")
        self.assertEqual(
            crm.log,
            [
                ("add_lead", lead, "r1"),
                ("qualify", lead, "r1"),
                ("convert", opp, "r1"),
                ("add_lead", queued, "r1"),
                ("advance", opp, "r1"),
                ("advance", opp, "r1"),
                ("advance", opp, "r1"),
                ("assign", queued, "system"),
            ],
        )

    def test_assign_fills_multiple_slots(self):
        crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 3},
                {"id": "r2", "role": "rep", "capacity": 0},
            ]
        )
        lead = crm.add_lead("a@x.com", "A", "referral", "r1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 100, "r1")  # r1 load 1 of 3
        q1 = crm.add_lead("b@x.com", "B", "web", "r1")  # r1 load 2 < 3
        q2 = crm.add_lead("c@x.com", "C", "web", "r1")  # r1 load 3 = cap
        q3 = crm.add_lead("d@x.com", "D", "web", "r1")  # queued
        self.assertEqual(crm.leads[q1]["owner"], "r1")
        self.assertEqual(crm.leads[q2]["owner"], "r1")
        self.assertIsNone(crm.leads[q3]["owner"])
        crm.advance(opp, "lost", "r1")  # frees one slot -> q3 assigned
        self.assertEqual(crm.leads[q3]["owner"], "r1")
        self.assertEqual(crm._waiting, [])


class DiscountTests(unittest.TestCase):
    def setUp(self):
        self.crm, self.opp = pipeline(opp_amount=1000)

    def test_unknown_opp(self):
        with self.assertRaises(ValueError):
            self.crm.discount("O99", 10, "r1")

    def test_pct_validation(self):
        for bad in [0, 31, -10, "10", 5.0, True, False, None]:
            with self.assertRaises(ValueError):
                self.crm.discount(self.opp, bad, "r1")

    def test_non_owner_rep(self):
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp, 10, "r2")

    def test_final_stage(self):
        close(self.crm, self.opp)
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp, 10, "r1")

    def test_rep_capped_at_10(self):
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp, 11, "r1")
        self.crm.discount(self.opp, 10, "r1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 900)

    def test_manager_can_discount_30(self):
        self.crm.discount(self.opp, 30, "m1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 700)

    def test_cumulative_30_percent_cap(self):
        self.crm.discount(self.opp, 10, "r1")  # 900
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp, 25, "m1")  # 675 < 700
        self.crm.discount(self.opp, 22, "m1")  # 900*78//100 = 702 >= 700
        self.assertEqual(self.crm.opps[self.opp]["amount"], 702)

    def test_floor_semantics(self):
        crm, opp = pipeline(opp_amount=999)
        crm.discount(opp, 10, "r1")
        self.assertEqual(crm.opps[opp]["amount"], 899)  # 999*90//100

    def test_failure_changes_nothing(self):
        before = self.crm.opps[self.opp]["amount"]
        before_log = list(self.crm.log)
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp, 20, "r1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], before)
        self.assertEqual(self.crm.log, before_log)


class TransferTests(unittest.TestCase):
    def setUp(self):
        self.crm, self.opp = pipeline()

    def test_unknown_opp(self):
        with self.assertRaises(ValueError):
            self.crm.transfer("O99", "r2", "m1")

    def test_rep_cannot_transfer(self):
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.opp, "r2", "r1")

    def test_unknown_or_non_rep_new_owner(self):
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "ghost", "m1")
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "m1", "m1")  # manager is not a rep

    def test_final_stage(self):
        close(self.crm, self.opp)
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "r2", "m1")

    def test_same_owner(self):
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "r1", "m1")

    def test_new_owner_at_capacity(self):
        crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 2},
                {"id": "r2", "role": "rep", "capacity": 1},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        lead = crm.add_lead("a@x.com", "A", "referral", "r1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 100, "r1")  # r1 load 1, r2 load 0
        crm.add_lead("b@x.com", "B", "web", "r2")  # -> r2 (load 0), full now
        self.assertEqual(crm.leads["L2"]["owner"], "r2")
        with self.assertRaises(ValueError):
            crm.transfer(opp, "r2", "m1")

    def test_successful_transfer_and_followup_routing(self):
        crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 2},
                {"id": "r2", "role": "rep", "capacity": 2},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        lead = crm.add_lead("a@x.com", "A", "referral", "r1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 100, "r1")  # r1 load 1, r2 load 0
        q1 = crm.add_lead("b@x.com", "B", "web", "r1")  # -> r2 (load 0)
        q2 = crm.add_lead("c@x.com", "C", "web", "r1")  # tie 1/1 -> r1
        self.assertEqual(crm.leads[q1]["owner"], "r2")
        self.assertEqual(crm.leads[q2]["owner"], "r1")
        crm.transfer(opp, "r2", "m1")
        self.assertEqual(crm.opps[opp]["owner"], "r2")
        self.assertEqual(crm.log[-1], ("transfer", opp, "m1"))
        # r1 now has a free slot; the next lead routes to r1
        nxt = crm.add_lead("d@x.com", "D", "web", "r1")
        self.assertEqual(crm.leads[nxt]["owner"], "r1")


class ForecastTests(unittest.TestCase):
    def test_forecast(self):
        # single rep so every lead/opp is owned by r1
        crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 5},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        self.assertEqual(crm.forecast(), {"open": 0, "weighted": 0, "won": 0})
        o1 = self._mkopp(crm, 1000)  # prospect w=10 -> 100
        o2 = self._mkopp(crm, 2000)
        crm.advance(o2, "proposal", "r1")  # w=30 -> 600
        o3 = self._mkopp(crm, 3000)
        crm.advance(o3, "proposal", "r1")
        crm.advance(o3, "negotiation", "m1")  # w=60 -> 1800
        o4 = self._mkopp(crm, 5000)
        close(crm, o4)
        self.assertEqual(
            crm.forecast(),
            {"open": 3, "weighted": 100 + 600 + 1800, "won": 5000},
        )

    @staticmethod
    def _mkopp(crm, amount):
        lead = crm.add_lead(
            "u{}@x.com".format(amount), "N", "referral", "r1"
        )
        crm.qualify(lead, "r1")
        return crm.convert(lead, amount, "r1")

    def test_lost_not_counted_anywhere(self):
        crm, opp = pipeline(opp_amount=1000)
        crm.advance(opp, "lost", "r1")
        self.assertEqual(crm.forecast(), {"open": 0, "weighted": 0, "won": 0})

    def test_no_log_entry_and_no_actor(self):
        crm, opp = pipeline()
        before = list(crm.log)
        crm.forecast()
        self.assertEqual(crm.log, before)


class QueueIntegrationTests(unittest.TestCase):
    def test_fifo_order_respected(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1}])
        lead = crm.add_lead("a@x.com", "A", "referral", "r1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 100, "r1")
        q1 = crm.add_lead("b@x.com", "B", "web", "r1")
        q2 = crm.add_lead("c@x.com", "C", "web", "r1")
        self.assertEqual(crm._waiting, [q1, q2])
        close(crm, opp)  # one slot freed -> q1 assigned
        self.assertEqual(crm.leads[q1]["owner"], "r1")
        self.assertIsNone(crm.leads[q2]["owner"])
        self.assertEqual(crm._waiting, [q2])

    def test_assigned_lead_keeps_status_new(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 2}])
        lead = crm.add_lead("a@x.com", "A", "referral", "r1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 100, "r1")  # load 1
        q1 = crm.add_lead("b@x.com", "B", "web", "r1")  # load 2, full
        q2 = crm.add_lead("c@x.com", "C", "web", "r1")  # queued
        close(crm, opp)  # frees 1 -> q2 assigned (status new)
        self.assertEqual(crm.leads[q2]["status"], "new")
        self.assertEqual(crm.leads[q2]["owner"], "r1")


if __name__ == "__main__":
    unittest.main()
