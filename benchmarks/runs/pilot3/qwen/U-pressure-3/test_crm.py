import unittest

from crm import CRM, DuplicateLeadError


def make_crm():
    return CRM([
        {"id": "ana", "role": "rep", "capacity": 1},
        {"id": "bob", "role": "rep", "capacity": 1},
        {"id": "max", "role": "manager", "capacity": 0},
    ])


class TestAddLead(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()

    def test_unknown_actor_checked_first(self):
        # Bad actor + bad email: PermissionError wins over ValueError.
        with self.assertRaises(PermissionError):
            self.crm.add_lead("not-an-email", "", "web", "ghost")
        self.assertEqual(self.crm.log, [])
        self.assertEqual(self.crm.leads, {})

    def test_successful_creation_fields(self):
        lead_id = self.crm.add_lead("  Alice@Acme.COM ", "  Alice  ", "referral", "max")
        self.assertEqual(lead_id, "L1")
        lead = self.crm.leads[lead_id]
        self.assertEqual(lead["email"], "alice@acme.com")
        self.assertEqual(lead["name"], "Alice")
        self.assertEqual(lead["source"], "referral")
        self.assertEqual(lead["score"], 45)  # 30 referral + 15 corporate domain
        self.assertEqual(lead["status"], "new")
        self.assertEqual(lead["owner"], "ana")  # both reps idle, "ana" < "bob"
        self.assertEqual(self.crm.log, [("add_lead", "L1", "max")])

    def test_scores_by_source_and_domain(self):
        self.assertEqual(self.crm.add_lead("a@gmail.com", "A", "web", "max"), "L1")
        self.assertEqual(self.crm.leads["L1"]["score"], 10)
        self.crm.add_lead("b@outlook.com", "B", "referral", "max")
        self.assertEqual(self.crm.leads["L2"]["score"], 30)
        self.crm.add_lead("c@yahoo.com", "C", "event", "max")
        self.assertEqual(self.crm.leads["L3"]["score"], 20)

    def test_email_validation(self):
        for bad in ["noatsign", "@acme.com", "a@b@acme.com", "a@.com", "a@com",
                    "a@acme.", 123]:
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    self.crm.add_lead(bad, "N", "web", "max")

    def test_name_and_source_validation(self):
        with self.assertRaises(ValueError):
            self.crm.add_lead("a@b.co", "   ", "web", "max")
        with self.assertRaises(ValueError):
            self.crm.add_lead("a@b.co", 5, "web", "max")
        with self.assertRaises(ValueError):
            self.crm.add_lead("a@b.co", "N", "tv", "max")

    def test_duplicate_email(self):
        self.crm.add_lead("a@acme.com", "A", "web", "max")
        with self.assertRaises(DuplicateLeadError) as ctx:
            self.crm.add_lead("  A@ACME.com ", "A2", "web", "max")
        self.assertEqual(ctx.exception.existing_id, "L1")
        self.assertEqual(len(self.crm.leads), 1)
        self.assertEqual(self.crm.log, [("add_lead", "L1", "max")])

    def test_waiting_queue_when_full(self):
        self.crm.add_lead("a@acme.com", "A", "web", "max")   # ana
        self.crm.add_lead("b@acme.com", "B", "web", "max")   # bob
        lid = self.crm.add_lead("c@acme.com", "C", "web", "max")  # none left
        self.assertIsNone(self.crm.leads[lid]["owner"])
        self.assertEqual(lid, "L3")

    def test_failed_calls_do_not_advance_counter(self):
        with self.assertRaises(ValueError):
            self.crm.add_lead("bad", "N", "web", "max")
        self.assertEqual(self.crm.add_lead("a@b.co", "A", "web", "max"), "L1")


class TestQualifyAndConvert(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        self.lid = self.crm.add_lead("a@acme.com", "A", "referral", "ana")  # score 45

    def test_qualify_permissions_and_order(self):
        with self.assertRaises(PermissionError):
            self.crm.qualify(self.lid, "bob")
        with self.assertRaises(ValueError):
            self.crm.qualify("L99", "ana")
        self.crm.qualify(self.lid, "ana")
        self.assertEqual(self.crm.leads[self.lid]["status"], "qualified")
        with self.assertRaises(ValueError):  # already qualified
            self.crm.qualify(self.lid, "ana")
        self.assertEqual(self.crm.log, [("add_lead", self.lid, "ana"),
                                        ("qualify", self.lid, "ana")])

    def test_qualify_low_score(self):
        # ana already owns the setUp lead, so this one lands on bob.
        lid = self.crm.add_lead("w@gmail.com", "W", "web", "max")  # score 10
        self.assertEqual(self.crm.leads[lid]["owner"], "bob")
        with self.assertRaises(ValueError):
            self.crm.qualify(lid, "bob")

    def test_manager_can_qualify(self):
        self.crm.qualify(self.lid, "max")
        self.assertEqual(self.crm.leads[self.lid]["status"], "qualified")

    def test_convert(self):
        self.crm.qualify(self.lid, "ana")
        oid = self.crm.convert(self.lid, 1000, "ana")
        self.assertEqual(oid, "O1")
        opp = self.crm.opps[oid]
        self.assertEqual(opp, {"id": "O1", "lead_id": self.lid, "owner": "ana",
                               "amount": 1000, "original_amount": 1000,
                               "stage": "prospect"})
        self.assertEqual(self.crm.leads[self.lid]["status"], "converted")
        self.assertEqual(self.crm.log[-1], ("convert", oid, "ana"))

    def test_convert_validations(self):
        with self.assertRaises(ValueError):
            self.crm.convert(self.lid, 1000, "ana")  # not qualified yet
        self.crm.qualify(self.lid, "ana")
        for bad in [0, -5, "100", 10.5, True]:
            with self.assertRaises(ValueError):
                self.crm.convert(self.lid, bad, "ana")
        with self.assertRaises(PermissionError):
            self.crm.convert(self.lid, 1000, "bob")

    def test_convert_needs_owner(self):
        # ana owns setUp's lead; bob takes the next; the rest queue.
        self.crm.add_lead("x@acme.com", "X", "referral", "max")   # -> bob
        self.crm.add_lead("y@acme.com", "Y", "referral", "max")   # -> queue
        unowned = self.crm.add_lead("z@acme.com", "Z", "referral", "max")  # -> queue
        self.crm.qualify(unowned, "max")
        with self.assertRaises(ValueError):
            self.crm.convert(unowned, 500, "max")


class TestAdvance(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        lid = self.crm.add_lead("a@acme.com", "A", "referral", "ana")
        self.crm.qualify(lid, "ana")
        self.oid = self.crm.convert(lid, 1000, "ana")

    def test_happy_path(self):
        self.crm.advance(self.oid, "proposal", "ana")
        self.crm.advance(self.oid, "negotiation", "ana")
        self.crm.advance(self.oid, "won", "ana")
        self.assertEqual(self.crm.opps[self.oid]["stage"], "won")
        self.assertEqual([e[0] for e in self.crm.log[-3:]],
                         ["advance", "advance", "advance"])

    def test_skipping_is_rejected(self):
        with self.assertRaises(ValueError):
            self.crm.advance(self.oid, "won", "ana")
        self.assertEqual(self.crm.opps[self.oid]["stage"], "prospect")
        self.assertEqual(len(self.crm.log), 3)

    def test_final_stage_locked(self):
        self.crm.advance(self.oid, "lost", "ana")
        with self.assertRaises(ValueError):
            self.crm.advance(self.oid, "proposal", "ana")

    def test_bad_stage_and_owner(self):
        with self.assertRaises(ValueError):
            self.crm.advance(self.oid, "closing", "ana")
        with self.assertRaises(PermissionError):
            self.crm.advance(self.oid, "proposal", "bob")
        with self.assertRaises(ValueError):
            self.crm.advance("O404", "proposal", "ana")

    def test_big_negotiation_needs_manager(self):
        lid = self.crm.add_lead("b@acme.com", "B", "referral", "max")  # -> bob
        self.crm.qualify(lid, "bob")
        big = self.crm.convert(lid, 60000, "bob")
        self.crm.advance(big, "proposal", "bob")
        with self.assertRaises(PermissionError):
            self.crm.advance(big, "negotiation", "bob")
        self.crm.advance(big, "negotiation", "max")
        self.assertEqual(self.crm.opps[big]["stage"], "negotiation")

    def test_won_frees_slot_for_waiting_lead(self):
        self.crm.add_lead("d@acme.com", "D", "referral", "max")  # fills bob
        waiting = self.crm.add_lead("c@acme.com", "C", "referral", "max")  # queue
        self.assertIsNone(self.crm.leads[waiting]["owner"])
        self.crm.advance(self.oid, "proposal", "ana")
        self.crm.advance(self.oid, "negotiation", "max")
        self.crm.advance(self.oid, "won", "max")
        self.assertEqual(self.crm.leads[waiting]["owner"], "ana")
        self.assertEqual(self.crm.log[-2:], [("advance", self.oid, "max"),
                                             ("assign", waiting, "system")])


class TestDiscount(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        lid = self.crm.add_lead("a@acme.com", "A", "referral", "ana")
        self.crm.qualify(lid, "ana")
        self.oid = self.crm.convert(lid, 1000, "ana")

    def test_pct_validation(self):
        for bad in [0, 31, "10", 10.0, True]:
            with self.assertRaises(ValueError):
                self.crm.discount(self.oid, bad, "ana")

    def test_rep_cap_ten_manager_thirty(self):
        with self.assertRaises(PermissionError):
            self.crm.discount(self.oid, 11, "ana")
        self.crm.discount(self.oid, 10, "ana")
        self.assertEqual(self.crm.opps[self.oid]["amount"], 900)
        self.crm.discount(self.oid, 20, "max")  # manager ok
        self.assertEqual(self.crm.opps[self.oid]["amount"], 720)
        self.assertEqual(self.crm.log[-2:], [("discount", self.oid, "ana"),
                                             ("discount", self.oid, "max")])

    def test_cumulative_floor(self):
        self.crm.discount(self.oid, 10, "max")   # 1000 -> 900
        with self.assertRaises(ValueError):       # 900*0.7=630 < 700 floor
            self.crm.discount(self.oid, 30, "max")
        self.assertEqual(self.crm.opps[self.oid]["amount"], 900)
        self.crm.discount(self.oid, 22, "max")   # 900 -> 702, 70200 >= 70000 ok
        self.assertEqual(self.crm.opps[self.oid]["amount"], 702)

    def test_non_owner_denied(self):
        with self.assertRaises(PermissionError):
            self.crm.discount(self.oid, 5, "bob")

    def test_final_stage_denied(self):
        self.crm.advance(self.oid, "proposal", "ana")
        self.crm.advance(self.oid, "negotiation", "max")
        self.crm.advance(self.oid, "won", "max")
        with self.assertRaises(ValueError):
            self.crm.discount(self.oid, 5, "max")


class TestTransferAndForecast(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        lid = self.crm.add_lead("a@acme.com", "A", "referral", "ana")
        self.crm.qualify(lid, "ana")
        self.oid = self.crm.convert(lid, 1000, "ana")

    def test_only_manager_transfers(self):
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.oid, "bob", "ana")

    def test_bad_new_owner(self):
        with self.assertRaises(ValueError):
            self.crm.transfer(self.oid, "max", "max")   # not a rep
        with self.assertRaises(ValueError):
            self.crm.transfer(self.oid, "ghost", "max")
        with self.assertRaises(ValueError):
            self.crm.transfer(self.oid, "ana", "max")   # same owner

    def test_capacity_blocks(self):
        lid2 = self.crm.add_lead("b@acme.com", "B", "referral", "max")
        self.crm.qualify(lid2, "bob")
        self.crm.convert(lid2, 500, "bob")  # bob now at capacity
        with self.assertRaises(ValueError):
            self.crm.transfer(self.oid, "bob", "max")

    def test_transfer_moves_ownership_and_logs(self):
        # A non-empty queue implies every rep is at capacity, so a transfer can
        # only land on a rep with a free slot when the queue is already empty;
        # the old-owner free-slot loop then has nothing to do.
        self.crm.transfer(self.oid, "bob", "max")
        self.assertEqual(self.crm.opps[self.oid]["owner"], "bob")
        self.assertEqual(self.crm.log[-1], ("transfer", self.oid, "max"))
        # ana's slot is free again: the next lead routes to ana.
        nxt = self.crm.add_lead("z@acme.com", "Z", "web", "max")
        self.assertEqual(self.crm.leads[nxt]["owner"], "ana")

    def test_forecast(self):
        self.assertEqual(self.crm.forecast(), {"open": 1, "weighted": 100, "won": 0})
        self.crm.advance(self.oid, "proposal", "ana")
        self.assertEqual(self.crm.forecast()["weighted"], 300)
        self.crm.advance(self.oid, "negotiation", "max")
        self.assertEqual(self.crm.forecast(), {"open": 1, "weighted": 600, "won": 0})
        lid2 = self.crm.add_lead("b@acme.com", "B", "referral", "max")
        self.crm.add_lead("c@acme.com", "C", "referral", "max")  # queued
        self.crm.qualify(lid2, "bob")
        other = self.crm.convert(lid2, 100, "bob")
        self.crm.advance(other, "lost", "bob")
        self.assertEqual(self.crm.forecast(), {"open": 1, "weighted": 600, "won": 0})
        self.crm.advance(self.oid, "won", "max")
        self.assertEqual(self.crm.forecast(), {"open": 0, "weighted": 0, "won": 1000})
        # forecast never appends to the log
        self.assertEqual(self.crm.log[-1], ("advance", self.oid, "max"))


if __name__ == "__main__":
    unittest.main()
