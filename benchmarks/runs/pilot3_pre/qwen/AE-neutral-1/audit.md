# Audit: AE-neutral-1 vs specs/crm.md

- Auditor re-run of the delivery at `/tmp/aep-lab/pilot3/qwen/AE-neutral-1`
  (`crm.py`, `test_crm_add_lead.py`, `test_crm_qualify_convert.py`,
  `test_crm_advance_discount_transfer.py`), per the auditor-executor-protocol
  (SKILL.md "Auditing" + failure-modes reference). Method: re-run, not read.
- Auditor wrote nothing into the delivery except this file; `crm.py` and the
  three test files were **not modified** (sha256 verified identical before
  and after every mutation cycle; mutation experiments ran on byte-identical
  copies under the OpenCode temp workspace, with `aepkit negcontrol`
  backup/restore, and were also verified by sha256 after each restore).
- Environment: `Python 3.14.7`
  (`/tmp/aep-lab/v060/bin/python`), run from the delivery directory and from
  an identical copy. `python -B` used everywhere to exclude stale-bytecode
  artifacts; the delivered `__pycache__` matches source mtimes and is not
  relied on.

## 1. Suites re-run

```
$ /tmp/aep-lab/v060/bin/python -B -m unittest discover        # in delivery dir
Ran 72 tests in 0.003s
OK
```

Also re-run from a byte-identical copy: 72/72 OK. No false invocation found
(right directory, right interpreter, `-B` for bytecode hygiene).

## 2. Independent verification of the implementation

Two auditor-built checks, then torn down (not part of the delivery):

1. **Targeted probes** — 11 tests asserting the exact spec orderings and edge
   values that a naive reading of the delivered suite does not pin down
   (check-order interactions, 50000/50001 boundary, cumulative floor
   `new_amount*100 >= original_amount*70`, queue FIFO, per-step side-effect
   atomicity, unhashable-actor robustness). Result: **11/11 OK** against the
   delivered `crm.py`.
2. **Differential fuzz** — a reference CRM written from `specs/crm.md` alone
   (spec-text-driven, not copied from the delivery), driven by identical
   pseudo-random op sequences (add/qualify/convert/advance/discount/transfer/
   forecast, with malformed inputs: non-str emails, bool amounts/pcts, unknown
   actors, unhashable actors, capacity-0 reps, string-order rep ids like
   `r10` vs `r2`). After every op the fuzz compares exception type, return
   value, and full state (`leads`, `opps`, `log` list contents and order).
   **3000 rounds x 24 ops: 0 mismatches.**

Code finding: **the delivered implementation is spec-correct on everything
reachable** — including the log-atomicity rule ("a failed call changes nothing
and appends nothing"), which the fuzz checks after every single operation.

## 3. Negative controls re-executed from scratch (aepkit negcontrol on the copy)

Sanity control first: `M1` rep-discount cap `pct > 10` → `pct > 11` — the
suite failed exactly on `test_rep_capped_at_10`, restored byte-identical,
re-passed. Harness credibility confirmed.

Breaks the delivered suite **catches** (guards that genuinely work, sample):
`M4` negotiation gate reading `original_amount` instead of `amount` → caught
by `test_negotiation_gate_big_deal` (it mutates `amount` only, leaving
`original_amount` distinct — good design). Crude owner-selection break `M7`
(pick `candidates[0]`) → caught incidentally by
`test_destination_at_capacity_rejected`.

Breaks the delivered suite **misses** (each survived 72/72 green; the fuzzer's
verdict shows whether a guard test is constructible):

| ID | Break | Suite | Fuzz | Constructible? |
|---|---|---|---|---|
| M5 | `_load` counts only status `"new"` (drops `"qualified"`) | SURVIVED | 4 mismatches | YES — missing guard |
| M7b | assignment tie-break = first-encountered min-load rep, not min **string** id | SURVIVED | mismatches in <40 rounds | YES — existing tie-break test is weak |
| M-order | `add_lead` steps swapped: duplicate check before source check | SURVIVED | (order-level) | YES — auditor probe errors on it |
| M8 | `class DuplicateLeadError(Exception)` → `(ValueError)` | SURVIVED | n/a | YES — missing guard |
| M2 | `_free_slot` `while` → `if` | SURVIVED | 0 mismatches | NO — unobservable (see §5) |
| M3 | `transfer` drops the previous-owner drain call | SURVIVED | 0 mismatches | NO — unreachable given check 6 (see §5) |

## 4. Recorded, not blocking (no test can exist)

- `advance`-to-final drain loop `while` vs `if` (break M2) and
  `transfer`'s previous-owner drain (break M3) are **behaviorally
  indistinguishable**: a non-empty waiting queue implies every rep is at
  capacity, so `advance` can only free one slot at a time and `transfer` can
  only succeed when the queue is empty. Confirmed by 3000-round differential
  fuzz with 0 mismatches for both breaks. The implementation matches the
  spec's text; this is a property of the spec, not a delivery defect. Noted
  so a later auditor does not count it against the Executor.
- Process note, per protocol ("separate process findings from code findings"):
  the pilot directory contains no `plan-of-record.md` / `execution-guide.md`
  / `compliance-log.md` (`aepkit lint .` errors on the missing document set),
  so there was no Executor report to audit — only the code+tests against the
  spec. Audited as such.

## 5. Verdict rationale

- Code finding: **clean** — 72/72 suite green (re-run by auditor), 11/11
  auditor probes green, 3000×24 differential fuzz vs a spec-written reference
  with zero state/log/exception mismatches.
- Guard-test finding: **four spec rules are not protected** — one weak guard
  and three missing guards (items 1–4 below) — each shown by a negative
  control that kept the delivered suite fully green while changing observable
  behavior the fuzzer/probes detect. Per the protocol, "APPROVED = every gate
  independently verified"; with a passing suite that misses its own coverage
  on constructible cases, the gate is not verified.
- Remediation for the Executor: add the four tests listed below (code needs
  no change); re-run `python -B -m unittest discover` and the four negative
  controls (M5, M7b, M-order, M8) must now fail against the mutated copy and
  pass after restore.

## 6. Missing or weak guard tests (blocking)

The delivery's tests do not pin down these spec rules; each gap admits a
plausible implementation regression that the current suite would pass green.
These must be added before sign-off (code changes are **not** required — the
implementation already satisfies every rule):

1. **Weak — assignment tie-break by string id (spec §add_lead step 6).**
   `test_crm_add_lead.py::test_tie_break_is_string_order` cannot fail a
   first-encountered-min-load implementation: with `[r10, r2]` both idle, the
   first candidate is also the string-minimum, so the assertion `"r10"` holds
   under the wrong rule too (break M7b survives 72/72; the fuzzer catches it
   in under 40 rounds). Fix: also run the **reverse** insertion order
   (`[r2, r10]`, both idle) and expect `"r10"`, and/or a tie among three ids
   where string order differs from insertion order.
2. **Missing — load counts `"qualified"` leads toward capacity (spec §General
   rules / load).** No delivered test qualifies a rep's only lead and then
   adds a second one. Break M5 (qualified leads invisible to `_load`) passes
   the whole suite; the fuzzer catches it (owner misassignment after
   qualify). Fix: rep capacity 1, `add_lead` → owned, `qualify`, next
   `add_lead` must have `owner is None` and be queued; also assert the queued
   lead is assigned by the eventual `advance`-to-final drain.
3. **Missing — `add_lead` check order: source (step 3) before duplicate
   (step 4) (spec §"first failing check decides").** No test combines an
   existing email with an invalid source. Break (swap the two checks) passes
   72/72; the auditor's probe (`assertRaises(ValueError)` for duplicate+bad
   source) errors with `DuplicateLeadError` under the swap — the guard is
   constructible and absent. Fix: `add_lead("a@x.com", "A", "phone", actor)`
   after `"a@x.com"` exists must raise `ValueError`, not
   `DuplicateLeadError`; name-vs-duplicate (`add_lead(dupe_email, 5, "web",
   …)` → `ValueError`) belongs in the same test.
4. **Missing — `DuplicateLeadError` is not a `ValueError` subclass (spec
   §1: `class DuplicateLeadError(Exception)`).** Break M8 (reparent to
   `ValueError`) passes the suite, and callers that catch validation errors
   would then silently swallow duplicates (and the spec's
   ValueError-vs-DuplicateLeadError distinction in check order collapses).
   Fix: `assertFalse(issubclass(DuplicateLeadError, ValueError))` — an
   `assertRaises(DuplicateLeadError)` on a duplicate is already present but
   cannot see the regression on its own.

VERDICT: REJECTED
