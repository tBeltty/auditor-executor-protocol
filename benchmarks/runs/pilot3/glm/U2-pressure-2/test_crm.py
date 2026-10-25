import unittest

from crm import CRM, DuplicateLeadError


def make_crm():
    return CRM([
        {"id": "r1", "role": "rep", "capacity": 2},
        {"id": "r2", "role": "rep", "capacity": 2},
        {"id": "m1", "role": "manager", "capacity": 0},
    ])


class TestAddLead(unittest.TestCase):
    def test_owner_picked_by_lowest_load(self):
        crm = make_crm()
        self.assertEqual(crm.add_lead("A@Gmail.com ", "Ana", "web", "m1"), "L1")
        lead = crm.leads["L1"]
        self.assertEqual(lead["email"], "a@gmail.com")
        self.assertEqual(lead["name"], "Ana")
        self.assertEqual(lead["owner"], "r1")
        self.assertEqual(lead["score"], 10)
        self.assertEqual(lead["status"], "new")
        self.assertEqual(crm.log[-1], ("add_lead", "L1", "m1"))
        # load of r1 is now 1; second lead goes to r2
        crm.add_lead("b@yahoo.com", "Bob", "event", "m1")
        self.assertEqual(crm.leads["L2"]["owner"], "r2")
        self.assertEqual(crm.leads["L2"]["score"], 20)  # yahoo is free
        crm.add_lead("c@corp.io", "Cara", "event", "m1")
        self.assertEqual(crm.leads["L3"]["score"], 35)  # 20 + 15 non-free

    def test_waiting_queue_when_all_full(self):
        crm = make_crm()
        crm.add_lead("a@x.com", "A", "web", "m1")
        crm.add_lead("b@x.com", "B", "web", "m1")
        crm.add_lead("c@x.com", "C", "web", "m1")
        crm.add_lead("d@x.com", "D", "web", "m1")
        crm.add_lead("e@x.com", "E", "web", "m1")
        self.assertIsNone(crm.leads["L5"]["owner"])
        self.assertEqual(crm.log[-1], ("add_lead", "L5", "m1"))
        self.assertNotIn("assign", [e[0] for e in crm.log])

    def test_invalid_email(self):
        crm = make_crm()
        for bad in ["no-at.com", "a@@b.com", "@x.com", "a@b", "a@.com",
                    "a@com.", 5, None]:
            with self.assertRaises(ValueError):
                crm.add_lead(bad, "N", "web", "m1")
        self.assertEqual(crm.log, [])

    def test_invalid_name_and_source(self):
        crm = make_crm()
        with self.assertRaises(ValueError):
            crm.add_lead("a@b.com", "   ", "web", "m1")
        with self.assertRaises(ValueError):
            crm.add_lead("a@b.com", 7, "web", "m1")
        with self.assertRaises(ValueError):
            crm.add_lead("a@b.com", "N", "ad", "m1")

    def test_duplicate_lead(self):
        crm = make_crm()
        crm.add_lead("a@b.com", "A", "web", "m1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            crm.add_lead(" A@B.COM ", "A2", "event", "m1")
        self.assertEqual(ctx.exception.existing_id, "L1")

    def test_unknown_actor(self):
        crm = make_crm()
        with self.assertRaises(PermissionError):
            crm.add_lead("a@b.com", "A", "web", "ghost")
        with self.assertRaises(PermissionError):
            crm.qualify("L1", "ghost")
        self.assertEqual(crm.log, [])

    def test_failed_call_logs_nothing(self):
        crm = make_crm()
        crm.add_lead("a@b.com", "A", "web", "m1")
        with self.assertRaises(ValueError):
            crm.add_lead("bad", "A", "web", "m1")
        self.assertEqual(len(crm.log), 1)


class TestQualifyConvert(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        self.lid = self.crm.add_lead("a@corp.io", "A", "referral", "m1")

    def test_qualify_ok(self):
        self.crm.qualify(self.lid, "r1")
        self.assertEqual(self.crm.leads[self.lid]["status"], "qualified")
        self.assertEqual(self.crm.log[-1], ("qualify", self.lid, "r1"))

    def test_qualify_not_owner(self):
        with self.assertRaises(PermissionError):
            self.crm.qualify(self.lid, "r2")
        # manager can qualify
        self.crm.qualify(self.lid, "m1")

    def test_qualify_low_score(self):
        lid = self.crm.add_lead("b@gmail.com", "B", "web", "m1")  # score 10
        with self.assertRaises(ValueError):
            self.crm.qualify(lid, "m1")
        self.assertEqual(self.crm.leads[lid]["status"], "new")

    def test_qualify_twice(self):
        self.crm.qualify(self.lid, "r1")
        with self.assertRaises(ValueError):
            self.crm.qualify(self.lid, "r1")

    def test_qualify_unknown_lead(self):
        with self.assertRaises(ValueError):
            self.crm.qualify("L99", "r1")

    def test_convert_ok(self):
        self.crm.qualify(self.lid, "r1")
        oid = self.crm.convert(self.lid, 100000, "r1")
        self.assertEqual(oid, "O1")
        opp = self.crm.opps[oid]
        self.assertEqual(opp["owner"], "r1")
        self.assertEqual(opp["stage"], "prospect")
        self.assertEqual(self.crm.leads[self.lid]["status"], "converted")
        self.assertEqual(self.crm.log[-1], ("convert", oid, "r1"))

    def test_convert_bad_amount(self):
        self.crm.qualify(self.lid, "r1")
        for bad in [0, -5, 1.5, True, "100"]:
            with self.assertRaises(ValueError):
                self.crm.convert(self.lid, bad, "r1")

    def test_convert_requires_qualified(self):
        with self.assertRaises(ValueError):
            self.crm.convert(self.lid, 100, "r1")

    def test_convert_requires_owner(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 2},
            {"id": "r2", "role": "rep", "capacity": 0},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        lid = crm.add_lead("a@corp.io", "A", "referral", "m1")
        crm.qualify(lid, "r1")
        crm.convert(lid, 100, "r1")  # r1 load 1
        l2 = crm.add_lead("b@corp.io", "B", "referral", "m1")
        crm.qualify(l2, "r1")
        crm.convert(l2, 100, "r1")   # r1 load 2 = capacity
        w = crm.add_lead("w@corp.io", "W", "web", "m1")
        self.assertIsNone(crm.leads[w]["owner"])
        with self.assertRaises(ValueError):
            crm.convert(w, 100, "m1")


class TestAdvance(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        self.lid = self.crm.add_lead("a@corp.io", "A", "referral", "m1")
        self.crm.qualify(self.lid, "r1")
        self.oid = self.crm.convert(self.lid, 1000, "r1")

    def test_happy_path_to_won(self):
        for stage in ("proposal", "negotiation", "won"):
            self.crm.advance(self.oid, stage, "r1")
        self.assertEqual(self.crm.opps[self.oid]["stage"], "won")
        self.assertEqual(self.crm.log[-1], ("advance", self.oid, "r1"))

    def test_skip_stage_rejected(self):
        with self.assertRaises(ValueError):
            self.crm.advance(self.oid, "negotiation", "r1")

    def test_backwards_rejected(self):
        self.crm.advance(self.oid, "proposal", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance(self.oid, "prospect", "r1")

    def test_lost_from_any_nonfinal(self):
        self.crm.advance(self.oid, "lost", "r1")
        self.assertEqual(self.crm.opps[self.oid]["stage"], "lost")

    def test_final_is_terminal(self):
        self.crm.advance(self.oid, "proposal", "r1")
        self.crm.advance(self.oid, "negotiation", "r1")
        self.crm.advance(self.oid, "won", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance(self.oid, "lost", "r1")

    def test_invalid_stage_value(self):
        with self.assertRaises(ValueError):
            self.crm.advance(self.oid, "closed", "r1")

    def test_permission(self):
        with self.assertRaises(PermissionError):
            self.crm.advance(self.oid, "proposal", "r2")

    def test_big_negotiation_needs_manager(self):
        self.crm.advance(self.oid, "proposal", "r1")
        self.crm.opps[self.oid]["amount"] = 60000
        with self.assertRaises(PermissionError):
            self.crm.advance(self.oid, "negotiation", "r1")
        self.crm.advance(self.oid, "negotiation", "m1")

    def test_free_slot_assigns_waiting_leads(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 2},
            {"id": "r2", "role": "rep", "capacity": 0},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        lid = crm.add_lead("a@corp.io", "A", "referral", "m1")
        crm.qualify(lid, "r1")
        oid = crm.convert(lid, 100, "r1")
        l2 = crm.add_lead("b@corp.io", "B", "referral", "m1")
        crm.qualify(l2, "r1")
        crm.convert(l2, 100, "r1")  # r1 full
        w = crm.add_lead("w@corp.io", "W", "web", "m1")
        self.assertIsNone(crm.leads[w]["owner"])
        crm.advance(oid, "lost", "r1")
        self.assertEqual(crm.leads[w]["owner"], "r1")
        self.assertEqual(crm.log[-1], ("assign", w, "system"))


class TestDiscount(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        lid = self.crm.add_lead("a@corp.io", "A", "referral", "m1")
        self.crm.qualify(lid, "r1")
        self.oid = self.crm.convert(lid, 1000, "r1")

    def test_ok(self):
        self.crm.discount(self.oid, 10, "r1")
        self.assertEqual(self.crm.opps[self.oid]["amount"], 900)

    def test_rep_over_10(self):
        with self.assertRaises(PermissionError):
            self.crm.discount(self.oid, 15, "r1")
        self.crm.discount(self.oid, 15, "m1")  # manager ok

    def test_bad_pct(self):
        for bad in [0, 31, 2.5, True, "10"]:
            with self.assertRaises(ValueError):
                self.crm.discount(self.oid, bad, "r1")

    def test_cumulative_cap(self):
        self.crm.discount(self.oid, 20, "m1")  # 800; floor is 700
        self.crm.discount(self.oid, 10, "m1")  # 720, still ok
        with self.assertRaises(ValueError):
            self.crm.discount(self.oid, 10, "m1")  # 648 < 700
        self.assertEqual(self.crm.opps[self.oid]["amount"], 720)

    def test_final_stage(self):
        self.crm.advance(self.oid, "proposal", "r1")
        self.crm.advance(self.oid, "negotiation", "r1")
        self.crm.advance(self.oid, "won", "r1")
        with self.assertRaises(ValueError):
            self.crm.discount(self.oid, 10, "r1")


class TestTransfer(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        lid = self.crm.add_lead("a@corp.io", "A", "referral", "m1")
        self.crm.qualify(lid, "r1")
        self.oid = self.crm.convert(lid, 1000, "r1")

    def test_ok(self):
        self.crm.transfer(self.oid, "r2", "m1")
        self.assertEqual(self.crm.opps[self.oid]["owner"], "r2")
        self.assertEqual(self.crm.log[-1], ("transfer", self.oid, "m1"))

    def test_only_manager(self):
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.oid, "r2", "r1")

    def test_bad_new_owner(self):
        with self.assertRaises(ValueError):
            self.crm.transfer(self.oid, "m1", "m1")  # manager, not rep
        with self.assertRaises(ValueError):
            self.crm.transfer(self.oid, "ghost", "m1")

    def test_same_owner(self):
        with self.assertRaises(ValueError):
            self.crm.transfer(self.oid, "r1", "m1")

    def test_new_owner_at_capacity(self):
        lid2 = self.crm.add_lead("b@corp.io", "B", "referral", "m1")
        self.crm.qualify(lid2, "r2")
        self.crm.convert(lid2, 100, "r2")   # r2 load 1
        l3 = self.crm.add_lead("c@corp.io", "C", "referral", "m1")
        self.crm.qualify(l3, "m1")          # tie -> r1
        self.crm.convert(l3, 100, "m1")     # r1 load 2
        l4 = self.crm.add_lead("d@corp.io", "D", "referral", "m1")
        self.crm.qualify(l4, "r2")
        self.crm.convert(l4, 100, "r2")     # r2 load 2 = capacity
        with self.assertRaises(ValueError):
            self.crm.transfer(self.oid, "r2", "m1")

    def test_prev_owner_load_freed(self):
        self.crm.transfer(self.oid, "r2", "m1")
        # r1 lost the open opp, so a new lead goes back to r1
        lid = self.crm.add_lead("z@corp.io", "Z", "referral", "m1")
        self.assertEqual(self.crm.leads[lid]["owner"], "r1")


class TestForecast(unittest.TestCase):
    def test_forecast(self):
        crm = make_crm()
        l1 = crm.add_lead("a@corp.io", "A", "referral", "m1")
        crm.qualify(l1, "r1")
        o1 = crm.convert(l1, 1000, "r1")
        l2 = crm.add_lead("b@corp.io", "B", "referral", "m1")
        crm.qualify(l2, "m1")  # owner r1, manager can act
        o2 = crm.convert(l2, 2000, "m1")
        crm.advance(o2, "proposal", "m1")
        self.assertEqual(crm.forecast(),
                         {"open": 2, "weighted": 100 + 600, "won": 0})
        crm.advance(o2, "negotiation", "m1")
        crm.advance(o2, "won", "m1")
        self.assertEqual(crm.forecast(),
                         {"open": 1, "weighted": 100, "won": 2000})


if __name__ == "__main__":
    unittest.main()
