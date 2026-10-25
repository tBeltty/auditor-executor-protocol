import unittest

from crm import CRM, DuplicateLeadError


def reps_default():
    return [
        {"id": "r1", "role": "rep", "capacity": 5},
        {"id": "r2", "role": "rep", "capacity": 5},
        {"id": "m1", "role": "manager", "capacity": 0},
    ]


def make_crm(reps=None):
    return CRM(reps if reps is not None else reps_default())


def add(crm, email="lead@corp.com", name="Lead", source="referral", actor="r1"):
    return crm.add_lead(email, name, source, actor)


def qualified_opp(crm, email="lead@corp.com", amount=1000, actor="r1"):
    lead_id = add(crm, email=email, actor=actor)
    crm.qualify(lead_id, actor)
    return crm.convert(lead_id, amount, actor)


class TestAddLead(unittest.TestCase):
    def test_unknown_actor_checked_first(self):
        crm = make_crm()
        with self.assertRaises(PermissionError):
            crm.add_lead("not-an-email", "", "bogus", "ghost")
        self.assertEqual(crm.leads, {})
        self.assertEqual(crm.log, [])

    def test_email_must_be_str(self):
        crm = make_crm()
        with self.assertRaises(ValueError):
            crm.add_lead(123, "Name", "web", "r1")

    def test_invalid_emails(self):
        crm = make_crm()
        for email in [
            "no-at-sign",
            "a@@b.com",
            "@b.com",
            "a@bcom",
            "a@.com",
            "a@com.",
            "a@b.",
            "a@.b",
            "two@at@b.com",
            "",
        ]:
            with self.subTest(email=email):
                with self.assertRaises(ValueError):
                    crm.add_lead(email, "Name", "web", "r1")
        self.assertEqual(crm.leads, {})

    def test_email_normalization_and_name_strip(self):
        crm = make_crm()
        lead_id = crm.add_lead("  Alice@Example.COM  ", "  Alice  ", "web", "r1")
        lead = crm.leads[lead_id]
        self.assertEqual(lead["email"], "alice@example.com")
        self.assertEqual(lead["name"], "Alice")
        self.assertEqual(lead["status"], "new")

    def test_name_validation(self):
        crm = make_crm()
        for name in ["", "   ", None, 5]:
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    crm.add_lead("a@b.com", name, "web", "r1")

    def test_source_validation(self):
        crm = make_crm()
        for source in ["Web", "email", "", None]:
            with self.subTest(source=source):
                with self.assertRaises(ValueError):
                    crm.add_lead("a@b.com", "Name", source, "r1")

    def test_scores(self):
        crm = make_crm()
        cases = [
            ("web", "a@gmail.com", 10),
            ("web", "b@corp.com", 25),
            ("referral", "c@yahoo.com", 30),
            ("referral", "d@corp.com", 45),
            ("event", "e@outlook.com", 20),
            ("event", "f@corp.com", 35),
        ]
        for source, email, expected in cases:
            with self.subTest(email=email):
                lead_id = add(crm, email=email, source=source)
                self.assertEqual(crm.leads[lead_id]["score"], expected)

    def test_duplicate_email(self):
        crm = make_crm()
        lead_id = add(crm, email="Dup@Corp.com")
        before_log = list(crm.log)
        before_leads = dict(crm.leads)
        with self.assertRaises(DuplicateLeadError) as ctx:
            crm.add_lead("  dup@corp.COM ", "Other", "web", "r1")
        self.assertEqual(ctx.exception.existing_id, lead_id)
        self.assertEqual(crm.log, before_log)
        self.assertEqual(crm.leads, before_leads)

    def test_ids_count_only_successes(self):
        crm = make_crm()
        with self.assertRaises(ValueError):
            crm.add_lead("bad", "Name", "web", "r1")
        self.assertEqual(add(crm, email="a@corp.com"), "L1")
        with self.assertRaises(ValueError):
            crm.add_lead("a@corp.com", "", "web", "r1")
        self.assertEqual(add(crm, email="b@corp.com"), "L2")

    def test_owner_is_least_loaded_with_tie_break(self):
        crm = make_crm(
            [
                {"id": "r2", "role": "rep", "capacity": 2},
                {"id": "r1", "role": "rep", "capacity": 2},
            ]
        )
        owners = [
            crm.leads[add(crm, email="%s@corp.com" % c)]["owner"]
            for c in ("a", "b", "c", "d")
        ]
        self.assertEqual(owners, ["r1", "r2", "r1", "r2"])

    def test_waiting_queue_when_no_capacity(self):
        crm = make_crm([{"id": "r1", "role": "rep", "capacity": 1}])
        first = add(crm, email="a@corp.com")
        self.assertEqual(crm.leads[first]["owner"], "r1")
        second = add(crm, email="b@corp.com")
        self.assertIsNone(crm.leads[second]["owner"])
        self.assertEqual(crm.log[-1], ("add_lead", second, "r1"))

    def test_managers_never_own(self):
        crm = make_crm(
            [
                {"id": "m1", "role": "manager", "capacity": 10},
                {"id": "r1", "role": "rep", "capacity": 1},
            ]
        )
        first = add(crm, email="a@corp.com", actor="m1")
        second = add(crm, email="b@corp.com", actor="m1")
        self.assertEqual(crm.leads[first]["owner"], "r1")
        self.assertIsNone(crm.leads[second]["owner"])

    def test_log_entry(self):
        crm = make_crm()
        lead_id = add(crm)
        self.assertEqual(crm.log, [("add_lead", lead_id, "r1")])


class TestQualify(unittest.TestCase):
    def test_unknown_actor_first(self):
        crm = make_crm()
        with self.assertRaises(PermissionError):
            crm.qualify("nope", "ghost")

    def test_unknown_lead(self):
        crm = make_crm()
        with self.assertRaises(ValueError):
            crm.qualify("L404", "r1")

    def test_permission(self):
        crm = make_crm([{"id": "r1", "role": "rep", "capacity": 5},
                        {"id": "r2", "role": "rep", "capacity": 5},
                        {"id": "m1", "role": "manager", "capacity": 0}])
        lead_id = add(crm, email="a@corp.com", actor="r1")
        with self.assertRaises(PermissionError):
            crm.qualify(lead_id, "r2")
        self.assertEqual(crm.leads[lead_id]["status"], "new")
        self.assertEqual(len(crm.log), 1)

    def test_manager_can_qualify(self):
        crm = make_crm()
        lead_id = add(crm)
        crm.qualify(lead_id, "m1")
        self.assertEqual(crm.leads[lead_id]["status"], "qualified")
        self.assertEqual(crm.log[-1], ("qualify", lead_id, "m1"))

    def test_status_must_be_new(self):
        crm = make_crm()
        lead_id = add(crm)
        crm.qualify(lead_id, "r1")
        with self.assertRaises(ValueError):
            crm.qualify(lead_id, "r1")
        self.assertEqual(len(crm.log), 2)

    def test_score_must_be_at_least_30(self):
        crm = make_crm([{"id": "r1", "role": "rep", "capacity": 5}])
        for source, email in [("web", "a@gmail.com"), ("event", "b@outlook.com")]:
            lead_id = add(crm, email=email, source=source)
            with self.subTest(source=source):
                with self.assertRaises(ValueError):
                    crm.qualify(lead_id, "r1")
                self.assertEqual(crm.leads[lead_id]["status"], "new")

    def test_score_exactly_30_passes(self):
        crm = make_crm()
        lead_id = add(crm, email="a@yahoo.com", source="referral")
        crm.qualify(lead_id, "r1")
        self.assertEqual(crm.leads[lead_id]["status"], "qualified")

    def test_ownerless_lead_can_be_qualified_by_manager(self):
        crm = make_crm([{"id": "m1", "role": "manager", "capacity": 0}])
        lead_id = add(crm, actor="m1")
        self.assertIsNone(crm.leads[lead_id]["owner"])
        crm.qualify(lead_id, "m1")
        self.assertEqual(crm.leads[lead_id]["status"], "qualified")


class TestConvert(unittest.TestCase):
    def test_unknown_actor_first(self):
        crm = make_crm()
        with self.assertRaises(PermissionError):
            crm.convert("L404", -1, "ghost")

    def test_unknown_lead(self):
        crm = make_crm()
        with self.assertRaises(ValueError):
            crm.convert("L404", 100, "r1")

    def test_amount_validation(self):
        crm = make_crm()
        lead_id = add(crm)
        crm.qualify(lead_id, "r1")
        for amount in [0, -1, 1.5, "100", True, False, None]:
            with self.subTest(amount=amount):
                with self.assertRaises(ValueError):
                    crm.convert(lead_id, amount, "r1")
        self.assertEqual(crm.opps, {})
        self.assertEqual(crm.leads[lead_id]["status"], "qualified")

    def test_permission(self):
        crm = make_crm([{"id": "r1", "role": "rep", "capacity": 5},
                        {"id": "r2", "role": "rep", "capacity": 5},
                        {"id": "m1", "role": "manager", "capacity": 0}])
        lead_id = add(crm, email="a@corp.com", actor="r1")
        crm.qualify(lead_id, "r1")
        with self.assertRaises(PermissionError):
            crm.convert(lead_id, 100, "r2")

    def test_status_must_be_qualified(self):
        crm = make_crm()
        lead_id = add(crm)
        with self.assertRaises(ValueError):
            crm.convert(lead_id, 100, "r1")

    def test_owner_required(self):
        crm = make_crm([{"id": "m1", "role": "manager", "capacity": 0}])
        lead_id = add(crm, actor="m1")
        crm.qualify(lead_id, "m1")
        with self.assertRaises(ValueError):
            crm.convert(lead_id, 100, "m1")
        self.assertEqual(crm.opps, {})

    def test_success(self):
        crm = make_crm()
        lead_id = add(crm, email="a@corp.com")
        crm.qualify(lead_id, "r1")
        opp_id = crm.convert(lead_id, 2500, "r1")
        self.assertEqual(opp_id, "O1")
        self.assertEqual(
            crm.opps[opp_id],
            {
                "id": opp_id,
                "lead_id": lead_id,
                "owner": "r1",
                "amount": 2500,
                "original_amount": 2500,
                "stage": "prospect",
            },
        )
        self.assertEqual(crm.leads[lead_id]["status"], "converted")
        self.assertIn(("convert", opp_id, "r1"), crm.log)

    def test_opp_ids_count_only_successes(self):
        crm = make_crm([{"id": "r1", "role": "rep", "capacity": 5},
                        {"id": "m1", "role": "manager", "capacity": 0}])
        lead_id = add(crm, email="a@corp.com")
        crm.qualify(lead_id, "r1")
        with self.assertRaises(ValueError):
            crm.convert(lead_id, 0, "r1")
        self.assertEqual(crm.convert(lead_id, 10, "r1"), "O1")
        other = add(crm, email="b@corp.com")
        crm.qualify(other, "r1")
        self.assertEqual(crm.convert(other, 10, "r1"), "O2")

    def test_conversion_keeps_rep_at_capacity_through_opportunity(self):
        crm = make_crm([{"id": "r1", "role": "rep", "capacity": 1}])
        lead_id = add(crm, email="a@corp.com")
        crm.qualify(lead_id, "r1")
        crm.convert(lead_id, 100, "r1")
        follow_up = add(crm, email="b@corp.com")
        self.assertIsNone(crm.leads[follow_up]["owner"])


class TestAdvance(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm([{"id": "r1", "role": "rep", "capacity": 5},
                             {"id": "r2", "role": "rep", "capacity": 0},
                             {"id": "m1", "role": "manager", "capacity": 0}])
        self.opp_id = qualified_opp(self.crm, amount=1000, actor="r1")

    def test_unknown_actor_first(self):
        with self.assertRaises(PermissionError):
            self.crm.advance("O404", "bogus", "ghost")

    def test_unknown_opp(self):
        with self.assertRaises(ValueError):
            self.crm.advance("O404", "proposal", "r1")

    def test_invalid_stage(self):
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp_id, "qualified", "r1")
        self.assertEqual(self.crm.opps[self.opp_id]["stage"], "prospect")

    def test_permission(self):
        with self.assertRaises(PermissionError):
            self.crm.advance(self.opp_id, "proposal", "r2")

    def test_transitions(self):
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp_id, "negotiation", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp_id, "won", "r1")
        self.crm.advance(self.opp_id, "proposal", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp_id, "proposal", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp_id, "won", "r1")
        self.crm.advance(self.opp_id, "negotiation", "r1")
        self.crm.advance(self.opp_id, "won", "r1")
        self.assertEqual(self.crm.opps[self.opp_id]["stage"], "won")
        self.assertIn(("advance", self.opp_id, "r1"), self.crm.log)

    def test_lost_from_any_open_stage(self):
        self.crm.advance(self.opp_id, "lost", "r1")
        self.assertEqual(self.crm.opps[self.opp_id]["stage"], "lost")

    def test_final_stage_cannot_move(self):
        self.crm.advance(self.opp_id, "lost", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp_id, "prospect", "r1")

    def test_negotiation_above_50000_requires_manager(self):
        opp = qualified_opp(self.crm, email="big@corp.com", amount=50001, actor="r1")
        self.crm.advance(opp, "proposal", "r1")
        with self.assertRaises(PermissionError):
            self.crm.advance(opp, "negotiation", "r1")
        self.assertEqual(self.crm.opps[opp]["stage"], "proposal")
        self.crm.advance(opp, "negotiation", "m1")
        self.assertEqual(self.crm.opps[opp]["stage"], "negotiation")

    def test_negotiation_at_50000_allowed_for_rep(self):
        opp = qualified_opp(self.crm, email="limit@corp.com", amount=50000, actor="r1")
        self.crm.advance(opp, "proposal", "r1")
        self.crm.advance(opp, "negotiation", "r1")
        self.assertEqual(self.crm.opps[opp]["stage"], "negotiation")

    def test_win_frees_slot_and_assigns_queue_fifo(self):
        crm = make_crm([{"id": "r1", "role": "rep", "capacity": 1}])
        first_lead = add(crm, email="a@corp.com", actor="r1")
        crm.qualify(first_lead, "r1")
        opp = crm.convert(first_lead, 1000, "r1")
        queued_one = add(crm, email="b@corp.com", actor="r1")
        queued_two = add(crm, email="c@corp.com", actor="r1")
        self.assertIsNone(crm.leads[queued_one]["owner"])
        self.assertIsNone(crm.leads[queued_two]["owner"])

        crm.advance(opp, "proposal", "r1")
        crm.advance(opp, "negotiation", "r1")
        crm.advance(opp, "won", "r1")

        self.assertEqual(crm.leads[queued_one]["owner"], "r1")
        self.assertIsNone(crm.leads[queued_two]["owner"])
        self.assertEqual(crm.log[-2], ("advance", opp, "r1"))
        self.assertEqual(crm.log[-1], ("assign", queued_one, "system"))

    def test_lost_frees_slot_but_respects_capacity(self):
        crm = make_crm([{"id": "r1", "role": "rep", "capacity": 2}])
        opp_one = qualified_opp(crm, email="a@corp.com", actor="r1")
        opp_two = qualified_opp(crm, email="b@corp.com", actor="r1")
        queued_one = add(crm, email="c@corp.com", actor="r1")
        queued_two = add(crm, email="d@corp.com", actor="r1")
        self.assertIsNone(crm.leads[queued_one]["owner"])

        crm.advance(opp_one, "lost", "r1")
        self.assertEqual(crm.leads[queued_one]["owner"], "r1")
        self.assertIsNone(crm.leads[queued_two]["owner"])
        self.assertEqual(len([e for e in crm.log if e[0] == "assign"]), 1)
        self.assertEqual(crm.opps[opp_two]["stage"], "prospect")


class TestDiscount(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm([{"id": "r1", "role": "rep", "capacity": 5},
                             {"id": "r2", "role": "rep", "capacity": 5},
                             {"id": "m1", "role": "manager", "capacity": 0}])
        self.opp_id = qualified_opp(self.crm, amount=1000, actor="r1")

    def test_unknown_actor_first(self):
        with self.assertRaises(PermissionError):
            self.crm.discount("O404", 999, "ghost")

    def test_unknown_opp(self):
        with self.assertRaises(ValueError):
            self.crm.discount("O404", 5, "r1")

    def test_pct_validation(self):
        for pct in [0, 31, -1, True, 5.0, "5", None]:
            with self.subTest(pct=pct):
                with self.assertRaises(ValueError):
                    self.crm.discount(self.opp_id, pct, "r1")
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 1000)

    def test_permission(self):
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp_id, 5, "r2")

    def test_final_stage(self):
        self.crm.advance(self.opp_id, "lost", "r1")
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp_id, 5, "r1")

    def test_rep_cap_of_10_percent(self):
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp_id, 11, "r1")
        self.crm.discount(self.opp_id, 10, "r1")
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 900)
        self.assertEqual(self.crm.opps[self.opp_id]["original_amount"], 1000)
        self.assertEqual(self.crm.log[-1], ("discount", self.opp_id, "r1"))

    def test_manager_may_use_larger_pct(self):
        self.crm.discount(self.opp_id, 25, "m1")
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 750)

    def test_cumulative_limit(self):
        self.crm.discount(self.opp_id, 30, "m1")
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 700)
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp_id, 1, "m1")
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 700)

    def test_floor_division_edge(self):
        self.crm.discount(self.opp_id, 7, "r1")
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 930)


class TestTransfer(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm([{"id": "r1", "role": "rep", "capacity": 5},
                             {"id": "r2", "role": "rep", "capacity": 5},
                             {"id": "m1", "role": "manager", "capacity": 0}])
        self.opp_id = qualified_opp(self.crm, amount=1000, actor="r1")

    def test_unknown_actor_first(self):
        with self.assertRaises(PermissionError):
            self.crm.transfer("O404", "r2", "ghost")

    def test_unknown_opp(self):
        with self.assertRaises(ValueError):
            self.crm.transfer("O404", "r2", "m1")

    def test_manager_required(self):
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.opp_id, "r2", "r1")

    def test_new_owner_must_be_known_rep(self):
        for target in ["ghost", "m1", None]:
            with self.subTest(target=target):
                with self.assertRaises(ValueError):
                    self.crm.transfer(self.opp_id, target, "m1")
        self.assertEqual(self.crm.opps[self.opp_id]["owner"], "r1")

    def test_final_stage(self):
        self.crm.advance(self.opp_id, "proposal", "m1")
        self.crm.advance(self.opp_id, "negotiation", "m1")
        self.crm.advance(self.opp_id, "won", "m1")
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp_id, "r2", "m1")

    def test_same_owner(self):
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp_id, "r1", "m1")

    def test_capacity_required(self):
        crm = make_crm([{"id": "r1", "role": "rep", "capacity": 5},
                        {"id": "r2", "role": "rep", "capacity": 1},
                        {"id": "m1", "role": "manager", "capacity": 0}])
        crm.add_lead("seed@corp.com", "S", "referral", "m1")
        # r1 gets the seed (lowest id at equal load), so force one onto r2.
        crm.add_lead("seed2@corp.com", "S", "referral", "m1")
        opp = qualified_opp(crm, email="opp@corp.com", amount=100, actor="r1")
        self.assertEqual(crm.opps[opp]["owner"], "r1")
        self.assertEqual(crm._load("r2"), 1)
        with self.assertRaises(ValueError):
            crm.transfer(opp, "r2", "m1")

    def test_success_frees_previous_owner(self):
        crm = make_crm([{"id": "r1", "role": "rep", "capacity": 1},
                        {"id": "r2", "role": "rep", "capacity": 5},
                        {"id": "m1", "role": "manager", "capacity": 0}])
        lead = add(crm, email="a@corp.com", actor="r1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 1000, "r1")

        crm.transfer(opp, "r2", "m1")
        self.assertEqual(crm.opps[opp]["owner"], "r2")
        self.assertEqual(crm.log[-1], ("transfer", opp, "m1"))
        freed = add(crm, email="b@corp.com", actor="m1")
        self.assertEqual(crm.leads[freed]["owner"], "r1")


class TestForecast(unittest.TestCase):
    def test_empty(self):
        crm = make_crm()
        self.assertEqual(crm.forecast(), {"open": 0, "weighted": 0, "won": 0})
        self.assertEqual(crm.log, [])

    def test_weighted_and_won(self):
        crm = make_crm([{"id": "r1", "role": "rep", "capacity": 20},
                        {"id": "m1", "role": "manager", "capacity": 0}])
        prospect = qualified_opp(crm, email="a@corp.com", amount=1000, actor="r1")
        proposal = qualified_opp(crm, email="b@corp.com", amount=1000, actor="r1")
        crm.advance(proposal, "proposal", "r1")
        negotiation = qualified_opp(crm, email="c@corp.com", amount=1000, actor="r1")
        crm.advance(negotiation, "proposal", "r1")
        crm.advance(negotiation, "negotiation", "r1")
        won = qualified_opp(crm, email="d@corp.com", amount=2000, actor="r1")
        crm.advance(won, "proposal", "r1")
        crm.advance(won, "negotiation", "r1")
        crm.advance(won, "won", "r1")
        lost = qualified_opp(crm, email="e@corp.com", amount=5000, actor="r1")
        crm.advance(lost, "lost", "r1")

        result = crm.forecast()
        self.assertEqual(result["open"], 3)
        self.assertEqual(result["weighted"], 100 + 300 + 600)
        self.assertEqual(result["won"], 2000)

    def test_forecast_adds_no_log_entry(self):
        crm = make_crm()
        qualified_opp(crm, amount=1000, actor="r1")
        before = list(crm.log)
        crm.forecast()
        self.assertEqual(crm.log, before)


class TestAtomicity(unittest.TestCase):
    def test_failed_calls_change_nothing(self):
        crm = make_crm([{"id": "r1", "role": "rep", "capacity": 1},
                        {"id": "m1", "role": "manager", "capacity": 0}])
        lead = add(crm, email="a@corp.com", actor="r1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 1000, "r1")
        queued = add(crm, email="b@corp.com", actor="r1")

        snapshot = (
            {k: dict(v) for k, v in crm.leads.items()},
            {k: dict(v) for k, v in crm.opps.items()},
            list(crm.log),
        )
        for call in [
            lambda: crm.advance(opp, "won", "r1"),
            lambda: crm.discount(opp, 30, "r1"),
            lambda: crm.transfer(opp, "r1", "m1"),
            lambda: crm.qualify(queued, "r1"),
            lambda: crm.convert(queued, 10, "r1"),
        ]:
            with self.assertRaises(Exception):
                call()

        self.assertEqual(crm.leads, snapshot[0])
        self.assertEqual(crm.opps, snapshot[1])
        self.assertEqual(crm.log, snapshot[2])


class TestSpecEdgeCases(unittest.TestCase):
    def test_non_string_actor_is_permission_error_everywhere(self):
        crm = make_crm()
        lead = add(crm)
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 1000, "r1")
        for actor in [None, 123, [], {}]:
            with self.subTest(actor=actor):
                with self.assertRaises(PermissionError):
                    crm.add_lead("x@corp.com", "X", "web", actor)
                with self.assertRaises(PermissionError):
                    crm.qualify(lead, actor)
                with self.assertRaises(PermissionError):
                    crm.convert(lead, 1, actor)
                with self.assertRaises(PermissionError):
                    crm.advance(opp, "proposal", actor)
                with self.assertRaises(PermissionError):
                    crm.discount(opp, 5, actor)
                with self.assertRaises(PermissionError):
                    crm.transfer(opp, "r2", actor)

    def test_unhashable_or_non_string_ids_are_value_errors(self):
        crm = make_crm()
        lead = add(crm)
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 1000, "r1")
        for bad_id in [None, 7, [], {}]:
            with self.subTest(bad_id=bad_id):
                with self.assertRaises(ValueError):
                    crm.qualify(bad_id, "r1")
                with self.assertRaises(ValueError):
                    crm.convert(bad_id, 100, "r1")
                with self.assertRaises(ValueError):
                    crm.advance(bad_id, "proposal", "r1")
                with self.assertRaises(ValueError):
                    crm.discount(bad_id, 5, "r1")
                with self.assertRaises(ValueError):
                    crm.transfer(bad_id, "r2", "m1")
        with self.assertRaises(ValueError):
            crm.advance(opp, ["proposal"], "r1")
        with self.assertRaises(ValueError):
            crm.add_lead("a@corp.com", "A", ["web"], "r1")

    def test_tie_break_uses_string_order(self):
        crm = make_crm(
            [
                {"id": "r2", "role": "rep", "capacity": 5},
                {"id": "r10", "role": "rep", "capacity": 5},
            ]
        )
        owners = [
            crm.leads[add(crm, email="%s@corp.com" % c, actor="r10")]["owner"]
            for c in ("a", "b", "c", "d")
        ]
        self.assertEqual(owners, ["r10", "r2", "r10", "r2"])

    def test_converted_lead_is_still_a_duplicate(self):
        crm = make_crm()
        lead = add(crm, email="dup@corp.com")
        crm.qualify(lead, "r1")
        crm.convert(lead, 100, "r1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            crm.add_lead("DUP@CORP.COM", "Other", "event", "r1")
        self.assertEqual(ctx.exception.existing_id, lead)

    def test_converted_lead_cannot_be_qualified_again(self):
        crm = make_crm()
        lead = add(crm)
        crm.qualify(lead, "r1")
        crm.convert(lead, 100, "r1")
        with self.assertRaises(ValueError):
            crm.qualify(lead, "m1")

    def test_free_email_domain_match_is_case_insensitive(self):
        crm = make_crm()
        lead = add(crm, email="Person@GMail.COM", source="referral")
        self.assertEqual(crm.leads[lead]["score"], 30)

    def test_advance_lost_from_proposal_frees_slot_and_drains_queue(self):
        crm = make_crm([{"id": "r1", "role": "rep", "capacity": 2}])
        first = add(crm, email="a@corp.com")
        crm.qualify(first, "r1")
        opp = crm.convert(first, 1000, "r1")
        second = add(crm, email="b@corp.com")
        third = add(crm, email="c@corp.com")
        fourth = add(crm, email="d@corp.com")
        self.assertIsNone(crm.leads[third]["owner"])
        self.assertIsNone(crm.leads[fourth]["owner"])

        crm.advance(opp, "proposal", "r1")
        crm.advance(opp, "lost", "r1")

        self.assertEqual(crm.leads[second]["owner"], "r1")
        self.assertEqual(crm.leads[third]["owner"], "r1")
        self.assertIsNone(crm.leads[fourth]["owner"])
        self.assertEqual(crm.log[-2], ("advance", opp, "r1"))
        self.assertEqual(crm.log[-1], ("assign", third, "system"))

    def test_transfer_moves_only_the_opportunity(self):
        crm = make_crm()
        lead = add(crm, email="a@corp.com", actor="r1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 1000, "r1")
        crm.transfer(opp, "r2", "m1")
        self.assertEqual(crm.opps[opp]["owner"], "r2")
        self.assertEqual(crm.leads[lead]["owner"], "r1")
        self.assertEqual(crm.leads[lead]["status"], "converted")
        self.assertEqual(crm._load("r1"), 0)
        self.assertEqual(crm._load("r2"), 1)

    def test_forecast_uses_current_discounted_amount(self):
        crm = make_crm()
        lead = add(crm, email="a@corp.com")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 1000, "r1")
        crm.advance(opp, "proposal", "r1")
        crm.discount(opp, 10, "r1")
        self.assertEqual(crm.forecast(), {"open": 1, "weighted": 270, "won": 0})

    def test_discount_validation_precedes_permission(self):
        crm = make_crm()
        lead = add(crm, email="a@corp.com", actor="r1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 1000, "r1")
        # r2 is a known rep but not the owner: pct check (2) comes first.
        with self.assertRaises(ValueError):
            crm.discount(opp, 0, "r2")

    def test_advance_stage_validation_precedes_permission(self):
        crm = make_crm()
        lead = add(crm, email="a@corp.com", actor="r1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 1000, "r1")
        with self.assertRaises(ValueError):
            crm.advance(opp, "bogus", "r2")

    def test_convert_amount_validation_precedes_permission(self):
        crm = make_crm()
        lead = add(crm, email="a@corp.com", actor="r1")
        crm.qualify(lead, "r1")
        with self.assertRaises(ValueError):
            crm.convert(lead, 0, "r2")

    def test_add_lead_checks_email_before_name(self):
        crm = make_crm()
        with self.assertRaises(ValueError):
            crm.add_lead("bad-email", "", "web", "r1")


if __name__ == "__main__":
    unittest.main()
