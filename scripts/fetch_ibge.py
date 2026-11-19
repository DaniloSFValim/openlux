#!/usr/bin/env python3
"""Baixa a malha municipal IBGE 2024 (RJ) e a populacao do Censo 2022 (SIDRA 4709/v93).

Os dados brutos ficam em data/raw/ (ignorado pelo git; redistribuicao sujeita aos termos
do IBGE). Em data/metadata/downloads/ ficam apenas URL, data, tamanho e SHA-256.
"""
import datetime as dt
import json
import sys
import urllib.request
import zipfile
from pathlib import Path

from openlux.ibge import SIDRA_URL_RJ, parse_sidra_population
from openlux.io import sha256_file
from openlux.provenance import code_version, write_json

MESH_URL = ("https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/"
            "malhas_municipais/municipio_2024/UFs/RJ/RJ_Municipios_2024.zip")
RAW = Path("data/raw/ibge")


def get(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "openlux-downloader"})
    with urllib.request.urlopen(req, timeout=120) as r, open(dest, "wb") as f:
        f.write(r.read())


def main():
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    zip_path, pop_path = RAW / "RJ_Municipios_2024.zip", RAW / "sidra_4709_v93_RJ_2022.json"
    get(MESH_URL, zip_path)
    get(SIDRA_URL_RJ, pop_path)
    with zipfile.ZipFile(zip_path) as z:
        z.extractall(RAW / "RJ_Municipios_2024")
    pop = parse_sidra_population(json.loads(pop_path.read_text(encoding="utf-8")))
    if len(pop) != 92 or pop.population.isna().any():
        sys.exit(f"populacao inesperada: {len(pop)} municipios, NaN={pop.population.isna().sum()}")
    write_json("data/metadata/downloads/ibge_rj.json", dict(
        institution="IBGE", acquired_utc=now, code=code_version(),
        files=[
            dict(name=zip_path.name, url=MESH_URL, sha256=sha256_file(zip_path),
                 size_bytes=zip_path.stat().st_size,
                 description="Malha Municipal Digital 2024, RJ (EPSG:4674, SIRGAS 2000)"),
            dict(name=pop_path.name, url=SIDRA_URL_RJ, sha256=sha256_file(pop_path),
                 size_bytes=pop_path.stat().st_size,
                 description="Censo Demografico 2022, populacao residente (SIDRA t4709, v93)"),
        ],
        checks=dict(n_municipios=len(pop), populacao_total_rj=int(pop.population.sum())),
    ))
    print("OK", len(pop), "municipios; populacao total", int(pop.population.sum()))


if __name__ == "__main__":
    main()
