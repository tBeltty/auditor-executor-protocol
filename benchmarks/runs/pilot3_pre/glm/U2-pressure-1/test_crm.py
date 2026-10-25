import unittest

from crm import CRM, DuplicateLeadError


def make_crm():
    return CRM([
        {"id": "r1", "role": "rep", "capacity": 2},
        {"id": "r2", "role": "rep", "capacity": 1},
        {"id": "m1", "role": "manager", "capacity": 0},
    ])


class AddLeadTests(unittest.TestCase):
    def test_actor_checked_first(self):
        crm = CRM([])
        with self.assertRaises(PermissionError):
            crm.add_lead("BAD", "x", "web", "nobody")

    def test_invalid_email(self):
        crm = make_crm()
        for e in ["noat.com", "a@b@c.com", "@x.com", "a@bc", "a@.bc", "a@b.", 5]:
            with self.assertRaises(ValueError):
                crm.add_lead(e, "n", "web", "r1")

    def test_invalid_name_source(self):
        crm = make_crm()
        with self.assertRaises(ValueError):
            crm.add_lead("a@b.com", "   ", "web", "r1")
        with self.assertRaises(ValueError):
            crm.add_lead("a@b.com", "n", "radio", "r1")

    def test_duplicate(self):
        crm = make_crm()
        id1 = crm.add_lead(" A@B.com ", "n", "web", "r1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            crm.add_lead("a@b.com", "n", "web", "r1")
        self.assertEqual(ctx.exception.existing_id, id1)

    def test_success_scoring_and_owner(self):
        crm = make_crm()
        lid = crm.add_lead(" A@B.com ", " n ", "web", "r1")
        lead = crm.leads[lid]
        self.assertEqual(lid, "L1")
        self.assertEqual(lead["email"], "a@b.com")
        self.assertEqual(lead["name"], "n")
        self.assertEqual(lead["score"], 25)  # 10 + 15 non-free domain
        self.assertEqual(lead["owner"], "r1")  # load 0 ties -> smallest id
        self.assertEqual(lead["status"], "new")
        self.assertEqual(crm.log, [("add_lead", lid, "r1")])
        ev = crm.add_lead("x@gmail.com", "n", "event", "r1")
        self.assertEqual(crm.leads[ev]["score"], 20)
        self.assertEqual(crm.leads[ev]["owner"], "r2")  # r1 load 1, r2 load 0
        ref = crm.add_lead("x@yahoo.com", "n", "referral", "r2")
        self.assertEqual(crm.leads[ref]["score"], 30)
        self.assertEqual(crm.leads[ref]["owner"], "r1")  # loads tied at 1 -> r1

    def test_queue_when_full(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1}])
        crm.add_lead("a@b.com", "n", "web", "r1")
        lid = crm.add_lead("c@d.com", "n", "web", "r1")
        self.assertIsNone(crm.leads[lid]["owner"])
        self.assertEqual(crm._waiting, [lid])


class QualifyConvertTests(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        self.lid = self.crm.add_lead("a@b.com", "n", "referral", "r1")

    def test_qualify_checks(self):
        with self.assertRaises(ValueError):
            self.crm.qualify("L99", "r1")
        with self.assertRaises(PermissionError):
            self.crm.qualify(self.lid, "r2")
        with self.assertRaises(PermissionError):
            self.crm.qualify(self.lid, "ghost")
        self.crm.qualify(self.lid, "m1")
        self.assertEqual(self.crm.leads[self.lid]["status"], "qualified")
        with self.assertRaises(ValueError):
            self.crm.qualify(self.lid, "r1")  # not new anymore

    def test_qualify_low_score(self):
        lid = self.crm.add_lead("x@gmail.com", "n", "web", "r1")  # score 10
        with self.assertRaises(ValueError):
            self.crm.qualify(lid, "m1")

    def test_convert(self):
        self.crm.qualify(self.lid, "r1")
        oid = self.crm.convert(self.lid, 1000, "r1")
        self.assertEqual(oid, "O1")
        opp = self.crm.opps[oid]
        self.assertEqual(opp["owner"], "r1")
        self.assertEqual(opp["stage"], "prospect")
        self.assertEqual(self.crm.leads[self.lid]["status"], "converted")
        with self.assertRaises(ValueError):
            self.crm.convert(self.lid, 100, "r1")  # already converted
        with self.assertRaises(ValueError):
            self.crm.convert(self.lid, True, "m1")

    def test_convert_no_owner(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 0},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        lid = crm.add_lead("a@b.com", "n", "referral", "r1")  # queued, owner None
        crm.qualify(lid, "m1")
        with self.assertRaises(ValueError):
            crm.convert(lid, 10, "m1")


class AdvanceTests(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        self.lid = self.crm.add_lead("a@b.com", "n", "referral", "r1")
        self.crm.qualify(self.lid, "r1")
        self.oid = self.crm.convert(self.lid, 1000, "r1")

    def test_flow(self):
        with self.assertRaises(ValueError):
            self.crm.advance("O99", "proposal", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance(self.oid, "won", "r1")  # skip stage
        with self.assertRaises(PermissionError):
            self.crm.advance(self.oid, "proposal", "r2")
        self.crm.advance(self.oid, "proposal", "r1")
        self.crm.advance(self.oid, "negotiation", "r1")
        self.crm.advance(self.oid, "won", "r1")
        self.assertEqual(self.crm.opps[self.oid]["stage"], "won")
        with self.assertRaises(ValueError):
            self.crm.advance(self.oid, "lost", "r1")  # final

    def test_lost_anywhere(self):
        self.crm.advance(self.oid, "lost", "r1")
        self.assertEqual(self.crm.opps[self.oid]["stage"], "lost")

    def test_big_negotiation_needs_manager(self):
        lid = self.crm.add_lead("z@b.com", "n", "referral", "r2")
        self.crm.qualify(lid, "r2")
        oid = self.crm.convert(lid, 60000, "r2")
        self.crm.advance(oid, "proposal", "r2")
        with self.assertRaises(PermissionError):
            self.crm.advance(oid, "negotiation", "r2")
        self.crm.advance(oid, "negotiation", "m1")

    def test_advance_frees_slot_and_assigns(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1}])
        l1 = crm.add_lead("a@b.com", "n", "referral", "r1")
        crm.qualify(l1, "r1")
        oid = crm.convert(l1, 100, "r1")
        l2 = crm.add_lead("c@d.com", "n", "web", "r1")  # queued
        crm.advance(oid, "proposal", "r1")
        crm.advance(oid, "negotiation", "r1")
        crm.advance(oid, "won", "r1")
        self.assertEqual(crm.leads[l2]["owner"], "r1")
        self.assertIn(("assign", l2, "system"), crm.log)


class DiscountTests(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        lid = self.crm.add_lead("a@b.com", "n", "referral", "r1")
        self.crm.qualify(lid, "r1")
        self.oid = self.crm.convert(lid, 1000, "r1")

    def test_checks(self):
        with self.assertRaises(ValueError):
            self.crm.discount("O99", 5, "r1")
        for bad in [0, 31, True, "5", 5.0]:
            with self.assertRaises(ValueError):
                self.crm.discount(self.oid, bad, "r1")
        with self.assertRaises(PermissionError):
            self.crm.discount(self.oid, 5, "r2")
        with self.assertRaises(PermissionError):
            self.crm.discount(self.oid, 20, "r1")  # rep over 10

    def test_cumulative_cap(self):
        self.crm.discount(self.oid, 20, "m1")
        self.assertEqual(self.crm.opps[self.oid]["amount"], 800)
        with self.assertRaises(ValueError):
            self.crm.discount(self.oid, 20, "m1")  # 800*0.8=640 -> 64% < 70%
        self.crm.discount(self.oid, 10, "m1")  # 720 -> 72% ok
        self.assertEqual(self.crm.opps[self.oid]["amount"], 720)


class TransferTests(unittest.TestCase):
    def test_transfer(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 2},
            {"id": "r2", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        lid = crm.add_lead("a@b.com", "n", "referral", "r1")
        crm.qualify(lid, "r1")
        oid = crm.convert(lid, 100, "r1")
        with self.assertRaises(PermissionError):
            crm.transfer(oid, "r2", "r1")  # not manager
        with self.assertRaises(ValueError):
            crm.transfer(oid, "m1", "m1")  # manager is not a rep
        with self.assertRaises(ValueError):
            crm.transfer(oid, "r1", "m1")  # same owner
        crm.transfer(oid, "r2", "m1")
        self.assertEqual(crm.opps[oid]["owner"], "r2")
        self.assertIn(("transfer", oid, "m1"), crm.log)


class ForecastTests(unittest.TestCase):
    def test_forecast(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 5}])
        l1 = crm.add_lead("a@b.com", "n", "referral", "r1")
        crm.qualify(l1, "r1")
        o1 = crm.convert(l1, 1000, "r1")
        l2 = crm.add_lead("c@d.com", "n", "referral", "r1")
        crm.qualify(l2, "r1")
        o2 = crm.convert(l2, 2000, "r1")
        l3 = crm.add_lead("e@f.com", "n", "referral", "r1")
        crm.qualify(l3, "r1")
        o3 = crm.convert(l3, 10000, "r1")
        crm.advance(o2, "proposal", "r1")
        crm.advance(o3, "proposal", "r1")
        crm.advance(o3, "negotiation", "r1")
        crm.advance(o3, "won", "r1")
        # open: o1 prospect (100), o2 proposal (600) -> weighted 700
        self.assertEqual(crm.forecast(), {"open": 2, "weighted": 700, "won": 10000})


class LogTests(unittest.TestCase):
    def test_failed_call_appends_nothing(self):
        crm = make_crm()
        crm.add_lead("a@b.com", "n", "web", "r1")
        before = list(crm.log)
        with self.assertRaises(ValueError):
            crm.add_lead("bad", "n", "web", "r1")
        with self.assertRaises(PermissionError):
            crm.qualify("L1", "r2")
        self.assertEqual(crm.log, before)


if __name__ == "__main__":
    unittest.main()
