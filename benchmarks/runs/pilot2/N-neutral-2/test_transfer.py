"""Guard group: transfer rules (manager only, valid rep target, non-final,
different owner, target capacity) and slot release after transfer."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import fixtures  # noqa: E402


def deal(amount=1000):
    system = fixtures.make(
        ("r1", "rep", 5), ("r2", "rep", 5), ("r3", "rep", 0), ("m1", "manager", 5)
    )
    lead = system.add_lead("t@corp.com", "T", "referral", "r1")
    system.qualify(lead, "r1")
    opp = system.convert(lead, amount, "r1")
    return system, opp


class TransferRulesTests(unittest.TestCase):
    def setUp(self):
        self.crm, self.opp = deal()

    def test_manager_transfer_moves_ownership_and_logs(self):
        self.crm.transfer(self.opp, "r2", "m1")
        self.assertEqual(self.crm.opps[self.opp]["owner"], "r2")
        self.assertEqual(self.crm.log[-1], ("transfer", self.opp, "m1"))

    def test_non_manager_cannot_transfer(self):
        for actor in ("r1", "r2"):
            with self.subTest(actor=actor):
                with self.assertRaises(PermissionError):
                    self.crm.transfer(self.opp, "r2", actor)
        self.assertEqual(self.crm.opps[self.opp]["owner"], "r1")

    def test_permission_precedes_target_validation(self):
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.opp, "nobody", "r1")
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.opp, "m1", "r1")

    def test_unknown_target_is_value_error(self):
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "ghost", "m1")
        self.assertEqual(self.crm.opps[self.opp]["owner"], "r1")

    def test_manager_cannot_be_target(self):
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "m1", "m1")
        self.assertEqual(self.crm.opps[self.opp]["owner"], "r1")

    def test_same_owner_is_rejected(self):
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "r1", "m1")
        self.assertEqual(self.crm.opps[self.opp]["owner"], "r1")

    def test_target_at_capacity_is_rejected(self):
        # r3 is a rep with capacity 0, so it is never below capacity
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "r3", "m1")
        self.assertEqual(self.crm.opps[self.opp]["owner"], "r1")

    def test_target_full_of_leads_is_rejected(self):
        system = fixtures.make(
            ("r1", "rep", 5), ("r2", "rep", 1), ("m1", "manager", 0)
        )
        lead = system.add_lead("a@corp.com", "A", "referral", "r1")
        system.qualify(lead, "r1")
        opp = system.convert(lead, 100, "r1")
        # r2 already owns one new lead: load 1, capacity 1
        other = system.add_lead("b@corp.com", "B", "web", "r1")
        self.assertEqual(system.leads[other]["owner"], "r2")
        with self.assertRaises(ValueError):
            system.transfer(opp, "r2", "m1")
        self.assertEqual(system.opps[opp]["owner"], "r1")

    def test_final_opportunity_cannot_be_transferred(self):
        self.crm.advance(self.opp, "lost", "r1")
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "r2", "m1")
        self.assertEqual(self.crm.opps[self.opp]["owner"], "r1")

    def test_unknown_opportunity_is_value_error(self):
        with self.assertRaises(ValueError):
            self.crm.transfer("O404", "r2", "m1")

    def test_failed_transfer_logs_nothing(self):
        log_before = list(self.crm.log)
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "r1", "m1")
        self.assertEqual(self.crm.log, log_before)


class SlotReleaseTests(unittest.TestCase):
    def test_transfer_frees_previous_owner_capacity(self):
        system = fixtures.make(("r1", "rep", 1), ("r2", "rep", 3), ("m1", "manager", 0))
        first = system.add_lead("a@gmail.com", "A", "referral", "r1")
        second = system.add_lead("b@corp.com", "B", "web", "r1")
        self.assertEqual(system.leads[second]["owner"], "r2")
        system.qualify(first, "r1")
        opp = system.convert(first, 100, "r1")
        blocked = system.add_lead("c@corp.com", "C", "web", "r1")
        self.assertEqual(system.leads[blocked]["owner"], "r2")
        system.transfer(opp, "r2", "m1")
        # r1 no longer owns the opportunity, so its slot is free again
        after = system.add_lead("d@corp.com", "D", "web", "r1")
        self.assertEqual(system.leads[after]["owner"], "r1")

    def test_transfer_hands_a_seeded_waiting_lead_to_the_previous_owner(self):
        system = fixtures.make(("r1", "rep", 1), ("r2", "rep", 5), ("m1", "manager", 0))
        first = system.add_lead("a@gmail.com", "A", "referral", "r1")
        waiting = system.add_lead("b@corp.com", "B", "web", "r1")
        system.qualify(first, "r1")
        opp = system.convert(first, 100, "r1")
        # Simulate a queue that formed while r1 was full.
        system.leads[waiting]["owner"] = None
        system._waiting.append(waiting)
        system.transfer(opp, "r2", "m1")
        self.assertEqual(system.leads[waiting]["owner"], "r1")
        self.assertEqual(
            system.log[-2:],
            [("transfer", opp, "m1"), ("assign", waiting, "system")],
        )
        self.assertEqual(system._waiting, [])

    def test_transfer_with_no_waiting_leads_logs_once(self):
        system = fixtures.make(("r1", "rep", 1), ("r2", "rep", 5), ("m1", "manager", 0))
        lead = system.add_lead("a@corp.com", "A", "referral", "r1")
        system.qualify(lead, "r1")
        opp = system.convert(lead, 100, "r1")
        before = len(system.log)
        system.transfer(opp, "r2", "m1")
        self.assertEqual(len(system.log), before + 1)
        self.assertEqual(system.log[-1], ("transfer", opp, "m1"))

    def test_transfer_to_owner_with_no_waiting_leads_just_moves(self):
        system = fixtures.make(("r1", "rep", 1), ("r2", "rep", 5), ("m1", "manager", 0))
        lead = system.add_lead("a@corp.com", "A", "referral", "r1")
        system.qualify(lead, "r1")
        opp = system.convert(lead, 100, "r1")
        before = len(system.log)
        system.transfer(opp, "r2", "m1")
        self.assertEqual(len(system.log), before + 1)


if __name__ == "__main__":
    unittest.main()
