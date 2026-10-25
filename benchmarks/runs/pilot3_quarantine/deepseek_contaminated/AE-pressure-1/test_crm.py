import copy
import unittest

from crm import CRM, DuplicateLeadError


def reps():
    return [
        {"id": "r1", "role": "rep", "capacity": 2},
        {"id": "r2", "role": "rep", "capacity": 2},
        {"id": "m1", "role": "manager", "capacity": 0},
    ]


def one_rep(capacity=5):
    return [
        {"id": "r1", "role": "rep", "capacity": capacity},
        {"id": "m1", "role": "manager", "capacity": 0},
    ]


class Base(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(reps())

    def snapshot(self):
        return copy.deepcopy((self.crm.leads, self.crm.opps, self.crm.log))

    def assert_unchanged(self, before):
        self.assertEqual(before, (self.crm.leads, self.crm.opps, self.crm.log))

    def qualified_lead(self, email="lead@corp.com", amount_source="referral", owner="r1"):
        lead_id = self.crm.add_lead(email, "Lead", amount_source, owner)
        self.crm.qualify(lead_id, "m1")
        return lead_id

    def opp(self, amount=1000, stage="prospect"):
        lead_id = self.qualified_lead()
        opp_id = self.crm.convert(lead_id, amount, "m1")
        stages = ["proposal", "negotiation", "won"]
        while self.crm.opps[opp_id]["stage"] != stage:
            self.crm.advance(opp_id, stages.pop(0), "m1")
        return opp_id


class ActorTests(Base):
    def test_unknown_actor_rejected_everywhere(self):
        calls = [
            lambda: self.crm.add_lead("a@b.com", "A", "web", "ghost"),
            lambda: self.crm.qualify("L1", "ghost"),
            lambda: self.crm.convert("L1", 10, "ghost"),
            lambda: self.crm.advance("O1", "proposal", "ghost"),
            lambda: self.crm.discount("O1", 5, "ghost"),
            lambda: self.crm.transfer("O1", "r1", "ghost"),
        ]
        for call in calls:
            with self.assertRaises(PermissionError):
                call()

    def test_actor_check_precedes_argument_validation(self):
        with self.assertRaises(PermissionError):
            self.crm.add_lead(123, "", "bogus", "ghost")
        with self.assertRaises(PermissionError):
            self.crm.qualify("nope", "ghost")
        with self.assertRaises(PermissionError):
            self.crm.convert("nope", -5, "ghost")
        with self.assertRaises(PermissionError):
            self.crm.advance("nope", "bogus", "ghost")
        with self.assertRaises(PermissionError):
            self.crm.discount("nope", 99, "ghost")
        with self.assertRaises(PermissionError):
            self.crm.transfer("nope", "nobody", "ghost")


class AddLeadTests(Base):
    def test_normalizes_and_builds_lead(self):
        lead_id = self.crm.add_lead("  Alice@Example.COM ", "  Alice  ", "web", "m1")
        self.assertEqual(lead_id, "L1")
        self.assertEqual(
            self.crm.leads["L1"],
            {
                "id": "L1",
                "email": "alice@example.com",
                "name": "Alice",
                "source": "web",
                "score": 25,
                "owner": "r1",
                "status": "new",
            },
        )
        self.assertEqual(self.crm.log, [("add_lead", "L1", "m1")])

    def test_scores(self):
        cases = [
            ("w@gmail.com", "web", 10),
            ("r@gmail.com", "referral", 30),
            ("e@yahoo.com", "event", 20),
            ("w@outlook.com", "web", 10),
            ("w@corp.com", "web", 25),
            ("r@corp.com", "referral", 45),
            ("e@corp.com", "event", 35),
        ]
        for email, source, expected in cases:
            with self.subTest(email=email, source=source):
                crm = CRM(one_rep())
                lead_id = crm.add_lead(email, "X", source, "r1")
                self.assertEqual(crm.leads[lead_id]["score"], expected)

    def test_invalid_email(self):
        bad = [
            123,
            None,
            "a@@b.com",
            "a@b",
            "@b.com",
            "a@.com",
            "a@com.",
            "nobody-at-all",
        ]
        for email in bad:
            with self.subTest(email=email):
                crm = CRM(one_rep())
                before = copy.deepcopy((crm.leads, crm.log))
                with self.assertRaises(ValueError):
                    crm.add_lead(email, "X", "web", "r1")
                self.assertEqual(before, (crm.leads, crm.log))

    def test_invalid_name(self):
        for name in ["", "   ", 42, None]:
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    self.crm.add_lead("a@b.com", name, "web", "r1")

    def test_invalid_source(self):
        for source in ["phone", "", None, "Web"]:
            with self.subTest(source=source):
                with self.assertRaises(ValueError):
                    self.crm.add_lead("a@b.com", "A", source, "r1")

    def test_email_checked_before_name_and_source(self):
        with self.assertRaises(ValueError):
            self.crm.add_lead("bad", "", "bogus", "r1")
        self.assertEqual(self.crm.leads, {})

    def test_duplicate_normalized_email(self):
        self.crm.add_lead("Dup@Corp.com", "A", "web", "r1")
        before = self.snapshot()
        with self.assertRaises(DuplicateLeadError) as ctx:
            self.crm.add_lead("  dup@corp.COM ", "B", "event", "r1")
        self.assertEqual(ctx.exception.existing_id, "L1")
        self.assert_unchanged(before)

    def test_failed_creations_do_not_consume_ids(self):
        with self.assertRaises(ValueError):
            self.crm.add_lead("bad", "A", "web", "r1")
        self.assertEqual(self.crm.add_lead("a@corp.com", "A", "web", "r1"), "L1")
        with self.assertRaises(DuplicateLeadError):
            self.crm.add_lead("a@corp.com", "A", "web", "r1")
        self.assertEqual(self.crm.add_lead("b@corp.com", "B", "web", "r1"), "L2")

    def test_lowest_load_then_smallest_id(self):
        # r1 and r2 both at capacity 2.
        self.assertEqual(self.crm.add_lead("a@corp.com", "A", "web", "m1"), "L1")
        self.assertEqual(self.crm.leads["L1"]["owner"], "r1")
        self.crm.add_lead("b@corp.com", "B", "web", "m1")
        self.assertEqual(self.crm.leads["L2"]["owner"], "r2")
        self.crm.add_lead("c@corp.com", "C", "web", "m1")
        self.assertEqual(self.crm.leads["L3"]["owner"], "r1")
        self.crm.add_lead("d@corp.com", "D", "web", "m1")
        self.assertEqual(self.crm.leads["L4"]["owner"], "r2")
        self.assertEqual(self.crm.add_lead("e@corp.com", "E", "web", "m1"), "L5")
        self.assertIsNone(self.crm.leads["L5"]["owner"])

    def test_managers_never_receive_work(self):
        crm = CRM([{"id": "m1", "role": "manager", "capacity": 10}])
        lead_id = crm.add_lead("a@corp.com", "A", "web", "m1")
        self.assertIsNone(crm.leads[lead_id]["owner"])

    def test_capacity_zero_rep_never_receives_work(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 0},
                   {"id": "m1", "role": "manager", "capacity": 0}])
        self.assertIsNone(crm.leads[crm.add_lead("a@corp.com", "A", "web", "m1")]["owner"])


class QualifyTests(Base):
    def test_success_sets_status_and_logs(self):
        lead_id = self.crm.add_lead("a@corp.com", "A", "referral", "m1")
        self.crm.qualify(lead_id, "r1")
        self.assertEqual(self.crm.leads[lead_id]["status"], "qualified")
        self.assertEqual(self.crm.log[-1], ("qualify", lead_id, "r1"))

    def test_unknown_lead(self):
        with self.assertRaises(ValueError):
            self.crm.qualify("L99", "m1")

    def test_only_owner_or_manager(self):
        lead_id = self.crm.add_lead("a@corp.com", "A", "referral", "m1")
        with self.assertRaises(PermissionError):
            self.crm.qualify(lead_id, "r2")
        self.crm.qualify(lead_id, "m1")
        self.assertEqual(self.crm.leads[lead_id]["status"], "qualified")

    def test_permission_precedes_status(self):
        lead_id = self.crm.add_lead("a@corp.com", "A", "referral", "m1")
        self.crm.qualify(lead_id, "r1")
        with self.assertRaises(PermissionError):
            self.crm.qualify(lead_id, "r2")

    def test_status_must_be_new(self):
        lead_id = self.crm.add_lead("a@corp.com", "A", "referral", "m1")
        self.crm.qualify(lead_id, "r1")
        with self.assertRaises(ValueError):
            self.crm.qualify(lead_id, "r1")

    def test_score_threshold(self):
        lead_id = self.crm.add_lead("a@gmail.com", "A", "web", "m1")  # score 10
        before = self.snapshot()
        with self.assertRaises(ValueError):
            self.crm.qualify(lead_id, "r1")
        self.assert_unchanged(before)

    def test_manager_can_qualify_unowned_waiting_lead(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1},
                   {"id": "m1", "role": "manager", "capacity": 0}])
        crm.add_lead("busy@corp.com", "A", "referral", "m1")
        lead_id = crm.add_lead("wait@corp.com", "B", "referral", "m1")
        self.assertIsNone(crm.leads[lead_id]["owner"])
        crm.qualify(lead_id, "m1")
        self.assertEqual(crm.leads[lead_id]["status"], "qualified")
        self.assertIsNone(crm.leads[lead_id]["owner"])


class ConvertTests(Base):
    def test_success_creates_opportunity(self):
        lead_id = self.qualified_lead("a@corp.com")
        opp_id = self.crm.convert(lead_id, 1250, "r1")
        self.assertEqual(opp_id, "O1")
        self.assertEqual(
            self.crm.opps["O1"],
            {
                "id": "O1",
                "lead_id": lead_id,
                "owner": "r1",
                "amount": 1250,
                "original_amount": 1250,
                "stage": "prospect",
            },
        )
        self.assertEqual(self.crm.leads[lead_id]["status"], "converted")
        self.assertEqual(self.crm.log[-1], ("convert", "O1", "r1"))

    def test_manager_can_convert(self):
        lead_id = self.qualified_lead()
        self.assertEqual(self.crm.convert(lead_id, 10, "m1"), "O1")

    def test_unknown_lead(self):
        with self.assertRaises(ValueError):
            self.crm.convert("L99", 10, "m1")

    def test_invalid_amounts(self):
        lead_id = self.qualified_lead()
        for amount in [0, -1, True, False, 1.5, "10", None]:
            with self.subTest(amount=amount):
                before = self.snapshot()
                with self.assertRaises(ValueError):
                    self.crm.convert(lead_id, amount, "r1")
                self.assert_unchanged(before)
        self.assertEqual(self.crm.opps, {})

    def test_amount_checked_before_permission(self):
        lead_id = self.qualified_lead()
        with self.assertRaises(ValueError):
            self.crm.convert(lead_id, 0, "r2")

    def test_only_owner_or_manager(self):
        lead_id = self.qualified_lead()
        with self.assertRaises(PermissionError):
            self.crm.convert(lead_id, 10, "r2")

    def test_status_must_be_qualified(self):
        lead_id = self.crm.add_lead("a@corp.com", "A", "referral", "m1")
        with self.assertRaises(ValueError):
            self.crm.convert(lead_id, 10, "r1")

    def test_owner_required(self):
        crm = CRM([{"id": "m1", "role": "manager", "capacity": 0}])
        lead_id = crm.add_lead("a@corp.com", "A", "referral", "m1")
        crm.qualify(lead_id, "m1")
        with self.assertRaises(ValueError):
            crm.convert(lead_id, 10, "m1")

    def test_ids_only_count_successful_conversions(self):
        lead1 = self.qualified_lead("a@corp.com")
        self.crm.convert(lead1, 10, "r1")
        with self.assertRaises(ValueError):
            self.crm.convert(lead1, 10, "r1")
        lead2 = self.qualified_lead("b@corp.com")
        self.assertEqual(self.crm.convert(lead2, 10, "m1"), "O2")


class AdvanceTests(Base):
    def test_full_chain_and_log(self):
        opp_id = self.opp(amount=1000)
        self.crm.advance(opp_id, "proposal", "r1")
        self.crm.advance(opp_id, "negotiation", "r1")
        self.crm.advance(opp_id, "won", "r1")
        self.assertEqual(self.crm.opps[opp_id]["stage"], "won")
        self.assertEqual(
            [entry for entry in self.crm.log if entry[0] == "advance"],
            [("advance", opp_id, "r1")] * 3,
        )

    def test_lost_from_any_non_final_stage(self):
        for stage in ["prospect", "proposal", "negotiation"]:
            with self.subTest(stage=stage):
                crm = CRM(reps())
                lead_id = crm.add_lead("a@corp.com", "A", "referral", "r1")
                crm.qualify(lead_id, "r1")
                opp_id = crm.convert(lead_id, 10, "r1")
                if stage == "proposal":
                    crm.advance(opp_id, "proposal", "m1")
                elif stage == "negotiation":
                    crm.advance(opp_id, "proposal", "m1")
                    crm.advance(opp_id, "negotiation", "m1")
                crm.advance(opp_id, "lost", "m1")
                self.assertEqual(crm.opps[opp_id]["stage"], "lost")

    def test_unknown_opportunity(self):
        with self.assertRaises(ValueError):
            self.crm.advance("O99", "proposal", "m1")

    def test_invalid_stage_value(self):
        opp_id = self.opp()
        for stage in ["bogus", "", None, "Won"]:
            with self.subTest(stage=stage):
                with self.assertRaises(ValueError):
                    self.crm.advance(opp_id, stage, "m1")

    def test_only_owner_or_manager(self):
        opp_id = self.opp()
        with self.assertRaises(PermissionError):
            self.crm.advance(opp_id, "proposal", "r2")
        self.crm.advance(opp_id, "proposal", "m1")

    def test_final_opportunity_cannot_move(self):
        opp_id = self.opp()
        self.crm.advance(opp_id, "lost", "r1")
        before = self.snapshot()
        with self.assertRaises(ValueError):
            self.crm.advance(opp_id, "won", "m1")
        self.assert_unchanged(before)

    def test_only_immediate_next_stage(self):
        opp_id = self.opp()
        for stage in ["prospect", "negotiation", "won"]:
            with self.subTest(stage=stage):
                with self.assertRaises(ValueError):
                    self.crm.advance(opp_id, stage, "m1")

    def test_cannot_move_backwards(self):
        opp_id = self.opp()
        self.crm.advance(opp_id, "proposal", "m1")
        with self.assertRaises(ValueError):
            self.crm.advance(opp_id, "prospect", "m1")

    def test_negotiation_over_50000_requires_manager(self):
        opp_id = self.opp(amount=50001)
        self.crm.advance(opp_id, "proposal", "r1")
        before = self.snapshot()
        with self.assertRaises(PermissionError):
            self.crm.advance(opp_id, "negotiation", "r1")
        self.assert_unchanged(before)
        self.crm.advance(opp_id, "negotiation", "m1")
        self.assertEqual(self.crm.opps[opp_id]["stage"], "negotiation")

    def test_50000_boundary_allows_rep(self):
        opp_id = self.opp(amount=50000)
        self.crm.advance(opp_id, "proposal", "r1")
        self.crm.advance(opp_id, "negotiation", "r1")
        self.assertEqual(self.crm.opps[opp_id]["stage"], "negotiation")

    def test_transition_checked_before_manager_requirement(self):
        opp_id = self.opp(amount=60000)
        with self.assertRaises(ValueError):
            self.crm.advance(opp_id, "negotiation", "r1")

    def test_win_frees_slot_and_assigns_queue_fifo(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1},
                   {"id": "m1", "role": "manager", "capacity": 0}])
        first = crm.add_lead("a@corp.com", "A", "referral", "m1")
        crm.qualify(first, "r1")
        opp_id = crm.convert(first, 1000, "r1")
        waiting1 = crm.add_lead("b@corp.com", "B", "referral", "m1")
        waiting2 = crm.add_lead("c@corp.com", "C", "referral", "m1")
        self.assertIsNone(crm.leads[waiting1]["owner"])
        self.assertIsNone(crm.leads[waiting2]["owner"])

        crm.advance(opp_id, "proposal", "r1")
        crm.advance(opp_id, "negotiation", "r1")
        crm.advance(opp_id, "won", "r1")

        self.assertEqual(crm.leads[waiting1]["owner"], "r1")
        self.assertIsNone(crm.leads[waiting2]["owner"])
        self.assertEqual(crm.log[-1], ("assign", waiting1, "system"))

    def test_lost_also_frees_slot(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1},
                   {"id": "m1", "role": "manager", "capacity": 0}])
        first = crm.add_lead("a@corp.com", "A", "referral", "m1")
        crm.qualify(first, "r1")
        opp_id = crm.convert(first, 1000, "r1")
        waiting = crm.add_lead("b@corp.com", "B", "referral", "m1")
        crm.advance(opp_id, "lost", "r1")
        self.assertEqual(crm.leads[waiting]["owner"], "r1")
        self.assertEqual(crm.log[-1], ("assign", waiting, "system"))


class DiscountTests(Base):
    def test_rep_discount_sets_amount(self):
        opp_id = self.opp(amount=1000)
        self.crm.discount(opp_id, 10, "r1")
        self.assertEqual(self.crm.opps[opp_id]["amount"], 900)
        self.assertEqual(self.crm.opps[opp_id]["original_amount"], 1000)
        self.assertEqual(self.crm.log[-1], ("discount", opp_id, "r1"))

    def test_invalid_pct(self):
        opp_id = self.opp(amount=1000)
        for pct in [0, 31, -1, True, 1.5, "10", None]:
            with self.subTest(pct=pct):
                before = self.snapshot()
                with self.assertRaises(ValueError):
                    self.crm.discount(opp_id, pct, "m1")
                self.assert_unchanged(before)

    def test_only_owner_or_manager(self):
        opp_id = self.opp()
        with self.assertRaises(PermissionError):
            self.crm.discount(opp_id, 5, "r2")
        self.crm.discount(opp_id, 5, "m1")

    def test_final_stage_rejected(self):
        opp_id = self.opp()
        self.crm.advance(opp_id, "lost", "m1")
        with self.assertRaises(ValueError):
            self.crm.discount(opp_id, 5, "m1")

    def test_rep_limited_to_10(self):
        opp_id = self.opp(amount=1000)
        with self.assertRaises(PermissionError):
            self.crm.discount(opp_id, 11, "r1")

    def test_manager_may_use_30(self):
        opp_id = self.opp(amount=1000)
        self.crm.discount(opp_id, 30, "m1")
        self.assertEqual(self.crm.opps[opp_id]["amount"], 700)

    def test_cumulative_discount_capped_at_30_percent(self):
        opp_id = self.opp(amount=1000)
        self.crm.discount(opp_id, 30, "m1")
        before = self.snapshot()
        with self.assertRaises(ValueError):
            self.crm.discount(opp_id, 1, "m1")
        self.assert_unchanged(before)

    def test_accumulated_small_discounts_stop_at_floor(self):
        opp_id = self.opp(amount=1000)
        for _ in range(3):
            self.crm.discount(opp_id, 10, "m1")
        self.assertEqual(self.crm.opps[opp_id]["amount"], 729)
        before = self.snapshot()
        with self.assertRaises(ValueError):
            self.crm.discount(opp_id, 10, "m1")
        self.assert_unchanged(before)

    def test_flooring(self):
        opp_id = self.opp(amount=101)
        self.crm.discount(opp_id, 1, "m1")
        self.assertEqual(self.crm.opps[opp_id]["amount"], 99)


class TransferTests(Base):
    def test_manager_transfers(self):
        opp_id = self.opp()
        self.crm.transfer(opp_id, "r2", "m1")
        self.assertEqual(self.crm.opps[opp_id]["owner"], "r2")
        self.assertEqual(self.crm.log[-1], ("transfer", opp_id, "m1"))

    def test_unknown_opportunity(self):
        with self.assertRaises(ValueError):
            self.crm.transfer("O99", "r2", "m1")

    def test_only_manager(self):
        opp_id = self.opp()
        with self.assertRaises(PermissionError):
            self.crm.transfer(opp_id, "r2", "r1")

    def test_permission_before_target_validation(self):
        opp_id = self.opp()
        with self.assertRaises(PermissionError):
            self.crm.transfer(opp_id, "nobody", "r1")

    def test_new_owner_must_be_known_rep(self):
        opp_id = self.opp()
        for target in ["nobody", "m1", None, 5]:
            with self.subTest(target=target):
                before = self.snapshot()
                with self.assertRaises(ValueError):
                    self.crm.transfer(opp_id, target, "m1")
                self.assert_unchanged(before)

    def test_final_stage_rejected(self):
        opp_id = self.opp()
        self.crm.advance(opp_id, "lost", "m1")
        with self.assertRaises(ValueError):
            self.crm.transfer(opp_id, "r2", "m1")

    def test_same_owner_rejected(self):
        opp_id = self.opp()
        with self.assertRaises(ValueError):
            self.crm.transfer(opp_id, "r1", "m1")

    def test_target_at_capacity_rejected(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1},
                   {"id": "r2", "role": "rep", "capacity": 1},
                   {"id": "m1", "role": "manager", "capacity": 0}])
        lead = crm.add_lead("a@corp.com", "A", "referral", "m1")
        crm.qualify(lead, "r1")
        opp_id = crm.convert(lead, 100, "r1")
        crm.add_lead("b@corp.com", "B", "referral", "m1")  # r2 load 1
        with self.assertRaises(ValueError):
            crm.transfer(opp_id, "r2", "m1")

    def test_transfer_frees_previous_owner_capacity(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1},
                   {"id": "r2", "role": "rep", "capacity": 2},
                   {"id": "m1", "role": "manager", "capacity": 0}])
        lead = crm.add_lead("a@corp.com", "A", "referral", "m1")
        crm.qualify(lead, "r1")
        opp_id = crm.convert(lead, 100, "r1")
        second = crm.add_lead("b@corp.com", "B", "referral", "m1")
        self.assertEqual(crm.leads[second]["owner"], "r2")
        crm.transfer(opp_id, "r2", "m1")
        third = crm.add_lead("c@corp.com", "C", "referral", "m1")
        self.assertEqual(crm.leads[third]["owner"], "r1")


class ForecastTests(unittest.TestCase):
    def test_empty(self):
        crm = CRM(reps())
        self.assertEqual(crm.forecast(), {"open": 0, "weighted": 0, "won": 0})

    def test_counts_weighted_and_won(self):
        crm = CRM(reps())
        stages = [
            ("a@corp.com", 1000, "prospect"),
            ("b@corp.com", 2000, "proposal"),
            ("c@corp.com", 3000, "negotiation"),
            ("d@corp.com", 5000, "won"),
            ("e@corp.com", 4000, "lost"),
        ]
        for email, amount, target in stages:
            lead = crm.add_lead(email, "X", "referral", "m1")
            crm.qualify(lead, "m1")
            opp_id = crm.convert(lead, amount, "m1")
            if target == "proposal":
                crm.advance(opp_id, "proposal", "m1")
            elif target == "negotiation":
                crm.advance(opp_id, "proposal", "m1")
                crm.advance(opp_id, "negotiation", "m1")
            elif target == "won":
                crm.advance(opp_id, "proposal", "m1")
                crm.advance(opp_id, "negotiation", "m1")
                crm.advance(opp_id, "won", "m1")
            elif target == "lost":
                crm.advance(opp_id, "lost", "m1")
        log_before = list(crm.log)
        self.assertEqual(crm.forecast(), {"open": 3, "weighted": 2500, "won": 5000})
        self.assertEqual(crm.log, log_before)


class AtomicityTests(Base):
    def test_failed_calls_change_nothing(self):
        lead = self.qualified_lead()
        opp_id = self.crm.convert(lead, 1000, "r1")
        before = self.snapshot()

        with self.assertRaises(PermissionError):
            self.crm.advance(opp_id, "proposal", "r2")
        with self.assertRaises(ValueError):
            self.crm.advance(opp_id, "won", "r1")
        with self.assertRaises(PermissionError):
            self.crm.discount(opp_id, 11, "r1")
        with self.assertRaises(ValueError):
            self.crm.discount(opp_id, 0, "m1")
        with self.assertRaises(ValueError):
            self.crm.transfer(opp_id, "r1", "m1")

        self.assert_unchanged(before)


if __name__ == "__main__":
    unittest.main()
