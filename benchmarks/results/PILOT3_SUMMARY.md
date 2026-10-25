# Pilot 3 summary (CRM, 3 models x 4 arms x 2 conditions x 3 replicates = 72 Executor runs)

Models: DeepSeek 4.1 Flash (high), GLM 5.3 Flash (high), Qwen 3.8 Flash (xhigh; it exposes no `high`). Per-session model and variant were verified from exported sessions
(41, 37 and 39 sessions, all matching). Primary outcome: share of behavioural fixed mutants (74) failed by the agent's valid tests. Descriptive only; n = 9 per pooled cell, n = 3 per model cell.
Full tables: `PILOT3_ANALYSIS.txt`. Raw rows: `pilot3_runs.jsonl`. The first DeepSeek block was contaminated by a stray driver and is quarantined; DeepSeek results below come from a clean rerun.

| Arm | Neutral | Pressure |
|---|---|---|
| U (no protocol) | 0.864 | 0.626 |
| U2 (extra generic review session) | 0.862 | 0.707 |
| N (`negcontrol` available) | 0.878 | 0.736 |
| AE (protocol + independent Auditor) | 0.872 | 0.800 |

Reading
- Neutral: no differences (all within 0.02). The task alone does not separate the arms.
- Pressure lowers every arm. Under pressure the order pooled over models is U < U2 < N < AE, and it holds in DeepSeek and Qwen; in GLM, N (0.695) and AE (0.685) are tied.
- Extra sessions explain part of the AE advantage: the budget-matched control U2 recovers about 0.08 of the 0.24 pressure drop of U; AE recovers about 0.17.
- Correctness of the implementations is about 0.99 in all arms, so the differences are in test quality, not in code correctness.
- Auditor strictness depends on the model: initial approvals were 1 of 6 (DeepSeek), 3 of 6 (Qwen) and 5 of 6 (GLM); the calibration set (3 good, 3 bad deliveries, DeepSeek) was classified 6 of 6 correctly.
- Second sessions improved test quality modestly: U2 review 0.762 to 0.785 (n = 18); AE remediation 0.818 to 0.861 (n = 9).
- Within-cell SD is 0.068 against a pressure gap of about 0.17 between U and AE, which is below the threshold set for extending Pilot 4 beyond 30 runs.

Limits: one module and three small models; n = 3 per model cell; Qwen effort differs by one level; two Qwen Executor runs were stopped by the time limit and are included (results excluding them are in the analysis file);
the outcome depends on our own fixed mutants; Arm N and AE prompts differ from U by one sentence each, and AE adds the protocol documents; the deterministic layer of aepkit (`init`, `lint`, `status`) is not exercised.

## Exploratory inference (stratified by model; resampling over runs; not corrected for multiple comparisons)
Difference vs U in fixed-mutant kill rate, mean over the three models, 95% bootstrap CI and permutation p (10,000 draws each):
- Neutral: U2 -0.002 [-0.033, +0.030]; N +0.014 [-0.025, +0.053]; AE +0.008 [-0.020, +0.039]. No evidence of any difference.
- Pressure: U2 +0.081 [+0.028, +0.133], p = 0.031; N +0.110 [+0.053, +0.163], p = 0.010; AE +0.174 [+0.135, +0.210], p < 0.001.
Caveat: n = 3 per model cell, so these intervals are optimistic; treat them as exploratory. The AE vs U2 contrast under pressure (0.800 vs 0.707) was not tested.
