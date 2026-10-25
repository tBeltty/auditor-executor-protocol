import copy
import unittest

from crm import CRM, DuplicateLeadError


def make_crm(reps=None):
    if reps is None:
        reps = [
            {"id": "r1", "role": "rep", "capacity": 2},
            {"id": "r2", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 0},
        ]
    return CRM(reps)


def qualified_lead(crm, email="lead@corp.com", name="Lead", source="referral", actor="r1"):
    lead_id = crm.add_lead(email, name, source, actor)
    crm.qualify(lead_id, actor)
    return lead_id


def snapshot(crm):
    return (
        copy.deepcopy(crm.leads),
        copy.deepcopy(crm.opps),
        list(crm.log),
        list(crm.waiting),
    )


class CheckOrderTests(unittest.TestCase):
    def test_add_lead_actor_before_payload(self):
        crm = make_crm()
        with self.assertRaises(PermissionError):
            crm.add_lead(123, None, "nope", "ghost")
        self.assertEqual(snapshot(crm), ({}, {}, [], []))

    def test_add_lead_email_before_name_before_source(self):
        crm = make_crm()
        with self.assertRaises(ValueError):
            crm.add_lead("bad", None, "nope", "r1")
        with self.assertRaises(ValueError):
            crm.add_lead("a@b.com", None, "nope", "r1")
        self.assertEqual(crm.leads, {})

    def test_convert_amount_before_permission(self):
        crm = make_crm()
        qualified_lead(crm)
        with self.assertRaises(ValueError):
            crm.convert("L1", 0, "r2")
        self.assertEqual(crm.opps, {})

    def test_advance_stage_before_permission(self):
        crm = make_crm()
        qualified_lead(crm)
        opp = crm.convert("L1", 100, "r1")
        with self.assertRaises(ValueError):
            crm.advance(opp, "closed", "r2")

    def test_discount_pct_before_permission(self):
        crm = make_crm()
        qualified_lead(crm)
        opp = crm.convert("L1", 100, "r1")
        with self.assertRaises(ValueError):
            crm.discount(opp, 0, "r2")

    def test_transfer_manager_before_target(self):
        crm = make_crm()
        qualified_lead(crm)
        opp = crm.convert("L1", 100, "r1")
        with self.assertRaises(PermissionError):
            crm.transfer(opp, "nobody", "r1")


class QueuedAssignmentTests(unittest.TestCase):
    def test_transfer_frees_slot_and_assigns_fifo(self):
        crm = make_crm([
            {"id": "r1", "role": "rep", "capacity": 2},
            {"id": "r2", "role": "rep", "capacity": 2},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        qualified_lead(crm, "a@corp.com")                 # L1 -> r1 (load 1)
        crm.add_lead("b@corp.com", "B", "web", "m1")      # L2 -> r2
        crm.add_lead("c@corp.com", "C", "web", "m1")      # L3 -> r1 (full)
        crm.add_lead("d@corp.com", "D", "web", "m1")      # L4 -> r2 (full)
        crm.add_lead("e@corp.com", "E", "web", "m1")      # L5 waiting
        crm.add_lead("f@corp.com", "F", "web", "m1")      # L6 waiting
        self.assertEqual(crm.waiting, ["L5", "L6"])
        opp = crm.convert("L1", 100, "r1")

        # A non-empty queue implies every rep is at capacity, so widen r2 to
        # make the transfer legal and exercise the slot-freeing path.
        crm.users["r2"]["capacity"] = 3
        crm.transfer(opp, "r2", "m1")
        # r1 load drops to 1, so exactly one waiting lead moves (FIFO).
        self.assertEqual(crm.leads["L5"]["owner"], "r1")
        self.assertEqual(crm.waiting, ["L6"])
        self.assertEqual(
            crm.log[-2:],
            [("transfer", opp, "m1"), ("assign", "L5", "system")],
        )

        # Winning the transferred opportunity frees an r2 slot for L6.
        crm.advance(opp, "proposal", "r2")
        crm.advance(opp, "negotiation", "r2")
        crm.advance(opp, "won", "r2")
        self.assertEqual(crm.leads["L6"]["owner"], "r2")
        self.assertEqual(crm.waiting, [])
        self.assertEqual(crm.log[-1], ("assign", "L6", "system"))

    def test_transfer_capacity_failure_does_not_assign(self):
        crm = make_crm([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        qualified_lead(crm, "a@corp.com")                 # L1 -> r1
        crm.add_lead("b@corp.com", "B", "web", "m1")      # L2 -> r2
        crm.add_lead("c@corp.com", "C", "web", "m1")      # L3 waiting
        opp = crm.convert("L1", 100, "r1")
        before = snapshot(crm)
        with self.assertRaises(ValueError):
            crm.transfer(opp, "r2", "m1")
        self.assertEqual(snapshot(crm), before)

    def test_advance_frees_only_available_slots(self):
        crm = make_crm([
            {"id": "r1", "role": "rep", "capacity": 2},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        qualified_lead(crm, "a@corp.com")                 # L1 -> r1
        crm.add_lead("b@corp.com", "B", "web", "m1")      # L2 -> r1 (now full)
        crm.add_lead("c@corp.com", "C", "web", "m1")      # L3 waiting
        crm.add_lead("d@corp.com", "D", "web", "m1")      # L4 waiting
        opp = crm.convert("L1", 100, "r1")
        # r1 load is 2 (L2 + O1) at capacity.
        crm.advance(opp, "proposal", "r1")
        crm.advance(opp, "negotiation", "r1")
        crm.advance(opp, "won", "r1")
        self.assertEqual(crm.leads["L3"]["owner"], "r1")
        self.assertEqual(crm.waiting, ["L4"])
        self.assertEqual(crm.log[-1], ("assign", "L3", "system"))

    def test_queue_is_fifo_across_multiple_frees(self):
        crm = make_crm([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        qualified_lead(crm, "a@corp.com")
        crm.add_lead("b@corp.com", "B", "web", "m1")
        crm.add_lead("c@corp.com", "C", "web", "m1")
        self.assertEqual(crm.waiting, ["L2", "L3"])
        opp = crm.convert("L1", 100, "r1")
        crm.advance(opp, "proposal", "r1")
        crm.advance(opp, "negotiation", "r1")
        crm.advance(opp, "won", "r1")
        self.assertEqual(crm.leads["L2"]["owner"], "r1")
        self.assertEqual(crm.waiting, ["L3"])
        self.assertEqual(crm.leads["L3"]["owner"], None)


class ManagerOwnershipTests(unittest.TestCase):
    def test_manager_acts_on_unowned_lead_but_convert_fails(self):
        crm = make_crm([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 1},
        ])
        crm.add_lead("a@corp.com", "A", "web", "m1")
        crm.add_lead("b@corp.com", "B", "referral", "m1")  # waiting, owner None
        crm.qualify("L2", "m1")
        self.assertEqual(crm.leads["L2"]["status"], "qualified")
        with self.assertRaises(ValueError):
            crm.convert("L2", 100, "m1")
        self.assertEqual(crm.opps, {})

    def test_convert_assigns_opportunity_to_lead_owner_not_actor(self):
        crm = make_crm()
        qualified_lead(crm)
        opp = crm.convert("L1", 100, "m1")
        self.assertEqual(crm.opps[opp]["owner"], "r1")
        self.assertEqual(crm.log[-1], ("convert", opp, "m1"))

    def test_manager_capacity_is_irrelevant_for_ownership(self):
        crm = CRM([{"id": "m1", "role": "manager", "capacity": 9}])
        lead = crm.add_lead("a@corp.com", "A", "referral", "m1")
        self.assertIsNone(crm.leads[lead]["owner"])


class LoadTests(unittest.TestCase):
    def test_lowest_load_receives_lead(self):
        crm = make_crm([
            {"id": "aa", "role": "rep", "capacity": 5},
            {"id": "zz", "role": "rep", "capacity": 5},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        crm.add_lead("a@corp.com", "A", "web", "m1")     # aa
        self.assertEqual(crm.leads["L1"]["owner"], "aa")
        crm.add_lead("b@corp.com", "B", "web", "m1")     # zz (aa load 1)
        self.assertEqual(crm.leads["L2"]["owner"], "zz")

    def test_converted_lead_releases_lead_slot_but_opp_holds_slot(self):
        crm = make_crm([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        qualified_lead(crm)
        crm.convert("L1", 100, "r1")
        crm.add_lead("b@corp.com", "B", "web", "m1")
        self.assertIsNone(crm.leads["L2"]["owner"])

    def test_final_stage_releases_slot(self):
        crm = make_crm([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        qualified_lead(crm)
        opp = crm.convert("L1", 100, "r1")
        crm.advance(opp, "lost", "r1")
        crm.add_lead("b@corp.com", "B", "web", "m1")
        self.assertEqual(crm.leads["L2"]["owner"], "r1")


class ScoreAndIdTests(unittest.TestCase):
    def test_score_matrix(self):
        crm = make_crm()
        cases = [
            ("w@gmail.com", "web", 10),
            ("x@corp.com", "web", 25),
            ("y@yahoo.com", "referral", 30),
            ("z@corp.com", "referral", 45),
            ("e@outlook.com", "event", 20),
            ("f@corp.com", "event", 35),
        ]
        for i, (email, source, expected) in enumerate(cases):
            lead_id = crm.add_lead(email, "N", source, "m1")
            self.assertEqual(crm.leads[lead_id]["score"], expected, email)
            self.assertEqual(lead_id, "L%d" % (i + 1))

    def test_failed_creations_do_not_consume_ids(self):
        crm = make_crm()
        with self.assertRaises(ValueError):
            crm.add_lead("bad", "N", "web", "m1")
        with self.assertRaises(ValueError):
            crm.add_lead("a@b.com", "", "web", "m1")
        self.assertEqual(crm.add_lead("a@b.com", "N", "web", "m1"), "L1")
        with self.assertRaises(DuplicateLeadError):
            crm.add_lead("a@b.com", "N", "web", "m1")
        self.assertEqual(crm.add_lead("c@d.com", "N", "web", "m1"), "L2")


class DiscountForecastTests(unittest.TestCase):
    def test_forecast_uses_discounted_amount(self):
        crm = make_crm([
            {"id": "r1", "role": "rep", "capacity": 5},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        qualified_lead(crm)
        opp = crm.convert("L1", 10000, "r1")
        crm.discount(opp, 10, "r1")
        self.assertEqual(crm.forecast(), {"open": 1, "weighted": 900, "won": 0})
        crm.advance(opp, "proposal", "r1")
        crm.advance(opp, "negotiation", "r1")
        crm.advance(opp, "won", "r1")
        self.assertEqual(crm.forecast(), {"open": 0, "weighted": 0, "won": 9000})

    def test_manager_may_discount_thirty(self):
        crm = make_crm([
            {"id": "r1", "role": "rep", "capacity": 5},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        qualified_lead(crm)
        opp = crm.convert("L1", 100, "r1")
        crm.discount(opp, 30, "m1")
        self.assertEqual(crm.opps[opp]["amount"], 70)
        with self.assertRaises(ValueError):
            crm.discount(opp, 1, "m1")

    def test_rep_may_stack_two_ten_percent_discounts(self):
        crm = make_crm([
            {"id": "r1", "role": "rep", "capacity": 5},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        qualified_lead(crm)
        opp = crm.convert("L1", 1000, "r1")
        crm.discount(opp, 10, "r1")
        crm.discount(opp, 10, "r1")
        self.assertEqual(crm.opps[opp]["amount"], 810)
        self.assertEqual(crm.opps[opp]["original_amount"], 1000)

    def test_discount_on_won_rejected(self):
        crm = make_crm([
            {"id": "r1", "role": "rep", "capacity": 5},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        qualified_lead(crm)
        opp = crm.convert("L1", 1000, "r1")
        crm.advance(opp, "proposal", "r1")
        crm.advance(opp, "negotiation", "r1")
        crm.advance(opp, "won", "r1")
        with self.assertRaises(ValueError):
            crm.discount(opp, 5, "m1")


class NoLogTests(unittest.TestCase):
    def test_forecast_is_side_effect_free(self):
        crm = make_crm()
        qualified_lead(crm)
        crm.convert("L1", 100, "r1")
        before = snapshot(crm)
        crm.forecast()
        crm.forecast()
        self.assertEqual(snapshot(crm), before)

    def test_log_entries_are_three_tuples(self):
        crm = make_crm()
        qualified_lead(crm)
        opp = crm.convert("L1", 100, "r1")
        crm.advance(opp, "proposal", "r1")
        for entry in crm.log:
            self.assertIsInstance(entry, tuple)
            self.assertEqual(len(entry), 3)


if __name__ == "__main__":
    unittest.main()
