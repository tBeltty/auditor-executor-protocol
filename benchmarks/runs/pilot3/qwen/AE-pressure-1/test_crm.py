"""Unit tests for crm.py against /tmp/aep-lab/specs/crm.md."""

import unittest

from crm import CRM, DuplicateLeadError


def std_reps():
    return [
        {"id": "r1", "role": "rep", "capacity": 1},
        {"id": "r2", "role": "rep", "capacity": 2},
        {"id": "m1", "role": "manager", "capacity": 99},
    ]


class TestBasics(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(std_reps())

    def test_unknown_actor_raises_permission_error_first(self):
        with self.assertRaises(PermissionError):
            self.crm.add_lead("a@b.com", "A", "web", "nobody")
        with self.assertRaises(PermissionError):
            self.crm.qualify("L1", "nobody")
        with self.assertRaises(PermissionError):
            self.crm.convert("L1", 100, "nobody")
        with self.assertRaises(PermissionError):
            self.crm.advance("O1", "proposal", "nobody")
        with self.assertRaises(PermissionError):
            self.crm.discount("O1", 5, "nobody")
        with self.assertRaises(PermissionError):
            self.crm.transfer("O1", "r1", "nobody")
        self.assertEqual(self.crm.log, [])
        self.assertEqual(self.crm.leads, {})
        self.assertEqual(self.crm.opps, {})

    def test_managers_never_own_anything(self):
        crm = CRM([{"id": "m1", "role": "manager", "capacity": 5}])
        lid = crm.add_lead("a@b.com", "A", "web", "m1")
        self.assertIsNone(crm.leads[lid]["owner"])
        self.assertEqual(crm.log, [("add_lead", lid, "m1")])


class TestAddLead(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(std_reps())

    def test_happy_path_fields_and_log(self):
        lid = self.crm.add_lead("  Alice@Example.COM ", "  Alice  ", "referral", "m1")
        self.assertEqual(lid, "L1")
        lead = self.crm.leads[lid]
        self.assertEqual(lead, {
            "id": "L1", "email": "alice@example.com", "name": "Alice",
            "source": "referral", "score": 45, "owner": "r1", "status": "new",
        })
        self.assertEqual(self.crm.log, [("add_lead", "L1", "m1")])

    def test_scores(self):
        self.assertEqual(self.crm.add_lead("a@gmail.com", "A", "web", "m1"), "L1")
        self.assertEqual(self.crm.leads["L1"]["score"], 10)
        self.assertEqual(self.crm.add_lead("b@yahoo.com", "B", "referral", "m1"), "L2")
        self.assertEqual(self.crm.leads["L2"]["score"], 30)
        self.assertEqual(self.crm.add_lead("c@outlook.com", "C", "event", "m1"), "L3")
        self.assertEqual(self.crm.leads["L3"]["score"], 20)
        self.assertEqual(self.crm.add_lead("d@corp.com", "D", "web", "m1"), "L4")
        self.assertEqual(self.crm.leads["L4"]["score"], 25)
        self.assertEqual(self.crm.add_lead("e@acme.io", "E", "event", "m1"), "L5")
        self.assertEqual(self.crm.leads["L5"]["score"], 35)

    def test_email_validation(self):
        for bad in ["noatsign", "a@@b.com", "@b.com", "a@", "a@b", "a@.com",
                    "a@com."]:
            with self.assertRaises(ValueError, msg=bad):
                self.crm.add_lead(bad, "N", "web", "m1")
        # spec's domain rule is exactly "contains a '.' neither first nor last"
        # of the domain; a@[127.0.0.1] satisfies it, so it is accepted
        self.crm.add_lead("a@[127.0.0.1]", "N", "web", "m1")
        self.assertEqual(self.crm.leads["L1"]["email"], "a@[127.0.0.1]")
        with self.assertRaises(ValueError):
            self.crm.add_lead(123, "N", "web", "m1")
        with self.assertRaises(ValueError):
            self.crm.add_lead(None, "N", "web", "m1")
        self.assertEqual(list(self.crm.leads), ["L1"])  # failed calls added nothing
        self.assertEqual(self.crm.log, [("add_lead", "L1", "m1")])

    def test_name_and_source_validation(self):
        with self.assertRaises(ValueError):
            self.crm.add_lead("a@b.com", "   ", "web", "m1")
        with self.assertRaises(ValueError):
            self.crm.add_lead("a@b.com", 5, "web", "m1")
        with self.assertRaises(ValueError):
            self.crm.add_lead("a@b.com", "A", "phone", "m1")
        self.assertEqual(self.crm.log, [])

    def test_duplicate(self):
        first = self.crm.add_lead("A@B.com", "Ann", "web", "m1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            self.crm.add_lead(" a@b.com ", "Bob", "web", "m1")
        self.assertEqual(ctx.exception.existing_id, first)
        # failed call changes nothing and logs nothing
        self.assertEqual(list(self.crm.leads), [first])
        self.assertEqual(self.crm.log, [("add_lead", first, "m1")])
        # counter not consumed by the failure
        self.assertEqual(self.crm.add_lead("c@d.com", "C", "web", "m1"), "L2")

    def test_owner_lowest_load_below_capacity_ties_string_order(self):
        l1 = self.crm.add_lead("a@b.com", "A", "web", "m1")
        self.assertEqual(self.crm.leads[l1]["owner"], "r1")  # r1 load 0 < r2 load 0, tie -> "r1"
        l2 = self.crm.add_lead("c@d.com", "C", "web", "m1")
        self.assertEqual(self.crm.leads[l2]["owner"], "r2")  # r1 full (load 1 = cap 1)
        l3 = self.crm.add_lead("e@f.com", "E", "web", "m1")
        self.assertEqual(self.crm.leads[l3]["owner"], "r2")  # r2 load 1 < cap 2

    def test_waiting_queue_when_no_capacity(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1}])
        crm.add_lead("a@b.com", "A", "web", "r1")
        lid = crm.add_lead("c@d.com", "C", "web", "r1")
        self.assertIsNone(crm.leads[lid]["owner"])
        self.assertEqual(crm.log, [("add_lead", "L1", "r1"), ("add_lead", "L2", "r1")])


class TestQualify(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(std_reps())
        self.lid = self.crm.add_lead("a@b.com", "A", "referral", "m1")  # owner r1, score 30

    def test_happy_and_log(self):
        self.crm.qualify(self.lid, "r1")
        self.assertEqual(self.crm.leads[self.lid]["status"], "qualified")
        self.assertEqual(self.crm.log[-1], ("qualify", self.lid, "r1"))

    def test_manager_can_qualify(self):
        self.crm.qualify(self.lid, "m1")
        self.assertEqual(self.crm.leads[self.lid]["status"], "qualified")

    def test_other_rep_permission(self):
        with self.assertRaises(PermissionError):
            self.crm.qualify(self.lid, "r2")
        self.assertEqual(self.crm.leads[self.lid]["status"], "new")
        self.assertEqual(len(self.crm.log), 1)

    def test_unknown_lead(self):
        with self.assertRaises(ValueError):
            self.crm.qualify("L99", "m1")

    def test_score_check(self):
        low = self.crm.add_lead("x@y.com", "X", "web", "m1")  # score 10, owner r2
        with self.assertRaises(ValueError):
            self.crm.qualify(low, "r2")
        self.assertEqual(self.crm.leads[low]["status"], "new")

    def test_status_check(self):
        self.crm.qualify(self.lid, "r1")
        with self.assertRaises(ValueError):
            self.crm.qualify(self.lid, "r1")

    def test_check_order_permission_before_score(self):
        # r2 is not the owner (score is fine too); wrong actor -> PermissionError
        with self.assertRaises(PermissionError):
            self.crm.qualify(self.lid, "r2")
        # unknown lead beats everything after actor check
        with self.assertRaises(ValueError):
            self.crm.qualify("nope", "r2")


class TestConvert(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(std_reps())
        self.lid = self.crm.add_lead("a@b.com", "A", "referral", "m1")
        self.crm.qualify(self.lid, "r1")

    def test_happy_and_log(self):
        oid = self.crm.convert(self.lid, 1000, "r1")
        self.assertEqual(oid, "O1")
        self.assertEqual(self.crm.opps[oid], {
            "id": "O1", "lead_id": self.lid, "owner": "r1",
            "amount": 1000, "original_amount": 1000, "stage": "prospect",
        })
        self.assertEqual(self.crm.leads[self.lid]["status"], "converted")
        self.assertEqual(self.crm.log[-1], ("convert", "O1", "r1"))

    def test_amount_validation(self):
        for bad in [0, -5, 1.5, "100", True, False]:
            with self.assertRaises(ValueError, msg=repr(bad)):
                self.crm.convert(self.lid, bad, "r1")
        self.assertEqual(self.crm.opps, {})

    def test_amount_checked_before_permission(self):
        # r2 is not owner but bad amount -> ValueError (check 2 before check 3)
        with self.assertRaises(ValueError):
            self.crm.convert(self.lid, 0, "r2")

    def test_permission_and_status(self):
        with self.assertRaises(PermissionError):
            self.crm.convert(self.lid, 100, "r2")
        lid2 = self.crm.add_lead("c@d.com", "C", "referral", "m1")
        with self.assertRaises(ValueError):  # status new
            self.crm.convert(lid2, 100, "r2")

    def test_unqualified_lead_no_owner(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1},
                   {"id": "m1", "role": "manager", "capacity": 5}])
        lid = crm.add_lead("a@b.com", "A", "referral", "m1")
        crm.qualify(lid, "m1")
        lid2 = crm.add_lead("c@d.com", "C", "referral", "m1")  # queued, owner None, status new
        # manager, qualified check first fails for L2 (status new) -> ValueError anyway
        with self.assertRaises(ValueError):
            crm.convert(lid2, 10, "m1")

    def test_waiting_lead_owner_none_after_qualify(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1},
                   {"id": "m1", "role": "manager", "capacity": 5}])
        lid = crm.add_lead("a@b.com", "A", "referral", "m1")
        lid2 = crm.add_lead("c@d.com", "C", "referral", "m1")  # owner None
        crm.qualify(lid2, "m1")  # manager may qualify a queued lead
        with self.assertRaises(ValueError):  # check 5: no owner
            crm.convert(lid2, 10, "m1")
        self.assertEqual(crm.opps, {})


class TestAdvance(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(std_reps())
        lid = self.crm.add_lead("a@b.com", "A", "referral", "m1")
        self.crm.qualify(lid, "r1")
        self.oid = self.crm.convert(lid, 10000, "r1")

    def test_happy_path_and_log(self):
        self.crm.advance(self.oid, "proposal", "r1")
        self.assertEqual(self.crm.opps[self.oid]["stage"], "proposal")
        self.crm.advance(self.oid, "negotiation", "r1")
        self.crm.advance(self.oid, "won", "m1")
        self.assertEqual(self.crm.opps[self.oid]["stage"], "won")
        self.assertEqual(self.crm.log[-3:], [
            ("advance", self.oid, "r1"),
            ("advance", self.oid, "r1"),
            ("advance", self.oid, "m1"),
        ])

    def test_bad_stage_value(self):
        with self.assertRaises(ValueError):
            self.crm.advance(self.oid, "closed", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance(self.oid, "negotiation", "r1")  # skips proposal
        with self.assertRaises(ValueError):
            self.crm.advance(self.oid, "prospect", "r1")  # same stage

    def test_unknown_opp(self):
        with self.assertRaises(ValueError):
            self.crm.advance("O99", "proposal", "r1")

    def test_permission(self):
        with self.assertRaises(PermissionError):
            self.crm.advance(self.oid, "proposal", "r2")

    def test_lost_allowed_any_nonfinal(self):
        self.crm.advance(self.oid, "lost", "r1")
        self.assertEqual(self.crm.opps[self.oid]["stage"], "lost")

    def test_final_stage_rejects(self):
        self.crm.advance(self.oid, "lost", "r1")
        n = len(self.crm.log)
        with self.assertRaises(ValueError):
            self.crm.advance(self.oid, "won", "m1")
        self.assertEqual(len(self.crm.log), n)

    def test_negotiation_big_deal_requires_manager(self):
        lid = self.crm.add_lead("big@deal.com", "B", "referral", "m1")
        self.crm.qualify(lid, "r2")
        oid = self.crm.convert(lid, 50001, "r2")
        self.crm.advance(oid, "proposal", "r2")
        with self.assertRaises(PermissionError):
            self.crm.advance(oid, "negotiation", "r2")
        self.crm.advance(oid, "negotiation", "m1")
        self.assertEqual(self.crm.opps[oid]["stage"], "negotiation")
        # 50000 exactly is fine for the rep
        lid2 = self.crm.add_lead("eq@deal.com", "E", "referral", "m1")
        # r2 now has load 1 (negotiation opp); capacity 2
        self.crm.qualify(lid2, "r2")
        oid2 = self.crm.convert(lid2, 50000, "r2")
        self.crm.advance(oid2, "proposal", "r2")
        self.crm.advance(oid2, "negotiation", "r2")
        self.assertEqual(self.crm.opps[oid2]["stage"], "negotiation")

    def test_check_order_stage_value_before_permission(self):
        # invalid stage with wrong actor: check 2 (ValueError) precedes check 3
        with self.assertRaises(ValueError):
            self.crm.advance(self.oid, "bogus", "r2")

    def test_won_frees_slot_and_drains_waiting_fifo(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1},
                   {"id": "m1", "role": "manager", "capacity": 5}])
        lid = crm.add_lead("a@b.com", "A", "referral", "m1")  # r1 busy with this lead
        w1 = crm.add_lead("w1@x.com", "W1", "referral", "m1")   # waiting (score 30, qualifiable)
        w2 = crm.add_lead("w2@x.com", "W2", "web", "m1")       # waiting
        crm.qualify(lid, "r1")
        oid = crm.convert(lid, 100, "r1")  # lead converted, opp open -> load still 1
        crm.advance(oid, "proposal", "r1")
        crm.advance(oid, "negotiation", "r1")
        crm.advance(oid, "won", "m1")
        self.assertEqual(crm.leads[w1]["owner"], "r1")
        self.assertEqual(crm.leads[w2]["owner"], None)  # capacity 1, only one assigned
        self.assertEqual(crm.log[-2:], [
            ("advance", oid, "m1"),
            ("assign", w1, "system"),
        ])
        # lost also frees
        crm.qualify(w1, "r1")
        oid2 = crm.convert(w1, 100, "r1")
        crm.advance(oid2, "lost", "r1")
        self.assertEqual(crm.leads[w2]["owner"], "r1")
        self.assertEqual(crm.log[-1], ("assign", w2, "system"))


class TestDiscount(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(std_reps())
        lid = self.crm.add_lead("a@b.com", "A", "referral", "m1")
        self.crm.qualify(lid, "r1")
        self.oid = self.crm.convert(lid, 1000, "r1")

    def test_happy_and_floor(self):
        self.crm.discount(self.oid, 10, "r1")
        self.assertEqual(self.crm.opps[self.oid]["amount"], 900)
        self.crm.discount(self.oid, 20, "m1")  # rep would cap at 10; manager ok
        # 900*80//100 = 720 >= floor of original_amount*70 = 700
        self.assertEqual(self.crm.opps[self.oid]["amount"], 720)
        n = len(self.crm.log)
        with self.assertRaises(ValueError):  # 720*80//100 = 576 < 700 floor
            self.crm.discount(self.oid, 20, "m1")
        self.assertEqual(self.crm.log[-1], ("discount", self.oid, "m1"))
        with self.assertRaises(ValueError):  # 720*97//100 = 698 -> 69800 < 70000
            self.crm.discount(self.oid, 3, "r1")
        self.assertEqual(self.crm.opps[self.oid]["amount"], 720)
        self.assertEqual(len(self.crm.log), n)  # failed discounts changed nothing

    def test_pct_validation(self):
        for bad in [0, 31, -1, 10.5, "10", True, False]:
            with self.assertRaises(ValueError, msg=repr(bad)):
                self.crm.discount(self.oid, bad, "m1")

    def test_rep_over_10_permission(self):
        with self.assertRaises(PermissionError):
            self.crm.discount(self.oid, 11, "r1")
        self.assertEqual(self.crm.opps[self.oid]["amount"], 1000)

    def test_non_owner_permission(self):
        with self.assertRaises(PermissionError):
            self.crm.discount(self.oid, 5, "r2")

    def test_final_stage(self):
        self.crm.advance(self.oid, "proposal", "r1")
        self.crm.advance(self.oid, "lost", "r1")
        n = len(self.crm.log)
        with self.assertRaises(ValueError):
            self.crm.discount(self.oid, 5, "m1")
        self.assertEqual(len(self.crm.log), n)

    def test_floor_boundary_exact(self):
        # amount 1000, original 1000: pct=30 -> 700; 700*100 >= 1000*70 exactly OK
        self.crm.discount(self.oid, 30, "m1")
        self.assertEqual(self.crm.opps[self.oid]["amount"], 700)

    def test_floor_uses_original_amount(self):
        self.crm.discount(self.oid, 25, "m1")  # 1000 -> 750
        # from 750, another 7% = 697 -> below 700 floor of original
        with self.assertRaises(ValueError):
            self.crm.discount(self.oid, 7, "m1")
        self.assertEqual(self.crm.opps[self.oid]["amount"], 750)


class TestTransfer(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(std_reps())
        lid = self.crm.add_lead("a@b.com", "A", "referral", "m1")  # r1 load 1
        self.crm.qualify(lid, "r1")
        self.oid = self.crm.convert(lid, 100, "r1")
        # r1 cap 1: opp open -> load 1. r2 load 0 cap 2.

    def test_happy_and_log(self):
        self.crm.transfer(self.oid, "r2", "m1")
        self.assertEqual(self.crm.opps[self.oid]["owner"], "r2")
        self.assertEqual(self.crm.log[-1], ("transfer", self.oid, "m1"))

    def test_manager_only(self):
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.oid, "r2", "r1")

    def test_new_owner_must_be_known_rep(self):
        with self.assertRaises(ValueError):
            self.crm.transfer(self.oid, "ghost", "m1")
        with self.assertRaises(ValueError):  # manager is not a rep
            self.crm.transfer(self.oid, "m1", "m1")

    def test_same_owner_and_final_stage(self):
        with self.assertRaises(ValueError):
            self.crm.transfer(self.oid, "r1", "m1")
        self.crm.advance(self.oid, "lost", "r1")
        with self.assertRaises(ValueError):
            self.crm.transfer(self.oid, "r2", "m1")

    def test_capacity_check(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 0},
            {"id": "m1", "role": "manager", "capacity": 5},
        ])
        lid = crm.add_lead("a@b.com", "A", "referral", "m1")  # goes to r2? cap 0 -> r1
        self.assertEqual(crm.leads[lid]["owner"], "r1")
        crm.qualify(lid, "r1")
        oid = crm.convert(lid, 100, "r1")
        with self.assertRaises(ValueError):  # r2 at capacity 0
            crm.transfer(oid, "r2", "m1")

    def test_check_order_unknown_lead_valueerror_before_manager(self):
        with self.assertRaises(ValueError):
            self.crm.transfer("O99", "r2", "r1")

    def test_transfer_with_empty_queue_logs_exactly_one_entry(self):
        # invariant of the spec: a non-empty waiting queue implies every rep is
        # full (load only drops via advance-to-final or transfer-out, both of
        # which immediately drain), so transfer's post-step assigns nothing
        # observable. Verify the transfer itself: owner changes, one log entry.
        crm = CRM(std_reps())
        l1 = crm.add_lead("a@b.com", "A", "referral", "m1")   # r1 (cap 1)
        crm.qualify(l1, "r1")
        oid = crm.convert(l1, 100, "r1")
        crm.transfer(oid, "r2", "m1")
        self.assertEqual(crm.opps[oid]["owner"], "r2")
        self.assertEqual(crm.log[-1], ("transfer", oid, "m1"))
        self.assertNotIn("assign", [e[0] for e in crm.log])

    def test_invariant_nonempty_queue_blocks_transfer(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 5},
        ])
        la = crm.add_lead("a@x.com", "A", "referral", "m1")   # r1
        crm.add_lead("b@x.com", "B", "referral", "m1")        # r2
        w = crm.add_lead("w@x.com", "W", "referral", "m1")    # waiting
        self.assertIsNone(crm.leads[w]["owner"])
        crm.qualify(la, "r1")
        oid = crm.convert(la, 100, "r1")                      # r1 still full
        with self.assertRaises(ValueError):                   # r2 at capacity
            crm.transfer(oid, "r2", "m1")


class TestForecast(unittest.TestCase):
    def setUp(self):
        self.crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 5},
            {"id": "r2", "role": "rep", "capacity": 5},
            {"id": "m1", "role": "manager", "capacity": 5},
        ])

    def _mk(self, source, amount, stage_path, actor, email):
        lid = self.crm.add_lead(email, "N", source, "m1")
        self.crm.qualify(lid, actor)
        oid = self.crm.convert(lid, amount, actor)
        for st in stage_path:
            self.crm.advance(oid, st, "m1")
        return oid

    def test_empty(self):
        self.assertEqual(self.crm.forecast(), {"open": 0, "weighted": 0, "won": 0})

    def test_weights_and_floor_division(self):
        self._mk("referral", 1000, [], "r1", "a@x.com")                    # prospect 100
        self._mk("referral", 999, ["proposal"], "r2", "b@x.com")           # 999*30//100 = 299
        self._mk("referral", 2000, ["proposal", "negotiation"], "r1", "c@x.com")  # 1200
        w = self._mk("referral", 500, ["proposal", "negotiation", "won"], "r2", "d@x.com")
        l = self._mk("referral", 700, ["lost"], "r2", "e@x.com")  # e lands on r2: load 1 < 2
        self.assertEqual(self.crm.forecast(), {"open": 3, "weighted": 100 + 299 + 1200, "won": 500})

    def test_forecast_no_log_and_uses_discounted_amount(self):
        oid = self._mk("referral", 1000, [], "r1", "a@x.com")
        self.crm.discount(oid, 10, "r1")  # 900
        n = len(self.crm.log)
        fc = self.crm.forecast()
        self.assertEqual(fc["weighted"], 900 * 10 // 100)
        self.assertEqual(len(self.crm.log), n)  # forecast logs nothing


class TestAtomicityAndLog(unittest.TestCase):
    def test_failed_advance_changes_nothing(self):
        crm = CRM(std_reps())
        lid = crm.add_lead("a@b.com", "A", "referral", "m1")
        crm.qualify(lid, "r1")
        oid = crm.convert(lid, 100, "r1")
        snapshot = (dict(crm.leads[lid]), dict(crm.opps[oid]), list(crm.log))
        with self.assertRaises(ValueError):
            crm.advance(oid, "won", "r1")
        self.assertEqual(crm.leads[lid], snapshot[0])
        self.assertEqual(crm.opps[oid], snapshot[1])
        self.assertEqual(crm.log, snapshot[2])

    def test_log_is_exact_sequence(self):
        crm = CRM(std_reps())
        lid = crm.add_lead("a@b.com", "A", "referral", "m1")
        crm.qualify(lid, "r1")
        oid = crm.convert(lid, 100, "r1")
        crm.advance(oid, "proposal", "r1")
        crm.discount(oid, 10, "r1")
        crm.advance(oid, "lost", "r1")
        self.assertEqual(crm.log, [
            ("add_lead", "L1", "m1"),
            ("qualify", "L1", "r1"),
            ("convert", "O1", "r1"),
            ("advance", "O1", "r1"),
            ("discount", "O1", "r1"),
            ("advance", "O1", "r1"),
        ])

    def test_load_definition(self):
        # load counts new/qualified leads + open opps, not converted leads
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 2},
            {"id": "m1", "role": "manager", "capacity": 5},
        ])
        l1 = crm.add_lead("a@x.com", "A", "referral", "m1")
        self.assertEqual(crm.leads[l1]["owner"], "r1")
        l2 = crm.add_lead("b@x.com", "B", "referral", "m1")  # r1 load 1 < 2
        self.assertEqual(crm.leads[l2]["owner"], "r1")
        l3 = crm.add_lead("c@x.com", "C", "referral", "m1")  # load 2 -> full -> waiting
        self.assertIsNone(crm.leads[l3]["owner"])
        crm.qualify(l1, "r1")
        oid = crm.convert(l1, 100, "r1")  # converted lead drops, open opp counts: load still 2
        l4 = crm.add_lead("d@x.com", "D", "referral", "m1")
        self.assertIsNone(crm.leads[l4]["owner"])
        crm.advance(oid, "lost", "r1")  # frees one slot -> oldest waiting is L3
        self.assertEqual(crm.leads[l3]["owner"], "r1")
        self.assertEqual(crm.leads[l4]["owner"], None)


if __name__ == "__main__":
    unittest.main()
