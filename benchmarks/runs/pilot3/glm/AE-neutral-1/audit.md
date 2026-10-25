# Audit: AE-neutral-1 (`crm.py` + `test_crm.py`) against `/tmp/aep-lab/specs/crm.md`

Auditor: independent re-run audit under the Auditor/Executor protocol
(`/tmp/aep-lab/protocol/SKILL.md`). Audit-by-re-running, not read-alone.
Delivered files were treated as read-only: every probe and mutation ran on
verified byte-identical copies in a scratch directory (hashes checked before and
after; the delivered tree is untouched, mtimes unchanged).

## 1. Re-run of the delivered suite (from a copy, then in place)

```
$ /tmp/aep-lab/v060/bin/python -m unittest test_crm -v   # both in the delivery dir and on a hash-identical copy
Ran 71 tests in 0.002s
OK
```

## 2. Independent spec-conformance probes (my own, 28 probes, no dependence on the delivered tests)

Written directly from the spec lines: add_lead normalization/validation/duplicate
ordering/id counting/scores/owner selection (string-order ties, FIFO queue,
manager-never-owns), qualify (check order incl. unknown-actor-first, score-30
boundary, ownerless leads), convert (dict shape, positive-int-not-bool amounts,
amount-before-permission order, ownerless rule, id counting), advance
(invalid/skip/backwards stages, stage-before-permission order, 50000 boundary,
lost-from-any-stage, slot freeing + FIFO assign on won/lost), discount
(validation, cap-at-10, cumulative 30% floor with exact-boundary chains
(100→90→81→79→…→71→70), kill-order between checks, floor arithmetic on odd
amounts (999→899→701)), transfer (manager-only, new_owner validation, stage and
same-owner and capacity checks and their declared order), forecast (weights,
per-opp floor, won/lost, no log entry), and the failed-calls-change-nothing rule.

```
$ /tmp/aep-lab/v060/bin/python probes.py
28 probes passed, 0 failed
```

No code findings: every probed spec behavior is implemented as specified.

## 3. Negative controls (re-executed from scratch, on copies only)

Mutation negative controls: 10 declared mutants (discount cumulative-floor
removed; negotiation threshold exclusive→inclusive; convert accepting amount 0;
LIFO queue; reversed tie-break; qualify threshold 30→10; non-manager discount
cap removed; transfer manager check removed; duplicate check removed;
unknown-actor guard removed). The delivered suite fails on every one — the
guards it claims, it actually has. Canonical `aepkit negcontrol` transcript
(neg → suite fails with the right test failing, restore is byte-identical, green again):

```
$ aepkit negcontrol --file crm.py --break-cmd 'sed ... opp["amount"] >= 50000 ...' \
    --test-cmd 'python -m unittest test_crm' --expect FAILED
$ ... ERROR: test_negotiation_exactly_50000_ok_for_rep ... FAILED ...
$ restored crm.py from backup (byte-identical)
$ Ran 71 tests ... OK (exit 0)
OK: negative control verified — the check fails without the protection and passes with it.
```

Seven further mutants probing check *ordering* and boundary/failure-atomicity
behaviors slip past the delivered suite (see §4). They are caught by my probes,
which is why they are guard-test findings and not code findings.

## 4. Missing or weak guard tests (mutant passes `test_crm.py`, spec says otherwise)

| # | Missing / weak guard | Falsifying mutant that passes the delivered suite | Spec reference |
|---|---|---|---|
| W1 | No test qualifies a lead with `score` exactly 30 | `if lead["score"] < 30:` → `<= 30` (a 30-score lead is wrongly rejected; 71/71 still OK) | qualify step 4: "score must be at least 30" |
| W2 | No test pins add_lead step 2 (name) before step 4 (duplicate) | moving the name check after the duplicate loop passes; `add_lead(existing-email, invalid-name)` must raise `ValueError`, mutant raises `DuplicateLeadError` | "Checks run in the order listed" — add_lead order 1–4 |
| W3 | No test pins convert step 2 (amount) before step 3 (permission) | swapping them passes; `convert(owned qualified lead, 0, r2)` must raise `ValueError`, mutant raises `PermissionError` | convert order 1–5 |
| W4 | No test pins advance step 2 (stage) before step 3 (permission) | swapping them passes; `advance(opp, "closed", r2)` must raise `ValueError`, mutant raises `PermissionError` | advance order 1–6 |
| W5 | No test pins discount step 2 (pct) before step 3 (permission) | swapping them passes; `discount(opp, 0, r2)` must raise `ValueError`, mutant raises `PermissionError` | discount order 1–6 |
| W6 | No test pins transfer step 2 (manager) before step 3 (new_owner) distinguisher | swapping them passes; `transfer(valid opp, "nobody", r1)` must raise `PermissionError`, mutant raises `ValueError` | transfer order 1–6 |
| W7 | No state-unchanged/log-unchanged assertion after a failed `discount` (nor after failed `convert`/`advance`/`transfer`; only `add_lead` and `qualify` are covered) | letting `discount` assign `opp["amount"] = new_amount` *before* the floor check raises passes the suite while violating "a failed call changes nothing" | General rule: "A failed call (any exception) changes nothing and appends nothing to `log`" |

Observation (not a defect): the spec-mandated "free the previous owner's slot"
in `transfer` is unreachable by construction — leads join the FIFO queue only
while every rep is at capacity, and queues drain only by refilling to
capacity — so a queued lead can never coexist with a transferable rep. The
delivered implementation keeps the call anyway and the delivered tests
document this invariant explicitly; behavior is correct either way.

Process note: the delivery directory contains no protocol document set
(`compliance-log.md` etc. is absent; `aepkit status` errors there). This audit
was scoped by the dispatch to `crm.py` + `test_crm.py` against the spec, so this
is recorded as an observation, not a gate. All audit files live in a scratch
directory; only `audit.md` was written into the delivery dir.

## 5. Verdict

The deliverable conforms to the spec: the full delivered suite re-runs green
(71/71), 28 independent spec probes all pass, every declared mutation is caught
by the delivered guards, and the canonical `aepkit` negative control verifies
end to end. No code findings; the weak guard-test list above stands as stated —
none of the seven probes found wrong delivered behavior, only under-tested
spec guarantees (an ordering or failure-atomicity regression would ship green
today). Recommend closing W1–W7 as verification hardening, not remediation of
`crm.py`.

VERDICT: APPROVED
