"""Testes de interação: seleção temporal, filtros, downloads e orçamento de desempenho cartográfico.

Os limites de desempenho são de regressão (pegam piora relevante), não metas. Medidos em 2026-11-26 no
Chromium headless: index 0,19 s e 0,14 MB; explorador 0,27 s e 1,14 MB; laboratório 0,15 s e 0,05 MB.
"""
import hashlib
import http.server
import json
import os
import socketserver
import threading
import time
from pathlib import Path

import pytest

playwright = pytest.importorskip("playwright.sync_api")
WEB = Path(__file__).resolve().parent.parent / "web"
LIMITE_TEMPO_S = 5.0          # tempo até a página mostrar conteúdo
LIMITE_TRANSFERENCIA_MB = 3.0  # bytes transferidos no carregamento inicial do explorador


@pytest.fixture(scope="module")
def server():
    if os.environ.get("OPENLUX_URL"):
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
def pg():
    with playwright.sync_playwright() as p:
        exe = os.environ.get("OPENLUX_CHROMIUM")
        b = p.chromium.launch(executable_path=exe) if exe else p.chromium.launch()
        page = b.new_page(viewport={"width": 1280, "height": 800})
        page.errors = []
        page.on("pageerror", lambda e: page.errors.append(str(e)))
        page.on("console", lambda m: page.errors.append(m.text) if m.type == "error" else None)
        yield page
        b.close()


def _define_valor(pg, sel, valor):
    pg.evaluate("([s, v]) => { const e = document.querySelector(s); e.value = v; e.dispatchEvent(new Event('input', {bubbles: true})); e.dispatchEvent(new Event('change', {bubbles: true})); }", [sel, valor])


def test_explorer_year_slider_changes_year(server, pg):
    pg.goto(server + "/explorar.html?y=2025")
    pg.wait_for_selector("#legClasses li", state="attached")
    _define_valor(pg, "#ano", "0")
    pg.wait_for_timeout(300)
    assert pg.inner_text("#anoNum") == "2018"  # sensor padrão NOAA-20 começa em 2018
    assert pg.errors == []


def test_downloads_serve_exactly_the_catalogued_bytes(server, pg):
    cat = json.loads((WEB / "data/downloads/catalogo.json").read_text(encoding="utf-8"))
    pg.goto(server + "/dados.html")
    pg.wait_for_selector("#catalogo tbody tr", state="attached")
    for a in cat["arquivos"]:
        r = pg.request.get(server + "/" + a["arquivo"])
        assert r.status == 200, a["arquivo"]
        corpo = r.body()
        assert len(corpo) == a["bytes"], a["arquivo"]
        assert hashlib.sha256(corpo).hexdigest() == a["sha256"], a["arquivo"]
    assert pg.errors == []


def test_explorer_meets_performance_budget(server, pg):
    tam = [0]
    pg.on("response", lambda r: tam.__setitem__(0, tam[0] + len(r.body())) if r.status == 200 else None)
    t0 = time.time()
    pg.goto(server + "/explorar.html?l=pix,mun,rad&y=2025", wait_until="domcontentloaded")
    pg.wait_for_selector("#legClasses li", state="attached")
    tempo = time.time() - t0
    assert tempo <= LIMITE_TEMPO_S, f"explorador levou {tempo:.2f} s (limite {LIMITE_TEMPO_S} s)"
    mb = tam[0] / 1e6
    assert mb <= LIMITE_TRANSFERENCIA_MB, f"explorador transferiu {mb:.2f} MB (limite {LIMITE_TRANSFERENCIA_MB} MB)"
    assert pg.errors == []


def test_home_year_slider_changes_class_counts(server, pg):
    pg.goto(server + "/index.html")
    pg.wait_for_selector("#classes li", state="attached")
    antes = pg.locator("#classes").inner_text()
    _define_valor(pg, "#ano", "0")
    pg.wait_for_timeout(300)
    assert pg.inner_text("#anoOut") == "2018"
    assert pg.locator("#classes").inner_text() != antes
    assert pg.errors == []
