from pathlib import Path

import pytest

from docling_progressive.converter.models import ConversionResult
from docling_progressive import pipeline
from docling_progressive.pipeline import build_progressive_package


class StubBackend:
    def convert(self, input_path: Path, work_dir: Path) -> ConversionResult:
        asset_dir = work_dir / "assets"
        asset_dir.mkdir(parents=True, exist_ok=True)
        return ConversionResult(
            markdown="# Sample\n\nIntro\n\n## Section\n\nBody",
            asset_dir=asset_dir,
            metadata={"source": input_path.name},
        )


def test_build_progressive_package_creates_root_files(tmp_path):
    input_pdf = tmp_path / "sample.pdf"
    input_pdf.write_bytes(b"%PDF-1.4")
    output_dir = tmp_path / "out"

    build_progressive_package(input_pdf, output_dir, backend=StubBackend())

    assert (output_dir / "index.md").exists()
    assert (output_dir / "content.md").exists()
    assert (output_dir / "node.json").exists()


def test_build_progressive_package_uses_default_backend_when_none_provided(monkeypatch, tmp_path):
    class DefaultBackend:
        def convert(self, input_path: Path, work_dir: Path) -> ConversionResult:
            return ConversionResult(
                markdown="# Sample",
                asset_dir=work_dir / "assets",
                metadata={},
            )

    monkeypatch.setattr(pipeline, "create_backend", lambda name: DefaultBackend())

    input_pdf = tmp_path / "sample.pdf"
    input_pdf.write_bytes(b"%PDF-1.4")

    build_progressive_package(input_pdf, tmp_path / "out")

    assert (tmp_path / "out" / "index.md").exists()


def test_build_progressive_package_raises_when_validation_fails(monkeypatch, tmp_path):
    monkeypatch.setattr(pipeline, "validate_output_tree", lambda output_dir: ["broken tree"])

    input_pdf = tmp_path / "sample.pdf"
    input_pdf.write_bytes(b"%PDF-1.4")

    with pytest.raises(ValueError, match="broken tree"):
        build_progressive_package(input_pdf, tmp_path / "out", backend=StubBackend())
