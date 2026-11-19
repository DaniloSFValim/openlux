"""Geometria da grade lat/lon do NASA Black Marble (VNP46A3/A4).

Decisao metodologica: a grade dos produtos e lat/lon (EPSG:4326) com pixels de
15 arc-s. As arrays ``lat``/``lon`` do HDF5 sao os cantos superior-esquerdos dos
pixels; o georreferenciamento correto e ``from_origin(lon0, lat0, 15", 15")`` com
(lon0, lat0) = canto superior esquerdo do tile (``GridOrigin=HE5_HDFE_GD_UL``),
sem deslocamento de meio pixel. Evidencia: StructMetadata.0 do VNP46A4 h13v11
(UpperLeft = -50, -20; LowerRight = -40, -30).
"""
from __future__ import annotations

import math

import numpy as np
from rasterio.transform import Affine, from_origin

#: Raio da esfera de area equivalente ao elipsoide WGS84 (esfera authalica), em metros.
AUTHALIC_RADIUS_M = 6371007.1809

PIXEL_ARCSEC = 15
PIXEL_DEG = PIXEL_ARCSEC / 3600
TILE_PIXELS = 2400  # 10 graus / 15 arc-s
TILE_DEG = 10


def tile_transform(h: int, v: int) -> Affine:
    """Transformacao afim do tile ``hXXvYY`` (origem no canto superior esquerdo)."""
    lon0 = -180.0 + TILE_DEG * h
    lat0 = 90.0 - TILE_DEG * v
    return from_origin(lon0, lat0, PIXEL_DEG, PIXEL_DEG)


def pixel_row_areas_m2(transform: Affine, nrows: int) -> np.ndarray:
    """Area (m2) de um pixel em cada linha, na esfera authalica.

    A = R^2 * dlon(rad) * (sin(lat_norte) - sin(lat_sul)). A area depende apenas
    da latitude, por isso e retornado um vetor por linha.
    """
    dlon = math.radians(abs(transform.a))
    rows = np.arange(nrows)
    lat_n = np.radians(transform.f + transform.e * rows)
    lat_s = np.radians(transform.f + transform.e * (rows + 1))
    return AUTHALIC_RADIUS_M**2 * dlon * (np.sin(lat_n) - np.sin(lat_s))
