import unittest

from crm import CRM, DuplicateLeadError

REPS = [
    {"id": "r1", "role": "rep", "capacity": 2},
    {"id": "r2", "role": "rep", "capacity": 2},
    {"id": "m1", "role": "manager", "capacity": 0},
]


class TestCRM(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(REPS)

    def test_unknown_actor(self):
        with self.assertRaises(PermissionError):
            self.crm.add_lead("a@b.com", "A", "web", "nobody")

    def test_add_lead_basic(self):
        lid = self.crm.add_lead("  Bob@Gmail.COM ", " Bob ", "web", "r1")
        lead = self.crm.leads[lid]
        self.assertEqual(lid, "L1")
        self.assertEqual(lead["email"], "bob@gmail.com")
        self.assertEqual(lead["name"], "Bob")
        self.assertEqual(lead["score"], 10)
        self.assertEqual(lead["owner"], "r1")
        self.assertEqual(lead["status"], "new")
        self.assertEqual(self.crm.log, [("add_lead", "L1", "r1")])

    def test_add_lead_scores(self):
        self.assertEqual(self.crm.leads[self.crm.add_lead("a@x.org", "A", "referral", "r1")]["score"], 45)
        self.assertEqual(self.crm.leads[self.crm.add_lead("b@yahoo.com", "B", "event", "r1")]["score"], 20)

    def test_email_validation(self):
        for bad in [123, "no-at.com", "a@@b.com", "@b.com", "a@b", "a@.b.com", "a@b.com.", "a@nodot"]:
            with self.assertRaises(ValueError):
                self.crm.add_lead(bad, "A", "web", "r1")

    def test_add_lead_invalid_name_source(self):
        with self.assertRaises(ValueError):
            self.crm.add_lead("a@b.com", "   ", "web", "r1")
        with self.assertRaises(ValueError):
            self.crm.add_lead("a@b.com", "A", "phone", "r1")

    def test_duplicate_lead(self):
        self.crm.add_lead("a@b.com", "A", "web", "r1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            self.crm.add_lead(" A@B.COM ", "A2", "web", "r1")
        self.assertEqual(ctx.exception.existing_id, "L1")
        self.assertEqual(len(self.crm.leads), 1)
        self.assertEqual(len(self.crm.log), 1)

    def test_owner_assignment_and_queue(self):
        l1 = self.crm.add_lead("a@b.com", "A", "web", "r1")
        l2 = self.crm.add_lead("b@b.com", "B", "web", "r1")
        l3 = self.crm.add_lead("c@b.com", "C", "web", "r1")  # all loads tie at 0, r1 picked; then r1 load 1
        l4 = self.crm.add_lead("d@b.com", "D", "web", "r1")
        l5 = self.crm.add_lead("e@b.com", "E", "web", "r1")
        self.assertEqual(self.crm.leads[l1]["owner"], "r1")
        self.assertEqual(self.crm.leads[l2]["owner"], "r2")
        self.assertEqual(self.crm.leads[l3]["owner"], "r1")
        self.assertEqual(self.crm.leads[l4]["owner"], "r2")
        self.assertIsNone(self.crm.leads[l5]["owner"])
        self.assertEqual(self.crm._waiting, [l5])

    def test_qualify(self):
        lid = self.crm.add_lead("a@x.org", "A", "referral", "r1")
        self.crm.qualify(lid, "r1")
        self.assertEqual(self.crm.leads[lid]["status"], "qualified")
        with self.assertRaises(ValueError):
            self.crm.qualify(lid, "r1")  # not new anymore

    def test_qualify_errors(self):
        with self.assertRaises(ValueError):
            self.crm.qualify("L99", "r1")
        lid = self.crm.add_lead("a@gmail.com", "A", "web", "r1")  # score 10
        with self.assertRaises(PermissionError):
            self.crm.qualify(lid, "r2")
        with self.assertRaises(ValueError):
            self.crm.qualify(lid, "m1")  # manager ok, but score < 30
        self.crm.leads[lid]["score"] = 30
        self.crm.qualify(lid, "m1")  # manager may act on someone else's lead

    def test_convert(self):
        lid = self.crm.add_lead("a@x.org", "A", "referral", "r1")
        self.crm.qualify(lid, "r1")
        oid = self.crm.convert(lid, 1000, "r1")
        self.assertEqual(oid, "O1")
        opp = self.crm.opps[oid]
        self.assertEqual(opp["owner"], "r1")
        self.assertEqual(opp["stage"], "prospect")
        self.assertEqual(opp["amount"], 1000)
        self.assertEqual(self.crm.leads[lid]["status"], "converted")
        with self.assertRaises(ValueError):
            self.crm.convert(lid, 1000, "r1")  # already converted

    def test_convert_validation(self):
        lid = self.crm.add_lead("a@x.org", "A", "referral", "r1")
        with self.assertRaises(ValueError):
            self.crm.convert("L99", 100, "r1")
        with self.assertRaises(ValueError):
            self.crm.convert(lid, True, "r1")
        with self.assertRaises(ValueError):
            self.crm.convert(lid, 0, "r1")
        with self.assertRaises(PermissionError):
            self.crm.convert(lid, 100, "r2")
        with self.assertRaises(ValueError):
            self.crm.convert(lid, 100, "r1")  # not qualified
        self.crm.qualify(lid, "r1")
        self.crm.leads[lid]["owner"] = None
        with self.assertRaises(ValueError):
            self.crm.convert(lid, 100, "m1")  # no owner

    def test_advance_flow(self):
        lid = self.crm.add_lead("a@x.org", "A", "referral", "r1")
        self.crm.qualify(lid, "r1")
        oid = self.crm.convert(lid, 60000, "r1")
        with self.assertRaises(ValueError):
            self.crm.advance(oid, "negotiation", "r1")  # skips proposal
        self.crm.advance(oid, "proposal", "r1")
        with self.assertRaises(PermissionError):
            self.crm.advance(oid, "negotiation", "r1")  # amount > 50000 needs manager
        self.crm.advance(oid, "negotiation", "m1")
        self.crm.advance(oid, "won", "m1")
        self.assertEqual(self.crm.opps[oid]["stage"], "won")
        with self.assertRaises(ValueError):
            self.crm.advance(oid, "prospect", "m1")  # final

    def test_advance_lost_and_slot_freeing(self):
        l1 = self.crm.add_lead("a@b.com", "A", "referral", "r1")
        l2 = self.crm.add_lead("b@b.com", "B", "web", "r1")
        l3 = self.crm.add_lead("c@b.com", "C", "web", "r1")
        l4 = self.crm.add_lead("d@b.com", "D", "web", "r1")
        waiting = self.crm.add_lead("e@b.com", "E", "web", "r1")
        self.crm.qualify(l1, "r1")
        oid = self.crm.convert(l1, 100, "r1")
        self.crm.advance(oid, "lost", "r1")
        self.assertEqual(self.crm.leads[waiting]["owner"], "r1")
        self.assertEqual(
            [e for e in self.crm.log if e[0] == "assign"][0], ("assign", waiting, "system")
        )
        self.assertEqual(len(self.crm._waiting), 0)

    def test_discount(self):
        lid = self.crm.add_lead("a@x.org", "A", "referral", "r1")
        self.crm.qualify(lid, "r1")
        oid = self.crm.convert(lid, 1000, "r1")
        self.crm.discount(oid, 10, "r1")
        self.assertEqual(self.crm.opps[oid]["amount"], 900)
        self.crm.discount(oid, 22, "m1")  # 900 * 78 // 100 = 702 -> exactly 70%
        self.assertEqual(self.crm.opps[oid]["amount"], 702)
        with self.assertRaises(ValueError):
            self.crm.discount(oid, 1, "m1")  # cumulative > 30%

    def test_discount_validation(self):
        lid = self.crm.add_lead("a@x.org", "A", "referral", "r1")
        self.crm.qualify(lid, "r1")
        oid = self.crm.convert(lid, 1000, "r1")
        with self.assertRaises(ValueError):
            self.crm.discount(oid, True, "r1")
        with self.assertRaises(ValueError):
            self.crm.discount(oid, 0, "r1")
        with self.assertRaises(ValueError):
            self.crm.discount(oid, 31, "m1")
        with self.assertRaises(PermissionError):
            self.crm.discount(oid, 11, "r1")  # non-manager > 10
        with self.assertRaises(PermissionError):
            self.crm.discount(oid, 5, "r2")
        self.crm.advance(oid, "lost", "r1")
        with self.assertRaises(ValueError):
            self.crm.discount(oid, 5, "r1")  # final stage

    def test_transfer(self):
        lid = self.crm.add_lead("a@x.org", "A", "referral", "r1")
        self.crm.qualify(lid, "r1")
        oid = self.crm.convert(lid, 100, "r1")
        big = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 3},
                {"id": "r2", "role": "rep", "capacity": 3},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        lid2 = big.add_lead("a@x.org", "A", "referral", "r1")
        big.qualify(lid2, "r1")
        oid2 = big.convert(lid2, 100, "r1")
        big.add_lead("c@b.com", "C", "web", "r1")
        big.add_lead("d@b.com", "D", "web", "r2")
        big.transfer(oid2, "r2", "m1")
        self.assertEqual(big.opps[oid2]["owner"], "r2")
        self.assertIn(("transfer", oid2, "m1"), big.log)
        self.assertEqual(
            [e for e in big.log if e[0] == "transfer"], [("transfer", oid2, "m1")]
        )

    def test_transfer_validation(self):
        lid = self.crm.add_lead("a@x.org", "A", "referral", "r1")
        self.crm.qualify(lid, "r1")
        oid = self.crm.convert(lid, 100, "r1")
        with self.assertRaises(PermissionError):
            self.crm.transfer(oid, "r2", "r1")  # not manager
        with self.assertRaises(PermissionError):
            self.crm.transfer(oid, "r2", "ghost")
        with self.assertRaises(ValueError):
            self.crm.transfer(oid, "m1", "m1")  # not a rep
        with self.assertRaises(ValueError):
            self.crm.transfer(oid, "r1", "m1")  # same owner
        self.crm.advance(oid, "lost", "r1")
        with self.assertRaises(ValueError):
            self.crm.transfer(oid, "r2", "m1")  # final stage


if __name__ == "__main__":
    unittest.main()
