# Analyzer Real PDF Normalization Design

## Goal

Improve outline extraction for real Docling output so Chinese research PDFs produce a stable root title and unique, meaningful child slugs.

## Problems Seen In Real Output

- the root title falls back to `Document`
- Chinese headings collapse to `section`
- duplicate or numeric-only headings produce unstable node ids
- front-matter lines such as analyst rosters and cover metadata pollute the section tree

## Chosen Approach

1. Detect the root title from the first meaningful non-image, non-date, non-analyst line when no `#` heading is present.
2. Treat common Docling title-like lines as top-level section candidates:
   - Markdown headings
   - numbered section headings such as `1 、`
   - subsection headings such as `2.1 、`
   - figure/table headings such as `图 1 ：` and `表 1 ：`
3. Generate slugs with Unicode-aware normalization so Chinese text remains meaningful.
4. Deduplicate child slugs deterministically by suffixing repeated slugs.
5. Skip early front-matter headings before the first substantive report title/section.

## Testing

- root title detection from real-style cover text
- unique slug generation for repeated Chinese headings
- section detection for numbered Chinese headings
- regression test using the real PDF-derived markdown pattern
