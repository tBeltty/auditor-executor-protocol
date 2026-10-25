"""Opportunity lifecycle tests for crm.py: convert, advance, discount,
transfer, forecast, and the waiting-queue slot-freeing rules."""

import unittest

from crm import CRM

REPS = [
    {"id": "r1", "role": "rep", "capacity": 2},
    {"id": "r2", "role": "rep", "capacity": 1},
    {"id": "m1", "role": "manager", "capacity": 99},
]


def make_crm():
    return CRM([dict(u) for u in REPS])


def seeded(lead_count=1, amount=1000):
    """CRM with `lead_count` qualified referral leads converted (distinct
    emails). Returns (crm, last_opp_id)."""
    crm = make_crm()
    last = None
    for i in range(lead_count):
        lid = crm.add_lead(f"x{i}@site.com", "N", "referral", "m1")
        crm.qualify(lid, "m1")
        last = crm.convert(lid, amount, "m1")
    return crm, last


class TestConvert(unittest.TestCase):
    def test_happy(self):
        crm, opp = seeded(1)
        o = crm.opps[opp]
        self.assertEqual(o, {
            "id": "O1", "lead_id": "L1", "owner": "r1",
            "amount": 1000, "original_amount": 1000, "stage": "prospect",
        })
        self.assertEqual(crm.leads["L1"]["status"], "converted")
        self.assertEqual(crm.log[-1], ("convert", "O1", "m1"))

    def test_amount_validation(self):
        crm = make_crm()
        lid = crm.add_lead("a@site.com", "A", "referral", "m1")
        crm.qualify(lid, "m1")
        for bad in [0, -1, 1.5, True, False, "100", None]:
            with self.assertRaises(ValueError, msg=repr(bad)):
                crm.convert(lid, bad, "m1")

    def test_check_order(self):
        crm = make_crm()
        lid = crm.add_lead("a@site.com", "A", "web", "m1")  # score 25, new
        with self.assertRaises(ValueError):
            crm.convert("L404", 0, "m1")          # 1. missing lead
        with self.assertRaises(ValueError):
            crm.convert(lid, -5, "m1")           # 2. amount before owner check
        with self.assertRaises(PermissionError):
            crm.convert(lid, 10, "r2")           # 3. not owner, not manager
        with self.assertRaises(PermissionError):
            crm.convert(lid, "x", "ghost")       # actor guard first of all
        with self.assertRaises(ValueError):
            crm.convert(lid, 10, "r1")           # 4. status not qualified

    def test_unowned_lead_value_error(self):
        crm = make_crm()
        lids = [crm.add_lead(f"q{i}@site.com", "Q", "referral", "m1") for i in range(5)]
        for lid in lids:
            crm.qualify(lid, "m1")
        orphan = crm.leads[lids[3]]
        self.assertIsNone(orphan["owner"])
        with self.assertRaises(ValueError):
            crm.convert(lids[3], 100, "m1")
        before = list(crm.log)
        self.assertEqual(crm.log, before)
        self.assertEqual(crm.opps, {})


class TestAdvance(unittest.TestCase):
    def test_full_path_to_won_and_queue_backfill(self):
        crm = make_crm()
        lids = [crm.add_lead(f"n{i}@site.com", "N", "referral", "m1")
                for i in range(4)]  # L1->r1 L2->r2 L3->r1 L4 queued
        for lid in lids[:3]:
            crm.qualify(lid, "m1")
            crm.convert(lid, 1000, "m1")
        # O1(L1,r1) O2(L2,r2) O3(L3,r1); loads r1=2 (cap), r2=1 (cap)
        crm.advance("O1", "proposal", "m1")
        self.assertEqual(crm.opps["O1"]["stage"], "proposal")
        self.assertEqual(crm.log[-1], ("advance", "O1", "m1"))
        crm.advance("O1", "negotiation", "m1")
        crm.advance("O1", "won", "r1")
        self.assertEqual(crm.log[-2], ("advance", "O1", "r1"))
        # slot freed on r1: queued L4 assigned with system log
        self.assertEqual(crm.log[-1], ("assign", "L4", "system"))
        self.assertEqual(crm.leads["L4"]["owner"], "r1")
        self.assertEqual(crm.leads["L4"]["status"], "new")

    def test_stage_validation_order(self):
        crm, opp = seeded(1)
        with self.assertRaises(ValueError):
            crm.advance("O404", "proposal", "m1")      # 1. missing
        with self.assertRaises(ValueError):
            crm.advance(opp, "closed", "m1")           # 2. bad stage
        with self.assertRaises(PermissionError):
            crm.advance(opp, "proposal", "r2")         # 3. not owner/mgr
        crm.advance(opp, "proposal", "m1")
        crm.advance(opp, "negotiation", "m1")
        crm.advance(opp, "won", "m1")
        with self.assertRaises(ValueError):
            crm.advance(opp, "lost", "m1")             # 4. final stage
        crm2, opp2 = seeded(1)
        with self.assertRaises(ValueError):
            crm2.advance(opp2, "negotiation", "m1")    # 5. not immediate next
        with self.assertRaises(ValueError):
            crm2.advance(opp2, "won", "m1")            # 5. skip
        with self.assertRaises(ValueError):
            crm2.advance(opp2, "prospect", "m1")       # 5. no self/sideways

    def test_lost_allowed_from_any_open_stage(self):
        for stage, n in [("prospect", 0), ("proposal", 1), ("negotiation", 2)]:
            crm, opp = seeded(1)
            for i in range(n):
                crm.advance(opp, ("proposal", "negotiation", "won")[i], "m1")
            self.assertEqual(crm.opps[opp]["stage"], stage)
            crm.advance(opp, "lost", "m1")
            self.assertEqual(crm.opps[opp]["stage"], "lost")
            with self.assertRaises(ValueError):
                crm.advance(opp, "won", "m1")

    def test_big_deal_negotiation_gate(self):
        crm, opp = seeded(1, amount=50001)
        crm.advance(opp, "proposal", "r1")
        with self.assertRaises(PermissionError):
            crm.advance(opp, "negotiation", "r1")   # 6. rep + >50000
        self.assertEqual(crm.opps[opp]["stage"], "proposal")
        crm.advance(opp, "negotiation", "m1")       # manager ok
        self.assertEqual(crm.opps[opp]["stage"], "negotiation")
        crm2, opp2 = seeded(1, amount=50000)
        crm2.advance(opp2, "proposal", "r1")
        crm2.advance(opp2, "negotiation", "r1")     # exactly 50000 ok for rep
        # gate is checked last: bad transition by rep raises ValueError first
        crm3, opp3 = seeded(1, amount=99999)
        crm3.advance(opp3, "proposal", "r1")
        with self.assertRaises(ValueError):
            crm3.advance(opp3, "won", "r1")         # 5 before 6

    def test_slot_free_only_fills_to_capacity(self):
        crm = make_crm()
        lids = [crm.add_lead(f"s{i}@site.com", "S", "referral", "m1")
                for i in range(6)]  # L1 r1, L2 r2, L3 r1, L4-L6 queued
        for lid in lids[:3]:
            crm.qualify(lid, "m1")
            crm.convert(lid, 100, "m1")
        # O1(L1,r1) O2(L2,r2) O3(L3,r1): r1 at cap 2, r2 at cap 1, L4-L6 queued
        crm.advance("O2", "lost", "m1")   # r2 frees its only slot
        self.assertEqual(crm.log[-1], ("assign", "L4", "system"))
        self.assertEqual(crm.leads["L4"]["owner"], "r2")
        self.assertIsNone(crm.leads["L5"]["owner"])  # r2 capacity 1: stops
        self.assertEqual(crm.log.count(("assign", "L5", "system")), 0)

    def test_failed_advance_logs_nothing(self):
        crm, opp = seeded(1)
        before = list(crm.log)
        with self.assertRaises(ValueError):
            crm.advance(opp, "won", "m1")
        self.assertEqual(crm.log, before)
        self.assertEqual(crm.opps[opp]["stage"], "prospect")


class TestDiscount(unittest.TestCase):
    def test_rep_and_manager_limits(self):
        crm, opp = seeded(1, amount=1000)
        crm.discount(opp, 10, "r1")
        self.assertEqual(crm.opps[opp]["amount"], 900)
        self.assertEqual(crm.log[-1], ("discount", opp, "r1"))
        with self.assertRaises(PermissionError):
            crm.discount(opp, 11, "r1")          # 5. rep cap
        crm.discount(opp, 20, "m1")              # manager up to 30 ok
        self.assertEqual(crm.opps[opp]["amount"], 720)

    def test_pct_validation(self):
        crm, opp = seeded(1)
        for bad in [0, 31, -1, 1.0, True, "5", None]:
            with self.assertRaises(ValueError, msg=repr(bad)):
                crm.discount(opp, bad, "m1")
        self.assertEqual(crm.log[-1], ("convert", opp, "m1"))  # untouched

    def test_cumulative_cap_floor(self):
        crm, opp = seeded(1, amount=1000)
        crm.discount(opp, 15, "m1")   # 850
        crm.discount(opp, 15, "m1")   # 722.5 -> 722 ; 722*100 >= 70000 ok
        self.assertEqual(crm.opps[opp]["amount"], 722)
        before = crm.opps[opp]["amount"]
        with self.assertRaises(ValueError):
            crm.discount(opp, 5, "m1")   # 685 -> 68500 < 70000
        self.assertEqual(crm.opps[opp]["amount"], before)

    def test_floor_math_edge(self):
        # 999 at 30% -> 699 ; 69900 >= 69930? no -> ValueError
        crm, opp = seeded(1, amount=999)
        with self.assertRaises(ValueError):
            crm.discount(opp, 30, "m1")

    def test_check_order(self):
        crm, opp = seeded(1)
        with self.assertRaises(ValueError):
            crm.discount("O500", 5, "m1")        # 1. missing opp
        with self.assertRaises(PermissionError):
            crm.discount(opp, 99, "ghost")       # actor guard first of all
        with self.assertRaises(ValueError):
            crm.discount(opp, 99, "r2")          # 2. pct before actor check
        with self.assertRaises(PermissionError):
            crm.discount(opp, 5, "r2")           # 3. not owner/mgr
        with self.assertRaises(PermissionError):
            crm.discount(opp, 11, "r1")          # 5. rep over 10
        crm.advance(opp, "proposal", "m1")
        crm.advance(opp, "negotiation", "m1")
        crm.advance(opp, "won", "m1")
        with self.assertRaises(ValueError):
            crm.discount(opp, 5, "m1")           # 4. final stage


class TestTransfer(unittest.TestCase):
    def test_manager_transfer(self):
        crm, opp = seeded(1)
        crm.transfer(opp, "r2", "m1")
        self.assertEqual(crm.opps[opp]["owner"], "r2")
        self.assertEqual(crm.log[-1], ("transfer", opp, "m1"))

    def test_rep_actor_permission(self):
        crm, opp = seeded(1)
        with self.assertRaises(PermissionError):
            crm.transfer(opp, "r2", "r1")        # 2. only managers

    def test_new_owner_must_be_rep(self):
        crm, opp = seeded(1)
        with self.assertRaises(ValueError):
            crm.transfer(opp, "m1", "m1")        # 3. manager is not a rep
        with self.assertRaises(ValueError):
            crm.transfer(opp, "ghost", "m1")     # 3. unknown user
        with self.assertRaises(ValueError):
            crm.transfer(opp, None, "m1")

    def test_same_owner_and_stage_and_capacity(self):
        crm, opp = seeded(1)
        with self.assertRaises(ValueError):
            crm.transfer(opp, "r1", "m1")        # 5. same owner
        crm2, opp2 = seeded(1)
        crm2.advance(opp2, "proposal", "m1")
        crm2.advance(opp2, "negotiation", "m1")
        crm2.advance(opp2, "won", "m1")
        with self.assertRaises(ValueError):
            crm2.transfer(opp2, "r2", "m1")      # 4. final stage
        crm3, opp3 = seeded(1)
        lid = crm3.add_lead("z@site.com", "Z", "referral", "m1")  # -> r2 (load 0)
        self.assertEqual(crm3.leads[lid]["owner"], "r2")
        crm3.qualify(lid, "m1")
        crm3.convert(lid, 10, "m1")              # O2 owned r2 -> r2 at cap
        with self.assertRaises(ValueError):
            crm3.transfer(opp3, "r2", "m1")      # 6. r2 at capacity

    def test_transfer_frees_previous_owner_slot(self):
        crm = make_crm()
        lids = [crm.add_lead(f"t{i}@site.com", "T", "referral", "m1")
                for i in range(4)]  # L1 r1, L2 r2, L3 r1, L4 queued
        for lid in lids[:3]:
            crm.qualify(lid, "m1")
            crm.convert(lid, 100, "m1")
        # O1(L1,r1) O2(L2,r2) O3(L3,r1): r1 cap 2 full, r2 cap 1 full, L4 queued
        self.assertIsNone(crm.leads["L4"]["owner"])
        crm.users["r2"]["capacity"] = 2  # open room on r2; queue still held
        crm.transfer("O1", "r2", "m1")
        self.assertEqual(crm.opps["O1"]["owner"], "r2")
        self.assertEqual(crm.log[-2], ("transfer", "O1", "m1"))
        # previous owner r1 load 1 < cap 2 -> oldest waiting lead lands on r1
        self.assertEqual(crm.log[-1], ("assign", "L4", "system"))
        self.assertEqual(crm.leads["L4"]["owner"], "r1")

    def test_failed_transfer_no_log(self):
        crm, opp = seeded(1)
        before = list(crm.log)
        with self.assertRaises(ValueError):
            crm.transfer(opp, "m1", "m1")
        self.assertEqual(crm.log, before)
        self.assertEqual(crm.opps[opp]["owner"], "r1")


class TestForecast(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(make_crm().forecast(),
                         {"open": 0, "weighted": 0, "won": 0})

    def test_weights_and_totals(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 9},
                   {"id": "m1", "role": "manager", "capacity": 99}])
        opps = []
        for i, amt in enumerate((1000, 2000, 4000, 500)):
            lid = crm.add_lead(f"f{i}@site.com", "F", "referral", "m1")
            crm.qualify(lid, "m1")
            opps.append(crm.convert(lid, amt, "m1"))
        o1, o2, o3, o4 = opps
        # O1 stays prospect; O2 -> proposal; O3 -> negotiation; O4 -> won
        crm.advance(o2, "proposal", "m1")
        crm.advance(o3, "proposal", "m1")
        crm.advance(o3, "negotiation", "m1")
        crm.advance(o4, "proposal", "m1")
        crm.advance(o4, "negotiation", "m1")
        crm.advance(o4, "won", "m1")
        f = crm.forecast()
        self.assertEqual(f["open"], 3)
        self.assertEqual(f["weighted"], 100 + 600 + 2400)  # 1000p,2000pr,4000n
        self.assertEqual(f["won"], 500)
        # forecast logs nothing
        self.assertNotIn("forecast", [entry[0] for entry in crm.log])

    def test_discount_affects_weighted(self):
        crm, opp = seeded(1, amount=1000)
        crm.discount(opp, 10, "m1")                  # 900 prospect
        self.assertEqual(crm.forecast()["weighted"], 90)


class TestIntegration(unittest.TestCase):
    def test_end_to_end_journal(self):
        crm = make_crm()
        l1 = crm.add_lead("Sam@Example.com ", " Sam ", "event", "r1")
        self.assertEqual(crm.leads[l1]["owner"], "r1")
        self.assertEqual(crm.leads[l1]["score"], 35)
        crm.qualify(l1, "r1")
        o1 = crm.convert(l1, 60000, "r1")
        crm.advance(o1, "proposal", "r1")
        with self.assertRaises(PermissionError):
            crm.advance(o1, "negotiation", "r1")
        crm.advance(o1, "negotiation", "m1")
        crm.discount(o1, 30, "m1")                   # 42000
        self.assertEqual(crm.opps[o1]["amount"], 42000)
        crm.transfer(o1, "r2", "m1")
        self.assertEqual(crm.opps[o1]["owner"], "r2")
        crm.advance(o1, "won", "m1")
        self.assertEqual(crm.forecast()["won"], 42000)
        ops = [e[0] for e in crm.log]
        self.assertEqual(ops, ["add_lead", "qualify", "convert", "advance",
                               "advance", "discount", "transfer", "advance"])


if __name__ == "__main__":
    unittest.main()
