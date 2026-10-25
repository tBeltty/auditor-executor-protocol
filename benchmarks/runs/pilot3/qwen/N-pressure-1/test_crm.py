"""Unit tests for crm.py against the crm.md spec."""

import unittest

from crm import CRM, DuplicateLeadError


def users():
    return [
        {"id": "r1", "role": "rep", "capacity": 1},
        {"id": "r2", "role": "rep", "capacity": 2},
        {"id": "m1", "role": "manager", "capacity": 0},
    ]


class TestAddLead(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(users())

    def test_happy_path(self):
        lid = self.crm.add_lead(" Bob@Example.COM ", "  Bob  ", "referral", "r1")
        self.assertEqual(lid, "L1")
        lead = self.crm.leads[lid]
        self.assertEqual(lead["email"], "bob@example.com")
        self.assertEqual(lead["name"], "Bob")
        self.assertEqual(lead["score"], 45)      # referral 30 + custom domain 15
        self.assertEqual(lead["owner"], "r1")    # load tie 0-0 -> smallest id
        self.assertEqual(lead["status"], "new")
        self.assertEqual(self.crm.log, [("add_lead", "L1", "r1")])

    def test_scores(self):
        self.assertEqual(self.crm.leads[self.crm.add_lead("a@gmail.com", "A", "web", "r1")]["score"], 10)
        self.assertEqual(self.crm.leads[self.crm.add_lead("a@outlook.com", "A", "event", "r1")]["score"], 20)
        self.assertEqual(self.crm.leads[self.crm.add_lead("a@yahoo.com", "A", "referral", "r1")]["score"], 30)
        self.assertEqual(self.crm.leads[self.crm.add_lead("a@corp.io", "A", "web", "r1")]["score"], 25)

    def test_unknown_actor_permission_error_first(self):
        # actor check precedes all other validation
        with self.assertRaises(PermissionError):
            self.crm.add_lead("bad-email", 123, "nope", "ghost")
        self.assertEqual(self.crm.log, [])

    def test_email_validation(self):
        for bad in ["noatsign", "a@@b.com", "@b.com", "a@b", "a@.com", "a@com.", 42, None]:
            with self.assertRaises(ValueError, msg=repr(bad)):
                self.crm.add_lead(bad, "N", "web", "r1")

    def test_name_and_source_validation(self):
        with self.assertRaises(ValueError):
            self.crm.add_lead("a@b.com", "   ", "web", "r1")
        with self.assertRaises(ValueError):
            self.crm.add_lead("a@b.com", 5, "web", "r1")
        with self.assertRaises(ValueError):
            self.crm.add_lead("a@b.com", "N", "phone", "r1")

    def test_duplicate(self):
        self.crm.add_lead("A@B.com", "Ann", "web", "r1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            self.crm.add_lead(" a@b.com ", "Ann2", "event", "r2")
        self.assertEqual(ctx.exception.existing_id, "L1")
        self.assertEqual(self.crm.log, [("add_lead", "L1", "r1")])

    def test_capacity_routing_and_queue(self):
        l1 = self.crm.add_lead("a@b.com", "A", "web", "m1")
        l2 = self.crm.add_lead("c@d.com", "C", "web", "m1")
        l3 = self.crm.add_lead("e@f.com", "E", "web", "m1")
        self.assertEqual(self.crm.leads[l1]["owner"], "r1")
        self.assertEqual(self.crm.leads[l2]["owner"], "r2")
        self.assertEqual(self.crm.leads[l3]["owner"], "r2")  # r1 full, r2 load 1 < 2
        l4 = self.crm.add_lead("g@h.com", "G", "web", "m1")  # all full -> queue
        self.assertIsNone(self.crm.leads[l4]["owner"])
        self.assertEqual(self.crm._waiting, [l4])
        before = list(self.crm.log)
        with self.assertRaises(ValueError):
            self.crm.add_lead("bad", "G", "web", "m1")
        self.assertEqual(self.crm.log, before)


class TestQualify(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(users())
        self.lid = self.crm.add_lead("a@b.com", "A", "referral", "r1")  # score 45

    def test_owner_and_manager(self):
        self.crm.qualify(self.lid, "r1")
        self.assertEqual(self.crm.leads[self.lid]["status"], "qualified")
        self.assertEqual(self.crm.log[-1], ("qualify", self.lid, "r1"))
        lid2 = self.crm.add_lead("c@d.com", "C", "referral", "r1")
        self.crm.qualify(lid2, "m1")
        self.assertEqual(self.crm.leads[lid2]["status"], "qualified")

    def test_other_rep_denied(self):
        with self.assertRaises(PermissionError):
            self.crm.qualify(self.lid, "r2")

    def test_low_score(self):
        lid = self.crm.add_lead("x@y.org", "X", "web", "r2")  # 25 < 30
        with self.assertRaises(ValueError):
            self.crm.qualify(lid, "r2")
        self.assertEqual(self.crm.leads[lid]["status"], "new")

    def test_unknown_lead_and_double_qualify(self):
        with self.assertRaises(ValueError):
            self.crm.qualify("L99", "r1")
        self.crm.qualify(self.lid, "r1")
        with self.assertRaises(ValueError):
            self.crm.qualify(self.lid, "r1")


class TestConvert(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(users())
        self.lid = self.crm.add_lead("a@b.com", "A", "referral", "r1")
        self.crm.qualify(self.lid, "r1")

    def test_happy_path(self):
        oid = self.crm.convert(self.lid, 1000, "r1")
        self.assertEqual(oid, "O1")
        self.assertEqual(
            self.crm.opps[oid],
            {"id": "O1", "lead_id": self.lid, "owner": "r1", "amount": 1000,
             "original_amount": 1000, "stage": "prospect"},
        )
        self.assertEqual(self.crm.leads[self.lid]["status"], "converted")
        self.assertEqual(self.crm.log[-1], ("convert", oid, "r1"))

    def test_amount_checked_before_permission(self):
        # r2 is a known user but not the owner: bad amount -> ValueError, not PermissionError
        for bad in [0, -5, 10.5, "100", True]:
            with self.assertRaises(ValueError, msg=repr(bad)):
                self.crm.convert(self.lid, bad, "r2")
        with self.assertRaises(PermissionError):
            self.crm.convert(self.lid, 100, "nobody")  # unknown actor first

    def test_permission_and_status_order(self):
        with self.assertRaises(PermissionError):
            self.crm.convert(self.lid, 100, "r2")
        lid2 = self.crm.add_lead("z@b.com", "Z", "referral", "r2")
        with self.assertRaises(ValueError):
            self.crm.convert(lid2, 100, "r2")  # status still "new"

    def test_queued_lead_needs_owner(self):
        # manager qualifies a queued lead; convert then fails on missing owner
        for email in ["c@d.com", "e@f.com", "g@h.com"]:
            self.crm.add_lead(email, "X", "web", "m1")
        q = self.crm.add_lead("q@h.com", "Q", "referral", "m1")
        self.assertIsNone(self.crm.leads[q]["owner"])
        self.crm.qualify(q, "m1")
        with self.assertRaises(ValueError):
            self.crm.convert(q, 100, "m1")


class TestAdvance(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(users())
        self.lid = self.crm.add_lead("a@b.com", "A", "referral", "r1")
        self.crm.qualify(self.lid, "r1")
        self.oid = self.crm.convert(self.lid, 60000, "r1")  # r1 now full

    def test_stage_chain_and_lost(self):
        self.crm.advance(self.oid, "proposal", "r1")
        self.assertEqual(self.crm.opps[self.oid]["stage"], "proposal")
        self.crm.advance(self.oid, "lost", "r1")  # lost allowed from any non-final
        self.assertEqual(self.crm.opps[self.oid]["stage"], "lost")
        with self.assertRaises(ValueError):
            self.crm.advance(self.oid, "won", "r1")

    def test_invalid_transitions(self):
        with self.assertRaises(ValueError):
            self.crm.advance(self.oid, "negotiation", "r1")  # skips proposal
        with self.assertRaises(ValueError):
            self.crm.advance(self.oid, "prospect", "r1")     # not forward
        with self.assertRaises(ValueError):
            self.crm.advance(self.oid, "bogus", "r1")

    def test_permission(self):
        with self.assertRaises(PermissionError):
            self.crm.advance(self.oid, "proposal", "r2")

    def test_big_negotiation_requires_manager(self):
        self.crm.advance(self.oid, "proposal", "r1")
        with self.assertRaises(PermissionError):
            self.crm.advance(self.oid, "negotiation", "r1")  # 60000 > 50000
        self.crm.advance(self.oid, "negotiation", "m1")
        self.assertEqual(self.crm.opps[self.oid]["stage"], "negotiation")

    def test_unknown_opp_and_log_on_failure(self):
        before = list(self.crm.log)
        with self.assertRaises(ValueError):
            self.crm.advance("O42", "proposal", "r1")
        self.assertEqual(self.crm.log, before)

    def test_won_frees_slot_and_assigns_queue(self):
        # fill r2 (cap 2) so the next leads queue up
        self.crm.add_lead("b@b.com", "B", "web", "m1")
        self.crm.add_lead("c@b.com", "C", "web", "m1")
        q1 = self.crm.add_lead("q1@b.com", "Q1", "web", "m1")
        q2 = self.crm.add_lead("q2@b.com", "Q2", "web", "m1")
        self.assertIsNone(self.crm.leads[q1]["owner"])
        self.assertIsNone(self.crm.leads[q2]["owner"])
        self.crm.advance(self.oid, "proposal", "m1")
        self.crm.advance(self.oid, "negotiation", "m1")
        self.crm.advance(self.oid, "won", "m1")
        self.assertEqual(self.crm.leads[q1]["owner"], "r1")  # oldest first, r1 cap 1
        self.assertIsNone(self.crm.leads[q2]["owner"])
        self.assertEqual(self.crm.log[-2], ("advance", self.oid, "m1"))
        self.assertEqual(self.crm.log[-1], ("assign", q1, "system"))
        # won opportunity does not count as open work; forecast sees it
        self.assertEqual(self.crm.forecast()["won"], 60000)


class TestDiscount(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(users())
        self.lid = self.crm.add_lead("a@b.com", "A", "referral", "r1")
        self.crm.qualify(self.lid, "r1")
        self.oid = self.crm.convert(self.lid, 10000, "r1")

    def test_rep_limited_to_10(self):
        self.crm.discount(self.oid, 10, "r1")
        self.assertEqual(self.crm.opps[self.oid]["amount"], 9000)
        self.assertEqual(self.crm.log[-1], ("discount", self.oid, "r1"))
        with self.assertRaises(PermissionError):
            self.crm.discount(self.oid, 11, "r1")

    def test_manager_cumulative_cap(self):
        self.crm.discount(self.oid, 25, "m1")  # 10000 -> 7500
        self.assertEqual(self.crm.opps[self.oid]["amount"], 7500)
        self.crm.discount(self.oid, 5, "m1")   # 7500 -> 7125, still >= 7000
        self.assertEqual(self.crm.opps[self.oid]["amount"], 7125)
        before = list(self.crm.log)
        with self.assertRaises(ValueError):
            self.crm.discount(self.oid, 5, "m1")  # 6768 < 7000 floor
        self.assertEqual(self.crm.opps[self.oid]["amount"], 7125)
        self.assertEqual(self.crm.log, before)

    def test_pct_validation(self):
        for bad in [0, 31, -1, 10.0, True, "10"]:
            with self.assertRaises(ValueError, msg=repr(bad)):
                self.crm.discount(self.oid, bad, "m1")

    def test_permission_and_final_stage(self):
        with self.assertRaises(PermissionError):
            self.crm.discount(self.oid, 5, "r2")
        self.crm.advance(self.oid, "lost", "r1")
        with self.assertRaises(ValueError):
            self.crm.discount(self.oid, 5, "m1")


class TestTransferAndForecast(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(users())
        self.lid = self.crm.add_lead("a@b.com", "A", "referral", "r1")
        self.crm.qualify(self.lid, "r1")
        self.oid = self.crm.convert(self.lid, 1000, "r1")  # r1 load 1 (full)

    def test_transfer_requires_manager(self):
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.oid, "r2", "r1")

    def test_transfer_validation(self):
        with self.assertRaises(ValueError):
            self.crm.transfer(self.oid, "m1", "m1")     # not a rep
        with self.assertRaises(ValueError):
            self.crm.transfer(self.oid, "ghost", "m1")  # unknown user
        with self.assertRaises(ValueError):
            self.crm.transfer(self.oid, "r1", "m1")     # same owner

    def test_transfer_capacity_check(self):
        self.crm.add_lead("b@c.com", "B", "referral", "m1")  # -> r2
        self.crm.add_lead("d@e.com", "D", "referral", "m1")  # -> r2 (now full)
        self.assertEqual(self.crm._load("r2"), 2)
        with self.assertRaises(ValueError):
            self.crm.transfer(self.oid, "r2", "m1")

    def test_transfer_moves_owner(self):
        # r2 has room (load 0) while r1 is full with the open opp
        self.crm.transfer(self.oid, "r2", "m1")
        self.assertEqual(self.crm.opps[self.oid]["owner"], "r2")
        self.assertEqual(self.crm.log[-1], ("transfer", self.oid, "m1"))
        self.assertEqual(self.crm._load("r1"), 0)
        self.assertEqual(self.crm._load("r2"), 1)

    def test_forecast(self):
        lid2 = self.crm.add_lead("b@c.com", "B", "referral", "m1")  # -> r2
        self.crm.qualify(lid2, "r2")
        oid2 = self.crm.convert(lid2, 20000, "r2")  # r2 owns O2
        self.crm.advance(self.oid, "proposal", "r1")
        self.crm.advance(oid2, "proposal", "r2")
        self.crm.advance(oid2, "negotiation", "r2")  # 20000 <= 50000: rep ok
        self.crm.discount(oid2, 30, "m1")            # 20000 -> 14000 (cumulative cap ok)
        self.crm.advance(self.oid, "lost", "r1")
        self.assertEqual(self.crm.forecast(), {"open": 1, "weighted": 8400, "won": 0})
        self.crm.advance(oid2, "won", "r2")
        self.assertEqual(self.crm.forecast(), {"open": 0, "weighted": 0, "won": 14000})
        self.assertEqual(self.crm.log[-1], ("advance", oid2, "r2"))  # no queue to fill


if __name__ == "__main__":
    unittest.main()
