#!/usr/bin/env python3
"""Serie municipal do NOAA-20 (VJ146A4, 2018-2025) e comparacao com o S-NPP por municipio.

Pre-requisitos: scripts/fetch_blackmarble.py (VNP46A4 e VJ146A4), scripts/fetch_ibge.py e
scripts/run_annual.py (gera outputs/annual/annual_main.csv do S-NPP). Saidas em outputs/noaa20/ e
outputs/sensors/ (nao versionadas).
"""
import glob
import json
import re
from pathlib import Path

import geopandas as gpd
import pandas as pd

from openlux.ibge import parse_sidra_population
from openlux.pipeline import compare_municipal_series, run_annual
from openlux.provenance import write_json

RAW = Path("data/raw")


def main():
    files = {int(re.search(r"\.A(\d{4})001\.", p).group(1)): Path(p)
             for p in sorted(glob.glob(str(RAW / "VJ146A4" / "*.h5")))}
    mun = gpd.read_file(next(glob.iglob(str(RAW / "ibge/RJ_Municipios_2024/*.shp")))).set_crs(
        "EPSG:4326", allow_override=True)
    pop = parse_sidra_population(json.loads((RAW / "ibge/sidra_4709_v93_RJ_2022.json").read_text(encoding="utf-8")))
    polys = mun[["CD_MUN", "NM_MUN", "geometry"]]
    # Serie NOAA-20 completa pelo mesmo pipeline (sensibilidade e controles de ruido incluidos).
    run_annual(files, polys, "CD_MUN", pop, "outputs/noaa20", extra_cols=("NM_MUN",),
               trend_windows={"2018_2025": (2018, 2025)}, min_years=8,
               qa_baseline_years=(2018, 2019, 2020, 2021))
    snpp = pd.read_csv("outputs/annual/annual_main.csv", dtype={"CD_MUN": str})
    n20 = pd.read_csv("outputs/noaa20/annual_main.csv", dtype={"CD_MUN": str})
    names = mun[["CD_MUN", "NM_MUN"]]
    out = Path("outputs/sensors")
    out.mkdir(parents=True, exist_ok=True)
    summary = {}
    for name, window, min_years, change in (("2018_2025", (2018, 2025), 8, (2021, 2025)),
                                            ("2018_2021", (2018, 2021), 4, None)):
        df, s = compare_municipal_series(snpp, n20, "CD_MUN", window=window, min_years=min_years,
                                         change_years=change)
        df = df.merge(names, on="CD_MUN").sort_values("CD_MUN")
        df.to_csv(out / f"municipal_comparison_{name}.csv", index=False, float_format="%.10g", lineterminator="\n")
        summary[name] = s
    # por ano: concordancia dos NIVEIS municipais entre sensores
    yearly = {}
    for y in range(2018, 2026):
        a = snpp[snpp.year == y].set_index("CD_MUN").mean_radiance
        b = n20[n20.year == y].set_index("CD_MUN").mean_radiance.reindex(a.index)
        yearly[str(y)] = dict(spearman=float(a.corr(b, method="spearman")), median_ratio_b_over_a=float((b / a).median()),
                              median_abs_diff=float((b - a).abs().median()))
    summary["levels_by_year"] = yearly
    write_json(out / "summary.json", summary)
    print(json.dumps(summary, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
