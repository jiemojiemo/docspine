from pathlib import Path

from docling_progressive.converter.models import ConversionResult


class DoclingBackend:
    def convert(self, input_path: Path, work_dir: Path) -> ConversionResult:
        from docling.document_converter import DocumentConverter

        converter = DocumentConverter()
        result = converter.convert(str(input_path))
        asset_dir = work_dir / "assets"
        asset_dir.mkdir(parents=True, exist_ok=True)
        return ConversionResult(
            markdown=result.document.export_to_markdown(),
            asset_dir=asset_dir,
            metadata={"backend": "docling", "source": str(input_path)},
        )
