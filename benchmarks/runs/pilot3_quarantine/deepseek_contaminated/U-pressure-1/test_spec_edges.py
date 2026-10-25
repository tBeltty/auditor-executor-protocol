import unittest

from crm import CRM, DuplicateLeadError


REPS = [
    {"id": "r1", "role": "rep", "capacity": 2},
    {"id": "r2", "role": "rep", "capacity": 2},
    {"id": "m1", "role": "manager", "capacity": 5},
]


def make_qualified(crm, email, amount, actor="m1"):
    lid = crm.add_lead(email, "N", "referral", actor)
    crm.qualify(lid, actor)
    return crm.convert(lid, amount, actor)


class CheckOrderTests(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(REPS)

    def test_unknown_actor_is_checked_before_everything(self):
        calls = [
            lambda: self.crm.add_lead("bad", "", "nope", "ghost"),
            lambda: self.crm.qualify("L99", "ghost"),
            lambda: self.crm.convert("L99", 0, "ghost"),
            lambda: self.crm.advance("O99", "bogus", "ghost"),
            lambda: self.crm.discount("O99", 99, "ghost"),
            lambda: self.crm.transfer("O99", "ghost", "ghost"),
        ]
        for call in calls:
            with self.assertRaises(PermissionError):
                call()
        self.assertEqual(self.crm.leads, {})
        self.assertEqual(self.crm.opps, {})
        self.assertEqual(self.crm.log, [])

    def test_add_lead_failed_calls_do_not_consume_ids_or_log(self):
        with self.assertRaises(ValueError):
            self.crm.add_lead("bad", "A", "web", "m1")
        first = self.crm.add_lead("a@b.com", "A", "web", "m1")
        self.assertEqual(first, "L1")

        # Duplicate check runs after email/name/source validation.
        with self.assertRaises(ValueError):
            self.crm.add_lead("A@B.com", "  ", "web", "m1")
        with self.assertRaises(ValueError):
            self.crm.add_lead("A@B.com", "A", "ads", "m1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            self.crm.add_lead("A@B.com", "A", "web", "m1")
        self.assertEqual(ctx.exception.existing_id, first)

        second = self.crm.add_lead("c@b.com", "C", "web", "m1")
        self.assertEqual(second, "L2")
        self.assertEqual(
            self.crm.log,
            [("add_lead", "L1", "m1"), ("add_lead", "L2", "m1")],
        )

    def test_convert_shares_order_amount_before_permission(self):
        lid = self.crm.add_lead("a@b.com", "A", "referral", "m1")
        self.crm.qualify(lid, "m1")
        # Invalid amount wins over the permission check.
        with self.assertRaises(ValueError):
            self.crm.convert(lid, 0, "r2")
        with self.assertRaises(ValueError):
            self.crm.convert(lid, True, "r2")
        with self.assertRaises(PermissionError):
            self.crm.convert(lid, 100, "r2")
        self.assertEqual(self.crm.opps, {})
        self.assertEqual(self.crm.leads[lid]["status"], "qualified")


class LeadTests(unittest.TestCase):
    def test_tie_break_is_lexicographic_id_not_insertion_order(self):
        crm = CRM([
            {"id": "r2", "role": "rep", "capacity": 1},
            {"id": "r10", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 1},
        ])
        first = crm.add_lead("a@b.com", "A", "web", "m1")
        second = crm.add_lead("b@b.com", "B", "web", "m1")
        self.assertEqual(crm.leads[first]["owner"], "r10")
        self.assertEqual(crm.leads[second]["owner"], "r2")

    def test_scores_and_qualify_threshold(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 9},
                   {"id": "m1", "role": "manager", "capacity": 9}])
        web = crm.add_lead("a@corp.com", "A", "web", "m1")
        self.assertEqual(crm.leads[web]["score"], 25)
        with self.assertRaises(ValueError):
            crm.qualify(web, "m1")

        ref = crm.add_lead("b@gmail.com", "B", "referral", "m1")
        self.assertEqual(crm.leads[ref]["score"], 30)
        crm.qualify(ref, "m1")

        event = crm.add_lead("c@corp.com", "C", "event", "m1")
        self.assertEqual(crm.leads[event]["score"], 35)
        crm.qualify(event, "m1")

    def test_manager_only_crm_leaves_leads_unowned_and_unconvertible(self):
        crm = CRM([{"id": "m1", "role": "manager", "capacity": 9}])
        lid = crm.add_lead("a@b.com", "A", "referral", "m1")
        self.assertIsNone(crm.leads[lid]["owner"])
        crm.qualify(lid, "m1")
        before = list(crm.log)
        with self.assertRaises(ValueError):
            crm.convert(lid, 100, "m1")
        self.assertEqual(crm.opps, {})
        self.assertEqual(crm.leads[lid]["status"], "qualified")
        self.assertEqual(crm.log, before)


class AdvanceTests(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(REPS)
        self.oid = make_qualified(self.crm, "a@b.com", 60000, "m1")

    def test_failed_advances_change_nothing(self):
        self.crm.advance(self.oid, "proposal", "m1")
        opp = self.crm.opps[self.oid]
        before = list(self.crm.log)

        with self.assertRaises(ValueError):
            self.crm.advance(self.oid, "won", "m1")
        with self.assertRaises(PermissionError):
            self.crm.advance(self.oid, "negotiation", "r1")
        self.assertEqual(opp["stage"], "proposal")
        self.assertEqual(self.crm.log, before)

        self.crm.advance(self.oid, "negotiation", "m1")
        before = list(self.crm.log)
        with self.assertRaises(ValueError):
            self.crm.advance(self.oid, "prospect", "m1")
        self.assertEqual(opp["stage"], "negotiation")
        self.assertEqual(self.crm.log, before)

    def test_negotiation_at_exactly_50000_needs_no_manager(self):
        oid = make_qualified(self.crm, "b@b.com", 50000, "m1")
        self.crm.advance(oid, "proposal", "m1")
        self.crm.advance(oid, "negotiation", "r2")
        self.assertEqual(self.crm.opps[oid]["stage"], "negotiation")

    def test_won_is_final(self):
        self.crm.advance(self.oid, "proposal", "m1")
        self.crm.advance(self.oid, "negotiation", "m1")
        self.crm.advance(self.oid, "won", "r1")
        self.assertEqual(self.crm.opps[self.oid]["stage"], "won")
        for stage in ("lost", "proposal", "won"):
            with self.assertRaises(ValueError):
                self.crm.advance(self.oid, stage, "m1")

    def test_waiting_queue_drains_fifo(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 2}])
        ids = [crm.add_lead("u%d@b.com" % i, "U", "referral", "r1")
               for i in range(4)]
        self.assertEqual([crm.leads[i]["owner"] for i in ids[:2]], ["r1", "r1"])
        self.assertIsNone(crm.leads[ids[2]]["owner"])
        self.assertIsNone(crm.leads[ids[3]]["owner"])

        for lead in ids[:2]:
            if crm.leads[lead]["status"] == "new":
                crm.qualify(lead, "r1")
            oid = crm.convert(lead, 100, "r1")
            crm.advance(oid, "proposal", "r1")
            crm.advance(oid, "negotiation", "r1")
            crm.advance(oid, "won", "r1")

        self.assertEqual(crm.leads[ids[2]]["owner"], "r1")
        self.assertEqual(crm.leads[ids[3]]["owner"], "r1")
        assigns = [entry[1] for entry in crm.log if entry[0] == "assign"]
        self.assertEqual(assigns, [ids[2], ids[3]])


class DiscountTests(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(REPS)
        self.oid = make_qualified(self.crm, "a@b.com", 10000, "m1")

    def test_discount_boundary_and_no_mutation(self):
        self.crm.discount(self.oid, 30, "m1")
        self.assertEqual(self.crm.opps[self.oid]["amount"], 7000)
        before = list(self.crm.log)
        with self.assertRaises(ValueError):
            self.crm.discount(self.oid, 1, "m1")
        self.assertEqual(self.crm.opps[self.oid]["amount"], 7000)
        self.assertEqual(self.crm.log, before)

    def test_discount_permission_and_type_checks(self):
        with self.assertRaises(ValueError):
            self.crm.discount(self.oid, True, "m1")
        with self.assertRaises(ValueError):
            self.crm.discount(self.oid, 0, "m1")
        with self.assertRaises(ValueError):
            self.crm.discount(self.oid, 31, "m1")
        with self.assertRaises(PermissionError):
            self.crm.discount(self.oid, 1, "r2")
        with self.assertRaises(PermissionError):
            self.crm.discount(self.oid, 11, "r1")
        self.assertEqual(self.crm.opps[self.oid]["amount"], 10000)
        self.assertEqual(self.crm.log, [("add_lead", "L1", "m1"),
                                        ("qualify", "L1", "m1"),
                                        ("convert", "O1", "m1")])


class ForecastTests(unittest.TestCase):
    def test_forecast_accounts_for_discount_lost_and_won(self):
        crm = CRM(REPS)
        first = make_qualified(crm, "a@b.com", 1000, "m1")
        second = make_qualified(crm, "b@b.com", 2000, "m1")
        crm.advance(first, "proposal", "m1")
        crm.discount(first, 10, "m1")
        crm.advance(second, "lost", "m1")
        self.assertEqual(crm.forecast(), {"open": 1, "weighted": 270, "won": 0})
        crm.advance(first, "negotiation", "m1")
        self.assertEqual(crm.forecast(), {"open": 1, "weighted": 540, "won": 0})
        crm.advance(first, "won", "m1")
        self.assertEqual(crm.forecast(), {"open": 0, "weighted": 0, "won": 900})


if __name__ == "__main__":
    unittest.main()
