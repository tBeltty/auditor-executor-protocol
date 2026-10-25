import unittest

from crm import CRM, DuplicateLeadError


def make_crm(reps=None):
    if reps is None:
        reps = [
            {"id": "R1", "role": "rep", "capacity": 5},
            {"id": "M1", "role": "manager", "capacity": 0},
        ]
    return CRM(reps)


class TestActorAndValidation(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()

    def test_unknown_actor_permission_error_first(self):
        # Actor check runs before everything else, even argument validation.
        with self.assertRaises(PermissionError):
            self.crm.add_lead("not an email", "", "bogus", "ghost")
        with self.assertRaises(PermissionError):
            self.crm.qualify("L1", "ghost")
        with self.assertRaises(PermissionError):
            self.crm.convert("L1", -5, "ghost")
        with self.assertRaises(PermissionError):
            self.crm.advance("O1", "won", "ghost")
        with self.assertRaises(PermissionError):
            self.crm.discount("O1", 99, "ghost")
        with self.assertRaises(PermissionError):
            self.crm.transfer("O1", "R1", "ghost")
        self.assertEqual(self.crm.log, [])
        self.assertEqual(self.crm.leads, {})

    def test_email_validation(self):
        bad = ["x@gmail", "a@@b.com", "@gmail.com", "u@.com", "u@com.",
               "noatsign.com", "  "]
        for e in bad:
            with self.assertRaises(ValueError):
                self.crm.add_lead(e, "N", "web", "R1")
        with self.assertRaises(ValueError):
            self.crm.add_lead(123, "N", "web", "R1")
        self.assertEqual(self.crm.log, [])
        self.assertEqual(self.crm.leads, {})

    def test_email_normalized(self):
        lid = self.crm.add_lead("  Ada@Acme.COM ", " Ada ", "web", "R1")
        self.assertEqual(self.crm.leads[lid]["email"], "ada@acme.com")
        self.assertEqual(self.crm.leads[lid]["name"], "Ada")

    def test_name_and_source_validation(self):
        with self.assertRaises(ValueError):
            self.crm.add_lead("a@b.com", "   ", "web", "R1")
        with self.assertRaises(ValueError):
            self.crm.add_lead("a@b.com", 7, "web", "R1")
        with self.assertRaises(ValueError):
            self.crm.add_lead("a@b.com", "N", "phone", "R1")

    def test_duplicate_lead_error(self):
        lid1 = self.crm.add_lead("a@b.com", "First", "web", "R1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            self.crm.add_lead(" A@B.COM ", "Second", "web", "R1")
        self.assertEqual(ctx.exception.existing_id, lid1)
        # failed call changed nothing
        self.assertEqual(len(self.crm.leads), 1)
        lid2 = self.crm.add_lead("c@d.com", "Third", "web", "R1")
        self.assertEqual(lid2, "L2")  # failed creations don't consume numbers

    def test_scoring(self):
        cases = [
            ("w@gmail.com", "web", 10),
            ("r@gmail.com", "referral", 30),
            ("e@gmail.com", "event", 20),
            ("w@acme.com", "web", 25),
            ("r@acme.com", "referral", 45),
            ("e@acme.com", "event", 35),
        ]
        for email, source, expected in cases:
            lid = self.crm.add_lead(email, "N", source, "R1")
            self.assertEqual(self.crm.leads[lid]["score"], expected)

    def test_log_on_success(self):
        lid = self.crm.add_lead("a@b.com", "N", "web", "R1")
        self.assertEqual(self.crm.log, [("add_lead", lid, "R1")])


class TestQualifyConvert(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()

    def test_qualify_flow(self):
        lid = self.crm.add_lead("a@acme.com", "A", "event", "R1")  # score 35
        self.crm.qualify(lid, "R1")
        self.assertEqual(self.crm.leads[lid]["status"], "qualified")
        n = len(self.crm.log)
        with self.assertRaises(ValueError):
            self.crm.qualify(lid, "M1")  # already qualified
        self.assertEqual(len(self.crm.log), n)  # failed call logs nothing
        self.assertEqual(self.crm.log[-1], ("qualify", lid, "R1"))

    def test_qualify_low_score(self):
        lid = self.crm.add_lead("a@gmail.com", "A", "web", "R1")  # score 10
        with self.assertRaises(ValueError):
            self.crm.qualify(lid, "R1")
        self.assertEqual(self.crm.leads[lid]["status"], "new")

    def test_qualify_permission(self):
        crm = CRM([
            {"id": "R1", "role": "rep", "capacity": 5},
            {"id": "R2", "role": "rep", "capacity": 5},
        ])
        lid = crm.add_lead("a@acme.com", "A", "event", "R2")
        self.assertEqual(crm.leads[lid]["owner"], "R1")  # tie on load -> smallest id
        with self.assertRaises(PermissionError):
            crm.qualify(lid, "R2")
        with self.assertRaises(ValueError):
            crm.qualify("L99", "R1")

    def test_manager_can_qualify_unowned_lead(self):
        crm = CRM([
            {"id": "R1", "role": "rep", "capacity": 0},
            {"id": "M1", "role": "manager", "capacity": 0},
        ])
        lid = crm.add_lead("a@acme.com", "A", "event", "R1")
        self.assertIsNone(crm.leads[lid]["owner"])
        crm.qualify(lid, "M1")
        self.assertEqual(crm.leads[lid]["status"], "qualified")

    def _qualified_lead(self, crm=None, email="a@acme.com"):
        crm = crm or self.crm
        lid = crm.add_lead(email, "A", "referral", "R1")
        crm.qualify(lid, "R1")
        return crm, lid

    def test_convert_amount_validation(self):
        crm, lid = self._qualified_lead()
        n = len(crm.log)
        for bad in (True, False, 0, -5, 10.5, "100"):
            with self.assertRaises(ValueError):
                crm.convert(lid, bad, "R1")
        with self.assertRaises(ValueError):
            crm.convert("L99", 100, "R1")
        self.assertEqual(len(crm.log), n)
        self.assertNotIn("O1", crm.opps)

    def test_convert_permission_and_status(self):
        crm = CRM([
            {"id": "R1", "role": "rep", "capacity": 5},
            {"id": "R2", "role": "rep", "capacity": 5},
            {"id": "M1", "role": "manager", "capacity": 0},
        ])
        lid = self._qualified_lead(crm)[1]  # owned by R1
        self.assertEqual(crm.leads[lid]["owner"], "R1")
        with self.assertRaises(PermissionError):
            crm.convert(lid, 100, "R2")  # R2: neither owner nor manager
        # unqualified lead: status check (4) after permission (3)
        l_b = crm.add_lead("b@acme.com", "B", "referral", "M1")
        self.assertEqual(crm.leads[l_b]["owner"], "R2")  # R2 has lower load
        with self.assertRaises(ValueError):
            crm.convert(l_b, 100, "R2")  # still "new"
        # qualified lead converts to O1, ids count successful conversions from 1
        crm.qualify(l_b, "M1")
        oid = crm.convert(l_b, 500, "M1")  # manager allowed
        self.assertEqual(oid, "O1")
        self.assertEqual(crm.opps["O1"], {
            "id": "O1", "lead_id": l_b, "owner": "R2",
            "amount": 500, "original_amount": 500, "stage": "prospect",
        })
        self.assertEqual(crm.leads[l_b]["status"], "converted")
        self.assertEqual(crm.log[-1], ("convert", "O1", "M1"))
        with self.assertRaises(ValueError):
            crm.convert(l_b, 500, "R2")  # already converted

    def test_convert_requires_owner(self):
        crm = CRM([
            {"id": "R1", "role": "rep", "capacity": 0},
            {"id": "M1", "role": "manager", "capacity": 0},
        ])
        lid = crm.add_lead("a@acme.com", "A", "referral", "M1")
        self.assertIsNone(crm.leads[lid]["owner"])
        crm.qualify(lid, "M1")
        with self.assertRaises(ValueError):
            crm.convert(lid, 100, "M1")  # manager passes permission, no owner


class TestCapacityAndQueue(unittest.TestCase):
    def test_lowest_load_then_smallest_id(self):
        crm = CRM([
            {"id": "R2", "role": "rep", "capacity": 1},
            {"id": "R1", "role": "rep", "capacity": 2},
        ])
        l1 = crm.add_lead("a@x.com", "A", "web", "R1")
        l2 = crm.add_lead("b@x.com", "B", "web", "R1")
        l3 = crm.add_lead("c@x.com", "C", "web", "R1")
        l4 = crm.add_lead("d@x.com", "D", "web", "R1")
        self.assertEqual(crm.leads[l1]["owner"], "R1")  # tie load 0, "R1" < "R2"
        self.assertEqual(crm.leads[l2]["owner"], "R2")  # R2 load 0 < R1 load 1
        self.assertEqual(crm.leads[l3]["owner"], "R1")  # R2 at capacity
        self.assertIsNone(crm.leads[l4]["owner"])       # all reps full -> queue

    def test_queue_frees_on_advance_to_won(self):
        crm = CRM([{"id": "R1", "role": "rep", "capacity": 1}])
        l1 = crm.add_lead("a@x.com", "A", "referral", "R1")
        l2 = crm.add_lead("b@x.com", "B", "web", "R1")  # queued
        crm.qualify(l1, "R1")
        oid = crm.convert(l1, 100, "R1")
        # converted lead drops from load but the open opp keeps slot at 1
        self.assertIsNone(crm.leads[l2]["owner"])
        crm.advance(oid, "proposal", "R1")
        crm.advance(oid, "negotiation", "R1")
        crm.advance(oid, "won", "R1")
        self.assertEqual(crm.leads[l2]["owner"], "R1")
        self.assertEqual(crm.leads[l2]["status"], "new")
        self.assertEqual(crm.log[-2:], [
            ("advance", oid, "R1"),
            ("assign", l2, "system"),
        ])

    def test_lost_also_frees_slot(self):
        crm = CRM([{"id": "R1", "role": "rep", "capacity": 1}])
        l1 = crm.add_lead("a@x.com", "A", "referral", "R1")
        l2 = crm.add_lead("b@x.com", "B", "web", "R1")  # queued
        crm.qualify(l1, "R1")
        oid = crm.convert(l1, 100, "R1")
        crm.advance(oid, "lost", "R1")
        self.assertEqual(crm.opps[oid]["stage"], "lost")
        self.assertEqual(crm.log[-2:], [
            ("advance", oid, "R1"),
            ("assign", l2, "system"),
        ])

    def test_stage_transitions(self):
        crm = CRM([{"id": "R1", "role": "rep", "capacity": 5}])
        l1 = crm.add_lead("a@x.com", "A", "referral", "R1")
        crm.qualify(l1, "R1")
        oid = crm.convert(l1, 1000, "R1")
        n = len(crm.log)
        with self.assertRaises(ValueError):
            crm.advance(oid, "negotiation", "R1")  # skips proposal
        with self.assertRaises(ValueError):
            crm.advance(oid, "won", "R1")
        with self.assertRaises(ValueError):
            crm.advance(oid, "bogus", "R1")
        with self.assertRaises(ValueError):
            crm.advance(oid, "prospect", "R1")  # not a forward move
        with self.assertRaises(PermissionError):
            crm.advance(oid, "proposal", "M2")  # unknown actor checked first
        self.assertEqual(crm.opps[oid]["stage"], "prospect")
        self.assertEqual(len(crm.log), n)
        crm.advance(oid, "lost", "R1")
        with self.assertRaises(ValueError):
            crm.advance(oid, "lost", "R1")  # final
        with self.assertRaises(ValueError):
            crm.advance("O404", "lost", "R1")

    def test_negotiation_manager_gate(self):
        crm = CRM([
            {"id": "R1", "role": "rep", "capacity": 5},
            {"id": "M1", "role": "manager", "capacity": 0},
        ])
        l1 = crm.add_lead("a@x.com", "A", "referral", "R1")
        crm.qualify(l1, "R1")
        big = crm.convert(l1, 50001, "R1")
        crm.advance(big, "proposal", "R1")
        n = len(crm.log)
        with self.assertRaises(PermissionError):
            crm.advance(big, "negotiation", "R1")
        self.assertEqual(crm.opps[big]["stage"], "proposal")
        self.assertEqual(len(crm.log), n)
        crm.advance(big, "negotiation", "M1")  # manager allowed
        l2 = crm.add_lead("b@x.com", "B", "referral", "R1")
        crm.qualify(l2, "R1")
        small = crm.convert(l2, 50000, "R1")  # exactly 50000: rep allowed
        crm.advance(small, "proposal", "R1")
        crm.advance(small, "negotiation", "R1")


class TestDiscount(unittest.TestCase):
    def setUp(self):
        self.crm = CRM([
            {"id": "R1", "role": "rep", "capacity": 5},
            {"id": "M1", "role": "manager", "capacity": 0},
        ])
        l1 = self.crm.add_lead("a@x.com", "A", "referral", "R1")
        self.crm.qualify(l1, "R1")
        self.oid = self.crm.convert(l1, 100000, "R1")

    def test_pct_validation(self):
        for bad in (0, 31, -5, True, False, 10.5, "10"):
            with self.assertRaises(ValueError):
                self.crm.discount(self.oid, bad, "M1")
        with self.assertRaises(ValueError):
            self.crm.discount("O404", 10, "M1")

    def test_role_limits(self):
        with self.assertRaises(PermissionError):
            self.crm.discount(self.oid, 11, "R1")
        self.crm.discount(self.oid, 10, "R1")  # rep limit 10
        self.assertEqual(self.crm.opps[self.oid]["amount"], 90000)
        self.crm.discount(self.oid, 10, "M1")  # manager: 90000 -> 81000
        self.assertEqual(self.crm.opps[self.oid]["amount"], 81000)
        self.assertEqual(self.crm.log[-1], ("discount", self.oid, "M1"))

    def test_permission_before_final_stage(self):
        # check 3 (owner-or-manager) fires before check 4 (final stage)
        self.crm.advance(self.oid, "proposal", "R1")
        self.crm.advance(self.oid, "negotiation", "M1")
        self.crm.advance(self.oid, "won", "R1")
        with self.assertRaises(ValueError):  # R1 is the owner, stage final -> ValueError
            self.crm.discount(self.oid, 5, "R1")

    def test_cumulative_cap(self):
        self.crm.discount(self.oid, 20, "M1")  # -> 80000
        n = len(self.crm.log)
        with self.assertRaises(ValueError):  # 68000 < 70% of 100000
            self.crm.discount(self.oid, 15, "M1")
        self.assertEqual(self.crm.opps[self.oid]["amount"], 80000)
        self.assertEqual(len(self.crm.log), n)
        self.crm.discount(self.oid, 12, "M1")  # -> 70400, still >= 70%
        self.assertEqual(self.crm.opps[self.oid]["amount"], 70400)


class TestTransfer(unittest.TestCase):
    def make_case(self):
        crm = CRM([
            {"id": "R1", "role": "rep", "capacity": 5},
            {"id": "R2", "role": "rep", "capacity": 5},
            {"id": "M1", "role": "manager", "capacity": 0},
        ])
        l1 = crm.add_lead("a@x.com", "A", "referral", "R1")
        crm.qualify(l1, "R1")
        oid = crm.convert(l1, 100, "R1")
        return crm, oid

    def test_transfer_rules(self):
        crm, oid = self.make_case()
        with self.assertRaises(PermissionError):
            crm.transfer(oid, "R2", "R1")  # actor must be manager
        with self.assertRaises(ValueError):
            crm.transfer(oid, "M1", "M1")  # target must be a rep
        with self.assertRaises(ValueError):
            crm.transfer(oid, "nobody", "M1")
        with self.assertRaises(ValueError):
            crm.transfer(oid, "R1", "M1")  # same owner
        with self.assertRaises(ValueError):
            crm.transfer("O404", "R2", "M1")
        self.assertEqual(crm.opps[oid]["owner"], "R1")
        crm.transfer(oid, "R2", "M1")
        self.assertEqual(crm.opps[oid]["owner"], "R2")
        self.assertEqual(crm.log[-1], ("transfer", oid, "M1"))
        crm.advance(oid, "lost", "R2")  # new owner can act
        with self.assertRaises(ValueError):
            crm.transfer(oid, "R1", "M1")  # final stage

    def test_transfer_capacity_check(self):
        crm = CRM([
            {"id": "R1", "role": "rep", "capacity": 5},
            {"id": "R2", "role": "rep", "capacity": 0},
            {"id": "M1", "role": "manager", "capacity": 0},
        ])
        l1 = crm.add_lead("a@x.com", "A", "referral", "R1")
        crm.qualify(l1, "R1")
        oid = crm.convert(l1, 100, "R1")
        with self.assertRaises(ValueError):
            crm.transfer(oid, "R2", "M1")  # target at capacity

    def test_transfer_frees_prev_owner_queue_empty(self):
        # With an empty waiting queue the freeing step is a silent no-op.
        crm, oid = self.make_case()
        crm.transfer(oid, "R2", "M1")
        self.assertEqual(crm.log.count(("transfer", oid, "M1")), 1)
        self.assertNotIn("assign", [e[0] for e in crm.log])

    def test_queue_nonempty_means_all_reps_full(self):
        # Spec invariant: while a lead waits, every rep is at capacity, so a
        # transfer target never has room at the same moment a queue exists.
        crm = CRM([
            {"id": "R1", "role": "rep", "capacity": 1},
            {"id": "M1", "role": "manager", "capacity": 0},
        ])
        l1 = crm.add_lead("a@x.com", "A", "referral", "R1")
        crm.qualify(l1, "R1")
        oid = crm.convert(l1, 100, "R1")
        l2 = crm.add_lead("b@x.com", "B", "web", "M1")
        self.assertIsNone(crm.leads[l2]["owner"])  # queued behind open opp
        # freeing happens via advance on the *owner*: closed opp -> assign
        crm.advance(oid, "proposal", "R1")
        crm.advance(oid, "negotiation", "R1")
        crm.advance(oid, "won", "R1")
        self.assertEqual(crm.leads[l2]["owner"], "R1")


class TestForecast(unittest.TestCase):
    def test_forecast(self):
        crm = CRM([{"id": "R1", "role": "rep", "capacity": 9}])
        self.assertEqual(crm.forecast(), {"open": 0, "weighted": 0, "won": 0})
        for email, amount, steps in [
            ("a@x.com", 1000, []),
            ("b@x.com", 2000, ["proposal"]),
            ("c@x.com", 4000, ["proposal", "negotiation"]),
            ("d@x.com", 8000, ["proposal", "negotiation", "won"]),
            ("e@x.com", 16000, ["lost"]),
        ]:
            lid = crm.add_lead(email, "N", "referral", "R1")
            crm.qualify(lid, "R1")
            oid = crm.convert(lid, amount, "R1")
            for st in steps:
                crm.advance(oid, st, "R1")
        snapshot = list(crm.log)
        self.assertEqual(crm.forecast(), {
            "open": 3,
            "weighted": 100 + 600 + 2400,  # 1000*.10 + 2000*.30 + 4000*.60
            "won": 8000,
        })
        # forecast logs nothing and mutates nothing
        self.assertEqual(crm.log, snapshot)


class TestReviewRegressions(unittest.TestCase):
    """Added during spec review: behaviours the original suite left uncovered."""

    def test_add_lead_check_order_before_duplicate(self):
        crm = make_crm()
        lid = crm.add_lead("dup@acme.com", "A", "web", "R1")
        # name (check 2) and source (check 3) fire before the duplicate check (4)
        with self.assertRaises(ValueError):
            crm.add_lead("dup@acme.com", "   ", "web", "R1")
        with self.assertRaises(ValueError):
            crm.add_lead("dup@acme.com", "B", "phone", "R1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            crm.add_lead(" DUP@ACME.COM ", "C", "web", "R1")
        self.assertEqual(ctx.exception.existing_id, lid)
        self.assertEqual(len(crm.leads), 1)
        self.assertEqual(len(crm.log), 1)

    def test_negotiation_gate_uses_current_amount(self):
        crm = CRM([{"id": "R1", "role": "rep", "capacity": 5},
                   {"id": "M1", "role": "manager", "capacity": 0}])
        lid = crm.add_lead("a@x.com", "A", "referral", "R1")
        crm.qualify(lid, "R1")
        oid = crm.convert(lid, 60000, "R1")
        crm.advance(oid, "proposal", "R1")
        with self.assertRaises(PermissionError):
            crm.advance(oid, "negotiation", "R1")  # 60000 > 50000
        crm.discount(oid, 20, "M1")  # -> 48000, under the threshold
        crm.advance(oid, "negotiation", "R1")
        self.assertEqual(crm.opps[oid]["stage"], "negotiation")

    def test_queue_frees_one_slot_fifo(self):
        crm = CRM([{"id": "R1", "role": "rep", "capacity": 2}])
        l1 = crm.add_lead("1@x.com", "1", "referral", "R1")
        l2 = crm.add_lead("2@x.com", "2", "web", "R1")   # R1 at capacity
        crm.qualify(l1, "R1")
        oid = crm.convert(l1, 100, "R1")  # converted lead + open opp = load 2
        l3 = crm.add_lead("3@x.com", "3", "web", "R1")   # queued first
        l4 = crm.add_lead("4@x.com", "4", "web", "R1")   # queued second
        for st in ("proposal", "negotiation", "won"):
            crm.advance(oid, st, "R1")
        self.assertEqual(crm.leads[l3]["owner"], "R1")  # oldest gets the slot
        self.assertIsNone(crm.leads[l4]["owner"])
        self.assertEqual(crm.log[-1], ("assign", l3, "system"))

    def test_non_string_arguments_raise_specified_errors(self):
        # Unhashable / wrong-type ids must raise the spec's exception, not TypeError.
        crm = make_crm()
        lid = crm.add_lead("a@x.com", "A", "referral", "R1")
        crm.qualify(lid, "R1")
        oid = crm.convert(lid, 100, "R1")
        n = len(crm.log)
        with self.assertRaises(PermissionError):
            crm.qualify(lid, ["ghost"])        # actor is not a known user id
        with self.assertRaises(ValueError):
            crm.qualify(["L1"], "R1")          # unknown lead
        with self.assertRaises(ValueError):
            crm.add_lead("ok@x.com", "N", ["web"], "R1")  # invalid source
        with self.assertRaises(ValueError):
            crm.advance(oid, ["won"], "R1")    # invalid stage
        with self.assertRaises(ValueError):
            crm.transfer(oid, ["R9"], "M1")    # target is not a rep id
        self.assertEqual(len(crm.log), n)      # none of the failures logged


if __name__ == "__main__":
    unittest.main()
