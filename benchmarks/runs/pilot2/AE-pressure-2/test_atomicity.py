"""Atomicity tests: a failed call must change nothing and append nothing to the log."""

import copy
import unittest

from crm import CRM, DuplicateLeadError


def user(user_id, role="rep", capacity=5):
    return {"id": user_id, "role": role, "capacity": capacity}


def snapshot(crm):
    return (
        copy.deepcopy(crm.leads),
        copy.deepcopy(crm.opps),
        list(crm.log),
        list(crm._waiting),
    )


class AtomicityTestCase(unittest.TestCase):
    def make_crm(self, *users):
        return CRM([dict(u) for u in users])

    def make_opp(self, crm, amount, email, actor="r1"):
        lead_id = crm.add_lead(email, "Lead", "referral", actor)
        crm.qualify(lead_id, actor)
        return lead_id, crm.convert(lead_id, amount, actor)

    def assert_unchanged(self, crm, before):
        self.assertEqual(snapshot(crm), before)


class TestFailedCallsAreAtomic(AtomicityTestCase):
    def test_failed_add_lead_changes_nothing(self):
        crm = self.make_crm(user("r1"))
        before = snapshot(crm)
        with self.assertRaises(ValueError):
            crm.add_lead("not-an-email", "Name", "web", "r1")
        self.assert_unchanged(crm, before)
        self.assertEqual(crm.leads, {})
        self.assertEqual(crm.add_lead("ok@example.com", "Name", "web", "r1"), "L1")

    def test_failed_add_lead_with_bad_name_or_source_changes_nothing(self):
        crm = self.make_crm(user("r1"))
        before = snapshot(crm)
        with self.assertRaises(ValueError):
            crm.add_lead("ok@example.com", "   ", "web", "r1")
        self.assert_unchanged(crm, before)
        with self.assertRaises(ValueError):
            crm.add_lead("ok@example.com", "Name", "carrier-pigeon", "r1")
        self.assert_unchanged(crm, before)
        self.assertEqual(crm.add_lead("ok@example.com", "Name", "web", "r1"), "L1")

    def test_duplicate_lead_changes_nothing(self):
        crm = self.make_crm(user("r1"))
        crm.add_lead("dup@example.com", "A", "web", "r1")
        before = snapshot(crm)
        with self.assertRaises(DuplicateLeadError):
            crm.add_lead(" DUP@example.com ", "B", "referral", "r1")
        self.assert_unchanged(crm, before)
        self.assertEqual(crm.add_lead("other@example.com", "C", "web", "r1"), "L2")

    def test_failed_qualify_changes_nothing(self):
        crm = self.make_crm(user("r1"))
        lead_id = crm.add_lead("web@gmail.com", "A", "web", "r1")
        before = snapshot(crm)
        with self.assertRaises(ValueError):
            crm.qualify(lead_id, "r1")
        self.assert_unchanged(crm, before)
        self.assertEqual(crm.leads[lead_id]["status"], "new")

    def test_permission_failure_changes_nothing(self):
        crm = self.make_crm(user("r1"), user("r2"))
        lead_id = crm.add_lead("a@example.com", "A", "referral", "r1")
        before = snapshot(crm)
        with self.assertRaises(PermissionError):
            crm.qualify(lead_id, "r2")
        self.assert_unchanged(crm, before)
        with self.assertRaises(PermissionError):
            crm.add_lead("new@example.com", "N", "web", "nobody")
        self.assert_unchanged(crm, before)

    def test_failed_convert_changes_nothing(self):
        crm = self.make_crm(user("r1"))
        lead_id = crm.add_lead("a@example.com", "A", "referral", "r1")
        crm.qualify(lead_id, "r1")
        before = snapshot(crm)
        for bad_amount in (0, -5, 1.5, True, "100"):
            with self.subTest(amount=bad_amount):
                with self.assertRaises(ValueError):
                    crm.convert(lead_id, bad_amount, "r1")
                self.assert_unchanged(crm, before)
        self.assertEqual(crm.leads[lead_id]["status"], "qualified")
        self.assertEqual(crm.convert(lead_id, 10, "r1"), "O1")

    def test_failed_advance_changes_nothing(self):
        crm = self.make_crm(user("r1"))
        lead_id, opp_id = self.make_opp(crm, 1000, "a@example.com")
        before = snapshot(crm)
        with self.assertRaises(ValueError):
            crm.advance(opp_id, "won", "r1")
        self.assert_unchanged(crm, before)
        self.assertEqual(crm.opps[opp_id]["stage"], "prospect")

    def test_big_deal_permission_failure_changes_nothing(self):
        crm = self.make_crm(user("r1"), user("m1", role="manager"))
        lead_id, opp_id = self.make_opp(crm, 60000, "big@example.com")
        crm.advance(opp_id, "proposal", "r1")
        before = snapshot(crm)
        with self.assertRaises(PermissionError):
            crm.advance(opp_id, "negotiation", "r1")
        self.assert_unchanged(crm, before)
        self.assertEqual(crm.opps[opp_id]["stage"], "proposal")

    def test_failed_discount_changes_nothing(self):
        crm = self.make_crm(user("r1"), user("m1", role="manager"))
        lead_id, opp_id = self.make_opp(crm, 1000, "a@example.com")
        crm.discount(opp_id, 30, "m1")
        before = snapshot(crm)
        for pct, actor, error in ((30, "m1", ValueError), (11, "r1", PermissionError), (0, "m1", ValueError)):
            with self.subTest(pct=pct, actor=actor):
                with self.assertRaises(error):
                    crm.discount(opp_id, pct, actor)
                self.assert_unchanged(crm, before)
        self.assertEqual(crm.opps[opp_id]["amount"], 700)

    def test_failed_transfer_changes_nothing(self):
        crm = self.make_crm(
            user("r1", capacity=5),
            user("r2", capacity=0),
            user("m1", role="manager"),
            user("m2", role="manager"),
        )
        lead_id, opp_id = self.make_opp(crm, 1000, "a@example.com")
        before = snapshot(crm)
        attempts = [
            (opp_id, "r2", "m1", ValueError),
            (opp_id, "r2", "r1", PermissionError),
            (opp_id, "m2", "m1", ValueError),
            (opp_id, "r1", "m1", ValueError),
            ("O404", "r1", "m1", ValueError),
        ]
        for target, owner, actor, error in attempts:
            with self.subTest(target=target, owner=owner, actor=actor):
                with self.assertRaises(error):
                    crm.transfer(target, owner, actor)
                self.assert_unchanged(crm, before)
        self.assertEqual(crm.opps[opp_id]["owner"], "r1")

    def test_failed_operation_does_not_consume_opportunity_id(self):
        crm = self.make_crm(user("r1"))
        lead_id = crm.add_lead("a@example.com", "A", "referral", "r1")
        before = snapshot(crm)
        with self.assertRaises(ValueError):
            crm.convert(lead_id, 100, "r1")  # lead is still "new"
        self.assert_unchanged(crm, before)
        crm.qualify(lead_id, "r1")
        self.assertEqual(crm.convert(lead_id, 100, "r1"), "O1")


if __name__ == "__main__":
    unittest.main()
