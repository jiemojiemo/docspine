import pytest

from docspine.converter.docling_backend import DoclingBackend
from docspine.converter.factory import create_backend


def test_create_backend_returns_docling_backend():
    backend = create_backend()

    assert isinstance(backend, DoclingBackend)


def test_create_backend_rejects_unknown_backend():
    with pytest.raises(ValueError, match="Unsupported backend: other"):
        create_backend("other")
