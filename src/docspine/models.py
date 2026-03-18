from dataclasses import dataclass, field


@dataclass(slots=True)
class AssetRef:
    asset_id: str
    asset_type: str
    path: str
    caption: str | None = None
    source_pages: list[int] = field(default_factory=list)


@dataclass(slots=True)
class DocumentNode:
    node_id: str
    title: str
    slug: str
    level: int
    summary: str
    content: str = ""
    children: list["DocumentNode"] = field(default_factory=list)
    assets: list[AssetRef] = field(default_factory=list)
    page_start: int | None = None
