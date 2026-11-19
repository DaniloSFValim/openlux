"""Orquestracao da serie anual: indicadores por municipio, tendencia e sensibilidade.

Determinismo: as tabelas de saida (CSV) nao contem datas nem caminhos absolutos e sao
ordenadas; duas execucoes com as mesmas entradas e parametros geram arquivos identicos
byte a byte. Datas e hashes ficam no registro de execucao (``run_record.json``).
"""
from __future__ import annotations

import datetime as dt
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from openlux.io import read_blackmarble, sha256_file
from openlux.provenance import code_version, write_json
from openlux.temporal import annual_table, change, rank_agreement, trend


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


def _table(files, polygons, id_col, cfg: Config) -> pd.DataFrame:
    def loader(year):
        return read_blackmarble(files[year], cfg.layer, n_min=cfg.n_min,
                                allowed_quality=cfg.allowed_quality)
    df = annual_table(loader, sorted(files), polygons, id_col=id_col)
    return df.sort_values([id_col, "year"], kind="stable").reset_index(drop=True)


def _trends(df, id_col, min_years) -> pd.DataFrame:
    rows = []
    for key, g in df.groupby(id_col, sort=True):
        t = trend(g["year"].to_numpy(), g["mean_radiance"].to_numpy(), min_years=min_years)
        rows.append({id_col: key, **t})
    return pd.DataFrame(rows)


def run_annual(files: dict, polygons, id_col: str, population: pd.DataFrame | None,
               outdir, *, min_years=8, floor_quantile=0.25, population_year=2022,
               configs=(MAIN, *SENSITIVITY), code_dir=".") -> dict:
    """Executa a serie. ``files``: {ano: caminho .h5}. Retorna o registro de execucao."""
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    tables = {c.name: _table(files, polygons, id_col, c) for c in configs}
    main = tables[MAIN.name]
    years = sorted(files)

    trends = _trends(main, id_col, min_years)
    first, last = years[0], years[-1]
    base = main[main.year == first].set_index(id_col)["mean_radiance"]
    fin = main[main.year == last].set_index(id_col)["mean_radiance"].reindex(base.index)
    floor = float(np.nanquantile(base.to_numpy(), floor_quantile))
    ch = change(base.to_numpy(), fin.to_numpy(), floor=floor)
    trends = trends.merge(pd.DataFrame({id_col: base.index, "change_abs": ch["abs"],
                                        "change_pct": ch["pct"]}), on=id_col)

    if population is not None and population_year in years:
        s = main[main.year == population_year][[id_col, "apparent_radiant_intensity_nw_sr"]]
        pc = s.merge(population, left_on=id_col, right_on="cd_mun", how="left")
        pc["intensity_per_capita_nw_sr_hab"] = pc.apparent_radiant_intensity_nw_sr / pc.population
        trends = trends.merge(pc[[id_col, "population", "intensity_per_capita_nw_sr_hab"]],
                              on=id_col, how="left")

    # Sensibilidade: concordancia de postos e de sinal da tendencia em relacao a 'main'.
    sens = {}
    t_main = trends.set_index(id_col)["slope"]
    for c in configs:
        if c.name == MAIN.name:
            continue
        tab = tables[c.name]
        tc = _trends(tab, id_col, min_years).set_index(id_col)["slope"].reindex(t_main.index)
        m_last_main = main[main.year == last].set_index(id_col)["mean_radiance"]
        m_last = tab[tab.year == last].set_index(id_col)["mean_radiance"].reindex(m_last_main.index)
        ok = t_main.notna() & tc.notna()
        sens[c.name] = dict(
            spearman_mean_last_year=rank_agreement(m_last_main.to_numpy(), m_last.to_numpy()),
            spearman_trend_slope=rank_agreement(t_main.to_numpy(), tc.to_numpy()),
            trend_sign_agreement=float((np.sign(t_main[ok]) == np.sign(tc[ok])).mean())
            if ok.any() else None,
            n_municipalities_with_nan_mean_last_year=int(m_last.isna().sum()),
        )

    outputs = {}
    for name, df in tables.items():
        p = outdir / f"annual_{name}.csv"
        df.to_csv(p, index=False, float_format="%.10g", lineterminator="\n")
        outputs[p.name] = sha256_file(p)
    p = outdir / "trends_main.csv"
    trends.to_csv(p, index=False, float_format="%.10g", lineterminator="\n")
    outputs[p.name] = sha256_file(p)
    p = outdir / "sensitivity.json"
    write_json(p, sens)
    outputs[p.name] = sha256_file(p)

    record = dict(
        processed_utc=dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        code=code_version(code_dir),
        parameters=dict(main=asdict(MAIN), sensitivity=[asdict(c) for c in configs
                                                        if c.name != MAIN.name],
                        min_years=min_years, floor_quantile=floor_quantile,
                        change_floor_nw_cm2_sr=floor, change_years=[first, last],
                        population_year=population_year),
        inputs={str(y): dict(name=Path(files[y]).name, sha256=sha256_file(files[y]))
                for y in years},
        outputs=outputs,
    )
    write_json(outdir / "run_record.json", record)
    return record
