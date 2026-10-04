from auditkit import lint, scaffold


def test_init_creates_all_four_documents(tmp_path):
    target = tmp_path / "run"
    code = scaffold.run(str(target), project_name="Test Project")
    assert code == 0
    assert (target / "plan-of-record.md").exists()
    assert (target / "execution-guide.md").exists()
    assert (target / "compliance-log.md").exists()
    assert (target / "annexes").is_dir()


def test_init_substitutes_project_name(tmp_path):
    target = tmp_path / "run"
    scaffold.run(str(target), project_name="Widget Migration")
    text = (target / "plan-of-record.md").read_text()
    assert "Widget Migration" in text
    assert "{{PROJECT_NAME}}" not in text


def test_init_does_not_overwrite_without_force(tmp_path, capsys):
    target = tmp_path / "run"
    scaffold.run(str(target), project_name="First")
    (target / "plan-of-record.md").write_text("edited by hand")
    scaffold.run(str(target), project_name="Second")
    assert (target / "plan-of-record.md").read_text() == "edited by hand"


def test_init_force_overwrites(tmp_path):
    target = tmp_path / "run"
    scaffold.run(str(target), project_name="First")
    (target / "plan-of-record.md").write_text("edited by hand")
    scaffold.run(str(target), project_name="Second", force=True)
    assert "edited by hand" not in (target / "plan-of-record.md").read_text()


def test_init_scaffold_passes_lint(tmp_path):
    target = tmp_path / "run"
    scaffold.run(str(target), project_name="Clean Run")
    assert lint.run(str(target)) == 0


def test_init_on_an_existing_file_is_a_usage_error(tmp_path, capsys):
    target = tmp_path / "notes.md"
    target.write_text("keep me\n")
    assert scaffold.run(str(target)) == 2
    assert "is not a directory" in capsys.readouterr().err
    assert target.read_text() == "keep me\n"
