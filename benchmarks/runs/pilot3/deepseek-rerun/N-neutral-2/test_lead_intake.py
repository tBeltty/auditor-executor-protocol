import unittest

from crm import CRM, DuplicateLeadError


def make_crm():
    return CRM(
        [
            {"id": "r1", "role": "rep", "capacity": 2},
            {"id": "r2", "role": "rep", "capacity": 2},
            {"id": "m1", "role": "manager", "capacity": 5},
        ]
    )


class AddLeadValidationTests(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()

    def test_actor_checked_before_everything_else(self):
        with self.assertRaises(PermissionError):
            self.crm.add_lead(None, None, None, "ghost")
        self.assertEqual(self.crm.leads, {})
        self.assertEqual(self.crm.log, [])

    def test_email_must_be_string(self):
        for bad in (None, 5, ["a@b.co"]):
            with self.assertRaises(ValueError):
                self.crm.add_lead(bad, "Name", "web", "r1")

    def test_email_shape(self):
        bad_emails = [
            "plain",
            "a@@b.co",
            "two@at@b.co",
            "@b.co",
            "a@",
            "a@bco",
            "a@.co",
            "a@bco.",
            "a@.co.",
        ]
        for bad in bad_emails:
            with self.assertRaises(ValueError, msg=bad):
                self.crm.add_lead(bad, "Name", "web", "r1")
        self.assertEqual(self.crm.leads, {})

    def test_email_with_internal_dot_is_accepted(self):
        for good in ("a@b.co", "a@sub.b.co", "a@b.c.d"):
            lead_id = self.crm.add_lead(good, "Name", "web", "r1")
            self.assertEqual(self.crm.leads[lead_id]["email"], good)

    def test_name_validation(self):
        for bad in (None, 3, "", "   ", "\t\n"):
            with self.assertRaises(ValueError, msg=repr(bad)):
                self.crm.add_lead("a@b.co", bad, "web", "r1")

    def test_name_is_stripped(self):
        lead_id = self.crm.add_lead("a@b.co", "  Ada  ", "web", "r1")
        self.assertEqual(self.crm.leads[lead_id]["name"], "Ada")

    def test_source_validation(self):
        for bad in ("ad", "WEB", "", None, 1):
            with self.assertRaises(ValueError, msg=repr(bad)):
                self.crm.add_lead("a@b.co", "Ada", bad, "r1")

    def test_source_order_is_checked_after_name(self):
        with self.assertRaises(ValueError):
            self.crm.add_lead("a@b.co", "", "nope", "r1")
        self.assertEqual(self.crm.log, [])

    def test_duplicate_email_raises_with_existing_id(self):
        lead_id = self.crm.add_lead("Ada@Example.com ", "Ada", "web", "r1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            self.crm.add_lead(" ada@example.COM", "Other", "event", "r1")
        self.assertEqual(ctx.exception.existing_id, lead_id)
        self.assertEqual(len(self.crm.leads), 1)
        self.assertEqual(len(self.crm.log), 1)

    def test_duplicate_also_detected_for_converted_leads(self):
        lead_id = self.crm.add_lead("ada@corp.com", "Ada", "referral", "r1")
        self.crm.qualify(lead_id, "r1")
        self.crm.convert(lead_id, 1000, "r1")
        with self.assertRaises(DuplicateLeadError):
            self.crm.add_lead("ada@corp.com", "Ada", "referral", "r1")

    def test_normalized_email_and_lead_fields(self):
        lead_id = self.crm.add_lead("  Ada@Corp.COM ", " Ada Lovelace ", "referral", "r1")
        self.assertEqual(lead_id, "L1")
        self.assertEqual(
            self.crm.leads[lead_id],
            {
                "id": "L1",
                "email": "ada@corp.com",
                "name": "Ada Lovelace",
                "source": "referral",
                "score": 45,
                "owner": "r1",
                "status": "new",
            },
        )
        self.assertEqual(self.crm.log, [("add_lead", "L1", "r1")])


class ScoringTests(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()

    def score(self, email, source):
        lead_id = self.crm.add_lead(email, "N", source, "m1")
        return self.crm.leads[lead_id]["score"]

    def test_base_scores(self):
        self.assertEqual(self.score("a@gmail.com", "web"), 10)
        self.assertEqual(self.score("b@gmail.com", "event"), 20)
        self.assertEqual(self.score("c@gmail.com", "referral"), 30)

    def test_free_domains_do_not_add_bonus(self):
        for domain in ("gmail.com", "yahoo.com", "outlook.com"):
            self.assertEqual(self.score("x@%s" % domain, "web"), 10)

    def test_other_domains_add_fifteen(self):
        self.assertEqual(self.score("x@corp.com", "web"), 25)
        self.assertEqual(self.score("x@yahoo.co.uk", "event"), 35)
        self.assertEqual(self.score("x@notgmail.com", "referral"), 45)


class LeadIdAndAssignmentTests(unittest.TestCase):
    def test_ids_increment_only_on_success(self):
        crm = make_crm()
        self.assertEqual(crm.add_lead("a@a.com", "A", "web", "r1"), "L1")
        with self.assertRaises(ValueError):
            crm.add_lead("bad", "B", "web", "r1")
        self.assertEqual(crm.add_lead("b@b.com", "B", "web", "r1"), "L2")

    def test_lowest_load_and_tie_break(self):
        crm = make_crm()
        l1 = crm.add_lead("a@a.com", "A", "web", "r1")
        l2 = crm.add_lead("b@b.com", "B", "web", "r1")
        l3 = crm.add_lead("c@c.com", "C", "web", "r1")
        l4 = crm.add_lead("d@d.com", "D", "web", "r1")
        self.assertEqual([crm.leads[i]["owner"] for i in (l1, l2, l3, l4)],
                         ["r1", "r2", "r1", "r2"])

    def test_managers_never_receive_leads(self):
        crm = CRM([{"id": "m1", "role": "manager", "capacity": 10}])
        lead_id = crm.add_lead("a@a.com", "A", "web", "m1")
        self.assertIsNone(crm.leads[lead_id]["owner"])

    def test_queue_when_all_reps_full(self):
        crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 1},
                {"id": "m1", "role": "manager", "capacity": 9},
            ]
        )
        first = crm.add_lead("a@a.com", "A", "web", "r1")
        waiting = crm.add_lead("b@b.com", "B", "web", "m1")
        self.assertEqual(crm.leads[first]["owner"], "r1")
        self.assertIsNone(crm.leads[waiting]["owner"])
        self.assertEqual(crm.log[-1], ("add_lead", waiting, "m1"))

    def test_assign_logged_with_system_actor(self):
        crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 1},
                {"id": "m1", "role": "manager", "capacity": 9},
            ]
        )
        first = crm.add_lead("a@corp.com", "A", "referral", "r1")
        waiting = crm.add_lead("b@corp.com", "B", "web", "r1")
        crm.qualify(first, "r1")
        opp = crm.convert(first, 100, "r1")
        crm.advance(opp, "proposal", "r1")
        crm.advance(opp, "negotiation", "r1")
        crm.advance(opp, "won", "r1")
        self.assertEqual(crm.leads[waiting]["owner"], "r1")
        self.assertEqual(crm.log[-1], ("assign", waiting, "system"))

    def test_queue_is_fifo(self):
        crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 1},
                {"id": "m1", "role": "manager", "capacity": 9},
            ]
        )
        lead = crm.add_lead("a@corp.com", "A", "referral", "r1")
        w1 = crm.add_lead("b@corp.com", "B", "web", "r1")
        w2 = crm.add_lead("c@corp.com", "C", "web", "r1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 100, "r1")
        crm.advance(opp, "lost", "r1")
        self.assertEqual(crm.leads[w1]["owner"], "r1")
        self.assertIsNone(crm.leads[w2]["owner"])


if __name__ == "__main__":
    unittest.main()
