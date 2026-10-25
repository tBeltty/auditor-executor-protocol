import unittest

from crm import CRM, DuplicateLeadError


def crm_with(*reps):
    return CRM(list(reps))


def rep(rid, capacity=5):
    return {"id": rid, "role": "rep", "capacity": capacity}


def manager(rid, capacity=0):
    return {"id": rid, "role": "manager", "capacity": capacity}


_EMAIL_SEQ = [0]


def add(crm, email=None, name="Lead", source="referral", actor="A"):
    if email is None:
        _EMAIL_SEQ[0] += 1
        email = "lead%d@corp.com" % _EMAIL_SEQ[0]
    return crm.add_lead(email, name, source, actor)


def qualified_opp(crm, amount=10000, actor="A"):
    """Create Lead -> qualify -> convert, returning the opportunity id."""
    lead_id = add(crm, actor="A")
    crm.qualify(lead_id, actor)
    return crm.convert(lead_id, amount, actor)


class TestEmailNameSourceValidation(unittest.TestCase):
    def setUp(self):
        self.crm = crm_with(rep("A"))

    def test_email_validation_rejects_malformed(self):
        for bad in ["plain", "a@@b.com", "@b.com", "a@.com", "a@com.", "a@bcom", "", 123, None]:
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    self.crm.add_lead(bad, "Name", "web", "A")
        self.assertEqual(self.crm.leads, {})
        self.assertEqual(self.crm.log, [])

    def test_email_is_stripped_and_lowered_and_scored(self):
        lead_id = add(self.crm, email="  Foo@Gmail.COM ", name=" N ", source="web")
        lead = self.crm.leads[lead_id]
        self.assertEqual(lead["email"], "foo@gmail.com")
        self.assertEqual(lead["name"], "N")
        self.assertEqual(lead["score"], 10)
        other = add(self.crm, email="foo@corp.com", name="P", source="web")
        self.assertEqual(self.crm.leads[other]["score"], 25)

    def test_name_validation_rejects_blank(self):
        for bad in ["", "   ", None, 7]:
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    self.crm.add_lead("a@b.com", bad, "web", "A")
        self.assertEqual(self.crm.leads, {})

    def test_source_validation_rejects_unknown(self):
        for bad in ["email", "Web", "", None, 3]:
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    self.crm.add_lead("a@b.com", "Name", bad, "A")
        self.assertEqual(self.crm.leads, {})

    def test_duplicate_detection_after_normalization(self):
        first = add(self.crm, email="Dup@Corp.com")
        with self.assertRaises(DuplicateLeadError) as ctx:
            add(self.crm, email="  dup@CORP.com  ")
        self.assertEqual(ctx.exception.existing_id, first)
        self.assertEqual(list(self.crm.leads), [first])
        self.assertEqual(len(self.crm.log), 1)


class TestAssignmentCapacityAndQueue(unittest.TestCase):
    def test_lowest_load_then_smallest_id(self):
        crm = crm_with(rep("A", 2), rep("B", 2), manager("M"))
        self.assertEqual(add(crm, email="1@corp.com"), "L1")
        self.assertEqual(add(crm, email="2@corp.com"), "L2")
        self.assertEqual(add(crm, email="3@corp.com"), "L3")
        self.assertEqual(add(crm, email="4@corp.com"), "L4")
        self.assertEqual(
            [crm.leads[i]["owner"] for i in ("L1", "L2", "L3", "L4")],
            ["A", "B", "A", "B"],
        )

    def test_capacity_exhaustion_queues_and_managers_never_own(self):
        crm = crm_with(rep("A", 1), manager("M"))
        first = add(crm, email="1@corp.com")
        second = add(crm, email="2@corp.com")
        self.assertEqual(crm.leads[first]["owner"], "A")
        self.assertIsNone(crm.leads[second]["owner"])
        self.assertEqual(crm.waiting, [second])
        self.assertNotEqual(crm.leads[first]["owner"], "M")

    def test_waiting_queue_fifo_drained_when_opportunity_won(self):
        crm = crm_with(rep("A", 1), rep("B", 1))
        l1 = add(crm, email="1@corp.com")
        add(crm, email="2@corp.com")
        queued_first = add(crm, email="3@corp.com")
        queued_second = add(crm, email="4@corp.com")
        self.assertEqual(crm.waiting, [queued_first, queued_second])
        crm.qualify(l1, "A")
        opp = crm.convert(l1, 1000, "A")
        crm.advance(opp, "proposal", "A")
        crm.advance(opp, "negotiation", "A")
        crm.advance(opp, "won", "A")
        self.assertEqual(crm.leads[queued_first]["owner"], "A")
        self.assertIsNone(crm.leads[queued_second]["owner"])
        self.assertEqual(crm.waiting, [queued_second])
        self.assertEqual(crm.log[-1], ("assign", queued_first, "system"))


class TestPermissions(unittest.TestCase):
    def setUp(self):
        self.crm = crm_with(rep("A", 3), rep("B", 3), manager("M"))
        self.lead = add(self.crm, email="own@corp.com")
        self.other = add(self.crm, email="other@corp.com")
        self.crm.qualify(self.lead, "A")
        self.opp = self.crm.convert(self.lead, 1000, "A")

    def test_unknown_actor_rejected_first_by_every_method(self):
        crm = self.crm
        with self.assertRaises(PermissionError):
            crm.add_lead("ghost@corp.com", "Ghost", "web", "ghost")
        with self.assertRaises(PermissionError):
            crm.add_lead("bad-email", "", "nope", "ghost")
        self.assertEqual(len(crm.leads), 2)
        self.assertNotIn(
            "ghost@corp.com", [lead["email"] for lead in crm.leads.values()]
        )
        with self.assertRaises(PermissionError):
            crm.qualify(self.lead, "ghost")
        with self.assertRaises(PermissionError):
            crm.convert(self.lead, 10, "ghost")
        with self.assertRaises(PermissionError):
            crm.advance(self.opp, "proposal", "ghost")
        with self.assertRaises(PermissionError):
            crm.discount(self.opp, 5, "ghost")
        with self.assertRaises(PermissionError):
            crm.transfer(self.opp, "A", "ghost")

    def test_non_owner_rep_cannot_mutate(self):
        with self.assertRaises(PermissionError):
            self.crm.qualify(self.lead, "B")
        with self.assertRaises(PermissionError):
            self.crm.convert(self.lead, 100, "B")
        with self.assertRaises(PermissionError):
            self.crm.advance(self.opp, "proposal", "B")
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp, 5, "B")
        self.assertEqual(self.crm.leads[self.lead]["status"], "converted")
        self.assertEqual(self.crm.opps[self.opp]["stage"], "prospect")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 1000)

    def test_manager_may_act_on_any_record(self):
        self.crm.advance(self.opp, "proposal", "M")
        self.crm.discount(self.opp, 5, "M")
        self.assertEqual(self.crm.opps[self.opp]["stage"], "proposal")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 950)


class TestQualificationThreshold(unittest.TestCase):
    def test_web_and_event_on_free_mail_fail_threshold(self):
        crm = crm_with(rep("A"))
        web = add(crm, email="w@gmail.com", source="web")
        event = add(crm, email="e@gmail.com", source="event")
        self.assertEqual(crm.leads[web]["score"], 10)
        self.assertEqual(crm.leads[event]["score"], 20)
        for lead in (web, event):
            with self.assertRaises(ValueError):
                crm.qualify(lead, "A")
            self.assertEqual(crm.leads[lead]["status"], "new")

    def test_referral_threshold_boundary_qualifies(self):
        crm = crm_with(rep("A"))
        lead = add(crm, email="r@gmail.com", source="referral")
        self.assertEqual(crm.leads[lead]["score"], 30)
        crm.qualify(lead, "A")
        self.assertEqual(crm.leads[lead]["status"], "qualified")

    def test_event_on_business_mail_qualifies(self):
        crm = crm_with(rep("A"))
        lead = add(crm, email="e@corp.com", source="event")
        self.assertEqual(crm.leads[lead]["score"], 35)
        crm.qualify(lead, "A")
        self.assertEqual(crm.leads[lead]["status"], "qualified")

    def test_cannot_qualify_twice(self):
        crm = crm_with(rep("A"))
        lead = add(crm, email="r@corp.com", source="referral")
        crm.qualify(lead, "A")
        with self.assertRaises(ValueError):
            crm.qualify(lead, "A")


class TestStageTransitions(unittest.TestCase):
    def setUp(self):
        self.crm = crm_with(rep("A"), manager("M"))
        self.opp = qualified_opp(self.crm, amount=1000)

    def test_unknown_stage_rejected(self):
        for bad in ["closed", "", None, "PROSPECT"]:
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    self.crm.advance(self.opp, bad, "A")
        self.assertEqual(self.crm.opps[self.opp]["stage"], "prospect")

    def test_skipping_stages_rejected(self):
        for bad in ["negotiation", "won"]:
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    self.crm.advance(self.opp, bad, "A")
        self.assertEqual(self.crm.opps[self.opp]["stage"], "prospect")

    def test_backwards_rejected(self):
        self.crm.advance(self.opp, "proposal", "A")
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "prospect", "A")
        self.assertEqual(self.crm.opps[self.opp]["stage"], "proposal")

    def test_full_path_and_lost(self):
        self.crm.advance(self.opp, "proposal", "A")
        self.crm.advance(self.opp, "negotiation", "A")
        self.crm.advance(self.opp, "won", "A")
        self.assertEqual(self.crm.opps[self.opp]["stage"], "won")
        self.assertEqual(self.crm.forecast()["won"], 1000)
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "lost", "A")

    def test_lost_allowed_from_each_non_final_stage(self):
        crm = self.crm
        second = qualified_opp(crm, amount=500)
        crm.advance(second, "proposal", "A")
        crm.advance(second, "lost", "A")
        self.assertEqual(crm.opps[second]["stage"], "lost")
        crm.advance(self.opp, "lost", "A")
        self.assertEqual(crm.opps[self.opp]["stage"], "lost")
        self.assertEqual(crm.forecast()["open"], 0)


class TestBigDealApproval(unittest.TestCase):
    def setUp(self):
        self.crm = crm_with(rep("A"), manager("M"))
        self.big = qualified_opp(self.crm, amount=60000)
        self.crm.advance(self.big, "proposal", "A")

    def test_rep_needs_manager_for_negotiation_above_50000(self):
        before = list(self.crm.log)
        with self.assertRaises(PermissionError):
            self.crm.advance(self.big, "negotiation", "A")
        self.assertEqual(self.crm.opps[self.big]["stage"], "proposal")
        self.assertEqual(self.crm.log, before)

    def test_manager_can_approve_big_deal(self):
        self.crm.advance(self.big, "negotiation", "M")
        self.assertEqual(self.crm.opps[self.big]["stage"], "negotiation")

    def test_exactly_50000_does_not_need_manager(self):
        crm = crm_with(rep("A"), manager("M"))
        opp = qualified_opp(crm, amount=50000)
        crm.advance(opp, "proposal", "A")
        crm.advance(opp, "negotiation", "A")
        self.assertEqual(crm.opps[opp]["stage"], "negotiation")


class TestDiscountLimits(unittest.TestCase):
    def setUp(self):
        self.crm = crm_with(rep("A"), manager("M"))
        self.opp = qualified_opp(self.crm, amount=10000)

    def test_pct_range_and_type(self):
        for bad in [0, 31, -5, True, "10", 1.5, None]:
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    self.crm.discount(self.opp, bad, "M")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 10000)

    def test_rep_discount_cap_is_10(self):
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp, 11, "A")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 10000)
        self.crm.discount(self.opp, 10, "A")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 9000)

    def test_manager_may_discount_30(self):
        self.crm.discount(self.opp, 30, "M")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 7000)
        self.assertEqual(self.crm.log[-1], ("discount", self.opp, "M"))

    def test_cumulative_floor_blocks_further_discount(self):
        self.crm.discount(self.opp, 30, "M")
        before = list(self.crm.log)
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp, 1, "M")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 7000)
        self.assertEqual(self.crm.log, before)

    def test_manager_cannot_exceed_cumulative_30(self):
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp, 31, "M")

    def test_final_stage_rejected(self):
        self.crm.advance(self.opp, "proposal", "M")
        self.crm.advance(self.opp, "negotiation", "M")
        self.crm.advance(self.opp, "won", "M")
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp, 5, "M")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 10000)


class TestTransferRules(unittest.TestCase):
    def setUp(self):
        self.crm = crm_with(rep("A", 2), rep("B", 2), manager("M", 5))
        self.opp = qualified_opp(self.crm, amount=1000)

    def test_only_manager_may_transfer(self):
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.opp, "B", "A")
        self.assertEqual(self.crm.opps[self.opp]["owner"], "A")

    def test_target_must_be_known_rep(self):
        for bad in ["M", "ghost", None, 5]:
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    self.crm.transfer(self.opp, bad, "M")
        self.assertEqual(self.crm.opps[self.opp]["owner"], "A")

    def test_same_owner_rejected(self):
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "A", "M")

    def test_target_at_capacity_rejected(self):
        add(self.crm, email="b1@corp.com", actor="B")
        add(self.crm, email="b2@corp.com", actor="B")
        add(self.crm, email="b3@corp.com", actor="B")
        self.assertEqual(self.crm._load("B"), 2)
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "B", "M")
        self.assertEqual(self.crm.opps[self.opp]["owner"], "A")

    def test_final_stage_rejected(self):
        self.crm.advance(self.opp, "proposal", "M")
        self.crm.advance(self.opp, "negotiation", "M")
        self.crm.advance(self.opp, "won", "M")
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "B", "M")

    def test_transfer_moves_owner_and_drains_previous_owner_queue(self):
        crm = crm_with(rep("A", 1), rep("B", 2), manager("M"))
        l1 = add(crm, email="1@corp.com")
        add(crm, email="2@corp.com")
        add(crm, email="3@corp.com")
        queued = add(crm, email="4@corp.com")
        self.assertEqual(crm.waiting, [queued])
        crm.qualify(l1, "A")
        opp = crm.convert(l1, 1000, "A")
        crm.users["B"]["capacity"] = 3
        crm.transfer(opp, "B", "M")
        self.assertEqual(crm.opps[opp]["owner"], "B")
        self.assertEqual(crm.leads[queued]["owner"], "A")
        self.assertIn(("assign", queued, "system"), crm.log)


class TestAtomicity(unittest.TestCase):
    def test_failed_add_changes_nothing(self):
        crm = crm_with(rep("A"))
        with self.assertRaises(ValueError):
            add(crm, email="not-an-email")
        self.assertEqual(crm.leads, {})
        self.assertEqual(crm.log, [])
        self.assertEqual(add(crm, email="ok@corp.com"), "L1")
        self.assertEqual(crm.log, [("add_lead", "L1", "A")])

    def test_duplicate_failure_changes_nothing(self):
        crm = crm_with(rep("A"))
        first = add(crm, email="ok@corp.com")
        with self.assertRaises(DuplicateLeadError):
            add(crm, email="OK@corp.com")
        self.assertEqual(list(crm.leads), [first])
        self.assertEqual(len(crm.log), 1)

    def test_failed_qualify_logs_nothing(self):
        crm = crm_with(rep("A"))
        lead = add(crm, email="web@gmail.com", source="web")
        with self.assertRaises(ValueError):
            crm.qualify(lead, "A")
        self.assertEqual(crm.leads[lead]["status"], "new")
        self.assertEqual(len(crm.log), 1)

    def test_failed_convert_creates_no_opportunity(self):
        crm = crm_with(rep("A"))
        lead = add(crm, email="ok@corp.com")
        crm.qualify(lead, "A")
        with self.assertRaises(ValueError):
            crm.convert(lead, 0, "A")
        self.assertEqual(crm.opps, {})
        self.assertEqual(crm.leads[lead]["status"], "qualified")
        self.assertEqual(len(crm.log), 2)

    def test_failed_advance_leaves_stage_and_log(self):
        crm = crm_with(rep("A"), manager("M"))
        opp = qualified_opp(crm, amount=60000)
        crm.advance(opp, "proposal", "A")
        before = list(crm.log)
        with self.assertRaises(PermissionError):
            crm.advance(opp, "negotiation", "A")
        self.assertEqual(crm.opps[opp]["stage"], "proposal")
        self.assertEqual(crm.log, before)

    def test_failed_discount_leaves_amount_and_log(self):
        crm = crm_with(rep("A"), manager("M"))
        opp = qualified_opp(crm, amount=10000)
        crm.discount(opp, 30, "M")
        before = list(crm.log)
        with self.assertRaises(ValueError):
            crm.discount(opp, 1, "M")
        self.assertEqual(crm.opps[opp]["amount"], 7000)
        self.assertEqual(crm.log, before)

    def test_failed_transfer_changes_nothing(self):
        crm = crm_with(rep("A"), rep("B"), manager("M"))
        opp = qualified_opp(crm, amount=1000)
        before = list(crm.log)
        with self.assertRaises(PermissionError):
            crm.transfer(opp, "B", "A")
        self.assertEqual(crm.opps[opp]["owner"], "A")
        self.assertEqual(crm.log, before)


class TestForecast(unittest.TestCase):
    def test_empty_forecast(self):
        self.assertEqual(
            crm_with(rep("A")).forecast(), {"open": 0, "weighted": 0, "won": 0}
        )

    def test_forecast_weights_and_totals(self):
        crm = crm_with(rep("A", 5), manager("M"))
        prospect = qualified_opp(crm, amount=1000)
        proposal = qualified_opp(crm, amount=2000)
        crm.advance(proposal, "proposal", "A")
        won = qualified_opp(crm, amount=4000)
        crm.advance(won, "proposal", "A")
        crm.advance(won, "negotiation", "A")
        crm.advance(won, "won", "A")
        self.assertEqual(crm.forecast(), {"open": 2, "weighted": 700, "won": 4000})
        self.assertEqual(crm.opps[prospect]["stage"], "prospect")


class TestCheckOrder(unittest.TestCase):
    """The spec fixes the order of the checks; the first failing one decides.

    Each test pairs an invalid value with an actor who would *also* fail the
    later permission check, so only the documented order yields the expected
    exception type.
    """

    def setUp(self):
        self.crm = crm_with(rep("A", 5), rep("B", 5), manager("M"))
        self.lead = add(self.crm, email="owner@corp.com")
        self.crm.qualify(self.lead, "A")
        self.opp = self.crm.convert(self.lead, 1000, "A")

    def test_advance_stage_name_checked_before_permission(self):
        for bad in ["closed", "", None, "PROSPECT", 3]:
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    self.crm.advance(self.opp, bad, "B")
        self.assertEqual(self.crm.opps[self.opp]["stage"], "prospect")

    def test_advance_permission_checked_before_final_stage(self):
        self.crm.advance(self.opp, "lost", "A")
        for stage in ["proposal", "lost"]:
            with self.subTest(stage=stage):
                with self.assertRaises(PermissionError):
                    self.crm.advance(self.opp, stage, "B")
        self.assertEqual(self.crm.opps[self.opp]["stage"], "lost")

    def test_convert_amount_checked_before_permission(self):
        lead = add(self.crm, email="second@corp.com")
        self.assertEqual(self.crm.leads[lead]["owner"], "B")
        self.crm.qualify(lead, "B")
        for bad in [0, -1, True, 1.5, "10"]:
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    self.crm.convert(lead, bad, "A")
        self.assertEqual(list(self.crm.opps), [self.opp])
        self.assertEqual(self.crm.leads[lead]["status"], "qualified")

    def test_discount_pct_checked_before_permission(self):
        for bad in [0, 31, -5, True, "10", 1.5, None]:
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    self.crm.discount(self.opp, bad, "B")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 1000)

    def test_discount_permission_checked_before_final_stage(self):
        self.crm.advance(self.opp, "proposal", "A")
        self.crm.advance(self.opp, "negotiation", "A")
        self.crm.advance(self.opp, "won", "A")
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp, 5, "B")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 1000)

    def test_discount_final_stage_checked_before_rep_cap(self):
        # pct=11 is beyond a rep's cap (check 5) *and* the stage is final
        # (check 4): the final-stage error must win.
        self.crm.advance(self.opp, "proposal", "A")
        self.crm.advance(self.opp, "negotiation", "A")
        self.crm.advance(self.opp, "won", "A")
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp, 11, "A")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 1000)

    def test_discount_rep_cap_still_applies_to_owner(self):
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp, 11, "A")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 1000)

    def test_transfer_manager_checked_before_target(self):
        for bad in ["ghost", None, 5, "M"]:
            with self.subTest(bad=bad):
                with self.assertRaises(PermissionError):
                    self.crm.transfer(self.opp, bad, "A")
        self.assertEqual(self.crm.opps[self.opp]["owner"], "A")

    def test_add_lead_source_checked_before_duplicate(self):
        before = list(self.crm.log)
        with self.assertRaises(ValueError):
            self.crm.add_lead("OWNER@corp.com", "Dup", "nope", "A")
        self.assertEqual(len(self.crm.leads), 1)
        self.assertEqual(self.crm.log, before)


class TestBehaviourEdges(unittest.TestCase):
    def test_manager_conversion_keeps_lead_owner(self):
        crm = crm_with(rep("A", 3), manager("M"))
        lead = add(crm, email="edge@corp.com", actor="A")
        crm.qualify(lead, "M")
        opp = crm.convert(lead, 1000, "M")
        self.assertEqual(crm.opps[opp]["owner"], "A")
        self.assertEqual(crm.log[-1], ("convert", opp, "M"))

    def test_lost_frees_slot_and_drains_waiting_queue(self):
        crm = crm_with(rep("A", 1), manager("M"))
        l1 = add(crm, email="one@corp.com")
        queued = add(crm, email="two@corp.com")
        self.assertEqual(crm.waiting, [queued])
        crm.qualify(l1, "A")
        opp = crm.convert(l1, 1000, "A")
        crm.advance(opp, "proposal", "A")
        crm.advance(opp, "lost", "A")
        self.assertEqual(crm.leads[queued]["owner"], "A")
        self.assertEqual(crm.waiting, [])
        self.assertEqual(crm.log[-1], ("assign", queued, "system"))

    def test_forecast_negotiation_weight_is_60(self):
        crm = crm_with(rep("A", 3))
        opp = qualified_opp(crm, amount=10000)
        crm.advance(opp, "proposal", "A")
        crm.advance(opp, "negotiation", "A")
        self.assertEqual(crm.forecast(), {"open": 1, "weighted": 6000, "won": 0})

    def test_convert_rejects_non_int_amounts(self):
        crm = crm_with(rep("A", 3))
        lead = add(crm, email="amt@corp.com")
        crm.qualify(lead, "A")
        for bad in [True, 1.5, "10", 0, -1, None]:
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    crm.convert(lead, bad, "A")
        self.assertEqual(crm.opps, {})
        self.assertEqual(crm.leads[lead]["status"], "qualified")

    def test_discount_keeps_amount_an_int(self):
        crm = crm_with(rep("A", 3), manager("M"))
        opp = qualified_opp(crm, amount=9000)
        crm.discount(opp, 30, "M")
        amount = crm.opps[opp]["amount"]
        self.assertIsInstance(amount, int)
        self.assertNotIsInstance(amount, bool)
        self.assertEqual(amount, 6300)

    def test_lost_final_stage_blocks_discount_and_transfer(self):
        crm = crm_with(rep("A", 3), rep("B", 3), manager("M"))
        opp = qualified_opp(crm, amount=1000)
        crm.advance(opp, "lost", "A")
        with self.assertRaises(ValueError):
            crm.discount(opp, 5, "M")
        with self.assertRaises(ValueError):
            crm.transfer(opp, "B", "M")
        self.assertEqual(crm.opps[opp]["amount"], 1000)
        self.assertEqual(crm.opps[opp]["owner"], "A")


if __name__ == "__main__":
    unittest.main()
