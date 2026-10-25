import unittest

from crm import CRM


def make_crm():
    return CRM(
        [
            {"id": "r1", "role": "rep", "capacity": 3},
            {"id": "r2", "role": "rep", "capacity": 2},
            {"id": "m1", "role": "manager", "capacity": 5},
        ]
    )


def new_lead(crm, email="lead@corp.com", source="referral", actor="r1"):
    return crm.add_lead(email, "Lead", source, actor)


def new_qualified_lead(crm, email="lead@corp.com", actor="r1"):
    lead_id = new_lead(crm, email=email, actor=actor)
    crm.qualify(lead_id, actor)
    return lead_id


class QualifyTests(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()

    def test_unknown_lead(self):
        with self.assertRaises(ValueError):
            self.crm.qualify("L99", "r1")

    def test_unknown_actor_wins_over_missing_lead(self):
        with self.assertRaises(PermissionError):
            self.crm.qualify("L99", "ghost")

    def test_non_owner_rep_forbidden(self):
        lead_id = new_lead(self.crm)
        with self.assertRaises(PermissionError):
            self.crm.qualify(lead_id, "r2")
        self.assertEqual(self.crm.leads[lead_id]["status"], "new")
        self.assertEqual(len(self.crm.log), 1)

    def test_permission_checked_before_score(self):
        lead_id = new_lead(self.crm, source="web")  # score 25
        with self.assertRaises(PermissionError):
            self.crm.qualify(lead_id, "r2")

    def test_manager_may_qualify_any_lead(self):
        lead_id = new_lead(self.crm)
        self.crm.qualify(lead_id, "m1")
        self.assertEqual(self.crm.leads[lead_id]["status"], "qualified")

    def test_status_must_be_new(self):
        lead_id = new_qualified_lead(self.crm)
        with self.assertRaises(ValueError):
            self.crm.qualify(lead_id, "r1")

    def test_score_threshold(self):
        low = new_lead(self.crm, email="low@corp.com", source="web")  # 25
        with self.assertRaises(ValueError):
            self.crm.qualify(low, "r1")
        self.assertEqual(self.crm.leads[low]["status"], "new")

    def test_score_exactly_thirty_is_enough(self):
        lead_id = new_lead(self.crm, email="ok@gmail.com", source="referral")
        self.crm.qualify(lead_id, "r1")
        self.assertEqual(self.crm.leads[lead_id]["status"], "qualified")

    def test_log_entry(self):
        lead_id = new_lead(self.crm)
        self.crm.qualify(lead_id, "r1")
        self.assertEqual(self.crm.log[-1], ("qualify", lead_id, "r1"))


class ConvertTests(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()

    def test_unknown_lead(self):
        with self.assertRaises(ValueError):
            self.crm.convert("L99", 100, "r1")

    def test_amount_validation(self):
        lead_id = new_qualified_lead(self.crm)
        for bad in (0, -1, True, False, 1.5, "100", None):
            with self.assertRaises(ValueError, msg=repr(bad)):
                self.crm.convert(lead_id, bad, "r1")
        self.assertEqual(self.crm.opps, {})
        self.assertEqual(self.crm.leads[lead_id]["status"], "qualified")

    def test_amount_checked_before_permission(self):
        lead_id = new_lead(self.crm)
        with self.assertRaises(ValueError):
            self.crm.convert(lead_id, 0, "r2")

    def test_non_owner_rep_forbidden(self):
        lead_id = new_qualified_lead(self.crm)
        with self.assertRaises(PermissionError):
            self.crm.convert(lead_id, 100, "r2")
        self.assertEqual(self.crm.opps, {})

    def test_permission_checked_before_status(self):
        lead_id = new_lead(self.crm)  # status new
        with self.assertRaises(PermissionError):
            self.crm.convert(lead_id, 100, "r2")

    def test_lead_must_be_qualified(self):
        lead_id = new_lead(self.crm)
        with self.assertRaises(ValueError):
            self.crm.convert(lead_id, 100, "r1")

    def test_lead_without_owner_cannot_convert(self):
        crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 1},
                {"id": "m1", "role": "manager", "capacity": 5},
            ]
        )
        blocker = new_lead(crm, email="blocker@corp.com")
        self.assertEqual(crm.leads[blocker]["owner"], "r1")
        lead_id = crm.add_lead("waiting@corp.com", "W", "referral", "m1")
        self.assertIsNone(crm.leads[lead_id]["owner"])
        crm.qualify(lead_id, "m1")
        with self.assertRaises(ValueError):
            crm.convert(lead_id, 100, "m1")
        self.assertEqual(crm.leads[lead_id]["status"], "qualified")
        self.assertEqual(crm.opps, {})

    def test_success(self):
        lead_id = new_qualified_lead(self.crm)
        opp_id = self.crm.convert(lead_id, 1234, "r1")
        self.assertEqual(opp_id, "O1")
        self.assertEqual(
            self.crm.opps[opp_id],
            {
                "id": "O1",
                "lead_id": lead_id,
                "owner": "r1",
                "amount": 1234,
                "original_amount": 1234,
                "stage": "prospect",
            },
        )
        self.assertEqual(self.crm.leads[lead_id]["status"], "converted")
        self.assertEqual(self.crm.log[-1], ("convert", opp_id, "r1"))

    def test_ids_count_only_successful_conversions(self):
        lead_a = new_qualified_lead(self.crm, email="a@corp.com")
        lead_b = new_qualified_lead(self.crm, email="b@corp.com", actor="m1")
        with self.assertRaises(ValueError):
            self.crm.convert(lead_a, 0, "r1")
        first = self.crm.convert(lead_a, 100, "r1")
        second = self.crm.convert(lead_b, 200, "m1")
        self.assertEqual((first, second), ("O1", "O2"))

    def test_manager_may_convert(self):
        lead_id = new_qualified_lead(self.crm)
        opp_id = self.crm.convert(lead_id, 500, "m1")
        self.assertEqual(self.crm.opps[opp_id]["owner"], "r1")


class AdvanceTests(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        self.lead_id = new_qualified_lead(self.crm)
        self.opp_id = self.crm.convert(self.lead_id, 1000, "r1")

    def test_unknown_opp(self):
        with self.assertRaises(ValueError):
            self.crm.advance("O99", "proposal", "r1")

    def test_invalid_stage(self):
        for bad in ("won ", "Proposal", "", None, 1):
            with self.assertRaises(ValueError, msg=repr(bad)):
                self.crm.advance(self.opp_id, bad, "r1")

    def test_non_owner_rep_forbidden(self):
        with self.assertRaises(PermissionError):
            self.crm.advance(self.opp_id, "proposal", "r2")
        self.assertEqual(self.crm.opps[self.opp_id]["stage"], "prospect")

    def test_invalid_stage_checked_before_permission(self):
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp_id, "bogus", "r2")

    def test_cannot_skip_stage(self):
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp_id, "negotiation", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp_id, "won", "r1")

    def test_lost_from_any_open_stage(self):
        self.crm.advance(self.opp_id, "proposal", "r1")
        self.crm.advance(self.opp_id, "lost", "r1")
        self.assertEqual(self.crm.opps[self.opp_id]["stage"], "lost")
        self.assertEqual(self.crm.log[-1], ("advance", self.opp_id, "r1"))

    def test_final_stage_is_terminal(self):
        self.crm.advance(self.opp_id, "lost", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp_id, "lost", "m1")
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp_id, "proposal", "m1")

    def test_full_happy_path(self):
        for stage in ("proposal", "negotiation", "won"):
            self.crm.advance(self.opp_id, stage, "r1")
            self.assertEqual(self.crm.opps[self.opp_id]["stage"], stage)

    def test_manager_may_advance(self):
        self.crm.advance(self.opp_id, "proposal", "m1")
        self.assertEqual(self.crm.opps[self.opp_id]["stage"], "proposal")

    def _deal(self, amount):
        crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 5},
                {"id": "m1", "role": "manager", "capacity": 5},
            ]
        )
        lead_id = crm.add_lead("deal@corp.com", "D", "referral", "r1")
        crm.qualify(lead_id, "r1")
        return crm, crm.convert(lead_id, amount, "r1")

    def test_large_deal_needs_manager_for_negotiation(self):
        crm, opp_id = self._deal(50001)
        crm.advance(opp_id, "proposal", "r1")
        with self.assertRaises(PermissionError):
            crm.advance(opp_id, "negotiation", "r1")
        self.assertEqual(crm.opps[opp_id]["stage"], "proposal")
        self.assertEqual(len(crm.log), 4)
        crm.advance(opp_id, "negotiation", "m1")
        self.assertEqual(crm.opps[opp_id]["stage"], "negotiation")

    def test_threshold_deal_allowed_for_rep(self):
        crm, opp_id = self._deal(50000)
        crm.advance(opp_id, "proposal", "r1")
        crm.advance(opp_id, "negotiation", "r1")
        self.assertEqual(crm.opps[opp_id]["stage"], "negotiation")

    def test_large_deal_lost_does_not_need_manager(self):
        crm, opp_id = self._deal(90000)
        crm.advance(opp_id, "lost", "r1")
        self.assertEqual(crm.opps[opp_id]["stage"], "lost")

    def test_winning_frees_slot_and_assigns_queued_lead(self):
        crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 1},
                {"id": "m1", "role": "manager", "capacity": 5},
            ]
        )
        lead_id = new_qualified_lead(crm)
        waiting = crm.add_lead("queued@corp.com", "Q", "web", "m1")
        self.assertIsNone(crm.leads[waiting]["owner"])
        opp_id = crm.convert(lead_id, 100, "r1")
        self.assertEqual(crm.forecast()["open"], 1)
        crm.advance(opp_id, "proposal", "r1")
        crm.advance(opp_id, "negotiation", "r1")
        crm.advance(opp_id, "won", "r1")
        self.assertEqual(crm.leads[waiting]["owner"], "r1")
        self.assertEqual(crm.log[-1], ("assign", waiting, "system"))
        self.assertEqual(crm.forecast()["open"], 0)


if __name__ == "__main__":
    unittest.main()
