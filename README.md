# Auditor/Executor Protocol

[![CI](https://github.com/tBeltty/auditor-executor-protocol/actions/workflows/ci.yml/badge.svg)](https://github.com/tBeltty/auditor-executor-protocol/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Checked with mypy](https://img.shields.io/badge/mypy-strict-blue)](https://mypy-lang.org/)
[![Zero Dependencies](https://img.shields.io/badge/dependencies-0-brightgreen)](pyproject.toml)

A two-role protocol for running multi-phase work through AI agents without the plan drifting into open-ended discussion and without "all tests pass" masquerading as verification.

The **Auditor** defines what "done" means and proves it independently. The **Executor** implements one numbered task at a time and logs command output. Neither role crosses into the other.

[`SKILL.md`](SKILL.md) specifies the protocol core; [`references/`](references/) holds the parts an agent loads only when it reaches that step (task and gate writing, handoff templates, Autonomous mode, failure modes and a worked example). `auditkit` is a zero-dependency Python CLI that automates scaffolding, drift linting, negative controls, status tallies, and installing the skill into your agent.

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

`auditkit init` generates the first three documents and an empty `annexes/` directory for the fourth. Keeping them separate prevents instructions from turning back into a discussion:

1. **Plan of Record (`plan-of-record.md`):** Explains the *what* and the *why*. Architecture decisions, rejected alternatives, and phase roadmaps. Nobody implements directly from this file.
2. **Execution Guide (`execution-guide.md`):** Explains the *how*. Numbered tasks (`P0-T1`) with target files, steps, literal verify commands, and phase gates (`P0-G1`).
3. **Compliance Log (`compliance-log.md`):** Records evidence. Holds a status board and one report entry per task and gate ID; the template starts with `P0-T1` and `P0-G1`, and you add an entry for each task you write. The Executor pastes verbatim command output here.
4. **Remediation Annexes (`annexes/`):** When an audit yields `CONDITIONAL` or `REJECTED`, the Auditor issues a standalone annex instead of editing tasks in flight. Rapid annex growth signals an under-planned phase.

---

## Quickstart

### 1. Install `auditkit`

Requires Python 3.11+ with zero third-party dependencies:

```bash
pipx install git+https://github.com/tBeltty/auditor-executor-protocol
```

Or from a clone, for development:

```bash
git clone https://github.com/tBeltty/auditor-executor-protocol.git
cd auditor-executor-protocol
pip install -e .
```

### 2. Install the Protocol into Your Agent

Provision `SKILL.md` and its `references/` directory into your workspace or global environment. Cursor rules hold a single file, so Cursor receives one bundled `.mdc` with the references appended:

```bash
auditkit install-skill                     # auto-detects Antigravity, Claude Code, or Cursor
auditkit install-skill --agent antigravity # writes to .agents/skills/auditor-executor-protocol/
auditkit install-skill --agent claude      # writes to .claude/skills/auditor-executor-protocol/
auditkit install-skill --agent cursor      # writes to .cursor/rules/auditor-executor-protocol.mdc
auditkit install-skill --global            # user-level install (Antigravity unless --agent is given)
auditkit install-skill --dest <path>       # explicit destination; a non-SKILL.md file name gets one bundled file
```

Auto-detection checks the target directory for `.agents/` or `.gemini/`, `.claude/`, and `.cursor/`, then agent environment variables, and falls back to Antigravity. With `--global`, the skill goes to `~/.gemini/config/skills/`, `~/.claude/skills/`, or `~/.cursor/rules/`. An existing install is skipped unless you pass `--force`.

### 3. Scaffold a Phased Project

```bash
auditkit init docs/<task-name> --name "<Task Name>"
```

Creates `plan-of-record.md`, `execution-guide.md`, `compliance-log.md`, and `annexes/`. `--name` defaults to the directory name; existing documents are kept unless you pass `--force`.

### 4. Track Status and Lint Drift

Inspect open tasks and tallied verdicts:

```bash
auditkit status docs/<task-name>
```

Cross-check document consistency:

```bash
auditkit lint docs/<task-name>
```

`auditkit lint` catches an empty guide, tasks without a report line, missing report entries, log entries with no matching task, `DONE` reports whose verify output is not pasted in a code block, gates without a stated negative control (hypothetical or waived ones do not count), work reported in a phase before every earlier phase is `APPROVED`, duplicated log paragraphs, and annex buildup past `--annex-threshold` (default 6, overall or per phase).

### 5. Run a Negative Control

When validating an authorization, tenant, or schema boundary:

```bash
auditkit negcontrol \
  --file server/middleware/auth.js \
  --break-cmd "sed -i '' 's/requireAuth/\/\/requireAuth/' server/middleware/auth.js" \
  --test-cmd "npm test -- auth.test.js"
```

The `sed -i ''` form above is BSD/macOS sed; on GNU/Linux use `sed -i 's/.../.../' file`.

`negcontrol` backs up the target file, applies the break mutation, confirms the test fails, restores the file with byte-level verification, confirms the test passes, and outputs a transcript ready for `compliance-log.md`. Without `--file`, pass `--restore-cmd` to undo the break yourself; with both, the backup still wins if the file is not byte-identical afterwards. `--timeout` limits each command in seconds.

---

## CLI Reference

| Command | Options | Description |
|---|---|---|
| `auditkit init <dir>` | `--name`, `--force` | Scaffold the three documents and `annexes/` from templates |
| `auditkit install-skill [dir]` | `--agent`, `--global`, `--dest`, `--force` | Provision `SKILL.md` and `references/` into Antigravity, Claude Code, or Cursor |
| `auditkit lint <dir>` | `--annex-threshold` | Cross-check IDs both ways, flag `DONE` without evidence, detect missing negative controls, and flag log rot |
| `auditkit negcontrol` | `--test-cmd` (required), `--file`, `--break-cmd`, `--restore-cmd`, `--timeout` | Run automated backup, break, fail, restore, and pass cycle |
| `auditkit status <dir>` | | Combine status board verdicts with reports; list everything not `APPROVED` |

Exit codes: `lint` and `negcontrol` return `0` when clean, `1` when they find a problem, and `2` on a usage error or missing document, so both can gate CI. `status` is informational and returns `0` whenever the compliance log exists.

`auditkit` reads and writes local Markdown files only: no external databases, daemons, or network calls. `negcontrol` runs the shell commands you pass it.

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

Contributions are welcome! Please read [`CONTRIBUTING.md`](CONTRIBUTING.md) for development guidelines, testing instructions, and our PR checklist. For security disclosures, refer to [`SECURITY.md`](SECURITY.md). Releases and historical updates are tracked in [`CHANGELOG.md`](CHANGELOG.md).

## License

MIT (see [`LICENSE`](LICENSE)).

---

Made with ♥️ by [tBelt](https://github.com/tBeltty).
