import unittest

from crm import CRM, DuplicateLeadError


def make_crm():
    """manager m1; reps r1, r2 capacity 1 each."""
    return CRM([
        {"id": "m1", "role": "manager", "capacity": 0},
        {"id": "r1", "role": "rep", "capacity": 1},
        {"id": "r2", "role": "rep", "capacity": 1},
    ])


def full_opp(crm, email, amount=1000, actor="m1"):
    """add -> qualify -> convert; returns opp id (lead score 45 via referral)."""
    lid = crm.add_lead(email, "N", "referral", actor)
    crm.qualify(lid, actor)
    return crm.convert(lid, amount, actor)


class TestActor(unittest.TestCase):
    def test_unknown_actor_checked_first(self):
        c = make_crm()
        calls = [
            ("add_lead", ("a@b.com", "N", "web", "ghost")),
            ("qualify", ("L1", "ghost")),
            ("convert", ("L1", 5, "ghost")),
            ("advance", ("O1", "proposal", "ghost")),
            ("discount", ("O1", 5, "ghost")),
            ("transfer", ("O1", "r1", "ghost")),
        ]
        for meth, args in calls:
            with self.assertRaises(PermissionError, msg=meth):
                getattr(c, meth)(*args)
        self.assertEqual((c.leads, c.opps, c.log), ({}, {}, []))


class TestAddLead(unittest.TestCase):
    def test_happy_path_fields_and_log(self):
        c = make_crm()
        lid = c.add_lead("  Alice@Acme.COM ", " Alice ", "referral", "m1")
        self.assertEqual(lid, "L1")
        lead = c.leads[lid]
        self.assertEqual(lead["email"], "alice@acme.com")
        self.assertEqual(lead["name"], "Alice")
        self.assertEqual(lead["source"], "referral")
        self.assertEqual(lead["score"], 45)  # 30 + 15 non-free domain
        self.assertEqual(lead["status"], "new")
        self.assertEqual(lead["owner"], "r1")  # load tie -> smallest id
        self.assertEqual(c.log, [("add_lead", "L1", "m1")])

    def test_scores(self):
        c = CRM([{"id": "m1", "role": "manager", "capacity": 0},
                 {"id": "r9", "role": "rep", "capacity": 99}])
        c.add_lead("x@gmail.com", "n", "web", "m1")
        self.assertEqual(c.leads["L1"]["score"], 10)
        c.add_lead("x@yahoo.com", "n2", "event", "m1")
        self.assertEqual(c.leads["L2"]["score"], 20)
        c.add_lead("x@outlook.com", "n3", "referral", "m1")
        self.assertEqual(c.leads["L3"]["score"], 30)
        c.add_lead("x@acme.com", "n4", "web", "m1")
        self.assertEqual(c.leads["L4"]["score"], 25)

    def test_bad_emails(self):
        c = make_crm()
        for bad in [None, 123, "", "noatsign", "a@@b.com", "a@b@c.com",
                    "@b.com", "a@", "a@b", "a@.b.com", "a@b.com.", "a@b.."]:
            with self.assertRaises(ValueError, msg=repr(bad)):
                c.add_lead(bad, "n", "web", "m1")
        self.assertEqual(c.leads, {})
        self.assertEqual(c.log, [])

    def test_valid_edge_emails(self):
        c = CRM([{"id": "m1", "role": "manager", "capacity": 0},
                 {"id": "r9", "role": "rep", "capacity": 99}])
        c.add_lead("a@b.co", "v1", "web", "m1")
        c.add_lead("a.b+c@sub.domain.org", "v2", "web", "m1")
        self.assertEqual(len(c.leads), 2)

    def test_name_and_source_validation(self):
        c = make_crm()
        with self.assertRaises(ValueError):
            c.add_lead("a@b.com", "   ", "web", "m1")
        with self.assertRaises(ValueError):
            c.add_lead("a@b.com", 5, "web", "m1")
        with self.assertRaises(ValueError):
            c.add_lead("a@b.com", "n", "phone", "m1")
        # validations precede duplicate detection
        with self.assertRaises(ValueError):
            c.add_lead("a@b.com", "", "bogus", "m1")
        self.assertEqual((c.leads, c.log), ({}, []))

    def test_duplicate(self):
        c = make_crm()
        lid = c.add_lead("a@b.com", "first", "web", "m1")
        with self.assertRaises(DuplicateLeadError) as cm:
            c.add_lead("  A@B.COM ", "dup", "referral", "m1")
        self.assertEqual(cm.exception.existing_id, lid)
        self.assertEqual(len(c.leads), 1)
        self.assertEqual(c.log, [("add_lead", lid, "m1")])


class TestRouting(unittest.TestCase):
    def test_tie_smallest_id_then_queue(self):
        c = CRM([
            {"id": "m1", "role": "manager", "capacity": 0},
            {"id": "rb", "role": "rep", "capacity": 1},
            {"id": "ra", "role": "rep", "capacity": 1},
        ])
        c.add_lead("1@x.com", "a", "web", "m1")
        self.assertEqual(c.leads["L1"]["owner"], "ra")
        c.add_lead("2@x.com", "b", "web", "m1")
        self.assertEqual(c.leads["L2"]["owner"], "rb")
        c.add_lead("3@x.com", "c", "web", "m1")
        self.assertIsNone(c.leads["L3"]["owner"])  # all full -> FIFO queue
        self.assertEqual(c.log, [("add_lead", lid, "m1") for lid in ("L1", "L2", "L3")])

    def test_lowest_load_beats_id(self):
        c = CRM([
            {"id": "m1", "role": "manager", "capacity": 0},
            {"id": "ra", "role": "rep", "capacity": 2},
            {"id": "rb", "role": "rep", "capacity": 2},
        ])
        c.add_lead("1@x.com", "a", "web", "m1")   # ra (tie, smaller id)
        c.add_lead("2@x.com", "b", "web", "m1")   # rb (load 0 < 1)
        c.add_lead("3@x.com", "c", "web", "m1")   # tie again -> ra
        self.assertEqual([c.leads[k]["owner"] for k in ("L1", "L2", "L3")],
                         ["ra", "rb", "ra"])

    def test_capacity_zero_never_owns(self):
        c = CRM([{"id": "m1", "role": "manager", "capacity": 0},
                 {"id": "r0", "role": "rep", "capacity": 0}])
        lid = c.add_lead("a@x.com", "a", "web", "m1")
        self.assertIsNone(c.leads[lid]["owner"])


class TestQualify(unittest.TestCase):
    def test_rules(self):
        c = CRM([{"id": "m1", "role": "manager", "capacity": 0},
                 {"id": "r1", "role": "rep", "capacity": 1},
                 {"id": "r2", "role": "rep", "capacity": 1}])
        low = c.add_lead("a@b.com", "A", "web", "m1")          # score 25, owner r1
        high = c.add_lead("h@acme.com", "H", "referral", "m1")  # score 45, owner r2
        with self.assertRaises(ValueError):
            c.qualify("L99", "m1")
        with self.assertRaises(PermissionError):
            c.qualify(high, "r1")     # neither owner nor manager
        with self.assertRaises(ValueError):
            c.qualify(low, "m1")      # score below 30
        self.assertEqual(c.leads[low]["status"], "new")
        c.qualify(high, "r2")
        self.assertEqual(c.leads[high]["status"], "qualified")
        with self.assertRaises(ValueError):
            c.qualify(high, "m1")     # no longer new
        self.assertEqual(c.log[2:], [("qualify", high, "r2")])
        self.assertEqual(c.leads[low]["status"], "new")


class TestConvert(unittest.TestCase):
    def setUp(self):
        self.c = make_crm()
        self.lid = self.c.add_lead("a@acme.com", "A", "referral", "m1")
        self.c.qualify(self.lid, "m1")

    def test_validation_order(self):
        c = self.c
        with self.assertRaises(ValueError):
            c.convert("L99", 5, "m1")
        for bad_amount in (True, False, 0, -3, "5", 1.5):
            with self.assertRaises(ValueError, msg=repr(bad_amount)):
                c.convert(self.lid, bad_amount, "m1")
        with self.assertRaises(PermissionError):
            c.convert(self.lid, 5, "r2")   # valid amount, wrong actor
        self.assertEqual(len(c.log), 2)    # add + qualify only
        self.assertEqual(c.leads[self.lid]["status"], "qualified")

    def test_success(self):
        c = self.c
        oid = c.convert(self.lid, 1000, "r1")
        self.assertEqual(oid, "O1")
        self.assertEqual(c.opps[oid], {
            "id": "O1", "lead_id": self.lid, "owner": "r1",
            "amount": 1000, "original_amount": 1000, "stage": "prospect",
        })
        self.assertEqual(c.leads[self.lid]["status"], "converted")
        self.assertEqual(c.log[-1], ("convert", "O1", "r1"))
        with self.assertRaises(ValueError):
            c.convert(self.lid, 5, "r1")   # not qualified anymore

    def test_manager_can_convert_any_and_seq_counts_only_success(self):
        c = self.c
        lid2 = c.add_lead("b@acme.com", "B", "referral", "m1")
        c.qualify(lid2, "m1")
        with self.assertRaises(ValueError):
            c.convert(lid2, 0, "m1")       # failed conversion consumes no id
        oid = c.convert(lid2, 10, "m1")
        self.assertEqual(oid, "O1")

    def test_unowned_qualified_lead_cannot_convert(self):
        c = CRM([{"id": "m1", "role": "manager", "capacity": 0},
                 {"id": "r1", "role": "rep", "capacity": 0}])
        lid = c.add_lead("a@acme.com", "A", "referral", "m1")  # queued
        self.assertIsNone(c.leads[lid]["owner"])
        c.qualify(lid, "m1")
        with self.assertRaises(ValueError):
            c.convert(lid, 100, "m1")      # needs an owner


class TestAdvance(unittest.TestCase):
    def setUp(self):
        self.c = make_crm()
        self.oid = full_opp(self.c, "a@acme.com", 1000)  # owner r1

    def test_stage_flow_errors(self):
        c, oid = self.c, self.oid
        with self.assertRaises(ValueError):
            c.advance("O9", "proposal", "m1")
        with self.assertRaises(ValueError):
            c.advance(oid, "bogus", "m1")
        with self.assertRaises(PermissionError):
            c.advance(oid, "proposal", "r2")     # not owner/manager
        with self.assertRaises(ValueError):
            c.advance(oid, "negotiation", "m1")  # skipping proposal
        c.advance(oid, "proposal", "r1")
        self.assertEqual(c.opps[oid]["stage"], "proposal")
        with self.assertRaises(ValueError):
            c.advance(oid, "prospect", "m1")     # backwards not allowed
        c.advance(oid, "lost", "r1")             # lost reachable from any open stage
        self.assertEqual(c.opps[oid]["stage"], "lost")
        with self.assertRaises(ValueError):
            c.advance(oid, "won", "m1")          # final
        self.assertEqual(c.opps[oid]["stage"], "lost")
        self.assertEqual(c.log[-2:], [("advance", oid, "r1"), ("advance", oid, "r1")])

    def test_won_only_from_negotiation(self):
        c, oid = self.c, self.oid
        with self.assertRaises(ValueError):
            c.advance(oid, "won", "m1")
        c.advance(oid, "proposal", "m1")
        c.advance(oid, "negotiation", "m1")
        c.advance(oid, "won", "m1")
        self.assertEqual(c.opps[oid]["stage"], "won")

    def test_negotiation_gate_above_50k(self):
        c = self.c
        oid2 = full_opp(c, "b@acme.com", 60000)  # queued->owner? r1,r2 full? 
        # r1 holds O1; r2 is free so oid2 opp owner is r2
        self.assertEqual(c.opps[oid2]["owner"], "r2")
        c.advance(oid2, "proposal", "r2")
        with self.assertRaises(PermissionError):
            c.advance(oid2, "negotiation", "r2")  # owner rep, > 50000
        self.assertEqual(c.opps[oid2]["stage"], "proposal")
        c.advance(oid2, "negotiation", "m1")      # manager ok
        self.assertEqual(c.opps[oid2]["stage"], "negotiation")
        # exactly 50000: rep owner may negotiate
        c2 = CRM([{"id": "m1", "role": "manager", "capacity": 0},
                  {"id": "r1", "role": "rep", "capacity": 5}])
        oid3 = full_opp(c2, "z@acme.com", 50000)
        c2.advance(oid3, "proposal", "r1")
        c2.advance(oid3, "negotiation", "r1")
        self.assertEqual(c2.opps[oid3]["stage"], "negotiation")

    def test_final_frees_slot_and_drains_queue_fifo(self):
        c = self.c
        oid2 = full_opp(c, "b@acme.com", 100)     # r2's opp
        lid3 = c.add_lead("c@acme.com", "C", "referral", "m1")  # queued (r1,r2 full)
        lid4 = c.add_lead("d@acme.com", "D", "referral", "m1")  # queued second
        self.assertIsNone(c.leads[lid3]["owner"])
        self.assertIsNone(c.leads[lid4]["owner"])
        c.advance(oid2, "proposal", "r2")
        c.advance(oid2, "negotiation", "r2")      # amount 100 -> no manager needed
        c.advance(oid2, "won", "r2")
        self.assertEqual(c.leads[lid3]["owner"], "r2")  # oldest first
        self.assertEqual(c.leads[lid3]["status"], "new")
        self.assertIsNone(c.leads[lid4]["owner"])      # r2 back at capacity
        self.assertEqual(c.log[-2:], [("advance", oid2, "r2"),
                                      ("assign", lid3, "system")])

    def test_failed_advance_no_side_effects(self):
        c, oid = self.c, self.oid
        lid = c.add_lead("q@acme.com", "Q", "referral", "m1")  # r2 owns it
        before = (dict(c.opps[oid]), dict(c.leads[lid]), list(c.log))
        with self.assertRaises(PermissionError):
            c.advance(oid, "proposal", "r2")
        self.assertEqual((c.opps[oid], c.leads[lid], c.log), before)


class TestDiscount(unittest.TestCase):
    def setUp(self):
        self.c = make_crm()
        self.oid = full_opp(self.c, "a@acme.com", 1000)  # owner r1

    def test_pct_validation(self):
        c = self.c
        for bad in [0, 31, 100, True, False, "5", 10.0]:
            with self.assertRaises(ValueError, msg=repr(bad)):
                c.discount(self.oid, bad, "m1")
        self.assertEqual(c.opps[self.oid]["amount"], 1000)
        self.assertEqual(len(c.log), 3)  # nothing logged by failures

    def test_permissions_and_stage(self):
        c = self.c
        with self.assertRaises(PermissionError):
            c.discount(self.oid, 5, "r2")
        with self.assertRaises(PermissionError):
            c.discount(self.oid, 11, "r1")   # rep limited to 10
        c.discount(self.oid, 10, "r1")
        self.assertEqual(c.opps[self.oid]["amount"], 900)
        c.discount(self.oid, 11, "m1")
        self.assertEqual(c.opps[self.oid]["amount"], 801)  # 900 * 89 // 100
        self.assertEqual(c.log[-2:], [("discount", self.oid, "r1"),
                                      ("discount", self.oid, "m1")])
        c.advance(self.oid, "proposal", "r1")
        c.advance(self.oid, "negotiation", "m1")
        c.advance(self.oid, "lost", "r1")
        with self.assertRaises(ValueError):
            c.discount(self.oid, 5, "m1")    # final stage
        self.assertEqual(c.opps[self.oid]["amount"], 801)

    def test_cumulative_floor_30_percent(self):
        c = self.c
        # exactly 30% off original 1000 -> 700; 700*100 >= 1000*70 passes the floor
        c.discount(self.oid, 30, "m1")
        self.assertEqual(c.opps[self.oid]["amount"], 700)
        # any further discount drops below the 70% floor of the ORIGINAL amount
        with self.assertRaises(ValueError):
            c.discount(self.oid, 1, "m1")    # 693*100 < 70000
        self.assertEqual(c.opps[self.oid]["amount"], 700)
        self.assertEqual(c.log[-1], ("discount", self.oid, "m1"))
        self.assertEqual(len(c.log), 4)      # failed call logged nothing

    def test_floor_after_partial_discount(self):
        c = self.c
        c.discount(self.oid, 10, "m1")       # 900
        with self.assertRaises(ValueError):
            c.discount(self.oid, 25, "m1")   # 900*75//100=675; 67500 < 70000
        self.assertEqual(c.opps[self.oid]["amount"], 900)
        c.discount(self.oid, 22, "m1")       # 900*78//100=702; 70200 >= 70000 ok
        self.assertEqual(c.opps[self.oid]["amount"], 702)


class TestTransfer(unittest.TestCase):
    def build(self):
        c = make_crm()
        oid = full_opp(c, "a@acme.com", 100)  # opp on r1
        return c, oid

    def test_error_order(self):
        c, oid = self.build()
        l2 = c.add_lead("b@acme.com", "B", "referral", "m1")  # r2 owns lead
        with self.assertRaises(PermissionError):
            c.transfer(oid, "r2", "r1")        # not manager
        with self.assertRaises(ValueError):
            c.transfer("O9", "r2", "m1")       # unknown opp
        with self.assertRaises(ValueError):
            c.transfer(oid, "m1", "m1")        # target not a rep
        with self.assertRaises(ValueError):
            c.transfer(oid, "ghost", "m1")     # target unknown
        with self.assertRaises(ValueError):
            c.transfer(oid, "r1", "m1")        # same owner
        with self.assertRaises(ValueError):
            c.transfer(oid, "r2", "m1")        # target at capacity
        self.assertEqual(c.opps[oid]["owner"], "r1")
        self.assertEqual(c.log[-1], ("add_lead", l2, "m1"))

    def test_final_stage_blocks(self):
        c, oid = self.build()
        c.advance(oid, "proposal", "m1")
        c.advance(oid, "negotiation", "m1")
        c.advance(oid, "won", "m1")
        r3 = CRM([{"id": "m1", "role": "manager", "capacity": 0},
                  {"id": "r1", "role": "rep", "capacity": 1},
                  {"id": "rz", "role": "rep", "capacity": 1}])
        oid3 = full_opp(r3, "x@acme.com", 100)  # r1 (tie -> r1); rz free
        r3.advance(oid3, "proposal", "m1")
        r3.advance(oid3, "negotiation", "m1")
        r3.advance(oid3, "won", "m1")
        with self.assertRaises(ValueError):
            r3.transfer(oid3, "rz", "m1")       # final stage wins over room check

    def test_success(self):
        c, oid = self.build()
        rz = CRM([{"id": "m1", "role": "manager", "capacity": 0},
                  {"id": "ra", "role": "rep", "capacity": 1},
                  {"id": "rz", "role": "rep", "capacity": 1}])
        oidz = full_opp(rz, "z@acme.com", 100)   # owner ra
        rz.transfer(oidz, "rz", "m1")
        self.assertEqual(rz.opps[oidz]["owner"], "rz")
        self.assertEqual(rz.log[-1], ("transfer", oidz, "m1"))
        # queue invariant: a successful transfer requires a rep below capacity,
        # which implies the waiting queue was empty; so no assign entries follow.
        self.assertNotIn("assign", [e[0] for e in rz.log])


class TestForecast(unittest.TestCase):
    def test_full_computation(self):
        c = CRM([{"id": "m1", "role": "manager", "capacity": 0},
                 {"id": "r1", "role": "rep", "capacity": 99}])
        o1 = full_opp(c, "a@acme.com", 1000)   # prospect
        o2 = full_opp(c, "b@acme.com", 2000)
        o3 = full_opp(c, "c@acme.com", 4000)
        c.advance(o2, "proposal", "m1")
        c.advance(o3, "proposal", "m1")
        c.advance(o3, "negotiation", "m1")
        self.assertEqual(c.forecast(),
                         {"open": 3, "weighted": 100 + 600 + 2400, "won": 0})
        c.advance(o1, "proposal", "m1")
        c.advance(o1, "negotiation", "m1")
        c.advance(o1, "won", "m1")
        c.advance(o3, "lost", "m1")
        self.assertEqual(c.forecast(), {"open": 1, "weighted": 600, "won": 1000})
        # discount affects forecast amount
        c.discount(o2, 10, "m1")   # 2000 -> 1800; weighted 540
        self.assertEqual(c.forecast(), {"open": 1, "weighted": 540, "won": 1000})
        n = len(c.log)
        c.forecast()
        self.assertEqual(len(c.log), n)  # forecast never logs

    def test_empty(self):
        c = make_crm()
        self.assertEqual(c.forecast(), {"open": 0, "weighted": 0, "won": 0})


if __name__ == "__main__":
    unittest.main()
