#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gera as figuras (SVG vetorial) do artigo a partir dos dados reais do parque
(consultados em produção via Supabase em 2026-07-11) e do modelo fotométrico
de primeira ordem. Sem dependências externas — emite SVG diretamente.

Paleta CVD-safe (Okabe–Ito), validada pelo skill dataviz:
  azul #0072B2 · vermilion #D55E00 · verde #009E73
"""
import math, os

OUT = os.path.dirname(os.path.abspath(__file__))
INK, MUTED, GRID, SURF = "#1a1a1a", "#666666", "#e6e6e6", "#ffffff"
BLUE, VERM, GREEN = "#0072B2", "#D55E00", "#009E73"
FONT = "font-family='Helvetica,Arial,sans-serif'"

def esc(s): return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def svg_open(w, h, title):
    return (f"<svg xmlns='http://www.w3.org/2000/svg' width='{w}' height='{h}' "
            f"viewBox='0 0 {w} {h}' font-size='13'>\n"
            f"<rect width='{w}' height='{h}' fill='{SURF}'/>\n"
            f"<text x='{w/2}' y='24' text-anchor='middle' {FONT} font-size='15' "
            f"font-weight='700' fill='{INK}'>{esc(title)}</text>\n")

def save(name, body):
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        f.write(body + "</svg>\n")
    print("wrote", name)

# ---------------------------------------------------------------- Fig 1
# Luminárias por tipo de lâmpada (barras horizontais). LED destacado.
def fig1():
    data = [("Vapor de sódio", 21207, BLUE), ("LED", 16667, GREEN),
            ("Metálico", 4462, BLUE), ("Fluorescente", 273, BLUE),
            ("Sem lâmpada", 55, BLUE), ("Desconhecido", 51, BLUE),
            ("Vapor de mercúrio", 50, BLUE)]
    W, H = 730, 300; x0, y0 = 170, 44; bw = 385; rh, gap = 26, 8
    mx = max(v for _, v, _ in data)
    s = svg_open(W, H, "Composição do parque por tipo de lâmpada (n=42.765)")
    for i, (lab, v, col) in enumerate(data):
        y = y0 + i*(rh+gap); w = max(2, bw*v/mx)
        s += f"<text x='{x0-8}' y='{y+rh/2+4}' text-anchor='end' {FONT} fill='{INK}'>{esc(lab)}</text>\n"
        s += f"<rect x='{x0}' y='{y}' width='{w:.1f}' height='{rh}' rx='4' fill='{col}'/>\n"
        pct = 100*v/42765
        s += (f"<text x='{x0+w+6}' y='{y+rh/2+4}' {FONT} fill='{MUTED}'>"
              f"{v:,}".replace(",", ".") + f" ({pct:.1f}%)</text>\n")
    s += (f"<text x='{x0}' y='{H-10}' {FONT} font-size='11' fill='{MUTED}'>"
          f"Fonte: base SECONSER/Censo ENEL · consulta em 2026-07-11</text>\n")
    save("fig1_tipo_lampada.svg", s)

# ---------------------------------------------------------------- Fig 2
# % LED nos 15 maiores bairros — heterogeneidade espacial.
def fig2():
    data = [("Fonseca",3589,49.4),("Piratininga",2953,47.8),("Icaraí",1943,38.9),
            ("Centro",1924,70.9),("São Francisco",1587,58.2),("Engenhoca",1578,38.5),
            ("Itaipu",1410,27.4),("Barreto",1382,54.0),("Engenho do Mato",1375,0.2),
            ("Santa Rosa",1370,24.0),("Maravista",1315,24.0),("Serra Grande",1300,0.8),
            ("Largo da Batalha",1029,48.7),("Santo Antônio",979,42.9),("Cantagalo",918,63.8)]
    W, H = 660, 470; x0, y0 = 150, 46; bw = 400; rh, gap = 20, 6
    s = svg_open(W, H, "Taxa de modernização LED nos 15 maiores bairros")
    # linha de referência: média do parque 39%
    xref = x0 + bw*39/100
    s += f"<line x1='{xref}' y1='{y0-6}' x2='{xref}' y2='{y0+len(data)*(rh+gap)}' stroke='{VERM}' stroke-width='1.5' stroke-dasharray='4,3'/>\n"
    s += f"<text x='{xref}' y='{y0-10}' text-anchor='middle' {FONT} font-size='11' fill='{VERM}'>média 39%</text>\n"
    for i, (lab, n, pct) in enumerate(data):
        y = y0 + i*(rh+gap); w = max(2, bw*pct/100)
        s += f"<text x='{x0-8}' y='{y+rh/2+4}' text-anchor='end' {FONT} font-size='12' fill='{INK}'>{esc(lab)}</text>\n"
        s += f"<rect x='{x0}' y='{y}' width='{w:.1f}' height='{rh}' rx='3' fill='{GREEN}'/>\n"
        s += f"<text x='{x0+w+6}' y='{y+rh/2+4}' {FONT} font-size='11' fill='{MUTED}'>{pct:.1f}%</text>\n"
    s += (f"<text x='{x0}' y='{H-12}' {FONT} font-size='11' fill='{MUTED}'>"
          f"Barra = % de pontos modernizados; rótulo à direita. Heterogeneidade de 0,2% a 70,9%.</text>\n")
    save("fig2_pct_led_bairro.svg", s)

# ---------------------------------------------------------------- Fig 3
# Modelo fotométrico de 1a ordem: eta_piso e P vs angulo (concreto, rho=0.30).
def fig3():
    W, H = 660, 380; x0, y0, pw, ph = 70, 56, 520, 250
    rho = 0.30
    def eta(t): return max(0.0, math.cos(math.radians(t)))
    def P(t):
        e = eta(t); return min(1.0, (1-e) + rho*e*0.5)
    s = svg_open(W, H, "Modelo de índices fotométricos vs. ângulo de apontamento (piso: concreto, ρ=0,30)")
    # eixos
    s += f"<line x1='{x0}' y1='{y0}' x2='{x0}' y2='{y0+ph}' stroke='{INK}' stroke-width='1'/>\n"
    s += f"<line x1='{x0}' y1='{y0+ph}' x2='{x0+pw}' y2='{y0+ph}' stroke='{INK}' stroke-width='1'/>\n"
    # grid + y ticks (0..1)
    for gy in range(0, 6):
        val = gy/5.0; yy = y0+ph - ph*val
        s += f"<line x1='{x0}' y1='{yy:.1f}' x2='{x0+pw}' y2='{yy:.1f}' stroke='{GRID}' stroke-width='1'/>\n"
        s += f"<text x='{x0-8}' y='{yy+4:.1f}' text-anchor='end' {FONT} font-size='11' fill='{MUTED}'>{val:.1f}</text>\n"
    # x ticks (0..120)
    xticks = [0,15,30,45,60,75,90,120]
    for t in xticks:
        xx = x0 + pw*t/120.0
        s += f"<line x1='{xx:.1f}' y1='{y0+ph}' x2='{xx:.1f}' y2='{y0+ph+5}' stroke='{INK}' stroke-width='1'/>\n"
        s += f"<text x='{xx:.1f}' y='{y0+ph+20}' text-anchor='middle' {FONT} font-size='11' fill='{MUTED}'>{t}°</text>\n"
    # curvas
    def path(fn, col):
        pts = []
        t = 0.0
        while t <= 120.0001:
            xx = x0 + pw*t/120.0; yy = y0+ph - ph*fn(t)
            pts.append(f"{xx:.1f},{yy:.1f}"); t += 1.0
        return f"<polyline fill='none' stroke='{col}' stroke-width='2.5' points='{' '.join(pts)}'/>\n"
    s += path(eta, BLUE)
    s += path(P, VERM)
    # marcadores nos ângulos preset
    for t in xticks:
        for fn, col in ((eta, BLUE), (P, VERM)):
            xx = x0 + pw*t/120.0; yy = y0+ph - ph*fn(t)
            s += f"<circle cx='{xx:.1f}' cy='{yy:.1f}' r='3' fill='{col}'/>\n"
    # legenda direta
    s += f"<circle cx='{x0+pw-150}' cy='{y0+8}' r='4' fill='{BLUE}'/><text x='{x0+pw-140}' y='{y0+12}' {FONT} font-size='12' fill='{INK}'>η_piso (aproveitamento)</text>\n"
    s += f"<circle cx='{x0+pw-150}' cy='{y0+26}' r='4' fill='{VERM}'/><text x='{x0+pw-140}' y='{y0+30}' {FONT} font-size='12' fill='{INK}'>P (poluição luminosa)</text>\n"
    # rótulos eixos
    s += f"<text x='{x0+pw/2}' y='{H-8}' text-anchor='middle' {FONT} font-size='12' fill='{INK}'>Ângulo de apontamento a partir do nadir (°)</text>\n"
    s += f"<text x='16' y='{y0+ph/2}' text-anchor='middle' {FONT} font-size='12' fill='{INK}' transform='rotate(-90 16 {y0+ph/2})'>Índice (0–1)</text>\n"
    save("fig3_modelo_fotometrico.svg", s)

# ---------------------------------------------------------------- Fig 4
# Distribuição de potência instalada (histograma por faixa).
def fig4():
    data = [("<70",6694),("70–99",14819),("100–149",3245),("150–249",10723),
            ("250–399",4121),("≥400",3107)]
    W, H = 660, 340; x0, y0, pw, ph = 60, 50, 560, 230
    mx = max(v for _, v in data); n = len(data); bw = pw/n*0.7; step = pw/n
    s = svg_open(W, H, "Distribuição da potência instalada por luminária (W)")
    for gy in range(0,5):
        val = mx*gy/4; yy = y0+ph - ph*(val/mx)
        s += f"<line x1='{x0}' y1='{yy:.1f}' x2='{x0+pw}' y2='{yy:.1f}' stroke='{GRID}' stroke-width='1'/>\n"
        s += f"<text x='{x0-8}' y='{yy+4:.1f}' text-anchor='end' {FONT} font-size='11' fill='{MUTED}'>{int(val/1000)}k</text>\n"
    for i,(lab,v) in enumerate(data):
        cx = x0 + step*i + (step-bw)/2; h = ph*v/mx; y = y0+ph-h
        s += f"<rect x='{cx:.1f}' y='{y:.1f}' width='{bw:.1f}' height='{h:.1f}' rx='4' fill='{BLUE}'/>\n"
        s += f"<text x='{cx+bw/2:.1f}' y='{y-6:.1f}' text-anchor='middle' {FONT} font-size='11' fill='{INK}'>{v:,}".replace(',', '.')+"</text>\n"
        s += f"<text x='{cx+bw/2:.1f}' y='{y0+ph+18}' text-anchor='middle' {FONT} font-size='11' fill='{MUTED}'>{esc(lab)}</text>\n"
    s += f"<text x='{x0+pw/2}' y='{H-8}' text-anchor='middle' {FONT} font-size='12' fill='{INK}'>Faixa de potência (W)</text>\n"
    save("fig4_potencia_dist.svg", s)

if __name__ == "__main__":
    fig1(); fig2(); fig3(); fig4()
    print("OK")
