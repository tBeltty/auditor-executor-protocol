import unittest

from crm import CRM, DuplicateLeadError


def reps():
    return [
        {"id": "r1", "role": "rep", "capacity": 2},
        {"id": "r2", "role": "rep", "capacity": 2},
        {"id": "m1", "role": "manager", "capacity": 99},
    ]


class TestAddLead(unittest.TestCase):
    def test_success_and_normalization(self):
        crm = CRM(reps())
        lead_id = crm.add_lead("  Bob@Example.COM ", "  Bob  ", "referral", "r1")
        self.assertEqual(lead_id, "L1")
        lead = crm.leads[lead_id]
        self.assertEqual(lead["email"], "bob@example.com")
        self.assertEqual(lead["name"], "Bob")
        self.assertEqual(lead["source"], "referral")
        self.assertEqual(lead["score"], 45)  # 30 + 15 corporate
        self.assertEqual(lead["owner"], "r1")
        self.assertEqual(lead["status"], "new")
        self.assertEqual(crm.log, [("add_lead", "L1", "r1")])

    def test_scores(self):
        crm = CRM(reps())
        self.assertEqual(crm.leads[crm.add_lead("a@gmail.com", "A", "web", "r1")]["score"], 10)
        self.assertEqual(crm.leads[crm.add_lead("b@gmail.com", "B", "event", "r1")]["score"], 20)
        self.assertEqual(crm.leads[crm.add_lead("c@corp.io", "C", "event", "r1")]["score"], 35)

    def test_invalid_email(self):
        crm = CRM(reps())
        for bad in ["", "no-at.com", "a@@b.com", "@b.com", "a@", "a@b", "a@.com",
                    "a@com.", " a@.x ", 5, None]:
            with self.assertRaises(ValueError):
                crm.add_lead(bad, "N", "web", "r1")
        self.assertEqual(crm.leads, {})
        self.assertEqual(crm.log, [])

    def test_valid_email_shapes(self):
        crm = CRM(reps())
        for email in ["a@b.co", "a.b@c.d.com", "x@y.z"]:
            crm.add_lead(email, "N", "web", "m1")

    def test_invalid_name_and_source(self):
        crm = CRM(reps())
        with self.assertRaises(ValueError):
            crm.add_lead("a@b.com", "   ", "web", "r1")
        with self.assertRaises(ValueError):
            crm.add_lead("a@b.com", None, "web", "r1")
        with self.assertRaises(ValueError):
            crm.add_lead("a@b.com", "N", "email", "r1")
        self.assertEqual(crm.log, [])

    def test_duplicate_normalized(self):
        crm = CRM(reps())
        first = crm.add_lead("A@B.com", "A", "web", "r1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            crm.add_lead(" a@b.COM ", "A2", "referral", "r1")
        self.assertEqual(ctx.exception.existing_id, first)
        self.assertEqual(len(crm.leads), 1)
        self.assertEqual(len(crm.log), 1)

    def test_unknown_actor_checked_first(self):
        crm = CRM(reps())
        with self.assertRaises(PermissionError):
            crm.add_lead("bad-email", "", "nope", "ghost")
        self.assertEqual(crm.leads, {})
        self.assertEqual(crm.log, [])

    def test_lowest_load_owner_and_tie_break(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 5},
            {"id": "r2", "role": "rep", "capacity": 5},
            {"id": "r0", "role": "rep", "capacity": 5},
            {"id": "m1", "role": "manager", "capacity": 5},
        ])
        # all loads 0 -> smallest id wins
        self.assertEqual(crm.leads[crm.add_lead("a@x.com", "A", "web", "m1")]["owner"], "r0")
        self.assertEqual(crm.leads[crm.add_lead("b@x.com", "B", "web", "m1")]["owner"], "r1")
        self.assertEqual(crm.leads[crm.add_lead("c@x.com", "C", "web", "m1")]["owner"], "r2")
        # r2 now has load 1, r0 and r1 also 1 -> r0
        self.assertEqual(crm.leads[crm.add_lead("d@x.com", "D", "web", "m1")]["owner"], "r0")

    def test_capacity_overflow_goes_to_queue(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1}])
        a = crm.add_lead("a@x.com", "A", "web", "r1")
        b = crm.add_lead("b@x.com", "B", "web", "r1")
        self.assertEqual(crm.leads[a]["owner"], "r1")
        self.assertIsNone(crm.leads[b]["owner"])
        self.assertEqual(list(crm.waiting), [b])


class TestQualifyConvert(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(reps())

    def test_qualify_success_manager_and_owner(self):
        lead = self.crm.add_lead("a@corp.com", "A", "referral", "r1")
        self.crm.qualify(lead, "r1")
        self.assertEqual(self.crm.leads[lead]["status"], "qualified")
        self.assertEqual(self.crm.log[-1], ("qualify", lead, "r1"))

    def test_qualify_manager_can_act(self):
        lead = self.crm.add_lead("a@corp.com", "A", "referral", "r1")
        self.crm.qualify(lead, "m1")
        self.assertEqual(self.crm.leads[lead]["status"], "qualified")

    def test_qualify_errors(self):
        lead = self.crm.add_lead("a@gmail.com", "A", "web", "r1")  # score 10
        with self.assertRaises(ValueError):
            self.crm.qualify("L999", "r1")
        with self.assertRaises(PermissionError):
            self.crm.qualify(lead, "r2")
        with self.assertRaises(ValueError):
            self.crm.qualify(lead, "r1")  # score too low
        self.assertEqual(self.crm.leads[lead]["status"], "new")
        self.assertEqual(len(self.crm.log), 1)

    def test_qualify_twice_fails(self):
        lead = self.crm.add_lead("a@corp.com", "A", "referral", "r1")
        self.crm.qualify(lead, "r1")
        with self.assertRaises(ValueError):
            self.crm.qualify(lead, "r1")
        self.assertEqual(len(self.crm.log), 2)

    def test_convert_success(self):
        lead = self.crm.add_lead("a@corp.com", "A", "referral", "r1")
        self.crm.qualify(lead, "r1")
        opp = self.crm.convert(lead, 1000, "r1")
        self.assertEqual(opp, "O1")
        self.assertEqual(self.crm.opps[opp], {
            "id": "O1", "lead_id": lead, "owner": "r1",
            "amount": 1000, "original_amount": 1000, "stage": "prospect",
        })
        self.assertEqual(self.crm.leads[lead]["status"], "converted")
        self.assertEqual(self.crm.log[-1], ("convert", "O1", "r1"))

    def test_convert_amount_validation_and_order(self):
        lead = self.crm.add_lead("a@corp.com", "A", "referral", "r1")
        self.crm.qualify(lead, "r1")
        for bad in [0, -5, 10.0, True, "10", None]:
            with self.assertRaises(ValueError):
                self.crm.convert(lead, bad, "r1")
        self.assertEqual(self.crm.opps, {})

    def test_convert_permission_and_status(self):
        lead = self.crm.add_lead("a@corp.com", "A", "referral", "r1")
        with self.assertRaises(PermissionError):
            self.crm.convert(lead, 100, "r2")  # not qualified yet but perm checked after amount
        with self.assertRaises(ValueError):
            self.crm.convert(lead, 100, "r1")  # not qualified
        self.crm.qualify(lead, "r1")
        with self.assertRaises(PermissionError):
            self.crm.convert(lead, 100, "r2")
        self.crm.convert(lead, 100, "m1")  # manager allowed

    def test_convert_unowned_lead(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 9},
        ])
        a = crm.add_lead("a@corp.com", "A", "referral", "r1")
        b = crm.add_lead("b@corp.com", "B", "referral", "r1")
        # b has no owner, force status qualified by direct state via manager qualify
        crm.qualify(b, "m1")
        with self.assertRaises(ValueError):
            crm.convert(b, 100, "m1")
        self.assertEqual(crm.opps, {})
        self.assertEqual(crm.leads[b]["status"], "qualified")


class TestAdvance(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(reps())
        lead = self.crm.add_lead("a@corp.com", "A", "referral", "r1")
        self.crm.qualify(lead, "r1")
        self.opp = self.crm.convert(lead, 1000, "r1")

    def test_full_pipeline_and_forecast(self):
        self.crm.advance(self.opp, "proposal", "r1")
        self.crm.advance(self.opp, "negotiation", "r1")
        self.assertEqual(self.crm.forecast(), {"open": 1, "weighted": 600, "won": 0})
        self.crm.advance(self.opp, "won", "r1")
        self.assertEqual(self.crm.forecast(), {"open": 0, "weighted": 0, "won": 1000})
        self.assertEqual(self.crm.log[-1], ("advance", self.opp, "r1"))

    def test_transition_rules(self):
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "negotiation", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "bogus", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance("O99", "proposal", "r1")
        with self.assertRaises(PermissionError):
            self.crm.advance(self.opp, "proposal", "r2")
        self.crm.advance(self.opp, "lost", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "proposal", "r1")

    def test_large_negotiation_needs_manager(self):
        crm = CRM(reps())
        lead = crm.add_lead("a@corp.com", "A", "referral", "r1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 60000, "r1")
        crm.advance(opp, "proposal", "r1")
        with self.assertRaises(PermissionError):
            crm.advance(opp, "negotiation", "r1")
        self.assertEqual(crm.opps[opp]["stage"], "proposal")
        crm.advance(opp, "negotiation", "m1")
        self.assertEqual(crm.opps[opp]["stage"], "negotiation")

    def test_advance_assigns_waiting_lead(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1}])
        lead = crm.add_lead("a@corp.com", "A", "referral", "r1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 1000, "r1")
        waiting = crm.add_lead("b@corp.com", "B", "referral", "r1")
        self.assertIsNone(crm.leads[waiting]["owner"])
        crm.advance(opp, "lost", "r1")
        self.assertEqual(crm.leads[waiting]["owner"], "r1")
        self.assertEqual(crm.log[-2:], [
            ("advance", opp, "r1"),
            ("assign", waiting, "system"),
        ])


class TestDiscount(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(reps())
        lead = self.crm.add_lead("a@corp.com", "A", "referral", "r1")
        self.crm.qualify(lead, "r1")
        self.opp = self.crm.convert(lead, 1000, "r1")

    def test_success(self):
        self.crm.discount(self.opp, 10, "r1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 900)
        self.assertEqual(self.crm.log[-1], ("discount", self.opp, "r1"))

    def test_pct_validation(self):
        for bad in [0, 31, -1, 5.0, True, None]:
            with self.assertRaises(ValueError):
                self.crm.discount(self.opp, bad, "r1")
        with self.assertRaises(ValueError):
            self.crm.discount("O9", 5, "r1")
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp, 5, "r2")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 1000)

    def test_rep_limit_10(self):
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp, 11, "r1")
        self.crm.discount(self.opp, 11, "m1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 890)

    def test_cumulative_limit(self):
        self.crm.discount(self.opp, 10, "r1")
        self.crm.discount(self.opp, 10, "r1")
        self.crm.discount(self.opp, 10, "r1")
        # compounding 10%: 1000 -> 900 -> 810 -> 729 (still >= 70% of original)
        self.assertEqual(self.crm.opps[self.opp]["amount"], 729)
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp, 5, "r1")  # 692 < 700
        self.assertEqual(self.crm.opps[self.opp]["amount"], 729)

    def test_final_stage(self):
        self.crm.advance(self.opp, "lost", "r1")
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp, 5, "r1")


class TestTransfer(unittest.TestCase):
    def setUp(self):
        self.crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 2},
            {"id": "r2", "role": "rep", "capacity": 2},
            {"id": "m1", "role": "manager", "capacity": 9},
        ])
        lead = self.crm.add_lead("a@corp.com", "A", "referral", "r1")
        self.crm.qualify(lead, "r1")
        self.opp = self.crm.convert(lead, 1000, "r1")

    def test_success(self):
        self.crm.transfer(self.opp, "r2", "m1")
        self.assertEqual(self.crm.opps[self.opp]["owner"], "r2")
        self.assertEqual(self.crm.log[-1], ("transfer", self.opp, "m1"))

    def test_errors(self):
        with self.assertRaises(ValueError):
            self.crm.transfer("O9", "r2", "m1")
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.opp, "r2", "r1")
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "m1", "m1")
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "nobody", "m1")
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "r1", "m1")
        self.assertEqual(self.crm.opps[self.opp]["owner"], "r1")

    def test_capacity_error(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 5},
            {"id": "r2", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 9},
        ])
        lead = crm.add_lead("z@corp.com", "Z", "referral", "r1")  # r1, tied lowest id
        other = crm.add_lead("a@corp.com", "A", "referral", "r1")  # r2 (load 0)
        self.assertEqual(crm.leads[lead]["owner"], "r1")
        self.assertEqual(crm.leads[other]["owner"], "r2")  # r2 now full
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 100, "r1")
        with self.assertRaises(ValueError):
            crm.transfer(opp, "r2", "m1")

    def test_final_stage_error(self):
        self.crm.advance(self.opp, "lost", "r1")
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "r2", "m1")

    def test_transfer_assigns_waiting(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 0},
            {"id": "m1", "role": "manager", "capacity": 9},
        ])
        lead = crm.add_lead("a@corp.com", "A", "referral", "r1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 100, "r1")
        waiting = crm.add_lead("b@corp.com", "B", "referral", "r1")
        # r2 cannot take anything (capacity 0); use a third rep with room
        crm.reps["r3"] = {"id": "r3", "role": "rep", "capacity": 2}
        crm.transfer(opp, "r3", "m1")
        self.assertEqual(crm.leads[waiting]["owner"], "r1")
        self.assertEqual(crm.log[-1], ("assign", waiting, "system"))


class TestForecastAndLog(unittest.TestCase):
    def test_weighted_rounding(self):
        crm = CRM(reps())
        lead = crm.add_lead("a@corp.com", "A", "referral", "r1")
        crm.qualify(lead, "r1")
        o1 = crm.convert(lead, 1001, "r1")
        lead2 = crm.add_lead("b@corp.com", "B", "referral", "r2")
        crm.qualify(lead2, "r2")
        o2 = crm.convert(lead2, 333, "r2")
        crm.advance(o2, "proposal", "r2")
        self.assertEqual(crm.forecast(), {"open": 2, "weighted": 100 + 99, "won": 0})
        crm.advance(o1, "proposal", "r1")
        crm.advance(o1, "negotiation", "r1")
        crm.advance(o1, "won", "r1")
        crm.advance(o2, "negotiation", "r2")
        crm.advance(o2, "won", "r2")
        self.assertEqual(crm.forecast(), {"open": 0, "weighted": 0, "won": 1334})

    def test_forecast_empty(self):
        self.assertEqual(CRM(reps()).forecast(), {"open": 0, "weighted": 0, "won": 0})

    def test_managers_never_own(self):
        crm = CRM([{"id": "m1", "role": "manager", "capacity": 5}])
        lead = crm.add_lead("a@corp.com", "A", "referral", "m1")
        self.assertIsNone(crm.leads[lead]["owner"])

    def test_failed_calls_do_not_change_state(self):
        crm = CRM(reps())
        lead = crm.add_lead("a@corp.com", "A", "referral", "r1")
        crm.qualify(lead, "r1")
        before_log = list(crm.log)
        before_leads = {k: dict(v) for k, v in crm.leads.items()}
        with self.assertRaises(DuplicateLeadError):
            crm.add_lead("a@corp.com", "dup", "web", "r1")
        with self.assertRaises(PermissionError):
            crm.qualify(lead, "r2")
        self.assertEqual(crm.log, before_log)
        self.assertEqual(crm.leads, before_leads)
        # lead counter untouched -> next id continues the sequence
        self.assertEqual(crm.add_lead("b@corp.com", "B", "web", "r1"), "L2")


class TestUnknownActorEverywhere(unittest.TestCase):
    def test_all_methods(self):
        crm = CRM(reps())
        lead = crm.add_lead("a@corp.com", "A", "referral", "r1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 100, "r1")
        with self.assertRaises(PermissionError):
            crm.qualify(lead, "ghost")
        with self.assertRaises(PermissionError):
            crm.convert(lead, 100, "ghost")
        with self.assertRaises(PermissionError):
            crm.advance(opp, "proposal", "ghost")
        with self.assertRaises(PermissionError):
            crm.discount(opp, 5, "ghost")
        with self.assertRaises(PermissionError):
            crm.transfer(opp, "r2", "ghost")
        self.assertEqual(len(crm.log), 3)


if __name__ == "__main__":
    unittest.main()
