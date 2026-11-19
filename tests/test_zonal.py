"""Testes de agregacao zonal. Rasters e poligonos aqui sao SINTETICOS (apenas para teste).

Grade de teste: 1 grau por pixel, para que a cobertura fracionaria seja exata e os
valores esperados possam ser calculados a mao.
"""
import geopandas as gpd
import numpy as np
import pytest
from rasterio.transform import from_origin
from shapely.geometry import box

from openlux.geo import pixel_row_areas_m2
from openlux.zonal import zonal_indicators

T = from_origin(0.0, 4.0, 1.0, 1.0)  # 4x4 pixels, canto sup. esq. em (0, 4)


def _gdf(*geoms):
    return gpd.GeoDataFrame({"id": list(range(len(geoms)))}, geometry=list(geoms), crs="EPSG:4326")


def test_constant_raster_whole_pixels():
    arr = np.full((4, 4), 2.0, dtype="float32")
    res = zonal_indicators(arr, T, _gdf(box(0, 2, 2, 4)))  # 2x2 pixels inteiros
    r = res.iloc[0]
    assert r.weight_sum == pytest.approx(4.0)
    assert r.mean_radiance == pytest.approx(2.0)
    assert r.median_radiance == pytest.approx(2.0)
    assert r.valid_fraction == pytest.approx(1.0)
    # S = sum(w * L * A) com A em cm2 -> nW/sr
    areas = pixel_row_areas_m2(T, 4)
    expected = sum(2.0 * areas[row] * 1e4 for row in (0, 1) for _ in (0, 1))
    assert r.apparent_radiant_intensity_nw_sr == pytest.approx(expected, rel=1e-12)


def test_fractional_coverage_weights():
    arr = np.zeros((4, 4), dtype="float32")
    arr[0, 0] = 0.0
    arr[0, 1] = 10.0
    # poligono: pixel (0,0) inteiro + metade esquerda do pixel (0,1)
    res = zonal_indicators(arr, T, _gdf(box(0, 3, 1.5, 4)))
    r = res.iloc[0]
    assert r.weight_sum == pytest.approx(1.5)
    assert r.mean_radiance == pytest.approx((0 * 1.0 + 10 * 0.5) / 1.5)


def test_weighted_median_uses_coverage_weights():
    arr = np.zeros((4, 4), dtype="float32")
    arr[0, 0] = 1.0
    arr[0, 1] = 5.0
    arr[0, 2] = 9.0
    # pesos: 1.0, 1.0, 0.2 -> total 2.2, metade 1.1; acumulado: 1.0 (v=1), 2.0 (v=5) -> mediana 5
    res = zonal_indicators(arr, T, _gdf(box(0, 3, 2.2, 4)))
    assert res.iloc[0].median_radiance == pytest.approx(5.0)


def test_invalid_pixels_are_excluded_from_weights():
    arr = np.full((4, 4), 4.0, dtype="float32")
    arr[0, 1] = np.nan  # pixel invalido (fill/mascara)
    res = zonal_indicators(arr, T, _gdf(box(0, 3, 2, 4)))
    r = res.iloc[0]
    assert r.weight_sum == pytest.approx(1.0)  # so o pixel (0,0) conta
    assert r.valid_fraction == pytest.approx(0.5)
    assert r.mean_radiance == pytest.approx(4.0)


def test_polygon_without_valid_pixels_gives_nan_not_zero():
    arr = np.full((4, 4), np.nan, dtype="float32")
    res = zonal_indicators(arr, T, _gdf(box(0, 2, 2, 4)))
    r = res.iloc[0]
    assert r.weight_sum == 0.0
    assert np.isnan(r.mean_radiance) and np.isnan(r.median_radiance)
    assert np.isnan(r.apparent_radiant_intensity_nw_sr)
    assert r.valid_fraction == 0.0


def test_polygon_outside_raster_does_not_crash():
    arr = np.full((4, 4), 1.0, dtype="float32")
    res = zonal_indicators(arr, T, _gdf(box(10, 10, 11, 11)))
    assert res.iloc[0].weight_sum == 0.0
    assert np.isnan(res.iloc[0].mean_radiance)


def test_input_array_is_not_modified():
    arr = np.full((4, 4), 3.0, dtype="float32")
    before = arr.copy()
    zonal_indicators(arr, T, _gdf(box(0, 2, 2, 4)))
    assert np.array_equal(arr, before)


def test_deterministic_repeated_runs():
    rng = np.random.default_rng(0)
    arr = rng.random((4, 4), dtype="float32")
    g = _gdf(box(0.3, 0.3, 3.1, 3.7))
    a = zonal_indicators(arr, T, g)
    b = zonal_indicators(arr, T, g)
    assert a.equals(b)
