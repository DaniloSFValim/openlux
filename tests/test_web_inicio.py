"""Página inicial "Quanta luz tem o seu município?": conteúdo, restrições científicas e cálculos de apoio."""
import json
import re
from pathlib import Path

from helpers import WEB

HTML = (WEB / "index.html").read_text(encoding="utf-8")
JS = (WEB / "js" / "inicio.js").read_text(encoding="utf-8")
DATA = json.loads((WEB / "data" / "indicators.json").read_text(encoding="utf-8"))


def test_front_page_loads_the_municipality_picker_and_the_scripts():
    assert 'id="mun-escolha"' in HTML
    assert 'src="js/inicio.js"' in HTML and 'src="js/charts.js"' in HTML


def test_front_page_never_claims_bortle_or_sky_quality():
    """O projeto não valida escala de céu: a página inicial não pode sugerir isso."""
    texto = HTML.lower()
    # "qualidade do céu" aparece só numa negação ("não é ... qualidade do céu"), por isso não é banido aqui.
    for termo in ("bortle", "sqm", "estrelas visíveis"):
        assert termo not in texto, termo


def test_front_page_states_it_is_an_estimate_from_remote_sensing():
    assert "estimativa de poluição luminosa baseada em sensoriamento remoto" in HTML.lower()


def test_reference_year_is_before_the_snpp_noise_and_present_in_the_data():
    m = re.search(r"const REF = (\d{4});", JS)
    assert m, "ano de referência ausente em inicio.js"
    ano = int(m.group(1))
    assert ano == 2021 and ano in DATA["meta"]["years"]


def test_population_weighted_indicator_is_used_and_not_the_saturated_lit_share():
    assert "pop_radiance" in JS
    assert "pop_lit" not in JS


def test_every_municipality_has_a_population_weighted_value_for_the_reference_year():
    ref = DATA["meta"]["years"].index(2021)
    faltam = [m["name"] for m in DATA["municipios"].values() if m["exposure"]["pop_radiance"][ref] is None]
    assert faltam == [], faltam


def test_front_page_links_to_the_explorer_and_the_other_pages():
    for alvo in ("explorar.html", "roteiros.html", "dados.html", "sobre.html"):
        assert f'href="{alvo}"' in HTML, alvo


def test_ranking_strip_is_in_the_front_page_and_drawn_by_the_script():
    assert 'id="faixa-ranking"' in HTML and 'id="ranking-resumo"' in HTML
    assert "function drawRanking" in JS
    assert "drawRanking(cod)" in JS  # redesenha ao trocar de município


def test_every_page_that_uses_reveal_loads_the_reveal_script():
    """Sem reveal.js, o conteúdo com a classe reveal fica invisível (opacidade 0)."""
    for pagina in sorted(WEB.glob("*.html")):
        texto = pagina.read_text(encoding="utf-8")
        if 'class="' in texto and "reveal" in texto:
            assert 'src="js/reveal.js"' in texto, pagina.name
