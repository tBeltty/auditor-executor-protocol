"""Tests for permissions, qualification, conversion, stages, discounts, transfers."""

import unittest

from crm import CRM
from crm_fixtures import add, make_opp, snapshot, wide_crm


class TestPermissionChecks(unittest.TestCase):
    def setUp(self):
        self.crm = wide_crm()
        self.lead_id = add(self.crm, email="owned@corp.com")
        self.crm.qualify(self.lead_id, "r1")
        self.opp_id = self.crm.convert(self.lead_id, 1000, "r1")

    def test_unknown_actor_rejected_everywhere(self):
        crm = self.crm
        calls = [
            lambda: crm.add_lead("new@corp.com", "New", "web", "ghost"),
            lambda: crm.qualify(self.lead_id, "ghost"),
            lambda: crm.convert(self.lead_id, 100, "ghost"),
            lambda: crm.advance(self.opp_id, "proposal", "ghost"),
            lambda: crm.discount(self.opp_id, 5, "ghost"),
            lambda: crm.transfer(self.opp_id, "r2", "ghost"),
        ]
        for index, call in enumerate(calls):
            with self.subTest(call=index):
                with self.assertRaises(PermissionError):
                    call()

    def test_unknown_actor_is_checked_before_entity_and_payload(self):
        crm = self.crm
        with self.assertRaises(PermissionError):
            crm.add_lead(None, None, "bogus", "ghost")
        with self.assertRaises(PermissionError):
            crm.qualify("missing", "ghost")
        with self.assertRaises(PermissionError):
            crm.convert("missing", -1, "ghost")
        with self.assertRaises(PermissionError):
            crm.advance("missing", "bogus", "ghost")
        with self.assertRaises(PermissionError):
            crm.discount("missing", 99, "ghost")
        with self.assertRaises(PermissionError):
            crm.transfer("missing", "nobody", "ghost")

    def test_non_owner_rep_cannot_act_on_someone_elses_work(self):
        crm = self.crm
        with self.assertRaises(PermissionError):
            crm.qualify(self.lead_id, "r2")
        with self.assertRaises(PermissionError):
            crm.convert(self.lead_id, 100, "r2")
        with self.assertRaises(PermissionError):
            crm.advance(self.opp_id, "proposal", "r2")
        with self.assertRaises(PermissionError):
            crm.discount(self.opp_id, 5, "r2")
        with self.assertRaises(PermissionError):
            crm.transfer(self.opp_id, "r2", "r1")

    def test_non_owner_cannot_qualify_a_new_lead(self):
        crm = wide_crm()
        lead_id = add(crm, email="fresh@corp.com")
        self.assertEqual(crm.leads[lead_id]["status"], "new")
        self.assertEqual(crm.leads[lead_id]["owner"], "r1")
        with self.assertRaises(PermissionError):
            crm.qualify(lead_id, "r2")
        self.assertEqual(crm.leads[lead_id]["status"], "new")

    def test_qualify_permission_checked_before_score(self):
        crm = wide_crm()
        lead_id = add(crm, email="low@gmail.com", source="web")  # score 10
        with self.assertRaises(PermissionError):
            crm.qualify(lead_id, "r2")
        self.assertEqual(crm.leads[lead_id]["status"], "new")

    def test_manager_may_act_on_any_work(self):
        crm = self.crm
        lead_id = add(crm, email="second@corp.com")
        crm.qualify(lead_id, "m1")
        opp_id = crm.convert(lead_id, 2000, "m1")
        crm.advance(opp_id, "proposal", "m1")
        crm.discount(opp_id, 5, "m1")
        crm.transfer(opp_id, "r1", "m1")
        self.assertEqual(crm.opps[opp_id]["owner"], "r1")


class TestQualify(unittest.TestCase):
    def test_score_below_threshold_rejected(self):
        cases = [
            ("web", "a@gmail.com", 10),
            ("web", "b@corp.com", 25),
            ("event", "c@gmail.com", 20),
            ("event", "d@corp.com", 35),  # accepted, checked separately below
        ]
        for source, email, expected_score in cases[:3]:
            with self.subTest(source=source, email=email):
                crm = wide_crm()
                lead_id = add(crm, email=email, source=source)
                self.assertEqual(crm.leads[lead_id]["score"], expected_score)
                with self.assertRaises(ValueError):
                    crm.qualify(lead_id, "r1")
                self.assertEqual(crm.leads[lead_id]["status"], "new")
                self.assertEqual(
                    crm.log, [("add_lead", lead_id, "r1")]
                )

        crm = wide_crm()
        lead_id = add(crm, email="d@corp.com", source="event")
        self.assertEqual(crm.leads[lead_id]["score"], 35)
        crm.qualify(lead_id, "r1")
        self.assertEqual(crm.leads[lead_id]["status"], "qualified")

    def test_referral_with_free_domain_meets_threshold(self):
        crm = wide_crm()
        lead_id = add(crm, email="x@gmail.com", source="referral")
        self.assertEqual(crm.leads[lead_id]["score"], 30)
        crm.qualify(lead_id, "r1")
        self.assertEqual(crm.leads[lead_id]["status"], "qualified")
        self.assertEqual(crm.log[-1], ("qualify", lead_id, "r1"))

    def test_unknown_lead(self):
        crm = wide_crm()
        with self.assertRaises(ValueError):
            crm.qualify("L404", "r1")

    def test_lead_must_be_new(self):
        crm = wide_crm()
        lead_id = add(crm, email="x@corp.com", source="referral")
        crm.qualify(lead_id, "r1")
        with self.assertRaises(ValueError):
            crm.qualify(lead_id, "r1")
        self.assertEqual(
            crm.log.count(("qualify", lead_id, "r1")), 1
        )

    def test_converted_lead_cannot_be_qualified(self):
        crm = wide_crm()
        lead_id = add(crm, email="x@corp.com", source="referral")
        crm.qualify(lead_id, "r1")
        crm.convert(lead_id, 1000, "r1")
        with self.assertRaises(ValueError):
            crm.qualify(lead_id, "r1")


class TestConvert(unittest.TestCase):
    def test_amount_must_be_positive_int_not_bool(self):
        crm = wide_crm()
        lead_id = add(crm, email="x@corp.com")
        crm.qualify(lead_id, "r1")
        for amount in (0, -1, 1.5, 10.0, "10", None, True, False):
            with self.subTest(amount=amount):
                with self.assertRaises(ValueError):
                    crm.convert(lead_id, amount, "r1")
                self.assertEqual(crm.leads[lead_id]["status"], "qualified")
                self.assertEqual(crm.opps, {})

    def test_lead_must_exist(self):
        crm = wide_crm()
        with self.assertRaises(ValueError):
            crm.convert("L404", 100, "r1")

    def test_lead_must_be_qualified(self):
        crm = wide_crm()
        lead_id = add(crm, email="x@corp.com")
        with self.assertRaises(ValueError):
            crm.convert(lead_id, 100, "r1")
        self.assertEqual(crm.opps, {})

    def test_amount_is_validated_before_permission(self):
        crm = wide_crm()
        lead_id = add(crm, email="x@corp.com")
        with self.assertRaises(ValueError):
            crm.convert(lead_id, -5, "r2")

    def test_permission_is_checked_before_status(self):
        crm = wide_crm()
        lead_id = add(crm, email="x@corp.com")  # still new
        with self.assertRaises(PermissionError):
            crm.convert(lead_id, 100, "r2")

    def test_successful_conversion_sets_fields_and_log(self):
        crm = wide_crm()
        lead_id = add(crm, email="x@corp.com")
        crm.qualify(lead_id, "r1")
        opp_id = crm.convert(lead_id, 1234, "r1")
        self.assertEqual(opp_id, "O1")
        self.assertEqual(
            crm.opps[opp_id],
            {
                "id": "O1",
                "lead_id": lead_id,
                "owner": "r1",
                "amount": 1234,
                "original_amount": 1234,
                "stage": "prospect",
            },
        )
        self.assertEqual(crm.leads[lead_id]["status"], "converted")
        self.assertEqual(crm.log[-1], ("convert", opp_id, "r1"))
        second_lead = add(crm, email="y@corp.com")
        crm.qualify(second_lead, "m1")
        self.assertEqual(crm.convert(second_lead, 500, "m1"), "O2")

    def test_failed_conversion_does_not_consume_opp_id(self):
        crm = wide_crm()
        lead_id = add(crm, email="x@corp.com")
        crm.qualify(lead_id, "r1")
        with self.assertRaises(ValueError):
            crm.convert(lead_id, 0, "r1")
        self.assertEqual(crm.convert(lead_id, 100, "r1"), "O1")

    def test_lead_without_owner_cannot_be_converted(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1}, {"id": "m1", "role": "manager", "capacity": 0}])
        add(crm, email="a@corp.com")
        queued = add(crm, email="b@corp.com")
        self.assertIsNone(crm.leads[queued]["owner"])
        crm.qualify(queued, "m1")  # managers may qualify a queued lead
        before = snapshot(crm)
        with self.assertRaises(ValueError):
            crm.convert(queued, 100, "m1")
        self.assertEqual(snapshot(crm), before)
        self.assertEqual(crm.opps, {})


class TestAdvance(unittest.TestCase):
    def test_happy_path_through_won(self):
        crm = wide_crm()
        opp_id, _ = make_opp(crm, amount=1000)
        for stage in ("proposal", "negotiation", "won"):
            crm.advance(opp_id, stage, "r1")
            self.assertEqual(crm.opps[opp_id]["stage"], stage)
            self.assertEqual(crm.log[-1], ("advance", opp_id, "r1"))

    def test_any_open_stage_may_go_lost(self):
        for steps in ((), ("proposal",), ("proposal", "negotiation")):
            with self.subTest(steps=steps):
                crm = wide_crm()
                opp_id, _ = make_opp(crm, amount=1000)
                for stage in steps:
                    crm.advance(opp_id, stage, "r1")
                crm.advance(opp_id, "lost", "r1")
                self.assertEqual(crm.opps[opp_id]["stage"], "lost")

    def test_invalid_stage_name(self):
        crm = wide_crm()
        opp_id, _ = make_opp(crm)
        for stage in ("closed", "", None, "PROPOSAL"):
            with self.subTest(stage=stage):
                with self.assertRaises(ValueError):
                    crm.advance(opp_id, stage, "r1")
                self.assertEqual(crm.opps[opp_id]["stage"], "prospect")

    def test_unknown_opportunity(self):
        crm = wide_crm()
        with self.assertRaises(ValueError):
            crm.advance("O404", "proposal", "r1")

    def test_stage_must_be_immediate_next_or_lost(self):
        bad_transitions = [
            ((), "negotiation"),
            ((), "won"),
            (("proposal",), "prospect"),
            (("proposal",), "won"),
            (("proposal", "negotiation"), "proposal"),
        ]
        for steps, target in bad_transitions:
            with self.subTest(steps=steps, target=target):
                crm = wide_crm()
                opp_id, _ = make_opp(crm)
                for stage in steps:
                    crm.advance(opp_id, stage, "r1")
                current = crm.opps[opp_id]["stage"]
                with self.assertRaises(ValueError):
                    crm.advance(opp_id, target, "r1")
                self.assertEqual(crm.opps[opp_id]["stage"], current)

    def test_final_stage_cannot_advance(self):
        for final in ("won", "lost"):
            with self.subTest(final=final):
                crm = wide_crm()
                opp_id, _ = make_opp(crm)
                if final == "won":
                    crm.advance(opp_id, "proposal", "r1")
                    crm.advance(opp_id, "negotiation", "r1")
                crm.advance(opp_id, final, "r1")
                for target in ("proposal", "lost", "won"):
                    with self.assertRaises(ValueError):
                        crm.advance(opp_id, target, "r1")

    def test_stage_name_is_validated_before_permission(self):
        crm = wide_crm()
        opp_id, _ = make_opp(crm)
        with self.assertRaises(ValueError):
            crm.advance(opp_id, "bogus", "r2")
        with self.assertRaises(PermissionError):
            crm.advance(opp_id, "proposal", "r2")

    def test_permission_checked_before_final_state(self):
        crm = wide_crm()
        opp_id, _ = make_opp(crm)
        crm.advance(opp_id, "lost", "r1")
        with self.assertRaises(PermissionError):
            crm.advance(opp_id, "proposal", "r2")

    def test_big_deal_requires_manager_for_negotiation(self):
        crm = wide_crm()
        opp_id, _ = make_opp(crm, amount=50001)
        crm.advance(opp_id, "proposal", "r1")
        with self.assertRaises(PermissionError):
            crm.advance(opp_id, "negotiation", "r1")
        self.assertEqual(crm.opps[opp_id]["stage"], "proposal")
        crm.advance(opp_id, "negotiation", "m1")
        self.assertEqual(crm.opps[opp_id]["stage"], "negotiation")

    def test_big_deal_threshold_is_strictly_greater_than_50000(self):
        crm = wide_crm()
        opp_id, _ = make_opp(crm, amount=50000)
        crm.advance(opp_id, "proposal", "r1")
        crm.advance(opp_id, "negotiation", "r1")
        self.assertEqual(crm.opps[opp_id]["stage"], "negotiation")

    def test_big_deal_gate_reads_current_amount_after_discount(self):
        """Spec line 30: the 50000 gate measures the current amount, not the original."""
        crm = wide_crm()
        opp_id, _ = make_opp(crm, amount=60000)
        crm.advance(opp_id, "proposal", "r1")
        crm.discount(opp_id, 30, "m1")  # 60000 -> 42000
        self.assertEqual(crm.opps[opp_id]["amount"], 42000)
        crm.advance(opp_id, "negotiation", "r1")  # no manager required any more
        self.assertEqual(crm.opps[opp_id]["stage"], "negotiation")

    def test_big_deal_check_only_applies_to_negotiation(self):
        crm = wide_crm()
        opp_id, _ = make_opp(crm, amount=90000)
        crm.advance(opp_id, "proposal", "r1")
        self.assertEqual(crm.opps[opp_id]["stage"], "proposal")
        with self.assertRaises(ValueError):
            crm.advance(opp_id, "won", "r1")  # transition fails before approval


class TestDiscount(unittest.TestCase):
    def test_pct_must_be_int_in_range(self):
        crm = wide_crm()
        opp_id, _ = make_opp(crm, amount=1000)
        for pct in (0, 31, -1, 1.5, 10.0, "10", None, True, False):
            with self.subTest(pct=pct):
                with self.assertRaises(ValueError):
                    crm.discount(opp_id, pct, "m1")
                self.assertEqual(crm.opps[opp_id]["amount"], 1000)

    def test_unknown_opportunity(self):
        crm = wide_crm()
        with self.assertRaises(ValueError):
            crm.discount("O404", 5, "m1")

    def test_pct_validated_before_permission(self):
        crm = wide_crm()
        opp_id, _ = make_opp(crm, amount=1000)
        with self.assertRaises(ValueError):
            crm.discount(opp_id, 99, "r2")

    def test_non_owner_rep_cannot_discount(self):
        crm = wide_crm()
        opp_id, _ = make_opp(crm, amount=1000)
        with self.assertRaises(PermissionError):
            crm.discount(opp_id, 5, "r2")

    def test_final_stage_cannot_be_discounted(self):
        crm = wide_crm()
        opp_id, _ = make_opp(crm, amount=1000)
        crm.advance(opp_id, "lost", "r1")
        with self.assertRaises(ValueError):
            crm.discount(opp_id, 5, "m1")
        self.assertEqual(crm.opps[opp_id]["amount"], 1000)

    def test_non_manager_discount_cap(self):
        crm = wide_crm()
        opp_id, _ = make_opp(crm, amount=1000)
        with self.assertRaises(PermissionError):
            crm.discount(opp_id, 11, "r1")
        self.assertEqual(crm.opps[opp_id]["amount"], 1000)
        crm.discount(opp_id, 10, "r1")
        self.assertEqual(crm.opps[opp_id]["amount"], 900)

    def test_manager_may_discount_up_to_thirty(self):
        crm = wide_crm()
        opp_id, _ = make_opp(crm, amount=1000)
        crm.discount(opp_id, 30, "m1")
        self.assertEqual(crm.opps[opp_id]["amount"], 700)
        self.assertEqual(crm.opps[opp_id]["original_amount"], 1000)
        self.assertEqual(crm.log[-1], ("discount", opp_id, "m1"))

    def test_cumulative_discount_floor_is_enforced(self):
        crm = wide_crm()
        opp_id, _ = make_opp(crm, amount=1000)
        crm.discount(opp_id, 30, "m1")
        self.assertEqual(crm.opps[opp_id]["amount"], 700)
        before = snapshot(crm)
        with self.assertRaises(ValueError):
            crm.discount(opp_id, 1, "m1")
        self.assertEqual(snapshot(crm), before)
        self.assertEqual(crm.opps[opp_id]["amount"], 700)

    def test_exactly_thirty_percent_total_is_allowed(self):
        crm = wide_crm()
        opp_id, _ = make_opp(crm, amount=100)
        crm.discount(opp_id, 30, "m1")
        self.assertEqual(crm.opps[opp_id]["amount"], 70)

    def test_non_manager_floor_still_applies(self):
        crm = wide_crm()
        opp_id, _ = make_opp(crm, amount=1000)
        crm.discount(opp_id, 10, "r1")
        crm.discount(opp_id, 10, "r1")
        crm.discount(opp_id, 10, "r1")
        self.assertEqual(crm.opps[opp_id]["amount"], 729)
        with self.assertRaises(ValueError):
            crm.discount(opp_id, 10, "r1")
        self.assertEqual(crm.opps[opp_id]["amount"], 729)

    def test_final_stage_is_checked_before_non_manager_cap(self):
        crm = wide_crm()
        opp_id, _ = make_opp(crm, amount=1000)
        crm.advance(opp_id, "lost", "r1")
        with self.assertRaises(ValueError):
            crm.discount(opp_id, 11, "r1")

    def test_permission_checked_before_final_stage(self):
        crm = wide_crm()
        opp_id, _ = make_opp(crm, amount=1000)
        crm.advance(opp_id, "lost", "r1")
        with self.assertRaises(PermissionError):
            crm.discount(opp_id, 5, "r2")


class TestTransfer(unittest.TestCase):
    def setUp(self):
        self.crm = wide_crm()
        self.opp_id, self.lead_id = make_opp(self.crm, amount=1000)

    def test_only_manager_may_transfer(self):
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.opp_id, "r2", "r1")
        self.assertEqual(self.crm.opps[self.opp_id]["owner"], "r1")

    def test_manager_permission_checked_before_final_stage(self):
        self.crm.advance(self.opp_id, "lost", "r1")
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.opp_id, "r2", "r1")

    def test_unknown_target(self):
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp_id, "ghost", "m1")

    def test_target_must_be_a_rep(self):
        crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 5},
                {"id": "m1", "role": "manager", "capacity": 5},
            ]
        )
        lead_id = add(crm, email="a@corp.com", actor="r1")
        crm.qualify(lead_id, "m1")
        opp_id = crm.convert(lead_id, 1000, "m1")
        with self.assertRaises(ValueError):
            crm.transfer(opp_id, "m1", "m1")
        self.assertEqual(crm.opps[opp_id]["owner"], "r1")

    def test_unknown_opportunity(self):
        with self.assertRaises(ValueError):
            self.crm.transfer("O404", "r2", "m1")
        with self.assertRaises(ValueError):
            self.crm.transfer("O404", "r2", "r1")

    def test_manager_permission_checked_before_target(self):
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.opp_id, "ghost", "r1")

    def test_final_opportunity_cannot_be_transferred(self):
        self.crm.advance(self.opp_id, "lost", "r1")
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp_id, "r2", "m1")

    def test_same_owner_rejected(self):
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp_id, "r1", "m1")

    def test_target_must_have_capacity(self):
        crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 1},
                {"id": "r2", "role": "rep", "capacity": 1},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        first = add(crm, email="a@corp.com")
        add(crm, email="b@corp.com")  # fills r2
        crm.qualify(first, "m1")
        opp_id = crm.convert(first, 1000, "m1")
        with self.assertRaises(ValueError):
            crm.transfer(opp_id, "r2", "m1")
        self.assertEqual(crm.opps[opp_id]["owner"], "r1")

    def test_successful_transfer_updates_owner_and_logs(self):
        before_log = list(self.crm.log)
        self.crm.transfer(self.opp_id, "r2", "m1")
        self.assertEqual(self.crm.opps[self.opp_id]["owner"], "r2")
        self.assertEqual(
            self.crm.log, before_log + [("transfer", self.opp_id, "m1")]
        )
        self.assertEqual(self.crm.leads[self.lead_id]["owner"], "r1")

    def test_transfer_to_rep_with_free_capacity_succeeds(self):
        crm = wide_crm()
        add(crm, email="fill1@corp.com")  # r1 gets a lead
        add(crm, email="fill2@corp.com")  # r2 gets a lead
        opp_id, _ = make_opp(crm, amount=1000, email="third@corp.com")
        crm.transfer(opp_id, "r2", "m1")
        self.assertEqual(crm.opps[opp_id]["owner"], "r2")


class TestForecast(unittest.TestCase):
    def test_empty_forecast(self):
        self.assertEqual(wide_crm().forecast(), {"open": 0, "weighted": 0, "won": 0})

    def test_weighted_value_by_stage(self):
        crm = wide_crm()
        o1, _ = make_opp(crm, amount=105, email="a@corp.com")
        o2, _ = make_opp(crm, amount=200, email="b@corp.com")
        o3, _ = make_opp(crm, amount=300, email="c@corp.com")
        crm.advance(o2, "proposal", "m1")
        crm.advance(o3, "proposal", "m1")
        crm.advance(o3, "negotiation", "m1")
        self.assertEqual(
            crm.forecast(), {"open": 3, "weighted": 10 + 60 + 180, "won": 0}
        )
        self.assertEqual(crm.opps[o1]["stage"], "prospect")

    def test_final_stages_excluded_and_won_summed(self):
        crm = wide_crm()
        o1, _ = make_opp(crm, amount=100, email="a@corp.com")
        o2, _ = make_opp(crm, amount=200, email="b@corp.com")
        o3, _ = make_opp(crm, amount=300, email="c@corp.com")
        crm.advance(o2, "proposal", "m1")
        crm.advance(o3, "proposal", "m1")
        crm.advance(o3, "negotiation", "m1")
        crm.advance(o1, "lost", "m1")
        crm.advance(o3, "won", "m1")
        self.assertEqual(crm.forecast(), {"open": 1, "weighted": 60, "won": 300})

    def test_weighted_value_uses_current_amount_after_discount(self):
        """Spec line 42: weighting applies to the current amount, not the original."""
        crm = wide_crm()
        opp_id, _ = make_opp(crm, amount=10000, email="a@corp.com")
        crm.advance(opp_id, "proposal", "m1")
        crm.discount(opp_id, 30, "m1")  # 10000 -> 7000
        self.assertEqual(crm.opps[opp_id]["amount"], 7000)
        self.assertEqual(crm.forecast(), {"open": 1, "weighted": 2100, "won": 0})

    def test_forecast_does_not_log(self):
        crm = wide_crm()
        make_opp(crm, amount=1000)
        before = snapshot(crm)
        crm.forecast()
        self.assertEqual(snapshot(crm), before)


if __name__ == "__main__":
    unittest.main()
