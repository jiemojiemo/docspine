# DocSpine Rename Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Rename the project from `docling-progressive` / `docling_progressive` to `DocSpine` / `docspine` without changing runtime behavior.

**Architecture:** Keep the existing pipeline intact and perform a pure naming migration across packaging metadata, import paths, CLI entry points, and user-facing docs. Verify the rename by running the existing test suite against the new package/module names.

**Tech Stack:** Python 3.13, setuptools, uv, pytest

---

### Task 1: Update package and entrypoint naming

**Files:**
- Modify: `pyproject.toml`
- Modify: `README.md`
- Modify: `AGENT.md`
- Modify: `src/docling_progressive/__init__.py`

**Step 1: Update packaging metadata**

Change the distribution name to `docspine`, rename the CLI script to `docspine`, and refresh user-facing descriptions to use `DocSpine`.

**Step 2: Update help text and docs**

Replace old CLI examples and project-name references in repo docs so the public interface matches the new name.

**Step 3: Keep behavior unchanged**

Do not alter pipeline logic, options, or output format during the rename.

### Task 2: Rename the Python package and imports

**Files:**
- Move: `src/docling_progressive/` -> `src/docspine/`
- Modify: `src/docspine/**/*.py`
- Modify: `tests/*.py`

**Step 1: Rename the package directory**

Move the package from `src/docling_progressive` to `src/docspine`.

**Step 2: Update internal imports**

Replace `docling_progressive` imports with `docspine` throughout the source tree.

**Step 3: Update tests**

Replace test imports and CLI expectations so the suite targets `docspine`.

### Task 3: Refresh generated metadata and verify

**Files:**
- Refresh: `uv.lock`

**Step 1: Re-lock if needed**

Regenerate lockfile metadata if the root package name remains embedded there after the rename.

**Step 2: Run verification**

Run the full test suite and confirm the renamed CLI/module surface passes unchanged behavior checks.
