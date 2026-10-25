import copy
import unittest

from crm import CRM, DuplicateLeadError


def make_crm():
    return CRM(
        [
            {"id": "r1", "role": "rep", "capacity": 2},
            {"id": "r2", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 5},
        ]
    )


def make_transfer_crm():
    return CRM(
        [
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 1},
            {"id": "r3", "role": "rep", "capacity": 2},
            {"id": "m1", "role": "manager", "capacity": 5},
        ]
    )


def snapshot(crm):
    return (
        copy.deepcopy(crm.leads),
        copy.deepcopy(crm.opps),
        copy.deepcopy(crm.log),
        copy.deepcopy(crm.waiting),
    )


def lead_opp(crm, email, amount, actor, source="referral", name="Lead"):
    """Create a qualified lead and convert it with ``actor``; return opp id."""
    lead_id = crm.add_lead(email, name, source, actor)
    crm.qualify(lead_id, actor)
    return crm.convert(lead_id, amount, actor)


class TestConstruction(unittest.TestCase):
    def test_initial_state(self):
        crm = make_crm()
        self.assertEqual(crm.leads, {})
        self.assertEqual(crm.opps, {})
        self.assertEqual(crm.log, [])

    def test_duplicate_lead_error_carries_existing_id(self):
        err = DuplicateLeadError("L7")
        self.assertEqual(err.existing_id, "L7")
        self.assertIsInstance(err, Exception)


class TestAddLead(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()

    def test_basic_creation_and_normalization(self):
        lead_id = self.crm.add_lead("  Alice@Example.COM  ", "  Alice  ", "referral", "r1")
        self.assertEqual(lead_id, "L1")
        lead = self.crm.leads["L1"]
        self.assertEqual(
            lead,
            {
                "id": "L1",
                "email": "alice@example.com",
                "name": "Alice",
                "source": "referral",
                "score": 45,
                "owner": "r1",
                "status": "new",
            },
        )
        self.assertEqual(self.crm.log, [("add_lead", "L1", "r1")])

    def test_scores(self):
        cases = [
            ("a@gmail.com", "web", 10),
            ("b@example.com", "web", 25),
            ("c@yahoo.com", "referral", 30),
            ("d@outlook.com", "event", 20),
            ("e@example.com", "event", 35),
            ("f@example.com", "referral", 45),
        ]
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 100}])
        for email, source, expected in cases:
            lead_id = crm.add_lead(email, "N", source, "r1")
            self.assertEqual(crm.leads[lead_id]["score"], expected, email)

    def test_email_validation(self):
        bad = ["", "nope", "a@b", "a@.com", "a@com.", "@example.com",
               "a@@example.com", "a@b@c.com", 42, None, ["a@b.com"]]
        for email in bad:
            with self.assertRaises(ValueError, msg=repr(email)):
                self.crm.add_lead(email, "Name", "web", "r1")
        self.assertEqual(self.crm.leads, {})
        self.assertEqual(self.crm.log, [])

    def test_email_with_inner_dot_only(self):
        lead_id = self.crm.add_lead("a@b..c", "N", "web", "r1")
        self.assertEqual(self.crm.leads[lead_id]["email"], "a@b..c")

    def test_name_validation(self):
        for name in ["", "   ", 7, None]:
            with self.assertRaises(ValueError, msg=repr(name)):
                self.crm.add_lead("a@example.com", name, "web", "r1")
        self.assertEqual(self.crm.leads, {})

    def test_source_validation(self):
        for source in ["phone", "WEB", "", None]:
            with self.assertRaises(ValueError, msg=repr(source)):
                self.crm.add_lead("a@example.com", "N", source, "r1")

    def test_unknown_actor_checked_first(self):
        with self.assertRaises(PermissionError):
            self.crm.add_lead("not-an-email", "", "bogus", "ghost")
        self.assertEqual(self.crm.log, [])

    def test_duplicate_is_normalized(self):
        first = self.crm.add_lead("a@example.com", "A", "web", "r1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            self.crm.add_lead("  A@EXAMPLE.com ", "A", "web", "r1")
        self.assertEqual(ctx.exception.existing_id, first)
        self.assertEqual(len(self.crm.leads), 1)
        self.assertEqual(len(self.crm.log), 1)

    def test_duplicate_checked_after_name_and_source(self):
        self.crm.add_lead("a@example.com", "A", "web", "r1")
        with self.assertRaises(ValueError):
            self.crm.add_lead("a@example.com", "", "web", "r1")
        with self.assertRaises(ValueError):
            self.crm.add_lead("a@example.com", "A", "nope", "r1")

    def test_failed_call_does_not_consume_id(self):
        with self.assertRaises(ValueError):
            self.crm.add_lead("bad", "A", "web", "r1")
        self.assertEqual(self.crm.add_lead("a@example.com", "A", "web", "r1"), "L1")
        with self.assertRaises(DuplicateLeadError):
            self.crm.add_lead("a@example.com", "A", "web", "r1")
        self.assertEqual(self.crm.add_lead("b@example.com", "B", "web", "r1"), "L2")

    def test_assignment_and_fifo_queue(self):
        self.crm.add_lead("a@example.com", "A", "referral", "r1")  # tie -> r1
        self.crm.add_lead("b@example.com", "B", "referral", "r1")  # r2
        self.crm.add_lead("c@example.com", "C", "referral", "r1")  # r1 (r2 full)
        self.crm.add_lead("d@example.com", "D", "referral", "r1")  # waiting
        self.crm.add_lead("e@example.com", "E", "referral", "r1")  # waiting
        owners = [self.crm.leads["L%d" % i]["owner"] for i in range(1, 6)]
        self.assertEqual(owners, ["r1", "r2", "r1", None, None])
        self.assertEqual(self.crm.waiting, ["L4", "L5"])

    def test_tie_break_is_string_order(self):
        crm = CRM(
            [
                {"id": "r2", "role": "rep", "capacity": 5},
                {"id": "r10", "role": "rep", "capacity": 5},
            ]
        )
        crm.add_lead("a@example.com", "A", "web", "r2")
        self.assertEqual(crm.leads["L1"]["owner"], "r10")

    def test_managers_never_own(self):
        crm = CRM([{"id": "m1", "role": "manager", "capacity": 5}])
        crm.add_lead("a@example.com", "A", "web", "m1")
        self.assertIsNone(crm.leads["L1"]["owner"])
        self.assertEqual(crm.waiting, ["L1"])

    def test_zero_capacity_rep_gets_nothing(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 0}])
        crm.add_lead("a@example.com", "A", "web", "r1")
        self.assertIsNone(crm.leads["L1"]["owner"])
        self.assertEqual(crm.waiting, ["L1"])


class TestQualify(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        self.lid = self.crm.add_lead("a@example.com", "A", "referral", "r1")

    def test_success(self):
        self.crm.qualify(self.lid, "r1")
        self.assertEqual(self.crm.leads[self.lid]["status"], "qualified")
        self.assertEqual(self.crm.log[-1], ("qualify", self.lid, "r1"))

    def test_manager_may_qualify_someone_elses_lead(self):
        self.crm.qualify(self.lid, "m1")
        self.assertEqual(self.crm.leads[self.lid]["status"], "qualified")

    def test_unknown_lead(self):
        with self.assertRaises(ValueError):
            self.crm.qualify("L99", "r1")

    def test_unknown_actor_checked_first(self):
        with self.assertRaises(PermissionError):
            self.crm.qualify("L99", "ghost")

    def test_non_owner_rep_denied(self):
        with self.assertRaises(PermissionError):
            self.crm.qualify(self.lid, "r2")
        self.assertEqual(self.crm.leads[self.lid]["status"], "new")

    def test_permission_precedes_status(self):
        self.crm.qualify(self.lid, "r1")
        with self.assertRaises(PermissionError):
            self.crm.qualify(self.lid, "r2")

    def test_status_must_be_new(self):
        self.crm.qualify(self.lid, "r1")
        before = snapshot(self.crm)
        with self.assertRaises(ValueError):
            self.crm.qualify(self.lid, "r1")
        self.assertEqual(snapshot(self.crm), before)

    def test_score_threshold(self):
        low = self.crm.add_lead("g@gmail.com", "G", "web", "r1")  # score 10, owned by r2
        before = snapshot(self.crm)
        with self.assertRaises(ValueError):
            self.crm.qualify(low, "r2")
        self.assertEqual(snapshot(self.crm), before)
        edge = self.crm.add_lead("h@yahoo.com", "H", "referral", "r1")  # score 30
        self.crm.qualify(edge, "m1")
        self.assertEqual(self.crm.leads[edge]["status"], "qualified")


class TestConvert(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        self.lid = self.crm.add_lead("a@example.com", "A", "referral", "r1")
        self.crm.qualify(self.lid, "r1")

    def test_success(self):
        oid = self.crm.convert(self.lid, 1200, "r1")
        self.assertEqual(oid, "O1")
        self.assertEqual(
            self.crm.opps["O1"],
            {
                "id": "O1",
                "lead_id": "L1",
                "owner": "r1",
                "amount": 1200,
                "original_amount": 1200,
                "stage": "prospect",
            },
        )
        self.assertEqual(self.crm.leads[self.lid]["status"], "converted")
        self.assertEqual(self.crm.log[-1], ("convert", "O1", "r1"))

    def test_manager_may_convert(self):
        oid = self.crm.convert(self.lid, 10, "m1")
        self.assertEqual(self.crm.opps[oid]["owner"], "r1")

    def test_unknown_lead(self):
        with self.assertRaises(ValueError):
            self.crm.convert("L99", 100, "r1")

    def test_amount_validation(self):
        for amount in [0, -1, True, False, 1.5, "100", None]:
            with self.assertRaises(ValueError, msg=repr(amount)):
                self.crm.convert(self.lid, amount, "r1")
        self.assertEqual(self.crm.opps, {})
        self.assertEqual(self.crm.leads[self.lid]["status"], "qualified")

    def test_amount_checked_before_permission(self):
        with self.assertRaises(ValueError):
            self.crm.convert(self.lid, 0, "r2")

    def test_permission(self):
        with self.assertRaises(PermissionError):
            self.crm.convert(self.lid, 100, "r2")

    def test_permission_precedes_status(self):
        other = self.crm.add_lead("b@example.com", "B", "referral", "r1")  # owned by r2
        self.assertEqual(self.crm.leads[other]["owner"], "r2")
        with self.assertRaises(PermissionError):
            self.crm.convert(other, 100, "r1")
        self.assertEqual(self.crm.leads[other]["status"], "new")

    def test_status_must_be_qualified(self):
        other = self.crm.add_lead("b@example.com", "B", "referral", "r1")  # owned by r2
        before = snapshot(self.crm)
        with self.assertRaises(ValueError):
            self.crm.convert(other, 100, "r2")
        self.assertEqual(snapshot(self.crm), before)

    def test_owner_required(self):
        crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 1},
                {"id": "m1", "role": "manager", "capacity": 5},
            ]
        )
        first = crm.add_lead("a@example.com", "A", "referral", "r1")
        waiting = crm.add_lead("b@example.com", "B", "referral", "r1")
        crm.qualify(waiting, "m1")
        self.assertIsNone(crm.leads[waiting]["owner"])
        with self.assertRaises(ValueError):
            crm.convert(waiting, 100, "m1")
        self.assertEqual(crm.opps, {})
        self.assertEqual(crm.leads[waiting]["status"], "qualified")
        crm.qualify(first, "r1")
        self.assertEqual(crm.convert(first, 100, "r1"), "O1")

    def test_failed_convert_does_not_consume_id(self):
        other = self.crm.add_lead("b@example.com", "B", "referral", "r1")  # owned by r2
        with self.assertRaises(ValueError):
            self.crm.convert(other, 100, "r2")
        self.assertEqual(self.crm.convert(self.lid, 100, "r1"), "O1")
        self.crm.qualify(other, "r2")
        self.assertEqual(self.crm.convert(other, 100, "r2"), "O2")


class TestAdvance(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        self.oid = lead_opp(self.crm, "a@example.com", 1000, "r1")

    def test_full_walk(self):
        for stage in ["proposal", "negotiation", "won"]:
            self.crm.advance(self.oid, stage, "r1")
            self.assertEqual(self.crm.opps[self.oid]["stage"], stage)
        self.assertEqual(
            self.crm.log[-3:],
            [
                ("advance", self.oid, "r1"),
                ("advance", self.oid, "r1"),
                ("advance", self.oid, "r1"),
            ],
        )

    def test_lost_from_any_non_final_stage(self):
        self.crm.advance(self.oid, "lost", "r1")
        self.assertEqual(self.crm.opps[self.oid]["stage"], "lost")

    def test_unknown_opp(self):
        with self.assertRaises(ValueError):
            self.crm.advance("O99", "proposal", "r1")

    def test_unknown_actor_checked_first(self):
        with self.assertRaises(PermissionError):
            self.crm.advance("O99", "nope", "ghost")

    def test_invalid_stage(self):
        for stage in ["contacted", "PROSPECT", "", None]:
            with self.assertRaises(ValueError, msg=repr(stage)):
                self.crm.advance(self.oid, stage, "r1")

    def test_invalid_stage_checked_before_permission(self):
        with self.assertRaises(ValueError):
            self.crm.advance(self.oid, "bogus", "r2")

    def test_non_owner_rep_denied(self):
        with self.assertRaises(PermissionError):
            self.crm.advance(self.oid, "proposal", "r2")
        self.assertEqual(self.crm.opps[self.oid]["stage"], "prospect")

    def test_skipping_stages_rejected(self):
        for stage in ["negotiation", "won"]:
            before = snapshot(self.crm)
            with self.assertRaises(ValueError):
                self.crm.advance(self.oid, stage, "r1")
            self.assertEqual(snapshot(self.crm), before)

    def test_final_stage_cannot_move(self):
        self.crm.advance(self.oid, "lost", "r1")
        before = snapshot(self.crm)
        with self.assertRaises(ValueError):
            self.crm.advance(self.oid, "won", "r1")
        self.assertEqual(snapshot(self.crm), before)

    def test_large_negotiation_requires_manager(self):
        crm = make_crm()
        oid = lead_opp(crm, "a@example.com", 50001, "r1")
        crm.advance(oid, "proposal", "r1")
        before = snapshot(crm)
        with self.assertRaises(PermissionError):
            crm.advance(oid, "negotiation", "r1")
        self.assertEqual(snapshot(crm), before)
        crm.advance(oid, "negotiation", "m1")
        self.assertEqual(crm.opps[oid]["stage"], "negotiation")

    def test_exact_threshold_needs_no_manager(self):
        crm = make_crm()
        oid = lead_opp(crm, "a@example.com", 50000, "r1")
        crm.advance(oid, "proposal", "r1")
        crm.advance(oid, "negotiation", "r1")
        self.assertEqual(crm.opps[oid]["stage"], "negotiation")

    def test_won_frees_slot_and_assigns_oldest_waiting(self):
        crm = make_crm()
        crm.add_lead("a@example.com", "A", "referral", "r1")  # L1 -> r1
        crm.add_lead("b@example.com", "B", "referral", "r1")  # L2 -> r2
        crm.add_lead("c@example.com", "C", "referral", "r1")  # L3 -> r1
        crm.add_lead("d@example.com", "D", "referral", "r1")  # L4 waiting
        crm.add_lead("e@example.com", "E", "referral", "r1")  # L5 waiting
        crm.qualify("L2", "r2")
        oid = crm.convert("L2", 900, "r2")
        crm.advance(oid, "proposal", "r2")
        crm.advance(oid, "negotiation", "r2")
        crm.advance(oid, "won", "r2")
        self.assertEqual(crm.leads["L4"]["owner"], "r2")
        self.assertEqual(crm.waiting, ["L5"])
        self.assertEqual(
            crm.log[-2:],
            [("advance", oid, "r2"), ("assign", "L4", "system")],
        )

    def test_assign_stops_at_capacity(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 2}])
        crm.add_lead("a@example.com", "A", "referral", "r1")  # L1 -> r1
        crm.add_lead("b@example.com", "B", "referral", "r1")  # L2 -> r1
        crm.qualify("L1", "r1")
        oid = crm.convert("L1", 500, "r1")
        crm.add_lead("c@example.com", "C", "referral", "r1")  # L3 waiting
        crm.add_lead("d@example.com", "D", "referral", "r1")  # L4 waiting
        self.assertEqual(crm.waiting, ["L3", "L4"])
        crm.advance(oid, "proposal", "r1")
        crm.advance(oid, "negotiation", "r1")
        crm.advance(oid, "won", "r1")
        self.assertEqual(crm.leads["L3"]["owner"], "r1")
        self.assertIsNone(crm.leads["L4"]["owner"])
        self.assertEqual(crm.waiting, ["L4"])
        self.assertEqual(crm.log[-2:], [("advance", oid, "r1"), ("assign", "L3", "system")])

    def test_lost_frees_slot(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1}])
        lead_opp(crm, "a@example.com", 100, "r1")
        waiting = crm.add_lead("b@example.com", "B", "referral", "r1")
        self.assertIsNone(crm.leads[waiting]["owner"])
        crm.advance("O1", "lost", "r1")
        self.assertEqual(crm.leads[waiting]["owner"], "r1")
        self.assertEqual(crm.log[-1], ("assign", waiting, "system"))


class TestDiscount(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        self.oid = lead_opp(self.crm, "a@example.com", 1000, "r1")

    def test_rep_discount_and_floor(self):
        self.crm.discount(self.oid, 10, "r1")
        self.assertEqual(self.crm.opps[self.oid]["amount"], 900)
        self.crm.discount(self.oid, 10, "r1")
        self.assertEqual(self.crm.opps[self.oid]["amount"], 810)
        self.crm.discount(self.oid, 10, "r1")
        self.assertEqual(self.crm.opps[self.oid]["amount"], 729)
        before = snapshot(self.crm)
        with self.assertRaises(ValueError):
            self.crm.discount(self.oid, 5, "r1")  # 692 -> cumulative > 30%
        self.assertEqual(snapshot(self.crm), before)

    def test_exact_thirty_percent_allowed(self):
        self.crm.discount(self.oid, 30, "m1")
        self.assertEqual(self.crm.opps[self.oid]["amount"], 700)
        with self.assertRaises(ValueError):
            self.crm.discount(self.oid, 1, "m1")

    def test_rep_discount_cap(self):
        with self.assertRaises(PermissionError):
            self.crm.discount(self.oid, 11, "r1")
        self.assertEqual(self.crm.opps[self.oid]["amount"], 1000)
        self.crm.discount(self.oid, 10, "m1")
        self.assertEqual(self.crm.opps[self.oid]["amount"], 900)

    def test_pct_validation(self):
        for pct in [0, 31, -5, True, 5.0, "5", None]:
            with self.assertRaises(ValueError, msg=repr(pct)):
                self.crm.discount(self.oid, pct, "r1")
        self.assertEqual(self.crm.opps[self.oid]["amount"], 1000)

    def test_pct_checked_before_permission(self):
        with self.assertRaises(ValueError):
            self.crm.discount(self.oid, 0, "r2")

    def test_unknown_opp(self):
        with self.assertRaises(ValueError):
            self.crm.discount("O99", 5, "r1")

    def test_permission(self):
        with self.assertRaises(PermissionError):
            self.crm.discount(self.oid, 5, "r2")

    def test_final_stage_rejected(self):
        self.crm.advance(self.oid, "lost", "r1")
        before = snapshot(self.crm)
        with self.assertRaises(ValueError):
            self.crm.discount(self.oid, 5, "r1")
        self.assertEqual(snapshot(self.crm), before)

    def test_permission_precedes_final_check(self):
        self.crm.advance(self.oid, "lost", "r1")
        with self.assertRaises(PermissionError):
            self.crm.discount(self.oid, 5, "r2")

    def test_cumulative_floor_uses_original_amount(self):
        self.crm.discount(self.oid, 30, "m1")
        self.crm.advance(self.oid, "proposal", "r1")
        with self.assertRaises(ValueError):
            self.crm.discount(self.oid, 1, "r1")
        self.assertEqual(self.crm.opps[self.oid]["amount"], 700)

    def test_amount_floors_toward_zero(self):
        crm = make_crm()
        oid = lead_opp(crm, "a@example.com", 999, "r1")
        crm.discount(oid, 10, "r1")
        self.assertEqual(crm.opps[oid]["amount"], 899)


class TestTransfer(unittest.TestCase):
    def setUp(self):
        self.crm = make_transfer_crm()
        self.crm.add_lead("a@example.com", "A", "referral", "r1")  # L1 -> r1 (cap 1)
        self.crm.add_lead("b@example.com", "B", "referral", "r1")  # L2 -> r2 (cap 1)
        self.crm.add_lead("c@example.com", "C", "referral", "r1")  # L3 -> r3 (cap 2)
        self.crm.qualify("L1", "r1")
        self.oid = self.crm.convert("L1", 4000, "r1")

    def test_success_moves_opportunity(self):
        self.crm.transfer(self.oid, "r3", "m1")
        self.assertEqual(self.crm.opps[self.oid]["owner"], "r3")
        self.assertEqual(self.crm.log[-1], ("transfer", self.oid, "m1"))
        self.assertEqual(self.crm.waiting, [])

    def test_unknown_opp(self):
        with self.assertRaises(ValueError):
            self.crm.transfer("O99", "r3", "m1")

    def test_unknown_actor_checked_first(self):
        with self.assertRaises(PermissionError):
            self.crm.transfer("O99", "r3", "ghost")

    def test_manager_required(self):
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.oid, "r3", "r1")
        self.assertEqual(self.crm.opps[self.oid]["owner"], "r1")

    def test_new_owner_must_be_rep(self):
        for new_owner in ["m1", "ghost", None, 5]:
            with self.assertRaises(ValueError, msg=repr(new_owner)):
                self.crm.transfer(self.oid, new_owner, "m1")

    def test_final_opportunity_rejected(self):
        self.crm.advance(self.oid, "lost", "r1")
        before = snapshot(self.crm)
        with self.assertRaises(ValueError):
            self.crm.transfer(self.oid, "r3", "m1")
        self.assertEqual(snapshot(self.crm), before)

    def test_same_owner_rejected(self):
        with self.assertRaises(ValueError):
            self.crm.transfer(self.oid, "r1", "m1")

    def test_target_at_capacity_rejected(self):
        # r2 holds L2 (new) with capacity 1 -> full
        with self.assertRaises(ValueError):
            self.crm.transfer(self.oid, "r2", "m1")
        self.assertEqual(self.crm.opps[self.oid]["owner"], "r1")

    def test_failure_changes_nothing(self):
        before = snapshot(self.crm)
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.oid, "r3", "r2")
        self.assertEqual(snapshot(self.crm), before)

    def test_load_ignores_converted_lead_but_counts_opportunity(self):
        # r1 owns L1 (converted, not counted) and O1 (prospect, counted) -> load 1.
        # Transferring O1 away frees r1 completely, so a second transfer back works.
        self.crm.transfer(self.oid, "r3", "m1")
        self.crm.transfer(self.oid, "r1", "m1")
        self.assertEqual(self.crm.opps[self.oid]["owner"], "r1")


class TestForecastAndPermissions(unittest.TestCase):
    def test_empty_forecast(self):
        self.assertEqual(make_crm().forecast(), {"open": 0, "weighted": 0, "won": 0})

    def test_forecast_values(self):
        crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 10},
                {"id": "r2", "role": "rep", "capacity": 10},
                {"id": "m1", "role": "manager", "capacity": 5},
            ]
        )
        lead_opp(crm, "a@example.com", 1000, "m1")  # O1 prospect
        o2 = lead_opp(crm, "b@example.com", 2000, "m1")
        crm.advance(o2, "proposal", "m1")
        o3 = lead_opp(crm, "c@example.com", 3000, "m1")
        crm.advance(o3, "proposal", "m1")
        crm.advance(o3, "negotiation", "m1")
        o4 = lead_opp(crm, "d@example.com", 5000, "m1")
        crm.advance(o4, "proposal", "m1")
        crm.advance(o4, "negotiation", "m1")
        crm.advance(o4, "won", "m1")
        o5 = lead_opp(crm, "e@example.com", 4000, "m1")
        crm.advance(o5, "lost", "m1")
        self.assertEqual(crm.forecast(), {"open": 3, "weighted": 2500, "won": 5000})

    def test_forecast_uses_current_amount(self):
        crm = make_crm()
        oid = lead_opp(crm, "a@example.com", 1000, "r1")
        crm.discount(oid, 10, "r1")
        self.assertEqual(crm.forecast(), {"open": 1, "weighted": 90, "won": 0})

    def test_forecast_does_not_log(self):
        crm = make_crm()
        lead_opp(crm, "a@example.com", 1000, "r1")
        log_before = list(crm.log)
        crm.forecast()
        self.assertEqual(crm.log, log_before)

    def test_every_mutating_method_rejects_unknown_actor(self):
        crm = make_crm()
        with self.assertRaises(PermissionError):
            crm.add_lead("a@example.com", "A", "web", "ghost")
        with self.assertRaises(PermissionError):
            crm.qualify("L1", "ghost")
        with self.assertRaises(PermissionError):
            crm.convert("L1", 1, "ghost")
        with self.assertRaises(PermissionError):
            crm.advance("O1", "proposal", "ghost")
        with self.assertRaises(PermissionError):
            crm.discount("O1", 5, "ghost")
        with self.assertRaises(PermissionError):
            crm.transfer("O1", "r1", "ghost")
        self.assertEqual(crm.log, [])
        self.assertEqual(crm.leads, {})
        self.assertEqual(crm.opps, {})

    def test_log_entries_are_triples(self):
        crm = make_crm()
        lead_opp(crm, "a@example.com", 1000, "r1")
        for entry in crm.log:
            self.assertIsInstance(entry, tuple)
            self.assertEqual(len(entry), 3)
            self.assertIsInstance(entry[0], str)
            self.assertIsInstance(entry[1], str)
            self.assertIsInstance(entry[2], str)


if __name__ == "__main__":
    unittest.main()
