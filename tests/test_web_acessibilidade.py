"""Verificação automatizada de acessibilidade básica (não substitui auditoria WCAG completa).

Confere, no DOM renderizado: idioma da página, nome acessível de botões e links, rótulo de campos de
formulário, texto alternativo de imagens e nome de SVG com papel de imagem.
"""
import os
import http.server
import socketserver
import threading
from pathlib import Path

import pytest

playwright = pytest.importorskip("playwright.sync_api")
WEB = Path(__file__).resolve().parent.parent / "web"
PAGINAS = ["index.html", "explorar.html", "laboratorio.html", "ambiental.html", "dados.html", "metodologia.html", "municipios.html", "municipio/niteroi.html"]

JS_CHECA = """() => {
  const nome = (el) => (el.getAttribute('aria-label') || el.getAttribute('aria-labelledby') || el.textContent || el.getAttribute('title') || '').trim();
  const problemas = [];
  document.querySelectorAll('button, a[href]').forEach((el) => {
    if (el.offsetParent === null && getComputedStyle(el).position !== 'fixed') return; // oculto
    if (!nome(el)) problemas.push('botão/link sem nome: ' + el.outerHTML.slice(0, 80));
  });
  document.querySelectorAll('input, select, textarea').forEach((el) => {
    if (el.type === 'hidden') return;
    const id = el.id, rotulo = id && document.querySelector('label[for="' + id + '"]');
    if (!(rotulo || el.closest('label') || el.getAttribute('aria-label') || el.getAttribute('aria-labelledby'))) problemas.push('campo sem rótulo: ' + el.outerHTML.slice(0, 80));
  });
  document.querySelectorAll('img').forEach((el) => { if (!el.hasAttribute('alt')) problemas.push('imagem sem alt: ' + el.src); });
  document.querySelectorAll('svg[role="img"]').forEach((el) => { if (!el.getAttribute('aria-label') && !el.getAttribute('aria-labelledby')) problemas.push('svg com role=img sem nome'); });
  if (!document.documentElement.getAttribute('lang')) problemas.push('html sem lang');
  return problemas;
}"""


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


@pytest.mark.parametrize("pagina", PAGINAS)
def test_pagina_sem_problemas_basicos_de_acessibilidade(server, pagina):
    with playwright.sync_playwright() as p:
        exe = os.environ.get("OPENLUX_CHROMIUM")
        b = p.chromium.launch(executable_path=exe) if exe else p.chromium.launch()
        pg = b.new_page(viewport={"width": 1280, "height": 800})
        pg.goto(server + "/" + pagina, wait_until="domcontentloaded")
        pg.wait_for_timeout(1200)
        problemas = pg.evaluate(JS_CHECA)
        b.close()
    assert problemas == [], "\n".join(problemas)
