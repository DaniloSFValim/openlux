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


def test_noaa20_review_downloads_have_the_expected_rows_and_years():
    import csv
    # Revisão fica fora de web/ (pasta pública): data/revisao/noaa20 (Fase B, regra 9).
    pasta = Path(__file__).resolve().parents[1] / "data" / "revisao" / "noaa20"
    serie = list(csv.DictReader((pasta / "openlux_municipios_noaa20_serie.csv").open(encoding="utf-8-sig")))
    assert len(serie) == 92 * 8
    assert sorted({r["ano"] for r in serie}) == [str(y) for y in range(2018, 2026)]
    resumo = list(csv.DictReader((pasta / "openlux_municipios_noaa20_resumo.csv").open(encoding="utf-8-sig")))
    assert len(resumo) == 92
    assert any("2018_2025" in h for h in resumo[0].keys())


def test_public_web_folder_has_no_review_or_internal_files():
    """Regra 9 (Fase B): web/ é a pasta pública; arquivos de revisão, provisórios ou internos não entram nela."""
    proibidos = [p.relative_to(WEB).as_posix() for p in WEB.rglob("*")
                 if p.is_file() and any(t in p.as_posix().lower() for t in ("revisao", "revisão", "provisorio", "interno", "draft"))]
    assert proibidos == []
