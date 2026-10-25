"""Unit tests for crm.py per /tmp/aep-lab/specs/crm.md.

Fixture note: owner assignment picks the rep with the LOWEST load among reps
below capacity (ties -> smallest id in string order), so each fixture below
asserts the owner it expects right after creating leads/opportunities.
"""

import unittest

from crm import CRM, DuplicateLeadError


def make_crm():
    """Default fixture: high-capacity rep r1, a rep r2 with capacity 0 (known
    user, never an owner), and a manager."""
    return CRM(
        [
            {"id": "r1", "role": "rep", "capacity": 100},
            {"id": "r2", "role": "rep", "capacity": 0},
            {"id": "m1", "role": "manager", "capacity": 0},
        ]
    )


def qi(crm, source="web", email="a@gmail.com"):
    """Add a lead with a manager actor; returns the id."""
    return crm.add_lead(email, "Name", source, "m1")


def qo(crm, lead_id, amount=10):
    """Qualify + convert quickly with the manager; returns the opportunity id."""
    crm.qualify(lead_id, "m1")
    return crm.convert(lead_id, amount, "m1")


class TestAddLead(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()

    def test_ids_and_log(self):
        self.assertEqual(self.crm.add_lead("a@gmail.com", "Ann", "web", "m1"), "L1")
        self.assertEqual(self.crm.add_lead("b@gmail.com", "Bob", "web", "m1"), "L2")
        self.assertEqual(self.crm.log, [("add_lead", "L1", "m1"), ("add_lead", "L2", "m1")])

    def test_normalization(self):
        lead_id = self.crm.add_lead("  GoOd@Example.COM  ", "  Ann  ", "web", "m1")
        lead = self.crm.leads[lead_id]
        self.assertEqual(lead["email"], "good@example.com")
        self.assertEqual(lead["name"], "Ann")

    def test_email_validation(self):
        for bad in [
            123,
            "",
            "no-at-sign.com",
            "@b.com",
            "a@",
            "a@b@c.com",
            "a@b",
            "a@b.",
            "a@.b",
        ]:
            with self.subTest(email=bad):
                with self.assertRaises(ValueError):
                    self.crm.add_lead(bad, "Ann", "web", "m1")
        self.assertEqual(self.crm.leads, {})
        self.assertEqual(self.crm.log, [])

    def test_valid_emails_accepted(self):
        for good in ["a@b.com", " x @Foo.COM ", "user.name@sub.example.org"]:
            with self.subTest(email=good):
                self.crm.add_lead(good, "A", "web", "m1")
        self.assertEqual(len(self.crm.leads), 3)

    def test_name_validation(self):
        for bad in [123, "", "   "]:
            with self.subTest(name=bad):
                with self.assertRaises(ValueError):
                    self.crm.add_lead("a@gmail.com", bad, "web", "m1")
        self.assertEqual(self.crm.log, [])

    def test_source_validation(self):
        with self.assertRaises(ValueError):
            self.crm.add_lead("a@gmail.com", "Ann", "other", "m1")
        self.assertEqual(self.crm.log, [])

    def test_duplicate_email(self):
        self.crm.add_lead("a@gmail.com", "Ann", "web", "m1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            self.crm.add_lead("  A@GMAIL.COM ", "Other", "referral", "m1")
        self.assertEqual(ctx.exception.existing_id, "L1")
        self.assertEqual(len(self.crm.leads), 1)  # nothing added

    def test_failed_add_does_not_consume_id(self):
        self.crm.add_lead("a@gmail.com", "Ann", "web", "m1")
        with self.assertRaises(DuplicateLeadError):
            self.crm.add_lead("a@gmail.com", "Ann", "web", "m1")
        self.assertEqual(self.crm.add_lead("b@gmail.com", "Bob", "web", "m1"), "L2")

    def test_scores(self):
        cases = [
            ("web", "a@gmail.com", 10),
            ("web", "b@corp.com", 25),
            ("referral", "c@gmail.com", 30),
            ("referral", "d@corp.com", 45),
            ("event", "e@gmail.com", 20),
            ("event", "f@corp.com", 35),
        ]
        for source, email, expected in cases:
            with self.subTest(source=source, email=email):
                lead_id = self.crm.add_lead(email, "X", source, "m1")
                self.assertEqual(self.crm.leads[lead_id]["score"], expected)

    def test_free_domains_no_bonus(self):
        crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 3},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        for email in ["a@outlook.com", "b@yahoo.com", "c@corp.org"]:
            lead_id = crm.add_lead(email, "X", "web", "m1")
            want = 25 if email == "c@corp.org" else 10
            self.assertEqual(crm.leads[lead_id]["score"], want)

    def test_owner_assignment_lowest_load(self):
        # r1 capacity 2, r2 capacity 1; both start at load 0 -> tie -> r1.
        crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 2},
                {"id": "r2", "role": "rep", "capacity": 1},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        leads = [
            crm.add_lead("%s@gmail.com" % name, "X", "referral", "m1")
            for name in ("a", "b", "c", "d", "e")
        ]
        # L1: tie at load 0 -> r1 (load 1). L2: r2 has load 0 -> r2 (load 1).
        # L3: tie at load 1 -> r1 (load 2). L4: both full -> queued.
        self.assertEqual(crm.leads[leads[0]]["owner"], "r1")
        self.assertEqual(crm.leads[leads[1]]["owner"], "r2")
        self.assertEqual(crm.leads[leads[2]]["owner"], "r1")
        self.assertIsNone(crm.leads[leads[3]]["owner"])
        self.assertIsNone(crm.leads[leads[4]]["owner"])
        self.assertEqual(crm.log, [("add_lead", lead_id, "m1") for lead_id in leads])

    def test_owner_tie_smallest_id(self):
        crm = CRM(
            [
                {"id": "zz", "role": "rep", "capacity": 2},
                {"id": "aa", "role": "rep", "capacity": 2},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        lead_id = crm.add_lead("a@gmail.com", "A", "web", "m1")
        self.assertEqual(crm.leads[lead_id]["owner"], "aa")

    def test_zero_capacity_rep_queues_lead(self):
        crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 0},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        lead_id = crm.add_lead("a@gmail.com", "A", "web", "m1")
        self.assertIsNone(crm.leads[lead_id]["owner"])

    def test_lead_fields(self):
        lead_id = self.crm.add_lead("a@gmail.com", "Ann", "referral", "m1")
        lead = self.crm.leads[lead_id]
        self.assertEqual(
            lead,
            {
                "id": lead_id,
                "email": "a@gmail.com",
                "name": "Ann",
                "source": "referral",
                "score": 30,
                "owner": "r1",
                "status": "new",
            },
        )

    def test_unknown_actor_raises_first(self):
        # Actor check precedes every other validation.
        with self.assertRaises(PermissionError):
            self.crm.add_lead(123, "", "nope", "nobody")
        self.assertEqual(self.crm.log, [])


class TestQualify(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()

    def test_success(self):
        lead_id = qi(self.crm, source="referral")
        self.crm.qualify(lead_id, "r1")
        self.assertEqual(self.crm.leads[lead_id]["status"], "qualified")
        self.assertEqual(self.crm.log, [("add_lead", lead_id, "m1"), ("qualify", lead_id, "r1")])

    def test_manager_can_qualify(self):
        lead_id = qi(self.crm, source="referral")
        self.crm.qualify(lead_id, "m1")

    def test_non_owner_rep_denied(self):
        lead_id = qi(self.crm, source="referral")
        with self.assertRaises(PermissionError):
            self.crm.qualify(lead_id, "r2")  # known rep, but not the owner
        self.assertEqual(self.crm.leads[lead_id]["status"], "new")
        self.assertEqual(self.crm.log, [("add_lead", lead_id, "m1")])

    def test_unknown_lead_value_error(self):
        with self.assertRaises(ValueError):
            self.crm.qualify("L99", "r1")
        with self.assertRaises(PermissionError):
            self.crm.qualify("L99", "nobody")  # actor checked first
        self.assertEqual(self.crm.log, [])

    def test_double_qualify_fails(self):
        lead_id = qi(self.crm, source="referral")
        self.crm.qualify(lead_id, "r1")
        with self.assertRaises(ValueError):
            self.crm.qualify(lead_id, "r1")
        self.assertEqual(self.crm.leads[lead_id]["status"], "qualified")
        self.assertEqual(self.crm.log[-1], ("qualify", lead_id, "r1"))  # unchanged

    def test_low_score_fails(self):
        lead_id = qi(self.crm, source="web", email="a@gmail.com")  # score 10
        with self.assertRaises(ValueError):
            self.crm.qualify(lead_id, "r1")
        self.assertEqual(self.crm.leads[lead_id]["status"], "new")
        self.assertEqual(self.crm.log, [("add_lead", lead_id, "m1")])

    def test_score_boundary(self):
        crm = make_crm()
        crm.leads["L9a"] = {
            "id": "L9a", "email": "low@gmail.com", "name": "L", "source": "web",
            "score": 29, "owner": "r1", "status": "new",
        }
        crm.leads["L9b"] = {
            "id": "L9b", "email": "ok@gmail.com", "name": "O", "source": "web",
            "score": 30, "owner": "r1", "status": "new",
        }
        with self.assertRaises(ValueError):
            crm.qualify("L9a", "r1")
        crm.qualify("L9b", "r1")
        self.assertEqual(crm.leads["L9b"]["status"], "qualified")


class TestConvert(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()

    def test_success(self):
        lead_id = qi(self.crm, source="referral")
        self.crm.qualify(lead_id, "r1")
        opp_id = self.crm.convert(lead_id, 500, "r1")
        self.assertEqual(opp_id, "O1")
        self.assertEqual(
            self.crm.opps["O1"],
            {
                "id": "O1",
                "lead_id": lead_id,
                "owner": "r1",
                "amount": 500,
                "original_amount": 500,
                "stage": "prospect",
            },
        )
        self.assertEqual(self.crm.leads[lead_id]["status"], "converted")
        self.assertEqual(
            self.crm.log,
            [("add_lead", lead_id, "m1"), ("qualify", lead_id, "r1"), ("convert", "O1", "r1")],
        )

    def test_opp_numbering_counts_successes(self):
        lead_a = qi(self.crm, source="referral", email="a@gmail.com")
        lead_b = qi(self.crm, source="referral", email="b@gmail.com")
        self.crm.qualify(lead_a, "r1")
        self.crm.qualify(lead_b, "r1")
        self.assertEqual(self.crm.convert(lead_a, 1, "r1"), "O1")
        with self.assertRaises(ValueError):
            self.crm.convert(lead_a, 1, "r1")  # already converted
        self.assertEqual(self.crm.convert(lead_b, 1, "r1"), "O2")  # no gap

    def test_amount_validation(self):
        lead_id = qi(self.crm, source="referral")
        self.crm.qualify(lead_id, "r1")
        for bad in [0, -3, True, False, 2.5, "10"]:
            with self.subTest(amount=bad):
                with self.assertRaises(ValueError):
                    self.crm.convert(lead_id, bad, "r1")
        self.assertNotIn("O1", self.crm.opps)
        self.assertEqual(self.crm.leads[lead_id]["status"], "qualified")

    def test_amount_check_precedes_permission(self):
        lead_a = qi(self.crm, source="referral", email="a@gmail.com")
        lead_b = qi(self.crm, source="referral", email="b@gmail.com")
        self.crm.qualify(lead_a, "r1")
        self.crm.qualify(lead_b, "r1")
        # lead_b is owned by r1; the invalid-amount case runs before permission.
        with self.assertRaises(ValueError):
            self.crm.convert(lead_b, 0, "r2")
        # then permission: the unauthorized rep is rejected second
        with self.assertRaises(PermissionError):
            self.crm.convert(lead_b, 10, "r2")

    def test_permission(self):
        lead_id = qi(self.crm, source="referral")
        self.crm.qualify(lead_id, "r1")
        with self.assertRaises(PermissionError):
            self.crm.convert(lead_id, 10, "r2")
        with self.assertRaises(PermissionError):
            self.crm.convert("L99", 10, "nobody")  # actor checked first
        self.assertEqual(self.crm.leads[lead_id]["status"], "qualified")

    def test_requires_qualified_status(self):
        lead_id = qi(self.crm, source="referral")  # still "new"
        with self.assertRaises(ValueError):
            self.crm.convert(lead_id, 10, "r1")
        self.assertEqual(self.crm.leads[lead_id]["status"], "new")

    def test_ownerless_lead_cannot_convert(self):
        crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 2},
                {"id": "r2", "role": "rep", "capacity": 1},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        for i in range(4):
            crm.add_lead("%d@gmail.com" % i, "X", "referral", "m1")
        self.assertIsNone(crm.leads["L4"]["owner"])  # all reps at capacity
        crm.qualify("L4", "m1")  # manager can qualify an ownerless lead
        with self.assertRaises(ValueError):
            crm.convert("L4", 10, "m1")  # check 5: no owner
        self.assertEqual(crm.leads["L4"]["status"], "qualified")
        self.assertEqual(crm.opps, {})


class TestAdvance(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        self.lead_id = qi(self.crm, source="referral")
        self.opp_id = qo(self.crm, self.lead_id)

    def test_full_happy_path(self):
        self.crm.advance(self.opp_id, "proposal", "r1")
        self.crm.advance(self.opp_id, "negotiation", "r1")
        self.crm.advance(self.opp_id, "won", "r1")
        self.assertEqual(self.crm.opps[self.opp_id]["stage"], "won")

    def test_lost_from_any_non_final_stage(self):
        for email in ["lost1@corp.com", "lost2@corp.com"]:
            lead = qi(self.crm, source="referral", email=email)
            self.crm.qualify(lead, "r1")
            opp_id = self.crm.convert(lead, 10, "r1")
            self.crm.advance(opp_id, "lost", "r1")
            self.assertEqual(self.crm.opps[opp_id]["stage"], "lost")

    def test_invalid_stage(self):
        for bad in ["negociate", "proposal2", "", 5]:
            with self.subTest(stage=bad):
                with self.assertRaises(ValueError):
                    self.crm.advance(self.opp_id, bad, "r1")
        self.assertEqual(self.crm.opps[self.opp_id]["stage"], "prospect")

    def test_check_order(self):
        # actor first (rule 0), then existence, then stage validity, then permission
        with self.assertRaises(PermissionError):
            self.crm.advance(self.opp_id, "proposal", "nobody")
        with self.assertRaises(ValueError):
            self.crm.advance("O9", "proposal", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp_id, "bogus", "r2")  # stage precedes permission
        with self.assertRaises(PermissionError):
            self.crm.advance(self.opp_id, "proposal", "r2")

    def test_permission(self):
        with self.assertRaises(PermissionError):
            self.crm.advance(self.opp_id, "proposal", "r2")
        self.assertEqual(self.crm.opps[self.opp_id]["stage"], "prospect")
        self.assertEqual(self.crm.log[-1], ("convert", self.opp_id, "m1"))

    def test_final_stage_movement_fails(self):
        self.crm.advance(self.opp_id, "proposal", "r1")
        self.crm.advance(self.opp_id, "negotiation", "r1")
        self.crm.advance(self.opp_id, "won", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance(self.opp_id, "lost", "r1")
        self.assertEqual(self.crm.opps[self.opp_id]["stage"], "won")

    def test_stage_transitions(self):
        lead = qi(self.crm, source="referral", email="b@gmail.com")
        self.crm.qualify(lead, "r1")
        opp_id = self.crm.convert(lead, 10, "r1")
        # skipping forward and going backward are invalid; "won" only from negotiation
        with self.assertRaises(ValueError):
            self.crm.advance(opp_id, "negotiation", "r1")  # skip proposal
        self.crm.advance(opp_id, "proposal", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance(opp_id, "won", "r1")  # skip negotiation
        with self.assertRaises(ValueError):
            self.crm.advance(opp_id, "prospect", "r1")  # backward
        self.assertEqual(self.crm.opps[opp_id]["stage"], "proposal")

    def test_big_negotiation_requires_manager(self):
        lead = qi(self.crm, source="referral", email="big@corp.com")
        self.crm.qualify(lead, "r1")
        big_opp = self.crm.convert(lead, 60000, "r1")
        self.crm.advance(big_opp, "proposal", "r1")
        with self.assertRaises(PermissionError):
            self.crm.advance(big_opp, "negotiation", "r1")
        self.assertEqual(self.crm.opps[big_opp]["stage"], "proposal")
        self.assertEqual(self.crm.log[-1], ("advance", big_opp, "r1"))  # log unchanged
        self.crm.advance(big_opp, "negotiation", "m1")  # manager is allowed
        self.assertEqual(self.crm.opps[big_opp]["stage"], "negotiation")

    def test_negotiation_at_50000_by_rep_ok(self):
        lead = qi(self.crm, source="referral", email="c@corp.com")
        self.crm.qualify(lead, "r1")
        opp_id = self.crm.convert(lead, 50000, "r1")
        self.crm.advance(opp_id, "proposal", "r1")
        self.crm.advance(opp_id, "negotiation", "r1")

    def test_won_frees_slot_assigns_waiting_fifo(self):
        crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 1},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        crm.add_lead("a@gmail.com", "A", "referral", "m1")  # -> r1
        crm.add_lead("b@gmail.com", "B", "referral", "m1")  # queued (r1 full)
        crm.add_lead("c@gmail.com", "C", "referral", "m1")  # queued
        self.assertIsNone(crm.leads["L3"]["owner"])
        crm.qualify("L1", "m1")
        opp_id = crm.convert("L1", 10, "m1")
        crm.advance(opp_id, "proposal", "m1")
        crm.advance(opp_id, "negotiation", "m1")
        crm.advance(opp_id, "won", "m1")
        # r1 freed; the oldest waiting lead (L2) gets the slot, not L3.
        self.assertEqual(crm.leads["L2"]["owner"], "r1")
        self.assertIsNone(crm.leads["L3"]["owner"])
        self.assertIn(("assign", "L2", "system"), crm.log)
        self.assertEqual(crm.leads["L2"]["status"], "new")

    def test_assignment_respects_capacity(self):
        crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 2},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        for name in "ab":
            crm.add_lead("%s@gmail.com" % name, name, "referral", "m1")  # both -> r1
        for name in "cde":
            crm.add_lead("%s@gmail.com" % name, name, "referral", "m1")  # queued
        crm.qualify("L1", "m1")
        opp_id = crm.convert("L1", 10, "m1")
        crm.advance(opp_id, "proposal", "m1")
        crm.advance(opp_id, "negotiation", "m1")
        crm.advance(opp_id, "won", "m1")
        # r1's load dropped to 1 (L2 remains); exactly one queued lead fits.
        self.assertEqual(crm.leads["L3"]["owner"], "r1")
        self.assertIsNone(crm.leads["L4"]["owner"])
        self.assertIsNone(crm.leads["L5"]["owner"])
        self.assertEqual(
            crm.log[-1], ("assign", "L3", "system")
        )

    def test_lost_also_frees_slot(self):
        crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 1},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        crm.add_lead("a@gmail.com", "A", "referral", "m1")
        crm.add_lead("b@gmail.com", "B", "referral", "m1")  # queued
        crm.qualify("L1", "m1")
        opp_id = crm.convert("L1", 10, "m1")
        crm.advance(opp_id, "lost", "m1")
        self.assertEqual(crm.leads["L2"]["owner"], "r1")


class TestDiscount(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        self.lead_id = qi(self.crm, source="referral")
        self.opp_id = qo(self.crm, self.lead_id, amount=1000)

    def test_success(self):
        self.crm.discount(self.opp_id, 10, "r1")
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 900)
        self.assertEqual(self.crm.opps[self.opp_id]["original_amount"], 1000)
        self.assertEqual(self.crm.log[-1], ("discount", self.opp_id, "r1"))

    def test_floor_division(self):
        lead2 = qi(self.crm, source="referral", email="b@gmail.com")
        self.crm.qualify(lead2, "r1")
        opp2 = self.crm.convert(lead2, 101, "r1")  # original_amount 101
        self.crm.discount(opp2, 10, "r1")
        self.assertEqual(self.crm.opps[opp2]["amount"], 90)  # 101*90//100 = 90
        # 90*100 = 9000 >= 101*70 = 7070, so the cumulative cap holds.

    def test_pct_validation(self):
        for bad in [0, -5, 31, True, False, 15.0, "10"]:
            with self.subTest(pct=bad):
                with self.assertRaises(ValueError):
                    self.crm.discount(self.opp_id, bad, "r1")
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 1000)

    def test_check_order(self):
        # actor, existence, pct [before permission], final [before rep cap]
        lead = qi(self.crm, source="referral", email="b@gmail.com")
        self.crm.qualify(lead, "r1")
        other_opp = self.crm.convert(lead, 1000, "r1")
        with self.assertRaises(PermissionError):
            self.crm.discount(other_opp, 10, "nobody")
        with self.assertRaises(ValueError):
            self.crm.discount("O9", 10, "r1")  # existence precedes permission
        with self.assertRaises(ValueError):
            self.crm.discount(other_opp, 0, "r2")  # pct precedes permission
        self.crm.advance(self.opp_id, "proposal", "r1")
        self.crm.advance(self.opp_id, "negotiation", "r1")
        self.crm.advance(self.opp_id, "won", "r1")
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp_id, 15, "r1")  # stage-final precedes rep cap

    def test_permission(self):
        lead = qi(self.crm, source="referral", email="b@gmail.com")
        self.crm.qualify(lead, "r1")
        other_opp = self.crm.convert(lead, 1000, "r1")
        with self.assertRaises(PermissionError):
            self.crm.discount(other_opp, 10, "OTHER_REP")
        self.assertEqual(self.crm.opps[other_opp]["amount"], 1000)

    def test_rep_cap_10(self):
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp_id, 11, "r1")
        self.crm.discount(self.opp_id, 10, "r1")  # exactly 10 is fine
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 900)

    def test_manager_discount_11(self):
        # Manager actor owns nothing, but manager is exempt from rep pct cap only
        # when allowed by check 3; discount uses owner-or-manager permission.
        crm = make_crm()
        lead = qi(crm, source="referral")
        crm.qualify(lead, "m1")
        opp_id = crm.convert(lead, 1000, "m1")
        crm.discount(opp_id, 11, "m1")
        self.assertEqual(crm.opps[opp_id]["amount"], 890)

    def test_cumulative_cap_30_percent(self):
        self.crm.discount(self.opp_id, 10, "r1")  # 1000 -> 900
        self.crm.discount(self.opp_id, 10, "r1")  # 900 -> 810
        self.crm.discount(self.opp_id, 10, "r1")  # 810 -> 729
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp_id, 10, "r1")  # 729 -> 656 < 700
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 729)
        # log = add_lead, qualify, convert, 3 discounts; the failed 4th is absent
        self.assertEqual(len(self.crm.log), 6)

    def test_cumulative_floor_exactly_30(self):
        # pct 30 exceeds the rep cap (10) so a manager applies it: 1000 -> 700;
        # 700*100 = 70000 = original_amount*70, allowed.
        self.crm.discount(self.opp_id, 30, "m1")
        self.assertEqual(self.crm.opps[self.opp_id]["amount"], 700)
        self.assertEqual(self.crm.log[-1], ("discount", self.opp_id, "m1"))

    def test_rep_cannot_discount_after_manager_reaches_cap(self):
        crm = CRM(
            [
                {"id": "r", "role": "rep", "capacity": 2},
                {"id": "m", "role": "manager", "capacity": 0},
            ]
        )
        lead = crm.add_lead("a@gmail.com", "A", "referral", "m")
        crm.qualify(lead, "m")
        opp_id = crm.convert(lead, 1000, "m")
        crm.discount(opp_id, 30, "m")  # 1000 -> 700
        with self.assertRaises(ValueError):
            crm.discount(opp_id, 5, "r")  # 700 -> 665 < 700
        self.assertEqual(crm.opps[opp_id]["amount"], 700)


class TestTransfer(unittest.TestCase):
    def build_opp(self, email, crm=None, amount=10):
        crm = crm or self.crm
        lead = crm.add_lead(email, "Name", "referral", "m1")
        crm.qualify(lead, "m1")
        return crm.convert(lead, amount, "m1")

    def test_success(self):
        self.crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 2},
                {"id": "r2", "role": "rep", "capacity": 2},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        opp_id = self.build_opp("a@gmail.com")  # L1: tie at load 0 -> r1
        self.assertEqual(self.crm.opps[opp_id]["owner"], "r1")
        self.crm.transfer(opp_id, "r2", "m1")
        self.assertEqual(self.crm.opps[opp_id]["owner"], "r2")
        self.assertEqual(self.crm.log[-1], ("transfer", opp_id, "m1"))

    def test_actor_must_be_manager(self):
        self.crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 2},
                {"id": "r2", "role": "rep", "capacity": 2},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        opp_id = self.build_opp("a@gmail.com")
        with self.assertRaises(PermissionError):
            self.crm.transfer(opp_id, "r2", "r1")  # rep actor
        self.assertEqual(self.crm.opps[opp_id]["owner"], "r1")
        self.assertEqual(self.crm.log[-1], ("convert", opp_id, "m1"))

    def test_unknown_or_non_rep_new_owner(self):
        self.crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 2},
                {"id": "r2", "role": "rep", "capacity": 2},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        opp_id = self.build_opp("a@gmail.com")
        for bad in ["nobody", "m1"]:  # unknown user; known user but not a rep
            with self.subTest(new_owner=bad):
                with self.assertRaises(ValueError):
                    self.crm.transfer(opp_id, bad, "m1")
        self.assertEqual(self.crm.opps[opp_id]["owner"], "r1")

    def test_check_roles_order(self):
        self.crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 2},
                {"id": "r2", "role": "rep", "capacity": 2},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        opp_id = self.build_opp("a@gmail.com")
        with self.assertRaises(PermissionError):
            self.crm.transfer(opp_id, "r2", "nobody")  # actor check first
        with self.assertRaises(ValueError):
            self.crm.transfer("O9", "r2", "m1")  # existence precedes manager check
        with self.assertRaises(PermissionError):
            self.crm.transfer(opp_id, "nobody-unknown", "r1")  # manager precedes new_owner

    def test_final_stage_rejected(self):
        self.crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 2},
                {"id": "r2", "role": "rep", "capacity": 2},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        opp_id = self.build_opp("a@gmail.com")
        self.crm.advance(opp_id, "proposal", "m1")
        self.crm.advance(opp_id, "negotiation", "m1")
        self.crm.advance(opp_id, "lost", "m1")
        with self.assertRaises(ValueError):
            self.crm.transfer(opp_id, "r2", "m1")
        self.assertEqual(self.crm.opps[opp_id]["owner"], "r1")

    def test_same_owner_rejected(self):
        self.crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 2},
                {"id": "r2", "role": "rep", "capacity": 2},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        opp_id = self.build_opp("a@gmail.com")
        with self.assertRaises(ValueError):
            self.crm.transfer(opp_id, "r1", "m1")

    def test_capacity_rejected(self):
        # r1 cap 2, r2 cap 1: L1 -> r1 (tie); L2 -> r2 (load 0); L3 -> r1 (tie at 1... r2 full).
        self.crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 2},
                {"id": "r2", "role": "rep", "capacity": 1},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        opp_a = self.build_opp("a@gmail.com")  # r1 load 1
        self.assertEqual(self.crm.opps[opp_a]["owner"], "r1")
        opp_b = self.build_opp("b@gmail.com")  # -> r2 (lowest load), r2 load 1
        self.assertEqual(self.crm.opps[opp_b]["owner"], "r2")
        lead_c = self.crm.add_lead("c@gmail.com", "C", "referral", "m1")  # -> r1
        opp_c = qo(self.crm, lead_c)  # r1 load 2 = capacity
        self.assertEqual(self.crm.opps[opp_c]["owner"], "r1")
        # different owner (r2), at capacity -> check 6 ValueError
        with self.assertRaises(ValueError):
            self.crm.transfer(opp_c, "r2", "m1")
        self.assertEqual(self.crm.opps[opp_c]["owner"], "r1")

    def test_no_spurious_assignment_when_queue_empty(self):
        self.crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 2},
                {"id": "r2", "role": "rep", "capacity": 2},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        opp_id = self.build_opp("a@gmail.com")
        self.crm.transfer(opp_id, "r2", "m1")
        self.assertNotIn("assign", [entry[0] for entry in self.crm.log])


class TestForecast(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()

    def build_opp(self, email):
        lead = qi(self.crm, source="referral", email=email)
        self.crm.qualify(lead, "m1")
        return self.crm.convert(lead, 1, "m1")

    def test_empty(self):
        self.assertEqual(self.crm.forecast(), {"open": 0, "weighted": 0, "won": 0})

    def test_no_log_entry_from_forecast(self):
        self.crm.forecast()
        self.assertEqual(self.crm.log, [])

    def test_weights_and_floors(self):
        opps = [self.build_opp(email) for email in ["a@corp.com", "b@corp.com", "c@corp.com"]]
        self.crm.opps[opps[0]]["amount"] = 55
        self.crm.opps[opps[1]]["amount"] = 100
        self.crm.opps[opps[2]]["amount"] = 101
        self.crm.advance(opps[0], "lost", "m1")  # lost: excluded from forecast
        self.crm.advance(opps[1], "proposal", "m1")
        self.crm.advance(opps[2], "proposal", "m1")
        self.crm.advance(opps[2], "negotiation", "m1")
        result = self.crm.forecast()
        # 55 lost; 100 at proposal -> 30; 101 at negotiation -> 101*60//100 = 60
        self.assertEqual(result, {"open": 2, "weighted": 30 + 60, "won": 0})

    def test_won_sum(self):
        opps = [self.build_opp(email) for email in ["a@corp.com", "b@corp.com", "c@corp.com"]]
        for opp_id in opps:
            self.crm.advance(opp_id, "proposal", "m1")
            self.crm.advance(opp_id, "negotiation", "m1")
        self.crm.advance(opps[0], "won", "m1")  # amount 1
        self.crm.opps[opps[1]]["amount"] = 40  # still open at negotiation
        self.crm.advance(opps[2], "won", "m1")  # amount 1
        result = self.crm.forecast()
        # open opp is at negotiation: 40*60//100 = 24; won: 1 + 1 = 2
        self.assertEqual(result, {"open": 1, "weighted": 24, "won": 2})

    def test_lost_excluded_from_won(self):
        opp_id = self.build_opp("a@corp.com")
        self.crm.opps[opp_id]["amount"] = 100
        self.crm.advance(opp_id, "lost", "m1")
        self.assertEqual(self.crm.forecast(), {"open": 0, "weighted": 0, "won": 0})


class TestLogSemantics(unittest.TestCase):
    def test_failed_calls_append_nothing(self):
        crm = make_crm()
        with self.assertRaises(ValueError):
            crm.add_lead(1, "A", "web", "m1")
        with self.assertRaises(ValueError):
            crm.qualify("L1", "m1")
        with self.assertRaises(ValueError):
            crm.convert("L1", 10, "m1")
        with self.assertRaises(ValueError):
            crm.advance("O1", "proposal", "m1")
        with self.assertRaises(ValueError):
            crm.discount("O1", 10, "m1")
        with self.assertRaises(ValueError):
            crm.transfer("O1", "r1", "m1")
        crm.forecast()
        lead_id = crm.add_lead("a@gmail.com", "A", "referral", "m1")
        self.assertEqual(lead_id, "L1")  # failed adds don't consume ids
        self.assertEqual(crm.log, [("add_lead", "L1", "m1")])

    def test_log_tuple_shape(self):
        crm = make_crm()
        lead_id = qi(crm, source="referral")
        opp_id = qo(crm, lead_id)
        self.assertEqual(len(crm.log), 3)
        for entry in crm.log:
            self.assertIsInstance(entry, tuple)
            self.assertEqual(len(entry), 3)
            op, entity_id, actor_id = entry
            self.assertIsInstance(op, str)
            self.assertIsInstance(entity_id, str)
            self.assertIsInstance(actor_id, str)
            self.assertIn(
                (op, entity_id),
                [("add_lead", lead_id), ("qualify", lead_id), ("convert", opp_id)],
            )


if __name__ == "__main__":
    unittest.main()
