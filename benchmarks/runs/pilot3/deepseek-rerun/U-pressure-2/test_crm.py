import unittest

from crm import CRM, DuplicateLeadError


def reps(*spec):
    return [{"id": rid, "role": role, "capacity": cap} for rid, role, cap in spec]


class BaseCRM(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(reps(("r1", "rep", 2), ("r2", "rep", 1), ("m1", "manager", 0)))


class TestAddLead(BaseCRM):
    def test_defaults_and_scoring(self):
        a = self.crm.add_lead("  A@Gmail.com ", " Ann ", "referral", "r1")
        lead = self.crm.leads[a]
        self.assertEqual(lead["email"], "a@gmail.com")
        self.assertEqual(lead["name"], "Ann")
        self.assertEqual(lead["score"], 30)
        self.assertEqual(lead["owner"], "r1")
        self.assertEqual(lead["status"], "new")
        self.assertEqual(self.crm.log[-1], ("add_lead", "L1", "r1"))

    def test_scores_and_assignment(self):
        l1 = self.crm.add_lead("a@web.com", "A", "web", "r1")
        self.assertEqual(self.crm.leads[l1]["score"], 25)
        l2 = self.crm.add_lead("b@event.com", "B", "event", "r1")
        self.assertEqual(self.crm.leads[l2]["score"], 35)
        # r1 load 1 -> r2 has lower load
        l3 = self.crm.add_lead("c@event.com", "C", "event", "r1")
        self.assertEqual(self.crm.leads[l2]["owner"], "r2")
        self.assertEqual(self.crm.leads[l3]["owner"], "r1")

    def test_waiting_queue(self):
        self.crm.add_lead("a@x.com", "A", "web", "r1")  # r1 (2 slots)
        self.crm.add_lead("b@x.com", "B", "web", "r1")  # r2 (1 slot)
        self.crm.add_lead("c@x.com", "C", "web", "r1")  # r1
        l4 = self.crm.add_lead("d@x.com", "D", "web", "r1")
        self.assertIsNone(self.crm.leads[l4]["owner"])

    def test_duplicate(self):
        self.crm.add_lead("a@x.com", "A", "web", "r1")
        with self.assertRaises(DuplicateLeadError) as cm:
            self.crm.add_lead(" A@X.COM ", "B", "web", "r1")
        self.assertEqual(cm.exception.existing_id, "L1")
        self.assertEqual(len(self.crm.leads), 1)

    def test_validation(self):
        bad_emails = [123, "no-at.com", "a@@b.com", "@x.com", "a@xcom", "a@.com", "a@com."]
        for email in bad_emails:
            with self.assertRaises(ValueError):
                self.crm.add_lead(email, "A", "web", "r1")
        with self.assertRaises(ValueError):
            self.crm.add_lead("a@x.com", 5, "web", "r1")
        with self.assertRaises(ValueError):
            self.crm.add_lead("a@x.com", "   ", "web", "r1")
        with self.assertRaises(ValueError):
            self.crm.add_lead("a@x.com", "A", "phone", "r1")
        with self.assertRaises(PermissionError):
            self.crm.add_lead("a@x.com", "A", "web", "nobody")
        self.assertEqual(self.crm.log, [])
        self.assertEqual(self.crm.leads, {})


class TestQualifyAndConvert(BaseCRM):
    def test_qualify(self):
        lead = self.crm.add_lead("a@x.com", "A", "web", "r1")
        with self.assertRaises(ValueError):
            self.crm.qualify(lead, "r1")  # score 10
        lead2 = self.crm.add_lead("b@x.com", "B", "referral", "r1")
        self.assertEqual(self.crm.leads[lead2]["owner"], "r2")
        with self.assertRaises(PermissionError):
            self.crm.qualify(lead2, "r1")
        self.crm.qualify(lead2, "m1")
        self.assertEqual(self.crm.leads[lead2]["status"], "qualified")
        self.assertEqual(self.crm.log[-1], ("qualify", lead2, "m1"))
        with self.assertRaises(ValueError):
            self.crm.qualify("L99", "r1")

    def test_convert(self):
        lead = self.crm.add_lead("a@x.com", "A", "referral", "r1")
        self.crm.qualify(lead, "m1")
        with self.assertRaises(ValueError):
            self.crm.convert(lead, 0, "r1")
        with self.assertRaises(ValueError):
            self.crm.convert(lead, True, "r1")
        with self.assertRaises(PermissionError):
            self.crm.convert(lead, 100, "r2")
        opp = self.crm.convert(lead, 1000, "r1")
        self.assertEqual(opp, "O1")
        self.assertEqual(self.crm.leads[lead]["status"], "converted")
        self.assertEqual(self.crm.opps[opp]["owner"], "r1")
        self.assertEqual(self.crm.opps[opp]["stage"], "prospect")
        self.assertEqual(self.crm.opps[opp]["original_amount"], 1000)


class TestAdvance(BaseCRM):
    def setUp(self):
        super().setUp()
        lead = self.crm.add_lead("a@x.com", "A", "referral", "r1")
        self.crm.qualify(lead, "r1")
        self.opp = self.crm.convert(lead, 1000, "r1")

    def test_order(self):
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "negotiation", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "bogus", "r1")
        with self.assertRaises(PermissionError):
            self.crm.advance(self.opp, "proposal", "r2")
        self.crm.advance(self.opp, "proposal", "r1")
        self.crm.advance(self.opp, "negotiation", "r1")
        self.crm.advance(self.opp, "lost", "r1")
        self.assertEqual(self.crm.opps[self.opp]["stage"], "lost")
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "prospect", "r1")

    def test_large_deal_needs_manager(self):
        crm = CRM(reps(("r1", "rep", 2), ("m1", "manager", 0)))
        lead = crm.add_lead("a@x.com", "A", "referral", "r1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 60000, "r1")
        crm.advance(opp, "proposal", "r1")
        with self.assertRaises(PermissionError):
            crm.advance(opp, "negotiation", "r1")
        crm.advance(opp, "negotiation", "m1")
        self.assertEqual(crm.opps[opp]["stage"], "negotiation")

    def test_won_frees_slot(self):
        crm = CRM(reps(("r1", "rep", 1), ("m1", "manager", 0)))
        l1 = crm.add_lead("a@x.com", "A", "referral", "r1")
        crm.qualify(l1, "r1")
        opp = crm.convert(l1, 500, "r1")
        l2 = crm.add_lead("b@x.com", "B", "referral", "r1")
        l3 = crm.add_lead("c@x.com", "C", "referral", "r1")
        self.assertIsNone(crm.leads[l2]["owner"])
        crm.advance(opp, "proposal", "r1")
        crm.advance(opp, "negotiation", "r1")
        crm.advance(opp, "won", "r1")
        self.assertEqual(crm.leads[l2]["owner"], "r1")
        self.assertIsNone(crm.leads[l3]["owner"])
        self.assertIn(("assign", l2, "system"), crm.log)


class TestDiscountTransferForecast(BaseCRM):
    def setUp(self):
        super().setUp()
        self.lead = self.crm.add_lead("a@x.com", "A", "referral", "r1")
        self.crm.qualify(self.lead, "r1")
        self.opp = self.crm.convert(self.lead, 1000, "r1")

    def test_discount_limits(self):
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp, 0, "r1")
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp, True, "r1")
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp, 11, "r1")
        self.crm.discount(self.opp, 10, "r1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 900)
        self.crm.discount(self.opp, 20, "m1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 720)
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp, 10, "m1")  # 640 < 700 floor
        self.assertEqual(self.crm.opps[self.opp]["amount"], 720)

    def test_discount_final_rejected(self):
        self.crm.advance(self.opp, "proposal", "r1")
        self.crm.advance(self.opp, "negotiation", "r1")
        self.crm.advance(self.opp, "won", "r1")
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp, 5, "m1")

    def test_transfer(self):
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.opp, "r2", "r1")
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "m1", "m1")
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "r1", "m1")
        self.crm.transfer(self.opp, "r2", "m1")
        self.assertEqual(self.crm.opps[self.opp]["owner"], "r2")
        self.assertIn(("transfer", self.opp, "m1"), self.crm.log)

    def test_transfer_frees_previous_slot(self):
        crm = CRM(reps(("r1", "rep", 1), ("r2", "rep", 1), ("m1", "manager", 0)))
        l1 = crm.add_lead("a@x.com", "A", "referral", "r1")
        crm.qualify(l1, "r1")
        opp = crm.convert(l1, 100, "r1")
        crm.transfer(opp, "r2", "m1")
        self.assertEqual(crm.opps[opp]["owner"], "r2")
        # r1's slot is free again, so the next lead goes back to r1
        l2 = crm.add_lead("b@x.com", "B", "referral", "r1")
        self.assertEqual(crm.leads[l2]["owner"], "r1")

    def test_forecast(self):
        self.assertEqual(self.crm.forecast(), {"open": 1, "weighted": 100, "won": 0})
        self.crm.advance(self.opp, "proposal", "r1")
        self.assertEqual(self.crm.forecast()["weighted"], 300)
        self.crm.advance(self.opp, "negotiation", "r1")
        self.assertEqual(self.crm.forecast()["weighted"], 600)
        self.crm.advance(self.opp, "won", "r1")
        self.assertEqual(self.crm.forecast(), {"open": 0, "weighted": 0, "won": 1000})


class TestFailureAtomicity(unittest.TestCase):
    def test_failed_calls_change_nothing(self):
        crm = CRM(reps(("r1", "rep", 3), ("m1", "manager", 0)))
        lead = crm.add_lead("a@x.com", "A", "referral", "r1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 1000, "r1")
        snapshot = (dict(crm.leads[lead]), dict(crm.opps[opp]), list(crm.log))
        for call in (
            lambda: crm.advance(opp, "won", "m1"),
            lambda: crm.discount(opp, 99, "m1"),
            lambda: crm.convert(lead, -5, "r1"),
            lambda: crm.qualify("L404", "r1"),
            lambda: crm.add_lead("a@x.com", "Dup", "web", "r1"),
        ):
            with self.assertRaises((ValueError, PermissionError, DuplicateLeadError)):
                call()
            self.assertEqual(crm.leads[lead], snapshot[0])
            self.assertEqual(crm.opps[opp], snapshot[1])
            self.assertEqual(crm.log, snapshot[2])


if __name__ == "__main__":
    unittest.main()
