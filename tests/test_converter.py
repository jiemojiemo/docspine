from pathlib import Path

from docspine.converter.base import ConverterBackend
from docspine.converter.models import ConversionChunk, ConversionResult, StreamingConversionSession
from docspine.progress import BuildProgress


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


def test_converter_backend_protocol_exposes_stream_convert_method():
    assert hasattr(ConverterBackend, "stream_convert")


def test_conversion_chunk_keeps_page_range_and_markdown():
    chunk = ConversionChunk(
        page_start=1,
        page_end=5,
        markdown="# Title",
        metadata={"batch": 1},
    )

    assert chunk.page_start == 1
    assert chunk.page_end == 5
    assert chunk.markdown == "# Title"
    assert chunk.metadata["batch"] == 1


def test_streaming_conversion_session_keeps_metadata_asset_dir_and_chunks():
    chunk = ConversionChunk(page_start=1, page_end=5, markdown="# Title")
    session = StreamingConversionSession(
        asset_dir=Path("assets"),
        metadata={"source": "sample.pdf"},
        chunks=iter([chunk]),
    )

    assert session.asset_dir == Path("assets")
    assert session.metadata["source"] == "sample.pdf"
    assert list(session.chunks) == [chunk]


def test_build_progress_keeps_stage_and_page_counts():
    progress = BuildProgress(stage="processing", processed_pages=20, total_pages=100)

    assert progress.stage == "processing"
    assert progress.processed_pages == 20
    assert progress.total_pages == 100
