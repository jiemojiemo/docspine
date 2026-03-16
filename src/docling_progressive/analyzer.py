import re
import unicodedata

from docling_progressive.models import DocumentNode

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
        node = DocumentNode(
            node_id=slug,
            title=title,
            slug=slug,
            level=level,
            summary="",
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
            line
            for line in lines[current_index + 1 : end_index]
            if line and not line.startswith("|")
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
            line
            for line in lines[start_index + 1 : end_index]
            if line and not line.startswith("|")
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
