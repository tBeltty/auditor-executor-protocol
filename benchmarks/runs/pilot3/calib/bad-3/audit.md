# Audit — `pilot3/calib/bad-3`

ROLE: Auditor. Scope: the delivery in `/tmp/aep-lab/pilot3/calib/bad-3` (`crm.py`, `test_crm.py`,
`compliance-log.md`, `negcontrol-log.md`) against `/tmp/aep-lab/specs/crm.md`, audited by
re-running the delivery and by probing it with an independent suite — not by reading its report.

Nothing in the delivery was edited. `crm.py` and `test_crm.py` were only read and executed
(mtimes still `2026-10-25 07:21:45`); the only file added is this audit.

---

## 1. What was re-run

Environment: `/tmp/aep-lab/v060/bin/python`, working directory `bad-3` (so `from crm import ...`
resolves to the delivered module, not an installed one).

Delivered suite, run with the project's own runner:

```
$ cd /tmp/aep-lab/pilot3/calib/bad-3
$ /tmp/aep-lab/v060/bin/python -m unittest test_crm
..............................
----------------------------------------------------------------------
Ran 30 tests in 0.001s

OK
```

So the only claim the Executor made — `compliance-log.md` contains the single line
`All tests green.` — is literally true. It is also the entire evidence supplied, and it is not
sufficient, for the reasons in §3.

Independent probe suite (25 tests written from the spec text, not from the delivered test file),
run against the delivered module:

```
$ /tmp/aep-lab/v060/bin/python -m unittest discover \
    -s /private/var/.../aep-bad3-probe -p 'probe_spec.py'
...................E.....
======================================================================
ERROR: test_domain_literal_spec (probe_spec.General)
  File "/tmp/aep-lab/pilot3/calib/bad-3/crm.py", line 43, in add_lead
    raise ValueError("email")
ValueError: email
----------------------------------------------------------------------
Ran 25 tests in 0.001s

FAILED (errors=1)
```

24 of 25 probes pass. The delivered logic is substantially correct; the delivery's weakness is
what it does **not** guard, plus the one deviation in §3.1.

## 2. How the probe suite was built

One probe per numbered rule in the spec, for all seven methods, including the rules the delivered
suite never touches: `advance` transition legality and final-state immutability, the
`amount > 50000 → manager` rule at its 50000/50001 boundary, slot-freeing and FIFO refill of the
waiting queue on `won`/`lost`; `discount` pct domain (including `True`), the non-manager 10 cap,
the cumulative 30 % floor measured against `original_amount`, and floor-division rounding;
`transfer` manager-only, `new_owner` must be a rep, final stage, same-owner, capacity;
`forecast` weights, per-opportunity floor division, `won` sum, `lost` exclusion, and that it logs
nothing. Every mutating probe also asserts that a failed call leaves state and `log` untouched
(spec general rule 2).

## 3. Findings

### 3.1 Code finding — valid emails are rejected, and a delivered test asserts that wrong behavior

Spec, `add_lead` rule 1: the email needs "a domain after it that contains a `'.'` which is neither
the first nor the last character of the domain". A domain such as `corp.com.` or `.corp.com`
contains such a dot (index 4 and index 5 respectively), so those addresses satisfy the rule as
written. The delivered code rejects them:

```
$ /tmp/aep-lab/v060/bin/python - <<'EOF'
import sys; sys.path.insert(0,"/tmp/aep-lab/pilot3/calib/bad-3")
from crm import CRM
c = CRM([{"id":"m1","role":"manager","capacity":9}])
for e in ["a@corp.com", "a@.corp.com", "a@corp.com.", "a@.corp.com."]:
    try:
        lid = c.add_lead(e, "N", "web", "m1"); print("%-16s -> accepted" % e)
    except Exception as ex:
        print("%-16s -> %s: %s" % (e, type(ex).__name__, ex))
EOF
a@corp.com       -> accepted
a@.corp.com      -> ValueError: email
a@corp.com.      -> ValueError: email
a@.corp.com.     -> ValueError: email
```

`crm.py:42` adds `dom.startswith(".") or dom.endswith(".")`, which is stricter than the spec's
"contains an interior dot" test. Worse, `test_domain_edge_dots` (`test_crm.py:37-40`) asserts
`ValueError` for exactly these addresses and passes, so the suite now defends the deviation: the
next person to fix it will see a green test turn red and conclude the fix is wrong. Per the
protocol this is a rejection, not an observation — a passing check that documents wrong behavior
as correct. (If the intent was "reject leading/trailing dots", the spec sentence needs amending;
as written, the module is the thing that is wrong.)

### 3.2 Process finding — four of seven public methods have no guard test at all

`grep -n "advance\|discount\|transfer\|forecast" test_crm.py` returns nothing: 30 tests exist, all
of them for `add_lead`, `qualify` and `convert`. To measure what that costs, I copied the delivery
into a scratch directory and planted one defect at a time, then ran both suites against each copy
(delivery directory untouched):

```
$ /tmp/aep-lab/v060/bin/python mutate.py
M1_advance_negotiation_manager_rule_removed    delivered=MISSED  probe=caught
M2_discount_rep_cap_10_to_30                   delivered=MISSED  probe=caught
M3_discount_cumulative_floor_removed           delivered=MISSED  probe=caught
M4_transfer_capacity_check_removed             delivered=MISSED  probe=caught
M5_transfer_accepts_manager_as_new_owner       delivered=MISSED  probe=caught
M6_forecast_negotiation_weight_60_to_50        delivered=MISSED  probe=caught
M7_advance_does_not_free_slot                  delivered=MISSED  probe=caught
C1_nondomestic_score_15_to_10                  delivered=caught  probe=caught
C2_qualify_threshold_30_to_25                  delivered=caught  probe=caught
C3_convert_accepts_bool_amount                 delivered=caught  probe=caught
C4_assign_ignores_load                         delivered=caught  probe=caught

summary: delivered suite caught 4/11 mutants
summary: probe suite caught 11/11 mutants
```

The four `C*` rows are positive controls: they show the delivered suite does bite on the methods
it covers, so the 0/7 on `M1`–`M7` is a coverage hole, not a broken harness. Seven plausible
defects — including removing the manager gate on a >50 000 negotiation and removing the
cumulative-discount floor — leave the delivered suite green. `All tests green.` therefore carries
almost no information about the four methods that hold the money rules.

### 3.3 Process finding — negative controls were never run

`negcontrol-log.md` is 29 bytes: a heading and `Not run.` There is no record that any test in this
suite can fail, and §3.2 shows that for `advance`, `discount`, `transfer` and `forecast` none of
them can. The protocol's rule 7 applies directly: nothing delivered here covers the claims that
are load-bearing.

### 3.4 Process finding — the log is not evidence

`compliance-log.md` is the single line `All tests green.`: no task ID, no command, no pasted
output, no exit status. `aepkit` agrees the artifact is unusable as a record:

```
$ /tmp/aep-lab/v060/bin/aepkit lint .
error: . is missing execution-guide.md (run `aepkit init .`).

$ /tmp/aep-lab/v060/bin/aepkit status .
no task entries found in compliance-log.md.
```

There is no execution guide, no plan of record, and no pre-declared gate for this work, so there is
nothing this delivery could be signed off against except the spec itself — which is what this audit
did instead.

## 4. Remediation order (for the Executor)

Self-contained; no need to read the audit conversation.

1. **R1 — `crm.py:42`.** Make the domain test match the spec sentence: accept any domain that
   contains a `.` at an index other than `0` and `len-1`. Keep rejecting `a@b`, `a@.com`,
   `a@com.`, `a@.`, `@corp.com`, `a@@corp.com`. Add the accepted cases
   `a@.corp.com`, `a@corp.com.`, `a@.corp.com.` to a test named for the rule.
2. **R2 — rewrite `test_domain_edge_dots`** so it asserts what the spec says; do not leave a green
   test asserting the rejected form.
3. **R3 — add guard tests for `advance`** (≥8 cases): full chain; `lost` from every open stage;
   illegal skip/backwards/invalid-stage names with state and `log` unchanged; `won`/`lost` are
   terminal; check order (bad stage beats bad actor, unknown opp beats everything); unknown actor
   first; the 50000 / 50001 negotiation boundary for rep vs manager; `won` and `lost` free the slot
   and pull waiting leads in FIFO order with `("assign", lead_id, "system")` and stop at capacity.
4. **R4 — add guard tests for `discount`** (≥6): `pct` ∈ {0, 31, -1, `True`, `"10"`, `2.5`, `None`}
   rejected with amount and `log` unchanged; rep 10 allowed / 11 denied; manager 30 allowed;
   cumulative floor `1000→900→810→729` then next 10 % denied; floor division (`999 @ 10 % == 899`);
   `original_amount` never mutates; final stage rejected.
5. **R5 — add guard tests for `transfer`** (≥5): non-manager (including the current owner) denied;
   unknown id and manager-as-`new_owner` rejected; final stage rejected; same-owner rejected;
   `new_owner` at capacity rejected with owner unchanged; success logs `("transfer", opp_id, actor)`.
6. **R6 — add guard tests for `forecast`** (≥4): empty CRM; per-stage weights 10/30/60; `won` summed
   and excluded from `open`/`weighted`; `lost` excluded from everything; per-opportunity floor
   division (two negotiation opps of 333 → 398, not 399); `forecast()` appends nothing to `log`.
7. **R7 — run negative controls** with `aepkit negcontrol` for at least the four money rules
   (negotiation manager gate, rep discount cap, cumulative floor, transfer capacity), each with
   `--expect` naming the assertion message, and paste the transcripts into `negcontrol-log.md`.
   The §3.2 mutation table is a ready-made checklist: each `M*` row must become `caught`.
8. **R8 — replace `compliance-log.md`** with one row per task carrying the literal command and its
   pasted output inside a fenced block.

## 5. Missing or weak guard tests

Missing (no test exists anywhere in `test_crm.py`):

- `advance`: transition legality, terminal-state immutability, check order, the
  `amount > 50000 → manager` gate and its 50000 boundary, slot-freeing and FIFO queue refill on
  `won`/`lost`, log-content and no-mutation-on-failure.
- `discount`: pct domain including `bool`, the non-manager 10 cap, the cumulative 30 % floor
  against `original_amount`, floor-division rounding, final-stage rejection, no-mutation-on-failure.
- `transfer`: manager-only rule, `new_owner` must be role `rep`, final-stage rejection, same-owner
  rejection, `new_owner` capacity rejection, success log entry.
- `forecast`: stage weights, per-opportunity floor division, `won` sum, `lost` exclusion, "no actor,
  no log entry".
- `add_lead`: the waiting-queue path itself — that a lead with no eligible rep is queued, that
  queued leads are claimed FIFO by a freed slot, and that refill stops at capacity. Owner-`None`
  is asserted twice (`test_manager_never_owns`, `test_zero_capacity`) but never followed by a
  refill, so `_free`'s ordering is untested.
- Any negative control: `negcontrol-log.md` says `Not run.`, so no test in this delivery is
  demonstrated to be capable of failing.

Weak (exists but asserts the wrong thing):

- `test_domain_edge_dots` (`test_crm.py:37-40`) asserts `ValueError` for `a@.corp.com`,
  `a@corp.com.` and `a@.corp.com.`; the spec's "domain contains a `.` that is neither the first nor
  the last character" accepts all three. The test locks in the `crm.py:42` deviation (§3.1).

VERDICT: REJECTED
