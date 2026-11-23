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
    header = (root / "docs/field/measurements_template.csv").read_text(encoding="utf-8").strip().split(",")
    for col in ("site_id", "visit_id", "lat", "lon", "sqm_mpsas", "sun_alt_deg", "moon_alt_deg", "cloud_free", "temp_c"):
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
