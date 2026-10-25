"""Tests for qualify/convert/advance/forecast pipeline and permissions."""

import unittest

from crm import CRM, DuplicateLeadError


def make_crm():
    return CRM([
        {"id": "r1", "role": "rep", "capacity": 3},
        {"id": "r2", "role": "rep", "capacity": 3},
        {"id": "m1", "role": "manager", "capacity": 0},
    ])


def funnel(crm, email="x@corp.io", source="referral", amount=1000):
    """add -> qualify -> convert using the lead's actual assigned owner."""
    lid = crm.add_lead(email, "Name", source, "m1")
    actor = crm.leads[lid]["owner"]
    crm.qualify(lid, actor)
    return lid, crm.convert(lid, amount, actor)


class QualifyConvert(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()

    def test_qualify_sad_path(self):
        lid = self.crm.add_lead("a@x.io", "A", "web", "r1")  # score 25
        with self.assertRaises(ValueError):  # unknown lead
            self.crm.qualify("L99", "r1")
        with self.assertRaises(PermissionError):
            self.crm.qualify(lid, "r2")
        with self.assertRaises(ValueError):  # score < 30
            self.crm.qualify(lid, "r1")
        self.crm.leads[lid]["status"] = "qualified"
        with self.assertRaises(ValueError):  # not "new" anymore
            self.crm.qualify(lid, "r1")

    def test_qualify_manager_or_owner(self):
        lid = self.crm.add_lead("a@x.io", "A", "referral", "r1")
        self.crm.qualify(lid, "m1")
        self.assertEqual(self.crm.leads[lid]["status"], "qualified")

    def test_convert_checks(self):
        lid = self.crm.add_lead("a@x.io", "A", "referral", "r1")
        with self.assertRaises(ValueError):
            self.crm.convert(lid, "big", "r1")  # not int
        with self.assertRaises(ValueError):
            self.crm.convert(lid, True, "r1")  # bool rejected
        with self.assertRaises(ValueError):
            self.crm.convert(lid, 0, "r1")  # not positive
        with self.assertRaises(ValueError):
            self.crm.convert(lid, 1000, "r1")  # not qualified yet
        self.crm.qualify(lid, "r1")
        with self.assertRaises(PermissionError):
            self.crm.convert(lid, 1000, "r2")
        oid = self.crm.convert(lid, 1000, "r1")
        with self.assertRaises(ValueError):  # not qualified anymore
            self.crm.convert(lid, 1000, "r1")

        opp = self.crm.opps[oid]
        self.assertEqual(opp["id"], oid)
        self.assertEqual(opp["lead_id"], lid)
        self.assertEqual(opp["owner"], "r1")
        self.assertEqual(opp["amount"], 1000)
        self.assertEqual(opp["original_amount"], 1000)
        self.assertEqual(opp["stage"], "prospect")
        self.assertEqual(self.crm.leads[lid]["status"], "converted")

    def test_convert_unowned_lead(self):
        self.crm.add_lead("a@x.io", "A", "web", "m1")
        for i in range(1, 7):
            self.crm.add_lead("l%d@x.io" % i, "L", "referral", "m1")
        # both capacity-3 reps fill first (r1, r2, r1, r2, r1, r2); 7th waits
        queued = self.crm.add_lead("zz@x.io", "Q", "referral", "m1")
        self.assertIsNone(self.crm.leads[queued]["owner"])
        self.crm.leads[queued]["status"] = "qualified"
        with self.assertRaises(ValueError):  # manager passes check 3, then no owner (check 5)
            self.crm.convert(queued, 100, "m1")

    def test_conversion_swaps_lead_for_opp_in_owner_load(self):
        lid1 = self.crm.add_lead("a@x.io", "A", "referral", "m1")
        self.assertEqual(self.crm._load("r1"), 1)
        self.crm.qualify(lid1, "r1")
        self.assertEqual(self.crm._load("r1"), 1)          # qualified still counts
        _, oid = funnel(self.crm, "b@x.io", "referral")    # owned by r2
        self.assertEqual(self.crm._load("r2"), 1)


class Advance(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        _, self.oid = funnel(self.crm)
        opp = self.crm.opps[self.oid]
        opp["amount"] = 60000  # force the manager-only negotiation branch in isolation

    def test_stage_path_validation(self):
        with self.assertRaises(ValueError):  # unknown opp
            self.crm.advance("O99", "proposal", "r1")
        with self.assertRaises(ValueError):  # invalid stage word
            self.crm.advance(self.oid, "closed", "r1")
        with self.assertRaises(PermissionError):  # not owner
            self.crm.advance(self.oid, "proposal", "r2")
        with self.assertRaises(ValueError):  # skipping a stage
            self.crm.advance(self.oid, "negotiation", "r1")
        self.crm.advance(self.oid, "proposal", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance(self.oid, "won", "r1")  # skips negotiation
        with self.assertRaises(ValueError):
            self.crm.advance(self.oid, "proposal", "r1")  # backwards

    def test_big_negotiation_needs_manager(self):
        self.crm.advance(self.oid, "proposal", "r1")
        with self.assertRaises(PermissionError):
            self.crm.advance(self.oid, "negotiation", "r1")  # 60000 > 50000
        self.crm.advance(self.oid, "negotiation", "m1")

    def test_small_negotiation_ok_for_rep(self):
        self.crm.opps[self.oid]["amount"] = 50000
        self.crm.advance(self.oid, "proposal", "r1")
        self.crm.advance(self.oid, "negotiation", "r1")

    def test_final_is_final(self):
        self.crm.advance(self.oid, "proposal", "r1")
        self.crm.opps[self.oid]["amount"] = 50000
        self.crm.advance(self.oid, "negotiation", "r1")
        self.crm.advance(self.oid, "won", "m1")
        with self.assertRaises(ValueError):
            self.crm.advance(self.oid, "lost", "r1")

    def test_log_entries(self):
        self.crm.advance(self.oid, "proposal", "r1")
        self.assertEqual(self.crm.log[-1], ("advance", self.oid, "r1"))


class Forecast(unittest.TestCase):
    def test_forecast_buckets(self):
        crm = make_crm()
        _, o1 = funnel(crm, "a@corp.io", amount=10_000)   # r1 owns; weighted 1000
        _, o2 = funnel(crm, "b@corp.io", "event", amount=7_000)    # r2 owns
        o2_owner = crm.opps[o2]["owner"]
        crm.advance(o2, "proposal", o2_owner)
        _, o3 = funnel(crm, "c@corp.io", "event", amount=7_000)    # r1 owns
        o3_owner = crm.opps[o3]["owner"]
        crm.advance(o3, "proposal", o3_owner)
        crm.advance(o3, "negotiation", o3_owner)
        crm.advance(o3, "won", "m1")
        result = crm.forecast()
        self.assertEqual(result["open"], 2)
        self.assertEqual(result["weighted"], 10_000 * 10 // 100 + 7_000 * 30 // 100)
        self.assertEqual(result["won"], 7_000)

    def test_forecast_no_interaction_logged(self):
        crm = make_crm()
        crm.add_lead("a@x.io", "A", "web", "r1")
        self.assertEqual(crm.forecast(), {"open": 0, "weighted": 0, "won": 0})


class WaitingQueueSlack(unittest.TestCase):
    def test_final_stage_frees_slot_and_assigns_oldest(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        lid1 = crm.add_lead("a@corp.io", "A", "referral", "m1")
        crm.add_lead("b@x.io", "B", "web", "m1")    # queued
        third = crm.add_lead("c@x.io", "C", "web", "m1")  # queued
        _, oid = funnel_test(crm, lid1)
        crm.advance(oid, "proposal", "r1")
        crm.advance(oid, "negotiation", "r1")  # small amounts: rep is fine
        crm.advance(oid, "won", "m1")
        # oldest waiting lead backfilled to r1 as a system log entry
        self.assertEqual(crm.leads[third]["owner"], None)  # third was added after b
        self.assertEqual(crm.leads[crm.leads["L2"]["id"]]["owner"], "r1")
        self.assertIn(("assign", "L2", "system"), crm.log)


def funnel_test(crm, lid, amount=1000):
    crm.qualify(lid, "r1")
    return lid, crm.convert(lid, amount, "r1")


if __name__ == "__main__":
    unittest.main()
