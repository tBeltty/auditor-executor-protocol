import unittest

from crm import CRM, DuplicateLeadError


def make_crm(*specs):
    reps = [{"id": i, "role": r, "capacity": c} for (i, r, c) in specs]
    return CRM(reps)


class TestActorFirst(unittest.TestCase):
    def test_unknown_actor_raises_permission_error_everywhere(self):
        c = make_crm(("r1", "rep", 1), ("m1", "manager", 0))
        lid = c.add_lead("a@b.com", "A", "web", "r1")
        self.assertEqual(len(c.log), 1)
        with self.assertRaises(PermissionError):
            c.add_lead("x@y.com", "X", "web", "ghost")
        with self.assertRaises(PermissionError):
            c.qualify(lid, "ghost")
        with self.assertRaises(PermissionError):
            c.qualify("nope", "ghost")  # actor check before existence
        with self.assertRaises(PermissionError):
            c.convert(lid, 10, "ghost")
        with self.assertRaises(PermissionError):
            c.advance("O-does-not-exist", "proposal", "ghost")
        with self.assertRaises(PermissionError):
            c.discount("O-does-not-exist", 5, "ghost")
        with self.assertRaises(PermissionError):
            c.transfer("O-does-not-exist", "r1", "ghost")
        # failed calls append nothing
        self.assertEqual(len(c.log), 1)

    def test_log_entry_shape(self):
        c = make_crm(("r1", "rep", 1))
        lid = c.add_lead("a@b.com", "Ann", "web", "r1")
        self.assertEqual(c.log, [("add_lead", lid, "r1")])


class TestEmailValidation(unittest.TestCase):
    BAD = [
        "",
        "noatsign.com",
        "@b.com",
        "a@@b.com",
        "a@b@c.com",
        "a@b",            # domain without "."
        "a@.com",         # "." first char of domain
        "a@com.",         # "." last char of domain
        "a@b.",
        "a@.",
        123,
        b"a@b.com",
        None,
    ]

    def test_invalid_emails(self):
        c = make_crm(("r1", "rep", 5))
        for bad in self.BAD:
            with self.assertRaises(ValueError, msg="email=%r" % (bad,)):
                c.add_lead(bad, "N", "web", "r1")
        self.assertEqual(c.leads, {})
        self.assertEqual(c.log, [])

    def test_normalization(self):
        c = make_crm(("r1", "rep", 5))
        lid = c.add_lead("  Jo.H@Example.COM ", "Bob", "web", "r1")
        self.assertEqual(c.leads[lid]["email"], "jo.h@example.com")
        self.assertEqual(c.leads[lid]["name"], "Bob")

    def test_valid_edge_domains(self):
        c = make_crm(("r1", "rep", 5))
        # interior dot present, local part non-empty
        c.add_lead("a@b.c", "A", "web", "r1")
        c.add_lead("a@sub.example.com", "A2", "web", "r1")
        self.assertEqual(len(c.leads), 2)


class TestNameSourceValidation(unittest.TestCase):
    def test_name(self):
        c = make_crm(("r1", "rep", 5))
        for bad in ["", "   ", "\t\n", 123, None, ["x"]]:
            with self.assertRaises(ValueError, msg="name=%r" % (bad,)):
                c.add_lead("a@b.com", bad, "web", "r1")

    def test_name_is_stripped(self):
        c = make_crm(("r1", "rep", 5))
        lid = c.add_lead("a@b.com", "  Vera  ", "web", "r1")
        self.assertEqual(c.leads[lid]["name"], "Vera")

    def test_source(self):
        c = make_crm(("r1", "rep", 5))
        for bad in ["phone", "WEB", "", None, 5]:
            with self.assertRaises(ValueError, msg="source=%r" % (bad,)):
                c.add_lead("a@b.com", "A", bad, "r1")

    def test_source_checked_before_duplicate(self):
        c = make_crm(("r1", "rep", 5))
        first = c.add_lead("a@b.com", "A", "web", "r1")
        with self.assertRaises(ValueError):
            c.add_lead("a@b.com", "A", "phone", "r1")  # not DuplicateLeadError
        self.assertEqual(first, "L1")


class TestDuplicate(unittest.TestCase):
    def test_duplicate_raises_with_existing_id(self):
        c = make_crm(("r1", "rep", 5))
        l1 = c.add_lead("Ann@Example.com", "A", "web", "r1")
        c.add_lead("other@x.com", "B", "web", "r1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            c.add_lead("  ann@example.COM ", "A again", "event", "r1")
        self.assertEqual(ctx.exception.existing_id, l1)
        self.assertEqual(l1, "L1")
        # failed add does not consume the id sequence nor log
        l3 = c.add_lead("third@x.com", "C", "web", "r1")
        self.assertEqual(l3, "L3")
        self.assertEqual(c.log[-1], ("add_lead", "L3", "r1"))


class TestScoring(unittest.TestCase):
    def test_scores(self):
        c = make_crm(("r1", "rep", 10))
        cases = [
            ("w1@corp.com", "web", 25),
            ("w2@gmail.com", "web", 10),
            ("r1x@yahoo.com", "referral", 30),
            ("r2x@corp.com", "referral", 45),
            ("e1@outlook.com", "event", 20),
            ("e2@sub.corp.com", "event", 35),
        ]
        for email, src, score in cases:
            lid = c.add_lead(email, "N", src, "r1")
            self.assertEqual(c.leads[lid]["score"], score, email)


class TestOwnerSelection(unittest.TestCase):
    def test_lowest_load_then_lexicographic_tie(self):
        c = make_crm(("r1", "rep", 3), ("r2", "rep", 3))
        a = c.add_lead("a@x.com", "A", "web", "r1")
        b = c.add_lead("b@x.com", "B", "web", "r1")
        d = c.add_lead("d@x.com", "D", "web", "r1")
        # loads: r1=0,r2=0 -> tie lexicographic r1; then r2 (load 0); then 1,1 tie -> r1
        self.assertEqual(c.leads[a]["owner"], "r1")
        self.assertEqual(c.leads[b]["owner"], "r2")
        self.assertEqual(c.leads[d]["owner"], "r1")

    def test_tie_break_is_string_order_not_numeric(self):
        c = make_crm(("r10", "rep", 5), ("r2", "rep", 5))
        a = c.add_lead("a@x.com", "A", "web", "r10")
        self.assertEqual(c.leads[a]["owner"], "r10")  # "r10" < "r2" as strings

    def test_managers_never_own(self):
        c = make_crm(("m1", "manager", 5))
        lid = c.add_lead("a@x.com", "A", "web", "m1")
        self.assertIsNone(c.leads[lid]["owner"])
        self.assertEqual(list(c.leads[lid].keys()),
                         ["id", "email", "name", "source", "score", "owner", "status"])

    def test_capacity_and_fifo_queue(self):
        c = make_crm(("r1", "rep", 2))
        l1 = c.add_lead("1@x.com", "A", "web", "r1")
        l2 = c.add_lead("2@x.com", "B", "web", "r1")
        l3 = c.add_lead("3@x.com", "C", "web", "r1")
        l4 = c.add_lead("4@x.com", "D", "web", "r1")
        self.assertEqual(c.leads[l1]["owner"], "r1")
        self.assertEqual(c.leads[l2]["owner"], "r1")
        self.assertIsNone(c.leads[l3]["owner"])
        self.assertIsNone(c.leads[l4]["owner"])
        # failed add_lead (duplicate) keeps queue intact
        with self.assertRaises(DuplicateLeadError):
            c.add_lead("1@x.com", "dup", "web", "r1")
        # freeing exactly one slot assigns exactly the oldest waiting lead
        c2 = make_crm(("r1", "rep", 1), ("m1", "manager", 0))
        l = c2.add_lead("q@x.com", "Q", "referral", "m1")
        self.assertEqual(c2.leads[l]["owner"], "r1")
        c2.qualify(l, "m1")
        opp = c2.convert(l, 100, "m1")
        self.assertEqual(opp, "O1")
        w1 = c2.add_lead("w1@x.com", "W1", "web", "r1")
        w2 = c2.add_lead("w2@x.com", "W2", "web", "r1")
        self.assertIsNone(c2.leads[w1]["owner"])
        self.assertIsNone(c2.leads[w2]["owner"])
        c2.advance(opp, "proposal", "r1")
        c2.advance(opp, "negotiation", "r1")
        c2.advance(opp, "won", "r1")
        self.assertEqual(c2.leads[w1]["owner"], "r1")
        self.assertIsNone(c2.leads[w2]["owner"])
        self.assertIn(("assign", w1, "system"), c2.log)
        n_assigns = [e for e in c2.log if e[0] == "assign"]
        self.assertEqual(n_assigns, [("assign", w1, "system")])


class TestQualify(unittest.TestCase):
    def setUp(self):
        self.c = make_crm(("r1", "rep", 2), ("r2", "rep", 2), ("m1", "manager", 0))
        self.lid = self.c.add_lead("a@x.com", "A", "referral", "r1")  # score 30

    def test_ok_by_owner_and_by_manager(self):
        self.c.qualify(self.lid, "r1")
        self.assertEqual(self.c.leads[self.lid]["status"], "qualified")
        self.assertEqual(self.c.log[-1], ("qualify", self.lid, "r1"))
        other = self.c.add_lead("b@x.com", "B", "referral", "r2")
        self.c.qualify(other, "m1")  # manager may qualify any lead
        self.assertEqual(self.c.leads[other]["status"], "qualified")

    def test_check_order(self):
        with self.assertRaises(ValueError):
            self.c.qualify("L99", "r1")  # unknown lead
        other = self.c.add_lead("b@x.com", "B", "referral", "r2")
        with self.assertRaises(PermissionError):
            self.c.qualify(other, "r1")  # not owner/manager, even though status fine
        low = self.c.add_lead("c@x.com", "C", "web", "r1")  # score 10, status new
        with self.assertRaises(ValueError):
            self.c.qualify(low, "r1")
        self.c.qualify(self.lid, "r1")
        with self.assertRaises(ValueError):
            self.c.qualify(self.lid, "r1")  # already qualified beats score check
        with self.assertRaises(PermissionError):
            self.c.qualify(other, "r1")
        # failures changed nothing
        self.assertEqual(self.c.leads[low]["status"], "new")
        self.assertEqual([e for e in self.c.log if e[0] == "qualify"],
                         [("qualify", self.lid, "r1")])

    def test_event_gmail_score_20_rejected(self):
        lid = self.c.add_lead("d@gmail.com", "D", "event", "r1")  # 20, no domain bonus
        self.assertEqual(self.c.leads[lid]["score"], 20)
        with self.assertRaises(ValueError):
            self.c.qualify(lid, "m1")


class TestConvert(unittest.TestCase):
    def setUp(self):
        self.c = make_crm(("r1", "rep", 3), ("r2", "rep", 3), ("m1", "manager", 0))
        self.lid = self.c.add_lead("a@x.com", "A", "referral", "r1")
        self.c.qualify(self.lid, "r1")

    def test_success(self):
        oid = self.c.convert(self.lid, 1000, "r1")
        self.assertEqual(oid, "O1")
        self.assertEqual(self.c.opps[oid], {
            "id": "O1", "lead_id": self.lid, "owner": "r1",
            "amount": 1000, "original_amount": 1000, "stage": "prospect",
        })
        self.assertEqual(self.c.leads[self.lid]["status"], "converted")
        self.assertEqual(self.c.log[-1], ("convert", "O1", "r1"))

    def test_amount_validation(self):
        for bad in [True, False, 0, -5, 10.0, "10", None]:
            with self.assertRaises(ValueError, msg="amount=%r" % (bad,)):
                self.c.convert(self.lid, bad, "r1")

    def test_check_order(self):
        other = self.c.add_lead("b@x.com", "B", "referral", "r2")
        self.c.qualify(other, "m1")
        # amount (ValueError) is checked before actor (PermissionError):
        # known-but-wrong actor with invalid amount -> ValueError wins
        with self.assertRaises(ValueError):
            self.c.convert(other, -1, "r1")
        # unknown actor still raises first -> PermissionError
        with self.assertRaises(PermissionError):
            self.c.convert(other, -1, "ghost2")
        # wrong actor with valid amount -> PermissionError
        with self.assertRaises(PermissionError):
            self.c.convert(other, 5, "r1")
        # unowned qualified lead: manager passes the actor check (#3),
        # then the no-owner check (#5) raises ValueError
        solo = make_crm(("m9", "manager", 0))
        un = solo.add_lead("c@y.com", "C", "referral", "m9")
        self.assertIsNone(solo.leads[un]["owner"])
        solo.qualify(un, "m9")
        with self.assertRaises(ValueError):
            solo.convert(un, 5, "m9")
        # failed converts do not consume opp ids
        oid = self.c.convert(self.lid, 7, "m1")
        self.assertEqual(oid, "O1")
        self.assertEqual([e for e in self.c.log if e[0] == "convert"],
                         [("convert", "O1", "m1")])


if __name__ == "__main__":
    unittest.main()
