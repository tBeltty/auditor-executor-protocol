"""Contract tests: data shapes, id counters, hostile arguments, end-to-end flow."""

import copy
import unittest

from crm import CRM, DuplicateLeadError

TEAM = [
    {"id": "r1", "role": "rep", "capacity": 1},
    {"id": "r2", "role": "rep", "capacity": 1},
    {"id": "m1", "role": "manager", "capacity": 0},
]


def build(reps=None):
    return CRM(copy.deepcopy(reps if reps is not None else TEAM))


class ShapeTest(unittest.TestCase):
    def test_lead_and_opportunity_keys(self):
        crm = build()
        lead = crm.add_lead("a@acme.com", "Ann", "referral", "m1")
        crm.qualify(lead, "m1")
        opp = crm.convert(lead, 1000, "m1")
        self.assertEqual(
            set(crm.leads[lead]), {"id", "email", "name", "source", "score", "owner", "status"}
        )
        self.assertEqual(
            set(crm.opps[opp]),
            {"id", "lead_id", "owner", "amount", "original_amount", "stage"},
        )
        self.assertEqual(crm.leads[lead]["id"], lead)
        self.assertEqual(crm.opps[opp]["lead_id"], lead)

    def test_top_level_attributes(self):
        crm = build()
        self.assertIsInstance(crm.leads, dict)
        self.assertIsInstance(crm.opps, dict)
        self.assertIsInstance(crm.log, list)
        self.assertEqual(crm.leads, {})
        self.assertEqual(crm.opps, {})
        self.assertEqual(crm.log, [])

    def test_leads_keyed_by_id(self):
        crm = build()
        ids = [crm.add_lead("u%d@acme.com" % i, "N", "web", "m1") for i in range(1, 4)]
        self.assertEqual(sorted(crm.leads), sorted(ids))
        for lead_id in ids:
            self.assertEqual(crm.leads[lead_id]["id"], lead_id)

    def test_id_counters_are_independent(self):
        crm = build([{"id": "r1", "role": "rep", "capacity": 9},
                     {"id": "m1", "role": "manager", "capacity": 9}])
        for i in range(1, 4):
            lead = crm.add_lead("u%d@acme.com" % i, "N", "referral", "m1")
            self.assertEqual(lead, "L%d" % i)
            crm.qualify(lead, "m1")
            self.assertEqual(crm.convert(lead, 100, "m1"), "O%d" % i)
        # A lead added after conversions still continues the lead counter.
        self.assertEqual(crm.add_lead("u9@acme.com", "N", "web", "m1"), "L4")
        # Failed conversions do not burn an opportunity number.
        with self.assertRaises(ValueError):
            crm.convert("O1", 100, "m1")  # already converted
        self.assertEqual(sorted(crm.opps), ["O1", "O2", "O3"])


class HostileArgumentTest(unittest.TestCase):
    def test_odd_types_raise_the_documented_errors(self):
        crm = build()
        lead = crm.add_lead("a@acme.com", "Ann", "web", "m1")
        opp_cases = [
            (lambda: crm.qualify(["L1"], "m1"), ValueError),
            (lambda: crm.advance({"O1": 1}, "proposal", "m1"), ValueError),
            (lambda: crm.transfer(("O1",), "r2", "m1"), ValueError),
            (lambda: crm.discount(["O1"], 5, "m1"), ValueError),
            (lambda: crm.add_lead("z@z.com", "Z", "web", ["m1"]), PermissionError),
            (lambda: crm.qualify(lead, {"m1": 1}), PermissionError),
        ]
        for call, expected in opp_cases:
            with self.assertRaises(expected):
                call()

    def test_none_ids_are_unknown_entities(self):
        crm = build()
        with self.assertRaises(ValueError):
            crm.qualify(None, "m1")
        with self.assertRaises(ValueError):
            crm.advance(None, "proposal", "m1")

    def test_empty_crm_has_no_valid_actor(self):
        crm = CRM([])
        with self.assertRaises(PermissionError):
            crm.add_lead("a@b.com", "A", "web", "r1")
        self.assertEqual(crm.forecast(), {"open": 0, "weighted": 0, "won": 0})
        self.assertEqual(crm.log, [])

    def test_duplicate_error_is_raised_not_returned(self):
        crm = build()
        crm.add_lead("a@acme.com", "Ann", "web", "m1")
        try:
            crm.add_lead("a@acme.com", "Ann", "web", "m1")
        except DuplicateLeadError as error:
            self.assertEqual(error.existing_id, "L1")
        else:
            self.fail("DuplicateLeadError was not raised")

    def test_duplicate_error_cannot_be_caught_as_value_error(self):
        # The spec distinguishes the two: a duplicate is not a validation problem.
        crm = build()
        crm.add_lead("a@acme.com", "Ann", "web", "m1")
        with self.assertRaises(DuplicateLeadError):
            try:
                crm.add_lead("a@acme.com", "Ann", "web", "m1")
            except ValueError:  # pragma: no cover - only if the class hierarchy changed
                self.fail("DuplicateLeadError should not be a ValueError")


class EndToEndTest(unittest.TestCase):
    def test_full_lifecycle(self):
        crm = build()
        # 1. Intake: two reps fill up, a third lead waits.
        a = crm.add_lead("  Alice@ACME.com ", "  Alice  ", "event", "m1")
        b = crm.add_lead("bob@acme.com", "Bob", "referral", "m1")
        c = crm.add_lead("carol@gmail.com", "Carol", "referral", "m1")
        self.assertEqual((crm.leads[a]["owner"], crm.leads[b]["owner"]), ("r1", "r2"))
        self.assertIsNone(crm.leads[c]["owner"])
        self.assertEqual(crm.leads[a]["score"], 35)
        self.assertEqual(crm.leads[c]["score"], 30)

        # 2. Qualification and conversion of Alice's lead.
        crm.qualify(a, "r1")
        opp = crm.convert(a, 60000, "r1")
        self.assertEqual(crm.opps[opp]["owner"], "r1")
        self.assertIsNone(crm.leads[c]["owner"])  # conversion is load neutral

        # 3. A big deal needs a manager to reach negotiation.
        crm.advance(opp, "proposal", "r1")
        with self.assertRaises(PermissionError):
            crm.advance(opp, "negotiation", "r1")
        with self.assertRaises(ValueError):
            crm.discount(opp, 0, "m1")

        # 4. A discount brings it within the rep's authority.
        crm.discount(opp, 30, "m1")
        self.assertEqual(crm.opps[opp]["amount"], 42000)
        crm.advance(opp, "negotiation", "r1")
        self.assertEqual(crm.forecast(), {"open": 1, "weighted": 25200, "won": 0})

        # 5. Winning frees r1's slot, which pulls Carol out of the queue.
        crm.advance(opp, "won", "r1")
        self.assertEqual(crm.leads[c]["owner"], "r1")
        self.assertEqual(
            crm.log,
            [
                ("add_lead", "L1", "m1"),
                ("add_lead", "L2", "m1"),
                ("add_lead", "L3", "m1"),
                ("qualify", "L1", "r1"),
                ("convert", "O1", "r1"),
                ("advance", "O1", "r1"),
                ("discount", "O1", "m1"),
                ("advance", "O1", "r1"),
                ("advance", "O1", "r1"),
                ("assign", "L3", "system"),
            ],
        )
        self.assertEqual(crm.forecast(), {"open": 0, "weighted": 0, "won": 42000})

        # 6. Bob's deal is handed to nobody else while r1 is busy again.
        crm.qualify(b, "m1")
        opp2 = crm.convert(b, 500, "m1")
        with self.assertRaises(ValueError):
            crm.transfer(opp2, "r1", "m1")  # r1 holds Carol
        crm.advance(opp2, "proposal", "m1")
        crm.advance(opp2, "lost", "m1")
        self.assertEqual(crm.forecast(), {"open": 0, "weighted": 0, "won": 42000})


if __name__ == "__main__":
    unittest.main()
