# Audit — `/tmp/aep-lab/pilot3/glm/AE-neutral-2` against `/tmp/aep-lab/specs/crm.md`

ROLE: Auditor (auditor-executor-protocol). Audited by re-running, not by reading.
No file in the delivery was edited; mutations for negative controls were applied
to a scratch copy under `/private/var/folders/.../opencode/audit-p3/nc/`.

## 1. Re-run of the delivered suite

```
$ cd /tmp/aep-lab/pilot3/glm/AE-neutral-2 && python3 -m unittest test_crm -v
Ran 66 tests in 0.003s
OK
```

## 2. Independent spec probes (Auditor-written, executed against the delivery)

Probe scripts `probe1.py` / `probe2.py` (scratch dir, outside the delivery) assert
spec behavior directly; 25 checks, all PASS. Highlights — each is a claim the
delivered suite does not itself pin:

- Transfer to a rep at capacity raises ValueError; owner, queue and log unchanged.
- Transfer with an empty queue appends no `assign` entries.
- `add_lead`: unknown actor raises PermissionError even when email/name/source are
  also invalid (actor check is first).
- Email dot rule: `a@b.c`, `a@b..c`, `a@.b.c`, `a@b.c.` accepted; `a@b`, `a@b.`,
  `a@.b` rejected (dot must exist strictly inside the domain).
- Manager can qualify an ownerless lead; converting an ownerless lead raises
  ValueError and appends nothing.
- Load accounting: a converted lead plus its open opportunity still weighs 1;
  `lost`/`won` frees the slot and pulls the oldest queued lead (FIFO).
- `forecast` weights and floor division (55→5, 101 at proposal→30, negotiation→60);
  `lost` excluded; no log entry.
- `DuplicateLeadError` is an Exception with `existing_id`.
- Negotiation over 50000: rep denied at 50001, rep allowed at 50000, manager allowed.
- `won` from `prospect` (skip) rejected.
- Manager with spare capacity never receives a lead (owners are reps only).
- Duplicate email is detected against a lead in any status (incl. `converted`).

## 3. Negative controls (re-executed from scratch, on a scratch copy of the delivery)

Each mutation was applied to a copy of `crm.py`, the delivered suite was run
(expect failure), the copy was restored from backup byte-identical (verified with
`diff`), and the suite was re-run (expect OK). Run with `python3 -B` and
`__pycache__` cleared between steps.

| Control | Mutation | Suite after mutation | Suite after restore |
|---|---|---|---|
| NC1 | duplicate-email check removed | FAILED (failures=2) | OK |
| NC2 | 30% cumulative cap `<` → `<=` | FAILED (errors=2) | OK |
| NC3 | owner tie-break min→max | FAILED (failures=8, errors=1) | OK |
| NC4 | rep discount cap `> 10` → `>= 10` | FAILED (errors=4) | OK |
| NC5 | `qualify` logs before its checks | FAILED (failures=6) | OK |

The delivered suite is not vacuous: every injected defect is caught, including the
"log only on success" rule and the owner-selection tie-break.

## 4. Code conformance findings

No code defects found. All check orders specified per method (actor first; then the
numbered order) are implemented as specified, including the orderings the delivered
suite does not distinguish (probes A1/A2): `advance` permission before final-stage
check, `discount` rep-cap before cumulative-cap check. ID counters consume values
only on successful calls. `transfer`'s slot-freeing branch (spec line 39) is
implemented as written; note that under the spec's own semantics a non-empty
waiting queue implies every rep is at capacity, so `transfer` check 6 always
rejects first and that branch is unreachable through the public API — this is a
property of the spec, not a defect in the delivery.

## 5. Missing or weak guard tests (in the delivered `test_crm.py`)

The suite is strong (66 tests, check-order and negative-state coverage), but the
following guards are missing or weak. Each was probed by the Auditor and the
implementation is correct, so these are test gaps, not defects:

1. `advance` — no test distinguishes check 3 (owner-or-manager PermissionError)
   from check 4 (current-stage-final ValueError). A final-stage opportunity
   advanced by an unauthorized rep must raise PermissionError. (Probe A1: correct.)
2. `discount` — no test distinguishes check 5 (rep pct cap, PermissionError) from
   check 6 (cumulative-cap ValueError). A rep discounting 11% on an opportunity
   already at the 30% floor must raise PermissionError. (Probe A2: correct.)
3. Duplicate-email detection is only tested against a lead with status `new`; no
   test checks a duplicate against a `qualified`/`converted` lead. (Probe A3:
   correct — DuplicateLeadError with the existing id.)
4. "Managers never own anything" is never directly pinned: every fixture gives the
   manager capacity 0, so a queued lead cannot distinguish "manager skipped" from
   "no capacity anywhere". A fixture with a zero-capacity rep and a high-capacity
   manager would. (Probe: correct — owner stays None.)
5. `transfer`'s slot-freeing branch ("free the previous owner's slot exactly as in
   advance") has no test with a non-empty waiting queue; per the spec's own
   semantics that state is unreachable through the public API (a non-empty queue
   implies all reps are at capacity, so transfer check 6 rejects first). Only the
   empty-queue no-spurious-assign case is tested. Unfixable as a black-box test;
   noted for the spec owner.
6. Minor: no explicit test that a failed `transfer`/`advance`/`discount` on a
   *valid* entity (failure at a late check) appends nothing —
   `test_failed_calls_append_nothing` exercises only failures on nonexistent
   entities, plus the add/duplicate path. (NC5 shows the suite would still catch a
   log-on-failure regression in `qualify` via other assertions.)

## 6. Verdict

Every claim in the delivery was re-run independently: the delivered suite passes,
all 25 spec probes pass, and five injected-defect negative controls confirm the
suite detects real regressions. No code defect was found; the items in section 5
are missing/weak guard tests recorded as process findings, none of which changes
the behavior of the delivered module.

VERDICT: APPROVED
