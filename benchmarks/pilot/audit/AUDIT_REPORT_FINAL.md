READY AFTER MINOR FIXES

# AUDIT_REPORT_FINAL: second, independent audit before push and submission

Auditor: fresh session, no part in the runs, the first audit, or the repairs. Date: 2026-10-25. Nothing in the repository, `manuscript.md`, `build_v2.py`, `pilot_text.py`, or any result file was edited. Scratch files are in `/tmp/final_audit/`. No subagents, no Orca workers, and no OpenCode sessions were used, so `~/.local/state/opencode/model.json` was never touched. Line numbers refer to `manuscript.md` (the shipped file, 61,390 characters).

## Summary

The numbers hold. Every Part E number I recomputed from `results/pilot3_runs.jsonl` with my own code matches the manuscript: Tables 5 to 8, the first-session rows, the Holm-adjusted p-values, the leave-one-model-out differences, the placebo contrast (+0.077, p 0.069), the "2.6 times" ratio, the approved and rejected means (0.830 and 0.825), correctness, and the second-session means. The corrected oracle validates (reference 72 of 72, 78 unique compiling mutants, 75 behavior-changing, three survivors argued equivalent). Nine distinct rescored runs match their stored rows. The 66-test suite hash matches and Pilot 2 reproduces 18 of 18. The shipped PDF equals the one in `arxiv_submission/`, and the build reproduces `manuscript.md` byte for byte. The main claim (AE above U under pressure) survives every alternative analysis I ran.

What is still wrong is about disclosure and reproducibility, not about the data:

1. The analysis that produces Table 8, the first-session rows, the placebo, and the leave-one-model-out figures (`pilot_text.py`) is not in the repository, although the commit message, `AUDIT_RESPONSE.md`, Section 7, and the README imply it is (N1).
2. The post-run oracle repair moved the N and U2 contrasts from non-significant to Holm-significant, and moved every non-U arm up. The manuscript reports that the repair happened but not what it did to the results (N2).
3. Several wording problems remain (N4 to N8).

None requires new runs or re-analysis. The first two require adding a file and two or three sentences.

## Findings

Findings the first audit raised that remain open keep their F-number (F4, F10, F15). New findings are N1 onward.

| id | severity | location | what is wrong | evidence | suggested fix |
| :-- | :-- | :-- | :-- | :-- | :-- |
| N1 | major | l.344 to l.352 (Section 7); `benchmarks/README.md` line 3; commit `dbf1036` message; `AUDIT_RESPONSE.md` F5, F6 | Table 8 (bootstrap, exact permutation, Holm), the leave-one-model-out differences, the placebo contrast, and the first-session rows of Table 6 are computed by `paper/pilot_text.py`, which is outside the repository. `exp3/analyze3.py` prints none of them. `pilot_text.py` also hard-codes `<local path>`. The commit message says it "adds first-session, placebo and Holm analyses", and the README says "Every number in the paper's evaluation is read from a file in `results/`". An outside reader can rescore runs but cannot regenerate the paper's inferential tables. | `git ls-files \| grep -i pilot_text` returns nothing. `grep -rl -i holm benchmarks` (py, md, txt) finds only run artifacts. `python3 benchmarks/exp3/analyze3.py` output (54 lines) has no permutation, Holm, placebo, or first-session lines; it shows "Paired difference vs U ... U2 +0.054, N +0.073, AE +0.102" (a different, all-cells statistic). | Copy the analysis half of `pilot_text.py` into `benchmarks/exp3/` as a path-independent script (read from `../results`), cite it in Section 7, and correct the README sentence. |
| N2 | major | l.254 (Outcomes), l.292 to l.294 (N and U2 sentences); `pilot/PILOT3_ORACLE_CORRECTION.md` | The oracle was repaired after the results were visible to the reviewer who found the defects. The repair did not use arm labels, but its effect is one-directional and crosses a threshold. Under the original oracle the pressure contrasts were U2 +0.081, N +0.110, AE +0.174 (Holm-adjusted about 0.14, 0.07, and significant for AE). After repair they are +0.107, +0.121, +0.203, and N and U2 reach Holm-adjusted 0.041 and 0.043. U's pressure mean moved 0.626 to 0.622, while U2, N, and AE rose 0.022, 0.008, and 0.025. The manuscript says "we repaired the instrument, rescored every run uniformly" and calls N and U2 "suggestive", but a reader cannot tell that those two contrasts were not significant before the repair. | Own computation from `results/pilot3_runs_original_oracle.jsonl` and `results/pilot3_runs.jsonl`: contrasts above; `mutants_behavioural` was 71 in every original row and is 75 in every corrected row. `PILOT3_ORACLE_CORRECTION.md` table gives the same means. | Add one sentence in 4.5: "Under the original oracle the pressure differences were +0.081 (U2), +0.110 (N), and +0.174 (AE), and only AE survived Holm correction." Keep the original rows and the correction note. Keep the current reading of N and U2 as suggestive. |
| N3 | minor | l.246 to l.254 (Pilot 3 description); `pilot/PILOT3_DEVIATIONS.md` item 1 | The manuscript says nothing about the invalidated first DeepSeek block (two drivers worked in the same cell directories; the block was moved to quarantine and rerun in fresh directories after the Qwen and GLM blocks). The owner intends this silence and I verified that the manuscript contains none of "free", "paid", "contamin", "stray", "quarantin" and no pricing tier. My recommendation differs: a reader who finds `results/quarantine/` in the repository (77 files) will ask. The sentence "Each design was fixed before the runs started" is true but incomplete. The discard was operational, not outcome-based, so the cost of disclosure is small. | Deviations log item 1; `grep -c quarantine` on the commit file list: 77. Model checks (`pilot3_model_check_*.json`) show 41, 39, and 37 sessions in the DeepSeek rerun, Qwen, and GLM blocks, equal to the expected session counts (24 + 6 + 6 + remediations). | One sentence: "A first DeepSeek block was invalidated by a duplicate driver process and rerun in fresh directories; the invalidated data are in the repository." Owner's decision. |
| N4 | minor | l.302 | "the three models are small and inexpensive" is a price-tier descriptor, which the handoff says the manuscript must not contain. | `grep -n -i "inexpensive" manuscript.md` hits l.302 (also present in the PDF text). | Delete "and inexpensive". |
| N5 | minor | l.294, l.308 (5.1 item 5), `AUDIT_RESPONSE.md` F2 | The approved versus rejected comparison (0.830 versus 0.825) pools three models whose approval rates are opposite (DeepSeek approves 1 of 6, GLM 5 of 6) and whose baselines differ. Within model the comparison is uninformative rather than null: DeepSeek approved 0.853 (n = 1) versus rejected 0.768 (n = 5); GLM approved 0.771 (n = 5) versus rejected 0.853 (n = 1); Qwen 0.920 (n = 3) versus 0.911 (n = 3). Section 5.1 item 5 says the verdicts "were unrelated". | `/tmp/final_audit/aud.py`. | Write "could not be assessed: pooled means were equal, and within-model cells hold 1 to 5 deliveries". Replace "unrelated". |
| N6 | minor | l.14, l.292, l.308, l.346 (conclusion) | The placebo contrast is a single draw (9 versus 9 runs, one difference, p 0.069). "2.6 times the difference between two identical conditions" and "survives a placebo comparison" read as if a test had been done. The ratio has no interval, and a +0.077 gap between identical conditions at p 0.069 also says the permutation p-values for the other contrasts are only as reliable as this noise level. | Own recomputation: placebo +0.077, exact p 0.0693. | Say "larger than the +0.077 difference observed between two identical conditions, which is one sample of the noise" and drop "survives a placebo comparison". |
| N7 | nit | l.292 | "In Qwen, U, U2, and N are within 0.03 of each other." The spread is 0.031 (0.760 to 0.791). The sentence is hard-coded in `pilot_text.py` (line 224) and not computed. | Table 7. | "within 0.04", or compute it. |
| N8 | minor | l.308 (5.1 item 4) | "This is the pattern the protocol predicts" sits next to "Most of the AE gain was already present in the Executor's first session, before the Auditor acted". The protocol's mechanism is independent review; the first-session result points to the documents and the reviewer notice. The sentence gives the data a confirmatory reading the section elsewhere avoids. | `prompts3.py`: the AE Executor prompt includes "A separate Auditor will review your delivery". First-session means: AE 0.797 versus U 0.622 versus U2-first 0.699. | Delete the sentence or write "consistent with the direction the protocol predicts, though most of it appears before the Auditor acts". |
| N9 | minor | l.246 to l.252 | The manuscript never states the model and effort of Pilots 1 and 2 (the design notes say DeepSeek 4.1 Flash at `high`). Readers cannot tell which model produced Table 5. | `grep -n "DeepSeek" manuscript.md`: only Pilot 3 and Table 7. | Add "Pilots 1 and 2 used DeepSeek 4.1 Flash at `high`." |
| N10 | minor | l.334 to l.338 (Section 6); `PREREGISTRATION_DRAFT.md` (both copies are identical) | Section 6 lists adjustments (an arm with an independent Auditor and no `negcontrol` tool, protocol documents delivered as files, a multi-phase task) but the Study 1 factor list and the 192-run count do not include them. The preregistration still says "a small and a mid-size Claude model" and "Limits: Claude models only", while the pilots used DeepSeek, GLM, and Qwen. It applies Holm "across H1 to H4" in one place and "H1 to H5" in another, and keeps a "Pilot (go/no-go)" section that describes an 18-run pilot as future work. | Preregistration lines 25, 40, 71, 83 to 88. | Update the factor list and run count to the adjusted design, change the model line, and mark the go/no-go section as completed. |
| N11 | minor | l.292, l.296 (limits) | The data already contain the contrast the paper says was not tested. AE minus U2 under pressure is +0.093 (DeepSeek), +0.089 (GLM), and +0.107 (Qwen); per-model one-sided exact p 0.15, 0.10, 0.05; Fisher combination 0.026 uncorrected. AE minus N is +0.084, +0.022, +0.138 (Fisher 0.048). These are exploratory and underpowered, but U2 is the only budget-matched control, and AE versus U2 is the fair comparison for the extra-session question. | `/tmp/final_audit` alternative-analysis command below. | Report AE minus U2 and AE minus N in Table 8 (or one sentence) labeled exploratory, and keep "we did not test AE against U2 as a planned contrast". |
| F4 | minor (was major) | l.348 to l.352 (Section 7 "Rerun") | The Pilot 2 rows now reproduce with `exp3/rescore_pilot2.py` and the released 66-test suite (18 of 18). Section 7 still says `exp2/score.py` regenerates "the pilot numbers"; on Pilot 2 that script uses the 72-test file and returns different values. The README names the right script; the manuscript does not. | `python3 benchmarks/exp3/rescore_pilot2.py`: "18 of 18 Pilot 2 runs reproduce exactly". `shasum -a 256 benchmarks/exp2/hidden/test_crm_v66.py` equals `e977915d...` in `FROZEN_HASHES_PILOT2.txt` (line for `exp2/hidden/test_crm.py`). | Name `rescore_pilot2.py` and `rescore3.py` in Section 7. |
| F10 | minor | `exp3/score3.py` `one()` | Open, as the response says. A timeout of the agent suite on a mutant and a valid test missing from the mutant run still count as kills. Neither occurred in the nine distinct rescored runs. | Code reading. | Document in Section 7 or count separately. |
| F15 | minor | `benchmarks/README.md`; `exp3/prompts3.py`; `build_v2.py` | Open. Prompts hard-code `/tmp/aep-lab`. `build_v2.py` and `pilot_text.py` hard-code `/Users/jhonatan` and need `manuscript_v1_backup.md`. The README documents the environment, which is enough to rerun scoring but not to rerun the agents. Only `SKILL.md` is hashed; the four files in `skill/references/` that the AE agents also read are not. | `pip download aepkit==0.6.0`: `SKILL.md` SHA-256 `4afe54cb...649e4fb`, equal to the hash in `FROZEN_HASHES_PILOT3.txt`; the `references/*.md` files have other hashes and are not listed. | Add the four reference hashes. |
| N12 | minor | repository, commits | Five commits are ahead of `origin/main`, not four: `d335cbc` (fault matrix and early experiments) is also unpushed. No message names an AI tool or carries `Co-Authored-By`. `git status` shows only `TO_CONSIDER.md` untracked. The commit adds 973 files, no file above 500 KB, no credential pattern, no email beyond test fixtures. Three committed lines in `benchmarks/pilot/audit/` contain `<local path>`. Those audit documents also describe Orca and OpenCode. `PROMPTS.md` and the preregistration copy mention "Claude" (correct for Parts B and C, stale for the preregistration). | `git log origin/main..HEAD --oneline`; grep scans of `git diff origin/main..HEAD`; `grep -c "/Users/jhonatan" benchmarks/pilot/audit/*` returns 2, 0, 1. | Decide whether the audit documents belong in the public repository. Replace the three personal paths. Push `d335cbc` knowingly. |
| N13 | nit | l.14; `benchmarks/README.md` line 8; `pilot_text.py` docstring | Remaining binary contrasts and an overclaim: "this shows which mechanisms exist and does not measure their effectiveness" (manuscript abstract, l.14) and "so the matrix shows which mechanisms exist in each version, not effectiveness" (README). The metadata abstract was fixed. The `pilot_text.py` docstring says "nothing is typed by hand", but several qualitative sentences are hard-coded ("survives ...", "within 0.03", "only AE separates"). | Line 224 and line 243 of `pilot_text.py`. | Use the metadata wording ("documents mechanism coverage and leaves effectiveness unmeasured"). Soften the docstring. |
| N14 | nit | l.14 | The manuscript abstract does not say that the deterministic layer (`init`, `lint`, `status`) was not exercised in the pilots. The body does (l.296, 5.2). Nothing in the abstract is stronger than the body. | Abstract text. | Optional: add six words. |

## Status of F1 to F19

| id | status | evidence |
| :-- | :-- | :-- |
| F1 | VERIFIED | `/tmp/final_audit/oracle.py`: 78 unique mutants, each `old` string occurs once in `crm.py`, all compile, none yields zero parsed tests, the hidden suite kills 75. `score3.py` now raises on zero parsed tests (code read). All 99 stored rows carry `mutants_behavioural` 75 and `mutants_total` 78. |
| F2 | VERIFIED | l.294 and l.308 now describe six calibration deliveries, one model, and equal approved and rejected means. See N5 for residual wording. |
| F3 | VERIFIED | Table 6 has the two first-session rows (0.864 and 0.699 for U2; 0.858 and 0.797 for AE), reproduced by my code. The abstract and conclusion no longer label the 0.83 arm by the Auditor. The notice to the Executor is stated as a limit. |
| F4 | PARTIAL | Suite released, hash equal, 18 of 18 reproduced. Section 7 still points to the wrong script (see F4 row). |
| F5 | VERIFIED | Placebo contrast reported (+0.077, p 0.069). The sentence "the extra sessions alone account for some of the AE difference" is gone. See N6. |
| F6 | VERIFIED | Holm column present and equal to mine (0.0015, 0.041, 0.043 for AE, N, U2 under pressure; 0.934, 1, 1 for the neutral contrasts). Leave-one-model-out values equal to mine. See N2 for the effect of the repair. |
| F7 | VERIFIED | "The order holds" is gone. The Qwen and GLM sentences are true (N7 for the 0.03 rounding). |
| F8 | VERIFIED | `test_pct_range_checked_before_owner_permission` is in the hidden suite and the mutant is killed. |
| F9 | VERIFIED | Reference uses `"." in dom[1:-1]`; the hidden test accepts `a@.corp.com`, `b@corp.com.`, `c@.corp.com.` and rejects `d@.com`, `d@corp.`, `d@.`. This matches the spec text literally. |
| F10 | PARTIAL | Zero-parse guard added; timeouts and missing tests still count as kills (disclosed in the correction note). |
| F11 | VERIFIED | l.334: "288 in total; the draft preregistration's 306 includes 18 pilot runs"; the preregistration table says the same. |
| F12 | VERIFIED | Section 6 and the preregistration both use a stratified permutation test as primary and fixed-effects-for-model as secondary. |
| F13 | VERIFIED | Mean sample SD of three-run cells: 0.044 (my code), equal to l.338. `analyze3.py` labels 0.070 as pooled over models. |
| F14 | VERIFIED | Exact permutation p-values are in Table 8 and the text says the bootstrap intervals are optimistic. My enumeration equals the shipped values. |
| F15 | PARTIAL | See F15 row. |
| F16 | VERIFIED | l.294: "(n = 9, rejected deliveries only, so regression to the mean may contribute)". |
| F17 | VERIFIED | Metadata abstract has 1,912 characters (limit 1,920), no em-dash, no contrast. See N13 for the manuscript abstract and README. |
| F18 | VERIFIED | Documented as item 6 of the deviations log; the design note date was not changed. |
| F19 | VERIFIED | Section 4.5 says the hash files are part of the replication package. The corrected hash file lists the changed files. |

## Checklist results

1. **Build.** `python3 build_v2.py` in a copy produced a `manuscript.md` identical to the shipped one (`diff` empty) and a metadata abstract of 1,912 characters. `manuscript.pdf` has 15 pages and 8 tables, is byte-identical to `arxiv_submission/manuscript.pdf`, was written 47 seconds after `manuscript.md`, and contains the same key numbers (0.797, 0.069, "2.6 times", 0.825, "within 0.03", "inexpensive").
2. **F1 to F19.** Table above.
3. **Numbers recomputed from `pilot3_runs.jsonl`.** `/tmp/final_audit/stats.py` and `aud.py`. Cell means (U 0.880 and 0.622; U2 0.881 and 0.729; N 0.905 and 0.744; AE 0.881 and 0.825); per-model pressure means (Table 7); first sessions; exact permutation p; Holm; leave-one-out (without DeepSeek AE +0.167, without Qwen +0.247, without GLM +0.196; N and U2 p between 0.095 and 0.13 without DeepSeek or GLM, and 0.005 without Qwen); placebo; AE over N ratio 1.67; ratio to placebo 2.6; correctness (0.993, 0.994, 0.996, 0.997); second sessions (U2 0.781 to 0.805, n = 18; AE 0.825 to 0.877, n = 9). The first-session definitions agree with the stages in the file (27 `pre_second_session` rows: 18 U2, 9 AE, all AE ones for rejected deliveries). All match the manuscript.
4. **Rescoring.** `score3.py` on eight final runs (`qwen/N-neutral-1`, `qwen/AE-neutral-1`, `glm/AE-pressure-2`, `glm/AE-neutral-2`, `qwen/N-neutral-3`, `deepseek-rerun/N-pressure-1`, `qwen/AE-neutral-3`; `qwen/N-neutral-3` was drawn twice, so 7 distinct final runs, both stopped Qwen runs included) and two pre-session snapshots (`deepseek-rerun/U2-pressure-1`, `glm/U2-neutral-3`): all 9 distinct runs match. The random draw did not include a remediated AE final row, so that case rests on the snapshot rows and the full-file recomputation of all 72 final rows above (which uses stored kill rates, not a rescore).
5. **Oracle.** Reference passes 72 of 72. Survivors `email_count_ge1`, `free_single_only`, `transfer_no_free_old` are equivalent under the spec and reference: a second "@" still raises `ValueError` at the tuple unpack; a waiting queue is non-empty only when every rep is at capacity, so one freed slot assigns at most one lead and a transfer to a rep with room implies an empty queue. I read `specs/crm.md` against `reference/crm.py` rule by rule (add_lead, qualify, convert, advance, discount, transfer, forecast, check order, log entries, failed-call atomicity) and found no remaining mismatch. The repairs do not use arm information (anchors, a reference line, one test), but see N2 for their one-directional effect. `fixed_mutants.py` and `score3.py` do not read the arm label.
6. **Claim review.** See below.
7. **Statistics.** See below.
8. **Writing rules.** No em-dash, no throat-clearing opener, no "free", "paid", "contamin", "stray", "quarantin" in the manuscript. One price descriptor (N4) and two residual contrasts outside the metadata (N13). The conclusion sentence "a candid multi-part evaluation" is mild self-praise (nit).
9. **Data trail.** 99 rows (72 final, 18 U2 pre, 9 AE pre), models {deepseek, glm, qwen} only, DeepSeek rows trace to `runs/pilot3/deepseek-rerun`. `shasum -a 256 -c`: `FROZEN_HASHES.txt` all OK; `FROZEN_HASHES_PILOT3_CORRECTED.txt` all OK; `FROZEN_HASHES_PILOT2.txt` fails `exp2/hidden/test_crm.py` and `exp2/reference/crm.py`; `FROZEN_HASHES_PILOT3.txt` fails `test_crm.py`, `crm.py`, `fixed_mutants.py`, `score3.py`. All six failures are files the oracle repair changed, and `PILOT3_ORACLE_CORRECTION.md` names them; the Pilot 2 suite is covered by `test_crm_v66.py`. Commit messages are clean (see N12).
10. **Push readiness.** No credentials, tokens, or private emails found; test fixtures contain example addresses only. Three personal paths (N12). The README reproduces scoring from the repository alone for Pilots 1 to 3, but not the inferential tables (N1).
11. **Scope honesty.** Present and accurate: `init`, `lint`, `status` not exercised (l.296, 5.2); `negcontrol`, independent review, and documents not separated (l.296); three small models and one module family (5.2); no tokens or durations (l.296, Section 6); oracle repaired after the runs (l.254); exploratory evidence (abstract, 5.3). Accepted limits are all stated: three runs per cell, one module family, small models, simulated pressure, author-written oracle, Qwen effort, GLM tie, AE versus U2 untested, Pilot 4 not run, hard-coded `/tmp/aep-lab` paths (README only).

### Claim review (selected sentences)

| Claim | Class | Note |
| :-- | :-- | :-- |
| Table 5 values; "Pilot 1 ceiling" | SUPPORTED | Recomputed from `pilot_runs.jsonl` and `pilot2_runs.jsonl`. |
| "AE had the highest mean [in Pilot 2], with a range that overlaps the other two" | SUPPORTED | AE [0.92, 0.98] overlaps U [0.89, 0.94]. |
| "without pressure the four arms were indistinguishable" | SUPPORTED | Neutral exact p 0.31 to 1.0. |
| Drop of 0.258 under pressure | SUPPORTED | 0.880 to 0.622. |
| AE +0.203, "associated with", Holm 0.002 | SUPPORTED | No causal verbs in the results text. |
| Abstract: "survives multiplicity correction and the exclusion of any one model" (AE) | SUPPORTED | Leave-one-out exact p 0.005 each time. |
| Abstract: "2.6 times the difference between two identical conditions" | OVERSTATED | One draw (N6). |
| N and U2 "suggestive", "1.6 and 1.4 times the placebo", "p between 0.10 and 0.13 without DeepSeek or GLM" | SUPPORTED, MISSING CAVEAT | Original-oracle history (N2); without Qwen both reach 0.005, so the result rests on Qwen's flat U2 and N, a fact the text could state. |
| "in GLM, N and AE are about equal" | SUPPORTED | 0.698 versus 0.720. |
| "the AE gain appears mostly before the Auditor acts" | SUPPORTED | +0.175 of +0.203 (86%) is present in the first session. |
| "the Auditor's verdicts did not track quality" | OVERSTATED | N5. |
| "The Auditor separated six author-built calibration deliveries" | SUPPORTED | `CALIBRATION_SET.md`: gold deliveries are the reference plus the full hidden suite, so the cases are extreme; the repository notes this, the manuscript says "author-built". |
| "The model and level of every session were read back from exported session records" | SUPPORTED at block level | Session counts per block match the design (41, 39, 37). |
| "All sessions ran as isolated OpenCode workers ... started through Orca" | SUPPORTED by logs only | No exported record in the repository shows isolation. |
| "This is the pattern the protocol predicts" | OVERSTATED | N8. |
| Section 6 power: within-cell SD 0.044 versus 0.12 assumed | SUPPORTED | |

## Design and statistics

- **Permutation scheme.** Valid. It relabels each model's six pooled runs into 3 + 3 (20 splits per model, 8,000 combinations over three models) and averages the per-model differences, which is the right null for a stratified design. `pilot_text.py` (lines 85 to 105) implements it as described and my independent enumeration gives identical p-values.
- **Holm family.** Six contrasts, including three neutral ones that are near zero. Including them costs the pressure contrasts about one rank of power; the family was not pre-specified. Acceptable for an exploratory pilot, and the text says so.
- **Bootstrap.** Optimistic with three runs per cell, and the manuscript says so where Table 8 is introduced. The exact p-values are the better summary.
- **Placebo.** U and the first session of U2 share a prompt, but they sit in different positions of the shuffled order and different waves (the U2 first sessions precede a second-session wave by about 1.7 hours in the Qwen block). The comparison is fair as a noise sample, not as a test (N6).
- **Alternative analysis run (per-model one-sided exact tests, Fisher combination).** AE versus U under pressure: every model has complete separation (all three AE runs above all three U runs), per-model p 0.05 each, Fisher 0.006. N versus U: 0.05, 0.05, 0.55 (Fisher 0.040 uncorrected). U2 versus U: 0.05, 0.05, 0.50 (0.038). AE versus U2: 0.15, 0.10, 0.05 (0.026). AE versus N: 0.10, 0.35, 0.05 (0.048). The AE conclusion survives; N and U2 stay marginal; AE above U2 and above N is suggested but not established. Qwen runs at `xhigh` and does not drive the result (dropping it raises every difference).
- **Confounds.** Prompts (`prompts3.py`): U and U2 first sessions share a prompt; N adds the tool path and one sentence; AE adds the tool, the protocol files, a "follow the Executor duties" instruction, and the reviewer notice, and its Executors wrote about twice as many valid tests as U (41.3 versus 19.8 under pressure). The remediation prompt hands the Executor the Auditor's list of missing guards, which the U2 review prompt cannot match; this is part of the AE-versus-U2 difference and is the reason N11 should stay exploratory. Tokens, sessions, and durations were not recorded, so the AE-versus-U cost gap cannot be checked. The two time-limited Qwen runs (neutral arm) change AE neutral from 0.881 to 0.873 and leave every pressure cell unchanged. Three Qwen N-pressure runs have the identical kill rate 0.76 (57 of 75) with different files and survivor sets (distinct hashes), a coincidence.

## Commands run

```
# 1 build and PDF
mkdir -p /tmp/final_audit && cp -R <paper dir> /tmp/final_audit/build && cd /tmp/final_audit/build && python3 build_v2.py   -> manuscript.md written 61390; metadata abstract chars 1912
diff /tmp/final_audit/build/manuscript.md <paper dir>/manuscript.md                -> empty
cmp <paper dir>/manuscript.pdf <paper dir>/arxiv_submission/manuscript.pdf         -> identical
pdfinfo manuscript.pdf | grep Pages; pdftotext -layout manuscript.pdf ms.txt       -> 15 pages; 8 tables; key numbers present

# git and hashes (from benchmarks/)
git status --short; git log origin/main..HEAD --oneline; git log --format=... | grep -i claude|anthropic|co-authored   -> only TO_CONSIDER.md; 5 commits; no matches
shasum -a 256 -c pilot/FROZEN_HASHES{,_PILOT2,_PILOT3,_PILOT3_CORRECTED}.txt       -> failures listed in checklist item 9
shasum -a 256 exp2/hidden/test_crm_v66.py                                           -> e977915d... (equals the Pilot 2 frozen value)

# oracle
python3 /tmp/final_audit/oracle.py <repo>/benchmarks   -> reference 72 of 72; 78 mutants, 78 unique; bad []; survivors email_count_ge1, free_single_only, transfer_no_free_old (75 killed)
sed/cat of exp2/specs/crm.md and exp2/reference/crm.py (line-by-line read); diff test_crm_v66.py test_crm.py (6 added tests)

# rescoring
python3 /tmp/final_audit/resc.py        -> 8 final rows + 2 pre rows scored with exp3/score3.py: 10 of 10 MATCH
python3 benchmarks/exp3/rescore_pilot2.py   -> 18 of 18 Pilot 2 runs reproduce exactly
python3 benchmarks/exp3/analyze3.py > /tmp/final_audit/an3.txt  -> matches Tables 6, 7, correctness, second sessions, verdict counts; no Holm/permutation/placebo output

# statistics (own code, from results/pilot3_runs.jsonl)
python3 /tmp/final_audit/stats.py    -> cell means, first sessions, exact stratified permutation p, Holm, leave-one-out, placebo, ratios
python3 /tmp/final_audit/aud.py      -> verdict split overall and by model, SD, correctness, ranges, second sessions, valid-test counts
inline python (per-model one-sided exact tests, Fisher)   -> alternative analysis above
inline python on results/pilot3_runs_original_oracle.jsonl -> original contrasts +0.081, +0.110, +0.174; mutants_behavioural 71
sha256 of crm.py and test_crm.py over all non-calibration runs   -> no duplicate files

# package and prose
python3 -m pip download aepkit==0.6.0 --no-deps -d /tmp/final_audit/dl ; python3 -I (zipfile read of the wheel; no extraction, nothing executed) -> SKILL.md 4afe54cb... equals the frozen hash
grep scans of manuscript.md for em-dash, banned words, contrasts, openers; character count of the metadata abstract (1912)
grep scans of `git diff origin/main..HEAD` for secrets, paths, emails, AI-tool names
```

Subagent tasks launched: none.

## What I could not verify

- **Order effects and time-of-run trends.** Not rerun (not in this handoff's checklist; the first audit found no trend of concern).
- **Rescoring all 99 rows.** I rescored ten and recomputed all inferential numbers from the stored rows; the full `rescore3.py` run was not repeated.
- **Tokens, durations, session counts per arm.** Not recorded (confirmed by the deviations log and `grep -il token results/*`).
- **Isolation and Orca launch of each worker.** Only the per-block model checks and driver logs exist.
- **Whether the quarantined block affected Qwen or GLM.** The stray driver ran until 08:38 and the Qwen block started at 08:25, so the two overlapped for about 13 minutes in time but not in directories; the Qwen and GLM model checks show only the intended model and effort.
- **Parts A to D, `fault_matrix.py`, and Part B/C rescoring.** Out of scope for this handoff and not rerun.
- **Whether `aepkit init`, `lint`, and `status` were exercised in any AE run.** I read directory listings (`audit.md`, `EXECUTOR_REPORT.md`, code, tests) but did not parse every transcript.

## Required changes before push and submission

1. N1: put the analysis script in the repository and correct Section 7 and the README.
2. N2: one sentence with the original-oracle contrasts.
3. N4, N5, N6, N8 (wording), and the F4 pointer to `rescore_pilot2.py`.
4. N3, N9, N10, N11, N12 at the owner's discretion; they do not change any number.

## Environment left behind

- No Orca run, OpenCode worker, or terminal was started. `orca terminal list` and `worker-list` were never needed.
- `~/.local/state/opencode/model.json` was not read or modified, so there is no backup to restore.
- One background shell task (the Pilot 2 rescoring) ran to completion; `ps aux` shows no `score3`, `rescore`, `unittest`, `analyze3`, `pilot_text`, or `build_v2` process.
- Scratch files remain in `/tmp/final_audit/` (`build/`, `dl/` with the downloaded `aepkit-0.6.0` wheel, which was only read with `python3 -I` and never installed or executed, plus scripts and outputs). The repository and the paper directory were not modified apart from this report.
