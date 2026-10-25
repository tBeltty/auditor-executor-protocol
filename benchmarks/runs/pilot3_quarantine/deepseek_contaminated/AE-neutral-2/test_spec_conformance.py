"""Independent, spec-derived tests for crm.py (specs/crm.md).

These are written from the specification text alone, with no reference to the
implementation, so that a test passing here is evidence about the spec rather
than about the way the code happens to be structured.
"""

import copy
import unittest

from crm import CRM, DuplicateLeadError


def snapshot(crm):
    return (
        copy.deepcopy(crm.leads),
        copy.deepcopy(crm.opps),
        copy.deepcopy(crm.log),
        copy.deepcopy(crm.waiting),
    )


def crm_of(*reps):
    return CRM(list(reps))


def rep(rid, capacity):
    return {"id": rid, "role": "rep", "capacity": capacity}


def manager(rid, capacity=99):
    return {"id": rid, "role": "manager", "capacity": capacity}


class TestGeneralRules(unittest.TestCase):
    def test_constructor_exposes_required_attributes(self):
        crm = crm_of(rep("r1", 1))
        self.assertEqual(crm.leads, {})
        self.assertEqual(crm.opps, {})
        self.assertEqual(crm.log, [])

    def test_unknown_actor_is_permission_error_before_anything_else(self):
        crm = crm_of(rep("r1", 1))
        calls = [
            lambda: crm.add_lead("bad", "", "bogus", "nobody"),
            lambda: crm.qualify("L404", "nobody"),
            lambda: crm.convert("L404", -5, "nobody"),
            lambda: crm.advance("O404", "bogus", "nobody"),
            lambda: crm.discount("O404", 999, "nobody"),
            lambda: crm.transfer("O404", "nobody", "nobody"),
        ]
        for call in calls:
            with self.assertRaises(PermissionError):
                call()
        self.assertEqual(crm.log, [])
        self.assertEqual(crm.leads, {})
        self.assertEqual(crm.opps, {})

    def test_non_string_actor_is_permission_error(self):
        crm = crm_of(rep("r1", 1))
        for actor in (None, 7, ["r1"], ("r1",)):
            with self.assertRaises(PermissionError, msg=repr(actor)):
                crm.qualify("L1", actor)

    def test_unknown_entity_ids_are_value_errors(self):
        crm = crm_of(rep("r1", 2), manager("m1"))
        for bad in (["L1"], {"L1": 1}, {"L1"}, None, 1, 1.0):
            with self.assertRaises(ValueError, msg=repr(bad)):
                crm.qualify(bad, "m1")
            with self.assertRaises(ValueError, msg=repr(bad)):
                crm.convert(bad, 10, "m1")
            with self.assertRaises(ValueError, msg=repr(bad)):
                crm.advance(bad, "proposal", "m1")
            with self.assertRaises(ValueError, msg=repr(bad)):
                crm.discount(bad, 5, "m1")
            with self.assertRaises(ValueError, msg=repr(bad)):
                crm.transfer(bad, "r1", "m1")
        self.assertEqual(crm.log, [])

    def test_failed_calls_change_nothing(self):
        crm = crm_of(rep("r1", 1), manager("m1"))
        crm.add_lead("a@example.com", "A", "referral", "r1")
        before = snapshot(crm)
        with self.assertRaises(ValueError):
            crm.add_lead("bad", "A", "web", "r1")
        self.assertEqual(snapshot(crm), before)
        with self.assertRaises(ValueError):
            crm.convert("L1", 10, "r1")  # lead is still "new"
        self.assertEqual(snapshot(crm), before)
        crm.qualify("L1", "r1")
        crm.convert("L1", 10, "r1")
        before = snapshot(crm)
        with self.assertRaises(ValueError):
            crm.advance("O1", "won", "r1")  # skipping a stage
        self.assertEqual(snapshot(crm), before)
        with self.assertRaises(ValueError):
            crm.discount("O1", 31, "m1")
        self.assertEqual(snapshot(crm), before)


class TestAddLead(unittest.TestCase):
    def test_record_contents(self):
        crm = crm_of(rep("r1", 5))
        lid = crm.add_lead("  Bob@Corp.example  ", "  Bob B  ", "event", "r1")
        self.assertEqual(lid, "L1")
        self.assertEqual(
            crm.leads["L1"],
            {
                "id": "L1",
                "email": "bob@corp.example",
                "name": "Bob B",
                "source": "event",
                "score": 35,
                "owner": "r1",
                "status": "new",
            },
        )
        self.assertEqual(crm.log, [("add_lead", "L1", "r1")])

    def test_score_matrix(self):
        crm = crm_of(rep("r1", 100))
        cases = [
            ("a@gmail.com", "web", 10),
            ("b@yahoo.com", "referral", 30),
            ("c@outlook.com", "event", 20),
            ("d@corp.example", "web", 25),
            ("e@corp.example", "event", 35),
            ("f@corp.example", "referral", 45),
            ("G@GMAIL.COM", "web", 10),
        ]
        for email, source, expected in cases:
            lid = crm.add_lead(email, "N", source, "r1")
            self.assertEqual(crm.leads[lid]["score"], expected, (email, source))

    def test_email_rejections(self):
        crm = crm_of(rep("r1", 5))
        bad = [
            "", "   ", "plain", "@corp.example", "a@", "a@corp",
            "a@.corp", "a@corp.", "a@@corp.example", "a@b@corp.example",
            5, None, b"a@corp.example", ["a@corp.example"],
        ]
        for email in bad:
            with self.assertRaises(ValueError, msg=repr(email)):
                crm.add_lead(email, "N", "web", "r1")
        self.assertEqual(crm.leads, {})
        self.assertEqual(crm.log, [])

    def test_email_accepts_interior_dot(self):
        crm = crm_of(rep("r1", 5))
        for email in ["a@b.c", "a@b..c", "a.b@c.d", "a@b.c.d"]:
            lid = crm.add_lead(email, "N", "web", "r1")
            self.assertEqual(crm.leads[lid]["email"], email)

    def test_name_rejections(self):
        crm = crm_of(rep("r1", 5))
        for name in ["", "  \t ", 3, None, ["N"]]:
            with self.assertRaises(ValueError, msg=repr(name)):
                crm.add_lead("a@corp.example", name, "web", "r1")
        self.assertEqual(crm.leads, {})

    def test_source_rejections(self):
        crm = crm_of(rep("r1", 5))
        for source in ["phone", "WEB", "web ", "", None, 1]:
            with self.assertRaises(ValueError, msg=repr(source)):
                crm.add_lead("a@corp.example", "N", source, "r1")

    def test_duplicate_uses_normalized_email_and_keeps_state(self):
        crm = crm_of(rep("r1", 5))
        first = crm.add_lead("a@corp.example", "A", "web", "r1")
        before = snapshot(crm)
        with self.assertRaises(DuplicateLeadError) as ctx:
            crm.add_lead("  A@CORP.EXAMPLE ", "Other", "referral", "r1")
        self.assertEqual(ctx.exception.existing_id, first)
        self.assertEqual(snapshot(crm), before)

    def test_duplicate_error_is_exception_subclass(self):
        err = DuplicateLeadError("L3")
        self.assertIsInstance(err, Exception)
        self.assertEqual(err.existing_id, "L3")

    def test_ids_count_successful_creations_only(self):
        crm = crm_of(rep("r1", 5))
        self.assertEqual(crm.add_lead("a@corp.example", "A", "web", "r1"), "L1")
        with self.assertRaises(DuplicateLeadError):
            crm.add_lead("a@corp.example", "A", "web", "r1")
        self.assertEqual(crm.add_lead("b@corp.example", "B", "web", "r1"), "L2")

    def test_owner_is_least_loaded_rep(self):
        crm = crm_of(rep("r1", 3), rep("r2", 3))
        crm.add_lead("a@corp.example", "A", "web", "r1")
        crm.add_lead("b@corp.example", "B", "web", "r1")
        owners = [crm.leads["L1"]["owner"], crm.leads["L2"]["owner"]]
        self.assertEqual(owners, ["r1", "r2"])

    def test_tie_break_is_smallest_id_in_string_order(self):
        crm = crm_of(rep("b", 3), rep("a", 3), rep("c", 3))
        crm.add_lead("x@corp.example", "X", "web", "a")
        self.assertEqual(crm.leads["L1"]["owner"], "a")
        crm = crm_of(rep("r2", 3), rep("r10", 3))
        crm.add_lead("x@corp.example", "X", "web", "r2")
        self.assertEqual(crm.leads["L1"]["owner"], "r10")

    def test_skips_reps_at_capacity(self):
        crm = crm_of(rep("r1", 1), rep("r2", 1))
        crm.add_lead("a@corp.example", "A", "web", "r1")
        self.assertEqual(crm.leads["L1"]["owner"], "r1")
        crm.add_lead("b@corp.example", "B", "web", "r1")
        self.assertEqual(crm.leads["L2"]["owner"], "r2")

    def test_managers_never_own(self):
        crm = crm_of(manager("m1", 10), rep("r1", 10))
        crm.add_lead("a@corp.example", "A", "web", "m1")
        self.assertEqual(crm.leads["L1"]["owner"], "r1")

        crm = crm_of(manager("m1", 10))
        crm.add_lead("a@corp.example", "A", "web", "m1")
        self.assertIsNone(crm.leads["L1"]["owner"])

    def test_capacity_zero_or_no_reps_queues_lead(self):
        crm = crm_of(rep("r1", 0), manager("m1"))
        crm.add_lead("a@corp.example", "A", "web", "m1")
        self.assertIsNone(crm.leads["L1"]["owner"])

        crm = CRM([])
        # no known users at all, so no valid actor exists
        with self.assertRaises(PermissionError):
            crm.add_lead("a@corp.example", "A", "web", "r1")

    def test_queue_is_fifo(self):
        crm = crm_of(rep("r1", 1))
        crm.add_lead("a@corp.example", "A", "referral", "r1")
        crm.add_lead("b@corp.example", "B", "referral", "r1")
        crm.add_lead("c@corp.example", "C", "referral", "r1")
        self.assertIsNone(crm.leads["L2"]["owner"])
        self.assertIsNone(crm.leads["L3"]["owner"])
        crm.qualify("L1", "r1")
        oid = crm.convert("L1", 100, "r1")
        crm.advance(oid, "lost", "r1")
        self.assertEqual(crm.leads["L2"]["owner"], "r1")
        self.assertIsNone(crm.leads["L3"]["owner"])


class TestQualify(unittest.TestCase):
    def setUp(self):
        self.crm = crm_of(rep("r1", 3), rep("r2", 3), manager("m1"))
        self.lid = self.crm.add_lead("a@corp.example", "A", "referral", "r1")

    def test_owner_qualifies(self):
        self.crm.qualify(self.lid, "r1")
        self.assertEqual(self.crm.leads[self.lid]["status"], "qualified")
        self.assertEqual(self.crm.log[-1], ("qualify", self.lid, "r1"))

    def test_manager_qualifies(self):
        self.crm.qualify(self.lid, "m1")
        self.assertEqual(self.crm.leads[self.lid]["status"], "qualified")

    def test_other_rep_denied(self):
        before = snapshot(self.crm)
        with self.assertRaises(PermissionError):
            self.crm.qualify(self.lid, "r2")
        self.assertEqual(snapshot(self.crm), before)

    def test_missing_lead(self):
        with self.assertRaises(ValueError):
            self.crm.qualify("L99", "r1")

    def test_status_must_be_new(self):
        self.crm.qualify(self.lid, "r1")
        before = snapshot(self.crm)
        with self.assertRaises(ValueError):
            self.crm.qualify(self.lid, "r1")
        self.assertEqual(snapshot(self.crm), before)

    def test_score_floor(self):
        low = self.crm.add_lead("b@corp.example", "B", "web", "r1")  # 25
        self.assertEqual(self.crm.leads[low]["score"], 25)
        with self.assertRaises(ValueError):
            self.crm.qualify(low, "m1")
        self.assertEqual(self.crm.leads[low]["status"], "new")

        exact = self.crm.add_lead("c@yahoo.com", "C", "referral", "r1")  # 30
        self.crm.qualify(exact, "m1")
        self.assertEqual(self.crm.leads[exact]["status"], "qualified")

    def test_permission_before_status_and_score(self):
        low = self.crm.add_lead("b@corp.example", "B", "web", "r1")  # 25, r2 owns
        self.assertEqual(self.crm.leads[low]["owner"], "r2")
        with self.assertRaises(PermissionError):
            self.crm.qualify(low, "r1")
        self.crm.qualify(self.lid, "r1")
        with self.assertRaises(PermissionError):
            self.crm.qualify(self.lid, "r2")

    def test_qualifying_does_not_change_load(self):
        crm = crm_of(rep("r1", 1))
        crm.add_lead("a@corp.example", "A", "referral", "r1")
        crm.qualify("L1", "r1")
        crm.add_lead("b@corp.example", "B", "referral", "r1")
        self.assertIsNone(crm.leads["L2"]["owner"])


class TestConvert(unittest.TestCase):
    def setUp(self):
        self.crm = crm_of(rep("r1", 3), rep("r2", 3), manager("m1"))
        self.lid = self.crm.add_lead("a@corp.example", "A", "referral", "r1")
        self.crm.qualify(self.lid, "r1")

    def test_creates_opportunity(self):
        oid = self.crm.convert(self.lid, 500, "r1")
        self.assertEqual(oid, "O1")
        self.assertEqual(
            self.crm.opps["O1"],
            {
                "id": "O1",
                "lead_id": self.lid,
                "owner": "r1",
                "amount": 500,
                "original_amount": 500,
                "stage": "prospect",
            },
        )
        self.assertEqual(self.crm.leads[self.lid]["status"], "converted")
        self.assertEqual(self.crm.log[-1], ("convert", "O1", "r1"))

    def test_amount_validation(self):
        bad = [0, -3, True, False, 1.0, "10", None, [10]]
        for amount in bad:
            with self.assertRaises(ValueError, msg=repr(amount)):
                self.crm.convert(self.lid, amount, "r1")
        self.assertEqual(self.crm.opps, {})
        self.assertEqual(self.crm.leads[self.lid]["status"], "qualified")

    def test_length_and_type_checks_precede_permission(self):
        with self.assertRaises(ValueError):
            self.crm.convert(self.lid, 0, "r2")

    def test_status_must_be_qualified(self):
        other = self.crm.add_lead("b@corp.example", "B", "referral", "r1")
        self.assertEqual(self.crm.leads[other]["owner"], "r2")
        with self.assertRaises(ValueError):
            self.crm.convert(other, 10, "r2")

    def test_lead_without_owner_cannot_convert(self):
        crm = crm_of(rep("r1", 1), manager("m1"))
        crm.add_lead("a@corp.example", "A", "referral", "r1")
        waiting = crm.add_lead("b@corp.example", "B", "referral", "r1")
        crm.qualify(waiting, "m1")
        with self.assertRaises(ValueError):
            crm.convert(waiting, 10, "m1")
        self.assertEqual(crm.opps, {})
        self.assertEqual(crm.leads[waiting]["status"], "qualified")

    def test_opportunity_ids_count_successful_conversions(self):
        other = self.crm.add_lead("b@corp.example", "B", "referral", "r1")
        with self.assertRaises(ValueError):
            self.crm.convert(other, 10, "r2")  # not qualified
        self.assertEqual(self.crm.convert(self.lid, 10, "r1"), "O1")
        self.crm.qualify(other, "r2")
        self.assertEqual(self.crm.convert(other, 10, "r2"), "O2")

    def test_convert_does_not_release_a_slot(self):
        crm = crm_of(rep("r1", 1))
        crm.add_lead("a@corp.example", "A", "referral", "r1")
        crm.qualify("L1", "r1")
        crm.add_lead("b@corp.example", "B", "referral", "r1")
        self.assertIsNone(crm.leads["L2"]["owner"])
        crm.convert("L1", 100, "r1")
        self.assertIsNone(crm.leads["L2"]["owner"])


class TestAdvance(unittest.TestCase):
    def setUp(self):
        self.crm = crm_of(rep("r1", 3), rep("r2", 3), manager("m1"))
        self.oid = self._make(1000)

    def _make(self, amount):
        lid = self.crm.add_lead(
            "a%d@corp.example" % len(self.crm.opps), "A", "referral", "m1"
        )
        self.crm.qualify(lid, "m1")
        return self.crm.convert(lid, amount, "m1")

    def _owner(self, oid):
        return self.crm.opps[oid]["owner"]

    def _other_rep(self, oid):
        return "r2" if self._owner(oid) == "r1" else "r1"

    def test_stage_walk_to_won(self):
        owner = self._owner(self.oid)
        for stage in ("proposal", "negotiation", "won"):
            self.crm.advance(self.oid, stage, owner)
            self.assertEqual(self.crm.opps[self.oid]["stage"], stage)
        self.assertEqual(len(self.crm.log), 6)

    def test_lost_from_each_non_final_stage(self):
        for prefix in ((), ("proposal",), ("proposal", "negotiation")):
            oid = self._make(10)
            owner = self._owner(oid)
            for stage in prefix:
                self.crm.advance(oid, stage, owner)
            before_len = len(self.crm.log)
            self.crm.advance(oid, "lost", owner)
            self.assertEqual(self.crm.opps[oid]["stage"], "lost")
            self.assertEqual(self.crm.log[-1], ("advance", oid, owner))
            self.assertEqual(len(self.crm.log), before_len + 1)

    def test_rejects_unknown_opportunity(self):
        with self.assertRaises(ValueError):
            self.crm.advance("O99", "proposal", "m1")
        with self.assertRaises(ValueError):
            self.crm.advance(None, "proposal", "m1")

    def test_rejects_unknown_stage(self):
        for stage in ("prospect", "contacted", "", "Won", None, 3):
            with self.assertRaises(ValueError, msg=repr(stage)):
                self.crm.advance(self.oid, stage, "m1")
        self.assertEqual(self.crm.opps[self.oid]["stage"], "prospect")

    def test_stage_validation_precedes_permission(self):
        with self.assertRaises(ValueError):
            self.crm.advance(self.oid, "bogus", self._other_rep(self.oid))

    def test_permission_precedes_final_and_transition(self):
        owner = self._owner(self.oid)
        self.crm.advance(self.oid, "lost", owner)
        with self.assertRaises(PermissionError):
            self.crm.advance(self.oid, "negotiation", self._other_rep(self.oid))

    def test_transition_must_be_immediate_or_lost(self):
        owner = self._owner(self.oid)
        for stage in ("negotiation", "won"):
            before = snapshot(self.crm)
            with self.assertRaises(ValueError):
                self.crm.advance(self.oid, stage, owner)
            self.assertEqual(snapshot(self.crm), before)
        self.crm.advance(self.oid, "proposal", owner)
        with self.assertRaises(ValueError):
            self.crm.advance(self.oid, "won", owner)

    def test_final_stage_is_frozen(self):
        owner = self._owner(self.oid)
        for stage in ("proposal", "negotiation", "won"):
            self.crm.advance(self.oid, stage, owner)
        for stage in ("prospect", "proposal", "negotiation", "won", "lost"):
            before = snapshot(self.crm)
            with self.assertRaises(ValueError):
                self.crm.advance(self.oid, stage, owner)
            self.assertEqual(snapshot(self.crm), before)

    def test_large_negotiation_needs_manager(self):
        oid = self._make(50001)
        owner = self._owner(oid)
        self.crm.advance(oid, "proposal", owner)
        before = snapshot(self.crm)
        with self.assertRaises(PermissionError):
            self.crm.advance(oid, "negotiation", owner)
        self.assertEqual(snapshot(self.crm), before)
        self.crm.advance(oid, "negotiation", "m1")
        self.assertEqual(self.crm.opps[oid]["stage"], "negotiation")

    def test_threshold_is_strictly_greater_than_50000(self):
        oid = self._make(50000)
        owner = self._owner(oid)
        self.crm.advance(oid, "proposal", owner)
        self.crm.advance(oid, "negotiation", owner)
        self.assertEqual(self.crm.opps[oid]["stage"], "negotiation")

    def test_threshold_uses_current_amount(self):
        oid = self._make(60000)
        owner = self._owner(oid)
        self.crm.discount(oid, 30, "m1")  # 42000
        self.crm.advance(oid, "proposal", owner)
        self.crm.advance(oid, "negotiation", owner)
        self.assertEqual(self.crm.opps[oid]["stage"], "negotiation")

    def test_large_opportunity_can_be_lost_without_manager(self):
        oid = self._make(90000)
        self.crm.advance(oid, "lost", self._owner(oid))
        self.assertEqual(self.crm.opps[oid]["stage"], "lost")

    def test_winning_releases_one_slot_and_assigns_oldest_waiter(self):
        crm = crm_of(rep("r1", 1), rep("r2", 1))
        crm.add_lead("a@corp.example", "A", "referral", "r1")  # L1 -> r1
        crm.add_lead("b@corp.example", "B", "referral", "r1")  # L2 -> r2
        crm.add_lead("c@corp.example", "C", "referral", "r1")  # L3 waiting
        crm.add_lead("d@corp.example", "D", "referral", "r1")  # L4 waiting
        self.assertEqual(
            [crm.leads[i]["owner"] for i in ("L1", "L2", "L3", "L4")],
            ["r1", "r2", None, None],
        )
        crm.qualify("L1", "r1")
        oid = crm.convert("L1", 100, "r1")
        crm.advance(oid, "proposal", "r1")
        crm.advance(oid, "negotiation", "r1")
        crm.advance(oid, "won", "r1")
        self.assertEqual(crm.log[-2:], [("advance", oid, "r1"), ("assign", "L3", "system")])
        self.assertEqual(crm.leads["L3"]["owner"], "r1")
        self.assertIsNone(crm.leads["L4"]["owner"])

    def test_release_assigns_until_capacity_is_full(self):
        crm = crm_of(rep("r1", 3), rep("r2", 1))
        crm.add_lead("a@corp.example", "A", "referral", "r1")   # L1 -> r1
        crm.add_lead("b@corp.example", "B", "referral", "r1")   # L2 -> r2
        crm.add_lead("c@corp.example", "C", "referral", "r1")   # L3 -> r1
        crm.add_lead("d@corp.example", "D", "referral", "r1")   # L4 -> r1
        crm.add_lead("e@corp.example", "E", "referral", "r1")   # L5 waiting
        crm.add_lead("f@corp.example", "F", "referral", "r1")   # L6 waiting
        crm.add_lead("g@corp.example", "G", "referral", "r1")   # L7 waiting
        self.assertEqual(
            [crm.leads[i]["owner"] for i in ("L1", "L2", "L3", "L4", "L5", "L6", "L7")],
            ["r1", "r2", "r1", "r1", None, None, None],
        )
        crm.qualify("L2", "r2")
        oid = crm.convert("L2", 100, "r2")
        crm.advance(oid, "lost", "r2")
        # r2 has capacity 1 and now zero load: exactly one waiter joins.
        self.assertEqual(crm.leads["L5"]["owner"], "r2")
        self.assertIsNone(crm.leads["L6"]["owner"])
        self.assertIsNone(crm.leads["L7"]["owner"])
        self.assertEqual(crm.log[-2:], [("advance", oid, "r2"), ("assign", "L5", "system")])

    def test_no_assignment_when_queue_is_empty(self):
        oid = self._make(100)
        owner = self._owner(oid)
        before = len(self.crm.log)
        self.crm.advance(oid, "lost", owner)
        self.assertEqual(len(self.crm.log), before + 1)
        self.assertEqual(self.crm.log[-1], ("advance", oid, owner))


class TestDiscount(unittest.TestCase):
    def setUp(self):
        self.crm = crm_of(rep("r1", 3), rep("r2", 3), manager("m1"))
        self.oid = self._make(1000)

    def _make(self, amount, email="a@corp.example"):
        lid = self.crm.add_lead(email, "A", "referral", "r1")
        self.crm.qualify(lid, "r1")
        return self.crm.convert(lid, amount, "r1")

    def test_rep_applies_ten_percent(self):
        self.crm.discount(self.oid, 10, "r1")
        self.assertEqual(self.crm.opps[self.oid]["amount"], 900)
        self.assertEqual(self.crm.opps[self.oid]["original_amount"], 1000)
        self.assertEqual(self.crm.log[-1], ("discount", self.oid, "r1"))

    def test_rep_cannot_exceed_ten(self):
        before = snapshot(self.crm)
        with self.assertRaises(PermissionError):
            self.crm.discount(self.oid, 11, "r1")
        self.assertEqual(snapshot(self.crm), before)

    def test_manager_can_go_to_thirty(self):
        self.crm.discount(self.oid, 30, "m1")
        self.assertEqual(self.crm.opps[self.oid]["amount"], 700)

    def test_pct_bounds(self):
        for pct in (0, 31, -1, 100, True, 5.0, "5", None):
            with self.assertRaises(ValueError, msg=repr(pct)):
                self.crm.discount(self.oid, pct, "m1")
        self.assertEqual(self.crm.opps[self.oid]["amount"], 1000)

    def test_pct_checked_before_permission(self):
        with self.assertRaises(ValueError):
            self.crm.discount(self.oid, 0, "r2")

    def test_permission_before_stage(self):
        self.crm.advance(self.oid, "lost", "r1")
        with self.assertRaises(PermissionError):
            self.crm.discount(self.oid, 5, "r2")

    def test_final_stage_rejected(self):
        self.crm.advance(self.oid, "lost", "r1")
        before = snapshot(self.crm)
        with self.assertRaises(ValueError):
            self.crm.discount(self.oid, 5, "m1")
        self.assertEqual(snapshot(self.crm), before)

    def test_cumulative_cap_uses_original_amount(self):
        self.crm.discount(self.oid, 30, "m1")
        with self.assertRaises(ValueError):
            self.crm.discount(self.oid, 1, "m1")
        self.assertEqual(self.crm.opps[self.oid]["amount"], 700)

    def test_cumulative_cap_is_exact_at_thirty(self):
        crm = crm_of(rep("r1", 3), manager("m1"))
        lid = crm.add_lead("a@corp.example", "A", "referral", "r1")
        crm.qualify(lid, "r1")
        oid = crm.convert(lid, 100, "r1")
        crm.discount(oid, 30, "m1")
        self.assertEqual(crm.opps[oid]["amount"], 70)
        with self.assertRaises(ValueError):
            crm.discount(oid, 1, "m1")

    def test_flooring_can_push_past_the_cap(self):
        crm = crm_of(rep("r1", 3), manager("m1"))
        lid = crm.add_lead("a@corp.example", "A", "referral", "r1")
        crm.qualify(lid, "r1")
        oid = crm.convert(lid, 101, "r1")
        # 101 * 70 // 100 == 70, which is more than 30% off 101 -> rejected.
        with self.assertRaises(ValueError):
            crm.discount(oid, 30, "m1")
        self.assertEqual(crm.opps[oid]["amount"], 101)

    def test_amount_uses_floor_division(self):
        crm = crm_of(rep("r1", 3), manager("m1"))
        lid = crm.add_lead("a@corp.example", "A", "referral", "r1")
        crm.qualify(lid, "r1")
        oid = crm.convert(lid, 999, "r1")
        crm.discount(oid, 10, "r1")
        self.assertEqual(crm.opps[oid]["amount"], 899)

    def test_manager_may_discount_someone_elses_opportunity(self):
        self.crm.discount(self.oid, 5, "m1")
        self.assertEqual(self.crm.opps[self.oid]["amount"], 950)

    def test_unknown_opportunity(self):
        with self.assertRaises(ValueError):
            self.crm.discount("O99", 5, "m1")


class TestTransfer(unittest.TestCase):
    def setUp(self):
        self.crm = crm_of(rep("r1", 2), rep("r2", 2), rep("r3", 1), manager("m1"))
        self.crm.add_lead("a@corp.example", "A", "referral", "r1")
        self.crm.qualify("L1", "r1")
        self.oid = self.crm.convert("L1", 1000, "r1")

    def test_manager_moves_opportunity(self):
        self.crm.transfer(self.oid, "r2", "m1")
        self.assertEqual(self.crm.opps[self.oid]["owner"], "r2")
        self.assertEqual(self.crm.log[-1], ("transfer", self.oid, "m1"))

    def test_only_manager_may_transfer(self):
        before = snapshot(self.crm)
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.oid, "r2", "r1")
        self.assertEqual(snapshot(self.crm), before)

    def test_target_must_be_rep(self):
        for target in ("m1", "ghost", None, 3):
            with self.assertRaises(ValueError, msg=repr(target)):
                self.crm.transfer(self.oid, target, "m1")
        self.assertEqual(self.crm.opps[self.oid]["owner"], "r1")

    def test_target_must_differ(self):
        with self.assertRaises(ValueError):
            self.crm.transfer(self.oid, "r1", "m1")

    def test_final_opportunity_rejected(self):
        self.crm.advance(self.oid, "lost", "r1")
        before = snapshot(self.crm)
        with self.assertRaises(ValueError):
            self.crm.transfer(self.oid, "r2", "m1")
        self.assertEqual(snapshot(self.crm), before)

    def test_target_at_capacity_rejected(self):
        crm = crm_of(rep("r1", 2), rep("r2", 1), manager("m1"))
        crm.add_lead("a@corp.example", "A", "referral", "r1")
        crm.qualify("L1", "r1")
        oid = crm.convert("L1", 1000, "r1")
        crm.add_lead("b@corp.example", "B", "referral", "r1")  # fills r2 (cap 1)
        self.assertEqual(crm.leads["L2"]["owner"], "r2")
        with self.assertRaises(ValueError):
            crm.transfer(oid, "r2", "m1")
        self.assertEqual(crm.opps[oid]["owner"], "r1")

    def test_transfer_appends_only_its_own_log_entry(self):
        before = len(self.crm.log)
        self.crm.transfer(self.oid, "r2", "m1")
        self.assertEqual(len(self.crm.log), before + 1)
        self.assertEqual(self.crm.log[-1], ("transfer", self.oid, "m1"))

    def test_transfer_does_not_reassign_leads(self):
        self.crm.add_lead("b@corp.example", "B", "referral", "r1")  # r2
        self.crm.add_lead("c@corp.example", "C", "referral", "r1")  # r3
        before = {lid: lead["owner"] for lid, lead in self.crm.leads.items()}
        self.crm.transfer(self.oid, "r2", "m1")
        after = {lid: lead["owner"] for lid, lead in self.crm.leads.items()}
        self.assertEqual(before, after)

    def test_transfer_does_not_move_leads(self):
        self.crm.transfer(self.oid, "r2", "m1")
        self.assertEqual(self.crm.leads["L1"]["owner"], "r1")
        self.assertEqual(self.crm.leads["L1"]["status"], "converted")


class TestForecast(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(crm_of(rep("r1", 1)).forecast(), {"open": 0, "weighted": 0, "won": 0})

    def test_mixed_pipeline(self):
        crm = crm_of(rep("r1", 10), manager("m1"))
        ids = []
        for i, amount in enumerate((1000, 2000, 3000, 4000, 5000), start=1):
            lid = crm.add_lead("a%d@corp.example" % i, "A", "referral", "r1")
            crm.qualify(lid, "r1")
            ids.append(crm.convert(lid, amount, "r1"))
        crm.advance(ids[1], "proposal", "r1")
        crm.advance(ids[2], "proposal", "r1")
        crm.advance(ids[2], "negotiation", "r1")
        crm.advance(ids[3], "proposal", "r1")
        crm.advance(ids[3], "negotiation", "r1")
        crm.advance(ids[3], "won", "r1")
        crm.advance(ids[4], "lost", "r1")
        self.assertEqual(
            crm.forecast(),
            {
                "open": 3,
                "weighted": 1000 * 10 // 100 + 2000 * 30 // 100 + 3000 * 60 // 100,
                "won": 4000,
            },
        )

    def test_weighted_uses_current_amount(self):
        crm = crm_of(rep("r1", 5), manager("m1"))
        lid = crm.add_lead("a@corp.example", "A", "referral", "r1")
        crm.qualify(lid, "r1")
        oid = crm.convert(lid, 1000, "r1")
        crm.discount(oid, 10, "m1")
        self.assertEqual(crm.forecast(), {"open": 1, "weighted": 90, "won": 0})

    def test_won_uses_current_amount(self):
        crm = crm_of(rep("r1", 5), manager("m1"))
        lid = crm.add_lead("a@corp.example", "A", "referral", "r1")
        crm.qualify(lid, "r1")
        oid = crm.convert(lid, 1000, "r1")
        crm.discount(oid, 20, "m1")
        crm.advance(oid, "proposal", "m1")
        crm.advance(oid, "negotiation", "m1")
        crm.advance(oid, "won", "m1")
        self.assertEqual(crm.forecast(), {"open": 0, "weighted": 0, "won": 800})

    def test_forecast_is_pure(self):
        crm = crm_of(rep("r1", 5))
        lid = crm.add_lead("a@corp.example", "A", "referral", "r1")
        crm.qualify(lid, "r1")
        crm.convert(lid, 1000, "r1")
        before = snapshot(crm)
        crm.forecast()
        self.assertEqual(snapshot(crm), before)

    def test_weighted_floor_division(self):
        crm = crm_of(rep("r1", 5))
        lid = crm.add_lead("a@corp.example", "A", "referral", "r1")
        crm.qualify(lid, "r1")
        oid = crm.convert(lid, 999, "r1")
        crm.advance(oid, "proposal", "r1")
        self.assertEqual(crm.forecast()["weighted"], 999 * 30 // 100)


if __name__ == "__main__":
    unittest.main()
