"""Tests for CRM.transfer and CRM.forecast."""

import unittest

from _helpers import manager, qualify_and_convert, rep, snapshot
from crm import CRM


class TransferTests(unittest.TestCase):
    def setUp(self):
        self.crm = CRM([rep("r1", 5), rep("r2", 5), manager("m1")])
        self.lead_id, self.opp_id = qualify_and_convert(self.crm, amount=1000)

    def test_unknown_actor_checked_first(self):
        before = snapshot(self.crm)
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.opp_id, "nobody", "ghost")
        self.assertEqual(snapshot(self.crm), before)

    def test_unknown_opportunity(self):
        with self.assertRaises(ValueError):
            self.crm.transfer("O99", "r2", "m1")

    def test_only_managers_may_transfer(self):
        before = snapshot(self.crm)
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.opp_id, "r2", "r1")
        self.assertEqual(snapshot(self.crm), before)

    def test_permission_checked_before_new_owner(self):
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.opp_id, "ghost", "r2")

    def test_new_owner_must_be_a_rep(self):
        for bad in ("ghost", "m1", None, 3):
            before = snapshot(self.crm)
            with self.assertRaises(ValueError):
                self.crm.transfer(self.opp_id, bad, "m1")
            self.assertEqual(snapshot(self.crm), before)

    def test_new_owner_checked_before_final_stage(self):
        self.crm.advance(self.opp_id, "lost", "r1")
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp_id, "ghost", "m1")

    def test_final_opportunity_cannot_be_transferred(self):
        self.crm.advance(self.opp_id, "lost", "r1")
        before = snapshot(self.crm)
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp_id, "r2", "m1")
        self.assertEqual(snapshot(self.crm), before)

    def test_same_owner_rejected(self):
        before = snapshot(self.crm)
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp_id, "r1", "m1")
        self.assertEqual(snapshot(self.crm), before)

    def test_new_owner_must_have_capacity(self):
        crm = CRM([rep("r1", 1), rep("r2", 1), manager("m1")])
        _, opp = qualify_and_convert(crm, actor="r1")
        lead_r2 = crm.add_lead("c@corp.com", "C", "referral", "r2")
        self.assertEqual(crm.leads[lead_r2]["owner"], "r2")
        before = snapshot(crm)
        with self.assertRaises(ValueError):
            crm.transfer(opp, "r2", "m1")
        self.assertEqual(snapshot(crm), before)

    def test_success_changes_owner_and_logs(self):
        self.crm.transfer(self.opp_id, "r2", "m1")
        self.assertEqual(self.crm.opps[self.opp_id]["owner"], "r2")
        self.assertEqual(self.crm.log[-1], ("transfer", self.opp_id, "m1"))

    def test_transfer_frees_previous_owner_slot(self):
        # The spec requires transfer to hand the previous owner's freed slot
        # to the waiting queue.  Public calls normally cannot leave a queued
        # lead while another rep has spare capacity, so seed that state.
        crm = CRM([rep("r1", 1), rep("r2", 2), manager("m1")])
        lead_a = crm.add_lead("a@corp.com", "A", "referral", "r1")
        crm.qualify(lead_a, "r1")
        opp = crm.convert(lead_a, 100, "r1")
        waiting = crm.add_lead("b@corp.com", "B", "referral", "r1")
        crm.leads[waiting]["owner"] = None
        crm.waiting.append(waiting)

        crm.transfer(opp, "r2", "m1")
        self.assertEqual(crm.opps[opp]["owner"], "r2")
        self.assertEqual(crm.leads[waiting]["owner"], "r1")
        self.assertEqual(crm.waiting, [])
        self.assertEqual(
            crm.log[-2:],
            [("transfer", opp, "m1"), ("assign", waiting, "system")],
        )

    def test_transfer_without_waiting_queue_logs_only_transfer(self):
        crm = CRM([rep("r1", 1), rep("r2", 2), manager("m1")])
        _, opp = qualify_and_convert(crm, actor="r1")
        crm.transfer(opp, "r2", "m1")
        self.assertEqual(crm.log[-1], ("transfer", opp, "m1"))
        self.assertEqual(crm.waiting, [])


class ForecastTests(unittest.TestCase):
    def setUp(self):
        self.crm = CRM([rep("r1", 20), manager("m1")])

    def test_empty(self):
        self.assertEqual(self.crm.forecast(), {"open": 0, "weighted": 0, "won": 0})

    def test_weights_by_stage_and_flooring(self):
        _, prospect = qualify_and_convert(self.crm, email="a@corp.com", amount=1000)
        _, proposal = qualify_and_convert(self.crm, email="b@corp.com", amount=333)
        _, negotiation = qualify_and_convert(self.crm, email="c@corp.com", amount=101)
        self.crm.advance(proposal, "proposal", "r1")
        self.crm.advance(negotiation, "proposal", "r1")
        self.crm.advance(negotiation, "negotiation", "r1")

        # 1000*10//100 + 333*30//100 + 101*60//100 == 100 + 99 + 60
        self.assertEqual(
            self.crm.forecast(), {"open": 3, "weighted": 259, "won": 0}
        )

    def test_won_and_lost_are_excluded_from_open(self):
        _, won = qualify_and_convert(self.crm, email="a@corp.com", amount=1000)
        _, lost = qualify_and_convert(self.crm, email="b@corp.com", amount=500)
        self.crm.advance(won, "proposal", "r1")
        self.crm.advance(won, "negotiation", "r1")
        self.crm.advance(won, "won", "r1")
        self.crm.advance(lost, "lost", "r1")
        self.assertEqual(self.crm.forecast(), {"open": 0, "weighted": 0, "won": 1000})

    def test_forecast_uses_current_discounted_amount(self):
        _, opp = qualify_and_convert(self.crm, amount=1000)
        self.crm.discount(opp, 10, "r1")  # 900 prospect
        self.crm.advance(opp, "proposal", "r1")  # 900 * 30 // 100 == 270
        self.assertEqual(self.crm.forecast(), {"open": 1, "weighted": 270, "won": 0})

    def test_forecast_does_not_log_or_mutate(self):
        qualify_and_convert(self.crm)
        before = snapshot(self.crm)
        self.crm.forecast()
        self.assertEqual(snapshot(self.crm), before)


if __name__ == "__main__":
    unittest.main()
