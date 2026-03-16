from pathlib import Path

from docling_progressive import cli


def test_main_runs_build_pipeline(monkeypatch):
    captured: dict[str, object] = {}

    def fake_build(
        input_path: Path,
        output_dir: Path,
        page_range: tuple[int, int] | None = None,
    ) -> None:
        captured["input_path"] = input_path
        captured["output_dir"] = output_dir
        captured["page_range"] = page_range

    monkeypatch.setattr(cli, "build_progressive_package", fake_build)
    monkeypatch.setattr(
        "sys.argv",
        [
            "docling-progressive",
            "build",
            "sample.pdf",
            "--out",
            "out",
            "--pages",
            "1-20",
        ],
    )

    assert cli.main() == 0
    assert captured == {
        "input_path": Path("sample.pdf"),
        "output_dir": Path("out"),
        "page_range": (1, 20),
    }
