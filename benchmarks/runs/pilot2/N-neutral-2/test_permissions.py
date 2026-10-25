"""Guard group: permission checks (unknown actor, ownership, manager-only actions)."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import fixtures  # noqa: E402


class UnknownActorTests(unittest.TestCase):
    def setUp(self):
        self.crm = fixtures.team()
        self.lead = self.crm.add_lead("a@corp.com", "A", "referral", "r1")
        self.crm.qualify(self.lead, "r1")
        self.opp = self.crm.convert(self.lead, 1000, "r1")

    def test_unknown_actor_rejected_everywhere(self):
        calls = (
            lambda: self.crm.add_lead("z@corp.com", "Z", "web", "ghost"),
            lambda: self.crm.qualify(self.lead, "ghost"),
            lambda: self.crm.convert(self.lead, 10, "ghost"),
            lambda: self.crm.advance(self.opp, "proposal", "ghost"),
            lambda: self.crm.discount(self.opp, 5, "ghost"),
            lambda: self.crm.transfer(self.opp, "r2", "ghost"),
        )
        for index, call in enumerate(calls):
            with self.subTest(call=index):
                with self.assertRaises(PermissionError):
                    call()

    def test_unknown_actor_is_checked_before_other_arguments(self):
        with self.assertRaises(PermissionError):
            self.crm.add_lead(None, None, "nonsense", "ghost")
        with self.assertRaises(PermissionError):
            self.crm.qualify("L999", "ghost")
        with self.assertRaises(PermissionError):
            self.crm.advance("O999", "bogus", "ghost")
        with self.assertRaises(PermissionError):
            self.crm.discount("O999", 999, "ghost")
        with self.assertRaises(PermissionError):
            self.crm.transfer("O999", "nobody", "ghost")

    def test_unknown_actor_does_not_log(self):
        log_before = list(self.crm.log)
        with self.assertRaises(PermissionError):
            self.crm.advance(self.opp, "proposal", "ghost")
        self.assertEqual(self.crm.log, log_before)
        self.assertEqual(self.crm.opps[self.opp]["stage"], "prospect")


class OwnershipTests(unittest.TestCase):
    def test_other_rep_cannot_qualify(self):
        system = fixtures.team()
        lead = system.add_lead("a@corp.com", "A", "referral", "r1")
        with self.assertRaises(PermissionError):
            system.qualify(lead, "r2")
        self.assertEqual(system.leads[lead]["status"], "new")
        self.assertEqual(len(system.log), 1)

    def test_other_rep_cannot_convert(self):
        system = fixtures.team()
        lead = system.add_lead("a@corp.com", "A", "referral", "r1")
        system.qualify(lead, "r1")
        with self.assertRaises(PermissionError):
            system.convert(lead, 100, "r2")
        self.assertEqual(system.opps, {})

    def test_other_rep_cannot_advance(self):
        system = fixtures.team()
        lead = system.add_lead("a@corp.com", "A", "referral", "r1")
        system.qualify(lead, "r1")
        opp = system.convert(lead, 100, "r1")
        with self.assertRaises(PermissionError):
            system.advance(opp, "proposal", "r2")
        self.assertEqual(system.opps[opp]["stage"], "prospect")

    def test_other_rep_cannot_discount(self):
        system = fixtures.team()
        lead = system.add_lead("a@corp.com", "A", "referral", "r1")
        system.qualify(lead, "r1")
        opp = system.convert(lead, 1000, "r1")
        with self.assertRaises(PermissionError):
            system.discount(opp, 5, "r2")
        self.assertEqual(system.opps[opp]["amount"], 1000)

    def test_owner_rep_may_act(self):
        system = fixtures.team()
        lead = system.add_lead("a@corp.com", "A", "referral", "r1")
        system.qualify(lead, "r1")
        opp = system.convert(lead, 1000, "r1")
        system.advance(opp, "proposal", "r1")
        system.discount(opp, 5, "r1")
        self.assertEqual(system.opps[opp]["stage"], "proposal")

    def test_manager_may_act_on_any_lead_and_opportunity(self):
        system = fixtures.team()
        lead = system.add_lead("a@corp.com", "A", "referral", "r1")
        system.qualify(lead, "m1")
        opp = system.convert(lead, 1000, "m1")
        system.advance(opp, "proposal", "m1")
        system.discount(opp, 5, "m1")
        self.assertEqual(system.opps[opp]["stage"], "proposal")
        self.assertEqual(system.leads[lead]["status"], "converted")

    def test_ownership_check_precedes_status_check(self):
        system = fixtures.team()
        lead = system.add_lead("a@corp.com", "A", "referral", "r1")
        # lead is still "new": r2 is rejected for ownership, not for status
        with self.assertRaises(PermissionError):
            system.qualify(lead, "r2")


class ManagerOnlyTests(unittest.TestCase):
    def test_transfer_requires_manager(self):
        system = fixtures.team()
        lead = system.add_lead("a@corp.com", "A", "referral", "r1")
        system.qualify(lead, "r1")
        opp = system.convert(lead, 100, "r1")
        with self.assertRaises(PermissionError):
            system.transfer(opp, "r2", "r1")
        self.assertEqual(system.opps[opp]["owner"], "r1")

    def test_manager_can_transfer(self):
        system = fixtures.team()
        lead = system.add_lead("a@corp.com", "A", "referral", "r1")
        system.qualify(lead, "r1")
        opp = system.convert(lead, 100, "r1")
        system.transfer(opp, "r2", "m1")
        self.assertEqual(system.opps[opp]["owner"], "r2")

    def test_manager_can_add_leads_too(self):
        system = fixtures.team()
        lead = system.add_lead("a@corp.com", "A", "referral", "m1")
        self.assertEqual(system.leads[lead]["owner"], "r1")


if __name__ == "__main__":
    unittest.main()
