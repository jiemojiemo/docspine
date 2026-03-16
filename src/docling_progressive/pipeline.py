from pathlib import Path

from docling_progressive.analyzer import build_outline_tree
from docling_progressive.converter.base import ConverterBackend
from docling_progressive.converter.factory import create_backend
from docling_progressive.renderer import render_node_tree
from docling_progressive.segmenter import segment_tree
from docling_progressive.validator import validate_output_tree


def build_progressive_package(
    input_pdf: Path,
    output_dir: Path,
    backend: ConverterBackend | None = None,
) -> None:
    active_backend = backend or create_backend("docling")
    conversion = active_backend.convert(input_pdf, output_dir)
    root = build_outline_tree(conversion.markdown, metadata=conversion.metadata)
    root = segment_tree(root)
    render_node_tree(root, output_dir)
    issues = validate_output_tree(output_dir)
    if issues:
        raise ValueError("\n".join(issues))
