import unittest

from crm import CRM


def make_reps(r1_cap=50, r2_cap=50):
    return [
        {"id": "r1", "role": "rep", "capacity": r1_cap},
        {"id": "r2", "role": "rep", "capacity": r2_cap},
        {"id": "m1", "role": "manager", "capacity": 5},
    ]


class CRMGapTests(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(make_reps())
        self._seq = 0

    def email(self):
        self._seq += 1
        return "gap%d@corp.com" % self._seq

    def make_lead(self, source="referral"):
        return self.crm.add_lead(self.email(), "Name", source, "r1")

    def make_opp(self, amount=1000):
        lid = self.make_lead()
        self.crm.qualify(lid, "r1")
        return self.crm.convert(lid, amount, "r1")

    def test_manager_can_qualify_and_convert_rep_lead(self):
        lid = self.make_lead()
        self.crm.qualify(lid, "m1")
        opp = self.crm.convert(lid, 750, "m1")
        self.assertEqual(self.crm.opps[opp]["owner"], "r1")
        self.assertEqual(self.crm.log, [
            ("add_lead", lid, "r1"),
            ("qualify", lid, "m1"),
            ("convert", opp, "m1"),
        ])

    def test_discount_final_stage_check_precedes_rep_limit(self):
        opp = self.make_opp()
        for stage in ("proposal", "negotiation", "won"):
            self.crm.advance(opp, stage, "r1")
        with self.assertRaises(ValueError):
            self.crm.discount(opp, 20, "r1")
        self.assertEqual(self.crm.opps[opp]["amount"], 1000)

    def test_advance_skip_is_value_error_even_over_50k_for_rep(self):
        opp = self.make_opp(60000)
        with self.assertRaises(ValueError):
            self.crm.advance(opp, "negotiation", "r1")
        self.crm.advance(opp, "proposal", "r1")
        with self.assertRaises(PermissionError):
            self.crm.advance(opp, "negotiation", "r1")
        self.assertEqual(self.crm.opps[opp]["stage"], "proposal")

    def test_forecast_uses_discounted_amount(self):
        opp = self.make_opp(1000)
        self.crm.advance(opp, "proposal", "r1")
        self.crm.discount(opp, 10, "r1")
        self.assertEqual(self.crm.forecast(), {"open": 1, "weighted": 270, "won": 0})

    def test_unhashable_arguments_raise_value_error(self):
        with self.assertRaises(ValueError):
            self.crm.add_lead("a@corp.com", "A", ["web"], "r1")
        with self.assertRaises(ValueError):
            self.crm.qualify([], "r1")
        with self.assertRaises(ValueError):
            self.crm.convert([], 10, "r1")
        with self.assertRaises(ValueError):
            self.crm.advance([], "proposal", "r1")
        with self.assertRaises(ValueError):
            self.crm.discount([], 5, "m1")
        with self.assertRaises(ValueError):
            self.crm.transfer([], "r2", "m1")
        with self.assertRaises(PermissionError):
            self.crm.qualify([], [])

    def test_convert_frees_no_queue_slot_but_final_stage_does(self):
        crm = CRM(make_reps(1, 1))
        a = crm.add_lead("a@corp.com", "A", "referral", "r1")
        b = crm.add_lead("b@corp.com", "B", "referral", "r1")
        c = crm.add_lead("c@corp.com", "C", "referral", "r1")
        self.assertEqual(crm.leads[a]["owner"], "r1")
        self.assertEqual(crm.leads[b]["owner"], "r2")
        self.assertIsNone(crm.leads[c]["owner"])

        crm.qualify(a, "r1")
        opp = crm.convert(a, 1000, "r1")
        self.assertIsNone(crm.leads[c]["owner"])
        self.assertEqual(crm.leads[b]["owner"], "r2")

        crm.advance(opp, "lost", "r1")
        self.assertEqual(crm.leads[c]["owner"], "r1")
        self.assertEqual(crm.log[-1], ("assign", c, "system"))


if __name__ == "__main__":
    unittest.main()
