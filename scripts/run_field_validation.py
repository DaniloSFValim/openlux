#!/usr/bin/env python3
"""Analise da validacao em campo (SQM) conforme docs/field/preregistration.json.

Uso: python scripts/run_field_validation.py --measurements campo.csv --year 2025 [--exploratory]
O CSV tem uma linha por LEITURA (modelo: docs/field/measurements_template.csv; confira antes com scripts/check_measurements.py). Sem a pre-especificacao
congelada (status = "frozen"), so roda com --exploratory e o resultado fica marcado como exploratorio.
Sem medicoes reais nao ha o que analisar; este script nao gera dados.
"""
import argparse
import glob
import json
import re
import sys
from pathlib import Path

import pandas as pd

from openlux.field import (CalibrationParams, QCParams, colocated_offsets, context_radiance, leave_one_out, permutation_max_spearman,
                           qc_visits, site_summary, split_validation_readings, validate_measurements)
from openlux.geo import tile_transform
from openlux.io import read_blackmarble, sha256_file
from openlux.log import JsonLogger
from openlux.provenance import code_version, write_json

RAW, OUT = Path("data/raw"), Path("outputs/field")
PREREG = Path("docs/field/preregistration.json")
PRODUCTS = {"primary": "VJ146A4", "secondary": "VNP46A4"}


def pick_file(product, year):
    files = {int(re.search(r"\.A(\d{4})001\.", p).group(1)): Path(p) for p in glob.glob(str(RAW / product / "*.h5"))}
    if not files:
        sys.exit(f"Sem arquivos {product} em data/raw/.")
    used = year if year in files else max(y for y in files if y <= year) if any(y <= year for y in files) else min(files)
    return used, files[used]


def evaluate(sites, sensor_key, pre, log):
    prod = PRODUCTS[sensor_key]
    used, path = pick_file(prod, pre["_year"])
    rad, t = read_blackmarble(path)
    radii = pre["radii_km"]
    ctx = [context_radiance(rad, t, r.lon, r.lat, radii) for r in sites.itertuples()]
    clipped = [sid for sid, c in zip(sites["site_id"], ctx) if not all(c[r]["complete"] for r in radii)]
    if clipped:      # disco do maior raio ultrapassa a borda do tile: o contexto seria parcial
        return dict(sensor=prod, verdict="insufficient_data", context_complete=False,
                    reason=f"locais com contexto incompleto (borda do tile a menos de {max(radii)} km): {clipped}"), {}
    x = {r: [c[r]["mean"] for c in ctx] for r in radii}
    vf = {r: min(c[r]["valid_fraction"] for c in ctx) for r in radii}
    y = sites["luminance_cd_m2"].to_numpy()
    ok = all(pd.notna(v) for r in radii for v in x[r])
    res = dict(sensor=prod, year_requested=pre["_year"], year_used=used, input_sha256=sha256_file(path),
               min_valid_fraction_by_radius=vf, context_complete=bool(ok))
    if not ok:
        res["verdict"] = "insufficient_data"
        res["reason"] = "ha local sem pixel valido em algum raio"
        return res, x
    perm = permutation_max_spearman(y, x, n_perm=pre["permutation"]["n_perm"], seed=pre["permutation"]["seed"])
    loo = leave_one_out(y, x[perm["best_radius"]])
    c = pre["criteria"]
    res.update(perm, leave_one_out_min=min(loo), leave_one_out_rho=loo)
    res["criteria_met"] = dict(rho=perm["observed_max"] >= c["min_observed_max_rho"], p=perm["p_value"] <= c["max_permutation_p"],
                               loo=min(loo) >= c["min_leave_one_out_rho"])
    res["verdict"] = "consistent" if all(res["criteria_met"].values()) else "inconsistent"
    log.log("sensor_done", sensor=prod, verdict=res["verdict"], best_radius=perm["best_radius"], rho=perm["observed_max"])
    return res, x


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--measurements", required=True)
    ap.add_argument("--year", type=int, required=True, help="ano do produto anual a usar (o mais recente disponivel se faltar)")
    ap.add_argument("--exploratory", action="store_true")
    ap.add_argument("--reference-device", default=None, help="device_id do aparelho de referencia (padrao: instruments.reference_device_id da pre-especificacao)")
    a = ap.parse_args()
    pre = json.loads(PREREG.read_text(encoding="utf-8"))
    frozen = pre["status"] == "frozen"
    if not frozen and not a.exploratory:
        sys.exit("Pre-especificacao nao congelada (status != 'frozen'). Aprove e congele antes da coleta, ou use --exploratory.")
    pre["_year"] = a.year
    log = JsonLogger(OUT / "run_field.jsonl")
    df = pd.read_csv(a.measurements, dtype=str, keep_default_na=False)
    m = re.fullmatch(r"h(\d{2})v(\d{2})", pre.get("tile", "h13v11"))
    t = tile_transform(int(m.group(1)), int(m.group(2)))
    issues = validate_measurements(df, tile_bounds=(t.c, t.f - 10.0, t.c + 10.0, t.f), max_radius_km=max(pre["radii_km"]))
    if (issues["severity"] == "erro").any():
        print(issues[issues["severity"] == "erro"].to_string(index=False))
        sys.exit("O arquivo de medicoes tem erros (rode scripts/check_measurements.py). Corrija antes de analisar.")
    for c in ("lat", "lon", "sqm_mpsas", "sun_alt_deg", "moon_alt_deg", "temp_c"):
        df[c] = pd.to_numeric(df[c])
    df["cloud_free"] = df["cloud_free"].map(lambda x: str(x).strip().lower() in ("true", "1", "sim", "yes", "verdadeiro"))
    qc = QCParams(**pre["qc"])
    devices = sorted(df["device_id"].unique())
    ref = a.reference_device or pre["instruments"].get("reference_device_id") or (devices[0] if len(devices) == 1 else "")
    if not ref:
        sys.exit("Ha mais de um aparelho: informe o de referencia (--reference-device ou instruments.reference_device_id na pre-especificacao).")
    if ref not in devices:
        sys.exit(f"Aparelho de referencia {ref!r} nao aparece no arquivo (aparelhos: {devices}).")
    offsets = colocated_offsets(df, ref, CalibrationParams(**pre["cross_calibration"]), qc)
    val, expl = split_validation_readings(df, offsets, ref)
    log.log("instrumentos", reference=ref, devices=devices, validation_readings=len(val), exploratory_readings=len(expl))
    visits = qc_visits(val, qc) if len(val) else pd.DataFrame(columns=["site_id", "visit_id", "pass"])
    summ = site_summary(val, qc) if len(val) else pd.DataFrame(columns=["site_id", "n_valid_visits", "luminance_cd_m2"])
    pos = val.groupby("site_id")[["lat", "lon"]].mean().reset_index() if len(val) else pd.DataFrame(columns=["site_id", "lat", "lon"])
    sites = summ.merge(pos, on="site_id")
    enough = sites[sites["n_valid_visits"] >= pre["min_valid_visits_per_site"]].reset_index(drop=True)
    log.log("sites", total=len(summ), usable=len(enough), visits=len(visits), visits_passed=int(visits["pass"].sum()))
    report = dict(mode="confirmatorio" if frozen else "EXPLORATORIO (pre-especificacao nao congelada)",
                  preregistration_sha256=sha256_file(PREREG), measurements_sha256=sha256_file(a.measurements),
                  n_sites_total=len(summ), n_sites_usable=len(enough), code=code_version(), reference_device=ref,
                  calibration=offsets.to_dict("records"), readings_validation=len(val), readings_exploratory=len(expl),
                  exploratory_devices=sorted(set(expl["device_id"])) if len(expl) else [])
    if len(enough) < pre["min_sites"]:
        report["verdict"] = "insufficient_data"
        report["reason"] = f"{len(enough)} locais utilizaveis < min_sites = {pre['min_sites']}"
    else:
        res = {}
        for key in ("primary", "secondary"):
            res[key], x = evaluate(enough, key, pre, log)
        report["sensors"] = res
        report["verdict"] = res["primary"]["verdict"]
    OUT.mkdir(parents=True, exist_ok=True)
    visits.to_csv(OUT / "visits_qc.csv", index=False)
    enough.to_csv(OUT / "sites.csv", index=False)
    write_json(OUT / "report.json", report)
    print(report["mode"], "->", report["verdict"])
    if "reason" in report:
        print(report["reason"])


if __name__ == "__main__":
    main()
