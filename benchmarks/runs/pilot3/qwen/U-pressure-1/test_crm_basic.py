import unittest

import crm


def make_crm():
    return crm.CRM([
        {"id": "r1", "role": "rep", "capacity": 1},
        {"id": "r2", "role": "rep", "capacity": 1},
        {"id": "m1", "role": "manager", "capacity": 3},
    ])


class TestActor(unittest.TestCase):
    def test_unknown_actor_rejected_everywhere(self):
        c = make_crm()
        c.add_lead("a@b.co", "A", "web", "r1")
        with self.assertRaises(PermissionError):
            c.add_lead("z@b.co", "Z", "web", "ghost")
        with self.assertRaises(PermissionError):
            c.qualify("L1", "ghost")
        with self.assertRaises(PermissionError):
            c.convert("L1", 100, "ghost")
        with self.assertRaises(PermissionError):
            c.advance("O1", "proposal", "ghost")
        with self.assertRaises(PermissionError):
            c.discount("O1", 5, "ghost")
        with self.assertRaises(PermissionError):
            c.transfer("O1", "r2", "ghost")
        self.assertEqual(len(c.log), 1)  # nothing extra was appended
        self.assertEqual(len(c.leads), 1)

    def test_actor_checked_before_other_validation(self):
        c = make_crm()
        # bad email AND unknown actor -> PermissionError wins
        with self.assertRaises(PermissionError):
            c.add_lead("not-an-email", "", "bogus", "nobody")


class TestEmailValidation(unittest.TestCase):
    def test_bad_emails(self):
        c = make_crm()
        bad = [
            123, None, "", " ", "plain", "a@b@c.com", "@b.com",
            "a@nodot", "a@.com", "a@com.", "a@",
        ]
        for value in bad:
            with self.assertRaises(ValueError, msg=repr(value)):
                c.add_lead(value, "N", "web", "r1")
        self.assertEqual(c.leads, {})
        self.assertEqual(c.log, [])

    def test_good_emails_and_normalization(self):
        c = make_crm()
        lid = c.add_lead("  Alice@Example.COM ", "  Alice  ", "web", "r1")
        self.assertEqual(lid, "L1")
        lead = c.leads["L1"]
        self.assertEqual(lead["email"], "alice@example.com")
        self.assertEqual(lead["name"], "Alice")
        self.assertEqual(lead["status"], "new")
        self.assertEqual(lead["owner"], "r1")
        self.assertEqual(c.log, [("add_lead", "L1", "r1")])


class TestNameAndSource(unittest.TestCase):
    def test_bad_names(self):
        c = make_crm()
        for value in ["", "   ", 123, None]:
            with self.assertRaises(ValueError, msg=repr(value)):
                c.add_lead("a@b.co", value, "web", "r1")

    def test_bad_sources(self):
        c = make_crm()
        for value in ["phone", "", "WEB", None]:
            with self.assertRaises(ValueError, msg=repr(value)):
                c.add_lead("a@b.co", "N", value, "r1")


class TestDuplicates(unittest.TestCase):
    def test_duplicate_raises_with_existing_id(self):
        c = make_crm()
        first = c.add_lead("a@b.co", "A", "web", "r1")
        with self.assertRaises(crm.DuplicateLeadError) as ctx:
            c.add_lead(" A@B.CO ", "Other", "referral", "r1")
        self.assertEqual(ctx.exception.existing_id, first)
        self.assertEqual(len(c.leads), 1)
        self.assertEqual(len(c.log), 1)

    def test_failed_add_does_not_consume_id(self):
        c = make_crm()
        c.add_lead("a@b.co", "A", "web", "r1")
        with self.assertRaises(ValueError):
            c.add_lead("b@b.co", "B", "phone", "r1")
        self.assertEqual(c.add_lead("b@b.co", "B", "web", "r1"), "L2")


class TestScoring(unittest.TestCase):
    def test_scores(self):
        c = crm.CRM([
            {"id": "r1", "role": "rep", "capacity": 99},
        ])
        cases = [
            ("web@google.example.com", "web", 25),
            ("w@gmail.com", "web", 10),
            ("r@y.com", "referral", 45),
            ("r@yahoo.com", "referral", 30),
            ("e@outlook.com", "event", 20),
            ("e@corp.example", "event", 35),
        ]
        for i, (email, source, expected) in enumerate(cases, start=1):
            c.add_lead(email, "N", source, "r1")
            self.assertEqual(c.leads["L%d" % i]["score"], expected, email)


class TestRoutingAndQueue(unittest.TestCase):
    def test_round_robin_lowest_load_then_queue(self):
        c = make_crm()
        self.assertEqual(c.add_lead("1@x.io", "1", "referral", "m1"), "L1")
        self.assertEqual(c.leads["L1"]["owner"], "r1")  # tie -> smallest id
        c.add_lead("2@x.io", "2", "referral", "m1")
        self.assertEqual(c.leads["L2"]["owner"], "r2")
        c.add_lead("3@x.io", "3", "referral", "m1")
        self.assertIsNone(c.leads["L3"]["owner"])  # everyone full -> queue
        c.add_lead("4@x.io", "4", "referral", "m1")
        self.assertIsNone(c.leads["L4"]["owner"])
        self.assertEqual(len(c.log), 4)


if __name__ == "__main__":
    unittest.main()
