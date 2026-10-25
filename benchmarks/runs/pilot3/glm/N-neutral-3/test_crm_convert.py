"""Tests for CRM.convert: validation, permission, id sequence, side effects."""

import copy
import unittest

from crm import CRM


def make_crm():
    return CRM([
        {"id": "r1", "role": "rep", "capacity": 2},
        {"id": "r2", "role": "rep", "capacity": 2},
        {"id": "m1", "role": "manager", "capacity": 0},
    ])


def other_rep(owner):
    return "r2" if owner == "r1" else "r1"


class TestConvert(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        self.lead = self.crm.add_lead("h@acme.io", "H", "referral", "m1")  # r1
        self.crm.qualify(self.lead, "r1")

    def test_convert_fields_and_log(self):
        opp_id = self.crm.convert(self.lead, 1000, "r1")
        self.assertEqual(opp_id, "O1")
        opp = self.crm.opps[opp_id]
        self.assertEqual(opp, {
            "id": "O1",
            "lead_id": self.lead,
            "owner": "r1",
            "amount": 1000,
            "original_amount": 1000,
            "stage": "prospect",
        })
        self.assertEqual(self.crm.leads[self.lead]["status"], "converted")
        self.assertEqual(self.crm.log[-1], ("convert", "O1", "r1"))

    def test_convert_by_manager(self):
        opp_id = self.crm.convert(self.lead, 1000, "m1")
        self.assertEqual(self.crm.opps[opp_id]["owner"], "r1")
        self.assertEqual(self.crm.log[-1], ("convert", "O1", "m1"))

    def test_missing_lead(self):
        with self.assertRaises(ValueError):
            self.crm.convert("L99", 100, "r1")
        self.assertEqual(self.crm.opps, {})

    def test_unknown_actor_beats_everything(self):
        with self.assertRaises(PermissionError):
            self.crm.convert("L99", -1, "ghost")

    def test_amount_must_be_positive_int_not_bool(self):
        for bad in (0, -1, -100, 1.5, 10.0, "100", True, False, None):
            with self.assertRaises(ValueError):
                self.crm.convert(self.lead, bad, "r1")
        self.assertEqual(self.crm.opps, {})
        self.assertEqual(self.crm.leads[self.lead]["status"], "qualified")

    def test_bad_amount_beats_permission(self):
        with self.assertRaises(ValueError):
            self.crm.convert(self.lead, -1, "r2")

    def test_permission_owner_or_manager(self):
        with self.assertRaises(PermissionError):
            self.crm.convert(self.lead, 1000, "r2")
        self.assertEqual(self.crm.opps, {})

    def test_requires_qualified_status(self):
        fresh = self.crm.add_lead("f@acme.io", "F", "referral", "m1")
        owner = self.crm.leads[fresh]["owner"]
        with self.assertRaises(ValueError):
            self.crm.convert(fresh, 100, owner)  # still "new"
        self.assertEqual(self.crm.opps, {})

    def test_permission_check_before_status_check(self):
        fresh = self.crm.add_lead("f@acme.io", "F", "referral", "m1")
        owner = self.crm.leads[fresh]["owner"]
        with self.assertRaises(PermissionError):
            self.crm.convert(fresh, 100, other_rep(owner))

    def test_requires_owner(self):
        crm = CRM([{"id": "m1", "role": "manager", "capacity": 1}])
        lead = crm.add_lead("h@acme.io", "H", "referral", "m1")  # waiting
        self.assertIsNone(crm.leads[lead]["owner"])
        crm.qualify(lead, "m1")
        with self.assertRaises(ValueError):
            crm.convert(lead, 100, "m1")
        self.assertEqual(crm.opps, {})

    def test_status_check_before_owner_check(self):
        crm = CRM([{"id": "m1", "role": "manager", "capacity": 1}])
        lead = crm.add_lead("h@acme.io", "H", "referral", "m1")  # waiting, "new"
        with self.assertRaises(ValueError):  # not qualified (checked first)
            crm.convert(lead, 100, "m1")

    def test_opp_ids_count_successful_conversions(self):
        owner = self.crm.leads[self.lead]["owner"]
        o1 = self.crm.convert(self.lead, 100, owner)
        lead2 = self.crm.add_lead("h2@acme.io", "H2", "referral", "m1")
        owner2 = self.crm.leads[lead2]["owner"]
        self.crm.qualify(lead2, owner2)
        o2 = self.crm.convert(lead2, 100, owner2)
        self.assertEqual((o1, o2), ("O1", "O2"))
        with self.assertRaises(ValueError):  # failed conversion consumes no id
            self.crm.convert(lead2, 100, owner2)
        lead3 = self.crm.add_lead("h3@acme.io", "H3", "referral", "m1")
        owner3 = self.crm.leads[lead3]["owner"]
        self.crm.qualify(lead3, owner3)
        self.assertEqual(self.crm.convert(lead3, 100, owner3), "O3")

    def test_failed_convert_changes_nothing(self):
        before = (copy.deepcopy(self.crm.leads), copy.deepcopy(self.crm.opps),
                  copy.deepcopy(self.crm.log))
        with self.assertRaises(ValueError):
            self.crm.convert(self.lead, 0, "r1")
        with self.assertRaises(PermissionError):
            self.crm.convert(self.lead, 100, "r2")
        after = (copy.deepcopy(self.crm.leads), copy.deepcopy(self.crm.opps),
                 copy.deepcopy(self.crm.log))
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
