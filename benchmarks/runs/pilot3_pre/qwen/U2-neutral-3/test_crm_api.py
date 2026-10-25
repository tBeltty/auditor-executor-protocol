"""Tests for crm.py: actors, add_lead validation/routing, qualify."""

import unittest

from crm import CRM, DuplicateLeadError

REPS = [
    {"id": "r1", "role": "rep", "capacity": 2},
    {"id": "r2", "role": "rep", "capacity": 1},
    {"id": "m1", "role": "manager", "capacity": 99},
]


def make_crm():
    return CRM([dict(u) for u in REPS])


class TestActorGuard(unittest.TestCase):
    def test_unknown_actor_raises_permission_first(self):
        crm = make_crm()
        with self.assertRaises(PermissionError):
            crm.add_lead("a@site.com", "A", "web", "ghost")
        with self.assertRaises(PermissionError):
            crm.qualify("L1", "ghost")
        with self.assertRaises(PermissionError):
            crm.convert("L1", 10, "ghost")
        with self.assertRaises(PermissionError):
            crm.advance("O1", "proposal", "ghost")
        with self.assertRaises(PermissionError):
            crm.discount("O1", 5, "ghost")
        with self.assertRaises(PermissionError):
            crm.transfer("O1", "r1", "ghost")
        self.assertEqual(crm.log, [])
        self.assertEqual(crm.leads, {})
        self.assertEqual(crm.opps, {})

    def test_actor_checked_before_other_validation(self):
        crm = make_crm()
        with self.assertRaises(PermissionError):
            crm.add_lead("nope", "", "bogus", "ghost")

    def test_non_string_actor(self):
        crm = make_crm()
        for bad in (None, 7, ["r1"]):
            with self.assertRaises(PermissionError):
                crm.add_lead("a@site.com", "A", "web", bad)


class TestAddLead(unittest.TestCase):
    def test_happy_path_and_fields(self):
        crm = make_crm()
        lid = crm.add_lead("  Ann@Site.COM ", "  Ann  ", "referral", "m1")
        self.assertEqual(lid, "L1")
        self.assertEqual(crm.leads[lid], {
            "id": "L1", "email": "ann@site.com", "name": "Ann",
            "source": "referral", "score": 45, "owner": "r1", "status": "new",
        })
        self.assertEqual(crm.log, [("add_lead", "L1", "m1")])

    def test_scores(self):
        crm = make_crm()
        self.assertEqual(crm.leads[crm.add_lead("a@site.com", "A", "web", "m1")]["score"], 25)
        self.assertEqual(crm.leads[crm.add_lead("b@site.com", "B", "referral", "m1")]["score"], 45)
        self.assertEqual(crm.leads[crm.add_lead("c@site.com", "C", "event", "m1")]["score"], 35)

    def test_free_domain_bonus(self):
        crm = make_crm()
        for dom in ("gmail.com", "yahoo.com", "outlook.com"):
            lid = crm.add_lead(f"x@{dom}", "X", "web", "m1")
            self.assertEqual(crm.leads[lid]["score"], 10)

    def test_invalid_emails(self):
        crm = make_crm()
        for bad in [42, None, "at", "@site.com", "a@", "a@b@c.com", "a@@b.c",
                    "a@sitecom", "a@.", "a@.b", "a@b.", "a@.."]:
            with self.assertRaises(ValueError, msg=repr(bad)):
                crm.add_lead(bad, "A", "web", "m1")
        self.assertEqual(crm.leads, {})

    def test_valid_email_shapes(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 9}])
        for ok in ["a@b.c", "a@mail.acme.co.uk", " A@Gmail.COM "]:
            crm.add_lead(ok, "A", "web", "r1")

    def test_name_and_source_validation(self):
        crm = make_crm()
        for bad in ["", "   ", None, 5]:
            with self.assertRaises(ValueError):
                crm.add_lead("a@site.com", bad, "web", "m1")
        for bad in ["phone", "WEB", "", None]:
            with self.assertRaises(ValueError):
                crm.add_lead("a@site.com", "A", bad, "m1")

    def test_validation_order(self):
        crm = make_crm()
        with self.assertRaises(ValueError):      # email beats name and source
            crm.add_lead("bad", "", "phone", "m1")
        with self.assertRaises(ValueError):      # name beats source
            crm.add_lead("a@site.com", "", "phone", "m1")

    def test_duplicate_normalized_email(self):
        crm = make_crm()
        lid = crm.add_lead("Ann@Site.com", "Ann", "web", "m1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            crm.add_lead("  ann@SITE.com ", "Other", "event", "m1")
        self.assertEqual(ctx.exception.existing_id, lid)
        self.assertIsInstance(ctx.exception, Exception)
        self.assertEqual(len(crm.leads), 1)

    def test_ids_count_only_successes(self):
        crm = make_crm()
        crm.add_lead("a@site.com", "A", "web", "m1")
        with self.assertRaises(ValueError):
            crm.add_lead("bad", "A", "web", "m1")
        with self.assertRaises(DuplicateLeadError):
            crm.add_lead("a@site.com", "A", "web", "m1")
        self.assertEqual(crm.add_lead("b@site.com", "B", "web", "m1"), "L2")

    def test_routing_lowest_load_tie_smallest_id(self):
        crm = make_crm()
        l1 = crm.add_lead("a@site.com", "A", "web", "m1")
        l2 = crm.add_lead("b@site.com", "B", "web", "m1")
        l3 = crm.add_lead("c@site.com", "C", "web", "m1")
        l4 = crm.add_lead("d@site.com", "D", "web", "m1")
        self.assertEqual(crm.leads[l1]["owner"], "r1")   # tie 0 -> smallest id
        self.assertEqual(crm.leads[l2]["owner"], "r2")   # load 0 beats r1's 1
        self.assertEqual(crm.leads[l3]["owner"], "r1")   # r2 full
        self.assertIsNone(crm.leads[l4]["owner"])        # everyone full: queue

    def test_string_order_tie(self):
        crm = CRM([{"id": "b2", "role": "rep", "capacity": 1},
                   {"id": "a10", "role": "rep", "capacity": 1},
                   {"id": "a9", "role": "rep", "capacity": 1}])
        lid = crm.add_lead("x@site.com", "X", "web", "a9")
        self.assertEqual(crm.leads[lid]["owner"], "a10")  # "a10" < "a9" < "b2"

    def test_managers_never_own(self):
        crm = CRM([{"id": "m1", "role": "manager", "capacity": 50}])
        lid = crm.add_lead("a@site.com", "A", "web", "m1")
        self.assertIsNone(crm.leads[lid]["owner"])


class TestQualify(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        self.lid = self.crm.add_lead("a@site.com", "A", "referral", "m1")  # score 45

    def test_owner_and_manager_paths(self):
        self.crm.qualify(self.lid, "r1")
        self.assertEqual(self.crm.leads[self.lid]["status"], "qualified")
        self.assertEqual(self.crm.log[-1], ("qualify", self.lid, "r1"))
        lid2 = self.crm.add_lead("b@site.com", "B", "referral", "m1")
        self.crm.qualify(lid2, "m1")                      # manager ok

    def test_other_rep_permission(self):
        with self.assertRaises(PermissionError):
            self.crm.qualify(self.lid, "r2")

    def test_score_floor(self):
        lid = self.crm.add_lead("c@site.com", "C", "web", "m1")  # score 25, owner r2
        with self.assertRaises(ValueError):
            self.crm.qualify(lid, "r2")
        self.assertEqual(self.crm.leads[lid]["status"], "new")

    def test_check_order(self):
        with self.assertRaises(ValueError):
            self.crm.qualify("L99", "m1")                 # 1 existence
        with self.assertRaises(PermissionError):
            self.crm.qualify(self.lid, "r2")              # 2 owner/mgr
        self.crm.qualify(self.lid, "m1")
        with self.assertRaises(ValueError):
            self.crm.qualify(self.lid, "m1")              # 3 status new

    def test_failed_call_inert(self):
        before = (dict(self.crm.leads["L1"]), list(self.crm.log))
        with self.assertRaises(ValueError):
            self.crm.qualify("nope", "m1")
        self.assertEqual(self.crm.log, before[1])


if __name__ == "__main__":
    unittest.main()
