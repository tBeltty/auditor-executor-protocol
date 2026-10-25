"""Unit tests for crm.py. Standard library only."""

import copy
import unittest

from crm import CRM, DuplicateLeadError


def rep(rid, capacity=5):
    return {"id": rid, "role": "rep", "capacity": capacity}


def manager(rid, capacity=0):
    return {"id": rid, "role": "manager", "capacity": capacity}


def add(crm, email="lead@corp.com", name="Lead", source="referral", actor="r1"):
    return crm.add_lead(email, name, source, actor)


def make_opp(crm, email="lead@corp.com", amount=1000, actor="r1", stages=()):
    lid = add(crm, email=email, actor=actor)
    crm.qualify(lid, actor)
    oid = crm.convert(lid, amount, actor)
    for stage in stages:
        crm.advance(oid, stage, actor)
    return oid


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.crm = CRM([rep("r1", 5)])

    def test_email_must_be_string(self):
        for bad in (None, 5, 10.5, ["a@b.com"]):
            with self.assertRaisesRegex(ValueError, "email must be a string"):
                self.crm.add_lead(bad, "N", "web", "r1")
        self.assertEqual(self.crm.leads, {})
        self.assertEqual(self.crm.log, [])

    def test_email_requires_exactly_one_at(self):
        for bad in ("nope", "a@b@c.com", "a@@b.com"):
            with self.assertRaisesRegex(ValueError, "exactly one @"):
                self.crm.add_lead(bad, "N", "web", "r1")
        self.assertEqual(self.crm.leads, {})
        self.assertEqual(self.crm.log, [])

    def test_email_requires_local_part_and_inner_dot(self):
        for bad in ("@example.com", "a@b", "a@.com", "a@com.", "a@."):
            with self.assertRaises(ValueError):
                self.crm.add_lead(bad, "N", "web", "r1")
        self.assertEqual(self.crm.leads, {})
        self.assertEqual(self.crm.log, [])

    def test_name_required(self):
        for bad in ("", "   ", None, 7):
            with self.assertRaisesRegex(ValueError, "name"):
                self.crm.add_lead("a@b.com", bad, "web", "r1")
        self.assertEqual(self.crm.leads, {})
        self.assertEqual(self.crm.log, [])

    def test_source_enum(self):
        for bad in ("tv", "", "Web", None):
            with self.assertRaisesRegex(ValueError, "source"):
                self.crm.add_lead("a@b.com", "N", bad, "r1")
        self.assertEqual(self.crm.leads, {})
        self.assertEqual(self.crm.log, [])

    def test_normalized_fields_and_score(self):
        lid = self.crm.add_lead("  Alice@Example.COM ", "  Alice  ", "web", "r1")
        lead = self.crm.leads[lid]
        self.assertEqual(lead["id"], "L1")
        self.assertEqual(lead["email"], "alice@example.com")
        self.assertEqual(lead["name"], "Alice")
        self.assertEqual(lead["score"], 25)
        self.assertEqual(lead["owner"], "r1")
        self.assertEqual(lead["status"], "new")
        self.assertEqual(self.crm.log, [("add_lead", lid, "r1")])

    def test_score_by_source_and_free_domain(self):
        cases = [
            (("free@gmail.com", "web"), 10),
            (("free@yahoo.com", "referral"), 30),
            (("free@outlook.com", "event"), 20),
            (("paid@corp.com", "web"), 25),
            (("paid@corp.com", "referral"), 45),
            (("paid@corp.com", "event"), 35),
        ]
        for index, ((email, source), expected) in enumerate(cases):
            crm = CRM([rep("r1", 5)])
            lid = crm.add_lead(email, "N", source, "r1")
            self.assertEqual(crm.leads[lid]["score"], expected, (email, source))

    def test_actor_checked_first(self):
        with self.assertRaises(PermissionError):
            self.crm.add_lead("bad", "", "tv", "ghost")
        with self.assertRaises(PermissionError):
            self.crm.qualify("L404", "ghost")
        with self.assertRaises(PermissionError):
            self.crm.convert("L404", -1, "ghost")
        with self.assertRaises(PermissionError):
            self.crm.advance("O404", "bogus", "ghost")
        with self.assertRaises(PermissionError):
            self.crm.discount("O404", 99, "ghost")
        with self.assertRaises(PermissionError):
            self.crm.transfer("O404", "nobody", "ghost")
        with self.assertRaises(PermissionError):
            self.crm.add_lead("a@b.com", "N", "web", [])
        self.assertEqual(self.crm.leads, {})
        self.assertEqual(self.crm.log, [])


class DuplicateTests(unittest.TestCase):
    def setUp(self):
        self.crm = CRM([rep("r1", 5), rep("r2", 5)])

    def test_duplicate_email_raises_with_existing_id(self):
        lid = self.crm.add_lead("bob@corp.com", "Bob", "web", "r1")
        log_before = list(self.crm.log)
        with self.assertRaises(DuplicateLeadError) as ctx:
            self.crm.add_lead("  BOB@Corp.COM ", "Bobby", "referral", "r2")
        self.assertEqual(ctx.exception.existing_id, lid)
        self.assertEqual(list(self.crm.leads), [lid])
        self.assertEqual(self.crm.log, log_before)

    def test_duplicate_does_not_consume_id(self):
        first = self.crm.add_lead("a@corp.com", "A", "web", "r1")
        with self.assertRaises(DuplicateLeadError):
            self.crm.add_lead("a@corp.com", "A", "web", "r1")
        second = self.crm.add_lead("b@corp.com", "B", "web", "r1")
        self.assertEqual((first, second), ("L1", "L2"))


class AssignmentTests(unittest.TestCase):
    def test_lowest_load_then_smallest_id(self):
        crm = CRM([rep("r2", 5), rep("r1", 5)])
        ids = [crm.add_lead("u%d@corp.com" % i, "U", "web", "r1") for i in range(4)]
        self.assertEqual([crm.leads[i]["owner"] for i in ids], ["r1", "r2", "r1", "r2"])

    def test_manager_never_owns(self):
        crm = CRM([manager("m1", 5)])
        lid = crm.add_lead("x@corp.com", "X", "web", "m1")
        self.assertIsNone(crm.leads[lid]["owner"])

    def test_capacity_enforced(self):
        crm = CRM([rep("r1", 1)])
        first = crm.add_lead("a@corp.com", "A", "web", "r1")
        second = crm.add_lead("b@corp.com", "B", "web", "r1")
        self.assertEqual(crm.leads[first]["owner"], "r1")
        self.assertIsNone(crm.leads[second]["owner"])

    def test_waiting_queue_fifo_and_refill(self):
        crm = CRM([rep("r1", 1)])
        first = crm.add_lead("a@corp.com", "A", "referral", "r1")
        second = crm.add_lead("b@corp.com", "B", "referral", "r1")
        third = crm.add_lead("c@corp.com", "C", "referral", "r1")
        self.assertIsNone(crm.leads[second]["owner"])
        self.assertIsNone(crm.leads[third]["owner"])
        self.assertEqual(crm.leads[first]["status"], "new")

        crm.qualify(first, "r1")
        first_oid = crm.convert(first, 1000, "r1")
        for stage in ("proposal", "negotiation", "won"):
            crm.advance(first_oid, stage, "r1")
        self.assertEqual(crm.leads[second]["owner"], "r1")
        self.assertIsNone(crm.leads[third]["owner"])
        self.assertEqual(crm.log[-1], ("assign", second, "system"))

        crm.qualify(second, "r1")
        second_oid = crm.convert(second, 1000, "r1")
        for stage in ("proposal", "negotiation", "won"):
            crm.advance(second_oid, stage, "r1")
        self.assertEqual(crm.leads[third]["owner"], "r1")
        self.assertEqual(crm.log[-1], ("assign", third, "system"))
        self.assertEqual(crm.leads[first]["status"], "converted")


class PermissionTests(unittest.TestCase):
    def setUp(self):
        self.crm = CRM([rep("r1", 5), rep("r2", 5), manager("m1")])
        self.lid = add(self.crm, "p@corp.com", "P", "referral", "r1")
        self.crm.qualify(self.lid, "r1")
        self.oid = self.crm.convert(self.lid, 1000, "r1")

    def test_unknown_actor_is_permission_error_first(self):
        with self.assertRaises(PermissionError):
            self.crm.qualify("L404", "ghost")
        with self.assertRaises(PermissionError):
            self.crm.convert(self.lid, -5, "ghost")
        with self.assertRaises(PermissionError):
            self.crm.advance("O404", "won", "ghost")
        with self.assertRaises(PermissionError):
            self.crm.discount(self.oid, 99, "ghost")
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.oid, "r2", "ghost")
        self.assertEqual(self.crm.log, [
            ("add_lead", self.lid, "r1"),
            ("qualify", self.lid, "r1"),
            ("convert", self.oid, "r1"),
        ])

    def test_non_owner_rep_cannot_qualify(self):
        with self.assertRaises(PermissionError):
            self.crm.qualify(self.lid, "r2")
        self.assertEqual(self.crm.leads[self.lid]["status"], "converted")

    def test_non_owner_rep_cannot_advance(self):
        with self.assertRaisesRegex(PermissionError, "advance"):
            self.crm.advance(self.oid, "proposal", "r2")
        self.assertEqual(self.crm.opps[self.oid]["stage"], "prospect")

    def test_non_owner_rep_cannot_discount(self):
        with self.assertRaisesRegex(PermissionError, "discount"):
            self.crm.discount(self.oid, 5, "r2")
        self.assertEqual(self.crm.opps[self.oid]["amount"], 1000)

    def test_non_owner_rep_cannot_mutate(self):
        with self.assertRaises(PermissionError):
            self.crm.advance(self.oid, "proposal", "r2")
        with self.assertRaises(PermissionError):
            self.crm.discount(self.oid, 5, "r2")
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.oid, "r2", "r1")
        self.assertEqual(self.crm.opps[self.oid]["stage"], "prospect")
        self.assertEqual(self.crm.opps[self.oid]["amount"], 1000)

    def test_non_owner_rep_cannot_convert(self):
        crm = CRM([rep("r1", 5), rep("r2", 5), manager("m1")])
        lid = add(crm, "own@corp.com", "O", "referral", "r1")
        crm.qualify(lid, "r1")
        log_before = list(crm.log)
        with self.assertRaisesRegex(PermissionError, "convert"):
            crm.convert(lid, 1000, "r2")
        self.assertEqual(crm.opps, {})
        self.assertEqual(crm.leads[lid]["status"], "qualified")
        self.assertEqual(crm.log, log_before)
        oid = crm.convert(lid, 1000, "m1")
        self.assertEqual(crm.opps[oid]["owner"], "r1")
        self.assertEqual(crm.log[-1], ("convert", oid, "m1"))

    def test_manager_bypasses_ownership(self):
        self.crm.advance(self.oid, "proposal", "m1")
        self.crm.discount(self.oid, 5, "m1")
        self.crm.transfer(self.oid, "r2", "m1")
        self.assertEqual(self.crm.opps[self.oid]["stage"], "proposal")
        self.assertEqual(self.crm.opps[self.oid]["amount"], 950)
        self.assertEqual(self.crm.opps[self.oid]["owner"], "r2")


class QualifyTests(unittest.TestCase):
    def setUp(self):
        self.crm = CRM([rep("r1", 5), rep("r2", 5), manager("m1")])

    def test_score_below_threshold_rejected(self):
        for source, email, expected in [
            ("web", "x@gmail.com", 10),
            ("web", "x@corp.com", 25),
            ("event", "x@gmail.com", 20),
        ]:
            crm = CRM([rep("r1", 5)])
            lid = add(crm, email, "X", source, "r1")
            self.assertEqual(crm.leads[lid]["score"], expected)
            with self.assertRaisesRegex(ValueError, "score"):
                crm.qualify(lid, "r1")
            self.assertEqual(crm.leads[lid]["status"], "new")
            self.assertEqual(len(crm.log), 1)

    def test_threshold_exact_passes(self):
        lid = add(self.crm, "edge@gmail.com", "E", "referral", "r1")
        self.assertEqual(self.crm.leads[lid]["score"], 30)
        self.crm.qualify(lid, "r1")
        self.assertEqual(self.crm.leads[lid]["status"], "qualified")
        self.assertEqual(self.crm.log[-1], ("qualify", lid, "r1"))

    def test_status_must_be_new(self):
        lid = add(self.crm, "s@corp.com", "S", "referral", "r1")
        self.crm.qualify(lid, "r1")
        log_before = list(self.crm.log)
        with self.assertRaises(ValueError):
            self.crm.qualify(lid, "r1")
        self.assertEqual(self.crm.log, log_before)

    def test_unknown_lead(self):
        with self.assertRaisesRegex(ValueError, "unknown lead"):
            self.crm.qualify("L404", "r1")


class ConvertTests(unittest.TestCase):
    def setUp(self):
        self.crm = CRM([rep("r1", 5), manager("m1")])
        self.lid = add(self.crm, "c@corp.com", "C", "referral", "r1")

    def test_amount_validation(self):
        self.crm.qualify(self.lid, "r1")
        log_before = list(self.crm.log)
        for bad in (0, -1, True, False, "10", 10.5, None):
            with self.assertRaises(ValueError):
                self.crm.convert(self.lid, bad, "r1")
        self.assertEqual(self.crm.opps, {})
        self.assertEqual(self.crm.log, log_before)
        self.assertEqual(self.crm.leads[self.lid]["status"], "qualified")

    def test_requires_qualified(self):
        with self.assertRaises(ValueError):
            self.crm.convert(self.lid, 1000, "r1")
        self.assertEqual(self.crm.opps, {})

    def test_requires_owner(self):
        crm = CRM([manager("m1", 5)])
        lid = add(crm, "n@corp.com", "N", "referral", "m1")
        crm.qualify(lid, "m1")
        with self.assertRaises(ValueError):
            crm.convert(lid, 100, "m1")
        self.assertEqual(crm.opps, {})
        self.assertEqual(crm.leads[lid]["status"], "qualified")

    def test_unknown_lead_with_valid_actor(self):
        log_before = list(self.crm.log)
        with self.assertRaisesRegex(ValueError, "unknown lead"):
            self.crm.convert("L404", 100, "m1")
        self.assertEqual(self.crm.opps, {})
        self.assertEqual(self.crm.leads[self.lid]["status"], "new")
        self.assertEqual(self.crm.log, log_before)

    def test_creates_opportunity_and_marks_lead(self):
        self.crm.qualify(self.lid, "r1")
        oid = self.crm.convert(self.lid, 5000, "r1")
        self.assertEqual(oid, "O1")
        self.assertEqual(self.crm.opps[oid], {
            "id": "O1",
            "lead_id": self.lid,
            "owner": "r1",
            "amount": 5000,
            "original_amount": 5000,
            "stage": "prospect",
        })
        self.assertEqual(self.crm.leads[self.lid]["status"], "converted")
        self.assertEqual(self.crm.log[-1], ("convert", oid, "r1"))
        with self.assertRaises(ValueError):
            self.crm.convert(self.lid, 5000, "r1")
        self.assertEqual(list(self.crm.opps), ["O1"])


class AdvanceTests(unittest.TestCase):
    def setUp(self):
        self.crm = CRM([rep("r1", 5), manager("m1")])
        self.oid = make_opp(self.crm, "adv@corp.com", 1000)

    def test_stage_chain_and_final_freeze(self):
        for stage in ("proposal", "negotiation", "won"):
            self.crm.advance(self.oid, stage, "r1")
            self.assertEqual(self.crm.opps[self.oid]["stage"], stage)
            self.assertEqual(self.crm.log[-1], ("advance", self.oid, "r1"))
        with self.assertRaises(ValueError):
            self.crm.advance(self.oid, "proposal", "r1")

    def test_illegal_transitions_rejected(self):
        log_before = list(self.crm.log)
        for bad in ("won", "negotiation"):
            with self.assertRaises(ValueError):
                self.crm.advance(self.oid, bad, "r1")
        self.assertEqual(self.crm.opps[self.oid]["stage"], "prospect")
        self.assertEqual(self.crm.log, log_before)

        self.crm.advance(self.oid, "proposal", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance(self.oid, "won", "r1")
        self.assertEqual(self.crm.opps[self.oid]["stage"], "proposal")

        self.crm.advance(self.oid, "negotiation", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance(self.oid, "proposal", "r1")
        self.assertEqual(self.crm.opps[self.oid]["stage"], "negotiation")

    def test_lost_allowed_and_final(self):
        log_before = list(self.crm.log)
        self.crm.advance(self.oid, "lost", "r1")
        self.assertEqual(self.crm.opps[self.oid]["stage"], "lost")
        self.assertEqual(self.crm.log[-1], ("advance", self.oid, "r1"))
        after = list(self.crm.log)
        with self.assertRaises(ValueError):
            self.crm.advance(self.oid, "lost", "r1")
        self.assertEqual(self.crm.log, after)

    def test_lost_frees_slot_and_refills_queue(self):
        crm = CRM([rep("r1", 1), rep("r2", 1), manager("m1")])
        lid = add(crm, "lost@corp.com", "L", "referral", "r1")
        crm.qualify(lid, "r1")
        oid = crm.convert(lid, 1000, "r1")
        add(crm, "other@corp.com", "O", "referral", "r1")
        waiting = add(crm, "wait@corp.com", "W", "referral", "r1")
        self.assertIsNone(crm.leads[waiting]["owner"])
        self.assertEqual(crm.load("r1"), 1)
        crm.advance(oid, "lost", "r1")
        self.assertEqual(crm.opps[oid]["stage"], "lost")
        self.assertEqual(crm.leads[waiting]["owner"], "r1")
        self.assertEqual(
            crm.log[-2:],
            [("advance", oid, "r1"), ("assign", waiting, "system")],
        )

    def test_final_stage_immutable(self):
        for stage in ("proposal", "negotiation", "won"):
            self.crm.advance(self.oid, stage, "r1")
        log_before = list(self.crm.log)
        with self.assertRaisesRegex(ValueError, "final"):
            self.crm.advance(self.oid, "lost", "r1")
        self.assertEqual(self.crm.opps[self.oid]["stage"], "won")
        self.assertEqual(self.crm.log, log_before)

    def test_unknown_stage_and_opportunity(self):
        with self.assertRaises(ValueError):
            self.crm.advance(self.oid, "bogus", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance("O404", "proposal", "r1")

    def test_big_deal_needs_manager(self):
        big = make_opp(self.crm, "big@corp.com", 60000)
        self.crm.advance(big, "proposal", "r1")
        log_before = list(self.crm.log)
        with self.assertRaises(PermissionError):
            self.crm.advance(big, "negotiation", "r1")
        self.assertEqual(self.crm.opps[big]["stage"], "proposal")
        self.assertEqual(self.crm.log, log_before)
        self.crm.advance(big, "negotiation", "m1")
        self.assertEqual(self.crm.opps[big]["stage"], "negotiation")

    def test_exactly_50000_allowed_for_rep(self):
        edge = make_opp(self.crm, "edge2@corp.com", 50000)
        self.crm.advance(edge, "proposal", "r1")
        self.crm.advance(edge, "negotiation", "r1")
        self.assertEqual(self.crm.opps[edge]["stage"], "negotiation")


class DiscountTests(unittest.TestCase):
    def setUp(self):
        self.crm = CRM([rep("r1", 5), manager("m1")])
        self.oid = make_opp(self.crm, "d@corp.com", 1000)

    def test_pct_bounds(self):
        for bad in (0, 31, -5, True, "10", 10.0, None):
            with self.assertRaises(ValueError):
                self.crm.discount(self.oid, bad, "r1")
        self.assertEqual(self.crm.opps[self.oid]["amount"], 1000)
        self.assertEqual(len(self.crm.log), 3)

    def test_non_manager_limit(self):
        log_before = list(self.crm.log)
        with self.assertRaisesRegex(PermissionError, "10"):
            self.crm.discount(self.oid, 11, "r1")
        self.assertEqual(self.crm.opps[self.oid]["amount"], 1000)
        self.assertEqual(self.crm.log, log_before)
        self.crm.discount(self.oid, 10, "r1")
        self.assertEqual(self.crm.opps[self.oid]["amount"], 900)

    def test_manager_max_and_cumulative_floor(self):
        self.crm.discount(self.oid, 30, "m1")
        self.assertEqual(self.crm.opps[self.oid]["amount"], 700)
        log_before = list(self.crm.log)
        with self.assertRaisesRegex(ValueError, "30"):
            self.crm.discount(self.oid, 1, "m1")
        self.assertEqual(self.crm.opps[self.oid]["amount"], 700)
        self.assertEqual(self.crm.log, log_before)

    def test_unknown_opportunity_with_valid_actor(self):
        log_before = list(self.crm.log)
        with self.assertRaisesRegex(ValueError, "unknown opportunity"):
            self.crm.discount("O404", 5, "m1")
        self.assertEqual(self.crm.opps[self.oid]["amount"], 1000)
        self.assertEqual(self.crm.log, log_before)

    def test_final_stage_rejected(self):
        for stage in ("proposal", "negotiation", "won"):
            self.crm.advance(self.oid, stage, "r1")
        with self.assertRaises(ValueError):
            self.crm.discount(self.oid, 5, "m1")
        self.assertEqual(self.crm.opps[self.oid]["amount"], 1000)


class TransferTests(unittest.TestCase):
    def setUp(self):
        self.crm = CRM([rep("r1", 2), rep("r2", 1), manager("m1", 5)])
        self.oid = make_opp(self.crm, "t@corp.com", 1000)

    def test_only_manager_can_transfer(self):
        log_before = list(self.crm.log)
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.oid, "r2", "r1")
        self.assertEqual(self.crm.opps[self.oid]["owner"], "r1")
        self.assertEqual(self.crm.log, log_before)

    def test_target_must_be_known_rep(self):
        with self.assertRaises(ValueError):
            self.crm.transfer(self.oid, "nope", "m1")
        with self.assertRaises(ValueError):
            self.crm.transfer(self.oid, "m1", "m1")
        with self.assertRaises(ValueError):
            self.crm.transfer(self.oid, [], "m1")
        self.assertEqual(self.crm.opps[self.oid]["owner"], "r1")

    def test_target_must_differ(self):
        with self.assertRaises(ValueError):
            self.crm.transfer(self.oid, "r1", "m1")
        self.assertEqual(self.crm.opps[self.oid]["owner"], "r1")

    def test_target_at_capacity(self):
        add(self.crm, "fill@corp.com", "F", "referral", "m1")
        self.assertEqual(self.crm.load("r2"), 1)
        with self.assertRaises(ValueError):
            self.crm.transfer(self.oid, "r2", "m1")
        self.assertEqual(self.crm.opps[self.oid]["owner"], "r1")

    def test_unknown_opportunity_with_valid_actor(self):
        log_before = list(self.crm.log)
        with self.assertRaisesRegex(ValueError, "unknown opportunity"):
            self.crm.transfer("O404", "r2", "m1")
        self.assertEqual(self.crm.log, log_before)

    def test_transfer_refills_previous_owner_and_log_order(self):
        # Fixture note: a lead only waits while every rep is at capacity, so the
        # transfer target is given room after the queue has formed. Everything
        # else goes through the public API.
        crm = CRM([rep("r1", 1), rep("r2", 1), manager("m1")])
        lid = add(crm, "tr1@corp.com", "T", "referral", "r1")
        crm.qualify(lid, "r1")
        oid = crm.convert(lid, 1000, "r1")
        add(crm, "tr0@corp.com", "T0", "referral", "r1")
        waiting = add(crm, "tr2@corp.com", "T2", "referral", "r1")
        self.assertIsNone(crm.leads[waiting]["owner"])
        crm.users["r2"]["capacity"] = 5
        log_before = list(crm.log)
        crm.transfer(oid, "r2", "m1")
        self.assertEqual(crm.opps[oid]["owner"], "r2")
        self.assertEqual(crm.leads[waiting]["owner"], "r1")
        self.assertEqual(
            crm.log,
            log_before + [("transfer", oid, "m1"), ("assign", waiting, "system")],
        )

    def test_transfer_success(self):
        self.crm.transfer(self.oid, "r2", "m1")
        self.assertEqual(self.crm.opps[self.oid]["owner"], "r2")
        self.assertEqual(self.crm.log[-1], ("transfer", self.oid, "m1"))

    def test_final_stage_cannot_transfer(self):
        for stage in ("proposal", "negotiation", "won"):
            self.crm.advance(self.oid, stage, "r1")
        with self.assertRaises(ValueError):
            self.crm.transfer(self.oid, "r2", "m1")
        self.assertEqual(self.crm.opps[self.oid]["owner"], "r1")


class ForecastTests(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(CRM([]).forecast(), {"open": 0, "weighted": 0, "won": 0})

    def test_weights_by_stage(self):
        crm = CRM([rep("r1", 10)])
        make_opp(crm, "w1@corp.com", 1000, stages=())
        make_opp(crm, "w2@corp.com", 1000, stages=("proposal",))
        make_opp(crm, "w3@corp.com", 1000, stages=("proposal", "negotiation"))
        self.assertEqual(crm.forecast()["weighted"], 1000)

    def test_open_count_excludes_final(self):
        crm = CRM([rep("r1", 10)])
        make_opp(crm, "o1@corp.com", 1000, stages=())
        make_opp(crm, "o2@corp.com", 1000, stages=("proposal",))
        make_opp(crm, "o3@corp.com", 1000, stages=("proposal", "negotiation"))
        make_opp(crm, "o4@corp.com", 1000, stages=("proposal", "negotiation", "won"))
        make_opp(crm, "o5@corp.com", 1000, stages=("lost",))
        forecast = crm.forecast()
        self.assertEqual(forecast["open"], 3)
        self.assertEqual(forecast["won"], 1000)

    def test_weights_and_won(self):
        crm = CRM([rep("r1", 10)])
        make_opp(crm, "f1@corp.com", 1000, stages=())
        make_opp(crm, "f2@corp.com", 1000, stages=("proposal",))
        make_opp(crm, "f3@corp.com", 1000, stages=("proposal", "negotiation"))
        make_opp(crm, "f4@corp.com", 1000, stages=("proposal", "negotiation", "won"))
        make_opp(crm, "f5@corp.com", 1000, stages=("lost",))
        self.assertEqual(crm.forecast(), {"open": 3, "weighted": 1000, "won": 1000})
        self.assertEqual(crm.log[-1], ("advance", "O5", "r1"))


class AtomicityTests(unittest.TestCase):
    def test_failed_duplicate_changes_nothing(self):
        crm = CRM([rep("r1", 5)])
        first = add(crm, "a@corp.com", "A", "web", "r1")
        leads_before = copy.deepcopy(crm.leads)
        log_before = list(crm.log)
        with self.assertRaises(DuplicateLeadError):
            add(crm, "a@corp.com", "A", "web", "r1")
        self.assertEqual(crm.leads, leads_before)
        self.assertEqual(crm.log, log_before)
        self.assertEqual(add(crm, "b@corp.com", "B", "web", "r1"), "L2")

    def test_failed_convert_changes_nothing(self):
        crm = CRM([rep("r1", 5)])
        lid = add(crm, "c@corp.com", "C", "referral", "r1")
        crm.qualify(lid, "r1")
        log_before = list(crm.log)
        with self.assertRaises(ValueError):
            crm.convert(lid, -3, "r1")
        self.assertEqual(crm.opps, {})
        self.assertEqual(crm.leads[lid]["status"], "qualified")
        self.assertEqual(crm.log, log_before)

    def test_failed_discount_changes_nothing(self):
        crm = CRM([rep("r1", 5), manager("m1")])
        oid = make_opp(crm, "d@corp.com", 1000)
        crm.discount(oid, 30, "m1")
        log_before = list(crm.log)
        with self.assertRaises(ValueError):
            crm.discount(oid, 1, "m1")
        self.assertEqual(crm.opps[oid]["amount"], 700)
        self.assertEqual(crm.log, log_before)

    def test_failed_transfer_changes_nothing(self):
        crm = CRM([rep("r1", 5), rep("r2", 1), manager("m1", 5)])
        oid = make_opp(crm, "t@corp.com", 1000)
        add(crm, "fill@corp.com", "F", "referral", "m1")
        log_before = list(crm.log)
        with self.assertRaises(ValueError):
            crm.transfer(oid, "r2", "m1")
        self.assertEqual(crm.opps[oid]["owner"], "r1")
        self.assertEqual(crm.log, log_before)

    def test_late_failure_rolls_back_everything(self):
        class ExplodingCRM(CRM):
            def _refill(self, rep_id):
                raise RuntimeError("boom")

        crm = ExplodingCRM([rep("r1", 1)])
        lid = add(crm, "x@corp.com", "X", "referral", "r1")
        crm.qualify(lid, "r1")
        oid = crm.convert(lid, 1000, "r1")
        crm.advance(oid, "proposal", "r1")
        crm.advance(oid, "negotiation", "r1")
        leads_before = copy.deepcopy(crm.leads)
        opps_before = copy.deepcopy(crm.opps)
        log_before = list(crm.log)
        with self.assertRaises(RuntimeError):
            crm.advance(oid, "won", "r1")
        self.assertEqual(crm.leads, leads_before)
        self.assertEqual(crm.opps, opps_before)
        self.assertEqual(crm.opps[oid]["stage"], "negotiation")
        self.assertEqual(crm.log, log_before)


if __name__ == "__main__":
    unittest.main()
