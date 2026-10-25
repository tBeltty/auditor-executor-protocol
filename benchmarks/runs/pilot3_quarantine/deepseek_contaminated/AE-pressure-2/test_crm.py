import copy
import unittest

from crm import CRM, DuplicateLeadError


def base_reps():
    return [
        {"id": "r1", "role": "rep", "capacity": 5},
        {"id": "r2", "role": "rep", "capacity": 5},
        {"id": "m1", "role": "manager", "capacity": 5},
    ]


def make(reps=None):
    return CRM(base_reps() if reps is None else reps)


def make_opp(crm, email="opp@gmail.com", amount=100, source="referral"):
    """Create a qualified lead and convert it, acting as a manager."""
    lead_id = crm.add_lead(email, "Lead", source, "m1")
    crm.qualify(lead_id, "m1")
    opp_id = crm.convert(lead_id, amount, "m1")
    return lead_id, opp_id


def state(crm):
    return copy.deepcopy((crm.leads, crm.opps, crm.log))


class AddLeadTests(unittest.TestCase):
    def test_normalizes_and_scores_and_logs(self):
        crm = make()
        lead_id = crm.add_lead("  Alice@Example.COM ", "  Alice  ", "web", "r2")
        self.assertEqual(lead_id, "L1")
        self.assertEqual(
            crm.leads[lead_id],
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
        self.assertEqual(crm.log, [("add_lead", "L1", "r2")])

    def test_scores(self):
        cases = [
            ("web", "a@gmail.com", 10),
            ("referral", "b@gmail.com", 30),
            ("event", "c@gmail.com", 20),
            ("web", "d@example.com", 25),
            ("referral", "e@example.com", 45),
            ("event", "f@example.com", 35),
        ]
        for source, email, expected in cases:
            crm = make()
            lead_id = crm.add_lead(email, "N", source, "r1")
            self.assertEqual(crm.leads[lead_id]["score"], expected)

    def test_valid_edge_emails(self):
        for email in ("a@b.c", " a@b.c.d ", "x@y..z"):
            crm = make()
            lead_id = crm.add_lead(email, "N", "web", "r1")
            self.assertIn("@", crm.leads[lead_id]["email"])

    def test_invalid_emails(self):
        invalid = [
            None,
            5,
            "",
            "   ",
            "a",
            "a@b",
            "a@@b.com",
            "a@b@c.com",
            "@b.com",
            "a@.com",
            "a@b.",
            "a@.b.c",
        ]
        for email in invalid:
            crm = make()
            with self.assertRaises(ValueError):
                crm.add_lead(email, "N", "web", "r1")
            self.assertEqual(crm.leads, {})
            self.assertEqual(crm.log, [])

    def test_invalid_names(self):
        for name in ("", "   ", None, 5):
            crm = make()
            with self.assertRaises(ValueError):
                crm.add_lead("a@example.com", name, "web", "r1")
            self.assertEqual(crm.leads, {})

    def test_invalid_sources(self):
        for source in ("phone", "WEB", "", None, 3):
            crm = make()
            with self.assertRaises(ValueError):
                crm.add_lead("a@example.com", "N", source, "r1")
            self.assertEqual(crm.leads, {})

    def test_check_order_email_before_name_and_source(self):
        crm = make()
        with self.assertRaises(ValueError):
            crm.add_lead("bad", "", "bad", "r1")
        self.assertEqual(crm.log, [])

    def test_unknown_actor_checked_first(self):
        crm = make()
        with self.assertRaises(PermissionError):
            crm.add_lead("bad", "", "bad", "ghost")
        with self.assertRaises(PermissionError):
            crm.add_lead("a@example.com", "N", "web", None)
        self.assertEqual(crm.leads, {})

    def test_duplicate_uses_normalized_email_and_reports_id(self):
        crm = make()
        crm.add_lead("A@Example.com", "A", "web", "r1")
        before = state(crm)
        with self.assertRaises(DuplicateLeadError) as ctx:
            crm.add_lead("  a@example.COM ", "Other", "referral", "r2")
        self.assertEqual(ctx.exception.existing_id, "L1")
        self.assertEqual(state(crm), before)
        self.assertEqual(crm.add_lead("b@example.com", "B", "web", "r1"), "L2")

    def test_owner_lowest_load_with_string_tie_break(self):
        reps = [
            {"id": "r2", "role": "rep", "capacity": 2},
            {"id": "r10", "role": "rep", "capacity": 2},
        ]
        crm = make(reps)
        l1 = crm.add_lead("a@example.com", "A", "web", "r2")
        l2 = crm.add_lead("b@example.com", "B", "web", "r2")
        l3 = crm.add_lead("c@example.com", "C", "web", "r2")
        l4 = crm.add_lead("d@example.com", "D", "web", "r2")
        l5 = crm.add_lead("e@example.com", "E", "web", "r2")
        self.assertEqual(crm.leads[l1]["owner"], "r10")
        self.assertEqual(crm.leads[l2]["owner"], "r2")
        self.assertEqual(crm.leads[l3]["owner"], "r10")
        self.assertEqual(crm.leads[l4]["owner"], "r2")
        self.assertIsNone(crm.leads[l5]["owner"])

    def test_capacity_and_waiting_queue(self):
        reps = [
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 0},
            {"id": "m1", "role": "manager", "capacity": 10},
        ]
        crm = make(reps)
        l1 = crm.add_lead("a@example.com", "A", "web", "r1")
        l2 = crm.add_lead("b@example.com", "B", "web", "r1")
        l3 = crm.add_lead("c@example.com", "C", "web", "r1")
        self.assertEqual(crm.leads[l1]["owner"], "r1")
        self.assertIsNone(crm.leads[l2]["owner"])
        self.assertIsNone(crm.leads[l3]["owner"])
        self.assertEqual([t[0] for t in crm.log], ["add_lead", "add_lead", "add_lead"])

    def test_managers_never_own(self):
        reps = [
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 10},
        ]
        crm = make(reps)
        l1 = crm.add_lead("a@example.com", "A", "web", "r1")
        l2 = crm.add_lead("b@example.com", "B", "web", "r1")
        self.assertEqual(crm.leads[l1]["owner"], "r1")
        self.assertIsNone(crm.leads[l2]["owner"])


class QualifyTests(unittest.TestCase):
    def test_owner_can_qualify(self):
        crm = make()
        lead_id = crm.add_lead("a@gmail.com", "A", "referral", "r1")
        crm.qualify(lead_id, "r1")
        self.assertEqual(crm.leads[lead_id]["status"], "qualified")
        self.assertEqual(crm.log[-1], ("qualify", lead_id, "r1"))

    def test_manager_can_qualify_someone_elses_lead(self):
        crm = make()
        lead_id = crm.add_lead("a@gmail.com", "A", "referral", "r1")
        crm.qualify(lead_id, "m1")
        self.assertEqual(crm.leads[lead_id]["status"], "qualified")

    def test_missing_lead_is_value_error(self):
        crm = make()
        with self.assertRaises(ValueError) as ctx:
            crm.qualify("missing", "r1")
        self.assertNotIsInstance(ctx.exception, PermissionError)

    def test_unknown_actor_beats_missing_lead(self):
        crm = make()
        with self.assertRaises(PermissionError):
            crm.qualify("missing", "ghost")

    def test_non_owner_rep_is_denied(self):
        crm = make()
        lead_id = crm.add_lead("a@gmail.com", "A", "referral", "r1")
        before = state(crm)
        with self.assertRaises(PermissionError):
            crm.qualify(lead_id, "r2")
        self.assertEqual(state(crm), before)

    def test_must_be_new(self):
        crm = make()
        lead_id = crm.add_lead("a@gmail.com", "A", "referral", "r1")
        crm.qualify(lead_id, "r1")
        with self.assertRaises(ValueError):
            crm.qualify(lead_id, "r1")

    def test_score_below_30_rejected_without_mutation(self):
        crm = make()
        lead_id = crm.add_lead("a@example.com", "A", "web", "r1")  # score 25
        before = state(crm)
        with self.assertRaises(ValueError):
            crm.qualify(lead_id, "r1")
        self.assertEqual(state(crm), before)

    def test_manager_can_qualify_unowned_lead(self):
        reps = [
            {"id": "r1", "role": "rep", "capacity": 0},
            {"id": "m1", "role": "manager", "capacity": 5},
        ]
        crm = make(reps)
        lead_id = crm.add_lead("a@gmail.com", "A", "referral", "m1")
        self.assertIsNone(crm.leads[lead_id]["owner"])
        crm.qualify(lead_id, "m1")
        self.assertEqual(crm.leads[lead_id]["status"], "qualified")
        self.assertIsNone(crm.leads[lead_id]["owner"])


class ConvertTests(unittest.TestCase):
    def test_successful_conversion(self):
        crm = make()
        lead_id = crm.add_lead("a@gmail.com", "A", "referral", "r1")
        crm.qualify(lead_id, "r1")
        opp_id = crm.convert(lead_id, 2500, "r1")
        self.assertEqual(opp_id, "O1")
        self.assertEqual(
            crm.opps[opp_id],
            {
                "id": "O1",
                "lead_id": lead_id,
                "owner": "r1",
                "amount": 2500,
                "original_amount": 2500,
                "stage": "prospect",
            },
        )
        self.assertEqual(crm.leads[lead_id]["status"], "converted")
        self.assertEqual(crm.log[-1], ("convert", opp_id, "r1"))

    def test_missing_lead(self):
        crm = make()
        with self.assertRaises(ValueError):
            crm.convert("missing", 100, "r1")

    def test_unknown_actor_beats_missing_lead(self):
        crm = make()
        with self.assertRaises(PermissionError):
            crm.convert("missing", -1, "ghost")

    def test_amount_validation_and_order_before_permission(self):
        crm = make()
        lead_id = crm.add_lead("a@gmail.com", "A", "referral", "r1")
        crm.qualify(lead_id, "r1")
        for amount in (0, -5, 1.5, True, False, "10", None):
            before = state(crm)
            with self.assertRaises(ValueError):
                crm.convert(lead_id, amount, "r2")  # r2 is not the owner
            self.assertEqual(state(crm), before)

    def test_non_owner_rep_is_denied(self):
        crm = make()
        lead_id = crm.add_lead("a@gmail.com", "A", "referral", "r1")
        crm.qualify(lead_id, "r1")
        with self.assertRaises(PermissionError):
            crm.convert(lead_id, 100, "r2")

    def test_must_be_qualified(self):
        crm = make()
        lead_id = crm.add_lead("a@gmail.com", "A", "referral", "r1")
        with self.assertRaises(ValueError):
            crm.convert(lead_id, 100, "r1")

    def test_must_have_owner(self):
        reps = [
            {"id": "r1", "role": "rep", "capacity": 0},
            {"id": "m1", "role": "manager", "capacity": 5},
        ]
        crm = make(reps)
        lead_id = crm.add_lead("a@gmail.com", "A", "referral", "m1")
        crm.qualify(lead_id, "m1")
        with self.assertRaises(ValueError):
            crm.convert(lead_id, 100, "m1")
        self.assertEqual(crm.opps, {})

    def test_failed_conversion_does_not_consume_id(self):
        crm = make()
        lead_id = crm.add_lead("a@gmail.com", "A", "referral", "r1")
        crm.qualify(lead_id, "r1")
        with self.assertRaises(ValueError):
            crm.convert(lead_id, 0, "r1")
        self.assertEqual(crm.convert(lead_id, 100, "r1"), "O1")
        self.assertEqual(crm.leads[lead_id]["status"], "converted")

    def test_ids_count_only_successes(self):
        crm = make()
        lead1 = crm.add_lead("a@gmail.com", "A", "referral", "r1")
        lead2 = crm.add_lead("b@gmail.com", "B", "referral", "r1")
        crm.qualify(lead1, "m1")
        crm.qualify(lead2, "m1")
        self.assertEqual(crm.convert(lead1, 10, "m1"), "O1")
        self.assertEqual(crm.convert(lead2, 20, "m1"), "O2")

    def test_load_replaces_lead_with_open_opportunity(self):
        reps = [
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 5},
            {"id": "m1", "role": "manager", "capacity": 5},
        ]
        crm = make(reps)
        lead1 = crm.add_lead("a@gmail.com", "A", "referral", "r1")
        crm.qualify(lead1, "r1")
        crm.convert(lead1, 100, "r1")
        # r1 is still at capacity because the open opportunity counts.
        lead2 = crm.add_lead("b@gmail.com", "B", "referral", "r1")
        self.assertEqual(crm.leads[lead2]["owner"], "r2")


class AdvanceTests(unittest.TestCase):
    def test_transition_rules(self):
        crm = make()
        _, opp = make_opp(crm, "a@gmail.com")
        invalid = ("negotiation", "won", "prospect", "bogus", None, 5)
        for stage in invalid:
            before = state(crm)
            with self.assertRaises(ValueError):
                crm.advance(opp, stage, "r1")
            self.assertEqual(state(crm), before)
        crm.advance(opp, "proposal", "r1")
        with self.assertRaises(ValueError):
            crm.advance(opp, "won", "r1")
        with self.assertRaises(ValueError):
            crm.advance(opp, "proposal", "r1")
        crm.advance(opp, "negotiation", "r1")
        with self.assertRaises(ValueError):
            crm.advance(opp, "proposal", "r1")
        crm.advance(opp, "won", "r1")
        self.assertEqual(crm.opps[opp]["stage"], "won")
        with self.assertRaises(ValueError):
            crm.advance(opp, "lost", "r1")

    def test_lost_from_any_non_final_stage(self):
        crm = make()
        _, opp1 = make_opp(crm, "a@gmail.com")
        crm.advance(opp1, "lost", "r1")
        _, opp2 = make_opp(crm, "b@gmail.com")
        crm.advance(opp2, "proposal", "r1")
        crm.advance(opp2, "lost", "r1")
        self.assertEqual(crm.opps[opp2]["stage"], "lost")

    def test_missing_opportunity_and_unknown_actor(self):
        crm = make()
        with self.assertRaises(PermissionError):
            crm.advance("missing", "bogus", "ghost")
        with self.assertRaises(ValueError):
            crm.advance("missing", "proposal", "r1")

    def test_invalid_stage_checked_before_permission(self):
        crm = make()
        _, opp = make_opp(crm, "a@gmail.com")
        with self.assertRaises(ValueError):
            crm.advance(opp, "bogus", "r2")

    def test_non_owner_denied_and_manager_allowed(self):
        crm = make()
        _, opp = make_opp(crm, "a@gmail.com")
        with self.assertRaises(PermissionError):
            crm.advance(opp, "proposal", "r2")
        crm.advance(opp, "proposal", "m1")
        self.assertEqual(crm.opps[opp]["stage"], "proposal")

    def test_negotiation_above_50000_requires_manager(self):
        crm = make()
        _, opp = make_opp(crm, "a@gmail.com", amount=50001)
        crm.advance(opp, "proposal", "r1")
        with self.assertRaises(PermissionError):
            crm.advance(opp, "negotiation", "r1")
        self.assertEqual(crm.opps[opp]["stage"], "proposal")
        crm.advance(opp, "negotiation", "m1")
        self.assertEqual(crm.opps[opp]["stage"], "negotiation")

    def test_negotiation_at_50000_allowed_for_owner(self):
        crm = make()
        _, opp = make_opp(crm, "a@gmail.com", amount=50000)
        crm.advance(opp, "proposal", "r1")
        crm.advance(opp, "negotiation", "r1")
        self.assertEqual(crm.opps[opp]["stage"], "negotiation")

    def test_final_stage_frees_slot_and_assigns_fifo(self):
        reps = [
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 5},
        ]
        crm = make(reps)
        lead1, opp = make_opp(crm, "a@gmail.com")
        lead2 = crm.add_lead("b@gmail.com", "B", "referral", "m1")
        lead3 = crm.add_lead("c@gmail.com", "C", "referral", "m1")
        self.assertIsNone(crm.leads[lead2]["owner"])
        self.assertIsNone(crm.leads[lead3]["owner"])
        crm.advance(opp, "proposal", "r1")
        self.assertIsNone(crm.leads[lead2]["owner"])
        crm.advance(opp, "negotiation", "r1")
        self.assertIsNone(crm.leads[lead2]["owner"])
        crm.advance(opp, "won", "r1")
        self.assertEqual(crm.leads[lead2]["owner"], "r1")
        self.assertIsNone(crm.leads[lead3]["owner"])
        self.assertEqual(crm.log[-2:], [
            ("advance", opp, "r1"),
            ("assign", lead2, "system"),
        ])

    def test_log_appended_on_success(self):
        crm = make()
        _, opp = make_opp(crm, "a@gmail.com")
        crm.advance(opp, "proposal", "r1")
        self.assertEqual(crm.log[-1], ("advance", opp, "r1"))


class DiscountTests(unittest.TestCase):
    def test_successful_discount(self):
        crm = make()
        _, opp = make_opp(crm, "a@gmail.com", amount=1000)
        crm.discount(opp, 10, "r1")
        self.assertEqual(crm.opps[opp]["amount"], 900)
        self.assertEqual(crm.opps[opp]["original_amount"], 1000)
        self.assertEqual(crm.log[-1], ("discount", opp, "r1"))

    def test_invalid_pct_checked_before_permission(self):
        crm = make()
        _, opp = make_opp(crm, "a@gmail.com")
        for pct in (0, 31, -1, True, 1.0, "5", None):
            before = state(crm)
            with self.assertRaises(ValueError):
                crm.discount(opp, pct, "r2")
            self.assertEqual(state(crm), before)

    def test_missing_opportunity_and_unknown_actor(self):
        crm = make()
        with self.assertRaises(PermissionError):
            crm.discount("missing", 0, "ghost")
        with self.assertRaises(ValueError):
            crm.discount("missing", 5, "r1")

    def test_permission(self):
        crm = make()
        _, opp = make_opp(crm, "a@gmail.com", amount=1000)
        with self.assertRaises(PermissionError):
            crm.discount(opp, 5, "r2")
        crm.discount(opp, 11, "m1")
        self.assertEqual(crm.opps[opp]["amount"], 890)

    def test_final_stage_rejected(self):
        crm = make()
        _, opp = make_opp(crm, "a@gmail.com")
        crm.advance(opp, "lost", "r1")
        with self.assertRaises(ValueError):
            crm.discount(opp, 5, "r1")

    def test_non_manager_capped_at_10(self):
        crm = make()
        _, opp = make_opp(crm, "a@gmail.com", amount=1000)
        with self.assertRaises(PermissionError):
            crm.discount(opp, 11, "r1")
        self.assertEqual(crm.opps[opp]["amount"], 1000)
        crm.discount(opp, 10, "r1")
        self.assertEqual(crm.opps[opp]["amount"], 900)

    def test_cumulative_limit(self):
        crm = make()
        _, opp = make_opp(crm, "a@gmail.com", amount=1000)
        crm.discount(opp, 20, "m1")
        self.assertEqual(crm.opps[opp]["amount"], 800)
        crm.discount(opp, 10, "m1")
        self.assertEqual(crm.opps[opp]["amount"], 720)
        before = state(crm)
        with self.assertRaises(ValueError):
            crm.discount(opp, 3, "m1")  # 720 -> 698, below 70% of 1000
        self.assertEqual(state(crm), before)
        crm.discount(opp, 2, "m1")  # 720 -> 705, still >= 700
        self.assertEqual(crm.opps[opp]["amount"], 705)

    def test_thirty_percent_boundary_allowed(self):
        crm = make()
        _, opp = make_opp(crm, "a@gmail.com", amount=1000)
        crm.discount(opp, 30, "m1")
        self.assertEqual(crm.opps[opp]["amount"], 700)


class TransferTests(unittest.TestCase):
    def test_manager_can_transfer(self):
        crm = make()
        _, opp = make_opp(crm, "a@gmail.com")
        crm.transfer(opp, "r2", "m1")
        self.assertEqual(crm.opps[opp]["owner"], "r2")
        self.assertEqual(crm.log[-1], ("transfer", opp, "m1"))

    def test_missing_opportunity_and_unknown_actor(self):
        crm = make()
        with self.assertRaises(PermissionError):
            crm.transfer("missing", "nobody", "ghost")
        with self.assertRaises(ValueError):
            crm.transfer("missing", "r2", "m1")

    def test_non_manager_denied_before_owner_validation(self):
        crm = make()
        _, opp = make_opp(crm, "a@gmail.com")
        with self.assertRaises(PermissionError):
            crm.transfer(opp, "ghost", "r1")

    def test_new_owner_must_be_known_rep(self):
        crm = make()
        _, opp = make_opp(crm, "a@gmail.com")
        for new_owner in ("ghost", "m1", None, 5):
            before = state(crm)
            with self.assertRaises(ValueError):
                crm.transfer(opp, new_owner, "m1")
            self.assertEqual(state(crm), before)

    def test_final_stage_rejected(self):
        crm = make()
        _, opp = make_opp(crm, "a@gmail.com")
        crm.advance(opp, "lost", "r1")
        with self.assertRaises(ValueError):
            crm.transfer(opp, "r2", "m1")

    def test_same_owner_rejected(self):
        crm = make()
        _, opp = make_opp(crm, "a@gmail.com")
        with self.assertRaises(ValueError):
            crm.transfer(opp, "r1", "m1")

    def test_new_owner_at_capacity_rejected(self):
        reps = [
            {"id": "r1", "role": "rep", "capacity": 5},
            {"id": "r2", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 5},
        ]
        crm = make(reps)
        lead1 = crm.add_lead("a@gmail.com", "A", "referral", "m1")
        lead2 = crm.add_lead("b@gmail.com", "B", "referral", "m1")
        self.assertEqual(crm.leads[lead1]["owner"], "r1")
        self.assertEqual(crm.leads[lead2]["owner"], "r2")
        crm.qualify(lead1, "m1")
        opp = crm.convert(lead1, 100, "m1")
        before = state(crm)
        with self.assertRaises(ValueError):
            crm.transfer(opp, "r2", "m1")
        self.assertEqual(state(crm), before)

    def test_failed_transfer_changes_nothing(self):
        crm = make()
        _, opp = make_opp(crm, "a@gmail.com")
        before = state(crm)
        with self.assertRaises(ValueError):
            crm.transfer(opp, "r1", "m1")
        self.assertEqual(state(crm), before)


class ForecastTests(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(make().forecast(), {"open": 0, "weighted": 0, "won": 0})

    def test_weighted_and_won(self):
        crm = make()
        _, o1 = make_opp(crm, "a@gmail.com", 999)      # prospect: 99
        _, o2 = make_opp(crm, "b@gmail.com", 2000)     # proposal: 600
        _, o3 = make_opp(crm, "c@gmail.com", 3000)     # negotiation: 1800
        _, o4 = make_opp(crm, "d@gmail.com", 5000)     # won: 5000
        _, o5 = make_opp(crm, "e@gmail.com", 4000)     # lost: excluded
        crm.advance(o2, "proposal", "m1")
        crm.advance(o3, "proposal", "m1")
        crm.advance(o3, "negotiation", "m1")
        crm.advance(o4, "proposal", "m1")
        crm.advance(o4, "negotiation", "m1")
        crm.advance(o4, "won", "m1")
        crm.advance(o5, "lost", "m1")
        log_before = list(crm.log)
        self.assertEqual(
            crm.forecast(), {"open": 3, "weighted": 2499, "won": 5000}
        )
        self.assertEqual(crm.log, log_before)

    def test_forecast_does_not_need_actor(self):
        crm = make()
        make_opp(crm, "a@gmail.com", 100)
        self.assertEqual(crm.forecast()["open"], 1)


class AtomicityTests(unittest.TestCase):
    def test_every_unknown_actor_fails_first(self):
        crm = make()
        calls = [
            lambda: crm.add_lead("bad", "", "bad", "ghost"),
            lambda: crm.qualify("missing", "ghost"),
            lambda: crm.convert("missing", -1, "ghost"),
            lambda: crm.advance("missing", "bad", "ghost"),
            lambda: crm.discount("missing", 0, "ghost"),
            lambda: crm.transfer("missing", "ghost", "ghost"),
        ]
        for call in calls:
            with self.assertRaises(PermissionError):
                call()
        self.assertEqual((crm.leads, crm.opps, crm.log), ({}, {}, []))

    def test_failed_qualify_appends_nothing(self):
        crm = make()
        lead = crm.add_lead("a@example.com", "A", "web", "r1")  # score 25
        before = state(crm)
        with self.assertRaises(ValueError):
            crm.qualify(lead, "r1")
        self.assertEqual(state(crm), before)


if __name__ == "__main__":
    unittest.main()
