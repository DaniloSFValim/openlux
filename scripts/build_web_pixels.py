#!/usr/bin/env python3
"""Gera web/data/pixels/<sensor>/: grades de CLASSES (uint8) por ano e de MUDANCA por pixel para a interface.

So codigos de classe sao gravados (ver openlux.pixelmap), nunca o valor de radiancia. Sensores: Suomi NPP
(VNP46A4, 2012-2025) e NOAA-20 (VJ146A4, 2018-2025); qualidade 0, mascara de terra. Pixels fora da malha
municipal = codigo 0. A mudanca por pixel usa openlux.pixeltrend com os mesmos parametros de run_sectors.py.
"""
import glob
import re
import shutil
from pathlib import Path

import geopandas as gpd
import h5py
import numpy as np
from rasterio.transform import Affine

from openlux.geo import bbox_window
from openlux.io import read_blackmarble, sha256_file
from openlux.log import JsonLogger
from openlux.pixelmap import BREAKS, FIRST_RADIANCE_CODE, LABELS, change_codes, radiance_classes, state_mask
from openlux.pixeltrend import significant_change
from openlux.provenance import code_version, write_json

RAW, OUT = Path("data/raw"), Path("web/data/pixels")
SENSORS = {"snpp": ("VNP46A4", "Suomi NPP (VNP46A4 v2.0)"), "noaa20": ("VJ146A4", "NOAA-20 (VJ146A4 v2.0)")}
CHANGE_WINDOWS = {"snpp": {"2012_2021": (2012, 2021), "2012_2025": (2012, 2025)}, "noaa20": {"2018_2025": (2018, 2025)}}
TAU, ALPHA, MIN_N = 0.5, 0.05, 8   # iguais a scripts/run_sectors.py


def main():
    log = JsonLogger()
    mesh = gpd.read_file(next(glob.iglob(str(RAW / "ibge/RJ_Municipios_2024/*.shp")))).set_crs("EPSG:4326", allow_override=True)
    series = {s: {int(re.search(r"\.A(\d{4})001\.", p).group(1)): Path(p) for p in sorted(glob.glob(str(RAW / prod / "*.h5")))}
              for s, (prod, _) in SENSORS.items()}
    first = series["snpp"][min(series["snpp"])]
    _, t = read_blackmarble(first)
    with h5py.File(first, "r") as f:
        shape = f["HDFEOS/GRIDS/VIIRS_Grid_DNB_2d/Data Fields/AllAngle_Composite_Snow_Free"].shape
    r0, r1, c0, c1 = bbox_window(t, shape, tuple(mesh.total_bounds))
    tw = t * Affine.translation(c0, r0)
    inside = state_mask(list(mesh.geometry), (r1 - r0, c1 - c0), tw)
    if OUT.exists():
        shutil.rmtree(OUT)
    meta = dict(grid=dict(rows=r1 - r0, cols=c1 - c0, lon_west=tw.c, lat_north=tw.f, pixel_deg=abs(tw.a)),
                classes=dict(first_code=FIRST_RADIANCE_CODE, breaks_nw_cm2_sr=BREAKS, labels=LABELS),
                codes={"0": "fora do estado", "1": "sem dado valido"},
                change_codes={"0": "fora do estado", "1": "nao testado", "2": "sem mudanca significativa", "3": "aumento significativo", "4": "reducao significativa"},
                change_params=dict(tau_nw_cm2_sr=TAU, alpha_fdr=ALPHA, min_valid_years=MIN_N, tested="mediana anual >= tau e >= min_valid_years anos validos"),
                sensors={}, code=code_version())
    for s, (prod, name) in SENSORS.items():
        d = OUT / s
        d.mkdir(parents=True, exist_ok=True)
        layers, years = {}, {}
        for y, p in sorted(series[s].items()):
            rad, _ = read_blackmarble(p)
            layers[y] = rad[r0:r1, c0:c1]
            codes = radiance_classes(layers[y], inside)
            (d / f"{y}.bin").write_bytes(codes.tobytes())
            years[str(y)] = dict(sha256=sha256_file(d / f"{y}.bin"), input_sha256=sha256_file(p))
            log.log("year_written", sensor=s, year=y, nodata_inside=int((codes == 1).sum()))
        changes = {}
        for w, (y0, y1) in CHANGE_WINDOWS[s].items():
            yrs = [y for y in sorted(layers) if y0 <= y <= y1]
            stack = np.stack([layers[y] for y in yrs])
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                active = (np.nanmedian(stack, axis=0) >= TAU) & inside   # so pixels do estado entram no teste e no FDR
            res = significant_change(stack, yrs, min_n=MIN_N, alpha=ALPHA, active=active)
            codes = change_codes(res["label"], res["tested"], inside)
            (d / f"change_{w}.bin").write_bytes(codes.tobytes())
            counts = {k: int((codes == v).sum()) for k, v in (("untested", 1), ("not_significant", 2), ("increase", 3), ("decrease", 4))}
            changes[w] = dict(years=[y0, y1], n_years=len(yrs), sha256=sha256_file(d / f"change_{w}.bin"), counts=counts)
            log.log("change_written", sensor=s, window=w, **counts)
        meta["sensors"][s] = dict(name=name, product=prod, years=years, change=changes)
    write_json(OUT / "meta.json", meta)
    print("OK", {s: len(v["years"]) for s, v in meta["sensors"].items()}, "grade", r1 - r0, "x", c1 - c0)


if __name__ == "__main__":
    main()
