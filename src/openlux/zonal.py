"""Agregacao zonal com cobertura fracionaria de pixels.

Metodo: para cada poligono, cada pixel recebe peso ``w_i`` = fracao da area do pixel
coberta pelo poligono (calculada por ``exactextract``, no plano lat/lon; dentro de um
pixel de ~460 m a diferenca em relacao a cobertura geodesica e desprezivel). Pixels
invalidos (NaN) ficam fora do numerador e do denominador e sao contabilizados em
``valid_fraction``. O raster NAO e reamostrado.

Indicadores por poligono (L em nW cm^-2 sr^-1):
- ``mean_radiance``   : sum(w L) / sum(w)
- ``median_radiance`` : mediana ponderada inferior (menor L cujo peso acumulado >= metade do total)
- ``apparent_radiant_intensity_nw_sr`` : sum(w L A) com A em cm^2.
  E uma intensidade radiante APARENTE na direcao observada pelo sensor; NAO e a
  emissao luminosa total do municipio.
- ``weight_sum``      : sum(w) sobre pixels validos (em unidades de pixel)
- ``valid_fraction``  : sum(w validos) / sum(w de todos os pixels cobertos)
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from exactextract import exact_extract
from rasterio.io import MemoryFile
from rasterio.transform import Affine

from openlux.geo import pixel_row_areas_m2

M2_TO_CM2 = 1e4


def _weighted_lower_median(values: np.ndarray, weights: np.ndarray) -> float:
    order = np.argsort(values, kind="stable")
    v, w = values[order], weights[order]
    cum = np.cumsum(w)
    idx = int(np.searchsorted(cum, 0.5 * cum[-1], side="left"))
    return float(v[min(idx, len(v) - 1)])


def zonal_indicators(array: np.ndarray, transform: Affine, polygons, crs: str = "EPSG:4326") -> pd.DataFrame:
    """Calcula indicadores zonais. ``array`` usa NaN para pixels invalidos.

    ``polygons`` e um GeoDataFrame no mesmo CRS do raster. Retorna um DataFrame com o
    mesmo indice de ``polygons``.
    """
    if array.ndim != 2:
        raise ValueError("array deve ser 2D")
    from pyproj import CRS
    if polygons.crs is None or CRS.from_user_input(polygons.crs) != CRS.from_user_input(crs):
        raise ValueError(f"CRS dos poligonos ({polygons.crs}) difere do CRS do raster ({crs}); "
                         "reprojete ou declare explicitamente a equivalencia antes de agregar")
    arr = np.asarray(array, dtype="float32")  # copia: o original nao e modificado
    nrows, ncols = arr.shape
    row_area_cm2 = pixel_row_areas_m2(transform, nrows) * M2_TO_CM2

    # exactextract descarta celulas NaN; para contabilizar a cobertura de TODOS os pixels
    # (incluindo invalidos) ele roda sobre um raster finito, e a validade e os valores
    # vem do array original via cell_id (indice linha-major).
    profile = dict(driver="GTiff", height=nrows, width=ncols, count=1, dtype="float32",
                   crs=crs, transform=transform)
    with MemoryFile() as mem:
        with mem.open(**profile) as ds:
            ds.write(np.zeros((nrows, ncols), dtype="float32"), 1)
        with mem.open() as ds:
            out = exact_extract(ds, polygons, ["coverage", "cell_id"], output="pandas")
    flat = arr.ravel()

    rows = []
    for i in range(len(polygons)):
        cov = np.asarray(out.iloc[i]["coverage"], dtype="float64")
        cell = np.asarray(out.iloc[i]["cell_id"], dtype="int64")
        vals = flat[cell].astype("float64")
        total_w = float(cov.sum())
        ok = np.isfinite(vals) & (cov > 0)
        w = cov[ok]
        v = vals[ok]
        wsum = float(w.sum())
        if wsum == 0.0:
            rows.append(dict(weight_sum=0.0, valid_fraction=0.0, mean_radiance=np.nan, median_radiance=np.nan,
                             apparent_radiant_intensity_nw_sr=np.nan))
            continue
        a_cm2 = row_area_cm2[cell[ok] // ncols]
        rows.append(dict(
            weight_sum=wsum,
            valid_fraction=wsum / total_w,
            mean_radiance=float((w * v).sum() / wsum),
            median_radiance=_weighted_lower_median(v, w),
            apparent_radiant_intensity_nw_sr=float((w * v * a_cm2).sum()),
        ))
    return pd.DataFrame(rows, index=polygons.index)
