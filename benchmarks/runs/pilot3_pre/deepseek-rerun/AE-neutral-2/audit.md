# Audit — AE-neutral-2 (`crm.py`)

Role held: **Auditor** (Auditor/Executor protocol, `/tmp/aep-lab/protocol/SKILL.md`).
Spec: `/tmp/aep-lab/specs/crm.md`. Delivery: `crm.py`, `test_crm_core.py`,
`test_crm_workflow.py`, `EXECUTOR_REPORT.md`.

Method — re-run, not read-only:

1. Re-ran the delivered suite with the command the report quotes.
2. Re-executed the delivered negative control from scratch (on a copy), with
   `--expect`.
3. Wrote an independent reference implementation from the spec alone and
   differential-fuzzed the delivery against it (state, log, queue, return value
   and exception class compared after every call).
4. Ran 26 targeted spec probes derived from the spec text.
5. Mutation-tested the delivered suite: one injected regression per load-bearing
   behavior, suite re-run, then the copy discarded.

Probe/audit code lives in `/tmp/aep-lab/pilot3/deepseek-rerun/audprobe/`
(`ref.py`, `fuzz.py`, `scenario.py`, `probe.py`, `mutate.py`). The delivery was
never edited: `crm.py` was `c20e39ba77bfd1…` before and after the audit.

## Re-run evidence

Delivered suite, exactly as reported (77 cases):

```
$ cd /tmp/aep-lab/pilot3/deepseek-rerun/AE-neutral-2
$ python3 -m unittest discover -s . -p "test*.py"
Ran 77 tests in 0.002s
OK
```

Delivered negative control, re-executed from scratch on a copy — replacing the
`_assign_waiting` loop with `while False:` reproduces the stated failure and the
stated restore:

```
FAIL: test_win_frees_slot_and_assigns_oldest_waiting_lead
AssertionError: None != 'r1'
FAILED (failures=1)
$ restored .../crm.py from backup (byte-identical)
OK
OK: negative control verified — the check fails without the protection and passes with it.
```

Differential fuzzing against the independent reference:

```
random sequences:  400 seeds x 80 ops  -> 0 divergences
valid workflows:   300 seeds x 70 ops  -> 0 divergences
spec probes:       25 passed, 1 failed
```

The suite is green, the negative control is real, and the implementation matches
the spec on 25 of 26 probed behaviors — including check ordering, failure
atomicity (state, log, waiting queue and id sequences unchanged across 13
failure modes), load accounting, FIFO assignment, the 50 000 manager gate, the
cumulative-discount floor and forecast arithmetic.

## Code finding (blocking)

**F1 — `add_lead` rejects email domains the spec admits; a delivered test
asserts that wrong behavior as correct.**

Spec: the domain must "contain a `.` which is neither the first nor the last
character of the domain." That is an existential rule: one interior dot makes
the domain valid. `b.com.` contains such a dot (index 1), so `a@b.com.` is
valid; so are `a@.b.com` and `a@b.c.`. `crm.py:103` rejects every domain that
starts or ends with a dot —

```python
if domain.startswith(".") or domain.endswith(".") or "." not in domain:
```

so the delivery is stricter than the spec on three probed inputs:

```
$ python3 audprobe/probe.py
FAIL email rule exactly as spec (interior dot) -- spec-valid 'a@b.com.' rejected with ValueError

  'a@b.c'     accepted
  'a@b.com'   accepted
  'a@b..com'  accepted
  'a@b.com.'  ValueError   <- spec admits (interior dot at index 1)
  'a@.b.com'  ValueError   <- spec admits (interior dot at index 2)
  'a@b.c.'    ValueError   <- spec admits (interior dot at index 1)
```

This is not a harmless observation, because `test_crm_core.py:62-63` puts
`a@b.com.` and `a@.b.com` in `test_invalid_emails`' invalid table. That test
will defend the deviation against whoever fixes it: removing the over-strict
clause makes the delivered suite fail. Per the protocol, a passing check that
documents wrong behavior as correct is a rejection, not an observation.

**Process finding (same root).** `EXECUTOR_REPORT.md` presents this as a
"Decision logged" — the Executor resolved a spec question itself instead of
stopping and asking (rule 6). It then wrote the decision into both the code and
the test, which is why the suite is green while the behavior is off-spec.

Remediation: implement the literal rule (`any(ch == "." and 0 < i < len(domain) - 1
...)`), move `a@b.com.` / `a@.b.com` out of `test_invalid_emails` into the valid
table, and keep `a@b.` / `a@.b` / `a@.` as the invalid boundary cases.

## Missing or weak guard tests

Mutation evidence: each mutant below was applied to a copy of `crm.py`, the
delivered 77-test suite re-run, and the copy deleted. `SURVIVED` means the
delivered tests do not notice the behavior changing. Four positive controls
(slot freeing on transfer, LIFO assignment, load ignoring open opportunities,
relaxed email rule) were caught, which validates the harness. Every behavior in
this table other than G1 was independently confirmed correct in the delivery by
probe or differential fuzzing — these are coverage gaps, not defects.

| # | Missing / weak guard test | Evidence | Mutant to catch it |
|---|---|---|---|
| G1 | **Email domain rule as written.** No test accepts an address whose domain has an interior dot *and* a leading/trailing dot; `test_invalid_emails` asserts the opposite. | `SURVIVED` is not the issue — the mutant is *caught*, i.e. the suite enforces the off-spec rule (F1). | Fix per F1, then assert `a@b.com.`, `a@.b.com`, `a@b.c.` are accepted and `a@b.`, `a@.b`, `a@.` rejected. |
| G2 | **`forecast` floors each opportunity before summing.** `test_mixed_pipeline` uses 1000/2000/3000, all exact multiples, so per-opp floor and floor-after-sum are indistinguishable. | `SURVIVED` — all 77 pass with `weighted` accumulated unfloored and divided once at the end. | Two prospect opps of 15 → `weighted == 2` (per-opp), not 3 (floor of total). |
| G3 | **`forecast` weights the current `amount` after a discount.** No test forecasts after `discount`. | `SURVIVED` — suite green with `original_amount` substituted into `weighted`. | Convert 1000, discount 10 %, then `forecast()["weighted"] == 90`. |
| G4 | **Owner tie-break is "smallest id in string order", not numeric.** `test_lowest_load_then_smallest_id` only uses `r1`/`r2`, where the two orders agree. | `SURVIVED` — suite green with `int(item[1][1:])` as the tie-break key. | Reps `r2`, `r10` equal load → owner `r10`. |
| G5 | **`advance` rule 6 applies only to `negotiation`.** No test closes an opportunity above 50 000 to `lost` as its owner, so over-applying the manager gate is invisible. | `SURVIVED` — suite green with the gate extended to `lost`. | Convert 60 000, advance to `proposal`, then owner moves it to `lost` with no PermissionError. |
| G6 | **`transfer`: opportunity existence is checked before the manager gate.** Every transfer test passes a known `opp_id`; the existence-then-permission pair is never exercised. | `SURVIVED` — suite green with the two checks swapped. | `transfer("O404", "nobody", "r1")` → `ValueError`, not `PermissionError`. |
| G7 | **`discount`: permission is checked before the final-stage check.** No test has a non-owner acting on a final opportunity. | `SURVIVED` — suite green with those two checks swapped. | Advance to `lost`, then `discount(opp, 10, "r2")` (known rep, not owner) → `PermissionError`. |
| G8 | **Failure atomicity for `add_lead` name/source failures and for `qualify` by a non-owner.** `test_name_validation` / `test_source_validation` assert only the exception; `test_other_rep_cannot_qualify` asserts only `status`. Nothing asserts the log, queue or id sequences stayed untouched. | `SURVIVED` — suite green with a log entry appended *before* the failing name check, and before the non-owner `qualify` rejection. | Assert full state (leads, opps, log, waiting, next id) after each failing call; the probes in `probe.py` already do this and pass. |
| G9 | **Negative-control coverage.** One control (queue assignment on a win) cannot cover the other load-bearing claims. No delivered probe removes the >50 000 manager gate, the cumulative-discount cap on `original_amount`, the FIFO order, or the per-opportunity forecast floor. | Report lists exactly one control. | One `aepkit negcontrol` per claim; G2–G5 mutants above are ready-made break commands. |

Also noted (not a guard-test gap): `test_transfer_frees_previous_owner_slot`
reaches its setup by writing `crm.users["r2"]` directly. Through the public API
a non-empty queue implies every rep is full, so that clause is unreachable
otherwise; the white-box setup is defensible but should be commented as such.

VERDICT: REJECTED
