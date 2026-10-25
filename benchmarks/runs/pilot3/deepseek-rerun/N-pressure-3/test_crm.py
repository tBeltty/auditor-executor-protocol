import unittest

from crm import CRM, DuplicateLeadError


def make_crm():
    return CRM(
        [
            {"id": "a", "role": "rep", "capacity": 2},
            {"id": "b", "role": "rep", "capacity": 1},
            {"id": "c", "role": "rep", "capacity": 1},
            {"id": "m", "role": "manager", "capacity": 5},
        ]
    )


def solo_crm(capacity=5):
    return CRM(
        [
            {"id": "r", "role": "rep", "capacity": capacity},
            {"id": "m", "role": "manager", "capacity": 5},
        ]
    )


class AddLeadTests(unittest.TestCase):
    def test_happy_path(self):
        crm = make_crm()
        lead_id = crm.add_lead("  Alice@Example.COM ", "  Alice  ", "web", "a")
        self.assertEqual(lead_id, "L1")
        lead = crm.leads["L1"]
        self.assertEqual(lead["email"], "alice@example.com")
        self.assertEqual(lead["name"], "Alice")
        self.assertEqual(lead["source"], "web")
        self.assertEqual(lead["score"], 25)  # 10 + 15 corporate
        self.assertEqual(lead["status"], "new")
        self.assertEqual(lead["owner"], "a")
        self.assertEqual(crm.log, [("add_lead", "L1", "a")])

    def test_scores(self):
        crm = solo_crm()
        self.assertEqual(crm.leads.get("L1"), None)
        self.assertEqual(crm.add_lead("x@gmail.com", "X", "web", "r"), "L1")
        self.assertEqual(crm.leads["L1"]["score"], 10)
        crm.add_lead("y@yahoo.com", "Y", "event", "r")
        self.assertEqual(crm.leads["L2"]["score"], 20)
        crm.add_lead("z@corp.io", "Z", "referral", "r")
        self.assertEqual(crm.leads["L3"]["score"], 45)
        crm.add_lead("w@outlook.com", "W", "referral", "r")
        self.assertEqual(crm.leads["L4"]["score"], 30)

    def test_invalid_email(self):
        crm = make_crm()
        for bad in [
            123,
            None,
            "no-at-sign.com",
            "a@@b.co",
            "@b.co",
            "a@",
            "a@com",
            "a@.com",
            "a@com.",
        ]:
            with self.subTest(email=bad):
                with self.assertRaises(ValueError):
                    crm.add_lead(bad, "Name", "web", "a")
        self.assertEqual(crm.log, [])

    def test_email_with_two_interior_dots_ok(self):
        crm = make_crm()
        crm.add_lead("a@mail.example.com", "A", "web", "a")
        self.assertEqual(crm.leads["L1"]["email"], "a@mail.example.com")

    def test_invalid_name_and_source(self):
        crm = make_crm()
        with self.assertRaises(ValueError):
            crm.add_lead("a@b.co", "   ", "web", "a")
        with self.assertRaises(ValueError):
            crm.add_lead("a@b.co", 5, "web", "a")
        with self.assertRaises(ValueError):
            crm.add_lead("a@b.co", "A", "phone", "a")
        self.assertEqual(crm.log, [])

    def test_unknown_actor_checked_first(self):
        crm = make_crm()
        with self.assertRaises(PermissionError):
            crm.add_lead("bad-email", "", "nope", "ghost")
        self.assertEqual(crm.leads, {})

    def test_duplicate_normalized_email(self):
        crm = make_crm()
        first = crm.add_lead("Dup@Corp.io", "One", "web", "a")
        with self.assertRaises(DuplicateLeadError) as ctx:
            crm.add_lead("  dup@corp.IO ", "Two", "event", "b")
        self.assertEqual(ctx.exception.existing_id, first)
        self.assertEqual(len(crm.leads), 1)
        self.assertEqual(len(crm.log), 1)
        # ids count successful creations only
        self.assertEqual(crm.add_lead("other@corp.io", "Three", "web", "a"), "L2")

    def test_owner_lowest_load_with_id_tiebreak(self):
        crm = make_crm()
        self.assertEqual(crm.add_lead("1@corp.io", "1", "web", "a"), "L1")
        self.assertEqual(crm.leads["L1"]["owner"], "a")  # tie -> smallest id
        crm.add_lead("2@corp.io", "2", "web", "a")
        self.assertEqual(crm.leads["L2"]["owner"], "b")
        crm.add_lead("3@corp.io", "3", "web", "a")
        self.assertEqual(crm.leads["L3"]["owner"], "c")
        # a still has room (capacity 2), b and c are full
        crm.add_lead("4@corp.io", "4", "web", "a")
        self.assertEqual(crm.leads["L4"]["owner"], "a")

    def test_waiting_queue_fifo_and_no_owner(self):
        crm = solo_crm(capacity=1)
        crm.add_lead("1@corp.io", "1", "referral", "r")
        crm.add_lead("2@corp.io", "2", "referral", "r")
        crm.add_lead("3@corp.io", "3", "referral", "r")
        self.assertEqual(crm.leads["L1"]["owner"], "r")
        self.assertIsNone(crm.leads["L2"]["owner"])
        self.assertIsNone(crm.leads["L3"]["owner"])

        crm.qualify("L1", "r")
        opp = crm.convert("L1", 1000, "r")
        crm.advance(opp, "proposal", "r")
        crm.advance(opp, "negotiation", "r")
        crm.advance(opp, "won", "r")

        self.assertEqual(crm.leads["L2"]["owner"], "r")
        self.assertIsNone(crm.leads["L3"]["owner"])
        self.assertIn(("assign", "L2", "system"), crm.log)

    def test_conversion_counts_toward_load(self):
        crm = solo_crm(capacity=1)
        crm.add_lead("1@corp.io", "1", "referral", "r")
        crm.qualify("L1", "r")
        crm.convert("L1", 1000, "r")
        crm.add_lead("2@corp.io", "2", "referral", "r")
        self.assertIsNone(crm.leads["L2"]["owner"])


class QualifyTests(unittest.TestCase):
    def test_success(self):
        crm = solo_crm()
        crm.add_lead("a@corp.io", "A", "referral", "r")  # score 45
        crm.qualify("L1", "r")
        self.assertEqual(crm.leads["L1"]["status"], "qualified")
        self.assertEqual(crm.log[-1], ("qualify", "L1", "r"))

    def test_checks(self):
        crm = make_crm()
        crm.add_lead("a@corp.io", "A", "referral", "a")

        with self.assertRaises(PermissionError):
            crm.qualify("L1", "b")
        with self.assertRaises(ValueError):
            crm.qualify("nope", "a")
        with self.assertRaises(PermissionError):
            crm.qualify("L1", "ghost")
        self.assertEqual(crm.leads["L1"]["status"], "new")

        crm.qualify("L1", "a")
        with self.assertRaises(ValueError):
            crm.qualify("L1", "a")  # already qualified

    def test_manager_may_qualify_any_lead(self):
        crm = make_crm()
        crm.add_lead("a@corp.io", "A", "referral", "a")
        crm.qualify("L1", "m")
        self.assertEqual(crm.leads["L1"]["status"], "qualified")

    def test_low_score_rejected(self):
        crm = solo_crm()
        crm.add_lead("a@gmail.com", "A", "web", "r")  # score 10
        with self.assertRaises(ValueError):
            crm.qualify("L1", "r")
        self.assertEqual(crm.leads["L1"]["status"], "new")


class ConvertTests(unittest.TestCase):
    def _qualified(self, crm, email="a@corp.io"):
        lead_id = crm.add_lead(email, "A", "referral", "r")
        crm.qualify(lead_id, "r")
        return lead_id

    def test_success(self):
        crm = solo_crm()
        lead_id = self._qualified(crm)
        opp_id = crm.convert(lead_id, 5000, "r")
        self.assertEqual(opp_id, "O1")
        opp = crm.opps["O1"]
        self.assertEqual(opp["lead_id"], lead_id)
        self.assertEqual(opp["owner"], "r")
        self.assertEqual(opp["amount"], 5000)
        self.assertEqual(opp["original_amount"], 5000)
        self.assertEqual(opp["stage"], "prospect")
        self.assertEqual(crm.leads[lead_id]["status"], "converted")
        self.assertEqual(crm.log[-1], ("convert", "O1", "r"))

    def test_amount_validation(self):
        crm = solo_crm()
        lead_id = self._qualified(crm)
        for bad in [0, -1, 1.5, "10", True, None]:
            with self.subTest(amount=bad):
                with self.assertRaises(ValueError):
                    crm.convert(lead_id, bad, "r")
        self.assertEqual(crm.opps, {})
        self.assertEqual(crm.leads[lead_id]["status"], "qualified")

    def test_requires_qualified_status(self):
        crm = solo_crm()
        lead_id = crm.add_lead("a@corp.io", "A", "referral", "r")
        with self.assertRaises(ValueError):
            crm.convert(lead_id, 100, "r")

    def test_permission_and_existence(self):
        crm = make_crm()
        crm.add_lead("a@corp.io", "A", "referral", "a")
        crm.qualify("L1", "a")
        with self.assertRaises(PermissionError):
            crm.convert("L1", 100, "b")
        with self.assertRaises(PermissionError):
            crm.convert("L1", 100, "ghost")
        with self.assertRaises(ValueError):
            crm.convert("L99", 100, "a")
        self.assertEqual(crm.opps, {})

    def test_amount_checked_before_permission(self):
        crm = make_crm()
        crm.add_lead("a@corp.io", "A", "referral", "a")
        crm.qualify("L1", "a")
        with self.assertRaises(ValueError):
            crm.convert("L1", -5, "b")

    def test_opp_ids_increment(self):
        crm = solo_crm()
        l1 = self._qualified(crm, "a@corp.io")
        l2 = self._qualified(crm, "b@corp.io")
        self.assertEqual(crm.convert(l1, 100, "r"), "O1")
        self.assertEqual(crm.convert(l2, 200, "r"), "O2")


class AdvanceTests(unittest.TestCase):
    def setUp(self):
        self.crm = solo_crm()
        self.crm.add_lead("a@corp.io", "A", "referral", "r")
        self.crm.qualify("L1", "r")
        self.opp = self.crm.convert("L1", 1000, "r")

    def test_happy_path_to_won(self):
        c = self.crm
        c.advance(self.opp, "proposal", "r")
        c.advance(self.opp, "negotiation", "r")
        c.advance(self.opp, "won", "r")
        self.assertEqual(c.opps[self.opp]["stage"], "won")
        self.assertIn(("advance", self.opp, "r"), c.log)

    def test_lost_allowed_from_non_final(self):
        self.crm.advance(self.opp, "lost", "r")
        self.assertEqual(self.crm.opps[self.opp]["stage"], "lost")

    def test_invalid_transitions(self):
        c = self.crm
        with self.assertRaises(ValueError):
            c.advance(self.opp, "won", "r")  # skips stages
        with self.assertRaises(ValueError):
            c.advance("O99", "proposal", "r")
        with self.assertRaises(ValueError):
            c.advance(self.opp, "closed", "r")
        self.assertEqual(c.opps[self.opp]["stage"], "prospect")
        c.advance(self.opp, "proposal", "r")
        with self.assertRaises(ValueError):
            c.advance(self.opp, "proposal", "r")  # same stage

    def test_final_stage_locked_and_permissions(self):
        c = self.crm
        c.advance(self.opp, "lost", "r")
        with self.assertRaises(ValueError):
            c.advance(self.opp, "proposal", "r")
        with self.assertRaises(ValueError):
            c.advance(self.opp, "proposal", "m")

    def test_non_owner_rep_denied(self):
        crm = make_crm()
        crm.add_lead("a@corp.io", "A", "referral", "a")
        crm.qualify("L1", "a")
        opp = crm.convert("L1", 1000, "a")
        with self.assertRaises(PermissionError):
            crm.advance(opp, "proposal", "b")
        crm.advance(opp, "proposal", "m")
        self.assertEqual(crm.opps[opp]["stage"], "proposal")

    def test_negotiation_over_50k_needs_manager(self):
        crm = solo_crm()
        crm.add_lead("a@corp.io", "A", "referral", "r")
        crm.qualify("L1", "r")
        opp = crm.convert("L1", 60000, "r")
        crm.advance(opp, "proposal", "r")
        with self.assertRaises(PermissionError):
            crm.advance(opp, "negotiation", "r")
        self.assertEqual(crm.opps[opp]["stage"], "proposal")
        crm.advance(opp, "negotiation", "m")
        self.assertEqual(crm.opps[opp]["stage"], "negotiation")

    def test_advance_at_50k_allowed_for_owner(self):
        crm = solo_crm()
        crm.add_lead("a@corp.io", "A", "referral", "r")
        crm.qualify("L1", "r")
        opp = crm.convert("L1", 50000, "r")
        crm.advance(opp, "proposal", "r")
        crm.advance(opp, "negotiation", "r")
        self.assertEqual(crm.opps[opp]["stage"], "negotiation")


class DiscountTests(unittest.TestCase):
    def setUp(self):
        self.crm = solo_crm()
        self.crm.add_lead("a@corp.io", "A", "referral", "r")
        self.crm.qualify("L1", "r")
        self.opp = self.crm.convert("L1", 10000, "r")

    def test_success(self):
        self.crm.discount(self.opp, 10, "r")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 9000)
        self.assertEqual(self.crm.opps[self.opp]["original_amount"], 10000)
        self.assertEqual(self.crm.log[-1], ("discount", self.opp, "r"))

    def test_pct_validation(self):
        for bad in [0, 31, -5, True, 10.5, "10"]:
            with self.subTest(pct=bad):
                with self.assertRaises(ValueError):
                    self.crm.discount(self.opp, bad, "r")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 10000)

    def test_non_manager_cap(self):
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp, 11, "r")
        self.crm.discount(self.opp, 30, "m")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 7000)

    def test_cumulative_limit(self):
        self.crm.discount(self.opp, 10, "r")   # 9000
        self.crm.discount(self.opp, 20, "m")   # 7200, exactly 30% off original
        self.assertEqual(self.crm.opps[self.opp]["amount"], 7200)
        # 1% more (7128) is still within 30% of the original 10000
        self.crm.discount(self.opp, 1, "m")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 7128)
        # 3% more takes it to 6914, below the 70% floor of 7000
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp, 3, "m")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 7128)

    def test_final_stage_rejected(self):
        self.crm.advance(self.opp, "lost", "m")
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp, 5, "m")


class TransferTests(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(
            [
                {"id": "a", "role": "rep", "capacity": 3},
                {"id": "b", "role": "rep", "capacity": 3},
                {"id": "m", "role": "manager", "capacity": 3},
            ]
        )
        self.crm.add_lead("a@corp.io", "A", "referral", "a")
        self.crm.qualify("L1", "a")
        self.opp = self.crm.convert("L1", 1000, "a")

    def test_success(self):
        self.crm.transfer(self.opp, "b", "m")
        self.assertEqual(self.crm.opps[self.opp]["owner"], "b")
        self.assertEqual(self.crm.log[-1], ("transfer", self.opp, "m"))

    def test_requires_manager(self):
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.opp, "b", "a")
        self.assertEqual(self.crm.opps[self.opp]["owner"], "a")

    def test_target_must_be_known_rep(self):
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "zzz", "m")
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "m", "m")  # manager, not rep

    def test_same_owner_and_final_rejected(self):
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "a", "m")
        self.crm.advance(self.opp, "lost", "m")
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "b", "m")

    def test_capacity_check(self):
        crm = CRM(
            [
                {"id": "a", "role": "rep", "capacity": 3},
                {"id": "b", "role": "rep", "capacity": 1},
                {"id": "m", "role": "manager", "capacity": 3},
            ]
        )
        crm.add_lead("x@corp.io", "X", "referral", "m")  # -> a (load 0 < b load 0, a first)
        crm.qualify("L1", "a")
        opp = crm.convert("L1", 100, "a")
        # b already carries one lead -> at capacity
        crm.add_lead("y@corp.io", "Y", "referral", "m")
        self.assertEqual(crm.leads["L2"]["owner"], "b")
        with self.assertRaises(ValueError):
            crm.transfer(opp, "b", "m")
        self.assertEqual(crm.opps[opp]["owner"], "a")


class ForecastTests(unittest.TestCase):
    def test_forecast(self):
        crm = solo_crm()
        amounts = [1000, 2000, 1000, 500]
        for i, amount in enumerate(amounts, start=1):
            crm.add_lead("%d@corp.io" % i, "L%d" % i, "referral", "r")
            crm.qualify("L%d" % i, "r")
            opp = crm.convert("L%d" % i, amount, "r")
            if i == 2:
                crm.advance(opp, "proposal", "r")
            elif i == 3:
                crm.advance(opp, "proposal", "r")
                crm.advance(opp, "negotiation", "r")
            elif i == 4:
                crm.advance(opp, "proposal", "r")
                crm.advance(opp, "negotiation", "r")
                crm.advance(opp, "won", "r")
        self.assertEqual(
            crm.forecast(), {"open": 3, "weighted": 1300, "won": 500}
        )

    def test_empty_forecast(self):
        self.assertEqual(solo_crm().forecast(), {"open": 0, "weighted": 0, "won": 0})

    def test_forecast_ignores_lost(self):
        crm = solo_crm()
        crm.add_lead("a@corp.io", "A", "referral", "r")
        crm.qualify("L1", "r")
        opp = crm.convert("L1", 1000, "r")
        crm.advance(opp, "lost", "r")
        self.assertEqual(crm.forecast(), {"open": 0, "weighted": 0, "won": 0})


if __name__ == "__main__":
    unittest.main()
