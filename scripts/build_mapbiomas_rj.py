#!/usr/bin/env python3
"""Cobertura e uso do solo do estado do Rio de Janeiro, MapBiomas Brasil Coleção 11 (30 m), por ano.

Entrada: data/raw/mapbiomas/MAPBIOMAS_BRAZIL-COL.11-BIOME_STATE.xlsx (aba COVERAGE_11), baixado de
brasil.mapbiomas.org/downloads/estatisticas/ (uso público, aberto e gratuito mediante referência; CC BY 4.0).
Saída: web/data/downloads/openlux_cobertura_rj_mapbiomas_col11.csv (área em hectares por classe de nível 1 e ano).

Limite: são estatísticas do estado, não de cada município. Os mapas em GeoTIFF estão suspensos no site do MapBiomas.
"""
import collections
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parent.parent
ENTRADA = ROOT / "data/raw/mapbiomas/MAPBIOMAS_BRAZIL-COL.11-BIOME_STATE.xlsx"
SAIDA = ROOT / "web/data/downloads/openlux_cobertura_rj_mapbiomas_col11.csv"


def main():
    wb = openpyxl.load_workbook(ENTRADA, read_only=True)
    ws = wb["COVERAGE_11"]
    linhas = ws.iter_rows(values_only=True)
    cab = next(linhas)
    idx = {h: i for i, h in enumerate(cab) if h}
    anos = sorted(int(h[1:]) for h in cab if isinstance(h, str) and h.startswith("y") and h[1:].isdigit())
    tot = collections.defaultdict(lambda: collections.defaultdict(float))
    for r in linhas:
        if len(r) < len(cab) or r[idx["state"]] is None:
            continue
        if str(r[idx["state"]]).strip() != "Rio de Janeiro":
            continue
        classe = r[idx["class_level_1"]]
        for a in anos:
            tot[a][classe] += float(r[idx[f"y{a}"]] or 0)
    classes = sorted({c for a in anos for c in tot[a]})
    with SAIDA.open("w", encoding="utf-8") as f:
        f.write("ano,classe_nivel_1,area_ha,fracao_do_estado\n")
        for a in anos:
            s = sum(tot[a].values())
            for c in classes:
                v = tot[a].get(c, 0.0)
                if v:
                    f.write(f"{a},{c},{v:.1f},{v / s:.4f}\n")
    print(f"OK: {len(anos)} anos, {len(classes)} classes em {SAIDA}")


if __name__ == "__main__":
    main()
