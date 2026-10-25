import copy
import unittest

from crm import CRM, DuplicateLeadError


def make_reps(*specs):
    """specs are (id, role, capacity) tuples."""
    return [{"id": i, "role": role, "capacity": cap} for i, role, cap in specs]


def base_crm():
    return CRM(
        make_reps(
            ("r1", "rep", 2),
            ("r2", "rep", 2),
            ("m1", "manager", 0),
        )
    )


def build_opp(crm, email="a@x.com", amount=1000, source="referral", actor="r1"):
    lead = crm.add_lead(email, "Lead " + email, source, actor)
    crm.qualify(lead, actor)
    return crm.convert(lead, amount, actor)


class TestConstruction(unittest.TestCase):
    def test_initial_state(self):
        crm = base_crm()
        self.assertEqual(crm.leads, {})
        self.assertEqual(crm.opps, {})
        self.assertEqual(crm.log, [])

    def test_duplicate_error_has_existing_id(self):
        err = DuplicateLeadError("L7")
        self.assertEqual(err.existing_id, "L7")
        self.assertIsInstance(err, Exception)


class TestActorValidation(unittest.TestCase):
    def test_unknown_actor_checked_first(self):
        crm = base_crm()
        with self.assertRaises(PermissionError):
            crm.add_lead("not-an-email", "", "bogus", "ghost")
        with self.assertRaises(PermissionError):
            crm.qualify("L99", "ghost")
        with self.assertRaises(PermissionError):
            crm.convert("L99", -5, "ghost")
        with self.assertRaises(PermissionError):
            crm.advance("O99", "nope", "ghost")
        with self.assertRaises(PermissionError):
            crm.discount("O99", 99, "ghost")
        with self.assertRaises(PermissionError):
            crm.transfer("O99", "nobody", "ghost")
        self.assertEqual(crm.log, [])
        self.assertEqual(crm.leads, {})
        self.assertEqual(crm.opps, {})

    def test_actor_must_be_string_id(self):
        crm = base_crm()
        for bad in (None, 1, ["r1"]):
            with self.assertRaises(PermissionError):
                crm.add_lead("a@x.com", "A", "web", bad)


class TestAddLeadValidation(unittest.TestCase):
    def setUp(self):
        self.crm = base_crm()

    def test_email_must_be_str(self):
        for bad in (None, 123, b"a@b.com", ["a@b.com"]):
            with self.assertRaises(ValueError):
                self.crm.add_lead(bad, "Ann", "web", "r1")

    def test_invalid_email_shapes(self):
        for email in [
            "",
            "plainaddress",
            "a@@b.com",
            "@b.com",
            "a@bcom",
            "a@.com",
            "a@b.",
            "a@.",
        ]:
            with self.assertRaises(ValueError):
                self.crm.add_lead(email, "Ann", "web", "r1")
        self.assertEqual(self.crm.leads, {})

    def test_email_normalized(self):
        lead_id = self.crm.add_lead("  A@B.COM  ", "Ann", "web", "r1")
        self.assertEqual(self.crm.leads[lead_id]["email"], "a@b.com")

    def test_email_dot_in_middle_of_domain(self):
        lead_id = self.crm.add_lead("ann@sub.example.com", "Ann", "web", "r1")
        self.assertEqual(self.crm.leads[lead_id]["email"], "ann@sub.example.com")

    def test_name_validation(self):
        for bad in ("", "   ", None, 42):
            with self.assertRaises(ValueError):
                self.crm.add_lead("ann@b.com", bad, "web", "r1")

    def test_source_validation(self):
        for bad in ("Web", "email", "", None, 1):
            with self.assertRaises(ValueError):
                self.crm.add_lead("ann@b.com", "Ann", bad, "r1")
        self.assertEqual(self.crm.leads, {})

    def test_check_order_email_then_name_then_source(self):
        with self.assertRaises(ValueError) as ctx:
            self.crm.add_lead("bad", "", "bogus", "r1")
        self.assertIn("email", str(ctx.exception).lower())
        with self.assertRaises(ValueError) as ctx:
            self.crm.add_lead("ann@b.com", "", "bogus", "r1")
        self.assertIn("name", str(ctx.exception).lower())

    def test_lead_shape_and_log(self):
        lead_id = self.crm.add_lead("  Ann@Example.COM ", "  Ann Lee  ", "referral", "m1")
        self.assertEqual(lead_id, "L1")
        self.assertEqual(
            self.crm.leads[lead_id],
            {
                "id": "L1",
                "email": "ann@example.com",
                "name": "Ann Lee",
                "source": "referral",
                "score": 45,
                "owner": "r1",
                "status": "new",
            },
        )
        self.assertEqual(self.crm.log, [("add_lead", "L1", "m1")])


class TestScoresAndOwnership(unittest.TestCase):
    def test_scores(self):
        crm = CRM(make_reps(("r1", "rep", 10)))
        cases = [
            ("a@gmail.com", "web", 10),
            ("b@gmail.com", "referral", 30),
            ("c@gmail.com", "event", 20),
            ("d@acme.io", "web", 25),
            ("e@acme.io", "event", 35),
            ("f@acme.io", "referral", 45),
            ("g@YAHOO.com", "web", 10),
            ("h@outlook.com", "event", 20),
        ]
        for email, source, expected in cases:
            lead_id = crm.add_lead(email, "N", source, "r1")
            self.assertEqual(crm.leads[lead_id]["score"], expected, email)

    def test_free_domain_is_exact_match(self):
        crm = CRM(make_reps(("r1", "rep", 10)))
        self.assertEqual(crm.leads[crm.add_lead("a@mail.gmail.com", "A", "web", "r1")]["score"], 25)
        self.assertEqual(
            crm.leads[crm.add_lead("b@outlook.com.evil.io", "B", "web", "r1")]["score"], 25
        )

    def test_owner_is_least_loaded(self):
        crm = CRM(make_reps(("r1", "rep", 3), ("r2", "rep", 3)))
        self.assertEqual(crm.leads[crm.add_lead("a@x.com", "A", "web", "r1")]["owner"], "r1")
        self.assertEqual(crm.leads[crm.add_lead("b@x.com", "B", "web", "r1")]["owner"], "r2")
        self.assertEqual(crm.leads[crm.add_lead("c@x.com", "C", "web", "r1")]["owner"], "r1")

    def test_tie_break_smallest_id_string_order(self):
        crm = CRM(make_reps(("zz", "rep", 5), ("aa", "rep", 5), ("mm", "rep", 5)))
        self.assertEqual(crm.leads[crm.add_lead("a@x.com", "A", "web", "zz")]["owner"], "aa")
        self.assertEqual(crm.leads[crm.add_lead("b@x.com", "B", "web", "zz")]["owner"], "mm")
        self.assertEqual(crm.leads[crm.add_lead("c@x.com", "C", "web", "zz")]["owner"], "zz")

    def test_managers_never_own(self):
        crm = CRM(make_reps(("m1", "manager", 99), ("r1", "rep", 0)))
        lead_id = crm.add_lead("a@x.com", "A", "web", "m1")
        self.assertIsNone(crm.leads[lead_id]["owner"])

    def test_capacity_zero_rep_never_owns(self):
        crm = CRM(make_reps(("r0", "rep", 0)))
        lead_id = crm.add_lead("a@x.com", "A", "web", "r0")
        self.assertIsNone(crm.leads[lead_id]["owner"])

    def test_no_capacity_goes_to_fifo_waiting_queue(self):
        crm = CRM(make_reps(("r1", "rep", 1)))
        first = crm.add_lead("a@x.com", "A", "referral", "r1")
        second = crm.add_lead("b@x.com", "B", "referral", "r1")
        third = crm.add_lead("c@x.com", "C", "referral", "r1")
        self.assertEqual(crm.leads[first]["owner"], "r1")
        self.assertIsNone(crm.leads[second]["owner"])
        self.assertIsNone(crm.leads[third]["owner"])
        crm.qualify(first, "r1")
        crm.convert(first, 100, "r1")
        self.assertIsNone(crm.leads[second]["owner"])
        for stage in ("proposal", "negotiation", "won"):
            crm.advance("O1", stage, "r1")
        self.assertEqual(crm.leads[second]["owner"], "r1")
        self.assertIsNone(crm.leads[third]["owner"])
        self.assertEqual(crm.log[-1], ("assign", second, "system"))


class TestDuplicates(unittest.TestCase):
    def test_duplicate_detection_and_counters(self):
        crm = base_crm()
        first = crm.add_lead("dup@x.com", "A", "web", "r1")
        log_before = list(crm.log)
        with self.assertRaises(DuplicateLeadError) as ctx:
            crm.add_lead(" DUP@X.com ", "B", "referral", "r1")
        self.assertEqual(ctx.exception.existing_id, first)
        self.assertEqual(crm.log, log_before)
        self.assertEqual(len(crm.leads), 1)
        self.assertEqual(crm.add_lead("other@x.com", "C", "web", "r1"), "L2")

    def test_duplicate_checked_after_source(self):
        crm = base_crm()
        crm.add_lead("dup@x.com", "A", "web", "r1")
        with self.assertRaises(ValueError):
            crm.add_lead("dup@x.com", "B", "bogus", "r1")


class TestQualify(unittest.TestCase):
    def test_happy_path(self):
        crm = base_crm()
        lead = crm.add_lead("a@x.com", "A", "referral", "r1")
        crm.qualify(lead, "r1")
        self.assertEqual(crm.leads[lead]["status"], "qualified")
        self.assertEqual(crm.log[-1], ("qualify", lead, "r1"))

    def test_manager_may_qualify(self):
        crm = base_crm()
        lead = crm.add_lead("a@x.com", "A", "referral", "r1")
        crm.qualify(lead, "m1")
        self.assertEqual(crm.leads[lead]["status"], "qualified")

    def test_unknown_lead(self):
        with self.assertRaises(ValueError):
            base_crm().qualify("L1", "r1")

    def test_other_rep_denied(self):
        crm = base_crm()
        lead = crm.add_lead("a@x.com", "A", "referral", "r1")
        with self.assertRaises(PermissionError):
            crm.qualify(lead, "r2")
        self.assertEqual(crm.leads[lead]["status"], "new")
        self.assertEqual(len(crm.log), 1)

    def test_ownerless_lead_needs_manager(self):
        crm = CRM(make_reps(("r1", "rep", 0), ("m1", "manager", 0)))
        lead = crm.add_lead("a@x.com", "A", "referral", "m1")
        with self.assertRaises(PermissionError):
            crm.qualify(lead, "r1")
        crm.qualify(lead, "m1")
        self.assertEqual(crm.leads[lead]["status"], "qualified")

    def test_status_must_be_new(self):
        crm = base_crm()
        lead = crm.add_lead("a@x.com", "A", "referral", "r1")
        crm.qualify(lead, "r1")
        with self.assertRaises(ValueError):
            crm.qualify(lead, "r1")

    def test_score_below_30_rejected(self):
        crm = base_crm()
        lead = crm.add_lead("a@gmail.com", "A", "web", "r1")  # score 10
        with self.assertRaises(ValueError):
            crm.qualify(lead, "r1")
        self.assertEqual(crm.leads[lead]["status"], "new")

    def test_score_boundary_30_allowed(self):
        crm = base_crm()
        lead = crm.add_lead("a@gmail.com", "A", "referral", "r1")  # exactly 30
        crm.qualify(lead, "r1")
        self.assertEqual(crm.leads[lead]["status"], "qualified")

    def test_permission_checked_before_score(self):
        crm = base_crm()
        lead = crm.add_lead("a@gmail.com", "A", "web", "r1")
        with self.assertRaises(PermissionError):
            crm.qualify(lead, "r2")


class TestConvert(unittest.TestCase):
    def setUp(self):
        self.crm = base_crm()
        self.lead = self.crm.add_lead("a@x.com", "A", "referral", "r1")
        self.crm.qualify(self.lead, "r1")

    def test_happy_path(self):
        opp = self.crm.convert(self.lead, 1000, "r1")
        self.assertEqual(opp, "O1")
        self.assertEqual(
            self.crm.opps[opp],
            {
                "id": "O1",
                "lead_id": self.lead,
                "owner": "r1",
                "amount": 1000,
                "original_amount": 1000,
                "stage": "prospect",
            },
        )
        self.assertEqual(self.crm.leads[self.lead]["status"], "converted")
        self.assertEqual(self.crm.log[-1], ("convert", "O1", "r1"))

    def test_manager_may_convert(self):
        self.assertEqual(self.crm.convert(self.lead, 100, "m1"), "O1")

    def test_unknown_lead(self):
        with self.assertRaises(ValueError):
            self.crm.convert("L99", 100, "r1")

    def test_amount_validation(self):
        for bad in (0, -1, True, False, None, "100", 1.0, 2.5):
            with self.assertRaises(ValueError):
                self.crm.convert(self.lead, bad, "r1")
        self.assertEqual(self.crm.opps, {})
        self.assertEqual(self.crm.leads[self.lead]["status"], "qualified")

    def test_amount_checked_before_permission(self):
        with self.assertRaises(ValueError):
            self.crm.convert(self.lead, 0, "r2")
        with self.assertRaises(PermissionError):
            self.crm.convert(self.lead, 1, "r2")

    def test_requires_qualified_status(self):
        crm = base_crm()
        lead = crm.add_lead("b@x.com", "B", "referral", "r1")
        with self.assertRaises(ValueError):
            crm.convert(lead, 100, "r1")
        self.assertEqual(crm.opps, {})

    def test_ownerless_lead_cannot_convert(self):
        crm = CRM(make_reps(("r1", "rep", 0), ("m1", "manager", 0)))
        lead = crm.add_lead("a@x.com", "A", "referral", "m1")
        crm.qualify(lead, "m1")
        with self.assertRaises(ValueError):
            crm.convert(lead, 100, "m1")
        self.assertEqual(crm.opps, {})
        self.assertEqual(crm.leads[lead]["status"], "qualified")

    def test_opp_counter_counts_successes_only(self):
        second_lead = self.crm.add_lead("b@x.com", "B", "referral", "r1")
        self.crm.qualify(second_lead, "m1")
        with self.assertRaises(ValueError):
            self.crm.convert(second_lead, 0, "m1")
        self.assertEqual(self.crm.convert(self.lead, 10, "r1"), "O1")
        self.assertEqual(self.crm.convert(second_lead, 10, "m1"), "O2")


class TestAdvance(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(make_reps(("r1", "rep", 5), ("r2", "rep", 5), ("m1", "manager", 0)))
        self.opp = build_opp(self.crm)

    def test_full_pipeline(self):
        for stage in ("proposal", "negotiation", "won"):
            self.crm.advance(self.opp, stage, "r1")
            self.assertEqual(self.crm.opps[self.opp]["stage"], stage)
        self.assertEqual(
            [entry[0] for entry in self.crm.log],
            ["add_lead", "qualify", "convert", "advance", "advance", "advance"],
        )
        self.assertEqual(self.crm.log[-1], ("advance", self.opp, "r1"))

    def test_unknown_opportunity(self):
        with self.assertRaises(ValueError):
            self.crm.advance("O9", "proposal", "r1")

    def test_invalid_stage_name(self):
        for bad in ("", "PROSPECT", "closed", None, 1):
            with self.assertRaises(ValueError):
                self.crm.advance(self.opp, bad, "r1")

    def test_permission_checked_before_stage_order(self):
        with self.assertRaises(PermissionError):
            self.crm.advance(self.opp, "won", "r2")
        self.assertEqual(self.crm.opps[self.opp]["stage"], "prospect")

    def test_cannot_skip_stages(self):
        for target in ("negotiation", "won"):
            with self.assertRaises(ValueError):
                self.crm.advance(self.opp, target, "r1")
        self.assertEqual(self.crm.opps[self.opp]["stage"], "prospect")

    def test_cannot_move_backwards(self):
        self.crm.advance(self.opp, "proposal", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "prospect", "r1")

    def test_final_stage_is_final(self):
        self.crm.advance(self.opp, "proposal", "r1")
        self.crm.advance(self.opp, "lost", "r1")
        for stage in ("prospect", "proposal", "lost", "won"):
            with self.assertRaises(ValueError):
                self.crm.advance(self.opp, stage, "m1")

    def test_lost_from_every_non_final_stage(self):
        for start in ((), ("proposal",), ("proposal", "negotiation")):
            crm = CRM(make_reps(("r1", "rep", 5)))
            opp = build_opp(crm)
            for stage in start:
                crm.advance(opp, stage, "r1")
            crm.advance(opp, "lost", "r1")
            self.assertEqual(crm.opps[opp]["stage"], "lost")
            self.assertEqual(crm.forecast(), {"open": 0, "weighted": 0, "won": 0})

    def test_negotiation_above_50000_requires_manager(self):
        crm = CRM(make_reps(("r1", "rep", 5), ("m1", "manager", 0)))
        opp = build_opp(crm, amount=50001)
        crm.advance(opp, "proposal", "r1")
        with self.assertRaises(PermissionError):
            crm.advance(opp, "negotiation", "r1")
        self.assertEqual(crm.opps[opp]["stage"], "proposal")
        crm.advance(opp, "negotiation", "m1")
        self.assertEqual(crm.opps[opp]["stage"], "negotiation")

    def test_negotiation_at_50000_allowed_for_owner(self):
        crm = CRM(make_reps(("r1", "rep", 5)))
        opp = build_opp(crm, amount=50000)
        crm.advance(opp, "proposal", "r1")
        crm.advance(opp, "negotiation", "r1")
        self.assertEqual(crm.opps[opp]["stage"], "negotiation")

    def test_amount_above_50000_proposal_ok(self):
        crm = CRM(make_reps(("r1", "rep", 5)))
        opp = build_opp(crm, amount=90000)
        crm.advance(opp, "proposal", "r1")
        self.assertEqual(crm.opps[opp]["stage"], "proposal")

    def test_won_frees_slot_and_assigns_oldest_waiter(self):
        crm = CRM(make_reps(("r1", "rep", 1), ("r2", "rep", 1)))
        l1 = crm.add_lead("a@x.com", "A", "referral", "r1")
        l2 = crm.add_lead("b@x.com", "B", "referral", "r1")
        l3 = crm.add_lead("c@x.com", "C", "referral", "r1")
        self.assertEqual(crm.leads[l1]["owner"], "r1")
        self.assertEqual(crm.leads[l2]["owner"], "r2")
        self.assertIsNone(crm.leads[l3]["owner"])
        crm.qualify(l1, "r1")
        opp = crm.convert(l1, 100, "r1")
        # r1 load = opp -> full, waiter stays queued
        crm.advance(opp, "proposal", "r1")
        self.assertIsNone(crm.leads[l3]["owner"])
        crm.advance(opp, "negotiation", "r1")
        crm.advance(opp, "won", "r1")
        self.assertEqual(crm.leads[l3]["owner"], "r1")
        self.assertEqual(crm.log[-1], ("assign", l3, "system"))

    def test_lost_frees_slot_and_assigns(self):
        crm = CRM(make_reps(("r1", "rep", 1)))
        l1 = crm.add_lead("a@x.com", "A", "referral", "r1")
        l2 = crm.add_lead("b@x.com", "B", "referral", "r1")
        crm.qualify(l1, "r1")
        opp = crm.convert(l1, 100, "r1")
        crm.advance(opp, "lost", "r1")
        self.assertEqual(crm.leads[l2]["owner"], "r1")

    def test_assign_stops_at_capacity(self):
        crm = CRM(make_reps(("r1", "rep", 2), ("r2", "rep", 0)))
        ids = [crm.add_lead("%s@x.com" % name, name, "referral", "r1") for name in "abc"]
        self.assertEqual(crm.leads[ids[0]]["owner"], "r1")
        self.assertEqual(crm.leads[ids[1]]["owner"], "r1")
        self.assertIsNone(crm.leads[ids[2]]["owner"])
        crm.qualify(ids[0], "r1")
        opp = crm.convert(ids[0], 100, "r1")
        # load = ids[1] (new lead) + opp = 2 -> full
        crm.advance(opp, "lost", "r1")
        self.assertEqual(crm.leads[ids[2]]["owner"], "r1")
        self.assertEqual(crm.log[-1], ("assign", ids[2], "system"))

    def test_advance_does_not_assign_on_non_final_stage(self):
        crm = CRM(make_reps(("r1", "rep", 1)))
        l1 = crm.add_lead("a@x.com", "A", "referral", "r1")
        l2 = crm.add_lead("b@x.com", "B", "referral", "r1")
        crm.qualify(l1, "r1")
        opp = crm.convert(l1, 100, "r1")
        crm.advance(opp, "proposal", "r1")
        self.assertIsNone(crm.leads[l2]["owner"])
        self.assertEqual([e[0] for e in crm.log].count("assign"), 0)


class TestDiscount(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(make_reps(("r1", "rep", 5), ("r2", "rep", 5), ("m1", "manager", 0)))
        self.opp = build_opp(self.crm)

    def test_owner_up_to_10(self):
        self.crm.discount(self.opp, 10, "r1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 900)
        self.assertEqual(self.crm.opps[self.opp]["original_amount"], 1000)
        self.assertEqual(self.crm.log[-1], ("discount", self.opp, "r1"))

    def test_owner_above_10_denied(self):
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp, 11, "r1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 1000)

    def test_manager_may_use_30(self):
        self.crm.discount(self.opp, 30, "m1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 700)

    def test_pct_validation(self):
        for bad in (0, -1, 31, True, False, 5.0, "5", None):
            with self.assertRaises(ValueError):
                self.crm.discount(self.opp, bad, "m1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 1000)

    def test_pct_checked_before_permission(self):
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp, 0, "r2")
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp, 5, "r2")

    def test_unknown_opp(self):
        with self.assertRaises(ValueError):
            self.crm.discount("O9", 5, "m1")

    def test_final_stage_checked_before_limit(self):
        self.crm.advance(self.opp, "lost", "r1")
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp, 20, "r1")

    def test_cumulative_cap(self):
        self.crm.discount(self.opp, 10, "r1")  # 900
        self.crm.discount(self.opp, 10, "r1")  # 810
        self.crm.discount(self.opp, 10, "r1")  # 729
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp, 10, "r1")  # 656 -> under 700
        self.assertEqual(self.crm.opps[self.opp]["amount"], 729)

    def test_cumulative_boundary_exactly_30(self):
        self.crm.discount(self.opp, 30, "m1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 700)
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp, 1, "m1")

    def test_amount_uses_integer_division(self):
        crm = CRM(make_reps(("r1", "rep", 5)))
        opp = build_opp(crm, amount=999)
        crm.discount(opp, 10, "r1")
        self.assertEqual(crm.opps[opp]["amount"], 999 * 90 // 100)


class TestTransfer(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(make_reps(("r1", "rep", 2), ("r2", "rep", 2), ("m1", "manager", 0)))
        self.opp = build_opp(self.crm)

    def test_happy_path(self):
        self.crm.transfer(self.opp, "r2", "m1")
        self.assertEqual(self.crm.opps[self.opp]["owner"], "r2")
        self.assertEqual(self.crm.log[-1], ("transfer", self.opp, "m1"))

    def test_only_managers(self):
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.opp, "r2", "r1")
        self.assertEqual(self.crm.opps[self.opp]["owner"], "r1")

    def test_manager_check_before_new_owner_validation(self):
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.opp, "ghost", "r1")

    def test_new_owner_must_be_known_rep(self):
        for bad in ("ghost", "m1", None, 5):
            with self.assertRaises(ValueError):
                self.crm.transfer(self.opp, bad, "m1")
        self.assertEqual(self.crm.opps[self.opp]["owner"], "r1")

    def test_final_stage_cannot_transfer(self):
        for stage in ("proposal", "negotiation", "won"):
            self.crm.advance(self.opp, stage, "r1")
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "r2", "m1")

    def test_same_owner_rejected(self):
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "r1", "m1")

    def test_new_owner_at_capacity(self):
        crm = CRM(make_reps(("r1", "rep", 2), ("r2", "rep", 1), ("m1", "manager", 0)))
        opp = build_opp(crm)  # owner r1, load r1 = 1
        crm.add_lead("b@x.com", "B", "referral", "m1")  # r2 (load 0)
        self.assertEqual(crm.leads["L2"]["owner"], "r2")
        with self.assertRaises(ValueError):
            crm.transfer(opp, "r2", "m1")
        self.assertEqual(crm.opps[opp]["owner"], "r1")

    def test_transfer_preserves_waiting_queue(self):
        crm = CRM(make_reps(("r1", "rep", 1), ("r2", "rep", 2), ("m1", "manager", 0)))
        l1 = crm.add_lead("a@x.com", "A", "referral", "r1")
        l2 = crm.add_lead("b@x.com", "B", "referral", "m1")  # r2
        waiter = crm.add_lead("c@x.com", "C", "referral", "m1")  # r2 (load 2)
        l4 = crm.add_lead("d@x.com", "D", "referral", "m1")  # queue
        self.assertEqual(crm.leads[l2]["owner"], "r2")
        self.assertEqual(crm.leads[waiter]["owner"], "r2")
        self.assertIsNone(crm.leads[l4]["owner"])
        crm.qualify(l1, "r1")
        opp = crm.convert(l1, 100, "r1")  # r1 full again with opp
        # r2 is full so transfer must fail, waiter untouched
        with self.assertRaises(ValueError):
            crm.transfer(opp, "r2", "m1")
        self.assertIsNone(crm.leads[l4]["owner"])


class TestForecast(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(base_crm().forecast(), {"open": 0, "weighted": 0, "won": 0})

    def build(self):
        crm = CRM(make_reps(("r1", "rep", 10), ("m1", "manager", 0)))
        plan = [
            ("p@x.com", ()),
            ("q@x.com", ("proposal",)),
            ("n@x.com", ("proposal", "negotiation")),
            ("w@x.com", ("proposal", "negotiation", "won")),
            ("l@x.com", ("lost",)),
        ]
        for index, (email, path) in enumerate(plan, start=1):
            lead = crm.add_lead(email, "N%d" % index, "referral", "r1")
            crm.qualify(lead, "r1")
            opp = crm.convert(lead, 1000, "r1")
            for stage in path:
                crm.advance(opp, stage, "r1")
        return crm

    def test_values(self):
        crm = self.build()
        self.assertEqual(crm.forecast(), {"open": 3, "weighted": 100 + 300 + 600, "won": 1000})

    def test_no_log_entry(self):
        crm = self.build()
        before = list(crm.log)
        crm.forecast()
        self.assertEqual(crm.log, before)

    def test_weighted_integer_division(self):
        crm = CRM(make_reps(("r1", "rep", 10)))
        opp = build_opp(crm, amount=101)
        self.assertEqual(crm.forecast()["weighted"], 10)

    def test_won_uses_current_amount(self):
        crm = CRM(make_reps(("r1", "rep", 10), ("m1", "manager", 0)))
        opp = build_opp(crm)
        crm.discount(opp, 30, "m1")
        for stage in ("proposal", "negotiation", "won"):
            crm.advance(opp, stage, "r1")
        self.assertEqual(crm.forecast(), {"open": 0, "weighted": 0, "won": 700})


class TestAtomicity(unittest.TestCase):
    @staticmethod
    def snapshot(crm):
        return copy.deepcopy(crm.leads), copy.deepcopy(crm.opps), list(crm.log)

    def test_failed_calls_leave_no_trace(self):
        crm = CRM(make_reps(("r1", "rep", 1), ("r2", "rep", 1), ("m1", "manager", 0)))
        lead = crm.add_lead("a@gmail.com", "A", "web", "r1")
        crm.add_lead("b@x.com", "B", "referral", "r1")
        before = self.snapshot(crm)
        calls = [
            lambda: crm.add_lead("bad", "A", "web", "r1"),
            lambda: crm.add_lead("a@gmail.com", "A", "web", "r1"),
            lambda: crm.add_lead("new@x.com", "A", "bogus", "r1"),
            lambda: crm.qualify(lead, "r1"),
            lambda: crm.convert(lead, 100, "r1"),
            lambda: crm.advance("O1", "proposal", "r1"),
            lambda: crm.discount("O1", 10, "r1"),
            lambda: crm.transfer("O1", "r2", "r1"),
            lambda: crm.qualify("L9", "r1"),
            lambda: crm.add_lead("x@x.com", "X", "web", "ghost"),
        ]
        for call in calls:
            with self.assertRaises(Exception):
                call()
            self.assertEqual(self.snapshot(crm), before)

    def test_load_accounting_across_lifecycle(self):
        crm = CRM(make_reps(("r1", "rep", 1)))
        lead = crm.add_lead("a@x.com", "A", "referral", "r1")
        waiter = crm.add_lead("b@x.com", "B", "referral", "r1")
        self.assertIsNone(crm.leads[waiter]["owner"])
        crm.qualify(lead, "r1")
        crm.convert(lead, 100, "r1")
        self.assertIsNone(crm.leads[waiter]["owner"])
        for stage in ("proposal", "negotiation", "won"):
            crm.advance("O1", stage, "r1")
        self.assertEqual(crm.leads[waiter]["owner"], "r1")
        self.assertEqual(crm.forecast()["won"], 100)


class TestUnknownIdentifierTypes(unittest.TestCase):
    def test_unhashable_ids_are_unknown_entities(self):
        crm = CRM(make_reps(("r1", "rep", 2), ("m1", "manager", 0)))
        lead = crm.add_lead("a@x.com", "A", "referral", "r1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 100, "r1")
        before = (copy.deepcopy(crm.leads), copy.deepcopy(crm.opps), list(crm.log))
        for bad in ([lead], {"id": lead}, {"x"}, (lead,)):
            for call in (
                lambda: crm.qualify(bad, "r1"),
                lambda: crm.convert(bad, 10, "r1"),
                lambda: crm.advance(bad, "proposal", "r1"),
                lambda: crm.discount(bad, 5, "r1"),
                lambda: crm.transfer(bad, "r1", "m1"),
            ):
                with self.assertRaises(ValueError):
                    call()
                self.assertEqual((crm.leads, crm.opps, crm.log), before)
        with self.assertRaises(ValueError):
            crm.transfer(opp, [lead], "m1")
        self.assertEqual((crm.leads, crm.opps, crm.log), before)

    def test_unhashable_stage_and_pct(self):
        crm = base_crm()
        opp = build_opp(crm)
        with self.assertRaises(ValueError):
            crm.advance(opp, ["proposal"], "r1")
        with self.assertRaises(ValueError):
            crm.discount(opp, [5], "r1")
        self.assertEqual(crm.opps[opp]["stage"], "prospect")
        self.assertEqual(crm.opps[opp]["amount"], 1000)


class TestIdentifierCounters(unittest.TestCase):
    def test_failed_adds_do_not_consume_lead_ids(self):
        crm = base_crm()
        for bad_call in (
            lambda: crm.add_lead("bad", "A", "web", "r1"),
            lambda: crm.add_lead("a@x.com", "", "web", "r1"),
            lambda: crm.add_lead("a@x.com", "A", "bogus", "r1"),
        ):
            with self.assertRaises(ValueError):
                bad_call()
        self.assertEqual(crm.add_lead("a@x.com", "A", "web", "r1"), "L1")
        with self.assertRaises(DuplicateLeadError):
            crm.add_lead("A@X.com", "A", "web", "r1")
        self.assertEqual(crm.add_lead("b@x.com", "B", "web", "r1"), "L2")

    def test_failed_converts_do_not_consume_opp_ids(self):
        crm = base_crm()
        lead = crm.add_lead("a@x.com", "A", "referral", "r1")
        crm.qualify(lead, "r1")
        for bad in (0, -1, True, None):
            with self.assertRaises(ValueError):
                crm.convert(lead, bad, "r1")
        self.assertEqual(crm.convert(lead, 1, "r1"), "O1")


class TestLoadAccounting(unittest.TestCase):
    def test_converted_lead_and_its_opportunity_count_once(self):
        crm = CRM(make_reps(("r1", "rep", 3)))
        first = crm.add_lead("a@x.com", "A", "referral", "r1")
        crm.qualify(first, "r1")
        crm.convert(first, 10, "r1")  # load 1 (opportunity only)
        second = crm.add_lead("b@x.com", "B", "referral", "r1")
        third = crm.add_lead("c@x.com", "C", "referral", "r1")
        fourth = crm.add_lead("d@x.com", "D", "referral", "r1")
        self.assertEqual(crm.leads[second]["owner"], "r1")
        self.assertEqual(crm.leads[third]["owner"], "r1")
        self.assertIsNone(crm.leads[fourth]["owner"])

    def test_transfer_moves_the_opportunity_load(self):
        crm = CRM(make_reps(("r1", "rep", 2), ("r2", "rep", 4), ("m1", "manager", 0)))
        l1 = crm.add_lead("a@x.com", "A", "referral", "r1")  # r1
        l2 = crm.add_lead("b@x.com", "B", "referral", "r1")  # r2
        l3 = crm.add_lead("c@x.com", "C", "referral", "r1")  # r1 (full)
        l4 = crm.add_lead("d@x.com", "D", "referral", "r1")  # r2
        crm.qualify(l1, "r1")
        opp = crm.convert(l1, 100, "r1")
        crm.transfer(opp, "r2", "m1")
        # r1 now holds only l3, r2 holds l2, l4 and the opportunity.
        self.assertEqual(crm.add_lead("e@x.com", "E", "referral", "r1"), "L5")
        self.assertEqual(crm.leads["L5"]["owner"], "r1")
        l6 = crm.add_lead("f@x.com", "F", "referral", "r1")
        self.assertEqual(crm.leads[l6]["owner"], "r2")
        l7 = crm.add_lead("g@x.com", "G", "referral", "r1")
        self.assertIsNone(crm.leads[l7]["owner"])


class TestEmailEdges(unittest.TestCase):
    def test_surrounding_whitespace_including_tabs_and_newlines(self):
        crm = base_crm()
        lead = crm.add_lead("\t Ann@Example.com \n", " Ann ", "web", "r1")
        self.assertEqual(crm.leads[lead]["email"], "ann@example.com")
        self.assertEqual(crm.leads[lead]["name"], "Ann")

    def test_single_character_domain_label_still_needs_inner_dot(self):
        crm = base_crm()
        self.assertEqual(crm.add_lead("a@b.c", "A", "web", "r1"), "L1")
        with self.assertRaises(ValueError):
            crm.add_lead("a@b", "A", "web", "r1")


class TestLogOrdering(unittest.TestCase):
    def test_advance_entry_precedes_assignments(self):
        crm = CRM(make_reps(("r1", "rep", 1)))
        l1 = crm.add_lead("a@x.com", "A", "referral", "r1")
        l2 = crm.add_lead("b@x.com", "B", "referral", "r1")
        crm.qualify(l1, "r1")
        opp = crm.convert(l1, 100, "r1")
        crm.advance(opp, "lost", "r1")
        self.assertEqual(crm.log[-2], ("advance", opp, "r1"))
        self.assertEqual(crm.log[-1], ("assign", l2, "system"))

    def test_transfer_entry_precedes_assignments(self):
        crm = CRM(make_reps(("r1", "rep", 1), ("r2", "rep", 2), ("m1", "manager", 0)))
        l1 = crm.add_lead("a@x.com", "A", "referral", "r1")
        l2 = crm.add_lead("b@x.com", "B", "referral", "r1")  # r2
        crm.qualify(l1, "r1")
        opp = crm.convert(l1, 100, "r1")
        crm.transfer(opp, "r2", "m1")
        self.assertEqual(crm.log[-1], ("transfer", opp, "m1"))
        self.assertEqual([e for e in crm.log if e[0] == "assign"], [])
        self.assertEqual(crm.leads[l2]["owner"], "r2")


class TestForecastRounding(unittest.TestCase):
    def test_weighted_rounds_down_at_each_stage(self):
        crm = CRM(make_reps(("r1", "rep", 10)))
        lead = crm.add_lead("a@x.com", "A", "referral", "r1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 101, "r1")
        self.assertEqual(crm.forecast()["weighted"], 101 * 10 // 100)
        crm.advance(opp, "proposal", "r1")
        self.assertEqual(crm.forecast()["weighted"], 101 * 30 // 100)
        crm.advance(opp, "negotiation", "r1")
        self.assertEqual(crm.forecast()["weighted"], 101 * 60 // 100)


if __name__ == "__main__":
    unittest.main()
