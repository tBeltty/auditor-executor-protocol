import unittest

from crm import CRM, DuplicateLeadError


def make_crm(capacity=10, extra=()):
    reps = [
        {"id": "r1", "role": "rep", "capacity": capacity},
        {"id": "r2", "role": "rep", "capacity": capacity},
        {"id": "m1", "role": "manager", "capacity": 0},
    ]
    reps.extend(extra)
    return CRM(reps)


def add_converted(crm, email, amount=1000, actor="m1"):
    lead_id = crm.add_lead(email, "Lead", "referral", actor)
    crm.qualify(lead_id, actor)
    return lead_id, crm.convert(lead_id, amount, actor)


class LeadIntakeTests(unittest.TestCase):
    def test_add_lead_normalizes_and_scores(self):
        crm = make_crm()
        web = crm.add_lead("  Jane@Gmail.com ", " Jane Doe ", "web", "r1")
        referral = crm.add_lead("bob@corp.io", "Bob", "referral", "r1")
        event = crm.add_lead("eve@gmail.com", "Eve", "event", "r1")

        self.assertEqual(web, "L1")
        self.assertEqual(referral, "L2")
        self.assertEqual(event, "L3")

        self.assertEqual(crm.leads[web]["email"], "jane@gmail.com")
        self.assertEqual(crm.leads[web]["name"], "Jane Doe")
        self.assertEqual(crm.leads[web]["score"], 10)
        self.assertEqual(crm.leads[referral]["score"], 45)
        self.assertEqual(crm.leads[event]["score"], 20)
        self.assertEqual(crm.leads[web]["status"], "new")
        self.assertEqual(crm.leads[web]["owner"], "r1")
        self.assertEqual(crm.log[0], ("add_lead", web, "r1"))

    def test_add_lead_rejects_unknown_actor_first(self):
        crm = make_crm()
        with self.assertRaises(PermissionError):
            crm.add_lead(123, 456, "nope", "ghost")
        self.assertEqual(crm.leads, {})
        self.assertEqual(crm.log, [])

    def test_add_lead_email_validation(self):
        crm = make_crm()
        bad_emails = [
            None,
            123,
            "",
            "no-at-sign",
            "a@@b.com",
            "@b.com",
            "a@",
            "a@com",
            "a@.com",
            "a@com.",
            " a@b.com@ ",
        ]
        for email in bad_emails:
            with self.subTest(email=email):
                with self.assertRaises(ValueError):
                    crm.add_lead(email, "Name", "web", "r1")
        self.assertEqual(crm.leads, {})
        self.assertEqual(crm.log, [])

    def test_add_lead_name_and_source_validation(self):
        crm = make_crm()
        for name in ["", "   ", None, 7]:
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    crm.add_lead("x@y.com", name, "web", "r1")
        for source in ["ads", "", None, 3]:
            with self.subTest(source=source):
                with self.assertRaises(ValueError):
                    crm.add_lead("x@y.com", "Name", source, "r1")
        self.assertEqual(crm.leads, {})

    def test_duplicate_lead_reports_existing_id_and_changes_nothing(self):
        crm = make_crm()
        first = crm.add_lead("dup@corp.io", "First", "referral", "r1")
        second = crm.add_lead("other@corp.io", "Other", "referral", "r1")
        log_before = list(crm.log)

        with self.assertRaises(DuplicateLeadError) as ctx:
            crm.add_lead("  DUP@Corp.IO ", "Copy", "web", "r1")

        self.assertEqual(ctx.exception.existing_id, first)
        self.assertEqual(len(crm.leads), 2)
        self.assertIn(second, crm.leads)
        self.assertEqual(crm.log, log_before)

    def test_failed_lead_does_not_consume_lead_id(self):
        crm = make_crm()
        with self.assertRaises(ValueError):
            crm.add_lead("bad", "Name", "web", "r1")
        self.assertEqual(crm.add_lead("ok@corp.io", "Name", "web", "r1"), "L1")

    def test_owner_is_least_loaded_with_id_tiebreak(self):
        crm = CRM([
            {"id": "b", "role": "rep", "capacity": 3},
            {"id": "a", "role": "rep", "capacity": 3},
        ])
        first = crm.add_lead("1@corp.io", "One", "web", "b")
        second = crm.add_lead("2@corp.io", "Two", "web", "b")
        third = crm.add_lead("3@corp.io", "Three", "web", "b")
        self.assertEqual(crm.leads[first]["owner"], "a")
        self.assertEqual(crm.leads[second]["owner"], "b")
        self.assertEqual(crm.leads[third]["owner"], "a")

    def test_full_capacity_queues_lead_and_managers_never_own(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 9},
        ])
        first = crm.add_lead("1@corp.io", "One", "web", "r1")
        second = crm.add_lead("2@corp.io", "Two", "web", "r1")
        self.assertEqual(crm.leads[first]["owner"], "r1")
        self.assertIsNone(crm.leads[second]["owner"])
        self.assertEqual(crm.waiting, [second])


class QualifyTests(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        self.lead = self.crm.add_lead("hot@corp.io", "Hot", "referral", "r1")

    def test_qualify_success_and_log(self):
        self.crm.qualify(self.lead, "r1")
        self.assertEqual(self.crm.leads[self.lead]["status"], "qualified")
        self.assertEqual(self.crm.log[-1], ("qualify", self.lead, "r1"))

    def test_qualify_unknown_lead(self):
        with self.assertRaises(ValueError):
            self.crm.qualify("L999", "r1")

    def test_qualify_requires_owner_or_manager(self):
        with self.assertRaises(PermissionError):
            self.crm.qualify(self.lead, "r2")
        self.crm.qualify(self.lead, "m1")
        self.assertEqual(self.crm.leads[self.lead]["status"], "qualified")

    def test_qualify_requires_new_status(self):
        self.crm.qualify(self.lead, "r1")
        with self.assertRaises(ValueError):
            self.crm.qualify(self.lead, "r1")

    def test_qualify_requires_minimum_score(self):
        cold = self.crm.add_lead("cold@gmail.com", "Cold", "web", "r1")
        with self.assertRaises(ValueError):
            self.crm.qualify(cold, "m1")
        self.assertEqual(self.crm.leads[cold]["status"], "new")


class ConvertTests(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        self.lead = self.crm.add_lead("hot@corp.io", "Hot", "referral", "r1")
        self.crm.qualify(self.lead, "r1")

    def test_convert_success(self):
        opp = self.crm.convert(self.lead, 2500, "r1")
        self.assertEqual(opp, "O1")
        self.assertEqual(self.crm.opps[opp], {
            "id": "O1",
            "lead_id": self.lead,
            "owner": "r1",
            "amount": 2500,
            "original_amount": 2500,
            "stage": "prospect",
        })
        self.assertEqual(self.crm.leads[self.lead]["status"], "converted")
        self.assertEqual(self.crm.log[-1], ("convert", opp, "r1"))

    def test_convert_unknown_lead(self):
        with self.assertRaises(ValueError):
            self.crm.convert("L999", 100, "r1")

    def test_convert_rejects_invalid_amounts(self):
        for amount in [0, -1, True, 1.5, "100", None]:
            with self.subTest(amount=amount):
                with self.assertRaises(ValueError):
                    self.crm.convert(self.lead, amount, "r1")
        self.assertEqual(self.crm.opps, {})

    def test_convert_requires_owner_or_manager(self):
        with self.assertRaises(PermissionError):
            self.crm.convert(self.lead, 100, "r2")

    def test_convert_requires_qualified_status(self):
        other = self.crm.add_lead("new@corp.io", "New", "referral", "r1")
        with self.assertRaises(ValueError):
            self.crm.convert(other, 100, "m1")

    def test_convert_requires_owner(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        crm.add_lead("blocker@corp.io", "Blocker", "web", "r1")
        queued = crm.add_lead("queued@corp.io", "Queued", "referral", "r1")
        crm.qualify(queued, "m1")
        with self.assertRaises(ValueError):
            crm.convert(queued, 100, "m1")
        self.assertEqual(crm.leads[queued]["status"], "qualified")
        self.assertEqual(crm.opps, {})

    def test_failed_convert_does_not_consume_opp_id(self):
        with self.assertRaises(ValueError):
            self.crm.convert(self.lead, -5, "r1")
        self.assertEqual(self.crm.convert(self.lead, 100, "r1"), "O1")


class AdvanceTests(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        self.lead, self.opp = add_converted(self.crm, "hot@corp.io")

    def test_advance_full_chain(self):
        self.crm.advance(self.opp, "proposal", "r1")
        self.crm.advance(self.opp, "negotiation", "r1")
        self.crm.advance(self.opp, "won", "r1")
        self.assertEqual(self.crm.opps[self.opp]["stage"], "won")
        self.assertEqual(
            self.crm.log[-3:],
            [
                ("advance", self.opp, "r1"),
                ("advance", self.opp, "r1"),
                ("advance", self.opp, "r1"),
            ],
        )

    def test_advance_rejects_skipping_and_backwards(self):
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "negotiation", "r1")
        self.crm.advance(self.opp, "proposal", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "prospect", "r1")

    def test_advance_rejects_invalid_stage_and_unknown_opp(self):
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "closed", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance("O999", "proposal", "r1")

    def test_advance_requires_owner_or_manager(self):
        with self.assertRaises(PermissionError):
            self.crm.advance(self.opp, "proposal", "r2")
        self.crm.advance(self.opp, "proposal", "m1")
        self.assertEqual(self.crm.opps[self.opp]["stage"], "proposal")

    def test_advance_rejects_moves_after_final_stage(self):
        self.crm.advance(self.opp, "lost", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "proposal", "r1")

    def test_lost_allowed_from_any_open_stage(self):
        other = add_converted(self.crm, "second@corp.io")[1]
        self.crm.advance(other, "proposal", "m1")
        self.crm.advance(other, "lost", "m1")
        self.assertEqual(self.crm.opps[other]["stage"], "lost")

    def test_negotiation_above_threshold_needs_manager(self):
        lead, opp = add_converted(self.crm, "big@corp.io", amount=60000)
        self.crm.advance(opp, "proposal", "r2")
        with self.assertRaises(PermissionError):
            self.crm.advance(opp, "negotiation", "r2")
        self.assertEqual(self.crm.opps[opp]["stage"], "proposal")
        self.crm.advance(opp, "negotiation", "m1")
        self.assertEqual(self.crm.opps[opp]["stage"], "negotiation")

    def test_winning_frees_slot_and_assigns_waiting_fifo(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        first = crm.add_lead("one@gmail.com", "One", "referral", "r1")
        second = crm.add_lead("two@gmail.com", "Two", "web", "r1")
        waiting_one = crm.add_lead("three@gmail.com", "Three", "web", "r1")
        waiting_two = crm.add_lead("four@gmail.com", "Four", "web", "r1")
        self.assertEqual(crm.leads[first]["owner"], "r1")
        self.assertEqual(crm.leads[second]["owner"], "r2")
        self.assertIsNone(crm.leads[waiting_one]["owner"])
        self.assertEqual(crm.waiting, [waiting_one, waiting_two])

        crm.qualify(first, "r1")
        opp = crm.convert(first, 1000, "r1")
        crm.advance(opp, "proposal", "r1")
        crm.advance(opp, "negotiation", "r1")
        crm.advance(opp, "won", "r1")

        self.assertEqual(crm.leads[waiting_one]["owner"], "r1")
        self.assertIsNone(crm.leads[waiting_two]["owner"])
        self.assertEqual(crm.waiting, [waiting_two])
        self.assertEqual(crm.log[-1], ("assign", waiting_one, "system"))


class DiscountTests(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        self.lead, self.opp = add_converted(self.crm, "hot@corp.io", amount=1000)

    def test_discount_success(self):
        self.crm.discount(self.opp, 10, "r1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 900)
        self.assertEqual(self.crm.opps[self.opp]["original_amount"], 1000)
        self.assertEqual(self.crm.log[-1], ("discount", self.opp, "r1"))

    def test_discount_validates_pct(self):
        for pct in [0, 31, -5, True, 5.0, "10", None]:
            with self.subTest(pct=pct):
                with self.assertRaises(ValueError):
                    self.crm.discount(self.opp, pct, "r1")

    def test_discount_requires_owner_or_manager(self):
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp, 5, "r2")

    def test_discount_non_manager_limited_to_ten(self):
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp, 11, "r1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 1000)

    def test_discount_cumulative_cap_is_thirty_percent(self):
        self.crm.discount(self.opp, 30, "m1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 700)
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp, 1, "m1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 700)

    def test_discount_rejects_final_stage(self):
        self.crm.advance(self.opp, "lost", "r1")
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp, 5, "r1")

    def test_failed_discount_is_atomic(self):
        log_before = list(self.crm.log)
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp, 30, "r1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 1000)
        self.assertEqual(self.crm.log, log_before)


class TransferTests(unittest.TestCase):
    def make_ready(self):
        crm = make_crm(capacity=2)
        first = crm.add_lead("one@corp.io", "One", "referral", "r1")
        crm.qualify(first, "r1")
        opp = crm.convert(first, 1000, "r1")
        return crm, opp

    def test_transfer_success(self):
        crm, opp = self.make_ready()
        crm.transfer(opp, "r2", "m1")
        self.assertEqual(crm.opps[opp]["owner"], "r2")
        self.assertEqual(crm.log[-1], ("transfer", opp, "m1"))

    def test_transfer_requires_manager(self):
        crm, opp = self.make_ready()
        with self.assertRaises(PermissionError):
            crm.transfer(opp, "r2", "r1")

    def test_transfer_rejects_unknown_or_manager_target(self):
        crm, opp = self.make_ready()
        with self.assertRaises(ValueError):
            crm.transfer(opp, "ghost", "m1")
        with self.assertRaises(ValueError):
            crm.transfer(opp, "m1", "m1")
        self.assertEqual(crm.opps[opp]["owner"], "r1")

    def test_transfer_rejects_same_owner(self):
        crm, opp = self.make_ready()
        with self.assertRaises(ValueError):
            crm.transfer(opp, "r1", "m1")

    def test_transfer_rejects_final_stage(self):
        crm, opp = self.make_ready()
        crm.advance(opp, "proposal", "r1")
        crm.advance(opp, "negotiation", "r1")
        crm.advance(opp, "won", "r1")
        with self.assertRaises(ValueError):
            crm.transfer(opp, "r2", "m1")

    def test_transfer_rejects_target_at_capacity(self):
        crm, opp = self.make_ready()
        crm.add_lead("two@corp.io", "Two", "web", "r1")
        crm.add_lead("three@corp.io", "Three", "web", "r1")
        crm.add_lead("four@corp.io", "Four", "web", "r1")
        with self.assertRaises(ValueError):
            crm.transfer(opp, "r2", "m1")
        self.assertEqual(crm.opps[opp]["owner"], "r1")


class ForecastTests(unittest.TestCase):
    def test_forecast_counts_and_weights(self):
        crm = make_crm()
        _, prospect = add_converted(crm, "a@corp.io", amount=500)
        _, proposal = add_converted(crm, "b@corp.io", amount=1000)
        crm.advance(proposal, "proposal", "m1")
        _, negotiation = add_converted(crm, "c@corp.io", amount=300)
        crm.advance(negotiation, "proposal", "m1")
        crm.advance(negotiation, "negotiation", "m1")
        _, won = add_converted(crm, "d@corp.io", amount=2000)
        crm.advance(won, "proposal", "m1")
        crm.advance(won, "negotiation", "m1")
        crm.advance(won, "won", "m1")

        log_before = list(crm.log)
        self.assertEqual(
            crm.forecast(),
            {"open": 3, "weighted": 50 + 300 + 180, "won": 2000},
        )
        self.assertEqual(crm.log, log_before)

    def test_forecast_empty(self):
        self.assertEqual(make_crm().forecast(), {"open": 0, "weighted": 0, "won": 0})


if __name__ == "__main__":
    unittest.main()
