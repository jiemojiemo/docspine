from pathlib import Path
from types import SimpleNamespace

import pytest

from docspine.converter.models import ConversionResult
from docspine import pipeline
from docspine.pipeline import build_progressive_package


class StubBackend:
    def convert(
        self,
        input_path: Path,
        work_dir: Path,
        page_range: tuple[int, int] | None = None,
    ) -> ConversionResult:
        asset_dir = work_dir / "assets"
        asset_dir.mkdir(parents=True, exist_ok=True)
        return ConversionResult(
            markdown="# Sample\n\nIntro\n\n## Section\n\nBody",
            asset_dir=asset_dir,
            metadata={"source": input_path.name},
        )


def test_build_progressive_package_creates_root_files(tmp_path):
    input_pdf = tmp_path / "sample.pdf"
    input_pdf.write_bytes(b"%PDF-1.4")
    output_dir = tmp_path / "out"

    build_progressive_package(input_pdf, output_dir, backend=StubBackend())

    assert (output_dir / "index.md").exists()
    assert (output_dir / "content.md").exists()
    assert (output_dir / "node.json").exists()


def test_build_progressive_package_passes_page_range_to_backend(tmp_path):
    captured: dict[str, object] = {}

    class CapturingBackend(StubBackend):
        def convert(
            self,
            input_path: Path,
            work_dir: Path,
            page_range: tuple[int, int] | None = None,
        ) -> ConversionResult:
            captured["page_range"] = page_range
            return super().convert(input_path, work_dir, page_range=page_range)

    input_pdf = tmp_path / "sample.pdf"
    input_pdf.write_bytes(b"%PDF-1.4")

    build_progressive_package(
        input_pdf,
        tmp_path / "out",
        backend=CapturingBackend(),
        page_range=(1, 20),
    )

    assert captured["page_range"] == (1, 20)


def test_build_progressive_package_uses_default_backend_when_none_provided(monkeypatch, tmp_path):
    class DefaultBackend:
        def convert(
            self,
            input_path: Path,
            work_dir: Path,
            page_range: tuple[int, int] | None = None,
        ) -> ConversionResult:
            return ConversionResult(
                markdown="# Sample",
                asset_dir=work_dir / "assets",
                metadata={},
            )

    monkeypatch.setattr(pipeline, "create_backend", lambda name: DefaultBackend())

    input_pdf = tmp_path / "sample.pdf"
    input_pdf.write_bytes(b"%PDF-1.4")

    build_progressive_package(input_pdf, tmp_path / "out")

    assert (tmp_path / "out" / "index.md").exists()


def test_build_progressive_package_raises_when_validation_fails(monkeypatch, tmp_path):
    monkeypatch.setattr(pipeline, "validate_output_tree", lambda output_dir: ["broken tree"])

    input_pdf = tmp_path / "sample.pdf"
    input_pdf.write_bytes(b"%PDF-1.4")

    with pytest.raises(ValueError, match="broken tree"):
        build_progressive_package(input_pdf, tmp_path / "out", backend=StubBackend())


def test_build_progressive_package_routes_stream_mode_to_streaming_pipeline(monkeypatch, tmp_path):
    captured: dict[str, object] = {}

    def fake_stream_build(
        input_pdf: Path,
        output_dir: Path,
        backend=None,
        page_range: tuple[int, int] | None = None,
        stream_batch_size: int = 5,
    ) -> None:
        captured["input_pdf"] = input_pdf
        captured["output_dir"] = output_dir
        captured["backend"] = backend
        captured["page_range"] = page_range
        captured["stream_batch_size"] = stream_batch_size

    input_pdf = tmp_path / "sample.pdf"
    input_pdf.write_bytes(b"%PDF-1.4")
    backend = StubBackend()

    monkeypatch.setattr(pipeline, "build_streaming_package", fake_stream_build)

    build_progressive_package(
        input_pdf,
        tmp_path / "out",
        backend=backend,
        page_range=(1, 20),
        stream=True,
    )

    assert captured == {
        "input_pdf": input_pdf,
        "output_dir": tmp_path / "out",
        "backend": backend,
        "page_range": (1, 20),
        "stream_batch_size": 5,
    }


def test_build_progressive_package_streaming_builds_skeleton_before_all_chunks_finish(tmp_path):
    input_pdf = tmp_path / "sample.pdf"
    input_pdf.write_bytes(b"%PDF-1.4")
    output_dir = tmp_path / "out"
    observations: dict[str, object] = {}

    class StreamingBackend:
        def convert(
            self,
            input_path: Path,
            work_dir: Path,
            page_range: tuple[int, int] | None = None,
        ) -> ConversionResult:
            raise AssertionError("non-stream convert should not be called")

        def stream_convert(
            self,
            input_path: Path,
            work_dir: Path,
            page_range: tuple[int, int] | None = None,
            batch_size: int = 5,
        ):
            def chunks():
                yield pipeline.ConversionChunk(
                    page_start=1,
                    page_end=5,
                    markdown="## 第一节 重要提示\n第一节正文。",
                )

                observations["root_exists_during_stream"] = (output_dir / "index.md").exists()
                observations["section_exists_during_stream"] = (
                    output_dir / "sections" / "01-第一节-重要提示" / "node.json"
                ).exists()
                observations["content_status_during_stream"] = (
                    output_dir / "sections" / "01-第一节-重要提示" / "node.json"
                ).read_text(encoding="utf-8")
                yield pipeline.ConversionChunk(
                    page_start=6,
                    page_end=10,
                    markdown="## 第二节 财务数据\n第二节正文。",
                )

            return pipeline.StreamingConversionSession(
                asset_dir=work_dir / "assets",
                metadata={
                    "source": str(input_path),
                    "backend": "stub",
                    "total_pages": 10,
                    "page_range": (1, 10),
                    "outline": [
                        {"title": "第一节 重要提示", "level": 1, "page": 1},
                        {"title": "第二节 财务数据", "level": 1, "page": 6},
                    ],
                },
                chunks=chunks(),
            )

    build_progressive_package(input_pdf, output_dir, backend=StreamingBackend(), stream=True)

    assert observations["root_exists_during_stream"] is True
    assert observations["section_exists_during_stream"] is True
    assert '"content_status": "partial"' in observations["content_status_during_stream"]
    assert '"content_status": "complete"' in (
        output_dir / "sections" / "01-第一节-重要提示" / "node.json"
    ).read_text(encoding="utf-8")
