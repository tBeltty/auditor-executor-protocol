"""Guard tests for spec rules the first delivery left unprotected.

Written in response to audit.md sections 3.1-3.7.  Each test is designed to
fail against a specific spec-violating mutation that the original suite let
through, and to pass against crm.py as delivered.  Where two checks raise the
same exception type, the test also asserts the observable state, so it cannot
pass merely because a later, unrelated check rejected the call.
"""

import unittest

from crm import CRM, DuplicateLeadError


def crm_one_rep(capacity=10):
    return CRM([
        {"id": "r1", "role": "rep", "capacity": capacity},
        {"id": "m1", "role": "manager", "capacity": 5},
    ])


def crm_two_reps(cap1=10, cap2=10):
    return CRM([
        {"id": "r1", "role": "rep", "capacity": cap1},
        {"id": "r2", "role": "rep", "capacity": cap2},
        {"id": "m1", "role": "manager", "capacity": 10},
    ])


def make_qualified(crm, email="a@corp.com", source="referral", actor="r1"):
    lead_id = crm.add_lead(email, "N", source, actor)
    crm.qualify(lead_id, actor)
    return lead_id


def make_opportunity(crm, amount=1000, email="a@corp.com", actor="r1"):
    lead_id = make_qualified(crm, email=email, actor=actor)
    return crm.convert(lead_id, amount, actor)


def win(crm, opp_id, actor="r1"):
    crm.advance(opp_id, "proposal", actor)
    crm.advance(opp_id, "negotiation", actor)
    crm.advance(opp_id, "won", actor)


class TestWonIsFinal(unittest.TestCase):
    """Audit 3.1: deleting advance's final-stage check must fail these."""

    def setUp(self):
        self.crm = crm_two_reps()
        self.opp_id = make_opportunity(self.crm, amount=1000)
        win(self.crm, self.opp_id)
        self.assertEqual(self.crm.opps[self.opp_id]["stage"], "won")

    def test_won_cannot_move_to_lost(self):
        log_before = list(self.crm.log)
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp_id, "lost", "r1")
        self.assertEqual(self.crm.opps[self.opp_id]["stage"], "won")
        self.assertEqual(self.crm.log, log_before)

    def test_won_cannot_be_advanced_to_won(self):
        log_before = list(self.crm.log)
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp_id, "won", "r1")
        self.assertEqual(self.crm.opps[self.opp_id]["stage"], "won")
        self.assertEqual(self.crm.log, log_before)

    def test_won_cannot_be_advanced_by_manager(self):
        log_before = list(self.crm.log)
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp_id, "lost", "m1")
        self.assertEqual(self.crm.opps[self.opp_id]["stage"], "won")
        self.assertEqual(self.crm.log, log_before)


class TestLostIsFinal(unittest.TestCase):
    """Audit 3.8: the original lost test passed on a ValueError raised by
    _STAGE_ORDER.index("lost"), not by the finality check.  Re-advancing to
    "lost" is the only target that isolates the finality check."""

    def test_lost_cannot_be_advanced_to_lost(self):
        crm = crm_two_reps()
        opp_id = make_opportunity(crm)
        crm.advance(opp_id, "lost", "r1")
        log_before = list(crm.log)
        with self.assertRaises(ValueError):
            crm.advance(opp_id, "lost", "r1")
        self.assertEqual(crm.opps[opp_id]["stage"], "lost")
        self.assertEqual(crm.log, log_before)


class TestLostFromAnyNonFinalStage(unittest.TestCase):
    """Audit 3.2: restricting "lost" to prospect must fail these tests."""

    def test_lost_from_proposal(self):
        crm = crm_two_reps()
        opp_id = make_opportunity(crm)
        crm.advance(opp_id, "proposal", "r1")
        crm.advance(opp_id, "lost", "r1")
        self.assertEqual(crm.opps[opp_id]["stage"], "lost")
        self.assertEqual(crm.log[-1], ("advance", opp_id, "r1"))

    def test_lost_from_negotiation(self):
        crm = crm_two_reps()
        opp_id = make_opportunity(crm)
        crm.advance(opp_id, "proposal", "r1")
        crm.advance(opp_id, "negotiation", "r1")
        self.assertEqual(crm.opps[opp_id]["stage"], "negotiation")
        crm.advance(opp_id, "lost", "r1")
        self.assertEqual(crm.opps[opp_id]["stage"], "lost")
        self.assertEqual(crm.forecast(), {"open": 0, "weighted": 0, "won": 0})


class TestForecastWonUsesCurrentAmount(unittest.TestCase):
    """Audit 3.3: forecast()["won"] must sum amount, not original_amount."""

    def test_won_after_manager_discount(self):
        crm = crm_two_reps()
        opp_id = make_opportunity(crm, amount=1000)
        crm.discount(opp_id, 10, "m1")
        win(crm, opp_id)
        self.assertEqual(crm.forecast(), {"open": 0, "weighted": 0, "won": 900})


class TestOpportunityIdsCountConversions(unittest.TestCase):
    """Audit 3.4: the opportunity counter advances on convert, not qualify."""

    def test_qualify_does_not_consume_opportunity_number(self):
        crm = crm_one_rep()
        lead_a = make_qualified(crm, email="a@corp.com")
        lead_b = make_qualified(crm, email="b@corp.com")
        self.assertEqual(crm.convert(lead_b, 200, "r1"), "O1")
        self.assertEqual(crm.convert(lead_a, 100, "r1"), "O2")
        self.assertEqual(crm.opps["O1"]["lead_id"], lead_b)
        self.assertEqual(crm.opps["O2"]["lead_id"], lead_a)


class TestDiscountUsesFloorDivision(unittest.TestCase):
    """Audit 3.5: 1015 at 10% is 913 floored, 914 rounded."""

    def test_1015_at_ten_percent_floors_to_913(self):
        crm = crm_two_reps()
        opp_id = make_opportunity(crm, amount=1015)
        crm.discount(opp_id, 10, "m1")
        self.assertEqual(crm.opps[opp_id]["amount"], 913)
        self.assertEqual(crm.opps[opp_id]["original_amount"], 1015)


class TestScoreUsesNormalizedDomain(unittest.TestCase):
    """Audit 3.6: the free-domain exemption reads the normalized email."""

    def test_uppercase_free_domain_gets_no_bonus(self):
        crm = crm_two_reps()
        lead_id = crm.add_lead("A@GMAIL.COM", "A", "web", "r1")
        self.assertEqual(crm.leads[lead_id]["email"], "a@gmail.com")
        self.assertEqual(crm.leads[lead_id]["score"], 10)

    def test_uppercase_corporate_domain_gets_bonus(self):
        crm = crm_two_reps()
        lead_id = crm.add_lead("A@CORP.COM", "A", "web", "r1")
        self.assertEqual(crm.leads[lead_id]["score"], 25)


class TestAdvanceCheckOrder(unittest.TestCase):
    """Audit 3.7: each call violates two checks; the earlier check wins."""

    def test_stage_validity_before_permission(self):
        crm = crm_two_reps()
        opp_id = make_opportunity(crm)
        with self.assertRaises(ValueError):
            crm.advance(opp_id, "bogus", "r2")
        self.assertEqual(crm.opps[opp_id]["stage"], "prospect")

    def test_permission_before_finality(self):
        crm = crm_two_reps()
        opp_id = make_opportunity(crm)
        win(crm, opp_id)
        with self.assertRaises(PermissionError):
            crm.advance(opp_id, "lost", "r2")
        self.assertEqual(crm.opps[opp_id]["stage"], "won")

    def test_transition_before_large_deal_manager_gate(self):
        crm = crm_two_reps()
        opp_id = make_opportunity(crm, amount=60000)
        with self.assertRaises(ValueError):
            crm.advance(opp_id, "negotiation", "r1")
        self.assertEqual(crm.opps[opp_id]["stage"], "prospect")


class TestConvertCheckOrder(unittest.TestCase):
    """Audit 3.7: amount validity is checked before the actor's permission."""

    def test_amount_before_permission(self):
        crm = crm_two_reps()
        lead_id = make_qualified(crm)
        with self.assertRaises(ValueError):
            crm.convert(lead_id, 0, "r2")
        self.assertEqual(crm.opps, {})
        self.assertEqual(crm.leads[lead_id]["status"], "qualified")


class TestDiscountCheckOrder(unittest.TestCase):
    """Audit 3.7: the four adjacent discount checks keep spec order."""

    def test_pct_validity_before_permission(self):
        crm = crm_two_reps()
        opp_id = make_opportunity(crm)
        with self.assertRaises(ValueError):
            crm.discount(opp_id, 99, "r2")
        self.assertEqual(crm.opps[opp_id]["amount"], 1000)

    def test_permission_before_finality(self):
        crm = crm_two_reps()
        opp_id = make_opportunity(crm)
        crm.advance(opp_id, "lost", "r1")
        with self.assertRaises(PermissionError):
            crm.discount(opp_id, 5, "r2")
        self.assertEqual(crm.opps[opp_id]["amount"], 1000)
        self.assertEqual(crm.opps[opp_id]["stage"], "lost")

    def test_finality_before_rep_cap(self):
        crm = crm_two_reps()
        opp_id = make_opportunity(crm)
        crm.advance(opp_id, "lost", "r1")
        with self.assertRaises(ValueError):
            crm.discount(opp_id, 11, "r1")
        self.assertEqual(crm.opps[opp_id]["amount"], 1000)

    def test_rep_cap_before_cumulative_cap(self):
        crm = crm_two_reps()
        opp_id = make_opportunity(crm, amount=1000)
        crm.discount(opp_id, 30, "m1")
        self.assertEqual(crm.opps[opp_id]["amount"], 700)
        # A rep using 11 would also break the cumulative cap; the rep cap (5)
        # is checked before the cumulative cap (6), so PermissionError wins.
        with self.assertRaises(PermissionError):
            crm.discount(opp_id, 11, "r1")
        self.assertEqual(crm.opps[opp_id]["amount"], 700)


class TestTransferCheckOrder(unittest.TestCase):
    """Audit 3.7: existence, then manager-only, then target role."""

    def test_existence_before_manager_only(self):
        crm = crm_two_reps()
        with self.assertRaises(ValueError):
            crm.transfer("O999", "r2", "r1")

    def test_manager_only_before_target_role(self):
        crm = crm_two_reps()
        opp_id = make_opportunity(crm)
        with self.assertRaises(PermissionError):
            crm.transfer(opp_id, "m1", "r1")
        self.assertEqual(crm.opps[opp_id]["owner"], "r1")


class TestAddLeadCheckOrder(unittest.TestCase):
    """Audit 3.7: name and source are validated before duplicate email."""

    def test_name_before_duplicate(self):
        crm = crm_two_reps()
        crm.add_lead("a@corp.com", "A", "web", "r1")
        log_before = list(crm.log)
        try:
            crm.add_lead("a@corp.com", "   ", "web", "r1")
        except DuplicateLeadError:
            self.fail("name check must run before the duplicate check")
        except ValueError:
            pass
        else:
            self.fail("a blank name must raise ValueError")
        self.assertEqual(len(crm.leads), 1)
        self.assertEqual(crm.log, log_before)

    def test_source_before_duplicate(self):
        crm = crm_two_reps()
        crm.add_lead("a@corp.com", "A", "web", "r1")
        log_before = list(crm.log)
        try:
            crm.add_lead("a@corp.com", "B", "bogus", "r1")
        except DuplicateLeadError:
            self.fail("source check must run before the duplicate check")
        except ValueError:
            pass
        else:
            self.fail("an invalid source must raise ValueError")
        self.assertEqual(len(crm.leads), 1)
        self.assertEqual(crm.log, log_before)


if __name__ == "__main__":
    unittest.main()
