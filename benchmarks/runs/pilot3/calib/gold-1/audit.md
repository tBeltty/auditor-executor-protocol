# Audit — `crm.py` against `/tmp/aep-lab/specs/crm.md`

ROLE: Auditor (Auditor/Executor protocol, `Auditor/Executor` §"Auditing"). I re-ran; I did not read and agree.
Delivery: `/tmp/aep-lab/pilot3/calib/gold-1/` — `crm.py` (sha1 `57c6dd0f…`), `test_crm.py` (sha1 `a1165e71…`, 71 tests, 112 assertions).
I did not modify either file. All mutation work ran on copies in `/tmp/aep-audit-scratch/` whose hashes match the delivered files exactly.

## 1. What I re-ran

| Command | Result |
|---|---|
| `/tmp/aep-lab/v060/bin/python -m unittest discover -s . -p "test*.py"` | `Ran 71 tests … OK` (exit 0) |
| same suite, `-v` | 71/71 pass, no skips, no xfail |
| `aepkit negcontrol` × 8 delivered break scripts, re-executed from scratch on a copy | 6 verified on the intended assertion; **2 verified only via `IndentationError`** (§3.3) |
| `aepkit status .` | `no task entries found in compliance-log.md` |
| `aepkit lint .` | `error: . is missing execution-guide.md` |

## 2. Independent evidence beyond the delivered suite

**2.1 Mutation campaign — 105 single-point mutants, 79 killed, 17 survived, 9 skipped** (anchor not unique). A surviving mutant means the suite cannot tell the guarded implementation from the broken one. Of the 17 survivors, 9 were proven equivalent, no-op, or unreachable through the public API:

- `add_lead` stage whitelist widened (`"closed"` accepted) — still `ValueError` via the transition check.
- `add_lead` `e.count("@") != 1` → `< 1` — still `ValueError` (unpacking then fails).
- `qualify` threshold `< 30` → `< 29` — score 29 is unreachable; real scores are {10, 20, 25, 30, 35, 45}.
- `discount` pct bound `<= 30` → `<= 31` — pct > 30 always violates the 70 % floor too, because `amount ≤ original_amount` (see §4.6).
- `transfer`'s `self._free(old)` → `pass` — **unreachable**: a non-empty waiting queue implies every rep is at capacity, which leaves no legal transfer target. Measured: 0 of 38,156 queued states admitted a legal transfer; `_free`'s `while` never assigned more than one lead (0 occurrences in 48,000 random calls).
- `_free` LIFO→"FIFO by sorted id" — identical order, ids are insertion-ordered.
- two mutants were my own no-ops (`amount + 0`, duplicated counter line); discarded.

The remaining 17−9 = 8 survivor instances are 7 distinct unguarded behaviours, listed in §5.

**2.2 Differential fuzz against an independent reference model.** I wrote a second implementation straight from the spec text and compared 1,000 random sequences × 60 operations (5 rep/capacity profiles, valid and invalid actors, bad amounts, out-of-order stages, cumulatively discounted opportunities). Compared on every call: outcome kind, exception **type**, and full state (`leads`, `opps`, `log`, queue order).

```
trials done, divergences: 0        # edge-dot emails excluded
```

Zero divergence. Adding `"a@corp.com."` / `"a@.corp.com"` produced exactly three divergences, all in that one rule (§4.7) — i.e. the implementation is behaviourally identical to an independently derived reading of the spec on every rule except the one the spec leaves ambiguous.

**2.3 Targeted probes for claims the suite does not assert** (`probe2.py`, `probe3.py` — all five pass on the delivered code):

- unknown-actor-first, `convert`, every check pair;
- unknown-actor-first, `transfer`, every check pair;
- a rep holding a **qualified** lead counts at load and is skipped for new work;
- a manager-converted opportunity is owned by the lead's owner, not the manager (`_load("m1") == 0`);
- a manager-driven `advance` to `lost` releases the queued lead to the **rep**, not the manager;
- `transfer` is accepted when the target has room even though the old owner's load equals the target's capacity;
- a failed `convert` does not burn an `O<n>`;
- 15 distinct failing calls leave `leads`, `opps`, `log` and queue **byte-identical** (spec line 8).

**2.4 Artifact checks.** `breaks/` holds 8 break scripts (one per claimed control); `compliance-log.md` and `negcontrol-log.md` exist. Timestamps: sources 07:21:40, logs 07:21:42 — logs post-date the code, so nothing is stale.

## 3. Process findings

These do not change the verdict on the artifact. They are recorded because a good outcome must not validate a broken control backward.

**3.1 No task or gate record.** `aepkit status` finds no task IDs, no `DONE` reports, and no verdicts; `aepkit lint` fails on a missing execution guide and plan of record. The delivery is an artifact plus two ad-hoc logs, so there is no per-task evidence trail to audit — the audit had to be built from the spec and the artifact, as done here.

**3.2 The two logs are the same file.** `compliance-log.md` and `negcontrol-log.md` are byte-identical (8,391 bytes, `diff` clean). Both record commands against `/tmp/aep-lab/calib/gold-1/…` while the delivery lives at `/tmp/aep-lab/pilot3/calib/gold-1/…`; the delivered `breaks/*.py` also hard-code `pathlib.Path('/tmp/aep-lab/calib/gold-1/crm.py')`. As shipped, the documented commands mutate a **different tree** than the one under audit, and would leave this `crm.py` untouched. The transcripts are consistent with being produced in the sibling tree and copied here.

**3.3 Two of eight negative controls are invalid.** `break_convert_no_owner_ok.py` and `break_transfer_capacity_ignored.py` delete a guarded block but leave its leading indentation behind, so the mutated file does not parse. Re-run from scratch:

```
break_advance_bigdeal_ge        VERIFIED   PermissionError: r1
break_advance_no_free           VERIFIED   AssertionError: None != 'r1'
break_assign_highest_load       VERIFIED   PermissionError: r1
break_convert_no_owner_ok       VERIFIED   IndentationError: unexpected indent   <-- false positive
break_discount_floor_strict     VERIFIED   ValueError: floor
break_dup_ignored               VERIFIED   AssertionError: DuplicateLeadError not raised
break_qualify_threshold_31      VERIFIED   ValueError: score
break_transfer_capacity_ignored VERIFIED   IndentationError: unexpected indent   <-- false positive
```

`--expect "FAIL|Error"` accepts a syntax error as proof of a guard. Both protections *are* in fact covered by positive tests (mutation kills them: `convert no owner guard`, `transfer no capacity`), so this is a control-quality defect, not a code defect — but the two controls as written prove nothing.

## 4. Code findings

**None.** Every numbered rule of the spec was exercised and holds. Specifically verified: actor check first in all six methods; check order per method including the pairs the suite never tests; failed call mutates nothing; load definition; email/name/source validation and normalization; duplicate `existing_id`; id counters; scoring incl. the free-domain bonus; lowest-load assignment, id tie-break, manager exclusion, zero-capacity, FIFO queue; `qualify`/`convert`/`advance`/`discount`/`transfer`/`forecast` semantics incl. the 50,000 boundary, the 70 % floor with truncating division, and the 50000-vs-discounted-amount interaction.

**4.7 One ambiguity the spec must settle (no functional risk either way).** Spec line 13: the domain must "contain a `'.'` which is neither the first nor the last character of the domain." For `corp.com.` the dot at index 4 is neither first nor last, so the literal rule accepts it; the delivered code rejects it, and `test_domain_edge_dots` asserts that rejection. The same literal reading also accepts `a@.corp.com`, which no sane validator intends. The delivery takes the conventional strict reading consistently; if the literal wording governs, `test_domain_edge_dots` is documenting a defect. Clarify the sentence in the spec, then align the test.

## 5. Missing or weak guard tests

Each entry names the behaviour, the mutant that survives the full suite, and whether the delivered code is nevertheless correct (probe evidence in §2.3).

1. **`convert`: unknown actor must win over every other check.** Mutant removing `self._actor(actor)` from `convert`: 71/71 green. No test calls `convert` with an unknown actor (it *is* tested for `add_lead`, `qualify`, `advance`, `discount`). Code is correct.
2. **`transfer`: unknown actor must win.** Same mutant on `transfer`: 71/71 green. Code is correct.
3. **Load counts leads with status `qualified`** (spec line 9). Mutant `_load` counting only `"new"`: 71/71 green — every lead that reaches `qualified` in the suite is immediately converted or the capacity check never turns on it. Code is correct.
4. **A manager-converted opportunity is owned by the lead's owner.** Mutant `"owner": actor` in `convert`: 71/71 green. `test_manager_converts` asserts only "did not raise", so a manager could silently end up owning work, load, and forecast. Code is correct.
5. **`advance` by a manager to `won`/`lost` frees the *owner's* slot.** Mutant `self._free(actor)`: 71/71 green — the only manager-actor `lost` test (`test_lost_from_any`) has an empty queue, so the freed slot is never observed. Related: the `("advance", opp_id, actor)` log entry is only asserted when actor == owner, so a manager actor is never checked in the log. Code is correct.
6. **`transfer`'s capacity check is against the new owner's load.** Mutant `self._load(o["owner"]) >= capacity(new_owner)`: 71/71 green. `test_capacity` passes for the wrong reason — the old owner's load (1) happens to equal the target's capacity (1), so both the correct and the broken check raise. A case with a target that has room is required (probe in §2.3 passes). Code is correct.
7. **A failed `convert` must not consume an `O<n>`.** No test at all (the analogous `L<n>` rule is tested by `test_failed_add_does_not_consume_id`). Code is correct.
8. **`transfer` frees the previous owner's slot** (spec line 39). Mutant `self._free(old)` → `pass`: 71/71 green. Structurally unreachable through the public API (§2.1), so this is a coverage hole that cannot be closed without a seam — or the rule is redundant and should be struck from the spec.

Weak tests, as opposed to missing ones:

9. **`test_pct_above_30_rejected_even_when_floor_allows` has a false premise.** At `amount=100000, pct=31` the floor also fails (69,000 < 70,000), so the pct ≤ 30 bound is never isolated; widening it to 31 keeps the suite green. For every reachable state the bound is redundant with the floor, so the test's name asserts something it cannot show.
10. **`test_domain_edge_dots` over-asserts relative to the spec** (§4.7): it pins the strict reading of a sentence that literally allows both cases it rejects.
11. **`test_capacity` (transfer) is the wrong-reason pass in entry 6** — worth restating because it is the only capacity test for `transfer`.

No test asserts anything about internals that the spec does not define (`leads`, `opps`, `log` only), and no test documents behaviour contrary to the spec except entry 10.

VERDICT: APPROVED
