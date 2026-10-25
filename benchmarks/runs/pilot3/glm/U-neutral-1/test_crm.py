"""Unit tests for crm.py (validation, ordering, and core flows)."""

import unittest

from crm import CRM, DuplicateLeadError


def make_crm():
    return CRM(
        [
            {"id": "r1", "role": "rep", "capacity": 2},
            {"id": "r2", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 0},
        ]
    )


class AddLeadTests(unittest.TestCase):
    def test_success_fields_and_log(self):
        crm = make_crm()
        lead_id = crm.add_lead("  Ana@Example.COM ", "  Ana  ", "web", "m1")
        self.assertEqual(lead_id, "L1")
        lead = crm.leads[lead_id]
        self.assertEqual(lead["email"], "ana@example.com")
        self.assertEqual(lead["name"], "Ana")
        self.assertEqual(lead["source"], "web")
        self.assertEqual(lead["status"], "new")
        self.assertEqual(lead["owner"], "r1")
        self.assertEqual(crm.log, [("add_lead", "L1", "m1")])

    def test_unknown_actor_first(self):
        crm = make_crm()
        with self.assertRaises(PermissionError):
            crm.add_lead("bad-email", "", "nope", "ghost")
        self.assertEqual(crm.log, [])
        self.assertEqual(crm.leads, {})

    def test_email_validation(self):
        crm = make_crm()
        bad = [
            None,
            123,
            "",
            "plain",
            "a@@b.com",
            "@b.com",
            "a@.com",
            "a@com.",
            "a@com",
            "a@b",
            "a@com.",
        ]
        for email in bad:
            with self.assertRaises(ValueError, msg=repr(email)):
                crm.add_lead(email, "n", "web", "m1")
        self.assertEqual(crm.log, [])
        self.assertEqual(crm.leads, {})

    def test_email_good_variants(self):
        crm = make_crm()
        ids = [
            crm.add_lead(e, "n", "referral", "m1")
            for e in ["a@b.c", "x.y@sub.domain.tld", "u@deep.a.b", "v@.b.c"]
        ]
        self.assertEqual(ids, ["L1", "L2", "L3", "L4"])

    def test_name_and_source_validation(self):
        crm = make_crm()
        for name in [None, 5, "", "   "]:
            with self.assertRaises(ValueError, msg=repr(name)):
                crm.add_lead("a@b.c", name, "web", "m1")
        for source in [None, "WEB", "friend", ""]:
            with self.assertRaises(ValueError, msg=repr(source)):
                crm.add_lead("a@b.c", "n", source, "m1")

    def test_duplicate_email_case_insensitive(self):
        crm = make_crm()
        crm.add_lead("ana@example.com", "Ana", "web", "m1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            crm.add_lead("  ANA@example.com ", "Ana2", "referral", "m1")
        self.assertEqual(ctx.exception.existing_id, "L1")
        self.assertEqual(len(crm.leads), 1)
        self.assertEqual(crm.log, [("add_lead", "L1", "m1")])

    def test_scoring(self):
        crm = make_crm()
        crm.add_lead("a@gmail.com", "a", "web", "m1")       # 10
        crm.add_lead("b@yahoo.com", "b", "event", "m1")     # 20
        crm.add_lead("c@corp.io", "c", "referral", "m1")    # 30 + 15
        crm.add_lead("d@outlook.com", "d", "referral", "m1")  # 30
        scores = [crm.leads["L%d" % i]["score"] for i in range(1, 5)]
        self.assertEqual(scores, [10, 20, 45, 30])

    def test_owner_lowest_load_tie_smallest_id(self):
        crm = make_crm()  # r1 cap 2, r2 cap 1, both load 0
        self.assertEqual(crm.add_lead("a@b.c", "a", "web", "m1"), "L1")
        self.assertEqual(crm.leads["L1"]["owner"], "r1")
        self.assertEqual(crm.add_lead("b@b.c", "b", "web", "m1"), "L2")
        self.assertEqual(crm.leads["L2"]["owner"], "r2")  # r1 load 1 < 2? yes but r2 load 0 < r1 load 1
        self.assertEqual(crm.add_lead("c@b.c", "c", "web", "m1"), "L3")
        self.assertEqual(crm.leads["L3"]["owner"], "r1")  # r2 full, r1 load 1 < 2

    def test_owner_none_queued_fifo(self):
        crm = CRM(
            [{"id": "r1", "role": "rep", "capacity": 1}, {"id": "m1", "role": "manager", "capacity": 0}]
        )
        self.assertEqual(crm.leads[crm.add_lead("a@b.c", "a", "web", "m1")]["owner"], "r1")
        l2 = crm.add_lead("b@b.c", "b", "web", "m1")
        l3 = crm.add_lead("c@b.c", "c", "web", "m1")
        self.assertIsNone(crm.leads[l2]["owner"])
        self.assertIsNone(crm.leads[l3]["owner"])
        self.assertEqual(crm._waiting, [l2, l3])
        # qualify+convert needs score>=30; use a referral lead instead.
        crm2 = CRM(
            [{"id": "r1", "role": "rep", "capacity": 1}, {"id": "m1", "role": "manager", "capacity": 0}]
        )
        first = crm2.add_lead("a@gmail.com", "a", "referral", "m1")  # score 30
        crm2.add_lead("b@b.c", "b", "web", "m1")
        crm2.add_lead("c@b.c", "c", "web", "m1")
        crm2.qualify(first, "m1")
        opp = crm2.convert(first, 100, "m1")
        self.assertEqual(crm2.leads[first]["status"], "converted")
        # load still 1 (the opp), queue untouched
        self.assertEqual(crm2._waiting, ["L2", "L3"])
        crm2.advance(opp, "lost", "m1")  # final stage frees r1's slot
        self.assertEqual(crm2.leads["L2"]["owner"], "r1")
        self.assertEqual(crm2.leads["L3"]["owner"], None)
        self.assertEqual(
            [e for e in crm2.log if e[0] == "assign"], [("assign", "L2", "system")]
        )

    def test_failed_add_does_not_consume_id(self):
        crm = make_crm()
        crm.add_lead("a@b.c", "a", "web", "m1")
        with self.assertRaises(ValueError):
            crm.add_lead("bad", "n", "web", "m1")
        self.assertEqual(crm.add_lead("z@b.c", "z", "web", "m1"), "L2")


class QualifyTests(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        # referral to gmail: score 30 (qualifiable), owned by r1
        self.lead = self.crm.add_lead("a@gmail.com", "a", "referral", "m1")

    def test_success_by_owner(self):
        self.crm.qualify(self.lead, "r1")
        self.assertEqual(self.crm.leads[self.lead]["status"], "qualified")
        self.assertEqual(self.crm.log[-1], ("qualify", self.lead, "r1"))

    def test_success_by_manager_not_owner(self):
        self.crm.qualify(self.lead, "m1")
        self.assertEqual(self.crm.leads[self.lead]["status"], "qualified")

    def test_unknown_lead(self):
        with self.assertRaises(ValueError):
            self.crm.qualify("L99", "m1")

    def test_non_owner_rep(self):
        with self.assertRaises(PermissionError):
            self.crm.qualify(self.lead, "r2")

    def test_wrong_status(self):
        self.crm.qualify(self.lead, "r1")
        with self.assertRaises(ValueError):
            self.crm.qualify(self.lead, "m1")

    def test_low_score(self):
        low = self.crm.add_lead("b@gmail.com", "b", "web", "m1")  # score 10
        owner = self.crm.leads[low]["owner"]
        with self.assertRaises(ValueError):
            self.crm.qualify(low, owner)
        self.assertEqual(self.crm.leads[low]["status"], "new")
        self.assertEqual(len(self.crm.log), 2)  # two add_lead entries only


class ConvertTests(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        self.lead = self.crm.add_lead("a@gmail.com", "a", "referral", "m1")
        self.crm.qualify(self.lead, "r1")

    def test_success(self):
        opp_id = self.crm.convert(self.lead, 1000, "r1")
        self.assertEqual(opp_id, "O1")
        opp = self.crm.opps[opp_id]
        self.assertEqual(
            opp,
            {
                "id": "O1",
                "lead_id": self.lead,
                "owner": "r1",
                "amount": 1000,
                "original_amount": 1000,
                "stage": "prospect",
            },
        )
        self.assertEqual(self.crm.leads[self.lead]["status"], "converted")
        self.assertEqual(self.crm.log[-1], ("convert", "O1", "r1"))

    def test_check_order_amount_before_actor(self):
        with self.assertRaises(ValueError):
            self.crm.convert(self.lead, True, "r2")  # bool amount
        with self.assertRaises(ValueError):
            self.crm.convert(self.lead, 0, "r2")
        with self.assertRaises(ValueError):
            self.crm.convert(self.lead, -5, "r2")
        with self.assertRaises(ValueError):
            self.crm.convert(self.lead, 10.0, "r2")
        # unknown actor is checked first even for unknown leads
        with self.assertRaises(PermissionError):
            self.crm.convert("L99", 100, "ghost-actor")

    def test_permission(self):
        with self.assertRaises(PermissionError):
            self.crm.convert(self.lead, 1000, "r2")
        self.crm.convert(self.lead, 1000, "m1")  # manager ok
        self.assertEqual(self.crm.log[-1], ("convert", "O1", "m1"))

    def test_status_must_be_qualified(self):
        other = self.crm.add_lead("b@gmail.com", "b", "referral", "m1")  # still new
        with self.assertRaises(ValueError):
            self.crm.convert(other, 100, "m1")
        self.assertEqual(self.crm.opps, {})
        self.assertEqual(self.crm.leads[other]["status"], "new")

    def test_counter_increments_only_on_success(self):
        with self.assertRaises(ValueError):
            self.crm.convert(self.lead, 0, "r1")
        opp1 = self.crm.convert(self.lead, 100, "r1")
        other = self.crm.add_lead("b@gmail.com", "b", "referral", "m1")
        self.crm.qualify(other, "m1")
        opp2 = self.crm.convert(other, 100, "m1")
        self.assertEqual((opp1, opp2), ("O1", "O2"))


class AdvanceTests(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        self.lead = self.crm.add_lead("a@gmail.com", "a", "referral", "m1")
        self.crm.qualify(self.lead, "r1")
        self.opp = self.crm.convert(self.lead, 40000, "r1")

    def test_full_path(self):
        for stage in ("proposal", "negotiation", "won"):
            self.crm.advance(self.opp, stage, "r1")
        self.assertEqual(self.crm.opps[self.opp]["stage"], "won")

    def test_lost_from_any_non_final(self):
        self.crm.advance(self.opp, "lost", "r1")
        self.assertEqual(self.crm.opps[self.opp]["stage"], "lost")

    def test_unknown_opp(self):
        with self.assertRaises(ValueError):
            self.crm.advance("O99", "proposal", "m1")

    def test_invalid_stage(self):
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "closed", "m1")

    def test_invalid_stage_before_permission(self):
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "bogus", "r2")

    def test_permission(self):
        with self.assertRaises(PermissionError):
            self.crm.advance(self.opp, "proposal", "r2")
        self.crm.advance(self.opp, "proposal", "m1")

    def test_cannot_advance_final(self):
        for stage in ("proposal", "negotiation", "won"):
            self.crm.advance(self.opp, stage, "r1")
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "lost", "m1")

    def test_skip_stage(self):
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "negotiation", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "won", "r1")
        self.assertEqual(self.crm.opps[self.opp]["stage"], "prospect")

    def test_big_negotiation_requires_manager(self):
        lead_big = self.crm.add_lead("b@gmail.com", "b", "referral", "m1")
        owner = self.crm.leads[lead_big]["owner"]
        self.crm.qualify(lead_big, owner)
        opp_big = self.crm.convert(lead_big, 60000, owner)
        self.crm.advance(opp_big, "proposal", owner)
        with self.assertRaises(PermissionError):
            self.crm.advance(opp_big, "negotiation", owner)
        self.crm.advance(opp_big, "negotiation", "m1")
        self.assertEqual(self.crm.opps[opp_big]["stage"], "negotiation")

    def test_small_negotiation_by_rep_ok(self):
        self.crm.advance(self.opp, "proposal", "r1")
        self.crm.advance(self.opp, "negotiation", "r1")  # 40000 <= 50000
        self.assertEqual(self.crm.opps[self.opp]["stage"], "negotiation")

    def test_big_negotiation_boundary_50000(self):
        self.crm.advance(self.opp, "proposal", "r1")
        self.crm.advance(self.opp, "negotiation", "r1")  # exactly 50000 is fine
        lead2 = self.crm.add_lead("b@gmail.com", "b", "referral", "m1")
        owner = self.crm.leads[lead2]["owner"]
        self.crm.qualify(lead2, owner)
        opp2 = self.crm.convert(lead2, 50001, owner)
        self.crm.advance(opp2, "proposal", owner)
        with self.assertRaises(PermissionError):
            self.crm.advance(opp2, "negotiation", owner)

    def test_won_frees_slot_and_assigns_queue(self):
        crm = CRM(
            [{"id": "r1", "role": "rep", "capacity": 1}, {"id": "m1", "role": "manager", "capacity": 0}]
        )
        lead = crm.add_lead("a@gmail.com", "a", "referral", "m1")
        crm.qualify(lead, "m1")
        opp = crm.convert(lead, 100, "m1")
        w1 = crm.add_lead("b@b.c", "b", "web", "m1")
        w2 = crm.add_lead("c@b.c", "c", "web", "m1")
        self.assertIsNone(crm.leads[w1]["owner"])
        crm.advance(opp, "proposal", "m1")
        crm.advance(opp, "negotiation", "m1")
        crm.advance(opp, "won", "m1")
        self.assertEqual(crm.leads[w1]["owner"], "r1")
        self.assertIsNone(crm.leads[w2]["owner"])  # capacity 1 reached again
        self.assertEqual(
            [e for e in crm.log if e[0] == "assign"], [("assign", w1, "system")]
        )

    def test_lost_also_frees_slot(self):
        crm = CRM(
            [{"id": "r1", "role": "rep", "capacity": 1}, {"id": "m1", "role": "manager", "capacity": 0}]
        )
        lead = crm.add_lead("a@gmail.com", "a", "referral", "m1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 100, "r1")
        w1 = crm.add_lead("b@b.c", "b", "web", "m1")
        crm.advance(opp, "lost", "r1")
        self.assertEqual(crm.leads[w1]["owner"], "r1")


class DiscountTests(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        self.lead = self.crm.add_lead("a@gmail.com", "a", "referral", "m1")
        self.crm.qualify(self.lead, "r1")
        self.opp = self.crm.convert(self.lead, 1000, "r1")

    def test_success(self):
        self.crm.discount(self.opp, 10, "r1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 900)
        self.assertEqual(self.crm.log[-1], ("discount", self.opp, "r1"))

    def test_pct_validation(self):
        for pct in [0, 31, -5, True, 1.5, "10", None]:
            with self.assertRaises(ValueError, msg=repr(pct)):
                self.crm.discount(self.opp, pct, "m1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 1000)

    def test_pct_validation_before_permission(self):
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp, 50, "r2")

    def test_permission_non_owner(self):
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp, 10, "r2")

    def test_final_stage(self):
        self.crm.advance(self.opp, "lost", "r1")
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp, 10, "r1")

    def test_non_manager_cap_10(self):
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp, 11, "r1")
        self.crm.discount(self.opp, 10, "r1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 900)

    def test_non_manager_cap_before_cumulative(self):
        # rep with pct 10 is allowed at step 5, then cumulative fails at 6
        crm = make_crm()
        lead = crm.add_lead("a@gmail.com", "a", "referral", "m1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 3, "r1")  # 3*90//100 = 2 -> 200 < 210
        with self.assertRaises(ValueError):
            crm.discount(opp, 10, "r1")
        self.assertEqual(crm.opps[opp]["amount"], 3)

    def test_cumulative_discount_limit(self):
        self.crm.discount(self.opp, 30, "m1")  # 700 exactly
        self.assertEqual(self.crm.opps[self.opp]["amount"], 700)
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp, 1, "m1")  # 693 -> 69300 < 70000
        self.assertEqual(self.crm.opps[self.opp]["amount"], 700)

    def test_floor_rule_blocks_tiny_amounts(self):
        crm = make_crm()
        lead = crm.add_lead("a@gmail.com", "a", "referral", "m1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 1, "r1")  # 1*99//100 = 0 -> blocked
        with self.assertRaises(ValueError):
            crm.discount(opp, 1, "r1")

    def test_successive_discounts_compound_on_amount(self):
        self.crm.discount(self.opp, 10, "r1")   # 900
        self.crm.discount(self.opp, 10, "r1")   # 810
        self.assertEqual(self.crm.opps[self.opp]["amount"], 810)
        self.assertEqual(self.crm.opps[self.opp]["original_amount"], 1000)


class TransferTests(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        self.lead = self.crm.add_lead("a@gmail.com", "a", "referral", "m1")
        self.crm.qualify(self.lead, "r1")
        self.opp = self.crm.convert(self.lead, 1000, "r1")

    def test_success(self):
        self.crm.transfer(self.opp, "r2", "m1")
        self.assertEqual(self.crm.opps[self.opp]["owner"], "r2")
        self.assertEqual(self.crm.log[-1], ("transfer", self.opp, "m1"))

    def test_only_manager(self):
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.opp, "r2", "r1")

    def test_manager_check_before_new_owner_check(self):
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.opp, "nobody", "r1")

    def test_unknown_new_owner(self):
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "r9", "m1")

    def test_manager_new_owner_rejected(self):
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "m1", "m1")

    def test_unknown_opp(self):
        with self.assertRaises(ValueError):
            self.crm.transfer("O99", "r2", "m1")

    def test_final_stage(self):
        self.crm.advance(self.opp, "lost", "r1")
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "r2", "m1")

    def test_same_owner(self):
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "r1", "m1")

    def test_new_owner_full(self):
        crm = make_crm()
        lead = crm.add_lead("a@gmail.com", "a", "referral", "m1")  # r1
        crm.qualify(lead, "r1")
        crm.convert(lead, 100, "r1")
        l2 = crm.add_lead("b@gmail.com", "b", "referral", "m1")  # r2
        crm.qualify(l2, "r2")
        opp2 = crm.convert(l2, 100, "r2")  # r2 now at capacity 1
        l3 = crm.add_lead("c@gmail.com", "c", "referral", "m1")  # r1 (load 1 < 2)
        crm.qualify(l3, "r1")
        opp3 = crm.convert(l3, 100, "r1")  # r1 load 2 = cap
        # r1 and r2 both full; transfer r1's opp to r2 must fail
        with self.assertRaises(ValueError):
            crm.transfer(opp3, "r2", "m1")
        self.assertEqual(crm.opps[opp3]["owner"], "r1")
        self.assertEqual(crm.opps[opp2]["owner"], "r2")

    def test_transfer_frees_previous_owner_slot(self):
        crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 2},
                {"id": "r2", "role": "rep", "capacity": 2},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        lead = crm.add_lead("a@gmail.com", "a", "referral", "m1")  # r1
        crm.qualify(lead, "m1")
        opp = crm.convert(lead, 100, "m1")  # r1 load 1
        w1 = crm.add_lead("b@b.c", "b", "web", "m1")   # r2 (load 0 < r1 load 1)
        w2 = crm.add_lead("c@b.c", "c", "web", "m1")   # tie load 1 -> r1
        self.assertEqual(crm.leads[w1]["owner"], "r2")
        self.assertEqual(crm.leads[w2]["owner"], "r1")
        crm.transfer(opp, "r2", "m1")  # r1 load drops to 1; queue empty
        self.assertEqual(crm.opps[opp]["owner"], "r2")
        self.assertEqual([e for e in crm.log if e[0] == "assign"], [])
        # r1 has a free slot again: the next lead goes to r1
        new_lead = crm.add_lead("d@b.c", "d", "web", "m1")
        self.assertEqual(crm.leads[new_lead]["owner"], "r1")

    def test_transfer_counts_toward_new_owner_load(self):
        crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 1},
                {"id": "r2", "role": "rep", "capacity": 1},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        lead = crm.add_lead("a@gmail.com", "a", "referral", "m1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 100, "r1")
        crm.transfer(opp, "r2", "m1")  # r1 freed (load 0), r2 now at capacity
        self.assertEqual(crm._load("r2"), 1)
        # a new lead goes to r1 (freed slot)
        w1 = crm.add_lead("b@b.c", "b", "web", "m1")
        self.assertEqual(crm.leads[w1]["owner"], "r1")
        # r1 is now at capacity: transferring back must fail
        with self.assertRaises(ValueError):
            crm.transfer(opp, "r1", "m1")
        self.assertEqual(crm.opps[opp]["owner"], "r2")


class LoadSemanticsTests(unittest.TestCase):
    def test_qualified_counts_converted_does_not(self):
        crm = CRM(
            [{"id": "r1", "role": "rep", "capacity": 2}, {"id": "m1", "role": "manager", "capacity": 0}]
        )
        lead = crm.add_lead("a@gmail.com", "a", "referral", "m1")
        self.assertEqual(crm._load("r1"), 1)
        crm.qualify(lead, "r1")
        self.assertEqual(crm._load("r1"), 1)
        opp = crm.convert(lead, 100, "r1")
        self.assertEqual(crm._load("r1"), 1)  # opp replaces lead
        crm.advance(opp, "lost", "r1")
        self.assertEqual(crm._load("r1"), 0)

    def test_lost_frees_load(self):
        crm = CRM(
            [{"id": "r1", "role": "rep", "capacity": 2}, {"id": "m1", "role": "manager", "capacity": 0}]
        )
        lead = crm.add_lead("a@gmail.com", "a", "referral", "m1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 100, "r1")
        crm.advance(opp, "lost", "r1")
        self.assertEqual(crm._load("r1"), 0)

    def test_managers_never_own_work(self):
        crm = make_crm()
        for _ in range(5):
            crm.add_lead("x%d@b.c" % _, "x", "web", "m1")
        for lead in crm.leads.values():
            self.assertIn(lead["owner"], ("r1", "r2", None))


class ForecastTests(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(make_crm().forecast(), {"open": 0, "weighted": 0, "won": 0})

    def test_weights_and_totals(self):
        crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 3},
                {"id": "r2", "role": "rep", "capacity": 2},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        l1 = crm.add_lead("a@gmail.com", "a", "referral", "m1")
        crm.qualify(l1, "m1")
        o1 = crm.convert(l1, 1000, "m1")     # prospect
        l2 = crm.add_lead("b@gmail.com", "b", "referral", "m1")
        crm.qualify(l2, "m1")
        o2 = crm.convert(l2, 2000, "m1")
        crm.advance(o2, "proposal", "m1")    # proposal
        l3 = crm.add_lead("c@gmail.com", "c", "referral", "m1")
        crm.qualify(l3, "m1")
        o3 = crm.convert(l3, 50000, "m1")
        crm.advance(o3, "proposal", "m1")
        crm.advance(o3, "negotiation", "m1")  # negotiation
        l4 = crm.add_lead("d@gmail.com", "d", "referral", "m1")
        crm.qualify(l4, "m1")
        o4 = crm.convert(l4, 400, "m1")
        crm.advance(o4, "proposal", "m1")
        crm.advance(o4, "negotiation", "m1")
        crm.advance(o4, "won", "m1")
        l5 = crm.add_lead("e@gmail.com", "e", "referral", "m1")
        crm.qualify(l5, "m1")
        o5 = crm.convert(l5, 300, "m1")
        crm.advance(o5, "lost", "m1")
        result = crm.forecast()
        # weighted: 1000*10//100 + 2000*30//100 + 50000*60//100 = 100 + 600 + 30000
        self.assertEqual(result["open"], 3)
        self.assertEqual(result["weighted"], 30700)
        self.assertEqual(result["won"], 400)

    def test_floor_per_opportunity(self):
        crm = make_crm()
        lead = crm.add_lead("a@gmail.com", "a", "referral", "m1")
        crm.qualify(lead, "r1")
        crm.convert(lead, 101, "r1")  # prospect: 101*10//100 = 10
        self.assertEqual(crm.forecast()["weighted"], 10)

    def test_no_log_entry(self):
        crm = make_crm()
        crm.forecast()
        self.assertEqual(crm.log, [])


class AtomicityTests(unittest.TestCase):
    def test_failed_advance_changes_nothing(self):
        crm = make_crm()
        lead = crm.add_lead("a@gmail.com", "a", "referral", "m1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 1000, "r1")
        before_log = list(crm.log)
        with self.assertRaises(ValueError):
            crm.advance(opp, "won", "r1")  # skipping stages
        self.assertEqual(crm.opps[opp]["stage"], "prospect")
        self.assertEqual(crm.log, before_log)

    def test_failed_transfer_changes_nothing(self):
        crm = make_crm()
        lead = crm.add_lead("a@gmail.com", "a", "referral", "m1")
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 1000, "r1")
        before_log = list(crm.log)
        with self.assertRaises(PermissionError):
            crm.transfer(opp, "r2", "r1")
        self.assertEqual(crm.opps[opp]["owner"], "r1")
        self.assertEqual(crm.log, before_log)

    def test_log_tuple_shape(self):
        crm = make_crm()
        crm.add_lead("a@b.c", "a", "web", "m1")
        self.assertTrue(all(isinstance(e, tuple) and len(e) == 3 for e in crm.log))


class DuplicateLeadErrorClassTests(unittest.TestCase):
    def test_is_exception_with_existing_id(self):
        err = DuplicateLeadError("L7")
        self.assertIsInstance(err, Exception)
        self.assertEqual(err.existing_id, "L7")


if __name__ == "__main__":
    unittest.main()
