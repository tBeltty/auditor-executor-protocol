import unittest

from crm import CRM, DuplicateLeadError


def make_reps():
    return [
        {"id": "r1", "role": "rep", "capacity": 1},
        {"id": "r2", "role": "rep", "capacity": 2},
        {"id": "r3", "role": "rep", "capacity": 0},
        {"id": "m1", "role": "manager", "capacity": 0},
    ]


class TestAddLead(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(make_reps())

    def test_basic_lead(self):
        lead_id = self.crm.add_lead("  Alice@Example.COM  ", "  Alice  ", "web", "r1")
        self.assertEqual(lead_id, "L1")
        lead = self.crm.leads["L1"]
        self.assertEqual(lead["email"], "alice@example.com")
        self.assertEqual(lead["name"], "Alice")
        self.assertEqual(lead["source"], "web")
        self.assertEqual(lead["score"], 25)
        self.assertEqual(lead["status"], "new")
        self.assertEqual(lead["owner"], "r1")
        self.assertEqual(self.crm.log, [("add_lead", "L1", "r1")])

    def test_scores(self):
        cases = [
            ("a@corp.io", "web", 25),
            ("b@corp.io", "referral", 45),
            ("c@corp.io", "event", 35),
            ("d@gmail.com", "web", 10),
            ("e@yahoo.com", "referral", 30),
            ("f@outlook.com", "event", 20),
        ]
        for email, source, expected in cases:
            crm = CRM(make_reps())
            lead_id = crm.add_lead(email, "x", source, "r1")
            self.assertEqual(crm.leads[lead_id]["score"], expected, email)

    def test_email_validation(self):
        bad = [
            123,
            None,
            "no-at-sign.com",
            "a@@b.com",
            "a@b@c.com",
            "@b.com",
            "a@",
            "a@b",
            "a@.com",
            "a@com.",
            "a@.",
        ]
        for email in bad:
            with self.assertRaises(ValueError, msg=repr(email)):
                self.crm.add_lead(email, "Name", "web", "r1")
        self.assertEqual(self.crm.leads, {})
        self.assertEqual(self.crm.log, [])

    def test_valid_domains(self):
        for email in ("a@b.co", "a@sub.domain.com", "a.b@corp.example.org"):
            crm = CRM(make_reps())
            crm.add_lead(email, "Name", "web", "r1")

    def test_name_validation(self):
        for name in ("", "   ", None, 5):
            with self.assertRaises(ValueError, msg=repr(name)):
                self.crm.add_lead("x@y.com", name, "web", "r1")

    def test_source_validation(self):
        for source in ("phone", "", None, "WEB"):
            with self.assertRaises(ValueError, msg=repr(source)):
                self.crm.add_lead("x@y.com", "n", source, "r1")

    def test_duplicate(self):
        first = self.crm.add_lead("dup@corp.io", "A", "web", "r1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            self.crm.add_lead("  DUP@corp.io ", "B", "event", "r2")
        self.assertEqual(ctx.exception.existing_id, first)
        self.assertIsInstance(ctx.exception, Exception)
        self.assertEqual(len(self.crm.leads), 1)
        self.assertEqual(len(self.crm.log), 1)

    def test_failed_calls_do_not_consume_ids(self):
        self.crm.add_lead("one@corp.io", "A", "web", "r1")
        for bad in (("bad-email", "A", "web", "r1"), ("ok@corp.io", "", "web", "r1")):
            with self.assertRaises(ValueError):
                self.crm.add_lead(*bad)
        self.assertEqual(self.crm.add_lead("two@corp.io", "B", "web", "r1"), "L2")

    def test_unknown_actor_checked_first(self):
        with self.assertRaises(PermissionError):
            self.crm.add_lead("bad-email", "", "nope", "ghost")
        with self.assertRaises(PermissionError):
            self.crm.add_lead("ok@corp.io", "Name", "web", "m2")
        self.assertEqual(self.crm.leads, {})
        self.assertEqual(self.crm.log, [])

    def test_owner_lowest_load_with_tiebreak(self):
        self.assertEqual(self.crm.add_lead("a@corp.io", "A", "web", "r1"), "L1")
        self.assertEqual(self.crm.leads["L1"]["owner"], "r1")
        self.assertEqual(self.crm.add_lead("b@corp.io", "B", "web", "r1"), "L2")
        self.assertEqual(self.crm.leads["L2"]["owner"], "r2")
        self.assertEqual(self.crm.add_lead("c@corp.io", "C", "web", "r1"), "L3")
        self.assertEqual(self.crm.leads["L3"]["owner"], "r2")
        # all reps full (r3 has capacity 0): lead waits
        self.assertEqual(self.crm.add_lead("d@corp.io", "D", "web", "r1"), "L4")
        self.assertIsNone(self.crm.leads["L4"]["owner"])

    def test_manager_never_owns(self):
        crm = CRM([{"id": "m1", "role": "manager", "capacity": 5}])
        lead_id = crm.add_lead("a@corp.io", "A", "web", "m1")
        self.assertIsNone(crm.leads[lead_id]["owner"])

    def test_load_counts_qualified_and_convert(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 3},
                   {"id": "m1", "role": "manager", "capacity": 0}])
        lead_id = crm.add_lead("a@corp.io", "A", "referral", "r1")
        self.assertEqual(crm._load("r1"), 1)
        crm.qualify(lead_id, "r1")
        self.assertEqual(crm._load("r1"), 1)  # qualified still occupies a slot
        opp_id = crm.convert(lead_id, 100, "r1")
        self.assertEqual(crm._load("r1"), 1)  # converted lead -> open opp
        self.assertEqual(crm.opps[opp_id]["stage"], "prospect")
        crm.advance(opp_id, "lost", "r1")
        self.assertEqual(crm._load("r1"), 0)  # final opp no longer counts
        # the freed slot is usable by the next lead
        new_lead = crm.add_lead("b@corp.io", "B", "web", "r1")
        self.assertEqual(crm.leads[new_lead]["owner"], "r1")

    def test_log_shape_is_tuple(self):
        self.crm.add_lead("a@corp.io", "A", "web", "r1")
        entry = self.crm.log[0]
        self.assertIsInstance(entry, tuple)
        self.assertEqual(len(entry), 3)


class TestQualify(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(make_reps())

    def test_ok(self):
        lead_id = self.crm.add_lead("a@corp.io", "A", "referral", "r1")
        self.crm.qualify(lead_id, "r1")
        self.assertEqual(self.crm.leads[lead_id]["status"], "qualified")
        self.assertEqual(self.crm.log[-1], ("qualify", lead_id, "r1"))

    def test_manager_can_qualify(self):
        lead_id = self.crm.add_lead("a@corp.io", "A", "referral", "r1")
        self.crm.qualify(lead_id, "m1")
        self.assertEqual(self.crm.leads[lead_id]["status"], "qualified")

    def test_missing_lead(self):
        with self.assertRaises(ValueError):
            self.crm.qualify("L99", "m1")

    def test_permission(self):
        lead_id = self.crm.add_lead("a@corp.io", "A", "referral", "r1")
        with self.assertRaises(PermissionError):
            self.crm.qualify(lead_id, "r2")
        self.assertEqual(self.crm.leads[lead_id]["status"], "new")

    def test_permission_before_status_and_score(self):
        lead_id = self.crm.add_lead("a@gmail.com", "A", "web", "r1")
        with self.assertRaises(PermissionError):
            self.crm.qualify(lead_id, "r2")

    def test_status_must_be_new(self):
        lead_id = self.crm.add_lead("a@corp.io", "A", "referral", "r1")
        self.crm.qualify(lead_id, "r1")
        with self.assertRaises(ValueError):
            self.crm.qualify(lead_id, "r1")

    def test_score_threshold(self):
        low = self.crm.add_lead("a@gmail.com", "A", "web", "r1")
        self.assertEqual(self.crm.leads[low]["score"], 10)
        with self.assertRaises(ValueError):
            self.crm.qualify(low, "r1")
        mid = self.crm.add_lead("b@corp.io", "B", "web", "r2")
        self.assertEqual(self.crm.leads[mid]["score"], 25)
        with self.assertRaises(ValueError):
            self.crm.qualify(mid, "r2")

    def test_twenty_five_score_fails_but_thirty_passes(self):
        lead = self.crm.add_lead("a@corp.io", "A", "event", "r1")
        self.assertEqual(self.crm.leads[lead]["score"], 35)
        self.crm.qualify(lead, "r1")
        crm2 = CRM(make_reps())
        low = crm2.add_lead("b@gmail.com", "B", "event", "r1")
        self.assertEqual(crm2.leads[low]["score"], 20)
        with self.assertRaises(ValueError):
            crm2.qualify(low, "r1")

    def test_failure_adds_no_log(self):
        lead_id = self.crm.add_lead("a@gmail.com", "A", "web", "r1")
        before = list(self.crm.log)
        with self.assertRaises(ValueError):
            self.crm.qualify(lead_id, "r1")
        self.assertEqual(self.crm.log, before)


class TestConvert(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(make_reps())
        self.lead = self.crm.add_lead("a@corp.io", "A", "referral", "r1")
        self.crm.qualify(self.lead, "r1")

    def test_ok(self):
        opp_id = self.crm.convert(self.lead, 1000, "r1")
        self.assertEqual(opp_id, "O1")
        opp = self.crm.opps["O1"]
        self.assertEqual(opp["lead_id"], self.lead)
        self.assertEqual(opp["owner"], "r1")
        self.assertEqual(opp["amount"], 1000)
        self.assertEqual(opp["original_amount"], 1000)
        self.assertEqual(opp["stage"], "prospect")
        self.assertEqual(self.crm.leads[self.lead]["status"], "converted")
        self.assertEqual(self.crm.log[-1], ("convert", "O1", "r1"))

    def test_amount_validation(self):
        for amount in (0, -1, 1.5, "100", None, True, False):
            with self.assertRaises(ValueError, msg=repr(amount)):
                self.crm.convert(self.lead, amount, "r1")
        self.assertEqual(self.crm.opps, {})
        self.assertEqual(self.crm.leads[self.lead]["status"], "qualified")

    def test_missing_lead(self):
        with self.assertRaises(ValueError):
            self.crm.convert("L42", 10, "m1")

    def test_permission(self):
        with self.assertRaises(PermissionError):
            self.crm.convert(self.lead, 10, "r2")

    def test_permission_after_amount(self):
        with self.assertRaises(ValueError):
            self.crm.convert(self.lead, 0, "r2")

    def test_must_be_qualified(self):
        crm = CRM(make_reps())
        lead = crm.add_lead("b@corp.io", "B", "referral", "r1")
        with self.assertRaises(ValueError):
            crm.convert(lead, 10, "r1")
        self.assertEqual(crm.opps, {})

    def test_manager_can_convert(self):
        opp_id = self.crm.convert(self.lead, 10, "m1")
        self.assertEqual(self.crm.opps[opp_id]["owner"], "r1")

    def test_no_owner(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 0},
                   {"id": "m1", "role": "manager", "capacity": 0}])
        lead = crm.add_lead("c@corp.io", "C", "referral", "m1")
        self.assertIsNone(crm.leads[lead]["owner"])
        crm.qualify(lead, "m1")
        with self.assertRaises(ValueError):
            crm.convert(lead, 10, "m1")
        self.assertEqual(crm.opps, {})

    def test_opp_ids_count_only_successes(self):
        first = self.crm.convert(self.lead, 100, "r1")
        lead2 = self.crm.add_lead("b@corp.io", "B", "referral", "r2")
        self.crm.qualify(lead2, "r2")
        with self.assertRaises(ValueError):
            self.crm.convert(lead2, -5, "r2")
        second = self.crm.convert(lead2, 200, "r2")
        self.assertEqual((first, second), ("O1", "O2"))


if __name__ == "__main__":
    unittest.main()
