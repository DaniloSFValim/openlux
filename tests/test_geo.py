"""Testes de geometria. Rasters aqui sao SINTETICOS (apenas para teste)."""
import math

import numpy as np
import pytest
from rasterio.transform import from_origin

from openlux.geo import AUTHALIC_RADIUS_M, WGS84_A, WGS84_E2, pixel_row_areas_m2, tile_transform


def test_global_area_equals_sphere_surface():
    # Soma das areas de todas as celulas de 15" do globo = 4*pi*R^2 (invariante exato).
    res = 15 / 3600
    t = from_origin(-180, 90, res, res)
    rows = int(round(180 / res))
    cols = int(round(360 / res))
    areas = pixel_row_areas_m2(t, rows)
    total = areas.sum() * cols
    assert total == pytest.approx(4 * math.pi * AUTHALIC_RADIUS_M**2, rel=1e-9)


def _ellipsoid_cell_area(lat_deg, dlon_deg, dlat_deg):
    """Referencia independente (aproximacao de celula pequena): dA = a^2 (1-e^2) cos(phi)
    / (1 - e^2 sin^2 phi)^2 * dlon * dlat."""
    ph = math.radians(lat_deg)
    f = WGS84_A**2 * (1 - WGS84_E2) * math.cos(ph) / (1 - WGS84_E2 * math.sin(ph) ** 2) ** 2
    return f * math.radians(dlon_deg) * math.radians(dlat_deg)


@pytest.mark.parametrize("lat_center", [0.0, -22.0, -45.0, 60.0])
def test_cell_area_matches_ellipsoid_reference(lat_center):
    res = 15 / 3600
    t = from_origin(0, lat_center + res / 2, res, res)
    a = pixel_row_areas_m2(t, 1)[0]
    assert a == pytest.approx(_ellipsoid_cell_area(lat_center, res, res), rel=1e-6)


def test_equatorial_one_degree_cell_area_km2():
    t = from_origin(0, 0.5, 1.0, 1.0)
    a = pixel_row_areas_m2(t, 1)[0]
    assert 12.30e9 < a < 12.32e9  # ~12.309 km2 no elipsoide (a esfera authalica daria 12.364)


def test_sphere_would_overestimate_at_rio_latitude():
    # Regressao: a esfera authalica superestima ~0,26% em 22 S (achado da validacao
    # raster x IBGE). O calculo elipsoidal nao deve repetir esse vies.
    res = 15 / 3600
    t = from_origin(0, -22.0 + res / 2, res, res)
    a = pixel_row_areas_m2(t, 1)[0]
    sphere = AUTHALIC_RADIUS_M**2 * math.radians(res) * (
        math.sin(math.radians(-22.0 + res / 2)) - math.sin(math.radians(-22.0 - res / 2)))
    assert sphere / a == pytest.approx(1.0026, abs=2e-4)


def test_area_decreases_with_latitude():
    res = 15 / 3600
    eq = pixel_row_areas_m2(from_origin(0, res / 2, res, res), 1)[0]
    hi = pixel_row_areas_m2(from_origin(0, 60 + res / 2, res, res), 1)[0]
    assert hi < eq


def test_tile_transform_h13v11_origin_is_upper_left_corner():
    # HDF-EOS StructMetadata do VNP46A4 h13v11: UL=(-50,-20), LR=(-40,-30), GridOrigin=UL.
    t = tile_transform(13, 11)
    assert (t.c, t.f) == (-50.0, -20.0)
    assert t.a == pytest.approx(15 / 3600)
    assert t.e == pytest.approx(-15 / 3600)
    # Borda inferior direita do tile (2400 px) = (-40, -30)
    assert t @ (2400, 2400) == pytest.approx((-40.0, -30.0))
