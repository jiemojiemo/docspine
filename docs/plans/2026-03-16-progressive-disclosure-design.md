# Progressive Disclosure Design

## Goal

Build a document packaging pipeline that converts long PDFs such as annual reports into a tree of progressively disclosed Markdown nodes that AI agents can browse layer by layer instead of reading the full document at once.

## Problem Statement

Open-source tools such as Docling already cover a large part of the `PDF -> Markdown` problem. The missing layer is a stable architecture that reorganizes extracted content into a navigation-first structure for agent consumption. The output must work for both:

- simple agents that can only open Markdown files and follow links
- smarter runtimes that want machine-readable metadata for routing, filtering, and selective expansion

## Chosen Approach

Use a dual-track output format:

- human and agent readable Markdown navigation via `index.md`
- machine-readable metadata via `node.json`

Each semantic section becomes a node directory containing:

- `index.md`: summary, navigation, and next-step guidance
- `content.md`: full content for the node
- `node.json`: structured metadata

The entire document is represented as a tree rooted at a top-level node.

## Core Principles

### 1. Section tree before chunking

The primary structure should come from the source document's heading hierarchy and layout cues. Fixed-size token chunking is only a fallback when semantic sections are too large.

### 2. Progressive disclosure is a navigation concern

`index.md` should help an agent decide what to read next. It should not duplicate the full section body.

### 3. Metadata is a first-class output

The system must expose parent-child relationships, page ranges, asset references, and rough token estimates in `node.json` so downstream tooling can make reading decisions programmatically.

### 4. Assets belong to nodes

Images, tables, and other extracted assets should be attached to the node they conceptually belong to, not only left embedded in the raw Markdown dump.

### 5. Parser output is not the final structure

The extraction backend is not the final source of truth. A normalization and segmentation layer must refine the structure before output is rendered.

### 6. Converter backends must be swappable

The conversion stage should expose one stable interface with multiple backend implementations. Docling can be the first backend, but the rest of the pipeline should only depend on a backend-neutral `ConversionResult`.

## Output Contract

Recommended first-version layout:

```text
out/<doc-slug>/
  index.md
  content.md
  node.json
  assets/
  sections/
    01-<slug>/
      index.md
      content.md
      node.json
      sections/
```

### `index.md`

Purpose:

- summarize what the current node covers
- list child nodes
- tell the agent what to open next

Suggested shape:

```md
# Business Overview

This node covers the company's business scope, market position, and major operating segments.

## Subsections
- [Industry Landscape](sections/01-industry-landscape/index.md): market size, competition, and trends
- [Core Products](sections/02-core-products/index.md): key product lines and revenue contribution

## Read Next
- Open [content.md](content.md) for the full text of this section.
- If you only need market context, start with [Industry Landscape](sections/01-industry-landscape/index.md).
```

### `content.md`

Purpose:

- hold the full text for the current node
- keep image, table, caption, and page reference material accessible

### `node.json`

Minimum useful schema:

```json
{
  "id": "business-overview",
  "title": "Business Overview",
  "slug": "business-overview",
  "level": 1,
  "parent_id": "root",
  "children": [
    "industry-landscape",
    "core-products"
  ],
  "summary": "This section introduces the company's business scope, market position, and core offerings.",
  "source_pages": [12, 13, 14, 15],
  "token_estimate": 1840,
  "has_content": true,
  "has_children": true,
  "content_path": "content.md",
  "index_path": "index.md",
  "child_paths": [
    "sections/01-industry-landscape/index.md",
    "sections/02-core-products/index.md"
  ],
  "assets": [
    "assets/figure-01-market-share.png"
  ]
}
```

## Internal Pipeline

The first-version implementation should follow five stages:

1. `convert`
   - run the selected extraction backend on the source PDF
   - collect raw Markdown and extracted assets in a backend-neutral format
2. `analyze`
   - derive headings, page ranges, tables, images, and layout hints
   - normalize into an internal document model
3. `segment`
   - build a semantic node tree
   - split oversized sections only when needed
4. `render`
   - write node directories and files
5. `validate`
   - detect empty nodes, broken links, missing assets, and oversize sections

## Node Segmentation Rules

Segmentation should be driven by these priorities:

1. prefer source section hierarchy
2. split by child headings when a node is too large
3. fall back to grouped paragraph chunks only if no meaningful child headings exist

Suggested defaults for version one:

- target node size: about `800-2500` tokens
- use heading hierarchy as the main split rule
- if a leaf section exceeds the target size, split into logical parts

## Assets and Tables

First-version behavior:

- persist images as files under the document output
- keep tables in Markdown when possible
- allow image fallback for complex tables
- record asset references in `node.json`
- keep page information at both node level and asset level when available

## First-Version Scope

Include:

- one PDF input per run
- one backend implementation for PDF conversion, with Docling as the first supported backend
- semantic node tree generation
- `index.md`, `content.md`, `node.json` output for each node
- asset persistence and node association
- validation checks

Exclude for now:

- vector search
- multi-document knowledge base support
- MCP server
- web UI
- advanced chart understanding
- incremental rebuilds

## Risks

The biggest risks are structural rather than algorithmic:

- inconsistent heading detection in financial PDFs
- multi-column layouts
- cross-page tables
- asset-to-section association ambiguity
- OCR-heavy scans with weak heading cues

The architecture should therefore reserve a dedicated normalization and repair layer rather than assuming backend output is final.

## Converter Boundary

The `converter` layer should be an adapter boundary, not a Docling-specific wrapper.

Recommended shape:

- `converter/base.py`
  - define a stable converter protocol such as `convert(input_path, work_dir) -> ConversionResult`
- `converter/models.py`
  - define backend-neutral conversion models
- `converter/docling.py`
  - first backend implementation
- `converter/factory.py`
  - select a backend from configuration or CLI input

The rest of the pipeline should depend only on the adapter contract:

- `converter` extracts
- `analyzer` normalizes
- `segmenter` restructures
- `renderer` writes outputs
- `validator` checks output integrity

This keeps future backend additions like Marker or other PDF extraction libraries isolated to the adapter layer.

## Success Criteria

The first version is successful if:

- a financial PDF can be converted into a browsable node tree
- the top-level `index.md` clearly exposes major sections
- each node has stable Markdown and JSON outputs
- an AI agent can navigate incrementally without reading the entire document up front
- images and tables remain accessible from the relevant section
