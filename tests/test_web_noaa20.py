"""indicators_noaa20.json: recalculo com o NOAA-20 (VJ146A4, 2018-2025), separado do S-NPP."""
import json
from pathlib import Path

from helpers import WEB

NOA = json.loads((WEB / "data" / "indicators_noaa20.json").read_text(encoding="utf-8"))
SNPP = json.loads((WEB / "data" / "indicators.json").read_text(encoding="utf-8"))


def test_noaa20_file_covers_the_92_municipalities_and_its_own_period():
    assert len(NOA["municipios"]) == 92
    assert NOA["meta"]["years"] == list(range(2018, 2026))
    assert "NOAA-20" in NOA["meta"]["sensor"]


def test_noaa20_population_weighted_values_are_complete_for_all_municipalities():
    faltam = [m["name"] for m in NOA["municipios"].values() if all(v is None for v in m["exposure"]["pop_radiance"])]
    assert faltam == []


def test_noaa20_and_snpp_agree_in_level_before_2022_as_documented():
    """docs/DECISIONS.md §8: razao mediana NOAA-20/S-NPP entre 0,98 e 1,01 ate 2021."""
    import statistics
    rat = []
    for cd, m in NOA["municipios"].items():
        sm = SNPP["municipios"][cd]
        for i, y in enumerate(NOA["meta"]["years"]):
            if y <= 2021:
                j = SNPP["meta"]["years"].index(y)
                a, b = m["mean"][i], sm["mean"][j]
                if a and b:
                    rat.append(a / b)
    assert 0.97 <= statistics.median(rat) <= 1.02


def test_noaa20_file_is_not_the_snpp_file():
    assert NOA["municipios"]["3304557"]["mean"][-1] != SNPP["municipios"]["3304557"]["mean"][-1]
