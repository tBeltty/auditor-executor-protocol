"""Atomicity, log-order and load-accounting tests."""

import unittest

from _helpers import manager, qualify_and_convert, rep, snapshot
from crm import CRM


class LogAndAtomicityTests(unittest.TestCase):
    def setUp(self):
        self.crm = CRM([rep("r1", 5), rep("r2", 5), manager("m1")])
        self.lead_id, self.opp_id = qualify_and_convert(self.crm, amount=1000)

    def test_happy_path_log_sequence(self):
        crm = CRM([rep("r1", 5)])
        lead = crm.add_lead("a@corp.com", "A", "referral", "r1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 1000, "r1")
        crm.advance(opp, "proposal", "r1")
        crm.discount(opp, 10, "r1")
        crm.advance(opp, "negotiation", "r1")
        crm.advance(opp, "won", "r1")
        self.assertEqual(
            crm.log,
            [
                ("add_lead", lead, "r1"),
                ("qualify", lead, "r1"),
                ("convert", opp, "r1"),
                ("advance", opp, "r1"),
                ("discount", opp, "r1"),
                ("advance", opp, "r1"),
                ("advance", opp, "r1"),
            ],
        )

    def test_failures_append_nothing(self):
        failed_calls = [
            (self.crm.add_lead, ("a@corp.com", "A", "referral", "ghost"), PermissionError),
            (self.crm.add_lead, ("bad", "A", "referral", "r1"), ValueError),
            (self.crm.add_lead, ("x@corp.com", "", "referral", "r1"), ValueError),
            (self.crm.add_lead, ("x@corp.com", "X", "nope", "r1"), ValueError),
            (self.crm.qualify, ("L99", "r1"), ValueError),
            (self.crm.qualify, (self.lead_id, "r2"), PermissionError),
            (self.crm.convert, (self.lead_id, 100, "r1"), ValueError),
            (self.crm.convert, (self.lead_id, 0, "r1"), ValueError),
            (self.crm.advance, (self.opp_id, "negotiation", "r1"), ValueError),
            (self.crm.advance, (self.opp_id, "proposal", "r2"), PermissionError),
            (self.crm.discount, (self.opp_id, 31, "r1"), ValueError),
            (self.crm.discount, (self.opp_id, 5, "r2"), PermissionError),
            (self.crm.transfer, (self.opp_id, "r2", "r1"), PermissionError),
            (self.crm.transfer, (self.opp_id, "ghost", "m1"), ValueError),
        ]
        for method, args, exc in failed_calls:
            before = snapshot(self.crm)
            with self.assertRaises(exc, msg=(method.__name__, args)):
                method(*args)
            self.assertEqual(snapshot(self.crm), before, (method.__name__, args))

    def test_unknown_actor_first_everywhere(self):
        checks = [
            (self.crm.add_lead, (None, None, None, "ghost")),
            (self.crm.qualify, ("L99", "ghost")),
            (self.crm.convert, ("L99", None, "ghost")),
            (self.crm.advance, ("O99", None, "ghost")),
            (self.crm.discount, ("O99", None, "ghost")),
            (self.crm.transfer, ("O99", None, "ghost")),
        ]
        for method, args in checks:
            with self.assertRaises(PermissionError, msg=method.__name__):
                method(*args)

    def test_unknown_actor_does_not_touch_counters(self):
        before = snapshot(self.crm)
        with self.assertRaises(PermissionError):
            self.crm.add_lead("z@corp.com", "Z", "referral", "ghost")
        self.crm.add_lead("z@corp.com", "Z", "referral", "r1")
        self.assertEqual(self.crm.leads["L2"]["email"], "z@corp.com")
        self.assertEqual(before[0], {"L1": self.crm.leads["L1"]})


class LoadAccountingTests(unittest.TestCase):
    def test_qualified_leads_still_count_toward_load(self):
        crm = CRM([rep("r1", 1)])
        lead = crm.add_lead("a@corp.com", "A", "referral", "r1")
        crm.qualify(lead, "r1")  # still occupies r1's only slot
        other = crm.add_lead("b@corp.com", "B", "referral", "r1")
        self.assertIsNone(crm.leads[other]["owner"])
        self.assertEqual(crm.waiting, [other])

    def test_open_opportunities_count_toward_load(self):
        crm = CRM([rep("r1", 1)])
        lead_a, opp = qualify_and_convert(crm, email="a@corp.com")
        blocked = crm.add_lead("b@corp.com", "B", "referral", "r1")
        self.assertIsNone(crm.leads[blocked]["owner"])

        crm.advance(opp, "proposal", "r1")
        self.assertIsNone(crm.leads[blocked]["owner"])
        crm.advance(opp, "negotiation", "r1")
        self.assertIsNone(crm.leads[blocked]["owner"])
        crm.advance(opp, "won", "r1")
        self.assertEqual(crm.leads[blocked]["owner"], "r1")

    def test_lost_opportunity_frees_load(self):
        crm = CRM([rep("r1", 1)])
        lead_a, opp = qualify_and_convert(crm, email="a@corp.com")
        waiting = crm.add_lead("b@corp.com", "B", "referral", "r1")
        crm.advance(opp, "lost", "r1")
        self.assertEqual(crm.leads[waiting]["owner"], "r1")

    def test_lowest_load_not_lowest_id(self):
        crm = CRM([rep("a", 3), rep("b", 3)])
        first = crm.add_lead("one@corp.com", "One", "referral", "a")
        second = crm.add_lead("two@corp.com", "Two", "referral", "a")
        third = crm.add_lead("three@corp.com", "Three", "referral", "a")
        self.assertEqual(crm.leads[first]["owner"], "a")
        self.assertEqual(crm.leads[second]["owner"], "b")
        self.assertEqual(crm.leads[third]["owner"], "a")


if __name__ == "__main__":
    unittest.main()
