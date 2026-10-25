"""Tests for CRM opportunities: advance, discount, transfer, forecast."""

import unittest

from crm import CRM


def opp_crm(r1_cap=1, r2_cap=1):
    """CRM where L1 is a qualified referral lead owned by r1, converted to O1.

    Returns (crm, opp_id, waiting_ids_info). L1 -> r1, L2 -> r2, L3 -> queue.
    """
    crm = CRM([
        {"id": "r1", "role": "rep", "capacity": r1_cap},
        {"id": "r2", "role": "rep", "capacity": r2_cap},
        {"id": "m", "role": "manager", "capacity": 5},
    ])
    l1 = crm.add_lead("a@acme.com", "A", "referral", "m")
    crm.qualify(l1, "r1")
    oid = crm.convert(l1, 1000, "r1")
    return crm, oid


class TestAdvance(unittest.TestCase):
    def setUp(self):
        self.crm, self.oid = opp_crm()
        self.crm.log = []  # ignore setup entries for clarity

    def test_happy_path_through_stages(self):
        self.crm.advance(self.oid, "proposal", "r1")
        self.crm.advance(self.oid, "negotiation", "r1")
        self.crm.advance(self.oid, "won", "r1")
        self.assertEqual(self.crm.opps[self.oid]["stage"], "won")
        self.assertEqual(self.crm.log, [
            ("advance", self.oid, "r1"),
            ("advance", self.oid, "r1"),
            ("advance", self.oid, "r1"),
        ])

    def test_manager_can_advance(self):
        self.crm.advance(self.oid, "proposal", "m")
        self.assertEqual(self.crm.opps[self.oid]["stage"], "proposal")

    def test_opp_must_exist(self):
        with self.assertRaises(ValueError):
            self.crm.advance("O99", "proposal", "r1")

    def test_stage_must_be_known(self):
        for bad in ("closed", "PROPOSAL", "", None, 3):
            with self.assertRaises(ValueError):
                self.crm.advance(self.oid, bad, "r1")
        self.assertEqual(self.crm.opps[self.oid]["stage"], "prospect")
        self.assertEqual(self.crm.log, [])

    def test_only_owner_or_manager(self):
        with self.assertRaises(PermissionError):
            self.crm.advance(self.oid, "proposal", "r2")

    def test_stage_validity_checked_before_actor(self):
        with self.assertRaises(ValueError):  # r2 is not owner, but bad stage wins
            self.crm.advance(self.oid, "bogus", "r2")

    def test_final_stages_are_frozen(self):
        self.crm.advance(self.oid, "lost", "r1")
        self.crm.log = []
        for stage in ("won", "lost", "proposal"):
            with self.assertRaises(ValueError):
                self.crm.advance(self.oid, stage, "m")
        self.assertEqual(self.crm.log, [])

    def test_must_move_to_immediate_next(self):
        for bad in ("prospect", "negotiation", "won"):
            with self.assertRaises(ValueError):
                self.crm.advance(self.oid, bad, "r1")
        self.crm.advance(self.oid, "proposal", "r1")
        with self.assertRaises(ValueError):  # backwards
            self.crm.advance(self.oid, "prospect", "r1")
        with self.assertRaises(ValueError):  # skipping
            self.crm.advance(self.oid, "won", "r1")

    def test_lost_allowed_from_any_nonfinal(self):
        for stage in ("prospect", "proposal", "negotiation"):
            crm, oid = opp_crm()
            if stage == "proposal":
                crm.advance(oid, "proposal", "r1")
            elif stage == "negotiation":
                crm.advance(oid, "proposal", "r1")
                crm.advance(oid, "negotiation", "r1")
            crm.advance(oid, "lost", "r1")
            self.assertEqual(crm.opps[oid]["stage"], "lost")

    def test_negotiation_over_50k_needs_manager(self):
        crm, oid = opp_crm()
        crm.opps[oid]["amount"] = 60000  # simulate a big deal
        crm.advance(oid, "proposal", "r1")
        with self.assertRaises(PermissionError):
            crm.advance(oid, "negotiation", "r1")
        crm.advance(oid, "negotiation", "m")  # manager fine
        self.assertEqual(crm.opps[oid]["stage"], "negotiation")

    def test_negotiation_at_exactly_50k_allowed_for_rep(self):
        crm, oid = opp_crm()
        crm.opps[oid]["amount"] = 50000
        crm.advance(oid, "proposal", "r1")
        crm.advance(oid, "negotiation", "r1")
        self.assertEqual(crm.opps[oid]["stage"], "negotiation")

    def test_next_stage_rule_before_manager_rule(self):
        crm, oid = opp_crm()
        crm.opps[oid]["amount"] = 60000
        # prospect -> negotiation is not the immediate next stage: ValueError,
        # even though the manager rule would say PermissionError
        with self.assertRaises(ValueError):
            crm.advance(oid, "negotiation", "r1")

    def test_won_frees_slot_and_assigns_oldest_waiting(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "m", "role": "manager", "capacity": 5},
        ])
        l1 = crm.add_lead("a@acme.com", "A", "referral", "m")   # -> r1
        l2 = crm.add_lead("b@acme.com", "B", "referral", "m")   # waiting (oldest)
        l3 = crm.add_lead("c@acme.com", "C", "web", "m")        # waiting
        crm.qualify(l1, "m")
        oid = crm.convert(l1, 1000, "m")
        crm.advance(oid, "proposal", "m")
        crm.advance(oid, "negotiation", "m")
        crm.log = []
        crm.advance(oid, "won", "m")
        self.assertEqual(crm.log, [
            ("advance", oid, "m"),
            ("assign", l2, "system"),  # only one slot: oldest waiting lead
        ])
        self.assertEqual(crm.leads[l2]["owner"], "r1")
        self.assertEqual(crm.leads[l2]["status"], "new")  # assignment only
        self.assertIsNone(crm.leads[l3]["owner"])

    def test_slot_release_fills_multiple_free_spaces(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 3},
            {"id": "m", "role": "manager", "capacity": 5},
        ])
        l1 = crm.add_lead("a@acme.com", "A", "referral", "m")  # r1
        l2 = crm.add_lead("b@acme.com", "B", "referral", "m")  # r1
        crm.add_lead("c@acme.com", "C", "web", "m")            # r1 full? no: cap3
        # loads now 3 -> next waits
        w1 = crm.add_lead("d@acme.com", "D", "web", "m")
        w2 = crm.add_lead("e@acme.com", "E", "web", "m")
        self.assertIsNone(crm.leads[w1]["owner"])
        crm.qualify(l1, "m")
        oid = crm.convert(l1, 1000, "m")  # converted lead frees a slot? lead
        # status converted no longer counts, opp counts: load stays 3
        crm.advance(oid, "proposal", "m")
        crm.advance(oid, "negotiation", "m")
        crm.log = []
        crm.advance(oid, "won", "m")  # load 2 < cap 3 -> assign oldest waiting
        self.assertEqual(crm.log, [
            ("advance", oid, "m"),
            ("assign", w1, "system"),
        ])  # after assign load back to 3 -> stop
        self.assertEqual(crm.leads[w1]["owner"], "r1")
        self.assertIsNone(crm.leads[w2]["owner"])

    def test_lost_also_frees_slot(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "m", "role": "manager", "capacity": 5},
        ])
        l1 = crm.add_lead("a@acme.com", "A", "referral", "m")
        l2 = crm.add_lead("b@acme.com", "B", "referral", "m")
        crm.qualify(l1, "m")
        oid = crm.convert(l1, 1000, "m")
        crm.advance(oid, "lost", "r1")
        self.assertEqual(crm.leads[l2]["owner"], "r1")

    def test_failed_advance_changes_nothing(self):
        with self.assertRaises(PermissionError):
            self.crm.advance(self.oid, "proposal", "r2")
        self.assertEqual(self.crm.opps[self.oid]["stage"], "prospect")
        self.assertEqual(self.crm.log, [])


class TestDiscount(unittest.TestCase):
    def setUp(self):
        self.crm, self.oid = opp_crm()
        self.crm.opps[self.oid]["amount"] = 10000
        self.crm.opps[self.oid]["original_amount"] = 10000
        self.crm.log = []

    def test_rep_up_to_10(self):
        self.crm.discount(self.oid, 10, "r1")
        self.assertEqual(self.crm.opps[self.oid]["amount"], 9000)
        self.assertEqual(self.crm.log, [("discount", self.oid, "r1")])

    def test_rep_over_10_denied(self):
        with self.assertRaises(PermissionError):
            self.crm.discount(self.oid, 11, "r1")
        self.assertEqual(self.crm.opps[self.oid]["amount"], 10000)
        self.assertEqual(self.crm.log, [])

    def test_manager_up_to_30(self):
        self.crm.discount(self.oid, 30, "m")
        self.assertEqual(self.crm.opps[self.oid]["amount"], 7000)

    def test_pct_range(self):
        for bad in (0, 31, -1, 100):
            with self.assertRaises(ValueError):
                self.crm.discount(self.oid, bad, "m")

    def test_pct_type(self):
        for bad in (10.5, "10", None, True, False):
            with self.assertRaises(ValueError):
                self.crm.discount(self.oid, bad, "m")

    def test_actor_must_be_owner_or_manager(self):
        with self.assertRaises(PermissionError):
            self.crm.discount(self.oid, 5, "r2")

    def test_final_stage_denied(self):
        self.crm.discount(self.oid, 5, "r1")
        self.crm.advance(self.oid, "proposal", "r1")
        self.crm.advance(self.oid, "negotiation", "r1")
        self.crm.advance(self.oid, "won", "r1")
        self.crm.log = []
        with self.assertRaises(ValueError):
            self.crm.discount(self.oid, 5, "m")

    def test_cumulative_cap_30_percent(self):
        self.crm.discount(self.oid, 20, "m")  # -> 8000
        with self.assertRaises(ValueError):    # 8000-30%=5600 < 7000
            self.crm.discount(self.oid, 30, "m")
        self.assertEqual(self.crm.opps[self.oid]["amount"], 8000)
        self.crm.discount(self.oid, 12, "m")   # 8000 -> 7040 >= 7000 OK
        self.assertEqual(self.crm.opps[self.oid]["amount"], 7040)
        with self.assertRaises(ValueError):    # 1% more: 6969 < 7000
            self.crm.discount(self.oid, 1, "m")

    def test_floor_division_at_the_boundary(self):
        self.crm.opps[self.oid]["amount"] = 1030
        self.crm.opps[self.oid]["original_amount"] = 1030
        # 1030 * 90 // 100 = 927; 927*100=92700 >= 1030*70=72100 -> OK
        self.crm.discount(self.oid, 10, "r1")
        self.assertEqual(self.crm.opps[self.oid]["amount"], 927)

    def test_boundary_exact_equality_allowed(self):
        # 700000 >= 700000 passes for 10000 at 30%
        self.crm.discount(self.oid, 30, "m")
        self.assertEqual(self.crm.opps[self.oid]["amount"], 7000)

    def test_opp_must_exist(self):
        with self.assertRaises(ValueError):
            self.crm.discount("O42", 5, "m")

    def test_permission_checked_before_stage(self):
        self.crm.advance(self.oid, "proposal", "r1")
        self.crm.advance(self.oid, "negotiation", "r1")
        self.crm.advance(self.oid, "won", "r1")
        with self.assertRaises(PermissionError):  # r2 outsider: not ValueError
            self.crm.discount(self.oid, 5, "r2")


class TestTransfer(unittest.TestCase):
    def setUp(self):
        self.crm, self.oid = opp_crm()
        self.crm.log = []

    def test_manager_transfers(self):
        self.crm.transfer(self.oid, "r2", "m")
        self.assertEqual(self.crm.opps[self.oid]["owner"], "r2")
        self.assertEqual(self.crm.log, [("transfer", self.oid, "m")])

    def test_only_manager_actor(self):
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.oid, "r2", "r1")  # current owner is not mgr
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.oid, "r2", "r2")

    def test_new_owner_must_be_rep(self):
        with self.assertRaises(ValueError):
            self.crm.transfer(self.oid, "m", "m")  # manager can't own
        with self.assertRaises(ValueError):
            self.crm.transfer(self.oid, "ghost", "m")
        with self.assertRaises(ValueError):
            self.crm.transfer(self.oid, 7, "m")

    def test_final_stage_denied(self):
        self.crm.advance(self.oid, "lost", "r1")
        self.crm.log = []
        with self.assertRaises(ValueError):
            self.crm.transfer(self.oid, "r2", "m")

    def test_same_owner_denied(self):
        with self.assertRaises(ValueError):
            self.crm.transfer(self.oid, "r1", "m")

    def test_capacity_denied(self):
        # r2 (cap 1) gets a lead first, so it is at capacity
        self.crm.add_lead("z@acme.com", "Z", "web", "m")  # r1 full -> r2
        self.crm.log = []
        with self.assertRaises(ValueError):
            self.crm.transfer(self.oid, "r2", "m")
        self.assertEqual(self.crm.opps[self.oid]["owner"], "r1")

    def test_target_check_order(self):
        # existence first: bogus opp + bogus owner -> ValueError anyway;
        # actor first: rep asking for manager-only transfer with bogus owner
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.oid, "ghost", "r1")

    def test_transfer_frees_previous_owner_slot(self):
        # A previous owner at load N drops to N-1, so the next incoming lead
        # is routed to them again (the freed slot made observable).
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 2},
            {"id": "m", "role": "manager", "capacity": 5},
        ])
        l1 = crm.add_lead("a@acme.com", "A", "referral", "m")  # -> r1 (full)
        crm.qualify(l1, "m")
        oid = crm.convert(l1, 1000, "m")  # r1 load still 1 (open opp)
        l2 = crm.add_lead("b@acme.com", "B", "web", "m")  # -> r2
        self.assertEqual(crm.leads[l2]["owner"], "r2")
        crm.transfer(oid, "r2", "m")  # r2 load 1 < cap 2, ok
        self.assertEqual(crm.opps[oid]["owner"], "r2")
        self.assertEqual(crm.log[-1], ("transfer", oid, "m"))
        l3 = crm.add_lead("c@acme.com", "C", "web", "m")
        self.assertEqual(crm.leads[l3]["owner"], "r1")  # r1's slot was freed

    def test_failed_transfer_no_state_change(self):
        # r2 (cap 1) takes the next lead, so it is at capacity
        self.crm.add_lead("z@acme.com", "Z", "web", "m")  # -> r2, r2 now full
        self.crm.log = []
        with self.assertRaises(ValueError):
            self.crm.transfer(self.oid, "r2", "m")
        self.assertEqual(self.crm.opps[self.oid]["owner"], "r1")
        self.assertEqual(self.crm.log, [])


class TestForecast(unittest.TestCase):
    def test_empty(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 2}])
        self.assertEqual(crm.forecast(), {"open": 0, "weighted": 0, "won": 0})
        self.assertEqual(crm.log, [])  # forecast never logs

    def test_weights_and_totals(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 10},
            {"id": "m", "role": "manager", "capacity": 5},
        ])

        def mk_op(amount):
            email = "x%d@acme.com" % len(crm.leads)
            lid = crm.add_lead(email, "N", "referral", "m")
            crm.qualify(lid, "m")
            return crm.convert(lid, amount, "m")

        o1 = mk_op(1000)   # prospect  -> 100
        o2 = mk_op(2000)   # proposal  -> 600
        o3 = mk_op(5000)   # negotiation -> 3000
        crm.advance(o2, "proposal", "r1")
        crm.advance(o3, "proposal", "r1")
        crm.advance(o3, "negotiation", "r1")
        o4 = mk_op(4000)   # won
        crm.advance(o4, "proposal", "r1")
        crm.advance(o4, "negotiation", "r1")
        crm.advance(o4, "won", "r1")
        o5 = mk_op(9999)   # lost
        crm.advance(o5, "lost", "r1")
        self.assertEqual(crm.forecast(), {
            "open": 3,
            "weighted": 100 + 600 + 3000,
            "won": 4000,
        })

    def test_floor_division(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 10}])
        lid = crm.add_lead("a@acme.com", "A", "referral", "r1")
        crm.qualify(lid, "r1")
        oid = crm.convert(lid, 999, "r1")  # prospect weight 10 -> 99
        self.assertEqual(crm.forecast()["weighted"], 99)

    def test_discount_reflects_in_forecast(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 10},
                   {"id": "m", "role": "manager", "capacity": 5}])
        lid = crm.add_lead("a@acme.com", "A", "referral", "r1")
        crm.qualify(lid, "r1")
        oid = crm.convert(lid, 10000, "r1")
        with self.assertRaises(PermissionError):
            crm.discount(oid, 30, "r1")  # rep max is 10
        crm.discount(oid, 10, "r1")      # 9000, prospect -> weighted 900
        self.assertEqual(crm.forecast()["weighted"], 900)
        crm.discount(oid, 20, "m")       # 9000*80//100=7200, 720000>=700000
        self.assertEqual(crm.forecast()["weighted"], 720)


class TestGeneralRules(unittest.TestCase):
    def test_attributes_exist(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1}])
        self.assertIsInstance(crm.leads, dict)
        self.assertIsInstance(crm.opps, dict)
        self.assertIsInstance(crm.log, list)

    def test_log_tuple_shape(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1},
                   {"id": "m", "role": "manager", "capacity": 1}])
        lid = crm.add_lead("a@acme.com", "A", "referral", "r1")
        crm.qualify(lid, "r1")
        oid = crm.convert(lid, 100, "r1")
        crm.advance(oid, "proposal", "r1")
        for entry in crm.log:
            self.assertIsInstance(entry, tuple)
            self.assertEqual(len(entry), 3)
        self.assertEqual(crm.log, [
            ("add_lead", "L1", "r1"),
            ("qualify", "L1", "r1"),
            ("convert", "O1", "r1"),
            ("advance", "O1", "r1"),
        ])

    def test_load_definition_counts_open_leads_and_opps(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 2},
            {"id": "m", "role": "manager", "capacity": 5},
        ])
        l1 = crm.add_lead("a@x.com", "A", "referral", "m")  # r1 load 1
        l2 = crm.add_lead("b@x.com", "B", "referral", "m")  # r1 load 2 (full)
        self.assertEqual(crm.leads[l2]["owner"], "r1")
        l3 = crm.add_lead("c@x.com", "C", "referral", "m")
        self.assertIsNone(crm.leads[l3]["owner"])
        crm.qualify(l1, "m")   # qualified still counts: load unchanged
        oid = crm.convert(l1, 1000, "m")  # converted lead replaced by open opp
        l4 = crm.add_lead("d@x.com", "D", "web", "m")
        self.assertIsNone(crm.leads[l4]["owner"])  # load still 2: opp + l2
        self.assertIsNone(crm.leads[l3]["owner"])  # no retroactive assignment
        crm.advance(oid, "proposal", "m")
        crm.advance(oid, "negotiation", "m")
        crm.advance(oid, "won", "m")  # opp final -> load 1 -> assign oldest
        self.assertEqual(crm.leads[l3]["owner"], "r1")
        self.assertEqual(crm.log[-1], ("assign", l3, "system"))
        self.assertIsNone(crm.leads[l4]["owner"])  # r1 full again


if __name__ == "__main__":
    unittest.main()
