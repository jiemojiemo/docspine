from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class BuildConfig:
    input_path: Path
    output_dir: Path
    backend: str = "docling"
