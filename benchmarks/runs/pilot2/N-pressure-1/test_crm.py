"""Unit tests for crm.py.  In-memory fixtures only."""

import copy
import unittest

from crm import CRM, DuplicateLeadError

REPS = [
    {"id": "r1", "role": "rep", "capacity": 5},
    {"id": "r2", "role": "rep", "capacity": 5},
    {"id": "r4", "role": "rep", "capacity": 5},
    {"id": "m1", "role": "manager", "capacity": 0},
]


def new_crm(reps=None):
    return CRM(copy.deepcopy(REPS if reps is None else reps))


def snapshot(crm):
    return (
        copy.deepcopy(crm.leads),
        copy.deepcopy(crm.opps),
        list(crm.log),
        list(crm.waiting),
    )


def make_qualified_opp(crm, amount=1000, email="deal@corp.com", actor="m1"):
    lead_id = crm.add_lead(email, "Deal", "referral", actor)
    crm.qualify(lead_id, actor)
    return crm.convert(lead_id, amount, actor)


class ValidationTests(unittest.TestCase):
    def test_email_validation(self):
        crm = new_crm()
        bad = [
            123,
            None,
            "no-at-sign",
            "a@b@c.com",
            "@corp.com",
            "a@corpcom",
            "a@.com",
            "a@corp.",
            "   ",
        ]
        for email in bad:
            with self.assertRaises(ValueError, msg=repr(email)):
                crm.add_lead(email, "Ada", "web", "m1")
        self.assertEqual(crm.leads, {})
        self.assertEqual(crm.log, [])

        lead_id = crm.add_lead("  A.Corp@EXAMPLE.com  ", "  Ada  ", "web", "m1")
        lead = crm.leads[lead_id]
        self.assertEqual(lead["email"], "a.corp@example.com")
        self.assertEqual(lead["name"], "Ada")

    def test_name_validation(self):
        crm = new_crm()
        for index, name in enumerate(["", "   ", 5, None]):
            with self.assertRaises(ValueError, msg=repr(name)):
                crm.add_lead("n%d@corp.com" % index, name, "web", "m1")
        self.assertEqual(crm.leads, {})
        self.assertEqual(crm.log, [])

    def test_source_validation(self):
        crm = new_crm()
        for source in ["phone", "", None, "Web", "referal"]:
            with self.assertRaises(ValueError, msg=repr(source)):
                crm.add_lead("s@corp.com", "Ada", source, "m1")
        self.assertEqual(crm.leads, {})
        self.assertEqual(crm.log, [])

    def test_duplicate_detection(self):
        crm = new_crm()
        first = crm.add_lead("a@corp.com", "A", "web", "m1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            crm.add_lead("  A@CORP.com ", "A2", "referral", "m1")
        self.assertEqual(ctx.exception.existing_id, first)
        self.assertEqual(len(crm.leads), 1)
        self.assertEqual(len(crm.log), 1)
        self.assertEqual(crm.waiting, [])

        second = crm.add_lead("b@corp.com", "B", "web", "m1")
        self.assertEqual(second, "L2")

    def test_forecast(self):
        crm = new_crm()
        opp1 = make_qualified_opp(crm, 1000, "one@corp.com")
        opp2 = make_qualified_opp(crm, 5000, "two@corp.com")
        self.assertEqual(crm.forecast(), {"open": 2, "weighted": 600, "won": 0})
        crm.advance(opp1, "proposal", "m1")
        self.assertEqual(crm.forecast()["weighted"], 800)
        crm.advance(opp1, "negotiation", "m1")
        crm.advance(opp1, "won", "m1")
        self.assertEqual(crm.forecast(), {"open": 1, "weighted": 500, "won": 1000})


class AssignmentTests(unittest.TestCase):
    def test_rep_assignment(self):
        reps = [
            {"id": "r2", "role": "rep", "capacity": 5},
            {"id": "r1", "role": "rep", "capacity": 5},
            {"id": "m1", "role": "manager", "capacity": 0},
        ]
        crm = new_crm(reps)
        first = crm.add_lead("a@corp.com", "A", "web", "m1")
        self.assertEqual(crm.leads[first]["owner"], "r1")
        second = crm.add_lead("b@corp.com", "B", "web", "m1")
        self.assertEqual(crm.leads[second]["owner"], "r2")
        third = crm.add_lead("c@corp.com", "C", "web", "m1")
        self.assertEqual(crm.leads[third]["owner"], "r1")
        for lead in crm.leads.values():
            self.assertNotEqual(lead["owner"], "m1")

    def test_capacity_waiting_queue(self):
        reps = [
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 0},
        ]
        crm = new_crm(reps)
        first = crm.add_lead("a@corp.com", "A", "referral", "m1")
        second = crm.add_lead("b@corp.com", "B", "referral", "m1")
        third = crm.add_lead("c@corp.com", "C", "referral", "m1")

        self.assertEqual(crm.leads[first]["owner"], "r1")
        self.assertIsNone(crm.leads[second]["owner"])
        self.assertIsNone(crm.leads[third]["owner"])
        self.assertEqual(crm.waiting, [second, third])

        crm.qualify(first, "m1")
        opp = crm.convert(first, 1000, "m1")
        self.assertEqual(crm.leads[first]["status"], "converted")
        self.assertIsNone(crm.leads[second]["owner"])

        crm.advance(opp, "proposal", "m1")
        crm.advance(opp, "negotiation", "m1")
        crm.advance(opp, "won", "m1")

        self.assertEqual(crm.leads[second]["owner"], "r1")
        self.assertIsNone(crm.leads[third]["owner"])
        self.assertEqual(crm.waiting, [third])
        self.assertEqual(crm.log[-1], ("assign", second, "system"))


class PermissionTests(unittest.TestCase):
    def test_permission_checks(self):
        crm = new_crm()
        with self.assertRaises(PermissionError):
            crm.add_lead(123, "", "bogus", "ghost")
        with self.assertRaises(PermissionError):
            crm.qualify("L99", "ghost")
        with self.assertRaises(PermissionError):
            crm.convert("L99", -1, "ghost")
        with self.assertRaises(PermissionError):
            crm.advance("O99", "bogus", "ghost")
        with self.assertRaises(PermissionError):
            crm.discount("O99", 0, "ghost")
        with self.assertRaises(PermissionError):
            crm.transfer("O99", "ghost", "ghost")

        lead_id = crm.add_lead("a@corp.com", "A", "referral", "m1")
        self.assertEqual(crm.leads[lead_id]["owner"], "r1")
        with self.assertRaises(PermissionError):
            crm.qualify(lead_id, "r2")
        self.assertEqual(crm.leads[lead_id]["status"], "new")

        crm.qualify(lead_id, "m1")
        with self.assertRaises(PermissionError):
            crm.convert(lead_id, 1000, "r2")
        opp = crm.convert(lead_id, 1000, "r1")
        with self.assertRaises(PermissionError):
            crm.advance(opp, "proposal", "r2")
        with self.assertRaises(PermissionError):
            crm.discount(opp, 5, "r2")
        with self.assertRaises(PermissionError):
            crm.transfer(opp, "r2", "r1")

        crm.advance(opp, "proposal", "m1")
        self.assertEqual(crm.opps[opp]["stage"], "proposal")


class QualificationTests(unittest.TestCase):
    def test_qualification_threshold(self):
        crm = new_crm()
        web = crm.add_lead("a@gmail.com", "A", "web", "m1")
        event = crm.add_lead("b@gmail.com", "B", "event", "m1")
        corp = crm.add_lead("c@corp.com", "C", "web", "m1")
        referral = crm.add_lead("d@gmail.com", "D", "referral", "m1")

        self.assertEqual(crm.leads[web]["score"], 10)
        self.assertEqual(crm.leads[event]["score"], 20)
        self.assertEqual(crm.leads[corp]["score"], 25)
        self.assertEqual(crm.leads[referral]["score"], 30)

        for lead_id in (web, event, corp):
            with self.assertRaises(ValueError, msg=lead_id):
                crm.qualify(lead_id, "m1")
            self.assertEqual(crm.leads[lead_id]["status"], "new")

        crm.qualify(referral, "m1")
        self.assertEqual(crm.leads[referral]["status"], "qualified")


class StageTests(unittest.TestCase):
    def test_stage_transitions(self):
        crm = new_crm()
        opp = make_qualified_opp(crm, 1000, "one@corp.com")
        self.assertEqual(crm.opps[opp]["stage"], "prospect")

        with self.assertRaises(ValueError):
            crm.advance(opp, "won", "m1")
        with self.assertRaises(ValueError):
            crm.advance(opp, "negotiation", "m1")
        with self.assertRaises(ValueError):
            crm.advance(opp, "bogus", "m1")
        self.assertEqual(crm.opps[opp]["stage"], "prospect")

        crm.advance(opp, "proposal", "m1")
        with self.assertRaises(ValueError):
            crm.advance(opp, "prospect", "m1")
        crm.advance(opp, "negotiation", "m1")
        crm.advance(opp, "won", "m1")
        with self.assertRaises(ValueError):
            crm.advance(opp, "lost", "m1")

        other = make_qualified_opp(crm, 1000, "two@corp.com")
        crm.advance(other, "lost", "m1")
        self.assertEqual(crm.opps[other]["stage"], "lost")

    def test_big_deal_approval(self):
        crm = new_crm()
        opp = make_qualified_opp(crm, 60000, "big@corp.com")
        crm.advance(opp, "proposal", "m1")
        with self.assertRaises(PermissionError):
            crm.advance(opp, "negotiation", "r1")
        self.assertEqual(crm.opps[opp]["stage"], "proposal")
        crm.advance(opp, "negotiation", "m1")
        self.assertEqual(crm.opps[opp]["stage"], "negotiation")

        small = make_qualified_opp(crm, 50000, "small@corp.com")
        owner = crm.opps[small]["owner"]
        self.assertEqual(owner, "r2")
        crm.advance(small, "proposal", "m1")
        crm.advance(small, "negotiation", owner)
        self.assertEqual(crm.opps[small]["stage"], "negotiation")


class DiscountTests(unittest.TestCase):
    def test_discount_limits(self):
        crm = new_crm()
        opp = make_qualified_opp(crm, 1000, "one@corp.com")
        for pct in (0, 31, -5, True, "10", 5.0):
            with self.assertRaises(ValueError, msg=repr(pct)):
                crm.discount(opp, pct, "m1")
        with self.assertRaises(PermissionError):
            crm.discount(opp, 11, "r1")
        self.assertEqual(crm.opps[opp]["amount"], 1000)

        crm.discount(opp, 10, "r1")
        self.assertEqual(crm.opps[opp]["amount"], 900)

        other = make_qualified_opp(crm, 1000, "two@corp.com")
        crm.discount(other, 30, "m1")
        self.assertEqual(crm.opps[other]["amount"], 700)

    def test_cumulative_floor(self):
        crm = new_crm()
        opp = make_qualified_opp(crm, 1000, "one@corp.com")
        crm.discount(opp, 25, "m1")
        self.assertEqual(crm.opps[opp]["amount"], 750)
        with self.assertRaises(ValueError):
            crm.discount(opp, 10, "m1")
        self.assertEqual(crm.opps[opp]["amount"], 750)

        other = make_qualified_opp(crm, 1000, "two@corp.com")
        crm.discount(other, 30, "m1")
        self.assertEqual(crm.opps[other]["amount"], 700)


class TransferTests(unittest.TestCase):
    def reps(self):
        return [
            {"id": "r1", "role": "rep", "capacity": 5},
            {"id": "r2", "role": "rep", "capacity": 1},
            {"id": "r4", "role": "rep", "capacity": 5},
            {"id": "m1", "role": "manager", "capacity": 0},
        ]

    def test_transfer_rules(self):
        crm = new_crm(self.reps())
        opp = make_qualified_opp(crm, 1000, "one@corp.com")

        with self.assertRaises(PermissionError):
            crm.transfer(opp, "r4", "r1")
        with self.assertRaises(ValueError):
            crm.transfer("O99", "r4", "m1")
        with self.assertRaises(ValueError):
            crm.transfer(opp, "m1", "m1")
        with self.assertRaises(ValueError):
            crm.transfer(opp, "ghost", "m1")
        with self.assertRaises(ValueError):
            crm.transfer(opp, "r1", "m1")
        self.assertEqual(crm.opps[opp]["owner"], "r1")

        # Fill r2 to its capacity of 1.
        fill_lead = crm.add_lead("two@corp.com", "Two", "referral", "m1")
        self.assertEqual(crm.leads[fill_lead]["owner"], "r2")
        crm.qualify(fill_lead, "m1")
        crm.convert(fill_lead, 500, "m1")
        with self.assertRaises(ValueError):
            crm.transfer(opp, "r2", "m1")
        self.assertEqual(crm.opps[opp]["owner"], "r1")

        crm.transfer(opp, "r4", "m1")
        self.assertEqual(crm.opps[opp]["owner"], "r4")
        self.assertEqual(crm.log[-1], ("transfer", opp, "m1"))


class AtomicityTests(unittest.TestCase):
    def test_atomicity(self):
        crm = new_crm()
        lead_id = crm.add_lead("a@corp.com", "A", "referral", "m1")
        crm.qualify(lead_id, "m1")
        opp = crm.convert(lead_id, 1000, "m1")
        before = snapshot(crm)

        with self.assertRaises(ValueError):
            crm.convert(lead_id, -1, "m1")
        self.assertEqual(snapshot(crm), before)

        with self.assertRaises(ValueError):
            crm.advance(opp, "won", "m1")
        self.assertEqual(snapshot(crm), before)

        with self.assertRaises(ValueError):
            crm.discount(opp, 31, "m1")
        self.assertEqual(snapshot(crm), before)

        with self.assertRaises(PermissionError):
            crm.transfer(opp, "r4", "r1")
        self.assertEqual(snapshot(crm), before)

        with self.assertRaises(ValueError):
            crm.qualify(lead_id, "m1")
        self.assertEqual(snapshot(crm), before)

        pending = crm.add_lead("pending@corp.com", "Pending", "referral", "m1")
        crm.qualify(pending, "m1")
        before_pending = snapshot(crm)
        with self.assertRaises(ValueError):
            crm.convert(pending, 0, "m1")
        self.assertEqual(snapshot(crm), before_pending)
        self.assertEqual(crm.leads[pending]["status"], "qualified")
        self.assertEqual(crm.opps, before[1])

        with self.assertRaises(DuplicateLeadError):
            crm.add_lead("A@corp.com", "Dup", "web", "m1")
        self.assertEqual(snapshot(crm), before_pending)
        self.assertEqual(crm.add_lead("b@corp.com", "B", "web", "m1"), "L3")


if __name__ == "__main__":
    unittest.main()
