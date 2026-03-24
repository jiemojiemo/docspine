import logging
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

from docspine.converter.docling_backend import DoclingBackend, _fix_scientific_notation
from docspine.converter.models import ConversionChunk, StreamingConversionSession


def test_docling_backend_converts_pdf_page_by_page(monkeypatch, tmp_path, capsys):
    calls: list[tuple[str, tuple[int, int]]] = []

    class FakeDocumentConverter:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        def convert(self, path: str, page_range: tuple[int, int]):
            calls.append((path, page_range))
            start_page, end_page = page_range
            return SimpleNamespace(
                document=SimpleNamespace(
                    export_to_markdown=lambda: f"# Page {start_page}-{end_page}"
                )
            )

    class FakePdfDocument:
        def __init__(self, path: str):
            assert path == str(tmp_path / "sample.pdf")

        def __len__(self):
            return 3

        def close(self):
            return None

    _install_docling_stubs(monkeypatch, FakeDocumentConverter, FakePdfDocument)

    backend = DoclingBackend()
    result = backend.convert(tmp_path / "sample.pdf", tmp_path / "work")

    assert calls == [
        (str(tmp_path / "sample.pdf"), (1, 3)),
    ]
    assert result.markdown == "# Page 1-3"
    assert result.asset_dir == tmp_path / "work" / "assets"
    assert result.metadata["backend"] == "docling"

    stderr = capsys.readouterr().err
    assert "converting pages 1-3/3" in stderr
    assert "finished pages 1-3/3" in stderr


def test_docling_backend_suppresses_docling_logger(monkeypatch, tmp_path):
    docling_logger = logging.getLogger("docling")
    original_level = docling_logger.level

    class FakeDocumentConverter:
        def __init__(self, **kwargs):
            pass

        def convert(self, path: str, page_range: tuple[int, int]):
            return SimpleNamespace(
                document=SimpleNamespace(export_to_markdown=lambda: "content")
            )

    class FakePdfDocument:
        def __init__(self, path: str):
            pass

        def __len__(self):
            return 20

        def close(self):
            return None

    _install_docling_stubs(monkeypatch, FakeDocumentConverter, FakePdfDocument)

    backend = DoclingBackend()
    backend.convert(tmp_path / "sample.pdf", tmp_path / "work")

    assert docling_logger.level == original_level


def test_docling_backend_uses_lightweight_pipeline_options(monkeypatch, tmp_path):
    captured_options: list[dict[str, object]] = []

    class FakeDocumentConverter:
        def __init__(self, **kwargs):
            option = kwargs["format_options"]["pdf"]
            captured_options.append(option.pipeline_options.kwargs)

        def convert(self, path: str, page_range: tuple[int, int]):
            return SimpleNamespace(
                document=SimpleNamespace(export_to_markdown=lambda: "content")
            )

    class FakePdfDocument:
        def __init__(self, path: str):
            pass

        def __len__(self):
            return 20

        def close(self):
            return None

    _install_docling_stubs(monkeypatch, FakeDocumentConverter, FakePdfDocument)

    backend = DoclingBackend()
    backend.convert(tmp_path / "sample.pdf", tmp_path / "work")

    assert captured_options == [
        {
            "do_ocr": False,
            "do_table_structure": True,
            "table_structure_options": SimpleNamespace(mode="fast"),
            "force_backend_text": False,
            "do_code_enrichment": False,
            "do_formula_enrichment": False,
            "do_picture_classification": False,
            "do_picture_description": False,
            "generate_page_images": False,
            "generate_picture_images": False,
            "accelerator_options": SimpleNamespace(num_threads=8, device="auto"),
            "layout_batch_size": 8,
            "table_batch_size": 8,
            "batch_polling_interval_seconds": 0.1,
        }
    ]


def test_docling_backend_extracts_pdf_outline_into_metadata(monkeypatch, tmp_path):
    class FakeDocumentConverter:
        def __init__(self, **kwargs):
            pass

        def convert(self, path: str, page_range: tuple[int, int]):
            return SimpleNamespace(
                document=SimpleNamespace(export_to_markdown=lambda: "content")
            )

    class FakePdfDocument:
        def __init__(self, path: str):
            pass

        def __len__(self):
            return 20

        def close(self):
            return None

    class FakeOutlineItem:
        def __init__(self, title: str):
            self.title = title

    class FakePdfReader:
        def __init__(self, path: str):
            self.outline = [FakeOutlineItem("第一节 重要提示、目录和释义"), FakeOutlineItem("第二节 公司简介和主要财务指标")]

        def get_destination_page_number(self, item):
            return {
                "第一节 重要提示、目录和释义": 5,
                "第二节 公司简介和主要财务指标": 19,
            }[item.title]

    _install_docling_stubs(
        monkeypatch,
        FakeDocumentConverter,
        FakePdfDocument,
        fake_pdf_reader=FakePdfReader,
    )

    backend = DoclingBackend()
    result = backend.convert(tmp_path / "sample.pdf", tmp_path / "work")

    assert result.metadata["outline"] == [
        {"title": "第一节 重要提示、目录和释义", "level": 1, "page": 6},
        {"title": "第二节 公司简介和主要财务指标", "level": 1, "page": 20},
    ]


def test_docling_backend_limits_conversion_and_outline_to_selected_page_range(
    monkeypatch, tmp_path, capsys
):
    calls: list[tuple[str, tuple[int, int]]] = []

    class FakeDocumentConverter:
        def __init__(self, **kwargs):
            pass

        def convert(self, path: str, page_range: tuple[int, int]):
            calls.append((path, page_range))
            start_page, end_page = page_range
            return SimpleNamespace(
                document=SimpleNamespace(
                    export_to_markdown=lambda: f"# Page {start_page}-{end_page}"
                )
            )

    class FakePdfDocument:
        def __init__(self, path: str):
            pass

        def __len__(self):
            return 400

        def close(self):
            return None

    class FakeOutlineItem:
        def __init__(self, title: str):
            self.title = title

    class FakePdfReader:
        def __init__(self, path: str):
            self.outline = [
                FakeOutlineItem("第一节 重要提示、目录和释义"),
                FakeOutlineItem("第二节 公司简介和主要财务指标"),
                FakeOutlineItem("第三节 管理层讨论与分析"),
            ]

        def get_destination_page_number(self, item):
            return {
                "第一节 重要提示、目录和释义": 5,
                "第二节 公司简介和主要财务指标": 19,
                "第三节 管理层讨论与分析": 23,
            }[item.title]

    _install_docling_stubs(
        monkeypatch,
        FakeDocumentConverter,
        FakePdfDocument,
        fake_pdf_reader=FakePdfReader,
    )

    backend = DoclingBackend()
    result = backend.convert(tmp_path / "sample.pdf", tmp_path / "work", page_range=(1, 20))

    assert calls == [
        (str(tmp_path / "sample.pdf"), (1, 20)),
    ]
    assert result.metadata["outline"] == [
        {"title": "第一节 重要提示、目录和释义", "level": 1, "page": 6},
        {"title": "第二节 公司简介和主要财务指标", "level": 1, "page": 20},
    ]

    stderr = capsys.readouterr().err
    assert "converting pages 1-20/20" in stderr
    assert "finished pages 1-20/20" in stderr


def _install_docling_stubs(
    monkeypatch, fake_converter, fake_pdf_document, *, fake_pdf_reader=None
):
    document_converter_module = ModuleType("docling.document_converter")
    document_converter_module.DocumentConverter = fake_converter
    document_converter_module.PdfFormatOption = FakePdfFormatOption

    base_models_module = ModuleType("docling.datamodel.base_models")
    base_models_module.InputFormat = SimpleNamespace(PDF="pdf")

    pipeline_options_module = ModuleType("docling.datamodel.pipeline_options")
    pipeline_options_module.PdfPipelineOptions = FakePdfPipelineOptions
    pipeline_options_module.TableFormerMode = SimpleNamespace(FAST="fast")
    pipeline_options_module.TableStructureOptions = lambda **kw: SimpleNamespace(**kw)

    accelerator_options_module = ModuleType("docling.datamodel.accelerator_options")
    accelerator_options_module.AcceleratorOptions = lambda **kw: SimpleNamespace(**kw)

    pypdfium_module = ModuleType("pypdfium2")
    pypdfium_module.PdfDocument = fake_pdf_document

    if fake_pdf_reader is not None:
        pypdf_module = ModuleType("pypdf")
        pypdf_module.PdfReader = fake_pdf_reader
        monkeypatch.setitem(sys.modules, "pypdf", pypdf_module)

    monkeypatch.setitem(sys.modules, "docling.document_converter", document_converter_module)
    monkeypatch.setitem(sys.modules, "docling.datamodel.base_models", base_models_module)
    monkeypatch.setitem(
        sys.modules, "docling.datamodel.pipeline_options", pipeline_options_module
    )
    monkeypatch.setitem(
        sys.modules, "docling.datamodel.accelerator_options", accelerator_options_module
    )
    monkeypatch.setitem(sys.modules, "pypdfium2", pypdfium_module)


class FakePdfFormatOption:
    def __init__(self, pipeline_options):
        self.pipeline_options = pipeline_options


class FakePdfPipelineOptions:
    def __init__(self, **kwargs):
        self.kwargs = kwargs


# --- _fix_scientific_notation unit tests ---


def test_fix_scientific_notation_converts_large_integer():
    assert _fix_scientific_notation("6.07846e+08") == "607846000"


def test_fix_scientific_notation_converts_negative_number():
    assert _fix_scientific_notation("-3.5e+06") == "-3500000"


def test_fix_scientific_notation_converts_multiple_numbers_in_table():
    text = "| 营业收入 | 6.07846e+08 | 5.12e+08 |"
    assert _fix_scientific_notation(text) == "| 营业收入 | 607846000 | 512000000 |"


def test_fix_scientific_notation_leaves_plain_text_unchanged():
    text = "净利润增长率为 12.5%，同比上升"
    assert _fix_scientific_notation(text) == text


def test_fix_scientific_notation_leaves_regular_numbers_unchanged():
    text = "| 2023 | 1,234,567 | 98.6% |"
    assert _fix_scientific_notation(text) == text


def test_docling_backend_fixes_scientific_notation_in_converted_markdown(
    monkeypatch, tmp_path
):
    """Table cells with scientific notation numbers are converted to plain integers."""

    class FakeDocumentConverter:
        def __init__(self, **kwargs):
            pass

        def convert(self, path: str, page_range: tuple[int, int]):
            return SimpleNamespace(
                document=SimpleNamespace(
                    export_to_markdown=lambda: "| 营业收入 | 6.07846e+08 |"
                )
            )

    class FakePdfDocument:
        def __init__(self, path: str):
            pass

        def __len__(self):
            return 3

        def close(self):
            return None

    _install_docling_stubs(monkeypatch, FakeDocumentConverter, FakePdfDocument)

    backend = DoclingBackend()
    result = backend.convert(tmp_path / "sample.pdf", tmp_path / "work")

    assert result.markdown == "| 营业收入 | 607846000 |"


def test_docling_backend_stream_convert_yields_chunks_with_metadata(monkeypatch, tmp_path, capsys):
    calls: list[tuple[str, tuple[int, int]]] = []

    class FakeDocumentConverter:
        def __init__(self, **kwargs):
            pass

        def convert(self, path: str, page_range: tuple[int, int]):
            calls.append((path, page_range))
            start_page, end_page = page_range
            return SimpleNamespace(
                document=SimpleNamespace(
                    export_to_markdown=lambda: f"# Page {start_page}-{end_page}"
                )
            )

    class FakePdfDocument:
        def __init__(self, path: str):
            pass

        def __len__(self):
            return 12

        def close(self):
            return None

    _install_docling_stubs(monkeypatch, FakeDocumentConverter, FakePdfDocument)

    backend = DoclingBackend()
    session = backend.stream_convert(tmp_path / "sample.pdf", tmp_path / "work", batch_size=5)

    assert isinstance(session, StreamingConversionSession)
    assert session.metadata["total_pages"] == 12
    assert session.metadata["page_range"] == (1, 12)
    assert list(session.chunks) == [
        ConversionChunk(page_start=1, page_end=5, markdown="# Page 1-5", metadata={}),
        ConversionChunk(page_start=6, page_end=10, markdown="# Page 6-10", metadata={}),
        ConversionChunk(page_start=11, page_end=12, markdown="# Page 11-12", metadata={}),
    ]
    assert calls == [
        (str(tmp_path / "sample.pdf"), (1, 5)),
        (str(tmp_path / "sample.pdf"), (6, 10)),
        (str(tmp_path / "sample.pdf"), (11, 12)),
    ]

    stderr = capsys.readouterr().err
    assert "converting pages 1-5/12" in stderr
    assert "finished pages 11-12/12" in stderr


def test_docling_backend_convert_collects_streaming_chunks(monkeypatch, tmp_path):
    class FakeDocumentConverter:
        def __init__(self, **kwargs):
            pass

        def convert(self, path: str, page_range: tuple[int, int]):
            start_page, end_page = page_range
            return SimpleNamespace(
                document=SimpleNamespace(
                    export_to_markdown=lambda: f"# Page {start_page}-{end_page}"
                )
            )

    class FakePdfDocument:
        def __init__(self, path: str):
            pass

        def __len__(self):
            return 6

        def close(self):
            return None

    _install_docling_stubs(monkeypatch, FakeDocumentConverter, FakePdfDocument)

    backend = DoclingBackend()
    result = backend.convert(tmp_path / "sample.pdf", tmp_path / "work", page_range=(2, 6))

    assert result.markdown == "# Page 2-6"
