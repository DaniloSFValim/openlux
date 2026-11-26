#!/usr/bin/env python3
"""Gera as páginas municipais (web/municipio/<slug>.html), os relatórios em PDF (web/municipio/<slug>.pdf)
e o índice web/municipios.html, a partir de arquivos publicados e da malha do IBGE em data/raw/ibge.

Nenhum número é digitado à mão: tudo vem de web/data (indicadores NOAA-20 e S-NPP, percentis, grade de pixels)
e da malha municipal (área, nomes das regiões). A contagem de pixels por município usa o centro do pixel dentro
do polígono (rasterize com all_touched=False) e lê só as classes de luz, nunca valores de radiância.
Premissa herdada da metodologia: malha IBGE (SIRGAS 2000) tratada como WGS84.
"""
import csv
import glob
import html
import json
import unicodedata
from pathlib import Path

import geopandas as gpd
import numpy as np
from rasterio.features import rasterize
from rasterio.transform import Affine
from reportlab.graphics.shapes import Drawing, Line, Polygon, PolyLine, String
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"
OUT = WEB / "municipio"
DJV = "/usr/share/fonts/truetype/dejavu/"
pdfmetrics.registerFont(TTFont("DejaVu", DJV + "DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("DejaVu-Bold", DJV + "DejaVuSans-Bold.ttf"))


def slug(nome):
    s = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode().lower()
    return "-".join("".join(ch if ch.isalnum() else " " for ch in s).split())


def fmt(v, d=2):
    if v is None or not np.isfinite(v):
        return "—"
    return f"{v:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def inteiro(v):
    return f"{int(v):,}".replace(",", ".")


def carregar():
    N = json.loads((WEB / "data/indicators_noaa20.json").read_text(encoding="utf-8"))
    S = json.loads((WEB / "data/indicators.json").read_text(encoding="utf-8"))
    perc = {}
    with open(WEB / "data/downloads/openlux_percentis_pixels_noaa20.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            perc.setdefault(r["CD_MUN"], {})[int(r["year"])] = {k: float(r[k]) for k in ("q75_radiance", "q90_radiance", "q95_radiance")}
    grade = json.loads((WEB / "data/pixels/meta.json").read_text(encoding="utf-8"))
    cat = json.loads((WEB / "data/downloads/catalogo.json").read_text(encoding="utf-8"))
    malha = gpd.read_file(next(glob.iglob(str(ROOT / "data/raw/ibge/RJ_Municipios_2024/*.shp"))))
    return N, S, perc, grade, cat, malha


def contagens_pixels(malha, grade, ano):
    """Classes de luz dentro de cada município no ano (centro do pixel)."""
    g = grade["grid"]
    rows, cols, pd = g["rows"], g["cols"], g["pixel_deg"]
    codigos = np.fromfile(WEB / f"data/pixels/noaa20/{ano}.bin", dtype=np.uint8).reshape(rows, cols)
    tr = Affine(pd, 0, g["lon_west"], 0, -pd, g["lat_north"])
    shapes = [(geom, i + 1) for i, geom in enumerate(malha.geometry)]
    lab = rasterize(shapes, out_shape=(rows, cols), transform=tr, fill=0, all_touched=False, dtype="int32")
    out = {}
    for i, cd in enumerate(malha["CD_MUN"].astype(str)):
        vals = codigos[lab == i + 1]
        out[cd] = np.bincount(vals, minlength=8)[:8]
    return out, grade["classes"]["labels"], grade["classes"]["first_code"]


def coords_svg(geom, x, y):
    """Caminho SVG de um polígono/multipolígono em lon/lat, projeção equirretangular com cos(lat)."""
    polys = [geom] if geom.geom_type == "Polygon" else list(geom.geoms)
    d = []
    for p in polys:
        for ring in [p.exterior] + list(p.interiors):
            pts = list(ring.coords)
            d.append("M" + "L".join(f"{x(px):.1f},{y(py):.1f}" for px, py in pts) + "Z")
    return "".join(d)


def mapa_svg(malha, cd, W=420, H=380):
    b = malha.total_bounds
    k = np.cos(np.radians((b[1] + b[3]) / 2))
    minx, maxx, miny, maxy = b
    esc = (W - 10) / ((maxx - minx) * k)
    x = lambda lon: 5 + (lon - minx) * k * esc
    y = lambda lat: 5 + (maxy - lat) * esc
    paths = []
    alvo = None
    for _, r in malha.iterrows():
        if str(r["CD_MUN"]) == cd:
            alvo = coords_svg(r.geometry, x, y)
        else:
            paths.append(coords_svg(r.geometry, x, y))
    hh = int((maxy - miny) * esc + 10)
    return (f'<svg viewBox="0 0 {W} {hh}" role="img" aria-label="Mapa do município destacado no Rio de Janeiro">'
            f'<path d="{"".join(paths)}" fill="#1b2540" stroke="rgba(255,255,255,.2)" stroke-width=".6"/>'
            f'<path d="{alvo}" fill="#ffd166" fill-opacity=".9" stroke="#fff" stroke-width="1.2"/></svg>')


def serie_svg(vals_n, anos_n, vals_s, anos_s, W=640, H=240):
    m = {"l": 52, "r": 12, "t": 12, "b": 30}
    todos = [v for v in vals_n + vals_s if v is not None]
    mx = max(todos + [1e-9])
    x = lambda a: m["l"] + (a - anos_s[0]) / (anos_s[-1] - anos_s[0]) * (W - m["l"] - m["r"])
    y = lambda v: H - m["b"] - v / mx * (H - m["t"] - m["b"])
    parts = []
    for f in (0, 0.5, 1):
        parts.append(f'<line x1="{m["l"]}" x2="{W - m["r"]}" y1="{y(mx * f):.1f}" y2="{y(mx * f):.1f}" stroke="rgba(255,255,255,.08)"/>')
        parts.append(f'<text x="4" y="{y(mx * f) + 4:.1f}">{fmt(mx * f, 1)}</text>')
    for a in anos_s:
        if a % 2 == 0:
            parts.append(f'<text x="{x(a) - 10:.1f}" y="{H - 8}">{a}</text>')

    def linha(vals, anos, cor, extra=""):
        pts = " ".join(f"{x(a):.1f},{y(v):.1f}" for a, v in zip(anos, vals) if v is not None)
        return f'<polyline points="{pts}" fill="none" stroke="{cor}" stroke-width="2.4" {extra}/>'
    parts.append(linha(vals_s, anos_s, "#9fb3cf", 'stroke-dasharray="5 4"'))
    parts.append(linha(vals_n, anos_n, "#ffd166"))
    return f'<svg class="grafico" viewBox="0 0 {W} {H}" role="img" aria-label="Série anual da radiância média">{"".join(parts)}</svg>'


def dados_municipio(cd, N, S, perc, contagens, rotulos, primeira, ano):
    anos = N["meta"]["years"]
    i = anos.index(ano)
    m = N["municipios"][cd]
    medias = {c: v["mean"][i] for c, v in N["municipios"].items() if v["mean"][i] is not None}
    ord_ = sorted(medias, key=lambda c: -medias[c])
    est_media = sum(medias.values()) / len(medias)
    est_mediana = float(np.median(list(medias.values())))
    t = m["trends"].get("2018_2025")
    anos_s = S["meta"]["years"]
    serie_s = S["municipios"][cd]["mean"]
    cont = contagens[cd]
    return dict(
        cd=cd, nome=m["name"], ano=ano, media=m["mean"][i], mediana=m["median"][i],
        perc=perc.get(cd, {}).get(ano), pos=ord_.index(cd) + 1, n=len(ord_),
        est_media=est_media, est_mediana=est_mediana, populacao=m["population"],
        serie_n=(anos, m["mean"]), serie_s=(anos_s, serie_s), t=t,
        contagem=cont, rotulos=rotulos, primeira=primeira,
        versao=N["meta"]["run"]["code_commit"], processado=N["meta"]["run"]["processed_utc"],
    )


CSS_PAG = """
  body.pagina{margin:0;background:radial-gradient(120% 90% at 60% 0%,#0f1e3d,#060a16 60%);color:#eef3fb;font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;line-height:1.5}
  main{max-width:1080px;margin:0 auto;padding:24px 16px 64px}
  h1{font-size:clamp(1.5rem,4vw,2.2rem);margin:4px 0 6px}
  h2{font-size:1.15rem;margin:30px 0 10px;color:#ffd166}
  p,li,dd,dt{max-width:74ch}
  .suave{color:#9fb3cf;font-size:.92rem}
  a{color:#ffd166}
  .bloco{background:rgba(10,16,34,.72);border:1px solid rgba(255,255,255,.08);border-radius:14px;padding:16px 18px;margin:12px 0}
  table.tab{width:100%;border-collapse:collapse;font-size:.92rem;font-variant-numeric:tabular-nums}
  table.tab th,table.tab td{padding:8px 10px;text-align:right;border-bottom:1px solid rgba(255,255,255,.08);vertical-align:top}
  table.tab th:first-child,table.tab td:first-child{text-align:left}
  .tabela-wrap{overflow-x:auto}
  dl.def{display:grid;grid-template-columns:minmax(120px,200px) 1fr;gap:6px 14px;font-size:.92rem}
  dl.def dt{color:#9fb3cf}dl.def dd{margin:0}
  .mapa svg{width:min(100%,420px);height:auto;display:block;margin:0 auto}
  .grafico{width:100%;height:auto;display:block}.grafico text{fill:#9fb3cf;font-size:11px}
  .menu-paginas{display:flex;flex-wrap:wrap;gap:6px 14px;margin-top:8px;font-size:.9rem}
  .menu-paginas a{color:#9fb3cf;text-decoration:none;padding:4px 0}
  .cabec{border-bottom:1px solid rgba(255,255,255,.1);padding:14px 16px}
  .marca{color:#9fb3cf;font-size:.85rem;letter-spacing:.08em;text-transform:uppercase}
  .acoes a{display:inline-block;background:#ffd166;color:#151a26;border-radius:10px;padding:8px 12px;font-weight:700;text-decoration:none;margin:4px 6px 4px 0}
  @media (max-width:640px){dl.def{grid-template-columns:1fr}}
"""


def cabecalho(prefixo):
    return f"""<header class="cabec"><div class="marca">OpenLux · Município</div>
<nav class="menu-paginas" aria-label="Áreas do OpenLux">
<a href="{prefixo}index.html">Observatório</a><a href="{prefixo}explorar.html">Explorador</a><a href="{prefixo}laboratorio.html">Laboratório</a><a href="{prefixo}ambiental.html">Observatório ambiental</a><a href="{prefixo}dados.html">Dados abertos</a><a href="{prefixo}metodologia.html">Metodologia</a>
</nav></header>"""


def fontes_html(N):
    itens = []
    for s in N["meta"]["sources"]:
        doi = f' DOI <a href="https://doi.org/{html.escape(s["doi"])}" rel="noopener">{html.escape(s["doi"])}</a>' if s.get("doi") else ""
        itens.append(f'<li>{html.escape(s["name"])} ({html.escape(s["institution"])}).{doi} Licença: {html.escape(s.get("license", "—"))}</li>')
    itens.append('<li>IBGE, Malha Municipal Digital 2024 (RJ): área territorial (AREA_KM2) e limites. Licença compatível com CC BY 4.0, conforme Notas Metodológicas 01/2025 do IBGE.</li>')
    itens.append('<li>IBGE, Censo Demográfico 2022, SIDRA tabela 4709, variável 93: população residente. Reuso permitido com citação da fonte.</li>')
    return "".join(itens)


def pagina_html(d, N, perc_ok, malha, geo_svg):
    cd, nome, ano = d["cd"], d["nome"], d["ano"]
    mal = malha.set_index(malha["CD_MUN"].astype(str)).loc[cd]
    area = float(mal["AREA_KM2"])
    rel = [f'{float(v):.0f}' for v in []]
    anos_n, vals_n = d["serie_n"]
    anos_s, vals_s = d["serie_s"]
    grafico = serie_svg(vals_n, anos_n, vals_s, anos_s)
    t = d["t"] or {}
    p = d["perc"] or {}
    cont = d["contagem"]
    validos = int(cont[2:8].sum())
    linhas_pix = "".join(
        f'<tr><td>{html.escape(d["rotulos"][k - d["primeira"]])}</td><td>{inteiro(cont[k])}</td><td>{fmt(100 * cont[k] / validos if validos else None, 1)} %</td></tr>'
        for k in range(d["primeira"], 8)
    )
    razao = d["media"] / d["est_media"] if d["media"] else None
    html_out = f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(nome)} — OpenLux</title>
<meta name="description" content="Luz noturna estimada por satélite em {html.escape(nome)}: indicadores, série 2018–2025, comparação com o estado, ranking e distribuição de pixels. Estimativa por sensoriamento remoto.">
<link rel="icon" href="data:,"><link rel="stylesheet" href="../css/prototipo.css"><link rel="stylesheet" href="../css/paginas.css">
<style>{CSS_PAG}</style></head>
<body class="pagina">
{cabecalho("../")}
<main>
<h1>{html.escape(nome)}</h1>
<p class="suave">Município do Rio de Janeiro · código IBGE {cd}</p>
<div class="acoes"><a href="../explorar.html?s=noaa20&amp;y={ano}&amp;m={cd}">Abrir no explorador</a><a href="{slug(nome)}.pdf" download>Baixar relatório em PDF</a></div>

<h2>Identificação</h2>
<div class="bloco"><dl class="def">
<dt>Município</dt><dd>{html.escape(nome)}</dd>
<dt>Código IBGE</dt><dd>{cd}</dd>
<dt>Região geográfica intermediária</dt><dd>{html.escape(str(mal["NM_RGINT"]))}</dd>
<dt>Região geográfica imediata</dt><dd>{html.escape(str(mal["NM_RGI"]))}</dd>
<dt>Área territorial</dt><dd>{fmt(area, 3)} km² (IBGE, Malha Municipal Digital 2024)</dd>
<dt>População residente</dt><dd>{fmt(d["populacao"], 0)} habitantes (IBGE, Censo Demográfico 2022, SIDRA tabela 4709)</dd>
</dl></div>

<h2>Mapa</h2>
<div class="bloco mapa">{geo_svg}<p class="suave">Município em amarelo, demais municípios do estado em cinza. Limites do IBGE (malha 2024).</p></div>

<h2>Indicadores de {ano}</h2>
<div class="bloco tabela-wrap"><table class="tab">
<thead><tr><th>Indicador</th><th>{html.escape(nome)}</th><th>Estado (média dos 92 municípios)</th></tr></thead><tbody>
<tr><td>Radiância média (nW·cm⁻²·sr⁻¹)</td><td>{fmt(d["media"], 2)}</td><td>{fmt(d["est_media"], 2)}</td></tr>
<tr><td>Mediana dos pixels (nW·cm⁻²·sr⁻¹)</td><td>{fmt(d["mediana"], 2)}</td><td>{fmt(d["est_mediana"], 2)}</td></tr>
<tr><td>Percentil 75 dos pixels</td><td>{fmt(p.get("q75_radiance"), 2)}</td><td>—</td></tr>
<tr><td>Percentil 90 dos pixels</td><td>{fmt(p.get("q90_radiance"), 2)}</td><td>—</td></tr>
<tr><td>Percentil 95 dos pixels</td><td>{fmt(p.get("q95_radiance"), 2)}</td><td>—</td></tr>
<tr><td>Posição entre os 92 municípios (1º = maior média)</td><td>{d["pos"]}º de {d["n"]}</td><td>—</td></tr>
<tr><td>Radiância média em relação ao estado (razão)</td><td>{fmt(razao, 2)}×</td><td>1,00×</td></tr>
</tbody></table></div>
<p class="suave">Variação 2018→2025 (média municipal): {fmt(t.get("change_pct"), 1)} %. Tendência Theil–Sen 2018–2025: inclinação {fmt(t.get("slope"), 3)} nW·cm⁻²·sr⁻¹ por ano, p-valor {fmt(t.get("p_value"), 3)}. {"Tendência sustentada (p < 0,05)." if t.get("p_value") is not None and t["p_value"] < 0.05 else "Sem tendência estatisticamente sustentada (p ≥ 0,05)."}</p>

<h2>Série histórica</h2>
<div class="bloco">{grafico}
<p class="suave">NOAA-20 (sólido, 2018–2025, primário) e S-NPP (tracejado, 2012–2025, continuidade). O S-NPP tem ruído em áreas escuras a partir de 2022: não leia essa diferença como mudança real.</p></div>

<h2>Comparação com o estado</h2>
<div class="bloco"><p>Em {ano}, a média de {html.escape(nome)} ({fmt(d["media"], 2)} nW·cm⁻²·sr⁻¹) é {fmt(razao, 2)} vez{"es" if razao and razao != 1 else ""} a média simples dos 92 municípios ({fmt(d["est_media"], 2)}). A comparação usa média simples, não ponderada por área ou população.</p></div>

<h2>Ranking</h2>
<div class="bloco"><p>{html.escape(nome)} ocupa a {d["pos"]}ª posição entre {d["n"]} municípios, pela média de {ano} (1º = maior média). Ranking completo em <a href="../index.html#h-rank">Observatório</a>.</p></div>

<h2>Distribuição espacial dos pixels ({ano})</h2>
<div class="bloco tabela-wrap"><table class="tab">
<thead><tr><th>Classe de luz (nW·cm⁻²·sr⁻¹)</th><th>Pixels</th><th>% dos pixels válidos</th></tr></thead><tbody>{linhas_pix}</tbody></table>
<p class="suave">Contagem pelo centro de cada pixel (≈ 460 m) dentro do polígono municipal. Pixels válidos: {validos:,}. Mostra classes de luz, não valores de radiância, e não é medição do brilho do céu.</p></div>

<h2>Metodologia</h2>
<div class="bloco"><p>Radiância média e percentis dos pixels válidos (máscara de qualidade 0 e terra). Agregação por fração de cobertura dos pixels. Tendências com Theil–Sen e teste de Kendall, mínimo de 8 anos válidos. Detalhes em <a href="../metodologia.html">Metodologia</a>, incluindo o que o OpenLux não mede.</p></div>

<h2>Fontes</h2>
<div class="bloco"><ul>{fontes_html(N)}</ul></div>

<h2>Dados e versão</h2>
<div class="bloco"><dl class="def">
<dt>Dados processados em</dt><dd>{html.escape(d["processado"])} (UTC)</dd>
<dt>Versão do código</dt><dd><code>{html.escape(d["versao"])}</code></dd>
<dt>Catálogo</dt><dd><a href="../dados.html">Dados abertos</a> (SHA-256 de cada arquivo)</dd>
</dl></div>
</main>
<footer class="suave" style="max-width:1080px;margin:0 auto;padding:0 16px 32px">Estimativa por sensoriamento remoto. Autor: Danilo Valim · ORCID 0009-0009-7250-6151 · DOI 10.5281/zenodo.24510755</footer>
</body></html>
"""
    return html_out


def pdf(d, N, malha, caminho):
    styles = getSampleStyleSheet()
    base = ParagraphStyle("b", parent=styles["Normal"], fontName="DejaVu", fontSize=9, leading=12)
    h1 = ParagraphStyle("h1", parent=base, fontName="DejaVu-Bold", fontSize=16, leading=20)
    h2 = ParagraphStyle("h2", parent=base, fontName="DejaVu-Bold", fontSize=11, leading=14, spaceBefore=10, spaceAfter=4, keepWithNext=1)
    cd, nome, ano = d["cd"], d["nome"], d["ano"]
    mal = malha.set_index(malha["CD_MUN"].astype(str)).loc[cd]
    p = d["perc"] or {}
    t = d["t"] or {}
    cont = d["contagem"]
    validos = int(cont[2:8].sum())
    doc = SimpleDocTemplate(str(caminho), pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=1.6 * cm, bottomMargin=1.6 * cm,
                            title=f"Relatório municipal — {nome}", author="OpenLux")
    el = []
    el.append(Paragraph(f"Relatório municipal: {html.escape(nome)}", h1))
    el.append(Paragraph("OpenLux · luz noturna estimada por sensoriamento remoto (não é medição do brilho do céu)", base))
    el.append(Spacer(1, 6))
    ident = [["Município", nome], ["Código IBGE", cd], ["Região intermediária", str(mal["NM_RGINT"])], ["Região imediata", str(mal["NM_RGI"])],
             ["Área territorial", f"{fmt(float(mal['AREA_KM2']), 3)} km² (IBGE Malha 2024)"],
             ["População residente", f"{fmt(d['populacao'], 0)} hab. (Censo 2022, SIDRA 4709)"]]
    tab = Table(ident, colWidths=[5 * cm, 11.5 * cm])
    tab.setStyle(TableStyle([("FONT", (0, 0), (-1, -1), "DejaVu", 9), ("FONT", (0, 0), (0, -1), "DejaVu-Bold", 9),
                             ("GRID", (0, 0), (-1, -1), 0.25, colors.grey), ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    el += [Paragraph("Identificação", h2), tab]
    # mapa
    W, H = 380, 340
    b = malha.total_bounds
    k = np.cos(np.radians((b[1] + b[3]) / 2))
    esc = (W - 10) / ((b[2] - b[0]) * k)
    X = lambda lon: 5 + (lon - b[0]) * k * esc
    Y = lambda lat: 5 + (b[3] - lat) * esc
    dr = Drawing(W, H)
    for _, r in malha.iterrows():
        polys = [r.geometry] if r.geometry.geom_type == "Polygon" else list(r.geometry.geoms)
        alvo = str(r["CD_MUN"]) == cd
        for pol in polys:
            pts = [c for xy in pol.exterior.coords for c in (X(xy[0]), Y(xy[1]))]
            dr.add(Polygon(pts, fillColor=colors.HexColor("#ffd166" if alvo else "#3a4a6b"), strokeColor=colors.white, strokeWidth=0.4))
    el += [Paragraph("Mapa", h2), dr]
    # indicadores
    ind = [["Indicador (" + str(ano) + ")", nome, "Estado (média dos 92)"],
           ["Radiância média (nW·cm⁻²·sr⁻¹)", fmt(d["media"]), fmt(d["est_media"])],
           ["Mediana dos pixels", fmt(d["mediana"]), fmt(d["est_mediana"])],
           ["Percentil 75 / 90 / 95 dos pixels", f"{fmt(p.get('q75_radiance'))} / {fmt(p.get('q90_radiance'))} / {fmt(p.get('q95_radiance'))}", "—"],
           ["Posição entre os 92 (1º = maior)", f"{d['pos']}º de {d['n']}", "—"],
           ["Variação 2018→2025 (%)", fmt(t.get("change_pct"), 1), "—"],
           ["Tendência 2018–2025: inclinação e p-valor", f"{fmt(t.get('slope'), 3)} · p = {fmt(t.get('p_value'), 3)}", "—"]]
    tb = Table(ind, colWidths=[7.5 * cm, 5 * cm, 4 * cm])
    tb.setStyle(TableStyle([("FONT", (0, 0), (-1, -1), "DejaVu", 8.5), ("FONT", (0, 0), (-1, 0), "DejaVu-Bold", 8.5),
                            ("GRID", (0, 0), (-1, -1), 0.25, colors.grey), ("ALIGN", (1, 1), (-1, -1), "RIGHT")]))
    el += [Paragraph("Indicadores", h2), tb]
    # série
    anos_n, vals_n = d["serie_n"]
    anos_s, vals_s = d["serie_s"]
    G = Drawing(480, 190)
    x0, y0, gw, gh = 40, 25, 420, 150
    mx = max([v for v in vals_n + vals_s if v is not None] + [1e-9])
    xa = lambda a: x0 + (a - anos_s[0]) / (anos_s[-1] - anos_s[0]) * gw
    ya = lambda v: y0 + v / mx * gh
    G.add(Line(x0, y0, x0 + gw, y0, strokeColor=colors.grey))
    G.add(Line(x0, y0, x0, y0 + gh, strokeColor=colors.grey))
    for a in anos_s:
        if a % 2 == 0:
            G.add(String(xa(a) - 6, y0 - 12, str(a), fontName="DejaVu", fontSize=7))
    G.add(String(2, y0 + gh + 4, f"{mx:.1f}", fontName="DejaVu", fontSize=7))
    pts_s = [c for a, v in zip(anos_s, vals_s) if v is not None for c in (xa(a), ya(v))]
    pts_n = [c for a, v in zip(anos_n, vals_n) if v is not None for c in (xa(a), ya(v))]
    G.add(PolyLine(pts_s, strokeColor=colors.HexColor("#9fb3cf"), strokeWidth=1.5, strokeDashArray=[4, 3]))
    G.add(PolyLine(pts_n, strokeColor=colors.HexColor("#ffd166"), strokeWidth=2))
    el += [Paragraph("Evolução histórica (média municipal, nW·cm⁻²·sr⁻¹)", h2), G,
           Paragraph("NOAA-20 em amarelo (2018–2025, primário); S-NPP tracejado (2012–2025). S-NPP tem ruído em áreas escuras a partir de 2022.", base)]
    # pixels
    rows = [["Classe de luz", "Pixels", "% válidos"]] + [
        [d["rotulos"][k - d["primeira"]], inteiro(cont[k]), f"{fmt(100 * cont[k] / validos if validos else None, 1)} %"]
        for k in range(d["primeira"], 8)]
    tp = Table(rows, colWidths=[7 * cm, 3.5 * cm, 3.5 * cm])
    tp.setStyle(TableStyle([("FONT", (0, 0), (-1, -1), "DejaVu", 8.5), ("FONT", (0, 0), (-1, 0), "DejaVu-Bold", 8.5),
                            ("GRID", (0, 0), (-1, -1), 0.25, colors.grey), ("ALIGN", (1, 1), (-1, -1), "RIGHT")]))
    el += [Paragraph(f"Distribuição espacial dos pixels ({ano})", h2), tp,
           Paragraph("Contagem pelo centro de cada pixel (≈ 460 m) dentro do polígono municipal. Classes de luz, não valores de radiância.", base)]
    el += [Paragraph("Metodologia", h2), Paragraph("Média e percentis dos pixels válidos (qualidade 0, máscara de terra), agregação por fração de cobertura. Tendências com Theil–Sen e Kendall, mínimo de 8 anos. Limitações completas em metodologia.html. Radiância do sensor orbital não é o brilho do céu.", base)]
    fontes = [s["name"] + " — " + s.get("doi", "") for s in N["meta"]["sources"]]
    fontes += ["IBGE, Malha Municipal Digital 2024 (RJ): área e limites.", "IBGE, Censo Demográfico 2022, SIDRA 4709 v93: população."]
    el += [Paragraph("Fontes", h2)] + [Paragraph("• " + html.escape(f), base) for f in fontes]
    el += [Paragraph("Versão dos dados", h2),
           Paragraph(f"Dados processados em {html.escape(d['processado'])} (UTC) · código {html.escape(d['versao'])}. Relatório gerado a partir dos arquivos publicados; nenhum valor é preenchido manualmente.", base)]
    doc.build(el)


def indice_html(municipios):
    linhas = "".join(
        f'<tr><td><a href="municipio/{s}.html">{html.escape(n)}</a></td><td><a href="municipio/{s}.pdf" download>PDF</a></td></tr>'
        for n, s in municipios)
    return f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Municípios — OpenLux</title><meta name="description" content="Página individual dos 92 municípios do Rio de Janeiro, com relatório em PDF.">
<link rel="icon" href="data:,"><link rel="stylesheet" href="css/prototipo.css"><link rel="stylesheet" href="css/paginas.css">
<style>{CSS_PAG}</style></head>
<body class="pagina">{cabecalho("")}
<main><h1>Municípios</h1>
<p>Página individual de cada um dos 92 municípios, com indicadores, série 2018–2025, ranking, distribuição de pixels e relatório em PDF.</p>
<div class="bloco tabela-wrap"><table class="tab"><thead><tr><th>Município</th><th>Relatório</th></tr></thead><tbody>{linhas}</tbody></table></div>
</main></body></html>
"""


def main():
    N, S, perc, grade, cat, malha = carregar()
    ano = N["meta"]["years"][-1]
    contagens, rotulos, primeira = contagens_pixels(malha, grade, ano)
    # desenho: geometria simplificada (tolerância 0,002°, ≈ 220 m, abaixo de 1 px na tela de 420 px);
    # a contagem de pixels acima usa a geometria original
    malha_desenho = malha.copy()
    malha_desenho["geometry"] = malha.geometry.simplify(0.002, preserve_topology=True)
    OUT.mkdir(parents=True, exist_ok=True)
    for f in OUT.glob("*"):
        f.unlink()
    nomes = []
    for cd in N["municipios"]:
        d = dados_municipio(cd, N, S, perc, contagens, rotulos, primeira, ano)
        s = slug(d["nome"])
        nomes.append((d["nome"], s))
        geo = mapa_svg(malha_desenho, cd)
        (OUT / f"{s}.html").write_text(pagina_html(d, N, True, malha, geo), encoding="utf-8")
        pdf(d, N, malha_desenho, OUT / f"{s}.pdf")
    (WEB / "municipios.html").write_text(indice_html(sorted(nomes)), encoding="utf-8")
    print(f"OK: {len(nomes)} páginas e relatórios em {OUT}")


if __name__ == "__main__":
    main()
