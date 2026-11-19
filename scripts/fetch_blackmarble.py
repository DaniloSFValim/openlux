#!/usr/bin/env python3
"""Baixa a serie anual/mensal Black Marble de um tile e registra a proveniencia.

Exemplo:  EARTHDATA_TOKEN=... python scripts/fetch_blackmarble.py --years 2012-2025
O token e lido SOMENTE da variavel de ambiente; nunca e gravado.
"""
import argparse
import datetime as dt
import sys
from pathlib import Path

from openlux.download import DownloadFailed, download_verified, laads_find_file, token_from_env
from openlux.provenance import code_version, write_json

PRODUCT_DOI = {"VNP46A4": "10.5067/VIIRS/VNP46A4.002", "VNP46A3": "10.5067/VIIRS/VNP46A3.002"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--product", default="VNP46A4", choices=sorted(PRODUCT_DOI))
    ap.add_argument("--tile", default="h13v11")
    ap.add_argument("--years", default="2012-2025", help="ex.: 2012-2025")
    ap.add_argument("--out", default="data/raw")
    ap.add_argument("--meta", default="data/metadata/downloads")
    a = ap.parse_args()
    y0, y1 = (int(x) for x in a.years.split("-"))
    token = token_from_env()
    if not token:
        sys.exit("Defina EARTHDATA_TOKEN no ambiente (nunca em arquivos versionados).")
    files, failures = [], []
    for year in range(y0, y1 + 1):
        try:
            name, url = laads_find_file(a.product, year, 1, a.tile, token=token)
            rec = download_verified(url, Path(a.out) / a.product / name, token=token)
            files.append(dict(year=year, name=name, **{k: rec[k] for k in
                              ("url", "sha256", "size_bytes", "downloaded_utc")}))
            print(f"OK  {year} {name} {rec['size_bytes']} B sha256={rec['sha256'][:12]}...")
        except Exception as e:  # registra e segue: o relatorio final lista as falhas
            failures.append(dict(year=year, error=str(e)))
            print(f"FALHA {year}: {e}")
    write_json(Path(a.meta) / f"{a.product}_{a.tile}.json", dict(
        source="NASA LAADS DAAC", institution="NASA / LAADS DAAC",
        product=a.product, doi=PRODUCT_DOI[a.product], collection="Colecao 2.0 (versao 002)",
        tile=a.tile, base_url="https://ladsweb.modaps.eosdis.nasa.gov",
        acquired_utc=dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        code=code_version(Path(__file__).resolve().parent.parent),
        files=files, failures=failures))
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
