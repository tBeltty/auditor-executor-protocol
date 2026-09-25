# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- `.gitattributes` normalizes line endings to LF, so checkouts on Windows match other platforms
  byte for byte (the framework vendors `SKILL.md`, `references/`, and the templates).

## [0.3.0] - 2026-09-25

### Added
- `auditkit lint` reports compliance-log entries with no matching task or gate in the
  execution guide.
- `auditkit negcontrol --timeout` bounds each command.
- `auditkit lint` flags `DONE` reports in `compliance-log.md` whose `**Verify output:**`
  field is missing, empty, or only a template placeholder. The protocol already records
  these as `FAILED`; the check makes that mechanical.
- README: install `auditkit` without cloning via `pipx install git+https://github.com/tBeltty/auditor-executor-protocol`.
- Conventional Commits specification documented in `CONTRIBUTING.md` and enforced in `AGENTS.md`.
- `SKILL.md`: optional Guided/Autonomous operating mode, with the autonomy charter, per-task
  model-tier assignment, the per-task cycle, and an Auditor-brief template for starting an
  autonomous run.
- `SKILL.md`: a deferred items ledger in the plan of record and a reserved-to-Auditor steps
  list in the execution guide, so cross-phase promises and recurring sandbox blocks are
  tracked as structured document state instead of prose an Auditor has to remember.
- `SKILL.md`: a `Blast radius` field on the task template covering both meaning-changing
  edits to a shared field and steps that empty/delete/replace shared code a later task
  still depends on.
- `SKILL.md`: gate-writing rules for compound gates (re-run every check, never cite a
  partial prior pass), realistic test fixtures (a minimal fixture shape hides bugs a
  realistic one would catch), and channel-crossing checks (a restriction proven on one
  transport/channel is not proven on all of them).
- `SKILL.md`: a "Worked example" section showing a filled-in, fictional Autonomous-mode
  run end to end.

### Changed
- `SKILL.md` split into a core file (24 KB, down from 47 KB) and four on-demand files in
  `references/`: `tasks-and-gates.md`, `handoffs.md`, `autonomous-mode.md`, and
  `failure-modes-and-example.md`. The core indexes each file with the step that needs it,
  so an agent that triggers the skill loads about half the tokens it did before.
- `auditkit install-skill` copies `references/` beside `SKILL.md`. Destinations that hold a
  single file (Cursor `.mdc`, or a `--dest` not named `SKILL.md`) get one bundled file.
- The packaged skill moved from `src/auditkit/templates/SKILL.md` to `src/auditkit/skill/`.
- `GEMINI.md` imports `AGENTS.md` instead of duplicating it, so the agent rules have one
  source of truth.
- Bumped `actions/checkout` and `actions/setup-python` to v7 in GitHub Actions CI workflow.
- Configured grouped updates in `.github/dependabot.yml` to bundle action and pip dependency bumps.

### Fixed
- `auditkit install-skill` shipped a stale 500-line copy of the protocol that predated the
  Autonomous mode, deferred items ledger, and gate-writing rules. `tests/test_skill_sync.py`
  now fails whenever the packaged copy differs from the repository root.
- `auditkit lint` returned "clean" (exit 0) for a missing directory or missing documents.
  It now exits 2 and names the missing file; linting nothing proves nothing.
- `auditkit status` ignored the Verdict column of the status board and counted a `DONE`
  self-report as closed, so a `REJECTED` task could appear closed. It now combines board
  verdicts with the latest report per ID; only `APPROVED` closes an item and `DONE` without
  a verdict is listed as awaiting audit.
- `auditkit negcontrol --file ... --restore-cmd ...` deleted the backup even when the
  restore command failed, leaving the file broken. With `--file`, the file must end
  byte-identical to the backup or it is restored from it, and the backup is kept if that
  still fails. The restore exit code is recorded.
- `auditkit lint` accepted a negated mention ("negative control: n/a") as a stated negative
  control.
- CLI help: `init` described four documents (it writes three plus `annexes/`), and
  `install-skill --dest` described a file path only.

## [0.2.0] - 2026-09-19

### Added
- PEP 561 marker (`src/auditkit/py.typed`) for inline static typing support.
- Complete test suite for `auditkit.cli` entry point (`tests/test_cli.py`).
- 90%+ test coverage enforcement across the repository.
- GitHub Actions CI workflow hardening: explicit token permissions, dedicated lint/format/typecheck job, package distribution verification, and weekly Dependabot configuration.
- Open-source governance files: `SECURITY.md`, `CONTRIBUTING.md`, `CHANGELOG.md`, PR and issue templates.
- Agent rule specifications (`AGENTS.md`, `GEMINI.md`) establishing mandatory changelog updates and test verification gates on every task.

### Changed
- Conformed all Python code to Ruff formatting and PEP 8 import conventions.
- Annotated all CLI runner entry points with strict parameter types (`argv: list[str] | None = None`).
- Standardized `pyproject.toml` metadata (SPDX license expression, project URLs, and keywords).
- Updated maintainer contact email to `jhonatan@tbelt.online` in `SECURITY.md` and `pyproject.toml`.

### Fixed
- Fixed cross-platform Windows newline and whitespace handling in negative control tests.

## [0.1.0] - 2026-08-30

### Added
- Initial release of Auditor/Executor Protocol specification (`SKILL.md`).
- `auditkit` CLI tool featuring `init`, `lint`, `negcontrol`, `status`, and `install-skill` subcommands.
- Multi-framework agent installation support for Antigravity, Claude Code, and Cursor.
- Zero-dependency test runner (`tests/run.py`).
