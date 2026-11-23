#!/usr/bin/env python3
"""Indicadores por setores censitarios (Censo 2022): exposicao populacional e urbano x rural.

Pre-requisitos: scripts/fetch_blackmarble.py e scripts/fetch_ibge.py (malha de setores). A populacao
e a do Censo 2022 e e MANTIDA FIXA em todos os anos (nao ha populacao anual por setor): variacoes
temporais refletem a radiancia, nao a mudanca demografica. Saidas em outputs/sectors/.
"""
import glob
import re
import sys
import warnings
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from rasterio.transform import Affine

from openlux.geo import bbox_window
from openlux.io import read_blackmarble, sha256_file
from openlux.log import JsonLogger
from openlux.pixeltrend import significant_change, trend_shares
from openlux.provenance import write_json
from openlux.sectors import dedupe_sectors, sector_indicators, sector_overlay

RAW = Path("data/raw")
OUT = Path("outputs/sectors")
TAU = 0.5  # mesmo limiar de referencia da fracao iluminada municipal (docs/DECISIONS.md)
ALPHA = 0.05  # FDR (Benjamini-Hochberg) da mudanca por pixel
MIN_N = 8  # anos validos minimos por pixel (igual a min_years municipal)
WINDOWS = {"snpp": {"2012_2021": (2012, 2021), "2012_2025": (2012, 2025)}, "noaa20": {}}


def main():
    log = JsonLogger(OUT / "run_sectors.jsonl")
    gpkg = RAW / "ibge/setores2022/RJ_setores_CD2022.gpkg"
    if not gpkg.exists():
        sys.exit("Malha de setores ausente. Rode scripts/fetch_ibge.py --sectors.")
    raw = gpd.read_file(gpkg)
    log.log("sectors_read", rows=len(raw), sha256=sha256_file(gpkg))
    sec = dedupe_sectors(raw)
    log.log("sectors_deduped", sectors=len(sec), population=float(sec["pop"].sum()),
            rows_removed=len(raw) - len(sec))
    products = {"snpp": "VNP46A4", "noaa20": "VJ146A4"}
    outputs, inputs = [], {}
    for sensor, prod in products.items():
        files = {int(re.search(r"\.A(\d{4})001\.", p).group(1)): Path(p)
                 for p in sorted(glob.glob(str(RAW / prod / "*.h5")))}
        if not files:
            log.warn("no_files", sensor=sensor)
            continue
        first = files[min(files)]
        _, t = read_blackmarble(first)
        import h5py
        with h5py.File(first, "r") as f:
            shape = f["HDFEOS/GRIDS/VIIRS_Grid_DNB_2d/Data Fields/AllAngle_Composite_Snow_Free"].shape
        r0, r1, c0, c1 = bbox_window(t, shape, tuple(sec.total_bounds))
        tw = t * Affine.translation(c0, r0)
        ov = sector_overlay(sec, (r1 - r0, c1 - c0), tw)
        log.log("overlay", sensor=sensor, window=[r0, r1, c0, c1], rows=len(ov),
                population_outside_grid=ov.attrs["population_outside_grid"],
                population_in_grid=float(ov["pop"].sum()))
        frames, layers = [], {}
        for y, p in sorted(files.items()):
            rad, _ = read_blackmarble(p)
            layers[y] = rad[r0:r1, c0:c1]
            d = sector_indicators(ov, layers[y], tau=TAU)
            d.insert(0, "year", y)
            d.insert(0, "sensor", sensor)
            frames.append(d)
            inputs[f"{prod}_{y}"] = sha256_file(p)
            log.log("year_done", sensor=sensor, year=y, municipalities=len(d))
        df = pd.concat(frames, ignore_index=True)
        for wname, (y0, y1) in WINDOWS[sensor].items():
            yrs = [y for y in sorted(layers) if y0 <= y <= y1]
            stack = np.stack([layers[y] for y in yrs])
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)   # fatias so com NaN (mar/agua) sao esperadas
                active = np.nanmedian(stack, axis=0) >= TAU      # pixels iluminados na mediana dos anos
            lab = significant_change(stack, yrs, min_n=MIN_N, alpha=ALPHA, active=active)
            sh = trend_shares(ov, lab["label"], lab["tested"])
            sh.insert(0, "window", wname); sh.insert(0, "sensor", sensor)
            tr_out = OUT / f"pixel_trend_{sensor}_{wname}.csv"
            sh.to_csv(tr_out, index=False, float_format="%.6g")
            log.log("pixel_trend", sensor=sensor, window=wname, years=len(yrs),
                    active_pixels=int(active.sum()), tested=int(lab["tested"].sum()),
                    increase=int((lab["label"] == 1).sum()), decrease=int((lab["label"] == -1).sum()))
            outputs.append({"path": str(tr_out), "sha256": sha256_file(tr_out), "rows": len(sh)})
        out = OUT / f"sector_indicators_{sensor}.csv"
        df.to_csv(out, index=False, float_format="%.6g")
        outputs.append({"path": str(out), "sha256": sha256_file(out), "rows": len(df)})
    write_json(OUT / "run_record_sectors.json", {
        "parameters": {"tau_nw_cm2_sr": TAU, "population_year": 2022, "population_static": True,
                       "valid_quality": [0], "sectors_deduped": len(sec),
                       "pixel_trend": {"alpha": ALPHA, "min_n": MIN_N, "active": "mediana anual >= tau"}},
        "input_sha256": {"sectors_gpkg": sha256_file(gpkg), **inputs}, "outputs": outputs})
    print("OK", [o["path"] for o in outputs])


if __name__ == "__main__":
    main()
