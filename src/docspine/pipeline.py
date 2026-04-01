from pathlib import Path
import inspect

from docspine.analyzer import build_outline_tree
from docspine.converter.models import ConversionChunk, StreamingConversionSession
from docspine.converter.base import ConverterBackend
from docspine.converter.factory import create_backend
from docspine.progress import BuildProgress, ProgressCallback
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
    progress_callback: ProgressCallback | None = None,
) -> None:
    if stream:
        build_streaming_package(
            input_pdf,
            output_dir,
            backend=backend,
            page_range=page_range,
            stream_batch_size=stream_batch_size,
            progress_callback=progress_callback,
        )
        return

    _emit_progress(progress_callback, stage="preparing")
    active_backend = backend or create_backend("docling")
    conversion = _convert_with_progress(
        active_backend,
        input_pdf,
        output_dir,
        page_range=page_range,
        progress_callback=progress_callback,
    )
    _emit_progress(progress_callback, stage="finalizing")
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
    _emit_progress(progress_callback, stage="complete")


def _emit_progress(
    progress_callback: ProgressCallback | None,
    *,
    stage: str,
    processed_pages: int | None = None,
    total_pages: int | None = None,
) -> None:
    if progress_callback is None:
        return
    progress_callback(
        BuildProgress(
            stage=stage,
            processed_pages=processed_pages,
            total_pages=total_pages,
        )
    )


def _convert_with_progress(
    backend: ConverterBackend,
    input_pdf: Path,
    output_dir: Path,
    *,
    page_range: tuple[int, int] | None,
    progress_callback: ProgressCallback | None,
):
    convert_signature = inspect.signature(backend.convert)
    if "progress_callback" in convert_signature.parameters:
        return backend.convert(
            input_pdf,
            output_dir,
            page_range=page_range,
            progress_callback=progress_callback,
        )
    return backend.convert(input_pdf, output_dir, page_range=page_range)
