import unittest

from crm import CRM, DuplicateLeadError


def make_reps():
    return [
        {"id": "r1", "role": "rep", "capacity": 2},
        {"id": "r2", "role": "rep", "capacity": 2},
        {"id": "m1", "role": "manager", "capacity": 0},
    ]


class TestCheckOrdering(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(make_reps())

    def test_unknown_actor_is_checked_first_in_add_lead(self):
        with self.assertRaises(PermissionError):
            self.crm.add_lead(123, "", "bogus", "ghost")
        self.assertEqual(self.crm.leads, {})
        self.assertEqual(self.crm.log, [])

    def test_unknown_actor_is_checked_first_in_qualify(self):
        with self.assertRaises(PermissionError):
            self.crm.qualify("L404", "ghost")

    def test_unknown_actor_is_checked_first_in_convert(self):
        with self.assertRaises(PermissionError):
            self.crm.convert("L404", 0, "ghost")

    def test_unknown_actor_is_checked_first_in_advance(self):
        with self.assertRaises(PermissionError):
            self.crm.advance("O404", "bogus", "ghost")

    def test_unknown_actor_is_checked_first_in_discount(self):
        with self.assertRaises(PermissionError):
            self.crm.discount("O404", 99, "ghost")

    def test_unknown_actor_is_checked_first_in_transfer(self):
        with self.assertRaises(PermissionError):
            self.crm.transfer("O404", "nobody", "ghost")

    def test_add_lead_email_checked_before_name_and_source(self):
        # All three are invalid; the email check (rule 1) must win.
        with self.assertRaises(ValueError):
            self.crm.add_lead("bad", "", "bogus", "m1")
        self.assertEqual(self.crm.leads, {})

    def test_convert_amount_checked_before_permission(self):
        lead = self.crm.add_lead("a@corp.com", "A", "referral", "m1")
        self.crm.qualify(lead, "m1")
        with self.assertRaises(ValueError):
            self.crm.convert(lead, 0, "r2")

    def test_advance_stage_checked_before_permission(self):
        lead = self.crm.add_lead("a@corp.com", "A", "referral", "m1")
        self.crm.qualify(lead, "m1")
        opp = self.crm.convert(lead, 100, "m1")
        with self.assertRaises(ValueError):
            self.crm.advance(opp, "bogus", "r2")

    def test_discount_pct_checked_before_permission(self):
        lead = self.crm.add_lead("a@corp.com", "A", "referral", "m1")
        self.crm.qualify(lead, "m1")
        opp = self.crm.convert(lead, 100, "m1")
        with self.assertRaises(ValueError):
            self.crm.discount(opp, 0, "r2")

    def test_qualify_permission_checked_before_status(self):
        lead = self.crm.add_lead("a@corp.com", "A", "referral", "m1")
        self.crm.qualify(lead, "m1")
        # Lead is no longer "new"; a non-owner must still get PermissionError.
        with self.assertRaises(PermissionError):
            self.crm.qualify(lead, "r2")

    def test_discount_stage_checked_before_rep_limit(self):
        lead = self.crm.add_lead("a@corp.com", "A", "referral", "m1")
        self.crm.qualify(lead, "m1")
        opp = self.crm.convert(lead, 100, "m1")
        self.crm.advance(opp, "lost", "m1")
        # Rule 4 (final) precedes rule 5 (rep limit); both are Value/Permission,
        # so assert the stage rule wins by requiring ValueError.
        with self.assertRaises(ValueError):
            self.crm.discount(opp, 30, "r1")


class TestAtomicity(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(make_reps())

    def test_failed_lead_does_not_consume_id(self):
        with self.assertRaises(ValueError):
            self.crm.add_lead("bad", "A", "web", "m1")
        first = self.crm.add_lead("a@corp.com", "A", "web", "m1")
        self.assertEqual(first, "L1")

        with self.assertRaises(DuplicateLeadError):
            self.crm.add_lead("A@CORP.com", "A", "web", "m1")

        second = self.crm.add_lead("b@corp.com", "B", "web", "m1")
        self.assertEqual(second, "L2")

    def test_failed_convert_does_not_consume_id(self):
        lead1 = self.crm.add_lead("a@corp.com", "A", "referral", "m1")
        self.crm.qualify(lead1, "m1")
        with self.assertRaises(ValueError):
            self.crm.convert(lead1, True, "m1")
        self.assertEqual(self.crm.convert(lead1, 100, "m1"), "O1")

        lead2 = self.crm.add_lead("b@corp.com", "B", "referral", "m1")
        self.crm.qualify(lead2, "m1")
        self.assertEqual(self.crm.convert(lead2, 100, "m1"), "O2")

    def test_failed_discount_leaves_log_and_amount(self):
        lead = self.crm.add_lead("a@corp.com", "A", "referral", "m1")
        self.crm.qualify(lead, "m1")
        opp = self.crm.convert(lead, 1000, "m1")
        self.crm.discount(opp, 30, "m1")
        log_before = list(self.crm.log)
        with self.assertRaises(ValueError):
            self.crm.discount(opp, 5, "m1")
        self.assertEqual(self.crm.opps[opp]["amount"], 700)
        self.assertEqual(self.crm.log, log_before)

    def test_failed_advance_leaves_state(self):
        lead = self.crm.add_lead("a@corp.com", "A", "referral", "m1")
        self.crm.qualify(lead, "m1")
        opp = self.crm.convert(lead, 60000, "m1")
        self.crm.advance(opp, "proposal", "m1")
        log_before = list(self.crm.log)
        with self.assertRaises(PermissionError):
            self.crm.advance(opp, "negotiation", "r1")
        self.assertEqual(self.crm.opps[opp]["stage"], "proposal")
        self.assertEqual(self.crm.log, log_before)

    def test_failed_transfer_leaves_state(self):
        lead = self.crm.add_lead("a@corp.com", "A", "referral", "m1")
        self.crm.qualify(lead, "m1")
        opp = self.crm.convert(lead, 100, "m1")
        log_before = list(self.crm.log)
        with self.assertRaises(ValueError):
            self.crm.transfer(opp, "m1", "m1")
        self.assertEqual(self.crm.opps[opp]["owner"], "r1")
        self.assertEqual(self.crm.log, log_before)

    def test_failed_qualify_leaves_state(self):
        lead = self.crm.add_lead("a@corp.com", "A", "web", "m1")
        log_before = list(self.crm.log)
        with self.assertRaises(ValueError):
            self.crm.qualify(lead, "m1")
        self.assertEqual(self.crm.leads[lead]["status"], "new")
        self.assertEqual(self.crm.log, log_before)


class TestOddInputs(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(make_reps())
        self.lead = self.crm.add_lead("a@corp.com", "A", "referral", "m1")
        self.crm.qualify(self.lead, "m1")
        self.opp = self.crm.convert(self.lead, 100, "m1")

    def test_unhashable_or_non_string_lead_ids_are_value_errors(self):
        for lead_id in [[], {}, 5, None, 1.5]:
            with self.subTest(lead_id=lead_id):
                with self.assertRaises(ValueError):
                    self.crm.qualify(lead_id, "m1")
                with self.assertRaises(ValueError):
                    self.crm.convert(lead_id, 10, "m1")

    def test_non_string_opportunity_ids_are_value_errors(self):
        for opp_id in [[], {}, 5, None, 1.5]:
            with self.subTest(opp_id=opp_id):
                with self.assertRaises(ValueError):
                    self.crm.advance(opp_id, "proposal", "m1")
                with self.assertRaises(ValueError):
                    self.crm.discount(opp_id, 5, "m1")
                with self.assertRaises(ValueError):
                    self.crm.transfer(opp_id, "r2", "m1")

    def test_non_string_source_is_value_error(self):
        for source in [[], {}, 5, None, 1.5]:
            with self.subTest(source=source):
                with self.assertRaises(ValueError):
                    self.crm.add_lead("b@corp.com", "B", source, "m1")

    def test_log_entries_are_triples_of_strings(self):
        for entry in self.crm.log:
            self.assertIsInstance(entry, tuple)
            self.assertEqual(len(entry), 3)
            for part in entry:
                self.assertIsInstance(part, str)


class TestTransitionTable(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(make_reps())

    def make_opp(self, amount=1000):
        lead = self.crm.add_lead("x@corp.com", "X", "referral", "m1")
        self.crm.qualify(lead, "m1")
        return self.crm.convert(lead, amount, "m1")

    def test_every_disallowed_transition_from_each_open_stage(self):
        stages = ["prospect", "proposal", "negotiation", "won", "lost"]
        paths = {
            "prospect": [],
            "proposal": ["proposal"],
            "negotiation": ["proposal", "negotiation"],
        }
        allowed_from = {
            "prospect": {"proposal", "lost"},
            "proposal": {"negotiation", "lost"},
            "negotiation": {"won", "lost"},
        }
        for start, steps in paths.items():
            for target in stages:
                with self.subTest(start=start, target=target):
                    crm = CRM(make_reps())
                    lead = crm.add_lead("x@corp.com", "X", "referral", "m1")
                    crm.qualify(lead, "m1")
                    opp = crm.convert(lead, 100, "m1")
                    for step in steps:
                        crm.advance(opp, step, "m1")
                    if target in allowed_from[start]:
                        crm.advance(opp, target, "m1")
                        self.assertEqual(crm.opps[opp]["stage"], target)
                    else:
                        with self.assertRaises(ValueError):
                            crm.advance(opp, target, "m1")
                        self.assertEqual(crm.opps[opp]["stage"], start)

    def test_loss_frees_slot_and_assigns_fifo(self):
        crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 1},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        lead = crm.add_lead("a@corp.com", "A", "referral", "m1")
        crm.qualify(lead, "m1")
        opp = crm.convert(lead, 100, "m1")
        first = crm.add_lead("b@corp.com", "B", "referral", "m1")
        second = crm.add_lead("c@corp.com", "C", "referral", "m1")
        self.assertEqual(crm.waiting, [first, second])

        crm.advance(opp, "lost", "m1")

        self.assertEqual(crm.leads[first]["owner"], "r1")
        self.assertEqual(crm.waiting, [second])
        self.assertEqual(crm.log[-2:], [("advance", opp, "m1"), ("assign", first, "system")])


if __name__ == "__main__":
    unittest.main()
