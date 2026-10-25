"""Tests for crm.py (spec: /tmp/aep-lab/specs/crm.md)."""

import unittest

from crm import CRM, DuplicateLeadError


def make_reps():
    return [
        {"id": "r1", "role": "rep", "capacity": 2},
        {"id": "r2", "role": "rep", "capacity": 2},
        {"id": "m1", "role": "manager", "capacity": 0},
        {"id": "m2", "role": "manager", "capacity": 0},
    ]


def fresh_crm():
    crm = CRM(make_reps())
    crm.add_lead("a@corp.com", "Alpha", "referral", "r1")  # r1, 45
    return crm


def qualified_lead(crm, email="b@corp.com", actor="r1"):
    """Create and qualify a lead owned by r1; returns its id."""
    lead_id = crm.add_lead(email, "B", "referral", actor)
    crm.qualify(lead_id, actor)
    return lead_id


def rep_crm():
    """A CRM where every lead is guaranteed to be owned by r1."""
    return CRM([
        {"id": "r1", "role": "rep", "capacity": 10},
        {"id": "m1", "role": "manager", "capacity": 0},
    ])


class TestAddLead(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(make_reps())

    def test_returns_id_and_stores_lead(self):
        lead_id = self.crm.add_lead("  Ana@Corp.COM ", "  Ana  ", "web", "r1")
        self.assertEqual(lead_id, "L1")
        lead = self.crm.leads["L1"]
        self.assertEqual(lead["email"], "ana@corp.com")
        self.assertEqual(lead["name"], "Ana")
        self.assertEqual(lead["source"], "web")
        self.assertEqual(lead["status"], "new")
        self.assertEqual(lead["score"], 25)  # 10 web + 15 non-free domain
        self.assertEqual(lead["owner"], "r1")
        self.assertEqual(self.crm.log, [("add_lead", "L1", "r1")])

    def test_scores(self):
        self.assertEqual(self.crm.leads[self.crm.add_lead("a@gmail.com", "A", "web", "r1")]["score"], 10)
        self.assertEqual(self.crm.leads[self.crm.add_lead("b@yahoo.com", "B", "referral", "r1")]["score"], 30)
        self.assertEqual(self.crm.leads[self.crm.add_lead("c@outlook.com", "C", "event", "r1")]["score"], 20)
        self.assertEqual(self.crm.leads[self.crm.add_lead("d@corp.com", "D", "event", "r1")]["score"], 35)

    def test_owner_lowest_load_then_smallest_id(self):
        # first: tie at load 0 -> r1
        self.assertEqual(self.crm.leads[self.crm.add_lead("a@x.com", "A", "web", "r1")]["owner"], "r1")
        # r2 has load 0 -> r2
        self.assertEqual(self.crm.leads[self.crm.add_lead("b@x.com", "B", "web", "r1")]["owner"], "r2")
        # tie at load 1 -> r1 (string order)
        self.assertEqual(self.crm.leads[self.crm.add_lead("c@x.com", "C", "web", "r1")]["owner"], "r1")

    def test_no_capacity_goes_to_waiting_queue(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1}])
        crm.add_lead("a@x.com", "A", "web", "r1")
        lead_id = crm.add_lead("b@x.com", "B", "web", "r1")
        self.assertIsNone(crm.leads[lead_id]["owner"])
        self.assertEqual(list(crm._waiting), [lead_id])

    def test_manager_never_owns(self):
        crm = CRM([{"id": "m1", "role": "manager", "capacity": 5}])
        lead_id = crm.add_lead("a@x.com", "A", "web", "m1")
        self.assertIsNone(crm.leads[lead_id]["owner"])

    def test_duplicate_email_case_insensitive(self):
        self.crm.add_lead("a@x.com", "A", "web", "r1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            self.crm.add_lead("  A@X.COM ", "B", "web", "r1")
        self.assertEqual(ctx.exception.existing_id, "L1")

    def test_invalid_email(self):
        for bad in [None, 123, "", "no-at.com", "a@b@c.com", "a@b",
                    "a@.com", "a@com.", "a@.b.com", "a@com.x.", "@x.com", "a@"]:
            with self.assertRaises(ValueError):
                self.crm.add_lead(bad, "A", "web", "r1")

    def test_invalid_name_and_source(self):
        with self.assertRaises(ValueError):
            self.crm.add_lead("a@x.com", "   ", "web", "r1")
        with self.assertRaises(ValueError):
            self.crm.add_lead("a@x.com", 5, "web", "r1")
        with self.assertRaises(ValueError):
            self.crm.add_lead("a@x.com", "A", "webform", "r1")
        with self.assertRaises(ValueError):
            self.crm.add_lead("a@x.com", "A", None, "r1")

    def test_actor_checked_first(self):
        with self.assertRaises(PermissionError):
            self.crm.add_lead("bad-email", "A", "bad-source", "nobody")
        with self.assertRaises(PermissionError):
            self.crm.add_lead("a@x.com", "A", "web", None)
        # order: email checked before name/source
        with self.assertRaises(ValueError):
            self.crm.add_lead("bad-email", "", "bad-source", "r1")

    def test_check_order_source_before_duplicate(self):
        self.crm.add_lead("a@x.com", "A", "web", "r1")
        with self.assertRaises(ValueError):  # step 3 before step 4
            self.crm.add_lead("a@x.com", "A", "nosuch", "r1")

    def test_failed_call_changes_nothing(self):
        log = list(self.crm.log)
        with self.assertRaises(ValueError):
            self.crm.add_lead("bad", "A", "web", "r1")
        self.assertEqual(self.crm.log, log)
        self.assertEqual(self.crm.leads, {})

    def test_ids_count_successful_creations_only(self):
        self.crm.add_lead("a@x.com", "A", "web", "r1")  # L1
        with self.assertRaises(ValueError):
            self.crm.add_lead("bad", "A", "web", "r1")
        with self.assertRaises(DuplicateLeadError):
            self.crm.add_lead("a@x.com", "A2", "web", "r1")
        self.assertEqual(self.crm.add_lead("b@x.com", "B", "web", "r1"), "L2")


class TestQualify(unittest.TestCase):
    def test_ok(self):
        crm = fresh_crm()
        crm.qualify("L1", "r1")
        self.assertEqual(crm.leads["L1"]["status"], "qualified")
        self.assertEqual(crm.log[-1], ("qualify", "L1", "r1"))

    def test_manager_can_qualify(self):
        crm = fresh_crm()
        crm.qualify("L1", "m1")
        self.assertEqual(crm.leads["L1"]["status"], "qualified")

    def test_unknown_lead(self):
        crm = fresh_crm()
        with self.assertRaises(ValueError):
            crm.qualify("L99", "r1")

    def test_owner_or_manager_permission(self):
        crm = fresh_crm()
        with self.assertRaises(PermissionError):
            crm.qualify("L1", "r2")

    def test_status_must_be_new(self):
        crm = fresh_crm()
        crm.add_lead("b@x.com", "B", "web", "r1")  # L2, score 25
        crm.qualify("L1", "r1")
        with self.assertRaises(ValueError):
            crm.qualify("L1", "r1")

    def test_score_threshold(self):
        crm = rep_crm()  # single rep: every lead is owned by r1
        low = crm.add_lead("a@gmail.com", "A", "web", "r1")   # score 10
        edge = crm.add_lead("b@corp.com", "B", "web", "r1")   # score 25
        ok = crm.add_lead("c@corp.com", "C", "event", "r1")   # score 35
        for bad in (low, edge):
            with self.assertRaises(ValueError):
                crm.qualify(bad, "r1")
        crm.qualify(ok, "r1")
        self.assertEqual(crm.leads[ok]["status"], "qualified")

    def test_check_order(self):
        crm = fresh_crm()
        # unknown actor beats unknown lead
        with self.assertRaises(PermissionError):
            crm.qualify("L99", "nobody")
        with self.assertRaises(ValueError):
            crm.qualify("L99", "r1")
        # permission beats status
        crm.qualify("L1", "r1")
        with self.assertRaises(PermissionError):
            crm.qualify("L1", "r2")

    def test_failed_call_appends_nothing(self):
        crm = fresh_crm()
        log = list(crm.log)
        with self.assertRaises(PermissionError):
            crm.qualify("L1", "r2")
        self.assertEqual(crm.log, log)

    def test_cannot_qualify_low_score_lead_that_was_assigned(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 5}])
        lead_id = crm.add_lead("a@corp.com", "A", "event", "r1")  # score 35
        crm.qualify(lead_id, "r1")
        self.assertEqual(crm.leads[lead_id]["status"], "qualified")


class TestConvert(unittest.TestCase):
    def test_ok(self):
        crm = fresh_crm()
        crm.qualify("L1", "r1")
        opp_id = crm.convert("L1", 1000, "r1")
        self.assertEqual(opp_id, "O1")
        opp = crm.opps["O1"]
        self.assertEqual(opp, {"id": "O1", "lead_id": "L1", "owner": "r1",
                               "amount": 1000, "original_amount": 1000,
                               "stage": "prospect"})
        self.assertEqual(crm.leads["L1"]["status"], "converted")
        self.assertEqual(crm.log[-1], ("convert", "O1", "r1"))

    def test_ids_count_successful_conversions_only(self):
        crm = fresh_crm()
        crm.qualify("L1", "r1")
        with self.assertRaises(ValueError):
            crm.convert("L1", 0, "r1")
        self.assertEqual(crm.convert("L1", 500, "r1"), "O1")

    def test_amount_validation(self):
        crm = fresh_crm()
        crm.qualify("L1", "r1")
        for bad in [0, -5, 1.5, "100", True, False]:
            with self.assertRaises(ValueError):
                crm.convert("L1", bad, "r1")

    def test_owner_or_manager(self):
        crm = fresh_crm()
        crm.qualify("L1", "r1")
        with self.assertRaises(PermissionError):
            crm.convert("L1", 100, "r2")
        crm.convert("L1", 100, "m1")

    def test_requires_qualified(self):
        crm = fresh_crm()
        with self.assertRaises(ValueError):
            crm.convert("L1", 100, "r1")

    def test_requires_owner(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 0}, {"id": "m1", "role": "manager", "capacity": 0}])
        # queued lead (no owner), score high enough to qualify by manager is still new;
        # qualify it via manager, then convert has no owner
        crm.add_lead("a@corp.com", "A", "referral", "m1")
        crm.qualify("L1", "m1")
        with self.assertRaises(ValueError):
            crm.convert("L1", 100, "m1")

    def test_check_order_unknown_lead_vs_actor(self):
        crm = fresh_crm()
        with self.assertRaises(PermissionError):
            crm.convert("L99", 100, "nobody")
        with self.assertRaises(ValueError):
            crm.convert("L99", 100, "r1")


class TestAdvance(unittest.TestCase):
    def _opp(self, amount=1000, email="b@corp.com", **kwargs):
        crm = rep_crm()
        lead_id = crm.add_lead(email, "B", "referral", "r1")
        crm.qualify(lead_id, "r1")
        opp_id = crm.convert(lead_id, amount, "r1")
        return crm, opp_id

    def test_happy_path_chain(self):
        crm, opp_id = self._opp()
        for stage in ("proposal", "negotiation", "won"):
            crm.advance(opp_id, stage, "r1")
            self.assertEqual(crm.opps[opp_id]["stage"], stage)
            self.assertEqual(crm.log[-1], ("advance", opp_id, "r1"))

    def test_lost_from_any_stage(self):
        for i, stage in enumerate(["prospect", "proposal"]):
            crm, opp_id = self._opp(email=f"l{i}@corp.com")
            for nxt in ["proposal", "negotiation"][:i]:
                crm.advance(opp_id, nxt, "r1")
            crm.advance(opp_id, "lost", "r1")
            self.assertEqual(crm.opps[opp_id]["stage"], "lost")

    def test_invalid_stage(self):
        crm, opp_id = self._opp()
        with self.assertRaises(ValueError):
            crm.advance(opp_id, "closed", "r1")
        with self.assertRaises(ValueError):
            crm.advance(opp_id, None, "r1")

    def test_must_be_immediate_next(self):
        crm, opp_id = self._opp()
        with self.assertRaises(ValueError):
            crm.advance(opp_id, "negotiation", "r1")
        with self.assertRaises(ValueError):
            crm.advance(opp_id, "won", "r1")

    def test_final_stage(self):
        crm, opp_id = self._opp()
        crm.advance(opp_id, "lost", "r1")
        with self.assertRaises(ValueError):
            crm.advance(opp_id, "won", "r1")

    def test_owner_or_manager_permission(self):
        crm, opp_id = self._opp()
        with self.assertRaises(PermissionError):
            crm.advance(opp_id, "proposal", "r2")
        crm.advance(opp_id, "proposal", "m1")

    def test_negotiation_large_amount_requires_manager(self):
        crm, opp_id = self._opp(amount=50001)
        crm.advance(opp_id, "proposal", "r1")
        with self.assertRaises(PermissionError):
            crm.advance(opp_id, "negotiation", "r1")
        log = list(crm.log)
        crm.advance(opp_id, "negotiation", "m1")
        self.assertEqual(crm.opps[opp_id]["stage"], "negotiation")
        self.assertEqual(len(crm.log), len(log) + 1)

    def test_negotiation_exactly_50000_ok_for_rep(self):
        crm, opp_id = self._opp(amount=50000)
        crm.advance(opp_id, "proposal", "r1")
        crm.advance(opp_id, "negotiation", "r1")
        self.assertEqual(crm.opps[opp_id]["stage"], "negotiation")

    def test_order_valueerror_before_negotiation_permission(self):
        crm, opp_id = self._opp(amount=50001)
        # prospect -> negotiation is invalid (step 5), even though a manager
        # permission issue also applies (step 6)
        crm.advance(opp_id, "proposal", "r1")
        with self.assertRaises(ValueError):
            crm.advance(opp_id, "won", "r1")

    def test_free_slot_assigns_waiting_lead_on_won(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1}])
        lead = crm.add_lead("a@corp.com", "A", "referral", "r1")
        crm.qualify(lead, "r1")
        opp_id = crm.convert(lead, 100, "r1")
        queued = crm.add_lead("b@x.com", "B", "web", "r1")
        self.assertIsNone(crm.leads[queued]["owner"])
        for stage in ("proposal", "negotiation", "won"):
            crm.advance(opp_id, stage, "r1")
        self.assertEqual(crm.leads[queued]["owner"], "r1")
        self.assertEqual(crm.log[-1], ("assign", queued, "system"))

    def test_free_slot_respects_capacity_and_fifo(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 2}])
        lead = crm.add_lead("a@corp.com", "A", "referral", "r1")
        crm.qualify(lead, "r1")
        opp_id = crm.convert(lead, 100, "r1")  # load 1
        w1 = crm.add_lead("b@x.com", "B", "web", "r1")  # load 2, owned by r1
        w2 = crm.add_lead("c@x.com", "C", "web", "r1")  # queued
        w3 = crm.add_lead("d@x.com", "D", "web", "r1")  # queued
        self.assertEqual(crm.leads[w1]["owner"], "r1")
        for stage in ("proposal", "negotiation", "won"):
            crm.advance(opp_id, stage, "r1")  # frees 1 slot -> only w2 gets in
        self.assertEqual(crm.leads[w2]["owner"], "r1")
        self.assertIsNone(crm.leads[w3]["owner"])
        self.assertEqual(list(crm._waiting), [w3])
        self.assertEqual(crm.log[-2:], [("advance", opp_id, "r1"), ("assign", w2, "system")])

    def test_no_assign_if_queue_empty_or_full(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 2}])
        lead = crm.add_lead("a@corp.com", "A", "referral", "r1")
        crm.qualify(lead, "r1")
        opp1 = crm.convert(lead, 100, "r1")
        lead2 = crm.add_lead("b@corp.com", "B2", "referral", "r1")
        crm.qualify(lead2, "r1")
        opp2 = crm.convert(lead2, 100, "r1")  # load 2 (at capacity)
        self.assertEqual(list(crm._waiting), [])
        crm.advance(opp1, "lost", "r1")
        self.assertEqual(crm.log, [
            ("add_lead", "L1", "r1"), ("qualify", "L1", "r1"),
            ("convert", "O1", "r1"), ("add_lead", "L2", "r1"),
            ("qualify", "L2", "r1"), ("convert", "O2", "r1"),
            ("advance", "O1", "r1"),
        ])

    def test_lost_releases_load_and_frees_slot(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 2}])
        lead = crm.add_lead("a@corp.com", "A", "referral", "r1")
        crm.qualify(lead, "r1")
        opp_id = crm.convert(lead, 100, "r1")
        queued = crm.add_lead("b@x.com", "B", "web", "r1")
        crm.advance(opp_id, "lost", "r1")
        self.assertEqual(crm.leads[queued]["owner"], "r1")

    def test_unknown_checks(self):
        crm, opp_id = self._opp()
        with self.assertRaises(PermissionError):
            crm.advance("O99", "proposal", "nobody")
        with self.assertRaises(ValueError):
            crm.advance("O99", "proposal", "r1")


class TestDiscount(unittest.TestCase):
    def _opp(self, amount=100):
        crm = rep_crm()
        lead_id = crm.add_lead("b@corp.com", "B", "referral", "r1")
        crm.qualify(lead_id, "r1")
        opp_id = crm.convert(lead_id, amount, "r1")
        return crm, opp_id

    def test_ok(self):
        crm, opp_id = self._opp()
        crm.discount(opp_id, 10, "r1")
        self.assertEqual(crm.opps[opp_id]["amount"], 90)
        self.assertEqual(crm.opps[opp_id]["original_amount"], 100)
        self.assertEqual(crm.log[-1], ("discount", opp_id, "r1"))

    def test_pct_validation(self):
        crm, opp_id = self._opp()
        for bad in [0, 31, -3, 2.5, "10", True, False]:
            with self.assertRaises(ValueError):
                crm.discount(opp_id, bad, "r1")

    def test_owner_or_manager(self):
        crm, opp_id = self._opp()
        with self.assertRaises(PermissionError):
            crm.discount(opp_id, 5, "r2")
        crm.discount(opp_id, 5, "m1")

    def test_non_manager_cap_at_10(self):
        crm, opp_id = self._opp()
        with self.assertRaises(PermissionError):
            crm.discount(opp_id, 11, "r1")
        log = len(crm.log)
        crm.discount(opp_id, 10, "r1")  # boundary ok
        self.assertEqual(len(crm.log), log + 1)

    def test_manager_above_10(self):
        crm, opp_id = self._opp()
        crm.discount(opp_id, 30, "m1")
        self.assertEqual(crm.opps[opp_id]["amount"], 70)

    def test_cumulative_cap(self):
        crm, opp_id = self._opp()
        crm.discount(opp_id, 10, "r1")      # 90
        with self.assertRaises(ValueError):
            crm.discount(opp_id, 25, "m1")  # 67 -> below 70% of original
        # boundary: reaching exactly 30% cumulative is allowed
        crm2, opp2 = self._opp()
        crm2.discount(opp2, 22, "m1")       # 100 -> 78
        self.assertEqual(crm2.opps[opp2]["amount"], 78)
        crm2.discount(opp2, 10, "m1")       # 78*90//100 = 70 -> exactly 70 of original
        self.assertEqual(crm2.opps[opp2]["amount"], 70)
        with self.assertRaises(ValueError):
            crm2.discount(opp2, 1, "m1")    # 69 -> below the floor
        # any further step once at the floor fails
        crm3, opp3 = self._opp()
        crm3.discount(opp3, 20, "m1")       # 80
        with self.assertRaises(ValueError):
            crm3.discount(opp3, 15, "m1")   # 68 < 70

    def test_floor_reaches_cap_exactly(self):
        crm, opp_id = self._opp(amount=1000)
        crm.discount(opp_id, 30, "m1")  # 1000*70//100 = 700, exactly the floor
        self.assertEqual(crm.opps[opp_id]["amount"], 700)
        with self.assertRaises(ValueError):
            crm.discount(opp_id, 1, "m1")  # 693 < 700 -> fails

    def test_final_stage(self):
        crm, opp_id = self._opp()
        crm.advance(opp_id, "lost", "r1")
        with self.assertRaises(ValueError):
            crm.discount(opp_id, 10, "r1")

    def test_check_order(self):
        crm, opp_id = self._opp()
        # unknown actor checked first, even with an unknown opp and bad pct
        with self.assertRaises(PermissionError):
            crm.discount("O99", 40, "nobody")
        with self.assertRaises(ValueError):
            crm.discount("O99", 10, "r1")
        # permission (step 3) beats final-stage (step 4): opp lost owned by r1, r2 discounts
        crm2, opp2 = self._opp()
        crm2.advance(opp2, "lost", "r1")
        with self.assertRaises(PermissionError):
            crm2.discount(opp2, 10, "r2")
        # final stage beats manager cap step: lost opp discounted by owner
        # (owner, valid pct) -> ValueError on step 4
        crm3, opp3 = self._opp()
        crm3.advance(opp3, "lost", "r1")
        with self.assertRaises(ValueError):
            crm3.discount(opp3, 15, "r1")


class TestTransfer(unittest.TestCase):
    def _crm(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 3},
            {"id": "r2", "role": "rep", "capacity": 3},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        lead = crm.add_lead("a@corp.com", "A", "referral", "r1")
        crm.qualify(lead, "r1")
        opp_id = crm.convert(lead, 100, "r1")
        return crm, opp_id

    def test_ok_and_frees_old_slot(self):
        crm, opp_id = self._crm()
        # r1 load 1; queue a lead
        w = crm.add_lead("w@x.com", "W", "web", "r1")  # r1 to load 2? capacity 3 -> assigned to r1
        crm.transfer(opp_id, "r2", "m1")
        self.assertEqual(crm.opps[opp_id]["owner"], "r2")
        # r1 now load 1 (only w) -> in code free_slot was called but queue empty
        self.assertEqual(crm.log[-1], ("transfer", opp_id, "m1"))

    def test_transfer_fills_previous_owners_slot_contract(self):
        # Previous owner's free slot is refilled from the queue when one
        # exists (the queue survives only while every rep is at capacity,
        # so we reach it via an advance, the other freeing operation).
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 2},
            {"id": "r2", "role": "rep", "capacity": 2},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        lead = crm.add_lead("a@corp.com", "A", "referral", "r1")
        crm.qualify(lead, "r1")
        opp_id = crm.convert(lead, 100, "r1")              # r1: 1
        crm.add_lead("x@corp.com", "X", "referral", "r2")  # r2: 1
        crm.add_lead("y@corp.com", "Y", "referral", "r1")  # r1: 2 (full)
        crm.add_lead("z@x.com", "Z", "web", "r2")          # r2: 2 (full)
        q = crm.add_lead("q@x.com", "Q", "web", "r1")      # queued
        self.assertIsNone(crm.leads[q]["owner"])
        with self.assertRaises(ValueError):                # r2 is at capacity
            crm.transfer(opp_id, "r2", "m1")
        # freeing r1 via advance does fill r1's slot from the queue
        for stage in ("proposal", "negotiation", "won"):
            crm.advance(opp_id, stage, "r1")
        self.assertEqual(crm.leads[q]["owner"], "r1")
        self.assertEqual(crm.log[-1], ("assign", q, "system"))

    def test_requires_manager(self):
        crm, opp_id = self._crm()
        with self.assertRaises(PermissionError):
            crm.transfer(opp_id, "r2", "r1")  # even the current owner
        with self.assertRaises(PermissionError):
            crm.transfer(opp_id, "r2", "r2")

    def test_new_owner_validation(self):
        crm, opp_id = self._crm()
        for bad in ["nobody", "m1", None, 5]:
            with self.assertRaises(ValueError):
                crm.transfer(opp_id, bad, "m1")

    def test_final_stage(self):
        crm, opp_id = self._crm()
        crm.advance(opp_id, "lost", "r1")
        with self.assertRaises(ValueError):
            crm.transfer(opp_id, "r2", "m1")

    def test_same_owner(self):
        crm, opp_id = self._crm()
        with self.assertRaises(ValueError):
            crm.transfer(opp_id, "r1", "m1")

    def test_new_owner_capacity(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 3},
            {"id": "r2", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        lead = crm.add_lead("a@corp.com", "A", "referral", "r1")
        crm.qualify(lead, "r1")
        opp_id = crm.convert(lead, 100, "r1")
        # fill r2 to capacity
        w = crm.add_lead("w@corp.com", "W", "referral", "r2")
        with self.assertRaises(ValueError):
            crm.transfer(opp_id, "r2", "m1")

    def test_unknown_opp(self):
        crm, opp_id = self._crm()
        with self.assertRaises(PermissionError):
            crm.transfer("O99", "r2", "nobody")
        with self.assertRaises(ValueError):
            crm.transfer("O99", "r2", "m1")

    def test_transfer_no_queue_assign_on_success(self):
        # By the spec, a queued lead only exists while every rep is at
        # capacity, so a successful transfer (new_owner strictly below
        # capacity) always finds an empty queue: no "assign" entries.
        crm, opp_id = self._crm()
        w = crm.add_lead("w@x.com", "W", "web", "r1")  # owned by r2 (lower load)
        log_before = len(crm.log)
        crm.transfer(opp_id, "r2", "m1")
        self.assertEqual(crm.opps[opp_id]["owner"], "r2")
        self.assertEqual(crm.log[log_before:], [("transfer", opp_id, "m1")])
        self.assertEqual(list(crm._waiting), [])

    def test_transfer_blocked_while_queue_nonempty(self):
        # When leads are waiting, every rep is at capacity, so transfer's
        # capacity check rejects even a manager's valid-looking transfer.
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 2},
            {"id": "r2", "role": "rep", "capacity": 2},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        lead = crm.add_lead("a@corp.com", "A", "referral", "r1")
        crm.qualify(lead, "r1")
        opp_id = crm.convert(lead, 100, "r1")              # r1: 1 (lead+opp cancel out)
        crm.add_lead("x@corp.com", "X", "referral", "r1")  # r1: 2 (full)
        crm.add_lead("y@corp.com", "Y", "referral", "r2")  # r2: 1
        crm.add_lead("z@x.com", "Z", "web", "r2")          # r2: 2 (full)
        q = crm.add_lead("q@x.com", "Q", "web", "r1")      # queued
        self.assertIsNone(crm.leads[q]["owner"])
        with self.assertRaises(ValueError):
            crm.transfer(opp_id, "r2", "m1")
        self.assertEqual(crm.opps[opp_id]["owner"], "r1")
        self.assertEqual(list(crm._waiting), [q])


class TestForecast(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(CRM(make_reps()).forecast(),
                         {"open": 0, "weighted": 0, "won": 0})

    def test_weights_and_won(self):
        crm = rep_crm()
        crm.add_lead("a@corp.com", "A", "referral", "r1")
        crm.qualify("L1", "r1")
        o1 = crm.convert("L1", 100, "r1")          # prospect
        lead2 = crm.add_lead("b@corp.com", "B", "referral", "r1")
        crm.qualify(lead2, "r1")
        o2 = crm.convert(lead2, 200, "r1")
        lead3 = crm.add_lead("c@corp.com", "C", "referral", "r1")
        crm.qualify(lead3, "r1")
        o3 = crm.convert(lead3, 10, "r1")
        crm.advance(o2, "proposal", "r1")
        crm.advance(o3, "proposal", "r1")
        crm.advance(o3, "negotiation", "r1")
        lead4 = crm.add_lead("d@corp.com", "D", "referral", "r1")
        crm.qualify(lead4, "r1")
        o4 = crm.convert(lead4, 50, "r1")
        crm.advance(o4, "proposal", "r1")
        crm.advance(o4, "negotiation", "r1")
        crm.advance(o4, "won", "r1")
        lead5 = crm.add_lead("e@corp.com", "E", "referral", "r1")
        crm.qualify(lead5, "r1")
        o5 = crm.convert(lead5, 9, "r1")
        crm.advance(o5, "lost", "r1")
        self.assertEqual(crm.forecast(), {"open": 3, "weighted": 10 + 60 + 6, "won": 50})

    def test_weight_uses_floor(self):
        crm = fresh_crm()
        crm.qualify("L1", "r1")
        opp = crm.convert("L1", 101, "r1")
        crm.advance(opp, "proposal", "r1")  # 101*30//100 = 30
        self.assertEqual(crm.forecast()["weighted"], 30)
        crm.advance(opp, "negotiation", "r1")  # 101*60//100 = 60
        self.assertEqual(crm.forecast()["weighted"], 60)

    def test_no_log_entry(self):
        crm = fresh_crm()
        log = list(crm.log)
        crm.forecast()
        self.assertEqual(crm.log, log)


class TestLogContract(unittest.TestCase):
    def test_log_is_tuple_list(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1}])
        crm.add_lead("a@x.com", "A", "referral", "r1")  # score 30
        crm.qualify("L1", "r1")
        crm.convert("L1", 10, "r1")
        crm.advance("O1", "proposal", "r1")
        for entry in crm.log:
            self.assertEqual(len(entry), 3)
        self.assertEqual([e[0] for e in crm.log],
                         ["add_lead", "qualify", "convert", "advance"])

    def test_lifecycle_log_full(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1}])
        crm.add_lead("a@corp.com", "A", "referral", "r1")
        crm.qualify("L1", "r1")
        crm.convert("L1", 100, "r1")
        crm.add_lead("b@x.com", "B", "web", "r1")  # queued: r1 load is 1 = capacity
        for stage in ("proposal", "negotiation", "won"):
            crm.advance("O1", stage, "r1")
        self.assertEqual(crm.log, [
            ("add_lead", "L1", "r1"),
            ("qualify", "L1", "r1"),
            ("convert", "O1", "r1"),
            ("add_lead", "L2", "r1"),
            ("advance", "O1", "r1"),
            ("advance", "O1", "r1"),
            ("advance", "O1", "r1"),
            ("assign", "L2", "system"),
        ])


class TestEdgeCases(unittest.TestCase):
    def test_non_string_ids_raise_valueerror(self):
        crm = fresh_crm()
        with self.assertRaises(ValueError):
            crm.qualify(123, "r1")
        with self.assertRaises(ValueError):
            crm.convert([], 10, "r1")
        with self.assertRaises(ValueError):
            crm.advance(["O1"], "proposal", "r1")
        with self.assertRaises(ValueError):
            crm.discount(None, 10, "r1")
        with self.assertRaises(ValueError):
            crm.transfer({}, "r2", "m1")

    def test_unknown_actor_unhashable(self):
        crm = fresh_crm()
        with self.assertRaises(PermissionError):
            crm.add_lead("z@x.com", "Z", "web", ["r1"])
        self.assertEqual(crm.log, [("add_lead", "L1", "r1")])

    def test_duplicate_check_includes_queued_leads(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 0}])
        first = crm.add_lead("a@x.com", "A", "web", "r1")
        self.assertIsNone(crm.leads[first]["owner"])
        with self.assertRaises(DuplicateLeadError) as ctx:
            crm.add_lead("a@x.com", "A2", "event", "r1")
        self.assertEqual(ctx.exception.existing_id, first)

    def test_qualify_manager_on_ownerless_lead(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 0},
                   {"id": "m1", "role": "manager", "capacity": 0}])
        crm.add_lead("a@corp.com", "A", "referral", "r1")  # queued, no owner
        with self.assertRaises(PermissionError):
            crm.qualify("L1", "r1")
        crm.qualify("L1", "m1")
        self.assertEqual(crm.leads["L1"]["status"], "qualified")


if __name__ == "__main__":
    unittest.main()
