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
    """Arquivos de web/data/pixels: tamanho = linhas x colunas, hash igual ao do meta.json, so codigos validos."""
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
    assert len(meta["years"]) == 14 and {int(y) for y in meta["years"]} == set(range(2012, 2026))
    for y, e in meta["years"].items():
        raw = (d / f"{y}.bin").read_bytes()
        assert len(raw) == g["rows"] * g["cols"] and hashlib.sha256(raw).hexdigest() == e["sha256"]
        a = np.frombuffer(raw, dtype="uint8")
        assert a.max() <= FIRST_RADIANCE_CODE + len(BREAKS)
    outside = [int((np.frombuffer((d / f"{y}.bin").read_bytes(), dtype="uint8") == 0).sum()) for y in meta["years"]]
    assert len(set(outside)) == 1          # a mascara do estado e a mesma em todos os anos
