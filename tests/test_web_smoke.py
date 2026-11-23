"""Teste de fumaca da interface em navegador real. Exige playwright e web/data gerado.

Por padrao serve ``web/`` localmente, aplicando o arquivo ``web/_headers`` (inclusive a politica de
seguranca de conteudo, entao violacoes aparecem como erros de console). Para testar uma
implantacao existente:

    OPENLUX_URL=https://openlux.labdados.org python -m pytest tests/test_web_smoke.py

Com ``OPENLUX_URL`` tambem se confere que os arquivos publicados sao identicos aos do repositorio.
Se o Chromium do Playwright nao estiver instalado, use ``OPENLUX_CHROMIUM`` com o caminho de um.
"""
import hashlib
import http.server
import json
import os
import socketserver
import threading
import urllib.request
from pathlib import Path

import numpy as np
import pytest
from helpers import WEB, has_cloudflare_injection, headers_for, parse_headers_file, strip_cloudflare_injections

playwright = pytest.importorskip("playwright.sync_api")
REMOTE = (os.environ.get("OPENLUX_URL") or "").rstrip("/")
if not (WEB / "data" / "indicators.json").exists():
    pytest.skip("web/data ausente (rode scripts/build_web_data.py)", allow_module_level=True)

SEQ = ["#ffffb2", "#fecc5c", "#fd8d3c", "#f03b20", "#bd0026"]
RULES = parse_headers_file((WEB / "_headers").read_text(encoding="utf-8"))
UA = {"User-Agent": "Mozilla/5.0 (openlux-smoke-test)"}


def _fetch(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
        return r.read(), dict(r.headers)


@pytest.fixture(scope="module")
def server():
    if REMOTE:
        yield REMOTE
        return

    class H(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **k):
            super().__init__(*a, directory=str(WEB), **k)

        def end_headers(self):  # aplica web/_headers como a Cloudflare faria
            for k, v in headers_for(self.path.split("?")[0], RULES).items():
                self.send_header(k, v)
            super().end_headers()

        def log_message(self, *a):
            pass
    httpd = socketserver.TCPServer(("127.0.0.1", 0), H)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()


def _cloudflare_injected(html: str) -> bool:
    return has_cloudflare_injection(html)


def _is_cloudflare_csp_noise(msg: str) -> bool:
    """Aviso de CSP causado SO pelas injecoes da Cloudflare: script inline de deteccao de bots
    ("... inline script ...") ou beacon do Web Analytics ("... cloudflareinsights ...")."""
    return "Content Security Policy" in msg and ("inline script" in msg or "cloudflareinsights" in msg)


def _relevant_errors(errors, injected: bool):
    """Em dominios com o proxy da Cloudflare, ignora apenas o aviso de CSP acima; qualquer outro
    erro de console continua sendo falha."""
    if not injected:
        return list(errors)
    return [e for e in errors if not _is_cloudflare_csp_noise(e)]


@pytest.fixture(scope="module")
def page(server):
    with playwright.sync_playwright() as p:
        exe = os.environ.get("OPENLUX_CHROMIUM")
        b = p.chromium.launch(executable_path=exe) if exe else p.chromium.launch()
        pg = b.new_page(viewport={"width": 1280, "height": 900})
        pg.errors = []
        pg.on("console", lambda m: pg.errors.append(m.text) if m.type == "error" else None)
        pg.on("pageerror", lambda e: pg.errors.append(str(e)))
        pg.goto(server)
        pg.wait_for_selector("#mapa path.leaflet-interactive")
        pg.injected = _cloudflare_injected(pg.content())
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
    assert _relevant_errors(page.errors, page.injected) == []


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


def test_lit_fraction_indicator_is_available_and_documented(page):
    page.select_option("#indicator", "lit")
    txt = page.inner_text("#legend")
    assert "Fração da área" in txt and "≥" in txt and "piso de ruído" in txt
    assert "fração da área válida" in txt
    page.select_option("#indicator", "mean")


def test_sensor_comparison_indicators_and_panels(page):
    page.select_option("#indicator", "slope_noaa20_1825")
    leg = page.inner_text("#legend")
    assert "NOAA-20" in leg and "2018–2025" in leg and "p < 0,05" in leg
    page.select_option("#indicator", "slope_snpp_1825")
    assert "S-NPP" in page.inner_text("#legend")
    page.select_option("#indicator", "mean")
    page.click("#case-btn")
    detail = page.inner_text("#mun-detail")
    assert "Comparação entre sensores, 2018–2025" in detail and "NOAA-20" in detail
    page.click("#tab-state")
    assert "Comparação municipal entre sensores" in page.inner_text("#state-content")
    page.click("#tab-mun")


def test_niteroi_case_button_shows_detail_and_chart(page):
    page.click("#tab-mun")
    page.click("#case-btn")
    assert "Niterói" in page.inner_text("#mun-detail")
    assert page.locator("#mun-chart svg.chart").count() == 1
    assert _relevant_errors(page.errors, page.injected) == []


def test_security_headers_are_served(server):
    """Confere os cabecalhos de seguranca do arquivo web/_headers na resposta real."""
    _, h = _fetch(server + "/")
    low = {k.lower(): v for k, v in h.items()}
    expected = headers_for("/index.html", RULES)
    for name, value in expected.items():
        assert low.get(name.lower()) == value, f"{name} ausente ou diferente na implantacao"
    _, d = _fetch(server + "/data/indicators.json")
    assert {k.lower(): v for k, v in d.items()}.get("cache-control") == "public, max-age=300"


@pytest.mark.skipif(not REMOTE, reason="defina OPENLUX_URL para comparar a implantacao com o repositorio")
def test_deployed_files_are_identical_to_the_repository(server):
    mismatches = []
    for f in sorted(p for p in WEB.rglob("*") if p.is_file() and p.name != "_headers"):
        rel = f.relative_to(WEB).as_posix()
        body, _ = _fetch(f"{server}/{rel}")
        if rel == "index.html":  # remove so os trechos conhecidos que a Cloudflare injeta
            body = strip_cloudflare_injections(body.decode("utf-8")).encode("utf-8")
        if hashlib.sha256(body).digest() != hashlib.sha256(f.read_bytes()).digest():
            mismatches.append(rel)
    assert mismatches == []
