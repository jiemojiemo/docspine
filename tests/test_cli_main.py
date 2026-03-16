from pathlib import Path

from docling_progressive import cli


def test_main_runs_build_pipeline(monkeypatch):
    captured: dict[str, Path] = {}

    def fake_build(input_path: Path, output_dir: Path) -> None:
        captured["input_path"] = input_path
        captured["output_dir"] = output_dir

    monkeypatch.setattr(cli, "build_progressive_package", fake_build)
    monkeypatch.setattr(
        "sys.argv",
        ["docling-progressive", "build", "sample.pdf", "--out", "out"],
    )

    assert cli.main() == 0
    assert captured == {
        "input_path": Path("sample.pdf"),
        "output_dir": Path("out"),
    }
