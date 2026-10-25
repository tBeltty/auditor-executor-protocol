"""Tests for CRM.qualify and CRM.convert."""

import unittest

from crm import DuplicateLeadError
from support import add, make_crm, snapshot


class TestQualify(unittest.TestCase):
    def test_happy_path_by_owner(self):
        crm = make_crm()
        l1 = add(crm, "a@b.com", source="referral")  # owner r1
        crm.qualify(l1, "r1")
        self.assertEqual(crm.leads[l1]["status"], "qualified")
        self.assertEqual(crm.log, [("add_lead", "L1", "m1"), ("qualify", "L1", "r1")])

    def test_happy_path_by_manager(self):
        crm = make_crm()
        l1 = add(crm, "a@b.com", source="event")  # score 35 with custom domain
        crm.qualify(l1, "m1")
        self.assertEqual(crm.leads[l1]["status"], "qualified")
        self.assertEqual(crm.log[-1], ("qualify", "L1", "m1"))

    def test_manager_can_qualify_a_queued_lead(self):
        reps = [{"id": "cap", "role": "rep", "capacity": 0},
                {"id": "m1", "role": "manager", "capacity": 0}]
        crm = make_crm(reps)
        l1 = add(crm, "a@b.com", source="referral")
        self.assertIsNone(crm.leads[l1]["owner"])
        crm.qualify(l1, "m1")
        self.assertEqual(crm.leads[l1]["status"], "qualified")

    def test_actor_check_runs_first(self):
        crm = make_crm()
        with self.assertRaises(PermissionError):
            crm.qualify("L404", "ghost")  # unknown actor beats missing lead

    def test_missing_lead_value_error(self):
        crm = make_crm()
        with self.assertRaises(ValueError):
            crm.qualify("L404", "m1")

    def test_not_owner_permission_error(self):
        crm = make_crm()
        l1 = add(crm, "a@b.com", source="referral")  # owner r1
        self.assertEqual(crm.leads[l1]["owner"], "r1")
        before = snapshot(crm)
        with self.assertRaises(PermissionError):
            crm.qualify(l1, "r2")
        self.assertEqual(snapshot(crm), before)

    def test_score_below_30_value_error(self):
        crm = make_crm()
        l1 = add(crm, "a@gmail.com", source="web")  # 10
        with self.assertRaises(ValueError):
            crm.qualify(l1, "r1")
        self.assertEqual(crm.leads[l1]["status"], "new")
        self.assertEqual(len(crm.log), 1)

    def test_score_exactly_30_qualifies(self):
        crm = make_crm()
        l1 = add(crm, "a@gmail.com", source="referral")  # 30, no bonus
        crm.qualify(l1, "r1")
        self.assertEqual(crm.leads[l1]["score"], 30)
        self.assertEqual(crm.leads[l1]["status"], "qualified")

    def test_event_with_bonus_35_qualifies(self):
        crm = make_crm()
        l1 = add(crm, "a@example.com", source="event")  # 20+15
        crm.qualify(l1, "r1")
        self.assertEqual(crm.leads[l1]["status"], "qualified")

    def test_double_qualify_value_error(self):
        crm = make_crm()
        l1 = add(crm, "a@b.com", source="referral")
        crm.qualify(l1, "r1")
        before = snapshot(crm)
        with self.assertRaises(ValueError):
            crm.qualify(l1, "r1")
        self.assertEqual(snapshot(crm), before)

    def test_status_check_rejects_converted_lead(self):
        # Both the status and score rules raise ValueError, so their relative
        # order is not observable; what must hold is that a lead that already
        # passed the score gate is still refused once it is no longer "new".
        crm = make_crm()
        l1 = add(crm, "a@gmail.com", source="web")  # new, score 10
        with self.assertRaises(ValueError):
            crm.qualify(l1, "r1")
        l2 = add(crm, "b@b.com", source="referral")
        crm.qualify(l2, "m1")
        crm.convert(l2, 500, "m1")
        with self.assertRaises(ValueError):
            crm.qualify(l2, "m1")
        self.assertEqual(crm.leads[l2]["status"], "converted")


    def test_failed_qualify_appends_nothing(self):
        crm = make_crm()
        l1 = add(crm, "a@gmail.com", source="web")
        before = snapshot(crm)
        with self.assertRaises(ValueError):
            crm.qualify(l1, "r1")
        self.assertEqual(snapshot(crm), before)


class TestConvert(unittest.TestCase):
    def test_happy_path_returns_opp_id_and_shapes_opportunity(self):
        crm = make_crm()
        l1 = add(crm, "a@b.com", source="referral")
        crm.qualify(l1, "r1")
        opp_id = crm.convert(l1, 1234, "r1")
        self.assertEqual(opp_id, "O1")
        self.assertEqual(
            crm.opps[opp_id],
            {
                "id": "O1",
                "lead_id": "L1",
                "owner": "r1",
                "amount": 1234,
                "original_amount": 1234,
                "stage": "prospect",
            },
        )
        self.assertEqual(crm.leads[l1]["status"], "converted")
        self.assertEqual(crm.log[-1], ("convert", "O1", "r1"))

    def test_opp_id_counter_independent_and_counts_successes_only(self):
        crm = make_crm()
        l1 = add(crm, "a@b.com", source="referral")
        self.assertEqual(crm.leads[l1]["owner"], "r1")
        crm.qualify(l1, "r1")
        with self.assertRaises(ValueError):
            crm.convert(l1, 0, "r1")  # amount not positive
        with self.assertRaises(ValueError):
            crm.convert("L404", 5, "r1")
        self.assertEqual(crm.convert(l1, 5, "r1"), "O1")
        # L2 routes to r2 (r1 is now busy with open O1, r2 load 0 < 1)
        l2 = add(crm, "c@d.com", source="referral")
        self.assertEqual(crm.leads[l2]["owner"], "r2")
        crm.qualify(l2, "m1")
        self.assertEqual(crm.convert(l2, 7, "m1"), "O2")
        self.assertEqual(crm.log[-1], ("convert", "O2", "m1"))
        self.assertEqual([e[0] for e in crm.log], ["add_lead", "qualify", "convert", "add_lead", "qualify", "convert"])



    def test_actor_check_first(self):
        crm = make_crm()
        l1 = add(crm, "a@b.com", source="referral")
        crm.qualify(l1, "r1")
        with self.assertRaises(PermissionError):
            crm.convert(l1, "bad-amount", "ghost")  # not even an int amount

    def test_missing_lead_value_error(self):
        crm = make_crm()
        with self.assertRaises(ValueError):
            crm.convert("L404", 100, "m1")

    def test_amount_must_be_positive_int_not_bool(self):
        crm = make_crm()
        l1 = add(crm, "a@b.com", source="referral")
        crm.qualify(l1, "r1")
        for bad in (0, -1, True, False, 1.0, 1500.5, "100", None):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    crm.convert(l1, bad, "r1")
        self.assertEqual(crm.opps, {})
        self.assertEqual(crm.leads[l1]["status"], "qualified")

    def test_amount_check_runs_before_permission_check(self):
        # other rep + bad amount -> ValueError (amount check #2 precedes permission #3)
        crm = make_crm()
        l1 = add(crm, "a@b.com", source="referral")  # owner r1
        crm.qualify(l1, "m1")
        with self.assertRaises(ValueError):
            crm.convert(l1, -5, "r2")

    def test_permission_check_runs_before_status_check(self):
        # new lead (not qualified) touched by wrong actor -> PermissionError first
        crm = make_crm()
        l1 = add(crm, "a@b.com", source="referral")
        with self.assertRaises(PermissionError):
            crm.convert(l1, 100, "r2")

    def test_status_must_be_qualified(self):
        crm = make_crm()
        l1 = add(crm, "a@b.com", source="referral")  # status new
        with self.assertRaises(ValueError):
            crm.convert(l1, 100, "r1")
        crm.qualify(l1, "r1")
        crm.convert(l1, 100, "r1")
        with self.assertRaises(ValueError):
            crm.convert(l1, 100, "r1")  # already converted

    def test_ownerless_lead_value_error(self):
        reps = [{"id": "cap0", "role": "rep", "capacity": 0},
                {"id": "m1", "role": "manager", "capacity": 0}]
        crm = make_crm(reps)
        l1 = add(crm, "a@b.com", source="referral")
        crm.qualify(l1, "m1")
        self.assertIsNone(crm.leads[l1]["owner"])
        before = snapshot(crm)
        with self.assertRaises(ValueError):
            crm.convert(l1, 100, "m1")
        self.assertEqual(snapshot(crm), before)

    def test_failed_convert_leaves_no_trace(self):
        crm = make_crm()
        l1 = add(crm, "a@b.com", source="referral")
        before = snapshot(crm)
        with self.assertRaises(ValueError):
            crm.convert(l1, 100, "m1")  # not qualified yet
        self.assertEqual(snapshot(crm), before)

    def test_convert_by_manager_keeps_rep_owner(self):
        crm = make_crm()
        l1 = add(crm, "a@b.com", source="referral")  # owner r1
        crm.qualify(l1, "r1")
        opp_id = crm.convert(l1, 900, "m1")
        self.assertEqual(crm.opps[opp_id]["owner"], "r1")
        self.assertEqual(crm.log[-1], ("convert", "O1", "m1"))

    def test_lead_id_reuse_is_guarded_by_duplicate_error(self):
        # sanity: duplicates never consume ids, conversions never re-run
        crm = make_crm()
        l1 = add(crm, "a@b.com", source="referral")
        with self.assertRaises(DuplicateLeadError):
            add(crm, "A@B.COM", source="referral")
        crm.qualify(l1, "r1")
        self.assertEqual(crm.convert(l1, 10, "r1"), "O1")


if __name__ == "__main__":
    unittest.main()
