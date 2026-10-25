"""Tests for CRM.convert / advance / discount / transfer / forecast."""

import copy
import unittest

from crm import CRM


def base_crm():
    return CRM([
        {"id": "r1", "role": "rep", "capacity": 5},
        {"id": "r2", "role": "rep", "capacity": 5},
        {"id": "m", "role": "manager", "capacity": 9},
    ])


def make_opp(crm, email, amount=1000):
    """Create a qualified, converted lead; return (opp_id, owner)."""
    lead_id = crm.add_lead(email, "N", "referral", "m")
    owner = crm.leads[lead_id]["owner"]
    crm.qualify(lead_id, "m")
    opp_id = crm.convert(lead_id, amount, "m")
    return opp_id, owner


class Convert(unittest.TestCase):
    def setUp(self):
        self.crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 1},
            {"id": "m", "role": "manager", "capacity": 9},
        ])
        self.lead_id = self.crm.add_lead("a@acme.io", "A", "referral", "m")  # -> r1
        self.crm.qualify(self.lead_id, "r1")

    def test_success(self):
        opp_id = self.crm.convert(self.lead_id, 1500, "r1")
        self.assertEqual(opp_id, "O1")
        self.assertEqual(self.crm.opps["O1"], {
            "id": "O1", "lead_id": "L1", "owner": "r1",
            "amount": 1500, "original_amount": 1500, "stage": "prospect",
        })
        self.assertEqual(self.crm.leads[self.lead_id]["status"], "converted")
        self.assertEqual(self.crm.log[-1], ("convert", "O1", "r1"))

    def test_manager_can_convert(self):
        opp_id = self.crm.convert(self.lead_id, 1, "m")
        self.assertEqual(opp_id, "O1")
        self.assertEqual(self.crm.log[-1], ("convert", "O1", "m"))

    def test_amount_validation(self):
        for bad in (True, False, 0, -5, 1.5, "100", None, []):
            self.assertRaises(ValueError, self.crm.convert, self.lead_id, bad, "r1")
        self.assertEqual(self.crm.opps, {})
        self.assertEqual(self.crm.log[-1], ("qualify", "L1", "r1"))

    def test_amount_checked_before_actor(self):
        # r2 is not the owner, but the bad amount (check 2) decides the error.
        self.assertRaises(ValueError, self.crm.convert, self.lead_id, 0, "r2")

    def test_actor_checked_before_status(self):
        crm = base_crm()
        lead_id = crm.add_lead("n@acme.io", "N", "referral", "m")  # status new
        # r2 is neither owner nor manager -> PermissionError, not the status error.
        self.assertRaises(PermissionError, crm.convert, lead_id, 100, "r2")

    def test_status_must_be_qualified(self):
        crm = base_crm()
        lead_id = crm.add_lead("n@acme.io", "N", "referral", "m")
        self.assertRaises(ValueError, crm.convert, lead_id, 100, "m")

    def test_waiting_qualified_lead_cannot_convert(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1},
                   {"id": "m", "role": "manager", "capacity": 9}])
        crm.add_lead("a@a.io", "A", "referral", "m")     # fills r1
        waiting = crm.add_lead("b@b.io", "B", "referral", "m")  # owner None
        self.assertIsNone(crm.leads[waiting]["owner"])
        crm.qualify(waiting, "m")
        self.assertRaises(ValueError, crm.convert, waiting, 100, "m")

    def test_unknown_lead(self):
        self.assertRaises(ValueError, self.crm.convert, "L42", 100, "m")
        self.assertRaises(PermissionError, self.crm.convert, "L42", 100, "ghost")

    def test_opp_ids_sequential_and_failures_dont_count(self):
        opp_id = self.crm.convert(self.lead_id, 100, "r1")
        self.assertEqual(opp_id, "O1")
        l2 = self.crm.add_lead("z@zz.io", "Z", "referral", "m")  # -> r2
        self.crm.qualify(l2, "m")
        self.assertRaises(ValueError, self.crm.convert, l2, 0, "m")       # amount fails
        self.assertRaises(PermissionError, self.crm.convert, l2, 5, "ghost")
        opp2 = self.crm.convert(l2, 500, "m")
        self.assertEqual(opp2, "O2")
        self.assertEqual(sorted(self.crm.opps), ["O1", "O2"])

    def test_failed_convert_changes_nothing(self):
        snapshot = {"leads": copy.deepcopy(self.crm.leads),
                    "opps": copy.deepcopy(self.crm.opps),
                    "log": list(self.crm.log)}
        self.assertRaises(ValueError, self.crm.convert, self.lead_id, 0, "m")
        self.assertEqual(self.crm.leads, snapshot["leads"])
        self.assertEqual(self.crm.opps, snapshot["opps"])
        self.assertEqual(self.crm.log, snapshot["log"])
        # Counter untouched: a success now yields O1.
        self.assertEqual(self.crm.convert(self.lead_id, 100, "m"), "O1")


class Advance(unittest.TestCase):
    def setUp(self):
        self.crm = base_crm()
        self.opp_id, self.owner = make_opp(self.crm, "p@p.io", 1000)

    def test_valid_path_and_logs(self):
        self.assertEqual(self.owner, "r1")
        self.crm.advance(self.opp_id, "proposal", "r1")
        self.crm.advance(self.opp_id, "negotiation", "r1")
        self.crm.advance(self.opp_id, "won", "r1")
        self.assertEqual(self.crm.opps[self.opp_id]["stage"], "won")
        self.assertEqual(self.crm.log[-3:], [
            ("advance", self.opp_id, "r1"),
            ("advance", self.opp_id, "r1"),
            ("advance", self.opp_id, "r1"),
        ])

    def test_manager_can_advance(self):
        self.crm.advance(self.opp_id, "proposal", "m")
        self.assertEqual(self.crm.opps[self.opp_id]["stage"], "proposal")
        self.assertEqual(self.crm.log[-1], ("advance", self.opp_id, "m"))

    def test_invalid_stage_names(self):
        for stage in ("", "Won", "WON", "prospecting", None, 5):
            self.assertRaises(ValueError, self.crm.advance, self.opp_id, stage, "r1")
        self.crm.advance(self.opp_id, "lost", "r1")
        self.assertEqual(self.crm.opps[self.opp_id]["stage"], "lost")

    def test_illegal_transitions(self):
        for stage in ("prospect", "won"):
            self.assertRaises(ValueError, self.crm.advance, self.opp_id, stage, "m")
        self.crm.advance(self.opp_id, "proposal", "m")
        for stage in ("prospect", "proposal", "won"):
            self.assertRaises(ValueError, self.crm.advance, self.opp_id, stage, "m")
        self.crm.advance(self.opp_id, "negotiation", "m")
        for stage in ("prospect", "proposal", "negotiation"):
            self.assertRaises(ValueError, self.crm.advance, self.opp_id, stage, "m")
        self.assertEqual(self.crm.opps[self.opp_id]["stage"], "negotiation")

    def test_lost_from_any_open_stage(self):
        for stage in (None, "proposal", "negotiation"):
            opp_id, owner = make_opp(self.crm, "l%s@x.io" % (stage or "start"), 1000)
            if stage == "proposal":
                self.crm.advance(opp_id, "proposal", owner)
            elif stage == "negotiation":
                self.crm.advance(opp_id, "proposal", owner)
                self.crm.advance(opp_id, "negotiation", owner)
            self.crm.advance(opp_id, "lost", owner)
            self.assertEqual(self.crm.opps[opp_id]["stage"], "lost")

    def test_final_stages_are_final(self):
        self.crm.advance(self.opp_id, "lost", "r1")
        for stage in ("lost", "won", "proposal"):
            self.assertRaises(ValueError, self.crm.advance, self.opp_id, stage, "m")
        opp2, owner2 = make_opp(self.crm, "w@w.io", 1000)
        self.crm.advance(opp2, "proposal", owner2)
        self.crm.advance(opp2, "negotiation", owner2)
        self.crm.advance(opp2, "won", owner2)
        self.assertRaises(ValueError, self.crm.advance, opp2, "lost", "m")

    def test_auth(self):
        opp_id, owner = make_opp(self.crm, "x@x.io", 1000)
        other = "r2" if owner == "r1" else "r1"
        self.assertRaises(PermissionError, self.crm.advance, opp_id, "proposal", other)
        self.assertRaises(PermissionError, self.crm.advance, opp_id, "proposal", "ghost")

    def test_stage_check_before_auth(self):
        other = "r2" if self.owner == "r1" else "r1"
        self.assertRaises(ValueError, self.crm.advance, self.opp_id, "bogus", other)

    def test_auth_before_final_stage_check(self):
        self.crm.advance(self.opp_id, "lost", "r1")
        other = "r2" if self.owner == "r1" else "r1"
        # Not owner/manager: PermissionError even though the stage is final too.
        self.assertRaises(PermissionError, self.crm.advance, self.opp_id, "proposal", other)

    def test_big_deal_negotiation_gate(self):
        opp_id, owner = make_opp(self.crm, "big@big.io", 60000)
        self.crm.advance(opp_id, "proposal", owner)
        self.assertRaises(PermissionError, self.crm.advance, opp_id, "negotiation", owner)
        self.assertEqual(self.crm.opps[opp_id]["stage"], "proposal")
        self.crm.advance(opp_id, "negotiation", "m")
        self.assertEqual(self.crm.opps[opp_id]["stage"], "negotiation")
        # The gate is only for entering negotiation: reps may still close it.
        self.crm.advance(opp_id, "won", owner)
        self.assertEqual(self.crm.opps[opp_id]["stage"], "won")

    def test_gate_boundary_amount_50000(self):
        opp_id, owner = make_opp(self.crm, "b50@b.io", 50000)
        self.crm.advance(opp_id, "proposal", owner)
        self.crm.advance(opp_id, "negotiation", owner)  # exactly 50000 is allowed
        opp2, owner2 = make_opp(self.crm, "b51@b.io", 50001)
        self.crm.advance(opp2, "proposal", owner2)
        self.assertRaises(PermissionError, self.crm.advance, opp2, "negotiation", owner2)

    def test_gate_after_discount(self):
        opp_id, owner = make_opp(self.crm, "d@d.io", 60000)
        self.crm.advance(opp_id, "proposal", owner)
        self.crm.discount(opp_id, 10, owner)   # 54000, still gated
        self.assertRaises(PermissionError, self.crm.advance, opp_id, "negotiation", owner)
        self.crm.discount(opp_id, 10, owner)   # 48600, under threshold
        self.crm.advance(opp_id, "negotiation", owner)

    def test_slot_freed_on_won_assigns_queue(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 1},
            {"id": "m", "role": "manager", "capacity": 9},
        ])
        l1 = crm.add_lead("a@a.io", "A", "referral", "m")   # r1
        l2 = crm.add_lead("b@b.io", "B", "referral", "m")   # r2
        l3 = crm.add_lead("c@c.io", "C", "event", "m")      # waiting (owner None)
        crm.qualify(l1, "m")
        o1 = crm.convert(l1, 100, "m")
        crm.advance(o1, "proposal", "m")
        crm.advance(o1, "negotiation", "m")
        crm.advance(o1, "won", "m")
        self.assertEqual(crm.leads[l3]["owner"], "r1")
        self.assertEqual(crm.leads[l3]["status"], "new")
        self.assertEqual(crm.log[-2:], [
            ("advance", o1, "m"),
            ("assign", l3, "system"),
        ])

    def test_slot_freed_on_lost(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "m", "role": "manager", "capacity": 9},
        ])
        l1 = crm.add_lead("a@a.io", "A", "referral", "m")
        l2 = crm.add_lead("b@b.io", "B", "referral", "m")   # waiting
        crm.qualify(l1, "m")
        o1 = crm.convert(l1, 100, "m")
        crm.advance(o1, "lost", "r1")
        self.assertEqual(crm.leads[l2]["owner"], "r1")
        self.assertEqual(crm.log[-1], ("assign", l2, "system"))

    def test_failed_advance_does_not_assign(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "m", "role": "manager", "capacity": 9},
        ])
        l1 = crm.add_lead("a@a.io", "A", "referral", "m")
        l2 = crm.add_lead("b@b.io", "B", "referral", "m")   # waiting
        crm.qualify(l1, "m")
        o1 = crm.convert(l1, 100, "m")
        crm.advance(o1, "proposal", "m")
        crm.advance(o1, "negotiation", "m")
        snapshot = {"leads": copy.deepcopy(crm.leads),
                    "opps": copy.deepcopy(crm.opps),
                    "log": list(crm.log)}
        self.assertRaises(ValueError, crm.advance, o1, "bogus", "m")
        self.assertRaises(PermissionError, crm.advance, o1, "won", "ghost")
        self.assertEqual(crm.leads, snapshot["leads"])
        self.assertEqual(crm.opps, snapshot["opps"])
        self.assertEqual(crm.log, snapshot["log"])

    def test_unknown_opp(self):
        self.assertRaises(ValueError, self.crm.advance, "O99", "proposal", "m")
        self.assertRaises(PermissionError, self.crm.advance, "O99", "proposal", "ghost")


class Discount(unittest.TestCase):
    def setUp(self):
        self.crm = base_crm()
        self.opp_id, self.owner = make_opp(self.crm, "d@d.io", 1000)

    def test_success(self):
        self.assertIsNone(self.crm.discount(self.opp_id, 10, "r1"))
        opp = self.crm.opps[self.opp_id]
        self.assertEqual(opp["amount"], 900)
        self.assertEqual(opp["original_amount"], 1000)
        self.assertEqual(self.crm.log[-1], ("discount", self.opp_id, "r1"))

    def test_pct_bounds_ok(self):
        self.crm.discount(self.opp_id, 1, "m")
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 990)
        self.crm.discount(self.opp_id, 1, "m")  # 990*99//100 = 980
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 980)
        opp2, owner2 = make_opp(self.crm, "d2@d.io", 2000)
        self.crm.discount(opp2, 30, "m")  # 1400, exactly 30% of original
        self.assertEqual(self.crm.opps[opp2]["amount"], 1400)

    def test_pct_invalid(self):
        for bad in (0, 31, -1, 10.5, True, False, "10", None):
            self.assertRaises(ValueError, self.crm.discount, self.opp_id, bad, "m")
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 1000)
        self.assertEqual(self.crm.log[-1], ("convert", self.opp_id, "m"))

    def test_rep_capped_at_10(self):
        self.assertRaises(PermissionError, self.crm.discount, self.opp_id, 11, self.owner)
        self.assertRaises(PermissionError, self.crm.discount, self.opp_id, 30, self.owner)
        self.crm.discount(self.opp_id, 10, self.owner)
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 900)

    def test_manager_up_to_30(self):
        self.crm.discount(self.opp_id, 30, "m")
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 700)

    def test_check_order(self):
        other = "r2" if self.owner == "r1" else "r1"
        # pct validated before actor (check 2 before check 3)
        self.assertRaises(ValueError, self.crm.discount, self.opp_id, 99, other)
        # actor validated before stage (check 3 before check 4)
        self.assertRaises(PermissionError, self.crm.discount, self.opp_id, 5, other)
        # stage validated before the rep cap (check 4 before check 5)
        opp2, owner2 = make_opp(self.crm, "d3@d.io", 1000)
        self.crm.advance(opp2, "lost", owner2)
        self.assertRaises(ValueError, self.crm.discount, opp2, 15, owner2)

    def test_final_stage_rejected(self):
        self.crm.advance(self.opp_id, "lost", self.owner)
        self.assertRaises(ValueError, self.crm.discount, self.opp_id, 5, "m")

    def test_cumulative_cap_with_floor(self):
        # 999: a 30% cut floors to 699, which breaches the 70% floor.
        opp_id, owner = make_opp(self.crm, "f@f.io", 999)
        self.assertRaises(ValueError, self.crm.discount, opp_id, 30, "m")
        self.crm.discount(opp_id, 29, "m")  # 999*71//100 = 709; 70900 >= 69930
        self.assertEqual(self.crm.opps[opp_id]["amount"], 709)

    def test_multiple_discounts_accumulate(self):
        for _ in range(3):
            self.crm.discount(self.opp_id, 10, "m")
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 729)
        before = copy.deepcopy(self.crm.opps[self.opp_id])
        self.assertRaises(ValueError, self.crm.discount, self.opp_id, 10, "m")  # 656 < 70%
        self.assertEqual(self.crm.opps[self.opp_id], before)
        self.crm.discount(self.opp_id, 3, "m")  # 729*97//100 = 707; 70700 >= 70000
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 707)
        self.assertRaises(ValueError, self.crm.discount, self.opp_id, 4, "m")  # 678 < 700

    def test_unknown_opp_and_no_log_on_failure(self):
        self.assertRaises(ValueError, self.crm.discount, "O99", 5, "m")
        self.assertEqual(self.crm.log.count(("discount", "O99", "m")), 0)


class Transfer(unittest.TestCase):
    def setUp(self):
        self.crm = base_crm()
        self.opp_id, self.owner = make_opp(self.crm, "t@t.io", 1000)

    def test_manager_transfer(self):
        self.assertIsNone(self.crm.transfer(self.opp_id, "r2", "m"))
        self.assertEqual(self.crm.opps[self.opp_id]["owner"], "r2")
        self.assertEqual(self.crm.log[-1], ("transfer", self.opp_id, "m"))

    def test_only_managers_transfer(self):
        self.assertRaises(PermissionError, self.crm.transfer, self.opp_id, "r2", self.owner)
        other = "r2" if self.owner == "r1" else "r1"
        self.assertRaises(PermissionError, self.crm.transfer, self.opp_id, "r2", other)
        self.assertRaises(PermissionError, self.crm.transfer, self.opp_id, "r2", "ghost")

    def test_actor_checked_before_new_owner_validation(self):
        self.assertRaises(PermissionError, self.crm.transfer, self.opp_id, "ghost", "r1")

    def test_new_owner_must_be_known_rep(self):
        self.assertRaises(ValueError, self.crm.transfer, self.opp_id, "ghost", "m")
        self.assertRaises(ValueError, self.crm.transfer, self.opp_id, "m", "m")  # manager
        self.assertRaises(ValueError, self.crm.transfer, self.opp_id, 12, "m")
        self.assertRaises(ValueError, self.crm.transfer, self.opp_id, None, "m")

    def test_same_owner_rejected(self):
        self.assertRaises(ValueError, self.crm.transfer, self.opp_id, self.owner, "m")

    def test_final_stage_rejected(self):
        self.crm.advance(self.opp_id, "lost", self.owner)
        self.assertRaises(ValueError, self.crm.transfer, self.opp_id, "r2", "m")
        self.assertEqual(self.crm.opps[self.opp_id]["owner"], self.owner)

    def test_capacity_enforced(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 1},
            {"id": "m", "role": "manager", "capacity": 9},
        ])
        l1 = crm.add_lead("a@a.io", "A", "referral", "m")   # r1
        l2 = crm.add_lead("b@b.io", "B", "referral", "m")   # r2 (load 1 = full)
        crm.qualify(l1, "m")
        o1 = crm.convert(l1, 100, "m")
        self.assertRaises(ValueError, crm.transfer, o1, "r2", "m")
        crm.qualify(l2, "m")
        crm.convert(l2, 100, "m")  # r2 still load 1 (one open opp)
        self.assertRaises(ValueError, crm.transfer, o1, "r2", "m")

    def test_transfer_frees_previous_owner(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 2},
            {"id": "m", "role": "manager", "capacity": 9},
        ])
        l1 = crm.add_lead("a@a.io", "A", "referral", "m")   # r1 (full)
        l2 = crm.add_lead("b@b.io", "B", "referral", "m")   # r2 (load 1)
        crm.qualify(l1, "m")
        o1 = crm.convert(l1, 100, "m")
        self.assertRaises(ValueError, crm.transfer, o1, "r1", "m")  # same owner
        crm.transfer(o1, "r2", "m")              # r2 load 2 (full)
        self.assertEqual(crm.opps[o1]["owner"], "r2")
        self.assertRaises(ValueError, crm.transfer, o1, "r2", "m")  # r2 at capacity
        l3 = crm.add_lead("c@c.io", "C", "referral", "m")   # r1 slot is free again
        self.assertEqual(crm.leads[l3]["owner"], "r1")
        self.assertEqual(crm.log[-2:], [
            ("transfer", o1, "m"),
            ("add_lead", l3, "m"),
        ])

    def test_failed_transfer_changes_nothing(self):
        snapshot = {"opps": copy.deepcopy(self.crm.opps), "log": list(self.crm.log)}
        self.assertRaises(PermissionError, self.crm.transfer, self.opp_id, "r2", "r1")
        self.assertRaises(ValueError, self.crm.transfer, self.opp_id, "ghost", "m")
        self.assertEqual(self.crm.opps, snapshot["opps"])
        self.assertEqual(self.crm.log, snapshot["log"])


class Forecast(unittest.TestCase):
    def test_empty(self):
        crm = base_crm()
        self.assertEqual(crm.forecast(), {"open": 0, "weighted": 0, "won": 0})

    def test_mixed_pipeline(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 5},
            {"id": "m", "role": "manager", "capacity": 9},
        ])
        o1, _ = make_opp(crm, "f1@f.io", 1000)                      # prospect
        o2, _ = make_opp(crm, "f2@f.io", 2000)
        crm.advance(o2, "proposal", "m")
        o3, _ = make_opp(crm, "f3@f.io", 3000)
        crm.advance(o3, "proposal", "m")
        crm.advance(o3, "negotiation", "m")
        o4, _ = make_opp(crm, "f4@f.io", 4000)
        crm.advance(o4, "proposal", "m")
        crm.advance(o4, "negotiation", "m")
        crm.advance(o4, "won", "m")
        o5, _ = make_opp(crm, "f5@f.io", 5000)
        crm.advance(o5, "lost", "m")
        self.assertEqual(crm.forecast(), {"open": 3, "weighted": 100 + 600 + 1800, "won": 4000})

    def test_weights_use_floor_and_current_amount(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 5},
            {"id": "m", "role": "manager", "capacity": 9},
        ])
        o1, owner = make_opp(crm, "g@g.io", 1001)   # prospect: 1001*10//100 = 100
        self.assertEqual(crm.forecast()["weighted"], 100)
        o2, owner2 = make_opp(crm, "h@h.io", 4000)
        crm.discount(o2, 10, "m")                   # 3600
        crm.advance(o2, "proposal", "m")
        crm.advance(o2, "negotiation", "m")
        crm.advance(o2, "won", "m")
        self.assertEqual(crm.forecast(), {"open": 1, "weighted": 100, "won": 3600})

    def test_no_actor_and_no_log(self):
        crm = base_crm()
        make_opp(crm, "k@k.io", 100)
        before = list(crm.log)
        crm.forecast()
        self.assertEqual(crm.log, before)


class EndToEnd(unittest.TestCase):
    def test_full_pipeline_and_exact_log(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 1},
            {"id": "m", "role": "manager", "capacity": 9},
        ])
        l1 = crm.add_lead("a@acme.io", "Alice", "referral", "m")
        l2 = crm.add_lead("b@acme.io", "Bob", "referral", "m")
        l3 = crm.add_lead("c@acme.io", "Cara", "event", "m")
        self.assertEqual((crm.leads[l1]["owner"], crm.leads[l2]["owner"],
                          crm.leads[l3]["owner"]), ("r1", "r2", None))
        self.assertEqual(crm.leads[l3]["score"], 35)
        crm.qualify(l1, "r1")
        o1 = crm.convert(l1, 60000, "r1")
        self.assertRaises(PermissionError, crm.advance, o1, "proposal", "r2")
        crm.advance(o1, "proposal", "r1")
        self.assertRaises(PermissionError, crm.advance, o1, "negotiation", "r1")
        crm.advance(o1, "negotiation", "m")
        crm.advance(o1, "won", "r1")
        self.assertEqual(crm.leads[l3]["owner"], "r1")
        self.assertEqual(crm.leads[l3]["status"], "new")
        self.assertEqual(crm.log, [
            ("add_lead", "L1", "m"),
            ("add_lead", "L2", "m"),
            ("add_lead", "L3", "m"),
            ("qualify", "L1", "r1"),
            ("convert", "O1", "r1"),
            ("advance", "O1", "r1"),
            ("advance", "O1", "m"),
            ("advance", "O1", "r1"),
            ("assign", "L3", "system"),
        ])
        self.assertEqual(crm.forecast(), {"open": 0, "weighted": 0, "won": 60000})
        self.assertEqual(crm.leads[l1]["status"], "converted")
        self.assertEqual(crm.opps[o1]["stage"], "won")


if __name__ == "__main__":
    unittest.main()
