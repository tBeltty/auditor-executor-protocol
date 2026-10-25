import unittest

from crm import CRM, DuplicateLeadError


def make_crm():
    return CRM(
        [
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 2},
            {"id": "m1", "role": "manager", "capacity": 0},
        ]
    )


class TestAddLead(unittest.TestCase):
    def test_normalizes_scores_and_assigns_lowest_load(self):
        crm = make_crm()
        lead_id = crm.add_lead("  Bob@Gmail.com ", " Bob ", "web", "m1")
        self.assertEqual(lead_id, "L1")
        lead = crm.leads[lead_id]
        self.assertEqual(lead["email"], "bob@gmail.com")
        self.assertEqual(lead["name"], "Bob")
        self.assertEqual(lead["score"], 10)
        self.assertEqual(lead["status"], "new")
        self.assertEqual(lead["owner"], "r1")
        self.assertEqual(crm.log, [("add_lead", "L1", "m1")])

        second = crm.add_lead("a@corp.io", "A", "referral", "r1")
        self.assertEqual(crm.leads[second]["score"], 45)
        self.assertEqual(crm.leads[second]["owner"], "r2")

    def test_waiting_queue_when_all_full(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1}])
        first = crm.add_lead("a@gmail.com", "A", "web", "r1")
        second = crm.add_lead("b@gmail.com", "B", "web", "r1")
        self.assertEqual(crm.leads[first]["owner"], "r1")
        self.assertIsNone(crm.leads[second]["owner"])

    def test_validation_and_duplicate(self):
        crm = make_crm()
        for bad in (123, "no-at", "@gmail.com", "a@b", "a@.com", "a@com.", "a@b@c.com"):
            with self.assertRaises(ValueError, msg=bad):
                crm.add_lead(bad, "N", "web", "r1")
        with self.assertRaises(ValueError):
            crm.add_lead("x@y.com", "   ", "web", "r1")
        with self.assertRaises(ValueError):
            crm.add_lead("x@y.com", "N", "ads", "r1")
        with self.assertRaises(PermissionError):
            crm.add_lead("x@y.com", "N", "web", "ghost")
        crm.add_lead("x@y.com", "N", "web", "r1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            crm.add_lead("X@Y.com", "N", "web", "r1")
        self.assertEqual(ctx.exception.existing_id, "L1")
        self.assertEqual(len(crm.leads), 1)
        self.assertEqual(len(crm.log), 1)


class TestQualifyConvert(unittest.TestCase):
    def test_qualify_path(self):
        crm = make_crm()
        low = crm.add_lead("a@gmail.com", "A", "web", "r1")
        with self.assertRaises(ValueError):
            crm.qualify(low, "r1")  # score 10
        with self.assertRaises(ValueError):
            crm.qualify("L99", "r1")
        good = crm.add_lead("b@corp.io", "B", "event", "r2")
        with self.assertRaises(PermissionError):
            crm.qualify(good, "r1")
        crm.qualify(good, "r2")
        self.assertEqual(crm.leads[good]["status"], "qualified")
        with self.assertRaises(ValueError):
            crm.qualify(good, "r2")
        self.assertEqual(crm.log[-1], ("qualify", good, "r2"))

    def test_convert_rules_and_opp(self):
        crm = make_crm()
        lead_id = crm.add_lead("b@corp.io", "B", "referral", "r1")
        with self.assertRaises(ValueError):
            crm.convert(lead_id, 100, "r1")  # not qualified
        crm.qualify(lead_id, "r1")
        for bad in (0, -5, True, 1.5, "100"):
            with self.assertRaises(ValueError):
                crm.convert(lead_id, bad, "r1")
        with self.assertRaises(PermissionError):
            crm.convert(lead_id, 100, "r2")
        opp_id = crm.convert(lead_id, 1000, "m1")
        self.assertEqual(opp_id, "O1")
        opp = crm.opps[opp_id]
        self.assertEqual(opp["owner"], "r1")
        self.assertEqual(opp["stage"], "prospect")
        self.assertEqual(opp["original_amount"], 1000)
        self.assertEqual(crm.leads[lead_id]["status"], "converted")
        with self.assertRaises(ValueError):
            crm.convert(lead_id, 100, "r1")


class TestAdvanceDiscountTransfer(unittest.TestCase):
    def _qualified_opp(self, amount=1000, owner="r1"):
        crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 2},
                {"id": "r2", "role": "rep", "capacity": 2},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        lead_id = crm.add_lead("b@corp.io", "B", "referral", owner)
        crm.qualify(lead_id, "m1")
        opp_id = crm.convert(lead_id, amount, "m1")
        return crm, opp_id

    def test_advance_stage_order_and_final(self):
        crm, opp = self._qualified_opp()
        with self.assertRaises(ValueError):
            crm.advance(opp, "negotiation", "r1")  # skips proposal
        with self.assertRaises(ValueError):
            crm.advance(opp, "bogus", "r1")
        with self.assertRaises(PermissionError):
            crm.advance(opp, "proposal", "r2")
        crm.advance(opp, "proposal", "r1")
        crm.advance(opp, "negotiation", "r1")
        crm.advance(opp, "won", "r1")
        self.assertEqual(crm.opps[opp]["stage"], "won")
        with self.assertRaises(ValueError):
            crm.advance(opp, "lost", "m1")

    def test_negotiation_over_50k_needs_manager(self):
        crm, opp = self._qualified_opp(amount=60000)
        crm.advance(opp, "proposal", "r1")
        with self.assertRaises(PermissionError):
            crm.advance(opp, "negotiation", "r1")
        crm.advance(opp, "negotiation", "m1")
        self.assertEqual(crm.opps[opp]["stage"], "negotiation")

    def test_advance_frees_slot_and_assigns_oldest_waiting(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1}])
        lead = crm.add_lead("a@corp.io", "A", "referral", "r1")
        waiting = crm.add_lead("b@corp.io", "B", "referral", "r1")
        self.assertIsNone(crm.leads[waiting]["owner"])
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 100, "r1")
        crm.advance(opp, "lost", "r1")
        self.assertEqual(crm.leads[waiting]["owner"], "r1")
        self.assertEqual(crm.log[-1], ("assign", waiting, "system"))

    def test_discount_rules(self):
        crm, opp = self._qualified_opp(amount=1000)
        for bad in (0, 31, True, 5.0):
            with self.assertRaises(ValueError):
                crm.discount(opp, bad, "m1")
        with self.assertRaises(PermissionError):
            crm.discount(opp, 5, "r2")
        with self.assertRaises(PermissionError):
            crm.discount(opp, 11, "r1")
        crm.discount(opp, 10, "r1")
        self.assertEqual(crm.opps[opp]["amount"], 900)
        with self.assertRaises(ValueError):
            crm.discount(opp, 30, "m1")  # cumulative would exceed 30%
        crm.discount(opp, 22, "m1")
        self.assertEqual(crm.opps[opp]["amount"], 702)
        crm.advance(opp, "proposal", "m1")
        crm.advance(opp, "negotiation", "m1")
        crm.advance(opp, "won", "m1")
        with self.assertRaises(ValueError):
            crm.discount(opp, 1, "m1")
        self.assertEqual(crm.log[-1], ("advance", opp, "m1"))

    def test_transfer(self):
        crm, opp = self._qualified_opp()
        with self.assertRaises(PermissionError):
            crm.transfer(opp, "r2", "r1")
        with self.assertRaises(ValueError):
            crm.transfer(opp, "m1", "m1")
        with self.assertRaises(ValueError):
            crm.transfer(opp, "nobody", "m1")
        with self.assertRaises(ValueError):
            crm.transfer(opp, "r1", "m1")
        crm.transfer(opp, "r2", "m1")
        self.assertEqual(crm.opps[opp]["owner"], "r2")
        self.assertEqual(crm.log[-1], ("transfer", opp, "m1"))

    def test_transfer_to_full_rep_rejected(self):
        crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 1},
                {"id": "r2", "role": "rep", "capacity": 1},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        lead = crm.add_lead("a@corp.io", "A", "referral", "r1")
        crm.add_lead("b@corp.io", "B", "referral", "r1")  # fills r2
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 100, "r1")
        with self.assertRaises(ValueError):
            crm.transfer(opp, "r2", "m1")
        self.assertEqual(crm.opps[opp]["owner"], "r1")
        self.assertEqual(len(crm.log), 4)

    def test_forecast(self):
        crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 5},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        self.assertEqual(crm.forecast(), {"open": 0, "weighted": 0, "won": 0})
        opps = []
        for i, amount in enumerate((1000, 2000, 3000)):
            lead = crm.add_lead("a%d@corp.io" % i, "A", "referral", "r1")
            crm.qualify(lead, "r1")
            opps.append(crm.convert(lead, amount, "r1"))
        crm.advance(opps[0], "proposal", "r1")
        crm.advance(opps[1], "proposal", "r1")
        crm.advance(opps[1], "negotiation", "r1")
        crm.advance(opps[2], "proposal", "r1")
        crm.advance(opps[2], "negotiation", "r1")
        crm.advance(opps[2], "won", "r1")
        self.assertEqual(
            crm.forecast(), {"open": 2, "weighted": 300 + 1200, "won": 3000}
        )
        before = len(crm.log)
        crm.forecast()
        self.assertEqual(len(crm.log), before)


if __name__ == "__main__":
    unittest.main()
