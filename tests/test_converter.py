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
