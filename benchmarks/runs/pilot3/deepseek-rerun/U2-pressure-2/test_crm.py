import unittest

from crm import CRM, DuplicateLeadError


def make_crm():
    return CRM(
        [
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 2},
            {"id": "m1", "role": "manager", "capacity": 0},
        ]
    )


class TestAddLead(unittest.TestCase):
    def test_normalizes_scores_and_assigns_lowest_load(self):
        crm = make_crm()
        lead_id = crm.add_lead("  Bob@Gmail.com ", " Bob ", "web", "m1")
        self.assertEqual(lead_id, "L1")
        lead = crm.leads[lead_id]
        self.assertEqual(lead["email"], "bob@gmail.com")
        self.assertEqual(lead["name"], "Bob")
        self.assertEqual(lead["score"], 10)
        self.assertEqual(lead["status"], "new")
        self.assertEqual(lead["owner"], "r1")
        self.assertEqual(crm.log, [("add_lead", "L1", "m1")])

        second = crm.add_lead("a@corp.io", "A", "referral", "r1")
        self.assertEqual(crm.leads[second]["score"], 45)
        self.assertEqual(crm.leads[second]["owner"], "r2")

    def test_waiting_queue_when_all_full(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1}])
        first = crm.add_lead("a@gmail.com", "A", "web", "r1")
        second = crm.add_lead("b@gmail.com", "B", "web", "r1")
        self.assertEqual(crm.leads[first]["owner"], "r1")
        self.assertIsNone(crm.leads[second]["owner"])

    def test_validation_and_duplicate(self):
        crm = make_crm()
        for bad in (123, "no-at", "@gmail.com", "a@b", "a@.com", "a@com.", "a@b@c.com"):
            with self.assertRaises(ValueError, msg=bad):
                crm.add_lead(bad, "N", "web", "r1")
        with self.assertRaises(ValueError):
            crm.add_lead("x@y.com", "   ", "web", "r1")
        with self.assertRaises(ValueError):
            crm.add_lead("x@y.com", "N", "ads", "r1")
        with self.assertRaises(PermissionError):
            crm.add_lead("x@y.com", "N", "web", "ghost")
        crm.add_lead("x@y.com", "N", "web", "r1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            crm.add_lead("X@Y.com", "N", "web", "r1")
        self.assertEqual(ctx.exception.existing_id, "L1")
        self.assertEqual(len(crm.leads), 1)
        self.assertEqual(len(crm.log), 1)


class TestQualifyConvert(unittest.TestCase):
    def test_qualify_path(self):
        crm = make_crm()
        low = crm.add_lead("a@gmail.com", "A", "web", "r1")
        with self.assertRaises(ValueError):
            crm.qualify(low, "r1")  # score 10
        with self.assertRaises(ValueError):
            crm.qualify("L99", "r1")
        good = crm.add_lead("b@corp.io", "B", "event", "r2")
        with self.assertRaises(PermissionError):
            crm.qualify(good, "r1")
        crm.qualify(good, "r2")
        self.assertEqual(crm.leads[good]["status"], "qualified")
        with self.assertRaises(ValueError):
            crm.qualify(good, "r2")
        self.assertEqual(crm.log[-1], ("qualify", good, "r2"))

    def test_convert_rules_and_opp(self):
        crm = make_crm()
        lead_id = crm.add_lead("b@corp.io", "B", "referral", "r1")
        with self.assertRaises(ValueError):
            crm.convert(lead_id, 100, "r1")  # not qualified
        crm.qualify(lead_id, "r1")
        for bad in (0, -5, True, 1.5, "100"):
            with self.assertRaises(ValueError):
                crm.convert(lead_id, bad, "r1")
        with self.assertRaises(PermissionError):
            crm.convert(lead_id, 100, "r2")
        opp_id = crm.convert(lead_id, 1000, "m1")
        self.assertEqual(opp_id, "O1")
        opp = crm.opps[opp_id]
        self.assertEqual(opp["owner"], "r1")
        self.assertEqual(opp["stage"], "prospect")
        self.assertEqual(opp["original_amount"], 1000)
        self.assertEqual(crm.leads[lead_id]["status"], "converted")
        with self.assertRaises(ValueError):
            crm.convert(lead_id, 100, "r1")


class TestAdvanceDiscountTransfer(unittest.TestCase):
    def _qualified_opp(self, amount=1000, owner="r1"):
        crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 2},
                {"id": "r2", "role": "rep", "capacity": 2},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        lead_id = crm.add_lead("b@corp.io", "B", "referral", owner)
        crm.qualify(lead_id, "m1")
        opp_id = crm.convert(lead_id, amount, "m1")
        return crm, opp_id

    def test_advance_stage_order_and_final(self):
        crm, opp = self._qualified_opp()
        with self.assertRaises(ValueError):
            crm.advance(opp, "negotiation", "r1")  # skips proposal
        with self.assertRaises(ValueError):
            crm.advance(opp, "bogus", "r1")
        with self.assertRaises(PermissionError):
            crm.advance(opp, "proposal", "r2")
        crm.advance(opp, "proposal", "r1")
        crm.advance(opp, "negotiation", "r1")
        crm.advance(opp, "won", "r1")
        self.assertEqual(crm.opps[opp]["stage"], "won")
        with self.assertRaises(ValueError):
            crm.advance(opp, "lost", "m1")

    def test_negotiation_over_50k_needs_manager(self):
        crm, opp = self._qualified_opp(amount=60000)
        crm.advance(opp, "proposal", "r1")
        with self.assertRaises(PermissionError):
            crm.advance(opp, "negotiation", "r1")
        crm.advance(opp, "negotiation", "m1")
        self.assertEqual(crm.opps[opp]["stage"], "negotiation")

    def test_advance_frees_slot_and_assigns_oldest_waiting(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1}])
        lead = crm.add_lead("a@corp.io", "A", "referral", "r1")
        waiting = crm.add_lead("b@corp.io", "B", "referral", "r1")
        self.assertIsNone(crm.leads[waiting]["owner"])
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 100, "r1")
        crm.advance(opp, "lost", "r1")
        self.assertEqual(crm.leads[waiting]["owner"], "r1")
        self.assertEqual(crm.log[-1], ("assign", waiting, "system"))

    def test_discount_rules(self):
        crm, opp = self._qualified_opp(amount=1000)
        for bad in (0, 31, True, 5.0):
            with self.assertRaises(ValueError):
                crm.discount(opp, bad, "m1")
        with self.assertRaises(PermissionError):
            crm.discount(opp, 5, "r2")
        with self.assertRaises(PermissionError):
            crm.discount(opp, 11, "r1")
        crm.discount(opp, 10, "r1")
        self.assertEqual(crm.opps[opp]["amount"], 900)
        with self.assertRaises(ValueError):
            crm.discount(opp, 30, "m1")  # cumulative would exceed 30%
        crm.discount(opp, 22, "m1")
        self.assertEqual(crm.opps[opp]["amount"], 702)
        crm.advance(opp, "proposal", "m1")
        crm.advance(opp, "negotiation", "m1")
        crm.advance(opp, "won", "m1")
        with self.assertRaises(ValueError):
            crm.discount(opp, 1, "m1")
        self.assertEqual(crm.log[-1], ("advance", opp, "m1"))

    def test_transfer(self):
        crm, opp = self._qualified_opp()
        with self.assertRaises(PermissionError):
            crm.transfer(opp, "r2", "r1")
        with self.assertRaises(ValueError):
            crm.transfer(opp, "m1", "m1")
        with self.assertRaises(ValueError):
            crm.transfer(opp, "nobody", "m1")
        with self.assertRaises(ValueError):
            crm.transfer(opp, "r1", "m1")
        crm.transfer(opp, "r2", "m1")
        self.assertEqual(crm.opps[opp]["owner"], "r2")
        self.assertEqual(crm.log[-1], ("transfer", opp, "m1"))

    def test_transfer_to_full_rep_rejected(self):
        crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 1},
                {"id": "r2", "role": "rep", "capacity": 1},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        lead = crm.add_lead("a@corp.io", "A", "referral", "r1")
        crm.add_lead("b@corp.io", "B", "referral", "r1")  # fills r2
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 100, "r1")
        with self.assertRaises(ValueError):
            crm.transfer(opp, "r2", "m1")
        self.assertEqual(crm.opps[opp]["owner"], "r1")
        self.assertEqual(len(crm.log), 4)

    def test_forecast(self):
        crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 5},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        self.assertEqual(crm.forecast(), {"open": 0, "weighted": 0, "won": 0})
        opps = []
        for i, amount in enumerate((1000, 2000, 3000)):
            lead = crm.add_lead("a%d@corp.io" % i, "A", "referral", "r1")
            crm.qualify(lead, "r1")
            opps.append(crm.convert(lead, amount, "r1"))
        crm.advance(opps[0], "proposal", "r1")
        crm.advance(opps[1], "proposal", "r1")
        crm.advance(opps[1], "negotiation", "r1")
        crm.advance(opps[2], "proposal", "r1")
        crm.advance(opps[2], "negotiation", "r1")
        crm.advance(opps[2], "won", "r1")
        self.assertEqual(
            crm.forecast(), {"open": 2, "weighted": 300 + 1200, "won": 3000}
        )
        before = len(crm.log)
        crm.forecast()
        self.assertEqual(len(crm.log), before)


class TestSpecGaps(unittest.TestCase):
    def test_waiting_queue_fifo_assigns_only_freed_slots(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1}])
        first = crm.add_lead("a@corp.io", "A", "referral", "r1")
        oldest = crm.add_lead("b@corp.io", "B", "referral", "r1")
        newer = crm.add_lead("c@corp.io", "C", "referral", "r1")
        self.assertIsNone(crm.leads[oldest]["owner"])
        self.assertIsNone(crm.leads[newer]["owner"])
        crm.qualify(first, "r1")
        opp = crm.convert(first, 100, "r1")
        crm.advance(opp, "lost", "r1")
        self.assertEqual(crm.leads[oldest]["owner"], "r1")
        self.assertIsNone(crm.leads[newer]["owner"])
        self.assertEqual(crm.log[-2:], [("advance", opp, "r1"), ("assign", oldest, "system")])
        self.assertEqual(crm._waiting, [newer])

    def test_owner_tie_break_is_smallest_id_and_managers_never_get_work(self):
        crm = CRM(
            [
                {"id": "r10", "role": "rep", "capacity": 1},
                {"id": "r2", "role": "rep", "capacity": 1},
                {"id": "m1", "role": "manager", "capacity": 5},
            ]
        )
        a = crm.add_lead("a@corp.io", "A", "web", "m1")
        b = crm.add_lead("b@corp.io", "B", "web", "m1")
        c = crm.add_lead("c@corp.io", "C", "web", "m1")
        self.assertEqual(crm.leads[a]["owner"], "r10")
        self.assertEqual(crm.leads[b]["owner"], "r2")
        self.assertIsNone(crm.leads[c]["owner"])

    def test_manager_may_qualify_unowned_lead_but_convert_needs_owner(self):
        crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 1},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        crm.add_lead("a@corp.io", "A", "referral", "r1")
        waiting = crm.add_lead("b@corp.io", "B", "referral", "m1")
        self.assertIsNone(crm.leads[waiting]["owner"])
        crm.qualify(waiting, "m1")
        self.assertEqual(crm.leads[waiting]["status"], "qualified")
        with self.assertRaises(ValueError):
            crm.convert(waiting, 100, "m1")
        self.assertEqual(crm.opps, {})

    def test_discount_rounding_and_cumulative_floor(self):
        crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 2},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        lead = crm.add_lead("a@corp.io", "A", "referral", "r1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 999, "r1")
        crm.discount(opp, 10, "r1")
        self.assertEqual(crm.opps[opp]["amount"], 899)  # 999 * 90 // 100
        crm.discount(opp, 22, "m1")
        self.assertEqual(crm.opps[opp]["amount"], 701)  # 899 * 78 // 100
        with self.assertRaises(ValueError):
            crm.discount(opp, 1, "m1")  # 693 * 100 < 999 * 70
        self.assertEqual(crm.opps[opp]["amount"], 701)

    def test_forecast_uses_discounted_amount(self):
        crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 2},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        lead = crm.add_lead("a@corp.io", "A", "referral", "r1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 1000, "r1")
        crm.discount(opp, 10, "m1")
        self.assertEqual(crm.forecast(), {"open": 1, "weighted": 90, "won": 0})

    def test_failures_leave_state_untouched(self):
        crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 1},
                {"id": "r2", "role": "rep", "capacity": 0},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        lead = crm.add_lead("a@corp.io", "A", "referral", "r1")
        waiting = crm.add_lead("b@corp.io", "B", "referral", "m1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 1000, "r1")
        snapshot = (dict(crm.leads), dict(crm.opps), list(crm.log), list(crm._waiting),
                    crm._lead_seq, crm._opp_seq)
        attempts = [
            (PermissionError, lambda: crm.add_lead("c@corp.io", "C", "web", "ghost")),
            (ValueError, lambda: crm.add_lead("bad", "C", "web", "r1")),
            (PermissionError, lambda: crm.qualify(waiting, "r1")),
            (ValueError, lambda: crm.convert(waiting, 10, "m1")),
            (ValueError, lambda: crm.advance(opp, "won", "r1")),
            (PermissionError, lambda: crm.advance(opp, "proposal", "r2")),
            (ValueError, lambda: crm.discount(opp, 0, "m1")),
            (ValueError, lambda: crm.transfer("O99", "r1", "m1")),
        ]
        for expected, call in attempts:
            with self.assertRaises(expected):
                call()
        self.assertEqual(
            (dict(crm.leads), dict(crm.opps), list(crm.log), list(crm._waiting),
             crm._lead_seq, crm._opp_seq),
            snapshot,
        )

    def test_non_string_identifiers_raise_value_error(self):
        crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 1},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        lead = crm.add_lead("a@corp.io", "A", "referral", "r1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 1000, "r1")
        with self.assertRaises(ValueError):
            crm.add_lead("b@corp.io", "B", ["web"], "r1")
        for call in (
            lambda: crm.qualify(["L1"], "r1"),
            lambda: crm.convert(None, 10, "r1"),
            lambda: crm.advance(["O1"], "proposal", "r1"),
            lambda: crm.discount({"id": opp}, 5, "m1"),
            lambda: crm.transfer(["O1"], "r1", "m1"),
            lambda: crm.transfer(opp, ["r1"], "m1"),
        ):
            with self.assertRaises(ValueError):
                call()

    def test_actor_check_precedes_entity_checks(self):
        crm = make_crm()
        with self.assertRaises(PermissionError):
            crm.qualify("L99", "ghost")
        with self.assertRaises(PermissionError):
            crm.convert("L99", "not-an-int", "ghost")
        with self.assertRaises(PermissionError):
            crm.discount("O99", 0, "ghost")
        # with a known actor the listed order applies: amount before permission
        lead = crm.add_lead("a@corp.io", "A", "referral", "r1")
        crm.qualify(lead, "r1")
        with self.assertRaises(ValueError):
            crm.convert(lead, 0, "r2")


if __name__ == "__main__":
    unittest.main()
