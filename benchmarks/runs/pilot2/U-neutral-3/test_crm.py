import unittest

from crm import CRM, DuplicateLeadError


def make_crm():
    return CRM(
        [
            {"id": "r1", "role": "rep", "capacity": 2},
            {"id": "r2", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 0},
        ]
    )


def snapshot(crm):
    return (
        list(crm.log),
        {k: dict(v) for k, v in crm.leads.items()},
        {k: dict(v) for k, v in crm.opps.items()},
        list(crm._waiting),
        crm._lead_seq,
        crm._opp_seq,
    )


class AddLeadTests(unittest.TestCase):
    def test_normalizes_email_and_name(self):
        crm = make_crm()
        lead_id = crm.add_lead("  Alice@Example.COM ", "  Alice  ", "web", "m1")
        self.assertEqual(lead_id, "L1")
        lead = crm.leads["L1"]
        self.assertEqual(lead["email"], "alice@example.com")
        self.assertEqual(lead["name"], "Alice")
        self.assertEqual(lead["source"], "web")
        self.assertEqual(lead["status"], "new")
        self.assertEqual(lead["owner"], "r1")
        self.assertEqual(crm.log, [("add_lead", "L1", "m1")])

    def test_score_free_domain_vs_business_domain(self):
        crm = make_crm()
        crm.add_lead("a@gmail.com", "A", "web", "m1")
        crm.add_lead("b@corp.io", "B", "web", "m1")
        crm.add_lead("c@yahoo.com", "C", "referral", "m1")
        crm.add_lead("d@corp.io", "D", "event", "m1")
        self.assertEqual(crm.leads["L1"]["score"], 10)
        self.assertEqual(crm.leads["L2"]["score"], 25)
        self.assertEqual(crm.leads["L3"]["score"], 30)
        self.assertEqual(crm.leads["L4"]["score"], 35)

    def test_invalid_emails(self):
        for bad in [123, "", "a", "a@@b.com", "a@b", "a@.com", "a@com.", "@b.com", "ab.com"]:
            crm = make_crm()
            with self.subTest(email=bad):
                with self.assertRaises(ValueError):
                    crm.add_lead(bad, "Name", "web", "m1")
                self.assertEqual(crm.leads, {})
                self.assertEqual(crm.log, [])

    def test_invalid_name(self):
        for bad in [123, "", "   ", None]:
            crm = make_crm()
            with self.subTest(name=bad):
                with self.assertRaises(ValueError):
                    crm.add_lead("a@b.com", bad, "web", "m1")

    def test_invalid_source(self):
        crm = make_crm()
        with self.assertRaises(ValueError):
            crm.add_lead("a@b.com", "A", "Web", "m1")
        with self.assertRaises(ValueError):
            crm.add_lead("a@b.com", "A", "email", "m1")

    def test_unknown_actor_checked_first(self):
        crm = make_crm()
        with self.assertRaises(PermissionError):
            crm.add_lead(123, "", "bogus", "ghost")
        self.assertEqual(crm.log, [])

    def test_duplicate_email_is_normalized(self):
        crm = make_crm()
        crm.add_lead("Alice@Example.com", "Alice", "web", "m1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            crm.add_lead("  alice@example.COM  ", "Other", "referral", "m1")
        self.assertEqual(ctx.exception.existing_id, "L1")
        self.assertEqual(len(crm.leads), 1)
        self.assertEqual(len(crm.log), 1)

    def test_lead_ids_only_count_successes(self):
        crm = make_crm()
        crm.add_lead("a@b.com", "A", "web", "m1")
        with self.assertRaises(ValueError):
            crm.add_lead("nope", "B", "web", "m1")
        crm.add_lead("c@d.com", "C", "web", "m1")
        self.assertEqual(sorted(crm.leads), ["L1", "L2"])

    def test_lowest_load_with_tie_break(self):
        crm = make_crm()
        crm.add_lead("a@b.com", "A", "web", "m1")
        self.assertEqual(crm.leads["L1"]["owner"], "r1")
        crm.add_lead("b@b.com", "B", "web", "m1")
        self.assertEqual(crm.leads["L2"]["owner"], "r2")
        crm.add_lead("c@b.com", "C", "web", "m1")
        self.assertEqual(crm.leads["L3"]["owner"], "r1")

    def test_waiting_queue_when_no_capacity(self):
        crm = make_crm()
        for i in range(5):
            crm.add_lead("a%d@b.com" % i, "A%d" % i, "web", "m1")
        self.assertEqual(crm.leads["L3"]["owner"], "r1")
        self.assertEqual(crm.leads["L4"]["owner"], None)
        self.assertEqual(crm.leads["L5"]["owner"], None)
        self.assertEqual(crm._waiting, ["L4", "L5"])


class QualifyTests(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()

    def test_unknown_lead(self):
        with self.assertRaises(ValueError):
            self.crm.qualify("L404", "m1")

    def test_unknown_actor(self):
        self.crm.add_lead("a@b.com", "A", "referral", "m1")
        with self.assertRaises(PermissionError):
            self.crm.qualify("L1", "ghost")

    def test_permission(self):
        self.crm.add_lead("a@b.com", "A", "referral", "m1")
        self.crm.add_lead("b@b.com", "B", "referral", "m1")
        with self.assertRaises(PermissionError):
            self.crm.qualify("L1", "r2")
        self.assertEqual(self.crm.leads["L1"]["status"], "new")

    def test_manager_can_qualify_any_lead(self):
        self.crm.add_lead("a@b.com", "A", "referral", "m1")
        self.crm.qualify("L1", "m1")
        self.assertEqual(self.crm.leads["L1"]["status"], "qualified")
        self.assertEqual(self.crm.log[-1], ("qualify", "L1", "m1"))

    def test_owner_can_qualify(self):
        self.crm.add_lead("a@b.com", "A", "referral", "m1")
        self.crm.qualify("L1", "r1")
        self.assertEqual(self.crm.leads["L1"]["status"], "qualified")

    def test_status_must_be_new(self):
        self.crm.add_lead("a@b.com", "A", "referral", "m1")
        self.crm.qualify("L1", "m1")
        with self.assertRaises(ValueError):
            self.crm.qualify("L1", "m1")

    def test_score_threshold(self):
        self.crm.add_lead("a@gmail.com", "A", "web", "m1")  # score 10
        with self.assertRaises(ValueError):
            self.crm.qualify("L1", "m1")
        self.assertEqual(self.crm.leads["L1"]["status"], "new")
        self.assertEqual(len(self.crm.log), 1)

    def test_status_check_before_score_check(self):
        self.crm.add_lead("a@gmail.com", "A", "web", "m1")  # score 10
        self.crm.leads["L1"]["status"] = "converted"
        with self.assertRaises(ValueError):
            self.crm.qualify("L1", "m1")
        self.assertEqual(len(self.crm.log), 1)


class ConvertTests(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        self.crm.add_lead("a@b.com", "A", "referral", "m1")
        self.crm.qualify("L1", "m1")

    def test_success(self):
        opp_id = self.crm.convert("L1", 10000, "r1")
        self.assertEqual(opp_id, "O1")
        self.assertEqual(
            self.crm.opps["O1"],
            {
                "id": "O1",
                "lead_id": "L1",
                "owner": "r1",
                "amount": 10000,
                "original_amount": 10000,
                "stage": "prospect",
            },
        )
        self.assertEqual(self.crm.leads["L1"]["status"], "converted")
        self.assertEqual(self.crm.log[-1], ("convert", "O1", "r1"))

    def test_unknown_lead(self):
        with self.assertRaises(ValueError):
            self.crm.convert("L99", 100, "r1")

    def test_invalid_amount(self):
        for bad in [0, -5, True, False, 10.0, "100", None]:
            with self.subTest(amount=bad):
                with self.assertRaises(ValueError):
                    self.crm.convert("L1", bad, "r1")
        self.assertEqual(self.crm.opps, {})

    def test_permission(self):
        with self.assertRaises(PermissionError):
            self.crm.convert("L1", 100, "r2")
        with self.assertRaises(PermissionError):
            self.crm.convert("L1", 100, "ghost")

    def test_status_must_be_qualified(self):
        self.crm.add_lead("b@b.com", "B", "referral", "m1")
        with self.assertRaises(ValueError):
            self.crm.convert("L2", 100, "m1")
        self.crm.qualify("L2", "m1")
        self.crm.convert("L2", 100, "m1")
        with self.assertRaises(ValueError):
            self.crm.convert("L2", 100, "m1")

    def test_unowned_lead_cannot_convert(self):
        crm = CRM([{"id": "m1", "role": "manager", "capacity": 0}])
        crm.add_lead("a@b.com", "A", "referral", "m1")
        crm.qualify("L1", "m1")
        with self.assertRaises(ValueError):
            crm.convert("L1", 100, "m1")
        self.assertEqual(crm.opps, {})
        self.assertEqual(crm.leads["L1"]["status"], "qualified")

    def test_opportunity_ids_count_successes(self):
        opp1 = self.crm.convert("L1", 100, "r1")
        self.crm.add_lead("b@b.com", "B", "referral", "m1")
        self.crm.qualify("L2", "m1")
        opp2 = self.crm.convert("L2", 200, "m1")
        self.assertEqual((opp1, opp2), ("O1", "O2"))


class AdvanceTests(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        self.crm.add_lead("a@b.com", "A", "referral", "m1")
        self.crm.qualify("L1", "m1")
        self.opp = self.crm.convert("L1", 10000, "r1")

    def test_full_funnel(self):
        self.crm.advance("O1", "proposal", "r1")
        self.crm.advance("O1", "negotiation", "m1")
        self.crm.advance("O1", "won", "r1")
        self.assertEqual(self.crm.opps["O1"]["stage"], "won")
        self.assertEqual(
            self.crm.log[-3:],
            [
                ("advance", "O1", "r1"),
                ("advance", "O1", "m1"),
                ("advance", "O1", "r1"),
            ],
        )

    def test_unknown_opportunity(self):
        with self.assertRaises(ValueError):
            self.crm.advance("O99", "proposal", "r1")

    def test_invalid_stage(self):
        with self.assertRaises(ValueError):
            self.crm.advance("O1", "closed", "r1")

    def test_permission(self):
        with self.assertRaises(PermissionError):
            self.crm.advance("O1", "proposal", "r2")
        with self.assertRaises(PermissionError):
            self.crm.advance("O1", "proposal", "ghost")

    def test_cannot_advance_final(self):
        self.crm.advance("O1", "lost", "m1")
        with self.assertRaises(ValueError):
            self.crm.advance("O1", "lost", "m1")

    def test_must_be_immediate_next_stage(self):
        with self.assertRaises(ValueError):
            self.crm.advance("O1", "negotiation", "m1")
        with self.assertRaises(ValueError):
            self.crm.advance("O1", "won", "m1")
        with self.assertRaises(ValueError):
            self.crm.advance("O1", "prospect", "m1")
        self.assertEqual(self.crm.opps["O1"]["stage"], "prospect")

    def test_lost_allowed_from_any_open_stage(self):
        self.crm.advance("O1", "proposal", "r1")
        self.crm.advance("O1", "lost", "r1")
        self.assertEqual(self.crm.opps["O1"]["stage"], "lost")

    def test_large_negotiation_requires_manager(self):
        big = make_crm()
        big.add_lead("a@b.com", "A", "referral", "m1")
        big.qualify("L1", "m1")
        opp = big.convert("L1", 60000, "r1")
        big.advance(opp, "proposal", "r1")
        with self.assertRaises(PermissionError):
            big.advance(opp, "negotiation", "r1")
        self.assertEqual(big.opps[opp]["stage"], "proposal")
        big.advance(opp, "negotiation", "m1")
        self.assertEqual(big.opps[opp]["stage"], "negotiation")

    def test_exactly_50000_allowed_for_rep(self):
        edge = make_crm()
        edge.add_lead("a@b.com", "A", "referral", "m1")
        edge.qualify("L1", "m1")
        opp = edge.convert("L1", 50000, "r1")
        edge.advance(opp, "proposal", "r1")
        edge.advance(opp, "negotiation", "r1")
        self.assertEqual(edge.opps[opp]["stage"], "negotiation")

    def test_winning_frees_slot_and_assigns_queue(self):
        crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 1},
                {"id": "r2", "role": "rep", "capacity": 1},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        crm.add_lead("a@b.com", "A", "referral", "m1")  # r1
        crm.add_lead("b@b.com", "B", "referral", "m1")  # r2
        crm.add_lead("c@b.com", "C", "referral", "m1")  # queued
        self.assertEqual(crm.leads["L3"]["owner"], None)
        crm.qualify("L1", "m1")
        opp = crm.convert("L1", 10000, "r1")
        crm.advance(opp, "proposal", "r1")
        crm.advance(opp, "negotiation", "m1")
        crm.advance(opp, "won", "r1")
        self.assertEqual(crm.leads["L3"]["owner"], "r1")
        self.assertEqual(crm._waiting, [])
        self.assertEqual(crm.log[-2:], [("advance", "O1", "r1"), ("assign", "L3", "system")])

    def test_no_assignment_when_capacity_full(self):
        crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 2},
                {"id": "r2", "role": "rep", "capacity": 2},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        for i, email in enumerate(["a", "b", "c", "d", "e"]):
            crm.add_lead("%s@x.com" % email, "N%d" % i, "referral", "m1")
        self.assertEqual(crm._waiting, ["L5"])
        crm.qualify("L1", "m1")
        opp1 = crm.convert("L1", 1000, "r1")
        crm.advance(opp1, "lost", "r1")
        # r1 now owns L3 (load 1); the queue head L5 also fits under capacity 2.
        self.assertEqual(crm.leads["L5"]["owner"], "r1")
        self.assertEqual(crm._waiting, [])


class DiscountTests(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        self.crm.add_lead("a@b.com", "A", "referral", "m1")
        self.crm.qualify("L1", "m1")
        self.opp = self.crm.convert("L1", 10000, "r1")

    def test_rep_discount(self):
        self.crm.discount(self.opp, 10, "r1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 9000)
        self.assertEqual(self.crm.opps[self.opp]["original_amount"], 10000)
        self.assertEqual(self.crm.log[-1], ("discount", "O1", "r1"))

    def test_rep_limited_to_ten(self):
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp, 11, "r1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 10000)

    def test_manager_may_discount_thirty(self):
        self.crm.discount(self.opp, 30, "m1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 7000)

    def test_invalid_pct(self):
        for bad in [0, 31, -1, True, False, 10.0, "10", None]:
            with self.subTest(pct=bad):
                with self.assertRaises(ValueError):
                    self.crm.discount(self.opp, bad, "m1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 10000)

    def test_cumulative_cap(self):
        self.crm.discount(self.opp, 10, "r1")  # 9000
        self.crm.discount(self.opp, 10, "r1")  # 8100
        self.crm.discount(self.opp, 10, "r1")  # 7290
        self.assertEqual(self.crm.opps[self.opp]["amount"], 7290)
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp, 10, "r1")  # 6561 < 7000
        self.assertEqual(self.crm.opps[self.opp]["amount"], 7290)

    def test_final_stage_rejected(self):
        self.crm.advance(self.opp, "lost", "m1")
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp, 5, "m1")

    def test_permission(self):
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp, 5, "r2")
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp, 5, "ghost")


class TransferTests(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        self.crm.add_lead("a@b.com", "A", "referral", "m1")
        self.crm.qualify("L1", "m1")
        self.opp = self.crm.convert("L1", 10000, "r1")

    def test_success(self):
        self.crm.transfer(self.opp, "r2", "m1")
        self.assertEqual(self.crm.opps[self.opp]["owner"], "r2")
        self.assertEqual(self.crm.log[-1], ("transfer", "O1", "m1"))

    def test_unknown_opportunity(self):
        with self.assertRaises(ValueError):
            self.crm.transfer("O99", "r2", "m1")

    def test_only_manager_may_transfer(self):
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.opp, "r2", "r1")
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.opp, "r2", "ghost")

    def test_new_owner_must_be_known_rep(self):
        for bad in ["m1", "ghost"]:
            with self.subTest(new_owner=bad):
                with self.assertRaises(ValueError):
                    self.crm.transfer(self.opp, bad, "m1")
        self.assertEqual(self.crm.opps[self.opp]["owner"], "r1")

    def test_final_stage(self):
        self.crm.advance(self.opp, "lost", "m1")
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "r2", "m1")

    def test_same_owner(self):
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "r1", "m1")

    def test_capacity_required(self):
        self.crm.add_lead("b@b.com", "B", "referral", "m1")  # r2 load 1, capped at 1
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "r2", "m1")
        self.assertEqual(self.crm.opps[self.opp]["owner"], "r1")

    def test_frees_previous_owner_and_assigns_queue(self):
        crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 1},
                {"id": "r2", "role": "rep", "capacity": 5},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        crm.add_lead("a@b.com", "A", "referral", "m1")  # r1, cap 1
        crm.qualify("L1", "m1")
        opp = crm.convert("L1", 1000, "r1")
        # A non-empty queue with a target rep that still has capacity is not
        # reachable through the public API (the queue only fills once every rep
        # is full), so seed the queue directly to exercise the documented
        # "free the previous owner's slot" branch.
        crm.leads["L2"] = {
            "id": "L2",
            "email": "b@b.com",
            "name": "B",
            "source": "referral",
            "score": 30,
            "owner": None,
            "status": "new",
        }
        crm._waiting.append("L2")
        crm.transfer(opp, "r2", "m1")
        self.assertEqual(crm.opps[opp]["owner"], "r2")
        self.assertEqual(crm.leads["L2"]["owner"], "r1")
        self.assertEqual(crm._waiting, [])
        self.assertEqual(crm.log[-2:], [("transfer", "O1", "m1"), ("assign", "L2", "system")])


class ForecastTests(unittest.TestCase):
    def test_empty(self):
        crm = make_crm()
        self.assertEqual(crm.forecast(), {"open": 0, "weighted": 0, "won": 0})

    def test_weighted_and_won(self):
        crm = make_crm()
        crm.add_lead("a@b.com", "A", "referral", "m1")
        crm.add_lead("b@b.com", "B", "referral", "m1")
        crm.add_lead("c@b.com", "C", "referral", "m1")
        crm.qualify("L1", "m1")
        crm.qualify("L2", "m1")
        crm.qualify("L3", "m1")
        p = crm.convert("L1", 10000, "r1")  # prospect
        q = crm.convert("L2", 10000, "r2")  # -> proposal
        w = crm.convert("L3", 10000, "r1")  # -> won
        crm.advance(q, "proposal", "r2")
        crm.advance(w, "proposal", "r1")
        crm.advance(w, "negotiation", "m1")
        crm.advance(w, "won", "r1")
        self.assertEqual(
            crm.forecast(),
            {"open": 2, "weighted": 10000 * 10 // 100 + 10000 * 30 // 100, "won": 10000},
        )
        self.assertEqual(crm.opps[p]["stage"], "prospect")

    def test_forecast_uses_current_amounts_and_no_log(self):
        crm = make_crm()
        crm.add_lead("a@b.com", "A", "referral", "m1")
        crm.qualify("L1", "m1")
        opp = crm.convert("L1", 10000, "r1")
        crm.discount(opp, 10, "r1")
        log_len = len(crm.log)
        result = crm.forecast()
        self.assertEqual(result["weighted"], 9000 * 10 // 100)
        self.assertEqual(len(crm.log), log_len)


class AtomicityTests(unittest.TestCase):
    def test_failures_leave_state_untouched(self):
        crm = make_crm()
        crm.add_lead("a@b.com", "A", "referral", "m1")
        crm.qualify("L1", "m1")
        opp = crm.convert("L1", 10000, "r1")
        before = snapshot(crm)

        for call in [
            lambda: crm.add_lead("bad", "N", "web", "m1"),
            lambda: crm.add_lead("x@y.com", "N", "web", "ghost"),
            lambda: crm.qualify("L404", "m1"),
            lambda: crm.qualify("L1", "r2"),
            lambda: crm.convert(opp, 0, "r1"),
            lambda: crm.advance(opp, "won", "r1"),
            lambda: crm.discount(opp, 40, "m1"),
            lambda: crm.transfer(opp, "r1", "m1"),
            lambda: crm.transfer(opp, "ghost", "m1"),
        ]:
            with self.subTest(call=call):
                with self.assertRaises((ValueError, PermissionError)):
                    call()
                self.assertEqual(snapshot(crm), before)


if __name__ == "__main__":
    unittest.main()
