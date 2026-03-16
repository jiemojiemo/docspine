import re

from docling_progressive.models import DocumentNode


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "section"


def build_outline_tree(markdown: str) -> DocumentNode:
    lines = markdown.splitlines()
    headings = [line for line in lines if line.startswith("# ")]
    root_title = headings[0][2:].strip() if headings else "Document"
    root = DocumentNode(
        node_id="root",
        title=root_title,
        slug=slugify(root_title),
        level=0,
        summary="",
    )

    current_child: DocumentNode | None = None
    root_content: list[str] = []

    for line in lines[1:] if headings else lines:
        if line.startswith("## "):
            title = line[3:].strip()
            current_child = DocumentNode(
                node_id=slugify(title),
                title=title,
                slug=slugify(title),
                level=1,
                summary="",
            )
            root.children.append(current_child)
            continue

        if current_child is None:
            root_content.append(line)
        else:
            current_child.content = "\n".join(
                part for part in [current_child.content, line] if part
            )

    root.content = "\n".join(line for line in root_content if line).strip()
    return root
