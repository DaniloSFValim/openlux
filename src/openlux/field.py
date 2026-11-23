"""Validacao em campo com SQM (Sky Quality Meter): conversoes, controle de qualidade, contexto de radiancia
do satelite em torno de cada local e estatistica de associacao.

O que isto testa: se o brilho zenital medido no chao (SQM, mag/arcsec2) cresce, em ordem de postos, com a
radiancia noturna vista pelo satelite no entorno do local. NAO e calibracao absoluta: sao grandezas
diferentes (luz emitida para cima, vista do espaco, x brilho do ceu, que integra luz de dezenas de km), e a
conversao mag->luminancia e aproximada (Unihedron; Bara et al., 2020 mostram que depende do espectro).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.stats import rankdata

#: Constante da formula oficial da Unihedron (manual do SQM-L e calculadora): L[cd/m2] = 10,8e4 * 10^(-0,4 m).
LUMINANCE_ZERO_POINT = 108000.0


def mpsas_to_luminance(m):
    """mag/arcsec2 (escala do SQM) -> cd/m2. Aproximada: depende do espectro do ceu."""
    return LUMINANCE_ZERO_POINT * 10.0 ** (-0.4 * np.asarray(m, dtype="float64"))


def luminance_to_mpsas(lum):
    return -2.5 * np.log10(np.asarray(lum, dtype="float64") / LUMINANCE_ZERO_POINT)


@dataclass(frozen=True)
class QCParams:
    """Criterios de controle de qualidade. Valores PROPOSTOS pelo projeto (nao vem de norma) e fixados na
    pre-especificacao antes da coleta (docs/field/preregistration.json)."""
    max_sun_alt_deg: float = -18.0    # fim do crepusculo astronomico
    max_moon_alt_deg: float = 0.0     # Lua abaixo do horizonte
    max_reading_range_mag: float = 0.2  # amplitude das leituras de uma visita
    min_readings: int = 5


def qc_visits(readings: pd.DataFrame, p: QCParams = QCParams()) -> pd.DataFrame:
    """Uma linha por visita (site_id, visit_id): mediana das leituras, amplitude, e se passou o controle.

    Colunas de entrada (uma linha por leitura): site_id, visit_id, sqm_mpsas, sun_alt_deg, moon_alt_deg,
    cloud_free (bool, observador), temp_c. Sol, Lua, nuvens e temperatura vem do registro do observador.
    """
    rows = []
    for (site, visit), g in readings.groupby(["site_id", "visit_id"], sort=True):
        v = g["sqm_mpsas"].to_numpy(dtype="float64")
        reasons = []
        if len(v) < p.min_readings:
            reasons.append(f"leituras < {p.min_readings}")
        if g["sun_alt_deg"].max() > p.max_sun_alt_deg:
            reasons.append("sol acima do limite")
        if g["moon_alt_deg"].max() > p.max_moon_alt_deg:
            reasons.append("lua acima do horizonte")
        if not bool(g["cloud_free"].all()):
            reasons.append("nuvens")
        rng = float(v.max() - v.min()) if len(v) else np.nan
        if len(v) and rng > p.max_reading_range_mag:
            reasons.append("dispersao das leituras")
        rows.append(dict(site_id=site, visit_id=visit, n_readings=len(v), sqm_mpsas=float(np.median(v)),
                         range_mag=rng, temp_c=float(g["temp_c"].mean()), reasons="; ".join(reasons),
                         **{"pass": not reasons}))
    return pd.DataFrame(rows)


def site_summary(readings: pd.DataFrame, p: QCParams = QCParams()) -> pd.DataFrame:
    """Por local: media da luminancia (cd/m2) das visitas validas (media feita em luminancia, nao em magnitude)."""
    v = qc_visits(readings, p)
    ok = v[v["pass"]].copy()
    ok["luminance_cd_m2"] = mpsas_to_luminance(ok["sqm_mpsas"].to_numpy())
    s = ok.groupby("site_id", sort=True).agg(n_valid_visits=("visit_id", "count"),
                                             luminance_cd_m2=("luminance_cd_m2", "mean"),
                                             visit_spread_mag=("sqm_mpsas", lambda x: float(x.max() - x.min()))).reset_index()
    s["sqm_mpsas"] = luminance_to_mpsas(s["luminance_cd_m2"].to_numpy())   # magnitude equivalente a luminancia media
    return s


def context_radiance(radiance, transform, lon, lat, radii_km) -> dict:
    """Radiancia media (ponderada pela area do pixel, cos(lat)) dos pixels validos cujo CENTRO esta a ate r km do
    local, para cada raio. Retorna {r: {mean, n_pixels, valid_fraction}}. Aproximacao: inclusao por centro do
    pixel (de pixel ~460 m, nao use raios menores que ~1 km). ``valid_fraction`` = pixels validos / pixels no raio
    (sobe de importancia junto ao mar, onde a mascara de agua remove pixels)."""
    rad = np.asarray(radiance, dtype="float64")
    nrows, ncols = rad.shape
    km_lat = 110.574
    out = {}
    for r in radii_km:
        dlat = r / km_lat
        dlon = r / (111.320 * np.cos(np.radians(lat)))
        c0 = max(int(np.floor((lon - dlon - transform.c) / transform.a)), 0)
        c1 = min(int(np.ceil((lon + dlon - transform.c) / transform.a)) + 1, ncols)
        r0 = max(int(np.floor((transform.f - (lat + dlat)) / abs(transform.e))), 0)
        r1 = min(int(np.ceil((transform.f - (lat - dlat)) / abs(transform.e))) + 1, nrows)
        if c1 <= c0 or r1 <= r0:
            out[r] = dict(mean=float("nan"), n_pixels=0, valid_fraction=float("nan"))
            continue
        cc = transform.c + (np.arange(c0, c1) + 0.5) * transform.a
        rr = transform.f + (np.arange(r0, r1) + 0.5) * transform.e
        LON, LAT = np.meshgrid(cc, rr)
        dx = (LON - lon) * 111.320 * np.cos(np.radians(lat))
        dy = (LAT - lat) * km_lat
        inside = np.hypot(dx, dy) <= r
        block = rad[r0:r1, c0:c1]
        valid = inside & np.isfinite(block)
        w = np.cos(np.radians(LAT))
        n_in = int(inside.sum())
        mean = float((block[valid] * w[valid]).sum() / w[valid].sum()) if valid.any() else float("nan")
        out[r] = dict(mean=mean, n_pixels=int(valid.sum()), valid_fraction=float(valid.sum() / n_in) if n_in else float("nan"))
    return out


def _rho(x_rank, y_rank):
    xr = x_rank - x_rank.mean(axis=-1, keepdims=True)
    yr = y_rank - y_rank.mean(axis=-1, keepdims=True)
    return (xr * yr).sum(axis=-1) / np.sqrt((xr ** 2).sum(axis=-1) * (yr ** 2).sum(axis=-1))


def spearman_by_radius(y, x_by_radius) -> dict:
    """Spearman entre y (luminancia do ceu) e a radiancia de contexto de cada raio. Retorna {raio: rho}."""
    yr = rankdata(np.asarray(y, dtype="float64"))
    return {r: float(_rho(rankdata(np.asarray(x, dtype="float64")), yr)) for r, x in x_by_radius.items()}


def permutation_max_spearman(y, x_by_radius, *, n_perm: int = 10000, seed: int = 0) -> dict:
    """Teste de permutacao do MAXIMO de rho sobre os raios (a escolha do raio entra no teste, entao o valor-p
    ja desconta a busca). Hipotese nula: nao ha associacao entre o ceu e o entorno; embaralha os locais."""
    radii = sorted(x_by_radius)
    X = np.stack([rankdata(np.asarray(x_by_radius[r], dtype="float64")) for r in radii])      # (R, n)
    yr = rankdata(np.asarray(y, dtype="float64"))
    obs_all = _rho(X, yr[None, :])
    obs = float(obs_all.max())
    rng = np.random.default_rng(seed)
    n = yr.size
    perms = np.stack([rng.permutation(yr) for _ in range(n_perm)])                              # (P, n)
    null = np.stack([_rho(X[i][None, :], perms) for i in range(len(radii))]).max(axis=0)         # (P,)
    p = float((1 + (null >= obs - 1e-12).sum()) / (n_perm + 1))
    return dict(observed_max=obs, best_radius=radii[int(obs_all.argmax())], p_value=p, n_perm=n_perm, seed=seed,
                rho_by_radius={r: float(v) for r, v in zip(radii, obs_all)})


def leave_one_out(y, x) -> list:
    """rho de Spearman retirando cada local, um por vez (sensibilidade a um unico local)."""
    y, x = np.asarray(y, dtype="float64"), np.asarray(x, dtype="float64")
    return [float(_rho(rankdata(np.delete(x, i)), rankdata(np.delete(y, i)))) for i in range(len(y))]
