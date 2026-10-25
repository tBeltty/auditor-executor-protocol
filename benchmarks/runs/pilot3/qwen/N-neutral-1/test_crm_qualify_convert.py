"""Tests for qualify and convert, including check ordering and atomicity."""

import unittest

from crm import CRM


def make_crm():
    return CRM([
        {"id": "r1", "role": "rep", "capacity": 2},
        {"id": "r2", "role": "rep", "capacity": 2},
        {"id": "m1", "role": "manager", "capacity": 5},
    ])


class TestQualify(unittest.TestCase):
    def test_owner_qualifies_own_lead(self):
        crm = make_crm()
        crm.add_lead("a@acme.com", "A", "referral", "m1")
        crm.qualify("L1", "r1")
        self.assertEqual(crm.leads["L1"]["status"], "qualified")
        self.assertEqual(crm.log, [("add_lead", "L1", "m1"),
                                   ("qualify", "L1", "r1")])

    def test_manager_can_qualify_any_lead(self):
        crm = make_crm()
        crm.add_lead("a@acme.com", "A", "referral", "m1")
        crm.qualify("L1", "m1")
        self.assertEqual(crm.leads["L1"]["status"], "qualified")

    def test_other_rep_forbidden(self):
        crm = make_crm()
        crm.add_lead("a@acme.com", "A", "referral", "m1")
        with self.assertRaises(PermissionError):
            crm.qualify("L1", "r2")
        self.assertEqual(crm.leads["L1"]["status"], "new")
        self.assertEqual(len(crm.log), 1)

    def test_unknown_lead_value_error(self):
        crm = make_crm()
        with self.assertRaises(ValueError):
            crm.qualify("L7", "m1")

    def test_existence_checked_before_permission(self):
        crm = make_crm()
        with self.assertRaises(ValueError):  # not PermissionError
            crm.qualify("L7", "r2")

    def test_low_score_rejected(self):
        crm = make_crm()
        crm.add_lead("a@gmail.com", "A", "web", "m1")      # score 10
        crm.add_lead("b@gmail.com", "B", "event", "m1")    # score 20
        for lid in ["L1", "L2"]:
            with self.assertRaises(ValueError):
                crm.qualify(lid, "m1")
            self.assertEqual(crm.leads[lid]["status"], "new")

    def test_score_threshold_30_inclusive(self):
        crm = make_crm()
        crm.add_lead("a@gmail.com", "A", "referral", "m1")  # 30 exactly
        self.assertEqual(crm.leads["L1"]["score"], 30)
        crm.qualify("L1", "m1")
        self.assertEqual(crm.leads["L1"]["status"], "qualified")

    def test_corporate_web_lead_can_qualify_after_bonus(self):
        crm = make_crm()
        crm.add_lead("a@acme.com", "A", "web", "m1")  # 10 + 15 = 25
        with self.assertRaises(ValueError):
            crm.qualify("L1", "m1")
        crm.add_lead("b@acme.com", "B", "event", "m1")  # 20 + 15 = 35
        crm.qualify("L2", "m1")
        self.assertEqual(crm.leads["L2"]["status"], "qualified")

    def test_double_qualify_rejected(self):
        crm = make_crm()
        crm.add_lead("a@acme.com", "A", "referral", "m1")
        crm.qualify("L1", "m1")
        with self.assertRaises(ValueError):
            crm.qualify("L1", "m1")
        self.assertEqual(crm.log.count(("qualify", "L1", "m1")), 1)

    def test_status_checks_after_permission(self):
        # r2 is not the owner of a converted lead: PermissionError (2) wins
        # over the status rule (3).
        crm = make_crm()
        crm.add_lead("a@acme.com", "A", "referral", "m1")
        crm.qualify("L1", "m1")
        with self.assertRaises(PermissionError):
            crm.qualify("L1", "r2")

    def test_failed_qualify_appends_nothing(self):
        crm = make_crm()
        crm.add_lead("a@gmail.com", "A", "web", "m1")
        before = list(crm.log)
        with self.assertRaises(ValueError):
            crm.qualify("L1", "m1")
        self.assertEqual(crm.log, before)


class TestConvert(unittest.TestCase):
    def qualified(self):
        crm = make_crm()
        crm.add_lead("a@acme.com", "A", "referral", "m1")
        crm.qualify("L1", "r1")
        return crm

    def test_returns_sequential_opp_ids(self):
        crm = self.qualified()
        self.assertEqual(crm.convert("L1", 1000, "r1"), "O1")
        self.assertEqual(len(crm.opps), 1)
        opp = crm.opps["O1"]
        self.assertEqual(sorted(opp.keys()),
                         ["amount", "id", "lead_id", "original_amount", "owner", "stage"])
        self.assertEqual(opp["id"], "O1")
        self.assertEqual(opp["lead_id"], "L1")
        self.assertEqual(opp["owner"], "r1")
        self.assertEqual(opp["amount"], 1000)
        self.assertEqual(opp["original_amount"], 1000)
        self.assertEqual(opp["stage"], "prospect")
        self.assertEqual(crm.leads["L1"]["status"], "converted")
        self.assertEqual(crm.log[-1], ("convert", "O1", "r1"))

    def test_second_conversion(self):
        crm = self.qualified()
        crm.convert("L1", 1000, "r1")
        crm.add_lead("b@acme.com", "B", "referral", "m1")
        crm.qualify("L2", "m1")  # manager qualifies regardless of ownership
        self.assertEqual(crm.convert("L2", 2000, "m1"), "O2")
        self.assertEqual(sorted(crm.opps), ["O1", "O2"])

    def test_amount_validation(self):
        crm = self.qualified()
        for bad in [0, -1, -1000, True, False, 1.0, 100.5, "100", None, []]:
            with self.subTest(amount=bad):
                with self.assertRaises(ValueError):
                    crm.convert("L1", bad, "r1")
        self.assertEqual(crm.opps, {})
        self.assertEqual(len(crm.log), 2)

    def test_large_amount_int_ok(self):
        crm = self.qualified()
        self.assertEqual(crm.convert("L1", 10 ** 12, "r1"), "O1")

    def test_manager_may_convert(self):
        crm = self.qualified()
        self.assertEqual(crm.convert("L1", 500, "m1"), "O1")

    def test_non_owner_rep_forbidden(self):
        crm = self.qualified()
        with self.assertRaises(PermissionError):
            crm.convert("L1", 500, "r2")

    def test_unqualified_lead_rejected(self):
        crm = make_crm()
        crm.add_lead("a@acme.com", "A", "referral", "m1")
        with self.assertRaises(ValueError):
            crm.convert("L1", 500, "r1")
        self.assertEqual(crm.opps, {})

    def test_amount_checked_before_permission(self):
        crm = self.qualified()
        with self.assertRaises(ValueError):  # amount invalid -> rule 2 first
            crm.convert("L1", 0, "r2")

    def test_unknown_actor_checked_before_lead_existence(self):
        crm = self.qualified()
        with self.assertRaises(PermissionError):  # general rule comes first
            crm.convert("L9", -5, "ghost")

    def test_lead_existence_checked_before_amount(self):
        crm = self.qualified()
        with self.assertRaises(ValueError):
            crm.convert("L9", -5, "m1")

    def test_lead_without_owner_rejected(self):
        crm = CRM([{"id": "m1", "role": "manager", "capacity": 5}])
        crm.add_lead("a@acme.com", "A", "referral", "m1")
        self.assertIsNone(crm.leads["L1"]["owner"])
        crm.qualify("L1", "m1")
        with self.assertRaises(ValueError):
            crm.convert("L1", 500, "m1")
        self.assertEqual(crm.opps, {})
        self.assertEqual(crm.leads["L1"]["status"], "qualified")
        self.assertEqual(len(crm.log), 2)

    def test_converting_twice_rejected(self):
        crm = self.qualified()
        crm.convert("L1", 1000, "r1")
        with self.assertRaises(ValueError):
            crm.convert("L1", 1000, "r1")
        self.assertEqual(len(crm.opps), 1)
        self.assertEqual(len(crm.log), 3)

    def test_opp_id_not_consumed_on_failure(self):
        crm = self.qualified()
        with self.assertRaises(ValueError):
            crm.convert("L1", 0, "r1")
        self.assertEqual(crm.convert("L1", 700, "r1"), "O1")


if __name__ == "__main__":
    unittest.main()
