"""Invariant/property tests and check-order cases the example tests do not cover.

The property test drives long pseudo-random sessions (fixed seed, so runs are
deterministic) and asserts, after every single call, that:

* a failing call left the CRM byte-for-byte unchanged;
* load never exceeds capacity and managers never own work;
* the waiting queue is exactly the unowned leads, in creation order;
* converted leads and opportunities are in one-to-one correspondence;
* discounts never break the 70 % floor or rewrite ``original_amount``;
* ``forecast()`` agrees with a fresh computation from ``opps``.
"""

import copy
import random
import unittest

from crm import CRM, DuplicateLeadError


REPS = [
    {"id": "r1", "role": "rep", "capacity": 2},
    {"id": "r2", "role": "rep", "capacity": 2},
    {"id": "r3", "role": "rep", "capacity": 1},
    {"id": "mgr", "role": "manager", "capacity": 0},
]

ALL_STAGES = ("prospect", "proposal", "negotiation", "won", "lost")
OPEN_STAGES = ("prospect", "proposal", "negotiation")
LEAD_STATUSES = ("new", "qualified", "converted")
VALID_SCORES = {10, 20, 25, 30, 35, 45}
WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}


def load(crm, rep_id):
    """Load exactly as the specification defines it."""
    total = 0
    for lead in crm.leads.values():
        if lead["owner"] == rep_id and lead["status"] in ("new", "qualified"):
            total += 1
    for opp in crm.opps.values():
        if opp["owner"] == rep_id and opp["stage"] in OPEN_STAGES:
            total += 1
    return total


def snapshot(crm):
    return (
        copy.deepcopy(crm.leads),
        copy.deepcopy(crm.opps),
        copy.deepcopy(crm.log),
        list(crm.waiting),
    )


def expected_forecast(crm):
    open_count = 0
    weighted = 0
    won = 0
    for opp in crm.opps.values():
        if opp["stage"] == "won":
            won += opp["amount"]
        elif opp["stage"] in OPEN_STAGES:
            open_count += 1
            weighted += opp["amount"] * WEIGHTS[opp["stage"]] // 100
    return {"open": open_count, "weighted": weighted, "won": won}


class InvariantMixin:
    def assert_invariants(self, crm, context=""):
        reps = {rep["id"]: rep for rep in crm.reps}
        rep_ids = {rid for rid, rep in reps.items() if rep["role"] == "rep"}

        # ids are dense and match their keys
        self.assertEqual(
            list(crm.leads), ["L%d" % i for i in range(1, len(crm.leads) + 1)], context
        )
        self.assertEqual(
            list(crm.opps), ["O%d" % i for i in range(1, len(crm.opps) + 1)], context
        )

        # capacity and role invariants
        for rep in crm.reps:
            if rep["role"] == "rep":
                self.assertLessEqual(load(crm, rep["id"]), rep["capacity"], context)
            else:
                self.assertEqual(load(crm, rep["id"]), 0, context)

        # waiting queue mirrors ownerless leads, oldest first
        unowned = [lid for lid, lead in crm.leads.items() if lead["owner"] is None]
        self.assertEqual(crm.waiting, unowned, context)
        self.assertEqual(len(set(crm.waiting)), len(crm.waiting), context)

        converted = set()
        for lead_id, lead in crm.leads.items():
            self.assertEqual(
                set(lead),
                {"id", "email", "name", "source", "score", "owner", "status"},
                context,
            )
            self.assertEqual(lead["id"], lead_id, context)
            self.assertEqual(lead["email"], lead["email"].strip().lower(), context)
            self.assertEqual(lead["email"].count("@"), 1, context)
            self.assertEqual(lead["name"], lead["name"].strip(), context)
            self.assertTrue(lead["name"], context)
            self.assertIn(lead["source"], ("web", "referral", "event"), context)
            self.assertIn(lead["score"], VALID_SCORES, context)
            self.assertIn(lead["status"], LEAD_STATUSES, context)
            self.assertTrue(lead["owner"] is None or lead["owner"] in rep_ids, context)
            if lead["owner"] is None:
                self.assertIn(lead["status"], ("new", "qualified"), context)
            if lead["status"] == "converted":
                self.assertIsNotNone(lead["owner"], context)
                converted.add(lead_id)

        owners_of_opps = set()
        for opp_id, opp in crm.opps.items():
            self.assertEqual(
                set(opp),
                {"id", "lead_id", "owner", "amount", "original_amount", "stage"},
                context,
            )
            self.assertEqual(opp["id"], opp_id, context)
            self.assertIn(opp["stage"], ALL_STAGES, context)
            self.assertIn(opp["owner"], rep_ids, context)
            self.assertGreater(opp["amount"], 0, context)
            self.assertLessEqual(opp["amount"], opp["original_amount"], context)
            self.assertGreaterEqual(
                opp["amount"] * 100, opp["original_amount"] * 70, context
            )
            self.assertIn(opp["lead_id"], crm.leads, context)
            self.assertEqual(
                crm.leads[opp["lead_id"]]["status"], "converted", context
            )
            owners_of_opps.add(opp["lead_id"])

        # one opportunity per converted lead, and only for converted leads
        self.assertEqual(len(owners_of_opps), len(crm.opps), context)
        self.assertEqual(owners_of_opps, converted, context)

        # every logged id refers to something that exists
        for entry in crm.log:
            self.assertIsInstance(entry, tuple, context)
            self.assertEqual(len(entry), 3, context)
            op, entity_id, actor = entry
            self.assertIn(
                op,
                ("add_lead", "qualify", "convert", "advance", "discount",
                 "transfer", "assign"),
                context,
            )
            target = crm.leads if op in ("add_lead", "qualify", "assign") else crm.opps
            self.assertIn(entity_id, target, context)
            if op == "assign":
                self.assertEqual(actor, "system", context)
            else:
                self.assertIn(actor, reps, context)

        self.assertEqual(crm.forecast(), expected_forecast(crm), context)


class TestRandomizedInvariants(InvariantMixin, unittest.TestCase):
    """Two deterministic sessions: one under queue pressure, one with room."""

    OPS = ("add", "qualify", "convert", "advance", "discount", "transfer")

    def _run(self, reps, seed, steps, add_weight):
        rng = random.Random(seed)
        crm = CRM(reps)
        rep_ids = [rep["id"] for rep in reps if rep["role"] == "rep"]
        successes = dict.fromkeys(self.OPS, 0)
        max_waiting = 0

        def qualified_leads():
            return [lid for lid, l in crm.leads.items() if l["status"] == "qualified"]

        def qualifiable_leads():
            return [
                lid for lid, l in crm.leads.items()
                if l["status"] == "new" and l["score"] >= 30
            ]

        def open_opps():
            return [oid for oid, o in crm.opps.items() if o["stage"] in OPEN_STAGES]

        def spare_reps(exclude=None):
            return [
                rid for rid in rep_ids
                if rid != exclude and load(crm, rid) < crm.users[rid]["capacity"]
            ]

        for step in range(steps):
            op = rng.choice(
                ["add"] * add_weight
                + ["qualify", "convert", "convert", "advance", "advance",
                   "advance", "discount", "discount", "transfer", "transfer"]
            )
            context = "seed %d step %d (%s)" % (seed, step, op)
            actor = "mgr"

            if op == "add":
                email = "user%d@%s" % (step, rng.choice(["acme.com", "gmail.com"]))
                args = (email, " Name ", rng.choice(["web", "referral", "event"]), actor)
            elif op == "qualify":
                pool = qualifiable_leads() or list(crm.leads) or ["L1"]
                args = (rng.choice(pool), actor)
            elif op == "convert":
                owned = [lid for lid in qualified_leads() if crm.leads[lid]["owner"]]
                pool = owned or qualified_leads()
                if pool:
                    lead_id = rng.choice(pool)
                    actor = crm.leads[lead_id]["owner"] or "mgr"
                    args = (lead_id, rng.choice([1, 999, 50000, 60000]), actor)
                else:
                    args = (rng.choice(list(crm.leads) or ["L1"]), 100, actor)
            elif op == "advance":
                pool = open_opps()
                if pool:
                    opp_id = rng.choice(pool)
                    current = crm.opps[opp_id]["stage"]
                    stage = (
                        "lost" if rng.random() < 0.2
                        else ["proposal", "negotiation", "won"][
                            list(OPEN_STAGES).index(current)
                        ]
                    )
                    args = (opp_id, stage, actor)
                else:
                    args = ("O1", "proposal", actor)
            elif op == "discount":
                pool = open_opps()
                args = (rng.choice(pool) if pool else "O1",
                        rng.choice([1, 5, 10, 15, 30]), actor)
            else:
                pool = open_opps()
                if pool:
                    opp_id = rng.choice(pool)
                    owners = spare_reps(crm.opps[opp_id]["owner"])
                    args = (opp_id, rng.choice(owners) if owners else "r1", actor)
                else:
                    args = ("O1", "r1", actor)

            # one call in six carries a deliberately broken argument
            if rng.random() < 1 / 6:
                slot = rng.randrange(len(args))
                junk = rng.choice(
                    ["bogus", None, 0, -1, True, 2.5, [], "L99", "O99", "ghost"]
                )
                args = args[:slot] + (junk,) + args[slot + 1:]

            before = snapshot(crm)
            call = getattr(crm, {"add": "add_lead"}.get(op, op))
            try:
                call(*args)
            except (ValueError, PermissionError, DuplicateLeadError):
                self.assertEqual(snapshot(crm), before, context)
            else:
                successes[op] += 1

            max_waiting = max(max_waiting, len(crm.waiting))
            self.assert_invariants(crm, context)

        return crm, successes, max_waiting

    def test_queue_pressure_session(self):
        tight = [
            {"id": "r1", "role": "rep", "capacity": 4},
            {"id": "r2", "role": "rep", "capacity": 3},
            {"id": "r3", "role": "rep", "capacity": 3},
            {"id": "mgr", "role": "manager", "capacity": 0},
        ]
        crm, successes, max_waiting = self._run(tight, 20260501, 400, add_weight=2)
        self.assertGreater(max_waiting, 0, successes)
        self.assertGreater(len(crm.leads), 10, successes)
        self.assertGreater(len(crm.opps), 5, successes)
        for op in ("add", "qualify", "convert", "advance", "discount"):
            self.assertGreater(successes[op], 0, successes)
        self.assert_invariants(crm, "final queue-pressure state")

    def test_lifecycle_session(self):
        roomy = [
            {"id": "r1", "role": "rep", "capacity": 40},
            {"id": "r2", "role": "rep", "capacity": 40},
            {"id": "r3", "role": "rep", "capacity": 40},
            {"id": "mgr", "role": "manager", "capacity": 0},
        ]
        crm, successes, _ = self._run(roomy, 987654, 500, add_weight=3)
        for op, count in successes.items():
            self.assertGreater(count, 0, "%s never succeeded: %r" % (op, successes))
        self.assertGreater(len(crm.opps), 10, successes)
        self.assertTrue(any(o["stage"] == "won" for o in crm.opps.values()))
        self.assert_invariants(crm, "final lifecycle state")


class TestCheckOrder(InvariantMixin, unittest.TestCase):
    def setUp(self):
        self.crm = CRM(REPS)
        self.lead = self.crm.add_lead("a@acme.com", "A", "referral", "mgr")
        self.crm.qualify(self.lead, "mgr")

    def test_illegal_transition_beats_manager_requirement(self):
        # check 5 (illegal jump) is evaluated before check 6 (large negotiation)
        opp = self.crm.convert(self.lead, 60000, "mgr")
        owner = self.crm.opps[opp]["owner"]
        with self.assertRaises(ValueError):
            self.crm.advance(opp, "negotiation", owner)
        self.assertEqual(self.crm.opps[opp]["stage"], "prospect")

    def test_manager_requirement_only_guards_entering_negotiation(self):
        opp = self.crm.convert(self.lead, 60000, "mgr")
        owner = self.crm.opps[opp]["owner"]
        self.crm.advance(opp, "proposal", owner)
        self.crm.advance(opp, "negotiation", "mgr")
        # closing a large deal is a plain rep action
        self.crm.advance(opp, "won", owner)
        self.assertEqual(self.crm.opps[opp]["stage"], "won")

    def test_unknown_actor_beats_duplicate_email(self):
        with self.assertRaises(PermissionError):
            self.crm.add_lead("A@ACME.COM", "A", "web", "ghost")

    def test_non_string_ids_are_value_errors(self):
        opp = self.crm.convert(self.lead, 10, "mgr")
        for bad in (True, False, 0, 1.0, [], {}, object()):
            with self.assertRaises(ValueError, msg=repr(bad)):
                self.crm.qualify(bad, "mgr")
            with self.assertRaises(ValueError, msg=repr(bad)):
                self.crm.convert(bad, 10, "mgr")
            with self.assertRaises(ValueError, msg=repr(bad)):
                self.crm.advance(bad, "proposal", "mgr")
            with self.assertRaises(ValueError, msg=repr(bad)):
                self.crm.discount(bad, 5, "mgr")
            with self.assertRaises(ValueError, msg=repr(bad)):
                self.crm.transfer(bad, "r2", "mgr")


class TestQueueBehaviour(InvariantMixin, unittest.TestCase):
    def reps(self, *capacities):
        reps = [
            {"id": "r%d" % (i + 1), "role": "rep", "capacity": cap}
            for i, cap in enumerate(capacities)
        ]
        reps.append({"id": "mgr", "role": "manager", "capacity": 0})
        return reps

    def test_transfer_then_assign_log_order_and_fifo(self):
        crm = CRM(self.reps(1, 0))
        first = crm.add_lead("a@acme.com", "A", "referral", "mgr")
        crm.qualify(first, "mgr")
        opp = crm.convert(first, 1000, "mgr")
        oldest = crm.add_lead("b@acme.com", "B", "referral", "mgr")
        newer = crm.add_lead("c@acme.com", "C", "referral", "mgr")
        self.assertEqual(crm.waiting, [oldest, newer])

        crm.users["r2"]["capacity"] = 2  # setup mutation: r2 gains room
        crm.transfer(opp, "r2", "mgr")

        self.assertEqual(crm.leads[oldest]["owner"], "r1")
        self.assertIsNone(crm.leads[newer]["owner"])
        self.assertEqual(crm.waiting, [newer])
        self.assertEqual(
            crm.log[-2:], [("transfer", opp, "mgr"), ("assign", oldest, "system")]
        )
        self.assert_invariants(crm)

    def test_manager_qualifies_queued_lead_without_removing_it(self):
        crm = CRM(self.reps(1))
        first = crm.add_lead("a@acme.com", "A", "referral", "mgr")
        queued = crm.add_lead("b@acme.com", "B", "referral", "mgr")
        self.assertIsNone(crm.leads[queued]["owner"])
        crm.qualify(queued, "mgr")
        self.assertEqual(crm.waiting, [queued])
        self.assertEqual(crm.leads[queued]["status"], "qualified")

        crm.qualify(first, "mgr")
        opp = crm.convert(first, 100, "mgr")
        crm.advance(opp, "lost", "mgr")

        self.assertEqual(crm.leads[queued]["owner"], "r1")
        self.assertEqual(crm.leads[queued]["status"], "qualified")
        self.assertEqual(crm.waiting, [])
        self.assert_invariants(crm)

    def test_assignment_loop_respects_capacity_and_fifo(self):
        crm = CRM(self.reps(2))
        a = crm.add_lead("a@acme.com", "A", "referral", "mgr")
        b = crm.add_lead("b@acme.com", "B", "referral", "mgr")
        crm.qualify(a, "mgr")
        opp = crm.convert(a, 100, "mgr")
        waiting = [
            crm.add_lead("%s@acme.com" % name, name, "referral", "mgr")
            for name in ("c", "d", "e")
        ]
        self.assertEqual(crm.waiting, waiting)

        crm.users["r1"]["capacity"] = 3  # room for two more after the close
        crm.advance(opp, "proposal", "mgr")
        crm.advance(opp, "negotiation", "mgr")
        crm.advance(opp, "won", "mgr")

        # b was already owned; the freed slot drains two queue entries, then stops
        self.assertEqual(crm.leads[b]["owner"], "r1")
        self.assertEqual(crm.leads[waiting[0]]["owner"], "r1")
        self.assertEqual(crm.leads[waiting[1]]["owner"], "r1")
        self.assertIsNone(crm.leads[waiting[2]]["owner"])
        self.assertEqual(crm.waiting, [waiting[2]])
        self.assertEqual(
            crm.log[-3:],
            [
                ("advance", opp, "mgr"),
                ("assign", waiting[0], "system"),
                ("assign", waiting[1], "system"),
            ],
        )
        self.assert_invariants(crm)


class TestMiscellaneousEdges(InvariantMixin, unittest.TestCase):
    def test_domain_scoring_is_literal(self):
        crm = CRM(REPS)
        cases = [
            ("a@GMAIL.com", "web", 10),
            ("b@gmail.com.", "web", 25),
            ("c@mail.gmail.com", "web", 25),
            ("d@acme.com", "event", 35),
        ]
        for email, source, score in cases:
            lead_id = crm.add_lead(email, "N", source, "mgr")
            self.assertEqual(crm.leads[lead_id]["score"], score, email)

    def test_non_string_emails_rejected(self):
        crm = CRM(REPS)
        for email in ([], {}, 1.5, True, object()):
            with self.assertRaises(ValueError, msg=repr(email)):
                crm.add_lead(email, "N", "web", "mgr")
        self.assertEqual(snapshot(crm), ({}, {}, [], []))

    def test_forecast_truncates_each_opportunity_separately(self):
        crm = CRM([
            {"id": "r", "role": "rep", "capacity": 5},
            {"id": "mgr", "role": "manager", "capacity": 0},
        ])
        leads = [crm.add_lead("%s@acme.com" % c, c, "referral", "mgr") for c in "pqr"]
        for lead in leads:
            crm.qualify(lead, "mgr")
        prospect = crm.convert(leads[0], 999, "mgr")
        proposal = crm.convert(leads[1], 999, "mgr")
        negotiation = crm.convert(leads[2], 999, "mgr")
        crm.advance(proposal, "proposal", "mgr")
        crm.advance(negotiation, "proposal", "mgr")
        crm.advance(negotiation, "negotiation", "mgr")

        self.assertEqual(crm.opps[prospect]["stage"], "prospect")
        self.assertEqual(
            crm.forecast(), {"open": 3, "weighted": 99 + 299 + 599, "won": 0}
        )
        self.assert_invariants(crm)

    def test_discount_never_rewrites_original_amount(self):
        crm = CRM(REPS)
        lead = crm.add_lead("a@acme.com", "A", "referral", "mgr")
        crm.qualify(lead, "mgr")
        opp = crm.convert(lead, 1001, "mgr")
        crm.discount(opp, 10, "mgr")
        crm.discount(opp, 10, "mgr")
        self.assertEqual(crm.opps[opp]["amount"], 1001 * 90 // 100 * 90 // 100)
        self.assertEqual(crm.opps[opp]["original_amount"], 1001)
        self.assert_invariants(crm)

    def test_duplicate_detection_is_email_only(self):
        crm = CRM(REPS)
        first = crm.add_lead("a@acme.com", "Alice", "web", "mgr")
        second = crm.add_lead("b@acme.com", "Alice", "web", "mgr")
        self.assertNotEqual(first, second)
        with self.assertRaises(DuplicateLeadError) as ctx:
            crm.add_lead("a@acme.com", "Someone Else", "event", "mgr")
        self.assertEqual(ctx.exception.existing_id, first)


if __name__ == "__main__":
    unittest.main()
