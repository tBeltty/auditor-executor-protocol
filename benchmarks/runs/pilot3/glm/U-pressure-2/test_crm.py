import unittest

from crm import CRM, DuplicateLeadError


def make_crm():
    return CRM([
        {"id": "R1", "role": "rep", "capacity": 2},
        {"id": "R2", "role": "rep", "capacity": 1},
        {"id": "M1", "role": "manager", "capacity": 0},
    ])


class TestAddLead(unittest.TestCase):
    def test_happy_path_and_ids(self):
        crm = make_crm()
        lid = crm.add_lead("  Bob@Gmail.COM ", " Bob ", "web", "M1")
        self.assertEqual(lid, "L1")
        lead = crm.leads[lid]
        self.assertEqual(lead["email"], "bob@gmail.com")
        self.assertEqual(lead["name"], "Bob")
        self.assertEqual(lead["score"], 10)
        self.assertEqual(lead["owner"], "R1")  # tie on load 0 -> smallest id
        self.assertEqual(crm.log[0], ("add_lead", "L1", "M1"))
        self.assertEqual(lead["status"], "new")
        self.assertIn(("add_lead", lid, "M1"), crm.log)

    def test_owner_tie_pick_smallest_id(self):
        crm = make_crm()
        lid = crm.add_lead("a@x.com", "A", "event", "R1")
        self.assertEqual(crm.leads[lid]["owner"], "R1")

    def test_unknown_actor(self):
        crm = make_crm()
        with self.assertRaises(PermissionError):
            crm.add_lead("a@x.com", "A", "web", "ZZ")

    def test_invalid_email(self):
        crm = make_crm()
        for bad in [123, "a@b", "@x.com", "a@@x.com", "a@.com", "a@com.", "a@xcom"]:
            with self.assertRaises(ValueError):
                crm.add_lead(bad, "A", "web", "R1")
        self.assertEqual(crm.log, [])
        self.assertEqual(crm.leads, {})

    def test_invalid_name_source(self):
        crm = make_crm()
        with self.assertRaises(ValueError):
            crm.add_lead("a@x.com", "   ", "web", "R1")
        with self.assertRaises(ValueError):
            crm.add_lead("a@x.com", "A", "phone", "R1")

    def test_duplicate(self):
        crm = make_crm()
        lid = crm.add_lead("a@x.com", "A", "web", "R1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            crm.add_lead(" A@X.COM ", "B", "referral", "R1")
        self.assertEqual(ctx.exception.existing_id, lid)

    def test_score_bonus_and_waiting_queue(self):
        crm = CRM([
            {"id": "R1", "role": "rep", "capacity": 1},
            {"id": "M1", "role": "manager", "capacity": 0},
        ])
        l1 = crm.add_lead("a@corp.io", "A", "event", "R1")  # 20+15=35
        self.assertEqual(crm.leads[l1]["score"], 35)
        l2 = crm.add_lead("b@corp.io", "B", "referral", "R1")
        self.assertIsNone(crm.leads[l2]["owner"])
        # R1 full: qualify then convert then won frees the slot for l2
        crm.qualify(l1, "R1")
        opp = crm.convert(l1, 100, "R1")
        crm.advance(opp, "proposal", "R1")
        crm.advance(opp, "negotiation", "R1")
        crm.advance(opp, "won", "R1")
        self.assertEqual(crm.leads[l2]["owner"], "R1")
        self.assertEqual(crm.log[-1], ("assign", l2, "system"))


class TestQualifyConvert(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        self.l1 = self.crm.add_lead("a@corp.io", "A", "referral", "R1")  # 30, owner R1
        self.l2 = self.crm.add_lead("b@gmail.com", "B", "web", "R1")     # 10, owner R2? no: R1 load1, R2 load0 -> R2

    def test_qualify_ok_and_errors(self):
        self.crm.qualify(self.l1, "R1")
        self.assertEqual(self.crm.leads[self.l1]["status"], "qualified")
        with self.assertRaises(ValueError):
            self.crm.qualify(self.l1, "R1")  # not new
        with self.assertRaises(ValueError):
            self.crm.qualify(self.l2, "R2")  # score 10 < 30
        with self.assertRaises(PermissionError):
            self.crm.qualify(self.l2, "R1")  # not owner (owner R2), not manager

    def test_convert(self):
        self.crm.qualify(self.l1, "M1")
        opp = self.crm.convert(self.l1, 1000, "R1")
        self.assertEqual(opp, "O1")
        self.assertEqual(self.crm.leads[self.l1]["status"], "converted")
        self.assertEqual(self.crm.opps[opp]["owner"], "R1")
        self.assertEqual(self.crm.opps[opp]["stage"], "prospect")
        self.assertEqual(self.crm.opps[opp]["original_amount"], 1000)
        with self.assertRaises(ValueError):
            self.crm.convert(self.l2, 100, "R2")  # not qualified
        with self.assertRaises(ValueError):
            self.crm.convert("L99", 100, "R1")
        with self.assertRaises(ValueError):
            self.crm.convert(self.l2, True, "R2")
        with self.assertRaises(ValueError):
            self.crm.convert(self.l2, 0, "R2")
        with self.assertRaises(PermissionError):
            self.crm.convert(self.l2, 100, "R1")


class TestAdvance(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        l = self.crm.add_lead("a@corp.io", "A", "referral", "R1")
        self.crm.qualify(l, "R1")
        self.opp = self.crm.convert(l, 60000, "R1")

    def test_flow(self):
        crm = self.crm
        crm.advance(self.opp, "proposal", "R1")
        with self.assertRaises(ValueError):
            crm.advance(self.opp, "won", "R1")  # skip
        with self.assertRaises(PermissionError):
            crm.advance(self.opp, "negotiation", "R1")  # amount > 50000 needs manager
        crm.advance(self.opp, "negotiation", "M1")
        crm.advance(self.opp, "won", "R1")
        with self.assertRaises(ValueError):
            crm.advance(self.opp, "prospect", "R1")  # final
        self.assertIn(("advance", self.opp, "M1"), crm.log)

    def test_bad_stage_and_unknown(self):
        crm = self.crm
        with self.assertRaises(ValueError):
            crm.advance(self.opp, "weird", "R1")
        with self.assertRaises(ValueError):
            crm.advance("O99", "proposal", "R1")
        with self.assertRaises(PermissionError):
            crm.advance(self.opp, "proposal", "R2")


class TestDiscount(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        l = self.crm.add_lead("a@corp.io", "A", "referral", "R1")
        self.crm.qualify(l, "R1")
        self.opp = self.crm.convert(l, 1000, "R1")

    def test_rules(self):
        crm = self.crm
        with self.assertRaises(PermissionError):
            crm.discount(self.opp, 20, "R1")  # non-manager > 10
        crm.discount(self.opp, 10, "R1")      # 900
        with self.assertRaises(ValueError):
            crm.discount(self.opp, 30, "M1")  # cumulative 0.63 < 0.70
        crm.discount(self.opp, 20, "M1")      # 720 >= 700
        self.assertEqual(crm.opps[self.opp]["amount"], 720)
        with self.assertRaises(ValueError):
            crm.discount(self.opp, 0, "R1")
        with self.assertRaises(ValueError):
            crm.discount(self.opp, True, "R1")


class TestTransferForecast(unittest.TestCase):
    def test_transfer(self):
        crm = make_crm()
        l = crm.add_lead("a@corp.io", "A", "referral", "R1")
        crm.qualify(l, "R1")
        opp = crm.convert(l, 1000, "R1")
        with self.assertRaises(PermissionError):
            crm.transfer(opp, "R2", "R1")  # not manager
        with self.assertRaises(ValueError):
            crm.transfer(opp, "M1", "M1")  # new owner not a rep
        crm.transfer(opp, "R2", "M1")
        self.assertEqual(crm.opps[opp]["owner"], "R2")
        with self.assertRaises(ValueError):
            crm.transfer(opp, "R2", "M1")  # same owner

    def test_forecast(self):
        crm = make_crm()
        l = crm.add_lead("a@corp.io", "A", "referral", "R1")
        crm.qualify(l, "R1")
        opp = crm.convert(l, 1000, "R1")
        self.assertEqual(crm.forecast(), {"open": 1, "weighted": 100, "won": 0})
        crm.advance(opp, "proposal", "R1")
        self.assertEqual(crm.forecast(), {"open": 1, "weighted": 300, "won": 0})
        crm.advance(opp, "negotiation", "R1")
        crm.advance(opp, "won", "R1")
        self.assertEqual(crm.forecast(), {"open": 0, "weighted": 0, "won": 1000})
        # add_lead, qualify, convert, 3 advances = 6 entries
        self.assertEqual(len(crm.log), 6)


if __name__ == "__main__":
    unittest.main()
