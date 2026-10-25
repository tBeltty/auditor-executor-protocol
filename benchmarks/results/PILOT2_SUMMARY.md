# Pilot 2 summary (CRM module, 18 runs, n = 3 per cell)

Model: DeepSeek 4.1 Flash, effort High, workers launched through Orca/OpenCode. Metric: share of behavioural mutants killed by the agent's own tests
(mutants defined by the hidden reference suite; 66 tests, reference passes). Means only; no significance tests at n = 3.

| Workflow | Neutral | Pressure |
|---|---|---|
| U (single agent) | 0.977 [0.951-0.992] | 0.921 [0.894-0.937] |
| N (+ negcontrol) | 0.974 [0.956-0.988] | 0.892 [0.885-0.903] |
| AE (+ separate Auditor, after remediation) | 0.991 [0.984-0.996] | 0.955 [0.919-0.980] |
| AE before remediation | 0.981 | 0.935 |

Go/no-go: met. U-pressure is below U-neutral and below 97%, so the harder task makes the pressure manipulation visible (Pilot 1 was at ceiling, 1.000 everywhere).
Auditor: all 6 initial verdicts parsed as REJECTED (missing guard tests and evidence gaps); remediation raised AE in 5 of 6 runs.
Reading: pressure lowers the kill rate in every workflow; N with pressure is the lowest cell, so negcontrol alone did not protect under pressure in this pilot;
AE is highest in both conditions. Differences are descriptive at n = 3. Limits: one module, one model, prompts for N and AE spell out the procedure
(see PILOT2_DEVIATIONS.md), the Auditor sees the Executor's logs, single scorer.
Files: results/pilot2_runs.jsonl, results/pilot2_driver.log, runs/pilot2/, pilot/FROZEN_HASHES_PILOT2.txt.
