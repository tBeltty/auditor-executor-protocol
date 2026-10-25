"""Edge cases complementing test_crm_core.py / test_crm_flow.py.

Covers: check-order interactions between methods, load accounting through
open opportunities, the full waiting-queue lifecycle, discount rounding
boundaries, and duplicates against queued (unowned) leads.
"""

import unittest

from crm import CRM, DuplicateLeadError


def make_crm(*specs):
    reps = [{"id": i, "role": r, "capacity": c} for (i, r, c) in specs]
    return CRM(reps)


def owned_open_opp(c, manager, email="a@x.com", amount=100):
    """Lead -> qualified -> converted, all by the manager; returns (lead, opp)."""
    lid = c.add_lead(email, "A", "referral", manager)
    c.qualify(lid, manager)
    return lid, c.convert(lid, amount, manager)


class TestCheckOrderInteractions(unittest.TestCase):
    def test_advance_bad_stage_beats_wrong_owner(self):
        # stage validation (#2, ValueError) runs before ownership (#3, PermissionError)
        c = make_crm(("r1", "rep", 1), ("r2", "rep", 1), ("m1", "manager", 0))
        _, oid = owned_open_opp(c, "m1")  # owner r1
        with self.assertRaises(ValueError):
            c.advance(oid, "nonsense", "r2")
        self.assertEqual(c.opps[oid]["stage"], "prospect")

    def test_discount_bad_pct_beats_wrong_owner(self):
        c = make_crm(("r1", "rep", 1), ("r2", "rep", 1), ("m1", "manager", 0))
        _, oid = owned_open_opp(c, "m1")
        with self.assertRaises(ValueError):
            c.discount(oid, 99, "r2")  # pct (#2) before ownership (#3)
        with self.assertRaises(PermissionError):
            c.discount(oid, 5, "r2")   # valid pct, wrong actor -> PermissionError

    def test_big_negotiation_failure_keeps_queue_and_stage(self):
        c = make_crm(("r1", "rep", 1), ("m1", "manager", 0))
        _, oid = owned_open_opp(c, "m1", amount=50001)
        c.advance(oid, "proposal", "m1")
        w = c.add_lead("w@x.com", "W", "web", "m1")  # queued: r1 at capacity via O1
        self.assertIsNone(c.leads[w]["owner"])
        with self.assertRaises(PermissionError):
            c.advance(oid, "negotiation", "r1")
        self.assertEqual(c.opps[oid]["stage"], "proposal")
        self.assertIsNone(c.leads[w]["owner"])
        # the manager may proceed; exactly 50000 would not have needed one
        c.advance(oid, "negotiation", "m1")
        self.assertEqual(c.opps[oid]["stage"], "negotiation")

    def test_unknown_actor_wins_everywhere(self):
        # general rule: the actor check is first in every method, beating any
        # ValueError from existence/format checks
        c = make_crm(("r1", "rep", 1))
        lid = c.add_lead("a@x.com", "A", "web", "r1")  # score 10
        before = list(c.log)
        for call in [
            lambda: c.add_lead("bad", "bad", "bad", "ghost"),
            lambda: c.qualify("L99", "ghost"),
            lambda: c.qualify(lid, "ghost"),
            lambda: c.convert(lid, -1, "ghost"),
            lambda: c.advance("O9", "closed", "ghost"),
            lambda: c.discount("O9", 0, "ghost"),
            lambda: c.transfer("O9", "ghost", "ghost"),
        ]:
            with self.assertRaises(PermissionError):
                call()
        self.assertEqual(c.log, before)  # nothing appended


class TestLoadAccountingViaOpps(unittest.TestCase):
    def test_conversion_frees_lead_slot_but_open_opp_occupies_it(self):
        # new/qualified leads and open opps each count 1; converted leads and
        # won/lost opps count 0, so conversion keeps the rep's load flat
        c = make_crm(("r1", "rep", 5), ("r2", "rep", 5), ("m1", "manager", 0))
        _, oa = owned_open_opp(c, "m1", "a@x.com")   # r1: lead then Oa -> load 1
        _, ob = owned_open_opp(c, "m1", "b@x.com")   # r2: load 1
        d = c.add_lead("d@x.com", "D", "referral", "m1")
        self.assertEqual(c.leads[d]["owner"], "r1")  # tie at load 1 -> "r1" < "r2"
        c.advance(oa, "proposal", "m1")
        c.advance(oa, "negotiation", "m1")
        c.advance(oa, "won", "m1")                   # r1 load drops 2 -> 1
        e = c.add_lead("e@x.com", "E", "referral", "m1")
        self.assertEqual(c.leads[e]["owner"], "r1")  # still tied at 1 -> "r1" again
        c.advance(ob, "lost", "m1")                  # r2 load drops to 0
        f = c.add_lead("f@x.com", "F", "referral", "m1")
        self.assertEqual(c.leads[f]["owner"], "r2")  # load 0 beats r1's load 2

    def test_lost_opp_frees_load_for_selection(self):
        c = make_crm(("r1", "rep", 1), ("r2", "rep", 1), ("m1", "manager", 0))
        _, oid = owned_open_opp(c, "m1")             # r1 full (O1), r2 idle
        w = c.add_lead("w@x.com", "W", "referral", "m1")
        self.assertEqual(c.leads[w]["owner"], "r2")  # r2 has load 0
        c.advance(oid, "lost", "m1")
        # r1's slot frees; queue is empty, so the next add picks r1 (load 0 < r2's 1)
        x = c.add_lead("x@x.com", "X", "referral", "m1")
        self.assertEqual(c.leads[x]["owner"], "r1")


class TestWaitingQueueLifecycle(unittest.TestCase):
    def test_qualified_queued_lead_keeps_status_when_assigned(self):
        c = make_crm(("r1", "rep", 1), ("m1", "manager", 0))
        _, oid = owned_open_opp(c, "m1", "a@x.com")
        q = c.add_lead("q@x.com", "Q", "referral", "m1")  # queued: r1 full via O1
        self.assertIsNone(c.leads[q]["owner"])
        c.qualify(q, "m1")  # managers may qualify unowned leads
        c.advance(oid, "proposal", "m1")
        c.advance(oid, "negotiation", "m1")
        c.log.clear()
        c.advance(oid, "won", "m1")  # frees r1's slot -> oldest waiting lead assigned
        self.assertEqual(c.leads[q]["owner"], "r1")
        self.assertEqual(c.leads[q]["status"], "qualified")
        self.assertEqual(c.log, [("advance", oid, "m1"), ("assign", q, "system")])
        # the assigned qualified lead counts toward load, so the next lead queues
        n = c.add_lead("n@x.com", "N", "referral", "m1")
        self.assertIsNone(c.leads[n]["owner"])
        # r1 can now convert the lead the system assigned to them
        oid2 = c.convert(q, 50, "r1")
        self.assertEqual(oid2, "O2")
        self.assertEqual(c.opps[oid2]["owner"], "r1")
        # converting dropped q's lead-count but O2 occupies the slot; n stays queued
        self.assertIsNone(c.leads[n]["owner"])

    def test_duplicate_against_queued_unowned_lead(self):
        c = make_crm(("m1", "manager", 0))  # no reps at all: everything queues
        l1 = c.add_lead("a@x.com", "A", "web", "m1")
        self.assertIsNone(c.leads[l1]["owner"])
        with self.assertRaises(DuplicateLeadError) as ctx:
            c.add_lead("  A@X.COM ", "A again", "event", "m1")
        self.assertEqual(ctx.exception.existing_id, l1)

    def test_capacity_zero_reps_queue_immediately(self):
        c = make_crm(("r1", "rep", 0), ("m1", "manager", 0))
        l = c.add_lead("a@x.com", "A", "web", "m1")
        self.assertIsNone(c.leads[l]["owner"])
        # a rep is not the owner of a queued lead (owner is None)
        with self.assertRaises(PermissionError):
            c.qualify(l, "r1")
        # still "new", so convert fails on status before the no-owner check
        with self.assertRaises(ValueError):
            c.convert(l, 5, "m1")
        self.assertEqual(l, "L1")
        self.assertEqual(c.log, [("add_lead", l, "m1")])

    def test_rep_may_not_act_on_another_reps_lead_or_queued_lead(self):
        c = make_crm(("r1", "rep", 1), ("r2", "rep", 1), ("m1", "manager", 0))
        l1 = c.add_lead("1@x.com", "A", "referral", "m1")  # -> r1
        c.add_lead("2@x.com", "B", "referral", "m1")       # -> r2
        l3 = c.add_lead("3@x.com", "C", "referral", "m1")  # queued
        with self.assertRaises(PermissionError):
            c.qualify(l1, "r2")   # r2 is neither owner nor manager
        with self.assertRaises(PermissionError):
            c.qualify(l3, "r1")   # queued lead has owner None; a rep is not the owner
        self.assertEqual(c.leads[l3]["status"], "new")


class TestDiscountRounding(unittest.TestCase):
    def test_floor_check_with_truncation(self):
        # 999 at 30% truncates to 699, and 699*100=69900 < 999*70=69930 -> rejected;
        # 29% gives 709 which clears the floor, and repeated small cuts then bind.
        c = make_crm(("r1", "rep", 5), ("m1", "manager", 0))
        _, oid = owned_open_opp(c, "m1", "a@x.com", amount=999)
        with self.assertRaises(ValueError):
            c.discount(oid, 30, "m1")
        self.assertEqual(c.opps[oid]["amount"], 999)
        c.discount(oid, 29, "m1")  # 999*71//100 = 709 -> 70900 >= 69930
        self.assertEqual(c.opps[oid]["amount"], 709)
        with self.assertRaises(ValueError):
            c.discount(oid, 2, "m1")  # 709*98//100 = 694 -> 69400 < 69930
        self.assertEqual(c.opps[oid]["amount"], 709)
        c.discount(oid, 1, "m1")  # 709*99//100 = 701 -> 70100 >= 69930
        self.assertEqual(c.opps[oid]["amount"], 701)

    def test_rep_cap_is_permission_error_not_value_error(self):
        c = make_crm(("r1", "rep", 5), ("m1", "manager", 0))
        _, oid = owned_open_opp(c, "m1", "a@x.com", amount=1000)
        with self.assertRaises(PermissionError):
            c.discount(oid, 11, "r1")  # over rep cap -> #5 PermissionError
        with self.assertRaises(ValueError):
            c.discount(oid, 31, "r1")  # outside 1..30 -> #2 ValueError (checked first)
        c.discount(oid, 30, "m1")      # manager: exactly the floor, 700*100 == 1000*70
        self.assertEqual(c.opps[oid]["amount"], 700)
        with self.assertRaises(ValueError):
            c.discount(oid, 1, "m1")   # 693*100 < 70000 -> cumulative floor binds
        self.assertEqual(c.opps[oid]["amount"], 700)


class TestForecastWeights(unittest.TestCase):
    def test_discount_reduces_weighted_forecast(self):
        c = make_crm(("r1", "rep", 5), ("m1", "manager", 0))
        _, o1 = owned_open_opp(c, "m1", "a@x.com", amount=1000)
        c.discount(o1, 10, "m1")  # 900, still prospect
        c.advance(o1, "proposal", "m1")
        self.assertEqual(c.forecast(), {"open": 1, "weighted": 270, "won": 0})
        c.advance(o1, "negotiation", "m1")
        self.assertEqual(c.forecast(), {"open": 1, "weighted": 540, "won": 0})
        c.advance(o1, "won", "m1")
        self.assertEqual(c.forecast(), {"open": 0, "weighted": 0, "won": 900})


if __name__ == "__main__":
    unittest.main()
