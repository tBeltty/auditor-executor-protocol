import unittest

from crm import CRM


def make_crm():
    return CRM(
        [
            {"id": "r1", "role": "rep", "capacity": 5},
            {"id": "r2", "role": "rep", "capacity": 5},
            {"id": "m1", "role": "manager", "capacity": 5},
        ]
    )


def new_opp(crm, amount=1000, email="deal@corp.com"):
    lead_id = crm.add_lead(email, "Deal", "referral", "m1")
    crm.qualify(lead_id, "m1")
    return crm.convert(lead_id, amount, "m1")


class DiscountTests(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        self.opp_id = new_opp(self.crm)

    def test_unknown_opp_checked_first(self):
        with self.assertRaises(ValueError):
            self.crm.discount("O99", 5, "r1")

    def test_pct_validation(self):
        for bad in (0, 31, -1, True, False, 5.0, "5", None):
            with self.assertRaises(ValueError, msg=repr(bad)):
                self.crm.discount(self.opp_id, bad, "r1")
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 1000)
        self.assertEqual(len(self.crm.log), 3)

    def test_permission(self):
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp_id, 5, "r2")
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 1000)

    def test_final_stage(self):
        self.crm.advance(self.opp_id, "lost", "r1")
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp_id, 5, "m1")
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 1000)

    def test_rep_limited_to_ten(self):
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp_id, 11, "r1")
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 1000)
        self.crm.discount(self.opp_id, 10, "r1")
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 900)

    def test_manager_may_go_to_thirty(self):
        self.crm.discount(self.opp_id, 30, "m1")
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 700)

    def test_cumulative_floor_enforced(self):
        self.crm.discount(self.opp_id, 30, "m1")
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp_id, 1, "m1")
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 700)

    def test_cumulative_floor_allows_exact_boundary(self):
        self.crm.discount(self.opp_id, 15, "m1")
        self.crm.discount(self.opp_id, 15, "m1")
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 722)

    def test_amount_uses_integer_division(self):
        opp_id = new_opp(self.crm, amount=999, email="floor@corp.com")
        self.crm.discount(opp_id, 10, "m1")
        self.assertEqual(self.crm.opps[opp_id]["amount"], 899)

    def test_original_amount_is_untouched(self):
        self.crm.discount(self.opp_id, 10, "m1")
        self.assertEqual(self.crm.opps[self.opp_id]["original_amount"], 1000)

    def test_log_entry(self):
        self.crm.discount(self.opp_id, 5, "r1")
        self.assertEqual(self.crm.log[-1], ("discount", self.opp_id, "r1"))


class TransferTests(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        self.opp_id = new_opp(self.crm)

    def test_unknown_opp(self):
        with self.assertRaises(ValueError):
            self.crm.transfer("O99", "r2", "m1")

    def test_actor_must_be_manager(self):
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.opp_id, "r2", "r1")
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.opp_id, "nobody", "r1")
        self.assertEqual(self.crm.opps[self.opp_id]["owner"], "r1")

    def test_new_owner_must_be_known_rep(self):
        for bad in ("m1", "ghost", "", None):
            with self.assertRaises(ValueError, msg=repr(bad)):
                self.crm.transfer(self.opp_id, bad, "m1")

    def test_final_opportunity_cannot_transfer(self):
        self.crm.advance(self.opp_id, "lost", "r1")
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp_id, "r2", "m1")
        self.assertEqual(self.crm.opps[self.opp_id]["owner"], "r1")

    def test_same_owner_rejected(self):
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp_id, "r1", "m1")

    def test_new_owner_at_capacity_rejected(self):
        crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 5},
                {"id": "r2", "role": "rep", "capacity": 1},
                {"id": "m1", "role": "manager", "capacity": 5},
            ]
        )
        opp_id = new_opp(crm)
        crm.add_lead("fill@corp.com", "F", "web", "r1")
        crm.add_lead("fill2@corp.com", "F", "web", "r1")
        # r1 load 2, r2 load 0 -> next lead goes to r2, filling it.
        crm.add_lead("fill3@corp.com", "F", "web", "r1")
        self.assertEqual(crm._load("r2"), 1)
        with self.assertRaises(ValueError):
            crm.transfer(opp_id, "r2", "m1")
        self.assertEqual(crm.opps[opp_id]["owner"], "r1")

    def test_successful_transfer(self):
        self.crm.transfer(self.opp_id, "r2", "m1")
        self.assertEqual(self.crm.opps[self.opp_id]["owner"], "r2")
        self.assertEqual(self.crm.log[-1], ("transfer", self.opp_id, "m1"))
        self.assertEqual(self.crm._load("r1"), 0)
        self.assertEqual(self.crm._load("r2"), 1)

    def test_previous_owner_slot_is_freed(self):
        self.crm.transfer(self.opp_id, "r2", "m1")
        lead_id = self.crm.add_lead("next@corp.com", "N", "web", "m1")
        self.assertEqual(self.crm.leads[lead_id]["owner"], "r1")


class ForecastTests(unittest.TestCase):
    def test_empty(self):
        crm = make_crm()
        self.assertEqual(crm.forecast(), {"open": 0, "weighted": 0, "won": 0})

    def test_weighted_and_won(self):
        crm = make_crm()
        new_opp(crm, amount=1000, email="a@corp.com")
        proposal = new_opp(crm, amount=1000, email="b@corp.com")
        crm.advance(proposal, "proposal", "m1")
        negotiation = new_opp(crm, amount=999, email="c@corp.com")
        crm.advance(negotiation, "proposal", "m1")
        crm.advance(negotiation, "negotiation", "m1")
        won = new_opp(crm, amount=500, email="d@corp.com")
        crm.advance(won, "proposal", "m1")
        crm.advance(won, "negotiation", "m1")
        crm.advance(won, "won", "m1")
        lost = new_opp(crm, amount=7000, email="e@corp.com")
        crm.advance(lost, "lost", "m1")

        result = crm.forecast()
        self.assertEqual(result["open"], 3)
        self.assertEqual(result["weighted"], 100 + 300 + 999 * 60 // 100)
        self.assertEqual(result["won"], 500)
        self.assertNotIn("forecast", [entry[0] for entry in crm.log])

    def test_discount_affects_weighted_amount(self):
        crm = make_crm()
        opp_id = new_opp(crm, amount=1000)
        crm.discount(opp_id, 10, "r1")
        self.assertEqual(crm.forecast()["weighted"], 90)


if __name__ == "__main__":
    unittest.main()
