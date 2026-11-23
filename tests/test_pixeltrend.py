"""Tendencia por pixel (Mann-Kendall + Sen + FDR de Benjamini-Hochberg): dados sinteticos."""
import numpy as np
import pandas as pd
from scipy.stats import norm

from openlux.pixeltrend import bh_reject, pixel_trend, significant_change, trend_shares

YEARS = np.arange(2012, 2022)


def _stack(cols):
    """cols: lista de series (len T); devolve (T, 1, ncols)."""
    return np.array(cols, dtype="float64").T[:, None, :]


def test_monotone_series_exact_slope_and_pvalue():
    r = pixel_trend(_stack([2.0 * (YEARS - 2012) + 1.0]), YEARS, min_n=8)
    assert r["n"][0, 0] == 10 and r["slope"][0, 0] == 2.0
    z = 44 / np.sqrt(10 * 9 * 25 / 18)                     # S=45, continuidade -1
    assert np.isclose(r["p"][0, 0], 2 * norm.sf(z), rtol=1e-6)


def test_tie_correction_hand_computed():
    y = np.arange(8)
    x = np.array([1, 1, 2, 3, 4, 5, 6, 7.0])               # um par empatado
    r = pixel_trend(_stack([x]), y, min_n=8)
    var = (8 * 7 * 21 - 2 * 1 * 9) / 18                    # n(n-1)(2n+5) - t(t-1)(2t+5)
    assert np.isclose(r["p"][0, 0], 2 * norm.sf(26 / np.sqrt(var)), rtol=1e-6)


def test_constant_and_insufficient_data():
    short = np.full(10, np.nan); short[:5] = [1, 2, 3, 4, 5]
    r = pixel_trend(_stack([np.zeros(10), short]), YEARS, min_n=8)
    assert r["p"][0, 0] == 1.0 and r["slope"][0, 0] == 0.0 and r["n"][0, 0] == 10
    assert np.isnan(r["p"][0, 1]) and np.isnan(r["slope"][0, 1]) and r["n"][0, 1] == 5


def test_missing_years_use_actual_time_spacing():
    x = np.array([0, 2, np.nan, 6, 8, 10, 12, 14, 16, 18.0])    # 2/ano, um ano ausente
    assert pixel_trend(_stack([x]), YEARS, min_n=8)["slope"][0, 0] == 2.0


def test_bh_controls_false_discoveries_on_noise_and_finds_signal():
    rng = np.random.default_rng(1)
    noise = rng.normal(size=(10, 1, 2000))
    r = pixel_trend(noise, YEARS, min_n=8)
    assert bh_reject(r["p"], 0.05).mean() < 0.05
    sig = noise.copy(); sig[:, 0, :100] += 3.0 * (YEARS - 2012)[:, None]
    lab = significant_change(sig, YEARS, min_n=8, alpha=0.05)
    assert (lab["label"][0, :100] == 1).mean() > 0.95 and lab["tested"].all()


def test_bh_ignores_nan_and_nothing_rejected_when_all_large():
    p = np.array([np.nan, 0.9, 0.8, 0.7])
    assert not bh_reject(p, 0.05).any()
    q = np.array([0.001, np.nan, 0.2, 0.9])
    assert bh_reject(q, 0.05).tolist() == [True, False, False, False]


def test_labels_up_down_and_shares_by_municipality():
    up = 1.0 * (YEARS - 2012); down = -up; flat = np.zeros(10)
    lab = significant_change(_stack([up, down, flat, flat]), YEARS, min_n=8, alpha=0.05, active=None)
    assert lab["label"][0].tolist() == [1, -1, 0, 0]
    ov = pd.DataFrame({"CD_MUN": ["A", "A", "B", "B"], "pix": [0, 1, 2, 3], "cov": [1.0, 1.0, 1.0, 1.0]})
    s = trend_shares(ov, lab["label"], lab["tested"]).set_index("CD_MUN")
    assert s.loc["A", "share_increase"] == 0.5 and s.loc["A", "share_decrease"] == 0.5
    assert s.loc["B", "share_increase"] == 0.0 and s.loc["B", "n_tested_weight"] == 2.0


def test_active_mask_excludes_pixels_from_test():
    up = 1.0 * (YEARS - 2012)
    lab = significant_change(_stack([up, up]), YEARS, min_n=8, alpha=0.05,
                             active=np.array([[True, False]]))
    assert lab["tested"].tolist() == [[True, False]] and lab["label"][0].tolist() == [1, 0]
