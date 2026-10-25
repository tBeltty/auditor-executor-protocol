import unittest
from crm import CRM, DuplicateLeadError

REPS = [{"id": "r1", "role": "rep", "capacity": 2}, {"id": "r2", "role": "rep", "capacity": 2},
        {"id": "m1", "role": "manager", "capacity": 5}]

def mk(reps=None):
    return CRM(REPS if reps is None else reps)

def opp(c, owner_actor="r1", amount=1000, email="a@corp.com", src="referral"):
    lid = c.add_lead(email, "N", src, "m1")
    own = c.leads[lid]["owner"]
    c.qualify(lid, own)
    return c.convert(lid, amount, own)

class Leads(unittest.TestCase):
    def test_add_and_fields(self):
        c = mk(); lid = c.add_lead("  Bob@Corp.COM ", "  Bob  ", "referral", "r1")
        self.assertEqual(lid, "L1")
        self.assertEqual(c.leads["L1"], {"id": "L1", "email": "bob@corp.com", "name": "Bob", "source": "referral",
                                         "score": 45, "owner": "r1", "status": "new"})
        self.assertEqual(c.log, [("add_lead", "L1", "r1")])
    def test_scores(self):
        c = mk()
        for i, (s, d, sc) in enumerate([("web", "corp.com", 25), ("web", "gmail.com", 10), ("event", "x.io", 35),
                                        ("event", "yahoo.com", 20), ("referral", "outlook.com", 30)]):
            lid = c.add_lead("u%d@%s" % (i, d), "n", s, "m1")
            self.assertEqual(c.leads[lid]["score"], sc)
    def test_unknown_actor_first(self):
        c = mk()
        with self.assertRaises(PermissionError): c.add_lead("bad", "", "x", "zz")
    def test_bad_emails(self):
        c = mk()
        for e in ["", "a", "a@b", "@corp.com", "a@@corp.com", "a@b@corp.com", "a@.com", "a@corp.", "a@.", 5, None]:
            with self.assertRaises(ValueError, msg=repr(e)): c.add_lead(e, "n", "web", "r1")
        self.assertEqual((c.leads, c.log), ({}, []))
    def test_good_email_edges(self):
        c = mk(); c.add_lead("a@b.c", "n", "web", "r1"); c.add_lead("a@x.y.z", "n", "web", "r1")
    def test_bad_name_source(self):
        c = mk()
        for n in ["", "   ", None, 3]:
            with self.assertRaises(ValueError): c.add_lead("a@corp.com", n, "web", "r1")
        for s in ["Web", "ads", None]:
            with self.assertRaises(ValueError): c.add_lead("a@corp.com", "n", s, "r1")
    def test_validation_order(self):
        c = mk(); c.add_lead("a@corp.com", "n", "web", "r1")
        with self.assertRaises(ValueError): c.add_lead("a@corp.com", "", "web", "r1")
        with self.assertRaises(ValueError): c.add_lead("a@corp.com", "n", "bad", "r1")
    def test_duplicate(self):
        c = mk(); c.add_lead("a@corp.com", "n", "web", "r1")
        with self.assertRaises(DuplicateLeadError) as cm: c.add_lead(" A@CORP.com", "n2", "event", "r2")
        self.assertEqual(cm.exception.existing_id, "L1")
        self.assertEqual((len(c.leads), len(c.log)), (1, 1))
        self.assertEqual(c.add_lead("b@corp.com", "n", "web", "r1"), "L2")
    def test_failed_add_does_not_consume_id(self):
        c = mk()
        with self.assertRaises(ValueError): c.add_lead("bad", "n", "web", "r1")
        self.assertEqual(c.add_lead("a@corp.com", "n", "web", "r1"), "L1")
    def test_assign_balanced_ties(self):
        c = mk(); owners = [c.leads[c.add_lead("u%d@corp.com" % i, "n", "web", "m1")]["owner"] for i in range(4)]
        self.assertEqual(owners, ["r1", "r2", "r1", "r2"])
    def test_assign_lowest_load_not_first(self):
        c = mk([{"id": "b", "role": "rep", "capacity": 3}, {"id": "a", "role": "rep", "capacity": 3}])
        owners = [c.leads[c.add_lead("u%d@corp.com" % i, "n", "web", "a")]["owner"] for i in range(3)]
        self.assertEqual(owners, ["a", "b", "a"])
    def test_assign_skips_full_rep(self):
        c = mk([{"id": "r1", "role": "rep", "capacity": 1}, {"id": "r2", "role": "rep", "capacity": 3}])
        owners = [c.leads[c.add_lead("u%d@corp.com" % i, "n", "web", "r1")]["owner"] for i in range(4)]
        self.assertEqual(owners, ["r1", "r2", "r2", "r2"])
    def test_manager_never_owns(self):
        c = mk([{"id": "m", "role": "manager", "capacity": 99}])
        lid = c.add_lead("a@corp.com", "n", "web", "m"); self.assertIsNone(c.leads[lid]["owner"])
    def test_zero_capacity(self):
        c = mk([{"id": "r1", "role": "rep", "capacity": 0}])
        self.assertIsNone(c.leads[c.add_lead("a@corp.com", "n", "web", "r1")]["owner"])

class Qualify(unittest.TestCase):
    def test_ok(self):
        c = mk(); c.add_lead("a@corp.com", "n", "referral", "r1"); c.qualify("L1", "r1")
        self.assertEqual(c.leads["L1"]["status"], "qualified"); self.assertEqual(c.log[-1], ("qualify", "L1", "r1"))
    def test_manager_ok(self):
        c = mk(); c.add_lead("a@corp.com", "n", "referral", "r1"); c.qualify("L1", "m1")
    def test_score_threshold(self):
        c = mk(); c.add_lead("a@gmail.com", "n", "referral", "r1")  # 30
        c.qualify("L1", "r1")
        c.add_lead("b@corp.com", "n", "web", "r1")  # 25
        with self.assertRaises(ValueError): c.qualify("L2", "m1")
        c.add_lead("c@gmail.com", "n", "event", "r1")  # 20
        with self.assertRaises(ValueError): c.qualify("L3", "m1")
    def test_not_owner(self):
        c = mk(); c.add_lead("a@corp.com", "n", "referral", "r1")
        with self.assertRaises(PermissionError): c.qualify("L1", "r2")
    def test_missing_and_twice(self):
        c = mk(); c.add_lead("a@corp.com", "n", "referral", "r1")
        with self.assertRaises(ValueError): c.qualify("L9", "r1")
        c.qualify("L1", "r1")
        with self.assertRaises(ValueError): c.qualify("L1", "r1")
    def test_check_order(self):
        c = mk(); c.add_lead("a@corp.com", "n", "web", "r1")  # score 25, owner r1
        with self.assertRaises(PermissionError): c.qualify("L1", "r2")
        with self.assertRaises(ValueError): c.qualify("zz", "r2")
        with self.assertRaises(PermissionError): c.qualify("zz", "nobody")

class Convert(unittest.TestCase):
    def test_ok(self):
        c = mk(); c.add_lead("a@corp.com", "n", "referral", "r1"); c.qualify("L1", "r1")
        oid = c.convert("L1", 5000, "r1"); self.assertEqual(oid, "O1")
        self.assertEqual(c.opps["O1"], {"id": "O1", "lead_id": "L1", "owner": "r1", "amount": 5000,
                                        "original_amount": 5000, "stage": "prospect"})
        self.assertEqual(c.leads["L1"]["status"], "converted"); self.assertEqual(c.log[-1], ("convert", "O1", "r1"))
    def test_manager_converts(self):
        c = mk(); c.add_lead("a@corp.com", "n", "referral", "r1"); c.qualify("L1", "r1"); c.convert("L1", 1, "m1")
    def test_bad_amounts(self):
        c = mk(); c.add_lead("a@corp.com", "n", "referral", "r1"); c.qualify("L1", "r1")
        for a in [0, -5, True, 2.5, "9", None]:
            with self.assertRaises(ValueError, msg=repr(a)): c.convert("L1", a, "r1")
        self.assertEqual(c.leads["L1"]["status"], "qualified")
    def test_not_qualified(self):
        c = mk(); c.add_lead("a@corp.com", "n", "referral", "r1")
        with self.assertRaises(ValueError): c.convert("L1", 10, "r1")
    def test_permission_and_order(self):
        c = mk(); c.add_lead("a@corp.com", "n", "referral", "r1"); c.qualify("L1", "r1")
        with self.assertRaises(PermissionError): c.convert("L1", 10, "r2")
        with self.assertRaises(ValueError): c.convert("L1", 0, "r2")
    def test_no_owner(self):
        c = mk([{"id": "r1", "role": "rep", "capacity": 0}, {"id": "m1", "role": "manager", "capacity": 1}])
        c.add_lead("a@corp.com", "n", "referral", "m1"); c.qualify("L1", "m1")
        with self.assertRaises(ValueError): c.convert("L1", 10, "m1")
    def test_convert_keeps_load_and_twice(self):
        c = mk([{"id": "r1", "role": "rep", "capacity": 1}, {"id": "m1", "role": "manager", "capacity": 1}]); oid = opp(c)
        self.assertIsNone(c.leads[c.add_lead("z@corp.com", "n", "web", "m1")]["owner"])
        with self.assertRaises(ValueError): c.convert("L1", 10, "r1")
    def test_ids_increment(self):
        c = mk(); self.assertEqual((opp(c, email="a@corp.com"), opp(c, email="b@corp.com")), ("O1", "O2"))

class Advance(unittest.TestCase):
    def test_path(self):
        c = mk(); o = opp(c)
        for s in ["proposal", "negotiation", "won"]:
            c.advance(o, s, "r1"); self.assertEqual(c.opps[o]["stage"], s)
        self.assertEqual(c.log[-1], ("advance", o, "r1"))
    def test_lost_from_any(self):
        for path in [[], ["proposal"], ["proposal", "negotiation"]]:
            c = mk(); o = opp(c)
            for s in path: c.advance(o, s, "r1")
            c.advance(o, "lost", "m1"); self.assertEqual(c.opps[o]["stage"], "lost")
    def test_skip_back_same(self):
        c = mk(); o = opp(c)
        for s in ["negotiation", "won", "prospect"]:
            with self.assertRaises(ValueError): c.advance(o, s, "r1")
        c.advance(o, "proposal", "r1")
        for s in ["prospect", "proposal", "won"]:
            with self.assertRaises(ValueError): c.advance(o, s, "r1")
    def test_final_immutable(self):
        for fin in ["won", "lost"]:
            c = mk(); o = opp(c)
            if fin == "won":
                for s in ["proposal", "negotiation", "won"]: c.advance(o, s, "r1")
            else: c.advance(o, "lost", "r1")
            for s in ["lost", "won", "prospect"]:
                with self.assertRaises(ValueError): c.advance(o, s, "r1")
    def test_bad_stage_and_missing(self):
        c = mk(); o = opp(c)
        with self.assertRaises(ValueError): c.advance(o, "closed", "r1")
        with self.assertRaises(ValueError): c.advance("O9", "proposal", "r1")
    def test_permission(self):
        c = mk(); o = opp(c)
        with self.assertRaises(PermissionError): c.advance(o, "proposal", "r2")
        c.advance(o, "proposal", "m1")
        with self.assertRaises(PermissionError): c.advance(o, "bogus", "nobody")
    def test_order_perm_before_final(self):
        c = mk(); o = opp(c); c.advance(o, "lost", "r1")
        with self.assertRaises(PermissionError): c.advance(o, "won", "r2")
    def test_big_deal_negotiation(self):
        c = mk(); o = opp(c, amount=50001); c.advance(o, "proposal", "r1")
        with self.assertRaises(PermissionError): c.advance(o, "negotiation", "r1")
        self.assertEqual(c.opps[o]["stage"], "proposal")
        c.advance(o, "negotiation", "m1"); c.advance(o, "won", "r1")
    def test_boundary_50000(self):
        c = mk(); o = opp(c, amount=50000); c.advance(o, "proposal", "r1"); c.advance(o, "negotiation", "r1")
    def test_big_deal_lost_and_proposal_free(self):
        c = mk(); o = opp(c, amount=90000); c.advance(o, "proposal", "r1"); c.advance(o, "lost", "r1")
    def test_failed_advance_leaves_log(self):
        c = mk(); o = opp(c); n = len(c.log)
        with self.assertRaises(ValueError): c.advance(o, "won", "r1")
        self.assertEqual(len(c.log), n)

class Queue(unittest.TestCase):
    def setUp(self):
        self.c = mk([{"id": "r1", "role": "rep", "capacity": 1}, {"id": "m1", "role": "manager", "capacity": 1}])
    def test_waiting_and_fifo_release_on_lost(self):
        c = self.c; o = opp(c, email="a@corp.com")
        w1 = c.add_lead("w1@corp.com", "n", "web", "m1"); w2 = c.add_lead("w2@corp.com", "n", "web", "m1")
        self.assertEqual((c.leads[w1]["owner"], c.leads[w2]["owner"]), (None, None))
        c.advance(o, "lost", "r1")
        self.assertEqual((c.leads[w1]["owner"], c.leads[w2]["owner"]), ("r1", None))
        self.assertEqual(c.log[-2:], [("advance", o, "r1"), ("assign", w1, "system")])
    def test_release_on_won(self):
        c = self.c; o = opp(c, email="a@corp.com"); w = c.add_lead("w@corp.com", "n", "web", "m1")
        for s in ["proposal", "negotiation", "won"]: c.advance(o, s, "r1")
        self.assertEqual(c.leads[w]["owner"], "r1")
    def test_no_release_while_other_work(self):
        c = mk([{"id": "r1", "role": "rep", "capacity": 2}, {"id": "m1", "role": "manager", "capacity": 1}])
        o1 = opp(c, email="a@corp.com"); opp(c, email="b@corp.com")
        w = c.add_lead("w@corp.com", "n", "web", "m1"); self.assertIsNone(c.leads[w]["owner"])
        c.advance(o1, "lost", "r1"); self.assertEqual(c.leads[w]["owner"], "r1")
    def test_no_release_on_intermediate_stage(self):
        c = self.c; o = opp(c, email="a@corp.com"); w = c.add_lead("w@corp.com", "n", "web", "m1")
        c.advance(o, "proposal", "r1"); self.assertIsNone(c.leads[w]["owner"])
    def test_waiting_lead_ownerless_perms(self):
        c = self.c; opp(c, email="a@corp.com"); w = c.add_lead("w@corp.com", "n", "referral", "m1")
        with self.assertRaises(PermissionError): c.qualify(w, "r1")
        c.qualify(w, "m1")

class Discount(unittest.TestCase):
    def test_owner_10(self):
        c = mk(); o = opp(c, amount=1000); c.discount(o, 10, "r1")
        self.assertEqual(c.opps[o]["amount"], 900); self.assertEqual(c.opps[o]["original_amount"], 1000)
        self.assertEqual(c.log[-1], ("discount", o, "r1"))
    def test_owner_over_10(self):
        c = mk(); o = opp(c)
        with self.assertRaises(PermissionError): c.discount(o, 11, "r1")
        c.discount(o, 11, "m1")
    def test_manager_30_and_floor(self):
        c = mk(); o = opp(c, amount=1000); c.discount(o, 30, "m1"); self.assertEqual(c.opps[o]["amount"], 700)
        with self.assertRaises(ValueError): c.discount(o, 1, "m1")
        self.assertEqual(c.opps[o]["amount"], 700)
    def test_cumulative(self):
        c = mk(); o = opp(c, amount=1000)
        for _ in range(3): c.discount(o, 10, "r1")
        self.assertEqual(c.opps[o]["amount"], 729)
        c.discount(o, 3, "r1")
        self.assertEqual(c.opps[o]["amount"], 707)
        with self.assertRaises(ValueError): c.discount(o, 5, "r1")
        self.assertEqual(c.opps[o]["amount"], 707)
    def test_floor_exact(self):
        c = mk(); o = opp(c, amount=1000); c.discount(o, 20, "m1"); c.discount(o, 12, "m1")  # 800 -> 704
        self.assertEqual(c.opps[o]["amount"], 704)
        with self.assertRaises(ValueError): c.discount(o, 1, "m1")  # 696 < 700
    def test_floor_uses_floor_division(self):
        c = mk(); o = opp(c, amount=10); c.discount(o, 25, "m1")
        self.assertEqual(c.opps[o]["amount"], 7)
    def test_bad_pct(self):
        c = mk(); o = opp(c)
        for p in [0, -1, 31, True, 5.5, "5", None]:
            with self.assertRaises(ValueError, msg=repr(p)): c.discount(o, p, "m1")
    def test_perm_and_final(self):
        c = mk(); o = opp(c)
        with self.assertRaises(PermissionError): c.discount(o, 5, "r2")
        c.advance(o, "lost", "r1")
        with self.assertRaises(ValueError): c.discount(o, 5, "r1")
    def test_check_order(self):
        c = mk(); o = opp(c); c.advance(o, "lost", "r1")
        with self.assertRaises(ValueError): c.discount(o, 20, "r1")  # final before pct>10 perm
        with self.assertRaises(ValueError): c.discount(o, 99, "r2")  # pct before perm
        with self.assertRaises(PermissionError): c.discount(o, 5, "r2")
    def test_missing(self):
        with self.assertRaises(ValueError): mk().discount("O1", 5, "r1")
    def test_discount_affects_big_deal_rule(self):
        c = mk(); o = opp(c, amount=55000); c.advance(o, "proposal", "r1")
        c.discount(o, 10, "r1"); c.advance(o, "negotiation", "r1")

class Transfer(unittest.TestCase):
    def test_ok(self):
        c = mk(); o = opp(c); c.transfer(o, "r2", "m1")
        self.assertEqual(c.opps[o]["owner"], "r2"); self.assertEqual(c.log[-1], ("transfer", o, "m1"))
    def test_only_manager(self):
        c = mk(); o = opp(c)
        with self.assertRaises(PermissionError): c.transfer(o, "r2", "r1")
    def test_bad_target(self):
        c = mk(); o = opp(c)
        for t in ["m1", "zz", "r1"]:
            with self.assertRaises(ValueError): c.transfer(o, t, "m1")
    def test_capacity(self):
        c = mk([{"id": "r1", "role": "rep", "capacity": 2}, {"id": "r2", "role": "rep", "capacity": 1},
                {"id": "m1", "role": "manager", "capacity": 1}])
        o = opp(c, email="a@corp.com"); c.add_lead("b@corp.com", "n", "web", "m1")
        self.assertEqual(c.leads["L2"]["owner"], "r2")
        with self.assertRaises(ValueError): c.transfer(o, "r2", "m1")
    def test_final_missing(self):
        c = mk(); o = opp(c); c.advance(o, "lost", "r1")
        with self.assertRaises(ValueError): c.transfer(o, "r2", "m1")
        with self.assertRaises(ValueError): c.transfer("O9", "r2", "m1")
    def test_frees_old_owner_slot(self):
        c = mk([{"id": "r1", "role": "rep", "capacity": 1}, {"id": "r2", "role": "rep", "capacity": 1},
                {"id": "m1", "role": "manager", "capacity": 1}])
        o = opp(c, email="a@corp.com"); opp(c, email="b@corp.com")
        w = c.add_lead("w@corp.com", "n", "web", "m1"); self.assertIsNone(c.leads[w]["owner"])
        c.advance(c.opps[o]["id"], "lost", "r1")
        self.assertEqual(c.leads[w]["owner"], "r1")
    def test_transfer_releases_queue(self):
        c = mk([{"id": "r1", "role": "rep", "capacity": 1}, {"id": "r2", "role": "rep", "capacity": 2},
                {"id": "m1", "role": "manager", "capacity": 1}])
        o = opp(c, email="a@corp.com")  # owner r1 (lowest id tie) 
        self.assertEqual(c.opps[o]["owner"], "r1")
        w = c.add_lead("w@corp.com", "n", "web", "m1"); self.assertEqual(c.leads[w]["owner"], "r2")
        w2 = c.add_lead("w2@corp.com", "n", "web", "m1"); w3 = c.add_lead("w3@corp.com", "n", "web", "m1")
        self.assertEqual((c.leads[w2]["owner"], c.leads[w3]["owner"]), ("r2", None))
    def test_transfer_to_rep_with_room_then_release(self):
        c = mk([{"id": "r1", "role": "rep", "capacity": 1}, {"id": "r2", "role": "rep", "capacity": 1},
                {"id": "m1", "role": "manager", "capacity": 1}])
        o = opp(c, email="a@corp.com")  # r1
        c.advance(o, "lost", "r1")  # r1 free again, nothing waiting
        o = opp(c, email="b@corp.com")  # r1 (tie -> r1) 
        self.assertEqual(c.opps[o]["owner"], "r1")
        w = c.add_lead("w@corp.com", "n", "web", "m1"); self.assertEqual(c.leads[w]["owner"], "r2")
        w2 = c.add_lead("w2@corp.com", "n", "web", "m1"); self.assertIsNone(c.leads[w2]["owner"])
        c.advance(o, "lost", "r1"); self.assertEqual(c.leads[w2]["owner"], "r1")

class Forecast(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(mk().forecast(), {"open": 0, "weighted": 0, "won": 0})
    def test_mix(self):
        c = mk([{"id": "r1", "role": "rep", "capacity": 9}, {"id": "m1", "role": "manager", "capacity": 1}])
        a = opp(c, amount=1005, email="a@corp.com"); b = opp(c, amount=1005, email="b@corp.com")
        d = opp(c, amount=1005, email="d@corp.com"); e = opp(c, amount=400, email="e@corp.com")
        f = opp(c, amount=999, email="f@corp.com")
        c.advance(b, "proposal", "r1")
        for s in ["proposal", "negotiation"]: c.advance(d, s, "r1")
        for s in ["proposal", "negotiation", "won"]: c.advance(e, s, "r1")
        c.advance(f, "lost", "r1")
        self.assertEqual(c.forecast(), {"open": 3, "weighted": 100 + 301 + 603, "won": 400})
    def test_no_log(self):
        c = mk(); n = len(c.log); c.forecast(); self.assertEqual(len(c.log), n)

if __name__ == "__main__":
    unittest.main()
