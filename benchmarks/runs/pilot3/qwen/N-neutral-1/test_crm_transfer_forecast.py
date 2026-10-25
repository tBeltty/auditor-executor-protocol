"""Tests for transfer and forecast."""

import unittest

from crm import CRM


def load_of(crm, rep_id):
    """The spec's definition of load, recomputed from the public dicts."""
    count = 0
    for lead in crm.leads.values():
        if lead["owner"] == rep_id and lead["status"] in ("new", "qualified"):
            count += 1
    for opp in crm.opps.values():
        if opp["owner"] == rep_id and opp["stage"] not in ("won", "lost"):
            count += 1
    return count



def crm_two_reps(amount=1000):
    crm = CRM([
        {"id": "r1", "role": "rep", "capacity": 2},
        {"id": "r2", "role": "rep", "capacity": 2},
        {"id": "m1", "role": "manager", "capacity": 2},
    ])
    crm.add_lead("a@acme.com", "A", "referral", "m1")
    crm.qualify("L1", "r1")
    crm.convert("L1", amount, "r1")
    return crm


class TestTransfer(unittest.TestCase):
    def test_manager_transfers(self):
        crm = crm_two_reps()
        crm.transfer("O1", "r2", "m1")
        self.assertEqual(crm.opps["O1"]["owner"], "r2")
        self.assertEqual(crm.opps["O1"]["amount"], 1000)
        self.assertEqual(crm.opps["O1"]["stage"], "prospect")
        self.assertEqual(crm.log[-1], ("transfer", "O1", "m1"))

    def test_only_managers_may_transfer(self):
        crm = crm_two_reps()
        with self.assertRaises(PermissionError):
            crm.transfer("O1", "r2", "r1")
        with self.assertRaises(PermissionError):
            crm.transfer("O1", "r2", "r2")
        self.assertEqual(crm.opps["O1"]["owner"], "r1")
        self.assertEqual(len(crm.log), 3)

    def test_new_owner_must_be_rep(self):
        crm = crm_two_reps()
        with self.assertRaises(ValueError):
            crm.transfer("O1", "m1", "m1")
        with self.assertRaises(ValueError):
            crm.transfer("O1", "ghost", "m1")
        with self.assertRaises(ValueError):
            crm.transfer("O1", None, "m1")
        with self.assertRaises(ValueError):
            crm.transfer("O1", 17, "m1")
        self.assertEqual(crm.opps["O1"]["owner"], "r1")

    def test_final_stage_rejected(self):
        crm = crm_two_reps()
        crm.advance("O1", "lost", "m1")
        with self.assertRaises(ValueError):
            crm.transfer("O1", "r2", "m1")
        self.assertEqual(crm.opps["O1"]["owner"], "r1")

    def test_same_owner_rejected(self):
        crm = crm_two_reps()
        with self.assertRaises(ValueError):
            crm.transfer("O1", "r1", "m1")
        self.assertEqual(len(crm.log), 3)

    def test_capacity_blocks_transfer(self):
        crm = crm_two_reps()
        # r1 already carries O1 (load 1); route leads until r2 is full (cap 2)
        self.assertEqual(crm.add_lead("b@acme.com", "B", "web", "m1"), "L2")
        self.assertEqual(crm.add_lead("c@acme.com", "C", "web", "m1"), "L3")
        self.assertEqual(crm.add_lead("d@acme.com", "D", "web", "m1"), "L4")
        self.assertEqual(load_of(crm, "r2"), 2)
        with self.assertRaises(ValueError):
            crm.transfer("O1", "r2", "m1")
        self.assertEqual(crm.opps["O1"]["owner"], "r1")
        self.assertEqual(load_of(crm, "r1"), 2)  # O1 + one new lead

    def test_unknown_opp_first(self):
        crm = crm_two_reps()
        with self.assertRaises(ValueError):
            crm.transfer("O5", "r2", "m1")

    def test_existence_before_permission(self):
        crm = crm_two_reps()
        with self.assertRaises(ValueError):
            crm.transfer("O5", "r2", "r1")

    def test_manager_check_before_new_owner_check(self):
        crm = crm_two_reps()
        with self.assertRaises(PermissionError):  # rule 2 before rule 3
            crm.transfer("O1", "m1", "r1")

    def test_new_work_follows_transferred_opp(self):
        crm = crm_two_reps()
        crm.transfer("O1", "r2", "m1")
        crm.add_lead("b@acme.com", "B", "web", "m1")
        # r1 now has load 0, r2 has load 1 -> the new lead goes to r1
        self.assertEqual(crm.leads["L2"]["owner"], "r1")

    def test_transfer_to_full_rep_is_rejected(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 2},
            {"id": "m1", "role": "manager", "capacity": 5},
        ])
        crm.add_lead("a@acme.com", "A", "referral", "m1")   # -> r1
        crm.add_lead("b@acme.com", "B", "web", "m1")        # -> r2
        crm.add_lead("c@acme.com", "C", "web", "m1")        # -> r2 (now full)
        self.assertEqual([crm.leads[i]["owner"] for i in ["L1", "L2", "L3"]],
                         ["r1", "r2", "r2"])
        crm.qualify("L1", "m1")
        crm.convert("L1", 1000, "m1")
        self.assertEqual(load_of(crm, "r1"), 1)
        self.assertEqual(load_of(crm, "r2"), 2)
        before = list(crm.log)
        with self.assertRaises(ValueError):
            crm.transfer("O1", "r2", "m1")
        self.assertEqual(crm.opps["O1"]["owner"], "r1")
        self.assertEqual(crm.log, before)

    def test_transfer_target_must_have_room_then_owns(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 2},
            {"id": "m1", "role": "manager", "capacity": 5},
        ])
        crm.add_lead("a@acme.com", "A", "referral", "m1")   # -> r1
        crm.add_lead("b@acme.com", "B", "web", "m1")        # -> r2
        crm.qualify("L1", "m1")
        crm.convert("L1", 1000, "m1")
        crm.transfer("O1", "r2", "m1")
        self.assertEqual(crm.opps["O1"]["owner"], "r2")
        self.assertEqual(load_of(crm, "r1"), 0)
        self.assertEqual(load_of(crm, "r2"), 2)
        self.assertEqual(crm.log[-1], ("transfer", "O1", "m1"))
        # no reassignment happens because the waiting queue was empty
        self.assertNotIn("assign", [entry[0] for entry in crm.log])

    def test_transfer_does_not_assign_and_frees_the_old_owner(self):
        # transfer() must free the previous owner's slot like advance() does.
        # That loop can never observe a non-empty queue: add_lead queues a
        # lead only when every rep is full, and rule 6 requires the target to
        # have room, so a legal transfer implies an empty queue.
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 2},
            {"id": "m1", "role": "manager", "capacity": 2},
        ])
        crm.add_lead("a@acme.com", "A", "referral", "m1")  # -> r1 (full)
        crm.add_lead("b@acme.com", "B", "web", "m1")       # -> r2
        self.assertEqual([crm.leads["L1"]["owner"], crm.leads["L2"]["owner"]],
                         ["r1", "r2"])
        crm.qualify("L1", "m1")
        crm.convert("L1", 1000, "m1")
        crm.transfer("O1", "r2", "m1")
        self.assertEqual(crm.opps["O1"]["owner"], "r2")
        self.assertEqual(load_of(crm, "r1"), 0)
        self.assertEqual(load_of(crm, "r2"), 2)
        self.assertNotIn("assign", [entry[0] for entry in crm.log])
        # the previous owner's slot is available to the next lead
        self.assertEqual(crm.add_lead("c@acme.com", "C", "web", "m1"), "L3")
        self.assertEqual(crm.leads["L3"]["owner"], "r1")

    def test_failed_transfer_changes_nothing(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 2},
            {"id": "m1", "role": "manager", "capacity": 5},
        ])
        crm.add_lead("a@acme.com", "A", "referral", "m1")
        crm.add_lead("b@acme.com", "B", "web", "m1")
        crm.qualify("L1", "m1")
        crm.convert("L1", 1000, "m1")
        before_log = list(crm.log)
        before_opp = dict(crm.opps["O1"])
        with self.assertRaises(ValueError):
            crm.transfer("O1", "r1", "m1")  # already owned by r1
        self.assertEqual(crm.log, before_log)
        self.assertEqual(crm.opps["O1"], before_opp)
        with self.assertRaises(ValueError):
            crm.transfer("O1", "ghost", "m1")
        self.assertEqual(crm.log, before_log)
        self.assertEqual(crm.opps["O1"], before_opp)


class TestForecast(unittest.TestCase):
    def build(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 20},
            {"id": "m1", "role": "manager", "capacity": 20},
        ])
        self.crm = crm

    def setUp(self):
        self.build()

    def make_opp(self, amount, stage_path):
        n = len(self.crm.leads) + 1
        lid = self.crm.add_lead("u%d@acme.com" % n, "N", "referral", "m1")
        self.crm.qualify(lid, "m1")
        opp = self.crm.convert(lid, amount, "m1")
        for stage in stage_path:
            self.crm.advance(opp, stage, "m1")
        return opp

    def test_empty(self):
        self.assertEqual(self.crm.forecast(),
                         {"open": 0, "weighted": 0, "won": 0})

    def test_weights_by_stage(self):
        self.make_opp(1000, [])               # prospect
        self.make_opp(1000, ["proposal"])     # proposal
        self.make_opp(1000, ["proposal", "negotiation"])
        self.assertEqual(self.crm.forecast(),
                         {"open": 3, "weighted": 100 + 300 + 600, "won": 0})

    def test_won_uses_discounted_amount(self):
        opp = self.make_opp(10000, ["proposal"])
        self.crm.discount(opp, 10, "m1")  # 10000 -> 9000
        self.crm.advance(opp, "negotiation", "m1")
        self.crm.advance(opp, "won", "m1")
        forecast = self.crm.forecast()
        self.assertEqual(forecast["won"], 9000)  # amount, not original_amount
        self.assertEqual(forecast["open"], 0)
        self.assertEqual(forecast["weighted"], 0)

    def test_won_sums_amount(self):
        self.make_opp(2000, ["proposal", "negotiation", "won"])
        self.assertEqual(self.crm.forecast(), {"open": 0, "weighted": 0, "won": 2000})

    def test_lost_excluded_everywhere(self):
        self.make_opp(2000, ["lost"])
        self.assertEqual(self.crm.forecast(), {"open": 0, "weighted": 0, "won": 0})

    def test_discount_lowers_weighting(self):
        opp = self.make_opp(10000, ["proposal"])
        self.crm.discount(opp, 10, "m1")  # 9000
        self.assertEqual(self.crm.forecast()["weighted"], 2700)
        self.assertEqual(self.crm.forecast()["open"], 1)

    def test_mixed_book(self):
        self.make_opp(1000, ["proposal"])
        self.make_opp(5000, ["proposal", "negotiation", "won"])
        self.make_opp(3000, ["proposal", "negotiation"])
        self.make_opp(9000, ["lost"])
        self.assertEqual(self.crm.forecast(),
                         {"open": 2, "weighted": 300 + 1800, "won": 5000})

    def test_integer_floor(self):
        self.make_opp(999, [])          # prospect: 999*10//100 == 99
        self.assertEqual(self.crm.forecast()["weighted"], 99)
        self.make_opp(999, ["proposal"])  # proposal: 999*30//100 == 299
        self.assertEqual(self.crm.forecast()["weighted"], 99 + 299)

    def test_forecast_has_no_actor_and_no_log(self):
        self.make_opp(1000, [])
        before = list(self.crm.log)
        self.crm.forecast()
        self.assertEqual(self.crm.log, before)

    def test_forecast_returns_fresh_dict(self):
        self.make_opp(1000, [])
        first = self.crm.forecast()
        first["open"] = 999
        self.assertEqual(self.crm.forecast()["open"], 1)


if __name__ == "__main__":
    unittest.main()
