"""Tests for load-aware ownership, the waiting queue, and slot freeing."""

import unittest

from crm import CRM


def load_of(crm, rep_id):
    """The spec's definition of load, recomputed from the public dicts."""
    count = 0
    for lead in crm.leads.values():
        if lead["owner"] == rep_id and lead["status"] in ("new", "qualified"):
            count += 1
    for opp in crm.opps.values():
        if opp["owner"] == rep_id and opp["stage"] not in ("won", "lost"):
            count += 1
    return count



def crm_with(reps):
    return CRM(reps)


REPS = [
    {"id": "r1", "role": "rep", "capacity": 1},
    {"id": "r2", "role": "rep", "capacity": 2},
    {"id": "m1", "role": "manager", "capacity": 10},
]


class TestOwnershipSelection(unittest.TestCase):
    def test_first_lead_goes_to_lowest_load(self):
        crm = crm_with(REPS)
        crm.add_lead("a@acme.com", "A", "web", "m1")
        # both reps have load 0 -> smallest id in string order wins
        self.assertEqual(crm.leads["L1"]["owner"], "r1")

    def test_next_lead_goes_to_other_rep_when_full(self):
        crm = crm_with(REPS)
        crm.add_lead("a@acme.com", "A", "web", "m1")
        crm.add_lead("b@acme.com", "B", "web", "m1")
        self.assertEqual(crm.leads["L2"]["owner"], "r2")

    def test_prefers_lower_load(self):
        crm = crm_with([
            {"id": "r1", "role": "rep", "capacity": 5},
            {"id": "r2", "role": "rep", "capacity": 5},
        ])
        crm.add_lead("a@acme.com", "A", "web", "r2")
        crm.add_lead("b@acme.com", "B", "web", "r2")
        crm.add_lead("c@acme.com", "C", "web", "r2")
        # L1 -> r1 (tie, smaller id), L2 -> r2 (r1 has 1, r2 has 0),
        # L3 -> r1 (tie again at load 1)
        self.assertEqual([crm.leads[i]["owner"] for i in ["L1", "L2", "L3"]],
                         ["r1", "r2", "r1"])

    def test_ties_broken_by_smallest_id_string(self):
        crm = crm_with([
            {"id": "zoe", "role": "rep", "capacity": 3},
            {"id": "amy", "role": "rep", "capacity": 3},
            {"id": "mia", "role": "rep", "capacity": 3},
        ])
        for i in range(3):
            crm.add_lead("u%d@acme.com" % i, "N", "web", "amy")
        self.assertEqual([crm.leads[i]["owner"] for i in ["L1", "L2", "L3"]],
                         ["amy", "mia", "zoe"])

    def test_manager_never_owns(self):
        crm = crm_with([{"id": "m1", "role": "manager", "capacity": 10}])
        crm.add_lead("a@acme.com", "A", "web", "m1")
        self.assertIsNone(crm.leads["L1"]["owner"])

    def test_rep_with_zero_capacity_never_owns(self):
        crm = crm_with([{"id": "r1", "role": "rep", "capacity": 0}])
        crm.add_lead("a@acme.com", "A", "web", "r1")
        self.assertIsNone(crm.leads["L1"]["owner"])


class TestWaitingQueue(unittest.TestCase):
    def test_lead_waits_when_everyone_is_full(self):
        crm = crm_with(REPS)
        crm.add_lead("a@acme.com", "A", "web", "m1")   # r1 (cap 1)
        crm.add_lead("b@acme.com", "B", "web", "m1")   # r2
        crm.add_lead("c@acme.com", "C", "web", "m1")   # r2
        crm.add_lead("d@acme.com", "D", "web", "m1")   # nobody
        self.assertIsNone(crm.leads["L4"]["owner"])
        self.assertEqual(len(crm.leads), 4)
        self.assertEqual(crm.log[-1], ("add_lead", "L4", "m1"))

    def test_no_assign_until_a_slot_frees(self):
        crm = crm_with(REPS)
        for i in range(4):
            crm.add_lead("u%d@acme.com" % i, "N", "web", "m1")
        self.assertIsNone(crm.leads["L4"]["owner"])
        self.assertNotIn("assign", [entry[0] for entry in crm.log])

    def test_winning_frees_slot_and_assigns_oldest_fifo(self):
        crm = crm_with([{"id": "r1", "role": "rep", "capacity": 2},
                        {"id": "m1", "role": "manager", "capacity": 2}])
        for i in range(4):
            crm.add_lead("u%d@acme.com" % i, "N", "referral", "m1")
        self.assertEqual(crm.leads["L1"]["owner"], "r1")
        self.assertEqual(crm.leads["L2"]["owner"], "r1")
        self.assertIsNone(crm.leads["L3"]["owner"])
        self.assertIsNone(crm.leads["L4"]["owner"])

        crm.qualify("L1", "m1")
        opp_id = crm.convert("L1", 1000, "m1")
        # convert empties r1's slot but the spec only frees slots on win/loss
        self.assertIsNone(crm.leads["L3"]["owner"])
        self.assertEqual(opp_id, "O1")

        crm.advance(opp_id, "proposal", "m1")
        crm.advance(opp_id, "negotiation", "m1")
        crm.advance(opp_id, "won", "m1")

        self.assertEqual(crm.leads["L3"]["owner"], "r1")  # oldest waiting
        self.assertEqual(crm.leads["L3"]["status"], "new")
        self.assertIsNone(crm.leads["L4"]["owner"])
        self.assertEqual(crm.log[-2:], [
            ("advance", "O1", "m1"),
            ("assign", "L3", "system"),
        ])

    def test_losing_also_frees_slot(self):
        crm = crm_with([{"id": "r1", "role": "rep", "capacity": 1},
                        {"id": "m1", "role": "manager", "capacity": 1}])
        crm.add_lead("a@acme.com", "A", "referral", "m1")
        crm.add_lead("b@acme.com", "B", "web", "m1")
        crm.qualify("L1", "m1")
        opp_id = crm.convert("L1", 500, "m1")
        crm.advance(opp_id, "lost", "m1")
        self.assertEqual(crm.leads["L2"]["owner"], "r1")
        self.assertIn(("assign", "L2", "system"), crm.log)

    def test_queue_is_drained_fifo_one_slot_per_closed_deal(self):
        crm = crm_with([{"id": "r1", "role": "rep", "capacity": 3},
                        {"id": "m1", "role": "manager", "capacity": 3}])
        for i in range(5):
            crm.add_lead("u%d@acme.com" % i, "N", "referral", "m1")
        self.assertEqual([crm.leads[i]["owner"] for i in ["L1", "L2", "L3"]],
                         ["r1", "r1", "r1"])
        self.assertIsNone(crm.leads["L4"]["owner"])
        self.assertIsNone(crm.leads["L5"]["owner"])

        crm.qualify("L1", "m1")
        opp1 = crm.convert("L1", 100, "m1")
        crm.qualify("L2", "m1")
        opp2 = crm.convert("L2", 100, "m1")

        crm.advance(opp1, "proposal", "m1")
        crm.advance(opp1, "negotiation", "m1")
        crm.advance(opp1, "won", "m1")
        self.assertEqual(crm.leads["L4"]["owner"], "r1")
        self.assertIsNone(crm.leads["L5"]["owner"])

        crm.advance(opp2, "lost", "m1")
        self.assertEqual(crm.leads["L5"]["owner"], "r1")

        assigns = [e for e in crm.log if e[0] == "assign"]
        self.assertEqual(assigns, [("assign", "L4", "system"),
                                   ("assign", "L5", "system")])

    def test_qualify_by_manager_of_unowned_lead(self):
        crm = crm_with([{"id": "r1", "role": "rep", "capacity": 1},
                        {"id": "m1", "role": "manager", "capacity": 1}])
        crm.add_lead("a@acme.com", "A", "referral", "m1")
        crm.add_lead("b@acme.com", "B", "referral", "m1")
        crm.qualify("L2", "m1")  # manager may qualify a queued lead
        self.assertEqual(crm.leads["L2"]["status"], "qualified")
        self.assertIsNone(crm.leads["L2"]["owner"])
        self.assertEqual(crm.log[-1], ("qualify", "L2", "m1"))


class TestLoadDefinition(unittest.TestCase):
    def build(self):
        crm = crm_with([{"id": "r1", "role": "rep", "capacity": 9},
                        {"id": "m1", "role": "manager", "capacity": 9}])
        return crm

    def test_new_and_qualified_leads_count(self):
        crm = self.build()
        crm.add_lead("a@acme.com", "A", "referral", "m1")
        crm.add_lead("b@acme.com", "B", "referral", "m1")
        crm.qualify("L1", "m1")
        self.assertEqual(load_of(crm, "r1"), 2)

    def test_converted_lead_no_longer_counts_but_opp_does(self):
        crm = self.build()
        crm.add_lead("a@acme.com", "A", "referral", "m1")
        crm.qualify("L1", "m1")
        opp = crm.convert("L1", 100, "m1")
        self.assertEqual(load_of(crm, "r1"), 1)
        crm.advance(opp, "proposal", "m1")
        crm.advance(opp, "negotiation", "m1")
        crm.advance(opp, "won", "m1")
        self.assertEqual(load_of(crm, "r1"), 0)

    def test_lost_opp_does_not_count(self):
        crm = self.build()
        crm.add_lead("a@acme.com", "A", "referral", "m1")
        crm.qualify("L1", "m1")
        opp = crm.convert("L1", 100, "m1")
        crm.advance(opp, "lost", "m1")
        self.assertEqual(load_of(crm, "r1"), 0)

    def test_capacity_gate_uses_open_work(self):
        # r1 capacity 1: a converted lead's opportunity still blocks it
        crm = crm_with([{"id": "r1", "role": "rep", "capacity": 1},
                        {"id": "m1", "role": "manager", "capacity": 1}])
        crm.add_lead("a@acme.com", "A", "referral", "m1")
        crm.qualify("L1", "m1")
        crm.convert("L1", 100, "m1")
        crm.add_lead("b@acme.com", "B", "web", "m1")
        self.assertEqual(crm.leads["L1"]["owner"], "r1")
        self.assertIsNone(crm.leads["L2"]["owner"])


if __name__ == "__main__":
    unittest.main()
