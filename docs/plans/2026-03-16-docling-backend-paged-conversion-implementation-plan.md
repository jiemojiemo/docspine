# Docling Backend Paged Conversion Implementation Plan

1. Add a failing test that expects page-by-page conversion and ordered markdown concatenation.
2. Add a failing test that expects progress output on `stderr`.
3. Add a failing test that covers logger suppression and total-page discovery.
4. Implement minimal `DoclingBackend` changes to satisfy the tests.
5. Run targeted tests, then the full test suite with coverage.
