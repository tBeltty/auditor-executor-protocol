import unittest

from crm import CRM, DuplicateLeadError

REPS = [
    {"id": "r1", "role": "rep", "capacity": 2},
    {"id": "r2", "role": "rep", "capacity": 2},
    {"id": "m1", "role": "manager", "capacity": 5},
]


def make(reps=None):
    return CRM([dict(r) for r in (reps or REPS)])


class TestAddLead(unittest.TestCase):
    def test_happy_path(self):
        c = make()
        lid = c.add_lead("  Bob@Example.com ", "  Bob  ", "web", "r1")
        self.assertEqual(lid, "L1")
        lead = c.leads[lid]
        self.assertEqual(lead["email"], "bob@example.com")
        self.assertEqual(lead["name"], "Bob")
        self.assertEqual(lead["score"], 25)
        self.assertEqual(lead["status"], "new")
        self.assertEqual(lead["owner"], "r1")
        self.assertEqual(c.log, [("add_lead", "L1", "r1")])

    def test_scores(self):
        c = make()
        self.assertEqual(c.leads[c.add_lead("a@gmail.com", "a", "referral", "r1")]["score"], 30)
        self.assertEqual(c.leads[c.add_lead("b@yahoo.com", "b", "event", "r1")]["score"], 20)
        self.assertEqual(c.leads[c.add_lead("c@corp.io", "c", "web", "r1")]["score"], 25)

    def test_email_rules(self):
        c = make()
        for bad in ["nope", "a@b@c.com", "@x.com", "a@com", "a@.com", "a@com.", 5]:
            with self.assertRaises(ValueError):
                c.add_lead(bad, "n", "web", "r1")
        self.assertEqual(c.log, [])

    def test_name_source_and_actor(self):
        c = make()
        with self.assertRaises(ValueError):
            c.add_lead("a@gmail.com", "   ", "web", "r1")
        with self.assertRaises(ValueError):
            c.add_lead("a@gmail.com", "a", "ads", "r1")
        with self.assertRaises(PermissionError):
            c.add_lead("a@gmail.com", "a", "web", "ghost")
        with self.assertRaises(PermissionError):
            c.add_lead("bad", "a", "web", "ghost")
        self.assertEqual(c.leads, {})
        self.assertEqual(c.log, [])

    def test_duplicate(self):
        c = make()
        first = c.add_lead("a@x.com", "a", "web", "r1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            c.add_lead("A@X.com", "a2", "event", "r1")
        self.assertEqual(ctx.exception.existing_id, first)
        self.assertEqual(len(c.leads), 1)
        self.assertEqual(c.add_lead("b@x.com", "b", "web", "r1"), "L2")

    def test_balances_load_then_queues_fifo(self):
        c = make()
        ids = [c.add_lead("u%d@x.com" % i, "u", "web", "r1") for i in range(5)]
        self.assertEqual(c.leads[ids[0]]["owner"], "r1")
        self.assertEqual(c.leads[ids[1]]["owner"], "r2")
        self.assertEqual(c.leads[ids[2]]["owner"], "r1")
        self.assertEqual(c.leads[ids[3]]["owner"], "r2")
        self.assertIsNone(c.leads[ids[4]]["owner"])
        self.assertEqual(c.queue, [ids[4]])
        self.assertEqual(c.add_lead("u10@x.com", "u", "web", "r1"), "L6")
        self.assertEqual(c.queue, [ids[4], "L6"])

    def test_tie_break_smallest_id(self):
        c = CRM([
            {"id": "b", "role": "rep", "capacity": 1},
            {"id": "a", "role": "rep", "capacity": 1},
        ])
        self.assertEqual(c.leads[c.add_lead("x@x.com", "x", "web", "a")]["owner"], "a")
        self.assertEqual(c.leads[c.add_lead("y@x.com", "y", "web", "b")]["owner"], "b")


class TestPipeline(unittest.TestCase):
    def test_qualify(self):
        c = make()
        web = c.add_lead("a@gmail.com", "a", "web", "r1")  # score 10
        ref = c.add_lead("b@gmail.com", "b", "referral", "r2")
        with self.assertRaises(ValueError):
            c.qualify(web, "r1")
        with self.assertRaises(PermissionError):
            c.qualify(ref, "r1")
        c.qualify(ref, "m1")
        self.assertEqual(c.leads[ref]["status"], "qualified")
        with self.assertRaises(ValueError):
            c.qualify(ref, "r2")
        with self.assertRaises(ValueError):
            c.qualify("L99", "r2")
        self.assertEqual(c.log[-1], ("qualify", ref, "m1"))

    def test_convert(self):
        c = make()
        lid = c.add_lead("a@x.com", "a", "referral", "r1")
        with self.assertRaises(ValueError):
            c.convert(lid, 10, "r1")
        c.qualify(lid, "r1")
        for bad in [0, -1, True, 1.5, "10"]:
            with self.assertRaises(ValueError):
                c.convert(lid, bad, "r1")
        oid = c.convert(lid, 1000, "r1")
        self.assertEqual(oid, "O1")
        self.assertEqual(c.leads[lid]["status"], "converted")
        self.assertEqual(c.opps[oid]["amount"], 1000)
        self.assertEqual(c.opps[oid]["original_amount"], 1000)
        self.assertEqual(c.opps[oid]["stage"], "prospect")
        self.assertEqual(c.opps[oid]["owner"], "r1")
        self.assertEqual(c.log[-1], ("convert", "O1", "r1"))

    def test_convert_requires_owner(self):
        c = make([{"id": "r1", "role": "rep", "capacity": 1}, {"id": "m1", "role": "manager", "capacity": 0}])
        a = c.add_lead("a@x.com", "a", "referral", "r1")
        b = c.add_lead("b@x.com", "b", "referral", "r1")
        self.assertIsNone(c.leads[b]["owner"])
        c.qualify(b, "m1")  # manager may qualify an unowned lead
        with self.assertRaises(ValueError):
            c.convert(b, 100, "m1")
        self.assertNotIn("O1", c.opps)
        self.assertEqual(c.leads[a]["owner"], "r1")


class TestAdvance(unittest.TestCase):
    def _opp(self, c, amount=1000, email="a@x.com", actor="r1"):
        lid = c.add_lead(email, "a", "referral", actor)
        c.qualify(lid, actor if c.leads[lid]["owner"] == actor else "m1")
        return c.convert(lid, amount, actor if c.leads[lid]["owner"] == actor else "m1")

    def test_transitions(self):
        c = make()
        oid = self._opp(c)
        with self.assertRaises(ValueError):
            c.advance(oid, "negotiation", "r1")
        with self.assertRaises(ValueError):
            c.advance(oid, "bogus", "r1")
        with self.assertRaises(PermissionError):
            c.advance(oid, "proposal", "r2")
        c.advance(oid, "proposal", "r1")
        c.advance(oid, "negotiation", "r1")
        c.advance(oid, "won", "r1")
        self.assertEqual(c.opps[oid]["stage"], "won")
        with self.assertRaises(ValueError):
            c.advance(oid, "lost", "r1")
        self.assertEqual(c.log[-1], ("advance", oid, "r1"))

    def test_lost_from_prospect(self):
        c = make()
        oid = self._opp(c)
        c.advance(oid, "lost", "r1")
        self.assertEqual(c.opps[oid]["stage"], "lost")

    def test_big_deal_needs_manager(self):
        c = make()
        oid = self._opp(c, amount=50001)
        c.advance(oid, "proposal", "r1")
        with self.assertRaises(PermissionError):
            c.advance(oid, "negotiation", "r1")
        self.assertEqual(c.opps[oid]["stage"], "proposal")
        c.advance(oid, "negotiation", "m1")
        self.assertEqual(c.opps[oid]["stage"], "negotiation")

    def test_exactly_50000_allowed(self):
        c = make()
        oid = self._opp(c, amount=50000)
        c.advance(oid, "proposal", "r1")
        c.advance(oid, "negotiation", "r1")
        self.assertEqual(c.opps[oid]["stage"], "negotiation")

    def test_win_frees_slot_and_assigns_fifo(self):
        c = make([{"id": "r1", "role": "rep", "capacity": 1}, {"id": "m1", "role": "manager", "capacity": 0}])
        a = c.add_lead("a@x.com", "a", "referral", "r1")
        b = c.add_lead("b@x.com", "b", "referral", "r1")
        self.assertEqual(c.queue, [b])
        c.qualify(a, "r1")
        oid = c.convert(a, 100, "r1")
        self.assertEqual(c.queue, [b])  # conversion does not free anything
        for stage in ("proposal", "negotiation", "won"):
            c.advance(oid, stage, "r1")
        self.assertEqual(c.leads[b]["owner"], "r1")
        self.assertEqual(c.queue, [])
        self.assertEqual(c.log[-1], ("assign", b, "system"))
        self.assertEqual(c.forecast()["won"], 100)

    def test_lost_also_frees_slot(self):
        c = make([{"id": "r1", "role": "rep", "capacity": 1}, {"id": "m1", "role": "manager", "capacity": 0}])
        a = c.add_lead("a@x.com", "a", "referral", "r1")
        c.qualify(a, "r1")
        oid = c.convert(a, 100, "r1")
        b = c.add_lead("b@x.com", "b", "web", "r1")
        self.assertIsNone(c.leads[b]["owner"])
        c.advance(oid, "lost", "r1")
        self.assertEqual(c.leads[b]["owner"], "r1")


class TestDiscount(unittest.TestCase):
    def _opp(self, c, amount=1000):
        lid = c.add_lead("a@x.com", "a", "referral", "r1")
        c.qualify(lid, "r1")
        return c.convert(lid, amount, "r1")

    def test_discount_math_and_log(self):
        c = make()
        oid = self._opp(c)
        c.discount(oid, 10, "r1")
        self.assertEqual(c.opps[oid]["amount"], 900)
        self.assertEqual(c.log[-1], ("discount", oid, "r1"))
        c.discount(oid, 20, "m1")
        self.assertEqual(c.opps[oid]["amount"], 720)
        c.discount(oid, 2, "m1")
        self.assertEqual(c.opps[oid]["amount"], 705)
        self.assertEqual(c.opps[oid]["original_amount"], 1000)

    def test_limits(self):
        c = make()
        oid = self._opp(c)
        with self.assertRaises(PermissionError):
            c.discount(oid, 11, "r1")
        for bad in [0, 31, True, 5.0]:
            with self.assertRaises(ValueError):
                c.discount(oid, bad, "r1")
        with self.assertRaises(PermissionError):
            c.discount(oid, 5, "r2")
        c.discount(oid, 10, "r1")
        c.discount(oid, 10, "m1")
        self.assertEqual(c.opps[oid]["amount"], 810)
        with self.assertRaises(ValueError):
            c.discount(oid, 15, "m1")
        self.assertEqual(c.opps[oid]["amount"], 810)

    def test_final_stage(self):
        c = make()
        oid = self._opp(c)
        c.advance(oid, "lost", "r1")
        with self.assertRaises(ValueError):
            c.discount(oid, 5, "m1")
        self.assertEqual(len(c.opps[oid]), 6)


class TestTransfer(unittest.TestCase):
    def _opp(self, c, actor="r1", email="a@x.com"):
        lid = c.add_lead(email, "a", "referral", actor)
        c.qualify(lid, actor)
        return c.convert(lid, 1000, actor)

    def test_transfer(self):
        c = make()
        oid = self._opp(c)
        with self.assertRaises(PermissionError):
            c.transfer(oid, "r2", "r1")
        with self.assertRaises(ValueError):
            c.transfer(oid, "m1", "m1")
        with self.assertRaises(ValueError):
            c.transfer(oid, "ghost", "m1")
        with self.assertRaises(ValueError):
            c.transfer(oid, "r1", "m1")
        c.transfer(oid, "r2", "m1")
        self.assertEqual(c.opps[oid]["owner"], "r2")
        self.assertEqual(c.log[-1], ("transfer", oid, "m1"))

    def test_transfer_capacity_and_final(self):
        c = make([{"id": "r1", "role": "rep", "capacity": 1}, {"id": "m1", "role": "manager", "capacity": 0}])
        oid = self._opp(c)
        with self.assertRaises(ValueError):
            c.transfer(oid, "ghost", "m1")
        c.add_lead("x@x.com", "x", "web", "m1")
        c.advance(oid, "lost", "r1")
        with self.assertRaises(ValueError):
            c.transfer(oid, "r1", "m1")

    def test_transfer_moves_opp_and_logs(self):
        c = make([{"id": "r1", "role": "rep", "capacity": 2}, {"id": "r2", "role": "rep", "capacity": 1},
                  {"id": "m1", "role": "manager", "capacity": 0}])
        oid = self._opp(c)  # r1: converted lead + open opp = load 1
        self.assertEqual(c._load("r1"), 1)
        c.transfer(oid, "r2", "m1")
        self.assertEqual(c.opps[oid]["owner"], "r2")
        self.assertEqual(c._load("r1"), 0)
        self.assertEqual(c.log[-1], ("transfer", oid, "m1"))


class TestForecast(unittest.TestCase):
    def test_forecast(self):
        c = make([{"id": "r1", "role": "rep", "capacity": 10}, {"id": "m1", "role": "manager", "capacity": 0}])
        self.assertEqual(c.forecast(), {"open": 0, "weighted": 0, "won": 0})
        for i, (stage, amount) in enumerate([("prospect", 1000), ("proposal", 2000), ("negotiation", 3000)]):
            lid = c.add_lead("u%d@x.com" % i, "u", "referral", "r1")
            c.qualify(lid, "r1")
            oid = c.convert(lid, amount, "r1")
            while c.opps[oid]["stage"] != stage:
                nxt = {"prospect": "proposal", "proposal": "negotiation"}[c.opps[oid]["stage"]]
                c.advance(oid, nxt, "r1")
        lid = c.add_lead("won@x.com", "w", "referral", "r1")
        c.qualify(lid, "r1")
        won = c.convert(lid, 5000, "r1")
        for st in ("proposal", "negotiation", "won"):
            c.advance(won, st, "r1")
        before = list(c.log)
        f = c.forecast()
        self.assertEqual(f, {"open": 3, "weighted": 100 + 600 + 1800, "won": 5000})
        self.assertEqual(c.log, before)

    def test_lost_ignored(self):
        c = make()
        lid = c.add_lead("a@x.com", "a", "referral", "r1")
        c.qualify(lid, "r1")
        oid = c.convert(lid, 700, "r1")
        c.advance(oid, "lost", "r1")
        self.assertEqual(c.forecast(), {"open": 0, "weighted": 0, "won": 0})


if __name__ == "__main__":
    unittest.main()
