"""Indicadores temporais por municipio e comparacao entre configuracoes.

- ``annual_table``: indicadores zonais por ano (uma configuracao de mascara por chamada).
- ``trend``: inclinacao de Theil-Sen e teste de Kendall (Mann-Kendall) sobre os anos
  validos; exige ``min_years`` anos validos, caso contrario devolve NaN (nao extrapola).
- ``change``: variacao absoluta e percentual; o percentual so e definido quando a linha
  de base e >= ``floor`` (evita razoes explosivas em areas escuras). ``floor`` e um
  parametro analitico do pesquisador e deve ser declarado em toda saida.
- ``rank_agreement``: correlacao de postos de Spearman entre duas configuracoes
  (sensibilidade da classificacao relativa dos municipios).
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
from scipy import stats

from openlux.zonal import zonal_indicators


def annual_table(loader, years, polygons, *, id_col: str) -> pd.DataFrame:
    """``loader(year) -> (array, transform)``; devolve tabela longa (id_col, year, ...)."""
    frames = []
    for y in years:
        arr, transform = loader(y)
        z = zonal_indicators(arr, transform, polygons)
        z.insert(0, id_col, polygons[id_col].values)
        z.insert(1, "year", y)
        frames.append(z.reset_index(drop=True))
    return pd.concat(frames, ignore_index=True)


def trend(years, values, *, min_years: int) -> dict:
    y = np.asarray(years, dtype=float)
    v = np.asarray(values, dtype=float)
    ok = np.isfinite(v)
    n = int(ok.sum())
    nan = dict(slope=np.nan, intercept=np.nan, tau=np.nan, p_value=np.nan, n_years=n)
    if n < min_years:
        return nan
    y, v = y[ok], v[ok]
    slope, intercept, _, _ = stats.theilslopes(v, y)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        tau, p = stats.kendalltau(y, v)
    return dict(slope=float(slope), intercept=float(intercept), tau=float(tau),
                p_value=float(p), n_years=n)


def change(baseline, final, *, floor: float) -> dict:
    b = np.asarray(baseline, dtype=float)
    f = np.asarray(final, dtype=float)
    absolute = f - b
    with np.errstate(divide="ignore", invalid="ignore"):
        pct = np.where((b >= floor) & (b > 0), 100.0 * absolute / b, np.nan)
    return dict(abs=absolute, pct=pct)


def rank_agreement(a, b) -> float:
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    ok = np.isfinite(a) & np.isfinite(b)
    if ok.sum() < 3:
        return float("nan")
    return float(stats.spearmanr(a[ok], b[ok]).statistic)
