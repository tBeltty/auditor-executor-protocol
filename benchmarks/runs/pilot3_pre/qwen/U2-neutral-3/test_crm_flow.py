"""Tests for crm.py: convert, advance, discount, transfer, forecast, queue."""

import unittest

from crm import CRM

REPS = [
    {"id": "r1", "role": "rep", "capacity": 2},
    {"id": "r2", "role": "rep", "capacity": 1},
    {"id": "m1", "role": "manager", "capacity": 99},
]


def make_crm():
    return CRM([dict(u) for u in REPS])


def qualified_opp(crm, email="x@site.com", amount=1000, actor="m1"):
    lid = crm.add_lead(email, "N", "referral", actor)
    crm.qualify(lid, actor)
    return lid, crm.convert(lid, amount, actor)


class TestConvert(unittest.TestCase):
    def test_happy(self):
        crm = make_crm()
        lid, oid = qualified_opp(crm)
        self.assertEqual(oid, "O1")
        self.assertEqual(crm.opps[oid], {
            "id": "O1", "lead_id": lid, "owner": "r1", "amount": 1000,
            "original_amount": 1000, "stage": "prospect",
        })
        self.assertEqual(crm.leads[lid]["status"], "converted")
        self.assertEqual(crm.log[-1], ("convert", "O1", "m1"))

    def test_amount_validation(self):
        crm = make_crm()
        lid = crm.add_lead("a@site.com", "A", "referral", "m1")
        crm.qualify(lid, "m1")
        for bad in [0, -3, 1.5, True, False, "10", None]:
            with self.assertRaises(ValueError, msg=repr(bad)):
                crm.convert(lid, bad, "m1")

    def test_check_order(self):
        crm = make_crm()
        lid = crm.add_lead("a@site.com", "A", "web", "m1")   # status new
        with self.assertRaises(ValueError):
            crm.convert("L404", -1, "m1")                    # 1 existence
        with self.assertRaises(ValueError):
            crm.convert(lid, -5, "m1")                       # 2 amount first
        with self.assertRaises(PermissionError):
            crm.convert(lid, 10, "r2")                       # 3 owner/mgr
        with self.assertRaises(ValueError):
            crm.convert(lid, 10, "r1")                       # 4 qualified

    def test_score25_lead_cannot_reach_convert_status_check(self):
        crm = make_crm()
        lid = crm.add_lead("a@site.com", "A", "web", "m1")
        with self.assertRaises(ValueError):                  # score too low
            crm.qualify(lid, "r1")
        with self.assertRaises(ValueError):                  # not qualified
            crm.convert(lid, 10, "r1")

    def test_ownerless_qualified_lead_value_error(self):
        crm = make_crm()
        lids = [crm.add_lead(f"q{i}@site.com", "Q", "referral", "m1")
                for i in range(4)]
        for lid in lids:
            crm.qualify(lid, "m1")
        self.assertIsNone(crm.leads[lids[3]]["owner"])       # queued
        with self.assertRaises(ValueError):                  # 5 must have owner
            crm.convert(lids[3], 100, "m1")
        self.assertEqual(crm.opps, {})

    def _fill_check_order(self):
        """Qualified lead, non-owner actor: order 3 before 4/5."""
        crm = make_crm()
        lid = crm.add_lead("a@site.com", "A", "referral", "m1")
        crm.qualify(lid, "m1")
        return crm, lid


class TestAdvance(unittest.TestCase):
    def test_stage_path_and_logging(self):
        crm = make_crm()
        _, oid = qualified_opp(crm)
        for stage in ("proposal", "negotiation", "won"):
            crm.advance(oid, stage, "m1")
            self.assertEqual(crm.opps[oid]["stage"], stage)
            self.assertEqual(crm.log[-1], ("advance", oid, "m1"))

    def test_won_frees_slot_and_backfills_fifo(self):
        crm = make_crm()
        lids = [crm.add_lead(f"n{i}@site.com", "N", "referral", "m1")
                for i in range(4)]      # L1 r1, L2 r2, L3 r1, L4 queued
        for lid in lids[:3]:
            crm.qualify(lid, "m1")
            crm.convert(lid, 1000, "m1")
        # O1(L1,r1) O2(L2,r2) O3(L3,r1)
        crm.advance("O1", "proposal", "m1")
        crm.advance("O1", "negotiation", "m1")
        crm.advance("O1", "won", "r1")
        self.assertEqual(crm.leads["L4"]["owner"], "r1")     # freed r1 slot
        self.assertEqual(crm.log[-1], ("assign", "L4", "system"))
        self.assertEqual(crm.leads["L4"]["status"], "new")

    def test_lost_also_frees_slot_limited_by_capacity(self):
        crm = make_crm()
        lids = [crm.add_lead(f"s{i}@site.com", "S", "referral", "m1")
                for i in range(5)]      # L1 r1, L2 r2, L3 r1, L4+L5 queued
        for lid in lids[:3]:
            crm.qualify(lid, "m1")
            crm.convert(lid, 100, "m1")
        crm.advance("O2", "lost", "m1")  # O2 owned r2 (cap 1)
        self.assertEqual(crm.log[-1], ("assign", "L4", "system"))
        self.assertEqual(crm.leads["L4"]["owner"], "r2")
        self.assertIsNone(crm.leads["L5"]["owner"])          # capacity 1 stops

    def test_check_order(self):
        crm = make_crm()
        _, oid = qualified_opp(crm)
        with self.assertRaises(ValueError):
            crm.advance("O404", "proposal", "m1")            # 1 existence
        with self.assertRaises(ValueError):
            crm.advance(oid, "closed", "m1")                 # 2 valid stage
        with self.assertRaises(PermissionError):
            crm.advance(oid, "proposal", "r2")               # 3 owner/mgr
        with self.assertRaises(ValueError):
            crm.advance(oid, "negotiation", "m1")            # 5 immediate next
        with self.assertRaises(ValueError):
            crm.advance(oid, "prospect", "m1")               # 5 no sideways
        crm.advance(oid, "proposal", "m1")
        crm.advance(oid, "negotiation", "m1")
        crm.advance(oid, "won", "m1")
        with self.assertRaises(ValueError):
            crm.advance(oid, "lost", "m1")                   # 4 final

    def test_big_deal_gate(self):
        crm = make_crm()
        _, oid = qualified_opp(crm, amount=50001)
        crm.advance(oid, "proposal", "r1")
        with self.assertRaises(PermissionError):
            crm.advance(oid, "negotiation", "r1")            # 6 needs manager
        crm.advance(oid, "negotiation", "m1")                # manager fine
        crm2 = make_crm()
        _, oid2 = qualified_opp(crm2, email="y@site.com", amount=50000)
        crm2.advance(oid2, "proposal", "r1")
        crm2.advance(oid2, "negotiation", "r1")              # exactly 50000 ok

    def test_gate_after_transition_validity(self):
        # rep + huge amount + *illegal* transition -> ValueError (5) not Permission (6)
        crm = make_crm()
        _, oid = qualified_opp(crm, amount=99999)
        with self.assertRaises(ValueError):
            crm.advance(oid, "won", "r1")

    def test_lost_from_any_open_stage(self):
        for stage, steps in [("prospect", 0), ("proposal", 1), ("negotiation", 2)]:
            crm = make_crm()
            _, oid = qualified_opp(crm, email=f"l{stage}@site.com")
            for s in ("proposal", "negotiation")[:steps]:
                crm.advance(oid, s, "m1")
            crm.advance(oid, "lost", "m1")
            self.assertEqual(crm.opps[oid]["stage"], "lost")


class TestDiscount(unittest.TestCase):
    def test_amount_math_and_log(self):
        crm = make_crm()
        _, oid = qualified_opp(crm, amount=1000)
        crm.discount(oid, 10, "r1")
        self.assertEqual(crm.opps[oid]["amount"], 900)
        self.assertEqual(crm.opps[oid]["original_amount"], 1000)
        self.assertEqual(crm.log[-1], ("discount", oid, "r1"))

    def test_pct_validation(self):
        crm = make_crm()
        _, oid = qualified_opp(crm)
        for bad in [0, 31, -1, 1.0, True, "5", None]:
            with self.assertRaises(ValueError, msg=repr(bad)):
                crm.discount(oid, bad, "m1")

    def test_rep_max_10_manager_30(self):
        crm = make_crm()
        _, oid = qualified_opp(crm)
        with self.assertRaises(PermissionError):
            crm.discount(oid, 11, "r1")
        crm.discount(oid, 30, "m1")                          # floor at 70%
        self.assertEqual(crm.opps[oid]["amount"], 700)

    def test_cumulative_floor_uses_original_amount(self):
        crm = make_crm()
        _, oid = qualified_opp(crm, amount=1000)
        crm.discount(oid, 20, "m1")                          # 800
        crm.discount(oid, 10, "m1")                          # 720
        with self.assertRaises(ValueError):                  # 648 < 700 floor
            crm.discount(oid, 10, "m1")
        self.assertEqual(crm.opps[oid]["amount"], 720)

    def test_floor_edge_via_floored_math(self):
        crm = make_crm()
        _, oid = qualified_opp(crm, amount=999)
        with self.assertRaises(ValueError):                  # 699*100 < 69930
            crm.discount(oid, 30, "m1")

    def test_check_order(self):
        crm = make_crm()
        _, oid = qualified_opp(crm)
        with self.assertRaises(ValueError):
            crm.discount("O777", 5, "m1")                    # 1 existence
        with self.assertRaises(ValueError):
            crm.discount(oid, 99, "r2")                      # 2 before 3
        with self.assertRaises(PermissionError):
            crm.discount(oid, 5, "r2")                       # 3 owner/mgr
        crm.advance(oid, "proposal", "m1")
        crm.advance(oid, "negotiation", "m1")
        crm.advance(oid, "won", "m1")
        with self.assertRaises(ValueError):
            crm.discount(oid, 5, "m1")                       # 4 final


class TestTransfer(unittest.TestCase):
    def test_manager_transfer(self):
        crm = make_crm()
        _, oid = qualified_opp(crm)
        crm.transfer(oid, "r2", "m1")
        self.assertEqual(crm.opps[oid]["owner"], "r2")
        self.assertEqual(crm.log[-1], ("transfer", oid, "m1"))

    def test_actor_must_be_manager(self):
        crm = make_crm()
        _, oid = qualified_opp(crm)
        with self.assertRaises(PermissionError):
            crm.transfer(oid, "r2", "r1")

    def test_new_owner_must_be_rep(self):
        crm = make_crm()
        _, oid = qualified_opp(crm)
        for bad in ["m1", "ghost", None, 3]:
            with self.assertRaises(ValueError, msg=repr(bad)):
                crm.transfer(oid, bad, "m1")

    def test_final_stage_same_owner_capacity(self):
        crm = make_crm()
        _, oid = qualified_opp(crm)
        with self.assertRaises(ValueError):
            crm.transfer(oid, "r1", "m1")                    # 5 same owner
        crm2 = make_crm()
        _, oid2 = qualified_opp(crm2, email="b@site.com")
        crm2.advance(oid2, "proposal", "m1")
        crm2.advance(oid2, "negotiation", "m1")
        crm2.advance(oid2, "won", "m1")
        with self.assertRaises(ValueError):
            crm2.transfer(oid2, "r2", "m1")                  # 4 final before 6
        crm3 = make_crm()
        _, oid3 = qualified_opp(crm3, email="c@site.com")
        z = crm3.add_lead("z@site.com", "Z", "referral", "m1")
        crm3.qualify(z, "m1")
        crm3.convert(z, 10, "m1")                            # O2 on r2, at cap
        with self.assertRaises(ValueError):
            crm3.transfer(oid3, "r2", "m1")                  # 6 r2 at capacity

    def test_stage_checks_precede_capacity(self):
        crm = make_crm()
        _, oid = qualified_opp(crm)
        z = crm.add_lead("z@site.com", "Z", "referral", "m1")   # r2 gets lead
        crm.qualify(z, "m1")
        crm.convert(z, 10, "m1")                                 # r2 now full
        crm.advance(oid, "proposal", "m1")
        crm.advance(oid, "negotiation", "m1")
        crm.advance(oid, "won", "m1")
        with self.assertRaises(ValueError):
            crm.transfer(oid, "r2", "m1")                        # 4 final hit

    def test_transfer_frees_previous_owner_slot(self):
        crm = make_crm()
        lids = [crm.add_lead(f"t{i}@site.com", "T", "referral", "m1")
                for i in range(4)]     # L1 r1, L2 r2, L3 r1, L4 queued
        for lid in lids[:3]:
            crm.qualify(lid, "m1")
            crm.convert(lid, 100, "m1")
        # O1(L1,r1) O2(L2,r2) O3(L3,r1); r1 and r2 at cap; L4 queued.
        self.assertIsNone(crm.leads["L4"]["owner"])
        crm.users["r2"]["capacity"] = 2       # give r2 room while L4 waits
        crm.transfer("O1", "r2", "m1")
        self.assertEqual(crm.opps["O1"]["owner"], "r2")
        self.assertEqual(crm.log[-2], ("transfer", "O1", "m1"))
        self.assertEqual(crm.log[-1], ("assign", "L4", "system"))
        self.assertEqual(crm.leads["L4"]["owner"], "r1")        # prev owner


class TestForecast(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(make_crm().forecast(),
                         {"open": 0, "weighted": 0, "won": 0})

    def test_weights_open_won_lost(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 9},
                   {"id": "m1", "role": "manager", "capacity": 1}])
        opps = []
        for i, amt in enumerate((1000, 2000, 4000, 500, 700)):
            lid = crm.add_lead(f"f{i}@site.com", "F", "referral", "m1")
            crm.qualify(lid, "m1")
            opps.append(crm.convert(lid, amt, "m1"))
        crm.advance(opps[1], "proposal", "m1")
        crm.advance(opps[2], "proposal", "m1")
        crm.advance(opps[2], "negotiation", "m1")
        crm.advance(opps[3], "proposal", "m1")
        crm.advance(opps[3], "negotiation", "m1")
        crm.advance(opps[3], "won", "m1")
        crm.advance(opps[4], "lost", "m1")
        f = crm.forecast()
        self.assertEqual(f, {"open": 3, "weighted": 100 + 600 + 2400, "won": 500})
        self.assertNotIn("forecast", [e[0] for e in crm.log])
        self.assertTrue(all(isinstance(t, tuple) for t in crm.log))

    def test_weighted_tracks_discounted_amount(self):
        crm = make_crm()
        _, oid = qualified_opp(crm, amount=1000)
        crm.discount(oid, 10, "m1")
        self.assertEqual(crm.forecast()["weighted"], 90)
        crm.advance(oid, "proposal", "m1")
        self.assertEqual(crm.forecast()["weighted"], 270)    # 900 * 30 // 100


class TestEndToEnd(unittest.TestCase):
    def test_full_journal_sequence(self):
        crm = make_crm()
        l1 = crm.add_lead("Sam@Example.com ", " Sam ", "event", "r1")
        self.assertEqual(crm.leads[l1]["owner"], "r1")
        self.assertEqual(crm.leads[l1]["score"], 35)
        crm.qualify(l1, "r1")
        o1 = crm.convert(l1, 60000, "r1")
        crm.advance(o1, "proposal", "r1")
        with self.assertRaises(PermissionError):
            crm.advance(o1, "negotiation", "r1")
        self.assertEqual(crm.log[-1], ("advance", o1, "r1"))  # failed call inert
        crm.advance(o1, "negotiation", "m1")
        crm.discount(o1, 30, "m1")
        self.assertEqual(crm.opps[o1]["amount"], 42000)
        crm.transfer(o1, "r2", "m1")
        crm.advance(o1, "won", "m1")
        self.assertEqual(crm.forecast(), {"open": 0, "weighted": 0, "won": 42000})
        self.assertEqual([e[0] for e in crm.log],
                         ["add_lead", "qualify", "convert", "advance",
                          "advance", "discount", "transfer", "advance"])
        self.assertEqual(crm.log[4], ("advance", o1, "m1"))   # the manager one
        self.assertEqual(len(crm.log), 8)


if __name__ == "__main__":
    unittest.main()
