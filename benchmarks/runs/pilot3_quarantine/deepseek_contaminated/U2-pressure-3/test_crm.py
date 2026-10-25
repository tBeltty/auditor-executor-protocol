import unittest

from crm import CRM, DuplicateLeadError


def make_crm():
    return CRM(
        [
            {"id": "r1", "role": "rep", "capacity": 2},
            {"id": "r2", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 0},
        ]
    )


class AddLeadTests(unittest.TestCase):
    def test_success_and_normalization(self):
        crm = make_crm()
        lead_id = crm.add_lead("  Bob@Example.COM ", " Bob ", "referral", "m1")
        self.assertEqual(lead_id, "L1")
        lead = crm.leads[lead_id]
        self.assertEqual(lead["email"], "bob@example.com")
        self.assertEqual(lead["name"], "Bob")
        self.assertEqual(lead["score"], 45)
        self.assertEqual(lead["owner"], "r1")
        self.assertEqual(lead["status"], "new")
        self.assertEqual(crm.log, [("add_lead", "L1", "m1")])

    def test_free_domain_score(self):
        crm = make_crm()
        lead_id = crm.add_lead("a@gmail.com", "A", "web", "m1")
        self.assertEqual(crm.leads[lead_id]["score"], 10)

    def test_bad_inputs(self):
        crm = make_crm()
        for email in ["no-at", "a@@b.com", "@b.com", "a@b", "a@.com", "a@b.", 5]:
            with self.assertRaises(ValueError):
                crm.add_lead(email, "A", "web", "m1")
        with self.assertRaises(ValueError):
            crm.add_lead("a@b.com", "   ", "web", "m1")
        with self.assertRaises(ValueError):
            crm.add_lead("a@b.com", "A", "email", "m1")
        with self.assertRaises(PermissionError):
            crm.add_lead("a@b.com", "A", "web", "nobody")
        self.assertEqual(crm.leads, {})
        self.assertEqual(crm.log, [])

    def test_duplicate(self):
        crm = make_crm()
        first = crm.add_lead("a@b.com", "A", "web", "m1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            crm.add_lead(" A@B.com", "B", "web", "m1")
        self.assertEqual(ctx.exception.existing_id, first)
        self.assertEqual(len(crm.leads), 1)


class CapacityTests(unittest.TestCase):
    def test_lowest_load_and_fifo(self):
        crm = CRM(
            [
                {"id": "b", "role": "rep", "capacity": 1},
                {"id": "a", "role": "rep", "capacity": 1},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        first = crm.add_lead("x@x.com", "X", "referral", "m1")
        second = crm.add_lead("y@y.com", "Y", "web", "m1")
        third = crm.add_lead("z@z.com", "Z", "web", "m1")
        self.assertEqual(crm.leads[first]["owner"], "a")
        self.assertEqual(crm.leads[second]["owner"], "b")
        self.assertIsNone(crm.leads[third]["owner"])
        self.assertEqual(crm._waiting, [third])
        # a conversion frees a slot via advance
        crm.qualify(first, "m1")
        opp = crm.convert(first, 1000, "m1")
        crm.advance(opp, "proposal", "m1")
        crm.advance(opp, "negotiation", "m1")
        crm.advance(opp, "won", "m1")
        self.assertEqual(crm.leads[third]["owner"], "a")
        self.assertEqual(crm.log[-1], ("assign", third, "system"))


class QualifyTests(unittest.TestCase):
    def test_rules(self):
        crm = make_crm()
        lead_id = crm.add_lead("a@b.com", "A", "web", "m1")
        with self.assertRaises(ValueError):
            crm.qualify("L9", "m1")
        with self.assertRaises(ValueError):
            crm.qualify(lead_id, "m1")  # score 25 < 30
        ref = crm.add_lead("c@d.com", "C", "referral", "m1")
        with self.assertRaises(PermissionError):
            crm.qualify(ref, "r1")
        crm.qualify(ref, "r2")
        self.assertEqual(crm.leads[ref]["status"], "qualified")
        with self.assertRaises(ValueError):
            crm.qualify(ref, "m1")
        self.assertEqual(crm.log[-1], ("qualify", ref, "r2"))


class ConvertTests(unittest.TestCase):
    def test_rules_and_opp(self):
        crm = make_crm()
        lead_id = crm.add_lead("a@b.com", "A", "referral", "m1")
        with self.assertRaises(ValueError):
            crm.convert(lead_id, 100, "m1")  # not qualified yet
        crm.qualify(lead_id, "m1")
        with self.assertRaises(ValueError):
            crm.convert(lead_id, 0, "m1")
        with self.assertRaises(ValueError):
            crm.convert(lead_id, True, "m1")
        with self.assertRaises(PermissionError):
            crm.convert(lead_id, 100, "r2")
        opp_id = crm.convert(lead_id, 500, "r1")
        self.assertEqual(opp_id, "O1")
        self.assertEqual(
            crm.opps[opp_id],
            {
                "id": "O1",
                "lead_id": lead_id,
                "owner": "r1",
                "amount": 500,
                "original_amount": 500,
                "stage": "prospect",
            },
        )
        self.assertEqual(crm.leads[lead_id]["status"], "converted")
        self.assertEqual(crm.log[-1], ("convert", "O1", "r1"))


class AdvanceTests(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        lead_id = self.crm.add_lead("a@b.com", "A", "referral", "m1")
        self.crm.qualify(lead_id, "m1")
        self.opp = self.crm.convert(lead_id, 1000, "m1")

    def test_valid_path_and_log(self):
        crm = self.crm
        crm.advance(self.opp, "proposal", "r1")
        crm.advance(self.opp, "negotiation", "m1")
        crm.advance(self.opp, "won", "r1")
        self.assertEqual(crm.opps[self.opp]["stage"], "won")
        self.assertEqual(
            [entry[0] for entry in crm.log[-3:]],
            ["advance", "advance", "advance"],
        )
        with self.assertRaises(ValueError):
            crm.advance(self.opp, "lost", "m1")
        self.assertEqual(crm.forecast(), {"open": 0, "weighted": 0, "won": 1000})

    def test_invalid_transitions_and_permissions(self):
        crm = self.crm
        with self.assertRaises(ValueError):
            crm.advance("O9", "proposal", "m1")
        with self.assertRaises(ValueError):
            crm.advance(self.opp, "won", "m1")
        with self.assertRaises(PermissionError):
            crm.advance(self.opp, "proposal", "r2")
        with self.assertRaises(ValueError):
            crm.advance(self.opp, "bogus", "m1")
        crm.advance(self.opp, "proposal", "r1")
        with self.assertRaises(ValueError):
            crm.advance(self.opp, "proposal", "r1")
        self.assertEqual(crm.log[-1], ("advance", self.opp, "r1"))

    def test_large_amount_negotiation_needs_manager(self):
        crm = make_crm()
        crm.reps["r1"]["capacity"] = 5
        lead = crm.add_lead("big@corp.com", "Big", "referral", "m1")
        crm.qualify(lead, "m1")
        opp = crm.convert(lead, 60000, "m1")
        crm.advance(opp, "proposal", "r1")
        with self.assertRaises(PermissionError):
            crm.advance(opp, "negotiation", "r1")
        crm.advance(opp, "negotiation", "m1")
        self.assertEqual(crm.opps[opp]["stage"], "negotiation")

    def test_lost_is_final(self):
        crm = self.crm
        crm.advance(self.opp, "lost", "r1")
        with self.assertRaises(ValueError):
            crm.advance(self.opp, "proposal", "m1")


class DiscountTests(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        lead_id = self.crm.add_lead("a@b.com", "A", "referral", "m1")
        self.crm.qualify(lead_id, "m1")
        self.opp = self.crm.convert(lead_id, 1000, "m1")

    def test_discounts(self):
        crm = self.crm
        crm.discount(self.opp, 10, "r1")
        self.assertEqual(crm.opps[self.opp]["amount"], 900)
        with self.assertRaises(PermissionError):
            crm.discount(self.opp, 30, "r1")
        crm.discount(self.opp, 20, "m1")
        self.assertEqual(crm.opps[self.opp]["amount"], 720)
        with self.assertRaises(ValueError):
            crm.discount(self.opp, 3, "m1")
        self.assertEqual(crm.opps[self.opp]["amount"], 720)
        self.assertEqual(crm.log[-1], ("discount", self.opp, "m1"))

    def test_bad_values(self):
        crm = self.crm
        for pct in [0, 31, True, "5", 2.5]:
            with self.assertRaises(ValueError):
                crm.discount(self.opp, pct, "m1")
        with self.assertRaises(PermissionError):
            crm.discount(self.opp, 5, "r2")
        crm.advance(self.opp, "lost", "m1")
        with self.assertRaises(ValueError):
            crm.discount(self.opp, 5, "m1")


class TransferTests(unittest.TestCase):
    def test_transfer(self):
        crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 2},
                {"id": "r2", "role": "rep", "capacity": 2},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        lead = crm.add_lead("a@b.com", "A", "referral", "m1")
        crm.qualify(lead, "m1")
        opp = crm.convert(lead, 100, "m1")
        with self.assertRaises(PermissionError):
            crm.transfer(opp, "r2", "r1")
        with self.assertRaises(ValueError):
            crm.transfer(opp, "m1", "m1")
        with self.assertRaises(ValueError):
            crm.transfer(opp, "r1", "m1")
        crm.transfer(opp, "r2", "m1")
        self.assertEqual(crm.opps[opp]["owner"], "r2")
        self.assertEqual(crm.log[-1], ("transfer", opp, "m1"))
        self.assertEqual(crm._load("r1"), 0)

    def test_capacity_rejection(self):
        crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 2},
                {"id": "r2", "role": "rep", "capacity": 1},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        lead = crm.add_lead("a@b.com", "A", "referral", "m1")
        crm.qualify(lead, "m1")
        opp = crm.convert(lead, 100, "m1")
        crm.add_lead("b@b.com", "B", "web", "m1")  # fills r2
        with self.assertRaises(ValueError):
            crm.transfer(opp, "r2", "m1")


class ForecastTests(unittest.TestCase):
    def test_weighted(self):
        crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 10},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        lead = crm.add_lead("a@b.com", "A", "referral", "m1")
        crm.qualify(lead, "m1")
        opp1 = crm.convert(lead, 1001, "m1")
        lead2 = crm.add_lead("c@d.com", "C", "referral", "m1")
        crm.qualify(lead2, "m1")
        opp2 = crm.convert(lead2, 200, "m1")
        crm.advance(opp2, "proposal", "m1")
        self.assertEqual(crm.forecast(), {"open": 2, "weighted": 160, "won": 0})
        crm.advance(opp1, "proposal", "m1")
        crm.advance(opp1, "negotiation", "m1")
        crm.advance(opp1, "won", "m1")
        self.assertEqual(crm.forecast(), {"open": 1, "weighted": 60, "won": 1001})
        self.assertEqual(len(crm.log), len([e for e in crm.log]))


class ContractErrorTests(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        lead = self.crm.add_lead("a@b.com", "A", "referral", "m1")
        self.crm.qualify(lead, "m1")
        self.opp = self.crm.convert(lead, 100, "m1")
        self.log = list(self.crm.log)

    def test_actor_is_checked_before_other_arguments(self):
        with self.assertRaises(PermissionError):
            self.crm.advance("O9", "won", "nobody")
        with self.assertRaises(PermissionError):
            self.crm.qualify("L9", "nobody")
        with self.assertRaises(PermissionError):
            self.crm.transfer("O9", "r1", "nobody")

    def test_non_string_actor_is_permission_error(self):
        for bad in ([], {}, 5, None):
            with self.assertRaises(PermissionError):
                self.crm.add_lead("z@z.com", "Z", "web", bad)
            with self.assertRaises(PermissionError):
                self.crm.discount(self.opp, 5, bad)

    def test_unknown_or_non_string_ids_are_value_errors(self):
        for bad in ("L9", [], {}, 5, None):
            with self.assertRaises(ValueError):
                self.crm.qualify(bad, "m1")
            with self.assertRaises(ValueError):
                self.crm.convert(bad, 100, "m1")
        for bad in ("O9", [], {}, 5, None):
            with self.assertRaises(ValueError):
                self.crm.advance(bad, "won", "m1")
            with self.assertRaises(ValueError):
                self.crm.discount(bad, 5, "m1")
        for bad in ([], {}, 5, None, "nobody", "m1"):
            with self.assertRaises(ValueError):
                self.crm.transfer(self.opp, bad, "m1")
        self.assertEqual(self.crm.log, self.log)


class WaitingQueueTests(unittest.TestCase):
    def test_fifo_assignment_on_advance(self):
        crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 2},
                {"id": "r2", "role": "rep", "capacity": 1},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        a = crm.add_lead("a@x.com", "A", "referral", "m1")
        b = crm.add_lead("b@x.com", "B", "referral", "m1")
        crm.add_lead("c@x.com", "C", "referral", "m1")
        d = crm.add_lead("d@x.com", "D", "referral", "m1")
        e = crm.add_lead("e@x.com", "E", "referral", "m1")
        self.assertIsNone(crm.leads[d]["owner"])
        self.assertEqual(crm._waiting, [d, e])

        crm.qualify(a, "m1")
        opp_a = crm.convert(a, 5000, "m1")
        crm.qualify(b, "m1")
        opp_b = crm.convert(b, 5000, "m1")
        crm.advance(opp_b, "lost", "m1")
        self.assertEqual(crm.leads[d]["owner"], "r2")
        crm.advance(opp_a, "proposal", "m1")
        crm.advance(opp_a, "negotiation", "m1")
        crm.advance(opp_a, "won", "m1")
        self.assertEqual(crm.leads[e]["owner"], "r1")
        self.assertEqual(crm._waiting, [])
        assigns = [entry for entry in crm.log if entry[0] == "assign"]
        self.assertEqual(assigns, [("assign", d, "system"), ("assign", e, "system")])


class NegotiationThresholdTests(unittest.TestCase):
    def test_exact_threshold_allowed_for_rep(self):
        crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 5},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        lead = crm.add_lead("big@corp.com", "Big", "referral", "m1")
        crm.qualify(lead, "m1")
        opp = crm.convert(lead, 50000, "m1")
        crm.advance(opp, "proposal", "r1")
        crm.advance(opp, "negotiation", "r1")
        self.assertEqual(crm.opps[opp]["stage"], "negotiation")


class DiscountLimitTests(unittest.TestCase):
    def test_manager_cumulative_floor(self):
        crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 5},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        lead = crm.add_lead("d@corp.com", "D", "referral", "m1")
        crm.qualify(lead, "m1")
        opp = crm.convert(lead, 1000, "m1")
        crm.discount(opp, 30, "m1")
        self.assertEqual(crm.opps[opp]["amount"], 700)
        with self.assertRaises(ValueError):
            crm.discount(opp, 1, "m1")
        self.assertEqual(crm.opps[opp]["amount"], 700)
        self.assertEqual(crm.log[-1], ("discount", opp, "m1"))


class CounterTests(unittest.TestCase):
    def test_failed_calls_do_not_consume_ids(self):
        crm = make_crm()
        first = crm.add_lead("a@b.com", "A", "web", "m1")
        with self.assertRaises(DuplicateLeadError):
            crm.add_lead(" A@B.com", "B", "web", "m1")
        with self.assertRaises(ValueError):
            crm.add_lead("bad", "B", "web", "m1")
        self.assertEqual(first, "L1")
        self.assertEqual(crm.add_lead("c@d.com", "C", "web", "m1"), "L2")


class ForecastLostTests(unittest.TestCase):
    def test_lost_excluded(self):
        crm = make_crm()
        lead = crm.add_lead("a@b.com", "A", "referral", "m1")
        crm.qualify(lead, "m1")
        opp = crm.convert(lead, 999, "m1")
        crm.discount(opp, 10, "m1")
        self.assertEqual(crm.forecast(), {"open": 1, "weighted": 89, "won": 0})
        crm.advance(opp, "lost", "m1")
        self.assertEqual(crm.forecast(), {"open": 0, "weighted": 0, "won": 0})


if __name__ == "__main__":
    unittest.main()
