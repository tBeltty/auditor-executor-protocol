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
