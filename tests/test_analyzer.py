from docling_progressive.analyzer import build_outline_tree


def test_build_outline_tree_groups_content_under_headings():
    markdown = "\n".join(
        [
            "# Annual Report",
            "Intro paragraph.",
            "## Business Overview",
            "Business content.",
            "## Risk Factors",
            "Risk content.",
        ]
    )

    root = build_outline_tree(markdown)

    assert root.title == "Annual Report"
    assert [child.title for child in root.children] == [
        "Business Overview",
        "Risk Factors",
    ]
