# Audit — AE-neutral-3 against `/tmp/aep-lab/specs/crm.md`

**Auditor session:** 2026-10-25. **Method:** re-running, not reading — protocol SKILL.md
"Auditing (Auditor)" steps 1–7. The delivery directory was never mutated: every
break/mutation ran in a scratch copy (`$TMP/negctl`) and the delivered `crm.py`
SHA-256 `02fdbbc51d81f308fb0c7b1d192e287693b986d5a4270378765721ae30b37f63` is
unchanged at close. Probe scripts were deleted after use.

## 1. Re-runs (independent, this session)

| Command | Result |
|---|---|
| `python3 -m unittest discover -s . -p "test*.py"` (delivery dir, v060 Python 3.14.7) | **Ran 149 tests — OK** (rc 0) |
| Per-file counts | 40 + 24 + 38 + 17 + 30 = 149 — matches the log exactly |
| `aepkit lint .` | 1 issue: `[missing report] P0-T1` (the `### P0-T1 — DONE (awaiting audit)` heading does not parse as a report entry) |
| `aepkit status .` | Both IDs PENDING, awaiting audit — consistent with the log |
| Executor's 5 negative controls, re-executed from scratch with `aepkit negcontrol --expect` (negotiation boundary `>=`, rep cap `pct > 30`, deleted `existing_id`, `while False` drain, log-before-raise on unknown actor) | **All 5 verified** ("fails without the protection, passes with it"); copy restored byte-identical |
| Auditor spec probe (15 independent assertions: convert 3-before-4 and 3-before-5, advance 5-before-6 skip-to-negotiation, rep winning a >50000 deal from negotiation, transfer 2-before-3, post-transfer ownership and slot, failed-call log neutrality, DuplicateLeadError contract, forecast floor-division) | **15/15 PASS** |

## 2. Mutation battery (does a wrong build stay green?)

Each mutation applied to the scratch copy, full suite run, `__pycache__` cleared
between passes (an early batch produced false "CAUGHT" reads from stale `.pyc`
files — size-preserving swaps inside the same clock second; results below are the
clean re-run and are reproducible).

| # | Mutation (wrong behavior) | Outcome | Meaning |
|---|---|---|---|
| M1 | `convert`: status-check before owner/manager-check | CAUGHT (`test_permission_failures_change_nothing`, via the converted lead) | convert 3-before-4 genuinely pinned |
| M2 | `advance`: 50000-manager rule before legal-move rule | **SURVIVED** | advance 5-vs-6 order has **no guard** |
| M3 | `transfer`: target-validity before manager-role check | **SURVIVED** | transfer 2-vs-3 order has **no guard** |
| M4 | `advance`: manager also required to WIN big (>50000) | **SURVIVED** | "rep may win a big deal" has **no guard** |
| M5 | string-order tie-break replaced by numeric | CAUGHT (`test_load_of_both_reps_zero...`) | control ✓ |
| M6 | 70%-floor made exclusive | CAUGHT (3 boundary tests) | control ✓ |
| M7 | `convert`: owner-must-exist check before owner/manager check | **SURVIVED** | convert 3-vs-5 has **no guard** |
| M8 | `discount`: floor before rep cap | CAUGHT (`test_rep_cap_is_ten...`, via the 737 amount) | discount 5-before-6 genuinely pinned |

## 3. Code findings

**None.** Every spec statement I could establish by running holds: actor-first
`PermissionError`; failed calls change nothing and log nothing; load and FIFO
semantics; `L<n>`/`O<n>` success counters; score table and free-domain bonus on the
whole lowercased domain; all method check orders that the spec makes observable
(probes P1–P3, P5, M-none apply: the implementation raised the spec-mandated
exception in every discriminating case, including the four where no test guards
it — behavior correct, guard absent). The acknowledged email-domain reading
("some interior `.`", so `a@corp..` valid, `a@.corp.` invalid) is the literal one:
the spec says "contains a '.'" and reserves "exactly one" for the `@`; the
implementation matches it and pins it in tests. The unreachable-by-construction
drain after `transfer` (log Observation 1) is sound — I re-derived the invariant
(a non-empty queue implies every rep at capacity, and every load-decreasing
operation drains immediately) and the delivered tests pin both observable
consequences.

## 4. Process findings (not blocking the code, recorded per protocol)

1. **The document set is unfilled scaffold.** `plan-of-record.md` and
   `execution-guide.md` are the `aepkit init` templates (placeholder phases, empty
   gates, item-8 rules blank, opportunity/shaping fields unfilled); `annexes/` is
   empty; the log candidly says so and executed against the TASK block + spec
   instead. `aepkit lint` still reports P0-T1 as having no report entry because the
   heading carries a status suffix. No gate definition ever existed for P0-G1.
2. **The log's "pinned explicitly" list is overstated.** It claims
   `convert 3-4/3-5; advance 5-6` are order-pinned; M2/M7 show advance 5-6 and
   convert 3-5 are not (convert 3-4 and the rest of the list are true — verified
   by M1/M8/controls). The claim, not the code, is what failed.
3. `test_winning_a_big_deal_needs_no_manager` is misnamed: its docstring asserts
   check 6 names negotiation only, but the body ends at `advance(..., "lost", ...)`,
   exercising a different claim. The behavior is correct (probe P4) — the coverage
   is not what the name advertises.
4. Ordering claims inside `add_lead` checks 1–3 (email/name/source) are listed as
   pinned; they are all `ValueError` and genuinely unobservable from outside. Not a
   defect — a wording caution for the log.

## 5. Guard-strength verdict input

The suite is strong: 149 tests, exact-dict and exact-log assertions throughout,
full state-snapshot invariants on failure paths, five negative controls that all
re-verify, and mutation controls M1/M5/M6/M8 caught. It leaves the four specific
order/behavior claims below unguarded; the implementation currently satisfies all
four (probes), so these are missing guards, not wrong code.

## Missing or weak guard tests

1. **`advance` — check 5 before check 6 not pinned.** No test asks for the
   discriminating case: a rep calling `advance(opp, "negotiation")` from
   `prospect` (illegal skip) with `amount > 50000` must raise `ValueError`, not
   `PermissionError`. `test_check_order_legal_move_before_manager_rule` uses target
   `"won"`, which check 6 never inspects — insensitive to the swap (M2 survived).
2. **`transfer` — check 2 before check 3 not pinned.** No test covers
   non-manager actor + invalid `new_owner` (e.g. `transfer(opp, "ghost", "r1")` by
   a rep): spec requires `PermissionError`, but with checks swapped a `ValueError`
   passes every delivered test (M3 survived).
3. **`convert` — check 3 before check 5 not pinned.** No test converts a *waiting*
   (unowned) qualified lead as a non-manager rep, where spec order yields
   `PermissionError` but a swapped build yields `ValueError` (M7 survived). The
   sibling claim (3 before 4) is genuinely pinned, but only incidentally, via the
   `converted`-status lead inside `test_permission_failures_change_nothing` — a
   rename or refactor of that test could silently drop it.
4. **"A rep may win a >50000 deal" not pinned (weak/misnamed guard).**
   `test_winning_a_big_deal_needs_no_manager` never advances to `won` (it goes to
   `lost`), so loosening check 6 to also guard `won` keeps the suite green
   (M4 survived). Add: walk 60001 to negotiation via manager, then
   `advance(opp, "won", "r1")` must succeed and log `("advance", opp, "r1")`.
5. **Minor:** non-string-actor `PermissionError` is pinned only for `qualify`
   (`test_non_string_actor_is_unknown`); `add_lead`/`convert`/`advance`/`discount`/
   `transfer` rely on the shared `_check_actor` with string-actor tests only.

VERDICT: APPROVED
