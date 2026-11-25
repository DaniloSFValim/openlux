#!/usr/bin/env python3
"""Gera web/data/indicators_noaa20.json a partir das saidas do NOAA-20 (VJ146A4, 2018-2025).

Usa a mesma funcao de calculo do indicators.json do S-NPP (openlux.webdata.build_indicators), so que
com as entradas do NOAA-20. Nao altera web/data/indicators.json. Nada e estimado: todas as entradas
sao saidas reais do pipeline (outputs/noaa20, outputs/sectors, outputs/sensors e outputs/annual).
"""
import json
from pathlib import Path

import pandas as pd

from openlux.webdata import build_indicators

NOA = Path("outputs/noaa20")
SEC = Path("outputs/sectors")
ANU = Path("outputs/annual")
SENS = Path("outputs/sensors")
WEB = Path("web/data")


def main():
    annual = pd.read_csv(NOA / "annual_main.csv", dtype={"CD_MUN": str})
    trends = pd.read_csv(NOA / "trends_main.csv", dtype={"CD_MUN": str})
    qa = pd.read_csv(NOA / "qa_background_controls.csv")
    sens = json.loads((NOA / "sensitivity.json").read_text())
    rec = json.loads((NOA / "run_record.json").read_text())
    cmp_ = json.loads((ANU / "sensor_comparison_snpp_noaa20.json").read_text())
    sm = pd.read_csv(SENS / "municipal_comparison_2018_2025.csv", dtype={"CD_MUN": str})
    ss = json.loads((SENS / "summary.json").read_text())
    sectors = pd.read_csv(SEC / "sector_indicators_noaa20.csv", dtype={"CD_MUN": str})
    pixel = {"2018_2025": pd.read_csv(SEC / "pixel_trend_noaa20_2018_2025.csv", dtype={"CD_MUN": str})}
    data = build_indicators(annual=annual, trends=trends, qa=qa, sensitivity=sens,
                            sensor_comparison=cmp_, run_record=rec, sensor_municipal=sm, sensor_summary=ss,
                            sectors=sectors, pixel_shares=pixel)
    data["meta"]["sensor"] = "NOAA-20 (VJ146A4, coleção 002)"
    out = WEB / "indicators_noaa20.json"
    out.write_text(json.dumps(data, ensure_ascii=False, allow_nan=False, separators=(",", ":")), encoding="utf-8")
    print("OK:", out, out.stat().st_size, "bytes; municipios:", len(data["municipios"]), "anos:", data["meta"]["years"])


if __name__ == "__main__":
    main()
