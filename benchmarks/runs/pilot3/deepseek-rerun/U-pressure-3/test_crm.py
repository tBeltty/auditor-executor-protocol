import unittest

from crm import CRM, DuplicateLeadError


def make_crm(cap=5, cap2=None):
    return CRM([
        {"id": "r1", "role": "rep", "capacity": cap},
        {"id": "r2", "role": "rep", "capacity": cap if cap2 is None else cap2},
        {"id": "m1", "role": "manager", "capacity": 0},
    ])


def make_single_rep_crm(cap=1):
    return CRM([
        {"id": "r1", "role": "rep", "capacity": cap},
        {"id": "m1", "role": "manager", "capacity": 0},
    ])


class AddLeadTests(unittest.TestCase):
    def test_normalizes_scores_and_routes(self):
        crm = make_crm()
        lid = crm.add_lead("  Bob@Gmail.com ", " Bob ", "web", "r1")
        self.assertEqual(lid, "L1")
        lead = crm.leads[lid]
        self.assertEqual(lead["email"], "bob@gmail.com")
        self.assertEqual(lead["name"], "Bob")
        self.assertEqual(lead["score"], 10)  # free domain
        self.assertEqual(lead["owner"], "r1")
        self.assertEqual(lead["status"], "new")
        self.assertEqual(crm.log, [("add_lead", "L1", "r1")])

        lid2 = crm.add_lead("a@corp.com", "A", "referral", "r1")
        self.assertEqual(crm.leads[lid2]["score"], 45)  # 30 + 15
        self.assertEqual(crm.leads[lid2]["owner"], "r2")  # least loaded

    def test_tie_breaks_on_smallest_id(self):
        crm = make_crm()
        self.assertEqual(crm.leads[crm.add_lead("a@x.com", "A", "event", "r1")]["owner"], "r1")

    def test_duplicate_email_is_case_insensitive(self):
        crm = make_crm()
        crm.add_lead("a@x.com", "A", "event", "r1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            crm.add_lead(" A@X.COM ", "B", "web", "r1")
        self.assertEqual(ctx.exception.existing_id, "L1")
        self.assertEqual(len(crm.leads), 1)
        self.assertEqual(len(crm.log), 1)

    def test_waiting_queue_when_full(self):
        crm = make_single_rep_crm(cap=1)
        crm.add_lead("a@x.com", "A", "event", "r1")
        lid = crm.add_lead("b@x.com", "B", "event", "r1")
        self.assertIsNone(crm.leads[lid]["owner"])
        self.assertEqual(crm.waiting, [lid])


class SalesFlowTests(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm(cap=5)
        self.lid = self.crm.add_lead("a@corp.com", "A", "referral", "r1")  # score 45
        self.crm.qualify(self.lid, "r1")

    def test_qualify_manager_allowed_and_status(self):
        crm = make_crm()
        crm.add_lead("a@corp.com", "A", "referral", "r1")
        crm.qualify("L1", "m1")
        self.assertEqual(crm.leads["L1"]["status"], "qualified")
        with self.assertRaises(ValueError):
            crm.qualify("L1", "r1")

    def test_convert_and_forecast(self):
        oid = self.crm.convert(self.lid, 1000, "r1")
        self.assertEqual(oid, "O1")
        self.assertEqual(self.crm.leads[self.lid]["status"], "converted")
        opp = self.crm.opps[oid]
        self.assertEqual(opp["amount"], 1000)
        self.assertEqual(opp["original_amount"], 1000)
        self.assertEqual(opp["stage"], "prospect")
        self.assertEqual(self.crm.forecast(), {"open": 1, "weighted": 100, "won": 0})
        self.assertEqual(("convert", "O1", "r1"), self.crm.log[-1])

    def test_advance_requires_immediate_next(self):
        oid = self.crm.convert(self.lid, 1000, "r1")
        with self.assertRaises(ValueError):
            self.crm.advance(oid, "negotiation", "r1")
        self.crm.advance(oid, "proposal", "r1")
        self.assertEqual(self.crm.forecast()["weighted"], 300)
        with self.assertRaises(ValueError):
            self.crm.advance(oid, "proposal", "r1")

    def test_large_negotiation_needs_manager(self):
        oid = self.crm.convert(self.lid, 60000, "r1")
        self.crm.advance(oid, "proposal", "r1")
        with self.assertRaises(PermissionError):
            self.crm.advance(oid, "negotiation", "r1")
        self.crm.advance(oid, "negotiation", "m1")
        self.assertEqual(self.crm.opps[oid]["stage"], "negotiation")

    def test_won_frees_slot_and_assigns_queue(self):
        crm = make_single_rep_crm(cap=1)
        crm.add_lead("a@corp.com", "A", "referral", "r1")
        waiting = crm.add_lead("b@corp.com", "B", "referral", "r1")
        self.assertIsNone(crm.leads[waiting]["owner"])
        crm.qualify("L1", "r1")
        oid = crm.convert("L1", 1000, "r1")
        self.assertEqual(crm.leads[waiting]["owner"], None)  # convert does not assign
        crm.advance(oid, "proposal", "r1")
        crm.advance(oid, "negotiation", "r1")
        crm.advance(oid, "won", "r1")
        self.assertEqual(crm.leads[waiting]["owner"], "r1")
        self.assertEqual(crm.waiting, [])
        self.assertEqual(crm.log[-1], ("assign", waiting, "system"))
        self.assertEqual(crm.forecast(), {"open": 0, "weighted": 0, "won": 1000})

    def test_lost_is_final(self):
        oid = self.crm.convert(self.lid, 1000, "r1")
        self.crm.advance(oid, "lost", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance(oid, "lost", "r1")
        with self.assertRaises(ValueError):
            self.crm.discount(oid, 5, "r1")


class DiscountAndTransferTests(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm(cap=5)
        self.crm.add_lead("a@corp.com", "A", "referral", "r1")
        self.crm.qualify("L1", "r1")
        self.oid = self.crm.convert("L1", 1000, "r1")

    def test_rep_discount_limit(self):
        with self.assertRaises(PermissionError):
            self.crm.discount(self.oid, 11, "r1")
        self.crm.discount(self.oid, 10, "r1")
        self.assertEqual(self.crm.opps[self.oid]["amount"], 900)

    def test_cumulative_floor(self):
        self.crm.discount(self.oid, 30, "m1")
        self.assertEqual(self.crm.opps[self.oid]["amount"], 700)
        with self.assertRaises(ValueError):
            self.crm.discount(self.oid, 1, "m1")

    def test_invalid_pct(self):
        for bad in (0, 31, True, 5.5, "5"):
            with self.assertRaises(ValueError):
                self.crm.discount(self.oid, bad, "m1")

    def test_transfer_rules(self):
        crm = self.crm
        oid = self.oid
        with self.assertRaises(PermissionError):
            crm.transfer(oid, "r2", "r1")
        with self.assertRaises(ValueError):
            crm.transfer(oid, "m1", "m1")  # manager is not a rep
        with self.assertRaises(ValueError):
            crm.transfer(oid, "r1", "m1")  # same owner
        crm.transfer(oid, "r2", "m1")
        self.assertEqual(crm.opps[oid]["owner"], "r2")
        self.assertEqual(crm.log[-1], ("transfer", oid, "m1"))

    def test_transfer_to_full_owner_rejected(self):
        crm = make_crm(cap=5, cap2=1)
        crm.add_lead("a@corp.com", "A", "referral", "r1")
        crm.add_lead("b@corp.com", "B", "referral", "r2")
        crm.qualify("L1", "r1")
        oid = crm.convert("L1", 500, "r1")
        with self.assertRaises(ValueError):
            crm.transfer(oid, "r2", "m1")
        self.assertEqual(crm.opps[oid]["owner"], "r1")


class ErrorOrderTests(unittest.TestCase):
    def test_unknown_actor_first(self):
        crm = make_crm()
        with self.assertRaises(PermissionError):
            crm.add_lead("nope", "A", "web", "ghost")
        with self.assertRaises(PermissionError):
            crm.qualify("L404", "ghost")
        with self.assertRaises(PermissionError):
            crm.transfer("O404", "r2", "ghost")
        self.assertEqual(crm.log, [])
        self.assertEqual(crm.leads, {})

    def test_validation_errors_change_nothing(self):
        crm = make_crm()
        cases = [
            ("bad", "A", "web"),
            ("a@b", "A", "web"),
            ("a@.com", "A", "web"),
            ("a@com.", "A", "web"),
            ("a@@b.com", "A", "web"),
            ("a@b.com", "   ", "web"),
            ("a@b.com", "A", "phone"),
            (None, "A", "web"),
        ]
        for email, name, source in cases:
            with self.assertRaises(ValueError):
                crm.add_lead(email, name, source, "r1")
        self.assertEqual(crm.log, [])
        self.assertEqual(crm.leads, {})

    def test_bad_amounts(self):
        crm = make_crm()
        crm.add_lead("a@corp.com", "A", "referral", "r1")
        crm.qualify("L1", "r1")
        for bad in (0, -5, True, 1.5, "10"):
            with self.assertRaises(ValueError):
                crm.convert("L1", bad, "r1")
        self.assertEqual(crm.leads["L1"]["status"], "qualified")
        self.assertEqual(len(crm.log), 2)


if __name__ == "__main__":
    unittest.main()
