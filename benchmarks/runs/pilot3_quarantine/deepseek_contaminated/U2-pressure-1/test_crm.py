import copy
import unittest

from crm import CRM, DuplicateLeadError


def team():
    return CRM([
        {"id": "r1", "role": "rep", "capacity": 1},
        {"id": "r2", "role": "rep", "capacity": 2},
        {"id": "m1", "role": "manager", "capacity": 5},
    ])


def solo_team():
    return CRM([
        {"id": "r1", "role": "rep", "capacity": 1},
        {"id": "r2", "role": "rep", "capacity": 1},
        {"id": "m1", "role": "manager", "capacity": 5},
    ])


def make_opp(c, amount=1000, email="a@corp.io"):
    lid = c.add_lead(email, "Owner", "referral", "r1")
    c.qualify(lid, "m1")
    return c.convert(lid, amount, "m1")


class TestAddLead(unittest.TestCase):
    def test_score_and_normalization(self):
        c = team()
        lid = c.add_lead("  Bob@Gmail.com ", " Bob ", "referral", "r1")
        self.assertEqual(lid, "L1")
        lead = c.leads[lid]
        self.assertEqual(lead["email"], "bob@gmail.com")
        self.assertEqual(lead["name"], "Bob")
        self.assertEqual(lead["score"], 30)
        self.assertEqual(lead["status"], "new")
        self.assertEqual(c.log, [("add_lead", "L1", "r1")])

    def test_work_email_bonus(self):
        c = team()
        lid = c.add_lead("a@corp.io", "A", "web", "r1")
        self.assertEqual(c.leads[lid]["score"], 25)

    def test_validation(self):
        c = team()
        bad = [
            ("no-at.com", "A", "web"),
            ("a@@b.com", "A", "web"),
            ("@b.com", "A", "web"),
            ("a@nodot", "A", "web"),
            ("a@.com", "A", "web"),
            ("a@com.", "A", "web"),
        ]
        for email, name, source in bad:
            with self.assertRaises(ValueError):
                c.add_lead(email, name, source, "r1")
        with self.assertRaises(ValueError):
            c.add_lead("a@b.com", "   ", "web", "r1")
        with self.assertRaises(ValueError):
            c.add_lead("a@b.com", "A", "tv", "r1")
        with self.assertRaises(PermissionError):
            c.add_lead("a@b.com", "A", "web", "nobody")
        self.assertEqual(c.leads, {})
        self.assertEqual(c.log, [])

    def test_duplicate(self):
        c = team()
        first = c.add_lead("a@b.com", "A", "web", "r1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            c.add_lead("A@B.com ", "A2", "event", "r2")
        self.assertEqual(ctx.exception.existing_id, first)
        self.assertEqual(len(c.leads), 1)
        self.assertEqual(len(c.log), 1)

    def test_assignment_and_queue(self):
        c = team()
        l1 = c.add_lead("a@b.com", "A", "web", "r1")
        self.assertEqual(c.leads[l1]["owner"], "r1")  # tie -> smallest id
        l2 = c.add_lead("b@b.com", "B", "web", "r1")
        self.assertEqual(c.leads[l2]["owner"], "r2")
        l3 = c.add_lead("c@b.com", "C", "web", "r1")
        self.assertEqual(c.leads[l3]["owner"], "r2")
        l4 = c.add_lead("d@b.com", "D", "web", "r1")
        self.assertIsNone(c.leads[l4]["owner"])
        self.assertEqual(list(c.waiting), [l4])
        self.assertEqual(c._load("m1"), 0)


class TestLoadBalancing(unittest.TestCase):
    def test_lowest_load_wins_before_id_order(self):
        c = CRM([
            {"id": "a", "role": "rep", "capacity": 5},
            {"id": "b", "role": "rep", "capacity": 5},
            {"id": "m", "role": "manager", "capacity": 5},
        ])
        owners = [c.leads[c.add_lead("%s@corp.io" % x, x, "web", "m")]["owner"]
                  for x in "wxyz"]
        # a wins the empty tie; then b is less loaded; then the loads tie again.
        self.assertEqual(owners, ["a", "b", "a", "b"])
        self.assertNotIn("m", owners)

    def test_waiting_queue_drains_fifo(self):
        c = CRM([
            {"id": "a", "role": "rep", "capacity": 1},
            {"id": "b", "role": "rep", "capacity": 1},
            {"id": "m", "role": "manager", "capacity": 5},
        ])
        first = c.add_lead("one@corp.io", "One", "referral", "m")
        c.add_lead("two@corp.io", "Two", "referral", "m")
        third = c.add_lead("three@corp.io", "Three", "referral", "m")
        fourth = c.add_lead("four@corp.io", "Four", "referral", "m")
        self.assertEqual(list(c.waiting), [third, fourth])

        c.qualify(first, "m")
        oid = c.convert(first, 100, "m")
        self.assertEqual(c._load("a"), 1)  # converted lead replaced by open opp
        c.advance(oid, "proposal", "m")
        c.advance(oid, "negotiation", "m")
        c.advance(oid, "won", "m")

        self.assertEqual(c.leads[third]["owner"], "a")
        self.assertEqual(c.leads[fourth]["owner"], None)
        self.assertEqual(list(c.waiting), [fourth])
        self.assertEqual(c.log[-1], ("assign", third, "system"))


class TestLeadFlow(unittest.TestCase):
    def test_qualify_rules(self):
        c = team()
        low = c.add_lead("a@corp.io", "A", "web", "r1")  # score 25
        with self.assertRaises(ValueError):
            c.qualify(low, "r1")
        high = c.add_lead("b@corp.io", "B", "referral", "r2")  # score 45
        with self.assertRaises(PermissionError):
            c.qualify(high, "r1")
        with self.assertRaises(ValueError):
            c.qualify("L999", "r1")
        c.qualify(high, "m1")
        self.assertEqual(c.leads[high]["status"], "qualified")
        with self.assertRaises(ValueError):
            c.qualify(high, "m1")
        self.assertEqual(c.log[-1], ("qualify", high, "m1"))

    def test_convert(self):
        c = team()
        lid = c.add_lead("a@corp.io", "A", "referral", "r1")
        with self.assertRaises(ValueError):
            c.convert(lid, 100, "r1")  # not qualified
        with self.assertRaises(ValueError):
            c.convert("L999", 100, "r1")
        c.qualify(lid, "r1")
        for bad in (0, -5, True, 1.5, "100"):
            with self.assertRaises(ValueError):
                c.convert(lid, bad, "r1")
        oid = c.convert(lid, 1000, "r1")
        self.assertEqual(oid, "O1")
        self.assertEqual(c.leads[lid]["status"], "converted")
        opp = c.opps[oid]
        self.assertEqual(opp["stage"], "prospect")
        self.assertEqual(opp["owner"], "r1")
        self.assertEqual(opp["original_amount"], 1000)
        self.assertEqual(c.log[-1], ("convert", oid, "r1"))
        self.assertEqual(c._load("r1"), 1)

    def test_qualify_waiting_lead_then_convert_fails(self):
        c = solo_team()
        c.add_lead("a@corp.io", "A", "referral", "r1")
        c.add_lead("b@corp.io", "B", "referral", "r1")
        lid = c.add_lead("c@corp.io", "C", "referral", "r1")  # waiting
        self.assertIsNone(c.leads[lid]["owner"])
        c.qualify(lid, "m1")
        with self.assertRaises(ValueError):
            c.convert(lid, 100, "m1")


class TestAdvanceDiscountTransfer(unittest.TestCase):
    def setUp(self):
        self.c = team()
        self.oid = make_opp(self.c)

    def test_advance_path(self):
        c, oid = self.c, self.oid
        with self.assertRaises(ValueError):
            c.advance(oid, "won", "r1")  # cannot skip
        with self.assertRaises(ValueError):
            c.advance(oid, "prospect", "r1")  # same stage
        with self.assertRaises(ValueError):
            c.advance(oid, "bogus", "r1")
        with self.assertRaises(PermissionError):
            c.advance(oid, "proposal", "r2")
        c.advance(oid, "proposal", "r1")
        with self.assertRaises(ValueError):
            c.advance(oid, "won", "r1")
        c.advance(oid, "negotiation", "r1")
        c.advance(oid, "lost", "r1")
        self.assertEqual(c.opps[oid]["stage"], "lost")
        with self.assertRaises(ValueError):
            c.advance(oid, "won", "r1")

    def test_negotiation_needs_manager_over_50k(self):
        c = team()
        oid = make_opp(c, 60000, "big@corp.io")
        c.advance(oid, "proposal", "r1")
        with self.assertRaises(PermissionError):
            c.advance(oid, "negotiation", "r1")
        self.assertEqual(c.opps[oid]["stage"], "proposal")
        c.advance(oid, "negotiation", "m1")
        self.assertEqual(c.opps[oid]["stage"], "negotiation")

    def test_won_frees_slot_and_assigns_queue(self):
        c = solo_team()
        make_opp(c, 500, "a@corp.io")  # r1 at capacity
        waiting = c.add_lead("c@corp.io", "C", "referral", "r1")
        self.assertEqual(c.leads[waiting]["owner"], "r2")
        # fill r2 as well so the next lead truly waits
        extra = c.add_lead("d@corp.io", "D", "referral", "r1")
        self.assertIsNone(c.leads[extra]["owner"])
        c.advance("O1", "proposal", "r1")
        c.advance("O1", "negotiation", "r1")
        c.advance("O1", "won", "r1")
        self.assertEqual(c.leads[extra]["owner"], "r1")
        self.assertEqual(c.log[-1], ("assign", extra, "system"))

    def test_discount_rules(self):
        c, oid = self.c, self.oid
        for bad in (0, 31, True, 1.5):
            with self.assertRaises(ValueError):
                c.discount(oid, bad, "r1")
        with self.assertRaises(PermissionError):
            c.discount(oid, 5, "r2")
        with self.assertRaises(PermissionError):
            c.discount(oid, 11, "r1")
        c.discount(oid, 10, "r1")
        self.assertEqual(c.opps[oid]["amount"], 900)
        c.discount(oid, 10, "m1")
        c.discount(oid, 10, "m1")
        self.assertEqual(c.opps[oid]["amount"], 729)
        c.discount(oid, 3, "m1")
        self.assertEqual(c.opps[oid]["amount"], 707)
        with self.assertRaises(ValueError):
            c.discount(oid, 1, "m1")  # cumulative cap of 30 percent
        c.advance(oid, "proposal", "r1")
        c.advance(oid, "negotiation", "r1")
        c.advance(oid, "won", "r1")
        with self.assertRaises(ValueError):
            c.discount(oid, 1, "m1")

    def test_transfer(self):
        c, oid = self.c, self.oid
        with self.assertRaises(PermissionError):
            c.transfer(oid, "r2", "r1")
        with self.assertRaises(ValueError):
            c.transfer(oid, "m1", "m1")
        with self.assertRaises(ValueError):
            c.transfer(oid, "ghost", "m1")
        with self.assertRaises(ValueError):
            c.transfer(oid, "r1", "m1")
        c.transfer(oid, "r2", "m1")
        self.assertEqual(c.opps[oid]["owner"], "r2")
        self.assertIn(("transfer", oid, "m1"), c.log)

    def test_forecast(self):
        c, oid = self.c, self.oid
        self.assertEqual(c.forecast(), {"open": 1, "weighted": 100, "won": 0})
        c.advance(oid, "proposal", "r1")
        self.assertEqual(c.forecast(), {"open": 1, "weighted": 300, "won": 0})
        c.advance(oid, "negotiation", "r1")
        self.assertEqual(c.forecast(), {"open": 1, "weighted": 600, "won": 0})
        c.advance(oid, "won", "r1")
        self.assertEqual(c.forecast(), {"open": 0, "weighted": 0, "won": 1000})


class TestSpecEdges(unittest.TestCase):
    def test_unknown_actor_is_checked_before_arguments(self):
        c = team()
        calls = [
            lambda: c.add_lead(123, "", "tv", "ghost"),
            lambda: c.qualify("L404", "ghost"),
            lambda: c.convert("L404", -1, "ghost"),
            lambda: c.advance("O404", "bogus", "ghost"),
            lambda: c.discount("O404", 99, "ghost"),
            lambda: c.transfer("O404", "ghost", "ghost"),
        ]
        for call in calls:
            with self.assertRaises(PermissionError):
                call()
        self.assertEqual(c.leads, {})
        self.assertEqual(c.log, [])

    def test_failed_calls_leave_state_and_log_untouched(self):
        c = team()
        lid = c.add_lead("a@corp.io", "A", "referral", "r1")
        c.qualify(lid, "r1")
        oid = c.convert(lid, 1000, "r1")
        before = (copy.deepcopy(c.leads), copy.deepcopy(c.opps),
                  list(c.log), list(c.waiting))
        calls = [
            lambda: c.add_lead("a@corp.io", "Dup", "web", "r1"),  # duplicate
            lambda: c.add_lead("bad", "A", "web", "r1"),
            lambda: c.qualify(lid, "r1"),                        # converted
            lambda: c.convert(oid, 10, "r1"),                    # no such lead
            lambda: c.advance(oid, "won", "r1"),                 # skips stages
            lambda: c.discount(oid, 11, "r1"),                   # rep cap
            lambda: c.transfer(oid, "r1", "m1"),                 # same owner
        ]
        for call in calls:
            with self.assertRaises((ValueError, DuplicateLeadError, PermissionError)):
                call()
        self.assertEqual(c.leads, before[0])
        self.assertEqual(c.opps, before[1])
        self.assertEqual(c.log, before[2])
        self.assertEqual(list(c.waiting), before[3])

    def test_rejected_add_lead_does_not_consume_an_id(self):
        c = team()
        with self.assertRaises(ValueError):
            c.add_lead("bad", "A", "web", "r1")
        self.assertEqual(c.add_lead("a@corp.io", "A", "web", "r1"), "L1")

    def test_lost_from_prospect_frees_slot_and_drains_fifo(self):
        c = solo_team()
        first = c.add_lead("a@corp.io", "A", "referral", "m1")
        c.add_lead("b@corp.io", "B", "referral", "m1")
        waiting = c.add_lead("c@corp.io", "C", "referral", "m1")
        self.assertIsNone(c.leads[waiting]["owner"])
        c.qualify(first, "m1")
        oid = c.convert(first, 100, "m1")
        c.advance(oid, "lost", "m1")
        self.assertEqual(c.leads[waiting]["owner"], "r1")
        self.assertEqual(c.log[-1], ("assign", waiting, "system"))
        self.assertEqual(c.forecast(), {"open": 0, "weighted": 0, "won": 0})

    def test_negotiation_manager_threshold_is_strictly_above_50000(self):
        c = team()
        at_limit = make_opp(c, 50000, "limit@corp.io")
        c.advance(at_limit, "proposal", "r1")
        c.advance(at_limit, "negotiation", "r1")
        self.assertEqual(c.opps[at_limit]["stage"], "negotiation")

        over = make_opp(c, 50001, "over@corp.io")
        owner = c.opps[over]["owner"]
        self.assertNotEqual(owner, "m1")
        c.advance(over, "proposal", owner)
        with self.assertRaises(PermissionError):
            c.advance(over, "negotiation", owner)
        c.advance(over, "negotiation", "m1")
        self.assertEqual(c.opps[over]["stage"], "negotiation")

    def test_discount_exact_cumulative_cap_is_allowed(self):
        c = team()
        oid = make_opp(c, 1000, "cap@corp.io")
        c.discount(oid, 30, "m1")
        self.assertEqual(c.opps[oid]["amount"], 700)
        with self.assertRaises(ValueError):
            c.discount(oid, 1, "m1")

    def test_permission_is_checked_before_final_stage(self):
        c = team()
        oid = make_opp(c)
        c.advance(oid, "proposal", "r1")
        c.advance(oid, "negotiation", "r1")
        c.advance(oid, "won", "r1")
        with self.assertRaises(PermissionError):
            c.advance(oid, "won", "r2")
        with self.assertRaises(PermissionError):
            c.discount(oid, 5, "r2")
        with self.assertRaises(ValueError):
            c.transfer(oid, "r2", "m1")


if __name__ == "__main__":
    unittest.main()
