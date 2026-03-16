from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class ConversionResult:
    markdown: str
    asset_dir: Path
    metadata: dict[str, Any] = field(default_factory=dict)
