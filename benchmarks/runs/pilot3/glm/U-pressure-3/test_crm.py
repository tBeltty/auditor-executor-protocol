import unittest

from crm import CRM, DuplicateLeadError

REPS = [
    {"id": "r1", "role": "rep", "capacity": 2},
    {"id": "r2", "role": "rep", "capacity": 2},
    {"id": "m1", "role": "manager", "capacity": 0},
]


class Base(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(REPS)


class TestAddLead(Base):
    def test_add_assigns_owner_and_score(self):
        lid = self.crm.add_lead(" A@Example.COM ", "Ann", "referral", "r1")
        lead = self.crm.leads[lid]
        self.assertEqual(lid, "L1")
        self.assertEqual(lead["email"], "a@example.com")
        self.assertEqual(lead["name"], "Ann")
        self.assertEqual(lead["score"], 45)  # referral 30 + non-free domain 15
        self.assertEqual(lead["owner"], "r1")
        self.assertEqual(lead["status"], "new")
        self.assertEqual(self.crm.log, [("add_lead", "L1", "r1")])
        # web/free domain: 10, no bonus; second lead goes to r2
        lid2 = self.crm.add_lead("b@gmail.com", "Bob", "web", "r1")
        self.assertEqual(self.crm.leads[lid2]["score"], 10)
        self.assertEqual(self.crm.leads[lid2]["owner"], "r2")

    def test_duplicate(self):
        self.crm.add_lead("a@x.com", "Ann", "web", "r1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            self.crm.add_lead("  A@X.COM ", "Ann", "web", "r1")
        self.assertEqual(ctx.exception.existing_id, "L1")
        self.assertEqual(self.crm.log, [("add_lead", "L1", "r1")])

    def test_validation_order(self):
        with self.assertRaises(PermissionError):
            self.crm.add_lead("bad", "n", "web", "nope")
        with self.assertRaises(ValueError):
            self.crm.add_lead("bad", "n", "web", "r1")  # email
        with self.assertRaises(ValueError):
            self.crm.add_lead("a@x.com", "  ", "web", "r1")  # name
        with self.assertRaises(ValueError):
            self.crm.add_lead("a@x.com", "n", "other", "r1")  # source
        with self.assertRaises(ValueError):
            self.crm.add_lead("a@x", "n", "web", "r1")
        with self.assertRaises(ValueError):
            self.crm.add_lead("a@x.com.", "n", "web", "r1")
        with self.assertRaises(ValueError):
            self.crm.add_lead("@x.com", "n", "web", "r1")
        self.assertEqual(self.crm.log, [])

    def test_waiting_queue_when_full(self):
        for i in range(6):
            lid = self.crm.add_lead("u%d@x.com" % i, "n", "web", "r1")
        self.assertEqual(self.crm.leads["L5"]["owner"], None)  # full -> queue
        with self.assertRaises(ValueError):
            self.crm.qualify(lid, "m1")  # score 10 too low, but exists


class TestQualify(Base):
    def test_ok_and_permissions(self):
        lid = self.crm.add_lead("a@corp.com", "Ann", "referral", "r1")  # score 45
        with self.assertRaises(PermissionError):
            self.crm.qualify(lid, "r2")
        self.crm.qualify(lid, "m1")
        self.assertEqual(self.crm.leads[lid]["status"], "qualified")
        with self.assertRaises(ValueError):
            self.crm.qualify(lid, "r1")  # already qualified

    def test_score_gate(self):
        lid = self.crm.add_lead("a@gmail.com", "Ann", "web", "r1")  # score 10
        with self.assertRaises(ValueError):
            self.crm.qualify(lid, "r1")


class TestConvertAdvance(Base):
    def make_lead_opp(self, actor="r1", amount=1000):
        lid = self.crm.add_lead("a@corp.com", "Ann", "referral", actor)
        self.crm.qualify(lid, actor)
        return self.crm.convert(lid, amount, actor)

    def test_convert_permission_and_status(self):
        lid = self.crm.add_lead("a@corp.com", "Ann", "referral", "r1")
        self.crm.qualify(lid, "r1")
        with self.assertRaises(PermissionError):
            self.crm.convert(lid, 100, "r2")
        with self.assertRaises(ValueError):
            self.crm.convert(lid, True, "r1")
        with self.assertRaises(ValueError):
            self.crm.convert(lid, 0, "r1")
        oid = self.crm.convert(lid, 1000, "r1")
        self.assertEqual(oid, "O1")
        self.assertEqual(self.crm.opps[oid]["stage"], "prospect")
        self.assertEqual(self.crm.leads[lid]["status"], "converted")

    def test_advance_chain_and_manager_gate(self):
        oid = self.make_lead_opp(amount=60000)
        with self.assertRaises(ValueError):
            self.crm.advance(oid, "won", "r1")
        self.crm.advance(oid, "proposal", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance(oid, "prospect", "r1")
        with self.assertRaises(PermissionError):
            self.crm.advance(oid, "negotiation", "r1")
        self.crm.advance(oid, "negotiation", "m1")
        self.crm.advance(oid, "won", "r1")
        self.assertEqual(self.crm.log[-1], ("advance", oid, "r1"))
        with self.assertRaises(ValueError):
            self.crm.advance(oid, "lost", "r1")

    def test_won_frees_slot_assigns_waiting(self):
        # fill both reps to capacity
        for e in "abcd":
            self.crm.add_lead(e + "@corp.com", e, "referral", "r1")
        wait = self.crm.add_lead("e@corp.com", "E", "referral", "r1")
        self.assertEqual(self.crm.leads[wait]["owner"], None)  # queued
        self.crm.qualify("L1", "r1")  # owns L1, L3
        oid = self.crm.convert("L1", 500, "r1")  # O1 owner r1
        self.crm.advance(oid, "proposal", "r1")
        self.crm.advance(oid, "negotiation", "m1")
        self.crm.advance(oid, "won", "m1")
        # r1 slot freed -> oldest waiting lead assigned
        assigned = [e for e in self.crm.log if e[0] == "assign"]
        self.assertEqual(assigned, [("assign", wait, "system")])
        self.assertEqual(self.crm.leads[wait]["owner"], "r1")

    def test_lost_from_any_stage(self):
        oid = self.make_lead_opp()
        self.crm.advance(oid, "lost", "r1")
        self.assertEqual(self.crm.opps[oid]["stage"], "lost")


class TestDiscount(Base):
    def test_rules(self):
        lid = self.crm.add_lead("a@corp.com", "Ann", "referral", "r1")
        self.crm.qualify(lid, "r1")
        oid = self.crm.convert(lid, 1000, "r1")
        with self.assertRaises(ValueError):
            self.crm.discount(oid, 40, "r1")
        with self.assertRaises(PermissionError):
            self.crm.discount(oid, 15, "r1")
        with self.assertRaises(ValueError):
            self.crm.discount(oid, True, "r1")
        self.crm.discount(oid, 10, "r1")  # 1000 -> 900
        self.assertEqual(self.crm.opps[oid]["amount"], 900)
        self.crm.discount(oid, 20, "m1")  # 900 -> 720, still >= 700
        self.assertEqual(self.crm.opps[oid]["amount"], 720)
        with self.assertRaises(ValueError):
            self.crm.discount(oid, 30, "m1")  # 720 -> 504 < 700
        self.assertEqual(self.crm.opps[oid]["amount"], 720)
        self.assertEqual(self.crm.log[-1], ("discount", oid, "m1"))


class TestTransfer(Base):
    def test_transfer_and_freed_slot(self):
        # r1 takes L1 (load 0), r2 takes L2
        lid = self.crm.add_lead("a@corp.com", "Ann", "referral", "r1")
        self.crm.add_lead("b@corp.com", "B", "referral", "r1")
        self.crm.qualify(lid, "r1")
        oid = self.crm.convert(lid, 1000, "r1")  # O1 owner r1
        with self.assertRaises(PermissionError):
            self.crm.transfer(oid, "r2", "r1")
        with self.assertRaises(ValueError):
            self.crm.transfer(oid, "m1", "m1")
        with self.assertRaises(ValueError):
            self.crm.transfer(oid, "r1", "m1")
        self.crm.transfer(oid, "r2", "m1")
        self.assertEqual(self.crm.opps[oid]["owner"], "r2")
        self.assertEqual(self.crm.log[-1], ("transfer", oid, "m1"))
        # no waiting leads -> no assign entries
        self.assertEqual([e for e in self.crm.log if e[0] == "assign"], [])


class TestForecast(Base):
    def test_forecast(self):
        lid = self.crm.add_lead("a@corp.com", "Ann", "referral", "r1")
        self.crm.qualify(lid, "r1")
        o1 = self.crm.convert(lid, 1000, "r1")
        self.crm.advance(o1, "proposal", "r1")
        lid2 = self.crm.add_lead("b@corp.com", "B", "referral", "r2")
        self.crm.qualify(lid2, "r2")
        o2 = self.crm.convert(lid2, 2000, "r2")
        self.crm.advance(o2, "proposal", "r2")
        self.crm.advance(o2, "negotiation", "r2")
        self.crm.advance(o2, "won", "r2")
        f = self.crm.forecast()
        self.assertEqual(f, {"open": 1, "weighted": 1000 * 30 // 100, "won": 2000})


if __name__ == "__main__":
    unittest.main()
