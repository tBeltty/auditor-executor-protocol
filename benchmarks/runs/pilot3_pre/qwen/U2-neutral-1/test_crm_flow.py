import copy
import unittest

from crm import CRM, DuplicateLeadError


def make_crm(*specs):
    reps = [{"id": i, "role": r, "capacity": c} for (i, r, c) in specs]
    return CRM(reps)


def seeded_crm(amount=1000):
    """One rep r1, one manager m1; r1 owns opp O1 (prospect) from a converted lead."""
    c = make_crm(("r1", "rep", 1), ("m1", "manager", 0))
    lid = c.add_lead("a@x.com", "A", "referral", "m1")
    c.qualify(lid, "m1")
    oid = c.convert(lid, amount, "m1")
    c.log.clear()
    return c, lid, oid


class TestAdvance(unittest.TestCase):
    def test_happy_path_and_logging(self):
        c, _, oid = seeded_crm()
        c.advance(oid, "proposal", "r1")
        c.advance(oid, "negotiation", "r1")
        c.advance(oid, "won", "r1")
        self.assertEqual(c.opps[oid]["stage"], "won")
        self.assertEqual(c.log, [("advance", oid, "r1")] * 3)

    def test_stage_validation_before_actor(self):
        c, _, oid = seeded_crm()
        # unknown actor is checked first, even with a bad stage
        with self.assertRaises(PermissionError):
            c.advance(oid, "closed", "ghost")
        # known actor + invalid stage -> ValueError
        with self.assertRaises(ValueError):
            c.advance(oid, "closed", "r1")
        with self.assertRaises(ValueError):
            c.advance("O9", "proposal", "r1")  # unknown opp
        with self.assertRaises(ValueError):
            c.advance(oid, "PROPOSAL", "r1")

    def test_actor_must_be_owner_or_manager(self):
        c = make_crm(("r1", "rep", 1), ("r2", "rep", 1), ("m1", "manager", 0))
        lid = c.add_lead("a@x.com", "A", "referral", "m1")
        c.qualify(lid, "m1")
        oid = c.convert(lid, 100, "m1")  # owner r1
        with self.assertRaises(PermissionError):
            c.advance(oid, "proposal", "r2")
        c.advance(oid, "proposal", "m1")  # manager fine

    def test_final_stage_and_skip_rules(self):
        c, _, oid = seeded_crm()
        with self.assertRaises(ValueError):
            c.advance(oid, "negotiation", "r1")  # skip ahead
        c.advance(oid, "proposal", "r1")
        with self.assertRaises(ValueError):
            c.advance(oid, "won", "r1")  # skip negotiation
        c.advance(oid, "lost", "r1")
        with self.assertRaises(ValueError):
            c.advance(oid, "lost", "r1")  # already final
        with self.assertRaises(ValueError):
            c.advance(oid, "proposal", "m1")  # final beats transition rules
        # actor check comes before final-stage check
        c2, _, o2 = seeded_crm()
        with self.assertRaises(PermissionError):
            c2.advance(o2, "proposal", "ghost")

    def test_big_negotiation_requires_manager(self):
        c, _, oid = seeded_crm(amount=50001)
        c.advance(oid, "proposal", "r1")
        with self.assertRaises(PermissionError):
            c.advance(oid, "negotiation", "r1")
        self.assertEqual(c.opps[oid]["stage"], "proposal")  # nothing changed
        c.advance(oid, "negotiation", "m1")
        self.assertEqual(c.opps[oid]["stage"], "negotiation")
        # exactly 50000 is fine for a rep
        c2, _, o2 = seeded_crm(amount=50000)
        c2.advance(o2, "proposal", "r1")
        c2.advance(o2, "negotiation", "r1")

    def test_lost_is_allowed_from_any_non_final_stage(self):
        c, _, oid = seeded_crm()
        c.advance(oid, "lost", "r1")
        self.assertEqual(c.opps[oid]["stage"], "lost")
        c2, _, o2 = seeded_crm()
        c2.advance(o2, "proposal", "r1")
        c2.advance(o2, "negotiation", "m1")
        c2.advance(o2, "lost", "r1")
        self.assertEqual(c2.opps[o2]["stage"], "lost")

    def test_won_frees_slot_for_waiting_queue(self):
        c, _, oid = seeded_crm()
        w1 = c.add_lead("w1@x.com", "W1", "web", "m1")
        self.assertIsNone(c.leads[w1]["owner"])
        c.log.clear()
        c.advance(oid, "proposal", "r1")
        c.advance(oid, "negotiation", "m1")
        c.advance(oid, "won", "r1")
        self.assertEqual(c.leads[w1]["owner"], "r1")
        self.assertEqual(c.log, [
            ("advance", oid, "r1"),
            ("advance", oid, "m1"),
            ("advance", oid, "r1"),
            ("assign", w1, "system"),
        ])
        # a lost outcome also frees the slot
        c2, _, o2 = seeded_crm()
        w2 = c2.add_lead("w2@x.com", "W2", "web", "m1")
        c2.advance(o2, "lost", "r1")
        self.assertEqual(c2.leads[w2]["owner"], "r1")


class TestDiscount(unittest.TestCase):
    def test_validation(self):
        c, _, oid = seeded_crm(amount=1000)
        with self.assertRaises(ValueError):
            c.discount("O9", 5, "r1")
        for bad in [0, 31, -1, True, False, 5.0, "5", None]:
            with self.assertRaises(ValueError, msg="pct=%r" % (bad,)):
                c.discount(oid, bad, "r1")
        # unknown actor first
        with self.assertRaises(PermissionError):
            c.discount(oid, 5, "ghost")
        self.assertEqual(c.opps[oid]["amount"], 1000)
        self.assertEqual(c.log, [])

    def test_actor_and_stage_order(self):
        c = make_crm(("r1", "rep", 1), ("r2", "rep", 1), ("m1", "manager", 0))
        lid = c.add_lead("a@x.com", "A", "referral", "m1")
        c.qualify(lid, "m1")
        oid = c.convert(lid, 1000, "m1")  # owner r1
        with self.assertRaises(PermissionError):
            c.discount(oid, 5, "r2")
        c.advance(oid, "proposal", "r1")
        c.advance(oid, "lost", "r1")
        # final stage (ValueError #4) beats rep-over-10 (PermissionError #5)
        with self.assertRaises(ValueError):
            c.discount(oid, 25, "r1")
        with self.assertRaises(ValueError):
            c.discount(oid, 5, "m1")

    def test_rep_limit_10_manager_limit_30(self):
        c, _, oid = seeded_crm(amount=1000)
        with self.assertRaises(PermissionError):
            c.discount(oid, 11, "r1")
        c.discount(oid, 10, "r1")
        self.assertEqual(c.opps[oid]["amount"], 900)
        self.assertEqual(c.log[-1], ("discount", oid, "r1"))
        # manager may use up to 30 per call, but the cumulative floor still binds:
        # 900*70//100 = 630 -> 63000 < 1000*70 -> ValueError
        with self.assertRaises(ValueError):
            c.discount(oid, 30, "m1")
        self.assertEqual(c.opps[oid]["amount"], 900)
        c.discount(oid, 22, "m1")  # 900*78//100 = 702 >= 700 floor
        self.assertEqual(c.opps[oid]["amount"], 702)
        with self.assertRaises(ValueError):
            c.discount(oid, 1, "m1")  # 702*99//100 = 694 -> 69400 < 70000
        self.assertEqual(c.opps[oid]["amount"], 702)
        # from a pristine 1000, a single manager 30% discount hits the floor exactly
        c2, _, oid2 = seeded_crm(amount=1000)
        c2.discount(oid2, 30, "m1")  # 700*100 == 1000*70 -> allowed
        self.assertEqual(c2.opps[oid2]["amount"], 700)

    def test_cumulative_cap(self):
        c, _, oid = seeded_crm(amount=1000)
        c.discount(oid, 20, "m1")   # 800
        c.discount(oid, 10, "m1")   # 720 (>= 700 floor ok)
        self.assertEqual(c.opps[oid]["amount"], 720)
        with self.assertRaises(ValueError):
            c.discount(oid, 3, "m1")  # 720*97//100 = 698 -> 69800 < 70000
        self.assertEqual(c.opps[oid]["amount"], 720)
        self.assertEqual(len([e for e in c.log if e[0] == "discount"]), 2)


class TestTransfer(unittest.TestCase):
    def build(self):
        # Only two leads are ever added, so they go to r1 and r2 (lexicographic
        # tie-breaks at equal load) and r3 stays idle with load 0 < capacity.
        c = make_crm(("r1", "rep", 1), ("r2", "rep", 1), ("r3", "rep", 1),
                     ("m1", "manager", 0))
        l1 = c.add_lead("1@x.com", "A", "referral", "m1")   # -> r1
        l2 = c.add_lead("2@x.com", "B", "referral", "m1")   # -> r2
        c.qualify(l1, "m1")
        c.qualify(l2, "m1")
        o1 = c.convert(l1, 500, "m1")  # r1 load 1 (O1 open, l1 converted)
        o2 = c.convert(l2, 500, "m1")  # r2 load 1
        return c, o1, o2

    def test_success(self):
        c, o1, o2 = self.build()
        c.log.clear()
        c.transfer(o1, "r3", "m1")
        self.assertEqual(c.opps[o1]["owner"], "r3")
        # waiting queue is empty, so freeing r1's slot assigns nothing
        self.assertEqual(c.log, [("transfer", o1, "m1")])

    def test_only_managers(self):
        c, o1, o2 = self.build()
        with self.assertRaises(PermissionError):
            c.transfer(o1, "r3", "r1")  # owner but not manager
        # manager check (#2) precedes new_owner validation (#3)
        with self.assertRaises(PermissionError):
            c.transfer(o1, "whoever", "r2")

    def test_target_validation(self):
        c, o1, o2 = self.build()
        with self.assertRaises(ValueError):
            c.transfer(o1, "ghost", "m1")     # unknown user
        with self.assertRaises(ValueError):
            c.transfer(o1, "m1", "m1")        # not a rep
        with self.assertRaises(ValueError):
            c.transfer(o1, "r1", "m1")        # same as current owner
        with self.assertRaises(ValueError):
            c.transfer(o1, "r2", "m1")        # r2 at capacity (load 1 of 1)

    def test_final_stage_rejected(self):
        c, o1, o2 = self.build()
        c.advance(o1, "lost", "r1")
        with self.assertRaises(ValueError):
            c.transfer(o1, "r3", "m1")

    def test_frees_previous_owner_slot(self):
        # Via the API alone, a non-empty queue implies every rep is at capacity
        # (any free slot is filled on add_lead or on a slot release), so a
        # transfer that drains the queue needs a slot freed by other means.
        # We drop one of r2's counted leads by editing the documented `leads`
        # attribute, then transfer to r2 and check r1's freed slot is refilled.
        c = make_crm(("r1", "rep", 1), ("r2", "rep", 1), ("m1", "manager", 0))
        l1 = c.add_lead("1@x.com", "A", "referral", "m1")  # -> r1
        l2 = c.add_lead("2@x.com", "B", "referral", "m1")  # -> r2
        l3 = c.add_lead("3@x.com", "C", "referral", "m1")  # queued (both full)
        self.assertIsNone(c.leads[l3]["owner"])
        c.qualify(l1, "m1")
        o1 = c.convert(l1, 500, "m1")   # r1 still load 1 (O1 open)
        c.leads[l2]["status"] = "converted"  # frees r2's slot directly
        c.log.clear()
        c.transfer(o1, "r2", "m1")
        self.assertEqual(c.opps[o1]["owner"], "r2")
        self.assertEqual(c.leads[l3]["owner"], "r1")  # oldest waiting lead
        self.assertEqual(c.log, [("transfer", o1, "m1"), ("assign", l3, "system")])

    def test_failed_call_changes_nothing(self):
        c, o1, o2 = self.build()
        l3 = c.add_lead("3@x.com", "C", "referral", "m1")  # -> r3
        snapshot = (copy.deepcopy(c.leads), copy.deepcopy(c.opps), list(c.log))
        for call in [
            lambda: c.transfer("O9", "r3", "m1"),
            lambda: c.transfer(o1, "ghost", "m1"),
            lambda: c.transfer(o1, "r3", "r1"),
            lambda: c.advance(o2, "nope", "m1"),
            lambda: c.discount(o2, 99, "m1"),
            lambda: c.qualify("nope", "m1"),
            lambda: c.add_lead("dup@domain", "x", "web", "m1"),
        ]:
            with self.assertRaises(Exception):
                call()
        self.assertEqual((c.leads, c.opps, c.log), snapshot)


class TestForecast(unittest.TestCase):
    def test_empty(self):
        c = make_crm(("r1", "rep", 1))
        self.assertEqual(c.forecast(), {"open": 0, "weighted": 0, "won": 0})

    def test_weights_and_totals(self):
        c = make_crm(("r1", "rep", 5), ("m1", "manager", 0))
        lid = c.add_lead("a@x.com", "A", "referral", "m1")
        c.qualify(lid, "m1")
        o1 = c.convert(lid, 1000, "m1")     # prospect
        lid2 = c.add_lead("b@x.com", "B", "referral", "m1")
        c.qualify(lid2, "m1")
        o2 = c.convert(lid2, 999, "m1")     # -> negotiation
        c.advance(o2, "proposal", "r1")
        c.advance(o2, "negotiation", "r1")
        lid3 = c.add_lead("c@x.com", "C", "referral", "m1")
        c.qualify(lid3, "m1")
        o3 = c.convert(lid3, 700, "m1")     # -> won
        c.advance(o3, "proposal", "r1")
        c.advance(o3, "negotiation", "m1")
        c.advance(o3, "won", "r1")
        lid4 = c.add_lead("d@x.com", "D", "referral", "m1")
        c.qualify(lid4, "m1")
        o4 = c.convert(lid4, 800, "m1")     # -> lost
        c.advance(o4, "lost", "r1")
        before = len(c.log)
        f = c.forecast()
        self.assertEqual(len(c.log), before)  # no log entry
        # open: o1 1000*10//100=100 ; o2 999*60//100=599 -> weighted 699
        self.assertEqual(f, {"open": 2, "weighted": 699, "won": 700})

    def test_won_uses_discounted_amount(self):
        c, _, oid = seeded_crm(amount=1000)
        c.discount(oid, 30, "m1")  # 700
        c.advance(oid, "proposal", "r1")
        c.advance(oid, "negotiation", "m1")
        c.advance(oid, "won", "r1")
        self.assertEqual(c.forecast(), {"open": 0, "weighted": 0, "won": 700})


class TestDuplicateErrorAttr(unittest.TestCase):
    def test_exception_type_and_attr(self):
        self.assertTrue(issubclass(DuplicateLeadError, Exception))
        c = make_crm(("r1", "rep", 5))
        lid = c.add_lead("a@b.com", "A", "web", "r1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            c.add_lead("A@B.COM", "A", "web", "r1")
        self.assertEqual(ctx.exception.existing_id, lid)


if __name__ == "__main__":
    unittest.main()
