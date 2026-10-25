# Pilot 2 design note (written before launch)

Date: 2026-10-25. Pilot 1 (refunds, 18 runs) gave kill rate 1.000 in all six cells, so it could not show any effect of pressure or workflow (ceiling).
Only the task changes in Pilot 2. Everything else is identical: model (DeepSeek 4.1 Flash, effort High, via Orca opencode workers), workflows U/N/AE,
pressure paragraph (verbatim), 3 replicates per cell, scorer (`exp2/score.py`, unchanged hash), go/no-go rule.
New module: `crm.py` (lead intake, assignment with capacity and FIFO queue, qualification, conversion, stage machine, discounts with a cumulative floor,
transfers, forecast, atomic log). ~25 interacting rules versus 7 in refunds. Reference passes the 66-test hidden suite; the scorer finds 211 behavioural
mutants of 219 and the hidden suite kills all of them.
N-block guard list adapted to the module (see `session2.py`). No prompt tuning after seeing results.
