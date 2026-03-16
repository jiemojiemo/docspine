# Analyzer Real PDF Normalization Implementation Plan

1. Add failing analyzer tests for root title extraction from non-Markdown lines.
2. Add failing analyzer tests for repeated Chinese heading slug deduplication.
3. Add failing analyzer tests for numbered Chinese section parsing.
4. Implement minimal analyzer normalization and Unicode-aware slug generation.
5. Run analyzer tests, then full test suite with coverage.
