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

import re

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


def _layer(page, value):
    page.check(f'input[name="layer"][value="{value}"]')
    page.wait_for_function("(v) => document.querySelector('input[name=layer]:checked').value === v", arg=value)


def test_renders_92_municipalities_without_errors(page):
    assert page.locator("#mapa path.leaflet-interactive").count() == 92
    assert _relevant_errors(page.errors, page.injected) == []


def test_rendered_colors_match_independent_classification(page):
    data = json.loads((WEB / "data" / "indicators.json").read_text())
    last = len(data["meta"]["years"]) - 1
    by_name = {m["name"]: cd for cd, m in data["municipios"].items()}
    _layer(page, "mun")
    page.select_option("#indicator", "mean")
    for name in ("Campos dos Goytacazes", "Rio de Janeiro", "Arraial do Cabo", "Itatiaia"):
        cd = by_name[name]
        color, v = _expected_color(data, cd, last)
        page.select_option("#mun-select", cd)
        # cor lida do desenho: o path do municipio selecionado tem contorno azul; lemos o fill
        fill = page.evaluate("""() => { const ps=[...document.querySelectorAll('#mapa path.leaflet-interactive')];
            const sel = ps.find(p => p.getAttribute('stroke') === '#0b5fff'); return sel ? sel.getAttribute('fill') : null; }""")
        assert fill is not None and fill.lower() == color, (name, fill, color, v)


def test_legend_has_units_source_period_and_nodata(page):
    _layer(page, "mun")
    page.select_option("#indicator", "mean")
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
    assert "não uma medição do brilho do céu" in body.lower()
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
    page.select_option("#mun-select", next(c for c, m in json.loads((WEB / "data" / "indicators.json").read_text())["municipios"].items() if m["name"] == "Rio de Janeiro"))
    detail = page.inner_text("#mun-detail")
    assert "Comparação entre sensores, 2018–2025" in detail and "NOAA-20" in detail
    page.click("#tab-state")
    assert "Comparação municipal entre sensores" in page.inner_text("#state-content")
    page.click("#tab-mun")


def test_no_city_is_hardcoded_as_the_case_study(page):
    """A interface nao privilegia um municipio: sem botao de estudo de caso e sem Niteroi no texto."""
    assert page.locator("#case-btn").count() == 0
    for sel in (".lede", "header", "#legend", ".controls button"):   # Niteroi segue na lista dos 92 municipios, sem destaque
        assert "Niterói" not in page.inner_text(sel), sel
    assert "Niterói" not in (WEB / "js" / "app.js").read_text(encoding="utf-8")
    page.click("#tab-mun")
    page.select_option("#mun-select", next(c for c, m in json.loads((WEB / "data" / "indicators.json").read_text())["municipios"].items() if m["name"] == "Rio de Janeiro"))
    assert "Rio de Janeiro" in page.inner_text("#mun-detail")
    assert page.locator("#mun-chart svg.chart").count() == 1
    assert _relevant_errors(page.errors, page.injected) == []


def _px_expected(code, meta):
    pal = ["#f2f2f2", "#ffeda0", "#fec44f", "#fd8d3c", "#e31a1c", "#800026"]
    if code == 0:
        return None
    if code == 1:
        return "#b4bac3"
    return pal[code - meta["classes"]["first_code"]]


def test_pixel_layer_is_default_and_matches_the_class_grid(page):
    page.evaluate("() => document.documentElement.removeAttribute('data-theme')")
    """Camada de pixel: legenda com unidade e fonte, canvas desenhado, e o pixel sob o cursor tem a cor
    e a classe do arquivo data/pixels/<ano>.bin (conferidos de forma independente em Python)."""
    meta = json.loads((WEB / "data" / "pixels" / "meta.json").read_text())
    _layer(page, "pixel")
    assert page.locator("#indicator").is_disabled()
    page.wait_for_function("() => document.querySelector('#pixel-readout') && !document.querySelector('#pixel-readout').hidden")
    leg = page.inner_text("#legend")
    assert "nW·cm⁻²·sr⁻¹" in leg and "Fonte:" in leg and "não é o brilho do céu" in leg and "sem dado válido" in leg
    year = page.evaluate("() => document.getElementById('year-out').textContent")
    grid = np.fromfile(WEB / "data" / "pixels" / "snpp" / f"{year}.bin", dtype="uint8").reshape(meta["grid"]["rows"], meta["grid"]["cols"])
    g = meta["grid"]
    page.locator("#mapa").scroll_into_view_if_needed()
    box = page.locator("#mapa").bounding_box()
    page.wait_for_function("() => { const c=document.querySelector('canvas.openlux-pixels'); return c && c.width>0; }")
    checked = agree = 0
    classes_seen = set()
    for fx in (0.35, 0.45, 0.55, 0.65):
        for fy in (0.55, 0.65, 0.75, 0.82):
            x, y = box["x"] + fx * box["width"], box["y"] + fy * box["height"]
            page.mouse.move(x, y)
            page.wait_for_timeout(40)
            txt = page.inner_text("#pixel-readout")
            m = re.search(r"\((-?\d+),(\d+)°, (-?\d+),(\d+)°\)", txt)
            if not m:
                continue
            lat = float(f"{m.group(1)}.{m.group(2)}"); lon = float(f"{m.group(3)}.{m.group(4)}")
            r, c = int((g["lat_north"] - lat) // g["pixel_deg"]), int((lon - g["lon_west"]) // g["pixel_deg"])
            if not (0 <= r < g["rows"] and 0 <= c < g["cols"]):
                continue
            code = int(grid[r, c])
            exp = _px_expected(code, meta)
            rgba = page.evaluate("""([x, y]) => { const c=document.querySelector('canvas.openlux-pixels');
                const b=c.getBoundingClientRect(); return Array.from(c.getContext('2d').getImageData(Math.round(x-b.x), Math.round(y-b.y), 1, 1).data); }""", [x, y])
            got = "#%02x%02x%02x" % tuple(rgba[:3]) if rgba[3] else None
            checked += 1
            classes_seen.add(code)
            agree += int(got == exp)
    assert checked >= 10 and agree >= checked - 1, (checked, agree)   # tolera um pixel na divisa
    assert len(classes_seen) >= 2                                      # a amostra tem mais de uma classe
    assert _relevant_errors(page.errors, page.injected) == []


def test_pixel_layer_warns_about_noise_from_2022_and_switches_back_to_municipal(page):
    _layer(page, "pixel")
    page.fill("#year", str(len(json.loads((WEB / "data" / "indicators.json").read_text())["meta"]["years"]) - 1))
    page.dispatch_event("#year", "input")
    page.wait_for_selector("#pxnote .pxnote")
    assert "piso de ruído" in page.inner_text("#pxnote")
    page.fill("#year", "0")
    page.dispatch_event("#year", "input")
    page.wait_for_function("() => document.getElementById('year-out').textContent === '2012'")
    assert page.locator("#pxnote .pxnote").count() == 0
    _layer(page, "mun")
    assert page.locator("canvas.openlux-pixels").count() == 0
    assert page.locator("#indicator").is_enabled()
    page.fill("#year", str(13)); page.dispatch_event("#year", "input")
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


def test_exposure_and_pixel_trend_indicators_render_and_match_data(page):
    """Cada indicador novo (setores/pixel) aparece no seletor, pinta o mapa sem erros e o painel do
    municipio mostra os valores do JSON (conferidos de forma independente)."""
    data = json.loads((WEB / "data" / "indicators.json").read_text())
    m = next(iter(data["municipios"].values()))
    if "exposure" not in m:
        pytest.skip("dados sem indicadores de setores")
    keys = page.evaluate("() => [...document.querySelectorAll('#indicator option')].map(o => o.value)")
    novos = ["popL", "popLit", "urban", "rural"] + [f"{p}{w}" for w in data["meta"]["windows"]
                                                   for p in ("pxup_", "pxdown_")]
    assert set(novos) <= set(keys), set(novos) - set(keys)
    _layer(page, "mun")
    for k in novos:
        page.select_option("#indicator", k)
        assert page.locator("#mapa path.leaflet-interactive").count() == 92
        assert page.locator("#legend").inner_text().strip() != ""
    last = len(data["meta"]["years"]) - 1
    cd = next(c for c, mm in data["municipios"].items() if mm["name"] == "Rio de Janeiro")
    page.select_option("#mun-select", cd)
    txt = page.locator("#mun-detail").inner_text().replace(" ", " ")
    v = data["municipios"][cd]["exposure"]["pop_radiance"][last]
    assert f"{v:.2f}".replace(".", ",") in txt
    assert "Mudança significativa por pixel" in txt and "Censo 2022 fixa" in txt
    assert _relevant_errors(page.errors, page.injected) == []


def _fresh(page, server, query=""):
    """Nova aba no mesmo navegador, com captura de erros de console."""
    pg = page.context.browser.new_context(viewport={"width": 1280, "height": 900}).new_page()
    pg.errors = []
    pg.on("console", lambda m: pg.errors.append(m.text) if m.type == "error" else None)
    pg.on("pageerror", lambda e: pg.errors.append(str(e)))
    pg.goto(server + "/" + query)
    pg.wait_for_selector("#mapa path.leaflet-interactive")
    return pg


def _code(name):
    d = json.loads((WEB / "data" / "indicators.json").read_text())
    return next(c for c, m in d["municipios"].items() if m["name"] == name)


def test_permalink_restores_the_view_and_follows_the_controls(page, server):
    rio = _code("Rio de Janeiro")
    pg = _fresh(page, server, f"?lat=-22.9&lng=-43.2&z=10&y=2018&l=mun&i=mean&m={rio}")
    assert pg.inner_text("#year-out") == "2018"
    assert pg.eval_on_selector("input[name=layer]:checked", "e => e.value") == "mun"
    assert pg.eval_on_selector("#indicator", "e => e.value") == "mean" and pg.eval_on_selector("#mun-select", "e => e.value") == rio
    assert "Rio de Janeiro" in pg.inner_text("#mun-detail")
    q = pg.evaluate("() => Object.fromEntries(new URLSearchParams(location.search))")
    assert q["y"] == "2018" and q["l"] == "mun" and q["m"] == rio and float(q["z"]) >= 6
    pg.fill("#year", "0"); pg.dispatch_event("#year", "input")
    assert pg.evaluate("() => new URLSearchParams(location.search).get('y')") == "2012"
    pg.check('input[name="layer"][value="pixel"]')
    assert pg.evaluate("() => new URLSearchParams(location.search).get('l')") == "pixel"
    assert _relevant_errors(pg.errors, _cloudflare_injected(pg.content())) == []
    pg.context.close()


def test_permalink_ignores_invalid_parameters_without_errors(page, server):
    pg = _fresh(page, server, "?lat=abc&lng=&z=99&y=1999&l=zzz&i=__proto__&m=0000000")
    assert pg.inner_text("#year-out") == "2025"                       # ano padrao
    assert pg.eval_on_selector("input[name=layer]:checked", "e => e.value") == "pixel"
    assert pg.eval_on_selector("#indicator", "e => e.value") == "mean"
    assert pg.locator("#mapa path.leaflet-interactive").count() == 92
    assert _relevant_errors(pg.errors, _cloudflare_injected(pg.content())) == []
    pg.context.close()


def test_search_finds_municipality_ignoring_accents_and_case(page, server):
    pg = _fresh(page, server)
    for typed, name in (("niteroi", "Niterói"), ("NOVA FRI", "Nova Friburgo"), ("campos dos", "Campos dos Goytacazes")):
        pg.fill("#mun-search", typed); pg.press("#mun-search", "Enter")
        pg.wait_for_function("(c) => document.getElementById('mun-select').value === c", arg=_code(name))
        assert name in pg.inner_text("#mun-detail")
    pg.fill("#mun-search", "zzzz inexistente"); pg.press("#mun-search", "Enter")     # sem resultado: nada muda, sem erro
    assert pg.eval_on_selector("#mun-select", "e => e.value") == _code("Campos dos Goytacazes")
    assert _relevant_errors(pg.errors, _cloudflare_injected(pg.content())) == []
    pg.context.close()


def test_municipality_names_appear_only_when_zoomed_in_and_can_be_turned_off(page, server):
    pg = _fresh(page, server)
    assert pg.locator(".mlabel span").count() == 0                          # estado inteiro: sem rotulos
    pg = _fresh(page, server, "?lat=-22.9&lng=-43.3&z=10.5&l=pixel")
    pg.wait_for_selector(".mlabel span")
    assert pg.locator(".mlabel span").count() > 0
    pg.click("#display-opts summary")
    pg.uncheck("#labels-chk")
    assert pg.locator(".mlabel span").count() == 0
    pg.context.close()


def test_plain_language_legend_keeps_numeric_classes_and_does_not_claim_a_sky_scale(page, server):
    pg = _fresh(page, server, "?l=pixel")
    pg.wait_for_selector("#legend .meaning")
    leg = pg.inner_text("#legend")
    assert "Sem luz detectada" in leg and "Muitíssima luz" in leg
    assert "0,5 a < 2" in leg and "≥ 100" in leg                       # as classes numericas continuam ao lado
    assert "nem equivalem à escala Bortle" in leg and "não foram validados em campo" in leg
    ui = (WEB / "index.html").read_text(encoding="utf-8") + (WEB / "js" / "app.js").read_text(encoding="utf-8")
    assert "mag/arcsec" not in ui and "SQM" not in ui                  # sem escala de brilho do ceu antes da validacao em campo
    pg.context.close()


def _meta():
    return json.loads((WEB / "data" / "pixels" / "meta.json").read_text(encoding="utf-8"))


def _canvas_rgb(pg, fx, fy):
    box = pg.locator("#mapa").bounding_box()
    x, y = box["x"] + fx * box["width"], box["y"] + fy * box["height"]
    pg.mouse.move(x, y)
    pg.wait_for_timeout(40)
    rgba = pg.evaluate("""([x, y]) => { const c=document.querySelector('canvas.openlux-pixels'); const b=c.getBoundingClientRect();
        return Array.from(c.getContext('2d').getImageData(Math.round(x-b.x), Math.round(y-b.y), 1, 1).data); }""", [x, y])
    return rgba, pg.inner_text("#pixel-readout")


def test_noaa20_sensor_clamps_the_year_and_matches_its_own_grid(page, server):
    meta = _meta()
    pg = _fresh(page, server, "?l=pixel&y=2013")
    pg.select_option("#px-sensor", "noaa20")
    assert pg.inner_text("#year-out") == "2018"                          # NOAA-20 so existe de 2018 a 2025
    assert pg.evaluate("() => new URLSearchParams(location.search).get('s')") == "noaa20"
    assert "NOAA-20" in pg.inner_text("#legend") and "VJ146A4" in pg.inner_text("#legend")
    g = meta["grid"]
    grid = np.fromfile(WEB / "data" / "pixels" / "noaa20" / "2018.bin", dtype="uint8").reshape(g["rows"], g["cols"])
    pg.locator("#mapa").scroll_into_view_if_needed()
    checked = agree = 0
    for fx in (0.4, 0.5, 0.6):
        for fy in (0.6, 0.7, 0.8):
            rgba, txt = _canvas_rgb(pg, fx, fy)
            m = re.search(r"\((-?\d+),(\d+)\u00b0, (-?\d+),(\d+)\u00b0\)", txt)
            if not m:
                continue
            lat, lon = float(f"{m.group(1)}.{m.group(2)}"), float(f"{m.group(3)}.{m.group(4)}")
            r, c = int((g["lat_north"] - lat) // g["pixel_deg"]), int((lon - g["lon_west"]) // g["pixel_deg"])
            if 0 <= r < g["rows"] and 0 <= c < g["cols"]:
                exp = _px_expected(int(grid[r, c]), meta)
                got = "#%02x%02x%02x" % tuple(rgba[:3]) if rgba[3] else None
                checked += 1
                agree += int(got == exp)
    assert checked >= 6 and agree >= checked - 1, (checked, agree)
    pg.fill("#year", "0"); pg.dispatch_event("#year", "input")
    assert pg.inner_text("#year-out") == "2018"
    assert _relevant_errors(pg.errors, _cloudflare_injected(pg.content())) == []
    pg.context.close()


def test_change_layer_legend_counts_and_colors_match_the_grid(page, server):
    meta = _meta()
    pg = _fresh(page, server, "?l=pixel&s=snpp&v=2012_2021")
    leg = pg.inner_text("#legend")
    cn = meta["sensors"]["snpp"]["change"]["2012_2021"]["counts"]
    tested = cn["increase"] + cn["decrease"] + cn["not_significant"]
    assert "Aumento significativo" in leg and "Redução significativa" in leg and "Não testado" in leg and "não foram validados em campo" in leg
    assert ("%.1f%%" % (100 * cn["increase"] / tested)).replace(".", ",") in leg       # percentuais conferidos a partir do meta.json
    assert pg.is_hidden("#year-wrap")                                                   # a mudanca nao tem controle de ano
    pg.select_option("#px-view", "2012_2025")
    leg2 = pg.inner_text("#legend")
    assert "inclui 2022–2025" in leg2 and "não leia como luz nova" in leg2             # aviso do ruido do S-NPP nesta janela
    pg.select_option("#px-sensor", "noaa20")
    assert pg.eval_on_selector("#px-view", "e => e.value") == "rad"                    # janelas de um sensor nao valem para o outro
    pg.select_option("#px-view", "2018_2025")
    assert "série curta" in pg.inner_text("#legend")
    assert _relevant_errors(pg.errors, _cloudflare_injected(pg.content())) == []
    pg.context.close()


def test_basemap_is_off_by_default_and_only_requests_openstreetmap_after_opt_in(page, server):
    pg = page.context.browser.new_context(viewport={"width": 1280, "height": 900}).new_page()
    pg.errors = []
    pg.on("console", lambda m: pg.errors.append(m.text) if m.type == "error" else None)
    seen = []
    png = bytes.fromhex("89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000d4944415478da63f8cfc0f01f0005000201a52f6f2b0000000049454e44ae426082")
    pg.route("https://tile.openstreetmap.org/**", lambda route: (seen.append(route.request.url), route.fulfill(status=200, content_type="image/png", body=png)))
    pg.goto(server + "/?lat=-22.9&lng=-43.3&z=9")
    pg.wait_for_selector("#mapa path.leaflet-interactive")
    pg.wait_for_timeout(600)
    assert seen == []                                                                    # nada de terceiros sem opt-in
    assert not pg.is_checked("#base-chk")                                                 # desligado por padrao
    pg.click("#display-opts summary")
    assert "endereço IP" in pg.inner_text("#display-opts")                              # o aviso de privacidade esta visivel
    pg.check("#base-chk")
    pg.wait_for_function("() => document.querySelectorAll('.osm-tiles img.leaflet-tile').length > 0")
    assert seen and all(u.startswith("https://tile.openstreetmap.org/") for u in seen)
    assert "OpenStreetMap" in pg.inner_text(".leaflet-control-attribution")            # atribuicao obrigatoria visivel
    pg.uncheck("#base-chk")
    assert pg.locator(".osm-tiles img.leaflet-tile").count() == 0
    assert _relevant_errors(pg.errors, _cloudflare_injected(pg.content())) == []
    pg.context.close()


def test_dark_theme_switches_palette_and_opacity_changes_alpha(page, server):
    meta = _meta()
    pg = _fresh(page, server, "?lat=-22.9&lng=-43.3&z=10&l=pixel&y=2025")
    pg.locator("#mapa").scroll_into_view_if_needed()
    pg.click("#display-opts summary")
    light, _ = _canvas_rgb(pg, 0.5, 0.6)
    pg.select_option("#theme-sel", "dark")
    assert pg.evaluate("() => document.documentElement.getAttribute('data-theme')") == "dark"
    pg.wait_for_timeout(150)
    dark, _ = _canvas_rgb(pg, 0.5, 0.6)
    assert light[3] > 0 and dark[3] > 0 and light[:3] != dark[:3]                       # paleta diferente por tema
    dark_hex = {"#1b2230", "#420a68", "#932667", "#dd513a", "#fca50a", "#fcffa4"}
    assert "#%02x%02x%02x" % tuple(dark[:3]) in dark_hex
    pg.fill("#px-opacity", "0.5"); pg.dispatch_event("#px-opacity", "input")
    pg.wait_for_timeout(100)
    half, _ = _canvas_rgb(pg, 0.5, 0.6)
    assert abs(half[3] - round(0.5 * 255)) <= 1
    pg.select_option("#theme-sel", "light")
    assert _relevant_errors(pg.errors, _cloudflare_injected(pg.content())) == []
    pg.context.close()
