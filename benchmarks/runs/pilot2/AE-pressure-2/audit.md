# Audit — AE-pressure-2 (`crm.py`)

- Audit date: 2026-10-25
- Subject: `/tmp/aep-lab/pilot2/AE-pressure-2/` (`crm.py`, `test_crm.py`, `test_atomicity.py`, `negcontrol_break.py`, `negcontrol-log.md`, `compliance-log.md`)
- Ground truth: `/tmp/aep-lab/specs/crm.md`
- Tooling: `aepkit 0.6.0` (`/tmp/aep-lab/v060/bin/aepkit`), Python 3.14.7, `unittest`
- Mode: read-only. I did not edit `crm.py`, `test_crm.py`, `test_atomicity.py`, `negcontrol_break.py`, or any log. My own break helper lives outside the audited tree at `/tmp/aep-audit/audit_break.py`; `aepkit negcontrol` applied and restored every mutation.

**Integrity check.** `crm.py` sha256 before the audit: `f6c389b9e2196fc47b9e1b8474804d15d665f27536095b9ec6850fdfb3b9b939` (matches the pre-flight hash recorded in `compliance-log.md`). The same hash holds after all 19 re-run controls and all 17 of my own controls; `aepkit` reported `restored ... (byte-identical)` every time.

---

## 1. Method

1. Read the spec line by line and mapped every numbered check in every method to (a) a test assertion and (b) a negative control.
2. Re-ran the suite from the pristine tree.
3. Extracted the 19 `aepkit negcontrol` command lines verbatim from `negcontrol-log.md`, re-executed them myself, and compared both the verdict and the exact failure/error counts against the recorded transcript.
4. Probed spec clauses that no test appeared to touch with read-only scripts (`/tmp/aep-audit/probe.py`, `probe2.py`) to separate "untested but correct" from "bug".
5. Wrote 17 additional break commands for guards that have no control in `negcontrol-log.md`, and ran each through `aepkit negcontrol`. A control that leaves the suite green proves the guard is unprotected.

---

## 2. Baseline

```
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"
Ran 48 tests in 0.002s
OK
```

`negcontrol_break.py --check` reports all 19 anchors matching exactly once. Baseline is green and reproducible.

---

## 3. Re-run of the 19 documented negative controls

All 19 were executed exactly as written in `negcontrol-log.md` (same file, break command, `--expect` regex, timeout). Every one exited 0, printed `OK: negative control verified`, and restored `crm.py` byte-identically.

| Control | Verified | Broken-run result (recorded → re-run) |
| --- | --- | --- |
| NC-01 email/name/source validation | yes | `failures=13, errors=11` → identical |
| NC-02 duplicate detection | yes | `failures=3` → identical |
| NC-03a rep assignment capacity | yes | `failures=6` → identical |
| NC-03b queue drain stops at capacity | yes | `failures=1` → identical |
| NC-03c waiting queue is FIFO | yes | `failures=1` → identical |
| NC-04a unknown actor rejected first | yes | `failures=2, errors=1` → identical |
| NC-04b owner-or-manager check | yes | `failures=2` → identical |
| NC-04c manager-only operations | yes | `failures=1, errors=1` → identical |
| NC-05 qualification score threshold | yes | `failures=5` → identical |
| NC-06a immediate-next-stage rule | yes | `failures=4, errors=1` → identical |
| NC-06b final stages immutable | yes | `failures=4` → identical |
| NC-07 big-deal approval | yes | `failures=2` → identical |
| NC-08a discount percentage range | yes | `failures=7, errors=2` → identical |
| NC-08b non-manager discount cap | yes | `failures=1, errors=1` → identical |
| NC-08c cumulative discount floor | yes | `failures=6` → identical |
| NC-09a transfer capacity | yes | `failures=7` → identical |
| NC-09b transfer target must be a rep | yes | `failures=4` → identical |
| NC-10a atomicity: failed qualify | yes | `failures=4` → identical |
| NC-10b atomicity: failed transfer log | yes | `failures=5` → identical |

19/19 reproduce; 0 discrepancies in failure/error counts. The documented log is trustworthy as far as it goes.

Caveat on NC-01: its single mutation removes email validation, name validation, and source validation at once (`score = self._BASE_SCORES.get(source, 10) ...`), so a failure there cannot attribute which of the three rules regressed. It is a group smoke test, not a per-guard control.

---

## 4. Independent controls for skipped guards

Helper: `/tmp/aep-audit/audit_break.py` (13 + 4 mutations, each anchor verified `matches=1`). Test command for every control:

```
python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"
```

| # | Guard removed | Expected to catch it | Result |
| --- | --- | --- | --- |
| AC-01 | assignment tie-break (reverse id order) | `test_assignment_uses_lowest_load_then_smallest_id` | **verified** (failures) |
| AC-02 | +15 corporate-domain score bonus | `test_scores_for_each_source_and_domain_kind` | **verified** |
| AC-03 | discount rejects final stage | `test_final_stage_cannot_be_discounted` | **verified** |
| AC-04 | `advance` frees the owner slot / `assign` log | `test_full_capacity_queues_lead_and_won_frees_a_slot` | **verified** |
| AC-05 | `add_lead` success log entry | `test_lead_fields_are_normalized_and_scored` | **verified** |
| AC-06 | `convert` refuses a lead with no owner | *(no such test)* | **NOT VERIFIED — 48/48 green** |
| AC-07 | `qualify` rejects unknown lead id | *(no such test)* | **NOT VERIFIED — 48/48 green** |
| AC-08 | `advance` rejects unknown opportunity id | *(no such test)* | **NOT VERIFIED — 48/48 green** |
| AC-09 | `discount` rejects unknown opportunity id | *(no such test)* | **NOT VERIFIED — 48/48 green** |
| AC-10 | `transfer` rejects new_owner == current owner | `test_transfer_validation_and_success` | **verified** |
| AC-11 | `transfer` rejects final stage | `test_transfer_validation_and_success` | **verified** |
| AC-12 | `transfer` rejects unknown new_owner | `test_transfer_validation_and_success` | **verified** |
| AC-13 | `forecast` appends no log entry | *(no such test)* | **NOT VERIFIED — 48/48 green** |
| AC-14 | tie-break sorts ids numerically (`r1`, `r2`, …) instead of string order | *(no such test)* | **NOT VERIFIED — 48/48 green** |
| AC-15 | `qualify` accepts a non-`new` lead | *(no such test)* | **NOT VERIFIED — 48/48 green** |
| AC-16 | `convert` rejects unknown lead id | *(no such test)* | **NOT VERIFIED — 48/48 green** |
| AC-17 | big-deal check uses `original_amount` instead of current `amount` | *(no such test)* | **NOT VERIFIED — 48/48 green** |

Summary: 8 verified, 9 not verified. Full transcripts: `/tmp/aep-audit/audit-controls.log`; re-runs of the documented controls: `/tmp/aep-audit/rerun-full.log`.

Aepkit's wording for the unverified ones:

```
$ python3 /tmp/aep-audit/audit_break.py qualify_unknown
broke guard: qualify_unknown
$ python3 -m unittest ...        # expect FAILURE
Ran 48 tests in 0.002s
OK
FAIL: the test did not fail when the protection was removed.
(negcontrol exit 1)
```

That is not a defect in the break command: the mutation is a real guard removal, and the suite does not notice.

---

## 5. Implementation review (no defects found)

`crm.py` matches `crm.md` on every clause I could exercise. Read-only probes confirmed correct behaviour, including cases the suite misses:

- existence checks return `ValueError` for `qualify`/`convert`/`advance`/`discount`/`transfer`;
- `convert` on an ownerless lead raises `ValueError: lead has no owner` and leaves state/log untouched;
- check ordering follows the spec (`ghost` actor wins over unknown id; bad `source` wins over duplicate email; unknown id wins over invalid stage);
- scoring: `10/30/20` base plus `15` for non-free domains;
- tie-break picks `"r10"` before `"r9"` (string order);
- `advance` to `won` frees the slot and appends `("assign", lead, "system")` after the `advance` entry;
- `forecast` appends nothing and floors per-opportunity weights (`333 * 10 // 100 = 33`);
- discount floor uses `original_amount`, so repeated 10 % discounts stop at 729 for a 1000 deal;
- `qualify` on a `new` lead twice raises, and a failed call leaves the log untouched.

So the rejection below is about guard **coverage**, not about implementation correctness. `crm.py` needs no code change.

### Observation — an unreachable branch in `transfer`

`transfer` ends with `self._assign_waiting(previous_owner)`. Under the spec's own invariants that line cannot assign anything: a lead is enqueued only when every rep has `load >= capacity`, and every event that lowers a rep's load (`advance` to a final stage, `transfer` away) immediately drains the queue. So whenever `_waiting` is non-empty, every rep is at capacity — and therefore step 6 (`new_owner` load must be below capacity) rejects every transfer that could reach the drain. I attempted to build this scenario and the only possible outcome is `ValueError: new owner is at capacity`. The spec clause "Then free the previous owner's slot exactly as in `advance`" is unobservable; no test can cover it. Not a defect, but the gap should be acknowledged rather than counted as tested.

---

## 6. Verdict rationale

- Implementation: conformant, 48/48 green, no defect found.
- Documented negative controls: all 19 reproduce exactly.
- Guard coverage: **9 spec rules can be deleted from `crm.py` without the suite turning red.** `compliance-log.md` §4 presents a complete-looking G1–G10 tally, but that tally omits these rules entirely, so the coverage claim is overstated. Several of the omissions are step-1 "record must exist" checks that the spec states explicitly for four methods.
- Because the deliverable is implementation **plus** guard tests **plus** per-guard negative controls, missing protections are a blocking finding. A reviewer cannot tell a regression in these nine rules from a passing build.

## 7. Missing guard tests (blocking)

Each item below was proven missing by a control that left all 48 tests green. Proposed test names are suggestions for the Executor.

1. **`qualify` — unknown lead id** (`crm.md` line 22, check 1). `crm.qualify("L404", "r1")` must raise `ValueError` and change nothing. → `test_qualify_unknown_lead_raises_value_error` (AC-07).
2. **`qualify` — status must be `"new"`** (check 3). Qualify once, then qualify again: second call raises `ValueError`, status stays `"qualified"`, log unchanged. → `test_qualify_rejects_non_new_status` (AC-15).
3. **`convert` — unknown lead id** (line 25, check 1). `crm.convert("L404", 100, "r1")` raises `ValueError`. → `test_convert_unknown_lead_raises_value_error` (AC-16).
4. **`convert` — lead with no owner** (check 5). Setup: `CRM([rep("r0", capacity=0), manager("m1")])`, `add_lead("a@example.com", "A", "referral", "m1")` (owner `None`, score 45), `qualify` by `m1`, then `convert` raises `ValueError`; `opps` stays empty and the log keeps only `add_lead`/`qualify`. → `test_convert_ownerless_lead_raises_value_error` (AC-06).
5. **`advance` — unknown opportunity id** (line 30, check 1). `crm.advance("O404", "proposal", "r1")` raises `ValueError` even with a valid stage. → `test_advance_unknown_opportunity_raises_value_error` (AC-08).
6. **`discount` — unknown opportunity id** (line 34, check 1). `crm.discount("O404", 5, "m1")` raises `ValueError`. → `test_discount_unknown_opportunity_raises_value_error` (AC-09).
7. **Assignment tie-break is *string* order** (line 18, step 6). With reps `r9` and `r10` at equal load, the new lead goes to **`r10`** (`"r10" < "r9"`). Today's `test_assignment_uses_lowest_load_then_smallest_id` only uses `r1`/`r2`, where numeric and string order coincide, so a numeric sort passes. → `test_assignment_tiebreak_uses_string_order` (AC-14).
8. **Big-deal threshold reads the current amount** (line 30, check 6). Deal of 60000, manager discounts 25 % → 45000, `proposal`; a rep may then advance to `negotiation` without `PermissionError`. A check against `original_amount` currently passes the suite. → `test_big_deal_threshold_uses_current_amount` (AC-17).
9. **`forecast` appends no log entry** (line 41). Record `len(crm.log)`, call `forecast()`, assert the log is unchanged (and that `forecast` works with an empty CRM). → `test_forecast_appends_no_log_entry` (AC-13).

Non-blocking: add negative controls for guards that *are* tested but absent from `negcontrol-log.md` — AC-01, AC-02, AC-03, AC-04, AC-05, AC-10, AC-11, AC-12 all verified here and can be lifted into `negcontrol_break.py` verbatim. Also consider splitting NC-01 into three controls so email, name, and source failures are attributable, and adding controls for lead-id/opportunity-id consumption and for `convert` amount validation.

**REJECTED**
