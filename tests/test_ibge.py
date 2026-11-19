"""Parser SIDRA. O JSON abaixo e SINTETICO (estrutura real da API, valores arbitrarios)."""
import pytest

from openlux.ibge import parse_sidra_population

HEADER = {"NC": "Nível Territorial (Código)", "V": "Valor", "D1C": "Município (Código)",
          "D2C": "Variável (Código)", "D3C": "Ano (Código)"}


def row(cod, val, var="93", ano="2022"):
    return {"NC": "6", "V": val, "D1C": cod, "D2C": var, "D3C": ano}


def test_parses_and_skips_header():
    df = parse_sidra_population([HEADER, row("3300100", "100"), row("3300159", "2500")])
    assert list(df.columns) == ["cd_mun", "population"]
    assert df.cd_mun.tolist() == ["3300100", "3300159"]
    assert df.population.tolist() == [100, 2500]


def test_missing_value_markers_become_nan():
    df = parse_sidra_population([HEADER, row("3300100", "..."), row("3300159", "-")])
    assert df.population.isna().all()


def test_wrong_variable_or_year_is_rejected():
    with pytest.raises(ValueError):
        parse_sidra_population([HEADER, row("3300100", "1", var="94")])
    with pytest.raises(ValueError):
        parse_sidra_population([HEADER, row("3300100", "1", ano="2010")])


def test_duplicate_municipality_is_rejected():
    with pytest.raises(ValueError):
        parse_sidra_population([HEADER, row("3300100", "1"), row("3300100", "2")])
