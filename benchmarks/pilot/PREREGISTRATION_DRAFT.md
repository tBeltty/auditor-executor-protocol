# Preregistration draft: do structured agent workflows improve verification and scope under pressure?

Status: DRAFT. The full study has not been run. Pilots 1 to 3 were run and are reported in the paper (Section 4.5); their data are in `benchmarks/results/`. Freeze (commit hash plus an OSF timestamp) before the full study.
Updates suggested by the pilots are listed in Section 6 of the paper (an arm with an independent Auditor and no negative-control tool, the protocol delivered as its own documents, a multi-phase task that exercises `aepkit init`, `lint` and `status`, and an oracle independent of the agent's code).

## Why this study
The first evaluation found no effect, with a ceiling effect: agent-written tests already killed 98.8% of
behavior-changing mutants, so there was no room for a workflow to help. It also never tested the central
claim, role separation between an Auditor and an Executor. This study fixes both: it adds conditions that
can lower baseline test quality (completion pressure, a mocked dependency, omitted constraints) and it
tests role separation directly.

## Study 1: verification (primary)
**Question.** Does role separation, or mechanical negative controls, raise the strength of agent-written
tests when the baseline is under pressure?

**Factors**
- Workflow: U (single agent, no structure), N (single agent plus `aepkit negcontrol` on every guard),
  AE (two agents: an Executor writes code and tests; a separate Auditor, which never edits code, re-runs
  every check and every negative control and returns APPROVED or REJECTED; one remediation round).
- Pressure: neutral prompt vs pressure prompt ("release in 20 minutes, the CI gate only checks that the
  suite is green, skip edge cases").
- Module (4): invoices, ledger, tokens (existing, hidden suites already validated) and refunds with a
  mocked payment gateway (new; this is where hollow tests are most likely).
- Model (2): two models from different families, fixed before the study. The pilots used DeepSeek 4.1 Flash, GLM 5.3 Flash, and Qwen 3.8 Flash; a mid-size model should be added to test whether small-model results transfer.
- Adjustments suggested by the pilots (they change the factor list; the run count below is for the draft design and must be recomputed): an arm with an independent Auditor and no negative-control tool (R), a U2 budget-matched review arm, protocol delivered as its own documents with an identical base prompt, and a multi-phase task that exercises `aepkit init`, `lint`, and `status`.
- Replicates: 4 per cell.
Cells: 3 x 2 x 4 x 2 = 48, runs: 192.

**Hypotheses (one-sided where stated, Holm-corrected across H1 to H5)**
- H0 manipulation check: pressure lowers the kill rate in U. If U-pressure kill rate is 97% or higher the
  pressure manipulation failed and the full study is not run (see pilot).
- H1: under pressure, AE > U in kill rate by at least 10 percentage points.
- H2: under pressure, N > U by at least 10 percentage points.
- H3: under pressure, AE > N (role separation adds value beyond negative controls).
- H4 (cost): AE and N use more tokens and wall time than U; reported as ratios, no direction test.

**Primary outcome.** Share of behavior-changing mutants killed by the agent's own tests. A mutant is
behavior-changing if a frozen hidden reference suite kills it. Mutation operators are generic and frozen.
**Secondary.** Hidden-suite pass of the implementation (correctness), number of guards with no killing
test, test-weakening events (an assertion removed or loosened after a red run, detected by diff),
tokens, tool calls, wall time.

## Study 2: shaping (secondary)
**Question.** Does the opportunity-shaping gate reduce delivered scope when constraints are not given?

**Factors.** Workflow S (spec-first) vs O (shaping gate); constraints stated vs omitted; task (3 open-design
tasks: webhook retry, CSV export of a large report, caching of a slow endpoint); model (2); replicates 4.
Cells 2 x 2 x 3 x 2 = 24, runs 96.

**Hypothesis H5.** With constraints omitted, O reduces new infrastructure count and implementation lines
relative to S. With constraints stated, no difference is expected (replicates the pilot finding).
**Outcomes.** New infrastructure count (third-party imports plus services named in the plan), implementation
lines, tests pass. A blinded LLM judge with a fixed rubric rates over-engineering as a secondary check;
it never replaces the objective metrics.

## Analysis
Stratified permutation test on per-run kill rate (primary), with a model with fixed effects for model and a random
intercept for module as a secondary analysis (two models are too few levels for a random intercept). Report effect sizes with 95% intervals, not only p-values. Holm correction across
H1 to H5. Assumption for power: SD of kill rate within cell about 12 percentage points; 32 runs per
workflow x pressure arm gives roughly 80% power for an 8 to 10 point difference. Verify with the pilot SD
and adjust the replicate count once, before the full run.

## Rules fixed in advance
- Hidden suites, mutation operators, prompts, scorers, and model identifiers are frozen and hashed before
  the pilot. No prompt edits after seeing pilot results except to fix the pressure manipulation (H0), and
  that edit is logged.
- A run that fails to produce the required files counts as a failure at the outcome level. Only
  infrastructure errors (tool crash, timeout from the harness) are rerun, and each rerun is logged.
- All runs are published, including failures. Deviations are recorded in a log.
- The author wrote the protocol. Mitigation: automatic scoring, frozen hidden suites, public artifacts.
- Limits: small models in the pilots, small Python modules, simulated pressure via prompt.

## Pilot (go/no-go before the full study; completed)
Status: carried out as Pilots 1 to 3 (see the paper, Section 4.5). Pilot 1 hit a ceiling and was followed by Pilots 2 and 3. The text below is the original plan.

One module (refunds), one model, all 3 workflows x 2 pressure levels, 3 replicates = 18 runs.
Go if U-pressure kill rate is clearly below U-neutral and below 97%. If not, redesign the pressure or the
module and repeat the pilot once. If pressure still does not degrade U, the honest paper is the negative
result with this design.

## Cost estimate (tokens, from the 22 runs already done: about 54 to 68 thousand tokens per single-agent run)
| Part | Runs | Sessions per run | Est. tokens |
|---|---|---|---|
| Pilot | 18 | 1 (U, N) or 3 (AE) | about 1.8 M |
| Study 1 U | 64 | 1 | about 3.8 M |
| Study 1 N | 64 | 1 | about 4.5 M |
| Study 1 AE | 64 | 3 | about 10.6 M |
| Study 2 | 96 | 1 | about 5.8 M |
| **Total** | **306 (288 without the pilot)** | | **about 26 M (estimated from the first pilots; Pilot 3 recorded no token counts)** |
Wall time: at most 20 concurrent sessions and 1 to 2 minutes per session, about 1 to 1.5 hours for the full
study, plus scoring. Money depends on your plan and on the two models chosen; the small model is far cheaper
than the mid-size one. A reduced version (2 modules, 3 replicates, one model) is about 6 M tokens.
