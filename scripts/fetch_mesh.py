#!/usr/bin/env python3
"""Baixa a Malha Municipal Digital 2024 de uma UF (IBGE) e registra URL, data e SHA-256.

Uso: python scripts/fetch_mesh.py --uf SP
O arquivo bruto fica em data/raw/ibge/ (ignorado pelo git); em data/metadata/downloads/ fica so o registro.
O RJ continua sendo baixado por scripts/fetch_ibge.py (que tambem traz a populacao do SIDRA).
"""
import argparse
import datetime as dt
import re
import sys
import urllib.request
import zipfile
from pathlib import Path

from openlux.io import sha256_file
from openlux.provenance import code_version, write_json

BASE = "https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/malhas_municipais/municipio_2024/UFs"
RAW = Path("data/raw/ibge")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--uf", required=True, help="sigla da UF, por exemplo SP")
    uf = ap.parse_args().uf.upper()
    if not re.fullmatch(r"[A-Z]{2}", uf):
        sys.exit("--uf deve ser a sigla de duas letras")
    url = f"{BASE}/{uf}/{uf}_Municipios_2024.zip"
    dest = RAW / f"{uf}_Municipios_2024.zip"
    dest.parent.mkdir(parents=True, exist_ok=True)
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    req = urllib.request.Request(url, headers={"User-Agent": "openlux-downloader"})
    with urllib.request.urlopen(req, timeout=180) as r, open(dest, "wb") as f:
        while block := r.read(1 << 20):
            f.write(block)
    with zipfile.ZipFile(dest) as z:
        z.extractall(RAW / f"{uf}_Municipios_2024")
    write_json(f"data/metadata/downloads/ibge_malha_{uf}.json", dict(
        institution="IBGE", acquired_utc=now, code=code_version(),
        files=[dict(name=dest.name, url=url, sha256=sha256_file(dest), size_bytes=dest.stat().st_size,
                    description=f"Malha Municipal Digital 2024, {uf} (EPSG:4674, SIRGAS 2000)")]))
    print("OK", dest, sha256_file(dest))


if __name__ == "__main__":
    main()
