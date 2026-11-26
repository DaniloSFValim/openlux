#!/usr/bin/env python3
"""Contagens de pixels por município (NOAA-20) a partir das grades publicadas em web/data/pixels.

Gera web/data/downloads/openlux_pixels_municipio_noaa20.csv (uma linha por município e ano: contagem de
cada classe de luz e de pixels válidos) e openlux_tendencia_pixels_noaa20_2018_2025.csv (contagem de pixels
com aumento, redução, sem mudança significativa e não testados, pela grade change_2018_2025).
Usa o centro do pixel dentro do polígono (mesma regra de scripts/build_web_municipios.py). Nenhum valor de radiância.
"""
import csv
import glob
from pathlib import Path

import geopandas as gpd
import numpy as np
from rasterio.features import rasterize
from rasterio.transform import Affine

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"
DL = WEB / "data/downloads"


def main():
    grade = __import__("json").loads((WEB / "data/pixels/meta.json").read_text(encoding="utf-8"))
    g = grade["grid"]
    rows, cols, pd = g["rows"], g["cols"], g["pixel_deg"]
    tr = Affine(pd, 0, g["lon_west"], 0, -pd, g["lat_north"])
    malha = gpd.read_file(next(glob.iglob(str(ROOT / "data/raw/ibge/RJ_Municipios_2024/*.shp"))))
    cds = malha["CD_MUN"].astype(str).tolist()
    lab = rasterize([(geom, i + 1) for i, geom in enumerate(malha.geometry)], out_shape=(rows, cols), transform=tr, fill=0, all_touched=False, dtype="int32")
    anos = sorted(int(Path(p).stem) for p in glob.glob(str(WEB / "data/pixels/noaa20/[0-9][0-9][0-9][0-9].bin")))
    with open(DL / "openlux_pixels_municipio_noaa20.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["CD_MUN", "year", "pix_fora_estado_ou_sem_mascara", "pix_sem_dado_valido"] + [f"pix_classe_{c}" for c in range(2, 8)] + ["pix_validos"])
        for y in anos:
            codigos = np.fromfile(WEB / f"data/pixels/noaa20/{y}.bin", dtype=np.uint8).reshape(rows, cols)
            for i, cd in enumerate(cds):
                c = np.bincount(codigos[lab == i + 1], minlength=8)[:8]
                w.writerow([cd, y, int(c[0]), int(c[1])] + [int(v) for v in c[2:8]] + [int(c[2:8].sum())])
    cod = np.fromfile(WEB / "data/pixels/noaa20/change_2018_2025.bin", dtype=np.uint8).reshape(rows, cols)
    with open(DL / "openlux_tendencia_pixels_noaa20_2018_2025.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["CD_MUN", "pix_nao_testado", "pix_sem_mudanca_significativa", "pix_aumento_significativo", "pix_reducao_significativa"])
        for i, cd in enumerate(cds):
            c = np.bincount(cod[lab == i + 1], minlength=5)[:5]
            w.writerow([cd, int(c[1]), int(c[2]), int(c[3]), int(c[4])])
    print(f"OK: {len(cds)} municípios, {len(anos)} anos")


if __name__ == "__main__":
    main()
