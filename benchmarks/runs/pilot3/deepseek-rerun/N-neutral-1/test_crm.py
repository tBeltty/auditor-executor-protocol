"""Unit tests for crm.py (lead capture, pipeline, discounts, forecast)."""

import copy
import unittest

from crm import CRM, DuplicateLeadError


def make_crm(reps=None):
    if reps is None:
        reps = [
            {"id": "r1", "role": "rep", "capacity": 2},
            {"id": "r2", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 0},
        ]
    return CRM(reps)


def pipeline(crm, lead_id, amount, actor="m1"):
    """Qualify and convert a lead as a manager; return the opportunity id."""
    crm.qualify(lead_id, actor)
    return crm.convert(lead_id, amount, actor)


class AddLeadTests(unittest.TestCase):
    def test_basic_creation_normalizes_and_logs(self):
        crm = make_crm()
        lid = crm.add_lead("  A@Corp.COM ", "  Ann  ", "referral", "r1")
        self.assertEqual(lid, "L1")
        self.assertEqual(
            crm.leads["L1"],
            {
                "id": "L1",
                "email": "a@corp.com",
                "name": "Ann",
                "source": "referral",
                "score": 45,
                "owner": "r1",
                "status": "new",
            },
        )
        self.assertEqual(crm.log, [("add_lead", "L1", "r1")])

    def test_invalid_emails(self):
        crm = make_crm()
        for bad in [
            123,
            None,
            "",
            "   ",
            "ab.com",
            "a@@b.com",
            "@b.com",
            "a@b",
            "a@.com",
            "a@com.",
            "a@b@c.com",
        ]:
            with self.subTest(email=bad):
                with self.assertRaises(ValueError):
                    crm.add_lead(bad, "Ann", "web", "r1")
        self.assertEqual(crm.leads, {})
        self.assertEqual(crm.log, [])

    def test_single_character_domain_labels_are_valid(self):
        crm = make_crm()
        crm.add_lead("a@b.c", "Ann", "web", "r1")
        self.assertIn("L1", crm.leads)

    def test_name_and_source_validation(self):
        crm = make_crm()
        with self.assertRaises(ValueError):
            crm.add_lead("a@corp.com", 7, "web", "r1")
        with self.assertRaises(ValueError):
            crm.add_lead("a@corp.com", "   ", "web", "r1")
        with self.assertRaises(ValueError):
            crm.add_lead("a@corp.com", "Ann", "phone", "r1")
        with self.assertRaises(ValueError):
            crm.add_lead("a@corp.com", "Ann", ["web"], "r1")
        self.assertEqual(crm.leads, {})
        self.assertEqual(crm.log, [])

    def test_scoring(self):
        crm = make_crm(
            [{"id": "r1", "role": "rep", "capacity": 10}]
        )
        crm.add_lead("a@gmail.com", "A", "web", "r1")
        crm.add_lead("b@yahoo.com", "B", "referral", "r1")
        crm.add_lead("c@outlook.com", "C", "event", "r1")
        crm.add_lead("d@corp.com", "D", "web", "r1")
        crm.add_lead("e@corp.com", "E", "event", "r1")
        crm.add_lead("f@corp.com", "F", "referral", "r1")
        self.assertEqual(crm.leads["L1"]["score"], 10)
        self.assertEqual(crm.leads["L2"]["score"], 30)
        self.assertEqual(crm.leads["L3"]["score"], 20)
        self.assertEqual(crm.leads["L4"]["score"], 25)
        self.assertEqual(crm.leads["L5"]["score"], 35)
        self.assertEqual(crm.leads["L6"]["score"], 45)

    def test_duplicate_lead_error(self):
        crm = make_crm()
        crm.add_lead("a@corp.com", "Ann", "web", "r1")
        before = copy.deepcopy(crm.leads)
        with self.assertRaises(DuplicateLeadError) as ctx:
            crm.add_lead("  A@CORP.com ", "Other", "event", "r1")
        self.assertEqual(ctx.exception.existing_id, "L1")
        self.assertIsInstance(ctx.exception, Exception)
        self.assertEqual(crm.leads, before)
        self.assertEqual(crm.log, [("add_lead", "L1", "r1")])
        # the failed creation must not consume an id
        self.assertEqual(crm.add_lead("b@corp.com", "Bob", "web", "r1"), "L2")

    def test_owner_selection_and_queue(self):
        crm = make_crm()
        self.assertEqual(crm.add_lead("a@corp.com", "A", "web", "r1"), "L1")
        self.assertEqual(crm.add_lead("b@corp.com", "B", "web", "r1"), "L2")
        self.assertEqual(crm.add_lead("c@corp.com", "C", "web", "r1"), "L3")
        self.assertEqual(crm.add_lead("d@corp.com", "D", "web", "r1"), "L4")
        self.assertEqual(crm.leads["L1"]["owner"], "r1")
        self.assertEqual(crm.leads["L2"]["owner"], "r2")
        self.assertEqual(crm.leads["L3"]["owner"], "r1")
        self.assertIsNone(crm.leads["L4"]["owner"])
        self.assertEqual(
            crm.log[-1], ("add_lead", "L4", "r1")
        )

    def test_managers_never_own_and_ties_use_smallest_id(self):
        crm = make_crm(
            [
                {"id": "b", "role": "rep", "capacity": 5},
                {"id": "a", "role": "rep", "capacity": 5},
                {"id": "m", "role": "manager", "capacity": 5},
            ]
        )
        crm.add_lead("x@corp.com", "X", "web", "m")
        crm.add_lead("y@corp.com", "Y", "web", "m")
        self.assertEqual(crm.leads["L1"]["owner"], "a")
        self.assertEqual(crm.leads["L2"]["owner"], "b")

    def test_all_reps_full_goes_to_queue(self):
        crm = make_crm([{"id": "m", "role": "manager", "capacity": 5}])
        crm.add_lead("x@corp.com", "X", "web", "m")
        self.assertIsNone(crm.leads["L1"]["owner"])


class QualifyTests(unittest.TestCase):
    def test_qualify_success(self):
        crm = make_crm()
        crm.add_lead("a@corp.com", "A", "referral", "r1")  # score 45
        crm.qualify("L1", "r1")
        self.assertEqual(crm.leads["L1"]["status"], "qualified")
        self.assertEqual(crm.log[-1], ("qualify", "L1", "r1"))

    def test_manager_may_qualify_any_lead(self):
        crm = make_crm()
        crm.add_lead("a@corp.com", "A", "referral", "r1")
        crm.qualify("L1", "m1")
        self.assertEqual(crm.leads["L1"]["status"], "qualified")

    def test_qualify_requires_existence(self):
        crm = make_crm()
        with self.assertRaises(ValueError):
            crm.qualify("L99", "r1")

    def test_qualify_requires_owner_or_manager(self):
        crm = make_crm()
        crm.add_lead("a@corp.com", "A", "referral", "r1")
        with self.assertRaises(PermissionError):
            crm.qualify("L1", "r2")
        self.assertEqual(crm.leads["L1"]["status"], "new")
        self.assertEqual(len(crm.log), 1)

    def test_qualify_requires_new_status(self):
        crm = make_crm()
        crm.add_lead("a@corp.com", "A", "referral", "r1")
        crm.qualify("L1", "r1")
        with self.assertRaises(ValueError):
            crm.qualify("L1", "r1")

    def test_qualify_requires_score_at_least_30(self):
        crm = make_crm([{"id": "r1", "role": "rep", "capacity": 10}])
        for i, (source, email, score) in enumerate(
            [
                ("web", "w@gmail.com", 10),
                ("event", "e@gmail.com", 20),
                ("web", "wc@corp.com", 25),
            ]
        ):
            lid = crm.add_lead(email, "N", source, "r1")
            with self.subTest(score=score):
                with self.assertRaises(ValueError):
                    crm.qualify(lid, "r1")
        ok = crm.add_lead("g@gmail.com", "N", "referral", "r1")  # 30
        crm.qualify(ok, "r1")
        self.assertEqual(crm.leads[ok]["status"], "qualified")

    def test_error_order_permission_before_status(self):
        crm = make_crm()
        crm.add_lead("a@corp.com", "A", "web", "r1")
        # already-not-qualifiable status, but the stranger is rejected first
        with self.assertRaises(PermissionError):
            crm.qualify("L1", "r2")


class ConvertTests(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        self.crm.add_lead("a@corp.com", "A", "referral", "r1")

    def test_convert_success(self):
        self.crm.qualify("L1", "r1")
        oid = self.crm.convert("L1", 1500, "r1")
        self.assertEqual(oid, "O1")
        self.assertEqual(
            self.crm.opps["O1"],
            {
                "id": "O1",
                "lead_id": "L1",
                "owner": "r1",
                "amount": 1500,
                "original_amount": 1500,
                "stage": "prospect",
            },
        )
        self.assertEqual(self.crm.leads["L1"]["status"], "converted")
        self.assertEqual(self.crm.log[-1], ("convert", "O1", "r1"))

    def test_amount_validation(self):
        self.crm.qualify("L1", "m1")
        for bad in [0, -1, 1.5, "10", True, False, None]:
            with self.subTest(amount=bad):
                with self.assertRaises(ValueError):
                    self.crm.convert("L1", bad, "m1")
        self.assertEqual(self.crm.opps, {})
        self.assertEqual(self.crm.leads["L1"]["status"], "qualified")

    def test_amount_checked_before_permission(self):
        self.crm.qualify("L1", "m1")
        with self.assertRaises(ValueError):
            self.crm.convert("L1", 0, "r2")  # stranger, but amount is bad

    def test_permission(self):
        self.crm.qualify("L1", "m1")
        with self.assertRaises(PermissionError):
            self.crm.convert("L1", 100, "r2")
        self.assertEqual(self.crm.opps, {})

    def test_requires_qualified(self):
        with self.assertRaises(ValueError):
            self.crm.convert("L1", 100, "m1")

    def test_requires_owner(self):
        crm = make_crm([{"id": "r1", "role": "rep", "capacity": 0},
                        {"id": "m1", "role": "manager", "capacity": 0}])
        crm.add_lead("q@corp.com", "Q", "referral", "m1")
        crm.qualify("L1", "m1")
        with self.assertRaises(ValueError):
            crm.convert("L1", 100, "m1")

    def test_conversion_ids_count_successes(self):
        self.crm.add_lead("b@corp.com", "B", "referral", "r1")
        self.crm.qualify("L1", "m1")
        self.crm.qualify("L2", "m1")
        self.assertEqual(self.crm.convert("L1", 100, "m1"), "O1")
        with self.assertRaises(ValueError):
            self.crm.convert("L1", 100, "m1")  # already converted
        self.assertEqual(self.crm.convert("L2", 200, "m1"), "O2")


class AdvanceTests(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm(
            [{"id": "r1", "role": "rep", "capacity": 10},
             {"id": "r2", "role": "rep", "capacity": 10},
             {"id": "m1", "role": "manager", "capacity": 0}]
        )
        self.crm.add_lead("a@corp.com", "A", "referral", "r1")
        self.oid = pipeline(self.crm, "L1", 1000)

    def test_happy_path_and_log(self):
        self.crm.advance("O1", "proposal", "r1")
        self.crm.advance("O1", "negotiation", "r1")
        self.crm.advance("O1", "won", "r1")
        self.assertEqual(self.crm.opps["O1"]["stage"], "won")
        self.assertEqual(
            self.crm.log[-3:],
            [
                ("advance", "O1", "r1"),
                ("advance", "O1", "r1"),
                ("advance", "O1", "r1"),
            ],
        )

    def test_lost_from_non_final(self):
        self.crm.advance("O1", "proposal", "r1")
        self.crm.advance("O1", "lost", "r1")
        self.assertEqual(self.crm.opps["O1"]["stage"], "lost")

    def test_invalid_stage(self):
        for bad in ["closed", "PROSPECT", None, 3, []]:
            with self.subTest(stage=bad):
                with self.assertRaises(ValueError):
                    self.crm.advance("O1", bad, "r1")

    def test_must_move_one_step_forward(self):
        with self.assertRaises(ValueError):
            self.crm.advance("O1", "negotiation", "r1")
        self.crm.advance("O1", "proposal", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance("O1", "won", "r1")
        self.crm.advance("O1", "negotiation", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance("O1", "proposal", "r1")

    def test_cannot_advance_final(self):
        self.crm.advance("O1", "lost", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance("O1", "proposal", "r1")

    def test_permission(self):
        with self.assertRaises(PermissionError):
            self.crm.advance("O1", "proposal", "r2")
        self.crm.advance("O1", "proposal", "m1")

    def test_large_deal_needs_manager_at_negotiation(self):
        crm = make_crm([{"id": "r1", "role": "rep", "capacity": 10},
                        {"id": "m1", "role": "manager", "capacity": 0}])
        crm.add_lead("big@corp.com", "Big", "referral", "m1")
        oid = pipeline(crm, "L1", 60000)
        crm.advance(oid, "proposal", "r1")
        with self.assertRaises(PermissionError):
            crm.advance(oid, "negotiation", "r1")
        self.assertEqual(crm.opps[oid]["stage"], "proposal")
        crm.advance(oid, "negotiation", "m1")
        self.assertEqual(crm.opps[oid]["stage"], "negotiation")

    def test_large_deal_amount_is_current_amount(self):
        crm = make_crm([{"id": "r1", "role": "rep", "capacity": 10},
                        {"id": "m1", "role": "manager", "capacity": 0}])
        crm.add_lead("a@corp.com", "A", "referral", "r1")
        oid = pipeline(crm, "L1", 60000)
        crm.discount(oid, 20, "m1")  # 48000 -> no manager needed now
        crm.advance(oid, "proposal", "r1")
        crm.advance(oid, "negotiation", "r1")
        self.assertEqual(crm.opps[oid]["stage"], "negotiation")

    def test_exactly_50000_does_not_need_manager(self):
        crm = make_crm([{"id": "r1", "role": "rep", "capacity": 10},
                        {"id": "m1", "role": "manager", "capacity": 0}])
        crm.add_lead("a@corp.com", "A", "referral", "r1")
        oid = pipeline(crm, "L1", 50000)
        crm.advance(oid, "proposal", "r1")
        crm.advance(oid, "negotiation", "r1")
        self.assertEqual(crm.opps[oid]["stage"], "negotiation")


class QueueTests(unittest.TestCase):
    def test_final_stage_assigns_fifo_waiting_leads(self):
        crm = make_crm([{"id": "r1", "role": "rep", "capacity": 2},
                        {"id": "m1", "role": "manager", "capacity": 0}])
        for i in range(4):
            crm.add_lead("l%d@corp.com" % i, "N%d" % i, "referral", "m1")
        self.assertEqual(crm.leads["L1"]["owner"], "r1")
        self.assertEqual(crm.leads["L2"]["owner"], "r1")
        self.assertIsNone(crm.leads["L3"]["owner"])
        self.assertIsNone(crm.leads["L4"]["owner"])

        o1 = pipeline(crm, "L1", 1000)
        crm.advance(o1, "lost", "m1")
        # L1 leaves the load: converted lead is not counted, final opp is not
        self.assertEqual(crm.leads["L3"]["owner"], "r1")
        self.assertIsNone(crm.leads["L4"]["owner"])
        self.assertEqual(crm.leads["L3"]["status"], "new")
        self.assertIn(("assign", "L3", "system"), crm.log)

        o2 = pipeline(crm, "L2", 1000)
        crm.advance(o2, "proposal", "m1")
        crm.advance(o2, "negotiation", "m1")
        crm.advance(o2, "won", "m1")
        self.assertEqual(crm.leads["L4"]["owner"], "r1")
        self.assertEqual(
            [entry for entry in crm.log if entry[0] == "assign"],
            [("assign", "L3", "system"), ("assign", "L4", "system")],
        )

    def test_assignment_stops_at_capacity(self):
        crm = make_crm([{"id": "r1", "role": "rep", "capacity": 1},
                        {"id": "m1", "role": "manager", "capacity": 0}])
        for i in range(3):
            crm.add_lead("l%d@corp.com" % i, "N", "referral", "m1")
        o1 = pipeline(crm, "L1", 1000)
        crm.advance(o1, "lost", "m1")
        self.assertEqual(crm.leads["L2"]["owner"], "r1")
        self.assertIsNone(crm.leads["L3"]["owner"])


class DiscountTests(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm([{"id": "r1", "role": "rep", "capacity": 10},
                             {"id": "r2", "role": "rep", "capacity": 10},
                             {"id": "m1", "role": "manager", "capacity": 0}])
        self.crm.add_lead("a@corp.com", "A", "referral", "r1")
        self.oid = pipeline(self.crm, "L1", 1000)

    def test_rep_discount_up_to_ten(self):
        self.crm.discount("O1", 10, "r1")
        self.assertEqual(self.crm.opps["O1"]["amount"], 900)
        self.assertEqual(self.crm.opps["O1"]["original_amount"], 1000)
        self.assertEqual(self.crm.log[-1], ("discount", "O1", "r1"))

    def test_pct_validation(self):
        for bad in [0, 31, -5, 10.0, True, "10", None]:
            with self.subTest(pct=bad):
                with self.assertRaises(ValueError):
                    self.crm.discount("O1", bad, "m1")
        self.assertEqual(self.crm.opps["O1"]["amount"], 1000)

    def test_rep_cap_and_manager_override(self):
        with self.assertRaises(PermissionError):
            self.crm.discount("O1", 11, "r1")
        self.crm.discount("O1", 11, "m1")
        self.assertEqual(self.crm.opps["O1"]["amount"], 890)

    def test_permission_before_rep_cap(self):
        with self.assertRaises(PermissionError):
            self.crm.discount("O1", 15, "r2")

    def test_cumulative_limit(self):
        self.crm.discount("O1", 30, "m1")
        self.assertEqual(self.crm.opps["O1"]["amount"], 700)
        with self.assertRaises(ValueError):
            self.crm.discount("O1", 1, "m1")
        self.assertEqual(self.crm.opps["O1"]["amount"], 700)

    def test_cumulative_limit_with_multiple_reps(self):
        self.crm.discount("O1", 10, "r1")
        self.crm.discount("O1", 10, "r1")
        self.crm.discount("O1", 10, "r1")
        self.assertEqual(self.crm.opps["O1"]["amount"], 729)
        with self.assertRaises(ValueError):
            self.crm.discount("O1", 4, "r1")  # would drop below 70% of original

    def test_final_stage_cannot_be_discounted(self):
        self.crm.advance("O1", "lost", "r1")
        with self.assertRaises(ValueError):
            self.crm.discount("O1", 5, "m1")
        self.assertEqual(self.crm.opps["O1"]["amount"], 1000)


class TransferTests(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm([{"id": "r1", "role": "rep", "capacity": 3},
                             {"id": "r2", "role": "rep", "capacity": 3},
                             {"id": "m1", "role": "manager", "capacity": 0}])
        for i in range(3):
            self.crm.add_lead("l%d@corp.com" % i, "N", "referral", "m1")
        self.oid = pipeline(self.crm, "L1", 1000)

    def test_transfer_success(self):
        self.crm.transfer("O1", "r2", "m1")
        self.assertEqual(self.crm.opps["O1"]["owner"], "r2")
        self.assertEqual(self.crm.log[-1], ("transfer", "O1", "m1"))

    def test_only_managers(self):
        with self.assertRaises(PermissionError):
            self.crm.transfer("O1", "r2", "r1")
        self.assertEqual(self.crm.opps["O1"]["owner"], "r1")

    def test_new_owner_must_be_rep(self):
        with self.assertRaises(ValueError):
            self.crm.transfer("O1", "m1", "m1")
        with self.assertRaises(ValueError):
            self.crm.transfer("O1", "nobody", "m1")

    def test_new_owner_must_differ(self):
        with self.assertRaises(ValueError):
            self.crm.transfer("O1", "r1", "m1")

    def test_final_stage_cannot_transfer(self):
        self.crm.advance("O1", "lost", "m1")
        with self.assertRaises(ValueError):
            self.crm.transfer("O1", "r2", "m1")

    def test_new_owner_must_have_capacity(self):
        small = make_crm([{"id": "r1", "role": "rep", "capacity": 5},
                          {"id": "r2", "role": "rep", "capacity": 1},
                          {"id": "m1", "role": "manager", "capacity": 0}])
        small.add_lead("a@corp.com", "A", "referral", "m1")  # r1
        small.add_lead("b@corp.com", "B", "referral", "m1")  # r2 (full)
        oid = pipeline(small, "L1", 100)
        with self.assertRaises(ValueError):
            small.transfer(oid, "r2", "m1")
        self.assertEqual(small.opps[oid]["owner"], "r1")

    def test_transfer_frees_previous_owner_slot(self):
        # A transfer moves one unit of load from the old owner to the new one.
        crm = make_crm([{"id": "r1", "role": "rep", "capacity": 2},
                        {"id": "r2", "role": "rep", "capacity": 3},
                        {"id": "m1", "role": "manager", "capacity": 0}])
        for i in range(3):
            crm.add_lead("l%d@corp.com" % i, "N", "referral", "m1")
        oid = pipeline(crm, "L1", 100)
        # r1 now holds one lead and the open opportunity (load 2 = capacity)
        crm.transfer(oid, "r2", "m1")
        # r1 dropped to load 1, so a new lead can be assigned to it
        crm.add_lead("new@corp.com", "New", "referral", "m1")
        self.assertEqual(crm.leads["L4"]["owner"], "r1")


class ForecastTests(unittest.TestCase):
    def test_forecast(self):
        crm = make_crm([{"id": "r1", "role": "rep", "capacity": 10},
                        {"id": "m1", "role": "manager", "capacity": 0}])
        crm.add_lead("a@corp.com", "A", "referral", "m1")
        crm.add_lead("b@corp.com", "B", "referral", "m1")
        crm.add_lead("c@corp.com", "C", "referral", "m1")
        o1 = pipeline(crm, "L1", 1000)
        o2 = pipeline(crm, "L2", 2000)
        o3 = pipeline(crm, "L3", 3000)
        crm.advance(o2, "proposal", "m1")
        crm.advance(o3, "proposal", "m1")
        crm.advance(o3, "negotiation", "m1")
        crm.advance(o3, "won", "m1")
        log_before = list(crm.log)
        result = crm.forecast()
        self.assertEqual(result, {"open": 2, "weighted": 100 + 600, "won": 3000})
        self.assertEqual(crm.log, log_before)

    def test_empty_forecast(self):
        self.assertEqual(
            make_crm().forecast(), {"open": 0, "weighted": 0, "won": 0}
        )

    def test_forecast_uses_discounted_amount(self):
        crm = make_crm([{"id": "r1", "role": "rep", "capacity": 10},
                        {"id": "m1", "role": "manager", "capacity": 0}])
        crm.add_lead("a@corp.com", "A", "referral", "m1")
        oid = pipeline(crm, "L1", 1000)
        crm.advance(oid, "proposal", "m1")
        crm.discount(oid, 10, "m1")
        self.assertEqual(crm.forecast()["weighted"], 900 * 30 // 100)


class PermissionAndAtomicityTests(unittest.TestCase):
    def test_unknown_actor_is_rejected_first(self):
        crm = make_crm()
        calls = [
            lambda: crm.add_lead("nonsense", "", "bogus", "ghost"),
            lambda: crm.qualify("L404", "ghost"),
            lambda: crm.convert("L404", -5, "ghost"),
            lambda: crm.advance("O404", "bogus", "ghost"),
            lambda: crm.discount("O404", 99, "ghost"),
            lambda: crm.transfer("O404", "ghost", "ghost"),
        ]
        for call in calls:
            with self.subTest(call=call):
                with self.assertRaises(PermissionError):
                    call()
        self.assertEqual(crm.leads, {})
        self.assertEqual(crm.opps, {})
        self.assertEqual(crm.log, [])

    def test_known_stranger_sees_existence_errors_first(self):
        crm = make_crm()
        with self.assertRaises(ValueError):
            crm.qualify("L404", "r2")
        with self.assertRaises(ValueError):
            crm.advance("O404", "proposal", "r2")
        with self.assertRaises(ValueError):
            crm.discount("O404", 5, "r2")
        with self.assertRaises(ValueError):
            crm.transfer("O404", "r1", "r2")

    def test_failed_calls_change_nothing(self):
        crm = make_crm()
        crm.add_lead("a@corp.com", "A", "referral", "r1")
        crm.add_lead("b@corp.com", "B", "referral", "r2")
        oid = pipeline(crm, "L1", 1000)
        snapshot = (
            copy.deepcopy(crm.leads),
            copy.deepcopy(crm.opps),
            list(crm.log),
        )
        attempts = [
            lambda: crm.add_lead("a@corp.com", "Dup", "web", "m1"),
            lambda: crm.add_lead("bad", "X", "web", "m1"),
            lambda: crm.qualify("L1", "m1"),  # already converted
            lambda: crm.convert("L1", 100, "m1"),  # already converted
            lambda: crm.advance(oid, "won", "m1"),  # skips a stage
            lambda: crm.discount(oid, 0, "m1"),
            lambda: crm.transfer(oid, "r1", "m1"),  # same owner
            lambda: crm.transfer(oid, "m1", "m1"),  # not a rep
        ]
        for attempt in attempts:
            with self.assertRaises(Exception):
                attempt()
            self.assertEqual(
                (crm.leads, crm.opps, crm.log),
                snapshot,
            )


if __name__ == "__main__":
    unittest.main()
