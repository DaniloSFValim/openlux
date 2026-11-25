"""Gera os arquivos para download do site a partir de web/data/indicators.json (sem rodar o pipeline).

Saídas em web/data/downloads/:
- openlux_municipios_snpp_serie.csv   : uma linha por município e ano (S-NPP, 2012–2025)
- openlux_municipios_snpp_resumo.csv  : uma linha por município (população, intensidade por habitante, tendências)
- metadata.json                       : licença, citação, ressalvas e SHA-256 dos arquivos acima

A licença dos arquivos é uma PROPOSTA a confirmar pelo autor (ver LICENSE_DATA abaixo).
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "web" / "data" / "indicators.json"
OUT = ROOT / "web" / "data" / "downloads"

LICENSE_DATA = {
    "id": "CC-BY-4.0",
    "url": "https://creativecommons.org/licenses/by/4.0/",
    "status": "confirmada pelo autor em 2026-11-25",
    "nota": "Dados derivados de NASA (política ESDIS, sem restrição) e IBGE (reuso com citação). "
            "CC BY 4.0 exige apenas a atribuição indicada em 'citacao'.",
}

CAVEATS = [
    "Resultados não validados em campo. Estimativas baseadas em sensoriamento remoto; não são medições do brilho do céu.",
    "O sensor Suomi NPP (VNP46A4) tem mais ruído em áreas escuras desde 2022. Não interpretar as diferenças entre "
    "2021 e 2022 como mudança real de iluminação sem essa ressalva. A causa não foi separada de um possível artefato do algoritmo.",
    "A população é a do Censo 2022 em todos os anos (repartição simples). Não é exposição individual.",
    "Os valores são agregados municipais; não há dados brutos de radiância por pixel neste arquivo.",
]

CITACAO = (
    "Valim, D. (2026). OpenLux: versão 0.1.0 [Software]. Zenodo. https://doi.org/10.5281/zenodo.24510755. "
    "Dados de radiância: VIIRS Land SIPS Processing Group, VIIRS/NPP Lunar BRDF-Adjusted Nighttime Lights Yearly L3 "
    "Global 15 arc second Linear Lat Lon Grid [Dataset], NASA LAADS DAAC, https://doi.org/10.5067/VIIRS/VNP46A4.002. "
    "Malha municipal: IBGE, Malha Municipal Digital 2024 (UF RJ). População: IBGE, Censo Demográfico 2022, "
    "SIDRA tabela 4709, variável 93."
)

SERIE_COLS = [
    ("cod_municipio", "cod_municipio"),
    ("municipio", "municipio"),
    ("ano", "ano"),
    ("radiancia_media_nW_cm-2_sr-1", "mean"),
    ("radiancia_mediana_nW_cm-2_sr-1", "median"),
    ("fracao_area_valida", "valid"),
    ("fracao_area_iluminada_limiar_0.5_nW_cm-2_sr-1", "lit"),
    ("intensidade_radiante_aparente_nW_sr-1", "intensity_nw_sr"),
]


def _sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _num(v):
    return "" if v is None else v


def build(src: Path = SRC, out: Path = OUT) -> dict:
    data = json.loads(src.read_text(encoding="utf-8"))
    years = data["meta"]["years"]
    munis = data["municipios"]
    out.mkdir(parents=True, exist_ok=True)

    serie = out / "openlux_municipios_snpp_serie.csv"
    with serie.open("w", encoding="utf-8-sig", newline="") as f:  # BOM: abre certo no Excel
        w = csv.writer(f)
        w.writerow([h for h, _ in SERIE_COLS])
        for cod in sorted(munis):
            m = munis[cod]
            for i, ano in enumerate(years):
                row = []
                for _, key in SERIE_COLS:
                    if key == "cod_municipio":
                        row.append(cod)
                    elif key == "municipio":
                        row.append(m["name"])
                    elif key == "ano":
                        row.append(ano)
                    else:
                        vals = m.get(key)
                        row.append(_num(vals[i]) if vals else "")
                w.writerow(row)

    resumo = out / "openlux_municipios_snpp_resumo.csv"
    windows = ["2012_2021", "2012_2025"]
    cols = ["cod_municipio", "municipio", "populacao_2022", "intensidade_por_habitante_mW_sr-1_hab-1"]
    for win in windows:
        cols += [f"tendencia_{win}_inclinacao_nW_cm-2_sr-1_por_ano", f"tendencia_{win}_p_valor_kendall",
                 f"tendencia_{win}_mudanca_pct"]
    with resumo.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for cod in sorted(munis):
            m = munis[cod]
            row = [cod, m["name"], _num(m.get("population")), _num(m.get("per_capita_mw_sr_hab"))]
            for win in windows:
                t = (m.get("trends") or {}).get(win) or {}
                row += [_num(t.get("slope")), _num(t.get("p_value")), _num(t.get("change_pct"))]
            w.writerow(row)

    meta = {
        "titulo": "OpenLux: indicadores municipais de radiância noturna (S-NPP, RJ)",
        "versao_software": "0.1.0",
        "doi_versao": "10.5281/zenodo.24510755",
        "doi_conceito": "10.5281/zenodo.24510754",
        "codigo_commit": data["meta"]["run"]["code_commit"],
        "processado_utc": data["meta"]["run"]["processed_utc"],
        "cobertura": {"municipios": len(munis), "anos": [years[0], years[-1]]},
        "licenca": LICENSE_DATA,
        "citacao": CITACAO,
        "unidades": {
            "radiancia": "nW·cm⁻²·sr⁻¹ (média e mediana anuais dos pixels válidos, ponderadas pela área)",
            "intensidade_radiante_aparente": "nW·sr⁻¹",
            "tendencia_inclinacao": "inclinação de Theil–Sen da radiância média, nW·cm⁻²·sr⁻¹ por ano",
            "tendencia_mudanca_pct": "100 × (L̄(t2) − L̄(t1)) / L̄(t1), em %",
            "tendencia_p_valor": "teste de Kendall sobre a mesma série (sem correção de múltiplas janelas)",
            "fracao": "adimensional, de 0 a 1",
        },
        "ressalvas": CAVEATS,
        "arquivos": {p.name: {"sha256": _sha256(p), "bytes": p.stat().st_size} for p in (serie, resumo)},
    }
    (out / "metadata.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return meta


def build_noaa20(src: Path = Path("web/data/indicators_noaa20.json"), out: Path = Path("web/data/downloads/revisao_noaa20")) -> dict:
    """Arquivos de REVISAO do NOAA-20 (2018-2025). Nao substituem os arquivos publicados do S-NPP.
    Gerados a partir de web/data/indicators_noaa20.json (saida de scripts/build_web_data_noaa20.py)."""
    data = json.loads(src.read_text(encoding="utf-8"))
    years = data["meta"]["years"]
    munis = data["municipios"]
    out.mkdir(parents=True, exist_ok=True)
    serie = out / "openlux_municipios_noaa20_serie.csv"
    with serie.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow([h for h, _ in SERIE_COLS])
        for cod in sorted(munis):
            m = munis[cod]
            for i, ano in enumerate(years):
                row = []
                for _, key in SERIE_COLS:
                    if key == "cod_municipio":
                        row.append(cod)
                    elif key == "municipio":
                        row.append(m["name"])
                    elif key == "ano":
                        row.append(ano)
                    else:
                        vals = m.get(key)
                        row.append(_num(vals[i]) if vals else "")
                w.writerow(row)
    resumo = out / "openlux_municipios_noaa20_resumo.csv"
    windows = ["2018_2025"]
    cols = ["cod_municipio", "municipio", "populacao_2022", "intensidade_por_habitante_mW_sr-1_hab-1"]
    for win in windows:
        cols += [f"tendencia_{win}_inclinacao_nW_cm-2_sr-1_por_ano", f"tendencia_{win}_p_valor_kendall", f"tendencia_{win}_mudanca_pct"]
    with resumo.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for cod in sorted(munis):
            m = munis[cod]
            row = [cod, m["name"], _num(m.get("population")), _num(m.get("per_capita_mw_sr_hab"))]
            for win in windows:
                t = (m.get("trends") or {}).get(win) or {}
                row += [_num(t.get("slope")), _num(t.get("p_value")), _num(t.get("change_pct"))]
            w.writerow(row)
    return {p.name: {"sha256": _sha256(p), "bytes": p.stat().st_size} for p in (serie, resumo)}


if __name__ == "__main__":
    m = build()
    print(json.dumps(m["arquivos"], ensure_ascii=False, indent=2))
    print(json.dumps(build_noaa20(), ensure_ascii=False, indent=2))
