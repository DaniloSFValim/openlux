"""Indicadores temporais. Series e rasters sao SINTETICOS (apenas para teste)."""
import geopandas as gpd
import numpy as np
import pytest
from rasterio.transform import from_origin
from shapely.geometry import box

from openlux.temporal import annual_table, change, rank_agreement, trend

T = from_origin(0.0, 4.0, 1.0, 1.0)


def test_trend_recovers_exact_linear_slope():
    years = np.arange(2012, 2022)
    vals = 2.0 * (years - 2012) + 1.0
    r = trend(years, vals, min_years=8)
    assert r["slope"] == pytest.approx(2.0)
    assert r["n_years"] == 10
    assert r["tau"] == pytest.approx(1.0)
    assert r["p_value"] < 1e-4


def test_trend_ignores_nan_and_enforces_min_years():
    years = np.arange(2012, 2022)
    vals = np.arange(10, dtype=float)
    vals[:4] = np.nan  # restam 6 anos validos
    assert np.isnan(trend(years, vals, min_years=8)["slope"])
    assert trend(years, vals, min_years=6)["slope"] == pytest.approx(1.0)


def test_trend_constant_series_has_zero_slope_and_undefined_p():
    r = trend(np.arange(2012, 2022), np.full(10, 3.0), min_years=8)
    assert r["slope"] == 0.0 and np.isnan(r["p_value"])


def test_trend_is_robust_to_single_outlier():
    years = np.arange(2012, 2022)
    vals = years - 2012.0
    vals[5] = 500.0
    assert trend(years, vals, min_years=8)["slope"] == pytest.approx(1.0, abs=0.2)


def test_change_relative_requires_baseline_above_floor():
    r = change(np.array([0.0, 0.2, 2.0]), np.array([1.0, 0.4, 3.0]), floor=0.5)
    np.testing.assert_allclose(r["abs"], [1.0, 0.2, 1.0])
    assert np.isnan(r["pct"][0]) and np.isnan(r["pct"][1])  # linha de base < piso
    assert r["pct"][2] == pytest.approx(50.0)


def test_change_never_returns_inf():
    r = change(np.array([0.0]), np.array([5.0]), floor=0.0)
    assert np.isnan(r["pct"][0])


def test_annual_table_uses_loader_and_orders_years():
    polys = gpd.GeoDataFrame({"cd_mun": ["A", "B"]},
                             geometry=[box(0, 2, 2, 4), box(2, 0, 4, 2)], crs="EPSG:4326")

    def loader(year):
        return np.full((4, 4), float(year - 2010), dtype="float32"), T

    df = annual_table(loader, [2012, 2013, 2014], polys, id_col="cd_mun")
    assert set(df.columns) >= {"cd_mun", "year", "mean_radiance", "median_radiance",
                               "apparent_radiant_intensity_nw_sr", "weight_sum", "valid_fraction"}
    a = df[df.cd_mun == "A"].sort_values("year")
    assert a.mean_radiance.tolist() == pytest.approx([2.0, 3.0, 4.0])
    assert len(df) == 6


def test_rank_agreement_identical_and_reversed():
    x = np.array([1.0, 5.0, 3.0, 9.0])
    assert rank_agreement(x, x) == pytest.approx(1.0)
    assert rank_agreement(x, -x) == pytest.approx(-1.0)


def test_rank_agreement_ignores_nan_pairs():
    x = np.array([1.0, 2.0, np.nan, 4.0])
    y = np.array([1.0, 2.0, 3.0, 4.0])
    assert rank_agreement(x, y) == pytest.approx(1.0)
