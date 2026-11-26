#!/usr/bin/env python3
"""Áreas urbanizadas do IBGE (2019) no estado do Rio de Janeiro: fração urbana por município e camada para mapa.

Entrada: data/raw/ibge/AreasUrbanizadas2019/AU_2022_AreasUrbanizadas2019_Brasil.shp (IBGE, SIRGAS 2000, EPSG:4674)
e a malha municipal de data/raw/ibge/RJ_Municipios_2024 (IBGE, Malha Municipal Digital 2024).

Saídas publicadas (web/data/downloads):
- openlux_area_urbana_municipio_2019.csv: área municipal, área urbana e fração urbana por município.
- openlux_areas_urbanizadas_rj_2019.geojson: união das áreas urbanizadas no estado, simplificada (0,001°) para mapa.

Cálculo: áreas em projeção de área igual (Albers, GRS80). Área urbana = área da união dos pedaços de cada
polígono urbano dentro do município (evita dupla contagem em polígonos sobrepostos). Fração = área urbana / área
municipal projetada. A coluna area_municipio_km2 vem da mesma projeção; a área oficial do IBGE (AREA_KM2) é outra.
"""
import csv
import glob
import json
from pathlib import Path

import geopandas as gpd
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data/raw/ibge"
DL = ROOT / "web/data/downloads"
AEA = "+proj=aea +lat_1=-2 +lat_2=-22 +lat_0=-12 +lon_0=-54 +x_0=0 +y_0=0 +ellps=GRS80 +units=m +no_defs"
SIMPLIFICA = 0.001


def main():
    au = gpd.read_file(RAW / "AreasUrbanizadas2019/AU_2022_AreasUrbanizadas2019_Brasil.shp")
    malha = gpd.read_file(next(glob.iglob(str(RAW / "RJ_Municipios_2024/*.shp"))))
    uniao = unary_union(malha.geometry)
    minx, miny, maxx, maxy = malha.total_bounds
    au = au.cx[minx:maxx, miny:maxy]
    au = au[au.intersects(uniao)].copy()

    au_p = au.to_crs(AEA)
    au_p["geometry"] = au_p.buffer(0)
    mal_p = malha.to_crs(AEA)
    sidx = au_p.sindex
    linhas = []
    for i, r in malha.reset_index(drop=True).iterrows():
        g = mal_p.iloc[i].geometry
        cand = au_p.iloc[list(sidx.query(g, predicate="intersects"))]
        pedacos = [p for p in (c.intersection(g) for c in cand.geometry) if not p.is_empty]
        urb = unary_union(pedacos).area if pedacos else 0.0
        linhas.append({"CD_MUN": str(r.CD_MUN), "NM_MUN": r.NM_MUN,
                       "area_municipio_km2": round(g.area / 1e6, 3),
                       "area_urbana_km2": round(urb / 1e6, 3),
                       "fracao_urbana": round(urb / g.area, 4)})
    linhas.sort(key=lambda x: x["CD_MUN"])
    assert all(0 <= x["fracao_urbana"] <= 1 for x in linhas), "fração fora de [0, 1]"
    with open(DL / "openlux_area_urbana_municipio_2019.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0].keys()))
        w.writeheader()
        w.writerows(linhas)

    g = unary_union(au.geometry.buffer(0)).simplify(SIMPLIFICA, preserve_topology=True)
    poligonos = [g] if g.geom_type == "Polygon" else list(g.geoms)
    def anel(c):
        return [[round(x, 5), round(y, 5)] for x, y in c.coords]
    geom = {"type": "MultiPolygon", "coordinates": [
        [anel(p.exterior)] + [anel(i) for i in p.interiors] for p in poligonos]}
    fc = {"type": "FeatureCollection", "name": "areas_urbanizadas_rj_2019",
          "features": [{"type": "Feature", "properties": {
              "fonte": "IBGE, Áreas Urbanizadas do Brasil 2019; recorte RJ simplificado para visualização"},
              "geometry": geom}]}
    (DL / "openlux_areas_urbanizadas_rj_2019.geojson").write_text(
        json.dumps(fc, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"OK: {len(linhas)} municípios; {len(poligonos)} polígonos na camada")


if __name__ == "__main__":
    main()
