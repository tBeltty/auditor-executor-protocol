import unittest

from crm import CRM, DuplicateLeadError


def make_crm():
    return CRM([
        {"id": "r1", "role": "rep", "capacity": 1},
        {"id": "r2", "role": "rep", "capacity": 2},
        {"id": "m1", "role": "manager", "capacity": 10},
    ])


class TestActor(unittest.TestCase):
    def test_unknown_actor_first(self):
        c = make_crm()
        for call in (
            lambda: c.add_lead("a@b.co", "N", "web", "ghost"),
            lambda: c.qualify("L1", "ghost"),
            lambda: c.convert("L1", 100, "ghost"),
            lambda: c.advance("O1", "proposal", "ghost"),
            lambda: c.discount("O1", 5, "ghost"),
            lambda: c.transfer("O1", "r1", "ghost"),
        ):
            with self.assertRaises(PermissionError):
                call()
        self.assertEqual(c.log, [])


class TestAddLead(unittest.TestCase):
    def test_valid_lead_and_score(self):
        c = make_crm()
        lid = c.add_lead("  Jane@Acme.COM ", "  Jane ", "referral", "m1")
        lead = c.leads[lid]
        self.assertEqual(lead["email"], "jane@acme.com")
        self.assertEqual(lead["name"], "Jane")
        self.assertEqual(lead["score"], 30 + 15)
        self.assertEqual(lead["status"], "new")
        self.assertEqual(c.log, [("add_lead", "L1", "m1")])

    def test_free_domain_no_bonus(self):
        c = make_crm()
        lid = c.add_lead("x@gmail.com", "X", "web", "r1")
        self.assertEqual(c.leads[lid]["score"], 10)

    def test_email_validation(self):
        c = make_crm()
        for bad in ("noat.com", "@acme.com", "a@@b.com", "a@b", "a@.com",
                    "a@com.", 42):
            with self.assertRaises(ValueError):
                c.add_lead(bad, "N", "web", "r1")
        self.assertEqual(c.log, [])

    def test_name_and_source_validation(self):
        c = make_crm()
        with self.assertRaises(ValueError):
            c.add_lead("a@b.co", "   ", "web", "r1")
        with self.assertRaises(ValueError):
            c.add_lead("a@b.co", "N", "phone", "r1")
        self.assertEqual(c.leads, {})

    def test_duplicate(self):
        c = make_crm()
        lid = c.add_lead("A@B.com", "First", "web", "r1")
        with self.assertRaises(DuplicateLeadError) as cm:
            c.add_lead(" a@b.com ", "Second", "event", "r1")
        self.assertEqual(cm.exception.existing_id, lid)

    def test_round_robin_tie_lowest_load_smallest_id(self):
        c = make_crm()
        l1 = c.add_lead("a@b.co", "A", "web", "m1")   # r1 load 0, r2 load 0 -> r1
        l2 = c.add_lead("c@d.co", "C", "web", "m1")   # r1 full -> r2
        l3 = c.add_lead("e@f.co", "E", "web", "m1")   # r2 load 1 < r1 full -> r2
        self.assertEqual(c.leads[l1]["owner"], "r1")
        self.assertEqual(c.leads[l2]["owner"], "r2")
        self.assertEqual(c.leads[l3]["owner"], "r2")

    def test_waiting_queue_when_full(self):
        c = CRM([{"id": "r1", "role": "rep", "capacity": 1}])
        l1 = c.add_lead("a@b.co", "A", "web", "r1")
        l2 = c.add_lead("c@d.co", "C", "web", "r1")
        self.assertEqual(c.leads[l1]["owner"], "r1")
        self.assertIsNone(c.leads[l2]["owner"])


class TestQualifyConvert(unittest.TestCase):
    def _lead(self, c, email="a@b.co", source="referral"):
        return c.add_lead(email, "N", source, "m1")

    def test_qualify_flow(self):
        c = make_crm()
        lid = self._lead(c)  # referral -> score 45, owner r1
        c.qualify(lid, "r1")
        self.assertEqual(c.leads[lid]["status"], "qualified")
        self.assertEqual(c.log[-1], ("qualify", lid, "r1"))

    def test_qualify_errors(self):
        c = make_crm()
        lid = self._lead(c)
        with self.assertRaises(ValueError):
            c.qualify("L99", "r1")
        with self.assertRaises(PermissionError):
            c.qualify(lid, "r2")
        low = self._lead(c, "z@b.co", "web")  # owner r2, score 10
        with self.assertRaises(ValueError):
            c.qualify(low, "r2")
        c.qualify(lid, "m1")
        with self.assertRaises(ValueError):
            c.qualify(lid, "m1")  # not "new" anymore
        self.assertEqual(c.log, [("add_lead", lid, "m1"),
                                 ("add_lead", low, "m1"),
                                 ("qualify", lid, "m1")])

    def test_convert(self):
        c = make_crm()
        lid = self._lead(c)
        c.qualify(lid, "r1")
        oid = c.convert(lid, 1000, "r1")
        self.assertEqual(oid, "O1")
        opp = c.opps[oid]
        self.assertEqual(opp, {"id": "O1", "lead_id": lid, "owner": "r1",
                               "amount": 1000, "original_amount": 1000,
                               "stage": "prospect"})
        self.assertEqual(c.leads[lid]["status"], "converted")

    def test_convert_amount_validation(self):
        c = make_crm()
        lid = self._lead(c)
        c.qualify(lid, "r1")
        for bad in (0, -5, "100", 10.0, True):
            with self.assertRaises(ValueError):
                c.convert(lid, bad, "r1")

    def test_convert_unqualified_and_queue_owner_none(self):
        c = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 9},
        ])
        l1 = self._lead(c)
        l2 = self._lead(c, "c@d.co")  # waiting, owner None
        c.qualify(l1, "r1")
        c.qualify(l2, "m1")  # manager can qualify ownerless lead
        with self.assertRaises(ValueError):
            c.convert(l2, 500, "m1")  # owner None -> ValueError
        # check order: bad actor PermissionError before status ValueError
        with self.assertRaises(PermissionError):
            c.convert(l2, 500, "r2")


class TestAdvance(unittest.TestCase):
    def _opp(self, c, amount=1000):
        lid = c.add_lead("a@b.co", "N", "referral", "m1")
        c.qualify(lid, "r1")
        return c.convert(lid, amount, "r1")

    def test_full_path_and_logs(self):
        c = make_crm()
        oid = self._opp(c)
        for stage in ("proposal", "negotiation", "won"):
            c.advance(oid, stage, "r1")
        self.assertEqual(c.opps[oid]["stage"], "won")
        self.assertEqual([e[0] for e in c.log][-3:], ["advance"] * 3)

    def test_bad_transitions(self):
        c = make_crm()
        oid = self._opp(c)
        with self.assertRaises(ValueError):
            c.advance(oid, "won", "r1")       # skip
        with self.assertRaises(ValueError):
            c.advance(oid, "prospect", "r1")  # same stage
        with self.assertRaises(ValueError):
            c.advance(oid, "bogus", "r1")
        c.advance(oid, "lost", "r1")
        with self.assertRaises(ValueError):
            c.advance(oid, "lost", "r1")      # final
        self.assertEqual(c.opps[oid]["stage"], "lost")

    def test_permission(self):
        c = make_crm()
        oid = self._opp(c)
        with self.assertRaises(PermissionError):
            c.advance(oid, "proposal", "r2")
        with self.assertRaises(ValueError):
            c.advance("O99", "proposal", "r1")

    def test_big_negotiation_needs_manager(self):
        c = make_crm()
        oid = self._opp(c, amount=60000)
        c.advance(oid, "proposal", "r1")
        with self.assertRaises(PermissionError):
            c.advance(oid, "negotiation", "r1")
        c.advance(oid, "negotiation", "m1")

    def test_slot_freed_assigns_waiting(self):
        c = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 9},
        ])
        l1 = c.add_lead("a@b.co", "A", "referral", "m1")  # r1 now full
        l2 = c.add_lead("c@d.co", "C", "referral", "m1")  # waiting queue
        self.assertIsNone(c.leads[l2]["owner"])
        c.qualify(l1, "r1")
        oid = c.convert(l1, 1000, "r1")  # r1 still full (open opp)
        c.advance(oid, "proposal", "r1")
        c.advance(oid, "negotiation", "m1")
        c.advance(oid, "won", "r1")  # frees r1's slot -> drains queue
        self.assertEqual(c.leads[l2]["owner"], "r1")
        self.assertEqual(c.log[-2:], [
            ("advance", oid, "r1"),
            ("assign", l2, "system"),
        ])


class TestDiscount(unittest.TestCase):
    def _opp(self, c, amount=10000):
        lid = c.add_lead("a@b.co", "N", "referral", "m1")
        c.qualify(lid, "r1")
        return c.convert(lid, amount, "r1")

    def test_rep_and_manager_limits(self):
        c = make_crm()
        oid = self._opp(c)
        with self.assertRaises(PermissionError):
            c.discount(oid, 11, "r1")
        c.discount(oid, 10, "r1")
        self.assertEqual(c.opps[oid]["amount"], 9000)
        with self.assertRaises(ValueError):
            c.discount(oid, 30, "m1")  # cumulative would breach the 70% floor
        c.discount(oid, 22, "m1")
        self.assertEqual(c.opps[oid]["amount"], 7020)  # 9000*78//100
        self.assertEqual(c.log[-1], ("discount", oid, "m1"))

    def test_cumulative_floor(self):
        c = make_crm()
        oid = self._opp(c, amount=1000)
        c.discount(oid, 30, "m1")  # 700, at the 70% floor exactly
        with self.assertRaises(ValueError):
            c.discount(oid, 1, "m1")  # would go below 700

    def test_validation(self):
        c = make_crm()
        oid = self._opp(c)
        for bad in (0, 31, "5", 5.0, True):
            with self.assertRaises(ValueError):
                c.discount(oid, bad, "m1")
        with self.assertRaises(PermissionError):
            c.discount(oid, 5, "r2")
        with self.assertRaises(ValueError):
            c.discount("O42", 5, "m1")


class TestTransfer(unittest.TestCase):
    def _opp(self, c):
        lid = c.add_lead("a@b.co", "N", "referral", "m1")  # owner r1
        c.qualify(lid, "r1")
        return c.convert(lid, 500, "r1")

    def test_transfer_flow(self):
        c = make_crm()
        oid = self._opp(c)
        c.transfer(oid, "r2", "m1")
        self.assertEqual(c.opps[oid]["owner"], "r2")
        self.assertEqual(c.log[-1], ("transfer", oid, "m1"))
        with self.assertRaises(PermissionError):
            c.transfer(oid, "r1", "r1")  # actor must be a manager

    def test_transfer_checks(self):
        c = make_crm()
        oid = self._opp(c)
        with self.assertRaises(PermissionError):
            c.transfer(oid, "r2", "r1")      # actor must be manager
        with self.assertRaises(ValueError):
            c.transfer(oid, "m1", "m1")      # new owner must be rep
        with self.assertRaises(ValueError):
            c.transfer(oid, "ghost", "m1")
        with self.assertRaises(ValueError):
            c.transfer(oid, "r1", "m1")      # same owner
        c.transfer(oid, "r2", "m1")
        c.advance(oid, "proposal", "r2")
        c.advance(oid, "negotiation", "r2")
        c.advance(oid, "won", "r2")
        with self.assertRaises(ValueError):
            c.transfer(oid, "r1", "m1")      # final stage

    def test_transfer_capacity(self):
        c = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 0},
            {"id": "m1", "role": "manager", "capacity": 9},
        ])
        lid = c.add_lead("a@b.co", "N", "referral", "m1")  # r2 at cap 0 -> r1
        c.qualify(lid, "r1")
        oid = c.convert(lid, 500, "r1")
        with self.assertRaises(ValueError):
            c.transfer(oid, "r2", "m1")  # r2 over capacity

    def test_transfer_moves_ownership_and_no_assign_when_queue_empty(self):
        c = CRM([
            {"id": "r1", "role": "rep", "capacity": 2},
            {"id": "r2", "role": "rep", "capacity": 2},
            {"id": "m1", "role": "manager", "capacity": 9},
        ])
        l1 = c.add_lead("a@b.co", "N", "referral", "m1")  # r1 (tie -> smallest id)
        c.qualify(l1, "r1")
        oid = c.convert(l1, 500, "r1")
        l2 = c.add_lead("c@d.co", "C", "referral", "m1")  # r2 (load 0 vs 1)
        c.transfer(oid, "r2", "m1")
        self.assertEqual(c.opps[oid]["owner"], "r2")
        self.assertEqual(c.log[-1], ("transfer", oid, "m1"))
        self.assertNotIn("assign", [e[0] for e in c.log])
        # r1's slot freed: next lead goes to r1 (load 0)
        l3 = c.add_lead("e@f.co", "E", "referral", "m1")
        self.assertEqual(c.leads[l3]["owner"], "r1")


class TestForecast(unittest.TestCase):
    def test_forecast(self):
        c = CRM([
            {"id": "r1", "role": "rep", "capacity": 5},
            {"id": "m1", "role": "manager", "capacity": 5},
        ])

        def opp(amount):
            lid = c.add_lead("%s@b.co" % amount, "N", "referral", "m1")
            c.qualify(lid, "r1")
            return c.convert(lid, amount, "r1")

        o1, o2, o3 = opp(1000), opp(2000), opp(4000)
        c.advance(o2, "proposal", "r1")
        c.advance(o3, "proposal", "r1")
        c.advance(o3, "negotiation", "r1")
        f = c.forecast()
        self.assertEqual(f["open"], 3)
        self.assertEqual(f["weighted"], 1000 * 10 // 100 + 2000 * 30 // 100 + 4000 * 60 // 100)
        self.assertEqual(f["won"], 0)
        c.advance(o3, "won", "r1")
        f = c.forecast()
        self.assertEqual(f["open"], 2)
        self.assertEqual(f["won"], 4000)


if __name__ == "__main__":
    unittest.main()
