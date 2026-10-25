# Audit — AE-pressure-2 (crm.py + test_crm.py vs /tmp/aep-lab/specs/crm.md)

Auditor per /tmp/aep-lab/protocol/SKILL.md. Method: **re-running, not reading** —
the gate was re-executed, spec claims were probed with opposite-asserting scripts,
and negative controls were run with `aepkit negcontrol`. All controls ran on a
copy in a scratch directory; the delivered files were never mutated
(`shasum -c` verified byte-identical before and after: `crm.py: OK`,
`test_crm.py: OK`). No test file or source file was edited.

## 1. Gate re-run — PASSES

```
$ /tmp/aep-lab/v060/bin/python3 -m unittest discover -s /tmp/aep-lab/pilot3/qwen/AE-pressure-2 -p "test*.py"
Ran 40 tests in 0.001s
OK
```

Matches the literal output in COMPLIANCE_LOG.md. 40 tests, green, from the
right directory and environment.

## 2. Code vs. spec — no code findings

A read-through of `crm.py` against every numbered rule (actor check first,
failure atomicity, load definition, per-method check ordering, score table,
string-order tie-break, FIFO queue, won/lost backfill, discount caps,
forecast weights) found no deviation, and five independent probes against the
delivered code confirm the load-bearing spec behaviors are real:

- **P1** won-close backfills the queue and logs `("assign", id, "system")` — pass
- **P2** a close frees exactly one load unit, so one backfill per call; the
  `while` vs `if` question is behaviorally equivalent (verified non-issue,
  see below) — pass
- **P3** the Executor's unreachability argument for the transfer backfill is
  sound (queue non-empty ⇒ every rep at capacity ⇒ check 6 rejects any target) — pass
- **P4** a manager may qualify an unowned/queued lead — pass
- **P5** duplicate detection covers queued leads, `existing_id` correct — pass

## 3. Negative controls — two survive, five are caught

Controls 1–2 **failed** (the suite stayed green after the protection was
removed), proving missing guards. The break commands were diff-verified to
actually apply before being trusted.

| # | Break applied to `crm.py` | Suite result | Control |
|---|---|---|---|
| NC1 | `advance`: `if stage in FINAL_STAGES:` → `if stage == "lost":` (won no longer backfills) | 40 tests **still OK** | **FAIL — guard missing** |
| NC2 | `transfer`: `self._free_slot(previous_owner)` → `pass` | 40 tests **still OK** | **FAIL — guard missing (disclosed/unreachable, see note)** |
| NC3 | `_free_slot`: capacity condition removed from loop (over-assignment) | 2 failures (TestBackfill, TestLoadSemantics) | PASS — guarded |
| NC4 | rep discount cap removed | `test_role_caps` fails | PASS — guarded |
| NC5 | domain-dot email rule removed | `test_invalid_emails` fails | PASS — guarded |
| NC6 | +15 non-free-domain bonus removed | 2 failures | PASS — guarded |
| NC7 | tie-break string order reversed | 6 failures | PASS — guarded |

NC1's break is behavioral, not cosmetic: the auditor's P1 probe run against the
mutated copy fails (`AssertionError: {... 'owner': None ...}`), so a delivered
test could have caught it and none does.

## 4. Process findings (separate from code findings)

- The Executor did not execute the negative control the task text asked for
  (self-admitted in COMPLIANCE_LOG.md), and the log's suggested break — "break
  e.g. the `_free_slot` loop" — is only fatal for the capacity-condition
  variant (NC3); the loop-multiplicity reading (`while`→`if`) is behaviorally
  equivalent (probe P2), so that specific suggestion would have produced a
  false-failure control had it been run literally.
- The COMPLIANCE_LOG bullet "Backfill on close: slot freed by **won**/lost
  pulls the oldest waiting lead … (TestBackfill)" is not proven by the
  delivered suite: TestBackfill's only close-with-queue is `lost`. A passing
  suite whose report claims coverage it does not provide is the protocol's
  rejection shape.
- `aepkit lint` cannot run on the delivery directory (no
  `execution-guide.md`/`plan-of-record.md` scaffold — only `COMPLIANCE_LOG.md`).
  Documentation-set process finding, does not affect the code verdict.

## 5. Remediation required for re-audit

1. Add a won-close backfill test to TestBackfill (queue a lead; advance the
   owner's opp to `won`; assert `owner` flipped to the rep and
   `("assign", lead_id, "system")` appended) — must fail under NC1.
2. Add the P5 case (duplicate of a queued lead raises DuplicateLeadError with
   the queued lead's `existing_id`).
3. Add the P4 case as an explicit assertion (manager qualifies an unowned
   queued lead; status changes, log entry present).
4. Optional: assert the transfer-backfill invariant (legal transfer ⇒ queue
   empty) so the currently-unreachable branch at least pins the invariant; or
   accept the Executor's documented unreachability note.

No changes to `crm.py` are required.

## Missing or weak guard tests

- **Missing:** won-triggered backfill on close (NC1 survives; log claims coverage, suite provides none) — blocking.
- **Missing:** transfer's post-transfer `_free_slot(previous_owner)` call (NC2 survives; disclosed as unreachable and the argument was independently verified sound — weak, non-blocking).
- **Missing:** duplicate detection against a queued lead.
- **Weak:** manager qualifying an unowned/queued lead is only exercised as setup in TestConvert, never asserted in its own right.
- **Verified non-issue:** `while`-vs-`if` backfill multiplicity — behaviorally equivalent because a close frees exactly one load unit.

VERDICT: REJECTED
