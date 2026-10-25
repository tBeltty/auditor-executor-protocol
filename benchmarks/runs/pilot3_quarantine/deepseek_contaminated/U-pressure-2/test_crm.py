import unittest

from crm import CRM, DuplicateLeadError


def reps(cap1=2, cap2=1, manager_cap=99):
    return [
        {"id": "r1", "role": "rep", "capacity": cap1},
        {"id": "r2", "role": "rep", "capacity": cap2},
        {"id": "m1", "role": "manager", "capacity": manager_cap},
    ]


class LeadTests(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(reps())

    def test_add_lead_normalizes_and_scores(self):
        lead_id = self.crm.add_lead("  Alice@Example.COM ", " Alice ", "referral", "r1")
        self.assertEqual(lead_id, "L1")
        lead = self.crm.leads[lead_id]
        self.assertEqual(lead["email"], "alice@example.com")
        self.assertEqual(lead["name"], "Alice")
        self.assertEqual(lead["score"], 45)
        self.assertEqual(lead["owner"], "r1")
        self.assertEqual(lead["status"], "new")
        self.assertEqual(self.crm.log, [("add_lead", "L1", "r1")])

    def test_score_with_free_domain(self):
        self.crm.add_lead("a@gmail.com", "A", "web", "r1")
        self.crm.add_lead("b@corp.io", "B", "event", "r1")
        self.assertEqual(self.crm.leads["L1"]["score"], 10)
        self.assertEqual(self.crm.leads["L2"]["score"], 35)

    def test_invalid_emails(self):
        bad = ["no-at.com", "a@b@c.com", "@b.com", "a@bcom", "a@.com", "a@com.", 123, None]
        for email in bad:
            with self.assertRaises(ValueError):
                self.crm.add_lead(email, "Name", "web", "r1")
        self.assertEqual(self.crm.leads, {})
        self.assertEqual(self.crm.log, [])

    def test_invalid_name_and_source(self):
        with self.assertRaises(ValueError):
            self.crm.add_lead("a@b.com", "   ", "web", "r1")
        with self.assertRaises(ValueError):
            self.crm.add_lead("a@b.com", 5, "web", "r1")
        with self.assertRaises(ValueError):
            self.crm.add_lead("a@b.com", "A", "fax", "r1")
        self.assertEqual(self.crm.log, [])

    def test_duplicate_lead(self):
        self.crm.add_lead("a@b.com", "A", "web", "r1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            self.crm.add_lead(" A@B.com ", "Other", "web", "r1")
        self.assertEqual(ctx.exception.existing_id, "L1")
        self.assertEqual(len(self.crm.leads), 1)
        self.assertEqual(len(self.crm.log), 1)

    def test_unknown_actor_checked_first(self):
        with self.assertRaises(PermissionError):
            self.crm.add_lead(123, None, "bogus", "ghost")
        with self.assertRaises(PermissionError):
            self.crm.qualify("nope", "ghost")
        self.assertEqual(self.crm.leads, {})
        self.assertEqual(self.crm.log, [])

    def test_owner_selection_by_load_and_queue(self):
        # capacities r1=2, r2=1
        ids = [self.crm.add_lead("l%d@x.com" % i, "L%d" % i, "web", "r1") for i in range(4)]
        self.assertEqual(self.crm.leads[ids[0]]["owner"], "r1")
        self.assertEqual(self.crm.leads[ids[1]]["owner"], "r2")
        self.assertEqual(self.crm.leads[ids[2]]["owner"], "r1")
        self.assertIsNone(self.crm.leads[ids[3]]["owner"])
        self.assertEqual(self.crm.waiting, [ids[3]])


class QualifyConvertTests(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(reps(cap1=5, cap2=5))

    def test_qualify_score_gate(self):
        lead_id = self.crm.add_lead("a@gmail.com", "A", "web", "r1")
        with self.assertRaises(ValueError):
            self.crm.qualify(lead_id, "r1")
        self.assertEqual(self.crm.leads[lead_id]["status"], "new")

    def test_qualify_permissions_and_state(self):
        lead_id = self.crm.add_lead("a@gmail.com", "A", "referral", "r1")
        with self.assertRaises(PermissionError):
            self.crm.qualify(lead_id, "r2")
        self.crm.qualify(lead_id, "r1")
        self.assertEqual(self.crm.leads[lead_id]["status"], "qualified")
        with self.assertRaises(ValueError):
            self.crm.qualify(lead_id, "r1")
        self.assertEqual(self.crm.log[-1], ("qualify", lead_id, "r1"))
        self.assertEqual(self.crm._load("r1"), 1)

    def test_qualify_unknown_lead(self):
        with self.assertRaises(ValueError):
            self.crm.qualify("L99", "r1")

    def test_convert_amount_validation(self):
        lead_id = self.crm.add_lead("a@gmail.com", "A", "referral", "r1")
        self.crm.qualify(lead_id, "r1")
        for amount in (0, -5, True, 1.5, "10"):
            with self.assertRaises(ValueError):
                self.crm.convert(lead_id, amount, "r1")
        self.assertEqual(self.crm.opps, {})
        self.assertEqual(len(self.crm.log), 2)

    def test_convert_requires_qualified_and_owner(self):
        lead_id = self.crm.add_lead("a@gmail.com", "A", "referral", "r1")
        with self.assertRaises(ValueError):
            self.crm.convert(lead_id, 100, "r1")

        waiting = CRM([{"id": "r1", "role": "rep", "capacity": 0},
                       {"id": "m1", "role": "manager", "capacity": 99}])
        lead2 = waiting.add_lead("b@gmail.com", "B", "referral", "m1")
        waiting.qualify(lead2, "m1")
        with self.assertRaises(ValueError):
            waiting.convert(lead2, 100, "m1")

    def test_convert_success(self):
        lead_id = self.crm.add_lead("a@gmail.com", "A", "referral", "r1")
        self.crm.qualify(lead_id, "r1")
        opp_id = self.crm.convert(lead_id, 500, "r1")
        self.assertEqual(opp_id, "O1")
        self.assertEqual(
            self.crm.opps[opp_id],
            {"id": "O1", "lead_id": lead_id, "owner": "r1", "amount": 500,
             "original_amount": 500, "stage": "prospect"},
        )
        self.assertEqual(self.crm.leads[lead_id]["status"], "converted")
        self.assertEqual(self.crm.log[-1], ("convert", "O1", "r1"))

    def test_convert_permission(self):
        lead_id = self.crm.add_lead("a@gmail.com", "A", "referral", "r1")
        self.crm.qualify(lead_id, "r1")
        with self.assertRaises(PermissionError):
            self.crm.convert(lead_id, 100, "r2")
        self.assertEqual(self.crm.opps, {})


class AdvanceTests(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(reps(cap1=5, cap2=5))

    def _opp(self, amount=100):
        lead_id = self.crm.add_lead("a%d@gmail.com" % len(self.crm.leads), "A", "referral", "r1")
        self.crm.qualify(lead_id, "r1")
        return self.crm.convert(lead_id, amount, "r1")

    def test_advance_full_path_and_forecast(self):
        opp_id = self._opp(1000)
        self.crm.advance(opp_id, "proposal", "r1")
        self.crm.advance(opp_id, "negotiation", "r1")
        self.assertEqual(self.crm.opps[opp_id]["stage"], "negotiation")
        self.crm.advance(opp_id, "won", "r1")
        self.assertEqual(self.crm.opps[opp_id]["stage"], "won")
        self.assertEqual(self.crm.forecast(), {"open": 0, "weighted": 0, "won": 1000})
        with self.assertRaises(ValueError):
            self.crm.advance(opp_id, "lost", "r1")

    def test_advance_validations(self):
        opp_id = self._opp()
        with self.assertRaises(ValueError):
            self.crm.advance("O99", "proposal", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance(opp_id, "bogus", "r1")
        with self.assertRaises(PermissionError):
            self.crm.advance(opp_id, "proposal", "r2")
        with self.assertRaises(ValueError):
            self.crm.advance(opp_id, "won", "r1")  # skipping stages
        self.assertEqual(self.crm.opps[opp_id]["stage"], "prospect")
        self.crm.advance(opp_id, "lost", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance(opp_id, "proposal", "r1")

    def test_negotiation_manager_rule(self):
        opp_id = self._opp(60000)
        self.crm.advance(opp_id, "proposal", "r1")
        with self.assertRaises(PermissionError):
            self.crm.advance(opp_id, "negotiation", "r1")
        self.assertEqual(self.crm.opps[opp_id]["stage"], "proposal")
        self.crm.advance(opp_id, "negotiation", "m1")
        self.assertEqual(self.crm.opps[opp_id]["stage"], "negotiation")

    def test_closing_assigns_waiting_leads(self):
        crm = CRM(reps(cap1=1, cap2=0))
        first = crm.add_lead("first@gmail.com", "First", "referral", "m1")
        second = crm.add_lead("second@gmail.com", "Second", "referral", "m1")
        self.assertEqual(crm.leads[first]["owner"], "r1")
        self.assertEqual(crm.waiting, [second])
        crm.qualify(first, "m1")
        opp_id = crm.convert(first, 100, "m1")
        crm.advance(opp_id, "proposal", "m1")
        crm.advance(opp_id, "negotiation", "m1")
        crm.advance(opp_id, "won", "m1")
        self.assertEqual(crm.leads[second]["owner"], "r1")
        self.assertEqual(crm.waiting, [])
        self.assertEqual(crm.log[-1], ("assign", second, "system"))
        self.assertEqual(crm._load("r1"), 1)


class DiscountTests(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(reps(cap1=5, cap2=5))
        lead_id = self.crm.add_lead("a@gmail.com", "A", "referral", "r1")
        self.crm.qualify(lead_id, "r1")
        self.opp_id = self.crm.convert(lead_id, 1000, "r1")

    def test_discount_cumulative_limit(self):
        self.crm.discount(self.opp_id, 10, "r1")
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 900)
        self.crm.discount(self.opp_id, 10, "r1")
        self.crm.discount(self.opp_id, 10, "r1")
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 729)
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp_id, 10, "r1")
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 729)
        self.assertEqual(self.crm.opps[self.opp_id]["original_amount"], 1000)

    def test_discount_validation_order(self):
        for pct in (0, 31, True, 1.0, "5"):
            with self.assertRaises(ValueError):
                self.crm.discount(self.opp_id, pct, "r1")
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp_id, 11, "r1")
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp_id, 5, "r2")
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 1000)

    def test_manager_may_discount_30(self):
        self.crm.discount(self.opp_id, 30, "m1")
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 700)

    def test_discount_rejects_final_stage(self):
        self.crm.advance(self.opp_id, "lost", "r1")
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp_id, 5, "r1")


class TransferTests(unittest.TestCase):
    def test_transfer_success(self):
        crm = CRM(reps(cap1=1, cap2=2))
        a = crm.add_lead("a@gmail.com", "A", "referral", "m1")
        b = crm.add_lead("b@gmail.com", "B", "referral", "m1")
        self.assertEqual(crm.leads[b]["owner"], "r2")
        crm.qualify(a, "m1")
        opp_id = crm.convert(a, 500, "m1")

        crm.transfer(opp_id, "r2", "m1")
        self.assertEqual(crm.opps[opp_id]["owner"], "r2")
        self.assertEqual(crm.log[-1], ("transfer", opp_id, "m1"))
        self.assertEqual(crm._load("r2"), 2)  # lead b + opp
        self.assertEqual(crm._load("r1"), 0)

    def test_transfer_validation_order(self):
        crm = CRM(reps(cap1=1, cap2=2))
        a = crm.add_lead("a@gmail.com", "A", "referral", "m1")
        crm.qualify(a, "m1")
        opp_id = crm.convert(a, 500, "m1")

        with self.assertRaises(ValueError):
            crm.transfer("O99", "r2", "m1")
        with self.assertRaises(PermissionError):
            crm.transfer(opp_id, "r2", "r1")
        with self.assertRaises(ValueError):
            crm.transfer(opp_id, "m1", "m1")  # managers are not reps
        with self.assertRaises(ValueError):
            crm.transfer(opp_id, "ghost", "m1")
        with self.assertRaises(ValueError):
            crm.transfer(opp_id, "r1", "m1")  # same owner
        self.assertEqual(crm.opps[opp_id]["owner"], "r1")

    def test_transfer_to_full_rep(self):
        crm = CRM(reps(cap1=5, cap2=1))
        a = crm.add_lead("a@gmail.com", "A", "referral", "m1")
        crm.add_lead("b@gmail.com", "B", "referral", "m1")
        crm.qualify(a, "m1")
        opp_id = crm.convert(a, 500, "m1")
        self.assertEqual(crm._load("r2"), 1)
        with self.assertRaises(ValueError):
            crm.transfer(opp_id, "r2", "m1")
        self.assertEqual(crm.opps[opp_id]["owner"], "r1")


class ForecastTests(unittest.TestCase):
    def test_forecast_weighting(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 10},
                   {"id": "m1", "role": "manager", "capacity": 99}])
        opps = []
        for i in range(4):
            lead = crm.add_lead("l%d@corp.io" % i, "L%d" % i, "referral", "m1")
            crm.qualify(lead, "m1")
            opps.append(crm.convert(lead, 1000 * (i + 1), "m1"))
        crm.advance(opps[1], "proposal", "m1")
        crm.advance(opps[2], "proposal", "m1")
        crm.advance(opps[2], "negotiation", "m1")
        for stage in ("proposal", "negotiation", "won"):
            crm.advance(opps[3], stage, "m1")
        self.assertEqual(crm.forecast(), {"open": 3, "weighted": 2500, "won": 4000})

    def test_forecast_empty(self):
        self.assertEqual(CRM(reps()).forecast(), {"open": 0, "weighted": 0, "won": 0})


if __name__ == "__main__":
    unittest.main()
