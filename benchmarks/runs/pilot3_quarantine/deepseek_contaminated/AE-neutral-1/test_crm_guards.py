"""Guard-ordering and load-accounting tests.

The spec fixes the order of checks inside each method and says the first
failing check decides the exception.  These tests pin that order down with
pairs of violations that raise different exception types, so a reordering in
``crm.py`` cannot pass silently.
"""

import unittest

from crm import CRM


def make_crm(reps=None):
    if reps is None:
        reps = [
            {"id": "r1", "role": "rep", "capacity": 2},
            {"id": "r2", "role": "rep", "capacity": 2},
            {"id": "m1", "role": "manager", "capacity": 10},
        ]
    return CRM(reps)


def deal(crm, amount=1000, email="deal@corp.com"):
    lead_id = crm.add_lead(email, "Deal", "referral", "m1")
    crm.qualify(lead_id, "m1")
    return lead_id, crm.convert(lead_id, amount, "m1")


class GuardOrderTests(unittest.TestCase):
    def test_advance_stage_check_beats_ownership_check(self):
        crm = make_crm()
        _, opp_id = deal(crm)
        with self.assertRaises(ValueError):
            crm.advance(opp_id, "bogus", "r2")
        self.assertEqual(crm.opps[opp_id]["stage"], "prospect")

    def test_convert_amount_check_beats_ownership_check(self):
        crm = make_crm()
        lead_id = crm.add_lead("a@corp.com", "A", "referral", "m1")
        crm.qualify(lead_id, "m1")
        with self.assertRaises(ValueError):
            crm.convert(lead_id, 0, "r2")
        self.assertEqual(crm.opps, {})

    def test_transfer_manager_check_beats_new_owner_check(self):
        crm = make_crm()
        _, opp_id = deal(crm)
        with self.assertRaises(PermissionError):
            crm.transfer(opp_id, "nobody", "r2")
        self.assertEqual(crm.opps[opp_id]["owner"], "r1")

    def test_qualify_existence_beats_ownership_check(self):
        crm = make_crm()
        with self.assertRaises(ValueError):
            crm.qualify("L99", "r2")

    def test_add_lead_source_check_beats_duplicate_check(self):
        crm = make_crm()
        crm.add_lead("a@corp.com", "A", "referral", "r1")
        with self.assertRaises(ValueError):
            crm.add_lead("a@corp.com", "A", "social", "r1")

    def test_add_lead_duplicate_beats_id_allocation(self):
        crm = make_crm()
        crm.add_lead("a@corp.com", "A", "referral", "r1")
        with self.assertRaises(Exception) as caught:
            crm.add_lead("A@Corp.com", "A", "referral", "r1")
        self.assertEqual(caught.exception.existing_id, "L1")
        self.assertEqual(crm.add_lead("b@corp.com", "B", "web", "r1"), "L2")

    def test_discount_validation_beats_final_stage(self):
        crm = make_crm()
        _, opp_id = deal(crm)
        crm.advance(opp_id, "lost", "m1")
        with self.assertRaises(ValueError):
            crm.discount(opp_id, 99, "m1")

    def test_unknown_actor_is_checked_first_in_every_method(self):
        crm = make_crm()
        lead_id, opp_id = deal(crm)
        calls = [
            lambda: crm.add_lead("bad", "", "bogus", "ghost"),
            lambda: crm.qualify("L99", "ghost"),
            lambda: crm.convert("L99", 0, "ghost"),
            lambda: crm.advance("O99", "bogus", "ghost"),
            lambda: crm.discount("O99", 99, "ghost"),
            lambda: crm.transfer("O99", "nobody", "ghost"),
        ]
        for call in calls:
            with self.subTest(call=call):
                with self.assertRaises(PermissionError):
                    call()
        self.assertEqual(crm.leads[lead_id]["status"], "converted")
        self.assertEqual(crm.opps[opp_id]["stage"], "prospect")


class LoadAccountingTests(unittest.TestCase):
    def test_open_opportunity_counts_against_capacity(self):
        crm = make_crm(
            [
                {"id": "r1", "role": "rep", "capacity": 3},
                {"id": "r2", "role": "rep", "capacity": 3},
                {"id": "m1", "role": "manager", "capacity": 10},
            ]
        )
        a = crm.add_lead("a@corp.com", "A", "referral", "m1")
        b = crm.add_lead("b@corp.com", "B", "referral", "m1")
        c = crm.add_lead("c@corp.com", "C", "referral", "m1")
        # Loads: 0/0 -> r1, 1/0 -> r2, 1/1 -> r1 (tie, smaller id).
        self.assertEqual(
            [crm.leads[x]["owner"] for x in (a, b, c)], ["r1", "r2", "r1"]
        )
        crm.qualify(a, "m1")
        crm.convert(a, 1000, "m1")
        # r1 now owns one open opp plus lead c; r2 owns one lead.
        d = crm.add_lead("d@corp.com", "D", "referral", "m1")
        self.assertEqual(crm.leads[d]["owner"], "r2")
        e = crm.add_lead("e@corp.com", "E", "referral", "m1")
        self.assertEqual(crm.leads[e]["owner"], "r1")

    def test_final_stage_stops_counting_toward_load(self):
        crm = make_crm(
            [
                {"id": "r1", "role": "rep", "capacity": 2},
                {"id": "r2", "role": "rep", "capacity": 2},
                {"id": "m1", "role": "manager", "capacity": 10},
            ]
        )
        a = crm.add_lead("a@corp.com", "A", "referral", "m1")
        b = crm.add_lead("b@corp.com", "B", "referral", "m1")
        self.assertEqual((crm.leads[a]["owner"], crm.leads[b]["owner"]), ("r1", "r2"))
        crm.qualify(a, "m1")
        opp_id = crm.convert(a, 1000, "m1")
        crm.advance(opp_id, "proposal", "m1")
        crm.advance(opp_id, "negotiation", "m1")
        crm.advance(opp_id, "won", "m1")
        # r1 (empty) and r2 (one lead) are both below capacity; r1 wins.
        c = crm.add_lead("c@corp.com", "C", "referral", "m1")
        self.assertEqual(crm.leads[c]["owner"], "r1")

    def test_capacity_is_a_strict_upper_bound(self):
        crm = make_crm(
            [
                {"id": "r1", "role": "rep", "capacity": 1},
                {"id": "m1", "role": "manager", "capacity": 5},
            ]
        )
        first = crm.add_lead("a@corp.com", "A", "referral", "m1")
        second = crm.add_lead("b@corp.com", "B", "referral", "m1")
        self.assertEqual(crm.leads[first]["owner"], "r1")
        self.assertIsNone(crm.leads[second]["owner"])


class NegotiationThresholdTests(unittest.TestCase):
    def test_threshold_uses_current_amount_after_discount(self):
        crm = make_crm()
        _, opp_id = deal(crm, amount=50001)
        owner = crm.opps[opp_id]["owner"]
        crm.advance(opp_id, "proposal", owner)
        crm.discount(opp_id, 1, "m1")  # 50001 -> 49500
        self.assertEqual(crm.opps[opp_id]["amount"], 49500)
        crm.advance(opp_id, "negotiation", owner)
        self.assertEqual(crm.opps[opp_id]["stage"], "negotiation")

    def test_threshold_uses_discounted_amount_for_manager_gate(self):
        crm = make_crm()
        _, opp_id = deal(crm, amount=40000)
        owner = crm.opps[opp_id]["owner"]
        crm.advance(opp_id, "proposal", owner)
        # Discounting never raises the amount, so 40000 stays under 50000.
        crm.discount(opp_id, 10, owner)
        crm.advance(opp_id, "negotiation", owner)
        self.assertEqual(crm.opps[opp_id]["stage"], "negotiation")

    def test_amount_50001_blocked_for_owner_but_allowed_for_manager(self):
        crm = make_crm()
        _, opp_id = deal(crm, amount=50001)
        owner = crm.opps[opp_id]["owner"]
        crm.advance(opp_id, "proposal", owner)
        with self.assertRaises(PermissionError):
            crm.advance(opp_id, "negotiation", owner)
        crm.advance(opp_id, "negotiation", "m1")
        self.assertEqual(crm.opps[opp_id]["stage"], "negotiation")


class DuplicateAcrossStagesTests(unittest.TestCase):
    def test_converted_lead_email_is_still_a_duplicate(self):
        crm = make_crm()
        lead_id = crm.add_lead("a@corp.com", "A", "referral", "m1")
        crm.qualify(lead_id, "m1")
        crm.convert(lead_id, 1000, "m1")
        with self.assertRaises(Exception) as caught:
            crm.add_lead(" A@Corp.COM ", "Again", "web", "m1")
        self.assertEqual(caught.exception.existing_id, lead_id)

    def test_qualified_lead_email_is_still_a_duplicate(self):
        crm = make_crm()
        lead_id = crm.add_lead("a@corp.com", "A", "referral", "m1")
        crm.qualify(lead_id, "m1")
        with self.assertRaises(Exception) as caught:
            crm.add_lead("a@corp.com", "Again", "web", "m1")
        self.assertEqual(caught.exception.existing_id, lead_id)


if __name__ == "__main__":
    unittest.main()
