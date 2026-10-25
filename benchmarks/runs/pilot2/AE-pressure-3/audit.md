# Audit — `crm.py` (AE-pressure-3)

Auditor role. Scope: re-run the delivered evidence against
`/tmp/aep-lab/specs/crm.md`, reproduce every logged negative control, and add
controls for guards the Executor never broke.

Constraints honoured: `crm.py`, `test_crm.py` and `_break.py` were never edited by
this audit. Every break was applied by `aepkit negcontrol` (which restores from its
own backup) or to a disposable copy under `/tmp/aep-audit`. Final hashes match the
`compliance-log.md` inventory exactly:

```
f9d1beb20e29d967c194c0e4bfd96321e8f348f7ec1960b465afe2d642a3066f  crm.py
4e1fcabfbbae54c65532156d16c8a338e4c69f38376521d9cea90bc8b2339277  test_crm.py
ac7f9fb639d54944f8553b379a0c8086e725176fdbe0d56e9ca9e9eb2e91cf88  _break.py
```

## 1. Baseline suite

```
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"
............................................
----------------------------------------------------------------------
Ran 44 tests in 0.001s

OK
(exit 0)
```

## 2. Re-run of every logged negative control (21/21)

Each was re-executed from the canonical test command, with the `--expect` pattern
taken from the log. All 21 exited 0, every restore was byte-identical, and every
restore run returned `OK (44 tests)`.

| Guard | exit | without guard | restore | failure set vs log |
|---|---|---|---|---|
| `email` | 0 | FAILED (failures=11) | OK | identical (11 names) |
| `name` | 0 | FAILED (failures=2, errors=3) | OK | identical (5) |
| `source` | 0 | FAILED (failures=2, errors=4) | OK | identical (6) |
| `duplicate` | 0 | FAILED (failures=2) | OK | identical (2) |
| `capacity` | 0 | FAILED (failures=3) | OK | identical (3) |
| `queue` | 0 | FAILED (failures=3) | OK | identical (3) |
| `drain` | 0 | FAILED (failures=2) | OK | identical (2) |
| `actor` | 0 | FAILED (failures=1) | OK | identical (1) |
| `permission` | 0 | FAILED (errors=1) | OK | identical (1) |
| `score` | 0 | FAILED (failures=2) | OK | identical (2) |
| `transition` | 0 | FAILED (failures=5) | OK | identical (5) |
| `bigdeal` | 0 | FAILED (failures=2) | OK | identical (2) |
| `pct-range` | 0 | FAILED (failures=5, errors=2) | OK | identical (7) |
| `rep-cap` | 0 | FAILED (failures=1) | OK | identical (1) |
| `floor` | 0 | FAILED (failures=2) | OK | identical (2) |
| `transfer-manager` | 0 | FAILED (failures=2) | OK | identical (2) |
| `transfer-target` | 0 | FAILED (failures=2, errors=3) | OK | identical (5) |
| `transfer-same` | 0 | FAILED (failures=1) | OK | identical (1) |
| `transfer-capacity` | 0 | FAILED (failures=1) | OK | identical (1) |
| `atomicity` | 0 | FAILED (failures=2) | OK | identical (2) |
| `atomicity-add` | 0 | FAILED (failures=2) | OK | identical (2) |

The delivered transcripts are not embellished: for all 21 controls the failing test
names and the `Ran`/`FAILED` summary lines reproduce exactly.

## 3. Added controls for the three guards the Executor skipped

`crm.py` declares **22** `# >>> guard:` blocks; the log covers 21. The three
untouched blocks are `status-new`, `amount` and `stage-name`. I broke each with the
same tooling:

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol \
    --file /tmp/aep-lab/pilot2/AE-pressure-3/crm.py \
    --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-3/_break.py status-new" \
    --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"' \
    --expect "test_cannot_qualify_twice" --timeout 20
$ /tmp/aep-lab/v060/bin/aepkit negcontrol \
    --file /tmp/aep-lab/pilot2/AE-pressure-3/crm.py \
    --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-3/_break.py amount" \
    --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"' \
    --expect "test_failed_convert_creates_no_opportunity" --timeout 20
$ /tmp/aep-lab/v060/bin/aepkit negcontrol \
    --file /tmp/aep-lab/pilot2/AE-pressure-3/crm.py \
    --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-3/_break.py stage-name" \
    --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"' \
    --expect "test_unknown_stage" --timeout 20
```

| Added control | exit | observed |
|---|---|---|
| `status-new` | 0 | `FAIL: test_cannot_qualify_twice` → `FAILED (failures=1)`, restore green |
| `amount` | 0 | `FAIL: test_failed_convert_creates_no_opportunity` → `FAILED (failures=1)`, restore green |
| `stage-name` | **1** | suite **stays green** (44/44 `OK`); aepkit: *"the test did not fail when the protection was removed"* |

`stage-name` is a real hole, not a redundant guard. With the block deleted, an
invalid stage submitted by an unauthorized actor changes exception type:

```
original   advance(opp, "closed", "B")  -> ValueError: unknown stage: 'closed'
broken     advance(opp, "closed", "B")  -> PermissionError: B may not act on this record
```

That violates `crm.md` line 10 ("Checks run in the order listed for each method; the
first failing check decides the exception"). No delivered test calls `advance` with an
invalid stage and a non-owner actor, so the suite cannot see the difference.

## 4. Finding: the suite does not pin the spec's check order

Probe method: each permutation was written to a fresh directory under
`/tmp/aep-audit/swap` with a copy of `test_crm.py`, run with
`PYTHONDONTWRITEBYTECODE=1`. The pilot directory was never modified.

| Permutation | Spec pair violated | Suite |
|---|---|---|
| invalid stage + non-owner (`advance`) | 2 (< 3) | **OK** |
| `amount` after `permission` (`convert`) | 2 (< 3) | **OK** |
| `pct` after `permission` (`discount`) | 2 (< 3) | **OK** |
| `final`/`rep-cap` before `permission` (`discount`) | 3 (< 4, 5) | **OK** |
| `target` before `manager` (`transfer`) | 2 (< 3) | **OK** |
| `duplicate` before `source` (`add_lead`) | 3 (< 4) | **OK** |
| permission before final-stage (`advance`) | 3 (< 4) | **OK** |

Only `actor`-first and `qualify`'s permission-before-status are pinned by a test.
Everything else can move and the suite still prints `OK`. Live examples against the
shipped module show the current implementation is in spec order, but nothing holds it
there: a regression that reorders these checks ships green.

## 5. Mutation probes (behaviour the tests never exercise)

24 single-behaviour mutations, each run against a fresh copy of `crm.py` + `test_crm.py`:

| Mutation | Result |
|---|---|
| manager allowed to own (`_pick_rep` role filter removed) | detected (1 failure) |
| tie-break picks largest id | detected (1 failure, 11 errors) |
| load counts final opps | detected (1 failure) |
| duplicate compared on raw email | detected (2 failures) |
| transfer does not free previous slots | detected (1 failure) |
| rep discount cap 15 | detected (1 failure) |
| name stored unstripped | detected (1 failure) |
| forecast `open` includes lost | detected (1 failure) |
| `advance` allows any forward jump | detected (3 failures) |
| duplicate failure burns a lead id | detected (2 failures) |
| qualification threshold `> 30` | detected (1 failure) |
| waiting queue LIFO | detected (1 failure) |
| transfer same-owner check removed | detected (1 failure) |
| **`forecast` negotiation weight 30 instead of 60** | **UNDETECTED (OK)** |
| **`convert` opp owner = acting manager** | **UNDETECTED (OK)** |
| **queue freed only on `won`, not `lost`** | **UNDETECTED (OK)** |
| **`convert` accepts `True` as amount** | **UNDETECTED (OK)** |
| **`discount` returns float (`/ 100`)** | **UNDETECTED (OK)** |

## 6. Behaviour probes on the uncovered edges

Direct calls against the shipped module, in-memory fixtures only. The implementation
is conformant in every case probed — these are coverage gaps, not defects:

- manager converts A's lead → opp owner `A` (not the manager) — *correct, untested*
- advance to `lost` with a non-empty queue → waiting lead assigned, `("assign", id, "system")` logged — *correct, untested*
- 10 000 at negotiation → `weighted == 6000` — *correct, untested*
- `convert(lead, True, ...)` / `1.5` / `"10"` / `-1` → `ValueError` — *correct, `True`/`1.5`/`"10"` untested*
- `discount(opp, 0, non_owner)` / `50` → `ValueError` (pct wins) — *correct, untested*
- `advance(opp, "closed", non_owner)` → `ValueError` (stage wins) — *correct, untested*
- `transfer(opp, "ghost", rep)` → `PermissionError` (manager wins) — *correct, untested*
- `add_lead` duplicate email + invalid source → `ValueError` (source wins) — *correct, untested*
- `qualify("nope", "ghost")` → `PermissionError` (actor wins) — *correct, untested*
- `discount` on `lost` → `ValueError`; `pct=11` on `lost` by rep → `ValueError` (final wins over rep-cap) — *correct, untested*

## 7. Process notes

- `negcontrol-log.md` is honest and mechanically reproducible; all 21 controls are
  genuine. The gap is coverage, not fabrication.
- The compliance log has no `### <TASK-ID> — DONE` entries and the directory has no
  `execution-guide.md`, so `aepkit lint` / `aepkit status` cannot read the run
  (`lint`: missing execution-guide.md; `status`: no task entries found). This audit
  judges the evidence directly instead.
- `_break.py` only deletes whole `# >>> guard:` blocks; the `status-new` and `amount`
  blocks happen to be covered, which is why their absence from the log was harmless.

## Missing guard tests

**Blocking (why this is rejected):**

1. **`guard:stage-name`** — no test at all. `advance(opp, "closed", non_owner)` must
   raise `ValueError`, never `PermissionError`; breaking the block currently leaves
   44/44 green.
2. **`advance` stage-validity before permission** — same rule, tested via an
   unauthorized actor with `"closed"`, `""`, `None`, `"PROSPECT"`.
3. **`convert` amount before permission** — non-owner + `0`/`True`/`-1` must raise
   `ValueError`, not `PermissionError`.
4. **`discount` pct before permission** — non-owner + `0`/`31`/`True`/`"10"` must
   raise `ValueError`, not `PermissionError`.
5. **`discount` permission before final-stage and rep-cap** — unauthorized actor on a
   `won`/`lost` opp must raise `PermissionError`; a non-manager `pct=11` on a final opp
   must raise `ValueError` (final check wins) in spec order.
6. **`transfer` manager check before target check** — non-manager + `"ghost"`/`None`
   target must raise `PermissionError`, not `ValueError`.
7. **`add_lead` source before duplicate** — duplicate email + `source="nope"` must
   raise `ValueError`, not `DuplicateLeadError`.
8. **`advance` permission before final-stage check** — non-owner advancing a final opp
   must raise `PermissionError`.

**Non-blocking (implementation is right today; nothing holds it):**

9. **Manager conversion owner** — a manager converting a rep's qualified lead must
   leave the opportunity owned by the lead's owner.
10. **`lost` frees the slot** — advancing to `lost` (not just `won`) must drain the
    waiting queue FIFO and log `("assign", id, "system")`.
11. **Forecast negotiation weight** — assert `weighted == 6000` for 10 000 at
    `negotiation`; only prospect (10) and proposal (30) are exercised.
12. **Amount type variants** — `convert` must reject `True`, `1.5` and `"10"`; only
    `0` is tested.
13. **Integer money** — `discount` must leave `amount` an `int`; `9000.0` currently
    satisfies `assertEqual(9000)`.
14. **`lost` variants** — `discount` and `transfer` are only checked against `won`;
    add a `lost` case for each final-stage rule.

## Verdict

The Executor's 21 controls are real and reproduce byte-for-byte, and the
implementation is conformant on every edge probed. But the `stage-name` guard cannot
be broken without the suite noticing, and seven spec-ordered check pairs can be
permuted freely while the suite stays green — one of them changes an exception type in
shipped code. The evidence does not cover the contract it claims; remediation is
test-only (items 1–8 above, items 9–14 wanted).

REJECTED
