# Auditor/Executor Protocol

A two-role protocol for running multi-phase work through AI agents without the plan drifting into open-ended discussion and without "all tests pass" masquerading as verification.

One role—the **Auditor**—defines what "done" means and independently proves it. The other—the **Executor**—implements one numbered task at a time and logs concrete command output. Neither crosses into the other's domain.

[`SKILL.md`](SKILL.md) specifies the protocol; `auditkit` is a zero-dependency Python CLI that automates scaffolding, drift linting, and negative control execution.

---

## When to Reach for This

Vibe coding—prompting an agent, reviewing the diff, and shipping when it feels right—is fast and effective for exploratory builds.

It breaks down when late mistakes carry high costs:
* Financial transactions and balances
* Authentication, authorization, and tenant isolation
* Destructive database schema migrations
* Automated background jobs that fire without human intervention

In these scenarios, plausible-looking diffs are not enough. Two failure modes reliably surface across multi-session agent work:

1. **Silent Plan Drift:** Implementing agents fill specification gaps with silent assumptions rather than stopping for clarification.
2. **Evidence-Free Completion:** Reports stating "I checked the implementation and it looks correct" pass unnoticed alongside actual test executions. Tests pass because fixtures bypass the assertion, not because the boundary holds.

The Auditor/Executor Protocol eliminates both with a strict four-document paper trail and mandatory **negative controls**: if a check has never been observed failing with the protection removed, it has not been verified.

---

## The Two Roles

| | Auditor | Executor |
|---|---|---|
| **Owns** | Instructions, gates, verdicts | Implementation, terminal evidence |
| **Never** | Writes feature code | Redesigns architecture, or expands scope |
| **Output** | Task expansions, verdicts, remediation orders | Working code, unedited command output |

You do not need two people. You can run this with two isolated agent sessions, switching hats between Auditor and Executor.

---

## The Four-Document Paper Trail

`auditkit init` scaffolds four separate documents. Keeping them separate prevents instructions from degrading back into discussion:

1. **Plan of Record (`plan-of-record.md`):** The *what* and the *why*. Architecture decisions, rejected alternatives, and phase roadmaps. Nobody implements directly from this file.
2. **Execution Guide (`execution-guide.md`):** The *how*. Numbered tasks (`P0-T1`) with files, exact steps, literal verify commands, and phase gates (`P0-G1`).
3. **Compliance Log (`compliance-log.md`):** The record of evidence. Pre-populated with every task and gate ID. The Executor pastes unedited terminal transcripts here.
4. **Remediation Annexes (`annexes/`):** When an audit yields `CONDITIONAL` or `REJECTED`, the Auditor writes a self-contained annex rather than editing in-flight tasks. High annex counts warn of an under-verified plan.

---

## Quickstart

### 1. Install `auditkit`

Requires only Python 3.9+ standard library:

```bash
git clone https://github.com/tBeltty/auditor-executor-protocol.git
cd auditor-executor-protocol
pip install -e .
```

### 2. Install the Protocol into Your Agent

Provision `SKILL.md` directly into your workspace or global configuration:

```bash
auditkit install-skill                     # auto-detects Antigravity, Claude Code, or Cursor
auditkit install-skill --agent antigravity # writes to .agents/skills/auditor-executor-protocol/
auditkit install-skill --agent claude      # writes to .claude/skills/auditor-executor-protocol/
auditkit install-skill --agent cursor      # writes to .cursor/rules/auditor-executor-protocol.mdc
auditkit install-skill --global            # installs to user home skills directory
```

### 3. Scaffold a New Phased Task

```bash
auditkit init docs/<task-name> --name "<Task Name>"
```

Creates `plan-of-record.md`, `execution-guide.md`, `compliance-log.md`, and `annexes/`.

### 4. Track and Verify Progress

Inspect pending items and tallied verdicts:

```bash
auditkit status docs/<task-name>
```

Lint cross-document integrity (missing reports, gates lacking negative controls, repeated log paragraphs, and annex buildup):

```bash
auditkit lint docs/<task-name>
```

### 5. Execute a Negative Control

When validating a security, authorization, or schema boundary:

```bash
auditkit negcontrol \
  --file server/middleware/auth.js \
  --break-cmd "sed -i '' 's/requireAuth/\/\/requireAuth/' server/middleware/auth.js" \
  --test-cmd "npm test -- auth.test.js"
```

`negcontrol` creates an isolated backup, applies the mutation, confirms the test fails, restores the original file with atomic byte-level verification, confirms the test returns to green, and prints a paste-ready transcript for `compliance-log.md`.

---

## CLI Reference

| Command | Description |
|---|---|
| `auditkit init <dir>` | Scaffold the 4-document protocol set from templates |
| `auditkit install-skill` | Provision `SKILL.md` into Antigravity, Claude Code, or Cursor |
| `auditkit lint <dir>` | Cross-check IDs, detect missing negative controls, and flag log rot |
| `auditkit negcontrol` | Run automated backup / break / fail / restore / pass cycle |
| `auditkit status <dir>` | Tally compliance log verdicts and list open items |

Every command operates on local Markdown files. Zero external state or network dependencies.

---

## Running the Tests

Run the full suite using the zero-dependency test runner:

```bash
python3 tests/run.py
```

Or run via `pytest` by installing test extras:

```bash
pip install -e ".[test]"
pytest
```

---

## Contributing

Open an issue if you encounter a failure mode not yet covered in the protocol, or if `auditkit` behavior deviates from [`SKILL.md`](SKILL.md).

## License

MIT — see [`LICENSE`](LICENSE).

---

Made with ♥️ by [tBelt](https://github.com/tBeltty).
