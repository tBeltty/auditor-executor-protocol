import unittest

from crm import CRM, DuplicateLeadError


def crm_with(r1_cap=5, r2_cap=5):
    return CRM([
        {"id": "r1", "role": "rep", "capacity": r1_cap},
        {"id": "r2", "role": "rep", "capacity": r2_cap},
        {"id": "m1", "role": "manager", "capacity": 0},
    ])


def make_crm():
    return crm_with(2, 1)


def make_solo():
    return crm_with(10, 0)


def make_small():
    return crm_with(1, 1)


def new_opp(crm, amount=1000, email="a@corp.com", source="referral", owner="r1"):
    lead_id = crm.add_lead(email, "Lead", source, owner)
    crm.qualify(lead_id, owner)
    return crm.convert(lead_id, amount, owner)


class TestAddLead(unittest.TestCase):
    def test_basic_creation(self):
        crm = make_crm()
        lead_id = crm.add_lead("  John@Example.COM ", "  John Doe  ", "web", "r1")
        self.assertEqual(lead_id, "L1")
        lead = crm.leads[lead_id]
        self.assertEqual(lead["email"], "john@example.com")
        self.assertEqual(lead["name"], "John Doe")
        self.assertEqual(lead["source"], "web")
        self.assertEqual(lead["status"], "new")
        self.assertEqual(lead["score"], 25)
        self.assertEqual(lead["owner"], "r1")
        self.assertEqual(crm.log, [("add_lead", "L1", "r1")])

    def test_score_by_source(self):
        crm = make_solo()
        a = crm.add_lead("a@gmail.com", "A", "web", "r1")
        b = crm.add_lead("b@gmail.com", "B", "referral", "r1")
        c = crm.add_lead("c@gmail.com", "C", "event", "r1")
        self.assertEqual(crm.leads[a]["score"], 10)
        self.assertEqual(crm.leads[b]["score"], 30)
        self.assertEqual(crm.leads[c]["score"], 20)

    def test_corporate_domain_bonus(self):
        crm = make_solo()
        lead_id = crm.add_lead("x@corp.com", "X", "web", "r1")
        self.assertEqual(crm.leads[lead_id]["score"], 25)

    def test_invalid_emails(self):
        crm = make_solo()
        bad = [
            123,
            None,
            "plain",
            "a@@b.com",
            "a@b@c.com",
            "@b.com",
            "a@b",
            "a@.com",
            "a@b.",
            "a@.b.",
        ]
        for email in bad:
            with self.assertRaises(ValueError, msg=repr(email)):
                crm.add_lead(email, "Name", "web", "r1")
        self.assertEqual(crm.log, [])
        self.assertEqual(crm.leads, {})

    def test_invalid_name(self):
        crm = make_solo()
        for name in ("", "   ", 5, None, ["x"]):
            with self.assertRaises(ValueError, msg=repr(name)):
                crm.add_lead("a@b.com", name, "web", "r1")
        self.assertEqual(crm.leads, {})

    def test_invalid_source(self):
        crm = make_solo()
        for source in ("phone", "", None, 1):
            with self.assertRaises(ValueError):
                crm.add_lead("a@b.com", "Name", source, "r1")

    def test_unknown_actor_checked_first(self):
        crm = make_solo()
        with self.assertRaises(PermissionError):
            crm.add_lead("bad-email", "", "nope", "ghost")
        self.assertEqual(crm.log, [])

    def test_duplicate_lead(self):
        crm = make_solo()
        first = crm.add_lead("a@b.com", "A", "web", "r1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            crm.add_lead(" A@B.COM ", "A2", "web", "r1")
        self.assertEqual(ctx.exception.existing_id, first)
        self.assertEqual(len(crm.leads), 1)
        self.assertEqual(crm.log, [("add_lead", first, "r1")])

    def test_ids_are_sequential_and_not_consumed_by_failures(self):
        crm = make_solo()
        with self.assertRaises(ValueError):
            crm.add_lead("bad", "A", "web", "r1")
        a = crm.add_lead("a@b.com", "A", "web", "r1")
        with self.assertRaises(DuplicateLeadError):
            crm.add_lead("a@b.com", "A", "web", "r1")
        b = crm.add_lead("b@b.com", "B", "web", "r1")
        self.assertEqual((a, b), ("L1", "L2"))

    def test_owner_assignment_ties_go_to_smallest_id(self):
        crm = make_crm()
        a = crm.add_lead("a@b.com", "A", "web", "r1")
        b = crm.add_lead("b@b.com", "B", "web", "r1")
        c = crm.add_lead("c@b.com", "C", "web", "r1")
        self.assertEqual(crm.leads[a]["owner"], "r1")
        self.assertEqual(crm.leads[b]["owner"], "r2")
        self.assertEqual(crm.leads[c]["owner"], "r1")

    def test_manager_never_owns(self):
        crm = crm_with(0, 0)
        lead_id = crm.add_lead("a@b.com", "A", "web", "m1")
        self.assertIsNone(crm.leads[lead_id]["owner"])

    def test_queue_when_all_full(self):
        crm = make_small()
        crm.add_lead("a@b.com", "A", "web", "r1")
        crm.add_lead("b@b.com", "B", "web", "r1")
        crm.add_lead("c@b.com", "C", "web", "r1")
        crm.add_lead("d@b.com", "D", "web", "r1")
        self.assertIsNone(crm.leads["L3"]["owner"])
        self.assertIsNone(crm.leads["L4"]["owner"])
        self.assertEqual(crm.load("r1"), 1)
        self.assertEqual(crm.load("r2"), 1)
        self.assertEqual(crm.load("m1"), 0)


class TestQualify(unittest.TestCase):
    def test_qualify_success(self):
        crm = make_solo()
        lead_id = crm.add_lead("a@corp.com", "A", "referral", "r1")
        crm.qualify(lead_id, "r1")
        self.assertEqual(crm.leads[lead_id]["status"], "qualified")
        self.assertEqual(crm.log[-1], ("qualify", lead_id, "r1"))

    def test_manager_can_qualify(self):
        crm = make_solo()
        lead_id = crm.add_lead("a@corp.com", "A", "referral", "r1")
        crm.qualify(lead_id, "m1")
        self.assertEqual(crm.leads[lead_id]["status"], "qualified")

    def test_unknown_lead(self):
        crm = make_solo()
        with self.assertRaises(ValueError):
            crm.qualify("L99", "r1")

    def test_not_owner_nor_manager(self):
        crm = make_solo()
        lead_id = crm.add_lead("a@corp.com", "A", "referral", "r1")
        with self.assertRaises(PermissionError):
            crm.qualify(lead_id, "r2")

    def test_low_score_rejected(self):
        crm = make_solo()
        lead_id = crm.add_lead("a@gmail.com", "A", "web", "r1")
        self.assertEqual(crm.leads[lead_id]["score"], 10)
        with self.assertRaises(ValueError):
            crm.qualify(lead_id, "r1")
        self.assertEqual(crm.leads[lead_id]["status"], "new")

    def test_already_qualified_rejected(self):
        crm = make_solo()
        lead_id = crm.add_lead("a@corp.com", "A", "referral", "r1")
        crm.qualify(lead_id, "r1")
        with self.assertRaises(ValueError):
            crm.qualify(lead_id, "r1")

    def test_converted_lead_cannot_qualify(self):
        crm = make_solo()
        lead_id = crm.add_lead("a@corp.com", "A", "referral", "r1")
        crm.qualify(lead_id, "r1")
        crm.convert(lead_id, 1000, "r1")
        with self.assertRaises(ValueError):
            crm.qualify(lead_id, "r1")

    def test_failure_leaves_no_log(self):
        crm = make_solo()
        lead_id = crm.add_lead("a@gmail.com", "A", "web", "r1")
        before = list(crm.log)
        with self.assertRaises(ValueError):
            crm.qualify(lead_id, "r1")
        self.assertEqual(crm.log, before)


class TestConvert(unittest.TestCase):
    def test_convert_success(self):
        crm = make_solo()
        lead_id = crm.add_lead("a@corp.com", "A", "referral", "r1")
        crm.qualify(lead_id, "r1")
        opp_id = crm.convert(lead_id, 1000, "r1")
        self.assertEqual(opp_id, "O1")
        self.assertEqual(crm.opps[opp_id], {
            "id": "O1",
            "lead_id": lead_id,
            "owner": "r1",
            "amount": 1000,
            "original_amount": 1000,
            "stage": "prospect",
        })
        self.assertEqual(crm.leads[lead_id]["status"], "converted")
        self.assertEqual(crm.log[-1], ("convert", "O1", "r1"))

    def test_opportunity_ids_sequential(self):
        crm = make_solo()
        a = crm.add_lead("a@corp.com", "A", "referral", "r1")
        b = crm.add_lead("b@corp.com", "B", "referral", "r1")
        crm.qualify(a, "r1")
        crm.qualify(b, "r1")
        self.assertEqual(crm.convert(a, 100, "r1"), "O1")
        with self.assertRaises(ValueError):
            crm.convert(a, 100, "r1")
        self.assertEqual(crm.convert(b, 200, "r1"), "O2")

    def test_amount_validation(self):
        crm = make_solo()
        lead_id = crm.add_lead("a@corp.com", "A", "referral", "r1")
        crm.qualify(lead_id, "r1")
        for amount in (0, -1, 1.5, "10", True, False, None):
            with self.assertRaises(ValueError, msg=repr(amount)):
                crm.convert(lead_id, amount, "r1")
        self.assertEqual(crm.opps, {})

    def test_permission(self):
        crm = make_solo()
        lead_id = crm.add_lead("a@corp.com", "A", "referral", "r1")
        crm.qualify(lead_id, "r1")
        with self.assertRaises(PermissionError):
            crm.convert(lead_id, 100, "r2")

    def test_manager_can_convert(self):
        crm = make_solo()
        lead_id = crm.add_lead("a@corp.com", "A", "referral", "r1")
        crm.qualify(lead_id, "r1")
        opp_id = crm.convert(lead_id, 100, "m1")
        self.assertEqual(crm.opps[opp_id]["owner"], "r1")

    def test_must_be_qualified(self):
        crm = make_solo()
        lead_id = crm.add_lead("a@corp.com", "A", "referral", "r1")
        with self.assertRaises(ValueError):
            crm.convert(lead_id, 100, "r1")

    def test_unknown_lead(self):
        crm = make_solo()
        with self.assertRaises(ValueError):
            crm.convert("L9", 100, "r1")

    def test_ownerless_lead_rejected(self):
        crm = make_small()
        crm.add_lead("a@b.com", "A", "referral", "r1")
        crm.add_lead("b@b.com", "B", "referral", "r1")
        queued = crm.add_lead("c@b.com", "C", "referral", "r1")
        self.assertIsNone(crm.leads[queued]["owner"])
        crm.qualify(queued, "m1")
        with self.assertRaises(ValueError):
            crm.convert(queued, 100, "m1")
        self.assertEqual(crm.opps, {})


class TestAdvance(unittest.TestCase):
    def test_happy_path(self):
        crm = make_solo()
        opp_id = new_opp(crm)
        crm.advance(opp_id, "proposal", "r1")
        self.assertEqual(crm.opps[opp_id]["stage"], "proposal")
        crm.advance(opp_id, "negotiation", "r1")
        self.assertEqual(crm.opps[opp_id]["stage"], "negotiation")
        crm.advance(opp_id, "won", "r1")
        self.assertEqual(crm.opps[opp_id]["stage"], "won")
        self.assertEqual(crm.log[-3:], [
            ("advance", opp_id, "r1"),
            ("advance", opp_id, "r1"),
            ("advance", opp_id, "r1"),
        ])

    def test_skip_stage_rejected(self):
        crm = make_solo()
        opp_id = new_opp(crm)
        with self.assertRaises(ValueError):
            crm.advance(opp_id, "negotiation", "r1")
        with self.assertRaises(ValueError):
            crm.advance(opp_id, "won", "r1")

    def test_backwards_rejected(self):
        crm = make_solo()
        opp_id = new_opp(crm)
        crm.advance(opp_id, "proposal", "r1")
        with self.assertRaises(ValueError):
            crm.advance(opp_id, "prospect", "r1")

    def test_lost_from_any_open_stage(self):
        for moves in ([], ["proposal"], ["proposal", "negotiation"]):
            crm = make_solo()
            opp_id = new_opp(crm)
            for move in moves:
                crm.advance(opp_id, move, "r1")
            crm.advance(opp_id, "lost", "r1")
            self.assertEqual(crm.opps[opp_id]["stage"], "lost")

    def test_final_stage_cannot_advance(self):
        crm = make_solo()
        opp_id = new_opp(crm)
        crm.advance(opp_id, "lost", "r1")
        with self.assertRaises(ValueError):
            crm.advance(opp_id, "proposal", "r1")

    def test_invalid_stage_name(self):
        crm = make_solo()
        opp_id = new_opp(crm)
        for stage in ("", "closed", None, 5, "WON"):
            with self.assertRaises(ValueError):
                crm.advance(opp_id, stage, "r1")

    def test_unknown_opp(self):
        crm = make_solo()
        with self.assertRaises(ValueError):
            crm.advance("O9", "proposal", "r1")

    def test_permission(self):
        crm = make_solo()
        opp_id = new_opp(crm)
        with self.assertRaises(PermissionError):
            crm.advance(opp_id, "proposal", "r2")
        crm.advance(opp_id, "proposal", "m1")
        self.assertEqual(crm.opps[opp_id]["stage"], "proposal")

    def test_large_deal_needs_manager_for_negotiation(self):
        crm = make_solo()
        opp_id = new_opp(crm, amount=50001)
        crm.advance(opp_id, "proposal", "r1")
        with self.assertRaises(PermissionError):
            crm.advance(opp_id, "negotiation", "r1")
        self.assertEqual(crm.opps[opp_id]["stage"], "proposal")
        crm.advance(opp_id, "negotiation", "m1")
        self.assertEqual(crm.opps[opp_id]["stage"], "negotiation")

    def test_exactly_50000_does_not_need_manager(self):
        crm = make_solo()
        opp_id = new_opp(crm, amount=50000)
        crm.advance(opp_id, "proposal", "r1")
        crm.advance(opp_id, "negotiation", "r1")
        self.assertEqual(crm.opps[opp_id]["stage"], "negotiation")

    def test_won_frees_slot_and_assigns_waiting_lead(self):
        crm = make_small()
        a = crm.add_lead("a@corp.com", "A", "referral", "r1")
        crm.add_lead("b@corp.com", "B", "referral", "r1")
        c = crm.add_lead("c@corp.com", "C", "referral", "r1")
        d = crm.add_lead("d@corp.com", "D", "referral", "r1")
        self.assertIsNone(crm.leads[c]["owner"])
        crm.qualify(a, "r1")
        opp_id = crm.convert(a, 1000, "r1")
        self.assertIsNone(crm.leads[c]["owner"])
        crm.advance(opp_id, "proposal", "r1")
        crm.advance(opp_id, "negotiation", "r1")
        crm.advance(opp_id, "won", "r1")
        self.assertEqual(crm.leads[c]["owner"], "r1")
        self.assertIsNone(crm.leads[d]["owner"])
        self.assertEqual(crm.log[-2:], [("advance", opp_id, "r1"), ("assign", c, "system")])

    def test_lost_also_frees_slot(self):
        crm = make_small()
        a = crm.add_lead("a@corp.com", "A", "referral", "r1")
        crm.add_lead("b@corp.com", "B", "referral", "r1")
        c = crm.add_lead("c@corp.com", "C", "referral", "r1")
        crm.qualify(a, "r1")
        opp_id = crm.convert(a, 1000, "r1")
        crm.advance(opp_id, "lost", "r1")
        self.assertEqual(crm.leads[c]["owner"], "r1")
        self.assertEqual(crm.log[-1], ("assign", c, "system"))

    def test_non_final_advance_does_not_assign(self):
        crm = make_small()
        a = crm.add_lead("a@corp.com", "A", "referral", "r1")
        crm.add_lead("b@corp.com", "B", "referral", "r1")
        c = crm.add_lead("c@corp.com", "C", "referral", "r1")
        crm.qualify(a, "r1")
        opp_id = crm.convert(a, 1000, "r1")
        crm.advance(opp_id, "proposal", "r1")
        self.assertIsNone(crm.leads[c]["owner"])

    def test_failed_advance_changes_nothing(self):
        crm = make_solo()
        opp_id = new_opp(crm)
        before_log = list(crm.log)
        with self.assertRaises(ValueError):
            crm.advance(opp_id, "won", "r1")
        self.assertEqual(crm.opps[opp_id]["stage"], "prospect")
        self.assertEqual(crm.log, before_log)

    def test_load_accounting(self):
        crm = make_solo()
        a = crm.add_lead("a@corp.com", "A", "referral", "r1")
        self.assertEqual(crm.load("r1"), 1)
        crm.qualify(a, "r1")
        self.assertEqual(crm.load("r1"), 1)
        opp_id = crm.convert(a, 1000, "r1")
        self.assertEqual(crm.load("r1"), 1)
        crm.advance(opp_id, "lost", "r1")
        self.assertEqual(crm.load("r1"), 0)


class TestDiscount(unittest.TestCase):
    def test_discount_success(self):
        crm = make_solo()
        opp_id = new_opp(crm, 1000)
        crm.discount(opp_id, 10, "r1")
        self.assertEqual(crm.opps[opp_id]["amount"], 900)
        self.assertEqual(crm.opps[opp_id]["original_amount"], 1000)
        self.assertEqual(crm.log[-1], ("discount", opp_id, "r1"))

    def test_invalid_pct(self):
        crm = make_solo()
        opp_id = new_opp(crm)
        for pct in (0, 31, -5, 10.0, "10", True):
            with self.assertRaises(ValueError, msg=repr(pct)):
                crm.discount(opp_id, pct, "r1")

    def test_rep_limited_to_ten(self):
        crm = make_solo()
        opp_id = new_opp(crm)
        with self.assertRaises(PermissionError):
            crm.discount(opp_id, 11, "r1")
        self.assertEqual(crm.opps[opp_id]["amount"], 1000)

    def test_manager_can_discount_thirty(self):
        crm = make_solo()
        opp_id = new_opp(crm, 1000)
        crm.discount(opp_id, 30, "m1")
        self.assertEqual(crm.opps[opp_id]["amount"], 700)

    def test_cumulative_cap(self):
        crm = make_solo()
        opp_id = new_opp(crm, 1000)
        crm.discount(opp_id, 20, "m1")
        self.assertEqual(crm.opps[opp_id]["amount"], 800)
        with self.assertRaises(ValueError):
            crm.discount(opp_id, 20, "m1")  # 640 would exceed 30% cumulative
        crm.discount(opp_id, 12, "m1")
        self.assertEqual(crm.opps[opp_id]["amount"], 704)
        with self.assertRaises(ValueError):
            crm.discount(opp_id, 1, "m1")  # 696 < 700 floor
        self.assertEqual(crm.opps[opp_id]["amount"], 704)

    def test_cap_uses_floor_arithmetic(self):
        crm = make_solo()
        opp_id = new_opp(crm, 999)
        # 999 * 70 // 100 == 699, and 69900 < 69930, so 30% is rejected.
        with self.assertRaises(ValueError):
            crm.discount(opp_id, 30, "m1")
        self.assertEqual(crm.opps[opp_id]["amount"], 999)
        crm.discount(opp_id, 29, "m1")
        self.assertEqual(crm.opps[opp_id]["amount"], 709)
        self.assertTrue(crm.opps[opp_id]["amount"] * 100 >= 999 * 70)

    def test_final_stage_rejected(self):
        crm = make_solo()
        opp_id = new_opp(crm)
        crm.advance(opp_id, "lost", "r1")
        with self.assertRaises(ValueError):
            crm.discount(opp_id, 5, "m1")

    def test_permission(self):
        crm = make_solo()
        opp_id = new_opp(crm)
        with self.assertRaises(PermissionError):
            crm.discount(opp_id, 5, "r2")

    def test_unknown_opp(self):
        crm = make_solo()
        with self.assertRaises(ValueError):
            crm.discount("O7", 5, "r1")

    def test_pct_checked_before_permission(self):
        crm = make_solo()
        opp_id = new_opp(crm)
        with self.assertRaises(ValueError):
            crm.discount(opp_id, 50, "r2")


class TestTransfer(unittest.TestCase):
    def test_transfer_success(self):
        crm = crm_with(5, 1)
        opp_id = new_opp(crm)
        crm.transfer(opp_id, "r2", "m1")
        self.assertEqual(crm.opps[opp_id]["owner"], "r2")
        self.assertEqual(crm.log[-1], ("transfer", opp_id, "m1"))
        self.assertEqual(crm.load("r1"), 0)
        self.assertEqual(crm.load("r2"), 1)

    def test_only_manager(self):
        crm = crm_with(5, 5)
        opp_id = new_opp(crm)
        with self.assertRaises(PermissionError):
            crm.transfer(opp_id, "r2", "r1")

    def test_new_owner_must_be_rep(self):
        crm = crm_with(5, 5)
        opp_id = new_opp(crm)
        for target in ("m1", "ghost"):
            with self.assertRaises(ValueError, msg=target):
                crm.transfer(opp_id, target, "m1")

    def test_same_owner_rejected(self):
        crm = crm_with(5, 5)
        opp_id = new_opp(crm)
        with self.assertRaises(ValueError):
            crm.transfer(opp_id, "r1", "m1")

    def test_final_stage_rejected(self):
        crm = crm_with(5, 5)
        opp_id = new_opp(crm)
        crm.advance(opp_id, "lost", "r1")
        with self.assertRaises(ValueError):
            crm.transfer(opp_id, "r2", "m1")

    def test_capacity_required(self):
        crm = crm_with(2, 1)
        crm.add_lead("y@corp.com", "Y", "web", "r1")  # r1
        crm.add_lead("z@corp.com", "Z", "web", "r1")  # r2 (now full)
        self.assertEqual(crm.load("r2"), 1)
        opp_id = new_opp(crm, email="a@corp.com")  # r1, which has spare capacity
        with self.assertRaises(ValueError):
            crm.transfer(opp_id, "r2", "m1")

    def test_unknown_opp(self):
        crm = crm_with(5, 5)
        with self.assertRaises(ValueError):
            crm.transfer("O5", "r2", "m1")

    def test_transfer_frees_previous_owner(self):
        crm = crm_with(1, 1)
        opp_id = new_opp(crm)
        self.assertEqual(crm.load("r1"), 1)
        crm.transfer(opp_id, "r2", "m1")
        lead_id = crm.add_lead("n@corp.com", "N", "web", "r1")
        self.assertEqual(crm.leads[lead_id]["owner"], "r1")

    def test_transfer_moves_load_to_new_owner(self):
        crm = crm_with(5, 5)
        opp_id = new_opp(crm)
        crm.transfer(opp_id, "r2", "m1")
        self.assertEqual(crm.load("r2"), 1)
        # r1 is now free and receives the next lead.
        lead_id = crm.add_lead("c@corp.com", "C", "web", "r1")
        self.assertEqual(crm.leads[lead_id]["owner"], "r1")


class TestForecast(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(make_crm().forecast(), {"open": 0, "weighted": 0, "won": 0})

    def test_weighted(self):
        crm = make_solo()
        a = new_opp(crm, 1000, email="a@corp.com")
        b = new_opp(crm, 1000, email="b@corp.com")
        c = new_opp(crm, 1000, email="c@corp.com")
        d = new_opp(crm, 1000, email="d@corp.com")
        crm.advance(b, "proposal", "r1")
        crm.advance(c, "proposal", "r1")
        crm.advance(c, "negotiation", "r1")
        crm.advance(d, "proposal", "r1")
        crm.advance(d, "negotiation", "r1")
        crm.advance(d, "won", "r1")
        self.assertEqual(crm.forecast(), {
            "open": 3,
            "weighted": 100 + 300 + 600,
            "won": 1000,
        })

    def test_forecast_uses_current_amount_and_logs_nothing(self):
        crm = make_solo()
        opp_id = new_opp(crm, 1000)
        crm.discount(opp_id, 10, "r1")
        before = list(crm.log)
        self.assertEqual(crm.forecast(), {"open": 1, "weighted": 90, "won": 0})
        self.assertEqual(crm.log, before)

    def test_lost_not_counted(self):
        crm = make_solo()
        opp_id = new_opp(crm, 5000)
        crm.advance(opp_id, "lost", "r1")
        self.assertEqual(crm.forecast(), {"open": 0, "weighted": 0, "won": 0})


class TestLoggingAndErrors(unittest.TestCase):
    def test_unknown_actor_in_every_method(self):
        crm = make_solo()
        lead_id = crm.add_lead("a@corp.com", "A", "referral", "r1")
        crm.qualify(lead_id, "r1")
        opp_id = crm.convert(lead_id, 1000, "r1")
        with self.assertRaises(PermissionError):
            crm.qualify(lead_id, "nobody")
        with self.assertRaises(PermissionError):
            crm.convert(lead_id, 10, "nobody")
        with self.assertRaises(PermissionError):
            crm.advance(opp_id, "proposal", "nobody")
        with self.assertRaises(PermissionError):
            crm.discount(opp_id, 5, "nobody")
        with self.assertRaises(PermissionError):
            crm.transfer(opp_id, "r2", "nobody")
        self.assertEqual(len(crm.log), 3)

    def test_no_partial_state_after_failed_methods(self):
        crm = make_small()
        a = crm.add_lead("a@corp.com", "A", "referral", "r1")
        crm.add_lead("b@corp.com", "B", "referral", "r1")
        crm.qualify(a, "r1")
        opp_id = crm.convert(a, 40000, "r1")
        crm.add_lead("c@corp.com", "C", "web", "r1")
        before_log = list(crm.log)
        before_opp = dict(crm.opps[opp_id])
        before_lead = dict(crm.leads["L3"])
        with self.assertRaises(PermissionError):
            crm.transfer(opp_id, "r2", "r1")
        with self.assertRaises(ValueError):
            crm.discount(opp_id, 40, "m1")
        with self.assertRaises(ValueError):
            crm.advance(opp_id, "won", "r1")
        self.assertEqual(crm.log, before_log)
        self.assertEqual(crm.opps[opp_id], before_opp)
        self.assertEqual(crm.leads["L3"], before_lead)

    def test_failed_duplicate_does_not_change_state(self):
        crm = make_solo()
        crm.add_lead("a@corp.com", "A", "referral", "r1")
        before = (dict(crm.leads), list(crm.log))
        with self.assertRaises(DuplicateLeadError):
            crm.add_lead("A@CORP.COM", "B", "web", "r1")
        self.assertEqual(dict(crm.leads), before[0])
        self.assertEqual(crm.log, before[1])


class TestSpecEdgeCases(unittest.TestCase):
    def test_tie_break_uses_smallest_id_regardless_of_rep_order(self):
        crm = CRM([
            {"id": "r2", "role": "rep", "capacity": 2},
            {"id": "r1", "role": "rep", "capacity": 2},
        ])
        lead_id = crm.add_lead("a@b.com", "A", "web", "r2")
        self.assertEqual(crm.leads[lead_id]["owner"], "r1")

    def test_free_domain_scoring_uses_normalized_domain(self):
        crm = make_solo()
        lead_id = crm.add_lead("A@GMAIL.COM", "A", "web", "r1")
        self.assertEqual(crm.leads[lead_id]["score"], 10)

    def test_score_of_exactly_thirty_can_qualify(self):
        crm = make_solo()
        lead_id = crm.add_lead("a@gmail.com", "A", "referral", "r1")
        self.assertEqual(crm.leads[lead_id]["score"], 30)
        crm.qualify(lead_id, "r1")
        self.assertEqual(crm.leads[lead_id]["status"], "qualified")

    def test_actor_is_validated_before_entity_lookup(self):
        crm = make_solo()
        with self.assertRaises(PermissionError):
            crm.qualify("L404", "ghost")
        with self.assertRaises(PermissionError):
            crm.convert("L404", 10, "ghost")
        with self.assertRaises(PermissionError):
            crm.advance("O404", "proposal", "ghost")
        with self.assertRaises(PermissionError):
            crm.discount("O404", 5, "ghost")
        with self.assertRaises(PermissionError):
            crm.transfer("O404", "r2", "ghost")

    def test_unhashable_actor_is_permission_error(self):
        crm = make_solo()
        lead_id = crm.add_lead("a@corp.com", "A", "referral", "r1")
        crm.qualify(lead_id, "r1")
        opp_id = crm.convert(lead_id, 100, "r1")
        calls = [
            lambda: crm.add_lead("b@b.com", "B", "web", []),
            lambda: crm.qualify(lead_id, []),
            lambda: crm.convert(lead_id, 10, []),
            lambda: crm.advance(opp_id, "proposal", []),
            lambda: crm.discount(opp_id, 5, []),
            lambda: crm.transfer(opp_id, "r2", []),
        ]
        for call in calls:
            with self.assertRaises(PermissionError):
                call()
        self.assertEqual(crm.log[-1], ("convert", opp_id, "r1"))

    def test_unhashable_lead_and_opp_ids_are_value_errors(self):
        crm = make_solo()
        for call in (
            lambda: crm.qualify([], "r1"),
            lambda: crm.convert({}, 10, "r1"),
            lambda: crm.advance([], "proposal", "r1"),
            lambda: crm.discount({}, 5, "r1"),
        ):
            with self.assertRaises(ValueError):
                call()

    def test_unhashable_new_owner_is_value_error(self):
        crm = make_solo()
        opp_id = new_opp(crm)
        with self.assertRaises(ValueError):
            crm.transfer(opp_id, [], "m1")

    def test_source_checked_before_duplicate_email(self):
        crm = make_solo()
        crm.add_lead("a@corp.com", "A", "web", "r1")
        with self.assertRaises(ValueError) as ctx:
            crm.add_lead("a@corp.com", "B", "phone", "r1")
        self.assertNotIsInstance(ctx.exception, DuplicateLeadError)

    def test_convert_amount_checked_before_permission(self):
        crm = make_solo()
        lead_id = crm.add_lead("a@corp.com", "A", "referral", "r1")
        crm.qualify(lead_id, "r1")
        with self.assertRaises(ValueError):
            crm.convert(lead_id, 0, "r2")
        self.assertEqual(crm.opps, {})

    def test_advance_stage_checked_before_permission(self):
        crm = make_solo()
        opp_id = new_opp(crm)
        with self.assertRaises(ValueError):
            crm.advance(opp_id, "bogus", "r2")
        self.assertEqual(crm.opps[opp_id]["stage"], "prospect")

    def test_discount_permission_checked_before_final_stage(self):
        crm = make_solo()
        opp_id = new_opp(crm)
        crm.advance(opp_id, "lost", "r1")
        with self.assertRaises(PermissionError):
            crm.discount(opp_id, 5, "r2")

    def test_transfer_manager_checked_before_target(self):
        crm = crm_with(5, 5)
        opp_id = new_opp(crm)
        with self.assertRaises(PermissionError):
            crm.transfer(opp_id, "ghost", "r1")

    def test_lost_assigns_waiting_leads_in_fifo_order_up_to_capacity(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 3},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        ids = [crm.add_lead("%d@corp.com" % i, "N", "referral", "r1") for i in range(5)]
        self.assertEqual(
            [crm.leads[i]["owner"] for i in ids],
            ["r1", "r1", "r1", None, None],
        )
        crm.qualify(ids[0], "r1")
        opp_id = crm.convert(ids[0], 100, "r1")
        crm.advance(opp_id, "lost", "r1")
        self.assertEqual(crm.leads[ids[3]]["owner"], "r1")
        self.assertIsNone(crm.leads[ids[4]]["owner"])
        self.assertEqual(crm.log[-2:], [
            ("advance", opp_id, "r1"),
            ("assign", ids[3], "system"),
        ])
        self.assertEqual(crm.leads[ids[3]]["status"], "new")
        self.assertEqual(crm.leads[ids[3]]["score"], 45)

    def test_won_assigns_waiting_leads_up_to_capacity(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 3},
            {"id": "m1", "role": "manager", "capacity": 0},
        ])
        ids = [crm.add_lead("%d@corp.com" % i, "N", "referral", "r1") for i in range(4)]
        crm.qualify(ids[0], "r1")
        opp_id = crm.convert(ids[0], 100, "r1")
        crm.advance(opp_id, "proposal", "r1")
        crm.advance(opp_id, "negotiation", "r1")
        crm.advance(opp_id, "won", "r1")
        self.assertEqual(crm.leads[ids[3]]["owner"], "r1")
        self.assertEqual(crm.log[-2:], [
            ("advance", opp_id, "r1"),
            ("assign", ids[3], "system"),
        ])
        self.assertEqual(crm.forecast()["won"], 100)

    def test_manager_can_close_a_large_deal(self):
        crm = make_solo()
        opp_id = new_opp(crm, amount=90000)
        crm.advance(opp_id, "proposal", "r1")
        crm.advance(opp_id, "negotiation", "m1")
        crm.advance(opp_id, "won", "r1")
        self.assertEqual(crm.opps[opp_id]["stage"], "won")
        self.assertEqual(crm.forecast()["won"], 90000)

    def test_forecast_floors_weighted_amount_per_opportunity(self):
        crm = make_solo()
        new_opp(crm, 999, email="a@corp.com")
        self.assertEqual(crm.forecast()["weighted"], 99)

    def test_manager_threshold_uses_current_amount_after_discount(self):
        crm = make_solo()
        opp_id = new_opp(crm, amount=60000)
        crm.discount(opp_id, 30, "m1")
        self.assertEqual(crm.opps[opp_id]["amount"], 42000)
        crm.advance(opp_id, "proposal", "r1")
        crm.advance(opp_id, "negotiation", "r1")
        self.assertEqual(crm.opps[opp_id]["stage"], "negotiation")

    def test_transfer_capacity_counts_open_opportunities(self):
        crm = crm_with(5, 1)
        first = new_opp(crm, email="a@corp.com")  # r1
        second = new_opp(crm, email="b@corp.com", owner="m1")  # r2
        self.assertEqual(crm.opps[second]["owner"], "r2")
        self.assertEqual(crm.load("r2"), 1)
        with self.assertRaises(ValueError):
            crm.transfer(first, "r2", "m1")  # r2 is full because of the open opp
        crm.advance(second, "lost", "r2")
        crm.transfer(first, "r2", "m1")
        self.assertEqual(crm.opps[first]["owner"], "r2")


if __name__ == "__main__":
    unittest.main()
