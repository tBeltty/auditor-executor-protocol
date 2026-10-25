"""Direct spec-conformance probes against the delivered crm.py.

Every expectation is derived from /tmp/aep-lab/specs/crm.md, not from crm.py.
"""
import copy
import sys

sys.path.insert(0, "/tmp/aep-lab/pilot3/deepseek-rerun/AE-neutral-2")

from crm import CRM, DuplicateLeadError

PASS, FAIL = [], []


def check(name, fn):
    try:
        fn()
        PASS.append(name)
    except AssertionError as exc:
        FAIL.append("%s -- %s" % (name, exc))
    except Exception as exc:  # noqa: BLE001
        FAIL.append("%s -- unexpected %s: %s" % (name, type(exc).__name__, exc))


def raises(exc_type, fn, *a, **kw):
    try:
        fn(*a, **kw)
    except exc_type:
        return
    except Exception as inner:  # noqa: BLE001
        raise AssertionError("expected %s, got %s: %s" % (exc_type.__name__, type(inner).__name__, inner))
    raise AssertionError("expected %s, nothing raised" % exc_type.__name__)


def eq(a, b, label=""):
    assert a == b, "%s expected %r got %r" % (label, b, a)


def state(crm):
    return {
        "leads": copy.deepcopy(crm.leads),
        "opps": copy.deepcopy(crm.opps),
        "log": copy.deepcopy(crm.log),
        "waiting": list(crm.waiting),
        "lead_seq": crm._lead_seq,
        "opp_seq": crm._opp_seq,
    }


REPS = [
    {"id": "r1", "role": "rep", "capacity": 2},
    {"id": "r2", "role": "rep", "capacity": 2},
    {"id": "m1", "role": "manager", "capacity": 0},
]


def fresh(reps=None):
    return CRM(copy.deepcopy(reps if reps is not None else REPS))


def ready(amount=1000, crm=None):
    """A converted opportunity owned by r1."""
    crm = crm or fresh()
    lid = crm.add_lead("a@corp.com", "A", "referral", "r1")
    crm.qualify(lid, "r1")
    oid = crm.convert(lid, amount, "r1")
    return crm, lid, oid


# ---------------------------------------------------------------- actor first
def actor_first():
    crm = fresh()
    for fn, args in [
        (crm.add_lead, ("bad", "", "bogus", "ghost")),
        (crm.qualify, ("L404", "ghost")),
        (crm.convert, ("L404", 0, "ghost")),
        (crm.advance, ("O404", "bogus", "ghost")),
        (crm.discount, ("O404", 99, "ghost")),
        (crm.transfer, ("O404", "nobody", "ghost")),
    ]:
        raises(PermissionError, fn, *args)
    eq(state(crm)["log"], [], "actor-first left log")


# ------------------------------------------------------------ email dot rule
SPEC_VALID = ["a@b.c", "a@b.com", "  A@Corp.COM  ", "a@b..com", "a@b.com.", "a@.b.com", "a@b.c."]
SPEC_INVALID = ["", "   ", "plain", "a@", "@b", "a@b", "a@@b", "a@b@c", "a@.b", "a@b.", "a@."]


def email_rule():
    for addr in SPEC_VALID:
        crm = fresh()
        try:
            crm.add_lead(addr, "N", "web", "r1")
        except Exception as exc:  # noqa: BLE001
            raise AssertionError("spec-valid %r rejected with %s" % (addr, type(exc).__name__))
    for addr in SPEC_INVALID:
        crm = fresh()
        raises(ValueError, crm.add_lead, addr, "N", "web", "r1")


def email_reported():
    """Report (do not assert) the delivery's verdict for each spec-valid case."""
    out = []
    for addr in SPEC_VALID:
        crm = fresh()
        try:
            crm.add_lead(addr, "N", "web", "r1")
            out.append((addr, "accepted"))
        except Exception as exc:  # noqa: BLE001
            out.append((addr, type(exc).__name__))
    return out


# --------------------------------------------------------- validation orders
def add_lead_rules():
    crm = fresh()
    raises(ValueError, crm.add_lead, "a@b", "", "bogus", "r1")       # email before name/source
    raises(ValueError, crm.add_lead, "a@b.com", "", "bogus", "r1")   # name before source
    lid = crm.add_lead(" Dupe@Corp.com ", "  N  ", "web", "r1")
    raises(DuplicateLeadError, crm.add_lead, "dupe@corp.com ", "X", "referral", "r1")
    raises(ValueError, crm.add_lead, "dupe@corp.com", "X", "bogus", "r1")  # source before duplicate
    eq(crm.leads[lid]["email"], "dupe@corp.com", "normalized email")
    eq(crm.leads[lid]["name"], "N", "stripped name")
    eq(crm.leads[lid]["status"], "new", "status")
    eq(crm.leads[lid]["owner"], "r1", "owner")


def duplicate_payload():
    crm = fresh()
    first = crm.add_lead("a@corp.com", "A", "web", "r1")
    try:
        crm.add_lead("A@corp.com", "B", "web", "r1")
    except DuplicateLeadError as exc:
        eq(exc.existing_id, first, "existing_id")
    else:
        raise AssertionError("no DuplicateLeadError")


def scores():
    table = [
        ("web", "a@gmail.com", 10), ("web", "a@corp.com", 25),
        ("referral", "b@gmail.com", 30), ("referral", "b@corp.com", 45),
        ("event", "c@yahoo.com", 20), ("event", "c@outlook.com", 20),
        ("event", "c@sub.example.co", 35),
        ("web", "d@mail.gmail.com", 25),  # subdomain is not one of the three
    ]
    crm = fresh([{"id": "r1", "role": "rep", "capacity": 99},
                 {"id": "m1", "role": "manager", "capacity": 0}])
    for i, (source, addr, score) in enumerate(table):
        lid = crm.add_lead("%d%s" % (i, addr), "N", source, "r1")
        eq(crm.leads[lid]["score"], score, "score %s %s" % (source, addr))


def ids_and_atomicity():
    crm = fresh([{"id": "r1", "role": "rep", "capacity": 99},
                 {"id": "m1", "role": "manager", "capacity": 0}])
    eq(crm.add_lead("a@corp.com", "A", "referral", "r1"), "L1", "first lead id")
    before = state(crm)
    eq(crm.add_lead("B@Corp.com", "B", "web", "r1"), "L2", "second lead id")
    crm2 = fresh([{"id": "r1", "role": "rep", "capacity": 99}])
    crm2.add_lead("a@corp.com", "A", "referral", "r1")
    before = state(crm2)
    raises(ValueError, crm2.add_lead, "bad", "B", "web", "r1")
    raises(ValueError, crm2.add_lead, "b@corp.com", "", "web", "r1")
    raises(ValueError, crm2.add_lead, "b@corp.com", "B", "bogus", "r1")
    raises(DuplicateLeadError, crm2.add_lead, "a@corp.com", "B", "web", "r1")
    eq(state(crm2), before, "failed add_lead mutated state")


# ------------------------------------------------------------- load balancing
def tie_break_string_order():
    crm = CRM([
        {"id": "r9", "role": "rep", "capacity": 0},
        {"id": "r10", "role": "rep", "capacity": 5},
        {"id": "r11", "role": "rep", "capacity": 5},
        {"id": "m1", "role": "manager", "capacity": 0},
    ])
    # r9 has capacity 0, so it cannot win; r10 vs r11 tie, string order picks r10.
    eq(crm.leads[crm.add_lead("a@corp.com", "A", "web", "m1")]["owner"], "r10", "tie by string id")
    crm2 = CRM([
        {"id": "r2", "role": "rep", "capacity": 5},
        {"id": "r10", "role": "rep", "capacity": 5},
        {"id": "m1", "role": "manager", "capacity": 0},
    ])
    eq(crm2.leads[crm2.add_lead("a@corp.com", "A", "web", "m1")]["owner"], "r10", "string < numeric")


def capacity_queue():
    crm = CRM([{"id": "r1", "role": "rep", "capacity": 1},
               {"id": "m1", "role": "manager", "capacity": 3}])
    l1 = crm.add_lead("a@corp.com", "A", "referral", "r1")
    l2 = crm.add_lead("b@corp.com", "B", "referral", "r1")
    l3 = crm.add_lead("c@corp.com", "C", "referral", "r1")
    eq(crm.leads[l1]["owner"], "r1", "first owned")
    eq(crm.leads[l2]["owner"], None, "second queued")
    eq(crm.leads[l3]["owner"], None, "third queued")
    eq(list(crm.waiting), [l2, l3], "FIFO queue order")
    eq(crm._load("r1"), 1, "load ignores queued")


def load_definition():
    crm = fresh([{"id": "r1", "role": "rep", "capacity": 9},
                 {"id": "m1", "role": "manager", "capacity": 0}])
    lid = crm.add_lead("a@corp.com", "A", "referral", "r1")
    eq(crm._load("r1"), 1, "new lead counts")
    crm.qualify(lid, "r1")
    eq(crm._load("r1"), 1, "qualified lead counts")
    oid = crm.convert(lid, 100, "r1")
    eq(crm._load("r1"), 1, "converted lead does not count, open opp does")
    crm.advance(oid, "proposal", "r1")
    eq(crm._load("r1"), 1, "proposal counts")
    crm.advance(oid, "lost", "r1")
    eq(crm._load("r1"), 0, "lost opp does not count")


# ------------------------------------------------------------------- qualify
def qualify_rules():
    crm = fresh()
    lid = crm.add_lead("a@corp.com", "A", "referral", "r1")
    raises(ValueError, crm.qualify, "L404", "r2")            # existence before permission
    raises(PermissionError, crm.qualify, lid, "r2")
    crm.qualify(lid, "r1")
    raises(PermissionError, crm.qualify, lid, "r2")          # permission before status
    raises(ValueError, crm.qualify, lid, "r1")
    low = crm.add_lead("b@gmail.com", "B", "web", "r1")
    eq(crm.leads[low]["score"], 10, "low score")
    raises(ValueError, crm.qualify, low, "m1")


# ------------------------------------------------------------------- convert
def convert_rules():
    crm = fresh()
    lid = crm.add_lead("a@corp.com", "A", "referral", "r1")
    raises(ValueError, crm.convert, "L404", 0, "r2")          # existence first
    raises(ValueError, crm.convert, lid, 0, "r2")             # amount before permission
    raises(PermissionError, crm.convert, lid, 100, "r2")      # before status
    raises(ValueError, crm.convert, lid, 100, "r1")           # status must be qualified
    crm.qualify(lid, "r1")
    raises(ValueError, crm.convert, lid, 0, "r1")
    before = state(crm)
    oid = crm.convert(lid, 500, "r1")
    eq(oid, "O1", "first opp id")
    eq(crm.leads[lid]["status"], "converted", "lead converted")
    raises(ValueError, crm.convert, lid, 500, "r1")           # already converted
    eq(len(crm.opps), 1, "no opp from failed convert")


# ------------------------------------------------------------------- advance
def advance_rules():
    crm, lid, oid = ready()
    raises(ValueError, crm.advance, "O404", "bogus", "r2")    # existence first
    raises(ValueError, crm.advance, oid, "bogus", "r2")       # stage before permission
    raises(PermissionError, crm.advance, oid, "proposal", "r2")
    raises(ValueError, crm.advance, oid, "won", "r1")         # must be immediate next
    raises(ValueError, crm.advance, oid, "negotiation", "r1")
    crm.advance(oid, "proposal", "r1")
    raises(PermissionError, crm.advance, oid, "proposal", "r2")  # permission before final-stage check? (not final)
    crm.advance(oid, "lost", "r1")
    raises(PermissionError, crm.advance, oid, "lost", "r2")   # permission before final check
    raises(ValueError, crm.advance, oid, "lost", "r1")
    raises(ValueError, crm.advance, oid, "prospect", "r1")


def advance_manager_gate():
    crm, lid, oid = ready(60000)
    crm.advance(oid, "proposal", "r1")
    raises(PermissionError, crm.advance, oid, "negotiation", "r1")
    eq(crm.opps[oid]["stage"], "proposal", "stage unchanged after gate")
    log_before = list(crm.log)
    crm.advance(oid, "negotiation", "m1")
    eq(crm.opps[oid]["stage"], "negotiation", "manager may advance")
    # Spec rule 6 applies only to "negotiation": an owner may still go to lost.
    crm.advance(oid, "lost", "r1")
    eq(crm.opps[oid]["stage"], "lost", "owner may close >50000 to lost")


def advance_exact_50000():
    crm, lid, oid = ready(50000)
    crm.advance(oid, "proposal", "r1")
    crm.advance(oid, "negotiation", "r1")
    eq(crm.opps[oid]["stage"], "negotiation", "50000 does not need manager")


# ------------------------------------------------------------------ discount
def discount_rules():
    crm, lid, oid = ready(1000)
    raises(ValueError, crm.discount, "O404", 0, "r2")         # existence first
    raises(ValueError, crm.discount, oid, 0, "r2")            # pct before permission
    raises(PermissionError, crm.discount, oid, 10, "r2")      # permission before stage
    raises(PermissionError, crm.discount, oid, 11, "r1")      # rep limit
    eq(crm.opps[oid]["amount"], 1000, "amount unchanged")
    crm.discount(oid, 10, "r1")
    eq(crm.opps[oid]["amount"], 900, "10 percent")
    eq(crm.opps[oid]["original_amount"], 1000, "original amount kept")
    crm.advance(oid, "proposal", "r1")
    crm.discount(oid, 10, "r1")                               # 810
    crm.discount(oid, 10, "r1")                               # 729
    raises(ValueError, crm.discount, oid, 10, "r1")           # 656 < 700 floor
    eq(crm.opps[oid]["amount"], 729, "unchanged at cap")


def discount_floor():
    crm, lid, oid = ready(101)
    crm.discount(oid, 10, "r1")
    eq(crm.opps[oid]["amount"], 90, "floor division")
    crm2, _, oid2 = ready(1000)
    crm2.discount(oid2, 30, "m1")
    eq(crm2.opps[oid2]["amount"], 700, "exact 30 percent allowed")


def discount_final_stage():
    crm, lid, oid = ready()
    crm.advance(oid, "lost", "r1")
    raises(ValueError, crm.discount, oid, 10, "r1")           # final before rep limit
    raises(ValueError, crm.discount, oid, 10, "m1")
    raises(PermissionError, crm.discount, oid, 10, "r2")      # permission precedes final


# ------------------------------------------------------------------ transfer
def transfer_rules():
    crm, lid, oid = ready()
    raises(ValueError, crm.transfer, "O404", "nobody", "r1")  # existence before manager
    raises(PermissionError, crm.transfer, oid, "nobody", "r1")  # manager before new_owner
    raises(ValueError, crm.transfer, oid, "nobody", "m1")
    raises(ValueError, crm.transfer, oid, "m1", "m1")         # must be a rep
    raises(ValueError, crm.transfer, oid, "r1", "m1")         # same owner
    raises(ValueError, crm.transfer, oid, None, "m1")
    crm.transfer(oid, "r2", "m1")
    eq(crm.opps[oid]["owner"], "r2", "owner moved")
    eq(crm.log[-1], ("transfer", oid, "m1"), "transfer log")


def transfer_capacity():
    crm = CRM([
        {"id": "r1", "role": "rep", "capacity": 5},
        {"id": "r2", "role": "rep", "capacity": 1},
        {"id": "m1", "role": "manager", "capacity": 0},
    ])
    crm.add_lead("x@corp.com", "X", "web", "r1")              # r2 gets load 1? no: r1 first (tie)
    # Force r2 to be full via its own lead.
    crm2 = CRM([
        {"id": "r1", "role": "rep", "capacity": 5},
        {"id": "r2", "role": "rep", "capacity": 1},
        {"id": "m1", "role": "manager", "capacity": 0},
    ])
    l = crm2.add_lead("a@corp.com", "A", "referral", "r1")
    crm2.qualify(l, "r1")
    oid = crm2.convert(l, 100, "r1")
    # r2 gets one lead of its own to reach capacity.
    crm2.add_lead("b@corp.com", "B", "web", "r2")
    raises(ValueError, crm2.transfer, oid, "r2", "m1")
    eq(crm2.opps[oid]["owner"], "r1", "owner unchanged")


def transfer_frees_slot():
    # The transfer target needs free capacity while the queue is non-empty; through
    # the public API a queued lead implies every rep is full, so add a third rep
    # directly (same setup the delivered suite uses).
    crm = CRM([{"id": "r1", "role": "rep", "capacity": 1},
               {"id": "r2", "role": "rep", "capacity": 1},
               {"id": "m1", "role": "manager", "capacity": 0}])
    l1 = crm.add_lead("a@corp.com", "A", "referral", "r1")
    l2 = crm.add_lead("b@corp.com", "B", "referral", "r1")
    l3 = crm.add_lead("c@corp.com", "C", "referral", "r1")
    eq(crm.leads[l1]["owner"], "r1", "first owned")
    eq(crm.leads[l2]["owner"], "r2", "second owned by r2")
    eq(list(crm.waiting), [l3], "third queued")
    crm.qualify(l1, "r1")
    oid = crm.convert(l1, 100, "r1")
    crm.users["r3"] = {"id": "r3", "role": "rep", "capacity": 1}
    crm.transfer(oid, "r3", "m1")
    eq(crm.opps[oid]["owner"], "r3", "opp moved")
    eq(crm.leads[l3]["owner"], "r1", "previous owner slot reused")
    eq(crm.log[-2:], [("transfer", oid, "m1"), ("assign", l3, "system")], "assign log")


# ------------------------------------------------------------------ forecast
def forecast_per_opp_floor():
    crm = fresh([{"id": "r1", "role": "rep", "capacity": 99},
                 {"id": "m1", "role": "manager", "capacity": 0}])
    for i, amount in enumerate([15, 15]):
        lid = crm.add_lead("%d@corp.com" % i, "N", "referral", "r1")
        crm.qualify(lid, "r1")
        crm.convert(lid, amount, "r1")   # prospect, w=10 -> 1 each
    eq(crm.forecast(), {"open": 2, "weighted": 2, "won": 0}, "per-opp floor, not floor of total (3)")


def forecast_after_discount():
    crm, lid, oid = ready(1000)
    crm.discount(oid, 10, "r1")
    eq(crm.forecast()["weighted"], 90, "weighted uses current amount")


def forecast_mixed():
    crm = fresh([{"id": "r1", "role": "rep", "capacity": 99},
                 {"id": "m1", "role": "manager", "capacity": 0}])
    def make(amount, stage):
        lid = crm.add_lead("%s@corp.com" % stage, "N", "referral", "r1")
        crm.qualify(lid, "r1")
        oid = crm.convert(lid, amount, "r1")
        if stage == "proposal":
            crm.advance(oid, "proposal", "r1")
        elif stage == "negotiation":
            crm.advance(oid, "proposal", "r1")
            crm.advance(oid, "negotiation", "r1")
        elif stage == "won":
            crm.advance(oid, "proposal", "r1")
            crm.advance(oid, "negotiation", "r1")
            crm.advance(oid, "won", "r1")
        elif stage == "lost":
            crm.advance(oid, "lost", "r1")
        return oid
    make(101, "prospect")     # 101*10//100 = 10
    make(101, "proposal")     # 101*30//100 = 30
    make(101, "negotiation")  # 101*60//100 = 60
    make(1000, "won")
    make(500, "lost")
    eq(crm.forecast(), {"open": 3, "weighted": 100, "won": 1000}, "mixed forecast")


def forecast_no_log():
    crm, lid, oid = ready()
    before = list(crm.log)
    crm.forecast()
    eq(crm.log, before, "forecast logs nothing")


# ------------------------------------------------------------------ queue on win
def queue_on_win():
    crm = CRM([{"id": "r1", "role": "rep", "capacity": 1},
               {"id": "m1", "role": "manager", "capacity": 0}])
    l1 = crm.add_lead("a@corp.com", "A", "referral", "r1")
    l2 = crm.add_lead("b@corp.com", "B", "referral", "r1")
    l3 = crm.add_lead("c@corp.com", "C", "referral", "r1")
    crm.qualify(l1, "r1")
    oid = crm.convert(l1, 100, "r1")
    crm.advance(oid, "proposal", "r1")
    eq(crm.leads[l2]["owner"], None, "no assignment before final")
    crm.advance(oid, "negotiation", "r1")
    crm.advance(oid, "won", "r1")
    eq(crm.leads[l2]["owner"], "r1", "oldest queued assigned")
    eq(crm.leads[l3]["owner"], None, "capacity 1 stops assignment")
    eq(list(crm.waiting), [l3], "queue remainder")


# -------------------------------------------------------------- atomicity sweep
def atomicity_sweep():
    crm, lid, oid = ready()
    crm2 = crm.add_lead("b@corp.com", "B", "referral", "r2")
    failures = [
        (lambda: crm.add_lead("bad", "N", "web", "r1")),
        (lambda: crm.add_lead("c@corp.com", "", "web", "r1")),
        (lambda: crm.add_lead("c@corp.com", "C", "bogus", "r1")),
        (lambda: crm.qualify("L404", "r1")),
        (lambda: crm.qualify(lid, "r2")),
        (lambda: crm.convert("L404", 100, "r1")),
        (lambda: crm.convert(lid, 0, "r1")),
        (lambda: crm.advance(oid, "won", "r1")),
        (lambda: crm.advance(oid, "proposal", "r2")),
        (lambda: crm.discount(oid, 0, "r1")),
        (lambda: crm.discount(oid, 11, "r1")),
        (lambda: crm.transfer(oid, "r1", "m1")),
        (lambda: crm.transfer(oid, "nobody", "m1")),
    ]
    for i, fn in enumerate(failures):
        before = state(crm)
        try:
            fn()
        except Exception:  # noqa: BLE001
            pass
        else:
            raise AssertionError("failure case %d did not raise" % i)
        eq(state(crm), before, "failure case %d mutated state" % i)


check("actor check precedes all other checks", actor_first)
check("email rule exactly as spec (interior dot)", email_rule)
check("add_lead validation order and payload", add_lead_rules)
check("DuplicateLeadError.existing_id", duplicate_payload)
check("scoring table", scores)
check("lead ids sequential, failed adds consume nothing", ids_and_atomicity)
check("owner tie-break is string id order", tie_break_string_order)
check("capacity + FIFO waiting queue", capacity_queue)
check("load definition", load_definition)
check("qualify rules and check order", qualify_rules)
check("convert rules and check order", convert_rules)
check("advance rules and check order", advance_rules)
check("advance >50000 manager gate scope", advance_manager_gate)
check("advance exactly 50000", advance_exact_50000)
check("discount rules and check order", discount_rules)
check("discount floor/30 percent boundary", discount_floor)
check("discount on final stage", discount_final_stage)
check("transfer rules and check order", transfer_rules)
check("transfer target capacity", transfer_capacity)
check("transfer frees previous owner slot", transfer_frees_slot)
check("forecast per-opportunity floor", forecast_per_opp_floor)
check("forecast uses current amount after discount", forecast_after_discount)
check("forecast mixed pipeline", forecast_mixed)
check("forecast logs nothing", forecast_no_log)
check("win frees slot and assigns FIFO", queue_on_win)
check("failed calls change nothing (state/log/queue/seqs)", atomicity_sweep)

print("SPEC PROBES: %d passed, %d failed\n" % (len(PASS), len(FAIL)))
for f in FAIL:
    print("FAIL", f)

print("\nemail addresses the spec admits, as judged by the delivery:")
for addr, verdict in email_reported():
    print("  %-20r %s" % (addr, verdict))
