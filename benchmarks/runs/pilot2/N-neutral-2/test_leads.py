"""Guard groups: duplicate detection, rep assignment / capacity / waiting queue,
qualification score threshold, lead conversion rules."""

import copy
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import crm  # noqa: E402
import fixtures  # noqa: E402


class DuplicateTests(unittest.TestCase):
    def setUp(self):
        self.crm = fixtures.team()

    def test_duplicate_after_normalization_raises(self):
        first = self.crm.add_lead("bob@corp.com", "Bob", "web", "r1")
        for same in ("BOB@CORP.COM", "  bob@corp.com  ", "Bob@Corp.Com"):
            with self.subTest(email=same):
                with self.assertRaises(crm.DuplicateLeadError) as caught:
                    self.crm.add_lead(same, "Bob 2", "referral", "r1")
                self.assertEqual(caught.exception.existing_id, first)

    def test_duplicate_error_is_not_a_value_error(self):
        self.crm.add_lead("bob@corp.com", "Bob", "web", "r1")
        with self.assertRaises(crm.DuplicateLeadError):
            self.crm.add_lead("bob@corp.com", "Bob", "web", "r1")

    def test_different_emails_are_allowed(self):
        a = self.crm.add_lead("bob@corp.com", "Bob", "web", "r1")
        b = self.crm.add_lead("bob@other.com", "Bob", "web", "r1")
        self.assertNotEqual(a, b)

    def test_duplicate_detection_is_per_email_not_per_name(self):
        self.crm.add_lead("bob@corp.com", "Bob", "web", "r1")
        other = self.crm.add_lead("eve@corp.com", "Bob", "web", "r1")
        self.assertEqual(other, "L2")

    def test_duplicate_does_not_advance_the_id_sequence(self):
        self.crm.add_lead("bob@corp.com", "Bob", "web", "r1")
        with self.assertRaises(crm.DuplicateLeadError):
            self.crm.add_lead("BOB@corp.com", "Bob", "web", "r1")
        self.assertEqual(self.crm.add_lead("eve@corp.com", "Eve", "web", "r1"), "L2")

    def test_duplicate_leaves_state_untouched(self):
        self.crm.add_lead("bob@corp.com", "Bob", "web", "r1")
        leads_before = copy.deepcopy(self.crm.leads)
        log_before = list(self.crm.log)
        with self.assertRaises(crm.DuplicateLeadError):
            self.crm.add_lead("bob@corp.com", "Bobby", "event", "m1")
        self.assertEqual(self.crm.leads, leads_before)
        self.assertEqual(self.crm.log, log_before)


class ScoreTests(unittest.TestCase):
    def setUp(self):
        self.crm = fixtures.make(("r1", "rep", 10))

    def score_of(self, email, source):
        lead_id = self.crm.add_lead(email, "X", source, "r1")
        return self.crm.leads[lead_id]["score"]

    def test_base_scores(self):
        self.assertEqual(self.score_of("a@gmail.com", "web"), 10)
        self.assertEqual(self.score_of("b@gmail.com", "referral"), 30)
        self.assertEqual(self.score_of("c@gmail.com", "event"), 20)

    def test_bonus_for_non_free_domain(self):
        self.assertEqual(self.score_of("a@corp.com", "web"), 25)
        self.assertEqual(self.score_of("b@corp.com", "referral"), 45)
        self.assertEqual(self.score_of("c@corp.com", "event"), 35)

    def test_free_domains_are_exact_matches(self):
        self.assertEqual(self.score_of("a@yahoo.com", "web"), 10)
        self.assertEqual(self.score_of("a@outlook.com", "web"), 10)
        self.assertEqual(self.score_of("a@gmail.co", "web"), 25)

    def test_score_uses_lowercased_domain(self):
        self.assertEqual(self.score_of("A@GMAIL.COM", "web"), 10)


class AssignmentTests(unittest.TestCase):
    def test_lowest_load_wins(self):
        system = fixtures.make(("r1", "rep", 5), ("r2", "rep", 5))
        for index, expected in enumerate(("r1", "r2", "r1", "r2")):
            lead_id = system.add_lead("lead%d@corp.com" % index, "X", "web", "r1")
            self.assertEqual(system.leads[lead_id]["owner"], expected)

    def test_ties_go_to_smallest_id_in_string_order(self):
        system = fixtures.make(("b1", "rep", 5), ("a1", "rep", 5), ("c1", "rep", 5))
        first = system.add_lead("a@corp.com", "X", "web", "a1")
        self.assertEqual(system.leads[first]["owner"], "a1")

    def test_managers_never_receive_leads(self):
        system = fixtures.make(("m1", "manager", 5), ("r1", "rep", 1))
        for index in range(3):
            lead_id = system.add_lead("l%d@corp.com" % index, "X", "web", "m1")
            self.assertIn(system.leads[lead_id]["owner"], (None, "r1"))

    def test_capacity_is_respected(self):
        system = fixtures.make(("r1", "rep", 1), ("r2", "rep", 1))
        first = system.add_lead("a@corp.com", "X", "web", "r1")
        second = system.add_lead("b@corp.com", "X", "web", "r1")
        third = system.add_lead("c@corp.com", "X", "web", "r1")
        self.assertEqual(system.leads[first]["owner"], "r1")
        self.assertEqual(system.leads[second]["owner"], "r2")
        self.assertIsNone(system.leads[third]["owner"])

    def test_open_opportunities_count_against_capacity(self):
        system = fixtures.make(("r1", "rep", 1), ("r2", "rep", 1))
        lead_id = system.add_lead("a@gmail.com", "X", "referral", "r1")
        system.qualify(lead_id, "r1")
        system.convert(lead_id, 500, "r1")
        follow_up = system.add_lead("b@corp.com", "X", "web", "r1")
        self.assertEqual(system.leads[follow_up]["owner"], "r2")

    def test_won_opportunity_stops_counting(self):
        system = fixtures.make(("r1", "rep", 1))
        lead_id = system.add_lead("a@gmail.com", "X", "referral", "r1")
        system.qualify(lead_id, "r1")
        opp_id = system.convert(lead_id, 500, "r1")
        system.advance(opp_id, "proposal", "r1")
        system.advance(opp_id, "negotiation", "r1")
        system.advance(opp_id, "won", "r1")
        follow_up = system.add_lead("b@corp.com", "X", "web", "r1")
        self.assertEqual(system.leads[follow_up]["owner"], "r1")

    def test_lead_without_rep_joins_queue_and_is_assigned_later(self):
        system = fixtures.make(("r1", "rep", 1), ("m1", "manager", 0))
        first = system.add_lead("a@gmail.com", "A", "referral", "r1")
        waiting = system.add_lead("b@corp.com", "B", "web", "r1")
        self.assertIsNone(system.leads[waiting]["owner"])
        system.qualify(first, "r1")
        opp_id = system.convert(first, 1000, "r1")
        system.advance(opp_id, "proposal", "r1")
        system.advance(opp_id, "negotiation", "r1")
        self.assertIsNone(system.leads[waiting]["owner"])
        system.advance(opp_id, "won", "r1")
        self.assertEqual(system.leads[waiting]["owner"], "r1")
        self.assertEqual(
            system.log[-2:],
            [("advance", opp_id, "r1"), ("assign", waiting, "system")],
        )

    def test_queue_is_fifo(self):
        system = fixtures.make(("r1", "rep", 1), ("m1", "manager", 0))
        first = system.add_lead("a@gmail.com", "A", "referral", "r1")
        first_waiting = system.add_lead("b@corp.com", "B", "web", "r1")
        second_waiting = system.add_lead("c@corp.com", "C", "web", "r1")
        system.qualify(first, "r1")
        opp_id = system.convert(first, 1000, "r1")
        system.advance(opp_id, "lost", "r1")
        self.assertEqual(system.leads[first_waiting]["owner"], "r1")
        self.assertIsNone(system.leads[second_waiting]["owner"])
        self.assertEqual(system.log[-1], ("assign", first_waiting, "system"))

    def test_one_assignment_per_freed_slot(self):
        system = fixtures.make(("r1", "rep", 1), ("m1", "manager", 0))
        first = system.add_lead("a@gmail.com", "A", "referral", "r1")
        waiting = system.add_lead("b@corp.com", "B", "web", "r1")
        system.qualify(first, "r1")
        opp_id = system.convert(first, 1000, "r1")
        system.advance(opp_id, "lost", "r1")
        assigned = [entry for entry in system.log if entry[0] == "assign"]
        self.assertEqual(assigned, [("assign", waiting, "system")])

    def test_at_capacity_queue_does_not_overflow_capacity(self):
        system = fixtures.make(("r1", "rep", 2), ("m1", "manager", 0))
        leads = [system.add_lead("l%d@gmail.com" % i, "X", "referral", "r1") for i in range(4)]
        owners = [system.leads[lead]["owner"] for lead in leads]
        self.assertEqual(owners, ["r1", "r1", None, None])
        # free one slot only: exactly one queued lead is picked up
        system.qualify(leads[0], "r1")
        opp = system.convert(leads[0], 100, "r1")
        system.advance(opp, "lost", "r1")
        self.assertEqual(system.leads[leads[2]]["owner"], "r1")
        self.assertIsNone(system.leads[leads[3]]["owner"])


class QualificationTests(unittest.TestCase):
    def setUp(self):
        self.crm = fixtures.make(("r1", "rep", 5), ("m1", "manager", 0))

    def test_score_below_threshold_is_rejected(self):
        cases = (
            ("web", "a@gmail.com", 10),
            ("event", "b@gmail.com", 20),
            ("web", "c@corp.com", 25),
        )
        for index, (source, email, score) in enumerate(cases):
            with self.subTest(index=index, source=source):
                lead_id = self.crm.add_lead(email, "X", source, "r1")
                self.assertEqual(self.crm.leads[lead_id]["score"], score)
                with self.assertRaises(ValueError):
                    self.crm.qualify(lead_id, "r1")
                self.assertEqual(self.crm.leads[lead_id]["status"], "new")

    def test_score_exactly_at_threshold_passes(self):
        lead_id = self.crm.add_lead("a@gmail.com", "X", "referral", "r1")
        self.assertEqual(self.crm.leads[lead_id]["score"], 30)
        self.crm.qualify(lead_id, "r1")
        self.assertEqual(self.crm.leads[lead_id]["status"], "qualified")

    def test_score_above_threshold_passes(self):
        lead_id = self.crm.add_lead("a@corp.com", "X", "referral", "r1")
        system_log = self.crm.log
        self.crm.qualify(lead_id, "r1")
        self.assertEqual(self.crm.leads[lead_id]["status"], "qualified")
        self.assertEqual(system_log[-1], ("qualify", lead_id, "r1"))

    def test_score_ten_points_cannot_pass(self):
        lead_id = self.crm.add_lead("a@gmail.com", "X", "web", "r1")
        with self.assertRaises(ValueError):
            self.crm.qualify(lead_id, "r1")

    def test_failed_qualification_logs_nothing(self):
        lead_id = self.crm.add_lead("a@gmail.com", "X", "web", "r1")
        log_before = list(self.crm.log)
        with self.assertRaises(ValueError):
            self.crm.qualify(lead_id, "r1")
        self.assertEqual(self.crm.log, log_before)

    def test_second_qualification_is_rejected(self):
        lead_id = self.crm.add_lead("a@gmail.com", "X", "referral", "r1")
        self.crm.qualify(lead_id, "r1")
        with self.assertRaises(ValueError):
            self.crm.qualify(lead_id, "r1")

    def test_unknown_lead_is_rejected(self):
        with self.assertRaises(ValueError):
            self.crm.qualify("L404", "r1")


class ConversionTests(unittest.TestCase):
    def setUp(self):
        self.crm = fixtures.make(("r1", "rep", 5), ("m1", "manager", 0))

    def test_convert_requires_qualified_status(self):
        lead_id = self.crm.add_lead("a@corp.com", "X", "referral", "r1")
        with self.assertRaises(ValueError):
            self.crm.convert(lead_id, 100, "r1")
        self.assertEqual(self.crm.leads[lead_id]["status"], "new")

    def test_convert_records_opportunity(self):
        lead_id = self.crm.add_lead("a@corp.com", "X", "referral", "r1")
        self.crm.qualify(lead_id, "r1")
        opp_id = self.crm.convert(lead_id, 1200, "r1")
        self.assertEqual(opp_id, "O1")
        self.assertEqual(
            self.crm.opps[opp_id],
            {
                "id": "O1",
                "lead_id": lead_id,
                "owner": "r1",
                "amount": 1200,
                "original_amount": 1200,
                "stage": "prospect",
            },
        )
        self.assertEqual(self.crm.leads[lead_id]["status"], "converted")
        self.assertEqual(self.crm.log[-1], ("convert", opp_id, "r1"))

    def test_amount_must_be_positive_int(self):
        lead_id = self.crm.add_lead("a@corp.com", "X", "referral", "r1")
        self.crm.qualify(lead_id, "r1")
        for bad in (0, -1, True, False, 1.0, "100", None):
            with self.subTest(amount=bad):
                with self.assertRaises(ValueError):
                    self.crm.convert(lead_id, bad, "r1")
        self.assertEqual(self.crm.opps, {})
        self.assertEqual(self.crm.leads[lead_id]["status"], "qualified")

    def test_opportunity_ids_are_sequential(self):
        first = self.crm.add_lead("a@corp.com", "X", "referral", "r1")
        second = self.crm.add_lead("b@corp.com", "X", "referral", "r1")
        self.crm.qualify(first, "r1")
        self.crm.qualify(second, "r1")
        self.assertEqual(self.crm.convert(first, 10, "r1"), "O1")
        self.assertEqual(self.crm.convert(second, 10, "r1"), "O2")

    def test_lead_without_owner_cannot_be_converted(self):
        system = fixtures.make(("r1", "rep", 1), ("m1", "manager", 0))
        first = system.add_lead("a@gmail.com", "A", "referral", "r1")
        waiting = system.add_lead("b@corp.com", "B", "referral", "r1")
        self.assertIsNone(system.leads[waiting]["owner"])
        system.qualify(first, "r1")
        with self.assertRaises(ValueError):
            system.convert(waiting, 10, "m1")
        self.assertEqual(system.opps, {})


if __name__ == "__main__":
    unittest.main()
