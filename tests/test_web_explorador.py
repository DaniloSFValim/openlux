"""Testes de navegador das páginas reconstruídas: index.html e explorar.html.

Executa Chromium real (Playwright) contra um servidor local de web/. Os resultados
esperados vêm dos dados publicados (web/data) e dos textos da interface.
"""
import http.server
import os
import socketserver
import threading
from pathlib import Path

import pytest

playwright = pytest.importorskip("playwright.sync_api")

WEB = Path(__file__).resolve().parent.parent / "web"
MUN_RIO = "3304557"  # Rio de Janeiro (conferido em web/data/indicators_noaa20.json)


@pytest.fixture(scope="module")
def server():
    if os.environ.get("OPENLUX_URL"):  # modo publicado: testa o site no ar, sem servidor local
        yield os.environ["OPENLUX_URL"].rstrip("/")
        return
    class H(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **k):
            super().__init__(*a, directory=str(WEB), **k)

        def log_message(self, *a):
            pass

    httpd = socketserver.TCPServer(("127.0.0.1", 0), H)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()


@pytest.fixture()
def browser_page():
    with playwright.sync_playwright() as p:
        exe = os.environ.get("OPENLUX_CHROMIUM")
        b = p.chromium.launch(executable_path=exe) if exe else p.chromium.launch()
        pg = b.new_page(viewport={"width": 1280, "height": 800})
        pg.errors = []
        pg.bins = []
        pg.on("console", lambda m: pg.errors.append(m.text) if m.type == "error" else None)
        pg.on("pageerror", lambda e: pg.errors.append(str(e)))
        pg.on("request", lambda r: pg.bins.append(r.url) if r.url.endswith(".bin") else None)
        yield pg
        b.close()


def _abre_gaveta(pg):
    if not pg.evaluate("document.getElementById('gaveta').classList.contains('aberta')"):
        pg.click("#abrirGaveta")
        pg.wait_for_function("document.getElementById('gaveta').classList.contains('aberta')")


def test_index_renders_92_municipalities_and_default_year(server, browser_page):
    pg = browser_page
    pg.goto(server + "/index.html")
    pg.wait_for_selector("#mapa path[data-cd]")
    assert pg.locator("#mapa path[data-cd]").count() == 92
    assert pg.inner_text("#anoNum") == "2025"
    assert pg.errors == []


def test_index_card_opens_from_url_and_shows_ranking(server, browser_page):
    pg = browser_page
    pg.goto(server + f"/index.html?s=noaa20&y=2025&m={MUN_RIO}")
    pg.wait_for_function("document.getElementById('cartao').classList.contains('on')")
    assert pg.inner_text("#cNome") == "Rio de Janeiro"
    assert pg.inner_text("#cPos").endswith("de 92")
    assert pg.errors == []


def test_explorer_loads_with_drawer_closed_and_legend(server, browser_page):
    pg = browser_page
    pg.goto(server + "/explorar.html")
    pg.wait_for_selector("#legClasses li")
    assert pg.inner_text("#anoNum") == "2025"
    assert pg.evaluate("document.getElementById('gaveta').classList.contains('aberta')") is False
    assert len(pg.locator("#legClasses li").all()) == 6
    assert pg.errors == []


def test_explorer_pixel_layer_is_fetched_once_and_hover_shows_class_only(server, browser_page):
    """Regressão: a camada de pixels entrou em laço entre repintar() e atualizarPixels()."""
    pg = browser_page
    pg.goto(server + f"/explorar.html?l=pix,mun,rad&y=2025&m={MUN_RIO}&lat=-22.3&lng=-42.7&z=9")
    pg.wait_for_function("document.getElementById('anoNum').textContent === '2025'")
    pg.wait_for_timeout(2500)
    pg.mouse.move(640, 420)
    pg.wait_for_timeout(600)
    info = pg.inner_text("#pixelInfo")
    assert info.startswith("Classe de luz:"), info
    assert "nW" not in info, "a radiância do pixel não é publicada"
    bins = [u for u in pg.bins if u.endswith("/2025.bin")]
    assert len(bins) <= 2, f"laço de requisições: {len(bins)} pedidos de 2025.bin"
    assert pg.errors == []


def test_explorer_lens_from_url_shows_both_years(server, browser_page):
    pg = browser_page
    pg.goto(server + "/explorar.html?y=2025&lente=2018&lx=0.5&lat=-22.3&lng=-42.7&z=9")
    pg.wait_for_selector(".lente-divisor")
    pg.wait_for_timeout(800)
    assert pg.evaluate("document.querySelector('.lente-divisor').style.display") == "block"

    _abre_gaveta(pg)
    pg.wait_for_timeout(300)
    assert "2018" in pg.inner_text("#notaLente") and "2025" in pg.inner_text("#notaLente")
    assert pg.errors == []


def test_explorer_sensor_switch_keeps_year_and_shows_snpp_noise_warning(server, browser_page):
    pg = browser_page
    pg.goto(server + "/explorar.html?y=2025")
    pg.wait_for_selector("#legClasses li")
    _abre_gaveta(pg)
    pg.select_option("#sensor", "snpp")
    pg.wait_for_url("**s=snpp**")
    pg.wait_for_selector("#legClasses li")
    _abre_gaveta(pg)
    assert "y=2025" in pg.url
    assert pg.inner_text("#anoNum") == "2025"
    assert "2022" in pg.inner_text("#avisoSensor")
    assert pg.errors == []


def test_explorer_share_button_copies_link(server, browser_page):
    pg = browser_page
    pg.context.grant_permissions(["clipboard-read", "clipboard-write"], origin=server)
    pg.goto(server + "/explorar.html?y=2025")
    pg.wait_for_selector("#legClasses li")
    _abre_gaveta(pg)
    pg.click("#btnLink")
    pg.wait_for_function("document.getElementById('notaLink').textContent === 'Link copiado.'")
    assert pg.errors == []


def test_explorer_sensor_switch_keeps_lens_active(server, browser_page):
    """Trocar o sensor recarrega a página; a lente ligada e o ano da lente devem continuar."""
    pg = browser_page
    pg.goto(server + "/explorar.html?y=2025&lente=2018&lx=0.5&lat=-22.3&lng=-42.7&z=9")
    pg.wait_for_selector(".lente-divisor")
    _abre_gaveta(pg)
    pg.select_option("#sensor", "snpp")
    pg.wait_for_url("**s=snpp**")
    pg.wait_for_selector(".lente-divisor")
    _abre_gaveta(pg)
    assert pg.is_checked("#lenteOn")
    assert "lente=2018" in pg.url
    assert pg.errors == []


def test_card_area_is_the_official_ibge_value(server, browser_page):
    """A área do cartão deve ser a da malha IBGE (AREA_KM2), igual à página municipal e ao PDF."""
    pg = browser_page
    pg.goto(server + "/explorar.html?y=2025&m=3304557&lat=-22.6&lng=-43.1&z=9")
    pg.wait_for_function("document.getElementById('cartao').classList.contains('on')")
    pg.wait_for_function("document.getElementById('cPopArea').textContent.includes('km²')")
    assert "1.200,3 km²" in pg.inner_text("#cPopArea")
    assert pg.errors == []


def test_pixel_lens_shows_second_year_pixels(server, browser_page):
    """Lente com camada de pixels: duas imagens de pixel (ano atual e ano da lente), fontes diferentes."""
    pg = browser_page
    pg.goto(server + "/explorar.html?l=pix,mun,rad&y=2025&lente=2018&lx=0.5&lat=-22.9&lng=-43.3&z=10")
    pg.wait_for_function("document.querySelectorAll('img.pixel-canvas').length >= 2", timeout=20000)
    srcs = pg.eval_on_selector_all("img.pixel-canvas", "els => els.map(e => e.src)")
    assert len(set(srcs)) == 2, "ano da lente deve ter pixels diferentes do ano atual"
    assert pg.errors == []
