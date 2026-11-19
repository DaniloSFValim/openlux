#!/usr/bin/env python3
"""Gera web/data/ a partir das saidas reais de scripts/run_annual.py (nada e inventado)."""
import glob
import json
from pathlib import Path

import geopandas as gpd
import pandas as pd

from openlux.provenance import write_json
from openlux.webdata import build_indicators, simplify_geojson

OUT = Path("outputs/annual")
WEB = Path("web/data")


def main():
    mesh = gpd.read_file(next(glob.iglob("data/raw/ibge/RJ_Municipios_2024/*.shp")))
    annual = pd.read_csv(OUT / "annual_main.csv", dtype={"CD_MUN": str})
    trends = pd.read_csv(OUT / "trends_main.csv", dtype={"CD_MUN": str})
    qa = pd.read_csv(OUT / "qa_background_controls.csv")
    sens = json.loads((OUT / "sensitivity.json").read_text())
    cmp_ = json.loads((OUT / "sensor_comparison_snpp_noaa20.json").read_text())
    rec = json.loads((OUT / "run_record.json").read_text())
    data = build_indicators(annual=annual, trends=trends, qa=qa, sensitivity=sens,
                            sensor_comparison=cmp_, run_record=rec)
    assert set(data["municipios"]) == set(mesh.CD_MUN), "municipios das saidas e da malha divergem"
    WEB.mkdir(parents=True, exist_ok=True)
    (WEB / "indicators.json").write_text(json.dumps(data, ensure_ascii=False, allow_nan=False,
                                                    separators=(",", ":")), encoding="utf-8")
    (WEB / "municipios.geojson").write_text(
        json.dumps(simplify_geojson(mesh), ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print("OK:", {p.name: p.stat().st_size for p in WEB.iterdir()})


if __name__ == "__main__":
    main()
