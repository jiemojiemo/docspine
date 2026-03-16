import logging
from pathlib import Path
from time import perf_counter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logging.getLogger("docling").setLevel(logging.INFO)

print("starting import...", flush=True)
t0 = perf_counter()

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from pypdfium2 import PdfDocument

print(f"import finished in {perf_counter() - t0:.2f}s", flush=True)

source = "/Users/user/Documents/work/money/财报/迈瑞_2024.pdf"
source_path = Path(source)
output_path = Path.cwd() / f"{source_path.stem}.md"

pipeline_options = PdfPipelineOptions(
    do_ocr=False,
    do_table_structure=False,
    force_backend_text=True,
    do_code_enrichment=False,
    do_formula_enrichment=False,
    do_picture_classification=False,
    do_picture_description=False,
    generate_page_images=False,
    generate_picture_images=False
)

t1 = perf_counter()
print("initializing converter...", flush=True)

converter = DocumentConverter(
    allowed_formats=[InputFormat.PDF],
    format_options={
        InputFormat.PDF: PdfFormatOption(
            pipeline_options=pipeline_options,
        )
    },
)

t2 = perf_counter()
print(f"converter initialized in {t2 - t1:.2f}s", flush=True)
print("starting conversion...", flush=True)

pdf = PdfDocument(str(source_path))
total_pages = len(pdf)
pdf.close()

markdown_parts: list[str] = []

for page_no in range(1, total_pages + 1):
    page_start = perf_counter()
    print(f"converting page {page_no}/{total_pages}...", flush=True)
    result = converter.convert(source, page_range=(page_no, page_no))
    markdown_parts.append(result.document.export_to_markdown())
    print(
        f"finished page {page_no}/{total_pages} in {perf_counter() - page_start:.2f}s",
        flush=True,
    )

print(f"conversion finished in {perf_counter() - t2:.2f}s", flush=True)
output_path.write_text("\n\n".join(markdown_parts), encoding="utf-8")
print(f"markdown saved to {output_path}", flush=True)
