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


def dark_class_masks(baseline_arrays, land_mask, sea_mask) -> dict:
    """Mascaras booleanas dos pixels escuros (mediana zero na linha de base) em terra e no mar."""
    import warnings
    base = np.stack([np.asarray(a, dtype="float64") for a in baseline_arrays])
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        med = np.nanmedian(base, axis=0)
    dark = med == 0
    return {"land": dark & np.asarray(land_mask, bool), "sea": dark & np.asarray(sea_mask, bool)}


def controls_for(array, masks: dict) -> dict:
    """Media e fracao positiva dos pixels escuros de uma camada (terra e mar)."""
    a = np.asarray(array, dtype="float64")
    row = {}
    for k, m in masks.items():
        v = a[m]
        v = v[np.isfinite(v)]
        row[f"n_dark_{k}"] = int(m.sum())
        row[f"dark_{k}_mean"] = float(v.mean()) if v.size else float("nan")
        row[f"dark_{k}_frac_positive"] = float((v > 0).mean()) if v.size else float("nan")
    return row


def background_controls(arrays: dict, land_mask, sea_mask, *, baseline_years) -> pd.DataFrame:
    """Radiancia media e fracao positiva dos pixels escuros (terra e mar), por ano.

    ``arrays``: {ano: array 2D com NaN nos invalidos}. Escuro = mediana (ignorando NaN) nos
    ``baseline_years`` igual a zero. Retorna colunas year, n_dark_land, dark_land_mean,
    dark_land_frac_positive, n_dark_sea, dark_sea_mean, dark_sea_frac_positive.
    """
    masks = dark_class_masks([arrays[y] for y in baseline_years], land_mask, sea_mask)
    rows = [{"year": y, **controls_for(arrays[y], masks)} for y in sorted(arrays)]
    cols = ["year", "n_dark_land", "dark_land_mean", "dark_land_frac_positive",
            "n_dark_sea", "dark_sea_mean", "dark_sea_frac_positive"]
    return pd.DataFrame(rows)[cols]
