import unittest

from crm import CRM, DuplicateLeadError

REPS = [
    {"id": "r1", "role": "rep", "capacity": 2},
    {"id": "r2", "role": "rep", "capacity": 1},
    {"id": "m1", "role": "manager", "capacity": 0},
]


def make():
    return CRM(REPS)


class AddLeadTest(unittest.TestCase):
    def test_happy_path_and_scoring(self):
        c = make()
        lid = c.add_lead(" A@Gmail.com ", " Bob ", "referral", "r1")
        self.assertEqual(lid, "L1")
        lead = c.leads[lid]
        self.assertEqual(lead["email"], "a@gmail.com")
        self.assertEqual(lead["name"], "Bob")
        self.assertEqual(lead["score"], 30)  # free domain
        self.assertEqual(lead["owner"], "r1")
        self.assertEqual(lead["status"], "new")
        self.assertEqual(c.log, [("add_lead", "L1", "r1")])

    def test_corporate_domain_bonus(self):
        c = make()
        lid = c.add_lead("a@acme.co", "Bob", "web", "r1")
        self.assertEqual(c.leads[lid]["score"], 25)

    def test_bad_email(self):
        c = make()
        for bad in (123, "noat.com", "a@b@c.com", "@b.com", "a@", "a@b", "a@.b", "a@b."):
            with self.assertRaises(ValueError):
                c.add_lead(bad, "n", "web", "r1")
        self.assertEqual(c.log, [])

    def test_bad_name_or_source(self):
        c = make()
        with self.assertRaises(ValueError):
            c.add_lead("a@b.com", "  ", "web", "r1")
        with self.assertRaises(ValueError):
            c.add_lead("a@b.com", "n", "phone", "r1")

    def test_unknown_actor(self):
        c = make()
        with self.assertRaises(PermissionError):
            c.add_lead("a@b.com", "n", "web", "zz")
        self.assertEqual(c.log, [])

    def test_duplicate_email(self):
        c = make()
        l1 = c.add_lead("a@b.com", "n", "web", "r1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            c.add_lead(" A@B.COM ", "x", "referral", "r1")
        self.assertEqual(ctx.exception.existing_id, l1)

    def test_capacity_and_queue(self):
        c = make()  # r1 cap 2, r2 cap 1
        a = c.add_lead("a@b.com", "n", "web", "r1")   # -> r1
        b = c.add_lead("b@b.com", "n", "web", "r1")   # r1 load 1, r2 load 0 -> r2
        e = c.add_lead("e@b.com", "n", "web", "r1")   # r2 full -> r1 (load 2)
        d = c.add_lead("d@b.com", "n", "web", "r1")   # both full -> queued
        self.assertEqual(c.leads[a]["owner"], "r1")
        self.assertEqual(c.leads[b]["owner"], "r2")
        self.assertEqual(c.leads[e]["owner"], "r1")
        self.assertIsNone(c.leads[d]["owner"])


class QualifyConvertTest(unittest.TestCase):
    def test_qualify_and_convert(self):
        c = make()
        lid = c.add_lead("a@b.com", "n", "referral", "r1")
        c.qualify(lid, "r1")
        self.assertEqual(c.leads[lid]["status"], "qualified")
        oid = c.convert(lid, 1000, "r1")
        self.assertEqual(oid, "O1")
        self.assertEqual(c.leads[lid]["status"], "converted")
        self.assertEqual(c.opps[oid]["owner"], "r1")
        self.assertEqual(c.opps[oid]["stage"], "prospect")
        self.assertEqual(c.log[-1], ("convert", "O1", "r1"))

    def test_qualify_low_score(self):
        c = make()
        lid = c.add_lead("a@b.com", "n", "web", "r1")  # score 25
        with self.assertRaises(ValueError):
            c.qualify(lid, "r1")

    def test_qualify_non_owner_rep(self):
        c = make()
        lid = c.add_lead("a@b.com", "n", "referral", "r1")
        with self.assertRaises(PermissionError):
            c.qualify(lid, "r2")
        c.qualify(lid, "m1")  # manager ok

    def test_qualify_twice(self):
        c = make()
        lid = c.add_lead("a@b.com", "n", "referral", "r1")
        c.qualify(lid, "r1")
        with self.assertRaises(ValueError):
            c.qualify(lid, "r1")

    def test_convert_checks(self):
        c = make()
        lid = c.add_lead("a@b.com", "n", "referral", "r1")
        with self.assertRaises(ValueError):
            c.convert(lid, True, "r1")  # bool
        with self.assertRaises(ValueError):
            c.convert(lid, 0, "r1")
        c.qualify(lid, "r1")
        c.convert(lid, 5, "r1")
        with self.assertRaises(ValueError):
            c.convert(lid, 5, "r1")  # not qualified anymore
        with self.assertRaises(ValueError):
            c.convert("L99", 5, "r1")


class AdvanceTest(unittest.TestCase):
    def build_opp(self, amount=100):
        c = make()
        lid = c.add_lead("a@b.com", "n", "referral", "r1")
        c.qualify(lid, "r1")
        oid = c.convert(lid, amount, "r1")
        return c, oid

    def test_advance_path(self):
        c, oid = self.build_opp()
        c.advance(oid, "proposal", "r1")
        c.advance(oid, "negotiation", "r1")
        c.advance(oid, "won", "r1")
        self.assertEqual(c.opps[oid]["stage"], "won")
        with self.assertRaises(ValueError):
            c.advance(oid, "lost", "r1")

    def test_advance_skip_invalid(self):
        c, oid = self.build_opp()
        with self.assertRaises(ValueError):
            c.advance(oid, "negotiation", "r1")

    def test_advance_unknown_stage(self):
        c, oid = self.build_opp()
        with self.assertRaises(ValueError):
            c.advance(oid, "pending", "r1")

    def test_big_deal_needs_manager(self):
        c, oid = self.build_opp(60000)
        c.advance(oid, "proposal", "r1")
        with self.assertRaises(PermissionError):
            c.advance(oid, "negotiation", "r1")
        c.advance(oid, "negotiation", "m1")

    def test_non_owner_rep(self):
        c, oid = self.build_opp()
        with self.assertRaises(PermissionError):
            c.advance(oid, "proposal", "r2")

    def test_won_frees_slot_and_assigns_waiting(self):
        c = make()  # r1 cap 2, r2 cap 1
        l1 = c.add_lead("a@b.com", "n", "referral", "r1")  # -> r1
        c.add_lead("b@b.com", "n", "referral", "r1")       # -> r2
        c.add_lead("c@b.com", "n", "web", "r1")            # -> r1 (r1 load 2)
        l4 = c.add_lead("d@b.com", "n", "web", "r1")       # queued
        self.assertIsNone(c.leads[l4]["owner"])
        c.qualify(l1, "r1")
        oid = c.convert(l1, 100, "r1")
        c.advance(oid, "proposal", "r1")
        c.advance(oid, "negotiation", "r1")
        c.advance(oid, "won", "r1")  # frees one slot -> assign oldest waiting
        self.assertEqual(c.leads[l4]["owner"], "r1")
        self.assertIn(("assign", l4, "system"), c.log)


class DiscountTest(unittest.TestCase):
    def build(self):
        c = make()
        lid = c.add_lead("a@b.com", "n", "referral", "r1")
        c.qualify(lid, "r1")
        oid = c.convert(lid, 1000, "r1")
        return c, oid

    def test_discount_ok(self):
        c, oid = self.build()
        c.discount(oid, 10, "r1")
        self.assertEqual(c.opps[oid]["amount"], 900)

    def test_bad_pct(self):
        c, oid = self.build()
        with self.assertRaises(ValueError):
            c.discount(oid, True, "r1")
        with self.assertRaises(ValueError):
            c.discount(oid, 0, "r1")
        with self.assertRaises(ValueError):
            c.discount(oid, 31, "r1")

    def test_rep_over_10(self):
        c, oid = self.build()
        with self.assertRaises(PermissionError):
            c.discount(oid, 15, "r1")

    def test_cumulative_cap(self):
        c, oid = self.build()
        c.discount(oid, 10, "r1")   # 900
        c.discount(oid, 10, "m1")   # 810
        c.discount(oid, 10, "r1")   # 729 -> below 700 allowed? 72900 >= 70000 yes
        self.assertEqual(c.opps[oid]["amount"], 729)
        with self.assertRaises(ValueError):
            c.discount(oid, 10, "m1")  # 656 -> below

    def test_final_stage(self):
        c, oid = self.build()
        c.advance(oid, "lost", "r1")
        with self.assertRaises(ValueError):
            c.discount(oid, 5, "r1")


class TransferTest(unittest.TestCase):
    def build(self):
        c = make()
        lid = c.add_lead("a@b.com", "n", "referral", "r1")
        c.qualify(lid, "r1")
        oid = c.convert(lid, 1000, "r1")
        return c, oid

    def test_transfer_ok(self):
        c, oid = self.build()
        c.transfer(oid, "r2", "m1")
        self.assertEqual(c.opps[oid]["owner"], "r2")

    def test_only_manager(self):
        c, oid = self.build()
        with self.assertRaises(PermissionError):
            c.transfer(oid, "r2", "r1")

    def test_bad_new_owner(self):
        c, oid = self.build()
        with self.assertRaises(ValueError):
            c.transfer(oid, "m1", "m1")   # not a rep
        with self.assertRaises(ValueError):
            c.transfer(oid, "zz", "m1")   # unknown

    def test_same_owner_or_full(self):
        c2 = make()  # r1 cap 2, r2 cap 1
        lid = c2.add_lead("d@b.com", "n", "referral", "r1")  # -> r1
        c2.add_lead("b@b.com", "n", "web", "r1")             # -> r2 (r2 full)
        c2.qualify(lid, "r1")
        oid2 = c2.convert(lid, 100, "r1")
        with self.assertRaises(ValueError):
            c2.transfer(oid2, "r1", "m1")   # same owner
        with self.assertRaises(ValueError):
            c2.transfer(oid2, "r2", "m1")   # r2 at capacity

    def test_transfer_frees_prev_slot(self):
        reps = [
            {"id": "r1", "role": "rep", "capacity": 3},
            {"id": "r2", "role": "rep", "capacity": 2},
            {"id": "m1", "role": "manager", "capacity": 0},
        ]
        c = CRM(reps)
        l1 = c.add_lead("a@b.com", "n", "referral", "r1")  # -> r1
        c.add_lead("b@b.com", "n", "referral", "r1")       # -> r2
        c.add_lead("c@b.com", "n", "web", "r1")            # -> r1
        c.add_lead("d@b.com", "n", "web", "r1")            # -> r1 (r1 load 3)
        c.add_lead("e@b.com", "n", "web", "r1")            # -> r2 (r2 load 2)
        l6 = c.add_lead("f@b.com", "n", "web", "r1")       # queued (all full)
        self.assertIsNone(c.leads[l6]["owner"])
        with self.assertRaises(ValueError):
            c.transfer("O1", "r2", "m1")  # not an opp yet
        c.qualify(l1, "r1")
        oid = c.convert(l1, 100, "r1")
        # all reps at capacity -> transfer must fail on capacity check
        with self.assertRaises(ValueError):
            c.transfer(oid, "r2", "m1")
        c.advance(oid, "proposal", "r1")
        c.advance(oid, "negotiation", "r1")
        c.advance(oid, "won", "r1")     # frees r1 -> L6 assigned to r1
        self.assertEqual(c.leads[l6]["owner"], "r1")
        self.assertIn(("assign", l6, "system"), c.log)
        # transfer success path with clean state
        c2 = CRM([
            {"id": "x1", "role": "rep", "capacity": 2},
            {"id": "x2", "role": "rep", "capacity": 2},
            {"id": "x3", "role": "manager", "capacity": 0},
        ])
        lid = c2.add_lead("p@b.com", "n", "referral", "x1")  # -> x1
        lid2 = c2.add_lead("q@b.com", "n", "referral", "x1")  # -> x1 (load 2)
        c2.qualify(lid, "x1")
        o = c2.convert(lid, 100, "x1")  # x1: lead2 + opp = 2
        c2.transfer(o, "x2", "x3")      # x2 load 0 < 2; x1 drops to 1
        self.assertEqual(c2.opps[o]["owner"], "x2")
        self.assertEqual(c2.log[-1], ("transfer", o, "x3"))


class ForecastTest(unittest.TestCase):
    def test_forecast(self):
        c = make()  # r1 cap 2, r2 cap 1
        l1 = c.add_lead("a@b.com", "n", "referral", "r1")  # -> r1
        c.qualify(l1, "r1")
        o1 = c.convert(l1, 1000, "r1")                     # r1 load 1
        l2 = c.add_lead("b@b.com", "n", "referral", "r1")  # -> r2
        c.qualify(l2, "r2")
        o2 = c.convert(l2, 1000, "r2")                     # r2 load 1 (full)
        l3 = c.add_lead("c@b.com", "n", "referral", "r1")  # -> r1 (load 2)
        c.qualify(l3, "r1")
        o3 = c.convert(l3, 1000, "r1")
        c.advance(o3, "proposal", "r1")
        c.advance(o3, "negotiation", "r1")
        c.advance(o2, "proposal", "r2")
        c.advance(o3, "won", "r1")
        c.advance(o1, "lost", "r1")
        # open: o2 (proposal) weighted 1000*30//100 = 300
        self.assertEqual(c.forecast(), {"open": 1, "weighted": 300, "won": 1000})


if __name__ == "__main__":
    unittest.main()
