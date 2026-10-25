import unittest

from crm import CRM

REPS = [
    {"id": "r1", "role": "rep", "capacity": 6},
    {"id": "r2", "role": "rep", "capacity": 6},
    {"id": "m1", "role": "manager", "capacity": 6},
]


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.crm = CRM([dict(rep) for rep in REPS])

    def make_opp(self, email, amount):
        lead = self.crm.add_lead(email, "N", "referral", "m1")
        self.crm.qualify(lead, "m1")
        return self.crm.convert(lead, amount, "m1")

    def test_qualify_moves_lead_and_logs(self):
        lead = self.crm.add_lead("a@corp.com", "A", "referral", "r1")
        self.crm.qualify(lead, "r1")
        self.assertEqual(self.crm.leads[lead]["status"], "qualified")
        self.assertEqual(self.crm.log[-1], ("qualify", lead, "r1"))

    def test_convert_creates_prospect(self):
        lead = self.crm.add_lead("a@corp.com", "A", "referral", "r1")
        self.crm.qualify(lead, "r1")
        opp_id = self.crm.convert(lead, 4000, "r1")
        self.assertEqual(opp_id, "O1")
        self.assertEqual(self.crm.opps[opp_id], {
            "id": "O1",
            "lead_id": lead,
            "owner": "r1",
            "amount": 4000,
            "original_amount": 4000,
            "stage": "prospect",
        })
        self.assertEqual(self.crm.leads[lead]["status"], "converted")
        self.assertEqual(self.crm.log[-1], ("convert", opp_id, "r1"))

    def test_advance_chain(self):
        opp = self.make_opp("a@corp.com", 4000)
        for stage in ("proposal", "negotiation", "won"):
            self.crm.advance(opp, stage, "m1")
            self.assertEqual(self.crm.opps[opp]["stage"], stage)
            self.assertEqual(self.crm.log[-1], ("advance", opp, "m1"))

    def test_lost_is_final(self):
        opp = self.make_opp("a@corp.com", 4000)
        self.crm.advance(opp, "lost", "m1")
        self.assertEqual(self.crm.opps[opp]["stage"], "lost")
        with self.assertRaises(ValueError):
            self.crm.advance(opp, "proposal", "m1")

    def test_forecast_weights_open_stages(self):
        prospect = self.make_opp("a@corp.com", 1000)
        proposal = self.make_opp("b@corp.com", 2000)
        self.crm.advance(proposal, "proposal", "m1")
        negotiation = self.make_opp("c@corp.com", 3000)
        self.crm.advance(negotiation, "proposal", "m1")
        self.crm.advance(negotiation, "negotiation", "m1")
        won = self.make_opp("d@corp.com", 4000)
        for stage in ("proposal", "negotiation", "won"):
            self.crm.advance(won, stage, "m1")
        lost = self.make_opp("e@corp.com", 5000)
        self.crm.advance(lost, "lost", "m1")
        self.assertEqual(self.crm.forecast(),
                         {"open": 3, "weighted": 100 + 600 + 1800, "won": 4000})

    def test_forecast_empty(self):
        self.assertEqual(self.crm.forecast(), {"open": 0, "weighted": 0, "won": 0})

    def test_discount_limits_for_manager(self):
        opp = self.make_opp("a@corp.com", 1000)
        self.crm.discount(opp, 30, "m1")
        self.assertEqual(self.crm.opps[opp]["amount"], 700)
        self.assertEqual(self.crm.opps[opp]["original_amount"], 1000)
        self.assertEqual(self.crm.log[-1], ("discount", opp, "m1"))

    def test_discount_ten_percent_for_owner(self):
        opp = self.make_opp("a@corp.com", 1000)
        self.crm.discount(opp, 10, self.crm.opps[opp]["owner"])
        self.assertEqual(self.crm.opps[opp]["amount"], 900)

    def test_transfer_moves_owner(self):
        opp = self.make_opp("a@corp.com", 1000)
        self.crm.transfer(opp, "r2", "m1")
        self.assertEqual(self.crm.opps[opp]["owner"], "r2")
        self.assertEqual(self.crm.log[-1], ("transfer", opp, "m1"))


if __name__ == "__main__":
    unittest.main()
