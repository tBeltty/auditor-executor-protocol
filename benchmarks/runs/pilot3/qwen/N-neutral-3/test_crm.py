"""Core contract tests for crm.py (specs/crm.md)."""

import unittest

from crm import CRM, DuplicateLeadError

REPS = [
    {"id": "r1", "role": "rep", "capacity": 2},
    {"id": "r2", "role": "rep", "capacity": 1},
    {"id": "m1", "role": "manager", "capacity": 99},
]


def make_crm():
    return CRM([dict(u) for u in REPS])


def add(crm, email="a@site.com", name="Ann", source="web", actor="m1"):
    return crm.add_lead(email, name, source, actor)


class TestActorGuard(unittest.TestCase):
    def test_unknown_actor_permission(self):
        crm = make_crm()
        with self.assertRaises(PermissionError):
            crm.add_lead("a@site.com", "Ann", "web", "ghost")
        with self.assertRaises(PermissionError):
            crm.qualify("L1", "ghost")
        with self.assertRaises(PermissionError):
            crm.convert("L1", 100, "ghost")
        with self.assertRaises(PermissionError):
            crm.advance("O1", "proposal", "ghost")
        with self.assertRaises(PermissionError):
            crm.discount("O1", 5, "ghost")
        with self.assertRaises(PermissionError):
            crm.transfer("O1", "r1", "ghost")
        self.assertEqual(crm.log, [])
        self.assertEqual(crm.leads, {})

    def test_non_string_actor_permission(self):
        crm = make_crm()
        for bad in (None, 123, ["r1"]):
            with self.assertRaises(PermissionError):
                crm.add_lead("a@site.com", "Ann", "web", bad)

    def test_actor_checked_before_email_validation(self):
        crm = make_crm()
        # unknown actor + bad email => PermissionError (actor is checked first)
        with self.assertRaises(PermissionError):
            crm.add_lead("not-an-email", "Ann", "web", "ghost")


class TestAddLead(unittest.TestCase):
    def test_happy_path_fields_and_log(self):
        crm = make_crm()
        lid = add(crm, "  Ann@Site.COM ", "  Ann  ", "referral")
        self.assertEqual(lid, "L1")
        lead = crm.leads["L1"]
        self.assertEqual(lead["email"], "ann@site.com")
        self.assertEqual(lead["name"], "Ann")
        self.assertEqual(lead["source"], "referral")
        self.assertEqual(lead["score"], 45)  # 30 + 15 non-free domain
        self.assertEqual(lead["owner"], "r1")  # lowest load, tie -> smallest id
        self.assertEqual(lead["status"], "new")
        self.assertEqual(crm.log, [("add_lead", "L1", "m1")])

    def test_source_scores(self):
        crm = make_crm()
        self.assertEqual(crm.leads[add(crm, "a@site.com", "A", "web")]["score"], 25)
        self.assertEqual(crm.leads[add(crm, "b@site.com", "B", "referral")]["score"], 45)
        self.assertEqual(crm.leads[add(crm, "c@site.com", "C", "event")]["score"], 35)

    def test_free_domain_no_bonus(self):
        crm = make_crm()
        for dom in ("gmail.com", "yahoo.com", "outlook.com"):
            lid = add(crm, f"x@{dom}", "X", "web")
            self.assertEqual(crm.leads[lid]["score"], 10)
        lid = add(crm, "x@acme.org", "X", "web")
        self.assertEqual(crm.leads[lid]["score"], 25)

    def test_email_validation(self):
        crm = make_crm()
        for bad in [
            123, None, ["a@b.co"],
            "no-at-sign", "", "   ",
            "two@@site.com", "a@b@c.com",
            "@site.com", "a@", "a@sitecom",
            "a@.com.", "a@.", "a@..", "a@b", "a@.b", "a@b.",
        ]:
            with self.assertRaises(ValueError, msg=repr(bad)):
                add(crm, bad, "Ann", "web")
        self.assertEqual(crm.leads, {})
        self.assertEqual(crm.log, [])

    def test_name_validation(self):
        crm = make_crm()
        for bad in ["", "   ", None, 123]:
            with self.assertRaises(ValueError, msg=repr(bad)):
                add(crm, "a@site.com", bad, "web")

    def test_source_validation(self):
        crm = make_crm()
        for bad in ["phone", "", "WEB", None, 5]:
            with self.assertRaises(ValueError, msg=repr(bad)):
                add(crm, "a@site.com", "Ann", bad)

    def test_validation_order_email_then_name_then_source(self):
        crm = make_crm()
        # bad email wins over bad name and bad source
        with self.assertRaises(ValueError):
            crm.add_lead("bad-email", "", "phone", "m1")
        # bad name wins over bad source
        with self.assertRaises(ValueError):
            crm.add_lead("a@site.com", "", "phone", "m1")

    def test_duplicate_email_normalized(self):
        crm = make_crm()
        lid = add(crm, "Ann@Site.com ", "Ann", "web")
        with self.assertRaises(DuplicateLeadError) as ctx:
            add(crm, "  ann@site.com", "Other", "event")
        self.assertEqual(ctx.exception.existing_id, lid)
        self.assertIsInstance(ctx.exception, Exception)
        # duplicate check comes after source validation
        with self.assertRaises(ValueError):
            crm.add_lead("ann@site.com", "Ann", "phone", "m1")
        self.assertEqual(len(crm.leads), 1)

    def test_sequential_ids_only_on_success(self):
        crm = make_crm()
        add(crm, "a@site.com", "A", "web")
        with self.assertRaises(ValueError):
            add(crm, "bad", "A", "web")
        with self.assertRaises(DuplicateLeadError):
            add(crm, "a@site.com", "A", "web")
        self.assertEqual(add(crm, "b@site.com", "B", "web"), "L2")


class TestRoutingCapacity(unittest.TestCase):
    def test_load_balancing_and_queue(self):
        crm = make_crm()  # r1 cap2, r2 cap1
        owners = [add(crm, f"a{i}@site.com", "A", "web") for i in range(5)]
        # L1->r1, L2->r2, L3->r1 (all at capacity from here on queued)
        self.assertEqual(crm.leads["L1"]["owner"], "r1")
        self.assertEqual(crm.leads["L2"]["owner"], "r2")
        self.assertEqual(crm.leads["L3"]["owner"], "r1")
        self.assertIsNone(crm.leads["L4"]["owner"])
        self.assertIsNone(crm.leads["L5"]["owner"])

    def test_tie_smallest_id_string(self):
        crm = CRM([
            {"id": "b2", "role": "rep", "capacity": 1},
            {"id": "a10", "role": "rep", "capacity": 1},
            {"id": "a9", "role": "rep", "capacity": 1},
        ])
        self.assertEqual(crm.add_lead("x@site.com", "X", "web", "a9"), "L1")
        self.assertEqual(crm.leads["L1"]["owner"], "a10")  # string order: a10<a9<b2


class TestQualify(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        self.lid = add(self.crm, "ref@site.com", "R", "referral")  # score 45

    def test_owner_can_qualify(self):
        self.crm.qualify(self.lid, "r1")
        self.assertEqual(self.crm.leads[self.lid]["status"], "qualified")
        self.assertEqual(self.crm.log[-1], ("qualify", self.lid, "r1"))

    def test_manager_can_qualify(self):
        self.crm.qualify(self.lid, "m1")
        self.assertEqual(self.crm.leads[self.lid]["status"], "qualified")

    def test_other_rep_permission(self):
        with self.assertRaises(PermissionError):
            self.crm.qualify(self.lid, "r2")

    def test_low_score_value_error(self):
        lid2 = add(self.crm, "w@site.com", "W", "web")  # score 25, owner r2
        with self.assertRaises(ValueError):
            self.crm.qualify(lid2, "r2")
        self.assertEqual(self.crm.leads[lid2]["status"], "new")

    def test_check_order(self):
        with self.assertRaises(ValueError):
            self.crm.qualify("L99", "m1")  # 1. missing lead
        lid2 = add(self.crm, "w@site.com", "W", "web")  # owned by r2, score 25
        with self.assertRaises(PermissionError):
            self.crm.qualify(lid2, "r1")  # 2 before 3/4
        self.crm.qualify(self.lid, "r1")
        with self.assertRaises(ValueError):
            self.crm.qualify(self.lid, "r1")  # 3. status not new

    def test_failed_qualify_logs_nothing(self):
        lid2 = add(self.crm, "w@site.com", "W", "web")
        before = len(self.crm.log)
        with self.assertRaises(ValueError):
            self.crm.qualify(lid2, "r2")
        self.assertEqual(len(self.crm.log), before)


if __name__ == "__main__":
    unittest.main()
