import unittest

from crm import CRM, DuplicateLeadError


REPS = [
    {"id": "r1", "role": "rep", "capacity": 2},
    {"id": "r2", "role": "rep", "capacity": 2},
    {"id": "m1", "role": "manager", "capacity": 5},
]


class AddLeadTests(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(REPS)

    def test_normalizes_and_scores(self):
        lid = self.crm.add_lead("  Bob@Acme.IO ", " Bob ", "web", "m1")
        lead = self.crm.leads[lid]
        self.assertEqual(lid, "L1")
        self.assertEqual(lead["email"], "bob@acme.io")
        self.assertEqual(lead["name"], "Bob")
        self.assertEqual(lead["score"], 25)
        self.assertEqual(lead["owner"], "r1")
        self.assertEqual(lead["status"], "new")
        self.assertEqual(self.crm.log, [("add_lead", "L1", "m1")])

    def test_source_scores(self):
        a = self.crm.add_lead("a@gmail.com", "A", "web", "m1")
        b = self.crm.add_lead("b@gmail.com", "B", "referral", "m1")
        c = self.crm.add_lead("c@gmail.com", "C", "event", "m1")
        self.assertEqual(self.crm.leads[a]["score"], 10)
        self.assertEqual(self.crm.leads[b]["score"], 30)
        self.assertEqual(self.crm.leads[c]["score"], 20)

    def test_bad_email(self):
        for email in ["nope", "a@b", "@x.com", "a@.com", "a@com.", "a@b@c.com", 5]:
            with self.assertRaises(ValueError):
                self.crm.add_lead(email, "N", "web", "m1")

    def test_bad_name_and_source(self):
        with self.assertRaises(ValueError):
            self.crm.add_lead("a@b.com", "   ", "web", "m1")
        with self.assertRaises(ValueError):
            self.crm.add_lead("a@b.com", 3, "web", "m1")
        with self.assertRaises(ValueError):
            self.crm.add_lead("a@b.com", "A", "ads", "m1")

    def test_unknown_actor_checked_first(self):
        with self.assertRaises(PermissionError):
            self.crm.add_lead("bad", "", "nope", "ghost")
        self.assertEqual(self.crm.log, [])

    def test_duplicate_raises_with_existing_id(self):
        lid = self.crm.add_lead("a@b.com", "A", "web", "m1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            self.crm.add_lead(" A@B.com ", "Other", "event", "m1")
        self.assertEqual(ctx.exception.existing_id, lid)
        self.assertEqual(len(self.crm.leads), 1)
        self.assertEqual(len(self.crm.log), 1)

    def test_manager_never_owns(self):
        crm = CRM([{"id": "m1", "role": "manager", "capacity": 5}])
        lid = crm.add_lead("a@b.com", "A", "web", "m1")
        self.assertIsNone(crm.leads[lid]["owner"])

    def test_waiting_queue_when_full(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1}])
        first = crm.add_lead("a@b.com", "A", "web", "r1")
        second = crm.add_lead("b@b.com", "B", "web", "r1")
        self.assertEqual(crm.leads[first]["owner"], "r1")
        self.assertIsNone(crm.leads[second]["owner"])


class QualifyConvertTests(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(REPS)
        self.lid = self.crm.add_lead("a@b.com", "A", "referral", "m1")

    def test_qualify_flow(self):
        self.crm.qualify(self.lid, "r1")
        self.assertEqual(self.crm.leads[self.lid]["status"], "qualified")
        self.assertEqual(self.crm.log[-1], ("qualify", self.lid, "r1"))

    def test_qualify_low_score(self):
        lid = self.crm.add_lead("x@b.com", "X", "web", "m1")
        with self.assertRaises(ValueError):
            self.crm.qualify(lid, "m1")

    def test_qualify_unknown_lead_and_wrong_status(self):
        with self.assertRaises(ValueError):
            self.crm.qualify("L99", "m1")
        self.crm.qualify(self.lid, "m1")
        with self.assertRaises(ValueError):
            self.crm.qualify(self.lid, "m1")

    def test_qualify_permission(self):
        with self.assertRaises(PermissionError):
            self.crm.qualify(self.lid, "r2")
        self.crm.qualify(self.lid, "m1")

    def test_convert_flow(self):
        self.crm.qualify(self.lid, "r1")
        oid = self.crm.convert(self.lid, 4000, "r1")
        self.assertEqual(oid, "O1")
        opp = self.crm.opps[oid]
        self.assertEqual(opp["owner"], "r1")
        self.assertEqual(opp["amount"], 4000)
        self.assertEqual(opp["original_amount"], 4000)
        self.assertEqual(opp["stage"], "prospect")
        self.assertEqual(self.crm.leads[self.lid]["status"], "converted")
        self.assertEqual(self.crm.log[-1], ("convert", "O1", "r1"))

    def test_convert_failures(self):
        self.crm.qualify(self.lid, "m1")
        with self.assertRaises(ValueError):
            self.crm.convert(self.lid, 0, "m1")
        with self.assertRaises(ValueError):
            self.crm.convert(self.lid, True, "m1")
        with self.assertRaises(ValueError):
            self.crm.convert(self.lid, 1.5, "m1")
        with self.assertRaises(PermissionError):
            self.crm.convert(self.lid, 100, "r2")
        self.assertEqual(self.crm.opps, {})
        self.assertEqual(self.crm.leads[self.lid]["status"], "qualified")


class AdvanceTests(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(REPS)
        self.lid = self.crm.add_lead("a@b.com", "A", "referral", "m1")
        self.crm.qualify(self.lid, "r1")
        self.oid = self.crm.convert(self.lid, 1000, "r1")

    def test_stage_sequence_and_won(self):
        self.crm.advance(self.oid, "proposal", "r1")
        self.crm.advance(self.oid, "negotiation", "r1")
        self.crm.advance(self.oid, "won", "r1")
        self.assertEqual(self.crm.opps[self.oid]["stage"], "won")
        with self.assertRaises(ValueError):
            self.crm.advance(self.oid, "lost", "r1")

    def test_invalid_transitions(self):
        with self.assertRaises(ValueError):
            self.crm.advance(self.oid, "won", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance(self.oid, "bogus", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance("O99", "proposal", "r1")
        with self.assertRaises(PermissionError):
            self.crm.advance(self.oid, "proposal", "r2")
        self.crm.advance(self.oid, "lost", "m1")
        self.assertEqual(self.crm.opps[self.oid]["stage"], "lost")

    def test_negotiation_over_50000_needs_manager(self):
        lid = self.crm.add_lead("big@b.com", "Big", "referral", "m1")
        self.crm.qualify(lid, "m1")
        oid = self.crm.convert(lid, 60000, "m1")
        self.crm.advance(oid, "proposal", "m1")
        with self.assertRaises(PermissionError):
            self.crm.advance(oid, "negotiation", "r1")
        self.crm.advance(oid, "negotiation", "m1")

    def test_won_frees_slot_and_assigns_waiting_lead(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1}])
        first = crm.add_lead("a@b.com", "A", "referral", "r1")
        second = crm.add_lead("b@b.com", "B", "web", "r1")
        crm.qualify(first, "r1")
        oid = crm.convert(first, 500, "r1")
        crm.advance(oid, "proposal", "r1")
        crm.advance(oid, "negotiation", "r1")
        crm.advance(oid, "won", "r1")
        self.assertEqual(crm.leads[second]["owner"], "r1")
        self.assertEqual(crm.log[-1], ("assign", second, "system"))


class DiscountTransferTests(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(REPS)
        lid = self.crm.add_lead("a@b.com", "A", "referral", "m1")
        self.crm.qualify(lid, "m1")
        self.oid = self.crm.convert(lid, 10000, "m1")

    def test_discount_limits(self):
        with self.assertRaises(ValueError):
            self.crm.discount(self.oid, 0, "m1")
        with self.assertRaises(ValueError):
            self.crm.discount(self.oid, 31, "m1")
        with self.assertRaises(ValueError):
            self.crm.discount(self.oid, True, "m1")
        with self.assertRaises(PermissionError):
            self.crm.discount(self.oid, 11, "r1")
        self.crm.discount(self.oid, 10, "r1")
        self.assertEqual(self.crm.opps[self.oid]["amount"], 9000)
        self.crm.discount(self.oid, 10, "m1")
        self.crm.discount(self.oid, 10, "m1")
        self.assertEqual(self.crm.opps[self.oid]["amount"], 7290)
        with self.assertRaises(ValueError):
            self.crm.discount(self.oid, 10, "m1")
        self.assertEqual(self.crm.opps[self.oid]["amount"], 7290)

    def test_discount_cumulative_on_original(self):
        self.crm.discount(self.oid, 30, "m1")
        self.assertEqual(self.crm.opps[self.oid]["amount"], 7000)
        with self.assertRaises(ValueError):
            self.crm.discount(self.oid, 1, "m1")

    def test_discount_final_stage(self):
        self.crm.advance(self.oid, "lost", "m1")
        with self.assertRaises(ValueError):
            self.crm.discount(self.oid, 5, "m1")

    def test_transfer(self):
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.oid, "r2", "r1")
        with self.assertRaises(ValueError):
            self.crm.transfer(self.oid, "m1", "m1")
        with self.assertRaises(ValueError):
            self.crm.transfer(self.oid, "ghost", "m1")
        with self.assertRaises(ValueError):
            self.crm.transfer(self.oid, "r1", "m1")
        self.crm.transfer(self.oid, "r2", "m1")
        self.assertEqual(self.crm.opps[self.oid]["owner"], "r2")
        self.assertEqual(self.crm.log[-1], ("transfer", self.oid, "m1"))

    def test_transfer_respects_capacity(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 2},
                   {"id": "r2", "role": "rep", "capacity": 1},
                   {"id": "m1", "role": "manager", "capacity": 1}])
        lead_a = crm.add_lead("a@b.com", "A", "referral", "m1")
        crm.add_lead("b@b.com", "B", "web", "m1")
        crm.qualify(lead_a, "m1")
        oid = crm.convert(lead_a, 100, "m1")
        self.assertEqual(crm.load("r2"), 1)
        with self.assertRaises(ValueError):
            crm.transfer(oid, "r2", "m1")

    def test_transfer_final_stage(self):
        self.crm.advance(self.oid, "proposal", "m1")
        self.crm.advance(self.oid, "lost", "m1")
        with self.assertRaises(ValueError):
            self.crm.transfer(self.oid, "r2", "m1")


class ForecastTests(unittest.TestCase):
    def test_forecast(self):
        crm = CRM(REPS)
        ids = []
        for i, amount in enumerate([1000, 2000, 3000]):
            lid = crm.add_lead("u%d@b.com" % i, "U", "referral", "m1")
            crm.qualify(lid, "m1")
            ids.append(crm.convert(lid, amount, "m1"))
        crm.advance(ids[1], "proposal", "m1")
        crm.advance(ids[2], "proposal", "m1")
        crm.advance(ids[2], "negotiation", "m1")
        self.assertEqual(crm.forecast(), {"open": 3, "weighted": 100 + 600 + 1800, "won": 0})
        crm.advance(ids[0], "proposal", "m1")
        crm.advance(ids[0], "negotiation", "m1")
        crm.advance(ids[0], "won", "m1")
        self.assertEqual(crm.forecast(), {"open": 2, "weighted": 2400, "won": 1000})


if __name__ == "__main__":
    unittest.main()
