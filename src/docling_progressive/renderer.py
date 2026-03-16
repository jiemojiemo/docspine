import json
from hashlib import sha1
from pathlib import Path

from docling_progressive.models import DocumentNode

MAX_DIRECTORY_NAME_LENGTH = 120


def render_node_tree(node: DocumentNode, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "index.md").write_text(_render_index(node), encoding="utf-8")
    (output_dir / "content.md").write_text(node.content, encoding="utf-8")
    (output_dir / "node.json").write_text(
        json.dumps(
            {
                "id": node.node_id,
                "title": node.title,
                "slug": node.slug,
                "level": node.level,
                "summary": node.summary,
                "children": [child.node_id for child in node.children],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    if not node.children:
        return

    sections_dir = output_dir / "sections"
    for index, child in enumerate(node.children, start=1):
        child_dir = sections_dir / _build_child_directory_name(index, child.slug)
        render_node_tree(child, child_dir)


def _render_index(node: DocumentNode) -> str:
    lines = [f"# {node.title}"]
    if node.summary:
        lines.extend(["", node.summary])
    if node.children:
        lines.extend(["", "## Subsections"])
        for index, child in enumerate(node.children, start=1):
            lines.append(
                f"- [{{child.title}}](sections/{index:02d}-{child.slug}/index.md)".format(
                    child=child
                )
            )
    return "\n".join(lines).strip() + "\n"


def _build_child_directory_name(index: int, slug: str) -> str:
    prefix = f"{index:02d}-"
    safe_slug = _truncate_slug(slug, max_length=MAX_DIRECTORY_NAME_LENGTH - len(prefix))
    return f"{prefix}{safe_slug}"


def _truncate_slug(slug: str, max_length: int) -> str:
    if len(slug) <= max_length:
        return slug

    digest = sha1(slug.encode("utf-8")).hexdigest()[:8]
    reserved = len(digest) + 1
    trimmed = slug[: max_length - reserved].rstrip("-")
    return f"{trimmed}-{digest}"
