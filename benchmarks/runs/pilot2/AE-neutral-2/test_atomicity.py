"""Tests that a failed call changes no state and appends nothing to the log."""

import unittest

from crm import CRM, DuplicateLeadError
from crm_fixtures import add, make_opp, snapshot, wide_crm


class TestAddLeadAtomicity(unittest.TestCase):
    def test_invalid_payloads_change_nothing(self):
        for email, name, source in [
            ("bad", "Lead", "web"),
            ("a@corp.com", "", "web"),
            ("a@corp.com", "Lead", "fax"),
            (None, None, None),
        ]:
            with self.subTest(email=email, name=name, source=source):
                crm = wide_crm()
                before = snapshot(crm)
                with self.assertRaises(ValueError):
                    crm.add_lead(email, name, source, "r1")
                self.assertEqual(snapshot(crm), before)

    def test_duplicate_changes_nothing(self):
        crm = wide_crm()
        add(crm, email="a@corp.com")
        before = snapshot(crm)
        with self.assertRaises(DuplicateLeadError):
            crm.add_lead("A@corp.com", "Other", "web", "r2")
        self.assertEqual(snapshot(crm), before)


class TestQualifyAtomicity(unittest.TestCase):
    def test_failed_qualify_changes_nothing(self):
        crm = wide_crm()
        lead_id = add(crm, email="a@corp.com")
        crm.qualify(lead_id, "r1")
        before = snapshot(crm)
        with self.assertRaises(ValueError):
            crm.qualify(lead_id, "r1")  # already qualified
        self.assertEqual(snapshot(crm), before)

    def test_qualify_permission_failure_changes_nothing(self):
        crm = wide_crm()
        lead_id = add(crm, email="a@corp.com")
        before = snapshot(crm)
        with self.assertRaises(PermissionError):
            crm.qualify(lead_id, "r2")
        self.assertEqual(snapshot(crm), before)

    def test_low_score_failure_changes_nothing(self):
        crm = wide_crm()
        lead_id = add(crm, email="a@gmail.com", source="web")
        before = snapshot(crm)
        with self.assertRaises(ValueError):
            crm.qualify(lead_id, "r1")
        self.assertEqual(snapshot(crm), before)


class TestConvertAtomicity(unittest.TestCase):
    def test_bad_amount_changes_nothing(self):
        crm = wide_crm()
        lead_id = add(crm, email="a@corp.com")
        crm.qualify(lead_id, "r1")
        before = snapshot(crm)
        for amount in (0, -1, 1.5, True, "10"):
            with self.subTest(amount=amount):
                with self.assertRaises(ValueError):
                    crm.convert(lead_id, amount, "r1")
                self.assertEqual(snapshot(crm), before)

    def test_convert_permission_failure_changes_nothing(self):
        crm = wide_crm()
        lead_id = add(crm, email="a@corp.com")
        crm.qualify(lead_id, "r1")
        before = snapshot(crm)
        with self.assertRaises(PermissionError):
            crm.convert(lead_id, 100, "r2")
        self.assertEqual(snapshot(crm), before)

    def test_unqualified_lead_changes_nothing(self):
        crm = wide_crm()
        lead_id = add(crm, email="a@corp.com")
        before = snapshot(crm)
        with self.assertRaises(ValueError):
            crm.convert(lead_id, 100, "r1")
        self.assertEqual(snapshot(crm), before)


class TestAdvanceAtomicity(unittest.TestCase):
    def test_failing_advances_change_nothing(self):
        crm = wide_crm()
        opp_id, _ = make_opp(crm, amount=60000)
        before = snapshot(crm)
        for stage, actor in [
            ("bogus", "r1"),
            ("negotiation", "r1"),
            ("proposal", "r2"),
            ("won", "r1"),
        ]:
            with self.subTest(stage=stage, actor=actor):
                with self.assertRaises((ValueError, PermissionError)):
                    crm.advance(opp_id, stage, actor)
                self.assertEqual(snapshot(crm), before)

    def test_final_opportunity_failure_changes_nothing(self):
        crm = wide_crm()
        opp_id, _ = make_opp(crm, amount=1000)
        crm.advance(opp_id, "lost", "r1")
        before = snapshot(crm)
        with self.assertRaises(ValueError):
            crm.advance(opp_id, "proposal", "r1")
        self.assertEqual(snapshot(crm), before)


class TestDiscountAtomicity(unittest.TestCase):
    def test_discount_failure_changes_nothing(self):
        crm = wide_crm()
        opp_id, _ = make_opp(crm, amount=1000)
        before = snapshot(crm)
        with self.assertRaises(ValueError):
            crm.discount(opp_id, 0, "m1")
        self.assertEqual(snapshot(crm), before)

    def test_discount_permission_failure_changes_nothing(self):
        crm = wide_crm()
        opp_id, _ = make_opp(crm, amount=1000)
        before = snapshot(crm)
        with self.assertRaises(PermissionError):
            crm.discount(opp_id, 11, "r1")
        self.assertEqual(snapshot(crm), before)

    def test_cumulative_floor_failure_changes_nothing(self):
        crm = wide_crm()
        opp_id, _ = make_opp(crm, amount=1000)
        crm.discount(opp_id, 30, "m1")
        before = snapshot(crm)
        with self.assertRaises(ValueError):
            crm.discount(opp_id, 1, "m1")
        self.assertEqual(snapshot(crm), before)

    def test_final_stage_failure_changes_nothing(self):
        crm = wide_crm()
        opp_id, _ = make_opp(crm, amount=1000)
        crm.advance(opp_id, "lost", "r1")
        before = snapshot(crm)
        with self.assertRaises(ValueError):
            crm.discount(opp_id, 5, "m1")
        self.assertEqual(snapshot(crm), before)


class TestTransferAtomicity(unittest.TestCase):
    def test_failing_transfers_change_nothing(self):
        crm = wide_crm()
        opp_id, _ = make_opp(crm, amount=1000)
        before = snapshot(crm)
        for target, actor in [
            ("r2", "r1"),
            ("ghost", "m1"),
            ("m1", "m1"),
            ("r1", "m1"),
        ]:
            with self.subTest(target=target, actor=actor):
                with self.assertRaises((ValueError, PermissionError)):
                    crm.transfer(opp_id, target, actor)
                self.assertEqual(snapshot(crm), before)

    def test_capacity_failure_leaves_queue_untouched(self):
        crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 1},
                {"id": "r2", "role": "rep", "capacity": 1},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        first = add(crm, email="a@corp.com")
        add(crm, email="b@corp.com")
        crm.qualify(first, "m1")
        opp_id = crm.convert(first, 1000, "m1")
        before = snapshot(crm)
        with self.assertRaises(ValueError):
            crm.transfer(opp_id, "r2", "m1")
        self.assertEqual(snapshot(crm), before)
        self.assertFalse(any(entry[0] == "assign" for entry in crm.log))


class TestIdCountersAreTransactional(unittest.TestCase):
    def test_failed_add_does_not_consume_lead_id(self):
        crm = wide_crm()
        with self.assertRaises(ValueError):
            crm.add_lead("bad", "Lead", "web", "r1")
        self.assertEqual(crm.add_lead("a@corp.com", "Lead", "web", "r1"), "L1")

    def test_failed_convert_does_not_consume_opp_id(self):
        crm = wide_crm()
        lead_id = add(crm, email="a@corp.com")
        crm.qualify(lead_id, "r1")
        with self.assertRaises(ValueError):
            crm.convert(lead_id, 0, "r1")
        self.assertEqual(crm.convert(lead_id, 100, "r1"), "O1")

    def test_every_failure_preserves_the_log(self):
        crm = wide_crm()
        lead_id = add(crm, email="a@corp.com")
        crm.qualify(lead_id, "r1")
        opp_id = crm.convert(lead_id, 1000, "r1")
        before_log = list(crm.log)
        failures = [
            lambda: crm.add_lead("bad", "Lead", "web", "r1"),
            lambda: crm.add_lead("a@corp.com", "Lead", "web", "r1"),
            lambda: crm.qualify(lead_id, "r1"),
            lambda: crm.convert(lead_id, 100, "r1"),
            lambda: crm.advance(opp_id, "bogus", "r1"),
            lambda: crm.discount(opp_id, 0, "m1"),
            lambda: crm.transfer(opp_id, "ghost", "m1"),
        ]
        for index, call in enumerate(failures):
            with self.subTest(call=index):
                with self.assertRaises(
                    (ValueError, PermissionError, DuplicateLeadError)
                ):
                    call()
                self.assertEqual(crm.log, before_log)


if __name__ == "__main__":
    unittest.main()
