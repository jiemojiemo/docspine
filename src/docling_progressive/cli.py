from argparse import ArgumentParser
from pathlib import Path


def build_parser() -> ArgumentParser:
    parser = ArgumentParser(prog="docling-progressive")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser("build")
    build_parser.add_argument("input_path", type=Path)
    build_parser.add_argument("--out", dest="output_dir", type=Path, required=True)
    return parser


def main() -> int:
    build_parser().parse_args()
    return 0
