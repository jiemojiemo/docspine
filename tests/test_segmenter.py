from docling_progressive.models import DocumentNode
from docling_progressive.segmenter import split_oversized_leaf


def test_split_oversized_leaf_creates_part_children_when_needed():
    leaf = DocumentNode(
        node_id="long-section",
        title="Long Section",
        slug="long-section",
        level=1,
        summary="summary",
        content="\n\n".join([f"Paragraph {i}" for i in range(12)]),
    )

    result = split_oversized_leaf(leaf, max_paragraphs=4)

    assert [child.slug for child in result.children] == [
        "long-section-part-1",
        "long-section-part-2",
        "long-section-part-3",
    ]
