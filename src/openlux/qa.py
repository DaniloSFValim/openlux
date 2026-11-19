"""Controles de ruido de fundo (QA) da serie temporal.

Motivacao: o guia do Black Marble informa que valores de composto < 0.5 nW cm^-2 sr^-1 sao
zerados para remover ruido residual. Pixels persistentemente escuros (mediana = 0 nos anos
de linha de base) servem entao de controle: se sua radiancia media sobe, o piso de ruido
mudou, e isso nao e crescimento de iluminacao. A classe e definida SOMENTE pelos anos de
linha de base, para nao selecionar pixels olhando o periodo que se quer avaliar.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def background_controls(arrays: dict, land_mask, sea_mask, *, baseline_years) -> pd.DataFrame:
    """Radiancia media e fracao positiva dos pixels escuros (terra e mar), por ano.

    ``arrays``: {ano: array 2D com NaN nos invalidos}. Escuro = mediana (ignorando NaN) nos
    ``baseline_years`` igual a zero. Retorna colunas year, n_dark_land, dark_land_mean,
    dark_land_frac_positive, n_dark_sea, dark_sea_mean, dark_sea_frac_positive.
    """
    base = np.stack([np.asarray(arrays[y], dtype="float64") for y in baseline_years])
    with np.errstate(all="ignore"):
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            med = np.nanmedian(base, axis=0)
    dark = med == 0
    classes = {"land": dark & np.asarray(land_mask, bool), "sea": dark & np.asarray(sea_mask, bool)}
    rows = []
    for y in sorted(arrays):
        a = np.asarray(arrays[y], dtype="float64")
        row = {"year": y}
        for k, m in classes.items():
            v = a[m]
            v = v[np.isfinite(v)]
            row[f"n_dark_{k}"] = int(m.sum())
            row[f"dark_{k}_mean"] = float(v.mean()) if v.size else float("nan")
            row[f"dark_{k}_frac_positive"] = float((v > 0).mean()) if v.size else float("nan")
        rows.append(row)
    cols = ["year", "n_dark_land", "dark_land_mean", "dark_land_frac_positive",
            "n_dark_sea", "dark_sea_mean", "dark_sea_frac_positive"]
    return pd.DataFrame(rows)[cols]
