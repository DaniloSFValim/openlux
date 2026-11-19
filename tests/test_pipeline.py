"""Pipeline ponta a ponta com HDF5 e poligonos SINTETICOS (so para teste)."""
import json

import geopandas as gpd
import h5py
import numpy as np
import pandas as pd
import pytest
from shapely.geometry import box

from openlux.pipeline import run_annual

GRID = "HDFEOS/GRIDS/VIIRS_Grid_DNB_2d/Data Fields"
N = 40  # grade sintetica 40x40 (a transformacao vem dos atributos de tile)


def make_h5(path, value_fn):
    rad = np.fromfunction(value_fn, (N, N), dtype="float32").astype("float32")
    with h5py.File(path, "w") as f:
        f.attrs["HorizontalTileNumber"] = 13
        f.attrs["VerticalTileNumber"] = 11
        g = f.create_group(GRID)
        for layer in ("AllAngle_Composite_Snow_Free", "NearNadir_Composite_Snow_Free"):
            g[layer] = rad
            g[layer + "_Quality"] = np.zeros((N, N), dtype="uint8")
            g[layer + "_Num"] = np.full((N, N), 20, dtype="uint16")
        g["Land_Water_Mask"] = np.ones((N, N), dtype="uint8")


@pytest.fixture
def setup(tmp_path):
    files = {}
    for i, year in enumerate(range(2012, 2022)):  # 10 anos; brilho cresce 1 por ano na cidade A
        p = tmp_path / f"y{year}.h5"
        make_h5(p, lambda r, c, i=i: np.where(c < 20, 5.0 + i, 1.0))
        files[year] = p
    res = 15 / 3600
    x0, y0 = -50.0, -20.0
    polys = gpd.GeoDataFrame(
        {"cd_mun": ["A", "B"]},
        geometry=[box(x0, y0 - 10 * res, x0 + 10 * res, y0),
                  box(x0 + 25 * res, y0 - 10 * res, x0 + 35 * res, y0)], crs="EPSG:4326")
    pop = pd.DataFrame({"cd_mun": ["A", "B"], "population": [1000, 500]})
    return files, polys, pop, tmp_path


def test_end_to_end_values_and_outputs(setup):
    files, polys, pop, tmp = setup
    rec = run_annual(files, polys, "cd_mun", pop, tmp / "out", population_year=2021,
                     code_dir=tmp)
    tr = pd.read_csv(tmp / "out" / "trends_main.csv").set_index("cd_mun")
    assert tr.loc["A", "slope"] == pytest.approx(1.0)   # +1 nW/cm2/sr por ano
    assert tr.loc["B", "slope"] == pytest.approx(0.0)   # constante
    assert tr.loc["A", "change_abs"] == pytest.approx(9.0)
    assert tr.loc["A", "population"] == 1000
    sens = json.loads((tmp / "out" / "sensitivity.json").read_text())
    assert sens["all"]["near_nadir"]["trend_sign_agreement"] == pytest.approx(1.0)
    assert set(rec["inputs"]) == {str(y) for y in files}
    assert all(len(h) == 64 for h in rec["outputs"].values())


def test_outputs_are_byte_identical_across_runs(setup):
    files, polys, pop, tmp = setup
    r1 = run_annual(files, polys, "cd_mun", pop, tmp / "o1", population_year=2021, code_dir=tmp)
    r2 = run_annual(files, polys, "cd_mun", pop, tmp / "o2", population_year=2021, code_dir=tmp)
    assert r1["outputs"] == r2["outputs"]


def test_record_has_no_token_like_content(setup):
    files, polys, pop, tmp = setup
    run_annual(files, polys, "cd_mun", pop, tmp / "o", population_year=2021, code_dir=tmp)
    text = (tmp / "o" / "run_record.json").read_text()
    assert "Bearer" not in text and "eyJ" not in text


def test_separate_trend_windows_and_extra_columns_and_units(setup):
    files, polys, pop, tmp = setup
    polys = polys.assign(nome=["Alfa", "Beta"])
    run_annual(files, polys, "cd_mun", pop, tmp / "o", population_year=2021, code_dir=tmp,
               trend_windows={"w1": (2012, 2016), "w2": (2012, 2021)}, min_years=5,
               extra_cols=("nome",))
    tr = pd.read_csv(tmp / "o" / "trends_main.csv")
    assert set(tr.window) == {"w1", "w2"} and set(tr.nome) == {"Alfa", "Beta"}
    a1 = tr[(tr.cd_mun == "A") & (tr.window == "w1")].iloc[0]
    assert a1.n_years == 5 and a1.change_abs == pytest.approx(4.0)
    # unidade por habitante: mW/sr/hab = (nW/sr * 1e-6) / hab
    ann = pd.read_csv(tmp / "o" / "annual_main.csv")
    s = ann[(ann.cd_mun == "A") & (ann.year == 2021)].apparent_radiant_intensity_nw_sr.iloc[0]
    a2 = tr[(tr.cd_mun == "A") & (tr.window == "w2")].iloc[0]
    assert a2.intensity_per_capita_mw_sr_hab == pytest.approx(s * 1e-6 / 1000, rel=1e-6)


def test_qa_controls_are_written_and_flag_background_rise(tmp_path):
    files = {}
    for i, year in enumerate(range(2012, 2018)):
        p = tmp_path / f"y{year}.h5"
        # fundo escuro (0) ate 2014; a partir de 2015 surge ruido de 0.8 num canto
        make_h5(p, lambda r, c, y=year: np.where((r > 30) & (c > 30) & (y >= 2015), 0.8, 0.0))
        files[year] = p
    res = 15 / 3600
    polys = gpd.GeoDataFrame({"cd_mun": ["A"]}, geometry=[box(-50, -20 - 40 * res, -50 + 40 * res, -20)],
                             crs="EPSG:4326")
    run_annual(files, polys, "cd_mun", None, tmp_path / "o", min_years=3, code_dir=tmp_path,
               qa_baseline_years=(2012, 2013, 2014))
    qa = pd.read_csv(tmp_path / "o" / "qa_background_controls.csv").set_index("year")
    assert qa.loc[2014, "dark_land_mean"] == 0.0
    assert qa.loc[2016, "dark_land_mean"] > 0.0
    assert qa.loc[2016, "dark_land_frac_positive"] == pytest.approx(81 / 1600, rel=0.2)


def test_compare_sensors_detects_same_trend_and_ratio(setup):
    from openlux.pipeline import compare_sensors
    files, polys, pop, tmp = setup
    other = {}
    for i, year in enumerate(range(2012, 2022)):
        p = tmp / f"n{year}.h5"
        make_h5(p, lambda r, c, i=i: np.where(c < 20, 2 * (5.0 + i), 2.0))  # sensor B = 2x sensor A
        other[year] = p
    r = compare_sensors(files, other, polys, "cd_mun", min_years=5)
    assert r["years"] == list(range(2012, 2022))
    assert all(v == pytest.approx(2.0) for v in r["ratio_b_over_a"].values())
    assert all(v == pytest.approx(1.0) for v in r["state_lit_fraction_a"].values())
    assert all(v == pytest.approx(1.0) for v in r["state_lit_fraction_b"].values())
    assert r["trend_sign_agreement"] == pytest.approx(1.0)


def test_lit_fraction_and_analytic_thresholds(setup):
    files, polys, pop, tmp = setup
    rec = run_annual(files, polys, "cd_mun", pop, tmp / "o", population_year=2021, code_dir=tmp)
    ann = pd.read_csv(tmp / "o" / "annual_main.csv")
    # todos os pixels de A (5+i) e de B (1.0) estao >= 0,5: fracao 1,0 em todos os anos
    assert (ann["frac_above_lit_0p5"] == 1.0).all()
    thr = rec["parameters"]["thresholds_nw_cm2_sr"]
    assert thr["lit_0p5"] == 0.5 and "q50_ref" in thr and "q90_ref" in thr
    # janela = caixa dos poligonos (colunas 0-34): 20 colunas valem 5.0 e 15 valem 1.0 -> q50 = 5.0
    assert thr["q50_ref"] == pytest.approx(5.0)
    a12 = ann[(ann.cd_mun == "A") & (ann.year == 2012)].iloc[0]
    b12 = ann[(ann.cd_mun == "B") & (ann.year == 2012)].iloc[0]
    assert a12["frac_above_q50_ref"] == 1.0 and b12["frac_above_q50_ref"] == 0.0
    assert rec["parameters"]["threshold_reference_year"] == 2012


def test_analytic_thresholds_skipped_when_reference_year_has_no_lit_pixels(tmp_path):
    files = {}
    for year in range(2012, 2015):
        p = tmp_path / f"y{year}.h5"
        make_h5(p, lambda r, c: np.zeros_like(r))
        files[year] = p
    res = 15 / 3600
    polys = gpd.GeoDataFrame({"cd_mun": ["A"]}, geometry=[box(-50, -20 - 10 * res, -50 + 10 * res, -20)],
                             crs="EPSG:4326")
    rec = run_annual(files, polys, "cd_mun", None, tmp_path / "o", min_years=3, code_dir=tmp_path)
    assert list(rec["parameters"]["thresholds_nw_cm2_sr"]) == ["lit_0p5"]
    ann = pd.read_csv(tmp_path / "o" / "annual_main.csv")
    assert (ann["frac_above_lit_0p5"] == 0.0).all()
