# Agent Guidelines & Repository Rules

These rules are unconditionally binding for all AI coding agents (Antigravity, Claude Code, Cursor, Codex) working within this repository.

## 1. Mandatory CHANGELOG Maintenance
* **Always update [`CHANGELOG.md`](CHANGELOG.md) after every change**: Any bugfix, feature, refactoring, documentation update, or release must be recorded in `CHANGELOG.md` under the `## [Unreleased]` section (or the new release header if cutting a release) following [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
* **Never commit or push without a synchronized `CHANGELOG.md`**: Keeping the changelog up to date is part of the definition of done for every single task. Do not require user prompting to do this.

## 2. Mandatory Verification Quality Gates
Before declaring any task complete, committing, or pushing, all of the following commands must execute cleanly:
```bash
# 1. Static analysis and formatting
ruff check .
ruff format --check .

# 2. Strict type checking
mypy --strict src

# 3. Zero-dependency standard library runner
python tests/run.py

# 4. Pytest suite with 90%+ branch coverage gate
pytest --cov=auditkit --cov-report=term-missing --cov-fail-under=90
```

## 3. Architecture Constraints
* **Zero Runtime Dependencies**: The `auditkit` runtime must strictly depend only on the Python Standard Library. Never add runtime dependencies to `[project.dependencies]`.
* **Mechanical Verification**: Ensure all new features or bug fixes have corresponding automated unit tests and, when testing security or critical boundary guarantees, negative controls.
