"""Tests for qualify, convert, advance, discount and transfer."""
import unittest

from crm import CRM, DuplicateLeadError


def build():
    return CRM([
        {"id": "r1", "role": "rep", "capacity": 2},
        {"id": "r2", "role": "rep", "capacity": 1},
        {"id": "m1", "role": "manager", "capacity": 0},
    ])


class TestQualify(unittest.TestCase):
    def test_owner_qualifies(self):
        crm = build()
        crm.add_lead("a@gmail.com", "A", "referral", "m1")  # score 30, r1
        crm.qualify("L1", "r1")
        self.assertEqual(crm.leads["L1"]["status"], "qualified")
        self.assertEqual(crm.log[-1], ("qualify", "L1", "r1"))

    def test_manager_qualifies_any_lead(self):
        crm = build()
        crm.add_lead("a@gmail.com", "A", "referral", "m1")
        crm.qualify("L1", "m1")
        self.assertEqual(crm.leads["L1"]["status"], "qualified")
        self.assertEqual(crm.log[-1], ("qualify", "L1", "m1"))

    def test_other_rep_cannot_qualify(self):
        crm = build()
        crm.add_lead("a@gmail.com", "A", "referral", "m1")  # owner r1
        with self.assertRaises(PermissionError):
            crm.qualify("L1", "r2")
        self.assertEqual(crm.leads["L1"]["status"], "new")
        self.assertEqual(crm.log, [("add_lead", "L1", "m1")])

    def test_unknown_lead(self):
        crm = build()
        with self.assertRaises(ValueError):
            crm.qualify("L99", "m1")
        self.assertEqual(crm.log, [])

    def test_unknown_actor_first(self):
        crm = build()
        with self.assertRaises(PermissionError):
            crm.qualify("L99", "ghost")

    def test_wrong_status(self):
        crm = build()
        crm.add_lead("a@gmail.com", "A", "referral", "m1")
        crm.qualify("L1", "m1")
        with self.assertRaises(ValueError):
            crm.qualify("L1", "m1")  # already qualified
        self.assertEqual(crm.leads["L1"]["status"], "qualified")
        self.assertEqual(len(crm.log), 2)

    def test_score_below_30(self):
        crm = build()
        crm.add_lead("a@gmail.com", "A", "web", "m1")       # 10
        crm.add_lead("b@gmail.com", "B", "event", "m1")    # 20
        crm.add_lead("c@corp.io", "C", "web", "m1")        # 25
        for lead_id in ["L1", "L2", "L3"]:
            with self.subTest(lead_id=lead_id):
                with self.assertRaises(ValueError):
                    crm.qualify(lead_id, "m1")
        self.assertEqual(crm.leads["L1"]["status"], "new")
        self.assertEqual(len(crm.log), 3)

    def test_score_exactly_30_ok(self):
        crm = build()
        crm.add_lead("a@gmail.com", "A", "referral", "m1")  # exactly 30
        crm.qualify("L1", "m1")
        self.assertEqual(crm.leads["L1"]["status"], "qualified")


class TestConvert(unittest.TestCase):
    def make_qualified(self):
        crm = build()
        crm.add_lead("a@gmail.com", "A", "referral", "m1")  # L1, owner r1
        crm.qualify("L1", "r1")
        return crm

    def test_convert_success(self):
        crm = self.make_qualified()
        opp_id = crm.convert("L1", 1000, "r1")
        self.assertEqual(opp_id, "O1")
        self.assertEqual(crm.opps["O1"], {
            "id": "O1",
            "lead_id": "L1",
            "owner": "r1",
            "amount": 1000,
            "original_amount": 1000,
            "stage": "prospect",
        })
        self.assertEqual(crm.leads["L1"]["status"], "converted")
        self.assertEqual(crm.log[-1], ("convert", "O1", "r1"))

    def test_manager_can_convert(self):
        crm = self.make_qualified()
        self.assertEqual(crm.convert("L1", 500, "m1"), "O1")
        self.assertEqual(crm.opps["O1"]["owner"], "r1")

    def test_unknown_lead(self):
        crm = build()
        with self.assertRaises(ValueError):
            crm.convert("L99", 100, "m1")

    def test_unknown_actor_first(self):
        crm = build()
        with self.assertRaises(PermissionError):
            crm.convert("L99", 100, "ghost")

    def test_amount_checked_before_permission(self):
        crm = build()
        crm.add_lead("a@gmail.com", "A", "referral", "m1")  # owner r1
        with self.assertRaises(ValueError):
            crm.convert("L1", -5, "r2")  # bad amount AND bad actor
        with self.assertRaises(ValueError):
            crm.convert("L1", 0, "r2")
        with self.assertRaises(ValueError):
            crm.convert("L1", True, "r2")   # bool is not allowed
        with self.assertRaises(ValueError):
            crm.convert("L1", 10.0, "r2")   # not an int
        with self.assertRaises(ValueError):
            crm.convert("L1", "100", "r2")
        self.assertEqual(crm.log, [("add_lead", "L1", "m1")])

    def test_permission(self):
        crm = self.make_qualified()
        with self.assertRaises(PermissionError):
            crm.convert("L1", 100, "r2")
        self.assertEqual(crm.leads["L1"]["status"], "qualified")

    def test_status_must_be_qualified(self):
        crm = build()
        crm.add_lead("a@gmail.com", "A", "referral", "m1")  # still "new"
        with self.assertRaises(ValueError):
            crm.convert("L1", 100, "m1")
        crm.qualify("L1", "m1")
        crm.convert("L1", 100, "m1")
        with self.assertRaises(ValueError):
            crm.convert("L1", 100, "m1")  # already converted
        self.assertEqual(crm.log[-1], ("convert", "O1", "m1"))

    def test_lead_without_owner(self):
        crm = build()  # r1 cap 2, r2 cap 1
        for i in range(4):
            crm.add_lead("%d@gmail.com" % i, "N", "referral", "m1")
        # L4 has no owner
        crm.qualify("L4", "m1")
        with self.assertRaises(ValueError):
            crm.convert("L4", 100, "m1")
        self.assertEqual(crm.leads["L4"]["status"], "qualified")
        self.assertEqual(crm.log[-1], ("qualify", "L4", "m1"))

    def test_opportunity_ids_sequence(self):
        crm = build()
        for i in range(3):
            crm.add_lead("%d@gmail.com" % i, "N", "referral", "m1")
        crm.qualify("L1", "m1")
        crm.qualify("L2", "m1")
        with self.assertRaises(ValueError):
            crm.convert("L3", 100, "m1")  # status new
        self.assertEqual(crm.convert("L1", 10, "m1"), "O1")
        self.assertEqual(crm.convert("L2", 10, "m1"), "O2")
        crm.qualify("L3", "m1")
        self.assertEqual(crm.convert("L3", 10, "m1"), "O3")


class TestAdvance(unittest.TestCase):
    def make_opp(self, amount=1000, email="a@gmail.com"):
        crm = build()
        crm.add_lead(email, "A", "referral", "m1")  # L1 owner r1
        crm.qualify("L1", "r1")
        opp_id = crm.convert("L1", amount, "r1")
        return crm, opp_id

    def test_full_pipeline(self):
        crm, opp_id = self.make_opp(amount=60000)
        crm.advance(opp_id, "proposal", "r1")
        crm.advance(opp_id, "negotiation", "m1")  # >50000 needs manager
        crm.advance(opp_id, "won", "r1")
        self.assertEqual(crm.opps[opp_id]["stage"], "won")
        ops = [e[0] for e in crm.log]
        self.assertEqual(ops.count("advance"), 3)

    def test_unknown_opp(self):
        crm = build()
        with self.assertRaises(ValueError):
            crm.advance("O9", "won", "m1")

    def test_unknown_actor_first(self):
        crm = build()
        with self.assertRaises(PermissionError):
            crm.advance("O9", "bogus", "ghost")

    def test_invalid_stage_before_permission(self):
        crm, opp_id = self.make_opp()
        with self.assertRaises(ValueError):
            crm.advance(opp_id, "bogus", "r2")  # bad stage AND bad actor
        self.assertEqual(crm.log[-1], ("convert", opp_id, "r1"))

    def test_permission(self):
        crm, opp_id = self.make_opp()
        with self.assertRaises(PermissionError):
            crm.advance(opp_id, "proposal", "r2")
        self.assertEqual(crm.opps[opp_id]["stage"], "prospect")

    def test_final_stage(self):
        crm, opp_id = self.make_opp()
        crm.advance(opp_id, "lost", "r1")
        with self.assertRaises(ValueError):
            crm.advance(opp_id, "proposal", "r1")
        self.assertEqual(crm.opps[opp_id]["stage"], "lost")

    def test_must_be_next_stage(self):
        crm, opp_id = self.make_opp()
        for bad in ["prospect", "negotiation", "won"]:
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    crm.advance(opp_id, bad, "r1")
        self.assertEqual(crm.opps[opp_id]["stage"], "prospect")
        self.assertEqual(len(crm.log), 3)
        crm.advance(opp_id, "proposal", "r1")
        with self.assertRaises(ValueError):
            crm.advance(opp_id, "won", "r1")  # skips negotiation
        crm.advance(opp_id, "negotiation", "r1")  # 1000 <= 50000, rep ok
        crm.advance(opp_id, "won", "r1")

    def test_negotiation_over_50000_requires_manager(self):
        crm, opp_id = self.make_opp(amount=50001)
        crm.advance(opp_id, "proposal", "r1")
        with self.assertRaises(PermissionError):
            crm.advance(opp_id, "negotiation", "r1")
        self.assertEqual(crm.opps[opp_id]["stage"], "proposal")
        self.assertEqual(len(crm.log), 4)
        crm.advance(opp_id, "negotiation", "m1")
        self.assertEqual(crm.opps[opp_id]["stage"], "negotiation")

    def test_negotiation_exactly_50000_rep_ok(self):
        crm, opp_id = self.make_opp(amount=50000)
        crm.advance(opp_id, "proposal", "r1")
        crm.advance(opp_id, "negotiation", "r1")
        self.assertEqual(crm.opps[opp_id]["stage"], "negotiation")

    def test_lost_from_any_non_final_stage(self):
        crm, opp_id = self.make_opp()
        crm.advance(opp_id, "lost", "r1")
        self.assertEqual(crm.opps[opp_id]["stage"], "lost")
        crm2, opp2 = self.make_opp(email="b@gmail.com")
        crm2.advance(opp2, "proposal", "r1")
        crm2.advance(opp2, "lost", "m1")
        self.assertEqual(crm2.opps[opp2]["stage"], "lost")

    def test_won_frees_slot_and_assigns_waiting(self):
        crm = build()  # r1 cap 2, r2 cap 1
        crm.add_lead("a@gmail.com", "A", "referral", "m1")   # L1 r1
        crm.add_lead("b@gmail.com", "B", "web", "m1")       # L2 r2
        crm.add_lead("c@gmail.com", "C", "referral", "m1")  # L3 r1
        waiting = crm.add_lead("d@gmail.com", "D", "web", "m1")  # L4 waiting
        crm.qualify("L1", "r1")
        crm.convert("L1", 100000, "r1")  # O1 owner r1
        # r1 load: L3 (new) + O1 (prospect) = 2 == capacity
        crm.qualify("L3", "r1")
        crm.advance("O1", "proposal", "r1")
        crm.advance("O1", "negotiation", "m1")
        crm.advance("O1", "won", "r1")
        self.assertEqual(crm.leads[waiting]["owner"], "r1")
        self.assertEqual(crm.log[-2], ("advance", "O1", "r1"))
        self.assertEqual(crm.log[-1], ("assign", waiting, "system"))

    def test_lost_also_frees_slot(self):
        crm = build()
        crm.add_lead("a@gmail.com", "A", "referral", "m1")   # L1 r1
        crm.add_lead("b@gmail.com", "B", "web", "m1")       # L2 r2
        crm.add_lead("c@gmail.com", "C", "referral", "m1")  # L3 r1
        waiting = crm.add_lead("d@gmail.com", "D", "web", "m1")  # L4 waiting
        crm.qualify("L1", "r1")
        crm.convert("L1", 100, "r1")  # O1
        crm.advance("O1", "lost", "r1")
        self.assertEqual(crm.leads[waiting]["owner"], "r1")
        self.assertEqual(crm.log[-1], ("assign", waiting, "system"))

    def test_no_assignment_when_rep_still_at_capacity(self):
        crm = build()
        crm.add_lead("a@gmail.com", "A", "referral", "m1")   # L1 r1
        crm.add_lead("b@gmail.com", "B", "web", "m1")       # L2 r2
        crm.add_lead("c@gmail.com", "C", "referral", "m1")  # L3 r1
        waiting = crm.add_lead("d@gmail.com", "D", "web", "m1")  # L4 waiting
        crm.qualify("L1", "r1")
        crm.convert("L1", 100, "r1")  # O1, r1 load: L3 + O1 = 2
        crm.advance("O1", "proposal", "r1")  # not final -> no freeing
        self.assertIsNone(crm.leads[waiting]["owner"])
        self.assertEqual([e[0] for e in crm.log],
                         ["add_lead"] * 4 + ["qualify", "convert", "advance"])

    def test_conversion_frees_lead_slot_but_not_queue(self):
        crm = build()
        crm.add_lead("a@gmail.com", "A", "referral", "m1")   # L1 r1
        crm.add_lead("b@gmail.com", "B", "web", "m1")       # L2 r2
        crm.add_lead("c@gmail.com", "C", "referral", "m1")  # L3 r1
        waiting = crm.add_lead("d@gmail.com", "D", "web", "m1")  # L4 waiting
        crm.qualify("L1", "r1")
        crm.convert("L1", 100, "r1")
        # r1 load unchanged (L3 + O1); spec only frees slots in advance/transfer
        self.assertIsNone(crm.leads[waiting]["owner"])


class TestDiscount(unittest.TestCase):
    def make_opp(self, amount=1000):
        crm = build()
        crm.add_lead("a@gmail.com", "A", "referral", "m1")
        crm.qualify("L1", "r1")
        opp_id = crm.convert("L1", amount, "r1")
        return crm, opp_id

    def test_discount_applies(self):
        crm, opp_id = self.make_opp(amount=1000)
        crm.discount(opp_id, 10, "r1")
        self.assertEqual(crm.opps[opp_id]["amount"], 900)
        self.assertEqual(crm.log[-1], ("discount", "O1", "r1"))

    def test_manager_any_pct_up_to_30(self):
        crm, opp_id = self.make_opp(amount=1000)
        crm.discount(opp_id, 30, "m1")
        self.assertEqual(crm.opps[opp_id]["amount"], 700)

    def test_rep_over_10_permission(self):
        crm, opp_id = self.make_opp(amount=1000)
        with self.assertRaises(PermissionError):
            crm.discount(opp_id, 11, "r1")
        self.assertEqual(crm.opps[opp_id]["amount"], 1000)
        self.assertEqual(len(crm.log), 3)
        crm.discount(opp_id, 10, "r1")  # boundary is allowed
        self.assertEqual(crm.opps[opp_id]["amount"], 900)

    def test_pct_validation(self):
        crm, opp_id = self.make_opp()
        for pct in [0, 31, -5, True, False, 2.5, "10", None]:
            with self.subTest(pct=pct):
                with self.assertRaises(ValueError):
                    crm.discount(opp_id, pct, "r1")
        self.assertEqual(crm.opps[opp_id]["amount"], 1000)

    def test_unknown_opp(self):
        crm = build()
        with self.assertRaises(ValueError):
            crm.discount("O9", 10, "m1")

    def test_unknown_actor_first(self):
        crm = build()
        with self.assertRaises(PermissionError):
            crm.discount("O9", 10, "ghost")

    def test_pct_checked_before_permission(self):
        crm, opp_id = self.make_opp()
        with self.assertRaises(ValueError):
            crm.discount(opp_id, 99, "r2")  # bad pct AND bad actor
        self.assertEqual(len(crm.log), 3)

    def test_final_stage(self):
        crm, opp_id = self.make_opp()
        crm.advance(opp_id, "lost", "r1")
        with self.assertRaises(ValueError):
            crm.discount(opp_id, 10, "m1")
        self.assertEqual(crm.opps[opp_id]["amount"], 1000)

    def test_stage_checked_before_rep_pct_cap(self):
        crm, opp_id = self.make_opp()
        crm.advance(opp_id, "lost", "r1")
        with self.assertRaises(ValueError):  # not PermissionError
            crm.discount(opp_id, 15, "r1")

    def test_cumulative_cap_30_percent(self):
        crm, opp_id = self.make_opp(amount=1000)
        crm.discount(opp_id, 10, "r1")   # 900
        crm.discount(opp_id, 10, "m1")   # 810
        # 810*78//100 = 631 -> 63100 < 70000 -> blocked
        with self.assertRaises(ValueError):
            crm.discount(opp_id, 22, "m1")
        self.assertEqual(crm.opps[opp_id]["amount"], 810)
        # 810*87//100 = 704 -> 70400 >= 70000 -> ok
        crm.discount(opp_id, 13, "m1")
        self.assertEqual(crm.opps[opp_id]["amount"], 704)
        # 704*99//100 = 696 -> 69600 < 70000 -> blocked
        with self.assertRaises(ValueError):
            crm.discount(opp_id, 1, "m1")
        self.assertEqual(crm.opps[opp_id]["amount"], 704)

    def test_exactly_30_percent_allowed(self):
        crm, opp_id = self.make_opp(amount=1000)
        crm.discount(opp_id, 30, "m1")  # 700*100 == 70000
        self.assertEqual(crm.opps[opp_id]["amount"], 700)
        with self.assertRaises(ValueError):
            crm.discount(opp_id, 1, "m1")  # 693 -> 69300 < 70000


class TestTransfer(unittest.TestCase):
    def make_opp(self):
        # r1 cap 2, r2 cap 3 so r2 has room
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 2},
            {"id": "r2", "role": "rep", "capacity": 3},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        crm.add_lead("a@gmail.com", "A", "referral", "m1")  # L1 r1
        crm.qualify("L1", "r1")
        crm.convert("L1", 1000, "r1")
        return crm, "O1"

    def test_success(self):
        crm, opp_id = self.make_opp()
        crm.transfer(opp_id, "r2", "m1")
        self.assertEqual(crm.opps[opp_id]["owner"], "r2")
        self.assertEqual(crm.log[-1], ("transfer", "O1", "m1"))

    def test_rep_cannot_transfer(self):
        crm, opp_id = self.make_opp()
        with self.assertRaises(PermissionError):
            crm.transfer(opp_id, "r2", "r1")
        with self.assertRaises(PermissionError):
            crm.transfer(opp_id, "r2", "r2")
        self.assertEqual(crm.opps[opp_id]["owner"], "r1")

    def test_unknown_opp(self):
        crm = build()
        with self.assertRaises(ValueError):
            crm.transfer("O9", "r1", "m1")

    def test_unknown_actor_first(self):
        crm = build()
        with self.assertRaises(PermissionError):
            crm.transfer("O9", "r1", "ghost")

    def test_actor_checked_before_new_owner(self):
        crm, opp_id = self.make_opp()
        with self.assertRaises(PermissionError):
            crm.transfer(opp_id, "ghost", "r1")  # rep actor AND bad owner
        self.assertEqual(crm.opps[opp_id]["owner"], "r1")

    def test_new_owner_must_be_known_rep(self):
        crm, opp_id = self.make_opp()
        for bad in ["ghost", "m1", None, 7]:
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    crm.transfer(opp_id, bad, "m1")
        self.assertEqual(crm.opps[opp_id]["owner"], "r1")

    def test_final_stage(self):
        crm, opp_id = self.make_opp()
        crm.advance(opp_id, "lost", "r1")
        with self.assertRaises(ValueError):
            crm.transfer(opp_id, "r2", "m1")
        self.assertEqual(crm.opps[opp_id]["owner"], "r1")

    def test_same_owner(self):
        crm, opp_id = self.make_opp()
        with self.assertRaises(ValueError):
            crm.transfer(opp_id, "r1", "m1")
        self.assertEqual(crm.opps[opp_id]["owner"], "r1")
        self.assertEqual(len(crm.log), 3)

    def test_new_owner_at_capacity(self):
        crm = build()  # r2 cap 1
        crm.add_lead("a@gmail.com", "A", "referral", "m1")  # L1 r1
        crm.add_lead("b@gmail.com", "B", "web", "m1")      # L2 r2 (full)
        crm.qualify("L1", "r1")
        crm.convert("L1", 1000, "r1")
        with self.assertRaises(ValueError):
            crm.transfer("O1", "r2", "m1")
        self.assertEqual(crm.opps["O1"]["owner"], "r1")

    def test_transfer_logs_and_changes_owner(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 2},
            {"id": "r2", "role": "rep", "capacity": 4},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        crm.add_lead("a@gmail.com", "A", "referral", "m1")  # L1 r1
        crm.add_lead("b@gmail.com", "B", "web", "m1")      # L2 r2
        crm.add_lead("c@gmail.com", "C", "referral", "m1") # L3 r1
        crm.add_lead("d@gmail.com", "D", "web", "m1")      # L4 r2
        crm.add_lead("e@gmail.com", "E", "web", "m1")      # L5 r2
        crm.qualify("L1", "r1")
        crm.convert("L1", 1000, "r1")  # O1; r1 load: L3 + O1 = 2
        crm.transfer("O1", "r2", "m1")  # r2 load 2 < 3
        self.assertEqual(crm.opps["O1"]["owner"], "r2")
        self.assertEqual(crm.log[-1], ("transfer", "O1", "m1"))
        # queue is empty, so no "assign" entries follow
        self.assertNotIn("assign", [e[0] for e in crm.log])

    def test_transfer_blocked_while_lead_is_waiting(self):
        # When the FIFO queue is non-empty every rep is at capacity, so
        # check 6 (new_owner below capacity) always fails.
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 2},
            {"id": "r2", "role": "rep", "capacity": 2},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        crm.add_lead("a@gmail.com", "A", "referral", "m1")  # L1 r1
        crm.add_lead("b@gmail.com", "B", "web", "m1")      # L2 r2
        crm.add_lead("c@gmail.com", "C", "referral", "m1") # L3 r1
        crm.add_lead("d@gmail.com", "D", "web", "m1")      # L4 r2
        waiting = crm.add_lead("e@gmail.com", "E", "web", "m1")  # L5 waiting
        crm.qualify("L1", "r1")
        crm.convert("L1", 1000, "r1")  # O1; r1 load: L3 + O1 = 2
        with self.assertRaises(ValueError):
            crm.transfer("O1", "r2", "m1")  # r2 load 2 == capacity
        self.assertEqual(crm.opps["O1"]["owner"], "r1")
        self.assertIsNone(crm.leads[waiting]["owner"])

    def test_transfer_twice(self):
        crm = build()
        crm.add_lead("a@gmail.com", "A", "referral", "m1")  # L1 r1
        crm.qualify("L1", "r1")
        crm.convert("L1", 1000, "r1")
        crm.transfer("O1", "r2", "m1")
        self.assertEqual(crm.opps["O1"]["owner"], "r2")
        # r2 is now at capacity (cap 1) so a transfer back to r2 is a
        # same-owner error; transferring back to r1 is fine.
        with self.assertRaises(ValueError):
            crm.transfer("O1", "r2", "m1")
        crm.transfer("O1", "r1", "m1")
        self.assertEqual(crm.opps["O1"]["owner"], "r1")


if __name__ == "__main__":
    unittest.main()
