import itertools
import unittest

from crm import CRM, DuplicateLeadError

_seq = itertools.count(1)


def make_crm(cap1=2, cap2=2):
    return CRM(
        [
            {"id": "r1", "role": "rep", "capacity": cap1},
            {"id": "r2", "role": "rep", "capacity": cap2},
            {"id": "m1", "role": "manager", "capacity": 0},
        ]
    )


def new_lead(crm, source="referral", domain="corp.example.com", name="Ada", actor="m1"):
    return crm.add_lead("user%d@%s" % (next(_seq), domain), name, source, actor)


def new_opp(crm, amount=1000, actor="m1", **kwargs):
    lead_id = new_lead(crm, **kwargs)
    crm.qualify(lead_id, actor)
    return lead_id, crm.convert(lead_id, amount, actor)


class AddLeadTests(unittest.TestCase):
    def test_lead_fields_normalization_and_log(self):
        crm = make_crm()
        lead_id = crm.add_lead("  Alice@Gmail.COM ", "  Alice  ", "web", "r1")
        self.assertEqual(lead_id, "L1")
        self.assertEqual(
            crm.leads["L1"],
            {
                "id": "L1",
                "email": "alice@gmail.com",
                "name": "Alice",
                "source": "web",
                "score": 10,
                "owner": "r1",
                "status": "new",
            },
        )
        self.assertEqual(crm.log, [("add_lead", "L1", "r1")])

    def test_scoring_matrix(self):
        crm = make_crm(5, 5)
        cases = [
            ("web", "gmail.com", 10),
            ("referral", "gmail.com", 30),
            ("event", "gmail.com", 20),
            ("web", "acme.io", 25),
            ("referral", "acme.io", 45),
            ("event", "acme.io", 35),
            ("web", "outlook.com", 10),
            ("web", "yahoo.com", 10),
        ]
        for index, (source, domain, score) in enumerate(cases):
            lead_id = crm.add_lead("s%d@%s" % (index, domain), "N", source, "m1")
            self.assertEqual(crm.leads[lead_id]["score"], score, (source, domain))

    def test_email_validation(self):
        crm = make_crm()
        invalid = [
            123,
            None,
            ["a@b.co"],
            "",
            "   ",
            "alice",
            "alice.example.com",
            "a@@b.com",
            "a@b@c.com",
            "@b.com",
            "a@",
            "a@.com",
            "a@com.",
            "a@com",
            "a@.com.",
        ]
        for email in invalid:
            with self.assertRaises(ValueError, msg=repr(email)):
                crm.add_lead(email, "Ada", "web", "r1")
        self.assertEqual(crm.leads, {})
        self.assertEqual(crm.log, [])

    def test_email_valid_variants(self):
        crm = make_crm(5, 5)
        for index, email in enumerate(["a@b.co", "A@B.C", "  x@y.z  ", "q@a-b.io"]):
            lead_id = crm.add_lead(email, "Ada", "web", "m1")
            self.assertEqual(crm.leads[lead_id]["email"], email.strip().lower())

    def test_name_validation(self):
        crm = make_crm()
        for name in ["", "   ", None, 5, ["Ada"]]:
            with self.assertRaises(ValueError, msg=repr(name)):
                crm.add_lead("a@b.co", name, "web", "r1")
        self.assertEqual(crm.log, [])

    def test_source_validation(self):
        crm = make_crm()
        for source in ["phone", "WEB", "", None, ["web"]]:
            with self.assertRaises(ValueError, msg=repr(source)):
                crm.add_lead("a@b.co", "Ada", source, "r1")
        self.assertEqual(crm.log, [])

    def test_duplicate_email_case_insensitive(self):
        crm = make_crm()
        first = crm.add_lead("dup@corp.example.com", "One", "web", "r1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            crm.add_lead("  DUP@Corp.Example.COM ", "Two", "event", "r1")
        self.assertEqual(ctx.exception.existing_id, first)
        self.assertEqual(len(crm.leads), 1)
        self.assertEqual(len(crm.log), 1)

    def test_name_check_runs_before_duplicate_check(self):
        crm = make_crm()
        crm.add_lead("dup@corp.example.com", "One", "web", "r1")
        with self.assertRaises(ValueError):
            crm.add_lead("dup@corp.example.com", "   ", "web", "r1")

    def test_source_check_runs_before_duplicate_check(self):
        crm = make_crm()
        crm.add_lead("dup@corp.example.com", "One", "web", "r1")
        with self.assertRaises(ValueError):
            crm.add_lead("dup@corp.example.com", "Two", "bogus", "r1")

    def test_lead_ids_count_only_successful_creations(self):
        crm = make_crm()
        self.assertEqual(crm.add_lead("a@corp.example.com", "A", "web", "r1"), "L1")
        with self.assertRaises(DuplicateLeadError):
            crm.add_lead("a@corp.example.com", "A", "web", "r1")
        with self.assertRaises(ValueError):
            crm.add_lead("bad", "A", "web", "r1")
        self.assertEqual(crm.add_lead("b@corp.example.com", "B", "web", "r1"), "L2")

    def test_actor_checked_first(self):
        crm = make_crm()
        with self.assertRaises(PermissionError):
            crm.add_lead(123, None, "bogus", "ghost")
        with self.assertRaises(PermissionError):
            crm.add_lead("a@b.co", "Ada", "web", None)
        self.assertEqual(crm.leads, {})
        self.assertEqual(crm.log, [])


class RoutingTests(unittest.TestCase):
    def test_tie_break_uses_string_order(self):
        crm = CRM(
            [
                {"id": "r2", "role": "rep", "capacity": 5},
                {"id": "r10", "role": "rep", "capacity": 5},
            ]
        )
        first = crm.add_lead("a@corp.example.com", "A", "web", "r2")
        second = crm.add_lead("b@corp.example.com", "B", "web", "r2")
        self.assertEqual(crm.leads[first]["owner"], "r10")
        self.assertEqual(crm.leads[second]["owner"], "r2")

    def test_lowest_load_wins(self):
        crm = make_crm(5, 5)
        first = crm.add_lead("a@corp.example.com", "A", "web", "m1")
        second = crm.add_lead("b@corp.example.com", "B", "web", "m1")
        third = crm.add_lead("c@corp.example.com", "C", "web", "m1")
        self.assertEqual(crm.leads[first]["owner"], "r1")
        self.assertEqual(crm.leads[second]["owner"], "r2")
        self.assertEqual(crm.leads[third]["owner"], "r1")

    def test_managers_never_own(self):
        crm = CRM([{"id": "m1", "role": "manager", "capacity": 10}])
        lead_id = crm.add_lead("a@corp.example.com", "A", "web", "m1")
        self.assertIsNone(crm.leads[lead_id]["owner"])

    def test_full_reps_push_lead_to_fifo_queue(self):
        crm = make_crm(1, 1)
        ids = [
            crm.add_lead("%s@corp.example.com" % name, "N", "web", "m1")
            for name in "abcd"
        ]
        self.assertEqual(crm.leads[ids[0]]["owner"], "r1")
        self.assertEqual(crm.leads[ids[1]]["owner"], "r2")
        self.assertIsNone(crm.leads[ids[2]]["owner"])
        self.assertIsNone(crm.leads[ids[3]]["owner"])
        self.assertEqual(
            crm.log,
            [("add_lead", lead_id, "m1") for lead_id in ids],
        )

    def test_won_frees_slot_and_assigns_fifo_until_capacity(self):
        crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 2},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        lead1 = crm.add_lead("one@corp.example.com", "One", "referral", "m1")
        crm.add_lead("two@corp.example.com", "Two", "web", "m1")
        waiting = [
            crm.add_lead("%s@corp.example.com" % name, name, "web", "m1")
            for name in ("three", "four", "five")
        ]
        self.assertTrue(all(crm.leads[w]["owner"] is None for w in waiting))

        crm.qualify(lead1, "m1")
        opp_id = crm.convert(lead1, 1000, "m1")
        for stage in ("proposal", "negotiation", "won"):
            crm.advance(opp_id, stage, "m1")

        self.assertEqual(crm.opps[opp_id]["stage"], "won")
        self.assertEqual(crm.leads[waiting[0]]["owner"], "r1")
        self.assertIsNone(crm.leads[waiting[1]]["owner"])
        self.assertIsNone(crm.leads[waiting[2]]["owner"])
        self.assertEqual(
            crm.log[-2:],
            [("advance", opp_id, "m1"), ("assign", waiting[0], "system")],
        )

    def test_lost_also_frees_slot(self):
        crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 1},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        lead_id, opp_id = new_opp(crm)
        waiting = new_lead(crm, source="web", name="Waiting")
        self.assertIsNone(crm.leads[waiting]["owner"])
        crm.advance(opp_id, "lost", "m1")
        self.assertEqual(crm.leads[waiting]["owner"], "r1")


class QualifyTests(unittest.TestCase):
    def test_missing_lead(self):
        crm = make_crm()
        with self.assertRaises(ValueError):
            crm.qualify("L99", "m1")
        with self.assertRaises(ValueError):
            crm.qualify(None, "m1")

    def test_permission(self):
        crm = make_crm()
        lead_id = new_lead(crm, source="referral", name="A")
        owner = crm.leads[lead_id]["owner"]
        other = "r2" if owner == "r1" else "r1"
        with self.assertRaises(PermissionError):
            crm.qualify(lead_id, other)
        self.assertEqual(crm.leads[lead_id]["status"], "new")

    def test_manager_can_qualify_others_lead(self):
        crm = make_crm()
        lead_id = new_lead(crm, source="referral", name="A")
        crm.qualify(lead_id, "m1")
        self.assertEqual(crm.leads[lead_id]["status"], "qualified")
        self.assertEqual(crm.log[-1], ("qualify", lead_id, "m1"))

    def test_status_check_before_score_check(self):
        crm = make_crm()
        lead_id = new_lead(crm, source="referral", name="A")
        crm.qualify(lead_id, "m1")
        with self.assertRaises(ValueError):
            crm.qualify(lead_id, "m1")

    def test_low_score_rejected(self):
        crm = make_crm()
        lead_id = new_lead(crm, source="web", domain="gmail.com", name="A")
        with self.assertRaises(ValueError):
            crm.qualify(lead_id, crm.leads[lead_id]["owner"])
        self.assertEqual(crm.leads[lead_id]["status"], "new")

    def test_score_exactly_thirty_allowed(self):
        crm = make_crm()
        lead_id = new_lead(crm, source="referral", domain="gmail.com", name="A")
        crm.qualify(lead_id, crm.leads[lead_id]["owner"])
        self.assertEqual(crm.leads[lead_id]["status"], "qualified")

    def test_permission_before_score(self):
        crm = make_crm()
        lead_id = new_lead(crm, source="web", domain="gmail.com", name="A")
        owner = crm.leads[lead_id]["owner"]
        other = "r2" if owner == "r1" else "r1"
        with self.assertRaises(PermissionError):
            crm.qualify(lead_id, other)


class ConvertTests(unittest.TestCase):
    def test_missing_lead(self):
        crm = make_crm()
        with self.assertRaises(ValueError):
            crm.convert("L99", 100, "m1")

    def test_amount_validation_before_permission(self):
        crm = make_crm()
        lead_id = new_lead(crm, source="referral", name="A")
        owner = crm.leads[lead_id]["owner"]
        other = "r2" if owner == "r1" else "r1"
        for amount in (0, -1, True, False, 1.5, "100", None, [100]):
            with self.assertRaises(ValueError, msg=repr(amount)):
                crm.convert(lead_id, amount, other)
        self.assertEqual(crm.opps, {})

    def test_permission_before_status(self):
        crm = make_crm()
        lead_id = new_lead(crm, source="referral", name="A")
        owner = crm.leads[lead_id]["owner"]
        other = "r2" if owner == "r1" else "r1"
        with self.assertRaises(PermissionError):
            crm.convert(lead_id, 100, other)

    def test_requires_qualified(self):
        crm = make_crm()
        lead_id = new_lead(crm, source="referral", name="A")
        with self.assertRaises(ValueError):
            crm.convert(lead_id, 100, crm.leads[lead_id]["owner"])

    def test_creates_opportunity(self):
        crm = make_crm()
        lead_id = new_lead(crm, source="referral", name="A")
        crm.qualify(lead_id, "m1")
        owner = crm.leads[lead_id]["owner"]
        opp_id = crm.convert(lead_id, 1500, "m1")
        self.assertEqual(opp_id, "O1")
        self.assertEqual(
            crm.opps["O1"],
            {
                "id": "O1",
                "lead_id": lead_id,
                "owner": owner,
                "amount": 1500,
                "original_amount": 1500,
                "stage": "prospect",
            },
        )
        self.assertEqual(crm.leads[lead_id]["status"], "converted")
        self.assertEqual(crm.log[-1], ("convert", "O1", "m1"))

    def test_opportunity_ids_count_successful_conversions(self):
        crm = make_crm(5, 5)
        _, first = new_opp(crm)
        _, second = new_opp(crm)
        self.assertEqual((first, second), ("O1", "O2"))

    def test_ownerless_qualified_lead_cannot_convert(self):
        crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 1},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        crm.add_lead("busy@corp.example.com", "Busy", "referral", "m1")
        waiting = crm.add_lead("waiting@corp.example.com", "Waiting", "referral", "m1")
        self.assertIsNone(crm.leads[waiting]["owner"])
        crm.qualify(waiting, "m1")
        with self.assertRaises(ValueError):
            crm.convert(waiting, 500, "m1")
        self.assertEqual(crm.opps, {})
        self.assertEqual(crm.leads[waiting]["status"], "qualified")


class AdvanceTests(unittest.TestCase):
    def test_missing_opportunity(self):
        crm = make_crm()
        with self.assertRaises(ValueError):
            crm.advance("O99", "proposal", "m1")

    def test_stage_validation_before_permission(self):
        crm = make_crm()
        _, opp_id = new_opp(crm)
        with self.assertRaises(ValueError):
            crm.advance(opp_id, "bogus", "r2")
        with self.assertRaises(ValueError):
            crm.advance(opp_id, None, "r2")
        self.assertEqual(crm.opps[opp_id]["stage"], "prospect")

    def test_permission(self):
        crm = make_crm()
        _, opp_id = new_opp(crm)
        owner = crm.opps[opp_id]["owner"]
        other = "r2" if owner == "r1" else "r1"
        with self.assertRaises(PermissionError):
            crm.advance(opp_id, "proposal", other)

    def test_forward_path_and_skips(self):
        crm = make_crm()
        _, opp_id = new_opp(crm)
        for skipped in ("negotiation", "won"):
            with self.assertRaises(ValueError):
                crm.advance(opp_id, skipped, "m1")
        self.assertEqual(crm.opps[opp_id]["stage"], "prospect")
        crm.advance(opp_id, "proposal", "m1")
        crm.advance(opp_id, "negotiation", "m1")
        crm.advance(opp_id, "won", "m1")
        self.assertEqual(crm.opps[opp_id]["stage"], "won")
        with self.assertRaises(ValueError):
            crm.advance(opp_id, "lost", "m1")

    def test_same_stage_rejected(self):
        crm = make_crm()
        _, opp_id = new_opp(crm)
        with self.assertRaises(ValueError):
            crm.advance(opp_id, "prospect", "m1")

    def test_lost_from_any_open_stage(self):
        crm = make_crm(5, 5)
        _, prospect_opp = new_opp(crm)
        _, proposal_opp = new_opp(crm)
        crm.advance(proposal_opp, "proposal", "m1")
        crm.advance(prospect_opp, "lost", "m1")
        crm.advance(proposal_opp, "lost", "m1")
        self.assertEqual(crm.opps[prospect_opp]["stage"], "lost")
        self.assertEqual(crm.opps[proposal_opp]["stage"], "lost")

    def test_large_negotiation_needs_manager(self):
        crm = make_crm()
        lead_id, opp_id = new_opp(crm, amount=50001)
        owner = crm.opps[opp_id]["owner"]
        crm.advance(opp_id, "proposal", owner)
        with self.assertRaises(PermissionError):
            crm.advance(opp_id, "negotiation", owner)
        self.assertEqual(crm.opps[opp_id]["stage"], "proposal")
        crm.advance(opp_id, "negotiation", "m1")
        self.assertEqual(crm.opps[opp_id]["stage"], "negotiation")
        self.assertEqual(crm.leads[lead_id]["status"], "converted")

    def test_exactly_fifty_thousand_allowed_for_rep(self):
        crm = make_crm()
        _, opp_id = new_opp(crm, amount=50000)
        owner = crm.opps[opp_id]["owner"]
        crm.advance(opp_id, "proposal", owner)
        crm.advance(opp_id, "negotiation", owner)
        self.assertEqual(crm.opps[opp_id]["stage"], "negotiation")

    def test_gate_uses_current_amount(self):
        crm = make_crm()
        _, opp_id = new_opp(crm, amount=60000)
        owner = crm.opps[opp_id]["owner"]
        crm.advance(opp_id, "proposal", owner)
        crm.discount(opp_id, 20, "m1")
        self.assertEqual(crm.opps[opp_id]["amount"], 48000)
        crm.advance(opp_id, "negotiation", owner)
        self.assertEqual(crm.opps[opp_id]["stage"], "negotiation")

    def test_log_untouched_on_failure(self):
        crm = make_crm()
        _, opp_id = new_opp(crm)
        before = list(crm.log)
        with self.assertRaises(PermissionError):
            crm.advance(opp_id, "proposal", "r2")
        with self.assertRaises(ValueError):
            crm.advance(opp_id, "won", "m1")
        self.assertEqual(crm.log, before)


class DiscountTests(unittest.TestCase):
    def test_missing_opportunity(self):
        crm = make_crm()
        with self.assertRaises(ValueError):
            crm.discount("O99", 5, "m1")

    def test_pct_validation_before_permission(self):
        crm = make_crm()
        _, opp_id = new_opp(crm)
        for pct in (0, 31, -1, True, False, 5.0, "5", None, [5]):
            with self.assertRaises(ValueError, msg=repr(pct)):
                crm.discount(opp_id, pct, "r2")
        self.assertEqual(crm.opps[opp_id]["amount"], 1000)

    def test_permission(self):
        crm = make_crm()
        _, opp_id = new_opp(crm)
        owner = crm.opps[opp_id]["owner"]
        other = "r2" if owner == "r1" else "r1"
        with self.assertRaises(PermissionError):
            crm.discount(opp_id, 5, other)

    def test_rep_discount_limit(self):
        crm = make_crm()
        _, opp_id = new_opp(crm)
        owner = crm.opps[opp_id]["owner"]
        crm.discount(opp_id, 10, owner)
        self.assertEqual(crm.opps[opp_id]["amount"], 900)
        with self.assertRaises(PermissionError):
            crm.discount(opp_id, 11, owner)
        crm.discount(opp_id, 11, "m1")
        self.assertLess(crm.opps[opp_id]["amount"], 900)

    def test_final_stage_checked_before_rep_limit(self):
        crm = make_crm()
        _, opp_id = new_opp(crm)
        crm.advance(opp_id, "lost", "m1")
        with self.assertRaises(ValueError):
            crm.discount(opp_id, 20, crm.opps[opp_id]["owner"])

    def test_cumulative_cap(self):
        crm = make_crm()
        _, opp_id = new_opp(crm, amount=1000)
        crm.discount(opp_id, 30, "m1")
        self.assertEqual(crm.opps[opp_id]["amount"], 700)
        with self.assertRaises(ValueError):
            crm.discount(opp_id, 1, "m1")
        self.assertEqual(crm.opps[opp_id]["amount"], 700)
        self.assertEqual(crm.opps[opp_id]["original_amount"], 1000)

    def test_floor_division(self):
        crm = make_crm()
        _, opp_id = new_opp(crm, amount=999)
        crm.discount(opp_id, 10, "m1")
        self.assertEqual(crm.opps[opp_id]["amount"], 899)
        self.assertEqual(crm.log[-1], ("discount", opp_id, "m1"))


class TransferTests(unittest.TestCase):
    def test_missing_opportunity(self):
        crm = make_crm()
        with self.assertRaises(ValueError):
            crm.transfer("O99", "r1", "m1")

    def test_manager_only(self):
        crm = make_crm()
        _, opp_id = new_opp(crm)
        owner = crm.opps[opp_id]["owner"]
        with self.assertRaises(PermissionError):
            crm.transfer(opp_id, owner, owner)
        with self.assertRaises(PermissionError):
            crm.transfer(opp_id, "ghost", owner)

    def test_target_validation(self):
        crm = make_crm()
        _, opp_id = new_opp(crm)
        for target in ("ghost", "m1", None, 5, ["r1"]):
            with self.assertRaises(ValueError, msg=repr(target)):
                crm.transfer(opp_id, target, "m1")

    def test_same_owner_rejected(self):
        crm = make_crm()
        _, opp_id = new_opp(crm)
        owner = crm.opps[opp_id]["owner"]
        with self.assertRaises(ValueError):
            crm.transfer(opp_id, owner, "m1")

    def test_final_stage_rejected(self):
        crm = make_crm(5, 5)
        _, opp_id = new_opp(crm)
        owner = crm.opps[opp_id]["owner"]
        other = "r2" if owner == "r1" else "r1"
        crm.advance(opp_id, "lost", "m1")
        with self.assertRaises(ValueError):
            crm.transfer(opp_id, other, "m1")

    def test_capacity_rejected(self):
        crm = make_crm(1, 1)
        _, opp_id = new_opp(crm)
        owner = crm.opps[opp_id]["owner"]
        other = "r2" if owner == "r1" else "r1"
        new_lead(crm, name="Filler")
        self.assertGreaterEqual(crm._load(other), 1)
        with self.assertRaises(ValueError):
            crm.transfer(opp_id, other, "m1")
        self.assertEqual(crm.opps[opp_id]["owner"], owner)

    def test_successful_transfer(self):
        crm = make_crm(1, 5)
        lead_id, opp_id = new_opp(crm)
        owner = crm.opps[opp_id]["owner"]
        other = "r2" if owner == "r1" else "r1"
        crm.transfer(opp_id, other, "m1")
        self.assertEqual(crm.opps[opp_id]["owner"], other)
        self.assertEqual(crm.log[-1], ("transfer", opp_id, "m1"))
        self.assertEqual(crm.leads[lead_id]["status"], "converted")

    def test_transfer_frees_previous_owner_slot(self):
        crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 1},
                {"id": "r2", "role": "rep", "capacity": 5},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        _, opp_id = new_opp(crm)
        owner = crm.opps[opp_id]["owner"]
        self.assertEqual(owner, "r1")
        self.assertEqual(crm._load("r1"), 1)
        # Force the documented waiting-queue state: r1 is freed by the transfer
        # while a lead waits, and r2 still has spare capacity.
        waiting = new_lead(crm, name="Waiting")
        crm.leads[waiting]["owner"] = None
        crm._waiting.append(waiting)
        crm.transfer(opp_id, "r2", "m1")
        self.assertEqual(crm.leads[waiting]["owner"], "r1")
        self.assertEqual(crm.log[-1], ("assign", waiting, "system"))


class ForecastTests(unittest.TestCase):
    def test_empty(self):
        crm = make_crm()
        self.assertEqual(crm.forecast(), {"open": 0, "weighted": 0, "won": 0})

    def test_mixed_pipeline(self):
        crm = make_crm(5, 5)
        _, prospect_opp = new_opp(crm, amount=1000)
        _, proposal_opp = new_opp(crm, amount=999)
        crm.advance(proposal_opp, "proposal", "m1")
        _, negotiation_opp = new_opp(crm, amount=1000)
        crm.advance(negotiation_opp, "proposal", "m1")
        crm.advance(negotiation_opp, "negotiation", "m1")
        _, won_opp = new_opp(crm, amount=2500)
        for stage in ("proposal", "negotiation", "won"):
            crm.advance(won_opp, stage, "m1")
        _, lost_opp = new_opp(crm, amount=5000)
        crm.advance(lost_opp, "lost", "m1")

        before = list(crm.log)
        self.assertEqual(
            crm.forecast(), {"open": 3, "weighted": 100 + 299 + 600, "won": 2500}
        )
        self.assertEqual(crm.log, before)

    def test_uses_current_amount_after_discount(self):
        crm = make_crm()
        _, opp_id = new_opp(crm, amount=1000)
        crm.discount(opp_id, 30, "m1")
        self.assertEqual(crm.forecast(), {"open": 1, "weighted": 70, "won": 0})


if __name__ == "__main__":
    unittest.main()
