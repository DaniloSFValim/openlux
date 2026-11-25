"""Catálogo de arquivos publicados (Fase 8): hashes e tamanhos conferidos contra os arquivos reais."""
import hashlib
import json

from helpers import WEB

CAT = json.loads((WEB / "data" / "downloads" / "catalogo.json").read_text(encoding="utf-8"))
OBRIGATORIOS = ("arquivo", "bytes", "sha256", "licenca", "titulo", "tipo", "unidade", "periodo", "sistema_de_referencia")


def test_every_listed_file_exists_and_its_hash_and_size_match():
    for a in CAT["arquivos"]:
        arq = WEB / a["arquivo"]
        assert arq.is_file(), a["arquivo"]
        assert arq.stat().st_size == a["bytes"], a["arquivo"]
        assert hashlib.sha256(arq.read_bytes()).hexdigest() == a["sha256"], a["arquivo"]


def test_every_entry_states_unit_period_reference_system_and_licence():
    for a in CAT["arquivos"]:
        for campo in OBRIGATORIOS:
            assert a.get(campo), (a.get("arquivo"), campo)
    assert CAT["licenca_dos_dados_derivados"]["id"] == "CC-BY-4.0"


def test_noaa20_entry_keeps_the_unreproducible_run_flag():
    # Não esconder: o JSON do NOAA-20 foi gerado com alterações não commitadas no código.
    noaa = next(a for a in CAT["arquivos"] if a["arquivo"] == "data/indicators_noaa20.json")
    assert noaa["execucao"]["codigo_com_alteracoes_nao_commitadas"] is True


def test_geopackage_has_the_92_municipalities_with_unique_codes():
    import geopandas as gpd
    gdf = gpd.read_file(WEB / "data" / "downloads" / "openlux_limites_municipais_rj.gpkg", layer="municipios")
    assert len(gdf) == 92 and gdf["CD_MUN"].is_unique
    assert str(gdf.crs).endswith("4326")


def test_data_page_no_longer_calls_the_licence_a_proposal():
    html = (WEB / "dados.html").read_text(encoding="utf-8")
    assert "proposta: a confirmar" not in html
    assert "confirmada pelo autor em 2026-11-25" in html
