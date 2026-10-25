"""Tests for the general rules: attributes, log shape, routing, atomicity."""

import unittest

from crm import CRM, DuplicateLeadError


def load_of(crm, rep_id):
    """The spec's definition of load, recomputed from the public dicts."""
    count = 0
    for lead in crm.leads.values():
        if lead["owner"] == rep_id and lead["status"] in ("new", "qualified"):
            count += 1
    for opp in crm.opps.values():
        if opp["owner"] == rep_id and opp["stage"] not in ("won", "lost"):
            count += 1
    return count



class TestAttributes(unittest.TestCase):
    def setUp(self):
        self.crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 1},
        ])

    def test_containers_exist_and_are_empty(self):
        self.assertEqual(self.crm.leads, {})
        self.assertEqual(self.crm.opps, {})
        self.assertEqual(self.crm.log, [])
        self.assertIsInstance(self.crm.leads, dict)
        self.assertIsInstance(self.crm.opps, dict)
        self.assertIsInstance(self.crm.log, list)

    def test_log_entries_are_three_tuples(self):
        self.crm.add_lead("a@acme.com", "A", "referral", "m1")
        self.crm.qualify("L1", "m1")
        self.crm.convert("L1", 500, "m1")
        self.crm.advance("O1", "proposal", "m1")
        self.crm.discount("O1", 5, "m1")
        self.crm.transfer("O1", "r2", "m1")
        for entry in self.crm.log:
            self.assertIsInstance(entry, tuple)
            self.assertEqual(len(entry), 3)
            op, entity, actor = entry
            self.assertIsInstance(op, str)
            self.assertIsInstance(entity, str)
            self.assertIsInstance(actor, str)
        self.assertEqual([e[0] for e in self.crm.log],
                         ["add_lead", "qualify", "convert", "advance",
                          "discount", "transfer"])
        self.assertTrue(all(e[2] == "m1" for e in self.crm.log))

    def test_leads_keyed_by_id(self):
        lid = self.crm.add_lead("a@acme.com", "A", "web", "m1")
        self.assertIn(lid, self.crm.leads)
        self.assertEqual(self.crm.leads[lid]["id"], lid)

    def test_opps_keyed_by_id(self):
        self.crm.add_lead("a@acme.com", "A", "referral", "m1")
        self.crm.qualify("L1", "m1")
        oid = self.crm.convert("L1", 500, "m1")
        self.assertIn(oid, self.crm.opps)
        self.assertEqual(self.crm.opps[oid]["id"], oid)

    def test_duplicate_lead_error_carries_existing_id(self):
        self.crm.add_lead("a@acme.com", "A", "web", "m1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            self.crm.add_lead("a@acme.com", "A", "web", "m1")
        self.assertEqual(ctx.exception.existing_id, "L1")
        self.assertIn("L1", str(ctx.exception))


class TestRoutingIgnoresActor(unittest.TestCase):
    def test_actor_is_not_the_owner_by_default(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1},
                   {"id": "r2", "role": "rep", "capacity": 1}])
        crm.add_lead("a@acme.com", "A", "web", "r2")
        self.assertEqual(crm.leads["L1"]["owner"], "r1")  # tie -> smallest id

    def test_managers_never_receive_work_even_with_earlier_id(self):
        crm = CRM([{"id": "aaa", "role": "manager", "capacity": 10},
                   {"id": "zzz", "role": "rep", "capacity": 10}])
        crm.add_lead("a@acme.com", "A", "web", "aaa")
        crm.add_lead("b@acme.com", "B", "web", "aaa")
        self.assertEqual(crm.leads["L1"]["owner"], "zzz")
        self.assertEqual(crm.leads["L2"]["owner"], "zzz")

    def test_no_reps_means_everything_waits(self):
        crm = CRM([{"id": "m1", "role": "manager", "capacity": 3}])
        for i in range(3):
            crm.add_lead("u%d@acme.com" % i, "N", "web", "m1")
            self.assertIsNone(crm.leads["L%d" % (i + 1)]["owner"])
        self.assertEqual(len(crm.leads), 3)

    def test_empty_team(self):
        crm = CRM([])
        with self.assertRaises(PermissionError):
            crm.add_lead("a@acme.com", "A", "web", "anyone")

    def test_load_helper_counts_open_work_only(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 4},
                   {"id": "m1", "role": "manager", "capacity": 4}])
        self.assertEqual(load_of(crm, "r1"), 0)
        crm.add_lead("a@acme.com", "A", "referral", "m1")
        crm.add_lead("b@acme.com", "B", "referral", "m1")
        self.assertEqual(load_of(crm, "r1"), 2)
        crm.qualify("L1", "m1")
        self.assertEqual(load_of(crm, "r1"), 2)
        crm.convert("L1", 100, "m1")
        self.assertEqual(load_of(crm, "r1"), 2)
        crm.advance("O1", "proposal", "m1")
        self.assertEqual(load_of(crm, "r1"), 2)
        crm.advance("O1", "negotiation", "m1")
        self.assertEqual(load_of(crm, "r1"), 2)
        crm.advance("O1", "won", "m1")
        self.assertEqual(load_of(crm, "r1"), 1)


class TestAtomicity(unittest.TestCase):
    def snapshot(self, crm):
        return (
            {k: dict(v) for k, v in crm.leads.items()},
            {k: dict(v) for k, v in crm.opps.items()},
            list(crm.log),
        )

    def test_every_rejected_call_is_inert(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1},
                   {"id": "r2", "role": "rep", "capacity": 1},
                   {"id": "m1", "role": "manager", "capacity": 1}])
        crm.add_lead("a@acme.com", "A", "referral", "m1")
        crm.qualify("L1", "m1")
        crm.convert("L1", 1000, "m1")
        crm.advance("O1", "proposal", "m1")
        crm.add_lead("b@acme.com", "B", "web", "m1")

        bad_calls = [
            ("add_lead", ("c@acme.com", "C", "radio", "m1")),
            ("add_lead", ("bad", "C", "web", "m1")),
            ("add_lead", ("a@acme.com", "dup", "web", "m1")),
            ("add_lead", ("d@acme.com", "D", "web", "ghost")),
            ("qualify", ("L1", "m1")),
            ("qualify", ("L9", "m1")),
            ("qualify", ("L2", "m1")),
            ("convert", ("L2", 100, "m1")),
            ("convert", ("L1", 100, "m1")),
            ("advance", ("O1", "won", "m1")),
            ("advance", ("O1", "bogus", "m1")),
            ("advance", ("O9", "proposal", "m1")),
            ("discount", ("O1", 40, "m1")),
            ("discount", ("O1", 31, "m1")),
            ("discount", ("O1", 5, "r2")),
            ("transfer", ("O1", "r2", "r1")),
            ("transfer", ("O1", "m1", "m1")),
            ("transfer", ("O1", "r1", "m1")),
        ]
        before = self.snapshot(crm)
        for name, args in bad_calls:
            with self.subTest(call=name, args=args):
                with self.assertRaises((ValueError, PermissionError,
                                        DuplicateLeadError)):
                    getattr(crm, name)(*args)
                after = self.snapshot(crm)
                self.assertEqual(before[0], after[0], "leads changed")
                self.assertEqual(before[1], after[1], "opps changed")
                self.assertEqual(before[2], after[2], "log changed")

    def test_failed_calls_do_not_consume_ids(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 5},
                   {"id": "m1", "role": "manager", "capacity": 5}])
        for _ in range(3):
            with self.assertRaises(ValueError):
                crm.add_lead("nope", "N", "web", "m1")
        self.assertEqual(crm.add_lead("a@acme.com", "A", "web", "m1"), "L1")
        crm.leads["L1"]["score"] = 30
        crm.qualify("L1", "m1")
        for _ in range(3):
            with self.assertRaises(ValueError):
                crm.convert("L1", -1, "m1")
        self.assertEqual(crm.convert("L1", 10, "m1"), "O1")

    def test_successful_calls_log_exactly_once(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 5},
                   {"id": "r2", "role": "rep", "capacity": 5},
                   {"id": "m1", "role": "manager", "capacity": 5}])
        crm.add_lead("a@acme.com", "A", "referral", "m1")
        crm.qualify("L1", "m1")
        crm.convert("L1", 100, "m1")
        crm.advance("O1", "proposal", "m1")
        crm.discount("O1", 5, "m1")
        crm.transfer("O1", "r2", "m1")
        self.assertEqual(crm.log, [
            ("add_lead", "L1", "m1"),
            ("qualify", "L1", "m1"),
            ("convert", "O1", "m1"),
            ("advance", "O1", "m1"),
            ("discount", "O1", "m1"),
            ("transfer", "O1", "m1"),
        ])


class TestPublicSurface(unittest.TestCase):
    def test_spec_attributes_only(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1}])
        for name in ("leads", "opps", "log"):
            self.assertTrue(hasattr(crm, name), name)

    def test_unhashable_source_is_value_error(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1}])
        for bad in [["web"], {"web": 1}, set()]:
            with self.subTest(source=bad):
                with self.assertRaises(ValueError):
                    crm.add_lead("a@b.co", "A", bad, "r1")

    def test_unhashable_stage_is_value_error(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1}])
        crm.add_lead("a@b.co", "A", "referral", "r1")
        crm.qualify("L1", "r1")
        crm.convert("L1", 10, "r1")
        with self.assertRaises(ValueError):
            crm.advance("O1", ["won"], "r1")

    def test_unhashable_ids_are_not_type_errors(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1},
                   {"id": "m1", "role": "manager", "capacity": 1}])
        with self.assertRaises(PermissionError):
            crm.add_lead("a@b.co", "A", "web", ["r1"])
        with self.assertRaises(ValueError):
            crm.qualify(["L1"], "r1")
        with self.assertRaises(ValueError):
            crm.convert(["L1"], 10, "r1")
        with self.assertRaises(ValueError):
            crm.advance({"O1": 1}, "won", "r1")
        with self.assertRaises(ValueError):
            crm.discount(["O1"], 5, "r1")
        with self.assertRaises(ValueError):
            crm.transfer(["O1"], "r1", "m1")
        # rule 1 (existence) is listed before rule 2 (manager) in transfer
        with self.assertRaises(ValueError):
            crm.transfer(["O1"], "r1", "r1")
        # but an unknown *actor* is always checked first
        with self.assertRaises(PermissionError):
            crm.transfer("O1", "r1", "ghost")

    def test_unknown_rep_id_on_transfer_is_value_error(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1},
                   {"id": "m1", "role": "manager", "capacity": 1}])
        crm.add_lead("a@b.co", "A", "referral", "m1")
        crm.qualify("L1", "m1")
        crm.convert("L1", 10, "m1")
        with self.assertRaises(ValueError):
            crm.transfer("O1", "nobody", "m1")

    def test_no_state_leakage_between_instances(self):
        a = CRM([{"id": "r1", "role": "rep", "capacity": 1}])
        b = CRM([{"id": "r1", "role": "rep", "capacity": 1}])
        a.add_lead("x@y.co", "X", "web", "r1")
        self.assertEqual(b.leads, {})
        self.assertEqual(b.log, [])


if __name__ == "__main__":
    unittest.main()
