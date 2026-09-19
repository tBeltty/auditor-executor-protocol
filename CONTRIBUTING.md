# Contributing to Auditor/Executor Protocol

Thank you for your interest in improving the Auditor/Executor protocol and `auditkit`!

## Principles

1. **Zero Runtime Dependencies:** `auditkit` must remain executable using only the Python standard library (`sys`, `pathlib`, `re`, `subprocess`, `argparse`). Never add runtime dependencies to `pyproject.toml`.
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
pytest --cov=auditkit --cov-report=term-missing --cov-fail-under=90
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

