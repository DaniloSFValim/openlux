#!/usr/bin/env python3
"""Baixa a malha de setores censitarios do Censo 2022 (RJ, com atributos) e confere o SHA-256.

O arquivo (~75 MB) fica em data/raw/ (ignorado pelo git; redistribuicao sujeita aos termos do IBGE).
Em data/metadata/downloads/ficam so URL, data, tamanho e SHA-256. Se o arquivo local ja tem o hash
esperado, nao e baixado de novo (``acquired_utc`` e a data de modificacao do arquivo).
"""
import datetime as dt
import sys
import urllib.request
from pathlib import Path

from openlux.io import sha256_file
from openlux.provenance import code_version, write_json

URL = ("https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/Agregados_por_Setores_Censitarios/"
       "malha_com_atributos/setores/gpkg/UF/RJ/RJ_setores_CD2022.gpkg")
EXPECTED_SHA256 = "ec6cecdc0297d1b79e25e2772f531cad5c99ac57bc3ac1b30fb08418dc513222"
DEST = Path("data/raw/ibge/setores2022/RJ_setores_CD2022.gpkg")


def main():
    if not (DEST.exists() and sha256_file(DEST) == EXPECTED_SHA256):
        DEST.parent.mkdir(parents=True, exist_ok=True)
        part = DEST.with_suffix(".part")
        req = urllib.request.Request(URL, headers={"User-Agent": "openlux-downloader"})
        with urllib.request.urlopen(req, timeout=300) as r, open(part, "wb") as f:
            while block := r.read(1 << 20):
                f.write(block)
        if sha256_file(part) != EXPECTED_SHA256:
            part.unlink()
            sys.exit("SHA-256 diferente do esperado: o IBGE pode ter republicado o arquivo; investigue antes de usar.")
        part.replace(DEST)
    acquired = dt.datetime.fromtimestamp(DEST.stat().st_mtime, dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    write_json("data/metadata/downloads/ibge_setores_rj.json", dict(
        institution="IBGE", acquired_utc=acquired, code=code_version(),
        files=[dict(name=DEST.name, url=URL, sha256=sha256_file(DEST), size_bytes=DEST.stat().st_size,
                    description="Malha de setores censitarios 2022 com atributos, RJ (CD2022, SIRGAS 2000, EPSG:4674); "
                                "atributo v0001 = populacao residente")]))
    print("OK", DEST, sha256_file(DEST))


if __name__ == "__main__":
    main()
