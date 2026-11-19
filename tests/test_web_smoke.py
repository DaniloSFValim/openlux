"""Teste de fumaca da interface em navegador real. Exige playwright e web/data gerado."""
import http.server
import json
import socketserver
import threading
from pathlib import Path

import numpy as np
import pytest

playwright = pytest.importorskip("playwright.sync_api")
WEB = Path(__file__).resolve().parent.parent / "web"
if not (WEB / "data" / "indicators.json").exists():
    pytest.skip("web/data ausente (rode scripts/build_web_data.py)", allow_module_level=True)

SEQ = ["#ffffb2", "#fecc5c", "#fd8d3c", "#f03b20", "#bd0026"]


@pytest.fixture(scope="module")
def server():
    class H(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **k):
            super().__init__(*a, directory=str(WEB), **k)

        def log_message(self, *a):
            pass
    httpd = socketserver.TCPServer(("127.0.0.1", 0), H)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()


@pytest.fixture(scope="module")
def page(server):
    with playwright.sync_playwright() as p:
        import os  # OPENLUX_CHROMIUM: caminho de um Chromium ja instalado (opcional)
        exe = os.environ.get("OPENLUX_CHROMIUM")
        b = p.chromium.launch(executable_path=exe) if exe else p.chromium.launch()
        pg = b.new_page(viewport={"width": 1280, "height": 900})
        pg.errors = []
        pg.on("console", lambda m: pg.errors.append(m.text) if m.type == "error" else None)
        pg.on("pageerror", lambda e: pg.errors.append(str(e)))
        pg.goto(server)
        pg.wait_for_selector("#mapa path.leaflet-interactive")
        yield pg
        b.close()


def _expected_color(data, cd, year_index):
    """Reimplementa a classificacao em Python (independente do JS)."""
    pooled = [v for m in data["municipios"].values() for v in m["mean"] if v is not None]
    br = [float(f"{np.quantile(pooled, p):.3g}") for p in (0.2, 0.4, 0.6, 0.8)]
    v = data["municipios"][cd]["mean"][year_index]
    return SEQ[sum(v >= b for b in br)], v


def test_renders_92_municipalities_without_errors(page):
    assert page.locator("#mapa path.leaflet-interactive").count() == 92
    assert page.errors == []


def test_rendered_colors_match_independent_classification(page):
    data = json.loads((WEB / "data" / "indicators.json").read_text())
    last = len(data["meta"]["years"]) - 1
    by_name = {m["name"]: cd for cd, m in data["municipios"].items()}
    for name in ("Niterói", "Rio de Janeiro", "Arraial do Cabo", "Itatiaia"):
        cd = by_name[name]
        color, v = _expected_color(data, cd, last)
        page.select_option("#mun-select", cd)
        # cor lida do desenho: o path do municipio selecionado tem contorno azul; lemos o fill
        fill = page.evaluate("""() => { const ps=[...document.querySelectorAll('#mapa path.leaflet-interactive')];
            const sel = ps.find(p => p.getAttribute('stroke') === '#0b5fff'); return sel ? sel.getAttribute('fill') : null; }""")
        assert fill is not None and fill.lower() == color, (name, fill, color, v)


def test_legend_has_units_source_period_and_nodata(page):
    txt = page.inner_text("#legend")
    assert "Unidade:" in txt and "nW·cm⁻²·sr⁻¹" in txt and "Fonte:" in txt and "Período:" in txt
    assert "sem dado" in txt and "classificação analítica" in txt.lower()


def test_alert_banner_is_data_driven_and_visible(page):
    page.click("#alert summary")
    t = page.inner_text("#alert")
    assert "não validados" in t.lower() and "piso de ruído" in t
    assert "pixels persistentemente escuros" in t  # detalhe com numeros vindos dos dados
    assert "Carregando" not in t


def test_no_demo_values_and_expression_present(page):
    body = page.inner_text("body")
    assert "estimativa baseada em sensoriamento remoto" in body.lower()
    assert "não medições do brilho do céu" in body.lower()
    assert "lorem" not in body.lower()


def test_indicator_switch_updates_legend_and_hides_year(page):
    page.select_option("#indicator", "percap")
    assert "mW·sr⁻¹ por habitante" in page.inner_text("#legend")
    assert page.locator("#year-wrap").is_hidden()
    page.select_option("#indicator", "slope_2012_2021")
    assert "p < 0,05" in page.inner_text("#legend")
    page.select_option("#indicator", "mean")
    assert page.locator("#year-wrap").is_visible()


def test_niteroi_case_button_shows_detail_and_chart(page):
    page.click("#tab-mun")
    page.click("#case-btn")
    assert "Niterói" in page.inner_text("#mun-detail")
    assert page.locator("#mun-chart svg.chart").count() == 1
    assert page.errors == []
