---
name: auditor-executor-protocol
description: "Runs multi-phase work as a two-role protocol: an Auditor who writes numbered, verifiable tasks and signs off phases, and an Executor who implements one task at a time and reports evidence. Use whenever a piece of work is large enough to span several phases or sessions, whenever handing a plan to another agent (subagent, spawned session, or a different tool) to implement, or when asked to audit/verify work another agent reports as complete. Also use when a plan needs to become executable instructions rather than a discussion document. Covers: the document set, rules of engagement, task and gate format, how to audit by re-running rather than reading, negative controls, verdict vocabulary, and the annex pattern for correcting an order that is already in flight. Triggers: 'audit', 'auditor', 'executor', 'phased plan', 'exit criteria', 'gate', 'compliance log', 'remediation', 'handoff', 'have another agent implement this', 'verify what was reported', 'sign off'. NOT for reviewing a diff or a pull request for bugs — that's a code review; this protocol audits an execution report against pre-declared gates, and governs how multi-phase work is handed off and signed off."
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

## The document set

Four documents. Keep them separate; merging them is how the instructions turn back into
a discussion.

1. **Plan of record** — the *what* and the *why*. Phases, decisions, trade-offs. Nobody
   implements from this.
2. **Execution guide** — the *how*. Numbered tasks (`P<phase>-T<n>`, or any scheme with a
   stable, greppable ID), each with files, steps, a verification command, and its
   expected output. Gates (`P<phase>-G<n>`) close each phase.
3. **Compliance log** — where the Executor reports. Pre-generate one empty row per task
   and gate ID so nothing can be quietly skipped.
4. **Remediation order (annex)** — written by the Auditor after an audit that isn't a
   clean `APPROVED`. Self-contained: the Executor must not need the audit conversation
   or the full log to act on it. Template and reasoning: "Remediation handoff" below.

**Annexes** supersede a document that is already open in the Executor's session. Never
edit an order in flight — issue a new annex, and say at the top which item it replaces.

`auditkit init <dir>` scaffolds all four as empty templates.

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

## Writing a task (Auditor)

```
### <TASK-ID> — <imperative, one line>

**Goal:** one sentence. What is true after this that was not before.
**Files:** every path the Executor should read or change.
**Steps:** numbered. Exact enough that two Executors produce the same thing.
**Verify:** the literal command, and the output that counts as success.
**Report:** the task ID.
```

Rules for the steps:

- Encode decisions, do not re-open them. "Polling, not a push channel — this is
  decided, believing otherwise is a stop, not a choice to make while implementing."
- **Name the failure you expect.** If a field might get overwritten, if a type behaves
  differently across two environments, if a cap is a layout decision and not a data
  one — say so in the task. Most bad output comes from an ambiguity the task's author
  already saw and didn't write down.
- State what must *not* change alongside what must.
- **When a task changes what an existing field or column means** (not just adds one),
  the task text must include the command to find every other reader of that field —
  and the Executor must run it and account for every hit, not only the call sites the
  task's own file list happened to name. A task's file list is a lower bound on its
  blast radius, discovered by the person who wrote the task before the work started —
  not the whole of it, discovered later by whoever happens to hit the stale reader
  next.
- **When a task changes what triggers an automatic action** (a scheduler, a background
  job, a materializer, anything that can fire without a human pressing a button), the
  task must require checking — before shipping — what state the change leaves the
  system in and whether anything is now primed to fire destructively on its next
  ordinary trigger. Passing tests prove the new code path is correct; they do not
  prove nothing is about to run against real data the moment it gets the chance.

## Writing a gate (Auditor)

A gate is a claim that can be proven false. "Tests pass" is not a gate. "The
visibility check was observed failing with the filter removed" is.

Every gate names how it is proven. Include, whenever the phase produces a security,
privacy, or financial-integrity boundary, a **negative control**: the Executor must
remove the protection, observe the check fail, restore it, and observe it pass. A
check never seen failing has not been verified. `auditkit negcontrol` runs this
sequence and produces a paste-ready transcript.

## Handing off a task (Auditor)

Writing the execution guide is not the handoff. The Executor's session starts cold — it
has none of the investigation behind the guide, and "read the execution guide, task
`<ID>`" is a pointer to an instruction, not the instruction itself. Producing the actual,
paste-ready message for a fresh Executor session is Auditor work, not something left for
whoever is relaying the plan to assemble by hand.

**The rules-of-engagement block in the template below is item 8, settled when the run
started** ("Rules of engagement" above) — not re-derived here, and not re-asked per
task. If you're about to write a handoff and item 8 is still blank, that's the actual
problem: go settle it before drafting the message, don't paste a rule set from a
different project or a different run to fill the gap. A rule copied in from elsewhere
either asserts something false about this codebase or hands the Executor a stop it has
no way to satisfy.

### Handoff template

One task per message, addressed to a fresh Executor session with no shared context. Fill
every section — do not leave "see the execution guide" where a fact belongs.

```
ROLE: Executor. Work from <EXECUTION_GUIDE> (Phase <n>, `<TASK-ID>`) only; report in
<COMPLIANCE_LOG>, section `<TASK-ID>` (already exists, empty).

REPORTED STATE: <what is already DONE in the log, and whether it was audited or only
self-reported — do not conflate the two>. Do not reopen <prior tasks>.

TASK: <TASK-ID> — <imperative title>
Source: <EXECUTION_GUIDE>, section "<TASK-ID>" in full.

Goal: <one sentence — what is true after this that was not before>.

Key finding (already verified, do not re-check it): <the concrete fact driving this
task, with the file/line/command that established it>.

Decided points, not reopenable without evidence that contradicts them:
1. <decision>
2. <decision>
...

Failure to avoid explicitly: <the specific mistake a context-free Executor would make by
reflex — copying a neighboring task's filter that doesn't apply here, re-deriving a
fact that was already established and getting it wrong, etc.>.

Verify (literal):
<exact command>

Success, minimum: <what the check(s) must prove, in terms of cases — not "it passes">.

Report: <TASK-ID>, in <COMPLIANCE_LOG>, section already created.

RULES OF ENGAGEMENT (this run's — confirmed at the start, not a default):
<the block settled above>
```

`Key finding` and `Failure to avoid` exist because a fresh Executor has no memory of the
investigation behind the task — it will make exactly the mistake full context would have
prevented. Naming the specific reflex to avoid is cheaper than an Executor discovering it
mid-task.

Do not paste a rules-of-engagement block from one project's run into another's handoff
without re-confirming it applies. It is a per-run artifact, not part of this skill.

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
holding up a phase; that turns a defect into paperwork.

### Remediation handoff

A verdict is not the deliverable — a well-evidenced `CONDITIONAL` or `REJECTED` that
ends in prose still leaves the Executor with nothing to act on. This is the
`Remediation order (annex)` from "The document set": write it, and hand it off the same
way the first task was handed off, not as a narrative the reader has to translate into
next steps themselves.

```
ROLE: Executor. Work from this remediation only; the rest of <EXECUTION_GUIDE> is
unaffected unless named below. Report in <COMPLIANCE_LOG>, appended under <GATE-ID> —
do not overwrite the original entry.

AUDIT RESULT: <Phase/Task> — <CONDITIONAL | REJECTED>. <one line: what was
independently re-verified and passed, so the Executor knows what not to touch>.

BLOCKED: <GATE-ID> — <what's actually wrong, in the Auditor's own re-run terms, not a
restatement of what the original delivery claimed>.

Root cause (verified — carries the command that established it, not reasoned from the
code): <the mechanism, with file/line and the falsifying probe or command that proved
it wrong>.

Candidate fix — a recommendation, not a decided point; the Auditor has not run it:
<the shape of a fix. Mark explicitly as unverified — the Executor confirms it, and may
find a better one, per "a factual claim always is reopenable">.

Do not touch: <what already passed and must not be disturbed by this fix — the other
approved gates or tasks in this delivery>.

Verify (literal): <the exact re-run command(s), including re-running the falsifying
probe that caught this — it must now pass>.

Success, minimum: <what must be true afterward — the probe that failed now passes, the
original suite stays green, nothing named under "Do not touch" moved>.

Report: <GATE-ID>, in <COMPLIANCE_LOG>, as a remediation entry.

RULES OF ENGAGEMENT: <this run's block>
```

The "candidate fix, not a decided point" framing matters — the Auditor found the defect
by running a probe, not by running the fix. Presenting it as settled would violate the
Auditor's own rule 4 below.

**`APPROVED` does not end the loop either, if a phase remains.** Only `APPROVED` with
nothing left to run closes without a handoff. Otherwise: hand off the next phase's first
task using the "Handing off a task" template above, in the same message as the verdict —
same reasoning as the remediation handoff, a different verdict feeding the same next
step. The Executor's next session starts cold whether the previous phase failed or
passed; "Phase 2 is APPROVED, go start Phase 3" is exactly the kind of pointer-not-an-
instruction this whole document exists to close.

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

## Failure modes seen in practice

- **Self-expansion.** The Executor implements phases marked "do not start." Work
  arrives with no checkpoints between phases; a defect in an early one gets built on
  before anyone looks.
- **Zero stops.** An empty "Blocked" section across dozens of tasks means ambiguities
  were resolved silently, not that none existed.
- **Letter over intent.** The task says "add a check for case X"; a check appears, it
  passes, and the condition X exists to detect is routed around by fixture ordering or
  test isolation. Anticipate this by naming the expected failure in the task itself.
- **Evidence-free `DONE`.** Treat as `FAILED`. Say so in the reporting rules up front.
- **A defect ships and nobody owns re-checking its blast radius.** A task changes what
  an existing field means; every other reader of that field is now a latent bug, and
  the person who finds it is usually a different, unrelated task that happens to hit
  it — not a re-audit of the original task. Grep for every reader before signing off,
  not after something breaks.
- **A change primes something to fire on its own before anyone can see or stop it.** A
  migration or config change that alters what triggers an automated write can leave
  the system armed to act — at scale, on real data — the moment its ordinary trigger
  next runs, with no one having pressed a button and no UI yet built to see or cancel
  it. Check the state the change leaves behind, not only the correctness of the new
  code path.

## Repo conventions this rides on

Cite whatever this codebase already enforces — version bumping, commit attribution,
fetch-before-push, environment-value discipline, evidence-driven debugging — from its
own source of truth rather than restating it here, so there's one place it can drift
out of sync from.

## The CLI

If `auditkit` is installed, prefer it over doing these by hand:

- `auditkit init <dir>` — scaffold the four documents from templates.
- `auditkit lint <dir>` — cross-check task IDs between the execution guide and the
  compliance log, flag near-duplicate paragraphs, warn on annex count per phase, flag
  gates with no stated negative control.
- `auditkit negcontrol --file <path> --break-cmd "<cmd>" --test-cmd "<cmd>"` — backs the
  file up, runs the break command, runs the test (expects failure), restores from the
  backup, runs the test again (expects success), and prints a paste-ready transcript.
- `auditkit status <dir>` — tallies verdicts in the compliance log and prints what's
  still open.

See the repo's `README.md` for install instructions.
