import unittest

from crm import CRM, DuplicateLeadError


def rep(rid, capacity=10):
    return {"id": rid, "role": "rep", "capacity": capacity}


def manager(mid="m1"):
    return {"id": mid, "role": "manager", "capacity": 0}


class AddLeadTests(unittest.TestCase):
    def test_basic_creation_normalization_and_score(self):
        crm = CRM([rep("r1")])
        lead_id = crm.add_lead("  Alice@Example.COM ", " Alice ", "referral", "r1")
        self.assertEqual(lead_id, "L1")
        self.assertEqual(
            crm.leads["L1"],
            {
                "id": "L1",
                "email": "alice@example.com",
                "name": "Alice",
                "source": "referral",
                "score": 45,
                "owner": "r1",
                "status": "new",
            },
        )
        self.assertEqual(crm.log, [("add_lead", "L1", "r1")])

    def test_source_and_free_domain_scoring(self):
        crm = CRM([rep("r1")])
        ids = [
            crm.add_lead("a@gmail.com", "A", "web", "r1"),
            crm.add_lead("b@gmail.com", "B", "event", "r1"),
            crm.add_lead("c@gmail.com", "C", "referral", "r1"),
            crm.add_lead("d@example.org", "D", "web", "r1"),
            crm.add_lead("e@corp.example.org", "E", "event", "r1"),
        ]
        self.assertEqual([crm.leads[i]["score"] for i in ids], [10, 20, 30, 25, 35])

    def test_lowest_load_and_string_tiebreak(self):
        crm = CRM([rep("r10", 5), rep("r2", 5)])
        first = crm.add_lead("a@example.com", "A", "web", "r10")
        second = crm.add_lead("b@example.com", "B", "web", "r10")
        third = crm.add_lead("c@example.com", "C", "web", "r10")
        self.assertEqual(crm.leads[first]["owner"], "r10")
        self.assertEqual(crm.leads[second]["owner"], "r2")
        # Loads are now 1 each, so the string-smallest id wins again.
        self.assertEqual(crm.leads[third]["owner"], "r10")

    def test_no_rep_capacity_goes_to_waiting_queue(self):
        crm = CRM([manager("m1")])
        first = crm.add_lead("a@example.com", "A", "web", "m1")
        second = crm.add_lead("b@example.com", "B", "web", "m1")
        self.assertIsNone(crm.leads[first]["owner"])
        self.assertIsNone(crm.leads[second]["owner"])

    def test_capacity_zero_never_gets_work(self):
        crm = CRM([rep("r0", 0), rep("r1", 10)])
        lead_id = crm.add_lead("a@example.com", "A", "web", "r1")
        self.assertEqual(crm.leads[lead_id]["owner"], "r1")

    def test_duplicate_normalized_email(self):
        crm = CRM([rep("r1")])
        first = crm.add_lead("A@B.com", "A", "web", "r1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            crm.add_lead("  a@B.COM ", "Other", "event", "r1")
        self.assertEqual(ctx.exception.existing_id, first)
        # Failed call created no lead and consumed no sequence number.
        self.assertEqual(list(crm.leads), ["L1"])
        self.assertEqual(crm.log, [("add_lead", "L1", "r1")])
        self.assertEqual(crm.add_lead("c@b.com", "C", "web", "r1"), "L2")

    def test_invalid_email_forms(self):
        crm = CRM([rep("r1")])
        invalids = [
            123,
            None,
            "no-at.com",
            "a@@b.com",
            "@b.com",
            "a@bcom",
            "a@.com",
            "a@com.",
            "   ",
        ]
        for value in invalids:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    crm.add_lead(value, "A", "web", "r1")
        self.assertEqual(crm.leads, {})
        self.assertEqual(crm.log, [])
        # A dot anywhere in the middle of the domain is enough.
        self.assertEqual(crm.add_lead("a@sub.example.com", "A", "web", "r1"), "L1")

    def test_validation_order_and_failed_calls_are_atomic(self):
        crm = CRM([rep("r1")])
        with self.assertRaises(PermissionError):
            crm.add_lead("bad", "", "nope", "ghost")
        with self.assertRaises(ValueError):
            crm.add_lead("bad", "", "nope", "r1")
        with self.assertRaises(ValueError):
            crm.add_lead("a@b.com", "   ", "nope", "r1")
        with self.assertRaises(ValueError):
            crm.add_lead("a@b.com", "A", "nope", "r1")
        self.assertEqual(crm.leads, {})
        self.assertEqual(crm.log, [])


class QualifyTests(unittest.TestCase):
    def test_success_and_manager_override(self):
        crm = CRM([rep("r1"), rep("r2"), manager("m1")])
        lead = crm.add_lead("a@example.com", "A", "referral", "r1")
        crm.qualify(lead, "m1")
        self.assertEqual(crm.leads[lead]["status"], "qualified")
        self.assertEqual(
            crm.log[-1],
            ("qualify", lead, "m1"),
        )

    def test_checks_and_order(self):
        crm = CRM([rep("r1"), rep("r2"), manager("m1")])
        with self.assertRaises(ValueError):
            crm.qualify("missing", "r1")

        low = crm.add_lead("a@gmail.com", "A", "web", "r1")
        # Permission check comes before the score check.
        with self.assertRaises(PermissionError):
            crm.qualify(low, "r2")
        with self.assertRaises(ValueError):
            crm.qualify(low, "r1")

        good = crm.add_lead("b@example.com", "B", "referral", "r1")
        self.assertEqual(crm.leads[good]["owner"], "r2")
        crm.qualify(good, "r2")
        with self.assertRaises(PermissionError):
            crm.qualify(good, "r1")
        with self.assertRaises(ValueError):
            crm.qualify(good, "r2")
        self.assertEqual(
            [entry for entry in crm.log if entry[0] == "qualify"],
            [("qualify", good, "r2")],
        )

    def test_unknown_actor_wins_over_missing_lead(self):
        crm = CRM([rep("r1")])
        with self.assertRaises(PermissionError):
            crm.qualify("missing", "ghost")


class ConvertTests(unittest.TestCase):
    def test_success_creates_opportunity(self):
        crm = CRM([rep("r1")])
        lead = crm.add_lead("a@example.com", "A", "referral", "r1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 2500, "r1")
        self.assertEqual(opp, "O1")
        self.assertEqual(
            crm.opps["O1"],
            {
                "id": "O1",
                "lead_id": lead,
                "owner": "r1",
                "amount": 2500,
                "original_amount": 2500,
                "stage": "prospect",
            },
        )
        self.assertEqual(crm.leads[lead]["status"], "converted")
        self.assertEqual(crm.log[-1], ("convert", "O1", "r1"))

    def test_manager_can_convert_and_sequence_skips_failures(self):
        crm = CRM([rep("r1"), rep("r2"), manager("m1")])
        lead = crm.add_lead("a@example.com", "A", "referral", "r1")
        crm.qualify(lead, "r1")
        with self.assertRaises(ValueError):
            crm.convert(lead, 0, "m1")
        with self.assertRaises(ValueError):
            crm.convert(lead, True, "m1")
        with self.assertRaises(ValueError):
            crm.convert(lead, 1.5, "m1")
        with self.assertRaises(PermissionError):
            crm.convert(lead, 100, "r2")
        self.assertEqual(crm.convert(lead, 100, "m1"), "O1")

    def test_checks(self):
        crm = CRM([rep("r1", 1), rep("r2", 0), manager("m1")])
        with self.assertRaises(ValueError):
            crm.convert("missing", 100, "r1")

        lead = crm.add_lead("a@example.com", "A", "referral", "r1")
        # Amount is validated before permission.
        with self.assertRaises(ValueError):
            crm.convert(lead, -1, "r2")
        with self.assertRaises(PermissionError):
            crm.convert(lead, 100, "r2")
        with self.assertRaises(ValueError):
            crm.convert(lead, 100, "r1")  # still new

        # Qualified but unowned leads cannot be converted.
        waiting = crm.add_lead("b@example.com", "B", "referral", "m1")
        crm.qualify(waiting, "m1")
        with self.assertRaises(ValueError):
            crm.convert(waiting, 100, "m1")

        self.assertEqual(crm.log, [
            ("add_lead", lead, "r1"),
            ("add_lead", waiting, "m1"),
            ("qualify", waiting, "m1"),
        ])

    def test_unknown_actor_wins_over_missing_opportunity(self):
        crm = CRM([rep("r1")])
        with self.assertRaises(PermissionError):
            crm.convert("missing", 100, "ghost")


class AdvanceTests(unittest.TestCase):
    def _make_opp(self, amount=1000, actor="r1", reps=None):
        crm = CRM(
            reps
            or [rep("r1"), rep("r2"), manager("m1")]
        )
        lead = crm.add_lead("a@example.com", "A", "referral", actor)
        crm.qualify(lead, actor)
        opp = crm.convert(lead, amount, actor)
        return crm, opp

    def test_full_chain_and_lost(self):
        crm, opp = self._make_opp()
        crm.advance(opp, "proposal", "r1")
        self.assertEqual(crm.opps[opp]["stage"], "proposal")
        crm.advance(opp, "negotiation", "r1")
        self.assertEqual(crm.opps[opp]["stage"], "negotiation")
        crm.advance(opp, "won", "r1")
        self.assertEqual(crm.opps[opp]["stage"], "won")
        self.assertEqual(
            [entry[0] for entry in crm.log],
            ["add_lead", "qualify", "convert", "advance", "advance", "advance"],
        )

        crm2, opp2 = self._make_opp()
        crm2.advance(opp2, "proposal", "r1")
        crm2.advance(opp2, "lost", "r1")
        self.assertEqual(crm2.opps[opp2]["stage"], "lost")

    def test_check_order_and_invalid_transitions(self):
        crm, opp = self._make_opp()
        with self.assertRaises(ValueError):
            crm.advance("missing", "bogus", "r1")
        with self.assertRaises(ValueError):
            crm.advance(opp, "bogus", "r1")
        with self.assertRaises(PermissionError):
            crm.advance(opp, "proposal", "r2")
        with self.assertRaises(PermissionError):
            crm.advance(opp, "bogus", "ghost")
        with self.assertRaises(ValueError):
            crm.advance(opp, "negotiation", "r1")
        with self.assertRaises(ValueError):
            crm.advance(opp, "prospect", "r1")
        self.assertEqual(crm.opps[opp]["stage"], "prospect")
        self.assertEqual(len(crm.log), 3)

        crm.advance(opp, "proposal", "r1")
        with self.assertRaises(ValueError):
            crm.advance(opp, "won", "r1")
        self.assertEqual(crm.opps[opp]["stage"], "proposal")

    def test_final_stage_cannot_advance(self):
        crm, opp = self._make_opp()
        for stage in ("proposal", "negotiation", "won"):
            crm.advance(opp, stage, "r1")
        with self.assertRaises(ValueError):
            crm.advance(opp, "lost", "r1")
        self.assertEqual(crm.opps[opp]["stage"], "won")

    def test_large_negotiation_needs_manager(self):
        crm, opp = self._make_opp(amount=60000)
        crm.advance(opp, "proposal", "r1")
        with self.assertRaises(PermissionError):
            crm.advance(opp, "negotiation", "r1")
        self.assertEqual(crm.opps[opp]["stage"], "proposal")
        crm.advance(opp, "negotiation", "m1")
        self.assertEqual(crm.opps[opp]["stage"], "negotiation")

    def test_negotiation_at_exactly_50000_is_allowed_for_rep(self):
        crm, opp = self._make_opp(amount=50000)
        crm.advance(opp, "proposal", "r1")
        crm.advance(opp, "negotiation", "r1")
        self.assertEqual(crm.opps[opp]["stage"], "negotiation")

    def test_winning_frees_slot_and_assigns_fifo(self):
        crm = CRM([rep("r1", 1), manager("m1")])
        first = crm.add_lead("a@example.com", "A", "referral", "r1")
        second = crm.add_lead("b@example.com", "B", "referral", "r1")
        third = crm.add_lead("c@example.com", "C", "referral", "r1")
        self.assertIsNone(crm.leads[second]["owner"])
        self.assertIsNone(crm.leads[third]["owner"])

        crm.qualify(first, "r1")
        opp = crm.convert(first, 1000, "r1")
        crm.advance(opp, "proposal", "r1")
        crm.advance(opp, "negotiation", "r1")
        crm.advance(opp, "won", "r1")

        self.assertEqual(crm.leads[second]["owner"], "r1")
        self.assertIsNone(crm.leads[third]["owner"])
        self.assertEqual(crm.log[-1], ("assign", second, "system"))

    def test_waiting_lead_assignment_fills_only_available_capacity(self):
        crm = CRM([rep("r1", 2), manager("m1")])
        first = crm.add_lead("a@example.com", "A", "referral", "r1")
        second = crm.add_lead("b@example.com", "B", "referral", "r1")
        waiting_a = crm.add_lead("c@example.com", "C", "referral", "r1")
        waiting_b = crm.add_lead("d@example.com", "D", "referral", "r1")
        self.assertIsNone(crm.leads[waiting_a]["owner"])
        self.assertIsNone(crm.leads[waiting_b]["owner"])

        crm.qualify(first, "r1")
        opp = crm.convert(first, 1000, "r1")
        crm.advance(opp, "lost", "r1")
        # Only one slot is free: the oldest waiting lead gets it.
        self.assertEqual(crm.leads[waiting_a]["owner"], "r1")
        self.assertIsNone(crm.leads[waiting_b]["owner"])
        assigns = [entry for entry in crm.log if entry[0] == "assign"]
        self.assertEqual(assigns, [("assign", waiting_a, "system")])

    def test_unknown_actor_first(self):
        crm, opp = self._make_opp()
        with self.assertRaises(PermissionError):
            crm.advance("missing", "bogus", "ghost")


class DiscountTests(unittest.TestCase):
    def _make_opp(self, amount=1000):
        crm = CRM([rep("r1"), rep("r2"), manager("m1")])
        lead = crm.add_lead("a@example.com", "A", "referral", "r1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, amount, "r1")
        return crm, opp

    def test_rep_and_manager_limits(self):
        crm, opp = self._make_opp(1000)
        crm.discount(opp, 10, "r1")
        self.assertEqual(crm.opps[opp]["amount"], 900)
        with self.assertRaises(PermissionError):
            crm.discount(opp, 11, "r1")
        self.assertEqual(crm.opps[opp]["amount"], 900)
        with self.assertRaises(ValueError):
            # 25 more would exceed the cumulative 30 percent cap.
            crm.discount(opp, 25, "m1")
        self.assertEqual(crm.opps[opp]["amount"], 900)
        crm.discount(opp, 20, "m1")
        self.assertEqual(crm.opps[opp]["amount"], 720)
        self.assertEqual(
            crm.log[-2:],
            [("discount", opp, "r1"), ("discount", opp, "m1")],
        )

    def test_cumulative_cap_uses_original_amount(self):
        crm, opp = self._make_opp(10000)
        crm.discount(opp, 30, "m1")
        self.assertEqual(crm.opps[opp]["amount"], 7000)
        with self.assertRaises(ValueError):
            crm.discount(opp, 1, "m1")
        self.assertEqual(crm.opps[opp]["amount"], 7000)

        crm2, opp2 = self._make_opp(1000)
        crm2.discount(opp2, 10, "r1")  # 900
        crm2.discount(opp2, 10, "r1")  # 810
        crm2.discount(opp2, 10, "r1")  # 729
        with self.assertRaises(ValueError):
            crm2.discount(opp2, 10, "r1")
        self.assertEqual(crm2.opps[opp2]["amount"], 729)

    def test_validation_and_order(self):
        crm, opp = self._make_opp()
        with self.assertRaises(ValueError):
            crm.discount("missing", 5, "r1")
        with self.assertRaises(ValueError):
            crm.discount(opp, 0, "r1")
        with self.assertRaises(ValueError):
            crm.discount(opp, 31, "r1")
        with self.assertRaises(ValueError):
            crm.discount(opp, True, "r1")
        with self.assertRaises(ValueError):
            crm.discount(opp, 5.0, "r1")
        with self.assertRaises(PermissionError):
            crm.discount(opp, 5, "r2")
        self.assertEqual(crm.opps[opp]["amount"], 1000)
        self.assertEqual(len(crm.log), 3)

    def test_final_stage_blocked(self):
        crm, opp = self._make_opp()
        crm.advance(opp, "lost", "r1")
        with self.assertRaises(ValueError):
            crm.discount(opp, 5, "m1")
        self.assertEqual(crm.opps[opp]["amount"], 1000)

    def test_unknown_actor_first(self):
        crm, opp = self._make_opp()
        with self.assertRaises(PermissionError):
            crm.discount("missing", 0, "ghost")


class TransferTests(unittest.TestCase):
    def _make_opp(self, reps=None):
        crm = CRM(reps or [rep("r1", 2), rep("r2", 2), manager("m1")])
        lead = crm.add_lead("a@example.com", "A", "referral", "r1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 1000, "r1")
        return crm, opp, lead

    def test_success_and_log(self):
        crm, opp, _ = self._make_opp()
        crm.transfer(opp, "r2", "m1")
        self.assertEqual(crm.opps[opp]["owner"], "r2")
        self.assertEqual(crm.log[-1], ("transfer", opp, "m1"))

    def test_transfer_frees_previous_owner_slot(self):
        crm = CRM([rep("r1", 1), rep("r2", 2), manager("m1")])
        lead = crm.add_lead("a@example.com", "A", "referral", "r1")
        waiting = crm.add_lead("b@example.com", "B", "referral", "r1")
        self.assertEqual(crm.leads[waiting]["owner"], "r2")
        # Put b back in the FIFO queue. Through the public API a queue only
        # exists when every rep is full, which would leave no transfer target.
        crm.leads[waiting]["owner"] = None
        crm._waiting.append(waiting)

        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 1000, "r1")

        crm.transfer(opp, "r2", "m1")
        self.assertEqual(crm.leads[waiting]["owner"], "r1")
        self.assertEqual(
            crm.log[-2:],
            [("transfer", opp, "m1"), ("assign", waiting, "system")],
        )

    def test_failure_checks(self):
        crm, opp, _ = self._make_opp()
        with self.assertRaises(ValueError):
            crm.transfer("missing", "r2", "m1")
        with self.assertRaises(PermissionError):
            crm.transfer(opp, "r2", "r1")
        with self.assertRaises(ValueError):
            crm.transfer(opp, "ghost", "m1")
        with self.assertRaises(ValueError):
            crm.transfer(opp, "m1", "m1")
        with self.assertRaises(ValueError):
            crm.transfer(opp, "r1", "m1")
        self.assertEqual(crm.opps[opp]["owner"], "r1")
        self.assertEqual(len(crm.log), 3)

        small = CRM([rep("r1", 2), rep("r2", 1), manager("m1")])
        lead = small.add_lead("a@example.com", "A", "referral", "r1")
        small.qualify(lead, "r1")
        opp2 = small.convert(lead, 1000, "r1")
        lead_r2 = small.add_lead("b@example.com", "B", "web", "r1")
        self.assertEqual(small.leads[lead_r2]["owner"], "r2")
        # r2 is now at capacity.
        with self.assertRaises(ValueError):
            small.transfer(opp2, "r2", "m1")
        self.assertEqual(small.opps[opp2]["owner"], "r1")

        crm.advance(opp, "lost", "r1")
        with self.assertRaises(ValueError):
            crm.transfer(opp, "r2", "m1")

    def test_unknown_actor_first(self):
        crm, opp, _ = self._make_opp()
        with self.assertRaises(PermissionError):
            crm.transfer("missing", "ghost", "ghost")


class ForecastTests(unittest.TestCase):
    def test_empty(self):
        crm = CRM([rep("r1")])
        self.assertEqual(crm.forecast(), {"open": 0, "weighted": 0, "won": 0})

    def test_mixed_stages(self):
        crm = CRM([rep("r1", 10), manager("m1")])
        amounts = [1000, 2000, 3000, 4000, 5000]
        opps = []
        for i, amount in enumerate(amounts):
            lead = crm.add_lead("a%d@example.com" % i, "A", "referral", "r1")
            crm.qualify(lead, "r1")
            opps.append(crm.convert(lead, amount, "r1"))

        # prospect: 1000 * 10 // 100 = 100
        # proposal: 2000 * 30 // 100 = 600
        crm.advance(opps[1], "proposal", "r1")
        # negotiation: 3000 * 60 // 100 = 1800
        crm.advance(opps[2], "proposal", "r1")
        crm.advance(opps[2], "negotiation", "r1")
        # won: 4000, not open
        crm.advance(opps[3], "proposal", "r1")
        crm.advance(opps[3], "negotiation", "r1")
        crm.advance(opps[3], "won", "r1")
        # lost: excluded entirely
        crm.advance(opps[4], "lost", "r1")

        self.assertEqual(
            crm.forecast(),
            {"open": 3, "weighted": 100 + 600 + 1800, "won": 4000},
        )
        self.assertEqual(crm.log[-1], ("advance", opps[4], "r1"))

    def test_forecast_does_not_log(self):
        crm = CRM([rep("r1")])
        before = list(crm.log)
        crm.forecast()
        self.assertEqual(crm.log, before)


class ActorFirstTests(unittest.TestCase):
    def test_unknown_actor_is_first_everywhere(self):
        crm = CRM([rep("r1")])
        with self.assertRaises(PermissionError):
            crm.add_lead("bad", "", "bad", "ghost")
        with self.assertRaises(PermissionError):
            crm.qualify("missing", "ghost")
        with self.assertRaises(PermissionError):
            crm.convert("missing", 0, "ghost")
        with self.assertRaises(PermissionError):
            crm.advance("missing", "bogus", "ghost")
        with self.assertRaises(PermissionError):
            crm.discount("missing", 0, "ghost")
        with self.assertRaises(PermissionError):
            crm.transfer("missing", "ghost", "ghost")
        self.assertEqual(crm.log, [])


if __name__ == "__main__":
    unittest.main()
