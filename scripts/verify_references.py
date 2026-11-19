#!/usr/bin/env python3
"""Verifica cada DOI de docs/references.json no Crossref e gera docs/REFERENCES.md.

Checa: o DOI resolve; o ano do registro coincide com o ano da citacao no texto; o primeiro
autor coincide com o nome da citacao. Os metadados da bibliografia vem do Crossref (nao sao
digitados). Com --texts, tambem confere citacoes autor-ano dos arquivos informados.
"""
import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from openlux.references import check_citations, format_entry


def crossref(doi, tries=4):
    req = urllib.request.Request("https://api.crossref.org/works/" + doi,
                                 headers={"User-Agent": "openlux-reference-check"})
    for k in range(1, tries + 1):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)["message"]
        except urllib.error.HTTPError as e:
            if e.code not in (429, 500, 502, 503) or k == tries:
                raise
            time.sleep(5 * k)  # limite de taxa do Crossref: espera crescente


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--refs", default="docs/references.json")
    ap.add_argument("--out", default="docs/REFERENCES.md")
    ap.add_argument("--texts", nargs="*", default=[])
    ap.add_argument("--offline", action="store_true",
                    help="nao consulta o Crossref: so confere as citacoes dos textos")
    a = ap.parse_args()
    refs = json.loads(Path(a.refs).read_text(encoding="utf-8"))
    entries, problems = [], []
    for r in ([] if a.offline else refs):
        msg = crossref(r["doi"])
        year = msg["issued"]["date-parts"][0][0]
        first = (msg.get("author") or [{}])[0]
        fam = first.get("family") or first.get("name", "")
        if str(year) not in r["cite"]:
            problems.append(f"{r['key']}: ano do Crossref ({year}) difere da citacao {r['cite']}")
        if fam.split()[-1].lower() not in r["cite"].lower():
            problems.append(f"{r['key']}: primeiro autor do Crossref ({fam}) difere da citacao {r['cite']}")
        entries.append((fam.lower(), year, format_entry(msg, r["doi"])))
    entries.sort()
    if not a.offline:
        lines = ["# Referencias", "",
                 "Gerado por `scripts/verify_references.py` a partir de metadados do Crossref; "
                 "cada DOI foi resolvido e conferido (ano e primeiro autor) contra a citacao no texto.", ""]
        lines += [f"- {e}" for _, _, e in entries]
        Path(a.out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    if a.texts:
        text = "\n".join(Path(t).read_text(encoding="utf-8") for t in a.texts)
        c = check_citations(text, refs)
        for k, v in c.items():
            if v:
                problems.append(f"{k}: {v}")
    print(f"{len(refs)} referencias; {len(problems)} problema(s)" + (" (modo offline: Crossref nao consultado)" if a.offline else ""))
    for p in problems:
        print(" -", p)
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
