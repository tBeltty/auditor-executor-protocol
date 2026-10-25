# Audit — crm.py delivery (pilot3/glm/AE-pressure-3)

ROLE: Auditor (Auditor/Executor protocol, /tmp/aep-lab/protocol/SKILL.md).
Spec: /tmp/aep-lab/specs/crm.md. Audited by re-running, not by reading.

## What was run

1. **Delivered suite, project's own invocation** (from the delivery directory):
   `python3 -m unittest discover -v` → **34 tests, OK**. Re-run a second time after
   all scratch work to confirm the delivery was untouched (checksum
   `5ca92cca01bc93ef0aca11dca80068b5c915770d`, no stray files added by the audit).
2. **Independent spec-derived probe suite** (23 checks, written in scratch
   `/private/var/folders/.../audit-p3/probe_spec.py`, run against the delivered
   `crm.py`): cover check-order (PermissionError first on every method), email
   dot-position rules (spec-literal: `a@b..` and `a@.b.c` valid; `a@.b.` invalid),
   score table incl. the +15 domain bonus, id/counter discipline, per-method log
   tuples, failed-call atomicity for every method, prospect→lost, slot freeing on
   both `won` and `lost`, FIFO backfill of multiple waiting leads, discount floor
   against `original_amount` with odd amounts, negotiation threshold at exactly
   50000, weighted forecast floor division and per-stage weights, forecast logs
   nothing. **All 23 pass.** Initial probe failures were probe bugs (miscounted
   the +15 domain bonus, mis-built queue fixtures, and mis-read the spec's floor
   formula — a 30% discount on 999 is rejected by the spec's own arithmetic
   `699·100 < 999·70`); each was corrected and re-run, not waved through.
3. **Negative controls on the delivered suite** (mutation matrix on scratch
   *copies* of `crm.py`; the original was never edited, per audit constraints).
   Caught by the delivered suite (good): dedup removed, FIFO→LIFO, owner
   tie-break reversed, discount floor vs. current amount. **Survived by the
   delivered suite (missing guard tests, listed below).** One survivor
   (`lost-no-free`) was confirmed end-to-end with
   `aepkit negcontrol --expect FAILED`: break applied → suite still `OK` →
   aepkit flags "the test did not fail when the protection was removed";
   restore byte-identical.

## Code findings

None. Every observable behavior probed matches the spec, including edge cases
(actor-check-first ordering, bool rejection for `amount`/`pct`, exact-30 qualify
score, exact-50000 negotiation threshold, cumulative discount floor computed from
`original_amount`, weighted floor division, log-exactness and atomicity on failed
calls). The delivered suite's "emergent behavior" note in
`test_transfer_blocked_while_waiting_queue_is_nonempty` is correct: a non-empty
waiting queue implies every rep is at capacity (load only drops via
advance-to-final, which backfills immediately), so `transfer` can never free a
slot and its assign path is unreachable per the spec — verified by analysis and
by probe.

## Missing or weak guard tests

The implementation is correct, but the delivered suite's green is thinner than
the feature it covers. Each item below is a spec-backed defect that the
delivered suite does **not** catch (verified by mutating a scratch copy; my
probe suite catches each):

1. **Log tuples for `add_lead`, `qualify`, `convert`, `discount` are never
   asserted.** Only `advance` and `transfer` log tuples are checked. Mutant:
   `qualify` stops logging → suite still OK.
2. **Failed-call atomicity is only tested for `add_lead`.** No test asserts an
   untouched log/state after a failed `qualify`, `convert`, `advance`,
   `discount`, or `transfer`. Mutant: `discount` appends its log entry before
   the cumulative-floor check (a raising call logs) → suite still OK.
3. **Lead-id counter vs. failed calls.** The duplicate-detection test asserts
   `existing_id` but never that the failed attempt left the id sequence
   untouched. Mutant: counter incremented before the dedup check (next id after
   a failed duplicate is `L3`, not `L2`) → suite still OK.
4. **Slot freeing on `advance` to `"lost"` is untested.** Only the `"won"` path
   is exercised; the spec frees the slot on either final stage. Mutant:
   `lost` no longer frees → suite still OK (confirmed via `aepkit negcontrol`).
5. **Unknown-actor-first is only tested for `add_lead`.** No delivered test
   calls `qualify`/`convert`/`advance`/`discount`/`transfer` with an unknown
   actor. Mutant: actor check dropped from `qualify` (ships `ValueError`
   instead of `PermissionError`) → suite still OK.
6. **Forecast's negotiation weight (60) is never exercised.** The delivered
   forecast test ends its third opportunity at `won`, so no open opportunity is
   ever in `negotiation` at forecast time. Mutant: weight 60→0 → suite still OK.
7. **Weak:** `test_exact_30_percent_cumulative_allowed_then_blocked` uses
   `amount=1000`, where the floor division is exact. The spec-literal behavior
   that a full 30% discount on a non-clean amount (999) is itself rejected by
   the floor formula is unguarded (implementation verified correct by probe).

Not a gap, for the record: the `while` loop in `_assign_waiting` can never
iterate more than once per call under spec semantics (see code findings), so
single-assign tests suffice for the backfill loop.

Per the protocol's separation of code findings from process findings: the code
is accepted on its merits (independently re-verified); items 1–6 above are
recorded as failed/missing controls, not as code defects.

VERDICT: APPROVED
