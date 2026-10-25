"""Extra edge-case tests for crm.py (specs/crm.md): email normalization,
failed-call atomicity, queue ordering, load accounting details."""

import unittest

from crm import CRM, DuplicateLeadError

REPS = [
    {"id": "r1", "role": "rep", "capacity": 2},
    {"id": "r2", "role": "rep", "capacity": 1},
    {"id": "m1", "role": "manager", "capacity": 99},
]


def make_crm():
    return CRM([dict(u) for u in REPS])


class TestEmailNormalization(unittest.TestCase):
    def test_strip_case_domain_bonus(self):
        crm = make_crm()
        lid = crm.add_lead("  Jo.Hn@ACME.COM ", "J", "web", "m1")
        self.assertEqual(crm.leads[lid]["email"], "jo.hn@acme.com")
        self.assertEqual(crm.leads[lid]["score"], 25)

    def test_case_insensitive_duplicate(self):
        crm = make_crm()
        lid = crm.add_lead("A@Site.com", "A", "web", "m1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            crm.add_lead(" a@SITE.COM ", "B", "referral", "m1")
        self.assertEqual(ctx.exception.existing_id, lid)

    def test_subdomain_ok(self):
        crm = make_crm()
        self.assertEqual(
            crm.add_lead("a@mail.acme.co.uk", "A", "web", "m1"), "L1")

    def test_domain_edge_shapes(self):
        crm = make_crm()
        # "a@b.c" is valid: dot is neither first nor last char of domain "b.c"
        self.assertEqual(crm.add_lead("a@b.c", "A", "web", "m1"), "L1")
        self.assertEqual(crm.add_lead("a@b.cd", "B", "web", "m1"), "L2")
        for bad in ["a@.", "a@.b", "a@b.", "a@.."]:
            with self.assertRaises(ValueError, msg=bad):
                crm.add_lead(bad, "A", "web", "m1")


class TestLoadAccounting(unittest.TestCase):
    def test_qualify_does_not_change_load(self):
        crm = make_crm()
        l1 = crm.add_lead("a@site.com", "A", "referral", "m1")  # r1 load 1
        crm.qualify(l1, "m1")  # qualified still counts: r1 load stays 1
        l2 = crm.add_lead("b@site.com", "B", "referral", "m1")
        # r1 load 1 vs r2 load 0 -> lowest is r2
        self.assertEqual(crm.leads[l2]["owner"], "r2")

    def test_converted_lead_no_longer_counts_as_lead(self):
        crm = make_crm()
        l1 = crm.add_lead("a@site.com", "A", "referral", "m1")
        crm.qualify(l1, "m1")
        crm.convert(l1, 10, "m1")  # lead stops counting, opp counts: r1 stays 1
        l2 = crm.add_lead("b@site.com", "B", "web", "m1")
        self.assertEqual(crm.leads[l2]["owner"], "r2")  # r1 load 1, r2 load 0

    def test_won_or_lost_opp_exits_load(self):
        crm = make_crm()
        lids = [crm.add_lead(f"w{i}@site.com", "W", "referral", "m1")
                for i in range(3)]  # r1, r2, r1
        opps = []
        for lid in lids:
            crm.qualify(lid, "m1")
            opps.append(crm.convert(lid, 10, "m1"))
        # loads r1=2 (2 opps), r2=1 (1 opp) -> both at cap
        self.assertIsNone(crm.add_lead("z@site.com", "Z", "web", "m1") and
                          crm.leads["L4"]["owner"])
        crm.advance(opps[0], "lost", "m1")  # O1 owned r1 -> frees r1 slot
        self.assertEqual(crm.leads["L4"]["owner"], "r1")
        self.assertEqual(crm.leads["L4"]["status"], "new")

    def test_queue_is_fifo(self):
        crm = make_crm()
        lids = [crm.add_lead(f"p{i}@site.com", "P", "referral", "m1")
                for i in range(5)]  # L1 r1, L2 r2, L3 r1, L4+L5 queued
        self.assertEqual(crm.leads["L4"]["owner"], None)
        self.assertEqual(crm.leads["L5"]["owner"], None)
        crm.qualify(lids[0], "m1")
        crm.convert(lids[0], 10, "m1")   # no slot change (r1 still 2)
        crm.advance("O1", "lost", "m1")  # r1 frees one
        self.assertEqual(crm.leads["L4"]["owner"], "r1")  # oldest first
        self.assertEqual(crm.log[-1], ("assign", "L4", "system"))
        self.assertIsNone(crm.leads["L5"]["owner"])


class TestAtomicity(unittest.TestCase):
    def _snapshot(self, crm):
        import copy
        return copy.deepcopy((crm.leads, crm.opps, list(crm.log)))

    def _assert_unchanged(self, crm, snap):
        import copy
        self.assertEqual(snap, copy.deepcopy((crm.leads, crm.opps, list(crm.log))))

    def test_every_failure_is_inert(self):
        crm = make_crm()
        l1 = crm.add_lead("a@site.com", "A", "referral", "m1")
        crm.qualify(l1, "m1")
        o1 = crm.convert(l1, 100, "m1")
        cases = [
            (crm.add_lead, ("bad", "A", "web", "m1")),
            (crm.add_lead, ("a@site.com", "A", "web", "m1")),
            (crm.add_lead, ("n@site.com", "A", "web", "ghost")),
            (crm.qualify, ("L9", "m1")),
            (crm.qualify, (l1, "m1")),           # already qualified
            (crm.convert, (l1, 0, "m1")),        # already converted + bad amount
            (crm.convert, ("L9", 10, "m1")),
            (crm.advance, (o1, "bogus", "m1")),
            (crm.advance, (o1, "won", "m1")),    # illegal skip
            (crm.discount, (o1, 0, "m1")),
            (crm.discount, (o1, 5, "r2")),
            (crm.transfer, (o1, "r2", "r1")),    # rep actor
            (crm.transfer, (o1, "m1", "m1")),    # manager not rep
        ]
        for fn, args in cases:
            snap = self._snapshot(crm)
            with self.assertRaises((ValueError, PermissionError,
                                    DuplicateLeadError)):
                fn(*args)
            self._assert_unchanged(crm, snap)

    def test_assign_not_logged_for_failed_calls(self):
        crm = make_crm()
        lids = [crm.add_lead(f"q{i}@site.com", "Q", "referral", "m1")
                for i in range(4)]
        for lid in lids[:3]:
            crm.qualify(lid, "m1")
            crm.convert(lid, 60001, "m1")
        with self.assertRaises(PermissionError):
            crm.advance("O1", "negotiation", "r2")  # r2 actor, needs manager... r2 owns O1? O1 owner r2 (L2->r2)
        # wait O1 from L2? order: L1->r1, L2->r2, L3->r1. O1 from L1? convert in loop order:
        # lids[:3] = L1,L2,L3 -> O1(L1,r1), O2(L2,r2), O3(L3,r1)
        # r2 owns O2. So O1 owner is r1: r1 tried negotiation on >50000 -> PermissionError
        self.assertEqual(crm.leads["L4"]["owner"], None)
        self.assertNotIn("assign", [e[0] for e in crm.log])


class TestManagersNeverOwn(unittest.TestCase):
    def test_manager_capacity_ignored(self):
        crm = CRM([
            {"id": "m1", "role": "manager", "capacity": 100},
            {"id": "r1", "role": "rep", "capacity": 1},
        ])
        l1 = crm.add_lead("a@site.com", "A", "web", "m1")
        self.assertEqual(crm.leads[l1]["owner"], "r1")
        l2 = crm.add_lead("b@site.com", "B", "web", "m1")
        self.assertIsNone(crm.leads[l2]["owner"])  # queued, never m1

    def test_only_managers_no_reps(self):
        crm = CRM([{"id": "m1", "role": "manager", "capacity": 5}])
        lid = crm.add_lead("a@site.com", "A", "web", "m1")
        self.assertIsNone(crm.leads[lid]["owner"])
        self.assertEqual(crm.log[-1], ("add_lead", lid, "m1"))


if __name__ == "__main__":
    unittest.main()
