import unittest

import crm


def make_crm():
    return crm.CRM([
        {"id": "r1", "role": "rep", "capacity": 1},
        {"id": "r2", "role": "rep", "capacity": 1},
        {"id": "m1", "role": "manager", "capacity": 3},
    ])


def crm_caps(r1, r2):
    return crm.CRM([
        {"id": "r1", "role": "rep", "capacity": r1},
        {"id": "r2", "role": "rep", "capacity": r2},
        {"id": "m1", "role": "manager", "capacity": 5},
    ])


def qualified_lead(c, email, actor):
    lid = c.add_lead(email, "Name", "referral", actor)  # score 45
    c.qualify(lid, actor)
    return lid


class TestQualify(unittest.TestCase):
    def test_owner_and_manager(self):
        c = make_crm()
        c.add_lead("a@x.io", "A", "referral", "r1")
        c.qualify("L1", "r1")
        self.assertEqual(c.leads["L1"]["status"], "qualified")
        c.add_lead("b@x.io", "B", "referral", "r1")
        c.qualify("L2", "m1")
        self.assertEqual(c.log[-1], ("qualify", "L2", "m1"))

    def test_other_rep_forbidden(self):
        c = make_crm()
        c.add_lead("a@x.io", "A", "referral", "r1")
        with self.assertRaises(PermissionError):
            c.qualify("L1", "r2")
        self.assertEqual(c.leads["L1"]["status"], "new")

    def test_checks_order_permission_before_status(self):
        c = make_crm()
        c.add_lead("a@x.io", "A", "web", "r1")  # score 25, below threshold
        with self.assertRaises(PermissionError):  # r2 fails check 2 first
            c.qualify("L1", "r2")
        with self.assertRaises(ValueError):
            c.qualify("L1", "r1")  # score too low (check 4)
        with self.assertRaises(ValueError):
            c.qualify("NOPE", "m1")  # unknown lead

    def test_already_qualified(self):
        c = make_crm()
        c.add_lead("a@x.io", "A", "referral", "r1")
        c.qualify("L1", "r1")
        with self.assertRaises(ValueError):
            c.qualify("L1", "r1")

    def test_manager_can_qualify_unowned(self):
        c = crm.CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        c.add_lead("a@x.io", "A", "referral", "m1")
        c.add_lead("b@x.io", "B", "referral", "m1")  # queued, owner None
        c.qualify("L2", "m1")
        self.assertEqual(c.leads["L2"]["status"], "qualified")


class TestConvert(unittest.TestCase):
    def test_success(self):
        c = make_crm()
        lid = qualified_lead(c, "a@x.io", "r1")
        oid = c.convert(lid, 1000, "r1")
        self.assertEqual(oid, "O1")
        opp = c.opps["O1"]
        self.assertEqual(opp, {"id": "O1", "lead_id": "L1", "owner": "r1",
                               "amount": 1000, "original_amount": 1000,
                               "stage": "prospect"})
        self.assertEqual(c.leads["L1"]["status"], "converted")
        self.assertEqual(c.log[-1], ("convert", "O1", "r1"))

    def test_amount_validation(self):
        c = make_crm()
        lid = qualified_lead(c, "a@x.io", "r1")
        for bad in [0, -5, True, 1.5, "100", None]:
            with self.assertRaises(ValueError, msg=repr(bad)):
                c.convert(lid, bad, "r1")

    def test_permission_and_status_and_owner(self):
        c = make_crm()
        lid = qualified_lead(c, "a@x.io", "r1")
        with self.assertRaises(PermissionError):
            c.convert(lid, 100, "r2")
        c2 = make_crm()
        c2.add_lead("a@x.io", "A", "referral", "r1")
        with self.assertRaises(ValueError):
            c2.convert("L1", 100, "r1")  # not qualified
        # unowned lead qualified by manager cannot convert
        c3 = crm.CRM([{"id": "r1", "role": "rep", "capacity": 1},
                      {"id": "m1", "role": "manager", "capacity": 0}])
        c3.add_lead("a@x.io", "A", "referral", "m1")
        c3.add_lead("b@x.io", "B", "referral", "m1")
        c3.qualify("L2", "m1")
        with self.assertRaises(ValueError):
            c3.convert("L2", 100, "m1")  # no owner

    def test_opp_ids_increment_only_on_success(self):
        c = make_crm()
        a = qualified_lead(c, "a@x.io", "r1")
        b = qualified_lead(c, "b@y.io", "m1")
        with self.assertRaises(PermissionError):
            c.convert(a, 10, "r2")  # wrong actor
        self.assertEqual(c.convert(a, 10, "r1"), "O1")
        self.assertEqual(c.convert(b, 20, "m1"), "O2")


class TestAdvance(unittest.TestCase):
    def _opp(self, amount=1000):
        c = make_crm()
        lid = qualified_lead(c, "a@x.io", "r1")
        oid = c.convert(lid, amount, "r1")
        return c, oid

    def test_full_happy_path(self):
        c, oid = self._opp()
        for stage in ["proposal", "negotiation", "won"]:
            c.advance(oid, stage, "r1")
            self.assertEqual(c.opps[oid]["stage"], stage)
            self.assertEqual(c.log[-1], ("advance", oid, "r1"))

    def test_invalid_stage_is_value_error_before_permission(self):
        c, oid = self._opp()
        with self.assertRaises(ValueError):
            c.advance(oid, "closed", "r2")
        with self.assertRaises(ValueError):
            c.advance("NOPE", "proposal", "m1")

    def test_skip_and_backwards_rejected(self):
        c, oid = self._opp()
        with self.assertRaises(ValueError):
            c.advance(oid, "negotiation", "r1")  # skips proposal
        c.advance(oid, "proposal", "r1")
        with self.assertRaises(ValueError):
            c.advance(oid, "prospect", "r1")  # backwards
        with self.assertRaises(ValueError):
            c.advance(oid, "proposal", "r1")  # same stage
        self.assertEqual(c.opps[oid]["stage"], "proposal")
        self.assertEqual(c.log[-1], ("advance", "O1", "r1"))
        self.assertEqual(len(c.log), 4)  # add, qualify, convert, one advance

    def test_lost_from_any_nonfinal_then_final(self):
        for prefix in [[], ["proposal"], ["proposal", "negotiation"]]:
            c, oid = self._opp()
            for s in prefix:
                c.advance(oid, s, "r1")
            c.advance(oid, "lost", "m1")
            self.assertEqual(c.opps[oid]["stage"], "lost")
            with self.assertRaises(ValueError):
                c.advance(oid, "won", "m1")  # final

    def test_big_negotiation_requires_manager(self):
        c, oid = self._opp(amount=60000)
        c.advance(oid, "proposal", "r1")
        with self.assertRaises(PermissionError):
            c.advance(oid, "negotiation", "r1")
        c.advance(oid, "negotiation", "m1")
        self.assertEqual(c.opps[oid]["stage"], "negotiation")
        # winning a big deal needs no manager
        c.advance(oid, "won", "r1")

    def test_won_frees_slot_and_drains_queue_fifo(self):
        c = make_crm()
        a = qualified_lead(c, "a@x.io", "r1")
        c.add_lead("b@x.io", "B", "referral", "r1")  # -> r2
        c.add_lead("c@x.io", "C", "referral", "r1")  # queued
        c.add_lead("d@x.io", "D", "referral", "r1")  # queued
        oid = c.convert(a, 500, "r1")
        for stage in ["proposal", "negotiation", "won"]:
            c.advance(oid, stage, "r1")
        # r1 is empty again, so the OLDEST waiting lead lands on r1 only
        self.assertEqual(c.leads["L3"]["owner"], "r1")
        self.assertIsNone(c.leads["L4"]["owner"])
        self.assertEqual(c.log[-1], ("assign", "L3", "system"))
        # assigned lead now counts toward load, so r1 stops at capacity
        self.assertEqual(c._load("r1"), 1)


class TestDiscount(unittest.TestCase):
    def _opp(self, amount=1000, actor="r1"):
        c = make_crm()
        lid = qualified_lead(c, "a@x.io", actor)
        return c, c.convert(lid, amount, actor)

    def test_pct_validation(self):
        c, oid = self._opp()
        for bad in [0, 31, -1, True, 1.5, "10", None]:
            with self.assertRaises(ValueError, msg=repr(bad)):
                c.discount(oid, bad, "r1")
        self.assertEqual(c.opps[oid]["amount"], 1000)

    def test_rep_limit_ten(self):
        c, oid = self._opp()
        with self.assertRaises(PermissionError):
            c.discount(oid, 11, "r1")
        c.discount(oid, 10, "r1")
        self.assertEqual(c.opps[oid]["amount"], 900)
        self.assertEqual(c.log[-1], ("discount", "O1", "r1"))
        with self.assertRaises(PermissionError):
            c.discount(oid, 30, "r2")  # non-owner rep

    def test_manager_cumulative_floor(self):
        c, oid = self._opp(amount=1000)
        c.discount(oid, 30, "m1")  # 700 = exactly 70% of original
        self.assertEqual(c.opps[oid]["amount"], 700)
        with self.assertRaises(ValueError):  # 700*99//100=693 < 70% of 1000
            c.discount(oid, 1, "m1")
        self.assertEqual(c.opps[oid]["amount"], 700)

    def test_final_stage_rejected(self):
        c, oid = self._opp()
        with self.assertRaises(PermissionError):
            c.discount(oid, 5, "r2")  # permission checked before stage
        for s in ["proposal", "negotiation", "won"]:
            c.advance(oid, s, "r1")
        with self.assertRaises(ValueError):
            c.discount(oid, 5, "r1")


class TestTransfer(unittest.TestCase):
    def test_success_moves_ownership_and_logs(self):
        c = crm_caps(2, 2)
        a = qualified_lead(c, "a@x.io", "m1")  # -> r1
        oid = c.convert(a, 100, "m1")  # O1 owned by r1, r1 load 1
        c.transfer(oid, "r2", "m1")
        self.assertEqual(c.opps[oid]["owner"], "r2")
        self.assertEqual(c.log[-1], ("transfer", oid, "m1"))
        self.assertEqual(c._load("r1"), 0)
        self.assertEqual(c._load("r2"), 1)

    def test_failures_leave_state_untouched(self):
        c = crm_caps(1, 1)
        a = qualified_lead(c, "a@x.io", "m1")  # r1
        b = qualified_lead(c, "b@x.io", "m1")  # r2 (at capacity)
        oid = c.convert(a, 100, "m1")
        log_len = len(c.log)
        with self.assertRaises(PermissionError):
            c.transfer(oid, "r2", "r1")  # actor must be manager
        with self.assertRaises(ValueError):
            c.transfer("NOPE", "r2", "m1")  # unknown opp
        with self.assertRaises(ValueError):
            c.transfer(oid, "m1", "m1")  # target must be rep
        with self.assertRaises(ValueError):
            c.transfer(oid, "ghost", "m1")  # unknown target user
        with self.assertRaises(ValueError):
            c.transfer(oid, "r1", "m1")  # same owner
        with self.assertRaises(ValueError):
            c.transfer(oid, "r2", "m1")  # r2 at capacity
        self.assertEqual(c.opps[oid]["owner"], "r1")
        self.assertEqual(len(c.log), log_len)

    def test_final_stage_rejected_before_target_checks(self):
        c = crm_caps(2, 2)
        a = qualified_lead(c, "a@x.io", "m1")
        oid = c.convert(a, 100, "m1")
        for s in ["proposal", "negotiation", "won"]:
            c.advance(oid, s, "m1")
        with self.assertRaises(ValueError):
            c.transfer(oid, "ghost2", "m1")  # stage check (4) before owner checks


class TestForecast(unittest.TestCase):
    def test_forecast_math_and_no_side_effects(self):
        c = crm_caps(10, 10)
        amounts = {}
        for i, (stage_stop, amt) in enumerate(
            [([], 1000), (["proposal"], 2000), (["proposal", "negotiation"], 10000),
             (["proposal", "negotiation", "won"], 5000),
             (["lost"], 3000)], start=1):
            lid = qualified_lead(c, "l%d@x.io" % i, "m1")
            oid = c.convert(lid, amt, "m1")
            amounts[oid] = amt
            for s in stage_stop:
                c.advance(oid, s, "m1")
        before = list(c.log)
        f = c.forecast()
        self.assertEqual(f, {"open": 3,
                             "weighted": 100 + 600 + 6000,
                             "won": 5000})
        self.assertEqual(c.log, before)  # forecast logs nothing

    def test_discount_affects_weighted(self):
        c = crm_caps(5, 5)
        lid = qualified_lead(c, "a@x.io", "m1")
        oid = c.convert(lid, 2000, "m1")
        c.discount(oid, 10, "m1")  # 1800
        self.assertEqual(c.forecast()["weighted"], 1800 * 10 // 100)


if __name__ == "__main__":
    unittest.main()
