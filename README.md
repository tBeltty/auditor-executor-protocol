# Auditor/Executor Protocol

A two-role protocol for running multi-phase work through AI agents without the plan drifting into open-ended discussion and without "all tests pass" masquerading as verification.

The **Auditor** defines what "done" means and proves it independently. The **Executor** implements one numbered task at a time and logs command output. Neither role crosses into the other.

[`SKILL.md`](SKILL.md) specifies the protocol. `auditkit` is a zero-dependency Python CLI that automates scaffolding, drift linting, and negative controls.

---

## When to Reach for This

Prompting an agent, scanning a diff, and shipping when it looks right works well for exploratory scripts and prototypes.

That approach fails when late mistakes carry real costs:
* Financial calculations and balance transfers
* Authorization, tenant isolation, and permission boundaries
* Destructive database schema migrations
* Automated background workers that run without human supervision

In these environments, plausible diffs are not evidence. Two failure modes break multi-session work:

1. **Silent Plan Drift:** Implementing agents quietly resolve ambiguities with assumptions instead of stopping to ask.
2. **Superficial Verification:** Reports like "reviewed and looks correct" mask unexecuted checks. Suites stay green because test fixtures bypass the assertion, not because the boundary holds.

The Auditor/Executor Protocol prevents both using a strict four-document paper trail and mandatory negative controls: a security check is not verified until you watch it fail with the protection removed.

---

## The Two Roles

| Role | Owns | Never | Output |
|---|---|---|---|
| **Auditor** | Instructions, gates, verdicts | Writes feature code | Task expansions, verdicts, remediation orders |
| **Executor** | Implementation, terminal evidence | Redesigns architecture, expands scope | Working code, unedited terminal output |

One person can run this workflow alone by switching hats between two isolated agent sessions.

---

## The Four-Document Paper Trail

`auditkit init` generates four documents. Keeping them separate prevents instructions from turning back into a discussion:

1. **Plan of Record (`plan-of-record.md`):** Explains the *what* and the *why*. Architecture decisions, rejected alternatives, and phase roadmaps. Nobody implements directly from this file.
2. **Execution Guide (`execution-guide.md`):** Explains the *how*. Numbered tasks (`P0-T1`) with target files, steps, literal verify commands, and phase gates (`P0-G1`).
3. **Compliance Log (`compliance-log.md`):** Records evidence. Pre-populated with every task and gate ID. The Executor pastes verbatim command output here.
4. **Remediation Annexes (`annexes/`):** When an audit yields `CONDITIONAL` or `REJECTED`, the Auditor issues a standalone annex instead of editing tasks in flight. Rapid annex growth signals an under-planned phase.

---

## Quickstart

### 1. Install `auditkit`

Requires Python 3.9+ with zero third-party dependencies:

```bash
git clone https://github.com/tBeltty/auditor-executor-protocol.git
cd auditor-executor-protocol
pip install -e .
```

### 2. Install the Protocol into Your Agent

Provision `SKILL.md` directly into your workspace or global environment:

```bash
auditkit install-skill                     # auto-detects Antigravity, Claude Code, or Cursor
auditkit install-skill --agent antigravity # writes to .agents/skills/auditor-executor-protocol/
auditkit install-skill --agent claude      # writes to .claude/skills/auditor-executor-protocol/
auditkit install-skill --agent cursor      # writes to .cursor/rules/auditor-executor-protocol.mdc
auditkit install-skill --global            # installs to user home skills directory
```

### 3. Scaffold a Phased Project

```bash
auditkit init docs/<task-name> --name "<Task Name>"
```

Creates `plan-of-record.md`, `execution-guide.md`, `compliance-log.md`, and `annexes/`.

### 4. Track Status and Lint Drift

Inspect open tasks and tallied verdicts:

```bash
auditkit status docs/<task-name>
```

Cross-check document consistency:

```bash
auditkit lint docs/<task-name>
```

`auditkit lint` catches missing report entries, gates without negative controls, duplicated log paragraphs, and phase annex buildup.

### 5. Run a Negative Control

When validating an authorization, tenant, or schema boundary:

```bash
auditkit negcontrol \
  --file server/middleware/auth.js \
  --break-cmd "sed -i '' 's/requireAuth/\/\/requireAuth/' server/middleware/auth.js" \
  --test-cmd "npm test -- auth.test.js"
```

`negcontrol` backs up the target file, applies the break mutation, confirms the test fails, restores the file with byte-level verification, confirms the test passes, and outputs a transcript ready for `compliance-log.md`.

---

## CLI Reference

| Command | Description |
|---|---|
| `auditkit init <dir>` | Scaffold the 4-document protocol set from templates |
| `auditkit install-skill` | Provision `SKILL.md` into Antigravity, Claude Code, or Cursor |
| `auditkit lint <dir>` | Cross-check IDs, detect missing negative controls, and flag log rot |
| `auditkit negcontrol` | Run automated backup, break, fail, restore, and pass cycle |
| `auditkit status <dir>` | Tally compliance log verdicts and list open items |

Every command operates on local Markdown files. No external databases, daemons, or network calls.

---

## Running Tests

Run the test suite using the standard library runner:

```bash
python3 tests/run.py
```

Or run with `pytest` by installing test extras:

```bash
pip install -e ".[test]"
pytest
```

---

## Contributing

Open an issue if you hit a failure mode not covered in the protocol, or if `auditkit` behavior deviates from [`SKILL.md`](SKILL.md).

## License

MIT (see [`LICENSE`](LICENSE)).

---

Made with ♥️ by [tBelt](https://github.com/tBeltty).
