"""Unit tests for crm.py: advance, discount, transfer, forecast, logging."""

import unittest

from crm import CRM


def make_crm(r1_cap=1, r2_cap=1):
    return CRM([
        {"id": "r1", "role": "rep", "capacity": r1_cap},
        {"id": "r2", "role": "rep", "capacity": r2_cap},
        {"id": "m1", "role": "manager", "capacity": 0},
    ])


class AdvanceFixtureMixin(object):
    """Helpers to build CRMs with an open opportunity owned by a rep."""

    def crm_with_opp(self, amount=1000, r1_cap=2, r2_cap=2):
        """Returns (crm, opp_id). L1 is qualified by r1 and converted.

        Score 30 (referral + gmail). L2 -> r2 (new)."""
        crm = make_crm(r1_cap=r1_cap, r2_cap=r2_cap)
        crm.add_lead("a@gmail.com", "A", "referral", "m1")
        crm.add_lead("b@yahoo.com", "B", "referral", "m1")
        crm.qualify("L1", "r1")
        opp_id = crm.convert("L1", amount, "r1")
        return crm, opp_id


class TestAdvance(AdvanceFixtureMixin, unittest.TestCase):
    def test_stepwise_progression(self):
        crm, opp_id = self.crm_with_opp()
        crm.advance(opp_id, "proposal", "r1")
        crm.advance(opp_id, "negotiation", "r1")
        crm.advance(opp_id, "won", "r1")
        self.assertEqual(crm.opps[opp_id]["stage"], "won")
        self.assertEqual(
            [entry[0] for entry in crm.log[-3:]],
            ["advance", "advance", "advance"],
        )
        self.assertEqual(crm.log[-1], ("advance", "O1", "r1"))

    def test_lost_allowed_from_any_nonfinal_stage(self):
        crm, opp_id = self.crm_with_opp()
        crm.advance(opp_id, "lost", "r1")
        self.assertEqual(crm.opps[opp_id]["stage"], "lost")
        crm2, opp2 = self.crm_with_opp()
        crm2.advance(opp2, "proposal", "r1")
        crm2.advance(opp2, "lost", "r1")
        self.assertEqual(crm2.opps[opp2]["stage"], "lost")

    def test_unknown_opportunity(self):
        crm = make_crm()
        with self.assertRaises(ValueError):
            crm.advance("O9", "proposal", "r1")

    def test_unknown_actor_first(self):
        crm = make_crm()
        with self.assertRaises(PermissionError):
            crm.advance("O9", "nope", "ghost")

    def test_invalid_stage_values(self):
        crm, opp_id = self.crm_with_opp()
        for stage in ("PROPOSAL", "final", "", None, 3):
            with self.subTest(stage=stage):
                with self.assertRaises(ValueError):
                    crm.advance(opp_id, stage, "r1")

    def test_only_owner_or_manager(self):
        crm, opp_id = self.crm_with_opp()
        # r2 is not r1 (owner) and not a manager
        crm = make_crm()  # fresh: use new CRM to avoid interfering loads
        crm.add_lead("a@gmail.com", "A", "referral", "m1")
        crm.add_lead("b@yahoo.com", "B", "referral", "m1")
        crm.qualify("L1", "r1")
        opp = crm.convert("L1", 1000, "r1")
        with self.assertRaises(PermissionError):
            crm.advance(opp, "proposal", "r2")
        crm.advance(opp, "proposal", "m1")
        self.assertEqual(crm.opps[opp]["stage"], "proposal")

    def test_final_stage_rejected(self):
        crm, opp_id = self.crm_with_opp()
        crm.advance(opp_id, "lost", "r1")
        with self.assertRaises(ValueError):
            crm.advance(opp_id, "proposal", "r1")

    def test_permission_beats_final_stage_check(self):
        crm, opp_id = self.crm_with_opp()
        crm.advance(opp_id, "lost", "r1")
        with self.assertRaises(PermissionError):
            crm.advance(opp_id, "proposal", "r2")

    def test_stage_skips_rejected(self):
        crm, opp_id = self.crm_with_opp()
        for bad in ("negotiation", "won", "prospect", "lost"):
            # prospect->negotiation (skip), ->won (skip), ->prospect (no-op)
            with self.subTest(bad=bad):
                fresh_crm, fresh_opp = self.crm_with_opp()
                if bad == "lost":
                    continue  # lost is allowed from prospect
                with self.assertRaises(ValueError):
                    fresh_crm.advance(fresh_opp, bad, "r1")

    def test_backwards_move_rejected(self):
        crm, opp_id = self.crm_with_opp()
        crm.advance(opp_id, "proposal", "r1")
        with self.assertRaises(ValueError):
            crm.advance(opp_id, "prospect", "r1")

    def test_negotiation_above_50000_requires_manager(self):
        crm, opp_id = self.crm_with_opp(amount=60000, r1_cap=2, r2_cap=2)
        crm.advance(opp_id, "proposal", "r1")
        with self.assertRaises(PermissionError):
            crm.advance(opp_id, "negotiation", "r1")
        crm.advance(opp_id, "negotiation", "m1")
        self.assertEqual(crm.opps[opp_id]["stage"], "negotiation")

    def test_negotiation_at_50000_allows_rep(self):
        crm, opp_id = self.crm_with_opp(amount=50000)
        crm.advance(opp_id, "proposal", "r1")
        crm.advance(opp_id, "negotiation", "r1")

    def test_won_frees_slot_and_assigns_waiting_lead(self):
        # r1 cap 1: L1 -> r1, L2 -> r2, L3 queued.
        crm = make_crm(r1_cap=1, r2_cap=1)
        crm.add_lead("a@gmail.com", "A", "referral", "m1")
        crm.add_lead("b@yahoo.com", "B", "referral", "m1")
        crm.add_lead("c@ok.com", "C", "referral", "m1")
        self.assertIsNone(crm.leads["L3"]["owner"])
        crm.qualify("L1", "r1")
        opp_id = crm.convert("L1", 1000, "r1")
        for stage in ("proposal", "negotiation", "won"):
            crm.advance(opp_id, stage, "r1")  # amount 1000 -> no manager needed
        self.assertEqual(crm.leads["L3"]["owner"], "r1")
        self.assertEqual(crm.log[-2], ("advance", "O1", "r1"))
        self.assertEqual(crm.log[-1], ("assign", "L3", "system"))

    def test_assignment_loop_stops_at_capacity(self):
        # r1 cap 2, r2 cap 1.
        # L1 -> r1, L2 -> r2 (full), L3 -> r1, L4 queued, L5 queued.
        crm = make_crm(r1_cap=2, r2_cap=1)
        for i in range(5):
            crm.add_lead("p%d@gmail.com" % i, "P%d" % i, "referral", "m1")
        self.assertIsNone(crm.leads["L4"]["owner"])
        self.assertIsNone(crm.leads["L5"]["owner"])
        crm.qualify("L1", "r1")
        opp_id = crm.convert("L1", 1000, "r1")
        for stage in ("proposal", "negotiation", "won"):
            crm.advance(opp_id, stage, "r1")
        # r1 load after won: L3 (new) = 1 < 2 -> assign L4 (load 2 -> stop)
        self.assertEqual(crm.leads["L4"]["owner"], "r1")
        self.assertIsNone(crm.leads["L5"]["owner"])
        self.assertEqual(crm.log[-2], ("advance", "O1", "r1"))
        self.assertEqual(crm.log[-1], ("assign", "L4", "system"))

    def test_lost_frees_slot_too(self):
        crm = make_crm(r1_cap=1, r2_cap=1)
        crm.add_lead("a@gmail.com", "A", "referral", "m1")
        crm.add_lead("b@yahoo.com", "B", "referral", "m1")
        crm.add_lead("c@ok.com", "C", "referral", "m1")
        crm.qualify("L1", "r1")
        opp_id = crm.convert("L1", 1000, "r1")
        crm.advance(opp_id, "lost", "r1")
        self.assertEqual(crm.leads["L3"]["owner"], "r1")
        self.assertEqual(crm.log[-1], ("assign", "L3", "system"))

    def test_won_without_waiting_queue_appends_no_assign(self):
        crm, opp_id = self.crm_with_opp(amount=1000)
        before = list(crm.log)
        crm.advance(opp_id, "proposal", "r1")
        crm.advance(opp_id, "negotiation", "r1")
        crm.advance(opp_id, "won", "r1")
        for entry in crm.log[len(before):]:
            self.assertEqual(entry[0], "advance")

    def test_failed_advance_changes_nothing(self):
        crm, opp_id = self.crm_with_opp()
        before_log = list(crm.log)
        before_stage = crm.opps[opp_id]["stage"]
        with self.assertRaises(ValueError):
            crm.advance(opp_id, "negotiation", "r1")
        self.assertEqual(crm.log, before_log)
        self.assertEqual(crm.opps[opp_id]["stage"], before_stage)


class TestDiscount(AdvanceFixtureMixin, unittest.TestCase):
    def test_success_reduces_amount_and_logs(self):
        crm, opp_id = self.crm_with_opp(amount=1000)
        crm.discount(opp_id, 20, "m1")
        self.assertEqual(crm.opps[opp_id]["amount"], 800)
        self.assertEqual(crm.opps[opp_id]["original_amount"], 1000)
        self.assertEqual(crm.log[-1], ("discount", "O1", "m1"))

    def test_unknown_opportunity(self):
        crm = make_crm()
        with self.assertRaises(ValueError):
            crm.discount("O9", 10, "r1")

    def test_unknown_actor_first(self):
        crm = make_crm()
        with self.assertRaises(PermissionError):
            crm.discount("O9", 99, "ghost")

    def test_pct_validation(self):
        crm, opp_id = self.crm_with_opp()
        for pct in (0, -1, 31, 100, "10", 10.0, None, True, False):
            with self.subTest(pct=pct):
                with self.assertRaises(ValueError):
                    crm.discount(opp_id, pct, "r1")

    def test_owner_or_manager_required(self):
        crm, opp_id = self.crm_with_opp()
        with self.assertRaises(PermissionError):
            crm.discount(opp_id, 5, "r2")

    def test_final_stage_rejected(self):
        crm, opp_id = self.crm_with_opp()
        crm.advance(opp_id, "lost", "r1")
        with self.assertRaises(ValueError):
            crm.discount(opp_id, 10, "m1")

    def test_permission_beats_final_stage_check(self):
        crm, opp_id = self.crm_with_opp()
        crm.advance(opp_id, "lost", "r1")
        with self.assertRaises(PermissionError):
            crm.discount(opp_id, 10, "r2")

    def test_non_manager_limited_to_10(self):
        crm, opp_id = self.crm_with_opp(amount=1000)
        with self.assertRaises(PermissionError):
            crm.discount(opp_id, 11, "r1")
        crm.discount(opp_id, 10, "r1")  # rep may use exactly 10
        self.assertEqual(crm.opps[opp_id]["amount"], 900)
        crm.discount(opp_id, 10, "m1")  # cumulative 19%, still allowed
        self.assertEqual(crm.opps[opp_id]["amount"], 810)
        crm2, opp2 = self.crm_with_opp(amount=1000)
        crm2.discount(opp2, 30, "m1")  # manager may use up to 30
        self.assertEqual(crm2.opps[opp2]["amount"], 700)

    def test_non_manager_limit_beats_cumulative_cap(self):
        crm, opp_id = self.crm_with_opp(amount=1000)
        crm.discount(opp_id, 10, "r1")   # 900
        crm.discount(opp_id, 10, "r1")   # 810
        crm.discount(opp_id, 10, "r1")   # 729 -> 70% floor breached
        with self.assertRaises(PermissionError):
            crm.discount(opp_id, 30, "r1")  # check 5 fires before check 6
        self.assertEqual(crm.opps[opp_id]["amount"], 729)
        crm.discount(opp_id, 3, "m1")   # 729*97//100 = 707 -> at the floor
        self.assertEqual(crm.opps[opp_id]["amount"], 707)

    def test_cumulative_discount_floor(self):
        crm, opp_id = self.crm_with_opp(amount=1000)
        crm.discount(opp_id, 20, "m1")   # 800; 80000 >= 70000 OK
        with self.assertRaises(ValueError):
            crm.discount(opp_id, 20, "m1")  # 640 -> 64000 < 70000
        self.assertEqual(crm.opps[opp_id]["amount"], 800)
        crm.discount(opp_id, 5, "m1")    # 760 OK
        self.assertEqual(crm.opps[opp_id]["amount"], 760)
        with self.assertRaises(ValueError):
            crm.discount(opp_id, 10, "m1")  # 684 -> < 70000
        self.assertEqual(crm.opps[opp_id]["amount"], 760)

    def test_exactly_30_percent_allowed(self):
        crm, opp_id = self.crm_with_opp(amount=1000)
        crm.discount(opp_id, 30, "m1")
        self.assertEqual(crm.opps[opp_id]["amount"], 700)

    def test_floor_uses_integer_division(self):
        crm, opp_id = self.crm_with_opp(amount=999)
        crm.discount(opp_id, 10, "m1")
        self.assertEqual(crm.opps[opp_id]["amount"], 999 * 90 // 100)  # 899

    def test_owner_rep_allowed_up_to_10(self):
        crm, opp_id = self.crm_with_opp(amount=10000)
        crm.discount(opp_id, 10, "r1")
        self.assertEqual(crm.opps[opp_id]["amount"], 9000)


class TestTransfer(AdvanceFixtureMixin, unittest.TestCase):
    def test_success_transfers_and_logs(self):
        crm, opp_id = self.crm_with_opp(r1_cap=2, r2_cap=2)
        crm.transfer(opp_id, "r2", "m1")
        self.assertEqual(crm.opps[opp_id]["owner"], "r2")
        self.assertEqual(crm.log[-1], ("transfer", "O1", "m1"))

    def test_unknown_opportunity(self):
        crm = make_crm()
        with self.assertRaises(ValueError):
            crm.transfer("O9", "r2", "m1")

    def test_unknown_actor_first(self):
        crm = make_crm()
        with self.assertRaises(PermissionError):
            crm.transfer("O9", "r2", "ghost")

    def test_only_manager(self):
        crm, opp_id = self.crm_with_opp()
        with self.assertRaises(PermissionError):
            crm.transfer(opp_id, "r2", "r1")

    def test_new_owner_must_be_known_rep(self):
        crm, opp_id = self.crm_with_opp()
        for bad in ("ghost", "m1", None, 42):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    crm.transfer(opp_id, bad, "m1")

    def test_stage_final_rejected(self):
        crm, opp_id = self.crm_with_opp()
        crm.advance(opp_id, "lost", "r1")
        with self.assertRaises(ValueError):
            crm.transfer(opp_id, "r2", "m1")

    def test_new_owner_check_beats_final_stage_check(self):
        crm, opp_id = self.crm_with_opp()
        crm.advance(opp_id, "lost", "r1")
        with self.assertRaises(ValueError):
            crm.transfer(opp_id, "ghost", "m1")

    def test_new_owner_must_differ(self):
        crm, opp_id = self.crm_with_opp()
        with self.assertRaises(ValueError):
            crm.transfer(opp_id, "r1", "m1")

    def test_new_owner_must_have_capacity(self):
        # r2 cap 1 already holds L2 (new) -> full.
        crm, opp_id = self.crm_with_opp(r1_cap=2, r2_cap=1)
        with self.assertRaises(ValueError):
            crm.transfer(opp_id, "r2", "m1")

    def test_transfer_frees_previous_owner_slot(self):
        # r1 cap 2, r2 cap 6.
        # Distribution: L1->r1, L2->r2, L3->r1 (r1 full), L4..L6->r2.
        crm = make_crm(r1_cap=2, r2_cap=6)
        for i in range(6):
            crm.add_lead("p%d@gmail.com" % i, "P%d" % i, "referral", "m1")
        crm.qualify("L1", "r1")
        opp_id = crm.convert("L1", 1000, "r1")
        # r1 load: L3 (new) + O1 (open) = 2 (full). r2 load: L2,L4,L5,L6 = 4.
        # A new lead right now can only be routed to r2 (r1 is full).
        crm.add_lead("probe@acme.io", "Probe", "web", "m1")
        self.assertEqual(crm.leads["L7"]["owner"], "r2")
        crm.transfer(opp_id, "r2", "m1")  # r2: 4 < 6 -> OK
        # Previous owner r1 now holds only L3: load 1 < 2 -> slot freed.
        # The next lead goes to r1 again (lowest load).
        crm.add_lead("probe2@acme.io", "Probe2", "web", "m1")
        self.assertEqual(crm.leads["L8"]["owner"], "r1")
        # The waiting queue was empty, so no "assign" entries were logged.
        self.assertNotIn("assign", [entry[0] for entry in crm.log])
        transfer_entries = [entry for entry in crm.log
                            if entry[0] == "transfer"]
        self.assertEqual(transfer_entries, [("transfer", "O1", "m1")])

    def test_failed_transfer_changes_nothing(self):
        crm, opp_id = self.crm_with_opp(r1_cap=2, r2_cap=2)
        before_log = list(crm.log)
        before_owner = crm.opps[opp_id]["owner"]
        with self.assertRaises(PermissionError):
            crm.transfer(opp_id, "r2", "r1")
        self.assertEqual(crm.opps[opp_id]["owner"], before_owner)
        self.assertEqual(crm.log, before_log)


class TestForecast(unittest.TestCase):
    def test_empty_crm(self):
        crm = make_crm()
        self.assertEqual(crm.forecast(), {"open": 0, "weighted": 0, "won": 0})

    def test_stages_weights_and_won(self):
        crm = make_crm(r1_cap=5, r2_cap=5)
        crm.add_lead("a@gmail.com", "A", "referral", "m1")  # L1 -> r1
        crm.add_lead("b@yahoo.com", "B", "referral", "m1")  # L2 -> r2
        crm.qualify("L1", "r1")
        crm.qualify("L2", "r2")
        o1 = crm.convert("L1", 40000, "r1")   # prospect, weight 10
        o2 = crm.convert("L2", 100000, "r2")  # prospect, weight 10
        crm.discount(o2, 20, "m1")            # amount 80000
        crm.advance(o2, "proposal", "r2")     # weight 30
        self.assertEqual(crm.forecast(),
                         {"open": 2, "weighted": 4000 + 24000, "won": 0})
        crm.advance(o1, "proposal", "r1")
        crm.advance(o1, "negotiation", "r1")  # 40000 <= 50000 -> rep is fine
        self.assertEqual(crm.forecast(),
                         {"open": 2, "weighted": 24000 + 24000, "won": 0})
        crm.advance(o1, "won", "r1")
        self.assertEqual(crm.forecast(),
                         {"open": 1, "weighted": 24000, "won": 40000})

    def test_lost_excluded_everywhere(self):
        crm = make_crm(r1_cap=5, r2_cap=5)
        crm.add_lead("a@gmail.com", "A", "referral", "m1")
        crm.qualify("L1", "r1")
        o1 = crm.convert("L1", 50000, "r1")
        crm.advance(o1, "lost", "r1")
        self.assertEqual(crm.forecast(), {"open": 0, "weighted": 0, "won": 0})

    def test_weighted_integer_division(self):
        crm = make_crm()
        crm.opps["O1"] = {"id": "O1", "lead_id": "L1", "owner": "r1",
                          "amount": 99999, "original_amount": 99999,
                          "stage": "proposal"}
        fc = crm.forecast()
        self.assertEqual(fc["weighted"], 99999 * 30 // 100)
        self.assertEqual(fc["open"], 1)

    def test_forecast_appends_no_log(self):
        crm = make_crm()
        crm.add_lead("a@gmail.com", "A", "referral", "m1")
        before = list(crm.log)
        crm.forecast()
        self.assertEqual(crm.log, before)


class TestLogAtomicity(unittest.TestCase):
    def test_failed_calls_append_nothing(self):
        crm = make_crm(r1_cap=1, r2_cap=1)
        crm.add_lead("a@gmail.com", "A", "referral", "m1")
        crm.add_lead("b@yahoo.com", "B", "referral", "m1")
        crm.add_lead("c@ok.com", "C", "referral", "m1")
        crm.qualify("L1", "r1")
        opp_id = crm.convert("L1", 1000, "r1")
        snapshot = list(crm.log)
        from crm import DuplicateLeadError
        with self.assertRaises(ValueError):
            crm.add_lead("bad-email", "D", "web", "m1")
        with self.assertRaises(PermissionError):
            crm.qualify("L2", "r1")
        with self.assertRaises(PermissionError):
            crm.convert("L2", 1000, "r1")  # L2 is owned by r2
        with self.assertRaises(ValueError):
            crm.advance(opp_id, "negotiation", "r1")
        with self.assertRaises(ValueError):
            crm.discount(opp_id, 0, "r1")
        with self.assertRaises(ValueError):
            crm.transfer(opp_id, "r1", "m1")
        self.assertEqual(crm.log, snapshot)

    def test_log_is_list_of_tuples(self):
        crm = make_crm()
        crm.add_lead("a@gmail.com", "A", "referral", "m1")
        for entry in crm.log:
            self.assertIsInstance(entry, tuple)
            self.assertEqual(len(entry), 3)


if __name__ == "__main__":
    unittest.main()
