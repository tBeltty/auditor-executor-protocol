import sys

from auditkit import negcontrol


def test_negcontrol_detects_real_protection(tmp_path):
    guarded_file = tmp_path / "flag.txt"
    guarded_file.write_text("protected\n")

    test_cmd = f'grep -q protected "{guarded_file}"'
    break_cmd = f'echo broken > "{guarded_file}"'

    code = negcontrol.run(test_cmd=test_cmd, break_cmd=break_cmd, file_path=str(guarded_file))
    assert code == 0
    assert guarded_file.read_text() == "protected\n"


def test_negcontrol_flags_a_fake_protection(tmp_path, capsys):
    guarded_file = tmp_path / "flag.txt"
    guarded_file.write_text("protected\n")

    # test_cmd always passes, so "breaking" it should not make it fail — this must be caught.
    test_cmd = "true"
    break_cmd = f'echo broken > "{guarded_file}"'

    code = negcontrol.run(test_cmd=test_cmd, break_cmd=break_cmd, file_path=str(guarded_file))
    out = capsys.readouterr().out
    assert code == 1
    assert "did not fail" in out
    assert guarded_file.read_text() == "protected\n"


def test_negcontrol_restores_file_on_break_failure(tmp_path):
    guarded_file = tmp_path / "flag.txt"
    guarded_file.write_text("protected\n")

    test_cmd = f'grep -q protected "{guarded_file}"'
    # Break cmd alters the file and then exits with non-zero
    break_cmd = f'echo broken > "{guarded_file}" && exit 42'

    code = negcontrol.run(test_cmd=test_cmd, break_cmd=break_cmd, file_path=str(guarded_file))
    # It broke as expected and then restored
    assert code == 0
    assert guarded_file.read_text() == "protected\n"


def test_negcontrol_missing_break_and_restore_cmd(capsys):
    code = negcontrol.run(test_cmd="true")
    out = capsys.readouterr().err
    assert code == 2
    assert "error: pass --break-cmd, or --restore-cmd" in out


def test_negcontrol_missing_file_and_restore_cmd(capsys):
    code = negcontrol.run(test_cmd="true", break_cmd="echo 1")
    out = capsys.readouterr().err
    assert code == 2
    assert "without --file, --restore-cmd is required" in out


def test_negcontrol_nonexistent_file(capsys):
    code = negcontrol.run(
        test_cmd="true", break_cmd="echo 1", file_path="nonexistent_file_12345.txt"
    )
    out = capsys.readouterr().err
    assert code == 2
    assert "is not an existing file" in out


def test_negcontrol_custom_restore_cmd(tmp_path):
    target = tmp_path / "data.txt"
    target.write_text("initial\n")

    code = negcontrol.run(
        test_cmd=f'grep -q initial "{target}"',
        break_cmd=f'echo broken > "{target}"',
        restore_cmd=f'echo initial > "{target}"',
    )
    assert code == 0
    assert target.read_text().strip() == "initial"


def test_negcontrol_fails_if_not_restored_to_green(tmp_path, capsys):
    target = tmp_path / "data.txt"
    target.write_text("initial\n")

    code = negcontrol.run(
        test_cmd=f'grep -q initial "{target}"',
        break_cmd=f'echo broken > "{target}"',
        restore_cmd="echo still_broken",  # does not restore data.txt
    )
    out = capsys.readouterr().out
    assert code == 1
    assert "did not return to passing after restore" in out


def test_negcontrol_failing_restore_cmd_falls_back_to_backup(tmp_path, capsys):
    guarded_file = tmp_path / "flag.txt"
    guarded_file.write_text("protected\n")

    code = negcontrol.run(
        test_cmd=f'grep -q protected "{guarded_file}"',
        break_cmd=f'echo broken > "{guarded_file}"',
        file_path=str(guarded_file),
        restore_cmd="false",
    )
    out = capsys.readouterr().out
    assert guarded_file.read_text() == "protected\n"
    assert "(restore exit 1)" in out
    assert "did not restore the file; using the backup" in out
    assert code == 0


def test_negcontrol_failed_restore_without_file_is_a_failure(tmp_path, capsys):
    target = tmp_path / "data.txt"
    target.write_text("initial\n")
    code = negcontrol.run(
        test_cmd=f'grep -q initial "{target}"',
        break_cmd=f'echo broken > "{target}"',
        restore_cmd="false",
    )
    out = capsys.readouterr().out
    assert code == 1
    assert "protection was not restored" in out


def test_negcontrol_timeout_is_reported(tmp_path, capsys):
    guarded_file = tmp_path / "flag.txt"
    guarded_file.write_text("protected\n")
    code = negcontrol.run(
        test_cmd=f'grep -q protected "{guarded_file}"',
        break_cmd=f'"{sys.executable}" -c "import time; time.sleep(5)"',
        file_path=str(guarded_file),
        timeout=0.5,
    )
    out = capsys.readouterr().out
    assert "timed out after 0.5s" in out
    assert guarded_file.read_text() == "protected\n"
    assert code == 1  # the break never happened, so the test did not fail


def test_negcontrol_restores_a_file_the_break_deleted_or_moved(tmp_path, capsys):
    for break_template in ('rm "{f}"', 'mv "{f}" "{f}.moved"'):
        guarded_file = tmp_path / "flag.txt"
        guarded_file.write_text("protected\n")
        code = negcontrol.run(
            test_cmd=f'grep -q protected "{guarded_file}"',
            break_cmd=break_template.format(f=guarded_file),
            file_path=str(guarded_file),
        )
        out = capsys.readouterr().out
        assert guarded_file.read_text() == "protected\n", break_template
        assert "restored" in out and "byte-identical" in out
        assert code == 0, break_template


def test_negcontrol_timeout_kills_processes_the_command_started(tmp_path, capsys):
    import time

    guarded_file = tmp_path / "flag.txt"
    guarded_file.write_text("protected\n")
    late = tmp_path / "late.py"
    late.write_text(
        f"import time\ntime.sleep(1.5)\nopen({str(guarded_file)!r}, 'w').write('broken late\\n')\n"
    )
    starter = tmp_path / "start.py"
    starter.write_text(
        "import subprocess, sys, time\n"
        f"subprocess.Popen([sys.executable, {str(late)!r}])\n"
        "time.sleep(10)\n"
    )
    negcontrol.run(
        test_cmd=f'grep -q protected "{guarded_file}"',
        break_cmd=f'"{sys.executable}" "{starter}"',
        file_path=str(guarded_file),
        timeout=0.5,
    )
    assert "timed out after 0.5s" in capsys.readouterr().out
    time.sleep(2.5)
    assert guarded_file.read_text() == "protected\n", "a process started by the break kept running"


def _guard_and_test(tmp_path):
    """A guarded file, and a test script that fails with 'access denied' once it changes."""
    guarded_file = tmp_path / "flag.txt"
    guarded_file.write_text("protected\n")
    check = tmp_path / "check.py"
    check.write_text(
        f"import sys\nif open({str(guarded_file)!r}).read() != 'protected\\n':\n"
        "    sys.exit('AssertionError: access denied was not enforced')\n"
    )
    return guarded_file, f'"{sys.executable}" "{check}"'


def _corrupt_the_test(tmp_path):
    """Commands that leave the protection alone but put a syntax error in the test."""
    _guard_and_test(tmp_path)
    check = tmp_path / "check.py"
    saved = tmp_path / "check.saved"
    saved.write_text(check.read_text())
    py = f'"{sys.executable}" -c'
    break_cmd = f"{py} \"open(r'{check}', 'w').write('def (')\""
    restore_cmd = f"{py} \"import shutil; shutil.copy(r'{saved}', r'{check}')\""
    return check, break_cmd, restore_cmd


def test_negcontrol_expect_passes_when_the_failure_matches(tmp_path, capsys):
    guarded_file, test_cmd = _guard_and_test(tmp_path)
    code = negcontrol.run(
        test_cmd=test_cmd,
        break_cmd=f'echo broken > "{guarded_file}"',
        file_path=str(guarded_file),
        expect=r"access denied",
    )
    out = capsys.readouterr().out
    assert code == 0, out
    assert "expect FAILURE matching /access denied/" in out
    assert "WARNING" not in out


def test_negcontrol_expect_rejects_a_failure_for_another_reason(tmp_path, capsys):
    # The break leaves the protection alone but corrupts the test itself.
    check, break_cmd, restore_cmd = _corrupt_the_test(tmp_path)
    code = negcontrol.run(
        test_cmd=f'"{sys.executable}" "{check}"',
        break_cmd=break_cmd,
        restore_cmd=restore_cmd,
        expect=r"access denied",
    )
    out = capsys.readouterr().out
    assert code == 1
    assert "does not match --expect /access denied/" in out
    assert "SyntaxError" in out


def test_negcontrol_warns_on_a_crash_without_expect(tmp_path, capsys):
    check, break_cmd, restore_cmd = _corrupt_the_test(tmp_path)
    code = negcontrol.run(
        test_cmd=f'"{sys.executable}" "{check}"',
        break_cmd=break_cmd,
        restore_cmd=restore_cmd,
    )
    out = capsys.readouterr().out
    assert code == 0
    assert "WARNING: the failing output contains 'SyntaxError'" in out
    assert "--expect" in out


def test_negcontrol_rejects_an_invalid_expect(capsys):
    code = negcontrol.run(test_cmd="true", break_cmd="true", restore_cmd="true", expect="(")
    assert code == 2
    assert "--expect is not a valid regular expression" in capsys.readouterr().err


def test_negcontrol_file_without_break_cmd_is_a_usage_error(tmp_path, capsys):
    # A file broken before the run would be backed up broken, then "restored" to that copy.
    guarded_file = tmp_path / "flag.txt"
    guarded_file.write_text("broken\n")
    original = tmp_path / "flag.orig"
    original.write_text("protected\n")
    code = negcontrol.run(
        test_cmd=f'grep -q protected "{guarded_file}"',
        file_path=str(guarded_file),
        restore_cmd=f'cp "{original}" "{guarded_file}"',
    )
    assert code == 2
    assert "--file needs --break-cmd" in capsys.readouterr().err
    assert guarded_file.read_text() == "broken\n"


def test_negcontrol_directory_as_file_is_a_usage_error(tmp_path, capsys):
    code = negcontrol.run(test_cmd="true", break_cmd="true", file_path=str(tmp_path))
    captured = capsys.readouterr()
    assert code == 2
    assert "is not an existing file" in captured.err
    assert "Backup kept" not in captured.err


def test_negcontrol_a_test_that_hangs_does_not_pass(tmp_path, capsys):
    guarded_file = tmp_path / "flag.txt"
    guarded_file.write_text("protected\n")
    hang = f'"{sys.executable}" -c "import time; time.sleep(5)"'
    code = negcontrol.run(
        test_cmd=f'grep -q protected "{guarded_file}" || {hang}',
        break_cmd=f'echo broken > "{guarded_file}"',
        file_path=str(guarded_file),
        timeout=0.5,
    )
    out = capsys.readouterr().out
    assert code == 1
    assert "timed out" in out and "A hang is not a caught break" in out
    assert "OK:" not in out
    assert guarded_file.read_text() == "protected\n"
