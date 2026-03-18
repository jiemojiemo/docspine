import logging
import sys
import threading
from pathlib import Path
from time import perf_counter

from docspine.converter.models import ConversionResult

PAGE_BATCH_SIZE = 20


class DoclingBackend:
    def convert(
        self,
        input_path: Path,
        work_dir: Path,
        page_range: tuple[int, int] | None = None,
    ) -> ConversionResult:
        from docling.datamodel.accelerator_options import AcceleratorOptions
        from docling.datamodel.base_models import InputFormat
        from docling.datamodel.pipeline_options import (
            PdfPipelineOptions,
            TableFormerMode,
            TableStructureOptions,
        )
        from docling.document_converter import DocumentConverter, PdfFormatOption
        from pypdfium2 import PdfDocument

        asset_dir = work_dir / "assets"
        asset_dir.mkdir(parents=True, exist_ok=True)

        pipeline_options = PdfPipelineOptions(
            do_ocr=False,
            do_table_structure=True,
            table_structure_options=TableStructureOptions(mode=TableFormerMode.FAST),
            force_backend_text=False,
            do_code_enrichment=False,
            do_formula_enrichment=False,
            do_picture_classification=False,
            do_picture_description=False,
            generate_page_images=False,
            generate_picture_images=False,
            accelerator_options=AcceleratorOptions(
                num_threads=8,
                device="auto",
            ),
            layout_batch_size=8,
            table_batch_size=8,
            batch_polling_interval_seconds=0.1,
        )
        print("loading models...", file=sys.stderr, flush=True)
        model_load_start = perf_counter()
        converter = DocumentConverter(
            allowed_formats=[InputFormat.PDF],
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            },
        )
        print(
            f"models loaded in {perf_counter() - model_load_start:.1f}s",
            file=sys.stderr,
            flush=True,
        )

        pdf = PdfDocument(str(input_path))
        total_pages = len(pdf)
        pdf.close()
        selected_range = _normalize_page_range(page_range, total_pages)
        outline = _extract_pdf_outline(input_path, selected_range)
        selected_total_pages = selected_range[1] - selected_range[0] + 1

        logger = logging.getLogger("docling")
        previous_level = logger.level
        logger.setLevel(logging.WARNING)
        try:
            markdown_parts: list[str] = []
            for start_page in range(
                selected_range[0], selected_range[1] + 1, PAGE_BATCH_SIZE
            ):
                end_page = min(start_page + PAGE_BATCH_SIZE - 1, total_pages)
                end_page = min(end_page, selected_range[1])
                batch_start = perf_counter()
                print(
                    f"converting pages {start_page}-{end_page}/{selected_range[1]}...",
                    file=sys.stderr,
                    flush=True,
                )
                stop_ticker = threading.Event()
                ticker = threading.Thread(
                    target=_progress_ticker,
                    args=(stop_ticker, batch_start),
                    daemon=True,
                )
                ticker.start()
                try:
                    result = converter.convert(
                        str(input_path), page_range=(start_page, end_page)
                    )
                    markdown_parts.append(result.document.export_to_markdown())
                finally:
                    stop_ticker.set()
                    ticker.join()
                print(
                    f"finished pages {start_page}-{end_page}/{selected_range[1]} in {perf_counter() - batch_start:.2f}s",
                    file=sys.stderr,
                    flush=True,
                )
        finally:
            logger.setLevel(previous_level)

        return ConversionResult(
            markdown="\n\n".join(markdown_parts),
            asset_dir=asset_dir,
            metadata={
                "backend": "docling",
                "source": str(input_path),
                "total_pages": total_pages,
                "processed_pages": selected_total_pages,
                "page_range": selected_range,
                "outline": outline,
            },
        )


def _extract_pdf_outline(
    input_path: Path,
    page_range: tuple[int, int] | None = None,
) -> list[dict[str, object]]:
    try:
        from pypdf import PdfReader
    except ImportError:
        return []

    try:
        reader = PdfReader(str(input_path))
        outline = getattr(reader, "outline", [])
    except Exception:
        return []

    entries = _flatten_outline(reader, outline, level=1)
    if page_range is None:
        return entries
    start_page, end_page = page_range
    return [
        entry
        for entry in entries
        if isinstance(entry.get("page"), int) and start_page <= entry["page"] <= end_page
    ]


def _normalize_page_range(
    page_range: tuple[int, int] | None, total_pages: int
) -> tuple[int, int]:
    if page_range is None:
        return (1, total_pages)

    start_page, end_page = page_range
    return (max(1, start_page), min(total_pages, end_page))


def _progress_ticker(stop: threading.Event, start: float) -> None:
    while not stop.wait(timeout=5.0):
        print(
            f"  still converting... {perf_counter() - start:.0f}s elapsed",
            file=sys.stderr,
            flush=True,
        )


def _flatten_outline(reader, items, *, level: int) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    for item in items:
        if isinstance(item, list):
            result.extend(_flatten_outline(reader, item, level=level + 1))
            continue
        title = getattr(item, "title", None)
        if not title:
            continue
        try:
            page = reader.get_destination_page_number(item) + 1
        except Exception:
            page = None
        result.append({"title": title, "level": level, "page": page})
    return result
