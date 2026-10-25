"""Unit tests for CRM.qualify and CRM.convert."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crm_test_support import add_lead, convert_lead, make_crm  # noqa: E402


class QualifyTests(unittest.TestCase):
    def test_happy_path_sets_qualified_and_logs(self):
        crm = make_crm()
        lead_id = add_lead(crm, 0)
        crm.qualify(lead_id, "r1")
        self.assertEqual(crm.leads[lead_id]["status"], "qualified")
        self.assertEqual(
            crm.log,
            [("add_lead", lead_id, "m1"), ("qualify", lead_id, "r1")],
        )

    def test_manager_may_qualify_any_lead(self):
        crm = make_crm()
        lead_id = add_lead(crm, 0)   # owned by r1
        crm.qualify(lead_id, "m1")
        self.assertEqual(crm.leads[lead_id]["status"], "qualified")
        self.assertEqual(crm.log[-1], ("qualify", lead_id, "m1"))

    def test_unknown_actor_checked_first(self):
        crm = make_crm()
        for actor in ("ghost", None, 3, ""):
            with self.subTest(actor=actor):
                with self.assertRaises(PermissionError):
                    crm.qualify("L404", actor)
        self.assertEqual(crm.log, [])

    def test_unknown_lead_raises_value_error_after_actor_check(self):
        crm = make_crm()
        with self.assertRaises(ValueError):
            crm.qualify("L404", "m1")
        with self.assertRaises(ValueError):
            crm.qualify("L404", "r2")  # known actor, missing lead
        self.assertEqual(crm.log, [])

    def test_other_rep_is_not_owner_and_gets_permission_error(self):
        crm = make_crm()
        lead_id = add_lead(crm, 0)   # owned by r1
        with self.assertRaises(PermissionError):
            crm.qualify(lead_id, "r2")
        self.assertEqual(crm.leads[lead_id]["status"], "new")
        self.assertEqual(crm.log, [("add_lead", lead_id, "m1")])

    def test_only_a_new_lead_may_be_qualified(self):
        crm = make_crm()
        lead_id, _ = convert_lead(crm, 0)
        log_before = list(crm.log)
        with self.assertRaises(ValueError):
            crm.qualify(lead_id, "r1")  # status is already "converted"
        self.assertEqual(crm.leads[lead_id]["status"], "converted")
        self.assertEqual(crm.log, log_before)

    def test_score_threshold_thirty_is_enforced(self):
        crm = make_crm()
        low = crm.add_lead("bob@gmail.com", "Bob", "web", "m1")           # score 10
        with self.assertRaises(ValueError):
            crm.qualify(low, "r1")   # score 10 owner r1
        self.assertEqual(crm.leads[low]["status"], "new")
        self.assertEqual([entry[0] for entry in crm.log], ["add_lead"])

        # referral on a common domain scores exactly 30.
        crm2 = make_crm()
        exactly = crm2.add_lead("ann@gmail.com", "Ann", "referral", "m1")
        crm2.qualify(exactly, "r1")
        self.assertEqual(crm2.leads[exactly]["status"], "qualified")


class ConvertTests(unittest.TestCase):
    def test_happy_path_creates_opportunity_and_logs(self):
        crm = make_crm()
        lead_id = add_lead(crm, 0)
        crm.qualify(lead_id, "r1")
        opp_id = crm.convert(lead_id, 1000, "r1")
        self.assertEqual(opp_id, "O1")
        opp = crm.opps["O1"]
        self.assertEqual(opp["id"], opp_id)
        self.assertEqual(opp["lead_id"], lead_id)
        self.assertEqual(opp["owner"], "r1")
        self.assertEqual(opp["amount"], 1000)
        self.assertEqual(opp["original_amount"], 1000)
        self.assertEqual(opp["stage"], "prospect")
        self.assertEqual(crm.leads[lead_id]["status"], "converted")
        self.assertEqual(
            crm.log,
            [
                ("add_lead", lead_id, "m1"),
                ("qualify", lead_id, "r1"),
                ("convert", opp_id, "r1"),
            ],
        )

    def test_manager_convert_sets_owner_to_the_lead_owner(self):
        crm = make_crm()
        lead_id = add_lead(crm, 0)            # owned by r1
        crm.qualify(lead_id, "m1")
        opp_id = crm.convert(lead_id, 500, "m1")
        self.assertEqual(crm.opps[opp_id]["owner"], "r1")
        lead2 = add_lead(crm, 1)              # owned by r2
        crm.qualify(lead2, "m1")
        opp2 = crm.convert(lead2, 300, "m1")
        self.assertEqual(crm.opps[opp2]["owner"], "r2")

    def test_unknown_actor_checked_first(self):
        crm = make_crm()
        for actor in ("ghost", 7, None):
            with self.subTest(actor=actor):
                with self.assertRaises(PermissionError):
                    crm.convert("L404", -5, actor)
        self.assertEqual(crm.log, [])

    def test_unknown_lead_raises_value_error(self):
        crm = make_crm()
        with self.assertRaises(ValueError):
            crm.convert("L404", 100, "m1")
        self.assertEqual(crm.log, [])

    def test_amount_must_be_a_positive_non_bool_int(self):
        crm = make_crm()
        lead_id = add_lead(crm, 0)
        crm.qualify(lead_id, "r1")     # qualified but not converted yet
        log_before = list(crm.log)
        for bad in (0, -1, -100, "100", 10.5, 2.0, True, False, None, [5]):
            with self.subTest(amount=bad):
                with self.assertRaises(ValueError):
                    crm.convert(lead_id, bad, "r1")
        self.assertEqual(crm.leads[lead_id]["status"], "qualified")
        self.assertEqual(crm.log, log_before)
        self.assertEqual(crm.opps, {})

    def test_amount_checked_before_permission(self):
        crm = make_crm()
        lead_id = add_lead(crm, 0)
        crm.qualify(lead_id, "r1")
        # r2 is a known user but not the owner; the bad amount fails first.
        with self.assertRaises(ValueError):
            crm.convert(lead_id, 0, "r2")
        self.assertEqual(
            [entry[0] for entry in crm.log], ["add_lead", "qualify"]
        )

    def test_non_owner_rep_gets_permission_error(self):
        crm = make_crm()
        lead_id = add_lead(crm, 0)
        crm.qualify(lead_id, "r1")
        with self.assertRaises(PermissionError):
            crm.convert(lead_id, 100, "r2")
        self.assertEqual(crm.opps, {})

    def test_requires_qualified_status(self):
        crm = make_crm()
        lead_id = add_lead(crm, 0)  # status "new"
        with self.assertRaises(ValueError):
            crm.convert(lead_id, 100, "r1")
        self.assertEqual(crm.leads[lead_id]["status"], "new")
        self.assertEqual(crm.opps, {})
        self.assertEqual([entry[0] for entry in crm.log], ["add_lead"])

    def test_requires_an_owner(self):
        # A lead that waited for a slot has no owner; it can still be
        # qualified by a manager, but converting it must fail (check 5).
        crm = make_crm([
            {"id": "r1", "role": "rep", "capacity": 0},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        lead_id = add_lead(crm, 0)
        self.assertIsNone(crm.leads[lead_id]["owner"])
        crm.qualify(lead_id, "m1")
        with self.assertRaises(ValueError):
            crm.convert(lead_id, 100, "m1")
        self.assertEqual(crm.leads[lead_id]["status"], "qualified")
        self.assertEqual(crm.opps, {})
        self.assertEqual([entry[0] for entry in crm.log], ["add_lead", "qualify"])

    def test_opportunity_ids_count_successful_conversions(self):
        crm = make_crm()
        lead1 = add_lead(crm, 0)
        crm.qualify(lead1, "r1")
        opp1 = crm.convert(lead1, 100, "r1")
        with self.assertRaises(ValueError):
            crm.convert(lead1, 100, "r1")  # failed: lead already converted
        lead2 = add_lead(crm, 1)
        crm.qualify(lead2, "m1")
        opp2 = crm.convert(lead2, 100, "r2")
        self.assertEqual((opp1, opp2), ("O1", "O2"))
        self.assertEqual([entry[0] for entry in crm.log],
                         ["add_lead", "qualify", "convert", "add_lead",
                          "qualify", "convert"])


if __name__ == "__main__":
    unittest.main()
