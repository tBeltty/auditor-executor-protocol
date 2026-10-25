"""Tests for qualify, convert, advance, discount, transfer, forecast, and
the general rules (actor checks, log entries, atomicity)."""

import unittest

from crm import CRM, DuplicateLeadError


def build(reps=None):
    if reps is None:
        reps = [
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 9},
        ]
    return CRM([dict(r) for r in reps])


def make_opp(crm, email="a@acme.com", amount=1000, rep="r1", actor=None):
    lead_id = crm.add_lead(email, "N", "referral", rep)
    crm.qualify(lead_id, actor if actor else rep)
    return crm.convert(lead_id, amount, actor if actor else rep), lead_id


class QualifyTests(unittest.TestCase):
    def setUp(self):
        self.crm = build()
        self.lead_id = self.crm.add_lead("a@acme.com", "A", "referral", "r1")

    def test_owner_qualifies(self):
        self.crm.qualify(self.lead_id, "r1")
        self.assertEqual(self.crm.leads[self.lead_id]["status"], "qualified")
        self.assertEqual(self.crm.log,
                         [("add_lead", "L1", "r1"), ("qualify", "L1", "r1")])

    def test_manager_qualifies_others_lead(self):
        self.crm.qualify(self.lead_id, "m1")
        self.assertEqual(self.crm.leads[self.lead_id]["status"], "qualified")

    def test_other_rep_forbidden(self):
        with self.assertRaises(PermissionError):
            self.crm.qualify(self.lead_id, "r2")
        self.assertEqual(self.crm.leads[self.lead_id]["status"], "new")
        self.assertEqual(len(self.crm.log), 1)

    def test_unknown_lead_value_error(self):
        with self.assertRaises(ValueError):
            self.crm.qualify("L99", "r1")

    def test_low_score_rejected(self):
        lead = self.crm.add_lead("b@gmail.com", "B", "web", "r2")
        with self.assertRaises(ValueError):
            self.crm.qualify(lead, "r2")
        self.assertEqual(self.crm.leads[lead]["status"], "new")

    def test_event_custom_domain_qualifies(self):
        lead = self.crm.add_lead("c@corp.com", "C", "event", "r2")
        self.crm.qualify(lead, "m1")  # event custom = 20+15 = 35 >= 30

    def test_double_qualify_rejected(self):
        self.crm.qualify(self.lead_id, "r1")
        with self.assertRaises(ValueError):
            self.crm.qualify(self.lead_id, "r1")

    def test_check_order(self):
        # unknown lead beats bad score; not-owner beats wrong status
        self.crm.qualify(self.lead_id, "r1")
        with self.assertRaises(PermissionError):
            self.crm.qualify(self.lead_id, "r2")  # wrong actor before status


class ConvertTests(unittest.TestCase):
    def setUp(self):
        self.crm = build()
        self.lead_id = self.crm.add_lead("a@acme.com", "A", "referral", "r1")
        self.crm.qualify(self.lead_id, "r1")

    def test_success(self):
        opp_id = self.crm.convert(self.lead_id, 2500, "r1")
        self.assertEqual(opp_id, "O1")
        self.assertEqual(self.crm.opps["O1"], {
            "id": "O1", "lead_id": "L1", "owner": "r1",
            "amount": 2500, "original_amount": 2500, "stage": "prospect",
        })
        self.assertEqual(self.crm.leads[self.lead_id]["status"], "converted")
        self.assertEqual(self.crm.log[-1], ("convert", "O1", "r1"))

    def test_amount_validation(self):
        for bad in [0, -5, True, False, 1.5, "2500", None]:
            with self.subTest(amount=bad):
                with self.assertRaises(ValueError):
                    self.crm.convert(self.lead_id, bad, "r1")

    def test_needs_qualified(self):
        lead = self.crm.add_lead("z@acme.com", "Z", "referral", "r2")
        with self.assertRaises(ValueError):
            self.crm.convert(lead, 100, "r2")

    def test_needs_owner(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 0},
                   {"id": "m1", "role": "manager", "capacity": 9}])
        lead = crm.add_lead("q@acme.com", "Q", "referral", "m1")  # waiting
        crm.qualify(lead, "m1")
        with self.assertRaises(ValueError):
            crm.convert(lead, 100, "m1")

    def test_permission(self):
        with self.assertRaises(PermissionError):
            self.crm.convert(self.lead_id, 100, "r2")
        opp = self.crm.convert(self.lead_id, 100, "m1")  # manager ok
        self.assertEqual(self.crm.opps[opp]["owner"], "r1")

    def test_failed_convert_consumes_no_id(self):
        with self.assertRaises(ValueError):
            self.crm.convert(self.lead_id, 0, "r1")
        self.assertEqual(self.crm.convert(self.lead_id, 100, "r1"), "O1")

    def test_unknown_lead(self):
        with self.assertRaises(ValueError):
            self.crm.convert("L99", 100, "r1")


class AdvanceTests(unittest.TestCase):
    def setUp(self):
        self.crm = build()
        self.opp_id, self.lead_id = make_opp(self.crm)

    def test_happy_path(self):
        self.crm.advance(self.opp_id, "proposal", "r1")
        self.crm.advance(self.opp_id, "negotiation", "r1")
        self.crm.advance(self.opp_id, "won", "r1")
        self.assertEqual(self.crm.opps[self.opp_id]["stage"], "won")
        self.assertEqual(self.crm.log, [
            ("add_lead", "L1", "r1"), ("qualify", "L1", "r1"),
            ("convert", "O1", "r1"), ("advance", "O1", "r1"),
            ("advance", "O1", "r1"), ("advance", "O1", "r1"),
        ])

    def test_wrong_stage_order(self):
        for stage in ["won", "negotiation", "prospect"]:
            with self.subTest(stage=stage):
                with self.assertRaises(ValueError):
                    self.crm.advance(self.opp_id, stage, "r1")
        self.assertEqual(self.crm.opps[self.opp_id]["stage"], "prospect")

    def test_lost_anytime(self):
        self.crm.advance(self.opp_id, "proposal", "m1")
        self.crm.advance(self.opp_id, "lost", "m1")
        self.assertEqual(self.crm.opps[self.opp_id]["stage"], "lost")

    def test_final_stages_are_final(self):
        self.crm.advance(self.opp_id, "lost", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp_id, "proposal", "r1")

    def test_invalid_stage_name(self):
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp_id, "closing", "r1")

    def test_permission(self):
        with self.assertRaises(PermissionError):
            self.crm.advance(self.opp_id, "proposal", "r2")

    def test_unknown_opp(self):
        with self.assertRaises(ValueError):
            self.crm.advance("O99", "proposal", "r1")

    def test_negotiation_big_amount_needs_manager(self):
        crm = build()
        opp, _ = make_opp(crm, email="x@acme.com", amount=50001)
        crm.advance(opp, "proposal", "r1")
        with self.assertRaises(PermissionError):
            crm.advance(opp, "negotiation", "r1")
        crm.advance(opp, "negotiation", "m1")
        self.assertEqual(crm.opps[opp]["stage"], "negotiation")

    def test_negotiation_at_50000_ok_for_rep(self):
        crm = build()
        opp, _ = make_opp(crm, email="y@acme.com", amount=50000)
        crm.advance(opp, "proposal", "r1")
        crm.advance(opp, "negotiation", "r1")

    def test_failed_advance_no_slot_free_no_assign(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1}])
        l1 = crm.add_lead("a@acme.com", "A", "referral", "r1")
        l2 = crm.add_lead("b@acme.com", "B", "referral", "r1")  # waiting
        crm.qualify(l1, "r1")
        opp = crm.convert(l1, 1000, "r1")
        with self.assertRaises(ValueError):
            crm.advance(opp, "won", "r1")  # skipping stages
        self.assertIsNone(crm.leads[l2]["owner"])
        self.assertEqual(crm.log[-1], ("convert", "O1", "r1"))


class SlotFreeingTests(unittest.TestCase):
    def test_win_assigns_waiting_fifo(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 2}])
        l1 = crm.add_lead("a@acme.com", "A", "referral", "r1")  # r1 load 1
        l2 = crm.add_lead("b@acme.com", "B", "referral", "r1")  # r1 load 2
        l3 = crm.add_lead("c@acme.com", "C", "referral", "r1")  # waiting
        l4 = crm.add_lead("d@acme.com", "D", "referral", "r1")  # waiting
        crm.qualify(l1, "r1")
        opp = crm.convert(l1, 1000, "r1")
        crm.advance(opp, "proposal", "r1")
        crm.advance(opp, "negotiation", "r1")
        crm.advance(opp, "won", "r1")
        self.assertEqual(crm.leads[l3]["owner"], "r1")   # oldest gets the slot
        self.assertIsNone(crm.leads[l4]["owner"])        # r1 full again
        self.assertEqual(crm.log[-1], ("assign", l3, "system"))
        # second closing frees the next slot and takes the next-oldest
        crm.qualify(l2, "r1")
        opp2 = crm.convert(l2, 1000, "r1")
        crm.advance(opp2, "lost", "r1")
        self.assertEqual(crm.leads[l4]["owner"], "r1")
        self.assertEqual(crm.log[-1], ("assign", l4, "system"))

    def test_queue_order_survives_qualification_by_manager(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1},
                   {"id": "m1", "role": "manager", "capacity": 9}])
        l1 = crm.add_lead("a@acme.com", "A", "referral", "r1")
        l2 = crm.add_lead("b@acme.com", "B", "referral", "r1")  # waiting
        crm.qualify(l2, "m1")   # waiting lead may be qualified by manager
        crm.qualify(l1, "r1")
        opp = crm.convert(l1, 100, "r1")
        crm.advance(opp, "lost", "r1")
        self.assertEqual(crm.leads[l2]["owner"], "r1")
        self.assertEqual(crm.leads[l2]["status"], "qualified")

    def test_lost_also_frees(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1}])
        l1 = crm.add_lead("a@acme.com", "A", "referral", "r1")
        l2 = crm.add_lead("b@acme.com", "B", "referral", "r1")
        crm.qualify(l1, "r1")
        opp = crm.convert(l1, 1000, "r1")
        crm.advance(opp, "lost", "r1")
        self.assertEqual(crm.leads[l2]["owner"], "r1")
        self.assertEqual(crm.log[-1], ("assign", l2, "system"))

    def test_load_counts_only_open_items(self):
        # converted lead + open opp: converted lead leaves the load, the
        # open opp takes its place.
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1}])
        l1 = crm.add_lead("a@acme.com", "A", "referral", "r1")
        crm.qualify(l1, "r1")
        opp = crm.convert(l1, 1000, "r1")
        l2 = crm.add_lead("b@acme.com", "B", "referral", "r1")
        self.assertIsNone(crm.leads[l2]["owner"])  # r1 load = 1 (open opp)


class DiscountTests(unittest.TestCase):
    def setUp(self):
        self.crm = build()
        self.opp_id, _ = make_opp(self.crm, amount=1000)

    def test_owner_small_discount(self):
        self.crm.discount(self.opp_id, 10, "r1")
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 900)
        self.assertEqual(self.crm.opps[self.opp_id]["original_amount"], 1000)
        self.assertEqual(self.crm.log[-1], ("discount", "O1", "r1"))

    def test_rep_cannot_exceed_10(self):
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp_id, 11, "r1")
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 1000)

    def test_manager_up_to_30(self):
        self.crm.discount(self.opp_id, 30, "m1")
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 700)

    def test_cumulative_floor_70_percent(self):
        self.crm.discount(self.opp_id, 25, "m1")   # 1000 -> 750
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp_id, 10, "m1")  # 675 -> below 700 floor
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 750)
        self.crm.discount(self.opp_id, 6, "m1")     # 750 -> 705, ok (>= 700)
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 705)

    def test_pct_validation(self):
        for bad in [0, 31, -1, True, False, 1.0, "5", None]:
            with self.subTest(pct=bad):
                with self.assertRaises(ValueError):
                    self.crm.discount(self.opp_id, bad, "m1")

    def test_final_stage_rejected(self):
        self.crm.advance(self.opp_id, "proposal", "r1")
        self.crm.advance(self.opp_id, "negotiation", "r1")
        self.crm.advance(self.opp_id, "won", "m1")
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp_id, 5, "m1")

    def test_permission(self):
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp_id, 5, "r2")

    def test_failed_discount_no_log(self):
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp_id, 20, "r1")
        self.assertEqual(self.crm.log[-1], ("convert", "O1", "r1"))


class TransferTests(unittest.TestCase):
    def setUp(self):
        self.crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 2},
            {"id": "r2", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 9},
        ])
        self.opp_id, self.lead_id = make_opp(self.crm)

    def test_manager_transfers(self):
        self.crm.transfer(self.opp_id, "r2", "m1")
        self.assertEqual(self.crm.opps[self.opp_id]["owner"], "r2")
        self.assertEqual(self.crm.log[-1], ("transfer", "O1", "m1"))

    def test_only_managers(self):
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.opp_id, "r2", "r1")

    def test_new_owner_must_be_rep(self):
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp_id, "m1", "m1")
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp_id, "ghost", "m1")

    def test_final_stage(self):
        self.crm.advance(self.opp_id, "lost", "r1")
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp_id, "r2", "m1")

    def test_same_owner_rejected(self):
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp_id, "r1", "m1")

    def test_target_capacity(self):
        l2 = self.crm.add_lead("b@acme.com", "B", "referral", "m1")
        self.crm.qualify(l2, "m1")
        opp2 = self.crm.convert(l2, 10, "m1")  # r2 owns opp2 -> load 1
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp_id, "r2", "m1")
        self.assertEqual(self.crm.opps[self.opp_id]["owner"], "r1")

    def test_transfer_frees_previous_owner_slot(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 9},
        ])
        l1 = crm.add_lead("a@acme.com", "A", "referral", "r1")   # r1
        l2 = crm.add_lead("b@acme.com", "B", "referral", "r1")   # r2
        crm.qualify(l1, "r1")
        opp1 = crm.convert(l1, 100, "r1")     # r1 load = open opp1
        crm.qualify(l2, "m1")
        opp2 = crm.convert(l2, 100, "m1")     # r2 load = open opp2
        crm.advance(opp1, "proposal", "r1")
        crm.advance(opp1, "negotiation", "r1")
        crm.advance(opp1, "won", "r1")        # r1 load 0
        crm.transfer(opp2, "r1", "m1")        # r2 freed, queue empty
        self.assertEqual(crm.opps[opp2]["owner"], "r1")
        self.assertNotIn("assign", [entry[0] for entry in crm.log])
        # next lead routes to the rep that just got its slot back
        l3 = crm.add_lead("c@acme.com", "C", "web", "r1")
        self.assertEqual(crm.leads[l3]["owner"], "r2")

    def test_transfer_drains_waiting_queue_of_previous_owner(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 9},
        ])
        l1 = crm.add_lead("a@acme.com", "A", "referral", "r1")   # r1
        l2 = crm.add_lead("b@acme.com", "B", "referral", "r1")   # r2
        l3 = crm.add_lead("c@acme.com", "C", "referral", "r1")   # waiting
        crm.qualify(l1, "r1")
        opp1 = crm.convert(l1, 100, "r1")
        # grow r2's capacity directly (opening a slot does not drain the
        # queue -- only advance/transfer closing does)
        crm.users["r2"]["capacity"] = 2
        crm.transfer(opp1, "r2", "m1")
        self.assertEqual(crm.leads[l3]["owner"], "r1")  # oldest waiting
        self.assertEqual(crm.log[-1], ("assign", l3, "system"))


class ForecastTests(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(build().forecast(),
                         {"open": 0, "weighted": 0, "won": 0})

    def test_weights(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 50}])
        o1, _ = make_opp(crm, "a@acme.com", 1000)         # prospect 100
        o2, _ = make_opp(crm, "b@acme.com", 2000)
        crm.advance(o2, "proposal", "r1")                 # 2000*30/100=600
        o3, _ = make_opp(crm, "c@acme.com", 3000)
        crm.advance(o3, "proposal", "r1")
        crm.advance(o3, "negotiation", "r1")              # 3000*60/100=1800
        o4, _ = make_opp(crm, "d@acme.com", 4000)
        crm.advance(o4, "lost", "r1")
        o5, _ = make_opp(crm, "e@acme.com", 5000)
        crm.advance(o5, "proposal", "r1")
        crm.advance(o5, "negotiation", "r1")
        crm.advance(o5, "won", "r1")
        self.assertEqual(crm.forecast(),
                         {"open": 3, "weighted": 100 + 600 + 1800,
                          "won": 5000})

    def test_weighted_uses_discounted_amount(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 50}])
        opp, _ = make_opp(crm, "a@acme.com", 1000)
        crm.discount(opp, 10, "r1")  # 900 prospect -> 90
        self.assertEqual(crm.forecast(), {"open": 1, "weighted": 90, "won": 0})

    def test_forecast_logs_nothing(self):
        crm = build()
        before = list(crm.log)
        crm.forecast()
        self.assertEqual(crm.log, before)


class GeneralRulesTests(unittest.TestCase):
    def test_failed_calls_change_nothing(self):
        crm = build()
        lead = crm.add_lead("a@acme.com", "A", "referral", "r1")
        snapshot_leads = {k: dict(v) for k, v in crm.leads.items()}
        log_len = len(crm.log)
        with self.assertRaises(DuplicateLeadError):
            crm.add_lead("a@acme.com", "Dup", "web", "r1")  # duplicate
        with self.assertRaises(PermissionError):
            crm.qualify(lead, "r2")
        with self.assertRaises(ValueError):
            crm.convert(lead, 0, "r1")
        self.assertEqual(crm.leads, snapshot_leads)
        self.assertEqual(len(crm.opps), 0)
        self.assertEqual(len(crm.log), log_len)

    def test_duplicate_lead_error_type(self):
        self.assertTrue(issubclass(DuplicateLeadError, Exception))

    def test_attributes_exist(self):
        crm = build()
        self.assertIsInstance(crm.leads, dict)
        self.assertIsInstance(crm.opps, dict)
        self.assertIsInstance(crm.log, list)
        self.assertEqual(crm.log, [])


if __name__ == "__main__":
    unittest.main()
