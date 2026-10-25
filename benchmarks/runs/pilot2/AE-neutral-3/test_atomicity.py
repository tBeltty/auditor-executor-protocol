import copy
import unittest

from crm import CRM, DuplicateLeadError


def make_crm(cap1=1, cap2=0):
    return CRM(
        [
            {"id": "rep1", "role": "rep", "capacity": cap1},
            {"id": "rep2", "role": "rep", "capacity": cap2},
            {"id": "boss", "role": "manager", "capacity": 0},
        ]
    )


def snapshot(crm):
    return copy.deepcopy(
        {
            "leads": crm.leads,
            "opps": crm.opps,
            "log": crm.log,
            "waiting": crm.waiting,
            "lead_seq": crm._lead_seq,
            "opp_seq": crm._opp_seq,
        }
    )


class AtomicityTest(unittest.TestCase):
    """Every failing call must leave the whole object byte-for-byte identical."""

    def setUp(self):
        self.crm = make_crm(cap1=1, cap2=0)
        self.lead_id = self.crm.add_lead("ana@corp.io", "Ana", "referral", "rep1")
        self.crm.qualify(self.lead_id, "rep1")
        self.opp_id = self.crm.convert(self.lead_id, 1000, "rep1")
        self.queued_id = self.crm.add_lead("bo@corp.io", "Bo", "referral", "rep1")
        self.assertEqual(self.crm.waiting, [self.queued_id])

    def assert_atomic(self, call, exc):
        before = snapshot(self.crm)
        with self.assertRaises(exc):
            call()
        self.assertEqual(snapshot(self.crm), before)

    def test_failed_add_lead_changes_nothing(self):
        self.assert_atomic(
            lambda: self.crm.add_lead("nope", "X", "web", "rep1"), ValueError
        )
        self.assert_atomic(
            lambda: self.crm.add_lead("x@corp.io", "  ", "web", "rep1"), ValueError
        )
        self.assert_atomic(
            lambda: self.crm.add_lead("x@corp.io", "X", "radio", "rep1"), ValueError
        )
        self.assert_atomic(
            lambda: self.crm.add_lead("ANA@corp.io ", "X", "web", "rep1"),
            DuplicateLeadError,
        )

    def test_failed_add_lead_does_not_consume_an_id(self):
        with self.assertRaises(ValueError):
            self.crm.add_lead("nope", "X", "web", "rep1")
        self.assertEqual(
            self.crm.add_lead("new@corp.io", "New", "web", "rep1"), "L3"
        )

    def test_failed_add_lead_with_unknown_actor_changes_nothing(self):
        self.assert_atomic(
            lambda: self.crm.add_lead("x@corp.io", "X", "web", "ghost"), PermissionError
        )

    def test_failed_qualify_changes_nothing(self):
        crm = make_crm(cap1=5)
        lead_id = crm.add_lead("low@gmail.com", "L", "web", "rep1")
        before = snapshot(crm)
        with self.assertRaises(ValueError):
            crm.qualify(lead_id, "rep1")
        self.assertEqual(snapshot(crm), before)
        with self.assertRaises(ValueError):
            crm.qualify("L404", "rep1")
        self.assertEqual(snapshot(crm), before)
        with self.assertRaises(PermissionError):
            crm.qualify(lead_id, "rep2")
        self.assertEqual(snapshot(crm), before)

    def test_failed_qualify_on_wrong_status_changes_nothing(self):
        self.assert_atomic(
            lambda: self.crm.qualify(self.lead_id, "boss"), ValueError
        )

    def test_failed_convert_changes_nothing(self):
        self.assert_atomic(lambda: self.crm.convert(self.lead_id, 0, "rep1"), ValueError)
        self.assert_atomic(
            lambda: self.crm.convert(self.lead_id, True, "rep1"), ValueError
        )
        self.assert_atomic(
            lambda: self.crm.convert(self.queued_id, 100, "boss"), ValueError
        )

    def test_failed_convert_does_not_consume_an_opportunity_id(self):
        with self.assertRaises(ValueError):
            self.crm.convert(self.lead_id, -1, "rep1")
        crm = make_crm(cap1=5)
        lead_id = crm.add_lead("b@corp.io", "B", "referral", "rep1")
        crm.qualify(lead_id, "rep1")
        self.assertEqual(crm.convert(lead_id, 100, "rep1"), "O1")

    def test_failed_convert_on_unowned_lead_changes_nothing(self):
        # crm.md:25 r5 -- the owner check is the last one, so it is the gate
        # that proves nothing was written before it.
        crm = make_crm(cap1=0, cap2=0)
        lead_id = crm.add_lead("a@corp.io", "A", "referral", "boss")
        crm.qualify(lead_id, "boss")
        before = snapshot(crm)
        with self.assertRaises(ValueError):
            crm.convert(lead_id, 100, "boss")
        self.assertEqual(snapshot(crm), before)
        self.assertEqual(crm.leads[lead_id]["status"], "qualified")

    def test_failed_advance_changes_nothing(self):
        self.assert_atomic(
            lambda: self.crm.advance(self.opp_id, "won", "rep1"), ValueError
        )
        self.assert_atomic(
            lambda: self.crm.advance(self.opp_id, "closed", "rep1"), ValueError
        )
        self.assert_atomic(
            lambda: self.crm.advance(self.opp_id, "proposal", "rep2"), PermissionError
        )
        self.assert_atomic(
            lambda: self.crm.advance(self.opp_id, "proposal", "ghost"), PermissionError
        )

    def test_failed_big_deal_advance_changes_nothing(self):
        crm = make_crm(cap1=5)
        lead_id = crm.add_lead("big@corp.io", "B", "referral", "rep1")
        crm.qualify(lead_id, "rep1")
        opp_id = crm.convert(lead_id, 80000, "rep1")
        crm.advance(opp_id, "proposal", "rep1")
        before = snapshot(crm)
        with self.assertRaises(PermissionError):
            crm.advance(opp_id, "negotiation", "rep1")
        self.assertEqual(snapshot(crm), before)

    def test_failed_advance_from_final_stage_changes_nothing(self):
        crm = make_crm(cap1=5)
        lead_id = crm.add_lead("a@corp.io", "A", "referral", "rep1")
        crm.qualify(lead_id, "rep1")
        opp_id = crm.convert(lead_id, 100, "rep1")
        crm.advance(opp_id, "lost", "rep1")
        before = snapshot(crm)
        with self.assertRaises(ValueError):
            crm.advance(opp_id, "prospect", "rep1")
        self.assertEqual(snapshot(crm), before)

    def test_failed_discount_changes_nothing(self):
        self.assert_atomic(
            lambda: self.crm.discount(self.opp_id, 11, "rep1"), PermissionError
        )
        self.assert_atomic(
            lambda: self.crm.discount(self.opp_id, 0, "rep1"), ValueError
        )
        self.assert_atomic(
            lambda: self.crm.discount(self.opp_id, 31, "boss"), ValueError
        )
        self.assert_atomic(
            lambda: self.crm.discount(self.opp_id, 5, "rep2"), PermissionError
        )

    def test_failed_cumulative_discount_changes_nothing(self):
        self.crm.discount(self.opp_id, 30, "boss")
        self.assert_atomic(
            lambda: self.crm.discount(self.opp_id, 1, "boss"), ValueError
        )

    def test_failed_discount_on_final_stage_changes_nothing(self):
        crm = make_crm(cap1=5)
        lead_id = crm.add_lead("a@corp.io", "A", "referral", "rep1")
        crm.qualify(lead_id, "rep1")
        opp_id = crm.convert(lead_id, 100, "rep1")
        for stage in ("proposal", "negotiation", "won"):
            crm.advance(opp_id, stage, "rep1")
        before = snapshot(crm)
        with self.assertRaises(ValueError):
            crm.discount(opp_id, 5, "boss")
        self.assertEqual(snapshot(crm), before)

    def test_failed_transfer_changes_nothing(self):
        self.assert_atomic(
            lambda: self.crm.transfer(self.opp_id, "rep2", "rep1"), PermissionError
        )
        self.assert_atomic(
            lambda: self.crm.transfer(self.opp_id, "rep1", "boss"), ValueError
        )
        self.assert_atomic(
            lambda: self.crm.transfer(self.opp_id, "boss", "boss"), ValueError
        )
        self.assert_atomic(
            lambda: self.crm.transfer(self.opp_id, "rep2", "boss"), ValueError
        )
        self.assert_atomic(
            lambda: self.crm.transfer("O404", "rep2", "boss"), ValueError
        )

    def test_failed_transfer_on_final_stage_changes_nothing(self):
        crm = make_crm(cap1=5, cap2=5)
        lead_id = crm.add_lead("a@corp.io", "A", "referral", "rep1")
        crm.qualify(lead_id, "rep1")
        opp_id = crm.convert(lead_id, 100, "rep1")
        crm.advance(opp_id, "lost", "rep1")
        before = snapshot(crm)
        with self.assertRaises(ValueError):
            crm.transfer(opp_id, "rep2", "boss")
        self.assertEqual(snapshot(crm), before)

    def test_successful_calls_only_append_the_named_entries(self):
        self.assertEqual(
            [entry[0] for entry in self.crm.log],
            ["add_lead", "qualify", "convert", "add_lead"],
        )
        self.crm.advance(self.opp_id, "lost", "rep1")
        self.assertEqual(self.crm.log[-2], ("advance", self.opp_id, "rep1"))
        self.assertEqual(self.crm.log[-1], ("assign", self.queued_id, "system"))
        self.assertEqual(len(self.crm.log), 6)


if __name__ == "__main__":
    unittest.main()
