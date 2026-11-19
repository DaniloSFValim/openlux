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
    assert sens["near_nadir"]["trend_sign_agreement"] == pytest.approx(1.0)
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
