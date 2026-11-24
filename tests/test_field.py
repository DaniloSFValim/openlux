"""Validacao em campo com SQM: conversoes, controle de qualidade, contexto de radiancia e estatistica.
Todos os dados aqui sao SINTETICOS (so para testar o codigo; nao representam medicoes)."""
import numpy as np
import pandas as pd
import pytest
from rasterio.transform import from_origin

from openlux.field import (QCParams, context_radiance, leave_one_out, luminance_to_mpsas, mpsas_to_luminance,
                           permutation_max_spearman, qc_visits, site_summary, spearman_by_radius)


def test_conversion_matches_unihedron_formula_and_round_trips():
    assert mpsas_to_luminance(0.0) == pytest.approx(108000.0)                 # 10,8e4 x 10^0
    assert mpsas_to_luminance(22.0) == pytest.approx(108000.0 * 10 ** (-8.8))  # ~1,71e-4 cd/m2
    m = np.array([17.5, 19.0, 21.3, 22.0])
    assert luminance_to_mpsas(mpsas_to_luminance(m)) == pytest.approx(m)
    assert mpsas_to_luminance(20.0) / mpsas_to_luminance(21.0) == pytest.approx(10 ** 0.4)   # 1 mag = fator 2,512


def _visits(**over):
    base = dict(site_id="A", visit_id="A1", sqm_mpsas=[21.0, 21.02, 21.01, 20.99, 21.0],
                sun_alt_deg=-30.0, moon_alt_deg=-20.0, cloud_free=True, temp_c=22.0)
    base.update(over)
    n = len(base["sqm_mpsas"])
    rows = [{k: (v[i] if k == "sqm_mpsas" else v) for k, v in base.items()} for i in range(n)]
    return pd.DataFrame(rows)


def test_qc_flags_each_rule_with_a_reason():
    p = QCParams()
    ok = qc_visits(_visits(), p)
    assert bool(ok.loc[0, "pass"]) and ok.loc[0, "reasons"] == ""
    assert "sol" in qc_visits(_visits(sun_alt_deg=-10.0), p).loc[0, "reasons"]
    assert "lua" in qc_visits(_visits(moon_alt_deg=5.0), p).loc[0, "reasons"]
    assert "nuvens" in qc_visits(_visits(cloud_free=False), p).loc[0, "reasons"]
    assert "dispersao" in qc_visits(_visits(sqm_mpsas=[21.0, 21.4, 21.0, 20.6, 21.0]), p).loc[0, "reasons"]
    assert "leituras" in qc_visits(_visits(sqm_mpsas=[21.0, 21.0]), p).loc[0, "reasons"]
    assert not bool(qc_visits(_visits(sun_alt_deg=-10.0), p).loc[0, "pass"])


def test_site_summary_uses_median_per_visit_then_across_valid_visits_only():
    five = lambda m: [m] * 5
    a = _visits(visit_id="A1", sqm_mpsas=five(21.0))
    b = _visits(visit_id="A2", sqm_mpsas=five(20.0))
    bad = _visits(visit_id="A3", sqm_mpsas=five(10.0), cloud_free=False)
    other = _visits(site_id="B", visit_id="B1", sqm_mpsas=five(19.0))
    s = site_summary(pd.concat([a, b, bad, other]), QCParams()).set_index("site_id")
    mean_lum = mpsas_to_luminance(np.array([21.0, 20.0])).mean()
    assert s.loc["A", "n_valid_visits"] == 2 and s.loc["A", "luminance_cd_m2"] == pytest.approx(mean_lum)
    assert s.loc["A", "sqm_mpsas"] == pytest.approx(luminance_to_mpsas(mean_lum))   # NAO e a media das magnitudes (20,5)
    assert abs(s.loc["A", "sqm_mpsas"] - 20.5) > 0.05
    assert s.loc["B", "n_valid_visits"] == 1


def test_context_radiance_counts_only_pixels_within_radius_and_reports_valid_fraction():
    t = from_origin(-43.0, -22.0, 0.01, 0.01)               # pixels de 0,01 grau (~1,1 km)
    rad = np.zeros((60, 60)); rad[30, 30] = 100.0            # um pixel brilhante
    lon, lat = -43.0 + 30.5 * 0.01, -22.0 - 30.5 * 0.01      # centro desse pixel
    r = context_radiance(rad, t, lon, lat, [0.5, 3.0])
    assert r[0.5]["mean"] == pytest.approx(100.0) and r[0.5]["n_pixels"] == 1
    assert 0 < r[3.0]["mean"] < 100.0 and r[3.0]["n_pixels"] > 1
    rad2 = rad.copy(); rad2[:, :30] = np.nan
    r2 = context_radiance(rad2, t, lon, lat, [3.0])
    assert 0.0 < r2[3.0]["valid_fraction"] < 1.0
    far = context_radiance(rad, t, lon + 1.0, lat, [3.0])    # longe da janela do raster com dados
    assert np.isnan(far[3.0]["mean"]) or far[3.0]["mean"] == 0.0


def test_spearman_and_permutation_on_synthetic_gradient():
    rng = np.random.default_rng(0)
    n = 20
    x = {1.0: rng.lognormal(size=n)}
    x[5.0] = x[1.0] * rng.lognormal(sigma=0.3, size=n)
    y = x[5.0] ** 0.8 * rng.lognormal(sigma=0.2, size=n)           # relacao monotonica com ruido
    rho = spearman_by_radius(y, x)
    assert rho[5.0] > 0.8 and set(rho) == {1.0, 5.0}
    res = permutation_max_spearman(y, x, n_perm=2000, seed=1)
    assert res["p_value"] < 0.01 and res["best_radius"] == max(rho, key=rho.get) and res["observed_max"] == pytest.approx(max(rho.values()))
    noise = permutation_max_spearman(rng.normal(size=n), x, n_perm=2000, seed=1)
    assert noise["p_value"] > 0.05


def test_permutation_is_deterministic_and_leave_one_out_reports_each_site():
    rng = np.random.default_rng(3)
    x = {2.0: rng.lognormal(size=12)}
    y = x[2.0] * rng.lognormal(sigma=0.1, size=12)
    a = permutation_max_spearman(y, x, n_perm=500, seed=7)
    b = permutation_max_spearman(y, x, n_perm=500, seed=7)
    assert a == b
    loo = leave_one_out(y, x[2.0])
    assert len(loo) == 12 and min(loo) > 0.8
    y2 = y.copy(); y2[0] = y.max() * 10                                # um local muda a correlacao
    assert min(leave_one_out(y2, x[2.0])) < spearman_by_radius(y2, x)[2.0] + 1e-9


def test_preregistration_and_template_are_consistent_with_the_code():
    import json
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    pre = json.loads((root / "docs/field/preregistration.json").read_text(encoding="utf-8"))
    assert QCParams(**pre["qc"]) == QCParams()               # defaults do codigo = pre-especificacao
    assert pre["status"] in ("draft", "frozen") and pre["radii_km"] == sorted(pre["radii_km"]) and min(pre["radii_km"]) >= 1
    assert 0 < pre["criteria"]["max_permutation_p"] <= 0.05 and pre["min_sites"] >= 20
    from openlux.field import INSTRUMENT_TYPES, CalibrationParams
    assert CalibrationParams(**pre["cross_calibration"]) == CalibrationParams()      # calibracao cruzada: codigo = pre-especificacao
    assert tuple(pre["instruments"]["allowed_types"]) == INSTRUMENT_TYPES and pre["instruments"]["reference_type"] == "sqm"
    assert pre["tile"] == "h13v11"
    header = (root / "docs/field/measurements_template.csv").read_text(encoding="utf-8").strip().split(",")
    from openlux.field import REQUIRED_COLUMNS
    for col in REQUIRED_COLUMNS:                                  # o modelo traz exatamente as colunas que o validador exige
        assert col in header
    assert (root / "docs/field/measurements_template.csv").read_text(encoding="utf-8").count("\n") == 1   # so o cabecalho: sem dados inventados


def test_runner_refuses_a_verdict_without_a_frozen_preregistration(tmp_path):
    import subprocess
    import sys
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    pre = __import__("json").loads((root / "docs/field/preregistration.json").read_text(encoding="utf-8"))
    if pre["status"] == "frozen":
        import pytest
        pytest.skip("pre-especificacao ja congelada")
    csv = tmp_path / "m.csv"
    csv.write_text("site_id,visit_id,datetime_local,lat,lon,sqm_mpsas,sun_alt_deg,moon_alt_deg,cloud_free,temp_c\n")
    r = subprocess.run([sys.executable, str(root / "scripts/run_field_validation.py"), "--measurements", str(csv), "--year", "2025"],
                       capture_output=True, text=True, cwd=root)
    assert r.returncode != 0 and "nao congelada" in (r.stdout + r.stderr)


def test_context_radiance_flags_discs_clipped_by_the_raster_edge():
    t = from_origin(-43.0, -22.0, 0.01, 0.01)               # 60 x 60 pixels de 0,01 grau (~0,6 grau de lado)
    rad = np.ones((60, 60))
    lon, lat = -43.0 + 0.3, -22.0 - 0.3                      # centro do raster
    r = context_radiance(rad, t, lon, lat, [5.0, 50.0])
    assert r[5.0]["complete"] is True and r[50.0]["complete"] is False      # 50 km (~0,45 grau) ultrapassa a borda
    near = context_radiance(rad, t, -43.0 + 0.01, -22.3, [5.0])             # a ~1 km da borda oeste
    assert near[5.0]["complete"] is False
    outside = context_radiance(rad, t, -41.0, -22.3, [5.0])                 # fora do raster
    assert outside[5.0]["complete"] is False


# ---------------------------------------------------------------- validador do CSV de medicoes
def _rows(site="S1", visit="S1-n1", device="SQM-A", itype="sqm", n=6, **over):
    base = dict(site_id=site, visit_id=visit, datetime_local="2026-12-05T22:10:00", lat=-22.45, lon=-44.60, sqm_mpsas=21.5,
                sun_alt_deg=-30.0, moon_alt_deg=-20.0, cloud_free="true", temp_c=18.0, device_id=device,
                instrument_type=itype, observer="obs1", ephemeris_source="almanaque", notes="")
    base.update(over)
    t0 = pd.Timestamp(base["datetime_local"])
    rows = []
    for i in range(n):          # leituras reais variam em valor e em hora; linhas identicas seriam duplicadas
        r = dict(base)
        r["sqm_mpsas"] = round(base["sqm_mpsas"] + 0.01 * i, 2)
        r["datetime_local"] = (t0 + pd.Timedelta(minutes=i)).isoformat()
        rows.append(r)
    return pd.DataFrame(rows)


TILE = (-50.0, -30.0, -40.0, -20.0)        # h13v11


def _issues(df, **kw):
    from openlux.field import validate_measurements
    return validate_measurements(df, tile_bounds=TILE, now=pd.Timestamp("2026-12-31"), **kw)


def test_validator_accepts_a_clean_file_and_reports_nothing():
    df = pd.concat([_rows("S1", "S1-n1"), _rows("S2", "S2-n1", lat=-23.2, lon=-45.3, sqm_mpsas=19.0)], ignore_index=True)
    assert len(_issues(df)) == 0


def test_validator_reports_missing_columns_and_stops():
    iss = _issues(_rows().drop(columns=["lat", "instrument_type"]))
    assert set(iss["column"]) == {"lat", "instrument_type"} and (iss["severity"] == "erro").all()


def test_validator_flags_values_out_of_range_with_row_numbers():
    df = _rows(n=7)
    df.loc[1, "sqm_mpsas"] = 5.0            # nao fisico: erro
    df.loc[2, "sqm_mpsas"] = 15.0           # improvavel mas possivel: aviso
    df.loc[3, "lat"] = 123.0
    df.loc[4, "cloud_free"] = "talvez"
    df.loc[5, "instrument_type"] = "telescopio"
    df.loc[6, "datetime_local"] = "ontem a noite"
    iss = _issues(df)
    got = {(int(r.row), r.column, r.severity) for r in iss.itertuples()}
    assert (3, "sqm_mpsas", "erro") in got and (4, "sqm_mpsas", "aviso") in got            # linha do CSV = indice + 2
    assert (5, "lat", "erro") in got and (6, "cloud_free", "erro") in got
    assert (7, "instrument_type", "erro") in got and (8, "datetime_local", "erro") in got


def test_validator_flags_site_coordinate_drift_and_visit_inconsistency_and_duplicates():
    a = _rows("S1", "S1-n1")
    b = _rows("S1", "S1-n2", lat=-22.50)                                      # mesmo local, ~5,5 km de diferenca
    c = _rows("S3", "S3-n1")
    c.loc[0, "device_id"] = "SQM-B"                                           # uma visita com dois aparelhos
    iss = _issues(pd.concat([a, b, c], ignore_index=True))
    msgs = " | ".join(iss["message"])
    assert "coordenadas" in msgs and "mais de um aparelho" in msgs
    dup = _issues(pd.concat([_rows(n=6), _rows(n=6)], ignore_index=True))
    assert "duplicad" in " ".join(dup["message"])                              # linhas identicas repetidas: aviso


def test_validator_flags_sites_outside_or_too_close_to_the_tile_edge():
    inside = _rows("S1", "S1-n1", lat=-25.0, lon=-45.0)
    edge = _rows("S2", "S2-n1", lat=-25.0, lon=-49.8)                          # ~20 km da borda oeste: contexto de 50 km incompleto
    outside = _rows("S3", "S3-n1", lat=-25.0, lon=-52.0)
    iss = _issues(pd.concat([inside, edge, outside], ignore_index=True))
    errs = iss[iss["severity"] == "erro"]
    assert set(errs["column"]) == {"lon"} and len(errs) >= 2
    assert "borda" in " ".join(errs["message"]) and "fora" in " ".join(errs["message"])
    assert (iss["row"].astype(int) >= 8).all()                                  # nenhum erro aponta para o local do meio do tile


def test_validator_warns_about_too_few_readings_and_future_dates():
    df = _rows(n=3)
    df["datetime_local"] = "2027-03-01T22:00:00"
    iss = _issues(df)
    msgs = " | ".join(iss["message"])
    assert "leituras" in msgs and "futuro" in msgs and (iss["severity"] == "aviso").all()


def test_check_measurements_cli_exit_codes_and_messages(tmp_path):
    import subprocess
    import sys
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    good = pd.concat([_rows("S1", "S1-n1"), _rows("S2", "S2-n1", lat=-23.2, lon=-45.3, sqm_mpsas=19.0)], ignore_index=True)
    bad = good.copy(); bad.loc[0, "sqm_mpsas"] = 3.0
    run = lambda df: subprocess.run([sys.executable, str(root / "scripts/check_measurements.py"), str(_save(df, tmp_path))],
                                    capture_output=True, text=True, cwd=root)
    ok, ko = run(good), run(bad)
    assert ok.returncode == 0 and "0 erro(s)" in ok.stdout
    assert ko.returncode == 1 and "linha 2" in ko.stdout and "nao e fisico" in ko.stdout


def _save(df, tmp_path):
    p = tmp_path / f"m{len(list(tmp_path.glob('*.csv')))}.csv"
    df.to_csv(p, index=False)
    return p


# ---------------------------------------------------------------- calibracao cruzada e niveis de instrumento
def _pair_night(site, ref_mag, dev_mag, dev="SQM-B", dev_type="sqm", when="2026-12-05T23:50:00", n=6):
    """Duas visitas lado a lado no mesmo local e na mesma noite: referencia (SQM-A) e outro aparelho."""
    a = _rows(site, f"{site}-A", device="SQM-A", itype="sqm", sqm_mpsas=ref_mag, datetime_local=when, n=n)
    b = _rows(site, f"{site}-B", device=dev, itype=dev_type, sqm_mpsas=dev_mag, datetime_local=when, n=n)
    return pd.concat([a, b], ignore_index=True)


def test_night_key_assigns_after_midnight_readings_to_the_previous_evening():
    from openlux.field import night_key
    assert night_key("2026-12-05T23:50:00") == night_key("2026-12-06T00:10:00") == "2026-12-05"
    assert night_key("2026-12-06T22:00:00") == "2026-12-06"


def test_cross_calibration_estimates_a_constant_offset_and_corrects_the_device():
    from openlux.field import CalibrationParams, apply_calibration, colocated_offsets
    df = pd.concat([_pair_night("S1", 21.0, 21.12), _pair_night("S2", 18.5, 18.62), _pair_night("S3", 20.0, 20.12)], ignore_index=True)
    off = colocated_offsets(df, "SQM-A", CalibrationParams()).set_index("device_id")
    assert off.loc["SQM-B", "offset_mag"] == pytest.approx(0.12, abs=1e-6) and bool(off.loc["SQM-B", "ok"])
    assert off.loc["SQM-B", "n_sites"] == 3 and off.loc["SQM-B", "reasons"] == ""
    fixed = apply_calibration(df, off.reset_index(), "SQM-A")
    b = fixed[fixed["device_id"] == "SQM-B"]
    assert (b["sqm_mpsas"] - b["sqm_mpsas_raw"]).round(6).eq(-0.12).all()          # corrigido = bruto - desvio
    assert fixed.loc[fixed["device_id"] == "SQM-A", "sqm_mpsas"].equals(fixed.loc[fixed["device_id"] == "SQM-A", "sqm_mpsas_raw"])
    assert (df["device_id"] == "SQM-B").sum() == len(b) and "sqm_mpsas_raw" not in df.columns   # a entrada nao e alterada


@pytest.mark.parametrize("data, fragment", [
    ([("S1", 21.0, 21.1)], "locais lado a lado"),                                                       # so um local
    ([("S1", 21.0, 21.5), ("S2", 18.5, 19.0)], "desvio"),                                               # desvio grande (0,5 mag)
    ([("S1", 21.0, 21.0), ("S2", 18.5, 18.9)], "varia"),                                                # desvio muda com o brilho
])
def test_cross_calibration_fails_with_a_reason(data, fragment):
    from openlux.field import CalibrationParams, colocated_offsets
    df = pd.concat([_pair_night(s, r, d) for s, r, d in data], ignore_index=True)
    off = colocated_offsets(df, "SQM-A", CalibrationParams())
    assert not bool(off.loc[0, "ok"]) and fragment in off.loc[0, "reasons"]


def test_device_without_any_side_by_side_visit_is_reported_as_not_calibrated():
    from openlux.field import CalibrationParams, colocated_offsets
    df = pd.concat([_rows("S1", "S1-A", device="SQM-A"), _rows("S9", "S9-C", device="CAM-1", itype="camera_calibrated")], ignore_index=True)
    off = colocated_offsets(df, "SQM-A", CalibrationParams()).set_index("device_id")
    assert not bool(off.loc["CAM-1", "ok"]) and "nenhuma visita lado a lado" in off.loc["CAM-1", "reasons"]


def test_tiers_phones_and_uncalibrated_cameras_never_reach_validation():
    from openlux.field import instrument_tier
    assert instrument_tier("sqm", is_reference=True, calibration_ok=False) == "validacao"
    assert instrument_tier("sqm", is_reference=False, calibration_ok=True) == "validacao"
    assert instrument_tier("sqm", is_reference=False, calibration_ok=False) == "exploratorio"
    assert instrument_tier("camera_calibrated", is_reference=False, calibration_ok=True) == "validacao"
    assert instrument_tier("camera_calibrated", is_reference=False, calibration_ok=False) == "exploratorio"
    for t in ("phone", "camera_uncalibrated"):
        assert instrument_tier(t, is_reference=False, calibration_ok=True) == "exploratorio"


def test_validation_readings_keeps_only_the_reference_and_calibrated_devices():
    from openlux.field import CalibrationParams, colocated_offsets, split_validation_readings
    ok = pd.concat([_pair_night("S1", 21.0, 21.1), _pair_night("S2", 18.5, 18.6)], ignore_index=True)
    ph = _rows("S5", "S5-P", device="PHONE-1", itype="phone")
    df = pd.concat([ok, ph], ignore_index=True)
    off = colocated_offsets(df, "SQM-A", CalibrationParams())
    val, expl = split_validation_readings(df, off, "SQM-A")
    assert set(val["device_id"]) == {"SQM-A", "SQM-B"} and set(expl["device_id"]) == {"PHONE-1"}
    assert len(val) + len(expl) == len(df)


# ---------------------------------------------------------------- gerador de locais candidatos
def _gradient_raster(n=400):
    """Raster sintetico 4 x 4 graus (pixels de 0,01): radiancia cresce 'logaritmicamente' da esquerda (0,1) para a direita (~200)."""
    t = from_origin(-46.0, -21.0, 0.01, 0.01)
    col = 10 ** np.linspace(-1.0, 2.3, n)
    return np.tile(col, (n, 1)), t


def test_candidate_sites_are_stratified_complete_separated_and_reproducible():
    from openlux.field import candidate_sites
    from openlux.pixelmap import LABELS
    rad, t = _gradient_raster()
    mask = np.ones(rad.shape, bool)
    kw = dict(per_stratum=2, radius_km=10.0, radii_km=(5.0, 10.0, 20.0), max_radius_km=20.0, min_valid_fraction=0.9,
              min_separation_km=15.0, n_try=1500, seed=3)
    a = candidate_sites(rad, t, mask, **kw)
    b = candidate_sites(rad, t, mask, **kw)
    assert a.equals(b)                                                          # mesma semente, mesmo resultado
    assert set(a["stratum"]) <= set(LABELS) and a.groupby("stratum").size().max() <= 2 and len(set(a["stratum"])) >= 4
    for r in a.itertuples():                                                    # o estrato bate com o contexto calculado de forma independente
        ctx = context_radiance(rad, t, r.lon, r.lat, [10.0, 20.0])
        assert ctx[20.0]["complete"] and ctx[10.0]["valid_fraction"] >= 0.9
        assert r.context_10km == pytest.approx(ctx[10.0]["mean"])
        assert r.stratum == LABELS[int(np.searchsorted([0.5, 2.0, 8.0, 30.0, 100.0], ctx[10.0]["mean"], side="right"))]
    pts = a[["lat", "lon"]].to_numpy()
    for i in range(len(pts)):                                                   # separacao minima entre candidatos
        for j in range(i + 1, len(pts)):
            dy, dx = (pts[i, 0] - pts[j, 0]) * 110.574, (pts[i, 1] - pts[j, 1]) * 111.32 * np.cos(np.radians(pts[i, 0]))
            assert np.hypot(dx, dy) >= 15.0 - 1e-6


def test_candidate_sites_respect_the_region_mask_and_skip_incomplete_or_invalid_context():
    from openlux.field import candidate_sites
    rad, t = _gradient_raster()
    mask = np.zeros(rad.shape, bool)
    mask[:, 200:] = True                                                        # so a metade direita (mais clara) pode ser sorteada
    rad2 = rad.copy(); rad2[:100, :] = np.nan                                   # faixa norte sem dado valido (mar/agua)
    a = candidate_sites(rad2, t, mask, per_stratum=3, radius_km=10.0, radii_km=(10.0, 20.0), max_radius_km=20.0,
                        min_valid_fraction=0.9, min_separation_km=10.0, n_try=1500, seed=1)
    assert len(a) > 0 and (a["lon"] >= -46.0 + 200 * 0.01).all()                # dentro da regiao
    assert (a["lat"] <= -21.0 - 100 * 0.01).all()                               # nenhum candidato dentro da faixa sem dado valido
    assert (a["valid_fraction_10km"] >= 0.9).all()
    edge = 20.0 / (111.32 * np.cos(np.radians(21.5)))
    assert (a["lon"] <= -46.0 + 400 * 0.01 - edge + 1e-9).all() and (a["lat"] >= -25.0 + 20.0 / 110.574 - 1e-9).all()   # disco de 20 km inteiro no raster
