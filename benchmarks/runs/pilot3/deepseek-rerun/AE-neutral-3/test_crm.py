import unittest

from crm import CRM, DuplicateLeadError


def make_reps():
    return [
        {"id": "r1", "role": "rep", "capacity": 2},
        {"id": "r2", "role": "rep", "capacity": 2},
        {"id": "m1", "role": "manager", "capacity": 0},
    ]


class CRMTestCase(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(make_reps())
        self._email_seq = 0

    def next_email(self):
        self._email_seq += 1
        return "lead%d@corp.com" % self._email_seq

    def add(self, email=None, name="Lead", source="referral", actor="m1"):
        if email is None:
            email = self.next_email()
        return self.crm.add_lead(email, name, source, actor)

    def make_opp(self, amount=1000, stage="prospect", actor="m1"):
        lead_id = self.add()
        self.crm.qualify(lead_id, actor)
        opp_id = self.crm.convert(lead_id, amount, actor)
        steps = {
            "prospect": [],
            "proposal": ["proposal"],
            "negotiation": ["proposal", "negotiation"],
            "won": ["proposal", "negotiation", "won"],
            "lost": ["lost"],
        }[stage]
        for step in steps:
            self.crm.advance(opp_id, step, actor)
        return opp_id


class TestPermissions(CRMTestCase):
    def test_unknown_actor_raises_permission_error_in_every_method(self):
        lead_id = self.add()
        self.crm.qualify(lead_id, "m1")
        opp_id = self.crm.convert(lead_id, 1000, "m1")
        before_log = list(self.crm.log)
        before_leads = dict(self.crm.leads)
        before_opps = dict(self.crm.opps)

        calls = [
            lambda: self.crm.add_lead("x@corp.com", "X", "web", "ghost"),
            lambda: self.crm.qualify(lead_id, "ghost"),
            lambda: self.crm.convert(lead_id, 10, "ghost"),
            lambda: self.crm.advance(opp_id, "proposal", "ghost"),
            lambda: self.crm.discount(opp_id, 5, "ghost"),
            lambda: self.crm.transfer(opp_id, "r2", "ghost"),
        ]
        for call in calls:
            with self.assertRaises(PermissionError):
                call()

        self.assertEqual(self.crm.log, before_log)
        self.assertEqual(self.crm.leads, before_leads)
        self.assertEqual(self.crm.opps, before_opps)


class TestAddLead(CRMTestCase):
    def test_valid_lead_is_normalized_scored_and_logged(self):
        lead_id = self.crm.add_lead("  Alice@Corp.COM ", "  Alice  ", "referral", "r1")

        self.assertEqual(lead_id, "L1")
        self.assertEqual(
            self.crm.leads["L1"],
            {
                "id": "L1",
                "email": "alice@corp.com",
                "name": "Alice",
                "source": "referral",
                "score": 45,
                "owner": "r1",
                "status": "new",
            },
        )
        self.assertEqual(self.crm.log, [("add_lead", "L1", "r1")])

    def test_invalid_email_values(self):
        invalid = [
            None,
            123,
            "",
            "   ",
            "plain",
            "a@b",
            "a@@b.com",
            "@corp.com",
            "a@.com",
            "a@corp.",
            "a@corp",
        ]
        for email in invalid:
            with self.subTest(email=email):
                crm = CRM(make_reps())
                with self.assertRaises(ValueError):
                    crm.add_lead(email, "Name", "web", "m1")
                self.assertEqual(crm.leads, {})
                self.assertEqual(crm.log, [])
                self.assertEqual(crm.waiting, [])

    def test_emails_accepted(self):
        accepted = ["a@b.co", "a.b@sub.example.com", " a@b.c "]
        for email in accepted:
            with self.subTest(email=email):
                crm = CRM(make_reps())
                lead_id = crm.add_lead(email, "Name", "web", "m1")
                self.assertIn(lead_id, crm.leads)
                self.assertEqual(crm.leads[lead_id]["email"], email.strip().lower())

    def test_invalid_name(self):
        for name in [None, 5, "", "   ", "\t\n"]:
            with self.subTest(name=name):
                crm = CRM(make_reps())
                with self.assertRaises(ValueError):
                    crm.add_lead("a@corp.com", name, "web", "m1")
                self.assertEqual(crm.leads, {})
                self.assertEqual(crm.log, [])

    def test_name_is_stripped(self):
        lead_id = self.add(name="  Grace Hopper  ")
        self.assertEqual(self.crm.leads[lead_id]["name"], "Grace Hopper")

    def test_invalid_source(self):
        for source in [None, "", "phone", "WEB", "web "] :
            with self.subTest(source=source):
                crm = CRM(make_reps())
                with self.assertRaises(ValueError):
                    crm.add_lead("a@corp.com", "Name", source, "m1")
                self.assertEqual(crm.leads, {})
                self.assertEqual(crm.log, [])

    def test_scores_by_source_and_domain(self):
        cases = [
            ("web", "gmail.com", 10),
            ("web", "yahoo.com", 10),
            ("web", "outlook.com", 10),
            ("web", "corp.com", 25),
            ("web", "b.c", 25),
            ("referral", "gmail.com", 30),
            ("referral", "corp.com", 45),
            ("event", "outlook.com", 20),
            ("event", "corp.com", 35),
        ]
        for source, domain, expected in cases:
            with self.subTest(source=source, domain=domain):
                crm = CRM(make_reps())
                lead_id = crm.add_lead("x@" + domain, "X", source, "m1")
                self.assertEqual(crm.leads[lead_id]["score"], expected)

    def test_duplicate_uses_normalized_email(self):
        first = self.add(email="Bob@Corp.com")
        with self.assertRaises(DuplicateLeadError) as ctx:
            self.add(email="  bob@CORP.com  ")
        self.assertEqual(ctx.exception.existing_id, first)
        self.assertEqual(len(self.crm.leads), 1)
        self.assertEqual(self.crm.log, [("add_lead", first, "m1")])

        second = self.add(email="bob@other.com")
        self.assertEqual(second, "L2")

    def test_owner_is_lowest_load_and_ties_use_smallest_id(self):
        ids = [self.add() for _ in range(4)]
        self.assertEqual([self.crm.leads[i]["owner"] for i in ids], ["r1", "r2", "r1", "r2"])

        fifth = self.add()
        self.assertIsNone(self.crm.leads[fifth]["owner"])
        self.assertEqual(self.crm.waiting, [fifth])
        self.assertEqual(self.crm.log[-1], ("add_lead", fifth, "m1"))

    def test_managers_never_receive_leads(self):
        crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 0},
                {"id": "m1", "role": "manager", "capacity": 5},
            ]
        )
        lead_id = crm.add_lead("a@corp.com", "A", "web", "m1")
        self.assertIsNone(crm.leads[lead_id]["owner"])
        self.assertEqual(crm.waiting, [lead_id])


class TestQualify(CRMTestCase):
    def test_unknown_lead(self):
        with self.assertRaises(ValueError):
            self.crm.qualify("L99", "m1")

    def test_owner_can_qualify(self):
        lead_id = self.add()
        self.crm.qualify(lead_id, "r1")
        self.assertEqual(self.crm.leads[lead_id]["status"], "qualified")
        self.assertEqual(self.crm.log[-1], ("qualify", lead_id, "r1"))

    def test_manager_can_qualify_any_lead(self):
        lead_id = self.add()
        self.crm.qualify(lead_id, "m1")
        self.assertEqual(self.crm.leads[lead_id]["status"], "qualified")

    def test_other_rep_cannot_qualify(self):
        lead_id = self.add()
        with self.assertRaises(PermissionError):
            self.crm.qualify(lead_id, "r2")
        self.assertEqual(self.crm.leads[lead_id]["status"], "new")
        self.assertEqual(len(self.crm.log), 1)

    def test_only_new_leads_can_be_qualified(self):
        lead_id = self.add()
        self.crm.qualify(lead_id, "r1")
        with self.assertRaises(ValueError):
            self.crm.qualify(lead_id, "m1")

    def test_low_score_cannot_be_qualified(self):
        lead_id = self.add(source="web", email="x@gmail.com")
        with self.assertRaises(ValueError):
            self.crm.qualify(lead_id, "m1")
        self.assertEqual(self.crm.leads[lead_id]["status"], "new")

    def test_unowned_lead_requires_manager(self):
        crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 0},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        lead_id = crm.add_lead("a@corp.com", "A", "referral", "m1")
        with self.assertRaises(PermissionError):
            crm.qualify(lead_id, "r1")
        crm.qualify(lead_id, "m1")
        self.assertEqual(crm.leads[lead_id]["status"], "qualified")


class TestConvert(CRMTestCase):
    def qualified_lead(self, actor="r1"):
        lead_id = self.add()
        self.crm.qualify(lead_id, actor)
        return lead_id

    def test_invalid_amounts_change_nothing(self):
        for amount in [True, False, 0, -1, 1.5, "10", None]:
            with self.subTest(amount=amount):
                crm = CRM(make_reps())
                lead_id = crm.add_lead("a@corp.com", "A", "referral", "m1")
                crm.qualify(lead_id, "m1")
                log_before = list(crm.log)
                with self.assertRaises(ValueError):
                    crm.convert(lead_id, amount, "m1")
                self.assertEqual(crm.opps, {})
                self.assertEqual(crm.leads[lead_id]["status"], "qualified")
                self.assertEqual(crm.log, log_before)

    def test_non_owner_rep_cannot_convert(self):
        lead_id = self.qualified_lead()
        with self.assertRaises(PermissionError):
            self.crm.convert(lead_id, 100, "r2")
        self.assertEqual(self.crm.opps, {})
        self.assertEqual(self.crm.leads[lead_id]["status"], "qualified")

    def test_amount_checked_before_permission(self):
        lead_id = self.qualified_lead()
        with self.assertRaises(ValueError):
            self.crm.convert(lead_id, True, "r2")

    def test_lead_must_be_qualified(self):
        lead_id = self.add()
        with self.assertRaises(ValueError):
            self.crm.convert(lead_id, 100, "m1")

    def test_unowned_qualified_lead_cannot_convert(self):
        crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 0},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        lead_id = crm.add_lead("a@corp.com", "A", "referral", "m1")
        crm.qualify(lead_id, "m1")
        with self.assertRaises(ValueError):
            crm.convert(lead_id, 100, "m1")
        self.assertEqual(crm.opps, {})
        self.assertEqual(crm.leads[lead_id]["status"], "qualified")

    def test_success_creates_opportunity(self):
        lead_id = self.qualified_lead()
        opp_id = self.crm.convert(lead_id, 5000, "r1")

        self.assertEqual(opp_id, "O1")
        self.assertEqual(
            self.crm.opps["O1"],
            {
                "id": "O1",
                "lead_id": lead_id,
                "owner": "r1",
                "amount": 5000,
                "original_amount": 5000,
                "stage": "prospect",
            },
        )
        self.assertEqual(self.crm.leads[lead_id]["status"], "converted")
        self.assertEqual(self.crm.log[-1], ("convert", "O1", "r1"))

    def test_manager_can_convert_and_ids_increment(self):
        lead1 = self.add()
        self.crm.qualify(lead1, "m1")
        self.assertEqual(self.crm.convert(lead1, 100, "m1"), "O1")

        lead2 = self.add()
        self.crm.qualify(lead2, "m1")
        self.assertEqual(self.crm.convert(lead2, 200, "m1"), "O2")


class TestAdvance(CRMTestCase):
    def test_unknown_opportunity(self):
        with self.assertRaises(ValueError):
            self.crm.advance("O99", "proposal", "m1")

    def test_invalid_stage(self):
        opp_id = self.make_opp()
        for stage in ["", "closed", None, "PROSPECT"]:
            with self.subTest(stage=stage):
                with self.assertRaises(ValueError):
                    self.crm.advance(opp_id, stage, "m1")
        self.assertEqual(self.crm.opps[opp_id]["stage"], "prospect")

    def test_non_owner_rep_cannot_advance(self):
        opp_id = self.make_opp()
        with self.assertRaises(PermissionError):
            self.crm.advance(opp_id, "proposal", "r2")
        self.assertEqual(self.crm.opps[opp_id]["stage"], "prospect")

    def test_stage_checked_before_permission(self):
        opp_id = self.make_opp()
        with self.assertRaises(ValueError):
            self.crm.advance(opp_id, "bogus", "r2")

    def test_valid_transition_path(self):
        opp_id = self.make_opp()
        self.crm.advance(opp_id, "proposal", "r1")
        self.assertEqual(self.crm.opps[opp_id]["stage"], "proposal")
        self.crm.advance(opp_id, "negotiation", "r1")
        self.assertEqual(self.crm.opps[opp_id]["stage"], "negotiation")
        self.crm.advance(opp_id, "won", "r1")
        self.assertEqual(self.crm.opps[opp_id]["stage"], "won")
        self.assertEqual(
            self.crm.log[-3:],
            [
                ("advance", opp_id, "r1"),
                ("advance", opp_id, "r1"),
                ("advance", opp_id, "r1"),
            ],
        )

    def test_invalid_transitions(self):
        opp_id = self.make_opp()
        for stage in ["won", "negotiation", "prospect"]:
            with self.subTest(stage=stage):
                with self.assertRaises(ValueError):
                    self.crm.advance(opp_id, stage, "m1")
        self.assertEqual(self.crm.opps[opp_id]["stage"], "prospect")

        self.crm.advance(opp_id, "proposal", "m1")
        for stage in ["prospect", "won", "proposal"]:
            with self.subTest(stage=stage):
                with self.assertRaises(ValueError):
                    self.crm.advance(opp_id, stage, "m1")
        self.assertEqual(self.crm.opps[opp_id]["stage"], "proposal")

    def test_lost_allowed_from_any_open_stage(self):
        for start, steps in [
            ("prospect", []),
            ("proposal", ["proposal"]),
            ("negotiation", ["proposal", "negotiation"]),
        ]:
            with self.subTest(start=start):
                crm = CRM(make_reps())
                lead = crm.add_lead("x@corp.com", "X", "referral", "m1")
                crm.qualify(lead, "m1")
                opp = crm.convert(lead, 100, "m1")
                for step in steps:
                    crm.advance(opp, step, "m1")
                crm.advance(opp, "lost", "m1")
                self.assertEqual(crm.opps[opp]["stage"], "lost")

    def test_final_stages_are_final(self):
        for final_stage in ["won", "lost"]:
            with self.subTest(final_stage=final_stage):
                crm = CRM(make_reps())
                lead = crm.add_lead("x@corp.com", "X", "referral", "m1")
                crm.qualify(lead, "m1")
                opp = crm.convert(lead, 100, "m1")
                if final_stage == "won":
                    for step in ["proposal", "negotiation", "won"]:
                        crm.advance(opp, step, "m1")
                else:
                    crm.advance(opp, "lost", "m1")
                for stage in ["prospect", "proposal", "negotiation", "won", "lost"]:
                    with self.assertRaises(ValueError):
                        crm.advance(opp, stage, "m1")

    def test_negotiation_above_threshold_requires_manager(self):
        opp_id = self.make_opp(amount=50001)
        self.crm.advance(opp_id, "proposal", "m1")
        with self.assertRaises(PermissionError):
            self.crm.advance(opp_id, "negotiation", "r1")
        self.assertEqual(self.crm.opps[opp_id]["stage"], "proposal")
        self.crm.advance(opp_id, "negotiation", "m1")
        self.assertEqual(self.crm.opps[opp_id]["stage"], "negotiation")

    def test_negotiation_threshold_is_strict(self):
        opp_id = self.make_opp(amount=50000)
        self.crm.advance(opp_id, "proposal", "m1")
        self.crm.advance(opp_id, "negotiation", "r1")
        self.assertEqual(self.crm.opps[opp_id]["stage"], "negotiation")

    def test_manager_can_advance_above_threshold(self):
        opp_id = self.make_opp(amount=90000)
        self.crm.advance(opp_id, "proposal", "m1")
        self.crm.advance(opp_id, "negotiation", "m1")
        self.assertEqual(self.crm.opps[opp_id]["stage"], "negotiation")

    def test_discount_can_bring_amount_below_threshold(self):
        opp_id = self.make_opp(amount=60000)
        self.crm.discount(opp_id, 20, "m1")
        self.assertEqual(self.crm.opps[opp_id]["amount"], 48000)
        self.crm.advance(opp_id, "proposal", "m1")
        self.crm.advance(opp_id, "negotiation", "r1")
        self.assertEqual(self.crm.opps[opp_id]["stage"], "negotiation")


class TestDiscount(CRMTestCase):
    def test_invalid_percentages(self):
        for pct in [True, False, 0, 31, -1, 1.5, "5", None]:
            with self.subTest(pct=pct):
                crm = CRM(make_reps())
                lead = crm.add_lead("x@corp.com", "X", "referral", "m1")
                crm.qualify(lead, "m1")
                opp = crm.convert(lead, 1000, "m1")
                log_before = list(crm.log)
                with self.assertRaises(ValueError):
                    crm.discount(opp, pct, "m1")
                self.assertEqual(crm.opps[opp]["amount"], 1000)
                self.assertEqual(crm.log, log_before)

    def test_other_rep_cannot_discount(self):
        opp_id = self.make_opp()
        with self.assertRaises(PermissionError):
            self.crm.discount(opp_id, 5, "r2")
        self.assertEqual(self.crm.opps[opp_id]["amount"], 1000)

    def test_non_manager_limited_to_ten(self):
        opp_id = self.make_opp()
        with self.assertRaises(PermissionError):
            self.crm.discount(opp_id, 11, "r1")
        self.crm.discount(opp_id, 10, "r1")
        self.assertEqual(self.crm.opps[opp_id]["amount"], 900)
        self.assertEqual(self.crm.log[-1], ("discount", opp_id, "r1"))

    def test_manager_can_discount_thirty(self):
        opp_id = self.make_opp()
        self.crm.discount(opp_id, 30, "m1")
        self.assertEqual(self.crm.opps[opp_id]["amount"], 700)

    def test_cumulative_cap_against_original_amount(self):
        opp_id = self.make_opp(amount=1000)
        self.crm.discount(opp_id, 30, "m1")
        self.assertEqual(self.crm.opps[opp_id]["amount"], 700)
        with self.assertRaises(ValueError):
            self.crm.discount(opp_id, 1, "m1")
        self.assertEqual(self.crm.opps[opp_id]["amount"], 700)
        self.assertEqual(self.crm.opps[opp_id]["original_amount"], 1000)

    def test_integer_floor_math(self):
        opp_id = self.make_opp(amount=101)
        self.crm.discount(opp_id, 10, "r1")
        self.assertEqual(self.crm.opps[opp_id]["amount"], 90)

    def test_final_stage_cannot_be_discounted(self):
        opp_id = self.make_opp(stage="lost")
        with self.assertRaises(ValueError):
            self.crm.discount(opp_id, 5, "m1")
        self.assertEqual(self.crm.opps[opp_id]["amount"], 1000)


class TestTransfer(CRMTestCase):
    def test_unknown_opportunity(self):
        with self.assertRaises(ValueError):
            self.crm.transfer("O99", "r2", "m1")

    def test_only_manager_can_transfer(self):
        opp_id = self.make_opp()
        with self.assertRaises(PermissionError):
            self.crm.transfer(opp_id, "r2", "r1")

    def test_manager_checked_before_new_owner(self):
        opp_id = self.make_opp()
        with self.assertRaises(PermissionError):
            self.crm.transfer(opp_id, "nobody", "r1")

    def test_new_owner_must_be_known_rep(self):
        opp_id = self.make_opp()
        for new_owner in ["nobody", "m1", None]:
            with self.subTest(new_owner=new_owner):
                with self.assertRaises(ValueError):
                    self.crm.transfer(opp_id, new_owner, "m1")
        self.assertEqual(self.crm.opps[opp_id]["owner"], "r1")

    def test_cannot_transfer_final_opportunity(self):
        opp_id = self.make_opp(stage="won")
        with self.assertRaises(ValueError):
            self.crm.transfer(opp_id, "r2", "m1")

    def test_cannot_transfer_to_same_owner(self):
        opp_id = self.make_opp()
        with self.assertRaises(ValueError):
            self.crm.transfer(opp_id, "r1", "m1")

    def test_cannot_transfer_to_rep_at_capacity(self):
        crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 1},
                {"id": "r2", "role": "rep", "capacity": 1},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        lead1 = crm.add_lead("a@corp.com", "A", "referral", "m1")
        crm.qualify(lead1, "m1")
        opp = crm.convert(lead1, 100, "m1")
        crm.add_lead("b@corp.com", "B", "referral", "m1")  # fills r2
        with self.assertRaises(ValueError):
            crm.transfer(opp, "r2", "m1")
        self.assertEqual(crm.opps[opp]["owner"], "r1")

    def test_transfer_changes_owner_and_logs(self):
        opp_id = self.make_opp()
        self.crm.transfer(opp_id, "r2", "m1")
        self.assertEqual(self.crm.opps[opp_id]["owner"], "r2")
        self.assertEqual(self.crm.log[-1], ("transfer", opp_id, "m1"))

    def test_transfer_assigns_new_owner_and_frees_previous_slot(self):
        crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 1},
                {"id": "r2", "role": "rep", "capacity": 3},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        lead1 = crm.add_lead("a@corp.com", "A", "referral", "m1")   # r1
        crm.qualify(lead1, "m1")
        opp = crm.convert(lead1, 100, "m1")                          # r1 load 1
        crm.add_lead("b@corp.com", "B", "referral", "m1")           # r2
        crm.add_lead("c@corp.com", "C", "referral", "m1")           # r2

        crm.transfer(opp, "r2", "m1")

        self.assertEqual(crm.opps[opp]["owner"], "r2")
        self.assertEqual(crm.log[-1], ("transfer", opp, "m1"))
        # r1's slot is free again, so the next lead goes to r1.
        new_lead = crm.add_lead("e@corp.com", "E", "referral", "m1")
        self.assertEqual(crm.leads[new_lead]["owner"], "r1")


class TestForecast(CRMTestCase):
    def test_empty_forecast(self):
        self.assertEqual(self.crm.forecast(), {"open": 0, "weighted": 0, "won": 0})
        self.assertEqual(self.crm.log, [])

    def test_forecast_math_and_no_log(self):
        crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 10},
                {"id": "r2", "role": "rep", "capacity": 10},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )

        def opp(amount, stage, email):
            lead = crm.add_lead(email, "X", "referral", "m1")
            crm.qualify(lead, "m1")
            oid = crm.convert(lead, amount, "m1")
            steps = {
                "prospect": [],
                "proposal": ["proposal"],
                "negotiation": ["proposal", "negotiation"],
                "won": ["proposal", "negotiation", "won"],
                "lost": ["lost"],
            }[stage]
            for step in steps:
                crm.advance(oid, step, "m1")
            return oid

        opp(1000, "prospect", "a@corp.com")
        opp(333, "proposal", "b@corp.com")
        opp(100, "negotiation", "c@corp.com")
        opp(500, "won", "d@corp.com")
        opp(700, "lost", "e@corp.com")

        log_before = list(crm.log)
        self.assertEqual(crm.forecast(), {"open": 3, "weighted": 259, "won": 500})
        self.assertEqual(crm.log, log_before)


class TestLoadAccounting(CRMTestCase):
    def test_load_counts_new_qualified_and_open_opps(self):
        crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 3},
                {"id": "r2", "role": "rep", "capacity": 3},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        # r1: L1 (new), r2: L2 (new)
        l1 = crm.add_lead("a@corp.com", "A", "referral", "m1")
        l2 = crm.add_lead("b@corp.com", "B", "referral", "m1")
        self.assertEqual(crm.leads[l1]["owner"], "r1")
        self.assertEqual(crm.leads[l2]["owner"], "r2")

        # qualified still counts; converted lead stops counting but its open opp counts.
        crm.qualify(l1, "m1")
        o1 = crm.convert(l1, 100, "m1")
        self.assertEqual(crm.leads[l1]["status"], "converted")

        # r1 load 1 (opp), r2 load 1 (lead) -> tie, r1 gets next.
        l3 = crm.add_lead("c@corp.com", "C", "referral", "m1")
        self.assertEqual(crm.leads[l3]["owner"], "r1")
        # r1 2, r2 1 -> r2
        l4 = crm.add_lead("d@corp.com", "D", "referral", "m1")
        self.assertEqual(crm.leads[l4]["owner"], "r2")
        # r1 2, r2 2 -> r1
        l5 = crm.add_lead("e@corp.com", "E", "referral", "m1")
        self.assertEqual(crm.leads[l5]["owner"], "r1")
        # r1 3 (capacity), r2 2 -> r2
        l6 = crm.add_lead("f@corp.com", "F", "referral", "m1")
        self.assertEqual(crm.leads[l6]["owner"], "r2")
        # both full -> waiting
        l7 = crm.add_lead("g@corp.com", "G", "referral", "m1")
        self.assertIsNone(crm.leads[l7]["owner"])
        self.assertEqual(crm.waiting, [l7])

        # closing the open opp frees an r1 slot, which takes the waiting lead.
        crm.advance(o1, "lost", "m1")
        self.assertEqual(crm.leads[l7]["owner"], "r1")
        self.assertEqual(crm.waiting, [])

    def test_won_and_lost_opportunities_do_not_count(self):
        crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 2},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        l1 = crm.add_lead("a@corp.com", "A", "referral", "m1")
        crm.qualify(l1, "m1")
        o1 = crm.convert(l1, 100, "m1")          # load 1
        l2 = crm.add_lead("b@corp.com", "B", "referral", "m1")  # load 2
        l3 = crm.add_lead("c@corp.com", "C", "referral", "m1")  # waiting
        self.assertIsNone(crm.leads[l3]["owner"])

        crm.advance(o1, "proposal", "m1")
        crm.advance(o1, "negotiation", "m1")
        crm.advance(o1, "won", "m1")             # frees one slot
        self.assertEqual(crm.leads[l3]["owner"], "r1")


if __name__ == "__main__":
    unittest.main()
