from pathlib import Path
from typing import Protocol

from docspine.converter.models import ConversionResult, StreamingConversionSession


class ConverterBackend(Protocol):
    def convert(
        self,
        input_path: Path,
        work_dir: Path,
        page_range: tuple[int, int] | None = None,
    ) -> ConversionResult:
        """Convert an input file into backend-neutral markdown output."""

    def stream_convert(
        self,
        input_path: Path,
        work_dir: Path,
        page_range: tuple[int, int] | None = None,
        batch_size: int = 5,
    ) -> StreamingConversionSession:
        """Convert an input file into streaming backend-neutral markdown output."""
