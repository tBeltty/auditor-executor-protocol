# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- Claude Code plugin 0.5.2, for the plugin directory's checks:
  - Every process it runs names a fixed program with fixed arguments: `aepkit status --json .`
    runs in the run folder (or `python3`, `python`, `py -m aepkit`), `orca` by its plain name,
    and the Windows load reading as a chain of plain PowerShell cmdlets.
  - The **Workers command** option becomes **Workers file**: another harness keeps a text file
    of its running workers and the plugin only reads it, running nothing. The **aepkit command**
    option is gone; aepkit must be on the PATH or importable by `python3`.
  - The guarded hooks no longer chain `.catch` on their registration: each asks a function in
    the hooks module whether to refuse, then passes the call on, and handles its own errors.

## [0.7.6] - 2026-11-08

### Changed
- Compaction at a phase close is now part of each mode. `SKILL.md` gains "Compacting at a
  phase close" and a row in the modes table: in Guided mode the owner compacts by hand
  (`/compact`, then a resume message the Auditor gives, with its template); in Autonomous
  mode the Auditor compacts its own session with no action from the owner, where the harness
  has a compaction tool such as the Claude Code plugin's `compact_and_resume`, and otherwise
  goes on uncompacted. `references/autonomous-mode.md` turns its optional step into that
  rule, orders the phase close (report, expand the next phase, update the brief, compact)
  and adds the compaction tool to the Auditor brief.
- `aeprogress` 0.5.1: the `compact_and_resume` tool tells the Auditor not to call it in
  Guided mode.
- Both READMEs: a plain-language pass, and the compaction rule per mode.

## [0.7.5] - 2026-11-08

### Changed
- The Claude Code plugin is now `auditor-executor-protocol` (it was `aeprogress`) and brings the
  protocol itself as a skill, the same `SKILL.md` and `references/` as the repository root (a
  test keeps the copy in sync), together with the `aeprogress` pane. Its listing and README start
  with what the protocol is, what the plugin brings, and the steps to start a run, and say that
  the pane does nothing without one. Install it with
  `/plugin install auditor-executor-protocol --marketplace tBeltty/auditor-executor-protocol`; a
  copy installed as `aeprogress` has to be uninstalled and installed again under the new name.
  The `/aeprogress` command is unchanged. Plugin version 0.5.0.
- README: section 6 describes the plugin, and section 2 points Claude Code users to it.
- `references/autonomous-mode.md`: the plugin update command uses the new name.

### Changed
- `aeprogress` 0.4.1, for the plugin directory's checks:
  - The launch limit for Claude Code subagents moves from the `agent.spawn` event, which the
    directory requires plugins to pass on unchanged, to the `Agent` tool call: an Executor
    launch past the limits is refused there, and every other call passes unchanged.
  - Every function that receives the mod API now sits in the hooks module itself, every call
    on it is written on one line, the load readings run fixed commands, and the version check
    names its one address at the call.
  - Two regular expressions spelled invisible characters literally; they now use escapes.
  - The hover card is gone: in the terminal it drew over the rows below it. Opening a phase
    shows the same.
  - The README lists every hook with what it does and changes, the one prompt it submits,
    and the tools whose calls it can refuse.

## [0.7.4] - 2026-11-08

### Added
- `references/autonomous-mode.md`: "Tool versions at the start of a run". Before the first task
  the Auditor updates the tools the run depends on (`aepkit`, any plugin or harness) and records
  their versions in the plan of record; the Auditor brief gains a `TOOLS` field for it.
- `aeprogress` 0.4.0:
  - Expandable phases: each phase row opens its full title, its bar and count, and its tasks and
    gate as state chips (approved, conditional, in progress with the worker, awaiting audit,
    pending, rejected). The active phase opens by itself; a phase the owner closes stays closed.
    Where the surface reports hover (desktop app, fullscreen terminal), a closed phase shows the
    same in a card.
  - Update check: the pane and `/aeprogress` say when a newer version exists, from the
    marketplace catalog Claude Code keeps on disk and, at most once a day, from the version
    published on GitHub (one request for a public file; option **Update check**: `daily`,
    `offline` or `off`; skipped for copies from the claude.ai directory and when
    `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` is set). The README explains how to turn on
    auto-update for this marketplace.
  - An icon (`.claude-plugin/icon.png`, source in `assets/icon.svg`), and `documentationUrl`,
    `supportUrl` and `privacyPolicyUrl` in `plugin.json`, for the plugin directory. The README
    gains "What it does on your machine" (every process it starts, the files and variables it
    reads, the one network request, and what it can refuse) and "Privacy", and shows its
    screenshots as Markdown images inside the plugin.

## [0.7.3] - 2026-11-08

No change to the package's code. This release puts the new README on PyPI: the protocol's
Guided and Autonomous modes, the `aeprogress` section with screenshots, and the DOI badge.

### Changed
- CI runs `claude plugin validate` (the mod and the marketplace) and `claude plugin test` for
  `aeprogress`, on Claude Code 2.1.319, the release the mod is tested against.
- Dev dependencies: ruff 0.17.3, mypy 2.4.1; GitHub Actions bumped (Dependabot #20, #22).
- `CITATION.cff` and the README carry the Zenodo concept DOI, 10.5281/zenodo.23633244, which
  resolves to the latest archived release.
- `aeprogress` 0.3.1: a worker's name in the pane no longer repeats the task ID it carries
  (`P2-T3  Executor P2-T3` is now `P2-T3  Executor`), for subagents, Orca workers and lines
  from a workers command. README screenshots of the pane, the launch limit and the
  compaction countdown.

## [0.7.2] - 2026-11-08

### Added
- `references/autonomous-mode.md`: an optional step at a phase's close. Once the gate is
  `APPROVED`, the work is pushed and the Auditor brief is up to date, the Auditor may compact
  its own session and resume itself from the brief.
- `aeprogress` 0.3.0: a `compact_and_resume` tool for the Auditor. After its turn ends, a band
  counts down 40 seconds with Cancel and Compact now; at zero the session is compacted and the
  Auditor resumed with its own `resume` message. A prompt typed by the owner, Esc on the turn,
  or Cancel drops it; a manual `/compact` during the countdown resumes once; a refused or vetoed
  compaction resumes nothing. Options for the seconds and to turn it off.

## [0.7.1] - 2026-11-08

### Added
- `references/handoffs.md`: an optional `Load: docs-only` line in the handoff template, for
  runs where a tool holds back Executor launches while the machine is busy. It marks a task
  that builds nothing, so it may run beside one that builds; a handoff without it counts as
  a build. The protocol does not require it.
- `aeprogress` 0.2.0 (`integrations/claude-code/aeprogress/`): a launch limit that, while a
  run is found, refuses launching another Executor past 2 live workers, 1 building worker,
  or a machine more than 75% busy for a build (each a `/config` option), with the reason in
  the refusal. It sees Claude Code subagents whose prompt names a task of the run, and Orca
  `worker-start` and `send` to a dispatch that is not live; it counts both together, and
  refuses when Orca cannot be asked. The pane shows the machine's load (Linux `/proc`,
  macOS and BSD `sysctl`, Windows PowerShell) and how full the limit is. On macOS, when
  Spotlight's indexing stays busy, it recommends excluding the project folder in System
  Settings; it never changes a setting.
- `aeprogress`: Windows fallbacks for finding aepkit (`python -m`, `py -m`,
  `%USERPROFILE%\.local\bin`).

## [0.7.0] - 2026-11-08

### Added
- `aepkit status --json` prints the status reading as one JSON object: each ID with its
  phase, kind, effective state, verdict, latest report, executor (a status board column
  named `Executor`, `Worker`, `Agent`, `Owner` or `Assignee`) and any board/header
  conflict; the phases with their titles from `execution-guide.md` and the plan's phase
  table, an optional `Weight` column, and phases the guide has not broken down; IDs the
  guide lists that the log has no entry for yet, marked `inLog: false`. The text output
  is unchanged.
- `aeprogress`, an optional Claude Code mod in `integrations/claude-code/aeprogress/`:
  a pane with the run's progress per phase, who is working on which ID (Claude Code
  subagents, Orca workers, or any harness through a command), what awaits audit and what
  needs attention, opened with `/aeprogress`. `.claude-plugin/marketplace.json` makes the
  repository installable with
  `/plugin install aeprogress --marketplace tBeltty/auditor-executor-protocol`.

### Fixed
- `SKILL.md`, `references/handoffs.md`, `references/autonomous-mode.md` and
  `references/failure-modes-and-example.md` spoke of "a plain `PASS`" on one task. `PASS`
  is not a verdict (the verdicts are `APPROVED`, `CONDITIONAL` and `REJECTED`), and a log
  that used it showed the task as awaiting audit in `aepkit status`. The four sentences
  now say `APPROVED`.

## [0.6.1] - 2026-10-25

### Added
- `CITATION.cff`, so each GitHub release is archived on Zenodo with citation metadata. This
  release is the first archived one (10.5281/zenodo.23633245). No code changes, and it was not
  published to PyPI: the package still reported 0.6.0.

## [0.6.0] - 2026-10-24

### Added
- `plan-of-record.md` template and `SKILL.md`: Opportunity & Shaping gate (`Target outcome`,
  `Problem / friction`, `Cost of doing nothing`, three-option set-based comparison with
  `Selected option & rationale`, `Riskiest assumption & first-phase validation`, `Explicit
  non-goals`, and the `Deferred items ledger` table), plus a fast-track bypass
  (`N/A (Deterministic Fix/Compliance)`) for bugfixes, security patches, migrations, and
  strict compliance work.
- `aepkit lint` flags `[unfilled plan]` when `plan-of-record.md` is present and work has
  been reported `DONE` or given a verdict while required opportunity, shaping, riskiest-assumption,
  or non-goal fields remain empty, deferred, or placeholders (unless the shaping/assumption
  fields declare `N/A (Deterministic Fix/Compliance)`).
- `aepkit lint` flags `[open deferred item]` when a row in the deferred items ledger of
  `plan-of-record.md` references a closing task ID that does not exist in `execution-guide.md`
  or remains open when its target phase is being closed.

### Changed
- **Breaking:** Renamed the PyPI distribution, Python package, and CLI binary to `aepkit`
  (`pipx install aepkit`, `aepkit`, `python -m aepkit`) to eliminate naming collisions with
  external `auditkit` packages and binaries.

## [0.5.1] - 2026-10-04

### Fixed
- `negcontrol --file` without `--break-cmd` is now a usage error (exit 2). The backup was taken
  of a file already broken by hand, so a correct `--restore-cmd` was overwritten with the broken
  copy and blamed for it.
- `negcontrol` fails the control when the test times out with the protection removed: a hang is
  not a caught break. It used to print `OK` with a warning.
- `negcontrol --file <directory>` and `auditkit init <existing file>` print an error and exit 2
  instead of crashing with a traceback.
- The execution guide's reporting format puts the verify output in a fenced block, so a report
  written as the template shows no longer fails `lint`.
- `lint` no longer cuts a report short at a `#`, `---` or `**Field:**` line inside pasted output.
- `lint`'s phase-order check reads verdicts the way `status` does: the latest report header wins,
  and a status board verdict that disagrees with it is a conflict, not an approval.
- `install-skill` auto-detects Claude Code through `CLAUDECODE`, the variable Claude Code sets.
- The install-skill tests no longer depend on the agent environment they run in.

### Changed
- The release workflow runs the full CI before building and publishing.
- CI pins ruff, mypy, build and twine through the `dev` extra, and smoke-tests the built wheel in
  a clean environment.
- README links are absolute, so they work on PyPI; `auditkit --help` and the installed skill
  link to GitHub instead of "the repo root".
- `--annex-threshold` is documented as a total with a per-phase breakdown, which is what it
  checks.
- `SECURITY.md` lists 0.5.x as supported; `CONTRIBUTING.md` documents the release steps.

## [0.5.0] - 2026-10-02

### Added
- `auditkit negcontrol --expect REGEX`: the failing run's output must match the expression, so
  a test that fails for an unrelated reason (a syntax error, a missing import, a mistyped
  command) fails the control instead of passing it.
- Without `--expect`, `negcontrol` adds a `WARNING` to its verdict when the failing output looks
  like a syntax, import, collection, timeout or command-not-found error, rather than the
  protection being caught.

### Changed
- **Breaking (Python API only):** `auditkit.negcontrol.run()` takes every argument after
  `test_cmd` by keyword. The `auditkit negcontrol` command is unchanged.

## [0.4.0] - 2026-10-01

### Added
- `python -m auditkit` runs the CLI.
- A release workflow publishes to PyPI through trusted publishing when a `v*` tag is pushed,
  then creates the GitHub release from this changelog.
- `CODE_OF_CONDUCT.md`, and an issue chooser that routes vulnerability reports to private
  disclosure.
- `auditkit lint` flags `[phase order]`: work reported in a phase before every earlier phase is
  `APPROVED`.
- Tests that check the README's CLI reference, exit codes, `install-skill` destinations,
  `negcontrol` behavior, and its promises: unevidenced `DONE`, waived controls, unplanned
  reports, and tests that cannot fail are caught.

### Changed
- The distribution is named `auditor-executor-protocol`, because `auditkit` on PyPI belongs to
  an unrelated project. The command and the import package are still `auditkit`. The README
  installs it from PyPI.
- **Breaking:** `auditkit lint` counts verify output only inside a fenced code block, so prose
  such as "all tests pass" or "looks correct" is reported as `DONE` without evidence. Logs that
  pasted output without a fence fail until it is wrapped in a ``` block; the lint message says
  how.
- `auditkit lint` rejects hypothetical negative controls ("could", "should", "may") and ones
  whose action removes nothing.
- README states that the Auditor re-runs every check in its own session and that `lint` checks
  the form of evidence, not whether it is genuine.
- Errors and warnings go to stderr; stdout carries only results and transcripts.
- Every `auditkit` option has help text. Each subcommand module no longer carries its own copy
  of the argument parser, so `auditkit <command> --help` is the single, complete reference.
- Dependabot only raises a pip minimum when it no longer admits the latest release.
- CI pins every action to a commit SHA, cancels superseded runs, and checks the built
  distributions with `twine check --strict`.
- Package metadata lists supported Python versions, `Development Status`, and `Typing :: Typed`;
  the version is defined once, in `auditkit.__version__`.
- `.gitignore` covers common virtualenv, coverage, tox/nox, and editor files; the PR template
  matches the CONTRIBUTING checklist.

### Removed
- Python 3.9 and 3.10 support (end of life in October 2025 and October 2026). `auditkit` now
  requires Python 3.11+.

### Fixed
- README: the compliance log template, `install-skill` detection and `--global`/`--dest`, every
  command's options, exit codes, and the BSD-only `sed -i ''` in the `negcontrol` example now match
  the CLI.

## [0.3.9] - 2026-09-26

### Fixed
- `auditkit lint` accepted hypothetical, waived, and action-negated negative controls.
- `auditkit lint` rejected some valid negative controls.

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
- Conventional Commits specification documented in `CONTRIBUTING.md`.
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

[Unreleased]: https://github.com/tBeltty/auditor-executor-protocol/compare/v0.7.6...HEAD
[0.7.6]: https://github.com/tBeltty/auditor-executor-protocol/compare/v0.7.5...v0.7.6
[0.7.5]: https://github.com/tBeltty/auditor-executor-protocol/compare/v0.7.4...v0.7.5
[0.7.4]: https://github.com/tBeltty/auditor-executor-protocol/compare/v0.7.3...v0.7.4
[0.7.3]: https://github.com/tBeltty/auditor-executor-protocol/compare/v0.7.2...v0.7.3
[0.7.2]: https://github.com/tBeltty/auditor-executor-protocol/compare/v0.7.1...v0.7.2
[0.7.1]: https://github.com/tBeltty/auditor-executor-protocol/compare/v0.7.0...v0.7.1
[0.7.0]: https://github.com/tBeltty/auditor-executor-protocol/compare/v0.6.0...v0.7.0
[0.6.1]: https://github.com/tBeltty/auditor-executor-protocol/compare/v0.6.0...v0.6.1
[0.6.0]: https://github.com/tBeltty/auditor-executor-protocol/compare/v0.5.1...v0.6.0
[0.5.1]: https://github.com/tBeltty/auditor-executor-protocol/compare/v0.5.0...v0.5.1
[0.5.0]: https://github.com/tBeltty/auditor-executor-protocol/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/tBeltty/auditor-executor-protocol/compare/v0.3.9...v0.4.0
[0.3.9]: https://github.com/tBeltty/auditor-executor-protocol/compare/v0.3.8...v0.3.9
[0.3.8]: https://github.com/tBeltty/auditor-executor-protocol/compare/v0.3.7...v0.3.8
[0.3.7]: https://github.com/tBeltty/auditor-executor-protocol/compare/v0.3.6...v0.3.7
[0.3.6]: https://github.com/tBeltty/auditor-executor-protocol/compare/v0.3.5...v0.3.6
[0.3.5]: https://github.com/tBeltty/auditor-executor-protocol/compare/v0.3.4...v0.3.5
[0.3.4]: https://github.com/tBeltty/auditor-executor-protocol/compare/v0.3.3...v0.3.4
[0.3.3]: https://github.com/tBeltty/auditor-executor-protocol/compare/v0.3.2...v0.3.3
[0.3.2]: https://github.com/tBeltty/auditor-executor-protocol/compare/v0.3.1...v0.3.2
[0.3.1]: https://github.com/tBeltty/auditor-executor-protocol/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/tBeltty/auditor-executor-protocol/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/tBeltty/auditor-executor-protocol/releases/tag/v0.2.0
[0.1.0]: https://github.com/tBeltty/auditor-executor-protocol/tree/7e9701cdacf732fa63b28428eedd9dcc7250fa2f
