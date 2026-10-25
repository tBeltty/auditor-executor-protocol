# Audit — pilot3/calib/bad-1 (`crm.py`)

Role: **Auditor** (per `protocol/SKILL.md`). Spec: `specs/crm.md`.
Deliverables audited: `crm.py`, `test_crm.py`, `compliance-log.md`, `negcontrol-log.md`.
Nothing in the delivery was edited. Probes live in a scratch directory outside the delivery
(`$TMPDIR/opencode/probe_bad1/`) and were not shipped.

## What I ran (re-run, not read)

| Command | Result |
|---|---|
| `python -m unittest -v test_crm` (from the delivery dir) | `Ran 1 test … OK` |
| `aepkit lint .` | `error: . is missing execution-guide.md` |
| `aepkit status .` | `no task entries found in compliance-log.md` |

Two independent harnesses, both run against the delivered `crm.py` by import (no copies of the
source under audit were modified):

1. **38 targeted spec probes** — every method, every numbered check, plus check-order and
   atomicity. Result: **38/38 pass**.
2. **Differential fuzz** — my own `CRM` written from the spec, driven side by side with the
   delivery over **400 seeded runs × 60 random calls = 24,000 calls**, comparing the exception
   *type*, the return value, `leads`, `opps`, `log` and `queue` after every call. Result:
   **0 divergences**.

So the code itself survives the audit. The delivery still fails, because nothing in it proves
that, and nothing in it would catch it if the code regressed tomorrow.

## Code findings

- Every method applies the unknown-actor check first, in the right order, and every numbered
  check fires in the specified sequence (verified by supplying inputs that violate several
  rules at once and comparing the exception type to the reference model).
- Checked and matching: email normalization and validation, name/source validation, duplicate
  detection and `existing_id`, all six score outcomes, lowest-load assignment with
  smallest-id tie-break, managers never owning, FIFO waiting queue, load definition
  (`new`/`qualified` leads + non-final opps), id counters not burned by failures,
  `qualify` threshold, `convert` positive-int-not-bool, stage adjacency and the >50000
  negotiation gate, slot release + FIFO reassignment on `won`/`lost`, the 10 % rep discount
  ceiling and 30 % cumulative floor, all six `transfer` guards, and all three `forecast`
  fields.
- **Observation (not a defect):** the spec says the domain must contain a `.` "which is
  neither the first nor the last character"; read literally, `a@b.co.` and `a@.b.co` contain
  such a dot and would be valid. The delivery rejects any domain starting or ending with `.`.
  That is the sane reading, and no test or order pins the ambiguity down. Worth one clarifying
  sentence in the spec, not a rejection on its own.
- I found **no** behavioral divergence from the spec in any non-ambiguous input.

## The failure: the guard tests do not guard anything

`test_crm.py` is 5 lines: one test, one assertion, on a single happy path
(`add_lead("a@b.co","n","web","r") == "L1"`). It reads neither `owner`, nor `score`, nor
`status`, nor `log`. It never calls `qualify`, `convert`, `advance`, `discount`, `transfer`
or `forecast`.

To measure that rather than assert it, I copied the delivery to a scratch directory and ran
the delivered test against **22 deliberately defective versions** of `crm.py` (temp copies
only; the delivered files were never touched). **22 of 22 mutants survived** — the suite stays
green while the module is wrong. Among the survivors:

| Mutant (single-line defect) | Delivered suite |
|---|---|
| corporate-domain score bonus removed (+15) | green |
| per-source score weights swapped | green |
| assignment tie-break reversed (max instead of min) | green |
| capacity ignored when assigning owners | green |
| `qualify` score ≥ 30 rule deleted | green |
| `bool` accepted as a conversion amount | green |
| `advance` allows skipping stages | green |
| manager requirement for negotiation > 50000 deleted | green |
| FIFO queue becomes LIFO (`pop(0)` → `pop()`) | green |
| winning an opportunity no longer reassigns the queue | green |
| 70 % cumulative discount floor lowered to 50 % | green |
| 10 % non-manager discount ceiling deleted | green |
| a rep may `transfer` | green |
| `transfer` no longer frees the previous owner | green |
| `transfer` capacity rule deleted | green |
| `lost` opportunities counted as open in `forecast` | green |
| negotiation forecast weight changed | green |
| duplicate-email detection deleted | green |
| empty local part accepted in email | green |
| `converted` leads still counted in load | green |
| failed `qualify` still appends to `log` | green |
| unknown-actor check deleted from `advance` | green |

### Missing or weak guard tests (required remediation)

**`add_lead` — untested except id echo**
1. Email validation: no negative test for non-`str`, `""`, no `@`, double `@`, empty local part,
   dotless domain, leading/trailing dot. (M19 survives.)
2. Name validation: no test for non-`str` or whitespace-only name.
3. Source enum: no test for an invalid source, and no test that source is checked *before*
   duplicate detection.
4. Duplicate detection: no test at all — `DuplicateLeadError` and `existing_id` are never
   exercised. (M18 survives.)
5. Normalization: no test that the stored email is `strip().lower()` and the name stripped.
6. Score: no test for any of the six outcomes (web/referral/event × free/corporate domain).
   (M1, M2 survive.)
7. Assignment: no test for lowest-load selection, smallest-id tie-break, the capacity floor,
   manager exclusion, or the `None` owner + FIFO queue when every rep is full. (M3, M4 survive.)
8. Log: no test for the `("add_lead", id, actor)` entry.

**`qualify`** — untested. Missing: unknown actor, non-owner non-manager, wrong status,
score < 30, manager-overrides-owner success path, and the log entry. (M5 survives.)

**`convert`** — untested. Missing: `0`/negative/`bool`/float/str amounts, permission, status
not `qualified`, owner `None`, `"O<n>"` sequence (including that failures do not consume a
number), `original_amount == amount`, lead status `converted`, and the log entry. (M6 survives.)

**`advance`** — untested. Missing: invalid stage, permission, final-stage rejection, adjacency
(pass and skip), the >50000 negotiation gate (rep denied, manager allowed, 50000 itself
allowed), the log entry, slot release on `won` **and** on `lost`, FIFO order of `assign`
entries, `assign` logged with actor `"system"`, and that no assignment happens above
capacity. (M7, M8, M9, M10 survive.)

**`discount`** — untested. Missing: pct `0`/`31`/`-1`/`bool`/float/str, permission, final
stage, the 10 % rep ceiling (10 allowed, 11 denied), the cumulative 70 % floor at exactly 30 %
and one point past it, floor-division arithmetic, the amount left untouched on failure, and
the log entry. (M11, M12 survive.)

**`transfer`** — untested. Missing: non-manager denied, target must be an existing `rep`
(manager and unknown ids rejected), final stage, same-owner no-op, capacity rule, success
path, previous owner's slot released, and the log entry. (M13, M14, M15 survive.)

**`forecast`** — untested entirely. Missing: open count excluding `won`/`lost`, weighted sum
per stage weight, `won` total, empty-CRM zeros, and that it logs nothing. (M16, M17 survive.)

**Cross-cutting invariants — untested**
- Failed calls change nothing and append nothing to `log` (atomicity). (M21 survives.)
- Unknown actor raises `PermissionError` before any other check, in *every* method. (M22 survives.)
- `log` tuple shape and ordering across a full lifecycle.
- Check precedence when several rules are violated at once (the spec's "first failing check
  decides the exception" is never tested).

**Process**
- `negcontrol-log.md` says **"Not run."** No negative control exists, so no test in this
  delivery has ever been observed to fail. A suite that has never gone red proves nothing.
- `compliance-log.md` contains the sentence `All tests green.` — no pasted command output, no
  task or gate IDs. `aepkit lint` rejects the tree (`missing execution-guide.md`) and
  `aepkit status` finds no task entries, so per the protocol's own rule ("`DONE` with no pasted
  verify output" does not count as evidence) this is an unevidenced claim, not a report.
- There is no execution guide and no declared gate, so there is no gate this audit could pass
  even if the code is right.

## Verdict rationale

`APPROVED` means every gate was independently verified. The code was verified; there are no
gates to verify, and the single test in the delivery is also provably blind — 22 out of 22
injected defects leave it green. Accepting this would sign off an unguarded module on the
strength of one assertion, which is exactly the failure the protocol exists to prevent.

Missing or weak guard tests, in summary: no negative test for email, name, or source
validation; no duplicate/`existing_id` test; no score test; no assignment, tie-break, or
capacity test; no queue or FIFO-reassignment test; no permission test for any method; no
check-order test; no atomicity test; no `forecast` test; and no negative control at all.

VERDICT: REJECTED
