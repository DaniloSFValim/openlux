#!/usr/bin/env python3
"""Gera web/data/ a partir das saidas reais de scripts/run_annual.py (nada e inventado)."""
import glob
import json
from pathlib import Path

import geopandas as gpd
import pandas as pd

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
    sm_path, ss_path = Path("outputs/sensors/municipal_comparison_2018_2025.csv"), Path("outputs/sensors/summary.json")
    sm = pd.read_csv(sm_path, dtype={"CD_MUN": str}) if sm_path.exists() else None
    ss = json.loads(ss_path.read_text()) if ss_path.exists() else None
    sp = Path("outputs/sectors/sector_indicators_snpp.csv")
    sectors = pd.read_csv(sp, dtype={"CD_MUN": str}) if sp.exists() else None
    pixel_shares = {w: pd.read_csv(f"outputs/sectors/pixel_trend_snpp_{w}.csv", dtype={"CD_MUN": str})
                    for w in rec["parameters"]["trend_windows"]
                    if Path(f"outputs/sectors/pixel_trend_snpp_{w}.csv").exists()} or None
    data = build_indicators(annual=annual, trends=trends, qa=qa, sensitivity=sens,
                            sensor_comparison=cmp_, run_record=rec, sensor_municipal=sm, sensor_summary=ss,
                            sectors=sectors, pixel_shares=pixel_shares)
    assert set(data["municipios"]) == set(mesh.CD_MUN), "municipios das saidas e da malha divergem"
    WEB.mkdir(parents=True, exist_ok=True)
    (WEB / "indicators.json").write_text(json.dumps(data, ensure_ascii=False, allow_nan=False,
                                                    separators=(",", ":")), encoding="utf-8")
    (WEB / "municipios.geojson").write_text(
        json.dumps(simplify_geojson(mesh), ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print("OK:", {p.name: p.stat().st_size for p in WEB.iterdir()})


if __name__ == "__main__":
    main()
