from auditkit import __version__, cli


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
