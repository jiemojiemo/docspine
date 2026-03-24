from pathlib import Path

from docspine.analyzer import build_outline_tree
from docspine.converter.models import ConversionChunk, StreamingConversionSession
from docspine.converter.base import ConverterBackend
from docspine.converter.factory import create_backend
from docspine.renderer import render_node_tree
from docspine.segmenter import segment_tree
from docspine.stream_pipeline import build_streaming_package
from docspine.validator import validate_output_tree


def build_progressive_package(
    input_pdf: Path,
    output_dir: Path,
    backend: ConverterBackend | None = None,
    page_range: tuple[int, int] | None = None,
    stream: bool = False,
    stream_batch_size: int = 5,
) -> None:
    if stream:
        build_streaming_package(
            input_pdf,
            output_dir,
            backend=backend,
            page_range=page_range,
            stream_batch_size=stream_batch_size,
        )
        return

    active_backend = backend or create_backend("docling")
    conversion = active_backend.convert(input_pdf, output_dir, page_range=page_range)
    root = build_outline_tree(conversion.markdown, metadata=conversion.metadata)
    root = segment_tree(root)
    render_node_tree(
        root,
        output_dir,
        source_path=input_pdf,
        metadata=conversion.metadata,
    )
    issues = validate_output_tree(output_dir)
    if issues:
        raise ValueError("\n".join(issues))
