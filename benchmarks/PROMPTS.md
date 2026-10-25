# Prompts used for the agent runs

All runs: Claude Sonnet through Claude Code sub-agents, one fresh session per run, background
execution, one empty working directory per run, Python 3 standard library only, no network.
The sub-agents were told to stay inside their directory. This is a convention, not an OS sandbox.

## Part B, shared context (S and O)
A Python 3.11 monolith (SQLite database file, no message broker, no Redis, no containers deployed)
sends an HTTP webhook to a customer URL whenever an order is confirmed. Today it makes the HTTP call
synchronously inside the request. When the customer endpoint times out (10 s), worker threads block and
p99 order-confirmation latency reaches 14.2 s. Peak load is 40 webhooks per second, with bursts up to
100 per second for 10 seconds. Goal: order-confirmation p99 latency under 1.5 s and no webhook lost.

## Part B, S (spec-first SDD)
1) write spec.md (functional requirements, user stories, acceptance criteria); 2) write plan.md; 3) write
tasks.md, each task a line beginning "TASK <n>:"; 4) implement with unittest tests and run them until they
pass. The last line of plan.md must be "NEW_INFRA: <list or none>". Deliver working code.

## Part B, O (opportunity-shaping gate first)
BEFORE any spec, task list or code, write plan-of-record.md with: Target outcome (measurable); Problem /
friction; Cost of doing nothing; Explicit non-goals; three DISTINCT options A (minimal / existing tooling /
config-only), B (balanced / pragmatic), C (full architectural / custom build) each with rough LOC and new
infrastructure; Selected option and rationale (why the other two were rejected); Riskiest assumption and the
first-phase task that validates it. Then execution-guide.md (tasks as "TASK <n>:" lines with one verify
command), then code and tests. The last line of plan-of-record.md must be "NEW_INFRA: <list or none>".

## Part C, U (unstructured)
Read the spec in specs/<module>.md. Implement the module exactly as specified and write unit tests with
unittest in files named test_*.py. Run them and iterate until all pass.

## Part C, N (negative controls)
Same as U, plus: for EACH security guard, prove that your tests fail when the guard is removed, using
`aepkit negcontrol --file <module>.py --break-cmd "<removes the guard>" --test-cmd "<runs your tests>"
--expect "<regex>" --timeout 20`. A control passes (exit 0) only if the tests fail with the break applied,
the output matches --expect, and the tests pass after the byte-identical restore. If a control fails,
strengthen the tests and rerun until it exits 0. Append every command and its verbatim output to
negcontrol-log.md.
