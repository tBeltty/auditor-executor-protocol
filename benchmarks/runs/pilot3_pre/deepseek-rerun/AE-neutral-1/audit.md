# Audit — AE-neutral-1 (`crm.py` against `specs/crm.md`)

Role: Auditor (Auditor/Executor protocol, `protocol/SKILL.md`).
Artifacts audited: `/tmp/aep-lab/pilot3/deepseek-rerun/AE-neutral-1/crm.py`
(md5 `3597873beecfb26151804d90520f33a6`) and `test_crm.py`
(md5 `ac08defa4568a606f9f9f3694be60de3`). Neither file was modified.

## 1. What was re-run

Environment: `/tmp/aep-lab/v060/bin/python` (Python 3.14.7), `aepkit 0.6.0`.

```text
$ cd /tmp/aep-lab/pilot3/deepseek-rerun/AE-neutral-1
$ python -B -m unittest -q test_crm
Ran 72 tests in 0.001s
OK
```

Green is not evidence, so three further checks were run:

1. **Independent reference implementation.** `ref_crm.py` was written from
   `specs/crm.md` alone (no imports from `crm.py`), including the per-method
   check order from spec line 10.
2. **Differential fuzz.** 60 seeds x 400 operations (24,000 calls) over four
   rep/manager/capacity configurations, mixing valid and invalid emails, names,
   sources, amounts, stages, percentages, actors and ids, comparing after every
   call: return value, exception type, `existing_id`, `leads`, `opps`, `log`,
   `forecast()`, and the waiting queue.
   Result: `NO MISMATCH`. The only divergence found anywhere was the spec
   ambiguity in section 4.
3. **Mutation testing.** 52 spec-breaking mutants applied to a *copy* of
   `crm.py`, each run against the delivered suite: **39 killed, 13 survived**.
   Three survivors are equivalent mutants (they cannot change observable
   behaviour through the public API), leaving 10 real holes. A second targeted
   pass added 8 more ordering/behavioural probes. Every surviving mutant below
   was verified the same way: delivered suite stays GREEN, a spec-derived probe
   fails on the mutant and passes on the pristine code.

## 2. Implementation findings

**None.** `crm.py` matches the spec on every rule I could execute: email
normalization and domain-dot rule, name/source validation, duplicate detection
against converted leads, score table and corporate bonus, id counters that only
advance on success, load accounting, lowest-load/smallest-id ownership, FIFO
queue and its drain, all six per-method check orders, finality, the >50000
manager gate, cumulative 30% cap with floored arithmetic, transfer mechanics,
and the three forecast fields. No write to the delivery was needed to establish
this.

## 3. Missing or weak guard tests

The suite exercises the happy paths well (39/52 mutants killed) but leaves the
following spec rules unguarded. Each item below was reproduced: the delivered
suite stays green while the mutation is present.

**3.1 `advance` on a WON opportunity is unguarded** — spec l.30 ("won" and
"lost" are final). Deleting the final-stage check keeps 72/72 green.
`test_final_cannot_advance` only advances from `lost`, and the `ValueError` it
catches is actually raised by `_STAGE_ORDER.index("lost")`, not by the finality
check — the test passes for the wrong reason. A mutant that reopens a won deal
as `lost` passes the suite.
*Required test:* advance a won opportunity to `lost` and to `won`; assert
`ValueError` and that the stage is still `won`.

**3.2 `advance` to `lost` from proposal/negotiation** — spec l.29 ("From any
non-final stage an opportunity may also go to lost"). `test_lost_from_any_non_final`
only exercises `prospect`, despite its name. A mutant restricting `lost` to
prospect survives.
*Required test:* prospect -> proposal -> `lost`, and proposal -> negotiation ->
`lost`.

**3.3 `forecast()["won"]` after a discount** — spec l.41 ("sum of amount over
opportunities with stage won"). No test wins a discounted opportunity, so a
mutant summing `original_amount` survives.
*Required test:* convert 1000, manager discount 10%, advance to `won`; assert
`forecast()["won"] == 900`.

**3.4 Opportunity id counter tied to conversions, not qualifications** — spec
l.26 ("O<n> where n counts successful conversions"). Every fixture performs
exactly one `qualify` immediately before each `convert`, so an implementation
whose counter is bumped by `qualify` produces the same ids in the suite.
*Required test:* qualify lead A and lead B, then `convert(B)` -> `"O1"`,
`convert(A)` -> `"O2"`.

**3.5 `test_rounding_floor` does not discriminate floor from rounding** — spec
l.34 (`amount * (100 - pct) // 100`). At 999 with 10% both `//` and
`round(...)` give 899, so a rounding implementation survives the test that
exists to forbid it (a weak guard for a spec-mandated arithmetic detail).
*Required test:* 1015 at 10% by a manager -> 913 (rounding yields 914).

**3.6 Free-domain score exemption uses the normalized domain** — spec l.17
(domain of the normalized email; bonus unless gmail.com/yahoo.com/outlook.com).
`test_scores` only uses lowercase addresses, so scoring the raw (unlowered)
email survives: `A@GMAIL.COM` would score 25 instead of 10.
*Required test:* `add_lead("A@GMAIL.COM", ..., "web")` -> score 10.

**3.7 Check precedence (spec l.10) is almost entirely unguarded** — only
"unknown actor first" (all methods) and `convert` permission-before-status are
protected. The following 12 adjacent pairs have no test that violates both
checks at once, so each reordering mutant survives (expected first failure
listed):

| Method | Unguarded pair | Scenario -> expected |
|---|---|---|
| advance | stage validity (2) vs permission (3) | non-owner rep + `"bogus"` stage -> `ValueError` |
| advance | permission (3) vs final (4) | non-owner rep + won opp -> `PermissionError` |
| advance | transition (5) vs >50000 approval (6) | owner rep, 60000, prospect -> `negotiation` -> `ValueError` |
| convert | amount (2) vs permission (3) | non-owner rep + amount 0 -> `ValueError` |
| discount | pct validity (2) vs permission (3) | non-owner rep + pct 99 -> `ValueError` |
| discount | permission (3) vs final (4) | non-owner rep + lost opp -> `PermissionError` |
| discount | final (4) vs rep 10% cap (5) | owner rep + lost opp + pct 11 -> `ValueError` |
| discount | rep 10% cap (5) vs cumulative cap (6) | owner rep + amount 700/1000 + pct 11 -> `PermissionError` |
| transfer | existence (1) vs manager-only (2) | non-manager + `"O999"` -> `ValueError` |
| transfer | manager-only (2) vs target role (3) | owner rep + target `"m1"` -> `PermissionError` |
| add_lead | name (2) vs duplicate (4) | duplicate email + blank name -> `ValueError` |
| add_lead | source (3) vs duplicate (4) | duplicate email + `"bogus"` source -> `ValueError` |

*Required tests:* one double-violation call per row, asserting the exception
type (and, where the type is shared, the message or the resulting state).

**3.8 Tests that assert an exception type without asserting the reason.** This
is the common root of 3.1 and 3.7 and is worth a separate note: `assertRaises`
alone cannot tell "rejected for the right check" from "rejected later for a
different reason". Two delivered tests (`test_final_cannot_advance`,
`test_invalid_transitions`) and several atomicity entries are in this class.

No other gap was found: ownership tie-breaks, queue FIFO, capacity boundaries,
score thresholds (30 / 50000 / 10% / 30%), lead-id consumption on failures,
`assign` log entries, manager non-ownership, duplicate detection against
converted leads, and the zero-log `forecast` are all genuinely guarded.

## 4. Observations (not code findings)

- **No Executor report in the delivery.** The directory contains only `crm.py`
  and `test_crm.py` — no execution guide, compliance log, or pasted verify
  transcript, so there is no report to compare against and `aepkit lint`/`status`
  have nothing to read. Recorded as a process gap, not as a code defect.
- **Spec ambiguity, leading-dot domains.** Spec l.13 reads "a domain ... that
  contains a '.' which is neither the first nor the last character". Under a
  literal reading, `a@.b.c` and `a@.corp.com` would be valid (they contain an
  inner dot); under the conventional reading — the one `crm.py` and its tests
  implement — a domain beginning with `.` is invalid. The delivery is internally
  consistent and takes the conventional reading; the sentence should be
  clarified by the spec owner. Not treated as a defect.
- Two surviving mutants were excluded as equivalent, not as gaps:
  `transfer`'s `_free_slot(previous)` is unreachable through the public API (a
  non-empty waiting queue implies every rep is at capacity, so no legal
  transfer recipient exists), and removing `advance`'s stage-name validation
  cannot change the exception type (the transition check raises the same
  `ValueError`).

## 5. Verdict

`crm.py` conforms to the spec on every executed check. The guard suite does not:
18 spec-relevant behaviours are unguarded, including the finality of `won`, a
named ordering rule (spec l.10), and a test that exists for the floor rule but
cannot detect rounding. Green is therefore not evidence of correctness here.
Remediation is additive tests only — the eight items in section 3, no change to
`crm.py`.

VERDICT: REJECTED
