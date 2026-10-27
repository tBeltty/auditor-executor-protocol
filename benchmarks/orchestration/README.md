# Launch scripts of the pilots

These are the scripts that launched the agent sessions of Pilots 1 to 3 and collected their completion messages. They need a
coding-agent environment (OpenCode and Orca) and will not run unchanged on another machine: they use `/tmp/aep-lab` as the
working area, the OpenCode state file `~/.local/state/opencode/model.json`, and run identifiers of the original Orca runs.

| File | Used for |
| :-- | :-- |
| `pilot1_session.py`, `pilot1_launch.sh`, `pilot1_collect.py` | Pilot 1 (refunds): builds the prompt of one session, starts it as an Orca worker, collects completions |
| `pilot2_driver.py` | Pilot 2 (CRM) |
| `pilot3_driver_calibration.py` | Pilot 3, Auditor calibration (log: `results/pilot3_driver_calibration.log`) |
| `pilot3_driver_main.py` | Pilot 3, main blocks (log: `results/pilot3_driver_main.log`) |
| `pilot3_driver_deepseek_rerun.py` | Pilot 3, DeepSeek rerun (log: `results/pilot3_driver_deepseek_rerun.log`) |
| `check_launch_order.py` | Reproduces the recorded launch order of the three Pilot 3 blocks from the shuffle in the drivers |

How the files were obtained: the original files were in a temporary directory that no longer exists. The scripts were rebuilt
from the shell commands recorded when they were written and patched (creation of the file, then each in-place edit, in
order). The rebuilt `pilot3_driver_main.py` and `pilot3_driver_deepseek_rerun.py` reproduce the launch order of every
Executor session in their logs (`python3 check_launch_order.py`). That check does not prove that the rebuilt files are
byte-identical to the originals, and an edit that was not recorded would not appear here.

Changes made when publishing: the author's home directory in two paths was replaced by `~` (`BM` and the working directory
of the `opencode session` calls). Nothing else was altered.

Facts the scripts show:

- Pilot 3 shuffles the 24 cells of each model block with `random.Random(<block key>)`, where the key is the block name
  (`qwen`, `glm`, `deepseek-rerun`), and launches them in waves of six.
- `pilot1_session.py` carries a model argument (`MODEL`), but the Pilot 1 sessions were started as Orca workers with `pilot1_launch.sh`, which does not pass a model. The model of those sessions is the one OpenCode had selected, and the OpenCode session records show its identifier (`benchmarks/pilot/TOOL_PROVENANCE.md`).
- `pilot2_driver.py` and the Pilot 3 drivers do not pass a model either; the Pilot 3 drivers write the model selection to the
  OpenCode state file before each block.
