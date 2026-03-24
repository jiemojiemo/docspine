from argparse import ArgumentParser, ArgumentTypeError
from pathlib import Path

from docspine.pipeline import build_progressive_package


def parse_page_range(value: str) -> tuple[int, int]:
    if "-" in value:
        start_text, end_text = value.split("-", maxsplit=1)
    else:
        start_text = end_text = value

    try:
        start = int(start_text)
        end = int(end_text)
    except ValueError as exc:
        raise ArgumentTypeError("page range must be N or N-M") from exc

    if start < 1 or end < start:
        raise ArgumentTypeError("page range must be positive and ordered")
    return (start, end)


def build_parser() -> ArgumentParser:
    parser = ArgumentParser(prog="docspine")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser("build")
    build_parser.add_argument("input_path", type=Path)
    build_parser.add_argument("--out", dest="output_dir", type=Path, required=True)
    build_parser.add_argument("--pages", dest="page_range", type=parse_page_range)
    build_parser.add_argument("--stream", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "build":
        build_progressive_package(
            args.input_path,
            args.output_dir,
            page_range=args.page_range,
            stream=args.stream,
        )
    return 0
