"""Laboratório de análises (Fase D): contrato, conferência independente e navegador."""
import json
import os
import re
import threading
from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

import pytest

from helpers import WEB

HTML = (WEB / "laboratorio.html").read_text(encoding="utf-8")
JS = (WEB / "js" / "laboratorio.js").read_text(encoding="utf-8")
NOA = json.loads((WEB / "data" / "indicators_noaa20.json").read_text(encoding="utf-8"))


def test_lab_page_loads_shared_chart_module_and_no_inline_script():
    assert 'src="js/graficos-svg.js"' in HTML and 'src="js/laboratorio.js"' in HTML
    assert "<script>" not in HTML
    assert set(re.findall(r"getJSON\('([^']+)'\)", JS)) == {"data/indicators_noaa20.json", "data/indicators.json"}


def test_trend_counts_and_rank_match_an_independent_recomputation():
    tr = [v["trends"]["2018_2025"] for v in NOA["municipios"].values()]
    sig = [t for t in tr if t["p_value"] is not None and t["p_value"] < 0.05]
    assert len(sig) == 53
    assert sum(1 for t in sig if t["slope"] > 0) == 52
    assert [v["name"] for v in NOA["municipios"].values() if v["trends"]["2018_2025"]["slope"] < 0 and v["trends"]["2018_2025"]["p_value"] < 0.05] == ["Belford Roxo"]
    j = NOA["meta"]["years"].index(2025)
    ordem = sorted(NOA["municipios"].items(), key=lambda kv: -kv[1]["mean"][j])
    rio = [i for i, (cd, _) in enumerate(ordem) if cd == "3304557"][0] + 1
    assert rio == 3 and len(ordem) == 92


@pytest.fixture(scope="module")
def site():
    handler = partial(SimpleHTTPRequestHandler, directory=str(WEB))
    handler.log_message = lambda *a, **k: None
    srv = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()


def test_rendered_lab_shows_comparison_trends_and_url(site):
    playwright = pytest.importorskip("playwright.sync_api")
    with playwright.sync_playwright() as p:
        exe = os.environ.get("OPENLUX_CHROMIUM")
        b = p.chromium.launch(executable_path=exe) if exe else p.chromium.launch()
        for vp in ({"width": 1280, "height": 900}, {"width": 390, "height": 844}):
            pg = b.new_context(viewport=vp).new_page()
            erros = []
            pg.on("console", lambda m: erros.append(m.text) if m.type == "error" else None)
            pg.on("pageerror", lambda e: erros.append(str(e)))
            pg.goto(site + "/laboratorio.html")
            pg.wait_for_selector("#tabela-comp table", timeout=20000)
            pg.select_option("#mun-2", label="Angra dos Reis")
            pg.wait_for_function("() => location.search.includes('Angra') === false && location.search.split('m=')[1].split(',').length === 2")
            assert pg.locator("#tabela-comp tbody tr").count() == 3                       # 2 municípios + estado
            assert pg.inner_text("#tend-resumo").startswith("53 de 92")
            assert pg.locator("#tend-subidas li").count() == 10
            assert pg.evaluate("() => document.documentElement.scrollWidth") <= vp["width"]
            assert erros == []
            pg.context.close()
        b.close()
