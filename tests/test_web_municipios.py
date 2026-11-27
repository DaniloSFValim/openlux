"""Páginas municipais (web/municipio) e relatórios em PDF: 92 municípios, valores conferidos
contra os dados publicados e links do Observatório."""
import json
import re
import shutil
import subprocess
import unicodedata
from pathlib import Path

import pytest

WEB = Path(__file__).resolve().parent.parent / "web"
N = json.loads((WEB / "data/indicators_noaa20.json").read_text(encoding="utf-8"))
RIO, NITEROI = "3304557", "3303302"


def slug(nome):
    s = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode().lower()
    return "-".join("".join(ch if ch.isalnum() else " " for ch in s).split())


def fmt(v):
    return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def test_one_html_and_pdf_per_municipality():
    for cd, m in N["municipios"].items():
        s = slug(m["name"])
        assert (WEB / "municipio" / f"{s}.html").is_file(), s
        pdf = WEB / "municipio" / f"{s}.pdf"
        assert pdf.is_file(), s
        assert pdf.read_bytes()[:5] == b"%PDF-", s


def test_index_lists_all_92():
    html = (WEB / "municipios.html").read_text(encoding="utf-8")
    assert len(re.findall(r'href="municipio/[^"]+\.html"', html)) == 92


def test_rio_page_values_match_published_data():
    s = slug(N["municipios"][RIO]["name"])
    html = (WEB / "municipio" / f"{s}.html").read_text(encoding="utf-8")
    media = N["municipios"][RIO]["mean"][-1]
    assert f"<td>{fmt(media)}</td>" in html
    medias = sorted((m["mean"][-1] for m in N["municipios"].values() if m["mean"][-1] is not None), reverse=True)
    assert f"{medias.index(media) + 1}º de 92" in html
    assert "6.211.223 habitantes" in html


def test_pdf_states_area_population_and_generation_data():
    if not shutil.which("pdftotext"):
        pytest.skip("pdftotext não instalado")
    pdf = WEB / "municipio" / "niteroi.pdf"
    texto = subprocess.run(["pdftotext", str(pdf), "-"], capture_output=True, text=True, check=True).stdout
    assert "Relatório municipal: Niterói" in texto
    assert "133,757 km²" in texto
    assert "481.749 hab." in texto
    assert "Dados processados em" in texto and "código" in texto


def test_interactive_maps_link_to_municipal_pages_that_exist():
    html = (WEB / "js/laboratorio.js").read_text(encoding="utf-8")
    assert "municipio/' + slug(" in html
    assert (WEB / "municipio" / f"{slug(N['municipios'][NITEROI]['name'])}.html").is_file()
