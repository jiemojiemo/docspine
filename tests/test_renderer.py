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
