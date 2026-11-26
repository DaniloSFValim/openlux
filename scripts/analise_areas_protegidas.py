#!/usr/bin/env python3
"""Observatorio ambiental (Fase 7): luz noturna e areas protegidas, analise EXPLORATORIA.

Fontes (licenca verificada):
- CNUC, MMA, shp_cnuc_2025_08 (Creative Commons Atribuicao; ver docs/OPENLUX_2_0_MASTER_PLAN.md)
- Malha municipal IBGE 2024 (CC BY 4.0, confirmada)
- NOAA-20 VJ146A4 2025 (radiancia, qualidade 0, terra) via openlux.io.read_blackmarble

Saidas em outputs/ambiental/ (NAO publicadas; aguardam revisao):
- uc_por_municipio.csv: fracao da area municipal coberta por UCs e radiancia media 2025
- resumo.json: correlacao de Spearman e radiancia dentro x fora das UCs no estado

Limites: correlacao nao e causa. Radiancia orbital de superficie nao mede impacto em fauna, flora ou saude.
Pre-requisitos: data/raw/ibge/RJ_Municipios_2024/*.shp, data/raw/VJ146A4/*A2025001*.h5 e o zip do CNUC
extraido em CNUC_DIR (variavel de ambiente), com SHAPE_ENCODING=ISO-8859-1 (ver nota no relatorio).
"""
import glob
import json
import os
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from rasterio.features import geometry_mask
from scipy.stats import spearmanr

from openlux.io import read_blackmarble

RAW = Path("data/raw")
OUT = Path("outputs/ambiental")
CNUC_DIR = Path(os.environ["CNUC_DIR"])
EQUAL_AREA = "EPSG:6933"   # equal-area global, so frações de área sao comparaveis


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    mun = gpd.read_file(next(glob.iglob(str(RAW / "ibge/RJ_Municipios_2024/*.shp"))))
    mun = mun.set_crs("EPSG:4326", allow_override=True)[["CD_MUN", "NM_MUN", "geometry"]]
    uc = gpd.read_file(CNUC_DIR / "cnuc_2025_08.shp")
    uc = uc.set_crs("EPSG:4674", allow_override=True) if uc.crs is None else uc
    uc = uc.to_crs("EPSG:4326")[["cd_cnuc", "grupo", "categoria", "geometry"]]
    uc = uc[uc.intersects(mun.unary_union)]                       # so UCs que tocam o estado
    uc_union_mun = uc.unary_union.intersection(mun.unary_union)

    eq = mun.to_crs(EQUAL_AREA); uce = uc.to_crs(EQUAL_AREA).unary_union
    rows = []
    for i, r in eq.iterrows():
        inter = r.geometry.intersection(uce)
        rows.append({"CD_MUN": r.CD_MUN, "NM_MUN": r.NM_MUN, "area_km2": r.geometry.area / 1e6,
                     "area_uc_km2": inter.area / 1e6, "fracao_area_uc": inter.area / r.geometry.area})
    tab = pd.DataFrame(rows)

    arq = sorted(glob.glob(str(RAW / "VJ146A4" / "*A2025001*.h5")))
    if not arq:
        raise SystemExit("Sem VJ146A4 2025 em data/raw/")
    arr, tr = read_blackmarble(arq[0], "AllAngle_Composite_Snow_Free", n_min=1, allowed_quality=(0,))
    shape = arr.shape
    dentro_uc = geometry_mask(list(uc_union_mun.geoms) if uc_union_mun.geom_type == "MultiPolygon" else [uc_union_mun],
                              out_shape=shape, transform=tr, invert=True)
    dentro_rj = geometry_mask(list(mun.unary_union.geoms) if mun.unary_union.geom_type == "MultiPolygon" else [mun.unary_union],
                              out_shape=shape, transform=tr, invert=True)
    valido = np.isfinite(arr) & dentro_rj
    luz_uc = arr[valido & dentro_uc]; luz_fora = arr[valido & ~dentro_uc]

    # radiancia media 2025 por municipio (serie principal do NOAA-20, ja publicada)
    ann = pd.read_csv("outputs/noaa20/annual_main.csv", dtype={"CD_MUN": str})
    m25 = ann[ann.year == 2025][["CD_MUN", "mean_radiance"]]
    tab = tab.merge(m25, on="CD_MUN", how="left")
    tab.to_csv(OUT / "uc_por_municipio.csv", index=False, float_format="%.6g")

    rho, p = spearmanr(tab.fracao_area_uc, tab.mean_radiance, nan_policy="omit")
    resumo = {
        "ano": 2025, "sensor": "NOAA-20 (VJ146A4)", "qualidade": 0,
        "municipios": int(len(tab)), "ucs_no_estado": int(len(uc)),
        "spearman_fracao_uc_x_radiancia_media": {"rho": float(rho), "p": float(p),
                                                  "nota": "associacao espacial exploratoria, nao causa"},
        "radiancia_pixels_dentro_ucs": {"n": int(luz_uc.size), "mediana": float(np.median(luz_uc)) if luz_uc.size else None,
                                        "media": float(luz_uc.mean()) if luz_uc.size else None},
        "radiancia_pixels_fora_ucs": {"n": int(luz_fora.size), "mediana": float(np.median(luz_fora)),
                                      "media": float(luz_fora.mean())},
        "limites": ["radiancia de superficie orbital, nao brilho do ceu",
                    "dentro/fora de UC nao controla urbanizacao, altitude nem bioma",
                    "nomes das UCs com codificacao dupla no dbf: nao usar nomes sem corrigir"],
    }
    (OUT / "resumo.json").write_text(json.dumps(resumo, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(resumo, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
