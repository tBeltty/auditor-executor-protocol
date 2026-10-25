import unittest

from crm import CRM, DuplicateLeadError
from helpers import GuardChecks

REPS = [
    {"id": "r1", "role": "rep", "capacity": 3},
    {"id": "r2", "role": "rep", "capacity": 3},
    {"id": "r3", "role": "rep", "capacity": 1},
    {"id": "m1", "role": "manager", "capacity": 9},
]


def build():
    return CRM([dict(rep) for rep in REPS])


def make_opp(crm, email, amount, owner="r1"):
    lead = crm.add_lead(email, "N", "referral", owner)
    crm.qualify(lead, owner)
    return crm.convert(lead, amount, owner)


class GuardTests(GuardChecks, unittest.TestCase):
    def test_unknown_actor_is_rejected_first(self):
        crm = build()
        self.expect_error("ACTOR_GUARD", PermissionError,
                          crm.add_lead, "a@x.com", "A", "web", "ghost")
        self.expect_error("ACTOR_GUARD", PermissionError,
                          crm.qualify, "L1", "ghost")
        self.assertEqual(crm.leads, {})
        self.assertEqual(crm.log, [])

    def test_only_owner_or_manager_may_qualify(self):
        crm = build()
        lead = crm.add_lead("a@corp.com", "A", "referral", "r1")
        self.expect_error("PERM_GUARD", PermissionError, crm.qualify, lead, "r2")
        self.assertEqual(crm.leads[lead]["status"], "new")
        self.assertEqual(crm.log, [("add_lead", lead, "r1")])
        crm.qualify(lead, "m1")
        self.assertEqual(crm.leads[lead]["status"], "qualified")

    def test_only_owner_or_manager_may_convert_and_advance(self):
        crm = build()
        opp = make_opp(crm, "a@corp.com", 1000)
        self.expect_error("PERM_GUARD", PermissionError,
                          crm.advance, opp, "proposal", "r2")
        self.expect_error("PERM_GUARD", PermissionError,
                          crm.discount, opp, 5, "r2")
        self.assertEqual(crm.opps[opp]["stage"], "prospect")
        self.assertEqual(crm.opps[opp]["amount"], 1000)

    def test_duplicate_email_rejected(self):
        crm = build()
        first = crm.add_lead("User@Corp.com", "A", "web", "r1")
        try:
            crm.add_lead("  user@corp.COM ", "Other", "event", "r2")
        except DuplicateLeadError as err:
            self.assertEqual(err.existing_id, first,
                             "DUPLICATE_GUARD: existing_id must point at the original lead")
        else:
            self.fail("DUPLICATE_GUARD: duplicate email must raise DuplicateLeadError")
        self.assertEqual(list(crm.leads), [first])
        self.assertEqual(crm.log, [("add_lead", first, "r1")])

    def test_score_below_thirty_cannot_qualify(self):
        crm = build()
        lead = crm.add_lead("a@gmail.com", "A", "web", "r1")
        self.expect_error("SCORE_GUARD", ValueError, crm.qualify, lead, "r1")
        self.assertEqual(crm.leads[lead]["status"], "new")
        boundary = crm.add_lead("b@gmail.com", "B", "referral", "r1")
        self.assertEqual(crm.leads[boundary]["score"], 30)
        crm.qualify(boundary, crm.leads[boundary]["owner"])
        self.assertEqual(crm.leads[boundary]["status"], "qualified")

    def test_cannot_skip_stages(self):
        crm = build()
        opp = make_opp(crm, "a@corp.com", 1000)
        self.expect_error("TRANSITION_GUARD", ValueError,
                          crm.advance, opp, "won", "m1")
        self.expect_error("TRANSITION_GUARD", ValueError,
                          crm.advance, opp, "negotiation", "m1")
        self.assertEqual(crm.opps[opp]["stage"], "prospect")
        crm.advance(opp, "proposal", "r1")
        self.expect_error("TRANSITION_GUARD", ValueError,
                          crm.advance, opp, "prospect", "r1")

    def test_big_deal_needs_manager(self):
        crm = build()
        opp = make_opp(crm, "a@corp.com", 60000)
        crm.advance(opp, "proposal", "r1")
        self.expect_error("BIGDEAL_GUARD", PermissionError,
                          crm.advance, opp, "negotiation", "r1")
        self.assertEqual(crm.opps[opp]["stage"], "proposal")
        crm.advance(opp, "negotiation", "m1")
        self.assertEqual(crm.opps[opp]["stage"], "negotiation")

    def test_big_deal_threshold_is_exclusive(self):
        crm = build()
        opp = make_opp(crm, "a@corp.com", 50000)
        crm.advance(opp, "proposal", "r1")
        crm.advance(opp, "negotiation", "r1")
        self.assertEqual(crm.opps[opp]["stage"], "negotiation")

    def test_discount_percentage_bounds(self):
        crm = build()
        opp = make_opp(crm, "a@corp.com", 1000)
        for bad in (0, 31, -5, True, "10", 2.5, None):
            self.expect_error("PCT_GUARD", ValueError, crm.discount, opp, bad, "m1")
        self.assertEqual(crm.opps[opp]["amount"], 1000)
        crm.discount(opp, 30, "m1")
        self.assertEqual(crm.opps[opp]["amount"], 700)

    def test_non_manager_discount_capped_at_ten(self):
        crm = build()
        opp = make_opp(crm, "a@corp.com", 1000)
        self.expect_error("PCT_ROLE_GUARD", PermissionError,
                          crm.discount, opp, 15, "r1")
        self.assertEqual(crm.opps[opp]["amount"], 1000)
        crm.discount(opp, 10, "r1")
        self.assertEqual(crm.opps[opp]["amount"], 900)

    def test_cumulative_discount_floor(self):
        crm = build()
        opp = make_opp(crm, "a@corp.com", 1000)
        crm.discount(opp, 30, "m1")
        self.expect_error("FLOOR_GUARD", ValueError, crm.discount, opp, 1, "m1")
        self.assertEqual(crm.opps[opp]["amount"], 700)

    def test_transfer_requires_manager_and_rep_target(self):
        crm = build()
        opp = make_opp(crm, "a@corp.com", 1000)
        self.expect_error("TRANSFER_ROLE_GUARD", PermissionError,
                          crm.transfer, opp, "r2", "r1")
        self.expect_error("TRANSFER_ROLE_GUARD", ValueError,
                          crm.transfer, opp, "m1", "m1")
        self.expect_error("TRANSFER_ROLE_GUARD", ValueError,
                          crm.transfer, opp, "nobody", "m1")
        self.assertEqual(crm.opps[opp]["owner"], "r1")

    def test_transfer_rejects_same_owner(self):
        crm = build()
        opp = make_opp(crm, "a@corp.com", 1000)
        self.expect_error("TRANSFER_SAME_GUARD", ValueError,
                          crm.transfer, opp, "r1", "m1")
        self.assertEqual(crm.opps[opp]["owner"], "r1")

    def test_transfer_rejects_full_target(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 5},
            {"id": "r3", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 5},
        ])
        opp = make_opp(crm, "a@corp.com", 1000)
        crm.add_lead("b@corp.com", "B", "web", "m1")
        self.assertEqual(crm.leads["L2"]["owner"], "r3")
        self.expect_error("TRANSFER_CAP_GUARD", ValueError,
                          crm.transfer, opp, "r3", "m1")
        self.assertEqual(crm.opps[opp]["owner"], "r1")

    def test_transfer_rejects_final_stage(self):
        crm = build()
        opp = make_opp(crm, "a@corp.com", 1000)
        for stage in ("proposal", "negotiation", "won"):
            crm.advance(opp, stage, "r1")
        self.expect_error("TRANSFER_FINAL_GUARD", ValueError,
                          crm.transfer, opp, "r2", "m1")


if __name__ == "__main__":
    unittest.main()
