"""Setores censitarios do Censo 2022 (IBGE): sobreposicao com a grade e indicadores.

Duas ideias, ambas com a limitacao de que a populacao e fixa (Censo 2022):

1. **Exposicao populacional.** A populacao de cada setor e repartida entre os pixels que ele cobre,
   proporcionalmente a fracao de cobertura (ponderacao areal simples, sem dasimetria). A radiancia
   ponderada pela populacao de um municipio e sum(pop_i * L_i) / sum(pop_i) sobre pixels validos.
   Responde "que radiancia a populacao do municipio habita", e NAO mede exposicao individual.
2. **Urbano x rural.** Radiancia media e fracao iluminada nas areas dos setores classificados pelo IBGE
   como Urbana e Rural (campo SITUACAO), ponderadas pela cobertura de cada pixel.

Cuidados: (a) a malha tem uma linha por poligono, e 133 setores multipoligonais aparecem em varias
linhas, cada uma com a populacao inteira; por isso os setores sao agrupados por ``CD_SETOR`` antes de
qualquer soma (a soma dos 41.700 setores do RJ reproduz os 92 municipios do SIDRA sem diferenca);
(b) setores menores que um pixel (~0,21 km2) compartilham pixels; (c) a malha SIRGAS 2000 e tratada como
WGS84, como no restante do projeto.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from exactextract import exact_extract
from rasterio.io import MemoryFile
from shapely import make_valid
from shapely.geometry import MultiPolygon, Polygon


def _polygons_only(geom):
    """Mantem so as partes poligonais (make_valid pode devolver linhas/pontos)."""
    if geom is None or geom.is_empty:
        return geom
    if geom.geom_type in ("Polygon", "MultiPolygon"):
        return geom
    parts = [g for g in getattr(geom, "geoms", []) if g.geom_type in ("Polygon", "MultiPolygon")]
    flat = []
    for p in parts:
        flat.extend(p.geoms if p.geom_type == "MultiPolygon" else [p])
    return MultiPolygon(flat) if len(flat) > 1 else (flat[0] if flat else Polygon())


def dedupe_sectors(gdf):
    """Um registro por ``CD_SETOR``: populacao (``v0001``) tomada uma vez, geometrias unidas e reparadas."""
    g = gdf.copy()
    g["pop"] = pd.to_numeric(g["v0001"], errors="coerce").fillna(0.0)
    g["geometry"] = g.geometry.apply(lambda x: _polygons_only(make_valid(x)))
    d = g.dissolve(by="CD_SETOR", aggfunc={"pop": "first", "CD_MUN": "first", "SITUACAO": "first",
                                           "CD_SIT": "first"}).reset_index()
    d["geometry"] = d.geometry.apply(_polygons_only)
    d["CD_SETOR"] = d["CD_SETOR"].astype(str)
    d["CD_MUN"] = d["CD_MUN"].astype(str)
    return d.set_crs("EPSG:4326", allow_override=True)  # SIRGAS 2000 ~ WGS84 (poucos metros)


def sector_overlay(sectors, shape, transform) -> pd.DataFrame:
    """Tabela (setor, pixel): cobertura do pixel pelo setor e parcela da populacao do setor no pixel.

    ``pop`` e a populacao do setor dividida entre os pixels cobertos, proporcionalmente a ``cov``;
    a soma por setor conserva a populacao. Setores sem nenhum pixel na grade ficam de fora e sua
    populacao e informada em ``attrs['population_outside_grid']``.
    """
    nrows, ncols = shape
    profile = dict(driver="GTiff", height=nrows, width=ncols, count=1, dtype="float32", crs="EPSG:4326",
                   transform=transform)
    with MemoryFile() as mem:
        with mem.open(**profile) as ds:
            ds.write(np.zeros(shape, dtype="float32"), 1)
        with mem.open() as ds:
            out = exact_extract(ds, sectors, ["cell_id", "coverage"], output="pandas")
    ids, muns, sits, pix, cov, pop = [], [], [], [], [], []
    outside = 0.0
    for i, r in enumerate(sectors.itertuples(index=False)):
        c = np.asarray(out.iloc[i]["coverage"], dtype="float64")
        cell = np.asarray(out.iloc[i]["cell_id"], dtype="int64")
        keep = c > 0
        c, cell = c[keep], cell[keep]
        if c.sum() <= 0:
            outside += float(r.pop)
            continue
        ids.extend([r.CD_SETOR] * len(c)); muns.extend([r.CD_MUN] * len(c)); sits.extend([r.SITUACAO] * len(c))
        pix.append(cell); cov.append(c); pop.append(float(r.pop) * c / c.sum())
    df = pd.DataFrame({"CD_SETOR": ids, "CD_MUN": muns, "SITUACAO": sits,
                       "pix": np.concatenate(pix) if pix else np.array([], dtype="int64"),
                       "cov": np.concatenate(cov) if cov else np.array([]),
                       "pop": np.concatenate(pop) if pop else np.array([])})
    df.attrs["population_outside_grid"] = outside
    return df


def sector_indicators(overlay: pd.DataFrame, radiance: np.ndarray, tau: float = 0.5) -> pd.DataFrame:
    """Indicadores por municipio para uma camada de radiancia (NaN nos pixels invalidos).

    Colunas: pop_weighted_radiance, pop_lit_fraction (populacao em pixels com L >= tau),
    pop_valid_fraction, mean_urban / mean_rural, frac_lit_urban / frac_lit_rural (ponderados pela cobertura),
    urban_weight / rural_weight (cobertura valida acumulada) e population.
    """
    flat = np.asarray(radiance, dtype="float64").ravel()
    d = overlay[["CD_MUN", "SITUACAO", "pix", "cov", "pop"]].copy()
    L = flat[d["pix"].to_numpy()]
    valid = np.isfinite(L)
    Lv = np.where(valid, L, 0.0)
    lit = valid & (L >= tau)
    d["pop_valid"] = d["pop"] * valid
    d["pop_L"] = d["pop"] * Lv
    d["pop_lit"] = d["pop"] * lit
    for tag, sit in (("urban", "Urbana"), ("rural", "Rural")):
        m = (d["SITUACAO"] == sit) & valid
        d[f"{tag}_w"] = np.where(m, d["cov"], 0.0)
        d[f"{tag}_wL"] = np.where(m, d["cov"] * Lv, 0.0)
        d[f"{tag}_wlit"] = np.where(m & lit, d["cov"], 0.0)
    s = d.groupby("CD_MUN", sort=True).sum(numeric_only=True)
    with np.errstate(divide="ignore", invalid="ignore"):
        out = pd.DataFrame({
            "population": s["pop"],
            "pop_valid_fraction": s["pop_valid"] / s["pop"],
            "pop_weighted_radiance": s["pop_L"] / s["pop_valid"],
            "pop_lit_fraction": s["pop_lit"] / s["pop_valid"],
            "mean_urban": s["urban_wL"] / s["urban_w"], "mean_rural": s["rural_wL"] / s["rural_w"],
            "frac_lit_urban": s["urban_wlit"] / s["urban_w"], "frac_lit_rural": s["rural_wlit"] / s["rural_w"],
            "urban_weight": s["urban_w"], "rural_weight": s["rural_w"],
        })
    out = out.replace([np.inf, -np.inf], np.nan)
    out.loc[s["pop_valid"] == 0, ["pop_weighted_radiance", "pop_lit_fraction"]] = np.nan
    out.loc[s["urban_w"] == 0, ["mean_urban", "frac_lit_urban"]] = np.nan
    out.loc[s["rural_w"] == 0, ["mean_rural", "frac_lit_rural"]] = np.nan
    return out.reset_index()
