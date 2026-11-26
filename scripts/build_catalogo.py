"""Gera web/data/downloads/catalogo.json: inventário dos arquivos publicados, com SHA-256 calculado
a partir do próprio arquivo (nada é digitado à mão). Rodar depois de qualquer mudança em web/data.

Uso: python scripts/build_catalogo.py
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
LICENCA = {"id": "CC-BY-4.0", "url": "https://creativecommons.org/licenses/by/4.0/", "status": "confirmada pelo autor em 2026-11-25"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def registro(caminho: Path, **campos) -> dict:
    return {
        "arquivo": caminho.relative_to(WEB).as_posix(),
        "bytes": caminho.stat().st_size,
        "sha256": sha256(caminho),
        "licenca": LICENCA["id"],
        **campos,
    }


def execucao(json_path: Path) -> dict:
    m = json.loads(json_path.read_text(encoding="utf-8"))
    run = m["meta"].get("run", {})
    return {"processado_utc": run.get("processed_utc"), "commit": run.get("code_commit"), "codigo_com_alteracoes_nao_commitadas": run.get("code_dirty")}


def main() -> None:
    itens = []
    dl = WEB / "data" / "downloads"
    itens.append(registro(dl / "openlux_municipios_snpp_serie.csv", titulo="Série anual por município (S-NPP)", tipo="CSV", fonte="NASA Black Marble VNP46A4 v2.0 (DOI 10.5067/VIIRS/VNP46A4.002)", unidade="nW·cm⁻²·sr⁻¹ (radiância média); fração adimensional", periodo="2012–2025", sistema_de_referencia="não se aplica (tabela)", situacao="publicado", execucao=execucao(WEB / "data" / "indicators.json")))
    itens.append(registro(dl / "openlux_municipios_snpp_resumo.csv", titulo="Resumo por município (S-NPP): população 2022, intensidade por habitante e tendências", tipo="CSV", fonte="NASA Black Marble VNP46A4; IBGE Censo 2022 (SIDRA 4709, v93)", unidade="mW·sr⁻¹ por habitante; nW·cm⁻²·sr⁻¹ por ano; p-valor adimensional", periodo="2012–2025 (janelas 2012–2021 e 2012–2025)", sistema_de_referencia="não se aplica (tabela)", situacao="publicado", execucao=execucao(WEB / "data" / "indicators.json")))
    itens.append(registro(WEB / "data" / "indicators.json", titulo="Indicadores municipais, S-NPP (JSON)", tipo="JSON", fonte="NASA Black Marble VNP46A4 v2.0; IBGE", unidade="nW·cm⁻²·sr⁻¹", periodo="2012–2025", sistema_de_referencia="não se aplica (JSON)", situacao="publicado", execucao=execucao(WEB / "data" / "indicators.json")))
    itens.append(registro(WEB / "data" / "indicators_noaa20.json", titulo="Indicadores municipais, NOAA-20 (JSON)", tipo="JSON", fonte="NASA Black Marble VJ146A4 v2.0 (DOI 10.5067/VIIRS/VJ146A4.002); IBGE", unidade="nW·cm⁻²·sr⁻¹", periodo="2018–2025", sistema_de_referencia="não se aplica (JSON)", situacao="publicado", execucao=execucao(WEB / "data" / "indicators_noaa20.json")))
    itens.append(registro(WEB / "data" / "municipios.geojson", titulo="Limites dos 92 municípios (GeoJSON)", tipo="GeoJSON", fonte="IBGE, Malha Municipal Digital 2024 (RJ)", unidade="graus decimais", periodo="malha 2024", sistema_de_referencia="WGS 84 (EPSG:4326) por convenção do GeoJSON (RFC 7946); o SIRGAS 2000 difere por poucos metros", situacao="publicado", execucao=None))
    itens.append(registro(dl / "openlux_municipios_noaa20_serie.csv", titulo="Série anual por município (NOAA-20, sensor primário)", tipo="CSV", fonte="NASA Black Marble VJ146A4 v2.0 (DOI 10.5067/VIIRS/VJ146A4.002)", unidade="nW·cm⁻²·sr⁻¹ (radiância média); fração adimensional", periodo="2018–2025", sistema_de_referencia="não se aplica (tabela)", situacao="publicado", execucao=execucao(WEB / "data" / "indicators_noaa20.json")))
    itens.append(registro(dl / "openlux_municipios_noaa20_resumo.csv", titulo="Resumo por município (NOAA-20): tendência 2018–2025 e variação", tipo="CSV", fonte="NASA Black Marble VJ146A4 v2.0; IBGE", unidade="nW·cm⁻²·sr⁻¹ por ano; p-valor adimensional; variação em %", periodo="2018–2025", sistema_de_referencia="não se aplica (tabela)", situacao="publicado", execucao=execucao(WEB / "data" / "indicators_noaa20.json")))
    for sensor, produto, per in (("snpp", "VNP46A4", "2012–2025"), ("noaa20", "VJ146A4", "2018–2025")):
        itens.append(registro(dl / f"openlux_percentis_pixels_{sensor}.csv", titulo=f"Percentis P75, P90 e P95 dos pixels por município e ano ({sensor.upper().replace('NOAA20', 'NOAA-20')})", tipo="CSV", fonte=f"NASA Black Marble {produto}", unidade="nW·cm⁻²·sr⁻¹ (quantil inferior ponderado pela cobertura dos pixels válidos; qualidade 0; terra)", periodo=per, sistema_de_referencia="não se aplica (tabela)", situacao="publicado", execucao=execucao(WEB / "data" / ("indicators.json" if sensor == "snpp" else "indicators_noaa20.json"))))
    itens.append(registro(dl / "openlux_limites_municipais_rj.gpkg", titulo="Limites dos 92 municípios (GeoPackage, camada 'municipios')", tipo="GeoPackage", fonte="IBGE, Malha Municipal Digital 2024 (RJ), convertida de municipios.geojson", unidade="graus decimais", periodo="malha 2024", sistema_de_referencia="EPSG:4326 declarado no arquivo", situacao="publicado", execucao=None))
    itens.append(registro(dl / "metadata.json", titulo="Metadados dos arquivos S-NPP (licença, citação, ressalvas)", tipo="JSON", fonte="OpenLux", unidade="não se aplica", periodo="2012–2025", sistema_de_referencia="não se aplica", situacao="publicado", execucao=None))
    doc = {
        "versao_software": "0.1.0",
        "licenca_dos_dados_derivados": LICENCA,
        "nota": "Os hashes são calculados sobre os arquivos publicados. 'codigo_com_alteracoes_nao_commitadas: true' indica que o pipeline rodou com alterações não commitadas: a reprodução exata depende de rerodar a partir de um commit limpo.",
        "arquivos": itens,
    }
    (dl / "catalogo.json").write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{len(itens)} arquivos inventariados em {dl / 'catalogo.json'}")


if __name__ == "__main__":
    main()
