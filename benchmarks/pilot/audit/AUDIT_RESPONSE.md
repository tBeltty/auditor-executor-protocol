# Response to AUDIT_REPORT.md

Disposition of each finding. "Fixed" means changed in the repository or the manuscript; the corrected numbers were regenerated from the result files (`build_v2.py`, `pilot_text.py`).

| id | disposition | what was done |
| :-- | :-- | :-- |
| F1 | Fixed | The three non-compiling mutants were repaired, all 78 mutants now compile, and `score3.py` raises an error if the hidden suite parses zero tests. All 99 rows were rescored; originals kept (`results/pilot3_runs_original_oracle.jsonl`). See `benchmarks/pilot/PILOT3_ORACLE_CORRECTION.md`. The manuscript reports the corrected oracle and says that it was repaired after the runs. |
| F2 | Fixed | The text now says that the Auditor separated six constructed deliveries (one model) and that its verdicts did not track kill rate in the main runs (approved 0.830, rejected 0.825). |
| F3 | Fixed | Table 6 has two new rows (first session of U2 and of AE); the abstract, 4.5, 5.1, and the conclusion no longer label the arm by the Auditor and state that most of the AE gain is present before the Auditor acts. The notice to the AE Executor is reported as a limit. |
| F4 | Fixed | The 66-test suite was reconstructed by reversing the five additive edits, and its SHA-256 equals the hash frozen before Pilot 2. It is released as `exp2/hidden/test_crm_v66.py`; `exp3/rescore_pilot2.py` reproduces all 18 Pilot 2 rows exactly. |
| F5 | Fixed | A placebo contrast (U against the first session of U2, which has U's prompt) is reported with its exact p-value, the causal sentence about extra sessions was removed, and the repeated pressure sentence in the review prompt is a stated limit. |
| F6 | Fixed | Table 8 reports exact permutation p-values and Holm-adjusted p-values; leave-one-model-out results are in the text. With the corrected oracle the N and U2 contrasts reach Holm-adjusted p of about 0.04, and the manuscript reads them as suggestive because they sit near the placebo scale and lose support when DeepSeek or GLM is left out. |
| F7 | Fixed | "The order holds" was removed; the text states that in Qwen only AE separates and that in GLM N and AE are about equal. |
| F8 | Fixed | Hidden test added for the exception order; the mutant is now behavior-changing. Three equivalent survivors remain, each argued in the audit. |
| F9 | Fixed | The reference and the hidden test now follow the specification text literally (`dom[1:-1]`), and the four domain mutants were rewritten. |
| F10 | Partly fixed | The empty-parse case now raises an error. Timeouts and missing tests still count as kills and are not counted separately; neither occurred in the rescored runs, and the choice is documented in `PILOT3_ORACLE_CORRECTION.md`. |
| F11 | Fixed | Section 6 and the preregistration state 288 runs (306 including the pilot) and that the token estimate comes from earlier pilots. |
| F12 | Fixed | Preregistration and Section 6 use a stratified permutation test as primary and a fixed-effects-for-model model as secondary. |
| F13 | Fixed | The manuscript uses the mean sample SD of three-run cells; `analyze3.py` labels its figure as the spread pooled over models. |
| F14 | Fixed | Exact permutation p-values are reported; the text says the bootstrap intervals are optimistic with three runs per cell. |
| F15 | Partly fixed | A reproduction section in `benchmarks/README.md` lists the environment and the order of documents. Prompt paths under `/tmp/aep-lab` remain hard-coded and are documented. `build_v2.py` still depends on the author's local paths and on the earlier manuscript backup. |
| F16 | Fixed | The remediation figure is labeled "rejected deliveries only, so regression to the mean may contribute". |
| F17 | Fixed | The metadata abstract has no binary contrast and is 1,912 characters. |
| F18 | Documented | The date discrepancy is logged in `PILOT3_DEVIATIONS.md`; the design note itself was left untouched. |
| F19 | Fixed | The text says that the hash files are part of the replication package; the corrected hashes are in `FROZEN_HASHES_PILOT3_CORRECTED.txt`. |

Items the auditor could not verify: token counts and durations were not recorded (stated in 4.5, the deviations log, and the README); the construction of the calibration set is now documented in `benchmarks/pilot/CALIBRATION_SET.md`; the model and effort check rests on per-block exported-session summaries, which are in `results/pilot3_model_check_*.json`.
