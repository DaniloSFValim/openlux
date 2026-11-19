"""Dados do IBGE: populacao residente do Censo 2022 (SIDRA, tabela 4709, variavel 93)."""
from __future__ import annotations

import pandas as pd

SIDRA_TABLE, SIDRA_VARIABLE, SIDRA_YEAR = "4709", "93", "2022"
SIDRA_URL_RJ = (f"https://apisidra.ibge.gov.br/values/t/{SIDRA_TABLE}/n6/in%20n3%2033"
                f"/v/{SIDRA_VARIABLE}/p/{SIDRA_YEAR}")
_MISSING = {"-", "..", "...", "X"}


def parse_sidra_population(rows: list[dict]) -> pd.DataFrame:
    """Converte a resposta JSON da API SIDRA em ``cd_mun`` (str, 7 digitos) e ``population``.

    A primeira linha da API e o cabecalho e e descartada. Valores ausentes
    ('-', '..', '...', 'X') viram NaN. Variavel, ano ou municipio duplicado sao erro.
    """
    data = rows[1:]
    out, seen = [], set()
    for r in data:
        if r["D2C"] != SIDRA_VARIABLE or r["D3C"] != SIDRA_YEAR:
            raise ValueError(f"variavel/ano inesperado: {r['D2C']}/{r['D3C']}")
        cod = r["D1C"]
        if cod in seen:
            raise ValueError(f"municipio duplicado: {cod}")
        seen.add(cod)
        v = r["V"]
        out.append((cod, float("nan") if v in _MISSING else int(v)))
    df = pd.DataFrame(out, columns=["cd_mun", "population"])
    return df
