# Response to AUDIT_REPORT_FINAL.md (verdict: ready after minor fixes)

| id | action |
| :-- | :-- |
| N1 | Fixed. The analysis module is released as `benchmarks/exp3/paper_analysis.py` (path-independent, prints Tables 5 to 8, placebo, leave-one-model-out, original-oracle contrasts). Section 7 and the README name it. |
| N2 | Fixed. Section 4.5 (Outcomes) now reports the pressure differences under the original oracle (+0.081, +0.110, +0.174) and that only AE survived Holm correction then. |
| N3 | Owner decision: the invalidated first DeepSeek block stays documented in the repository (`pilot/PILOT3_DEVIATIONS.md`, `results/quarantine/`) and is not described in the paper. |
| N4 | Fixed. "inexpensive" removed. |
| N5 | Fixed. Verdict-versus-quality wording changed to "could not be related", with the within-model cell sizes. |
| N6 | Fixed. The placebo is described as a single noise draw; "survives a placebo comparison" removed. |
| N7 | Fixed. The Qwen spread is computed (0.04). |
| N8 | Fixed. The sentence "the pattern the protocol predicts" is replaced by a statement that the timing points to the documents and the reviewer notice. |
| N9 | Fixed. Pilots 1 and 2 model and level stated. |
| N10 | Fixed in the preregistration copy: models, adjustments (R arm, U2, documents, multi-phase task), Holm family H1 to H5, go/no-go section marked completed. The run count remains the draft design and is flagged for recomputation. |
| N11 | Fixed. Exploratory AE minus U2 (+0.096, exact p 0.004) and AE minus N (+0.081, p 0.008) reported in 4.5, uncorrected and not planned. |
| N12 | Three personal paths replaced in `pilot/audit/HANDOFF_AUDIT.md`. Five local commits are ahead of origin (the first one holds the fault matrix); the owner pushes. |
| N13, N14 | Fixed. Abstract wording matches the metadata wording; the abstract says `init`, `lint`, and `status` were not exercised; docstring softened. |
| F4 | Fixed. Section 7 names `rescore_pilot2.py` and `rescore3.py`. |
| F10 | Disclosed in Section 7 (timeouts and absent valid tests count as kills; neither occurred in the rescored runs). |
| F15 | Hashes of the four reference files added in `pilot/SKILL_REFERENCE_HASHES.txt`. The hard-coded `/tmp/aep-lab` paths in the agent prompts remain and are documented in the README. |

Build after the fixes: `manuscript.md` regenerated, metadata abstract 1,906 characters, PDF 16 pages (the reference list spills to a short last page); metadata updated.
