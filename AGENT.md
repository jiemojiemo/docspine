# Project Guide

## What This Repo Does

`DocSpine` converts a PDF into a progressive document tree for agent navigation.

Core flow:
- `cli.py`: parses `docspine build ...`
- `pipeline.py`: orchestrates convert -> analyze -> segment -> render -> validate
- `converter/docling_backend.py`: runs Docling, extracts PDF outline metadata, supports `--pages` debug ranges
- `analyzer.py`: builds the node tree, preferring PDF outline over textual TOC over heading scan
- `renderer.py`: writes `index.md`, `content.md`, `node.json`, and root `AGENT.md` / `context.md`

## How To Run

Install deps:
```bash
uv sync --group dev
```

Full build:
```bash
uv run docspine build input.pdf --out out
```

Small-range debug build:
```bash
uv run docspine build input.pdf --out out --pages 1-20
```

Tests:
```bash
uv run --group dev pytest -q
```

## Important Behavior

- Structure priority is: PDF outline/bookmarks > textual table of contents > heading scan.
- Docling conversion runs in 5-page batches with stderr progress.
- Table structure recognition is enabled; analyzer must preserve Markdown table rows inside section content.
- Output trees are meant for agents to read through `index.md`, `content.md`, `node.json`, and `sections/`.

## Where To Look First

- Extraction or performance issue: `src/docspine/converter/docling_backend.py`
- Wrong tree structure: `src/docspine/analyzer.py`
- Wrong output files or metadata: `src/docspine/renderer.py`
- End-to-end regressions: `tests/test_pipeline_regression.py`
- Real behavior on current features: `tests/test_docling_backend.py`, `tests/test_analyzer.py`, `tests/test_renderer.py`

## Current Constraints

- Partial `--pages` runs are for debugging extraction, not guaranteed to produce a complete global tree.
- Real annual reports can still produce imperfect deep hierarchy or noisy subheadings.
- Root output directories intentionally contain `AGENT.md` and `context.md`; child section directories do not.
