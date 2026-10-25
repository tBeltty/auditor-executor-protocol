import unittest

from crm import CRM, DuplicateLeadError


def make(*specs):
    """make(("a", "rep", 1), ("m", "manager", 0))"""
    return CRM([{"id": i, "role": r, "capacity": c} for i, r, c in specs])


def referral(crm, email, actor="a"):
    return crm.add_lead(email, "Lead", "referral", actor)


def with_opp(crm, email, amount=1000, actor="a"):
    lead_id = referral(crm, email, actor)
    crm.qualify(lead_id, actor)
    return crm.convert(lead_id, amount, actor)


class ActorAndValidationTests(unittest.TestCase):
    def test_unknown_actor_is_rejected_first(self):
        c = make(("a", "rep", 1))
        calls = [
            lambda: c.add_lead("bad", "", "nope", "ghost"),
            lambda: c.qualify("L1", "ghost"),
            lambda: c.convert("L1", 0, "ghost"),
            lambda: c.advance("O1", "nope", "ghost"),
            lambda: c.discount("O1", 99, "ghost"),
            lambda: c.transfer("O1", "a", "ghost"),
        ]
        for call in calls:
            with self.assertRaises(PermissionError):
                call()
        self.assertEqual(c.leads, {})
        self.assertEqual(c.opps, {})
        self.assertEqual(c.log, [])

    def test_bad_email_is_rejected(self):
        c = make(("a", "rep", 5))
        bad = [None, 7, "", "plain", "a@b", "a@.com", "a@com.", "a@@b.com",
               "@b.com", "a@b@c.com"]
        for email in bad:
            with self.assertRaises(ValueError, msg=repr(email)):
                c.add_lead(email, "N", "web", "a")
        self.assertEqual(c.leads, {})
        self.assertEqual(c.log, [])

    def test_bad_name_and_source_are_rejected(self):
        c = make(("a", "rep", 5))
        for name in [None, 7, "", "   "]:
            with self.assertRaises(ValueError):
                c.add_lead("x@y.com", name, "web", "a")
        for source in ["email", None, "Web"]:
            with self.assertRaises(ValueError):
                c.add_lead("x@y.com", "N", source, "a")
        self.assertEqual(c.log, [])

    def test_failed_call_does_not_mutate_or_log(self):
        c = make(("a", "rep", 5))
        opp_id = with_opp(c, "x@corp.com", 1000)
        log_len = len(c.log)
        with self.assertRaises(ValueError):
            c.discount(opp_id, 0, "a")
        with self.assertRaises(ValueError):
            c.advance(opp_id, "won", "a")
        self.assertEqual(c.opps[opp_id]["amount"], 1000)
        self.assertEqual(c.opps[opp_id]["stage"], "prospect")
        self.assertEqual(len(c.log), log_len)


class AddLeadTests(unittest.TestCase):
    def test_normalization_and_scores(self):
        c = make(("a", "rep", 10))
        c.add_lead(" Alice@Example.COM ", " Alice ", "web", "a")
        c.add_lead("bob@gmail.com", "Bob", "web", "a")
        c.add_lead("carl@gmail.com", "Carl", "referral", "a")
        c.add_lead("d@corp.io", "Dee", "event", "a")

        first = c.leads["L1"]
        self.assertEqual(first["email"], "alice@example.com")
        self.assertEqual(first["name"], "Alice")
        self.assertEqual(first["score"], 25)  # web 10 + non-free bonus 15
        self.assertEqual(c.leads["L2"]["score"], 10)
        self.assertEqual(c.leads["L3"]["score"], 30)
        self.assertEqual(c.leads["L4"]["score"], 35)
        self.assertEqual([e[0] for e in c.log], ["add_lead"] * 4)

    def test_duplicate_email_keeps_existing_lead(self):
        c = make(("a", "rep", 5))
        c.add_lead("Alice@Example.com", "Alice", "web", "a")
        with self.assertRaises(DuplicateLeadError) as ctx:
            c.add_lead("  ALICE@example.COM ", "Other", "web", "a")
        self.assertEqual(ctx.exception.existing_id, "L1")
        self.assertEqual(len(c.leads), 1)
        self.assertEqual(len(c.log), 1)

    def test_source_checked_before_duplicate(self):
        c = make(("a", "rep", 5))
        c.add_lead("a@b.com", "A", "web", "a")
        with self.assertRaises(ValueError):
            c.add_lead("a@b.com", "A", "bogus", "a")

    def test_assignment_prefers_lowest_load_then_smallest_id(self):
        c = make(("b", "rep", 1), ("a", "rep", 2))
        one = c.add_lead("1@x.com", "One", "web", "b")
        two = c.add_lead("2@x.com", "Two", "web", "b")
        three = c.add_lead("3@x.com", "Three", "web", "b")
        four = c.add_lead("4@x.com", "Four", "web", "b")
        self.assertEqual(c.leads[one]["owner"], "a")  # tie -> "a"
        self.assertEqual(c.leads[two]["owner"], "b")
        self.assertEqual(c.leads[three]["owner"], "a")
        self.assertIsNone(c.leads[four]["owner"])  # everyone full

    def test_waiting_lead_assigned_when_slot_frees(self):
        c = make(("a", "rep", 1), ("m", "manager", 0))
        first = referral(c, "1@x.com")
        queued = c.add_lead("2@x.com", "Two", "web", "a")
        self.assertIsNone(c.leads[queued]["owner"])

        c.qualify(first, "a")
        opp = c.convert(first, 1000, "a")
        c.advance(opp, "proposal", "a")
        c.advance(opp, "negotiation", "a")
        c.advance(opp, "won", "a")

        self.assertEqual(c.leads[queued]["owner"], "a")
        self.assertEqual(c.log[-2], ("advance", opp, "a"))
        self.assertEqual(c.log[-1], ("assign", queued, "system"))


class QualifyConvertTests(unittest.TestCase):
    def test_qualify_permissions_status_and_score(self):
        c = make(("a", "rep", 5), ("b", "rep", 0), ("m", "manager", 0))
        low = c.add_lead("low@gmail.com", "Low", "web", "a")  # score 10
        with self.assertRaises(ValueError):
            c.qualify(low, "m")  # score too low
        with self.assertRaises(ValueError):
            c.qualify("L999", "a")

        high = c.add_lead("high@corp.com", "High", "web", "a")  # score 25 < 30
        with self.assertRaises(ValueError):
            c.qualify(high, "m")

        good = c.add_lead("good@free.com", "Good", "referral", "a")  # score 45
        with self.assertRaises(PermissionError):
            c.qualify(good, "b")
        c.qualify(good, "m")
        self.assertEqual(c.leads[good]["status"], "qualified")
        with self.assertRaises(ValueError):
            c.qualify(good, "a")  # not new anymore
        self.assertEqual(c.log[-1], ("qualify", good, "m"))

    def test_convert_validation_and_success(self):
        c = make(("a", "rep", 5), ("b", "rep", 0), ("m", "manager", 0))
        lead = referral(c, "lead@corp.com")
        c.qualify(lead, "a")

        for amount in [0, -1, True, 1.0, "5"]:
            with self.assertRaises(ValueError, msg=repr(amount)):
                c.convert(lead, amount, "a")
        with self.assertRaises(PermissionError):
            c.convert(lead, 1000, "b")
        # amount is validated before the actor check
        with self.assertRaises(ValueError):
            c.convert(lead, 0, "b")

        unqualified = referral(c, "other@corp.com")
        with self.assertRaises(ValueError):
            c.convert(unqualified, 1000, "m")

        opp = c.convert(lead, 2500, "a")
        self.assertEqual(opp, "O1")
        self.assertEqual(c.opps[opp], {
            "id": "O1",
            "lead_id": lead,
            "owner": "a",
            "amount": 2500,
            "original_amount": 2500,
            "stage": "prospect",
        })
        self.assertEqual(c.leads[lead]["status"], "converted")
        self.assertEqual(c.log[-1], ("convert", opp, "a"))
        lead2 = referral(c, "lead2@corp.com")
        c.qualify(lead2, "a")
        self.assertEqual(c.convert(lead2, 50, "a"), "O2")

    def test_convert_requires_an_owner(self):
        c = make(("a", "rep", 0), ("m", "manager", 0))
        lead = referral(c, "orphan@corp.com")
        self.assertIsNone(c.leads[lead]["owner"])
        c.qualify(lead, "m")
        with self.assertRaises(ValueError):
            c.convert(lead, 100, "m")


class AdvanceTests(unittest.TestCase):
    def test_stage_validation_and_permissions(self):
        c = make(("a", "rep", 3), ("b", "rep", 0), ("m", "manager", 0))
        opp = with_opp(c, "one@corp.com")

        with self.assertRaises(ValueError):
            c.advance("O99", "proposal", "a")
        with self.assertRaises(ValueError):
            c.advance(opp, "closed", "b")  # stage checked before actor
        with self.assertRaises(PermissionError):
            c.advance(opp, "proposal", "b")
        with self.assertRaises(ValueError):
            c.advance(opp, "negotiation", "a")  # no skipping

        c.advance(opp, "proposal", "a")
        with self.assertRaises(ValueError):
            c.advance(opp, "prospect", "a")  # no going back

        c.advance(opp, "lost", "a")  # lost is always allowed
        self.assertEqual(c.opps[opp]["stage"], "lost")
        with self.assertRaises(ValueError):
            c.advance(opp, "won", "a")  # final

    def test_negotiation_over_50000_needs_manager(self):
        c = make(("a", "rep", 3), ("m", "manager", 0))
        opp = with_opp(c, "big@corp.com", 50001)
        c.advance(opp, "proposal", "a")
        with self.assertRaises(PermissionError):
            c.advance(opp, "negotiation", "a")
        c.advance(opp, "negotiation", "m")
        self.assertEqual(c.opps[opp]["stage"], "negotiation")

        exact = with_opp(c, "exact@corp.com", 50000)
        c.advance(exact, "proposal", "a")
        c.advance(exact, "negotiation", "a")
        self.assertEqual(c.opps[exact]["stage"], "negotiation")

    def test_won_frees_slot_and_logs_assignment(self):
        c = make(("a", "rep", 1))
        first = referral(c, "first@corp.com")
        second = c.add_lead("second@corp.com", "Second", "web", "a")
        c.qualify(first, "a")
        opp = c.convert(first, 1000, "a")
        for stage in ("proposal", "negotiation", "won"):
            c.advance(opp, stage, "a")
        self.assertEqual(c.leads[second]["owner"], "a")
        self.assertEqual(c.log[-1], ("assign", second, "system"))


class DiscountTests(unittest.TestCase):
    def test_discount_validation_and_limits(self):
        c = make(("a", "rep", 5), ("b", "rep", 0), ("m", "manager", 0))
        opp = with_opp(c, "deal@corp.com", 1000)

        with self.assertRaises(ValueError):
            c.discount("O99", 0, "a")  # opportunity checked before pct
        for pct in [0, 31, -1, True, 10.0]:
            with self.assertRaises(ValueError, msg=repr(pct)):
                c.discount(opp, pct, "a")
        with self.assertRaises(PermissionError):
            c.discount(opp, 5, "b")
        with self.assertRaises(PermissionError):
            c.discount(opp, 11, "a")  # rep above 10

        c.discount(opp, 10, "a")
        self.assertEqual(c.opps[opp]["amount"], 900)
        self.assertEqual(c.opps[opp]["original_amount"], 1000)

        # 10% then 30% is cumulative 37% -> rejected even for a manager
        with self.assertRaises(ValueError):
            c.discount(opp, 30, "m")
        self.assertEqual(c.opps[opp]["amount"], 900)

        fresh = with_opp(c, "fresh@corp.com", 1000)
        c.discount(fresh, 30, "m")
        self.assertEqual(c.opps[fresh]["amount"], 700)

    def test_discount_rejected_on_final_stage(self):
        c = make(("a", "rep", 3))
        opp = with_opp(c, "done@corp.com", 1000)
        c.advance(opp, "lost", "a")
        with self.assertRaises(ValueError):
            c.discount(opp, 5, "a")


class TransferTests(unittest.TestCase):
    def test_transfer_checks(self):
        c = make(("a", "rep", 2), ("b", "rep", 1), ("m", "manager", 0))
        opp = with_opp(c, "t@corp.com", 1000)

        with self.assertRaises(PermissionError):
            c.transfer(opp, "nobody", "a")  # non-manager checked first
        with self.assertRaises(ValueError):
            c.transfer("O99", "b", "m")
        with self.assertRaises(ValueError):
            c.transfer(opp, "ghost", "m")
        with self.assertRaises(ValueError):
            c.transfer(opp, "m", "m")  # managers never own work
        with self.assertRaises(ValueError):
            c.transfer(opp, "a", "m")  # same owner
        self.assertEqual(c.opps[opp]["owner"], "a")

        c.transfer(opp, "b", "m")
        self.assertEqual(c.opps[opp]["owner"], "b")
        self.assertEqual(c.log[-1], ("transfer", opp, "m"))

    def test_transfer_success_changes_owner(self):
        c = make(("a", "rep", 2), ("b", "rep", 2), ("m", "manager", 0))
        opp = with_opp(c, "move@corp.com", 1000)
        c.transfer(opp, "b", "m")
        self.assertEqual(c.opps[opp]["owner"], "b")
        self.assertEqual(c.log[-1], ("transfer", opp, "m"))
        self.assertEqual(c.forecast(), {"open": 1, "weighted": 100, "won": 0})

    def test_transfer_rejects_final_and_full_owner(self):
        c = make(("a", "rep", 2), ("b", "rep", 1), ("full", "rep", 0),
                 ("m", "manager", 0))
        opp = with_opp(c, "final@corp.com", 1000)
        self.assertEqual(c.leads["L1"]["owner"], "a")
        with self.assertRaises(ValueError):
            c.transfer(opp, "full", "m")  # full has capacity 0
        c.advance(opp, "lost", "a")
        with self.assertRaises(ValueError):
            c.transfer(opp, "b", "m")
        self.assertEqual(c.opps[opp]["owner"], "a")


class ForecastTests(unittest.TestCase):
    def test_empty_forecast(self):
        self.assertEqual(make(("a", "rep", 1)).forecast(),
                         {"open": 0, "weighted": 0, "won": 0})

    def test_forecast_weights_and_final_stages(self):
        c = make(("a", "rep", 10))
        prospect = with_opp(c, "p@corp.com", 1001)
        proposal = with_opp(c, "q@corp.com", 999)
        negotiation = with_opp(c, "r@corp.com", 1000)
        won = with_opp(c, "s@corp.com", 500)
        lost = with_opp(c, "t@corp.com", 400)

        c.advance(proposal, "proposal", "a")
        c.advance(negotiation, "proposal", "a")
        c.advance(negotiation, "negotiation", "a")
        for stage in ("proposal", "negotiation", "won"):
            c.advance(won, stage, "a")
        c.advance(lost, "lost", "a")

        self.assertEqual(prospect, "O1")
        self.assertEqual(c.forecast(), {
            "open": 3,
            "weighted": 1001 * 10 // 100 + 999 * 30 // 100 + 1000 * 60 // 100,
            "won": 500,
        })


class LogTests(unittest.TestCase):
    def test_full_flow_log_entries(self):
        c = make(("a", "rep", 2), ("m", "manager", 0))
        lead = referral(c, "flow@corp.com")
        c.qualify(lead, "a")
        opp = c.convert(lead, 1000, "a")
        c.discount(opp, 5, "a")
        c.advance(opp, "proposal", "a")
        c.advance(opp, "negotiation", "a")
        c.advance(opp, "won", "a")
        self.assertEqual(c.log, [
            ("add_lead", "L1", "a"),
            ("qualify", "L1", "a"),
            ("convert", "O1", "a"),
            ("discount", "O1", "a"),
            ("advance", "O1", "a"),
            ("advance", "O1", "a"),
            ("advance", "O1", "a"),
        ])
        self.assertEqual(c.forecast(), {"open": 0, "weighted": 0, "won": 950})


if __name__ == "__main__":
    unittest.main()
