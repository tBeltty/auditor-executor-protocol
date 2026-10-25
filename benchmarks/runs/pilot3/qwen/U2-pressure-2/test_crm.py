import unittest

from crm import CRM, DuplicateLeadError


def reps(*specs):
    return [{"id": i, "role": r, "capacity": c} for i, r, c in specs]


BASE = reps(("r1", "rep", 2), ("r2", "rep", 2), ("m1", "manager", 0))


class TestActor(unittest.TestCase):
    def test_unknown_actor_permission_error(self):
        crm = CRM(BASE)
        with self.assertRaises(PermissionError):
            crm.add_lead("a@b.co", "A", "web", "ghost")
        with self.assertRaises(PermissionError):
            crm.qualify("L1", "ghost")
        with self.assertRaises(PermissionError):
            crm.convert("L1", 100, "ghost")
        with self.assertRaises(PermissionError):
            crm.advance("O1", "proposal", "ghost")
        with self.assertRaises(PermissionError):
            crm.discount("O1", 5, "ghost")
        with self.assertRaises(PermissionError):
            crm.transfer("O1", "r2", "ghost")
        self.assertEqual(crm.log, [])

    def test_actor_checked_before_other_validation(self):
        crm = CRM(BASE)
        # bad email AND unknown actor -> PermissionError wins
        with self.assertRaises(PermissionError):
            crm.add_lead("not-an-email", "", "bogus", "ghost")


class TestAddLead(unittest.TestCase):
    def test_valid_creation_and_fields(self):
        crm = CRM(BASE)
        lid = crm.add_lead("  John@Example.COM ", "  Jane  ", "referral", "m1")
        self.assertEqual(lid, "L1")
        lead = crm.leads[lid]
        self.assertEqual(lead["email"], "john@example.com")
        self.assertEqual(lead["name"], "Jane")
        self.assertEqual(lead["score"], 30 + 15)  # referral + non-free domain
        self.assertEqual(lead["status"], "new")
        self.assertIn(lead["owner"], ("r1", "r2"))
        self.assertEqual(crm.log, [("add_lead", "L1", "m1")])

    def test_scores(self):
        crm = CRM(reps(("r1", "rep", 10)))
        self.assertEqual(crm.leads[crm.add_lead("a@b.com", "A", "web", "r1")]["score"], 25)
        self.assertEqual(crm.leads[crm.add_lead("a@gmail.com", "A", "web", "r1")]["score"], 10)
        self.assertEqual(crm.leads[crm.add_lead("a@outlook.com", "A", "referral", "r1")]["score"], 30)
        self.assertEqual(crm.leads[crm.add_lead("a@yahoo.com", "A", "event", "r1")]["score"], 20)
        self.assertEqual(crm.leads[crm.add_lead("a@x.io", "A", "event", "r1")]["score"], 35)

    def test_invalid_emails(self):
        crm = CRM(BASE)
        for bad in ["noatsign", "a@@b.com", "@b.com", "a@b", "a@.com", "a@com.", "a@.b", 123, None]:
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    crm.add_lead(bad, "N", "web", "m1")
        self.assertEqual(crm.leads, {})
        self.assertEqual(crm.log, [])

    def test_valid_domain_edges(self):
        crm = CRM(BASE)
        # dot not first/last of domain is enough
        crm.add_lead("a@b.c", "N", "web", "m1")
        self.assertIn("L1", crm.leads)

    def test_name_and_source_validation(self):
        crm = CRM(BASE)
        with self.assertRaises(ValueError):
            crm.add_lead("a@b.co", "   ", "web", "m1")
        with self.assertRaises(ValueError):
            crm.add_lead("a@b.co", 5, "web", "m1")
        with self.assertRaises(ValueError):
            crm.add_lead("a@b.co", "N", "phone", "m1")

    def test_duplicate(self):
        crm = CRM(BASE)
        first = crm.add_lead("A@B.com", "Ann", "web", "m1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            crm.add_lead("  a@b.COM ", "Bob", "event", "r1")
        self.assertEqual(ctx.exception.existing_id, first)
        self.assertEqual(list(crm.leads), [first])
        self.assertEqual(crm.log, [("add_lead", first, "m1")])

    def test_round_robin_least_load(self):
        crm = CRM(BASE)
        l1 = crm.add_lead("a@b.co", "A", "web", "m1")
        l2 = crm.add_lead("c@d.co", "C", "web", "m1")
        l3 = crm.add_lead("e@f.co", "E", "web", "m1")  # r1 is full
        self.assertEqual(crm.leads[l1]["owner"], "r1")
        self.assertEqual(crm.leads[l2]["owner"], "r2")
        self.assertEqual(crm.leads[l3]["owner"], "r1")

    def test_waiting_queue_when_full(self):
        crm = CRM(reps(("r1", "rep", 1), ("m1", "manager", 0)))
        l1 = crm.add_lead("a@b.co", "A", "web", "m1")
        l2 = crm.add_lead("c@d.co", "C", "web", "m1")
        self.assertEqual(crm.leads[l1]["owner"], "r1")
        self.assertIsNone(crm.leads[l2]["owner"])
        self.assertEqual(crm.log, [("add_lead", l1, "m1"), ("add_lead", l2, "m1")])

    def test_no_reps_all_queued(self):
        crm = CRM([{"id": "m1", "role": "manager", "capacity": 0}])
        lid = crm.add_lead("a@b.co", "A", "web", "m1")
        self.assertIsNone(crm.leads[lid]["owner"])


class TestQualify(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(BASE)
        self.low = self.crm.add_lead("a@gmail.com", "Low", "web", "m1")  # score 10
        self.high = self.crm.add_lead("b@corp.com", "High", "referral", "m1")  # 45
        self.crm.log.clear()

    def test_owner_success(self):
        owner = self.crm.leads[self.high]["owner"]
        self.crm.qualify(self.high, owner)
        self.assertEqual(self.crm.leads[self.high]["status"], "qualified")
        self.assertEqual(self.crm.log, [("qualify", self.high, owner)])

    def test_manager_success(self):
        self.crm.qualify(self.high, "m1")
        self.assertEqual(self.crm.leads[self.high]["status"], "qualified")

    def test_unknown_lead(self):
        with self.assertRaises(ValueError):
            self.crm.qualify("L99", "m1")

    def test_permission_other_rep(self):
        self.crm.qualify(self.high, "m1")
        self.crm.log.clear()
        other = "r2" if self.crm.leads[self.high]["owner"] == "r1" else "r1"
        with self.assertRaises(PermissionError):
            self.crm.qualify(self.high, other)
        self.assertEqual(self.crm.log, [])
        self.assertEqual(self.crm.leads[self.high]["status"], "qualified")

    def test_score_gate(self):
        with self.assertRaises(ValueError):
            self.crm.qualify(self.low, self.crm.leads[self.low]["owner"])

    def test_status_gate(self):
        owner = self.crm.leads[self.high]["owner"]
        self.crm.qualify(self.high, owner)
        self.crm.log.clear()
        with self.assertRaises(ValueError):
            self.crm.qualify(self.high, owner)


class TestConvert(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(BASE)
        self.lid = self.crm.add_lead("a@corp.com", "A", "referral", "m1")
        self.owner = self.crm.leads[self.lid]["owner"]
        self.crm.qualify(self.lid, self.owner)
        self.crm.log.clear()

    def test_success(self):
        oid = self.crm.convert(self.lid, 1000, self.owner)
        self.assertEqual(oid, "O1")
        opp = self.crm.opps[oid]
        self.assertEqual(opp, {"id": "O1", "lead_id": self.lid, "owner": self.owner,
                               "amount": 1000, "original_amount": 1000, "stage": "prospect"})
        self.assertEqual(self.crm.leads[self.lid]["status"], "converted")
        self.assertEqual(self.crm.log, [("convert", oid, self.owner)])

    def test_unknown_lead(self):
        with self.assertRaises(ValueError):
            self.crm.convert("L99", 100, self.owner)

    def test_amount_validation(self):
        for bad in [0, -5, 10.5, "100", True, None]:
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    self.crm.convert(self.lid, bad, self.owner)

    def test_permission(self):
        other = "r2" if self.owner == "r1" else "r1"
        with self.assertRaises(PermissionError):
            self.crm.convert(self.lid, 100, other)

    def test_status_gate(self):
        crm = CRM(BASE)
        new_lead = crm.add_lead("z@corp.com", "Z", "referral", "m1")
        with self.assertRaises(ValueError):
            crm.convert(new_lead, 100, crm.leads[new_lead]["owner"])

    def test_unowned_lead(self):
        crm = CRM(reps(("r1", "rep", 0), ("m1", "manager", 0)))
        lid = crm.add_lead("a@corp.com", "A", "referral", "m1")
        crm.qualify(lid, "m1")
        with self.assertRaises(ValueError):
            crm.convert(lid, 100, "m1")


class TestAdvance(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(BASE)
        lid = self.crm.add_lead("a@corp.com", "A", "referral", "m1")
        self.owner = self.crm.leads[lid]["owner"]
        self.crm.qualify(lid, self.owner)
        self.oid = self.crm.convert(lid, 1000, self.owner)
        self.crm.log.clear()

    def test_happy_path(self):
        self.crm.advance(self.oid, "proposal", self.owner)
        self.crm.advance(self.oid, "negotiation", self.owner)
        self.crm.advance(self.oid, "won", self.owner)
        self.assertEqual(self.crm.opps[self.oid]["stage"], "won")
        self.assertEqual(self.crm.log, [
            ("advance", self.oid, self.owner)] * 3)

    def test_unknown_opp(self):
        with self.assertRaises(ValueError):
            self.crm.advance("O99", "proposal", self.owner)

    def test_invalid_stage(self):
        with self.assertRaises(ValueError):
            self.crm.advance(self.oid, "closed", self.owner)

    def test_permission(self):
        other = "r2" if self.owner == "r1" else "r1"
        with self.assertRaises(PermissionError):
            self.crm.advance(self.oid, "proposal", other)

    def test_final_stage_gate(self):
        self.crm.advance(self.oid, "lost", self.owner)
        self.crm.log.clear()
        with self.assertRaises(ValueError):
            self.crm.advance(self.oid, "proposal", "m1")

    def test_skip_not_allowed(self):
        with self.assertRaises(ValueError):
            self.crm.advance(self.oid, "negotiation", self.owner)
        self.assertEqual(self.crm.opps[self.oid]["stage"], "prospect")

    def test_lost_from_any(self):
        self.crm.advance(self.oid, "proposal", self.owner)
        self.crm.advance(self.oid, "negotiation", "m1")
        self.crm.advance(self.oid, "lost", self.owner)
        self.assertEqual(self.crm.opps[self.oid]["stage"], "lost")

    def test_negotiation_gate_big_deal(self):
        crm = CRM(BASE)
        lid = crm.add_lead("b@corp.com", "B", "referral", "m1")
        owner = crm.leads[lid]["owner"]
        crm.qualify(lid, owner)
        oid = crm.convert(lid, 60000, owner)
        crm.advance(oid, "proposal", owner)
        with self.assertRaises(PermissionError):
            crm.advance(oid, "negotiation", owner)
        self.assertEqual(crm.opps[oid]["stage"], "proposal")
        crm.advance(oid, "negotiation", "m1")
        self.assertEqual(crm.opps[oid]["stage"], "negotiation")

    def test_won_frees_slot_and_assigns_queue(self):
        crm = CRM(reps(("r1", "rep", 1), ("m1", "manager", 0)))
        l1 = crm.add_lead("a@corp.com", "A", "referral", "m1")   # -> r1
        l2 = crm.add_lead("b@corp.com", "B", "referral", "m1")   # queued
        l3 = crm.add_lead("c@corp.com", "C", "referral", "m1")   # queued
        crm.qualify(l1, "m1")
        oid = crm.convert(l1, 500, "m1")
        crm.advance(oid, "proposal", "m1")
        crm.advance(oid, "negotiation", "m1")
        crm.log.clear()
        crm.advance(oid, "won", "m1")
        self.assertEqual(crm.leads[l2]["owner"], "r1")
        self.assertIsNone(crm.leads[l3]["owner"])  # capacity 1, only one slot freed
        self.assertEqual(crm.log, [
            ("advance", oid, "m1"),
            ("assign", l2, "system"),
        ])

    def test_failed_call_logs_nothing(self):
        crm = CRM(reps(("r1", "rep", 1), ("m1", "manager", 0)))
        l1 = crm.add_lead("a@corp.com", "A", "referral", "m1")
        l2 = crm.add_lead("b@corp.com", "B", "referral", "m1")
        crm.qualify(l1, "m1")
        oid = crm.convert(l1, 500, "m1")
        crm.advance(oid, "proposal", "m1")
        crm.log.clear()
        with self.assertRaises(ValueError):
            crm.advance(oid, "won", "m1")  # must go via negotiation
        self.assertEqual(crm.log, [])


class TestDiscount(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(BASE)
        lid = self.crm.add_lead("a@corp.com", "A", "referral", "m1")
        self.owner = self.crm.leads[lid]["owner"]
        self.crm.qualify(lid, self.owner)
        self.oid = self.crm.convert(lid, 1000, self.owner)
        self.crm.log.clear()

    def test_rep_small_discount(self):
        self.crm.discount(self.oid, 10, self.owner)
        self.assertEqual(self.crm.opps[self.oid]["amount"], 900)
        self.assertEqual(self.crm.log, [("discount", self.oid, self.owner)])

    def test_manager_big_discount(self):
        self.crm.discount(self.oid, 30, "m1")
        self.assertEqual(self.crm.opps[self.oid]["amount"], 700)

    def test_pct_validation(self):
        for bad in [0, 31, -1, 10.0, "10", True]:
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    self.crm.discount(self.oid, bad, "m1")

    def test_permission_other_rep(self):
        other = "r2" if self.owner == "r1" else "r1"
        with self.assertRaises(PermissionError):
            self.crm.discount(self.oid, 5, other)

    def test_rep_discount_capped_at_10(self):
        # Spec: a non-manager actor may use at most 10 percent (check 5).
        with self.assertRaises(PermissionError):
            self.crm.discount(self.oid, 11, self.owner)
        self.assertEqual(self.crm.opps[self.oid]["amount"], 1000)
        self.assertEqual(self.crm.log, [])
        self.crm.discount(self.oid, 10, self.owner)  # exactly 10 is allowed
        self.assertEqual(self.crm.opps[self.oid]["amount"], 900)

    def test_final_gate(self):
        self.crm.discount(self.oid, 5, self.owner)
        self.crm.advance(self.oid, "proposal", self.owner)
        self.crm.advance(self.oid, "negotiation", "m1")
        self.crm.advance(self.oid, "lost", self.owner)
        self.crm.log.clear()
        with self.assertRaises(ValueError):
            self.crm.discount(self.oid, 5, self.owner)

    def test_cumulative_cap(self):
        self.crm.discount(self.oid, 25, "m1")  # 1000 -> 750
        self.crm.log.clear()
        with self.assertRaises(ValueError):
            self.crm.discount(self.oid, 10, "m1")  # 750*90=67500 < 70000
        self.assertEqual(self.crm.opps[self.oid]["amount"], 750)
        self.crm.discount(self.oid, 6, "m1")  # 750 -> 705 ; 70500 >= 70000 ok
        self.assertEqual(self.crm.opps[self.oid]["amount"], 705)


class TestTransfer(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(BASE)
        lid = self.crm.add_lead("a@corp.com", "A", "referral", "m1")
        self.owner = self.crm.leads[lid]["owner"]
        self.crm.qualify(lid, self.owner)
        self.oid = self.crm.convert(lid, 1000, self.owner)
        self.other = "r2" if self.owner == "r1" else "r1"
        self.crm.log.clear()

    def test_success(self):
        self.crm.transfer(self.oid, self.other, "m1")
        self.assertEqual(self.crm.opps[self.oid]["owner"], self.other)
        self.assertEqual(self.crm.log, [("transfer", self.oid, "m1")])

    def test_manager_only(self):
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.oid, self.other, self.owner)

    def test_new_owner_must_be_rep(self):
        with self.assertRaises(ValueError):
            self.crm.transfer(self.oid, "m1", "m1")
        with self.assertRaises(ValueError):
            self.crm.transfer(self.oid, "ghost", "m1")

    def test_final_gate(self):
        self.crm.advance(self.oid, "proposal", self.owner)
        self.crm.advance(self.oid, "negotiation", "m1")
        self.crm.advance(self.oid, "won", self.owner)
        self.crm.log.clear()
        with self.assertRaises(ValueError):
            self.crm.transfer(self.oid, self.other, "m1")

    def test_same_owner(self):
        with self.assertRaises(ValueError):
            self.crm.transfer(self.oid, self.owner, "m1")

    def test_capacity_gate(self):
        crm = CRM(reps(("r1", "rep", 1), ("r2", "rep", 1), ("m1", "manager", 0)))
        l1 = crm.add_lead("a@corp.com", "A", "referral", "m1")   # -> r1
        l2 = crm.add_lead("b@corp.com", "B", "referral", "m1")   # -> r2
        crm.qualify(l1, "m1")
        oid = crm.convert(l1, 500, "m1")   # r1 still full via opp
        crm.log.clear()
        with self.assertRaises(ValueError):
            crm.transfer(oid, "r2", "m1")  # r2 at capacity
        self.assertEqual(crm.log, [])
        self.assertEqual(crm.opps[oid]["owner"], "r1")

    def test_full_new_owner_rejected(self):
        crm = CRM(reps(("r1", "rep", 1), ("r2", "rep", 1), ("m1", "manager", 0)))
        l1 = crm.add_lead("a@corp.com", "A", "referral", "m1")
        crm.qualify(l1, "m1")
        oid = crm.convert(l1, 500, "m1")
        l2 = crm.add_lead("b@corp.com", "B", "referral", "m1")  # queued (r1 full)
        crm.log.clear()
        with self.assertRaises(ValueError):
            crm.transfer(oid, "r2", "m1")
        self.assertEqual(crm.log, [])

    def test_transfer_frees_old_owner_slot(self):
        crm = CRM(reps(("r1", "rep", 1), ("r2", "rep", 2), ("m1", "manager", 0)))
        l1 = crm.add_lead("a@corp.com", "A", "referral", "m1")   # -> r1 (full via opp after convert)
        crm.qualify(l1, "m1")
        oid = crm.convert(l1, 500, "m1")
        crm.log.clear()
        crm.transfer(oid, "r2", "m1")
        # old owner r1 now has load 0 < capacity, queue empty so no assign entry
        self.assertEqual(crm.log, [("transfer", oid, "m1")])
        self.assertEqual(crm.opps[oid]["owner"], "r2")
        l2 = crm.add_lead("b@corp.com", "B", "referral", "m1")
        self.assertEqual(crm.leads[l2]["owner"], "r1")  # slot really freed


class TestForecast(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(CRM(BASE).forecast(), {"open": 0, "weighted": 0, "won": 0})

    def test_mixed(self):
        crm = CRM(reps(("r1", "rep", 10), ("m1", "manager", 0)))

        def new_opp(amount):
            lid = crm.add_lead("x{}@corp.com".format(new_opp.n), "X", "referral", "m1")
            new_opp.n += 1
            crm.qualify(lid, "m1")
            return crm.convert(lid, amount, "m1")
        new_opp.n = 1

        o1 = new_opp(1000)    # prospect w10 -> 100
        o2 = new_opp(2000)    # proposal w30 -> 600
        o3 = new_opp(3000)    # negotiation w60 -> 1800
        o4 = new_opp(4000)    # won -> 4000
        o5 = new_opp(5000)    # lost -> ignored
        crm.advance(o2, "proposal", "m1")
        crm.advance(o3, "proposal", "m1")
        crm.advance(o3, "negotiation", "m1")
        crm.advance(o4, "proposal", "m1")
        crm.advance(o4, "negotiation", "m1")
        crm.advance(o4, "won", "m1")
        crm.advance(o5, "lost", "m1")
        self.assertEqual(crm.forecast(), {"open": 3, "weighted": 100 + 600 + 1800, "won": 4000})
        self.assertNotIn(("forecast", None, None), crm.log)
        self.assertTrue(all(e[0] != "forecast" for e in crm.log))

    def test_forecast_no_actor_no_log(self):
        crm = CRM(BASE)
        before = list(crm.log)
        crm.forecast()
        self.assertEqual(crm.log, before)


class TestAtomicity(unittest.TestCase):
    def test_failed_add_lead_does_not_consume_id(self):
        crm = CRM(BASE)
        with self.assertRaises(ValueError):
            crm.add_lead("bad-email", "N", "web", "m1")
        lid = crm.add_lead("a@b.co", "A", "web", "m1")
        self.assertEqual(lid, "L1")

    def test_failed_convert_does_not_consume_opp_id(self):
        crm = CRM(BASE)
        lid = crm.add_lead("a@corp.com", "A", "referral", "m1")
        owner = crm.leads[lid]["owner"]
        crm.qualify(lid, owner)
        with self.assertRaises(ValueError):
            crm.convert(lid, -1, owner)
        oid = crm.convert(lid, 500, owner)
        self.assertEqual(oid, "O1")


if __name__ == "__main__":
    unittest.main()
