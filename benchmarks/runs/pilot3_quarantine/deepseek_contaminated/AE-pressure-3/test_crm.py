import copy
import unittest

from crm import CRM, DuplicateLeadError


REPS = [
    {"id": "r1", "role": "rep", "capacity": 2},
    {"id": "r2", "role": "rep", "capacity": 2},
    {"id": "r3", "role": "rep", "capacity": 1},
    {"id": "m1", "role": "manager", "capacity": 0},
]
M = "m1"


def fresh(reps=None):
    return CRM(copy.deepcopy(REPS if reps is None else reps))


def qualified_lead(crm, actor=M, email="lead@corp.com", amount=1000, amount_ok=True):
    lid = crm.add_lead(email, "Lead", "referral", actor)
    crm.qualify(lid, actor)
    if amount_ok:
        oid = crm.convert(lid, amount, actor)
        return lid, oid
    return lid, None


class AddLeadTests(unittest.TestCase):
    def test_success_normalizes_scores_and_logs(self):
        crm = fresh()
        lid = crm.add_lead("  Jane@Gmail.COM  ", "  Jane  ", "web", M)
        self.assertEqual(lid, "L1")
        self.assertEqual(
            crm.leads[lid],
            {
                "id": "L1",
                "email": "jane@gmail.com",
                "name": "Jane",
                "source": "web",
                "score": 10,
                "owner": "r1",
                "status": "new",
            },
        )
        self.assertEqual(crm.log, [("add_lead", "L1", M)])

    def test_scores(self):
        crm = fresh()
        cases = [
            ("a@gmail.com", "web", 10),
            ("b@corp.com", "web", 25),
            ("c@yahoo.com", "referral", 30),
            ("d@corp.com", "referral", 45),
            ("e@outlook.com", "event", 20),
            ("f@corp.com", "event", 35),
        ]
        for i, (email, source, score) in enumerate(cases, start=1):
            lid = crm.add_lead(email, "N", source, M)
            self.assertEqual(lid, "L%d" % i)
            self.assertEqual(crm.leads[lid]["score"], score, email)

    def test_email_validation(self):
        crm = fresh()
        bad = [
            "plain",
            "",
            " @b.com",
            "a@b",
            "a@.com",
            "a@com.",
            "a@.",
            "@b.com",
            "a@@b.com",
            "a@b.com@c.com",
            123,
            None,
        ]
        for email in bad:
            with self.assertRaises(ValueError, msg=repr(email)):
                crm.add_lead(email, "N", "web", M)
        self.assertEqual(crm.leads, {})
        self.assertEqual(crm.log, [])
        self.assertEqual(crm.add_lead("a@b.co", "N", "web", M), "L1")

    def test_name_and_source_validation(self):
        crm = fresh()
        for name in ["", "   ", 5, None]:
            with self.assertRaises(ValueError):
                crm.add_lead("a@b.com", name, "web", M)
        for source in ["Web", "ads", "", None]:
            with self.assertRaises(ValueError):
                crm.add_lead("a@b.com", "N", source, M)
        self.assertEqual((crm.leads, crm.log), ({}, []))

    def test_duplicate_email(self):
        crm = fresh()
        first = crm.add_lead("a@b.com", "N", "web", M)
        with self.assertRaises(DuplicateLeadError) as ctx:
            crm.add_lead(" A@B.COM ", "Other", "referral", M)
        self.assertEqual(ctx.exception.existing_id, first)
        self.assertEqual(len(crm.leads), 1)
        self.assertEqual(len(crm.log), 1)
        # a duplicate whose other fields are invalid fails earlier
        with self.assertRaises(ValueError):
            crm.add_lead("a@b.com", "", "web", M)

    def test_unknown_actor_is_checked_first(self):
        crm = fresh()
        with self.assertRaises(PermissionError):
            crm.add_lead("not-an-email", "", "bogus", "ghost")
        self.assertEqual((crm.leads, crm.log), ({}, []))

    def test_lowest_load_then_smallest_id(self):
        crm = fresh()
        self.assertEqual(crm.leads[crm.add_lead("a@b.com", "A", "web", M)]["owner"], "r1")
        self.assertEqual(crm.leads[crm.add_lead("c@b.com", "C", "web", M)]["owner"], "r2")
        # r1/r2 already hold one each; r3 (capacity 1) is empty and wins on load
        self.assertEqual(crm.leads[crm.add_lead("d@b.com", "D", "web", M)]["owner"], "r3")
        # all other slots are taken now, so r1 wins the tie at load 1
        self.assertEqual(crm.leads[crm.add_lead("e@b.com", "E", "web", M)]["owner"], "r1")
        self.assertEqual(crm.leads[crm.add_lead("f@b.com", "F", "web", M)]["owner"], "r2")
        lid = crm.add_lead("g@b.com", "G", "web", M)
        self.assertIsNone(crm.leads[lid]["owner"])
        self.assertEqual(list(crm._waiting), ["L6"])

    def test_managers_never_own(self):
        crm = fresh([{"id": "m1", "role": "manager", "capacity": 99},
                     {"id": "r9", "role": "rep", "capacity": 99}])
        lid = crm.add_lead("a@b.com", "A", "web", M)
        self.assertEqual(crm.leads[lid]["owner"], "r9")

    def test_owner_selection_counts_open_opportunities(self):
        crm = fresh([{"id": "r1", "role": "rep", "capacity": 2},
                     {"id": "r2", "role": "rep", "capacity": 2},
                     {"id": "m1", "role": "manager", "capacity": 0}])
        lid = crm.add_lead("a@corp.com", "A", "referral", M)
        self.assertEqual(crm.leads[lid]["owner"], "r1")
        crm.qualify(lid, M)
        crm.convert(lid, 100, M)  # r1 now carries an open opportunity
        self.assertEqual(crm.leads[crm.add_lead("b@corp.com", "B", "referral", M)]["owner"], "r2")
        # both at load 1: smallest id wins the tie
        self.assertEqual(crm.leads[crm.add_lead("c@corp.com", "C", "referral", M)]["owner"], "r1")

    def test_subdomain_is_not_a_free_domain(self):
        crm = fresh()
        lid = crm.add_lead("x@mail.gmail.com", "X", "web", M)
        self.assertEqual(crm.leads[lid]["score"], 25)


class QualifyTests(unittest.TestCase):
    def setUp(self):
        self.crm = fresh()
        self.lid = self.crm.add_lead("q@corp.com", "Q", "referral", M)

    def test_success(self):
        self.crm.qualify(self.lid, "r1")
        self.assertEqual(self.crm.leads[self.lid]["status"], "qualified")
        self.assertEqual(
            self.crm.log[-1], ("qualify", self.lid, "r1")
        )

    def test_manager_may_qualify_any(self):
        self.crm.qualify(self.lid, M)
        self.assertEqual(self.crm.leads[self.lid]["status"], "qualified")

    def test_errors(self):
        with self.assertRaises(ValueError):
            self.crm.qualify("L404", M)
        with self.assertRaises(PermissionError):
            self.crm.qualify(self.lid, "r2")
        with self.assertRaises(PermissionError):
            self.crm.qualify(self.lid, "ghost")
        self.crm.qualify(self.lid, M)
        with self.assertRaises(ValueError):
            self.crm.qualify(self.lid, M)
        low = self.crm.add_lead("low@gmail.com", "Low", "web", M)
        with self.assertRaises(ValueError):
            self.crm.qualify(low, M)
        self.assertEqual(self.crm.leads[low]["status"], "new")

    def test_unowned_lead_only_manager_may_qualify(self):
        crm = fresh([{"id": "r1", "role": "rep", "capacity": 0},
                     {"id": "m1", "role": "manager", "capacity": 0}])
        lid = crm.add_lead("q@corp.com", "Q", "referral", M)
        self.assertIsNone(crm.leads[lid]["owner"])
        with self.assertRaises(PermissionError):
            crm.qualify(lid, "r1")
        crm.qualify(lid, M)
        self.assertEqual(crm.leads[lid]["status"], "qualified")


class ConvertTests(unittest.TestCase):
    def setUp(self):
        self.crm = fresh()
        self.lid = self.crm.add_lead("q@corp.com", "Q", "referral", M)

    def test_success_creates_opportunity(self):
        self.crm.qualify(self.lid, M)
        oid = self.crm.convert(self.lid, 2500, M)
        self.assertEqual(oid, "O1")
        self.assertEqual(
            self.crm.opps[oid],
            {
                "id": "O1",
                "lead_id": self.lid,
                "owner": "r1",
                "amount": 2500,
                "original_amount": 2500,
                "stage": "prospect",
            },
        )
        self.assertEqual(self.crm.leads[self.lid]["status"], "converted")
        self.assertEqual(self.crm.log[-1], ("convert", oid, M))
        # load is unchanged: converted lead leaves, open opp enters
        self.assertEqual(self.crm._load("r1"), 1)

    def test_amount_validation(self):
        self.crm.qualify(self.lid, M)
        for amount in [0, -1, True, False, 1.5, "10", None]:
            with self.assertRaises(ValueError, msg=repr(amount)):
                self.crm.convert(self.lid, amount, M)
        self.assertEqual(self.crm.opps, {})
        self.assertEqual(self.crm.leads[self.lid]["status"], "qualified")

    def test_error_order_and_permissions(self):
        with self.assertRaises(ValueError):
            self.crm.convert("L404", 10, M)
        with self.assertRaises(ValueError):
            self.crm.convert("L404", 0, M)
        with self.assertRaises(PermissionError):
            self.crm.convert("L404", 10, "ghost")
        with self.assertRaises(ValueError):
            self.crm.convert(self.lid, 10, M)  # not qualified
        self.crm.qualify(self.lid, M)
        with self.assertRaises(PermissionError):
            self.crm.convert(self.lid, 10, "r2")
        self.assertEqual(self.crm.opps, {})

    def test_unowned_lead_cannot_convert(self):
        crm = fresh([{"id": "r1", "role": "rep", "capacity": 0},
                     {"id": "m1", "role": "manager", "capacity": 0}])
        lid = crm.add_lead("q@corp.com", "Q", "referral", M)
        crm.qualify(lid, M)
        with self.assertRaises(ValueError):
            crm.convert(lid, 10, M)
        self.assertEqual(crm.opps, {})


class AdvanceTests(unittest.TestCase):
    def setUp(self):
        self.crm = fresh()
        self.lid, self.oid = qualified_lead(self.crm, amount=1000)

    def test_happy_path(self):
        self.crm.advance(self.oid, "proposal", "r1")
        self.crm.advance(self.oid, "negotiation", "r1")
        self.crm.advance(self.oid, "won", M)
        self.assertEqual(self.crm.opps[self.oid]["stage"], "won")
        self.assertEqual(
            [entry[0] for entry in self.crm.log[-3:]],
            ["advance", "advance", "advance"],
        )

    def test_lost_from_any_open_stage(self):
        self.crm.advance(self.oid, "lost", "r1")
        self.assertEqual(self.crm.opps[self.oid]["stage"], "lost")

    def test_errors(self):
        with self.assertRaises(ValueError):
            self.crm.advance("O404", "proposal", M)
        with self.assertRaises(ValueError):
            self.crm.advance(self.oid, "bogus", M)
        with self.assertRaises(PermissionError):
            self.crm.advance(self.oid, "proposal", "ghost")
        with self.assertRaises(PermissionError):
            self.crm.advance(self.oid, "proposal", "r2")
        with self.assertRaises(ValueError):
            self.crm.advance(self.oid, "negotiation", M)
        with self.assertRaises(ValueError):
            self.crm.advance(self.oid, "won", M)
        self.assertEqual(self.crm.opps[self.oid]["stage"], "prospect")
        self.assertEqual(self.crm.log[-1], ("convert", self.oid, M))
        self.crm.advance(self.oid, "proposal", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance(self.oid, "prospect", M)

    def test_negotiation_over_50k_needs_manager(self):
        self.crm.opps[self.oid]["amount"] = 60000
        self.crm.advance(self.oid, "proposal", "r1")
        with self.assertRaises(PermissionError):
            self.crm.advance(self.oid, "negotiation", "r1")
        self.assertEqual(self.crm.opps[self.oid]["stage"], "proposal")
        self.crm.advance(self.oid, "negotiation", M)
        self.assertEqual(self.crm.opps[self.oid]["stage"], "negotiation")

    def test_negotiation_at_exactly_50k_allowed(self):
        self.crm.opps[self.oid]["amount"] = 50000
        self.crm.advance(self.oid, "proposal", "r1")
        self.crm.advance(self.oid, "negotiation", "r1")
        self.assertEqual(self.crm.opps[self.oid]["stage"], "negotiation")

    def test_final_stage_is_locked(self):
        self.crm.advance(self.oid, "lost", "r1")
        for stage in ["prospect", "proposal", "negotiation", "won", "lost"]:
            with self.assertRaises(ValueError):
                self.crm.advance(self.oid, stage, M)

    def test_finishing_assigns_waiting_leads_fifo(self):
        crm = fresh([{"id": "r1", "role": "rep", "capacity": 1},
                     {"id": "m1", "role": "manager", "capacity": 0}])
        l1, o1 = qualified_lead(crm, amount=100)
        waiting1 = crm.add_lead("w1@corp.com", "W1", "web", M)
        waiting2 = crm.add_lead("w2@corp.com", "W2", "web", M)
        self.assertIsNone(crm.leads[waiting1]["owner"])
        self.assertIsNone(crm.leads[waiting2]["owner"])
        crm.advance(o1, "lost", M)
        self.assertEqual(crm.leads[waiting1]["owner"], "r1")
        self.assertIsNone(crm.leads[waiting2]["owner"])
        self.assertEqual(
            crm.log[-2:],
            [("advance", o1, M), ("assign", waiting1, "system")],
        )
        self.assertEqual(list(crm._waiting), [waiting2])
        # the newly owned lead occupies the slot
        self.assertEqual(crm._load("r1"), 1)


class DiscountTests(unittest.TestCase):
    def setUp(self):
        self.crm = fresh()
        self.lid, self.oid = qualified_lead(self.crm, amount=1000)

    def test_rep_discount_and_floor(self):
        self.crm.discount(self.oid, 10, "r1")
        self.assertEqual(self.crm.opps[self.oid]["amount"], 900)
        self.assertEqual(self.crm.opps[self.oid]["original_amount"], 1000)
        self.assertEqual(self.crm.log[-1], ("discount", self.oid, "r1"))

    def test_floor_rounding(self):
        self.crm.opps[self.oid]["amount"] = 333
        self.crm.opps[self.oid]["original_amount"] = 333
        self.crm.discount(self.oid, 10, "r1")
        self.assertEqual(self.crm.opps[self.oid]["amount"], 299)

    def test_manager_can_reach_30_percent(self):
        self.crm.discount(self.oid, 30, M)
        self.assertEqual(self.crm.opps[self.oid]["amount"], 700)

    def test_pct_validation(self):
        for pct in [0, 31, -1, True, 1.5, "10", None]:
            with self.assertRaises(ValueError, msg=repr(pct)):
                self.crm.discount(self.oid, pct, M)
        self.assertEqual(self.crm.opps[self.oid]["amount"], 1000)

    def test_permissions_and_cumulative_limit(self):
        with self.assertRaises(ValueError):
            self.crm.discount("O404", 10, M)
        with self.assertRaises(PermissionError):
            self.crm.discount(self.oid, 10, "ghost")
        with self.assertRaises(PermissionError):
            self.crm.discount(self.oid, 10, "r2")
        with self.assertRaises(PermissionError):
            self.crm.discount(self.oid, 11, "r1")
        self.crm.discount(self.oid, 10, "r1")
        self.crm.discount(self.oid, 10, "r1")
        self.crm.discount(self.oid, 10, "r1")  # 27.1 percent cumulative, still legal
        self.assertEqual(self.crm.opps[self.oid]["amount"], 729)

    def test_cumulative_limit(self):
        self.crm.discount(self.oid, 30, M)
        self.assertEqual(self.crm.opps[self.oid]["amount"], 700)
        with self.assertRaises(ValueError):
            self.crm.discount(self.oid, 1, M)
        self.assertEqual(self.crm.opps[self.oid]["amount"], 700)

    def test_final_stage_rejected(self):
        self.crm.advance(self.oid, "lost", "r1")
        with self.assertRaises(ValueError):
            self.crm.discount(self.oid, 10, M)


class TransferTests(unittest.TestCase):
    def setUp(self):
        self.crm = fresh()
        self.lid, self.oid = qualified_lead(self.crm, amount=1000)

    def test_success(self):
        self.crm.transfer(self.oid, "r2", M)
        self.assertEqual(self.crm.opps[self.oid]["owner"], "r2")
        self.assertEqual(self.crm.log[-1], ("transfer", self.oid, M))
        self.assertEqual(self.crm._load("r2"), 1)

    def test_errors(self):
        with self.assertRaises(ValueError):
            self.crm.transfer("O404", "r2", M)
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.oid, "r2", "r1")
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.oid, "r2", "ghost")
        with self.assertRaises(ValueError):
            self.crm.transfer(self.oid, "nobody", M)
        with self.assertRaises(ValueError):
            self.crm.transfer(self.oid, M, M)  # manager is not a rep
        with self.assertRaises(ValueError):
            self.crm.transfer(self.oid, "r1", M)  # same owner
        self.assertEqual(self.crm.opps[self.oid]["owner"], "r1")
        self.crm.advance(self.oid, "lost", "r1")
        with self.assertRaises(ValueError):
            self.crm.transfer(self.oid, "r2", M)

    def test_target_at_capacity(self):
        crm = fresh([{"id": "r1", "role": "rep", "capacity": 2},
                     {"id": "r2", "role": "rep", "capacity": 1},
                     {"id": "m1", "role": "manager", "capacity": 0}])
        _, oid = qualified_lead(crm, amount=1000)
        crm.add_lead("fill@corp.com", "Fill", "web", M)  # r2 at capacity 1
        self.assertEqual(crm.leads["L2"]["owner"], "r2")
        with self.assertRaises(ValueError):
            crm.transfer(oid, "r2", M)
        self.assertEqual(crm.opps[oid]["owner"], "r1")

    def test_transfer_frees_previous_owner_slot(self):
        crm = fresh([{"id": "r1", "role": "rep", "capacity": 1},
                     {"id": "r2", "role": "rep", "capacity": 2},
                     {"id": "m1", "role": "manager", "capacity": 0}])
        _, oid = qualified_lead(crm, amount=1000)
        before = len(crm.log)
        crm.transfer(oid, "r2", M)
        self.assertEqual(crm.log[before:], [("transfer", oid, M)])
        # r1 is free again, so the next lead goes to r1 rather than r2
        lid = crm.add_lead("next@corp.com", "Next", "web", M)
        self.assertEqual(crm.leads[lid]["owner"], "r1")


class ForecastTests(unittest.TestCase):
    def test_forecast(self):
        crm = fresh([{"id": "r1", "role": "rep", "capacity": 10},
                     {"id": "m1", "role": "manager", "capacity": 0}])
        oids = []
        for i, amount in enumerate([1000, 500, 200, 700, 300], start=1):
            _, oid = qualified_lead(crm, email="l%d@corp.com" % i, amount=amount)
            oids.append(oid)
        crm.advance(oids[1], "proposal", M)
        crm.advance(oids[2], "proposal", M)
        crm.advance(oids[2], "negotiation", M)
        for stage in ["proposal", "negotiation", "won"]:
            crm.advance(oids[3], stage, M)
        crm.advance(oids[4], "lost", M)
        before = len(crm.log)
        self.assertEqual(
            crm.forecast(), {"open": 3, "weighted": 370, "won": 700}
        )
        self.assertEqual(len(crm.log), before)
        self.assertEqual(
            fresh().forecast(), {"open": 0, "weighted": 0, "won": 0}
        )

    def test_forecast_uses_current_amount_after_discount(self):
        crm = fresh([{"id": "r1", "role": "rep", "capacity": 10},
                     {"id": "m1", "role": "manager", "capacity": 0}])
        _, oid = qualified_lead(crm, amount=1000)
        crm.discount(oid, 10, M)
        for stage in ["proposal", "negotiation", "won"]:
            crm.advance(oid, stage, M)
        self.assertEqual(crm.forecast(), {"open": 0, "weighted": 0, "won": 900})


class NoSideEffectTests(unittest.TestCase):
    def test_failed_calls_leave_state_untouched(self):
        crm = fresh()
        lid, oid = qualified_lead(crm, amount=1000)
        state = copy.deepcopy(
            (crm.leads, crm.opps, crm.log, crm._lead_seq, crm._opp_seq, list(crm._waiting))
        )
        failing = [
            lambda: crm.add_lead("bad-email", "", "bogus", M),
            lambda: crm.add_lead("x@y.com", "", "web", M),
            lambda: crm.qualify("L404", M),
            lambda: crm.qualify(lid, "r2"),
            lambda: crm.convert("L404", 10, M),
            lambda: crm.convert(lid, 0, M),
            lambda: crm.advance(oid, "won", M),
            lambda: crm.advance(oid, "proposal", "r2"),
            lambda: crm.discount(oid, 11, "r1"),
            lambda: crm.discount(oid, 40, M),
            lambda: crm.transfer(oid, "r2", "r1"),
            lambda: crm.transfer(oid, "r1", M),
        ]
        for call in failing:
            with self.assertRaises((ValueError, PermissionError)):
                call()
            self.assertEqual(
                (crm.leads, crm.opps, crm.log, crm._lead_seq, crm._opp_seq,
                 list(crm._waiting)),
                state,
            )

    def test_failed_duplicate_appends_nothing(self):
        crm = fresh()
        crm.add_lead("a@b.com", "A", "web", M)
        state = copy.deepcopy((crm.leads, crm.opps, crm.log, crm._lead_seq))
        with self.assertRaises(DuplicateLeadError):
            crm.add_lead("A@B.com", "A2", "web", M)
        self.assertEqual((crm.leads, crm.opps, crm.log, crm._lead_seq), state)


if __name__ == "__main__":
    unittest.main()
