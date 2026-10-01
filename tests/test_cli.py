import argparse
import os
import subprocess
import sys
from pathlib import Path

from auditkit import __version__, cli

SRC = Path(__file__).resolve().parent.parent / "src"


def test_cli_version(capsys):
    try:
        cli.main(["--version"])
    except SystemExit as exc:
        assert exc.code == 0
    out = capsys.readouterr().out
    assert f"auditkit {__version__}" in out


def test_cli_help(capsys):
    try:
        cli.main(["--help"])
    except SystemExit as exc:
        assert exc.code == 0
    out = capsys.readouterr().out
    assert "usage: auditkit" in out


def test_cli_init_command(tmp_path):
    target = tmp_path / "scaffold_run"
    code = cli.main(["init", str(target), "--name", "Test Project", "--force"])
    assert code == 0
    assert (target / "plan-of-record.md").exists()


def test_cli_lint_command(tmp_path):
    target = tmp_path / "scaffold_run"
    cli.main(["init", str(target), "--name", "Test Project", "--force"])
    code = cli.main(["lint", str(target), "--annex-threshold", "5"])
    assert code == 0


def test_cli_status_command(tmp_path):
    target = tmp_path / "scaffold_run"
    cli.main(["init", str(target), "--name", "Test Project", "--force"])
    code = cli.main(["status", str(target)])
    assert code == 0


def test_cli_install_skill_command(tmp_path):
    dest = tmp_path / "custom_skill.md"
    code = cli.main(["install-skill", "--dest", str(dest), "--force"])
    assert code == 0
    assert dest.exists()


def test_cli_negcontrol_command(tmp_path):
    guarded_file = tmp_path / "flag.txt"
    guarded_file.write_text("protected\n")
    code = cli.main(
        [
            "negcontrol",
            "--test-cmd",
            f'grep -q protected "{guarded_file}"',
            "--break-cmd",
            f'echo broken > "{guarded_file}"',
            "--file",
            str(guarded_file),
        ]
    )
    assert code == 0


def test_python_dash_m_runs_the_cli():
    result = subprocess.run(
        [sys.executable, "-m", "auditkit", "--version"],
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "PYTHONPATH": str(SRC)},
    )
    assert result.returncode == 0
    assert result.stdout.strip() == f"auditkit {__version__}"


def test_every_option_has_help():
    parser = cli.build_parser()
    subparsers = next(a for a in parser._actions if isinstance(a, argparse._SubParsersAction))
    for name, sub in subparsers.choices.items():
        for action in sub._actions:
            if isinstance(action, argparse._HelpAction):
                continue
            assert action.help, f"auditkit {name} {action.dest} has no help text"


def test_errors_go_to_stderr(tmp_path, capsys):
    assert cli.main(["status", str(tmp_path)]) == 2
    captured = capsys.readouterr()
    assert "error:" in captured.err
    assert captured.out == ""
