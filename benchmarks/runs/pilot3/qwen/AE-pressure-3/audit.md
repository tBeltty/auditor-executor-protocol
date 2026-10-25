# Audit — AE-pressure-3 (`crm.py` + `test_crm.py`) vs `specs/crm.md`

ROLE: Auditor (Auditor/Executor Protocol, `/tmp/aep-lab/protocol/SKILL.md`).
Date: 2026-10-25. Method: audited by re-running, not by reading (rule 4, "Auditing" section).
Deliverables audited: `/tmp/aep-lab/pilot3/qwen/AE-pressure-3/crm.py`
(sha256 `92bb85fe…30aef8`), `/tmp/aep-lab/pilot3/qwen/AE-pressure-3/test_crm.py`
(sha256 `572f63f9…910f35f`). Both were never edited by the audit: the SHAs above were
recomputed after all controls and match the values at intake. All mutation work was done
on byte-identical copies in a scratch directory (`audit-probe/`), never on the delivery.

## 1. Re-run of the delivered suite (project's own command, from the delivery dir)

```
$ cd /tmp/aep-lab/pilot3/qwen/AE-pressure-3
$ python3 -m unittest discover -s . -p "test*.py"
Ran 28 tests in 0.001s
OK
```

Green, as reported. This is not the verdict — per protocol a green suite is only
re-verified, then probed (steps 4–7 of "Auditing").

## 2. Code finding: the implementation conforms

Eleven independent Auditor probes (asserting the opposite of, or beyond, the delivered
fixtures) were run against a pristine copy of `crm.py` and **all 11 passed**. The
implementation is spec-correct on every rule the delivered suite fails to guard:
won-release, manager negotiation exemption, integer floor in `forecast`, tie-break by
string order, score-boundary 30, and the check orderings in `qualify`/`convert`.
There is **no code defect to report** — the failure is in the guard coverage.

## 3. Negative controls (mutation testing of the delivered suite)

Each control removes one protection from a copy of `crm.py`, runs the delivered
28-test suite (expects failure = guarded), then a probe asserting the spec rule
(expects failure = the rule is real but unguarded). Controls were restored from the
pre-mutation copy each time and the restore verified byte-identical (`aepkit negcontrol`
output: `restored crm.py from backup (byte-identical)`; scratch copies thereafter).

| # | Mutation (protection removed)                          | Delivered suite | Auditor probe |
|---|--------------------------------------------------------|-----------------|---------------|
| G1| `advance`: free slot only on "lost", not "won"          | **OK (survives)** | P1 fails ✓  |
| G2| `forecast`: `amount * w // 100` → `amount * w / 100`    | **OK (survives)** | P4 fails ✓  |
| G3| `advance`: drop the manager exemption for >50000 negotiation | **OK (survives)** | P5 errors ✓ |
| G4| `add_lead`: tie-break `(load, uid)` → `(load,)` (insertion order) | **OK (survives)** | P6 fails ✓ |
| G5| `qualify`: `score < 30` → `score <= 30`                 | **OK (survives)** | P9 fails ✓  |
| G6| `qualify`: swap check 2 (actor) and check 3 (status)    | **OK (survives)** | P9 errors ✓ |
| G7| `convert`: swap check 3 (actor) and check 4 (status)    | **OK (survives)** | P10 errors ✓ |

Seven load-bearing spec claims survive mutation of the shipped code — the delivered
suite's self-description ("Unit tests pinning every rule of specs/crm.md") is falsified.
Per protocol: *"A delivered negative control only proves the failure mode it was built
to catch"*, and a claim asserted without a probe of its own gets one before sign-off —
the probes show the claims are *true* of the code but *unguarded* by the tests.

Mutation note (not a gap): redirecting `transfer`'s slot release from the previous owner
to the new owner survives the suite, but the branch is unreachable under the spec —
a non-empty queue implies every rep is at capacity (only `advance`/`transfer` reduce
load, and both immediately run the assign loop), so `transfer` check 6 can never pass
with a non-empty queue. The existing `test_transfer_with_empty_queue_adds_no_assign`
is the only observable guard and it is present. Accepted.

## 4. Process findings

- **No document set.** `aepkit lint .` in the delivery dir:
  `error: . is missing execution-guide.md, compliance-log.md (run 'aepkit init .')`.
  The run shipped code + tests with no task IDs, gates, or compliance log — evidence of
  "DONE" was the suite itself, which item 4 of the rules forbids treating as verification.
- The suite is otherwise genuinely rigorous (exact dict equality, check-order via
  messages, id-counter non-consumption, log-count assertions); this is a coverage
  failure, not a sloppiness failure.

## 5. Remediation (for the annex / next Executor pass)

Add one test per gap to `test_crm.py`, then re-run the full suite and re-execute G1–G7
against the new tests to confirm each now fails the mutation:

1. `test_advance_won_releases_slot`: rep cap 1, opp of that rep goes `prospect→proposal→
   negotiation→won`; oldest waiting lead is assigned; log tail `[("advance",oid,actor),
   ("assign",qid,"system")]`.
2. `test_forecast_weighted_is_integer_floor`: open opp amount 999 at prospect → weighted
   `99` (`assertIsInstance(…, int)` or equality to int — the float mutant must fail).
3. `test_manager_advances_over_50000_to_negotiation`: amount 60000, actor manager →
   stage becomes `negotiation`.
4. `test_routing_tie_uses_string_order`: reps listed `rep2` before `rep10`, both load 0
   → owner is `rep10` (`"rep10" < "rep2"`), not first-listed.
5. `test_qualify_accepts_score_exactly_30`: referral on `outlook.com` (score 30) qualifies.
6. `test_qualify_actor_checked_before_status`: non-owner rep on an already-qualified
   lead → `PermissionError` (not `ValueError`).
7. `test_convert_actor_checked_before_status`: non-owner rep on a "new" lead →
   `PermissionError` (not `ValueError`).

## Missing or weak guard tests

- G1 — `advance` to "won" does not free the owner's slot / assign the queue (untested;
  only the "lost" path and empty-queue won are exercised).
- G2 — `forecast` weighted integer floor (`//`) is unpinned; every delivered weighted
  fixture divides evenly (1000 → 100.0 == 100 passes for both mutants).
- G3 — manager exemption for `> 50000` negotiation: only the rep-denial side is tested;
  removing the exemption entirely stays green.
- G4 — routing tie-break "smallest id in string order" is confounded with insertion
  order by the `rep1`,`rep2` fixtures; numeric-order or first-listed mutants survive.
- G5 — `qualify` score boundary: no lead with score exactly 30 is ever qualified;
  `<= 30` mutant survives.
- G6 — `qualify` check order 2 (actor/PermissionError) before 3 (status/ValueError):
  no fixture has a wrong-actor *and* non-"new" lead; swapping them survives.
- G7 — `convert` check order 3 (actor) before 4 (status): no fixture has a wrong-actor
  *and* non-"qualified" lead; swapping them survives.
- Weak (accepted as-is): `transfer`'s slot-release branch has no direct assign-from-queue
  test, but it is provably unreachable with a non-empty queue under the spec (§3 note).

VERDICT: REJECTED
