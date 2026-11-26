#!/usr/bin/env python3
"""Quantis P75, P90 e P95 dos pixels validos, por municipio e ano, para os dois sensores.

Saida: outputs/percentiles/annual_percentiles_{snpp,noaa20}.csv e run_record.json (hashes das entradas
e das saidas). Entrada SEPARADA da serie principal: nao altera outputs/annual nem outputs/noaa20.

Os arquivos NAO sao publicados por este script. Publicacao exige revisao previa do responsavel.
Pre-requisitos: scripts/fetch_blackmarble.py e scripts/fetch_ibge.py (data/raw/).
"""
import glob
import re
import sys
from pathlib import Path

import geopandas as gpd

from openlux.pipeline import percentile_table
from openlux.provenance import code_version, write_json
from openlux.io import sha256_file as sha256

RAW = Path("data/raw")
OUT = Path("outputs/percentiles")
QUANTIS = (0.75, 0.9, 0.95)




def serie(produto: str) -> dict:
    out = {}
    for p in sorted(glob.glob(str(RAW / produto / "*.h5"))):
        out[int(re.search(r"\.A(\d{4})001\.", p).group(1))] = Path(p)
    return out


def main():
    mun = gpd.read_file(next(glob.iglob(str(RAW / "ibge/RJ_Municipios_2024/*.shp"))))
    assert mun.crs.to_epsg() == 4674, mun.crs
    mun = mun.set_crs("EPSG:4326", allow_override=True)   # mesma premissa de run_annual (ver DECISIONS §1)
    polys = mun[["CD_MUN", "geometry"]]
    OUT.mkdir(parents=True, exist_ok=True)
    registro = {"codigo": code_version("."), "quantis": list(QUANTIS), "entradas": {}, "saidas": {}}
    for sensor, produto in (("snpp", "VNP46A4"), ("noaa20", "VJ146A4")):
        arquivos = serie(produto)
        if not arquivos:
            sys.exit(f"Nenhum arquivo {produto} em data/raw/.")
        df = percentile_table(arquivos, polys, "CD_MUN", quantiles=QUANTIS)
        saida = OUT / f"annual_percentiles_{sensor}.csv"
        df.to_csv(saida, index=False, float_format="%.9g")
        registro["entradas"][produto] = {Path(p).name: sha256(Path(p)) for p in arquivos.values()}
        registro["saidas"][saida.name] = sha256(saida)
        print(f"{sensor}: {len(df)} linhas ({df['year'].nunique()} anos) -> {saida}")
    write_json(OUT / "run_record.json", registro)


if __name__ == "__main__":
    main()
