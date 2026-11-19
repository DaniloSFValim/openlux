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


# --- Leitura do produto Black Marble (VNP46A3/A4, Colecao 2) -----------------------------

_GRID = "HDFEOS/GRIDS/VIIRS_Grid_DNB_2d/Data Fields"
RADIANCE_FILL = -999.9
QUALITY_GOOD, QUALITY_POOR, QUALITY_GAP_FILLED = 0, 1, 2
#: Land_Water_Mask: 0 terra/deserto, 1 terra sem deserto, 2 agua interna, 3 mar, 5 costeiro.
DEFAULT_LAND_CODES = (0, 1, 5)


def read_blackmarble(path, layer="AllAngle_Composite_Snow_Free", *, n_min=1,
                     allowed_quality=(QUALITY_GOOD,), land_codes=DEFAULT_LAND_CODES):
    """Le uma camada de radiancia e aplica as mascaras de validade.

    Retorna ``(radiance, transform)``: ``radiance`` e float32 (nW cm^-2 sr^-1) com NaN
    onde: valor de preenchimento, radiancia negativa, qualidade fora de
    ``allowed_quality``, numero de observacoes < ``n_min`` ou fora de ``land_codes``.
    Parametros de mascara sao escolhas analiticas do pesquisador (ver analise de
    sensibilidade), nao propriedades do produto.
    """
    import h5py
    import numpy as np

    from openlux.geo import tile_transform

    verify_hdf5(path)
    with h5py.File(path, "r") as f:
        h = int(f.attrs["HorizontalTileNumber"])
        v = int(f.attrs["VerticalTileNumber"])
        g = f[_GRID]
        rad = g[layer][:].astype("float32")
        qual = g[f"{layer}_Quality"][:]
        num = g[f"{layer}_Num"][:]
        lw = g["Land_Water_Mask"][:]
    valid = (rad != RADIANCE_FILL) & (rad >= 0)
    valid &= np.isin(qual, allowed_quality)
    valid &= (num != 65535) & (num >= n_min)
    valid &= np.isin(lw, land_codes)
    out = np.where(valid, rad, np.nan).astype("float32")
    return out, tile_transform(h, v)


def read_for_qa(path, layer="AllAngle_Composite_Snow_Free", *, window=None, allowed_quality=(QUALITY_GOOD,)):
    """Radiancia (NaN em fill/negativo/qualidade nao permitida) e mascara terra/agua, SEM
    mascarar mar: usada pelos controles de ruido de fundo. ``window`` = (r0, r1, c0, c1)."""
    import h5py
    import numpy as np

    verify_hdf5(path)
    sl = (slice(None), slice(None)) if window is None else (slice(window[0], window[1]),
                                                           slice(window[2], window[3]))
    with h5py.File(path, "r") as f:
        g = f[_GRID]
        rad = g[layer][sl].astype("float32")
        qual = g[f"{layer}_Quality"][sl]
        lw = g["Land_Water_Mask"][sl]
    bad = (rad == RADIANCE_FILL) | (rad < 0) | ~np.isin(qual, allowed_quality)
    rad[bad] = np.nan
    return rad, lw
