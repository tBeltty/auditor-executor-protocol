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


def qualified_lead(crm, email="lead@corp.com", name="Lead", source="referral", actor="r1"):
    lead_id = crm.add_lead(email, name, source, actor)
    crm.qualify(lead_id, actor)
    return lead_id


class AddLeadTests(unittest.TestCase):
    def test_basic_web_lead(self):
        crm = make_crm()
        lead_id = crm.add_lead("  Alice@Gmail.COM ", " Alice ", "web", "m1")
        self.assertEqual(lead_id, "L1")
        lead = crm.leads["L1"]
        self.assertEqual(lead["email"], "alice@gmail.com")
        self.assertEqual(lead["name"], "Alice")
        self.assertEqual(lead["source"], "web")
        self.assertEqual(lead["score"], 10)
        self.assertEqual(lead["owner"], "r1")
        self.assertEqual(lead["status"], "new")
        self.assertEqual(crm.log, [("add_lead", "L1", "m1")])

    def test_referral_custom_domain_score(self):
        crm = make_crm()
        crm.add_lead("bob@corp.io", "Bob", "referral", "r1")
        self.assertEqual(crm.leads["L1"]["score"], 45)

    def test_event_free_domain_score(self):
        crm = make_crm()
        crm.add_lead("bob@outlook.com", "Bob", "event", "r1")
        self.assertEqual(crm.leads["L1"]["score"], 20)

    def test_subdomain_is_not_free(self):
        crm = make_crm()
        crm.add_lead("bob@mail.gmail.com", "Bob", "web", "r1")
        self.assertEqual(crm.leads["L1"]["score"], 25)

    def test_email_validation(self):
        crm = make_crm()
        bad = [
            123,
            None,
            "no-at-sign.com",
            "a@@b.com",
            "@b.com",
            "a@b",
            "a@.com",
            "a@com.",
            "a@b@c.com",
        ]
        for email in bad:
            with self.assertRaises(ValueError, msg=repr(email)):
                crm.add_lead(email, "Name", "web", "r1")
        self.assertEqual(crm.leads, {})
        self.assertEqual(crm.log, [])

    def test_valid_email_shapes(self):
        crm = make_crm()
        for i, email in enumerate(["a@b.c", "x@y.co.uk", "a@b..c"]):
            crm.add_lead(email, "N", "web", "r1")
            self.assertIn("L%d" % (i + 1), crm.leads)

    def test_name_validation(self):
        crm = make_crm()
        for name in [None, 5, "", "   "]:
            with self.assertRaises(ValueError):
                crm.add_lead("a@b.com", name, "web", "r1")

    def test_source_validation(self):
        crm = make_crm()
        for source in ["WEB", "email", None, 1]:
            with self.assertRaises(ValueError):
                crm.add_lead("a@b.com", "N", source, "r1")

    def test_duplicate_email(self):
        crm = make_crm()
        crm.add_lead("a@b.com", "A", "web", "r1")
        before_log = list(crm.log)
        with self.assertRaises(DuplicateLeadError) as ctx:
            crm.add_lead(" A@B.COM ", "Other", "event", "m1")
        self.assertEqual(ctx.exception.existing_id, "L1")
        self.assertEqual(crm.log, before_log)
        self.assertEqual(len(crm.leads), 1)
        self.assertEqual(crm.add_lead("c@d.com", "C", "web", "r1"), "L2")

    def test_unknown_actor_checked_first(self):
        crm = make_crm()
        crm.add_lead("a@corp.com", "A", "referral", "r1")
        crm.qualify("L1", "r1")
        crm.convert("L1", 100, "r1")
        for call in [
            lambda: crm.add_lead(None, None, None, "ghost"),
            lambda: crm.qualify("nope", "ghost"),
            lambda: crm.convert("nope", -1, "ghost"),
            lambda: crm.advance("nope", "won", "ghost"),
            lambda: crm.discount("nope", 99, "ghost"),
            lambda: crm.transfer("nope", "r1", "ghost"),
        ]:
            with self.assertRaises(PermissionError):
                call()

    def test_owner_selection_ties_and_waiting_queue(self):
        crm = make_crm()
        crm.add_lead("a@corp.com", "A", "web", "m1")
        crm.add_lead("b@corp.com", "B", "web", "m1")
        crm.add_lead("c@corp.com", "C", "web", "m1")
        crm.add_lead("d@corp.com", "D", "web", "m1")
        self.assertEqual(crm.leads["L1"]["owner"], "r1")
        self.assertEqual(crm.leads["L2"]["owner"], "r2")
        self.assertEqual(crm.leads["L3"]["owner"], "r1")
        self.assertIsNone(crm.leads["L4"]["owner"])
        self.assertEqual(crm.waiting, ["L4"])

    def test_managers_never_own(self):
        crm = make_crm([
            {"id": "m1", "role": "manager", "capacity": 5},
            {"id": "r1", "role": "rep", "capacity": 1},
        ])
        crm.add_lead("a@corp.com", "A", "web", "m1")
        crm.add_lead("b@corp.com", "B", "web", "m1")
        self.assertEqual(crm.leads["L1"]["owner"], "r1")
        self.assertIsNone(crm.leads["L2"]["owner"])


class QualifyTests(unittest.TestCase):
    def test_qualify_success_and_log(self):
        crm = make_crm()
        crm.add_lead("a@corp.com", "A", "referral", "r1")
        crm.qualify("L1", "r1")
        self.assertEqual(crm.leads["L1"]["status"], "qualified")
        self.assertEqual(crm.log[-1], ("qualify", "L1", "r1"))

    def test_qualify_by_manager(self):
        crm = make_crm()
        crm.add_lead("a@corp.com", "A", "referral", "r1")
        crm.qualify("L1", "m1")
        self.assertEqual(crm.leads["L1"]["status"], "qualified")

    def test_qualify_unknown_lead(self):
        crm = make_crm()
        with self.assertRaises(ValueError):
            crm.qualify("L99", "r1")

    def test_qualify_permission(self):
        crm = make_crm()
        crm.add_lead("a@corp.com", "A", "referral", "r1")
        with self.assertRaises(PermissionError):
            crm.qualify("L1", "r2")

    def test_qualify_status_and_score(self):
        crm = make_crm()
        crm.add_lead("a@corp.com", "A", "web", "r1")
        with self.assertRaises(ValueError):
            crm.qualify("L1", "r1")  # score 10
        crm2 = make_crm()
        crm2.add_lead("a@corp.com", "A", "referral", "r1")
        crm2.qualify("L1", "r1")
        with self.assertRaises(ValueError):
            crm2.qualify("L1", "r1")  # not new

    def test_qualify_check_order(self):
        crm = make_crm()
        crm.add_lead("a@corp.com", "A", "web", "r1")
        # permission is checked before score
        with self.assertRaises(PermissionError):
            crm.qualify("L1", "r2")
        # status is checked before score only after permission; owner fails on score
        with self.assertRaises(ValueError):
            crm.qualify("L1", "r1")
        self.assertEqual(crm.log, [("add_lead", "L1", "r1")])


class ConvertTests(unittest.TestCase):
    def test_convert_success(self):
        crm = make_crm()
        qualified_lead(crm)
        opp_id = crm.convert("L1", 1000, "r1")
        self.assertEqual(opp_id, "O1")
        self.assertEqual(crm.leads["L1"]["status"], "converted")
        opp = crm.opps["O1"]
        self.assertEqual(opp["lead_id"], "L1")
        self.assertEqual(opp["owner"], "r1")
        self.assertEqual(opp["amount"], 1000)
        self.assertEqual(opp["original_amount"], 1000)
        self.assertEqual(opp["stage"], "prospect")
        self.assertEqual(crm.log[-1], ("convert", "O1", "r1"))

    def test_convert_ids_increment(self):
        crm = make_crm([
            {"id": "r1", "role": "rep", "capacity": 5},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        qualified_lead(crm, "a@corp.com")
        qualified_lead(crm, "b@corp.com")
        self.assertEqual(crm.convert("L1", 10, "r1"), "O1")
        self.assertEqual(crm.convert("L2", 10, "r1"), "O2")

    def test_convert_amount_validation(self):
        crm = make_crm()
        qualified_lead(crm)
        for amount in [0, -5, True, False, 1.5, "100", None]:
            with self.assertRaises(ValueError):
                crm.convert("L1", amount, "r1")
        self.assertEqual(crm.opps, {})

    def test_convert_unknown_lead_and_permission(self):
        crm = make_crm()
        with self.assertRaises(ValueError):
            crm.convert("L99", 10, "r1")
        qualified_lead(crm)
        with self.assertRaises(PermissionError):
            crm.convert("L1", 10, "r2")

    def test_convert_requires_qualified(self):
        crm = make_crm()
        crm.add_lead("a@corp.com", "A", "referral", "r1")
        with self.assertRaises(ValueError):
            crm.convert("L1", 10, "r1")

    def test_convert_requires_owner(self):
        crm = make_crm()
        crm.add_lead("a@corp.com", "A", "referral", "r1")
        crm.add_lead("b@corp.com", "B", "referral", "r1")
        crm.add_lead("c@corp.com", "C", "referral", "r1")
        crm.add_lead("d@corp.com", "D", "referral", "r1")
        self.assertIsNone(crm.leads["L4"]["owner"])
        crm.qualify("L4", "m1")
        before_log = list(crm.log)
        with self.assertRaises(ValueError):
            crm.convert("L4", 10, "m1")
        self.assertEqual(crm.log, before_log)
        self.assertEqual(crm.opps, {})


class AdvanceTests(unittest.TestCase):
    def _crm_with_opp(self, amount=1000):
        crm = make_crm()
        qualified_lead(crm)
        opp_id = crm.convert("L1", amount, "r1")
        return crm, opp_id

    def test_advance_forward_chain(self):
        crm, opp_id = self._crm_with_opp()
        for stage in ["proposal", "negotiation", "won"]:
            crm.advance(opp_id, stage, "r1")
            self.assertEqual(crm.opps[opp_id]["stage"], stage)
        self.assertEqual(crm.log[-1], ("advance", opp_id, "r1"))

    def test_advance_lost_from_any_non_final(self):
        crm, opp_id = self._crm_with_opp()
        crm.advance(opp_id, "lost", "r1")
        self.assertEqual(crm.opps[opp_id]["stage"], "lost")

    def test_advance_unknown_and_bad_stage(self):
        crm, opp_id = self._crm_with_opp()
        with self.assertRaises(ValueError):
            crm.advance("O99", "proposal", "r1")
        with self.assertRaises(ValueError):
            crm.advance(opp_id, "closed", "r1")

    def test_advance_permission(self):
        crm, opp_id = self._crm_with_opp()
        with self.assertRaises(PermissionError):
            crm.advance(opp_id, "proposal", "r2")
        crm.advance(opp_id, "proposal", "m1")
        self.assertEqual(crm.opps[opp_id]["stage"], "proposal")

    def test_advance_skipping_stages(self):
        crm, opp_id = self._crm_with_opp()
        with self.assertRaises(ValueError):
            crm.advance(opp_id, "won", "r1")
        with self.assertRaises(ValueError):
            crm.advance(opp_id, "negotiation", "r1")

    def test_advance_final_is_final(self):
        crm, opp_id = self._crm_with_opp()
        crm.advance(opp_id, "lost", "r1")
        with self.assertRaises(ValueError):
            crm.advance(opp_id, "proposal", "r1")

    def test_negotiation_needs_manager_over_50000(self):
        crm, opp_id = self._crm_with_opp(60000)
        crm.advance(opp_id, "proposal", "r1")
        with self.assertRaises(PermissionError):
            crm.advance(opp_id, "negotiation", "r1")
        self.assertEqual(crm.opps[opp_id]["stage"], "proposal")
        crm.advance(opp_id, "negotiation", "m1")
        self.assertEqual(crm.opps[opp_id]["stage"], "negotiation")

    def test_negotiation_boundary_50000_rep_allowed(self):
        crm, opp_id = self._crm_with_opp(50000)
        crm.advance(opp_id, "proposal", "r1")
        crm.advance(opp_id, "negotiation", "r1")
        self.assertEqual(crm.opps[opp_id]["stage"], "negotiation")

    def test_final_stage_assigns_waiting_leads(self):
        crm = make_crm([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        qualified_lead(crm, "a@corp.com")   # L1 -> r1
        crm.add_lead("b@corp.com", "B", "web", "m1")  # L2 -> r2
        crm.add_lead("c@corp.com", "C", "web", "m1")  # L3 waiting
        self.assertEqual(crm.waiting, ["L3"])
        opp_id = crm.convert("L1", 1000, "r1")
        crm.advance(opp_id, "proposal", "r1")
        crm.advance(opp_id, "negotiation", "r1")
        crm.advance(opp_id, "won", "r1")
        self.assertEqual(crm.leads["L3"]["owner"], "r1")
        self.assertEqual(crm.waiting, [])
        self.assertEqual(crm.log[-1], ("assign", "L3", "system"))

    def test_lost_stage_assigns_waiting_leads(self):
        crm = make_crm([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        qualified_lead(crm, "a@corp.com")
        crm.add_lead("b@corp.com", "B", "web", "m1")
        crm.add_lead("c@corp.com", "C", "web", "m1")
        opp_id = crm.convert("L1", 1000, "r1")
        crm.advance(opp_id, "lost", "r1")
        self.assertEqual(crm.leads["L3"]["owner"], "r1")


class DiscountTests(unittest.TestCase):
    def _crm_with_opp(self, amount=1000):
        crm = make_crm([
            {"id": "r1", "role": "rep", "capacity": 5},
            {"id": "r2", "role": "rep", "capacity": 5},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        qualified_lead(crm)
        opp_id = crm.convert("L1", amount, "r1")
        return crm, opp_id

    def test_discount_basic(self):
        crm, opp_id = self._crm_with_opp()
        crm.discount(opp_id, 10, "r1")
        self.assertEqual(crm.opps[opp_id]["amount"], 900)
        self.assertEqual(crm.opps[opp_id]["original_amount"], 1000)
        self.assertEqual(crm.log[-1], ("discount", opp_id, "r1"))

    def test_discount_pct_validation(self):
        crm, opp_id = self._crm_with_opp()
        for pct in [0, 31, -1, True, 5.0, "5", None]:
            with self.assertRaises(ValueError):
                crm.discount(opp_id, pct, "r1")
        self.assertEqual(crm.opps[opp_id]["amount"], 1000)

    def test_discount_non_manager_cap(self):
        crm, opp_id = self._crm_with_opp()
        with self.assertRaises(PermissionError):
            crm.discount(opp_id, 11, "r1")
        crm.discount(opp_id, 10, "r1")
        self.assertEqual(crm.opps[opp_id]["amount"], 900)

    def test_discount_permission_and_final(self):
        crm, opp_id = self._crm_with_opp()
        with self.assertRaises(PermissionError):
            crm.discount(opp_id, 5, "r2")
        crm.advance(opp_id, "lost", "r1")
        with self.assertRaises(ValueError):
            crm.discount(opp_id, 5, "m1")

    def test_discount_cumulative_limit(self):
        crm, opp_id = self._crm_with_opp()
        crm.discount(opp_id, 30, "m1")
        self.assertEqual(crm.opps[opp_id]["amount"], 700)
        before = crm.opps[opp_id]["amount"]
        with self.assertRaises(ValueError):
            crm.discount(opp_id, 1, "m1")
        self.assertEqual(crm.opps[opp_id]["amount"], before)

    def test_discount_rounding_floor(self):
        crm, opp_id = self._crm_with_opp(101)
        crm.discount(opp_id, 10, "r1")
        self.assertEqual(crm.opps[opp_id]["amount"], 90)


class TransferTests(unittest.TestCase):
    def _crm_with_opp(self, amount=1000):
        crm = make_crm([
            {"id": "r1", "role": "rep", "capacity": 2},
            {"id": "r2", "role": "rep", "capacity": 2},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        qualified_lead(crm)
        opp_id = crm.convert("L1", amount, "r1")
        return crm, opp_id

    def test_transfer_success(self):
        crm, opp_id = self._crm_with_opp()
        crm.transfer(opp_id, "r2", "m1")
        self.assertEqual(crm.opps[opp_id]["owner"], "r2")
        self.assertEqual(crm.log[-1], ("transfer", opp_id, "m1"))

    def test_transfer_unknown_and_permission(self):
        crm, opp_id = self._crm_with_opp()
        with self.assertRaises(ValueError):
            crm.transfer("O99", "r2", "m1")
        with self.assertRaises(PermissionError):
            crm.transfer(opp_id, "r2", "r1")

    def test_transfer_target_validation(self):
        crm, opp_id = self._crm_with_opp()
        with self.assertRaises(ValueError):
            crm.transfer(opp_id, "m1", "m1")   # manager is not a rep
        with self.assertRaises(ValueError):
            crm.transfer(opp_id, "nobody", "m1")
        with self.assertRaises(ValueError):
            crm.transfer(opp_id, "r1", "m1")   # same owner

    def test_transfer_final_stage(self):
        crm, opp_id = self._crm_with_opp()
        crm.transfer(opp_id, "r2", "m1")
        crm.advance(opp_id, "proposal", "m1")
        crm.advance(opp_id, "negotiation", "m1")
        crm.advance(opp_id, "won", "m1")
        with self.assertRaises(ValueError):
            crm.transfer(opp_id, "r1", "m1")

    def test_transfer_capacity(self):
        crm = make_crm([
            {"id": "r1", "role": "rep", "capacity": 5},
            {"id": "r2", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        qualified_lead(crm)                 # L1 -> r1
        crm.add_lead("b@corp.com", "B", "web", "m1")  # L2 -> r2 (full)
        opp_id = crm.convert("L1", 1000, "r1")
        with self.assertRaises(ValueError):
            crm.transfer(opp_id, "r2", "m1")
        self.assertEqual(crm.opps[opp_id]["owner"], "r1")


class ForecastTests(unittest.TestCase):
    def test_forecast(self):
        crm = make_crm([
            {"id": "r1", "role": "rep", "capacity": 10},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        qualified_lead(crm, "a@corp.com")
        o1 = crm.convert("L1", 10000, "r1")
        qualified_lead(crm, "b@corp.com")
        o2 = crm.convert("L2", 20000, "r1")
        qualified_lead(crm, "c@corp.com")
        o3 = crm.convert("L3", 5000, "r1")

        self.assertEqual(crm.forecast(), {"open": 3, "weighted": 3500, "won": 0})

        crm.advance(o1, "proposal", "r1")
        self.assertEqual(crm.forecast(), {"open": 3, "weighted": 3000 + 2000 + 500, "won": 0})
        crm.advance(o1, "negotiation", "r1")
        self.assertEqual(crm.forecast(), {"open": 3, "weighted": 6000 + 2000 + 500, "won": 0})

        crm.advance(o2, "proposal", "r1")
        crm.advance(o2, "negotiation", "r1")
        crm.advance(o2, "won", "r1")
        self.assertEqual(crm.forecast(), {"open": 2, "weighted": 6000 + 500, "won": 20000})

        crm.advance(o3, "lost", "r1")
        self.assertEqual(crm.forecast(), {"open": 1, "weighted": 6000, "won": 20000})

    def test_forecast_empty(self):
        self.assertEqual(make_crm().forecast(), {"open": 0, "weighted": 0, "won": 0})


class AtomicityTests(unittest.TestCase):
    def test_failed_calls_change_nothing(self):
        crm = make_crm()
        qualified_lead(crm)
        crm.convert("L1", 1000, "r1")
        crm.add_lead("b@corp.com", "B", "web", "m1")
        leads_before = copy.deepcopy(crm.leads)
        opps_before = copy.deepcopy(crm.opps)
        log_before = list(crm.log)
        waiting_before = list(crm.waiting)

        for call in [
            lambda: crm.add_lead("lead@corp.com", "A", "web", "m1"),   # duplicate
            lambda: crm.qualify("L99", "r1"),
            lambda: crm.convert("L2", 100, "r1"),                   # not qualified
            lambda: crm.advance("O1", "won", "r1"),                 # skips stages
            lambda: crm.discount("O1", 31, "m1"),                   # bad pct
            lambda: crm.transfer("O1", "r1", "m1"),                 # same owner
        ]:
            with self.assertRaises((ValueError, PermissionError, DuplicateLeadError)):
                call()
            self.assertEqual(crm.leads, leads_before)
            self.assertEqual(crm.opps, opps_before)
            self.assertEqual(crm.log, log_before)
            self.assertEqual(crm.waiting, waiting_before)


if __name__ == "__main__":
    unittest.main()
