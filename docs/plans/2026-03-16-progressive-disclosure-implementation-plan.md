# Progressive Disclosure Pipeline Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a CLI tool that converts a PDF into a progressively disclosed Markdown document tree with navigation files, full-content files, and machine-readable node metadata, while supporting multiple interchangeable extraction backends.

**Architecture:** Define a backend-neutral converter interface, implement Docling as the first backend, normalize the conversion result into an internal document model, segment that model into semantic nodes, then render a stable output contract made of `index.md`, `content.md`, and `node.json` per node. Keep the implementation modular so new extraction backends can be added without changing the downstream pipeline.

**Tech Stack:** Python 3.13, Docling as the first converter backend, `pathlib`, `dataclasses`, `json`, `pytest`, optional `typer` or standard library `argparse`

---

### Task 1: Establish package layout and CLI skeleton

**Files:**
- Create: `src/docling_progressive/__init__.py`
- Create: `src/docling_progressive/cli.py`
- Create: `src/docling_progressive/config.py`
- Modify: `pyproject.toml`
- Test: `tests/test_cli.py`

**Step 1: Write the failing test**

```python
from pathlib import Path

from docling_progressive.cli import build_parser


def test_build_parser_accepts_input_and_output_paths():
    parser = build_parser()
    args = parser.parse_args(["build", "sample.pdf", "--out", "out"])

    assert args.command == "build"
    assert args.input_path == Path("sample.pdf")
    assert args.output_dir == Path("out")
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_cli.py::test_build_parser_accepts_input_and_output_paths -v`
Expected: FAIL with `ModuleNotFoundError` or missing `build_parser`

**Step 3: Write minimal implementation**

```python
from argparse import ArgumentParser
from pathlib import Path


def build_parser() -> ArgumentParser:
    parser = ArgumentParser(prog="docling-progressive")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser("build")
    build_parser.add_argument("input_path", type=Path)
    build_parser.add_argument("--out", dest="output_dir", type=Path, required=True)
    return parser
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_cli.py::test_build_parser_accepts_input_and_output_paths -v`
Expected: PASS

**Step 5: Commit**

```bash
git add pyproject.toml src/docling_progressive/__init__.py src/docling_progressive/cli.py src/docling_progressive/config.py tests/test_cli.py
git commit -m "feat: add progressive disclosure cli skeleton"
```

### Task 2: Define the internal document and node models

**Files:**
- Create: `src/docling_progressive/models.py`
- Test: `tests/test_models.py`

**Step 1: Write the failing test**

```python
from docling_progressive.models import AssetRef, DocumentNode


def test_document_node_tracks_children_and_assets():
    asset = AssetRef(
        asset_id="figure-1",
        asset_type="image",
        path="assets/figure-1.png",
        caption="Revenue chart",
        source_pages=[3],
    )
    child = DocumentNode(
        node_id="child",
        title="Child",
        slug="child",
        level=1,
        summary="child summary",
    )
    root = DocumentNode(
        node_id="root",
        title="Root",
        slug="root",
        level=0,
        summary="root summary",
        children=[child],
        assets=[asset],
    )

    assert root.children[0].node_id == "child"
    assert root.assets[0].asset_type == "image"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_models.py::test_document_node_tracks_children_and_assets -v`
Expected: FAIL with missing module or missing dataclasses

**Step 3: Write minimal implementation**

```python
from dataclasses import dataclass, field


@dataclass(slots=True)
class AssetRef:
    asset_id: str
    asset_type: str
    path: str
    caption: str | None = None
    source_pages: list[int] = field(default_factory=list)


@dataclass(slots=True)
class DocumentNode:
    node_id: str
    title: str
    slug: str
    level: int
    summary: str
    children: list["DocumentNode"] = field(default_factory=list)
    assets: list[AssetRef] = field(default_factory=list)
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_models.py::test_document_node_tracks_children_and_assets -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/docling_progressive/models.py tests/test_models.py
git commit -m "feat: define progressive disclosure document models"
```

### Task 3: Define the converter interface and add the first backend

**Files:**
- Create: `src/docling_progressive/converter/__init__.py`
- Create: `src/docling_progressive/converter/base.py`
- Create: `src/docling_progressive/converter/models.py`
- Create: `src/docling_progressive/converter/docling_backend.py`
- Create: `src/docling_progressive/converter/factory.py`
- Test: `tests/test_converter.py`

**Step 1: Write the failing test**

```python
from pathlib import Path

from docling_progressive.converter.base import ConverterBackend
from docling_progressive.converter.models import ConversionResult


def test_conversion_result_keeps_markdown_and_asset_dir():
    result = ConversionResult(
        markdown="# Title",
        asset_dir=Path("assets"),
        metadata={"source": "sample.pdf"},
    )

    assert result.markdown == "# Title"
    assert result.asset_dir == Path("assets")
    assert result.metadata["source"] == "sample.pdf"


def test_converter_backend_protocol_exposes_convert_method():
    assert hasattr(ConverterBackend, "convert")
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_converter.py::test_conversion_result_keeps_markdown_and_asset_dir -v`
Expected: FAIL with missing converter package or missing `ConversionResult`

**Step 3: Write minimal implementation**

```python
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(slots=True)
class ConversionResult:
    markdown: str
    asset_dir: Path
    metadata: dict


class ConverterBackend(Protocol):
    def convert(self, input_path: Path, work_dir: Path) -> ConversionResult:
        ...
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_converter.py::test_conversion_result_keeps_markdown_and_asset_dir -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/docling_progressive/converter tests/test_converter.py
git commit -m "feat: add converter interface and docling backend scaffold"
```

### Task 4: Normalize extracted content into a document tree

**Files:**
- Create: `src/docling_progressive/analyzer.py`
- Test: `tests/test_analyzer.py`

**Step 1: Write the failing test**

```python
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
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_analyzer.py::test_build_outline_tree_groups_content_under_headings -v`
Expected: FAIL with missing function or wrong tree structure

**Step 3: Write minimal implementation**

```python
def build_outline_tree(markdown: str) -> DocumentNode:
    lines = markdown.splitlines()
    root_title = lines[0].lstrip("# ").strip()
    root = DocumentNode(
        node_id="root",
        title=root_title,
        slug="root",
        level=0,
        summary="",
    )
    for line in lines:
        if line.startswith("## "):
            title = line[3:].strip()
            root.children.append(
                DocumentNode(
                    node_id=title.lower().replace(" ", "-"),
                    title=title,
                    slug=title.lower().replace(" ", "-"),
                    level=1,
                    summary="",
                )
            )
    return root
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_analyzer.py::test_build_outline_tree_groups_content_under_headings -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/docling_progressive/analyzer.py tests/test_analyzer.py
git commit -m "feat: derive document outline from extracted markdown"
```

### Task 5: Implement node segmentation rules

**Files:**
- Create: `src/docling_progressive/segmenter.py`
- Test: `tests/test_segmenter.py`

**Step 1: Write the failing test**

```python
from docling_progressive.models import DocumentNode
from docling_progressive.segmenter import split_oversized_leaf


def test_split_oversized_leaf_creates_part_children_when_needed():
    leaf = DocumentNode(
        node_id="long-section",
        title="Long Section",
        slug="long-section",
        level=1,
        summary="summary",
        content="\n\n".join([f"Paragraph {i}" for i in range(12)]),
    )

    result = split_oversized_leaf(leaf, max_paragraphs=4)

    assert [child.slug for child in result.children] == [
        "long-section-part-1",
        "long-section-part-2",
        "long-section-part-3",
    ]
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_segmenter.py::test_split_oversized_leaf_creates_part_children_when_needed -v`
Expected: FAIL with missing `content` field or missing `split_oversized_leaf`

**Step 3: Write minimal implementation**

```python
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
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_segmenter.py::test_split_oversized_leaf_creates_part_children_when_needed -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/docling_progressive/segmenter.py tests/test_segmenter.py src/docling_progressive/models.py
git commit -m "feat: add oversized node segmentation"
```

### Task 6: Render the progressive disclosure directory structure

**Files:**
- Create: `src/docling_progressive/renderer.py`
- Test: `tests/test_renderer.py`

**Step 1: Write the failing test**

```python
import json

from docling_progressive.models import DocumentNode
from docling_progressive.renderer import render_node_tree


def test_render_node_tree_writes_index_content_and_metadata(tmp_path):
    root = DocumentNode(
        node_id="root",
        title="Annual Report",
        slug="annual-report",
        level=0,
        summary="Top summary",
        content="Root content",
    )

    render_node_tree(root, tmp_path)

    assert (tmp_path / "index.md").exists()
    assert (tmp_path / "content.md").exists()
    metadata = json.loads((tmp_path / "node.json").read_text())
    assert metadata["title"] == "Annual Report"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_renderer.py::test_render_node_tree_writes_index_content_and_metadata -v`
Expected: FAIL with missing module or missing renderer

**Step 3: Write minimal implementation**

```python
import json


def render_node_tree(node: DocumentNode, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "index.md").write_text(f"# {node.title}\n\n{node.summary}\n")
    (output_dir / "content.md").write_text(node.content)
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
        )
    )
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_renderer.py::test_render_node_tree_writes_index_content_and_metadata -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/docling_progressive/renderer.py tests/test_renderer.py
git commit -m "feat: render progressive disclosure node directories"
```

### Task 7: Add validation for output integrity

**Files:**
- Create: `src/docling_progressive/validator.py`
- Test: `tests/test_validator.py`

**Step 1: Write the failing test**

```python
from pathlib import Path

from docling_progressive.validator import validate_output_tree


def test_validate_output_tree_reports_missing_content_file(tmp_path):
    (tmp_path / "index.md").write_text("# Title\n")
    issues = validate_output_tree(tmp_path)

    assert issues == ["Missing content.md at root"]
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_validator.py::test_validate_output_tree_reports_missing_content_file -v`
Expected: FAIL with missing validator

**Step 3: Write minimal implementation**

```python
def validate_output_tree(root_dir: Path) -> list[str]:
    issues = []
    if not (root_dir / "content.md").exists():
        issues.append("Missing content.md at root")
    return issues
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_validator.py::test_validate_output_tree_reports_missing_content_file -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/docling_progressive/validator.py tests/test_validator.py
git commit -m "feat: validate progressive disclosure output trees"
```

### Task 8: Wire the end-to-end build command

**Files:**
- Modify: `src/docling_progressive/cli.py`
- Create: `src/docling_progressive/pipeline.py`
- Test: `tests/test_pipeline.py`

**Step 1: Write the failing test**

```python
from pathlib import Path

from docling_progressive.pipeline import build_progressive_package


def test_build_progressive_package_creates_root_files(tmp_path):
    input_pdf = tmp_path / "sample.pdf"
    input_pdf.write_bytes(b"%PDF-1.4")
    output_dir = tmp_path / "out"

    build_progressive_package(input_pdf, output_dir)

    assert (output_dir / "index.md").exists()
    assert (output_dir / "content.md").exists()
    assert (output_dir / "node.json").exists()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_pipeline.py::test_build_progressive_package_creates_root_files -v`
Expected: FAIL because the pipeline function does not exist

**Step 3: Write minimal implementation**

```python
def build_progressive_package(input_pdf: Path, output_dir: Path) -> None:
    conversion = convert_pdf(input_pdf)
    root = build_outline_tree(conversion.markdown)
    root = segment_tree(root)
    render_node_tree(root, output_dir)
    issues = validate_output_tree(output_dir)
    if issues:
        raise ValueError("\n".join(issues))
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_pipeline.py::test_build_progressive_package_creates_root_files -v`
Expected: PASS with a test double or fixture-backed converter backend

**Step 5: Commit**

```bash
git add src/docling_progressive/cli.py src/docling_progressive/pipeline.py tests/test_pipeline.py
git commit -m "feat: connect progressive disclosure pipeline end to end"
```

### Task 9: Add regression fixtures and documentation

**Files:**
- Create: `tests/fixtures/sample_outline.md`
- Create: `tests/fixtures/sample_expected_tree/`
- Modify: `README.md`
- Test: `tests/test_pipeline_regression.py`

**Step 1: Write the failing test**

```python
def test_pipeline_regression_matches_expected_tree(snapshot_tree):
    actual_tree = snapshot_tree("sample_outline")
    expected_tree = snapshot_tree("sample_expected_tree")

    assert actual_tree == expected_tree
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_pipeline_regression.py::test_pipeline_regression_matches_expected_tree -v`
Expected: FAIL because fixture files and helper do not exist yet

**Step 3: Write minimal implementation**

```python
# Add a fixture-backed regression helper that renders a small outline,
# walks the output tree, and compares relative file names and contents.
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_pipeline_regression.py::test_pipeline_regression_matches_expected_tree -v`
Expected: PASS

**Step 5: Commit**

```bash
git add README.md tests/fixtures tests/test_pipeline_regression.py
git commit -m "test: add regression coverage for progressive disclosure output"
```

## Notes for Execution

- Use `superpowers:test-driven-development` before implementing each feature or bugfix task.
- Keep the first version focused on one PDF per run and file-based output only.
- Prefer parser-backed fixtures and test doubles over calling a real backend in every unit test.
- Keep analyzer input backend-neutral so future converter additions do not affect downstream tests.
- Add one or two real sample documents only after the deterministic test harness is in place.
- Defer retrieval, vectorization, UI, and MCP integration until the core output contract is stable.
