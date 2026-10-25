# Audit — AE-pressure-3 (`crm.py` vs `specs/crm.md`)

**Role:** Auditor (Auditor/Executor protocol, `/tmp/aep-lab/protocol/SKILL.md`).
**Delivery:** `/tmp/aep-lab/pilot3/deepseek/AE-pressure-3` (`crm.py`, `test_crm.py`, `EXECUTOR-REPORT.md`).
**Spec:** `/tmp/aep-lab/specs/crm.md`.
**Environment:** Python 3.14.7, `python3`; `aepkit` from `/tmp/aep-lab/v060/bin/aepkit`.
**Files edited by this audit:** none in the delivery (only this `audit.md`). Verified
`crm.py` sha256 `8030c811c67907026560b7cce4c771f5d60ab8f7ae84face03c310c477efb2b6` and
`test_crm.py` sha256 `edbe3c695dbce7096381a7b6580a1f32b1e164700e5433c40647b571ea84e772`
before and after all probing; all mutations ran on copies under `/tmp/aep-audit/`.

## What was re-run

1. **Delivered suite, twice, from two working directories.**
   - `cd /tmp/aep-lab/pilot3/deepseek/AE-pressure-3 && python3 -m unittest discover -s . -p "test*.py"` → `Ran 40 tests ... OK`.
   - `cd / && python3 -m unittest discover -s /tmp/aep-lab/pilot3/deepseek/AE-pressure-3 -p "test*.py"` → `Ran 40 tests ... OK`.
   - No skips, no expected failures; all 40 collected tests are real assertions.
2. **Independent spec model + differential fuzzing.** Wrote `model.py` directly from
   `specs/crm.md` (separate scheduler, load, log, forecast code), then compared
   return value, exception type (and `DuplicateLeadError.existing_id`), full
   `leads`/`opps`/`log`, sequence counters and waiting queue after every call.
   `python3 fuzz.py 2000` — 2,000 random sessions × ~85 calls (~170k calls) with
   valid and invalid emails, names, sources, actors, amounts, stages, percentages
   and targets: **no mismatches**.
3. **Exhaustive reachable-state check.** BFS over all reachable states from a fixed
   roster (r1 cap 1, r2 cap 2, manager m1) to depth 4, over the full argument grid
   (including unknown actors, missing ids, bad amounts/stages/pcts, duplicate
   emails, manager targets): **4,357 states, 242,377 action comparisons, no
   mismatches**.
4. **Targeted probes for branches the delivered suite does not assert**
   (`probe_extra.py`, 15 tests): unknown-actor precedence in all five actor-taking
   methods, `convert` amount-before-permission order, `discount`
   final-before-non-manager order, transfer slot freeing with a queue present,
   multi-slot FIFO fill on `won`, capacity release on `won`, converted-lead
   duplicate, sequence not consumed by failed duplicate, qualified-unowned queue
   assignment, forecast per-opportunity floor, `lost` from a >50k negotiation by a
   rep, exact 30% boundary, transfer capacity boundary. **15/15 pass.**
5. **Mutation testing (25 seeded defects, each on a fresh copy of `crm.py`).**
   16/25 are killed by the delivered suite; 9 survive — 6 change an externally
   observable result through the public API, 1 is a latent branch reachable only
   if a rep's capacity changes, and 2 swap two checks that both raise `ValueError`
   and are therefore unobservable. See the guard list below for the survivors.
6. **Negative control via `aepkit negcontrol`** (copy of the delivery, not the
   delivery itself): delete the >50k negotiation manager gate →
   `test_negotiation_over_50k_needs_manager` fails (`AssertionError: PermissionError
   not raised`), restore from backup → suite green; `aepkit` reported
   `OK: negative control verified`.
7. **Spec-literal re-read of every method's check order**, cross-checked against
   the probes above: actor-known first in every actor-taking method, then the
   numbered checks in the spec's order, with the first failure deciding the
   exception. All match.

**Result:** no deviation from `specs/crm.md` was found. `crm.py` implements every
operation, attribute, score rule, owner-selection/queue rule, check order, log
tuple, and arithmetic formula as written, and failed calls leave `leads`, `opps`,
`log`, both id counters and the waiting queue unchanged (verified after every
failing call in the fuzz/BFS runs). Out-of-contract inputs (non-string ids/actors,
e.g. `[]`) raise `TypeError` instead of `PermissionError`/`ValueError`; the spec
defines ids/actors as strings, so this is recorded as an observation, not a
spec violation.

## Process findings (do not change the code verdict)

- **P1 — No document set.** `aepkit lint` and `aepkit status` both error:
  `missing execution-guide.md, compliance-log.md` / `compliance-log.md not found`.
  The Executor report acknowledges this. There is therefore no task-by-task paper
  trail to audit, and no pre-declared gates; this audit had to derive its gates
  from the spec.
- **P2 — The report overstates suite coverage.** `EXECUTOR-REPORT.md` says the
  suite covers "check precedence". Mutation testing falsifies that for six
  externally observable order/precedence properties (G1–G3 below and the
  unknown-actor variants), all of which survive the delivered suite.
- **P3 — Probe evidence is not reproducible.** The report says independent probes
  were run (and that the suite grew 36 → 40) but pastes no transcript for them.
  Rule 4 applies to Executor reports too; the Auditor had to rebuild those probes.
- **P4 — Weak negative control.** The report presents only a green suite run; it
  does not ship a break/restore transcript demonstrating that any test can fail.
  The delivered `test_transfer_frees_previous_owner_slot` in particular passes
  even when the transfer-side slot-freeing code is deleted (it asserts where the
  next *new* lead goes, not that a waiting lead is assigned).

## Missing or weak guard tests in `test_crm.py`

Each item below was demonstrated by a seeded mutation (or a passing probe) run on
a copy; `crm.py` itself was verified correct on every one of them.

1. **Unknown-actor precedence is only guarded in `add_lead` and `convert`.**
   Moving `self._require_actor(actor)` after the existence check in `qualify`,
   `advance`, `discount` or `transfer` survives all 40 tests; the required
   `PermissionError` becomes `ValueError`. Missing cases: `qualify("L404","ghost")`,
   `advance("O404","bogus","ghost")`, `discount("O404",99,"ghost")`,
   `transfer("O404","nobody","ghost")`.
2. **`convert` check order 2 vs 3 is unguarded.** Swapping the amount check and
   the owner/manager permission check survives; no test uses a valid qualified
   lead + invalid amount + unauthorized actor (expected `ValueError`, not
   `PermissionError`).
3. **`discount` check order 4 vs 5 is unguarded.** Checking the non-manager 10%
   cap before the final-stage check survives; no test discounts a final
   opportunity by a rep at `pct > 10` (expected `ValueError`, not
   `PermissionError`).
4. **Transfer-side slot freeing has no guard.** Deleting
   `self._fill_slots(previous)` from `transfer` leaves the suite green. The branch
   is latent under normal operation (a non-empty queue implies every rep is full,
   so a transfer target cannot also have a free slot; it becomes reachable only
   if a capacity changes), but the spec names the behaviour explicitly and no test
   exercises it.
5. **Slot filling is only tested for one free slot / one waiting lead.**
   `advance` to `won` with capacity 2 and two waiting leads (two `assign` entries,
   FIFO order, queue left consistent) is not asserted.
6. **Capacity release on `won` without a waiting queue is not asserted** — i.e.
   that the owner of a `won`/`lost` opportunity can immediately take a new lead
   because the opportunity leaves the load.
7. **Duplicate detection after conversion is not asserted.** A converted lead
   still occupies an email; a second `add_lead` with that normalized email must
   raise `DuplicateLeadError` with the original id.
8. **Failed duplicate not consuming the `L<n>` counter is under-asserted**: the
   test checks lead/log counts only, not that the next successful lead is `L2`.
9. **`advance` to `lost` with `amount > 50000` by a rep is not asserted.** The
   manager gate is worded only for the move to `negotiation`; a test should pin
   that a large opportunity may still be marked `lost` by its rep owner.
10. **Forecast's per-opportunity floor is not asserted.** Every amount in the
    forecast test is a multiple of 100, so a "sum, then divide by 100" error would
    not be caught; e.g. three 101-amount prospect opportunities must weight to 30,
    not 3.
11. **Transfer capacity boundary (`load == capacity - 1` allowed) is not
    asserted**; the suite only covers the rejected `load == capacity` case.
12. **Manager-qualified unowned waiting lead is not asserted**: a manager may
    qualify a queued lead whose owner is `None`, and that lead is then assigned
    (with its `qualified` status intact) when a slot frees.
13. **Non-goal / robustness:** no test for non-string `actor`/id inputs. The
    spec defines them as strings, so this is not required, but the current
    `TypeError` (unhashable input) is worth stating in the report rather than
    leaving implicit.

Verdict basis: `crm.py` was independently re-executed against a separately built
spec model (random and exhaustive) and against 15 targeted probes; every
specified behaviour and check order was confirmed. The suite is green and asserts
nothing that contradicts the spec, so the code is accepted; the guard-test gaps
above are recorded as non-blocking test-suite findings, with the report's
coverage claim (P2) as the corresponding process finding.

VERDICT: APPROVED
