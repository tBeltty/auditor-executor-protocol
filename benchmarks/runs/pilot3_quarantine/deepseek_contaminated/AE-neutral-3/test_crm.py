"""Unit tests for crm.py (spec: specs/crm.md)."""

import copy
import unittest

from crm import CRM, DuplicateLeadError


def make_reps():
    return [
        {"id": "r1", "role": "rep", "capacity": 5},
        {"id": "r2", "role": "rep", "capacity": 5},
        {"id": "m1", "role": "manager", "capacity": 0},
    ]


def new_crm(reps=None):
    return CRM(copy.deepcopy(reps if reps is not None else make_reps()))


def converted(crm, email="lead@corp.com", amount=10000, source="referral"):
    """Create a qualified, converted lead owned by its assigned rep."""
    lead_id = crm.add_lead(email, "Lead", source, "r1")
    owner = crm.leads[lead_id]["owner"]
    crm.qualify(lead_id, owner)
    opp_id = crm.convert(lead_id, amount, owner)
    return lead_id, opp_id


def advance_to_won(crm, opp_id, actor="m1"):
    crm.advance(opp_id, "proposal", actor)
    crm.advance(opp_id, "negotiation", actor)
    crm.advance(opp_id, "won", actor)
    return opp_id


class AssertUntouchedMixin:
    def assert_untouched(self, crm, fn, exc=ValueError):
        before = copy.deepcopy((crm.leads, crm.opps, crm.log))
        with self.assertRaises(exc):
            fn()
        self.assertEqual((crm.leads, crm.opps, crm.log), before)


class TestActor(AssertUntouchedMixin, unittest.TestCase):
    def test_unknown_actor_fails_first_everywhere(self):
        crm = new_crm()
        calls = [
            lambda: crm.add_lead(1, "", "bogus", "ghost"),
            lambda: crm.qualify("nope", "ghost"),
            lambda: crm.convert("nope", "bad", "ghost"),
            lambda: crm.advance("nope", "bogus", "ghost"),
            lambda: crm.discount("nope", 999, "ghost"),
            lambda: crm.transfer("nope", "nope", "ghost"),
        ]
        for call in calls:
            self.assert_untouched(crm, call, PermissionError)

    def test_non_string_actor_is_unknown(self):
        crm = new_crm()
        for actor in (None, 5, ["r1"]):
            with self.assertRaises(PermissionError):
                crm.add_lead("a@b.com", "A", "web", actor)

    def test_known_actor_from_any_role_may_add_leads(self):
        crm = new_crm()
        lid = crm.add_lead("a@b.com", "A", "web", "m1")
        self.assertEqual(crm.log, [("add_lead", lid, "m1")])


class TestAddLead(AssertUntouchedMixin, unittest.TestCase):
    def test_stores_normalized_lead(self):
        crm = new_crm()
        lid = crm.add_lead("  Foo@Example.COM  ", "  Bob  ", "referral", "r1")
        self.assertEqual(lid, "L1")
        self.assertEqual(
            crm.leads["L1"],
            {
                "id": "L1",
                "email": "foo@example.com",
                "name": "Bob",
                "source": "referral",
                "score": 45,
                "owner": "r1",
                "status": "new",
            },
        )
        self.assertEqual(crm.log, [("add_lead", "L1", "r1")])

    def test_email_validation(self):
        crm = new_crm()
        bad_emails = [
            123,
            None,
            "",
            "   ",
            "plainaddress",
            "a@@b.com",
            "a@b@c.com",
            "@b.com",
            "a@b",
            "a@.com",
            "a@com.",
            "a@.b",
            "a@.",
        ]
        for index, email in enumerate(bad_emails):
            self.assert_untouched(
                crm,
                lambda email=email: crm.add_lead(email, "A", "web", "r1"),
            )

    def test_valid_email_edges(self):
        crm = new_crm()
        for email in (" a@b.c ", "A@B.CO"):
            crm.add_lead(email, "A", "web", "r1")
        self.assertEqual(crm.leads["L1"]["email"], "a@b.c")
        self.assertEqual(crm.leads["L2"]["email"], "a@b.co")

    def test_name_validation(self):
        crm = new_crm()
        for name in (None, 5, "", "   "):
            self.assert_untouched(
                crm, lambda name=name: crm.add_lead("a@b.com", name, "web", "r1")
            )

    def test_source_validation(self):
        crm = new_crm()
        for source in (None, "", "phone", "WEB", 3):
            self.assert_untouched(
                crm, lambda source=source: crm.add_lead("a@b.com", "A", source, "r1")
            )

    def test_duplicate_email_raises_with_existing_id(self):
        crm = new_crm()
        lid = crm.add_lead("Foo@Corp.com", "A", "web", "r1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            crm.add_lead("  foo@corp.COM ", "B", "event", "r1")
        self.assertEqual(ctx.exception.existing_id, lid)

    def test_duplicate_attempt_changes_nothing(self):
        crm = new_crm()
        crm.add_lead("foo@corp.com", "A", "web", "r1")
        self.assert_untouched(
            crm,
            lambda: crm.add_lead("foo@corp.com", "B", "web", "r1"),
            DuplicateLeadError,
        )

    def test_scores(self):
        crm = new_crm()
        cases = [
            ("web", "a@gmail.com", 10),
            ("web", "b@corp.com", 25),
            ("referral", "c@gmail.com", 30),
            ("referral", "d@corp.com", 45),
            ("event", "e@yahoo.com", 20),
            ("event", "f@outlook.com", 20),
            ("event", "g@corp.com", 35),
        ]
        for source, email, expected in cases:
            lid = crm.add_lead(email, "A", source, "r1")
            self.assertEqual(crm.leads[lid]["score"], expected, (source, email))

    def test_owner_is_lowest_load_with_tie_by_smallest_id(self):
        reps = [
            {"id": "r2", "role": "rep", "capacity": 5},
            {"id": "r1", "role": "rep", "capacity": 5},
            {"id": "m1", "role": "manager", "capacity": 5},
        ]
        crm = new_crm(reps)
        first = crm.add_lead("a@corp.com", "A", "web", "r1")
        second = crm.add_lead("b@corp.com", "B", "web", "r1")
        third = crm.add_lead("c@corp.com", "C", "web", "r1")
        self.assertEqual(crm.leads[first]["owner"], "r1")
        self.assertEqual(crm.leads[second]["owner"], "r2")
        self.assertEqual(crm.leads[third]["owner"], "r1")

    def test_waits_when_no_rep_has_capacity(self):
        crm = new_crm(
            [
                {"id": "r1", "role": "rep", "capacity": 1},
                {"id": "m1", "role": "manager", "capacity": 5},
            ]
        )
        first = crm.add_lead("a@corp.com", "A", "web", "r1")
        second = crm.add_lead("b@corp.com", "B", "web", "r1")
        self.assertEqual(crm.leads[first]["owner"], "r1")
        self.assertIsNone(crm.leads[second]["owner"])
        self.assertEqual(crm.leads[second]["status"], "new")
        self.assertEqual(
            crm.log,
            [("add_lead", first, "r1"), ("add_lead", second, "r1")],
        )

    def test_manager_never_owns(self):
        crm = new_crm([{"id": "m1", "role": "manager", "capacity": 5}])
        lid = crm.add_lead("a@corp.com", "A", "web", "m1")
        self.assertIsNone(crm.leads[lid]["owner"])

    def test_lead_ids_count_successful_creations_only(self):
        crm = new_crm()
        self.assertEqual(crm.add_lead("a@corp.com", "A", "web", "r1"), "L1")
        with self.assertRaises(DuplicateLeadError):
            crm.add_lead("a@corp.com", "B", "web", "r1")
        with self.assertRaises(ValueError):
            crm.add_lead("bad", "B", "web", "r1")
        self.assertEqual(crm.add_lead("b@corp.com", "B", "web", "r1"), "L2")


class TestQualify(AssertUntouchedMixin, unittest.TestCase):
    def test_unknown_lead(self):
        crm = new_crm()
        for lead_id in ("nope", None, 1):
            self.assert_untouched(crm, lambda lead_id=lead_id: crm.qualify(lead_id, "r1"))

    def test_only_owner_or_manager_may_qualify(self):
        crm = new_crm()
        lid = crm.add_lead("a@corp.com", "A", "referral", "r1")
        self.assert_untouched(crm, lambda: crm.qualify(lid, "r2"), PermissionError)
        crm.qualify(lid, "m1")
        self.assertEqual(crm.leads[lid]["status"], "qualified")
        self.assertEqual(crm.log[-1], ("qualify", lid, "m1"))

    def test_must_be_new(self):
        crm = new_crm()
        lid = crm.add_lead("a@corp.com", "A", "referral", "r1")
        crm.qualify(lid, "r1")
        self.assert_untouched(crm, lambda: crm.qualify(lid, "r1"))

    def test_score_must_reach_thirty(self):
        crm = new_crm()
        low = crm.add_lead("a@gmail.com", "A", "web", "r1")  # 10
        exact = crm.add_lead("b@gmail.com", "B", "referral", "r1")  # 30
        self.assert_untouched(crm, lambda: crm.qualify(low, "r1"))
        crm.qualify(exact, "m1")
        self.assertEqual(crm.leads[low]["status"], "new")
        self.assertEqual(crm.leads[exact]["status"], "qualified")


class TestConvert(AssertUntouchedMixin, unittest.TestCase):
    def test_unknown_lead(self):
        crm = new_crm()
        self.assert_untouched(crm, lambda: crm.convert("nope", 10, "r1"))

    def test_amount_validation(self):
        crm = new_crm()
        lid = crm.add_lead("a@corp.com", "A", "referral", "r1")
        crm.qualify(lid, "r1")
        for amount in (0, -1, True, False, 1.5, "100", None):
            self.assert_untouched(crm, lambda amount=amount: crm.convert(lid, amount, "r1"))

    def test_amount_checked_before_permission(self):
        crm = new_crm()
        lid = crm.add_lead("a@corp.com", "A", "referral", "r1")
        crm.qualify(lid, "r1")
        self.assert_untouched(crm, lambda: crm.convert(lid, 0, "r2"))

    def test_only_owner_or_manager_may_convert(self):
        crm = new_crm()
        lid = crm.add_lead("a@corp.com", "A", "referral", "r1")
        crm.qualify(lid, "r1")
        self.assert_untouched(crm, lambda: crm.convert(lid, 100, "r2"), PermissionError)

    def test_must_be_qualified(self):
        crm = new_crm()
        lid = crm.add_lead("a@corp.com", "A", "referral", "r1")
        self.assert_untouched(crm, lambda: crm.convert(lid, 100, "r1"))

    def test_requires_owner(self):
        crm = new_crm([{"id": "r1", "role": "rep", "capacity": 1},
                       {"id": "m1", "role": "manager", "capacity": 0}])
        waiting = crm.add_lead("a@corp.com", "A", "referral", "r1")  # L1 owned
        crm.add_lead("b@corp.com", "B", "referral", "r1")  # L2 waiting
        crm.qualify("L2", "m1")
        self.assert_untouched(crm, lambda: crm.convert("L2", 100, "m1"))
        self.assertEqual(crm.leads[waiting]["status"], "new")

    def test_successful_conversion(self):
        crm = new_crm()
        lid = crm.add_lead("a@corp.com", "A", "referral", "r1")
        crm.qualify(lid, "r1")
        oid = crm.convert(lid, 2500, "r1")
        self.assertEqual(oid, "O1")
        self.assertEqual(
            crm.opps["O1"],
            {
                "id": "O1",
                "lead_id": lid,
                "owner": "r1",
                "amount": 2500,
                "original_amount": 2500,
                "stage": "prospect",
            },
        )
        self.assertEqual(crm.leads[lid]["status"], "converted")
        self.assertEqual(crm.log[-1], ("convert", "O1", "r1"))

    def test_manager_may_convert_someone_elses_qualified_lead(self):
        crm = new_crm()
        lid = crm.add_lead("a@corp.com", "A", "referral", "r1")
        crm.qualify(lid, "r1")
        oid = crm.convert(lid, 2500, "m1")
        self.assertEqual(crm.opps[oid]["owner"], "r1")
        self.assertEqual(crm.log[-1], ("convert", oid, "m1"))

    def test_opportunity_ids_count_successful_conversions_only(self):
        crm = new_crm()
        first = crm.add_lead("a@corp.com", "A", "referral", "r1")
        second = crm.add_lead("b@corp.com", "B", "referral", "r1")
        crm.qualify(first, "m1")
        crm.qualify(second, "m1")
        with self.assertRaises(ValueError):
            crm.convert(first, 0, "r1")
        self.assertEqual(crm.convert(first, 100, "r1"), "O1")
        self.assertEqual(crm.convert(second, 100, "m1"), "O2")


class TestAdvance(AssertUntouchedMixin, unittest.TestCase):
    def test_unknown_opportunity(self):
        crm = new_crm()
        for opp_id in ("nope", None, 3):
            self.assert_untouched(crm, lambda opp_id=opp_id: crm.advance(opp_id, "proposal", "r1"))

    def test_stage_validated_before_permission(self):
        crm = new_crm()
        _, oid = converted(crm)
        self.assert_untouched(crm, lambda: crm.advance(oid, "bogus", "r2"))

    def test_only_owner_or_manager(self):
        crm = new_crm()
        _, oid = converted(crm)
        self.assert_untouched(crm, lambda: crm.advance(oid, "proposal", "r2"), PermissionError)
        crm.advance(oid, "proposal", "m1")
        self.assertEqual(crm.opps[oid]["stage"], "proposal")
        self.assertEqual(crm.log[-1], ("advance", oid, "m1"))

    def test_next_stage_only_or_lost(self):
        crm = new_crm()
        _, oid = converted(crm)
        for stage in ("negotiation", "won", "prospect"):
            self.assert_untouched(crm, lambda stage=stage: crm.advance(oid, stage, "r1"))
        crm.advance(oid, "proposal", "r1")
        self.assert_untouched(crm, lambda: crm.advance(oid, "won", "r1"))
        crm.advance(oid, "negotiation", "r1")
        crm.advance(oid, "won", "r1")
        self.assertEqual(crm.opps[oid]["stage"], "won")

    def test_lost_allowed_from_any_open_stage(self):
        crm = new_crm()
        _, oid = converted(crm)
        crm.advance(oid, "lost", "r1")
        self.assertEqual(crm.opps[oid]["stage"], "lost")
        self.assertEqual(crm.log[-1], ("advance", oid, "r1"))

    def test_final_stage_cannot_move(self):
        crm = new_crm()
        _, oid = converted(crm)
        crm.advance(oid, "lost", "r1")
        self.assert_untouched(crm, lambda: crm.advance(oid, "proposal", "r1"))

    def test_negotiation_over_50000_needs_manager(self):
        crm = new_crm()
        _, oid = converted(crm, amount=50001)
        crm.advance(oid, "proposal", "r1")
        self.assert_untouched(
            crm, lambda: crm.advance(oid, "negotiation", "r1"), PermissionError
        )
        crm.advance(oid, "negotiation", "m1")
        self.assertEqual(crm.opps[oid]["stage"], "negotiation")

    def test_negotiation_at_50000_allowed_for_rep(self):
        crm = new_crm()
        _, oid = converted(crm, amount=50000)
        crm.advance(oid, "proposal", "r1")
        crm.advance(oid, "negotiation", "r1")
        self.assertEqual(crm.opps[oid]["stage"], "negotiation")

    def test_win_frees_slot_and_assigns_fifo(self):
        crm = new_crm(
            [
                {"id": "r1", "role": "rep", "capacity": 2},
                {"id": "r2", "role": "rep", "capacity": 1},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        l1 = crm.add_lead("a@corp.com", "A", "referral", "r1")  # r1 (load 1)
        l2 = crm.add_lead("b@corp.com", "B", "referral", "r1")  # r2 (load 1)
        l3 = crm.add_lead("c@corp.com", "C", "referral", "r1")  # r1 (load 2)
        l4 = crm.add_lead("d@corp.com", "D", "referral", "r1")  # queued
        l5 = crm.add_lead("e@corp.com", "E", "referral", "r1")  # queued
        crm.qualify(l1, "r1")
        oid = crm.convert(l1, 1000, "r1")

        crm.advance(oid, "proposal", "r1")
        crm.advance(oid, "negotiation", "r1")
        crm.advance(oid, "won", "r1")

        self.assertEqual(crm.leads[l4]["owner"], "r1")
        self.assertIsNone(crm.leads[l5]["owner"])
        self.assertEqual(crm.log[-1], ("assign", l4, "system"))
        self.assertEqual(crm.leads[l2]["owner"], "r2")
        self.assertEqual(crm.leads[l3]["owner"], "r1")

    def test_lost_frees_slot_too(self):
        crm = new_crm(
            [
                {"id": "r1", "role": "rep", "capacity": 1},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        first = crm.add_lead("a@corp.com", "A", "referral", "r1")
        waiting = crm.add_lead("b@corp.com", "B", "referral", "r1")
        crm.qualify(first, "r1")
        oid = crm.convert(first, 1000, "r1")
        self.assertIsNone(crm.leads[waiting]["owner"])
        crm.advance(oid, "lost", "r1")
        self.assertEqual(crm.leads[waiting]["owner"], "r1")
        self.assertEqual(crm.log[-1], ("assign", waiting, "system"))


class TestDiscount(AssertUntouchedMixin, unittest.TestCase):
    def test_unknown_opportunity(self):
        crm = new_crm()
        self.assert_untouched(crm, lambda: crm.discount("nope", 5, "r1"))

    def test_pct_validation(self):
        crm = new_crm()
        _, oid = converted(crm)
        for pct in (0, 31, -5, True, False, 10.0, "10", None):
            self.assert_untouched(crm, lambda pct=pct: crm.discount(oid, pct, "r1"))

    def test_only_owner_or_manager(self):
        crm = new_crm()
        _, oid = converted(crm)
        self.assert_untouched(crm, lambda: crm.discount(oid, 5, "r2"), PermissionError)

    def test_final_stage_rejected(self):
        crm = new_crm()
        _, oid = converted(crm)
        advance_to_won(crm, oid)
        self.assert_untouched(crm, lambda: crm.discount(oid, 5, "m1"))

    def test_rep_limit_is_ten(self):
        crm = new_crm()
        _, oid = converted(crm, amount=10000)
        self.assert_untouched(crm, lambda: crm.discount(oid, 11, "r1"), PermissionError)
        crm.discount(oid, 10, "r1")
        self.assertEqual(crm.opps[oid]["amount"], 9000)

    def test_manager_limit_is_thirty(self):
        crm = new_crm()
        _, oid = converted(crm, amount=10000)
        crm.discount(oid, 30, "m1")
        self.assertEqual(crm.opps[oid]["amount"], 7000)
        self.assertEqual(crm.opps[oid]["original_amount"], 10000)
        self.assertEqual(crm.log[-1], ("discount", oid, "m1"))

    def test_cumulative_discount_capped_at_thirty_percent(self):
        crm = new_crm()
        _, oid = converted(crm, amount=10000)
        crm.discount(oid, 30, "m1")
        self.assert_untouched(crm, lambda: crm.discount(oid, 1, "m1"))
        self.assertEqual(crm.opps[oid]["amount"], 7000)
        self.assertEqual([entry for entry in crm.log if entry[0] == "discount"],
                         [("discount", oid, "m1")])

    def test_integer_floor(self):
        crm = new_crm()
        _, oid = converted(crm, amount=999)
        crm.discount(oid, 10, "r1")
        self.assertEqual(crm.opps[oid]["amount"], 899)


class TestTransfer(AssertUntouchedMixin, unittest.TestCase):
    def test_unknown_opportunity(self):
        crm = new_crm()
        self.assert_untouched(crm, lambda: crm.transfer("nope", "r2", "m1"))

    def test_only_manager_may_transfer(self):
        crm = new_crm()
        _, oid = converted(crm)
        self.assert_untouched(crm, lambda: crm.transfer(oid, "r2", "r1"), PermissionError)
        self.assert_untouched(crm, lambda: crm.transfer(oid, "nope", "r1"), PermissionError)

    def test_new_owner_must_be_known_rep(self):
        crm = new_crm()
        _, oid = converted(crm)
        for new_owner in ("nope", "m1", None, 7):
            self.assert_untouched(crm, lambda new_owner=new_owner: crm.transfer(oid, new_owner, "m1"))

    def test_final_stage_rejected(self):
        crm = new_crm()
        _, oid = converted(crm)
        advance_to_won(crm, oid)
        self.assert_untouched(crm, lambda: crm.transfer(oid, "r2", "m1"))

    def test_same_owner_rejected(self):
        crm = new_crm()
        _, oid = converted(crm)
        self.assert_untouched(crm, lambda: crm.transfer(oid, "r1", "m1"))

    def test_new_owner_needs_capacity(self):
        crm = new_crm(
            [
                {"id": "r1", "role": "rep", "capacity": 5},
                {"id": "r2", "role": "rep", "capacity": 0},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        _, oid = converted(crm)
        self.assert_untouched(crm, lambda: crm.transfer(oid, "r2", "m1"))

    def test_successful_transfer(self):
        crm = new_crm()
        _, oid = converted(crm)
        crm.transfer(oid, "r2", "m1")
        self.assertEqual(crm.opps[oid]["owner"], "r2")
        self.assertEqual(crm.log[-1], ("transfer", oid, "m1"))


class TestForecast(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(new_crm().forecast(), {"open": 0, "weighted": 0, "won": 0})

    def test_mixed_pipeline(self):
        crm = new_crm()
        _, prospect = converted(crm, email="a@corp.com", amount=10000)
        _, proposal = converted(crm, email="b@corp.com", amount=20000)
        crm.advance(proposal, "proposal", "m1")
        _, negotiation = converted(crm, email="c@corp.com", amount=30000)
        crm.advance(negotiation, "proposal", "m1")
        crm.advance(negotiation, "negotiation", "m1")
        _, won = converted(crm, email="d@corp.com", amount=40000)
        advance_to_won(crm, won)
        _, lost = converted(crm, email="e@corp.com", amount=5000)
        crm.advance(lost, "lost", "m1")

        log_before = list(crm.log)
        self.assertEqual(
            crm.forecast(),
            {"open": 3, "weighted": 25000, "won": 40000},
        )
        self.assertEqual(crm.log, log_before)

    def test_floors_weighted_values(self):
        crm = new_crm()
        converted(crm, amount=1001)
        self.assertEqual(crm.forecast()["weighted"], 100)


class TestLog(AssertUntouchedMixin, unittest.TestCase):
    def test_happy_path_log_is_exact_tuple_sequence(self):
        crm = new_crm()
        lid = crm.add_lead("a@corp.com", "A", "referral", "r1")
        crm.qualify(lid, "m1")
        oid = crm.convert(lid, 1000, "m1")
        crm.advance(oid, "proposal", "m1")
        crm.discount(oid, 10, "m1")
        crm.transfer(oid, "r2", "m1")
        crm.advance(oid, "negotiation", "r2")
        crm.advance(oid, "won", "r2")
        self.assertEqual(
            crm.log,
            [
                ("add_lead", "L1", "r1"),
                ("qualify", "L1", "m1"),
                ("convert", "O1", "m1"),
                ("advance", "O1", "m1"),
                ("discount", "O1", "m1"),
                ("transfer", "O1", "m1"),
                ("advance", "O1", "r2"),
                ("advance", "O1", "r2"),
            ],
        )
        for entry in crm.log:
            self.assertIsInstance(entry, tuple)
            self.assertEqual(len(entry), 3)

    def test_every_failure_is_silent(self):
        crm = new_crm()
        lid = crm.add_lead("a@corp.com", "A", "referral", "r1")
        crm.qualify(lid, "r1")
        oid = crm.convert(lid, 1000, "r1")
        failing_calls = [
            lambda: crm.add_lead("bad", "A", "web", "r1"),
            lambda: crm.qualify("nope", "r1"),
            lambda: crm.convert(oid, 0, "r1"),
            lambda: crm.advance(oid, "won", "r1"),
            lambda: crm.discount(oid, 0, "r1"),
            lambda: crm.transfer(oid, "r2", "r1"),
            lambda: crm.discount(oid, 5, "ghost"),
        ]
        for call in failing_calls:
            before = copy.deepcopy((crm.leads, crm.opps, crm.log))
            with self.assertRaises((ValueError, PermissionError)):
                call()
            self.assertEqual((crm.leads, crm.opps, crm.log), before)


class TestLoadAccounting(unittest.TestCase):
    def test_converted_lead_does_not_count_but_opportunity_does(self):
        crm = new_crm(
            [
                {"id": "r1", "role": "rep", "capacity": 1},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        lid = crm.add_lead("a@corp.com", "A", "referral", "r1")
        crm.qualify(lid, "r1")
        crm.convert(lid, 1000, "r1")
        blocked = crm.add_lead("b@corp.com", "B", "referral", "r1")
        self.assertIsNone(crm.leads[blocked]["owner"])

    def test_qualified_lead_still_counts(self):
        crm = new_crm(
            [
                {"id": "r1", "role": "rep", "capacity": 1},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        lid = crm.add_lead("a@corp.com", "A", "referral", "r1")
        crm.qualify(lid, "r1")
        blocked = crm.add_lead("b@corp.com", "B", "referral", "r1")
        self.assertIsNone(crm.leads[blocked]["owner"])


if __name__ == "__main__":
    unittest.main()
