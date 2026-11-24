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
    local, para cada raio. Retorna {r: {mean, n_pixels, valid_fraction, complete}}; ``complete`` = False quando o disco do raio
    ultrapassa a borda do raster (contexto incompleto: nao use esse local sem tratar). Aproximacao: inclusao por centro do
    pixel (de pixel ~460 m, nao use raios menores que ~1 km). ``valid_fraction`` = pixels validos / pixels no raio
    (sobe de importancia junto ao mar, onde a mascara de agua remove pixels)."""
    rad = np.asarray(radiance, dtype="float64")
    nrows, ncols = rad.shape
    km_lat = 110.574
    west, north = transform.c, transform.f
    east, south = west + ncols * transform.a, north + nrows * transform.e
    out = {}
    for r in radii_km:
        dlat = r / km_lat
        dlon = r / (111.320 * np.cos(np.radians(lat)))
        # disco inteiro dentro do raster? (senao a media usa so parte do entorno: contexto incompleto)
        complete = bool(lon - dlon >= west and lon + dlon <= east and lat + dlat <= north and lat - dlat >= south)
        c0 = max(int(np.floor((lon - dlon - transform.c) / transform.a)), 0)
        c1 = min(int(np.ceil((lon + dlon - transform.c) / transform.a)) + 1, ncols)
        r0 = max(int(np.floor((transform.f - (lat + dlat)) / abs(transform.e))), 0)
        r1 = min(int(np.ceil((transform.f - (lat - dlat)) / abs(transform.e))) + 1, nrows)
        if c1 <= c0 or r1 <= r0:
            out[r] = dict(mean=float("nan"), n_pixels=0, valid_fraction=float("nan"), complete=False)
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
        out[r] = dict(mean=mean, n_pixels=int(valid.sum()), valid_fraction=float(valid.sum() / n_in) if n_in else float("nan"),
                      complete=complete)
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


# ---------------------------------------------------------------- validacao do arquivo de medicoes
REQUIRED_COLUMNS = ("site_id", "visit_id", "datetime_local", "lat", "lon", "sqm_mpsas", "sun_alt_deg", "moon_alt_deg",
                    "cloud_free", "temp_c", "device_id", "instrument_type", "observer", "ephemeris_source")
#: Tipos de instrumento aceitos. Apenas ``sqm`` e, depois de calibrada contra o SQM de referencia, ``camera_calibrated``
#: podem chegar ao nivel de validacao; ``phone`` e ``camera_uncalibrated`` ficam sempre como dado exploratorio.
INSTRUMENT_TYPES = ("sqm", "camera_calibrated", "camera_uncalibrated", "phone")
_TRUE, _FALSE = {"true", "1", "sim", "yes", "verdadeiro"}, {"false", "0", "nao", "não", "no", "falso"}


def parse_bool(x):
    """Aceita true/false, 1/0, sim/nao (qualquer caixa); devolve None se nao reconhecer."""
    if isinstance(x, (bool, np.bool_)):
        return bool(x)
    t = str(x).strip().lower()
    return True if t in _TRUE else False if t in _FALSE else None


def validate_measurements(df: pd.DataFrame, *, tile_bounds=None, max_radius_km: float = 50.0, now=None,
                          min_readings: int = QCParams().min_readings) -> pd.DataFrame:
    """Verifica o CSV de medicoes antes da analise. Retorna uma linha por problema: severity ('erro' ou 'aviso'),
    row (numero da linha no CSV, cabecalho = 1), column e message. Erros impedem a analise; avisos pedem conferencia.

    Os limites de sanidade (SQM entre 10 e 25 = erro; fora de 16 a 23 = aviso) sao verificacoes de plausibilidade
    do projeto, nao propriedades do instrumento. ``tile_bounds`` = (oeste, sul, leste, norte) em graus.
    """
    issues = []

    def add(sev, row, col, msg):
        issues.append(dict(severity=sev, row=int(row), column=col, message=msg))

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    for c in missing:
        add("erro", 1, c, f"coluna obrigatoria ausente: {c}")
    if missing:
        return pd.DataFrame(issues, columns=["severity", "row", "column", "message"])
    now = pd.Timestamp.now() if now is None else pd.Timestamp(now)
    d = df.reset_index(drop=True)
    line = lambda i: i + 2          # indice 0 = linha 2 do CSV (a 1 e o cabecalho)
    num = {c: pd.to_numeric(d[c], errors="coerce") for c in ("lat", "lon", "sqm_mpsas", "sun_alt_deg", "moon_alt_deg", "temp_c")}
    when = pd.to_datetime(d["datetime_local"], errors="coerce")
    for i in range(len(d)):
        for c in ("site_id", "visit_id", "device_id", "observer"):
            if str(d.at[i, c]).strip() in ("", "nan", "None"):
                add("erro", line(i), c, f"{c} vazio")
        if d.at[i, "instrument_type"] not in INSTRUMENT_TYPES:
            add("erro", line(i), "instrument_type", f"instrument_type invalido ({d.at[i, 'instrument_type']!r}); use um de {list(INSTRUMENT_TYPES)}")
        for c, lo, hi in (("lat", -90, 90), ("lon", -180, 180), ("sun_alt_deg", -90, 90), ("moon_alt_deg", -90, 90), ("temp_c", -50, 60)):
            v = num[c].iat[i]
            if pd.isna(v):
                add("erro", line(i), c, f"{c} ausente ou nao numerico")
            elif not lo <= v <= hi:
                add("erro", line(i), c, f"{c} = {v} fora do intervalo possivel [{lo}, {hi}]")
        v = num["sqm_mpsas"].iat[i]
        if pd.isna(v):
            add("erro", line(i), "sqm_mpsas", "sqm_mpsas ausente ou nao numerico")
        elif not 10 <= v <= 25:
            add("erro", line(i), "sqm_mpsas", f"sqm_mpsas = {v} nao e fisico (esperado entre 10 e 25 mag/arcsec2)")
        elif not 16 <= v <= 23:
            add("aviso", line(i), "sqm_mpsas", f"sqm_mpsas = {v} fora da faixa tipica (16 a 23): confira a leitura")
        if parse_bool(d.at[i, "cloud_free"]) is None:
            add("erro", line(i), "cloud_free", f"cloud_free nao reconhecido ({d.at[i, 'cloud_free']!r}); use true/false")
        if pd.isna(when.iat[i]):
            add("erro", line(i), "datetime_local", "datetime_local nao e uma data/hora valida (use AAAA-MM-DDTHH:MM:SS)")
        elif when.iat[i] > now:
            add("aviso", line(i), "datetime_local", "datetime_local esta no futuro")
        elif when.iat[i].year < 2012:
            add("aviso", line(i), "datetime_local", "datetime_local anterior a 2012 (inicio da serie VIIRS)")
    # coerencia entre linhas
    for site, g in d.assign(_lat=num["lat"], _lon=num["lon"]).groupby("site_id"):
        if (g["_lat"].max() - g["_lat"].min() > 0.001) or (g["_lon"].max() - g["_lon"].min() > 0.001):
            add("erro", line(int(g.index[0])), "lat", f"coordenadas do local {site} variam mais de ~100 m entre as linhas")
    for visit, g in d.assign(_day=when.dt.date).groupby("visit_id"):
        if g["device_id"].nunique() > 1:
            add("erro", line(int(g.index[0])), "device_id", f"a visita {visit} tem mais de um aparelho (use visit_id diferentes)")
        if g["site_id"].nunique() > 1 or g["_day"].nunique() > 1:
            add("erro", line(int(g.index[0])), "visit_id", f"a visita {visit} mistura locais ou dias diferentes")
        if len(g) < min_readings:
            add("aviso", line(int(g.index[0])), "sqm_mpsas", f"a visita {visit} tem {len(g)} leituras (< {min_readings}): sera descartada no controle de qualidade")
    dup = d.duplicated(keep="first")
    for i in d.index[dup][:20]:
        add("aviso", line(int(i)), "site_id", "linha duplicada (identica a uma anterior)")
    if dup.sum() > 20:
        add("aviso", 0, "site_id", f"... e mais {int(dup.sum()) - 20} linhas duplicadas")
    if tile_bounds is not None:
        west, south, east, north = tile_bounds
        for i in range(len(d)):
            la, lo = num["lat"].iat[i], num["lon"].iat[i]
            if pd.isna(la) or pd.isna(lo):
                continue
            dlat = max_radius_km / 110.574
            dlon = max_radius_km / (111.320 * np.cos(np.radians(la)))
            if not (west <= lo <= east and south <= la <= north):
                add("erro", line(i), "lon", "local fora do tile de satelite carregado")
            elif lo - dlon < west or lo + dlon > east or la - dlat < south or la + dlat > north:
                add("erro", line(i), "lon", f"local a menos de {max_radius_km:g} km da borda do tile: contexto de satelite incompleto")
    out = pd.DataFrame(issues, columns=["severity", "row", "column", "message"])
    return out.drop_duplicates().reset_index(drop=True)


# ---------------------------------------------------------------- calibracao cruzada entre aparelhos e niveis de instrumento
@dataclass(frozen=True)
class CalibrationParams:
    """Criterios para aceitar um aparelho alem do de referencia. PROPOSTAS do projeto (nao vem de norma), a congelar na
    pre-especificacao antes da coleta (docs/field/preregistration.json)."""
    min_sites: int = 2             # locais com visitas lado a lado (um claro e um escuro e o ideal)
    min_pairs: int = 2             # visitas lado a lado no total
    max_abs_offset_mag: float = 0.3    # desvio medio maximo aceito em relacao a referencia (mag/arcsec2)
    max_offset_spread_mag: float = 0.15  # variacao maxima do desvio entre locais (desvio que muda com o brilho nao e constante)


def night_key(datetime_local) -> str:
    """Noite da leitura: a data local de (hora - 12 h), para que leituras depois da meia-noite pertencam a noite anterior."""
    return (pd.Timestamp(datetime_local) - pd.Timedelta(hours=12)).date().isoformat()


def _visit_table(readings: pd.DataFrame, qc: QCParams) -> pd.DataFrame:
    v = qc_visits(readings, qc)
    meta = (readings.groupby(["site_id", "visit_id"], sort=True)
            .agg(device_id=("device_id", "first"), datetime_local=("datetime_local", "min")).reset_index())
    out = v.merge(meta, on=["site_id", "visit_id"])
    out["night"] = out["datetime_local"].map(night_key)
    return out[out["pass"]]


def colocated_offsets(readings: pd.DataFrame, reference_device: str, params: CalibrationParams = CalibrationParams(),
                      qc: QCParams = QCParams()) -> pd.DataFrame:
    """Desvio de cada aparelho em relacao ao de referencia, estimado em visitas LADO A LADO (mesmo local e mesma noite,
    ambas aprovadas no controle de qualidade). ``offset_mag`` = mediana de (magnitude do aparelho - magnitude da referencia);
    a magnitude corrigida do aparelho e ``bruta - offset_mag``. Uma linha por aparelho diferente da referencia, com ``ok``
    e ``reasons`` (vazio quando aprovado)."""
    visits = _visit_table(readings, qc)
    ref = visits[visits["device_id"] == reference_device]
    rows = []
    for dev in sorted(set(readings["device_id"]) - {reference_device}):
        d = visits[visits["device_id"] == dev]
        pairs = d.merge(ref, on=["site_id", "night"], suffixes=("_d", "_r"))
        diffs = (pairs["sqm_mpsas_d"] - pairs["sqm_mpsas_r"]).to_numpy(dtype="float64")
        per_site = pairs.assign(diff=diffs).groupby("site_id")["diff"].median() if len(pairs) else pd.Series(dtype="float64")
        n_sites, n_pairs = int(per_site.size), int(len(pairs))
        offset = float(np.median(diffs)) if n_pairs else float("nan")
        spread = float(per_site.max() - per_site.min()) if n_sites >= 1 else float("nan")
        reasons = []
        if n_pairs == 0:
            reasons.append("nenhuma visita lado a lado com a referencia")
        else:
            if n_sites < params.min_sites:
                reasons.append(f"locais lado a lado ({n_sites}) < {params.min_sites}")
            if n_pairs < params.min_pairs:
                reasons.append(f"visitas lado a lado ({n_pairs}) < {params.min_pairs}")
            if abs(offset) > params.max_abs_offset_mag:
                reasons.append(f"desvio medio {offset:+.2f} mag acima de {params.max_abs_offset_mag}")
            if n_sites >= 2 and spread > params.max_offset_spread_mag:
                reasons.append(f"o desvio varia {spread:.2f} mag entre locais (> {params.max_offset_spread_mag}): nao e constante")
        rows.append(dict(device_id=dev, offset_mag=offset, spread_mag=spread, n_sites=n_sites, n_pairs=n_pairs,
                         ok=not reasons, reasons="; ".join(reasons)))
    return pd.DataFrame(rows, columns=["device_id", "offset_mag", "spread_mag", "n_sites", "n_pairs", "ok", "reasons"])


def apply_calibration(readings: pd.DataFrame, offsets: pd.DataFrame, reference_device: str) -> pd.DataFrame:
    """Copia de ``readings`` com ``sqm_mpsas_raw`` (valor original) e ``sqm_mpsas`` corrigido (bruto - desvio) para os
    aparelhos calibrados. Aparelhos nao calibrados mantem o valor bruto (e devem ser tratados como exploratorios)."""
    out = readings.copy()
    out["sqm_mpsas_raw"] = pd.to_numeric(out["sqm_mpsas"], errors="coerce")
    off = {r.device_id: r.offset_mag for r in offsets.itertuples() if bool(r.ok)}
    shift = out["device_id"].map(off).fillna(0.0)
    out["sqm_mpsas"] = out["sqm_mpsas_raw"] - shift
    return out


def instrument_tier(instrument_type: str, *, is_reference: bool, calibration_ok: bool) -> str:
    """'validacao' (entra na estatistica confirmatoria) ou 'exploratorio'. Celular e camera sem calibracao nunca chegam
    ao nivel de validacao; SQM e camera calibrada chegam se forem a referencia ou passarem na calibracao cruzada."""
    if instrument_type == "sqm" and is_reference:
        return "validacao"
    if instrument_type in ("sqm", "camera_calibrated") and calibration_ok:
        return "validacao"
    return "exploratorio"


def split_validation_readings(readings: pd.DataFrame, offsets: pd.DataFrame, reference_device: str):
    """Separa as leituras em (validacao, exploratorio), ja com a correcao de desvio aplicada nas de validacao."""
    cal = apply_calibration(readings, offsets, reference_device)
    ok = {r.device_id: bool(r.ok) for r in offsets.itertuples()}
    tier = [instrument_tier(t, is_reference=(d == reference_device), calibration_ok=ok.get(d, False))
            for d, t in zip(cal["device_id"], cal["instrument_type"])]
    cal["tier"] = tier
    return cal[cal["tier"] == "validacao"].reset_index(drop=True), cal[cal["tier"] == "exploratorio"].reset_index(drop=True)


# ---------------------------------------------------------------- locais candidatos para a campanha
def candidate_sites(radiance, transform, region_mask, *, per_stratum: int = 8, radius_km: float = 10.0,
                    radii_km=(1.0, 2.0, 5.0, 10.0, 20.0, 50.0), max_radius_km: float = 50.0, min_valid_fraction: float = 0.9,
                    min_separation_km: float = 10.0, n_try: int = 4000, seed: int = 0) -> pd.DataFrame:
    """Sorteia, na regiao, locais candidatos estratificados pela radiancia de satelite do entorno (media a ``radius_km``),
    nas mesmas classes fixas da interface (``pixelmap.BREAKS``). Apenas planejamento: a escolha final depende de acesso,
    seguranca e permissao, que o satelite nao informa. Estratificar pelo preditor garante o gradiente do escuro ao claro
    sem enviesar a associacao que sera testada.

    Exige: pixel valido (terra), disco de ``max_radius_km`` inteiro dentro do raster, fracao valida do disco de
    ``radius_km`` >= ``min_valid_fraction`` (evita a costa, onde a mascara de agua tira pixels) e separacao minima entre
    candidatos. Determinístico para a mesma ``seed``."""
    from openlux.pixelmap import BREAKS, LABELS
    rad = np.asarray(radiance, dtype="float64")
    ok = np.isfinite(rad) & np.asarray(region_mask, dtype=bool)
    rr, cc = np.nonzero(ok)
    if rr.size == 0:
        return pd.DataFrame()
    rng = np.random.default_rng(seed)
    pick = rng.permutation(rr.size)[:n_try]
    chosen: dict[str, list] = {lab: [] for lab in LABELS}
    for idx in pick:
        r, c = rr[idx], cc[idx]
        lon = transform.c + (c + 0.5) * transform.a
        lat = transform.f + (r + 0.5) * transform.e
        ctx = context_radiance(rad, transform, lon, lat, [radius_km, max_radius_km])
        if not ctx[max_radius_km]["complete"] or not ctx[radius_km]["valid_fraction"] >= min_valid_fraction:
            continue
        mean = ctx[radius_km]["mean"]
        if not np.isfinite(mean):
            continue
        lab = LABELS[int(np.searchsorted(BREAKS, mean, side="right"))]
        if len(chosen[lab]) >= per_stratum:
            continue
        too_close = False
        for other in chosen[lab]:      # separacao minima dentro do estrato (entre estratos a distancia nao importa para o gradiente)
            dy = (lat - other["lat"]) * 110.574
            dx = (lon - other["lon"]) * 111.320 * np.cos(np.radians(lat))
            if np.hypot(dx, dy) < min_separation_km:
                too_close = True
                break
        if too_close:
            continue
        chosen[lab].append(dict(stratum=lab, lat=float(lat), lon=float(lon), **{f"valid_fraction_{radius_km:g}km": float(ctx[radius_km]["valid_fraction"])},
                                **{f"context_{radius_km:g}km": float(mean)}))
        if all(len(v) >= per_stratum for v in chosen.values()):
            break
    rows = []
    for lab in LABELS:
        for site in chosen[lab]:
            full = context_radiance(rad, transform, site["lon"], site["lat"], list(radii_km))
            for rk in radii_km:
                site[f"context_{rk:g}km"] = float(full[rk]["mean"])
            rows.append(site)
    return pd.DataFrame(rows)
