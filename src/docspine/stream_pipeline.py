from pathlib import Path

import shutil

from docspine.analyzer import (
    assign_chunk_to_nodes,
    build_stream_skeleton,
    finalize_stream_tree,
    set_stream_statuses,
)
from docspine.converter.base import ConverterBackend
from docspine.converter.models import ConversionChunk, ConversionResult, StreamingConversionSession
from docspine.converter.factory import create_backend
from docspine.progress import BuildProgress, ProgressCallback
from docspine.renderer import render_node_tree
from docspine.segmenter import segment_tree
from docspine.validator import validate_output_tree


def build_streaming_package(
    input_pdf: Path,
    output_dir: Path,
    backend: ConverterBackend | None = None,
    page_range: tuple[int, int] | None = None,
    stream_batch_size: int = 5,
    progress_callback: ProgressCallback | None = None,
) -> None:
    _emit_progress(progress_callback, stage="preparing")
    active_backend = backend or create_backend("docling")
    session = _start_streaming_session(
        active_backend,
        input_pdf,
        output_dir,
        page_range=page_range,
        stream_batch_size=stream_batch_size,
    )

    metadata = session.metadata
    root = build_stream_skeleton(metadata)
    render_node_tree(root, output_dir, source_path=input_pdf, metadata=metadata)

    all_chunks: list[ConversionChunk] = []
    processed_pages = 0
    total_pages = _resolve_total_pages(metadata)
    for chunk in session.chunks:
        all_chunks.append(chunk)
        processed_pages += chunk.page_end - chunk.page_start + 1
        _emit_progress(
            progress_callback,
            stage="processing",
            processed_pages=processed_pages,
            total_pages=total_pages,
        )
        assign_chunk_to_nodes(root, chunk)
        render_node_tree(root, output_dir, source_path=input_pdf, metadata=metadata)

    _emit_progress(progress_callback, stage="finalizing")
    final_root = finalize_stream_tree(root, all_chunks, metadata)
    final_root = segment_tree(final_root)
    set_stream_statuses(final_root, structure_status="ready", content_status="complete")
    _reset_output_tree(output_dir)
    render_node_tree(final_root, output_dir, source_path=input_pdf, metadata=metadata)

    issues = validate_output_tree(output_dir)
    if issues:
        raise ValueError("\n".join(issues))
    _emit_progress(progress_callback, stage="complete")


def _start_streaming_session(
    backend: ConverterBackend,
    input_pdf: Path,
    output_dir: Path,
    *,
    page_range: tuple[int, int] | None,
    stream_batch_size: int,
) -> StreamingConversionSession:
    if hasattr(backend, "stream_convert"):
        return backend.stream_convert(
            input_pdf,
            output_dir,
            page_range=page_range,
            batch_size=stream_batch_size,
        )

    conversion = backend.convert(input_pdf, output_dir, page_range=page_range)
    return StreamingConversionSession(
        asset_dir=conversion.asset_dir,
        metadata=conversion.metadata,
        chunks=iter(
            [
                ConversionChunk(
                    page_start=page_range[0] if page_range else 1,
                    page_end=page_range[1] if page_range else conversion.metadata.get("total_pages", 1),
                    markdown=conversion.markdown,
                    metadata={},
                )
            ]
        ),
    )


def _reset_output_tree(output_dir: Path) -> None:
    if output_dir.exists():
        shutil.rmtree(output_dir)


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


def _resolve_total_pages(metadata: dict[str, object]) -> int | None:
    processed_pages = metadata.get("processed_pages")
    if processed_pages is not None:
        return int(processed_pages)

    page_range = metadata.get("page_range")
    if isinstance(page_range, tuple) and len(page_range) == 2:
        return int(page_range[1]) - int(page_range[0]) + 1

    total_pages = metadata.get("total_pages")
    if total_pages is None:
        return None
    return int(total_pages)
