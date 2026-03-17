import json
from pathlib import Path

from docspine.models import DocumentNode
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
