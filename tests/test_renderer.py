import json
from pathlib import Path

from docspine.models import AssetRef, DocumentNode
from docspine.renderer import render_node_tree


def test_render_node_tree_writes_index_content_and_metadata(tmp_path):
    root = DocumentNode(
        node_id="root",
        title="Annual Report",
        slug="annual-report",
        level=0,
        summary="Top summary",
        content="Root content",
    )

    render_node_tree(root, tmp_path)

    assert (tmp_path / "index.md").exists()
    assert (tmp_path / "content.md").exists()
    metadata = json.loads((tmp_path / "node.json").read_text())
    assert metadata["title"] == "Annual Report"


def test_render_node_tree_truncates_long_child_directory_names(tmp_path):
    long_slug = "very-long-section-" + ("x" * 240)
    root = DocumentNode(
        node_id="root",
        title="Annual Report",
        slug="annual-report",
        level=0,
        summary="Top summary",
        content="Root content",
        children=[
            DocumentNode(
                node_id="child",
                title="Long Child",
                slug=long_slug,
                level=1,
                summary="",
                content="Child content",
            )
        ],
    )

    render_node_tree(root, tmp_path)

    child_dirs = [path.name for path in (tmp_path / "sections").iterdir() if path.is_dir()]
    assert len(child_dirs) == 1
    assert len(child_dirs[0]) <= 120
    assert child_dirs[0].startswith("01-very-long-section-")


def test_render_node_tree_keeps_duplicate_truncated_directory_names_unique(tmp_path):
    shared_slug = "shared-" + ("x" * 240)
    root = DocumentNode(
        node_id="root",
        title="Annual Report",
        slug="annual-report",
        level=0,
        summary="Top summary",
        content="Root content",
        children=[
            DocumentNode(
                node_id="child-1",
                title="Child One",
                slug=shared_slug,
                level=1,
                summary="",
                content="Child content 1",
            ),
            DocumentNode(
                node_id="child-2",
                title="Child Two",
                slug=shared_slug,
                level=1,
                summary="",
                content="Child content 2",
            ),
        ],
    )

    render_node_tree(root, tmp_path)

    child_dirs = sorted(path.name for path in (tmp_path / "sections").iterdir() if path.is_dir())
    assert len(child_dirs) == 2
    assert child_dirs[0] != child_dirs[1]


def test_render_node_tree_writes_readable_utf8_metadata(tmp_path):
    root = DocumentNode(
        node_id="第一节-重要提示-目录和释义",
        title="第一节 重要提示、目录和释义",
        slug="第一节-重要提示-目录和释义",
        level=1,
        summary="",
        content="正文",
    )

    render_node_tree(root, tmp_path)

    metadata_text = (tmp_path / "node.json").read_text(encoding="utf-8")
    assert "\\u7b2c" not in metadata_text
    assert "第一节 重要提示、目录和释义" in metadata_text


def test_render_node_tree_writes_root_agent_and_context_files(tmp_path):
    root = DocumentNode(
        node_id="root",
        title="Annual Report",
        slug="annual-report",
        level=0,
        summary="Top summary",
        content="Root content",
    )

    render_node_tree(
        root,
        tmp_path,
        source_path=Path("/docs/sample.pdf"),
        metadata={"backend": "docling", "total_pages": 12, "outline": []},
    )

    assert (tmp_path / "AGENT.md").exists()
    assert (tmp_path / "context.md").exists()


def test_render_node_tree_root_agent_and_context_include_key_guidance(tmp_path):
    root = DocumentNode(
        node_id="root",
        title="Annual Report",
        slug="annual-report",
        level=0,
        summary="Top summary",
        content="Root content",
    )

    render_node_tree(
        root,
        tmp_path,
        source_path=Path("/docs/sample.pdf"),
        metadata={"backend": "docling", "total_pages": 12, "outline": [{"title": "One"}]},
    )

    agent_text = (tmp_path / "AGENT.md").read_text(encoding="utf-8")
    context_text = (tmp_path / "context.md").read_text(encoding="utf-8")

    assert "index.md" in agent_text
    assert "node.json" in agent_text
    assert "/docs/sample.pdf" in agent_text
    assert "PDF outline" in context_text
    assert "source_path" in context_text


# --- node.json metadata ---

def test_node_json_includes_word_count(tmp_path):
    node = DocumentNode(
        node_id="root", title="Report", slug="report", level=0, summary="",
        content="one two three four five",
    )
    render_node_tree(node, tmp_path)
    meta = json.loads((tmp_path / "node.json").read_text())
    assert meta["word_count"] == 5


def test_node_json_word_count_is_zero_for_empty_content(tmp_path):
    node = DocumentNode(
        node_id="root", title="Report", slug="report", level=0, summary="", content="",
    )
    render_node_tree(node, tmp_path)
    meta = json.loads((tmp_path / "node.json").read_text())
    assert meta["word_count"] == 0


def test_node_json_has_tables_true_when_content_has_markdown_table(tmp_path):
    node = DocumentNode(
        node_id="root", title="Report", slug="report", level=0, summary="",
        content="Intro.\n| Col A | Col B |\n|---|---|\n| 1 | 2 |",
    )
    render_node_tree(node, tmp_path)
    meta = json.loads((tmp_path / "node.json").read_text())
    assert meta["has_tables"] is True


def test_node_json_has_tables_false_when_no_table(tmp_path):
    node = DocumentNode(
        node_id="root", title="Report", slug="report", level=0, summary="",
        content="Just plain text. No tables here.",
    )
    render_node_tree(node, tmp_path)
    meta = json.loads((tmp_path / "node.json").read_text())
    assert meta["has_tables"] is False


def test_node_json_includes_asset_count_and_types(tmp_path):
    node = DocumentNode(
        node_id="root", title="Report", slug="report", level=0, summary="",
        content="body",
        assets=[
            AssetRef(asset_id="a1", asset_type="image", path="img1.png"),
            AssetRef(asset_id="a2", asset_type="table", path="tbl1.csv"),
            AssetRef(asset_id="a3", asset_type="image", path="img2.png"),
        ],
    )
    render_node_tree(node, tmp_path)
    meta = json.loads((tmp_path / "node.json").read_text())
    assert meta["asset_count"] == 3
    assert meta["asset_types"] == ["image", "table"]


def test_node_json_includes_page_start_when_set(tmp_path):
    node = DocumentNode(
        node_id="root", title="Report", slug="report", level=0, summary="",
        content="body", page_start=42,
    )
    render_node_tree(node, tmp_path)
    meta = json.loads((tmp_path / "node.json").read_text())
    assert meta["page_start"] == 42


def test_node_json_omits_page_start_when_none(tmp_path):
    node = DocumentNode(
        node_id="root", title="Report", slug="report", level=0, summary="",
        content="body", page_start=None,
    )
    render_node_tree(node, tmp_path)
    meta = json.loads((tmp_path / "node.json").read_text())
    assert "page_start" not in meta


def test_node_json_does_not_include_summary(tmp_path):
    node = DocumentNode(
        node_id="root", title="Report", slug="report", level=0, summary="ignore me",
        content="body",
    )
    render_node_tree(node, tmp_path)
    meta = json.loads((tmp_path / "node.json").read_text())
    assert "summary" not in meta


# --- index.md hints ---

def _make_root_with_child(content: str, page_start: int | None = None) -> DocumentNode:
    child = DocumentNode(
        node_id="sec", title="Section One", slug="section-one", level=1, summary="",
        content=content, page_start=page_start,
    )
    return DocumentNode(
        node_id="root", title="Report", slug="report", level=0, summary="",
        content="", children=[child],
    )


def test_index_md_shows_word_count_hint_for_children(tmp_path):
    root = _make_root_with_child("alpha beta gamma")
    render_node_tree(root, tmp_path)
    index = (tmp_path / "index.md").read_text()
    assert "3 words" in index


def test_index_md_shows_tables_hint_when_child_has_table(tmp_path):
    root = _make_root_with_child("| A | B |\n|---|---|\n| 1 | 2 |")
    render_node_tree(root, tmp_path)
    index = (tmp_path / "index.md").read_text()
    assert "tables" in index


def test_index_md_shows_page_hint_when_child_has_page_start(tmp_path):
    root = _make_root_with_child("some content", page_start=15)
    render_node_tree(root, tmp_path)
    index = (tmp_path / "index.md").read_text()
    assert "p.15" in index


def test_index_md_shows_no_hint_for_empty_child(tmp_path):
    root = _make_root_with_child("")
    render_node_tree(root, tmp_path)
    index = (tmp_path / "index.md").read_text()
    assert " — " not in index
