from pathlib import Path


def validate_output_tree(root_dir: Path) -> list[str]:
    issues: list[str] = []
    _validate_node_dir(root_dir, issues, is_root=True)
    return issues


def _validate_node_dir(node_dir: Path, issues: list[str], *, is_root: bool) -> None:
    location = "root" if is_root else str(node_dir)
    if not (node_dir / "index.md").exists():
        issues.append(f"Missing index.md at {location}")
    if not (node_dir / "content.md").exists():
        issues.append(f"Missing content.md at {location}")
    if not is_root and not (node_dir / "node.json").exists():
        issues.append(f"Missing node.json at {location}")

    sections_dir = node_dir / "sections"
    if not sections_dir.exists():
        return

    for child_dir in sorted(path for path in sections_dir.iterdir() if path.is_dir()):
        _validate_node_dir(child_dir, issues, is_root=False)
