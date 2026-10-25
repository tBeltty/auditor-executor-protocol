import unittest

from crm import CRM

CHAIN = ["prospect", "proposal", "negotiation", "won"]


def make_crm(cap1=5, cap2=5, boss_capacity=0):
    return CRM(
        [
            {"id": "rep1", "role": "rep", "capacity": cap1},
            {"id": "rep2", "role": "rep", "capacity": cap2},
            {"id": "boss", "role": "manager", "capacity": boss_capacity},
        ]
    )


def walk(crm, opp_id, target, actor="rep1", manager="boss"):
    if target == "lost":
        crm.advance(opp_id, "lost", actor)
        return
    while crm.opps[opp_id]["stage"] != target:
        current = crm.opps[opp_id]["stage"]
        nxt = CHAIN[CHAIN.index(current) + 1]
        who = manager if (nxt == "negotiation" and crm.opps[opp_id]["amount"] > 50000) else actor
        crm.advance(opp_id, nxt, who)


def new_opp(crm, email="ana@corp.io", source="referral", amount=1000, actor="rep1"):
    lead_id = crm.add_lead(email, "Ana", source, actor)
    owner = crm.leads[lead_id]["owner"] or "boss"
    crm.qualify(lead_id, owner)
    return crm.convert(lead_id, amount, owner)


class AssignmentTest(unittest.TestCase):
    def test_tie_breaks_on_smallest_id_string(self):
        crm = CRM(
            [
                {"id": "r2", "role": "rep", "capacity": 5},
                {"id": "r10", "role": "rep", "capacity": 5},
            ]
        )
        lead_id = crm.add_lead("ana@corp.io", "Ana", "web", "r2")
        self.assertEqual(crm.leads[lead_id]["owner"], "r10")

    def test_lowest_load_wins_and_alternates(self):
        crm = make_crm()
        owners = [
            crm.leads[crm.add_lead("u%d@corp.io" % i, "A", "web", "rep1")]["owner"]
            for i in range(4)
        ]
        self.assertEqual(owners, ["rep1", "rep2", "rep1", "rep2"])

    def test_full_reps_produce_unowned_leads_in_queue(self):
        crm = make_crm(cap1=1, cap2=0)
        first = crm.add_lead("a@corp.io", "A", "web", "rep1")
        second = crm.add_lead("b@corp.io", "B", "web", "rep1")
        third = crm.add_lead("c@corp.io", "C", "web", "rep1")
        self.assertEqual(crm.leads[first]["owner"], "rep1")
        self.assertIsNone(crm.leads[second]["owner"])
        self.assertIsNone(crm.leads[third]["owner"])
        self.assertEqual(crm.waiting, [second, third])

    def test_manager_never_receives_work(self):
        crm = make_crm(cap1=0, cap2=0, boss_capacity=5)
        lead_id = crm.add_lead("a@corp.io", "A", "web", "rep1")
        self.assertIsNone(crm.leads[lead_id]["owner"])

    def test_qualified_leads_still_count_toward_load(self):
        crm = make_crm(cap1=1, cap2=0)
        first = crm.add_lead("a@corp.io", "A", "referral", "rep1")
        crm.qualify(first, "rep1")
        second = crm.add_lead("b@corp.io", "B", "web", "rep1")
        self.assertIsNone(crm.leads[second]["owner"])
        self.assertEqual(crm.waiting, [second])

    def test_open_opportunities_count_toward_load(self):
        crm = make_crm(cap1=1, cap2=0)
        first = crm.add_lead("a@corp.io", "A", "referral", "rep1")
        crm.qualify(first, "rep1")
        crm.convert(first, 1000, "rep1")
        second = crm.add_lead("b@corp.io", "B", "web", "rep1")
        self.assertIsNone(crm.leads[second]["owner"])
        self.assertEqual(crm.waiting, [second])

    def test_converted_lead_no_longer_counts_toward_load(self):
        # crm.md:9 -- only leads with status "new" or "qualified" count.  Once
        # the lead is converted and its opportunity is closed, the rep has a
        # free slot again even though the lead row still says "converted".
        crm = make_crm(cap1=1, cap2=5)
        lead_id = crm.add_lead("a@corp.io", "A", "referral", "rep1")
        self.assertEqual(crm.leads[lead_id]["owner"], "rep1")
        crm.qualify(lead_id, "rep1")
        opp_id = crm.convert(lead_id, 1000, "rep1")
        crm.advance(opp_id, "lost", "rep1")
        self.assertEqual(crm.leads[lead_id]["status"], "converted")
        self.assertEqual(crm.opps[opp_id]["stage"], "lost")
        replacement = crm.add_lead("b@corp.io", "B", "web", "rep1")
        self.assertEqual(crm.leads[replacement]["owner"], "rep1")
        self.assertEqual(crm.waiting, [])


class WaitingQueueTest(unittest.TestCase):
    def test_win_assigns_oldest_waiting_lead_and_logs_system(self):
        crm = make_crm(cap1=1, cap2=0)
        opp_id = new_opp(crm)
        waiting_id = crm.add_lead("b@corp.io", "B", "web", "rep1")
        self.assertIsNone(crm.leads[waiting_id]["owner"])
        walk(crm, opp_id, "won")
        self.assertEqual(crm.leads[waiting_id]["owner"], "rep1")
        self.assertEqual(crm.waiting, [])
        self.assertEqual(crm.log[-2], ("advance", opp_id, "rep1"))
        self.assertEqual(crm.log[-1], ("assign", waiting_id, "system"))

    def test_queue_is_fifo(self):
        crm = make_crm(cap1=2, cap2=0)
        first = new_opp(crm)
        second = crm.add_lead("b@corp.io", "B", "referral", "rep1")
        crm.qualify(second, "rep1")
        third = crm.add_lead("c@corp.io", "C", "web", "rep1")
        fourth = crm.add_lead("d@corp.io", "D", "web", "rep1")
        self.assertEqual(crm.waiting, [third, fourth])
        walk(crm, first, "lost")
        self.assertEqual(crm.leads[third]["owner"], "rep1")
        self.assertEqual(crm.waiting, [fourth])
        second_opp = crm.convert(second, 500, "rep1")
        walk(crm, second_opp, "lost")
        self.assertEqual(crm.leads[fourth]["owner"], "rep1")
        self.assertEqual(crm.waiting, [])

    def test_no_assignment_when_queue_is_empty(self):
        crm = make_crm(cap1=2, cap2=0)
        opp_id = new_opp(crm)
        walk(crm, opp_id, "won")
        self.assertEqual(crm.waiting, [])
        self.assertEqual([entry[0] for entry in crm.log[-1:]], ["advance"])

    def test_lost_stage_frees_the_slot_too(self):
        crm = make_crm(cap1=1, cap2=0)
        opp_id = new_opp(crm)
        waiting_id = crm.add_lead("b@corp.io", "B", "web", "rep1")
        crm.advance(opp_id, "lost", "rep1")
        self.assertEqual(crm.leads[waiting_id]["owner"], "rep1")
        self.assertEqual(crm.log[-1], ("assign", waiting_id, "system"))


class PermissionTest(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm(cap1=5, cap2=0)
        self.lead_id = self.crm.add_lead("ana@corp.io", "Ana", "referral", "rep1")
        self.opp_id = new_opp(self.crm, email="bo@corp.io")

    def test_unknown_actor_is_rejected_first_everywhere(self):
        crm = make_crm()
        with self.assertRaises(PermissionError):
            crm.add_lead("a@corp.io", "A", "web", "ghost")
        with self.assertRaises(PermissionError):
            crm.qualify("L404", "ghost")
        with self.assertRaises(PermissionError):
            crm.convert("L404", 10, "ghost")
        with self.assertRaises(PermissionError):
            crm.advance("O404", "won", "ghost")
        with self.assertRaises(PermissionError):
            crm.discount("O404", 5, "ghost")
        with self.assertRaises(PermissionError):
            crm.transfer("O404", "rep1", "ghost")
        self.assertEqual(crm.log, [])

    def test_other_rep_cannot_qualify(self):
        with self.assertRaises(PermissionError):
            self.crm.qualify(self.lead_id, "rep2")

    def test_other_rep_cannot_convert(self):
        self.crm.qualify(self.lead_id, "rep1")
        with self.assertRaises(PermissionError):
            self.crm.convert(self.lead_id, 100, "rep2")

    def test_other_rep_cannot_advance(self):
        with self.assertRaises(PermissionError):
            self.crm.advance(self.opp_id, "proposal", "rep2")

    def test_other_rep_cannot_discount(self):
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp_id, 5, "rep2")

    def test_manager_may_act_on_any_lead_and_opportunity(self):
        crm = make_crm()
        lead_id = crm.add_lead("ana@corp.io", "Ana", "referral", "rep1")
        crm.qualify(lead_id, "boss")
        opp_id = crm.convert(lead_id, 1000, "boss")
        crm.advance(opp_id, "proposal", "boss")
        crm.discount(opp_id, 5, "boss")
        crm.transfer(opp_id, "rep2", "boss")

    def test_existence_is_checked_before_permission(self):
        with self.assertRaises(ValueError):
            self.crm.qualify("L404", "rep2")
        with self.assertRaises(ValueError):
            self.crm.convert("L404", 100, "rep2")
        with self.assertRaises(ValueError):
            self.crm.advance("O404", "proposal", "rep2")
        with self.assertRaises(ValueError):
            self.crm.discount("O404", 5, "rep2")

    def test_argument_validity_is_checked_before_permission(self):
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp_id, "closed", "rep2")
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp_id, 99, "rep2")
        with self.assertRaises(ValueError):
            self.crm.convert(self.lead_id, -1, "rep2")

    def test_transfer_requires_manager_before_owner_validation(self):
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.opp_id, "ghost", "rep1")

    def test_unowned_lead_cannot_be_qualified_by_a_rep(self):
        crm = make_crm(cap1=0, cap2=0)
        lead_id = crm.add_lead("ana@corp.io", "Ana", "referral", "rep1")
        with self.assertRaises(PermissionError):
            crm.qualify(lead_id, "rep1")
        crm.qualify(lead_id, "boss")
        self.assertEqual(crm.leads[lead_id]["status"], "qualified")


class QualifyTest(unittest.TestCase):
    def test_web_free_domain_lead_below_threshold(self):
        crm = make_crm()
        lead_id = crm.add_lead("ana@gmail.com", "Ana", "web", "rep1")
        with self.assertRaises(ValueError):
            crm.qualify(lead_id, "rep1")
        self.assertEqual(crm.leads[lead_id]["status"], "new")

    def test_web_corporate_lead_below_threshold(self):
        crm = make_crm()
        lead_id = crm.add_lead("ana@corp.io", "Ana", "web", "rep1")
        with self.assertRaises(ValueError):
            crm.qualify(lead_id, "rep1")

    def test_threshold_boundary_is_qualifiable(self):
        crm = make_crm()
        lead_id = crm.add_lead("ana@gmail.com", "Ana", "referral", "rep1")
        crm.qualify(lead_id, "rep1")
        self.assertEqual(crm.leads[lead_id]["status"], "qualified")
        self.assertEqual(crm.log[-1], ("qualify", lead_id, "rep1"))

    def test_cannot_qualify_twice(self):
        crm = make_crm()
        lead_id = crm.add_lead("ana@corp.io", "Ana", "referral", "rep1")
        crm.qualify(lead_id, "rep1")
        with self.assertRaises(ValueError):
            crm.qualify(lead_id, "rep1")

    def test_cannot_qualify_converted_lead(self):
        crm = make_crm()
        opp_id = new_opp(crm)
        lead_id = crm.opps[opp_id]["lead_id"]
        with self.assertRaises(ValueError):
            crm.qualify(lead_id, "rep1")


class ConvertTest(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        self.lead_id = self.crm.add_lead("ana@corp.io", "Ana", "referral", "rep1")
        self.crm.qualify(self.lead_id, "rep1")

    def test_bad_amounts_are_rejected(self):
        for bad in (True, False, 0, -5, 1.5, "100", None, [100]):
            with self.assertRaises(ValueError):
                self.crm.convert(self.lead_id, bad, "rep1")
        self.assertEqual(self.crm.opps, {})

    def test_unknown_lead_is_rejected(self):
        with self.assertRaises(ValueError):
            self.crm.convert("L404", 100, "rep1")

    def test_unqualified_lead_is_rejected(self):
        crm = make_crm()
        lead_id = crm.add_lead("ana@corp.io", "Ana", "referral", "rep1")
        with self.assertRaises(ValueError):
            crm.convert(lead_id, 100, "rep1")

    def test_unowned_lead_is_rejected(self):
        crm = make_crm(cap1=0, cap2=0)
        lead_id = crm.add_lead("ana@corp.io", "Ana", "referral", "rep1")
        crm.qualify(lead_id, "boss")
        with self.assertRaises(ValueError):
            crm.convert(lead_id, 100, "boss")

    def test_successful_conversion_shape(self):
        opp_id = self.crm.convert(self.lead_id, 2500, "rep1")
        self.assertEqual(opp_id, "O1")
        self.assertEqual(
            self.crm.opps[opp_id],
            {
                "id": "O1",
                "lead_id": self.lead_id,
                "owner": "rep1",
                "amount": 2500,
                "original_amount": 2500,
                "stage": "prospect",
            },
        )
        self.assertEqual(self.crm.leads[self.lead_id]["status"], "converted")
        self.assertEqual(self.crm.log[-1], ("convert", "O1", "rep1"))

    def test_opportunity_ids_increment_on_success_only(self):
        self.crm.convert(self.lead_id, 100, "rep1")
        other = self.crm.add_lead("bo@corp.io", "Bo", "referral", "rep1")
        crm_owner = self.crm.leads[other]["owner"] or "boss"
        self.crm.qualify(other, crm_owner)
        with self.assertRaises(ValueError):
            self.crm.convert(other, 0, "rep1")
        self.assertEqual(self.crm.convert(other, 100, crm_owner), "O2")


class AdvanceTest(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        self.opp_id = new_opp(self.crm)

    def test_invalid_stage_names_rejected(self):
        for bad in ("QUALIFIED", "", None, "closed", "PROSPECT"):
            with self.assertRaises(ValueError):
                self.crm.advance(self.opp_id, bad, "rep1")

    def test_invalid_stage_names_are_rejected_before_the_permission_check(self):
        # crm.md:10 + crm.md:30 -- check 2 (valid stage name) runs before check
        # 3 (permission), so a non-owner actor still gets ValueError, not
        # PermissionError.  This is what makes the named-stage guard observable
        # even though the transition guard would also reject "closed".
        for bad in ("closed", "QUALIFIED", "", None, "PROSPECT", "won "):
            with self.assertRaises(ValueError):
                self.crm.advance(self.opp_id, bad, "rep2")
        self.assertEqual(self.crm.opps[self.opp_id]["stage"], "prospect")

    def test_unknown_opportunity_rejected(self):
        with self.assertRaises(ValueError):
            self.crm.advance("O404", "proposal", "rep1")

    def test_skipping_a_stage_is_rejected(self):
        for bad in ("negotiation", "won"):
            with self.assertRaises(ValueError):
                self.crm.advance(self.opp_id, bad, "rep1")
        self.assertEqual(self.crm.opps[self.opp_id]["stage"], "prospect")

    def test_going_backwards_is_rejected(self):
        walk(self.crm, self.opp_id, "negotiation")
        for bad in ("proposal", "prospect"):
            with self.assertRaises(ValueError):
                self.crm.advance(self.opp_id, bad, "rep1")

    def test_same_stage_is_rejected(self):
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp_id, "prospect", "rep1")

    def test_lost_is_reachable_from_every_open_stage(self):
        for start, target in (("prospect", "lost"), ("proposal", "lost")):
            crm = make_crm()
            opp_id = new_opp(crm, email="%s@corp.io" % start)
            while crm.opps[opp_id]["stage"] != start:
                walk(crm, opp_id, start)
            crm.advance(opp_id, target, "rep1")
            self.assertEqual(crm.opps[opp_id]["stage"], "lost")
            self.assertEqual(crm.log[-1], ("advance", opp_id, "rep1"))

    def test_full_chain_logs_every_step(self):
        walk(self.crm, self.opp_id, "won")
        self.assertEqual(self.crm.opps[self.opp_id]["stage"], "won")
        self.assertEqual(
            [entry[0] for entry in self.crm.log[-3:]],
            ["advance", "advance", "advance"],
        )
        self.assertEqual(self.crm.log[-1], ("advance", self.opp_id, "rep1"))

    def test_final_stages_are_terminal(self):
        walk(self.crm, self.opp_id, "won")
        before = dict(self.crm.opps[self.opp_id])
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp_id, "lost", "rep1")
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp_id, "prospect", "rep1")
        self.assertEqual(self.crm.opps[self.opp_id], before)

    def test_lost_is_terminal(self):
        self.crm.advance(self.opp_id, "lost", "rep1")
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp_id, "prospect", "rep1")

    def test_negotiation_can_go_lost(self):
        walk(self.crm, self.opp_id, "negotiation")
        self.crm.advance(self.opp_id, "lost", "rep1")
        self.assertEqual(self.crm.opps[self.opp_id]["stage"], "lost")


class BigDealApprovalTest(unittest.TestCase):
    def _opp_at_proposal(self, amount):
        crm = make_crm()
        opp_id = new_opp(crm, amount=amount)
        crm.advance(opp_id, "proposal", "rep1")
        return crm, opp_id

    def test_rep_cannot_take_big_deal_to_negotiation(self):
        crm, opp_id = self._opp_at_proposal(50001)
        with self.assertRaises(PermissionError):
            crm.advance(opp_id, "negotiation", "rep1")
        self.assertEqual(crm.opps[opp_id]["stage"], "proposal")

    def test_manager_can_take_big_deal_to_negotiation(self):
        crm, opp_id = self._opp_at_proposal(50001)
        crm.advance(opp_id, "negotiation", "boss")
        self.assertEqual(crm.opps[opp_id]["stage"], "negotiation")

    def test_exactly_fifty_thousand_needs_no_manager(self):
        crm, opp_id = self._opp_at_proposal(50000)
        crm.advance(opp_id, "negotiation", "rep1")
        self.assertEqual(crm.opps[opp_id]["stage"], "negotiation")

    def test_big_deal_can_still_go_lost_without_manager(self):
        crm, opp_id = self._opp_at_proposal(90000)
        crm.advance(opp_id, "lost", "rep1")
        self.assertEqual(crm.opps[opp_id]["stage"], "lost")


class DiscountTest(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        self.opp_id = new_opp(self.crm, amount=1000)

    def test_invalid_percentages_rejected(self):
        for bad in (True, False, 0, 31, -5, 10.5, "10", None):
            with self.assertRaises(ValueError):
                self.crm.discount(self.opp_id, bad, "rep1")
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 1000)

    def test_lower_bound_of_one_percent_is_accepted(self):
        self.crm.discount(self.opp_id, 1, "rep1")
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 990)
        self.assertEqual(self.crm.log[-1], ("discount", self.opp_id, "rep1"))

    def test_rep_limit_is_ten(self):
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp_id, 11, "rep1")
        self.crm.discount(self.opp_id, 10, "rep1")
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 900)

    def test_manager_may_use_full_range(self):
        self.crm.discount(self.opp_id, 30, "boss")
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 700)

    def test_discount_on_final_stage_rejected(self):
        walk(self.crm, self.opp_id, "won")
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp_id, 5, "boss")

    def test_cumulative_floor_is_enforced(self):
        self.crm.discount(self.opp_id, 30, "boss")
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 700)
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp_id, 1, "boss")
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 700)

    def test_floor_uses_original_amount_and_integer_truncation(self):
        crm = make_crm()
        opp_id = new_opp(crm, amount=999)
        with self.assertRaises(ValueError):
            crm.discount(opp_id, 30, "boss")
        self.assertEqual(crm.opps[opp_id]["amount"], 999)

    def test_two_steps_can_reach_exactly_the_floor(self):
        crm = make_crm()
        opp_id = new_opp(crm, amount=1000)
        crm.discount(opp_id, 20, "boss")
        crm.discount(opp_id, 12, "boss")
        self.assertEqual(crm.opps[opp_id]["amount"], 704)
        with self.assertRaises(ValueError):
            crm.discount(opp_id, 1, "boss")
        self.assertEqual(crm.opps[opp_id]["amount"], 704)

    def test_repeated_rep_discounts_stop_at_the_floor(self):
        amounts = []
        for _ in range(3):
            self.crm.discount(self.opp_id, 10, "rep1")
            amounts.append(self.crm.opps[self.opp_id]["amount"])
        self.assertEqual(amounts, [900, 810, 729])
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp_id, 10, "rep1")
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 729)

    def test_amount_truncation(self):
        crm = make_crm()
        opp_id = new_opp(crm, amount=999)
        crm.discount(opp_id, 10, "boss")
        self.assertEqual(crm.opps[opp_id]["amount"], 899)

    def test_discount_logs(self):
        self.crm.discount(self.opp_id, 5, "rep1")
        self.assertEqual(self.crm.log[-1], ("discount", self.opp_id, "rep1"))


class TransferTest(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm(cap1=1, cap2=1)
        self.opp_id = new_opp(self.crm)
        self.assertEqual(self.crm.opps[self.opp_id]["owner"], "rep1")

    def test_only_manager_may_transfer(self):
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.opp_id, "rep2", "rep1")

    def test_new_owner_must_be_a_known_rep(self):
        crm = make_crm(cap1=1, cap2=1, boss_capacity=5)
        opp_id = new_opp(crm)
        for bad in ("ghost", "boss", None, "", [], {}, 0):
            with self.assertRaises(ValueError):
                crm.transfer(opp_id, bad, "boss")
        self.assertEqual(crm.opps[opp_id]["owner"], "rep1")
        self.assertEqual(crm.waiting, [])

    def test_unknown_opportunity_rejected(self):
        with self.assertRaises(ValueError):
            self.crm.transfer("O404", "rep2", "boss")

    def test_same_owner_rejected(self):
        crm = make_crm(cap1=5, cap2=5)
        opp_id = new_opp(crm)
        with self.assertRaises(ValueError):
            crm.transfer(opp_id, "rep1", "boss")
        self.assertEqual(crm.opps[opp_id]["owner"], "rep1")

    def test_final_stage_rejected(self):
        walk(self.crm, self.opp_id, "lost")
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp_id, "rep2", "boss")

    def test_full_target_rejected(self):
        crm = make_crm(cap1=1, cap2=1)
        opp_id = new_opp(crm, email="a@corp.io")
        crm.add_lead("b@corp.io", "B", "referral", "rep1")
        self.assertEqual(crm.leads["L2"]["owner"], "rep2")
        with self.assertRaises(ValueError):
            crm.transfer(opp_id, "rep2", "boss")

    def test_transfer_moves_owner_and_logs(self):
        crm = make_crm(cap1=1, cap2=2)
        opp_id = new_opp(crm)
        crm.transfer(opp_id, "rep2", "boss")
        self.assertEqual(crm.opps[opp_id]["owner"], "rep2")
        self.assertEqual(crm.log[-1], ("transfer", opp_id, "boss"))

    def test_transfer_counts_open_opportunities_against_capacity(self):
        crm = make_crm(cap1=5, cap2=1)
        opp_id = new_opp(crm)
        other = crm.add_lead("b@corp.io", "B", "referral", "rep1")
        self.assertEqual(crm.leads[other]["owner"], "rep2")
        with self.assertRaises(ValueError):
            crm.transfer(opp_id, "rep2", "boss")
        self.assertEqual(crm.opps[opp_id]["owner"], "rep1")

    def test_target_at_capacity_minus_one_is_accepted(self):
        # crm.md:38 r6 rejects only load >= capacity, so a target one slot
        # below its capacity must be allowed.
        crm = make_crm(cap1=5, cap2=2)
        opp_id = new_opp(crm, email="a@corp.io")
        crm.add_lead("b@corp.io", "B", "referral", "rep1")
        crm.add_lead("c@corp.io", "C", "referral", "rep1")
        self.assertEqual(crm.leads["L2"]["owner"], "rep2")
        self.assertEqual(crm._load("rep2"), 1)
        crm.transfer(opp_id, "rep2", "boss")
        self.assertEqual(crm.opps[opp_id]["owner"], "rep2")
        self.assertEqual(crm.log[-1], ("transfer", opp_id, "boss"))
        self.assertEqual(crm.waiting, [])


class ForecastTest(unittest.TestCase):
    def test_empty_crm(self):
        self.assertEqual(make_crm().forecast(), {"open": 0, "weighted": 0, "won": 0})

    def test_weights_and_won_sum(self):
        crm = make_crm()
        prospect = new_opp(crm, email="a@corp.io", amount=1000)
        proposal = new_opp(crm, email="b@corp.io", amount=2000)
        negotiation = new_opp(crm, email="c@corp.io", amount=3000)
        won = new_opp(crm, email="d@corp.io", amount=5000)
        crm.advance(proposal, "proposal", "boss")
        crm.advance(negotiation, "proposal", "boss")
        crm.advance(negotiation, "negotiation", "boss")
        walk(crm, won, "won", actor="boss")
        self.assertEqual(crm.forecast(), {"open": 3, "weighted": 2500, "won": 5000})
        self.assertEqual(crm.opps[prospect]["stage"], "prospect")

    def test_lost_is_excluded(self):
        crm = make_crm()
        opp_id = new_opp(crm, amount=4000)
        crm.advance(opp_id, "lost", "rep1")
        self.assertEqual(crm.forecast(), {"open": 0, "weighted": 0, "won": 0})

    def test_forecast_truncates_each_opportunity(self):
        # crm.md:42 -- amount * w // 100 is computed per opportunity, so each
        # contribution is truncated individually: 999*10//100 = 99,
        # 333*30//100 = 99, 1001*60//100 = 600.
        crm = make_crm()
        prospect = new_opp(crm, email="a@corp.io", amount=999)
        proposal = new_opp(crm, email="b@corp.io", amount=333)
        negotiation = new_opp(crm, email="c@corp.io", amount=1001)
        crm.advance(proposal, "proposal", crm.opps[proposal]["owner"])
        crm.advance(negotiation, "proposal", crm.opps[negotiation]["owner"])
        crm.advance(negotiation, "negotiation", crm.opps[negotiation]["owner"])
        self.assertEqual(
            crm.forecast(), {"open": 3, "weighted": 99 + 99 + 600, "won": 0}
        )
        self.assertEqual(crm.opps[prospect]["stage"], "prospect")

    def test_discount_changes_weighted_value(self):
        crm = make_crm()
        opp_id = new_opp(crm, amount=1000)
        crm.discount(opp_id, 10, "rep1")
        self.assertEqual(crm.forecast(), {"open": 1, "weighted": 90, "won": 0})

    def test_forecast_does_not_log(self):
        crm = make_crm()
        new_opp(crm)
        before = crm.log[:]
        crm.forecast()
        self.assertEqual(crm.log, before)


if __name__ == "__main__":
    unittest.main()
