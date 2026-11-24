"""Camada de pixel da interface: classes fixas e mascara do estado (dados SINTETICOS)."""
import numpy as np
from rasterio.transform import from_origin
from shapely.geometry import box

from openlux.pixelmap import BREAKS, CODE_INSIDE_NODATA, CODE_OUTSIDE, FIRST_RADIANCE_CODE, radiance_classes, state_mask


def test_classes_are_closed_on_the_left_and_codes_are_distinct():
    rad = np.array([[0.0, 0.49, 0.5, 1.99], [2.0, 7.99, 8.0, 29.9], [30.0, 99.9, 100.0, 5000.0]])
    inside = np.ones(rad.shape, bool)
    c = radiance_classes(rad, inside)
    k = FIRST_RADIANCE_CODE
    assert c.dtype == np.uint8
    assert c.tolist() == [[k, k, k + 1, k + 1], [k + 2, k + 2, k + 3, k + 3], [k + 4, k + 4, k + 5, k + 5]]
    assert BREAKS == [0.5, 2.0, 8.0, 30.0, 100.0] and k == 2   # 0 fora do estado, 1 sem dado


def test_nodata_and_outside_are_not_painted_as_dark():
    rad = np.array([[np.nan, 0.0, 3.0, np.nan]])
    inside = np.array([[True, True, False, False]])
    c = radiance_classes(rad, inside)
    assert c.tolist() == [[CODE_INSIDE_NODATA, FIRST_RADIANCE_CODE, CODE_OUTSIDE, CODE_OUTSIDE]]
    assert CODE_INSIDE_NODATA != FIRST_RADIANCE_CODE != CODE_OUTSIDE


def test_state_mask_marks_pixels_touched_by_polygon():
    t = from_origin(0.0, 3.0, 1.0, 1.0)                   # 3x3, pixels de 1 grau
    m = state_mask([box(0.2, 1.2, 1.8, 2.8)], (3, 3), t)   # cobre linhas 0-1, colunas 0-1
    assert m.tolist() == [[True, True, False], [True, True, False], [False, False, False]]


def test_published_pixel_grids_match_their_metadata():
    """web/data/pixels/<sensor>/: tamanho = linhas x colunas, hash igual ao do meta.json, so codigos validos, mascara
    do estado igual em todos os arquivos e contagens da mudanca iguais as da grade."""
    import hashlib
    import json
    from pathlib import Path
    d = Path(__file__).resolve().parents[1] / "web" / "data" / "pixels"
    if not (d / "meta.json").exists():
        import pytest
        pytest.skip("web/data/pixels ausente (rode scripts/build_web_pixels.py)")
    meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
    g = meta["grid"]
    assert meta["classes"]["breaks_nw_cm2_sr"] == BREAKS and len(meta["classes"]["labels"]) == len(BREAKS) + 1
    assert set(meta["sensors"]) == {"snpp", "noaa20"}
    assert {int(y) for y in meta["sensors"]["snpp"]["years"]} == set(range(2012, 2026))
    assert {int(y) for y in meta["sensors"]["noaa20"]["years"]} == set(range(2018, 2026))
    outside = set()
    for sk, sm in meta["sensors"].items():
        for y, e in sm["years"].items():
            raw = (d / sk / f"{y}.bin").read_bytes()
            assert len(raw) == g["rows"] * g["cols"] and hashlib.sha256(raw).hexdigest() == e["sha256"]
            a = np.frombuffer(raw, dtype="uint8")
            assert a.max() <= FIRST_RADIANCE_CODE + len(BREAKS)
            outside.add(int((a == 0).sum()))
        for w, e in sm["change"].items():
            raw = (d / sk / f"change_{w}.bin").read_bytes()
            assert len(raw) == g["rows"] * g["cols"] and hashlib.sha256(raw).hexdigest() == e["sha256"]
            a = np.frombuffer(raw, dtype="uint8")
            assert a.max() <= 4
            outside.add(int((a == 0).sum()))
            for name, code in (("untested", 1), ("not_significant", 2), ("increase", 3), ("decrease", 4)):
                assert e["counts"][name] == int((a == code).sum())
    assert len(outside) == 1                # a mascara do estado e a mesma em todos os arquivos


def test_change_codes_distinguish_untested_insignificant_increase_and_decrease():
    from openlux.pixelmap import (CHANGE_DECREASE, CHANGE_INCREASE, CHANGE_NOT_SIGNIFICANT, CHANGE_UNTESTED,
                                  change_codes)
    label = np.array([[1, -1, 0, 0, 1]], dtype="int8")
    tested = np.array([[True, True, True, False, True]])
    inside = np.array([[True, True, True, True, False]])
    c = change_codes(label, tested, inside)
    assert c.dtype == np.uint8
    assert c.tolist() == [[CHANGE_INCREASE, CHANGE_DECREASE, CHANGE_NOT_SIGNIFICANT, CHANGE_UNTESTED, CODE_OUTSIDE]]
    assert len({CODE_OUTSIDE, CHANGE_UNTESTED, CHANGE_NOT_SIGNIFICANT, CHANGE_INCREASE, CHANGE_DECREASE}) == 5
