"""Mudanca significativa por pixel: Mann-Kendall (com correcao de empates) + Sen + FDR (Benjamini-Hochberg).

Para cada pixel com ao menos ``min_n`` anos validos:
 - ``slope``: mediana das inclinacoes pareadas (Theil-Sen), em unidades de radiancia por ano, usando os anos
   reais (anos ausentes nao deslocam o tempo);
 - ``p``: valor-p bilateral do teste de Mann-Kendall, com correcao de continuidade e de empates; pixels sem
   variacao (S = 0 e variancia 0) recebem p = 1.
Como ha centenas de milhares de testes, a significancia usa controle da taxa de falsas descobertas
(Benjamini-Hochberg) sobre os pixels testados; NAO e correcao de dependencia espacial (pixels vizinhos
sao correlacionados; BH e valido sob independencia ou dependencia positiva). Sinal e magnitude vem do Sen.

Limitacoes: o teste detecta tendencia monotonica, nao mudanca de nivel; herda o ruido de fundo do S-NPP
pos-2021 (ver docs/DECISIONS.md); "significativo" nao implica mudanca fisica da iluminacao.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.special import erfc


def pixel_trend(stack, years, *, min_n: int = 8) -> dict:
    """stack (T, R, C) com NaN nos invalidos. Retorna dict de arrays (R, C): n, slope, p."""
    x = np.asarray(stack, dtype="float64")
    t = np.asarray(years, dtype="float64")
    T, R, C = x.shape
    x = x.reshape(T, -1)
    valid = np.isfinite(x)
    n = valid.sum(axis=0)
    ok = n >= min_n
    slope = np.full(x.shape[1], np.nan); p = np.full(x.shape[1], np.nan)
    idx = np.flatnonzero(ok)
    if idx.size:
        xs, vs, ns = x[:, idx], valid[:, idx], n[idx].astype("float64")
        S = np.zeros(idx.size)
        pair = []
        for i in range(T - 1):
            for j in range(i + 1, T):
                m = vs[i] & vs[j]
                d = xs[j] - xs[i]
                S += np.where(m, np.sign(d), 0.0)
                pair.append(np.where(m, d / (t[j] - t[i]), np.nan))
        slope[idx] = np.nanmedian(np.stack(pair), axis=0)
        # correcao de empates: sum_i (c_i - 1)(2 c_i + 5), c_i = tamanho do grupo de valores iguais de i
        tie = np.zeros(idx.size)
        for i in range(T):
            c = ((xs == xs[i]) & vs & vs[i]).sum(axis=0).astype("float64")
            tie += np.where(vs[i], (c - 1) * (2 * c + 5), 0.0)
        var = (ns * (ns - 1) * (2 * ns + 5) - tie) / 18.0
        with np.errstate(divide="ignore", invalid="ignore"):
            z = np.where(S > 0, S - 1, np.where(S < 0, S + 1, 0.0)) / np.sqrt(var)
        pv = erfc(np.abs(np.nan_to_num(z)) / np.sqrt(2.0))
        pv[~(var > 0)] = 1.0
        p[idx] = pv
    return {"n": n.reshape(R, C), "slope": slope.reshape(R, C), "p": p.reshape(R, C)}


def bh_reject(p, alpha: float = 0.05) -> np.ndarray:
    """Benjamini-Hochberg: mascara booleana de rejeicoes (NaN nunca rejeita e nao conta como teste)."""
    p = np.asarray(p, dtype="float64")
    flat = p.ravel()
    ok = np.isfinite(flat)
    out = np.zeros(flat.shape, dtype=bool)
    vals = flat[ok]
    m = vals.size
    if m == 0:
        return out.reshape(p.shape)
    order = np.argsort(vals, kind="stable")
    passed = vals[order] <= alpha * (np.arange(1, m + 1) / m)
    if passed.any():
        kmax = np.flatnonzero(passed).max()
        rej = np.zeros(m, dtype=bool)
        rej[order[: kmax + 1]] = True
        out[np.flatnonzero(ok)] = rej
    return out.reshape(p.shape)


def significant_change(stack, years, *, min_n: int = 8, alpha: float = 0.05, active=None) -> dict:
    """Rotulos por pixel: +1 aumento, -1 reducao, 0 nao significativo/nao testado.

    ``active`` (R, C) restringe os pixels testados (ex.: pixels iluminados em algum ano); None testa todos.
    ``tested`` marca os pixels que entraram no teste (n >= min_n e ativos).
    """
    stack = np.asarray(stack, dtype="float64")
    if active is not None:  # pixels inativos viram NaN: nao sao calculados nem entram no FDR
        stack = np.where(np.asarray(active, dtype=bool)[None], stack, np.nan)
    r = pixel_trend(stack, years, min_n=min_n)
    tested = np.isfinite(r["p"])
    rej = bh_reject(r["p"], alpha)
    label = np.where(rej & (r["slope"] > 0), 1, np.where(rej & (r["slope"] < 0), -1, 0)).astype("int8")
    return {"label": label, "tested": tested, **r}


def trend_shares(overlay: pd.DataFrame, label, tested) -> pd.DataFrame:
    """Participacao (ponderada pela cobertura) de pixels com aumento/reducao significativo, por municipio,
    entre os pixels testados. ``overlay`` tem CD_MUN, pix (indice plano) e cov."""
    pix = overlay["pix"].to_numpy()
    tt = np.asarray(tested).ravel()[pix]
    lab = np.asarray(label).ravel()[pix]
    w = overlay["cov"].to_numpy() * tt
    d = pd.DataFrame({"CD_MUN": overlay["CD_MUN"].to_numpy(), "w": w,
                      "up": w * (lab == 1), "down": w * (lab == -1)})
    s = d.groupby("CD_MUN", sort=True).sum()
    with np.errstate(divide="ignore", invalid="ignore"):
        out = pd.DataFrame({"n_tested_weight": s["w"], "share_increase": s["up"] / s["w"],
                            "share_decrease": s["down"] / s["w"]})
    return out.reset_index()
