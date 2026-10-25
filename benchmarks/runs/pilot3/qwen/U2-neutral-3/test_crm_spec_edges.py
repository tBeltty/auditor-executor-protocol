"""Spec-boundary tests for crm.py: check order, inertness, odd inputs.

These cases pin the corners of specs/crm.md that the flow tests do not
cover: which check decides first when several could fail, that a rejected
call consumes neither an ID nor a log slot, and that malformed ids/types
raise the exception class the spec names rather than a TypeError.
"""

import unittest

from crm import CRM, DuplicateLeadError

REPS = [
    {"id": "r1", "role": "rep", "capacity": 1},
    {"id": "r2", "role": "rep", "capacity": 2},
    {"id": "m1", "role": "manager", "capacity": 99},
]


def make_crm():
    return CRM([dict(u) for u in REPS])


def qualified_opp(crm, email="a@site.com", amount=1000, actor="m1"):
    lid = crm.add_lead(email, "N", "referral", actor)
    crm.qualify(lid, actor)
    return lid, crm.convert(lid, amount, actor)


class TestAddLeadCheckOrder(unittest.TestCase):
    def test_source_check_precedes_duplicate_check(self):
        # Check 3 (source) is listed before check 4 (duplicate), so an
        # existing email with a bad source is a plain ValueError.
        crm = make_crm()
        crm.add_lead("a@site.com", "A", "web", "m1")
        with self.assertRaises(ValueError):
            crm.add_lead("a@site.com", "A", "phone", "m1")

    def test_name_check_precedes_duplicate_check(self):
        crm = make_crm()
        crm.add_lead("a@site.com", "A", "web", "m1")
        with self.assertRaises(ValueError):
            crm.add_lead("a@site.com", "  ", "web", "m1")

    def test_email_check_precedes_name_and_source(self):
        crm = make_crm()
        with self.assertRaises(ValueError):
            crm.add_lead("nope", "", "phone", "m1")

    def test_duplicate_existing_id_may_be_a_queued_lead(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 0},
                   {"id": "m1", "role": "manager", "capacity": 1}])
        queued = crm.add_lead("q@site.com", "Q", "web", "m1")
        self.assertIsNone(crm.leads[queued]["owner"])
        with self.assertRaises(DuplicateLeadError) as ctx:
            crm.add_lead("Q@site.com", "Q2", "web", "m1")
        self.assertEqual(ctx.exception.existing_id, queued)
        self.assertEqual(len(crm.leads), 1)

    def test_email_with_whitespace_inside_is_accepted(self):
        # The spec lists exactly three email conditions (one "@", non-empty
        # local part, an interior "." in the domain); it adds no whitespace
        # rule, so validation must not invent one.
        crm = make_crm()
        lid = crm.add_lead("first last@site.com", "N", "web", "m1")
        self.assertEqual(crm.leads[lid]["email"], "first last@site.com")

    def test_non_string_entity_ids_never_reach_the_caller_as_typeerror(self):
        crm = make_crm()
        for bad_id in (None, 5, ["L1"], {"id": "L1"}):
            with self.assertRaises(ValueError, msg=repr(bad_id)):
                crm.qualify(bad_id, "m1")
            with self.assertRaises(ValueError, msg=repr(bad_id)):
                crm.convert(bad_id, 10, "m1")
            with self.assertRaises(ValueError, msg=repr(bad_id)):
                crm.advance(bad_id, "proposal", "m1")
            with self.assertRaises(ValueError, msg=repr(bad_id)):
                crm.discount(bad_id, 5, "m1")
            with self.assertRaises(ValueError, msg=repr(bad_id)):
                crm.transfer(bad_id, "r1", "m1")


class TestUserTableIsSnapshot(unittest.TestCase):
    def test_mutating_the_reps_argument_does_not_change_routing(self):
        reps = [{"id": "r1", "role": "rep", "capacity": 1},
                {"id": "r2", "role": "rep", "capacity": 1}]
        crm = CRM(reps)
        reps[0]["capacity"] = 99
        reps[1]["role"] = "manager"
        reps.append({"id": "r3", "role": "rep", "capacity": 5})
        l1 = crm.add_lead("1@x.com", "1", "web", "r1")
        l2 = crm.add_lead("2@x.com", "2", "web", "r1")
        l3 = crm.add_lead("3@x.com", "3", "web", "r1")
        self.assertEqual(crm.leads[l1]["owner"], "r1")
        self.assertEqual(crm.leads[l2]["owner"], "r2")
        self.assertIsNone(crm.leads[l3]["owner"])   # r3 unknown, r1/r2 full

    def test_unknown_new_owner_types(self):
        crm = make_crm()
        _, oid = qualified_opp(crm)
        for bad in (["r2"], {"id": "r2"}, 3, None, "m1", "ghost"):
            with self.assertRaises(ValueError, msg=repr(bad)):
                crm.transfer(oid, bad, "m1")

    def test_rep_with_zero_capacity_can_never_receive_a_transfer(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1},
                   {"id": "r0", "role": "rep", "capacity": 0},
                   {"id": "m1", "role": "manager", "capacity": 0}])
        _, oid = qualified_opp(crm, actor="m1")
        with self.assertRaises(ValueError):
            crm.transfer(oid, "r0", "m1")


class TestQualifyAndConvertOrder(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        self.lid = self.crm.add_lead("a@site.com", "A", "referral", "m1")
        self.crm.qualify(self.lid, "m1")

    def test_convert_consumes_the_lead_exactly_once(self):
        opp = self.crm.convert(self.lid, 500, "m1")
        self.assertEqual(self.crm.leads[self.lid]["status"], "converted")
        before = list(self.crm.log)
        with self.assertRaises(ValueError):          # 4: not qualified anymore
            self.crm.convert(self.lid, 500, "m1")
        self.assertEqual(len(self.crm.opps), 1)
        self.assertEqual(self.crm.log, before)
        # The rejected call did not consume O2.
        other = self.crm.add_lead("b@site.com", "B", "referral", "m1")
        self.crm.qualify(other, "m1")
        self.assertEqual(self.crm.convert(other, 500, "m1"), "O2")
        self.assertNotEqual(self.crm.opps[opp]["lead_id"], other)

    def test_owner_check_precedes_qualified_check(self):
        fresh = self.crm.add_lead("c@site.com", "C", "referral", "m1")  # r2, new
        with self.assertRaises(PermissionError):
            self.crm.convert(fresh, 100, "r1")        # not the owner

    def test_qualify_a_converted_lead_is_value_error(self):
        self.crm.convert(self.lid, 100, "m1")
        with self.assertRaises(ValueError):
            self.crm.qualify(self.lid, "m1")

    def test_unhashable_stage_and_pct(self):
        opp = self.crm.convert(self.lid, 100, "m1")
        with self.assertRaises(ValueError):
            self.crm.advance(opp, ["won"], "m1")
        with self.assertRaises(ValueError):
            self.crm.discount(opp, [5], "m1")


class TestAdvanceAndDiscountOrder(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        self.lid, self.opp = qualified_opp(self.crm, amount=1000)

    def test_final_stage_check_precedes_rep_discount_cap(self):
        self.crm.advance(self.opp, "lost", "m1")
        # r1 is the owner, so check 3 passes; check 4 (final) is ValueError
        # and precedes check 5 (which would be PermissionError for pct 20).
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp, 20, "r1")

    def test_rep_cap_check_precedes_cumulative_floor(self):
        self.crm.discount(self.opp, 25, "m1")         # amount 750, at the floor
        # pct 11 by a rep: check 5 PermissionError before check 6 ValueError.
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp, 11, "r1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 750)

    def test_rep_can_hit_the_cumulative_floor_value_error(self):
        self.crm.discount(self.opp, 25, "m1")         # 750
        with self.assertRaises(ValueError):           # 750*0.9 = 675 < 700
            self.crm.discount(self.opp, 10, "r1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 750)

    def test_negotiation_gate_uses_current_amount(self):
        # "when amount is greater than 50000": the live amount, so a manager
        # discount below the threshold lets the rep advance alone afterwards.
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 5},
                   {"id": "m1", "role": "manager", "capacity": 5}])
        _, oid = qualified_opp(crm, amount=60000, actor="m1")
        crm.advance(oid, "proposal", "r1")
        with self.assertRaises(PermissionError):
            crm.advance(oid, "negotiation", "r1")
        crm.discount(oid, 30, "m1")                   # 42000 <= 50000
        crm.advance(oid, "negotiation", "r1")
        self.assertEqual(crm.opps[oid]["stage"], "negotiation")

    def test_advance_to_final_frees_a_slot_for_a_waiting_lead_only_for_reps(self):
        # A manager holds no work, so winning by/for a manager must not
        # hand waiting leads to the manager.
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1},
                   {"id": "m1", "role": "manager", "capacity": 99}])
        l1 = crm.add_lead("1@x.com", "1", "referral", "m1")   # r1
        l2 = crm.add_lead("2@x.com", "2", "referral", "m1")   # queued
        crm.qualify(l1, "m1")
        o1 = crm.convert(l1, 100, "m1")
        crm.advance(o1, "proposal", "m1")
        crm.advance(o1, "negotiation", "m1")
        crm.advance(o1, "won", "m1")
        self.assertEqual(crm.leads[l2]["owner"], "r1")
        self.assertEqual(crm.log[-1], ("assign", l2, "system"))


class TestBackfillKeepsLeadState(unittest.TestCase):
    def test_backfill_preserves_qualified_status_and_allows_convert(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1},
                   {"id": "m1", "role": "manager", "capacity": 1}])
        l1 = crm.add_lead("1@x.com", "1", "referral", "m1")   # r1
        l2 = crm.add_lead("2@x.com", "2", "referral", "m1")   # queued
        crm.qualify(l1, "m1")
        crm.qualify(l2, "m1")                     # manager can queue-qualify
        o1 = crm.convert(l1, 100, "m1")
        self.assertEqual(crm.leads[l2]["status"], "qualified")
        self.assertIsNone(crm.leads[l2]["owner"])
        with self.assertRaises(ValueError):       # 5: no owner yet
            crm.convert(l2, 100, "m1")
        crm.advance(o1, "lost", "m1")
        self.assertEqual(crm.leads[l2]["owner"], "r1")
        self.assertEqual(crm.leads[l2]["status"], "qualified")
        o2 = crm.convert(l2, 100, "r1")
        self.assertEqual(crm.opps[o2]["owner"], "r1")


class TestLogShape(unittest.TestCase):
    OPS = {"add_lead", "qualify", "convert", "advance", "discount",
           "transfer", "assign"}

    def win_path_session(self):
        """Advance-to-final that backfills: exercises the "assign" entry."""
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1},
                   {"id": "r2", "role": "rep", "capacity": 1},
                   {"id": "m1", "role": "manager", "capacity": 1}])
        l1 = crm.add_lead("1@x.com", "1", "referral", "m1")   # r1
        l2 = crm.add_lead("2@x.com", "2", "referral", "m1")   # r2
        l3 = crm.add_lead("3@x.com", "3", "referral", "m1")   # queued
        crm.qualify(l1, "r1")
        o1 = crm.convert(l1, 70000, "r1")
        crm.advance(o1, "proposal", "r1")
        crm.discount(o1, 30, "m1")                # 70000 -> 49000
        crm.advance(o1, "negotiation", "r1")      # rep ok once under 50000
        crm.advance(o1, "won", "m1")              # frees r1 -> takes l3
        return crm, (l1, l2, l3), o1

    def transfer_session(self):
        """Manager transfer of an open opportunity (queue empty by design)."""
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1},
                   {"id": "r2", "role": "rep", "capacity": 4},
                   {"id": "m1", "role": "manager", "capacity": 1}])
        lids = [crm.add_lead(f"{i}@x.com", str(i), "referral", "m1")
                for i in range(1, 4)]            # L1 r1, L2/L3 r2
        crm.qualify(lids[0], "r1")
        o1 = crm.convert(lids[0], 100, "r1")     # r1 full again (opp counts)
        crm.transfer(o1, "r2", "m1")             # r2 load 2 -> 3, r1 -> 0
        crm.advance(o1, "proposal", "m1")
        return crm, tuple(lids), o1

    def test_entries_are_op_entity_actor_tuples(self):
        for crm, _, _ in (self.win_path_session(), self.transfer_session()):
            for entry in crm.log:
                self.assertIsInstance(entry, tuple)
                self.assertEqual(len(entry), 3)
                op, entity_id, actor = entry
                self.assertIn(op, self.OPS)
                self.assertIsInstance(entity_id, str)
                self.assertIsInstance(actor, str)
                self.assertIn(actor, {"r1", "r2", "m1", "system"})
                if op == "assign":
                    self.assertEqual(actor, "system")

    def test_win_path_log_is_exactly_the_named_entries(self):
        crm, (l1, l2, l3), o1 = self.win_path_session()
        self.assertEqual(crm.log, [
            ("add_lead", l1, "m1"),
            ("add_lead", l2, "m1"),
            ("add_lead", l3, "m1"),
            ("qualify", l1, "r1"),
            ("convert", o1, "r1"),
            ("advance", o1, "r1"),
            ("discount", o1, "m1"),
            ("advance", o1, "r1"),
            ("advance", o1, "m1"),
            ("assign", l3, "system"),     # the freed r1 slot took the oldest lead
        ])
        self.assertEqual(crm.leads[l3]["owner"], "r1")
        self.assertEqual(crm.leads[l2]["owner"], "r2")   # untouched

    def test_transfer_log_has_no_system_assign_when_queue_is_empty(self):
        crm, lids, o1 = self.transfer_session()
        self.assertEqual(crm.log[-2:], [
            ("transfer", o1, "m1"),
            ("advance", o1, "m1"),
        ])
        self.assertNotIn("assign", [e[0] for e in crm.log])
        self.assertEqual(crm.opps[o1]["owner"], "r2")
        self.assertEqual(crm._load("r1"), 0)     # prev owner has room now
        self.assertEqual(crm._load("r2"), 3)     # two leads + the moved opp

    def test_every_entity_id_in_log_exists(self):
        for crm, _, _ in (self.win_path_session(), self.transfer_session()):
            ids = set(crm.leads) | set(crm.opps)
            for _, entity_id, _ in crm.log:
                self.assertIn(entity_id, ids)


if __name__ == "__main__":
    unittest.main()
