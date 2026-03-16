from docling_progressive.converter.docling_backend import DoclingBackend


def create_backend(name: str = "docling") -> DoclingBackend:
    if name != "docling":
        raise ValueError(f"Unsupported backend: {name}")
    return DoclingBackend()
