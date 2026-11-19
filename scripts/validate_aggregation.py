#!/usr/bin/env python3
"""Estabilidade dos indicadores municipais frente ao criterio de agregacao e a resolucao.

Compara, por ano, a media municipal da configuracao principal (cobertura fracionaria, grade
original de 15 arc-s) com (a) criterio de centro do pixel e (b) grade agregada 2x2 e 4x4.
Reporta distribuicoes de diferenca; NAO define limite de aprovacao.
"""
import glob
import re
from pathlib import Path

import geopandas as gpd
import numpy as np

from openlux.io import read_blackmarble
from openlux.provenance import write_json
from openlux.validation import centroid_zonal_mean, coarsen
from openlux.zonal import zonal_indicators
from openlux.temporal import rank_agreement

RAW = Path("data/raw")


def summarize(base, other, floor):
    ok = np.isfinite(base) & np.isfinite(other)
    big = ok & (base >= floor)
    rel = np.abs(other - base)[big] / base[big]
    return dict(n_compared=int(ok.sum()), n_nan_other=int((np.isfinite(base) & ~np.isfinite(other)).sum()),
                spearman=rank_agreement(base[ok], other[ok]),
                max_abs_diff_nw=float(np.abs(other - base)[ok].max()),
                median_rel_diff=float(np.median(rel)), p95_rel_diff=float(np.quantile(rel, 0.95)),
                max_rel_diff=float(rel.max()), n_rel=int(big.sum()))


def main():
    mun = gpd.read_file(next(glob.iglob(str(RAW / "ibge/RJ_Municipios_2024/*.shp")))).set_crs(
        "EPSG:4326", allow_override=True)[["CD_MUN", "AREA_KM2", "geometry"]]
    files = {int(re.search(r"\.A(\d{4})001\.", p).group(1)): p
             for p in sorted(glob.glob(str(RAW / "VNP46A4/*.h5")))}
    out = {}
    # Consistencia raster x vetor: area dos pixels ponderada pela cobertura vs AREA_KM2 do IBGE.
    _, t0 = read_blackmarble(next(iter(files.values())))
    ones = np.ones((2400, 2400), dtype="float32")
    km2 = zonal_indicators(ones, t0, mun)["apparent_radiant_intensity_nw_sr"].to_numpy() / 1e10
    rel = (km2 - mun["AREA_KM2"].to_numpy()) / mun["AREA_KM2"].to_numpy()
    out["area_raster_vs_ibge"] = dict(max_abs_rel_diff=float(np.abs(rel).max()), median_rel_diff=float(np.median(rel)),
                                      soma_km2_raster=float(km2.sum()), soma_km2_ibge=float(mun["AREA_KM2"].sum()))
    for y in sorted(files):
        arr, t = read_blackmarble(files[y])
        base = zonal_indicators(arr, t, mun)["mean_radiance"].to_numpy()
        floor = float(np.nanquantile(base, 0.25))  # mesmo criterio do piso de variacao (declarado)
        res = {"centroide": summarize(base, centroid_zonal_mean(arr, t, mun), floor)}
        for k in (2, 4):
            ca, ct = coarsen(arr, t, k)
            res[f"grade_{k}x{k}"] = summarize(base, zonal_indicators(ca, ct, mun)["mean_radiance"].to_numpy(), floor)
        res["piso_nw_cm2_sr"] = floor
        out[str(y)] = res
    Path("outputs/validation").mkdir(parents=True, exist_ok=True)
    write_json("outputs/validation/aggregation_stability.json", out)
    print("area:", out["area_raster_vs_ibge"])
    for y in ("2012", "2023", "2025"):
        print(y, {k: (round(v["spearman"], 4), round(v["median_rel_diff"], 4), round(v["p95_rel_diff"], 4), round(v["max_rel_diff"], 4), v["n_nan_other"])
                  for k, v in out[y].items() if k != "piso_nw_cm2_sr"})


if __name__ == "__main__":
    main()
