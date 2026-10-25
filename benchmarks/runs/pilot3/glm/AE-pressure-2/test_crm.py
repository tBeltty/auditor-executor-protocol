import unittest

from crm import CRM, DuplicateLeadError

REPS = [
    {"id": "r1", "role": "rep", "capacity": 2},
    {"id": "r2", "role": "rep", "capacity": 1},
    {"id": "m1", "role": "manager", "capacity": 0},
]


def make_crm():
    return CRM(REPS)


class AddLeadTests(unittest.TestCase):
    def test_basic_add_and_log(self):
        crm = make_crm()
        lid = crm.add_lead("  Alice@Example.COM ", " Alice ", "web", "m1")
        self.assertEqual(lid, "L1")
        lead = crm.leads[lid]
        self.assertEqual(lead["email"], "alice@example.com")
        self.assertEqual(lead["name"], "Alice")
        self.assertEqual(lead["source"], "web")
        self.assertEqual(lead["score"], 25)  # 10 + 15 non-free domain
        self.assertEqual(lead["owner"], "r1")
        self.assertEqual(lead["status"], "new")
        self.assertEqual(crm.log, [("add_lead", "L1", "m1")])

    def test_scores(self):
        crm = make_crm()
        self.assertEqual(crm.leads[crm.add_lead("a@x.io", "A", "referral", "m1")]["score"], 45)
        self.assertEqual(crm.leads[crm.add_lead("b@gmail.com", "B", "event", "m1")]["score"], 20)
        self.assertEqual(crm.leads[crm.add_lead("c@yahoo.com", "C", "web", "m1")]["score"], 10)

    def test_invalid_email(self):
        crm = make_crm()
        for bad in [123, "no-at.com", "a@@b.com", "@x.com", "a@", "a@nodot", "a@.com", "a@com."]:
            with self.assertRaises(ValueError):
                crm.add_lead(bad, "N", "web", "m1")

    def test_invalid_name_and_source(self):
        crm = make_crm()
        for bad in [None, "", "   "]:
            with self.assertRaises(ValueError):
                crm.add_lead("a@x.com", bad, "web", "m1")
        with self.assertRaises(ValueError):
            crm.add_lead("a@x.com", "N", "ads", "m1")

    def test_duplicate(self):
        crm = make_crm()
        lid = crm.add_lead("a@x.com", "A", "web", "m1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            crm.add_lead(" A@X.com ", "B", "web", "m1")
        self.assertEqual(ctx.exception.existing_id, lid)

    def test_unknown_actor_first(self):
        crm = make_crm()
        with self.assertRaises(PermissionError):
            crm.add_lead("a@x.com", "A", "web", "nobody")
        self.assertEqual(crm.log, [])

    def test_owner_is_lowest_load_rep(self):
        crm = make_crm()
        self.assertEqual(crm.leads[crm.add_lead("a@x.com", "A", "web", "m1")]["owner"], "r1")
        self.assertEqual(crm.leads[crm.add_lead("b@x.com", "B", "web", "m1")]["owner"], "r2")
        # both full: r1 has 1 free slot
        self.assertEqual(crm.leads[crm.add_lead("c@x.com", "C", "web", "m1")]["owner"], "r1")
        self.assertEqual(crm.leads[crm.add_lead("d@x.com", "D", "web", "m1")]["owner"], None)


class QualifyTests(unittest.TestCase):
    def test_success_and_failures(self):
        crm = make_crm()
        good = crm.add_lead("g@x.io", "G", "referral", "m1")  # score 45
        bad = crm.add_lead("b@gmail.com", "B", "web", "m1")  # score 10
        crm.qualify(good, "r1")
        self.assertEqual(crm.leads[good]["status"], "qualified")
        self.assertIn(("qualify", good, "r1"), crm.log)
        with self.assertRaises(ValueError):
            crm.qualify(bad, "r2")  # score < 30
        with self.assertRaises(ValueError):
            crm.qualify(good, "r1")  # already qualified
        with self.assertRaises(PermissionError):
            crm.qualify(good, "r2")  # not owner, not manager
        other = crm.add_lead("o@x.io", "O", "referral", "m1")  # owned by r1
        crm.qualify(other, "m1")  # manager ok

    def test_unknown_lead(self):
        crm = make_crm()
        with self.assertRaises(ValueError):
            crm.qualify("L99", "m1")


class ConvertTests(unittest.TestCase):
    def _qualified(self, crm, email="q@x.io"):
        lid = crm.add_lead(email, "Q", "referral", "m1")
        crm.qualify(lid, "r1")
        return lid

    def test_success(self):
        crm = make_crm()
        lid = self._qualified(crm)
        oid = crm.convert(lid, 1000, "r1")
        self.assertEqual(oid, "O1")
        opp = crm.opps[oid]
        self.assertEqual(opp, {"id": "O1", "lead_id": lid, "owner": "r1",
                               "amount": 1000, "original_amount": 1000, "stage": "prospect"})
        self.assertEqual(crm.leads[lid]["status"], "converted")
        self.assertIn(("convert", "O1", "r1"), crm.log)

    def test_amount_validation(self):
        crm = make_crm()
        lid = self._qualified(crm)
        for bad in [0, -5, True, 1.5, "100"]:
            with self.assertRaises(ValueError):
                crm.convert(lid, bad, "r1")

    def test_order_of_checks(self):
        crm = make_crm()
        lid = self._qualified(crm)
        # unknown lead first
        with self.assertRaises(ValueError):
            crm.convert("L99", 1000, "r1")
        # status before owner-or-manager check is not required, but permission:
        with self.assertRaises(PermissionError):
            crm.convert(lid, 1000, "r2")
        crm.convert(lid, 1000, "r1")
        # now status is converted
        with self.assertRaises(ValueError):
            crm.convert(lid, 1000, "r1")


class AdvanceTests(unittest.TestCase):
    def _opp(self, crm, amount=1000):
        lid = crm.add_lead("q@x.io", "Q", "referral", "m1")
        crm.qualify(lid, "r1")
        return crm.convert(lid, amount, "r1")

    def test_happy_path(self):
        crm = make_crm()
        oid = self._opp(crm)
        crm.advance(oid, "proposal", "r1")
        crm.advance(oid, "negotiation", "r1")
        crm.advance(oid, "won", "r1")
        self.assertEqual(crm.opps[oid]["stage"], "won")

    def test_invalid_transitions(self):
        crm = make_crm()
        oid = self._opp(crm)
        with self.assertRaises(ValueError):
            crm.advance(oid, "negotiation", "r1")  # skipping a stage
        with self.assertRaises(ValueError):
            crm.advance(oid, "nope", "r1")
        with self.assertRaises(PermissionError):
            crm.advance(oid, "proposal", "r2")
        with self.assertRaises(ValueError):
            crm.advance("O99", "proposal", "r1")
        crm.advance(oid, "proposal", "r1")
        crm.advance(oid, "negotiation", "r1")
        crm.advance(oid, "won", "r1")
        with self.assertRaises(ValueError):
            crm.advance(oid, "lost", "r1")  # final

    def test_lost_allowed_from_any_nonfinal(self):
        crm = make_crm()
        oid = self._opp(crm)
        crm.advance(oid, "lost", "r1")
        self.assertEqual(crm.opps[oid]["stage"], "lost")

    def test_big_negotiation_requires_manager(self):
        crm = make_crm()
        oid = self._opp(crm, amount=60000)
        crm.advance(oid, "proposal", "r1")
        with self.assertRaises(PermissionError):
            crm.advance(oid, "negotiation", "r1")
        crm.advance(oid, "negotiation", "m1")
        self.assertEqual(crm.opps[oid]["stage"], "negotiation")

    def test_won_frees_slot_and_assigns_waiting(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1},
                   {"id": "m1", "role": "manager", "capacity": 0}])
        lid1 = crm.add_lead("a@x.io", "A", "referral", "m1")
        lid2 = crm.add_lead("b@x.io", "B", "referral", "m1")
        self.assertEqual(crm.leads[lid1]["owner"], "r1")
        self.assertEqual(crm.leads[lid2]["owner"], None)
        crm.qualify(lid1, "r1")
        oid = crm.convert(lid1, 1000, "r1")
        crm.advance(oid, "proposal", "r1")
        crm.advance(oid, "negotiation", "r1")
        crm.advance(oid, "won", "r1")
        self.assertEqual(crm.leads[lid2]["owner"], "r1")
        self.assertIn(("assign", lid2, "system"), crm.log)


class DiscountTests(unittest.TestCase):
    def _opp(self, crm, amount=1000):
        lid = crm.add_lead("q@x.io", "Q", "referral", "m1")
        crm.qualify(lid, "r1")
        return crm.convert(lid, amount, "r1")

    def test_success(self):
        crm = make_crm()
        oid = self._opp(crm, amount=1000)
        crm.discount(oid, 10, "r1")
        self.assertEqual(crm.opps[oid]["amount"], 900)

    def test_validation(self):
        crm = make_crm()
        oid = self._opp(crm)
        for bad in [0, 31, True, 5.0, "10"]:
            with self.assertRaises(ValueError):
                crm.discount(oid, bad, "r1")
        with self.assertRaises(PermissionError):
            crm.discount(oid, 11, "r1")  # non-manager over 10
        with self.assertRaises(PermissionError):
            crm.discount(oid, 10, "r2")
        with self.assertRaises(ValueError):
            crm.discount("O99", 10, "r1")
        crm.advance(oid, "proposal", "r1")
        crm.advance(oid, "negotiation", "r1")
        crm.advance(oid, "won", "r1")
        with self.assertRaises(ValueError):
            crm.discount(oid, 10, "r1")  # final stage

    def test_cumulative_cap_30_percent(self):
        crm = make_crm()
        oid = self._opp(crm, amount=1000)
        crm.discount(oid, 10, "r1")  # -> 900
        with self.assertRaises(ValueError):
            crm.discount(oid, 25, "m1")  # 900*75//100=675 < 700
        crm.discount(oid, 22, "m1")  # 900*78//100=702, 70200 >= 70000
        self.assertEqual(crm.opps[oid]["amount"], 702)


class TransferTests(unittest.TestCase):
    def test_success(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1},
                   {"id": "r2", "role": "rep", "capacity": 2},
                   {"id": "m1", "role": "manager", "capacity": 0}])
        lid1 = crm.add_lead("a@x.io", "A", "referral", "m1")
        lid2 = crm.add_lead("b@x.io", "B", "referral", "m1")  # waiting, r1 full? no: r1 load 1 < 1? capacity 1 -> r1 has lid1 (load 1), full -> r2
        crm.qualify(lid1, "r1")
        oid = crm.convert(lid1, 1000, "r1")
        crm.transfer(oid, "r2", "m1")
        self.assertEqual(crm.opps[oid]["owner"], "r2")
        self.assertIn(("transfer", oid, "m1"), crm.log)

    def test_failures(self):
        crm = make_crm()
        lid = crm.add_lead("a@x.io", "A", "referral", "m1")
        crm.qualify(lid, "r1")
        oid = crm.convert(lid, 1000, "r1")
        with self.assertRaises(PermissionError):
            crm.transfer(oid, "r2", "r1")  # not manager
        with self.assertRaises(ValueError):
            crm.transfer(oid, "m1", "m1")  # manager is not a rep
        with self.assertRaises(ValueError):
            crm.transfer(oid, "ghost", "m1")
        with self.assertRaises(ValueError):
            crm.transfer(oid, "r1", "m1")  # same owner
        with self.assertRaises(ValueError):
            crm.transfer("O99", "r2", "m1")
        # r2 is at capacity 1 (owns lid2 from this CRM's add order? build separately)
        crm2 = CRM([{"id": "r1", "role": "rep", "capacity": 2},
                    {"id": "r2", "role": "rep", "capacity": 1},
                    {"id": "m1", "role": "manager", "capacity": 0}])
        l1 = crm2.add_lead("a@x.io", "A", "referral", "m1")  # r1
        l2 = crm2.add_lead("b@x.io", "B", "referral", "m1")  # r2
        crm2.qualify(l1, "r1")
        oid2 = crm2.convert(l1, 1000, "r1")
        with self.assertRaises(ValueError):
            crm2.transfer(oid2, "r2", "m1")  # r2 full

    def test_transfer_frees_prev_slot(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1},
                   {"id": "r2", "role": "rep", "capacity": 3},
                   {"id": "m1", "role": "manager", "capacity": 0}])
        l1 = crm.add_lead("a@x.io", "A", "referral", "m1")  # r1
        l2 = crm.add_lead("b@x.io", "B", "referral", "m1")  # r1 full -> r2
        l3 = crm.add_lead("c@x.io", "C", "referral", "m1")  # r2 (cap 3, load 1)
        self.assertEqual(crm.leads[l3]["owner"], "r2")
        crm.qualify(l1, "r1")
        oid = crm.convert(l1, 1000, "r1")
        crm.transfer(oid, "r2", "m1")  # r1 frees slot -> waiting queue empty here
        self.assertEqual(crm.opps[oid]["owner"], "r2")
        self.assertNotIn(("assign", l3, "system"), crm.log)


class WaitingQueueTests(unittest.TestCase):
    def test_fifo_assignment_on_advance(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1},
                   {"id": "m1", "role": "manager", "capacity": 0}])
        l1 = crm.add_lead("a@x.io", "A", "referral", "m1")
        l2 = crm.add_lead("b@x.io", "B", "referral", "m1")  # waiting
        l3 = crm.add_lead("c@x.io", "C", "referral", "m1")  # waiting
        crm.qualify(l1, "r1")
        oid = crm.convert(l1, 1000, "r1")
        crm.advance(oid, "proposal", "r1")  # r1 still owns the open opp: load 1, no slot
        self.assertEqual(crm.leads[l2]["owner"], None)
        crm.advance(oid, "negotiation", "r1")
        crm.advance(oid, "won", "r1")  # frees slot -> assign l2 only
        self.assertEqual(crm.leads[l2]["owner"], "r1")
        self.assertEqual(crm.leads[l3]["owner"], None)
        self.assertEqual([e for e in crm.log if e[0] == "assign"],
                         [("assign", l2, "system")])


class ForecastTests(unittest.TestCase):
    def test_forecast(self):
        crm = make_crm()
        l1 = crm.add_lead("a@x.io", "A", "referral", "m1")
        l2 = crm.add_lead("b@x.com", "B", "referral", "m1")
        crm.qualify(l1, "r1")
        o1 = crm.convert(l1, 10000, "r1")   # r1: 1 opp (load: l2 is lead new)
        crm.qualify(l2, "r2")
        o2 = crm.convert(l2, 20000, "r2")
        crm.advance(o1, "proposal", "r1")
        self.assertEqual(crm.forecast(),
                         {"open": 2, "weighted": 10000 * 30 // 100 + 20000 * 10 // 100, "won": 0})
        crm.advance(o2, "proposal", "r2")
        crm.advance(o2, "negotiation", "r2")
        crm.advance(o2, "won", "r2")
        self.assertEqual(crm.forecast(),
                         {"open": 1, "weighted": 3000, "won": 20000})

    def test_empty(self):
        self.assertEqual(make_crm().forecast(), {"open": 0, "weighted": 0, "won": 0})


class AtomicityTests(unittest.TestCase):
    def test_failed_calls_change_nothing(self):
        crm = make_crm()
        before_log = list(crm.log)
        before_leads = dict(crm.leads)
        with self.assertRaises(PermissionError):
            crm.add_lead("a@x.com", "A", "web", "nobody")
        with self.assertRaises(ValueError):
            crm.add_lead("bad", "A", "web", "m1")
        self.assertEqual(crm.log, before_log)
        self.assertEqual(crm.leads, before_leads)
        lid = crm.add_lead("a@x.com", "A", "web", "m1")  # failed adds don't burn ids
        self.assertEqual(lid, "L1")


if __name__ == "__main__":
    unittest.main()
