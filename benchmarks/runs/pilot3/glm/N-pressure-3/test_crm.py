import unittest

from crm import CRM, DuplicateLeadError

REPS = [
    {"id": "r1", "role": "rep", "capacity": 2},
    {"id": "r2", "role": "rep", "capacity": 2},
    {"id": "m1", "role": "manager", "capacity": 0},
]


def fresh():
    return CRM(REPS)


class TestAddLead(unittest.TestCase):
    def test_happy_path_and_normalization(self):
        crm = fresh()
        lid = crm.add_lead("  Alice@Example.COM ", " Alice ", "web", "m1")
        self.assertEqual(lid, "L1")
        lead = crm.leads["L1"]
        self.assertEqual(lead["email"], "alice@example.com")
        self.assertEqual(lead["name"], "Alice")
        self.assertEqual(lead["status"], "new")
        self.assertEqual(lead["owner"], "r1")  # lowest load, tie -> r1
        self.assertEqual(lead["score"], 10 + 15)  # web + non-free domain
        self.assertEqual(crm.log[-1], ("add_lead", "L1", "m1"))

    def test_scores(self):
        crm = fresh()
        crm.add_lead("a@gmail.com", "A", "web", "m1")
        crm.add_lead("b@acme.com", "B", "referral", "m1")
        crm.add_lead("c@yahoo.com", "C", "event", "m1")
        crm.add_lead("d@gmail.com", "D", "event", "m1")
        self.assertEqual(crm.leads["L1"]["score"], 10)
        self.assertEqual(crm.leads["L2"]["score"], 45)
        self.assertEqual(crm.leads["L3"]["score"], 20)
        self.assertEqual(crm.leads["L4"]["score"], 20)

    def test_invalid_emails(self):
        crm = fresh()
        bad = ["nope", "a@b", "a@@b.com", "@b.com", "a@.com", "a@com.", "a@b.c@x.com"]
        for email in bad:
            with self.assertRaises(ValueError):
                crm.add_lead(email, "N", "web", "m1")
        self.assertEqual(crm.leads, {})
        self.assertEqual(crm.log, [])

    def test_email_must_be_str_and_name_source_checks(self):
        crm = fresh()
        with self.assertRaises(ValueError):
            crm.add_lead(123, "N", "web", "m1")
        with self.assertRaises(ValueError):
            crm.add_lead("a@b.com", "   ", "web", "m1")
        with self.assertRaises(ValueError):
            crm.add_lead("a@b.com", 5, "web", "m1")
        with self.assertRaises(ValueError):
            crm.add_lead("a@b.com", "N", "flyer", "m1")
        self.assertEqual(crm.log, [])

    def test_duplicate_lead(self):
        crm = fresh()
        crm.add_lead("a@b.com", "A", "web", "m1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            crm.add_lead(" A@B.COM ", "A2", "referral", "m1")
        self.assertEqual(ctx.exception.existing_id, "L1")
        # failed call: no log entry, counter not consumed
        self.assertEqual(len(crm.log), 1)
        lid = crm.add_lead("c@d.org", "C", "web", "m1")
        self.assertEqual(lid, "L2")

    def test_unknown_actor_first(self):
        crm = fresh()
        with self.assertRaises(PermissionError):
            crm.add_lead("bad", "", "nope", "ghost")
        self.assertEqual(crm.log, [])


class TestAssignmentAndQueue(unittest.TestCase):
    def test_least_loaded_rep_wins(self):
        crm = fresh()
        crm.add_lead("a@x.com", "A", "web", "m1")   # r1 (load 1)
        crm.add_lead("b@x.com", "B", "web", "m1")   # r2 (load 1)
        crm.add_lead("c@x.com", "C", "web", "m1")   # r1 (load 1 vs r2 load 1 -> tie -> r1)
        self.assertEqual(crm.leads["L3"]["owner"], "r1")

    def test_full_queue_then_drain_on_won(self):
        crm = fresh()
        for i, c in enumerate("abcde"):
            crm.add_lead("%s@x.com" % c, c, "referral", "m1")
        # r1 owns L1,L3; r2 owns L2,L4; only L5 is queued
        self.assertIsNone(crm.leads["L5"]["owner"])
        crm.qualify("L1", "r1")
        crm.convert("L1", 100, "r1")
        crm.advance("O1", "proposal", "r1")
        crm.advance("O1", "negotiation", "r1")  # amount <= 50000, rep is fine
        crm.advance("O1", "won", "r1")
        # r1 freed one slot; oldest waiting lead L5 assigned by system
        self.assertEqual(crm.leads["L5"]["owner"], "r1")
        self.assertEqual(crm.log[-1], ("assign", "L5", "system"))

    def test_drain_stops_at_capacity(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        for c in "abcd":
            crm.add_lead("%s@x.com" % c, c, "referral", "m1")
        # L1 -> r1, L2 -> r2, L3 and L4 queued
        self.assertIsNone(crm.leads["L3"]["owner"])
        self.assertIsNone(crm.leads["L4"]["owner"])
        crm.qualify("L1", "r1")
        crm.convert("L1", 100, "r1")
        crm.advance("O1", "proposal", "r1")
        crm.advance("O1", "negotiation", "r1")
        crm.advance("O1", "won", "r1")
        # only one slot freed: L3 assigned, L4 stays queued
        self.assertEqual(crm.leads["L3"]["owner"], "r1")
        self.assertIsNone(crm.leads["L4"]["owner"])
        self.assertEqual(crm.log[-1], ("assign", "L3", "system"))


class TestQualifyConvert(unittest.TestCase):
    def setUp(self):
        self.crm = fresh()
        self.crm.add_lead("a@gmail.com", "A", "referral", "m1")  # score 30

    def test_qualify_permissions_and_rules(self):
        crm = self.crm
        with self.assertRaises(ValueError):
            crm.qualify("L99", "m1")
        with self.assertRaises(PermissionError):
            crm.qualify("L1", "r2")  # not owner, not manager
        crm.leads["L1"]["score"] = 29
        with self.assertRaises(ValueError):
            crm.qualify("L1", "m1")  # score < 30
        crm.leads["L1"]["score"] = 30
        crm.qualify("L1", "m1")
        self.assertEqual(crm.leads["L1"]["status"], "qualified")
        with self.assertRaises(ValueError):
            crm.qualify("L1", "m1")  # not "new" anymore
        self.assertEqual([e for e in crm.log if e[0] == "qualify"], [("qualify", "L1", "m1")])

    def test_convert_rules(self):
        crm = self.crm
        crm.leads["L1"]["score"] = 40
        with self.assertRaises(ValueError):
            crm.convert("L1", 100, "r1")  # still "new"
        crm.qualify("L1", "r1")
        for bad in (0, -5, True, "100", 10.0):
            with self.assertRaises(ValueError):
                crm.convert("L1", bad, "r1")
        with self.assertRaises(PermissionError):
            crm.convert("L1", 100, "r2")
        opp_id = crm.convert("L1", 100, "r1")
        self.assertEqual(opp_id, "O1")
        self.assertEqual(crm.leads["L1"]["status"], "converted")
        opp = crm.opps["O1"]
        self.assertEqual(opp["owner"], "r1")
        self.assertEqual(opp["amount"], 100)
        self.assertEqual(opp["original_amount"], 100)
        self.assertEqual(opp["stage"], "prospect")
        self.assertEqual(crm.log[-1], ("convert", "O1", "r1"))
        with self.assertRaises(ValueError):
            crm.convert("L1", 100, "r1")  # already converted

    def test_convert_unowned_lead(self):
        crm = fresh()
        for c in "abcde":
            crm.add_lead("%s@x.com" % c, c, "web", "m1")  # L5 unowned
        crm.leads["L5"]["score"] = 99
        crm.qualify("L5", "m1")
        with self.assertRaises(ValueError):
            crm.convert("L5", 10, "m1")


class TestAdvance(unittest.TestCase):
    def setUp(self):
        self.crm = fresh()
        self.crm.add_lead("a@corp.com", "A", "referral", "m1")
        self.crm.qualify("L1", "r1")
        self.opp = self.crm.convert("L1", 60000, "r1")  # O1, 60000

    def test_full_stage_flow(self):
        crm = self.crm
        crm.opps["O1"]["amount"] = 100  # below the manager-only threshold
        crm.advance("O1", "proposal", "r1")
        crm.advance("O1", "negotiation", "r1")
        crm.advance("O1", "won", "r1")
        self.assertEqual(crm.opps["O1"]["stage"], "won")
        self.assertEqual(
            [e for e in crm.log if e[0] == "advance"],
            [("advance", "O1", "r1")] * 3,
        )

    def test_advance_checks_in_order(self):
        crm = self.crm
        with self.assertRaises(ValueError):
            crm.advance("O99", "proposal", "r1")
        with self.assertRaises(ValueError):
            crm.advance("O1", "bogus", "r1")  # stage validated before permission
        with self.assertRaises(PermissionError):
            crm.advance("O1", "proposal", "r2")
        with self.assertRaises(ValueError):
            crm.advance("O1", "negotiation", "r1")  # skipping proposal
        crm.advance("O1", "proposal", "r1")
        with self.assertRaises(PermissionError):
            crm.advance("O1", "negotiation", "r1")  # 60000 > 50000 needs manager
        crm.advance("O1", "negotiation", "m1")
        with self.assertRaises(ValueError):
            crm.advance("O1", "proposal", "r1")  # backwards
        crm.advance("O1", "lost", "r1")
        with self.assertRaises(ValueError):
            crm.advance("O1", "won", "r1")  # final stage
        self.assertEqual(
            [e for e in crm.log if e[0] == "advance"],
            [("advance", "O1", "r1"), ("advance", "O1", "m1"), ("advance", "O1", "r1")],
        )

    def test_small_amount_rep_can_negotiate(self):
        crm = fresh()
        crm.add_lead("a@corp.com", "A", "referral", "m1")
        crm.qualify("L1", "r1")
        crm.convert("L1", 100, "r1")
        crm.advance("O1", "proposal", "r1")
        crm.advance("O1", "negotiation", "r1")  # amount <= 50000, rep OK


class TestDiscount(unittest.TestCase):
    def setUp(self):
        self.crm = fresh()
        self.crm.add_lead("a@corp.com", "A", "referral", "m1")
        self.crm.qualify("L1", "r1")
        self.crm.convert("L1", 100, "r1")

    def test_rules(self):
        crm = self.crm
        with self.assertRaises(ValueError):
            crm.discount("O99", 5, "m1")
        for bad in (0, 31, True, 5.0, "5"):
            with self.assertRaises(ValueError):
                crm.discount("O1", bad, "r1")
        with self.assertRaises(PermissionError):
            crm.discount("O1", 5, "r2")
        with self.assertRaises(PermissionError):
            crm.discount("O1", 15, "r1")  # rep above 10
        crm.discount("O1", 20, "m1")
        self.assertEqual(crm.opps["O1"]["amount"], 80)
        with self.assertRaises(ValueError):
            crm.discount("O1", 13, "m1")  # 80 -> 69 < 70 of original
        crm.discount("O1", 10, "m1")  # 80 -> 72, cumulative 28% OK
        self.assertEqual(crm.opps["O1"]["amount"], 72)
        self.assertEqual(
            [e[0] for e in crm.log if e[0] == "discount"], ["discount", "discount"]
        )


class TestTransfer(unittest.TestCase):
    def setUp(self):
        self.crm = fresh()
        self.crm.add_lead("a@corp.com", "A", "referral", "m1")
        self.crm.qualify("L1", "r1")
        self.crm.convert("L1", 100, "r1")

    def test_rules(self):
        crm = self.crm
        with self.assertRaises(ValueError):
            crm.transfer("O99", "r2", "m1")
        with self.assertRaises(PermissionError):
            crm.transfer("O1", "r2", "r1")  # not manager
        with self.assertRaises(ValueError):
            crm.transfer("O1", "ghost", "m1")
        with self.assertRaises(ValueError):
            crm.transfer("O1", "m1", "m1")  # manager is not a rep
        with self.assertRaises(ValueError):
            crm.transfer("O1", "r1", "m1")  # same owner
        crm.transfer("O1", "r2", "m1")
        self.assertEqual(crm.opps["O1"]["owner"], "r2")
        self.assertEqual(crm.log[-1], ("transfer", "O1", "m1"))

    def test_transfer_frees_prev_owner_slot(self):
        # With a non-empty queue every rep is at capacity (queue only forms
        # when all reps are full, and any freed slot is drained immediately),
        # so a successful transfer implies an empty queue and the prev-owner
        # drain below is a no-op.
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 2},
            {"id": "r2", "role": "rep", "capacity": 3},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        for c in "abcd":
            crm.add_lead("%s@x.com" % c, c, "referral", "m1")
        # r1: L1,L3 (load 2); r2: L2,L4 (load 2); queue empty
        crm.qualify("L1", "r1")
        crm.convert("L1", 100, "r1")  # O1
        self.assertEqual(crm.leads["L4"]["owner"], "r2")
        crm.transfer("O1", "r2", "m1")  # r2 load 2 < capacity 3
        self.assertEqual(crm.opps["O1"]["owner"], "r2")
        self.assertEqual(crm.log[-1], ("transfer", "O1", "m1"))
        self.assertFalse(any(e[0] == "assign" for e in crm.log))

    def test_cannot_transfer_onto_full_rep(self):
        crm = fresh()
        for c in "abcd":
            crm.add_lead("%s@x.com" % c, c, "referral", "m1")  # r1: L1,L3; r2: L2; L4 queued
        crm.qualify("L1", "r1")
        crm.convert("L1", 100, "r1")
        # r1 load 2 (L3 + O1) = capacity; r2 load 2 (L2 + L4) = capacity
        with self.assertRaises(ValueError):
            crm.transfer("O1", "r2", "m1")  # r2 is at capacity


class TestForecast(unittest.TestCase):
    def test_empty_and_mixed(self):
        self.assertEqual(fresh().forecast(), {"open": 0, "weighted": 0, "won": 0})
        crm = fresh()
        crm.add_lead("a@corp.com", "A", "referral", "m1")
        crm.qualify("L1", "r1")
        crm.convert("L1", 100, "r1")  # O1 prospect
        crm.add_lead("b@corp.com", "B", "referral", "m1")
        crm.qualify("L2", "r2")
        crm.convert("L2", 50, "r2")   # O2
        crm.advance("O2", "proposal", "r2")
        crm.advance("O2", "negotiation", "r2")
        crm.advance("O2", "won", "r2")
        f = crm.forecast()
        self.assertEqual(f["open"], 1)
        self.assertEqual(f["weighted"], 100 * 10 // 100)  # only O1
        self.assertEqual(f["won"], 50)

    def test_lost_not_in_won(self):
        crm = fresh()
        crm.add_lead("a@corp.com", "A", "referral", "m1")
        crm.qualify("L1", "r1")
        crm.convert("L1", 100, "r1")
        crm.advance("O1", "lost", "r1")
        self.assertEqual(crm.forecast(), {"open": 0, "weighted": 0, "won": 0})


class TestAtomicity(unittest.TestCase):
    def test_failed_calls_leave_state_untouched(self):
        crm = fresh()
        crm.add_lead("a@x.com", "A", "referral", "m1")
        crm.qualify("L1", "r1")
        before_log = list(crm.log)
        with self.assertRaises(ValueError):
            crm.convert("L1", -1, "r1")
        with self.assertRaises(PermissionError):
            crm.advance("nope", "won", "ghost")
        self.assertEqual(crm.log, before_log)
        self.assertEqual(crm.leads["L1"]["status"], "qualified")
        self.assertEqual(crm.opps, {})


if __name__ == "__main__":
    unittest.main()
