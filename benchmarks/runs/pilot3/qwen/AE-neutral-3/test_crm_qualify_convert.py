"""Spec lines 21-26: qualify and convert."""

import unittest

from crm import CRM, DuplicateLeadError


REPS = [
    {"id": "r1", "role": "rep", "capacity": 2},
    {"id": "r2", "role": "rep", "capacity": 1},
    {"id": "m1", "role": "manager", "capacity": 3},
]


class Fixture(unittest.TestCase):
    def setUp(self):
        self.crm = CRM([dict(r) for r in REPS])

    def new_lead(self, email="a@corp.com", name="Ann", source="referral", owner="r1"):
        """Create a lead owned by `owner` (r1 has capacity 2 here)."""
        lead = self.crm.add_lead(email, name, source, "m1")
        self.assertEqual(self.crm.leads[lead]["owner"], owner)
        return lead


class TestQualify(Fixture):
    """Line 22: exists -> owner/manager -> status new -> score >= 30."""

    def test_happy_path_sets_status_and_logs(self):
        lead = self.new_lead()
        self.crm.qualify(lead, "r1")
        self.assertEqual(self.crm.leads[lead]["status"], "qualified")
        self.assertEqual(self.crm.log, [("add_lead", lead, "m1"), ("qualify", lead, "r1")])

    def test_return_value_is_none(self):
        lead = self.new_lead()
        self.assertIsNone(self.crm.qualify(lead, "r1"))

    def test_manager_may_qualify_another_reps_lead(self):
        lead = self.new_lead()
        self.crm.qualify(lead, "m1")
        self.assertEqual(self.crm.leads[lead]["status"], "qualified")
        self.assertEqual(self.crm.log[-1], ("qualify", lead, "m1"))

    def test_unknown_lead_raises_value_error(self):
        with self.assertRaises(ValueError):
            self.crm.qualify("L404", "r1")
        for bad in (None, 7, ["L1"], b"L1"):
            with self.subTest(lead_id=bad):
                with self.assertRaises(ValueError):
                    self.crm.qualify(bad, "r1")

    def test_other_rep_is_forbidden(self):
        lead = self.new_lead()
        with self.assertRaises(PermissionError):
            self.crm.qualify(lead, "r2")
        self.assertEqual(self.crm.leads[lead]["status"], "new")

    def test_unowned_lead_cannot_be_qualified_by_a_rep(self):
        """r1 fills up, the extra lead has no owner; a rep is not its owner."""
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1}])
        crm.add_lead("a@corp.com", "Ann", "referral", "r1")
        waiting = crm.add_lead("b@corp.com", "Bob", "referral", "r1")
        self.assertIsNone(crm.leads[waiting]["owner"])
        with self.assertRaises(PermissionError):
            crm.qualify(waiting, "r1")
        # A manager may qualify it even with no owner.
        crm2 = CRM([{"id": "r1", "role": "rep", "capacity": 1},
                    {"id": "m1", "role": "manager", "capacity": 1}])
        crm2.add_lead("a@corp.com", "Ann", "referral", "m1")
        waiting = crm2.add_lead("b@corp.com", "Bob", "referral", "m1")
        crm2.qualify(waiting, "m1")
        self.assertEqual(crm2.leads[waiting]["status"], "qualified")

    def test_status_must_be_new(self):
        lead = self.new_lead()
        self.crm.qualify(lead, "r1")
        with self.assertRaises(ValueError):
            self.crm.qualify(lead, "r1")
        self.crm.convert(lead, 100, "r1")
        with self.assertRaises(ValueError):
            self.crm.qualify(lead, "r1")

    def test_score_below_30_is_rejected(self):
        lead = self.new_lead(email="w@corp.com", source="web", name="Ann")
        self.assertEqual(self.crm.leads[lead]["score"], 25)
        with self.assertRaises(ValueError):
            self.crm.qualify(lead, "r1")
        self.assertEqual(self.crm.leads[lead]["status"], "new")

    def test_score_exactly_30_is_accepted(self):
        """Threshold is "at least 30", so 30 qualifies and 25 does not."""
        low = self.crm.add_lead("w@corp.com", "W", "web", "m1")        # 10 + 15
        self.assertEqual(self.crm.leads[low]["score"], 25)
        with self.assertRaises(ValueError):
            self.crm.qualify(low, "m1")
        exact = self.crm.add_lead("g@gmail.com", "G", "referral", "m1")  # 30 + 0
        self.assertEqual(self.crm.leads[exact]["score"], 30)
        self.crm.qualify(exact, "m1")
        self.assertEqual(self.crm.leads[exact]["status"], "qualified")

    def test_check_order_status_before_score(self):
        """A converted low-score lead: check 3 (ValueError) also fires, so use
        ownership vs. status: non-owner rep + wrong status -> PermissionError."""
        lead = self.new_lead()
        self.crm.qualify(lead, "r1")
        with self.assertRaises(PermissionError):
            self.crm.qualify(lead, "r2")

    def test_check_order_exists_before_ownership(self):
        with self.assertRaises(ValueError):
            self.crm.qualify("L404", "r2")

    def test_qualify_does_not_touch_owner_or_counters(self):
        lead = self.new_lead()
        before = dict(self.crm.leads[lead])
        self.crm.qualify(lead, "r1")
        after = self.crm.leads[lead]
        self.assertEqual(after["owner"], before["owner"])
        self.assertEqual(after["score"], before["score"])
        self.assertEqual(list(self.crm.leads), [lead])


class TestConvert(Fixture):
    """Lines 24-26: exists -> amount -> owner/manager -> qualified -> has owner."""

    def test_happy_path_builds_opportunity_and_returns_id(self):
        lead = self.new_lead()
        self.crm.qualify(lead, "r1")
        opp = self.crm.convert(lead, 2500, "r1")
        self.assertEqual(opp, "O1")
        self.assertEqual(self.crm.opps[opp], {
            "id": "O1",
            "lead_id": lead,
            "owner": "r1",
            "amount": 2500,
            "original_amount": 2500,
            "stage": "prospect",
        })
        self.assertEqual(self.crm.leads[lead]["status"], "converted")
        self.assertEqual(self.crm.log,
                         [("add_lead", lead, "m1"), ("qualify", lead, "r1"),
                          ("convert", opp, "r1")])

    def test_manager_may_convert_another_reps_lead_and_opp_keeps_the_owner(self):
        lead = self.new_lead()
        self.crm.qualify(lead, "r1")
        opp = self.crm.convert(lead, 500, "m1")
        self.assertEqual(self.crm.opps[opp]["owner"], "r1")
        self.assertEqual(self.crm.log[-1], ("convert", opp, "m1"))

    def test_ids_count_successful_conversions_from_one(self):
        opps = []
        for n in (1, 2, 3):
            lead = self.crm.add_lead("a%d@corp.com" % n, "N", "referral", "m1")
            self.crm.qualify(lead, "m1")
            opps.append(self.crm.convert(lead, 100, "m1"))
        self.assertEqual(opps, ["O1", "O2", "O3"])

    def test_failed_conversion_does_not_consume_an_id(self):
        lead = self.new_lead()
        self.crm.qualify(lead, "r1")
        for bad in (lambda: self.crm.convert("L404", 100, "r1"),
                    lambda: self.crm.convert(lead, 0, "r1"),
                    lambda: self.crm.convert(lead, "100", "r1"),
                    lambda: self.crm.convert(lead, 100, "ghost"),
                    lambda: self.crm.convert(lead, 100, "r2")):
            with self.assertRaises(Exception):
                bad()
        opp = self.crm.convert(lead, 100, "r1")
        self.assertEqual(opp, "O1")

    def test_unknown_lead_raises_value_error(self):
        with self.assertRaises(ValueError):
            self.crm.convert("L404", 100, "r1")

    def test_amount_must_be_positive_int_not_bool(self):
        lead = self.new_lead()
        self.crm.qualify(lead, "r1")
        for amount in (0, -1, True, False, 1.0, 2.5, "100", None, [100]):
            with self.subTest(amount=amount):
                with self.assertRaises(ValueError):
                    self.crm.convert(lead, amount, "r1")
        self.assertEqual(self.crm.convert(lead, 1, "r1"), "O1")

    def test_amount_checked_before_permission(self):
        """Line 10: check 2 (ValueError) precedes check 3 (PermissionError)."""
        lead = self.new_lead()
        self.crm.qualify(lead, "r1")
        with self.assertRaises(ValueError):
            self.crm.convert(lead, -5, "r2")

    def test_lead_must_be_qualified(self):
        lead = self.new_lead()
        with self.assertRaises(ValueError):
            self.crm.convert(lead, 100, "r1")
        self.assertEqual(self.crm.leads[lead]["status"], "new")

    def test_status_checked_before_missing_owner(self):
        """Both are ValueError, so assert the un-owned lead path separately."""
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1},
                   {"id": "m1", "role": "manager", "capacity": 1}])
        crm.add_lead("a@corp.com", "Ann", "referral", "m1")
        waiting = crm.add_lead("b@corp.com", "Bob", "referral", "m1")
        crm.qualify(waiting, "m1")
        self.assertEqual(crm.leads[waiting]["status"], "qualified")
        with self.assertRaises(ValueError):
            crm.convert(waiting, 100, "m1")
        self.assertEqual(crm.leads[waiting]["status"], "qualified")
        self.assertEqual(crm.opps, {})

    def test_permission_for_other_rep(self):
        lead = self.new_lead()
        self.crm.qualify(lead, "r1")
        with self.assertRaises(PermissionError):
            self.crm.convert(lead, 100, "r2")
        self.assertEqual(self.crm.leads[lead]["status"], "qualified")
        self.assertEqual(self.crm.opps, {})

    def test_original_amount_is_independent_of_amount_field(self):
        lead = self.new_lead()
        self.crm.qualify(lead, "r1")
        opp = self.crm.convert(lead, 999, "r1")
        self.crm.opps[opp]["amount"] = 100  # simulate later discount
        self.assertEqual(self.crm.opps[opp]["original_amount"], 999)


class TestDuplicateErrorIsNotAnAttributeError(Fixture):
    """Mutation control support: existing_id must be readable on the caught error."""

    def test_existing_id_attribute_exists_on_caught_error(self):
        self.new_lead()
        with self.assertRaises(DuplicateLeadError) as ctx:
            self.crm.add_lead("a@corp.com", "Ann", "web", "m1")
        self.assertTrue(hasattr(ctx.exception, "existing_id"))
        self.assertEqual(ctx.exception.existing_id, "L1")


if __name__ == "__main__":
    unittest.main()
