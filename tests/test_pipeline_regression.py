from pathlib import Path

from docling_progressive.converter.models import ConversionResult
from docling_progressive.pipeline import build_progressive_package


class FixtureBackend:
    def __init__(self, markdown: str):
        self._markdown = markdown

    def convert(self, input_path: Path, work_dir: Path) -> ConversionResult:
        asset_dir = work_dir / "assets"
        asset_dir.mkdir(parents=True, exist_ok=True)
        return ConversionResult(
            markdown=self._markdown,
            asset_dir=asset_dir,
            metadata={"source": input_path.name},
        )


def snapshot_tree(path: Path) -> dict[str, str]:
    return {
        str(file.relative_to(path)): file.read_text(encoding="utf-8").rstrip("\n")
        for file in sorted(path.rglob("*"))
        if file.is_file()
    }


def test_pipeline_regression_matches_expected_tree(tmp_path):
    fixture_root = Path(__file__).parent / "fixtures"
    input_pdf = tmp_path / "sample.pdf"
    input_pdf.write_bytes(b"%PDF-1.4")
    actual_tree_root = tmp_path / "actual"

    build_progressive_package(
        input_pdf,
        actual_tree_root,
        backend=FixtureBackend((fixture_root / "sample_outline.md").read_text(encoding="utf-8")),
    )

    actual_tree = snapshot_tree(actual_tree_root)
    expected_tree = snapshot_tree(fixture_root / "sample_expected_tree")

    assert actual_tree == expected_tree
