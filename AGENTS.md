# Agent Guidelines

Instructions for AI coding agents working in this repository. They restate the human
contributor workflow in [`CONTRIBUTING.md`](CONTRIBUTING.md); when the two differ, `CONTRIBUTING.md` wins.

- Keep `auditkit` free of runtime dependencies: standard library only.
- Before calling a change done, run `ruff check .`, `ruff format --check .`, `mypy --strict src`,
  `python tests/run.py`, and `pytest --cov=auditkit --cov-fail-under=90`.
- Cover every behavior change with a test.
- Record user-visible changes in `CHANGELOG.md` under `## [Unreleased]`.
- Copy edits to `SKILL.md` or `references/` into `src/auditkit/skill/`.
- Write commit messages as [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/).
