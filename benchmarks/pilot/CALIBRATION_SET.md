# Auditor calibration set (Pilot 3)

Purpose: check, before the main runs, that the Auditor prompt (`exp3/prompts3.py`, role `audit`) separates a strong delivery from a weak one. Six deliveries, one model (DeepSeek 4.1 Flash, `high`), the same Auditor prompt used in the main runs. Results: `results/pilot3_calibration.json`; directories: `runs/pilot3/calib/`.

Construction (all by the study author, from the reference implementation `exp2/reference/crm.py`, which was the 71-test-suite version at that time):
- `gold-1`, `gold-2`, `gold-3` (identical content, three separate audits): the reference `crm.py`, the full hidden suite as the delivery's tests (`test_crm.py`), and a `negcontrol-log.md` and `compliance-log.md` produced by running `aepkit negcontrol` for eight breaks (`dup_ignored`, `qualify_threshold_31`, `advance_bigdeal_ge`, `discount_floor_strict`, `transfer_capacity_ignored`, `advance_no_free`, `convert_no_owner_ok`, `assign_highest_load`) with the break scripts under `breaks/`. Expected verdict: APPROVED.
- `bad-1`: the reference `crm.py` with a single test; logs say negative controls were not run. Expected verdict: REJECTED.
- `bad-2`: the reference `crm.py` with only the lead-intake test class of the hidden suite; no negative controls. Expected verdict: REJECTED.
- `bad-3`: the reference `crm.py` with the lead-intake, qualification, and conversion test classes; no negative controls. Expected verdict: REJECTED.

Outcome: 3 of 3 good deliveries approved, 3 of 3 bad deliveries rejected. One Auditor session (`bad-1`) wrote its verdict but never reported completion; the driver was changed to detect that case (`pilot/PILOT3_DEVIATIONS.md`).

Limits: six items, one model, constructed cases that differ greatly in quality. The set shows that the prompt can separate extreme cases and says nothing about its accuracy on deliveries of intermediate quality, which is what the main runs contain.
