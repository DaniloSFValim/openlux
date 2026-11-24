#!/usr/bin/env python3
"""Confere o CSV de medicoes de campo ANTES da analise (modelo: docs/field/measurements_template.csv).

Uso: python scripts/check_measurements.py campo.csv [--tile h13v11] [--max-radius-km 50]
Sai com codigo 1 se houver ERROS (avisos pedem conferencia, mas nao bloqueiam). Nao altera o arquivo.
"""
import argparse
import re
import sys

import pandas as pd

from openlux.field import validate_measurements
from openlux.geo import tile_transform


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--tile", default="h13v11", help="tile do Black Marble que cobre os locais (padrao: h13v11, RJ e leste de SP)")
    ap.add_argument("--max-radius-km", type=float, default=50.0, help="maior raio de contexto da analise")
    a = ap.parse_args()
    m = re.fullmatch(r"h(\d{2})v(\d{2})", a.tile)
    if not m:
        sys.exit("--tile deve ter o formato hNNvNN, por exemplo h13v11")
    t = tile_transform(int(m.group(1)), int(m.group(2)))
    bounds = (t.c, t.f - 10.0, t.c + 10.0, t.f)
    df = pd.read_csv(a.csv, dtype=str, keep_default_na=False)
    iss = validate_measurements(df, tile_bounds=bounds, max_radius_km=a.max_radius_km)
    nerr, nwarn = int((iss["severity"] == "erro").sum()), int((iss["severity"] == "aviso").sum())
    for r in iss.itertuples():
        print(f"[{r.severity.upper()}] linha {r.row}, coluna {r.column}: {r.message}")
    print(f"{len(df)} leituras, {df['site_id'].nunique() if 'site_id' in df else '?'} locais: {nerr} erro(s), {nwarn} aviso(s).")
    sys.exit(1 if nerr else 0)


if __name__ == "__main__":
    main()
