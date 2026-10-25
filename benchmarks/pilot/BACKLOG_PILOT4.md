# Backlog: Pilot 4 (start only after Pilot 3 is finished, scored and summarized)

Status: not started. Nothing here changes Pilot 3, which is running with frozen hashes (`FROZEN_HASHES_PILOT3.txt`).

## Why Pilot 4
Pilots 1 to 3 use a single module, one Executor session and one Auditor session. That exercises the protocol text and `aepkit negcontrol`, but not the
deterministic layer of `aepkit` (`init`, `lint`, `status`), which checks a document set with numbered tasks, annexes and a compliance log. Pilot 3 also cannot
separate the contribution of `negcontrol` from the contribution of independent review. Pilot 4 must close both gaps.

## Requirements
1. Multi-phase task. Split the CRM into 3 phases with gates, for example Phase 1 leads and assignment, Phase 2 qualification, conversion and stage machine,
   Phase 3 discounts, transfers and forecast. Each phase has a numbered task list and an exit gate. Later phases depend on earlier ones, so a defect in
   Phase 1 can propagate.
2. Real use of the deterministic layer. The Auditor scaffolds the document set with `aepkit init`, and `aepkit lint` and `aepkit status` are run at the end of
   every phase. Record from the transcripts whether each command was executed (not only quoted), its exit code, and what it flagged.
3. Separate the two ingredients. Arms: U (no protocol), U2 (budget-matched generic review), N (`negcontrol` only), R (independent Auditor without `negcontrol`
   and without the deterministic layer), AE (full protocol with `init`, `lint`, `status` and `negcontrol`). Compare AE with N and R to attribute the effect.
4. Measure the deterministic layer directly. Seed a fixed set of inconsistencies between the task list and the compliance log (for example a task marked done with
   no evidence, an annex over the limit, a verdict missing) and report how many `lint` and `status` catch versus how many the Auditor catches by hand.
5. Outcomes. Per phase and final: fixed-mutant kill rate against reference mutants (same method as `exp3/score3.py`, extended to the phase modules), correctness
   against the hidden suite, defect propagation across phases, count of inconsistencies detected, sessions and tokens per run.
6. Design hygiene carried over from Pilot 3. Identical base prompt across arms; the protocol is delivered as its own documents, not as procedures we write;
   a single model, DeepSeek 4.1 Flash at effort high (decision of the owner to keep the run count affordable; multi-model replication is left to Pilot 3 and to
   the full preregistered study); per-session model and variant verified from session exports; analysis pre-declared and hashes frozen before launch; idle-done detection in the driver.
7. Calibration. Auditor calibration set with known-good and known-bad deliveries for every arm that has an Auditor, plus a lint calibration set with known
   inconsistencies.
8. Mutation check of the hidden suites before launch, as done for Pilot 3, and hashes written to `FROZEN_HASHES_PILOT4.txt`.

## Decisions (delegated by the owner to the coordinator, 2026-10-26)
- Run count: start with 30 Executor runs (5 arms x 2 pressure x 3 replicates). Extend to 50 (5 replicates) only if, in Pilot 3, the within-cell standard deviation of the
  fixed-mutant kill rate exceeds half of the gap between arms. Auditor, remediation and review sessions add about 1.5 to 2 sessions per run, plus the lint calibration set.
- Pressure: keep both conditions (neutral and pressure). Pressure is what made differences visible in Pilot 2; dropping it risks returning to the ceiling.

## Paper impact
Until Pilot 4 exists, the paper must state that the study evaluates the protocol text and `aepkit negcontrol`, not the deterministic checks (`init`, `lint`, `status`),
and that the effects of `negcontrol` and of independent review are not separated.
