#!/usr/bin/env python3
"""Produto anual (A4) x media dos 12 mensais (A3): como diferem, por municipio (2021-2023).

Para cada sensor e ano, compara a radiancia media municipal do composto anual com a media simples
das 12 medias municipais mensais (mesmas mascaras e agregacao). Diferencas esperadas: o anual remove
valores atipicos das observacoes diarias do ano inteiro (criterio de Tukey) e zera < 0,5 nW uma vez;
o mensal faz isso por mes. Saida: outputs/monthly/annual_vs_monthly.csv e resumo no stdout.
"""
import glob
import re
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

from openlux.io import read_blackmarble
from openlux.temporal import annual_table

RAW = Path("data/raw")


def main():
    mun = gpd.read_file(next(glob.iglob(str(RAW / "ibge/RJ_Municipios_2024/*.shp")))).set_crs(
        "EPSG:4326", allow_override=True)[["CD_MUN", "geometry"]]
    rows = []
    for sensor, a3, a4 in (("S-NPP", "VNP46A3", "VNP46A4"), ("NOAA-20", "VJ146A3", "VJ146A4")):
        files = {}
        for p in sorted(glob.glob(str(RAW / a3 / "*.h5"))):
            y, doy = (int(x) for x in re.search(r"\.A(\d{4})(\d{3})\.", p).groups())
            files[y * 1000 + doy] = p      # chave unica ano*1000+dia (mes identificado pelo dia inicial)
        monthly = annual_table(lambda k: read_blackmarble(files[k]), sorted(files), mun, id_col="CD_MUN")
        monthly["year_"] = monthly["year"] // 1000
        annual = {}
        for p in sorted(glob.glob(str(RAW / a4 / "*.h5"))):
            annual[int(re.search(r"\.A(\d{4})001\.", p).group(1))] = p
        for y in sorted({k // 1000 for k in files}):
            ann = annual_table(lambda k: read_blackmarble(annual[k]), [y], mun, id_col="CD_MUN").set_index("CD_MUN")
            m = monthly[monthly.year_ == y].groupby("CD_MUN").mean_radiance.mean()
            n_months = monthly[monthly.year_ == y].year.nunique()
            for cd in mun.CD_MUN:
                rows.append(dict(sensor=sensor, year=y, CD_MUN=cd, annual=ann.loc[cd, "mean_radiance"],
                                 monthly_mean=m.get(cd, np.nan), n_months=n_months))
    df = pd.DataFrame(rows)
    df["ratio_monthly_over_annual"] = df.monthly_mean / df.annual
    Path("outputs/monthly").mkdir(parents=True, exist_ok=True)
    df.to_csv("outputs/monthly/annual_vs_monthly.csv", index=False, float_format="%.8g", lineterminator="\n")
    for (s, y), g in df.groupby(["sensor", "year"]):
        rho = g.annual.corr(g.monthly_mean, method="spearman")
        print(f"{s:8s} {y}  meses={int(g.n_months.iloc[0])}  Spearman={rho:.4f}  razao mensal/anual: mediana {g.ratio_monthly_over_annual.median():.3f} "
              f"[p10 {g.ratio_monthly_over_annual.quantile(.1):.3f}, p90 {g.ratio_monthly_over_annual.quantile(.9):.3f}]  "
              f"|dif| mediana {np.abs(g.monthly_mean - g.annual).median():.3f} nW")


if __name__ == "__main__":
    main()
