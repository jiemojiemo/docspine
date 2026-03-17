from pathlib import Path
from typing import Protocol

from docspine.converter.models import ConversionResult


class ConverterBackend(Protocol):
    def convert(
        self,
        input_path: Path,
        work_dir: Path,
        page_range: tuple[int, int] | None = None,
    ) -> ConversionResult:
        """Convert an input file into backend-neutral markdown output."""
