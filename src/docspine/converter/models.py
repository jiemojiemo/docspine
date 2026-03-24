from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator


@dataclass(slots=True)
class ConversionResult:
    markdown: str
    asset_dir: Path
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ConversionChunk:
    page_start: int
    page_end: int
    markdown: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class StreamingConversionSession:
    asset_dir: Path
    metadata: dict[str, Any] = field(default_factory=dict)
    chunks: Iterator[ConversionChunk] = field(default_factory=iter)
