"""Tests for work routing: load-based assignment, ties, capacity and the queue."""

import copy
import unittest

from crm import CRM

REPS_TWO = [
    {"id": "r1", "role": "rep", "capacity": 2},
    {"id": "r2", "role": "rep", "capacity": 1},
    {"id": "r3", "role": "rep", "capacity": 0},
    {"id": "m1", "role": "manager", "capacity": 9},
]


def build(reps):
    return CRM(copy.deepcopy(reps))


def lead_email(n):
    return "lead%d@acme.com" % n


class RoutingTest(unittest.TestCase):
    def test_lowest_load_and_capacity_are_respected(self):
        crm = build(REPS_TWO)
        owners = [crm.add_lead(lead_email(n), "N", "web", "m1") for n in range(1, 6)]
        self.assertEqual(
            [crm.leads[lead]["owner"] for lead in owners],
            ["r1", "r2", "r1", None, None],
        )

    def test_ties_broken_by_smallest_id_string_order(self):
        crm = build([
            {"id": "r10", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 1},
        ])
        first = crm.add_lead(lead_email(1), "N", "web", "r10")
        self.assertEqual(crm.leads[first]["owner"], "r10")  # "r10" < "r2" as strings
        second = crm.add_lead(lead_email(2), "N", "web", "r10")
        self.assertEqual(crm.leads[second]["owner"], "r2")  # r10 is now at capacity

    def test_lowest_load_beats_smallest_id(self):
        crm = build([
            {"id": "a1", "role": "rep", "capacity": 5},
            {"id": "z9", "role": "rep", "capacity": 5},
        ])
        crm.add_lead(lead_email(1), "N", "web", "a1")  # -> a1 (tie on load 0)
        second = crm.add_lead(lead_email(2), "N", "web", "a1")
        self.assertEqual(crm.leads[second]["owner"], "z9")  # z9 has the lower load

    def test_managers_never_own_leads(self):
        crm = build([{"id": "m1", "role": "manager", "capacity": 10}])
        lead = crm.add_lead(lead_email(1), "N", "web", "m1")
        self.assertIsNone(crm.leads[lead]["owner"])

    def test_no_reps_at_all_queues_everything(self):
        crm = build([{"id": "m1", "role": "manager", "capacity": 0}])
        for n in range(1, 4):
            self.assertIsNone(crm.leads[crm.add_lead(lead_email(n), "N", "web", "m1")]["owner"])

    def test_queue_join_logs_only_add_lead(self):
        crm = build([{"id": "r1", "role": "rep", "capacity": 1}])
        crm.add_lead(lead_email(1), "N", "web", "r1")
        crm.add_lead(lead_email(2), "N", "web", "r1")
        self.assertEqual(crm.log, [("add_lead", "L1", "r1"), ("add_lead", "L2", "r1")])

    def test_rep_with_zero_capacity_is_skipped(self):
        crm = build([
            {"id": "a0", "role": "rep", "capacity": 0},
            {"id": "b1", "role": "rep", "capacity": 1},
        ])
        lead = crm.add_lead(lead_email(1), "N", "web", "b1")
        self.assertEqual(crm.leads[lead]["owner"], "b1")


class LoadDefinitionTest(unittest.TestCase):
    """Load = owned new/qualified leads + owned opportunities in an open stage."""

    def single_rep_crm(self, capacity=1):
        return build([
            {"id": "r1", "role": "rep", "capacity": capacity},
            {"id": "m1", "role": "manager", "capacity": 9},
        ])

    def test_new_lead_counts(self):
        crm = self.single_rep_crm()
        crm.add_lead(lead_email(1), "N", "web", "m1")
        queued = crm.add_lead(lead_email(2), "N", "web", "m1")
        self.assertIsNone(crm.leads[queued]["owner"])

    def test_qualified_lead_still_counts(self):
        crm = self.single_rep_crm()
        lead = crm.add_lead(lead_email(1), "N", "referral", "m1")
        crm.qualify(lead, "r1")
        queued = crm.add_lead(lead_email(2), "N", "web", "m1")
        self.assertIsNone(crm.leads[queued]["owner"])

    def test_conversion_is_load_neutral(self):
        crm = self.single_rep_crm()
        lead = crm.add_lead(lead_email(1), "N", "referral", "m1")
        crm.qualify(lead, "r1")
        crm.convert(lead, 1000, "r1")
        queued = crm.add_lead(lead_email(2), "N", "web", "m1")
        self.assertIsNone(crm.leads[queued]["owner"])

    def test_non_final_stages_keep_the_slot(self):
        crm = self.single_rep_crm()
        lead = crm.add_lead(lead_email(1), "N", "referral", "m1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 1000, "r1")
        for stage in ("proposal", "negotiation"):
            crm.advance(opp, stage, "r1")
        queued = crm.add_lead(lead_email(2), "N", "web", "m1")
        self.assertIsNone(crm.leads[queued]["owner"])

    def test_discount_does_not_free_a_slot(self):
        crm = self.single_rep_crm()
        lead = crm.add_lead(lead_email(1), "N", "referral", "m1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 1000, "r1")
        crm.discount(opp, 5, "r1")
        queued = crm.add_lead(lead_email(2), "N", "web", "m1")
        self.assertIsNone(crm.leads[queued]["owner"])

    def test_lost_frees_the_slot(self):
        crm = self.single_rep_crm()
        lead = crm.add_lead(lead_email(1), "N", "referral", "m1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 1000, "r1")
        crm.advance(opp, "lost", "r1")
        free = crm.add_lead(lead_email(2), "N", "web", "m1")
        self.assertEqual(crm.leads[free]["owner"], "r1")

    def test_load_moves_with_ownership(self):
        crm = build([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 9},
        ])
        lead = crm.add_lead(lead_email(1), "N", "referral", "m1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 1000, "r1")
        crm.transfer(opp, "r2", "m1")
        next_lead = crm.add_lead(lead_email(2), "N", "web", "m1")
        self.assertEqual(crm.leads[next_lead]["owner"], "r1")

    def test_other_reps_load_is_not_affected(self):
        crm = build([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 1},
        ])
        crm.add_lead(lead_email(1), "N", "web", "r1")
        won_lead = crm.add_lead(lead_email(2), "N", "referral", "r2")
        crm.qualify(won_lead, "r2")
        opp = crm.convert(won_lead, 100, "r2")
        crm.advance(opp, "lost", "r2")
        # r2 has a free slot again, r1 still owns its lead
        third = crm.add_lead(lead_email(3), "N", "web", "r1")
        self.assertEqual(crm.leads[third]["owner"], "r2")


class SlotFillingTest(unittest.TestCase):
    def setUp(self):
        self.crm = build([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 5},
        ])

    def owned_opp(self, email_n=1, owner="r1", amount=1000):
        lead = self.crm.add_lead(lead_email(email_n), "A", "referral", "m1")
        self.crm.qualify(lead, owner)
        return lead, self.crm.convert(lead, amount, owner)

    def test_win_walks_through_stages_and_assigns_oldest_waiting_lead(self):
        _, opp = self.owned_opp()
        queued = [self.crm.add_lead(lead_email(n), "Q", "web", "m1") for n in (2, 3)]
        self.assertEqual([self.crm.leads[l]["owner"] for l in queued], [None, None])
        self.crm.log.clear()
        for stage in ("proposal", "negotiation", "won"):
            self.crm.advance(opp, stage, "r1")
        self.assertEqual(
            self.crm.log,
            [
                ("advance", "O1", "r1"),
                ("advance", "O1", "r1"),
                ("advance", "O1", "r1"),
                ("assign", "L2", "system"),
            ],
        )
        self.assertEqual(self.crm.leads["L2"]["owner"], "r1")
        self.assertEqual(self.crm.leads["L2"]["status"], "new")
        self.assertIsNone(self.crm.leads["L3"]["owner"])

    def test_lost_also_frees_the_slot(self):
        _, opp = self.owned_opp()
        self.crm.add_lead(lead_email(2), "B", "web", "m1")
        self.crm.log.clear()
        self.crm.advance(opp, "lost", "r1")
        self.assertEqual(self.crm.log, [("advance", "O1", "r1"), ("assign", "L2", "system")])

    def test_non_final_advance_does_not_assign(self):
        _, opp = self.owned_opp()
        self.crm.add_lead(lead_email(2), "B", "web", "m1")
        self.crm.log.clear()
        self.crm.advance(opp, "proposal", "r1")
        self.assertEqual(self.crm.log, [("advance", "O1", "r1")])

    def test_failed_advance_does_not_assign(self):
        _, opp = self.owned_opp()
        self.crm.add_lead(lead_email(2), "B", "web", "m1")
        self.crm.log.clear()
        with self.assertRaises(ValueError):
            self.crm.advance(opp, "won", "r1")  # prospect -> won skips negotiation
        self.assertEqual(self.crm.log, [])
        self.assertIsNone(self.crm.leads["L2"]["owner"])

    def test_convert_does_not_fill_the_queue(self):
        lead = self.crm.add_lead(lead_email(1), "A", "referral", "m1")
        self.crm.qualify(lead, "r1")
        self.crm.add_lead(lead_email(2), "B", "web", "m1")
        self.crm.log.clear()
        self.crm.convert(lead, 1000, "r1")  # frees a lead slot, costs an opp slot
        self.assertEqual(self.crm.log, [("convert", "O1", "r1")])
        self.assertIsNone(self.crm.leads["L2"]["owner"])

    def test_queue_is_fifo_across_multiple_closures(self):
        crm = build([
            {"id": "r1", "role": "rep", "capacity": 2},
            {"id": "m1", "role": "manager", "capacity": 5},
        ])
        owned = [crm.add_lead(lead_email(n), "N", "referral", "m1") for n in (1, 2)]
        waiting = [crm.add_lead(lead_email(n), "N", "event", "m1") for n in (3, 4)]
        opps = []
        for lead in owned:
            crm.qualify(lead, "m1")
            opps.append(crm.convert(lead, 1000, "m1"))
        crm.log.clear()
        crm.advance(opps[0], "lost", "m1")
        self.assertEqual(crm.log[-1], ("assign", waiting[0], "system"))
        crm.advance(opps[1], "lost", "m1")
        self.assertEqual(crm.log[-1], ("assign", waiting[1], "system"))
        self.assertEqual(crm.leads[waiting[0]]["owner"], "r1")
        self.assertEqual(crm.leads[waiting[1]]["owner"], "r1")
        # Both slots are used again, so a further closure assigns nobody.
        crm.qualify(waiting[0], "m1")
        crm.convert(waiting[0], 1000, "m1")
        before = len(crm.log)
        crm.advance("O3", "lost", "m1")
        self.assertEqual(len(crm.log), before + 1)
        self.assertEqual([entry for entry in crm.log if entry[0] == "assign"],
                         [("assign", "L3", "system"), ("assign", "L4", "system")])

    def test_only_the_freed_rep_is_filled(self):
        crm = build([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 5},
        ])
        first = crm.add_lead(lead_email(1), "A", "referral", "m1")   # r1, load 45
        second = crm.add_lead(lead_email(2), "B", "referral", "m1")  # r2
        crm.qualify(first, "r1")
        opp = crm.convert(first, 1000, "r1")
        waiting = [crm.add_lead(lead_email(n), "W", "web", "m1") for n in (3, 4)]
        self.assertEqual([crm.leads[l]["owner"] for l in waiting], [None, None])
        self.assertEqual(crm.leads[second]["owner"], "r2")
        crm.log.clear()
        crm.advance(opp, "lost", "r1")
        self.assertEqual(crm.log, [("advance", "O1", "r1"), ("assign", "L3", "system")])
        self.assertIsNone(crm.leads["L4"]["owner"])
        self.assertEqual(crm.leads["L2"]["owner"], "r2")

    def test_waiting_lead_id_numbers_are_not_reused(self):
        crm = build([{"id": "r1", "role": "rep", "capacity": 1}])
        for n in range(1, 4):
            self.assertEqual(crm.add_lead(lead_email(n), "N", "web", "r1"), "L%d" % n)

    def test_assigned_lead_keeps_qualified_status(self):
        crm = build([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 1},
        ])
        busy = crm.add_lead(lead_email(1), "A", "referral", "m1")
        crm.qualify(busy, "r1")
        opp = crm.convert(busy, 1000, "r1")
        queued = crm.add_lead(lead_email(2), "B", "referral", "m1")
        self.assertIsNone(crm.leads[queued]["owner"])
        # A manager may qualify an unowned lead while it waits.
        crm.qualify(queued, "m1")
        self.assertEqual(crm.leads[queued]["status"], "qualified")
        for stage in ("proposal", "negotiation", "won"):
            crm.advance(opp, stage, "m1")
        self.assertEqual(crm.leads[queued]["owner"], "r1")
        self.assertEqual(crm.leads[queued]["status"], "qualified")


if __name__ == "__main__":
    unittest.main()
