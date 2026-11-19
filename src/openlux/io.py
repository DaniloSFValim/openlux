"""Integridade de arquivos e leitura dos produtos Black Marble."""
from __future__ import annotations

import hashlib
from pathlib import Path

HDF5_SIGNATURE = b"\x89HDF\r\n\x1a\n"


class InvalidDownload(Exception):
    """O arquivo baixado nao e um HDF5 valido (ex.: pagina de login ou erro de proxy)."""


def sha256_file(path: str | Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while block := f.read(chunk):
            h.update(block)
    return h.hexdigest()


def is_hdf5(path: str | Path) -> bool:
    try:
        with open(path, "rb") as f:
            return f.read(8) == HDF5_SIGNATURE
    except OSError:
        return False


def verify_hdf5(path: str | Path) -> None:
    """Levanta ``InvalidDownload`` se ``path`` nao for um HDF5 (assinatura de 8 bytes)."""
    p = Path(path)
    if not p.is_file():
        raise InvalidDownload(f"arquivo inexistente: {p}")
    if not is_hdf5(p):
        raise InvalidDownload(
            f"{p.name} ({p.stat().st_size} bytes) nao tem assinatura HDF5; "
            "provavel pagina de login, erro de proxy ou licenca nao aceita"
        )
