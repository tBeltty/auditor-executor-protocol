"""Spec-driven tests for crm.py (kept independent of test_crm.py)."""

import copy
import unittest

from crm import CRM, DuplicateLeadError


def build(reps=None):
    if reps is None:
        reps = [
            {"id": "m1", "role": "manager", "capacity": 99},
            {"id": "r1", "role": "rep", "capacity": 3},
            {"id": "r2", "role": "rep", "capacity": 3},
        ]
    return CRM(reps)


def snapshot(crm):
    return (
        copy.deepcopy(crm.leads),
        copy.deepcopy(crm.opps),
        list(crm.log),
    )


def make_lead(crm, email="lead@gmail.com", name="Lead", source="referral",
              actor="m1"):
    return crm.add_lead(email, name, source, actor)


def make_qualified(crm, email="lead@gmail.com", name="Lead",
                   source="referral", actor="m1"):
    lead_id = make_lead(crm, email, name, source, actor)
    crm.qualify(lead_id, actor)
    return lead_id


def make_opp(crm, amount=1000, email="lead@gmail.com", name="Lead",
             source="referral", actor="m1"):
    lead_id = make_qualified(crm, email, name, source, actor)
    return crm.convert(lead_id, amount, actor)


class TestConstruction(unittest.TestCase):
    def test_initial_attributes(self):
        crm = build()
        self.assertEqual(crm.leads, {})
        self.assertEqual(crm.opps, {})
        self.assertEqual(crm.log, [])

    def test_duplicate_error_attribute(self):
        err = DuplicateLeadError("L7")
        self.assertEqual(err.existing_id, "L7")
        self.assertIsInstance(err, Exception)


class TestActorFirst(unittest.TestCase):
    def test_every_method_rejects_unknown_actor_first(self):
        crm = build()
        cases = [
            lambda: crm.add_lead("bad-email", "", "nope", "ghost"),
            lambda: crm.qualify("L404", "ghost"),
            lambda: crm.convert("L404", -1, "ghost"),
            lambda: crm.advance("O404", "nope", "ghost"),
            lambda: crm.discount("O404", 99, "ghost"),
            lambda: crm.transfer("O404", "ghost", "ghost"),
        ]
        for call in cases:
            with self.assertRaises(PermissionError):
                call()
        self.assertEqual(crm.log, [])
        self.assertEqual(crm.leads, {})
        self.assertEqual(crm.opps, {})

    def test_non_string_actor_is_rejected(self):
        crm = build()
        for actor in (None, 123, ["r1"], {"id": "r1"}):
            with self.assertRaises(PermissionError):
                crm.add_lead("a@b.com", "Ann", "web", actor)

    def test_forecast_needs_no_actor(self):
        self.assertEqual(build().forecast(), {"open": 0, "weighted": 0, "won": 0})


class TestAddLeadValidation(unittest.TestCase):
    def setUp(self):
        self.crm = build()

    def test_bad_email_shapes(self):
        bad = [
            None, 12, 3.5, ["a@b.com"], {}, "",
            "no-at-sign", "two@at@sign.com", "@b.com", "a@", "a@bcom",
            "a@.com", "a@com.", "a@.com.", "a@.b.", "a@..",
        ]
        for email in bad:
            with self.assertRaises(ValueError):
                self.crm.add_lead(email, "Ann", "web", "m1")
        self.assertEqual(self.crm.leads, {})
        self.assertEqual(self.crm.log, [])

    def test_good_email_shapes(self):
        good = [
            "a@b.co", "user.name+tag@gmail.com", "x@y.z",
            "  Ann@Example.COM  ", "a@b..c", "a@b.c.d",
        ]
        for index, email in enumerate(good):
            lead_id = self.crm.add_lead(email, "Ann", "web", "m1")
            self.assertIn(lead_id, self.crm.leads)

    def test_normalization(self):
        lead_id = self.crm.add_lead("  Ann@Example.COM ", "  Ann Lee  ", "web", "m1")
        lead = self.crm.leads[lead_id]
        self.assertEqual(lead["email"], "ann@example.com")
        self.assertEqual(lead["name"], "Ann Lee")

    def test_bad_name(self):
        for name in (None, "", "   ", "\t\n", 7, ["Ann"]):
            with self.assertRaises(ValueError):
                self.crm.add_lead("a@b.com", name, "web", "m1")
        self.assertEqual(self.crm.leads, {})

    def test_bad_source(self):
        for source in ("", "Web", "WEB", "ads", None, 1, ["web"], {"web"}):
            with self.assertRaises(ValueError):
                self.crm.add_lead("a@b.com", "Ann", source, "m1")
        self.assertEqual(self.crm.leads, {})

    def test_check_order_name_before_duplicate(self):
        self.crm.add_lead("a@b.com", "Ann", "web", "m1")
        with self.assertRaises(ValueError):
            self.crm.add_lead("A@B.COM", "   ", "web", "m1")

    def test_check_order_source_before_duplicate(self):
        self.crm.add_lead("a@b.com", "Ann", "web", "m1")
        with self.assertRaises(ValueError):
            self.crm.add_lead("A@B.COM", "Ann", "ads", "m1")

    def test_duplicate_raises_with_existing_id(self):
        first = self.crm.add_lead("a@b.com", "Ann", "web", "m1")
        log_before = list(self.crm.log)
        with self.assertRaises(DuplicateLeadError) as ctx:
            self.crm.add_lead("  A@B.COM ", "Other", "referral", "m1")
        self.assertEqual(ctx.exception.existing_id, first)
        self.assertEqual(self.crm.log, log_before)
        self.assertEqual(len(self.crm.leads), 1)

    def test_duplicate_after_conversion_still_duplicate(self):
        lead_id = make_qualified(self.crm)
        self.crm.convert(lead_id, 100, "m1")
        with self.assertRaises(DuplicateLeadError):
            self.crm.add_lead("LEAD@gmail.com", "Again", "referral", "m1")

    def test_lead_shape_and_log_entry(self):
        lead_id = self.crm.add_lead("a@b.com", " Ann ", "event", "m1")
        self.assertEqual(
            set(self.crm.leads[lead_id]),
            {"id", "email", "name", "source", "score", "owner", "status"},
        )
        self.assertEqual(self.crm.leads[lead_id]["status"], "new")
        self.assertEqual(self.crm.log, [("add_lead", lead_id, "m1")])
        self.assertTrue(all(isinstance(entry, tuple) for entry in self.crm.log))

    def test_ids_increment_only_on_success(self):
        first = self.crm.add_lead("a@b.com", "A", "web", "m1")
        for _ in range(3):
            with self.assertRaises(ValueError):
                self.crm.add_lead("bad", "B", "web", "m1")
        second = self.crm.add_lead("c@d.com", "C", "web", "m1")
        self.assertEqual((first, second), ("L1", "L2"))


class TestScore(unittest.TestCase):
    def score_for(self, email, source):
        crm = build([{"id": "r1", "role": "rep", "capacity": 10}])
        lead_id = crm.add_lead(email, "N", source, "r1")
        return crm.leads[lead_id]["score"]

    def test_scores(self):
        self.assertEqual(self.score_for("a@gmail.com", "web"), 10)
        self.assertEqual(self.score_for("a@example.com", "web"), 25)
        self.assertEqual(self.score_for("a@gmail.com", "referral"), 30)
        self.assertEqual(self.score_for("a@example.com", "referral"), 45)
        self.assertEqual(self.score_for("a@gmail.com", "event"), 20)
        self.assertEqual(self.score_for("a@example.com", "event"), 35)

    def test_free_domains(self):
        for domain in ("gmail.com", "yahoo.com", "outlook.com"):
            self.assertEqual(self.score_for("a@%s" % domain, "web"), 10)

    def test_subdomain_of_free_domain_is_not_free(self):
        self.assertEqual(self.score_for("a@mail.gmail.com", "web"), 25)


class TestOwnership(unittest.TestCase):
    def test_least_load_tie_break_smallest_id(self):
        crm = build([
            {"id": "b", "role": "rep", "capacity": 5},
            {"id": "a", "role": "rep", "capacity": 5},
        ])
        first = crm.add_lead("1@x.com", "A", "web", "a")
        second = crm.add_lead("2@x.com", "B", "web", "a")
        third = crm.add_lead("3@x.com", "C", "web", "a")
        self.assertEqual(crm.leads[first]["owner"], "a")
        self.assertEqual(crm.leads[second]["owner"], "b")
        self.assertEqual(crm.leads[third]["owner"], "a")

    def test_string_order_tie_break(self):
        crm = build([
            {"id": "r9", "role": "rep", "capacity": 5},
            {"id": "r10", "role": "rep", "capacity": 5},
        ])
        lead_id = crm.add_lead("1@x.com", "A", "web", "r9")
        self.assertEqual(crm.leads[lead_id]["owner"], "r10")

    def test_managers_never_own(self):
        crm = build([{"id": "m1", "role": "manager", "capacity": 5}])
        lead_id = crm.add_lead("1@x.com", "A", "web", "m1")
        self.assertIsNone(crm.leads[lead_id]["owner"])

    def test_zero_capacity_rep_never_owns(self):
        crm = build([{"id": "r1", "role": "rep", "capacity": 0}])
        lead_id = crm.add_lead("1@x.com", "A", "web", "r1")
        self.assertIsNone(crm.leads[lead_id]["owner"])

    def test_queue_is_fifo_on_advance(self):
        crm = build([
            {"id": "m1", "role": "manager", "capacity": 9},
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 1},
        ])
        l1 = crm.add_lead("1@x.com", "A", "referral", "m1")
        l2 = crm.add_lead("2@x.com", "B", "referral", "m1")
        l3 = crm.add_lead("3@x.com", "C", "referral", "m1")
        l4 = crm.add_lead("4@x.com", "D", "referral", "m1")
        self.assertEqual(crm.leads[l1]["owner"], "r1")
        self.assertEqual(crm.leads[l2]["owner"], "r2")
        self.assertIsNone(crm.leads[l3]["owner"])
        self.assertIsNone(crm.leads[l4]["owner"])

        crm.qualify(l1, "m1")
        o1 = crm.convert(l1, 100, "m1")
        crm.advance(o1, "proposal", "m1")
        self.assertIsNone(crm.leads[l3]["owner"])
        crm.advance(o1, "negotiation", "m1")
        crm.advance(o1, "won", "m1")
        self.assertEqual(crm.leads[l3]["owner"], "r1")
        self.assertIsNone(crm.leads[l4]["owner"])
        self.assertEqual(crm.log[-1], ("assign", l3, "system"))

    def test_queue_drains_in_order_across_successive_frees(self):
        crm = build([
            {"id": "m1", "role": "manager", "capacity": 9},
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 1},
        ])
        l1 = crm.add_lead("1@x.com", "A", "referral", "m1")
        l2 = crm.add_lead("2@x.com", "B", "referral", "m1")
        l3 = crm.add_lead("3@x.com", "C", "referral", "m1")
        l4 = crm.add_lead("4@x.com", "D", "referral", "m1")
        self.assertEqual(crm.leads[l1]["owner"], "r1")
        self.assertEqual(crm.leads[l2]["owner"], "r2")
        self.assertIsNone(crm.leads[l3]["owner"])
        self.assertIsNone(crm.leads[l4]["owner"])

        crm.qualify(l1, "m1")
        o1 = crm.convert(l1, 100, "m1")
        crm.advance(o1, "proposal", "m1")
        crm.advance(o1, "negotiation", "m1")
        crm.advance(o1, "won", "m1")
        self.assertEqual(crm.leads[l3]["owner"], "r1")
        self.assertIsNone(crm.leads[l4]["owner"])

        crm.qualify(l2, "m1")
        o2 = crm.convert(l2, 100, "m1")
        crm.advance(o2, "proposal", "m1")
        crm.advance(o2, "negotiation", "m1")
        crm.advance(o2, "won", "m1")
        self.assertEqual(crm.leads[l4]["owner"], "r2")
        self.assertEqual(
            [entry for entry in crm.log if entry[0] == "assign"],
            [("assign", l3, "system"), ("assign", l4, "system")],
        )


class TestQualify(unittest.TestCase):
    def setUp(self):
        self.crm = build()

    def test_unknown_lead(self):
        with self.assertRaises(ValueError):
            self.crm.qualify("L404", "m1")
        with self.assertRaises(ValueError):
            self.crm.qualify(["L1"], "m1")

    def test_permission_checks(self):
        lead_id = self.crm.add_lead("a@example.com", "A", "referral", "m1")
        other = "r2" if self.crm.leads[lead_id]["owner"] == "r1" else "r1"
        with self.assertRaises(PermissionError):
            self.crm.qualify(lead_id, other)
        self.assertEqual(self.crm.leads[lead_id]["status"], "new")

    def test_manager_may_qualify_any_lead(self):
        lead_id = self.crm.add_lead("a@example.com", "A", "referral", "m1")
        self.crm.qualify(lead_id, "m1")
        self.assertEqual(self.crm.leads[lead_id]["status"], "qualified")
        self.assertEqual(self.crm.log[-1], ("qualify", lead_id, "m1"))

    def test_score_threshold(self):
        weak = self.crm.add_lead("a@gmail.com", "A", "web", "m1")
        with self.assertRaises(ValueError):
            self.crm.qualify(weak, "m1")
        self.assertEqual(self.crm.leads[weak]["status"], "new")

    def test_score_exactly_thirty(self):
        lead_id = self.crm.add_lead("a@gmail.com", "A", "referral", "m1")
        self.crm.qualify(lead_id, "m1")
        self.assertEqual(self.crm.leads[lead_id]["status"], "qualified")

    def test_status_must_be_new(self):
        lead_id = make_qualified(self.crm)
        self.crm.convert(lead_id, 100, "m1")
        with self.assertRaises(ValueError):
            self.crm.qualify(lead_id, "m1")

    def test_check_order_permission_before_status(self):
        lead_id = self.crm.add_lead("a@gmail.com", "A", "web", "m1")
        other = "r2" if self.crm.leads[lead_id]["owner"] == "r1" else "r1"
        with self.assertRaises(PermissionError):
            self.crm.qualify(lead_id, other)

    def test_failed_qualify_is_atomic(self):
        weak = self.crm.add_lead("a@gmail.com", "A", "web", "m1")
        before = snapshot(self.crm)
        with self.assertRaises(ValueError):
            self.crm.qualify(weak, "m1")
        self.assertEqual(snapshot(self.crm), before)


class TestConvert(unittest.TestCase):
    def setUp(self):
        self.crm = build()

    def test_unknown_lead(self):
        with self.assertRaises(ValueError):
            self.crm.convert("L404", 100, "m1")

    def test_bad_amounts(self):
        lead_id = make_qualified(self.crm)
        for amount in (0, -1, -100, 1.0, 1.5, "100", None, True, False, [100]):
            with self.assertRaises(ValueError):
                self.crm.convert(lead_id, amount, "m1")
        self.assertEqual(self.crm.opps, {})
        self.assertEqual(self.crm.leads[lead_id]["status"], "qualified")

    def test_amount_checked_before_permission(self):
        lead_id = make_qualified(self.crm)
        other = "r2" if self.crm.leads[lead_id]["owner"] == "r1" else "r1"
        with self.assertRaises(ValueError):
            self.crm.convert(lead_id, 0, other)

    def test_permission(self):
        lead_id = make_qualified(self.crm)
        other = "r2" if self.crm.leads[lead_id]["owner"] == "r1" else "r1"
        with self.assertRaises(PermissionError):
            self.crm.convert(lead_id, 100, other)
        self.assertEqual(self.crm.opps, {})
        self.assertEqual(self.crm.leads[lead_id]["status"], "qualified")

    def test_owner_may_convert(self):
        lead_id = make_qualified(self.crm)
        owner = self.crm.leads[lead_id]["owner"]
        opp_id = self.crm.convert(lead_id, 500, owner)
        self.assertEqual(opp_id, "O1")
        self.assertEqual(self.crm.leads[lead_id]["status"], "converted")
        self.assertEqual(self.crm.log[-1], ("convert", opp_id, owner))

    def test_requires_qualified(self):
        lead_id = self.crm.add_lead("a@example.com", "A", "referral", "m1")
        with self.assertRaises(ValueError):
            self.crm.convert(lead_id, 100, "m1")

    def test_requires_owner(self):
        crm = build([{"id": "m1", "role": "manager", "capacity": 1}])
        lead_id = crm.add_lead("a@gmail.com", "A", "referral", "m1")
        crm.qualify(lead_id, "m1")
        self.assertIsNone(crm.leads[lead_id]["owner"])
        with self.assertRaises(ValueError):
            crm.convert(lead_id, 100, "m1")
        self.assertEqual(crm.opps, {})
        self.assertEqual(crm.leads[lead_id]["status"], "qualified")

    def test_opportunity_shape_and_ids(self):
        first_lead = make_qualified(self.crm, email="1@x.com")
        second_lead = make_qualified(self.crm, email="2@x.com")
        with self.assertRaises(ValueError):
            self.crm.convert("L404", 10, "m1")
        o1 = self.crm.convert(first_lead, 1000, "m1")
        o2 = self.crm.convert(second_lead, 2000, "m1")
        self.assertEqual((o1, o2), ("O1", "O2"))
        opp = self.crm.opps[o1]
        self.assertEqual(
            set(opp),
            {"id", "lead_id", "owner", "amount", "original_amount", "stage"},
        )
        self.assertEqual(opp["lead_id"], first_lead)
        self.assertEqual(opp["owner"], self.crm.leads[first_lead]["owner"])
        self.assertEqual(opp["amount"], 1000)
        self.assertEqual(opp["original_amount"], 1000)
        self.assertEqual(opp["stage"], "prospect")

    def test_lead_cannot_be_converted_twice(self):
        lead_id = make_qualified(self.crm)
        self.crm.convert(lead_id, 100, "m1")
        with self.assertRaises(ValueError):
            self.crm.convert(lead_id, 100, "m1")

    def test_failed_convert_is_atomic(self):
        lead_id = self.crm.add_lead("a@example.com", "A", "referral", "m1")
        before = snapshot(self.crm)
        with self.assertRaises(ValueError):
            self.crm.convert(lead_id, 100, "m1")
        self.assertEqual(snapshot(self.crm), before)


class TestAdvance(unittest.TestCase):
    def setUp(self):
        self.crm = build()
        self.opp_id = make_opp(self.crm)

    def test_unknown_opportunity(self):
        with self.assertRaises(ValueError):
            self.crm.advance("O404", "proposal", "m1")
        with self.assertRaises(ValueError):
            self.crm.advance(["O1"], "proposal", "m1")

    def test_invalid_stage_value(self):
        for stage in ("", "closed", "Proposal", None, 1, ["proposal"]):
            with self.assertRaises(ValueError):
                self.crm.advance(self.opp_id, stage, "m1")

    def test_stage_checked_before_permission(self):
        other = "r2" if self.crm.opps[self.opp_id]["owner"] == "r1" else "r1"
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp_id, "bogus", other)

    def test_permission(self):
        other = "r2" if self.crm.opps[self.opp_id]["owner"] == "r1" else "r1"
        with self.assertRaises(PermissionError):
            self.crm.advance(self.opp_id, "proposal", other)
        self.assertEqual(self.crm.opps[self.opp_id]["stage"], "prospect")

    def test_permission_before_final_check(self):
        self.crm.advance(self.opp_id, "proposal", "m1")
        self.crm.advance(self.opp_id, "negotiation", "m1")
        self.crm.advance(self.opp_id, "won", "m1")
        other = "r2" if self.crm.opps[self.opp_id]["owner"] == "r1" else "r1"
        with self.assertRaises(PermissionError):
            self.crm.advance(self.opp_id, "lost", other)

    def test_happy_path_and_log(self):
        owner = self.crm.opps[self.opp_id]["owner"]
        self.crm.advance(self.opp_id, "proposal", owner)
        self.crm.advance(self.opp_id, "negotiation", owner)
        self.crm.advance(self.opp_id, "won", owner)
        self.assertEqual(self.crm.opps[self.opp_id]["stage"], "won")
        self.assertEqual(self.crm.log[-3:], [
            ("advance", self.opp_id, owner),
            ("advance", self.opp_id, owner),
            ("advance", self.opp_id, owner),
        ])

    def test_lost_from_any_open_stage(self):
        for start in ("prospect", "proposal", "negotiation"):
            crm = build()
            opp_id = make_opp(crm)
            if start in ("proposal", "negotiation"):
                crm.advance(opp_id, "proposal", "m1")
            if start == "negotiation":
                crm.advance(opp_id, "negotiation", "m1")
            crm.advance(opp_id, "lost", "m1")
            self.assertEqual(crm.opps[opp_id]["stage"], "lost")

    def test_forward_skip_rejected(self):
        for stage in ("negotiation", "won"):
            with self.assertRaises(ValueError):
                self.crm.advance(self.opp_id, stage, "m1")

    def test_same_stage_rejected(self):
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp_id, "prospect", "m1")

    def test_backward_rejected(self):
        self.crm.advance(self.opp_id, "proposal", "m1")
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp_id, "prospect", "m1")

    def test_final_stage_cannot_move(self):
        self.crm.advance(self.opp_id, "lost", "m1")
        for stage in ("prospect", "proposal", "negotiation", "won", "lost"):
            with self.assertRaises(ValueError):
                self.crm.advance(self.opp_id, stage, "m1")

    def test_negotiation_manager_threshold(self):
        crm = build()
        opp_id = make_opp(crm, amount=50000)
        owner = crm.opps[opp_id]["owner"]
        crm.advance(opp_id, "proposal", owner)
        crm.advance(opp_id, "negotiation", owner)
        self.assertEqual(crm.opps[opp_id]["stage"], "negotiation")

        crm2 = build()
        opp2 = make_opp(crm2, amount=50001)
        owner2 = crm2.opps[opp2]["owner"]
        crm2.advance(opp2, "proposal", owner2)
        with self.assertRaises(PermissionError):
            crm2.advance(opp2, "negotiation", owner2)
        self.assertEqual(crm2.opps[opp2]["stage"], "proposal")
        crm2.advance(opp2, "negotiation", "m1")
        self.assertEqual(crm2.opps[opp2]["stage"], "negotiation")

    def test_won_frees_slot_and_assigns(self):
        crm = build([
            {"id": "m1", "role": "manager", "capacity": 9},
            {"id": "r1", "role": "rep", "capacity": 1},
        ])
        l1 = crm.add_lead("1@x.com", "A", "referral", "m1")
        l2 = crm.add_lead("2@x.com", "B", "referral", "m1")
        self.assertEqual(crm.leads[l1]["owner"], "r1")
        self.assertIsNone(crm.leads[l2]["owner"])
        crm.qualify(l1, "m1")
        opp_id = crm.convert(l1, 100, "m1")
        crm.advance(opp_id, "proposal", "m1")
        crm.advance(opp_id, "negotiation", "m1")
        crm.advance(opp_id, "won", "m1")
        self.assertEqual(crm.leads[l2]["owner"], "r1")
        self.assertEqual(crm.log[-2:], [
            ("advance", opp_id, "m1"),
            ("assign", l2, "system"),
        ])

    def test_lost_frees_slot_and_assigns(self):
        crm = build([
            {"id": "m1", "role": "manager", "capacity": 9},
            {"id": "r1", "role": "rep", "capacity": 1},
        ])
        l1 = crm.add_lead("1@x.com", "A", "referral", "m1")
        l2 = crm.add_lead("2@x.com", "B", "referral", "m1")
        crm.qualify(l1, "m1")
        opp_id = crm.convert(l1, 100, "m1")
        crm.advance(opp_id, "lost", "m1")
        self.assertEqual(crm.leads[l2]["owner"], "r1")

    def test_non_final_advance_does_not_assign(self):
        crm = build([
            {"id": "m1", "role": "manager", "capacity": 9},
            {"id": "r1", "role": "rep", "capacity": 1},
        ])
        l1 = crm.add_lead("1@x.com", "A", "referral", "m1")
        l2 = crm.add_lead("2@x.com", "B", "referral", "m1")
        crm.qualify(l1, "m1")
        opp_id = crm.convert(l1, 100, "m1")
        crm.advance(opp_id, "proposal", "m1")
        self.assertIsNone(crm.leads[l2]["owner"])

    def test_failed_advance_is_atomic(self):
        before = snapshot(self.crm)
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp_id, "won", "m1")
        self.assertEqual(snapshot(self.crm), before)


class TestDiscount(unittest.TestCase):
    def setUp(self):
        self.crm = build()
        self.opp_id = make_opp(self.crm, amount=1000)

    def test_unknown_opportunity(self):
        with self.assertRaises(ValueError):
            self.crm.discount("O404", 10, "m1")

    def test_bad_percentages(self):
        for pct in (0, 31, -1, 1.0, "10", None, True, False, [10]):
            with self.assertRaises(ValueError):
                self.crm.discount(self.opp_id, pct, "m1")
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 1000)
        self.assertEqual(self.crm.log[-1], ("convert", self.opp_id, "m1"))

    def test_pct_checked_before_permission(self):
        other = "r2" if self.crm.opps[self.opp_id]["owner"] == "r1" else "r1"
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp_id, 99, other)

    def test_permission(self):
        other = "r2" if self.crm.opps[self.opp_id]["owner"] == "r1" else "r1"
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp_id, 10, other)

    def test_final_stage_rejected(self):
        self.crm.advance(self.opp_id, "lost", "m1")
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp_id, 10, "m1")

    def test_final_check_before_non_manager_limit(self):
        self.crm.advance(self.opp_id, "lost", "m1")
        owner = self.crm.opps[self.opp_id]["owner"]
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp_id, 11, owner)

    def test_non_manager_limit(self):
        owner = self.crm.opps[self.opp_id]["owner"]
        self.crm.discount(self.opp_id, 10, owner)
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 900)
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp_id, 11, owner)

    def test_manager_may_use_thirty(self):
        self.crm.discount(self.opp_id, 30, "m1")
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 700)
        self.assertEqual(self.crm.opps[self.opp_id]["original_amount"], 1000)
        self.assertEqual(self.crm.log[-1], ("discount", self.opp_id, "m1"))

    def test_cumulative_cap(self):
        self.crm.discount(self.opp_id, 30, "m1")   # 700, exactly 70%
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp_id, 1, "m1")
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 700)

    def test_floor_division(self):
        self.crm.discount(self.opp_id, 1, "m1")
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 990)

    def test_cumulative_across_calls(self):
        self.crm.discount(self.opp_id, 20, "m1")   # 800
        self.crm.discount(self.opp_id, 10, "m1")   # 720
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 720)
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp_id, 3, "m1")  # 698 < 700

    def test_failed_discount_is_atomic(self):
        before = snapshot(self.crm)
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp_id, 40, "m1")
        self.assertEqual(snapshot(self.crm), before)

        self.crm.discount(self.opp_id, 30, "m1")
        state = snapshot(self.crm)
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp_id, 5, "m1")
        self.assertEqual(snapshot(self.crm), state)


class TestTransfer(unittest.TestCase):
    def setUp(self):
        self.crm = build()
        self.opp_id = make_opp(self.crm)
        self.owner = self.crm.opps[self.opp_id]["owner"]

    def other_rep(self):
        return "r2" if self.owner == "r1" else "r1"

    def test_unknown_opportunity_checked_first(self):
        with self.assertRaises(ValueError):
            self.crm.transfer("O404", "r1", "r1")
        with self.assertRaises(ValueError):
            self.crm.transfer("O404", "r1", "m1")

    def test_only_manager_may_transfer(self):
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.opp_id, self.other_rep(), self.owner)
        self.assertEqual(self.crm.opps[self.opp_id]["owner"], self.owner)

    def test_new_owner_must_be_known_rep(self):
        for target in ("ghost", None, 1, "m1", ["r1"]):
            with self.assertRaises(ValueError):
                self.crm.transfer(self.opp_id, target, "m1")

    def test_final_opportunity_rejected(self):
        self.crm.advance(self.opp_id, "proposal", "m1")
        self.crm.advance(self.opp_id, "negotiation", "m1")
        self.crm.advance(self.opp_id, "won", "m1")
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp_id, self.other_rep(), "m1")

    def test_same_owner_rejected(self):
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp_id, self.owner, "m1")

    def test_target_at_capacity_rejected(self):
        crm = build([
            {"id": "m1", "role": "manager", "capacity": 9},
            {"id": "r1", "role": "rep", "capacity": 5},
            {"id": "r2", "role": "rep", "capacity": 1},
        ])
        opp_id = make_opp(crm)
        owner = crm.opps[opp_id]["owner"]
        self.assertEqual(owner, "r1")
        # r2 has load 0, so the next lead goes to r2 and fills it.
        crm.add_lead("full@x.com", "F", "web", "m1")
        self.assertEqual(crm._load("r2"), 1)
        with self.assertRaises(ValueError):
            crm.transfer(opp_id, "r2", "m1")
        self.assertEqual(crm.opps[opp_id]["owner"], "r1")

    def test_successful_transfer(self):
        target = self.other_rep()
        self.crm.transfer(self.opp_id, target, "m1")
        self.assertEqual(self.crm.opps[self.opp_id]["owner"], target)
        self.assertEqual(self.crm.log[-1], ("transfer", self.opp_id, "m1"))
        self.assertEqual(self.crm.opps[self.opp_id]["stage"], "prospect")

    def test_failed_transfer_is_atomic(self):
        before = snapshot(self.crm)
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp_id, self.owner, "m1")
        self.assertEqual(snapshot(self.crm), before)

    def test_transfer_changes_future_assignment_balance(self):
        # After moving the opp away, the previous owner has a spare slot.
        crm = build([
            {"id": "m1", "role": "manager", "capacity": 9},
            {"id": "r1", "role": "rep", "capacity": 2},
            {"id": "r2", "role": "rep", "capacity": 3},
        ])
        opp_id = make_opp(crm)
        self.assertEqual(crm.opps[opp_id]["owner"], "r1")
        crm.transfer(opp_id, "r2", "m1")
        lead_id = crm.add_lead("new@x.com", "N", "web", "m1")
        self.assertEqual(crm.leads[lead_id]["owner"], "r1")


class TestForecast(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(build().forecast(), {"open": 0, "weighted": 0, "won": 0})

    def test_weighted_and_open(self):
        crm = build()
        o1 = make_opp(crm, amount=999, email="1@x.com")
        o2 = make_opp(crm, amount=1234, email="2@x.com")
        o3 = make_opp(crm, amount=500, email="3@x.com")
        crm.advance(o2, "proposal", "m1")
        crm.advance(o3, "proposal", "m1")
        crm.advance(o3, "negotiation", "m1")
        result = crm.forecast()
        self.assertEqual(result["open"], 3)
        self.assertEqual(result["weighted"], 99 + 370 + 300)
        self.assertEqual(result["won"], 0)
        self.assertEqual(set(result), {"open", "weighted", "won"})

    def test_won_and_lost_excluded(self):
        crm = build()
        o1 = make_opp(crm, amount=1000, email="1@x.com")
        o2 = make_opp(crm, amount=2000, email="2@x.com")
        crm.advance(o1, "proposal", "m1")
        crm.advance(o1, "negotiation", "m1")
        crm.advance(o1, "won", "m1")
        crm.advance(o2, "lost", "m1")
        result = crm.forecast()
        self.assertEqual(result, {"open": 0, "weighted": 0, "won": 1000})

    def test_uses_discounted_amount(self):
        crm = build()
        opp_id = make_opp(crm, amount=1000)
        crm.discount(opp_id, 30, "m1")
        self.assertEqual(crm.forecast()["weighted"], 700 * 10 // 100)
        crm.advance(opp_id, "proposal", "m1")
        self.assertEqual(crm.forecast()["weighted"], 700 * 30 // 100)

    def test_forecast_does_not_log(self):
        crm = build()
        make_opp(crm)
        log_before = list(crm.log)
        crm.forecast()
        self.assertEqual(crm.log, log_before)


class TestLogDiscipline(unittest.TestCase):
    def test_full_happy_path_log(self):
        crm = build([
            {"id": "m1", "role": "manager", "capacity": 9},
            {"id": "r1", "role": "rep", "capacity": 1},
        ])
        l1 = crm.add_lead("1@x.com", "A", "referral", "m1")
        l2 = crm.add_lead("2@x.com", "B", "referral", "m1")
        crm.qualify(l1, "m1")
        opp_id = crm.convert(l1, 1000, "m1")
        crm.discount(opp_id, 30, "m1")
        crm.advance(opp_id, "proposal", "m1")
        crm.advance(opp_id, "negotiation", "m1")
        crm.advance(opp_id, "won", "m1")
        self.assertEqual(crm.log, [
            ("add_lead", l1, "m1"),
            ("add_lead", l2, "m1"),
            ("qualify", l1, "m1"),
            ("convert", opp_id, "m1"),
            ("discount", opp_id, "m1"),
            ("advance", opp_id, "m1"),
            ("advance", opp_id, "m1"),
            ("advance", opp_id, "m1"),
            ("assign", l2, "system"),
        ])

    def test_no_log_entry_for_failures(self):
        crm = build()
        lead_id = crm.add_lead("a@example.com", "A", "referral", "m1")
        count = len(crm.log)
        with self.assertRaises(PermissionError):
            crm.qualify(lead_id, "r2" if crm.leads[lead_id]["owner"] == "r1" else "r1")
        self.assertEqual(len(crm.log), count)


class TestLoadAccounting(unittest.TestCase):
    def test_lower_load_wins_over_smaller_id(self):
        crm = build([
            {"id": "m1", "role": "manager", "capacity": 9},
            {"id": "a", "role": "rep", "capacity": 2},
            {"id": "z", "role": "rep", "capacity": 2},
        ])
        first = crm.add_lead("1@x.com", "A", "web", "m1")
        second = crm.add_lead("2@x.com", "B", "web", "m1")
        self.assertEqual(crm.leads[first]["owner"], "a")
        self.assertEqual(crm.leads[second]["owner"], "z")

    def test_qualified_leads_still_count_toward_load(self):
        crm = build([
            {"id": "m1", "role": "manager", "capacity": 9},
            {"id": "r1", "role": "rep", "capacity": 1},
        ])
        lead_id = crm.add_lead("1@x.com", "A", "referral", "m1")
        self.assertEqual(crm._load("r1"), 1)
        crm.qualify(lead_id, "m1")
        self.assertEqual(crm._load("r1"), 1)
        queued = crm.add_lead("2@x.com", "B", "referral", "m1")
        self.assertIsNone(crm.leads[queued]["owner"])

    def test_convert_keeps_owner_load_flat(self):
        crm = build([
            {"id": "m1", "role": "manager", "capacity": 9},
            {"id": "r1", "role": "rep", "capacity": 1},
        ])
        lead_id = crm.add_lead("1@x.com", "A", "referral", "m1")
        queued = crm.add_lead("2@x.com", "B", "referral", "m1")
        self.assertIsNone(crm.leads[queued]["owner"])
        crm.qualify(lead_id, "m1")
        crm.convert(lead_id, 1000, "m1")
        self.assertEqual(crm._load("r1"), 1)
        self.assertIsNone(crm.leads[queued]["owner"])
        self.assertFalse([entry for entry in crm.log if entry[0] == "assign"])

    def test_manager_may_qualify_unowned_queued_lead(self):
        crm = build([{"id": "m1", "role": "manager", "capacity": 9}])
        lead_id = crm.add_lead("1@x.com", "A", "referral", "m1")
        self.assertIsNone(crm.leads[lead_id]["owner"])
        crm.qualify(lead_id, "m1")
        self.assertEqual(crm.leads[lead_id]["status"], "qualified")
        self.assertIsNone(crm.leads[lead_id]["owner"])
        self.assertFalse([entry for entry in crm.log if entry[0] == "assign"])


class TestQueueOrdering(unittest.TestCase):
    def test_additions_join_back_of_queue(self):
        crm = build([
            {"id": "m1", "role": "manager", "capacity": 9},
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 1},
        ])
        l1 = crm.add_lead("1@x.com", "A", "referral", "m1")
        l2 = crm.add_lead("2@x.com", "B", "referral", "m1")
        l3 = crm.add_lead("3@x.com", "C", "referral", "m1")
        self.assertEqual(crm.leads[l1]["owner"], "r1")
        self.assertEqual(crm.leads[l2]["owner"], "r2")
        self.assertIsNone(crm.leads[l3]["owner"])
        self.assertEqual(list(crm._waiting), [l3])

        crm.qualify(l1, "m1")
        opp_id = crm.convert(l1, 100, "m1")
        crm.advance(opp_id, "proposal", "m1")
        crm.advance(opp_id, "negotiation", "m1")
        crm.advance(opp_id, "won", "m1")
        self.assertEqual(crm.leads[l3]["owner"], "r1")
        self.assertEqual(list(crm._waiting), [])

        # r2 still has no slot, so a brand new lead has to wait behind nobody.
        l4 = crm.add_lead("4@x.com", "D", "referral", "m1")
        self.assertIsNone(crm.leads[l4]["owner"])
        self.assertEqual(list(crm._waiting), [l4])


class TestNegotiationThreshold(unittest.TestCase):
    def test_discounted_amount_decides_manager_requirement(self):
        crm = build()
        opp_id = make_opp(crm, amount=60000)
        owner = crm.opps[opp_id]["owner"]
        crm.discount(opp_id, 20, "m1")           # 48000, now under the limit
        crm.advance(opp_id, "proposal", owner)
        crm.advance(opp_id, "negotiation", owner)
        self.assertEqual(crm.opps[opp_id]["stage"], "negotiation")


class TestLeadIdentity(unittest.TestCase):
    def test_duplicate_ignores_case_and_surrounding_space(self):
        crm = build()
        first = crm.add_lead("  A@B.com ", "Ann", "web", "m1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            crm.add_lead("a@b.COM   ", "Other", "referral", "m1")
        self.assertEqual(ctx.exception.existing_id, first)
        self.assertEqual(list(crm.leads), [first])

    def test_duplicate_does_not_consume_a_lead_id(self):
        crm = build()
        first = crm.add_lead("a@b.com", "Ann", "web", "m1")
        with self.assertRaises(DuplicateLeadError):
            crm.add_lead("A@B.COM", "Ann", "web", "m1")
        second = crm.add_lead("c@d.com", "Cid", "web", "m1")
        self.assertEqual((first, second), ("L1", "L2"))

    def test_different_emails_are_not_duplicates(self):
        crm = build()
        first = crm.add_lead("a@b.com", "Ann", "web", "m1")
        second = crm.add_lead("a@c.com", "Ann", "web", "m1")
        self.assertNotEqual(first, second)
        self.assertEqual(len(crm.leads), 2)

    def test_free_domain_scoring_is_case_insensitive(self):
        crm = build()
        lead_id = crm.add_lead("Ann@GMAIL.COM", "Ann", "web", "m1")
        self.assertEqual(crm.leads[lead_id]["score"], 10)


if __name__ == "__main__":
    unittest.main()
