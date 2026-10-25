import unittest

from crm import CRM, DuplicateLeadError
from helpers import GuardChecks

REPS = [
    {"id": "r1", "role": "rep", "capacity": 3},
    {"id": "r2", "role": "rep", "capacity": 3},
    {"id": "m1", "role": "manager", "capacity": 9},
]


class AtomicityTests(GuardChecks, unittest.TestCase):
    def setUp(self):
        self.crm = CRM([dict(rep) for rep in REPS])
        lead = self.crm.add_lead("a@corp.com", "A", "referral", "r1")
        self.crm.qualify(lead, "r1")
        self.opp = self.crm.convert(lead, 1000, "r1")

    def test_failed_discount_changes_nothing(self):
        self.crm.discount(self.opp, 30, "m1")
        log_before = list(self.crm.log)
        self.expect_error("ATOMIC_STATE_GUARD", ValueError,
                          self.crm.discount, self.opp, 5, "m1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 700,
                         "ATOMIC_STATE_GUARD: a failed call must not change state")
        self.assertEqual(self.crm.log, log_before,
                         "ATOMIC_LOG_GUARD: a failed call must not append to the log")

    def test_failed_calls_change_nothing(self):
        before_log = list(self.crm.log)
        before_lead = dict(self.crm.leads["L1"])
        self.expect_error("ATOMIC_STATE_GUARD", PermissionError,
                          self.crm.advance, self.opp, "proposal", "r2")
        self.expect_error("ATOMIC_STATE_GUARD", ValueError,
                          self.crm.advance, self.opp, "won", "r1")
        self.expect_error("ATOMIC_STATE_GUARD", ValueError,
                          self.crm.discount, self.opp, 31, "m1")
        self.assertEqual(self.crm.log, before_log)
        self.assertEqual(self.crm.leads["L1"], before_lead)
        self.assertEqual(self.crm.opps[self.opp]["stage"], "prospect")

    def test_failed_add_lead_does_not_consume_ids(self):
        self.expect_error("ATOMIC_STATE_GUARD", DuplicateLeadError,
                          self.crm.add_lead, "a@corp.com", "A", "web", "r1")
        self.expect_error("ATOMIC_STATE_GUARD", PermissionError,
                          self.crm.add_lead, "b@corp.com", "B", "web", "ghost")
        self.assertEqual(len(self.crm.leads), 1)
        new_id = self.crm.add_lead("b@corp.com", "B", "web", "r1")
        self.assertEqual(new_id, "L2",
                         "ATOMIC_STATE_GUARD: failed calls must not consume ids")


if __name__ == "__main__":
    unittest.main()
