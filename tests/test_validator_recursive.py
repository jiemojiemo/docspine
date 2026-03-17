from docspine.validator import validate_output_tree


def test_validate_output_tree_checks_nested_sections(tmp_path):
    (tmp_path / "index.md").write_text("# Root\n", encoding="utf-8")
    (tmp_path / "content.md").write_text("root", encoding="utf-8")
    child_dir = tmp_path / "sections" / "01-child"
    child_dir.mkdir(parents=True)
    (child_dir / "index.md").write_text("# Child\n", encoding="utf-8")
    (child_dir / "content.md").write_text("child", encoding="utf-8")

    issues = validate_output_tree(tmp_path)

    assert issues == [f"Missing node.json at {child_dir}"]
