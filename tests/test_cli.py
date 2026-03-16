from pathlib import Path

from docling_progressive.cli import build_parser


def test_build_parser_accepts_input_and_output_paths():
    parser = build_parser()
    args = parser.parse_args(["build", "sample.pdf", "--out", "out"])

    assert args.command == "build"
    assert args.input_path == Path("sample.pdf")
    assert args.output_dir == Path("out")


def test_build_parser_accepts_optional_page_range():
    parser = build_parser()
    args = parser.parse_args(
        ["build", "sample.pdf", "--out", "out", "--pages", "1-20"]
    )

    assert args.page_range == (1, 20)
