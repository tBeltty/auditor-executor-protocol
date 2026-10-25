"""Tests for the review findings: waiting-queue mechanics, atomicity of
failed calls, spec check-order edges, and robustness to odd argument types."""

import unittest

from crm import CRM, DuplicateLeadError


class TestWaitingQueue(unittest.TestCase):
    def test_queue_drains_fifo_across_successive_frees(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 2},
            {"id": "m", "role": "manager", "capacity": 5},
        ])
        l1 = crm.add_lead("a@acme.com", "A", "referral", "m")  # r1
        l2 = crm.add_lead("b@acme.com", "B", "referral", "m")  # r1, full
        w1 = crm.add_lead("c@acme.com", "C", "web", "m")       # oldest waiter
        w2 = crm.add_lead("d@acme.com", "D", "web", "m")       # waiter
        crm.qualify(l1, "m")
        o1 = crm.convert(l1, 1000, "m")
        crm.qualify(l2, "m")
        o2 = crm.convert(l2, 1000, "m")
        crm.log = []
        crm.advance(o1, "lost", "m")  # frees one slot -> oldest waiter
        self.assertEqual(crm.log[-1], ("assign", w1, "system"))
        self.assertEqual(crm.leads[w1]["owner"], "r1")
        self.assertIsNone(crm.leads[w2]["owner"])
        crm.advance(o2, "lost", "m")  # next slot -> next oldest waiter
        self.assertEqual(crm.log[-1], ("assign", w2, "system"))
        self.assertEqual(crm.leads[w2]["owner"], "r1")

    def test_manager_actor_won_frees_the_owner_slot(self):
        # The slot freed belongs to the opportunity's owner (a rep), not the
        # acting manager; the waiting lead lands on the rep.
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "m", "role": "manager", "capacity": 5},
        ])
        l1 = crm.add_lead("a@acme.com", "A", "referral", "m")  # r1, full
        l2 = crm.add_lead("b@acme.com", "B", "web", "m")       # waiting
        crm.qualify(l1, "m")
        oid = crm.convert(l1, 1000, "m")
        crm.advance(oid, "proposal", "m")
        crm.advance(oid, "negotiation", "m")
        crm.advance(oid, "won", "m")  # manager acts; r1's slot frees
        self.assertEqual(crm.leads[l2]["owner"], "r1")
        self.assertEqual(crm.log[-1], ("assign", l2, "system"))

    def test_zero_capacity_pool_queues_everything(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 0},
            {"id": "m", "role": "manager", "capacity": 5},
        ])
        lids = [
            crm.add_lead("u%d@acme.com" % i, "U", "referral", "m")
            for i in range(3)
        ]
        for lid in lids:
            self.assertIsNone(crm.leads[lid]["owner"])
            with self.assertRaises(PermissionError):
                crm.qualify(lid, "r1")
        crm.qualify(lids[0], "m")  # managers may touch unowned leads
        with self.assertRaises(ValueError):
            crm.convert(lids[0], 100, "m")  # still no owner
        self.assertEqual(crm.opps, {})

    def test_qualified_waiting_lead_keeps_status_when_assigned(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "m", "role": "manager", "capacity": 5},
        ])
        l1 = crm.add_lead("a@acme.com", "A", "referral", "m")
        l2 = crm.add_lead("b@acme.com", "B", "referral", "m")
        crm.qualify(l1, "m")
        oid = crm.convert(l1, 1000, "m")
        crm.qualify(l2, "m")  # waiting lead, qualified by manager
        crm.advance(oid, "lost", "m")
        self.assertEqual(crm.leads[l2]["owner"], "r1")
        self.assertEqual(crm.leads[l2]["status"], "qualified")

    def test_waiting_lead_still_blocks_duplicate_email(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "m", "role": "manager", "capacity": 5},
        ])
        crm.add_lead("a@acme.com", "A", "web", "m")
        w = crm.add_lead("w@acme.com", "W", "web", "m")  # waiting
        with self.assertRaises(DuplicateLeadError) as ctx:
            crm.add_lead("W@acme.com", "dup", "web", "m")
        self.assertEqual(ctx.exception.existing_id, w)

    def test_converted_lead_still_blocks_duplicate_email(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 5},
            {"id": "m", "role": "manager", "capacity": 5},
        ])
        lid = crm.add_lead("a@acme.com", "A", "referral", "m")
        crm.qualify(lid, "m")
        crm.convert(lid, 1000, "m")
        with self.assertRaises(DuplicateLeadError) as ctx:
            crm.add_lead("a@acme.com", "B", "web", "m")
        self.assertEqual(ctx.exception.existing_id, lid)

    def test_failed_calls_never_assign_from_the_queue(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "m", "role": "manager", "capacity": 5},
        ])
        l1 = crm.add_lead("a@acme.com", "A", "referral", "m")
        w1 = crm.add_lead("b@acme.com", "B", "web", "m")  # waiting
        crm.qualify(l1, "m")
        oid = crm.convert(l1, 1000, "m")
        crm.log = []
        crm.advance(oid, "proposal", "m")  # non-final: no assignment yet
        with self.assertRaises(ValueError):
            crm.transfer(oid, "m", "m")  # managers cannot own (check 3)
        with self.assertRaises(ValueError):
            crm.transfer(oid, "r1", "m")  # same owner (check 5)
        self.assertEqual(crm.log, [("advance", oid, "m")])
        self.assertIsNone(crm.leads[w1]["owner"])


class TestConstructorEdgeCases(unittest.TestCase):
    def test_redeclared_id_takes_its_final_role(self):
        crm = CRM([
            {"id": "x", "role": "rep", "capacity": 5},
            {"id": "x", "role": "manager", "capacity": 5},
            {"id": "m", "role": "manager", "capacity": 5},
        ])
        lid = crm.add_lead("a@x.com", "A", "web", "m")
        self.assertIsNone(crm.leads[lid]["owner"])  # "x" is no longer a rep

    def test_empty_reps_list(self):
        crm = CRM([])
        with self.assertRaises(PermissionError):
            crm.add_lead("a@x.com", "A", "web", "ghost")
        self.assertEqual(crm.forecast(), {"open": 0, "weighted": 0, "won": 0})


class TestCheckOrderEdges(unittest.TestCase):
    def test_name_check_precedes_duplicate_check(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 5}])
        crm.add_lead("a@acme.com", "A", "web", "r1")
        with self.assertRaises(ValueError):  # not DuplicateLeadError
            crm.add_lead("a@acme.com", "", "web", "r1")

    def test_source_check_precedes_duplicate_check(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 5}])
        crm.add_lead("a@acme.com", "A", "web", "r1")
        with self.assertRaises(ValueError):  # not DuplicateLeadError
            crm.add_lead("a@acme.com", "B", "phone", "r1")

    def test_permission_precedes_final_stage_in_advance(self):
        crm, oid = self._crm_with_opp()
        crm.advance(oid, "lost", "r1")
        # outsider hits check 3 (PermissionError) before check 4 (final stage)
        with self.assertRaises(PermissionError):
            crm.advance(oid, "proposal", "r2")

    def test_final_stage_precedes_rep_discount_cap(self):
        crm, oid = self._crm_with_opp()
        crm.advance(oid, "lost", "r1")
        with self.assertRaises(ValueError):  # stage checked before pct cap
            crm.discount(oid, 30, "r1")

    def _crm_with_opp(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 5},
            {"id": "r2", "role": "rep", "capacity": 5},
            {"id": "m", "role": "manager", "capacity": 5},
        ])
        lid = crm.add_lead("a@acme.com", "A", "referral", "m")
        crm.qualify(lid, "m")
        oid = crm.convert(lid, 1000, "m")
        return crm, oid

    def test_manager_actor_precedes_new_owner_check(self):
        crm, oid = self._setup_opp()
        with self.assertRaises(PermissionError):  # rep actor, unknown owner
            crm.transfer(oid, "ghost", "r1")

    def _setup_opp(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 5},
            {"id": "m", "role": "manager", "capacity": 5},
        ])
        lid = crm.add_lead("a@acme.com", "A", "referral", "m")
        crm.qualify(lid, "m")
        oid = crm.convert(lid, 1000, "m")
        return crm, oid

    def test_lead_existence_precedes_actor_permission(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 5},
            {"id": "m", "role": "manager", "capacity": 5},
        ])
        with self.assertRaises(ValueError):  # unknown lead, owner-or-mgr check
            crm.qualify("L7", "r1")

    def test_actor_existence_precedes_entity_checks(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 5}])
        with self.assertRaises(PermissionError):  # unknown actor first
            crm.qualify("L7", "ghost")
        with self.assertRaises(PermissionError):
            crm.advance("O7", "bogus", "ghost")


class TestArgumentRobustness(unittest.TestCase):
    def setUp(self):
        self.crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 5},
            {"id": "m", "role": "manager", "capacity": 5},
        ])

    def test_unhashable_actor_is_permission_error(self):
        for call in (
            lambda: self.crm.add_lead("a@x.com", "A", "web", ["r1"]),
            lambda: self.crm.qualify("L1", ["r1"]),
            lambda: self.crm.convert("L1", 1, {"a": 1}),
            lambda: self.crm.advance("O1", "won", ["r1"]),
            lambda: self.crm.discount("O1", 5, ["r1"]),
            lambda: self.crm.transfer("O1", "r1", ["m"]),
        ):
            with self.assertRaises(PermissionError):
                call()

    def test_unhashable_ids_are_value_error(self):
        lid = self.crm.add_lead("a@x.com", "A", "referral", "m")
        self.crm.qualify(lid, "m")
        oid = self.crm.convert(lid, 1000, "m")
        for call in (
            lambda: self.crm.qualify(["L1"], "m"),
            lambda: self.crm.convert(["L1"], 100, "m"),
            lambda: self.crm.advance(["O1"], "proposal", "m"),
            lambda: self.crm.discount(["O1"], 5, "m"),
            lambda: self.crm.transfer(oid, ["r1"], "m"),
        ):
            with self.assertRaises(ValueError):
                call()
        self.assertEqual(self.crm.log[-1], ("convert", oid, "m"))

    def test_unhashable_enum_arguments_are_value_error(self):
        lid = self.crm.add_lead("a@x.com", "A", "referral", "m")
        self.crm.qualify(lid, "m")
        oid = self.crm.convert(lid, 1000, "m")
        with self.assertRaises(ValueError):
            self.crm.advance(oid, ["won"], "m")
        with self.assertRaises(ValueError):
            self.crm.discount(oid, [5], "m")
        with self.assertRaises(ValueError):
            self.crm.add_lead("b@x.com", "B", ["web"], "m")
        self.assertEqual(self.crm.opps[oid]["stage"], "prospect")
        self.assertEqual(self.crm.opps[oid]["amount"], 1000)


class TestNoRetroactiveAssignment(unittest.TestCase):
    def test_convert_freeing_a_lead_slot_does_not_dequeue(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 2},
            {"id": "m", "role": "manager", "capacity": 5},
        ])
        l1 = crm.add_lead("a@acme.com", "A", "referral", "m")  # r1
        l2 = crm.add_lead("b@acme.com", "B", "web", "m")       # r1, full
        w1 = crm.add_lead("c@acme.com", "C", "web", "m")       # waiting
        crm.qualify(l1, "m")
        crm.convert(l1, 1000, "m")  # lead slot opens but an open opp fills it
        self.assertIsNone(crm.leads[w1]["owner"])
        # load is still 2 (l2 + opp), so the next lead also waits
        w2 = crm.add_lead("d@acme.com", "D", "web", "m")
        self.assertIsNone(crm.leads[w2]["owner"])

    def test_failed_advance_does_not_dequeue(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "m", "role": "manager", "capacity": 5},
        ])
        l1 = crm.add_lead("a@acme.com", "A", "referral", "m")  # r1
        w1 = crm.add_lead("b@acme.com", "B", "web", "m")       # waiting
        crm.qualify(l1, "m")
        oid = crm.convert(l1, 1000, "m")
        with self.assertRaises(ValueError):
            crm.advance(oid, "won", "m")  # prospect -> won skips negotiation
        self.assertIsNone(crm.leads[w1]["owner"])
        self.assertNotIn(("assign", w1, "system"), crm.log)
        crm.advance(oid, "proposal", "m")
        crm.advance(oid, "negotiation", "m")
        crm.advance(oid, "won", "m")  # the valid final move dequeues
        self.assertEqual(crm.leads[w1]["owner"], "r1")


if __name__ == "__main__":
    unittest.main()
