import unittest

from crm import CRM, DuplicateLeadError


def make_crm():
    return CRM(
        [
            {"id": "r1", "role": "rep", "capacity": 2},
            {"id": "r2", "role": "rep", "capacity": 2},
            {"id": "m1", "role": "manager", "capacity": 0},
        ]
    )


def make_tight_crm():
    return CRM(
        [
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 0},
        ]
    )


class AddLeadTests(unittest.TestCase):
    def test_normalizes_and_scores(self):
        crm = make_crm()
        lead_id = crm.add_lead("  Alice@Example.COM ", " Alice ", "web", "r1")
        self.assertEqual(lead_id, "L1")
        lead = crm.leads[lead_id]
        self.assertEqual(lead["email"], "alice@example.com")
        self.assertEqual(lead["name"], "Alice")
        self.assertEqual(lead["score"], 25)  # web 10 + 15 non-free domain
        self.assertEqual(lead["owner"], "r1")
        self.assertEqual(lead["status"], "new")
        self.assertEqual(crm.log, [("add_lead", "L1", "r1")])

    def test_free_domain_scores(self):
        crm = make_crm()
        referral = crm.add_lead("a@gmail.com", "A", "referral", "m1")
        event = crm.add_lead("b@yahoo.com", "B", "event", "m1")
        self.assertEqual(crm.leads[referral]["score"], 30)
        self.assertEqual(crm.leads[event]["score"], 20)

    def test_unknown_actor_checked_first(self):
        crm = make_crm()
        with self.assertRaises(PermissionError):
            crm.add_lead("not-an-email", "", "bogus", "nobody")
        self.assertEqual(crm.leads, {})
        self.assertEqual(crm.log, [])

    def test_email_validation(self):
        bad = [
            None,
            5,
            "plain",
            "a@b@c.com",
            "@example.com",
            "a@example",
            "a@.com",
            "a@example.",
        ]
        for email in bad:
            crm = make_crm()
            with self.assertRaises(ValueError, msg=repr(email)):
                crm.add_lead(email, "Name", "web", "r1")

    def test_name_and_source_validation(self):
        with self.assertRaises(ValueError):
            make_crm().add_lead("a@example.com", "   ", "web", "r1")
        with self.assertRaises(ValueError):
            make_crm().add_lead("a@example.com", 7, "web", "r1")
        with self.assertRaises(ValueError):
            make_crm().add_lead("a@example.com", "A", "ads", "r1")

    def test_duplicate_detection_on_normalized_email(self):
        crm = make_crm()
        first = crm.add_lead("a@example.com", "A", "web", "r1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            crm.add_lead("  A@Example.com ", "Other", "event", "r1")
        self.assertEqual(ctx.exception.existing_id, first)
        self.assertEqual(len(crm.leads), 1)
        self.assertEqual(len(crm.log), 1)

    def test_lowest_load_and_tie_break(self):
        crm = make_crm()
        crm.add_lead("a@example.com", "A", "web", "m1")
        self.assertEqual(crm.leads["L1"]["owner"], "r1")
        crm.add_lead("b@example.com", "B", "web", "m1")
        self.assertEqual(crm.leads["L2"]["owner"], "r2")
        crm.add_lead("c@example.com", "C", "web", "m1")
        self.assertEqual(crm.leads["L3"]["owner"], "r1")

    def test_capacity_and_waiting_queue(self):
        crm = make_tight_crm()
        crm.add_lead("a@example.com", "A", "web", "m1")
        crm.add_lead("b@example.com", "B", "web", "m1")
        crm.add_lead("c@example.com", "C", "web", "m1")
        self.assertEqual(crm.leads["L1"]["owner"], "r1")
        self.assertEqual(crm.leads["L2"]["owner"], "r2")
        self.assertIsNone(crm.leads["L3"]["owner"])
        self.assertEqual(list(crm.waiting), ["L3"])
        self.assertEqual(crm._load("r1"), 1)
        self.assertEqual(crm._load("r2"), 1)


class QualifyTests(unittest.TestCase):
    def test_success(self):
        crm = make_crm()
        lead_id = crm.add_lead("a@example.com", "A", "referral", "r1")
        crm.qualify(lead_id, "r1")
        self.assertEqual(crm.leads[lead_id]["status"], "qualified")
        self.assertEqual(crm.log[-1], ("qualify", lead_id, "r1"))

    def test_manager_may_qualify_someone_elses_lead(self):
        crm = make_crm()
        lead_id = crm.add_lead("a@example.com", "A", "referral", "r1")
        crm.qualify(lead_id, "m1")
        self.assertEqual(crm.leads[lead_id]["status"], "qualified")

    def test_failures_change_nothing(self):
        crm = make_crm()
        lead_id = crm.add_lead("a@example.com", "A", "web", "r1")  # score 25
        with self.assertRaises(ValueError):  # unknown lead
            crm.qualify("L999", "r1")
        with self.assertRaises(PermissionError):  # not owner, not manager
            crm.qualify(lead_id, "r2")
        with self.assertRaises(ValueError):  # score too low
            crm.qualify(lead_id, "r1")
        self.assertEqual(crm.leads[lead_id]["status"], "new")
        self.assertEqual(len(crm.log), 1)

    def test_status_must_be_new(self):
        crm = make_crm()
        lead_id = crm.add_lead("a@example.com", "A", "referral", "r1")
        crm.qualify(lead_id, "r1")
        with self.assertRaises(ValueError):
            crm.qualify(lead_id, "r1")


class ConvertTests(unittest.TestCase):
    def _qualified(self):
        crm = make_crm()
        lead_id = crm.add_lead("a@example.com", "A", "referral", "r1")
        crm.qualify(lead_id, "r1")
        return crm, lead_id

    def test_success(self):
        crm, lead_id = self._qualified()
        opp_id = crm.convert(lead_id, 1000, "r1")
        self.assertEqual(opp_id, "O1")
        opp = crm.opps[opp_id]
        self.assertEqual(
            opp,
            {
                "id": "O1",
                "lead_id": lead_id,
                "owner": "r1",
                "amount": 1000,
                "original_amount": 1000,
                "stage": "prospect",
            },
        )
        self.assertEqual(crm.leads[lead_id]["status"], "converted")
        self.assertEqual(crm.log[-1], ("convert", "O1", "r1"))

    def test_amount_validation(self):
        crm, lead_id = self._qualified()
        for bad in (0, -5, True, 10.0, "10"):
            with self.assertRaises(ValueError):
                crm.convert(lead_id, bad, "r1")
        self.assertEqual(crm.opps, {})

    def test_requires_qualified_and_owner(self):
        crm = make_crm()
        new_lead = crm.add_lead("a@example.com", "A", "referral", "r1")
        with self.assertRaises(ValueError):
            crm.convert(new_lead, 100, "r1")

        tight = make_tight_crm()
        tight.add_lead("x@example.com", "X", "web", "m1")
        tight.add_lead("y@example.com", "Y", "web", "m1")
        waiting = tight.add_lead("z@example.com", "Z", "referral", "m1")
        tight.qualify(waiting, "m1")
        with self.assertRaises(ValueError):
            tight.convert(waiting, 100, "m1")

    def test_permission(self):
        crm, lead_id = self._qualified()
        with self.assertRaises(PermissionError):
            crm.convert(lead_id, 100, "r2")
        self.assertEqual(crm.leads[lead_id]["status"], "qualified")


class AdvanceTests(unittest.TestCase):
    def _opp(self, amount=1000):
        crm = make_crm()
        lead_id = crm.add_lead("a@example.com", "A", "referral", "r1")
        crm.qualify(lead_id, "r1")
        opp_id = crm.convert(lead_id, amount, "r1")
        return crm, opp_id

    def test_step_through_to_won(self):
        crm, opp_id = self._opp()
        crm.advance(opp_id, "proposal", "r1")
        crm.advance(opp_id, "negotiation", "r1")
        crm.advance(opp_id, "won", "r1")
        self.assertEqual(crm.opps[opp_id]["stage"], "won")
        self.assertEqual(crm.log[-1], ("advance", opp_id, "r1"))

    def test_lost_from_any_open_stage(self):
        crm, opp_id = self._opp()
        crm.advance(opp_id, "lost", "r1")
        self.assertEqual(crm.opps[opp_id]["stage"], "lost")
        with self.assertRaises(ValueError):
            crm.advance(opp_id, "proposal", "r1")

    def test_transition_validation(self):
        crm, opp_id = self._opp()
        with self.assertRaises(ValueError):
            crm.advance(opp_id, "won", "r1")
        with self.assertRaises(ValueError):
            crm.advance(opp_id, "bogus", "r1")
        with self.assertRaises(ValueError):
            crm.advance("O999", "proposal", "r1")
        self.assertEqual(crm.opps[opp_id]["stage"], "prospect")

    def test_permission(self):
        crm, opp_id = self._opp()
        with self.assertRaises(PermissionError):
            crm.advance(opp_id, "proposal", "r2")
        crm.advance(opp_id, "proposal", "m1")
        self.assertEqual(crm.opps[opp_id]["stage"], "proposal")

    def test_large_negotiation_requires_manager(self):
        crm, opp_id = self._opp(amount=50001)
        crm.advance(opp_id, "proposal", "r1")
        with self.assertRaises(PermissionError):
            crm.advance(opp_id, "negotiation", "r1")
        self.assertEqual(crm.opps[opp_id]["stage"], "proposal")
        crm.advance(opp_id, "negotiation", "m1")
        self.assertEqual(crm.opps[opp_id]["stage"], "negotiation")

    def test_50000_is_not_large(self):
        crm, opp_id = self._opp(amount=50000)
        crm.advance(opp_id, "proposal", "r1")
        crm.advance(opp_id, "negotiation", "r1")
        self.assertEqual(crm.opps[opp_id]["stage"], "negotiation")

    def test_win_frees_slot_and_assigns_oldest_waiting_lead(self):
        crm = make_tight_crm()
        crm.add_lead("a@example.com", "A", "referral", "m1")  # r1
        crm.add_lead("b@example.com", "B", "web", "m1")  # r2
        crm.add_lead("c@example.com", "C", "web", "m1")  # waiting
        crm.qualify("L1", "r1")
        opp_id = crm.convert("L1", 1000, "r1")
        crm.advance(opp_id, "proposal", "r1")
        crm.advance(opp_id, "negotiation", "r1")
        crm.advance(opp_id, "won", "r1")
        self.assertEqual(crm.leads["L3"]["owner"], "r1")
        self.assertEqual(list(crm.waiting), [])
        self.assertEqual(crm.log[-2:], [("advance", opp_id, "r1"), ("assign", "L3", "system")])


class DiscountTests(unittest.TestCase):
    def _opp(self, amount=1000):
        crm = make_crm()
        lead_id = crm.add_lead("a@example.com", "A", "referral", "r1")
        crm.qualify(lead_id, "r1")
        return crm, crm.convert(lead_id, amount, "r1")

    def test_rep_can_discount_ten(self):
        crm, opp_id = self._opp()
        crm.discount(opp_id, 10, "r1")
        self.assertEqual(crm.opps[opp_id]["amount"], 900)
        self.assertEqual(crm.opps[opp_id]["original_amount"], 1000)
        self.assertEqual(crm.log[-1], ("discount", opp_id, "r1"))

    def test_rep_limited_to_ten(self):
        crm, opp_id = self._opp()
        with self.assertRaises(PermissionError):
            crm.discount(opp_id, 11, "r1")
        self.assertEqual(crm.opps[opp_id]["amount"], 1000)

    def test_manager_can_reach_thirty_percent_cumulative(self):
        crm, opp_id = self._opp()
        crm.discount(opp_id, 30, "m1")
        self.assertEqual(crm.opps[opp_id]["amount"], 700)
        with self.assertRaises(ValueError):
            crm.discount(opp_id, 1, "m1")
        self.assertEqual(crm.opps[opp_id]["amount"], 700)

    def test_validation(self):
        crm, opp_id = self._opp()
        for bad in (0, 31, -1, True, 5.0, "5"):
            with self.assertRaises(ValueError):
                crm.discount(opp_id, bad, "r1")
        with self.assertRaises(PermissionError):
            crm.discount(opp_id, 5, "r2")
        crm.advance(opp_id, "lost", "r1")
        with self.assertRaises(ValueError):
            crm.discount(opp_id, 5, "m1")


class TransferTests(unittest.TestCase):
    def _opp(self):
        crm = make_crm()
        lead_id = crm.add_lead("a@example.com", "A", "referral", "r1")
        crm.qualify(lead_id, "r1")
        return crm, crm.convert(lead_id, 1000, "r1")

    def test_manager_transfers(self):
        crm, opp_id = self._opp()
        crm.transfer(opp_id, "r2", "m1")
        self.assertEqual(crm.opps[opp_id]["owner"], "r2")
        self.assertEqual(crm.log[-1], ("transfer", opp_id, "m1"))

    def test_validation_rules(self):
        crm, opp_id = self._opp()
        with self.assertRaises(PermissionError):
            crm.transfer(opp_id, "r2", "r1")
        with self.assertRaises(ValueError):
            crm.transfer(opp_id, "m1", "m1")
        with self.assertRaises(ValueError):
            crm.transfer(opp_id, "nobody", "m1")
        with self.assertRaises(ValueError):
            crm.transfer(opp_id, "r1", "m1")
        self.assertEqual(crm.opps[opp_id]["owner"], "r1")

    def test_capacity_checked(self):
        crm = make_tight_crm()
        crm.add_lead("a@example.com", "A", "referral", "m1")  # r1
        crm.add_lead("b@example.com", "B", "referral", "m1")  # r2
        crm.qualify("L1", "r1")
        crm.qualify("L2", "r2")
        self.assertEqual(crm._load("r2"), 1)
        opp_id = crm.convert("L1", 1000, "r1")
        with self.assertRaises(ValueError):
            crm.transfer(opp_id, "r2", "m1")

    def test_final_opp_cannot_transfer(self):
        crm, opp_id = self._opp()
        crm.advance(opp_id, "lost", "r1")
        with self.assertRaises(ValueError):
            crm.transfer(opp_id, "r2", "m1")

    def test_transfer_keeps_queue_intact_when_nobody_has_room(self):
        crm = make_tight_crm()
        crm.add_lead("a@example.com", "A", "referral", "m1")  # r1
        crm.add_lead("b@example.com", "B", "web", "m1")  # r2
        crm.add_lead("c@example.com", "C", "web", "m1")  # waiting
        crm.qualify("L1", "r1")
        opp_id = crm.convert("L1", 1000, "r1")
        with self.assertRaises(ValueError):  # r2 is already at capacity
            crm.transfer(opp_id, "r2", "m1")
        self.assertEqual(list(crm.waiting), ["L3"])
        self.assertEqual(crm.log[-1], ("convert", opp_id, "r1"))


class ForecastTests(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(make_crm().forecast(), {"open": 0, "weighted": 0, "won": 0})

    def test_weighted_and_won(self):
        crm = make_crm()
        a = crm.add_lead("a@example.com", "A", "referral", "r1")
        b = crm.add_lead("b@example.com", "B", "referral", "r2")
        c = crm.add_lead("c@example.com", "C", "referral", "r1")
        crm.qualify(a, "r1")
        crm.qualify(b, "r2")
        crm.qualify(c, "r1")
        o1 = crm.convert(a, 1000, "r1")
        o2 = crm.convert(b, 500, "r2")
        o3 = crm.convert(c, 999, "r1")
        crm.advance(o1, "proposal", "r1")
        crm.advance(o2, "proposal", "r2")
        crm.advance(o2, "negotiation", "r2")
        crm.advance(o2, "won", "r2")
        crm.advance(o3, "proposal", "r1")
        crm.advance(o3, "negotiation", "r1")
        # open: o1 proposal 1000*30//100=300, o3 negotiation 999*60//100=599
        self.assertEqual(crm.forecast(), {"open": 2, "weighted": 899, "won": 500})


class SequenceAndQueueTests(unittest.TestCase):
    def test_failed_add_does_not_consume_lead_number(self):
        crm = make_crm()
        with self.assertRaises(ValueError):
            crm.add_lead("bad", "A", "web", "r1")
        self.assertEqual(crm.add_lead("a@example.com", "A", "web", "r1"), "L1")
        with self.assertRaises(DuplicateLeadError):
            crm.add_lead("a@example.com", "A", "web", "r1")
        self.assertEqual(crm.add_lead("b@example.com", "B", "web", "r1"), "L2")

    def test_failed_convert_does_not_consume_opp_number(self):
        crm = make_crm()
        lead_id = crm.add_lead("a@example.com", "A", "referral", "r1")
        with self.assertRaises(ValueError):  # not qualified yet
            crm.convert(lead_id, 100, "r1")
        crm.qualify(lead_id, "r1")
        self.assertEqual(crm.convert(lead_id, 100, "r1"), "O1")

    def test_waiting_leads_assigned_in_fifo_order_as_slots_free(self):
        crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 2},
                {"id": "r2", "role": "rep", "capacity": 0},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        for email in ("a@x.com", "b@x.com", "c@x.com", "d@x.com"):
            crm.add_lead(email, email[0], "referral", "m1")
        self.assertIsNone(crm.leads["L3"]["owner"])
        self.assertIsNone(crm.leads["L4"]["owner"])
        crm.qualify("L1", "r1")
        o1 = crm.convert("L1", 100, "r1")
        crm.advance(o1, "lost", "r1")
        self.assertEqual(crm.leads["L3"]["owner"], "r1")
        self.assertEqual(list(crm.waiting), ["L4"])
        crm.qualify("L2", "r1")
        o2 = crm.convert("L2", 100, "r1")
        crm.advance(o2, "lost", "r1")
        self.assertEqual(crm.leads["L4"]["owner"], "r1")
        self.assertEqual(list(crm.waiting), [])
        self.assertEqual(
            crm.log[-2:],
            [("advance", o2, "r1"), ("assign", "L4", "system")],
        )

    def test_managers_never_receive_work(self):
        crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 1},
                {"id": "m1", "role": "manager", "capacity": 5},
            ]
        )
        crm.add_lead("a@x.com", "A", "referral", "m1")
        crm.add_lead("b@x.com", "B", "referral", "m1")
        self.assertEqual(crm.leads["L1"]["owner"], "r1")
        self.assertIsNone(crm.leads["L2"]["owner"])


class ArgumentTypeTests(unittest.TestCase):
    def test_unknown_actor_is_permission_error_for_any_type(self):
        crm = make_crm()
        for actor in (None, 7, [], {}):
            with self.assertRaises(PermissionError, msg=repr(actor)):
                crm.add_lead("a@example.com", "A", "web", actor)
        self.assertEqual(crm.leads, {})
        self.assertEqual(crm.log, [])

    def test_unknown_ids_are_value_errors_for_any_type(self):
        crm = make_crm()
        for key in (None, [], {}):
            with self.assertRaises(ValueError, msg=repr(key)):
                crm.qualify(key, "r1")
            with self.assertRaises(ValueError, msg=repr(key)):
                crm.convert(key, 100, "r1")
            with self.assertRaises(ValueError, msg=repr(key)):
                crm.advance(key, "proposal", "r1")
            with self.assertRaises(ValueError, msg=repr(key)):
                crm.discount(key, 5, "r1")

    def test_bad_source_and_new_owner_types(self):
        crm = make_crm()
        for source in (None, 7, [], "ads"):
            with self.assertRaises(ValueError, msg=repr(source)):
                crm.add_lead("a@example.com", "A", source, "r1")
        lead_id = crm.add_lead("a@example.com", "A", "referral", "r1")
        crm.qualify(lead_id, "r1")
        opp_id = crm.convert(lead_id, 100, "r1")
        for new_owner in (None, 7, [], "nobody", "m1"):
            with self.assertRaises(ValueError, msg=repr(new_owner)):
                crm.transfer(opp_id, new_owner, "m1")


if __name__ == "__main__":
    unittest.main()
