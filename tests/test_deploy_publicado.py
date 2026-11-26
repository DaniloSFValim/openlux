"""Verificação pós-deploy: o site publicado serve os mesmos arquivos do repositório.

Ativo só com OPENLUX_URL (ex.: https://openlux.labdados.org). Compara o SHA-256 de cada arquivo de web/
com o que o servidor entrega. Em HTML, remove as injeções da Cloudflare (script de bots e beacon) antes de comparar.
"""
import hashlib
import os
import urllib.request
from pathlib import Path

import pytest

from helpers import WEB, strip_cloudflare_injections

URL = os.environ.get("OPENLUX_URL", "").rstrip("/")
pytestmark = pytest.mark.skipif(not URL, reason="defina OPENLUX_URL para verificar o site publicado")


def _baixa(url):
    req = urllib.request.Request(url, headers={"Cache-Control": "no-cache", "User-Agent": "OpenLux-verificacao-publicacao/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def _arquivos():
    return sorted(p for p in WEB.rglob("*") if p.is_file() and not p.name.startswith("_"))


@pytest.mark.parametrize("arq", [str(p.relative_to(WEB)) for p in _arquivos()] if URL else [])
def test_arquivo_publicado_igual_ao_repositorio(arq):
    local = (WEB / arq).read_bytes()
    remoto = _baixa(f"{URL}/{arq}")
    if arq.endswith(".html"):
        remoto = strip_cloudflare_injections(remoto.decode("utf-8")).encode("utf-8")
        local = local
    assert hashlib.sha256(remoto).hexdigest() == hashlib.sha256(local).hexdigest(), f"diferente no ar: {arq}"
