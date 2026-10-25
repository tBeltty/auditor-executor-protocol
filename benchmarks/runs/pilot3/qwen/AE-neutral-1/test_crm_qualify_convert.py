"""Tests for CRM.qualify and CRM.convert: check order, states, atomicity."""
import unittest

from crm import CRM


REPS = [
    {"id": "r1", "role": "rep", "capacity": 1},
    {"id": "m1", "role": "manager", "capacity": 99},
]


class QualifyTest(unittest.TestCase):
    def setUp(self):
        self.crm = CRM([dict(r) for r in REPS])

    def _make(self, email="a@x.com", name="A", source="web"):
        return self.crm.add_lead(email, name, source, "m1")

    def test_unknown_actor_first(self):
        lid = self._make()
        with self.assertRaises(PermissionError):
            self.crm.qualify(lid, "ghost")
        with self.assertRaises(PermissionError):
            self.crm.qualify("L99", "ghost")  # unknown actor beats missing lead

    def test_missing_lead_value_error(self):
        with self.assertRaises(ValueError):
            self.crm.qualify("L42", "m1")

    def test_non_owner_rep_permission_before_status(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 2},
            {"id": "r2", "role": "rep", "capacity": 2},
            {"id": "m1", "role": "manager", "capacity": 99},
        ])
        lid = crm.add_lead("a@x.com", "A", "referral", "m1")  # owned by r1, score 45
        crm.qualify(lid, "r1")  # now status is qualified
        with self.assertRaises(PermissionError):  # step 2 before step 3
            crm.qualify(lid, "r2")

    def test_manager_can_qualify_any_lead(self):
        lid = self._make(source="referral")
        self.crm.qualify(lid, "m1")
        self.assertEqual(self.crm.leads[lid]["status"], "qualified")

    def test_already_qualified_value_error(self):
        lid = self._make(source="referral")
        self.crm.qualify(lid, "m1")
        with self.assertRaises(ValueError):
            self.crm.qualify(lid, "m1")

    def test_score_below_30_value_error(self):
        lid = self._make()  # web@x.com = 10 + 15 = 25
        with self.assertRaises(ValueError):
            self.crm.qualify(lid, "m1")
        self.assertEqual(self.crm.leads[lid]["status"], "new")
        self.assertEqual(self.crm.log, [("add_lead", lid, "m1")])

    def test_score_exactly_30_ok(self):
        lid = self._make(email="a@gmail.com", source="referral")  # 30, free domain
        self.crm.qualify(lid, "m1")
        self.assertEqual(self.crm.leads[lid]["status"], "qualified")
        self.assertEqual(self.crm.log[-1], ("qualify", lid, "m1"))

    def test_qualify_unowned_lead_owner_only_none_matches(self):
        crm = CRM([{"id": "m1", "role": "manager", "capacity": 5}])
        lid = crm.add_lead("a@x.com", "A", "referral", "m1")  # no reps -> queued
        crm.qualify(lid, "m1")  # manager passes
        self.assertEqual(crm.leads[lid]["status"], "qualified")


class ConvertTest(unittest.TestCase):
    def setUp(self):
        self.crm = CRM([dict(r) for r in REPS])
        self.lid = None

    def _qualified(self):
        self.lid = self.crm.add_lead("a@x.com", "A", "referral", "m1")
        self.crm.qualify(self.lid, "r1")
        return self.lid

    def test_unknown_actor_first(self):
        lid = self._qualified()
        with self.assertRaises(PermissionError):
            self.crm.convert(lid, "bad-amount", "ghost")

    def test_missing_lead(self):
        with self.assertRaises(ValueError):
            self.crm.convert("L7", 100, "m1")

    def test_amount_validation_before_actor(self):
        crm2 = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 9},
        ])
        lid2 = crm2.add_lead("a@x.com", "A", "referral", "m1")  # -> r1
        crm2.qualify(lid2, "r1")
        # r2 is a known non-owner rep -> bad amount (ValueError, step 2)
        # must fire before the owner check (PermissionError, step 3)
        with self.assertRaises(ValueError):
            crm2.convert(lid2, 100.0, "r2")
        with self.assertRaises(ValueError):
            crm2.convert(lid2, True, "r1")
        with self.assertRaises(ValueError):
            crm2.convert(lid2, 0, "r1")
        with self.assertRaises(ValueError):
            crm2.convert(lid2, -5, "r1")
        with self.assertRaises(ValueError):
            crm2.convert(lid2, "100", "r1")

    def test_non_owner_permission_before_status(self):
        # step 3 (PermissionError) fires before step 4 (status ValueError)
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 2},
            {"id": "r2", "role": "rep", "capacity": 2},
            {"id": "m1", "role": "manager", "capacity": 9},
        ])
        lid = crm.add_lead("a@x.com", "A", "web", "m1")  # owned by r1, status new
        with self.assertRaises(PermissionError):
            crm.convert(lid, 100, "r2")

    def test_new_status_value_error(self):
        lid = self.crm.add_lead("a@x.com", "A", "referral", "m1")
        with self.assertRaises(ValueError):
            self.crm.convert(lid, 100, "m1")

    def test_unowned_qualified_lead_value_error(self):
        crm = CRM([{"id": "m1", "role": "manager", "capacity": 5}])
        lid = crm.add_lead("a@x.com", "A", "referral", "m1")
        crm.qualify(lid, "m1")  # owner None
        with self.assertRaises(ValueError):
            crm.convert(lid, 100, "m1")

    def test_success_builds_opportunity(self):
        lid = self._qualified()
        before = len(self.crm.log)
        oid = self.crm.convert(lid, 12345, "r1")
        self.assertEqual(oid, "O1")
        opp = self.crm.opps[oid]
        self.assertEqual(
            opp,
            {
                "id": "O1",
                "lead_id": lid,
                "owner": "r1",
                "amount": 12345,
                "original_amount": 12345,
                "stage": "prospect",
            },
        )
        self.assertEqual(self.crm.leads[lid]["status"], "converted")
        self.assertEqual(self.crm.log[before], ("convert", oid, "r1"))
        self.assertEqual(len(self.crm.log), before + 1)

    def test_failed_convert_changes_nothing(self):
        lid = self._qualified()
        log_before = list(self.crm.log)
        with self.assertRaises(ValueError):
            self.crm.convert(lid, True, "r1")
        self.assertEqual(self.crm.log, log_before)
        self.assertEqual(self.crm.opps, {})
        self.assertEqual(self.crm.leads[lid]["status"], "qualified")
        # counter not consumed: next success is O1
        self.assertEqual(self.crm.convert(lid, 10, "r1"), "O1")

    def test_convert_id_counter_and_second_conversion(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 2},
            {"id": "m1", "role": "manager", "capacity": 9},
        ])
        l1 = crm.add_lead("a@x.com", "A", "referral", "m1")
        crm.qualify(l1, "m1")
        o1 = crm.convert(l1, 100, "m1")
        l2 = crm.add_lead("b@y.com", "B", "event", "m1")  # -> r1, still below cap
        self.assertEqual(crm.leads[l2]["owner"], "r1")
        crm.qualify(l2, "m1")
        o2 = crm.convert(l2, 200, "m1")
        self.assertEqual((o1, o2), ("O1", "O2"))
        converts = [entry for entry in crm.log if entry[0] == "convert"]
        self.assertEqual(converts, [("convert", "O1", "m1"), ("convert", "O2", "m1")])


if __name__ == "__main__":
    unittest.main()
