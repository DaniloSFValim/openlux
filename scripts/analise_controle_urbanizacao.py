#!/usr/bin/env python3
"""Controle de urbanização na análise de unidades de conservação (nível municipal, 92 municípios).

Entradas publicadas (web/data/downloads):
- openlux_uc_fracao_municipio_2025.csv: fração da área em UC e radiância média 2025.
- openlux_area_urbana_municipio_2019.csv: fração urbana (IBGE, Áreas Urbanizadas 2019) e área municipal.

Método: correlação parcial de Spearman entre a fração em UC e a radiância, controlando pela fração urbana
(e, num segundo modelo, pela área municipal). Calcula-se o resíduo dos postos de cada variável numa regressão
linear dos postos sobre os postos das variáveis de controle, e a correlação entre os resíduos. O p-valor vem de
permutação das frações de UC (5.000 reamostras, semente fixa).

Limite: associação exploratória entre municípios, não causa. A fração urbana é de 2019 e a radiância, de 2025.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import rankdata, spearmanr

ROOT = Path(__file__).resolve().parent.parent
DL = ROOT / "web/data/downloads"
OUT = ROOT / "outputs/ambiental/controle_urbanizacao.json"


def residuo(v, controles):
    X = np.column_stack([np.ones(len(v))] + [rankdata(c) for c in controles])
    b = np.linalg.lstsq(X, rankdata(v), rcond=None)[0]
    return rankdata(v) - X @ b


def parcial(x, y, controles):
    return float(np.corrcoef(residuo(x, controles), residuo(y, controles))[0, 1])


def main():
    uc = pd.read_csv(DL / "openlux_uc_fracao_municipio_2025.csv", dtype={"CD_MUN": str})
    urb = pd.read_csv(DL / "openlux_area_urbana_municipio_2019.csv", dtype={"CD_MUN": str})
    d = uc.merge(urb[["CD_MUN", "fracao_urbana", "area_municipio_km2"]], on="CD_MUN", how="inner", validate="one_to_one")
    assert len(d) == 92 and not d.isna().any().any()
    x, y = d.fracao_area_uc.values, d.mean_radiance.values
    z, a = d.fracao_urbana.values, d.area_municipio_km2.values

    rho, p = spearmanr(x, y)
    parc_urb = parcial(x, y, [z])
    parc_urb_area = parcial(x, y, [z, a])
    rng = np.random.default_rng(20251126)
    obs = abs(parc_urb)
    hits = sum(abs(parcial(rng.permutation(x), y, [z])) >= obs for _ in range(5000))
    p_perm = (hits + 1) / 5001

    res = {
        "n_municipios": int(len(d)),
        "rho_uc_x_radiancia": round(float(rho), 4), "p_uc_x_radiancia": round(float(p), 4),
        "rho_urbana_x_radiancia": round(float(spearmanr(z, y)[0]), 4),
        "rho_uc_x_urbana": round(float(spearmanr(x, z)[0]), 4),
        "parcial_controle_urbana": round(parc_urb, 4), "p_permutacao_parcial": round(p_perm, 4),
        "parcial_controle_urbana_e_area": round(parc_urb_area, 4),
        "nota": "associação entre municípios, exploratória, não causal; urbana de 2019 e radiância de 2025",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
