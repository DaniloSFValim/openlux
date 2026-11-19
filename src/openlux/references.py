"""Referencias: formatacao a partir de metadados do Crossref e checagem texto x bibliografia."""
from __future__ import annotations

import re


def _initials(given: str) -> str:
    parts = re.split(r"[\s\-]+", given.strip())
    return " ".join(p[0] + "." for p in parts if p)


def format_entry(msg: dict, doi: str, max_authors: int = 6) -> str:
    authors = msg.get("author") or []
    def fam(a):
        f = a.get("family") or a.get("name", "?")
        return f.title() if f.isupper() else f
    names = [f"{fam(a)}, {_initials(a.get('given', ''))}".rstrip(", ") for a in authors]
    if len(names) > max_authors:
        auth = f"{names[0]} et al."
    else:
        auth = ", ".join(names)
    year = ((msg.get("issued") or {}).get("date-parts") or [[None]])[0][0]
    title = (msg.get("title") or ["?"])[0].rstrip(".")
    if title.isupper():  # alguns registros antigos vem em caixa alta
        title = title.capitalize()
    cont = (msg.get("container-title") or [""])[0]
    vol, page = msg.get("volume"), msg.get("page") or msg.get("article-number")
    tail = ""
    if cont:
        tail = f" *{cont}*"
        if vol:
            tail += f", {vol}"
        if page:
            tail += f", {str(page).replace('-', '–')}"
        tail += "."
    return f"{auth} ({year}). {title}.{tail} https://doi.org/{doi}"


# Citacoes autor-ano: narrativa "Silva et al. (2020)" e parentetica "(Silva et al., 2020)".
_NAME = r"[A-ZÀ-Ý][\wÀ-ÿ'\-]+(?: et al\.)?"
_CITE = re.compile(rf"({_NAME}) \(((?:1[89]|20)\d{{2}})\)|({_NAME}), ((?:1[89]|20)\d{{2}})(?=[;)])")


def check_citations(text: str, refs: list[dict]) -> dict:
    """Compara citacoes autor-ano do texto com a lista. Retorna orfas e nao cadastradas.

    As citacoes sao normalizadas para "Autor (ano)" e comparadas com o campo ``cite``.
    """
    known = {r["cite"] for r in refs}
    found = {f"{m.group(1) or m.group(3)} ({m.group(2) or m.group(4)})" for m in _CITE.finditer(text)}
    return dict(uncited_references=sorted(known - found), unknown_citations=sorted(found - known))
