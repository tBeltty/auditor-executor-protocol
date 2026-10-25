import unittest

from crm import CRM, DuplicateLeadError


def default_reps():
    return [
        {"id": "r1", "role": "rep", "capacity": 5},
        {"id": "r2", "role": "rep", "capacity": 5},
        {"id": "m1", "role": "manager", "capacity": 0},
    ]


class CRMTestCase(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(default_reps())

    def add(self, email="lead@corp.com", source="referral", name="Lead", actor="m1"):
        return self.crm.add_lead(email, name, source, actor)

    def qualified(self, email="lead@corp.com", source="referral"):
        lead_id = self.add(email, source)
        self.crm.qualify(lead_id, "m1")
        return lead_id

    def opp(self, email="lead@corp.com", amount=1000):
        return self.crm.convert(self.qualified(email), amount, "m1")

    def other_rep(self, rep_id):
        return "r2" if rep_id == "r1" else "r1"


class AddLeadTests(CRMTestCase):
    def test_normalizes_email_and_name(self):
        lead_id = self.add("  Alice@Example.COM ", name="  Alice  ")
        lead = self.crm.leads[lead_id]
        self.assertEqual(lead["email"], "alice@example.com")
        self.assertEqual(lead["name"], "Alice")
        self.assertEqual(lead["status"], "new")
        self.assertEqual(lead["owner"], "r1")
        self.assertEqual(self.crm.log[-1], ("add_lead", lead_id, "m1"))

    def test_scores_by_source_and_domain(self):
        expected = {
            "a@gmail.com": ("web", 10),
            "b@corp.com": ("web", 25),
            "c@gmail.com": ("referral", 30),
            "d@corp.com": ("referral", 45),
            "e@yahoo.com": ("event", 20),
            "f@corp.com": ("event", 35),
            "g@outlook.com": ("referral", 30),
        }
        for email, (source, score) in expected.items():
            lead_id = self.add(email, source)
            self.assertEqual(self.crm.leads[lead_id]["score"], score, email)

    def test_rejects_invalid_emails(self):
        bad = [
            "plain",
            "a@b@c.com",
            "@b.com",
            "a@com",
            "a@.com",
            "a@com.",
            "a@.",
            5,
            None,
        ]
        for email in bad:
            with self.assertRaises(ValueError, msg=repr(email)):
                self.add(email)
        self.assertEqual(self.crm.leads, {})
        self.assertEqual(self.crm.log, [])

    def test_rejects_invalid_name_and_source(self):
        for name in ("", "   ", 7, None):
            with self.assertRaises(ValueError, msg=repr(name)):
                self.add(name=name)
        for source in ("phone", "Web", "", None):
            with self.assertRaises(ValueError, msg=repr(source)):
                self.add(source=source)
        self.assertEqual(self.crm.leads, {})

    def test_unknown_actor_is_checked_first(self):
        with self.assertRaises(PermissionError):
            self.crm.add_lead("not-an-email", "", "phone", "ghost")

    def test_duplicate_lead_uses_normalized_email(self):
        first = self.add("Alice@Corp.com")
        with self.assertRaises(DuplicateLeadError) as ctx:
            self.add("  alice@corp.COM ")
        self.assertEqual(ctx.exception.existing_id, first)
        self.assertIsInstance(ctx.exception, Exception)
        self.assertEqual(len(self.crm.leads), 1)
        self.assertEqual(len(self.crm.log), 1)

    def test_failed_add_does_not_consume_lead_number(self):
        with self.assertRaises(ValueError):
            self.add("broken")
        lead_id = self.add()
        self.assertEqual(lead_id, "L1")
        self.assertEqual(self.add("second@corp.com"), "L2")

    def test_owner_has_lowest_load_with_string_tiebreak(self):
        crm = CRM([
            {"id": "b", "role": "rep", "capacity": 5},
            {"id": "a", "role": "rep", "capacity": 5},
        ])
        self.assertEqual(crm.add_lead("1@corp.com", "x", "web", "a"), "L1")
        self.assertEqual(crm.leads["L1"]["owner"], "a")
        self.assertEqual(crm.add_lead("2@corp.com", "x", "web", "b"), "L2")
        self.assertEqual(crm.leads["L2"]["owner"], "b")
        self.assertEqual(crm.add_lead("3@corp.com", "x", "web", "a"), "L3")
        self.assertEqual(crm.leads["L3"]["owner"], "a")

    def test_capacity_exhausted_puts_lead_in_waiting_queue(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 5},
        ])
        self.assertEqual(crm.add_lead("1@corp.com", "x", "web", "m1"), "L1")
        self.assertEqual(crm.leads["L1"]["owner"], "r1")
        self.assertEqual(crm.add_lead("2@corp.com", "x", "web", "m1"), "L2")
        self.assertIsNone(crm.leads["L2"]["owner"])
        self.assertEqual(crm.log, [("add_lead", "L1", "m1"), ("add_lead", "L2", "m1")])

    def test_manager_never_receives_leads(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 0},
            {"id": "m1", "role": "manager", "capacity": 5},
        ])
        lead_id = crm.add_lead("1@corp.com", "x", "web", "m1")
        self.assertIsNone(crm.leads[lead_id]["owner"])

    def test_qualified_lead_and_open_opportunity_count_as_load(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        crm.add_lead("1@corp.com", "x", "referral", "m1")
        crm.qualify("L1", "m1")
        self.assertEqual(crm.add_lead("2@corp.com", "x", "web", "m1"), "L2")
        self.assertEqual(crm.leads["L2"]["owner"], "r2")
        crm.convert("L1", 1000, "m1")
        self.assertEqual(crm.add_lead("3@corp.com", "x", "web", "m1"), "L3")
        self.assertIsNone(crm.leads["L3"]["owner"])


class QualifyTests(CRMTestCase):
    def test_unknown_lead(self):
        with self.assertRaises(ValueError):
            self.crm.qualify("L99", "m1")

    def test_requires_owner_or_manager(self):
        lead_id = self.add()
        with self.assertRaises(PermissionError):
            self.crm.qualify(lead_id, "r2")
        self.assertEqual(self.crm.leads[lead_id]["status"], "new")

    def test_manager_may_qualify(self):
        lead_id = self.add()
        self.crm.qualify(lead_id, "m1")
        self.assertEqual(self.crm.leads[lead_id]["status"], "qualified")

    def test_requires_new_status(self):
        lead_id = self.qualified()
        with self.assertRaises(ValueError):
            self.crm.qualify(lead_id, "m1")

    def test_requires_score_of_at_least_30(self):
        web = self.add("web@gmail.com", "web")
        with self.assertRaises(ValueError):
            self.crm.qualify(web, self.crm.leads[web]["owner"])
        corporate_web = self.add("web@corp.com", "web")
        with self.assertRaises(ValueError):
            self.crm.qualify(corporate_web, self.crm.leads[corporate_web]["owner"])
        referral = self.add("ref@gmail.com", "referral")
        self.crm.qualify(referral, self.crm.leads[referral]["owner"])
        self.assertEqual(self.crm.leads[referral]["status"], "qualified")

    def test_permission_checked_before_score(self):
        lead_id = self.add("web@gmail.com", "web")
        with self.assertRaises(PermissionError):
            self.crm.qualify(lead_id, "r2")

    def test_success_logs_once(self):
        lead_id = self.add()
        before = len(self.crm.log)
        self.crm.qualify(lead_id, "r1")
        self.assertEqual(len(self.crm.log), before + 1)
        self.assertEqual(self.crm.log[-1], ("qualify", lead_id, "r1"))


class ConvertTests(CRMTestCase):
    def test_amount_must_be_positive_int_not_bool(self):
        lead_id = self.qualified()
        for amount in (0, -5, 10.5, True, False, "100", None):
            with self.assertRaises(ValueError, msg=repr(amount)):
                self.crm.convert(lead_id, amount, "m1")
        self.assertEqual(self.crm.opps, {})
        self.assertEqual(self.crm.leads[lead_id]["status"], "qualified")

    def test_permissions_and_check_order(self):
        lead_id = self.qualified()
        with self.assertRaises(PermissionError):
            self.crm.convert(lead_id, 100, "r2")
        with self.assertRaises(ValueError):
            self.crm.convert(lead_id, 0, "r2")

    def test_requires_qualified_status_and_permission_precedes_status(self):
        lead_id = self.add()
        with self.assertRaises(PermissionError):
            self.crm.convert(lead_id, 100, "r2")
        with self.assertRaises(ValueError):
            self.crm.convert(lead_id, 100, "m1")

    def test_requires_an_owner(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 0},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        lead_id = crm.add_lead("a@corp.com", "x", "referral", "m1")
        crm.qualify(lead_id, "m1")
        self.assertIsNone(crm.leads[lead_id]["owner"])
        with self.assertRaises(ValueError):
            crm.convert(lead_id, 100, "m1")

    def test_success_creates_opportunity(self):
        lead_id = self.qualified("a@corp.com")
        opp_id = self.crm.convert(lead_id, 5000, "r1")
        self.assertEqual(opp_id, "O1")
        self.assertEqual(self.crm.opps[opp_id], {
            "id": "O1",
            "lead_id": lead_id,
            "owner": "r1",
            "amount": 5000,
            "original_amount": 5000,
            "stage": "prospect",
        })
        self.assertEqual(self.crm.leads[lead_id]["status"], "converted")
        self.assertEqual(self.crm.log[-1], ("convert", "O1", "r1"))

    def test_failed_convert_does_not_consume_opportunity_number(self):
        lead_id = self.qualified()
        with self.assertRaises(ValueError):
            self.crm.convert(lead_id, 0, "m1")
        self.assertEqual(self.crm.convert(lead_id, 100, "m1"), "O1")


class AdvanceTests(CRMTestCase):
    def test_unknown_opportunity_and_invalid_stage(self):
        with self.assertRaises(ValueError):
            self.crm.advance("O99", "proposal", "m1")
        opp_id = self.opp()
        for stage in ("closed", "", None):
            with self.assertRaises(ValueError, msg=repr(stage)):
                self.crm.advance(opp_id, stage, "m1")

    def test_requires_owner_or_manager(self):
        opp_id = self.opp()
        owner = self.crm.opps[opp_id]["owner"]
        with self.assertRaises(PermissionError):
            self.crm.advance(opp_id, "proposal", self.other_rep(owner))
        self.assertEqual(self.crm.opps[opp_id]["stage"], "prospect")
        self.crm.advance(opp_id, "proposal", "m1")
        self.assertEqual(self.crm.opps[opp_id]["stage"], "proposal")

    def test_final_stage_cannot_advance(self):
        opp_id = self.opp()
        self.crm.advance(opp_id, "lost", "m1")
        before = len(self.crm.log)
        with self.assertRaises(ValueError):
            self.crm.advance(opp_id, "proposal", "m1")
        self.assertEqual(len(self.crm.log), before)

    def test_stage_order(self):
        opp_id = self.opp()
        with self.assertRaises(ValueError):
            self.crm.advance(opp_id, "negotiation", "m1")
        with self.assertRaises(ValueError):
            self.crm.advance(opp_id, "won", "m1")
        self.crm.advance(opp_id, "proposal", "m1")
        with self.assertRaises(ValueError):
            self.crm.advance(opp_id, "prospect", "m1")
        self.crm.advance(opp_id, "negotiation", "m1")
        with self.assertRaises(ValueError):
            self.crm.advance(opp_id, "proposal", "m1")
        self.crm.advance(opp_id, "won", "m1")
        self.assertEqual(self.crm.opps[opp_id]["stage"], "won")
        with self.assertRaises(ValueError):
            self.crm.advance(opp_id, "lost", "m1")

    def test_lost_allowed_from_any_non_final_stage(self):
        opp_id = self.opp()
        self.crm.advance(opp_id, "lost", "m1")
        self.assertEqual(self.crm.opps[opp_id]["stage"], "lost")
        self.assertEqual(self.crm.log[-1], ("advance", opp_id, "m1"))

    def test_negotiation_over_50000_requires_manager(self):
        opp_id = self.opp("big@corp.com", 60000)
        owner = self.crm.opps[opp_id]["owner"]
        self.crm.advance(opp_id, "proposal", owner)
        before = len(self.crm.log)
        with self.assertRaises(PermissionError):
            self.crm.advance(opp_id, "negotiation", owner)
        self.assertEqual(self.crm.opps[opp_id]["stage"], "proposal")
        self.assertEqual(len(self.crm.log), before)
        self.crm.advance(opp_id, "negotiation", "m1")
        self.assertEqual(self.crm.opps[opp_id]["stage"], "negotiation")

    def test_negotiation_at_50000_allowed_for_rep(self):
        opp_id = self.opp("edge@corp.com", 50000)
        owner = self.crm.opps[opp_id]["owner"]
        self.crm.advance(opp_id, "proposal", owner)
        self.crm.advance(opp_id, "negotiation", owner)
        self.assertEqual(self.crm.opps[opp_id]["stage"], "negotiation")

    def test_won_frees_slot_and_assigns_waiting_leads_fifo(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        for email in ("1@corp.com", "2@corp.com", "3@corp.com", "4@corp.com"):
            crm.add_lead(email, "x", "referral", "m1")
        self.assertEqual([crm.leads[lid]["owner"] for lid in ("L1", "L2", "L3", "L4")],
                         ["r1", "r2", None, None])
        crm.qualify("L1", "m1")
        crm.qualify("L2", "m1")
        o1 = crm.convert("L1", 1000, "m1")
        o2 = crm.convert("L2", 1000, "m1")
        crm.advance(o1, "proposal", "m1")
        crm.advance(o1, "negotiation", "m1")
        crm.advance(o1, "won", "m1")
        self.assertEqual(crm.leads["L3"]["owner"], "r1")
        self.assertIsNone(crm.leads["L4"]["owner"])
        crm.advance(o2, "proposal", "m1")
        crm.advance(o2, "negotiation", "m1")
        crm.advance(o2, "won", "m1")
        self.assertEqual(crm.leads["L4"]["owner"], "r2")
        assigns = [entry for entry in crm.log if entry[0] == "assign"]
        self.assertEqual(assigns, [("assign", "L3", "system"), ("assign", "L4", "system")])


class DiscountTests(CRMTestCase):
    def test_pct_validation(self):
        opp_id = self.opp()
        for pct in (0, -1, 31, True, 10.0, "10", None):
            with self.assertRaises(ValueError, msg=repr(pct)):
                self.crm.discount(opp_id, pct, "m1")
        self.assertEqual(self.crm.opps[opp_id]["amount"], 1000)

    def test_requires_owner_or_manager(self):
        opp_id = self.opp()
        owner = self.crm.opps[opp_id]["owner"]
        with self.assertRaises(PermissionError):
            self.crm.discount(opp_id, 5, self.other_rep(owner))
        self.crm.discount(opp_id, 5, "m1")
        self.assertEqual(self.crm.opps[opp_id]["amount"], 950)

    def test_final_stage_rejected(self):
        opp_id = self.opp()
        self.crm.advance(opp_id, "lost", "m1")
        before = len(self.crm.log)
        with self.assertRaises(ValueError):
            self.crm.discount(opp_id, 5, "m1")
        self.assertEqual(self.crm.opps[opp_id]["amount"], 1000)
        self.assertEqual(len(self.crm.log), before)

    def test_non_manager_may_use_at_most_10(self):
        opp_id = self.opp()
        owner = self.crm.opps[opp_id]["owner"]
        with self.assertRaises(PermissionError):
            self.crm.discount(opp_id, 11, owner)
        self.crm.discount(opp_id, 10, owner)
        self.assertEqual(self.crm.opps[opp_id]["amount"], 900)

    def test_cumulative_discount_cannot_exceed_30_percent(self):
        opp_id = self.opp("big@corp.com", 1000)
        self.crm.discount(opp_id, 10, "m1")
        self.crm.discount(opp_id, 10, "m1")
        self.crm.discount(opp_id, 10, "m1")
        self.assertEqual(self.crm.opps[opp_id]["amount"], 729)
        before = len(self.crm.log)
        with self.assertRaises(ValueError):
            self.crm.discount(opp_id, 10, "m1")
        self.assertEqual(self.crm.opps[opp_id]["amount"], 729)
        self.assertEqual(len(self.crm.log), before)

    def test_manager_discount_30_then_any_further_fails(self):
        opp_id = self.opp("m@corp.com", 1000)
        self.crm.discount(opp_id, 30, "m1")
        self.assertEqual(self.crm.opps[opp_id]["amount"], 700)
        with self.assertRaises(ValueError):
            self.crm.discount(opp_id, 1, "m1")

    def test_success_updates_amount_but_not_original(self):
        opp_id = self.opp("d@corp.com", 1000)
        self.crm.discount(opp_id, 25, "m1")
        self.assertEqual(self.crm.opps[opp_id]["amount"], 750)
        self.assertEqual(self.crm.opps[opp_id]["original_amount"], 1000)
        self.assertEqual(self.crm.log[-1], ("discount", opp_id, "m1"))


class TransferTests(CRMTestCase):
    def test_only_manager_may_transfer(self):
        opp_id = self.opp()
        owner = self.crm.opps[opp_id]["owner"]
        with self.assertRaises(PermissionError):
            self.crm.transfer(opp_id, self.other_rep(owner), owner)

    def test_new_owner_must_be_a_known_rep(self):
        opp_id = self.opp()
        owner = self.crm.opps[opp_id]["owner"]
        for new_owner in ("m1", "ghost"):
            with self.assertRaises(ValueError, msg=repr(new_owner)):
                self.crm.transfer(opp_id, new_owner, "m1")
        self.assertEqual(self.crm.opps[opp_id]["owner"], owner)

    def test_final_same_owner_and_capacity_checks(self):
        opp_id = self.opp()
        owner = self.crm.opps[opp_id]["owner"]
        with self.assertRaises(ValueError):
            self.crm.transfer(opp_id, owner, "m1")
        self.crm.advance(opp_id, "lost", "m1")
        with self.assertRaises(ValueError):
            self.crm.transfer(opp_id, self.other_rep(owner), "m1")

        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 5},
            {"id": "r2", "role": "rep", "capacity": 0},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        lead = crm.add_lead("x@corp.com", "x", "referral", "m1")
        crm.qualify(lead, "m1")
        opp = crm.convert(lead, 100, "m1")
        with self.assertRaises(ValueError):
            crm.transfer(opp, "r2", "m1")

    def test_success_changes_owner_and_logs(self):
        opp_id = self.opp()
        owner = self.crm.opps[opp_id]["owner"]
        other = self.other_rep(owner)
        self.crm.transfer(opp_id, other, "m1")
        self.assertEqual(self.crm.opps[opp_id]["owner"], other)
        self.assertEqual(self.crm.log[-1], ("transfer", opp_id, "m1"))


class ForecastTests(CRMTestCase):
    def test_empty_forecast(self):
        before = len(self.crm.log)
        self.assertEqual(self.crm.forecast(), {"open": 0, "weighted": 0, "won": 0})
        self.assertEqual(len(self.crm.log), before)

    def test_forecast_counts_and_weights(self):
        amounts = {"1@corp.com": 1000, "2@corp.com": 3000,
                   "3@corp.com": 5000, "4@corp.com": 7000, "5@corp.com": 999}
        opps = {}
        for email, amount in amounts.items():
            opps[email] = self.opp(email, amount)
        self.crm.advance(opps["2@corp.com"], "proposal", "m1")
        self.crm.advance(opps["3@corp.com"], "proposal", "m1")
        self.crm.advance(opps["3@corp.com"], "negotiation", "m1")
        self.crm.advance(opps["4@corp.com"], "proposal", "m1")
        self.crm.advance(opps["4@corp.com"], "negotiation", "m1")
        self.crm.advance(opps["4@corp.com"], "won", "m1")
        result = self.crm.forecast()
        self.assertEqual(result["open"], 4)
        self.assertEqual(result["weighted"], 100 + 900 + 3000 + 99)
        self.assertEqual(result["won"], 7000)


class LogAndAtomicityTests(CRMTestCase):
    def test_log_sequence_is_exact(self):
        self.add("seq@corp.com")
        self.crm.qualify("L1", "r1")
        self.crm.convert("L1", 1000, "m1")
        self.crm.advance("O1", "proposal", "m1")
        self.crm.discount("O1", 10, "m1")
        self.crm.forecast()
        self.assertEqual(self.crm.log, [
            ("add_lead", "L1", "m1"),
            ("qualify", "L1", "r1"),
            ("convert", "O1", "m1"),
            ("advance", "O1", "m1"),
            ("discount", "O1", "m1"),
        ])

    def test_unknown_actor_rejected_in_every_mutating_method(self):
        lead_id = self.qualified()
        opp_id = self.crm.convert(lead_id, 1000, "m1")
        before_log = list(self.crm.log)
        before_leads = {k: dict(v) for k, v in self.crm.leads.items()}
        before_opps = {k: dict(v) for k, v in self.crm.opps.items()}
        calls = [
            lambda: self.crm.add_lead("bad", "", "bad", "ghost"),
            lambda: self.crm.qualify(lead_id, "ghost"),
            lambda: self.crm.convert(lead_id, 100, "ghost"),
            lambda: self.crm.advance(opp_id, "proposal", "ghost"),
            lambda: self.crm.discount(opp_id, 5, "ghost"),
            lambda: self.crm.transfer(opp_id, "r1", "ghost"),
        ]
        for call in calls:
            with self.assertRaises(PermissionError):
                call()
        self.assertEqual(self.crm.log, before_log)
        self.assertEqual(self.crm.leads, before_leads)
        self.assertEqual(self.crm.opps, before_opps)

    def test_failed_calls_do_not_log_or_mutate(self):
        lead_id = self.qualified()
        opp_id = self.crm.convert(lead_id, 1000, "m1")
        before_log = list(self.crm.log)

        with self.assertRaises(DuplicateLeadError):
            self.add("lead@corp.com")
        with self.assertRaises(ValueError):
            self.crm.discount(opp_id, 0, "m1")
        with self.assertRaises(ValueError):
            self.crm.advance(opp_id, "won", "m1")
        with self.assertRaises(PermissionError):
            self.crm.transfer(opp_id, "r1", "r1")
        with self.assertRaises(ValueError):
            self.crm.convert(lead_id, 0, "m1")

        self.assertEqual(self.crm.log, before_log)
        self.assertEqual(self.crm.opps[opp_id]["amount"], 1000)
        self.assertEqual(self.crm.opps[opp_id]["stage"], "prospect")


if __name__ == "__main__":
    unittest.main()
