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
    out = capsys.readouterr().out
    assert code == 2
    assert "error: pass --break-cmd, or --restore-cmd" in out


def test_negcontrol_missing_file_and_restore_cmd(capsys):
    code = negcontrol.run(test_cmd="true", break_cmd="echo 1")
    out = capsys.readouterr().out
    assert code == 2
    assert "without --file, --restore-cmd is required" in out


def test_negcontrol_nonexistent_file(capsys):
    code = negcontrol.run(
        test_cmd="true", break_cmd="echo 1", file_path="nonexistent_file_12345.txt"
    )
    out = capsys.readouterr().out
    assert code == 2
    assert "does not exist" in out


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


def test_negcontrol_main_cli(tmp_path):
    guarded_file = tmp_path / "flag.txt"
    guarded_file.write_text("protected\n")
    code = negcontrol.main(
        [
            "--test-cmd",
            f'grep -q protected "{guarded_file}"',
            "--break-cmd",
            f'echo broken > "{guarded_file}"',
            "--file",
            str(guarded_file),
        ]
    )
    assert code == 0


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
