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

#: Elipsoide WGS84 (diferenca para GRS80/SIRGAS 2000 na area e desprezivel para este uso).
WGS84_A = 6378137.0
WGS84_E2 = 0.00669437999014
#: Raio da esfera de area equivalente ao elipsoide (so o TOTAL global coincide), metros.
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


def _q(sin_lat: np.ndarray) -> np.ndarray:
    """Funcao de area authalica q(phi) (Snyder, 1987): area da zona = a^2/2 * dlon * dq."""
    e = math.sqrt(WGS84_E2)
    return (1 - WGS84_E2) * (
        sin_lat / (1 - WGS84_E2 * sin_lat**2)
        - (1 / (2 * e)) * np.log((1 - e * sin_lat) / (1 + e * sin_lat))
    )


def pixel_row_areas_m2(transform: Affine, nrows: int) -> np.ndarray:
    """Area (m2) de um pixel em cada linha, no elipsoide WGS84 (formula exata).

    A = (a^2 / 2) * dlon(rad) * [q(lat_norte) - q(lat_sul)]. A area depende apenas da
    latitude, por isso e retornado um vetor por linha. Nao se usa a esfera authalica
    porque ela so conserva a area no total global: em ~22 S superestima ~0,26%, vies
    detectado ao comparar a area raster com a area oficial do IBGE.
    """
    dlon = math.radians(abs(transform.a))
    rows = np.arange(nrows)
    lat_n = np.radians(transform.f + transform.e * rows)
    lat_s = np.radians(transform.f + transform.e * (rows + 1))
    return 0.5 * WGS84_A**2 * dlon * (_q(np.sin(lat_n)) - _q(np.sin(lat_s)))
