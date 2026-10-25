# Pilot 3 summary (CRM, 3 models x 4 arms x 2 conditions x 3 replicates = 72 Executor runs)

Corrected oracle (see `pilot/PILOT3_ORACLE_CORRECTION.md`; original rows in `pilot3_runs_original_oracle.jsonl`). Models: DeepSeek 4.1 Flash (high), GLM 5.3 Flash (high), Qwen 3.8 Flash (xhigh, the nearest level above high because it exposes no high). Per-session model and variant were verified from exported sessions (41, 37, 39 sessions, all matching).
Primary outcome: share of the 75 behavioural fixed mutants failed by the agent's valid tests. Descriptive; n = 9 per pooled cell, n = 3 per model cell. Tables and tests: `PILOT3_ANALYSIS.txt` and `paper/manuscript.md` Section 4.5.

| Arm | Neutral | Pressure |
|---|---|---|
| U (no protocol) | 0.880 | 0.622 |
| U2 (extra generic review session) | 0.881 | 0.729 |
| N (`negcontrol` available) | 0.905 | 0.744 |
| AE (protocol documents + Auditor + remediation) | 0.881 | 0.825 |
| AE, Executor first session (before the Auditor) | 0.858 | 0.797 |

Reading
- Neutral: no differences. Pressure lowers every arm.
- AE minus U under pressure: +0.203, exact permutation p < 0.001, Holm-adjusted 0.002; stable when any one model is left out; 2.6 times the placebo difference between two identical conditions (+0.077, p 0.069).
- N minus U +0.121 (Holm 0.041) and U2 minus U +0.107 (Holm 0.043) are suggestive: close to the placebo scale and unstable when DeepSeek or GLM is left out.
- Most of the AE gain is already present in the Executor's first session, before the Auditor acts. Auditor verdicts did not track the kill rate of the work in the main runs; the calibration set (6 constructed deliveries, one model) was classified correctly.
- Correctness of the implementations is about 0.99 in every arm.

Limits: three runs per model cell, one module family, small models, simulated pressure, author-written oracle, Qwen one effort level above the others, no token or duration data, the AE prompt tells the Executor that a reviewer will read the delivery, the U2 review prompt repeats the pressure sentence, and `aepkit init`, `lint` and `status` were not exercised.
