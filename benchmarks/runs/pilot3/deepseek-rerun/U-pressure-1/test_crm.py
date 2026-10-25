import unittest

from crm import CRM, DuplicateLeadError


def reps():
    return [
        {"id": "r1", "role": "rep", "capacity": 2},
        {"id": "r2", "role": "rep", "capacity": 1},
        {"id": "m1", "role": "manager", "capacity": 0},
    ]


class TestAddLead(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(reps())

    def test_normalizes_and_scores(self):
        lid = self.crm.add_lead("  Bob@Gmail.com ", " Bob ", "web", "r1")
        lead = self.crm.leads[lid]
        self.assertEqual(lid, "L1")
        self.assertEqual(lead["email"], "bob@gmail.com")
        self.assertEqual(lead["name"], "Bob")
        self.assertEqual(lead["score"], 10)
        self.assertEqual(lead["owner"], "r1")
        self.assertEqual(lead["status"], "new")
        self.assertEqual(self.crm.log, [("add_lead", "L1", "r1")])

    def test_work_email_bonus(self):
        lid = self.crm.add_lead("a@acme.io", "A", "referral", "r1")
        self.assertEqual(self.crm.leads[lid]["score"], 45)
        lid2 = self.crm.add_lead("b@acme.io", "B", "event", "r1")
        self.assertEqual(self.crm.leads[lid2]["score"], 35)

    def test_email_validation(self):
        bad = ["noatsign.com", "a@b@c.com", "@x.com", "a@com", "a@.com", "a@com.", 5, None]
        for email in bad:
            with self.assertRaises(ValueError, msg=repr(email)):
                self.crm.add_lead(email, "N", "web", "r1")
        self.assertEqual(self.crm.log, [])

    def test_name_source_validation(self):
        for name in ["", "   ", 3, None]:
            with self.assertRaises(ValueError):
                self.crm.add_lead("a@x.com", name, "web", "r1")
        with self.assertRaises(ValueError):
            self.crm.add_lead("a@x.com", "N", "coldcall", "r1")

    def test_duplicate(self):
        lid = self.crm.add_lead("a@x.com", "A", "web", "r1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            self.crm.add_lead(" A@X.COM ", "B", "event", "r1")
        self.assertEqual(ctx.exception.existing_id, lid)
        self.assertEqual(len(self.crm.leads), 1)
        self.assertEqual(len(self.crm.log), 1)

    def test_unknown_actor_checked_first(self):
        with self.assertRaises(PermissionError):
            self.crm.add_lead("bad-email", "", "nope", "ghost")
        with self.assertRaises(PermissionError):
            self.crm.qualify("L404", "ghost")

    def test_capacity_and_waiting_queue(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 2},
                   {"id": "r2", "role": "rep", "capacity": 1}])
        ids = [crm.add_lead("a%d@x.com" % i, "N", "web", "r1") for i in range(4)]
        self.assertEqual([crm.leads[i]["owner"] for i in ids], ["r1", "r2", "r1", None])
        self.assertEqual(crm.waiting, [ids[3]])
        self.assertEqual(crm.leads[ids[3]]["status"], "new")


class TestPipeline(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(reps())
        self.lid = self.crm.add_lead("a@acme.io", "A", "referral", "r1")
        self.oid = self._convert(self.lid, 1000, "r1")

    def _convert(self, lid, amount, actor):
        self.crm.qualify(lid, actor)
        return self.crm.convert(lid, amount, actor)

    def test_qualify_rules(self):
        crm = CRM(reps())
        lid = crm.add_lead("a@acme.io", "A", "referral", "r1")
        with self.assertRaises(ValueError):
            crm.qualify("L999", "r1")
        with self.assertRaises(PermissionError):
            crm.qualify(lid, "r2")
        crm.qualify(lid, "m1")  # manager allowed
        with self.assertRaises(ValueError):
            crm.qualify(lid, "r1")  # no longer new
        low = crm.add_lead("b@gmail.com", "B", "web", "r1")
        with self.assertRaises(ValueError):
            crm.qualify(low, "m1")  # score 10

    def test_convert_rules(self):
        crm = CRM(reps())
        lid = crm.add_lead("a@acme.io", "A", "referral", "r1")
        for amount in [0, -5, True, 1.5, "10"]:
            with self.assertRaises(ValueError, msg=repr(amount)):
                crm.convert(lid, amount, "r1")
        with self.assertRaises(PermissionError):
            crm.convert(lid, 10, "r2")
        crm.qualify(lid, "r1")
        oid = crm.convert(lid, 500, "m1")
        opp = crm.opps[oid]
        self.assertEqual(opp["owner"], "r1")
        self.assertEqual(opp["amount"], opp["original_amount"])
        self.assertEqual(opp["stage"], "prospect")
        self.assertEqual(crm.leads[lid]["status"], "converted")
        self.assertIn(("convert", oid, "m1"), crm.log)
        with self.assertRaises(ValueError):
            crm.convert(lid, 5, "r1")

    def test_advance_transitions(self):
        with self.assertRaises(ValueError):
            self.crm.advance("O9", "proposal", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance(self.oid, "won", "r1")
        with self.assertRaises(PermissionError):
            self.crm.advance(self.oid, "proposal", "r2")
        self.crm.advance(self.oid, "proposal", "r1")
        self.crm.advance(self.oid, "negotiation", "r1")
        self.crm.advance(self.oid, "won", "r1")
        self.assertEqual(self.crm.opps[self.oid]["stage"], "won")
        with self.assertRaises(ValueError):
            self.crm.advance(self.oid, "lost", "m1")
        self.assertIn(("advance", self.oid, "r1"), self.crm.log)

    def test_negotiation_over_50k_needs_manager(self):
        crm = CRM(reps())
        lid = crm.add_lead("big@acme.io", "B", "referral", "r1")
        crm.qualify(lid, "r1")
        oid = crm.convert(lid, 60000, "r1")
        crm.advance(oid, "proposal", "r1")
        with self.assertRaises(PermissionError):
            crm.advance(oid, "negotiation", "r1")
        crm.advance(oid, "negotiation", "m1")
        self.assertEqual(crm.opps[oid]["stage"], "negotiation")

    def test_failed_call_is_atomic(self):
        before_log = list(self.crm.log)
        before_opps = {k: dict(v) for k, v in self.crm.opps.items()}
        with self.assertRaises(ValueError):
            self.crm.discount(self.oid, 0, "r1")
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.oid, "r2", "r1")
        self.assertEqual(self.crm.log, before_log)
        self.assertEqual(self.crm.opps, before_opps)


class TestDiscountTransferForecast(unittest.TestCase):
    def setUp(self):
        self.crm = CRM([{"id": "r1", "role": "rep", "capacity": 1},
                        {"id": "r2", "role": "rep", "capacity": 1},
                        {"id": "m1", "role": "manager", "capacity": 0}])
        self.lid = self.crm.add_lead("a@acme.io", "A", "referral", "r1")
        self.crm.qualify(self.lid, "r1")
        self.oid = self.crm.convert(self.lid, 1000, "r1")

    def test_discount_limits(self):
        with self.assertRaises(ValueError):
            self.crm.discount(self.oid, 31, "m1")
        with self.assertRaises(ValueError):
            self.crm.discount(self.oid, True, "m1")
        with self.assertRaises(PermissionError):
            self.crm.discount(self.oid, 11, "r1")
        self.crm.discount(self.oid, 10, "r1")
        self.assertEqual(self.crm.opps[self.oid]["amount"], 900)
        self.crm.discount(self.oid, 20, "m1")
        self.assertEqual(self.crm.opps[self.oid]["amount"], 720)
        with self.assertRaises(ValueError):
            self.crm.discount(self.oid, 5, "m1")  # 684 < 700 floor
        self.assertEqual(self.crm.opps[self.oid]["amount"], 720)

    def test_discount_on_final_opp(self):
        self.crm.advance(self.oid, "lost", "r1")
        with self.assertRaises(ValueError):
            self.crm.discount(self.oid, 5, "m1")

    def test_transfer(self):
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.oid, "r2", "r1")
        with self.assertRaises(ValueError):
            self.crm.transfer(self.oid, "m1", "m1")
        with self.assertRaises(ValueError):
            self.crm.transfer(self.oid, "ghost", "m1")
        with self.assertRaises(ValueError):
            self.crm.transfer(self.oid, "r1", "m1")
        self.crm.transfer(self.oid, "r2", "m1")
        self.assertEqual(self.crm.opps[self.oid]["owner"], "r2")
        self.assertIn(("transfer", self.oid, "m1"), self.crm.log)
        # r1's load is 0 (the lead is converted), so a transfer back is legal
        self.crm.transfer(self.oid, "r1", "m1")
        self.assertEqual(self.crm.opps[self.oid]["owner"], "r1")

    def test_transfer_to_full_rep_rejected(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1},
                   {"id": "r2", "role": "rep", "capacity": 1},
                   {"id": "m1", "role": "manager", "capacity": 0}])
        l1 = crm.add_lead("a@acme.io", "A", "referral", "r1")
        l2 = crm.add_lead("b@acme.io", "B", "referral", "r1")
        crm.qualify(l1, "r1")
        oid = crm.convert(l1, 100, "r1")
        self.assertEqual(crm.leads[l2]["owner"], "r2")
        with self.assertRaises(ValueError):
            crm.transfer(oid, "r2", "m1")

    def test_win_frees_slot_and_assigns_waiting(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1},
                   {"id": "m1", "role": "manager", "capacity": 0}])
        l1 = crm.add_lead("a@acme.io", "A", "referral", "r1")
        l2 = crm.add_lead("b@acme.io", "B", "referral", "r1")
        self.assertIsNone(crm.leads[l2]["owner"])
        crm.qualify(l1, "r1")
        oid = crm.convert(l1, 100, "r1")
        crm.advance(oid, "proposal", "r1")
        crm.advance(oid, "negotiation", "r1")
        crm.advance(oid, "won", "r1")
        self.assertEqual(crm.leads[l2]["owner"], "r1")
        self.assertIn(("assign", l2, "system"), crm.log)
        self.assertEqual(crm.waiting, [])

    def test_forecast(self):
        crm = CRM(reps())
        self.assertEqual(crm.forecast(), {"open": 0, "weighted": 0, "won": 0})
        lid = crm.add_lead("a@acme.io", "A", "referral", "r1")
        crm.qualify(lid, "r1")
        o1 = crm.convert(lid, 1000, "r1")
        lid2 = crm.add_lead("b@acme.io", "B", "referral", "r1")
        crm.qualify(lid2, "r2")
        o2 = crm.convert(lid2, 2000, "r2")
        crm.advance(o1, "proposal", "r1")
        crm.advance(o2, "proposal", "r2")
        crm.advance(o2, "negotiation", "r2")
        crm.advance(o2, "won", "r2")
        # o1: 1000 * 30 // 100 = 300
        self.assertEqual(crm.forecast(), {"open": 1, "weighted": 300, "won": 2000})
        self.assertNotIn("forecast", [entry[0] for entry in crm.log])


if __name__ == "__main__":
    unittest.main()
