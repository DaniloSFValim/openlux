#!/usr/bin/env python3
"""Camada de unidades de conservação do Rio de Janeiro (CNUC, 2025-08).

Os nomes no .dbf têm codificação dupla (UTF-8 lido como Latin-1); são desfeitos por _decodificar. A
conferência com o relatório oficial do CNUC (cnuc-backend.mma.gov.br/api/v1/report/uc/<n>) foi feita em
2026-11-27 para quatro UCs (0000.00.0154, 0000.31.0395, 0000.23.3713, 0000.27.2676): nomes idênticos.
A decodificação funciona em todos os 3.122 registros do arquivo nacional.

Entrada: CNUC_DIR (pasta com cnuc_2025_08.shp, extraída do zip do MMA) e os limites municipais do IBGE
em data/raw/ibge/RJ_Municipios_2024/*.shp. Saída: web/data/downloads/openlux_ucs_rj_cnuc_2025_08.geojson
Recorte: polígonos que tocam o estado, cortados pela união dos municípios, simplificados em 0,001°.
Licença dos dados: CC BY 4.0 (conjunto MMA, verificado em 2026-11-26).
"""
import glob
import os
from pathlib import Path

import geopandas as gpd
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parent.parent
SAIDA = ROOT / "web/data/downloads/openlux_ucs_rj_cnuc_2025_08.geojson"


def _decodificar(s):
    """Desfaz UTF-8 lido como Latin-1 (codificação dupla do dbf do CNUC); mantém o texto se não for o caso."""
    if not isinstance(s, str):
        return s
    try:
        return s.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return s


def main():
    os.environ.setdefault("SHAPE_ENCODING", "ISO-8859-1")
    cnuc = Path(os.environ["CNUC_DIR"]) / "cnuc_2025_08.shp"
    uc = gpd.read_file(cnuc)
    mun = gpd.read_file(glob.glob(str(ROOT / "data/raw/ibge/RJ_Municipios_2024/*.shp"))[0]).to_crs(uc.crs)
    rj = unary_union(mun.geometry)
    uc = uc[uc.intersects(rj)].copy()
    uc["geometry"] = uc.geometry.intersection(rj).simplify(0.001, preserve_topology=True)
    uc = uc[uc.geometry.notna() & ~uc.geometry.is_empty].to_crs(4326)
    out = gpd.GeoDataFrame({
        "cd_cnuc": uc["cd_cnuc"].astype(str),
        "nome": uc["nome_uc"].map(_decodificar),
        "categoria": uc["categoria"].map(_decodificar),
        "grupo": uc["grupo"].map(_decodificar),
        "esfera": uc["esfera"].astype(str),
        "ano_criacao": uc["cria_ano"].astype(str),
        "situacao": uc["situacao"].map(_decodificar),
    }, geometry=uc.geometry.values, crs="EPSG:4326")
    out.to_file(SAIDA, driver="GeoJSON")
    print(f"OK: {len(out)} unidades em {SAIDA}")


if __name__ == "__main__":
    main()
