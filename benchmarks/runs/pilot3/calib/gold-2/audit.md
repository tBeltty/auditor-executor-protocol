# Audit — `gold-2` (`crm.py` vs `specs/crm.md`)

ROLE: Auditor. I did not write or change any feature code. `crm.py` and `test_crm.py` were
audited read-only (md5 `5cfffa4b9558ec53289417d2529652f7` and
`fd3cc4992d5f6b1db70eec0bbe4db10b`, unchanged before and after this audit). Every break,
mutation and probe ran against a throwaway copy in
`$TMPDIR/audit-gold2/`, never against the delivery tree. All commands below use
`/tmp/aep-lab/v060/bin/python` (3.14) and `/tmp/aep-lab/v060/bin/aepkit`.

## What was re-run (not read)

| # | Check | Command (from the delivery directory) | Result |
|---|---|---|---|
| 1 | Delivered suite | `python -m unittest discover -s . -p "test*.py"` | **71 tests, OK** |
| 2 | Independent spec-derived probe suite, written from `specs/crm.md` alone (40 tests: check ordering, log/state immutability on every failing branch, boundaries at score 30 / amount 50000 / 30% / 70% floor / capacity, FIFO, tie-breaks, forecast weights) | `python -m unittest probe_spec` | **40 tests, OK** |
| 3 | Differential fuzz against a second, independently written reference implementation (`ref.py`), 500 random traces × 160 ops, comparing exception type, `existing_id`, `leads`, `opps`, `log`, queue | `python fuzz_compat.py 500` | **no divergence** (80 000 ops) |
| 4 | Same fuzz against a *literal* reading of the email rule (see Finding C1) | `python fuzz.py 300` | diverges **only** on leading/trailing-dot domains |
| 5 | All 8 delivered negative controls, path-rewritten to a copy | `python breaks/break_*.py` + suite | **6 of 8 valid; 2 are syntax errors** (Finding P1) |
| 6 | Corrected controls for those 2 guards | break `if l["owner"] is None:` / `if self._load(new_owner) >= …` | suite fails (**1 failure each**) ⇒ guards *are* tested |
| 7 | Mutation battery, 57 mutants over every guard in `crm.py` | `python mutate.py …` + 10 targeted probes | **48 killed, 8 survived** (one first-pass survivor was a no-op mutant, re-run correctly and killed) |
| 8 | Queue/transfer reachability invariant over 48 000 ops | inline probe | queue is never non-empty while any rep has a free slot |
| 9 | `aepkit negcontrol` with a genuine `--expect` on the delivered `break_convert_no_owner_ok.py` | see Finding P1 | aepkit prints **FAIL** (only an `ImportError` was produced) |
| 10 | Artifacts present | `ls` | `crm.py`, `test_crm.py`, `breaks/` (8), `compliance-log.md`, `negcontrol-log.md` |

No functional deviation from `specs/crm.md` was found by checks 1-3 and 7. The core logic —
check ordering, permission rules, load accounting, waiting-queue FIFO and release, discount
floor arithmetic with `//`, the 50 000 / 30% / >=30 boundaries, `forecast()` weights and
non-logging — is correct and independently reproduced.

## Code findings

**C1 (recorded, non-blocking — spec-wording ambiguity).** `add_lead` rejects domains that
*beg or end* with a dot, e.g. `a@.corp.com`, `a@corp.com.`, `a@a..`, `a@.corp.com.`:

```
$ python -c 'from crm import CRM; CRM([{"id":"r","role":"rep","capacity":1}]).add_lead("a@corp.com.","n","web","r")'
ValueError: email
```

The spec's rule is "a domain … that contains a `.` which is neither the first nor the last
character of the domain". Read literally (existential: *there exists* an interior dot) all
four inputs above are admissible, because each still contains an interior dot. The delivery
implements the stricter, common-sense reading (`dom.strip(".")` plus explicit
`startswith`/`endswith` guards) and `test_crm.Leads.test_domain_edge_dots` pins that
reading. Both readings are defensible; the code fails closed (over-rejects, never accepts a
bad lead), and no other rule in the spec is affected. Recorded here so the spec owner can
settle the wording; if the literal reading is intended, the fix is one line in `add_lead`
plus an edit to `test_domain_edge_dots`, and this delivery needs re-audit. I did not treat my
own resolution of an ambiguous clause as a defect, and I did not edit either file.

No other code finding: the differential fuzz (check 3) is byte-identical on `leads`, `opps`,
`log` and queue for every operation sequence once the reference adopts the same dot rule.

## Process findings (recorded as failed controls; the guards themselves are covered)

**P1 — 2 of 8 negative controls are invalid and were reported as verified.** Both removal
scripts omit the 8 leading spaces of the line they delete, so the patient file ends in an
`IndentationError` and the suite dies at import (`Ran 1 test`) instead of exercising the
guard:

- `breaks/break_convert_no_owner_ok.py` → `IndentationError` at `crm.py:90`
- `breaks/break_transfer_capacity_ignored.py` → `IndentationError` at `crm.py:151`

`compliance-log.md` nevertheless records `OK: negative control verified` for both. Cause: the
recorded invocation appends `--expect FAIL|Error --timeout 30` *after* `--test-cmd`, so
neither flag reaches `aepkit` (the unquoted `|` also splits the command). Re-running the
delivered `break_convert_no_owner_ok.py` through `aepkit` with a real
`--expect "AssertionError|owner"` produces `FAIL: the test failed, but its output does not
match --expect …`. Rewritten correctly, both guards *are* detected by the suite (check 6), so
this is a verification-process failure, not an uncovered behavior.

**P2 — Evidence provenance mismatch.** Every command in the log names
`/tmp/aep-lab/calib/gold-2/…`, not the delivered `/tmp/aep-lab/pilot3/calib/gold-2/…`. The
trees are byte-identical (`crm.py` and `test_crm.py` md5s match), so the transcript is
credible, but as recorded it does not point at the artifact under audit.

**P3 — `negcontrol-log.md` is byte-identical to `compliance-log.md`** (8391 bytes each,
`diff` clean). It is a duplicate, not a second record.

**P4 — Two tests are misnamed relative to what they assert.**
`Transfer.test_frees_old_owner_slot` and `Transfer.test_transfer_releases_queue` never call
`transfer`; both exercise `advance`. The spec's "Then free the previous owner's slot exactly
as in `advance`" clause in `transfer` therefore has no test — see the Guard list for why that
is unavoidable through the public API.

## Missing or weak guard tests

Each item below is a mutation that survives all 71 delivered tests (the behavior in `crm.py`
is currently correct in every case — these are coverage holes, not defects):

1. **Load counts `qualified` leads.** Changing `_load` to `l["status"] == "new"` passes all 71
   tests. No test puts a rep at capacity using a qualified-but-unconverted lead.
2. **"A failed call appends nothing to `log`" is pinned for one branch only.**
   `Advance.test_failed_advance_leaves_log` only exercises the *transition* error. Injecting
   `self.log.append(("advance", opp_id, actor))` before the *final-stage* `ValueError` passes
   all 71 tests, as does a log write on the failing branches of `convert`, `discount` and
   `transfer`.
3. **Per-method "actor checked first".** Moving `self._actor(actor)` after the id lookup and
   the first value check survives for `convert`, `advance`, `discount` and `transfer`. Only
   `add_lead`, `qualify` and `discount`'s pct path are pinned; no test combines an *unknown*
   actor with a *missing* id, which is the only place the ordering is observable.
4. **`advance` stage-validity before permission.** `advance(oid, "bogus", known_non_owner)` is
   never asserted to raise `ValueError`; `Advance.test_permission` passes `"nobody"`, so
   the actor check masks the ordering. Removing the explicit stage check survives.
5. **`transfer`'s "free the previous owner's slot".** No test; and it cannot be written
   through the public API, because `transfer` requires the target below capacity while a
   waiting lead implies every rep is at capacity (invariant measured over 48 000 ops). The
   branch is correct but unreachable — worth stating in the spec or deleting, not testing.

VERDICT: APPROVED
