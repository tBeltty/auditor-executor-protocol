# Executor report — crm.py

ROLE: Executor, reporting on the `crm.py` implementation and its unit tests,
after the review of `audit.md` (verdict REJECTED).

STATUS: DONE — F1 fixed, G1–G9 addressed; all 88 unittest cases pass.

Verify results (literal output, exact command from the task):

```text
$ python3 -m unittest discover -s /tmp/aep-lab/pilot3/deepseek-rerun/AE-neutral-2 -p "test*.py"
........................................................................................
----------------------------------------------------------------------
Ran 88 tests in 0.002s

OK
```

## Remediation of the audit findings

**F1 (blocking) — email domain rule implemented literally.**
`crm.py` now accepts a domain when *some* `.` sits at an index that is neither
the first nor the last character (`any(ch == "." and 0 < i < len(domain) - 1)`),
instead of rejecting every domain that starts or ends with a dot. Direct probe:

```text
ACCEPT 'a@b.com.' -> 25
ACCEPT 'a@.b.com' -> 25
ACCEPT 'a@b.c.' -> 25
REJECT 'a@b.'
REJECT 'a@.b'
REJECT 'a@.'
REJECT 'a@.com'
REJECT 'a@com.'
```

`test_invalid_emails` no longer lists `a@b.com.` / `a@.b.com`; both moved to the
valid table, and `test_email_domain_rule_is_existential_interior_dot` asserts
the accepted set (`a@b.com.`, `a@.b.com`, `a@b.c.`, `a@b..com`, `a@b.c`) and the
rejected boundary set (`a@b.`, `a@.b`, `a@.`, `a@.com`, `a@com.`).

**G1–G8 — guard tests added (one or more per row).**
G1 as above; G2 `test_weighted_floors_each_opportunity_before_summing`
(2 prospects of 15 → `weighted == 2`); G3
`test_weighted_uses_discounted_current_amount` (1000, −10 %, → 90);
G4 `test_tie_break_is_string_order_not_numeric` (`r10` beats `r2`);
G5 `test_manager_gate_applies_only_to_negotiation` (60 000 → `lost` by its rep);
G6 `test_existence_check_precedes_manager_gate` (`transfer("O404", "nobody", "r1")`
→ `ValueError`); G7 `test_permission_precedes_final_stage_check` (non-owner rep
on a final opp → `PermissionError`); G8 `snapshot()`-based full-state assertions
on failing `add_lead` (email/name/source/duplicate) and on a non-owner
`qualify`, covering `leads`, `opps`, `log`, `waiting` and the id counters.
The white-box `crm.users["r2"] = ...` setup in
`test_transfer_frees_previous_owner_slot` is now commented as such.

**G9 — one negative control per load-bearing claim** (`aepkit negcontrol`,
each with `--file crm.py` and `--expect`; every run reported
`restored crm.py from backup (byte-identical)` and ended
`OK: negative control verified — the check fails without the protection and
passes with it.`):

| Claim removed | Test that caught it |
|---|---|
| >50 000 manager gate on `negotiation` | `test_negotiation_over_50000_needs_manager` (`PermissionError not raised`) |
| cumulative 30 % discount floor on `original_amount` | `test_cumulative_discount_cap_uses_original_amount` (`ValueError not raised`) |
| FIFO waiting-queue order (`popleft` → `pop`) | `test_assignment_stops_when_capacity_is_reached_in_fifo_order` |
| per-opportunity forecast floor | `test_weighted_floors_each_opportunity_before_summing` |
| email interior-dot rule | `test_email_domain_rule_is_existential_interior_dot` |
| slot freeing on win | `test_win_frees_slot_and_assigns_oldest_waiting_lead` |
| string tie-break (`int(id[1:])`) | `test_tie_break_is_string_order_not_numeric` |
| `transfer` existence-before-manager order | `test_manager_check_precedes_new_owner_check` (`new_owner must be a known user`) |
| `discount` permission-before-final order | `test_permission_precedes_final_stage_check` (`opportunity is already final`) |
| `add_lead` atomicity before the name check | `test_name_failure_leaves_state_untouched` |

`crm.py` was `41d4141ea425761f81c684b37dac6072047bf2b11d4042e02f884d959220c47f`
before and after the controls; the throwaway mutant injector was deleted.

Deliverables:

- `crm.py` — `CRM` and `DuplicateLeadError` per `specs/crm.md`.
- `test_crm_core.py` — actor checks, email/name/source validation, normalization,
  scoring, ids, duplicates, load balancing, capacity, FIFO queue, `add_lead`
  atomicity.
- `test_crm_workflow.py` — qualify, convert, advance, discount, transfer, slot
  freeing/queue assignment, forecast, load accounting, check ordering and
  failure atomicity.

Deviations from the task text: none.

Stops logged: none.

Ready for: re-audit of the delivery.
