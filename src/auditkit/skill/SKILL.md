---
name: auditor-executor-protocol
description: "Runs multi-phase work as a two-role protocol: an Auditor who writes numbered, verifiable tasks and signs off phases, and an Executor who implements one task at a time and reports evidence. Use whenever a piece of work is large enough to span several phases or sessions, whenever handing a plan to another agent (subagent, spawned session, or a different tool) to implement, or when asked to audit/verify work another agent reports as complete. Also use when a plan needs to become executable instructions rather than a discussion document. Covers: the document set, rules of engagement, task and gate format, how to audit by re-running rather than reading, negative controls, verdict vocabulary, the annex pattern for correcting an order that is already in flight, and an optional operating mode chosen per run — Guided (the owner relays each handoff) or Autonomous (the Auditor launches Executors as subagents with an explicit per-task model tier, answers their BLOCKED questions itself, and interrupts the owner only for a numbered critical-risk list). Triggers: 'audit', 'auditor', 'executor', 'phased plan', 'exit criteria', 'gate', 'compliance log', 'remediation', 'handoff', 'have another agent implement this', 'verify what was reported', 'sign off', 'autonomous mode', 'guided mode'. NOT for reviewing a diff or a pull request for bugs — that's a code review; this protocol audits an execution report against pre-declared gates, and governs how multi-phase work is handed off and signed off."
---

# Auditor / Executor Protocol

Two roles, one paper trail. The Auditor decides what "done" means and proves it
independently. The Executor implements and reports evidence. Neither does the other's job.

This exists because a plan handed to an implementing agent is not instructions until
someone makes it unambiguous, and a report that says "all green" is not verification
until someone re-runs it. Both failures are common and both are expensive once they
compound across dozens of tasks.

A companion CLI, `auditkit`, operationalizes the mechanical parts of this: scaffolding
the document set, checking the task list and the log agree with each other, running a
negative control end to end, and printing where a run stands. Use it if it's installed;
follow this document either way.

## When to use this

- Work spanning more than one phase or more than one session.
- Handing a plan to another agent to implement — a subagent, a spawned session, a
  different tool, another person.
- Auditing work someone else reports as complete.
- Turning a roadmap into something executable.

Not for single-session tasks you are doing yourself. The overhead only pays off when the
implementer is not the person who wrote the plan.

## The two roles

| | Auditor | Executor |
|---|---|---|
| Owns | The instructions, the gates, the verdicts | The implementation, the evidence |
| Never | Writes feature code | Redesigns, or decides scope |
| Output | Task expansions, verdicts, remediation orders | Working code, pasted command output |

Whoever writes the plan is the Auditor. Say which role you are holding at the start of a
session so it does not drift.

## Reference files (load on demand)

The core rules are in this file. Load a reference file only when you reach the step it
covers; each one is self-contained and refers back to sections of this file by name.

| File | Load when |
|---|---|
| [`references/tasks-and-gates.md`](references/tasks-and-gates.md) | Writing a task or a gate (Auditor) |
| [`references/handoffs.md`](references/handoffs.md) | Handing a task to an Executor, or writing a remediation after a verdict that is not a clean `APPROVED` (Auditor) |
| [`references/autonomous-mode.md`](references/autonomous-mode.md) | The run is in Autonomous mode, or you are writing the Auditor brief that starts one |
| [`references/failure-modes-and-example.md`](references/failure-modes-and-example.md) | Auditing a delivery, or you want to see a filled-in run end to end |

## Operating mode: Guided or Autonomous (chosen at the start of the run)

The mode is optional and the owner's choice. Two ways to run the protocol:

| | Guided mode | Autonomous mode |
|---|---|---|
| Who launches Executors | The owner pastes each handoff into a fresh session | The Auditor, as subagents |
| Who answers `BLOCKED` | The owner, or the Auditor through the owner | The Auditor, with a decision entry in the log |
| Owner's role | Relays every message, sees every verdict | Receives one short report per closed phase; interrupted only for the critical-risk list |
| Fits when | The owner wants to watch and approve each step, the work is new territory, or the Auditor has no subagent tool | The plan is settled and the owner wants it run end to end |

How the mode is chosen:

- **If the owner already named it** ("autonomous", "guided", or an unambiguous
  equivalent like "don't interrupt me for every step"), use it. Do not ask again.
- **If not, ask once, before task 1**, as a single two-option question with a one-line
  recommendation (Guided for a first run in unfamiliar code or anything touching money
  or production data with no rehearsal; Autonomous for a settled plan with strong gates).
  This is one of the few questions that is genuinely the owner's: it decides how often
  they get interrupted for the rest of the run.
- **If the environment has no subagent tool**, Autonomous is not available; say so and
  run Guided.
- Record the choice as a governance decision in the plan of record, next to the rules of
  engagement. Switching modes mid-run is allowed only when the owner asks, and is
  recorded by annex. The Auditor never switches itself from Guided to Autonomous; it may
  drop from Autonomous to Guided only through an item on the critical-risk list.

Everything else in this document applies to both modes. Autonomous mode adds the rules in
`references/autonomous-mode.md`; it removes none. Re-running, negative controls and separate
process/code findings matter more when nobody is watching, not less.

## The document set

Four documents. Keep them separate; merging them is how the instructions turn back into
a discussion.

1. **Plan of record** — the *what* and the *why*. Phases, decisions, trade-offs. Nobody
   implements from this. Carries the **deferred items ledger** (below).
2. **Execution guide** — the *how*. Numbered tasks (`P<phase>-T<n>`, or any scheme with a
   stable, greppable ID), each with files, steps, a verification command, and its
   expected output. Gates (`P<phase>-G<n>`) close each phase. Carries the
   **reserved-to-Auditor steps** list (below).
3. **Compliance log** — where the Executor reports. Pre-generate one empty row per task
   and gate ID so nothing can be quietly skipped.
4. **Remediation order (annex)** — written by the Auditor after an audit that isn't a
   clean `APPROVED`. Self-contained: the Executor must not need the audit conversation
   or the full log to act on it. Template and reasoning: "Remediation handoff" in `references/handoffs.md`.

**Annexes** supersede a document that is already open in the Executor's session. Never
edit an order in flight — issue a new annex, and say at the top which item it replaces.

`auditkit init <dir>` scaffolds the first three as empty templates plus an empty
`annexes/` directory for the fourth.

### The deferred items ledger (in the plan of record)

A single running table, not prose scattered across the log:

```
| ID | What | Deferred to | Closed by |
|---|---|---|---|
| D14 | Move the export job into the reporting module | P5 | — |
```

Every decision (or annex) that pushes work to a future phase gets a row here the moment
it's made, in the same edit. **Before drafting any phase's tasks, read this table for
rows whose "Deferred to" matches the phase being drafted** — not a grep of the whole log
from memory. A row stays open until a task ID appears in "Closed by." An open row for a
phase that's about to be marked done is a stop, not a note for later: a promise made in
an early phase and never carried into the later phase's own task expansion is easy to
lose track of across a long run, and expensive to recover once several phases have
already closed on top of it. The ledger exists so that promise is a row someone has to
close, not a sentence someone has to remember.

### The reserved-to-Auditor steps list (in the execution guide)

A running list, next to the rules of engagement, not a per-task Observations note:

```
Steps reserved to the Auditor (never the Executor's model tier, whatever it is):
- The credential-adjacent check after a ship task (blocked for every model tier so far).
- Any commit touching a shared or generated resource (harness blocks it for every tier).
```

The first time a harness or permission block turns out predictable — same step, blocked
for every Executor tried — add it here once. Every subsequent handoff whose task includes
that step cites this list instead of the step being rediscovered as a fresh `BLOCKED`
each time. A note written into one task's Observations after the first occurrence is read
once and never again; this list is read on every handoff.

## Rules of engagement (the Executor follows these)

Put these at the head of the execution guide, ordered by how often they get broken.
Items 1-7 are fixed — copy them as they are. **Item 8 is not written from memory or
inherited from a different run; it is the first concrete step of starting a new run,
done before task 1 is drafted:**

- Check whether this codebase or team already states these somewhere authoritative — a
  CONTRIBUTING file, CI config, an existing style guide, a prior run's execution guide.
  If so, cite it; do not restate it.
- If nothing authoritative exists, **look at the project before asking** — grep for
  what's already there rather than handing the user a blank checklist:

  | Rule | Look for |
  |---|---|
  | Version bump per change | A version field (`package.json`, `pyproject.toml`, a `VERSION` file) and any script that already bumps it |
  | No AI co-author trailers | `git log --grep="Co-Authored-By"` — existing trailers (or their consistent absence) |
  | Fetch-before-push | Multiple contributors or branches in `git log`/`git branch -a` — a solo, single-branch repo needs this less |
  | Quality gate green before push | CI config (`.github/workflows/`, `.gitlab-ci.yml`) or a `test`/`lint`/`build` script already wired together |
  | i18n/locale parity | A locales/translations directory with more than one language file |
  | Dependency lockstep | A lockfile and how strict its existing commit history is about touching it |

  **Then ask with the finding attached, not a blank menu** — turn each hit into a
  yes/no the user can answer in one word instead of a checklist they have to reason
  through from nothing: *"Found `package.json` version `0.2.1` and no bump script — want
  every task to bump it, and if so, how (semver rule, or you decide per task)?"* /
  *"No CI config found — is there a command that should gate every push, or does this
  repo not have one yet?"* This matters most for a user who isn't deep in the codebase
  themselves (vibe-coding a project, not maintaining one they know by heart) — inspecting
  first is the difference between a real choice and homework.
  A rule with nothing detected for it is still offered, just without a finding attached.
- **Custom rules stay first-class** — a rule is usable as item 8 once it names what it
  enforces, how it's checked, and what triggers it, whether or not it came from the
  table above. Example: *"No schema migration touches a table over 10k rows without a
  stated rollback plan in the task text, and the migration is run once with `--dry-run`
  before it lands for real."* Names the trigger (a migration over the row threshold),
  the requirement (a rollback plan, in the task text), and the check (`--dry-run` first).
- Settle it once, at the start of the run. Item 8 does not change task to task.

1. **One task at a time, in order.** No batching. No starting a phase whose predecessor
   is not `APPROVED`.
2. **Never invent a value the codebase, infra, or environment declares.** Ports, origins,
   domains, permission keys, versions, enum members — read them. Needing to ask for one
   means a file was skipped.
3. **Never guess a cause. Observe it.** Read the log, run the query, print the value.
   When investigating a claim about the code, prefer whatever fast navigation tool this
   project already has over blind grep — a code graph, ctags, an LSP, anything that
   answers "who else reads this" faster than a full-text search. Never assume one is
   installed or working; grep is the guaranteed fallback, not a default to reach past a
   faster tool for. This check is quiet, not a topic — look, then use whatever's there.
   Finding nothing is not itself worth telling the user; only bring it up if a tool was
   found and is why the next command looks unusual.
4. **Verification is running the thing, not reading the code.** "I reviewed it and it
   looks correct" is reported as `FAILED`.
5. **Scope is the task text.** Note unrelated problems in *Observations*; do not fix
   them.
6. **Stop and ask** when the instruction contradicts the code, when a task needs a
   decision the document does not make, or when a previously passing check starts
   failing for reasons unrelated to the change. An empty "Blocked" section across a
   whole run reads as ambiguities resolved silently, not as ambiguities that never
   existed. If you resolve one without stopping, log the decision.
7. **When the system cannot do what a task asks, that is the deliverable.** Report it
   and stop. A task that ends in a well-argued finding is a success.
8. Project-specific rules go here: version bumping, commit attribution, dependency
   sync before pushing, i18n parity, design-system checks, whatever this codebase
   already enforces elsewhere. Cite the source file instead of restating it — one
   source of truth. **Settled above, before task 1 — not filled in retroactively.**

## Before expanding a phase into tasks

Read the deferred items ledger (above) for rows whose "Deferred to" matches the phase
about to be drafted. Every open row becomes a task, or gets re-deferred by editing the
row — never dropped silently. This replaces re-deriving the phase's obligations from
memory or a fresh grep of the whole log; the ledger is what makes that unnecessary.

## Reporting back (Executor)

A compliance log entry is not addressed to anyone — it is a record. When a task, or the
last task of a phase, is done, close with a message back to the Auditor, same reasoning
as the handoff that started the work: whoever picks up the audit may be a fresh session
too, with nothing but the log to go on unless this exists.

```
ROLE: Executor, reporting on <TASK-ID or "Phase <n>, tasks <first>-<last>">.

STATUS: <DONE | BLOCKED | FAILED> — logged in <COMPLIANCE_LOG>, section(s) already
filled in with literal command output.

Verify results: <the one-line summary an Auditor would want before deciding whether to
re-run everything themselves — not a substitute for that re-run>.

Deviations from the task text: <any, with the reasoning — or "none">.

Stops logged: <any "Blocked" entries raised mid-task per rule 6 — or "none">.

Ready for: <"Audit of Phase <n>" | "the next task, <ID>, once this is reviewed">.
```

Do not narrate confidence ("this should be solid now") in place of the verify results —
the Auditor is about to re-run everything regardless (rule 4 applies to them too); a
report's job is to point at the evidence, not to argue for a verdict.

## Auditing (Auditor)

**Re-run. Do not read the report and agree with it.**

1. Run every suite yourself, with the project's own commands. A wrong invocation
   produces a false failure and destroys your credibility for the rest of the audit —
   confirm you're running from the right directory, against the right environment,
   before treating an error as a finding.
2. Re-execute the negative controls from scratch. Back the file up before mutating it
   and restore from that copy — never with a source-control command that could discard
   other uncommitted work in the same tree.
3. Check artifacts exist: migrations, screenshots, specs, generated bundles.
4. Read the checks, not just their names. Ask what ordering or fixture would make a
   passing check pass for the wrong reason.
5. **Write a probe when a claim is load-bearing.** A temporary check that asserts the
   opposite of what the delivered one asserts tells you in thirty seconds whether the
   behavior is real. Delete it afterward.
6. Check timestamps before concluding something is missing. Work may have landed after
   you looked.
7. **A delivered negative control only proves the failure mode it was built to catch.**
   Before signing a task off, ask what other claim in the same delivery is load-bearing
   and has no probe of its own — do not accept the one control that exists as coverage
   for the whole feature.
8. **Before sending the verdict, check what it's missing, not just what it says.** This
   applies to every verdict, not only a full-phase `APPROVED` or a `CONDITIONAL`/
   `REJECTED` with an obvious remediation — a plain `PASS` on one task, mid-phase, with
   something else already outstanding (an earlier remediation, the next task) needs the
   same discipline: it does not end the message on its own. If anything is left to do —
   a remediation handoff, the next task's handoff, or a re-statement of a handoff already
   sent but not yet acted on — it ships in the same message as the verdict, as the
   literal pasteable block from `references/handoffs.md`, not a sentence describing that
   it's still pending. A verdict is not the deliverable; see "Remediation handoff" in
   `references/handoffs.md`. In Autonomous mode, "ships in the same message" means the
   Auditor launches that subagent in the same turn.

### Verdicts

| Verdict | Meaning |
|---|---|
| `APPROVED` | Every gate independently verified |
| `CONDITIONAL` | Accepted except for named items; state which and what closes them |
| `REJECTED` | The deliverable does not do what it claims, even if it is green |

A passing check that documents wrong behavior as correct is a **rejection**, not an
observation. It will defend the defect against whoever tries to fix it later.

Separate **process findings** from **code findings**. Work can be accepted on its
merits while the control that should have caught a defect is recorded as failed. Good
outcomes do not validate a broken process backward. A condition holds as written or it
stays open — do not fold an unmet condition into "recorded, not blocking" just to avoid
holding up a phase; that turns a defect into paperwork. Process findings include: the
wrong model tier (or an inherited one), a small-model task that improvised instead of
escalating, a negative control restored with a command that discarded other uncommitted
work, and a question sent to the owner that belonged to the Auditor.

### Closing the run

A verdict says whether one phase or task passed. It does not say whether the *run* is
over — those are different claims, and leaving the second one to tone or inference
means the user ends up asking "so is that everything?" directly, which is the signal
this section exists to make unnecessary.

Before saying a run is over, check the plan of record itself for a phase that exists on
paper but was never turned into tasks — not just for a next task in the current
execution guide. A phase can be planned and never scheduled; "nothing left in the guide
I'm looking at" and "nothing left in the plan" are not the same check.

When every phase is `APPROVED` and the plan of record declares no further phase, say so
as its own line, not folded into other prose:

```
RUN COMPLETE — <plan of record name>. Every phase APPROVED. No further phase declared.
Nothing outstanding.
```

Anything short of that — one phase closing, a conditional approval, work still queued —
uses the verdict-plus-handoff shapes in `references/handoffs.md` instead. `RUN COMPLETE` is reserved for the
one message that actually ends the need for another Auditor turn on this plan of record.

## The Auditor is bound by rule 4 too

An order can be wrong in the same way a delivery can be wrong, and it is more
dangerous when it is: the Executor is told a decided item is a stop, not a choice, so a
wrong decided item arrives armored against the one person positioned to catch it.

The failure has one shape: the Auditor asserted a fact about the system — a field
exists, a function behaves a certain way, a value has a certain sign — from reasoning
or a single grep hit, without running the command that would actually confirm it.
**Deliveries get audited by running them; orders too often get written by reasoning
about them.** That asymmetry is the whole problem.

Two rules close it:

**1. An order may not assert what it has not run.** Any claim in an order about a
field, a function's behavior, or a runtime value carries the command that established
it, pasted, in the order. Rule 4 above — *verification is running the thing, not
reading the code* — is not only the Executor's rule. It is the protocol's. If the
Auditor cannot paste the command, the Auditor cannot assert the fact; it goes in the
order as a question for the Executor to establish, not as a decision.

For anything touching money, permissions, or schema, the cheapest form of this is a
falsifying probe: write the smallest script that would prove the claim wrong and run
it before the order goes out.

**2. A decided item is not reopenable; a factual claim always is.**

| | Reopenable by the Executor? |
|---|---|
| A decision — scope, trade-off, design | **No.** Believing otherwise is a stop. |
| A factual claim — this field exists, this function does X, this value is Y | **Always**, with a pasted command that contradicts it. The evidence outranks the order. |

An Executor who runs a command that falsifies an order is not exceeding scope; that is
the second pair of eyes the arrangement exists to buy.

## Maintaining the log

A compliance log that only ever gets appended to accumulates duplicate paragraphs —
the same open condition re-stated verbatim across several entries because it was
easier to copy the last summary than to write a new one. That is a cost, not a
neutral habit: it makes the current state of the run more expensive to find for
whoever reads it next, human or agent. Compact the log periodically — collapse a
condition that has appeared unchanged across several entries into one current
statement with a pointer to when it opened. `auditkit lint` flags near-duplicate
paragraphs so this doesn't have to be caught by eye.

**Annex count is a health signal, not just a history.** A phase that accumulates many
corrections after work started is a phase whose plan was under-verified before work
started, more often than it is a phase that hit genuine surprises. If one phase is
generating annexes faster than the others, that is worth naming as a finding about the
planning step, not only fixing task by task. `auditkit lint` warns past a configurable
threshold.

## Repo conventions this rides on

Cite whatever this codebase already enforces — version bumping, commit attribution,
fetch-before-push, environment-value discipline, evidence-driven debugging — from its
own source of truth rather than restating it here, so there's one place it can drift
out of sync from.

## The CLI

If `auditkit` is installed, prefer it over doing these by hand:

- `auditkit init <dir>` — scaffold the plan of record, execution guide, and compliance
  log from templates, plus an empty `annexes/` directory.
- `auditkit lint <dir>` — cross-check task IDs between the execution guide and the
  compliance log in both directions, flag `DONE` reports with no pasted verify output,
  flag near-duplicate paragraphs, warn on annex count per phase, flag gates with no
  stated negative control (a negated mention such as "n/a" does not count). Missing
  documents are an error, not a clean result.
- `auditkit negcontrol --file <path> --break-cmd "<cmd>" --test-cmd "<cmd>"` — backs the
  file up, runs the break command, runs the test (expects failure), restores from the
  backup, runs the test again (expects success), and prints a paste-ready transcript.
  With `--restore-cmd`, the file must still end byte-identical to the backup or it is
  restored from it; `--timeout` bounds each command.
- `auditkit status <dir>` — combines the status board verdicts with the latest report
  per ID and prints what's still open. Only `APPROVED` closes an item; a `DONE` with no
  verdict is listed as awaiting audit.

See the repo's `README.md` for install instructions.
