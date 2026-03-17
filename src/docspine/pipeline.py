from pathlib import Path

from docspine.analyzer import build_outline_tree
from docspine.converter.base import ConverterBackend
from docspine.converter.factory import create_backend
from docspine.renderer import render_node_tree
from docspine.segmenter import segment_tree
from docspine.validator import validate_output_tree


def build_progressive_package(
    input_pdf: Path,
    output_dir: Path,
    backend: ConverterBackend | None = None,
    page_range: tuple[int, int] | None = None,
) -> None:
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
