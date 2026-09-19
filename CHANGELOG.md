# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Conventional Commits specification documented in `CONTRIBUTING.md` and enforced in `AGENTS.md`.

### Changed
- Bumped `actions/checkout` and `actions/setup-python` to v7 in GitHub Actions CI workflow.
- Configured grouped updates in `.github/dependabot.yml` to bundle action and pip dependency bumps.

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
