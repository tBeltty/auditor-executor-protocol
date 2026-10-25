import unittest

from crm import CRM, DuplicateLeadError


def big_crm():
    return CRM([
        {"id": "r1", "role": "rep", "capacity": 10},
        {"id": "r2", "role": "rep", "capacity": 10},
        {"id": "m1", "role": "manager", "capacity": 0},
    ])


def small_crm():
    return CRM([
        {"id": "r1", "role": "rep", "capacity": 2},
        {"id": "r2", "role": "rep", "capacity": 1},
        {"id": "m1", "role": "manager", "capacity": 0},
    ])


def seed_opp(crm, amount, stage="prospect"):
    email = "lead%d@example.com" % (len(crm.leads) + 1)
    lead_id = crm.add_lead(email, "Lead", "referral", "m1")
    crm.qualify(lead_id, "m1")
    opp_id = crm.convert(lead_id, amount, "m1")
    paths = {
        "prospect": [],
        "proposal": ["proposal"],
        "negotiation": ["proposal", "negotiation"],
        "won": ["proposal", "negotiation", "won"],
    }
    for next_stage in paths[stage]:
        crm.advance(opp_id, next_stage, "m1")
    return opp_id


class AddLeadTests(unittest.TestCase):
    def test_normalizes_and_scores(self):
        crm = big_crm()
        lead_id = crm.add_lead("  Ada@Example.COM ", "  Ada  ", "referral", "r1")
        self.assertEqual(lead_id, "L1")
        lead = crm.leads[lead_id]
        self.assertEqual(lead["email"], "ada@example.com")
        self.assertEqual(lead["name"], "Ada")
        self.assertEqual(lead["score"], 45)  # 30 + 15 for a non-free domain
        self.assertEqual(lead["owner"], "r1")
        self.assertEqual(lead["status"], "new")
        self.assertEqual(crm.log, [("add_lead", "L1", "r1")])

    def test_source_scores(self):
        crm = big_crm()
        self.assertEqual(crm.leads[crm.add_lead("a@gmail.com", "A", "web", "r1")]["score"], 10)
        self.assertEqual(crm.leads[crm.add_lead("b@gmail.com", "B", "event", "r1")]["score"], 20)
        self.assertEqual(crm.leads[crm.add_lead("c@gmail.com", "C", "referral", "r1")]["score"], 30)
        self.assertEqual(crm.leads[crm.add_lead("d@acme.io", "D", "web", "r1")]["score"], 25)

    def test_invalid_email(self):
        crm = big_crm()
        for bad in ["no-at", "a@@b.com", "@example.com", "a@nodot", "a@.com", "a@com.", 5, None]:
            with self.assertRaises(ValueError):
                crm.add_lead(bad, "Name", "web", "r1")
        self.assertEqual(crm.leads, {})
        self.assertEqual(crm.log, [])

    def test_invalid_name_and_source(self):
        crm = big_crm()
        with self.assertRaises(ValueError):
            crm.add_lead("a@example.com", "   ", "web", "r1")
        with self.assertRaises(ValueError):
            crm.add_lead("a@example.com", "A", "phone", "r1")

    def test_unknown_actor_checked_first(self):
        crm = big_crm()
        with self.assertRaises(PermissionError):
            crm.add_lead("broken", "", "phone", "nobody")
        self.assertEqual(crm.log, [])

    def test_duplicate_lead(self):
        crm = big_crm()
        first = crm.add_lead("a@example.com", "A", "web", "r1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            crm.add_lead("  A@EXAMPLE.com ", "Other", "event", "r1")
        self.assertEqual(ctx.exception.existing_id, first)
        # a failed duplicate does not consume an id or add a log entry
        self.assertEqual(crm.add_lead("b@example.com", "B", "web", "r1"), "L2")
        self.assertEqual(len(crm.log), 2)

    def test_tie_break_and_queue(self):
        crm = small_crm()
        self.assertEqual(crm.leads[crm.add_lead("a@example.com", "A", "referral", "r1")]["owner"], "r1")
        self.assertEqual(crm.leads[crm.add_lead("b@example.com", "B", "referral", "r1")]["owner"], "r2")
        self.assertEqual(crm.leads[crm.add_lead("c@example.com", "C", "referral", "r1")]["owner"], "r1")
        lead4 = crm.add_lead("d@example.com", "D", "referral", "r1")
        self.assertIsNone(crm.leads[lead4]["owner"])


class QualifyTests(unittest.TestCase):
    def test_qualify_requires_score_and_owner(self):
        crm = big_crm()
        low = crm.add_lead("a@gmail.com", "A", "web", "r1")
        with self.assertRaises(ValueError):
            crm.qualify(low, "r1")
        good = crm.add_lead("b@example.com", "B", "referral", "r1")
        with self.assertRaises(PermissionError):
            crm.qualify(good, "r1")  # r1 does not own this lead
        crm.qualify(good, "r2")
        self.assertEqual(crm.leads[good]["status"], "qualified")
        self.assertEqual(crm.log[-1], ("qualify", good, "r2"))
        with self.assertRaises(ValueError):
            crm.qualify(good, "r2")  # no longer "new"

    def test_manager_may_qualify(self):
        crm = big_crm()
        lead = crm.add_lead("a@example.com", "A", "referral", "r1")
        crm.qualify(lead, "m1")
        self.assertEqual(crm.leads[lead]["status"], "qualified")

    def test_unknown_lead(self):
        crm = big_crm()
        with self.assertRaises(ValueError):
            crm.qualify("L99", "r1")


class ConvertTests(unittest.TestCase):
    def test_convert_creates_opportunity(self):
        crm = big_crm()
        lead = crm.add_lead("a@example.com", "A", "referral", "r1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 5000, "r1")
        self.assertEqual(opp, "O1")
        self.assertEqual(crm.opps[opp], {
            "id": "O1",
            "lead_id": lead,
            "owner": "r1",
            "amount": 5000,
            "original_amount": 5000,
            "stage": "prospect",
        })
        self.assertEqual(crm.leads[lead]["status"], "converted")
        self.assertEqual(crm.log[-1], ("convert", "O1", "r1"))

    def test_amount_validation(self):
        crm = big_crm()
        lead = crm.add_lead("a@example.com", "A", "referral", "r1")
        crm.qualify(lead, "r1")
        for bad in [0, -1, True, 1.5, "100", None]:
            with self.assertRaises(ValueError):
                crm.convert(lead, bad, "r1")
        self.assertEqual(crm.leads[lead]["status"], "qualified")
        self.assertEqual(crm.opps, {})

    def test_requires_qualified_status_and_permission(self):
        crm = big_crm()
        lead = crm.add_lead("a@example.com", "A", "referral", "r1")
        with self.assertRaises(ValueError):
            crm.convert(lead, 100, "r1")  # still new
        crm.qualify(lead, "r1")
        with self.assertRaises(PermissionError):
            crm.convert(lead, 100, "r2")

    def test_unowned_lead_cannot_convert(self):
        crm = small_crm()
        crm.add_lead("a@example.com", "A", "referral", "r1")
        crm.add_lead("b@example.com", "B", "referral", "r1")
        crm.add_lead("c@example.com", "C", "referral", "r1")
        queued = crm.add_lead("d@example.com", "D", "referral", "r1")
        crm.qualify(queued, "m1")
        with self.assertRaises(ValueError):
            crm.convert(queued, 100, "m1")


class AdvanceTests(unittest.TestCase):
    def test_full_path_and_frees_slot(self):
        crm = small_crm()
        first = crm.add_lead("a@example.com", "A", "referral", "r1")
        crm.add_lead("b@example.com", "B", "referral", "r1")
        crm.add_lead("c@example.com", "C", "referral", "r1")
        queued = crm.add_lead("d@example.com", "D", "referral", "r1")
        crm.qualify(first, "r1")
        opp = crm.convert(first, 1000, "r1")
        crm.advance(opp, "proposal", "r1")
        crm.advance(opp, "negotiation", "r1")
        self.assertEqual(crm.opps[opp]["stage"], "negotiation")
        self.assertEqual(crm.log[-1], ("advance", opp, "r1"))
        crm.advance(opp, "won", "r1")
        self.assertEqual(crm.leads[queued]["owner"], "r1")
        self.assertEqual(crm.log[-1], ("assign", queued, "system"))

    def test_invalid_transitions(self):
        crm = big_crm()
        opp = seed_opp(crm, 1000)
        with self.assertRaises(ValueError):
            crm.advance(opp, "negotiation", "r1")  # skips proposal
        with self.assertRaises(ValueError):
            crm.advance("O99", "proposal", "r1")
        with self.assertRaises(ValueError):
            crm.advance(opp, "bogus", "r1")
        with self.assertRaises(PermissionError):
            crm.advance(opp, "proposal", "r2")
        crm.advance(opp, "proposal", "r1")
        with self.assertRaises(ValueError):
            crm.advance(opp, "prospect", "r1")  # backwards

    def test_final_stage_is_frozen(self):
        crm = big_crm()
        opp = seed_opp(crm, 1000)
        crm.advance(opp, "lost", "r1")
        with self.assertRaises(ValueError):
            crm.advance(opp, "won", "r1")

    def test_large_negotiation_requires_manager(self):
        crm = big_crm()
        opp = seed_opp(crm, 60000, stage="proposal")
        with self.assertRaises(PermissionError):
            crm.advance(opp, "negotiation", "r1")
        crm.advance(opp, "negotiation", "m1")
        self.assertEqual(crm.opps[opp]["stage"], "negotiation")


class DiscountTests(unittest.TestCase):
    def test_discount_and_limits(self):
        crm = big_crm()
        opp = seed_opp(crm, 1000)
        with self.assertRaises(ValueError):
            crm.discount(opp, 0, "r1")
        with self.assertRaises(ValueError):
            crm.discount(opp, 31, "r1")
        with self.assertRaises(ValueError):
            crm.discount(opp, True, "r1")
        with self.assertRaises(PermissionError):
            crm.discount(opp, 11, "r1")
        with self.assertRaises(PermissionError):
            crm.discount(opp, 5, "r2")
        crm.discount(opp, 10, "r1")
        self.assertEqual(crm.opps[opp]["amount"], 900)
        self.assertEqual(crm.log[-1], ("discount", opp, "r1"))
        crm.discount(opp, 20, "m1")
        self.assertEqual(crm.opps[opp]["amount"], 720)
        with self.assertRaises(ValueError):
            crm.discount(opp, 3, "m1")  # would break the 30% cumulative floor
        self.assertEqual(crm.opps[opp]["amount"], 720)

    def test_discount_on_final_stage(self):
        crm = big_crm()
        opp = seed_opp(crm, 1000)
        crm.advance(opp, "lost", "r1")
        with self.assertRaises(ValueError):
            crm.discount(opp, 10, "r1")
        self.assertEqual(crm.opps[opp]["amount"], 1000)


class TransferTests(unittest.TestCase):
    def test_only_manager_transfers(self):
        crm = big_crm()
        opp = seed_opp(crm, 1000)
        with self.assertRaises(PermissionError):
            crm.transfer(opp, "r2", "r1")
        with self.assertRaises(ValueError):
            crm.transfer(opp, "m1", "m1")  # not a rep
        with self.assertRaises(ValueError):
            crm.transfer(opp, "r1", "m1")  # same owner
        crm.transfer(opp, "r2", "m1")
        self.assertEqual(crm.opps[opp]["owner"], "r2")
        self.assertEqual(crm.log[-1], ("transfer", opp, "m1"))

    def test_capacity_and_final_state(self):
        crm = small_crm()
        first = crm.add_lead("a@example.com", "A", "referral", "r1")
        crm.add_lead("b@example.com", "B", "referral", "r1")  # r2, now full
        crm.qualify(first, "r1")
        opp = crm.convert(first, 1000, "r1")
        with self.assertRaises(ValueError):
            crm.transfer(opp, "r2", "m1")  # r2 is at capacity
        crm.advance(opp, "lost", "r1")
        with self.assertRaises(ValueError):
            crm.transfer(opp, "r2", "m1")  # final stage


class ForecastTests(unittest.TestCase):
    def test_forecast(self):
        crm = big_crm()
        seed_opp(crm, 1000, "prospect")
        seed_opp(crm, 2000, "proposal")
        seed_opp(crm, 3000, "won")
        self.assertEqual(crm.forecast(), {"open": 2, "weighted": 100 + 600, "won": 3000})

    def test_empty_forecast(self):
        self.assertEqual(big_crm().forecast(), {"open": 0, "weighted": 0, "won": 0})


if __name__ == "__main__":
    unittest.main()
