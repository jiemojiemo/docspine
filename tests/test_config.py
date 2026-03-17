from pathlib import Path

from docspine.config import BuildConfig


def test_build_config_defaults_to_docling_backend():
    config = BuildConfig(input_path=Path("sample.pdf"), output_dir=Path("out"))

    assert config.backend == "docling"
