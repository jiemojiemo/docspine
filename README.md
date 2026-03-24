# DocSpine

<p align="center">
  <a href="README.md">English</a> &bull;
  <a href="README.zh.md">中文</a>
</p>

---

PDFs are too long for AI agents to read efficiently. DocSpine converts a PDF into a navigable tree of Markdown files, so agents can locate and read only what they need.

## How It Works

Instead of dumping the full PDF text at an agent, DocSpine produces a tree where each node has:

- `index.md` — section list with word count, table presence, and page hints so the agent can decide what to open
- `content.md` — full text of that section
- `node.json` — machine-readable metadata

The agent starts at the root `index.md`, reads the hints, and drills into only the sections relevant to its task.

## Output Format

```text
out/
  AGENTS.md         ← read this first
  index.md          ← navigation surface
  content.md        ← root-level text
  node.json         ← root metadata
  sections/
    01-section-slug/
      index.md
      content.md
      node.json
```

### index.md example

```markdown
# 冰轮环境技术股份有限公司

## Subsections
- [第一节 重要提示、目录和释义](sections/01-.../index.md) — 381 words · tables · p.2
- [第二节 公司简介和主要财务指标](sections/02-.../index.md) — 567 words · tables · p.6
- [第三节 管理层讨论与分析](sections/03-.../index.md) — 3,017 words · tables · p.10
```

### node.json fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique node identifier |
| `title` | string | Section title |
| `slug` | string | URL-safe title |
| `level` | int | Depth in tree (0 = root) |
| `word_count` | int | Word count of this section's content |
| `has_tables` | bool | Whether the section contains Markdown tables |
| `asset_count` | int | Number of referenced assets (images, tables) |
| `asset_types` | string[] | Distinct asset types present |
| `page_start` | int? | Starting page in the source PDF (when available) |
| `children` | string[] | IDs of child nodes |

## Usage

Install dependencies:

```bash
uv sync --group dev
```

Build from a PDF:

```bash
uv run docspine build input.pdf --out out
```

Debug with a page range:

```bash
uv run docspine build input.pdf --out out --pages 1-30
```

Run tests:

```bash
uv run --group dev pytest
```

## For AI Agents

Start by reading `AGENTS.md` and `index.md` in the output root. Use the hints on each link to decide where to look:

- Skip sections with low `word_count` if you need detailed content
- Prioritise sections where `has_tables` is true for structured data
- Use `page_start` to cross-reference the original PDF if needed
- Open `content.md` only when the index confirms the section is relevant
- Recurse into `sections/` subdirectories for deeper hierarchy

The structure priority used during conversion is: **PDF outline bookmarks → textual table of contents → heading scan**.
