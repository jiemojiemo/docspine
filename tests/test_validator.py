from docspine.validator import validate_output_tree


def test_validate_output_tree_reports_missing_content_file(tmp_path):
    (tmp_path / "index.md").write_text("# Title\n", encoding="utf-8")
    issues = validate_output_tree(tmp_path)

    assert issues == ["Missing content.md at root"]


def test_validate_output_tree_reports_missing_root_index(tmp_path):
    (tmp_path / "content.md").write_text("body", encoding="utf-8")

    issues = validate_output_tree(tmp_path)

    assert "Missing index.md at root" in issues
