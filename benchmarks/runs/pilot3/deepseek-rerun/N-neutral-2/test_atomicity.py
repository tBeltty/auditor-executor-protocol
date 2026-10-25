import copy
import unittest

from crm import CRM, DuplicateLeadError


class AtomicityTests(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 2},
                {"id": "r2", "role": "rep", "capacity": 2},
                {"id": "m1", "role": "manager", "capacity": 5},
            ]
        )
        self.lead_id = self.crm.add_lead("deal@corp.com", "Deal", "referral", "r1")
        self.crm.qualify(self.lead_id, "r1")
        self.opp_id = self.crm.convert(self.lead_id, 60000, "r1")

    def snapshot(self):
        return (
            copy.deepcopy(self.crm.leads),
            copy.deepcopy(self.crm.opps),
            copy.deepcopy(self.crm.log),
        )

    def assert_unchanged(self, exc_type, call):
        before = self.snapshot()
        with self.assertRaises(exc_type):
            call()
        self.assertEqual(before, self.snapshot())

    def test_add_lead_failures(self):
        self.assert_unchanged(
            DuplicateLeadError,
            lambda: self.crm.add_lead(" DEAL@corp.com ", "Dup", "web", "r1"),
        )
        self.assert_unchanged(
            ValueError, lambda: self.crm.add_lead("nope", "N", "web", "r1")
        )
        self.assert_unchanged(
            ValueError, lambda: self.crm.add_lead("x@corp.com", " ", "web", "r1")
        )
        self.assert_unchanged(
            ValueError, lambda: self.crm.add_lead("x@corp.com", "X", "tv", "r1")
        )
        self.assert_unchanged(
            PermissionError,
            lambda: self.crm.add_lead("x@corp.com", "X", "web", "ghost"),
        )

    def test_qualify_failures(self):
        second = self.crm.add_lead("second@corp.com", "S", "referral", "r1")
        self.assert_unchanged(
            PermissionError, lambda: self.crm.qualify(second, "r1")
        )
        self.assert_unchanged(
            ValueError, lambda: self.crm.qualify(self.lead_id, "r1")
        )
        self.assert_unchanged(ValueError, lambda: self.crm.qualify("L99", "r1"))
        self.assert_unchanged(
            PermissionError, lambda: self.crm.qualify(second, "ghost")
        )

    def test_convert_failures(self):
        lead = self.crm.add_lead("third@corp.com", "T", "referral", "r1")
        self.crm.qualify(lead, "m1")
        self.assert_unchanged(ValueError, lambda: self.crm.convert(lead, 0, "r1"))
        self.assert_unchanged(
            ValueError, lambda: self.crm.convert(lead, True, "r1")
        )
        self.assert_unchanged(
            PermissionError, lambda: self.crm.convert(lead, 10, "r1")
        )
        self.assert_unchanged(
            ValueError, lambda: self.crm.convert(self.lead_id, 10, "m1")
        )

    def test_advance_failures(self):
        self.assert_unchanged(
            ValueError, lambda: self.crm.advance(self.opp_id, "won", "r1")
        )
        self.assert_unchanged(
            PermissionError, lambda: self.crm.advance(self.opp_id, "proposal", "r2")
        )
        self.crm.advance(self.opp_id, "proposal", "r1")
        self.assert_unchanged(
            PermissionError, lambda: self.crm.advance(self.opp_id, "negotiation", "r1")
        )
        self.crm.advance(self.opp_id, "lost", "r1")
        self.assert_unchanged(
            ValueError, lambda: self.crm.advance(self.opp_id, "lost", "m1")
        )

    def test_discount_failures(self):
        self.assert_unchanged(
            PermissionError, lambda: self.crm.discount(self.opp_id, 20, "r1")
        )
        self.assert_unchanged(
            ValueError, lambda: self.crm.discount(self.opp_id, 31, "m1")
        )
        self.crm.discount(self.opp_id, 30, "m1")
        self.assert_unchanged(
            ValueError, lambda: self.crm.discount(self.opp_id, 1, "m1")
        )

    def test_transfer_failures(self):
        self.assert_unchanged(
            PermissionError, lambda: self.crm.transfer(self.opp_id, "r2", "r1")
        )
        self.assert_unchanged(
            ValueError, lambda: self.crm.transfer(self.opp_id, "m1", "m1")
        )
        self.assert_unchanged(
            ValueError, lambda: self.crm.transfer(self.opp_id, "r1", "m1")
        )

    def test_failed_calls_do_not_consume_ids(self):
        with self.assertRaises(ValueError):
            self.crm.add_lead("bad", "B", "web", "r1")
        new_lead = self.crm.add_lead("fresh@corp.com", "F", "referral", "m1")
        self.assertEqual(new_lead, "L2")
        lead = self.crm.add_lead("fresh2@corp.com", "F2", "referral", "m1")
        self.crm.qualify(lead, "m1")
        with self.assertRaises(ValueError):
            self.crm.convert(lead, -5, "m1")
        self.assertEqual(self.crm.convert(lead, 10, "m1"), "O2")


if __name__ == "__main__":
    unittest.main()
