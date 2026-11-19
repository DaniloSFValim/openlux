"""Testes de geometria. Rasters aqui sao SINTETICOS (apenas para teste)."""
import math

import numpy as np
import pytest
from rasterio.transform import from_origin

from openlux.geo import AUTHALIC_RADIUS_M, pixel_row_areas_m2, tile_transform


def test_global_area_equals_sphere_surface():
    # Soma das areas de todas as celulas de 15" do globo = 4*pi*R^2 (invariante exato).
    res = 15 / 3600
    t = from_origin(-180, 90, res, res)
    rows = int(round(180 / res))
    cols = int(round(360 / res))
    areas = pixel_row_areas_m2(t, rows)
    total = areas.sum() * cols
    assert total == pytest.approx(4 * math.pi * AUTHALIC_RADIUS_M**2, rel=1e-9)


def test_equatorial_one_degree_cell_area():
    t = from_origin(0, 0.5, 1.0, 1.0)  # celula 1x1 grau centrada no equador
    a = pixel_row_areas_m2(t, 1)[0]
    # ~12.364 km2 na esfera authalica (valor calculado analiticamente: R^2*dlon*2*sin(0.5deg))
    expected = AUTHALIC_RADIUS_M**2 * math.radians(1) * 2 * math.sin(math.radians(0.5))
    assert a == pytest.approx(expected, rel=1e-12)
    assert 12.3e9 < a < 12.4e9


def test_area_decreases_with_latitude():
    res = 15 / 3600
    t = from_origin(0, 0.0, res, res)
    eq = pixel_row_areas_m2(t, 1)[0]
    t2 = from_origin(0, -60.0, res, res)
    hi = pixel_row_areas_m2(t2, 1)[0]
    assert hi / eq == pytest.approx(math.cos(math.radians(60)), rel=1e-3)


def test_tile_transform_h13v11_origin_is_upper_left_corner():
    # HDF-EOS StructMetadata do VNP46A4 h13v11: UL=(-50,-20), LR=(-40,-30), GridOrigin=UL.
    t = tile_transform(13, 11)
    assert (t.c, t.f) == (-50.0, -20.0)
    assert t.a == pytest.approx(15 / 3600)
    assert t.e == pytest.approx(-15 / 3600)
    # Borda inferior direita do tile (2400 px) = (-40, -30)
    assert t @ (2400, 2400) == pytest.approx((-40.0, -30.0))
