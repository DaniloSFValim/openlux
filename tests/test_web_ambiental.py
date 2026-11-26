"""Observatório ambiental (Fase 7): a página lê exatamente os números do JSON gerado pela análise."""
import json
import re

from helpers import WEB

HTML = (WEB / "ambiental.html").read_text(encoding="utf-8")
JS = (WEB / "js" / "ambiental.js").read_text(encoding="utf-8")
DATA = json.loads((WEB / "data" / "ambiental" / "uc_municipios.json").read_text(encoding="utf-8"))


def test_page_states_exploratory_scope_and_no_causal_claim():
    assert "associação espacial exploratória, não uma causa" in HTML
    assert "não controla a urbanização" in HTML
    assert "<script>" not in HTML


def test_json_carries_source_licence_and_method():
    assert "CC BY 4.0" in DATA["fonte_uc"]["licenca"]
    assert "10.5067/VIIRS/VJ146A4.002" in DATA["fonte_radiancia"]["doi"]
    assert "EPSG:6933" in DATA["metodo"]
    assert len(DATA["municipios"]) == 92


def test_displayed_correlation_matches_the_json_and_is_not_presented_as_cause():
    rho = DATA["resumo"]["spearman_fracao_uc_x_radiancia_media"]["rho"]
    assert f"{rho:.2f}".replace(".", ",") == "0,32"
    assert "nota" in DATA["resumo"]["spearman_fracao_uc_x_radiancia_media"]
    assert "causa" not in JS.lower()                        # o script não afirma causalidade


def test_script_reads_only_the_published_json():
    assert re.findall(r"fetch\('([^']+)'\)", JS) == ["data/ambiental/uc_municipios.json"]
