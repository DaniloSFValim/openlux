"""Camada de dados da interface. Tabelas aqui sao SINTETICAS (apenas para teste)."""
import json

import geopandas as gpd
import numpy as np
import pandas as pd
import pytest
from shapely.geometry import box

from openlux.webdata import SOURCES, build_indicators, simplify_geojson


def _annual():
    rows = []
    for cd, nm, base in (("1", "Alfa", 2.0), ("2", "Beta", 4.0)):
        for y in (2012, 2013, 2014):
            rows.append(dict(CD_MUN=cd, NM_MUN=nm, year=y, mean_radiance=base + (y - 2012),
                             median_radiance=base, apparent_radiant_intensity_nw_sr=1e9 * base,
                             weight_sum=10.0 if cd == "1" else 30.0,
                             valid_fraction=1.0 if cd == "1" else np.nan))
    return pd.DataFrame(rows)


def _trends():
    rows = []
    for cd, nm in (("1", "Alfa"), ("2", "Beta")):
        for w in ("w1", "w2"):
            rows.append(dict(CD_MUN=cd, window=w, slope=1.0 if cd == "1" else np.nan, intercept=0.0,
                             tau=1.0, p_value=0.01, n_years=3, change_abs=2.0, change_pct=np.nan,
                             NM_MUN=nm, population=1000, intensity_per_capita_mw_sr_hab=5.5))
    return pd.DataFrame(rows)


def _build():
    return build_indicators(
        annual=_annual(), trends=_trends(), qa=pd.DataFrame({"year": [2012], "dark_land_mean": [0.0]}),
        sensitivity={"w1": {"near_nadir": {"spearman_trend_slope": 0.9}}},
        sensor_comparison={"years": [2018]},
        run_record={"processed_utc": "2026-01-01T00:00:00Z", "code": {"commit": "abc", "dirty": False},
                    "parameters": {"trend_windows": {"w1": [2012, 2013], "w2": [2012, 2014]},
                                   "change_floor_nw_cm2_sr": {"w1": 0.4, "w2": 0.5}},
                    "outputs": {"annual_main.csv": "0" * 64}})


def test_json_is_strict_no_nan_tokens():
    data = _build()
    text = json.dumps(data, allow_nan=False)  # levanta ValueError se houver NaN/inf
    assert "NaN" not in text


def test_series_are_aligned_to_years_and_nan_becomes_null():
    d = _build()
    assert d["meta"]["years"] == [2012, 2013, 2014]
    m = d["municipios"]["1"]
    assert m["name"] == "Alfa" and m["mean"] == [2.0, 3.0, 4.0]
    assert d["municipios"]["2"]["valid"] == [None, None, None]
    assert m["trends"]["w1"]["slope"] == 1.0 and m["trends"]["w1"]["change_pct"] is None
    assert d["municipios"]["2"]["trends"]["w1"]["slope"] is None
    assert m["population"] == 1000 and m["per_capita_mw_sr_hab"] == 5.5


def test_state_mean_is_weighted_by_valid_weight():
    d = _build()
    # (2.0*10 + 4.0*30) / 40 = 3.5 em 2012
    assert d["state"]["mean"][0] == pytest.approx(3.5)


def test_meta_carries_provenance_and_windows():
    d = _build()
    assert d["meta"]["windows"] == {"w1": [2012, 2013], "w2": [2012, 2014]}
    assert d["meta"]["run"]["code_commit"] == "abc"
    assert d["meta"]["run"]["output_sha256"]["annual_main.csv"] == "0" * 64


def test_sources_have_required_fields_and_no_unknown_license_is_hidden():
    for s in SOURCES:
        assert {"name", "institution", "url", "version", "license", "license_status"} <= set(s)
        assert s["license_status"] in {"confirmado", "nao_confirmado"}
        assert s["url"].startswith("https://")


def test_simplified_geojson_keeps_only_code_and_name():
    g = gpd.GeoDataFrame({"CD_MUN": ["1"], "NM_MUN": ["A"], "AREA_KM2": [1.0]},
                         geometry=[box(0, 0, 1, 1)], crs="EPSG:4674")
    fc = simplify_geojson(g, tolerance=0.001, ndigits=4)
    assert fc["type"] == "FeatureCollection" and len(fc["features"]) == 1
    assert fc["features"][0]["properties"] == {"CD_MUN": "1", "NM_MUN": "A"}
