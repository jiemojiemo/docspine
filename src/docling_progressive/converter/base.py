from pathlib import Path
from typing import Protocol

from docling_progressive.converter.models import ConversionResult


class ConverterBackend(Protocol):
    def convert(self, input_path: Path, work_dir: Path) -> ConversionResult:
        """Convert an input file into backend-neutral markdown output."""
