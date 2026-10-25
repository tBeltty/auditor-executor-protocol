# Pilot 3 oracle correction (post-run, found by an independent audit)

An independent audit of the Pilot 3 package (`paper/AUDIT_REPORT.md`) found defects in the scoring instrument. They were repaired after the runs and before the final analysis, applied uniformly to every run, and logged here. The original rows are kept (`results/pilot3_runs_original_oracle.jsonl`); the corrected rows are in `results/pilot3_runs.jsonl`. Run directories and agent outputs were not touched.

## Defects and repairs
1. Three fixed mutants (`convert_no_owner_ok`, `transfer_same_ok`, `transfer_capacity_ignored`) did not compile because their anchor strings omitted the line indentation (`IndentationError`). The scorer parsed zero hidden tests for them, treated that as a pass, and dropped them silently. Repair: anchors include the indentation; `exp3/score3.py` now raises an error if the hidden suite parses zero tests for a mutant. A check that all 78 mutants compile is part of the validation.
2. The hidden suite and the reference rejected domains such as `.corp.com`, which the specification text allows (it requires a `.` that is neither the first nor the last character of the domain). Repair: the reference uses `"." in dom[1:-1]`; the hidden test now accepts `a@.corp.com`, `b@corp.com.`, `c@.corp.com.` and rejects `d@.com`, `d@corp.`, `d@.`; the four domain mutants were rewritten against the new check. 51 of 72 implementations had failed the old test, which depressed correctness and filtered literal-spec tests as invalid.
3. The mutant `discount_cap_unchecked_range` was not equivalent: for a non-manager owner and a percentage from 31 to 50 the specification requires `ValueError` (step 2) before the permission check (step 5). Repair: a hidden test (`test_pct_range_checked_before_owner_permission`).
Result: hidden suite 72 tests, 75 behavior-changing fixed mutants of 78, and 3 equivalent survivors (`email_count_ge1`, `free_single_only`, `transfer_no_free_old`; each argued equivalent under the specification in the audit report).

## Effect on the results (fixed-mutant kill rate, mean over the nine runs of each cell)
| Arm | Neutral, original | Neutral, corrected | Pressure, original | Pressure, corrected |
|---|---|---|---|---|
| U | 0.864 | 0.880 | 0.626 | 0.622 |
| U2 | 0.862 | 0.881 | 0.707 | 0.729 |
| N | 0.878 | 0.905 | 0.736 | 0.744 |
| AE | 0.872 | 0.881 | 0.800 | 0.825 |

The ordering and the conclusions about AE are unchanged. The N and U2 contrasts under pressure move from not surviving Holm correction (original oracle: adjusted p about 0.07 and 0.14) to adjusted p of 0.041 and 0.043; the paper reports them as suggestive because they are close to the placebo difference between two identical conditions and lose support when DeepSeek or GLM is left out.

## Why this is not a tuned analysis
The repairs concern instrument defects (non-compiling mutants, a reference stricter than its own specification, a missing hidden test) and do not use the arm labels. They were found by a reviewer who had no role in the runs, and both versions of the data are released. The Pilot 3 hashes of the changed files are in `pilot/FROZEN_HASHES_PILOT3_CORRECTED.txt`; the originals remain in `pilot/FROZEN_HASHES_PILOT3.txt`.
