"""Unit tests for crm.py (spec: /tmp/aep-lab/specs/crm.md)."""

import unittest

from crm import CRM, DuplicateLeadError


def make_crm():
    return CRM([
        {"id": "r1", "role": "rep", "capacity": 2},
        {"id": "r2", "role": "rep", "capacity": 1},
        {"id": "m1", "role": "manager", "capacity": 0},
    ])


class AddLeadTests(unittest.TestCase):
    def test_happy_path(self):
        crm = make_crm()
        lead_id = crm.add_lead("  Ana@Gmail.COM ", "  Ana  ", "web", "m1")
        self.assertEqual(lead_id, "L1")
        lead = crm.leads["L1"]
        self.assertEqual(lead["email"], "ana@gmail.com")
        self.assertEqual(lead["name"], "Ana")
        self.assertEqual(lead["score"], 10)  # web, free domain
        self.assertEqual(lead["owner"], "r1")  # lowest load (0), tie with r2 -> r1
        self.assertEqual(lead["status"], "new")
        self.assertEqual(crm.log, [("add_lead", "L1", "m1")])

    def test_score_plus15_and_sources(self):
        crm2 = make_crm()
        crm2.add_lead("a@corp.com", "A", "web", "m1")
        crm2.add_lead("b@corp.com", "B", "referral", "m1")
        crm2.add_lead("c@corp.com", "C", "event", "m1")
        self.assertEqual(crm2.leads["L1"]["score"], 25)  # 10 + 15
        self.assertEqual(crm2.leads["L2"]["score"], 45)  # 30 + 15
        self.assertEqual(crm2.leads["L3"]["score"], 35)  # 20 + 15

    def test_email_validation(self):
        crm = make_crm()
        bad = ["noat.com", "a@b@c.com", "@b.com", "a@bcom", "a@.bc", "a@bc.", "a@b.c"]
        for email in bad[:6]:
            with self.assertRaises(ValueError):
                crm.add_lead(email, "N", "web", "m1")
        # a@b.c is valid: dot is not first/last char of domain "b.c"
        crm.add_lead("a@b.c", "N", "web", "m1")
        with self.assertRaises(ValueError):
            crm.add_lead(123, "N", "web", "m1")

    def test_name_and_source_validation(self):
        crm = make_crm()
        with self.assertRaises(ValueError):
            crm.add_lead("a@b.co", "   ", "web", "m1")
        with self.assertRaises(ValueError):
            crm.add_lead("a@b.co", None, "web", "m1")
        with self.assertRaises(ValueError):
            crm.add_lead("a@b.co", "N", "mail", "m1")

    def test_duplicate(self):
        crm = make_crm()
        crm.add_lead("a@b.co", "A", "web", "m1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            crm.add_lead("  A@B.CO ", "A2", "referral", "m1")
        self.assertEqual(ctx.exception.existing_id, "L1")

    def test_unknown_actor(self):
        crm = make_crm()
        with self.assertRaises(PermissionError):
            crm.add_lead("a@b.co", "A", "web", "nobody")

    def test_waiting_queue_when_no_capacity(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 0},
                   {"id": "m1", "role": "manager", "capacity": 0}])
        lead_id = crm.add_lead("a@b.co", "A", "web", "m1")
        self.assertIsNone(crm.leads[lead_id]["owner"])


class QualifyTests(unittest.TestCase):
    def test_happy_path_owner(self):
        crm = make_crm()
        crm.add_lead("a@corp.com", "A", "referral", "m1")  # score 45, owner r1
        crm.qualify("L1", "r1")
        self.assertEqual(crm.leads["L1"]["status"], "qualified")
        self.assertEqual(crm.log[-1], ("qualify", "L1", "r1"))

    def test_manager_may_qualify(self):
        crm = make_crm()
        crm.add_lead("a@corp.com", "A", "referral", "m1")
        crm.qualify("L1", "m1")

    def test_unknown_lead_is_valueerror(self):
        crm = make_crm()
        with self.assertRaises(ValueError):
            crm.qualify("L99", "r1")

    def test_errors_in_order(self):
        crm = make_crm()
        crm.add_lead("a@corp.com", "A", "referral", "m1")
        with self.assertRaises(PermissionError):  # not owner, not manager
            crm.qualify("L1", "r2")
        crm.add_lead("b@gmail.com", "B", "web", "m1")  # score 10 < 30
        with self.assertRaises(ValueError):
            crm.qualify("L2", "m1")
        crm.qualify("L1", "m1")
        with self.assertRaises(ValueError):  # already qualified
            crm.qualify("L1", "m1")
        self.assertEqual([e[0] for e in crm.log],
                         ["add_lead", "add_lead", "qualify"])

    def test_failed_call_logs_nothing(self):
        crm = make_crm()
        crm.add_lead("a@gmail.com", "A", "web", "m1")
        before = list(crm.log)
        with self.assertRaises(ValueError):
            crm.qualify("L1", "m1")  # score 10 < 30
        self.assertEqual(crm.log, before)
        self.assertEqual(crm.leads["L1"]["status"], "new")


class ConvertTests(unittest.TestCase):
    def _qualified_lead(self, crm):
        crm.add_lead("a@corp.com", "A", "referral", "m1")
        crm.qualify("L1", "m1")

    def test_happy_path(self):
        crm = make_crm()
        self._qualified_lead(crm)
        opp_id = crm.convert("L1", 100000, "r1")
        self.assertEqual(opp_id, "O1")
        opp = crm.opps["O1"]
        self.assertEqual(opp, {"id": "O1", "lead_id": "L1", "owner": "r1",
                               "amount": 100000, "original_amount": 100000,
                               "stage": "prospect"})
        self.assertEqual(crm.leads["L1"]["status"], "converted")
        self.assertEqual(crm.log[-1], ("convert", "O1", "r1"))

    def test_error_order(self):
        crm = make_crm()
        with self.assertRaises(ValueError):  # unknown lead checked before amount
            crm.convert("L99", True, "r1")
        self._qualified_lead(crm)
        with self.assertRaises(ValueError):  # bool is not a valid amount
            crm.convert("L1", True, "r1")
        with self.assertRaises(PermissionError):  # not owner/manager
            crm.convert("L1", 100, "r2")
        crm.add_lead("b@corp.com", "B", "referral", "m1")  # owner r2 (r1 busy)
        with self.assertRaises(ValueError):  # status is 'new', not 'qualified'
            crm.convert("L2", 100, "r2")
        crm.qualify("L2", "m1")
        crm.convert("L2", 100, "r2")
        crm.convert("L1", 100, "m1")
        with self.assertRaises(ValueError):  # already converted
            crm.convert("L1", 100, "m1")

    def test_opp_counter_counts_successes(self):
        crm = make_crm()
        self._qualified_lead(crm)
        crm.convert("L1", 10, "r1")
        crm.add_lead("b@corp.com", "B", "referral", "m1")  # owner r2
        crm.qualify("L2", "m1")
        self.assertEqual(crm.convert("L2", 10, "r2"), "O2")


class AdvanceTests(unittest.TestCase):
    def _opp(self, crm, amount=1000, actor="m1"):
        crm.add_lead("a@corp.com", "A", "referral", actor)
        crm.qualify("L1", actor)
        return crm.convert("L1", amount, actor)

    def test_stage_flow(self):
        crm = make_crm()
        opp = self._opp(crm)
        crm.advance(opp, "proposal", "r1")
        crm.advance(opp, "negotiation", "r1")
        crm.advance(opp, "won", "r1")
        self.assertEqual(crm.opps[opp]["stage"], "won")

    def test_lost_from_any_nonfinal(self):
        crm = make_crm()
        opp = self._opp(crm)
        crm.advance(opp, "lost", "m1")

    def test_errors(self):
        crm = make_crm()
        with self.assertRaises(ValueError):
            crm.advance("O99", "proposal", "r1")
        opp = self._opp(crm)
        with self.assertRaises(ValueError):  # invalid stage name
            crm.advance(opp, "bogus", "r1")
        with self.assertRaises(PermissionError):  # not owner/manager
            crm.advance(opp, "proposal", "r2")
        with self.assertRaises(ValueError):  # skip a stage
            crm.advance(opp, "negotiation", "r1")
        with self.assertRaises(ValueError):  # backwards: not lost, not next
            crm.advance(opp, "prospect", "r1")
        crm.advance(opp, "lost", "m1")
        with self.assertRaises(ValueError):  # final stage cannot advance
            crm.advance(opp, "proposal", "m1")
        self.assertEqual(crm.opps[opp]["stage"], "lost")

    def test_big_negotiation_needs_manager(self):
        crm = make_crm()
        opp = self._opp(crm, amount=60000)
        crm.advance(opp, "proposal", "r1")  # only negotiation is manager-gated
        with self.assertRaises(PermissionError):
            crm.advance(opp, "negotiation", "r1")
        crm.advance(opp, "negotiation", "m1")

    def test_won_frees_slot_and_assigns_waiting(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1},
                   {"id": "m1", "role": "manager", "capacity": 0}])
        opp = self._opp(crm)  # r1 at load 1 (capacity 1)
        w1 = crm.add_lead("b@b.co", "B", "web", "m1")  # no capacity -> waiting
        w2 = crm.add_lead("c@b.co", "C", "web", "m1")
        self.assertIsNone(crm.leads[w1]["owner"])
        crm.advance(opp, "proposal", "m1")
        crm.advance(opp, "negotiation", "m1")
        crm.advance(opp, "won", "m1")
        self.assertEqual(crm.leads[w1]["owner"], "r1")  # capacity 1, refilled
        self.assertIsNone(crm.leads[w2]["owner"])       # FIFO: still waiting
        self.assertEqual(crm.log[-2], ("advance", opp, "m1"))
        self.assertEqual(crm.log[-1], ("assign", w1, "system"))


class DiscountTests(unittest.TestCase):
    def _opp(self, crm, amount=1000):
        crm.add_lead("a@corp.com", "A", "referral", "m1")
        crm.qualify("L1", "m1")
        return crm.convert("L1", amount, "r1")

    def test_happy_path(self):
        crm = make_crm()
        opp = self._opp(crm, amount=1000)
        crm.discount(opp, 10, "r1")   # 1000 -> 900 (total 10%)
        self.assertEqual(crm.opps[opp]["amount"], 900)
        crm.discount(opp, 22, "m1")   # 900*78//100 = 702; 70200 >= 70000 floor
        self.assertEqual(crm.opps[opp]["amount"], 702)

    def test_errors(self):
        crm = make_crm()
        with self.assertRaises(ValueError):
            crm.discount("O99", 10, "r1")
        opp = self._opp(crm, amount=100)
        with self.assertRaises(ValueError):
            crm.discount(opp, True, "r1")
        with self.assertRaises(ValueError):
            crm.discount(opp, 0, "r1")
        with self.assertRaises(ValueError):
            crm.discount(opp, 31, "r1")
        with self.assertRaises(PermissionError):  # not owner/manager
            crm.discount(opp, 10, "r2")
        with self.assertRaises(PermissionError):  # rep over 10
            crm.discount(opp, 11, "r1")
        crm.discount(opp, 10, "r1")   # 100 -> 90 (total 10%)
        self.assertEqual(crm.opps[opp]["amount"], 90)
        with self.assertRaises(ValueError):  # 90 -> 69 would be 31% total
            crm.discount(opp, 23, "m1")
        self.assertEqual(crm.opps[opp]["amount"], 90)  # nothing applied

    def test_exact_30_percent_ok(self):
        crm = make_crm()
        opp = self._opp(crm, amount=100)
        crm.discount(opp, 30, "m1")
        self.assertEqual(crm.opps[opp]["amount"], 70)


class TransferTests(unittest.TestCase):
    def test_happy_path(self):
        crm = make_crm()
        crm.add_lead("a@corp.com", "A", "referral", "m1")  # owner r1
        crm.qualify("L1", "m1")
        opp = crm.convert("L1", 100, "r1")
        crm.transfer(opp, "r2", "m1")  # r2 load 0 < capacity 1
        self.assertEqual(crm.opps[opp]["owner"], "r2")
        self.assertEqual([e for e in crm.log if e[0] == "transfer"],
                         [("transfer", opp, "m1")])

    def test_errors(self):
        crm = make_crm()
        crm.add_lead("a@corp.com", "A", "referral", "m1")
        crm.qualify("L1", "m1")
        opp = crm.convert("L1", 100, "r1")
        with self.assertRaises(ValueError):
            crm.transfer("O99", "r2", "m1")
        with self.assertRaises(PermissionError):  # only a manager transfers
            crm.transfer(opp, "r2", "r1")
        with self.assertRaises(ValueError):  # unknown user
            crm.transfer(opp, "ghost", "m1")
        with self.assertRaises(ValueError):  # managers never own
            crm.transfer(opp, "m1", "m1")
        with self.assertRaises(ValueError):  # same owner
            crm.transfer(opp, "r1", "m1")

    def test_new_owner_at_capacity(self):
        crm = make_crm()
        crm.add_lead("a@corp.com", "A", "referral", "m1")
        crm.qualify("L1", "m1")
        opp = crm.convert("L1", 100, "r1")
        crm.add_lead("filler@b.co", "F", "web", "m1")  # r2 -> load 1, capacity 1
        with self.assertRaises(ValueError):
            crm.transfer(opp, "r2", "m1")
        self.assertEqual(crm.opps[opp]["owner"], "r1")

    def test_final_stage_cannot_transfer(self):
        crm = make_crm()
        crm.add_lead("a@corp.com", "A", "referral", "m1")
        crm.qualify("L1", "m1")
        opp = crm.convert("L1", 100, "r1")
        crm.advance(opp, "lost", "m1")
        with self.assertRaises(ValueError):
            crm.transfer(opp, "r2", "m1")
        self.assertEqual(crm.opps[opp]["owner"], "r1")


class ForecastTests(unittest.TestCase):
    def test_forecast(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 5},
                   {"id": "r2", "role": "rep", "capacity": 5},
                   {"id": "m1", "role": "manager", "capacity": 0}])
        self.assertEqual(crm.forecast(), {"open": 0, "weighted": 0, "won": 0})
        crm.add_lead("a@corp.com", "A", "referral", "m1")
        crm.qualify("L1", "m1")
        o1 = crm.convert("L1", 1000, "r1")   # prospect, w=10
        crm.add_lead("b@corp.com", "B", "referral", "m1")
        crm.qualify("L2", "m1")
        o2 = crm.convert("L2", 1000, "r2")   # prospect
        crm.advance(o2, "proposal", "r2")    # w=30
        crm.add_lead("c@corp.com", "C", "referral", "m1")
        crm.qualify("L3", "m1")
        o3 = crm.convert("L3", 1000, "r1")
        crm.advance(o3, "proposal", "r1")
        crm.advance(o3, "negotiation", "r1")  # w=60
        crm.add_lead("d@corp.com", "D", "referral", "m1")
        crm.qualify("L4", "m1")
        o4 = crm.convert("L4", 500, "r2")
        crm.advance(o4, "proposal", "r2")
        crm.advance(o4, "negotiation", "r2")
        crm.advance(o4, "won", "r2")
        # open: o1 (100), o2 (300), o3 (600) -> open=3, weighted=100+300+600=1000
        self.assertEqual(crm.forecast(), {"open": 3, "weighted": 1000, "won": 500})


class LoadAccountingTests(unittest.TestCase):
    def test_converted_lead_frees_lead_slot_via_opp(self):
        # A converted lead no longer counts as a lead, but its open opp counts.
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1},
                   {"id": "m1", "role": "manager", "capacity": 0}])
        crm.add_lead("a@corp.com", "A", "referral", "m1")
        crm.qualify("L1", "m1")
        crm.convert("L1", 100, "r1")  # still load 1 (open opp)
        w = crm.add_lead("w@b.co", "W", "web", "m1")  # waiting
        self.assertIsNone(crm.leads[w]["owner"])
        crm.advance("O1", "lost", "m1")  # frees the slot
        self.assertEqual(crm.leads[w]["owner"], "r1")


if __name__ == "__main__":
    unittest.main()
