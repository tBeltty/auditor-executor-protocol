import copy
import unittest

from crm import CRM, DuplicateLeadError


BASE_REPS = [
    {"id": "r1", "role": "rep", "capacity": 50},
    {"id": "r2", "role": "rep", "capacity": 0},
    {"id": "m1", "role": "manager", "capacity": 5},
]


class CRMLeadTests(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(copy.deepcopy(BASE_REPS))
        self._seq = 0

    def email(self):
        self._seq += 1
        return "lead%d@corp.com" % self._seq

    def add(self, email=None, name="Ada", source="referral", actor="r1"):
        return self.crm.add_lead(self.email() if email is None else email,
                                 name, source, actor)

    # ---------------------------------------------------------------- add_lead
    def test_add_lead_happy_path_normalizes_and_scores(self):
        lid = self.crm.add_lead("  Ada@Gmail.COM ", "  Ada Lovelace  ", "web", "r1")
        self.assertEqual(lid, "L1")
        lead = self.crm.leads[lid]
        self.assertEqual(lead["email"], "ada@gmail.com")
        self.assertEqual(lead["name"], "Ada Lovelace")
        self.assertEqual(lead["score"], 10)
        self.assertEqual(lead["owner"], "r1")
        self.assertEqual(lead["status"], "new")
        self.assertEqual(self.crm.log[-1], ("add_lead", "L1", "r1"))

        self.assertEqual(self.crm.leads[self.add(source="event")]["score"], 35)
        self.assertEqual(self.crm.leads[self.add(source="referral")]["score"], 45)

    def test_add_lead_corporate_domain_bonus(self):
        web = self.crm.leads[self.crm.add_lead("a@corp.com", "A", "web", "r1")]
        self.assertEqual(web["score"], 25)
        event = self.crm.leads[self.crm.add_lead("b@corp.com", "B", "event", "r1")]
        self.assertEqual(event["score"], 35)
        referral = self.crm.leads[self.crm.add_lead("c@corp.com", "C", "referral", "r1")]
        self.assertEqual(referral["score"], 45)

    def test_add_lead_ids_count_only_successes(self):
        self.assertEqual(self.add(), "L1")
        with self.assertRaises(DuplicateLeadError):
            self.add(email="lead1@corp.com")
        with self.assertRaises(ValueError):
            self.crm.add_lead("bad", "X", "web", "r1")
        self.assertEqual(self.add(), "L2")

    def test_add_lead_rejects_bad_emails(self):
        for bad in ["plain", "@x.com", "a@", "a@b", "a@.com", "a@com.",
                    "a@b@c.com", "a@@b.com", 123, None]:
            with self.subTest(email=bad):
                with self.assertRaises(ValueError):
                    self.crm.add_lead(bad, "Name", "web", "r1")
        self.assertEqual(self.crm.leads, {})
        self.assertEqual(self.crm.log, [])

    def test_add_lead_rejects_bad_names_and_sources(self):
        for bad_name in ["", "   ", None, 5]:
            with self.subTest(name=bad_name):
                with self.assertRaises(ValueError):
                    self.crm.add_lead("a@corp.com", bad_name, "web", "r1")
        for bad_source in ["", "Web", "cold", None]:
            with self.subTest(source=bad_source):
                with self.assertRaises(ValueError):
                    self.crm.add_lead("a@corp.com", "Name", bad_source, "r1")

    def test_add_lead_duplicate_is_case_and_space_insensitive(self):
        first = self.crm.add_lead("A@Corp.com", "A", "web", "r1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            self.crm.add_lead("  a@CORP.COM ", "Other", "event", "r1")
        self.assertEqual(ctx.exception.existing_id, first)
        self.assertEqual(len(self.crm.leads), 1)
        self.assertEqual(len(self.crm.log), 1)

    def test_owner_is_lowest_load_with_smallest_id_tiebreak(self):
        crm = CRM([
            {"id": "r2", "role": "rep", "capacity": 1},
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 5},
        ])
        self.assertEqual(crm.add_lead("a@corp.com", "A", "web", "r1"), "L1")
        self.assertEqual(crm.leads["L1"]["owner"], "r1")
        crm.add_lead("b@corp.com", "B", "web", "r1")
        self.assertEqual(crm.leads["L2"]["owner"], "r2")
        crm.add_lead("c@corp.com", "C", "web", "r1")
        self.assertIsNone(crm.leads["L3"]["owner"])

    def test_managers_and_zero_capacity_reps_never_own(self):
        crm = CRM([
            {"id": "m1", "role": "manager", "capacity": 10},
            {"id": "r0", "role": "rep", "capacity": 0},
        ])
        crm.add_lead("a@corp.com", "A", "web", "m1")
        self.assertIsNone(crm.leads["L1"]["owner"])

    def test_load_prefers_rep_with_room(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 3},
        ])
        crm.add_lead("a@corp.com", "A", "web", "r1")
        crm.add_lead("b@corp.com", "B", "web", "r1")
        self.assertEqual(crm.leads["L1"]["owner"], "r1")
        self.assertEqual(crm.leads["L2"]["owner"], "r2")

    def test_unknown_actor_is_rejected_first(self):
        with self.assertRaises(PermissionError):
            self.crm.add_lead(123, "", "nope", "ghost")
        self.assertEqual(self.crm.leads, {})
        self.assertEqual(self.crm.log, [])

    # ----------------------------------------------------------------- qualify
    def test_qualify_requires_score_and_new_status(self):
        web = self.add(source="web")
        with self.assertRaises(ValueError):
            self.crm.qualify(web, "r1")
        event = self.add(source="event")
        self.crm.qualify(event, "r1")
        self.assertEqual(self.crm.leads[event]["status"], "qualified")
        with self.assertRaises(ValueError):
            self.crm.qualify(event, "r1")

    def test_qualify_permissions(self):
        lid = self.add()
        with self.assertRaises(PermissionError):
            self.crm.qualify(lid, "r2")
        self.assertEqual(self.crm.leads[lid]["status"], "new")
        self.crm.qualify(lid, "m1")
        self.assertEqual(self.crm.leads[lid]["status"], "qualified")

    def test_qualify_unknown_lead_and_actor(self):
        with self.assertRaises(ValueError):
            self.crm.qualify("L404", "r1")
        with self.assertRaises(PermissionError):
            self.crm.qualify("L404", "ghost")

    # ----------------------------------------------------------------- convert
    def test_convert_creates_opportunity(self):
        lid = self.add()
        self.crm.qualify(lid, "r1")
        opp = self.crm.convert(lid, 1500, "r1")
        self.assertEqual(opp, "O1")
        self.assertEqual(self.crm.leads[lid]["status"], "converted")
        self.assertEqual(self.crm.opps[opp], {
            "id": "O1", "lead_id": lid, "owner": "r1", "amount": 1500,
            "original_amount": 1500, "stage": "prospect",
        })
        self.assertEqual(self.crm.log[-1], ("convert", "O1", "r1"))

    def test_convert_ids_count_only_successes(self):
        lid1 = self.add()
        lid2 = self.add()
        self.crm.qualify(lid1, "r1")
        self.crm.qualify(lid2, "r1")
        self.assertEqual(self.crm.convert(lid1, 100, "r1"), "O1")
        with self.assertRaises(ValueError):
            self.crm.convert(lid1, 0, "r1")
        self.assertEqual(self.crm.convert(lid2, 100, "r1"), "O2")

    def test_convert_rejects_bad_amounts(self):
        lid = self.add()
        self.crm.qualify(lid, "r1")
        for bad in [0, -1, True, False, 1.5, "10", None]:
            with self.subTest(amount=bad):
                with self.assertRaises(ValueError):
                    self.crm.convert(lid, bad, "r1")
        self.assertEqual(self.crm.opps, {})
        self.assertEqual(self.crm.leads[lid]["status"], "qualified")

    def test_convert_requires_qualified_lead_and_permission(self):
        lid = self.add()
        with self.assertRaises(ValueError):
            self.crm.convert(lid, 100, "r1")
        self.crm.qualify(lid, "r1")
        with self.assertRaises(PermissionError):
            self.crm.convert(lid, 100, "r2")
        self.assertEqual(self.crm.opps, {})

    def test_convert_requires_owner(self):
        crm = CRM([
            {"id": "m1", "role": "manager", "capacity": 5},
            {"id": "r0", "role": "rep", "capacity": 0},
        ])
        lid = crm.add_lead("a@corp.com", "A", "referral", "m1")
        self.assertIsNone(crm.leads[lid]["owner"])
        crm.qualify(lid, "m1")
        with self.assertRaises(ValueError):
            crm.convert(lid, 100, "m1")
        self.assertEqual(crm.opps, {})
        self.assertEqual(crm.leads[lid]["status"], "qualified")
        self.assertEqual(len(crm.log), 2)

    def test_failed_calls_append_nothing(self):
        lid = self.add()
        before = (copy.deepcopy(self.crm.leads), copy.deepcopy(self.crm.opps),
                  list(self.crm.log))
        failures = [
            lambda: self.crm.qualify(lid, "r2"),
            lambda: self.crm.convert(lid, 0, "r1"),
            lambda: self.crm.convert(lid, 10, "r1"),
            lambda: self.crm.advance("O9", "proposal", "r1"),
        ]
        for call in failures:
            with self.assertRaises((ValueError, PermissionError)):
                call()
        self.assertEqual(self.crm.leads, before[0])
        self.assertEqual(self.crm.opps, before[1])
        self.assertEqual(self.crm.log, before[2])


if __name__ == "__main__":
    unittest.main()
