# Benchmarks for the paper

Every number in the paper's evaluation is read from a file in `results/`.

| Part | What | How to rerun |
|---|---|---|
| A | Executed fault-coverage matrix over released versions 0.4.0, 0.5.2, 0.6.0 | `python3 benchmarks/fault_matrix.py` (needs PyPI access) |
| B | 10 agent runs, spec-first vs shaping gate | prompts in `PROMPTS.md`, runs in `runs/e1/`, `python3 benchmarks/exp1/score_e1.py benchmarks/runs/e1` |
| C | 12 agent runs, with and without negative controls, scored by a generic AST mutation oracle and a hidden reference suite | runs in `runs/e2/`, `python3 benchmarks/exp2/score.py benchmarks/runs/e2/<run> <module>` |

Limits: the faults in Part A were written by the tool author, so the matrix shows which
mechanisms exist in each version, not effectiveness. Parts B and C are small (n = 5 and n = 2 per
cell), one model, and found no measurable effect. New agent runs will differ from the stored ones.

## Part E: pilots under completion pressure

| Pilot | What | Files | How to rerun the scoring |
|---|---|---|---|
| 1 | `refunds` module, 18 runs (U, N, AE x neutral, pressure x 3) | `runs/pilot/`, `results/pilot_runs.jsonl` | `python3 benchmarks/exp2/score.py benchmarks/runs/pilot/<run> refunds` |
| 2 | CRM module, 18 runs, same design | `runs/pilot2/`, `results/pilot2_runs.jsonl` | `python3 benchmarks/exp3/rescore_pilot2.py` (uses the 66-test suite `exp2/hidden/test_crm_v66.py`, sha256 in `pilot/FROZEN_HASHES_PILOT2.txt`) |
| 3 | CRM module, 3 models x 4 arms x 2 conditions x 3 replicates = 72 Executor runs, plus second sessions | `runs/pilot3/`, `runs/pilot3_pre/` (snapshots before the second session), `results/pilot3_runs.jsonl` | `python3 benchmarks/exp3/score3.py benchmarks/runs/pilot3/<model>/<run>`; all rows: `python3 benchmarks/exp3/rescore3.py`; tables: `python3 benchmarks/exp3/analyze3.py` |

Environment for new runs: Python 3 standard library; `aepkit` 0.6.0 in a virtual environment (`pip install aepkit==0.6.0`); the CRM spec copied to `/tmp/aep-lab/specs/crm.md`; the protocol files from `aepkit/skill/` copied to `/tmp/aep-lab/protocol/` (their hash is in `pilot/FROZEN_HASHES_PILOT3.txt`). The prompts in `exp3/prompts3.py` hard-code those paths. Scoring needs none of that: `score3.py` reads only the run directory, `exp2/reference/crm.py`, `exp2/hidden/test_crm.py`, and `exp3/fixed_mutants.py`.

Order of documents to read: `pilot/PILOT3_DESIGN_NOTE.md` (written before the runs), `pilot/PILOT3_DEVIATIONS.md`, `pilot/PILOT3_ORACLE_CORRECTION.md` (post-run repair of the oracle, with original and corrected rows), `pilot/CALIBRATION_SET.md`, `results/PILOT3_SUMMARY.md`, `pilot/BACKLOG_PILOT4.md`.
Not recorded: token counts and session durations per run.
