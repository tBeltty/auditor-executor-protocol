import unittest

from crm import CRM, DuplicateLeadError


def sample_crm():
    return CRM([
        {"id": "r1", "role": "rep", "capacity": 1},
        {"id": "r2", "role": "rep", "capacity": 2},
        {"id": "m1", "role": "manager", "capacity": 5},
    ])


class TestActor(unittest.TestCase):
    def test_unknown_actor_raises_first(self):
        crm = sample_crm()
        with self.assertRaises(PermissionError):
            crm.add_lead("a@b.co", "N", "web", "ghost")
        with self.assertRaises(PermissionError):
            crm.qualify("L1", "ghost")
        with self.assertRaises(PermissionError):
            crm.convert("L1", 100, "ghost")
        self.assertEqual(crm.leads, {})
        self.assertEqual(crm.log, [])

    def test_failed_call_does_not_consume_id_or_log(self):
        crm = sample_crm()
        with self.assertRaises(ValueError):
            crm.add_lead("bad-email", "N", "web", "m1")
        lid = crm.add_lead("a@b.co", "N", "web", "m1")
        self.assertEqual(lid, "L1")  # failed call did not advance the counter
        self.assertEqual(crm.log, [("add_lead", "L1", "m1")])


class TestAddLead(unittest.TestCase):
    def test_normalization_and_score(self):
        crm = sample_crm()
        lid = crm.add_lead("  Alice@Example.COM ", " Alice ", "web", "m1")
        lead = crm.leads[lid]
        self.assertEqual(lead["email"], "alice@example.com")
        self.assertEqual(lead["name"], "Alice")
        self.assertEqual(lead["score"], 25)  # web 10 + 15 non-free domain
        lead2 = crm.leads[crm.add_lead("bob@gmail.com", "B", "referral", "m1")]
        self.assertEqual(lead2["score"], 30)  # gmail: no domain bonus
        lead3 = crm.leads[crm.add_lead("c@x.io", "C", "event", "m1")]
        self.assertEqual(lead3["score"], 35)  # event 20 + 15

    def test_email_validation(self):
        crm = sample_crm()
        for bad in [None, 42, "noat", "a@b@c.com", "@b.com", "a@.com", "a@com.", "a@com"]:
            with self.assertRaises(ValueError, msg=repr(bad)):
                crm.add_lead(bad, "N", "web", "m1")

    def test_name_and_source_validation(self):
        crm = sample_crm()
        with self.assertRaises(ValueError):
            crm.add_lead("a@b.co", "   ", "web", "m1")
        with self.assertRaises(ValueError):
            crm.add_lead("a@b.co", 7, "web", "m1")
        with self.assertRaises(ValueError):
            crm.add_lead("a@b.co", "N", "twitter", "m1")

    def test_duplicate_raises_with_existing_id(self):
        crm = sample_crm()
        first = crm.add_lead("A@B.com", "N", "web", "m1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            crm.add_lead(" a@b.com ", "N2", "web", "m1")
        self.assertEqual(ctx.exception.existing_id, first)
        self.assertEqual(len(crm.leads), 1)


class TestRoutingAndQueue(unittest.TestCase):
    def test_lowest_load_then_capacity(self):
        crm = sample_crm()  # r1 cap 1, r2 cap 2
        l1 = crm.add_lead("a@b.co", "A", "web", "m1")
        l2 = crm.add_lead("c@d.co", "C", "web", "m1")
        l3 = crm.add_lead("e@f.co", "E", "web", "m1")
        self.assertEqual(crm.leads[l1]["owner"], "r1")  # both load 0, tie -> r1
        self.assertEqual(crm.leads[l2]["owner"], "r2")  # r1 full
        self.assertEqual(crm.leads[l3]["owner"], "r2")  # r2 has capacity 2
        l4 = crm.add_lead("g@h.co", "G", "web", "m1")
        self.assertIsNone(crm.leads[l4]["owner"])  # everyone full -> queue

    def test_waiting_lead_assigned_on_win(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1}])
        l1 = crm.add_lead("a@b.co", "A", "referral", "r1")
        l2 = crm.add_lead("c@d.co", "C", "web", "r1")
        self.assertIsNone(crm.leads[l2]["owner"])
        crm.qualify(l1, "r1")
        oid = crm.convert(l1, 100, "r1")
        crm.advance(oid, "proposal", "r1")
        crm.advance(oid, "negotiation", "r1")
        crm.advance(oid, "won", "r1")
        self.assertEqual(crm.leads[l2]["owner"], "r1")
        self.assertIn(("assign", l2, "system"), crm.log)


class TestQualifyConvert(unittest.TestCase):
    def test_qualify_flow_and_permissions(self):
        crm = sample_crm()
        lid = crm.add_lead("a@b.co", "A", "web", "m1")  # score 25, owner r1
        with self.assertRaises(ValueError):
            crm.qualify(lid, "r1")  # score < 30
        lid2 = crm.add_lead("c@d.co", "C", "referral", "m1")  # score 45, owner r2
        with self.assertRaises(PermissionError):
            crm.qualify(lid2, "r1")  # not owner, not manager
        crm.qualify(lid2, "m1")  # manager can act on anyone's lead
        self.assertEqual(crm.leads[lid2]["status"], "qualified")
        with self.assertRaises(ValueError):
            crm.qualify(lid2, "m1")  # already qualified
        with self.assertRaises(ValueError):
            crm.qualify("L99", "m1")

    def test_convert_validation_order(self):
        crm = sample_crm()
        lid = crm.add_lead("a@b.co", "A", "referral", "m1")
        with self.assertRaises(ValueError):
            crm.convert(lid, 100, "r1")  # not qualified yet... owner is r1 though
        # amount checks run before permission check:
        crm.qualify(lid, "r1")
        with self.assertRaises(ValueError):
            crm.convert(lid, True, "r1")
        with self.assertRaises(ValueError):
            crm.convert(lid, 0, "r1")
        with self.assertRaises(ValueError):
            crm.convert(lid, 10.5, "r1")
        with self.assertRaises(PermissionError):
            crm.convert(lid, 100, "r2")
        oid = crm.convert(lid, 500, "r1")
        self.assertEqual(oid, "O1")
        opp = crm.opps[oid]
        self.assertEqual(
            opp,
            {"id": "O1", "lead_id": lid, "owner": "r1", "amount": 500,
             "original_amount": 500, "stage": "prospect"},
        )
        self.assertEqual(crm.leads[lid]["status"], "converted")
        self.assertEqual(crm.log[-1], ("convert", "O1", "r1"))

    def test_convert_waiting_lead_fails(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1},
                   {"id": "m1", "role": "manager", "capacity": 5}])
        l1 = crm.add_lead("a@b.co", "A", "referral", "r1")
        l2 = crm.add_lead("c@d.co", "C", "referral", "r1")
        crm.qualify(l2, "m1")  # manager can qualify an unowned lead
        with self.assertRaises(ValueError):
            crm.convert(l2, 10, "m1")  # no owner


class TestAdvanceDiscount(unittest.TestCase):
    def _opp(self, amount=1000):
        crm = sample_crm()
        lid = crm.add_lead("a@b.co", "A", "referral", "m1")
        crm.qualify(lid, "r1")
        oid = crm.convert(lid, amount, "r1")
        return crm, oid

    def test_stage_order_and_finality(self):
        crm, oid = self._opp()
        with self.assertRaises(ValueError):
            crm.advance(oid, "won", "r1")  # not immediate next
        with self.assertRaises(ValueError):
            crm.advance(oid, "brief", "r1")  # unknown stage
        crm.advance(oid, "proposal", "r1")
        crm.advance(oid, "negotiation", "r1")
        crm.advance(oid, "won", "r1")
        self.assertEqual(crm.opps[oid]["stage"], "won")
        with self.assertRaises(ValueError):
            crm.advance(oid, "lost", "m1")  # final

    def test_lost_from_any_non_final_stage(self):
        crm, oid = self._opp()
        crm.advance(oid, "lost", "r1")
        self.assertEqual(crm.opps[oid]["stage"], "lost")

    def test_large_negotiation_requires_manager(self):
        crm, oid = self._opp(amount=60000)
        crm.advance(oid, "proposal", "r1")
        with self.assertRaises(PermissionError):
            crm.advance(oid, "negotiation", "r1")
        crm.advance(oid, "negotiation", "m1")
        self.assertEqual(crm.opps[oid]["stage"], "negotiation")

    def test_discount_rules(self):
        crm, oid = self._opp(amount=10000)
        with self.assertRaises(ValueError):
            crm.discount(oid, 0, "r1")
        with self.assertRaises(ValueError):
            crm.discount(oid, 31, "r1")
        with self.assertRaises(ValueError):
            crm.discount(oid, True, "r1")
        with self.assertRaises(PermissionError):
            crm.discount(oid, 20, "r1")  # rep max 10
        crm.discount(oid, 10, "r1")  # 10000 -> 9000
        self.assertEqual(crm.opps[oid]["amount"], 9000)
        # next 10 is fine (8100 >= 70% of 10000), but a 30 cumulative floor blocks 30 now
        crm.discount(oid, 10, "m1")
        self.assertEqual(crm.opps[oid]["amount"], 8100)
        with self.assertRaises(ValueError):
            crm.discount(oid, 30, "m1")  # 5670 would be below 70% of original 10000
        # manager may discount 30 up front: floor is measured from original
        crm2, oid2 = self._opp(amount=10000)
        crm2.discount(oid2, 30, "m1")  # -> 7000, exactly 70%: allowed
        self.assertEqual(crm2.opps[oid2]["amount"], 7000)

    def test_discount_on_final_stage_rejected(self):
        crm, oid = self._opp()
        crm.advance(oid, "lost", "r1")
        with self.assertRaises(ValueError):
            crm.discount(oid, 5, "m1")


class TestTransferAndForecast(unittest.TestCase):
    def _two_opps(self):
        crm = sample_crm()
        lids = []
        for i, email in enumerate(["a@b.co", "c@d.co"]):
            lids.append(crm.add_lead(email, "N%d" % i, "referral", "m1"))
        opps = []
        for lid in lids:  # L1 -> r1, L2 -> r2
            crm.qualify(lid, "m1")
            opps.append(crm.convert(lid, 1000, "m1"))
        return crm, opps

    def test_transfer_checks(self):
        crm, (o1, o2) = self._two_opps()
        with self.assertRaises(PermissionError):
            crm.transfer(o1, "r2", "r1")  # only managers
        with self.assertRaises(ValueError):
            crm.transfer(o1, "m1", "m1")  # target must be a rep
        with self.assertRaises(ValueError):
            crm.transfer(o1, "ghost", "m1")  # unknown user
        with self.assertRaises(ValueError):
            crm.transfer(o1, "r1", "m1")  # same owner
        with self.assertRaises(ValueError):
            crm.transfer("O99", "r2", "m1")  # no such opp
        # r2 has room (load 1 of capacity 2); r1 is full (load 1 of capacity 1)
        with self.assertRaises(ValueError):
            crm.transfer(o2, "r1", "m1")
        crm.transfer(o1, "r2", "m1")
        self.assertEqual(crm.opps[o1]["owner"], "r2")
        self.assertEqual(crm.log[-1], ("transfer", o1, "m1"))
        # r1 is free now and r2 is full: o2 can move back to r1
        crm.transfer(o2, "r1", "m1")
        self.assertEqual(crm.opps[o2]["owner"], "r1")

    def test_transfer_final_stage_rejected(self):
        crm, (o1, _) = self._two_opps()
        crm.advance(o1, "lost", "r1")
        with self.assertRaises(ValueError):
            crm.transfer(o1, "r2", "m1")

    def test_forecast(self):
        crm, (o1, o2) = self._two_opps()  # both 1000 at prospect
        self.assertEqual(crm.forecast(), {"open": 2, "weighted": 200, "won": 0})
        crm.advance(o1, "proposal", "r1")
        crm.advance(o1, "negotiation", "r1")  # 1000 <= 50000, rep OK
        self.assertEqual(crm.forecast(), {"open": 2, "weighted": 600 + 100, "won": 0})
        crm.advance(o2, "lost", "r2")
        crm.advance(o1, "won", "r1")
        self.assertEqual(crm.forecast(), {"open": 0, "weighted": 0, "won": 1000})
        self.assertEqual(crm.log[-1], ("advance", o1, "r1"))  # forecast logs nothing


if __name__ == "__main__":
    unittest.main()
