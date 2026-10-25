import unittest

from crm import CRM, DuplicateLeadError


def std_reps():
    return [
        {"id": "r1", "role": "rep", "capacity": 2},
        {"id": "r2", "role": "rep", "capacity": 2},
        {"id": "m1", "role": "manager", "capacity": 0},
    ]


class AddLeadTest(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(std_reps())

    def test_unknown_actor_raises_permission_first(self):
        with self.assertRaises(PermissionError):
            self.crm.add_lead("bad-email", "N", "web", "ghost")

    def test_happy_path(self):
        lid = self.crm.add_lead("  Alice@Example.COM ", " Alice ", "web", "m1")
        self.assertEqual(lid, "L1")
        lead = self.crm.leads[lid]
        self.assertEqual(lead["email"], "alice@example.com")
        self.assertEqual(lead["name"], "Alice")
        self.assertEqual(lead["score"], 25)  # web 10 + 15 non-free domain
        self.assertEqual(lead["status"], "new")
        self.assertIn(lead["owner"], ("r1", "r2"))
        self.assertEqual(self.crm.log[-1], ("add_lead", "L1", "m1"))

    def test_scores(self):
        self.crm.add_lead("a@gmail.com", "A", "web", "r1")
        self.assertEqual(self.crm.leads["L1"]["score"], 10)
        self.crm.add_lead("b@yahoo.com", "B", "referral", "r1")
        self.assertEqual(self.crm.leads["L2"]["score"], 30)
        self.crm.add_lead("c@outlook.com", "C", "event", "r1")
        self.assertEqual(self.crm.leads["L3"]["score"], 20)
        self.crm.add_lead("d@corp.io", "D", "event", "r1")
        self.assertEqual(self.crm.leads["L4"]["score"], 35)
        self.crm.add_lead("e@corp.io", "E", "web", "r1")
        self.assertEqual(self.crm.leads["L5"]["score"], 25)

    def test_email_validation(self):
        for bad in ["noatsign", "a@b", "a@.com", "a@com.", "@b.com", "a@b.com@c", 5, "a b@c"]:
            with self.assertRaises(ValueError, msg=repr(bad)):
                self.crm.add_lead(bad, "N", "web", "r1")
        # multi-dot domains are fine per spec wording
        self.crm.add_lead("a@sub.example.com", "N", "web", "r1")

    def test_name_and_source_validation(self):
        with self.assertRaises(ValueError):
            self.crm.add_lead("a@b.co", "   ", "web", "r1")
        with self.assertRaises(ValueError):
            self.crm.add_lead("a@b.co", "A", "phone", "r1")

    def test_duplicate(self):
        first = self.crm.add_lead("A@B.co ", "A", "web", "r1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            self.crm.add_lead(" a@b.co", "A2", "web", "r1")
        self.assertEqual(ctx.exception.existing_id, first)
        self.assertEqual(len(self.crm.leads), 1)
        self.assertEqual(len(self.crm.log), 1)

    def test_round_robin_lowest_load_then_queue(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1},
                   {"id": "r2", "role": "rep", "capacity": 1},
                   {"id": "m1", "role": "manager", "capacity": 0}])
        l1 = crm.add_lead("a@a.com", "A", "web", "m1")
        l2 = crm.add_lead("b@b.com", "B", "web", "m1")
        l3 = crm.add_lead("c@c.com", "C", "web", "m1")
        self.assertEqual(crm.leads[l1]["owner"], "r1")
        self.assertEqual(crm.leads[l2]["owner"], "r2")
        self.assertIsNone(crm.leads[l3]["owner"])
        l4 = crm.add_lead("x@x.com", "X", "web", "m1")
        self.assertIsNone(crm.leads[l4]["owner"])  # FIFO: stays queued behind l3


class QualifyConvertTest(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(std_reps())
        self.lid = self.crm.add_lead("a@corp.com", "A", "referral", "m1")
        self.owner = self.crm.leads[self.lid]["owner"]

    def test_qualify_by_owner(self):
        self.crm.qualify(self.lid, self.owner)
        self.assertEqual(self.crm.leads[self.lid]["status"], "qualified")
        self.assertEqual(self.crm.log[-1], ("qualify", self.lid, self.owner))

    def test_qualify_wrong_actor(self):
        other = "r2" if self.owner == "r1" else "r1"
        with self.assertRaises(PermissionError):
            self.crm.qualify(self.lid, other)

    def test_qualify_low_score(self):
        lid = self.crm.add_lead("w@corp.com", "W", "web", "m1")
        with self.assertRaises(ValueError):
            self.crm.qualify(lid, self.crm.leads[lid]["owner"])

    def test_qualify_twice_fails(self):
        self.crm.qualify(self.lid, "m1")
        with self.assertRaises(ValueError):
            self.crm.qualify(self.lid, "m1")

    def test_convert(self):
        self.crm.qualify(self.lid, self.owner)
        oid = self.crm.convert(self.lid, 1000, self.owner)
        self.assertEqual(oid, "O1")
        opp = self.crm.opps[oid]
        self.assertEqual(opp, {"id": "O1", "lead_id": self.lid, "owner": self.owner,
                               "amount": 1000, "original_amount": 1000, "stage": "prospect"})
        self.assertEqual(self.crm.leads[self.lid]["status"], "converted")
        self.assertEqual(self.crm.log[-1], ("convert", oid, self.owner))

    def test_convert_amount_validation(self):
        self.crm.qualify(self.lid, "m1")
        for bad in [0, -5, True, 1.5, "10"]:
            with self.assertRaises(ValueError, msg=repr(bad)):
                self.crm.convert(self.lid, bad, "m1")

    def test_convert_needs_qualified(self):
        with self.assertRaises(ValueError):
            self.crm.convert(self.lid, 100, "m1")

    def test_convert_check_order_amount_before_permission(self):
        # unknown lead -> ValueError; bad amount -> ValueError even from non-owner rep
        other = "r2" if self.owner == "r1" else "r1"
        self.crm.qualify(self.lid, "m1")
        with self.assertRaises(ValueError):
            self.crm.convert(self.lid, -1, other)


class AdvanceDiscountTest(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(std_reps())
        lid = self.crm.add_lead("a@corp.com", "A", "referral", "m1")
        self.owner = self.crm.leads[lid]["owner"]
        self.crm.qualify(lid, "m1")
        self.oid = self.crm.convert(lid, 40000, "m1")

    def test_happy_advance_chain(self):
        self.crm.advance(self.oid, "proposal", self.owner)
        self.crm.advance(self.oid, "negotiation", self.owner)  # 40000 <= 50000 ok for rep
        self.crm.advance(self.oid, "won", "m1")
        self.assertEqual(self.crm.opps[self.oid]["stage"], "won")
        self.assertEqual([e[0] for e in self.crm.log][-4:],
                         ["convert", "advance", "advance", "advance"])

    def test_invalid_transitions(self):
        with self.assertRaises(ValueError):
            self.crm.advance(self.oid, "negotiation", self.owner)  # skips proposal
        with self.assertRaises(ValueError):
            self.crm.advance(self.oid, "prospect", self.owner)  # not forward
        with self.assertRaises(ValueError):
            self.crm.advance(self.oid, "bogus", self.owner)
        self.assertEqual(self.crm.opps[self.oid]["stage"], "prospect")

    def test_final_stage_locked(self):
        self.crm.advance(self.oid, "lost", self.owner)
        self.assertEqual(len(self.crm.log), 4)  # add, qualify, convert, advance
        with self.assertRaises(ValueError):
            self.crm.advance(self.oid, "proposal", "m1")

    def test_big_negotiation_needs_manager(self):
        self.crm.advance(self.oid, "proposal", self.owner)
        big = self.crm.add_lead("b@corp.com", "B", "referral", "m1")
        self.crm.qualify(big, "m1")
        boid = self.crm.convert(big, 60000, "m1")
        self.crm.advance(boid, "proposal", self.crm.leads[big]["owner"])
        bowner = self.crm.opps[boid]["owner"]
        with self.assertRaises(PermissionError):
            self.crm.advance(boid, "negotiation", bowner)
        self.crm.advance(boid, "negotiation", "m1")
        self.assertEqual(self.crm.opps[boid]["stage"], "negotiation")

    def test_discount_limits(self):
        with self.assertRaises(ValueError):
            self.crm.discount(self.oid, 0, "m1")
        with self.assertRaises(ValueError):
            self.crm.discount(self.oid, 31, "m1")
        with self.assertRaises(ValueError):
            self.crm.discount(self.oid, True, "m1")
        other = "r2" if self.owner == "r1" else "r1"
        with self.assertRaises(PermissionError):
            self.crm.discount(self.oid, 5, other)
        with self.assertRaises(PermissionError):
            self.crm.discount(self.oid, 15, self.owner)  # rep max 10
        self.crm.discount(self.oid, 10, self.owner)
        self.assertEqual(self.crm.opps[self.oid]["amount"], 36000)
        self.crm.discount(self.oid, 20, "m1")  # 36000*80//100=28800; 28800*100 >= 40000*70? 2.88M >= 2.8M ok
        self.assertEqual(self.crm.opps[self.oid]["amount"], 28800)
        with self.assertRaises(ValueError):
            self.crm.discount(self.oid, 5, "m1")  # would go under 70% of original

    def test_won_frees_slot_and_assigns_from_queue(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1},
                   {"id": "m1", "role": "manager", "capacity": 0}])
        l1 = crm.add_lead("a@a.co", "A", "referral", "m1")
        self.assertEqual(crm.leads[l1]["owner"], "r1")
        l2 = crm.add_lead("b@b.co", "B", "referral", "m1")
        self.assertIsNone(crm.leads[l2]["owner"])
        crm.qualify(l1, "m1")
        oid = crm.convert(l1, 100, "m1")
        # r1 busy with open opp; l2 still waiting
        crm.advance(oid, "proposal", "m1")
        crm.advance(oid, "negotiation", "m1")
        crm.advance(oid, "won", "m1")
        self.assertEqual(crm.leads[l2]["owner"], "r1")
        self.assertEqual(crm.log[-1], ("assign", l2, "system"))


class TransferForecastTest(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(std_reps())
        lid = self.crm.add_lead("a@corp.com", "A", "referral", "m1")
        self.owner = self.crm.leads[lid]["owner"]
        self.other = "r2" if self.owner == "r1" else "r1"
        self.crm.qualify(lid, "m1")
        self.oid = self.crm.convert(lid, 1000, "m1")

    def test_transfer_requires_manager(self):
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.oid, self.other, self.owner)

    def test_transfer_validations(self):
        with self.assertRaises(ValueError):
            self.crm.transfer("O99", self.other, "m1")
        with self.assertRaises(ValueError):
            self.crm.transfer(self.oid, "m1", "m1")   # manager cannot own
        with self.assertRaises(ValueError):
            self.crm.transfer(self.oid, "ghost", "m1")
        with self.assertRaises(ValueError):
            self.crm.transfer(self.oid, self.owner, "m1")  # same owner

    def test_transfer_works(self):
        self.crm.transfer(self.oid, self.other, "m1")
        self.assertEqual(self.crm.opps[self.oid]["owner"], self.other)
        self.assertEqual(self.crm.log[-1], ("transfer", self.oid, "m1"))

    def test_transfer_capacity(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1},
                   {"id": "r2", "role": "rep", "capacity": 0},
                   {"id": "m1", "role": "manager", "capacity": 0}])
        lid = crm.add_lead("a@a.co", "A", "referral", "m1")
        crm.qualify(lid, "m1")
        oid = crm.convert(lid, 100, "m1")
        with self.assertRaises(ValueError):
            crm.transfer(oid, "r2", "m1")  # capacity 0

    def test_transfer_frees_previous_owner_slot(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1},
                   {"id": "r2", "role": "rep", "capacity": 1},
                   {"id": "m1", "role": "manager", "capacity": 0}])
        l1 = crm.add_lead("a@a.co", "A", "referral", "m1")   # -> r1
        self.assertEqual(crm.leads[l1]["owner"], "r1")
        crm.qualify(l1, "m1")
        oid = crm.convert(l1, 100, "m1")                     # r1 busy with open opp
        crm.transfer(oid, "r2", "m1")                        # r1's slot frees
        self.assertEqual(crm.opps[oid]["owner"], "r2")
        l2 = crm.add_lead("b@b.co", "B", "referral", "m1")   # lowest load now r1
        self.assertEqual(crm.leads[l2]["owner"], "r1")

    def test_forecast(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 5},
                   {"id": "m1", "role": "manager", "capacity": 0}])
        self.assertEqual(crm.forecast(), {"open": 0, "weighted": 0, "won": 0})
        ids = []
        for i, (src, amt) in enumerate([("referral", 1000), ("referral", 2000), ("referral", 3000)]):
            lid = crm.add_lead("x%d@corp.com" % i, "X", src, "m1")
            crm.qualify(lid, "m1")
            ids.append(crm.convert(lid, amt, "m1"))
        crm.advance(ids[1], "proposal", "m1")
        crm.advance(ids[2], "proposal", "m1")
        crm.advance(ids[2], "negotiation", "m1")
        crm.advance(ids[0], "proposal", "m1")
        crm.advance(ids[0], "negotiation", "m1")
        crm.advance(ids[0], "won", "m1")
        # open: O2 proposal 2000*30//100=600 ; O3 negotiation 3000*60//100=1800
        self.assertEqual(crm.forecast(), {"open": 2, "weighted": 600 + 1800, "won": 1000})


class AtomicityTest(unittest.TestCase):
    def test_failures_change_nothing(self):
        crm = CRM(std_reps())
        lid = crm.add_lead("a@corp.com", "A", "referral", "m1")
        snapshot_log = list(crm.log)
        snapshot_lead = dict(crm.leads[lid])
        with self.assertRaises(ValueError):
            crm.qualify("L9", "m1")
        with self.assertRaises(PermissionError):
            crm.qualify(lid, "r2" if crm.leads[lid]["owner"] == "r1" else "r1")
        self.assertEqual(crm.log, snapshot_log)
        self.assertEqual(crm.leads[lid], snapshot_lead)
        self.assertEqual(crm._lead_seq, 1)  # failed add doesn't burn an id
        try:
            crm.add_lead("a@bad", "A", "web", "m1")
        except ValueError:
            pass
        self.assertEqual(len(crm.leads), 1)
        self.assertEqual(len(crm.log), 1)


if __name__ == "__main__":
    unittest.main()
