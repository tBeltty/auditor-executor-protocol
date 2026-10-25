import unittest

from crm import CRM, DuplicateLeadError


def make(**overrides):
    reps = [
        {"id": "M1", "role": "manager", "capacity": 99},
        {"id": "R1", "role": "rep", "capacity": 2},
        {"id": "R2", "role": "rep", "capacity": 1},
    ]
    for rid, cap in overrides.items():
        for rep in reps:
            if rep["id"] == rid:
                rep["capacity"] = cap
    return CRM(reps)


class TestAddLead(unittest.TestCase):
    def test_unknown_actor_denied_first(self):
        c = make()
        with self.assertRaises(PermissionError):
            c.add_lead("not-an-email", "", "bogus", "nobody")
        self.assertEqual(c.log, [])
        self.assertEqual(c.leads, {})

    def test_email_validation(self):
        c = make()
        bad = ["", "a@b", "a@b.", "a@.b", "a@b@c", "@b.co", 12, None]
        for email in bad:
            with self.assertRaises(ValueError, msg=repr(email)):
                c.add_lead(email, "N", "web", "M1")
        self.assertEqual(c.log, [])

    def test_name_and_source_validation(self):
        c = make()
        with self.assertRaises(ValueError):
            c.add_lead("a@b.co", "   ", "web", "M1")
        with self.assertRaises(ValueError):
            c.add_lead("a@b.co", 5, "web", "M1")
        with self.assertRaises(ValueError):
            c.add_lead("a@b.co", "N", "phone", "M1")
        self.assertEqual(c.log, [])

    def test_normalization_and_lead_fields(self):
        c = make()
        lid = c.add_lead("  Ann@Example.COM ", "  Ann  ", "referral", "M1")
        self.assertEqual(lid, "L1")
        lead = c.leads[lid]
        self.assertEqual(lead["email"], "ann@example.com")
        self.assertEqual(lead["name"], "Ann")
        self.assertEqual(lead["score"], 45)  # referral 30 + 15 corporate domain
        self.assertEqual(lead["status"], "new")
        self.assertEqual(c.log, [("add_lead", "L1", "M1")])

    def test_scores(self):
        c = make()
        self.assertEqual(c.leads[c.add_lead("a@gmail.com", "a", "web", "R1")]["score"], 10)
        self.assertEqual(c.leads[c.add_lead("b@corp.io", "b", "web", "R1")]["score"], 25)
        self.assertEqual(c.leads[c.add_lead("c@corp.io", "c", "event", "M1")]["score"], 35)

    def test_duplicate(self):
        c = make()
        lid = c.add_lead("a@corp.io", "a", "web", "R1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            c.add_lead(" A@CORP.IO ", "other", "event", "R1")
        self.assertEqual(ctx.exception.existing_id, lid)
        self.assertEqual(len(c.log), 1)
        self.assertEqual(len(c.leads), 1)

    def test_capacity_queue_and_lowest_load(self):
        c = make(R1=1)
        l1 = c.add_lead("1@corp.io", "1", "web", "M1")
        l2 = c.add_lead("2@corp.io", "2", "web", "M1")
        l3 = c.add_lead("3@corp.io", "3", "web", "M1")
        # R1 load 0 < R2 load 0 -> tie broken by smallest id: R1
        self.assertEqual(c.leads[l1]["owner"], "R1")
        self.assertEqual(c.leads[l2]["owner"], "R2")
        # both full -> queued
        self.assertIsNone(c.leads[l3]["owner"])
        self.assertEqual(c.waiting, [l3])

    def test_manager_never_owns(self):
        c = CRM([{"id": "M1", "role": "manager", "capacity": 5}])
        lid = c.add_lead("a@corp.io", "a", "web", "M1")
        self.assertIsNone(c.leads[lid]["owner"])
        self.assertEqual(c.waiting, [lid])


class TestQualifyConvert(unittest.TestCase):
    def test_qualify_rules(self):
        c = make()
        web = c.add_lead("w@corp.io", "w", "web", "R1")  # score 25
        with self.assertRaises(ValueError):
            c.qualify(web, "R1")  # score below 30
        ref = c.add_lead("r@corp.io", "r", "referral", "R1")
        with self.assertRaises(PermissionError):
            c.qualify(ref, "R1")  # R2 owns it
        with self.assertRaises(ValueError):
            c.qualify("L99", "R1")
        c.qualify(ref, "M1")
        self.assertEqual(c.leads[ref]["status"], "qualified")
        with self.assertRaises(ValueError):
            c.qualify(ref, "M1")  # no longer new
        self.assertEqual(c.log[-1], ("qualify", ref, "M1"))

    def test_manager_can_qualify(self):
        c = make()
        ref = c.add_lead("r@corp.io", "r", "referral", "R1")
        c.qualify(ref, "M1")
        self.assertEqual(c.leads[ref]["status"], "qualified")

    def test_convert_rules_and_effect(self):
        c = make()
        lead = c.add_lead("r@corp.io", "r", "referral", "R1")
        with self.assertRaises(ValueError):
            c.convert(lead, 100, "R1")  # not qualified yet
        c.qualify(lead, "R1")
        for bad in (0, -5, True, 1.5, "10"):
            with self.assertRaises(ValueError, msg=repr(bad)):
                c.convert(lead, bad, "R1")
        with self.assertRaises(PermissionError):
            c.convert(lead, 100, "R2")
        opp = c.convert(lead, 1000, "R1")
        self.assertEqual(opp, "O1")
        self.assertEqual(c.opps[opp], {
            "id": "O1", "lead_id": lead, "owner": "R1", "amount": 1000,
            "original_amount": 1000, "stage": "prospect",
        })
        self.assertEqual(c.leads[lead]["status"], "converted")
        self.assertEqual(c.log[-1], ("convert", "O1", "R1"))
        self.assertEqual(c.forecast(), {"open": 1, "weighted": 100, "won": 0})

    def test_convert_requires_owner(self):
        c = make(R1=0, R2=0)
        lead = c.add_lead("r@corp.io", "r", "referral", "M1")
        c.qualify(lead, "M1")
        with self.assertRaises(ValueError):
            c.convert(lead, 10, "M1")


class TestAdvance(unittest.TestCase):
    def setup_opp(self, amount=1000):
        c = make()
        lead = c.add_lead("r@corp.io", "r", "referral", "R1")
        c.qualify(lead, "R1")
        opp = c.convert(lead, amount, "R1")
        return c, lead, opp

    def test_stage_order(self):
        c, _, opp = self.setup_opp()
        with self.assertRaises(ValueError):
            c.advance(opp, "negotiation", "R1")  # skip proposal
        with self.assertRaises(ValueError):
            c.advance(opp, "won", "R1")
        with self.assertRaises(ValueError):
            c.advance(opp, "bogus", "R1")
        with self.assertRaises(ValueError):
            c.advance("O99", "proposal", "R1")
        with self.assertRaises(PermissionError):
            c.advance(opp, "proposal", "R2")
        c.advance(opp, "proposal", "R1")
        c.advance(opp, "negotiation", "M1")  # manager can act on any opp
        self.assertEqual(c.opps[opp]["stage"], "negotiation")

    def test_final_stage_is_final(self):
        c, _, opp = self.setup_opp()
        c.advance(opp, "lost", "R1")
        with self.assertRaises(ValueError):
            c.advance(opp, "proposal", "R1")
        self.assertEqual(c.forecast(), {"open": 0, "weighted": 0, "won": 0})

    def test_negotiation_threshold_requires_manager(self):
        c, _, opp = self.setup_opp(50001)
        c.advance(opp, "proposal", "R1")
        with self.assertRaises(PermissionError):
            c.advance(opp, "negotiation", "R1")
        c.advance(opp, "negotiation", "M1")
        self.assertEqual(c.opps[opp]["stage"], "negotiation")

    def test_threshold_not_triggered_at_exact_50000(self):
        c, _, opp = self.setup_opp(50000)
        c.advance(opp, "proposal", "R1")
        c.advance(opp, "negotiation", "R1")
        self.assertEqual(c.opps[opp]["stage"], "negotiation")

    def test_closing_frees_slot_and_assigns_queue(self):
        c = make(R1=1, R2=0)
        lead = c.add_lead("r@corp.io", "r", "referral", "R1")
        waiting = c.add_lead("x@corp.io", "x", "referral", "R1")  # queued
        self.assertIsNone(c.leads[waiting]["owner"])
        c.qualify(lead, "R1")
        opp = c.convert(lead, 500, "R1")
        c.advance(opp, "proposal", "R1")
        c.advance(opp, "negotiation", "R1")
        c.advance(opp, "won", "R1")
        self.assertEqual(c.leads[waiting]["owner"], "R1")
        self.assertEqual(c.waiting, [])
        self.assertIn(("assign", waiting, "system"), c.log)

    def test_forecast(self):
        c, _, o1 = self.setup_opp(1000)
        c.advance(o1, "proposal", "R1")
        lead = c.add_lead("s@corp.io", "s", "referral", "R1")
        c.qualify(lead, "M1")
        o2 = c.convert(lead, 3000, "M1")
        self.assertEqual(c.forecast(), {"open": 2, "weighted": 600, "won": 0})
        c.advance(o2, "proposal", "M1")
        c.advance(o2, "negotiation", "M1")
        c.advance(o2, "won", "M1")
        self.assertEqual(c.forecast(), {"open": 1, "weighted": 300, "won": 3000})


class TestDiscount(unittest.TestCase):
    def setup_opp(self):
        c = make()
        lead = c.add_lead("r@corp.io", "r", "referral", "R1")
        c.qualify(lead, "R1")
        return c, c.convert(lead, 1000, "R1")

    def test_validation_and_pct(self):
        c, opp = self.setup_opp()
        for bad in (0, 31, -1, True, 5.0, "5"):
            with self.assertRaises(ValueError, msg=repr(bad)):
                c.discount(opp, bad, "R1")
        with self.assertRaises(PermissionError):
            c.discount(opp, 5, "R2")
        with self.assertRaises(PermissionError):
            c.discount(opp, 11, "R1")  # rep capped at 10
        c.discount(opp, 10, "R1")
        self.assertEqual(c.opps[opp]["amount"], 900)

    def test_cumulative_cap(self):
        c, opp = self.setup_opp()
        c.discount(opp, 10, "M1")
        c.discount(opp, 10, "M1")
        self.assertEqual(c.opps[opp]["amount"], 810)
        with self.assertRaises(ValueError):
            c.discount(opp, 15, "M1")  # 810*85//100 = 688 < 700
        c.discount(opp, 10, "M1")
        self.assertEqual(c.opps[opp]["amount"], 729)
        with self.assertRaises(ValueError):
            c.discount(opp, 4, "M1")  # 729*96//100 = 699 < 700
        c.discount(opp, 1, "M1")  # 729*99//100 = 721 stays above the floor
        self.assertEqual(c.opps[opp]["amount"], 721)

    def test_final_stage_rejected(self):
        c, opp = self.setup_opp()
        c.advance(opp, "lost", "R1")
        with self.assertRaises(ValueError):
            c.discount(opp, 5, "M1")


class TestTransfer(unittest.TestCase):
    def setup_opp(self):
        c = make(R2=1)
        lead = c.add_lead("r@corp.io", "r", "referral", "R1")
        c.qualify(lead, "R1")
        return c, c.convert(lead, 1000, "R1")

    def test_transfer_rules(self):
        c, opp = self.setup_opp()
        with self.assertRaises(PermissionError):
            c.transfer(opp, "R2", "R1")  # not a manager
        with self.assertRaises(ValueError):
            c.transfer("O99", "R2", "M1")
        with self.assertRaises(ValueError):
            c.transfer(opp, "M1", "M1")  # not a rep
        with self.assertRaises(ValueError):
            c.transfer(opp, "R1", "M1")  # same owner
        with self.assertRaises(ValueError):
            c.transfer(opp, "nobody", "M1")

    def test_transfer_moves_owner(self):
        c, opp = self.setup_opp()
        c.transfer(opp, "R2", "M1")
        self.assertEqual(c.opps[opp]["owner"], "R2")
        self.assertEqual(c.log[-1], ("transfer", opp, "M1"))
        # the freed slot in R1 is usable again by new leads
        lead = c.add_lead("z@corp.io", "z", "referral", "R1")
        self.assertEqual(c.leads[lead]["owner"], "R1")

    def test_transfer_rejects_full_rep(self):
        c = make(R2=1)
        lead = c.add_lead("r@corp.io", "r", "referral", "R1")
        c.qualify(lead, "R1")
        opp = c.convert(lead, 1000, "R1")
        c.add_lead("filler@corp.io", "f", "referral", "R1")  # load: R1 1, R2 0 -> R2
        self.assertEqual(c.leads["L2"]["owner"], "R2")  # R2 now at capacity
        with self.assertRaises(ValueError):
            c.transfer(opp, "R2", "M1")


class TestAtomicity(unittest.TestCase):
    def test_failed_calls_do_not_mutate(self):
        c = make()
        lead = c.add_lead("r@corp.io", "r", "referral", "R1")
        c.qualify(lead, "R1")
        opp = c.convert(lead, 100, "R1")
        before_log = list(c.log)
        before_opp = dict(c.opps[opp])
        with self.assertRaises(ValueError):
            c.discount(opp, 50, "M1")
        with self.assertRaises(ValueError):
            c.advance(opp, "won", "R1")
        self.assertEqual(c.log, before_log)
        self.assertEqual(c.opps[opp], before_opp)
        self.assertEqual(c.forecast(), {"open": 1, "weighted": 10, "won": 0})


if __name__ == "__main__":
    unittest.main()
