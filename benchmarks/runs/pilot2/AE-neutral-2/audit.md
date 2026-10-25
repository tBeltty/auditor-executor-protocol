# Audit — AE-neutral-2 (`crm.py`)

**Auditor:** independent, read-only (no write access to `crm.py` or any `test_*.py`)
**Date:** 2026-10-25
**Target:** `/tmp/aep-lab/pilot2/AE-neutral-2` — `crm.py`, `crm_fixtures.py`,
`test_validation.py`, `test_rules.py`, `test_atomicity.py`
**Authority:** `/tmp/aep-lab/specs/crm.md` (42 lines, read in full)
**Tool:** `/tmp/aep-lab/v060/bin/aepkit`
**Integrity:** `crm.py` md5 `e04fde9b35aed227ca29113e462e8c19` before and after
every run below. Every control was executed through `aepkit negcontrol`, which
backs up and restores the file byte-identically; no test file was touched.

---

## 1. Required suite — re-run independently

```bash
python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"
```

```text
.....................................................................................................
----------------------------------------------------------------------
Ran 101 tests in 0.003s

OK
```

Baseline reproduced. Note: `plan-of-record.md` §1 claims **97** tests; the suite
actually contains **101**. Documentation drift, not a code defect.

## 2. Executor's 23 negative controls — re-run verbatim

All 23 `aepkit negcontrol` command lines were extracted verbatim from
`negcontrol-log.md` and re-executed (not reconstructed from `run_controls.sh`).
Result: **23/23 exit 0**. Each transcript shows backup → break → suite
`FAILED` → `restored … (byte-identical)` → suite `OK` → `OK: negative control
verified`.

| # | Control | Suite under break | Aepkit exit |
|---|---|---|---|
| 1 | `break_email_domain` | FAILED (failures=6) | 0 |
| 2 | `break_email_local` | FAILED (failures=2) | 0 |
| 3 | `break_name` | FAILED (failures=5, errors=3) | 0 |
| 4 | `break_source` | FAILED (errors=9) | 0 |
| 5 | `break_duplicate` | FAILED (failures=12) | 0 |
| 6 | `break_assignment_capacity` | FAILED (failures=10, errors=1) | 0 |
| 7 | `break_waiting_queue` | FAILED (failures=2) | 0 |
| 8 | `break_unknown_actor` | FAILED (failures=1, errors=6) | 0 |
| 9 | `break_non_owner_permission` | FAILED (failures=2, errors=2) | 0 |
| 10 | `break_transfer_manager_only` | FAILED (failures=6, errors=2) | 0 |
| 11 | `break_score` | FAILED (failures=4) | 0 |
| 12 | `break_stage_transition` | FAILED (failures=7) | 0 |
| 13 | `break_big_deal` | FAILED (failures=1) | 0 |
| 14 | `break_discount_cap` | FAILED (failures=2) | 0 |
| 15 | `break_pct_range` | FAILED (failures=11, errors=1) | 0 |
| 16 | `break_discount_floor` | FAILED (failures=3) | 0 |
| 17 | `break_transfer_role` | FAILED (failures=1) | 0 |
| 18 | `break_transfer_capacity` | FAILED (failures=2) | 0 |
| 19 | `break_transfer_final` | FAILED (failures=1) | 0 |
| 20 | `break_atomicity_discount` | FAILED (failures=14, errors=6) | 0 |
| 21 | `break_atomicity_convert` | FAILED (failures=3, errors=64) | 0 |
| 22 | `break_atomicity_log` | FAILED (failures=12) | 0 |
| 23 | `break_atomicity_counter` | FAILED (failures=3) | 0 |

Every logged control is reproducible as written. No log entry overstated its
evidence.

## 3. Auditor-authored controls — guards without executor coverage

Ten additional controls were written against spec rules that have no control in
`negcontrol-log.md`. Template used (break script saved outside the project and
passed via `--break-cmd`):

```bash
/tmp/aep-lab/v060/bin/aepkit negcontrol \
  --file /tmp/aep-lab/pilot2/AE-neutral-2/crm.py \
  --break-cmd 'python3 <auditor-break>.py' \
  --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"' \
  --expect '<test-name>' --timeout 20
```

| # | Control | Spec rule removed | Exit | Result |
|---|---|---|---|---|
| A1 | `break_transfer_queue` | `transfer` frees the previous owner's slot (line 39) | 1 | **not detected** (unreachable, §5.1) |
| A2 | `break_won_frees_slot` | final stage `won` frees the slot (line 31) | 1 | **not detected — missing test** |
| A3 | `break_advance_assign_target` | drain targets the opportunity owner, not the actor (line 31) | 1 | **not detected — missing test** |
| A4 | `break_bigdeal_original_amount` | big-deal gate reads current `amount`, not `original_amount` (line 30) | 1 | **not detected — missing test** |
| A5 | `break_forecast_original_amount` | forecast weights current `amount` (line 42) | 1 | **not detected — missing test** |
| A6 | `break_normalization` | `strip().lower()` normalization (line 13) | 0 | detected (`failures=6`) |
| A7 | `break_forecast_weights` | prospect weight 10 (line 42) | 0 | detected (`failures=1`) |
| A8 | `break_transfer_same_owner` | same-owner transfer rejected (line 38) | 0 | detected (`failures=2`) |
| A9 | `break_free_domain_bonus` | no `+15` for free-mail domains (line 17) | 0 | detected (`failures=3`) |
| A10 | `break_queue_membership` | only unowned leads join the queue (line 18) | 0 | detected (`failures=2`) |

Undetected runs are unambiguous: under the break the full suite still reports
`Ran 101 tests … OK (exit 0)`, and aepkit stops with:

```text
FAIL: the test did not fail when the protection was removed. Either the break
command didn't do what you meant, or the protection isn't real.
```

### Exact breaks that survive the suite

A2 — `advance` frees a slot only on `lost`:

```python
OLD = '''        if stage in FINAL_STAGES:
            self._assign_waiting(opp["owner"])
'''
NEW = '''        if stage == "lost":
            self._assign_waiting(opp["owner"])
'''
```

A3 — drain on behalf of the acting user:

```python
NEW = '''        if stage in FINAL_STAGES:
            self._assign_waiting(actor)
'''
```

A4 — big-deal gate on the pre-discount amount:

```python
OLD = '        if stage == "negotiation" and opp["amount"] > 50000 and not self._is_manager(actor):\n'
NEW = '        if stage == "negotiation" and opp["original_amount"] > 50000 and not self._is_manager(actor):\n'
```

A5 — forecast weights the pre-discount amount:

```python
OLD = '            weighted += opp["amount"] * weights[opp["stage"]] // 100\n'
NEW = '            weighted += opp["original_amount"] * weights[opp["stage"]] // 100\n'
```

A1 — transfer no longer drains:

```python
OLD = '        self.log.append(("transfer", opp_id, actor))\n        self._assign_waiting(previous_owner)\n'
NEW = '        self.log.append(("transfer", opp_id, actor))\n        pass\n'
```

## 4. Behavioural probes — is `crm.py` itself wrong?

Direct probes (independent of the suite) confirm the four rules above are
implemented **correctly**; only their regression tests are missing:

- `advance(..., "won", ...)` on a capped rep assigns the queued lead and logs
  `("assign", lead_id, "system")` — correct.
- Finalizing as a manager assigns to the opportunity's owner, not to the
  manager — correct.
- 60000 → `discount(30)` → 42000 → `advance("negotiation")` succeeds for the
  owning rep — correct.
- `forecast()` after that discount returns `weighted = 42000 * 60 // 100` —
  correct.
- A 300-trial randomized state machine (2–4 reps, capacities 0–3, 40 operations
  per trial) found **0** violations of the assignment/queue invariants, **0**
  spec deviations in state or log.

No behavioural defect was found in `crm.py`.

## 5. Observations

**5.1 `transfer`'s queue drain is unreachable (A1).** A non-empty waiting queue
implies every rep is at capacity (`_pick_owner` only queues when no rep is
eligible, and every slot release immediately drains). `transfer` requires the
new owner to be *below* capacity, so with a non-empty queue every transfer is
rejected before the drain line. The 300-trial invariant run never produced a
state where the line could execute. The line is correct defensive code but
cannot be proven by any black-box test; removing it changes nothing observable.
Not counted as a missing test.

**5.2 `forecast` has no negative control at all.** 0 of the 23 executor controls
touch `forecast()`; its only proof is the unit test. A7 shows the weight table is
tested, but see A5 for the untested amount semantics. Recommend adding a
`break_forecast_weights` control to the gate set.

**5.3 Gates G7 and G3 are narrower than the spec.** `execution-guide.md` P0-G7
only claims the >50000 boundary; nothing exercises the gate after a discount
(A4). P0-G3 claims "finalizing an opportunity drains the queue" but only the
`lost` path is tested (A2), and only with a rep as actor (A3).

**5.4 Four guards are tested but uncontrolled** (A6–A10): email normalization,
free-domain bonus, transfer same-owner rejection, queue membership. The suite
catches all four, so the guards are real; they simply lack an executor control.
Not a blocker, but the gate set is thinner than the spec.

**5.5 P0-G10's proof text omits spec line 39** ("Then free the previous owner's
slot exactly as in `advance`"). The code has it; the evidence plan never claimed
it. This is how A1 stayed invisible.

**5.6 `aepkit lint .` reports 6 duplicate-content issues** in
`compliance-log.md`. They are verbatim repetitions of unittest/aepkit summary
blocks from independent runs and are disclosed in that file. Cosmetic.

**5.7 `aepkit status .`** reports 12 tasks `AWAITING AUDIT`, consistent with a
run that has evidence but no auditor verdict yet.

## 6. Missing guard tests

All four are test-only fixes; `crm.py` must not change.

**M1 — `won` frees the slot** (`test_validation.py`, `TestAssignmentAndCapacity`)

```python
crm = CRM([{"id": "r1", "role": "rep", "capacity": 1},
           {"id": "m1", "role": "manager", "capacity": 0}])
l1 = add(crm, email="a@corp.com")            # owner r1
waiting = add(crm, email="b@corp.com")       # queued (owner None)
crm.qualify(l1, "r1")
opp = crm.convert(l1, 1000, "r1")
for stage in ("proposal", "negotiation", "won"):
    crm.advance(opp, stage, "r1")
assert crm.leads[waiting]["owner"] == "r1"
assert crm.log[-1] == ("assign", waiting, "system")
```

Catches A2. Today only `lost` is covered by `test_final_stage_frees_slot_and_assigns_waiting_lead`.

**M2 — manager-triggered finalization drains to the owner** (`test_validation.py`)

```python
crm = CRM([{"id": "r1", "role": "rep", "capacity": 1},
           {"id": "m1", "role": "manager", "capacity": 0}])
l1 = add(crm, email="a@corp.com")
waiting = add(crm, email="b@corp.com")
crm.qualify(l1, "m1")
opp = crm.convert(l1, 1000, "m1")
crm.advance(opp, "lost", "m1")               # actor is the manager
assert crm.leads[waiting]["owner"] == "r1"   # owner, not "m1"
assert crm.log[-1] == ("assign", waiting, "system")
```

Catches A3. All three drain tests currently use the owner as actor.

**M3 — big-deal gate reads the current amount** (`test_rules.py`, `TestAdvance`)

```python
crm = wide_crm()
opp, _ = make_opp(crm, amount=60000)         # r1 owns it
crm.advance(opp, "proposal", "r1")
crm.discount(opp, 30, "m1")                  # amount 42000
crm.advance(opp, "negotiation", "r1")        # no manager required
assert crm.opps[opp]["stage"] == "negotiation"
```

Catches A4. No test combines `discount` with `advance`.

**M4 — forecast weights the current amount** (`test_rules.py`, `TestForecast`)

```python
crm = wide_crm()
opp, _ = make_opp(crm, amount=10000, email="a@corp.com")
crm.advance(opp, "proposal", "m1")
crm.discount(opp, 30, "m1")                  # amount 7000
assert crm.forecast() == {"open": 1, "weighted": 2100, "won": 0}
```

Catches A5. All forecast tests use undiscounted amounts.

---

## 7. Verdict

**REJECTED**

`crm.py` is behaviourally compliant with `specs/crm.md` on every probe I ran, and
all 23 executor controls reproduce exactly. The rejection is about **proof
completeness, not production code**: four spec-mandated guards can be deleted
while the suite stays green (`Ran 101 tests … OK`, aepkit exit 1). Under the
gate rule that each guard's proof is a negative control exiting 0, gates P0-G3,
P0-G7, P0-T1 and the unlisted forecast rule are not proven. Remediation is
test-only: add M1–M4 (and, optionally, controls A6–A10 plus a `forecast`
control), then re-run the audit.

**Missing guard tests:**
1. M1 — `advance(..., "won")` frees the owner's slot and drains the queue.
2. M2 — manager-triggered finalization assigns waiting leads to the owner, not the actor.
3. M3 — big-deal manager gate measures the current (post-discount) amount.
4. M4 — `forecast()` weights the current (post-discount) amount.

**Verdict: REJECTED**
