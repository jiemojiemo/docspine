from argparse import ArgumentParser
from pathlib import Path

from docling_progressive.pipeline import build_progressive_package


def build_parser() -> ArgumentParser:
    parser = ArgumentParser(prog="docling-progressive")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser("build")
    build_parser.add_argument("input_path", type=Path)
    build_parser.add_argument("--out", dest="output_dir", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "build":
        build_progressive_package(args.input_path, args.output_dir)
    return 0
