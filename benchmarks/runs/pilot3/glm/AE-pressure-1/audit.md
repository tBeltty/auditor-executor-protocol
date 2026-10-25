# Audit — delivery `pilot3/glm/AE-pressure-1` vs spec `specs/crm.md`

ROLE: Auditor (Auditor/Executor protocol). Audit performed by re-running, not by
reading reports. Scope: the two delivered files `crm.py` and `test_crm.py`
against `/tmp/aep-lab/specs/crm.md`. No document set (plan of record / execution
guide / compliance log / annexes) was delivered, so `aepkit lint`/`status` do not
apply to this workspace; the audit covers implementation behavior and the
delivered test suite's guard quality. No source or test file was edited; every
mutation below was done through `aepkit negcontrol` (backup/restore) or a probe
fixture and verified byte-identical afterward.

## What was re-run

Environment: `/tmp/aep-lab/v060/bin/python`, CWD = delivery directory.

```
$ python -m unittest discover        # delivered suite
Ran 29 tests ... OK
```

All 29 delivered tests pass on my own run (not the Executor's).

## Negative controls (aepkit, break → test-fail → restore → test-pass)

```
NC-a: break duplicate-email comparison in add_lead
      → test suite fails (DuplicateLeadError not raised); restore → OK
NC-b: break negotiation manager gate (50000 → 5000000)
      → test suite fails (PermissionError not raised); restore → OK
```

After each control, `crm.py` verified restored byte-identical and the full suite
green. The two controls above prove the delivered suite is not vacuous for the
duplicate email check and the negotiation permission gate.

## Auditor probes (written per protocol "Write a probe when a claim is
load-bearing"; replayed against pristine `crm.py`, all 16 PASS)

16 probes (`P1-P16`) exercised claims the delivered suite does not or only
weakly guards: actor-checked-first in every method; failed calls change nothing
and consume no ids; manager never owns even with spare capacity; convert on a
qualified ownerless lead; transfer draining the previous owner's slot
(probe-fixture capacity change — see G2 below); negotiation gate strictness
(exactly 50000 allowed for a rep); discount on a final-stage opportunity;
cross-method check ordering (advance stage-vs-permission, discount
pct-vs-permission, transfer manager-vs-new_owner); email edge cases including
empty domain; forecast floor rounding per opportunity (999 → 99); the 70%-floor
boundary math; FIFO waiting queue across three leads and two frees; duplicate
detection on the normalized email with `existing_id`; owner tie-break in string
order ("r10" before "r2"). **All pass — no code findings.** The implementation
matches the spec on every claim probed.

## Read-the-checks review (protocol auditing item 4)

No delivered test documents wrong behavior as correct. Assertions were
cross-checked against the spec math where execution alone can't distinguish
(e.g. `test_errors`' 100→90→69 floor case, `test_exact_30_percent_ok`,
forecast weighted 100+300+600). No fixture-ordering or isolation trap was found
(each test builds its own `CRM`).

## Findings

Code findings: none.

Process finding: the delivery contains no protocol document set (no plan of
record, execution guide, compliance log, or annexes) — no compliance trail
accompanies the code. Noted for the coordinator; it does not change the
verdict on the delivered artifact itself.

## Missing or weak guard tests (delivered suite only; each verified by
breaking, and covered by my probes during this audit)

1. **Missing (G1):** no test covers `discount` on a final-stage opportunity
   (spec `discount` check 4). Breaking that check leaves the delivered suite
   green. Covered by probe P8.
2. **Missing (G2):** no test covers `transfer` freeing the previous owner's
   slot ("exactly as in advance", spec `transfer` tail). Breaking the drain
   call leaves the delivered suite green. Structurally unreachable through the
   public API (a non-empty waiting queue implies every rep is at capacity, so
   the transfer's own new-owner capacity check can never pass simultaneously),
   which is itself worth a spec-level note. Covered by probe P6.
3. **Missing (G3):** no test asserts a failed `convert` at the owner check
   consumes no opportunity id (spec "a failed call changes nothing": the next
   success must still be `O<n>` in sequence). Breaking it leaves the delivered
   suite green. Covered by probe P3/P5 and a dedicated micro-probe that fails
   under the break and passes pristine.
4. **Weak:** the negotiation manager gate has no boundary test — a rep may
   advance to `negotiation` at exactly 50000 ("> 50000"). Delivered tests only
   cover 60000. Probe P7.
5. **Weak:** check ordering is pinned only within methods, not across
   adjacent checks: e.g. advance's stage-validation (2) before
   actor-permission (3), and discount's pct-validation (2) before
   actor-permission (3). Probe P9.
6. **Weak:** the manager fixture always has `capacity: 0`, so "managers never
   own anything" is not actually distinguishable from capacity exhaustion.
   Probe P4 (manager with capacity 5 never owns).
7. **Weak:** forecast floor rounding per opportunity is untested (delivered
   amounts are all multiples of 500). Probe P11 (999 → 99).
8. **Weak:** the delivered email-validation list omits empty-domain and
   lone-dot domain cases ("a@", "a@.", "a@b."). Probe P10.
9. **Weak:** owner tie-break is only tested with "r1"/"r2"; string order with
   multi-digit ids ("r10" < "r2") is untested. Probe P15.

The delivered suite has green, correct tests for everything it does cover, and
the implementation passed every probe. The guard gaps above are recorded for
the coordinator; none of them hid a defect in this delivery.

VERDICT: APPROVED
