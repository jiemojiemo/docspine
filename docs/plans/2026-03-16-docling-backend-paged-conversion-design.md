# Docling Backend Paged Conversion Design

## Goal

Improve `DoclingBackend` for long PDFs by converting one page at a time, surfacing conversion progress, and suppressing noisy Docling logs by default.

## Chosen Approach

Keep the existing `ConversionResult` contract and change only the backend internals:

- initialize a Docling converter with conservative `PdfPipelineOptions`
- read total page count up front with `pypdfium2.PdfDocument`
- convert one page at a time with `page_range=(page_no, page_no)`
- concatenate page markdown in order
- emit progress messages to `stderr`
- suppress Docling logger output during conversion

## Why This Approach

This preserves the current pipeline interface while improving behavior for long-running conversions. Callers continue to depend on a backend-neutral `convert(input_path, work_dir)` API.

## Testing

- verify the backend converts page by page and concatenates markdown in order
- verify progress messages are emitted
- verify Docling logging is suppressed during conversion
