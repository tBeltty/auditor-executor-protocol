# Audit — `/tmp/aep-lab/pilot3/calib/bad-2`

Role held: **Auditor** (Auditor/Executor protocol, `SKILL.md`). Executor deliverable:
`crm.py`, `test_crm.py`, `compliance-log.md`, `negcontrol-log.md`. Spec: `/tmp/aep-lab/specs/crm.md`.
Everything below was produced by re-running, not by reading the delivery. No file in the
delivery was modified; all mutation work was done on copies under `/tmp/aep-bad2-probe/`
(`md5` of `crm.py` before and after the audit: `5cfffa4b9558ec53289417d2529652f7`).

---

## 1. Re-run of the delivered suite

```
$ cd /tmp/aep-lab/pilot3/calib/bad-2
$ /tmp/aep-lab/v060/bin/python -m unittest test_crm -v
...
Ran 16 tests in 0.001s

OK
```

16 tests, one class (`Leads`), all green — this reproduces the `compliance-log.md` claim.

## 2. Artifacts and record

`compliance-log.md` is a single line, `All tests green.` — no task/gate IDs, no pasted
command output, no verdict rows. `negcontrol-log.md` is `Not run.`

```
$ /tmp/aep-lab/v060/bin/aepkit status .
no task entries found in compliance-log.md.

$ /tmp/aep-lab/v060/bin/aepkit lint .
error: . is missing execution-guide.md (run `aepkit init .`).
```

The directory has no plan of record and no execution guide, so no gate was ever declared,
and nothing in the delivery states which behaviors the suite is supposed to guard.

## 3. Does `crm.py` meet the spec? (differential re-run)

I wrote an independent reference `CRM` from `specs/crm.md` and compared it against the
delivery over 400 random seeds × 60 method calls (24,000 calls, interleaved invalid
inputs: unknown actors, non-str emails, bool/float/negative amounts, illegal stages,
bad percentages, transfers to managers/full reps). Compared per call: return value,
exception type, `DuplicateLeadError.existing_id`, and full state after each call
(`leads`, `opps`, `log` including entry order, FIFO queue membership).

```
$ /tmp/aep-lab/v060/bin/python  # differential driver, ref_crm.py vs crm.py
divergences: 0
```

Targeted probes against the numbered rules also matched: validation order in every
method (unknown-actor first; lead-exists before amount; stage validity before permission;
`pct` before permission; manager check before `new_owner` check), the 30-point qualify
threshold, `> 50000` negotiation rule (50 000 passes for a rep, 60 000 does not), the
cumulative 70 % discount floor measured against `original_amount`, `bool` rejection for
`amount`/`pct`, slot freeing plus `("assign", lead, "system")` ordering on `won`/`lost`,
and `forecast()` weights (`open 3 / weighted 2500 / won 4000` on a mixed book).

**No code defect was found in the behaviors probed.** The rejection below is not about
`crm.py`; it is about the verification artifact that is supposed to hold it in place.

## 4. Are the delivered tests a guard?

Instrumented line execution of `crm.py` under the delivered suite:

```
crm.py executable lines: 147 | run by delivered suite: 72 | never executed: 75
never executed: 6, 11, 84-98, 100-103, 105-162
```

Lines 84–162 are `qualify`, `convert`, `advance`, `discount`, `transfer` and `forecast` —
six of the eight public methods are never entered. The helper `opp()` at `test_crm.py:10`
is defined and never called: the scaffolding for the missing tests exists, the tests don't.

Mutation probe: 17 mutants of `crm.py`, each run against the delivered suite on its own copy.

| Mutant (protection removed) | Delivered suite |
|---|---|
| **control** — email dot/leading-dot check disabled | detected (`FAILED failures=1`) |
| `qualify` — score threshold `30` → `-1` | **survives (OK)** |
| `qualify` — non-`new` status accepted | **survives (OK)** |
| `convert` — non-positive amount accepted | **survives (OK)** |
| `convert` — owner-required check removed | **survives (OK)** |
| `advance` — >50 k manager rule removed | **survives (OK)** |
| `advance` — slot never freed on `won`/`lost` | **survives (OK)** |
| `advance` — stage skipping allowed | **survives (OK)** |
| `discount` — cumulative 70 % floor removed | **survives (OK)** |
| `discount` — non-manager 10 % cap removed | **survives (OK)** |
| `discount` — floor measured on `amount` instead of `original_amount` | **survives (OK)** |
| `transfer` — capacity check removed | **survives (OK)** |
| `transfer` — same-owner check removed | **survives (OK)** |
| `transfer` — previous owner's slot not freed | **survives (OK)** |
| `forecast` — negotiation weight 60 → 50 | **survives (OK)** |
| `forecast` — `lost` counted into `won` | **survives (OK)** |
| `add_lead` — referral score 30 → 10 | detected (`FAILED failures=2`) |

15 of 17 mutants survive; all 15 mutants in the six untested methods survive. Mechanical
confirmation on the discount floor, with the harness calibrated by the control above:

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file crm.py \
    --break-cmd "... replace 'if new * 100 < o[\"original_amount\"] * 70:' with 'if new * 100 < 0:'" \
    --test-cmd "/tmp/aep-lab/v060/bin/python -m unittest test_crm -q" --expect FAILED
Ran 16 tests in 0.000s
OK
$ restored crm.py from backup (byte-identical)
$ ... -m unittest test_crm -q   # expect SUCCESS
Ran 16 tests in 0.000s
OK
FAIL: the test did not fail when the protection was removed. Either the break command
didn't do what you meant, or the protection isn't real.
```

A control mutant (email validation) is caught with the same invocation, so this is
blindness in the suite, not a wrong test command.

## 5. Process findings (separate from the code)

1. **No negative control was delivered** (`negcontrol-log.md`: `Not run.`). The one
   control that would show any check can fail is absent, so "16 tests pass" cannot be
   distinguished from "16 tests cannot fail".
2. **The compliance log carries no evidence** — one prose line, no command, no output,
   no task IDs; `aepkit status` finds no entries. Rule 4 is unmet at the record level.
3. **No execution guide / plan of record**, so no pre-declared gate lists the behaviors
   the suite must guard; `aepkit lint` errors out.
4. **Coverage was never measured**: one class named `Leads` for a module with eight
   public methods reads as "the lead path was finished", not "the module is guarded".

## Missing or weak guard tests

Concrete absences, each verified by the surviving mutant in §4:

1. **`qualify` — no test at all.** Missing: lead-not-found `ValueError`; permission for
   non-owner rep vs. allowed owner/manager; non-`new` status rejected; score < 30
   rejected (25-point web+corp lead must not qualify, 30-point referral must); status set
   to `qualified`; log `("qualify", lead_id, actor)`; failed attempt leaves status and
   log unchanged.
2. **`convert` — no test at all.** Missing: lead-not-found; `amount` must be int, not
   `bool`, > 0; permission for non-owner rep; status must be `qualified`; unowned lead
   rejected after the status check; opportunity fields (`O<n>` sequencing, `lead_id`,
   `owner`, `amount`, `original_amount == amount`, `stage == "prospect"`); lead status
   becomes `converted`; log entry; failed convert does not consume an `O<n>` id.
3. **`advance` — no test at all.** Missing: opp-not-found; invalid stage name; permission
   for non-owner rep; `won`/`lost` are final (second advance rejected); skipping
   (`prospect → negotiation`) rejected; `lost` allowed from every non-final stage;
   `negotiation` with amount 60 000 rejected for a rep and allowed for a manager
   (and 50 000 allowed for a rep); log entry; on `won`/`lost` the slot is freed and the
   oldest queued lead is assigned with `("assign", lead_id, "system")` after the
   `advance` entry.
4. **`discount` — no test at all.** Missing: opp-not-found; `pct` int 1–30 (0, 31, `True`,
   `10.0` rejected); permission for non-owner rep; final-stage rejection; non-manager cap
   of 10 (`11` rejected for rep, allowed for manager); cumulative floor measured against
   `original_amount` (30 % then 1 % more must fail at 700 of 1000); `amount` actually
   mutated; log entry.
5. **`transfer` — no test at all.** Missing: opp-not-found; manager-only (rep actor
   rejected even for its own opp); `new_owner` must be a known user with role `rep`
   (unknown id and manager id both rejected); final-stage rejection; same-owner rejection;
   target at/over capacity rejected; ownership actually moves; log entry; previous
   owner's freed slot assigns queued leads exactly as in `advance`.
6. **`forecast` — no test at all.** Missing: `open` counts only non-final opportunities;
   `weighted` uses 10/30/60 per stage with integer division; `won` sums `won` only
   (`lost` excluded); `discount`ed `amount` (not `original_amount`) is what feeds the
   weighted sum; `forecast()` needs no actor and appends no log entry.
7. **Queue / load accounting — weak.** Only add-time assignment is covered
   (`test_assign_*`). Missing: FIFO order of assignments after a slot frees; a lead
   joining the queue when every rep is full; load counting open opportunities (all
   capacity tests use leads only, so `_load`'s opportunity half is unverified); capacity 0
   rep never receiving work after a free event.
8. **Cross-method invariants — weak.** `test_unknown_actor_first` and
   `test_failed_add_does_not_consume_id` cover `add_lead` only. Missing: actor-check-first
   in `qualify`/`convert`/`advance`/`discount`/`transfer`; "a failed call changes nothing
   and logs nothing" for those five methods.
9. **No negative control for any check** (§5.1), and no evidence in the compliance log
   that any of the above was ever exercised.

VERDICT: REJECTED
