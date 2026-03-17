from docspine.models import DocumentNode


def split_oversized_leaf(node: DocumentNode, max_paragraphs: int) -> DocumentNode:
    paragraphs = [part for part in node.content.split("\n\n") if part.strip()]
    if len(paragraphs) <= max_paragraphs:
        return node

    node.children = []
    for start in range(0, len(paragraphs), max_paragraphs):
        part_number = start // max_paragraphs + 1
        node.children.append(
            DocumentNode(
                node_id=f"{node.slug}-part-{part_number}",
                title=f"{node.title} Part {part_number}",
                slug=f"{node.slug}-part-{part_number}",
                level=node.level + 1,
                summary=node.summary,
                content="\n\n".join(paragraphs[start : start + max_paragraphs]),
            )
        )
    return node


def segment_tree(node: DocumentNode, max_paragraphs: int = 8) -> DocumentNode:
    if node.children:
        node.children = [segment_tree(child, max_paragraphs) for child in node.children]
        return node
    return split_oversized_leaf(node, max_paragraphs=max_paragraphs)
