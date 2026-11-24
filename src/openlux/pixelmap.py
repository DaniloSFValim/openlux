"""Camada de pixel da interface: classes FIXAS de radiancia e mascara do estado.

Esquema manual (nao quantis), igual em todos os anos para que os mapas sejam comparaveis. Limites em
nW cm-2 sr-1, fechados a esquerda: 0,5 (valor abaixo do qual o produto zera a radiancia, guia Black Marble),
2, 8, 30 e 100 (escala aproximadamente logaritmica, fator ~4). A grade enviada ao navegador contem
APENAS o codigo da classe (uint8), nunca o valor da radiancia: a interface nao redistribui o dado da NASA
pixel a pixel.

Codigos: 0 fora do estado; 1 dentro do estado sem dado valido (agua, qualidade, fill); 2.. classes.
"""
from __future__ import annotations

import numpy as np
from rasterio.features import rasterize

BREAKS = [0.5, 2.0, 8.0, 30.0, 100.0]
CODE_OUTSIDE, CODE_INSIDE_NODATA, FIRST_RADIANCE_CODE = 0, 1, 2
LABELS = ["< 0,5", "0,5 a < 2", "2 a < 8", "8 a < 30", "30 a < 100", "≥ 100"]   # rotulos das classes de radiancia


def radiance_classes(radiance, inside, breaks=BREAKS) -> np.ndarray:
    """Codigos uint8 por pixel. ``radiance`` com NaN nos invalidos; ``inside`` = pixel no estado."""
    r = np.asarray(radiance, dtype="float64")
    out = np.full(r.shape, CODE_OUTSIDE, dtype="uint8")
    valid = np.isfinite(r)
    cls = FIRST_RADIANCE_CODE + np.searchsorted(np.asarray(breaks), np.where(valid, r, 0.0), side="right")
    inside = np.asarray(inside, dtype=bool)
    out[inside] = CODE_INSIDE_NODATA
    out[inside & valid] = cls[inside & valid].astype("uint8")
    return out


def state_mask(geometries, shape, transform) -> np.ndarray:
    """Pixels tocados por qualquer geometria (all_touched, para nao abrir buracos na divisa)."""
    m = rasterize([(g, 1) for g in geometries], out_shape=shape, transform=transform, fill=0,
                  all_touched=True, dtype="uint8")
    return m.astype(bool)


#: Camada de mudanca por pixel (Mann-Kendall + Sen + FDR, openlux.pixeltrend). 0 fora do estado.
CHANGE_UNTESTED, CHANGE_NOT_SIGNIFICANT, CHANGE_INCREASE, CHANGE_DECREASE = 1, 2, 3, 4


def change_codes(label, tested, inside) -> np.ndarray:
    """Codigos uint8 da mudanca por pixel: 1 nao testado (nao iluminado ou poucos anos), 2 sem mudanca
    significativa, 3 aumento significativo, 4 reducao significativa; 0 fora do estado."""
    label, tested, inside = np.asarray(label), np.asarray(tested, dtype=bool), np.asarray(inside, dtype=bool)
    out = np.full(label.shape, CODE_OUTSIDE, dtype="uint8")
    out[inside] = CHANGE_UNTESTED
    out[inside & tested] = CHANGE_NOT_SIGNIFICANT
    out[inside & tested & (label == 1)] = CHANGE_INCREASE
    out[inside & tested & (label == -1)] = CHANGE_DECREASE
    return out
