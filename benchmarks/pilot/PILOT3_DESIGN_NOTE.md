# Pilot 3 design note (written before launch)

Date: 2026-10-26. Purpose: a more robust version of Pilot 2 on the CRM module, addressing its stated limits.

## Changes relative to Pilot 2
1. Treatment comes from the protocol itself. Base prompt and pressure text are identical across arms. Arm AE receives the shipped `SKILL.md` and
   references of aepkit 0.6.0 as reading material for both Executor and Auditor, with no step-by-step procedure written by us. Arm N receives one sentence
   stating that `aepkit negcontrol` exists.
2. Budget-matched control (arm U2): a second, generic "review and improve your work" session with no protocol, to match the extra sessions that AE receives.
3. Second oracle independent of the agent's code: 78 fixed semantic mutants of the reference implementation (`exp3/fixed_mutants.py`); the primary outcome is the
   share of behavioural mutants (those the hidden suite kills; 74 of 78) failed by at least one of the agent's tests that pass on the reference implementation
   (`exp3/score3.py`). Secondary outcomes: correctness (share of the 71-test hidden suite passing on the agent's implementation) and number of valid tests.
4. Three models: DeepSeek 4.1 Flash (effort High), Qwen 3.8 Flash and GLM 5.3 Flash (their default effort; no `high` variant is exposed for them). Model is a blocking factor.
5. Auditor calibration: 3 known-good and 3 known-bad deliveries are audited with the same Auditor prompt before the main runs (DeepSeek).
6. Hidden suite strengthened (71 tests) before launch after a mutation check; four remaining unkilled fixed mutants are equivalent under the spec.

## Design
Models (3) x arms U, U2, N, AE (4) x pressure neutral/pressure (2) x 3 replicates = 72 Executor runs, plus U2 review sessions, AE Auditor sessions and one
remediation round for rejected AE deliveries. Run order within a model is shuffled with a fixed seed. Pressure text is the Pilot 1 and 2 text, unchanged.

## Pre-declared analysis (descriptive; no p-values used for conclusions)
Primary: mean fixed-mutant kill rate per arm x pressure, pooled over models and per model, with min-max ranges; and the within-model paired difference
(arm minus U) averaged over models. Secondary: correctness, valid test count, Auditor verdict rates and calibration accuracy. Exploratory: bootstrap intervals over runs.
No prompt edits after launch except to repair infrastructure faults, each logged in `PILOT3_DEVIATIONS.md`.
