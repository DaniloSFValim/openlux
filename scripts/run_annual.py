#!/usr/bin/env python3
"""Executa a serie anual real: indicadores municipais, tendencia e sensibilidade.

Pre-requisitos: scripts/fetch_blackmarble.py e scripts/fetch_ibge.py. Saidas em outputs/
(ignoradas pelo git ate a decisao de publicacao de produtos derivados).
"""
import glob
import json
import re
import sys
from pathlib import Path

import geopandas as gpd

from openlux.ibge import parse_sidra_population
from openlux.pipeline import run_annual

RAW = Path("data/raw")


def main():
    files = {}
    for p in sorted(glob.glob(str(RAW / "VNP46A4" / "*.h5"))):
        files[int(re.search(r"\.A(\d{4})001\.", p).group(1))] = Path(p)
    if not files:
        sys.exit("Nenhum arquivo VNP46A4 em data/raw/. Rode scripts/fetch_blackmarble.py.")
    mun = gpd.read_file(next(glob.iglob(str(RAW / "ibge/RJ_Municipios_2024/*.shp"))))
    assert mun.crs.to_epsg() == 4674, mun.crs
    # SIRGAS 2000 (4674) e WGS84 (4326) diferem de poucos metros (< 1 pixel de ~460 m):
    # a malha e tratada como 4326 para a agregacao. Premissa documentada na metodologia.
    mun = mun.set_crs("EPSG:4326", allow_override=True)
    pop = parse_sidra_population(json.loads((RAW / "ibge/sidra_4709_v93_RJ_2022.json")
                                            .read_text(encoding="utf-8")))
    assert set(pop.cd_mun) == set(mun.CD_MUN), "codigos de municipio da malha e do SIDRA divergem"
    rec = run_annual(files, mun[["CD_MUN", "NM_MUN", "geometry"]], "CD_MUN", pop, "outputs/annual")
    print("OK; anos:", sorted(files)[0], "-", sorted(files)[-1])
    print(json.dumps(rec["parameters"], indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
