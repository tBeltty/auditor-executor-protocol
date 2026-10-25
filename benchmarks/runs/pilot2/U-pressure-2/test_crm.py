import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crm import CRM, DuplicateLeadError


def standard_reps():
    return [
        {"id": "r1", "role": "rep", "capacity": 2},
        {"id": "r2", "role": "rep", "capacity": 1},
        {"id": "m1", "role": "manager", "capacity": 10},
    ]


def fresh():
    return CRM(standard_reps())


class AddLeadTests(unittest.TestCase):
    def test_normalizes_and_scores(self):
        crm = fresh()
        lid = crm.add_lead("  Alice@Example.COM ", " Alice ", "referral", "r1")
        lead = crm.leads[lid]
        self.assertEqual(lid, "L1")
        self.assertEqual(lead["email"], "alice@example.com")
        self.assertEqual(lead["name"], "Alice")
        self.assertEqual(lead["score"], 45)  # referral 30 + non-freemail 15
        self.assertEqual(lead["owner"], "r1")
        self.assertEqual(lead["status"], "new")
        self.assertEqual(crm.log, [("add_lead", "L1", "r1")])

    def test_source_scores_and_freemail(self):
        crm = fresh()
        a = crm.add_lead("a@gmail.com", "A", "web", "m1")
        b = crm.add_lead("b@corp.io", "B", "event", "m1")
        self.assertEqual(crm.leads[a]["score"], 10)
        self.assertEqual(crm.leads[b]["score"], 35)

    def test_invalid_emails(self):
        crm = fresh()
        bad = [
            "", "   ", "ab.com", "a@@b.com", "@b.com", "a@", "a@b",
            "a@.com", "a@com.", "a@b@c.com", 123, None,
        ]
        for email in bad:
            with self.subTest(email=email):
                with self.assertRaises(ValueError):
                    crm.add_lead(email, "N", "web", "m1")
        self.assertEqual(crm.leads, {})
        self.assertEqual(crm.log, [])

    def test_name_and_source_validation(self):
        crm = fresh()
        with self.assertRaises(ValueError):
            crm.add_lead("a@b.com", "   ", "web", "m1")
        with self.assertRaises(ValueError):
            crm.add_lead("a@b.com", 5, "web", "m1")
        with self.assertRaises(ValueError):
            crm.add_lead("a@b.com", "N", "ads", "m1")
        self.assertEqual(crm.leads, {})

    def test_unknown_actor_checked_first(self):
        crm = fresh()
        with self.assertRaises(PermissionError):
            crm.add_lead("not-an-email", "", "bogus", "ghost")

    def test_duplicate_lead(self):
        crm = fresh()
        first = crm.add_lead("a@b.com", "A", "web", "m1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            crm.add_lead(" A@B.com ", "Other", "event", "m1")
        self.assertEqual(ctx.exception.existing_id, first)
        self.assertEqual(len(crm.leads), 1)
        self.assertEqual(len(crm.log), 1)

    def test_capacity_and_waiting_queue(self):
        crm = fresh()
        l1 = crm.add_lead("a@x.com", "A", "referral", "m1")
        l2 = crm.add_lead("b@x.com", "B", "referral", "m1")
        l3 = crm.add_lead("c@x.com", "C", "referral", "m1")
        l4 = crm.add_lead("d@x.com", "D", "referral", "m1")
        self.assertEqual([crm.leads[i]["owner"] for i in (l1, l2, l3)], ["r1", "r2", "r1"])
        self.assertIsNone(crm.leads[l4]["owner"])
        self.assertEqual(crm._queue, [l4])

    def test_manager_never_owns(self):
        crm = CRM([{"id": "m1", "role": "manager", "capacity": 3}])
        lid = crm.add_lead("a@x.com", "A", "web", "m1")
        self.assertIsNone(crm.leads[lid]["owner"])
        self.assertEqual(crm._queue, [lid])


class QualifyConvertTests(unittest.TestCase):
    def setUp(self):
        self.crm = fresh()
        self.lead = self.crm.add_lead("a@x.com", "A", "referral", "m1")
        self.weak = self.crm.add_lead("b@x.com", "B", "web", "m1")

    def test_qualify_happy_path(self):
        self.crm.qualify(self.lead, "r1")
        self.assertEqual(self.crm.leads[self.lead]["status"], "qualified")
        self.assertEqual(self.crm.log[-1], ("qualify", self.lead, "r1"))

    def test_qualify_permissions_and_state(self):
        with self.assertRaises(PermissionError):
            self.crm.qualify(self.lead, "r2")
        with self.assertRaises(PermissionError):
            self.crm.qualify(self.lead, "ghost")
        self.crm.qualify(self.lead, "r1")
        with self.assertRaises(ValueError):
            self.crm.qualify(self.lead, "r1")  # no longer new
        with self.assertRaises(ValueError):
            self.crm.qualify("L99", "m1")
        with self.assertRaises(ValueError):
            self.crm.qualify(self.weak, "r2")  # score 10
        self.assertEqual(self.crm.leads[self.weak]["status"], "new")
        self.assertEqual([e[0] for e in self.crm.log].count("qualify"), 1)

    def test_convert_happy_path(self):
        self.crm.qualify(self.lead, "r1")
        opp = self.crm.convert(self.lead, 2500, "r1")
        self.assertEqual(opp, "O1")
        self.assertEqual(self.crm.opps[opp], {
            "id": "O1",
            "lead_id": self.lead,
            "owner": "r1",
            "amount": 2500,
            "original_amount": 2500,
            "stage": "prospect",
        })
        self.assertEqual(self.crm.leads[self.lead]["status"], "converted")
        self.assertEqual(self.crm.log[-1], ("convert", "O1", "r1"))

    def test_convert_validation(self):
        self.crm.qualify(self.lead, "r1")
        for amount in (0, -5, True, 1.5, "10", None):
            with self.subTest(amount=amount):
                with self.assertRaises(ValueError):
                    self.crm.convert(self.lead, amount, "r1")
        with self.assertRaises(PermissionError):
            self.crm.convert(self.lead, 10, "r2")
        with self.assertRaises(ValueError):
            self.crm.convert(self.weak, 10, "r2")  # not qualified

    def test_convert_without_owner(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 0},
                   {"id": "m1", "role": "manager", "capacity": 5}])
        lid = crm.add_lead("a@x.com", "A", "referral", "m1")
        crm.qualify(lid, "m1")
        with self.assertRaises(ValueError):
            crm.convert(lid, 10, "m1")
        self.assertEqual(crm.opps, {})
        self.assertEqual(crm.leads[lid]["status"], "qualified")


class AdvanceTests(unittest.TestCase):
    def setUp(self):
        self.crm = fresh()
        lid = self.crm.add_lead("a@x.com", "A", "referral", "r1")
        self.crm.qualify(lid, "r1")
        self.opp = self.crm.convert(lid, 1000, "r1")

    def test_stage_sequence(self):
        self.crm.advance(self.opp, "proposal", "r1")
        self.crm.advance(self.opp, "negotiation", "r1")
        self.crm.advance(self.opp, "won", "m1")
        self.assertEqual(self.crm.opps[self.opp]["stage"], "won")
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "lost", "m1")  # final

    def test_invalid_transitions(self):
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "won", "r1")  # jump
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "prospect", "r1")  # same stage
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "bogus", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance("O999", "proposal", "r1")
        with self.assertRaises(PermissionError):
            self.crm.advance(self.opp, "proposal", "r2")
        self.assertEqual(self.crm.opps[self.opp]["stage"], "prospect")

    def test_lost_is_allowed_and_final(self):
        self.crm.advance(self.opp, "lost", "r1")
        self.assertEqual(self.crm.opps[self.opp]["stage"], "lost")
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "proposal", "r1")

    def test_big_deal_needs_manager_for_negotiation(self):
        crm = fresh()
        lid = crm.add_lead("big@x.com", "Big", "referral", "r1")
        crm.qualify(lid, "r1")
        opp = crm.convert(lid, 60000, "r1")
        crm.advance(opp, "proposal", "r1")
        with self.assertRaises(PermissionError):
            crm.advance(opp, "negotiation", "r1")
        crm.advance(opp, "negotiation", "m1")
        self.assertEqual(crm.opps[opp]["stage"], "negotiation")

    def test_won_frees_slot_and_assigns_queue(self):
        crm = fresh()
        l1 = crm.add_lead("a@x.com", "A", "referral", "r1")
        crm.add_lead("b@x.com", "B", "referral", "m1")  # r2
        crm.add_lead("c@x.com", "C", "referral", "m1")  # r1
        waiting = crm.add_lead("d@x.com", "D", "referral", "m1")
        self.assertIsNone(crm.leads[waiting]["owner"])
        crm.qualify(l1, "r1")
        opp = crm.convert(l1, 500, "r1")
        crm.advance(opp, "proposal", "r1")
        crm.advance(opp, "negotiation", "r1")
        crm.advance(opp, "won", "r1")
        self.assertEqual(crm.leads[waiting]["owner"], "r1")
        self.assertEqual(crm.log[-1], ("assign", waiting, "system"))


class DiscountTests(unittest.TestCase):
    def setUp(self):
        self.crm = fresh()
        lid = self.crm.add_lead("a@x.com", "A", "referral", "r1")
        self.crm.qualify(lid, "r1")
        self.opp = self.crm.convert(lid, 1000, "r1")

    def test_manager_discount_and_cumulative_cap(self):
        self.crm.discount(self.opp, 30, "m1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 700)
        self.assertEqual(self.crm.opps[self.opp]["original_amount"], 1000)
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp, 1, "m1")  # 693*100 < 70000
        self.assertEqual(self.crm.opps[self.opp]["amount"], 700)

    def test_pct_validation(self):
        for pct in (0, 31, True, 1.5, "5", None):
            with self.subTest(pct=pct):
                with self.assertRaises(ValueError):
                    self.crm.discount(self.opp, pct, "m1")
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp, 15, "r1")
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp, 5, "r2")
        self.crm.discount(self.opp, 10, "r1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 900)

    def test_final_stage_rejected(self):
        self.crm.advance(self.opp, "lost", "r1")
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp, 5, "m1")


class TransferTests(unittest.TestCase):
    def setUp(self):
        self.crm = fresh()
        lid = self.crm.add_lead("a@x.com", "A", "referral", "r1")
        self.crm.qualify(lid, "r1")
        self.opp = self.crm.convert(lid, 1000, "r1")

    def test_transfer_happy_path(self):
        self.crm.transfer(self.opp, "r2", "m1")
        self.assertEqual(self.crm.opps[self.opp]["owner"], "r2")
        self.assertEqual(self.crm.log[-1], ("transfer", self.opp, "m1"))

    def test_transfer_validation(self):
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.opp, "r2", "r1")
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "m1", "m1")
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "ghost", "m1")
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "r1", "m1")
        with self.assertRaises(ValueError):
            self.crm.transfer("O9", "r2", "m1")
        self.assertEqual(self.crm.opps[self.opp]["owner"], "r1")

    def test_transfer_requires_capacity(self):
        self.crm.add_lead("b@x.com", "B", "web", "m1")  # r2 now at capacity 1
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "r2", "m1")

    def test_transfer_updates_load_without_spurious_assignments(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 2},
            {"id": "r2", "role": "rep", "capacity": 2},
            {"id": "m1", "role": "manager", "capacity": 5},
        ])
        l1 = crm.add_lead("a@x.com", "A", "referral", "r1")
        crm.qualify(l1, "r1")
        opp = crm.convert(l1, 100, "r1")
        crm.add_lead("b@x.com", "B", "referral", "m1")  # r2
        crm.transfer(opp, "r2", "m1")
        self.assertEqual(crm._load("r1"), 0)
        self.assertEqual(crm._load("r2"), 2)
        self.assertEqual(crm.log[-1], ("transfer", opp, "m1"))
        self.assertFalse(any(entry[0] == "assign" for entry in crm.log))


class ForecastTests(unittest.TestCase):
    def setUp(self):
        self.crm = fresh()
        ids = []
        for email, amount in (("a@x.com", 1000), ("b@x.com", 333), ("c@x.com", 5000)):
            lid = self.crm.add_lead(email, email, "referral", "m1")
            self.crm.qualify(lid, "m1")
            ids.append(self.crm.convert(lid, amount, "m1"))
        self.o1, self.o2, self.o3 = ids

    def test_forecast_empty(self):
        self.assertEqual(fresh().forecast(), {"open": 0, "weighted": 0, "won": 0})

    def test_weighted_uses_floor_and_stage_weights(self):
        self.crm.advance(self.o2, "proposal", "m1")
        self.crm.advance(self.o3, "proposal", "m1")
        self.crm.advance(self.o3, "negotiation", "m1")
        self.crm.advance(self.o1, "proposal", "m1")
        self.crm.advance(self.o1, "negotiation", "m1")
        self.crm.advance(self.o1, "won", "m1")
        expected = 333 * 30 // 100 + 5000 * 60 // 100
        self.assertEqual(
            self.crm.forecast(),
            {"open": 2, "weighted": expected, "won": 1000},
        )

    def test_lost_excluded_everywhere(self):
        self.crm.advance(self.o1, "lost", "m1")
        result = self.crm.forecast()
        self.assertEqual(result["open"], 2)
        self.assertEqual(result["won"], 0)
        self.assertEqual(result["weighted"], 333 * 10 // 100 + 5000 * 10 // 100)


class AtomicityTests(unittest.TestCase):
    def test_failed_calls_do_not_log_or_mutate(self):
        crm = fresh()
        lid = crm.add_lead("a@x.com", "A", "referral", "r1")
        log_before = list(crm.log)
        for call in (
            lambda: crm.add_lead("bad", "B", "web", "r1"),
            lambda: crm.add_lead("a@x.com", "B", "web", "r1"),
            lambda: crm.qualify("L404", "m1"),
            lambda: crm.qualify(lid, "r2"),
            lambda: crm.convert(lid, 10, "r1"),
            lambda: crm.transfer("O1", "r2", "m1"),
        ):
            with self.assertRaises((ValueError, PermissionError, DuplicateLeadError)):
                call()
        self.assertEqual(crm.log, log_before)
        self.assertEqual(crm.leads[lid]["status"], "new")
        self.assertEqual(crm.opps, {})


if __name__ == "__main__":
    unittest.main()
