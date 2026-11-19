"""Validacao de estabilidade. Arrays e poligonos SINTETICOS (apenas para teste)."""
import geopandas as gpd
import numpy as np
import pytest
from rasterio.transform import from_origin
from shapely.geometry import box

from openlux.validation import centroid_zonal_mean, coarsen

T = from_origin(0.0, 4.0, 1.0, 1.0)


def _g(*geoms):
    return gpd.GeoDataFrame({"id": range(len(geoms))}, geometry=list(geoms), crs="EPSG:4326")


def test_coarsen_block_mean_and_transform():
    a = np.arange(16, dtype="float32").reshape(4, 4)
    c, t = coarsen(a, T, 2)
    np.testing.assert_allclose(c, [[2.5, 4.5], [10.5, 12.5]])
    assert (t.a, t.e, t.c, t.f) == (2.0, -2.0, 0.0, 4.0)


def test_coarsen_ignores_nan_and_keeps_all_nan_blocks_nan():
    a = np.full((4, 4), 2.0, dtype="float32")
    a[0, 0] = np.nan
    a[2:, 2:] = np.nan
    c, _ = coarsen(a, T, 2)
    assert c[0, 0] == pytest.approx(2.0) and np.isnan(c[1, 1])


def test_coarsen_rejects_non_divisible_shape():
    with pytest.raises(ValueError):
        coarsen(np.zeros((5, 4), dtype="float32"), T, 2)


def test_centroid_mean_counts_pixels_by_center():
    a = np.zeros((4, 4), dtype="float32")
    a[0, 0], a[0, 1] = 0.0, 10.0
    # poligono cobre o pixel (0,0) e 40% do pixel (0,1): centro do (0,1) fica FORA
    r = centroid_zonal_mean(a, T, _g(box(0, 3, 1.4, 4)))
    assert r[0] == pytest.approx(0.0)
    # cobrindo 60% do pixel (0,1): centro DENTRO
    r2 = centroid_zonal_mean(a, T, _g(box(0, 3, 1.6, 4)))
    assert r2[0] == pytest.approx(5.0)


def test_centroid_mean_nan_when_no_valid_center_and_excludes_nan():
    a = np.full((4, 4), np.nan, dtype="float32")
    assert np.isnan(centroid_zonal_mean(a, T, _g(box(0, 2, 2, 4)))[0])
    b = np.full((4, 4), 3.0, dtype="float32")
    b[0, 0] = np.nan
    assert centroid_zonal_mean(b, T, _g(box(0, 2, 2, 4)))[0] == pytest.approx(3.0)
    assert np.isnan(centroid_zonal_mean(b, T, _g(box(10, 10, 11, 11)))[0])
