"""Correspondencia entre citacoes no texto e lista bibliografica (textos SINTETICOS)."""
from openlux.references import check_citations, format_entry

REFS = [{"key": "a", "doi": "10.1/a", "cite": "Silva et al. (2020)"},
        {"key": "b", "doi": "10.1/b", "cite": "Souza (1999)"}]


def test_all_cited_and_no_orphans():
    r = check_citations("Como em Silva et al. (2020) e Souza (1999).", REFS)
    assert r["uncited_references"] == [] and r["unknown_citations"] == []


def test_detects_uncited_reference_and_unknown_citation():
    r = check_citations("Segundo Silva et al. (2020) e Pereira et al. (2018).", REFS)
    assert r["uncited_references"] == ["Souza (1999)"]
    assert r["unknown_citations"] == ["Pereira et al. (2018)"]


def test_year_mismatch_is_unknown_citation():
    r = check_citations("Silva et al. (2021) e Souza (1999).", REFS)
    assert "Silva et al. (2021)" in r["unknown_citations"]
    assert r["uncited_references"] == ["Silva et al. (2020)"]


def test_format_entry_apa_like_with_initials_and_doi():
    msg = {"author": [{"given": "Miguel O.", "family": "Román"}, {"given": "Zhuosen", "family": "Wang"}],
           "title": ["Um título"], "issued": {"date-parts": [[2018]]},
           "container-title": ["Revista X"], "volume": "210", "page": "113-143"}
    e = format_entry(msg, "10.1/x")
    assert e == "Román, M. O., Wang, Z. (2018). Um título. *Revista X*, 210, 113–143. https://doi.org/10.1/x"


def test_format_entry_truncates_long_author_lists():
    msg = {"author": [{"given": "A", "family": f"F{i}"} for i in range(12)], "title": ["T"],
           "issued": {"date-parts": [[2020]]}, "container-title": ["R"]}
    e = format_entry(msg, "10.1/y")
    assert e.startswith("F0, A. et al. (2020).")


def test_format_entry_fixes_all_caps_records():
    msg = {"author": [{"given": "M. G.", "family": "KENDALL"}], "title": ["A NEW MEASURE OF RANK CORRELATION"],
           "issued": {"date-parts": [[1938]]}, "container-title": ["Biometrika"], "volume": "30", "page": "81-93"}
    e = format_entry(msg, "10.1/z")
    assert e.startswith("Kendall, M. G. (1938). A new measure of rank correlation.")


def test_parenthetical_citation_style_is_recognized():
    r = check_citations("Resultado conhecido (Silva et al., 2020; Souza, 1999).", REFS)
    assert r["uncited_references"] == [] and r["unknown_citations"] == []


def test_parenthetical_unknown_and_year_mismatch():
    r = check_citations("(Silva et al., 2019) e (Souza, 1999)", REFS)
    assert "Silva et al. (2019)" in r["unknown_citations"]
    assert r["uncited_references"] == ["Silva et al. (2020)"]


def test_plain_years_without_author_are_not_citations():
    r = check_citations("Dados de 2022, versão 2.0 (outubro de 2024), tabela 4709.", REFS)
    assert r["unknown_citations"] == []


def test_years_in_other_contexts_are_not_citations():
    t = "Censo Demográfico 2022, SIRGAS 2000 (EPSG:4674), NOAA-20 (2018–2025), Malha Digital 2024 (RJ)."
    assert check_citations(t, REFS)["unknown_citations"] == []
