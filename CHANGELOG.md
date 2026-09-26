# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.8] - 2026-09-26

### Changed
- `auditkit lint` recognizes a stated negative control by what it says, not by a list of
  excuses to reject: it must name the action that removes the protection (or feeds the input it
  must stop) and the failure that follows, with no deferral and no negated failure. Waivers and
  refusals in any wording ("waived by the tech lead", "out of scope", "does not apply") no longer
  pass.

## [0.3.7] - 2026-09-26

### Fixed
- `auditkit lint` accepted refusals written as the negative control ("No control; ...",
  "deliberately omitted", "could not break it", "nothing to show").

## [0.3.6] - 2026-09-25

### Fixed
- `auditkit lint` accepted passive or scheduled deferrals as a negative control ("will be added
  in P1", "TBC", "to follow", "coming soon", "planned for the next release").

## [0.3.5] - 2026-09-25

### Fixed
- `auditkit lint` accepted a negative control that only deferred or pointed elsewhere
  ("will add later", "TBA", "see above"). A stated control now needs at least a short sentence
  (four words) with no deferral in it.

## [0.3.4] - 2026-09-25

### Fixed
- `auditkit lint` accepted deferred controls written in the plural ("Negative controls: none").
- The scaffolded gate stated a generic negative control ("A negative control — remove the
  protection, ..."), so a gate reported `DONE` without ever writing one passed lint. The
  template now has a `**Negative control:**` placeholder, and a gate still exactly as scaffolded
  is skipped only until it is reported `DONE`.

## [0.3.3] - 2026-09-25

### Fixed
- `auditkit lint` counted any mention of "negative control" as a stated one, so an empty label
  (`**Negative control:**`), a dash, a template placeholder, "to be written", or "N.A." passed.
  A mention now needs text after it (on the same line or the next ones) that is not a
  placeholder, punctuation, or a deferral.
- `auditkit lint` accepted `DONE` reports whose verify output was only punctuation ("-", "…") or
  "None yet".

## [0.3.2] - 2026-09-25

Fixes from a second independent review.

### Fixed
- `auditkit lint` accepted a deferred negative control written as a bold field
  (`**Negative control:** n/a`, `**Negative control**: none`); only up to three punctuation
  characters were allowed between the label and the deferral.
- `auditkit lint` counted a `DONE` report whose verify output was only a deferral ("n/a", "TBD",
  "pending") as pasted output.
- `auditkit negcontrol --timeout` killed only the shell; processes the command started kept
  running and could change the file after the restore check. Each command now runs in its own
  process group, which is killed as a whole on timeout.

## [0.3.1] - 2026-09-25

Fixes from an independent review of 0.3.0.

### Fixed
- `auditkit lint` reported "clean" for an execution guide with no tasks, or with tasks that have no
  `**Report:**` line, so empty documents passed. Both are now reported.
- `auditkit lint` accepted deferred negative controls ("Negative control: TBD", "skipped",
  "the negative control step was not done") as stated ones.
- `auditkit negcontrol --file` crashed and deleted the backup when the break command deleted or
  moved the file. The file is now recreated from the backup, and the backup is kept unless the
  file is verified byte-identical.
- `auditkit status` let a status board verdict silently override a later, different report-header
  verdict. Such items are now listed as `CONFLICT` and stay open.
- `auditkit install-skill --dest <directory>` skipped, crashed with `--force`, or wrote a file
  named after the directory. A directory destination now receives `SKILL.md` and `references/`.
- The sdist now includes `SKILL.md` and `references/`, so its own test suite passes.

### Changed
- `.gitattributes` normalizes line endings to LF, so checkouts on Windows match other platforms
  byte for byte (the framework vendors `SKILL.md`, `references/`, and the templates).
- Build requirement raised to `setuptools>=77`, which supports the SPDX `license` string.
- `SKILL.md` states that lint checks that evidence is present, not that it is authentic.

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
