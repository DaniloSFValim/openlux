"""Orquestracao da serie anual: indicadores por municipio, tendencia, sensibilidade, QA.

Determinismo: as tabelas de saida (CSV/JSON de resultados) nao contem datas nem caminhos
absolutos e sao ordenadas; duas execucoes com as mesmas entradas e parametros geram
arquivos identicos byte a byte. Datas e hashes ficam em ``run_record.json``.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from openlux.geo import bbox_window
from openlux.io import read_blackmarble, read_for_qa, sha256_file
from openlux.provenance import code_version, write_json
from openlux.qa import background_controls
from openlux.temporal import annual_table, change, rank_agreement, trend

NW_TO_MW = 1e-6
#: Limiar documentado: o guia do Black Marble (secao 2.3) informa que valores de composto
#: abaixo de 0,5 nW cm^-2 sr^-1 sao zerados para remover ruido de fundo.
LIT_THRESHOLD = {"lit_0p5": 0.5}


@dataclass(frozen=True)
class Config:
    name: str
    layer: str = "AllAngle_Composite_Snow_Free"
    allowed_quality: tuple = (0,)
    n_min: int = 1


MAIN = Config("main")
SENSITIVITY = (
    Config("quality_0_1", allowed_quality=(0, 1)),
    Config("near_nadir", layer="NearNadir_Composite_Snow_Free"),
    Config("n_min_5", n_min=5),
    Config("n_min_10", n_min=10),
)


def _table(files, polygons, id_col, cfg: Config, extra_cols=(), thresholds=None) -> pd.DataFrame:
    def loader(year):
        return read_blackmarble(files[year], cfg.layer, n_min=cfg.n_min,
                                allowed_quality=cfg.allowed_quality)
    df = annual_table(loader, sorted(files), polygons, id_col=id_col, extra_cols=extra_cols,
                      thresholds=thresholds)
    return df.sort_values([id_col, "year"], kind="stable").reset_index(drop=True)


def _window_trends(df, id_col, years_window, min_years, floor_quantile):
    y0, y1 = years_window
    sub = df[(df.year >= y0) & (df.year <= y1)]
    rows = []
    for key, g in sub.groupby(id_col, sort=True):
        rows.append({id_col: key, **trend(g["year"].to_numpy(), g["mean_radiance"].to_numpy(),
                                          min_years=min_years)})
    tr = pd.DataFrame(rows)
    base = sub[sub.year == y0].set_index(id_col)["mean_radiance"]
    fin = sub[sub.year == y1].set_index(id_col)["mean_radiance"].reindex(base.index)
    floor = float(np.nanquantile(base.to_numpy(), floor_quantile))
    ch = change(base.to_numpy(), fin.to_numpy(), floor=floor)
    tr = tr.merge(pd.DataFrame({id_col: base.index, "change_abs": ch["abs"],
                                "change_pct": ch["pct"]}), on=id_col)
    return tr, floor


def run_annual(files: dict, polygons, id_col: str, population: pd.DataFrame | None, outdir, *,
               min_years=8, floor_quantile=0.25, population_year=2022, trend_windows=None,
               extra_cols=(), qa_baseline_years=None, configs=(MAIN, *SENSITIVITY),
               thresholds=None, threshold_quantiles=(0.5, 0.9), code_dir=".") -> dict:
    """Executa a serie. ``files``: {ano: caminho .h5}. Retorna o registro de execucao."""
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    years = sorted(files)
    first, last = years[0], years[-1]
    windows = trend_windows or {"all": (first, last)}
    thr = dict(LIT_THRESHOLD if thresholds is None else thresholds)
    thr.update(_analytic_thresholds(files[first], polygons, threshold_quantiles))
    tables = {c.name: _table(files, polygons, id_col, c, extra_cols, thr) for c in configs}
    main = tables[MAIN.name]

    trend_frames, floors = [], {}
    sens = {}
    for wname, wy in windows.items():
        tr, floors[wname] = _window_trends(main, id_col, wy, min_years, floor_quantile)
        tr.insert(1, "window", wname)
        trend_frames.append(tr)
        t_main = tr.set_index(id_col)["slope"]
        sens[wname] = {}
        for c in configs:
            if c.name == MAIN.name:
                continue
            tc, _ = _window_trends(tables[c.name], id_col, wy, min_years, floor_quantile)
            tcs = tc.set_index(id_col)["slope"].reindex(t_main.index)
            m_main = main[main.year == wy[1]].set_index(id_col)["mean_radiance"]
            m_c = tables[c.name][tables[c.name].year == wy[1]].set_index(id_col)[
                "mean_radiance"].reindex(m_main.index)
            ok = t_main.notna() & tcs.notna()
            sens[wname][c.name] = dict(
                spearman_mean_end_year=rank_agreement(m_main.to_numpy(), m_c.to_numpy()),
                spearman_trend_slope=rank_agreement(t_main.to_numpy(), tcs.to_numpy()),
                trend_sign_agreement=float((np.sign(t_main[ok]) == np.sign(tcs[ok])).mean())
                if ok.any() else None,
                n_municipalities_with_nan_mean_end_year=int(m_c.isna().sum()),
            )
    trends = pd.concat(trend_frames, ignore_index=True)
    names = polygons[[id_col, *extra_cols]].drop_duplicates(id_col)
    if extra_cols:
        trends = trends.merge(names, on=id_col, how="left")
    if population is not None and population_year in years:
        s = main[main.year == population_year][[id_col, "apparent_radiant_intensity_nw_sr"]]
        pc = s.merge(population, left_on=id_col, right_on="cd_mun", how="left")
        pc["intensity_per_capita_mw_sr_hab"] = (pc.apparent_radiant_intensity_nw_sr * NW_TO_MW
                                                / pc.population)
        trends = trends.merge(pc[[id_col, "population", "intensity_per_capita_mw_sr_hab"]],
                              on=id_col, how="left")
    trends = trends.sort_values([id_col, "window"], kind="stable").reset_index(drop=True)

    qa = _qa(files, polygons, qa_baseline_years or tuple(years[:min(5, len(years))]))

    outputs = {}

    def save_csv(name, df):
        p = outdir / name
        df.to_csv(p, index=False, float_format="%.10g", lineterminator="\n")
        outputs[name] = sha256_file(p)

    for name, df in tables.items():
        save_csv(f"annual_{name}.csv", df)
    save_csv("trends_main.csv", trends)
    save_csv("qa_background_controls.csv", qa)
    write_json(outdir / "sensitivity.json", sens)
    outputs["sensitivity.json"] = sha256_file(outdir / "sensitivity.json")

    record = dict(
        processed_utc=dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        code=code_version(code_dir),
        parameters=dict(main=asdict(MAIN), sensitivity=[asdict(c) for c in configs
                                                        if c.name != MAIN.name],
                        min_years=min_years, floor_quantile=floor_quantile,
                        change_floor_nw_cm2_sr=floors,
                        trend_windows={k: list(v) for k, v in windows.items()},
                        population_year=population_year, thresholds_nw_cm2_sr=thr,
                        threshold_reference_year=first, threshold_quantiles=list(threshold_quantiles),
                        qa_baseline_years=list(qa_baseline_years or years[:min(5, len(years))])),
        inputs={str(y): dict(name=Path(files[y]).name, sha256=sha256_file(files[y]))
                for y in years},
        outputs=outputs,
    )
    write_json(outdir / "run_record.json", record)
    return record


def _analytic_thresholds(path, polygons, quantiles) -> dict:
    """Limiares analiticos: quantis da radiancia dos pixels de terra ja iluminados (>= limiar
    documentado) no ano de referencia, na caixa dos poligonos. Parametros do pesquisador."""
    if not quantiles:
        return {}
    _, t = read_blackmarble(path)
    window = bbox_window(t, _shape(path), tuple(polygons.total_bounds))
    rad, lw = read_for_qa(path, window=window)
    sel = np.isin(lw, (0, 1, 5)) & np.isfinite(rad) & (rad >= LIT_THRESHOLD["lit_0p5"])
    vals = rad[sel]
    if vals.size == 0:  # ano de referencia sem pixels iluminados: nao ha distribuicao para quantis
        return {}
    return {f"q{int(round(q * 100))}_ref": float(f"{np.quantile(vals, q):.3g}") for q in quantiles}


def _qa(files, polygons, baseline_years) -> pd.DataFrame:
    """Controles de ruido de fundo na caixa dos poligonos (inclui terra e mar vizinhos)."""
    from openlux.geo import tile_transform  # noqa: F401  (transformacao vem do leitor)
    arrays, lw = {}, None
    window = None
    for y in sorted(files):
        if window is None:
            _, t = read_blackmarble(files[y])
            window = bbox_window(t, _shape(files[y]), tuple(polygons.total_bounds))
        rad, lw = read_for_qa(files[y], window=window)
        arrays[y] = rad
    land = np.isin(lw, (0, 1, 5))
    sea = lw == 3
    return background_controls(arrays, land, sea, baseline_years=baseline_years)


def _shape(path):
    import h5py
    with h5py.File(path, "r") as f:
        return f["HDFEOS/GRIDS/VIIRS_Grid_DNB_2d/Data Fields/Land_Water_Mask"].shape


def compare_sensors(files_a: dict, files_b: dict, polygons, id_col: str, *, min_years=5) -> dict:
    """Compara dois sensores (ex.: S-NPP x NOAA-20) nos anos em comum, config principal.

    Retorna razao b/a da media estadual por ano e concordancia (Spearman e sinal) da
    inclinacao de Theil-Sen por municipio. Nao decide qual sensor esta certo.
    """
    common = sorted(set(files_a) & set(files_b))
    ta = _table({y: files_a[y] for y in common}, polygons, id_col, MAIN, thresholds=LIT_THRESHOLD)
    tb = _table({y: files_b[y] for y in common}, polygons, id_col, MAIN, thresholds=LIT_THRESHOLD)

    def state_mean(t):
        return t.groupby("year").apply(
            lambda g: float((g.mean_radiance * g.weight_sum).sum() / g.weight_sum.sum()),
            include_groups=False)
    ma, mb = state_mean(ta), state_mean(tb)

    def state_lit(t):
        return t.groupby("year").apply(
            lambda g: float((g["frac_above_lit_0p5"] * g.weight_sum).sum() / g.weight_sum.sum()),
            include_groups=False)
    la, lb = state_lit(ta), state_lit(tb)
    sa = _window_trends(ta, id_col, (common[0], common[-1]), min_years, 0.25)[0].set_index(id_col)
    sb = _window_trends(tb, id_col, (common[0], common[-1]), min_years, 0.25)[0].set_index(id_col)
    ok = sa.slope.notna() & sb.slope.notna()
    return dict(
        years=common,
        state_mean_a={int(y): float(v) for y, v in ma.items()},
        state_mean_b={int(y): float(v) for y, v in mb.items()},
        ratio_b_over_a={int(y): float(mb[y] / ma[y]) if ma[y] else None for y in common},
        state_lit_fraction_a={int(y): float(v) for y, v in la.items()},
        state_lit_fraction_b={int(y): float(v) for y, v in lb.items()},
        spearman_trend_slope=rank_agreement(sa.slope.to_numpy(), sb.slope.reindex(sa.index).to_numpy()),
        trend_sign_agreement=float((np.sign(sa.slope[ok]) == np.sign(sb.slope[ok])).mean())
        if ok.any() else None,
    )


def compare_municipal_series(ta: pd.DataFrame, tb: pd.DataFrame, id_col: str, *, window, min_years,
                             change_years=None):
    """Compara, por municipio, duas series anuais de radiancia media (sensores A e B).

    ``ta``/``tb``: tabelas anuais (colunas ``id_col``, ``year``, ``mean_radiance``, ``weight_sum``).
    Retorna ``(df, resumo)``. ``df`` tem, por municipio, inclinacao de Theil-Sen de A e B na ``window``
    (NaN se menos de ``min_years`` anos validos), razao media B/A dos anos da janela e, se
    ``change_years=(y1, y2)``, a variacao absoluta de cada sensor entre esses anos. O resumo traz
    concordancia de postos (Spearman) e de sinal das inclinacoes, razao mediana B/A e o numero de
    municipios comparados. Nao decide qual sensor esta certo.
    """
    y0, y1 = window
    rows = []
    ids = sorted(set(ta[id_col]) | set(tb[id_col]))
    for cd in ids:
        ga = ta[(ta[id_col] == cd) & (ta.year >= y0) & (ta.year <= y1)].sort_values("year")
        gb = tb[(tb[id_col] == cd) & (tb.year >= y0) & (tb.year <= y1)].sort_values("year")
        sa = trend(ga["year"].to_numpy(), ga["mean_radiance"].to_numpy(), min_years=min_years)
        sb = trend(gb["year"].to_numpy(), gb["mean_radiance"].to_numpy(), min_years=min_years)
        m = ga.merge(gb, on="year", suffixes=("_a", "_b"))
        with np.errstate(divide="ignore", invalid="ignore"):
            ratio = (m["mean_radiance_b"] / m["mean_radiance_a"]).replace([np.inf, -np.inf], np.nan)
        row = {id_col: cd, "slope_a": sa["slope"], "p_a": sa["p_value"], "slope_b": sb["slope"],
               "p_b": sb["p_value"], "n_years_a": sa["n_years"], "n_years_b": sb["n_years"],
               "mean_ratio_b_over_a": float(np.nanmean(ratio)) if len(ratio) and np.isfinite(ratio).any()
               else np.nan}
        if change_years:
            c1, c2 = change_years
            for tag, g in (("a", ta), ("b", tb)):
                gg = g[g[id_col] == cd].set_index("year")["mean_radiance"]
                row[f"change_{tag}"] = (float(gg[c2] - gg[c1]) if c1 in gg.index and c2 in gg.index
                                        else np.nan)
        rows.append(row)
    df = pd.DataFrame(rows)
    ok = df.slope_a.notna() & df.slope_b.notna()
    summ = dict(
        n_municipalities=int(ok.sum()),
        spearman_slopes=rank_agreement(df.slope_a[ok].to_numpy(), df.slope_b[ok].to_numpy()),
        sign_agreement=float((np.sign(df.slope_a[ok]) == np.sign(df.slope_b[ok])).mean()) if ok.any() else None,
        median_ratio_b_over_a=float(df.mean_ratio_b_over_a.median()) if len(df) else None,
    )
    if change_years:
        okc = df.change_a.notna() & df.change_b.notna()
        summ["spearman_changes"] = rank_agreement(df.change_a[okc].to_numpy(), df.change_b[okc].to_numpy())
        summ["median_change_a"] = float(df.change_a[okc].median()) if okc.any() else None
        summ["median_change_b"] = float(df.change_b[okc].median()) if okc.any() else None
    return df, summ
