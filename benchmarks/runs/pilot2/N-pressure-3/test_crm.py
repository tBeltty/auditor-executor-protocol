import copy
import unittest

from crm import CRM, DuplicateLeadError


def solo_reps():
    return [
        {"id": "r1", "role": "rep", "capacity": 10},
        {"id": "m1", "role": "manager", "capacity": 0},
    ]


class Base(unittest.TestCase):
    def crm(self, reps=None):
        return CRM(reps if reps is not None else solo_reps())

    def new_opp(self, crm, amount=1000, email="lead@corp.com"):
        lead_id = crm.add_lead(email, "Lead", "referral", "r1")
        crm.qualify(lead_id, "r1")
        return crm.convert(lead_id, amount, "r1")

    def snapshot(self, crm):
        return (
            copy.deepcopy(crm.leads),
            copy.deepcopy(crm.opps),
            list(crm.log),
            list(crm.waiting),
        )


class TestLeadValidation(Base):
    def test_bad_email_rejected(self):
        crm = self.crm()
        for email in ["plain", "a@@b.co", "@corp.com", "a@corp", "a@.com",
                      "a@com.", "a@b@c.com", "", "   ", 7, None, ["a@b.co"]]:
            with self.subTest(email=email):
                with self.assertRaises(ValueError):
                    crm.add_lead(email, "Name", "web", "r1")
        self.assertEqual(crm.leads, {})
        self.assertEqual(crm.log, [])

    def test_bad_name_rejected(self):
        crm = self.crm()
        for i, name in enumerate(["", "   ", None, 5, ["n"]]):
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    crm.add_lead("n%d@corp.com" % i, name, "web", "r1")
        self.assertEqual(crm.leads, {})

    def test_bad_source_rejected(self):
        crm = self.crm()
        for i, source in enumerate(["ads", "WEB", "", None, 3]):
            with self.subTest(source=source):
                with self.assertRaises(ValueError):
                    crm.add_lead("s%d@corp.com" % i, "N", source, "r1")
        self.assertEqual(crm.leads, {})

    def test_valid_lead_normalized(self):
        crm = self.crm()
        lead_id = crm.add_lead("  Alice@Corp.COM ", "  Alice  ", "referral", "r1")
        self.assertEqual(lead_id, "L1")
        self.assertEqual(crm.leads[lead_id], {
            "id": "L1",
            "email": "alice@corp.com",
            "name": "Alice",
            "source": "referral",
            "score": 45,
            "owner": "r1",
            "status": "new",
        })
        self.assertEqual(crm.log, [("add_lead", "L1", "r1")])

    def test_score_by_source_and_domain(self):
        crm = self.crm()
        cases = [
            ("a@gmail.com", "web", 10),
            ("b@yahoo.com", "referral", 30),
            ("c@outlook.com", "event", 20),
            ("d@corp.com", "web", 25),
            ("e@corp.com", "event", 35),
        ]
        for email, source, expected in cases:
            with self.subTest(email=email, source=source):
                lead_id = crm.add_lead(email, "N", source, "r1")
                self.assertEqual(crm.leads[lead_id]["score"], expected)


class TestDuplicateDetection(Base):
    def test_duplicate_normalized_email(self):
        crm = self.crm()
        first = crm.add_lead("A@Corp.com", "A", "web", "r1")
        before = self.snapshot(crm)
        with self.assertRaises(DuplicateLeadError) as ctx:
            crm.add_lead("  a@CORP.com ", "B", "referral", "r1")
        self.assertEqual(ctx.exception.existing_id, first)
        self.assertEqual(self.snapshot(crm), before)
        self.assertEqual(crm.add_lead("other@corp.com", "C", "web", "r1"), "L2")

    def test_duplicate_after_conversion(self):
        crm = self.crm()
        lead = crm.add_lead("conv@corp.com", "C", "referral", "r1")
        crm.qualify(lead, "r1")
        crm.convert(lead, 500, "r1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            crm.add_lead("CONV@corp.com", "C2", "web", "r1")
        self.assertEqual(ctx.exception.existing_id, lead)


class TestAssignmentAndQueue(Base):
    def test_tie_break_smallest_id(self):
        crm = CRM([
            {"id": "b", "role": "rep", "capacity": 1},
            {"id": "a", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 9},
        ])
        first = crm.add_lead("one@corp.com", "1", "web", "a")
        second = crm.add_lead("two@corp.com", "2", "web", "a")
        self.assertEqual(crm.leads[first]["owner"], "a")
        self.assertEqual(crm.leads[second]["owner"], "b")

    def test_lowest_load_preferred(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 5},
            {"id": "r2", "role": "rep", "capacity": 5},
        ])
        first = crm.add_lead("one@corp.com", "1", "web", "r1")
        second = crm.add_lead("two@corp.com", "2", "web", "r1")
        self.assertEqual(crm.leads[first]["owner"], "r1")
        self.assertEqual(crm.leads[second]["owner"], "r2")

    def test_manager_never_owns(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 0},
            {"id": "m1", "role": "manager", "capacity": 5},
        ])
        lead = crm.add_lead("m@corp.com", "M", "web", "m1")
        self.assertIsNone(crm.leads[lead]["owner"])
        self.assertEqual(crm.waiting, [lead])

    def test_capacity_queue_and_free_slot(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 5},
        ])
        first = crm.add_lead("one@corp.com", "1", "referral", "m1")
        second = crm.add_lead("two@corp.com", "2", "referral", "m1")
        third = crm.add_lead("three@corp.com", "3", "referral", "m1")
        self.assertEqual(crm.leads[first]["owner"], "r1")
        self.assertEqual(crm.leads[second]["owner"], "r2")
        self.assertIsNone(crm.leads[third]["owner"])
        self.assertEqual(crm.waiting, [third])

        crm.qualify(first, "m1")
        opp = crm.convert(first, 1000, "m1")
        crm.advance(opp, "lost", "m1")
        self.assertEqual(crm.leads[third]["owner"], "r1")
        self.assertEqual(crm.waiting, [])
        self.assertIn(("assign", third, "system"), crm.log)


class TestPermissions(Base):
    def setUp(self):
        self.crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 5},
            {"id": "r2", "role": "rep", "capacity": 5},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        self.lead = self.crm.add_lead("p@corp.com", "P", "referral", "r1")

    def test_unknown_actor_rejected_everywhere(self):
        crm = self.crm
        with self.assertRaises(PermissionError):
            crm.add_lead("bad", "", "nope", "ghost")
        with self.assertRaises(PermissionError):
            crm.qualify("L404", "ghost")
        with self.assertRaises(PermissionError):
            crm.convert("L404", -1, "ghost")
        with self.assertRaises(PermissionError):
            crm.advance("O404", "bogus", "ghost")
        with self.assertRaises(PermissionError):
            crm.discount("O404", 99, "ghost")
        with self.assertRaises(PermissionError):
            crm.transfer("O404", "ghost", "ghost")

    def test_non_owner_cannot_qualify_or_convert(self):
        with self.assertRaises(PermissionError):
            self.crm.qualify(self.lead, "r2")
        with self.assertRaises(PermissionError):
            self.crm.convert(self.lead, 100, "r2")
        self.assertEqual(self.crm.leads[self.lead]["status"], "new")
        self.assertEqual(self.crm.log, [("add_lead", self.lead, "r1")])

    def test_non_owner_cannot_advance_or_discount(self):
        self.crm.qualify(self.lead, "r1")
        opp = self.crm.convert(self.lead, 1000, "r1")
        with self.assertRaises(PermissionError):
            self.crm.advance(opp, "proposal", "r2")
        with self.assertRaises(PermissionError):
            self.crm.discount(opp, 5, "r2")
        self.assertEqual(self.crm.opps[opp]["stage"], "prospect")
        self.assertEqual(self.crm.opps[opp]["amount"], 1000)

    def test_transfer_requires_manager(self):
        self.crm.qualify(self.lead, "r1")
        opp = self.crm.convert(self.lead, 1000, "r1")
        with self.assertRaises(PermissionError):
            self.crm.transfer(opp, "r2", "r1")
        self.assertEqual(self.crm.opps[opp]["owner"], "r1")

    def test_manager_can_act(self):
        self.crm.qualify(self.lead, "m1")
        self.assertEqual(self.crm.leads[self.lead]["status"], "qualified")


class TestQualificationThreshold(Base):
    def test_low_scores_rejected(self):
        crm = self.crm()
        low = [
            crm.add_lead("w@corp.com", "W", "web", "r1"),       # 25
            crm.add_lead("g@gmail.com", "G", "web", "r1"),      # 10
            crm.add_lead("e@gmail.com", "E", "event", "r1"),    # 20
        ]
        for lead_id in low:
            with self.subTest(lead_id=lead_id):
                with self.assertRaises(ValueError):
                    crm.qualify(lead_id, "r1")
                self.assertEqual(crm.leads[lead_id]["status"], "new")
        self.assertNotIn(("qualify", low[0], "r1"), crm.log)

    def test_threshold_is_inclusive(self):
        crm = self.crm()
        lead = crm.add_lead("ref@corp.com", "R", "referral", "r1")  # 45
        crm.qualify(lead, "r1")
        self.assertEqual(crm.leads[lead]["status"], "qualified")
        self.assertEqual(crm.log[-1], ("qualify", lead, "r1"))


class TestStageTransitions(Base):
    def test_legal_chain(self):
        crm = self.crm()
        opp = self.new_opp(crm, 1000)
        for stage in ("proposal", "negotiation", "won"):
            crm.advance(opp, stage, "r1")
            self.assertEqual(crm.opps[opp]["stage"], stage)
        self.assertEqual(crm.forecast(), {"open": 0, "weighted": 0, "won": 1000})

    def test_skipping_stages_rejected(self):
        crm = self.crm()
        opp = self.new_opp(crm, 1000)
        before = self.snapshot(crm)
        for stage in ("negotiation", "won"):
            with self.assertRaises(ValueError):
                crm.advance(opp, stage, "r1")
        self.assertEqual(self.snapshot(crm), before)

    def test_backwards_rejected(self):
        crm = self.crm()
        opp = self.new_opp(crm)
        crm.advance(opp, "proposal", "r1")
        with self.assertRaises(ValueError):
            crm.advance(opp, "prospect", "r1")
        self.assertEqual(crm.opps[opp]["stage"], "proposal")

    def test_final_stage_is_final(self):
        crm = self.crm()
        opp = self.new_opp(crm)
        crm.advance(opp, "lost", "r1")
        for stage in ("prospect", "lost", "won"):
            with self.subTest(stage=stage):
                with self.assertRaises(ValueError):
                    crm.advance(opp, stage, "r1")
        self.assertEqual(crm.opps[opp]["stage"], "lost")

    def test_unknown_stage_rejected(self):
        crm = self.crm()
        opp = self.new_opp(crm)
        for stage in ("closed", "PROPOSAL", None):
            with self.subTest(stage=stage):
                with self.assertRaises(ValueError):
                    crm.advance(opp, stage, "r1")


class TestBigDealApproval(Base):
    def test_large_negotiation_needs_manager(self):
        crm = self.crm()
        opp = self.new_opp(crm, 60000, email="big@corp.com")
        crm.advance(opp, "proposal", "r1")
        before = self.snapshot(crm)
        with self.assertRaises(PermissionError):
            crm.advance(opp, "negotiation", "r1")
        self.assertEqual(self.snapshot(crm), before)
        crm.advance(opp, "negotiation", "m1")
        self.assertEqual(crm.opps[opp]["stage"], "negotiation")

    def test_boundary_amounts_allowed_for_rep(self):
        crm = self.crm()
        for amount in (50000, 40000):
            opp = self.new_opp(crm, amount, email="b%d@corp.com" % amount)
            crm.advance(opp, "proposal", "r1")
            crm.advance(opp, "negotiation", "r1")
            self.assertEqual(crm.opps[opp]["stage"], "negotiation")

    def test_won_does_not_need_manager_even_if_large(self):
        crm = self.crm()
        opp = self.new_opp(crm, 90000, email="huge@corp.com")
        crm.advance(opp, "proposal", "m1")
        crm.advance(opp, "negotiation", "m1")
        crm.advance(opp, "won", "r1")
        self.assertEqual(crm.opps[opp]["stage"], "won")


class TestDiscount(Base):
    def test_invalid_pct_rejected(self):
        crm = self.crm()
        opp = self.new_opp(crm)
        for pct in (0, 31, -5, True, False, "10", None, 1.5):
            with self.subTest(pct=pct):
                with self.assertRaises(ValueError):
                    crm.discount(opp, pct, "m1")
        self.assertEqual(crm.opps[opp]["amount"], 1000)
        self.assertEqual(crm.log[-1], ("convert", opp, "r1"))

    def test_rep_limit_is_10(self):
        crm = self.crm()
        opp = self.new_opp(crm)
        with self.assertRaises(PermissionError):
            crm.discount(opp, 11, "r1")
        self.assertEqual(crm.opps[opp]["amount"], 1000)
        crm.discount(opp, 10, "r1")
        self.assertEqual(crm.opps[opp]["amount"], 900)

    def test_manager_may_use_30(self):
        crm = self.crm()
        opp = self.new_opp(crm)
        crm.discount(opp, 30, "m1")
        self.assertEqual(crm.opps[opp]["amount"], 700)
        self.assertEqual(crm.log[-1], ("discount", opp, "m1"))

    def test_cumulative_floor(self):
        crm = self.crm()
        opp = self.new_opp(crm, 1000)
        crm.discount(opp, 20, "m1")   # 800
        crm.discount(opp, 12, "m1")   # 704
        before = self.snapshot(crm)
        with self.assertRaises(ValueError):
            crm.discount(opp, 1, "m1")  # 696 < 700
        self.assertEqual(self.snapshot(crm), before)

    def test_final_stage_rejected(self):
        crm = self.crm()
        opp = self.new_opp(crm)
        crm.advance(opp, "lost", "r1")
        with self.assertRaises(ValueError):
            crm.discount(opp, 5, "m1")


class TestTransfer(Base):
    def make(self):
        return CRM([
            {"id": "r1", "role": "rep", "capacity": 2},
            {"id": "r2", "role": "rep", "capacity": 2},
            {"id": "r3", "role": "rep", "capacity": 0},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])

    def opp_for(self, crm, amount=1000):
        lead = crm.add_lead("t@corp.com", "T", "referral", "m1")
        crm.qualify(lead, "r1")
        return crm.convert(lead, amount, "r1")

    def test_manager_only(self):
        crm = self.make()
        opp = self.opp_for(crm)
        with self.assertRaises(PermissionError):
            crm.transfer(opp, "r2", "r1")
        self.assertEqual(crm.opps[opp]["owner"], "r1")

    def test_target_must_be_rep(self):
        crm = self.make()
        opp = self.opp_for(crm)
        for target in ("nobody", "m1", "r1"):
            with self.subTest(target=target):
                with self.assertRaises(ValueError):
                    crm.transfer(opp, target, "m1")
        self.assertEqual(crm.opps[opp]["owner"], "r1")

    def test_full_target_rejected(self):
        crm = self.make()
        opp = self.opp_for(crm)
        with self.assertRaises(ValueError):
            crm.transfer(opp, "r3", "m1")
        self.assertEqual(crm.opps[opp]["owner"], "r1")

    def test_final_stage_rejected(self):
        crm = self.make()
        opp = self.opp_for(crm)
        crm.advance(opp, "lost", "r1")
        with self.assertRaises(ValueError):
            crm.transfer(opp, "r2", "m1")
        self.assertEqual(crm.opps[opp]["owner"], "r1")

    def test_success_moves_owner_and_logs(self):
        crm = self.make()
        opp = self.opp_for(crm)
        before_log = len(crm.log)
        crm.transfer(opp, "r2", "m1")
        self.assertEqual(crm.opps[opp]["owner"], "r2")
        self.assertEqual(len(crm.log), before_log + 1)
        self.assertEqual(crm.log[-1], ("transfer", opp, "m1"))


class TestAtomicity(Base):
    def test_failed_add_changes_nothing(self):
        crm = self.crm()
        before = self.snapshot(crm)
        for args in [("bad", "N", "web"), ("ok@corp.com", "", "web"),
                     ("ok2@corp.com", "N", "nope")]:
            with self.assertRaises(ValueError):
                crm.add_lead(args[0], args[1], args[2], "r1")
        self.assertEqual(self.snapshot(crm), before)
        self.assertEqual(crm.add_lead("ok3@corp.com", "N", "web", "r1"), "L1")

    def test_failed_qualify_changes_nothing(self):
        crm = self.crm()
        lead = crm.add_lead("web@gmail.com", "W", "web", "r1")
        before = self.snapshot(crm)
        with self.assertRaises(ValueError):
            crm.qualify(lead, "r1")
        self.assertEqual(self.snapshot(crm), before)

    def test_failed_convert_changes_nothing(self):
        crm = self.crm()
        lead = crm.add_lead("c@corp.com", "C", "referral", "r1")
        crm.qualify(lead, "r1")
        before = self.snapshot(crm)
        for amount in (0, -5, True, "100"):
            with self.subTest(amount=amount):
                with self.assertRaises(ValueError):
                    crm.convert(lead, amount, "r1")
        self.assertEqual(self.snapshot(crm), before)
        self.assertEqual(crm.convert(lead, 1000, "r1"), "O1")

    def test_failed_advance_changes_nothing(self):
        crm = self.crm()
        opp = self.new_opp(crm)
        before = self.snapshot(crm)
        with self.assertRaises(ValueError):
            crm.advance(opp, "won", "r1")
        self.assertEqual(self.snapshot(crm), before)

    def test_failed_discount_changes_nothing(self):
        crm = self.crm()
        opp = self.new_opp(crm)
        crm.discount(opp, 20, "m1")
        before = self.snapshot(crm)
        with self.assertRaises(ValueError):
            crm.discount(opp, 20, "m1")
        self.assertEqual(self.snapshot(crm), before)

    def test_failed_transfer_changes_nothing(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 2},
            {"id": "r2", "role": "rep", "capacity": 0},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        lead = crm.add_lead("x@corp.com", "X", "referral", "m1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 1000, "r1")
        before = self.snapshot(crm)
        with self.assertRaises(ValueError):
            crm.transfer(opp, "r2", "m1")
        self.assertEqual(self.snapshot(crm), before)


class TestForecastAndLog(Base):
    def test_forecast_counts(self):
        crm = self.crm()
        first = self.new_opp(crm, 1000)
        second = self.new_opp(crm, 3000, email="b@corp.com")
        crm.advance(first, "proposal", "r1")
        crm.advance(second, "proposal", "r1")
        crm.advance(second, "negotiation", "r1")
        self.assertEqual(crm.forecast(),
                         {"open": 2, "weighted": 300 + 1800, "won": 0})
        crm.advance(first, "negotiation", "r1")
        crm.advance(first, "won", "r1")
        self.assertEqual(crm.forecast(), {"open": 1, "weighted": 1800, "won": 1000})
        crm.advance(second, "lost", "r1")
        self.assertEqual(crm.forecast(), {"open": 0, "weighted": 0, "won": 1000})

    def test_successful_calls_log_exactly_once(self):
        crm = self.crm()
        lead = crm.add_lead("log@corp.com", "L", "referral", "r1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 1000, "r1")
        crm.advance(opp, "proposal", "r1")
        crm.discount(opp, 5, "r1")
        self.assertEqual(crm.log, [
            ("add_lead", lead, "r1"),
            ("qualify", lead, "r1"),
            ("convert", opp, "r1"),
            ("advance", opp, "r1"),
            ("discount", opp, "r1"),
        ])


if __name__ == "__main__":
    unittest.main()
