#!/usr/bin/env python3
"""Controle de urbanização no nível dos pixels: radiância dentro x fora de UCs, estratificada por urbanização.

Entradas (data/raw, sem versionamento):
- VJ146A4 (NOAA-20) ano 2025, tile h13v11: radiância com máscaras de validade (qualidade 0, terra).
- Malha municipal IBGE 2024 (limite do estado).
- Áreas Urbanizadas do Brasil 2019 (IBGE), shapefile AU_2022_AreasUrbanizadas2019_Brasil.shp.
- CNUC shp_cnuc_2025_08 (MMA, CC BY 4.0), polígonos cnuc_2025_08.shp (encoding ISO-8859-1).

Método: para cada pixel válido dentro do estado, classifica-se (dentro/fora de UC) x (urbano/não urbano),
pelo centro do pixel. Compara-se a radiância entre dentro e fora de UC em cada estrato urbano.
Não se publicam p-valores: pixels são espacialmente autocorrelacionados e os tamanhos amostrais são grandes,
então testes de significância não são interpretáveis aqui. Resultado exploratório, não causal.
"""
import glob
import json
import os
from pathlib import Path

import geopandas as gpd
import numpy as np
from rasterio.features import rasterize
from rasterio.transform import Affine
from shapely.ops import unary_union

from openlux.geo import bbox_window
from openlux.io import read_blackmarble
from openlux.pixelmap import state_mask

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data/raw"
OUT = ROOT / "web/data/downloads/openlux_uc_controle_urbanizacao_pixels_2025.json"


def main():
    os.environ.setdefault("SHAPE_ENCODING", "ISO-8859-1")
    malha = gpd.read_file(next(glob.iglob(str(RAW / "ibge/RJ_Municipios_2024/*.shp"))))
    au = gpd.read_file(RAW / "ibge/AreasUrbanizadas2019/AU_2022_AreasUrbanizadas2019_Brasil.shp")
    uc = gpd.read_file(f"zip://{RAW / 'cnuc/shp_cnuc_2025_08.zip'}!cnuc_2025_08.shp")

    h5 = next(glob.iglob(str(RAW / "VJ146A4/VJ146A4.A2025001.*.h5")))
    rad, t = read_blackmarble(h5)
    r0, r1, c0, c1 = bbox_window(t, rad.shape, tuple(malha.total_bounds))
    rad = rad[r0:r1, c0:c1]
    tw = t * Affine.translation(c0, r0)
    shape = rad.shape

    dentro_estado = state_mask(list(malha.geometry), shape, tw)
    urbano = rasterize([(g, 1) for g in au.to_crs(malha.crs).cx[malha.total_bounds[0]:malha.total_bounds[2],
                                                                malha.total_bounds[1]:malha.total_bounds[3]].geometry
                        if g is not None], out_shape=shape, transform=tw, fill=0, all_touched=False, dtype="uint8").astype(bool)
    uc_uniao = unary_union(uc.to_crs(malha.crs).geometry.buffer(0))
    em_uc = rasterize([(uc_uniao, 1)], out_shape=shape, transform=tw, fill=0, all_touched=False, dtype="uint8").astype(bool)

    valido = dentro_estado & np.isfinite(rad)
    estratos = {
        "urbano_dentro_uc": valido & urbano & em_uc,
        "urbano_fora_uc": valido & urbano & ~em_uc,
        "nao_urbano_dentro_uc": valido & ~urbano & em_uc,
        "nao_urbano_fora_uc": valido & ~urbano & ~em_uc,
    }
    resumo = {}
    for nome, m in estratos.items():
        v = rad[m]
        resumo[nome] = {"n": int(v.size), "mediana": round(float(np.median(v)), 4) if v.size else None,
                        "media": round(float(v.mean()), 4) if v.size else None}
    comparacoes = {}
    for estrato in ["urbano", "nao_urbano"]:
        a = rad[estratos[f"{estrato}_dentro_uc"]]
        b = rad[estratos[f"{estrato}_fora_uc"]]
        if a.size and b.size:
            comparacoes[estrato] = {"diferenca_medianas_dentro_menos_fora": round(float(np.median(a) - np.median(b)), 4),
                                    "diferenca_medias_dentro_menos_fora": round(float(a.mean() - b.mean()), 4)}
    res = {"ano": 2025, "sensor": "NOAA-20 (VJ146A4)", "qualidade": 0, "estratos": resumo, "comparacoes": comparacoes,
           "nota": "exploratório; sem p-valores (pixels autocorrelacionados); não causal"}
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
