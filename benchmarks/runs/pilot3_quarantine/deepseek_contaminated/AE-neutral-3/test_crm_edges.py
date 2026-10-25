"""Additional unit tests for crm.py covering spec edges (spec: specs/crm.md)."""

import copy
import unittest

from crm import CRM, DuplicateLeadError


def new_crm(reps=None):
    default = [
        {"id": "r1", "role": "rep", "capacity": 5},
        {"id": "r2", "role": "rep", "capacity": 5},
        {"id": "m1", "role": "manager", "capacity": 0},
    ]
    return CRM(copy.deepcopy(default if reps is None else reps))


def owned_opp(crm, email="a@corp.com", amount=1000, source="referral"):
    lead_id = crm.add_lead(email, "Lead", source, "r1")
    owner = crm.leads[lead_id]["owner"]
    crm.qualify(lead_id, owner)
    opp_id = crm.convert(lead_id, amount, owner)
    return lead_id, opp_id, owner


class SnapshotMixin:
    def snapshot(self, crm):
        return copy.deepcopy((crm.leads, crm.opps, crm.log))

    def assert_unchanged(self, crm, fn, exc=ValueError):
        before = self.snapshot(crm)
        with self.assertRaises(exc):
            fn()
        self.assertEqual(self.snapshot(crm), before)


class TestOwnerSelection(SnapshotMixin, unittest.TestCase):
    def test_tie_break_is_lexicographic_string_order(self):
        crm = new_crm(
            [
                {"id": "r2", "role": "rep", "capacity": 5},
                {"id": "r10", "role": "rep", "capacity": 5},
                {"id": "m1", "role": "manager", "capacity": 5},
            ]
        )
        lid = crm.add_lead("a@corp.com", "A", "web", "m1")
        self.assertEqual(crm.leads[lid]["owner"], "r10")

    def test_lowest_load_wins_even_if_id_is_larger(self):
        crm = new_crm(
            [
                {"id": "r1", "role": "rep", "capacity": 5},
                {"id": "r2", "role": "rep", "capacity": 5},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        first = crm.add_lead("a@corp.com", "A", "referral", "r1")  # r1, load 1
        crm.qualify(first, "r1")
        crm.convert(first, 100, "r1")  # r1 lead -> opp, still load 1
        second = crm.add_lead("b@corp.com", "B", "referral", "r1")
        self.assertEqual(crm.leads[second]["owner"], "r2")

    def test_winning_an_opportunity_reopens_capacity(self):
        crm = new_crm(
            [
                {"id": "r1", "role": "rep", "capacity": 1},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        first, opp, owner = owned_opp(crm)
        crm.advance(opp, "proposal", owner)
        crm.advance(opp, "negotiation", owner)
        crm.advance(opp, "won", owner)
        nxt = crm.add_lead("b@corp.com", "B", "referral", "r1")
        self.assertEqual(crm.leads[nxt]["owner"], "r1")

    def test_full_queue_assigns_one_lead_per_freed_slot_in_fifo_order(self):
        crm = new_crm(
            [
                {"id": "r1", "role": "rep", "capacity": 1},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        first = crm.add_lead("a@corp.com", "A", "referral", "r1")
        second = crm.add_lead("b@corp.com", "B", "referral", "r1")
        third = crm.add_lead("c@corp.com", "C", "referral", "r1")
        self.assertIsNone(crm.leads[second]["owner"])
        self.assertIsNone(crm.leads[third]["owner"])

        crm.qualify(first, "r1")
        opp = crm.convert(first, 100, "r1")
        crm.advance(opp, "lost", "r1")
        self.assertEqual(crm.leads[second]["owner"], "r1")
        self.assertIsNone(crm.leads[third]["owner"])
        self.assertEqual(crm.log[-1], ("assign", second, "system"))

    def test_manager_may_qualify_unowned_lead_and_it_is_assigned_later(self):
        crm = new_crm(
            [
                {"id": "r1", "role": "rep", "capacity": 1},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        first = crm.add_lead("a@corp.com", "A", "referral", "r1")
        waiting = crm.add_lead("b@corp.com", "B", "referral", "r1")
        crm.qualify(waiting, "m1")
        self.assertEqual(crm.leads[waiting]["status"], "qualified")
        self.assertIsNone(crm.leads[waiting]["owner"])

        crm.qualify(first, "r1")
        opp = crm.convert(first, 100, "r1")
        crm.advance(opp, "lost", "r1")
        self.assertEqual(crm.leads[waiting]["owner"], "r1")
        self.assertEqual(crm.leads[waiting]["status"], "qualified")
        self.assertEqual(
            crm.log[-2:],
            [("advance", opp, "r1"), ("assign", waiting, "system")],
        )


class TestLeadEdges(SnapshotMixin, unittest.TestCase):
    def test_email_dotted_domain_boundaries(self):
        crm = new_crm()
        for email in ("a@b.c", "a@b.co", "a@sub.b.co", "e@B.Co "):
            crm.add_lead(email, "A", "web", "r1")
        accepted = [lead["email"] for lead in crm.leads.values()]
        self.assertEqual(accepted, ["a@b.c", "a@b.co", "a@sub.b.co", "e@b.co"])

        before = self.snapshot(crm)
        for email in ("a@.bc", "a@bc.", "a@.", "a@b", "a@", "@b.c", "a@b@c.d"):
            self.assert_unchanged(
                crm, lambda email=email: crm.add_lead(email, "A", "web", "r1")
            )
        self.assertEqual(self.snapshot(crm), before)

    def test_email_and_name_errors_precede_the_duplicate_check(self):
        crm = new_crm()
        first = crm.add_lead("dup@corp.com", "A", "web", "r1")
        self.assert_unchanged(
            crm, lambda: crm.add_lead("bad", "B", "web", "r1")
        )
        self.assert_unchanged(
            crm, lambda: crm.add_lead("dup@corp.com", "   ", "web", "r1")
        )
        self.assert_unchanged(
            crm, lambda: crm.add_lead("dup@corp.com", "B", "phone", "r1")
        )
        with self.assertRaises(DuplicateLeadError) as ctx:
            crm.add_lead("  DUP@corp.COM ", "B", "event", "r1")
        self.assertEqual(ctx.exception.existing_id, first)
        self.assertTrue(issubclass(DuplicateLeadError, Exception))

    def test_web_corporate_score_of_25_cannot_qualify(self):
        crm = new_crm()
        lid = crm.add_lead("a@corp.com", "A", "web", "r1")
        self.assertEqual(crm.leads[lid]["score"], 25)
        self.assert_unchanged(crm, lambda: crm.qualify(lid, "r1"))

    def test_converted_lead_cannot_be_qualified_or_converted_again(self):
        crm = new_crm()
        lead, opp, owner = owned_opp(crm)
        self.assertEqual(crm.leads[lead]["status"], "converted")
        self.assert_unchanged(crm, lambda: crm.qualify(lead, "m1"))
        self.assert_unchanged(crm, lambda: crm.convert(lead, 500, "m1"))
        self.assertEqual(list(crm.opps), [opp])


class TestAdvanceEdges(SnapshotMixin, unittest.TestCase):
    def test_stage_validation_precedes_permission(self):
        crm = new_crm()
        _, opp, _ = owned_opp(crm)
        self.assert_unchanged(crm, lambda: crm.advance(opp, "bogus", "r2"))

    def test_skipping_a_stage_is_a_value_error_before_the_manager_rule(self):
        crm = new_crm()
        _, opp, owner = owned_opp(crm, amount=60000)
        self.assert_unchanged(crm, lambda: crm.advance(opp, "negotiation", owner))
        crm.advance(opp, "proposal", owner)
        self.assert_unchanged(
            crm, lambda: crm.advance(opp, "negotiation", owner), PermissionError
        )
        crm.advance(opp, "negotiation", "m1")
        self.assertEqual(crm.opps[opp]["stage"], "negotiation")

    def test_exactly_50000_does_not_need_a_manager(self):
        crm = new_crm()
        _, opp, owner = owned_opp(crm, amount=50000)
        crm.advance(opp, "proposal", owner)
        crm.advance(opp, "negotiation", owner)
        self.assertEqual(crm.opps[opp]["stage"], "negotiation")

    def test_discount_shrinking_amount_below_threshold_lets_rep_advance(self):
        crm = new_crm()
        _, opp, owner = owned_opp(crm, amount=60000)
        crm.advance(opp, "proposal", owner)
        crm.discount(opp, 30, "m1")  # 60000 -> 42000
        self.assertEqual(crm.opps[opp]["amount"], 42000)
        crm.advance(opp, "negotiation", owner)
        self.assertEqual(crm.opps[opp]["stage"], "negotiation")

    def test_final_opportunity_refuses_same_stage(self):
        crm = new_crm()
        _, opp, owner = owned_opp(crm)
        crm.advance(opp, "lost", owner)
        self.assert_unchanged(crm, lambda: crm.advance(opp, "lost", owner))


class TestDiscountEdges(SnapshotMixin, unittest.TestCase):
    def test_pct_validated_before_permission(self):
        crm = new_crm()
        _, opp, _ = owned_opp(crm)
        self.assert_unchanged(crm, lambda: crm.discount(opp, 0, "r2"))
        self.assert_unchanged(crm, lambda: crm.discount(opp, 31, "r2"))

    def test_final_stage_rejected_before_rep_limit(self):
        crm = new_crm()
        _, opp, owner = owned_opp(crm)
        crm.advance(opp, "lost", owner)
        self.assert_unchanged(crm, lambda: crm.discount(opp, 11, owner))

    def test_cumulative_cap_uses_original_amount(self):
        crm = new_crm()
        _, opp, _ = owned_opp(crm, amount=10000)
        crm.discount(opp, 20, "m1")  # 8000
        self.assert_unchanged(crm, lambda: crm.discount(opp, 20, "m1"))
        self.assertEqual(crm.opps[opp]["amount"], 8000)
        crm.discount(opp, 10, "m1")  # 7200
        self.assertEqual(crm.opps[opp]["amount"], 7200)
        self.assert_unchanged(crm, lambda: crm.discount(opp, 3, "m1"))
        self.assertEqual(crm.opps[opp]["original_amount"], 10000)
        self.assertEqual(
            [entry for entry in crm.log if entry[0] == "discount"],
            [("discount", opp, "m1"), ("discount", opp, "m1")],
        )


class TestTransferEdges(SnapshotMixin, unittest.TestCase):
    def test_transfer_updates_owner_load_and_log_only(self):
        crm = new_crm()
        lead, opp, _ = owned_opp(crm)
        before_leads = copy.deepcopy(crm.leads)
        crm.transfer(opp, "r2", "m1")
        self.assertEqual(crm.opps[opp]["owner"], "r2")
        self.assertEqual(crm.log[-1], ("transfer", opp, "m1"))
        self.assertEqual(crm.leads, before_leads)
        self.assertEqual(crm.leads[lead]["status"], "converted")
        self.assertEqual(crm.opps[opp]["amount"], 1000)

    def test_same_owner_rejected_before_capacity(self):
        crm = new_crm(
            [
                {"id": "r1", "role": "rep", "capacity": 1},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        _, opp, owner = owned_opp(crm)
        self.assert_unchanged(crm, lambda: crm.transfer(opp, owner, "m1"))

    def test_manager_cannot_be_new_owner(self):
        crm = new_crm()
        _, opp, _ = owned_opp(crm)
        self.assert_unchanged(crm, lambda: crm.transfer(opp, "m1", "m1"))


class TestForecastEdges(unittest.TestCase):
    def test_weighted_uses_discounted_amounts_and_skips_lost(self):
        crm = new_crm()
        _, prospect, owner = owned_opp(crm, email="a@corp.com", amount=10000)
        _, proposal, _ = owned_opp(crm, email="b@corp.com", amount=10000)
        crm.advance(proposal, "proposal", "m1")
        _, negotiation, _ = owned_opp(crm, email="c@corp.com", amount=10000)
        crm.advance(negotiation, "proposal", "m1")
        crm.advance(negotiation, "negotiation", "m1")
        crm.discount(negotiation, 10, "m1")  # 9000 * 60 // 100 = 5400
        _, lost, _ = owned_opp(crm, email="d@corp.com", amount=9000)
        crm.advance(lost, "lost", "m1")

        self.assertEqual(
            crm.forecast(),
            {"open": 3, "weighted": 1000 + 3000 + 5400, "won": 0},
        )

    def test_forecast_ignores_actor_and_writes_no_log(self):
        crm = new_crm()
        owned_opp(crm)
        before = list(crm.log)
        crm.forecast()
        self.assertEqual(crm.log, before)
        with self.assertRaises(TypeError):
            crm.forecast("r1")


if __name__ == "__main__":
    unittest.main()
