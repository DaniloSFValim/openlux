"""Setores censitarios: sobreposicao com a grade e indicadores. Dados SINTETICOS (so para teste)."""
import geopandas as gpd
import numpy as np
import pytest
from rasterio.transform import from_origin
from shapely.geometry import box

from openlux.sectors import dedupe_sectors, sector_indicators, sector_overlay

T = from_origin(0.0, 2.0, 1.0, 1.0)      # grade 2x2: pixel (r, c) = [c, c+1] x [1-r+... ] ; origem (0, 2)
SHAPE = (2, 2)


def _sectors(rows):
    """rows: (CD_SETOR, CD_MUN, SITUACAO, pop, geometry)."""
    return gpd.GeoDataFrame(
        {"CD_SETOR": [r[0] for r in rows], "CD_MUN": [r[1] for r in rows], "SITUACAO": [r[2] for r in rows],
         "CD_SIT": ["1" for _ in rows], "pop": [r[3] for r in rows]},
        geometry=[r[4] for r in rows], crs="EPSG:4326")


def test_dedupe_keeps_one_population_per_sector_and_unions_geometry():
    g = gpd.GeoDataFrame({"CD_SETOR": ["1", "1", "2"], "CD_MUN": ["10", "10", "10"],
                          "SITUACAO": ["Urbana"] * 3, "CD_SIT": ["1"] * 3, "v0001": ["100", "100", "50"]},
                         geometry=[box(0, 0, 1, 1), box(5, 5, 6, 6), box(1, 0, 2, 1)], crs="EPSG:4674")
    d = dedupe_sectors(g)
    assert len(d) == 2 and d["pop"].sum() == 150                    # 100 (nao 200) + 50
    assert d.crs.to_epsg() == 4326                                # equivalencia declarada SIRGAS ~ WGS84
    assert d[d.CD_SETOR == "1"].geometry.iloc[0].geom_type == "MultiPolygon"


def test_dedupe_repairs_invalid_geometries():
    from shapely.geometry import Polygon
    invalid = Polygon([(0, 0), (1, 1), (1, 0), (0, 1)])           # gravata (invalido)
    g = gpd.GeoDataFrame({"CD_SETOR": ["1"], "CD_MUN": ["10"], "SITUACAO": ["Urbana"], "CD_SIT": ["1"],
                          "v0001": ["10"]}, geometry=[invalid], crs="EPSG:4674")
    assert not invalid.is_valid and dedupe_sectors(g).geometry.is_valid.all()


def test_population_is_split_by_coverage_and_conserved():
    # setor A cobre o pixel (0,0) inteiro (pop 100); setor B cobre metade esquerda de (0,1) e de (1,1) (pop 60)
    s = _sectors([("A", "10", "Urbana", 100, box(0, 1, 1, 2)), ("B", "10", "Rural", 60, box(1, 0, 1.5, 2))])
    ov = sector_overlay(s, SHAPE, T)
    assert ov.groupby("CD_SETOR")["pop"].sum().to_dict() == pytest.approx({"A": 100.0, "B": 60.0})
    b = ov[ov.CD_SETOR == "B"].sort_values("pix")
    assert b["pop"].tolist() == pytest.approx([30.0, 30.0])       # divisao igual entre os dois pixels cobertos
    assert b["cov"].tolist() == pytest.approx([0.5, 0.5])


def test_indicators_population_weighted_radiance_and_lit_fraction():
    s = _sectors([("A", "10", "Urbana", 100, box(0, 1, 1, 2)), ("B", "10", "Rural", 100, box(1, 1, 2, 2))])
    ov = sector_overlay(s, SHAPE, T)
    rad = np.array([[10.0, 0.0], [5.0, 5.0]])                     # A em (0,0)=10; B em (0,1)=0
    out = sector_indicators(ov, rad, tau=0.5).set_index("CD_MUN").loc["10"]
    assert out.pop_weighted_radiance == pytest.approx(5.0)        # (100*10 + 100*0)/200
    assert out.pop_lit_fraction == pytest.approx(0.5)             # so A (pop 100) esta >= 0,5
    assert out.mean_urban == pytest.approx(10.0) and out.mean_rural == pytest.approx(0.0)
    assert out.frac_lit_urban == pytest.approx(1.0) and out.frac_lit_rural == pytest.approx(0.0)
    assert out.pop_valid_fraction == pytest.approx(1.0)


def test_invalid_pixels_leave_numerator_and_denominator_and_are_reported():
    s = _sectors([("A", "10", "Urbana", 100, box(0, 1, 1, 2)), ("B", "10", "Urbana", 100, box(1, 1, 2, 2))])
    ov = sector_overlay(s, SHAPE, T)
    rad = np.array([[8.0, np.nan], [0.0, 0.0]])
    o = sector_indicators(ov, rad, tau=0.5).iloc[0]
    assert o.pop_weighted_radiance == pytest.approx(8.0)          # so A conta
    assert o.pop_valid_fraction == pytest.approx(0.5)             # metade da populacao sem pixel valido


def test_all_invalid_gives_nan_not_zero_and_sector_outside_grid_is_reported():
    s = _sectors([("A", "10", "Urbana", 100, box(0, 1, 1, 2)), ("Z", "10", "Urbana", 40, box(50, 50, 51, 51))])
    ov = sector_overlay(s, SHAPE, T)
    assert "Z" not in set(ov.CD_SETOR) and ov.attrs["population_outside_grid"] == pytest.approx(40.0)
    o = sector_indicators(ov, np.full((2, 2), np.nan), tau=0.5).iloc[0]
    assert np.isnan(o.pop_weighted_radiance) and np.isnan(o.mean_urban)
    assert o.pop_valid_fraction == 0.0
