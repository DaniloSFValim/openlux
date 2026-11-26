#!/usr/bin/env python3
"""Relatório de qualidade dos dados publicados (web/qualidade.html).

Roda verificações sobre os arquivos atuais e grava o resultado com a data e o commit da execução.
Não copia números antigos: cada linha é uma verificação feita agora.
Verificações: hashes do catálogo, contagem de municípios e anos dos JSONs, grades de pixels, hashes de
pixels, páginas e PDFs municipais, geometrias válidas e área total da malha do IBGE.
"""
import hashlib
import html
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"
AREA_TOTAL_DOCUMENTADA = 43750.425  # km², METHODOLOGY.md §11 (soma das áreas do IBGE)


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def verificacoes():
    out = []

    def ok(nome, passou, detalhe):
        out.append((nome, "passou" if passou else "falhou", detalhe))

    cat = json.loads((WEB / "data/downloads/catalogo.json").read_text(encoding="utf-8"))
    bons = [a for a in cat["arquivos"] if (WEB / a["arquivo"]).exists() and sha(WEB / a["arquivo"]) == a["sha256"]]
    ok("Catálogo: SHA-256 dos arquivos publicados", len(bons) == len(cat["arquivos"]),
       f"{len(bons)} de {len(cat['arquivos'])} arquivos conferem")

    for nome in ["indicators_noaa20.json", "indicators.json"]:
        d = json.loads((WEB / "data" / nome).read_text(encoding="utf-8"))
        n = len(d["municipios"])
        anos = d["meta"]["years"]
        ok(f"{nome}: municípios e anos", n == 92 and len(anos) > 0,
           f"{n} municípios; anos {anos[0]}–{anos[-1]}; código {d['meta']['run']['code_commit'][:7]}")

    grade = json.loads((WEB / "data/pixels/meta.json").read_text(encoding="utf-8"))
    rows, cols = grade["grid"]["rows"], grade["grid"]["cols"]
    for sensor in grade["sensors"]:
        bins = list((WEB / "data/pixels" / sensor).glob("*.bin"))
        tamanhos = {b.stat().st_size for b in bins}
        ok(f"Pixels {sensor}: tamanho das grades", tamanhos == {rows * cols},
           f"{len(bins)} arquivos de {rows}×{cols} pixels")
        conferem = all(sha(WEB / "data/pixels" / sensor / f"{y}.bin") == v["sha256"]
                       for y, v in grade["sensors"][sensor]["years"].items())
        ok(f"Pixels {sensor}: SHA-256 registrado em meta.json", conferem, "todos os anos conferem" if conferem else "divergência")
    ok("Pixels: execução a partir de árvore limpa", grade["code"]["dirty"] is False,
       f"commit {grade['code']['commit'][:7]}, dirty={grade['code']['dirty']}")

    mun = list((WEB / "municipio").glob("*.html"))
    pdfs = list((WEB / "municipio").glob("*.pdf"))
    validos = sum(1 for p in pdfs if p.read_bytes()[:5] == b"%PDF-")
    ok("Páginas municipais e PDFs", len(mun) == 92 and len(pdfs) == 92 and validos == 92,
       f"{len(mun)} páginas; {len(pdfs)} PDFs; {validos} com cabeçalho %PDF-")

    malha = gpd.read_file(next((ROOT / "data/raw/ibge/RJ_Municipios_2024").glob("*.shp")))
    validas = int(malha.geometry.is_valid.sum())
    ok("Malha IBGE: geometrias válidas", validas == len(malha), f"{validas} de {len(malha)}")
    area = float(malha["AREA_KM2"].sum())
    dif = abs(area - AREA_TOTAL_DOCUMENTADA)
    ok("Malha IBGE: área total conferida com a documentada", dif < 0.01,
       f"soma AREA_KM2 = {area:,.3f} km²; documentada = {AREA_TOTAL_DOCUMENTADA:,.3f} km²".replace(",", "."))
    return out


def commit():
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        return "desconhecido"


def main():
    res = verificacoes()
    agora = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    passou = sum(1 for _, s, _ in res if s == "passou")
    linhas = "".join(
        f"<tr><td>{html.escape(n)}</td><td class=\"{s}\">{s}</td><td>{html.escape(d)}</td></tr>" for n, s, d in res)
    pagina = f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Qualidade dos dados — OpenLux</title>
<meta name="description" content="Verificações automáticas dos dados publicados: hashes, contagens, grades, páginas e geometrias.">
<link rel="icon" href="data:,"><link rel="stylesheet" href="css/prototipo.css"><link rel="stylesheet" href="css/paginas.css">
</head><body class="pagina">
<header class="cabec"><div class="marca">OpenLux · Qualidade dos dados</div>
<nav class="menu-paginas" aria-label="Áreas do OpenLux">
<a href="index.html">Observatório</a><a href="explorar.html">Explorador</a><a href="laboratorio.html">Laboratório</a><a href="ambiental.html">Observatório ambiental</a><a href="dados.html" aria-current="page">Dados abertos</a><a href="metodologia.html">Metodologia</a>
</nav></header>
<main>
<h1>Relatório de qualidade dos dados</h1>
<p class="suave">Gerado em {agora} pelo commit {commit()} com <code>scripts/build_relatorio_qualidade.py</code>. Cada linha é uma verificação feita nesta execução, não um número copiado.</p>
<p><strong>{passou} de {len(res)} verificações passaram.</strong></p>
<div class="bloco tabela-wrap"><table class="tab"><thead><tr><th>Verificação</th><th>Resultado</th><th>Detalhe</th></tr></thead><tbody>{linhas}</tbody></table></div>
<h2>Estabilidade e validação</h2>
<div class="bloco"><p>Os testes de estabilidade da agregação, das máscaras e do sensor (Spearman, diferenças relativas) estão descritos na seção 11 de <code>METHODOLOGY.md</code>. Eles não são validação externa: nenhum resultado foi comparado a valores publicados. A validação em campo não foi realizada.</p></div>
</main></body></html>
"""
    (WEB / "qualidade.html").write_text(pagina, encoding="utf-8")
    print(f"OK: {passou}/{len(res)} verificações passaram")
    for n, s, d in res:
        print(f"  [{s}] {n}: {d}")


if __name__ == "__main__":
    main()
