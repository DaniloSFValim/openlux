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


def test_mismatched_or_missing_polygon_crs_is_rejected():
    arr = np.full((4, 4), 1.0, dtype="float32")
    g = _gdf(box(0, 2, 2, 4)).set_crs("EPSG:4674", allow_override=True)
    with pytest.raises(ValueError, match="CRS"):
        zonal_indicators(arr, T, g)
    g2 = gpd.GeoDataFrame({"id": [0]}, geometry=[box(0, 2, 2, 4)])  # sem CRS
    with pytest.raises(ValueError, match="CRS"):
        zonal_indicators(arr, T, g2)


# --- fracao da area acima de limiares ---------------------------------------------------------

def test_fraction_above_threshold_uses_coverage_weights_and_ge():
    arr = np.zeros((4, 4), dtype="float32")
    arr[0, 0], arr[0, 1] = 2.0, 10.0
    # pesos: pixel (0,0)=1.0 (valor 2) e pixel (0,1)=0.5 (valor 10)
    res = zonal_indicators(arr, T, _gdf(box(0, 3, 1.5, 4)), thresholds={"t5": 5.0, "t2": 2.0, "t11": 11.0})
    r = res.iloc[0]
    assert r.frac_above_t5 == pytest.approx(0.5 / 1.5)
    assert r.frac_above_t2 == pytest.approx(1.0)      # >= : valor igual ao limiar conta
    assert r.frac_above_t11 == pytest.approx(0.0)


def test_fraction_above_excludes_invalid_pixels_and_is_nan_without_valid():
    arr = np.full((4, 4), 3.0, dtype="float32")
    arr[0, 1] = np.nan
    r = zonal_indicators(arr, T, _gdf(box(0, 3, 2, 4)), thresholds={"t": 1.0}).iloc[0]
    assert r.frac_above_t == pytest.approx(1.0)       # o NaN nao entra no denominador
    allnan = np.full((4, 4), np.nan, dtype="float32")
    r2 = zonal_indicators(allnan, T, _gdf(box(0, 2, 2, 4)), thresholds={"t": 1.0}).iloc[0]
    assert np.isnan(r2.frac_above_t)


def test_no_threshold_columns_by_default():
    arr = np.full((4, 4), 3.0, dtype="float32")
    res = zonal_indicators(arr, T, _gdf(box(0, 2, 2, 4)))
    assert not [c for c in res.columns if c.startswith("frac_above")]


def test_weighted_lower_quantile_hand_computed():
    from openlux.zonal import _weighted_lower_quantile, _weighted_lower_median
    v = np.array([1.0, 2.0, 3.0, 4.0]); w = np.ones(4)
    assert _weighted_lower_quantile(v, w, 0.75) == 3.0      # alvo 3 -> primeiro acumulado >= 3
    assert _weighted_lower_quantile(v, w, 0.9) == 4.0       # alvo 3,6 -> 4
    assert _weighted_lower_median(v, w) == 2.0               # mediana inferior, como antes
    v2 = np.array([10.0, 20.0]); w2 = np.array([1.0, 3.0])   # peso total 4
    assert _weighted_lower_quantile(v2, w2, 0.25) == 10.0    # alvo 1
    assert _weighted_lower_quantile(v2, w2, 0.5) == 20.0     # alvo 2 -> cumulado 4


def test_zonal_quantiles_are_opt_in_and_do_not_change_default_columns():
    import geopandas as gpd
    from shapely.geometry import box
    from affine import Affine
    from openlux.zonal import zonal_indicators
    arr = np.arange(16, dtype="float32").reshape(4, 4)
    t = Affine(1.0, 0, 0, 0, -1.0, 4)
    polys = gpd.GeoDataFrame({"id": [1]}, geometry=[box(0, 0, 4, 4)], crs="EPSG:4326")
    base = zonal_indicators(arr, t, polys)
    assert not any(c.startswith("q") and c.endswith("_radiance") for c in base.columns)
    com = zonal_indicators(arr, t, polys, quantiles=(0.75,))
    assert "q75_radiance" in com.columns and np.isfinite(com["q75_radiance"].iloc[0])
