"""Verificação de links internos: todo href/src relativo das páginas publicadas aponta para um arquivo existente."""
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

import pytest

WEB = Path(__file__).resolve().parent.parent / "web"
PAGINAS = sorted(list(WEB.glob("*.html")) + list(WEB.glob("municipio/*.html")))


@pytest.mark.parametrize("pagina", PAGINAS, ids=lambda p: str(p.relative_to(WEB)))
def test_links_internos_resolvem(pagina):
    txt = pagina.read_text(encoding="utf-8")
    quebrados = []
    for href in re.findall(r'(?:href|src)="([^"#?]+)', txt):
        u = urlsplit(href)
        if u.scheme or href.startswith(("//", "mailto:", "data:")):
            continue
        alvo = (WEB / unquote(u.path.lstrip("/"))) if href.startswith("/") else (pagina.parent / unquote(u.path))
        if not alvo.resolve().exists():
            quebrados.append(href)
    assert quebrados == [], quebrados


@pytest.mark.parametrize("pagina", PAGINAS, ids=lambda p: str(p.relative_to(WEB)))
def test_sem_script_inline_compativel_com_csp(pagina):
    """web/_headers proíbe scripts inline (script-src 'self'). Toda tag <script> precisa de src."""
    txt = pagina.read_text(encoding="utf-8")
    inline = [m for m in re.findall(r"<script\b[^>]*>", txt) if "src=" not in m]
    assert inline == [], inline
