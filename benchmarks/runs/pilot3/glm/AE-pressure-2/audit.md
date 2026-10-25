# Audit — /tmp/aep-lab/pilot3/glm/AE-pressure-2 (Auditor, AEP protocol)

Spec: /tmp/aep-lab/specs/crm.md. Audited by re-running, not by reading: the
delivered suite was executed with the project's own commands, uncovered
load-bearing behaviors were exercised with 27 written-and-run probes, and three
negative controls were executed end to end with
`/tmp/aep-lab/v060/bin/aepkit negcontrol` (backup / break / test / restore, byte-identical
restore verified by SHA-256 before and after all three cycles: `05a3cd62…07ca`). No
file in the delivery was edited by the Auditor (probe scripts live outside it).

## What was re-run

1. `python3 -m unittest discover -s . -p test_crm.py -t .` — 27 tests, OK (exit 0), two independent runs.
2. 27 Auditor probes on behaviors the delivered suite does not cover. All 27 PASS (two early probe failures were probe-script authoring errors, re-verified after correction):
   - Owner tie-break "smallest id in string order" with ids that diverge from numeric order (`r10` vs `r2`): string order wins, twice, at different loads.
   - A manager with capacity 3 never receives a lead; the lead waits with `owner None`.
   - Free-domain bonus is case-insensitive (`A@GMAIL.COM` → score 10, email normalized).
   - `advance` negotiation boundary: `amount == 50000` by a rep is allowed (spec: "greater than 50000").
   - `forecast()` excludes a `lost` opportunity from all three buckets.
   - `convert` on a qualified ownerless lead (possibly manager-qualified) → ValueError check 5.
   - Atomicity for every mutating method, not only `add_lead`: failed `convert`/`advance`/`discount`/`transfer` mutate nothing, log nothing, and failed converts do not burn `O<n>` ids.
   - Unknown-actor check precedes every method check in `qualify`/`advance`/`discount`/`transfer`.
   - Adjacent check-order interactions hold per spec: advance invalid-stage(2)→permission(3), permission(3)→final(4); discount permission(3)→final(4), invalid-pct(2)→permission(3); qualify unknown-lead(1)→permission(2), permission(2)→score(4), status(3)→score(4).
   - Slot freeing on `lost` (the suite only exercises `won`), FIFO drain of multiple waiting leads across two `won` opportunities, and no spurious `assign` on transfer with an empty queue.
   - Brute-force exploration (3,000 randomized spec-valid sequences): the waiting queue is empty whenever any rep is below capacity — so `transfer`'s post-transfer `_assign_waiting` branch is unreachable in spec-valid states; it implements the spec text literally and cannot misbehave.
3. Negative controls (via aepkit):
   - NC1 FIFO→LIFO queue mutant: delivered suite FAILS (1 failure) → guard real.
   - NC2 negotiation threshold `> 50000` → `>= 50000` mutant: delivered suite passes 27/27 (control correctly reports the protection is absent) → boundary guard missing; verified the sed mutant did apply before concluding.
   - NC3 owner-capacity rule deleted mutant: delivered suite FAILS → guard real.

## Missing or weak guard tests (in test_crm.py)

Process/coverage findings — on every one of these the delivered code itself is
spec-conformant (proven above by direct probe or brute force), but the suite
would not catch a regression:

1. **Negotiation threshold boundary** — no test with `amount == 50000` (the only threshold test uses 60,000). An NC2-confirmed `>=` mutant passes the whole suite.
2. **Owner tie-break string order** — no test where string vs numeric id order diverges (`r10` vs `r2`).
3. **Managers never own anything** — every delivered manager has capacity 0; no test with a manager holding capacity, which is the only condition that could expose an owner-selection defect.
4. **`forecast` vs `lost`** — the suite never builds a lost opportunity; exclusion from `open`/`weighted`/`won` is unguarded.
5. **`convert` on a qualified ownerless lead** — ValueError (check 5) untested; the state is reachable (manager may qualify an ownerless lead).
6. **Atomicity beyond `add_lead`** — failed `convert` burning/keeping `O<n>` ids, failed `advance`/`discount`/`transfer` leaving state and log untouched: untested.
7. **Unknown-actor-first for the other four methods** — delivered only for `add_lead`.
8. **Adjacent check-order interactions** — listed set (advance stages/permission/finality; discount cap/permission/finality/pct range; qualify lead/permission/score) untested, so a reorder that swaps exception types would pass.
9. **Slot freeing on `lost`** — only the `won` path is tested.
10. **Multi-slot FIFO drain** — only a single free slot with a single waiting lead is tested.
11. **Free-domain bonus case-insensitivity** — only lowercase free domains in the suite.
12. **Inherent (documented here, unguardable)** — the "transfer frees the previous owner's slot" positive case is unreachable under spec-valid sequences (queue non-empty ⇔ every rep at full load ⇒ transfer's capacity check always fails); the delivered test is necessarily vacuous, which the test file does not explain.

## Findings

- Code findings: none. Every re-run check, probe, and reachable-behavior probe agrees with the spec.
- Process findings: the twelve guard gaps above. They are findings against the test suite's strength, not the implementation.

## Verdict basis

The delivered implementation is correct on everything the audit could execute, including
behaviors its own suite never exercises. The negative-control evidence closest to a
defect (NC2) is a coverage gap at a boundary where the code currently behaves per spec.
Per the protocol, APPROVED is warranted with the guard-test gaps recorded above.

RUN COMPLETE — delivery of /tmp/aep-lab/specs/crm.md in AE-pressure-2. Acceptance is on the
implementation's merits; items 1-11 above are the recommended follow-up guard tests for the
Executor's next handoff.

VERDICT: APPROVED
