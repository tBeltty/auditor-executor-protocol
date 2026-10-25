import unittest

from crm import CRM, DuplicateLeadError

REPS = [
    {"id": "r1", "role": "rep", "capacity": 2},
    {"id": "r2", "role": "rep", "capacity": 1},
    {"id": "m1", "role": "manager", "capacity": 0},
]


def fresh():
    return CRM(REPS)


class AddLeadTests(unittest.TestCase):
    def test_basic_add_and_id_sequence(self):
        c = fresh()
        a = c.add_lead(" A@B.com ", "Ann", "web", "r1")
        b = c.add_lead("b@b.com", "Bo", "referral", "r1")
        self.assertEqual(a, "L1")
        self.assertEqual(b, "L2")
        self.assertEqual(c.leads["L1"]["email"], "a@b.com")
        self.assertEqual(c.leads["L1"]["name"], "Ann")
        self.assertEqual(c.leads["L1"]["owner"], "r1")
        self.assertEqual(c.log[-1], ("add_lead", "L2", "r1"))

    def test_scores(self):
        c = fresh()
        c.add_lead("x@web.com", "X", "web", "r1")  # 10+15
        c.add_lead("y@gmail.com", "Y", "referral", "r2")  # 30
        c.add_lead("z@yahoo.com", "Z", "event", "r1")  # 20
        self.assertEqual(c.leads["L1"]["score"], 25)
        self.assertEqual(c.leads["L2"]["score"], 30)
        self.assertEqual(c.leads["L3"]["score"], 20)

    def test_bad_email(self):
        c = fresh()
        for bad in [None, 5, "a@b", "@b.com", "a@b.com.", "a@@b.com", "@b.com", "a@.b", "a@b.", "a@bcom"]:
            with self.assertRaises(ValueError):
                c.add_lead(bad, "N", "web", "r1")

    def test_bad_name_source(self):
        c = fresh()
        with self.assertRaises(ValueError):
            c.add_lead("a@b.com", "  ", "web", "r1")
        with self.assertRaises(ValueError):
            c.add_lead("a@b.com", 3, "web", "r1")
        with self.assertRaises(ValueError):
            c.add_lead("a@b.com", "N", "blog", "r1")

    def test_duplicate(self):
        c = fresh()
        c.add_lead("a@b.com", "Ann", "web", "r1")
        with self.assertRaises(DuplicateLeadError) as cm:
            c.add_lead("A@B.com ", "Again", "web", "r1")
        self.assertEqual(cm.exception.existing_id, "L1")
        self.assertEqual(len(c.log), 1)

    def test_unknown_actor_first(self):
        c = fresh()
        with self.assertRaises(PermissionError):
            c.add_lead("a@b.com", "Ann", "web", "zz")
        self.assertEqual(c.log, [])

    def test_capacity_and_queue(self):
        c = CRM([{"id": "r1", "role": "rep", "capacity": 1}])
        c.add_lead("a@b.com", "Ann", "web", "r1")  # r1 now at capacity
        l2 = c.add_lead("b@b.com", "Bob", "web", "r1")
        self.assertIsNone(c.leads[l2]["owner"])
        l3 = c.add_lead("c@b.com", "Cid", "web", "r1")
        self.assertIsNone(c.leads[l2]["owner"])
        self.assertIsNone(c.leads[l3]["owner"])
        # closing nothing yet; check ties pick smallest id
        c2 = CRM([
            {"id": "rb", "role": "rep", "capacity": 3},
            {"id": "ra", "role": "rep", "capacity": 3},
        ])
        lid = c2.add_lead("d@b.com", "Dee", "web", "ra")
        self.assertEqual(c2.leads[lid]["owner"], "ra")


class QualifyConvertTests(unittest.TestCase):
    def test_qualify_path(self):
        c = fresh()
        lid = c.add_lead("ref@corp.com", "Ann", "referral", "r1")  # score 30
        c.qualify(lid, "r1")
        self.assertEqual(c.leads[lid]["status"], "qualified")
        self.assertEqual(c.log[-1], ("qualify", lid, "r1"))
        with self.assertRaises(ValueError):
            c.qualify(lid, "m1")  # no longer "new"

    def test_qualify_low_score(self):
        c = fresh()
        lid = c.add_lead("a@gmail.com", "Ann", "web", "r1")  # 10
        with self.assertRaises(ValueError):
            c.qualify(lid, "r1")

    def test_qualify_permissions_and_status(self):
        c = fresh()
        lid = c.add_lead("ref@corp.com", "Ann", "referral", "r1")
        with self.assertRaises(PermissionError):
            c.qualify(lid, "r2")
        with self.assertRaises(PermissionError):
            c.qualify(lid, "unknown")
        with self.assertRaises(ValueError):
            c.qualify("L99", "m1")
        c.qualify(lid, "m1")
        with self.assertRaises(ValueError):
            c.qualify(lid, "r1")

    def test_convert(self):
        c = fresh()
        lid = c.add_lead("ref@corp.com", "Ann", "referral", "r1")
        with self.assertRaises(ValueError):
            c.convert(lid, 100, "r1")  # not qualified
        c.qualify(lid, "r1")
        with self.assertRaises(ValueError):
            c.convert(lid, True, "r1")
        with self.assertRaises(ValueError):
            c.convert(lid, -5, "r1")
        with self.assertRaises(ValueError):
            c.convert(lid, 1.5, "r1")
        with self.assertRaises(ValueError):
            c.convert(lid, 0, "r1")
        with self.assertRaises(PermissionError):
            c.convert(lid, 100, "r2")
        oid = c.convert(lid, 100, "m1")
        self.assertEqual(oid, "O1")
        self.assertEqual(c.opps[oid]["owner"], "r1")
        self.assertEqual(c.opps[oid]["stage"], "prospect")
        self.assertEqual(c.leads[lid]["status"], "converted")
        self.assertEqual(c.log[-1], ("convert", oid, "m1"))


class AdvanceTests(unittest.TestCase):
    def test_full_path(self):
        c = fresh()
        lid = c.add_lead("ref@corp.com", "Ann", "referral", "r1")
        c.qualify(lid, "r1")
        oid = c.convert(lid, 100, "r1")
        c.advance(oid, "proposal", "r1")
        c.advance(oid, "negotiation", "m1")  # manager may act
        c.advance(oid, "won", "m1")
        self.assertEqual(c.opps[oid]["stage"], "won")
        self.assertEqual(c.log[-1], ("advance", oid, "m1"))
        with self.assertRaises(ValueError):
            c.advance(oid, "proposal", "m1")

    def test_losses_and_skips(self):
        c = fresh()
        lid = c.add_lead("ref@corp.com", "Ann", "referral", "r1")
        c.qualify(lid, "r1")
        oid = c.convert(lid, 100, "r1")
        with self.assertRaises(ValueError):
            c.advance(oid, "won", "r1")  # skip
        with self.assertRaises(ValueError):
            c.advance(oid, "bogus", "r1")
        with self.assertRaises(ValueError):
            c.advance("O9", "won", "r1")
        with self.assertRaises(PermissionError):
            c.advance(oid, "lost", "r2")
        c.advance(oid, "lost", "r1")
        self.assertEqual(c.opps[oid]["stage"], "lost")

    def test_big_negotiation_needs_manager(self):
        c = fresh()
        lid = c.add_lead("ref@corp.com", "Ann", "referral", "r1")
        c.qualify(lid, "r1")
        oid = c.convert(lid, 60000, "r1")
        c.advance(oid, "proposal", "r1")
        with self.assertRaises(PermissionError):
            c.advance(oid, "negotiation", "r1")
        c.advance(oid, "negotiation", "m1")
        self.assertEqual(c.opps[oid]["stage"], "negotiation")


class DiscountTests(unittest.TestCase):
    def make_opp(self, c, amount=1000, lid=None):
        lid = c.add_lead("ref@corp.com", "Ann", "referral", "r1")
        c.qualify(lid, "r1")
        return c.convert(lid, amount, "r1")

    def test_discount_rules(self):
        c = fresh()
        oid = self.make_opp(c)
        with self.assertRaises(ValueError):
            c.discount(oid, 0, "r1")
        with self.assertRaises(ValueError):
            c.discount(oid, 31, "r1")
        with self.assertRaises(ValueError):
            c.discount(oid, True, "r1")
        with self.assertRaises(ValueError):
            c.discount(oid, 5.0, "r1")
        with self.assertRaises(ValueError):
            c.discount("O9", 5, "r1")
        with self.assertRaises(PermissionError):
            c.discount(oid, 5, "r2")
        c.discount(oid, 10, "r1")
        self.assertEqual(c.opps[oid]["amount"], 900)
        c.discount(oid, 10, "r1")
        self.assertEqual(c.opps[oid]["amount"], 810)
        with self.assertRaises(PermissionError):
            c.discount(oid, 30, "r1")  # rep above 10
        with self.assertRaises(ValueError):
            c.discount(oid, 20, "m1")  # 810*0.8=648 -> below 700 floor
        c.discount(oid, 10, "m1")  # 729: 72900 >= 70000 ok
        self.assertEqual(c.opps[oid]["amount"], 729)

    def test_cumulative_floor(self):
        c = fresh()
        oid = self.make_opp(c)
        c.discount(oid, 30, "m1")  # 700 == floor, allowed
        with self.assertRaises(ValueError):
            c.discount(oid, 1, "m1")  # 700*99//100 = 693 < 700


class TransferTests(unittest.TestCase):
    def test_transfer_flow(self):
        c = fresh()
        lid = c.add_lead("ref@corp.com", "Ann", "referral", "r1")
        c.qualify(lid, "r1")
        oid = c.convert(lid, 100, "r1")  # r1 owner
        with self.assertRaises(PermissionError):
            c.transfer(oid, "r2", "r1")  # not manager
        with self.assertRaises(ValueError):
            c.transfer("O9", "r2", "m1")
        with self.assertRaises(ValueError):
            c.transfer(oid, "m1", "m1")  # not a rep
        with self.assertRaises(ValueError):
            c.transfer(oid, "zz", "m1")
        with self.assertRaises(ValueError):
            c.transfer(oid, "r1", "m1")  # same owner
        c.transfer(oid, "r2", "m1")
        self.assertEqual(c.opps[oid]["owner"], "r2")
        self.assertEqual(c.log[-1], ("transfer", oid, "m1"))

    def test_transfer_to_full_rep(self):
        c = fresh()
        lid = c.add_lead("ref@corp.com", "Ann", "referral", "r1")
        c.qualify(lid, "r1")
        oid = c.convert(lid, 100, "r1")
        c.add_lead("b@b.com", "Bob", "web", "r2")  # r2 now at capacity (1)
        with self.assertRaises(ValueError):
            c.transfer(oid, "r2", "m1")


class QueueFreedSlotTests(unittest.TestCase):
    def test_assign_to_freer_of_slot_on_advance(self):
        c = CRM([{"id": "r1", "role": "rep", "capacity": 1}, {"id": "m1", "role": "manager", "capacity": 0}])
        lid1 = c.add_lead("ref@corp.com", "Ann", "referral", "r1")
        c.qualify(lid1, "r1")
        oid = c.convert(lid1, 100, "r1")
        # r1 load: opp=1 (lead1 is "converted", not counted)
        lid2 = c.add_lead("b@b.com", "Bob", "web", "r1")
        # r1 load 1 >= capacity 1 -> queued
        self.assertIsNone(c.leads[lid2]["owner"])
        # closing the opp frees the slot -> L2 assigned
        c.advance(oid, "lost", "r1")
        self.assertEqual(c.leads[lid2]["owner"], "r1")
        self.assertEqual([e for e in c.log if e[0] == "assign"], [("assign", lid2, "system")])

    def test_assign_multiple_in_fifo_order(self):
        c = CRM([{"id": "r1", "role": "rep", "capacity": 1}, {"id": "m1", "role": "manager", "capacity": 0}])
        lid = c.add_lead("ref@corp.com", "Ann", "referral", "r1")
        c.qualify(lid, "r1")
        oid = c.convert(lid, 100, "r1")
        lid2 = c.add_lead("b@b.com", "Bob", "web", "r1")
        lid3 = c.add_lead("c@b.com", "Cid", "web", "r1")
        # r1 at capacity (1 opp) -> both queued
        self.assertIsNone(c.leads[lid2]["owner"])
        self.assertIsNone(c.leads[lid3]["owner"])
        # closing frees exactly one slot: only the oldest queued lead is pulled
        c.advance(oid, "lost", "r1")
        self.assertEqual(c.leads[lid2]["owner"], "r1")
        self.assertIsNone(c.leads[lid3]["owner"])
        self.assertEqual([e for e in c.log if e[0] == "assign"], [("assign", lid2, "system")])

    def test_transfer_changes_owner_and_logs(self):
        c = CRM([
            {"id": "r1", "role": "rep", "capacity": 3},
            {"id": "r2", "role": "rep", "capacity": 3},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        lid = c.add_lead("ref@corp.com", "Ann", "referral", "r1")
        c.qualify(lid, "r1")
        oid = c.convert(lid, 100, "r1")
        c.transfer(oid, "r2", "m1")
        self.assertEqual(c.opps[oid]["owner"], "r2")
        self.assertEqual(c.log[-1], ("transfer", oid, "m1"))
        self.assertEqual([e for e in c.log if e[0] == "assign"], [])  # nothing queued


class ForecastTests(unittest.TestCase):
    def test_forecast(self):
        c = fresh()
        lid = c.add_lead("ref@corp.com", "Ann", "referral", "r1")
        c.qualify(lid, "r1")
        o1 = c.convert(lid, 1000, "r1")  # prospect
        c.advance(o1, "proposal", "r1")
        lid2 = c.add_lead("ref2@corp.com", "Bo", "referral", "r1")
        self.assertEqual(c.leads[lid2]["owner"], "r2")  # r2 has lower load
        c.qualify(lid2, "r2")
        o2 = c.convert(lid2, 2000, "r2")  # prospect
        self.assertEqual(c.opps[o2]["owner"], "r2")
        c.advance(o1, "negotiation", "r1")
        c.advance(o1, "won", "r1")
        f = c.forecast()
        self.assertEqual(f["open"], 1)
        self.assertEqual(f["weighted"], 2000 * 10 // 100)
        self.assertEqual(f["won"], 1000)
        self.assertEqual(c.log[-1], ("advance", o1, "r1"))


if __name__ == "__main__":
    unittest.main()
