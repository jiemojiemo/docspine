import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

from docling_progressive.converter.docling_backend import DoclingBackend


def test_docling_backend_converts_to_backend_neutral_result(monkeypatch, tmp_path):
    class FakeDocumentConverter:
        def convert(self, path: str):
            assert path == str(tmp_path / "sample.pdf")
            return SimpleNamespace(
                document=SimpleNamespace(export_to_markdown=lambda: "# Title")
            )

    fake_module = ModuleType("docling.document_converter")
    fake_module.DocumentConverter = FakeDocumentConverter
    monkeypatch.setitem(sys.modules, "docling.document_converter", fake_module)

    backend = DoclingBackend()
    result = backend.convert(tmp_path / "sample.pdf", tmp_path / "work")

    assert result.markdown == "# Title"
    assert result.asset_dir == tmp_path / "work" / "assets"
    assert result.metadata["backend"] == "docling"
