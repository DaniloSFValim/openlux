#!/usr/bin/env python3
"""Sugere locais CANDIDATOS para a campanha de campo, estratificados pela radiancia de satelite do entorno.

Uso: python scripts/suggest_sites.py [--ufs RJ SP] [--sensor noaa20|snpp] [--year 2025] [--per-stratum 6] [--seed 0]
Apenas planejamento: acesso, seguranca e permissao nao sao conhecidos pelo satelite. Saidas em outputs/field/ (nao versionadas:
sao coordenadas de planejamento). A malha de cada UF vem de scripts/fetch_ibge.py (RJ) ou scripts/fetch_mesh.py --uf XX.
"""
import argparse
import glob
import re
import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd

from openlux.field import candidate_sites
from openlux.io import read_blackmarble, sha256_file
from openlux.log import JsonLogger
from openlux.pixelmap import LABELS, state_mask
from openlux.provenance import code_version, write_json

RAW, OUT = Path("data/raw"), Path("outputs/field")
PRODUCTS = {"noaa20": "VJ146A4", "snpp": "VNP46A4"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ufs", nargs="+", default=["RJ", "SP"])
    ap.add_argument("--sensor", choices=PRODUCTS, default="noaa20")
    ap.add_argument("--year", type=int, default=2025)
    ap.add_argument("--per-stratum", type=int, default=6)
    ap.add_argument("--min-separation-km", type=float, default=10.0)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    log = JsonLogger(OUT / "suggest_sites.jsonl")
    files = {int(re.search(r"\.A(\d{4})001\.", p).group(1)): Path(p) for p in glob.glob(str(RAW / PRODUCTS[a.sensor] / "*.h5"))}
    if a.year not in files:
        sys.exit(f"Sem {PRODUCTS[a.sensor]} de {a.year} em data/raw/ (anos: {sorted(files)}).")
    meshes = []
    for uf in a.ufs:
        shp = glob.glob(str(RAW / f"ibge/{uf}_Municipios_2024/*.shp")) or glob.glob(str(RAW / f"ibge/RJ_Municipios_2024/*.shp") if uf == "RJ" else "")
        if not shp:
            sys.exit(f"Malha de {uf} ausente: rode scripts/fetch_mesh.py --uf {uf}.")
        m = gpd.read_file(shp[0]).set_crs("EPSG:4326", allow_override=True)[["NM_MUN", "SIGLA_UF", "geometry"]] if "SIGLA_UF" in gpd.read_file(shp[0]).columns \
            else gpd.read_file(shp[0]).set_crs("EPSG:4326", allow_override=True).assign(SIGLA_UF=uf)[["NM_MUN", "SIGLA_UF", "geometry"]]
        meshes.append(m)
    mesh = pd.concat(meshes, ignore_index=True)
    rad, t = read_blackmarble(files[a.year])
    mask = state_mask(list(mesh.geometry), rad.shape, t)
    log.log("regiao", ufs=a.ufs, pixels_na_regiao=int(mask.sum()), tile="h13v11", sensor=PRODUCTS[a.sensor], year=a.year)
    cand = candidate_sites(rad, t, mask, per_stratum=a.per_stratum, min_separation_km=a.min_separation_km, seed=a.seed)
    if cand.empty:
        sys.exit("Nenhum candidato encontrado (regiao fora do tile?).")
    pts = gpd.GeoDataFrame(cand, geometry=gpd.points_from_xy(cand["lon"], cand["lat"]), crs="EPSG:4326")
    named = gpd.sjoin(pts, mesh, how="left", predicate="within").drop(columns=["geometry", "index_right"])
    cols = ["stratum", "SIGLA_UF", "NM_MUN", "lat", "lon"] + [c for c in named.columns if c.startswith("context_")] + ["valid_fraction_10km"]
    named["_ord"] = named["stratum"].map({lab: i for i, lab in enumerate(LABELS)})    # do escuro ao claro
    named = named.sort_values(["_ord", "SIGLA_UF", "NM_MUN"])[cols].reset_index(drop=True)
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / f"candidates_{'_'.join(a.ufs)}_{a.sensor}_{a.year}.csv"
    named.to_csv(out, index=False, float_format="%.5f")
    write_json(OUT / "suggest_sites_record.json", dict(parameters=vars(a), input_sha256=sha256_file(files[a.year]), output=str(out),
                                                       output_sha256=sha256_file(out), code=code_version()))
    show = named.assign(ctx10=named["context_10km"].round(2))[["stratum", "SIGLA_UF", "NM_MUN", "lat", "lon", "ctx10"]]
    print(show.to_string(index=False))
    print(f"\n{len(named)} candidatos em {out}")


if __name__ == "__main__":
    main()
