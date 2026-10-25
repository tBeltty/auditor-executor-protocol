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
