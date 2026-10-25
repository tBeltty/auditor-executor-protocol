"""Conformance tests for clauses the main suite leaves untested.

Each test is derived directly from /tmp/aep-lab/specs/crm.md: exception
ordering, load accounting, queue FIFO, score boundaries and forecast flooring.
"""

import unittest

from crm import CRM, DuplicateLeadError


def reps():
    return [
        {"id": "r1", "role": "rep", "capacity": 2},
        {"id": "r2", "role": "rep", "capacity": 2},
        {"id": "m1", "role": "manager", "capacity": 0},
    ]


def one_rep(capacity=1):
    return [
        {"id": "r1", "role": "rep", "capacity": capacity},
        {"id": "m1", "role": "manager", "capacity": 0},
    ]


class Base(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(reps())

    def qualified(self, email="lead@corp.com", actor="r1", source="referral"):
        lead_id = self.crm.add_lead(email, "Lead", source, actor)
        self.crm.qualify(lead_id, "m1")
        return lead_id

    def opp(self, amount=1000):
        lead_id = self.qualified()
        return self.crm.convert(lead_id, amount, "r1")


class ExceptionOrderingTests(Base):
    """Spec line 10: checks run in the listed order; first failure decides."""

    def test_source_is_checked_before_duplicate_email(self):
        self.crm.add_lead("dup@corp.com", "A", "web", "m1")
        with self.assertRaises(ValueError) as ctx:
            self.crm.add_lead("DUP@corp.com", "B", "bogus", "m1")
        self.assertNotIsInstance(ctx.exception, DuplicateLeadError)

    def test_name_is_checked_before_duplicate_email(self):
        self.crm.add_lead("dup@corp.com", "A", "web", "m1")
        with self.assertRaises(ValueError) as ctx:
            self.crm.add_lead("DUP@corp.com", "   ", "web", "m1")
        self.assertNotIsInstance(ctx.exception, DuplicateLeadError)

    def test_convert_permission_is_checked_before_status(self):
        lead_id = self.crm.add_lead("a@corp.com", "A", "referral", "r1")
        # Lead is still "new": rule 3 (permission) must win over rule 4 (status).
        with self.assertRaises(PermissionError):
            self.crm.convert(lead_id, 100, "r2")

    def test_discount_final_stage_is_checked_before_rep_limit(self):
        opp_id = self.opp()
        self.crm.advance(opp_id, "lost", "r1")
        # Rule 4 (final stage) must win over rule 5 (rep pct limit).
        with self.assertRaises(ValueError) as ctx:
            self.crm.discount(opp_id, 11, "r1")
        self.assertNotIsInstance(ctx.exception, PermissionError)

    def test_advance_permission_is_checked_before_final_stage(self):
        opp_id = self.opp()
        self.crm.advance(opp_id, "lost", "r1")
        with self.assertRaises(PermissionError):
            self.crm.advance(opp_id, "won", "r2")

    def test_transfer_target_must_be_rep_before_same_owner_check(self):
        opp_id = self.opp()
        with self.assertRaises(ValueError):
            self.crm.transfer(opp_id, "m1", "m1")

    def test_qualify_unowned_lead_rejects_non_manager(self):
        crm = CRM([{"id": "m1", "role": "manager", "capacity": 0},
                   {"id": "r1", "role": "rep", "capacity": 0}])
        lead_id = crm.add_lead("a@corp.com", "A", "referral", "m1")
        self.assertIsNone(crm.leads[lead_id]["owner"])
        with self.assertRaises(PermissionError):
            crm.qualify(lead_id, "r1")
        crm.qualify(lead_id, "m1")

    def test_convert_unowned_lead_owner_check_after_permission(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 0},
                   {"id": "m1", "role": "manager", "capacity": 0}])
        lead_id = crm.add_lead("a@corp.com", "A", "referral", "m1")
        crm.qualify(lead_id, "m1")
        self.assertIsNone(crm.leads[lead_id]["owner"])
        with self.assertRaises(PermissionError):
            crm.convert(lead_id, 100, "r1")
        with self.assertRaises(ValueError):
            crm.convert(lead_id, 100, "m1")


class LoadAccountingTests(Base):
    """Spec line 9: load = new/qualified leads + non-final opportunities."""

    def test_converted_lead_is_not_double_counted_with_its_opportunity(self):
        crm = CRM(one_rep(capacity=2))
        lead_id = crm.add_lead("a@corp.com", "A", "referral", "r1")
        crm.qualify(lead_id, "r1")
        crm.convert(lead_id, 100, "r1")
        # Load is 1 (the opportunity only), so the next lead still fits.
        second = crm.add_lead("b@corp.com", "B", "referral", "m1")
        self.assertEqual(crm.leads[second]["owner"], "r1")

    def test_final_opportunity_frees_a_slot(self):
        crm = CRM(one_rep(capacity=1))
        lead_id = crm.add_lead("a@corp.com", "A", "referral", "r1")
        crm.qualify(lead_id, "r1")
        opp_id = crm.convert(lead_id, 100, "r1")
        waiting = crm.add_lead("b@corp.com", "B", "referral", "m1")
        self.assertIsNone(crm.leads[waiting]["owner"])
        crm.advance(opp_id, "lost", "r1")
        self.assertEqual(crm.leads[waiting]["owner"], "r1")

    def test_qualifying_a_lead_does_not_free_its_slot(self):
        crm = CRM(one_rep(capacity=1))
        lead_id = crm.add_lead("a@corp.com", "A", "referral", "r1")
        crm.qualify(lead_id, "r1")
        waiting = crm.add_lead("b@corp.com", "B", "referral", "m1")
        self.assertIsNone(crm.leads[waiting]["owner"])


class QueueTests(Base):
    """Spec line 18/31: FIFO waiting queue, "system" assign entries."""

    def test_waiting_lead_logs_only_add_lead(self):
        crm = CRM(one_rep(capacity=1))
        crm.add_lead("a@corp.com", "A", "referral", "r1")
        crm.add_lead("b@corp.com", "B", "referral", "m1")
        self.assertEqual(crm.log[-1], ("add_lead", "L2", "m1"))

    def test_queue_is_fifo_across_successive_freed_slots(self):
        crm = CRM(one_rep(capacity=1))
        first = crm.add_lead("a@corp.com", "A", "referral", "r1")
        crm.qualify(first, "r1")
        opp1 = crm.convert(first, 100, "r1")
        q1 = crm.add_lead("b@corp.com", "B", "referral", "m1")
        q2 = crm.add_lead("c@corp.com", "C", "referral", "m1")
        self.assertIsNone(crm.leads[q1]["owner"])
        self.assertIsNone(crm.leads[q2]["owner"])

        crm.advance(opp1, "lost", "r1")
        self.assertEqual(crm.leads[q1]["owner"], "r1")
        self.assertIsNone(crm.leads[q2]["owner"])
        self.assertEqual(crm.log[-1], ("assign", q1, "system"))

        crm.qualify(q1, "r1")
        opp2 = crm.convert(q1, 100, "r1")
        crm.advance(opp2, "lost", "r1")
        self.assertEqual(crm.leads[q2]["owner"], "r1")
        self.assertEqual(crm.log[-1], ("assign", q2, "system"))

    def test_qualified_waiting_lead_keeps_status_when_assigned(self):
        crm = CRM(one_rep(capacity=1))
        first = crm.add_lead("a@corp.com", "A", "referral", "r1")
        crm.qualify(first, "r1")
        opp_id = crm.convert(first, 100, "r1")
        waiting = crm.add_lead("b@corp.com", "B", "referral", "m1")
        crm.qualify(waiting, "m1")
        self.assertEqual(crm.leads[waiting]["status"], "qualified")
        crm.advance(opp_id, "lost", "r1")
        self.assertEqual(crm.leads[waiting]["owner"], "r1")
        self.assertEqual(crm.leads[waiting]["status"], "qualified")


class ScoreBoundaryTests(Base):
    """Spec line 17/22: score 30 is the qualify threshold."""

    def test_referral_on_free_domain_scores_exactly_30_and_qualifies(self):
        lead_id = self.crm.add_lead("a@gmail.com", "A", "referral", "r1")
        self.assertEqual(self.crm.leads[lead_id]["score"], 30)
        self.crm.qualify(lead_id, "r1")
        self.assertEqual(self.crm.leads[lead_id]["status"], "qualified")

    def test_web_on_corporate_domain_scores_25_and_cannot_qualify(self):
        lead_id = self.crm.add_lead("a@corp.com", "A", "web", "r1")
        self.assertEqual(self.crm.leads[lead_id]["score"], 25)
        with self.assertRaises(ValueError):
            self.crm.qualify(lead_id, "r1")


class ForecastFlooringTests(Base):
    def test_weighted_floors_each_opportunity_before_summing(self):
        for email, amount in [("a@corp.com", 101), ("b@corp.com", 202)]:
            lead_id = self.crm.add_lead(email, "X", "referral", "m1")
            self.crm.qualify(lead_id, "m1")
            opp_id = self.crm.convert(lead_id, amount, "m1")
            self.crm.advance(opp_id, "proposal", "m1")
        # 101 * 30 // 100 = 30 and 202 * 30 // 100 = 60 (not 90.9 floored).
        self.assertEqual(self.crm.forecast(), {"open": 2, "weighted": 90, "won": 0})


if __name__ == "__main__":
    unittest.main()
