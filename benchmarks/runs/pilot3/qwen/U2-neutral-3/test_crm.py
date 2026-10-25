import unittest

from crm import CRM, DuplicateLeadError


def rep(uid, capacity):
    return {"id": uid, "role": "rep", "capacity": capacity}


def mgr(uid):
    return {"id": uid, "role": "manager", "capacity": 0}


class TestBasics(unittest.TestCase):
    def setUp(self):
        self.crm = CRM([rep("r1", 1), rep("r2", 1), mgr("m1")])

    def test_attributes_exist(self):
        self.assertIsInstance(self.crm.leads, dict)
        self.assertIsInstance(self.crm.opps, dict)
        self.assertIsInstance(self.crm.log, list)

    def test_unknown_actor_permission_error(self):
        with self.assertRaises(PermissionError):
            self.crm.add_lead("a@b.com", "A", "web", "ghost")
        with self.assertRaises(PermissionError):
            self.crm.qualify("L1", "ghost")
        with self.assertRaises(PermissionError):
            self.crm.convert("L1", 100, "ghost")
        with self.assertRaises(PermissionError):
            self.crm.advance("O1", "proposal", "ghost")
        with self.assertRaises(PermissionError):
            self.crm.discount("O1", 5, "ghost")
        with self.assertRaises(PermissionError):
            self.crm.transfer("O1", "r1", "ghost")

    def test_actor_checked_before_other_validation(self):
        # Unknown actor + invalid email -> PermissionError wins (actor first).
        with self.assertRaises(PermissionError):
            self.crm.add_lead("not-an-email", "", "bad", "nobody")

    def test_forecast_needs_no_actor(self):
        self.assertEqual(
            self.crm.forecast(), {"open": 0, "weighted": 0, "won": 0}
        )


class TestAddLead(unittest.TestCase):
    def setUp(self):
        self.crm = CRM([rep("r1", 5), mgr("m1")])

    def test_valid_lead_structure(self):
        lead_id = self.crm.add_lead(
            "  User@Example.COM ", "  Alice  ", "referral", "m1")
        self.assertEqual(lead_id, "L1")
        lead = self.crm.leads["L1"]
        self.assertEqual(lead["id"], "L1")
        self.assertEqual(lead["email"], "user@example.com")
        self.assertEqual(lead["name"], "Alice")
        self.assertEqual(lead["source"], "referral")
        self.assertEqual(lead["score"], 30 + 15)
        self.assertEqual(lead["owner"], "r1")
        self.assertEqual(lead["status"], "new")
        self.assertEqual(self.crm.log, [("add_lead", "L1", "m1")])

    def test_scores(self):
        cases = [
            ("w@gmail.com", "web", 10),
            ("w@yahoo.com", "web", 10),
            ("w@outlook.com", "web", 10),
            ("w@corp.com", "web", 25),
            ("r@gmail.com", "referral", 30),
            ("r@corp.com", "referral", 45),
            ("e@gmail.com", "event", 20),
            ("e@corp.com", "event", 35),
        ]
        for i, (email, source, score) in enumerate(cases, start=1):
            lead_id = self.crm.add_lead(email, "N", source, "m1")
            self.assertEqual(lead_id, "L%d" % i)
            self.assertEqual(self.crm.leads[lead_id]["score"], score, email)

    def test_invalid_emails(self):
        bad = [
            "no-at-sign.com",
            "@missing-local.com",
            "a@",
            "two@@at.com",
            "a@nodot",
            "a@.",           # only dot is the whole domain: boundary dot
            "a@..",          # both dots are boundary dots
            "a@.com.",       # interior slice "com" has no dot
            "a@b.",          # trailing dot only
            "a@.b",          # leading dot only
            "  ",
        ]
        for email in bad:
            with self.assertRaises(ValueError, msg=repr(email)):
                self.crm.add_lead(email, "N", "web", "m1")

    def test_domain_dot_rule_is_existential(self):
        # Spec: the domain must "contain a '.' which is neither the first nor
        # the last character of the domain".  That is an *existence* claim
        # about one dot, not a ban on boundary dots: a domain with an interior
        # dot is valid even when it also starts or ends with a dot.
        for email in ["a@.leading-dot.com", "a@trailing-dot.com.",
                      "a@dot.com.", "a@.a.b."]:
            lead_id = self.crm.add_lead(email, "N", "web", "m1")
            self.assertEqual(self.crm.leads[lead_id]["email"], email)

    def test_email_must_be_str(self):
        for bad in [None, 42, b"a@b.com", ["a@b.com"]]:
            with self.assertRaises(ValueError, msg=repr(bad)):
                self.crm.add_lead(bad, "N", "web", "m1")

    def test_domain_dot_in_middle_ok(self):
        lead_id = self.crm.add_lead("a@sub.domain.com", "N", "web", "m1")
        self.assertEqual(self.crm.leads[lead_id]["email"], "a@sub.domain.com")

    def test_name_validation(self):
        for bad in [None, 42, "", "   ", "\t\n"]:
            with self.assertRaises(ValueError, msg=repr(bad)):
                self.crm.add_lead("a@b.com", bad, "web", "m1")

    def test_source_validation(self):
        for bad in [None, "phone", "", 3, "WEB"]:
            with self.assertRaises(ValueError, msg=repr(bad)):
                self.crm.add_lead("a@b.com", "N", bad, "m1")

    def test_duplicate_raises_with_existing_id(self):
        first = self.crm.add_lead("a@b.com", "Ann", "web", "m1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            self.crm.add_lead("  A@B.COM  ", "Ann Other", "event", "m1")
        self.assertEqual(ctx.exception.existing_id, first)
        self.assertTrue(issubclass(DuplicateLeadError, Exception))
        # Nothing changed by the failed call.
        self.assertEqual(len(self.crm.leads), 1)
        self.assertEqual(self.crm.log, [("add_lead", first, "m1")])
        # Counter was not consumed by the failure.
        second = self.crm.add_lead("c@d.com", "C", "web", "m1")
        self.assertEqual(second, "L2")

    def test_failed_call_leaves_no_log(self):
        with self.assertRaises(ValueError):
            self.crm.add_lead("bad-email", "N", "web", "m1")
        self.assertEqual(self.crm.log, [])
        self.assertEqual(self.crm.leads, {})
        # Next success is still L1 (only successes are counted).
        self.assertEqual(self.crm.add_lead("a@b.com", "N", "web", "m1"), "L1")

    def test_domain_case_normalization_free_provider(self):
        lead_id = self.crm.add_lead("x@GMAIL.COM", "X", "event", "m1")
        self.assertEqual(self.crm.leads[lead_id]["score"], 20)  # no +15


class TestOwnershipAndQueue(unittest.TestCase):
    def test_lowest_load_then_string_id_tie_break(self):
        crm = CRM([rep("b", 2), rep("a", 2)])
        l1 = crm.add_lead("1@x.com", "N", "web", "b")
        self.assertEqual(crm.leads[l1]["owner"], "a")   # tie at 0 -> "a"
        l2 = crm.add_lead("2@x.com", "N", "web", "b")
        self.assertEqual(crm.leads[l2]["owner"], "b")   # b load 0 < a load 1
        l3 = crm.add_lead("3@x.com", "N", "web", "b")
        self.assertEqual(crm.leads[l3]["owner"], "a")   # tie at 1 -> "a"
        l4 = crm.add_lead("4@x.com", "N", "web", "b")
        self.assertEqual(crm.leads[l4]["owner"], "b")   # a full at 2

    def test_tie_break_is_string_order_not_numeric(self):
        crm = CRM([rep("r2", 1), rep("r10", 1)])
        l = crm.add_lead("1@x.com", "N", "web", "r2")
        self.assertEqual(crm.leads[l]["owner"], "r10")  # "r10" < "r2"

    def test_managers_never_own(self):
        crm = CRM([mgr("aaa"), rep("zzz", 1)])
        lead_id = crm.add_lead("a@b.com", "N", "web", "aaa")
        self.assertEqual(crm.leads[lead_id]["owner"], "zzz")

    def test_queue_when_all_reps_full(self):
        crm = CRM([rep("r1", 1), rep("r2", 1), rep("r3", 0), mgr("m")])
        l1 = crm.add_lead("1@x.com", "N", "web", "m")
        l2 = crm.add_lead("2@x.com", "N", "web", "m")
        l3 = crm.add_lead("3@x.com", "N", "web", "m")
        l4 = crm.add_lead("4@x.com", "N", "web", "m")
        self.assertEqual(crm.leads[l1]["owner"], "r1")
        self.assertEqual(crm.leads[l2]["owner"], "r2")
        self.assertIsNone(crm.leads[l3]["owner"])
        self.assertIsNone(crm.leads[l4]["owner"])
        self.assertEqual(crm.leads[l3]["status"], "new")

    def test_manager_qualifies_unowned_lead(self):
        crm = CRM([rep("r1", 0), mgr("m")])
        lead_id = crm.add_lead("q@corp.com", "Q", "referral", "m")
        crm.qualify(lead_id, "m")  # managers pass the ownership check
        self.assertEqual(crm.leads[lead_id]["status"], "qualified")


class TestQualify(unittest.TestCase):
    def setUp(self):
        self.crm = CRM([rep("r1", 3), rep("r2", 3), mgr("m1")])
        self.high = self.crm.add_lead("a@corp.com", "A", "referral", "m1")  # 45
        self.low = self.crm.add_lead("b@corp.com", "B", "web", "m1")  # 25

    def test_qualify_success(self):
        self.crm.qualify(self.high, "r1")
        self.assertEqual(self.crm.leads[self.high]["status"], "qualified")
        self.assertEqual(self.crm.log[-1], ("qualify", self.high, "r1"))

    def test_qualify_by_manager(self):
        self.crm.qualify(self.high, "m1")
        self.assertEqual(self.crm.leads[self.high]["status"], "qualified")

    def test_unknown_lead_value_error(self):
        with self.assertRaises(ValueError):
            self.crm.qualify("L99", "r1")

    def test_wrong_owner_permission_error(self):
        # self.high is owned by r1; r2 is a known user but not the owner.
        with self.assertRaises(PermissionError):
            self.crm.qualify(self.high, "r2")

    def test_score_below_30_value_error(self):
        self.assertEqual(self.crm.leads[self.low]["owner"], "r2")
        with self.assertRaises(ValueError):
            self.crm.qualify(self.low, "r2")

    def test_score_exactly_30_ok(self):
        lead_id = self.crm.add_lead("d@gmail.com", "D", "referral", "m1")  # 30
        owner = self.crm.leads[lead_id]["owner"]
        self.crm.qualify(lead_id, owner)
        self.assertEqual(self.crm.leads[lead_id]["status"], "qualified")

    def test_status_must_be_new(self):
        self.crm.qualify(self.high, "m1")
        with self.assertRaises(ValueError):
            self.crm.qualify(self.high, "m1")

    def test_check_order_owner_before_score(self):
        # r1 is not the owner of the low-score lead (owned by r2),
        # so PermissionError decides, not the score ValueError.
        with self.assertRaises(PermissionError):
            self.crm.qualify(self.low, "r1")

    def test_failed_qualify_no_log(self):
        before = list(self.crm.log)
        with self.assertRaises(ValueError):
            self.crm.qualify(self.low, "r2")
        self.assertEqual(self.crm.log, before)
        self.assertEqual(self.crm.leads[self.low]["status"], "new")


class TestConvert(unittest.TestCase):
    def setUp(self):
        self.crm = CRM([rep("r1", 3), rep("r2", 3), mgr("m1")])
        self.lead = self.crm.add_lead("a@corp.com", "A", "referral", "m1")
        self.crm.qualify(self.lead, "r1")

    def test_convert_success(self):
        opp_id = self.crm.convert(self.lead, 1500, "r1")
        self.assertEqual(opp_id, "O1")
        opp = self.crm.opps[opp_id]
        self.assertEqual(
            opp,
            {
                "id": "O1",
                "lead_id": self.lead,
                "owner": "r1",
                "amount": 1500,
                "original_amount": 1500,
                "stage": "prospect",
            },
        )
        self.assertEqual(self.crm.leads[self.lead]["status"], "converted")
        self.assertEqual(self.crm.log[-1], ("convert", "O1", "r1"))

    def test_amount_validation(self):
        for bad in [0, -5, 1.5, "100", None, True, False]:
            with self.assertRaises(ValueError, msg=repr(bad)):
                self.crm.convert(self.lead, bad, "r1")
        self.assertEqual(self.crm.leads[self.lead]["status"], "qualified")

    def test_unknown_lead(self):
        with self.assertRaises(ValueError):
            self.crm.convert("L42", 100, "r1")

    def test_wrong_owner(self):
        with self.assertRaises(PermissionError):
            self.crm.convert(self.lead, 100, "r2")

    def test_status_must_be_qualified(self):
        fresh = self.crm.add_lead("n@corp.com", "N", "referral", "m1")
        owner = self.crm.leads[fresh]["owner"]
        with self.assertRaises(ValueError):
            self.crm.convert(fresh, 100, owner)

    def test_check_order_amount_before_owner(self):
        # bad amount + wrong owner -> ValueError (amount check is earlier).
        with self.assertRaises(ValueError):
            self.crm.convert(self.lead, -1, "r2")

    def test_unowned_lead_value_error(self):
        # Manager qualifies a queued lead; conversion then has no owner.
        crm = CRM([rep("r1", 0), mgr("m")])
        lead_id = crm.add_lead("q@corp.com", "Q", "referral", "m")
        crm.qualify(lead_id, "m")
        with self.assertRaises(ValueError):
            crm.convert(lead_id, 100, "m")

    def test_failed_convert_no_log_no_counter(self):
        before = list(self.crm.log)
        with self.assertRaises(ValueError):
            self.crm.convert(self.lead, -1, "r1")
        self.assertEqual(self.crm.log, before)
        # Counter untouched by failure: next success is O1.
        self.assertEqual(self.crm.convert(self.lead, 10, "r1"), "O1")


class TestAdvance(unittest.TestCase):
    def setUp(self):
        self.crm = CRM([rep("r1", 1), rep("r2", 2), mgr("m1")])
        self.lead = self.crm.add_lead("a@corp.com", "A", "referral", "m1")
        self.crm.qualify(self.lead, "r1")
        self.opp = self.crm.convert(self.lead, 1000, "r1")  # under 50000

    def test_full_winning_path(self):
        self.crm.advance(self.opp, "proposal", "r1")
        self.crm.advance(self.opp, "negotiation", "r1")
        self.crm.advance(self.opp, "won", "r1")
        self.assertEqual(self.crm.opps[self.opp]["stage"], "won")
        self.assertEqual(
            self.crm.log[-3:],
            [
                ("advance", self.opp, "r1"),
                ("advance", self.opp, "r1"),
                ("advance", self.opp, "r1"),
            ],
        )

    def test_lost_from_prospect(self):
        self.crm.advance(self.opp, "lost", "r1")
        self.assertEqual(self.crm.opps[self.opp]["stage"], "lost")

    def test_lost_from_proposal_by_manager(self):
        crm = CRM([rep("r1", 1), mgr("m")])
        l = crm.add_lead("a@corp.com", "A", "referral", "m")
        crm.qualify(l, "r1")
        o = crm.convert(l, 100, "r1")
        crm.advance(o, "proposal", "r1")
        crm.advance(o, "lost", "m")
        self.assertEqual(crm.opps[o]["stage"], "lost")

    def test_skip_stage_value_error(self):
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "negotiation", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "won", "r1")

    def test_same_stage_value_error(self):
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "prospect", "r1")

    def test_invalid_stage_name(self):
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "closed", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, None, "r1")

    def test_unknown_opp(self):
        with self.assertRaises(ValueError):
            self.crm.advance("O99", "proposal", "r1")

    def test_wrong_owner_permission(self):
        with self.assertRaises(PermissionError):
            self.crm.advance(self.opp, "proposal", "r2")

    def test_final_stage_frozen(self):
        self.crm.advance(self.opp, "lost", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "proposal", "m1")
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "lost", "m1")

    def test_check_order_stage_valid_before_owner(self):
        # r2 is not the owner, but invalid stage decides first.
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp, "bogus", "r2")

    def test_big_deal_negotiation_needs_manager(self):
        crm = CRM([rep("r1", 2), mgr("m")])
        l = crm.add_lead("a@corp.com", "A", "referral", "m")
        crm.qualify(l, "r1")
        o = crm.convert(l, 50001, "r1")
        crm.advance(o, "proposal", "r1")
        with self.assertRaises(PermissionError):
            crm.advance(o, "negotiation", "r1")
        self.assertEqual(crm.opps[o]["stage"], "proposal")
        crm.advance(o, "negotiation", "m")  # manager can push it through
        self.assertEqual(crm.opps[o]["stage"], "negotiation")

    def test_exactly_50000_needs_no_manager(self):
        crm = CRM([rep("r1", 1), mgr("m")])
        l = crm.add_lead("a@corp.com", "A", "referral", "m")
        crm.qualify(l, "r1")
        o = crm.convert(l, 50000, "r1")
        crm.advance(o, "proposal", "r1")
        crm.advance(o, "negotiation", "r1")
        self.assertEqual(crm.opps[o]["stage"], "negotiation")

    def test_failed_advance_changes_nothing(self):
        with self.assertRaises(PermissionError):
            self.crm.advance(self.opp, "proposal", "r2")
        self.assertEqual(self.crm.opps[self.opp]["stage"], "prospect")
        self.assertEqual(len(self.crm.log), 3)

    def test_win_frees_slot_and_assigns_waiting(self):
        crm = CRM([rep("r1", 1), rep("r2", 1), mgr("m1")])
        lead = crm.add_lead("a@corp.com", "A", "referral", "m1")  # -> r1
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 1000, "r1")
        w1 = crm.add_lead("w1@x.com", "W1", "web", "m1")  # -> r2 (r1 full)
        w2 = crm.add_lead("w2@x.com", "W2", "web", "m1")  # queued: all full
        self.assertIsNone(crm.leads[w2]["owner"])
        crm.advance(opp, "proposal", "m1")
        crm.advance(opp, "negotiation", "m1")
        crm.advance(opp, "won", "m1")
        self.assertEqual(crm.leads[w2]["owner"], "r1")  # oldest waiting
        self.assertEqual(crm.leads[w1]["owner"], "r2")  # untouched
        self.assertEqual(crm.leads[w2]["status"], "new")
        self.assertEqual(
            crm.log[-2:],
            [("advance", opp, "m1"), ("assign", w2, "system")],
        )

    def test_lost_frees_slot_too(self):
        crm = CRM([rep("r1", 1), rep("r2", 1), mgr("m1")])
        lead = crm.add_lead("a@corp.com", "A", "referral", "m1")  # -> r1
        crm.qualify(lead, "r1")
        opp = crm.convert(lead, 1000, "r1")
        crm.add_lead("o@x.com", "O", "web", "m1")  # -> r2
        waiting = crm.add_lead("w@x.com", "W", "web", "m1")  # queued
        crm.advance(opp, "lost", "r1")
        self.assertEqual(crm.leads[waiting]["owner"], "r1")
        self.assertEqual(
            crm.log[-2:],
            [("advance", opp, "r1"), ("assign", waiting, "system")],
        )

    def test_slot_fill_assigns_multiple_in_fifo_order(self):
        crm = CRM([rep("r1", 2), mgr("m")])
        l1 = crm.add_lead("1@x.com", "1", "referral", "m")  # r1 load 1
        l2 = crm.add_lead("2@x.com", "2", "referral", "m")  # r1 load 2
        l3 = crm.add_lead("3@x.com", "3", "referral", "m")  # queued
        l4 = crm.add_lead("4@x.com", "4", "referral", "m")  # queued
        crm.qualify(l1, "r1")
        o1 = crm.convert(l1, 100, "r1")  # still load 2 (lead->opp swap)
        crm.advance(o1, "proposal", "r1")
        crm.advance(o1, "lost", "r1")  # load 1 -> take oldest waiting (l3)
        self.assertEqual(crm.leads[l3]["owner"], "r1")
        self.assertIsNone(crm.leads[l4]["owner"])  # capacity reached again


class TestDiscount(unittest.TestCase):
    def setUp(self):
        self.crm = CRM([rep("r1", 3), rep("r2", 3), mgr("m1")])
        self.lead = self.crm.add_lead("a@corp.com", "A", "referral", "m1")
        self.crm.qualify(self.lead, "r1")
        self.opp = self.crm.convert(self.lead, 1000, "r1")

    def test_rep_small_discount(self):
        self.crm.discount(self.opp, 10, "r1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 900)
        self.assertEqual(self.crm.opps[self.opp]["original_amount"], 1000)
        self.assertEqual(self.crm.log[-1], ("discount", self.opp, "r1"))

    def test_pct_validation(self):
        for bad in [0, 31, -1, 1.0, "10", None, True, False]:
            with self.assertRaises(ValueError, msg=repr(bad)):
                self.crm.discount(self.opp, bad, "r1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 1000)

    def test_rep_over_10_permission_error(self):
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp, 11, "r1")

    def test_manager_up_to_30(self):
        self.crm.discount(self.opp, 30, "m1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 700)

    def test_wrong_owner_permission(self):
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp, 5, "r2")

    def test_final_stage_value_error(self):
        self.crm.advance(self.opp, "lost", "r1")
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp, 5, "m1")

    def test_cumulative_floor_exact(self):
        # 30% off 1000 leaves 700; any further discount breaks the 70% floor.
        self.crm.discount(self.opp, 30, "m1")
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp, 1, "m1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 700)

    def test_multiple_discounts_within_floor(self):
        # 10% then 20% of 900 = 720; 72000 >= 70000 ok.
        self.crm.discount(self.opp, 10, "r1")
        self.crm.discount(self.opp, 20, "m1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 720)

    def test_floor_rejects_even_when_pct_seems_fine(self):
        # amount 999: 30% -> 999*70//100 = 699; 699*100=69900 < 999*70=69930.
        lead = self.crm.add_lead("b@corp.com", "B", "referral", "m1")
        owner = self.crm.leads[lead]["owner"]
        self.crm.qualify(lead, owner)
        opp = self.crm.convert(lead, 999, owner)
        with self.assertRaises(ValueError):
            self.crm.discount(opp, 30, "m1")
        self.assertEqual(self.crm.opps[opp]["amount"], 999)

    def test_check_order_pct_before_owner(self):
        with self.assertRaises(ValueError):  # invalid pct wins over non-owner
            self.crm.discount(self.opp, 99, "r2")

    def test_check_order_owner_before_final_stage(self):
        self.crm.advance(self.opp, "proposal", "m1")
        self.crm.advance(self.opp, "negotiation", "m1")
        self.crm.advance(self.opp, "won", "m1")
        # r2 is neither owner nor manager, and stage is final: owner check is
        # earlier, so PermissionError decides.
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp, 5, "r2")

    def test_failed_discount_no_log(self):
        before = list(self.crm.log)
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp, 20, "r1")
        self.assertEqual(self.crm.log, before)


class TestTransfer(unittest.TestCase):
    def setUp(self):
        self.crm = CRM([rep("r1", 1), rep("r2", 1), mgr("m1")])
        self.lead = self.crm.add_lead("a@corp.com", "A", "referral", "m1")
        self.crm.qualify(self.lead, "r1")
        self.opp = self.crm.convert(self.lead, 1000, "r1")

    def test_manager_transfers_open_opp(self):
        self.crm.transfer(self.opp, "r2", "m1")
        self.assertEqual(self.crm.opps[self.opp]["owner"], "r2")
        self.assertEqual(self.crm.log[-1], ("transfer", self.opp, "m1"))

    def test_only_managers(self):
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.opp, "r2", "r1")

    def test_new_owner_must_be_known_rep(self):
        for bad in ["ghost", "m1", 1, None]:
            with self.assertRaises(ValueError, msg=repr(bad)):
                self.crm.transfer(self.opp, bad, "m1")

    def test_final_stage_value_error(self):
        self.crm.advance(self.opp, "lost", "m1")
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "r2", "m1")

    def test_same_owner_value_error(self):
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "r1", "m1")

    def test_target_at_capacity_value_error(self):
        other = self.crm.add_lead("b@corp.com", "B", "referral", "m1")
        self.assertEqual(self.crm.leads[other]["owner"], "r2")  # r2 now full
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "r2", "m1")
        self.assertEqual(self.crm.opps[self.opp]["owner"], "r1")

    def test_check_order_manager_before_new_owner(self):
        # rep actor: PermissionError even though new_owner is unknown.
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.opp, "ghost", "r1")

    def test_check_order_new_owner_valid_before_stage(self):
        self.crm.advance(self.opp, "lost", "r1")
        # unknown new_owner (ValueError, check 3) precedes final-stage
        # (also ValueError, check 4); both are ValueError either way.
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "ghost", "m1")

    def test_transfer_moves_opp_load(self):
        crm = CRM([rep("r1", 2), rep("r2", 2), mgr("m")])
        l = crm.add_lead("a@corp.com", "A", "referral", "m")
        crm.qualify(l, "r1")
        o = crm.convert(l, 100, "r1")
        crm.transfer(o, "r2", "m")
        self.assertEqual(crm.opps[o]["owner"], "r2")

    def test_transfer_frees_previous_owner(self):
        self.crm.transfer(self.opp, "r2", "m1")
        # No assign entries: a non-empty waiting queue implies every rep is
        # at capacity, so a capacity-having transfer target and queued leads
        # cannot coexist. The freed slot shows up on the next add_lead.
        self.assertEqual(
            [e for e in self.crm.log if e[0] == "assign"], [])
        nxt = self.crm.add_lead("n@x.com", "N", "web", "m1")
        # r1 now has load 0, r2 has load 1 -> r1 takes the new lead.
        self.assertEqual(self.crm.leads[nxt]["owner"], "r1")

    def test_failed_transfer_changes_nothing(self):
        before = list(self.crm.log)
        with self.assertRaises(ValueError):
            self.crm.transfer(self.opp, "m1", "m1")
        self.assertEqual(self.crm.opps[self.opp]["owner"], "r1")
        self.assertEqual(self.crm.log, before)


class TestLoadAccounting(unittest.TestCase):
    def test_converted_lead_frees_lead_slot_but_opp_counts(self):
        crm = CRM([rep("r1", 1), mgr("m")])
        l1 = crm.add_lead("1@x.com", "1", "referral", "m")
        l2 = crm.add_lead("2@x.com", "2", "web", "m")  # queued
        crm.qualify(l1, "r1")
        o1 = crm.convert(l1, 100, "r1")
        self.assertIsNone(crm.leads[l2]["owner"])
        crm.advance(o1, "proposal", "r1")
        self.assertIsNone(crm.leads[l2]["owner"])
        crm.advance(o1, "negotiation", "m")
        self.assertIsNone(crm.leads[l2]["owner"])
        crm.advance(o1, "won", "m")
        self.assertEqual(crm.leads[l2]["owner"], "r1")
        self.assertEqual(crm.leads[l2]["status"], "new")

    def test_qualify_does_not_change_load(self):
        crm = CRM([rep("r1", 1), mgr("m")])
        l1 = crm.add_lead("1@x.com", "1", "referral", "m")
        l2 = crm.add_lead("2@x.com", "2", "web", "m")  # queued
        crm.qualify(l1, "r1")  # new -> qualified still counts toward load
        self.assertIsNone(crm.leads[l2]["owner"])

    def test_won_lost_opps_stop_counting(self):
        crm = CRM([rep("r1", 2), mgr("m")])
        l1 = crm.add_lead("1@x.com", "1", "referral", "m")
        l2 = crm.add_lead("2@x.com", "2", "referral", "m")
        crm.qualify(l1, "r1")
        o1 = crm.convert(l1, 100, "r1")  # r1 load: l2 + o1 = 2
        l3 = crm.add_lead("3@x.com", "3", "web", "m")  # queued (r1 full)
        crm.advance(o1, "proposal", "r1")
        crm.advance(o1, "negotiation", "m")
        crm.advance(o1, "won", "m")
        self.assertEqual(crm.leads[l3]["owner"], "r1")
        # r1 now holds l2 (qualified) and l3 (new) -> full again.
        l4 = crm.add_lead("4@x.com", "4", "web", "m")
        self.assertIsNone(crm.leads[l4]["owner"])


class TestForecast(unittest.TestCase):
    def build(self):
        crm = CRM([rep("r1", 10), rep("r2", 10), mgr("m")])

        def pipeline(email, amount):
            l = crm.add_lead(email, "N", "referral", "m")
            crm.qualify(l, "m")
            return crm.convert(l, amount, "m")

        p = pipeline("p@x.com", 1000)   # prospect
        pr = pipeline("pr@x.com", 2000)
        crm.advance(pr, "proposal", "m")
        ng = pipeline("ng@x.com", 3000)
        crm.advance(ng, "proposal", "m")
        crm.advance(ng, "negotiation", "m")
        w = pipeline("w@x.com", 4000)
        crm.advance(w, "proposal", "m")
        crm.advance(w, "negotiation", "m")
        crm.advance(w, "won", "m")
        lost = pipeline("lo@x.com", 9000)
        crm.advance(lost, "lost", "m")
        return crm

    def test_mixed_book(self):
        result = self.build().forecast()
        self.assertEqual(result, {
            "open": 3,
            "weighted": 100 + 600 + 1800,
            "won": 4000,
        })

    def test_forecast_no_log_entry(self):
        crm = self.build()
        before = list(crm.log)
        crm.forecast()
        self.assertEqual(crm.log, before)

    def test_discount_changes_weighted_amount(self):
        crm = CRM([rep("r1", 1), mgr("m")])
        l = crm.add_lead("a@x.com", "A", "referral", "m")
        crm.qualify(l, "r1")
        o = crm.convert(l, 1000, "r1")
        crm.discount(o, 10, "r1")
        self.assertEqual(crm.forecast()["weighted"], 90)  # 900*10//100

    def test_integer_weights_floor_division(self):
        crm = CRM([rep("r1", 1), mgr("m")])
        l = crm.add_lead("a@x.com", "A", "referral", "m")
        crm.qualify(l, "r1")
        o = crm.convert(l, 999, "r1")
        self.assertEqual(crm.forecast()["weighted"], 99)  # 999*10//100

    def test_empty_book(self):
        crm = CRM([rep("r1", 1), mgr("m")])
        crm.add_lead("a@x.com", "A", "web", "m")
        self.assertEqual(
            crm.forecast(), {"open": 0, "weighted": 0, "won": 0})


if __name__ == "__main__":
    unittest.main()
