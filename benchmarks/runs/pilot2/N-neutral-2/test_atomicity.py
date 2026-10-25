"""Guard group: atomicity -- a failed call changes nothing and logs nothing."""

import copy
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import crm  # noqa: E402
import fixtures  # noqa: E402


def snapshot(system):
    return {
        "leads": copy.deepcopy(system.leads),
        "opps": copy.deepcopy(system.opps),
        "log": copy.deepcopy(system.log),
    }


class AtomicityTests(unittest.TestCase):
    def setUp(self):
        self.crm = fixtures.make(("r1", "rep", 5), ("r2", "rep", 5), ("m1", "manager", 0))
        self.lead = self.crm.add_lead("base@corp.com", "Base", "referral", "r1")
        self.crm.qualify(self.lead, "r1")
        self.opp = self.crm.convert(self.lead, 1000, "r1")

    def assert_fails_cleanly(self, exception_type, call):
        before = snapshot(self.crm)
        with self.assertRaises(exception_type):
            call()
        self.assertEqual(snapshot(self.crm), before)

    def test_failed_add_lead_changes_nothing(self):
        self.assert_fails_cleanly(
            ValueError, lambda: self.crm.add_lead("bad-email", "X", "web", "r1")
        )
        self.assert_fails_cleanly(
            ValueError, lambda: self.crm.add_lead("new@corp.com", "", "web", "r1")
        )
        self.assert_fails_cleanly(
            ValueError, lambda: self.crm.add_lead("new@corp.com", "X", "billboard", "r1")
        )
        self.assert_fails_cleanly(
            crm.DuplicateLeadError,
            lambda: self.crm.add_lead("BASE@corp.com", "Clone", "event", "m1"),
        )
        self.assert_fails_cleanly(
            PermissionError, lambda: self.crm.add_lead("new@corp.com", "X", "web", "ghost")
        )

    def test_failed_qualify_changes_nothing(self):
        low = self.crm.add_lead("low@gmail.com", "Low", "web", "r1")
        owner = self.crm.leads[low]["owner"]
        before_status = self.crm.leads[low]["status"]
        self.assert_fails_cleanly(ValueError, lambda: self.crm.qualify(low, owner))
        self.assertEqual(self.crm.leads[low]["status"], before_status)
        self.assert_fails_cleanly(ValueError, lambda: self.crm.qualify(self.lead, "r1"))
        self.assert_fails_cleanly(ValueError, lambda: self.crm.qualify("L404", "r1"))
        other = "r2" if owner == "r1" else "r1"
        self.assert_fails_cleanly(PermissionError, lambda: self.crm.qualify(low, other))

    def test_failed_convert_changes_nothing(self):
        fresh = self.crm.add_lead("fresh@corp.com", "Fresh", "referral", "r1")
        owner = self.crm.leads[fresh]["owner"]
        self.assert_fails_cleanly(ValueError, lambda: self.crm.convert(fresh, 100, owner))
        self.assert_fails_cleanly(ValueError, lambda: self.crm.convert(self.lead, 0, "r1"))
        self.assert_fails_cleanly(
            ValueError, lambda: self.crm.convert(self.lead, True, "r1")
        )
        other = "r2" if owner == "r1" else "r1"
        self.assert_fails_cleanly(
            PermissionError, lambda: self.crm.convert(fresh, 100, other)
        )
        self.assertEqual(self.crm.leads[fresh]["status"], "new")
        self.assertEqual(list(self.crm.opps), [self.opp])

    def test_failed_advance_changes_nothing(self):
        self.assert_fails_cleanly(
            ValueError, lambda: self.crm.advance(self.opp, "won", "r1")
        )
        self.assert_fails_cleanly(
            ValueError, lambda: self.crm.advance(self.opp, "teleported", "r1")
        )
        self.assert_fails_cleanly(
            PermissionError, lambda: self.crm.advance(self.opp, "proposal", "r2")
        )
        self.assert_fails_cleanly(
            ValueError, lambda: self.crm.advance("O404", "proposal", "r1")
        )
        self.assertEqual(self.crm.opps[self.opp]["stage"], "prospect")

    def test_failed_discount_changes_nothing(self):
        self.assert_fails_cleanly(ValueError, lambda: self.crm.discount(self.opp, 0, "r1"))
        self.assert_fails_cleanly(ValueError, lambda: self.crm.discount(self.opp, 31, "m1"))
        self.assert_fails_cleanly(
            PermissionError, lambda: self.crm.discount(self.opp, 11, "r1")
        )
        self.assert_fails_cleanly(
            PermissionError, lambda: self.crm.discount(self.opp, 5, "r2")
        )
        self.assertEqual(self.crm.opps[self.opp]["amount"], 1000)

    def test_failed_discount_does_not_move_amount_below_the_floor(self):
        self.crm.discount(self.opp, 30, "m1")
        before = snapshot(self.crm)
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp, 1, "m1")
        self.assertEqual(snapshot(self.crm), before)
        self.assertEqual(self.crm.opps[self.opp]["amount"], 700)

    def test_failed_transfer_changes_nothing(self):
        self.assert_fails_cleanly(
            PermissionError, lambda: self.crm.transfer(self.opp, "r2", "r1")
        )
        self.assert_fails_cleanly(
            ValueError, lambda: self.crm.transfer(self.opp, "ghost", "m1")
        )
        self.assert_fails_cleanly(
            ValueError, lambda: self.crm.transfer(self.opp, "r1", "m1")
        )
        self.assertEqual(self.crm.opps[self.opp]["owner"], "r1")

    def test_failed_calls_do_not_consume_ids(self):
        self.assert_fails_cleanly(
            crm.DuplicateLeadError,
            lambda: self.crm.add_lead("base@corp.com", "Clone", "web", "r1"),
        )
        self.assertEqual(self.crm.add_lead("next@corp.com", "Next", "web", "r1"), "L2")
        self.assert_fails_cleanly(
            ValueError, lambda: self.crm.convert(self.lead, -5, "r1")
        )
        other = self.crm.add_lead("third@corp.com", "Third", "referral", "r1")
        self.crm.qualify(other, "r1")
        self.assertEqual(self.crm.convert(other, 50, "r1"), "O2")

    def test_failed_call_does_not_assign_waiting_leads(self):
        system = fixtures.make(("r1", "rep", 1), ("m1", "manager", 0))
        first = system.add_lead("a@gmail.com", "A", "referral", "r1")
        waiting = system.add_lead("b@corp.com", "B", "web", "r1")
        system.qualify(first, "r1")
        opp = system.convert(first, 100, "r1")
        before = snapshot(system)
        with self.assertRaises(ValueError):
            system.advance(opp, "won", "r1")  # illegal jump
        self.assertEqual(snapshot(system), before)
        self.assertIsNone(system.leads[waiting]["owner"])


if __name__ == "__main__":
    unittest.main()
