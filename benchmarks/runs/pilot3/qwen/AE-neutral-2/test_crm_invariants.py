"""Cross-cutting spec rules: actor-first checks, call atomicity, log contents."""

import copy
import unittest

from crm import CRM, DuplicateLeadError
from support import add, converted, make_crm, qualified, snapshot


class TestActorCheckIsFirst(unittest.TestCase):
    """Every actor-taking method raises PermissionError for an unknown actor
    before any other validation, no matter how broken the remaining args are."""

    def setUp(self):
        self.crm = make_crm()
        # one real lead/opp so id-bearing calls exercise real entities too
        opp = converted(self.crm, "a@b.com", 1000)
        self.opp = opp
        self.lead = "L1"

    def cases(self, crm):
        return [
            ("add_lead", lambda: crm.add_lead(12345, None, "wrong-src", "ghost")),
            ("qualify", lambda: crm.qualify("L404", "ghost")),
            ("convert", lambda: crm.convert(self.lead, -1, "ghost")),
            ("advance", lambda: crm.advance(self.opp, "not-a-stage", "ghost")),
            ("discount", lambda: crm.discount(self.opp, 999, "ghost")),
            ("transfer", lambda: crm.transfer("O404", "nobody", "ghost")),
        ]

    def test_unknown_actor_is_permission_error_everywhere(self):
        for name, call in self.cases(self.crm):
            with self.subTest(method=name):
                with self.assertRaises(PermissionError):
                    call()

    def test_failed_actor_check_appends_no_log(self):
        before = snapshot(self.crm)
        for _, call in self.cases(self.crm):
            try:
                call()
            except PermissionError:
                pass
        self.assertEqual(snapshot(self.crm), before)

    def test_forecast_takes_no_actor(self):
        self.assertEqual(
            self.crm.forecast(), {"open": 1, "weighted": 100, "won": 0}
        )


class TestAtomicity(unittest.TestCase):
    """A failed call changes nothing (attributes or log) for every method."""

    def failing_calls_sweep(self):
        cases = []
        for reps in (None, [{"id": "z", "role": "rep", "capacity": 1},
                            {"id": "m1", "role": "manager", "capacity": 0}]):
            crm = make_crm(reps)
            l1 = qualified(crm, "keep@b.com")
            opp = crm.convert(l1, 777, "m1")
            lq = add(crm, "queued@b.com")  # "new" lead; convert must fail
            cases.append((crm, [
                (lambda: crm.add_lead("a@b.com", "N", "sms", "m1")),
                (lambda: crm.add_lead("keep@b.com", "N", "web", "m1")),  # dup
                (lambda: crm.qualify("L404", "m1")),
                (lambda: crm.qualify(l1, "m1")),  # already qualified
                (lambda: crm.convert(l1, 0, "m1")),
                (lambda: crm.convert(lq, 5, "m1")),  # lead is still "new"
                (lambda: crm.advance(opp, "negotiation", "m1")),  # illegal jump
                (lambda: crm.advance(opp, "proposal", "nope")),  # unknown actor
                (lambda: crm.discount(opp, 40, "m1")),  # pct out of range
                (lambda: crm.transfer(opp, "m1", "m1")),  # target is a manager
                (lambda: crm.transfer(opp, "m1", "z")),  # rep actor, not manager
            ]))
        return cases


    def test_no_exception_no_side_effects(self):
        for crm, calls in self.failing_calls_sweep():
            before = snapshot(crm)
            for call in calls:
                with self.assertRaises((ValueError, PermissionError, DuplicateLeadError)):
                    call()
            self.assertEqual(snapshot(crm), before)

    def test_duplicate_lead_error_carries_existing_id(self):
        crm = make_crm()
        first = add(crm, "dup@b.com")
        add(crm, "other@b.com")
        with self.assertRaises(DuplicateLeadError) as ctx:
            add(crm, " DUP@B.COM ")
        self.assertEqual(ctx.exception.existing_id, first)

    def test_exception_hierarchy(self):
        self.assertTrue(issubclass(DuplicateLeadError, Exception))
        self.assertFalse(issubclass(DuplicateLeadError, ValueError))
        self.assertTrue(issubclass(PermissionError, Exception))


class TestLogContract(unittest.TestCase):
    def test_log_is_list_of_three_tuples(self):
        crm = make_crm()
        l1 = qualified(crm, "a@b.com")
        crm.convert(l1, 100, "m1")
        crm.advance("O1", "proposal", "m1")
        crm.discount("O1", 5, "m1")
        crm.transfer("O1", "r2", "m1")
        for entry in crm.log:
            self.assertIsInstance(entry, tuple)
            self.assertEqual(len(entry), 3)
            self.assertTrue(all(isinstance(x, str) for x in entry))

    def test_successful_call_appends_exactly_the_named_entries(self):
        crm = make_crm([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        l1 = qualified(crm, "1@b.com")  # r1 (tie -> "r1")
        l2 = add(crm, "2@b.com")  # r2
        l3 = add(crm, "3@b.com")  # queue (both full)
        opp = crm.convert(l1, 40000, "m1")  # r1 still at cap via the opp
        crm.advance(opp, "proposal", "r1")
        crm.discount(opp, 10, "r1")  # 40000 -> 36000
        crm.advance(opp, "negotiation", "r1")  # 36000 <= 50000, no manager needed
        crm.advance(opp, "won", "r1")  # frees the slot -> L3 assigned to r1
        self.assertEqual(
            crm.log,
            [
                ("add_lead", "L1", "m1"),
                ("qualify", "L1", "m1"),
                ("add_lead", "L2", "m1"),
                ("add_lead", "L3", "m1"),
                ("convert", "O1", "m1"),
                ("advance", "O1", "r1"),
                ("discount", "O1", "r1"),
                ("advance", "O1", "r1"),
                ("advance", "O1", "r1"),
                ("assign", "L3", "system"),
            ],
        )
        self.assertEqual(crm.leads[l3]["owner"], "r1")
        self.assertEqual(crm.forecast(), {"open": 0, "weighted": 0, "won": 36000})

    def test_no_log_entry_for_forecast(self):
        crm = make_crm()
        converted(crm, "a@b.com", 500)
        n = len(crm.log)
        crm.forecast()
        self.assertEqual(len(crm.log), n)


class TestPublicSurface(unittest.TestCase):
    def test_attributes_exist_with_spec_types(self):
        crm = CRM([{"id": "r", "role": "rep", "capacity": 1}])
        self.assertIsInstance(crm.leads, dict)
        self.assertIsInstance(crm.opps, dict)
        self.assertIsInstance(crm.log, list)
        self.assertEqual(crm.leads, {})
        self.assertEqual(crm.opps, {})
        self.assertEqual(crm.log, [])

    def test_duplicate_lead_error_is_raisable_and_constructible(self):
        err = DuplicateLeadError("L9")
        self.assertEqual(err.existing_id, "L9")

    def test_reps_input_dicts_are_not_mutated(self):
        reps = [{"id": "r1", "role": "rep", "capacity": 5}]
        pristine = copy.deepcopy(reps)
        crm = CRM(reps)
        crm.add_lead("a@b.com", "N", "referral", "r1")
        crm.qualify("L1", "r1")

        crm.convert("L1", 100, "r1")
        crm.advance("O1", "proposal", "r1")
        crm.discount("O1", 5, "r1")
        self.assertEqual(reps, pristine)
        self.assertEqual(reps[0].keys(), {"id", "role", "capacity"})


if __name__ == "__main__":
    unittest.main()
