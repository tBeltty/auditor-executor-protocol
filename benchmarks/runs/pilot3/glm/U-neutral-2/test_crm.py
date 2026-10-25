import unittest

from crm import CRM, DuplicateLeadError


def make_users():
    return [
        {"id": "R1", "role": "rep", "capacity": 2},
        {"id": "R2", "role": "rep", "capacity": 1},
        {"id": "M1", "role": "manager", "capacity": 0},
    ]


class AddLeadTests(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(make_users())

    def test_valid_lead(self):
        lead_id = self.crm.add_lead("  Bob@Test.COM ", "  Bob  ", "web", "R1")
        self.assertEqual(lead_id, "L1")
        lead = self.crm.leads["L1"]
        self.assertEqual(lead["email"], "bob@test.com")
        self.assertEqual(lead["name"], "Bob")
        self.assertEqual(lead["source"], "web")
        self.assertEqual(lead["score"], 25)  # 10 + 15 non-default domain
        self.assertEqual(lead["status"], "new")
        self.assertEqual(lead["owner"], "R1")
        self.assertEqual(self.crm.log, [("add_lead", "L1", "R1")])

    def test_unknown_actor_first(self):
        with self.assertRaises(PermissionError):
            self.crm.add_lead("a@b.com", "A", "web", "NOPE")
        self.assertEqual(self.crm.log, [])

    def test_email_must_be_str(self):
        with self.assertRaises(ValueError):
            self.crm.add_lead(123, "A", "web", "R1")

    def test_email_validation(self):
        for email in ["no-at.com", "a@@b.com", "@b.com", "a@", "a@b",
                      "a@.com", "a@com."]:
            with self.assertRaises(ValueError, msg=email):
                self.crm.add_lead(email, "A", "web", "R1")
        self.assertEqual(self.crm.log, [])

    def test_name_and_source_validation(self):
        for name in ["   ", 5, None]:
            with self.assertRaises(ValueError, msg=name):
                self.crm.add_lead("a@b.com", name, "web", "R1")
        for source in ["tv", "", None, "WEB"]:
            with self.assertRaises(ValueError, msg=source):
                self.crm.add_lead("a@b.com", "A", source, "R1")
        self.assertEqual(self.crm.log, [])

    def test_duplicate_lead(self):
        self.crm.add_lead("a@b.com", "A", "web", "R1")
        with self.assertRaises(DuplicateLeadError) as cm:
            self.crm.add_lead(" A@B.COM ", "Other", "referral", "R1")
        self.assertEqual(cm.exception.existing_id, "L1")
        self.assertEqual(len(self.crm.leads), 1)
        self.assertEqual(self.crm.log, [("add_lead", "L1", "R1")])

    def test_scores(self):
        cases = [("a@gmail.com", "web", 10),
                 ("b@acme.com", "web", 25),
                 ("c@gmail.com", "referral", 30),
                 ("d@gmail.com", "event", 20),
                 ("e@acme.com", "event", 35)]
        for email, source, expected in cases:
            lid = self.crm.add_lead(email, "N", source, "M1")
            self.assertEqual(self.crm.leads[lid]["score"], expected, email)

    def test_owner_lowest_load_tiebreak(self):
        crm = CRM([
            {"id": "B", "role": "rep", "capacity": 3},
            {"id": "A", "role": "rep", "capacity": 3},
        ])
        # tie at load 0 -> smallest id in string order
        self.assertEqual(crm.leads[crm.add_lead("a@b.com", "A", "web", "A")]["owner"], "A")
        # A load 1, B load 0 -> B
        self.assertEqual(crm.leads[crm.add_lead("c@b.com", "C", "web", "A")]["owner"], "B")
        # A 1, B 1 -> tie -> A
        self.assertEqual(crm.leads[crm.add_lead("e@b.com", "E", "web", "A")]["owner"], "A")

    def test_waiting_queue_fifo(self):
        ids = [self.crm.add_lead(e, "N%d" % i, "web", "M1")
               for i, e in enumerate(["a@b.com", "c@b.com", "e@b.com",
                                      "g@b.com", "i@b.com"])]
        owners = [self.crm.leads[lid]["owner"] for lid in ids]
        # L1 -> R1 (0<2), L2 -> R2 (0<1 beats R1's 1), L3 -> R1 (1<2, R2 full),
        # then R1=2, R2=1 -> nobody qualifies
        self.assertEqual(owners, ["R1", "R2", "R1", None, None])


class UnknownActorTests(unittest.TestCase):
    def test_unknown_actor_first_in_every_method(self):
        crm = CRM(make_users())
        with self.assertRaises(PermissionError):
            crm.qualify("L1", "X")
        with self.assertRaises(PermissionError):
            crm.convert("L1", 10, "X")
        with self.assertRaises(PermissionError):
            crm.advance("O1", "proposal", "X")
        with self.assertRaises(PermissionError):
            crm.discount("O1", 5, "X")
        with self.assertRaises(PermissionError):
            crm.transfer("O1", "R1", "X")
        self.assertEqual(crm.log, [])


class QualifyTests(unittest.TestCase):
    def setUp(self):
        # R2 has no capacity so both leads land on R1
        self.crm = CRM([
            {"id": "R1", "role": "rep", "capacity": 5},
            {"id": "R2", "role": "rep", "capacity": 0},
            {"id": "M1", "role": "manager", "capacity": 0},
        ])
        self.low = self.crm.add_lead("a@b.com", "A", "web", "R1")       # 25
        self.ok = self.crm.add_lead("c@acme.com", "C", "event", "R1")   # 35
        self.crm.log.clear()

    def test_missing_lead(self):
        with self.assertRaises(ValueError):
            self.crm.qualify("L99", "R1")
        self.assertEqual(self.crm.log, [])

    def test_permission_before_status_and_score(self):
        # R2 is neither owner nor manager; lead is score-25 and "new":
        # PermissionError must win over both ValueErrors.
        with self.assertRaises(PermissionError):
            self.crm.qualify(self.low, "R2")
        self.assertEqual(self.crm.log, [])

    def test_success_by_owner(self):
        self.crm.qualify(self.ok, "R1")
        self.assertEqual(self.crm.leads[self.ok]["status"], "qualified")
        self.assertEqual(self.crm.log, [("qualify", self.ok, "R1")])

    def test_success_by_manager(self):
        self.crm.qualify(self.ok, "M1")
        self.assertEqual(self.crm.log, [("qualify", self.ok, "M1")])

    def test_not_owner(self):
        with self.assertRaises(PermissionError):
            self.crm.qualify(self.ok, "R2")
        self.assertEqual(self.crm.log, [])

    def test_low_score(self):
        with self.assertRaises(ValueError):
            self.crm.qualify(self.low, "R1")
        self.assertEqual(self.crm.leads[self.low]["status"], "new")
        self.assertEqual(self.crm.log, [])

    def test_not_new(self):
        self.crm.qualify(self.ok, "R1")
        self.crm.log.clear()
        with self.assertRaises(ValueError):
            self.crm.qualify(self.ok, "R1")
        self.assertEqual(self.crm.log, [])


class ConvertTests(unittest.TestCase):
    def setUp(self):
        crm = CRM(make_users())
        self.lead = crm.add_lead("a@acme.com", "A", "event", "R1")  # 35
        crm.qualify(self.lead, "R1")
        crm.log.clear()
        self.crm = crm

    def test_success(self):
        opp_id = self.crm.convert(self.lead, 1000, "R1")
        self.assertEqual(opp_id, "O1")
        opp = self.crm.opps["O1"]
        self.assertEqual(opp["lead_id"], self.lead)
        self.assertEqual(opp["owner"], "R1")
        self.assertEqual(opp["amount"], 1000)
        self.assertEqual(opp["original_amount"], 1000)
        self.assertEqual(opp["stage"], "prospect")
        self.assertEqual(self.crm.leads[self.lead]["status"], "converted")
        self.assertEqual(self.crm.log, [("convert", "O1", "R1")])

    def test_amount_validation(self):
        for amount in [0, -5, "x", True, False, 1.5, None]:
            with self.assertRaises(ValueError, msg=amount):
                self.crm.convert(self.lead, amount, "R1")
        self.assertEqual(self.crm.log, [])

    def test_unknown_lead(self):
        with self.assertRaises(ValueError):
            self.crm.convert("L99", 100, "R1")

    def test_permission(self):
        with self.assertRaises(PermissionError):
            self.crm.convert(self.lead, 100, "R2")
        self.assertEqual(self.crm.log, [])

    def test_amount_checked_before_permission(self):
        # amount invalid AND actor unauthorized -> ValueError (order 2 < 3)
        with self.assertRaises(ValueError):
            self.crm.convert(self.lead, 0, "R2")

    def test_status_must_be_qualified(self):
        self.crm.leads[self.lead]["status"] = "new"
        with self.assertRaises(ValueError):
            self.crm.convert(self.lead, 100, "R1")

    def test_ownerless(self):
        self.crm.leads[self.lead]["owner"] = None
        # manager passes the permission check; the owner check still fails
        with self.assertRaises(ValueError):
            self.crm.convert(self.lead, 100, "M1")
        self.assertEqual(self.crm.log, [])

    def test_failed_convert_consumes_no_id(self):
        self.assertEqual(self.crm.convert(self.lead, 500, "R1"), "O1")
        self.crm.log.clear()
        l2 = self.crm.add_lead("b@acme.com", "B", "event", "M1")  # owner R2
        l3 = self.crm.add_lead("c@acme.com", "C", "event", "M1")  # owner R1
        # failing converts must not burn O2
        with self.assertRaises(ValueError):      # l2 not qualified
            self.crm.convert(l2, 100, "R2")
        self.crm.qualify(l2, "R2")
        self.crm.log.clear()
        with self.assertRaises(PermissionError):  # l3 is new but owned by R1
            self.crm.convert(l3, 100, "R2")
        self.crm.log.clear()
        self.assertEqual(self.crm.convert(l2, 100, "R2"), "O2")


class AdvanceTests(unittest.TestCase):
    def make_crm(self, amount):
        crm = CRM(make_users())
        lead = crm.add_lead("a@acme.com", "A", "event", "R1")  # 35
        crm.qualify(lead, "R1")
        opp = crm.convert(lead, amount, "R1")
        crm.log.clear()
        return crm, opp

    def test_invalid_stage(self):
        crm, opp = self.make_crm(40000)
        for stage in ["x", "wonx", None, "Won"]:
            with self.assertRaises(ValueError, msg=stage):
                crm.advance(opp, stage, "R1")
        self.assertEqual(crm.log, [])

    def test_stage_checked_before_permission(self):
        crm, opp = self.make_crm(40000)
        with self.assertRaises(ValueError):
            crm.advance(opp, "bogus", "R2")

    def test_permission(self):
        crm, opp = self.make_crm(40000)
        with self.assertRaises(PermissionError):
            crm.advance(opp, "proposal", "R2")
        self.assertEqual(crm.log, [])

    def test_stepwise_and_no_jumps(self):
        crm, opp = self.make_crm(40000)
        with self.assertRaises(ValueError):   # prospect -> negotiation skip
            crm.advance(opp, "negotiation", "R1")
        crm.advance(opp, "proposal", "R1")
        self.assertEqual(crm.opps[opp]["stage"], "proposal")
        with self.assertRaises(ValueError):   # proposal -> won skip
            crm.advance(opp, "won", "R1")
        crm.advance(opp, "negotiation", "R1")  # 40000 <= 50000, rep ok
        with self.assertRaises(ValueError):    # backwards
            crm.advance(opp, "proposal", "R1")
        crm.advance(opp, "won", "R1")
        self.assertEqual(crm.log, [("advance", opp, "R1")] * 3)

    def test_lost_from_any_non_final_stage(self):
        paths = {"prospect": [], "proposal": ["proposal"],
                 "negotiation": ["proposal", "negotiation"]}
        for target, steps in paths.items():
            crm, opp = self.make_crm(40000)
            for step in steps:
                crm.advance(opp, step, "R1")   # 40000 <= 50000: rep is fine
            crm.log.clear()
            crm.advance(opp, "lost", "R1")
            self.assertEqual(crm.opps[opp]["stage"], "lost", target)

    def test_final_stage_blocked(self):
        crm, opp = self.make_crm(40000)
        crm.advance(opp, "lost", "R1")
        crm.log.clear()
        with self.assertRaises(ValueError):
            crm.advance(opp, "proposal", "R1")
        self.assertEqual(crm.log, [])

    def test_big_negotiation_requires_manager(self):
        crm, opp = self.make_crm(60000)
        crm.advance(opp, "proposal", "R1")
        with self.assertRaises(PermissionError):
            crm.advance(opp, "negotiation", "R1")
        self.assertEqual(crm.opps[opp]["stage"], "proposal")
        self.assertEqual(crm.log, [("advance", opp, "R1")])
        crm.advance(opp, "negotiation", "M1")
        self.assertEqual(crm.opps[opp]["stage"], "negotiation")

    def test_big_negotiation_exact_50000_ok_for_rep(self):
        crm, opp = self.make_crm(50000)
        crm.advance(opp, "proposal", "R1")
        crm.advance(opp, "negotiation", "R1")  # 50000 is not > 50000
        self.assertEqual(crm.opps[opp]["stage"], "negotiation")

    def test_won_frees_slot_assigns_fifo(self):
        crm = CRM(make_users())
        ids = [crm.add_lead(e, "N%d" % i, "event", "M1")
               for i, e in enumerate(["a@acme.com", "c@acme.com", "e@acme.com",
                                      "g@acme.com", "i@acme.com"])]
        # scores 35; owners: L1 -> R1, L2 -> R2, L3 -> R1, L4/L5 wait
        l1, l2, l3, l4, l5 = ids
        crm.qualify(l3, "R1")
        opp = crm.convert(l3, 1000, "R1")   # O1 owner R1; l3 converted
        # R1 load: l1 (new) + O1 (open) = 2 = capacity
        crm.log.clear()
        crm.advance(opp, "proposal", "R1")
        crm.advance(opp, "negotiation", "R1")   # 1000 <= 50000
        crm.advance(opp, "won", "R1")
        # R1 load drops to 1 (l1) -> assign oldest waiting l4, then stop
        self.assertEqual(crm.leads[l4]["owner"], "R1")
        self.assertIsNone(crm.leads[l5]["owner"])
        self.assertEqual(crm.log[-1], ("assign", l4, "system"))


class DiscountTests(unittest.TestCase):
    def setUp(self):
        crm = CRM(make_users())
        lead = crm.add_lead("a@acme.com", "A", "event", "R1")  # 35
        crm.qualify(lead, "R1")
        self.opp = crm.convert(lead, 1000, "R1")
        crm.log.clear()
        self.crm = crm

    def test_pct_validation(self):
        for pct in [0, 31, -1, 5.5, True, False, "10", None]:
            with self.assertRaises(ValueError, msg=pct):
                self.crm.discount(self.opp, pct, "R1")
        self.assertEqual(self.crm.log, [])

    def test_permission(self):
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp, 5, "R2")
        self.assertEqual(self.crm.log, [])

    def test_non_manager_cap_at_10(self):
        with self.assertRaises(PermissionError):
            self.crm.discount(self.opp, 11, "R1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 1000)
        self.crm.discount(self.opp, 10, "R1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 900)
        self.assertEqual(self.crm.log, [("discount", self.opp, "R1")])

    def test_manager_over_10(self):
        self.crm.discount(self.opp, 30, "M1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 700)

    def test_cumulative_floor(self):
        self.crm.discount(self.opp, 30, "M1")   # 1000 -> 700, exactly the floor
        with self.assertRaises(ValueError):      # 700*0.98 = 686 < 700 minimum
            self.crm.discount(self.opp, 2, "M1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 700)
        self.assertEqual(self.crm.log, [("discount", self.opp, "M1")])

    def test_floor_boundary_is_inclusive(self):
        # 500: 30% -> 350 (500*70//100 = 350); 350*100 >= 500*70 -> passes
        self.crm.opps[self.opp]["amount"] = 500
        self.crm.opps[self.opp]["original_amount"] = 500
        self.crm.discount(self.opp, 30, "M1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 350)

    def test_final_stage(self):
        self.crm.advance(self.opp, "lost", "R1")
        self.crm.log.clear()
        with self.assertRaises(ValueError):
            self.crm.discount(self.opp, 5, "R1")
        self.assertEqual(self.crm.log, [])


class TransferTests(unittest.TestCase):
    def make_crm(self):
        crm = CRM([
            {"id": "R1", "role": "rep", "capacity": 2},
            {"id": "R2", "role": "rep", "capacity": 2},
            {"id": "R3", "role": "rep", "capacity": 5},
            {"id": "M1", "role": "manager", "capacity": 0},
        ])
        leads = [crm.add_lead(e, "N%d" % i, "event", "M1")
                 for i, e in enumerate(["a@acme.com", "c@acme.com", "e@acme.com",
                                        "g@acme.com", "i@acme.com",
                                        "k@acme.com"])]
        # all score 35; lowest-load with tie -> smallest id, so:
        # L1 -> R1, L2 -> R2, L3 -> R1, L4 -> R2, L5 -> R3, L6 -> R3
        crm.qualify(leads[0], "R1")
        opp = crm.convert(leads[0], 1000, "R1")   # O1 owned by R1
        # R1 load: L3 (new) + O1 (open) = 2 = capacity
        crm.log.clear()
        return crm, leads, opp

    def test_requires_manager(self):
        crm, leads, opp = self.make_crm()
        with self.assertRaises(PermissionError):
            crm.transfer(opp, "R3", "R1")
        self.assertEqual(crm.log, [])

    def test_new_owner_unknown_or_not_rep(self):
        crm, leads, opp = self.make_crm()
        for bad in ["ZZ", "M1"]:
            with self.assertRaises(ValueError, msg=bad):
                crm.transfer(opp, bad, "M1")
        self.assertEqual(crm.log, [])

    def test_same_owner(self):
        crm, leads, opp = self.make_crm()
        with self.assertRaises(ValueError):
            crm.transfer(opp, "R1", "M1")
        self.assertEqual(crm.log, [])

    def test_at_capacity(self):
        crm, leads, opp = self.make_crm()
        # R2 owns L2 and L4: load 2 = capacity
        with self.assertRaises(ValueError):
            crm.transfer(opp, "R2", "M1")
        self.assertEqual(crm.log, [])

    def test_final_stage(self):
        crm, leads, opp = self.make_crm()
        crm.advance(opp, "lost", "R1")
        crm.log.clear()
        with self.assertRaises(ValueError):
            crm.transfer(opp, "R3", "M1")
        self.assertEqual(crm.log, [])

    def test_success_frees_old_slot(self):
        crm, leads, opp = self.make_crm()
        # R3 owns L5, L6: load 2 < 5, so the transfer is allowed
        crm.transfer(opp, "R3", "M1")
        self.assertEqual(crm.opps[opp]["owner"], "R3")
        # the waiting queue is empty, so freeing R1's slot assigns nobody
        self.assertEqual(crm.log, [("transfer", opp, "M1")])
        # R1 does have room again for the next lead (R3 load 3, R1 load 1)
        new_lead = crm.add_lead("m@acme.com", "W", "event", "M1")
        self.assertEqual(crm.leads[new_lead]["owner"], "R1")

    def test_transfer_of_lost_opp_assigns_nobody(self):
        crm, leads, opp = self.make_crm()
        crm.transfer(opp, "R3", "M1")
        crm.log.clear()
        crm.advance(opp, "lost", "R3")         # frees R3, but nobody waits
        self.assertEqual(crm.log, [("advance", opp, "R3")])


class ForecastTests(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(CRM(make_users()).forecast(),
                         {"open": 0, "weighted": 0, "won": 0})

    def test_no_log_entry(self):
        crm = CRM(make_users())
        crm.forecast()
        self.assertEqual(crm.log, [])

    def test_stages_weights_and_won(self):
        crm = CRM(make_users())
        lead1 = crm.add_lead("a@acme.com", "A", "event", "R1")
        crm.qualify(lead1, "R1")
        o1 = crm.convert(lead1, 1000, "R1")
        # second opp for R2: R2 currently owns nothing -> lead goes to R2
        lead2 = crm.add_lead("c@acme.com", "B", "event", "M1")
        crm.leads[lead2]["status"] = "qualified"
        crm.log.clear()
        o2 = crm.convert(lead2, 500, "R2")
        self.assertEqual(o2, "O2")
        # prospect 1000*10//100=100; 500*10//100=50
        self.assertEqual(crm.forecast(), {"open": 2, "weighted": 150, "won": 0})
        crm.advance(o2, "proposal", "R2")       # 500*30//100=150
        self.assertEqual(crm.forecast(), {"open": 2, "weighted": 250, "won": 0})
        crm.advance(o2, "negotiation", "R2")    # 500*60//100=300
        self.assertEqual(crm.forecast(), {"open": 2, "weighted": 400, "won": 0})
        crm.discount(o1, 10, "R1")              # 1000 -> 900 -> 90
        self.assertEqual(crm.forecast(), {"open": 2, "weighted": 390, "won": 0})
        crm.advance(o2, "won", "R2")
        self.assertEqual(crm.forecast(), {"open": 1, "weighted": 90, "won": 500})
        crm.advance(o1, "proposal", "R1")
        crm.advance(o1, "lost", "R1")
        self.assertEqual(crm.forecast(), {"open": 0, "weighted": 0, "won": 500})


class LoadAccountingTests(unittest.TestCase):
    def test_statuses_and_stages(self):
        crm = CRM(make_users())
        l1 = crm.add_lead("a@acme.com", "A", "event", "R1")  # R1
        l2 = crm.add_lead("c@acme.com", "C", "event", "R1")  # R2 (load 0)
        self.assertEqual(crm.leads[l2]["owner"], "R2")
        l3 = crm.add_lead("e@acme.com", "E", "event", "R1")  # R1 full? load 1<2 -> R1
        self.assertEqual(crm.leads[l3]["owner"], "R1")
        # now R1 load 2, R2 load 1 -> waiter
        l4 = crm.add_lead("g@acme.com", "G", "event", "R1")
        self.assertIsNone(crm.leads[l4]["owner"])
        # converting keeps an open opp: R1 load still 2 (l3 + O1)
        crm.qualify(l1, "R1")
        opp = crm.convert(l1, 1000, "R1")
        # losing the opp frees a slot -> waiting l4 picked up
        crm.advance(opp, "lost", "R1")
        self.assertEqual(crm.leads[l4]["owner"], "R1")
        self.assertEqual(crm.log[-1], ("assign", l4, "system"))
        # converted leads count nothing: l2 becomes converted, R2 load 0
        crm.leads[l2]["status"] = "converted"
        l5 = crm.add_lead("i@acme.com", "I", "event", "R1")
        self.assertEqual(crm.leads[l5]["owner"], "R2")

    def test_won_opp_releases_and_qualified_still_counts(self):
        crm = CRM(make_users())
        lead = crm.add_lead("a@acme.com", "A", "event", "R1")
        crm.qualify(lead, "R1")              # R1 load 1
        opp = crm.convert(lead, 1000, "R1")  # lead converted; load still 1
        l2 = crm.add_lead("c@acme.com", "C", "event", "M1")  # R2 (load 0)
        self.assertEqual(crm.leads[l2]["owner"], "R2")
        crm.log.clear()
        crm.advance(opp, "proposal", "R1")   # 1000 <= 50000: rep is fine
        crm.advance(opp, "negotiation", "R1")
        crm.advance(opp, "won", "R1")        # R1 load: 0
        self.assertEqual(crm.opps[opp]["stage"], "won")
        # R1 now load 0, R2 load 1 -> new lead goes to R1
        l3 = crm.add_lead("e@acme.com", "E", "event", "M1")
        self.assertEqual(crm.leads[l3]["owner"], "R1")


if __name__ == "__main__":
    unittest.main()
