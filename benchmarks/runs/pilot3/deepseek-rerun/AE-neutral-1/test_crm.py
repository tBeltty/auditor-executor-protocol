import copy
import unittest

from crm import CRM, DuplicateLeadError


def crm_one_rep(capacity=10):
    return CRM([
        {"id": "r1", "role": "rep", "capacity": capacity},
        {"id": "m1", "role": "manager", "capacity": 5},
    ])


def crm_two_reps(cap1=5, cap2=5):
    return CRM([
        {"id": "r1", "role": "rep", "capacity": cap1},
        {"id": "r2", "role": "rep", "capacity": cap2},
        {"id": "m1", "role": "manager", "capacity": 5},
    ])


def make_qualified(crm, email="a@corp.com", name="A", source="referral", actor="r1"):
    lead_id = crm.add_lead(email, name, source, actor)
    crm.qualify(lead_id, actor)
    return lead_id


def make_opportunity(crm, amount=1000, email="a@corp.com", source="referral", actor="r1"):
    lead_id = make_qualified(crm, email=email, source=source, actor=actor)
    return crm.convert(lead_id, amount, actor)


class TestAddLead(unittest.TestCase):
    def test_basic_fields_and_log(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 2},
            {"id": "m1", "role": "manager", "capacity": 5},
        ])
        lead_id = crm.add_lead(" Alice@Corp.COM ", " Alice ", "web", "r1")
        self.assertEqual(lead_id, "L1")
        self.assertEqual(crm.leads["L1"], {
            "id": "L1",
            "email": "alice@corp.com",
            "name": "Alice",
            "source": "web",
            "score": 25,
            "owner": "r1",
            "status": "new",
        })
        self.assertEqual(crm.log, [("add_lead", "L1", "r1")])

    def test_scores(self):
        crm = crm_one_rep()
        cases = [
            ("a@gmail.com", "web", 10),
            ("b@yahoo.com", "referral", 30),
            ("c@outlook.com", "event", 20),
            ("d@corp.com", "referral", 45),
            ("e@corp.com", "event", 35),
            ("f@gmail.com", "web", 10),
        ]
        for email, source, expected in cases:
            lead_id = crm.add_lead(email, "N", source, "r1")
            self.assertEqual(crm.leads[lead_id]["score"], expected, email)

    def test_failed_creation_does_not_consume_id(self):
        crm = crm_one_rep()
        with self.assertRaises(ValueError):
            crm.add_lead("not-an-email", "A", "web", "r1")
        first = crm.add_lead("a@corp.com", "A", "web", "r1")
        self.assertEqual(first, "L1")
        with self.assertRaises(DuplicateLeadError):
            crm.add_lead("A@CORP.com", "B", "web", "r1")
        second = crm.add_lead("b@corp.com", "B", "web", "r1")
        self.assertEqual(second, "L2")

    def test_duplicate_normalized_email(self):
        crm = crm_one_rep()
        crm.add_lead("Alice@Corp.com", "Alice", "web", "r1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            crm.add_lead("  alice@corp.COM  ", "Other", "referral", "r1")
        self.assertEqual(ctx.exception.existing_id, "L1")
        self.assertEqual(len(crm.leads), 1)
        self.assertEqual(crm.log, [("add_lead", "L1", "r1")])

    def test_email_validation(self):
        invalid = [
            None,
            123,
            "",
            "   ",
            "plain",
            "a@b@c.com",
            "@corp.com",
            "a@",
            "a@corp",
            "a@.corp.com",
            "a@corp.",
        ]
        for email in invalid:
            crm = crm_one_rep()
            with self.assertRaises(ValueError, msg=repr(email)):
                crm.add_lead(email, "A", "web", "r1")
            self.assertEqual(crm.leads, {})

    def test_valid_email_shapes(self):
        crm = crm_one_rep()
        for email in ["a@b.co", "first.last@sub.corp.com", "x+y@z.io"]:
            lead_id = crm.add_lead(email, "A", "web", "r1")
            self.assertEqual(crm.leads[lead_id]["email"], email.lower())

    def test_name_validation(self):
        for name in [None, 5, "", "   "]:
            crm = crm_one_rep()
            with self.assertRaises(ValueError, msg=repr(name)):
                crm.add_lead("a@corp.com", name, "web", "r1")
            self.assertEqual(crm.leads, {})

    def test_source_validation(self):
        for source in [None, "Web", "email", "", 3]:
            crm = crm_one_rep()
            with self.assertRaises(ValueError, msg=repr(source)):
                crm.add_lead("a@corp.com", "A", source, "r1")
            self.assertEqual(crm.leads, {})

    def test_unknown_actor_is_checked_first(self):
        crm = crm_one_rep()
        with self.assertRaises(PermissionError):
            crm.add_lead("bad", "", "bogus", "nobody")
        self.assertEqual(crm.leads, {})
        self.assertEqual(crm.log, [])

    def test_duplicate_checked_against_converted_leads(self):
        crm = crm_one_rep()
        lead_id = make_qualified(crm)
        crm.convert(lead_id, 100, "r1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            crm.add_lead("a@corp.com", "Again", "web", "r1")
        self.assertEqual(ctx.exception.existing_id, lead_id)

    def test_all_reps_at_zero_capacity_queues_everything(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 0},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        lead_id = crm.add_lead("a@corp.com", "A", "web", "m1")
        self.assertIsNone(crm.leads[lead_id]["owner"])

    def test_owner_choice_lowest_load_and_tie_by_id(self):
        crm = CRM([
            {"id": "b", "role": "rep", "capacity": 5},
            {"id": "a", "role": "rep", "capacity": 5},
            {"id": "m1", "role": "manager", "capacity": 5},
        ])
        first = crm.add_lead("1@corp.com", "N", "web", "m1")
        second = crm.add_lead("2@corp.com", "N", "web", "m1")
        third = crm.add_lead("3@corp.com", "N", "web", "m1")
        self.assertEqual(crm.leads[first]["owner"], "a")
        self.assertEqual(crm.leads[second]["owner"], "b")
        self.assertEqual(crm.leads[third]["owner"], "a")

    def test_capacity_and_waiting_queue(self):
        crm = crm_two_reps(cap1=1, cap2=1)
        l1 = crm.add_lead("1@corp.com", "N", "web", "m1")
        l2 = crm.add_lead("2@corp.com", "N", "web", "m1")
        l3 = crm.add_lead("3@corp.com", "N", "web", "m1")
        self.assertEqual(crm.leads[l1]["owner"], "r1")
        self.assertEqual(crm.leads[l2]["owner"], "r2")
        self.assertIsNone(crm.leads[l3]["owner"])

    def test_managers_never_own(self):
        crm = CRM([
            {"id": "m1", "role": "manager", "capacity": 10},
        ])
        lead_id = crm.add_lead("a@corp.com", "A", "web", "m1")
        self.assertIsNone(crm.leads[lead_id]["owner"])


class TestQualify(unittest.TestCase):
    def setUp(self):
        self.crm = crm_two_reps()
        self.lead_id = self.crm.add_lead("a@corp.com", "A", "referral", "m1")

    def test_owner_can_qualify(self):
        self.crm.qualify(self.lead_id, "r1")
        self.assertEqual(self.crm.leads[self.lead_id]["status"], "qualified")
        self.assertEqual(self.crm.log[-1], ("qualify", self.lead_id, "r1"))

    def test_manager_can_qualify(self):
        self.crm.qualify(self.lead_id, "m1")
        self.assertEqual(self.crm.leads[self.lead_id]["status"], "qualified")

    def test_unknown_lead(self):
        with self.assertRaises(ValueError):
            self.crm.qualify("L999", "r1")

    def test_unknown_actor_checked_first(self):
        with self.assertRaises(PermissionError):
            self.crm.qualify("L999", "nobody")

    def test_non_owner_rep_forbidden(self):
        with self.assertRaises(PermissionError):
            self.crm.qualify(self.lead_id, "r2")
        self.assertEqual(self.crm.leads[self.lead_id]["status"], "new")

    def test_already_qualified(self):
        self.crm.qualify(self.lead_id, "r1")
        with self.assertRaises(ValueError):
            self.crm.qualify(self.lead_id, "r1")
        self.assertEqual(self.crm.leads[self.lead_id]["status"], "qualified")

    def test_converted_lead_cannot_be_qualified(self):
        self.crm.qualify(self.lead_id, "r1")
        self.crm.convert(self.lead_id, 100, "r1")
        with self.assertRaises(ValueError):
            self.crm.qualify(self.lead_id, "r1")

    def test_score_below_threshold(self):
        crm = crm_one_rep()
        lead_id = crm.add_lead("a@gmail.com", "A", "web", "r1")
        before = copy.deepcopy(crm.log)
        with self.assertRaises(ValueError):
            crm.qualify(lead_id, "r1")
        self.assertEqual(crm.leads[lead_id]["status"], "new")
        self.assertEqual(crm.log, before)

    def test_score_at_threshold(self):
        crm = crm_one_rep()
        lead_id = crm.add_lead("a@gmail.com", "A", "referral", "r1")
        crm.qualify(lead_id, "r1")
        self.assertEqual(crm.leads[lead_id]["status"], "qualified")

    def test_ownerless_lead_can_be_qualified_by_manager(self):
        crm = CRM([{"id": "m1", "role": "manager", "capacity": 5}])
        lead_id = crm.add_lead("a@corp.com", "A", "referral", "m1")
        crm.qualify(lead_id, "m1")
        self.assertEqual(crm.leads[lead_id]["status"], "qualified")


class TestConvert(unittest.TestCase):
    def setUp(self):
        self.crm = crm_two_reps()
        self.lead_id = make_qualified(self.crm)

    def test_success(self):
        opp_id = self.crm.convert(self.lead_id, 2500, "r1")
        self.assertEqual(opp_id, "O1")
        self.assertEqual(self.crm.opps["O1"], {
            "id": "O1",
            "lead_id": self.lead_id,
            "owner": "r1",
            "amount": 2500,
            "original_amount": 2500,
            "stage": "prospect",
        })
        self.assertEqual(self.crm.leads[self.lead_id]["status"], "converted")
        self.assertEqual(self.crm.log[-1], ("convert", "O1", "r1"))

    def test_manager_can_convert(self):
        opp_id = self.crm.convert(self.lead_id, 100, "m1")
        self.assertEqual(self.crm.opps[opp_id]["owner"], "r1")
        self.assertEqual(self.crm.log[-1], ("convert", opp_id, "m1"))

    def test_unknown_lead(self):
        with self.assertRaises(ValueError):
            self.crm.convert("L999", 100, "r1")

    def test_unknown_actor_checked_first(self):
        with self.assertRaises(PermissionError):
            self.crm.convert("L999", -1, "nobody")

    def test_invalid_amounts(self):
        for amount in [0, -5, True, False, 1.5, "100", None]:
            with self.assertRaises(ValueError, msg=repr(amount)):
                self.crm.convert(self.lead_id, amount, "r1")
        self.assertEqual(self.crm.opps, {})
        self.assertEqual(self.crm.leads[self.lead_id]["status"], "qualified")

    def test_non_owner_rep_forbidden(self):
        with self.assertRaises(PermissionError):
            self.crm.convert(self.lead_id, 100, "r2")
        self.assertEqual(self.crm.opps, {})

    def test_must_be_qualified(self):
        crm = crm_one_rep()
        lead_id = crm.add_lead("a@corp.com", "A", "referral", "r1")
        with self.assertRaises(ValueError):
            crm.convert(lead_id, 100, "r1")
        self.assertEqual(crm.opps, {})

    def test_ownerless_lead_cannot_convert(self):
        crm = CRM([{"id": "m1", "role": "manager", "capacity": 5}])
        lead_id = crm.add_lead("a@corp.com", "A", "referral", "m1")
        crm.qualify(lead_id, "m1")
        with self.assertRaises(ValueError):
            crm.convert(lead_id, 100, "m1")
        self.assertEqual(crm.leads[lead_id]["status"], "qualified")
        self.assertEqual(crm.opps, {})

    def test_sequence_increments_only_on_success(self):
        with self.assertRaises(ValueError):
            self.crm.convert(self.lead_id, 0, "r1")
        first = self.crm.convert(self.lead_id, 100, "r1")
        self.assertEqual(first, "O1")
        second_lead = make_qualified(self.crm, email="b@corp.com", actor="m1")
        second = self.crm.convert(second_lead, 200, "m1")
        self.assertEqual(second, "O2")


class TestAdvance(unittest.TestCase):
    def setUp(self):
        self.crm = crm_two_reps()
        self.opp_id = make_opportunity(self.crm, amount=1000)

    def test_happy_path_to_won(self):
        self.crm.advance(self.opp_id, "proposal", "r1")
        self.crm.advance(self.opp_id, "negotiation", "r1")
        self.crm.advance(self.opp_id, "won", "r1")
        self.assertEqual(self.crm.opps[self.opp_id]["stage"], "won")
        self.assertEqual(
            self.crm.log[-3:],
            [
                ("advance", self.opp_id, "r1"),
                ("advance", self.opp_id, "r1"),
                ("advance", self.opp_id, "r1"),
            ],
        )

    def test_lost_from_any_non_final(self):
        self.crm.advance(self.opp_id, "lost", "r1")
        self.assertEqual(self.crm.opps[self.opp_id]["stage"], "lost")

    def test_final_cannot_advance(self):
        self.crm.advance(self.opp_id, "lost", "r1")
        log_before = copy.deepcopy(self.crm.log)
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp_id, "won", "r1")
        self.assertEqual(self.crm.opps[self.opp_id]["stage"], "lost")
        self.assertEqual(self.crm.log, log_before)

    def test_unknown_opp(self):
        with self.assertRaises(ValueError):
            self.crm.advance("O999", "proposal", "r1")

    def test_unknown_actor_checked_first(self):
        with self.assertRaises(PermissionError):
            self.crm.advance("O999", "bogus", "nobody")

    def test_invalid_stage_names(self):
        for stage in ["Won", "closed", "", None, 1]:
            with self.assertRaises(ValueError, msg=repr(stage)):
                self.crm.advance(self.opp_id, stage, "r1")
        self.assertEqual(self.crm.opps[self.opp_id]["stage"], "prospect")

    def test_non_owner_rep_forbidden(self):
        with self.assertRaises(PermissionError):
            self.crm.advance(self.opp_id, "proposal", "r2")
        self.assertEqual(self.crm.opps[self.opp_id]["stage"], "prospect")

    def test_manager_can_advance(self):
        self.crm.advance(self.opp_id, "proposal", "m1")
        self.assertEqual(self.crm.opps[self.opp_id]["stage"], "proposal")

    def test_invalid_transitions(self):
        for stage in ["negotiation", "won", "prospect"]:
            with self.assertRaises(ValueError, msg=stage):
                self.crm.advance(self.opp_id, stage, "r1")
            self.assertEqual(self.crm.opps[self.opp_id]["stage"], "prospect", stage)
        self.crm.advance(self.opp_id, "proposal", "r1")
        for stage in ["won", "prospect"]:
            with self.assertRaises(ValueError, msg=stage):
                self.crm.advance(self.opp_id, stage, "r1")
            self.assertEqual(self.crm.opps[self.opp_id]["stage"], "proposal", stage)
        self.assertEqual(self.crm.opps[self.opp_id]["stage"], "proposal")

    def test_negotiation_over_50000_needs_manager(self):
        crm = crm_two_reps()
        opp_id = make_opportunity(crm, amount=50001)
        crm.advance(opp_id, "proposal", "r1")
        before = copy.deepcopy(crm.log)
        with self.assertRaises(PermissionError):
            crm.advance(opp_id, "negotiation", "r1")
        self.assertEqual(crm.opps[opp_id]["stage"], "proposal")
        self.assertEqual(crm.log, before)
        crm.advance(opp_id, "negotiation", "m1")
        self.assertEqual(crm.opps[opp_id]["stage"], "negotiation")

    def test_negotiation_at_50000_allowed_for_rep(self):
        crm = crm_two_reps()
        opp_id = make_opportunity(crm, amount=50000)
        crm.advance(opp_id, "proposal", "r1")
        crm.advance(opp_id, "negotiation", "r1")
        self.assertEqual(crm.opps[opp_id]["stage"], "negotiation")

    def test_won_frees_one_slot_and_assigns_fifo(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 5},
        ])
        lead_a = crm.add_lead("a@corp.com", "A", "referral", "m1")
        lead_b = crm.add_lead("b@corp.com", "B", "referral", "m1")
        lead_c = crm.add_lead("c@corp.com", "C", "referral", "m1")
        self.assertEqual(crm.leads[lead_a]["owner"], "r1")
        self.assertIsNone(crm.leads[lead_b]["owner"])
        self.assertIsNone(crm.leads[lead_c]["owner"])
        crm.qualify(lead_a, "r1")
        opp_id = crm.convert(lead_a, 1000, "r1")
        crm.advance(opp_id, "proposal", "r1")
        crm.advance(opp_id, "negotiation", "r1")
        crm.advance(opp_id, "won", "r1")
        self.assertEqual(crm.leads[lead_b]["owner"], "r1")
        self.assertIsNone(crm.leads[lead_c]["owner"])
        self.assertEqual(crm.log[-2:], [
            ("advance", opp_id, "r1"),
            ("assign", lead_b, "system"),
        ])

    def test_manager_advance_frees_owner_slot(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 5},
        ])
        lead_a = crm.add_lead("a@corp.com", "A", "referral", "m1")
        lead_b = crm.add_lead("b@corp.com", "B", "referral", "m1")
        crm.qualify(lead_a, "r1")
        opp_id = crm.convert(lead_a, 100, "r1")
        crm.advance(opp_id, "lost", "m1")
        self.assertEqual(crm.leads[lead_b]["owner"], "r1")
        self.assertEqual(crm.log[-1], ("assign", lead_b, "system"))


class TestDiscount(unittest.TestCase):
    def setUp(self):
        self.crm = crm_two_reps()
        self.opp_id = make_opportunity(self.crm, amount=1000)

    def test_rep_discount(self):
        self.crm.discount(self.opp_id, 10, "r1")
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 900)
        self.assertEqual(self.crm.opps[self.opp_id]["original_amount"], 1000)
        self.assertEqual(self.crm.log[-1], ("discount", self.opp_id, "r1"))

    def test_manager_discount_30(self):
        self.crm.discount(self.opp_id, 30, "m1")
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 700)

    def test_rounding_floor(self):
        crm = crm_two_reps()
        opp_id = make_opportunity(crm, amount=999)
        crm.discount(opp_id, 10, "m1")
        self.assertEqual(crm.opps[opp_id]["amount"], 899)

    def test_invalid_pct(self):
        for pct in [0, 31, -1, True, False, 1.5, "10", None]:
            with self.assertRaises(ValueError, msg=repr(pct)):
                self.crm.discount(self.opp_id, pct, "r1")
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 1000)

    def test_unknown_opp(self):
        with self.assertRaises(ValueError):
            self.crm.discount("O999", 10, "r1")

    def test_unknown_actor_checked_first(self):
        with self.assertRaises(PermissionError):
            self.crm.discount("O999", 99, "nobody")

    def test_non_owner_rep_forbidden(self):
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp_id, 5, "r2")

    def test_final_stage(self):
        self.crm.advance(self.opp_id, "lost", "r1")
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp_id, 5, "r1")

    def test_rep_limited_to_10(self):
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp_id, 11, "r1")
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 1000)

    def test_cumulative_cap(self):
        self.crm.discount(self.opp_id, 30, "m1")
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 700)
        before = copy.deepcopy(self.crm.log)
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp_id, 1, "m1")
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 700)
        self.assertEqual(self.crm.log, before)

    def test_repeated_rep_discounts_stay_within_cumulative_cap(self):
        self.crm.discount(self.opp_id, 10, "r1")
        self.crm.discount(self.opp_id, 10, "r1")
        self.crm.discount(self.opp_id, 10, "r1")
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 729)
        self.assertEqual(self.crm.opps[self.opp_id]["original_amount"], 1000)


class TestTransfer(unittest.TestCase):
    def setUp(self):
        self.crm = crm_two_reps()
        self.opp_id = make_opportunity(self.crm, amount=1000)

    def test_success(self):
        self.crm.transfer(self.opp_id, "r2", "m1")
        self.assertEqual(self.crm.opps[self.opp_id]["owner"], "r2")
        self.assertEqual(self.crm.log[-1], ("transfer", self.opp_id, "m1"))

    def test_unknown_opp(self):
        with self.assertRaises(ValueError):
            self.crm.transfer("O999", "r2", "m1")

    def test_unknown_actor_checked_first(self):
        with self.assertRaises(PermissionError):
            self.crm.transfer("O999", "nobody", "nobody")

    def test_non_manager_forbidden(self):
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.opp_id, "r2", "r1")

    def test_new_owner_must_be_rep(self):
        self.crm.add_lead("x@corp.com", "X", "referral", "m1")
        for new_owner in ["m1", "unknown", None]:
            with self.assertRaises(ValueError, msg=repr(new_owner)):
                self.crm.transfer(self.opp_id, new_owner, "m1")
        self.assertEqual(self.crm.opps[self.opp_id]["owner"], "r1")

    def test_final_stage_forbidden(self):
        self.crm.advance(self.opp_id, "lost", "r1")
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp_id, "r2", "m1")

    def test_same_owner_forbidden(self):
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp_id, "r1", "m1")

    def test_new_owner_at_capacity(self):
        crm = crm_two_reps(cap2=0)
        opp_id = make_opportunity(crm)
        with self.assertRaises(ValueError):
            crm.transfer(opp_id, "r2", "m1")
        self.assertEqual(crm.opps[opp_id]["owner"], "r1")

    def test_manager_actor_required_even_for_own_nothing(self):
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.opp_id, "r2", "r2")


class TestForecast(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(crm_one_rep().forecast(), {"open": 0, "weighted": 0, "won": 0})

    def test_mixed_pipeline(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 10},
            {"id": "m1", "role": "manager", "capacity": 5},
        ])
        opps = []
        for i, amount in enumerate([1000, 999, 500, 700, 800], start=1):
            lead_id = crm.add_lead("%d@corp.com" % i, "N", "referral", "r1")
            crm.qualify(lead_id, "r1")
            opps.append(crm.convert(lead_id, amount, "r1"))
        crm.advance(opps[1], "proposal", "r1")
        crm.advance(opps[2], "proposal", "r1")
        crm.advance(opps[2], "negotiation", "r1")
        crm.advance(opps[3], "proposal", "r1")
        crm.advance(opps[3], "negotiation", "r1")
        crm.advance(opps[3], "won", "r1")
        crm.advance(opps[4], "lost", "r1")
        self.assertEqual(crm.forecast(), {"open": 3, "weighted": 699, "won": 700})

    def test_forecast_has_no_log_entry(self):
        crm = crm_one_rep()
        before = copy.deepcopy(crm.log)
        crm.forecast()
        self.assertEqual(crm.log, before)


class TestAtomicityAndOrdering(unittest.TestCase):
    def test_failed_calls_change_nothing(self):
        crm = crm_two_reps()
        lead_id = make_qualified(crm)
        opp_id = crm.convert(lead_id, 1000, "r1")
        leads_before = copy.deepcopy(crm.leads)
        opps_before = copy.deepcopy(crm.opps)
        log_before = copy.deepcopy(crm.log)

        failures = [
            (ValueError, lambda: crm.add_lead("bad", "N", "web", "r1")),
            (ValueError, lambda: crm.qualify("L999", "r1")),
            (PermissionError, lambda: crm.qualify(lead_id, "r2")),
            (ValueError, lambda: crm.convert(lead_id, 0, "r1")),
            (PermissionError, lambda: crm.convert(lead_id, 10, "r2")),
            (ValueError, lambda: crm.advance(opp_id, "won", "r1")),
            (PermissionError, lambda: crm.advance(opp_id, "proposal", "r2")),
            (ValueError, lambda: crm.discount(opp_id, 0, "r1")),
            (PermissionError, lambda: crm.discount(opp_id, 10, "r2")),
            (PermissionError, lambda: crm.discount(opp_id, 20, "r1")),
            (PermissionError, lambda: crm.transfer(opp_id, "r2", "r2")),
            (ValueError, lambda: crm.transfer(opp_id, "r1", "m1")),
        ]
        for exc, call in failures:
            with self.assertRaises(exc, msg=call):
                call()
            self.assertEqual(crm.leads, leads_before)
            self.assertEqual(crm.opps, opps_before)
            self.assertEqual(crm.log, log_before)

    def test_actor_checked_before_arguments_everywhere(self):
        crm = crm_two_reps()
        calls = [
            lambda: crm.qualify("L999", "ghost"),
            lambda: crm.convert("L999", -1, "ghost"),
            lambda: crm.advance("O999", "bogus", "ghost"),
            lambda: crm.discount("O999", 500, "ghost"),
            lambda: crm.transfer("O999", "ghost", "ghost"),
        ]
        for call in calls:
            with self.assertRaises(PermissionError, msg=call):
                call()

    def test_no_implicit_assignment_on_convert(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 5},
        ])
        lead_a = crm.add_lead("a@corp.com", "A", "referral", "m1")
        lead_b = crm.add_lead("b@corp.com", "B", "referral", "m1")
        crm.qualify(lead_a, "r1")
        crm.convert(lead_a, 100, "r1")
        # Conversion frees load but the spec only assigns on advance/transfer.
        self.assertIsNone(crm.leads[lead_b]["owner"])
        self.assertNotIn(("assign", lead_b, "system"), crm.log)


if __name__ == "__main__":
    unittest.main()
