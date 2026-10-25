"""Tests for discount, transfer, slot freeing, and failed-call atomicity."""

import unittest

from crm import CRM


def make_crm(r1_capacity=3):
    return CRM([
        {"id": "r1", "role": "rep", "capacity": r1_capacity},
        {"id": "r2", "role": "rep", "capacity": 3},
        {"id": "m1", "role": "manager", "capacity": 0},
    ])


def funnel(crm, email, source="referral", amount=10000):
    """add -> qualify -> convert using the lead's actual assigned owner."""
    lid = crm.add_lead(email, "N", source, "m1")
    actor = crm.leads[lid]["owner"]
    crm.qualify(lid, actor)
    return lid, crm.convert(lid, amount, actor)


class Discount(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        _, self.oid = funnel(self.crm, "a@corp.io", amount=10_000)

    def test_validation(self):
        with self.assertRaises(ValueError):
            self.crm.discount("O99", 10, "r1")  # unknown opp
        for bad in [0, 31, 1.5, True, False, "10"]:
            with self.assertRaises(ValueError, msg=repr(bad)):
                self.crm.discount(self.oid, bad, "r1")
        with self.assertRaises(PermissionError):
            self.crm.discount(self.oid, 10, "r2")

    def test_stage_must_be_open(self):
        self.crm.advance(self.oid, "lost", "r1")
        with self.assertRaises(ValueError):
            self.crm.discount(self.oid, 10, "r1")

    def test_non_manager_cap_and_math_and_cumulative_cap(self):
        self.crm.discount(self.oid, 10, "r1")   # 10000 -> 9000
        self.assertEqual(self.crm.opps[self.oid]["amount"], 9_000)
        with self.assertRaises(PermissionError):  # rep > 10
            self.crm.discount(self.oid, 15, "r1")
        self.crm.discount(self.oid, 15, "m1")   # 25% cumulative -> 7650
        self.assertEqual(self.crm.opps[self.oid]["amount"], 7_650)
    def test_exact_30_percent_cumulative_allowed_then_blocked(self):
        lid, oid = funnel(self.crm, "b@corp.io", amount=1_000)
        self.crm.discount(oid, 30, "m1")   # 1000 -> 700, exactly the floor
        self.assertEqual(self.crm.opps[oid]["amount"], 700)
        with self.assertRaises(ValueError):  # any further discount breaks the floor
            self.crm.discount(oid, 1, "m1")


class Transfer(unittest.TestCase):
    def test_only_managers(self):
        crm = make_crm()
        _, oid = funnel(crm, "a@corp.io")
        with self.assertRaises(PermissionError):
            crm.transfer(oid, "r2", "r1")

    def test_target_checks(self):
        crm = make_crm()
        _, oid = funnel(crm, "a@corp.io")
        with self.assertRaises(ValueError):  # unknown user
            crm.transfer(oid, "nobody", "m1")
        with self.assertRaises(ValueError):  # not a rep
            crm.transfer(oid, "m1", "m1")
        crm.transfer(oid, "r2", "m1")        # valid
        self.assertEqual(crm.opps[oid]["owner"], "r2")
        self.assertEqual(crm.log[-1], ("transfer", oid, "m1"))
        with self.assertRaises(ValueError):  # same owner
            crm.transfer(oid, "r2", "m1")
        crm.advance(oid, "lost", "r2")
        with self.assertRaises(ValueError):  # final stage
            crm.transfer(oid, "r1", "m1")

    def test_capacity_of_new_owner(self):
        crm = make_crm()
        _, oid1 = funnel(crm, "a@corp.io", "event", amount=1_000)
        # six referral leads fully load both capacity-3 reps (r1, r1, r2, r2, r1, r2)
        for i in range(1, 6):
            crm.add_lead("filler%d@corp.io" % i, "F", "referral", "m1")
        self.assertEqual(crm._load("r2"), 3)
        with self.assertRaises(ValueError):  # r2 at full capacity
            crm.transfer(oid1, "r2", "m1")


class SlotFreeing(unittest.TestCase):
    def test_transfer_blocked_while_waiting_queue_is_nonempty(self):
        # Emergent spec behavior (verified): leads only queue when every rep is
        # at capacity, so while a lead waits every rep is full and transfer
        # hits its capacity check — no transfer can free a slot then.
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        lid1 = crm.add_lead("a@corp.io", "A", "referral", "m1")   # r1
        crm.qualify(lid1, "r1")
        oid1 = crm.convert(lid1, 1_000, "r1")                     # O1, r1 still full
        lid2 = crm.add_lead("b@corp.io", "B", "referral", "m1")   # r2
        overflow = crm.add_lead("c@x.io", "C", "web", "m1")      # queued (all full)
        self.assertIsNone(crm.leads[overflow]["owner"])
        with self.assertRaises(ValueError):                       # no free slot
            crm.transfer(oid1, "r2", "m1")

    def test_transfer_with_empty_queue_logs_no_assign(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 3},
            {"id": "r2", "role": "rep", "capacity": 3},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        _, oid = funnel(crm, "a@corp.io")
        before = len(crm.log)
        crm.transfer(oid, "r2", "m1")
        ops = {entry[0] for entry in crm.log[before:]}
        self.assertEqual(ops, {"transfer"})


if __name__ == "__main__":
    unittest.main()
