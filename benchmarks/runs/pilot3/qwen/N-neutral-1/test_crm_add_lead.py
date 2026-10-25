"""Tests for CRM.add_lead: actor rule, validation order, score, duplicates."""

import unittest

from crm import CRM, DuplicateLeadError


def make_crm():
    return CRM([
        {"id": "r1", "role": "rep", "capacity": 5},
        {"id": "m1", "role": "manager", "capacity": 0},
    ])


class TestAddLeadBasics(unittest.TestCase):
    def test_returns_sequential_ids(self):
        crm = make_crm()
        self.assertEqual(crm.add_lead("a@acme.com", "Ann", "web", "r1"), "L1")
        self.assertEqual(crm.add_lead("b@acme.com", "Bob", "web", "r1"), "L2")
        self.assertEqual(crm.add_lead("c@acme.com", "Cy", "web", "r1"), "L3")

    def test_lead_record_shape(self):
        crm = make_crm()
        crm.add_lead("Ann@Acme.com", "  Ann Lee  ", "referral", "r1")
        lead = crm.leads["L1"]
        self.assertEqual(sorted(lead.keys()),
                         ["email", "id", "name", "owner", "score", "source", "status"])
        self.assertEqual(lead["id"], "L1")
        self.assertEqual(lead["email"], "ann@acme.com")  # stripped + lowered
        self.assertEqual(lead["name"], "Ann Lee")  # stripped
        self.assertEqual(lead["source"], "referral")
        self.assertEqual(lead["status"], "new")
        self.assertEqual(lead["score"], 45)

    def test_logs_add_lead(self):
        crm = make_crm()
        crm.add_lead("a@acme.com", "Ann", "web", "r1")
        self.assertEqual(crm.log, [("add_lead", "L1", "r1")])

    def test_failed_call_logs_nothing(self):
        crm = make_crm()
        crm.add_lead("a@acme.com", "Ann", "web", "r1")
        before = list(crm.log)
        with self.assertRaises(ValueError):
            crm.add_lead("bad-email", "Zoe", "web", "r1")
        self.assertEqual(crm.log, before)
        self.assertEqual(len(crm.leads), 1)


class TestActorRule(unittest.TestCase):
    def test_unknown_actor_is_permission_error(self):
        crm = make_crm()
        with self.assertRaises(PermissionError):
            crm.add_lead("a@acme.com", "Ann", "web", "ghost")
        with self.assertRaises(PermissionError):
            crm.qualify("L1", "ghost")
        with self.assertRaises(PermissionError):
            crm.convert("L1", 100, "ghost")
        with self.assertRaises(PermissionError):
            crm.advance("O1", "proposal", "ghost")
        with self.assertRaises(PermissionError):
            crm.discount("O1", 5, "ghost")
        with self.assertRaises(PermissionError):
            crm.transfer("O1", "r1", "ghost")

    def test_actor_checked_before_other_validation(self):
        # A garbage email from an unknown actor still raises PermissionError.
        crm = make_crm()
        with self.assertRaises(PermissionError):
            crm.add_lead("no-at-sign", "", "nonsense", "ghost")

    def test_manager_can_add(self):
        crm = make_crm()
        self.assertEqual(crm.add_lead("a@acme.com", "Ann", "web", "m1"), "L1")


class TestEmailValidation(unittest.TestCase):
    def cases(self):
        return [
            None, 123, 4.5, [], b"a@b.com",
            "a@b@c.com",        # two @
            "plainaddress",     # no @
            "",
            "@acme.com",        # empty local part
            "a@.com",           # dot first in domain
            "a@acme.",          # dot last in domain
            "a@com",            # no dot in domain
            "a@.",              # domain is a single dot
        ]

    def test_rejects(self):
        crm = make_crm()
        for bad in self.cases():
            with self.subTest(email=bad):
                with self.assertRaises(ValueError):
                    crm.add_lead(bad, "Ann", "web", "r1")
        self.assertEqual(crm.leads, {})

    def test_accepts(self):
        crm = make_crm()
        for good in ["a@b.co", "ann@acme.com", "  ANN@Sub.ACME.COM  ", "a@b.c.d"]:
            with self.subTest(email=good):
                crm.add_lead(good, "Ann", "web", "r1")
        self.assertEqual(crm.leads["L1"]["email"], "a@b.co")
        self.assertEqual(crm.leads["L3"]["email"], "ann@sub.acme.com")

    def test_counter_not_consumed_by_invalid_email(self):
        crm = make_crm()
        with self.assertRaises(ValueError):
            crm.add_lead("nope", "Ann", "web", "r1")
        self.assertEqual(crm.add_lead("a@acme.com", "Ann", "web", "r1"), "L1")


class TestNameValidation(unittest.TestCase):
    def test_rejects(self):
        crm = make_crm()
        for bad in [None, 5, "", "   ", "\t\n", []]:
            with self.subTest(name=bad):
                with self.assertRaises(ValueError):
                    crm.add_lead("a@acme.com", bad, "web", "r1")
        self.assertEqual(crm.leads, {})

    def test_email_validated_before_name(self):
        crm = make_crm()
        # both bad -> ValueError either way, but counter must not move
        with self.assertRaises(ValueError):
            crm.add_lead("bad", "", "web", "r1")
        self.assertEqual(crm.add_lead("a@acme.com", "Ann", "web", "r1"), "L1")


class TestSourceValidation(unittest.TestCase):
    def test_rejects(self):
        crm = make_crm()
        for bad in ["WEB", "phone", "", None, 0, "web "]:
            with self.subTest(source=bad):
                with self.assertRaises(ValueError):
                    crm.add_lead("a@acme.com", "Ann", bad, "r1")
        self.assertEqual(crm.leads, {})

    def test_accepts_the_three(self):
        crm = make_crm()
        for i, src in enumerate(["web", "referral", "event"], start=1):
            crm.add_lead("a%d@acme.com" % i, "N", src, "r1")
        self.assertEqual(len(crm.leads), 3)


class TestScore(unittest.TestCase):
    def test_base_and_domain_bonus(self):
        crm = make_crm()
        expectations = [
            ("web", "gmail.com", 10),
            ("referral", "yahoo.com", 30),
            ("event", "outlook.com", 20),
            ("web", "acme.com", 25),
            ("referral", "acme.com", 45),
            ("event", "acme.com", 35),
        ]
        for i, (src, domain, score) in enumerate(expectations, start=1):
            lead_id = crm.add_lead("u%d@%s" % (i, domain), "N", src, "r1")
            self.assertEqual(crm.leads[lead_id]["score"], score, (src, domain))

    def test_free_domain_check_is_lowered(self):
        crm = make_crm()
        lead_id = crm.add_lead("ann@GMAIL.com", "Ann", "web", "r1")
        self.assertEqual(crm.leads[lead_id]["score"], 10)
        lead_id = crm.add_lead("ann@acme.com", "Ann", "web", "r1")
        self.assertEqual(crm.leads[lead_id]["score"], 25)


class TestDuplicates(unittest.TestCase):
    def test_second_email_raises_with_existing_id(self):
        crm = make_crm()
        crm.add_lead("ann@acme.com", "Ann", "web", "r1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            crm.add_lead("ann@acme.com", "Other", "event", "r1")
        self.assertEqual(ctx.exception.existing_id, "L1")

    def test_duplicate_detection_uses_normalized_form(self):
        crm = make_crm()
        crm.add_lead("ann@acme.com", "Ann", "web", "r1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            crm.add_lead("  ANN@ACME.COM ", "Other", "web", "r1")
        self.assertEqual(ctx.exception.existing_id, "L1")

    def test_duplicate_after_conversion_still_duplicate(self):
        crm = make_crm()
        crm.add_lead("ann@acme.com", "Ann", "referral", "r1")
        crm.qualify("L1", "r1")
        crm.convert("L1", 1000, "r1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            crm.add_lead("ann@acme.com", "Ann again", "web", "r1")
        self.assertEqual(ctx.exception.existing_id, "L1")

    def test_duplicate_changes_nothing(self):
        crm = make_crm()
        crm.add_lead("ann@acme.com", "Ann", "web", "r1")
        snapshot_log = list(crm.log)
        snapshot = dict(crm.leads["L1"])
        with self.assertRaises(DuplicateLeadError):
            crm.add_lead("ann@acme.com", "Bigger", "referral", "r1")
        self.assertEqual(crm.log, snapshot_log)
        self.assertEqual(crm.leads["L1"], snapshot)
        self.assertEqual(len(crm.leads), 1)

    def test_validation_order_beats_duplicate(self):
        # source is checked (rule 3) before the duplicate check (rule 4)
        crm = make_crm()
        crm.add_lead("ann@acme.com", "Ann", "web", "r1")
        with self.assertRaises(ValueError):
            crm.add_lead("ann@acme.com", "Ann", "telephone", "r1")

    def test_is_an_exception(self):
        self.assertTrue(issubclass(DuplicateLeadError, Exception))


if __name__ == "__main__":
    unittest.main()
