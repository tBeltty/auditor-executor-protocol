import unittest

from crm import CRM, DuplicateLeadError


def make_crm(capacity=5):
    return CRM(
        [
            {"id": "rep1", "role": "rep", "capacity": capacity},
            {"id": "rep2", "role": "rep", "capacity": capacity},
            {"id": "boss", "role": "manager", "capacity": 0},
        ]
    )


class Base(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()

    def assert_untouched(self):
        self.assertEqual(self.crm.leads, {})
        self.assertEqual(self.crm.opps, {})
        self.assertEqual(self.crm.log, [])
        self.assertEqual(self.crm.waiting, [])


class EmailValidationTest(Base):
    def assert_rejected(self, email):
        with self.assertRaises(ValueError):
            self.crm.add_lead(email, "Ana", "web", "rep1")
        self.assert_untouched()

    def test_non_string_email_rejected(self):
        for bad in (None, 123, 12.5, ["ana@example.com"], b"ana@example.com"):
            self.assert_rejected(bad)

    def test_missing_at_rejected(self):
        self.assert_rejected("ana.example.com")

    def test_multiple_at_rejected(self):
        for bad in ("ana@@example.com", "a@b@example.com", "ana@corp@example.com"):
            self.assert_rejected(bad)

    def test_empty_local_part_rejected(self):
        for bad in ("@example.com", "   @example.com", "@"):
            self.assert_rejected(bad)

    def test_empty_or_missing_domain_rejected(self):
        for bad in ("ana@", "ana@ "):
            self.assert_rejected(bad)

    def test_domain_without_dot_rejected(self):
        self.assert_rejected("ana@localhost")

    def test_dot_on_domain_edges_rejected(self):
        # crm.md:13 -- a domain whose only dot is its first or last character
        # has no interior dot, so it is invalid.
        for bad in ("ana@.com", "ana@example.", "ana@."):
            self.assert_rejected(bad)

    def test_interior_dot_is_what_the_spec_requires(self):
        # crm.md:13 asks for a dot that is "neither the first nor the last
        # character of the domain"; ".example.com" has one, so it is accepted
        # even though the dot at index 0 is not interior.
        lead_id = self.crm.add_lead("ana@.example.com", "Ana", "web", "rep1")
        self.assertEqual(self.crm.leads[lead_id]["email"], "ana@.example.com")
        self.assertEqual(self.crm.leads[lead_id]["score"], 25)

    def test_valid_email_stored_normalized(self):
        lead_id = self.crm.add_lead("  Ana.B+CRM@Sub.Example.COM  ", "Ana", "web", "rep1")
        self.assertEqual(self.crm.leads[lead_id]["email"], "ana.b+crm@sub.example.com")


class NameValidationTest(Base):
    def test_non_string_name_rejected(self):
        for bad in (None, 5, ["Ana"], b"Ana"):
            with self.assertRaises(ValueError):
                self.crm.add_lead("ana@example.com", bad, "web", "rep1")
            self.assert_untouched()

    def test_blank_name_rejected(self):
        for bad in ("", "   ", "\t\n"):
            with self.assertRaises(ValueError):
                self.crm.add_lead("ana@example.com", bad, "web", "rep1")
            self.assert_untouched()

    def test_name_is_stored_stripped(self):
        lead_id = self.crm.add_lead("ana@example.com", "  Ana Ruiz  ", "web", "rep1")
        self.assertEqual(self.crm.leads[lead_id]["name"], "Ana Ruiz")


class SourceValidationTest(Base):
    def test_unknown_source_rejected(self):
        for bad in ("ads", "WEB", "Web", "", None, 3, ["web"]):
            with self.assertRaises(ValueError):
                self.crm.add_lead("ana@example.com", "Ana", bad, "rep1")
            self.assert_untouched()

    def test_source_scores_for_free_domains(self):
        expected = {"web": 10, "referral": 30, "event": 20}
        for index, (source, score) in enumerate(expected.items()):
            crm = make_crm()
            lead_id = crm.add_lead("user%d@gmail.com" % index, "A", source, "rep1")
            self.assertEqual(crm.leads[lead_id]["score"], score)
            self.assertEqual(crm.leads[lead_id]["source"], source)

    def test_source_scores_include_domain_bonus(self):
        expected = {"web": 25, "referral": 45, "event": 35}
        for index, (source, score) in enumerate(expected.items()):
            crm = make_crm()
            lead_id = crm.add_lead("user%d@corp.io" % index, "A", source, "rep1")
            self.assertEqual(crm.leads[lead_id]["score"], score)

    def test_free_domains_are_exact_after_normalization(self):
        crm = make_crm()
        lead_id = crm.add_lead("ana@Gmail.COM", "A", "web", "rep1")
        self.assertEqual(crm.leads[lead_id]["score"], 10)
        other = crm.add_lead("bob@mail.gmail.com", "B", "web", "rep1")
        self.assertEqual(crm.leads[other]["score"], 25)


class DuplicateTest(Base):
    def test_duplicate_after_normalization(self):
        first = self.crm.add_lead("Ana@Example.com", "Ana", "web", "rep1")
        before = self.crm.log[:]
        with self.assertRaises(DuplicateLeadError) as caught:
            self.crm.add_lead("  ana@EXAMPLE.com ", "Other", "event", "rep2")
        self.assertEqual(caught.exception.existing_id, first)
        self.assertEqual(len(self.crm.leads), 1)
        self.assertEqual(self.crm.log, before)

    def test_duplicate_check_runs_after_source_validation(self):
        self.crm.add_lead("ana@example.com", "Ana", "web", "rep1")
        with self.assertRaises(ValueError):
            self.crm.add_lead("ana@example.com", "Ana", "podcast", "rep1")

    def test_duplicate_check_runs_after_name_validation(self):
        self.crm.add_lead("ana@example.com", "Ana", "web", "rep1")
        with self.assertRaises(ValueError):
            self.crm.add_lead("ana@example.com", "  ", "web", "rep1")

    def test_failed_duplicate_does_not_consume_an_id(self):
        self.crm.add_lead("ana@example.com", "Ana", "web", "rep1")
        with self.assertRaises(DuplicateLeadError):
            self.crm.add_lead("ana@example.com", "Ana", "web", "rep1")
        self.assertEqual(self.crm.add_lead("bob@example.com", "Bob", "web", "rep1"), "L2")

    def test_different_emails_are_not_duplicates(self):
        a = self.crm.add_lead("ana@example.com", "Ana", "web", "rep1")
        b = self.crm.add_lead("ana@example.org", "Ana", "web", "rep1")
        self.assertNotEqual(a, b)

    def test_duplicate_after_conversion(self):
        # A converted lead stays in crm.leads, so its email is still taken.
        first = self.crm.add_lead("ana@corp.io", "Ana", "referral", "rep1")
        self.crm.qualify(first, "rep1")
        self.crm.convert(first, 1000, "rep1")
        self.assertEqual(self.crm.leads[first]["status"], "converted")
        before = self.crm.log[:]
        with self.assertRaises(DuplicateLeadError) as caught:
            self.crm.add_lead("  ANA@Corp.IO ", "Ana", "web", "rep1")
        self.assertEqual(caught.exception.existing_id, first)
        self.assertEqual(len(self.crm.leads), 1)
        self.assertEqual(self.crm.log, before)


class UnhashableActorTest(unittest.TestCase):
    """crm.md:7 -- any actor that is not a known user id raises PermissionError.

    A list or dict is unhashable, so a naive ``actor not in self.users`` lookup
    raises TypeError instead.  The contract is PermissionError.
    """

    def setUp(self):
        self.crm = make_crm()
        self.lead_id = self.crm.add_lead("ana@corp.io", "Ana", "referral", "rep1")
        self.crm.qualify(self.lead_id, "rep1")
        self.opp_id = self.crm.convert(self.lead_id, 1000, "rep1")
        self.before = (
            dict(self.crm.leads),
            dict(self.crm.opps),
            list(self.crm.log),
            list(self.crm.waiting),
            self.crm._lead_seq,
            self.crm._opp_seq,
        )

    def assert_permission_error_and_no_change(self, call):
        with self.assertRaises(PermissionError):
            call()
        after = (
            dict(self.crm.leads),
            dict(self.crm.opps),
            list(self.crm.log),
            list(self.crm.waiting),
            self.crm._lead_seq,
            self.crm._opp_seq,
        )
        self.assertEqual(after, self.before)

    def test_unhashable_actor_rejected_by_every_method(self):
        for bad in ([], {}, set()):
            self.assert_permission_error_and_no_change(
                lambda bad=bad: self.crm.add_lead("x@corp.io", "X", "web", bad)
            )
            self.assert_permission_error_and_no_change(
                lambda bad=bad: self.crm.qualify(self.lead_id, bad)
            )
            self.assert_permission_error_and_no_change(
                lambda bad=bad: self.crm.convert(self.lead_id, 100, bad)
            )
            self.assert_permission_error_and_no_change(
                lambda bad=bad: self.crm.advance(self.opp_id, "proposal", bad)
            )
            self.assert_permission_error_and_no_change(
                lambda bad=bad: self.crm.discount(self.opp_id, 5, bad)
            )
            self.assert_permission_error_and_no_change(
                lambda bad=bad: self.crm.transfer(self.opp_id, "rep2", bad)
            )


class AddLeadShapeTest(Base):
    def test_lead_fields_and_log(self):
        lead_id = self.crm.add_lead("ana@corp.io", "  Ana  ", "referral", "rep1")
        self.assertEqual(lead_id, "L1")
        self.assertEqual(
            self.crm.leads[lead_id],
            {
                "id": "L1",
                "email": "ana@corp.io",
                "name": "Ana",
                "source": "referral",
                "score": 45,
                "owner": "rep1",
                "status": "new",
            },
        )
        self.assertEqual(self.crm.log, [("add_lead", "L1", "rep1")])

    def test_ids_increment_on_success_only(self):
        self.assertEqual(self.crm.add_lead("a@corp.io", "A", "web", "rep1"), "L1")
        with self.assertRaises(ValueError):
            self.crm.add_lead("bad", "A", "web", "rep1")
        self.assertEqual(self.crm.add_lead("b@corp.io", "B", "web", "rep1"), "L2")
        self.assertEqual(self.crm.add_lead("c@corp.io", "C", "web", "rep1"), "L3")


if __name__ == "__main__":
    unittest.main()
