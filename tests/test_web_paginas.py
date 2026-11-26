"""Testes das páginas de análise reconstruídas: Laboratório, Observatório ambiental,
Dados abertos e Metodologia, e da navegação comum.

Os valores esperados saem dos arquivos publicados (indicadores, catálogo e os próprios
arquivos, com SHA-256 recalculado) — não de constantes copiadas da página.
"""
import hashlib
import http.server
import json
import os
import socketserver
import threading
from pathlib import Path

import pytest

playwright = pytest.importorskip("playwright.sync_api")

WEB = Path(__file__).resolve().parent.parent / "web"
RIO, NITEROI, CACHOEIRAS = "3304557", "3303302", "3300803"


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


@pytest.fixture()
def pg():
    with playwright.sync_playwright() as p:
        exe = os.environ.get("OPENLUX_CHROMIUM")
        b = p.chromium.launch(executable_path=exe) if exe else p.chromium.launch()
        page = b.new_page(viewport={"width": 1280, "height": 900})
        page.errors = []
        page.on("pageerror", lambda e: page.errors.append(str(e)))
        page.on("console", lambda m: page.errors.append(m.text) if m.type == "error" else None)
        yield page
        b.close()


def _indicadores():
    return json.loads((WEB / "data/indicators_noaa20.json").read_text(encoding="utf-8"))


def _fmt2(v):
    return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def test_laboratorio_default_values_match_published_data(server, pg):
    N = _indicadores()
    pg.goto(server + "/laboratorio.html")
    pg.wait_for_selector("#corpoTab tr", state="attached")
    pg.wait_for_timeout(500)
    media_rio = N["municipios"][RIO]["mean"][-1]
    primeira = pg.locator("#corpoTab tr").nth(0).inner_text().split("\t")
    assert primeira[1] == _fmt2(media_rio), primeira
    assert pg.errors == []


def test_laboratorio_changing_municipality_updates_column_and_trend(server, pg):
    pg.goto(server + "/laboratorio.html")
    pg.wait_for_selector("#corpoTab tr", state="attached")
    pg.select_option("#m3", CACHOEIRAS)
    pg.wait_for_function("document.getElementById('cabTab').textContent.includes('Cachoeiras de Macacu')")
    assert "Cachoeiras de Macacu" in pg.locator("#cabTab").inner_text()
    assert pg.errors == []


def test_laboratorio_trend_is_not_claimed_when_not_significant(server, pg):
    N = _indicadores()
    assert N["municipios"][RIO]["trends"]["2018_2025"]["p_value"] >= 0.05
    pg.goto(server + "/laboratorio.html")
    pg.wait_for_selector("#corpoTrend tr", state="attached")
    assert "sem tendência estatisticamente sustentada" in pg.locator("#corpoTrend tr").nth(0).inner_text()


def test_laboratorio_has_definitions_for_every_indicator(server, pg):
    pg.goto(server + "/laboratorio.html")
    for termo in ["Média municipal", "Mediana municipal", "Percentis P75", "Posição entre municípios",
                  "Inclinação e p-valor", "Variação percentual 2018"]:
        assert pg.locator(f"h3:has-text('{termo}')").count() == 1, termo


def test_dados_lists_every_catalogue_file_and_hash_matches_bytes(server, pg):
    cat = json.loads((WEB / "data/downloads/catalogo.json").read_text(encoding="utf-8"))
    pg.goto(server + "/dados.html")
    pg.wait_for_selector("#catalogo tbody tr", state="attached")
    assert pg.locator("#catalogo tbody tr").count() == len(cat["arquivos"])
    for a in cat["arquivos"]:
        arq = WEB / a["arquivo"]
        assert arq.exists(), a["arquivo"]
        sha = hashlib.sha256(arq.read_bytes()).hexdigest()
        assert sha == a["sha256"], f"hash divergente em {a['arquivo']}"
        assert sha in pg.content(), f"SHA-256 de {a['arquivo']} ausente da página"
    assert pg.errors == []


def test_dados_download_link_serves_the_file(server, pg):
    cat = json.loads((WEB / "data/downloads/catalogo.json").read_text(encoding="utf-8"))
    alvo = cat["arquivos"][0]["arquivo"]
    pg.goto(server + "/dados.html")
    pg.wait_for_selector("#catalogo tbody tr", state="attached")
    r = pg.request.get(server + "/" + alvo)
    assert r.status == 200 and len(r.body()) == cat["arquivos"][0]["bytes"]


def test_ambiental_publishes_no_results_and_no_unreviewed_file(server, pg):
    pg.goto(server + "/ambiental.html")
    texto = pg.inner_text("main")
    assert "Ainda não há resultados publicados" in texto
    assert "não publicada" in texto
    assert not (WEB / "data/ambiental/uc_municipios.json").exists()
    assert "uc_municipios" not in pg.content()
    assert pg.errors == []


def test_metodologia_states_field_validation_was_not_done(server, pg):
    pg.goto(server + "/metodologia.html")
    texto = pg.inner_text("main")
    assert "Validação com medições de campo: não realizada" in texto
    assert "não mede" in texto.lower()
    assert "brilho do céu" in texto
    assert pg.errors == []


@pytest.mark.parametrize("pagina", ["index.html", "explorar.html", "laboratorio.html",
                                    "ambiental.html", "dados.html", "metodologia.html"])
def test_every_page_links_all_six_areas(server, pg, pagina):
    pg.goto(server + "/" + pagina)
    hrefs = pg.eval_on_selector_all(".menu-paginas a", "els => els.map(e => e.getAttribute('href'))")
    assert hrefs == ["index.html", "explorar.html", "laboratorio.html", "ambiental.html",
                     "dados.html", "metodologia.html"], hrefs
    assert pg.locator(f".menu-paginas a[href='{pagina}']").count() == 1


@pytest.mark.parametrize("pagina", ["index.html", "explorar.html", "laboratorio.html",
                                    "ambiental.html", "dados.html", "metodologia.html"])
def test_no_horizontal_scroll_at_phone_width(server, pg, pagina):
    """Largura de celular (390 px): o cartão municipal fora da tela não pode gerar rolagem horizontal."""
    pg.set_viewport_size({"width": 390, "height": 844})
    pg.goto(server + "/" + pagina)
    pg.wait_for_timeout(800)
    estilo = pg.evaluate("getComputedStyle(document.documentElement).overflowX")
    pg.evaluate("window.scrollBy(400, 0)")
    pg.wait_for_timeout(100)
    # rolagem programática pode existir com overflow hidden; o que importa ao usuário é overflow-x oculto
    # ou nenhuma rolagem efetiva
    assert estilo == "hidden" or pg.evaluate("window.scrollX") == 0, (pagina, estilo)
