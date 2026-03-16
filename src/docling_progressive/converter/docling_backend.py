import logging
import sys
from pathlib import Path
from time import perf_counter

from docling_progressive.converter.models import ConversionResult


class DoclingBackend:
    def convert(self, input_path: Path, work_dir: Path) -> ConversionResult:
        from docling.datamodel.base_models import InputFormat
        from docling.datamodel.pipeline_options import PdfPipelineOptions
        from docling.document_converter import DocumentConverter, PdfFormatOption
        from pypdfium2 import PdfDocument

        asset_dir = work_dir / "assets"
        asset_dir.mkdir(parents=True, exist_ok=True)

        pipeline_options = PdfPipelineOptions(
            do_ocr=False,
            do_table_structure=False,
            force_backend_text=True,
            do_code_enrichment=False,
            do_formula_enrichment=False,
            do_picture_classification=False,
            do_picture_description=False,
            generate_page_images=False,
            generate_picture_images=False,
        )
        converter = DocumentConverter(
            allowed_formats=[InputFormat.PDF],
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            },
        )

        pdf = PdfDocument(str(input_path))
        total_pages = len(pdf)
        pdf.close()

        logger = logging.getLogger("docling")
        previous_level = logger.level
        logger.setLevel(logging.WARNING)
        try:
            markdown_parts: list[str] = []
            for page_no in range(1, total_pages + 1):
                page_start = perf_counter()
                print(
                    f"converting page {page_no}/{total_pages}...",
                    file=sys.stderr,
                    flush=True,
                )
                result = converter.convert(str(input_path), page_range=(page_no, page_no))
                markdown_parts.append(result.document.export_to_markdown())
                print(
                    f"finished page {page_no}/{total_pages} in {perf_counter() - page_start:.2f}s",
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
            },
        )
