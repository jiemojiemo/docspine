from pathlib import Path
import re
import unicodedata

from docspine.converter.models import ConversionChunk
from docspine.models import DocumentNode

SECTION_PATTERN = re.compile(
    r"^(?:(#+)\s+.+|\d+(?:\.\d+)*\s*[、.．]\s*.+|[图表]\s*\d+\s*[：:]\s*.+)$"
)
DATE_PATTERN = re.compile(r"^\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日$")
TOC_SECTION_PATTERN = re.compile(r"(第[一二三四五六七八九十百]+节\s+[^\.。\|]+?)\s+\.*\s+\d+")


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value.strip()).lower()
    normalized = re.sub(r"[^\w\u4e00-\u9fff]+", "-", normalized, flags=re.UNICODE)
    slug = normalized.strip("-").replace("_", "-")
    return slug or "section"


def build_outline_tree(markdown: str, metadata: dict | None = None) -> DocumentNode:
    lines = [line.strip() for line in markdown.splitlines()]
    root_title, root_line_index = _detect_root_title(lines)
    root = DocumentNode(
        node_id="root",
        title=root_title,
        slug=slugify(root_title),
        level=0,
        summary="",
    )

    outline_entries = _extract_outline_entries(metadata or {})
    if outline_entries:
        root.children = _build_children_from_outline(lines, outline_entries, root_line_index)
        return root

    toc_titles, toc_start_index = _extract_toc_section_titles(lines)
    if toc_titles:
        root.children = _build_children_from_toc(lines, toc_titles, toc_start_index)
        return root

    current_child: DocumentNode | None = None
    root_content: list[str] = []
    seen_slugs: dict[str, int] = {}
    consume_root_prefix = True

    for index, line in enumerate(lines):
        if index < root_line_index:
            continue
        if not line or line == f"# {root_title}" or line == root_title:
            continue

        if _is_section_heading(line):
            consume_root_prefix = False
            title = _normalize_heading_title(line)
            slug = _dedupe_slug(slugify(title), seen_slugs)
            current_child = DocumentNode(
                node_id=slug,
                title=title,
                slug=slug,
                level=1,
                summary="",
            )
            root.children.append(current_child)
            continue

        if consume_root_prefix and _is_front_matter_noise(line):
            continue

        if current_child is None:
            root_content.append(line)
        else:
            current_child.content = "\n".join(
                part for part in [current_child.content, line] if part
            )

    root.content = "\n".join(root_content).strip()
    return root


def build_stream_skeleton(
    metadata: dict | None = None, initial_markdown_hint: str | None = None
) -> DocumentNode:
    info = metadata or {}
    root_title = _derive_stream_root_title(info, initial_markdown_hint)
    root = DocumentNode(
        node_id="root",
        title=root_title,
        slug=slugify(root_title),
        level=0,
        summary="",
        structure_status="ready",
        content_status="pending",
    )

    outline_entries = _extract_outline_entries(info)
    total_pages = int(info.get("page_range", (1, info.get("total_pages", 1)))[1])

    if outline_entries:
        root.children = _build_stream_children_from_outline(outline_entries)
        _assign_page_end_ranges(root.children, total_pages)
        _set_stream_statuses(root.children, structure_status="ready", content_status="pending")
        return root

    if initial_markdown_hint:
        provisional_root = build_outline_tree(initial_markdown_hint, info)
        _set_stream_statuses(
            [provisional_root], structure_status="ready", content_status="pending"
        )
        return provisional_root

    return root


def assign_chunk_to_nodes(root: DocumentNode, chunk: ConversionChunk) -> list[DocumentNode]:
    target = _find_best_target_node(root, chunk.page_start, chunk.page_end)
    target.content = "\n\n".join(part for part in [target.content, chunk.markdown] if part).strip()
    target.content_status = "partial"
    root.content_status = "partial"
    return [target]


def finalize_stream_tree(
    root: DocumentNode, all_chunks: list[ConversionChunk], metadata: dict | None = None
) -> DocumentNode:
    markdown = "\n\n".join(chunk.markdown for chunk in all_chunks if chunk.markdown.strip())
    if markdown:
        final_root = build_outline_tree(markdown, metadata=metadata)
        if (
            root.title
            and root.title != "Document"
            and (not final_root.children or final_root.title == final_root.children[0].title)
        ):
            final_root.title = root.title
            final_root.slug = slugify(root.title)
    else:
        final_root = root
    set_stream_statuses(
        final_root, structure_status="ready", content_status="complete"
    )
    return final_root


def set_stream_statuses(
    root: DocumentNode, *, structure_status: str, content_status: str
) -> None:
    _set_stream_statuses(
        [root], structure_status=structure_status, content_status=content_status
    )


def _detect_root_title(lines: list[str]) -> tuple[str, int]:
    for index, line in enumerate(lines):
        if not line.startswith("#"):
            continue
        title = _normalize_heading_title(line)
        if _is_front_matter_noise(title) or _is_section_heading(title):
            continue
        return title, index

    candidates = [
        (index, line)
        for index, line in enumerate(lines)
        if line
        and not line.startswith("<!--")
        and not DATE_PATTERN.match(line)
        and not _is_front_matter_noise(line)
        and not _is_section_heading(line)
    ]
    if candidates:
        index, title = candidates[0]
        return title, index
    return "Document", 0


def _derive_stream_root_title(metadata: dict, initial_markdown_hint: str | None) -> str:
    if initial_markdown_hint:
        title, _ = _detect_root_title([line.strip() for line in initial_markdown_hint.splitlines()])
        if title and title != "Document":
            return title

    source = metadata.get("source")
    if isinstance(source, str) and source:
        stem = Path(source).stem.strip()
        if stem:
            return stem
    return "Document"


def _is_section_heading(line: str) -> bool:
    return bool(SECTION_PATTERN.match(line))


def _normalize_heading_title(line: str) -> str:
    if line.startswith("#"):
        return line.lstrip("#").strip()
    return line


def _is_front_matter_noise(line: str) -> bool:
    noise_tokens = (
        "金融工程研究团队",
        "分析师",
        "研究员",
        "首席",
        "金融工程团队",
        "开源证券",
        "相关研究报告",
        "目 录",
    )
    return any(token in line for token in noise_tokens)


def _dedupe_slug(base_slug: str, seen_slugs: dict[str, int]) -> str:
    count = seen_slugs.get(base_slug, 0) + 1
    seen_slugs[base_slug] = count
    if count == 1:
        return base_slug
    return f"{base_slug}-{count}"


def _extract_toc_section_titles(lines: list[str]) -> tuple[list[str], int]:
    toc_started = False
    titles: list[str] = []
    seen: set[str] = set()
    toc_start_index = -1

    for index, line in enumerate(lines):
        if line == "## 目 录":
            toc_started = True
            toc_start_index = index
            continue
        if not toc_started:
            continue
        if line.startswith("## ") and line != "## 目 录":
            break
        if not line.startswith("|"):
            continue
        for match in TOC_SECTION_PATTERN.finditer(line):
            title = " ".join(match.group(1).split())
            if title in seen:
                continue
            seen.add(title)
            titles.append(title)
    return titles, toc_start_index


def _extract_outline_entries(metadata: dict) -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []
    seen: set[tuple[str, int]] = set()
    for item in metadata.get("outline", []):
        level = int(item.get("level", 0))
        if level < 1:
            continue
        title = " ".join(str(item.get("title", "")).split())
        key = (title, level)
        if not title or key in seen:
            continue
        seen.add(key)
        entries.append({"title": title, "level": level, "page": item.get("page")})
    return entries


def _build_children_from_outline(
    lines: list[str], outline_entries: list[dict[str, object]], start_index: int
) -> list[DocumentNode]:
    heading_index_by_title: dict[str, int] = {}
    for index, line in enumerate(lines):
        if index <= start_index or not line.startswith("## "):
            continue
        title = _normalize_heading_title(line)
        if title not in heading_index_by_title:
            heading_index_by_title[title] = index

    seen_slugs: dict[str, int] = {}
    nodes_with_level: list[tuple[DocumentNode, int]] = []
    stack: list[tuple[DocumentNode, int]] = []

    for entry in outline_entries:
        title = str(entry["title"])
        level = int(entry["level"])
        slug = _dedupe_slug(slugify(title), seen_slugs)
        page = entry.get("page")
        node = DocumentNode(
            node_id=slug,
            title=title,
            slug=slug,
            level=level,
            summary="",
            page_start=int(page) if page is not None else None,
        )
        nodes_with_level.append((node, level))

        while stack and stack[-1][1] >= level:
            stack.pop()
        if stack:
            stack[-1][0].children.append(node)
        stack.append((node, level))

    ordered_positions = [
        (node, level, heading_index_by_title.get(node.title))
        for node, level in nodes_with_level
        if node.title in heading_index_by_title
    ]
    sorted_positions = sorted(
        ((node, level, index) for node, level, index in ordered_positions if index is not None),
        key=lambda item: item[2],
    )
    position_lookup = {node.title: index for node, _, index in sorted_positions}

    for node, level in nodes_with_level:
        current_index = position_lookup.get(node.title)
        if current_index is None:
            continue
        later = [
            index
            for other_node, other_level, index in sorted_positions
            if index > current_index and other_level <= level
        ]
        end_index = later[0] if later else len(lines)
        node.content = "\n".join(
            line for line in lines[current_index + 1 : end_index] if line
        ).strip()

    return [node for node, level in nodes_with_level if level == 1]


def _build_children_from_toc(
    lines: list[str], toc_titles: list[str], toc_start_index: int
) -> list[DocumentNode]:
    heading_index_by_title: dict[str, int] = {}
    for index, line in enumerate(lines):
        if index <= toc_start_index:
            continue
        if not line.startswith("## "):
            continue
        title = _normalize_heading_title(line)
        if title in toc_titles and title not in heading_index_by_title:
            heading_index_by_title[title] = index

    matched_titles = [title for title in toc_titles if title in heading_index_by_title]
    if not matched_titles:
        return []

    ordered_positions = [
        (title, heading_index_by_title[title]) for title in matched_titles
    ]
    next_start_positions = [position for _, position in sorted(ordered_positions, key=lambda item: item[1])]

    seen_slugs: dict[str, int] = {}
    children: list[DocumentNode] = []
    for title, start_index in ordered_positions:
        later_positions = [position for position in next_start_positions if position > start_index]
        end_index = later_positions[0] if later_positions else len(lines)
        content = "\n".join(
            line for line in lines[start_index + 1 : end_index] if line
        ).strip()
        slug = _dedupe_slug(slugify(title), seen_slugs)
        children.append(
            DocumentNode(
                node_id=slug,
                title=title,
                slug=slug,
                level=1,
                summary="",
                content=content,
            )
        )
    return children


def _build_stream_children_from_outline(
    outline_entries: list[dict[str, object]]
) -> list[DocumentNode]:
    seen_slugs: dict[str, int] = {}
    nodes_with_level: list[tuple[DocumentNode, int]] = []
    stack: list[tuple[DocumentNode, int]] = []

    for entry in outline_entries:
        title = str(entry["title"])
        level = int(entry["level"])
        slug = _dedupe_slug(slugify(title), seen_slugs)
        page = entry.get("page")
        node = DocumentNode(
            node_id=slug,
            title=title,
            slug=slug,
            level=level,
            summary="",
            page_start=int(page) if page is not None else None,
        )
        nodes_with_level.append((node, level))

        while stack and stack[-1][1] >= level:
            stack.pop()
        if stack:
            stack[-1][0].children.append(node)
        stack.append((node, level))

    return [node for node, level in nodes_with_level if level == 1]


def _assign_page_end_ranges(nodes: list[DocumentNode], total_pages: int) -> None:
    flat_nodes = _flatten_nodes_with_pages(nodes)
    for index, node in enumerate(flat_nodes):
        current_start = node.page_start
        if current_start is None:
            continue
        next_page = next(
            (
                other.page_start
                for other in flat_nodes[index + 1 :]
                if other.page_start is not None and other.page_start > current_start
            ),
            None,
        )
        node.page_end = total_pages if next_page is None else next_page - 1


def _flatten_nodes_with_pages(nodes: list[DocumentNode]) -> list[DocumentNode]:
    result: list[DocumentNode] = []
    for node in nodes:
        result.append(node)
        result.extend(_flatten_nodes_with_pages(node.children))
    return result


def _find_best_target_node(
    root: DocumentNode, chunk_page_start: int, chunk_page_end: int
) -> DocumentNode:
    current = root
    while True:
        matching_children = [
            child
            for child in current.children
            if child.page_start is not None
            and child.page_end is not None
            and child.page_start <= chunk_page_start
            and chunk_page_end <= child.page_end
        ]
        if not matching_children:
            return current
        current = matching_children[0]


def _set_stream_statuses(
    nodes: list[DocumentNode], *, structure_status: str, content_status: str
) -> None:
    for node in nodes:
        node.structure_status = structure_status
        node.content_status = content_status
        if node.children:
            _set_stream_statuses(
                node.children,
                structure_status=structure_status,
                content_status=content_status,
            )
