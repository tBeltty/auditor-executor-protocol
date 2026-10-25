ROLE: Executor, reporting on the delivered task (`crm.py` + unit tests).

STATUS: DONE. No execution guide or compliance log exists in this directory, so
the evidence is recorded here rather than in a pre-generated log section.

Verify results (literal):

```
$ cd /tmp/aep-lab/pilot3/deepseek/AE-neutral-1
$ python3 --version
Python 3.14.7
$ python3 -m unittest discover -s /tmp/aep-lab/pilot3/deepseek/AE-neutral-1 -p "test*.py"
.........................................................................................................
----------------------------------------------------------------------
Ran 105 tests in 0.004s

OK
```

Standard library only (`unittest`, `copy`); no network, no third-party imports,
`crm.py` imports nothing at all.

Negative controls (run with `aepkit negcontrol`; each file restored
byte-identical and the suite green afterward):

1. Removed the cumulative-discount protection
   (`MIN_REMAINING_PERCENT = 70` -> `60`).
   Failing run matched `ValueError not raised`:
   `test_cumulative_discount_capped_at_30_percent` —
   `AssertionError: ValueError not raised`. Green after restore.
2. Removed the management-approval threshold
   (`NEGOTIATION_MANAGER_AMOUNT = 50000` -> `500000`).
   Failing run matched `PermissionError not raised`:
   `test_negotiation_above_50000_needs_manager`. Green after restore.
3. Removed the transfer capacity guard
   (`if self._load(new_owner) >= new_user["capacity"]:` -> `if False and ...`).
   Failing run matched `ValueError not raised`:
   `test_new_owner_at_capacity_rejected`. Green after restore.

Delivered files:
- `crm.py` — `CRM`, `DuplicateLeadError` (with `existing_id`), per spec.
- `test_crm_leads.py` — intake validation/order, scoring, duplicate handling,
  owner selection and tie-break, FIFO queue, qualify, convert.
- `test_crm_pipeline.py` — stage machine, manager gate at negotiation > 50000,
  slot freeing and assignment on win/lost, discount ladder and cumulative cap,
  transfer rules.
- `test_crm_forecast.py` — forecast math/flooring, exact log sequence, failure
  atomicity (state deep-equal and log unchanged after 15 distinct failures).
- `test_crm_guards.py` — cross-check ordering within each method (two
  violations per call raising different exception types), load accounting that
  counts open opportunities, capacity as a strict upper bound, the negotiation
  threshold measured against the current (post-discount) amount, and duplicate
  detection for qualified/converted leads.

Re-verification note: the first four files were inherited from an earlier
attempt on this task. Every spec clause was re-checked against the code with a
throwaway probe (since deleted), the suite was re-run from scratch, and the
guard-order/load coverage above was added because the inherited suite did not
pin those orderings down. No defect was found in the inherited code.

Steps in order that the tests pin down (global actor check first, then the
numbered checks per method):
- `add_lead`: actor -> email -> name -> source -> duplicate -> id/score/owner.
- `qualify`: actor -> lead exists -> owner-or-manager -> status -> score.
- `convert`: actor -> lead exists -> amount -> owner-or-manager -> status ->
  owner present.
- `advance`: actor -> opp exists -> stage name -> owner-or-manager -> not final
  -> immediate next/lost -> manager above 50000.
- `discount`: actor -> opp exists -> pct -> owner-or-manager -> not final ->
  rep limit 10 -> cumulative 30% off original.
- `transfer`: actor -> opp exists -> manager -> new_owner is a rep -> not final
  -> different owner -> capacity.

Deviations from the task text: none.

Decisions logged (rule 6; none of these required a stop):
1. The global rule "actor is checked first in every method" is applied before
   the per-method numbered checks, including `add_lead` (so an unknown actor
   beats an invalid email/name/source/duplicate).
2. Email domain rule implemented literally: valid iff some character at index
   1..len(domain)-2 is `.` (so `a@.com`, `a@com.`, `a@b.` are rejected and
   `a@b.c` is accepted). No extra restrictions (spaces, double dots, unicode)
   were invented beyond the spec's three conditions.
3. The waiting queue has no name in the spec; kept as a private FIFO list and
   exposed only through observable behavior (`owner is None`, assignment order,
   `("assign", lead_id, "system")` log entries).
4. Discount bound uses the literal integer formula per call:
   `new_amount = amount * (100 - pct) // 100` then
   `new_amount * 100 >= original_amount * 70`; equality is allowed
   (1000 at 30% -> 700 passes; a further 1% fails).
5. The negotiation manager gate is evaluated against the current `amount`
   (after any discounts), which is what the spec's word "amount" refers to.
6. Lead/opportunity counters increment only after all checks pass, so failed
   calls never consume an id (`L<n>`, `O<n>` count successes only).
7. Duplicate detection scans all leads, including qualified and converted ones.
8. Unhashable ids/actors are treated as absent (ValueError / PermissionError),
   never as a `TypeError` leak.

Observations (not changed; outside scope):
- `aepkit negcontrol` restores the file within the same second and at the same
  byte size, so a stale `__pycache__/*.pyc` can make the post-restore test run
  report the broken behavior (Python's `.pyc` header stores second-resolution
  mtime + size). All controls above were run with `python3 -B` after clearing
  `__pycache__`, so no cached bytecode was involved.
- The spec's "after transfer, free the previous owner's slot" loop is
  implemented, but through the public API it cannot fire: a non-empty waiting
  queue implies every rep is at capacity, so no rep has spare capacity to be a
  valid `new_owner`. Implemented as specified regardless.
- The exact log order for a win/loss is `("advance", ...)` first, then one
  `("assign", ..., "system")` per waiting lead pulled, matching the spec's
  sentence order.

Stops logged: none.

Ready for: audit of the delivery.
