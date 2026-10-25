import unittest

from crm import CRM, DuplicateLeadError


def make_crm(cap1=2, cap2=2):
    return CRM([
        {"id": "r1", "role": "rep", "capacity": cap1},
        {"id": "r2", "role": "rep", "capacity": cap2},
        {"id": "m1", "role": "manager", "capacity": 5},
    ])


def referral(crm, email, actor="m1", name="N"):
    return crm.add_lead(email, name, "referral", actor)


def to_negotiation(crm, opp_id, actor):
    crm.advance(opp_id, "proposal", actor)
    crm.advance(opp_id, "negotiation", actor)


class AddLeadTests(unittest.TestCase):
    def test_normalizes_and_scores(self):
        crm = make_crm()
        lead_id = crm.add_lead("  Bob@Gmail.com ", "  Bob  ", "web", "m1")
        lead = crm.leads[lead_id]
        self.assertEqual(lead_id, "L1")
        self.assertEqual(lead["email"], "bob@gmail.com")
        self.assertEqual(lead["name"], "Bob")
        self.assertEqual(lead["score"], 10)
        self.assertEqual(lead["status"], "new")
        self.assertEqual(crm.log, [("add_lead", "L1", "m1")])

        other = crm.add_lead("bob@acme.com", "Bob", "referral", "m1")
        self.assertEqual(crm.leads[other]["score"], 45)

    def test_score_by_source(self):
        crm = make_crm()
        for source, score in (("web", 10), ("referral", 30), ("event", 20)):
            lead_id = crm.add_lead("x%s@acme.com" % source, "X", source, "m1")
            self.assertEqual(crm.leads[lead_id]["score"], score + 15)

    def test_id_counter_counts_only_successes(self):
        crm = make_crm()
        crm.add_lead("a@acme.com", "A", "web", "m1")
        with self.assertRaises(ValueError):
            crm.add_lead("bad", "B", "web", "m1")
        self.assertEqual(crm.add_lead("c@acme.com", "C", "web", "m1"), "L2")

    def test_email_validation(self):
        crm = make_crm()
        bad = ["", "plain", "a@@b.com", "@b.com", "a@b", "a@.com", "a@b.", 42, None]
        for email in bad:
            with self.assertRaises(ValueError):
                crm.add_lead(email, "A", "web", "m1")
        self.assertEqual(crm.leads, {})

    def test_name_and_source_validation(self):
        crm = make_crm()
        with self.assertRaises(ValueError):
            crm.add_lead("a@acme.com", "   ", "web", "m1")
        with self.assertRaises(ValueError):
            crm.add_lead("a@acme.com", 5, "web", "m1")
        with self.assertRaises(ValueError):
            crm.add_lead("a@acme.com", "A", "mail", "m1")
        self.assertEqual(crm.leads, {})
        self.assertEqual(crm.log, [])

    def test_unknown_actor_checked_first(self):
        crm = make_crm()
        with self.assertRaises(PermissionError):
            crm.add_lead("bad", "", "nope", "ghost")
        self.assertEqual(crm.log, [])

    def test_duplicate_email(self):
        crm = make_crm()
        first = crm.add_lead("a@acme.com", "A", "web", "m1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            crm.add_lead("  A@ACME.COM  ", "A2", "event", "m1")
        self.assertEqual(ctx.exception.existing_id, first)
        self.assertEqual(len(crm.leads), 1)

    def test_round_robin_and_waiting_queue(self):
        crm = make_crm(cap1=1, cap2=1)
        l1 = crm.add_lead("a@acme.com", "A", "web", "m1")
        l2 = crm.add_lead("b@acme.com", "B", "web", "m1")
        l3 = crm.add_lead("c@acme.com", "C", "web", "m1")
        self.assertEqual(crm.leads[l1]["owner"], "r1")
        self.assertEqual(crm.leads[l2]["owner"], "r2")
        self.assertIsNone(crm.leads[l3]["owner"])

    def test_manager_never_owns(self):
        crm = make_crm(cap1=0, cap2=0)
        lead_id = crm.add_lead("a@acme.com", "A", "web", "m1")
        self.assertIsNone(crm.leads[lead_id]["owner"])

    def test_owner_tie_break_uses_string_order(self):
        crm = CRM([
            {"id": "r2", "role": "rep", "capacity": 5},
            {"id": "r10", "role": "rep", "capacity": 5},
            {"id": "m1", "role": "manager", "capacity": 5},
        ])
        lead_id = crm.add_lead("a@acme.com", "A", "web", "m1")
        self.assertEqual(crm.leads[lead_id]["owner"], "r10")

    def test_source_checked_before_duplicate(self):
        crm = make_crm()
        crm.add_lead("a@acme.com", "A", "web", "m1")
        with self.assertRaises(ValueError):
            crm.add_lead("a@acme.com", "A", "mail", "m1")


class QualifyConvertTests(unittest.TestCase):
    def test_qualify_requires_owner_or_manager(self):
        crm = make_crm(cap1=1, cap2=1)
        lead_id = referral(crm, "a@acme.com")  # owner r1, score 30
        with self.assertRaises(PermissionError):
            crm.qualify(lead_id, "r2")
        crm.qualify(lead_id, "m1")
        self.assertEqual(crm.leads[lead_id]["status"], "qualified")

    def test_qualify_rejects_low_score_and_wrong_status(self):
        crm = make_crm()
        low = crm.add_lead("a@gmail.com", "A", "web", "m1")
        with self.assertRaises(ValueError):
            crm.qualify(low, "m1")
        good = referral(crm, "b@acme.com")
        with self.assertRaises(ValueError):
            crm.qualify("L99", "m1")
        crm.qualify(good, "m1")
        with self.assertRaises(ValueError):
            crm.qualify(good, "m1")

    def test_convert_happy_path(self):
        crm = make_crm()
        lead_id = referral(crm, "a@acme.com")
        crm.qualify(lead_id, "r1")
        opp_id = crm.convert(lead_id, 1000, "r1")
        self.assertEqual(opp_id, "O1")
        opp = crm.opps[opp_id]
        self.assertEqual(opp["owner"], "r1")
        self.assertEqual(opp["stage"], "prospect")
        self.assertEqual(opp["amount"], 1000)
        self.assertEqual(opp["original_amount"], 1000)
        self.assertEqual(crm.leads[lead_id]["status"], "converted")
        self.assertEqual(crm.log[-1], ("convert", "O1", "r1"))

    def test_convert_validation_order(self):
        crm = make_crm()
        lead_id = referral(crm, "a@acme.com")
        with self.assertRaises(ValueError):
            crm.convert(lead_id, 0, "m1")          # amount before status
        with self.assertRaises(ValueError):
            crm.convert(lead_id, True, "m1")
        with self.assertRaises(ValueError):
            crm.convert(lead_id, 10, "m1")         # not qualified yet
        crm.qualify(lead_id, "m1")
        with self.assertRaises(PermissionError):
            crm.convert(lead_id, 10, "r2")
        with self.assertRaises(ValueError):
            crm.convert("L99", 10, "m1")
        self.assertEqual(crm.opps, {})

    def test_convert_requires_owner(self):
        crm = make_crm(cap1=0, cap2=0)
        lead_id = referral(crm, "a@acme.com")
        self.assertIsNone(crm.leads[lead_id]["owner"])
        crm.qualify(lead_id, "m1")
        with self.assertRaises(ValueError):
            crm.convert(lead_id, 100, "m1")
        self.assertEqual(crm.leads[lead_id]["status"], "qualified")

    def test_conversion_does_not_drain_waiting_queue(self):
        crm = make_crm(cap1=1, cap2=0)
        first = referral(crm, "a@acme.com")    # r1's only slot
        queued = referral(crm, "b@acme.com")   # waiting
        crm.qualify(first, "m1")
        crm.convert(first, 100, "m1")
        # the converted lead no longer counts, but the new opportunity does
        self.assertIsNone(crm.leads[queued]["owner"])
        self.assertFalse(any(entry[0] == "assign" for entry in crm.log))


class AdvanceTests(unittest.TestCase):
    def _opp(self, crm, amount=1000):
        lead_id = referral(crm, "a@acme.com")
        crm.qualify(lead_id, "m1")
        return crm.convert(lead_id, amount, "m1")

    def test_stage_order(self):
        crm = make_crm()
        opp_id = self._opp(crm)
        with self.assertRaises(ValueError):
            crm.advance(opp_id, "won", "m1")       # skips stages
        crm.advance(opp_id, "proposal", "m1")
        self.assertEqual(crm.opps[opp_id]["stage"], "proposal")
        crm.advance(opp_id, "negotiation", "m1")
        crm.advance(opp_id, "won", "m1")
        with self.assertRaises(ValueError):
            crm.advance(opp_id, "lost", "m1")      # final
        self.assertEqual(crm.opps[opp_id]["stage"], "won")
        self.assertEqual(crm.log[-1], ("advance", opp_id, "m1"))

    def test_lost_allowed_from_any_open_stage(self):
        crm = make_crm()
        opp_id = self._opp(crm)
        crm.advance(opp_id, "lost", "r1")
        self.assertEqual(crm.opps[opp_id]["stage"], "lost")

    def test_invalid_stage_and_permissions(self):
        crm = make_crm()
        opp_id = self._opp(crm)
        with self.assertRaises(ValueError):
            crm.advance(opp_id, "bogus", "m1")
        with self.assertRaises(ValueError):       # stage check precedes permission
            crm.advance(opp_id, "bogus", "r2")
        with self.assertRaises(PermissionError):
            crm.advance(opp_id, "proposal", "r2")
        self.assertEqual(crm.opps[opp_id]["stage"], "prospect")

    def test_large_negotiation_requires_manager(self):
        crm = make_crm()
        opp_id = self._opp(crm, amount=50001)
        crm.advance(opp_id, "proposal", "r1")
        with self.assertRaises(PermissionError):
            crm.advance(opp_id, "negotiation", "r1")
        self.assertEqual(crm.opps[opp_id]["stage"], "proposal")
        crm.advance(opp_id, "negotiation", "m1")
        self.assertEqual(crm.opps[opp_id]["stage"], "negotiation")

    def test_won_frees_slot_and_assigns_queue(self):
        crm = make_crm(cap1=1, cap2=1)
        lead_id = referral(crm, "a@acme.com")       # r1
        referral(crm, "b@acme.com")                 # r2
        queued = referral(crm, "c@acme.com")        # queue
        crm.qualify(lead_id, "r1")
        opp_id = crm.convert(lead_id, 1000, "r1")
        crm.advance(opp_id, "proposal", "r1")
        crm.advance(opp_id, "negotiation", "r1")
        crm.advance(opp_id, "won", "r1")
        self.assertEqual(crm.leads[queued]["owner"], "r1")
        self.assertEqual(crm.log[-1], ("assign", queued, "system"))

    def test_drain_stops_at_capacity(self):
        crm = make_crm(cap1=3, cap2=0)
        leads = [referral(crm, "u%d@acme.com" % i) for i in range(3)]
        first_queued = referral(crm, "q1@acme.com")
        second_queued = referral(crm, "q2@acme.com")
        crm.qualify(leads[0], "m1")
        opp_id = crm.convert(leads[0], 1000, "m1")
        crm.advance(opp_id, "proposal", "m1")
        crm.advance(opp_id, "negotiation", "m1")
        crm.advance(opp_id, "won", "m1")
        self.assertEqual(crm.leads[first_queued]["owner"], "r1")
        self.assertIsNone(crm.leads[second_queued]["owner"])
        assigns = [entry for entry in crm.log if entry[0] == "assign"]
        self.assertEqual(assigns, [("assign", first_queued, "system")])


class DiscountTests(unittest.TestCase):
    def _opp(self, crm, amount=1000):
        lead_id = referral(crm, "a@acme.com")
        crm.qualify(lead_id, "m1")
        return crm.convert(lead_id, amount, "m1")

    def test_rep_capped_at_ten(self):
        crm = make_crm()
        opp_id = self._opp(crm)
        with self.assertRaises(PermissionError):
            crm.discount(opp_id, 11, "r1")
        crm.discount(opp_id, 10, "r1")
        self.assertEqual(crm.opps[opp_id]["amount"], 900)
        self.assertEqual(crm.log[-1], ("discount", opp_id, "r1"))

    def test_cumulative_limit(self):
        crm = make_crm()
        opp_id = self._opp(crm)
        crm.discount(opp_id, 20, "m1")
        crm.discount(opp_id, 10, "m1")
        self.assertEqual(crm.opps[opp_id]["amount"], 720)
        with self.assertRaises(ValueError):
            crm.discount(opp_id, 10, "m1")          # 648 < 700 floor
        self.assertEqual(crm.opps[opp_id]["amount"], 720)

    def test_validation_and_final_stage(self):
        crm = make_crm()
        opp_id = self._opp(crm)
        for pct in (0, 31, 5.5, True, "5"):
            with self.assertRaises(ValueError):
                crm.discount(opp_id, pct, "m1")
        with self.assertRaises(PermissionError):
            crm.discount(opp_id, 5, "r2")
        crm.advance(opp_id, "lost", "m1")
        with self.assertRaises(ValueError):
            crm.discount(opp_id, 5, "m1")

    def test_floor_allows_exactly_thirty_percent(self):
        crm = make_crm()
        opp_id = self._opp(crm, amount=1000)
        crm.discount(opp_id, 30, "m1")
        self.assertEqual(crm.opps[opp_id]["amount"], 700)

    def test_floor_rejects_rounded_total_below_seventy_percent(self):
        crm = make_crm()
        opp_id = self._opp(crm, amount=1001)
        # 1001 * 70 // 100 == 700, and 700 * 100 < 1001 * 70
        with self.assertRaises(ValueError):
            crm.discount(opp_id, 30, "m1")
        self.assertEqual(crm.opps[opp_id]["amount"], 1001)

    def test_pct_validated_before_permissions(self):
        crm = make_crm()
        opp_id = self._opp(crm)
        with self.assertRaises(ValueError):     # bad pct wins over wrong actor
            crm.discount(opp_id, 0, "r2")


class TransferTests(unittest.TestCase):
    def test_transfer_moves_owner(self):
        crm = make_crm(cap1=2, cap2=3)
        l1 = referral(crm, "a@acme.com")   # r1
        crm.qualify(l1, "m1")
        opp_id = crm.convert(l1, 1000, "m1")
        crm.transfer(opp_id, "r2", "m1")
        self.assertEqual(crm.opps[opp_id]["owner"], "r2")
        self.assertEqual(crm.log[-1], ("transfer", opp_id, "m1"))

    def test_transfer_validation(self):
        crm = make_crm(cap1=2, cap2=2)
        lead_id = referral(crm, "a@acme.com")
        crm.qualify(lead_id, "m1")
        opp_id = crm.convert(lead_id, 1000, "m1")
        with self.assertRaises(PermissionError):
            crm.transfer(opp_id, "r2", "r1")
        with self.assertRaises(ValueError):
            crm.transfer(opp_id, "m1", "m1")        # manager is not a rep
        with self.assertRaises(ValueError):
            crm.transfer(opp_id, "ghost", "m1")
        with self.assertRaises(ValueError):
            crm.transfer(opp_id, "r1", "m1")        # same owner
        self.assertEqual(crm.opps[opp_id]["owner"], "r1")

    def test_transfer_to_full_rep(self):
        crm = make_crm(cap1=2, cap2=1)
        l1 = referral(crm, "a@acme.com")   # r1
        referral(crm, "b@acme.com")        # r2 fills
        crm.qualify(l1, "m1")
        opp_id = crm.convert(l1, 100, "m1")
        with self.assertRaises(ValueError):
            crm.transfer(opp_id, "r2", "m1")
        self.assertEqual(crm.opps[opp_id]["owner"], "r1")


class ForecastTests(unittest.TestCase):
    def test_forecast(self):
        crm = make_crm()
        self.assertEqual(crm.forecast(), {"open": 0, "weighted": 0, "won": 0})

        def opp(email, amount):
            lead_id = referral(crm, email)
            crm.qualify(lead_id, "m1")
            return crm.convert(lead_id, amount, "m1")

        a = opp("a@acme.com", 1000)
        b = opp("b@acme.com", 2000)
        c = opp("c@acme.com", 3000)
        crm.advance(a, "proposal", "m1")
        crm.advance(b, "proposal", "m1")
        crm.advance(b, "negotiation", "m1")
        crm.advance(c, "proposal", "m1")
        crm.advance(c, "negotiation", "m1")
        crm.advance(c, "won", "m1")
        self.assertEqual(crm.forecast(), {
            "open": 2,
            "weighted": 1000 * 30 // 100 + 2000 * 60 // 100,
            "won": 3000,
        })
        self.assertEqual(crm.log[-1], ("advance", c, "m1"))


class AtomicityTests(unittest.TestCase):
    def test_failed_calls_mutate_nothing(self):
        crm = make_crm()
        lead_id = referral(crm, "a@acme.com")
        before_log = list(crm.log)
        before_leads = {k: dict(v) for k, v in crm.leads.items()}
        with self.assertRaises(ValueError):
            crm.convert(lead_id, 100, "m1")
        with self.assertRaises(ValueError):
            crm.qualify("L99", "m1")
        with self.assertRaises(DuplicateLeadError):
            crm.add_lead("A@acme.com", "A", "web", "m1")
        self.assertEqual(crm.log, before_log)
        self.assertEqual(crm.leads, before_leads)
        self.assertEqual(crm.opps, {})


class ReviewHardeningTests(unittest.TestCase):
    def test_duplicate_detected_after_conversion(self):
        crm = make_crm()
        lead_id = referral(crm, "a@acme.com")
        crm.qualify(lead_id, "m1")
        crm.convert(lead_id, 100, "m1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            referral(crm, " A@ACME.com ")
        self.assertEqual(ctx.exception.existing_id, lead_id)

    def test_non_string_actor_is_unknown(self):
        crm = make_crm()
        for actor in (["r1"], None, 5, {"id": "r1"}):
            with self.assertRaises(PermissionError):
                crm.add_lead("a@acme.com", "A", "web", actor)
        self.assertEqual(crm.leads, {})
        self.assertEqual(crm.log, [])

    def test_non_string_ids_are_unknown(self):
        crm = make_crm()
        with self.assertRaises(ValueError):
            crm.qualify(["L1"], "m1")
        with self.assertRaises(ValueError):
            crm.convert(["L1"], 10, "m1")
        with self.assertRaises(ValueError):
            crm.advance(["O1"], "proposal", "m1")
        with self.assertRaises(ValueError):
            crm.discount(["O1"], 5, "m1")
        with self.assertRaises(ValueError):
            crm.transfer(["O1"], "r2", "m1")

    def test_transfer_rejects_non_string_new_owner(self):
        crm = make_crm()
        lead_id = referral(crm, "a@acme.com")
        crm.qualify(lead_id, "m1")
        opp_id = crm.convert(lead_id, 100, "m1")
        for new_owner in (["r2"], None, 2):
            with self.assertRaises(ValueError):
                crm.transfer(opp_id, new_owner, "m1")
        self.assertEqual(crm.opps[opp_id]["owner"], "r1")

    def test_loads_stay_consistent_after_transfer(self):
        crm = make_crm(cap1=2, cap2=2)
        l1 = referral(crm, "a@acme.com")       # r1
        referral(crm, "b@acme.com")            # r2
        crm.qualify(l1, "m1")
        opp_id = crm.convert(l1, 100, "m1")
        crm.transfer(opp_id, "r2", "m1")       # r2 now at capacity
        new_lead = referral(crm, "c@acme.com")
        self.assertEqual(crm.leads[new_lead]["owner"], "r1")
        self.assertEqual(crm._load("r1"), 1)
        self.assertEqual(crm._load("r2"), 2)

    def test_negotiation_gate_uses_current_amount(self):
        crm = make_crm()
        lead_id = referral(crm, "a@acme.com")
        crm.qualify(lead_id, "m1")
        opp_id = crm.convert(lead_id, 60000, "m1")
        crm.advance(opp_id, "proposal", "r1")
        with self.assertRaises(PermissionError):
            crm.advance(opp_id, "negotiation", "r1")
        crm.discount(opp_id, 20, "m1")
        crm.advance(opp_id, "negotiation", "r1")
        self.assertEqual(crm.opps[opp_id]["stage"], "negotiation")

    def test_forecast_ignores_lost_opportunities(self):
        crm = make_crm()
        lead_id = referral(crm, "a@acme.com")
        crm.qualify(lead_id, "m1")
        opp_id = crm.convert(lead_id, 2000, "m1")
        crm.advance(opp_id, "proposal", "m1")
        crm.advance(opp_id, "lost", "m1")
        self.assertEqual(crm.forecast(), {"open": 0, "weighted": 0, "won": 0})


if __name__ == "__main__":
    unittest.main()
