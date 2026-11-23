#!/usr/bin/env python3
"""Quando o piso de ruido sobe? Controles de pixels escuros por MES, S-NPP e NOAA-20.

A classe de pixels escuros vem da linha de base ANUAL do S-NPP 2012-2021 (mediana zero), a mesma de
`openlux.qa` e do pipeline anual. Para cada arquivo mensal reporta a radiancia media e a fracao positiva
desses pixels (terra e mar), o numero mediano de observacoes e a composicao de qualidade da camada.
Saida: outputs/monthly/monthly_noise_controls.csv (deterministica).
"""
import datetime as dt
import glob
import re
from pathlib import Path

import geopandas as gpd
import h5py
import numpy as np
import pandas as pd

from openlux.geo import bbox_window
from openlux.io import read_blackmarble, read_for_qa
from openlux.qa import controls_for, dark_class_masks

RAW = Path("data/raw")
G = "HDFEOS/GRIDS/VIIRS_Grid_DNB_2d/Data Fields"
LAYER = "AllAngle_Composite_Snow_Free"


def month_of(path):
    m = re.search(r"\.A(\d{4})(\d{3})\.", path)
    d = dt.date(int(m.group(1)), 1, 1) + dt.timedelta(days=int(m.group(2)) - 1)
    return f"{d.year}-{d.month:02d}"


def main():
    mesh = gpd.read_file(next(glob.iglob(str(RAW / "ibge/RJ_Municipios_2024/*.shp"))))
    annual = sorted(glob.glob(str(RAW / "VNP46A4/*.h5")))
    _, t = read_blackmarble(annual[0])
    with h5py.File(annual[0]) as f:
        shape = f[f"{G}/Land_Water_Mask"].shape
    win = bbox_window(t, shape, tuple(mesh.total_bounds))
    sl = (slice(win[0], win[1]), slice(win[2], win[3]))
    base = []
    lw = None
    for p in annual:
        if int(re.search(r"\.A(\d{4})", p).group(1)) <= 2021:
            rad, lw = read_for_qa(p, window=win)
            base.append(rad)
    land, sea = np.isin(lw, (0, 1, 5)), lw == 3
    masks = dark_class_masks(base, land, sea)
    rows = []
    for sensor, prod in (("S-NPP", "VNP46A3"), ("NOAA-20", "VJ146A3")):
        for p in sorted(glob.glob(str(RAW / prod / "*.h5"))):
            rad, lw_m = read_for_qa(p, window=win)
            with h5py.File(p) as f:
                q = f[f"{G}/{LAYER}_Quality"][sl]
                n = f[f"{G}/{LAYER}_Num"][sl].astype(float)
            n[n == 65535] = np.nan
            rows.append({"sensor": sensor, "month": month_of(p), **controls_for(rad, masks),
                         "obs_median_land": float(np.nanmedian(n[land])),
                         "land_quality1_frac": float((q[land] == 1).mean()),
                         "land_quality2_frac": float((q[land] == 2).mean())})
    df = pd.DataFrame(rows).sort_values(["sensor", "month"]).reset_index(drop=True)
    Path("outputs/monthly").mkdir(parents=True, exist_ok=True)
    df.to_csv("outputs/monthly/monthly_noise_controls.csv", index=False, float_format="%.6g", lineterminator="\n")
    show = ["sensor", "month", "dark_land_mean", "dark_land_frac_positive", "dark_sea_mean", "obs_median_land",
            "land_quality1_frac", "land_quality2_frac"]
    print(df[show].round(4).to_string(index=False))


if __name__ == "__main__":
    main()
