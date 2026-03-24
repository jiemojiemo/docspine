import json
from hashlib import sha1
from pathlib import Path

from docspine.models import DocumentNode

MAX_DIRECTORY_NAME_LENGTH = 120


def render_node_tree(
    node: DocumentNode,
    output_dir: Path,
    *,
    source_path: Path | None = None,
    metadata: dict | None = None,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "index.md").write_text(_render_index(node), encoding="utf-8")
    (output_dir / "content.md").write_text(node.content, encoding="utf-8")
    asset_types = sorted({a.asset_type for a in node.assets})
    node_meta: dict = {
        "id": node.node_id,
        "title": node.title,
        "slug": node.slug,
        "level": node.level,
        "word_count": len(node.content.split()) if node.content else 0,
        "has_tables": _has_tables(node.content),
        "asset_count": len(node.assets),
        "asset_types": asset_types,
        "children": [child.node_id for child in node.children],
    }
    if node.page_start is not None:
        node_meta["page_start"] = node.page_start
    if node.page_end is not None:
        node_meta["page_end"] = node.page_end
    if node.structure_status is not None:
        node_meta["structure_status"] = node.structure_status
    if node.content_status is not None:
        node_meta["content_status"] = node.content_status
    (output_dir / "node.json").write_text(
        json.dumps(node_meta, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    if node.level == 0:
        (output_dir / "AGENTS.md").write_text(
            _render_agent_guide(node, source_path=source_path, metadata=metadata or {}),
            encoding="utf-8",
        )
        (output_dir / "context.md").write_text(
            _render_context(node, source_path=source_path, metadata=metadata or {}),
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
            hint = _section_hint(child)
            link = f"- [{child.title}](sections/{index:02d}-{child.slug}/index.md)"
            lines.append(f"{link}{hint}")
    return "\n".join(lines).strip() + "\n"


def _section_hint(node: DocumentNode) -> str:
    parts = []
    word_count = len(node.content.split()) if node.content else 0
    if word_count > 0:
        parts.append(f"{word_count:,} words")
    if _has_tables(node.content):
        parts.append("tables")
    if node.page_start is not None:
        parts.append(f"p.{node.page_start}")
    return f" — {' · '.join(parts)}" if parts else ""


def _has_tables(content: str) -> bool:
    if not content:
        return False
    return any(line.startswith("|") for line in content.splitlines())


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


def _render_agent_guide(
    node: DocumentNode, *, source_path: Path | None, metadata: dict
) -> str:
    source = str(source_path) if source_path is not None else "unknown"
    return (
        "# AGENTS Guide\n\n"
        f"Source PDF: `{source}`\n\n"
        "Read order:\n"
        "- Start with `index.md` for section navigation.\n"
        "- Open `content.md` only when you need the full text of the current node.\n"
        "- Use `node.json` for machine-readable metadata such as title, level, and children.\n"
        "- Browse subnodes under `sections/`.\n"
    )


def _render_context(
    node: DocumentNode, *, source_path: Path | None, metadata: dict
) -> str:
    source = str(source_path) if source_path is not None else "unknown"
    outline_state = "available" if metadata.get("outline") else "not available"
    backend = metadata.get("backend", "unknown")
    total_pages = metadata.get("total_pages", "unknown")
    return (
        "# Context\n\n"
        f"- source_path: `{source}`\n"
        f"- title: `{node.title}`\n"
        f"- backend: `{backend}`\n"
        f"- total_pages: `{total_pages}`\n"
        f"- PDF outline: {outline_state}\n"
        "- Structure priority: PDF outline > textual table of contents > heading scan.\n"
        "- Key files: `index.md`, `content.md`, `node.json`, `sections/`.\n"
    )
