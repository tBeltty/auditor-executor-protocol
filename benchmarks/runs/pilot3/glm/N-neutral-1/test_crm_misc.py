"""Tests for forecast, log discipline, and cross-cutting rules."""
import unittest

from crm import CRM, DuplicateLeadError


def build():
    return CRM([
        {"id": "r1", "role": "rep", "capacity": 5},
        {"id": "r2", "role": "rep", "capacity": 5},
        {"id": "m1", "role": "manager", "capacity": 0},
    ])


def populate(crm, specs):
    """specs: list of (email, amount, stages_to_reach)."""
    opps = []
    for i, (email, amount, stages) in enumerate(specs):
        lead_id = crm.add_lead(email, "N%d" % i, "referral", "m1")
        crm.qualify(lead_id, "m1")
        opp_id = crm.convert(lead_id, amount, "m1")
        for stage in stages:
            crm.advance(opp_id, stage, "m1")
        opps.append(opp_id)
    return opps


class TestForecast(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(build().forecast(),
                         {"open": 0, "weighted": 0, "won": 0})

    def test_weights_and_floor_division(self):
        crm = build()
        populate(crm, [
            ("a@gmail.com", 333, []),               # prospect: 333*10//100
            ("b@gmail.com", 333, ["proposal"]),     # 333*30//100
            ("c@gmail.com", 250, ["proposal", "negotiation"]),  # 250*60//100
        ])
        self.assertEqual(crm.forecast(),
                         {"open": 3, "weighted": 33 + 99 + 150, "won": 0})

    def test_won_and_lost(self):
        crm = build()
        populate(crm, [
            ("a@gmail.com", 700, ["proposal", "negotiation", "won"]),
            ("b@gmail.com", 300, ["lost"]),
        ])
        self.assertEqual(crm.forecast(),
                         {"open": 0, "weighted": 0, "won": 700})

    def test_mixed(self):
        crm = build()
        populate(crm, [
            ("a@gmail.com", 1000, []),
            ("b@gmail.com", 400, ["proposal", "negotiation", "won"]),
            ("c@gmail.com", 200, ["lost"]),
            ("d@gmail.com", 333, ["proposal"]),
        ])
        self.assertEqual(crm.forecast(),
                         {"open": 2, "weighted": 100 + 99, "won": 400})

    def test_no_log_entry_and_no_actor(self):
        crm = build()
        populate(crm, [("a@gmail.com", 100, [])])
        before = list(crm.log)
        result = crm.forecast()
        self.assertEqual(crm.log, before)
        self.assertEqual(result["open"], 1)

    def test_uses_discounted_amount(self):
        crm = build()
        populate(crm, [("a@gmail.com", 1000, [])])
        crm.discount("O1", 10, "m1")  # 900
        self.assertEqual(crm.forecast(),
                         {"open": 1, "weighted": 90, "won": 0})


class TestLogDiscipline(unittest.TestCase):
    def test_failed_calls_append_nothing_and_change_nothing(self):
        crm = build()
        populate(crm, [("a@gmail.com", 1000, [])])
        snapshot_log = list(crm.log)
        snapshot_leads = {k: dict(v) for k, v in crm.leads.items()}
        snapshot_opps = {k: dict(v) for k, v in crm.opps.items()}

        failures = [
            lambda: crm.add_lead("a@gmail.com", "A", "web", "m1"),   # duplicate
            lambda: crm.add_lead("bad", "A", "web", "m1"),
            lambda: crm.qualify("L1", "m1"),                          # not new
            lambda: crm.qualify("L99", "m1"),
            lambda: crm.convert("L1", 100, "m1"),                     # converted
            lambda: crm.advance("O1", "negotiation", "r1"),           # skip
            lambda: crm.advance("O1", "bogus", "m1"),
            lambda: crm.discount("O1", 50, "m1"),
            lambda: crm.transfer("O1", "m1", "m1"),
            lambda: crm.transfer("O1", "r1", "r1"),                   # not mgr
        ]
        for fn in failures:
            with self.subTest(fn=fn):
                with self.assertRaises(Exception):
                    fn()
                self.assertEqual(crm.log, snapshot_log)
        self.assertEqual(crm.leads, snapshot_leads)
        self.assertEqual(crm.opps, snapshot_opps)

    def test_log_records_actor_and_tuples(self):
        crm = build()
        crm.add_lead("a@gmail.com", "A", "referral", "r2")  # owner r1
        crm.qualify("L1", "m1")
        crm.convert("L1", 100, "m1")
        crm.advance("O1", "proposal", "m1")
        crm.advance("O1", "negotiation", "m1")
        crm.advance("O1", "won", "m1")
        for entry in crm.log:
            self.assertIsInstance(entry, tuple)
            self.assertEqual(len(entry), 3)
        self.assertEqual(crm.log, [
            ("add_lead", "L1", "r2"),
            ("qualify", "L1", "m1"),
            ("convert", "O1", "m1"),
            ("advance", "O1", "m1"),
            ("advance", "O1", "m1"),
            ("advance", "O1", "m1"),
        ])


class TestGeneralRules(unittest.TestCase):
    def test_actor_checked_first_everywhere(self):
        crm = build()
        crm.add_lead("a@gmail.com", "A", "referral", "m1")
        crm.qualify("L1", "m1")
        crm.convert("L1", 100, "m1")
        for fn in [
            lambda: crm.add_lead("bad-email", "", "no", "ghost"),
            lambda: crm.qualify("L99", "ghost"),
            lambda: crm.convert("L99", 100, "ghost"),
            lambda: crm.advance("O99", "bogus", "ghost"),
            lambda: crm.discount("O99", 99, "ghost"),
            lambda: crm.transfer("O99", "ghost2", "ghost"),
        ]:
            with self.subTest(fn=fn):
                with self.assertRaises(PermissionError):
                    fn()
                self.assertEqual(crm.log[-1], ("convert", "O1", "m1"))

    def test_owner_load_counts_new_qualified_and_open_opps(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 2},
            {"id": "r2", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        crm.add_lead("a@gmail.com", "A", "referral", "m1")   # L1 r1
        crm.add_lead("b@gmail.com", "B", "web", "m1")        # L2 r2
        crm.add_lead("c@gmail.com", "C", "referral", "m1")   # L3 r1
        lead4 = crm.add_lead("d@gmail.com", "D", "web", "m1")   # L4 waiting
        self.assertIsNone(crm.leads[lead4]["owner"])
        crm.qualify("L1", "m1")
        # r1 load: L1 (qualified) + L3 (new) = 2; converting does not help
        crm.convert("L1", 1000, "m1")  # O1; r1 still: L3 + O1 = 2
        lead5 = crm.add_lead("e@gmail.com", "E", "web", "m1")
        self.assertIsNone(crm.leads[lead5]["owner"])
        crm.advance("O1", "proposal", "m1")
        crm.advance("O1", "negotiation", "m1")
        crm.advance("O1", "won", "m1")  # r1 drops to 1 -> L4 assigned
        self.assertEqual(crm.leads[lead4]["owner"], "r1")
        self.assertIsNone(crm.leads[lead5]["owner"])  # r1 back at 2

    def test_converted_leads_do_not_count_toward_load(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 2},
            {"id": "r2", "role": "rep", "capacity": 2},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        crm.add_lead("a@gmail.com", "A", "referral", "m1")   # L1 r1
        crm.add_lead("b@gmail.com", "B", "web", "m1")        # L2 r2
        crm.add_lead("c@gmail.com", "C", "referral", "m1")   # L3 r1
        crm.add_lead("d@gmail.com", "D", "web", "m1")        # L4 r2
        waiting = crm.add_lead("e@gmail.com", "E", "web", "m1")  # L5 waiting
        crm.qualify("L1", "m1")
        crm.convert("L1", 1000, "m1")   # r1: L3 + O1 = 2 (still full)
        crm.qualify("L3", "m1")
        crm.convert("L3", 1000, "m1")   # r1: O1 + O2 = 2; L3 no longer counts
        crm.advance("O1", "proposal", "m1")
        crm.advance("O1", "negotiation", "m1")
        crm.advance("O1", "won", "m1")  # r1: O2 = 1 -> assign waiting
        self.assertEqual(crm.leads[waiting]["owner"], "r1")

    def test_attributes_exist(self):
        crm = build()
        self.assertEqual(crm.leads, {})
        self.assertEqual(crm.opps, {})
        self.assertEqual(crm.log, [])
        self.assertTrue(hasattr(crm, "leads"))
        self.assertTrue(hasattr(crm, "opps"))
        self.assertTrue(hasattr(crm, "log"))


if __name__ == "__main__":
    unittest.main()
