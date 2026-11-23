"""Utilitarios de teste: leitura do arquivo web/_headers (formato Cloudflare Pages/Workers)."""
from __future__ import annotations

import fnmatch
import re
from pathlib import Path

WEB = Path(__file__).resolve().parent.parent / "web"
# Trechos que a Cloudflare injeta antes de </body> em dominios personalizados:
#  - script inline de deteccao de bots (window.__CF$cv$params);
#  - beacon do Cloudflare Web Analytics (static.cloudflareinsights.com), se a analise estiver ativada.
CF_INJECTION = re.compile(r"<script>window\.__CF\$cv\$params.*?</script>", re.S)
# O beacon vem seguido de uma quebra de linha que a Cloudflare acrescenta.
CF_BEACON = re.compile(r"<script[^>]*static\.cloudflareinsights\.com[^>]*></script>\n?", re.S)


def strip_cloudflare_injections(html: str) -> str:
    return CF_BEACON.sub("", CF_INJECTION.sub("", html))


def has_cloudflare_injection(html: str) -> bool:
    return bool(CF_INJECTION.search(html) or CF_BEACON.search(html))


def parse_headers_file(text: str) -> list[tuple[str, dict]]:
    """[(padrao, {cabecalho: valor})]. Linha sem recuo iniciada por '/' = padrao; linhas
    recuadas 'Nome: valor' pertencem ao ultimo padrao. Comentarios iniciam com '#'."""
    rules: list[tuple[str, dict]] = []
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if not raw[0].isspace():
            rules.append((raw.strip(), {}))
        else:
            name, _, value = raw.strip().partition(":")
            rules[-1][1][name.strip()] = value.strip()
    return rules


def headers_for(path: str, rules) -> dict:
    out: dict = {}
    for pattern, hdrs in rules:
        if fnmatch.fnmatchcase(path, pattern):
            out.update(hdrs)
    return out
