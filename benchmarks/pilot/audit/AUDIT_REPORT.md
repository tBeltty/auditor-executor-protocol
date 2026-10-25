# AUDIT_REPORT: independent audit of the rewritten paper (Part E, Sections 5 to 7, abstract). Verdict: APPROVED WITH REQUIRED CHANGES

Auditor: fresh session, no edits to `manuscript.md`, `build_v2.py`, `pilot_text.py`, or any result file. All checks were run on copies in `/tmp` or read-only against the repo. Date of audit: 2026-10-25. Line numbers refer to `manuscript.md` (384 lines).

## Summary

The numbers in Part E trace to the result files and reproduce exactly (Tables 5 to 8, correctness, second-session means, Auditor counts, the abstract's 0.63, 0.74, 0.80, 0.71). The build is reproducible without hand edits, the data trail is clean, and the `SKILL.md` frozen in the hashes is byte-identical to the one shipped in `aepkit` 0.6.0.

The required changes come from four places where the text claims more than the data support:

1. The oracle has 71 effective mutants, not 74. Three fixed mutants are syntactically invalid and are silently dropped by a scorer bug. A fourth "equivalent" survivor is not equivalent under the specification.
2. The Auditor-based claims are weaker than stated. Auditor verdicts are uncorrelated with delivery quality in the main runs (F2), and most of the AE advantage already exists in the Executor's first session, before the Auditor acts (F3).
3. The Pilot 2 numbers (Table 5) cannot be regenerated from the repository, although Section 7 says they can (F4).
4. The U2 contrast is read as a pure "extra sessions" control, but U2's first session, which is the same treatment as U, already differs from U by +0.052 under pressure (F5).

No finding changes the main pooled result for AE versus U (it survives every robustness check I ran). Findings about N and U2 versus U do not survive a multiplicity correction or leaving out one model.

## Findings

| id | severity | location | what is wrong | evidence | suggested fix |
| :-- | :-- | :-- | :-- | :-- | :-- |
| F1 | major | l.254 (Outcomes); `pilot/PILOT3_DESIGN_NOTE.md` item 3; `exp3/score3.py` `one()` | "74 are behavior-changing ... the other four are equivalent". The scorer uses 71. Three mutants (`convert_no_owner_ok`, `transfer_same_ok`, `transfer_capacity_ignored`) delete an `if ... raise` block but their `old` string omits the line indent, so the mutated `crm.py` has an `IndentationError`. The hidden suite then parses zero tests, `all({}.values())` is `True`, and `one()` returns "not behavioural". The three were never real mutants, and they are the guard-deletion mutants a validation test would be expected to kill. | Check 4 below: scorer drops 7 mutants (4 true survivors plus these 3). Direct run of the three mutants shows `IndentationError: unexpected indent` at `crm.py` lines 90 and 149. Every stored row has `mutants_behavioural: 71`. | Fix the three anchors (include the leading indent), rescore all 72 runs plus the 27 pre-session rows, and regenerate Tables 6 to 8. Or keep the data and write "71 effective mutants (78 minus 4 equivalent minus 3 invalid)". Guard the scorer: treat an empty parsed result as an error, not as a pass. |
| F2 | major | l.294, l.308 (5.1 item 5), l.14 | "The Auditor discriminates." Evidence is 3 good and 3 bad calibration deliveries, one model (DeepSeek), built by the author. In the 18 main AE deliveries the verdict is unrelated to quality: mean initial fixed-kill rate is 0.811 for the 9 APPROVED and 0.818 for the 9 REJECTED. GLM approved 5 of 6 deliveries with a kill rate near N's; the GLM sample audit approves while listing guard gaps ("none of them hid a defect"). | Check 7 below (first-session table and verdict split). `results/pilot3_calibration.json`, `PILOT3_DESIGN_NOTE.md` item 5. | Replace "The Auditor discriminates" with: "The Auditor separated six author-built calibration deliveries (one model); in the 18 main deliveries its verdicts did not track the fixed-mutant kill rate (0.811 approved, 0.818 rejected)". Drop "independent Auditor" as the label of the 0.80 arm in the abstract (see F3). |
| F3 | major | l.14, l.292, l.296, l.307 | The AE advantage is credited to "an independent Auditor". The data decompose it. Under pressure the AE Executor's first session (before any Auditor input) has mean kill rate 0.772 against U 0.626 (+0.146); the audit plus remediation adds 0.028 (0.772 to 0.800). Only 4 of 9 pressure deliveries were rejected. The first-session gain comes from the protocol documents, the tool path, and the sentence "A separate Auditor will review your delivery", which also contradicts the pressure text "nobody will read the tests". Section 4.5 says the documents and the Auditor are not separated, but the abstract and conclusion still label the arm by the Auditor. | Check 7. `exp3/prompts3.py` lines for `exec`/`AE`. Per model first-session pressure: DeepSeek 0.761, GLM 0.685, Qwen 0.869 versus U 0.568, 0.549, 0.761. | Report the first-session decomposition in 4.5 (one sentence and a row in Table 6). In the abstract write "a workflow with protocol documents and a separate Auditor session (0.80)". State that the prompt tells the AE Executor it will be reviewed, which weakens the pressure manipulation for that arm. |
| F4 | major | l.256 to l.262 (Table 5), l.346 (Section 7 "Rerun") | Section 7 says `exp2/score.py` regenerates the pilot numbers from stored runs. For Pilot 2 it does not. Pilot 2 was scored with the 66-test hidden suite, which is not in the repo (the file was overwritten with the 71-test version; `git log` shows one commit; no copy). Rescoring now returns different numbers and `hidden_pass_on_original: false`. | `python3 exp2/score.py runs/pilot2/U-pressure-2 crm`: 0.895 (248 behavioural of 248) versus stored 0.937 (237 of 248). `AE-pressure-1`: 0.942 versus stored 0.965. `shasum -c FROZEN_HASHES_PILOT2.txt`: `exp2/hidden/test_crm.py: FAILED` (explained in `PILOT3_DEVIATIONS.md` item 4, but the old file is not shipped). Pilot 1 rows and hashes are fine. | Ship the 66-test suite (for example `exp2/hidden/test_crm_v66.py` with its hash and a `score.py` flag), or say in Section 7 and the Table 5 caption that Pilot 2 values were computed with a 66-test suite that is not released and rescoring with the released suite gives different values. |
| F5 | major | l.292, l.307 | "Because U2 recovers a part of the drop, the extra sessions alone account for some of the AE difference." The U2 contrast mixes a review effect with baseline noise. U2's first session is the same treatment as U, yet under pressure it averages 0.678 versus 0.626 for U (+0.052). The review session itself adds +0.030 under pressure (0.023 overall, n = 18). So about two thirds of the reported U2 minus U difference (+0.081) is between-run noise in two identical conditions. The intervals in Table 8 do not include this noise because U and U2 first sessions are never compared. The U2 review prompt also repeats the pressure sentence ("keep it fast"), so it is a weak review control. | Check 7: first-session means U 0.626, U2 0.678, N 0.736, AE 0.772. `prompts3.py` `review` role appends `p`. | Add the U versus U2-first-session difference to 4.5 as an empirical noise floor. Replace "the extra sessions alone account for" with "a generic second session was followed by a small gain (+0.030 under pressure)". Note the pressure text in the U2 and remediation prompts. |
| F6 | major | l.288 to l.290 (Table 8), l.292, l.307 | p-values with no multiplicity correction and an unqualified ordering claim. With Holm over the six contrasts (exact permutation p) only AE minus U under pressure survives (adjusted 0.0015); N minus U gives 0.0675 and U2 minus U 0.135. Leaving out DeepSeek gives N minus U exact p = 0.115 and U2 minus U 0.245; leaving out GLM gives 0.100 and 0.135. Only the AE contrast is stable. Section 5.3 says "exploratory", but 5.1 item 4 and the conclusion list N and U2 as higher than U. | Check 6 below. | Report AE minus U as the one contrast that survives Holm and leave-one-model-out. Say N and U2 contrasts are consistent in direction but not robust. Add the Holm-adjusted column or a sentence. |
| F7 | major | l.292 | "The order holds in DeepSeek and Qwen." In Qwen, U, U2, and N are 0.761, 0.770, 0.775 (gaps of 0.009 and 0.005 on n = 3 with within-cell SD around 0.05); only AE (0.878) separates. The order U < U2 < N < AE is a numerical ordering, not a replicated one. Per-model exact permutation p-values cannot go below 0.1 with three runs per cell (20 splits). | Check 6 per-model output: Qwen U2 diff 0.009 (p 1.0), N 0.014 (p 0.8), AE 0.117 (p 0.1). | Write "AE is highest in all three models under pressure except GLM where AE and N are tied; in Qwen U, U2, and N are indistinguishable". Drop "the order holds". |
| F8 | minor | l.254, l.254 (3 survivors), `exp2/specs/crm.md` step 6 of `discount` | One of the four "equivalent" survivors is not equivalent under the specification. `discount_cap_unchecked_range` (limit 30 to 50) changes the exception for a non-manager owner with pct in 31 to 50: the spec says step 2 fails first (ValueError), the mutant reaches step 5 (PermissionError). The hidden suite lacks that test. The other three are equivalent: `email_count_ge1` (a second "@" makes `split("@")` raise ValueError anyway), `free_single_only` (a queue is non-empty only when every rep is at capacity, so one slot frees at most one lead), `transfer_no_free_old` (a transfer needs the new owner below capacity, which implies an empty queue, so the freeing loop is a no-op). | Direct execution: `discount(o, 40, "r1")` raises `ValueError` on the reference and `PermissionError` on the mutant. | Add the missing hidden test (and a note that the suite is weaker than the spec), or reclassify the mutant as a real, unkilled, defect and update counts. |
| F9 | minor | `exp2/hidden/test_crm.py::test_domain_edge_dots`, `exp2/reference/crm.py` line 42, l.294 | 51 of 72 final implementations fail one hidden test (hence correctness 0.986 in most rows). The failing assertion rejects `a@.corp.com`. The spec says the domain "contains a '.' which is neither the first nor the last character of the domain", which `.corp.com` satisfies literally. The reference is stricter than the text. The two related mutants (`email_dom_start_dot_ok`, `email_dom_end_dot_ok`) survive in 65 and 64 of 72 runs, subtract about 0.03 from nearly every run equally, and agent tests that follow the literal spec are filtered out as "invalid" because they fail on the reference. This does not bias contrasts (survivor counts per arm are similar) but it lowers the level, and "correctness was high and almost constant" hides that the shared miss is a spec ambiguity. | Check 4 and survivor frequency table below. | Clarify the spec wording or drop the two mutants and the test; mention the ambiguity as a threat. |
| F10 | minor | `exp3/score3.py` `one()` | Scorer details that can inflate the kill rate: a timeout of the agent suite on a mutant counts as a kill (`a is None`), and any valid test missing from the mutant run counts as a kill (`t not in a`), for example after a collection error. Neither was observed to matter here (no hidden-suite hangs; all mutants import), but both are untested. Filter side: tests that fail on the reference are excluded, which lowers the valid-test count for agents that follow the spec literally (F9). | Code reading; `/tmp/audit_oracle.py` shows all 78 mutants run within the timeout against the hidden suite. | Count timeouts and missing tests separately in the output row, or document them. |
| F11 | minor | l.332, `PREREGISTRATION_DRAFT.md` line 87 | "The full design has 306 runs". Study 1 (192) plus Study 2 (96) is 288. The 306 in the cost table includes the 18 earlier pilot runs. The "about 26 million tokens" and "6 million" come from that table, estimated from the first 22 runs; no token data for Pilot 3 are in the repo. | Preregistration cost table; `grep -il token results/*` finds nothing. | Write 288 (or "306 including the pilot") and say the token estimate is from the first pilots. |
| F12 | minor | l.328, `PREREGISTRATION_DRAFT.md` line 57 | "Mixed-effects model with random intercepts for module and model" with two models and four modules: random intercepts with two levels are not estimable. | Design reading. | Use fixed effects for model, a random intercept for module only, or state the permutation test as primary. |
| F13 | minor | l.332 (v), `analyze3.py` line 52 | The within-cell SD of 0.040 uses `pstdev` (divisor n) on three runs. The sample SD is 0.049. `analyze3.py` prints 0.068 because it pools over the nine runs per arm and condition (it includes model differences). Three numbers for "within-cell SD" appear in the package. | `/tmp/audit_stats.py`: pstdev 0.040, sample SD 0.049. | Use the sample SD in the text and label the `analyze3.py` figure as pooled over models. |
| F14 | minor | `pilot_text.py` line 70 to 88, l.283 | Bootstrap percentile intervals over three runs per cell resample from three distinct values, so they are too narrow (the bootstrap understates variance by about (n-1)/n per cell, and the per-cell resampling is independent across arms). The permutation p has no +1 correction (the `< 0.001` row is exact p 0.0003, so it is fine in practice). The permutation scheme itself is valid: it permutes arm labels within model and pressure and averages the per-model differences. | Own exact enumeration of the 8,000 stratified splits reproduces the stored p-values within Monte Carlo error: U2 0.034 (stored 0.031), N 0.0135 (0.010), AE 0.0003. | Report the exact permutation p, or add a sentence that bootstrap intervals are optimistic with three runs per cell (Section 4.5 already says "optimistic"). |
| F15 | minor | `exp3/prompts3.py`, `FROZEN_HASHES_PILOT3.txt` | Hard-coded `/tmp/aep-lab/...` paths for the tool, spec, and protocol. `build_v2.py` and `pilot_text.py` hard-code `/Users/jhonatan/...` and `build_v2.py` needs `manuscript_v1_backup.md`. Running `python3 -I build_v2.py` fails (`No module named 'pilot_text'`) because `-I` removes the script directory from `sys.path`; without `-I` it succeeds. | Check 1. | Add a README block in `benchmarks/` listing the environment (`aepkit` 0.6.0 in a venv, spec copy, protocol copy) and make paths configurable. |
| F16 | minor | l.252, l.294 | "Auditor approved 1 of 6 (DeepSeek), 3 of 6 (Qwen), 5 of 6 (GLM)" is correct (9 approved, 9 rejected overall). The reported before/after for AE remediation (0.818 to 0.861, n = 9) covers only the rejected deliveries, which are selected on quality, so regression to the mean inflates it. U2 (n = 18) is unselected. The two numbers are not comparable. | `analyze3.py` output. | Add "(rejected deliveries only)" next to 0.818 to 0.861. |
| F17 | minor | l.13, l.14, metadata abstract | Abstract line 14 attributes the 0.80 to "an independent Auditor". The metadata abstract has "it shows which mechanisms exist, not effectiveness", a binary contrast the author's rules prohibit. The manuscript abstract is 2,790 characters; the arXiv metadata abstract is 1,722 (limit 1,920, passes). | Character counts in Check 10. | Rewrite the metadata sentence ("it shows which mechanisms exist and says nothing about their effectiveness"). |
| F18 | nit | `pilot/PILOT3_DESIGN_NOTE.md` line 3 | The note is dated 2026-10-26; all files are dated 2026-10-25. The note also states "74 of 78" (see F1). | `ls -la`, `head pilot/PILOT3_DESIGN_NOTE.md`. | Correct the date or explain the timezone. |
| F19 | nit | l.246 | "each pilot's scorer, hidden suite, and prompts were hashed (Section 7)". Section 7 describes the hash files only in one clause. `analyze3.py` and `pilot_text.py` are not hashed. | Section 7 text. | Say which files are hashed. |

## Claim-by-claim review (4.5, 5.1, abstract, Section 7)

| Claim | Location | Class | Evidence |
| :-- | :-- | :-- | :-- |
| Tables 5 to 8 values, correctness, second-session means, Auditor counts | l.256 to l.294 | SUPPORTED | Recomputed from result files |
| "78 mutants, 74 behavior-changing, four equivalent" | l.254 | UNSUPPORTED | 71 effective; one survivor is not equivalent (F1, F8) |
| Pilot 1 ceiling | l.292 | SUPPORTED | All 18 rows at 1.000. MISSING CAVEAT: the denominator is mutants of the agent's own code that a hidden suite kills, so a ceiling can partly reflect the operator set |
| "The pressure condition visible" in Pilot 2 | l.292 | SUPPORTED, MISSING CAVEAT | Neutral to pressure: U 0.977 to 0.921, N 0.974 to 0.892, AE 0.991 to 0.955; ranges barely overlap only for AE. Scores used a 66-test suite that is not released (F4) |
| "AE stayed highest under pressure" in Pilot 2 | l.292 | OVERSTATED | AE [0.92, 0.98] overlaps U [0.89, 0.94] with three runs per cell |
| "In Pilot 3, without pressure the four arms were indistinguishable" | l.292 | SUPPORTED | Differences -0.002 to +0.014, exact p 0.60 to 1.0 |
| Pressure drop of 0.238 for U | l.292 | SUPPORTED | 0.864 to 0.626 |
| AE +0.174, N +0.110, U2 +0.081 "associated with" | l.292 | SUPPORTED for AE; MISSING CAVEAT for N and U2 (F5, F6) | Holm and leave-one-out |
| "associated with" wording | throughout | SUPPORTED | No causal verbs found in results text. Exception: "the extra sessions alone account for some of the AE difference" is causal (F5) |
| "The order holds in DeepSeek and Qwen" | l.292 | OVERSTATED | F7 |
| "U2 matches the number of sessions" / extra-session control | l.248, l.292 | MISSING CAVEAT | Not matched in tokens (no token data), not matched in presence of an independent reader, and U2's own first session differs from U by +0.052 (F5) |
| "The Auditor discriminates" | l.308 | UNSUPPORTED for the main runs | F2 |
| "Auditor approved 1, 3, 5 of 6" | l.294 | SUPPORTED | 9 approved, 9 rejected |
| "Correctness high and almost constant" | l.294 | SUPPORTED, MISSING CAVEAT | Shared miss is the spec ambiguity in F9 |
| "AE arm differs from U in two ways at once" | l.296 | SUPPORTED but incomplete | Also the review notice in the prompt and the tool path; the first-session decomposition shows documents or prompt carry most of the effect (F3) |
| `init`, `lint`, `status` not exercised | l.296, l.312 | SUPPORTED | Pilot 3 AE directories hold only `audit.md`, code, tests, and occasional reports or logs |
| Qwen at `xhigh`, two time-limit runs included | l.296 | SUPPORTED | `pilot3_model_check_qwen.json` shows `qwen3.8-flash/opencode-go/xhigh: 39`; the exclusion analysis moves N neutral 0.878 to 0.877 and AE neutral 0.872 to 0.866 |
| "Anything in the abstract stronger than the body" | l.14 | OVERSTATED in one place | "with an independent Auditor (0.80)" (F3) |

## Design and statistics

- **Pooling.** Pooling three models with different baselines is acceptable here because every contrast is computed within model and then averaged (the permutation also shuffles within model). The pooled interval treats the three models as fixed, so it says nothing about other models.
- **Intervals.** With three runs per cell the bootstrap is optimistic (F14). The exact permutation test is the more defensible summary.
- **Alternative analyses run.**
  - Exact stratified permutation (8,000 splits): AE minus U under pressure p = 0.0003; N 0.0135; U2 0.034. Neutral contrasts p between 0.60 and 1.0. Same conclusion as the paper.
  - Holm over six contrasts: AE 0.0015, N 0.0675, U2 0.135.
  - Leave-one-model-out for AE minus U under pressure: +0.127 (without DeepSeek), +0.192 (without GLM), +0.202 (without Qwen), each exact p = 0.005 (the smallest value possible with two models). N minus U: +0.080, +0.092, +0.157 (exact p 0.115, 0.100, 0.020). So Qwen attenuates the pooled result instead of driving it (dropping Qwen raises every difference). The N and U2 contrasts lose significance whenever DeepSeek or GLM is dropped, so they rest on all three models.
  - Per model: AE minus U is +0.268 (DeepSeek), +0.136 (GLM), +0.117 (Qwen), all with the minimum possible exact p of 0.1; every replicate-paired difference for AE minus U is positive (9 of 9). Pairing by replicate number carries no meaning unless seeds were shared, so I used it only as a sign check.
- **Mixed model.** Not run; with 3 runs per cell and 3 models it would add little. A per-model analysis changes the story in one respect: the pooled significance comes from consistent direction across models, not from any single model.
- **Confounds.**
  - (a) Tokens and sessions: no token or session-record data are in the repo, so the AE versus U token gap could not be checked.
  - (b) Qwen effort: see leave-one-out above; Qwen has the highest U baseline (0.761) and no U2 or N effect.
  - (c) Time-limit runs: the exclusion analysis in `PILOT3_ANALYSIS.txt` reproduces; both stopped runs are neutral arms.
  - (d) Prompt differences: AE gets the tool, the protocol files, and "A separate Auditor will review your delivery"; N gets the tool path and one sentence. U and U2 first sessions have identical prompts (so their difference is a direct noise estimate, F5).
  - (e) The Auditor reads the whole run directory. In Pilot 3 the Executors left no compliance logs in most directories, so there was little to lead it. It can still be influenced by test names, docstrings, and report files that some Executors wrote (`EXECUTOR_REPORT.md`, `REMEDIATION.md`, `COMPLIANCE_LOG.md`). Not quantified.
  - (f) Order effects: correlation between launch order within a model block and the residual against the cell mean: Qwen -0.01, GLM -0.26, DeepSeek 0.03 (n = 24 each). No trend of concern.

## Data trail

- `results/pilot3_runs.jsonl`: 99 rows = 72 `final` + 18 `pre_second_session` U2 + 9 `pre_second_session` AE. Matches the handoff.
- Every `final` row has `model` in {deepseek, glm, qwen}; DeepSeek rows trace to `runs/pilot3/deepseek-rerun`. Quarantined data are in `results/quarantine/` and `runs/pilot3_quarantine/`.
- Run counts: 18 + 18 + 72 = 108 Executor runs. The manuscript text never states "108"; the metadata abstract does.
- Hashes: `FROZEN_HASHES.txt` and `FROZEN_HASHES_PILOT3.txt` all OK; `FROZEN_HASHES_PILOT2.txt` fails only on `exp2/hidden/test_crm.py`, explained in `PILOT3_DEVIATIONS.md` item 4 (but see F4).
- `aepkit` 0.6.0 wheel from PyPI: `aepkit/skill/SKILL.md` SHA-256 `4afe54cb...649e4fb`, identical to `/tmp/aep-lab/protocol/SKILL.md`.

## Writing rules and consistency

- Scan of the abstract, Contributions, and Sections 4.5 to 7: no em-dashes, no throat-clearing openers, no "not X but Y" in the manuscript text. One binary contrast in the metadata abstract (F17).
- Cross-references: repository as Section 7 and confirmatory design as Section 6 are correct; 8 tables; 15 pages in both `manuscript.pdf` and `arxiv_submission/manuscript.pdf` (identical SHA-256); metadata abstract 1,722 characters (limit 1,920).
- Metadata says "15 pages, 1 figure, 8 tables": consistent.
- Scope honesty: the body states that `init`, `lint`, and `status` were not exercised, that `negcontrol`, independent review, and the documents are not separated, and that the pilots used small models and one module family. The abstract states small models, simulated pressure, and small samples but does not mention the deterministic layer and labels the 0.80 arm by the Auditor (F3).
- Known accepted weaknesses (three runs per cell, one module family, small models, simulated pressure, author-written oracle, AE versus U2 not tested, Qwen effort, GLM tie, Pilot 4 backlog) are all stated in 4.5, 5.2, or 5.3.

## Commands run and results

```
# 1 rebuild (on a copy)
rm -rf /tmp/audit_build && cp -R <paper dir>/. /tmp/audit_build/
cd /tmp/audit_build && python3 -I build_v2.py      -> ModuleNotFoundError: pilot_text   (F15)
cd /tmp/audit_build && python3 build_v2.py         -> manuscript.md written 57659
diff /tmp/audit_build/manuscript.md <paper dir>/manuscript.md   -> identical

# 2 recompute
python3 benchmarks/exp3/analyze3.py                -> Tables 6, 7, correctness, second-session means, verdict counts match
python3 /tmp/audit_stats.py                        -> Table 6 and Table 8 point estimates match; exact permutation, Holm,
                                                      leave-one-model-out, per-model tests (outputs above)

# 3 rescore sample (stored rows matched exactly)
python3 benchmarks/exp3/score3.py benchmarks/runs/pilot3/{deepseek-rerun/U-pressure-1, deepseek-rerun/AE-neutral-2,
    glm/U2-pressure-2, glm/N-neutral-1, qwen/AE-pressure-3, qwen/U-neutral-2}   -> 6 of 6 match
python3 benchmarks/exp2/score.py benchmarks/runs/pilot2/{U-pressure-2, AE-pressure-1} crm   -> 2 of 2 MISMATCH (F4)

# 4 oracle
python3 /tmp/audit_oracle.py <repo>/benchmarks   -> 78 unique mutants, all anchors apply exactly once, reference passes 71 of 71,
                                                    hidden suite kills 74, survivors: email_count_ge1, free_single_only,
                                                    discount_cap_unchecked_range, transfer_no_free_old
inline script: 7 mutants treated as non-behavioural by score3.py; 3 of them are IndentationError mutants (F1)
inline script: discount(o, 40, "r1") -> ValueError on reference, PermissionError on mutant (F8)
unittest of hidden suite on a Qwen run: test_domain_edge_dots fails on "a@.corp.com" (F9)

# 7 and 8
inline scripts: first-session kill rates, verdict split, launch-order residual correlation
shasum -a 256 -c pilot/FROZEN_HASHES.txt, ..._PILOT2.txt, ..._PILOT3.txt   -> only exp2/hidden/test_crm.py fails (Pilot 2 file)
python3 -m pip download aepkit==0.6.0 --no-deps -d /tmp/audit_dl            -> aepkit-0.6.0-py3-none-any.whl
unzip via python3 -I zipfile into /tmp/audit_x; shasum -a 256 SKILL.md       -> identical to /tmp/aep-lab/protocol/SKILL.md

# 10
grep scans of the abstract, Contributions, 4.5 to 7 for em-dashes, contrasts, openers; character count of metadata abstract; pdfinfo
```

Scratch files left in `/tmp` (`audit_build`, `audit_dl`, `audit_x`, `audit_oracle.py`, `audit_stats.py`). No background processes were started.

## What I could not verify

- **Tokens, wall time, and session counts per arm** (confound a): no session records or token counts are in the repo.
- **Model and effort of every session read back from exported records**: only the per-block `pilot3_model_check_*.json` summaries are present, and they agree with the paper.
- **"Isolated OpenCode workers started through Orca"**: no artifact in the repo evidences it beyond the driver logs.
- **The 66-test Pilot 2 hidden suite**: not in the repo (F4), so Table 5 cannot be rescored.
- **Whether any agent test suite hangs on a mutant** (F10): not observed in the six rescored runs; I did not rescore all 72.
- **How the calibration deliveries (gold, bad) were constructed**: only their verdicts are stored; the construction is not documented in the design note.
- **`fault_matrix.py` and Parts A to D**: out of scope and not rerun (network access to PyPI required).
- **The claim that the Auditor can be led by the Executor's logs** (confound e): not quantified.

## Required changes before submission

1. F1 (mutant count and scorer bug), with Tables 6 to 8 regenerated if the three mutants are repaired.
2. F2 and F3 (Auditor wording in the abstract, 4.5, 5.1, and the conclusion; add the first-session decomposition).
3. F4 (ship or disclose the 66-test suite).
4. F5, F6, F7 (rewrite the U2, N, and ordering sentences; mention Holm and leave-one-out).

The remaining items are minor and can be fixed in the same pass.
