"""Arquivos para download do site: formato, contagens, somas SHA-256 e consistência da citação na página."""
import csv
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_web_downloads as bwd  # noqa: E402

DL = ROOT / "web" / "data" / "downloads"


def _meta():
    return json.loads((DL / "metadata.json").read_text(encoding="utf-8"))


def _norm(s):
    return re.sub(r"\s+", " ", s).strip()


def test_serie_has_one_row_per_municipality_and_year():
    rows = list(csv.DictReader((DL / "openlux_municipios_snpp_serie.csv").open(encoding="utf-8-sig")))
    cods = {r["cod_municipio"] for r in rows}
    anos = sorted({int(r["ano"]) for r in rows})
    assert len(cods) == 92
    assert anos == list(range(2012, 2026))
    assert len(rows) == 92 * 14
    assert len({(r["cod_municipio"], r["ano"]) for r in rows}) == len(rows)


def test_resumo_has_one_row_per_municipality_and_units_in_headers():
    rows = list(csv.DictReader((DL / "openlux_municipios_snpp_resumo.csv").open(encoding="utf-8-sig")))
    assert len(rows) == 92
    header = rows[0].keys()
    assert "populacao_2022" in header
    assert any(h.endswith("_por_ano") for h in header)


def test_sha256_in_metadata_matches_the_files():
    for nome, info in _meta()["arquivos"].items():
        dados = (DL / nome).read_bytes()
        assert hashlib.sha256(dados).hexdigest() == info["sha256"]
        assert len(dados) == info["bytes"]


def test_generated_files_are_deterministic(tmp_path):
    bwd.build(out=tmp_path)
    for nome in ("openlux_municipios_snpp_serie.csv", "openlux_municipios_snpp_resumo.csv"):
        assert (tmp_path / nome).read_bytes() == (DL / nome).read_bytes()


def test_license_is_declared_as_a_proposal_and_caveats_are_present():
    m = _meta()
    assert m["licenca"]["id"] == "CC-BY-4.0"
    assert "proposta" in m["licenca"]["status"]
    texto = " ".join(m["ressalvas"])
    assert "ruído" in texto and "Resultados não validados" in texto


def test_citation_on_the_page_matches_metadata():
    html = (ROOT / "web" / "dados.html").read_text(encoding="utf-8")
    m = re.search(r'<p class="cite">(.*?)</p>', html, re.S)
    assert m, "bloco de citação ausente na página"
    import html as h
    assert _norm(h.unescape(m.group(1))) == _norm(_meta()["citacao"])


def test_download_links_point_to_existing_files():
    html = (ROOT / "web" / "dados.html").read_text(encoding="utf-8")
    for href in re.findall(r'href="(data/downloads/[^"]+)" download', html):
        assert (ROOT / "web" / href).is_file(), href
