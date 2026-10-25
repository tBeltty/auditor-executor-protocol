"""Tests for CRM lead intake, routing, qualifying and converting."""

import unittest

from crm import CRM, DuplicateLeadError


def fresh_crm():
    return CRM([
        {"id": "r1", "role": "rep", "capacity": 2},
        {"id": "r2", "role": "rep", "capacity": 2},
        {"id": "m1", "role": "manager", "capacity": 9},
    ])


class TestUnknownActor(unittest.TestCase):
    def test_every_method_checks_actor_first(self):
        crm = fresh_crm()
        lid = crm.add_lead("a@acme.com", "A", "referral", "r1")
        crm.qualify(lid, "r1")
        oid = crm.convert(lid, 1000, "r1")
        log_before = list(crm.log)
        calls = [
            lambda: crm.add_lead("b@acme.com", "B", "web", "ghost"),
            lambda: crm.qualify(lid, "ghost"),
            lambda: crm.convert(lid, 1000, "ghost"),
            lambda: crm.advance(oid, "proposal", "ghost"),
            lambda: crm.discount(oid, 5, "ghost"),
            lambda: crm.transfer(oid, "r2", "ghost"),
        ]
        for call in calls:
            with self.assertRaises(PermissionError):
                call()
        self.assertEqual(crm.log, log_before)


class TestAddLead(unittest.TestCase):
    def setUp(self):
        self.crm = fresh_crm()

    def test_happy_path(self):
        lid = self.crm.add_lead("Alice@Acme.com", "  Alice  ", "referral", "m1")
        self.assertEqual(lid, "L1")
        lead = self.crm.leads[lid]
        self.assertEqual(lead["id"], "L1")
        self.assertEqual(lead["email"], "alice@acme.com")
        self.assertEqual(lead["name"], "Alice")
        self.assertEqual(lead["source"], "referral")
        self.assertEqual(lead["score"], 45)  # 30 + 15 corporate domain
        self.assertIn(lead["owner"], ("r1", "r2"))
        self.assertEqual(lead["status"], "new")
        self.assertEqual(self.crm.log, [("add_lead", "L1", "m1")])

    def test_scores(self):
        cases = [
            ("web", "gmail.com", 10),
            ("web", "acme.com", 25),
            ("referral", "yahoo.com", 30),
            ("referral", "acme.com", 45),
            ("event", "outlook.com", 20),
            ("event", "corp.co.uk", 35),
        ]
        for i, (source, domain, score) in enumerate(cases, 1):
            lid = self.crm.add_lead("p%d@%s" % (i, domain), "P", source, "r1")
            self.assertEqual(self.crm.leads[lid]["score"], score)
            self.assertEqual(lid, "L%d" % i)

    def test_email_must_be_str(self):
        for bad in (123, None, True, ["a@b.com"]):
            with self.assertRaises(ValueError):
                self.crm.add_lead(bad, "A", "web", "r1")
        self.assertEqual(self.crm.leads, {})
        self.assertEqual(self.crm.log, [])

    def test_invalid_emails(self):
        bad_emails = [
            "plainaddress",       # no @
            "",                   # empty
            "   ",                # whitespace only
            "a@@acme.com",        # two @
            "@acme.com",          # empty local part
            "a@",                 # empty domain
            "a@bcom",             # domain without dot
            "a@.com",             # dot first in domain
            "a@b.",               # dot last in domain
            "a@.",                # domain is only a dot
        ]
        for bad in bad_emails:
            with self.assertRaises(ValueError):
                self.crm.add_lead(bad, "A", "web", "r1")
        self.assertEqual(self.crm.log, [])

    def test_valid_edge_emails(self):
        for good in ("a@b.co", "x.y@sub.acme.com", "A@B.COMPANY", " a@b.com "):
            self.crm.add_lead(good, "N", "web", "r1")
        emails = [l["email"] for l in self.crm.leads.values()]
        self.assertEqual(
            emails, ["a@b.co", "x.y@sub.acme.com", "a@b.company", "a@b.com"]
        )

    def test_name_must_be_nonempty_str(self):
        for bad in ("", "   ", "\t\n", 42, None):
            with self.assertRaises(ValueError):
                self.crm.add_lead("a@acme.com", bad, "web", "r1")

    def test_source_must_be_known(self):
        for bad in ("phone", "Web", "", None, 3):
            with self.assertRaises(ValueError):
                self.crm.add_lead("a@acme.com", "A", bad, "r1")

    def test_duplicate_email_raises_with_existing_id(self):
        lid1 = self.crm.add_lead("a@acme.com", "First", "web", "r1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            self.crm.add_lead("  A@ACME.com ", "Second", "referral", "r1")
        self.assertEqual(ctx.exception.existing_id, lid1)
        self.assertEqual(len(self.crm.leads), 1)
        self.assertEqual(self.crm.log, [("add_lead", "L1", "r1")])

    def test_duplicate_is_exception_not_valueerror(self):
        self.crm.add_lead("a@acme.com", "A", "web", "r1")
        with self.assertRaises(DuplicateLeadError):
            self.crm.add_lead("a@acme.com", "A", "web", "r1")
        self.assertTrue(issubclass(DuplicateLeadError, Exception))

    def test_failed_add_does_not_consume_id(self):
        with self.assertRaises(ValueError):
            self.crm.add_lead("bad", "A", "web", "r1")
        lid = self.crm.add_lead("a@acme.com", "A", "web", "r1")
        self.assertEqual(lid, "L1")

    def test_invalid_email_wins_over_duplicate(self):
        # email validation (check 1) runs before the duplicate check (4)
        self.crm.add_lead("a@acme.com", "A", "web", "r1")
        with self.assertRaises(ValueError):
            self.crm.add_lead("a@acme.com@", "A", "web", "r1")


class TestRouting(unittest.TestCase):
    def test_lowest_load_wins(self):
        crm = CRM([
            {"id": "ra", "role": "rep", "capacity": 2},
            {"id": "rb", "role": "rep", "capacity": 2},
            {"id": "mm", "role": "manager", "capacity": 5},
        ])
        l1 = crm.add_lead("a@x.com", "A", "web", "mm")
        owner1 = crm.leads[l1]["owner"]  # tie at load 0 -> smallest id: "ra"
        self.assertEqual(owner1, "ra")
        l2 = crm.add_lead("b@x.com", "B", "web", "mm")
        owner2 = crm.leads[l2]["owner"]
        self.assertEqual(owner2, "rb")  # ra load 1, rb load 0 -> lowest wins
        l3 = crm.add_lead("c@x.com", "C", "web", "mm")
        self.assertEqual(crm.leads[l3]["owner"], owner1)  # tie again -> "ra"

    def test_ties_smallest_id_string_order(self):
        crm = CRM([
            {"id": "r9", "role": "rep", "capacity": 1},
            {"id": "r10", "role": "rep", "capacity": 1},
        ])
        l1 = crm.add_lead("a@x.com", "A", "web", "r9")
        self.assertEqual(crm.leads[l1]["owner"], "r10")  # "r10" < "r9"

    def test_managers_never_own(self):
        crm = CRM([
            {"id": "zz", "role": "rep", "capacity": 1},
            {"id": "aa", "role": "manager", "capacity": 100},
        ])
        l1 = crm.add_lead("a@x.com", "A", "web", "aa")
        self.assertEqual(crm.leads[l1]["owner"], "zz")

    def test_zero_capacity_rep_skipped(self):
        crm = CRM([
            {"id": "a0", "role": "rep", "capacity": 0},
            {"id": "b5", "role": "rep", "capacity": 5},
        ])
        lid = crm.add_lead("a@x.com", "A", "web", "b5")
        self.assertEqual(crm.leads[lid]["owner"], "b5")

    def test_all_full_joins_waiting_queue(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1}])
        l1 = crm.add_lead("a@x.com", "A", "web", "r1")
        l2 = crm.add_lead("b@x.com", "B", "web", "r1")
        self.assertEqual(crm.leads[l1]["owner"], "r1")
        self.assertIsNone(crm.leads[l2]["owner"])
        self.assertEqual(crm.log, [
            ("add_lead", "L1", "r1"),
            ("add_lead", "L2", "r1"),
        ])  # queued lead logs no assignment

    def test_no_reps_all_wait(self):
        crm = CRM([{"id": "m", "role": "manager", "capacity": 3}])
        lid = crm.add_lead("a@x.com", "A", "web", "m")
        self.assertIsNone(crm.leads[lid]["owner"])


class TestQualify(unittest.TestCase):
    def setUp(self):
        self.crm = fresh_crm()
        self.lid = self.crm.add_lead("a@acme.com", "A", "referral", "r1")
        self.owner = self.crm.leads[self.lid]["owner"]

    def test_happy_path(self):
        self.crm.qualify(self.lid, self.owner)
        self.assertEqual(self.crm.leads[self.lid]["status"], "qualified")
        self.assertEqual(self.crm.log, [
            ("add_lead", "L1", "r1"),
            ("qualify", self.lid, self.owner),
        ])

    def test_manager_can_qualify_any_lead(self):
        self.crm.qualify(self.lid, "m1")
        self.assertEqual(self.crm.leads[self.lid]["status"], "qualified")

    def test_other_rep_denied(self):
        other = "r2" if self.owner == "r1" else "r1"
        with self.assertRaises(PermissionError):
            self.crm.qualify(self.lid, other)
        self.assertEqual(self.crm.leads[self.lid]["status"], "new")
        self.assertEqual(len(self.crm.log), 1)

    def test_unknown_lead_value_error(self):
        with self.assertRaises(ValueError):
            self.crm.qualify("L99", self.owner)

    def test_status_must_be_new(self):
        self.crm.qualify(self.lid, self.owner)
        with self.assertRaises(ValueError):
            self.crm.qualify(self.lid, self.owner)

    def test_score_below_30_denied(self):
        lid = self.crm.add_lead("b@gmail.com", "B", "web", "m1")  # score 10
        with self.assertRaises(ValueError):
            self.crm.qualify(lid, "m1")
        # exactly 30 is allowed
        lid2 = self.crm.add_lead("c@gmail.com", "C", "referral", "m1")  # 30
        self.crm.qualify(lid2, "m1")
        self.assertEqual(self.crm.leads[lid2]["status"], "qualified")

    def test_permission_checked_before_status_and_score(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 1},
            {"id": "m", "role": "manager", "capacity": 3},
        ])
        low = crm.add_lead("d@gmail.com", "D", "web", "m")  # owner r1, score 10
        self.assertEqual(crm.leads[low]["owner"], "r1")
        # r2 is not the owner: PermissionError beats the score ValueError
        with self.assertRaises(PermissionError):
            crm.qualify(low, "r2")
        good = crm.add_lead("e@acme.com", "E", "referral", "m")  # owner r2
        self.assertEqual(crm.leads[good]["owner"], "r2")
        crm.qualify(good, "m")  # now status is qualified
        # r1 is not the owner of `good`: PermissionError beats the status ValueError
        with self.assertRaises(PermissionError):
            crm.qualify(good, "r1")

    def test_waiting_lead_only_manager(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 0}])
        lid = crm.add_lead("a@x.com", "A", "referral", "r1")
        lid = lid  # owner None
        with self.assertRaises(PermissionError):
            crm.qualify(lid, "r1")  # actor "r1" is a rep, not owner(None)


class TestConvert(unittest.TestCase):
    def setUp(self):
        self.crm = fresh_crm()
        self.lid = self.crm.add_lead("a@acme.com", "A", "referral", "r1")
        self.owner = self.crm.leads[self.lid]["owner"]
        self.crm.qualify(self.lid, self.owner)

    def test_happy_path(self):
        oid = self.crm.convert(self.lid, 1500, self.owner)
        self.assertEqual(oid, "O1")
        opp = self.crm.opps[oid]
        self.assertEqual(opp, {
            "id": "O1",
            "lead_id": self.lid,
            "owner": self.owner,
            "amount": 1500,
            "original_amount": 1500,
            "stage": "prospect",
        })
        self.assertEqual(self.crm.leads[self.lid]["status"], "converted")
        self.assertEqual(self.crm.log[-1], ("convert", "O1", self.owner))

    def test_manager_converts_keeping_rep_owner(self):
        oid = self.crm.convert(self.lid, 500, "m1")
        self.assertEqual(self.crm.opps[oid]["owner"], self.owner)

    def test_bad_amount(self):
        for bad in (0, -5, 1.5, "100", None, True, False):
            with self.assertRaises(ValueError):
                self.crm.convert(self.lid, bad, self.owner)
        self.assertEqual(self.crm.opps, {})
        self.assertEqual(len(self.crm.log), 2)

    def test_lead_must_exist(self):
        with self.assertRaises(ValueError):
            self.crm.convert("L42", 100, self.owner)

    def test_not_owner_denied(self):
        other = "r2" if self.owner == "r1" else "r1"
        with self.assertRaises(PermissionError):
            self.crm.convert(self.lid, 100, other)

    def test_amount_checked_before_actor(self):
        other = "r2" if self.owner == "r1" else "r1"
        with self.assertRaises(ValueError):  # not PermissionError
            self.crm.convert(self.lid, 0, other)

    def test_status_must_be_qualified(self):
        lid = self.crm.add_lead("z@acme.com", "Z", "referral", "m1")
        with self.assertRaises(ValueError):
            self.crm.convert(lid, 100, "m1")

    def test_lead_must_have_owner(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 0},
            {"id": "m", "role": "manager", "capacity": 5},
        ])
        lid = crm.add_lead("a@x.com", "A", "referral", "m")
        crm.qualify(lid, "m")  # manager may qualify unowned lead
        with self.assertRaises(ValueError):
            crm.convert(lid, 100, "m")  # but no owner to convert for

    def test_failed_convert_does_not_consume_opp_id(self):
        with self.assertRaises(ValueError):
            self.crm.convert(self.lid, -1, self.owner)
        oid = self.crm.convert(self.lid, 100, self.owner)
        self.assertEqual(oid, "O1")


if __name__ == "__main__":
    unittest.main()
