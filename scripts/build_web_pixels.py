#!/usr/bin/env python3
"""Gera web/data/pixels/: uma grade de CLASSES (uint8) por ano para a camada de pixel da interface.

So o codigo da classe e gravado (ver openlux.pixelmap), nunca o valor de radiancia. Usa o S-NPP
(VNP46A4, qualidade 0, mascara de terra) na janela do estado; pixels fora da malha municipal = codigo 0.
"""
import glob
import re
from pathlib import Path

import geopandas as gpd
import h5py
from rasterio.transform import Affine

from openlux.geo import bbox_window
from openlux.io import read_blackmarble, sha256_file
from openlux.log import JsonLogger
from openlux.pixelmap import BREAKS, FIRST_RADIANCE_CODE, radiance_classes, state_mask
from openlux.provenance import code_version, write_json

RAW, OUT = Path("data/raw"), Path("web/data/pixels")
LABELS = ["< 0,5", "0,5 a < 2", "2 a < 8", "8 a < 30", "30 a < 100", "≥ 100"]


def main():
    log = JsonLogger()
    mesh = gpd.read_file(next(glob.iglob(str(RAW / "ibge/RJ_Municipios_2024/*.shp")))).set_crs(
        "EPSG:4326", allow_override=True)
    files = {int(re.search(r"\.A(\d{4})001\.", p).group(1)): Path(p)
             for p in sorted(glob.glob(str(RAW / "VNP46A4/*.h5")))}
    first = files[min(files)]
    _, t = read_blackmarble(first)
    with h5py.File(first, "r") as f:
        shape = f["HDFEOS/GRIDS/VIIRS_Grid_DNB_2d/Data Fields/AllAngle_Composite_Snow_Free"].shape
    r0, r1, c0, c1 = bbox_window(t, shape, tuple(mesh.total_bounds))
    tw = t * Affine.translation(c0, r0)
    inside = state_mask(list(mesh.geometry), (r1 - r0, c1 - c0), tw)
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.bin"):
        old.unlink()
    entries = {}
    for y, p in sorted(files.items()):
        rad, _ = read_blackmarble(p)
        codes = radiance_classes(rad[r0:r1, c0:c1], inside)
        (OUT / f"{y}.bin").write_bytes(codes.tobytes())
        entries[str(y)] = dict(sha256=sha256_file(OUT / f"{y}.bin"), input_sha256=sha256_file(p))
        log.log("year_written", year=y, inside_pixels=int(inside.sum()),
                nodata_inside=int(((codes == 1)).sum()))
    write_json(OUT / "meta.json", dict(
        grid=dict(rows=r1 - r0, cols=c1 - c0, lon_west=tw.c, lat_north=tw.f, pixel_deg=abs(tw.a)),
        classes=dict(first_code=FIRST_RADIANCE_CODE, breaks_nw_cm2_sr=BREAKS, labels=LABELS),
        codes={"0": "fora do estado", "1": "sem dado valido"},
        sensor="Suomi NPP (VNP46A4 v2.0), AllAngle_Composite_Snow_Free, qualidade 0, mascara de terra",
        years=entries, code=code_version()))
    print("OK", len(entries), "anos;", (r1 - r0), "x", (c1 - c0))


if __name__ == "__main__":
    main()
