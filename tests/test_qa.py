"""Controles de ruido de fundo. Arrays SINTETICOS (apenas para teste)."""
import numpy as np
import pytest

from openlux.qa import background_controls


def test_dark_pixels_are_defined_by_baseline_median_only():
    z = np.zeros((4, 4), dtype="float32")
    base = {2018: z.copy(), 2019: z.copy(), 2020: z.copy()}
    base[2018][0, 0] = base[2019][0, 0] = base[2020][0, 0] = 50.0  # pixel sempre aceso: nao e escuro
    late = z.copy()
    late[0, 0] = 80.0       # pixel aceso (fora da classe escura)
    late[3, 3] = 0.8        # pixel escuro com ruido novo
    arrays = {**base, 2022: late}
    land = np.ones((4, 4), bool)
    sea = np.zeros((4, 4), bool)
    df = background_controls(arrays, land, sea, baseline_years=(2018, 2019, 2020))
    r22 = df[df.year == 2022].iloc[0]
    assert r22.n_dark_land == 15
    assert r22.dark_land_mean == pytest.approx(0.8 / 15)
    assert r22.dark_land_frac_positive == pytest.approx(1 / 15)
    assert df[df.year == 2019].iloc[0].dark_land_mean == 0.0


def test_sea_control_reported_separately_and_nan_when_empty():
    arr = {2018: np.zeros((2, 2), "float32"), 2019: np.full((2, 2), 0.3, "float32")}
    land = np.array([[True, True], [False, False]])
    sea = np.array([[False, False], [True, True]])
    df = background_controls(arr, land, sea, baseline_years=(2018,))
    assert df[df.year == 2019].iloc[0].dark_sea_mean == pytest.approx(0.3)
    assert df[df.year == 2019].iloc[0].n_dark_sea == 2
    empty = background_controls(arr, land, np.zeros((2, 2), bool), baseline_years=(2018,))
    assert np.isnan(empty.iloc[0].dark_sea_mean) and empty.iloc[0].n_dark_sea == 0


def test_nan_pixels_are_ignored():
    a = np.zeros((2, 2), "float32")
    b = a.copy()
    b[0, 0] = np.nan
    df = background_controls({2018: a, 2019: b}, np.ones((2, 2), bool), np.zeros((2, 2), bool),
                             baseline_years=(2018,))
    r = df[df.year == 2019].iloc[0]
    assert r.dark_land_mean == 0.0 and r.n_dark_land == 4  # classe definida na linha de base


def test_dark_class_masks_and_controls_for_match_background_controls():
    from openlux.qa import controls_for, dark_class_masks
    z = np.zeros((4, 4), dtype="float32")
    base = [z.copy(), z.copy(), z.copy()]
    for b in base:
        b[0, 0] = 50.0                                   # sempre aceso: fora da classe escura
    late = z.copy()
    late[0, 0] = 80.0
    late[3, 3] = 0.8
    land = np.ones((4, 4), bool)
    sea = np.zeros((4, 4), bool)
    masks = dark_class_masks(base, land, sea)
    assert masks["land"].sum() == 15 and masks["sea"].sum() == 0
    got = controls_for(late, masks)
    ref = background_controls({2018: base[0], 2019: base[1], 2020: base[2], 2022: late}, land, sea,
                              baseline_years=(2018, 2019, 2020))
    ref = ref[ref.year == 2022].iloc[0]
    assert got["dark_land_mean"] == pytest.approx(ref.dark_land_mean)
    assert got["dark_land_frac_positive"] == pytest.approx(ref.dark_land_frac_positive)
    assert got["n_dark_land"] == ref.n_dark_land and np.isnan(got["dark_sea_mean"])
