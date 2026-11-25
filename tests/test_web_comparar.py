"""Lente de comparação entre dois anos (Fase D): contrato, conferência independente e navegador."""
import json
import os
import re
import threading
from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

import pytest

from helpers import WEB

HTML = (WEB / "comparar.html").read_text(encoding="utf-8")
JS = (WEB / "js" / "comparar.js").read_text(encoding="utf-8")
NOA = json.loads((WEB / "data" / "indicators_noaa20.json").read_text(encoding="utf-8"))


def test_compare_page_loads_shared_map_module_and_no_inline_script():
    assert 'src="js/mapa-svg.js"' in HTML and 'src="js/comparar.js"' in HTML
    assert "<script>" not in HTML
    assert set(re.findall(r"getJSON\('([^']+)'\)", JS)) == {
        "data/indicators_noaa20.json", "data/indicators.json", "data/municipios.geojson"}
    assert not re.search(r"\b6[.,]336\b|\b5[.,]520\b", JS)           # nenhum número digitado


def test_default_pair_matches_an_independent_recomputation():
    yrs = NOA["meta"]["years"]
    iA, iB = yrs.index(2018), yrs.index(2025)
    pares = [(v["mean"][iA], v["mean"][iB]) for v in NOA["municipios"].values()]
    pares = [(a, b) for a, b in pares if a is not None and b is not None]
    mA = sum(a for a, _ in pares) / len(pares)
    mB = sum(b for _, b in pares) / len(pares)
    assert len(pares) == 92
    assert f"{mA:.3f}".replace(".", ",") == "5,520"
    assert f"{mB:.3f}".replace(".", ",") == "6,336"
    assert f"{mB - mA:+.3f}".replace(".", ",") == "+0,815"
    assert f"{100 * (mB / mA - 1):+.1f}".replace(".", ",") == "+14,8"


@pytest.fixture(scope="module")
def site():
    handler = partial(SimpleHTTPRequestHandler, directory=str(WEB))
    handler.log_message = lambda *a, **k: None
    srv = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()


def test_rendered_comparison_has_three_maps_and_updates_the_url(site):
    playwright = pytest.importorskip("playwright.sync_api")
    with playwright.sync_playwright() as p:
        exe = os.environ.get("OPENLUX_CHROMIUM")
        b = p.chromium.launch(executable_path=exe) if exe else p.chromium.launch()
        for vp in ({"width": 1280, "height": 900}, {"width": 390, "height": 844}):
            pg = b.new_context(viewport=vp).new_page()
            erros = []
            pg.on("console", lambda m: erros.append(m.text) if m.type == "error" else None)
            pg.on("pageerror", lambda e: erros.append(str(e)))
            pg.goto(site + "/comparar.html")
            pg.wait_for_selector("#mapa-dif a path", timeout=20000)
            assert pg.locator("#mapa-a a path").count() == 92
            assert pg.locator("#mapa-b a path").count() == 92
            assert pg.locator("#mapa-dif a path").count() == 92
            assert pg.inner_text("#k-a").startswith("5,520") and pg.inner_text("#k-b").startswith("6,336")
            assert pg.inner_text("#k-pct").startswith("+14,8")
            pg.select_option("#ano-b", "2024")
            pg.wait_for_function("() => location.search.includes('b=2024')")
            assert pg.inner_text("#k-b").startswith("5,865")       # 2024 do NOAA-20 (valor publicado)
            assert pg.evaluate("() => document.documentElement.scrollWidth") <= vp["width"]
            assert erros == []
            pg.context.close()
        b.close()
