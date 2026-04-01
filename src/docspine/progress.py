from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal, TypeAlias


ProgressStage = Literal["preparing", "processing", "finalizing", "complete"]


@dataclass(frozen=True, slots=True)
class BuildProgress:
    stage: ProgressStage
    processed_pages: int | None = None
    total_pages: int | None = None


ProgressCallback: TypeAlias = Callable[[BuildProgress], None]
