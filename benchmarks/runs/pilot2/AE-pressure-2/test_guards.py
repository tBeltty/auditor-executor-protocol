"""Guard coverage for spec rules the first suite missed.

Each test here corresponds to a blocking finding in ``audit.md`` §7: a guard
that could be deleted from ``crm.py`` while the original 48 tests stayed green.
"""

import copy
import unittest

from crm import CRM


def user(user_id, role="rep", capacity=5):
    return {"id": user_id, "role": role, "capacity": capacity}


class GuardTestCase(unittest.TestCase):
    def make_crm(self, *users):
        return CRM([dict(u) for u in users])

    def snapshot(self, crm):
        return (
            copy.deepcopy(crm.leads),
            copy.deepcopy(crm.opps),
            list(crm.log),
            list(crm._waiting),
        )

    def make_opp(self, crm, amount, email, actor="r1", source="referral"):
        lead_id = crm.add_lead(email, "Lead", source, actor)
        crm.qualify(lead_id, actor)
        return lead_id, crm.convert(lead_id, amount, actor)


class TestExistenceChecks(GuardTestCase):
    def test_qualify_unknown_lead_raises_value_error(self):
        crm = self.make_crm(user("r1"), user("m1", role="manager"))
        crm.add_lead("known@example.com", "A", "web", "r1")
        before = self.snapshot(crm)
        # The record lookup is check 1, before the permission check, so both a
        # rep and a manager must get ValueError rather than PermissionError.
        with self.assertRaises(ValueError):
            crm.qualify("L404", "r1")
        with self.assertRaises(ValueError):
            crm.qualify("L404", "m1")
        self.assertEqual(self.snapshot(crm), before)

    def test_convert_unknown_lead_raises_value_error(self):
        crm = self.make_crm(user("r1"), user("m1", role="manager"))
        before = self.snapshot(crm)
        with self.assertRaises(ValueError):
            crm.convert("L404", 100, "r1")
        with self.assertRaises(ValueError):
            crm.convert("L404", 100, "m1")
        self.assertEqual(self.snapshot(crm), before)
        # A rejected lookup must not consume an opportunity id either.
        lead_id, opp_id = self.make_opp(crm, 100, "real@example.com")
        self.assertEqual(opp_id, "O1")

    def test_advance_unknown_opportunity_raises_value_error(self):
        crm = self.make_crm(user("r1"), user("m1", role="manager"))
        before = self.snapshot(crm)
        with self.assertRaises(ValueError):
            crm.advance("O404", "proposal", "r1")
        with self.assertRaises(ValueError):
            crm.advance("O404", "proposal", "m1")
        # Check 1 precedes check 2: unknown id wins over an invalid stage.
        with self.assertRaises(ValueError):
            crm.advance("O404", "bogus", "r1")
        self.assertEqual(self.snapshot(crm), before)

    def test_discount_unknown_opportunity_raises_value_error(self):
        crm = self.make_crm(user("r1"), user("m1", role="manager"))
        before = self.snapshot(crm)
        with self.assertRaises(ValueError):
            crm.discount("O404", 5, "m1")
        with self.assertRaises(ValueError):
            crm.discount("O404", 5, "r1")
        self.assertEqual(self.snapshot(crm), before)


class TestQualifyStatusGuard(GuardTestCase):
    def test_qualify_rejects_non_new_status(self):
        crm = self.make_crm(user("r1"))
        lead_id = crm.add_lead("ref@example.com", "A", "referral", "r1")
        crm.qualify(lead_id, "r1")
        self.assertEqual(crm.leads[lead_id]["status"], "qualified")

        before = self.snapshot(crm)
        with self.assertRaises(ValueError):
            crm.qualify(lead_id, "r1")
        self.assertEqual(self.snapshot(crm), before)
        self.assertEqual(crm.leads[lead_id]["status"], "qualified")

        # A converted lead is not "new" either.
        crm.convert(lead_id, 100, "r1")
        self.assertEqual(crm.leads[lead_id]["status"], "converted")
        before = self.snapshot(crm)
        with self.assertRaises(ValueError):
            crm.qualify(lead_id, "r1")
        self.assertEqual(self.snapshot(crm), before)


class TestConvertOwnerGuard(GuardTestCase):
    def test_convert_ownerless_lead_raises_value_error(self):
        crm = self.make_crm(user("r0", capacity=0), user("m1", role="manager"))
        lead_id = crm.add_lead("a@example.com", "A", "referral", "m1")
        self.assertIsNone(crm.leads[lead_id]["owner"])
        self.assertEqual(crm.leads[lead_id]["score"], 45)
        crm.qualify(lead_id, "m1")

        before = self.snapshot(crm)
        with self.assertRaises(ValueError):
            crm.convert(lead_id, 100, "m1")
        self.assertEqual(crm.opps, {})
        self.assertEqual(self.snapshot(crm), before)
        self.assertEqual([entry[0] for entry in crm.log], ["add_lead", "qualify"])
        self.assertEqual(crm.leads[lead_id]["status"], "qualified")


class TestAssignmentTieBreak(GuardTestCase):
    def test_assignment_tiebreak_uses_string_order(self):
        crm = self.make_crm(user("r9", capacity=1), user("r10", capacity=1))
        first = crm.add_lead("a@example.com", "A", "web", "r9")
        # "r10" < "r9" in string order, so the first free rep by id is r10.
        self.assertEqual(crm.leads[first]["owner"], "r10")
        second = crm.add_lead("b@example.com", "B", "web", "r9")
        self.assertEqual(crm.leads[second]["owner"], "r9")


class TestBigDealThresholdSource(GuardTestCase):
    def test_big_deal_threshold_uses_current_amount(self):
        crm = self.make_crm(user("r1"), user("m1", role="manager"))
        lead_id, opp_id = self.make_opp(crm, 60000, "big@example.com")
        crm.advance(opp_id, "proposal", "r1")
        crm.discount(opp_id, 25, "m1")
        self.assertEqual(crm.opps[opp_id]["amount"], 45000)
        self.assertEqual(crm.opps[opp_id]["original_amount"], 60000)

        # 45000 is not above the threshold, so a rep may close the transition;
        # a check against original_amount (60000) would wrongly demand a manager.
        crm.advance(opp_id, "negotiation", "r1")
        self.assertEqual(crm.opps[opp_id]["stage"], "negotiation")


class TestForecastIsPure(GuardTestCase):
    def test_forecast_appends_no_log_entry(self):
        empty = self.make_crm(user("r1"))
        self.assertEqual(empty.forecast(), {"open": 0, "weighted": 0, "won": 0})
        self.assertEqual(empty.log, [])

        crm = self.make_crm(user("r1"))
        lead_id, opp_id = self.make_opp(crm, 1000, "a@example.com")
        crm.advance(opp_id, "proposal", "r1")
        before = self.snapshot(crm)
        forecast = crm.forecast()
        self.assertEqual(crm.forecast(), forecast)
        self.assertEqual(self.snapshot(crm), before)
        self.assertEqual(crm.forecast(), {"open": 1, "weighted": 300, "won": 0})


if __name__ == "__main__":
    unittest.main()
