import unittest

from crm import CRM
from helpers import GuardChecks


class AssignmentTests(GuardChecks, unittest.TestCase):
    def test_lowest_load_wins_with_id_tie_break(self):
        crm = CRM([
            {"id": "r2", "role": "rep", "capacity": 5},
            {"id": "r1", "role": "rep", "capacity": 5},
        ])
        first = crm.add_lead("a@x.com", "A", "web", "r1")
        second = crm.add_lead("b@x.com", "B", "web", "r1")
        third = crm.add_lead("c@x.com", "C", "web", "r1")
        self.assertEqual(crm.leads[first]["owner"], "r1")
        self.assertEqual(crm.leads[second]["owner"], "r2")
        self.assertEqual(crm.leads[third]["owner"], "r1")

    def test_managers_never_own_work(self):
        crm = CRM([{"id": "m1", "role": "manager", "capacity": 10}])
        lead_id = crm.add_lead("a@x.com", "A", "web", "m1")
        self.assertIsNone(crm.leads[lead_id]["owner"])
        self.assertEqual(crm.waiting, [lead_id])

    def test_capacity_is_respected_and_queue_is_fifo(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1}])
        first = crm.add_lead("a@x.com", "A", "web", "r1")
        second = crm.add_lead("b@x.com", "B", "web", "r1")
        third = crm.add_lead("c@x.com", "C", "web", "r1")
        self.assertEqual(crm.leads[first]["owner"], "r1")
        self.assertIsNone(crm.leads[second]["owner"],
                          "CAPACITY_GUARD: a rep at capacity must not take more leads")
        self.assertEqual(crm.waiting, [second, third])

    def test_queue_released_when_slot_frees(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1}])
        first = crm.add_lead("a@x.com", "A", "referral", "r1")
        second = crm.add_lead("b@x.com", "B", "web", "r1")
        third = crm.add_lead("c@x.com", "C", "web", "r1")
        self.assertEqual(crm.waiting, [second, third])
        crm.qualify(first, "r1")
        opp = crm.convert(first, 1000, "r1")
        crm.advance(opp, "proposal", "r1")
        crm.advance(opp, "negotiation", "r1")
        crm.advance(opp, "won", "r1")
        self.assertEqual(crm.leads[second]["owner"], "r1",
                         "QUEUE_GUARD: oldest waiting lead must be assigned when a slot frees")
        self.assertEqual(crm.waiting, [third])

    def test_transfer_frees_a_slot(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 5},
            {"id": "m1", "role": "manager", "capacity": 5},
        ])
        first = crm.add_lead("a@x.com", "A", "referral", "r1")
        crm.qualify(first, "r1")
        opp = crm.convert(first, 1000, "r1")
        crm.transfer(opp, "r2", "m1")
        self.assertEqual(crm.opps[opp]["owner"], "r2")
        later = crm.add_lead("b@x.com", "B", "web", "r1")
        self.assertEqual(crm.leads[later]["owner"], "r1")


if __name__ == "__main__":
    unittest.main()
