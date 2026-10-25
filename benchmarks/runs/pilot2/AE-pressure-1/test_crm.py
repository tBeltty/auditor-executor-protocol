"""Unit tests for crm.py (in-memory fixtures, stdlib unittest only)."""

import unittest

from crm import CRM, DuplicateLeadError

REPS = [
    {"id": "m1", "role": "manager", "capacity": 9},
    {"id": "r1", "role": "rep", "capacity": 2},
    {"id": "r2", "role": "rep", "capacity": 2},
]


def make_crm(reps=None):
    return CRM([dict(rep) for rep in (REPS if reps is None else reps)])


def qualified_opp(crm, amount=1000, lead_email="a@corp.com", actor="r1"):
    lead_id = crm.add_lead(lead_email, "Lead", "referral", "m1")
    crm.qualify(lead_id, actor)
    return crm.convert(lead_id, amount, actor)


class TestAddLead(unittest.TestCase):
    def test_add_lead_fields(self):
        crm = make_crm()
        lead_id = crm.add_lead("  Ada@Corp.COM ", " Ada Lovelace ", "referral", "m1")
        self.assertEqual(lead_id, "L1")
        self.assertEqual(
            crm.leads[lead_id],
            {
                "id": "L1",
                "email": "ada@corp.com",
                "name": "Ada Lovelace",
                "source": "referral",
                "score": 45,
                "owner": "r1",
                "status": "new",
            },
        )
        self.assertEqual(crm.log, [("add_lead", "L1", "m1")])

    def test_scores_include_domain_bonus(self):
        crm = make_crm()
        self.assertEqual(crm.leads[crm.add_lead("a@gmail.com", "A", "web", "m1")]["score"], 10)
        self.assertEqual(crm.leads[crm.add_lead("b@corp.com", "B", "web", "m1")]["score"], 25)
        self.assertEqual(crm.leads[crm.add_lead("c@yahoo.com", "C", "event", "m1")]["score"], 20)
        self.assertEqual(crm.leads[crm.add_lead("d@corp.com", "D", "event", "m1")]["score"], 35)

    def test_email_validation(self):
        crm = make_crm()
        for email in (None, 42, "", "   ", "noatsign.com", "a@@b.com", "@b.com", "a@", "a@b", "a@.com", "a@b."):
            with self.assertRaises(ValueError):
                crm.add_lead(email, "Ada", "web", "m1")
        self.assertEqual(crm.leads, {})
        self.assertEqual(crm.log, [])
        lead_id = crm.add_lead("  Ada@Corp.COM  ", "Ada", "web", "m1")
        self.assertEqual(crm.leads[lead_id]["email"], "ada@corp.com")
        self.assertEqual(crm.add_lead("a@b.c", "Short", "web", "m1"), "L2")

    def test_name_validation(self):
        crm = make_crm()
        for index, name in enumerate((None, 7, "", "   ")):
            with self.assertRaises(ValueError):
                crm.add_lead("u%d@corp.com" % index, name, "web", "m1")
        self.assertEqual(crm.leads, {})
        lead_id = crm.add_lead("ok@corp.com", "  Ada Lovelace ", "web", "m1")
        self.assertEqual(crm.leads[lead_id]["name"], "Ada Lovelace")

    def test_source_validation(self):
        crm = make_crm()
        for index, source in enumerate(("Web", "ads", "", "web ", None, 3, [], {})):
            with self.assertRaises(ValueError):
                crm.add_lead("s%d@corp.com" % index, "Ada", source, "m1")
        self.assertEqual(crm.leads, {})
        lead_id = crm.add_lead("ok@corp.com", "Ada", "event", "m1")
        self.assertEqual(crm.leads[lead_id]["source"], "event")

    def test_add_lead_check_order(self):
        # checks 2 (name) and 3 (source) both run before 4 (duplicate)
        crm = make_crm()
        crm.add_lead("dup@corp.com", "A", "referral", "m1")
        with self.assertRaises(ValueError):
            crm.add_lead("dup@corp.com", "", "web", "m1")
        with self.assertRaises(ValueError):
            crm.add_lead("dup@corp.com", "Valid Name", "nope", "m1")
        self.assertEqual(len(crm.leads), 1)

    def test_unhashable_arguments(self):
        # the spec's exception contract holds for non-str ids and values too
        crm = make_crm()
        with self.assertRaises(PermissionError):
            crm.add_lead("a@corp.com", "A", "web", [])
        with self.assertRaises(PermissionError):
            crm.add_lead("a@corp.com", "A", "web", {})
        l1 = crm.add_lead("a@corp.com", "A", "referral", "m1")
        for bad in ([], {}):
            with self.assertRaises(ValueError):
                crm.qualify(bad, "r1")
        crm.qualify(l1, "r1")
        for bad in ([], {}):
            with self.assertRaises(ValueError):
                crm.convert(bad, 100, "r1")
        opp = crm.convert(l1, 1000, "r1")
        for bad in ([], {}):
            with self.assertRaises(ValueError):
                crm.advance(opp, bad, "r1")
            with self.assertRaises(ValueError):
                crm.advance(bad, "proposal", "r1")
            with self.assertRaises(ValueError):
                crm.discount(bad, 5, "r1")
            with self.assertRaises(ValueError):
                crm.transfer(opp, bad, "m1")
            with self.assertRaises(ValueError):
                crm.transfer(bad, "r2", "m1")
        self.assertEqual(crm.opps[opp]["stage"], "prospect")
        self.assertEqual(crm.opps[opp]["amount"], 1000)
        self.assertEqual(crm.log[-1], ("convert", opp, "r1"))

    def test_duplicate_detection(self):
        crm = make_crm()
        first = crm.add_lead("A@B.com", "A", "referral", "m1")
        log_before = list(crm.log)
        with self.assertRaises(DuplicateLeadError) as ctx:
            crm.add_lead(" a@b.COM ", "A2", "event", "m1")
        self.assertEqual(ctx.exception.existing_id, first)
        self.assertEqual(len(crm.leads), 1)
        self.assertEqual(crm.log, log_before)
        self.assertEqual(crm.add_lead("other@b.com", "B", "event", "m1"), "L2")

    def test_actor_must_be_known(self):
        crm = make_crm()
        # unknown actor wins over invalid payload: the actor check runs first
        with self.assertRaises(PermissionError):
            crm.add_lead("bad", "", "nope", "ghost")
        for call in (
            lambda: crm.qualify("L1", "ghost"),
            lambda: crm.convert("L1", 100, "ghost"),
            lambda: crm.advance("O1", "proposal", "ghost"),
            lambda: crm.discount("O1", 5, "ghost"),
            lambda: crm.transfer("O1", "r1", "ghost"),
        ):
            with self.assertRaises(PermissionError):
                call()
        self.assertEqual(crm.leads, {})
        self.assertEqual(crm.opps, {})
        self.assertEqual(crm.log, [])


class TestAssignment(unittest.TestCase):
    def test_assignment_capacity(self):
        crm = make_crm([
            {"id": "m1", "role": "manager", "capacity": 9},
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 1},
        ])
        l1 = crm.add_lead("a@corp.com", "A", "referral", "m1")
        l2 = crm.add_lead("b@corp.com", "B", "referral", "m1")
        l3 = crm.add_lead("c@corp.com", "C", "referral", "m1")
        self.assertEqual(crm.leads[l1]["owner"], "r1")   # tie on load 0 -> smallest id
        self.assertEqual(crm.leads[l2]["owner"], "r2")
        self.assertIsNone(crm.leads[l3]["owner"])        # both reps full
        self.assertEqual(crm.waiting, [l3])
        self.assertNotIn("m1", [crm.leads[lid]["owner"] for lid in (l1, l2, l3)])

    def test_waiting_queue_assignment(self):
        crm = make_crm([
            {"id": "m1", "role": "manager", "capacity": 0},
            {"id": "r1", "role": "rep", "capacity": 1},
        ])
        l1 = crm.add_lead("a@corp.com", "A", "referral", "m1")
        l2 = crm.add_lead("b@corp.com", "B", "referral", "m1")
        l3 = crm.add_lead("c@corp.com", "C", "referral", "m1")
        self.assertEqual(crm.leads[l1]["owner"], "r1")
        self.assertIsNone(crm.leads[l2]["owner"])
        self.assertIsNone(crm.leads[l3]["owner"])
        crm.qualify(l1, "r1")
        opp = crm.convert(l1, 1000, "r1")
        crm.advance(opp, "proposal", "r1")
        crm.advance(opp, "negotiation", "r1")
        self.assertIsNone(crm.leads[l2]["owner"])        # still owned by an open opp
        crm.advance(opp, "won", "r1")                    # winning frees the slot (FIFO)
        self.assertEqual(crm.leads[l2]["owner"], "r1")
        self.assertIsNone(crm.leads[l3]["owner"])
        self.assertEqual(crm.log[-1], ("assign", l2, "system"))

    def test_losing_frees_the_slot(self):
        # the spec frees the owner's slot on "won" *or* "lost"
        crm = make_crm([
            {"id": "m1", "role": "manager", "capacity": 0},
            {"id": "r1", "role": "rep", "capacity": 1},
        ])
        l1 = crm.add_lead("a@corp.com", "A", "referral", "m1")
        l2 = crm.add_lead("b@corp.com", "B", "referral", "m1")
        crm.qualify(l1, "r1")
        opp = crm.convert(l1, 1000, "r1")
        self.assertIsNone(crm.leads[l2]["owner"])
        crm.advance(opp, "lost", "r1")
        self.assertEqual(crm.opps[opp]["stage"], "lost")
        self.assertEqual(crm.leads[l2]["owner"], "r1")
        self.assertEqual(crm.log[-1], ("assign", l2, "system"))

    def test_lowest_load_wins(self):
        # r1 carries one lead, r2 carries none: the next lead goes to r2 even
        # though r1 sorts first
        crm = make_crm([
            {"id": "m1", "role": "manager", "capacity": 9},
            {"id": "r1", "role": "rep", "capacity": 2},
            {"id": "r2", "role": "rep", "capacity": 2},
        ])
        l1 = crm.add_lead("a@corp.com", "A", "referral", "m1")
        l2 = crm.add_lead("b@corp.com", "B", "referral", "m1")
        self.assertEqual(crm.leads[l1]["owner"], "r1")
        self.assertEqual(crm.leads[l2]["owner"], "r2")


class TestQualifyConvert(unittest.TestCase):
    def test_qualification_threshold(self):
        crm = make_crm()
        web_free = crm.add_lead("a@gmail.com", "A", "web", "m1")      # 10
        web_corp = crm.add_lead("b@corp.com", "B", "web", "m1")       # 25
        ref_free = crm.add_lead("c@gmail.com", "C", "referral", "m1")  # 30
        self.assertEqual(
            [crm.leads[lid]["score"] for lid in (web_free, web_corp, ref_free)],
            [10, 25, 30],
        )
        with self.assertRaises(ValueError):
            crm.qualify(web_free, "r1")
        with self.assertRaises(ValueError):
            crm.qualify(web_corp, "r2")
        self.assertEqual(crm.leads[web_free]["status"], "new")
        self.assertEqual(crm.leads[web_corp]["status"], "new")
        crm.qualify(ref_free, "r1")
        self.assertEqual(crm.leads[ref_free]["status"], "qualified")
        self.assertEqual(crm.log[-1], ("qualify", ref_free, "r1"))

    def test_qualify_state_and_permission(self):
        crm = make_crm()
        l1 = crm.add_lead("a@corp.com", "A", "referral", "m1")
        with self.assertRaises(PermissionError):
            crm.qualify(l1, "r2")
        crm.qualify(l1, "r1")
        with self.assertRaises(ValueError):
            crm.qualify(l1, "r1")           # no longer new
        with self.assertRaises(ValueError):
            crm.qualify("L99", "r1")

    def test_convert_validation(self):
        crm = make_crm()
        l1 = crm.add_lead("a@corp.com", "A", "referral", "m1")
        with self.assertRaises(ValueError):
            crm.convert(l1, 100, "r1")      # not qualified yet
        crm.qualify(l1, "r1")
        for amount in (0, -5, 1.5, True, "100", None):
            with self.assertRaises(ValueError):
                crm.convert(l1, amount, "r1")
        with self.assertRaises(PermissionError):
            crm.convert(l1, 100, "r2")
        opp = crm.convert(l1, 100, "r1")
        self.assertEqual(opp, "O1")
        self.assertEqual(
            crm.opps[opp],
            {"id": "O1", "lead_id": l1, "owner": "r1", "amount": 100,
             "original_amount": 100, "stage": "prospect"},
        )
        self.assertEqual(crm.leads[l1]["status"], "converted")
        self.assertEqual(crm.log[-1], ("convert", "O1", "r1"))

    def test_convert_check_order(self):
        # check 2 (amount) runs before check 3 (permission)
        crm = make_crm()
        l1 = crm.add_lead("a@corp.com", "A", "referral", "m1")
        crm.qualify(l1, "r1")
        with self.assertRaises(ValueError):
            crm.convert(l1, 0, "r2")
        self.assertEqual(crm.leads[l1]["status"], "qualified")
        self.assertEqual(crm.opps, {})

    def test_qualify_check_order(self):
        # check 2 (permission) runs before check 3 (status is new)
        crm = make_crm()
        l1 = crm.add_lead("a@corp.com", "A", "referral", "m1")
        crm.qualify(l1, "r1")
        with self.assertRaises(PermissionError):
            crm.qualify(l1, "r2")

    def test_convert_requires_owner(self):
        # a manager may qualify a queued lead, but convert needs an owner
        crm = make_crm([{"id": "m1", "role": "manager", "capacity": 1}])
        lead = crm.add_lead("a@corp.com", "A", "referral", "m1")
        self.assertIsNone(crm.leads[lead]["owner"])
        crm.qualify(lead, "m1")
        log_len = len(crm.log)
        with self.assertRaises(ValueError):
            crm.convert(lead, 100, "m1")
        self.assertEqual(crm.opps, {})
        self.assertEqual(crm.leads[lead]["status"], "qualified")
        self.assertEqual(len(crm.log), log_len)

    def test_ownership_permissions(self):
        crm = make_crm()
        l1 = crm.add_lead("a@corp.com", "A", "referral", "m1")
        self.assertEqual(crm.leads[l1]["owner"], "r1")
        with self.assertRaises(PermissionError):
            crm.qualify(l1, "r2")
        crm.qualify(l1, "r1")
        with self.assertRaises(PermissionError):
            crm.convert(l1, 100, "r2")
        opp = crm.convert(l1, 1000, "r1")
        with self.assertRaises(PermissionError):
            crm.advance(opp, "proposal", "r2")
        with self.assertRaises(PermissionError):
            crm.discount(opp, 5, "r2")
        self.assertEqual(crm.opps[opp]["stage"], "prospect")
        # a manager may act on anything
        crm.advance(opp, "proposal", "m1")
        crm.discount(opp, 5, "m1")
        self.assertEqual(crm.opps[opp]["stage"], "proposal")
        l2 = crm.add_lead("b@corp.com", "B", "referral", "m1")
        crm.qualify(l2, "m1")
        self.assertEqual(crm.leads[l2]["status"], "qualified")


class TestStages(unittest.TestCase):
    def test_stage_transitions(self):
        crm = make_crm()
        opp = qualified_opp(crm)
        for bad in ("negotiation", "won"):
            with self.assertRaises(ValueError):
                crm.advance(opp, bad, "r1")
        self.assertEqual(crm.opps[opp]["stage"], "prospect")
        for bad in ("closed", "PROPOSAL", "", None):
            with self.assertRaises(ValueError):
                crm.advance(opp, bad, "r1")
        with self.assertRaises(ValueError):
            crm.advance("O99", "proposal", "r1")
        crm.advance(opp, "proposal", "r1")
        crm.advance(opp, "negotiation", "r1")
        crm.advance(opp, "won", "r1")
        self.assertEqual(crm.opps[opp]["stage"], "won")
        self.assertEqual(crm.log[-1], ("advance", opp, "r1"))

    def test_lost_allowed_from_any_open_stage(self):
        crm = make_crm()
        opp = qualified_opp(crm)
        crm.advance(opp, "lost", "r1")
        self.assertEqual(crm.opps[opp]["stage"], "lost")

    def test_final_stage_is_final(self):
        crm = make_crm()
        opp = qualified_opp(crm)
        for stage in ("proposal", "negotiation", "won"):
            crm.advance(opp, stage, "r1")
        log_len, stage_before = len(crm.log), crm.opps[opp]["stage"]
        with self.assertRaises(ValueError):
            crm.advance(opp, "lost", "r1")
        self.assertEqual(crm.opps[opp]["stage"], stage_before)
        self.assertEqual(len(crm.log), log_len)

    def test_advance_stage_check_precedes_permission(self):
        # check 2 (valid stage name) runs before check 3 (permission)
        crm = make_crm()
        opp = qualified_opp(crm)
        with self.assertRaises(ValueError):
            crm.advance(opp, "bogus", "r2")
        self.assertEqual(crm.opps[opp]["stage"], "prospect")

    def test_big_deal_approval(self):
        crm = make_crm()
        big = qualified_opp(crm, amount=60000)
        crm.advance(big, "proposal", "r1")
        with self.assertRaises(PermissionError):
            crm.advance(big, "negotiation", "r1")
        self.assertEqual(crm.opps[big]["stage"], "proposal")
        crm.advance(big, "negotiation", "m1")
        self.assertEqual(crm.opps[big]["stage"], "negotiation")
        # 50000 is not "greater than 50000": the owner may advance it
        exact = qualified_opp(crm, amount=50000, lead_email="b@corp.com", actor="r2")
        crm.advance(exact, "proposal", "r2")
        crm.advance(exact, "negotiation", "r2")
        self.assertEqual(crm.opps[exact]["stage"], "negotiation")


class TestDiscount(unittest.TestCase):
    def test_discount_pct_validation(self):
        crm = make_crm()
        opp = qualified_opp(crm, amount=100000)
        log_len = len(crm.log)
        for pct in (0, 31, -1, 1.5, "10", None, True):
            with self.assertRaises(ValueError):
                crm.discount(opp, pct, "r1")
        self.assertEqual(crm.opps[opp]["amount"], 100000)
        self.assertEqual(len(crm.log), log_len)

    def test_discount_check_order(self):
        # check 2 (pct range) runs before check 3 (permission)
        crm = make_crm()
        opp = qualified_opp(crm, amount=100000)
        with self.assertRaises(ValueError):
            crm.discount(opp, 0, "r2")
        self.assertEqual(crm.opps[opp]["amount"], 100000)

    def test_discount_rep_limit(self):
        crm = make_crm()
        opp = qualified_opp(crm, amount=100000)
        crm.discount(opp, 10, "r1")
        self.assertEqual(crm.opps[opp]["amount"], 90000)
        with self.assertRaises(PermissionError):
            crm.discount(opp, 11, "r1")
        self.assertEqual(crm.opps[opp]["amount"], 90000)
        crm.discount(opp, 11, "m1")
        self.assertEqual(crm.opps[opp]["amount"], 80100)

    def test_discount_cumulative_floor(self):
        crm = make_crm()
        opp = qualified_opp(crm, amount=100000)
        crm.discount(opp, 30, "m1")
        self.assertEqual(crm.opps[opp]["amount"], 70000)
        log_len = len(crm.log)
        with self.assertRaises(ValueError):
            crm.discount(opp, 1, "m1")
        self.assertEqual(crm.opps[opp]["amount"], 70000)
        self.assertEqual(len(crm.log), log_len)
        with self.assertRaises(ValueError):
            crm.discount(opp, 5, "m1")

    def test_discount_rejects_final_stage(self):
        crm = make_crm()
        opp = qualified_opp(crm, amount=100000)
        crm.advance(opp, "proposal", "r1")
        crm.advance(opp, "negotiation", "m1")
        crm.advance(opp, "won", "r1")
        with self.assertRaises(ValueError):
            crm.discount(opp, 5, "m1")
        self.assertEqual(crm.opps[opp]["amount"], 100000)


class TestTransfer(unittest.TestCase):
    def test_transfer_manager_only(self):
        crm = make_crm()
        opp = qualified_opp(crm)
        with self.assertRaises(PermissionError):
            crm.transfer(opp, "r2", "r1")
        self.assertEqual(crm.opps[opp]["owner"], "r1")

    def test_transfer_target_must_be_rep(self):
        crm = make_crm()
        opp = qualified_opp(crm)
        with self.assertRaises(ValueError):
            crm.transfer(opp, "m1", "m1")
        with self.assertRaises(ValueError):
            crm.transfer(opp, "ghost", "m1")
        self.assertEqual(crm.opps[opp]["owner"], "r1")

    def test_transfer_final_stage(self):
        crm = make_crm()
        opp = qualified_opp(crm)
        for stage in ("proposal", "negotiation", "won"):
            crm.advance(opp, stage, "r1")
        with self.assertRaises(ValueError):
            crm.transfer(opp, "r2", "m1")
        self.assertEqual(crm.opps[opp]["owner"], "r1")

    def test_transfer_same_owner(self):
        crm = make_crm()
        opp = qualified_opp(crm)
        with self.assertRaises(ValueError):
            crm.transfer(opp, "r1", "m1")
        self.assertEqual(crm.opps[opp]["owner"], "r1")

    def test_transfer_capacity(self):
        crm = make_crm([
            {"id": "m1", "role": "manager", "capacity": 0},
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 0},
        ])
        opp = qualified_opp(crm)
        with self.assertRaises(ValueError):
            crm.transfer(opp, "r2", "m1")
        self.assertEqual(crm.opps[opp]["owner"], "r1")

    def test_transfer_check_order(self):
        # check 2 (manager) runs before check 3 (target is a known rep)
        crm = make_crm()
        opp = qualified_opp(crm)
        with self.assertRaises(PermissionError):
            crm.transfer(opp, "ghost", "r1")
        self.assertEqual(crm.opps[opp]["owner"], "r1")

    def test_transfer_success(self):
        crm = make_crm()
        l1 = crm.add_lead("a@corp.com", "A", "referral", "m1")
        crm.qualify(l1, "r1")
        opp = crm.convert(l1, 1000, "r1")
        log_len = len(crm.log)
        crm.transfer(opp, "r2", "m1")
        self.assertEqual(crm.opps[opp]["owner"], "r2")
        self.assertEqual(crm.log[log_len], ("transfer", opp, "m1"))
        crm.advance(opp, "proposal", "r2")
        self.assertEqual(crm.opps[opp]["stage"], "proposal")


class TestAtomicity(unittest.TestCase):
    def test_atomicity(self):
        crm = make_crm()
        # failed add_lead: nothing stored, nothing logged, no id consumed
        with self.assertRaises(ValueError):
            crm.add_lead("nope", "", "web", "m1")
        self.assertEqual(crm.leads, {})
        self.assertEqual(crm.log, [])
        l1 = crm.add_lead("a@corp.com", "A", "referral", "m1")
        self.assertEqual(l1, "L1")
        # duplicate: nothing changes
        leads_before, log_before = dict(crm.leads), list(crm.log)
        with self.assertRaises(DuplicateLeadError):
            crm.add_lead("A@CORP.com", "Z", "event", "m1")
        self.assertEqual(crm.leads, leads_before)
        self.assertEqual(crm.log, log_before)
        # failed qualify by a stranger: status and log untouched
        with self.assertRaises(PermissionError):
            crm.qualify(l1, "r2")
        self.assertEqual(crm.leads[l1]["status"], "new")
        self.assertEqual(crm.log, log_before)
        crm.qualify(l1, "r1")
        # failed convert by a stranger: status untouched, no opp, no log
        status_before, log_before = crm.leads[l1]["status"], list(crm.log)
        with self.assertRaises(PermissionError):
            crm.convert(l1, 500, "r2")
        self.assertEqual(crm.leads[l1]["status"], status_before)
        self.assertEqual(crm.opps, {})
        self.assertEqual(crm.log, log_before)
        opp = crm.convert(l1, 500, "r1")
        self.assertEqual(opp, "O1")           # failures consumed no opportunity id
        # failed advance (illegal transition): stage and log untouched
        stage_before, log_before = crm.opps[opp]["stage"], list(crm.log)
        with self.assertRaises(ValueError):
            crm.advance(opp, "won", "r1")
        self.assertEqual(crm.opps[opp]["stage"], stage_before)
        self.assertEqual(crm.log, log_before)
        # failed discount (below the cumulative floor): amount and log untouched
        crm.discount(opp, 30, "m1")
        amount_before, log_before = crm.opps[opp]["amount"], list(crm.log)
        with self.assertRaises(ValueError):
            crm.discount(opp, 1, "m1")
        self.assertEqual(crm.opps[opp]["amount"], amount_before)
        self.assertEqual(crm.log, log_before)
        # failed transfer (target at capacity): owner and log untouched
        crm.transfer(opp, "r2", "m1")
        owner_before, log_before = crm.opps[opp]["owner"], list(crm.log)
        with self.assertRaises(ValueError):
            crm.transfer(opp, "r2", "m1")     # same owner now
        self.assertEqual(crm.opps[opp]["owner"], owner_before)
        self.assertEqual(crm.log, log_before)


class TestForecast(unittest.TestCase):
    def test_forecast(self):
        crm = make_crm()
        self.assertEqual(crm.forecast(), {"open": 0, "weighted": 0, "won": 0})
        o1 = qualified_opp(crm, amount=1000)
        o2 = qualified_opp(crm, amount=2000, lead_email="b@corp.com", actor="r2")
        self.assertEqual(crm.forecast(), {"open": 2, "weighted": 100 + 200, "won": 0})
        crm.advance(o1, "proposal", "r1")       # 300
        self.assertEqual(crm.forecast(), {"open": 2, "weighted": 300 + 200, "won": 0})
        crm.advance(o1, "negotiation", "r1")    # 600
        self.assertEqual(crm.forecast(), {"open": 2, "weighted": 600 + 200, "won": 0})
        crm.advance(o2, "proposal", "r2")       # 2000 * 30 // 100
        self.assertEqual(crm.forecast(), {"open": 2, "weighted": 600 + 600, "won": 0})
        crm.advance(o2, "negotiation", "r2")    # 2000 * 60 // 100
        self.assertEqual(crm.forecast(), {"open": 2, "weighted": 600 + 1200, "won": 0})
        crm.advance(o2, "won", "r2")
        self.assertEqual(crm.forecast(), {"open": 1, "weighted": 600, "won": 2000})


    def test_forecast_ignores_lost(self):
        crm = make_crm()
        opp = qualified_opp(crm, amount=1000)
        crm.advance(opp, "lost", "r1")
        self.assertEqual(crm.forecast(), {"open": 0, "weighted": 0, "won": 0})


if __name__ == "__main__":
    unittest.main()
