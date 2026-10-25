"""Behavioural tests for crm.py (spec: /tmp/aep-lab/specs/crm.md)."""

import unittest

from crm import CRM, DuplicateLeadError


def user(user_id, role="rep", capacity=5):
    return {"id": user_id, "role": role, "capacity": capacity}


class CRMTestCase(unittest.TestCase):
    def make_crm(self, *users):
        return CRM([dict(u) for u in users])

    def make_opp(self, crm, amount, email, actor="r1", source="referral"):
        """Create, qualify and convert a lead owned by ``actor``; return (lead_id, opp_id)."""
        lead_id = crm.add_lead(email, "Lead", source, actor)
        crm.qualify(lead_id, actor)
        opp_id = crm.convert(lead_id, amount, actor)
        return lead_id, opp_id


class TestLeadValidation(CRMTestCase):
    def test_lead_fields_are_normalized_and_scored(self):
        crm = self.make_crm(user("r1"))
        lead_id = crm.add_lead("  Jane.Doe@Example.COM  ", "  Jane  ", "referral", "r1")
        lead = crm.leads[lead_id]
        self.assertEqual(
            lead,
            {
                "id": "L1",
                "email": "jane.doe@example.com",
                "name": "Jane",
                "source": "referral",
                "score": 45,
                "owner": "r1",
                "status": "new",
            },
        )
        self.assertEqual(crm.log, [("add_lead", "L1", "r1")])

    def test_scores_for_each_source_and_domain_kind(self):
        crm = self.make_crm(user("r1", capacity=10))
        scores = {
            crm.add_lead("web.free@gmail.com", "A", "web", "r1"): 10,
            crm.add_lead("web.corp@acme.io", "B", "web", "r1"): 25,
            crm.add_lead("ref.free@yahoo.com", "C", "referral", "r1"): 30,
            crm.add_lead("ref.corp@acme.io", "D", "referral", "r1"): 45,
            crm.add_lead("evt.free@outlook.com", "E", "event", "r1"): 20,
            crm.add_lead("evt.corp@acme.io", "F", "event", "r1"): 35,
        }
        for lead_id, expected in scores.items():
            self.assertEqual(crm.leads[lead_id]["score"], expected, lead_id)

    def test_email_validation_rejects_bad_input(self):
        crm = self.make_crm(user("r1"))
        bad_emails = [
            None,
            123,
            "",
            "plainaddress",
            "@example.com",
            "a@@example.com",
            "a@b@example.com",
            "a@b",
            "a@.com",
            "a@example.",
        ]
        for bad in bad_emails:
            with self.subTest(email=bad):
                with self.assertRaises(ValueError):
                    crm.add_lead(bad, "Valid", "web", "r1")
        self.assertEqual(crm.leads, {})
        self.assertEqual(crm.log, [])

    def test_email_validation_accepts_dot_inside_domain(self):
        crm = self.make_crm(user("r1"))
        lead_id = crm.add_lead("x@y.z", "Valid", "web", "r1")
        self.assertEqual(crm.leads[lead_id]["email"], "x@y.z")

    def test_name_and_source_validation(self):
        crm = self.make_crm(user("r1"))
        for bad_name in ["", "   ", "\t\n", None, 7]:
            with self.subTest(name=bad_name):
                with self.assertRaises(ValueError):
                    crm.add_lead("a@example.com", bad_name, "web", "r1")
        for bad_source in ["tv", "", None, 3, "WEB"]:
            with self.subTest(source=bad_source):
                with self.assertRaises(ValueError):
                    crm.add_lead("a@example.com", "Valid", bad_source, "r1")
        self.assertEqual(crm.leads, {})
        self.assertEqual(crm.log, [])


class TestDuplicateDetection(CRMTestCase):
    def test_duplicate_normalized_email_is_rejected(self):
        crm = self.make_crm(user("r1"))
        lead_id = crm.add_lead("Jane@Example.com", "Jane", "web", "r1")
        with self.assertRaises(DuplicateLeadError) as caught:
            crm.add_lead("  jane@EXAMPLE.COM ", "Other", "referral", "r1")
        self.assertEqual(caught.exception.existing_id, lead_id)
        self.assertEqual(list(crm.leads), [lead_id])
        self.assertEqual(crm.log, [("add_lead", "L1", "r1")])

    def test_duplicate_does_not_consume_a_lead_id(self):
        crm = self.make_crm(user("r1"))
        first = crm.add_lead("dup@example.com", "A", "web", "r1")
        with self.assertRaises(DuplicateLeadError):
            crm.add_lead("dup@example.com", "B", "web", "r1")
        second = crm.add_lead("other@example.com", "C", "web", "r1")
        self.assertEqual(first, "L1")
        self.assertEqual(second, "L2")


class TestAssignmentAndCapacity(CRMTestCase):
    def test_assignment_uses_lowest_load_then_smallest_id(self):
        crm = self.make_crm(user("r2"), user("r1"), user("m1", role="manager"))
        owners = [
            crm.leads[crm.add_lead("a@example.com", "A", "web", "m1")]["owner"],
            crm.leads[crm.add_lead("b@example.com", "B", "web", "m1")]["owner"],
            crm.leads[crm.add_lead("c@example.com", "C", "web", "m1")]["owner"],
            crm.leads[crm.add_lead("d@example.com", "D", "web", "m1")]["owner"],
        ]
        self.assertEqual(owners, ["r1", "r2", "r1", "r2"])
        for lead in crm.leads.values():
            self.assertIn(lead["owner"], ("r1", "r2"))

    def test_managers_never_own_work(self):
        crm = self.make_crm(user("m1", role="manager"), user("m2", role="manager"))
        lead_id = crm.add_lead("a@example.com", "A", "web", "m1")
        self.assertIsNone(crm.leads[lead_id]["owner"])

    def test_capacity_zero_rep_is_never_assigned(self):
        crm = self.make_crm(user("r0", capacity=0), user("r1", capacity=1))
        first = crm.add_lead("a@example.com", "A", "web", "r1")
        second = crm.add_lead("b@example.com", "B", "web", "r1")
        self.assertEqual(crm.leads[first]["owner"], "r1")
        self.assertIsNone(crm.leads[second]["owner"])

    def test_full_capacity_queues_lead_and_won_frees_a_slot(self):
        crm = self.make_crm(user("r1", capacity=1), user("r2", capacity=1))
        lead1, opp1 = self.make_opp(crm, 1000, "deal1@example.com")
        lead2 = crm.add_lead("deal2@example.com", "B", "referral", "r2")
        lead3 = crm.add_lead("deal3@example.com", "C", "referral", "r1")
        self.assertEqual(crm.leads[lead1]["owner"], "r1")
        self.assertEqual(crm.leads[lead2]["owner"], "r2")
        self.assertIsNone(crm.leads[lead3]["owner"])

        crm.advance(opp1, "proposal", "r1")
        crm.advance(opp1, "negotiation", "r1")
        crm.advance(opp1, "won", "r1")
        self.assertEqual(crm.leads[lead3]["owner"], "r1")
        self.assertEqual(crm.log[-1], ("assign", lead3, "system"))

    def test_waiting_queue_is_fifo(self):
        crm = self.make_crm(user("r1", capacity=1), user("r2", capacity=1))
        lead1, opp1 = self.make_opp(crm, 1000, "deal1@example.com")
        lead2, opp2 = self.make_opp(crm, 1000, "deal2@example.com", actor="r2")
        lead3 = crm.add_lead("deal3@example.com", "C", "referral", "r1")
        lead4 = crm.add_lead("deal4@example.com", "D", "referral", "r1")
        lead5 = crm.add_lead("deal5@example.com", "E", "referral", "r1")
        self.assertEqual([crm.leads[i]["owner"] for i in (lead3, lead4, lead5)], [None, None, None])

        for stage in ("proposal", "negotiation", "won"):
            crm.advance(opp1, stage, "r1")
        self.assertEqual(crm.leads[lead3]["owner"], "r1")
        self.assertIsNone(crm.leads[lead4]["owner"])

        for stage in ("proposal", "negotiation", "won"):
            crm.advance(opp2, stage, "r2")
        self.assertEqual(crm.leads[lead4]["owner"], "r2")
        self.assertIsNone(crm.leads[lead5]["owner"])
        assigns = [entry for entry in crm.log if entry[0] == "assign"]
        self.assertEqual(assigns, [("assign", lead3, "system"), ("assign", lead4, "system")])

    def test_convert_alone_does_not_drain_the_queue(self):
        crm = self.make_crm(user("r1", capacity=1), user("r2", capacity=1))
        lead1 = crm.add_lead("deal1@example.com", "A", "referral", "r1")
        lead2 = crm.add_lead("deal2@example.com", "B", "referral", "r2")
        waiting = crm.add_lead("deal3@example.com", "C", "referral", "r1")
        crm.qualify(lead1, "r1")
        crm.convert(lead1, 1000, "r1")
        self.assertIsNone(crm.leads[waiting]["owner"])
        self.assertEqual(crm.leads[lead2]["owner"], "r2")

    def test_won_and_lost_opportunities_stop_counting_as_load(self):
        crm = self.make_crm(user("r1", capacity=1))
        lead1, opp1 = self.make_opp(crm, 1000, "deal1@example.com")
        waiting = crm.add_lead("deal2@example.com", "B", "web", "r1")
        self.assertIsNone(crm.leads[waiting]["owner"])
        crm.advance(opp1, "lost", "r1")
        self.assertEqual(crm.leads[waiting]["owner"], "r1")


class TestPermissions(CRMTestCase):
    def test_unknown_actor_is_rejected_everywhere(self):
        crm = self.make_crm(user("r1"))
        lead_id, opp_id = self.make_opp(crm, 1000, "deal1@example.com")
        calls = [
            lambda: crm.add_lead("new@example.com", "N", "web", "ghost"),
            lambda: crm.qualify(lead_id, "ghost"),
            lambda: crm.convert(lead_id, 10, "ghost"),
            lambda: crm.advance(opp_id, "proposal", "ghost"),
            lambda: crm.discount(opp_id, 5, "ghost"),
            lambda: crm.transfer(opp_id, "r1", "ghost"),
            lambda: crm.add_lead("new@example.com", "N", "web", None),
        ]
        for call in calls:
            with self.assertRaises(PermissionError):
                call()
        self.assertEqual(len(crm.leads), 1)
        self.assertEqual(len(crm.opps), 1)
        self.assertEqual(crm.opps[opp_id]["stage"], "prospect")

    def test_non_owner_rep_cannot_act_on_a_lead_or_opportunity(self):
        crm = self.make_crm(user("r1"), user("r2"), user("m1", role="manager"))
        lead1 = crm.add_lead("a@example.com", "A", "referral", "r1")
        crm.add_lead("b@example.com", "B", "referral", "r1")
        self.assertEqual(crm.leads[lead1]["owner"], "r1")

        with self.assertRaises(PermissionError):
            crm.qualify(lead1, "r2")
        self.assertEqual(crm.leads[lead1]["status"], "new")

        crm.qualify(lead1, "r1")
        with self.assertRaises(PermissionError):
            crm.convert(lead1, 500, "r2")
        self.assertEqual(crm.opps, {})

        opp_id = crm.convert(lead1, 500, "r1")
        with self.assertRaises(PermissionError):
            crm.advance(opp_id, "proposal", "r2")
        with self.assertRaises(PermissionError):
            crm.discount(opp_id, 5, "r2")
        self.assertEqual(crm.opps[opp_id]["stage"], "prospect")
        self.assertEqual(crm.opps[opp_id]["amount"], 500)

    def test_manager_may_act_on_any_lead(self):
        crm = self.make_crm(user("r1"), user("m1", role="manager"))
        lead_id = crm.add_lead("a@example.com", "A", "referral", "r1")
        crm.qualify(lead_id, "m1")
        self.assertEqual(crm.leads[lead_id]["status"], "qualified")


class TestQualification(CRMTestCase):
    def test_score_below_threshold_cannot_be_qualified(self):
        crm = self.make_crm(user("r1", capacity=10))
        below = [
            crm.add_lead("web@gmail.com", "A", "web", "r1"),
            crm.add_lead("event@gmail.com", "B", "event", "r1"),
            crm.add_lead("web@acme.io", "C", "web", "r1"),
        ]
        for lead_id in below:
            with self.subTest(lead_id=lead_id):
                with self.assertRaises(ValueError):
                    crm.qualify(lead_id, "r1")
                self.assertEqual(crm.leads[lead_id]["status"], "new")
        self.assertEqual(len(crm.log), 3)

    def test_score_at_threshold_can_be_qualified(self):
        crm = self.make_crm(user("r1"))
        lead_id = crm.add_lead("ref@gmail.com", "A", "referral", "r1")
        crm.qualify(lead_id, "r1")
        self.assertEqual(crm.leads[lead_id]["status"], "qualified")
        self.assertEqual(crm.log[-1], ("qualify", lead_id, "r1"))


class TestStageTransitions(CRMTestCase):
    def test_happy_path_order(self):
        crm = self.make_crm(user("r1"))
        lead_id, opp_id = self.make_opp(crm, 1000, "deal@example.com")
        self.assertEqual(crm.opps[opp_id]["stage"], "prospect")
        for stage in ("proposal", "negotiation", "won"):
            crm.advance(opp_id, stage, "r1")
            self.assertEqual(crm.opps[opp_id]["stage"], stage)

    def test_illegal_transitions_are_rejected(self):
        crm = self.make_crm(user("r1"))
        lead_id, opp_id = self.make_opp(crm, 1000, "deal@example.com")
        for bad in ("negotiation", "won", "prospect"):
            with self.subTest(stage=bad):
                with self.assertRaises(ValueError):
                    crm.advance(opp_id, bad, "r1")
                self.assertEqual(crm.opps[opp_id]["stage"], "prospect")
        crm.advance(opp_id, "proposal", "r1")
        for bad in ("proposal", "won"):
            with self.subTest(stage=bad):
                with self.assertRaises(ValueError):
                    crm.advance(opp_id, bad, "r1")
                self.assertEqual(crm.opps[opp_id]["stage"], "proposal")
        with self.assertRaises(ValueError):
            crm.advance(opp_id, "bogus", "r1")

    def test_lost_is_reachable_from_any_open_stage(self):
        crm = self.make_crm(user("r1"))
        lead_a, opp_a = self.make_opp(crm, 100, "a@example.com")
        crm.advance(opp_a, "lost", "r1")
        self.assertEqual(crm.opps[opp_a]["stage"], "lost")
        lead_b, opp_b = self.make_opp(crm, 100, "b@example.com")
        crm.advance(opp_b, "proposal", "r1")
        crm.advance(opp_b, "lost", "r1")
        self.assertEqual(crm.opps[opp_b]["stage"], "lost")

    def test_final_stages_are_immutable(self):
        crm = self.make_crm(user("r1"))
        lead_id, opp_id = self.make_opp(crm, 1000, "deal@example.com")
        for stage in ("proposal", "negotiation", "won"):
            crm.advance(opp_id, stage, "r1")
        for bad in ("lost", "won", "negotiation"):
            with self.subTest(stage=bad):
                with self.assertRaises(ValueError):
                    crm.advance(opp_id, bad, "r1")
                self.assertEqual(crm.opps[opp_id]["stage"], "won")

        lead_b, opp_b = self.make_opp(crm, 1000, "b@example.com")
        crm.advance(opp_b, "lost", "r1")
        with self.assertRaises(ValueError):
            crm.advance(opp_b, "lost", "r1")


class TestBigDealApproval(CRMTestCase):
    def test_rep_cannot_move_big_deal_to_negotiation(self):
        crm = self.make_crm(user("r1"), user("m1", role="manager"))
        lead_id, opp_id = self.make_opp(crm, 60000, "big@example.com")
        crm.advance(opp_id, "proposal", "r1")
        with self.assertRaises(PermissionError):
            crm.advance(opp_id, "negotiation", "r1")
        self.assertEqual(crm.opps[opp_id]["stage"], "proposal")
        self.assertEqual(crm.log[-1], ("advance", opp_id, "r1"))
        crm.advance(opp_id, "negotiation", "m1")
        self.assertEqual(crm.opps[opp_id]["stage"], "negotiation")

    def test_threshold_is_strictly_greater_than_50000(self):
        crm = self.make_crm(user("r1"), user("m1", role="manager"))
        lead_id, opp_id = self.make_opp(crm, 50000, "edge@example.com")
        crm.advance(opp_id, "proposal", "r1")
        crm.advance(opp_id, "negotiation", "r1")
        self.assertEqual(crm.opps[opp_id]["stage"], "negotiation")


class TestDiscounts(CRMTestCase):
    def test_pct_must_be_an_int_in_range(self):
        crm = self.make_crm(user("r1"), user("m1", role="manager"))
        lead_id, opp_id = self.make_opp(crm, 1000, "deal@example.com")
        for bad in (True, False, 5.5, "10", 0, 31, -1, None):
            with self.subTest(pct=bad):
                with self.assertRaises(ValueError):
                    crm.discount(opp_id, bad, "m1")
        self.assertEqual(crm.opps[opp_id]["amount"], 1000)

    def test_rep_is_limited_to_ten_percent(self):
        crm = self.make_crm(user("r1"), user("m1", role="manager"))
        lead_id, opp_id = self.make_opp(crm, 1000, "deal@example.com")
        with self.assertRaises(PermissionError):
            crm.discount(opp_id, 11, "r1")
        self.assertEqual(crm.opps[opp_id]["amount"], 1000)
        crm.discount(opp_id, 10, "r1")
        self.assertEqual(crm.opps[opp_id]["amount"], 900)
        self.assertEqual(crm.log[-1], ("discount", opp_id, "r1"))

    def test_manager_can_discount_up_to_thirty_percent(self):
        crm = self.make_crm(user("r1"), user("m1", role="manager"))
        lead_id, opp_id = self.make_opp(crm, 1000, "deal@example.com")
        crm.discount(opp_id, 30, "m1")
        self.assertEqual(crm.opps[opp_id]["amount"], 700)

    def test_final_stage_cannot_be_discounted(self):
        crm = self.make_crm(user("r1"), user("m1", role="manager"))
        lead_id, opp_id = self.make_opp(crm, 1000, "deal@example.com")
        crm.advance(opp_id, "lost", "r1")
        with self.assertRaises(ValueError):
            crm.discount(opp_id, 5, "m1")
        with self.assertRaises(ValueError):
            crm.discount(opp_id, 20, "r1")

    def test_cumulative_discount_cannot_drop_below_seventy_percent(self):
        crm = self.make_crm(user("r1"), user("m1", role="manager"))
        lead_id, opp_id = self.make_opp(crm, 1000, "deal@example.com")
        crm.discount(opp_id, 30, "m1")
        self.assertEqual(crm.opps[opp_id]["amount"], 700)
        log_len = len(crm.log)
        with self.assertRaises(ValueError):
            crm.discount(opp_id, 30, "m1")
        self.assertEqual(crm.opps[opp_id]["amount"], 700)
        self.assertEqual(len(crm.log), log_len)

    def test_repeated_small_discounts_hit_the_floor(self):
        crm = self.make_crm(user("r1"))
        lead_id, opp_id = self.make_opp(crm, 1000, "deal@example.com")
        expected = [900, 810, 729]
        for amount in expected:
            crm.discount(opp_id, 10, "r1")
            self.assertEqual(crm.opps[opp_id]["amount"], amount)
        with self.assertRaises(ValueError):
            crm.discount(opp_id, 10, "r1")
        self.assertEqual(crm.opps[opp_id]["amount"], 729)


class TestTransfer(CRMTestCase):
    def test_transfer_validation_and_success(self):
        crm = self.make_crm(
            user("r1", capacity=2),
            user("r2", capacity=2),
            user("r3", capacity=0),
            user("m1", role="manager"),
            user("m2", role="manager"),
        )
        lead_id, opp_id = self.make_opp(crm, 1000, "deal@example.com")

        with self.assertRaises(ValueError):
            crm.transfer("O99", "r2", "m1")
        with self.assertRaises(PermissionError):
            crm.transfer("O99", "r2", "ghost")
        with self.assertRaises(PermissionError):
            crm.transfer(opp_id, "r2", "r1")
        with self.assertRaises(ValueError):
            crm.transfer(opp_id, "m2", "m1")
        with self.assertRaises(ValueError):
            crm.transfer(opp_id, "ghost", "m1")
        with self.assertRaises(ValueError):
            crm.transfer(opp_id, "r1", "m1")
        with self.assertRaises(ValueError):
            crm.transfer(opp_id, "r3", "m1")
        self.assertEqual(crm.opps[opp_id]["owner"], "r1")

        crm.transfer(opp_id, "r2", "m1")
        self.assertEqual(crm.opps[opp_id]["owner"], "r2")
        self.assertEqual(crm.log[-1], ("transfer", opp_id, "m1"))

        for stage in ("proposal", "negotiation", "won"):
            crm.advance(opp_id, stage, "r2")
        with self.assertRaises(ValueError):
            crm.transfer(opp_id, "r1", "m1")
        self.assertEqual(crm.opps[opp_id]["owner"], "r2")

    def test_capacity_check_uses_new_owner_load(self):
        crm = self.make_crm(user("r1", capacity=5), user("r2", capacity=1), user("m1", role="manager"))
        lead_id, opp_id = self.make_opp(crm, 1000, "deal@example.com")
        crm.add_lead("filler@example.com", "Filler", "web", "r2")
        self.assertEqual(crm._load("r2"), 1)
        with self.assertRaises(ValueError):
            crm.transfer(opp_id, "r2", "m1")
        self.assertEqual(crm.opps[opp_id]["owner"], "r1")


class TestForecast(CRMTestCase):
    def test_forecast_tracks_stage_weights_and_won_total(self):
        crm = self.make_crm(user("r1"), user("m1", role="manager"))
        lead_a, opp_a = self.make_opp(crm, 1000, "a@example.com")
        lead_b, opp_b = self.make_opp(crm, 333, "b@example.com")
        self.assertEqual(crm.forecast(), {"open": 2, "weighted": 133, "won": 0})

        crm.advance(opp_a, "proposal", "r1")
        self.assertEqual(crm.forecast(), {"open": 2, "weighted": 333, "won": 0})

        crm.advance(opp_a, "negotiation", "r1")
        self.assertEqual(crm.forecast(), {"open": 2, "weighted": 633, "won": 0})

        crm.advance(opp_a, "won", "r1")
        self.assertEqual(crm.forecast(), {"open": 1, "weighted": 33, "won": 1000})

        crm.discount(opp_b, 10, "m1")
        self.assertEqual(crm.opps[opp_b]["amount"], 299)
        for stage in ("proposal", "negotiation", "won"):
            crm.advance(opp_b, stage, "r1")
        self.assertEqual(crm.forecast(), {"open": 0, "weighted": 0, "won": 1299})

    def test_lost_opportunities_are_not_forecast(self):
        crm = self.make_crm(user("r1"))
        lead_id, opp_id = self.make_opp(crm, 1000, "a@example.com")
        crm.advance(opp_id, "lost", "r1")
        self.assertEqual(crm.forecast(), {"open": 0, "weighted": 0, "won": 0})
        self.assertEqual(crm.log[-1], ("advance", opp_id, "r1"))


class TestLogAndRecords(CRMTestCase):
    def test_log_records_every_successful_operation_in_order(self):
        crm = self.make_crm(user("r1", capacity=1), user("r2", capacity=1))
        lead1 = crm.add_lead("a@example.com", "A", "referral", "r1")
        lead2 = crm.add_lead("b@example.com", "B", "referral", "r2")
        lead3 = crm.add_lead("c@example.com", "C", "referral", "r1")
        crm.qualify(lead1, "r1")
        opp1 = crm.convert(lead1, 1000, "r1")
        for stage in ("proposal", "negotiation", "won"):
            crm.advance(opp1, stage, "r1")
        self.assertEqual(
            crm.log,
            [
                ("add_lead", lead1, "r1"),
                ("add_lead", lead2, "r2"),
                ("add_lead", lead3, "r1"),
                ("qualify", lead1, "r1"),
                ("convert", opp1, "r1"),
                ("advance", opp1, "r1"),
                ("advance", opp1, "r1"),
                ("advance", opp1, "r1"),
                ("assign", lead3, "system"),
            ],
        )

    def test_opportunity_record_shape(self):
        crm = self.make_crm(user("r1"))
        lead_id, opp_id = self.make_opp(crm, 1000, "deal@example.com")
        self.assertEqual(
            crm.opps[opp_id],
            {
                "id": "O1",
                "lead_id": lead_id,
                "owner": "r1",
                "amount": 1000,
                "original_amount": 1000,
                "stage": "prospect",
            },
        )
        self.assertEqual(crm.leads[lead_id]["status"], "converted")


if __name__ == "__main__":
    unittest.main()
