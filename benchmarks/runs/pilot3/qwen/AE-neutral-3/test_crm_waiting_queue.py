"""Spec lines 9, 18, 31, 39: the load rule, the FIFO waiting queue, and escaping it.

Line 18 says a lead with no eligible rep "joins a FIFO waiting queue"; line 31
describes how it leaves. These tests pin both halves plus the transfer variant of
the same freeing rule (line 39).
"""

import unittest

from crm import CRM


def crm_of(*reps):
    return CRM([{"id": rid, "role": role, "capacity": cap}
                for rid, role, cap in reps])


class TestLoadDefinition(unittest.TestCase):
    """Line 9: load = own leads with status new/qualified + own non-final opps."""

    def test_new_and_qualified_leads_both_count(self):
        crm = crm_of(("r1", "rep", 2), ("m1", "manager", 5))
        a = crm.add_lead("a@corp.com", "A", "referral", "m1")
        b = crm.add_lead("b@corp.com", "B", "referral", "m1")
        self.assertEqual((crm.leads[a]["owner"], crm.leads[b]["owner"]), ("r1", "r1"))
        crm.qualify(a, "m1")                       # qualifying keeps the load
        c = crm.add_lead("c@corp.com", "C", "referral", "m1")
        self.assertIsNone(crm.leads[c]["owner"])

    def test_converted_lead_does_not_count_but_its_opportunity_does(self):
        crm = crm_of(("r1", "rep", 1), ("m1", "manager", 5))
        lead = crm.add_lead("a@corp.com", "A", "referral", "m1")
        crm.qualify(lead, "m1")
        opp = crm.convert(lead, 1000, "m1")
        blocked = crm.add_lead("b@corp.com", "B", "referral", "m1")
        self.assertIsNone(crm.leads[blocked]["owner"])
        crm.advance(opp, "lost", "m1")
        self.assertEqual(crm.leads[blocked]["owner"], "r1")

    def test_open_opportunity_keeps_the_slot_until_final(self):
        crm = crm_of(("r1", "rep", 1), ("m1", "manager", 5))
        lead = crm.add_lead("a@corp.com", "A", "referral", "m1")
        crm.qualify(lead, "m1")
        opp = crm.convert(lead, 1000, "m1")
        for stage in ("proposal", "negotiation"):
            crm.advance(opp, stage, "m1")
            blocked = crm.add_lead("b%s@corp.com" % stage, "B", "referral", "m1")
            self.assertIsNone(crm.leads[blocked]["owner"])
        crm.advance(opp, "won", "m1")
        self.assertEqual(crm.leads["L2"]["owner"], "r1")   # oldest waiting lead escaped
        self.assertIsNone(crm.leads["L3"]["owner"])        # capacity is still 1

    def test_managers_never_receive_work_whatever_their_capacity(self):
        crm = crm_of(("m1", "manager", 100))
        for n in range(3):
            lead = crm.add_lead("a%d@corp.com" % n, "A", "referral", "m1")
            self.assertIsNone(crm.leads[lead]["owner"])
        self.assertEqual([e for e in crm.log if e[0] == "assign"], [])
        self.assertNotIn("m1", [lead["owner"] for lead in crm.leads.values()])

    def test_assignment_moves_as_loads_change(self):
        crm = crm_of(("r1", "rep", 1), ("r2", "rep", 1), ("m1", "manager", 5))
        a = crm.add_lead("a@corp.com", "A", "referral", "m1")   # tie -> "r1"
        b = crm.add_lead("b@corp.com", "B", "referral", "m1")   # r1 full -> r2
        c = crm.add_lead("c@corp.com", "C", "referral", "m1")   # both full -> queue
        self.assertEqual((crm.leads[a]["owner"], crm.leads[b]["owner"]), ("r1", "r2"))
        self.assertIsNone(crm.leads[c]["owner"])


class TestQueueJoin(unittest.TestCase):
    """Line 18, first half: with no eligible rep, owner is None and it joins the queue."""

    def test_lead_joins_queue_when_every_rep_is_full(self):
        crm = crm_of(("r1", "rep", 1), ("m1", "manager", 5))
        first = crm.add_lead("a@corp.com", "A", "referral", "m1")
        joined = crm.add_lead("b@corp.com", "B", "web", "m1")
        self.assertEqual(crm.leads[first]["owner"], "r1")
        self.assertIsNone(crm.leads[joined]["owner"])
        self.assertEqual(crm.leads[joined]["status"], "new")
        # Joining the queue is not an assignment: only the add_lead entry is logged.
        self.assertEqual(crm.log, [("add_lead", first, "m1"), ("add_lead", joined, "m1")])

    def test_joined_lead_is_still_intact_and_claimable(self):
        crm = crm_of(("r1", "rep", 1), ("m1", "manager", 5))
        mine = crm.add_lead("a@corp.com", "A", "referral", "m1")
        crm.qualify(mine, "m1")
        opp = crm.convert(mine, 1000, "m1")
        joined = crm.add_lead("b@corp.com", "Bea", "event", "m1")
        before = dict(crm.leads[joined])
        crm.advance(opp, "lost", "m1")
        after = crm.leads[joined]
        self.assertEqual(after["owner"], "r1")
        for field in ("id", "email", "name", "source", "score", "status"):
            self.assertEqual(after[field], before[field], field)


class TestQueueEscape(unittest.TestCase):
    """Line 18 + line 31: an escaping lead leaves the FIFO queue exactly once."""

    def setUp(self):
        self.crm = crm_of(("r1", "rep", 1), ("m1", "manager", 5))
        mine = self.crm.add_lead("a@corp.com", "A", "referral", "m1")
        self.crm.qualify(mine, "m1")
        self.opp = self.crm.convert(mine, 1000, "m1")
        # referral (score 45) so the escaped lead can later be qualified itself.
        self.waiting = self.crm.add_lead("w@corp.com", "W", "referral", "m1")
        self.assertIsNone(self.crm.leads[self.waiting]["owner"])

    def assertEscapes(self):
        for stage in ("proposal", "negotiation", "won"):
            self.crm.advance(self.opp, stage, "m1")
        self.assertEqual(self.crm.leads[self.waiting]["owner"], "r1")
        self.assertEqual(self.crm.log[-1], ("assign", self.waiting, "system"))

    def test_queued_lead_escapes_when_a_slot_frees(self):
        self.assertEscapes()

    def test_escape_does_not_change_status_or_score(self):
        self.assertEscapes()
        self.assertEqual(self.crm.leads[self.waiting]["status"], "new")
        self.assertEqual(self.crm.leads[self.waiting]["score"], 45)

    def test_a_lead_escapes_the_queue_only_once(self):
        self.assertEscapes()
        first_escape_log = list(self.crm.log)
        # Another slot frees (the escaped lead is now load-bearing, so convert it).
        self.crm.qualify(self.waiting, "m1")
        second_opp = self.crm.convert(self.waiting, 2000, "m1")
        self.crm.advance(second_opp, "lost", "m1")
        assigns = [e for e in self.crm.log if e[0] == "assign"]
        self.assertEqual(assigns, [("assign", self.waiting, "system")],
                         "the same lead was assigned twice")
        extra = [e for e in self.crm.log[len(first_escape_log):] if e[0] == "assign"]
        self.assertEqual(extra, [], "a slot freed again re-assigned an owned lead")

    def test_escape_order_is_fifo_not_last_in_first(self):
        """The oldest waiting lead leaves first (a LIFO queue would take "younger")."""
        crm = crm_of(("r1", "rep", 1), ("r2", "rep", 1), ("m1", "manager", 5))
        l1 = crm.add_lead("a@corp.com", "A", "referral", "m1")   # r1
        crm.add_lead("b@corp.com", "B", "referral", "m1")        # r2
        older = crm.add_lead("zz@corp.com", "Z", "referral", "m1")
        younger = crm.add_lead("aa@corp.com", "A2", "referral", "m1")
        self.assertEqual((crm.leads[older]["owner"], crm.leads[younger]["owner"]),
                         (None, None))
        crm.qualify(l1, "m1")
        opp = crm.convert(l1, 1000, "m1")
        crm.advance(opp, "lost", "m1")
        self.assertEqual(crm.leads[older]["owner"], "r1")
        self.assertIsNone(crm.leads[younger]["owner"])
        assigns = [e[1] for e in crm.log if e[0] == "assign"]
        self.assertEqual(assigns, [older], "only the oldest waiting lead escaped")

    def test_escape_stops_at_capacity(self):
        crm = crm_of(("r1", "rep", 2), ("m1", "manager", 5))
        first = crm.add_lead("a@corp.com", "A", "referral", "m1")
        crm.add_lead("b@corp.com", "B", "referral", "m1")
        queued1 = crm.add_lead("c@corp.com", "C", "referral", "m1")
        queued2 = crm.add_lead("d@corp.com", "D", "referral", "m1")
        self.assertEqual([crm.leads[q]["owner"] for q in (queued1, queued2)],
                         [None, None])
        crm.qualify(first, "m1")
        opp = crm.convert(first, 500, "m1")
        for stage in ("proposal", "negotiation", "won"):
            crm.advance(opp, stage, "m1")
        self.assertEqual(crm.leads[queued1]["owner"], "r1")
        self.assertIsNone(crm.leads[queued2]["owner"])
        self.assertEqual([e for e in crm.log if e[0] == "assign"],
                         [("assign", queued1, "system")])

    def test_only_the_rep_whose_slot_freed_takes_waiting_leads(self):
        crm = crm_of(("r1", "rep", 1), ("r2", "rep", 1), ("m1", "manager", 5))
        l1 = crm.add_lead("a@corp.com", "A", "referral", "m1")   # r1
        l2 = crm.add_lead("b@corp.com", "B", "referral", "m1")   # r2
        waiting = crm.add_lead("c@corp.com", "C", "referral", "m1")
        crm.qualify(l2, "m1")
        opp2 = crm.convert(l2, 1000, "m1")
        crm.advance(opp2, "lost", "m1")
        self.assertEqual(crm.leads[waiting]["owner"], "r2")
        self.assertEqual(crm.leads[l1]["owner"], "r1")
        self.assertEqual(crm.log[-1], ("assign", waiting, "system"))

    def test_advance_to_non_final_stage_does_not_release_a_slot(self):
        crm = crm_of(("r1", "rep", 1), ("m1", "manager", 5))
        mine = crm.add_lead("a@corp.com", "A", "referral", "m1")
        crm.qualify(mine, "m1")
        opp = crm.convert(mine, 1000, "m1")
        waiting = crm.add_lead("w@corp.com", "W", "referral", "m1")
        crm.advance(opp, "proposal", "m1")
        self.assertIsNone(crm.leads[waiting]["owner"])
        self.assertNotIn("assign", [e[0] for e in crm.log])


class TestTransferAndTheQueue(unittest.TestCase):
    """Line 39: transfer frees the previous owner's slot the same way advance does."""

    def test_transfer_frees_the_previous_owner_for_the_next_lead(self):
        crm = crm_of(("r1", "rep", 1), ("r2", "rep", 1), ("m1", "manager", 5))
        lead = crm.add_lead("a@corp.com", "A", "referral", "m1")   # r1, full
        crm.qualify(lead, "m1")
        opp = crm.convert(lead, 1000, "m1")                        # r1 still full
        # r2 holds no work, so the transfer is legal: check 6 looks at the target.
        crm.transfer(opp, "r2", "m1")
        self.assertEqual(crm.opps[opp]["owner"], "r2")
        next_lead = crm.add_lead("c@corp.com", "C", "referral", "m1")
        self.assertEqual(crm.leads[next_lead]["owner"], "r1",
                         "the previous owner's slot was freed")

    def test_transfer_cannot_run_while_a_lead_waits_and_every_rep_is_full(self):
        """Documented consequence of lines 9/18/39: a non-empty queue means every rep
        is at capacity, so transfer check 6 (target below capacity) must fail."""
        crm = crm_of(("r1", "rep", 1), ("r2", "rep", 1), ("m1", "manager", 5))
        l1 = crm.add_lead("a@corp.com", "A", "referral", "m1")   # r1
        crm.add_lead("b@corp.com", "B", "referral", "m1")        # r2
        waiting = crm.add_lead("c@corp.com", "C", "referral", "m1")
        self.assertIsNone(crm.leads[waiting]["owner"])
        crm.qualify(l1, "m1")
        opp = crm.convert(l1, 1000, "m1")
        with self.assertRaises(ValueError):
            crm.transfer(opp, "r2", "m1")
        self.assertEqual(crm.opps[opp]["owner"], "r1")
        self.assertNotIn("assign", [e[0] for e in crm.log])

    def test_successful_transfer_logs_no_assign(self):
        """When transfer is legal the queue is necessarily empty: no assign entries."""
        crm = crm_of(("r1", "rep", 2), ("r2", "rep", 2), ("m1", "manager", 5))
        lead = crm.add_lead("a@corp.com", "A", "referral", "m1")   # r1
        crm.qualify(lead, "m1")
        opp = crm.convert(lead, 1000, "m1")
        crm.transfer(opp, "r2", "m1")
        self.assertEqual([e for e in crm.log if e[0] == "assign"], [])
        self.assertEqual(crm.log[-1], ("transfer", opp, "m1"))


if __name__ == "__main__":
    unittest.main()
