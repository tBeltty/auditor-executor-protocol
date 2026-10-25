"""Atomicity tests: a failed call must change nothing and log nothing."""

import unittest

from crm import CRM, DuplicateLeadError


def staff():
    return [
        {"id": "r1", "role": "rep", "capacity": 1},
        {"id": "r2", "role": "rep", "capacity": 1},
        {"id": "m1", "role": "manager", "capacity": 9},
    ]


class TestFailedCallsLeaveNoTrace(unittest.TestCase):
    def test_failed_add_lead_does_not_burn_an_id(self):
        crm = CRM(staff())
        with self.assertRaises(ValueError):
            crm.add_lead("buyer@acme.com", "", "web", "r1")
        self.assertEqual(crm.leads, {})
        self.assertEqual(crm.log, [])
        self.assertEqual(crm.add_lead("buyer@acme.com", "Ada", "web", "r1"), "L1")

    def test_duplicate_does_not_burn_an_id_or_log(self):
        crm = CRM(staff())
        first = crm.add_lead("buyer@acme.com", "Ada", "web", "r1")
        log_before = list(crm.log)
        with self.assertRaises(DuplicateLeadError):
            crm.add_lead("BUYER@acme.com", "Other", "referral", "r1")
        self.assertEqual(list(crm.leads), [first])
        self.assertEqual(crm.log, log_before)
        self.assertEqual(crm.add_lead("other@acme.com", "B", "web", "r1"), "L2")

    def test_failed_qualify_leaves_the_status_new(self):
        crm = CRM(staff())
        lead = crm.add_lead("a@acme.com", "A", "web", "r1")
        log_before = list(crm.log)
        with self.assertRaises(ValueError):
            crm.qualify(lead, "r1")
        self.assertEqual(crm.leads[lead]["status"], "new")
        self.assertEqual(crm.log, log_before)

    def test_failed_convert_leaves_the_lead_qualified_and_no_opposition(self):
        crm = CRM(staff())
        lead = crm.add_lead("a@acme.com", "A", "referral", "r1")
        crm.qualify(lead, "r1")
        log_before = list(crm.log)
        for bad in (0, -10, True, "100"):
            with self.assertRaises(ValueError):
                crm.convert(lead, bad, "r1")
        self.assertEqual(crm.leads[lead]["status"], "qualified")
        self.assertEqual(crm.opps, {})
        self.assertEqual(crm.log, log_before)

    def test_failed_convert_by_stranger_leaves_everything_intact(self):
        crm = CRM(staff())
        lead = crm.add_lead("a@acme.com", "A", "referral", "r1")
        crm.qualify(lead, "r1")
        log_before = list(crm.log)
        with self.assertRaises(PermissionError):
            crm.convert(lead, 100, "r2")
        self.assertEqual(crm.leads[lead]["status"], "qualified")
        self.assertEqual(crm.opps, {})
        self.assertEqual(crm.log, log_before)

    def test_failed_advance_keeps_the_stage_and_the_log(self):
        crm = CRM(staff())
        lead = crm.add_lead("a@acme.com", "A", "referral", "r1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 1000, "r1")
        log_before = list(crm.log)
        with self.assertRaises(PermissionError):
            crm.advance(opp, "proposal", "r2")
        with self.assertRaises(ValueError):
            crm.advance(opp, "won", "r1")
        self.assertEqual(crm.opps[opp]["stage"], "prospect")
        self.assertEqual(crm.log, log_before)

    def test_failed_big_deal_advance_keeps_the_stage(self):
        crm = CRM(staff())
        lead = crm.add_lead("a@acme.com", "A", "referral", "r1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 90000, "r1")
        crm.advance(opp, "proposal", "r1")
        log_before = list(crm.log)
        with self.assertRaises(PermissionError):
            crm.advance(opp, "negotiation", "r1")
        self.assertEqual(crm.opps[opp]["stage"], "proposal")
        self.assertEqual(crm.log, log_before)

    def test_failed_discount_keeps_amount_and_log(self):
        crm = CRM(staff())
        lead = crm.add_lead("a@acme.com", "A", "referral", "r1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 1000, "r1")
        crm.discount(opp, 20, "m1")
        log_before = list(crm.log)
        with self.assertRaises(ValueError):
            crm.discount(opp, 20, "m1")
        with self.assertRaises(PermissionError):
            crm.discount(opp, 15, "r1")
        self.assertEqual(crm.opps[opp]["amount"], 800)
        self.assertEqual(crm.log, log_before)

    def test_failed_transfer_keeps_owner_log_and_queue(self):
        crm = CRM(staff())
        lead = crm.add_lead("a@acme.com", "A", "referral", "r1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 1000, "r1")
        filler = crm.add_lead("b@acme.com", "B", "referral", "r2")
        self.assertEqual(crm.leads[filler]["owner"], "r2")
        crm.qualify(filler, "r2")
        # r2 is now at capacity, so the transfer must fail
        log_before = list(crm.log)
        with self.assertRaises(ValueError):
            crm.transfer(opp, "r2", "m1")
        with self.assertRaises(PermissionError):
            crm.transfer(opp, "r2", "r1")
        self.assertEqual(crm.opps[opp]["owner"], "r1")
        self.assertEqual(crm.log, log_before)
        self.assertEqual(crm.load("r1"), 1)
        self.assertEqual(crm.load("r2"), 1)

    def test_unknown_actor_never_mutates(self):
        crm = CRM(staff())
        lead = crm.add_lead("a@acme.com", "A", "referral", "r1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 1000, "r1")
        snapshot = (dict(crm.leads[lead]), dict(crm.opps[opp]), list(crm.log), list(crm.waiting))
        for call in (
            lambda: crm.add_lead("z@acme.com", "Z", "web", "ghost"),
            lambda: crm.qualify(lead, "ghost"),
            lambda: crm.convert(lead, 1000, "ghost"),
            lambda: crm.advance(opp, "proposal", "ghost"),
            lambda: crm.discount(opp, 10, "ghost"),
            lambda: crm.transfer(opp, "r2", "ghost"),
        ):
            with self.assertRaises(PermissionError):
                call()
        self.assertEqual(dict(crm.leads[lead]), snapshot[0])
        self.assertEqual(dict(crm.opps[opp]), snapshot[1])
        self.assertEqual(crm.log, snapshot[2])
        self.assertEqual(crm.waiting, snapshot[3])

    def test_winning_assigns_exactly_one_waiting_lead_per_freed_slot(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 0},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        lead = crm.add_lead("a@acme.com", "A", "referral", "r1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 1000, "r1")
        waiting = crm.add_lead("b@acme.com", "B", "web", "m1")
        self.assertEqual(crm.waiting, [waiting])
        for stage in ("proposal", "negotiation", "won"):
            crm.advance(opp, stage, "r1")
        self.assertEqual(crm.leads[waiting]["owner"], "r1")
        self.assertEqual(crm.waiting, [])
        assigns = [entry for entry in crm.log if entry[0] == "assign"]
        self.assertEqual(assigns, [("assign", waiting, "system")])


if __name__ == "__main__":
    unittest.main()
