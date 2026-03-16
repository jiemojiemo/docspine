import json

from docling_progressive.models import DocumentNode
from docling_progressive.renderer import render_node_tree


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
