import unittest

from crm import CRM


BASE_REPS = [
    {"id": "r1", "role": "rep", "capacity": 50},
    {"id": "r2", "role": "rep", "capacity": 0},
    {"id": "m1", "role": "manager", "capacity": 5},
]


class CRMSalesTests(unittest.TestCase):
    reps = BASE_REPS

    def setUp(self):
        self.crm = CRM([dict(r) for r in self.reps])
        self._seq = 0

    def email(self):
        self._seq += 1
        return "opp%d@corp.com" % self._seq

    def make_opp(self, amount=1000, actor="r1"):
        lid = self.crm.add_lead(self.email(), "Name", "referral", "r1")
        self.crm.qualify(lid, actor)
        return self.crm.convert(lid, amount, actor)

    def advance_to(self, opp, stage, actor="r1"):
        for target in ["proposal", "negotiation", "won"]:
            self.crm.advance(opp, target, actor)
            if target == stage:
                return

    # ----------------------------------------------------------------- advance
    def test_advance_full_flow(self):
        opp = self.make_opp(1000)
        self.crm.advance(opp, "proposal", "r1")
        self.assertEqual(self.crm.opps[opp]["stage"], "proposal")
        self.crm.advance(opp, "negotiation", "r1")
        self.assertEqual(self.crm.opps[opp]["stage"], "negotiation")
        self.crm.advance(opp, "won", "r1")
        self.assertEqual(self.crm.opps[opp]["stage"], "won")
        self.assertEqual(self.crm.log[-3:], [
            ("advance", opp, "r1"), ("advance", opp, "r1"), ("advance", opp, "r1"),
        ])
        self.assertEqual(self.crm.forecast(), {"open": 0, "weighted": 0, "won": 1000})

    def test_advance_lost_is_final(self):
        opp = self.make_opp(1000)
        self.crm.advance(opp, "lost", "r1")
        self.assertEqual(self.crm.opps[opp]["stage"], "lost")
        with self.assertRaises(ValueError):
            self.crm.advance(opp, "proposal", "r1")
        self.assertEqual(self.crm.forecast(), {"open": 0, "weighted": 0, "won": 0})

    def test_advance_rejects_skips_and_bad_stages(self):
        opp = self.make_opp(1000)
        for bad in ["negotiation", "won", "bogus", "PROPOSAL"]:
            with self.subTest(stage=bad):
                with self.assertRaises(ValueError):
                    self.crm.advance(opp, bad, "r1")
        self.assertEqual(self.crm.opps[opp]["stage"], "prospect")
        with self.assertRaises(ValueError):
            self.crm.advance("O404", "proposal", "r1")

    def test_advance_permission_and_final_checks(self):
        opp = self.make_opp(1000)
        with self.assertRaises(PermissionError):
            self.crm.advance(opp, "proposal", "r2")
        self.assertEqual(self.crm.opps[opp]["stage"], "prospect")
        self.crm.advance(opp, "proposal", "r1")
        self.crm.advance(opp, "negotiation", "r1")
        self.crm.advance(opp, "won", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance(opp, "lost", "m1")

    def test_advance_unknown_actor_checked_first(self):
        with self.assertRaises(PermissionError):
            self.crm.advance("O404", "bogus", "ghost")
        self.assertEqual(self.crm.opps, {})

    def test_negotiation_over_50k_requires_manager(self):
        big = self.make_opp(50001)
        self.crm.advance(big, "proposal", "r1")
        with self.assertRaises(PermissionError):
            self.crm.advance(big, "negotiation", "r1")
        self.assertEqual(self.crm.opps[big]["stage"], "proposal")
        self.crm.advance(big, "negotiation", "m1")
        self.assertEqual(self.crm.opps[big]["stage"], "negotiation")

        edge = self.make_opp(50000)
        self.crm.advance(edge, "proposal", "r1")
        self.crm.advance(edge, "negotiation", "r1")
        self.assertEqual(self.crm.opps[edge]["stage"], "negotiation")

    def test_advance_to_final_assigns_waiting_leads_fifo(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 5},
        ])
        l1 = crm.add_lead("l1@corp.com", "L1", "referral", "r1")
        l2 = crm.add_lead("l2@corp.com", "L2", "referral", "r1")
        l3 = crm.add_lead("l3@corp.com", "L3", "referral", "r1")
        l4 = crm.add_lead("l4@corp.com", "L4", "referral", "r1")
        self.assertEqual(crm.leads[l1]["owner"], "r1")
        self.assertEqual(crm.leads[l2]["owner"], "r2")
        self.assertIsNone(crm.leads[l3]["owner"])
        self.assertIsNone(crm.leads[l4]["owner"])

        crm.qualify(l1, "r1")
        opp = crm.convert(l1, 1000, "r1")
        crm.advance(opp, "proposal", "r1")
        crm.advance(opp, "negotiation", "r1")
        crm.advance(opp, "won", "r1")
        self.assertEqual(crm.leads[l3]["owner"], "r1")
        self.assertIsNone(crm.leads[l4]["owner"])
        self.assertEqual(crm.log[-1], ("assign", l3, "system"))

        crm.qualify(l3, "r1")
        opp2 = crm.convert(l3, 1000, "r1")
        crm.advance(opp2, "proposal", "r1")
        crm.advance(opp2, "negotiation", "r1")
        crm.advance(opp2, "lost", "r1")
        self.assertEqual(crm.leads[l4]["owner"], "r1")
        self.assertEqual(crm.log[-1], ("assign", l4, "system"))

    def test_advance_failure_leaves_state_untouched(self):
        opp = self.make_opp(1000)
        log_before = list(self.crm.log)
        with self.assertRaises(ValueError):
            self.crm.advance(opp, "negotiation", "r1")  # skip
        self.assertEqual(self.crm.opps[opp]["stage"], "prospect")
        self.assertEqual(self.crm.log, log_before)

    # ---------------------------------------------------------------- discount
    def test_discount_bounds_and_permissions(self):
        opp = self.make_opp(1000)
        for bad in [0, 31, -5, True, 10.0, "10", None]:
            with self.subTest(pct=bad):
                with self.assertRaises(ValueError):
                    self.crm.discount(opp, bad, "r1")
        with self.assertRaises(PermissionError):
            self.crm.discount(opp, 10, "r2")
        with self.assertRaises(PermissionError):
            self.crm.discount(opp, 11, "r1")
        self.assertEqual(self.crm.opps[opp]["amount"], 1000)

        self.crm.discount(opp, 10, "r1")
        self.assertEqual(self.crm.opps[opp]["amount"], 900)
        self.crm.discount(opp, 20, "m1")
        self.assertEqual(self.crm.opps[opp]["amount"], 720)
        self.assertEqual(self.crm.log[-1], ("discount", opp, "m1"))

    def test_discount_cumulative_cap(self):
        opp = self.make_opp(1000)
        for _ in range(3):
            self.crm.discount(opp, 10, "r1")
        self.assertEqual(self.crm.opps[opp]["amount"], 729)
        with self.assertRaises(ValueError):
            self.crm.discount(opp, 10, "r1")
        self.assertEqual(self.crm.opps[opp]["amount"], 729)

        manager_opp = self.make_opp(1000)
        self.crm.discount(manager_opp, 30, "m1")
        self.assertEqual(self.crm.opps[manager_opp]["amount"], 700)
        with self.assertRaises(ValueError):
            self.crm.discount(manager_opp, 30, "m1")
        self.assertEqual(self.crm.opps[manager_opp]["amount"], 700)

    def test_discount_uses_floor_and_original_amount(self):
        opp = self.make_opp(999)
        self.crm.discount(opp, 10, "r1")
        self.assertEqual(self.crm.opps[opp]["amount"], 899)
        self.assertEqual(self.crm.opps[opp]["original_amount"], 999)
        self.crm.discount(opp, 22, "m1")
        self.assertEqual(self.crm.opps[opp]["amount"], 899 * 78 // 100)

    def test_discount_rejects_final_stage_and_unknown(self):
        opp = self.make_opp(1000)
        self.advance_to(opp, "won")
        with self.assertRaises(ValueError):
            self.crm.discount(opp, 5, "m1")
        self.assertEqual(self.crm.opps[opp]["amount"], 1000)
        with self.assertRaises(ValueError):
            self.crm.discount("O404", 5, "m1")

    def test_discount_cumulative_cap_respected_around_threshold(self):
        opp = self.make_opp(1000)
        self.crm.discount(opp, 30, "m1")  # 700
        with self.assertRaises(ValueError):
            self.crm.discount(opp, 1, "m1")  # 693 < 700
        self.assertEqual(self.crm.opps[opp]["amount"], 700)

    # ---------------------------------------------------------------- transfer
    def test_transfer_happy_path(self):
        self.crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 5},
            {"id": "r2", "role": "rep", "capacity": 5},
            {"id": "m1", "role": "manager", "capacity": 5},
        ])
        opp = self.make_opp(1000)
        self.crm.transfer(opp, "r2", "m1")
        self.assertEqual(self.crm.opps[opp]["owner"], "r2")
        self.assertEqual(self.crm.log[-1], ("transfer", opp, "m1"))

    def test_transfer_validation(self):
        opp = self.make_opp(1000)
        with self.assertRaises(PermissionError):
            self.crm.transfer(opp, "r2", "r1")
        with self.assertRaises(ValueError):
            self.crm.transfer(opp, "m1", "m1")
        with self.assertRaises(ValueError):
            self.crm.transfer(opp, "nobody", "m1")
        with self.assertRaises(ValueError):
            self.crm.transfer(opp, "r1", "m1")
        with self.assertRaises(ValueError):
            self.crm.transfer("O404", "r2", "m1")
        self.assertEqual(self.crm.opps[opp]["owner"], "r1")

    def test_transfer_requires_capacity_on_new_owner(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 5},
        ])
        l1 = crm.add_lead("a@corp.com", "A", "referral", "r1")
        crm.add_lead("b@corp.com", "B", "referral", "r1")
        crm.qualify(l1, "r1")
        opp = crm.convert(l1, 1000, "r1")
        with self.assertRaises(ValueError):
            crm.transfer(opp, "r2", "m1")
        self.assertEqual(crm.opps[opp]["owner"], "r1")

    def test_transfer_rejects_final_stage(self):
        self.crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 5},
            {"id": "r2", "role": "rep", "capacity": 5},
            {"id": "m1", "role": "manager", "capacity": 5},
        ])
        opp = self.make_opp(1000)
        self.advance_to(opp, "won")
        with self.assertRaises(ValueError):
            self.crm.transfer(opp, "r2", "m1")
        self.assertEqual(self.crm.opps[opp]["owner"], "r1")

    def test_transfer_unknown_actor_checked_first(self):
        with self.assertRaises(PermissionError):
            self.crm.transfer("O404", "nobody", "ghost")

    # ---------------------------------------------------------------- forecast
    def test_forecast_weighting_and_won(self):
        p = self.make_opp(1000)
        prop = self.make_opp(2000)
        neg = self.make_opp(5000)
        won = self.make_opp(4000)
        lost = self.make_opp(3000)
        self.crm.advance(prop, "proposal", "r1")
        self.crm.advance(neg, "proposal", "r1")
        self.crm.advance(neg, "negotiation", "r1")
        self.advance_to(won, "won")
        self.crm.advance(lost, "lost", "r1")

        log_before = list(self.crm.log)
        self.assertEqual(self.crm.forecast(), {
            "open": 3, "weighted": 100 + 600 + 3000, "won": 4000,
        })
        self.assertEqual(self.crm.log, log_before)

    def test_forecast_rounds_down(self):
        opp = self.make_opp(999)
        self.crm.advance(opp, "proposal", "r1")  # 999 * 30 // 100 == 299
        self.assertEqual(self.crm.forecast()["weighted"], 299)

    def test_forecast_empty(self):
        self.assertEqual(self.crm.forecast(), {"open": 0, "weighted": 0, "won": 0})

    # -------------------------------------------------------------------- log
    def test_log_sequence_has_no_extra_entries(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 2},
            {"id": "r2", "role": "rep", "capacity": 2},
            {"id": "m1", "role": "manager", "capacity": 5},
        ])
        lid = crm.add_lead("log@corp.com", "Log", "referral", "r1")
        crm.qualify(lid, "r1")
        opp = crm.convert(lid, 1000, "r1")
        crm.advance(opp, "proposal", "r1")
        crm.discount(opp, 10, "r1")
        crm.transfer(opp, "r2", "m1")
        self.assertEqual(crm.log, [
            ("add_lead", lid, "r1"),
            ("qualify", lid, "r1"),
            ("convert", opp, "r1"),
            ("advance", opp, "r1"),
            ("discount", opp, "r1"),
            ("transfer", opp, "m1"),
        ])
        for entry in crm.log:
            self.assertIsInstance(entry, tuple)
            self.assertEqual(len(entry), 3)


if __name__ == "__main__":
    unittest.main()
