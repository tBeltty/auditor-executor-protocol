# Audit — CRM delivery (`/tmp/aep-lab/pilot3/deepseek/AE-pressure-2`)

- **Role:** Auditor (Auditor/Executor protocol, `/tmp/aep-lab/protocol/SKILL.md`).
- **Artifact audited:** `crm.py` (10,527 B) + `test_crm.py` (23,972 B), 60 tests.
- **Spec:** `/tmp/aep-lab/specs/crm.md` (42 lines).
- **Environment:** `/tmp/aep-lab/v060/bin/python` 3.14.7; `PYTHONDONTWRITEBYTECODE=1`; delivery files only read, never edited.

## Gates and results

| Gate | Claim | Method | Result |
|---|---|---|---|
| G1 | Every `CRM`/`DuplicateLeadError` behaviour matches the spec | Differential fuzz vs. an independent reference written from the spec: 150 seeds × 400 ops = 60,000 operations across 4 rep configurations, comparing `leads`/`opps`/`log`, exception type and `forecast()` after every op | **PASS** — 0 divergences |
| G2 | Failed calls change nothing and append nothing | State snapshots (leads+opps+log) around each failing probe; fuzz compares state after every op | **PASS** |
| G3 | Checks run in the spec's stated order | 21 hand-written probes of the ordering pairs (email/name/source, amount/permission, stage/permission, pct/permission, permission/status, transition/manager-threshold, cap/cumulative-floor) | **PASS** (all 21 probes) |
| G4 | Delivered suite passes | `python -m unittest -v test_crm` | **PASS** — 60/60, 0.003 s |
| G5 | Delivered suite is an adequate negative control: a spec-violating implementation must fail it | 42 mutants applied to a **copy** of `crm.py` in throwaway directories, each run against the delivered `test_crm.py` | **FAIL** — 18 mutants survive; 15 are observable spec violations (3 are provably equivalent, see below) |
| G6 | Protocol document set present | `aepkit status .` / `aepkit lint .` | **FAIL (process)** — `. is missing execution-guide.md, compliance-log.md`; no plan of record. Audited against the spec directly instead. |

**Code findings: none.** `crm.py` behaves per spec on every probe and in 60,000 differential operations. **All findings below are guard-test findings.**

## Missing or weak guard tests

Each item names the delivered-blind-spot, the mutation that survives the delivered suite, and the test required to close it.

1. **Load accounting ignores "qualified" leads.** `_load` must count leads with status `new` **or** `qualified`; the suite only ever exercises `new` leads when checking capacity. Mutant `status == "new"` passes all 60 tests. Probe shows the real code is right (a `qualified`, unconverted lead still blocks the only free slot — verified), but no test pins it. *Add:* fill a rep with one qualified-unconverted lead, then show the next lead is unowned.
2. **Two of the three free e-mail domains are unguarded.** `test_scores` only uses `gmail.com` as a free domain. Mutants deleting `yahoo.com` or deleting `outlook.com` from `FREE_EMAIL_DOMAINS` both pass all 60 tests. *Add:* assert score 10 on `a@yahoo.com` and `a@outlook.com`.
3. **Domain matching is not pinned to exact equality.** A mutant that treats subdomains as free (`domain.endswith("." + d)`) passes the suite; no test covers `mail.gmail.com`, which per spec is not in the free list and must score +15. *Add:* `a@mail.gmail.com` with source `web` → score 25.
4. **`add_lead` id sequence after non-duplicate failures is unguarded.** The suite only proves a `DuplicateLeadError` does not consume an id. Mutants that increment `_lead_seq` on an invalid name or an invalid source both pass all 60 tests, so the first successful lead is silently numbered `L2`. *Add:* fail `add_lead` with a bad name (and again with a bad source), then assert the next good lead is `L1`.
5. **`add_lead` check order: source (3) must precede duplicate (4).** A mutant that checks the duplicate e-mail before validating `source` passes the suite: no test supplies a duplicate e-mail together with an invalid source. Real code returns `ValueError`, not `DuplicateLeadError` (probe verified), but nothing pins it. *Add:* create a lead, then call with the same e-mail and `source="phone"` → `ValueError` (and `not DuplicateLeadError`).
6. **`qualify` check order: permission (2) before status (3)/score (4).** A mutant that validates status before permission passes all 60 tests; no test calls `qualify` with a non-owner rep on an already-qualified or low-score lead. Real code raises `PermissionError` (probe verified). *Add:* wrong rep on a `qualified` lead → `PermissionError`; wrong rep on a score-25 lead → `PermissionError`.
7. **`convert` check order: permission (3) before status (4).** A mutant that validates status before permission passes all 60 tests. Nothing calls `convert` with a non-owner rep on a `new` (not-yet-qualified) lead. Real code raises `PermissionError` (probe verified). *Add:* non-owner rep, `new` lead → `PermissionError`.
8. **`convert` opportunity-id sequence after denials.** The suite only proves a bad `amount` does not consume `O<n>`. A mutant that increments `_opp_seq` when permission is denied passes all 60 tests, so the next successful conversion returns `O2`. *Add:* denied `convert` (wrong rep), then a successful one → `O1`.
9. **`advance` to `lost` must free the owner's slot.** Slot-freeing is only tested on `won`. A mutant that calls `_fill_slots` only for `won` passes the suite. Real code assigns the oldest waiting lead on `lost` too (probe verified). *Add:* capacity-1 rep, one open opp, two waiting leads; `advance(..., "lost")` → first waiting lead owned, second still waiting, `("assign", lead_id, "system")` logged.
10. **`advance` check order: transition (5) before the >50000 manager rule (6).** A mutant that applies the manager rule first passes the suite, because every existing >50000 case is on a *legal* transition. No test asks for an illegal move to `negotiation` with amount > 50000. Real code raises `ValueError` (probe verified: prospect→negotiation with 60000 → `ValueError`, not `PermissionError`). *Add:* that exact call as a rep.
11. **`discount` check order: non-manager cap (5) before cumulative floor (6).** A mutant that checks the cumulative floor first passes the suite; no test has both violations at once. Real code raises `PermissionError` (probe verified: 1000 → 750 by manager, then rep `pct=20`). *Add:* that exact sequence.
12. **`forecast` after a discount is unguarded.** Every forecast test runs on pre-discount opportunities, so `original_amount` and `amount` are equal. Mutants using `original_amount` for `weighted` and for `won` both pass all 60 tests. Real code uses the discounted amount (probe: 1000, −20%, proposal → weighted 240; won → 800). *Add:* forecast with a discounted open opp and a discounted `won` opp.
13. **Ambiguous e-mail rule is locked in without a decision.** The spec requires a domain with a `.` that is *neither first nor last*. Read existentially (`'.' in domain[1:-1]`), `a@.b.c` satisfies it (dot at index 2); `crm.py` and `test_invalid_emails` reject it. One reading is wrong, and the suite currently documents the stricter one as correct. Not counted as a code defect because the stricter reading is defensible, but it must be decided explicitly (owner ruling) and pinned by a test either way; `x@y..z` is also accepted only under the stricter-labelled set and deserves the same treatment.

## Provably equivalent survivors (not gaps)

Three mutations survive but cannot be observed through the public API, so no test can guard them:

- *transfer never frees the previous owner's slot*, and *transfer frees the wrong rep's slot*. A waiting lead exists only when every rep is at capacity, and `transfer` step 6 rejects every candidate new owner in that state. Instrumented search over 40,121 queue-non-empty states (capacities 0–3, three reps, 48,000 ops): **0** reps below capacity, **0** legal transfer targets. The clause in `crm.py` is dead code that satisfies the spec's wording.
- *advance frees slots on every transition*. Same invariant makes `_fill_slots` a no-op on non-final transitions.

## Verdict rationale

The implementation is conformant, but the delivery's own guard suite cannot distinguish it from an implementation that breaks 15 observable spec rules, including load accounting (capacity/assignment), opportunity and lead id numbering, money-adjacent `forecast` arithmetic after discounts, `advance`→`lost` slot recovery, and four check-ordering contracts the spec makes explicit. Under "APPROVED = every gate independently verified" (G4 is not), the delivery is rejected on its guard tests, not on its behaviour. Closing the 13 items above (item 13 after an owner ruling) is the whole remediation; no change to `crm.py` is requested.

Missing or weak guard tests: items 1–13 above.

VERDICT: REJECTED
