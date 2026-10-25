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
    def test_domain_edge_dots(self):
        c = mk()
        for e in ["a@.corp.com", "a@corp.com.", "a@.corp.com."]:
            with self.assertRaises(ValueError, msg=e): c.add_lead(e, "n", "web", "r1")
    def test_duplicate_reports_matching_id(self):
        c = mk(); c.add_lead("a@corp.com", "n", "web", "r1"); c.add_lead("b@corp.com", "n", "web", "r1")
        with self.assertRaises(DuplicateLeadError) as cm: c.add_lead("B@corp.com", "n", "web", "r1")
        self.assertEqual(cm.exception.existing_id, "L2")
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


if __name__=="__main__":
    unittest.main()
