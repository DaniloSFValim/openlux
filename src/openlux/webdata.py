"""Dados estaticos da interface web, gerados SOMENTE a partir das saidas reais do pipeline.

Nada aqui cria valores: so reorganiza, arredonda e converte NaN em ``null`` (JSON estrito).
A geometria e simplificada apenas para exibicao; todos os calculos usaram a geometria
completa da malha do IBGE.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd
from shapely.geometry import mapping

SOURCES = [
    dict(name="NASA Black Marble VNP46A4 v2.0 (Suomi NPP, anual)",
         institution="NASA / LAADS DAAC", doi="10.5067/VIIRS/VNP46A4.002",
         url="https://ladsweb.modaps.eosdis.nasa.gov/missions-and-measurements/products/VNP46A4",
         version="Colecao 2.0 (versao 002), tile h13v11, 2012-2025",
         license="Politica ESDIS da NASA: dados de missoes lideradas pela NASA sem marcacao de restricao sao CC0; "
                 "citacao solicitada.",
         license_status="confirmado_com_ressalva",
         note="Texto oficial lido; os arquivos nao trazem marcacao de restricao. Ressalva: o enquadramento "
              "como missao liderada pela NASA e interpretacao do autor."),
    dict(name="NASA Black Marble VJ146A4 v2.0 (NOAA-20, anual)",
         institution="NASA / LAADS DAAC", doi="10.5067/VIIRS/VJ146A4.002",
         url="https://ladsweb.modaps.eosdis.nasa.gov/api/v2/content/details/allData/5200/VJ146A4",
         version="Colecao 2.0 (versao 002), tile h13v11, 2018-2025 (comparacao entre sensores)",
         license="Politica ESDIS da NASA: dados de missoes lideradas pela NASA sem marcacao de restricao sao CC0; "
                 "citacao solicitada.",
         license_status="confirmado_com_ressalva",
         note="Texto oficial lido; os arquivos nao trazem marcacao de restricao. Ressalva: o enquadramento "
              "como missao liderada pela NASA e interpretacao do autor."),
    dict(name="Malha Municipal Digital 2024 (RJ)", institution="IBGE",
         url="https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/"
             "malhas_municipais/municipio_2024/UFs/RJ/RJ_Municipios_2024.zip",
         version="2024 (SIRGAS 2000, EPSG:4674)",
         license="Licenca compativel com Creative Commons BY 4.0 (Notas Metodologicas 01/2025); "
                 "credito ao IBGE; isencao de responsabilidade.",
         license_status="confirmado", note=""),
    dict(name="Censo Demografico 2022: populacao residente (SIDRA, tabela 4709, variavel 93)",
         institution="IBGE", url="https://apisidra.ibge.gov.br/values/t/4709/n6/in%20n3%2033/v/93/p/2022",
         version="Censo 2022", license="Reuso permitido com citacao da fonte (IBGE).",
         license_status="confirmado",
         note="Conferido pelo autor nos termos do IBGE/SIDRA em 2026-11-19; o texto nao foi lido por ferramenta automatizada."),
]

DOCS = [
    dict(name="Black Marble User Guide, Version 2.0 (outubro de 2024)", institution="NASA",
         url="https://ladsweb.modaps.eosdis.nasa.gov/api/v2/content/archives/Document%20Archive/"
             "Science%20Data%20Product%20Documentation/Black-Marble_v2.0_UG_2024.pdf"),
    dict(name="Notas Metodologicas 01/2025: Malha Municipal Digital e Areas Territoriais 2024",
         institution="IBGE", url="https://biblioteca.ibge.gov.br/visualizacao/livros/liv102169.pdf"),
]

REFERENCES = [
    dict(cite="Roman, M. O. et al. (2018). NASA's Black Marble nighttime lights product suite. "
              "Remote Sensing of Environment, 210, 113-143.",
         doi="10.1016/j.rse.2018.03.017"),
    dict(cite="Wang, Z.; Shrestha, R. M.; Roman, M. O.; Kalb, V. L. (2022). NASA's Black Marble "
              "multiangle nighttime lights temporal composites. IEEE Geoscience and Remote "
              "Sensing Letters.", doi="10.1109/LGRS.2022.3176616"),
    dict(cite="Levin, N. et al. (2020). Remote sensing of night lights: a review and an outlook "
              "for the future. Remote Sensing of Environment, 237, 111443.",
         doi="10.1016/j.rse.2019.111443"),
]


def _clean(x, nd=6):
    """float/NaN/inf -> float arredondado ou None; tipos numpy -> nativos."""
    if x is None:
        return None
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (float, np.floating)):
        x = float(x)
        return None if (math.isnan(x) or math.isinf(x)) else round(x, nd)
    return x


def simplify_geojson(gdf, *, tolerance=0.001, ndigits=4) -> dict:
    """GeoJSON simplificado (so para exibicao) com apenas CD_MUN e NM_MUN."""
    feats = []
    for _, r in gdf.iterrows():
        geom = r.geometry.simplify(tolerance, preserve_topology=True)
        m = mapping(geom)

        def rnd(c):
            return [rnd(i) for i in c] if isinstance(c[0], (list, tuple)) else \
                [round(v, ndigits) for v in c]
        m = {"type": m["type"], "coordinates": rnd(m["coordinates"])}
        feats.append({"type": "Feature", "properties": {"CD_MUN": str(r.CD_MUN), "NM_MUN": r.NM_MUN},
                      "geometry": m})
    return {"type": "FeatureCollection", "features": feats}


def build_indicators(*, annual, trends, qa, sensitivity, sensor_comparison, run_record,
                     id_col="CD_MUN", name_col="NM_MUN", sensor_municipal=None, sensor_summary=None) -> dict:
    years = sorted(int(y) for y in annual["year"].unique())
    params = run_record["parameters"]
    muni = {}
    for cd, g in annual.groupby(id_col, sort=True):
        g = g.sort_values("year").set_index("year").reindex(years)
        tr = trends[trends[id_col] == cd]
        first = tr.iloc[0] if len(tr) else None
        muni[str(cd)] = dict(
            name=annual.loc[annual[id_col] == cd, name_col].iloc[0],
            mean=[_clean(v) for v in g["mean_radiance"]],
            median=[_clean(v) for v in g["median_radiance"]],
            valid=[_clean(v, 4) for v in g["valid_fraction"]],
            lit=[_clean(v, 4) for v in g["frac_above_lit_0p5"]] if "frac_above_lit_0p5" in g else None,
            intensity_nw_sr=[_clean(v, 3) for v in g["apparent_radiant_intensity_nw_sr"]],
            population=_clean(first["population"]) if first is not None else None,
            per_capita_mw_sr_hab=_clean(first["intensity_per_capita_mw_sr_hab"], 3)
            if first is not None else None,
            trends={r["window"]: dict(
                slope=_clean(r["slope"]), p_value=_clean(r["p_value"]), tau=_clean(r["tau"]),
                n_years=_clean(r["n_years"]), change_abs=_clean(r["change_abs"]),
                change_pct=_clean(r["change_pct"], 3)) for _, r in tr.iterrows()},
        )
    if sensor_municipal is not None:  # comparacao municipal S-NPP (a) x NOAA-20 (b), janela 2018-2025
        for _, r in sensor_municipal.iterrows():
            muni[str(r[id_col])]["sensors"] = dict(
                slope_snpp=_clean(r["slope_a"]), p_snpp=_clean(r["p_a"]), slope_noaa20=_clean(r["slope_b"]),
                p_noaa20=_clean(r["p_b"]), change_snpp=_clean(r.get("change_a")),
                change_noaa20=_clean(r.get("change_b")), ratio_noaa20_over_snpp=_clean(r["mean_ratio_b_over_a"], 4))
    w = annual.copy()
    w["wm"] = w["mean_radiance"] * w["weight_sum"]
    state_mean = []
    for y in years:
        s = w[w.year == y]
        state_mean.append(_clean(s["wm"].sum() / s["weight_sum"].sum()))
    return dict(
        meta=dict(
            years=years,
            windows={k: list(v) for k, v in params["trend_windows"].items()},
            change_floor_nw_cm2_sr={k: _clean(v) for k, v in params["change_floor_nw_cm2_sr"].items()},
            thresholds_nw_cm2_sr={k: _clean(v) for k, v in params.get("thresholds_nw_cm2_sr", {}).items()},
            run=dict(processed_utc=run_record["processed_utc"],
                     code_commit=run_record["code"]["commit"], code_dirty=run_record["code"]["dirty"],
                     output_sha256=run_record["outputs"]),
            sources=SOURCES, documents=DOCS, references=REFERENCES,
        ),
        state=dict(mean=state_mean),
        municipios=muni,
        qa=[{k: _clean(v, 5) for k, v in r.items()} for r in qa.to_dict("records")],
        sensitivity=_scrub(sensitivity),
        sensor_comparison=_scrub(sensor_comparison),
        sensor_municipal=_scrub(sensor_summary) if sensor_summary is not None else None,
    )


def _scrub(o):
    if isinstance(o, dict):
        return {str(k): _scrub(v) for k, v in o.items()}
    if isinstance(o, list):
        return [_scrub(v) for v in o]
    return _clean(o)
