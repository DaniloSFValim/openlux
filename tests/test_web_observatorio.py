"""Observatório (página inicial, Fase D): contrato da página e números conferidos de forma independente."""
import json
import re
import threading
from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

import pytest

from helpers import WEB

HTML = (WEB / "index.html").read_text(encoding="utf-8")
JS = (WEB / "js" / "observatorio.js").read_text(encoding="utf-8")
NOA = json.loads((WEB / "data" / "indicators_noaa20.json").read_text(encoding="utf-8"))


def test_front_page_states_the_official_terminology_and_the_six_areas():
    assert "estimativa de poluição luminosa baseada em sensoriamento remoto" in HTML.lower()
    for area in ("Observatório", "Explorador", "Roteiros", "Dados abertos", "Metodologia"):
        assert area in HTML
    assert 'src="js/observatorio.js"' in HTML and "<script>" not in HTML   # sem script inline (CSP)


def test_script_reads_only_published_files_and_has_no_typed_numbers():
    urls = re.findall(r"getJSON\('([^']+)'\)", JS)
    assert urls == ["data/indicators_noaa20.json", "data/indicators.json", "data/municipios.geojson"]
    # nenhum número digitado no script: os valores vêm dos arquivos publicados
    assert not re.search(r"\b6[.,]3\d{2}\b", JS)


def test_state_kpis_match_an_independent_recomputation():
    yrs = NOA["meta"]["years"]
    i25, i18 = yrs.index(2025), yrs.index(2018)
    m25 = [v["mean"][i25] for v in NOA["municipios"].values() if v["mean"][i25] is not None]
    m18 = [v["mean"][i18] for v in NOA["municipios"].values() if v["mean"][i18] is not None]
    media25 = sum(m25) / len(m25)
    var = 100 * (media25 / (sum(m18) / len(m18)) - 1)
    assert len(NOA["municipios"]) == 92 and len(m25) == 92
    assert f"{media25:.3f}".replace(".", ",") == "6,336"          # o mesmo número que a página mostra
    assert f"{var:+.1f}".replace(".", ",") == "+14,8"


@pytest.fixture(scope="module")
def site():
    handler = partial(SimpleHTTPRequestHandler, directory=str(WEB))
    handler.log_message = lambda *a, **k: None
    srv = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()


def test_rendered_page_shows_92_municipalities_and_no_console_errors(site):
    playwright = pytest.importorskip("playwright.sync_api")
    import os
    with playwright.sync_playwright() as p:
        exe = os.environ.get("OPENLUX_CHROMIUM")
        b = p.chromium.launch(executable_path=exe) if exe else p.chromium.launch()
        for vp in ({"width": 1280, "height": 900}, {"width": 390, "height": 844}):
            pg = b.new_context(viewport=vp).new_page()
            erros = []
            pg.on("console", lambda m: erros.append(m.text) if m.type == "error" else None)
            pg.on("pageerror", lambda e: erros.append(str(e)))
            pg.goto(site + "/index.html")
            pg.wait_for_selector("#mapa-destaque a path", timeout=20000)
            assert pg.locator("#mapa-destaque a path").count() == 92
            assert pg.inner_text("#k-mun") == "92"
            assert pg.inner_text("#k-media").startswith("6,336")
            assert pg.locator("#ranking-maiores li").count() == 10 and pg.locator("#ranking-menores li").count() == 10
            assert pg.evaluate("() => document.documentElement.scrollWidth") <= vp["width"]   # sem rolagem horizontal
            assert erros == []
            pg.context.close()
        b.close()
