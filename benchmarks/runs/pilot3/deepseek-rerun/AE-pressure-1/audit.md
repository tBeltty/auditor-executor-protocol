# Audit — AE-pressure-1 (`crm.py` against `specs/crm.md`)

**Role:** Auditor (Auditor/Executor protocol, `/tmp/aep-lab/protocol/SKILL.md`).
**Subject:** `/tmp/aep-lab/pilot3/deepseek-rerun/AE-pressure-1` — `crm.py`
(md5 `d6d604ec…`, 12:55) and `test_crm.py` (md5 `c394efa2…`, 12:56). No other files:
no compliance log, no execution guide, no declared negative control, no verify transcript.
**Environment:** Python 3.14.7, stdlib only, tests run from the delivery directory.
**Method:** re-ran everything. Nothing below is inferred from reading the code or from
the names of the delivered tests.

## 1. Delivered suite, re-run

```
$ cd /tmp/aep-lab/pilot3/deepseek-rerun/AE-pressure-1
$ python3 -m unittest -q test_crm
Ran 48 tests in 0.001s

OK
```

48/48 pass. No skips, no xfail, no network, no `pytest` dependency.

## 2. Independent probes (23, all passing)

Written against the spec text, run against the delivered module from a scratch copy:

- **add_lead** — tie-break is string order (`r10` beats `r2`); consumer-domain scoring is an
  exact match (`a@mail.gmail.com` → 25, `B@GMAIL.COM` → 10); duplicate/source/name/email
  precedence order; valid domains `a@b.c`, `a@b..c`, `a@b.c.d`; invalid `a@.com`, `a@com.`,
  `a@com`, `a@b@c.com`, `a@`, `@b.com`.
- **qualify** — actor checked before lead existence; permission before status and score;
  score exactly 30 accepted, 25 rejected.
- **convert** — amount checked before permission, permission before status; ids not consumed
  by a failed call; converted lead leaves the lead-load and adds an open opp.
- **advance** — permission before final-stage, stage value before permission; `won` above
  50 000 needs no manager, the gate only applies to the move *into* `negotiation` and uses the
  current (post-discount) amount; `lost` from `negotiation` by the owning rep; `lost` frees the
  slot and pulls the FIFO queue; non-final advance assigns nothing; a *qualified* waiting lead
  is assigned when a slot frees.
- **discount** — permission before final, final before the rep's 10 % ceiling; exactly 30 %
  cumulative allowed (1 000 → 700), one more point rejected; floor rounding (333 at 30 % →
  23 300 < 23 310 → rejected, at 29 % → 236).
- **transfer** — permission before final, target validated against live load, same-owner and
  capacity errors, lead ownership untouched.
- **forecast** — lost excluded from `open`, per-opp floor division, `won` sums only `won`,
  no actor, no log entry.
- **atomicity** — 18 distinct failing calls (one per rule) on a populated CRM, comparing
  `leads`, `opps`, `log` and the waiting queue snapshots before/after: no call mutates or logs.

## 3. Differential run against an independent reference implementation

`RefCRM` was written from the spec (different decomposition, explicit numbered checks) and
driven through randomized operation traces against the delivery, comparing after every step
the exception type, returned id, `leads`, `opps`, `log` and waiting-queue contents:

```
1500 traces × 200 operations (300 000 operations), email pool without the C1 shapes:
  mismatches = 0
same corpus including those shapes:
  4 mismatching traces — every one of them add_lead on a domain with an interior dot
  plus a leading and/or trailing dot (finding C1)
```

Every business rule — load arithmetic, owner selection, queue discipline, id sequencing,
scoring, stage graph, discount arithmetic, forecast — behaves identically to a from-scratch
reading of the spec.

## 4. Negative controls (none declared by the delivery; constructed here)

`/tmp/aep-lab/v060/bin/aepkit negcontrol`, scratch copy, backup/restore byte-identical:

| Break | Expected | Observed |
|---|---|---|
| `_waiting.popleft()` → `pop()` (FIFO) | suite fails | `AssertionError: None != 'r1'` at test_crm.py:336, restore OK |
| cumulative-discount gate removed | suite fails | 2 failures, restore OK |
| `transfer`'s `_assign_waiting(previous)` removed | suite fails | **suite green — no guard** (item 6 below) |
| `forecast` "open" counts `lost` | suite fails | **suite green — no guard** (item 7 below) |

Plus a 34-mutant matrix, one spec-violating edit per mutant: **25 killed, 9 survived**. The
nine survivors are exactly the rules in section 7.

## 5. Code findings

**C1 (minor, non-blocking) — `add_lead` email rule is stricter than the spec on one domain
shape.** Reproducer:

```
$ python3 - <<'PY'
from crm import CRM
crm = CRM([{"id": "r1", "role": "rep", "capacity": 5},
           {"id": "m1", "role": "manager", "capacity": 0}])
for email in ("a@b.c", "a@b.c.", "a@.b.c"):
    try:
        crm.add_lead(email, "x", "web", "m1")
        print("%-9s accepted" % email)
    except Exception as exc:
        print("%-9s %s: %s" % (email, type(exc).__name__, exc))
PY
a@b.c     accepted
a@b.c.    ValueError: invalid email: 'a@b.c.'
a@.b.c    ValueError: invalid email: 'a@.b.c'
```

Spec line 13 requires a domain that "contains a `.` which is neither the first nor the last
character of the domain". `b.c.` and `.b.c` satisfy that literally (the dot at index 1 / 2 is
interior) but are rejected, because `crm.py` additionally rejects any domain that starts or
ends with a dot. Seven shapes diverge: `b.c.`, `.b.c`, `.b.c.`, `b..c.`, `.b..c`, `b.c..`,
`..b.c`.

Scope of the deviation: the acceptance set is a **strict subset** of the spec's — the module
never accepts an address the spec rejects. Every rule-bearing case is correct (`a@b.com`,
`a@b.c`, `a@com`, `a@.com`, `a@com.`, `a@b@c.com` all behave as specified); the divergent
inputs are DNS-invalid addresses. Assessed as a recorded conformance nit, not a blocker: I am
not holding a correct delivery for a stricter-than-spec check on malformed input. If the
literal rule is the contract, the change is to delete the `domain.startswith(".")` /
`domain.endswith(".")` clauses and let the interior-dot test decide; nothing else moves.

**No other code findings.** Check order matches the spec in all six methods, including the
pairs the delivered suite never exercises; ids are consumed only by successful calls; the
final-stage slot release is FIFO and logs `("assign", lead_id, "system")` after the
`advance`/`transfer` entry; `original_amount` survives discounts; `forecast` uses per-opp
floor division.

**One spec clause is unreachable, and the code is harmless there.** `transfer` is required to
free the previous owner's slot "exactly as in advance". A transfer target must be below
capacity, but a non-empty waiting queue implies every rep is exactly at capacity: the only
two events that lower a rep's load (`advance` to a final stage, `transfer` away) refill the
queue immediately. Probed over 45 000 randomized operations (300 traces × 150 ops): zero
states with a non-empty queue and a rep below capacity, and no transfer with a non-empty queue
ever succeeds. The clause therefore can never fire; `_assign_waiting(previous)` is a
harmless no-op. No test can guard it through the public API.

## 6. Process findings

- **P1** — the delivery contains no compliance log, no pasted verify output and no declared
  negative control, so there is no Executor report to check claims against; the audit was run
  directly against the spec.
- **P2** — the suite does not guard nine spec rules (section 7). This is a coverage finding,
  not a latent defect: each of the nine was verified independently by probe or differential
  run, so nothing is hiding behind the gaps. A passing suite that leaves check precedence and
  `lost`-driven queue behaviour unpinned is still one refactor away from defending a
  regression.

## 7. Missing or weak guard tests

Each item names the surviving mutant (a real spec-violating edit the delivered suite does not
catch) and the test that would close it.

1. **Consumer-domain scoring is only tested for exact consumer domains** (`consumer_domain_prefix_match`).
   Changing the bonus to `endswith(".gmail.com")` survives: no test asserts that
   `a@mail.gmail.com` scores 25. *Close with:* one add on a subdomain of a consumer domain.
2. **`lost` never frees a slot** (`advance_assign_only_on_won`). Restricting the queue pull to
   `stage == "won"` survives; only `won` is exercised with a waiting queue. *Close with:* the
   `test_won_frees_slot_and_assigns_waiting_leads_fifo` scenario replayed with `lost`.
3. **`advance`: permission vs final-stage precedence untested** (`advance_perm_after_final`).
   Swapping steps 3 and 4 survives: no test calls `advance` on a final opportunity with a
   non-owner rep (must be `PermissionError`). *Close with:* one assertion pair on a `lost` opp.
4. **`advance`: stage-value vs permission precedence untested** (`advance_stage_valid_after_perm`).
   Moving the stage-validity check after the permission check survives: invalid stages are only
   attempted by a manager. *Close with:* `advance(opp, "closed", other_rep)` → `ValueError`.
5. **`discount`: permission vs final-stage precedence untested** (`discount_perm_after_final`).
   Swapping steps 3 and 4 survives. *Close with:* a non-owner rep discounting a `lost` opp →
   `PermissionError`.
6. **`transfer`'s slot release unasserted** (`transfer_no_assign`). Deleting
   `_assign_waiting(previous)` leaves 48/48 green. The clause is unreachable through the public
   API (section 5), so the honest close is either a direct unit call on `_assign_waiting` or a
   written note in the suite that the clause is dead — silently untested is worst.
7. **`forecast` with a `lost` opportunity untested** (`forecast_open_includes_lost`). Counting
   `lost` as open survives — and would then `KeyError` on `WEIGHTS["lost"]`, i.e. the suite is
   one fixture away from a crash nobody asserts. *Close with:* one scenario containing a lost
   opp, asserting `open` and `weighted`.
8. **`forecast["won"]` with a `lost` opportunity untested** (`forecast_won_includes_lost`).
   Summing `lost` into `won` survives; no test has a lost opp at all.
9. **`add_lead`: source vs duplicate precedence untested** (`add_lead_duplicate_before_source`).
   Reordering steps 3 and 4 survives, and would make a duplicate probe with a bad source raise
   `DuplicateLeadError` instead of `ValueError`. *Close with:* `add` an existing email with
   source `"phone"` → `ValueError`.
10. **The email-domain rule is not pinned at its literal boundary.** No test covers a domain
    with an interior dot *and* a leading/trailing dot; the module rejects them (finding C1),
    which the literal rule accepts. Writing that test is the decision C1 defers.

No code finding other than C1; no unmet gate other than the boundary in item 10, which is
recorded and not treated as blocking. 48/48 delivered tests, 23/23 probes, 300 000 differential
operations, 34 mutants and 4 `aepkit` controls agree that the module implements `specs/crm.md`.

VERDICT: APPROVED
