# DocSpine

`DocSpine` converts a PDF into a progressively disclosed document tree for agent-style navigation.

## Output Layout

Each run writes a root node plus nested section nodes:

```text
out/
  index.md
  content.md
  node.json
  sections/
    01-section-slug/
      index.md
      content.md
      node.json
```

`index.md` is the navigation surface, `content.md` contains the full section text, and `node.json` exposes machine-readable metadata.

## Usage

Install dependencies:

```bash
uv sync --group dev
```

Build a package from a PDF:

```bash
uv run docspine build input.pdf --out out
```

Run tests with coverage:

```bash
uv run --group dev pytest --cov=src/docspine --cov-report=term-missing
```
