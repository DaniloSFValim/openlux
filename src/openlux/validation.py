"""Utilitarios de validacao: estabilidade frente ao criterio de agregacao e a resolucao."""
from __future__ import annotations

import numpy as np
from rasterio.features import rasterize
from rasterio.transform import Affine


def coarsen(array: np.ndarray, transform: Affine, k: int):
    """Agrega blocos k x k pela media ignorando NaN (bloco todo NaN -> NaN).

    Retorna ``(array_grosso, transform_grosso)``. As dimensoes devem ser divisiveis por k.
    """
    r, c = array.shape
    if r % k or c % k:
        raise ValueError("dimensoes nao divisiveis por k")
    blocks = array.astype("float64").reshape(r // k, k, c // k, k)
    valid = np.isfinite(blocks)
    cnt = valid.sum(axis=(1, 3))
    s = np.where(valid, blocks, 0.0).sum(axis=(1, 3))
    out = np.where(cnt > 0, s / np.maximum(cnt, 1), np.nan).astype("float32")
    t = Affine(transform.a * k, transform.b, transform.c, transform.d, transform.e * k, transform.f)
    return out, t


def centroid_zonal_mean(array: np.ndarray, transform: Affine, polygons) -> np.ndarray:
    """Media por poligono usando apenas pixels cujo CENTRO esta dentro do poligono.

    Criterio alternativo (sem cobertura fracionaria) para comparar com ``zonal_indicators``.
    Poligonos sem pixel valido retornam NaN.
    """
    n = len(polygons)
    shapes = [(g, i + 1) for i, g in enumerate(polygons.geometry)]
    lab = rasterize(shapes, out_shape=array.shape, transform=transform, fill=0,
                    all_touched=False, dtype="int32")
    v = array.astype("float64")
    ok = np.isfinite(v) & (lab > 0)
    cnt = np.bincount(lab[ok], minlength=n + 1)[1:]
    s = np.bincount(lab[ok], weights=v[ok], minlength=n + 1)[1:]
    return np.where(cnt > 0, s / np.maximum(cnt, 1), np.nan)
