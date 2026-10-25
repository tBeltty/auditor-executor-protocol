# Pilot 3 deviations log

1. Stray driver and contaminated DeepSeek block. During calibration, one Auditor (bad-1) wrote its audit but never reported completion. The first driver
   (`driver3.py`) was stopped with a pattern that did not match its process name, so it kept running and, after its wave timeout at 07:53, started a second
   DeepSeek block while the replacement driver (`driver3b.py`, started 07:39) was running the same cells in the same directories. Both agents therefore worked on the
   same cell directories at different times, so the first DeepSeek block is invalid. The stray driver was stopped at 08:38, its workers' terminals were closed, and
   all its data and the first DeepSeek block were moved to `results/quarantine/` and `runs/pilot3_quarantine/`. The DeepSeek block is rerun cleanly in fresh
   directories (`driver3c.py`, key `deepseek-rerun`) after the Qwen and GLM blocks. The Qwen block started at 08:25, after the stray driver's last model change,
   and the stray driver never changed `model.json` after 07:53; the per-block model check confirms the variant used.
2. Idle-done detection. Workers that finish their turn without sending `worker_done` are treated as finished after 120 s of reported activity "done".
3. Effort mapping. DeepSeek and GLM run at `high`; Qwen exposes no `high` and runs at `xhigh`, the nearest level above.
4. The hidden suite was strengthened from 66 to 71 tests before launch, so the `test_crm.py` hash recorded for Pilot 2 no longer matches the file (Pilot 2 used the 66-test version).
5. Oracle correction after the runs: see `PILOT3_ORACLE_CORRECTION.md`.
6. The design note carries the date 2026-10-26 while the run logs are dated 2026-10-25; the discrepancy comes from the local clock and has no other cause.
7. No token counts or session durations were recorded for any run.
8. The pre-second-session snapshots (U2 before the review, AE before the remediation) were copied into `runs/pilot3_pre/` after the runs so that those rows can be rescored.
