# Contributing to Auditor/Executor Protocol

Thank you for your interest in improving the Auditor/Executor protocol and `aepkit`!

## Principles

1. **Zero Runtime Dependencies:** `aepkit` must remain executable using only the Python standard library (`sys`, `pathlib`, `re`, `subprocess`, `argparse`). Never add runtime dependencies to `pyproject.toml`.
2. **Deterministic Mechanical Checks:** The CLI handles checklist verifications, not subjective interpretation. Keep checks crisp, fast, and reproducible.
3. **Strict Quality Gates:** All code must pass strict typing (`mypy --strict src`), formatting and linting (`ruff check .`, `ruff format --check .`), and maintain at least 90% test coverage.

## Local Development Setup

Clone the repository and install development dependencies:

```bash
git clone https://github.com/tBeltty/auditor-executor-protocol.git
cd auditor-executor-protocol

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install package with dev dependencies
pip install -e ".[dev]"
```

## Running Tests

You can run tests with the zero-dependency standard library runner:

```bash
python tests/run.py
```

Or run the full test suite with coverage enforcement via pytest:

```bash
pytest --cov=aepkit --cov-report=term-missing --cov-fail-under=90
```

## Code Quality & Formatting

Run the linter and format verification:

```bash
# Check and auto-fix linter issues
ruff check --fix .

# Auto-format code
ruff format .

# Type check with strict mode
mypy --strict src
```

## Commit Guidelines

We adhere to [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/). Commit messages should follow the structure:

`<type>(<optional scope>): <description>`

Common types:
- `feat`: A new feature, CLI command, or mechanical check
- `fix`: A bug fix or test correction
- `docs`: Documentation, README, or rule updates
- `refactor`: Code refactoring with no functional change
- `test`: Adding or refining tests
- `chore`: Packaging, CI workflow, or dependency updates
- `release`: Version bump and formal release

## Pull Request Checklist

Before submitting a PR:
- [ ] Zero runtime dependencies maintained.
- [ ] Tests pass under `python tests/run.py` and `pytest`.
- [ ] Test coverage is >= 90%.
- [ ] `ruff check .` and `ruff format --check .` report no issues.
- [ ] `mypy --strict src` reports 0 errors.
- [ ] Commit messages follow Conventional Commits.
- [ ] [`CHANGELOG.md`](CHANGELOG.md) is updated under `## [Unreleased]`.
- [ ] Documentation is updated if relevant.
- [ ] Edits to `SKILL.md` or `references/` are copied to `src/aepkit/skill/` and to the plugin's `skills/auditor-executor-protocol/` (`tests/test_skill_sync.py` enforces it).

## Releasing

Two things ship from this repository, each with its own version:

- **`aepkit`** (`src/aepkit/__init__.py`), published to PyPI by the release workflow.
- **The Claude Code plugin** (`integrations/claude-code/aeprogress/`), installed from `main`
  through `.claude-plugin/marketplace.json`. Its version lives in `plugin.json`, in the
  marketplace entry and in `VERSION` in `hooks/register.tsx`;
  `tests/test_plugin_version.py` keeps the three equal.

A commit that changes a version names which one in its subject, for example
`fix(plugin): ... (plugin 0.5.6)` or `release: aepkit 0.7.7`.

A plugin change reaches users when it is merged, so it needs no PyPI release. Its changelog
entry waits under `## [Unreleased]` for the next `aepkit` release, and so does a README-only
change. Cut an `aepkit` release when the CLI, the protocol files it ships (`SKILL.md`,
`references/`, templates) or its packaging change, and group the merged changes into one
release.

To release `aepkit`:

1. In a pull request, bump `aepkit.__version__` (Semantic Versioning) and move the
   `## [Unreleased]` entries of `CHANGELOG.md` into a new `## [X.Y.Z] - YYYY-MM-DD` section,
   with its compare link at the bottom.
2. For a new minor version, update the supported-versions table in [`SECURITY.md`](SECURITY.md).
3. After the pull request is merged, tag the merge commit with an annotated tag,
   `git tag -a vX.Y.Z -m "aepkit X.Y.Z"`, and push it. Release tags cannot be moved or deleted.
4. The release workflow runs the full CI and checks that the tag matches `__version__`. Publishing
   to PyPI waits for a maintainer's approval in the `pypi` environment; once approved, the
   workflow publishes and creates the GitHub release from the changelog section.
